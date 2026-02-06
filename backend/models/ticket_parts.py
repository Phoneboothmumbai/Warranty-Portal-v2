"""
Ticket Parts Models
===================
Parts request and issue tracking for service tickets.

TicketPartRequest: Technician requests parts for a ticket
TicketPartIssue: Parts actually issued from inventory to a ticket
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from utils.helpers import get_ist_isoformat


# ==================== PART REQUEST ====================

class PartRequestStatus(str, Enum):
    """Status of a parts request"""
    REQUESTED = "requested"     # Technician requested
    APPROVED = "approved"       # Request approved
    REJECTED = "rejected"       # Request rejected
    ORDERED = "ordered"         # Part ordered (PR created)
    AVAILABLE = "available"     # Part available for pickup
    ISSUED = "issued"           # Part issued to technician
    RETURNED = "returned"       # Part returned (unused)
    CANCELLED = "cancelled"     # Request cancelled


class TicketPartRequest(BaseModel):
    """
    Parts Request - Request for parts from a service ticket.
    
    Flow:
    Technician requests → Admin approves → PR created (if not in stock) → Part issued
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # Ticket reference
    ticket_id: str
    ticket_number: str
    visit_id: Optional[str] = None  # Specific visit (optional)
    
    # Item requested
    item_id: str  # Reference to ItemMaster
    item_name: str
    item_sku: Optional[str] = None
    
    # Quantity
    quantity_requested: int = 1
    quantity_approved: int = 0
    quantity_issued: int = 0
    quantity_returned: int = 0
    
    # Status
    status: str = PartRequestStatus.REQUESTED.value
    
    # Requester (technician)
    requested_by_id: str
    requested_by_name: str
    requested_at: str = Field(default_factory=get_ist_isoformat)
    request_notes: Optional[str] = None
    urgency: str = "normal"  # normal, urgent
    
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
    
    # Purchase Request reference (if part was ordered)
    purchase_request_id: Optional[str] = None
    purchase_request_number: Optional[str] = None
    
    # Issue reference
    issue_ids: List[str] = Field(default_factory=list)  # References to TicketPartIssue
    
    # Estimated cost
    estimated_unit_cost: float = 0
    estimated_total_cost: float = 0
    
    # Flags
    is_deleted: bool = False
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class TicketPartRequestCreate(BaseModel):
    """Create a new parts request"""
    ticket_id: str
    visit_id: Optional[str] = None
    item_id: str
    quantity_requested: int = 1
    request_notes: Optional[str] = None
    urgency: str = "normal"


class TicketPartRequestApproval(BaseModel):
    """Approve or reject a parts request"""
    approved: bool
    quantity_approved: Optional[int] = None  # If approving less than requested
    notes: Optional[str] = None


# ==================== PART ISSUE ====================

class TicketPartIssue(BaseModel):
    """
    Parts Issue - Actual issuance of parts from inventory to a ticket.
    
    This creates a StockLedger entry when parts are issued.
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # Ticket reference
    ticket_id: str
    ticket_number: str
    visit_id: Optional[str] = None  # Specific visit
    
    # Part request reference (if issued against a request)
    part_request_id: Optional[str] = None
    
    # Item issued
    item_id: str
    item_name: str
    item_sku: Optional[str] = None
    
    # Quantity
    quantity_issued: int = 1
    quantity_returned: int = 0  # If part was returned
    quantity_used: int = 0  # Calculated: issued - returned
    
    # Serial numbers (for serialized items)
    serial_numbers: List[str] = Field(default_factory=list)
    
    # Source location
    issued_from_location_id: str
    issued_from_location_name: str
    
    # Stock ledger reference
    ledger_entry_id: Optional[str] = None  # Reference to StockLedger entry
    return_ledger_entry_id: Optional[str] = None  # If returned
    
    # Costing
    unit_cost: float = 0
    total_cost: float = 0  # unit_cost * quantity_used
    
    # Billing
    unit_price: float = 0  # Selling price to customer
    total_price: float = 0
    is_billable: bool = True
    is_billed: bool = False
    
    # Issued by
    issued_by_id: str
    issued_by_name: str
    issued_at: str = Field(default_factory=get_ist_isoformat)
    
    # Received by (technician)
    received_by_id: Optional[str] = None
    received_by_name: Optional[str] = None
    
    # Return (if any)
    returned_at: Optional[str] = None
    returned_by_id: Optional[str] = None
    returned_by_name: Optional[str] = None
    return_reason: Optional[str] = None
    return_location_id: Optional[str] = None
    
    # Notes
    notes: Optional[str] = None
    
    # Flags
    is_warranty_claim: bool = False  # Part under warranty
    is_deleted: bool = False
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class TicketPartIssueCreate(BaseModel):
    """Issue parts to a ticket"""
    ticket_id: str
    visit_id: Optional[str] = None
    part_request_id: Optional[str] = None
    item_id: str
    quantity_issued: int = 1
    serial_numbers: Optional[List[str]] = None
    issued_from_location_id: str
    received_by_id: Optional[str] = None
    unit_cost: Optional[float] = None
    unit_price: Optional[float] = None
    is_billable: bool = True
    is_warranty_claim: bool = False
    notes: Optional[str] = None


class TicketPartReturnCreate(BaseModel):
    """Return issued parts"""
    quantity_returned: int = 1
    serial_numbers: Optional[List[str]] = None
    return_location_id: str
    return_reason: Optional[str] = None
