"""
TGMS Integration Models
==============================
Multi-tenant TGMS configuration with white-label support.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict
from utils.helpers import get_ist_isoformat


class TGMSBranding(BaseModel):
    """White-label branding configuration for TGMS"""
    title: str = "Remote Management"
    title2: str = "IT Support Portal"
    welcome_text: str = "Welcome to Remote Support"
    logo_url: Optional[str] = None
    login_background_url: Optional[str] = None
    favicon_url: Optional[str] = None
    primary_color: str = "#0F62FE"
    background_color: str = "#1a1a2e"
    night_mode: bool = True
    
    # Agent customization
    agent_display_name: str = "Support Agent"
    agent_description: str = "Remote Support Agent"
    agent_company_name: str = "IT Support"
    agent_service_name: str = "SupportAgent"
    agent_icon_url: Optional[str] = None
    agent_foreground_color: str = "#FFFFFF"
    agent_background_color: str = "#0F62FE"


class TGMSConfig(BaseModel):
    """TGMS configuration for a tenant"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    
    # Connection settings
    server_url: str = ""  # e.g., https://rmm.example.com
    username: str = ""
    password_encrypted: str = ""  # Encrypted password
    api_token: Optional[str] = None  # Alternative to user/pass
    
    # Feature toggles
    is_enabled: bool = False
    sync_devices: bool = True  # Auto-sync devices to portal
    allow_remote_desktop: bool = True
    allow_remote_terminal: bool = True
    allow_file_transfer: bool = True
    
    # Domain/Group mapping
    mesh_domain: str = ""  # TGMS domain for this tenant
    device_group_id: Optional[str] = None  # TGMS device group
    
    # White-label branding
    branding: TGMSBranding = Field(default_factory=TGMSBranding)
    
    # Sync status
    last_sync_at: Optional[str] = None
    last_sync_status: str = "never"  # never, success, failed
    last_sync_error: Optional[str] = None
    device_count: int = 0
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: Optional[str] = None
    updated_by_id: Optional[str] = None


class TGMSConfigCreate(BaseModel):
    """Create TGMS configuration"""
    server_url: str
    username: Optional[str] = None
    password: Optional[str] = None
    api_token: Optional[str] = None
    mesh_domain: Optional[str] = None


class TGMSConfigUpdate(BaseModel):
    """Update TGMS configuration"""
    server_url: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_token: Optional[str] = None
    is_enabled: Optional[bool] = None
    sync_devices: Optional[bool] = None
    allow_remote_desktop: Optional[bool] = None
    allow_remote_terminal: Optional[bool] = None
    allow_file_transfer: Optional[bool] = None
    mesh_domain: Optional[str] = None
    device_group_id: Optional[str] = None
    branding: Optional[Dict[str, Any]] = None


class TGMSDevice(BaseModel):
    """Device from TGMS"""
    id: str  # TGMS node ID
    name: str
    host: Optional[str] = None
    os: Optional[str] = None
    agent_version: Optional[str] = None
    last_connect: Optional[str] = None
    ip_addresses: List[str] = Field(default_factory=list)
    is_online: bool = False
    
    # Mapping to portal
    portal_device_id: Optional[str] = None  # Linked device in our system
    organization_id: Optional[str] = None


class TGMSSession(BaseModel):
    """Active remote session"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    device_id: str
    device_name: str
    session_type: str  # desktop, terminal, files
    started_at: str = Field(default_factory=get_ist_isoformat)
    started_by_id: str
    started_by_name: str
    mesh_session_id: Optional[str] = None
    status: str = "active"  # active, ended
    ended_at: Optional[str] = None


class AgentDownloadInfo(BaseModel):
    """Agent download information"""
    platform: str  # windows, linux, macos
    architecture: str  # x64, x86, arm64
    download_url: str
    filename: str
    instructions: str
