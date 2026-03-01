"""
Engineer Visit Workflow
=======================
Handles the full field visit lifecycle:
  1. Start Visit (check-in) → timer starts
  2. Update diagnosis, problem, solution, resolution type
  3. Request Parts (auto-creates quotation draft)
  4. Checkout → logs duration, moves ticket to appropriate stage
"""

import uuid
import random
import string
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from pydantic import BaseModel
from services.auth import get_current_engineer, get_current_admin

logger = logging.getLogger(__name__)
router = APIRouter()
_db = None

IST = timezone(timedelta(hours=5, minutes=30))

def init_db(database):
    global _db
    _db = database

def now_ist():
    return datetime.now(IST).isoformat()


# ── Pydantic Models ──────────────────────────────────────

class StartVisitRequest(BaseModel):
    ticket_id: str
    notes: Optional[str] = None

class UpdateVisitRequest(BaseModel):
    problem_found: Optional[str] = None
    diagnosis: Optional[str] = None
    solution_applied: Optional[str] = None
    resolution_type: Optional[str] = None  # "fixed", "parts_needed", "escalation"
    notes: Optional[str] = None

class PartItem(BaseModel):
    product_id: Optional[str] = None
    product_name: str
    sku: Optional[str] = None
    hsn_code: Optional[str] = None
    quantity: int = 1
    unit_price: float = 0
    gst_slab: int = 18
    description: Optional[str] = None

class RequestPartsRequest(BaseModel):
    parts: List[PartItem]
    notes: Optional[str] = None

class CheckoutRequest(BaseModel):
    resolution_type: str  # "fixed", "parts_needed", "escalation"
    problem_found: Optional[str] = None
    diagnosis: Optional[str] = None
    solution_applied: Optional[str] = None
    notes: Optional[str] = None
    customer_name: Optional[str] = None


# ── Engineer ID resolution (reuse from job_acceptance pattern) ──

async def _resolve_eng(user: dict):
    email = user.get("email", "")
    org_id = user.get("organization_id")
    ids = set()
    name = user.get("name", email)

    for coll_name in ["engineers", "staff_users", "organization_members"]:
        doc = await _db[coll_name].find_one(
            {"email": email, "organization_id": org_id, "is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1}
        )
        if doc:
            ids.add(doc["id"])
            if doc.get("name"):
                name = doc["name"]

    if not ids:
        ids.add(user.get("id", ""))

    return {
        "id": user.get("id", list(ids)[0]),
        "all_ids": list(ids),
        "name": name,
        "email": email,
        "organization_id": org_id,
    }


# ── Helpers ──────────────────────────────────────────────

def _calc_line(item: dict) -> dict:
    qty = item.get("quantity", 1)
    price = item.get("unit_price", 0)
    slab = item.get("gst_slab", 18)
    base = price * qty
    gst = round(base * slab / 100, 2)
    item["gst_amount"] = gst
    item["line_total"] = round(base + gst, 2)
    return item

async def _gen_qnum(org_id: str) -> str:
    for _ in range(10):
        num = f"QT-{''.join(random.choices(string.digits, k=6))}"
        if not await _db.quotations.find_one({"organization_id": org_id, "quotation_number": num}):
            return num
    import time
    return f"QT-{int(time.time())}"


# ══════════════════════════════════════════════════════════
# ENGINEER ENDPOINTS
# ══════════════════════════════════════════════════════════

@router.post("/api/engineer/visit/start")
async def start_visit(data: StartVisitRequest, engineer: dict = Depends(get_current_engineer)):
    """Engineer starts a visit (check-in). Creates a visit record and starts timer."""
    eng = await _resolve_eng(engineer)
    org_id = eng["organization_id"]

    # Find the ticket
    ticket = await _db.tickets_v2.find_one({
        "id": data.ticket_id,
        "assigned_to_id": {"$in": eng["all_ids"]},
        "is_deleted": {"$ne": True},
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not assigned to you")

    # Check for existing active visit
    active = await _db.visits.find_one({
        "ticket_id": data.ticket_id,
        "engineer_id": eng["id"],
        "status": "in_progress",
    })
    if active:
        # Return existing visit
        active.pop("_id", None)
        return {"visit": active, "message": "Visit already in progress"}

    visit_id = str(uuid.uuid4())
    visit = {
        "id": visit_id,
        "organization_id": org_id,
        "ticket_id": data.ticket_id,
        "ticket_number": ticket.get("ticket_number"),
        "engineer_id": eng["id"],
        "engineer_name": eng["name"],
        "company_id": ticket.get("company_id"),
        "company_name": ticket.get("company_name"),
        "device_id": ticket.get("device_id"),
        "check_in_time": now_ist(),
        "check_out_time": None,
        "duration_minutes": None,
        "status": "in_progress",
        "problem_found": None,
        "diagnosis": None,
        "solution_applied": None,
        "resolution_type": None,  # fixed, parts_needed, escalation
        "parts_requested": [],
        "parts_request_id": None,
        "notes": data.notes,
        "customer_name": None,
        "created_at": now_ist(),
        "updated_at": now_ist(),
    }
    await _db.visits.insert_one(visit)
    visit.pop("_id", None)

    # Update ticket status
    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "visit_started",
        "description": f"{eng['name']} checked in and started visit",
        "user_name": eng["name"],
        "created_at": now_ist(),
    }
    await _db.tickets_v2.update_one(
        {"id": data.ticket_id},
        {"$set": {"current_stage_name": "In Progress", "updated_at": now_ist()},
         "$push": {"timeline": timeline_entry}}
    )

    return {"visit": visit, "message": "Visit started"}


@router.get("/api/engineer/visit/{ticket_id}")
async def get_visit(ticket_id: str, engineer: dict = Depends(get_current_engineer)):
    """Get the active or most recent visit for a ticket."""
    eng = await _resolve_eng(engineer)

    visit = await _db.visits.find_one(
        {"ticket_id": ticket_id, "engineer_id": {"$in": eng["all_ids"]}},
        {"_id": 0},
        sort=[("created_at", -1)]
    )
    return {"visit": visit}


@router.put("/api/engineer/visit/{visit_id}/update")
async def update_visit(visit_id: str, data: UpdateVisitRequest, engineer: dict = Depends(get_current_engineer)):
    """Update visit diagnosis, problem, solution while visit is in progress."""
    eng = await _resolve_eng(engineer)

    visit = await _db.visits.find_one({
        "id": visit_id, "engineer_id": {"$in": eng["all_ids"]}, "status": "in_progress"
    })
    if not visit:
        raise HTTPException(status_code=404, detail="Active visit not found")

    updates = {"updated_at": now_ist()}
    for field in ["problem_found", "diagnosis", "solution_applied", "resolution_type", "notes"]:
        val = getattr(data, field, None)
        if val is not None:
            updates[field] = val

    await _db.visits.update_one({"id": visit_id}, {"$set": updates})
    updated = await _db.visits.find_one({"id": visit_id}, {"_id": 0})
    return {"visit": updated, "message": "Visit updated"}


@router.post("/api/engineer/visit/{visit_id}/request-parts")
async def request_parts(visit_id: str, data: RequestPartsRequest, engineer: dict = Depends(get_current_engineer)):
    """Engineer requests parts. Auto-creates a quotation draft for back office."""
    eng = await _resolve_eng(engineer)
    org_id = eng["organization_id"]

    visit = await _db.visits.find_one({
        "id": visit_id, "engineer_id": {"$in": eng["all_ids"]}, "status": "in_progress"
    })
    if not visit:
        raise HTTPException(status_code=404, detail="Active visit not found")

    if not data.parts:
        raise HTTPException(status_code=400, detail="At least one part is required")

    # Create parts request record
    request_id = str(uuid.uuid4())
    items = []
    for p in data.parts:
        item = p.model_dump()
        item = _calc_line(item)
        items.append(item)

    subtotal = sum(i.get("unit_price", 0) * i.get("quantity", 1) for i in items)
    total_gst = sum(i.get("gst_amount", 0) for i in items)

    parts_request = {
        "id": request_id,
        "organization_id": org_id,
        "visit_id": visit_id,
        "ticket_id": visit.get("ticket_id"),
        "ticket_number": visit.get("ticket_number"),
        "engineer_id": eng["id"],
        "engineer_name": eng["name"],
        "company_id": visit.get("company_id"),
        "company_name": visit.get("company_name"),
        "device_id": visit.get("device_id"),
        "items": items,
        "subtotal": round(subtotal, 2),
        "total_gst": round(total_gst, 2),
        "grand_total": round(subtotal + total_gst, 2),
        "notes": data.notes,
        "status": "pending",  # pending → quoted → approved → procured → delivered
        "quotation_id": None,
        "created_at": now_ist(),
        "updated_at": now_ist(),
    }
    await _db.parts_requests.insert_one(parts_request)
    parts_request.pop("_id", None)

    # Auto-create quotation draft
    quotation_id = str(uuid.uuid4())
    quotation = {
        "id": quotation_id,
        "organization_id": org_id,
        "quotation_number": await _gen_qnum(org_id),
        "ticket_id": visit.get("ticket_id"),
        "ticket_number": visit.get("ticket_number"),
        "company_id": visit.get("company_id"),
        "company_name": visit.get("company_name"),
        "parts_request_id": request_id,
        "items": items,
        "subtotal": round(subtotal, 2),
        "total_gst": round(total_gst, 2),
        "grand_total": round(subtotal + total_gst, 2),
        "status": "draft",
        "notes": f"Parts requested by {eng['name']} during field visit.\n{data.notes or ''}".strip(),
        "terms_and_conditions": None,
        "valid_days": 30,
        "created_by_id": eng["id"],
        "created_by_name": eng["name"],
        "is_deleted": False,
        "created_at": now_ist(),
        "updated_at": now_ist(),
    }
    await _db.quotations.insert_one(quotation)

    # Link quotation back to parts request
    await _db.parts_requests.update_one(
        {"id": request_id},
        {"$set": {"quotation_id": quotation_id, "status": "quoted"}}
    )

    # Update visit
    await _db.visits.update_one(
        {"id": visit_id},
        {"$set": {
            "parts_requested": [p.model_dump() for p in data.parts],
            "parts_request_id": request_id,
            "resolution_type": "parts_needed",
            "updated_at": now_ist(),
        }}
    )

    # Timeline
    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "parts_requested",
        "description": f"{eng['name']} requested {len(data.parts)} part(s) — quotation {quotation['quotation_number']} auto-created",
        "user_name": eng["name"],
        "created_at": now_ist(),
    }
    await _db.tickets_v2.update_one(
        {"id": visit.get("ticket_id")},
        {"$push": {"timeline": timeline_entry}}
    )

    return {
        "parts_request": parts_request,
        "quotation_id": quotation_id,
        "quotation_number": quotation["quotation_number"],
        "message": f"Parts requested. Quotation {quotation['quotation_number']} created as draft for back office."
    }


@router.post("/api/engineer/visit/{visit_id}/checkout")
async def checkout_visit(visit_id: str, data: CheckoutRequest, engineer: dict = Depends(get_current_engineer)):
    """Engineer checks out. Logs duration, updates ticket stage."""
    eng = await _resolve_eng(engineer)

    visit = await _db.visits.find_one({
        "id": visit_id, "engineer_id": {"$in": eng["all_ids"]}, "status": "in_progress"
    })
    if not visit:
        raise HTTPException(status_code=404, detail="Active visit not found")

    checkout_time = now_ist()
    checkin_time = visit.get("check_in_time", "")

    # Calculate duration
    duration_minutes = None
    try:
        cin = datetime.fromisoformat(checkin_time)
        cout = datetime.fromisoformat(checkout_time)
        duration_minutes = int((cout - cin).total_seconds() / 60)
    except (ValueError, TypeError):
        pass

    # Determine next ticket stage based on resolution
    resolution = data.resolution_type
    stage_map = {
        "fixed": "Work Done",
        "parts_needed": "Awaiting Parts",
        "escalation": "Escalated",
    }
    next_stage = stage_map.get(resolution, "Work Done")

    # Update visit
    visit_updates = {
        "check_out_time": checkout_time,
        "duration_minutes": duration_minutes,
        "status": "completed",
        "resolution_type": resolution,
        "customer_name": data.customer_name,
        "updated_at": checkout_time,
    }
    for field in ["problem_found", "diagnosis", "solution_applied", "notes"]:
        val = getattr(data, field, None)
        if val is not None:
            visit_updates[field] = val

    await _db.visits.update_one({"id": visit_id}, {"$set": visit_updates})

    # Auto-deduct inventory for parts used during this visit
    parts_used = visit.get("parts_requested", [])
    if parts_used:
        org_id = eng["organization_id"]
        for part in parts_used:
            pid = part.get("product_id")
            if not pid:
                continue
            qty = part.get("quantity", 1)
            # Deduct from inventory
            await _db.inventory.update_one(
                {"organization_id": org_id, "product_id": pid},
                {"$inc": {"quantity_in_stock": -qty, "total_used": qty},
                 "$set": {"updated_at": checkout_time}}
            )
            # Log transaction
            await _db.inventory_transactions.insert_one({
                "id": str(uuid.uuid4()),
                "organization_id": org_id,
                "product_id": pid,
                "product_name": part.get("product_name", ""),
                "type": "used",
                "quantity": qty,
                "ticket_id": visit.get("ticket_id"),
                "ticket_number": visit.get("ticket_number"),
                "company_name": visit.get("company_name"),
                "visit_id": visit_id,
                "engineer_name": eng["name"],
                "reference": f"Job #{visit.get('ticket_number')}",
                "notes": f"Used during visit by {eng['name']}",
                "performed_by": eng["name"],
                "performed_by_id": eng["id"],
                "created_at": checkout_time,
            })

        # Auto-create/update pending bill for this ticket
        from routes.inventory import upsert_pending_bill
        await upsert_pending_bill(org_id, visit.get("ticket_id"), parts_used, visit_id, eng["name"])

    # Update ticket stage
    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "visit_completed",
        "description": f"{eng['name']} completed visit ({duration_minutes or '?'} min). Resolution: {resolution}",
        "user_name": eng["name"],
        "created_at": checkout_time,
    }
    ticket_updates = {
        "current_stage_name": next_stage,
        "updated_at": checkout_time,
    }
    if resolution == "fixed":
        ticket_updates["is_open"] = False
        ticket_updates["closed_at"] = checkout_time

    await _db.tickets_v2.update_one(
        {"id": visit.get("ticket_id")},
        {"$set": ticket_updates, "$push": {"timeline": timeline_entry}}
    )

    updated_visit = await _db.visits.find_one({"id": visit_id}, {"_id": 0})
    return {"visit": updated_visit, "next_stage": next_stage, "message": f"Visit completed. Ticket moved to '{next_stage}'"}


@router.get("/api/engineer/visit/history/{ticket_id}")
async def get_visit_history(ticket_id: str, engineer: dict = Depends(get_current_engineer)):
    """Get all visits for a ticket."""
    eng = await _resolve_eng(engineer)
    visits = await _db.visits.find(
        {"ticket_id": ticket_id, "organization_id": eng["organization_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(50)
    return {"visits": visits}


# ══════════════════════════════════════════════════════════
# ADMIN ENDPOINTS - Parts Requests
# ══════════════════════════════════════════════════════════

@router.get("/api/admin/parts-requests")
async def list_parts_requests(
    admin: dict = Depends(get_current_admin),
    status: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
):
    """List all parts requests for the organization."""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    query = {"organization_id": org_id}
    if status:
        query["status"] = status

    total = await _db.parts_requests.count_documents(query)
    skip = (page - 1) * limit
    docs = await _db.parts_requests.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"parts_requests": docs, "total": total, "page": page}


@router.put("/api/admin/parts-requests/{request_id}/status")
async def update_parts_request_status(
    request_id: str,
    status: str = Query(..., description="New status: pending, quoted, approved, procured, delivered"),
    admin: dict = Depends(get_current_admin),
):
    """Admin updates parts request status."""
    org_id = admin.get("organization_id")
    pr = await _db.parts_requests.find_one({"id": request_id, "organization_id": org_id})
    if not pr:
        raise HTTPException(status_code=404, detail="Parts request not found")

    valid = ["pending", "quoted", "approved", "procured", "delivered"]
    if status not in valid:
        raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {valid}")

    await _db.parts_requests.update_one(
        {"id": request_id},
        {"$set": {"status": status, "updated_at": now_ist()}}
    )

    # If approved, add timeline to ticket
    if status == "approved":
        timeline_entry = {
            "id": str(uuid.uuid4()),
            "type": "parts_approved",
            "description": "Parts request approved. Procurement in progress.",
            "user_name": admin.get("name", "Admin"),
            "created_at": now_ist(),
        }
        await _db.tickets_v2.update_one(
            {"id": pr.get("ticket_id")},
            {"$push": {"timeline": timeline_entry}}
        )

    if status == "delivered":
        timeline_entry = {
            "id": str(uuid.uuid4()),
            "type": "parts_delivered",
            "description": "Parts delivered. Ready for engineer revisit.",
            "user_name": admin.get("name", "Admin"),
            "created_at": now_ist(),
        }
        await _db.tickets_v2.update_one(
            {"id": pr.get("ticket_id")},
            {"$set": {"current_stage_name": "Parts Delivered"},
             "$push": {"timeline": timeline_entry}}
        )

    return {"status": status, "message": f"Parts request updated to '{status}'"}
