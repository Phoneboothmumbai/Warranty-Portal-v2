"""
Job Lifecycle Routes
====================
Complete job lifecycle management with custody tracking, warranty decisions, and repair workflows.

Paths after diagnosis:
1. Resolved on Visit - Simple close
2. Pending for Part - SLA paused until parts arrive
3. Device to Back Office - Full custody tracking + warranty decision

Hard Rules:
- Path selection is mandatory after diagnosis
- Cannot close ticket without delivery details (Path 3)
- Cannot skip warranty decision
- Every custody change = timestamp + user
"""
import logging
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from services.auth import get_current_admin, get_current_engineer
from database import db
from utils.helpers import get_ist_isoformat
from models.service_ticket import (
    TicketStatus, ResolutionPath, WarrantyType, PickupDeliveryType,
    DiagnosisDetails, DevicePickup, WarrantyDecision, AMCRepairDetails,
    OEMRepairDetails, DeviceDelivery, CustodyLog, StatusChange
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/job-lifecycle", tags=["Job Lifecycle"])


# ==================== REQUEST MODELS ====================

class DiagnosisRequest(BaseModel):
    """Diagnosis submission"""
    problem_identified: str
    root_cause: Optional[str] = None
    observations: Optional[str] = None
    time_spent_minutes: int = 0


class PathSelectionRequest(BaseModel):
    """Mandatory path selection after diagnosis"""
    path: str  # resolved_on_visit, pending_for_part, device_to_backoffice
    notes: Optional[str] = None
    
    # For resolved_on_visit
    resolution_summary: Optional[str] = None
    parts_used: Optional[List[Dict]] = None
    
    # For pending_for_part
    parts_required: Optional[List[Dict]] = None
    estimated_availability: Optional[str] = None


class DevicePickupRequest(BaseModel):
    """Device pickup details"""
    pickup_type: str  # engineer, office_boy, courier, customer_drop
    pickup_person_id: Optional[str] = None
    pickup_person_name: str
    pickup_date: str
    pickup_time: Optional[str] = None
    pickup_location: str
    device_condition: str
    accessories_taken: List[str] = []
    customer_acknowledgement: bool = False
    customer_name: Optional[str] = None
    notes: Optional[str] = None


class WarrantyDecisionRequest(BaseModel):
    """Warranty classification"""
    warranty_type: str  # under_amc, under_oem, out_of_warranty
    amc_contract_id: Optional[str] = None
    notes: Optional[str] = None


class AMCRepairRequest(BaseModel):
    """AMC internal repair details"""
    assigned_engineer_id: str
    assigned_engineer_name: str
    issue_identified: str
    repair_actions: List[str] = []
    parts_replaced: List[Dict] = []
    repair_start_date: Optional[str] = None
    repair_end_date: Optional[str] = None
    internal_notes: Optional[str] = None


class OEMRepairRequest(BaseModel):
    """OEM repair tracking"""
    oem_name: str
    oem_service_center: Optional[str] = None
    oem_engineer_name: Optional[str] = None
    oem_ticket_number: Optional[str] = None
    other_reference_numbers: List[str] = []
    sent_to_oem_date: Optional[str] = None
    repair_date: Optional[str] = None
    received_back_date: Optional[str] = None
    repair_performed: Optional[str] = None
    parts_replaced_by_oem: List[Dict] = []
    oem_notes: Optional[str] = None


class DeviceDeliveryRequest(BaseModel):
    """Device delivery/return details"""
    delivery_type: str  # engineer, office_boy, courier, customer_pickup
    delivery_person_id: Optional[str] = None
    delivery_person_name: str
    delivery_date: str
    delivery_time: Optional[str] = None
    delivery_location: str
    delivered_to_name: str
    delivered_to_designation: Optional[str] = None
    customer_confirmation: bool = False
    notes: Optional[str] = None


class ResumeFromPartsRequest(BaseModel):
    """Resume ticket after parts received"""
    parts_received: List[Dict] = []
    notes: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

async def get_ticket_or_404(ticket_id: str, org_id: str):
    """Get ticket or raise 404"""
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


def create_status_change(from_status: str, to_status: str, user_id: str, user_name: str, notes: str = None) -> dict:
    """Create a status change record"""
    return StatusChange(
        from_status=from_status,
        to_status=to_status,
        changed_by_id=user_id,
        changed_by_name=user_name,
        notes=notes
    ).model_dump()


def create_custody_log(action: str, user_id: str, user_name: str, **kwargs) -> dict:
    """Create a custody log entry"""
    return CustodyLog(
        action=action,
        to_person_id=user_id,
        to_person_name=user_name,
        **kwargs
    ).model_dump()


# ==================== DIAGNOSIS ====================

@router.post("/{ticket_id}/diagnosis")
async def submit_diagnosis(
    ticket_id: str,
    data: DiagnosisRequest,
    admin: dict = Depends(get_current_admin)
):
    """Submit diagnosis for a ticket. Required before path selection."""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    # Must be in IN_PROGRESS status
    if ticket.get("status") != TicketStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot submit diagnosis in '{ticket.get('status')}' status. Ticket must be In Progress."
        )
    
    diagnosis = DiagnosisDetails(
        problem_identified=data.problem_identified,
        root_cause=data.root_cause,
        observations=data.observations,
        time_spent_minutes=data.time_spent_minutes,
        diagnosed_by_id=admin.get("id", ""),
        diagnosed_by_name=admin.get("name", "")
    ).model_dump()
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "diagnosis": diagnosis,
                "total_time_minutes": ticket.get("total_time_minutes", 0) + data.time_spent_minutes,
                "updated_at": get_ist_isoformat()
            }
        }
    )
    
    logger.info(f"Diagnosis submitted for ticket {ticket.get('ticket_number')}")
    return {"success": True, "message": "Diagnosis submitted. Please select a resolution path."}


# ==================== PATH SELECTION ====================

@router.post("/{ticket_id}/select-path")
async def select_resolution_path(
    ticket_id: str,
    data: PathSelectionRequest,
    admin: dict = Depends(get_current_admin)
):
    """
    MANDATORY: Select resolution path after diagnosis.
    
    Paths:
    - resolved_on_visit: Fix on-site, move to completed
    - pending_for_part: Wait for parts, pause SLA
    - device_to_backoffice: Take device for repair
    """
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    # Must be in IN_PROGRESS and have diagnosis
    if ticket.get("status") != TicketStatus.IN_PROGRESS.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot select path in '{ticket.get('status')}' status."
        )
    
    if not ticket.get("diagnosis"):
        raise HTTPException(
            status_code=400,
            detail="Diagnosis must be submitted before selecting a path."
        )
    
    # Validate path
    valid_paths = [p.value for p in ResolutionPath]
    if data.path not in valid_paths:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid path. Must be one of: {valid_paths}"
        )
    
    now = get_ist_isoformat()
    update_data = {
        "resolution_path": data.path,
        "path_selected_at": now,
        "path_selected_by_id": admin.get("id"),
        "path_selected_by_name": admin.get("name"),
        "updated_at": now
    }
    
    # Handle each path
    if data.path == ResolutionPath.RESOLVED_ON_VISIT.value:
        # Path 1: Resolved on site
        if not data.resolution_summary:
            raise HTTPException(status_code=400, detail="Resolution summary required for on-site resolution")
        
        update_data["status"] = TicketStatus.COMPLETED.value
        update_data["resolution_summary"] = data.resolution_summary
        update_data["resolved_at"] = now
        update_data["resolved_by_id"] = admin.get("id")
        update_data["resolved_by_name"] = admin.get("name")
        
        status_change = create_status_change(
            ticket.get("status"), TicketStatus.COMPLETED.value,
            admin.get("id", ""), admin.get("name", ""),
            f"Resolved on visit: {data.resolution_summary}"
        )
        
    elif data.path == ResolutionPath.PENDING_FOR_PART.value:
        # Path 2: Pending for parts
        update_data["status"] = TicketStatus.PENDING_PARTS.value
        update_data["requires_parts"] = True
        update_data["sla_paused"] = True
        update_data["sla_paused_at"] = now
        
        status_change = create_status_change(
            ticket.get("status"), TicketStatus.PENDING_PARTS.value,
            admin.get("id", ""), admin.get("name", ""),
            f"Pending for parts. {data.notes or ''}"
        )
        
    elif data.path == ResolutionPath.DEVICE_TO_BACKOFFICE.value:
        # Path 3: Device to back office
        update_data["status"] = TicketStatus.DEVICE_PICKUP.value
        update_data["device_in_custody"] = False  # Not yet picked up
        
        status_change = create_status_change(
            ticket.get("status"), TicketStatus.DEVICE_PICKUP.value,
            admin.get("id", ""), admin.get("name", ""),
            f"Device to be picked up for back office repair. {data.notes or ''}"
        )
    
    update_data["$push"] = {"status_history": status_change}
    
    # Separate $set and $push
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {k: v for k, v in update_data.items() if k != "$push"},
            "$push": {"status_history": status_change}
        }
    )
    
    logger.info(f"Path '{data.path}' selected for ticket {ticket.get('ticket_number')}")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== PATH 2: PENDING PARTS ====================

@router.post("/{ticket_id}/resume-from-parts")
async def resume_from_parts(
    ticket_id: str,
    data: ResumeFromPartsRequest,
    admin: dict = Depends(get_current_admin)
):
    """Resume work after parts received"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.PENDING_PARTS.value:
        raise HTTPException(
            status_code=400,
            detail="Can only resume tickets that are pending parts"
        )
    
    now = get_ist_isoformat()
    
    # Calculate SLA pause duration
    sla_paused_at = ticket.get("sla_paused_at")
    pause_minutes = 0
    if sla_paused_at:
        pause_start = datetime.fromisoformat(sla_paused_at.replace('Z', '+00:00'))
        pause_end = datetime.now(timezone.utc)
        pause_minutes = int((pause_end - pause_start).total_seconds() / 60)
    
    status_change = create_status_change(
        ticket.get("status"), TicketStatus.IN_PROGRESS.value,
        admin.get("id", ""), admin.get("name", ""),
        f"Resumed from pending parts. Parts received. {data.notes or ''}"
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.IN_PROGRESS.value,
                "sla_paused": False,
                "sla_resumed_at": now,
                "total_sla_paused_minutes": ticket.get("total_sla_paused_minutes", 0) + pause_minutes,
                "updated_at": now
            },
            "$push": {"status_history": status_change}
        }
    )
    
    logger.info(f"Ticket {ticket.get('ticket_number')} resumed from pending parts")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== PATH 3: DEVICE CUSTODY ====================

@router.post("/{ticket_id}/device-pickup")
async def record_device_pickup(
    ticket_id: str,
    data: DevicePickupRequest,
    admin: dict = Depends(get_current_admin)
):
    """Record device pickup - enters custody"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.DEVICE_PICKUP.value:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot record pickup in '{ticket.get('status')}' status. Device must be marked for pickup."
        )
    
    now = get_ist_isoformat()
    
    pickup = DevicePickup(
        pickup_type=data.pickup_type,
        pickup_person_id=data.pickup_person_id,
        pickup_person_name=data.pickup_person_name,
        pickup_date=data.pickup_date,
        pickup_time=data.pickup_time,
        pickup_location=data.pickup_location,
        device_condition=data.device_condition,
        accessories_taken=data.accessories_taken,
        customer_acknowledgement=data.customer_acknowledgement,
        customer_name=data.customer_name,
        notes=data.notes,
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", "")
    ).model_dump()
    
    custody_log = create_custody_log(
        action="pickup",
        user_id=data.pickup_person_id or admin.get("id", ""),
        user_name=data.pickup_person_name,
        from_location=data.pickup_location,
        to_location="Back Office",
        notes=f"Device picked up by {data.pickup_person_name} ({data.pickup_type})"
    )
    
    status_change = create_status_change(
        ticket.get("status"), TicketStatus.DEVICE_UNDER_REPAIR.value,
        admin.get("id", ""), admin.get("name", ""),
        f"Device picked up by {data.pickup_person_name}"
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.DEVICE_UNDER_REPAIR.value,
                "device_in_custody": True,
                "device_pickup": pickup,
                "updated_at": now
            },
            "$push": {
                "custody_log": custody_log,
                "status_history": status_change
            }
        }
    )
    
    logger.info(f"Device picked up for ticket {ticket.get('ticket_number')}")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== WARRANTY DECISION ====================

@router.post("/{ticket_id}/warranty-decision")
async def record_warranty_decision(
    ticket_id: str,
    data: WarrantyDecisionRequest,
    admin: dict = Depends(get_current_admin)
):
    """MANDATORY: Record warranty classification"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.DEVICE_UNDER_REPAIR.value:
        raise HTTPException(
            status_code=400,
            detail="Warranty decision can only be made when device is under repair"
        )
    
    # Validate warranty type
    valid_types = [w.value for w in WarrantyType]
    if data.warranty_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid warranty type. Must be one of: {valid_types}"
        )
    
    now = get_ist_isoformat()
    
    warranty = WarrantyDecision(
        warranty_type=data.warranty_type,
        decided_by_id=admin.get("id", ""),
        decided_by_name=admin.get("name", ""),
        amc_contract_id=data.amc_contract_id,
        notes=data.notes
    ).model_dump()
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "warranty_decision": warranty,
                "warranty_type": data.warranty_type,
                "updated_at": now
            }
        }
    )
    
    logger.info(f"Warranty decision '{data.warranty_type}' recorded for ticket {ticket.get('ticket_number')}")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== AMC REPAIR ====================

@router.post("/{ticket_id}/amc-repair")
async def record_amc_repair(
    ticket_id: str,
    data: AMCRepairRequest,
    admin: dict = Depends(get_current_admin)
):
    """Record AMC internal repair details"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.DEVICE_UNDER_REPAIR.value:
        raise HTTPException(status_code=400, detail="Device must be under repair")
    
    if ticket.get("warranty_type") != WarrantyType.UNDER_AMC.value:
        raise HTTPException(status_code=400, detail="Ticket must be under AMC warranty")
    
    now = get_ist_isoformat()
    
    amc_repair = AMCRepairDetails(
        assigned_engineer_id=data.assigned_engineer_id,
        assigned_engineer_name=data.assigned_engineer_name,
        issue_identified=data.issue_identified,
        repair_actions=data.repair_actions,
        parts_replaced=data.parts_replaced,
        repair_start_date=data.repair_start_date or now,
        repair_end_date=data.repair_end_date,
        internal_notes=data.internal_notes,
        status="in_progress" if not data.repair_end_date else "completed"
    ).model_dump()
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "amc_repair": amc_repair,
                "updated_at": now
            }
        }
    )
    
    logger.info(f"AMC repair recorded for ticket {ticket.get('ticket_number')}")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/{ticket_id}/amc-repair/complete")
async def complete_amc_repair(
    ticket_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Mark AMC repair as complete - device ready for delivery"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.DEVICE_UNDER_REPAIR.value:
        raise HTTPException(status_code=400, detail="Device must be under repair")
    
    if not ticket.get("amc_repair"):
        raise HTTPException(status_code=400, detail="AMC repair details must be recorded first")
    
    now = get_ist_isoformat()
    
    amc_repair = ticket.get("amc_repair", {})
    amc_repair["status"] = "completed"
    amc_repair["repair_end_date"] = now
    
    status_change = create_status_change(
        ticket.get("status"), TicketStatus.READY_FOR_DELIVERY.value,
        admin.get("id", ""), admin.get("name", ""),
        "AMC repair completed. Device ready for delivery."
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.READY_FOR_DELIVERY.value,
                "amc_repair": amc_repair,
                "updated_at": now
            },
            "$push": {"status_history": status_change}
        }
    )
    
    logger.info(f"AMC repair completed for ticket {ticket.get('ticket_number')}")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== OEM REPAIR ====================

@router.post("/{ticket_id}/oem-repair")
async def record_oem_repair(
    ticket_id: str,
    data: OEMRepairRequest,
    admin: dict = Depends(get_current_admin)
):
    """Record OEM repair tracking details"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.DEVICE_UNDER_REPAIR.value:
        raise HTTPException(status_code=400, detail="Device must be under repair")
    
    if ticket.get("warranty_type") != WarrantyType.UNDER_OEM.value:
        raise HTTPException(status_code=400, detail="Ticket must be under OEM warranty")
    
    now = get_ist_isoformat()
    
    oem_repair = OEMRepairDetails(
        oem_name=data.oem_name,
        oem_service_center=data.oem_service_center,
        oem_engineer_name=data.oem_engineer_name,
        oem_ticket_number=data.oem_ticket_number,
        other_reference_numbers=data.other_reference_numbers,
        sent_to_oem_date=data.sent_to_oem_date,
        repair_date=data.repair_date,
        received_back_date=data.received_back_date,
        repair_performed=data.repair_performed,
        parts_replaced_by_oem=data.parts_replaced_by_oem,
        oem_notes=data.oem_notes,
        status="pending" if not data.sent_to_oem_date else ("under_repair" if not data.received_back_date else "completed")
    ).model_dump()
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "oem_repair": oem_repair,
                "updated_at": now
            }
        }
    )
    
    logger.info(f"OEM repair recorded for ticket {ticket.get('ticket_number')}")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/{ticket_id}/oem-repair/complete")
async def complete_oem_repair(
    ticket_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Mark OEM repair as complete - device ready for delivery"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.DEVICE_UNDER_REPAIR.value:
        raise HTTPException(status_code=400, detail="Device must be under repair")
    
    if not ticket.get("oem_repair"):
        raise HTTPException(status_code=400, detail="OEM repair details must be recorded first")
    
    oem_repair = ticket.get("oem_repair", {})
    if not oem_repair.get("received_back_date"):
        raise HTTPException(status_code=400, detail="Device must be received back from OEM before completion")
    
    now = get_ist_isoformat()
    
    oem_repair["status"] = "completed"
    
    status_change = create_status_change(
        ticket.get("status"), TicketStatus.READY_FOR_DELIVERY.value,
        admin.get("id", ""), admin.get("name", ""),
        "OEM repair completed. Device ready for delivery."
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.READY_FOR_DELIVERY.value,
                "oem_repair": oem_repair,
                "updated_at": now
            },
            "$push": {"status_history": status_change}
        }
    )
    
    logger.info(f"OEM repair completed for ticket {ticket.get('ticket_number')}")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== DEVICE DELIVERY ====================

@router.post("/{ticket_id}/device-delivery")
async def record_device_delivery(
    ticket_id: str,
    data: DeviceDeliveryRequest,
    admin: dict = Depends(get_current_admin)
):
    """Record device delivery to customer"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    valid_statuses = [TicketStatus.READY_FOR_DELIVERY.value, TicketStatus.OUT_FOR_DELIVERY.value]
    if ticket.get("status") not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail="Device must be ready for delivery or out for delivery"
        )
    
    now = get_ist_isoformat()
    
    delivery = DeviceDelivery(
        delivery_type=data.delivery_type,
        delivery_person_id=data.delivery_person_id,
        delivery_person_name=data.delivery_person_name,
        delivery_date=data.delivery_date,
        delivery_time=data.delivery_time,
        delivery_location=data.delivery_location,
        delivered_to_name=data.delivered_to_name,
        delivered_to_designation=data.delivered_to_designation,
        customer_confirmation=data.customer_confirmation,
        notes=data.notes,
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", "")
    ).model_dump()
    
    custody_log = create_custody_log(
        action="delivery",
        user_id=data.delivery_person_id or admin.get("id", ""),
        user_name=data.delivery_person_name,
        from_location="Back Office",
        to_location=data.delivery_location,
        notes=f"Device delivered by {data.delivery_person_name} to {data.delivered_to_name}"
    )
    
    status_change = create_status_change(
        ticket.get("status"), TicketStatus.COMPLETED.value,
        admin.get("id", ""), admin.get("name", ""),
        f"Device delivered to {data.delivered_to_name}"
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.COMPLETED.value,
                "device_in_custody": False,
                "device_delivery": delivery,
                "resolved_at": now,
                "resolved_by_id": admin.get("id"),
                "resolved_by_name": admin.get("name"),
                "updated_at": now
            },
            "$push": {
                "custody_log": custody_log,
                "status_history": status_change
            }
        }
    )
    
    logger.info(f"Device delivered for ticket {ticket.get('ticket_number')}")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/{ticket_id}/mark-out-for-delivery")
async def mark_out_for_delivery(
    ticket_id: str,
    delivery_person_id: str,
    delivery_person_name: str,
    admin: dict = Depends(get_current_admin)
):
    """Mark device as out for delivery (optional step)"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.READY_FOR_DELIVERY.value:
        raise HTTPException(status_code=400, detail="Device must be ready for delivery")
    
    now = get_ist_isoformat()
    
    status_change = create_status_change(
        ticket.get("status"), TicketStatus.OUT_FOR_DELIVERY.value,
        admin.get("id", ""), admin.get("name", ""),
        f"Device out for delivery with {delivery_person_name}"
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.OUT_FOR_DELIVERY.value,
                "updated_at": now
            },
            "$push": {"status_history": status_change}
        }
    )
    
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== FINAL CLOSURE ====================

@router.post("/{ticket_id}/close")
async def close_ticket(
    ticket_id: str,
    closure_notes: str = None,
    admin: dict = Depends(get_current_admin)
):
    """Final ticket closure with audit lock"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    if ticket.get("status") != TicketStatus.COMPLETED.value:
        raise HTTPException(
            status_code=400,
            detail="Only completed tickets can be closed"
        )
    
    # Validate Path 3 requirements
    if ticket.get("resolution_path") == ResolutionPath.DEVICE_TO_BACKOFFICE.value:
        if not ticket.get("device_delivery"):
            raise HTTPException(
                status_code=400,
                detail="Cannot close ticket without delivery details for back office repair"
            )
        if ticket.get("device_in_custody"):
            raise HTTPException(
                status_code=400,
                detail="Device is still in custody. Record delivery first."
            )
    
    now = get_ist_isoformat()
    
    status_change = create_status_change(
        ticket.get("status"), TicketStatus.CLOSED.value,
        admin.get("id", ""), admin.get("name", ""),
        closure_notes or "Ticket closed"
    )
    
    await db.service_tickets_new.update_one(
        {"id": ticket_id},
        {
            "$set": {
                "status": TicketStatus.CLOSED.value,
                "closed_at": now,
                "closed_by_id": admin.get("id"),
                "closed_by_name": admin.get("name"),
                "closure_notes": closure_notes,
                "updated_at": now
            },
            "$push": {"status_history": status_change}
        }
    )
    
    logger.info(f"Ticket {ticket.get('ticket_number')} closed")
    return await db.service_tickets_new.find_one({"id": ticket_id}, {"_id": 0})


# ==================== WORKFLOW STATUS ====================

@router.get("/{ticket_id}/workflow-status")
async def get_workflow_status(
    ticket_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get current workflow status and available actions"""
    org_id = admin.get("organization_id")
    ticket = await get_ticket_or_404(ticket_id, org_id)
    
    status = ticket.get("status")
    path = ticket.get("resolution_path")
    
    available_actions = []
    required_actions = []
    
    if status == TicketStatus.IN_PROGRESS.value:
        if not ticket.get("diagnosis"):
            required_actions.append("submit_diagnosis")
            available_actions.append("submit_diagnosis")
        else:
            required_actions.append("select_path")
            available_actions.append("select_path")
    
    elif status == TicketStatus.PENDING_PARTS.value:
        available_actions.append("resume_from_parts")
    
    elif status == TicketStatus.DEVICE_PICKUP.value:
        required_actions.append("record_pickup")
        available_actions.append("record_pickup")
    
    elif status == TicketStatus.DEVICE_UNDER_REPAIR.value:
        if not ticket.get("warranty_decision"):
            required_actions.append("warranty_decision")
            available_actions.append("warranty_decision")
        else:
            warranty_type = ticket.get("warranty_type")
            if warranty_type == WarrantyType.UNDER_AMC.value:
                available_actions.append("record_amc_repair")
                available_actions.append("complete_amc_repair")
            elif warranty_type == WarrantyType.UNDER_OEM.value:
                available_actions.append("record_oem_repair")
                available_actions.append("complete_oem_repair")
    
    elif status == TicketStatus.READY_FOR_DELIVERY.value:
        available_actions.append("mark_out_for_delivery")
        available_actions.append("record_delivery")
    
    elif status == TicketStatus.OUT_FOR_DELIVERY.value:
        required_actions.append("record_delivery")
        available_actions.append("record_delivery")
    
    elif status == TicketStatus.COMPLETED.value:
        available_actions.append("close_ticket")
    
    return {
        "ticket_id": ticket_id,
        "ticket_number": ticket.get("ticket_number"),
        "status": status,
        "resolution_path": path,
        "warranty_type": ticket.get("warranty_type"),
        "device_in_custody": ticket.get("device_in_custody", False),
        "available_actions": available_actions,
        "required_actions": required_actions,
        "has_diagnosis": bool(ticket.get("diagnosis")),
        "has_warranty_decision": bool(ticket.get("warranty_decision")),
        "has_pickup": bool(ticket.get("device_pickup")),
        "has_delivery": bool(ticket.get("device_delivery"))
    }
