"""
Vendor Models
=============
Vendor/Supplier management and item-vendor price mappings.
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from utils.helpers import get_ist_isoformat


class VendorMaster(BaseModel):
    """Vendor/Supplier definition"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # Vendor identification
    name: str  # e.g., "ABC Supplies Pvt Ltd"
    code: Optional[str] = None  # Short code like "ABC-01"
    vendor_type: str = "supplier"  # supplier, manufacturer, distributor, oem
    
    # Contact information
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_mobile: Optional[str] = None
    
    # Address
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    country: str = "India"
    
    # Business details
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    
    # Banking
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    
    # Payment terms
    payment_terms: str = "net_30"  # immediate, net_15, net_30, net_45, net_60
    credit_limit: float = 0
    credit_days: int = 30
    
    # Rating/Performance
    rating: int = 3  # 1-5 star rating
    notes: Optional[str] = None
    
    # Preferred vendor for categories
    preferred_categories: List[str] = Field(default_factory=list)
    
    # Flags
    is_active: bool = True
    is_verified: bool = False
    is_deleted: bool = False
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None


class VendorMasterCreate(BaseModel):
    """Create a new vendor"""
    name: str
    code: Optional[str] = None
    vendor_type: str = "supplier"
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    payment_terms: str = "net_30"
    credit_limit: float = 0
    credit_days: int = 30
    preferred_categories: Optional[List[str]] = None


class VendorMasterUpdate(BaseModel):
    """Update vendor"""
    name: Optional[str] = None
    code: Optional[str] = None
    vendor_type: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_mobile: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    bank_ifsc: Optional[str] = None
    payment_terms: Optional[str] = None
    credit_limit: Optional[float] = None
    credit_days: Optional[int] = None
    rating: Optional[int] = None
    notes: Optional[str] = None
    preferred_categories: Optional[List[str]] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None


class VendorItemMapping(BaseModel):
    """
    Mapping between Vendor and Items with pricing.
    One item can have multiple vendors with different prices.
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # References
    vendor_id: str  # Reference to VendorMaster
    item_id: str    # Reference to ItemMaster
    
    # Denormalized names for quick lookup
    vendor_name: str
    item_name: str
    
    # Vendor's part number (may differ from our SKU)
    vendor_sku: Optional[str] = None
    vendor_part_number: Optional[str] = None
    
    # Pricing
    unit_price: float = 0  # Purchase price from this vendor
    currency: str = "INR"
    min_order_quantity: int = 1
    
    # Lead time
    lead_time_days: int = 0
    
    # Priority (lower = preferred)
    priority: int = 1  # 1 = primary vendor, 2 = secondary, etc.
    
    # Contract/Agreement
    contract_start: Optional[str] = None
    contract_end: Optional[str] = None
    contract_reference: Optional[str] = None
    
    # Flags
    is_preferred: bool = False  # Preferred vendor for this item
    is_active: bool = True
    is_deleted: bool = False
    
    # Price history (last few prices for reference)
    price_history: List[Dict[str, Any]] = Field(default_factory=list)
    # e.g., [{"price": 1000, "date": "2025-01-01", "notes": "bulk discount"}]
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class VendorItemMappingCreate(BaseModel):
    """Create a new vendor-item mapping"""
    vendor_id: str
    item_id: str
    vendor_sku: Optional[str] = None
    vendor_part_number: Optional[str] = None
    unit_price: float = 0
    min_order_quantity: int = 1
    lead_time_days: int = 0
    priority: int = 1
    contract_start: Optional[str] = None
    contract_end: Optional[str] = None
    contract_reference: Optional[str] = None
    is_preferred: bool = False


class VendorItemMappingUpdate(BaseModel):
    """Update vendor-item mapping"""
    vendor_sku: Optional[str] = None
    vendor_part_number: Optional[str] = None
    unit_price: Optional[float] = None
    min_order_quantity: Optional[int] = None
    lead_time_days: Optional[int] = None
    priority: Optional[int] = None
    contract_start: Optional[str] = None
    contract_end: Optional[str] = None
    contract_reference: Optional[str] = None
    is_preferred: Optional[bool] = None
    is_active: Optional[bool] = None
