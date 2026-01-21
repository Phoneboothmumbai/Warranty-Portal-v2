"""
Device and Parts related models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from utils.helpers import get_ist_isoformat


class ConsumableItem(BaseModel):
    """Individual consumable item for a device (e.g., one color toner)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Black Toner", "Cyan Ink"
    consumable_type: str  # Toner Cartridge, Ink Cartridge, Drum, etc.
    model_number: str  # e.g., HP 26A, Canon 325
    brand: Optional[str] = None
    color: Optional[str] = None  # Black, Cyan, Magenta, Yellow, etc.
    notes: Optional[str] = None


class Device(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    assigned_user_id: Optional[str] = None
    assigned_employee_id: Optional[str] = None  # NEW: Employee from company_employees
    device_type: str
    brand: str
    model: str
    serial_number: str
    asset_tag: Optional[str] = None
    purchase_date: str
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    location: Optional[str] = None
    condition: str = "good"
    status: str = "active"
    notes: Optional[str] = None
    # NEW: Configuration details for Laptops/Desktops/Tablets
    configuration: Optional[str] = None
    # Deployment source tracking
    source: str = "manual"
    deployment_id: Optional[str] = None
    deployment_item_index: Optional[int] = None
    site_id: Optional[str] = None
    # Consumable details (for printers, etc.) - Legacy single consumable
    consumable_type: Optional[str] = None
    consumable_model: Optional[str] = None
    consumable_brand: Optional[str] = None
    consumable_notes: Optional[str] = None
    # NEW: Multiple consumables support
    consumables: List[dict] = Field(default_factory=list)
    # NEW: Device-specific credentials and access details
    credentials: Optional[dict] = None  # Stores type-specific access info
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class DeviceCreate(BaseModel):
    company_id: str
    assigned_user_id: Optional[str] = None
    assigned_employee_id: Optional[str] = None  # NEW: Employee from company_employees
    device_type: str
    brand: str
    model: str
    serial_number: str
    asset_tag: Optional[str] = None
    purchase_date: str
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    location: Optional[str] = None
    condition: str = "good"
    status: str = "active"
    notes: Optional[str] = None
    # NEW: Configuration details for Laptops/Desktops/Tablets
    configuration: Optional[str] = None
    # Deployment source tracking
    source: str = "manual"
    deployment_id: Optional[str] = None
    deployment_item_index: Optional[int] = None
    site_id: Optional[str] = None
    # Consumable details (for printers, etc.) - Legacy
    consumable_type: Optional[str] = None
    consumable_model: Optional[str] = None
    consumable_brand: Optional[str] = None
    consumable_notes: Optional[str] = None
    # NEW: Multiple consumables
    consumables: Optional[List[dict]] = None
    # NEW: Device-specific credentials
    credentials: Optional[dict] = None


class DeviceUpdate(BaseModel):
    company_id: Optional[str] = None
    assigned_user_id: Optional[str] = None
    assigned_employee_id: Optional[str] = None  # NEW: Employee from company_employees
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    asset_tag: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    # NEW: Configuration details for Laptops/Desktops/Tablets
    configuration: Optional[str] = None
    site_id: Optional[str] = None
    # Consumable details - Legacy
    consumable_type: Optional[str] = None
    consumable_model: Optional[str] = None
    consumable_brand: Optional[str] = None
    consumable_notes: Optional[str] = None
    # NEW: Multiple consumables
    consumables: Optional[List[dict]] = None
    # NEW: Device-specific credentials
    credentials: Optional[dict] = None


class AssignmentHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    from_user_id: Optional[str] = None
    to_user_id: Optional[str] = None
    from_user_name: Optional[str] = None
    to_user_name: Optional[str] = None
    reason: Optional[str] = None
    changed_by: str
    changed_by_name: str
    created_at: str = Field(default_factory=get_ist_isoformat)


class Part(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    part_name: str
    serial_number: Optional[str] = None
    replaced_date: str
    warranty_months: int
    warranty_expiry_date: str
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class PartCreate(BaseModel):
    device_id: str
    part_name: str
    serial_number: Optional[str] = None
    replaced_date: str
    warranty_months: int
    notes: Optional[str] = None


class PartUpdate(BaseModel):
    part_name: Optional[str] = None
    serial_number: Optional[str] = None
    replaced_date: Optional[str] = None
    warranty_months: Optional[int] = None
    notes: Optional[str] = None


class ConsumableOrderItem(BaseModel):
    """Individual item in a consumable order"""
    consumable_id: str
    name: str
    consumable_type: str
    model_number: str
    brand: Optional[str] = None
    color: Optional[str] = None
    quantity: int = 1


class ConsumableOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = Field(default_factory=lambda: f"ORD-{__import__('utils.helpers', fromlist=['get_ist_now']).get_ist_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    company_id: str
    device_id: str
    requested_by: str
    requested_by_name: str
    requested_by_email: str
    # Legacy single consumable fields
    consumable_type: Optional[str] = None
    consumable_model: Optional[str] = None
    quantity: int = 1
    # NEW: Multiple items support
    items: List[dict] = Field(default_factory=list)
    notes: Optional[str] = None
    status: str = "pending"
    osticket_id: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
