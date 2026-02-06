"""
Item Master Model
=================
Master catalog of parts, consumables, and items used in service operations.
This is the central parts catalog - not inventory levels (those are in StockLedger).
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from utils.helpers import get_ist_isoformat


class ItemMaster(BaseModel):
    """Item/Part definition in the catalog"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # Item identification
    name: str  # e.g., "HP 26A Toner Cartridge"
    sku: Optional[str] = None  # Stock Keeping Unit
    part_number: Optional[str] = None  # Manufacturer part number
    barcode: Optional[str] = None  # Barcode for scanning
    
    # Categorization
    category: str = "part"  # part, consumable, accessory, spare, tool
    sub_category: Optional[str] = None  # e.g., "toner", "drum", "fuser"
    
    # Brand/Model
    brand: Optional[str] = None
    model: Optional[str] = None
    
    # Specifications
    specifications: Dict[str, Any] = Field(default_factory=dict)
    # e.g., {"capacity": "3100 pages", "color": "black", "yield": "standard"}
    
    # Compatibility
    compatible_devices: List[str] = Field(default_factory=list)  # List of device model names
    compatible_brands: List[str] = Field(default_factory=list)   # List of brands
    
    # Pricing (base prices, actual prices in VendorItemMapping)
    unit_price: float = 0  # Default selling price
    cost_price: float = 0  # Default cost price
    currency: str = "INR"
    
    # Units
    unit_of_measure: str = "piece"  # piece, box, set, kg, meter, etc.
    
    # Serialization
    is_serialized: bool = False  # Track individual serial numbers
    
    # Inventory hints
    reorder_level: int = 0  # Alert when stock falls below
    reorder_quantity: int = 0  # Suggested reorder quantity
    lead_time_days: int = 0  # Typical lead time from vendor
    
    # Tax
    hsn_code: Optional[str] = None  # For GST
    gst_rate: float = 18  # GST percentage
    
    # Media
    image_url: Optional[str] = None
    datasheet_url: Optional[str] = None
    
    # Flags
    is_active: bool = True
    is_deleted: bool = False
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None


class ItemMasterCreate(BaseModel):
    """Create a new item"""
    name: str
    sku: Optional[str] = None
    part_number: Optional[str] = None
    barcode: Optional[str] = None
    category: str = "part"
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    compatible_devices: Optional[List[str]] = None
    compatible_brands: Optional[List[str]] = None
    unit_price: float = 0
    cost_price: float = 0
    unit_of_measure: str = "piece"
    is_serialized: bool = False
    reorder_level: int = 0
    reorder_quantity: int = 0
    lead_time_days: int = 0
    hsn_code: Optional[str] = None
    gst_rate: float = 18
    image_url: Optional[str] = None


class ItemMasterUpdate(BaseModel):
    """Update item"""
    name: Optional[str] = None
    sku: Optional[str] = None
    part_number: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    compatible_devices: Optional[List[str]] = None
    compatible_brands: Optional[List[str]] = None
    unit_price: Optional[float] = None
    cost_price: Optional[float] = None
    unit_of_measure: Optional[str] = None
    is_serialized: Optional[bool] = None
    reorder_level: Optional[int] = None
    reorder_quantity: Optional[int] = None
    lead_time_days: Optional[int] = None
    hsn_code: Optional[str] = None
    gst_rate: Optional[float] = None
    image_url: Optional[str] = None
    is_active: Optional[bool] = None
