"""
Seeding functions for default data - Tenant-scoped
"""
import logging
from database import db
from models.common import MasterItem
from models.supplies import SupplyCategory, SupplyProduct

logger = logging.getLogger(__name__)


async def seed_default_masters():
    """Seed default master data per organization if not exists"""
    orgs = await db.organizations.find({"is_deleted": {"$ne": True}}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
    if not orgs:
        return

    defaults = [
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
        {"type": "service_type", "name": "Repair", "code": "REPAIR", "sort_order": 1},
        {"type": "service_type", "name": "Part Replacement", "code": "PART_REPLACE", "sort_order": 2},
        {"type": "service_type", "name": "Inspection", "code": "INSPECTION", "sort_order": 3},
        {"type": "service_type", "name": "AMC Visit", "code": "AMC_VISIT", "sort_order": 4},
        {"type": "service_type", "name": "Preventive Maintenance", "code": "PM", "sort_order": 5},
        {"type": "service_type", "name": "Software Update", "code": "SOFTWARE", "sort_order": 6},
        {"type": "service_type", "name": "Warranty Claim", "code": "WARRANTY_CLAIM", "sort_order": 7},
        {"type": "service_type", "name": "Other", "code": "OTHER", "sort_order": 99},
        {"type": "condition", "name": "New", "code": "NEW", "sort_order": 1},
        {"type": "condition", "name": "Good", "code": "GOOD", "sort_order": 2},
        {"type": "condition", "name": "Fair", "code": "FAIR", "sort_order": 3},
        {"type": "condition", "name": "Poor", "code": "POOR", "sort_order": 4},
        {"type": "asset_status", "name": "Active", "code": "ACTIVE", "sort_order": 1},
        {"type": "asset_status", "name": "In Repair", "code": "IN_REPAIR", "sort_order": 2},
        {"type": "asset_status", "name": "Retired", "code": "RETIRED", "sort_order": 3},
        {"type": "asset_status", "name": "Lost", "code": "LOST", "sort_order": 4},
        {"type": "asset_status", "name": "Scrapped", "code": "SCRAPPED", "sort_order": 5},
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
        {"type": "brand", "name": "Logitech", "code": "LOGITECH", "sort_order": 15},
        {"type": "brand", "name": "Microsoft", "code": "MICROSOFT", "sort_order": 16},
        {"type": "brand", "name": "Other", "code": "OTHER", "sort_order": 99},
        {"type": "accessory_type", "name": "Keyboard", "code": "KEYBOARD", "sort_order": 1},
        {"type": "accessory_type", "name": "Mouse", "code": "MOUSE", "sort_order": 2},
        {"type": "accessory_type", "name": "Headset", "code": "HEADSET", "sort_order": 3},
        {"type": "accessory_type", "name": "Webcam", "code": "WEBCAM", "sort_order": 4},
        {"type": "accessory_type", "name": "Monitor Stand", "code": "MONITOR_STAND", "sort_order": 5},
        {"type": "accessory_type", "name": "Laptop Stand", "code": "LAPTOP_STAND", "sort_order": 6},
        {"type": "accessory_type", "name": "Docking Station", "code": "DOCKING_STATION", "sort_order": 7},
        {"type": "accessory_type", "name": "USB Hub", "code": "USB_HUB", "sort_order": 8},
        {"type": "accessory_type", "name": "Power Adapter", "code": "POWER_ADAPTER", "sort_order": 9},
        {"type": "accessory_type", "name": "Cable", "code": "CABLE", "sort_order": 10},
        {"type": "accessory_type", "name": "External HDD", "code": "EXTERNAL_HDD", "sort_order": 11},
        {"type": "accessory_type", "name": "Pen Drive", "code": "PEN_DRIVE", "sort_order": 12},
        {"type": "accessory_type", "name": "Memory Card", "code": "MEMORY_CARD", "sort_order": 13},
        {"type": "accessory_type", "name": "Bag/Case", "code": "BAG_CASE", "sort_order": 14},
        {"type": "accessory_type", "name": "Other", "code": "OTHER", "sort_order": 99},
        {"type": "asset_group_type", "name": "Workstation", "code": "WORKSTATION", "description": "Desktop setup with CPU, Monitor, KB, Mouse", "sort_order": 1},
        {"type": "asset_group_type", "name": "CCTV System", "code": "CCTV_SYSTEM", "description": "NVR with cameras and storage", "sort_order": 2},
        {"type": "asset_group_type", "name": "Server Rack", "code": "SERVER_RACK", "description": "Server with UPS, switches", "sort_order": 3},
        {"type": "asset_group_type", "name": "Network Setup", "code": "NETWORK_SETUP", "description": "Router, switches, access points", "sort_order": 4},
        {"type": "asset_group_type", "name": "Conference Room", "code": "CONFERENCE_ROOM", "description": "Display, camera, speaker system", "sort_order": 5},
        {"type": "asset_group_type", "name": "Custom", "code": "CUSTOM", "description": "Custom grouping", "sort_order": 99},
        {"type": "duration_unit", "name": "Days", "code": "DAYS", "description": "Calendar days", "sort_order": 1},
        {"type": "duration_unit", "name": "Months", "code": "MONTHS", "description": "Calendar months", "sort_order": 2},
        {"type": "duration_unit", "name": "Years", "code": "YEARS", "description": "Calendar years", "sort_order": 3},
        {"type": "subscription_provider", "name": "Google Workspace", "code": "GOOGLE_WORKSPACE", "description": "Google's business email and productivity suite", "sort_order": 1},
        {"type": "subscription_provider", "name": "Microsoft 365", "code": "MICROSOFT_365", "description": "Microsoft's cloud productivity suite", "sort_order": 2},
        {"type": "subscription_provider", "name": "Titan Email", "code": "TITAN", "description": "Professional email hosting by Titan", "sort_order": 3},
        {"type": "subscription_provider", "name": "Zoho Mail", "code": "ZOHO", "description": "Zoho's business email service", "sort_order": 4},
        {"type": "subscription_provider", "name": "Other", "code": "OTHER", "description": "Other email/cloud provider", "sort_order": 99},
        {"type": "subscription_plan", "name": "Business Starter", "code": "BUSINESS_STARTER", "description": "Entry-level business plan", "sort_order": 1},
        {"type": "subscription_plan", "name": "Business Standard", "code": "BUSINESS_STANDARD", "description": "Standard business plan", "sort_order": 2},
        {"type": "subscription_plan", "name": "Business Plus", "code": "BUSINESS_PLUS", "description": "Advanced business plan", "sort_order": 3},
        {"type": "subscription_plan", "name": "Business Premium", "code": "BUSINESS_PREMIUM", "description": "Premium business plan", "sort_order": 4},
        {"type": "subscription_plan", "name": "Enterprise Starter", "code": "ENTERPRISE_STARTER", "description": "Entry-level enterprise plan", "sort_order": 5},
        {"type": "subscription_plan", "name": "Enterprise Standard", "code": "ENTERPRISE_STANDARD", "description": "Standard enterprise plan", "sort_order": 6},
        {"type": "subscription_plan", "name": "Enterprise Plus", "code": "ENTERPRISE_PLUS", "description": "Advanced enterprise plan", "sort_order": 7},
        {"type": "subscription_plan", "name": "E3", "code": "E3", "description": "Microsoft Enterprise E3", "sort_order": 8},
        {"type": "subscription_plan", "name": "E5", "code": "E5", "description": "Microsoft Enterprise E5", "sort_order": 9},
        {"type": "subscription_plan", "name": "Lite", "code": "LITE", "description": "Basic/Lite plan", "sort_order": 10},
        {"type": "subscription_plan", "name": "Premium", "code": "PREMIUM", "description": "Premium tier plan", "sort_order": 11},
        {"type": "subscription_plan", "name": "Custom", "code": "CUSTOM", "description": "Custom/Other plan", "sort_order": 99},
        {"type": "billing_cycle", "name": "Monthly", "code": "MONTHLY", "description": "Billed every month", "sort_order": 1},
        {"type": "billing_cycle", "name": "Quarterly", "code": "QUARTERLY", "description": "Billed every 3 months", "sort_order": 2},
        {"type": "billing_cycle", "name": "Half Yearly", "code": "HALF_YEARLY", "description": "Billed every 6 months", "sort_order": 3},
        {"type": "billing_cycle", "name": "Yearly", "code": "YEARLY", "description": "Billed annually", "sort_order": 4},
    ]

    for org in orgs:
        org_id = org.get("id")
        if not org_id:
            continue
        existing = await db.masters.count_documents({"organization_id": org_id})
        if existing > 0:
            continue
        for item in defaults:
            master = MasterItem(**item)
            doc = master.model_dump()
            doc["organization_id"] = org_id
            await db.masters.insert_one(doc)
        logger.info(f"Seeded {len(defaults)} masters for org {org.get('name', org_id)}")


async def seed_default_supplies():
    """Seed default supply categories and products per organization"""
    orgs = await db.organizations.find({"is_deleted": {"$ne": True}}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
    if not orgs:
        return

    for org in orgs:
        org_id = org.get("id")
        if not org_id:
            continue
        existing = await db.supply_categories.count_documents({"organization_id": org_id})
        if existing > 0:
            continue

        stationery_cat = SupplyCategory(name="Stationery", icon="", description="Paper, pens, files, and other office stationery", sort_order=1)
        consumables_cat = SupplyCategory(name="Printer Consumables", icon="", description="Ink, toner, drums, and labels", sort_order=2)

        for cat in [stationery_cat, consumables_cat]:
            doc = cat.model_dump()
            doc["organization_id"] = org_id
            await db.supply_categories.insert_one(doc)

        sample_products = [
            SupplyProduct(category_id=stationery_cat.id, name="A4 Paper (500 sheets)", unit="ream"),
            SupplyProduct(category_id=stationery_cat.id, name="Legal Size Paper (500 sheets)", unit="ream"),
            SupplyProduct(category_id=stationery_cat.id, name="Ball Point Pen - Blue", unit="pack of 10"),
            SupplyProduct(category_id=stationery_cat.id, name="Ball Point Pen - Black", unit="pack of 10"),
            SupplyProduct(category_id=stationery_cat.id, name="File Folder", unit="pack of 10"),
            SupplyProduct(category_id=stationery_cat.id, name="Sticky Notes (3x3)", unit="pack"),
            SupplyProduct(category_id=stationery_cat.id, name="Envelopes - A4", unit="pack of 50"),
            SupplyProduct(category_id=stationery_cat.id, name="Stapler Pins", unit="box"),
            SupplyProduct(category_id=consumables_cat.id, name="Printer Ink - Black", unit="cartridge"),
            SupplyProduct(category_id=consumables_cat.id, name="Printer Ink - Color", unit="cartridge"),
            SupplyProduct(category_id=consumables_cat.id, name="Toner Cartridge - Black", unit="piece"),
            SupplyProduct(category_id=consumables_cat.id, name="Toner Cartridge - Cyan", unit="piece"),
            SupplyProduct(category_id=consumables_cat.id, name="Toner Cartridge - Magenta", unit="piece"),
            SupplyProduct(category_id=consumables_cat.id, name="Toner Cartridge - Yellow", unit="piece"),
            SupplyProduct(category_id=consumables_cat.id, name="Drum Unit", unit="piece"),
            SupplyProduct(category_id=consumables_cat.id, name="Printer Labels (A4 Sheet)", unit="pack of 100"),
        ]

        for p in sample_products:
            doc = p.model_dump()
            doc["organization_id"] = org_id
            await db.supply_products.insert_one(doc)

        logger.info(f"Seeded default supplies for org {org.get('name', org_id)}")
