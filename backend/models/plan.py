"""
Plan Management Model
=====================
Dynamic, config-driven subscription plans for the SaaS platform.
Supports versioning, feature flags, and usage limits.
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


def get_ist_isoformat():
    return datetime.utcnow().isoformat() + "Z"


# Default feature flags template
DEFAULT_FEATURE_FLAGS = {
    "ticketing": True,
    "device_management": True,
    "warranty_tracking": True,
    "amc_management": False,
    "sla_management": False,
    "email_integration": False,
    "api_access": False,
    "custom_forms": False,
    "knowledge_base": False,
    "reports_basic": True,
    "reports_advanced": False,
    "white_labeling": False,
    "custom_domain": False,
    "sso_integration": False,
    "priority_support": False,
    "dedicated_support": False,
    "ai_features": False,
    "bulk_import": True,
    "export_data": True,
    "audit_logs": False,
    "multi_department": False,
    "custom_workflows": False,
}

# Default usage limits template
DEFAULT_USAGE_LIMITS = {
    "max_companies": 2,
    "max_devices": 50,
    "max_users": 5,
    "max_tickets_per_month": 100,
    "max_storage_gb": 1,
    "max_email_templates": 5,
    "max_custom_fields": 10,
    "max_departments": 1,
    "max_sla_policies": 0,
    "max_canned_responses": 10,
    "max_knowledge_articles": 20,
}


class Plan(BaseModel):
    """
    Subscription plan model with feature flags and usage limits.
    Supports versioning for grandfathering existing customers.
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic info
    name: str
    slug: str  # URL-friendly identifier
    description: str = ""
    tagline: str = ""  # Short description for cards
    
    # Pricing
    price_monthly: int = 0  # In smallest currency unit (paise for INR)
    price_yearly: int = 0
    currency: str = "INR"
    billing_period: str = "monthly"  # monthly, yearly, one_time
    
    # Display
    display_order: int = 0  # For ordering on pricing page
    is_popular: bool = False  # Show "Most Popular" badge
    is_public: bool = True  # Show on public pricing page
    color: str = "#6366f1"  # Accent color for the plan card
    
    # Status
    status: str = "active"  # active, draft, archived
    
    # Feature flags (what features are enabled)
    features: Dict[str, bool] = Field(default_factory=lambda: DEFAULT_FEATURE_FLAGS.copy())
    
    # Usage limits (how much of each feature)
    limits: Dict[str, int] = Field(default_factory=lambda: DEFAULT_USAGE_LIMITS.copy())
    
    # Support configuration
    support_level: str = "community"  # community, email, priority, dedicated
    response_time_hours: Optional[int] = None  # SLA response time
    
    # Trial settings
    is_trial: bool = False
    trial_days: int = 0
    
    # Versioning
    version: int = 1
    parent_version_id: Optional[str] = None  # Reference to previous version
    
    # Usage tracking
    used_by_count: int = 0  # Number of organizations using this plan
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None
    
    # Soft delete
    is_deleted: bool = False
    deleted_at: Optional[str] = None
    deleted_by: Optional[str] = None


class PlanCreate(BaseModel):
    """Create a new plan"""
    name: str
    slug: str
    description: Optional[str] = ""
    tagline: Optional[str] = ""
    price_monthly: int = 0
    price_yearly: int = 0
    currency: str = "INR"
    display_order: Optional[int] = 0
    is_popular: Optional[bool] = False
    is_public: Optional[bool] = True
    color: Optional[str] = "#6366f1"
    status: Optional[str] = "draft"
    features: Optional[Dict[str, bool]] = None
    limits: Optional[Dict[str, int]] = None
    support_level: Optional[str] = "community"
    response_time_hours: Optional[int] = None
    is_trial: Optional[bool] = False
    trial_days: Optional[int] = 0


class PlanUpdate(BaseModel):
    """Update an existing plan"""
    name: Optional[str] = None
    description: Optional[str] = None
    tagline: Optional[str] = None
    price_monthly: Optional[int] = None
    price_yearly: Optional[int] = None
    currency: Optional[str] = None
    display_order: Optional[int] = None
    is_popular: Optional[bool] = None
    is_public: Optional[bool] = None
    color: Optional[str] = None
    status: Optional[str] = None
    features: Optional[Dict[str, bool]] = None
    limits: Optional[Dict[str, int]] = None
    support_level: Optional[str] = None
    response_time_hours: Optional[int] = None
    is_trial: Optional[bool] = None
    trial_days: Optional[int] = None


class PlanReorder(BaseModel):
    """Reorder plans"""
    plan_ids: List[str]  # Ordered list of plan IDs


# Feature metadata for UI display
FEATURE_METADATA = {
    "ticketing": {"name": "Support Ticketing", "category": "Core", "description": "Create and manage support tickets"},
    "device_management": {"name": "Device Management", "category": "Core", "description": "Track and manage devices"},
    "warranty_tracking": {"name": "Warranty Tracking", "category": "Core", "description": "Track warranty status and expiry"},
    "amc_management": {"name": "AMC Management", "category": "Service", "description": "Annual maintenance contracts"},
    "sla_management": {"name": "SLA Management", "category": "Service", "description": "Service level agreements with breach alerts"},
    "email_integration": {"name": "Email Integration", "category": "Integration", "description": "Send/receive emails from tickets"},
    "api_access": {"name": "API Access", "category": "Integration", "description": "REST API for integrations"},
    "custom_forms": {"name": "Custom Forms", "category": "Advanced", "description": "Dynamic forms per ticket type"},
    "knowledge_base": {"name": "Knowledge Base", "category": "Advanced", "description": "Self-service articles"},
    "reports_basic": {"name": "Basic Reports", "category": "Reporting", "description": "Standard dashboards and reports"},
    "reports_advanced": {"name": "Advanced Reports", "category": "Reporting", "description": "Custom reports and analytics"},
    "white_labeling": {"name": "White Labeling", "category": "Branding", "description": "Custom branding and colors"},
    "custom_domain": {"name": "Custom Domain", "category": "Branding", "description": "Use your own domain"},
    "sso_integration": {"name": "SSO Integration", "category": "Security", "description": "Single sign-on support"},
    "priority_support": {"name": "Priority Support", "category": "Support", "description": "Faster response times"},
    "dedicated_support": {"name": "Dedicated Support", "category": "Support", "description": "Dedicated account manager"},
    "ai_features": {"name": "AI Features", "category": "Advanced", "description": "AI-powered ticket triage and summaries"},
    "bulk_import": {"name": "Bulk Import", "category": "Data", "description": "Import data from CSV/Excel"},
    "export_data": {"name": "Export Data", "category": "Data", "description": "Export your data"},
    "audit_logs": {"name": "Audit Logs", "category": "Security", "description": "Track all user actions"},
    "multi_department": {"name": "Multi-Department", "category": "Organization", "description": "Multiple departments support"},
    "custom_workflows": {"name": "Custom Workflows", "category": "Advanced", "description": "Automated ticket workflows"},
}

LIMIT_METADATA = {
    "max_companies": {"name": "Client Companies", "unit": "companies", "description": "Maximum client companies"},
    "max_devices": {"name": "Devices", "unit": "devices", "description": "Maximum tracked devices"},
    "max_users": {"name": "Team Members", "unit": "users", "description": "Maximum team members"},
    "max_tickets_per_month": {"name": "Tickets/Month", "unit": "tickets", "description": "Monthly ticket limit"},
    "max_storage_gb": {"name": "Storage", "unit": "GB", "description": "File storage limit"},
    "max_email_templates": {"name": "Email Templates", "unit": "templates", "description": "Custom email templates"},
    "max_custom_fields": {"name": "Custom Fields", "unit": "fields", "description": "Custom ticket fields"},
    "max_departments": {"name": "Departments", "unit": "departments", "description": "Maximum departments"},
    "max_sla_policies": {"name": "SLA Policies", "unit": "policies", "description": "SLA policy limit"},
    "max_canned_responses": {"name": "Canned Responses", "unit": "responses", "description": "Quick reply templates"},
    "max_knowledge_articles": {"name": "KB Articles", "unit": "articles", "description": "Knowledge base articles"},
}


# Default plans to seed
DEFAULT_PLANS = [
    {
        "name": "Free Trial",
        "slug": "free-trial",
        "tagline": "Try all features free for 14 days",
        "description": "Perfect for evaluating the platform before committing",
        "price_monthly": 0,
        "price_yearly": 0,
        "display_order": 0,
        "is_trial": True,
        "trial_days": 14,
        "status": "active",
        "is_public": True,
        "color": "#64748b",
        "support_level": "community",
        "features": {
            **DEFAULT_FEATURE_FLAGS,
            "ticketing": True,
            "device_management": True,
            "warranty_tracking": True,
            "reports_basic": True,
            "bulk_import": True,
            "export_data": True,
        },
        "limits": {
            "max_companies": 2,
            "max_devices": 50,
            "max_users": 5,
            "max_tickets_per_month": 100,
            "max_storage_gb": 1,
            "max_email_templates": 5,
            "max_custom_fields": 5,
            "max_departments": 1,
            "max_sla_policies": 0,
            "max_canned_responses": 10,
            "max_knowledge_articles": 10,
        }
    },
    {
        "name": "Starter",
        "slug": "starter",
        "tagline": "For small IT teams",
        "description": "Everything you need to get started with IT service management",
        "price_monthly": 299900,  # ₹2,999 in paise
        "price_yearly": 2999000,  # ₹29,990 in paise
        "display_order": 1,
        "status": "active",
        "is_public": True,
        "color": "#3b82f6",
        "support_level": "email",
        "response_time_hours": 24,
        "features": {
            **DEFAULT_FEATURE_FLAGS,
            "ticketing": True,
            "device_management": True,
            "warranty_tracking": True,
            "amc_management": True,
            "sla_management": True,
            "email_integration": True,
            "api_access": True,
            "reports_basic": True,
            "bulk_import": True,
            "export_data": True,
        },
        "limits": {
            "max_companies": 5,
            "max_devices": 100,
            "max_users": 10,
            "max_tickets_per_month": 500,
            "max_storage_gb": 5,
            "max_email_templates": 10,
            "max_custom_fields": 20,
            "max_departments": 3,
            "max_sla_policies": 3,
            "max_canned_responses": 25,
            "max_knowledge_articles": 50,
        }
    },
    {
        "name": "Professional",
        "slug": "professional",
        "tagline": "For growing businesses",
        "description": "Advanced features for scaling your IT operations",
        "price_monthly": 799900,  # ₹7,999 in paise
        "price_yearly": 7999000,  # ₹79,990 in paise
        "display_order": 2,
        "is_popular": True,
        "status": "active",
        "is_public": True,
        "color": "#8b5cf6",
        "support_level": "priority",
        "response_time_hours": 8,
        "features": {
            **DEFAULT_FEATURE_FLAGS,
            "ticketing": True,
            "device_management": True,
            "warranty_tracking": True,
            "amc_management": True,
            "sla_management": True,
            "email_integration": True,
            "api_access": True,
            "custom_forms": True,
            "knowledge_base": True,
            "reports_basic": True,
            "reports_advanced": True,
            "white_labeling": True,
            "ai_features": True,
            "bulk_import": True,
            "export_data": True,
            "audit_logs": True,
            "multi_department": True,
        },
        "limits": {
            "max_companies": 25,
            "max_devices": 500,
            "max_users": 50,
            "max_tickets_per_month": 2000,
            "max_storage_gb": 25,
            "max_email_templates": 50,
            "max_custom_fields": 50,
            "max_departments": 10,
            "max_sla_policies": 10,
            "max_canned_responses": 100,
            "max_knowledge_articles": 200,
        }
    },
    {
        "name": "Enterprise",
        "slug": "enterprise",
        "tagline": "For large organizations",
        "description": "Unlimited everything with dedicated support and custom SLAs",
        "price_monthly": 0,  # Custom pricing
        "price_yearly": 0,
        "display_order": 3,
        "status": "active",
        "is_public": True,
        "color": "#0f172a",
        "support_level": "dedicated",
        "response_time_hours": 4,
        "features": {
            key: True for key in DEFAULT_FEATURE_FLAGS.keys()
        },
        "limits": {
            "max_companies": -1,  # -1 = unlimited
            "max_devices": -1,
            "max_users": -1,
            "max_tickets_per_month": -1,
            "max_storage_gb": -1,
            "max_email_templates": -1,
            "max_custom_fields": -1,
            "max_departments": -1,
            "max_sla_policies": -1,
            "max_canned_responses": -1,
            "max_knowledge_articles": -1,
        }
    }
]
