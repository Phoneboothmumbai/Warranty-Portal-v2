"""
Platform Admin Model - Super Admin for SaaS Platform
=====================================================
Platform admins manage the entire SaaS platform.
They are separate from organization (tenant) admins.
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from utils.helpers import get_ist_isoformat


class PlatformAdmin(BaseModel):
    """
    Platform-level super admin.
    These users manage the entire SaaS platform, not tied to any tenant.
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    password_hash: str
    
    # Role within platform
    role: str = "platform_admin"  # platform_owner, platform_admin, platform_support
    
    # Permissions
    permissions: List[str] = Field(default_factory=lambda: [
        "view_organizations",
        "manage_organizations",
        "view_billing",
        "manage_billing",
        "platform_settings"
    ])
    
    # Status
    is_active: bool = True
    is_deleted: bool = False
    
    # Audit
    last_login: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None  # Who created this admin


class PlatformAdminCreate(BaseModel):
    """Create a new platform admin"""
    email: str
    name: str
    password: str
    role: str = "platform_admin"


class PlatformAdminUpdate(BaseModel):
    """Update platform admin"""
    name: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


class PlatformLogin(BaseModel):
    """Platform admin login"""
    email: str
    password: str


class PlatformSettings(BaseModel):
    """Platform-wide settings"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = "platform_settings"
    
    # Platform branding
    platform_name: str = "Warranty Portal SaaS"
    platform_logo_url: Optional[str] = None
    support_email: str = "support@yourplatform.com"
    
    # Trial settings
    trial_days: int = 14
    trial_plan: str = "trial"
    
    # Self-signup
    allow_self_signup: bool = True
    require_email_verification: bool = True
    
    # Default limits for new tenants
    default_plan: str = "trial"
    
    # Feature flags
    maintenance_mode: bool = False
    maintenance_message: Optional[str] = None
    
    # Analytics
    enable_analytics: bool = True
    
    updated_at: str = Field(default_factory=get_ist_isoformat)
    updated_by: Optional[str] = None


class PlatformSettingsUpdate(BaseModel):
    """Update platform settings"""
    platform_name: Optional[str] = None
    platform_logo_url: Optional[str] = None
    support_email: Optional[str] = None
    trial_days: Optional[int] = None
    allow_self_signup: Optional[bool] = None
    require_email_verification: Optional[bool] = None
    default_plan: Optional[str] = None
    maintenance_mode: Optional[bool] = None
    maintenance_message: Optional[str] = None


# Platform-level audit log
class PlatformAuditLog(BaseModel):
    """Audit log for platform-level actions"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Action details
    action: str  # create_org, suspend_org, update_billing, etc.
    entity_type: str  # organization, platform_admin, billing
    entity_id: str
    
    # Changes
    changes: dict = Field(default_factory=dict)
    
    # Who did it
    performed_by: str  # Platform admin ID
    performed_by_name: str
    performed_by_email: str
    
    # When
    created_at: str = Field(default_factory=get_ist_isoformat)
    
    # Additional context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
