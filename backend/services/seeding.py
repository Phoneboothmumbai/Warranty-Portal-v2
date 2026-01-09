"""
Seeding functions for default data
"""
import logging
from database import db
from models.common import MasterItem
from models.supplies import SupplyCategory, SupplyProduct

logger = logging.getLogger(__name__)


async def seed_default_masters():
    """Seed default master data if not exists"""
    existing = await db.masters.count_documents({})
    if existing > 0:
        return
    
    defaults = [
        # Device Types
        {"type": "device_type", "name": "Laptop", "code": "LAPTOP", "sort_order": 1},
        {"type": "device_type", "name": "Desktop", "code": "DESKTOP", "sort_order": 2},
        {"type": "device_type", "name": "Monitor", "code": "MONITOR", "sort_order": 3},
        {"type": "device_type", "name": "Printer", "code": "PRINTER", "sort_order": 4},
        {"type": "device_type", "name": "CCTV", "code": "CCTV", "sort_order": 5},
        {"type": "device_type", "name": "Router", "code": "ROUTER", "sort_order": 6},
        {"type": "device_type", "name": "Server", "code": "SERVER", "sort_order": 7},
        {"type": "device_type", "name": "UPS", "code": "UPS", "sort_order": 8},
        {"type": "device_type", "name": "Scanner", "code": "SCANNER", "sort_order": 9},
        {"type": "device_type", "name": "Projector", "code": "PROJECTOR", "sort_order": 10},
        {"type": "device_type", "name": "Other", "code": "OTHER", "sort_order": 99},
        
        # Part Types
        {"type": "part_type", "name": "Keyboard", "code": "KEYBOARD", "sort_order": 1},
        {"type": "part_type", "name": "Battery", "code": "BATTERY", "sort_order": 2},
        {"type": "part_type", "name": "HDD", "code": "HDD", "sort_order": 3},
        {"type": "part_type", "name": "SSD", "code": "SSD", "sort_order": 4},
        {"type": "part_type", "name": "RAM", "code": "RAM", "sort_order": 5},
        {"type": "part_type", "name": "Screen/Display", "code": "SCREEN", "sort_order": 6},
        {"type": "part_type", "name": "Motherboard", "code": "MOTHERBOARD", "sort_order": 7},
        {"type": "part_type", "name": "Power Supply", "code": "PSU", "sort_order": 8},
        {"type": "part_type", "name": "Fan/Cooling", "code": "FAN", "sort_order": 9},
        {"type": "part_type", "name": "Charger/Adapter", "code": "CHARGER", "sort_order": 10},
        {"type": "part_type", "name": "Camera/Webcam", "code": "CAMERA", "sort_order": 11},
        {"type": "part_type", "name": "Touchpad", "code": "TOUCHPAD", "sort_order": 12},
        {"type": "part_type", "name": "Speakers", "code": "SPEAKERS", "sort_order": 13},
        {"type": "part_type", "name": "Other", "code": "OTHER", "sort_order": 99},
        
        # Service Types
        {"type": "service_type", "name": "Repair", "code": "REPAIR", "sort_order": 1},
        {"type": "service_type", "name": "Part Replacement", "code": "PART_REPLACE", "sort_order": 2},
        {"type": "service_type", "name": "Inspection", "code": "INSPECTION", "sort_order": 3},
        {"type": "service_type", "name": "AMC Visit", "code": "AMC_VISIT", "sort_order": 4},
        {"type": "service_type", "name": "Preventive Maintenance", "code": "PM", "sort_order": 5},
        {"type": "service_type", "name": "Software Update", "code": "SOFTWARE", "sort_order": 6},
        {"type": "service_type", "name": "Warranty Claim", "code": "WARRANTY_CLAIM", "sort_order": 7},
        {"type": "service_type", "name": "Other", "code": "OTHER", "sort_order": 99},
        
        # Conditions
        {"type": "condition", "name": "New", "code": "NEW", "sort_order": 1},
        {"type": "condition", "name": "Good", "code": "GOOD", "sort_order": 2},
        {"type": "condition", "name": "Fair", "code": "FAIR", "sort_order": 3},
        {"type": "condition", "name": "Poor", "code": "POOR", "sort_order": 4},
        
        # Asset Statuses
        {"type": "asset_status", "name": "Active", "code": "ACTIVE", "sort_order": 1},
        {"type": "asset_status", "name": "In Repair", "code": "IN_REPAIR", "sort_order": 2},
        {"type": "asset_status", "name": "Retired", "code": "RETIRED", "sort_order": 3},
        {"type": "asset_status", "name": "Lost", "code": "LOST", "sort_order": 4},
        {"type": "asset_status", "name": "Scrapped", "code": "SCRAPPED", "sort_order": 5},
        
        # Common Brands
        {"type": "brand", "name": "Dell", "code": "DELL", "sort_order": 1},
        {"type": "brand", "name": "HP", "code": "HP", "sort_order": 2},
        {"type": "brand", "name": "Lenovo", "code": "LENOVO", "sort_order": 3},
        {"type": "brand", "name": "Asus", "code": "ASUS", "sort_order": 4},
        {"type": "brand", "name": "Acer", "code": "ACER", "sort_order": 5},
        {"type": "brand", "name": "Apple", "code": "APPLE", "sort_order": 6},
        {"type": "brand", "name": "Samsung", "code": "SAMSUNG", "sort_order": 7},
        {"type": "brand", "name": "LG", "code": "LG", "sort_order": 8},
        {"type": "brand", "name": "Canon", "code": "CANON", "sort_order": 9},
        {"type": "brand", "name": "Epson", "code": "EPSON", "sort_order": 10},
        {"type": "brand", "name": "Hikvision", "code": "HIKVISION", "sort_order": 11},
        {"type": "brand", "name": "Cisco", "code": "CISCO", "sort_order": 12},
        {"type": "brand", "name": "TP-Link", "code": "TPLINK", "sort_order": 13},
        {"type": "brand", "name": "APC", "code": "APC", "sort_order": 14},
        {"type": "brand", "name": "Other", "code": "OTHER", "sort_order": 99},
        
        # Duration Units (for warranty/AMC/license calculations)
        {"type": "duration_unit", "name": "Days", "code": "DAYS", "description": "Calendar days", "sort_order": 1},
        {"type": "duration_unit", "name": "Months", "code": "MONTHS", "description": "Calendar months", "sort_order": 2},
        {"type": "duration_unit", "name": "Years", "code": "YEARS", "description": "Calendar years", "sort_order": 3},
    ]
    
    for item in defaults:
        master = MasterItem(**item)
        await db.masters.insert_one(master.model_dump())
    
    logger.info(f"Seeded {len(defaults)} default master items")


async def seed_default_supplies():
    """Seed default supply categories and products if none exist"""
    existing_categories = await db.supply_categories.count_documents({})
    if existing_categories > 0:
        return
    
    # Create default categories
    stationery_cat = SupplyCategory(
        name="Stationery",
        icon="📁",
        description="Paper, pens, files, and other office stationery",
        sort_order=1
    )
    consumables_cat = SupplyCategory(
        name="Printer Consumables",
        icon="🖨",
        description="Ink, toner, drums, and labels",
        sort_order=2
    )
    
    await db.supply_categories.insert_many([
        stationery_cat.model_dump(),
        consumables_cat.model_dump()
    ])
    
    # Create sample products
    sample_products = [
        # Stationery
        SupplyProduct(category_id=stationery_cat.id, name="A4 Paper (500 sheets)", unit="ream"),
        SupplyProduct(category_id=stationery_cat.id, name="Legal Size Paper (500 sheets)", unit="ream"),
        SupplyProduct(category_id=stationery_cat.id, name="Ball Point Pen - Blue", unit="pack of 10"),
        SupplyProduct(category_id=stationery_cat.id, name="Ball Point Pen - Black", unit="pack of 10"),
        SupplyProduct(category_id=stationery_cat.id, name="File Folder", unit="pack of 10"),
        SupplyProduct(category_id=stationery_cat.id, name="Sticky Notes (3x3)", unit="pack"),
        SupplyProduct(category_id=stationery_cat.id, name="Envelopes - A4", unit="pack of 50"),
        SupplyProduct(category_id=stationery_cat.id, name="Stapler Pins", unit="box"),
        # Consumables
        SupplyProduct(category_id=consumables_cat.id, name="Printer Ink - Black", unit="cartridge"),
        SupplyProduct(category_id=consumables_cat.id, name="Printer Ink - Color", unit="cartridge"),
        SupplyProduct(category_id=consumables_cat.id, name="Toner Cartridge - Black", unit="piece"),
        SupplyProduct(category_id=consumables_cat.id, name="Toner Cartridge - Cyan", unit="piece"),
        SupplyProduct(category_id=consumables_cat.id, name="Toner Cartridge - Magenta", unit="piece"),
        SupplyProduct(category_id=consumables_cat.id, name="Toner Cartridge - Yellow", unit="piece"),
        SupplyProduct(category_id=consumables_cat.id, name="Drum Unit", unit="piece"),
        SupplyProduct(category_id=consumables_cat.id, name="Printer Labels (A4 Sheet)", unit="pack of 100"),
    ]
    
    await db.supply_products.insert_many([p.model_dump() for p in sample_products])
    logger.info("Seeded default supply categories and products")
