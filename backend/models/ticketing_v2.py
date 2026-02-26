"""
Ticketing System v2 - Complete Models
=====================================
A fully configurable, workflow-driven ticketing system.

Collections:
- ticket_help_topics: Help topics that drive ticket creation
- ticket_forms: Custom forms linked to help topics
- ticket_workflows: Workflow templates with stages
- ticket_stages: Individual workflow stages
- ticket_sla_policies: SLA rules
- ticket_priorities: Priority levels
- ticket_teams: Teams/departments
- ticket_roles: Roles with permissions
- ticket_task_types: Task templates
- ticket_canned_responses: Pre-written responses
- ticket_notification_templates: Email/SMS templates
- ticket_business_hours: Working hours/holidays
- tickets_v2: Main ticket collection
- ticket_tasks: Tasks generated from workflows
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


def get_ist_isoformat():
    """Get current time in IST as ISO format string"""
    from datetime import timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).isoformat()


# ==================== ENUMS ====================

class FieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    DATETIME = "datetime"
    SELECT = "select"
    MULTISELECT = "multiselect"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    EMAIL = "email"
    PHONE = "phone"
    URL = "url"
    FILE = "file"
    COMPANY_LOOKUP = "company_lookup"
    DEVICE_LOOKUP = "device_lookup"
    CONTACT_LOOKUP = "contact_lookup"
    USER_LOOKUP = "user_lookup"
    HIDDEN = "hidden"


class StageType(str, Enum):
    INITIAL = "initial"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    TERMINAL_SUCCESS = "terminal_success"
    TERMINAL_FAILURE = "terminal_failure"


class ActionType(str, Enum):
    CREATE_TASK = "create_task"
    ASSIGN_TO_TEAM = "assign_to_team"
    ASSIGN_TO_USER = "assign_to_user"
    SEND_NOTIFICATION = "send_notification"
    SEND_EMAIL = "send_email"
    UPDATE_FIELD = "update_field"
    CREATE_QUOTE = "create_quote"
    WEBHOOK = "webhook"


class NotificationChannel(str, Enum):
    EMAIL = "email"
    IN_APP = "in_app"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class AssignmentMethod(str, Enum):
    ROUND_ROBIN = "round_robin"
    LOAD_BALANCED = "load_balanced"
    MANUAL = "manual"
    SKILL_BASED = "skill_based"


# ==================== FORM MODELS ====================

class FormField(BaseModel):
    """Individual form field definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    field_type: str = FieldType.TEXT.value
    label: str
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    required: bool = False
    order: int = 0
    default_value: Optional[Any] = None
    options: List[Dict[str, str]] = Field(default_factory=list)  # For select/radio
    validation: Optional[Dict[str, Any]] = None  # min, max, pattern, etc.
    conditional: Optional[Dict[str, Any]] = None  # Show/hide based on other field
    width: str = "full"  # full, half, third
    section: Optional[str] = None  # Group fields into sections


class TicketForm(BaseModel):
    """Custom form definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None
    fields: List[FormField] = Field(default_factory=list)
    is_active: bool = True
    is_system: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


# ==================== WORKFLOW MODELS ====================

class StageAction(BaseModel):
    """Action to perform when entering a stage"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    action_type: str = ActionType.CREATE_TASK.value
    config: Dict[str, Any] = Field(default_factory=dict)
    # Config examples:
    # CREATE_TASK: {task_type_id, assign_to_team_id, due_hours}
    # ASSIGN_TO_TEAM: {team_id}
    # SEND_NOTIFICATION: {template_id, recipients: [assignee, creator, customer]}
    # SEND_EMAIL: {template_id, to: customer}
    order: int = 0


class StageTransition(BaseModel):
    """Transition rule between stages"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    to_stage_id: str
    label: str  # Button text: "Mark Complete", "Approve", etc.
    icon: Optional[str] = None
    color: str = "default"  # default, success, warning, danger
    confirm_message: Optional[str] = None
    required_fields: List[str] = Field(default_factory=list)  # Fields that must be filled
    required_permissions: List[str] = Field(default_factory=list)
    conditions: Optional[Dict[str, Any]] = None  # Field conditions for this transition
    order: int = 0


class WorkflowStage(BaseModel):
    """Individual workflow stage"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    slug: str
    description: Optional[str] = None
    stage_type: str = StageType.IN_PROGRESS.value
    color: str = "#6B7280"
    icon: Optional[str] = None
    order: int = 0
    
    # Who handles tickets at this stage
    assigned_team_id: Optional[str] = None
    assigned_role: Optional[str] = None
    
    # SLA for this stage
    sla_hours: Optional[int] = None
    
    # Actions when ticket enters this stage
    entry_actions: List[StageAction] = Field(default_factory=list)
    
    # Possible transitions from this stage
    transitions: List[StageTransition] = Field(default_factory=list)
    
    # Fields to show/require at this stage
    visible_fields: List[str] = Field(default_factory=list)
    required_fields: List[str] = Field(default_factory=list)


class TicketWorkflow(BaseModel):
    """Complete workflow definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None
    stages: List[WorkflowStage] = Field(default_factory=list)
    is_active: bool = True
    is_system: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


# ==================== HELP TOPIC ====================

class HelpTopic(BaseModel):
    """Help topic - the master controller"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Basic info
    name: str
    slug: str
    description: Optional[str] = None
    icon: str = "ticket"
    color: str = "#3B82F6"
    category: str = "general"  # support, sales, operations, etc.
    
    # Linked entities
    form_id: Optional[str] = None
    workflow_id: Optional[str] = None
    sla_policy_id: Optional[str] = None
    default_team_id: Optional[str] = None
    default_priority: str = "medium"
    
    # Settings
    auto_assign: bool = False
    assignment_method: str = AssignmentMethod.MANUAL.value
    require_company: bool = True
    require_contact: bool = True
    require_device: bool = False
    
    # Visibility
    is_public: bool = True  # Show in customer portal
    is_active: bool = True
    is_system: bool = False
    
    # Stats
    ticket_count: int = 0
    
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


# ==================== SLA POLICY ====================

class SLAPolicy(BaseModel):
    """SLA Policy definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    description: Optional[str] = None
    
    # Response time (first reply)
    response_time_hours: int = 4
    
    # Resolution time
    resolution_time_hours: int = 24
    
    # Business hours only
    business_hours_only: bool = True
    business_hours_id: Optional[str] = None
    
    # Escalation
    escalation_enabled: bool = True
    escalation_after_hours: int = 8
    escalate_to_team_id: Optional[str] = None
    
    # Priority multipliers
    priority_multipliers: Dict[str, float] = Field(default_factory=lambda: {
        "low": 2.0,
        "medium": 1.0,
        "high": 0.5,
        "critical": 0.25
    })
    
    is_default: bool = False
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)


# ==================== PRIORITY ====================

class TicketPriority(BaseModel):
    """Priority level definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    slug: str
    color: str
    icon: Optional[str] = None
    order: int = 0
    sla_multiplier: float = 1.0
    auto_escalate: bool = False
    is_default: bool = False
    is_active: bool = True


# ==================== TEAM ====================

class TeamMember(BaseModel):
    """Team member assignment"""
    user_id: str
    user_name: str
    user_email: str
    role_id: Optional[str] = None
    is_manager: bool = False
    added_at: str = Field(default_factory=get_ist_isoformat)


class TicketTeam(BaseModel):
    """Team/Department definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: str = "#6B7280"
    
    # Members
    members: List[TeamMember] = Field(default_factory=list)
    manager_id: Optional[str] = None
    
    # Assignment
    assignment_method: str = AssignmentMethod.ROUND_ROBIN.value
    
    # Working hours
    business_hours_id: Optional[str] = None
    
    # Email
    team_email: Optional[str] = None
    
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)


# ==================== ROLE ====================

class TicketRole(BaseModel):
    """Role with permissions"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None
    
    # Permissions
    permissions: List[str] = Field(default_factory=list)
    # Examples:
    # tickets.view_all, tickets.view_assigned, tickets.create, tickets.edit
    # tickets.assign, tickets.close, tickets.delete
    # tasks.view, tasks.complete, tasks.reassign
    # quotes.create, quotes.send, quotes.approve
    # parts.request, parts.order, parts.receive
    # admin.settings, admin.users, admin.reports
    
    # Dashboard config
    dashboard_widgets: List[str] = Field(default_factory=list)
    
    is_system: bool = False
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)


# ==================== TASK TYPE ====================

class TaskChecklistItem(BaseModel):
    """Checklist item for a task"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    text: str
    required: bool = False
    order: int = 0


class TaskType(BaseModel):
    """Task type template"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: str = "#6B7280"
    
    # Default assignment
    default_team_id: Optional[str] = None
    default_role: Optional[str] = None
    
    # Time
    default_due_hours: int = 24
    
    # Checklist template
    checklist: List[TaskChecklistItem] = Field(default_factory=list)
    
    # Fields to capture when completing
    completion_fields: List[FormField] = Field(default_factory=list)
    
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)


# ==================== CANNED RESPONSE ====================

class CannedResponse(BaseModel):
    """Pre-written response template"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    slug: str
    category: Optional[str] = None
    
    # Content
    subject: Optional[str] = None
    body: str
    
    # Variables available: {{ticket.number}}, {{customer.name}}, etc.
    
    # Restrictions
    help_topic_ids: List[str] = Field(default_factory=list)  # Empty = all topics
    
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)


# ==================== NOTIFICATION TEMPLATE ====================

class NotificationTemplate(BaseModel):
    """Notification template"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    slug: str
    event: str  # ticket_created, ticket_assigned, task_created, etc.
    
    # Channels
    channels: List[str] = Field(default_factory=lambda: [NotificationChannel.EMAIL.value, NotificationChannel.IN_APP.value])
    
    # Email content
    email_subject: Optional[str] = None
    email_body: Optional[str] = None
    
    # In-app content
    in_app_title: Optional[str] = None
    in_app_body: Optional[str] = None
    
    # SMS content
    sms_body: Optional[str] = None
    
    # WhatsApp content
    whatsapp_template_id: Optional[str] = None
    
    # Recipients
    recipients: List[str] = Field(default_factory=list)  # assignee, creator, customer, team, manager
    
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)


# ==================== BUSINESS HOURS ====================

class BusinessHours(BaseModel):
    """Business hours definition"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    
    # Weekly schedule
    schedule: Dict[str, Dict[str, str]] = Field(default_factory=lambda: {
        "monday": {"start": "09:00", "end": "18:00"},
        "tuesday": {"start": "09:00", "end": "18:00"},
        "wednesday": {"start": "09:00", "end": "18:00"},
        "thursday": {"start": "09:00", "end": "18:00"},
        "friday": {"start": "09:00", "end": "18:00"},
        "saturday": {"start": "09:00", "end": "14:00"},
        "sunday": None
    })
    
    # Holidays
    holidays: List[Dict[str, str]] = Field(default_factory=list)  # [{date, name}]
    
    timezone: str = "Asia/Kolkata"
    is_default: bool = False
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)


# ==================== TICKET (NEW) ====================

class TicketContact(BaseModel):
    """Contact information"""
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class TicketTimelineEntry(BaseModel):
    """Timeline entry for ticket history"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # stage_change, comment, task_created, task_completed, email_sent, etc.
    description: str
    details: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    is_internal: bool = False  # Internal note vs public comment
    created_at: str = Field(default_factory=get_ist_isoformat)


class TicketV2(BaseModel):
    """New ticket model - workflow driven"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Identification
    ticket_number: str
    
    # Help Topic & Workflow
    help_topic_id: str
    help_topic_name: str
    workflow_id: Optional[str] = None
    current_stage_id: Optional[str] = None
    current_stage_name: Optional[str] = None
    
    # Basic info
    subject: str
    description: Optional[str] = None
    
    # Custom form values
    form_values: Dict[str, Any] = Field(default_factory=dict)
    
    # Company & Contact
    company_id: Optional[str] = None
    company_name: Optional[str] = None
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    custom_location: Optional[str] = None
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    contact: Optional[TicketContact] = None
    
    # Device (if applicable)
    device_id: Optional[str] = None
    device_name: Optional[str] = None
    device_description: Optional[str] = None
    
    # Priority & SLA
    priority_id: Optional[str] = None
    priority_name: str = "medium"
    sla_policy_id: Optional[str] = None
    response_due_at: Optional[str] = None
    resolution_due_at: Optional[str] = None
    sla_breached: bool = False
    
    # Assignment
    assigned_team_id: Optional[str] = None
    assigned_team_name: Optional[str] = None
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    
    # Status flags
    is_open: bool = True
    is_overdue: bool = False
    is_escalated: bool = False
    
    # Source
    source: str = "web"  # web, email, phone, chat, api
    source_reference: Optional[str] = None
    
    # Timeline
    timeline: List[TicketTimelineEntry] = Field(default_factory=list)
    
    # Tasks
    task_ids: List[str] = Field(default_factory=list)
    
    # Linked entities
    quote_ids: List[str] = Field(default_factory=list)
    
    # Metadata
    tags: List[str] = Field(default_factory=list)
    
    # Timestamps
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: Optional[str] = None
    created_by_name: Optional[str] = None
    updated_at: str = Field(default_factory=get_ist_isoformat)
    first_response_at: Optional[str] = None
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    
    # Soft delete
    is_deleted: bool = False


# ==================== TASK ====================

class TaskChecklist(BaseModel):
    """Task checklist item with completion status"""
    id: str
    text: str
    required: bool = False
    completed: bool = False
    completed_at: Optional[str] = None
    completed_by_id: Optional[str] = None


class TicketTask(BaseModel):
    """Task generated from workflow"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Link to ticket
    ticket_id: str
    ticket_number: str
    
    # Task type
    task_type_id: Optional[str] = None
    task_type_name: Optional[str] = None
    
    # Task info
    name: str
    description: Optional[str] = None
    
    # Assignment
    assigned_team_id: Optional[str] = None
    assigned_team_name: Optional[str] = None
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    
    # Status
    status: str = "pending"  # pending, in_progress, completed, cancelled
    
    # Checklist
    checklist: List[TaskChecklist] = Field(default_factory=list)
    
    # Completion data
    completion_values: Dict[str, Any] = Field(default_factory=dict)
    completion_notes: Optional[str] = None
    
    # Time
    due_at: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    
    # Metadata
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: Optional[str] = None
    updated_at: str = Field(default_factory=get_ist_isoformat)


# ==================== CREATE/UPDATE MODELS ====================

class TicketCreateV2(BaseModel):
    """Create new ticket"""
    help_topic_id: str
    subject: str
    description: Optional[str] = None
    form_values: Dict[str, Any] = Field(default_factory=dict)
    company_id: Optional[str] = None
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    custom_location: Optional[str] = None  # For "another location" not in list
    employee_id: Optional[str] = None
    employee_name: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    device_id: Optional[str] = None
    device_description: Optional[str] = None  # Free-text for unlisted device
    priority_id: Optional[str] = None
    source: str = "web"


class TicketUpdateV2(BaseModel):
    """Update ticket"""
    subject: Optional[str] = None
    description: Optional[str] = None
    form_values: Optional[Dict[str, Any]] = None
    priority_id: Optional[str] = None
    assigned_team_id: Optional[str] = None
    assigned_to_id: Optional[str] = None
    tags: Optional[List[str]] = None


class StageTransitionRequest(BaseModel):
    """Request to transition ticket to new stage"""
    transition_id: str
    notes: Optional[str] = None
    field_values: Optional[Dict[str, Any]] = None
    # Engineer assignment
    assigned_to_id: Optional[str] = None
    assigned_to_name: Optional[str] = None
    # Visit scheduling
    scheduled_at: Optional[str] = None
    scheduled_end_at: Optional[str] = None
    schedule_notes: Optional[str] = None
    # Diagnosis
    diagnosis_findings: Optional[str] = None
    diagnosis_recommendation: Optional[str] = None
    # Parts
    parts_list: Optional[List[Dict[str, Any]]] = None
    # Resolution
    resolution_notes: Optional[str] = None
