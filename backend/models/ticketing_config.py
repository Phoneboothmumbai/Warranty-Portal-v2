"""
Ticketing Configuration Models
Centralized configuration for service ticket workflows
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from datetime import datetime
from enum import Enum


# =============================================================================
# SERVICE MASTERS
# =============================================================================

class ServiceMasterType(str, Enum):
    PROBLEM_TYPE = "problem_type"
    TICKET_STATUS = "ticket_status"
    PRIORITY = "priority"
    VISIT_TYPE = "visit_type"
    SERVICE_CATEGORY = "service_category"
    RESOLUTION_TYPE = "resolution_type"


class ServiceMasterCreate(BaseModel):
    master_type: ServiceMasterType
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None  # For status badges
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    is_default: bool = False
    metadata: Optional[Dict[str, Any]] = None


class ServiceMasterUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None


class ServiceMasterResponse(BaseModel):
    id: str
    organization_id: str
    master_type: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    icon: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    is_default: bool = False
    is_system: bool = False  # System defaults can't be deleted
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


# =============================================================================
# HELP TOPICS WITH CUSTOM FORMS
# =============================================================================

class FormFieldType(str, Enum):
    TEXT = "text"
    TEXTAREA = "textarea"
    NUMBER = "number"
    EMAIL = "email"
    PHONE = "phone"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    DATE = "date"
    DATETIME = "datetime"
    FILE = "file"
    SECTION_HEADER = "section_header"


class FormFieldValidation(BaseModel):
    required: bool = False
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    pattern: Optional[str] = None  # Regex pattern
    pattern_message: Optional[str] = None
    allowed_extensions: Optional[List[str]] = None  # For file uploads


class FormFieldCondition(BaseModel):
    """Conditional logic for showing/hiding fields"""
    field_id: str  # ID of the field to check
    operator: str  # equals, not_equals, contains, greater_than, less_than, is_empty, is_not_empty
    value: Any  # Value to compare against
    logic: str = "and"  # and, or - for multiple conditions


class FormFieldOption(BaseModel):
    label: str
    value: str
    is_default: bool = False


class CustomFormField(BaseModel):
    id: str
    field_type: FormFieldType
    label: str
    placeholder: Optional[str] = None
    help_text: Optional[str] = None
    default_value: Optional[Any] = None
    options: Optional[List[FormFieldOption]] = None  # For select, radio, checkbox
    validation: Optional[FormFieldValidation] = None
    conditions: Optional[List[FormFieldCondition]] = None  # Show field only if conditions met
    width: str = "full"  # full, half, third
    sort_order: int = 0
    is_visible: bool = True


class HelpTopicCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True
    is_public: bool = True  # Visible in customer portal
    sort_order: int = 0
    
    # Default values for tickets created with this topic
    default_priority: Optional[str] = None
    default_category: Optional[str] = None
    default_problem_type: Optional[str] = None
    
    # Auto-assignment
    auto_assign_to: Optional[str] = None  # User ID
    auto_assign_team: Optional[str] = None  # Team/Department ID
    
    # SLA
    sla_response_hours: Optional[int] = None
    sla_resolution_hours: Optional[int] = None
    
    # Custom form
    custom_fields: Optional[List[CustomFormField]] = None
    
    # Parent topic for hierarchy
    parent_topic_id: Optional[str] = None


class HelpTopicUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    sort_order: Optional[int] = None
    default_priority: Optional[str] = None
    default_category: Optional[str] = None
    default_problem_type: Optional[str] = None
    auto_assign_to: Optional[str] = None
    auto_assign_team: Optional[str] = None
    sla_response_hours: Optional[int] = None
    sla_resolution_hours: Optional[int] = None
    custom_fields: Optional[List[CustomFormField]] = None
    parent_topic_id: Optional[str] = None


class HelpTopicResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True
    is_public: bool = True
    sort_order: int = 0
    default_priority: Optional[str] = None
    default_category: Optional[str] = None
    default_problem_type: Optional[str] = None
    auto_assign_to: Optional[str] = None
    auto_assign_team: Optional[str] = None
    sla_response_hours: Optional[int] = None
    sla_resolution_hours: Optional[int] = None
    custom_fields: Optional[List[CustomFormField]] = None
    parent_topic_id: Optional[str] = None
    children: Optional[List['HelpTopicResponse']] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# WORKFLOW RULES
# =============================================================================

class RuleConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"


class RuleCondition(BaseModel):
    field: str  # ticket.priority, ticket.company_id, ticket.problem_type, etc.
    operator: RuleConditionOperator
    value: Any
    logic: str = "and"  # and, or


class RuleActionType(str, Enum):
    ASSIGN_TO_USER = "assign_to_user"
    ASSIGN_TO_TEAM = "assign_to_team"
    SET_PRIORITY = "set_priority"
    SET_CATEGORY = "set_category"
    SET_STATUS = "set_status"
    ADD_TAG = "add_tag"
    SEND_EMAIL = "send_email"
    SEND_SMS = "send_sms"
    SEND_WEBHOOK = "send_webhook"
    REQUIRE_APPROVAL = "require_approval"
    ESCALATE = "escalate"
    ADD_COMMENT = "add_comment"


class RuleAction(BaseModel):
    action_type: RuleActionType
    value: Any  # User ID, Team ID, Priority value, etc.
    config: Optional[Dict[str, Any]] = None  # Additional config like email template


class WorkflowRuleTrigger(str, Enum):
    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    TICKET_PRIORITY_CHANGED = "ticket_priority_changed"
    SLA_BREACH_WARNING = "sla_breach_warning"  # X hours before breach
    SLA_BREACHED = "sla_breached"
    PARTS_REQUESTED = "parts_requested"
    VISIT_SCHEDULED = "visit_scheduled"
    VISIT_COMPLETED = "visit_completed"


class WorkflowRuleCreate(BaseModel):
    name: str
    description: Optional[str] = None
    trigger: WorkflowRuleTrigger
    conditions: List[RuleCondition]
    condition_logic: str = "all"  # all (AND) or any (OR)
    actions: List[RuleAction]
    is_active: bool = True
    sort_order: int = 0  # For execution order
    stop_processing: bool = False  # Stop other rules after this one


class WorkflowRuleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger: Optional[WorkflowRuleTrigger] = None
    conditions: Optional[List[RuleCondition]] = None
    condition_logic: Optional[str] = None
    actions: Optional[List[RuleAction]] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    stop_processing: Optional[bool] = None


class WorkflowRuleResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    description: Optional[str] = None
    trigger: str
    conditions: List[RuleCondition]
    condition_logic: str = "all"
    actions: List[RuleAction]
    is_active: bool = True
    sort_order: int = 0
    stop_processing: bool = False
    execution_count: int = 0
    last_executed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# NOTIFICATION SETTINGS
# =============================================================================

class NotificationChannel(str, Enum):
    EMAIL = "email"
    SMS = "sms"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationEvent(str, Enum):
    TICKET_CREATED = "ticket_created"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    TICKET_COMMENT_ADDED = "ticket_comment_added"
    TICKET_COMPLETED = "ticket_completed"
    TICKET_CLOSED = "ticket_closed"
    VISIT_SCHEDULED = "visit_scheduled"
    VISIT_STARTED = "visit_started"
    VISIT_COMPLETED = "visit_completed"
    PARTS_REQUESTED = "parts_requested"
    PARTS_APPROVED = "parts_approved"
    PARTS_REJECTED = "parts_rejected"
    SLA_WARNING = "sla_warning"
    SLA_BREACHED = "sla_breached"


class NotificationRecipient(str, Enum):
    TICKET_CREATOR = "ticket_creator"
    ASSIGNED_TECHNICIAN = "assigned_technician"
    COMPANY_CONTACT = "company_contact"
    TEAM_MEMBERS = "team_members"
    MANAGERS = "managers"
    SPECIFIC_USERS = "specific_users"
    SPECIFIC_EMAILS = "specific_emails"


class NotificationSettingCreate(BaseModel):
    event: NotificationEvent
    channels: List[NotificationChannel]
    recipients: List[NotificationRecipient]
    specific_user_ids: Optional[List[str]] = None
    specific_emails: Optional[List[str]] = None
    is_active: bool = True
    
    # Template customization
    email_subject: Optional[str] = None
    email_template: Optional[str] = None
    sms_template: Optional[str] = None
    
    # Conditions for sending
    conditions: Optional[List[RuleCondition]] = None


class NotificationSettingUpdate(BaseModel):
    channels: Optional[List[NotificationChannel]] = None
    recipients: Optional[List[NotificationRecipient]] = None
    specific_user_ids: Optional[List[str]] = None
    specific_emails: Optional[List[str]] = None
    is_active: Optional[bool] = None
    email_subject: Optional[str] = None
    email_template: Optional[str] = None
    sms_template: Optional[str] = None
    conditions: Optional[List[RuleCondition]] = None


class NotificationSettingResponse(BaseModel):
    id: str
    organization_id: str
    event: str
    channels: List[str]
    recipients: List[str]
    specific_user_ids: Optional[List[str]] = None
    specific_emails: Optional[List[str]] = None
    is_active: bool = True
    email_subject: Optional[str] = None
    email_template: Optional[str] = None
    sms_template: Optional[str] = None
    conditions: Optional[List[RuleCondition]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# =============================================================================
# APPROVAL SETTINGS
# =============================================================================

class ApprovalType(str, Enum):
    PARTS_REQUEST = "parts_request"
    QUOTATION = "quotation"
    TICKET_CLOSURE = "ticket_closure"
    VISIT_EXPENSE = "visit_expense"


class ApprovalSettingCreate(BaseModel):
    approval_type: ApprovalType
    name: str
    description: Optional[str] = None
    is_active: bool = True
    
    # Threshold-based approval
    threshold_field: Optional[str] = None  # e.g., "total_amount"
    threshold_value: Optional[float] = None  # e.g., 5000
    threshold_operator: str = "greater_than"  # greater_than, greater_equal
    
    # Approvers
    approver_user_ids: Optional[List[str]] = None
    approver_role: Optional[str] = None  # e.g., "manager"
    require_all_approvers: bool = False  # All must approve vs any one
    
    # Auto-approval
    auto_approve_below_threshold: bool = True


class ApprovalSettingResponse(BaseModel):
    id: str
    organization_id: str
    approval_type: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    threshold_field: Optional[str] = None
    threshold_value: Optional[float] = None
    threshold_operator: str = "greater_than"
    approver_user_ids: Optional[List[str]] = None
    approver_role: Optional[str] = None
    require_all_approvers: bool = False
    auto_approve_below_threshold: bool = True
    created_at: Optional[datetime] = None
