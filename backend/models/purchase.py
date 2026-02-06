"""
Purchase Models
===============
Purchase Request and Purchase Order management for procurement workflow.
"""
import uuid
import random
import string
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from utils.helpers import get_ist_isoformat


class PurchaseRequestStatus(str, Enum):
    """Status of a purchase request"""
    DRAFT = "draft"              # Being prepared
    PENDING = "pending"          # Awaiting approval
    APPROVED = "approved"        # Approved for ordering
    ORDERED = "ordered"          # PO sent to vendor
    PARTIAL = "partial"          # Partially received
    RECEIVED = "received"        # Fully received
    CANCELLED = "cancelled"      # Cancelled
    REJECTED = "rejected"        # Approval rejected


class PurchaseRequestItem(BaseModel):
    """Line item in a purchase request"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Item reference
    item_id: str  # Reference to ItemMaster
    item_name: str
    item_sku: Optional[str] = None
    
    # Quantity
    quantity_requested: int = 1
    quantity_approved: int = 0
    quantity_ordered: int = 0
    quantity_received: int = 0
    
    # Pricing (estimated at request, confirmed at order)
    estimated_unit_price: float = 0
    actual_unit_price: float = 0
    
    # Vendor suggestion
    suggested_vendor_id: Optional[str] = None
    suggested_vendor_name: Optional[str] = None
    
    # For which ticket (if applicable)
    ticket_id: Optional[str] = None
    ticket_number: Optional[str] = None
    
    # Notes
    notes: Optional[str] = None
    
    # Status tracking
    status: str = "pending"  # pending, approved, ordered, received, cancelled


class PurchaseRequest(BaseModel):
    """
    Purchase Request - Request for parts/items procurement.
    
    Workflow:
    DRAFT → PENDING → APPROVED → ORDERED → (PARTIAL) → RECEIVED
                   ↓
                REJECTED
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # PR identification
    pr_number: str  # Auto-generated PR number like "PR-2025-001234"
    
    # Status
    status: str = PurchaseRequestStatus.DRAFT.value
    
    # Vendor (can be selected at request or at approval)
    vendor_id: Optional[str] = None
    vendor_name: Optional[str] = None
    
    # Items
    items: List[PurchaseRequestItem] = Field(default_factory=list)
    
    # Totals (calculated)
    total_items: int = 0
    estimated_total: float = 0
    actual_total: float = 0
    
    # Urgency
    priority: str = "medium"  # low, medium, high, urgent
    required_by_date: Optional[str] = None
    
    # Delivery location
    delivery_location_id: Optional[str] = None
    delivery_location_name: Optional[str] = None
    
    # Related service ticket (if PR is for a specific ticket)
    ticket_id: Optional[str] = None
    ticket_number: Optional[str] = None
    
    # Requester
    requested_by_id: str = ""
    requested_by_name: str = ""
    requested_at: str = Field(default_factory=get_ist_isoformat)
    
    # Approval
    approved_by_id: Optional[str] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[str] = None
    approval_notes: Optional[str] = None
    
    # Rejection
    rejected_by_id: Optional[str] = None
    rejected_by_name: Optional[str] = None
    rejected_at: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # PO reference (when ordered)
    po_number: Optional[str] = None
    po_date: Optional[str] = None
    
    # Receiving
    received_at: Optional[str] = None
    received_by_id: Optional[str] = None
    received_by_name: Optional[str] = None
    
    # Notes and attachments
    notes: Optional[str] = None
    internal_notes: Optional[str] = None
    attachments: List[Dict[str, str]] = Field(default_factory=list)
    # e.g., [{"name": "quotation.pdf", "url": "/uploads/..."}]
    
    # Flags
    is_urgent: bool = False
    is_deleted: bool = False
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    
    # Status history
    status_history: List[Dict[str, Any]] = Field(default_factory=list)


class PurchaseRequestCreate(BaseModel):
    """Create a new purchase request"""
    vendor_id: Optional[str] = None
    items: List[Dict[str, Any]]  # List of items with item_id, quantity_requested, notes
    priority: str = "medium"
    required_by_date: Optional[str] = None
    delivery_location_id: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None
    is_urgent: bool = False


class PurchaseRequestItemInput(BaseModel):
    """Input model for adding items to PR"""
    item_id: str
    quantity_requested: int = 1
    estimated_unit_price: Optional[float] = None
    suggested_vendor_id: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None


class PurchaseRequestUpdate(BaseModel):
    """Update purchase request (only when in DRAFT status)"""
    vendor_id: Optional[str] = None
    priority: Optional[str] = None
    required_by_date: Optional[str] = None
    delivery_location_id: Optional[str] = None
    notes: Optional[str] = None
    is_urgent: Optional[bool] = None


class PurchaseRequestApproval(BaseModel):
    """Approve or reject a purchase request"""
    approved: bool
    notes: Optional[str] = None
    vendor_id: Optional[str] = None  # Can specify vendor at approval time
    items_approved: Optional[List[Dict[str, int]]] = None  # [{"item_id": ..., "quantity_approved": ...}]


class PurchaseRequestReceive(BaseModel):
    """Record receipt of items from a purchase request"""
    items_received: List[Dict[str, Any]]
    # e.g., [{"item_id": ..., "quantity_received": 5, "serial_numbers": [...]}]
    receiving_location_id: str
    notes: Optional[str] = None
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None


def generate_pr_number() -> str:
    """Generate a unique PR number"""
    from datetime import datetime
    year = datetime.now().year
    random_part = ''.join(random.choices(string.digits, k=6))
    return f"PR-{year}-{random_part}"


async def generate_unique_pr_number(db, organization_id: str) -> str:
    """Generate a collision-safe PR number"""
    for _ in range(10):
        pr_number = generate_pr_number()
        existing = await db.purchase_requests.find_one({
            "organization_id": organization_id,
            "pr_number": pr_number
        })
        if not existing:
            return pr_number
    # Fallback with timestamp
    import time
    return f"PR-{time.time():.0f}"
