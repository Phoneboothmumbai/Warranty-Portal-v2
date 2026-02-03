"""
Staff Module Models
===================
Implements the complete staff management system with:
- User lifecycle FSM (CREATED → ACTIVE → SUSPENDED → ARCHIVED)
- Dynamic Roles & Permissions (no hardcoding)
- Departments (organizational grouping)
- Audit logging (append-only)

Authority Layers:
- Layer 1: Super Admin (platform owner)
- Layer 2: Platform Admin (manages tenants)
- Layer 3: Tenant/MSP (manages their staff & customers)
- Layer 4: Customer Organization (limited access)
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from utils.helpers import get_ist_isoformat


# ==================== ENUMS ====================

class UserState(str, Enum):
    """FSM States for User Lifecycle"""
    CREATED = "created"      # User exists but cannot log in
    ACTIVE = "active"        # User can log in, permissions enforced
    SUSPENDED = "suspended"  # Temporary lock, login blocked
    ARCHIVED = "archived"    # Permanently inactive, data retained for audit


class UserType(str, Enum):
    """User Types"""
    INTERNAL = "internal"    # Your company staff (MSP employees)
    CUSTOMER = "customer"    # Client company staff


# Valid state transitions
VALID_STATE_TRANSITIONS = {
    UserState.CREATED: [UserState.ACTIVE, UserState.ARCHIVED],
    UserState.ACTIVE: [UserState.SUSPENDED, UserState.ARCHIVED],
    UserState.SUSPENDED: [UserState.ACTIVE, UserState.ARCHIVED],
    UserState.ARCHIVED: []  # No transitions allowed from ARCHIVED
}


# ==================== PERMISSION MODEL ====================

class Permission(BaseModel):
    """
    Permission Definition
    Format: MODULE → RESOURCE → ACTION
    
    Example:
    - module: "inventory", resource: "stock", action: "view"
    - module: "service", resource: "job", action: "assign"
    - module: "staff", resource: "user", action: "edit"
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant this permission belongs to
    
    # Permission definition
    module: str           # e.g., "inventory", "service", "staff", "tickets"
    resource: str         # e.g., "stock", "job", "user", "ticket"
    action: str           # e.g., "view", "create", "edit", "delete", "assign"
    
    # Display
    name: str             # Human-readable name
    description: Optional[str] = None
    
    # Categorization
    category: Optional[str] = None  # For grouping in UI
    
    # Metadata
    is_system: bool = False  # System permissions cannot be deleted
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    
    @property
    def code(self) -> str:
        """Generate permission code: module.resource.action"""
        return f"{self.module}.{self.resource}.{self.action}"


class PermissionCreate(BaseModel):
    """Create a new permission"""
    module: str
    resource: str
    action: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None


class PermissionUpdate(BaseModel):
    """Update permission (only display fields)"""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


# ==================== ROLE MODEL ====================

class RolePermission(BaseModel):
    """Permission assignment within a role"""
    permission_id: str
    permission_code: str  # Denormalized for quick lookup
    
    # Time-bound access (optional)
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None
    
    # Visibility scope
    visibility_scope: str = "self"  # global, assigned_companies, assigned_customers, self


class Role(BaseModel):
    """
    Dynamic Role Definition
    
    Roles:
    - Start with ZERO permissions
    - Admin must explicitly assign permissions
    - Changes affect all users instantly
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant this role belongs to
    
    # Role info
    name: str
    description: Optional[str] = None
    
    # Permissions
    permissions: List[RolePermission] = Field(default_factory=list)
    
    # Role level (for hierarchy)
    level: int = 100  # Lower = more authority. 0=admin, 100=default
    
    # Flags
    is_system: bool = False      # System roles cannot be deleted
    is_default: bool = False     # Default role for new users
    can_be_assigned: bool = True # Can this role be assigned to users?
    
    # Metadata
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None


class RoleCreate(BaseModel):
    """Create a new role"""
    name: str
    description: Optional[str] = None
    level: int = 100
    is_default: bool = False


class RoleUpdate(BaseModel):
    """Update role details"""
    name: Optional[str] = None
    description: Optional[str] = None
    level: Optional[int] = None
    is_default: Optional[bool] = None
    can_be_assigned: Optional[bool] = None


class RolePermissionAssignment(BaseModel):
    """Assign/remove permissions from a role"""
    permission_ids: List[str]
    visibility_scope: str = "self"
    valid_from: Optional[str] = None
    valid_until: Optional[str] = None


# ==================== DEPARTMENT MODEL ====================

class Department(BaseModel):
    """
    Department - Organizational grouping
    
    Departments:
    - Are purely organizational
    - Do NOT grant permissions
    - Do NOT override roles
    - Used for: Reporting, Filtering, Ownership grouping
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant this department belongs to
    
    # Department info
    name: str
    code: Optional[str] = None  # Short code for the department
    description: Optional[str] = None
    
    # Hierarchy
    parent_id: Optional[str] = None  # For nested departments
    
    # Manager
    manager_id: Optional[str] = None  # User ID of department manager
    
    # Metadata
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None


class DepartmentCreate(BaseModel):
    """Create a new department"""
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None


class DepartmentUpdate(BaseModel):
    """Update department"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: Optional[bool] = None


# ==================== STAFF USER MODEL ====================

class StaffUser(BaseModel):
    """
    Staff User - Internal or Customer user with FSM lifecycle
    
    FSM States:
    - CREATED: User exists but cannot log in
    - ACTIVE: User can log in, permissions enforced
    - SUSPENDED: Temporary lock, login blocked
    - ARCHIVED: Permanently inactive (no reactivation)
    
    Each user belongs to:
    - Exactly one company (organization for internal, customer company for customer users)
    - One or more departments
    - One or more roles
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant (MSP) this user belongs to
    
    # User type
    user_type: str = UserType.INTERNAL  # internal or customer
    
    # For customer users: which customer company they belong to
    customer_company_id: Optional[str] = None
    
    # Basic info
    email: str
    name: str
    password_hash: Optional[str] = None  # Optional for invited users
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    employee_id: Optional[str] = None  # Internal employee ID
    job_title: Optional[str] = None
    
    # FSM State
    state: str = UserState.CREATED
    state_changed_at: str = Field(default_factory=get_ist_isoformat)
    state_changed_by: Optional[str] = None
    state_change_reason: Optional[str] = None
    
    # Departments (one or more)
    department_ids: List[str] = Field(default_factory=list)
    primary_department_id: Optional[str] = None
    
    # Roles (one or more)
    role_ids: List[str] = Field(default_factory=list)
    
    # For technicians: assigned customer companies
    assigned_company_ids: List[str] = Field(default_factory=list)
    
    # Security
    ip_whitelist: List[str] = Field(default_factory=list)  # Empty = no restriction
    device_ids: List[str] = Field(default_factory=list)    # Approved devices
    
    # Sensitive data (separate permission required)
    salary: Optional[float] = None
    internal_notes: Optional[str] = None
    performance_rating: Optional[int] = None
    
    # Session tracking
    last_login: Optional[str] = None
    last_login_ip: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    
    # Invitation
    invite_token: Optional[str] = None
    invite_expires_at: Optional[str] = None
    invited_by: Optional[str] = None
    
    # Metadata
    is_deleted: bool = False  # Soft delete only
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None
    
    def can_transition_to(self, new_state: UserState) -> bool:
        """Check if state transition is valid"""
        current = UserState(self.state)
        return new_state in VALID_STATE_TRANSITIONS.get(current, [])
    
    def is_login_allowed(self) -> bool:
        """Check if user can log in"""
        return self.state == UserState.ACTIVE and not self.is_deleted


class StaffUserCreate(BaseModel):
    """Create a new staff user"""
    email: str
    name: str
    password: Optional[str] = None  # If None, send invitation
    user_type: str = UserType.INTERNAL
    customer_company_id: Optional[str] = None  # Required for customer users
    phone: Optional[str] = None
    employee_id: Optional[str] = None
    job_title: Optional[str] = None
    department_ids: Optional[List[str]] = None
    primary_department_id: Optional[str] = None
    role_ids: Optional[List[str]] = None
    assigned_company_ids: Optional[List[str]] = None


class StaffUserUpdate(BaseModel):
    """Update staff user"""
    name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    employee_id: Optional[str] = None
    job_title: Optional[str] = None
    department_ids: Optional[List[str]] = None
    primary_department_id: Optional[str] = None
    role_ids: Optional[List[str]] = None
    assigned_company_ids: Optional[List[str]] = None
    ip_whitelist: Optional[List[str]] = None
    device_ids: Optional[List[str]] = None


class StaffUserStateTransition(BaseModel):
    """Request to change user state"""
    new_state: str
    reason: str  # Mandatory reason for audit


class SensitiveDataUpdate(BaseModel):
    """Update sensitive user data (requires special permission)"""
    salary: Optional[float] = None
    internal_notes: Optional[str] = None
    performance_rating: Optional[int] = None


# ==================== AUDIT LOG MODEL ====================

class StaffAuditLog(BaseModel):
    """
    Immutable Audit Log Entry
    
    Logs every:
    - User creation, update, deletion
    - Role assignment/removal
    - Permission changes
    - Department changes
    - State transitions (activation/suspension/archival)
    - Login failures (restricted access)
    
    Properties:
    - Append-only (cannot be edited or deleted)
    - Includes before/after state
    - Tracks who made the change
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant
    
    # What changed
    entity_type: str      # user, role, permission, department
    entity_id: str        # ID of the entity
    entity_name: Optional[str] = None  # For display
    
    # Action
    action: str           # create, update, delete, state_change, login_failed, permission_granted, etc.
    
    # Changes
    changes: Dict[str, Any] = Field(default_factory=dict)  # {field: {before, after}}
    before_state: Optional[Dict[str, Any]] = None  # Full state before
    after_state: Optional[Dict[str, Any]] = None   # Full state after
    
    # Who made the change
    performed_by_id: str
    performed_by_name: str
    performed_by_email: Optional[str] = None
    performed_by_role: Optional[str] = None
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Override tracking
    is_override: bool = False
    override_reason: Optional[str] = None
    
    # Timestamp (immutable)
    timestamp: str = Field(default_factory=get_ist_isoformat)
    
    # Flags
    severity: str = "info"  # info, warning, critical


# ==================== DEFAULT PERMISSIONS ====================

DEFAULT_PERMISSIONS = [
    # Staff Module
    {"module": "staff", "resource": "user", "action": "view", "name": "View Users", "category": "Staff"},
    {"module": "staff", "resource": "user", "action": "create", "name": "Create Users", "category": "Staff"},
    {"module": "staff", "resource": "user", "action": "edit", "name": "Edit Users", "category": "Staff"},
    {"module": "staff", "resource": "user", "action": "delete", "name": "Archive Users", "category": "Staff"},
    {"module": "staff", "resource": "user", "action": "activate", "name": "Activate Users", "category": "Staff"},
    {"module": "staff", "resource": "user", "action": "suspend", "name": "Suspend Users", "category": "Staff"},
    {"module": "staff", "resource": "user_sensitive", "action": "view", "name": "View Sensitive Data", "category": "Staff"},
    {"module": "staff", "resource": "user_sensitive", "action": "edit", "name": "Edit Sensitive Data", "category": "Staff"},
    {"module": "staff", "resource": "role", "action": "view", "name": "View Roles", "category": "Staff"},
    {"module": "staff", "resource": "role", "action": "create", "name": "Create Roles", "category": "Staff"},
    {"module": "staff", "resource": "role", "action": "edit", "name": "Edit Roles", "category": "Staff"},
    {"module": "staff", "resource": "role", "action": "delete", "name": "Delete Roles", "category": "Staff"},
    {"module": "staff", "resource": "department", "action": "view", "name": "View Departments", "category": "Staff"},
    {"module": "staff", "resource": "department", "action": "create", "name": "Create Departments", "category": "Staff"},
    {"module": "staff", "resource": "department", "action": "edit", "name": "Edit Departments", "category": "Staff"},
    {"module": "staff", "resource": "department", "action": "delete", "name": "Delete Departments", "category": "Staff"},
    {"module": "staff", "resource": "audit", "action": "view", "name": "View Audit Logs", "category": "Staff"},
    
    # Inventory Module
    {"module": "inventory", "resource": "device", "action": "view", "name": "View Devices", "category": "Inventory"},
    {"module": "inventory", "resource": "device", "action": "create", "name": "Create Devices", "category": "Inventory"},
    {"module": "inventory", "resource": "device", "action": "edit", "name": "Edit Devices", "category": "Inventory"},
    {"module": "inventory", "resource": "device", "action": "delete", "name": "Delete Devices", "category": "Inventory"},
    {"module": "inventory", "resource": "stock", "action": "view", "name": "View Stock", "category": "Inventory"},
    {"module": "inventory", "resource": "stock", "action": "edit", "name": "Manage Stock", "category": "Inventory"},
    
    # Service Module
    {"module": "service", "resource": "ticket", "action": "view", "name": "View Tickets", "category": "Service"},
    {"module": "service", "resource": "ticket", "action": "create", "name": "Create Tickets", "category": "Service"},
    {"module": "service", "resource": "ticket", "action": "edit", "name": "Edit Tickets", "category": "Service"},
    {"module": "service", "resource": "ticket", "action": "delete", "name": "Delete Tickets", "category": "Service"},
    {"module": "service", "resource": "ticket", "action": "assign", "name": "Assign Tickets", "category": "Service"},
    {"module": "service", "resource": "ticket", "action": "close", "name": "Close Tickets", "category": "Service"},
    {"module": "service", "resource": "job", "action": "view", "name": "View Jobs", "category": "Service"},
    {"module": "service", "resource": "job", "action": "create", "name": "Create Jobs", "category": "Service"},
    {"module": "service", "resource": "job", "action": "assign", "name": "Assign Jobs", "category": "Service"},
    
    # AMC Module
    {"module": "amc", "resource": "contract", "action": "view", "name": "View AMC Contracts", "category": "AMC"},
    {"module": "amc", "resource": "contract", "action": "create", "name": "Create AMC Contracts", "category": "AMC"},
    {"module": "amc", "resource": "contract", "action": "edit", "name": "Edit AMC Contracts", "category": "AMC"},
    {"module": "amc", "resource": "contract", "action": "delete", "name": "Delete AMC Contracts", "category": "AMC"},
    
    # Company Module
    {"module": "company", "resource": "company", "action": "view", "name": "View Companies", "category": "Company"},
    {"module": "company", "resource": "company", "action": "create", "name": "Create Companies", "category": "Company"},
    {"module": "company", "resource": "company", "action": "edit", "name": "Edit Companies", "category": "Company"},
    {"module": "company", "resource": "company", "action": "delete", "name": "Delete Companies", "category": "Company"},
    
    # Reports Module
    {"module": "reports", "resource": "report", "action": "view", "name": "View Reports", "category": "Reports"},
    {"module": "reports", "resource": "report", "action": "export", "name": "Export Reports", "category": "Reports"},
    
    # Settings Module
    {"module": "settings", "resource": "organization", "action": "view", "name": "View Settings", "category": "Settings"},
    {"module": "settings", "resource": "organization", "action": "edit", "name": "Edit Settings", "category": "Settings"},
    {"module": "settings", "resource": "billing", "action": "view", "name": "View Billing", "category": "Settings"},
    {"module": "settings", "resource": "billing", "action": "edit", "name": "Manage Billing", "category": "Settings"},
]


# ==================== DEFAULT ROLES ====================

DEFAULT_ROLES = [
    {
        "name": "Administrator",
        "description": "Full access to all features within the organization",
        "level": 0,
        "is_system": True,
        "is_default": False,
        "permissions": ["*"]  # All permissions
    },
    {
        "name": "Manager",
        "description": "Can manage staff, view all data, and perform most operations",
        "level": 10,
        "is_system": True,
        "is_default": False,
        "permissions": [
            "staff.user.view", "staff.user.create", "staff.user.edit",
            "staff.role.view", "staff.department.view", "staff.audit.view",
            "inventory.*", "service.*", "amc.*", "company.*", "reports.*"
        ]
    },
    {
        "name": "Technician",
        "description": "Field technician with access to assigned companies and tickets",
        "level": 50,
        "is_system": True,
        "is_default": False,
        "permissions": [
            "inventory.device.view", "inventory.device.edit",
            "service.ticket.view", "service.ticket.edit", "service.ticket.assign",
            "service.job.view", "service.job.create",
            "amc.contract.view"
        ]
    },
    {
        "name": "Support Agent",
        "description": "Handles tickets and customer support",
        "level": 60,
        "is_system": True,
        "is_default": False,
        "permissions": [
            "service.ticket.view", "service.ticket.create", "service.ticket.edit",
            "inventory.device.view",
            "company.company.view"
        ]
    },
    {
        "name": "Viewer",
        "description": "Read-only access to most data",
        "level": 90,
        "is_system": True,
        "is_default": True,
        "permissions": [
            "inventory.device.view", "service.ticket.view",
            "amc.contract.view", "company.company.view"
        ]
    }
]
