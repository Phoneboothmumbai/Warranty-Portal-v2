"""
Enterprise Ticketing System Models
Inspired by osTicket - Built for real IT support operations
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from utils.helpers import get_ist_isoformat


# ==================== ENUMS ====================

TICKET_SOURCES = [
    "email",
    "portal", 
    "phone",
    "whatsapp",
    "api",
    "manual"
]

TICKET_STATUSES = [
    "open",
    "in_progress",
    "waiting_on_customer",
    "waiting_on_third_party",
    "on_hold",
    "resolved",
    "closed"
]

TICKET_PRIORITIES = [
    "low",
    "medium", 
    "high",
    "critical"
]

THREAD_ENTRY_TYPES = [
    "customer_message",      # Message from customer
    "technician_reply",      # Reply visible to customer
    "internal_note",         # Staff-only note
    "system_event"           # Auto-logged events
]

SYSTEM_EVENT_TYPES = [
    "ticket_created",
    "status_changed",
    "priority_changed",
    "assigned",
    "reassigned",
    "department_changed",
    "sla_applied",
    "sla_breached",
    "sla_paused",
    "sla_resumed",
    "escalated",
    "merged",
    "auto_closed",
    "reopened",
    "attachment_added"
]

STAFF_ROLES = [
    "technician",
    "senior_technician",
    "supervisor",
    "admin"
]


# ==================== DEPARTMENT ====================

class Department(BaseModel):
    """Support department/queue configuration"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None  # None = system-wide, else company-specific
    
    name: str
    description: Optional[str] = None
    email: Optional[str] = None  # Department email for incoming tickets
    
    # Defaults
    default_sla_id: Optional[str] = None
    default_priority: str = "medium"
    auto_assign_to: Optional[str] = None  # User ID for auto-assignment
    
    # Escalation
    escalation_department_id: Optional[str] = None
    escalation_after_hours: int = 24  # Hours before escalation
    
    # Settings
    is_active: bool = True
    is_public: bool = True  # Visible to customers in portal
    sort_order: int = 0
    
    # Audit
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False


class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    default_sla_id: Optional[str] = None
    default_priority: str = "medium"
    auto_assign_to: Optional[str] = None
    is_public: bool = True
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    default_sla_id: Optional[str] = None
    default_priority: Optional[str] = None
    auto_assign_to: Optional[str] = None
    escalation_department_id: Optional[str] = None
    escalation_after_hours: Optional[int] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None


# ==================== SLA POLICY ====================

class SLAPolicy(BaseModel):
    """Service Level Agreement configuration"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None  # None = system-wide
    
    name: str
    description: Optional[str] = None
    
    # Response SLA (first reply time)
    response_time_hours: int = 4  # Hours to first response
    response_time_business_hours: bool = True  # Count only business hours
    
    # Resolution SLA
    resolution_time_hours: int = 24  # Hours to resolution
    resolution_time_business_hours: bool = True
    
    # Business hours (24h format)
    business_hours_start: str = "09:00"
    business_hours_end: str = "18:00"
    business_days: List[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])  # Mon-Fri
    
    # Holidays (dates in YYYY-MM-DD format)
    holidays: List[str] = Field(default_factory=list)
    
    # Priority multipliers (optional)
    priority_multipliers: Dict[str, float] = Field(default_factory=lambda: {
        "low": 2.0,      # 2x the time for low priority
        "medium": 1.0,   # Standard time
        "high": 0.5,     # Half time for high priority
        "critical": 0.25 # Quarter time for critical
    })
    
    # Pause conditions - SLA timer pauses when ticket in these statuses
    pause_on_statuses: List[str] = Field(default_factory=lambda: [
        "waiting_on_customer",
        "waiting_on_third_party"
    ])
    
    # Escalation
    escalate_on_breach: bool = True
    escalate_to_role: str = "supervisor"
    
    # Settings
    is_active: bool = True
    is_default: bool = False
    
    # Audit
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False


class SLAPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    response_time_hours: int = 4
    response_time_business_hours: bool = True
    resolution_time_hours: int = 24
    resolution_time_business_hours: bool = True
    business_hours_start: str = "09:00"
    business_hours_end: str = "18:00"
    business_days: List[int] = [1, 2, 3, 4, 5]
    holidays: List[str] = []
    priority_multipliers: Optional[Dict[str, float]] = None
    pause_on_statuses: List[str] = ["waiting_on_customer", "waiting_on_third_party"]
    escalate_on_breach: bool = True
    is_default: bool = False


class SLAPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    response_time_hours: Optional[int] = None
    response_time_business_hours: Optional[bool] = None
    resolution_time_hours: Optional[int] = None
    resolution_time_business_hours: Optional[bool] = None
    business_hours_start: Optional[str] = None
    business_hours_end: Optional[str] = None
    business_days: Optional[List[int]] = None
    holidays: Optional[List[str]] = None
    priority_multipliers: Optional[Dict[str, float]] = None
    pause_on_statuses: Optional[List[str]] = None
    escalate_on_breach: Optional[bool] = None
    escalate_to_role: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


# ==================== TICKET ====================

class TicketSLAStatus(BaseModel):
    """SLA tracking for a ticket"""
    sla_policy_id: Optional[str] = None
    sla_policy_name: Optional[str] = None
    
    # Response SLA
    response_due_at: Optional[str] = None
    response_met: Optional[bool] = None
    first_response_at: Optional[str] = None
    
    # Resolution SLA
    resolution_due_at: Optional[str] = None
    resolution_met: Optional[bool] = None
    resolved_at: Optional[str] = None
    
    # Pause tracking
    is_paused: bool = False
    paused_at: Optional[str] = None
    total_paused_seconds: int = 0
    
    # Breach info
    response_breached: bool = False
    resolution_breached: bool = False
    escalated: bool = False


class Ticket(BaseModel):
    """Core ticket model"""
    model_config = ConfigDict(extra="ignore")
    
    # Identity
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str = Field(default_factory=lambda: f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    
    # Multi-tenant
    company_id: str
    
    # Source & Classification
    source: str = "portal"  # email, portal, phone, whatsapp, api, manual
    department_id: Optional[str] = None
    
    # Subject & Description
    subject: str
    description: str
    
    # Status & Priority
    status: str = "open"
    priority: str = "medium"
    
    # Requester (who raised the ticket)
    requester_id: str  # User ID from company_users
    requester_name: str
    requester_email: str
    requester_phone: Optional[str] = None
    
    # Assignment
    assigned_to: Optional[str] = None  # Primary assignee (staff user ID)
    assigned_to_name: Optional[str] = None
    assigned_at: Optional[str] = None
    watchers: List[str] = Field(default_factory=list)  # Secondary watchers
    
    # SLA
    sla_status: Optional[dict] = None  # TicketSLAStatus as dict
    
    # Tags & Categories
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    
    # Custom Fields (dynamic)
    custom_fields: Dict[str, Any] = Field(default_factory=dict)
    # Examples: asset_id, serial_number, service_tag, location, warranty_status, vendor_name
    
    # Linked entities
    device_id: Optional[str] = None
    service_id: Optional[str] = None  # Link to service history
    
    # Attachments (initial attachments)
    attachments: List[dict] = Field(default_factory=list)
    
    # Counts (denormalized for performance)
    reply_count: int = 0
    internal_note_count: int = 0
    
    # Timestamps
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    first_response_at: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    last_customer_reply_at: Optional[str] = None
    last_staff_reply_at: Optional[str] = None
    
    # Audit
    created_by: str
    created_by_type: str = "customer"  # customer, staff, system
    is_deleted: bool = False


class TicketCreate(BaseModel):
    """Create ticket - used by customers and staff"""
    subject: str
    description: str
    department_id: Optional[str] = None
    priority: str = "medium"
    source: str = "portal"
    category: Optional[str] = None
    tags: List[str] = []
    custom_fields: Dict[str, Any] = {}
    device_id: Optional[str] = None
    attachments: List[dict] = []


class TicketUpdate(BaseModel):
    """Update ticket - staff only for most fields"""
    subject: Optional[str] = None
    description: Optional[str] = None
    department_id: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    assigned_to: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    custom_fields: Optional[Dict[str, Any]] = None


# ==================== TICKET THREAD ====================

class TicketThreadEntry(BaseModel):
    """Single entry in ticket conversation thread - IMMUTABLE"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    
    # Entry type
    entry_type: str  # customer_message, technician_reply, internal_note, system_event
    
    # Content (for messages/notes)
    content: Optional[str] = None
    content_html: Optional[str] = None  # Rich text version
    
    # System event details
    event_type: Optional[str] = None  # status_changed, assigned, etc.
    event_data: Optional[dict] = None  # {"old": "open", "new": "in_progress"}
    
    # Author
    author_id: str
    author_name: str
    author_type: str  # customer, technician, senior_technician, supervisor, admin, system
    author_email: Optional[str] = None
    
    # Attachments for this entry
    attachments: List[dict] = Field(default_factory=list)
    
    # Visibility
    is_internal: bool = False  # True = not visible to customer
    
    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Timestamp - IMMUTABLE
    created_at: str = Field(default_factory=get_ist_isoformat)
    
    # Soft delete only (for legal compliance, can hide but not delete)
    is_hidden: bool = False
    hidden_by: Optional[str] = None
    hidden_at: Optional[str] = None
    hidden_reason: Optional[str] = None


class TicketReplyCreate(BaseModel):
    """Create a reply to a ticket"""
    content: str
    is_internal: bool = False  # True = internal note
    attachments: List[dict] = []


# ==================== CUSTOM FIELD DEFINITION ====================

class CustomFieldDefinition(BaseModel):
    """Dynamic custom field configuration"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None  # None = system-wide
    
    name: str  # Internal name (asset_id, serial_number)
    label: str  # Display label
    field_type: str  # text, number, select, multiselect, date, checkbox
    
    # For select/multiselect
    options: List[str] = Field(default_factory=list)
    
    # Validation
    required: bool = False
    default_value: Optional[str] = None
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    
    # Visibility
    visible_to_customer: bool = True
    editable_by_customer: bool = False
    
    # Settings
    is_active: bool = True
    sort_order: int = 0
    applies_to_departments: List[str] = Field(default_factory=list)  # Empty = all
    
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False


# ==================== STAFF USER EXTENSION ====================

class TicketingStaffProfile(BaseModel):
    """Extended profile for staff in ticketing system"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    admin_user_id: str  # Links to admin_users collection
    
    # Ticketing role (separate from admin role)
    ticketing_role: str = "technician"  # technician, senior_technician, supervisor, admin
    
    # Department access
    departments: List[str] = Field(default_factory=list)  # Department IDs
    primary_department_id: Optional[str] = None
    
    # Skills/tags for auto-assignment
    skill_tags: List[str] = Field(default_factory=list)
    
    # Capacity
    max_open_tickets: int = 50  # Max tickets assignable
    
    # Signature for replies
    signature: Optional[str] = None
    
    # Settings
    auto_assign_enabled: bool = True
    notification_preferences: Dict[str, bool] = Field(default_factory=lambda: {
        "new_ticket": True,
        "ticket_assigned": True,
        "customer_reply": True,
        "sla_warning": True,
        "sla_breach": True
    })
    
    # Stats (denormalized)
    open_tickets_count: int = 0
    resolved_today_count: int = 0
    
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


# ==================== HELP TOPICS (Replaces Categories) ====================

class HelpTopic(BaseModel):
    """Help Topics define what the issue is about and drive form logic, routing, and assignment"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None  # None = system-wide
    
    name: str  # e.g., "Hardware Issue", "AppleCare+ Request"
    description: Optional[str] = None
    parent_id: Optional[str] = None  # For nested topics
    icon: Optional[str] = None  # Icon name for UI
    
    # Auto-routing configuration
    auto_department_id: Optional[str] = None
    auto_priority: Optional[str] = None
    auto_sla_id: Optional[str] = None
    auto_assign_to: Optional[str] = None  # Staff user ID
    auto_assign_team: Optional[str] = None  # Team/queue name
    
    # Custom form linked to this help topic
    custom_form_id: Optional[str] = None
    
    # Visibility
    is_public: bool = True  # Visible in customer portal
    is_active: bool = True
    sort_order: int = 0
    
    # Metadata
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False


class HelpTopicCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None
    icon: Optional[str] = None
    auto_department_id: Optional[str] = None
    auto_priority: Optional[str] = None
    auto_sla_id: Optional[str] = None
    auto_assign_to: Optional[str] = None
    auto_assign_team: Optional[str] = None
    custom_form_id: Optional[str] = None
    is_public: bool = True
    sort_order: int = 0


class HelpTopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    icon: Optional[str] = None
    auto_department_id: Optional[str] = None
    auto_priority: Optional[str] = None
    auto_sla_id: Optional[str] = None
    auto_assign_to: Optional[str] = None
    auto_assign_team: Optional[str] = None
    custom_form_id: Optional[str] = None
    is_public: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


# ==================== CUSTOM FORMS (Dynamic Forms per Help Topic) ====================

class CustomFormField(BaseModel):
    """Single field in a custom form"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Internal field name (e.g., "serial_number")
    label: str  # Display label (e.g., "Serial Number")
    field_type: str  # text, textarea, number, email, phone, select, multiselect, checkbox, date, datetime, file
    
    # For select/multiselect fields
    options: List[Dict[str, str]] = Field(default_factory=list)  # [{"value": "laptop", "label": "Laptop"}]
    
    # Validation
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    pattern: Optional[str] = None  # Regex pattern
    
    # UI
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    default_value: Optional[Any] = None
    width: str = "full"  # full, half, third
    
    # Visibility
    visible_to_customer: bool = True
    editable_by_customer: bool = True
    
    sort_order: int = 0


class CustomForm(BaseModel):
    """Custom form definition - linked to Help Topics"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None
    
    name: str  # e.g., "Hardware Issue Form", "AppleCare+ Request Form"
    description: Optional[str] = None
    
    # Form fields
    fields: List[CustomFormField] = Field(default_factory=list)
    
    # Versioning - when form changes, increment version
    version: int = 1
    
    is_active: bool = True
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False


class CustomFormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    fields: List[dict] = []


class CustomFormUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    fields: Optional[List[dict]] = None
    is_active: Optional[bool] = None


# ==================== TICKET PARTICIPANTS (CC/Collaboration) ====================

class TicketParticipant(BaseModel):
    """Participant on a ticket - for CC/collaboration"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    
    # Participant info
    user_id: Optional[str] = None  # If internal user
    name: str
    email: str
    phone: Optional[str] = None
    
    # Type
    participant_type: str = "cc"  # cc, collaborator, watcher
    is_external: bool = False  # True for email-only participants
    
    # Permissions
    can_reply: bool = True
    can_view_internal_notes: bool = False
    receives_notifications: bool = True
    
    # Metadata
    added_by: str  # User ID who added this participant
    added_by_name: str
    added_at: str = Field(default_factory=get_ist_isoformat)
    removed_at: Optional[str] = None
    is_active: bool = True


class AddParticipantRequest(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    participant_type: str = "cc"
    can_reply: bool = True


# ==================== CANNED RESPONSES ====================

class CannedResponse(BaseModel):
    """Predefined reply templates"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Ownership
    company_id: Optional[str] = None  # None = system-wide
    department_id: Optional[str] = None  # None = all departments
    created_by: str  # Staff user ID
    
    # Content
    title: str  # Short name for quick selection
    content: str  # The actual response text with variables
    
    # Variables supported: {{customer_name}}, {{ticket_id}}, {{ticket_number}}, 
    # {{device_name}}, {{sla_due}}, {{department_name}}, {{assigned_to}}
    
    # Categorization
    category: Optional[str] = None  # e.g., "Acknowledgement", "Troubleshooting", "Closure"
    tags: List[str] = Field(default_factory=list)
    
    # Scope
    is_personal: bool = False  # True = only creator can use, False = shared
    is_active: bool = True
    
    # Stats
    usage_count: int = 0
    last_used_at: Optional[str] = None
    
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False


class CannedResponseCreate(BaseModel):
    title: str
    content: str
    department_id: Optional[str] = None
    category: Optional[str] = None
    tags: List[str] = []
    is_personal: bool = False


class CannedResponseUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    department_id: Optional[str] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    is_personal: Optional[bool] = None
    is_active: Optional[bool] = None


# ==================== TICKET FORM DATA (Versioned snapshot) ====================

class TicketFormData(BaseModel):
    """Stores the form data submitted with a ticket - immutable snapshot"""
    form_id: str
    form_name: str
    form_version: int
    fields: List[dict]  # Snapshot of field definitions at submission time
    values: Dict[str, Any]  # Actual values submitted
    submitted_at: str = Field(default_factory=get_ist_isoformat)


# ==================== LEGACY: TICKET CATEGORY (Deprecated - use HelpTopic) ====================

class TicketCategory(BaseModel):
    """Ticket categories/issue types - DEPRECATED: Use HelpTopic instead"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: Optional[str] = None
    
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None  # For nested categories
    
    # Auto-routing
    auto_department_id: Optional[str] = None
    auto_priority: Optional[str] = None
    
    is_active: bool = True
    sort_order: int = 0
    
    created_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False
