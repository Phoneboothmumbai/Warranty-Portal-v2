"""
Organization (Tenant) Model - Multi-tenancy foundation
======================================================
Each Organization is a tenant in the SaaS model.
Organizations can have multiple companies (for MSP model).
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from utils.helpers import get_ist_isoformat


# ==================== SUBSCRIPTION PLANS ====================

SUBSCRIPTION_PLANS = {
    "trial": {
        "name": "Trial",
        "price_monthly": 0,
        "price_yearly": 0,
        "limits": {
            "companies": 2,
            "devices": 50,
            "users": 5,
            "tickets_per_month": 100,
            "storage_gb": 1
        },
        "features": ["basic_ticketing", "device_management", "warranty_tracking"],
        "trial_days": 14
    },
    "starter": {
        "name": "Starter",
        "price_monthly": 2999,  # INR
        "price_yearly": 29990,  # ~2 months free
        "limits": {
            "companies": 5,
            "devices": 100,
            "users": 10,
            "tickets_per_month": 500,
            "storage_gb": 5
        },
        "features": ["basic_ticketing", "device_management", "warranty_tracking", "amc_management", "reports_basic"]
    },
    "professional": {
        "name": "Professional",
        "price_monthly": 7999,
        "price_yearly": 79990,
        "limits": {
            "companies": 25,
            "devices": 500,
            "users": 50,
            "tickets_per_month": 2000,
            "storage_gb": 25
        },
        "features": ["basic_ticketing", "device_management", "warranty_tracking", "amc_management", 
                     "reports_basic", "sla_management", "email_integration", "custom_forms", 
                     "api_access_basic", "reports_advanced"]
    },
    "enterprise": {
        "name": "Enterprise",
        "price_monthly": None,  # Custom pricing
        "price_yearly": None,
        "limits": {
            "companies": -1,  # Unlimited
            "devices": -1,
            "users": -1,
            "tickets_per_month": -1,
            "storage_gb": 100
        },
        "features": ["all"]  # All features
    }
}


# ==================== ORGANIZATION STATUS ====================

ORGANIZATION_STATUSES = [
    "trial",           # In trial period
    "active",          # Paid and active
    "past_due",        # Payment overdue
    "suspended",       # Temporarily suspended (non-payment)
    "cancelled",       # Cancelled by user
    "churned"          # Cancelled and data retention period ended
]


# ==================== ORGANIZATION MODEL ====================

class OrganizationBranding(BaseModel):
    """Custom branding settings for the organization"""
    logo_url: Optional[str] = None
    logo_base64: Optional[str] = None
    accent_color: str = "#0F62FE"
    company_name: Optional[str] = None  # Display name in portal
    favicon_url: Optional[str] = None
    custom_css: Optional[str] = None


class OrganizationSettings(BaseModel):
    """Organization-specific settings"""
    timezone: str = "Asia/Kolkata"
    date_format: str = "DD/MM/YYYY"
    currency: str = "INR"
    language: str = "en"
    
    # Email settings
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None  # Encrypted
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None  # Encrypted
    
    # Notification preferences
    notify_on_new_ticket: bool = True
    notify_on_ticket_reply: bool = True
    notify_on_sla_breach: bool = True
    
    # Feature toggles
    enable_public_portal: bool = True
    enable_qr_codes: bool = True
    enable_ai_features: bool = True
    enable_email_ticketing: bool = False


class OrganizationFeatureFlags(BaseModel):
    """Feature flags controlled by Platform Admin - controls what features are visible to tenant"""
    tactical_rmm: bool = False  # Tactical RMM integration - OFF by default
    white_labeling: bool = False  # Custom branding/white-label
    api_access: bool = False  # API access for integrations
    advanced_reports: bool = False  # Advanced reporting module
    sla_management: bool = False  # SLA management features
    custom_domains: bool = False  # Custom domain support
    email_integration: bool = False  # Email-to-ticket integration
    knowledge_base: bool = False  # Knowledge base module
    staff_module: bool = True  # Staff management module - ON by default


class OrganizationSubscription(BaseModel):
    """Subscription details for the organization"""
    plan: str = "trial"  # trial, starter, professional, enterprise
    status: str = "trial"  # trial, active, past_due, cancelled
    
    # Billing
    billing_cycle: str = "monthly"  # monthly, yearly
    current_period_start: Optional[str] = None
    current_period_end: Optional[str] = None
    trial_ends_at: Optional[str] = None
    
    # Payment
    payment_method_id: Optional[str] = None  # Stripe payment method
    stripe_customer_id: Optional[str] = None
    stripe_subscription_id: Optional[str] = None
    
    # Usage tracking
    companies_count: int = 0
    devices_count: int = 0
    users_count: int = 0
    tickets_this_month: int = 0
    storage_used_mb: int = 0
    
    # History
    plan_changed_at: Optional[str] = None
    cancelled_at: Optional[str] = None
    cancel_reason: Optional[str] = None


class Organization(BaseModel):
    """
    Organization (Tenant) - The top-level entity in multi-tenancy.
    Each organization can have multiple companies (client companies).
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic info
    name: str  # Organization name
    slug: str  # URL-safe identifier (e.g., "acme-corp")
    
    # Owner
    owner_user_id: str  # Admin who created this org
    owner_email: str
    
    # Status
    status: str = "trial"  # trial, active, past_due, suspended, cancelled, churned
    
    # Subscription & Billing
    subscription: OrganizationSubscription = Field(default_factory=OrganizationSubscription)
    
    # Branding
    branding: OrganizationBranding = Field(default_factory=OrganizationBranding)
    
    # Settings
    settings: OrganizationSettings = Field(default_factory=OrganizationSettings)
    
    # Contact
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    phone: Optional[str] = None
    
    # Metadata
    industry: Optional[str] = None  # IT Services, Manufacturing, etc.
    company_size: Optional[str] = None  # 1-10, 11-50, 51-200, 201-500, 500+
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    is_deleted: bool = False


class OrganizationCreate(BaseModel):
    """Create a new organization"""
    name: str
    slug: str  # Must be unique
    owner_email: str
    owner_name: str
    owner_password: str
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None


class OrganizationUpdate(BaseModel):
    """Update organization details"""
    name: Optional[str] = None
    billing_email: Optional[str] = None
    billing_address: Optional[str] = None
    phone: Optional[str] = None
    industry: Optional[str] = None
    company_size: Optional[str] = None
    branding: Optional[Dict[str, Any]] = None
    settings: Optional[Dict[str, Any]] = None


class OrganizationBrandingUpdate(BaseModel):
    """Update organization branding"""
    logo_url: Optional[str] = None
    logo_base64: Optional[str] = None
    accent_color: Optional[str] = None
    company_name: Optional[str] = None
    favicon_url: Optional[str] = None
    custom_css: Optional[str] = None
    custom_domain: Optional[str] = None
    support_email: Optional[str] = None
    footer_text: Optional[str] = None
    hide_powered_by: Optional[bool] = None


class OrganizationSettingsUpdate(BaseModel):
    """Update organization settings"""
    timezone: Optional[str] = None
    date_format: Optional[str] = None
    currency: Optional[str] = None
    language: Optional[str] = None
    email_from_name: Optional[str] = None
    email_from_address: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    imap_username: Optional[str] = None
    imap_password: Optional[str] = None
    notify_on_new_ticket: Optional[bool] = None
    notify_on_ticket_reply: Optional[bool] = None
    notify_on_sla_breach: Optional[bool] = None
    enable_public_portal: Optional[bool] = None
    enable_qr_codes: Optional[bool] = None
    enable_ai_features: Optional[bool] = None
    enable_email_ticketing: Optional[bool] = None


# ==================== ROLE SYSTEM (4-Level SaaS Architecture) ====================
# 
# Level 0: Platform (Super Admin) - Managed separately in platform_admins collection
# Level 1: Tenant (MSP) - msp_admin, msp_technician
# Level 2: Company (Client) - company_admin, company_employee
# Level 3: External - external_customer (limited access)
#
# This aligns with subdomain-based multi-tenancy:
# - Platform: app.aftersales.support
# - Tenants: {tenant}.aftersales.support
# - Companies: Managed within tenant workspace (no separate subdomain)

TENANT_ROLES = {
    "msp_admin": {
        "name": "MSP Admin",
        "level": 1,
        "description": "Full access to tenant workspace. Can manage all companies, users, and settings.",
        "permissions": ["all"],
        "can_switch_companies": True,
        "can_manage_companies": True,
        "can_manage_users": True,
        "can_manage_settings": True,
        "can_view_billing": True
    },
    "msp_technician": {
        "name": "MSP Technician",
        "level": 1,
        "description": "Access to assigned companies only. Can manage devices, tickets, and service.",
        "permissions": [
            "view_assigned_companies",
            "manage_devices",
            "manage_tickets",
            "manage_services",
            "view_amc",
            "manage_parts"
        ],
        "can_switch_companies": True,  # Only between assigned companies
        "can_manage_companies": False,
        "can_manage_users": False,
        "can_manage_settings": False,
        "can_view_billing": False
    },
    "company_admin": {
        "name": "Company Admin",
        "level": 2,
        "description": "Admin of a specific client company. Can manage company employees and view all company data.",
        "permissions": [
            "view_company",
            "manage_employees",
            "manage_tickets",
            "view_devices",
            "view_amc",
            "manage_company_settings"
        ],
        "can_switch_companies": False,  # Locked to their company
        "can_manage_companies": False,
        "can_manage_users": True,  # Only company employees
        "can_manage_settings": True,  # Only company settings
        "can_view_billing": False
    },
    "company_employee": {
        "name": "Company Employee",
        "level": 2,
        "description": "Regular employee of a client company. Can view devices and create tickets.",
        "permissions": [
            "view_company",
            "view_devices",
            "create_tickets",
            "view_own_tickets"
        ],
        "can_switch_companies": False,
        "can_manage_companies": False,
        "can_manage_users": False,
        "can_manage_settings": False,
        "can_view_billing": False
    },
    "external_customer": {
        "name": "External Customer",
        "level": 3,
        "description": "External end-user with minimal access. Can view warranty status and create support requests.",
        "permissions": [
            "view_warranty",
            "create_support_request"
        ],
        "can_switch_companies": False,
        "can_manage_companies": False,
        "can_manage_users": False,
        "can_manage_settings": False,
        "can_view_billing": False
    }
}

# Legacy role mapping (for backward compatibility)
LEGACY_ROLE_MAP = {
    "owner": "msp_admin",
    "admin": "msp_admin", 
    "member": "msp_technician",
    "readonly": "company_employee"
}


# ==================== ORGANIZATION MEMBER ====================

class OrganizationMember(BaseModel):
    """
    Users who belong to a tenant (MSP organization).
    Supports the 4-level SaaS architecture with role-based access.
    
    Roles:
    - msp_admin: Full tenant access
    - msp_technician: Access to assigned companies
    - company_admin: Admin of a specific company
    - company_employee: Regular company user
    - external_customer: Limited external access
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # The tenant (MSP) this user belongs to
    
    # User info
    email: str
    name: str
    password_hash: str
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Role within the organization (new 5-tier system)
    role: str = "company_employee"  # msp_admin, msp_technician, company_admin, company_employee, external_customer
    
    # Company assignment (for company_admin, company_employee, external_customer)
    # None = can access all companies (msp_admin/msp_technician)
    company_id: Optional[str] = None
    
    # For msp_technician: list of company IDs they are assigned to
    assigned_company_ids: List[str] = Field(default_factory=list)
    
    # Permissions (granular, overrides role defaults)
    permissions: List[str] = Field(default_factory=list)
    
    # Status
    is_active: bool = True
    is_deleted: bool = False
    
    # Audit
    last_login: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    invited_by: Optional[str] = None
    
    def get_effective_permissions(self) -> List[str]:
        """Get effective permissions based on role and custom permissions"""
        role_info = TENANT_ROLES.get(self.role, {})
        base_perms = role_info.get("permissions", [])
        if "all" in base_perms:
            return ["all"]
        # Merge role permissions with custom permissions
        return list(set(base_perms + self.permissions))
    
    def can_access_company(self, company_id: str) -> bool:
        """Check if user can access a specific company"""
        role_info = TENANT_ROLES.get(self.role, {})
        
        # MSP Admin can access all companies
        if self.role == "msp_admin":
            return True
        
        # MSP Technician can access assigned companies
        if self.role == "msp_technician":
            return company_id in self.assigned_company_ids
        
        # Company-level users can only access their company
        if self.company_id:
            return self.company_id == company_id
        
        return False


class OrganizationMemberCreate(BaseModel):
    """Create a new member in the organization"""
    email: str
    name: str
    password: Optional[str] = None  # Optional - can send invite instead
    role: str = "company_employee"  # msp_admin, msp_technician, company_admin, company_employee, external_customer
    company_id: Optional[str] = None  # Required for company-level roles
    assigned_company_ids: Optional[List[str]] = None  # For msp_technician
    permissions: Optional[List[str]] = None
    phone: Optional[str] = None


class OrganizationMemberUpdate(BaseModel):
    """Update member details"""
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    company_id: Optional[str] = None
    assigned_company_ids: Optional[List[str]] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


# ==================== ORGANIZATION INVITATION ====================

class OrganizationInvitation(BaseModel):
    """Pending invitation to join an organization"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    email: str
    role: str = "member"
    permissions: List[str] = Field(default_factory=list)
    
    # Invitation details
    invite_token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    invited_by: str  # Member ID who sent the invite
    invited_by_name: str
    
    # Status
    status: str = "pending"  # pending, accepted, expired, revoked
    expires_at: str  # 7 days from creation
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    accepted_at: Optional[str] = None


# ==================== USAGE TRACKING ====================

class OrganizationUsageLog(BaseModel):
    """Track usage for billing and limits"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Period
    period_start: str  # First day of month
    period_end: str    # Last day of month
    
    # Counts
    companies_count: int = 0
    devices_count: int = 0
    users_count: int = 0
    tickets_created: int = 0
    storage_used_mb: int = 0
    api_calls: int = 0
    
    # Features used
    ai_queries: int = 0
    emails_sent: int = 0
    emails_received: int = 0
    
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
