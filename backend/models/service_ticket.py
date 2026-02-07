"""
Service Ticket Models (NEW)
===========================
Complete rebuild of service ticket management for MSP-grade workflow.

Key Features:
- Simplified but complete ticket lifecycle
- Multi-visit support with time tracking
- Parts request/issue workflow
- Integration with inventory system

Ticket Lifecycle:
NEW → ASSIGNED → IN_PROGRESS → (PENDING_PARTS) → COMPLETED → CLOSED
                     ↓
                 CANCELLED

Visits:
- Multiple visits per ticket
- Time tracking (start/end timer)
- Actions and diagnostics per visit
"""
import uuid
import random
import string
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from utils.helpers import get_ist_isoformat


# ==================== TICKET STATES ====================

class TicketStatus(str, Enum):
    """Ticket status (simplified from old 13-state FSM)"""
    NEW = "new"                    # Ticket created, awaiting assignment
    PENDING_ACCEPTANCE = "pending_acceptance"  # Assigned, awaiting engineer acceptance
    ASSIGNED = "assigned"          # Assigned to technician (accepted)
    IN_PROGRESS = "in_progress"    # Work has begun
    PENDING_PARTS = "pending_parts"  # Waiting for parts
    COMPLETED = "completed"        # Work done, awaiting closure
    CLOSED = "closed"              # Ticket closed
    CANCELLED = "cancelled"        # Ticket cancelled


class AssignmentStatus(str, Enum):
    """Status of ticket assignment to engineer"""
    PENDING = "pending"            # Awaiting engineer's response
    ACCEPTED = "accepted"          # Engineer accepted the assignment
    DECLINED = "declined"          # Engineer declined the assignment


class TicketPriority(str, Enum):
    """Ticket priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketSource(str, Enum):
    """How the ticket was created"""
    MANUAL = "manual"          # Created by admin
    PORTAL = "portal"          # Created via company portal
    EMAIL = "email"            # Created from email
    QR_SCAN = "qr_scan"        # Created from QR code scan
    API = "api"                # Created via API
    SCHEDULED = "scheduled"    # Auto-created from schedule


# ==================== SUPPORTING MODELS ====================

class TicketContact(BaseModel):
    """Contact person for the ticket"""
    name: str
    phone: Optional[str] = None
    email: Optional[str] = None
    designation: Optional[str] = None


class TicketLocation(BaseModel):
    """Service location details"""
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None


class StatusChange(BaseModel):
    """Record of status change (audit)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_status: Optional[str] = None
    to_status: str
    changed_by_id: str
    changed_by_name: str
    changed_at: str = Field(default_factory=get_ist_isoformat)
    reason: Optional[str] = None
    notes: Optional[str] = None


# ==================== MAIN SERVICE TICKET ====================

class ServiceTicketNew(BaseModel):
    """
    Service Ticket - Core entity for service management.
    
    This is the NEW simplified model that replaces the old FSM-based system.
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # Ticket identification
    ticket_number: str  # 6-char alphanumeric, immutable
    
    # Status
    status: str = TicketStatus.NEW.value
    priority: str = TicketPriority.MEDIUM.value
    
    # Customer/Company
    company_id: str
    company_name: str  # Denormalized
    contact: Optional[TicketContact] = None
    
    # Location
    location: Optional[TicketLocation] = None
    
    # Device (optional - ticket may not be device-specific)
    device_id: Optional[str] = None
    device_serial: Optional[str] = None
    device_name: Optional[str] = None  # e.g., "HP LaserJet Pro M428fdn"
    device_type: Optional[str] = None
    asset_tag: Optional[str] = None
    
    # Problem/Issue
    problem_id: Optional[str] = None  # Reference to ProblemMaster
    problem_name: Optional[str] = None
    title: str  # Brief title
    description: Optional[str] = None  # Detailed description
    
    # Assignment
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    assigned_at: Optional[str] = None
    assigned_by_id: Optional[str] = None
    assigned_by_name: Optional[str] = None
    
    # SLA
    sla_response_due: Optional[str] = None  # First response due
    sla_resolution_due: Optional[str] = None  # Resolution due
    sla_response_met: Optional[bool] = None
    sla_resolution_met: Optional[bool] = None
    first_response_at: Optional[str] = None
    
    # Resolution
    resolution_summary: Optional[str] = None
    resolution_type: Optional[str] = None  # fixed, replaced, not_reproducible, etc.
    resolved_at: Optional[str] = None
    resolved_by_id: Optional[str] = None
    resolved_by_name: Optional[str] = None
    
    # Closure
    closed_at: Optional[str] = None
    closed_by_id: Optional[str] = None
    closed_by_name: Optional[str] = None
    closure_notes: Optional[str] = None
    
    # Cancellation
    cancelled_at: Optional[str] = None
    cancelled_by_id: Optional[str] = None
    cancelled_by_name: Optional[str] = None
    cancellation_reason: Optional[str] = None
    
    # Time tracking (total across all visits)
    total_time_minutes: int = 0
    
    # Costing
    labour_cost: float = 0
    parts_cost: float = 0
    travel_cost: float = 0
    other_cost: float = 0
    total_cost: float = 0
    
    # Billing
    is_billable: bool = True
    is_billed: bool = False
    invoice_id: Optional[str] = None
    
    # Quotation (for pending_parts workflow)
    quotation_id: Optional[str] = None
    quotation_status: Optional[str] = None  # draft, sent, approved, rejected
    quotation_sent_at: Optional[str] = None
    quotation_approved_at: Optional[str] = None
    quotation_approved_by: Optional[str] = None
    
    # Customer feedback
    customer_rating: Optional[int] = None  # 1-5
    customer_feedback: Optional[str] = None
    
    # Source
    source: str = TicketSource.MANUAL.value
    source_reference: Optional[str] = None  # Email ID, QR code, etc.
    
    # Tags and custom fields
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # Status history (audit trail)
    status_history: List[StatusChange] = Field(default_factory=list)
    
    # Comments/Notes (internal communication)
    comments: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Attachments
    attachments: List[Dict[str, str]] = Field(default_factory=list)
    
    # Flags
    is_urgent: bool = False
    requires_parts: bool = False
    requires_followup: bool = False
    is_deleted: bool = False
    
    # Resolution (required for closure)
    resolution_notes: Optional[str] = None
    resolution_type: Optional[str] = None  # on_site_fix, parts_replaced, referred, no_issue_found
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: str = ""
    created_by_name: str = ""
    updated_at: str = Field(default_factory=get_ist_isoformat)


# ==================== QUOTATION MODEL ====================

class QuotationStatus(str, Enum):
    """Quotation status"""
    DRAFT = "draft"
    SENT = "sent"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"


class QuotationItem(BaseModel):
    """Single item in a quotation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_type: str = "part"  # part, labour, other
    description: str
    quantity: int = 1
    unit_price: float = 0
    total_price: float = 0
    part_id: Optional[str] = None  # Reference to parts inventory
    part_number: Optional[str] = None


class Quotation(BaseModel):
    """Quotation for service ticket"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    ticket_id: str
    ticket_number: str
    quotation_number: str  # Auto-generated
    
    # Customer details
    company_id: str
    company_name: str
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # Status
    status: str = QuotationStatus.DRAFT.value
    
    # Items
    items: List[QuotationItem] = Field(default_factory=list)
    
    # Totals
    subtotal: float = 0
    tax_rate: float = 18.0  # GST percentage
    tax_amount: float = 0
    total_amount: float = 0
    
    # Validity
    valid_until: Optional[str] = None
    
    # Notes
    terms_and_conditions: Optional[str] = None
    internal_notes: Optional[str] = None
    customer_notes: Optional[str] = None
    
    # Approval
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    # Flags
    is_deleted: bool = False
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: str = ""
    created_by_name: str = ""
    updated_at: str = Field(default_factory=get_ist_isoformat)
    sent_at: Optional[str] = None


class ServiceTicketCreate(BaseModel):
    """Create a new service ticket"""
    company_id: str
    title: str
    description: Optional[str] = None
    priority: str = TicketPriority.MEDIUM.value
    
    # Contact
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Location
    site_id: Optional[str] = None
    location_address: Optional[str] = None
    location_city: Optional[str] = None
    
    # Device
    device_id: Optional[str] = None
    device_serial: Optional[str] = None
    
    # Problem
    problem_id: Optional[str] = None
    
    # Assignment (optional at creation)
    assigned_to_id: Optional[str] = None
    
    # Source
    source: str = TicketSource.MANUAL.value
    source_reference: Optional[str] = None
    
    # Flags
    is_urgent: bool = False
    
    # Tags
    tags: Optional[List[str]] = None


class ServiceTicketUpdate(BaseModel):
    """Update service ticket"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    
    # Contact
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    
    # Location
    site_id: Optional[str] = None
    location_address: Optional[str] = None
    
    # Device
    device_id: Optional[str] = None
    
    # Problem
    problem_id: Optional[str] = None
    
    # Costing
    labour_cost: Optional[float] = None
    travel_cost: Optional[float] = None
    other_cost: Optional[float] = None
    
    # Flags
    is_urgent: Optional[bool] = None
    is_billable: Optional[bool] = None
    requires_followup: Optional[bool] = None
    
    # Tags
    tags: Optional[List[str]] = None


class TicketAssignRequest(BaseModel):
    """Request to assign ticket to technician"""
    technician_id: str
    notes: Optional[str] = None


class TicketResolveRequest(BaseModel):
    """Request to mark ticket as completed"""
    resolution_summary: str
    resolution_type: str = "fixed"  # fixed, replaced, workaround, not_reproducible, duplicate
    notes: Optional[str] = None


class TicketCloseRequest(BaseModel):
    """Request to close ticket"""
    closure_notes: Optional[str] = None


class TicketCancelRequest(BaseModel):
    """Request to cancel ticket"""
    cancellation_reason: str


class TicketCommentCreate(BaseModel):
    """Add comment to ticket"""
    text: str
    is_internal: bool = True  # Internal note or visible to customer


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
        
        existing = await db.service_tickets_new.find_one({
            "organization_id": organization_id,
            "ticket_number": ticket_number
        })
        
        if not existing:
            return ticket_number
    
    # Fallback: add timestamp suffix
    import time
    return f"{generate_ticket_number()[:4]}{int(time.time()) % 100:02d}"
