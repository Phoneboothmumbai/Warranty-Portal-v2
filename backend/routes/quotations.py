"""
Quotation API Routes
Handles quotation generation, sending, and approval workflow
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from services.auth import get_current_admin
from services.database import db
from models.service_ticket import Quotation, QuotationItem, QuotationStatus, TicketStatus, get_ist_isoformat

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/quotations")


# ==================== REQUEST MODELS ====================

class QuotationItemCreate(BaseModel):
    item_type: str = "part"
    description: str
    quantity: int = 1
    unit_price: float = 0
    part_id: Optional[str] = None
    part_number: Optional[str] = None


class QuotationCreate(BaseModel):
    ticket_id: str
    items: List[QuotationItemCreate] = []
    tax_rate: float = 18.0
    valid_days: int = 7
    terms_and_conditions: Optional[str] = None
    internal_notes: Optional[str] = None


class QuotationUpdate(BaseModel):
    items: Optional[List[QuotationItemCreate]] = None
    tax_rate: Optional[float] = None
    valid_until: Optional[str] = None
    terms_and_conditions: Optional[str] = None
    internal_notes: Optional[str] = None


class QuotationApproval(BaseModel):
    approved: bool
    customer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


# ==================== HELPER FUNCTIONS ====================

async def generate_quotation_number(org_id: str) -> str:
    """Generate unique quotation number"""
    prefix = "QT"
    today = datetime.now().strftime("%y%m%d")
    
    # Get count for today
    count = await db.quotations.count_documents({
        "organization_id": org_id,
        "quotation_number": {"$regex": f"^{prefix}{today}"}
    })
    
    return f"{prefix}{today}{count + 1:03d}"


def calculate_totals(items: List[QuotationItem], tax_rate: float) -> tuple:
    """Calculate subtotal, tax, and total"""
    subtotal = sum(item.total_price for item in items)
    tax_amount = subtotal * (tax_rate / 100)
    total = subtotal + tax_amount
    return subtotal, tax_amount, total


# ==================== ENDPOINTS ====================

@router.get("")
async def list_quotations(
    admin: dict = Depends(get_current_admin),
    ticket_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 20
):
    """List quotations"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if ticket_id:
        query["ticket_id"] = ticket_id
    if status:
        query["status"] = status
    
    total = await db.quotations.count_documents(query)
    skip = (page - 1) * limit
    
    quotations = await db.quotations.find(query, {"_id": 0})\
        .sort("created_at", -1)\
        .skip(skip)\
        .limit(limit)\
        .to_list(limit)
    
    return {
        "quotations": quotations,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/{quotation_id}")
async def get_quotation(quotation_id: str, admin: dict = Depends(get_current_admin)):
    """Get single quotation"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    quotation = await db.quotations.find_one({
        "id": quotation_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    return quotation


@router.post("")
async def create_quotation(
    data: QuotationCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a quotation for a ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Get ticket
    ticket = await db.service_tickets_new.find_one({
        "id": data.ticket_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Ticket must be in pending_parts status
    if ticket.get("status") != TicketStatus.PENDING_PARTS.value:
        raise HTTPException(
            status_code=400,
            detail="Quotation can only be created for tickets pending for parts"
        )
    
    # Check if quotation already exists
    existing = await db.quotations.find_one({
        "ticket_id": data.ticket_id,
        "is_deleted": {"$ne": True},
        "status": {"$nin": [QuotationStatus.REJECTED.value, QuotationStatus.EXPIRED.value]}
    })
    if existing:
        raise HTTPException(
            status_code=400,
            detail="A quotation already exists for this ticket"
        )
    
    # Create quotation items
    items = []
    for item_data in data.items:
        item = QuotationItem(
            item_type=item_data.item_type,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=item_data.quantity * item_data.unit_price,
            part_id=item_data.part_id,
            part_number=item_data.part_number
        )
        items.append(item)
    
    # Calculate totals
    subtotal, tax_amount, total = calculate_totals(items, data.tax_rate)
    
    # Generate quotation number
    quotation_number = await generate_quotation_number(org_id)
    
    # Calculate validity
    valid_until = (datetime.now() + timedelta(days=data.valid_days)).isoformat()
    
    quotation = Quotation(
        organization_id=org_id,
        ticket_id=data.ticket_id,
        ticket_number=ticket.get("ticket_number"),
        quotation_number=quotation_number,
        company_id=ticket.get("company_id"),
        company_name=ticket.get("company_name"),
        contact_name=ticket.get("contact_name"),
        contact_email=ticket.get("contact_email"),
        contact_phone=ticket.get("contact_phone"),
        status=QuotationStatus.DRAFT.value,
        items=[item.model_dump() for item in items],
        subtotal=subtotal,
        tax_rate=data.tax_rate,
        tax_amount=tax_amount,
        total_amount=total,
        valid_until=valid_until,
        terms_and_conditions=data.terms_and_conditions,
        internal_notes=data.internal_notes,
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", "")
    )
    
    await db.quotations.insert_one(quotation.model_dump())
    
    # Update ticket with quotation reference
    await db.service_tickets_new.update_one(
        {"id": data.ticket_id},
        {"$set": {
            "quotation_id": quotation.id,
            "quotation_status": QuotationStatus.DRAFT.value,
            "updated_at": get_ist_isoformat()
        }}
    )
    
    logger.info(f"Created quotation {quotation_number} for ticket {ticket.get('ticket_number')}")
    
    return await db.quotations.find_one({"id": quotation.id}, {"_id": 0})


@router.put("/{quotation_id}")
async def update_quotation(
    quotation_id: str,
    data: QuotationUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update quotation (only draft status)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    quotation = await db.quotations.find_one({
        "id": quotation_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.get("status") != QuotationStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail="Can only update draft quotations"
        )
    
    update_dict = {"updated_at": get_ist_isoformat()}
    
    if data.items is not None:
        items = []
        for item_data in data.items:
            item = QuotationItem(
                item_type=item_data.item_type,
                description=item_data.description,
                quantity=item_data.quantity,
                unit_price=item_data.unit_price,
                total_price=item_data.quantity * item_data.unit_price,
                part_id=item_data.part_id,
                part_number=item_data.part_number
            )
            items.append(item)
        
        tax_rate = data.tax_rate if data.tax_rate is not None else quotation.get("tax_rate", 18.0)
        subtotal, tax_amount, total = calculate_totals(items, tax_rate)
        
        update_dict["items"] = [item.model_dump() for item in items]
        update_dict["subtotal"] = subtotal
        update_dict["tax_amount"] = tax_amount
        update_dict["total_amount"] = total
    
    if data.tax_rate is not None:
        update_dict["tax_rate"] = data.tax_rate
    if data.valid_until is not None:
        update_dict["valid_until"] = data.valid_until
    if data.terms_and_conditions is not None:
        update_dict["terms_and_conditions"] = data.terms_and_conditions
    if data.internal_notes is not None:
        update_dict["internal_notes"] = data.internal_notes
    
    await db.quotations.update_one({"id": quotation_id}, {"$set": update_dict})
    
    return await db.quotations.find_one({"id": quotation_id}, {"_id": 0})


@router.post("/{quotation_id}/send")
async def send_quotation(quotation_id: str, admin: dict = Depends(get_current_admin)):
    """Send quotation to customer"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    quotation = await db.quotations.find_one({
        "id": quotation_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.get("status") != QuotationStatus.DRAFT.value:
        raise HTTPException(
            status_code=400,
            detail="Can only send draft quotations"
        )
    
    if not quotation.get("items") or len(quotation.get("items", [])) == 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot send empty quotation. Add at least one item."
        )
    
    now = get_ist_isoformat()
    
    await db.quotations.update_one(
        {"id": quotation_id},
        {"$set": {
            "status": QuotationStatus.SENT.value,
            "sent_at": now,
            "updated_at": now
        }}
    )
    
    # Update ticket
    await db.service_tickets_new.update_one(
        {"id": quotation.get("ticket_id")},
        {"$set": {
            "quotation_status": QuotationStatus.SENT.value,
            "quotation_sent_at": now,
            "updated_at": now
        }}
    )
    
    # TODO: Send email notification to customer
    logger.info(f"Quotation {quotation.get('quotation_number')} sent to customer")
    
    return await db.quotations.find_one({"id": quotation_id}, {"_id": 0})


@router.post("/{quotation_id}/approve")
async def approve_quotation(
    quotation_id: str,
    data: QuotationApproval,
    admin: dict = Depends(get_current_admin)
):
    """Approve or reject quotation (by back office on behalf of customer)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    quotation = await db.quotations.find_one({
        "id": quotation_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.get("status") != QuotationStatus.SENT.value:
        raise HTTPException(
            status_code=400,
            detail="Can only approve/reject sent quotations"
        )
    
    now = get_ist_isoformat()
    
    if data.approved:
        await db.quotations.update_one(
            {"id": quotation_id},
            {"$set": {
                "status": QuotationStatus.APPROVED.value,
                "approved_at": now,
                "approved_by": admin.get("name"),
                "customer_notes": data.customer_notes,
                "updated_at": now
            }}
        )
        
        # Update ticket - quotation approved, can now be worked on
        await db.service_tickets_new.update_one(
            {"id": quotation.get("ticket_id")},
            {"$set": {
                "quotation_status": QuotationStatus.APPROVED.value,
                "quotation_approved_at": now,
                "quotation_approved_by": admin.get("name"),
                "updated_at": now
            }}
        )
        
        logger.info(f"Quotation {quotation.get('quotation_number')} approved")
    else:
        if not data.rejection_reason:
            raise HTTPException(
                status_code=400,
                detail="Rejection reason is required"
            )
        
        await db.quotations.update_one(
            {"id": quotation_id},
            {"$set": {
                "status": QuotationStatus.REJECTED.value,
                "rejection_reason": data.rejection_reason,
                "customer_notes": data.customer_notes,
                "updated_at": now
            }}
        )
        
        # Update ticket
        await db.service_tickets_new.update_one(
            {"id": quotation.get("ticket_id")},
            {"$set": {
                "quotation_status": QuotationStatus.REJECTED.value,
                "updated_at": now
            }}
        )
        
        logger.info(f"Quotation {quotation.get('quotation_number')} rejected")
    
    return await db.quotations.find_one({"id": quotation_id}, {"_id": 0})


@router.delete("/{quotation_id}")
async def delete_quotation(quotation_id: str, admin: dict = Depends(get_current_admin)):
    """Delete quotation (soft delete)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    quotation = await db.quotations.find_one({
        "id": quotation_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not quotation:
        raise HTTPException(status_code=404, detail="Quotation not found")
    
    if quotation.get("status") not in [QuotationStatus.DRAFT.value, QuotationStatus.REJECTED.value]:
        raise HTTPException(
            status_code=400,
            detail="Can only delete draft or rejected quotations"
        )
    
    await db.quotations.update_one(
        {"id": quotation_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    # Clear quotation reference from ticket
    await db.service_tickets_new.update_one(
        {"id": quotation.get("ticket_id")},
        {"$set": {
            "quotation_id": None,
            "quotation_status": None,
            "updated_at": get_ist_isoformat()
        }}
    )
    
    return {"success": True, "message": "Quotation deleted"}
