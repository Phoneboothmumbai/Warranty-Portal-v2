"""
AI-powered device specification lookup service
Uses OpenAI GPT via Emergent LLM Key to fetch device specs
"""
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


def get_device_type_prompt(device_type: str) -> str:
    """Get device-type specific prompt instructions"""
    prompts = {
        "Printer": """
For this PRINTER, provide:
- print_technology: Laser/Inkjet/Thermal
- color_support: Mono/Color
- print_speed: pages per minute (e.g., "40 ppm")
- paper_sizes: supported sizes array (A4, A3, Letter, Legal)
- duplex: true/false
- scanner: true/false (if MFP)
- adf: true/false (Auto Document Feeder)
- fax: true/false
- connectivity: array (USB, WiFi, Ethernet, Bluetooth)

For compatible_consumables, list ALL compatible toners/inks/drums with:
- consumable_type: Toner/Ink/Drum/Maintenance Kit
- name: Full product name
- part_number: Official part number (CRITICAL - be accurate)
- color: Black/Cyan/Magenta/Yellow (if applicable)
- yield_pages: Page yield (e.g., "3000 pages")
""",
        "Laptop": """
For this LAPTOP, provide:
- processor: CPU model
- ram_slots: number of RAM slots
- max_ram: maximum supported RAM
- storage_type: HDD/SSD/NVMe
- storage_capacity: included storage
- display_size: screen size in inches
- graphics: GPU model
- operating_system: pre-installed OS
- connectivity: array (USB-A, USB-C, HDMI, WiFi, Bluetooth)
- weight: in kg
- battery type and capacity

For compatible_upgrades, list compatible:
- RAM modules (DDR4/DDR5, speed, max capacity per slot)
- SSD/NVMe drives (form factor, interface)
- Battery replacement part numbers
""",
        "Desktop": """
For this DESKTOP, provide:
- processor: CPU model
- ram_slots: number of RAM slots
- max_ram: maximum supported RAM
- storage_type: HDD/SSD/NVMe
- storage_capacity: included storage
- graphics: GPU model (if applicable)
- operating_system: pre-installed OS
- connectivity: array (USB ports, HDMI, DisplayPort)
- form_factor: Tower/SFF/Mini

For compatible_upgrades, list compatible:
- RAM modules (DDR4/DDR5, speed)
- Storage drives
- Power supply specs (if upgradeable)
""",
        "NVR": """
For this NVR (Network Video Recorder), provide:
- channels: number of camera channels
- resolution: max supported resolution (4K, 5MP, 1080p)
- hdd_bays: number of HDD bays
- max_hdd_capacity: max HDD per bay
- poe_support: true/false (built-in PoE)
- connectivity: array (Ethernet ports, USB, HDMI, VGA)

For compatible_consumables, list compatible:
- HDDs: Surveillance-rated HDDs (WD Purple, Seagate SkyHawk) with part numbers and capacities
""",
        "CCTV": """
For this CCTV Camera, provide:
- resolution: camera resolution (4K, 5MP, 2MP/1080p)
- night_vision: true/false
- poe_support: true/false
- motion_detection: true/false
- connectivity: array (Ethernet, WiFi if applicable)
- weather_rating: IP rating if outdoor

List any compatible accessories like mounts, power adapters, etc.
""",
        "Router": """
For this ROUTER, provide:
- ports: number of LAN ports
- speed: port speed (Gigabit, 10/100)
- wifi_bands: array (2.4GHz, 5GHz, 6GHz)
- wifi_standard: WiFi 5/WiFi 6/WiFi 6E
- connectivity: array (WAN, LAN, USB)

List any compatible accessories.
""",
        "UPS": """
For this UPS, provide:
- va_rating: VA rating
- watt_rating: Watt rating
- battery_type: battery type
- backup_time: typical backup time at half load
- outlets: number of outlets

For compatible_consumables, list:
- Replacement batteries with part numbers
""",
        "Server": """
For this SERVER, provide:
- form_factor: Tower/Rack (1U, 2U, etc.)
- cpu_sockets: number of CPU sockets
- processor: supported CPU types
- ram_slots: number of RAM slots
- max_ram: maximum RAM capacity
- drive_bays: number of drive bays
- raid_support: array of supported RAID levels

For compatible_upgrades, list compatible:
- RAM modules (ECC/non-ECC, DDR type)
- Storage drives (form factor, interface)
- RAID controllers if applicable
"""
    }
    return prompts.get(device_type, "Provide all relevant technical specifications and compatible consumables/upgrades.")


async def fetch_device_specs_ai(device_type: str, brand: str, model: str) -> Optional[Dict[str, Any]]:
    """
    Use AI to fetch device specifications and compatible consumables.
    Returns structured data or None if lookup fails.
    """
    try:
        from emergentintegrations.llm.chat import chat, Message, Model
        
        type_specific_prompt = get_device_type_prompt(device_type)
        
        system_prompt = """You are a technical product database assistant. Your job is to provide accurate device specifications and compatible consumables/parts.

IMPORTANT RULES:
1. Be ACCURATE with part numbers - these are critical for ordering
2. If you're not sure about a specific detail, omit it rather than guess
3. Return ONLY valid JSON, no markdown or explanations
4. Use the exact field names provided
5. For arrays, use proper JSON arrays
6. For booleans, use true/false (lowercase)

Return a JSON object with this structure:
{
    "found": true/false,
    "category": "category description",
    "specifications": { ... device specs ... },
    "compatible_consumables": [ ... array of consumables ... ],
    "compatible_upgrades": [ ... array of upgrades ... ],
    "confidence": 0.0-1.0
}

If you cannot find reliable information about this exact model, return:
{"found": false, "message": "reason"}"""

        user_prompt = f"""Look up specifications for:
Device Type: {device_type}
Brand: {brand}
Model: {model}

{type_specific_prompt}

Return ONLY the JSON response, no other text."""

        # Call OpenAI via Emergent
        response = await chat(
            messages=[
                Message(role="system", content=system_prompt),
                Message(role="user", content=user_prompt)
            ],
            model=Model.GPT_4O_MINI,
            temperature=0.1  # Low temperature for factual accuracy
        )
        
        # Parse the response
        response_text = response.message.strip()
        
        # Clean up response if it has markdown code blocks
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1])
        
        result = json.loads(response_text)
        return result
        
    except json.JSONDecodeError as e:
        logger.error(f"AI response JSON parse error: {e}")
        return None
    except Exception as e:
        logger.error(f"AI lookup error: {e}")
        return None


async def get_or_create_device_model(
    db,
    device_type: str,
    brand: str,
    model: str,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Get device model from cache or fetch from AI.
    
    Args:
        db: Database instance
        device_type: Type of device
        brand: Device brand
        model: Device model name
        force_refresh: Force AI lookup even if cached
    
    Returns:
        Device model data or error message
    """
    from models.device_model import DeviceModel, DeviceSpecifications, CompatibleConsumable
    from utils.helpers import get_ist_isoformat
    
    # Normalize inputs
    brand_normalized = brand.strip().title()
    model_normalized = model.strip()
    
    # Check cache first (unless force refresh)
    if not force_refresh:
        cached = await db.device_models.find_one({
            "brand": {"$regex": f"^{brand_normalized}$", "$options": "i"},
            "model": {"$regex": f"^{model_normalized}$", "$options": "i"},
            "device_type": device_type,
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        
        if cached:
            return {
                "found": True,
                "device_model": cached,
                "source": "cache",
                "message": "Found in device catalog"
            }
    
    # Fetch from AI
    ai_result = await fetch_device_specs_ai(device_type, brand_normalized, model_normalized)
    
    if not ai_result or not ai_result.get("found", False):
        return {
            "found": False,
            "device_model": None,
            "source": "ai_generated",
            "message": ai_result.get("message", "Could not find specifications for this device model")
        }
    
    # Build device model from AI response
    specs_data = ai_result.get("specifications", {})
    consumables_data = ai_result.get("compatible_consumables", [])
    upgrades_data = ai_result.get("compatible_upgrades", [])
    
    # Create consumables list
    consumables = []
    for c in consumables_data:
        if c.get("part_number") and c.get("name"):
            consumables.append({
                "consumable_type": c.get("consumable_type", "Unknown"),
                "name": c.get("name"),
                "part_number": c.get("part_number"),
                "color": c.get("color"),
                "yield_pages": c.get("yield_pages"),
                "capacity": c.get("capacity"),
                "notes": c.get("notes")
            })
    
    # Create upgrades list
    upgrades = []
    for u in upgrades_data:
        if u.get("name"):
            upgrades.append({
                "consumable_type": u.get("consumable_type", "Upgrade"),
                "name": u.get("name"),
                "part_number": u.get("part_number", ""),
                "capacity": u.get("capacity"),
                "notes": u.get("notes")
            })
    
    # Create the device model
    device_model = DeviceModel(
        device_type=device_type,
        brand=brand_normalized,
        model=model_normalized,
        category=ai_result.get("category"),
        specifications=DeviceSpecifications(**specs_data) if specs_data else DeviceSpecifications(),
        compatible_consumables=consumables,
        compatible_upgrades=upgrades,
        source="ai_generated",
        ai_confidence=ai_result.get("confidence", 0.7),
        is_verified=False
    )
    
    # Save to cache
    model_dict = device_model.model_dump()
    
    # Check if exists and update, or insert new
    existing = await db.device_models.find_one({
        "brand": {"$regex": f"^{brand_normalized}$", "$options": "i"},
        "model": {"$regex": f"^{model_normalized}$", "$options": "i"},
        "device_type": device_type
    })
    
    if existing:
        model_dict["id"] = existing["id"]
        model_dict["updated_at"] = get_ist_isoformat()
        await db.device_models.update_one(
            {"id": existing["id"]},
            {"$set": model_dict}
        )
    else:
        await db.device_models.insert_one(model_dict)
    
    # Fetch the saved model
    saved = await db.device_models.find_one({"id": model_dict["id"]}, {"_id": 0})
    
    return {
        "found": True,
        "device_model": saved,
        "source": "ai_generated",
        "message": "Specifications fetched via AI"
    }
