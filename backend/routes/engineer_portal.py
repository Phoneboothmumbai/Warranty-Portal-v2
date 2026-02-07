"""
Engineer Portal API Routes
===========================
Comprehensive endpoints for technician/engineer portal with full workflow support.
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File, Form
from pydantic import BaseModel, Field
from services.auth import get_current_engineer
from database import db
from utils.helpers import get_ist_isoformat
import base64

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/engineer", tags=["Engineer Portal"])


# ==================== REQUEST/RESPONSE MODELS ====================

class DiagnosisUpdate(BaseModel):
    """Issue diagnosis and findings"""
    problem_identified: str
    root_cause: Optional[str] = None
    observations: Optional[str] = None
    photos: List[str] = Field(default_factory=list)  # List of photo URLs


class ResolutionRequest(BaseModel):
    """Resolution details"""
    resolution_summary: str
    actions_taken: List[str] = Field(default_factory=list)
    recommendations: Optional[str] = None


class PartRequestItem(BaseModel):
    """Part request from engineer"""
    item_id: Optional[str] = None  # From inventory
    item_name: str  # Required for manual entry
    item_description: Optional[str] = None
    quantity: int = 1
    urgency: str = "normal"  # normal, urgent, critical
    notes: Optional[str] = None


class PendingPartsRequest(BaseModel):
    """Mark ticket as pending parts"""
    diagnosis: DiagnosisUpdate
    parts_required: List[PartRequestItem]
    remarks: str  # Mandatory remarks


class CloseTicketRequest(BaseModel):
    """Close ticket with final details"""
    final_findings: str
    solution_details: str
    customer_feedback: Optional[str] = None
    customer_signature: Optional[str] = None


class PhotoUploadResponse(BaseModel):
    """Photo upload response"""
    url: str
    filename: str
    uploaded_at: str


# ==================== DASHBOARD & TICKETS ====================

@router.get("/dashboard/stats")
async def get_dashboard_stats(engineer: dict = Depends(get_current_engineer)):
    """Get dashboard statistics for engineer"""
    engineer_id = engineer["id"]
    
    # Get ticket counts by status
    pipeline = [
        {"$match": {
            "assigned_to_id": engineer_id,
            "is_deleted": {"$ne": True},
            "status": {"$nin": ["closed", "cancelled"]}
        }},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1}
        }}
    ]
    
    status_counts = {}
    async for doc in db.service_tickets_new.aggregate(pipeline):
        status_counts[doc["_id"]] = doc["count"]
    
    # Get visit counts
    today = datetime.now().strftime("%Y-%m-%d")
    
    visits_today = await db.service_visits_new.count_documents({
        "technician_id": engineer_id,
        "scheduled_date": today,
        "is_deleted": {"$ne": True}
    })
    
    visits_in_progress = await db.service_visits_new.count_documents({
        "technician_id": engineer_id,
        "status": {"$in": ["in_progress", "on_site"]},
        "is_deleted": {"$ne": True}
    })
    
    visits_completed_today = await db.service_visits_new.count_documents({
        "technician_id": engineer_id,
        "status": "completed",
        "is_deleted": {"$ne": True},
        "check_out_time": {"$regex": f"^{today}"}
    })
    
    return {
        "tickets": {
            "pending_acceptance": status_counts.get("pending_acceptance", 0),
            "assigned": status_counts.get("assigned", 0),
            "in_progress": status_counts.get("in_progress", 0),
            "pending_parts": status_counts.get("pending_parts", 0),
            "total_active": sum(status_counts.values())
        },
        "visits": {
            "scheduled_today": visits_today,
            "in_progress": visits_in_progress,
            "completed_today": visits_completed_today
        },
        "date": today
    }


@router.get("/tickets")
async def get_engineer_tickets(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=100),
    engineer: dict = Depends(get_current_engineer)
):
    """Get all tickets assigned to engineer with filtering"""
    engineer_id = engineer["id"]
    
    query = {
        "assigned_to_id": engineer_id,
        "is_deleted": {"$ne": True}
    }
    
    # Status filter
    if status:
        if status == "active":
            query["status"] = {"$nin": ["closed", "cancelled"]}
        else:
            query["status"] = status
    else:
        # Default: active tickets
        query["status"] = {"$nin": ["closed", "cancelled"]}
    
    # Priority filter
    if priority:
        query["priority"] = priority
    
    # Date range filter
    if date_from:
        query["created_at"] = {"$gte": date_from}
    if date_to:
        if "created_at" in query:
            query["created_at"]["$lte"] = date_to + "T23:59:59"
        else:
            query["created_at"] = {"$lte": date_to + "T23:59:59"}
    
    # Search filter
    if search:
        query["$or"] = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.service_tickets_new.count_documents(query)
    skip = (page - 1) * limit
    
    tickets = await db.service_tickets_new.find(
        query, {"_id": 0}
    ).sort([("is_urgent", -1), ("priority", -1), ("created_at", -1)]).skip(skip).limit(limit).to_list(limit)
    
    # Group by status for UI convenience
    grouped = {
        "pending_acceptance": [],
        "assigned": [],
        "in_progress": [],
        "pending_parts": [],
        "completed": [],
        "closed": []
    }
    
    for ticket in tickets:
        status_key = ticket.get("status", "new")
        if status_key in grouped:
            grouped[status_key].append(ticket)
    
    return {
        "tickets": tickets,
        "grouped": grouped,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/tickets/{ticket_id}")
async def get_ticket_detail(
    ticket_id: str,
    engineer: dict = Depends(get_current_engineer)
):
    """Get detailed ticket information for engineer"""
    engineer_id = engineer["id"]
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "assigned_to_id": engineer_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not assigned to you")
    
    # Get all visits for this ticket
    visits = await db.service_visits_new.find({
        "ticket_id": ticket_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("visit_number", 1).to_list(50)
    
    # Get parts requests
    parts_requests = await db.ticket_part_requests.find({
        "ticket_id": ticket_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(50)
    
    # Get parts issued
    parts_issued = await db.ticket_part_issues.find({
        "ticket_id": ticket_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(50)
    
    # Get quotation if exists
    quotation = None
    if ticket.get("quotation_id"):
        quotation = await db.quotations.find_one({
            "id": ticket.get("quotation_id"),
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
    
    # Calculate SLA info
    sla_info = None
    if ticket.get("sla_due_at"):
        due_at = datetime.fromisoformat(ticket["sla_due_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        is_breached = now > due_at
        time_remaining = None if is_breached else int((due_at - now).total_seconds() / 3600)
        
        sla_info = {
            "due_at": ticket["sla_due_at"],
            "response_due_at": ticket.get("sla_response_due_at"),
            "is_breached": is_breached,
            "time_remaining_hours": time_remaining,
            "response_at": ticket.get("first_response_at")
        }
    
    ticket["visits"] = visits
    ticket["parts_requests"] = parts_requests
    ticket["parts_issued"] = parts_issued
    ticket["quotation"] = quotation
    ticket["sla_info"] = sla_info
    
    return ticket


# ==================== VISIT MANAGEMENT ====================

@router.get("/visits")
async def get_engineer_visits(
    status: Optional[str] = None,
    date: Optional[str] = None,
    engineer: dict = Depends(get_current_engineer)
):
    """Get all visits for engineer"""
    engineer_id = engineer["id"]
    
    query = {
        "technician_id": engineer_id,
        "is_deleted": {"$ne": True}
    }
    
    if status:
        query["status"] = status
    
    if date:
        query["scheduled_date"] = date
    
    visits = await db.service_visits_new.find(
        query, {"_id": 0}
    ).sort([("scheduled_date", -1), ("scheduled_time_from", 1)]).to_list(100)
    
    # Enrich with ticket info
    for visit in visits:
        ticket = await db.service_tickets_new.find_one(
            {"id": visit["ticket_id"]},
            {"_id": 0, "title": 1, "company_name": 1, "priority": 1, "contact": 1, "location": 1}
        )
        visit["ticket"] = ticket
    
    return {"visits": visits}


@router.get("/visits/{visit_id}")
async def get_visit_detail(
    visit_id: str,
    engineer: dict = Depends(get_current_engineer)
):
    """Get visit detail"""
    engineer_id = engineer["id"]
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "technician_id": engineer_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Get ticket details
    ticket = await db.service_tickets_new.find_one(
        {"id": visit["ticket_id"]},
        {"_id": 0, "ticket_number": 1, "title": 1, "description": 1, 
         "company_name": 1, "contact": 1, "location": 1, "device_name": 1, 
         "device_serial": 1, "asset_tag": 1, "priority": 1, "is_urgent": 1,
         "warranty_status": 1}
    )
    
    # Get previous visits for this ticket
    previous_visits = await db.service_visits_new.find({
        "ticket_id": visit["ticket_id"],
        "visit_number": {"$lt": visit.get("visit_number", 1)},
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "visit_number": 1, "status": 1, "scheduled_date": 1, 
        "findings": 1, "problem_found": 1, "diagnosis": 1, "resolution": 1,
        "action_taken": 1, "technician_name": 1}).sort("visit_number", 1).to_list(20)
    
    # Get parts issued for this visit
    parts_issued = await db.ticket_part_issues.find({
        "visit_id": visit_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(50)
    
    visit["ticket"] = ticket
    visit["previous_visits"] = previous_visits
    visit["parts_issued"] = parts_issued
    
    return visit


@router.post("/visits/{visit_id}/start")
async def start_visit(
    visit_id: str,
    engineer: dict = Depends(get_current_engineer)
):
    """Start a visit - auto captures timestamp"""
    engineer_id = engineer["id"]
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "technician_id": engineer_id,
        "is_deleted": {"$ne": True}
    })
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if visit.get("status") not in ["scheduled", "in_transit"]:
        raise HTTPException(status_code=400, detail=f"Cannot start visit in {visit.get('status')} status")
    
    now = get_ist_isoformat()
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {"$set": {
            "status": "in_progress",
            "start_time": now,
            "check_in_time": now,
            "updated_at": now
        }}
    )
    
    # Update ticket status to in_progress
    ticket = await db.service_tickets_new.find_one({"id": visit["ticket_id"]})
    if ticket and ticket.get("status") in ["assigned", "pending_acceptance"]:
        status_change = {
            "id": str(uuid.uuid4()),
            "from_status": ticket.get("status"),
            "to_status": "in_progress",
            "changed_at": now,
            "changed_by_id": engineer_id,
            "changed_by_name": engineer.get("name"),
            "notes": f"Visit #{visit.get('visit_number', 1)} started"
        }
        
        update_data = {
            "status": "in_progress",
            "updated_at": now
        }
        
        # Set first response time if not already set
        if not ticket.get("first_response_at"):
            update_data["first_response_at"] = now
        
        await db.service_tickets_new.update_one(
            {"id": visit["ticket_id"]},
            {
                "$set": update_data,
                "$push": {"status_history": status_change}
            }
        )
    
    logger.info(f"Visit {visit_id} started by engineer {engineer.get('name')}")
    
    return await db.service_visits_new.find_one({"id": visit_id}, {"_id": 0})


@router.post("/visits/{visit_id}/end")
async def end_visit(
    visit_id: str,
    engineer: dict = Depends(get_current_engineer)
):
    """End a visit - auto captures timestamp and calculates duration"""
    engineer_id = engineer["id"]
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "technician_id": engineer_id,
        "is_deleted": {"$ne": True}
    })
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if visit.get("status") != "in_progress":
        raise HTTPException(status_code=400, detail="Visit must be in_progress to end")
    
    now = get_ist_isoformat()
    
    # Calculate duration
    duration_minutes = 0
    if visit.get("start_time"):
        try:
            start_dt = datetime.fromisoformat(visit["start_time"].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        except Exception as e:
            logger.error(f"Error calculating duration: {e}")
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {"$set": {
            "end_time": now,
            "check_out_time": now,
            "duration_minutes": duration_minutes,
            "updated_at": now
        }}
    )
    
    # Update ticket total time
    visits = await db.service_visits_new.find(
        {"ticket_id": visit["ticket_id"], "is_deleted": {"$ne": True}},
        {"duration_minutes": 1}
    ).to_list(100)
    
    total_time = sum(v.get("duration_minutes", 0) for v in visits)
    
    await db.service_tickets_new.update_one(
        {"id": visit["ticket_id"]},
        {"$set": {"total_time_minutes": total_time, "updated_at": now}}
    )
    
    logger.info(f"Visit {visit_id} ended. Duration: {duration_minutes} minutes")
    
    return await db.service_visits_new.find_one({"id": visit_id}, {"_id": 0})


# ==================== DIAGNOSIS & FINDINGS ====================

@router.post("/visits/{visit_id}/diagnosis")
async def update_diagnosis(
    visit_id: str,
    data: DiagnosisUpdate,
    engineer: dict = Depends(get_current_engineer)
):
    """Update diagnosis and findings for a visit"""
    engineer_id = engineer["id"]
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "technician_id": engineer_id,
        "is_deleted": {"$ne": True}
    })
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if visit.get("status") not in ["in_progress", "on_site"]:
        raise HTTPException(status_code=400, detail="Can only update diagnosis during active visit")
    
    now = get_ist_isoformat()
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {"$set": {
            "problem_found": data.problem_identified,
            "diagnosis": data.root_cause,
            "findings": data.observations,
            "diagnostics": data.observations,
            "photos": data.photos,
            "updated_at": now
        }}
    )
    
    return {"success": True, "message": "Diagnosis updated"}


@router.post("/visits/{visit_id}/photos")
async def upload_visit_photo(
    visit_id: str,
    file: UploadFile = File(...),
    caption: str = Form(default=""),
    engineer: dict = Depends(get_current_engineer)
):
    """Upload photo for a visit (stored as base64)"""
    engineer_id = engineer["id"]
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "technician_id": engineer_id,
        "is_deleted": {"$ne": True}
    })
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Read and encode file
    contents = await file.read()
    
    if len(contents) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB.")
    
    # Generate unique filename
    ext = file.filename.split('.')[-1] if '.' in file.filename else 'jpg'
    filename = f"{visit_id}_{uuid.uuid4().hex[:8]}.{ext}"
    
    # Store as base64 data URL
    base64_data = base64.b64encode(contents).decode('utf-8')
    content_type = file.content_type or f"image/{ext}"
    photo_url = f"data:{content_type};base64,{base64_data}"
    
    now = get_ist_isoformat()
    
    photo_entry = {
        "id": str(uuid.uuid4()),
        "url": photo_url,
        "filename": filename,
        "caption": caption,
        "uploaded_at": now,
        "uploaded_by_id": engineer_id,
        "uploaded_by_name": engineer.get("name")
    }
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {
            "$push": {"photos": photo_url, "photo_attachments": photo_entry},
            "$set": {"updated_at": now}
        }
    )
    
    return PhotoUploadResponse(url=photo_url, filename=filename, uploaded_at=now)


# ==================== RESOLUTION & PENDING PARTS ====================

@router.post("/visits/{visit_id}/resolve")
async def resolve_visit(
    visit_id: str,
    data: ResolutionRequest,
    engineer: dict = Depends(get_current_engineer)
):
    """Mark visit as resolved with resolution details"""
    engineer_id = engineer["id"]
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "technician_id": engineer_id,
        "is_deleted": {"$ne": True}
    })
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if visit.get("status") not in ["in_progress", "on_site"]:
        raise HTTPException(status_code=400, detail="Visit must be in progress to resolve")
    
    if not visit.get("problem_found") and not visit.get("diagnosis"):
        raise HTTPException(status_code=400, detail="Please record diagnosis before resolving")
    
    now = get_ist_isoformat()
    
    # Calculate duration if not already done
    duration_minutes = visit.get("duration_minutes", 0)
    if visit.get("start_time") and not visit.get("end_time"):
        try:
            start_dt = datetime.fromisoformat(visit["start_time"].replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        except Exception as e:
            logger.error(f"Error calculating duration: {e}")
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {"$set": {
            "status": "completed",
            "resolution": data.resolution_summary,
            "actions_taken": data.actions_taken,
            "recommendations": data.recommendations,
            "work_summary": data.resolution_summary,
            "outcome": "resolved",
            "end_time": now,
            "check_out_time": now,
            "duration_minutes": duration_minutes,
            "is_completed": True,
            "updated_at": now
        }}
    )
    
    # Update ticket status to completed
    ticket = await db.service_tickets_new.find_one({"id": visit["ticket_id"]})
    if ticket:
        status_change = {
            "id": str(uuid.uuid4()),
            "from_status": ticket.get("status"),
            "to_status": "completed",
            "changed_at": now,
            "changed_by_id": engineer_id,
            "changed_by_name": engineer.get("name"),
            "notes": f"Resolved: {data.resolution_summary}"
        }
        
        await db.service_tickets_new.update_one(
            {"id": visit["ticket_id"]},
            {
                "$set": {
                    "status": "completed",
                    "resolution_summary": data.resolution_summary,
                    "resolved_at": now,
                    "resolved_by_id": engineer_id,
                    "resolved_by_name": engineer.get("name"),
                    "updated_at": now
                },
                "$push": {"status_history": status_change}
            }
        )
    
    logger.info(f"Visit {visit_id} resolved by {engineer.get('name')}")
    
    return {
        "success": True,
        "message": "Visit resolved successfully",
        "status": "completed"
    }


@router.post("/visits/{visit_id}/pending-parts")
async def mark_pending_parts(
    visit_id: str,
    data: PendingPartsRequest,
    engineer: dict = Depends(get_current_engineer)
):
    """Mark visit as pending parts - auto-creates draft quotation"""
    engineer_id = engineer["id"]
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "technician_id": engineer_id,
        "is_deleted": {"$ne": True}
    })
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if visit.get("status") not in ["in_progress", "on_site"]:
        raise HTTPException(status_code=400, detail="Visit must be in progress")
    
    now = get_ist_isoformat()
    ticket = await db.service_tickets_new.find_one({"id": visit["ticket_id"]})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Update visit with diagnosis
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {"$set": {
            "status": "paused",
            "problem_found": data.diagnosis.problem_identified,
            "diagnosis": data.diagnosis.root_cause,
            "findings": data.diagnosis.observations,
            "photos": data.diagnosis.photos,
            "parts_required": [p.model_dump() for p in data.parts_required],
            "paused_reason": "pending_parts",
            "paused_at": now,
            "engineer_remarks": data.remarks,
            "updated_at": now
        }}
    )
    
    # Create part requests for each part
    part_request_ids = []
    quotation_items = []
    
    for part in data.parts_required:
        # If item_id provided, get from inventory
        item_info = None
        if part.item_id:
            item_info = await db.item_masters.find_one({
                "id": part.item_id,
                "is_deleted": {"$ne": True}
            }, {"_id": 0, "name": 1, "sku": 1, "cost_price": 1, "unit_price": 1})
        
        part_request = {
            "id": str(uuid.uuid4()),
            "organization_id": ticket.get("organization_id"),
            "ticket_id": visit["ticket_id"],
            "ticket_number": visit.get("ticket_number"),
            "visit_id": visit_id,
            "item_id": part.item_id,
            "item_name": item_info.get("name") if item_info else part.item_name,
            "item_sku": item_info.get("sku") if item_info else None,
            "item_description": part.item_description,
            "quantity_requested": part.quantity,
            "urgency": part.urgency,
            "request_notes": part.notes,
            "status": "requested",
            "requested_by_id": engineer_id,
            "requested_by_name": engineer.get("name"),
            "requested_at": now,
            "estimated_unit_cost": item_info.get("cost_price", 0) if item_info else 0,
            "is_deleted": False,
            "created_at": now,
            "updated_at": now
        }
        
        await db.ticket_part_requests.insert_one(part_request)
        part_request_ids.append(part_request["id"])
        
        # Add to quotation items
        unit_price = item_info.get("unit_price", 0) if item_info else 0
        quotation_items.append({
            "id": str(uuid.uuid4()),
            "part_request_id": part_request["id"],
            "item_id": part.item_id,
            "item_name": item_info.get("name") if item_info else part.item_name,
            "item_sku": item_info.get("sku") if item_info else None,
            "description": part.item_description or (item_info.get("name") if item_info else part.item_name),
            "quantity": part.quantity,
            "unit_price": unit_price,
            "total_price": unit_price * part.quantity,
            "is_taxable": True
        })
    
    # Create draft quotation automatically
    subtotal = sum(item["total_price"] for item in quotation_items)
    tax_rate = 18  # Default GST
    tax_amount = subtotal * tax_rate / 100
    total_amount = subtotal + tax_amount
    
    quotation = {
        "id": str(uuid.uuid4()),
        "organization_id": ticket.get("organization_id"),
        "quotation_number": f"QT-{ticket.get('ticket_number', '')}-{uuid.uuid4().hex[:4].upper()}",
        "ticket_id": visit["ticket_id"],
        "ticket_number": ticket.get("ticket_number"),
        "company_id": ticket.get("company_id"),
        "company_name": ticket.get("company_name"),
        "contact_name": ticket.get("contact", {}).get("name"),
        "contact_email": ticket.get("contact", {}).get("email"),
        "contact_phone": ticket.get("contact", {}).get("phone"),
        "items": quotation_items,
        "subtotal": subtotal,
        "tax_rate": tax_rate,
        "tax_amount": tax_amount,
        "discount_amount": 0,
        "total_amount": total_amount,
        "currency": "INR",
        "status": "draft",
        "valid_until": None,  # Admin will set
        "notes": f"Parts required for ticket #{ticket.get('ticket_number')}. Engineer remarks: {data.remarks}",
        "engineer_remarks": data.remarks,
        "created_by_id": engineer_id,
        "created_by_name": engineer.get("name"),
        "created_at": now,
        "updated_at": now,
        "is_deleted": False
    }
    
    await db.quotations.insert_one(quotation)
    
    # Update ticket status to pending_parts
    status_change = {
        "id": str(uuid.uuid4()),
        "from_status": ticket.get("status"),
        "to_status": "pending_parts",
        "changed_at": now,
        "changed_by_id": engineer_id,
        "changed_by_name": engineer.get("name"),
        "notes": f"Parts required: {data.remarks}"
    }
    
    await db.service_tickets_new.update_one(
        {"id": visit["ticket_id"]},
        {
            "$set": {
                "status": "pending_parts",
                "requires_parts": True,
                "quotation_id": quotation["id"],
                "quotation_status": "draft",
                "updated_at": now
            },
            "$push": {"status_history": status_change}
        }
    )
    
    logger.info(f"Ticket {ticket.get('ticket_number')} marked pending parts. Quotation {quotation['quotation_number']} created.")
    
    return {
        "success": True,
        "message": "Ticket marked as pending parts. Draft quotation created for admin review.",
        "status": "pending_parts",
        "quotation_id": quotation["id"],
        "quotation_number": quotation["quotation_number"],
        "parts_requested": len(data.parts_required)
    }


# ==================== TICKET CLOSURE ====================

@router.post("/tickets/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    data: CloseTicketRequest,
    engineer: dict = Depends(get_current_engineer)
):
    """Close ticket with final findings and solution details"""
    engineer_id = engineer["id"]
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "assigned_to_id": engineer_id,
        "is_deleted": {"$ne": True}
    })
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not assigned to you")
    
    # Validate ticket can be closed
    if ticket.get("status") == "pending_parts":
        raise HTTPException(
            status_code=400,
            detail="Cannot close ticket while pending parts. Wait for quotation approval and complete the work."
        )
    
    if ticket.get("status") not in ["completed", "in_progress"]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot close ticket in {ticket.get('status')} status. Must be completed or in_progress."
        )
    
    # Check if there are any incomplete visits
    incomplete_visits = await db.service_visits_new.count_documents({
        "ticket_id": ticket_id,
        "status": {"$in": ["scheduled", "in_progress", "on_site"]},
        "is_deleted": {"$ne": True}
    })
    
    if incomplete_visits > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot close ticket with {incomplete_visits} incomplete visits"
        )
    
    now = get_ist_isoformat()
    
    status_change = {
        "id": str(uuid.uuid4()),
        "from_status": ticket.get("status"),
        "to_status": "closed",
        "changed_at": now,
        "changed_by_id": engineer_id,
        "changed_by_name": engineer.get("name"),
        "notes": f"Final findings: {data.final_findings}"
    }
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": "closed",
                "closure_notes": data.final_findings,
                "resolution_summary": data.solution_details,
                "customer_feedback": data.customer_feedback,
                "customer_signature": data.customer_signature,
                "closed_at": now,
                "closed_by_id": engineer_id,
                "closed_by_name": engineer.get("name"),
                "updated_at": now
            },
            "$push": {"status_history": status_change}
        }
    )
    
    logger.info(f"Ticket {ticket.get('ticket_number')} closed by {engineer.get('name')}")
    
    return {
        "success": True,
        "message": "Ticket closed successfully",
        "status": "closed"
    }


# ==================== INVENTORY LOOKUP ====================

@router.get("/inventory/items")
async def search_inventory_items(
    search: Optional[str] = None,
    category: Optional[str] = None,
    limit: int = Query(default=20, le=50),
    engineer: dict = Depends(get_current_engineer)
):
    """Search inventory items for parts selection"""
    # Get organization from engineer's association
    staff = await db.staff_users.find_one({"id": engineer["id"]}, {"organization_id": 1})
    org_id = staff.get("organization_id") if staff else None
    
    query = {"is_deleted": {"$ne": True}}
    
    if org_id:
        query["organization_id"] = org_id
    
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if category:
        query["category"] = category
    
    items = await db.item_masters.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "sku": 1, "description": 1, 
         "category": 1, "unit_price": 1, "cost_price": 1}
    ).limit(limit).to_list(limit)
    
    return {"items": items}


# ==================== REVISIT HANDLING ====================

@router.get("/tickets/{ticket_id}/revisits")
async def get_ticket_revisits(
    ticket_id: str,
    engineer: dict = Depends(get_current_engineer)
):
    """Get revisit history for a ticket"""
    engineer_id = engineer["id"]
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "assigned_to_id": engineer_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "id": 1, "ticket_number": 1})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    visits = await db.service_visits_new.find({
        "ticket_id": ticket_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("visit_number", 1).to_list(50)
    
    # Mark which visits are revisits
    for i, visit in enumerate(visits):
        visit["is_revisit"] = i > 0
        visit["is_post_quotation_revisit"] = visit.get("created_after_quotation", False)
    
    return {
        "ticket": ticket,
        "visits": visits,
        "total_visits": len(visits),
        "has_revisits": len(visits) > 1
    }
