"""
Inventory Models
================
Inventory Location and Stock Ledger for tracking stock movements.

Key Concepts:
- InventoryLocation: Physical/logical places where stock is held (warehouse, van, etc.)
- StockLedger: IMMUTABLE ledger of all stock movements (source of truth)
- Stock levels are CALCULATED from ledger entries, not stored directly
"""
import uuid
from datetime import datetime, timezone
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from enum import Enum
from utils.helpers import get_ist_isoformat


# ==================== INVENTORY LOCATION ====================

class LocationType(str, Enum):
    """Types of inventory locations"""
    WAREHOUSE = "warehouse"      # Main warehouse/godown
    VAN = "van"                  # Technician's van/vehicle
    OFFICE = "office"           # Office storage
    SITE = "site"               # Customer site (for consignment)
    REPAIR_CENTER = "repair"    # Repair center/workshop
    QUARANTINE = "quarantine"   # Quarantine for defective items
    TRANSIT = "transit"         # In transit between locations


class InventoryLocation(BaseModel):
    """Physical or logical location where inventory is stored"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # Location identification
    name: str  # e.g., "Main Warehouse", "Van-01", "Mumbai Office"
    code: Optional[str] = None  # Short code like "WH-01", "VAN-AK"
    
    # Type and hierarchy
    location_type: str = LocationType.WAREHOUSE.value
    parent_location_id: Optional[str] = None  # For hierarchical locations
    
    # Address (for physical locations)
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    
    # Contact
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    
    # For van/technician locations
    assigned_user_id: Optional[str] = None  # Technician assigned to this van
    assigned_user_name: Optional[str] = None
    
    # For site locations
    company_id: Optional[str] = None  # If this is a customer site
    site_id: Optional[str] = None
    
    # Flags
    is_active: bool = True
    allows_negative: bool = False  # Allow negative stock (for special cases)
    is_default: bool = False  # Default receive location
    
    # Audit
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None


class InventoryLocationCreate(BaseModel):
    """Create a new inventory location"""
    name: str
    code: Optional[str] = None
    location_type: str = LocationType.WAREHOUSE.value
    parent_location_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    assigned_user_id: Optional[str] = None
    company_id: Optional[str] = None
    site_id: Optional[str] = None
    is_default: bool = False


class InventoryLocationUpdate(BaseModel):
    """Update inventory location"""
    name: Optional[str] = None
    code: Optional[str] = None
    location_type: Optional[str] = None
    parent_location_id: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    assigned_user_id: Optional[str] = None
    company_id: Optional[str] = None
    site_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


# ==================== STOCK LEDGER ====================

class StockTransactionType(str, Enum):
    """Types of stock transactions"""
    # Inbound
    PURCHASE = "purchase"           # Received from vendor
    TRANSFER_IN = "transfer_in"     # Received from another location
    RETURN = "return"               # Returned from service/customer
    ADJUSTMENT_IN = "adjustment_in" # Manual positive adjustment
    OPENING = "opening"             # Opening stock entry
    
    # Outbound
    ISSUE = "issue"                 # Issued to service ticket
    TRANSFER_OUT = "transfer_out"   # Sent to another location
    DAMAGE = "damage"               # Written off as damaged
    ADJUSTMENT_OUT = "adjustment_out" # Manual negative adjustment
    SALE = "sale"                   # Sold to customer


class StockLedger(BaseModel):
    """
    IMMUTABLE stock movement record.
    
    This is an append-only ledger - entries can NEVER be modified or deleted.
    Stock levels are calculated by summing qty_in - qty_out for an item+location.
    
    Golden Rule: Current Stock = SUM(qty_in) - SUM(qty_out) for item_id + location_id
    """
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # What moved
    item_id: str  # Reference to ItemMaster
    item_name: str  # Denormalized for quick lookup
    
    # Where
    location_id: str  # Reference to InventoryLocation
    location_name: str  # Denormalized for quick lookup
    
    # Quantity (only one of these should be > 0)
    qty_in: int = 0   # Quantity added to this location
    qty_out: int = 0  # Quantity removed from this location
    
    # For serialized items
    serial_numbers: List[str] = Field(default_factory=list)
    
    # Transaction type
    transaction_type: str = StockTransactionType.ADJUSTMENT_IN.value
    
    # Reference to source document
    reference_type: Optional[str] = None  # purchase_request, service_ticket, transfer, etc.
    reference_id: Optional[str] = None    # ID of the source document
    reference_number: Optional[str] = None  # Human-readable reference number
    
    # For transfers (track from/to)
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    
    # Costing (for this transaction)
    unit_cost: float = 0
    total_cost: float = 0
    
    # Notes
    notes: Optional[str] = None
    
    # Audit (IMMUTABLE)
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by_id: str = ""
    created_by_name: str = ""
    
    # Running balance (calculated at creation time for reference)
    running_balance: int = 0


class StockLedgerCreate(BaseModel):
    """Create a new stock ledger entry (stock movement)"""
    item_id: str
    location_id: str
    qty_in: int = 0
    qty_out: int = 0
    serial_numbers: Optional[List[str]] = None
    transaction_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[str] = None
    reference_number: Optional[str] = None
    from_location_id: Optional[str] = None
    to_location_id: Optional[str] = None
    unit_cost: float = 0
    notes: Optional[str] = None


class StockTransferRequest(BaseModel):
    """Request to transfer stock between locations"""
    item_id: str
    from_location_id: str
    to_location_id: str
    quantity: int
    serial_numbers: Optional[List[str]] = None
    notes: Optional[str] = None


class StockAdjustmentRequest(BaseModel):
    """Request to adjust stock (positive or negative)"""
    item_id: str
    location_id: str
    quantity: int  # Positive for increase, negative for decrease
    serial_numbers: Optional[List[str]] = None
    reason: str  # Required reason for adjustment
    notes: Optional[str] = None


class StockLevelResponse(BaseModel):
    """Response model for stock levels"""
    item_id: str
    item_name: str
    location_id: str
    location_name: str
    current_stock: int
    reserved_stock: int = 0  # Reserved for pending tickets
    available_stock: int = 0  # current_stock - reserved_stock
