"""
Engineer related models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from utils.helpers import get_ist_isoformat


class Engineer(BaseModel):
    """Service Engineer account"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    password_hash: str
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class EngineerCreate(BaseModel):
    name: str
    email: str
    phone: str
    password: str


class EngineerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


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
