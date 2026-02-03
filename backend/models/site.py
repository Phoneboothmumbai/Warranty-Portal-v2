"""
Site and Deployment related models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from utils.helpers import get_ist_isoformat


class Site(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None  # Tenant scoping - links to organization
    company_id: str
    name: str
    site_type: str = "office"
    address: Optional[str] = None
    city: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class SiteCreate(BaseModel):
    company_id: str
    name: str
    site_type: str = "office"
    address: Optional[str] = None
    city: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    site_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None


class DeploymentItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_type: str
    category: str
    brand: Optional[str] = None
    model: Optional[str] = None
    quantity: int = 1
    is_serialized: bool = False
    serial_numbers: List[str] = []
    zone_location: Optional[str] = None
    installation_date: Optional[str] = None
    warranty_start_date: Optional[str] = None
    warranty_end_date: Optional[str] = None
    warranty_type: Optional[str] = None
    amc_contract_id: Optional[str] = None
    notes: Optional[str] = None
    linked_device_ids: List[str] = []


class Deployment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    site_id: str
    name: str
    deployment_date: str
    installed_by: Optional[str] = None
    notes: Optional[str] = None
    items: List[dict] = []
    is_deleted: bool = False
    created_by: str
    created_by_name: str
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class DeploymentCreate(BaseModel):
    company_id: str
    site_id: str
    name: str
    deployment_date: str
    installed_by: Optional[str] = None
    notes: Optional[str] = None
    items: List[dict] = []


class DeploymentUpdate(BaseModel):
    name: Optional[str] = None
    deployment_date: Optional[str] = None
    installed_by: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[dict]] = None
