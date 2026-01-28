"""
Service related models (Tickets, History, etc.)
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from utils.helpers import get_ist_isoformat


# ==================== ENUMS FOR SERVICE RECORDS ====================

SERVICE_CATEGORIES = [
    "internal_service",           # Provided by Us
    "oem_warranty_service",       # OEM Warranty Service (Facilitated)
    "paid_third_party_service",   # Paid Third-Party Service
    "inspection_diagnosis"        # Inspection / Diagnosis Only
]

SERVICE_RESPONSIBILITIES = [
    "our_team",      # Our Team
    "oem",           # OEM
    "partner_vendor" # Partner / Vendor
]

SERVICE_ROLES = [
    "provider",              # Provider
    "coordinator_facilitator", # Coordinator / Facilitator
    "observer"               # Observer
]

OEM_NAMES = [
    "Dell", "HP", "Lenovo", "Asus", "Acer", "Apple", 
    "Microsoft", "Samsung", "LG", "Epson", "Canon", 
    "Brother", "Cisco", "Logitech", "Other"
]

OEM_WARRANTY_TYPES = [
    "ADP",       # Accidental Damage Protection
    "NBD",       # Next Business Day
    "Standard",  # Standard Warranty
    "ProSupport",
    "Premium",
    "Extended",
    "Other"
]

OEM_CASE_RAISED_VIA = [
    "phone",
    "oem_portal",
    "email",
    "chat"
]

OEM_PRIORITY = [
    "NBD",        # Next Business Day
    "Standard",   # Standard
    "Deferred",   # Deferred
    "Critical"    # Critical/Urgent
]

OEM_CASE_STATUSES = [
    "reported_to_oem",      # Reported to OEM
    "oem_accepted",         # OEM Accepted
    "engineer_assigned",    # Engineer Assigned
    "parts_dispatched",     # Parts Dispatched
    "visit_scheduled",      # Visit Scheduled
    "resolved_by_oem",      # Resolved by OEM
    "closed_by_oem"         # Closed by OEM
]

BILLING_IMPACT = [
    "not_billable",      # Not Billable
    "warranty_covered",  # Warranty Covered
    "chargeable"         # Chargeable
]


class OEMServiceDetails(BaseModel):
    """OEM-specific service details - required for OEM warranty cases"""
    oem_name: str                          # Dell, HP, Lenovo, etc.
    oem_service_tag: Optional[str] = None  # OEM Service Tag / Serial Number
    oem_warranty_type: str                 # ADP, NBD, Standard, etc.
    oem_case_number: str                   # OEM Case / SR Number (REQUIRED)
    case_raised_date: str                  # Case Raised Date
    case_raised_via: str                   # Phone, OEM Portal, Email
    oem_priority: str = "Standard"         # NBD, Standard, Deferred
    oem_case_status: str = "reported_to_oem"  # OEM-specific status
    oem_engineer_name: Optional[str] = None
    oem_engineer_phone: Optional[str] = None
    oem_visit_date: Optional[str] = None
    oem_resolution_date: Optional[str] = None
    oem_closure_date: Optional[str] = None
    oem_remarks: Optional[str] = None


class ServiceOutcome(BaseModel):
    """Service closure/outcome details"""
    resolution_summary: str
    part_replaced: Optional[str] = None
    cost_incurred: float = 0.0
    closed_by: str  # OEM, Our Team, Customer, etc.
    closure_date: str


# ==================== SERVICE STAGE TRACKING ====================

# Default stage templates (configurable)
DEFAULT_SERVICE_STAGES = [
    {"key": "request_raised", "label": "Request Raised", "order": 1},
    {"key": "reviewed", "label": "Reviewed", "order": 2},
    {"key": "parts_approved", "label": "Parts Approved", "order": 3},
    {"key": "engineer_scheduled", "label": "Engineer Visit Scheduled", "order": 4},
    {"key": "diagnosis_completed", "label": "Engineer Diagnosed Issue", "order": 5},
    {"key": "parts_ordered", "label": "Replacement Parts Ordered", "order": 6},
    {"key": "parts_received", "label": "Parts Received", "order": 7},
    {"key": "repair_completed", "label": "Repair Completed", "order": 8},
    {"key": "request_closed", "label": "Request Closed", "order": 9},
]

# OEM-specific stages
OEM_SERVICE_STAGES = [
    {"key": "request_raised", "label": "Request Raised", "order": 1},
    {"key": "case_logged_with_oem", "label": "Case Logged with OEM", "order": 2},
    {"key": "oem_acknowledged", "label": "OEM Acknowledged", "order": 3},
    {"key": "oem_engineer_assigned", "label": "OEM Engineer Assigned", "order": 4},
    {"key": "parts_dispatched_by_oem", "label": "Parts Dispatched by OEM", "order": 5},
    {"key": "oem_visit_scheduled", "label": "OEM Visit Scheduled", "order": 6},
    {"key": "oem_repair_completed", "label": "OEM Repair Completed", "order": 7},
    {"key": "verified_by_us", "label": "Verified by Us", "order": 8},
    {"key": "request_closed", "label": "Request Closed", "order": 9},
]


class ServiceStage(BaseModel):
    """Individual stage in service timeline"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    stage_key: str                          # e.g., "request_raised", "parts_ordered"
    stage_label: str                        # e.g., "Request Raised", "Parts Ordered"
    status: str = "pending"                 # pending, in_progress, completed, skipped
    timestamp: Optional[str] = None         # When this stage was completed
    started_at: Optional[str] = None        # When this stage started
    completed_at: Optional[str] = None      # When this stage was completed
    notes: Optional[str] = None             # Stage-specific notes
    updated_by: Optional[str] = None        # Who updated this stage
    updated_by_name: Optional[str] = None   # Name of person who updated
    attachments: List[str] = []             # File references for this stage
    metadata: Optional[dict] = None         # Extra data (engineer name, part details, etc.)


class ServiceStageUpdate(BaseModel):
    """Update a specific stage"""
    stage_key: str
    status: str  # pending, in_progress, completed, skipped
    notes: Optional[str] = None
    metadata: Optional[dict] = None
    attachments: List[str] = []


class ServiceTicket(BaseModel):
    """Service tickets created by company users"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str = Field(default_factory=lambda: f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    company_id: str
    device_id: str
    created_by: str
    issue_category: str
    priority: str = "medium"
    subject: str
    description: str
    status: str = "open"
    sla_status: str = "on_track"
    attachments: List[str] = Field(default_factory=list)
    comments: List[dict] = Field(default_factory=list)
    assigned_to: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class ServiceTicketCreate(BaseModel):
    device_id: str
    issue_category: str
    subject: str
    description: str
    attachments: List[str] = []


class ServiceTicketComment(BaseModel):
    comment: str
    attachments: List[str] = []


class RenewalRequest(BaseModel):
    """Warranty/AMC renewal requests from companies"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_number: str = Field(default_factory=lambda: f"REN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    company_id: str
    request_type: str
    device_id: Optional[str] = None
    amc_contract_id: Optional[str] = None
    requested_by: str
    notes: Optional[str] = None
    status: str = "pending"
    admin_notes: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class RenewalRequestCreate(BaseModel):
    request_type: str
    device_id: Optional[str] = None
    amc_contract_id: Optional[str] = None
    notes: Optional[str] = None


class ServiceAttachment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_name: str
    file_type: str
    file_size: int
    uploaded_at: str = Field(default_factory=get_ist_isoformat)


class ServiceHistory(BaseModel):
    """Enhanced Service History with OEM support and classification"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    company_id: str
    site_id: Optional[str] = None
    deployment_id: Optional[str] = None
    
    # Basic service info
    service_date: str
    service_type: str  # Preventive Maintenance, Repair, Remote Support, etc.
    problem_reported: Optional[str] = None
    action_taken: str
    status: str = "open"  # open, in_progress, on_hold, completed, closed
    
    # ==================== NEW: Service Classification ====================
    service_category: str = "internal_service"  # internal_service, oem_warranty_service, paid_third_party_service, inspection_diagnosis
    service_responsibility: str = "our_team"    # our_team, oem, partner_vendor
    service_role: str = "provider"              # provider, coordinator_facilitator, observer
    
    # ==================== NEW: OEM Service Details ====================
    oem_details: Optional[dict] = None  # OEMServiceDetails when service_category = oem_warranty_service
    
    # ==================== NEW: Billing & AMC Protection ====================
    billing_impact: str = "not_billable"  # not_billable, warranty_covered, chargeable
    counts_toward_amc: bool = True        # Auto-locked to False for OEM cases
    
    # ==================== NEW: Service Outcome ====================
    service_outcome: Optional[dict] = None  # ServiceOutcome on closure
    
    # Parts and costs
    parts_used: Optional[List[dict]] = None
    parts_involved: Optional[List[dict]] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    total_cost: Optional[float] = None
    
    # Warranty/AMC tracking (legacy - kept for compatibility)
    warranty_impact: str = "not_applicable"
    extends_device_warranty: bool = False
    new_warranty_end_date: Optional[str] = None
    consumes_amc_quota: bool = False
    amc_quota_type: Optional[str] = None
    amc_contract_id: Optional[str] = None
    amc_covered: bool = False
    billing_type: str = "covered"
    chargeable_reason: Optional[str] = None
    
    # Assignment and tracking
    technician_name: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None
    attachments: List[ServiceAttachment] = []
    
    # Audit trail
    created_by: str
    created_by_name: str
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    closed_at: Optional[str] = None
    is_closed: bool = False


class ServiceHistoryCreate(BaseModel):
    """Create service record - with OEM support"""
    device_id: str
    site_id: Optional[str] = None
    deployment_id: Optional[str] = None
    service_date: str
    service_type: str
    problem_reported: Optional[str] = None
    action_taken: str
    status: str = "open"
    
    # Service Classification (NEW)
    service_category: str = "internal_service"
    service_responsibility: str = "our_team"
    service_role: str = "provider"
    
    # OEM Details (NEW - required if service_category = oem_warranty_service)
    oem_details: Optional[dict] = None
    
    # Billing (NEW)
    billing_impact: str = "not_billable"
    counts_toward_amc: bool = True
    
    # Parts and costs
    parts_used: Optional[List[dict]] = None
    parts_involved: Optional[List[dict]] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    
    # Legacy fields
    warranty_impact: str = "not_applicable"
    extends_device_warranty: bool = False
    new_warranty_end_date: Optional[str] = None
    consumes_amc_quota: bool = False
    amc_quota_type: Optional[str] = None
    technician_name: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None
    amc_contract_id: Optional[str] = None
    billing_type: str = "covered"
    chargeable_reason: Optional[str] = None


class ServiceHistoryUpdate(BaseModel):
    """Update service record - with OEM support and closure"""
    service_date: Optional[str] = None
    service_type: Optional[str] = None
    problem_reported: Optional[str] = None
    action_taken: Optional[str] = None
    status: Optional[str] = None
    
    # Service Classification (NEW)
    service_category: Optional[str] = None
    service_responsibility: Optional[str] = None
    service_role: Optional[str] = None
    
    # OEM Details (NEW)
    oem_details: Optional[dict] = None
    
    # Billing (NEW)
    billing_impact: Optional[str] = None
    counts_toward_amc: Optional[bool] = None
    
    # Service Outcome (NEW - for closure)
    service_outcome: Optional[dict] = None
    
    # Parts and costs
    parts_used: Optional[List[dict]] = None
    parts_involved: Optional[List[dict]] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    
    # Legacy fields
    warranty_impact: Optional[str] = None
    extends_device_warranty: Optional[bool] = None
    new_warranty_end_date: Optional[str] = None
    consumes_amc_quota: Optional[bool] = None
    amc_quota_type: Optional[str] = None
    technician_name: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None
    site_id: Optional[str] = None
    deployment_id: Optional[str] = None
    amc_contract_id: Optional[str] = None
    billing_type: Optional[str] = None
    chargeable_reason: Optional[str] = None


class ServicePartUsed(BaseModel):
    """Part used during a service record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    part_name: str
    part_type: str
    serial_number: Optional[str] = None
    quantity: int = 1
    replacement_type: str = "new"
    warranty_inherited_from_amc: bool = False
    warranty_start_date: Optional[str] = None
    warranty_end_date: Optional[str] = None
    linked_device_id: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None
