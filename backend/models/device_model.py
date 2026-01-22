"""
Device Model Catalog - Smart device specifications and compatibility
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
import uuid


def get_ist_isoformat() -> str:
    from datetime import datetime, timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).isoformat()


class DeviceSpecifications(BaseModel):
    """Device specifications based on device type"""
    # Common specs
    connectivity: List[str] = []  # USB, WiFi, Ethernet, Bluetooth
    dimensions: Optional[str] = None
    weight: Optional[str] = None
    power_consumption: Optional[str] = None
    
    # Printer specific
    print_technology: Optional[str] = None  # Laser, Inkjet, Thermal
    color_support: Optional[str] = None  # Mono, Color
    print_speed: Optional[str] = None  # e.g., "40 ppm"
    paper_sizes: List[str] = []  # A4, A3, Letter, Legal
    duplex: Optional[bool] = None
    scanner: Optional[bool] = None
    adf: Optional[bool] = None  # Auto Document Feeder
    fax: Optional[bool] = None
    
    # Laptop/Desktop specific
    processor: Optional[str] = None
    ram_slots: Optional[int] = None
    max_ram: Optional[str] = None
    storage_type: Optional[str] = None  # HDD, SSD, NVMe
    storage_capacity: Optional[str] = None
    display_size: Optional[str] = None
    graphics: Optional[str] = None
    operating_system: Optional[str] = None
    
    # CCTV/NVR specific
    resolution: Optional[str] = None  # 1080p, 4K, 5MP
    channels: Optional[int] = None
    poe_support: Optional[bool] = None
    max_hdd_capacity: Optional[str] = None
    hdd_bays: Optional[int] = None
    night_vision: Optional[bool] = None
    motion_detection: Optional[bool] = None
    
    # Router/Switch specific
    ports: Optional[int] = None
    speed: Optional[str] = None  # 10/100, Gigabit
    wifi_bands: List[str] = []  # 2.4GHz, 5GHz, 6GHz
    wifi_standard: Optional[str] = None  # WiFi 5, WiFi 6, WiFi 6E
    
    # UPS specific
    va_rating: Optional[str] = None
    watt_rating: Optional[str] = None
    battery_type: Optional[str] = None
    backup_time: Optional[str] = None
    outlets: Optional[int] = None
    
    # Server specific
    form_factor: Optional[str] = None  # Tower, Rack
    cpu_sockets: Optional[int] = None
    drive_bays: Optional[int] = None
    raid_support: List[str] = []


class CompatibleConsumable(BaseModel):
    """Compatible consumable/part for a device model"""
    consumable_type: str  # Toner, Ink, Drum, HDD, RAM, SSD, Battery
    name: str
    part_number: str
    color: Optional[str] = None  # Black, Cyan, Magenta, Yellow
    yield_pages: Optional[str] = None  # For toners/inks
    capacity: Optional[str] = None  # For HDD/RAM/SSD
    notes: Optional[str] = None


class DeviceModel(BaseModel):
    """Catalog of device models with specifications and compatible parts"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Basic identification
    device_type: str  # Printer, Laptop, Desktop, CCTV, NVR, Router, UPS, Server
    brand: str
    model: str
    model_variants: List[str] = []  # Alternative model names
    
    # Category
    category: Optional[str] = None  # e.g., "Mono Laser MFP", "Gaming Laptop"
    
    # Specifications (AI-fetched or manually entered)
    specifications: DeviceSpecifications = Field(default_factory=DeviceSpecifications)
    
    # Compatible consumables and parts
    compatible_consumables: List[CompatibleConsumable] = []
    
    # Compatible upgrades (RAM, SSD, etc.)
    compatible_upgrades: List[CompatibleConsumable] = []
    
    # Images
    image_url: Optional[str] = None
    
    # Data source
    source: str = "manual"  # manual, ai_generated, manufacturer
    ai_confidence: Optional[float] = None  # 0-1 confidence score
    
    # Metadata
    is_verified: bool = False  # Admin verified the data
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: Optional[str] = None


class DeviceModelCreate(BaseModel):
    device_type: str
    brand: str
    model: str
    model_variants: List[str] = []
    category: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    compatible_consumables: List[Dict[str, Any]] = []
    compatible_upgrades: List[Dict[str, Any]] = []
    image_url: Optional[str] = None


class DeviceModelUpdate(BaseModel):
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    model_variants: Optional[List[str]] = None
    category: Optional[str] = None
    specifications: Optional[Dict[str, Any]] = None
    compatible_consumables: Optional[List[Dict[str, Any]]] = None
    compatible_upgrades: Optional[List[Dict[str, Any]]] = None
    image_url: Optional[str] = None
    is_verified: Optional[bool] = None


class AILookupRequest(BaseModel):
    """Request for AI-powered device lookup"""
    device_type: str
    brand: str
    model: str


class AILookupResponse(BaseModel):
    """Response from AI device lookup"""
    found: bool
    device_model: Optional[DeviceModel] = None
    message: str
    source: str = "ai_generated"
