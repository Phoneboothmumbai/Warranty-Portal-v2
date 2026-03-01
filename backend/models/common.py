"""
Common/Master data models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from utils.helpers import get_ist_isoformat


class MasterItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # device_type, part_type, brand, service_type, condition, location, status
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None  # For hierarchical data like models under brands
    is_active: bool = True
    sort_order: int = 0
    created_at: str = Field(default_factory=get_ist_isoformat)


class MasterItemCreate(BaseModel):
    type: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class MasterItemUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str  # company, user, device, part, amc, service, master
    entity_id: str
    action: str  # create, update, delete, assign
    changes: dict  # {field: {old: x, new: y}}
    performed_by: str
    performed_by_name: str
    created_at: str = Field(default_factory=get_ist_isoformat)


class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "settings"
    logo_url: Optional[str] = None
    logo_base64: Optional[str] = None
    accent_color: str = "#0F62FE"
    company_name: str = "Warranty Portal"
    updated_at: str = Field(default_factory=get_ist_isoformat)


class SettingsUpdate(BaseModel):
    logo_url: Optional[str] = None
    logo_base64: Optional[str] = None
    accent_color: Optional[str] = None
    company_name: Optional[str] = None
    billing_emails: Optional[list] = None
