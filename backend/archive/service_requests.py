"""
Service Request API Routes
===========================
All state changes go through /transition internally.
Specific endpoints (/accept, /assign, etc.) are thin wrappers
that call the same internal FSM transition handler.

Middleware Rule: If module disabled AND request.method != GET → BLOCK
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from services.auth import get_current_admin
from services.service_request_fsm import (
    ServiceRequestFSM, FSMValidationError, FSMDataRequiredError
)
from models.service_request import (
    ServiceRequest, ServiceRequestCreate, ServiceRequestUpdate,
    StateTransitionRequest, AddVisitRequest, UpdateVisitRequest,
    ApprovalResponseRequest, ServiceState, STATE_METADATA,
    CustomerSnapshot, LocationSnapshot, ServiceVisit,
    generate_unique_ticket_number
)
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/service-requests", tags=["Service Requests"])


# ==================== MIDDLEWARE ====================

async def check_module_enabled(admin: dict):
    """Middleware to check if module is enabled"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    org = await db.organizations.find_one(
        {"id": org_id, "is_deleted": {"$ne": True}},
        {"feature_flags": 1}
    )
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    feature_flags = org.get("feature_flags", {})
    if not feature_flags.get("service_management", True):
        raise HTTPException(
            status_code=403, 
            detail="Service Management module is disabled for this organization"
        )
    
    return True


# ==================== LIST & GET ====================

@router.get("")
async def list_service_requests(
    admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    state: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_staff_id: Optional[str] = None,
    customer_id: Optional[str] = None,
    device_id: Optional[str] = None,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """List service requests with filtering"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Build query
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if state:
        query["state"] = state
    if priority:
        query["priority"] = priority
    if assigned_staff_id:
        query["assigned_staff_id"] = assigned_staff_id
    if customer_id:
        query["customer_id"] = customer_id
    if device_id:
        query["device_id"] = device_id
    if search:
        query["$or"] = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}},
            {"customer_snapshot.name": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count
    total = await db.service_requests.count_documents(query)
    
    # Sort direction
    sort_dir = -1 if sort_order == "desc" else 1
    
    # Get paginated results
    skip = (page - 1) * limit
    requests = await db.service_requests.find(
        query,
        {"_id": 0}
    ).sort(sort_by, sort_dir).skip(skip).limit(limit).to_list(None)
    
    # Add state metadata to each request
    for req in requests:
        state_key = req.get("state")
        if state_key:
            try:
                req["state_metadata"] = STATE_METADATA.get(ServiceState(state_key), {})
            except ValueError:
                pass
    
    return {
        "service_requests": requests,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/states")
async def get_all_states(admin: dict = Depends(get_current_admin)):
    """Get all FSM states with metadata"""
    return {
        "states": [
            {
                "value": state.value,
                **STATE_METADATA.get(state, {})
            }
            for state in ServiceState
        ]
    }


@router.get("/stats")
async def get_service_request_stats(admin: dict = Depends(get_current_admin)):
    """Get statistics for service requests"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    pipeline = [
        {"$match": {"organization_id": org_id, "is_deleted": {"$ne": True}}},
        {"$group": {"_id": "$state", "count": {"$sum": 1}}}
    ]
    
    results = await db.service_requests.aggregate(pipeline).to_list(None)
    
    # Build stats dict
    by_state = {r["_id"]: r["count"] for r in results}
    total = sum(by_state.values())
    
    # Open vs Closed
    terminal_states = [ServiceState.RESOLVED.value, ServiceState.CANCELLED.value]
    closed = sum(by_state.get(s, 0) for s in terminal_states)
    open_count = total - closed
    
    return {
        "total": total,
        "open": open_count,
        "closed": closed,
        "by_state": by_state
    }


@router.get("/{request_id}")
async def get_service_request(
    request_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get service request details"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    service_request = await db.service_requests.find_one(
        {"id": request_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not service_request:
        raise HTTPException(status_code=404, detail="Service request not found")
    
    # Add available transitions
    available_transitions = await ServiceRequestFSM.get_available_transitions(request_id, org_id)
    service_request["available_transitions"] = available_transitions
    
    # Add state metadata
    state_key = service_request.get("state")
    if state_key:
        try:
            service_request["state_metadata"] = STATE_METADATA.get(ServiceState(state_key), {})
        except ValueError:
            pass
    
    return service_request


@router.get("/{request_id}/history")
async def get_state_history(
    request_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get state transition history for a service request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    service_request = await db.service_requests.find_one(
        {"id": request_id, "organization_id": org_id},
        {"_id": 0, "state_history": 1, "ticket_number": 1}
    )
    
    if not service_request:
        raise HTTPException(status_code=404, detail="Service request not found")
    
    return {
        "ticket_number": service_request.get("ticket_number"),
        "history": service_request.get("state_history", [])
    }


# ==================== CREATE ====================

@router.post("")
async def create_service_request(
    request_data: ServiceRequestCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new service request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check module enabled
    await check_module_enabled(admin)
    
    # Generate unique ticket number
    ticket_number = await generate_unique_ticket_number(db, org_id)
    
    # Build customer snapshot
    customer_snapshot = None
    if request_data.customer_name:
        customer_snapshot = CustomerSnapshot(
            name=request_data.customer_name,
            mobile=request_data.customer_mobile,
            email=request_data.customer_email,
            company_name=request_data.customer_company_name
        ).model_dump()
    
    # Build location snapshot
    location_snapshot = None
    if request_data.location_address:
        location_snapshot = LocationSnapshot(
            address=request_data.location_address,
            city=request_data.location_city,
            pincode=request_data.location_pincode
        ).model_dump()
    
    # Create service request
    service_request = ServiceRequest(
        ticket_number=ticket_number,
        organization_id=org_id,
        title=request_data.title,
        description=request_data.description,
        category=request_data.category,
        priority=request_data.priority,
        customer_id=request_data.customer_id,
        customer_snapshot=customer_snapshot,
        location_snapshot=location_snapshot,
        device_id=request_data.device_id,
        device_serial=request_data.device_serial,
        device_name=request_data.device_name,
        tags=request_data.tags or [],
        custom_fields=request_data.custom_fields or {},
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", "")
    )
    
    # Initial state history
    initial_transition = {
        "id": str(__import__('uuid').uuid4()),
        "from_state": None,
        "to_state": ServiceState.CREATED.value,
        "actor_id": admin.get("id", ""),
        "actor_name": admin.get("name", ""),
        "actor_role": admin.get("role", "admin"),
        "timestamp": get_ist_isoformat(),
        "reason": "Service request created",
        "metadata": {}
    }
    service_request.state_history = [initial_transition]
    
    await db.service_requests.insert_one(service_request.model_dump())
    
    # Log audit
    await db.service_request_audit.insert_one({
        "id": str(__import__('uuid').uuid4()),
        "organization_id": org_id,
        "service_request_id": service_request.id,
        "ticket_number": ticket_number,
        "action": "created",
        "actor_id": admin.get("id"),
        "actor_name": admin.get("name"),
        "actor_role": admin.get("role", "admin"),
        "timestamp": get_ist_isoformat()
    })
    
    # If assigned_staff_id provided, auto-assign
    if request_data.assigned_staff_id:
        try:
            # Get staff name
            staff = await db.staff_users.find_one(
                {"id": request_data.assigned_staff_id, "organization_id": org_id},
                {"name": 1}
            ) or await db.organization_members.find_one(
                {"id": request_data.assigned_staff_id},
                {"name": 1}
            )
            staff_name = staff.get("name", "") if staff else ""
            
            return await ServiceRequestFSM.assign(
                service_request_id=service_request.id,
                organization_id=org_id,
                staff_id=request_data.assigned_staff_id,
                staff_name=staff_name,
                actor={
                    "id": admin.get("id"),
                    "name": admin.get("name"),
                    "role": admin.get("role", "admin")
                },
                reason="Auto-assigned at creation"
            )
        except FSMValidationError:
            pass  # Return created state if assignment fails
    
    result = await db.service_requests.find_one({"id": service_request.id}, {"_id": 0})
    return {"success": True, "service_request": result}


# ==================== UPDATE (NON-FSM FIELDS) ====================

@router.put("/{request_id}")
async def update_service_request(
    request_id: str,
    update_data: ServiceRequestUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update non-FSM fields of a service request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    await check_module_enabled(admin)
    
    # Get existing
    existing = await db.service_requests.find_one(
        {"id": request_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Service request not found")
    
    # Check if terminal state
    if existing.get("state") in [ServiceState.RESOLVED.value, ServiceState.CANCELLED.value]:
        raise HTTPException(status_code=400, detail="Cannot update resolved/cancelled requests")
    
    # Build update
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.service_requests.update_one(
        {"id": request_id},
        {"$set": update_dict}
    )
    
    result = await db.service_requests.find_one({"id": request_id}, {"_id": 0})
    return {"success": True, "service_request": result}


# ==================== FSM TRANSITIONS ====================
# All state changes go through /transition - this is THE ONLY way

@router.post("/{request_id}/transition")
async def transition_state(
    request_id: str,
    transition: StateTransitionRequest,
    admin: dict = Depends(get_current_admin)
):
    """
    THE ONLY endpoint for FSM state transitions.
    All other transition endpoints are thin wrappers around this.
    """
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    actor = {
        "id": admin.get("id", ""),
        "name": admin.get("name", ""),
        "role": admin.get("role", "admin")
    }
    
    # Build transition data from request
    transition_data = {}
    if transition.assigned_staff_id:
        transition_data["assigned_staff_id"] = transition.assigned_staff_id
        # Get staff name
        staff = await db.staff_users.find_one(
            {"id": transition.assigned_staff_id, "organization_id": org_id},
            {"name": 1}
        ) or await db.organization_members.find_one(
            {"id": transition.assigned_staff_id},
            {"name": 1}
        )
        transition_data["assigned_staff_name"] = staff.get("name", "") if staff else ""
    
    if transition.decline_reason:
        transition_data["decline_reason"] = transition.decline_reason
    if transition.diagnostics:
        transition_data["diagnostics"] = transition.diagnostics
    if transition.parts_required:
        transition_data["parts_required"] = transition.parts_required
    if transition.approval_amount is not None:
        transition_data["approval_amount"] = transition.approval_amount
    if transition.resolution_notes:
        transition_data["resolution_notes"] = transition.resolution_notes
    if transition.cancellation_reason:
        transition_data["cancellation_reason"] = transition.cancellation_reason
    
    try:
        result = await ServiceRequestFSM.transition(
            service_request_id=request_id,
            organization_id=org_id,
            target_state=transition.target_state,
            actor=actor,
            reason=transition.reason,
            metadata=transition.metadata,
            transition_data=transition_data
        )
        return {"success": True, "service_request": result}
    
    except FSMValidationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except FSMDataRequiredError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"{e.message}",
            headers={"X-Missing-Fields": ",".join(e.missing_fields)}
        )


# ==================== CONVENIENCE TRANSITION ENDPOINTS ====================
# These are thin wrappers - they all call /transition internally

@router.post("/{request_id}/assign")
async def assign_request(
    request_id: str,
    staff_id: str = Query(...),
    admin: dict = Depends(get_current_admin)
):
    """Assign to technician - wrapper around /transition"""
    return await transition_state(
        request_id,
        StateTransitionRequest(
            target_state=ServiceState.ASSIGNED.value,
            assigned_staff_id=staff_id,
            reason="Assigned by admin"
        ),
        admin
    )


@router.post("/{request_id}/accept")
async def accept_assignment(
    request_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Accept assignment - wrapper around /transition"""
    return await transition_state(
        request_id,
        StateTransitionRequest(
            target_state=ServiceState.ACCEPTED.value,
            reason="Assignment accepted"
        ),
        admin
    )


@router.post("/{request_id}/decline")
async def decline_assignment(
    request_id: str,
    reason: str = Query(...),
    admin: dict = Depends(get_current_admin)
):
    """Decline assignment - wrapper around /transition"""
    return await transition_state(
        request_id,
        StateTransitionRequest(
            target_state=ServiceState.DECLINED.value,
            decline_reason=reason,
            reason=reason
        ),
        admin
    )


@router.post("/{request_id}/start-visit")
async def start_visit(
    request_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Start visit - wrapper around /transition"""
    return await transition_state(
        request_id,
        StateTransitionRequest(
            target_state=ServiceState.VISIT_IN_PROGRESS.value,
            reason="Visit started"
        ),
        admin
    )


@router.post("/{request_id}/complete-visit")
async def complete_visit(
    request_id: str,
    diagnostics: str = Query(...),
    admin: dict = Depends(get_current_admin)
):
    """Complete visit - wrapper around /transition"""
    return await transition_state(
        request_id,
        StateTransitionRequest(
            target_state=ServiceState.VISIT_COMPLETED.value,
            diagnostics=diagnostics,
            reason="Visit completed"
        ),
        admin
    )


@router.post("/{request_id}/resolve")
async def resolve_request(
    request_id: str,
    resolution_notes: str = Query(...),
    admin: dict = Depends(get_current_admin)
):
    """Resolve request - wrapper around /transition"""
    return await transition_state(
        request_id,
        StateTransitionRequest(
            target_state=ServiceState.RESOLVED.value,
            resolution_notes=resolution_notes,
            reason="Request resolved"
        ),
        admin
    )


@router.post("/{request_id}/cancel")
async def cancel_request(
    request_id: str,
    cancellation_reason: str = Query(...),
    admin: dict = Depends(get_current_admin)
):
    """Cancel request - wrapper around /transition"""
    return await transition_state(
        request_id,
        StateTransitionRequest(
            target_state=ServiceState.CANCELLED.value,
            cancellation_reason=cancellation_reason,
            reason=cancellation_reason
        ),
        admin
    )


# ==================== VISITS ====================

@router.post("/{request_id}/visits")
async def add_visit(
    request_id: str,
    visit_data: AddVisitRequest,
    admin: dict = Depends(get_current_admin)
):
    """Add a new visit to service request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    await check_module_enabled(admin)
    
    # Get service request
    service_request = await db.service_requests.find_one(
        {"id": request_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "visits": 1}
    )
    if not service_request:
        raise HTTPException(status_code=404, detail="Service request not found")
    
    # Get technician name
    technician = await db.staff_users.find_one(
        {"id": visit_data.technician_id, "organization_id": org_id},
        {"name": 1}
    ) or await db.organization_members.find_one(
        {"id": visit_data.technician_id},
        {"name": 1}
    )
    technician_name = technician.get("name", "") if technician else ""
    
    # Create visit
    visit_number = len(service_request.get("visits", [])) + 1
    visit = ServiceVisit(
        visit_number=visit_number,
        technician_id=visit_data.technician_id,
        technician_name=technician_name,
        scheduled_at=visit_data.scheduled_at,
        notes=visit_data.notes
    )
    
    await db.service_requests.update_one(
        {"id": request_id},
        {
            "$push": {"visits": visit.model_dump()},
            "$set": {"current_visit_id": visit.visit_id, "updated_at": get_ist_isoformat()}
        }
    )
    
    result = await db.service_requests.find_one({"id": request_id}, {"_id": 0})
    return {"success": True, "service_request": result, "visit": visit.model_dump()}


@router.put("/{request_id}/visits/{visit_id}")
async def update_visit(
    request_id: str,
    visit_id: str,
    visit_data: UpdateVisitRequest,
    admin: dict = Depends(get_current_admin)
):
    """Update visit details"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    await check_module_enabled(admin)
    
    # Build update for nested array element
    update_fields = {}
    for field, value in visit_data.model_dump().items():
        if value is not None:
            update_fields[f"visits.$.{field}"] = value
    
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_fields["updated_at"] = get_ist_isoformat()
    
    result = await db.service_requests.update_one(
        {"id": request_id, "organization_id": org_id, "visits.visit_id": visit_id},
        {"$set": update_fields}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Visit not found")
    
    service_request = await db.service_requests.find_one({"id": request_id}, {"_id": 0})
    return {"success": True, "service_request": service_request}


# ==================== DELETE ====================

@router.delete("/{request_id}")
async def delete_service_request(
    request_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Soft delete a service request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    await check_module_enabled(admin)
    
    result = await db.service_requests.update_one(
        {"id": request_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Service request not found")
    
    return {"success": True, "message": "Service request deleted"}
