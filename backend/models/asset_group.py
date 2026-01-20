"""
Asset Groups & Accessories Models
- Asset Groups: Bundle related devices together (CCTV System, Workstation, etc.)
- Accessories: Track peripherals like keyboards, mice, cables
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid


def get_ist_isoformat() -> str:
    from datetime import timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).isoformat()


# ==================== ASSET GROUPS ====================

class AssetGroup(BaseModel):
    """Group related devices together (e.g., CCTV System, Workstation)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    name: str  # e.g., "CCTV System - Floor 1", "Workstation - John"
    description: Optional[str] = None
    group_type: str = "custom"  # cctv_system, workstation, server_rack, network_setup, custom
    
    # Primary device (main device in the group)
    primary_device_id: Optional[str] = None
    
    # List of device IDs in this group
    device_ids: List[str] = []
    
    # List of accessory IDs in this group
    accessory_ids: List[str] = []
    
    # Location
    site_id: Optional[str] = None
    location: Optional[str] = None
    
    # Metadata
    tags: List[str] = []
    notes: Optional[str] = None
    
    # Status
    status: str = "active"  # active, inactive, archived
    is_deleted: bool = False
    
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: Optional[str] = None


class AssetGroupCreate(BaseModel):
    company_id: str
    name: str
    description: Optional[str] = None
    group_type: str = "custom"
    primary_device_id: Optional[str] = None
    device_ids: List[str] = []
    accessory_ids: List[str] = []
    site_id: Optional[str] = None
    location: Optional[str] = None
    tags: List[str] = []
    notes: Optional[str] = None


class AssetGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    group_type: Optional[str] = None
    primary_device_id: Optional[str] = None
    device_ids: Optional[List[str]] = None
    accessory_ids: Optional[List[str]] = None
    site_id: Optional[str] = None
    location: Optional[str] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    status: Optional[str] = None


# ==================== ACCESSORIES ====================

class Accessory(BaseModel):
    """Track peripherals and accessories (keyboards, mice, cables, etc.)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    
    # Basic info
    name: str  # e.g., "Logitech Wireless Keyboard"
    accessory_type: str  # keyboard, mouse, headset, webcam, cable, adapter, monitor_stand, etc.
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    
    # Assignment
    assigned_employee_id: Optional[str] = None
    assigned_device_id: Optional[str] = None  # Can be linked to a device
    assigned_group_id: Optional[str] = None  # Can be part of an asset group
    
    # Purchase & Warranty
    purchase_date: Optional[str] = None
    purchase_price: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    
    # Status & Condition
    status: str = "available"  # available, assigned, in_repair, disposed
    condition: str = "good"  # new, good, fair, poor
    
    # Location
    site_id: Optional[str] = None
    location: Optional[str] = None
    
    # Quantity (for bulk items like cables)
    quantity: int = 1
    
    # Metadata
    notes: Optional[str] = None
    is_deleted: bool = False
    
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: Optional[str] = None


class AccessoryCreate(BaseModel):
    company_id: str
    name: str
    accessory_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    assigned_employee_id: Optional[str] = None
    assigned_device_id: Optional[str] = None
    assigned_group_id: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_price: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    status: str = "available"
    condition: str = "good"
    site_id: Optional[str] = None
    location: Optional[str] = None
    quantity: int = 1
    notes: Optional[str] = None


class AccessoryUpdate(BaseModel):
    name: Optional[str] = None
    accessory_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    assigned_employee_id: Optional[str] = None
    assigned_device_id: Optional[str] = None
    assigned_group_id: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_price: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    status: Optional[str] = None
    condition: Optional[str] = None
    site_id: Optional[str] = None
    location: Optional[str] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None
