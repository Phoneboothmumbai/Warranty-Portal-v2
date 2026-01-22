"""
Device Category Synonyms and Smart Search Utility

This module provides synonym mapping for device categories to enable
intelligent search across alternative names and related terms.
"""

# Device category synonyms - each key maps to a list of equivalent terms
DEVICE_CATEGORY_SYNONYMS = {
    # CCTV / Surveillance
    "cctv": [
        "cctv", "video surveillance", "ip camera", "security camera", 
        "surveillance camera", "digital surveillance", "video monitoring",
        "electronic surveillance", "smart surveillance", "cctv camera",
        "surveillance system", "security system", "camera system",
        "ip cam", "security cam", "dvr camera", "nvr camera"
    ],
    
    # NVR / DVR
    "nvr": [
        "nvr", "network video recorder", "video recorder", "dvr",
        "digital video recorder", "surveillance recorder", "cctv recorder",
        "security recorder", "video storage", "camera recorder"
    ],
    
    # Printer
    "printer": [
        "printer", "laser printer", "inkjet printer", "multifunction",
        "mfp", "all-in-one", "copier", "printing device", "laserjet",
        "deskjet", "officejet", "print machine", "scanner printer",
        "fax machine", "photo printer", "label printer", "thermal printer"
    ],
    
    # Laptop
    "laptop": [
        "laptop", "notebook", "portable computer", "ultrabook", 
        "macbook", "chromebook", "netbook", "mobile workstation",
        "portable pc", "laptop computer", "thin and light"
    ],
    
    # Desktop
    "desktop": [
        "desktop", "desktop computer", "pc", "personal computer",
        "workstation", "tower", "mini pc", "all-in-one pc", "aio",
        "desktop pc", "computer", "cpu", "system unit", "imac"
    ],
    
    # Server
    "server": [
        "server", "rack server", "tower server", "blade server",
        "file server", "web server", "database server", "application server",
        "nas", "network attached storage", "storage server", "compute server",
        "virtual server", "hypervisor", "server machine"
    ],
    
    # Router / Network
    "router": [
        "router", "wifi router", "wireless router", "network router",
        "gateway", "modem router", "access point", "wifi access point",
        "mesh router", "wireless access point", "wap", "wifi ap",
        "network gateway", "internet router"
    ],
    
    # Switch
    "switch": [
        "switch", "network switch", "ethernet switch", "managed switch",
        "unmanaged switch", "poe switch", "gigabit switch", "layer 2 switch",
        "layer 3 switch", "data switch", "lan switch", "hub"
    ],
    
    # UPS / Power
    "ups": [
        "ups", "uninterruptible power supply", "battery backup",
        "power backup", "power supply", "inverter", "power protection",
        "surge protector", "voltage regulator", "power conditioner",
        "backup power", "emergency power"
    ],
    
    # Firewall / Security
    "firewall": [
        "firewall", "network firewall", "hardware firewall", "utm",
        "unified threat management", "security appliance", "next gen firewall",
        "ngfw", "network security", "intrusion prevention"
    ],
    
    # Monitor / Display
    "monitor": [
        "monitor", "display", "screen", "lcd monitor", "led monitor",
        "computer monitor", "display screen", "flat panel", "curved monitor",
        "gaming monitor", "professional monitor", "4k monitor"
    ],
    
    # Projector
    "projector": [
        "projector", "lcd projector", "dlp projector", "laser projector",
        "video projector", "multimedia projector", "presentation projector",
        "home theater projector", "portable projector", "short throw"
    ],
    
    # Scanner
    "scanner": [
        "scanner", "document scanner", "flatbed scanner", "sheet fed scanner",
        "barcode scanner", "image scanner", "photo scanner", "portable scanner",
        "book scanner", "film scanner"
    ],
    
    # Phone / Communication
    "phone": [
        "phone", "telephone", "ip phone", "voip phone", "desk phone",
        "conference phone", "cordless phone", "landline", "pbx phone",
        "video phone", "sip phone", "business phone"
    ],
    
    # Tablet
    "tablet": [
        "tablet", "ipad", "android tablet", "windows tablet", "tab",
        "slate", "tablet pc", "touchscreen tablet", "portable tablet",
        "drawing tablet", "graphics tablet"
    ],
    
    # Keyboard
    "keyboard": [
        "keyboard", "wireless keyboard", "mechanical keyboard",
        "gaming keyboard", "ergonomic keyboard", "bluetooth keyboard",
        "usb keyboard", "compact keyboard", "full size keyboard"
    ],
    
    # Mouse
    "mouse": [
        "mouse", "wireless mouse", "optical mouse", "gaming mouse",
        "ergonomic mouse", "bluetooth mouse", "trackball", "vertical mouse",
        "usb mouse", "computer mouse"
    ],
    
    # Headset / Audio
    "headset": [
        "headset", "headphones", "earphones", "wireless headset",
        "bluetooth headset", "gaming headset", "usb headset",
        "noise cancelling headphones", "earbuds", "audio headset"
    ],
    
    # Webcam
    "webcam": [
        "webcam", "web camera", "usb camera", "video camera",
        "conference camera", "streaming camera", "hd webcam",
        "4k webcam", "computer camera"
    ],
    
    # HDD / Storage
    "hdd": [
        "hdd", "hard drive", "hard disk", "internal hard drive",
        "external hard drive", "storage drive", "disk drive",
        "mechanical drive", "sata drive", "desktop hdd", "laptop hdd"
    ],
    
    # SSD
    "ssd": [
        "ssd", "solid state drive", "nvme", "nvme ssd", "sata ssd",
        "m.2 ssd", "flash storage", "flash drive", "solid state disk"
    ],
    
    # RAM / Memory
    "ram": [
        "ram", "memory", "ddr4", "ddr5", "dimm", "sodimm",
        "computer memory", "system memory", "memory module",
        "desktop memory", "laptop memory", "ecc memory"
    ],
    
    # Toner / Cartridge
    "toner": [
        "toner", "toner cartridge", "laser toner", "printer toner",
        "toner kit", "toner bottle", "black toner", "color toner",
        "compatible toner", "oem toner", "replacement toner"
    ],
    
    # Ink
    "ink": [
        "ink", "ink cartridge", "printer ink", "inkjet cartridge",
        "ink tank", "ink bottle", "refill ink", "compatible ink",
        "oem ink", "photo ink", "pigment ink", "dye ink"
    ],
    
    # Cable / Connector
    "cable": [
        "cable", "network cable", "ethernet cable", "hdmi cable",
        "usb cable", "power cable", "data cable", "patch cable",
        "fiber cable", "cat6 cable", "cat5 cable", "displayport cable"
    ],
    
    # Biometric
    "biometric": [
        "biometric", "fingerprint scanner", "biometric device",
        "attendance machine", "time attendance", "access control",
        "fingerprint reader", "face recognition", "biometric attendance",
        "punch machine", "time clock"
    ],
    
    # Intercom
    "intercom": [
        "intercom", "video intercom", "door phone", "video door phone",
        "door bell", "video doorbell", "entry system", "intercom system",
        "door intercom", "audio intercom"
    ],
    
    # AC / Air Conditioner
    "ac": [
        "ac", "air conditioner", "air conditioning", "split ac",
        "window ac", "cassette ac", "ductable ac", "hvac",
        "cooling system", "climate control", "inverter ac"
    ]
}

# Build reverse lookup: term -> canonical category
TERM_TO_CATEGORY = {}
for category, terms in DEVICE_CATEGORY_SYNONYMS.items():
    for term in terms:
        TERM_TO_CATEGORY[term.lower()] = category


def get_synonym_terms(query: str) -> list:
    """
    Get all synonym terms for a search query.
    
    Args:
        query: Search query string
    
    Returns:
        List of all related terms including the original query
    """
    query_lower = query.lower().strip()
    
    # Check if query matches any term
    if query_lower in TERM_TO_CATEGORY:
        category = TERM_TO_CATEGORY[query_lower]
        return DEVICE_CATEGORY_SYNONYMS[category]
    
    # Check for partial matches
    matched_categories = set()
    for term, category in TERM_TO_CATEGORY.items():
        if query_lower in term or term in query_lower:
            matched_categories.add(category)
    
    if matched_categories:
        all_terms = []
        for category in matched_categories:
            all_terms.extend(DEVICE_CATEGORY_SYNONYMS[category])
        return list(set(all_terms))
    
    return [query]


def build_synonym_regex(query: str) -> str:
    """
    Build a regex pattern that matches the query and all its synonyms.
    
    Args:
        query: Search query string
    
    Returns:
        Regex pattern string for MongoDB
    """
    terms = get_synonym_terms(query)
    
    # Escape special regex characters and join with OR
    escaped_terms = [term.replace("(", "\\(").replace(")", "\\)").replace("+", "\\+") for term in terms]
    
    # Also include the original query
    if query.lower() not in [t.lower() for t in terms]:
        escaped_terms.append(query)
    
    return "|".join(escaped_terms)


def expand_search_query(query: str) -> dict:
    """
    Expand a search query to include synonyms for MongoDB $or queries.
    
    Args:
        query: Search query string
    
    Returns:
        MongoDB query dict with synonym expansion
    """
    terms = get_synonym_terms(query)
    
    # Build regex that matches any of the terms
    regex_pattern = build_synonym_regex(query)
    
    return {
        "$regex": regex_pattern,
        "$options": "i"
    }


# Common brand aliases
BRAND_ALIASES = {
    "hp": ["hp", "hewlett packard", "hewlett-packard"],
    "dell": ["dell", "dell technologies", "dell inc"],
    "lenovo": ["lenovo", "thinkpad", "ideapad"],
    "apple": ["apple", "macbook", "imac", "mac"],
    "samsung": ["samsung", "samsung electronics"],
    "lg": ["lg", "lg electronics"],
    "asus": ["asus", "republic of gamers", "rog"],
    "acer": ["acer", "acer inc"],
    "microsoft": ["microsoft", "surface"],
    "cisco": ["cisco", "cisco systems"],
    "hikvision": ["hikvision", "hik vision", "hik-vision"],
    "dahua": ["dahua", "dahua technology"],
    "epson": ["epson", "seiko epson"],
    "canon": ["canon", "canon inc"],
    "brother": ["brother", "brother industries"],
    "xerox": ["xerox", "xerox corporation"],
    "sony": ["sony", "sony corporation"],
    "logitech": ["logitech", "logi"],
    "apc": ["apc", "schneider electric", "apc by schneider"],
    "seagate": ["seagate", "seagate technology"],
    "wd": ["wd", "western digital", "wdc"],
    "tplink": ["tp-link", "tplink", "tp link"],
    "dlink": ["d-link", "dlink", "d link"],
    "netgear": ["netgear", "net gear"],
    "ubiquiti": ["ubiquiti", "unifi", "ubnt"],
    "fortinet": ["fortinet", "fortigate"],
    "sophos": ["sophos", "sophos ltd"],
    "mikrotik": ["mikrotik", "mikro tik"]
}

# Build reverse lookup for brands
BRAND_ALIAS_LOOKUP = {}
for canonical, aliases in BRAND_ALIASES.items():
    for alias in aliases:
        BRAND_ALIAS_LOOKUP[alias.lower()] = canonical


def get_brand_variants(brand: str) -> list:
    """Get all variants of a brand name."""
    brand_lower = brand.lower().strip()
    if brand_lower in BRAND_ALIAS_LOOKUP:
        canonical = BRAND_ALIAS_LOOKUP[brand_lower]
        return BRAND_ALIASES[canonical]
    return [brand]
