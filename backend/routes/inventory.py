"""
Inventory Management API
========================
Stock tracking, transactions, bulk upload, and item usage history.
Auto-updates when engineers use parts during field visits.
"""

import csv
import io
import uuid
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from services.auth import get_current_admin, get_current_engineer
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Inventory"])

IST = timezone(timedelta(hours=5, minutes=30))


def _org(admin: dict) -> str:
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    return org_id


# ── Models ────────────────────────────────────────────────

class StockAdjustment(BaseModel):
    product_id: str
    quantity: int
    type: str  # "purchase", "return", "adjustment", "initial"
    unit_cost: Optional[float] = None
    reference: Optional[str] = None
    notes: Optional[str] = None


# ── Inventory CRUD ────────────────────────────────────────

@router.get("/api/admin/inventory")
async def list_inventory(
    admin: dict = Depends(get_current_admin),
    search: Optional[str] = None,
    category_id: Optional[str] = None,
    low_stock: Optional[bool] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
):
    """List inventory items with stock levels."""
    org_id = _org(admin)

    product_query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    if category_id:
        product_query["category_id"] = category_id
    if search:
        product_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
        ]

    total = await db.item_products.count_documents(product_query)
    skip = (page - 1) * limit
    products = await db.item_products.find(product_query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit).to_list(limit)

    # Get category names
    cat_ids = list({p["category_id"] for p in products if p.get("category_id")})
    cat_map = {}
    if cat_ids:
        cats = await db.item_categories.find({"id": {"$in": cat_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
        cat_map = {c["id"]: c["name"] for c in cats}

    # Get stock levels from inventory collection
    pids = [p["id"] for p in products]
    stock_docs = await db.inventory.find(
        {"organization_id": org_id, "product_id": {"$in": pids}},
        {"_id": 0, "product_id": 1, "quantity_in_stock": 1, "total_purchased": 1, "total_used": 1, "reorder_level": 1}
    ).to_list(500)
    stock_map = {s["product_id"]: s for s in stock_docs}

    items = []
    for p in products:
        stock = stock_map.get(p["id"], {})
        item = {
            **p,
            "category_name": cat_map.get(p.get("category_id"), ""),
            "quantity_in_stock": stock.get("quantity_in_stock", 0),
            "total_purchased": stock.get("total_purchased", 0),
            "total_used": stock.get("total_used", 0),
            "reorder_level": stock.get("reorder_level", 5),
        }
        items.append(item)

    if low_stock:
        items = [i for i in items if i["quantity_in_stock"] <= i["reorder_level"]]
        total = len(items)

    return {"items": items, "total": total, "page": page}


@router.post("/api/admin/inventory/adjust")
async def adjust_stock(data: StockAdjustment, admin: dict = Depends(get_current_admin)):
    """Manually adjust stock (purchase, return, initial stock, adjustment)."""
    org_id = _org(admin)

    product = await db.item_products.find_one(
        {"id": data.product_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1}
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Update or create inventory record
    inv = await db.inventory.find_one({"organization_id": org_id, "product_id": data.product_id})
    if not inv:
        inv = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "product_id": data.product_id,
            "quantity_in_stock": 0,
            "total_purchased": 0,
            "total_used": 0,
            "reorder_level": 5,
            "created_at": get_ist_isoformat(),
        }
        await db.inventory.insert_one(inv)

    # Calculate stock change
    qty_change = data.quantity if data.type in ("purchase", "return", "initial", "adjustment") else -data.quantity

    update_ops = {
        "$inc": {"quantity_in_stock": qty_change},
        "$set": {"updated_at": get_ist_isoformat()},
    }
    if data.type == "purchase":
        update_ops["$inc"]["total_purchased"] = data.quantity

    await db.inventory.update_one(
        {"organization_id": org_id, "product_id": data.product_id},
        update_ops
    )

    # Log transaction
    txn = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "product_id": data.product_id,
        "product_name": product["name"],
        "type": data.type,
        "quantity": data.quantity,
        "unit_cost": data.unit_cost,
        "reference": data.reference,
        "notes": data.notes,
        "performed_by": admin.get("name", "Admin"),
        "performed_by_id": admin.get("id"),
        "created_at": get_ist_isoformat(),
    }
    await db.inventory_transactions.insert_one(txn)

    updated = await db.inventory.find_one(
        {"organization_id": org_id, "product_id": data.product_id}, {"_id": 0}
    )
    return {"inventory": updated, "message": f"Stock adjusted: +{data.quantity} ({data.type})"}


@router.get("/api/admin/inventory/{product_id}/history")
async def get_inventory_history(
    product_id: str,
    admin: dict = Depends(get_current_admin),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
):
    """Get transaction history for a product including job usage details."""
    org_id = _org(admin)

    product = await db.item_products.find_one(
        {"id": product_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get inventory summary
    inv = await db.inventory.find_one(
        {"organization_id": org_id, "product_id": product_id}, {"_id": 0}
    )

    # Get transactions
    total = await db.inventory_transactions.count_documents(
        {"organization_id": org_id, "product_id": product_id}
    )
    skip = (page - 1) * limit
    transactions = await db.inventory_transactions.find(
        {"organization_id": org_id, "product_id": product_id}, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    # Enrich job-usage transactions with ticket details
    ticket_ids = [t.get("ticket_id") for t in transactions if t.get("ticket_id")]
    ticket_map = {}
    if ticket_ids:
        tickets = await db.tickets_v2.find(
            {"id": {"$in": ticket_ids}},
            {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "company_name": 1, "assigned_to_name": 1}
        ).to_list(200)
        ticket_map = {t["id"]: t for t in tickets}

    for txn in transactions:
        if txn.get("ticket_id") and txn["ticket_id"] in ticket_map:
            txn["ticket_details"] = ticket_map[txn["ticket_id"]]

    cat_name = ""
    if product.get("category_id"):
        cat = await db.item_categories.find_one({"id": product["category_id"]}, {"_id": 0, "name": 1})
        cat_name = cat["name"] if cat else ""

    return {
        "product": {**product, "category_name": cat_name},
        "inventory": inv or {"quantity_in_stock": 0, "total_purchased": 0, "total_used": 0},
        "transactions": transactions,
        "total": total,
        "page": page,
    }


# ── Bulk Upload ───────────────────────────────────────────

@router.get("/api/admin/item-master/bulk-upload/sample")
async def download_sample_csv(admin: dict = Depends(get_current_admin)):
    """Download sample CSV template for bulk product upload."""
    org_id = _org(admin)

    # Get categories for reference
    cats = await db.item_categories.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1}
    ).to_list(100)
    cat_names = [c["name"] for c in cats]

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "name", "sku", "category", "part_number", "brand", "manufacturer",
        "description", "unit_price", "gst_slab", "hsn_code", "unit_of_measure",
        "initial_stock", "reorder_level"
    ])
    # Sample rows
    writer.writerow([
        "Hikvision 2MP Dome Camera", "HIK-DS-2CD1123", cat_names[0] if cat_names else "Security",
        "DS-2CD1123G0E", "Hikvision", "Hikvision India",
        "2MP Fixed Dome Network Camera", "3500", "18", "85258090", "unit", "10", "5"
    ])
    writer.writerow([
        "Cat6 Ethernet Cable 1M", "CAT6-1M-BL", cat_names[0] if cat_names else "Networking",
        "CAT6-PATCH-1M", "DLink", "DLink India",
        "Cat6 UTP Patch Cable 1 Meter Blue", "85", "18", "85444900", "piece", "50", "20"
    ])
    writer.writerow([
        f"# Available categories: {', '.join(cat_names) if cat_names else 'Create categories first'}",
        "", "", "", "", "", "# GST slabs: 0, 5, 12, 18, 28", "", "", "", "", "", ""
    ])

    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=item_master_bulk_upload_sample.csv"},
    )


@router.post("/api/admin/item-master/bulk-upload")
async def bulk_upload_products(
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin),
):
    """Bulk upload products from CSV. Skips duplicates (by SKU or name)."""
    org_id = _org(admin)

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = content.decode("latin-1")

    reader = csv.DictReader(io.StringIO(text))

    # Get existing categories
    cats = await db.item_categories.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(500)
    cat_map = {c["name"].lower().strip(): c["id"] for c in cats}

    # Get existing products for duplicate check
    existing_products = await db.item_products.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "sku": 1}
    ).to_list(10000)
    existing_names = {p["name"].lower().strip() for p in existing_products}
    existing_skus = {p["sku"].lower().strip() for p in existing_products if p.get("sku")}

    created = 0
    skipped = 0
    errors = []
    now = get_ist_isoformat()

    for row_num, row in enumerate(reader, start=2):
        name = (row.get("name") or "").strip()
        if not name or name.startswith("#"):
            continue

        sku = (row.get("sku") or "").strip()
        category_name = (row.get("category") or "").strip()

        # Duplicate check
        if sku and sku.lower() in existing_skus:
            errors.append({"row": row_num, "name": name, "reason": f"Duplicate SKU: {sku}"})
            skipped += 1
            continue
        if name.lower() in existing_names:
            errors.append({"row": row_num, "name": name, "reason": f"Duplicate product name: {name}"})
            skipped += 1
            continue

        # Resolve category
        cat_id = cat_map.get(category_name.lower()) if category_name else None
        if not cat_id and category_name:
            # Auto-create category
            new_cat_id = str(uuid.uuid4())
            await db.item_categories.insert_one({
                "id": new_cat_id, "organization_id": org_id,
                "name": category_name, "is_active": True, "is_deleted": False,
                "sort_order": len(cat_map), "created_at": now, "updated_at": now,
            })
            cat_map[category_name.lower()] = new_cat_id
            cat_id = new_cat_id

        if not cat_id:
            errors.append({"row": row_num, "name": name, "reason": "No category specified"})
            skipped += 1
            continue

        try:
            unit_price = float(row.get("unit_price") or 0)
            gst_slab = int(row.get("gst_slab") or 18)
            if gst_slab not in [0, 5, 12, 18, 28]:
                gst_slab = 18
            initial_stock = int(row.get("initial_stock") or 0)
            reorder_level = int(row.get("reorder_level") or 5)
        except (ValueError, TypeError) as e:
            errors.append({"row": row_num, "name": name, "reason": f"Invalid number: {e}"})
            skipped += 1
            continue

        product_id = str(uuid.uuid4())
        product = {
            "id": product_id,
            "organization_id": org_id,
            "category_id": cat_id,
            "name": name,
            "sku": sku or None,
            "part_number": (row.get("part_number") or "").strip() or None,
            "brand": (row.get("brand") or "").strip() or None,
            "manufacturer": (row.get("manufacturer") or "").strip() or None,
            "description": (row.get("description") or "").strip() or None,
            "unit_price": unit_price,
            "gst_slab": gst_slab,
            "hsn_code": (row.get("hsn_code") or "").strip() or None,
            "unit_of_measure": (row.get("unit_of_measure") or "unit").strip(),
            "is_active": True,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now,
            "created_by": admin.get("id"),
        }
        await db.item_products.insert_one(product)

        # Add to duplicate tracking sets
        existing_names.add(name.lower())
        if sku:
            existing_skus.add(sku.lower())

        # Create initial stock if specified
        if initial_stock > 0:
            await db.inventory.insert_one({
                "id": str(uuid.uuid4()),
                "organization_id": org_id,
                "product_id": product_id,
                "quantity_in_stock": initial_stock,
                "total_purchased": initial_stock,
                "total_used": 0,
                "reorder_level": reorder_level,
                "created_at": now,
                "updated_at": now,
            })
            await db.inventory_transactions.insert_one({
                "id": str(uuid.uuid4()),
                "organization_id": org_id,
                "product_id": product_id,
                "product_name": name,
                "type": "initial",
                "quantity": initial_stock,
                "unit_cost": unit_price,
                "reference": "Bulk Upload",
                "notes": "Initial stock from CSV upload",
                "performed_by": admin.get("name", "Admin"),
                "performed_by_id": admin.get("id"),
                "created_at": now,
            })

        created += 1

    return {
        "created": created,
        "skipped": skipped,
        "errors": errors[:50],
        "message": f"Uploaded {created} products. {skipped} skipped (duplicates/errors).",
    }


# ── Engineer Inventory View ───────────────────────────────

@router.get("/api/engineer/inventory")
async def engineer_list_inventory(
    engineer: dict = Depends(get_current_engineer),
    search: Optional[str] = None,
):
    """Engineers can view available inventory."""
    org_id = engineer.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    product_query = {"organization_id": org_id, "is_deleted": {"$ne": True}, "is_active": True}
    if search:
        product_query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
        ]

    products = await db.item_products.find(product_query, {"_id": 0}).sort("name", 1).to_list(500)

    pids = [p["id"] for p in products]
    stock_docs = await db.inventory.find(
        {"organization_id": org_id, "product_id": {"$in": pids}},
        {"_id": 0, "product_id": 1, "quantity_in_stock": 1}
    ).to_list(500)
    stock_map = {s["product_id"]: s.get("quantity_in_stock", 0) for s in stock_docs}

    items = []
    for p in products:
        items.append({
            "id": p["id"],
            "name": p["name"],
            "sku": p.get("sku"),
            "brand": p.get("brand"),
            "unit_price": p.get("unit_price", 0),
            "gst_slab": p.get("gst_slab", 18),
            "quantity_in_stock": stock_map.get(p["id"], 0),
        })

    return {"items": items}
