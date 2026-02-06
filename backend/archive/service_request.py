"""
Service/Repair Management - FSM Models
=======================================
Complete FSM-driven service request management system.

Key Features:
- 13-state FSM with strict transition validation
- 6-character alphanumeric ticket numbers
- Immutable state history for audit
- Customer/location snapshots for historical accuracy
- First-class visit tracking
- Approval workflow with immutable responses

This module REPLACES the old job system entirely.
"""
import uuid
import random
import string
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from utils.helpers import get_ist_isoformat


# ==================== FSM STATES ====================

class ServiceState(str, Enum):
    """All 13 FSM states - implemented from Day 1"""
    CREATED = "CREATED"
    ASSIGNED = "ASSIGNED"
    DECLINED = "DECLINED"
    ACCEPTED = "ACCEPTED"
    VISIT_IN_PROGRESS = "VISIT_IN_PROGRESS"
    VISIT_COMPLETED = "VISIT_COMPLETED"
    PENDING_PART = "PENDING_PART"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    REPAIR_IN_PROGRESS = "REPAIR_IN_PROGRESS"
    QC_PENDING = "QC_PENDING"
    READY_FOR_RETURN = "READY_FOR_RETURN"
    RESOLVED = "RESOLVED"
    CANCELLED = "CANCELLED"


# FSM Transition Rules - The Law
# Format: {current_state: [allowed_next_states]}
FSM_TRANSITIONS = {
    ServiceState.CREATED: [ServiceState.ASSIGNED, ServiceState.CANCELLED],
    ServiceState.ASSIGNED: [ServiceState.ACCEPTED, ServiceState.DECLINED, ServiceState.CANCELLED],
    ServiceState.DECLINED: [ServiceState.ASSIGNED, ServiceState.CANCELLED],  # Can reassign
    ServiceState.ACCEPTED: [ServiceState.VISIT_IN_PROGRESS, ServiceState.CANCELLED],
    ServiceState.VISIT_IN_PROGRESS: [ServiceState.VISIT_COMPLETED, ServiceState.CANCELLED],
    ServiceState.VISIT_COMPLETED: [
        ServiceState.PENDING_PART,
        ServiceState.PENDING_APPROVAL,
        ServiceState.REPAIR_IN_PROGRESS,
        ServiceState.RESOLVED,  # Quick fix, no repair needed
        ServiceState.CANCELLED
    ],
    ServiceState.PENDING_PART: [ServiceState.REPAIR_IN_PROGRESS, ServiceState.CANCELLED],
    ServiceState.PENDING_APPROVAL: [ServiceState.REPAIR_IN_PROGRESS, ServiceState.CANCELLED],
    ServiceState.REPAIR_IN_PROGRESS: [ServiceState.QC_PENDING, ServiceState.CANCELLED],
    ServiceState.QC_PENDING: [ServiceState.READY_FOR_RETURN, ServiceState.REPAIR_IN_PROGRESS, ServiceState.CANCELLED],
    ServiceState.READY_FOR_RETURN: [ServiceState.RESOLVED, ServiceState.CANCELLED],
    ServiceState.RESOLVED: [],  # Terminal state
    ServiceState.CANCELLED: []  # Terminal state
}


# State metadata for UI and business logic
STATE_METADATA = {
    ServiceState.CREATED: {
        "label": "Created",
        "description": "Request created, awaiting assignment",
        "color": "slate",
        "is_terminal": False,
        "requires_data": []
    },
    ServiceState.ASSIGNED: {
        "label": "Assigned",
        "description": "Technician assigned, awaiting response",
        "color": "blue",
        "is_terminal": False,
        "requires_data": ["assigned_staff_id"]
    },
    ServiceState.DECLINED: {
        "label": "Declined",
        "description": "Assignment declined by technician",
        "color": "red",
        "is_terminal": False,
        "requires_data": ["decline_reason"]
    },
    ServiceState.ACCEPTED: {
        "label": "Accepted",
        "description": "Technician accepted, ready for visit",
        "color": "emerald",
        "is_terminal": False,
        "requires_data": []
    },
    ServiceState.VISIT_IN_PROGRESS: {
        "label": "Visit In Progress",
        "description": "Technician on-site",
        "color": "amber",
        "is_terminal": False,
        "requires_data": []  # visit_start_time is auto-populated
    },
    ServiceState.VISIT_COMPLETED: {
        "label": "Visit Completed",
        "description": "On-site visit completed, diagnostics done",
        "color": "teal",
        "is_terminal": False,
        "requires_data": ["diagnostics"]
    },
    ServiceState.PENDING_PART: {
        "label": "Pending Part",
        "description": "Waiting for parts",
        "color": "orange",
        "is_terminal": False,
        "requires_data": ["parts_required"]
    },
    ServiceState.PENDING_APPROVAL: {
        "label": "Pending Approval",
        "description": "Waiting for customer approval",
        "color": "purple",
        "is_terminal": False,
        "requires_data": ["approval.amount"]
    },
    ServiceState.REPAIR_IN_PROGRESS: {
        "label": "Repair In Progress",
        "description": "Repair work underway",
        "color": "indigo",
        "is_terminal": False,
        "requires_data": []
    },
    ServiceState.QC_PENDING: {
        "label": "QC Pending",
        "description": "Quality check required",
        "color": "cyan",
        "is_terminal": False,
        "requires_data": []
    },
    ServiceState.READY_FOR_RETURN: {
        "label": "Ready for Return",
        "description": "Device ready for customer pickup/delivery",
        "color": "green",
        "is_terminal": False,
        "requires_data": []
    },
    ServiceState.RESOLVED: {
        "label": "Resolved",
        "description": "Service request completed successfully",
        "color": "emerald",
        "is_terminal": True,
        "requires_data": ["resolution_notes"]
    },
    ServiceState.CANCELLED: {
        "label": "Cancelled",
        "description": "Service request cancelled",
        "color": "slate",
        "is_terminal": True,
        "requires_data": ["cancellation_reason"]
    }
}


# ==================== SUPPORTING MODELS ====================

class CustomerSnapshot(BaseModel):
    """Immutable snapshot of customer at ticket creation time"""
    name: str
    mobile: Optional[str] = None
    email: Optional[str] = None
    company_name: Optional[str] = None


class LocationSnapshot(BaseModel):
    """Immutable snapshot of service location"""
    address: str
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None


class StateTransition(BaseModel):
    """Immutable record of a state transition - NEVER modify after creation"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    from_state: str
    to_state: str
    actor_id: str
    actor_name: str
    actor_role: str  # e.g., "admin", "technician", "system"
    timestamp: str = Field(default_factory=get_ist_isoformat)
    reason: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VisitCostSnapshot(BaseModel):
    """Auto-calculated cost snapshot at visit completion"""
    labour_cost: float = 0
    travel_cost: float = 0
    parts_cost: float = 0
    total: float = 0
    calculated_at: str = Field(default_factory=get_ist_isoformat)


class ServiceVisit(BaseModel):
    """First-class visit record - supports multi-visit scenarios"""
    visit_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    visit_number: int = 1
    technician_id: str
    technician_name: str
    
    # Timing
    scheduled_at: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    
    # Visit details
    diagnostics: Optional[str] = None
    actions_taken: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    
    # Cost tracking
    auto_cost_snapshot: Optional[VisitCostSnapshot] = None
    
    # Status
    status: str = "scheduled"  # scheduled, in_progress, completed, cancelled
    created_at: str = Field(default_factory=get_ist_isoformat)


class PartRequired(BaseModel):
    """Part requirement tracking"""
    part_id: Optional[str] = None
    part_name: str
    quantity: int = 1
    estimated_cost: float = 0
    status: str = "requested"  # requested, ordered, received, used
    notes: Optional[str] = None
    requested_at: str = Field(default_factory=get_ist_isoformat)
    received_at: Optional[str] = None


class ApprovalRequest(BaseModel):
    """Immutable approval workflow - cannot be modified after response"""
    required: bool = False
    status: str = "NOT_REQUIRED"  # NOT_REQUIRED, PENDING, APPROVED, REJECTED
    amount: float = 0
    description: Optional[str] = None
    requested_at: Optional[str] = None
    requested_by_id: Optional[str] = None
    requested_by_name: Optional[str] = None
    responded_at: Optional[str] = None
    responded_by_id: Optional[str] = None
    responded_by_name: Optional[str] = None
    response_notes: Optional[str] = None
    response_snapshot: Dict[str, Any] = Field(default_factory=dict)


# ==================== MAIN SERVICE REQUEST MODEL ====================

class ServiceRequest(BaseModel):
    """
    FSM-driven Service Request - The core entity
    
    This is the SINGLE SOURCE OF TRUTH for all service/repair management.
    The FSM state drives all business logic.
    """
    model_config = ConfigDict(extra="ignore")
    
    # Core identifiers
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str  # 6-char alphanumeric, immutable after creation
    organization_id: str  # Tenant isolation
    
    # FSM State (THE LAW)
    state: str = ServiceState.CREATED.value
    state_history: List[StateTransition] = Field(default_factory=list)
    
    # Customer & Location (snapshots for historical accuracy)
    customer_id: Optional[str] = None
    customer_snapshot: Optional[CustomerSnapshot] = None
    location_id: Optional[str] = None
    location_snapshot: Optional[LocationSnapshot] = None
    
    # Device/Asset
    device_id: Optional[str] = None
    device_serial: Optional[str] = None
    device_name: Optional[str] = None
    device_type: Optional[str] = None
    
    # Request details
    title: str
    description: Optional[str] = None
    category: Optional[str] = None  # e.g., "repair", "maintenance", "installation"
    priority: str = "medium"  # low, medium, high, urgent
    source: str = "manual"  # manual, email, portal, api
    
    # Assignment
    assigned_staff_id: Optional[str] = None
    assigned_staff_name: Optional[str] = None
    assigned_at: Optional[str] = None
    decline_reason: Optional[str] = None
    
    # Visits (first-class citizens)
    visits: List[ServiceVisit] = Field(default_factory=list)
    current_visit_id: Optional[str] = None
    
    # Parts & Inventory
    parts_required: List[PartRequired] = Field(default_factory=list)
    
    # Approval workflow (immutable once responded)
    approval: ApprovalRequest = Field(default_factory=ApprovalRequest)
    
    # Costing
    estimated_cost: float = 0
    actual_cost: float = 0
    labour_cost: float = 0
    parts_cost: float = 0
    travel_cost: float = 0
    
    # Resolution
    resolution_notes: Optional[str] = None
    resolved_at: Optional[str] = None
    resolved_by_id: Optional[str] = None
    resolved_by_name: Optional[str] = None
    
    # Cancellation
    cancellation_reason: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancelled_by_id: Optional[str] = None
    cancelled_by_name: Optional[str] = None
    
    # SLA tracking
    sla_due_at: Optional[str] = None
    sla_breached: bool = False
    sla_breached_at: Optional[str] = None
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: str = ""
    created_by_name: str = ""
    updated_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False
    
    def get_valid_transitions(self) -> List[str]:
        """Get list of valid next states from current state"""
        current = ServiceState(self.state)
        return [s.value for s in FSM_TRANSITIONS.get(current, [])]
    
    def can_transition_to(self, target_state: str) -> bool:
        """Check if transition to target state is valid"""
        return target_state in self.get_valid_transitions()
    
    def is_terminal(self) -> bool:
        """Check if current state is terminal (no further transitions)"""
        return self.state in [ServiceState.RESOLVED.value, ServiceState.CANCELLED.value]


# ==================== REQUEST/RESPONSE MODELS ====================

class ServiceRequestCreate(BaseModel):
    """Create a new service request"""
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    priority: str = "medium"
    
    # Customer (optional - can be linked later)
    customer_id: Optional[str] = None
    customer_name: Optional[str] = None
    customer_mobile: Optional[str] = None
    customer_email: Optional[str] = None
    customer_company_name: Optional[str] = None
    
    # Location
    location_address: Optional[str] = None
    location_city: Optional[str] = None
    location_pincode: Optional[str] = None
    
    # Device
    device_id: Optional[str] = None
    device_serial: Optional[str] = None
    device_name: Optional[str] = None
    
    # Optional initial assignment
    assigned_staff_id: Optional[str] = None
    
    # Tags & custom
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


class ServiceRequestUpdate(BaseModel):
    """Update service request (non-FSM fields only)"""
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None
    estimated_cost: Optional[float] = None


class StateTransitionRequest(BaseModel):
    """Request to transition FSM state - THE ONLY WAY to change state"""
    target_state: str
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    # State-specific data
    assigned_staff_id: Optional[str] = None  # For ASSIGNED
    decline_reason: Optional[str] = None  # For DECLINED
    diagnostics: Optional[str] = None  # For VISIT_COMPLETED
    parts_required: Optional[List[Dict]] = None  # For PENDING_PART
    approval_amount: Optional[float] = None  # For PENDING_APPROVAL
    resolution_notes: Optional[str] = None  # For RESOLVED
    cancellation_reason: Optional[str] = None  # For CANCELLED


class AddVisitRequest(BaseModel):
    """Add a new visit to service request"""
    technician_id: str
    scheduled_at: Optional[str] = None
    notes: Optional[str] = None


class UpdateVisitRequest(BaseModel):
    """Update visit details"""
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    diagnostics: Optional[str] = None
    actions_taken: Optional[List[str]] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class ApprovalResponseRequest(BaseModel):
    """Respond to approval request"""
    approved: bool
    notes: Optional[str] = None


# ==================== TICKET NUMBER GENERATOR ====================

def generate_ticket_number() -> str:
    """
    Generate a 6-character uppercase alphanumeric ticket number.
    
    Format: A9F2KQ
    - Uses uppercase letters and digits
    - Excludes confusing characters (O, 0, I, 1, L)
    - ~1.5 billion possible combinations
    """
    # Exclude confusing characters
    allowed_chars = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
    return ''.join(random.choices(allowed_chars, k=6))


async def generate_unique_ticket_number(db, organization_id: str, max_retries: int = 10) -> str:
    """
    Generate a collision-safe ticket number unique within the tenant.
    
    Uses retry logic to handle the (very unlikely) collision case.
    """
    for _ in range(max_retries):
        ticket_number = generate_ticket_number()
        
        # Check for collision within tenant
        existing = await db.service_requests.find_one({
            "organization_id": organization_id,
            "ticket_number": ticket_number
        })
        
        if not existing:
            return ticket_number
    
    # Fallback: add timestamp suffix (should never happen)
    import time
    return f"{generate_ticket_number()[:4]}{int(time.time()) % 100:02d}"
