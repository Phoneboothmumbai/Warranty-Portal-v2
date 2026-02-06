"""
Service Job Management - MSP-Grade Workflow
============================================
Complete implementation following the ERD and workflow spec.

Build Order (This file implements 1, 8, 9, 10, 11):
1. ProblemMaster ✓
8. ServiceTicket ✓  
9. ServiceVisit ✓
10. TicketPartRequest ✓
11. TicketPartIssue ✓

Key Design Principles:
- ServiceVisit is mandatory (no work logged directly on ticket)
- Timer is engineer-controlled (Back Office cannot edit)
- Every step is traceable
- Clean separation: Request ≠ Issue (physical movement)
"""
import uuid
import random
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from utils.helpers import get_ist_isoformat


# ==================== PROBLEM MASTER ====================

class ProblemMaster(BaseModel):
    """Predefined problem list - NO free text chaos"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str  # e.g., "System not booting"
    category: Optional[str] = None  # Optional grouping for reporting
    description: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class ProblemMasterCreate(BaseModel):
    name: str
    category: Optional[str] = None
    description: Optional[str] = None


class ProblemMasterUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== TICKET STATES ====================

class TicketState(str, Enum):
    """Service ticket lifecycle states"""
    NEW = "NEW"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    PENDING_PARTS = "PENDING_PARTS"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    COMPLETED = "COMPLETED"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"


# Valid state transitions
TICKET_STATE_TRANSITIONS = {
    TicketState.NEW: [TicketState.ASSIGNED, TicketState.CANCELLED],
    TicketState.ASSIGNED: [TicketState.IN_PROGRESS, TicketState.NEW, TicketState.CANCELLED],
    TicketState.IN_PROGRESS: [
        TicketState.PENDING_PARTS, 
        TicketState.PENDING_APPROVAL,
        TicketState.COMPLETED, 
        TicketState.CANCELLED
    ],
    TicketState.PENDING_PARTS: [TicketState.IN_PROGRESS, TicketState.CANCELLED],
    TicketState.PENDING_APPROVAL: [TicketState.IN_PROGRESS, TicketState.CANCELLED],
    TicketState.COMPLETED: [TicketState.CLOSED, TicketState.IN_PROGRESS],  # Can reopen
    TicketState.CLOSED: [],  # Terminal
    TicketState.CANCELLED: [],  # Terminal
}


STATE_METADATA = {
    TicketState.NEW: {"label": "New", "color": "slate", "is_terminal": False},
    TicketState.ASSIGNED: {"label": "Assigned", "color": "blue", "is_terminal": False},
    TicketState.IN_PROGRESS: {"label": "In Progress", "color": "amber", "is_terminal": False},
    TicketState.PENDING_PARTS: {"label": "Pending Parts", "color": "orange", "is_terminal": False},
    TicketState.PENDING_APPROVAL: {"label": "Pending Approval", "color": "purple", "is_terminal": False},
    TicketState.COMPLETED: {"label": "Completed", "color": "green", "is_terminal": False},
    TicketState.CLOSED: {"label": "Closed", "color": "emerald", "is_terminal": True},
    TicketState.CANCELLED: {"label": "Cancelled", "color": "red", "is_terminal": True},
}


# ==================== BILLING TYPES ====================

class BillingType(str, Enum):
    """How the service will be billed"""
    WARRANTY = "warranty"
    AMC = "amc"
    PAID = "paid"
    THIRD_PARTY = "third_party"


# ==================== SERVICE TICKET ====================

class ServiceTicket(BaseModel):
    """
    Main service ticket entity.
    
    Rules:
    - Work is logged via ServiceVisit, NOT directly on ticket
    - Status changes must follow TICKET_STATE_TRANSITIONS
    - All changes are audited in state_history
    """
    model_config = ConfigDict(extra="ignore")
    
    # Core identifiers
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str  # 6-char alphanumeric
    organization_id: str
    
    # Company & Contact (FK references)
    company_id: str
    company_name: str  # Snapshot for display
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Location (FK to Site or inline)
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    location_address: Optional[str] = None
    location_city: Optional[str] = None
    
    # Problem (FK to ProblemMaster)
    problem_id: str
    problem_name: str  # Snapshot
    problem_description: Optional[str] = None  # Additional details from caller
    
    # Device (optional - can be unlinked asset)
    device_id: Optional[str] = None
    device_serial: Optional[str] = None
    device_name: Optional[str] = None
    is_unlinked_asset: bool = False  # Flag for devices without serial
    
    # Status & Priority
    status: str = TicketState.NEW.value
    priority: str = "medium"  # low, medium, high, urgent
    
    # Assignment
    assigned_technician_id: Optional[str] = None
    assigned_technician_name: Optional[str] = None
    assigned_at: Optional[str] = None
    assigned_by_id: Optional[str] = None
    assigned_by_name: Optional[str] = None
    
    # Billing
    billing_type: str = BillingType.PAID.value
    
    # Timestamps
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: str = ""
    created_by_name: str = ""
    updated_at: str = Field(default_factory=get_ist_isoformat)
    
    # Resolution
    resolution_notes: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by_id: Optional[str] = None
    resolved_by_name: Optional[str] = None
    
    # Closure
    closed_at: Optional[str] = None
    closed_by_id: Optional[str] = None
    closed_by_name: Optional[str] = None
    
    # Cancellation
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancelled_by_id: Optional[str] = None
    cancelled_by_name: Optional[str] = None
    
    # Audit trail
    state_history: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Soft delete
    is_deleted: bool = False
    
    def get_valid_transitions(self) -> List[str]:
        """Get list of valid next states from current state"""
        current = TicketState(self.status)
        return [s.value for s in TICKET_STATE_TRANSITIONS.get(current, [])]
    
    def can_transition_to(self, target_state: str) -> bool:
        """Check if transition to target state is valid"""
        return target_state in self.get_valid_transitions()
    
    def is_terminal(self) -> bool:
        """Check if current state is terminal"""
        return self.status in [TicketState.CLOSED.value, TicketState.CANCELLED.value]


class ServiceTicketCreate(BaseModel):
    """Create a new service ticket"""
    # Company & Contact
    company_id: str
    contact_id: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Location
    site_id: Optional[str] = None
    location_address: Optional[str] = None
    location_city: Optional[str] = None
    
    # Problem
    problem_id: str
    problem_description: Optional[str] = None
    
    # Device
    device_id: Optional[str] = None
    device_serial: Optional[str] = None
    device_name: Optional[str] = None
    
    # Priority & Billing
    priority: str = "medium"
    billing_type: str = BillingType.PAID.value
    
    # Optional initial assignment
    assigned_technician_id: Optional[str] = None


class ServiceTicketUpdate(BaseModel):
    """Update service ticket (non-status fields)"""
    priority: Optional[str] = None
    problem_description: Optional[str] = None
    billing_type: Optional[str] = None
    site_id: Optional[str] = None
    location_address: Optional[str] = None
    location_city: Optional[str] = None


# ==================== SERVICE VISIT ====================

class VisitStatus(str, Enum):
    """Visit lifecycle"""
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ServiceVisit(BaseModel):
    """
    Service visit record - supports multi-visit scenarios.
    
    Rules:
    - Timer is engineer-controlled
    - Back Office CANNOT modify engineer timers
    - Each visit has its own timer
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    organization_id: str
    visit_number: int = 1
    
    # Technician
    technician_id: str
    technician_name: str
    
    # Timer (engineer-controlled)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_minutes: Optional[int] = None
    
    # Visit details
    visit_notes: Optional[str] = None
    work_performed: Optional[str] = None
    observations: Optional[str] = None
    actions_taken: List[str] = Field(default_factory=list)
    
    # Status
    status: str = VisitStatus.SCHEDULED.value
    
    # Timestamps
    scheduled_at: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    
    is_deleted: bool = False
    
    def start_timer(self) -> None:
        """Start the visit timer"""
        if self.status != VisitStatus.IN_PROGRESS.value:
            self.status = VisitStatus.IN_PROGRESS.value
        self.start_time = get_ist_isoformat()
        self.updated_at = get_ist_isoformat()
    
    def stop_timer(self) -> None:
        """Stop the visit timer and calculate duration"""
        if self.start_time:
            self.end_time = get_ist_isoformat()
            # Calculate duration
            from datetime import datetime
            start = datetime.fromisoformat(self.start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(self.end_time.replace('Z', '+00:00'))
            self.total_minutes = int((end - start).total_seconds() / 60)
        self.status = VisitStatus.COMPLETED.value
        self.updated_at = get_ist_isoformat()


class ServiceVisitCreate(BaseModel):
    """Create a new visit"""
    ticket_id: str
    technician_id: str
    scheduled_at: Optional[str] = None
    visit_notes: Optional[str] = None


class ServiceVisitUpdate(BaseModel):
    """Update visit details"""
    visit_notes: Optional[str] = None
    work_performed: Optional[str] = None
    observations: Optional[str] = None
    actions_taken: Optional[List[str]] = None


# ==================== PART REQUEST STATUS ====================

class PartRequestStatus(str, Enum):
    """Part request lifecycle"""
    REQUESTED = "requested"
    APPROVED = "approved"
    ISSUED = "issued"
    CANCELLED = "cancelled"


# ==================== TICKET PART REQUEST ====================

class TicketPartRequest(BaseModel):
    """
    Part request raised by engineer.
    
    Rules:
    - Request ≠ physical movement
    - Must go through approval for paid jobs
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    visit_id: str
    organization_id: str
    
    # Item requested
    item_id: str
    item_name: str  # Snapshot
    quantity: int = 1
    
    # Billing context
    request_type: str = BillingType.PAID.value  # warranty, amc, paid, third_party
    
    # Status
    status: str = PartRequestStatus.REQUESTED.value
    
    # Approval workflow
    estimated_cost: Optional[float] = None
    approved_at: Optional[str] = None
    approved_by_id: Optional[str] = None
    approved_by_name: Optional[str] = None
    
    # Timestamps
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: str = ""  # Technician who raised
    created_by_name: str = ""
    
    is_deleted: bool = False


class TicketPartRequestCreate(BaseModel):
    """Create a part request"""
    ticket_id: str
    visit_id: str
    item_id: str
    quantity: int = 1
    request_type: str = BillingType.PAID.value
    estimated_cost: Optional[float] = None


# ==================== TICKET PART ISSUE ====================

class TicketPartIssue(BaseModel):
    """
    Actual physical issue of parts.
    
    Rules:
    - This represents real inventory movement
    - Links to StockLedger for audit
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    organization_id: str
    
    # What was issued
    item_id: str
    item_name: str  # Snapshot
    quantity: int = 1
    
    # Where it came from and went to
    issued_from_location_id: str
    issued_from_location_name: str  # Snapshot
    issued_to_technician_id: str
    issued_to_technician_name: str  # Snapshot
    
    # Link to request (optional - can issue without prior request)
    part_request_id: Optional[str] = None
    
    # Cost at time of issue
    unit_cost: Optional[float] = None
    total_cost: Optional[float] = None
    
    # Timestamps
    issued_at: str = Field(default_factory=get_ist_isoformat)
    issued_by_id: str = ""
    issued_by_name: str = ""
    
    is_deleted: bool = False


class TicketPartIssueCreate(BaseModel):
    """Create a part issue"""
    ticket_id: str
    item_id: str
    quantity: int = 1
    issued_from_location_id: str
    issued_to_technician_id: str
    part_request_id: Optional[str] = None


# ==================== QUOTATION ====================

class QuotationStatus(str, Enum):
    """Quotation lifecycle"""
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class TicketQuotation(BaseModel):
    """
    Quotation for paid services.
    Sent to customer for approval.
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    organization_id: str
    
    # Items
    items: List[Dict[str, Any]] = Field(default_factory=list)
    # Each item: {description, quantity, unit_price, total}
    
    # Costs
    parts_cost: float = 0
    labour_cost: float = 0
    other_cost: float = 0
    tax_amount: float = 0
    total_amount: float = 0
    
    # Status
    status: str = QuotationStatus.DRAFT.value
    
    # Customer response
    sent_at: Optional[str] = None
    responded_at: Optional[str] = None
    response_notes: Optional[str] = None
    
    # Timestamps
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: str = ""
    created_by_name: str = ""
    valid_until: Optional[str] = None
    
    is_deleted: bool = False


# ==================== TICKET NUMBER GENERATOR ====================

def generate_ticket_number() -> str:
    """
    Generate a 6-character uppercase alphanumeric ticket number.
    Excludes confusing characters (O, 0, I, 1, L)
    """
    allowed_chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(random.choices(allowed_chars, k=6))


async def generate_unique_ticket_number(db, organization_id: str, max_retries: int = 10) -> str:
    """Generate a collision-safe ticket number unique within the tenant."""
    for _ in range(max_retries):
        ticket_number = generate_ticket_number()
        existing = await db.service_tickets.find_one({
            "organization_id": organization_id,
            "ticket_number": ticket_number
        })
        if not existing:
            return ticket_number
    
    # Fallback with timestamp
    import time
    return f"{generate_ticket_number()[:4]}{int(time.time()) % 100:02d}"
