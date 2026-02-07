"""
Service Tickets API Routes (NEW)
================================
Complete service ticket management with simplified workflow.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin
from models.service_ticket import (
    ServiceTicketNew, ServiceTicketCreate, ServiceTicketUpdate,
    TicketAssignRequest, TicketResolveRequest, TicketCloseRequest, TicketCancelRequest,
    TicketCommentCreate, TicketStatus, TicketPriority, StatusChange,
    TicketContact, TicketLocation,
    generate_unique_ticket_number
)
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/service-tickets", tags=["Service Tickets (New)"])


# ==================== LIST & STATS ====================

@router.get("")
async def list_tickets(
    admin: dict = Depends(get_current_admin),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    company_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    problem_id: Optional[str] = None,
    device_id: Optional[str] = None,
    is_urgent: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100)
):
    """List service tickets with filtering"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if status:
        # Support comma-separated statuses
        statuses = [s.strip() for s in status.split(",")]
        if len(statuses) == 1:
            query["status"] = statuses[0]
        else:
            query["status"] = {"$in": statuses}
    if priority:
        query["priority"] = priority
    if company_id:
        query["company_id"] = company_id
    if assigned_to_id:
        query["assigned_to_id"] = assigned_to_id
    if problem_id:
        query["problem_id"] = problem_id
    if device_id:
        query["device_id"] = device_id
    if is_urgent is not None:
        query["is_urgent"] = is_urgent
    if search:
        query["$or"] = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}},
            {"company_name": {"$regex": search, "$options": "i"}},
            {"device_serial": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.service_tickets_new.count_documents(query)
    
    sort_dir = -1 if sort_order == "desc" else 1
    skip = (page - 1) * limit
    
    tickets = await db.service_tickets_new.find(
        query, {"_id": 0}
    ).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(limit)
    
    return {
        "tickets": tickets,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/stats")
async def get_ticket_stats(admin: dict = Depends(get_current_admin)):
    """Get ticket statistics"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # By status
    status_pipeline = [
        {"$match": {"organization_id": org_id, "is_deleted": {"$ne": True}}},
        {"$group": {"_id": "$status", "count": {"$sum": 1}}}
    ]
    status_results = await db.service_tickets_new.aggregate(status_pipeline).to_list(20)
    by_status = {r["_id"]: r["count"] for r in status_results}
    
    # By priority
    priority_pipeline = [
        {"$match": {"organization_id": org_id, "is_deleted": {"$ne": True}}},
        {"$group": {"_id": "$priority", "count": {"$sum": 1}}}
    ]
    priority_results = await db.service_tickets_new.aggregate(priority_pipeline).to_list(10)
    by_priority = {r["_id"]: r["count"] for r in priority_results}
    
    # Calculate totals
    total = sum(by_status.values())
    open_statuses = [TicketStatus.NEW.value, TicketStatus.ASSIGNED.value, 
                     TicketStatus.IN_PROGRESS.value, TicketStatus.PENDING_PARTS.value]
    open_count = sum(by_status.get(s, 0) for s in open_statuses)
    closed_count = by_status.get(TicketStatus.CLOSED.value, 0) + by_status.get(TicketStatus.COMPLETED.value, 0)
    
    # Urgent count
    urgent_count = await db.service_tickets_new.count_documents({
        "organization_id": org_id,
        "is_deleted": {"$ne": True},
        "is_urgent": True,
        "status": {"$nin": [TicketStatus.CLOSED.value, TicketStatus.CANCELLED.value]}
    })
    
    return {
        "total": total,
        "open": open_count,
        "closed": closed_count,
        "urgent": urgent_count,
        "by_status": by_status,
        "by_priority": by_priority
    }


@router.get("/statuses")
async def get_ticket_statuses(admin: dict = Depends(get_current_admin)):
    """Get all ticket statuses with metadata"""
    return {
        "statuses": [
            {"value": "new", "label": "New", "color": "slate", "is_open": True},
            {"value": "pending_acceptance", "label": "Pending Acceptance", "color": "purple", "is_open": True},
            {"value": "assigned", "label": "Assigned", "color": "blue", "is_open": True},
            {"value": "in_progress", "label": "In Progress", "color": "amber", "is_open": True},
            {"value": "pending_parts", "label": "Pending Parts", "color": "orange", "is_open": True},
            {"value": "completed", "label": "Completed", "color": "green", "is_open": False},
            {"value": "closed", "label": "Closed", "color": "emerald", "is_open": False},
            {"value": "cancelled", "label": "Cancelled", "color": "red", "is_open": False}
        ]
    }


# ==================== GET & CREATE ====================

@router.get("/{ticket_id}")
async def get_ticket(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific ticket with related data"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await db.service_tickets_new.find_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get visits for this ticket
    visits = await db.service_visits_new.find(
        {"ticket_id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("visit_number", 1).to_list(50)
    
    ticket["visits"] = visits
    
    # Get parts requests
    part_requests = await db.ticket_part_requests.find(
        {"ticket_id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("requested_at", -1).to_list(50)
    
    ticket["part_requests"] = part_requests
    
    # Get parts issued
    parts_issued = await db.ticket_part_issues.find(
        {"ticket_id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("issued_at", -1).to_list(50)
    
    ticket["parts_issued"] = parts_issued
    
    return ticket


@router.post("")
async def create_ticket(
    data: ServiceTicketCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new service ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Get company details
    company = await db.companies.find_one(
        {"id": data.company_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "contact_name": 1, "contact_phone": 1, "contact_email": 1}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Generate ticket number
    ticket_number = await generate_unique_ticket_number(db, org_id)
    
    # Build contact
    contact = None
    if data.contact_name or company.get("contact_name"):
        contact = TicketContact(
            name=data.contact_name or company.get("contact_name", ""),
            phone=data.contact_phone or company.get("contact_phone"),
            email=data.contact_email or company.get("contact_email")
        )
    
    # Build location
    location = None
    if data.site_id or data.location_address:
        site_name = None
        if data.site_id:
            site = await db.sites.find_one(
                {"id": data.site_id, "organization_id": org_id},
                {"_id": 0, "name": 1, "address": 1, "city": 1}
            )
            if site:
                site_name = site.get("name")
                data.location_address = data.location_address or site.get("address")
                data.location_city = data.location_city or site.get("city")
        
        location = TicketLocation(
            site_id=data.site_id,
            site_name=site_name,
            address=data.location_address,
            city=data.location_city
        )
    
    # Get device details if provided
    device_name = None
    device_type = None
    asset_tag = None
    if data.device_id:
        device = await db.devices.find_one(
            {"id": data.device_id, "organization_id": org_id},
            {"_id": 0, "brand": 1, "model": 1, "device_type": 1, "serial_number": 1, "asset_tag": 1}
        )
        if device:
            device_name = f"{device.get('brand', '')} {device.get('model', '')}".strip()
            device_type = device.get("device_type")
            data.device_serial = data.device_serial or device.get("serial_number")
            asset_tag = device.get("asset_tag")
    
    # Get problem details if provided
    problem_name = None
    if data.problem_id:
        problem = await db.problem_masters.find_one(
            {"id": data.problem_id, "organization_id": org_id},
            {"_id": 0, "name": 1}
        )
        if problem:
            problem_name = problem.get("name")
    
    # Create ticket
    ticket = ServiceTicketNew(
        organization_id=org_id,
        ticket_number=ticket_number,
        company_id=data.company_id,
        company_name=company["name"],
        contact=contact,
        location=location,
        device_id=data.device_id,
        device_serial=data.device_serial,
        device_name=device_name,
        device_type=device_type,
        asset_tag=asset_tag,
        problem_id=data.problem_id,
        problem_name=problem_name,
        title=data.title,
        description=data.description,
        priority=data.priority,
        source=data.source,
        source_reference=data.source_reference,
        is_urgent=data.is_urgent,
        tags=data.tags or [],
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", "")
    )
    
    # Add initial status history
    initial_status = StatusChange(
        to_status=TicketStatus.NEW.value,
        changed_by_id=admin.get("id", ""),
        changed_by_name=admin.get("name", ""),
        notes="Ticket created"
    )
    ticket.status_history = [initial_status.model_dump()]
    
    # If assigned_to_id provided, auto-assign
    if data.assigned_to_id:
        tech = await db.staff_users.find_one(
            {"id": data.assigned_to_id, "organization_id": org_id},
            {"name": 1}
        ) or await db.organization_members.find_one(
            {"id": data.assigned_to_id},
            {"name": 1}
        )
        if tech:
            now = get_ist_isoformat()
            ticket.status = TicketStatus.ASSIGNED.value
            ticket.assigned_to_id = data.assigned_to_id
            ticket.assigned_to_name = tech.get("name", "")
            ticket.assigned_at = now
            ticket.assigned_by_id = admin.get("id")
            ticket.assigned_by_name = admin.get("name")
            
            # Add assignment to history
            assign_status = StatusChange(
                from_status=TicketStatus.NEW.value,
                to_status=TicketStatus.ASSIGNED.value,
                changed_by_id=admin.get("id", ""),
                changed_by_name=admin.get("name", ""),
                notes=f"Assigned to {tech.get('name', '')}"
            )
            ticket.status_history.append(assign_status.model_dump())
    
    await db.service_tickets_new.insert_one(ticket.model_dump())
    
    logger.info(f"Created ticket {ticket_number} for company {company['name']}")
    
    return await db.service_tickets_new.find_one({"id": ticket.id}, {"_id": 0})


@router.put("/{ticket_id}")
async def update_ticket(
    ticket_id: str,
    data: ServiceTicketUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a ticket (non-status fields)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Don't allow updates to closed/cancelled tickets
    if existing.get("status") in [TicketStatus.CLOSED.value, TicketStatus.CANCELLED.value]:
        raise HTTPException(status_code=400, detail="Cannot update closed or cancelled tickets")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Handle device updates
    if "device_id" in update_dict and update_dict["device_id"]:
        device = await db.devices.find_one(
            {"id": update_dict["device_id"], "organization_id": org_id},
            {"_id": 0, "brand": 1, "model": 1, "device_type": 1, "serial_number": 1, "asset_tag": 1}
        )
        if device:
            update_dict["device_name"] = f"{device.get('brand', '')} {device.get('model', '')}".strip()
            update_dict["device_type"] = device.get("device_type")
            update_dict["device_serial"] = device.get("serial_number")
            update_dict["asset_tag"] = device.get("asset_tag")
    
    # Handle problem updates
    if "problem_id" in update_dict and update_dict["problem_id"]:
        problem = await db.problem_masters.find_one(
            {"id": update_dict["problem_id"], "organization_id": org_id},
            {"_id": 0, "name": 1}
        )
        if problem:
            update_dict["problem_name"] = problem.get("name")
    
    # Recalculate total cost
    if any(k in update_dict for k in ["labour_cost", "travel_cost", "other_cost"]):
        labour = update_dict.get("labour_cost", existing.get("labour_cost", 0))
        travel = update_dict.get("travel_cost", existing.get("travel_cost", 0))
        other = update_dict.get("other_cost", existing.get("other_cost", 0))
        parts = existing.get("parts_cost", 0)
        update_dict["total_cost"] = labour + travel + other + parts
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {"$set": update_dict}
    )
    
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.delete("/{ticket_id}")
async def delete_ticket(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    result = await db.service_tickets_new.update_one(
        {"id": ticket_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return {"success": True, "message": "Ticket deleted"}


# ==================== STATUS ACTIONS ====================

@router.post("/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    data: TicketAssignRequest,
    admin: dict = Depends(get_current_admin)
):
    """Assign ticket to a technician - engineer must accept/decline"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check valid status for assignment
    valid_statuses = [TicketStatus.NEW.value, TicketStatus.PENDING_ACCEPTANCE.value, TicketStatus.ASSIGNED.value]
    if ticket.get("status") not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot assign ticket in {ticket.get('status')} status"
        )
    
    # Get technician details
    tech = await db.staff_users.find_one(
        {"id": data.technician_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"name": 1, "email": 1, "phone": 1}
    ) or await db.organization_members.find_one(
        {"id": data.technician_id, "is_deleted": {"$ne": True}},
        {"name": 1, "email": 1, "phone": 1}
    )
    if not tech:
        raise HTTPException(status_code=404, detail="Technician not found")
    
    now = get_ist_isoformat()
    
    status_change = StatusChange(
        from_status=ticket.get("status"),
        to_status=TicketStatus.PENDING_ACCEPTANCE.value,
        changed_by_id=admin.get("id", ""),
        changed_by_name=admin.get("name", ""),
        notes=data.notes or f"Assigned to {tech.get('name', '')} - awaiting acceptance"
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.PENDING_ACCEPTANCE.value,
                "assigned_to_id": data.technician_id,
                "assigned_to_name": tech.get("name", ""),
                "assigned_at": now,
                "assigned_by_id": admin.get("id"),
                "assigned_by_name": admin.get("name"),
                "assignment_status": "pending",
                "assignment_accepted_at": None,
                "assignment_declined_at": None,
                "assignment_decline_reason": None,
                "updated_at": now
            },
            "$push": {"status_history": status_change.model_dump()}
        }
    )
    
    # TODO: Send notification to technician (email/push)
    logger.info(f"Ticket {ticket.get('ticket_number')} assigned to {tech.get('name')} - awaiting acceptance")
    
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/{ticket_id}/start")
async def start_work(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Start work on ticket (move to in_progress)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.get("status") not in [TicketStatus.ASSIGNED.value, TicketStatus.PENDING_PARTS.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot start work on ticket in {ticket.get('status')} status"
        )
    
    now = get_ist_isoformat()
    
    status_change = StatusChange(
        from_status=ticket.get("status"),
        to_status=TicketStatus.IN_PROGRESS.value,
        changed_by_id=admin.get("id", ""),
        changed_by_name=admin.get("name", ""),
        notes="Work started"
    )
    
    update_data = {
        "status": TicketStatus.IN_PROGRESS.value,
        "updated_at": now
    }
    
    # Set first response time if not already set
    if not ticket.get("first_response_at"):
        update_data["first_response_at"] = now
        if ticket.get("sla_response_due"):
            update_data["sla_response_met"] = now <= ticket["sla_response_due"]
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": update_data,
            "$push": {"status_history": status_change.model_dump()}
        }
    )
    
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/{ticket_id}/pending-parts")
async def mark_pending_parts(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Mark ticket as pending parts"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.get("status") != TicketStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail=f"Can only mark pending parts from in_progress status"
        )
    
    now = get_ist_isoformat()
    
    status_change = StatusChange(
        from_status=ticket.get("status"),
        to_status=TicketStatus.PENDING_PARTS.value,
        changed_by_id=admin.get("id", ""),
        changed_by_name=admin.get("name", ""),
        notes="Waiting for parts"
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.PENDING_PARTS.value,
                "requires_parts": True,
                "updated_at": now
            },
            "$push": {"status_history": status_change.model_dump()}
        }
    )
    
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/{ticket_id}/complete")
async def complete_ticket(
    ticket_id: str,
    data: TicketResolveRequest,
    admin: dict = Depends(get_current_admin)
):
    """Mark ticket as completed"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # ⚠️ IMPORTANT: Cannot complete ticket if pending_parts without quotation approval
    if ticket.get("status") == TicketStatus.PENDING_PARTS.value:
        # Check if quotation is approved
        if ticket.get("quotation_status") != "approved":
            raise HTTPException(
                status_code=400,
                detail="Cannot complete ticket pending for parts. Quotation must be approved first."
            )
    
    if ticket.get("status") not in [TicketStatus.IN_PROGRESS.value, TicketStatus.PENDING_PARTS.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete ticket in {ticket.get('status')} status"
        )
    
    # ⚠️ IMPORTANT: Resolution notes are required for completion
    if not data.resolution_summary:
        raise HTTPException(
            status_code=400,
            detail="Resolution notes are required to complete the ticket"
        )
    
    now = get_ist_isoformat()
    
    status_change = StatusChange(
        from_status=ticket.get("status"),
        to_status=TicketStatus.COMPLETED.value,
        changed_by_id=admin.get("id", ""),
        changed_by_name=admin.get("name", ""),
        notes=data.notes or f"Completed: {data.resolution_type}"
    )
    
    update_data = {
        "status": TicketStatus.COMPLETED.value,
        "resolution_summary": data.resolution_summary,
        "resolution_type": data.resolution_type,
        "resolution_notes": data.resolution_summary,  # Store in both fields
        "resolved_at": now,
        "resolved_by_id": admin.get("id"),
        "resolved_by_name": admin.get("name"),
        "updated_at": now
    }
    
    # Check SLA resolution
    if ticket.get("sla_resolution_due"):
        update_data["sla_resolution_met"] = now <= ticket["sla_resolution_due"]
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": update_data,
            "$push": {"status_history": status_change.model_dump()}
        }
    )
    
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    data: TicketCloseRequest,
    admin: dict = Depends(get_current_admin)
):
    """Close a completed ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.get("status") != TicketStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail=f"Can only close completed tickets"
        )
    
    now = get_ist_isoformat()
    
    status_change = StatusChange(
        from_status=ticket.get("status"),
        to_status=TicketStatus.CLOSED.value,
        changed_by_id=admin.get("id", ""),
        changed_by_name=admin.get("name", ""),
        notes=data.closure_notes or "Ticket closed"
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.CLOSED.value,
                "closed_at": now,
                "closed_by_id": admin.get("id"),
                "closed_by_name": admin.get("name"),
                "closure_notes": data.closure_notes,
                "updated_at": now
            },
            "$push": {"status_history": status_change.model_dump()}
        }
    )
    
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/{ticket_id}/cancel")
async def cancel_ticket(
    ticket_id: str,
    data: TicketCancelRequest,
    admin: dict = Depends(get_current_admin)
):
    """Cancel a ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Can't cancel already closed or cancelled tickets
    if ticket.get("status") in [TicketStatus.CLOSED.value, TicketStatus.CANCELLED.value]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel ticket in {ticket.get('status')} status"
        )
    
    now = get_ist_isoformat()
    
    status_change = StatusChange(
        from_status=ticket.get("status"),
        to_status=TicketStatus.CANCELLED.value,
        changed_by_id=admin.get("id", ""),
        changed_by_name=admin.get("name", ""),
        notes=data.cancellation_reason
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.CANCELLED.value,
                "cancelled_at": now,
                "cancelled_by_id": admin.get("id"),
                "cancelled_by_name": admin.get("name"),
                "cancellation_reason": data.cancellation_reason,
                "updated_at": now
            },
            "$push": {"status_history": status_change.model_dump()}
        }
    )
    
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== COMMENTS ====================

@router.post("/{ticket_id}/comments")
async def add_comment(
    ticket_id: str,
    data: TicketCommentCreate,
    admin: dict = Depends(get_current_admin)
):
    """Add a comment to a ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    comment = {
        "id": str(__import__('uuid').uuid4()),
        "text": data.text,
        "is_internal": data.is_internal,
        "author_id": admin.get("id"),
        "author_name": admin.get("name"),
        "created_at": get_ist_isoformat()
    }
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$push": {"comments": comment},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    return {"success": True, "comment": comment}
