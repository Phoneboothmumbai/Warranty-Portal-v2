"""
Problem Master Model
====================
Master list of problem types/categories for service tickets.
Examples: Hardware Failure, Software Issue, Network Problem, etc.
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from utils.helpers import get_ist_isoformat


class ProblemMaster(BaseModel):
    """Problem/Issue type definition"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str  # Tenant scoping
    
    # Problem definition
    name: str  # e.g., "Hardware Failure", "Software Crash"
    code: Optional[str] = None  # Short code like "HW-FAIL"
    description: Optional[str] = None
    
    # Categorization
    category: str = "general"  # hardware, software, network, peripheral, other
    sub_category: Optional[str] = None
    
    # SLA/Priority hints
    default_priority: str = "medium"  # low, medium, high, critical
    estimated_resolution_hours: Optional[int] = None
    
    # Flags
    requires_onsite: bool = False  # Typically requires onsite visit
    requires_parts: bool = False   # Typically requires parts
    is_active: bool = True
    
    # Display
    sort_order: int = 0
    icon: Optional[str] = None  # Icon name for UI
    color: Optional[str] = None  # Color code for UI
    
    # Audit
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None


class ProblemMasterCreate(BaseModel):
    """Create a new problem type"""
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    category: str = "general"
    sub_category: Optional[str] = None
    default_priority: str = "medium"
    estimated_resolution_hours: Optional[int] = None
    requires_onsite: bool = False
    requires_parts: bool = False
    sort_order: int = 0
    icon: Optional[str] = None
    color: Optional[str] = None


class ProblemMasterUpdate(BaseModel):
    """Update problem type"""
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    default_priority: Optional[str] = None
    estimated_resolution_hours: Optional[int] = None
    requires_onsite: Optional[bool] = None
    requires_parts: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    icon: Optional[str] = None
    color: Optional[str] = None


# Default problem types to seed
DEFAULT_PROBLEMS = [
    {
        "name": "Hardware Failure",
        "code": "HW-FAIL",
        "category": "hardware",
        "default_priority": "high",
        "requires_onsite": True,
        "requires_parts": True,
        "icon": "wrench",
        "color": "#ef4444"
    },
    {
        "name": "Software Crash",
        "code": "SW-CRASH",
        "category": "software",
        "default_priority": "medium",
        "requires_onsite": False,
        "icon": "bug",
        "color": "#f59e0b"
    },
    {
        "name": "Network Connectivity",
        "code": "NET-CONN",
        "category": "network",
        "default_priority": "high",
        "requires_onsite": True,
        "icon": "wifi",
        "color": "#3b82f6"
    },
    {
        "name": "Printer Issue",
        "code": "PRT-ISS",
        "category": "peripheral",
        "default_priority": "low",
        "requires_onsite": True,
        "requires_parts": True,
        "icon": "printer",
        "color": "#8b5cf6"
    },
    {
        "name": "Preventive Maintenance",
        "code": "PM",
        "category": "maintenance",
        "default_priority": "low",
        "requires_onsite": True,
        "icon": "calendar-check",
        "color": "#22c55e"
    },
    {
        "name": "New Installation",
        "code": "INSTALL",
        "category": "installation",
        "default_priority": "medium",
        "requires_onsite": True,
        "icon": "package-plus",
        "color": "#06b6d4"
    },
    {
        "name": "User Training",
        "code": "TRAIN",
        "category": "support",
        "default_priority": "low",
        "requires_onsite": False,
        "icon": "graduation-cap",
        "color": "#64748b"
    },
    {
        "name": "Other",
        "code": "OTHER",
        "category": "other",
        "default_priority": "medium",
        "icon": "help-circle",
        "color": "#94a3b8"
    }
]
