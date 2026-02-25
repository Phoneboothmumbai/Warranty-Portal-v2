"""
Engineer related models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict
from utils.helpers import get_ist_isoformat


class DaySchedule(BaseModel):
    is_working: bool = True
    start: str = "09:00"
    end: str = "18:00"


class Engineer(BaseModel):
    """Service Engineer account"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: Optional[str] = None
    name: str
    email: str
    phone: str
    password_hash: str
    specialization: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    salary: Optional[float] = None
    working_hours: Dict[str, Dict] = Field(default_factory=lambda: {
        "monday": {"is_working": True, "start": "09:00", "end": "18:00"},
        "tuesday": {"is_working": True, "start": "09:00", "end": "18:00"},
        "wednesday": {"is_working": True, "start": "09:00", "end": "18:00"},
        "thursday": {"is_working": True, "start": "09:00", "end": "18:00"},
        "friday": {"is_working": True, "start": "09:00", "end": "18:00"},
        "saturday": {"is_working": True, "start": "09:00", "end": "14:00"},
        "sunday": {"is_working": False, "start": "09:00", "end": "18:00"},
    })
    holidays: List[str] = Field(default_factory=list)  # list of "YYYY-MM-DD"
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class EngineerCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    specialization: Optional[str] = None
    skills: Optional[List[str]] = None
    salary: Optional[float] = None
    working_hours: Optional[Dict[str, Dict]] = None
    holidays: Optional[List[str]] = None


class EngineerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None
    specialization: Optional[str] = None
    skills: Optional[List[str]] = None
    salary: Optional[float] = None
    working_hours: Optional[Dict[str, Dict]] = None
    holidays: Optional[List[str]] = None


class EngineerLogin(BaseModel):
    email: str
    password: str


class FieldVisit(BaseModel):
    """Field visit record for a service ticket"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_id: str
    engineer_id: str
    engineer_name: str
    device_id: str
    company_id: str
    # Check-in details
    check_in_time: Optional[str] = None
    check_in_location: Optional[str] = None
    check_in_notes: Optional[str] = None
    # Service details
    problem_found: Optional[str] = None
    action_taken: Optional[str] = None
    parts_used: List[dict] = Field(default_factory=list)  # [{name, quantity, serial}]
    photos: List[str] = Field(default_factory=list)  # List of file paths
    # Check-out details
    check_out_time: Optional[str] = None
    check_out_notes: Optional[str] = None
    customer_name: Optional[str] = None
    # Status
    status: str = "assigned"  # assigned, in_progress, completed
    created_at: str = Field(default_factory=get_ist_isoformat)


class ServiceReportSubmit(BaseModel):
    """Service report submission by engineer"""
    problem_found: str
    action_taken: str
    parts_used: Optional[List[dict]] = None
    notes: Optional[str] = None
