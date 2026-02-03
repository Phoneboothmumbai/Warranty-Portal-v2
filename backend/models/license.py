"""
License related models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from utils.helpers import get_ist_isoformat


class License(BaseModel):
    """Software License entity for tracking software assets and renewals"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None  # Tenant scoping - links to organization
    company_id: str
    software_name: str
    vendor: Optional[str] = None
    license_type: str = "subscription"
    license_key: Optional[str] = None
    seats: int = 1
    assigned_to_type: str = "company"
    assigned_device_ids: List[str] = []
    assigned_user_ids: List[str] = []
    start_date: str
    end_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    renewal_cost: Optional[float] = None
    auto_renew: bool = False
    renewal_reminder_days: int = 30
    status: str = "active"
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class LicenseCreate(BaseModel):
    company_id: str
    software_name: str
    vendor: Optional[str] = None
    license_type: str = "subscription"
    license_key: Optional[str] = None
    seats: int = 1
    assigned_to_type: str = "company"
    assigned_device_ids: List[str] = []
    assigned_user_ids: List[str] = []
    start_date: str
    end_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    renewal_cost: Optional[float] = None
    auto_renew: bool = False
    renewal_reminder_days: int = 30
    notes: Optional[str] = None


class LicenseUpdate(BaseModel):
    software_name: Optional[str] = None
    vendor: Optional[str] = None
    license_type: Optional[str] = None
    license_key: Optional[str] = None
    seats: Optional[int] = None
    assigned_to_type: Optional[str] = None
    assigned_device_ids: Optional[List[str]] = None
    assigned_user_ids: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    renewal_cost: Optional[float] = None
    auto_renew: Optional[bool] = None
    renewal_reminder_days: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None
