"""
Item Master API Routes
======================
CRUD for categories, products (with pricing/GST), and product bundles.
All endpoints are tenant-scoped.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin
from models.item_master import (
    ItemCategory, ItemCategoryCreate, ItemCategoryUpdate,
    ItemProduct, ItemProductCreate, ItemProductUpdate,
    ItemBundle, ItemBundleCreate, ItemBundleUpdate,
    GST_SLABS,
)
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/item-master", tags=["Item Master"])


def _org(admin: dict) -> str:
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    return org_id


# ── Categories ────────────────────────────────────────────

@router.get("/categories")
async def list_categories(admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    cats = await db.item_categories.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).sort("sort_order", 1).to_list(500)
    return {"categories": cats}


@router.post("/categories")
async def create_category(data: ItemCategoryCreate, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    # duplicate guard
    dup = await db.item_categories.find_one({
        "organization_id": org_id,
        "name": {"$regex": f"^{data.name}$", "$options": "i"},
        "is_deleted": {"$ne": True},
    })
    if dup:
        raise HTTPException(status_code=400, detail="Category with this name already exists")

    cat = ItemCategory(organization_id=org_id, **data.model_dump())
    await db.item_categories.insert_one(cat.model_dump())
    return await db.item_categories.find_one({"id": cat.id}, {"_id": 0})


@router.put("/categories/{cat_id}")
async def update_category(cat_id: str, data: ItemCategoryUpdate, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    existing = await db.item_categories.find_one({"id": cat_id, "organization_id": org_id, "is_deleted": {"$ne": True}})
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    updates["updated_at"] = get_ist_isoformat()

    await db.item_categories.update_one({"id": cat_id}, {"$set": updates})
    return await db.item_categories.find_one({"id": cat_id}, {"_id": 0})


@router.delete("/categories/{cat_id}")
async def delete_category(cat_id: str, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    # check for products under this category
    product_count = await db.item_products.count_documents({
        "organization_id": org_id, "category_id": cat_id, "is_deleted": {"$ne": True}
    })
    if product_count > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete: {product_count} product(s) still linked to this category")

    result = await db.item_categories.update_one(
        {"id": cat_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"success": True, "message": "Category deleted"}


# ── Products ──────────────────────────────────────────────

@router.get("/products")
async def list_products(
    admin: dict = Depends(get_current_admin),
    category_id: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
):
    org_id = _org(admin)
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    if category_id:
        query["category_id"] = category_id
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
        ]

    total = await db.item_products.count_documents(query)
    skip = (page - 1) * limit
    products = await db.item_products.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit).to_list(limit)

    # attach category name
    cat_ids = list({p["category_id"] for p in products if p.get("category_id")})
    if cat_ids:
        cats = await db.item_categories.find({"id": {"$in": cat_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(500)
        cat_map = {c["id"]: c["name"] for c in cats}
        for p in products:
            p["category_name"] = cat_map.get(p.get("category_id"), "")

    return {"products": products, "total": total, "page": page, "limit": limit, "pages": max(1, (total + limit - 1) // limit)}


@router.post("/products")
async def create_product(data: ItemProductCreate, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)

    # validate category
    cat = await db.item_categories.find_one({"id": data.category_id, "organization_id": org_id, "is_deleted": {"$ne": True}})
    if not cat:
        raise HTTPException(status_code=400, detail="Invalid category")

    if data.gst_slab not in GST_SLABS:
        raise HTTPException(status_code=400, detail=f"GST slab must be one of {GST_SLABS}")

    # duplicate SKU guard
    if data.sku:
        dup = await db.item_products.find_one({
            "organization_id": org_id,
            "sku": {"$regex": f"^{data.sku}$", "$options": "i"},
            "is_deleted": {"$ne": True},
        })
        if dup:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")

    product = ItemProduct(organization_id=org_id, created_by=admin.get("id"), **data.model_dump())
    await db.item_products.insert_one(product.model_dump())
    created = await db.item_products.find_one({"id": product.id}, {"_id": 0})
    created["category_name"] = cat.get("name", "")
    return created


@router.get("/products/{product_id}")
async def get_product(product_id: str, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    product = await db.item_products.find_one({"id": product_id, "organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.put("/products/{product_id}")
async def update_product(product_id: str, data: ItemProductUpdate, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    existing = await db.item_products.find_one({"id": product_id, "organization_id": org_id, "is_deleted": {"$ne": True}})
    if not existing:
        raise HTTPException(status_code=404, detail="Product not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")

    if "gst_slab" in updates and updates["gst_slab"] not in GST_SLABS:
        raise HTTPException(status_code=400, detail=f"GST slab must be one of {GST_SLABS}")

    if "category_id" in updates:
        cat = await db.item_categories.find_one({"id": updates["category_id"], "organization_id": org_id, "is_deleted": {"$ne": True}})
        if not cat:
            raise HTTPException(status_code=400, detail="Invalid category")

    updates["updated_at"] = get_ist_isoformat()
    await db.item_products.update_one({"id": product_id}, {"$set": updates})
    return await db.item_products.find_one({"id": product_id}, {"_id": 0})


@router.delete("/products/{product_id}")
async def delete_product(product_id: str, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    result = await db.item_products.update_one(
        {"id": product_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    # also soft-delete any bundles where this product is the source
    await db.item_bundles.update_many(
        {"source_product_id": product_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}},
    )
    return {"success": True, "message": "Product deleted"}


# ── Bundles ───────────────────────────────────────────────

@router.get("/bundles")
async def list_bundles(admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    bundles = await db.item_bundles.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).sort("created_at", -1).to_list(500)

    # enrich with product names
    all_pids = set()
    for b in bundles:
        all_pids.add(b["source_product_id"])
        all_pids.update(b.get("recommended_product_ids", []))
    if all_pids:
        prods = await db.item_products.find({"id": {"$in": list(all_pids)}}, {"_id": 0, "id": 1, "name": 1, "sku": 1}).to_list(500)
        pmap = {p["id"]: p for p in prods}
        for b in bundles:
            b["source_product"] = pmap.get(b["source_product_id"], {})
            b["recommended_products"] = [pmap.get(pid, {}) for pid in b.get("recommended_product_ids", [])]

    return {"bundles": bundles}


@router.post("/bundles")
async def create_bundle(data: ItemBundleCreate, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)

    # validate source product
    src = await db.item_products.find_one({"id": data.source_product_id, "organization_id": org_id, "is_deleted": {"$ne": True}})
    if not src:
        raise HTTPException(status_code=400, detail="Source product not found")

    # check for existing bundle on this source
    existing = await db.item_bundles.find_one({
        "organization_id": org_id,
        "source_product_id": data.source_product_id,
        "is_deleted": {"$ne": True},
    })
    if existing:
        raise HTTPException(status_code=400, detail="A bundle already exists for this product. Edit the existing one.")

    if not data.recommended_product_ids:
        raise HTTPException(status_code=400, detail="At least one recommended product is required")

    bundle = ItemBundle(organization_id=org_id, **data.model_dump())
    await db.item_bundles.insert_one(bundle.model_dump())
    return await db.item_bundles.find_one({"id": bundle.id}, {"_id": 0})


@router.put("/bundles/{bundle_id}")
async def update_bundle(bundle_id: str, data: ItemBundleUpdate, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    existing = await db.item_bundles.find_one({"id": bundle_id, "organization_id": org_id, "is_deleted": {"$ne": True}})
    if not existing:
        raise HTTPException(status_code=404, detail="Bundle not found")

    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    updates["updated_at"] = get_ist_isoformat()

    await db.item_bundles.update_one({"id": bundle_id}, {"$set": updates})
    return await db.item_bundles.find_one({"id": bundle_id}, {"_id": 0})


@router.delete("/bundles/{bundle_id}")
async def delete_bundle(bundle_id: str, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    result = await db.item_bundles.update_one(
        {"id": bundle_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Bundle not found")
    return {"success": True, "message": "Bundle deleted"}


# ── Suggestions (for quotation integration) ───────────────

@router.get("/products/{product_id}/suggestions")
async def get_product_suggestions(product_id: str, admin: dict = Depends(get_current_admin)):
    """Return bundle recommendations for a product (used during quotation creation)."""
    org_id = _org(admin)
    bundle = await db.item_bundles.find_one(
        {"organization_id": org_id, "source_product_id": product_id, "is_deleted": {"$ne": True}, "is_active": True},
        {"_id": 0},
    )
    if not bundle:
        return {"suggestions": []}

    rec_ids = bundle.get("recommended_product_ids", [])
    if not rec_ids:
        return {"suggestions": []}

    products = await db.item_products.find(
        {"id": {"$in": rec_ids}, "organization_id": org_id, "is_deleted": {"$ne": True}, "is_active": True},
        {"_id": 0},
    ).to_list(50)

    # attach category name
    cat_ids = list({p["category_id"] for p in products if p.get("category_id")})
    if cat_ids:
        cats = await db.item_categories.find({"id": {"$in": cat_ids}}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
        cat_map = {c["id"]: c["name"] for c in cats}
        for p in products:
            p["category_name"] = cat_map.get(p.get("category_id"), "")

    return {"suggestions": products, "bundle_description": bundle.get("description", "")}


# ── GST helper ────────────────────────────────────────────

@router.get("/gst-slabs")
async def get_gst_slabs(admin: dict = Depends(get_current_admin)):
    _org(admin)
    return {"slabs": [{"value": s, "label": f"{s}%"} for s in GST_SLABS]}
