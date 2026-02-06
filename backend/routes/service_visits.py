"""
Service Visits API Routes
=========================
Multi-visit management with timer functionality.
"""
import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin
from models.service_visit import (
    ServiceVisitNew, ServiceVisitCreate, ServiceVisitUpdate,
    VisitStartTimerRequest, VisitStopTimerRequest, VisitAddActionRequest,
    VisitStatus
)
from models.service_ticket import TicketStatus
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/visits", tags=["Service Visits"])


@router.get("")
async def list_visits(
    admin: dict = Depends(get_current_admin),
    ticket_id: Optional[str] = None,
    technician_id: Optional[str] = None,
    status: Optional[str] = None,
    scheduled_date: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200)
):
    """List service visits"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if ticket_id:
        query["ticket_id"] = ticket_id
    if technician_id:
        query["technician_id"] = technician_id
    if status:
        query["status"] = status
    if scheduled_date:
        query["scheduled_date"] = scheduled_date
    
    total = await db.service_visits_new.count_documents(query)
    skip = (page - 1) * limit
    
    visits = await db.service_visits_new.find(
        query, {"_id": 0}
    ).sort([("scheduled_date", -1), ("visit_number", 1)]).skip(skip).limit(limit).to_list(limit)
    
    return {
        "visits": visits,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/today")
async def get_todays_visits(admin: dict = Depends(get_current_admin)):
    """Get visits scheduled for today"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    today = datetime.now().strftime("%Y-%m-%d")
    
    visits = await db.service_visits_new.find(
        {
            "organization_id": org_id,
            "is_deleted": {"$ne": True},
            "$or": [
                {"scheduled_date": today},
                {"status": VisitStatus.IN_PROGRESS.value}  # Include ongoing visits
            ]
        },
        {"_id": 0}
    ).sort("scheduled_time_from", 1).to_list(100)
    
    return {"visits": visits, "date": today}


@router.get("/technician/{technician_id}")
async def get_technician_visits(
    technician_id: str,
    admin: dict = Depends(get_current_admin),
    status: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """Get visits for a specific technician"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {
        "organization_id": org_id,
        "technician_id": technician_id,
        "is_deleted": {"$ne": True}
    }
    
    if status:
        query["status"] = status
    if from_date:
        query["scheduled_date"] = {"$gte": from_date}
    if to_date:
        if "scheduled_date" in query:
            query["scheduled_date"]["$lte"] = to_date
        else:
            query["scheduled_date"] = {"$lte": to_date}
    
    visits = await db.service_visits_new.find(
        query, {"_id": 0}
    ).sort("scheduled_date", -1).to_list(100)
    
    return {"visits": visits}


@router.get("/{visit_id}")
async def get_visit(visit_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific visit"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    visit = await db.service_visits_new.find_one(
        {"id": visit_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    # Get ticket details
    ticket = await db.service_tickets_new.find_one(
        {"id": visit["ticket_id"], "organization_id": org_id},
        {"_id": 0, "ticket_number": 1, "title": 1, "company_name": 1, "device_name": 1, "contact": 1, "location": 1}
    )
    
    visit["ticket"] = ticket
    
    # Get parts issued for this visit
    parts_issued = await db.ticket_part_issues.find(
        {"visit_id": visit_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(50)
    
    visit["parts_issued"] = parts_issued
    
    return visit


@router.post("")
async def create_visit(
    data: ServiceVisitCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new service visit"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Verify ticket exists and is open
    ticket = await db.service_tickets_new.find_one(
        {"id": data.ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "ticket_number": 1, "status": 1}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.get("status") in [TicketStatus.CLOSED.value, TicketStatus.CANCELLED.value]:
        raise HTTPException(status_code=400, detail="Cannot add visits to closed or cancelled tickets")
    
    # Get technician details
    tech = await db.staff_users.find_one(
        {"id": data.technician_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"name": 1}
    ) or await db.organization_members.find_one(
        {"id": data.technician_id, "is_deleted": {"$ne": True}},
        {"name": 1}
    )
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")
    
    # Get visit number
    existing_visits = await db.service_visits_new.count_documents({
        "ticket_id": data.ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    visit_number = existing_visits + 1
    
    visit = ServiceVisitNew(
        organization_id=org_id,
        ticket_id=data.ticket_id,
        ticket_number=ticket["ticket_number"],
        visit_number=visit_number,
        technician_id=data.technician_id,
        technician_name=tech.get("name", ""),
        scheduled_date=data.scheduled_date,
        scheduled_time_from=data.scheduled_time_from,
        scheduled_time_to=data.scheduled_time_to,
        purpose=data.purpose,
        visit_location=data.visit_location,
        created_by_id=admin.get("id"),
        created_by_name=admin.get("name")
    )
    
    await db.service_visits_new.insert_one(visit.model_dump())
    
    return await db.service_visits_new.find_one({"id": visit.id}, {"_id": 0})


@router.put("/{visit_id}")
async def update_visit(
    visit_id: str,
    data: ServiceVisitUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a visit"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.service_visits_new.find_one({
        "id": visit_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if existing.get("status") == VisitStatus.COMPLETED.value:
        raise HTTPException(status_code=400, detail="Cannot update completed visits")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {"$set": update_dict}
    )
    
    return await db.service_visits_new.find_one({"id": visit_id}, {"_id": 0})


@router.delete("/{visit_id}")
async def delete_visit(visit_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a visit (only if not started)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.service_visits_new.find_one({
        "id": visit_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if existing.get("status") != VisitStatus.SCHEDULED.value:
        raise HTTPException(status_code=400, detail="Can only delete scheduled (not started) visits")
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    return {"success": True, "message": "Visit deleted"}


# ==================== TIMER ====================

@router.post("/{visit_id}/start-timer")
async def start_timer(
    visit_id: str,
    data: VisitStartTimerRequest = None,
    admin: dict = Depends(get_current_admin)
):
    """Start the visit timer (check-in)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if visit.get("status") != VisitStatus.SCHEDULED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start timer. Visit is already {visit.get('status')}"
        )
    
    now = get_ist_isoformat()
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {
            "$set": {
                "status": VisitStatus.IN_PROGRESS.value,
                "start_time": now,
                "updated_at": now
            }
        }
    )
    
    # Update ticket status to in_progress if not already
    ticket = await db.service_tickets_new.find_one(
        {"id": visit["ticket_id"], "organization_id": org_id},
        {"status": 1}
    )
    if ticket and ticket.get("status") == TicketStatus.ASSIGNED.value:
        from models.service_ticket import StatusChange
        status_change = StatusChange(
            from_status=ticket.get("status"),
            to_status=TicketStatus.IN_PROGRESS.value,
            changed_by_id=admin.get("id", ""),
            changed_by_name=admin.get("name", ""),
            notes="Visit timer started"
        )
        await db.service_tickets_new.update_one(
            {"id": visit["ticket_id"]},
            {
                "$set": {
                    "status": TicketStatus.IN_PROGRESS.value,
                    "first_response_at": now,
                    "updated_at": now
                },
                "$push": {"status_history": status_change.model_dump()}
            }
        )
    
    logger.info(f"Timer started for visit {visit_id}")
    
    return await db.service_visits_new.find_one({"id": visit_id}, {"_id": 0})


@router.post("/{visit_id}/stop-timer")
async def stop_timer(
    visit_id: str,
    data: VisitStopTimerRequest,
    admin: dict = Depends(get_current_admin)
):
    """Stop the visit timer and complete the visit"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if visit.get("status") != VisitStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot stop timer. Visit is {visit.get('status')}, not in_progress"
        )
    
    now = get_ist_isoformat()
    
    # Calculate duration
    start_time = visit.get("start_time")
    duration_minutes = 0
    if start_time:
        try:
            start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
        except Exception as e:
            logger.error(f"Error calculating duration: {e}")
    
    update_data = {
        "status": VisitStatus.COMPLETED.value,
        "end_time": now,
        "duration_minutes": duration_minutes,
        "is_completed": True,
        "updated_at": now
    }
    
    if data.diagnostics:
        update_data["diagnostics"] = data.diagnostics
    if data.actions_taken:
        update_data["actions_taken"] = data.actions_taken
    if data.work_summary:
        update_data["work_summary"] = data.work_summary
    if data.outcome:
        update_data["outcome"] = data.outcome
    if data.customer_name:
        update_data["customer_name"] = data.customer_name
    if data.customer_signature:
        update_data["customer_signature"] = data.customer_signature
    if data.notes:
        update_data["internal_notes"] = data.notes
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {"$set": update_data}
    )
    
    # Update ticket total time
    ticket_id = visit.get("ticket_id")
    if ticket_id:
        # Get all visits for this ticket to calculate total time
        visits = await db.service_visits_new.find(
            {"ticket_id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
            {"duration_minutes": 1}
        ).to_list(100)
        
        total_time = sum(v.get("duration_minutes", 0) for v in visits) + duration_minutes
        
        await db.service_tickets_new.update_one(
            {"id": ticket_id},
            {"$set": {"total_time_minutes": total_time, "updated_at": now}}
        )
    
    logger.info(f"Timer stopped for visit {visit_id}. Duration: {duration_minutes} minutes")
    
    return await db.service_visits_new.find_one({"id": visit_id}, {"_id": 0})


@router.post("/{visit_id}/add-action")
async def add_action(
    visit_id: str,
    data: VisitAddActionRequest,
    admin: dict = Depends(get_current_admin)
):
    """Add an action to the visit"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    visit = await db.service_visits_new.find_one({
        "id": visit_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not visit:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    if visit.get("status") != VisitStatus.IN_PROGRESS.value:
        raise HTTPException(status_code=400, detail="Can only add actions to in-progress visits")
    
    await db.service_visits_new.update_one(
        {"id": visit_id},
        {
            "$push": {"actions_taken": data.action},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    return {"success": True, "action": data.action}
