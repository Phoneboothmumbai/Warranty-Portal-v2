"""
Company and User related models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from utils.helpers import get_ist_isoformat


class Company(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str = Field(default_factory=lambda: str(uuid.uuid4())[:8].upper())
    gst_number: Optional[str] = None
    address: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: str
    notification_email: Optional[str] = None
    amc_status: str = "not_applicable"
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class CompanyCreate(BaseModel):
    name: str
    code: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: str
    notification_email: Optional[str] = None
    amc_status: str = "not_applicable"
    notes: Optional[str] = None


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    gst_number: Optional[str] = None
    address: Optional[str] = None
    contact_name: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    notification_email: Optional[str] = None
    amc_status: Optional[str] = None
    notes: Optional[str] = None


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str = "employee"
    status: str = "active"
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class UserCreate(BaseModel):
    company_id: str
    name: str
    email: str
    phone: Optional[str] = None
    role: str = "employee"
    status: str = "active"


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class CompanyUser(BaseModel):
    """User accounts for company portal login"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    email: str
    password_hash: str
    name: str
    phone: Optional[str] = None
    role: str = "company_viewer"  # company_admin, company_viewer
    is_active: bool = True
    is_deleted: bool = False
    last_login: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None


class CompanyUserCreate(BaseModel):
    company_id: str
    email: str
    password: str
    name: str
    phone: Optional[str] = None
    role: str = "company_viewer"


class CompanyUserUpdate(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class CompanyUserRegister(BaseModel):
    """Self-registration for company users"""
    company_code: str
    email: str
    password: str
    name: str
    phone: Optional[str] = None


class CompanyLogin(BaseModel):
    email: str
    password: str


# ==================== Company Employees (Device Users) ====================

class CompanyEmployee(BaseModel):
    """Employees who can be assigned to devices (different from portal users)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    employee_id: Optional[str] = None  # Company's internal employee ID
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None  # Office location, floor, desk
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class CompanyEmployeeCreate(BaseModel):
    company_id: str
    employee_id: Optional[str] = None
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None


class CompanyEmployeeUpdate(BaseModel):
    employee_id: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    designation: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None
