"""
Office Supplies related models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from utils.helpers import get_ist_isoformat, get_ist_now


class SupplyCategory(BaseModel):
    """Category for office supplies (Stationery, Consumables, IT/Misc)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class SupplyCategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0


class SupplyCategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class SupplyProduct(BaseModel):
    """Product within a supply category"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category_id: str
    name: str
    description: Optional[str] = None
    unit: str = "piece"
    price: Optional[float] = None  # Price per unit
    image_url: Optional[str] = None  # Product image URL
    sku: Optional[str] = None  # Stock Keeping Unit
    internal_notes: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class SupplyProductCreate(BaseModel):
    category_id: str
    name: str
    description: Optional[str] = None
    unit: str = "piece"
    price: Optional[float] = None
    image_url: Optional[str] = None
    sku: Optional[str] = None
    internal_notes: Optional[str] = None


class SupplyProductUpdate(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = None
    image_url: Optional[str] = None
    sku: Optional[str] = None
    internal_notes: Optional[str] = None
    is_active: Optional[bool] = None


class SupplyOrderItem(BaseModel):
    """Individual item in a supply order"""
    product_id: str
    product_name: str
    category_name: str
    quantity: int
    unit: str


class SupplyOrderLocation(BaseModel):
    """Delivery location for supply order"""
    type: str = "existing"
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None


class SupplyOrder(BaseModel):
    """Office supplies order"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = Field(default_factory=lambda: f"SUP-{get_ist_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    company_id: str
    company_name: str
    requested_by: str
    requested_by_name: str
    requested_by_email: str
    requested_by_phone: Optional[str] = None
    delivery_location: dict
    items: List[dict]
    notes: Optional[str] = None
    status: str = "requested"
    osticket_id: Optional[str] = None
    admin_notes: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
