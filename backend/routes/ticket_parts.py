"""
Ticket Parts API Routes
=======================
Parts request and issue management for service tickets.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin
from models.ticket_parts import (
    TicketPartRequest, TicketPartRequestCreate, TicketPartRequestApproval,
    TicketPartIssue, TicketPartIssueCreate, TicketPartReturnCreate,
    PartRequestStatus
)
from models.inventory import StockLedger, StockTransactionType
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/ticket-parts", tags=["Ticket Parts"])


# ==================== PART REQUESTS ====================

@router.get("/requests")
async def list_part_requests(
    admin: dict = Depends(get_current_admin),
    ticket_id: Optional[str] = None,
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    requested_by_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200)
):
    """List parts requests"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if ticket_id:
        query["ticket_id"] = ticket_id
    if status:
        query["status"] = status
    if urgency:
        query["urgency"] = urgency
    if requested_by_id:
        query["requested_by_id"] = requested_by_id
    
    total = await db.ticket_part_requests.count_documents(query)
    skip = (page - 1) * limit
    
    requests = await db.ticket_part_requests.find(
        query, {"_id": 0}
    ).sort("requested_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "requests": requests,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/requests/pending")
async def get_pending_requests(admin: dict = Depends(get_current_admin)):
    """Get pending parts requests awaiting approval"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    requests = await db.ticket_part_requests.find(
        {
            "organization_id": org_id,
            "status": PartRequestStatus.REQUESTED.value,
            "is_deleted": {"$ne": True}
        },
        {"_id": 0}
    ).sort([("urgency", -1), ("requested_at", 1)]).to_list(100)
    
    return {"requests": requests}


@router.get("/requests/{request_id}")
async def get_part_request(request_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific parts request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    request = await db.ticket_part_requests.find_one(
        {"id": request_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not request:
        raise HTTPException(status_code=404, detail="Part request not found")
    
    return request


@router.post("/requests")
async def create_part_request(
    data: TicketPartRequestCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new parts request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Verify ticket exists
    ticket = await db.service_tickets_new.find_one(
        {"id": data.ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "ticket_number": 1, "status": 1}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get item details
    item = await db.item_masters.find_one(
        {"id": data.item_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "sku": 1, "cost_price": 1}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    request = TicketPartRequest(
        organization_id=org_id,
        ticket_id=data.ticket_id,
        ticket_number=ticket["ticket_number"],
        visit_id=data.visit_id,
        item_id=data.item_id,
        item_name=item["name"],
        item_sku=item.get("sku"),
        quantity_requested=data.quantity_requested,
        request_notes=data.request_notes,
        urgency=data.urgency,
        requested_by_id=admin.get("id", ""),
        requested_by_name=admin.get("name", ""),
        estimated_unit_cost=item.get("cost_price", 0),
        estimated_total_cost=item.get("cost_price", 0) * data.quantity_requested
    )
    
    await db.ticket_part_requests.insert_one(request.model_dump())
    
    # Mark ticket as requiring parts
    await db.service_tickets_new.update_one(
        {"id": data.ticket_id},
        {"$set": {"requires_parts": True, "updated_at": get_ist_isoformat()}}
    )
    
    return await db.ticket_part_requests.find_one({"id": request.id}, {"_id": 0})


@router.post("/requests/{request_id}/approve")
async def approve_part_request(
    request_id: str,
    data: TicketPartRequestApproval,
    admin: dict = Depends(get_current_admin)
):
    """Approve or reject a parts request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    request = await db.ticket_part_requests.find_one({
        "id": request_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not request:
        raise HTTPException(status_code=404, detail="Part request not found")
    
    if request.get("status") != PartRequestStatus.REQUESTED.value:
        raise HTTPException(status_code=400, detail="Request is not pending approval")
    
    now = get_ist_isoformat()
    
    if data.approved:
        qty_approved = data.quantity_approved or request.get("quantity_requested", 1)
        
        await db.ticket_part_requests.update_one(
            {"id": request_id},
            {
                "$set": {
                    "status": PartRequestStatus.APPROVED.value,
                    "quantity_approved": qty_approved,
                    "approved_by_id": admin.get("id"),
                    "approved_by_name": admin.get("name"),
                    "approved_at": now,
                    "approval_notes": data.notes,
                    "updated_at": now
                }
            }
        )
    else:
        await db.ticket_part_requests.update_one(
            {"id": request_id},
            {
                "$set": {
                    "status": PartRequestStatus.REJECTED.value,
                    "rejected_by_id": admin.get("id"),
                    "rejected_by_name": admin.get("name"),
                    "rejected_at": now,
                    "rejection_reason": data.notes,
                    "updated_at": now
                }
            }
        )
    
    return await db.ticket_part_requests.find_one({"id": request_id}, {"_id": 0})


@router.delete("/requests/{request_id}")
async def cancel_part_request(request_id: str, admin: dict = Depends(get_current_admin)):
    """Cancel a parts request"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    request = await db.ticket_part_requests.find_one({
        "id": request_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not request:
        raise HTTPException(status_code=404, detail="Part request not found")
    
    if request.get("status") not in [PartRequestStatus.REQUESTED.value, PartRequestStatus.APPROVED.value]:
        raise HTTPException(status_code=400, detail="Cannot cancel request in current status")
    
    await db.ticket_part_requests.update_one(
        {"id": request_id},
        {
            "$set": {
                "status": PartRequestStatus.CANCELLED.value,
                "updated_at": get_ist_isoformat()
            }
        }
    )
    
    return {"success": True, "message": "Part request cancelled"}


# ==================== PART ISSUES ====================

@router.get("/issues")
async def list_part_issues(
    admin: dict = Depends(get_current_admin),
    ticket_id: Optional[str] = None,
    visit_id: Optional[str] = None,
    item_id: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200)
):
    """List parts issued"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if ticket_id:
        query["ticket_id"] = ticket_id
    if visit_id:
        query["visit_id"] = visit_id
    if item_id:
        query["item_id"] = item_id
    
    total = await db.ticket_part_issues.count_documents(query)
    skip = (page - 1) * limit
    
    issues = await db.ticket_part_issues.find(
        query, {"_id": 0}
    ).sort("issued_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "issues": issues,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/issues/{issue_id}")
async def get_part_issue(issue_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific part issue"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    issue = await db.ticket_part_issues.find_one(
        {"id": issue_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not issue:
        raise HTTPException(status_code=404, detail="Part issue not found")
    
    return issue


@router.post("/issues")
async def issue_part(
    data: TicketPartIssueCreate,
    admin: dict = Depends(get_current_admin)
):
    """Issue parts to a ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Verify ticket exists
    ticket = await db.service_tickets_new.find_one(
        {"id": data.ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "ticket_number": 1}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get item details
    item = await db.item_masters.find_one(
        {"id": data.item_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "sku": 1, "cost_price": 1, "unit_price": 1, "is_serialized": 1}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Validate serial numbers for serialized items
    if item.get("is_serialized"):
        if not data.serial_numbers or len(data.serial_numbers) != data.quantity_issued:
            raise HTTPException(
                status_code=400,
                detail=f"Serial numbers required. Expected {data.quantity_issued} serial numbers."
            )
    
    # Get location details
    location = await db.inventory_locations.find_one(
        {"id": data.issued_from_location_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1}
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check available stock
    pipeline = [
        {"$match": {"organization_id": org_id, "item_id": data.item_id, "location_id": data.issued_from_location_id}},
        {"$group": {
            "_id": None,
            "total_in": {"$sum": "$qty_in"},
            "total_out": {"$sum": "$qty_out"}
        }},
        {"$project": {
            "current_stock": {"$subtract": ["$total_in", "$total_out"]}
        }}
    ]
    stock_result = await db.stock_ledger.aggregate(pipeline).to_list(1)
    current_stock = stock_result[0]["current_stock"] if stock_result else 0
    
    if current_stock < data.quantity_issued:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {current_stock}, Requested: {data.quantity_issued}"
        )
    
    # Determine costs
    unit_cost = data.unit_cost if data.unit_cost is not None else item.get("cost_price", 0)
    unit_price = data.unit_price if data.unit_price is not None else item.get("unit_price", 0)
    
    # Create stock ledger entry (OUT)
    ledger_entry = StockLedger(
        organization_id=org_id,
        item_id=data.item_id,
        item_name=item["name"],
        location_id=data.issued_from_location_id,
        location_name=location["name"],
        qty_out=data.quantity_issued,
        serial_numbers=data.serial_numbers or [],
        transaction_type=StockTransactionType.ISSUE.value,
        reference_type="service_ticket",
        reference_id=data.ticket_id,
        reference_number=ticket["ticket_number"],
        unit_cost=unit_cost,
        total_cost=unit_cost * data.quantity_issued,
        notes=data.notes,
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", ""),
        running_balance=current_stock - data.quantity_issued
    )
    
    await db.stock_ledger.insert_one(ledger_entry.model_dump())
    
    # Get received by name if provided
    received_by_name = None
    if data.received_by_id:
        tech = await db.staff_users.find_one(
            {"id": data.received_by_id, "organization_id": org_id},
            {"name": 1}
        ) or await db.organization_members.find_one(
            {"id": data.received_by_id},
            {"name": 1}
        )
        received_by_name = tech.get("name") if tech else None
    
    # Create part issue record
    issue = TicketPartIssue(
        organization_id=org_id,
        ticket_id=data.ticket_id,
        ticket_number=ticket["ticket_number"],
        visit_id=data.visit_id,
        part_request_id=data.part_request_id,
        item_id=data.item_id,
        item_name=item["name"],
        item_sku=item.get("sku"),
        quantity_issued=data.quantity_issued,
        quantity_used=data.quantity_issued,  # Initially all used
        serial_numbers=data.serial_numbers or [],
        issued_from_location_id=data.issued_from_location_id,
        issued_from_location_name=location["name"],
        ledger_entry_id=ledger_entry.id,
        unit_cost=unit_cost,
        total_cost=unit_cost * data.quantity_issued,
        unit_price=unit_price,
        total_price=unit_price * data.quantity_issued,
        is_billable=data.is_billable,
        is_warranty_claim=data.is_warranty_claim,
        issued_by_id=admin.get("id", ""),
        issued_by_name=admin.get("name", ""),
        received_by_id=data.received_by_id,
        received_by_name=received_by_name,
        notes=data.notes
    )
    
    await db.ticket_part_issues.insert_one(issue.model_dump())
    
    # Update part request status if linked
    if data.part_request_id:
        # Get request to update quantity
        request = await db.ticket_part_requests.find_one({"id": data.part_request_id})
        if request:
            new_qty_issued = request.get("quantity_issued", 0) + data.quantity_issued
            status = PartRequestStatus.ISSUED.value if new_qty_issued >= request.get("quantity_approved", 0) else request.get("status")
            
            await db.ticket_part_requests.update_one(
                {"id": data.part_request_id},
                {
                    "$set": {
                        "status": status,
                        "quantity_issued": new_qty_issued,
                        "updated_at": get_ist_isoformat()
                    },
                    "$push": {"issue_ids": issue.id}
                }
            )
    
    # Update ticket parts cost
    # Get all parts issued for this ticket
    parts_issued = await db.ticket_part_issues.find(
        {"ticket_id": data.ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"total_cost": 1}
    ).to_list(100)
    
    total_parts_cost = sum(p.get("total_cost", 0) for p in parts_issued)
    
    # Update ticket
    ticket_doc = await db.service_tickets_new.find_one(
        {"id": data.ticket_id},
        {"labour_cost": 1, "travel_cost": 1, "other_cost": 1}
    )
    total_cost = (
        ticket_doc.get("labour_cost", 0) +
        ticket_doc.get("travel_cost", 0) +
        ticket_doc.get("other_cost", 0) +
        total_parts_cost
    )
    
    await db.service_tickets_new.update_one(
        {"id": data.ticket_id},
        {
            "$set": {
                "parts_cost": total_parts_cost,
                "total_cost": total_cost,
                "updated_at": get_ist_isoformat()
            }
        }
    )
    
    return await db.ticket_part_issues.find_one({"id": issue.id}, {"_id": 0})


@router.post("/issues/{issue_id}/return")
async def return_part(
    issue_id: str,
    data: TicketPartReturnCreate,
    admin: dict = Depends(get_current_admin)
):
    """Return unused parts from an issue"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    issue = await db.ticket_part_issues.find_one({
        "id": issue_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not issue:
        raise HTTPException(status_code=404, detail="Part issue not found")
    
    # Check if return quantity is valid
    available_to_return = issue.get("quantity_issued", 0) - issue.get("quantity_returned", 0)
    if data.quantity_returned > available_to_return:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot return {data.quantity_returned}. Only {available_to_return} available to return."
        )
    
    # Get return location details
    return_location = await db.inventory_locations.find_one(
        {"id": data.return_location_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1}
    )
    if not return_location:
        raise HTTPException(status_code=404, detail="Return location not found")
    
    # Create stock ledger entry (IN)
    ledger_entry = StockLedger(
        organization_id=org_id,
        item_id=issue["item_id"],
        item_name=issue["item_name"],
        location_id=data.return_location_id,
        location_name=return_location["name"],
        qty_in=data.quantity_returned,
        serial_numbers=data.serial_numbers or [],
        transaction_type=StockTransactionType.RETURN.value,
        reference_type="service_ticket_return",
        reference_id=issue["ticket_id"],
        reference_number=issue["ticket_number"],
        notes=data.return_reason,
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", "")
    )
    
    await db.stock_ledger.insert_one(ledger_entry.model_dump())
    
    now = get_ist_isoformat()
    new_qty_returned = issue.get("quantity_returned", 0) + data.quantity_returned
    new_qty_used = issue.get("quantity_issued", 0) - new_qty_returned
    
    # Recalculate costs
    unit_cost = issue.get("unit_cost", 0)
    unit_price = issue.get("unit_price", 0)
    
    await db.ticket_part_issues.update_one(
        {"id": issue_id},
        {
            "$set": {
                "quantity_returned": new_qty_returned,
                "quantity_used": new_qty_used,
                "total_cost": unit_cost * new_qty_used,
                "total_price": unit_price * new_qty_used,
                "returned_at": now,
                "returned_by_id": admin.get("id"),
                "returned_by_name": admin.get("name"),
                "return_reason": data.return_reason,
                "return_location_id": data.return_location_id,
                "return_ledger_entry_id": ledger_entry.id,
                "updated_at": now
            }
        }
    )
    
    # Update ticket parts cost
    parts_issued = await db.ticket_part_issues.find(
        {"ticket_id": issue["ticket_id"], "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"total_cost": 1}
    ).to_list(100)
    
    total_parts_cost = sum(p.get("total_cost", 0) for p in parts_issued)
    
    await db.service_tickets_new.update_one(
        {"id": issue["ticket_id"]},
        {"$set": {"parts_cost": total_parts_cost, "updated_at": now}}
    )
    
    return await db.ticket_part_issues.find_one({"id": issue_id}, {"_id": 0})
