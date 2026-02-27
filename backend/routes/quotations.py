"""
Quotation API Routes
====================
Create, manage, and send quotations to companies.
Products are picked from Item Master with auto GST calculation.
"""
import uuid
import random
import string
import logging
from typing import Optional, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin, get_current_company_user
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Quotations"])


# ── Pydantic Models ──────────────────────────────────────

class QuotationLineItem(BaseModel):
    product_id: Optional[str] = None
    product_name: str
    sku: Optional[str] = None
    hsn_code: Optional[str] = None
    quantity: int = 1
    unit_price: float = 0
    gst_slab: int = 18
    gst_amount: float = 0
    line_total: float = 0          # unit_price * quantity + gst
    description: Optional[str] = None


class QuotationCreate(BaseModel):
    ticket_id: Optional[str] = None
    ticket_number: Optional[str] = None
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    items: List[QuotationLineItem]
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    valid_days: int = 30


class QuotationUpdate(BaseModel):
    items: Optional[List[QuotationLineItem]] = None
    notes: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    valid_days: Optional[int] = None


# ── Helpers ───────────────────────────────────────────────

def _org(admin: dict) -> str:
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    return org_id


def _calc_line(item: dict) -> dict:
    """Recalculate a single line item's GST and totals."""
    qty = item.get("quantity", 1)
    price = item.get("unit_price", 0)
    slab = item.get("gst_slab", 18)
    base = price * qty
    gst = round(base * slab / 100, 2)
    item["gst_amount"] = gst
    item["line_total"] = round(base + gst, 2)
    return item


def _calc_totals(items: list) -> dict:
    """Return subtotal, total_gst, grand_total from a list of line items."""
    subtotal = sum(i.get("unit_price", 0) * i.get("quantity", 1) for i in items)
    total_gst = sum(i.get("gst_amount", 0) for i in items)
    return {
        "subtotal": round(subtotal, 2),
        "total_gst": round(total_gst, 2),
        "grand_total": round(subtotal + total_gst, 2),
    }


async def _gen_qnum(org_id: str) -> str:
    for _ in range(10):
        num = f"QT-{''.join(random.choices(string.digits, k=6))}"
        if not await db.quotations.find_one({"organization_id": org_id, "quotation_number": num}):
            return num
    import time
    return f"QT-{int(time.time())}"


# ── Admin Endpoints ───────────────────────────────────────

@router.get("/api/admin/quotations")
async def list_quotations(
    admin: dict = Depends(get_current_admin),
    status: Optional[str] = None,
    ticket_id: Optional[str] = None,
    company_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
):
    org_id = _org(admin)
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    if status:
        query["status"] = status
    if ticket_id:
        query["ticket_id"] = ticket_id
    if company_id:
        query["company_id"] = company_id

    total = await db.quotations.count_documents(query)
    skip = (page - 1) * limit
    docs = await db.quotations.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"quotations": docs, "total": total, "page": page}


@router.get("/api/admin/quotations/{quotation_id}")
async def get_quotation(quotation_id: str, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    doc = await db.quotations.find_one({"id": quotation_id, "organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not doc:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return doc


@router.post("/api/admin/quotations")
async def create_quotation(data: QuotationCreate, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    if not data.items:
        raise HTTPException(status_code=400, detail="At least one line item is required")

    items = [_calc_line(i.model_dump()) for i in data.items]
    totals = _calc_totals(items)

    doc = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "quotation_number": await _gen_qnum(org_id),
        "ticket_id": data.ticket_id,
        "ticket_number": data.ticket_number,
        "company_id": data.company_id,
        "company_name": data.company_name,
        "items": items,
        **totals,
        "status": "draft",
        "notes": data.notes,
        "terms_and_conditions": data.terms_and_conditions,
        "valid_days": data.valid_days,
        "created_by_id": admin.get("id"),
        "created_by_name": admin.get("name", "Admin"),
        "is_deleted": False,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
    }
    await db.quotations.insert_one(doc)
    doc.pop("_id", None)
    return doc


@router.put("/api/admin/quotations/{quotation_id}")
async def update_quotation(quotation_id: str, data: QuotationUpdate, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    existing = await db.quotations.find_one({"id": quotation_id, "organization_id": org_id, "is_deleted": {"$ne": True}})
    if not existing:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if existing.get("status") not in ("draft", None):
        raise HTTPException(status_code=400, detail="Only draft quotations can be edited")

    updates = {}
    if data.items is not None:
        items = [_calc_line(i.model_dump()) for i in data.items]
        updates["items"] = items
        updates.update(_calc_totals(items))
    if data.notes is not None:
        updates["notes"] = data.notes
    if data.terms_and_conditions is not None:
        updates["terms_and_conditions"] = data.terms_and_conditions
    if data.valid_days is not None:
        updates["valid_days"] = data.valid_days

    if not updates:
        raise HTTPException(status_code=400, detail="Nothing to update")
    updates["updated_at"] = get_ist_isoformat()

    await db.quotations.update_one({"id": quotation_id}, {"$set": updates})
    return await db.quotations.find_one({"id": quotation_id}, {"_id": 0})


@router.post("/api/admin/quotations/{quotation_id}/send")
async def send_quotation(quotation_id: str, admin: dict = Depends(get_current_admin)):
    """Mark quotation as sent (visible to company)."""
    org_id = _org(admin)
    existing = await db.quotations.find_one({"id": quotation_id, "organization_id": org_id, "is_deleted": {"$ne": True}})
    if not existing:
        raise HTTPException(status_code=404, detail="Quotation not found")
    if existing.get("status") not in ("draft",):
        raise HTTPException(status_code=400, detail="Quotation already sent")

    await db.quotations.update_one({"id": quotation_id}, {"$set": {
        "status": "sent",
        "sent_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
    }})
    return await db.quotations.find_one({"id": quotation_id}, {"_id": 0})


@router.delete("/api/admin/quotations/{quotation_id}")
async def delete_quotation(quotation_id: str, admin: dict = Depends(get_current_admin)):
    org_id = _org(admin)
    result = await db.quotations.update_one(
        {"id": quotation_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}},
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return {"success": True, "message": "Quotation deleted"}


# ── Company Endpoints ─────────────────────────────────────

@router.get("/api/company/quotations")
async def company_list_quotations(user: dict = Depends(get_current_company_user)):
    company_id = user.get("company_id")
    org_id = user.get("organization_id")
    if not company_id:
        raise HTTPException(status_code=403, detail="Company context required")

    query = {"company_id": company_id, "is_deleted": {"$ne": True}, "status": {"$ne": "draft"}}
    if org_id:
        query["organization_id"] = org_id

    docs = await db.quotations.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    return {"quotations": docs}


@router.get("/api/company/quotations/{quotation_id}")
async def company_get_quotation(quotation_id: str, user: dict = Depends(get_current_company_user)):
    company_id = user.get("company_id")
    doc = await db.quotations.find_one(
        {"id": quotation_id, "company_id": company_id, "is_deleted": {"$ne": True}, "status": {"$ne": "draft"}},
        {"_id": 0},
    )
    if not doc:
        raise HTTPException(status_code=404, detail="Quotation not found")
    return doc


@router.post("/api/company/quotations/{quotation_id}/respond")
async def company_respond_quotation(
    quotation_id: str,
    approved: bool = Query(...),
    notes: Optional[str] = None,
    user: dict = Depends(get_current_company_user),
):
    company_id = user.get("company_id")
    existing = await db.quotations.find_one(
        {"id": quotation_id, "company_id": company_id, "is_deleted": {"$ne": True}, "status": "sent"},
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Quotation not found or already responded")

    new_status = "approved" if approved else "rejected"
    updates = {
        "status": new_status,
        "responded_at": get_ist_isoformat(),
        "responded_by_id": user.get("id"),
        "responded_by_name": user.get("name", ""),
        "response_notes": notes,
        "updated_at": get_ist_isoformat(),
    }
    await db.quotations.update_one({"id": quotation_id}, {"$set": updates})
    return await db.quotations.find_one({"id": quotation_id}, {"_id": 0})
