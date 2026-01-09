"""
Warranty & Asset Tracking Portal - Main Server
==============================================
This is a refactored version with modular architecture.
Models, services, and utilities are now in separate modules.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import shutil
import json

# Import from modular structure
from config import ROOT_DIR, UPLOAD_DIR, OSTICKET_URL, OSTICKET_API_KEY, SECRET_KEY, ALGORITHM, IST
from database import db, client
from utils.helpers import get_ist_now, get_ist_isoformat, calculate_warranty_expiry, is_warranty_active, days_until_expiry
from services.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_admin, get_current_company_user, require_company_admin,
    log_audit, security
)
from services.osticket import create_osticket
from services.seeding import seed_default_masters, seed_default_supplies

# Import all models
from models.auth import Token, AdminUser, AdminLogin, AdminCreate
from models.common import MasterItem, MasterItemCreate, MasterItemUpdate, AuditLog, Settings, SettingsUpdate
from models.company import (
    Company, CompanyCreate, CompanyUpdate,
    User, UserCreate, UserUpdate,
    CompanyUser, CompanyUserCreate, CompanyUserUpdate,
    CompanyUserRegister, CompanyLogin
)
from models.device import (
    ConsumableItem, Device, DeviceCreate, DeviceUpdate,
    AssignmentHistory, Part, PartCreate, PartUpdate,
    ConsumableOrderItem, ConsumableOrder
)
from models.service import (
    ServiceTicket, ServiceTicketCreate, ServiceTicketComment,
    RenewalRequest, RenewalRequestCreate,
    ServiceAttachment, ServiceHistory, ServiceHistoryCreate, ServiceHistoryUpdate,
    ServicePartUsed
)
from models.amc import (
    AMC, AMCCreate, AMCUpdate,
    AMCCoverageIncludes, AMCExclusions, AMCEntitlements, AMCAssetMapping,
    AMCContract, AMCContractCreate, AMCContractUpdate,
    AMCUsageRecord, AMCDeviceAssignment, AMCDeviceAssignmentCreate,
    AMCBulkAssignmentPreview
)
from models.site import (
    Site, SiteCreate, SiteUpdate,
    DeploymentItem, Deployment, DeploymentCreate, DeploymentUpdate
)
from models.license import License, LicenseCreate, LicenseUpdate
from models.supplies import (
    SupplyCategory, SupplyCategoryCreate, SupplyCategoryUpdate,
    SupplyProduct, SupplyProductCreate, SupplyProductUpdate,
    SupplyOrderItem, SupplyOrderLocation, SupplyOrder
)

# Create the main app
app = FastAPI(title="Warranty & Asset Tracking Portal")
api_router = APIRouter(prefix="/api")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ==================== MODELS ====================

class Token(BaseModel):
    access_token: str
    token_type: str

class AdminUser(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    password_hash: str
    role: str = "admin"
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class AdminLogin(BaseModel):
    email: str
    password: str

class AdminCreate(BaseModel):
    email: str
    name: str
    password: str

# ==================== MASTER DATA MODELS ====================

class MasterItem(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str  # device_type, part_type, brand, service_type, condition, location, status
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None  # For hierarchical data like models under brands
    is_active: bool = True
    sort_order: int = 0
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class MasterItemCreate(BaseModel):
    type: str
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class MasterItemUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

# ==================== COMPANY & USER MODELS ====================

class Company(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    code: str = Field(default_factory=lambda: str(uuid.uuid4())[:8].upper())  # Unique code for self-registration
    gst_number: Optional[str] = None
    address: Optional[str] = None
    contact_name: str
    contact_email: str
    contact_phone: str
    notification_email: Optional[str] = None
    amc_status: str = "not_applicable"
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class CompanyCreate(BaseModel):
    name: str
    code: Optional[str] = None  # Auto-generated if not provided
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
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

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

# ==================== COMPANY USER MODELS (Portal Login) ====================

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
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())
    created_by: Optional[str] = None  # admin who created this user

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
    company_code: str  # Company must provide their code to register
    email: str
    password: str
    name: str
    phone: Optional[str] = None

class CompanyLogin(BaseModel):
    email: str
    password: str

# ==================== SERVICE TICKET MODELS ====================

class ServiceTicket(BaseModel):
    """Service tickets created by company users"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    ticket_number: str = Field(default_factory=lambda: f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    company_id: str
    device_id: str
    created_by: str  # company_user_id
    issue_category: str  # hardware, software, network, other
    priority: str = "medium"  # low, medium, high, critical
    subject: str
    description: str
    status: str = "open"  # open, in_progress, resolved, closed
    sla_status: str = "on_track"  # on_track, at_risk, breached
    attachments: List[str] = Field(default_factory=list)
    comments: List[dict] = Field(default_factory=list)
    assigned_to: Optional[str] = None  # admin user
    resolved_at: Optional[str] = None
    closed_at: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())
    updated_at: str = Field(default_factory=lambda: get_ist_isoformat())

class ServiceTicketCreate(BaseModel):
    device_id: str
    issue_category: str
    subject: str
    description: str
    attachments: List[str] = []

class ServiceTicketComment(BaseModel):
    comment: str
    attachments: List[str] = []

# ==================== RENEWAL REQUEST MODELS ====================

class RenewalRequest(BaseModel):
    """Warranty/AMC renewal requests from companies"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    request_number: str = Field(default_factory=lambda: f"REN-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    company_id: str
    request_type: str  # warranty_renewal, amc_renewal, amc_upgrade
    device_id: Optional[str] = None
    amc_contract_id: Optional[str] = None
    requested_by: str  # company_user_id
    notes: Optional[str] = None
    status: str = "pending"  # pending, reviewed, approved, rejected
    admin_notes: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class RenewalRequestCreate(BaseModel):
    request_type: str
    device_id: Optional[str] = None
    amc_contract_id: Optional[str] = None
    notes: Optional[str] = None

# ==================== DEVICE / ASSET MODELS ====================

class ConsumableItem(BaseModel):
    """Individual consumable item for a device (e.g., one color toner)"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Black Toner", "Cyan Ink"
    consumable_type: str  # Toner Cartridge, Ink Cartridge, Drum, etc.
    model_number: str  # e.g., HP 26A, Canon 325
    brand: Optional[str] = None
    color: Optional[str] = None  # Black, Cyan, Magenta, Yellow, etc.
    notes: Optional[str] = None

class Device(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    assigned_user_id: Optional[str] = None
    device_type: str
    brand: str
    model: str
    serial_number: str
    asset_tag: Optional[str] = None
    purchase_date: str
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    location: Optional[str] = None
    condition: str = "good"  # new, good, fair, poor
    status: str = "active"  # active, in_repair, retired, lost, scrapped
    notes: Optional[str] = None
    # Deployment source tracking
    source: str = "manual"  # manual, deployment
    deployment_id: Optional[str] = None
    deployment_item_index: Optional[int] = None
    site_id: Optional[str] = None
    # Consumable details (for printers, etc.) - Legacy single consumable
    consumable_type: Optional[str] = None  # Toner, Ink Cartridge, Drum, etc.
    consumable_model: Optional[str] = None  # e.g., HP 26A, Canon 325
    consumable_brand: Optional[str] = None  # Brand of consumable
    consumable_notes: Optional[str] = None  # Any special notes
    # NEW: Multiple consumables support
    consumables: List[dict] = Field(default_factory=list)  # List of ConsumableItem dicts
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class DeviceCreate(BaseModel):
    company_id: str
    assigned_user_id: Optional[str] = None
    device_type: str
    brand: str
    model: str
    serial_number: str
    asset_tag: Optional[str] = None
    purchase_date: str
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    location: Optional[str] = None
    condition: str = "good"
    status: str = "active"
    notes: Optional[str] = None
    # Deployment source tracking
    source: str = "manual"
    deployment_id: Optional[str] = None
    deployment_item_index: Optional[int] = None
    site_id: Optional[str] = None
    # Consumable details (for printers, etc.) - Legacy
    consumable_type: Optional[str] = None
    consumable_model: Optional[str] = None
    consumable_brand: Optional[str] = None
    consumable_notes: Optional[str] = None
    # NEW: Multiple consumables
    consumables: Optional[List[dict]] = None

class DeviceUpdate(BaseModel):
    company_id: Optional[str] = None
    assigned_user_id: Optional[str] = None
    device_type: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    asset_tag: Optional[str] = None
    purchase_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    vendor: Optional[str] = None
    warranty_end_date: Optional[str] = None
    location: Optional[str] = None
    condition: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    site_id: Optional[str] = None
    # Consumable details - Legacy
    consumable_type: Optional[str] = None
    consumable_model: Optional[str] = None
    consumable_brand: Optional[str] = None
    consumable_notes: Optional[str] = None
    # NEW: Multiple consumables
    consumables: Optional[List[dict]] = None

# ==================== ASSIGNMENT HISTORY ====================

class AssignmentHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    from_user_id: Optional[str] = None
    to_user_id: Optional[str] = None
    from_user_name: Optional[str] = None
    to_user_name: Optional[str] = None
    reason: Optional[str] = None
    changed_by: str
    changed_by_name: str
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

# ==================== CONSUMABLE ORDERS ====================

class ConsumableOrderItem(BaseModel):
    """Individual item in a consumable order"""
    consumable_id: str  # Reference to the consumable item in device.consumables
    name: str  # e.g., "Black Toner"
    consumable_type: str
    model_number: str
    brand: Optional[str] = None
    color: Optional[str] = None
    quantity: int = 1

class ConsumableOrder(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = Field(default_factory=lambda: f"ORD-{get_ist_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    company_id: str
    device_id: str
    requested_by: str  # company_user id
    requested_by_name: str
    requested_by_email: str
    # Legacy single consumable fields (for backward compatibility)
    consumable_type: Optional[str] = None
    consumable_model: Optional[str] = None
    quantity: int = 1
    # NEW: Multiple items support
    items: List[dict] = Field(default_factory=list)  # List of ConsumableOrderItem dicts
    notes: Optional[str] = None
    status: str = "pending"  # pending, processing, fulfilled, cancelled
    osticket_id: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

# ==================== SERVICE HISTORY ====================

class ServiceAttachment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    filename: str
    original_name: str
    file_type: str
    file_size: int
    uploaded_at: str = Field(default_factory=lambda: get_ist_isoformat())

class ServiceHistory(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    company_id: str
    site_id: Optional[str] = None  # Site reference
    deployment_id: Optional[str] = None  # Deployment reference
    service_date: str
    service_type: str  # repair, part_replacement, inspection, amc_visit, preventive_maintenance, other
    problem_reported: Optional[str] = None
    action_taken: str
    # Enhanced Parts Tracking
    parts_used: Optional[List[dict]] = None  # List of ServicePartUsed dicts
    parts_involved: Optional[List[dict]] = None  # Legacy: [{part_name, old_part, new_part, warranty_started}]
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    total_cost: Optional[float] = None
    # Warranty Impact
    warranty_impact: str = "not_applicable"  # started, extended, not_applicable
    extends_device_warranty: bool = False
    new_warranty_end_date: Optional[str] = None
    # AMC Impact
    consumes_amc_quota: bool = False
    amc_quota_type: Optional[str] = None  # onsite_visit, remote_support, preventive_maintenance
    technician_name: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None
    attachments: List[ServiceAttachment] = []
    # AMC Integration fields
    amc_contract_id: Optional[str] = None
    amc_covered: bool = False  # Is this service covered under AMC?
    billing_type: str = "covered"  # covered, chargeable
    chargeable_reason: Optional[str] = None  # Why is it chargeable? (e.g., "Hardware parts excluded")
    created_by: str
    created_by_name: str
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class ServiceHistoryCreate(BaseModel):
    device_id: str
    site_id: Optional[str] = None
    deployment_id: Optional[str] = None
    service_date: str
    service_type: str
    problem_reported: Optional[str] = None
    action_taken: str
    # Enhanced Parts
    parts_used: Optional[List[dict]] = None
    parts_involved: Optional[List[dict]] = None  # Legacy support
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    # Warranty Impact
    warranty_impact: str = "not_applicable"
    extends_device_warranty: bool = False
    new_warranty_end_date: Optional[str] = None
    # AMC Impact
    consumes_amc_quota: bool = False
    amc_quota_type: Optional[str] = None
    technician_name: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None
    # AMC fields
    amc_contract_id: Optional[str] = None
    billing_type: str = "covered"
    chargeable_reason: Optional[str] = None

class ServiceHistoryUpdate(BaseModel):
    service_date: Optional[str] = None
    service_type: Optional[str] = None
    problem_reported: Optional[str] = None
    action_taken: Optional[str] = None
    # Enhanced Parts
    parts_used: Optional[List[dict]] = None
    parts_involved: Optional[List[dict]] = None
    labor_cost: Optional[float] = None
    parts_cost: Optional[float] = None
    # Warranty Impact
    warranty_impact: Optional[str] = None
    extends_device_warranty: Optional[bool] = None
    new_warranty_end_date: Optional[str] = None
    # AMC Impact
    consumes_amc_quota: Optional[bool] = None
    amc_quota_type: Optional[str] = None
    technician_name: Optional[str] = None
    ticket_id: Optional[str] = None
    notes: Optional[str] = None
    site_id: Optional[str] = None
    deployment_id: Optional[str] = None
    # AMC fields
    amc_contract_id: Optional[str] = None
    billing_type: Optional[str] = None
    chargeable_reason: Optional[str] = None

# ==================== PARTS & AMC (existing) ====================

class Part(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    part_name: str
    serial_number: Optional[str] = None
    replaced_date: str
    warranty_months: int
    warranty_expiry_date: str
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class PartCreate(BaseModel):
    device_id: str
    part_name: str
    serial_number: Optional[str] = None
    replaced_date: str
    warranty_months: int
    notes: Optional[str] = None

class PartUpdate(BaseModel):
    part_name: Optional[str] = None
    serial_number: Optional[str] = None
    replaced_date: Optional[str] = None
    warranty_months: Optional[int] = None
    notes: Optional[str] = None

class AMC(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    start_date: str
    end_date: str
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

# ==================== AMC V2 (Enhanced) ====================

class AMCCoverageIncludes(BaseModel):
    onsite_support: bool = False
    remote_support: bool = False
    preventive_maintenance: bool = False

class AMCExclusions(BaseModel):
    hardware_parts: bool = True
    consumables: bool = True
    accessories: bool = True
    third_party_software: bool = True
    physical_liquid_damage: bool = True

class AMCEntitlements(BaseModel):
    onsite_visits_per_year: Optional[int] = None  # None = Unlimited
    remote_support_type: str = "unlimited"  # unlimited, count_based
    remote_support_count: Optional[int] = None
    preventive_maintenance_frequency: str = "quarterly"  # quarterly, half_yearly, yearly

class AMCAssetMapping(BaseModel):
    mapping_type: str = "all_company"  # all_company, selected_assets, device_types
    selected_asset_ids: List[str] = []
    selected_device_types: List[str] = []

class AMCContract(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    name: str  # e.g., "CoreCare AMC 2025-26"
    amc_type: str = "comprehensive"  # comprehensive, non_comprehensive, support_only
    start_date: str
    end_date: str
    coverage_includes: dict = Field(default_factory=lambda: AMCCoverageIncludes().model_dump())
    exclusions: dict = Field(default_factory=lambda: AMCExclusions().model_dump())
    entitlements: dict = Field(default_factory=lambda: AMCEntitlements().model_dump())
    asset_mapping: dict = Field(default_factory=lambda: AMCAssetMapping().model_dump())
    internal_notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())
    updated_at: str = Field(default_factory=lambda: get_ist_isoformat())

class AMCContractCreate(BaseModel):
    company_id: str
    name: str
    amc_type: str = "comprehensive"
    start_date: str
    end_date: str
    coverage_includes: Optional[dict] = None
    exclusions: Optional[dict] = None
    entitlements: Optional[dict] = None
    asset_mapping: Optional[dict] = None
    internal_notes: Optional[str] = None

class AMCContractUpdate(BaseModel):
    name: Optional[str] = None
    amc_type: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    coverage_includes: Optional[dict] = None
    exclusions: Optional[dict] = None
    entitlements: Optional[dict] = None
    asset_mapping: Optional[dict] = None
    internal_notes: Optional[str] = None

# AMC Visit/Service Usage Tracking
class AMCUsageRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amc_contract_id: str
    service_id: Optional[str] = None
    usage_type: str  # onsite_visit, remote_support, preventive_maintenance
    usage_date: str
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class AMCCreate(BaseModel):
    device_id: str
    start_date: str
    end_date: str
    notes: Optional[str] = None

class AMCUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None

# ==================== SITE / LOCATION ====================

class Site(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    name: str  # e.g., "Wadhwa 1620 – Mulund"
    site_type: str = "office"  # office, warehouse, site_project, branch
    address: Optional[str] = None
    city: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())
    updated_at: str = Field(default_factory=lambda: get_ist_isoformat())

class SiteCreate(BaseModel):
    company_id: str
    name: str
    site_type: str = "office"
    address: Optional[str] = None
    city: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None

class SiteUpdate(BaseModel):
    name: Optional[str] = None
    site_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    primary_contact_name: Optional[str] = None
    contact_number: Optional[str] = None
    contact_email: Optional[str] = None
    notes: Optional[str] = None

# ==================== DEPLOYMENT / INSTALLATION ====================

class DeploymentItem(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_type: str  # device, infrastructure, software, subscription
    category: str  # CCTV Camera, NVR, Access Point, Switch, Speaker, Computer, Software License, etc.
    brand: Optional[str] = None
    model: Optional[str] = None
    quantity: int = 1
    is_serialized: bool = False
    serial_numbers: List[str] = []  # Multiple serial numbers for serialized items
    zone_location: Optional[str] = None  # Floor 3 – Reception
    installation_date: Optional[str] = None
    warranty_start_date: Optional[str] = None
    warranty_end_date: Optional[str] = None
    warranty_type: Optional[str] = None  # manufacturer, installer, amc_linked
    amc_contract_id: Optional[str] = None
    notes: Optional[str] = None
    # Auto-created device IDs for serialized items
    linked_device_ids: List[str] = []

class Deployment(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    site_id: str
    name: str  # e.g., "Phase 1 Infra Deployment"
    deployment_date: str
    installed_by: Optional[str] = None  # Internal / Vendor name
    notes: Optional[str] = None
    items: List[dict] = []  # List of DeploymentItem dicts
    is_deleted: bool = False
    created_by: str
    created_by_name: str
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())
    updated_at: str = Field(default_factory=lambda: get_ist_isoformat())

class DeploymentCreate(BaseModel):
    company_id: str
    site_id: str
    name: str
    deployment_date: str
    installed_by: Optional[str] = None
    notes: Optional[str] = None
    items: List[dict] = []

class DeploymentUpdate(BaseModel):
    name: Optional[str] = None
    deployment_date: Optional[str] = None
    installed_by: Optional[str] = None
    notes: Optional[str] = None
    items: Optional[List[dict]] = None

# ==================== SOFTWARE & LICENSE MODULE ====================

class License(BaseModel):
    """Software License entity for tracking software assets and renewals"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    software_name: str  # e.g., "Windows 11 Pro", "Microsoft 365 Business", "Antivirus"
    vendor: Optional[str] = None  # Microsoft, Adobe, etc.
    license_type: str = "subscription"  # perpetual, subscription
    license_key: Optional[str] = None  # Masked/encrypted in responses
    seats: int = 1  # Number of allowed installations
    assigned_to_type: str = "company"  # company, devices, users
    assigned_device_ids: List[str] = []  # If assigned to specific devices
    assigned_user_ids: List[str] = []  # If assigned to specific users
    start_date: str
    end_date: Optional[str] = None  # Null for perpetual licenses
    purchase_cost: Optional[float] = None
    renewal_cost: Optional[float] = None
    auto_renew: bool = False
    renewal_reminder_days: int = 30  # Days before expiry to send reminder
    status: str = "active"  # active, expiring, expired, cancelled
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())
    updated_at: str = Field(default_factory=lambda: get_ist_isoformat())

class LicenseCreate(BaseModel):
    company_id: str
    software_name: str
    vendor: Optional[str] = None
    license_type: str = "subscription"
    license_key: Optional[str] = None
    seats: int = 1
    assigned_to_type: str = "company"
    assigned_device_ids: List[str] = []
    assigned_user_ids: List[str] = []
    start_date: str
    end_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    renewal_cost: Optional[float] = None
    auto_renew: bool = False
    renewal_reminder_days: int = 30
    notes: Optional[str] = None

class LicenseUpdate(BaseModel):
    software_name: Optional[str] = None
    vendor: Optional[str] = None
    license_type: Optional[str] = None
    license_key: Optional[str] = None
    seats: Optional[int] = None
    assigned_to_type: Optional[str] = None
    assigned_device_ids: Optional[List[str]] = None
    assigned_user_ids: Optional[List[str]] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    purchase_cost: Optional[float] = None
    renewal_cost: Optional[float] = None
    auto_renew: Optional[bool] = None
    renewal_reminder_days: Optional[int] = None
    status: Optional[str] = None
    notes: Optional[str] = None

# ==================== AMC DEVICE ASSIGNMENT (Join Table) ====================

class AMCDeviceAssignment(BaseModel):
    """Join table for AMC Contract to Device assignments"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amc_contract_id: str
    device_id: str
    coverage_start: str
    coverage_end: str
    coverage_source: str = "manual"  # manual, bulk_upload, filter_based
    status: str = "active"  # active, expired, suspended
    notes: Optional[str] = None
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())
    created_by: Optional[str] = None

class AMCDeviceAssignmentCreate(BaseModel):
    amc_contract_id: str
    device_id: str
    coverage_start: str
    coverage_end: str
    coverage_source: str = "manual"
    notes: Optional[str] = None

class AMCBulkAssignmentPreview(BaseModel):
    amc_contract_id: str
    device_identifiers: List[str]  # Serial numbers or asset tags
    coverage_start: str
    coverage_end: str

# ==================== SERVICE RECORD PARTS (Enhanced) ====================

class ServicePartUsed(BaseModel):
    """Part used during a service record"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    part_name: str
    part_type: str  # hardware, software
    serial_number: Optional[str] = None
    quantity: int = 1
    replacement_type: str = "new"  # new, refurbished, temporary
    warranty_inherited_from_amc: bool = False
    warranty_start_date: Optional[str] = None
    warranty_end_date: Optional[str] = None
    linked_device_id: Optional[str] = None
    cost: Optional[float] = None
    notes: Optional[str] = None

# ==================== AUDIT LOG (Hidden) ====================

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str  # company, user, device, part, amc, service, master
    entity_id: str
    action: str  # create, update, delete, assign
    changes: dict  # {field: {old: x, new: y}}
    performed_by: str
    performed_by_name: str
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

# ==================== SETTINGS ====================

class Settings(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = "settings"
    logo_url: Optional[str] = None
    logo_base64: Optional[str] = None
    accent_color: str = "#0F62FE"
    company_name: str = "Warranty Portal"
    updated_at: str = Field(default_factory=lambda: get_ist_isoformat())

class SettingsUpdate(BaseModel):
    logo_url: Optional[str] = None
    logo_base64: Optional[str] = None
    accent_color: Optional[str] = None
    company_name: Optional[str] = None

# ==================== OFFICE SUPPLIES MODELS ====================

class SupplyCategory(BaseModel):
    """Category for office supplies (Stationery, Consumables, IT/Misc)"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    icon: Optional[str] = None  # emoji or icon name
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class SupplyCategoryCreate(BaseModel):
    name: str
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: int = 0

class SupplyCategoryUpdate(BaseModel):
    name: Optional[str] = None
    icon: Optional[str] = None
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None

class SupplyProduct(BaseModel):
    """Product within a supply category"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    category_id: str
    name: str
    description: Optional[str] = None
    unit: str = "piece"  # piece, pack, box, ream, etc.
    internal_notes: Optional[str] = None  # admin-only notes (vendor, cost, availability)
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

class SupplyProductCreate(BaseModel):
    category_id: str
    name: str
    description: Optional[str] = None
    unit: str = "piece"
    internal_notes: Optional[str] = None

class SupplyProductUpdate(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None
    internal_notes: Optional[str] = None
    is_active: Optional[bool] = None

class SupplyOrderItem(BaseModel):
    """Individual item in a supply order"""
    product_id: str
    product_name: str
    category_name: str
    quantity: int
    unit: str

class SupplyOrderLocation(BaseModel):
    """Delivery location for supply order"""
    type: str = "existing"  # existing (site) or new
    site_id: Optional[str] = None
    site_name: Optional[str] = None
    # For new locations
    address: Optional[str] = None
    city: Optional[str] = None
    pincode: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None

class SupplyOrder(BaseModel):
    """Office supplies order"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_number: str = Field(default_factory=lambda: f"SUP-{get_ist_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}")
    company_id: str
    company_name: str
    requested_by: str  # company_user id
    requested_by_name: str
    requested_by_email: str
    requested_by_phone: Optional[str] = None
    # Delivery location
    delivery_location: dict  # SupplyOrderLocation as dict
    # Order items
    items: List[dict]  # List of SupplyOrderItem as dicts
    notes: Optional[str] = None  # Special instructions
    # Status tracking
    status: str = "requested"  # requested, approved, processing, delivered, cancelled
    osticket_id: Optional[str] = None
    # Admin fields
    admin_notes: Optional[str] = None
    processed_by: Optional[str] = None
    processed_at: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=lambda: get_ist_isoformat())

# ==================== AUTH HELPERS ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    admin = await db.admins.find_one({"email": email}, {"_id": 0})
    if admin is None:
        raise credentials_exception
    return admin

async def get_current_company_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current company portal user from JWT token"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        if user_id is None or user_type != "company_user":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = await db.company_users.find_one(
        {"id": user_id, "is_active": True, "is_deleted": {"$ne": True}}, 
        {"_id": 0, "password_hash": 0}
    )
    if user is None:
        raise credentials_exception
    return user

def require_company_admin(user: dict = Depends(get_current_company_user)):
    """Dependency to require company_admin role"""
    if user.get("role") != "company_admin":
        raise HTTPException(status_code=403, detail="Admin role required for this action")
    return user

# ==================== AUDIT HELPER ====================

async def log_audit(entity_type: str, entity_id: str, action: str, changes: dict, admin: dict):
    """Log audit entry - silent, no failures"""
    try:
        audit = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            changes=changes,
            performed_by=admin.get("id", "unknown"),
            performed_by_name=admin.get("name", "Unknown")
        )
        await db.audit_logs.insert_one(audit.model_dump())
    except Exception as e:
        logger.error(f"Audit log failed: {e}")

# ==================== UTILITY FUNCTIONS ====================

def calculate_warranty_expiry(replaced_date: str, warranty_months: int) -> str:
    date = datetime.fromisoformat(replaced_date.replace('Z', '+00:00'))
    expiry = date + timedelta(days=warranty_months * 30)
    return expiry.strftime('%Y-%m-%d')

def is_warranty_active(expiry_date: str) -> bool:
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        # Compare without timezone info
        today = get_ist_now().replace(tzinfo=None)
        return today.date() <= expiry.date()
    except:
        return False

def days_until_expiry(expiry_date: str) -> int:
    try:
        expiry = datetime.strptime(expiry_date, '%Y-%m-%d')
        today = get_ist_now().replace(tzinfo=None)
        return (expiry.date() - today.date()).days
    except:
        return -9999

# ==================== OSTICKET INTEGRATION ====================

async def create_osticket(
    email: str,
    name: str,
    subject: str,
    message: str,
    phone: str = "",
    priority_id: Optional[int] = None
) -> dict:
    """
    Create a ticket in osTicket system.
    Returns dict with 'ticket_id' on success, or 'error' on failure.
    Note: osTicket API keys are IP-restricted. This will only work from the configured server IP.
    """
    if not OSTICKET_URL or not OSTICKET_API_KEY:
        logger.warning("osTicket not configured - skipping ticket sync")
        return {"error": "osTicket not configured", "ticket_id": None}
    
    try:
        api_url = f"{OSTICKET_URL.rstrip('/')}/api/tickets.json"
        
        logger.info(f"Creating osTicket: URL={api_url}, Email={email}, Subject={subject[:50]}...")
        
        payload = {
            "alert": True,
            "autorespond": True,
            "source": "API",
            "name": name,
            "email": email,
            "subject": subject,
            "message": f"data:text/html,{message}",
        }
        
        if phone:
            payload["phone"] = phone
        
        if priority_id:
            payload["priority"] = priority_id
        
        headers = {
            "X-API-Key": OSTICKET_API_KEY,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(api_url, json=payload, headers=headers)
            
            logger.info(f"osTicket response: status={response.status_code}, body={response.text[:200]}")
            
            if response.status_code == 201:
                # Success - response body contains the ticket number
                osticket_id = response.text.strip()
                logger.info(f"osTicket created successfully: {osticket_id}")
                return {"ticket_id": osticket_id, "error": None}
            elif response.status_code == 401:
                # API key is IP-restricted - log but don't fail
                error_msg = f"API key rejected (IP restriction): {response.text}"
                logger.warning(f"osTicket: {error_msg}")
                return {"ticket_id": None, "error": error_msg}
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(f"osTicket: {error_msg}")
                return {"ticket_id": None, "error": error_msg}
                
    except Exception as e:
        error_msg = f"Connection failed: {str(e)}"
        logger.error(f"osTicket integration failed: {error_msg}")
        return {"ticket_id": None, "error": error_msg}

# ==================== SEED DEFAULT MASTERS ====================

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

# ==================== PUBLIC ENDPOINTS ====================

@api_router.get("/")
async def root():
    return {"message": "Warranty & Asset Tracking Portal API"}

@api_router.get("/settings/public")
async def get_public_settings():
    settings = await db.settings.find_one({"id": "settings"}, {"_id": 0})
    if not settings:
        settings = Settings().model_dump()
    return {
        "logo_url": settings.get("logo_url"),
        "logo_base64": settings.get("logo_base64"),
        "accent_color": settings.get("accent_color", "#0F62FE"),
        "company_name": settings.get("company_name", "Warranty Portal")
    }

@api_router.get("/masters/public")
async def get_public_masters(
    master_type: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """Get active masters for public forms with optional search"""
    query = {"is_active": True}
    if master_type:
        query["type"] = master_type
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"code": search_regex}
        ]
    
    masters = await db.masters.find(query, {"_id": 0}).sort("sort_order", 1).to_list(limit)
    
    # Add label for SmartSelect compatibility
    for m in masters:
        m["label"] = m["name"]
    
    return masters

@api_router.get("/warranty/search")
async def search_warranty(q: str):
    """
    Search warranty by serial number or asset tag
    
    P0 FIX - AMC OVERRIDE RULE:
    IF device has ACTIVE AMC:
      → Show AMC coverage (ignore device warranty expiry)
    ELSE:
      → Show device warranty
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query too short")
    
    q = q.strip()
    
    # Search device by serial number or asset tag
    device = await db.devices.find_one(
        {"$and": [
            {"is_deleted": {"$ne": True}},
            {"$or": [
                {"serial_number": {"$regex": f"^{q}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{q}$", "$options": "i"}}
            ]}
        ]},
        {"_id": 0}
    )
    
    if not device:
        raise HTTPException(status_code=404, detail="No records found for this Serial Number / Asset Tag")
    
    # Check if device is retired/scrapped
    if device.get("status") in ["retired", "scrapped"]:
        return {
            "device": {
                "id": device.get("id"),
                "device_type": device.get("device_type"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "asset_tag": device.get("asset_tag"),
                "status": device.get("status"),
                "message": "This asset is no longer active"
            },
            "company_name": None,
            "assigned_user": None,
            "parts": [],
            "amc": None,
            "amc_contract": None,
            "coverage_source": None,
            "service_count": 0
        }
    
    # Get company info (only name, no sensitive data)
    company = await db.companies.find_one({"id": device["company_id"], "is_deleted": {"$ne": True}}, {"_id": 0, "name": 1})
    company_name = company.get("name") if company else "Unknown"
    
    # Get assigned user (only name, no sensitive data)
    assigned_user = None
    if device.get("assigned_user_id"):
        user = await db.users.find_one({"id": device["assigned_user_id"], "is_deleted": {"$ne": True}}, {"_id": 0, "name": 1})
        assigned_user = user.get("name") if user else None
    
    # Calculate device warranty status
    device_warranty_expiry = device.get("warranty_end_date")
    device_warranty_active = is_warranty_active(device_warranty_expiry) if device_warranty_expiry else False
    
    # P0 FIX: Check AMC from amc_device_assignments JOIN (not old amc collection)
    active_amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device["id"],
        "status": "active"
    }, {"_id": 0})
    
    amc_contract_info = None
    amc_coverage_active = False
    coverage_source = "device_warranty"  # Default
    effective_coverage_end = device_warranty_expiry
    
    if active_amc_assignment:
        # Check if AMC coverage is still valid
        amc_coverage_active = is_warranty_active(active_amc_assignment.get("coverage_end", ""))
        
        if amc_coverage_active:
            # Get full AMC contract details
            amc_contract = await db.amc_contracts.find_one({
                "id": active_amc_assignment["amc_contract_id"],
                "is_deleted": {"$ne": True}
            }, {"_id": 0})
            
            if amc_contract:
                coverage_source = "amc_contract"
                effective_coverage_end = active_amc_assignment.get("coverage_end")
                
                amc_contract_info = {
                    "contract_id": amc_contract["id"],
                    "name": amc_contract.get("name"),
                    "amc_type": amc_contract.get("amc_type"),
                    "coverage_start": active_amc_assignment.get("coverage_start"),
                    "coverage_end": active_amc_assignment.get("coverage_end"),
                    "active": True,
                    "coverage_includes": amc_contract.get("coverage_includes"),
                    "entitlements": amc_contract.get("entitlements")
                }
    
    # Also check legacy AMC collection for backward compatibility
    legacy_amc = await db.amc.find_one({"device_id": device["id"], "is_deleted": {"$ne": True}}, {"_id": 0})
    legacy_amc_info = None
    if legacy_amc:
        legacy_amc_active = is_warranty_active(legacy_amc.get("end_date", ""))
        legacy_amc_info = {
            "start_date": legacy_amc.get("start_date"),
            "end_date": legacy_amc.get("end_date"),
            "active": legacy_amc_active
        }
        
        # If no active AMC contract but legacy AMC is active, use it
        if not amc_coverage_active and legacy_amc_active:
            coverage_source = "legacy_amc"
            effective_coverage_end = legacy_amc.get("end_date")
    
    # Get parts and their warranty status
    parts_cursor = db.parts.find({"device_id": device["id"], "is_deleted": {"$ne": True}}, {"_id": 0})
    parts = []
    async for part in parts_cursor:
        part_warranty_active = is_warranty_active(part.get("warranty_expiry_date", ""))
        parts.append({
            "part_name": part.get("part_name"),
            "replaced_date": part.get("replaced_date"),
            "warranty_months": part.get("warranty_months"),
            "warranty_expiry_date": part.get("warranty_expiry_date"),
            "warranty_active": part_warranty_active
        })
    
    # Get service history count (public sees count, not details)
    service_count = await db.service_history.count_documents({"device_id": device["id"]})
    
    # Determine final warranty status based on AMC OVERRIDE RULE
    # AMC takes priority over device warranty
    final_warranty_active = amc_coverage_active or device_warranty_active
    if amc_coverage_active:
        final_warranty_active = True  # AMC overrides even if device warranty expired
    
    return {
        "device": {
            "id": device.get("id"),
            "device_type": device.get("device_type"),
            "brand": device.get("brand"),
            "model": device.get("model"),
            "serial_number": device.get("serial_number"),
            "asset_tag": device.get("asset_tag"),
            "purchase_date": device.get("purchase_date"),
            "warranty_end_date": device_warranty_expiry,
            "warranty_active": final_warranty_active,
            "device_warranty_active": device_warranty_active,  # Original device warranty status
            "condition": device.get("condition"),
            "status": device.get("status")
        },
        "company_name": company_name,
        "assigned_user": assigned_user,
        "parts": parts,
        "amc": legacy_amc_info,  # Legacy AMC for backward compatibility
        "amc_contract": amc_contract_info,  # New AMC contract info
        "coverage_source": coverage_source,  # "amc_contract", "legacy_amc", or "device_warranty"
        "effective_coverage_end": effective_coverage_end,
        "service_count": service_count
    }

@api_router.get("/warranty/pdf/{serial_number}")
async def generate_warranty_pdf(serial_number: str):
    """Generate PDF warranty report"""
    device = await db.devices.find_one(
        {"$and": [
            {"is_deleted": {"$ne": True}},
            {"$or": [
                {"serial_number": {"$regex": f"^{serial_number}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{serial_number}$", "$options": "i"}}
            ]}
        ]},
        {"_id": 0}
    )
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    company = await db.companies.find_one({"id": device["company_id"]}, {"_id": 0, "name": 1})
    company_name = company.get("name") if company else "Unknown"
    
    parts_cursor = db.parts.find({"device_id": device["id"], "is_deleted": {"$ne": True}}, {"_id": 0})
    parts = []
    async for part in parts_cursor:
        parts.append(part)
    
    # P0 FIX: Check AMC from amc_device_assignments JOIN (not old amc collection)
    active_amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device["id"],
        "status": "active"
    }, {"_id": 0})
    
    amc_contract_info = None
    if active_amc_assignment:
        # Check if AMC coverage is still valid
        if is_warranty_active(active_amc_assignment.get("coverage_end", "")):
            # Get full AMC contract details
            amc_contract = await db.amc_contracts.find_one({
                "id": active_amc_assignment["amc_contract_id"],
                "is_deleted": {"$ne": True}
            }, {"_id": 0})
            
            if amc_contract:
                amc_contract_info = {
                    "name": amc_contract.get("name"),
                    "amc_type": amc_contract.get("amc_type"),
                    "coverage_start": active_amc_assignment.get("coverage_start"),
                    "coverage_end": active_amc_assignment.get("coverage_end"),
                    "coverage_includes": amc_contract.get("coverage_includes"),
                    "entitlements": amc_contract.get("entitlements")
                }
    
    settings = await db.settings.find_one({"id": "settings"}, {"_id": 0})
    portal_name = settings.get("company_name", "Warranty Portal") if settings else "Warranty Portal"
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=20, textColor=colors.HexColor('#0F172A'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=10, textColor=colors.HexColor('#0F172A'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=5, textColor=colors.HexColor('#64748B'))
    
    story.append(Paragraph(f"{portal_name} - Warranty Report", title_style))
    story.append(Paragraph(f"Generated: {get_ist_now().strftime('%d %B %Y, %H:%M')}", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Device Information", heading_style))
    device_data = [
        ["Device Type", device.get("device_type", "-")],
        ["Brand", device.get("brand", "-")],
        ["Model", device.get("model", "-")],
        ["Serial Number", device.get("serial_number", "-")],
        ["Asset Tag", device.get("asset_tag", "-") or "-"],
        ["Company", company_name],
        ["Purchase Date", device.get("purchase_date", "-")],
        ["Condition", device.get("condition", "-").title()],
        ["Warranty Expiry", device.get("warranty_end_date", "-") or "Not specified"],
        ["Warranty Status", "Active" if is_warranty_active(device.get("warranty_end_date", "")) else "Expired / Not Covered"]
    ]
    
    device_table = Table(device_data, colWidths=[2*inch, 4*inch])
    device_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(device_table)
    story.append(Spacer(1, 20))
    
    if parts:
        story.append(Paragraph("Parts Warranty Status", heading_style))
        parts_data = [["Part Name", "Replaced Date", "Warranty", "Expiry", "Status"]]
        for part in parts:
            status = "Active" if is_warranty_active(part.get("warranty_expiry_date", "")) else "Expired"
            parts_data.append([
                part.get("part_name", "-"),
                part.get("replaced_date", "-"),
                f"{part.get('warranty_months', 0)} months",
                part.get("warranty_expiry_date", "-"),
                status
            ])
        
        parts_table = Table(parts_data, colWidths=[1.5*inch, 1.2*inch, 1*inch, 1.2*inch, 1*inch])
        parts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F62FE')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        story.append(parts_table)
        story.append(Spacer(1, 20))
    
    story.append(Paragraph("AMC / Service Coverage", heading_style))
    if amc_contract_info:
        amc_type_display = (amc_contract_info.get("amc_type") or "standard").replace("_", " ").title()
        coverage_includes = amc_contract_info.get("coverage_includes", {})
        
        # Build coverage details string
        coverage_items = []
        if coverage_includes.get("onsite_support"):
            coverage_items.append("Onsite Support")
        if coverage_includes.get("remote_support"):
            coverage_items.append("Remote Support")
        if coverage_includes.get("preventive_maintenance"):
            coverage_items.append("Preventive Maintenance")
        coverage_str = ", ".join(coverage_items) if coverage_items else "Standard Coverage"
        
        # Build entitlements string
        entitlements = amc_contract_info.get("entitlements", {})
        entitlement_items = []
        if entitlements.get("onsite_visits_per_year"):
            visits = entitlements["onsite_visits_per_year"]
            entitlement_items.append(f"{visits} Onsite Visits/Year" if visits != -1 else "Unlimited Onsite Visits")
        if entitlements.get("remote_support_count"):
            remote = entitlements["remote_support_count"]
            entitlement_items.append(f"{remote} Remote Support Sessions" if remote != -1 else "Unlimited Remote Support")
        entitlement_str = ", ".join(entitlement_items) if entitlement_items else "-"
        
        amc_data = [
            ["Contract Name", amc_contract_info.get("name", "-")],
            ["AMC Type", amc_type_display],
            ["Coverage Start", amc_contract_info.get("coverage_start", "-")],
            ["Coverage End", amc_contract_info.get("coverage_end", "-")],
            ["Status", "Active"],
            ["Coverage Includes", coverage_str],
            ["Entitlements", entitlement_str]
        ]
    else:
        amc_data = [["Status", "No active AMC found for this device"]]
    
    amc_table = Table(amc_data, colWidths=[2*inch, 4*inch])
    amc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(amc_table)
    story.append(Spacer(1, 30))
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#94A3B8'))
    story.append(Paragraph("This document is auto-generated and valid as of the date mentioned above.", footer_style))
    story.append(Paragraph("For any discrepancies, please contact support.", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"warranty_report_{serial_number}_{get_ist_now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/login", response_model=Token)
async def admin_login(login: AdminLogin):
    admin = await db.admins.find_one({"email": login.email}, {"_id": 0})
    if not admin or not verify_password(login.password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": admin["email"]})
    return {"access_token": access_token, "token_type": "bearer"}

@api_router.get("/auth/me")
async def get_current_admin_info(admin: dict = Depends(get_current_admin)):
    return {
        "id": admin.get("id"),
        "email": admin.get("email"),
        "name": admin.get("name"),
        "role": admin.get("role")
    }

@api_router.post("/auth/setup")
async def setup_first_admin(admin_data: AdminCreate):
    existing = await db.admins.find_one({}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Admin already exists. Use login.")
    
    admin = AdminUser(
        email=admin_data.email,
        name=admin_data.name,
        password_hash=get_password_hash(admin_data.password)
    )
    await db.admins.insert_one(admin.model_dump())
    
    # Seed default masters
    await seed_default_masters()
    
    return {"message": "Admin created successfully", "email": admin.email}

# ==================== MASTER DATA ENDPOINTS ====================

@api_router.get("/admin/masters")
async def list_masters(master_type: Optional[str] = None, include_inactive: bool = False, admin: dict = Depends(get_current_admin)):
    query = {}
    if master_type:
        query["type"] = master_type
    if not include_inactive:
        query["is_active"] = True
    
    masters = await db.masters.find(query, {"_id": 0}).sort([("type", 1), ("sort_order", 1)]).to_list(1000)
    return masters

@api_router.post("/admin/masters")
async def create_master(item: MasterItemCreate, admin: dict = Depends(get_current_admin)):
    # Check for duplicate
    existing = await db.masters.find_one({"type": item.type, "name": item.name}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail=f"Master item '{item.name}' already exists for type '{item.type}'")
    
    master = MasterItem(**item.model_dump())
    await db.masters.insert_one(master.model_dump())
    await log_audit("master", master.id, "create", {"data": item.model_dump()}, admin)
    return master.model_dump()

@api_router.put("/admin/masters/{master_id}")
async def update_master(master_id: str, updates: MasterItemUpdate, admin: dict = Depends(get_current_admin)):
    existing = await db.masters.find_one({"id": master_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Master item not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # Track changes for audit
    changes = {}
    for k, v in update_data.items():
        if existing.get(k) != v:
            changes[k] = {"old": existing.get(k), "new": v}
    
    result = await db.masters.update_one({"id": master_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Master item not found")
    
    await log_audit("master", master_id, "update", changes, admin)
    return await db.masters.find_one({"id": master_id}, {"_id": 0})

@api_router.delete("/admin/masters/{master_id}")
async def disable_master(master_id: str, admin: dict = Depends(get_current_admin)):
    """Disable master (soft delete - preserve history)"""
    result = await db.masters.update_one({"id": master_id}, {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Master item not found")
    
    await log_audit("master", master_id, "disable", {"is_active": {"old": True, "new": False}}, admin)
    return {"message": "Master item disabled"}

@api_router.post("/admin/masters/seed")
async def seed_masters(admin: dict = Depends(get_current_admin)):
    """Force re-seed default masters"""
    await seed_default_masters()
    return {"message": "Default masters seeded"}

@api_router.post("/admin/masters/quick-create")
async def quick_create_master(item: MasterItemCreate, admin: dict = Depends(get_current_admin)):
    """Quick create master item (for inline creation from dropdowns)"""
    # Check for duplicate
    existing = await db.masters.find_one({"type": item.type, "name": item.name}, {"_id": 0})
    if existing:
        # Return existing item instead of error (idempotent)
        return existing
    
    # Get next sort order
    last = await db.masters.find_one({"type": item.type}, {"_id": 0}, sort=[("sort_order", -1)])
    next_order = (last.get("sort_order", 0) + 1) if last else 1
    
    master_data = item.model_dump()
    master_data["sort_order"] = next_order
    master = MasterItem(**master_data)
    await db.masters.insert_one(master.model_dump())
    await log_audit("master", master.id, "quick_create", {"data": item.model_dump()}, admin)
    
    result = master.model_dump()
    # Add label for SmartSelect compatibility
    result["label"] = result["name"]
    return result

# ==================== ADMIN ENDPOINTS - COMPANIES ====================

@api_router.get("/admin/companies")
async def list_companies(
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List companies with optional search support"""
    query = {"is_deleted": {"$ne": True}}
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"contact_name": search_regex},
            {"contact_email": search_regex},
            {"gst_number": search_regex}
        ]
    
    skip = (page - 1) * limit
    companies = await db.companies.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Add label field for SmartSelect compatibility
    for c in companies:
        c["label"] = c["name"]
    
    return companies

@api_router.post("/admin/companies")
async def create_company(company_data: CompanyCreate, admin: dict = Depends(get_current_admin)):
    company = Company(**company_data.model_dump())
    await db.companies.insert_one(company.model_dump())
    await log_audit("company", company.id, "create", {"data": company_data.model_dump()}, admin)
    result = company.model_dump()
    result["label"] = result["name"]
    return result

@api_router.post("/admin/companies/quick-create")
async def quick_create_company(company_data: CompanyCreate, admin: dict = Depends(get_current_admin)):
    """Quick create company (for inline creation from dropdowns)"""
    # Check if company with same name exists
    existing = await db.companies.find_one(
        {"name": {"$regex": f"^{company_data.name}$", "$options": "i"}, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if existing:
        # Return existing instead of error (idempotent)
        existing["label"] = existing["name"]
        return existing
    
    company = Company(**company_data.model_dump())
    await db.companies.insert_one(company.model_dump())
    await log_audit("company", company.id, "quick_create", {"data": company_data.model_dump()}, admin)
    
    result = company.model_dump()
    result["label"] = result["name"]
    return result

@api_router.get("/admin/companies/{company_id}")
async def get_company(company_id: str, admin: dict = Depends(get_current_admin)):
    company = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@api_router.put("/admin/companies/{company_id}")
async def update_company(company_id: str, updates: CompanyUpdate, admin: dict = Depends(get_current_admin)):
    existing = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.companies.update_one({"id": company_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    await log_audit("company", company_id, "update", changes, admin)
    return await db.companies.find_one({"id": company_id}, {"_id": 0})

@api_router.delete("/admin/companies/{company_id}")
async def delete_company(company_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.companies.update_one({"id": company_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Soft delete related users
    await db.users.update_many({"company_id": company_id}, {"$set": {"is_deleted": True}})
    await log_audit("company", company_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Company archived"}

# ==================== BULK IMPORT ENDPOINTS ====================

@api_router.post("/admin/bulk-import/companies")
async def bulk_import_companies(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import companies from CSV data"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            # Check required fields
            if not record.get("name"):
                errors.append({"row": idx + 2, "message": "Company name is required"})
                continue
            
            # Check for duplicate company code (field is 'code' in Company model)
            company_code = record.get("company_code") or record.get("code")
            if company_code:
                existing = await db.companies.find_one({
                    "code": company_code,
                    "is_deleted": {"$ne": True}
                })
                if existing:
                    errors.append({"row": idx + 2, "message": f"Company code {company_code} already exists"})
                    continue
            
            company = Company(
                name=record.get("name"),
                code=company_code or f"C{str(uuid.uuid4())[:6].upper()}",
                industry=record.get("industry"),
                contact_name=record.get("contact_name"),
                contact_email=record.get("contact_email"),
                contact_phone=record.get("contact_phone"),
                address=record.get("address"),
                city=record.get("city"),
                state=record.get("state"),
                country=record.get("country", "India"),
                pincode=record.get("pincode"),
                gst_number=record.get("gst_number"),
                notes=record.get("notes"),
                status="active"
            )
            
            await db.companies.insert_one(company.model_dump())
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}

@api_router.post("/admin/bulk-import/sites")
async def bulk_import_sites(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import sites from CSV data"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    # Get company mapping by code and name
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    company_by_code = {c.get("code", "").upper(): c["id"] for c in companies if c.get("code")}
    company_by_name = {c["name"].lower(): c["id"] for c in companies}
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            if not record.get("name"):
                errors.append({"row": idx + 2, "message": "Site name is required"})
                continue
            
            # Find company by code or name
            company_id = None
            if record.get("company_code"):
                company_id = company_by_code.get(record["company_code"].upper())
            if not company_id and record.get("company_name"):
                company_id = company_by_name.get(record["company_name"].lower())
            
            if not company_id:
                errors.append({"row": idx + 2, "message": "Company not found"})
                continue
            
            site = Site(
                company_id=company_id,
                name=record.get("name"),
                site_code=record.get("site_code"),
                address=record.get("address"),
                city=record.get("city"),
                state=record.get("state"),
                pincode=record.get("pincode"),
                country=record.get("country", "India"),
                contact_person=record.get("contact_person"),
                contact_phone=record.get("contact_phone"),
                contact_email=record.get("contact_email"),
                notes=record.get("notes"),
                status="active"
            )
            
            await db.sites.insert_one(site.model_dump())
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}

@api_router.post("/admin/bulk-import/devices")
async def bulk_import_devices(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import devices from CSV data"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    # Get lookups
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    company_by_code = {c.get("code", "").upper(): c["id"] for c in companies if c.get("code")}
    company_by_name = {c["name"].lower(): c["id"] for c in companies}
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            # Required fields
            if not record.get("serial_number"):
                errors.append({"row": idx + 2, "message": "Serial number is required"})
                continue
            if not record.get("brand"):
                errors.append({"row": idx + 2, "message": "Brand is required"})
                continue
            if not record.get("model"):
                errors.append({"row": idx + 2, "message": "Model is required"})
                continue
            
            # Find company
            company_id = None
            if record.get("company_code"):
                company_id = company_by_code.get(record["company_code"].upper())
            if not company_id and record.get("company_name"):
                company_id = company_by_name.get(record["company_name"].lower())
            
            if not company_id:
                errors.append({"row": idx + 2, "message": "Company not found"})
                continue
            
            # Check for duplicate serial number
            existing = await db.devices.find_one({
                "serial_number": record["serial_number"],
                "is_deleted": {"$ne": True}
            })
            if existing:
                errors.append({"row": idx + 2, "message": f"Serial number {record['serial_number']} already exists"})
                continue
            
            device = Device(
                company_id=company_id,
                device_type=record.get("device_type", "Laptop"),
                brand=record.get("brand"),
                model=record.get("model"),
                serial_number=record.get("serial_number"),
                asset_tag=record.get("asset_tag"),
                purchase_date=record.get("purchase_date", get_ist_isoformat().split("T")[0]),
                purchase_cost=float(record["purchase_cost"]) if record.get("purchase_cost") else None,
                vendor=record.get("vendor"),
                warranty_end_date=record.get("warranty_end_date"),
                location=record.get("location"),
                condition=record.get("condition", "good"),
                status=record.get("status", "active"),
                notes=record.get("notes")
            )
            
            await db.devices.insert_one(device.model_dump())
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}

@api_router.post("/admin/bulk-import/supply-products")
async def bulk_import_supply_products(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import supply products from CSV data"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    # Get category mapping
    categories = await db.supply_categories.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    category_by_name = {c["name"].lower(): c["id"] for c in categories}
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            if not record.get("name"):
                errors.append({"row": idx + 2, "message": "Product name is required"})
                continue
            
            # Find category
            category_id = None
            if record.get("category"):
                category_id = category_by_name.get(record["category"].lower())
            
            if not category_id:
                # Create category if it doesn't exist
                if record.get("category"):
                    new_cat = SupplyCategory(name=record["category"])
                    await db.supply_categories.insert_one(new_cat.model_dump())
                    category_id = new_cat.id
                    category_by_name[record["category"].lower()] = category_id
                else:
                    errors.append({"row": idx + 2, "message": "Category is required"})
                    continue
            
            product = SupplyProduct(
                category_id=category_id,
                name=record.get("name"),
                description=record.get("description"),
                unit=record.get("unit", "piece"),
                internal_notes=record.get("internal_notes")
            )
            
            await db.supply_products.insert_one(product.model_dump())
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}

@api_router.get("/admin/companies/{company_id}/overview")
async def get_company_overview(company_id: str, admin: dict = Depends(get_current_admin)):
    """Get comprehensive company 360° view with all related data"""
    # Get company details
    company = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get all related data in parallel
    devices_cursor = db.devices.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    devices = await devices_cursor.to_list(500)
    
    # Enrich devices with warranty status
    for device in devices:
        device["warranty_active"] = is_warranty_active(device.get("warranty_end_date", ""))
        # Check AMC status
        amc_assignment = await db.amc_device_assignments.find_one({
            "device_id": device["id"],
            "status": "active"
        }, {"_id": 0})
        if amc_assignment and is_warranty_active(amc_assignment.get("coverage_end", "")):
            device["amc_status"] = "active"
            device["amc_coverage_end"] = amc_assignment.get("coverage_end")
        else:
            device["amc_status"] = "none"
    
    # Get sites
    sites_cursor = db.sites.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    sites = await sites_cursor.to_list(100)
    
    # Get users/contacts
    users_cursor = db.users.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    users = await users_cursor.to_list(500)
    
    # Get deployments
    deployments_cursor = db.deployments.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    deployments = await deployments_cursor.to_list(100)
    for dep in deployments:
        site = await db.sites.find_one({"id": dep.get("site_id")}, {"_id": 0, "name": 1})
        dep["site_name"] = site.get("name") if site else "Unknown"
        dep["items_count"] = len(dep.get("items", []))
    
    # Get licenses
    licenses_cursor = db.licenses.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    licenses = await licenses_cursor.to_list(100)
    for lic in licenses:
        lic["is_expired"] = not is_warranty_active(lic.get("end_date", ""))
    
    # Get AMC contracts
    amc_cursor = db.amc_contracts.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    amc_contracts = await amc_cursor.to_list(50)
    for amc in amc_contracts:
        amc["is_active"] = is_warranty_active(amc.get("end_date", ""))
        # Count devices covered
        device_count = await db.amc_device_assignments.count_documents({
            "amc_contract_id": amc["id"],
            "status": "active"
        })
        amc["devices_covered"] = device_count
    
    # Get service history
    # First get all device IDs for this company
    device_ids = [d["id"] for d in devices]
    services = []
    if device_ids:
        services_cursor = db.service_history.find({
            "device_id": {"$in": device_ids},
            "is_deleted": {"$ne": True}
        }, {"_id": 0}).sort("service_date", -1).limit(100)
        services = await services_cursor.to_list(100)
        for svc in services:
            device = next((d for d in devices if d["id"] == svc.get("device_id")), None)
            if device:
                svc["device_info"] = f"{device.get('brand', '')} {device.get('model', '')} ({device.get('serial_number', '')})"
    
    # Calculate summary stats
    summary = {
        "total_devices": len(devices),
        "active_warranties": sum(1 for d in devices if d.get("warranty_active")),
        "active_amc_devices": sum(1 for d in devices if d.get("amc_status") == "active"),
        "total_sites": len(sites),
        "total_users": len(users),
        "total_deployments": len(deployments),
        "total_licenses": len(licenses),
        "active_licenses": sum(1 for l in licenses if not l.get("is_expired")),
        "total_amc_contracts": len(amc_contracts),
        "active_amc_contracts": sum(1 for a in amc_contracts if a.get("is_active")),
        "total_service_records": len(services)
    }
    
    return {
        "company": company,
        "summary": summary,
        "devices": devices,
        "sites": sites,
        "users": users,
        "deployments": deployments,
        "licenses": licenses,
        "amc_contracts": amc_contracts,
        "services": services
    }

# --- Admin: Manage Company Portal Users ---

@api_router.get("/admin/companies/{company_id}/portal-users")
async def list_company_portal_users(company_id: str, admin: dict = Depends(get_current_admin)):
    """List all portal users for a company"""
    company = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    users_cursor = db.company_users.find(
        {"company_id": company_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    )
    users = await users_cursor.to_list(100)
    return users

@api_router.post("/admin/companies/{company_id}/portal-users")
async def create_company_portal_user(
    company_id: str,
    user_data: dict,
    admin: dict = Depends(get_current_admin)
):
    """Create a new portal user for a company"""
    company = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if email already exists
    existing = await db.company_users.find_one({"email": user_data.get("email"), "is_deleted": {"$ne": True}})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate required fields
    if not user_data.get("name") or not user_data.get("email") or not user_data.get("password"):
        raise HTTPException(status_code=400, detail="Name, email, and password are required")
    
    if len(user_data.get("password", "")) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    # Create user
    new_user = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "email": user_data.get("email"),
        "password_hash": get_password_hash(user_data.get("password")),
        "name": user_data.get("name"),
        "phone": user_data.get("phone", ""),
        "role": user_data.get("role", "company_viewer"),
        "is_active": True,
        "is_deleted": False,
        "created_at": get_ist_isoformat(),
        "created_by": f"admin:{admin.get('id')}"
    }
    
    await db.company_users.insert_one(new_user)
    
    return {"message": "Portal user created successfully", "id": new_user["id"]}

@api_router.delete("/admin/companies/{company_id}/portal-users/{user_id}")
async def delete_company_portal_user(
    company_id: str,
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Delete (soft) a portal user"""
    result = await db.company_users.update_one(
        {"id": user_id, "company_id": company_id},
        {"$set": {"is_deleted": True, "deleted_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Portal user not found")
    
    return {"message": "Portal user deleted"}

@api_router.put("/admin/companies/{company_id}/portal-users/{user_id}/reset-password")
async def reset_portal_user_password(
    company_id: str,
    user_id: str,
    data: dict,
    admin: dict = Depends(get_current_admin)
):
    """Reset a portal user's password"""
    new_password = data.get("password")
    if not new_password or len(new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    
    result = await db.company_users.update_one(
        {"id": user_id, "company_id": company_id, "is_deleted": {"$ne": True}},
        {"$set": {
            "password_hash": get_password_hash(new_password),
            "updated_at": get_ist_isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Portal user not found")
    
    return {"message": "Password reset successfully"}

# ==================== ADMIN ENDPOINTS - USERS ====================

@api_router.get("/admin/users")
async def list_users(
    company_id: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List users with optional search support"""
    query = {"is_deleted": {"$ne": True}}
    if company_id:
        query["company_id"] = company_id
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"email": search_regex},
            {"phone": search_regex},
            {"department": search_regex}
        ]
    
    skip = (page - 1) * limit
    users = await db.users.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Add label field for SmartSelect compatibility
    for u in users:
        u["label"] = u["name"]
    
    return users

@api_router.post("/admin/users")
async def create_user(user_data: UserCreate, admin: dict = Depends(get_current_admin)):
    company = await db.companies.find_one({"id": user_data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    user = User(**user_data.model_dump())
    await db.users.insert_one(user.model_dump())
    await log_audit("user", user.id, "create", {"data": user_data.model_dump()}, admin)
    result = user.model_dump()
    result["label"] = result["name"]
    return result

@api_router.post("/admin/users/quick-create")
async def quick_create_user(user_data: UserCreate, admin: dict = Depends(get_current_admin)):
    """Quick create user (for inline creation from dropdowns)"""
    company = await db.companies.find_one({"id": user_data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if user with same email exists in same company
    existing = await db.users.find_one(
        {"email": user_data.email, "company_id": user_data.company_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if existing:
        existing["label"] = existing["name"]
        return existing
    
    user = User(**user_data.model_dump())
    await db.users.insert_one(user.model_dump())
    await log_audit("user", user.id, "quick_create", {"data": user_data.model_dump()}, admin)
    
    result = user.model_dump()
    result["label"] = result["name"]
    return result

@api_router.get("/admin/users/{user_id}")
async def get_user(user_id: str, admin: dict = Depends(get_current_admin)):
    user = await db.users.find_one({"id": user_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.put("/admin/users/{user_id}")
async def update_user(user_id: str, updates: UserUpdate, admin: dict = Depends(get_current_admin)):
    existing = await db.users.find_one({"id": user_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.users.update_one({"id": user_id}, {"$set": update_data})
    await log_audit("user", user_id, "update", changes, admin)
    return await db.users.find_one({"id": user_id}, {"_id": 0})

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.users.update_one({"id": user_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit("user", user_id, "delete", {"is_deleted": True}, admin)
    return {"message": "User archived"}

# ==================== ADMIN ENDPOINTS - DEVICES ====================

@api_router.get("/admin/devices")
async def list_devices(
    company_id: Optional[str] = None, 
    status: Optional[str] = None,
    amc_status: Optional[str] = None,  # Filter by AMC status: active, none, expired
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List devices with AMC status - P0 Fix"""
    query = {"is_deleted": {"$ne": True}}
    if company_id:
        query["company_id"] = company_id
    if status:
        query["status"] = status
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"serial_number": search_regex},
            {"asset_tag": search_regex},
            {"brand": search_regex},
            {"model": search_regex}
        ]
    
    skip = (page - 1) * limit
    devices = await db.devices.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich each device with AMC status from amc_device_assignments JOIN
    result = []
    for device in devices:
        # Get company name
        company = await db.companies.find_one({"id": device.get("company_id")}, {"_id": 0, "name": 1})
        device["company_name"] = company.get("name") if company else "Unknown"
        
        # Get assigned user name
        if device.get("assigned_user_id"):
            user = await db.users.find_one({"id": device["assigned_user_id"]}, {"_id": 0, "name": 1})
            device["assigned_user_name"] = user.get("name") if user else None
        
        # JOIN amc_device_assignments to get AMC status
        amc_assignment = await db.amc_device_assignments.find_one({
            "device_id": device["id"],
            "status": "active"
        }, {"_id": 0})
        
        if amc_assignment:
            # Check if coverage is still valid
            coverage_active = is_warranty_active(amc_assignment.get("coverage_end", ""))
            if coverage_active:
                # Get AMC contract details
                amc_contract = await db.amc_contracts.find_one({
                    "id": amc_assignment["amc_contract_id"],
                    "is_deleted": {"$ne": True}
                }, {"_id": 0, "name": 1, "amc_type": 1})
                
                device["amc_status"] = "active"
                device["amc_contract_id"] = amc_assignment["amc_contract_id"]
                device["amc_contract_name"] = amc_contract.get("name") if amc_contract else None
                device["amc_coverage_end"] = amc_assignment.get("coverage_end")
            else:
                device["amc_status"] = "expired"
                device["amc_contract_id"] = amc_assignment["amc_contract_id"]
                device["amc_coverage_end"] = amc_assignment.get("coverage_end")
        else:
            device["amc_status"] = "none"
            device["amc_contract_id"] = None
            device["amc_contract_name"] = None
            device["amc_coverage_end"] = None
        
        # Add SmartSelect label
        device["label"] = f"{device.get('brand', '')} {device.get('model', '')} - {device.get('serial_number', '')}"
        
        # Add deployment info if device was created from deployment
        if device.get("source") == "deployment" and device.get("deployment_id"):
            deployment = await db.deployments.find_one(
                {"id": device["deployment_id"], "is_deleted": {"$ne": True}}, 
                {"_id": 0, "name": 1, "site_id": 1}
            )
            if deployment:
                device["deployment_name"] = deployment.get("name")
                # Get site name
                site = await db.sites.find_one({"id": deployment.get("site_id")}, {"_id": 0, "name": 1})
                device["site_name"] = site.get("name") if site else None
        
        # Filter by AMC status if requested
        if amc_status and device["amc_status"] != amc_status:
            continue
        
        result.append(device)
    
    return result

@api_router.post("/admin/devices")
async def create_device(device_data: DeviceCreate, admin: dict = Depends(get_current_admin)):
    company = await db.companies.find_one({"id": device_data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    existing = await db.devices.find_one({"serial_number": device_data.serial_number, "is_deleted": {"$ne": True}}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Serial number already exists")
    
    device = Device(**device_data.model_dump())
    await db.devices.insert_one(device.model_dump())
    
    # Log initial assignment if user is assigned
    if device_data.assigned_user_id:
        user = await db.users.find_one({"id": device_data.assigned_user_id}, {"_id": 0, "name": 1})
        assignment = AssignmentHistory(
            device_id=device.id,
            from_user_id=None,
            to_user_id=device_data.assigned_user_id,
            from_user_name=None,
            to_user_name=user.get("name") if user else None,
            reason="Initial assignment",
            changed_by=admin.get("id"),
            changed_by_name=admin.get("name")
        )
        await db.assignment_history.insert_one(assignment.model_dump())
    
    await log_audit("device", device.id, "create", {"data": device_data.model_dump()}, admin)
    return device.model_dump()

@api_router.get("/admin/devices/{device_id}")
async def get_device(device_id: str, admin: dict = Depends(get_current_admin)):
    """Get device with full AMC contract details - P0 Fix"""
    device = await db.devices.find_one({"id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get company details
    company = await db.companies.find_one({"id": device.get("company_id")}, {"_id": 0, "name": 1})
    device["company_name"] = company.get("name") if company else "Unknown"
    
    # Get assigned user details
    if device.get("assigned_user_id"):
        user = await db.users.find_one({"id": device["assigned_user_id"]}, {"_id": 0, "name": 1, "email": 1})
        device["assigned_user_name"] = user.get("name") if user else None
        device["assigned_user_email"] = user.get("email") if user else None
    
    # JOIN amc_device_assignments → amc_contracts for full AMC info
    amc_assignments = await db.amc_device_assignments.find({
        "device_id": device_id
    }, {"_id": 0}).to_list(100)
    
    device["amc_assignments"] = []
    device["active_amc"] = None
    
    for assignment in amc_assignments:
        # Get full contract details
        contract = await db.amc_contracts.find_one({
            "id": assignment["amc_contract_id"],
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        
        if contract:
            coverage_active = is_warranty_active(assignment.get("coverage_end", ""))
            amc_info = {
                "assignment_id": assignment["id"],
                "amc_contract_id": contract["id"],
                "amc_name": contract.get("name"),
                "amc_type": contract.get("amc_type"),
                "coverage_start": assignment.get("coverage_start"),
                "coverage_end": assignment.get("coverage_end"),
                "coverage_active": coverage_active,
                "assignment_status": assignment.get("status"),
                "coverage_includes": contract.get("coverage_includes"),
                "entitlements": contract.get("entitlements")
            }
            device["amc_assignments"].append(amc_info)
            
            # Set active AMC if coverage is current
            if coverage_active and assignment.get("status") == "active" and not device["active_amc"]:
                device["active_amc"] = amc_info
    
    # Compute overall AMC status
    if device["active_amc"]:
        device["amc_status"] = "active"
    elif len(amc_assignments) > 0:
        device["amc_status"] = "expired"
    else:
        device["amc_status"] = "none"
    
    # Get parts
    parts = await db.parts.find({"device_id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    device["parts"] = parts
    
    # Get service history count
    service_count = await db.service_history.count_documents({"device_id": device_id})
    device["service_count"] = service_count
    
    return device

@api_router.put("/admin/devices/{device_id}")
async def update_device(device_id: str, updates: DeviceUpdate, admin: dict = Depends(get_current_admin)):
    existing = await db.devices.find_one({"id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # Check serial number uniqueness if updating
    if "serial_number" in update_data:
        dup = await db.devices.find_one({
            "serial_number": update_data["serial_number"],
            "id": {"$ne": device_id},
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        if dup:
            raise HTTPException(status_code=400, detail="Serial number already exists")
    
    # Track assignment change
    if "assigned_user_id" in update_data and update_data["assigned_user_id"] != existing.get("assigned_user_id"):
        old_user = None
        new_user = None
        
        if existing.get("assigned_user_id"):
            old_u = await db.users.find_one({"id": existing["assigned_user_id"]}, {"_id": 0, "name": 1})
            old_user = old_u.get("name") if old_u else None
        
        if update_data["assigned_user_id"]:
            new_u = await db.users.find_one({"id": update_data["assigned_user_id"]}, {"_id": 0, "name": 1})
            new_user = new_u.get("name") if new_u else None
        
        assignment = AssignmentHistory(
            device_id=device_id,
            from_user_id=existing.get("assigned_user_id"),
            to_user_id=update_data["assigned_user_id"],
            from_user_name=old_user,
            to_user_name=new_user,
            reason="Reassignment",
            changed_by=admin.get("id"),
            changed_by_name=admin.get("name")
        )
        await db.assignment_history.insert_one(assignment.model_dump())
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.devices.update_one({"id": device_id}, {"$set": update_data})
    await log_audit("device", device_id, "update", changes, admin)
    return await db.devices.find_one({"id": device_id}, {"_id": 0})

@api_router.delete("/admin/devices/{device_id}")
async def delete_device(device_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.devices.update_one({"id": device_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Soft delete related data
    await db.parts.update_many({"device_id": device_id}, {"$set": {"is_deleted": True}})
    await db.amc.update_many({"device_id": device_id}, {"$set": {"is_deleted": True}})
    await log_audit("device", device_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Device archived"}

@api_router.get("/admin/devices/{device_id}/assignment-history")
async def get_assignment_history(device_id: str, admin: dict = Depends(get_current_admin)):
    history = await db.assignment_history.find({"device_id": device_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return history

@api_router.get("/admin/devices/{device_id}/timeline")
async def get_device_timeline(device_id: str, admin: dict = Depends(get_current_admin)):
    """Get unified timeline for a device (assignments, services, parts, AMC)"""
    device = await db.devices.find_one({"id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    timeline = []
    
    # Purchase event
    timeline.append({
        "type": "purchase",
        "date": device.get("purchase_date"),
        "title": "Device Purchased",
        "description": f"{device.get('brand')} {device.get('model')} added to inventory",
        "icon": "package"
    })
    
    # Assignment history
    assignments = await db.assignment_history.find({"device_id": device_id}, {"_id": 0}).to_list(100)
    for a in assignments:
        from_name = a.get("from_user_name") or "Unassigned"
        to_name = a.get("to_user_name") or "Unassigned"
        timeline.append({
            "type": "assignment",
            "date": a.get("created_at"),
            "title": "Assignment Changed",
            "description": f"{from_name} → {to_name}",
            "changed_by": a.get("changed_by_name"),
            "icon": "user"
        })
    
    # Service history
    services = await db.service_history.find({"device_id": device_id}, {"_id": 0}).to_list(100)
    for s in services:
        timeline.append({
            "type": "service",
            "date": s.get("service_date"),
            "title": s.get("service_type", "Service").replace("_", " ").title(),
            "description": s.get("action_taken"),
            "technician": s.get("technician_name"),
            "icon": "wrench"
        })
    
    # Parts replacements
    parts = await db.parts.find({"device_id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    for p in parts:
        timeline.append({
            "type": "part",
            "date": p.get("replaced_date"),
            "title": f"Part Replaced: {p.get('part_name')}",
            "description": f"Warranty: {p.get('warranty_months')} months",
            "icon": "cpu"
        })
    
    # AMC
    amc_list = await db.amc.find({"device_id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(10)
    for amc in amc_list:
        timeline.append({
            "type": "amc",
            "date": amc.get("start_date"),
            "title": "AMC Started",
            "description": f"Valid until {amc.get('end_date')}",
            "icon": "shield"
        })
    
    # Sort by date descending
    timeline.sort(key=lambda x: x.get("date", ""), reverse=True)
    
    return timeline

# ==================== SERVICE HISTORY ENDPOINTS ====================

@api_router.get("/admin/services")
async def list_services(device_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {}
    if device_id:
        query["device_id"] = device_id
    services = await db.service_history.find(query, {"_id": 0}).sort("service_date", -1).to_list(1000)
    return services

@api_router.post("/admin/services")
async def create_service(service_data: ServiceHistoryCreate, admin: dict = Depends(get_current_admin)):
    device = await db.devices.find_one({"id": service_data.device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    service = ServiceHistory(
        **service_data.model_dump(),
        company_id=device.get("company_id"),
        created_by=admin.get("id"),
        created_by_name=admin.get("name")
    )
    await db.service_history.insert_one(service.model_dump())
    await log_audit("service", service.id, "create", {"data": service_data.model_dump()}, admin)
    return service.model_dump()

@api_router.get("/admin/services/{service_id}")
async def get_service(service_id: str, admin: dict = Depends(get_current_admin)):
    service = await db.service_history.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")
    return service

@api_router.put("/admin/services/{service_id}")
async def update_service(service_id: str, updates: ServiceHistoryUpdate, admin: dict = Depends(get_current_admin)):
    existing = await db.service_history.find_one({"id": service_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.service_history.update_one({"id": service_id}, {"$set": update_data})
    await log_audit("service", service_id, "update", changes, admin)
    return await db.service_history.find_one({"id": service_id}, {"_id": 0})

@api_router.post("/admin/services/{service_id}/attachments")
async def upload_service_attachment(
    service_id: str, 
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin)
):
    """Upload attachment to service record"""
    service = await db.service_history.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed. Use PDF, JPG, or PNG.")
    
    # Validate file size (5MB max)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB.")
    
    # Save file
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    filename = f"{file_id}.{ext}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create attachment record
    attachment = ServiceAttachment(
        id=file_id,
        filename=filename,
        original_name=file.filename,
        file_type=file.content_type,
        file_size=len(content)
    )
    
    # Add to service record
    attachments = service.get("attachments", [])
    attachments.append(attachment.model_dump())
    
    await db.service_history.update_one(
        {"id": service_id},
        {"$set": {"attachments": attachments}}
    )
    
    await log_audit("service", service_id, "attachment_upload", {"filename": file.filename}, admin)
    return {"message": "Attachment uploaded", "attachment": attachment.model_dump()}

@api_router.delete("/admin/services/{service_id}/attachments/{attachment_id}")
async def delete_service_attachment(service_id: str, attachment_id: str, admin: dict = Depends(get_current_admin)):
    service = await db.service_history.find_one({"id": service_id}, {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    attachments = service.get("attachments", [])
    attachment = next((a for a in attachments if a.get("id") == attachment_id), None)
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Delete file
    file_path = UPLOAD_DIR / attachment.get("filename")
    if file_path.exists():
        file_path.unlink()
    
    # Remove from service record
    attachments = [a for a in attachments if a.get("id") != attachment_id]
    await db.service_history.update_one(
        {"id": service_id},
        {"$set": {"attachments": attachments}}
    )
    
    await log_audit("service", service_id, "attachment_delete", {"attachment_id": attachment_id}, admin)
    return {"message": "Attachment deleted"}

# ==================== ADMIN ENDPOINTS - PARTS ====================

@api_router.get("/admin/parts")
async def list_parts(device_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {"is_deleted": {"$ne": True}}
    if device_id:
        query["device_id"] = device_id
    parts = await db.parts.find(query, {"_id": 0}).to_list(1000)
    return parts

@api_router.post("/admin/parts")
async def create_part(part_data: PartCreate, admin: dict = Depends(get_current_admin)):
    device = await db.devices.find_one({"id": part_data.device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    warranty_expiry = calculate_warranty_expiry(part_data.replaced_date, part_data.warranty_months)
    
    part = Part(
        **part_data.model_dump(),
        warranty_expiry_date=warranty_expiry
    )
    await db.parts.insert_one(part.model_dump())
    await log_audit("part", part.id, "create", {"data": part_data.model_dump()}, admin)
    return part.model_dump()

@api_router.get("/admin/parts/{part_id}")
async def get_part(part_id: str, admin: dict = Depends(get_current_admin)):
    part = await db.parts.find_one({"id": part_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part

@api_router.put("/admin/parts/{part_id}")
async def update_part(part_id: str, updates: PartUpdate, admin: dict = Depends(get_current_admin)):
    existing = await db.parts.find_one({"id": part_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Part not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    if "replaced_date" in update_data or "warranty_months" in update_data:
        replaced_date = update_data.get("replaced_date", existing.get("replaced_date"))
        warranty_months = update_data.get("warranty_months", existing.get("warranty_months"))
        update_data["warranty_expiry_date"] = calculate_warranty_expiry(replaced_date, warranty_months)
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.parts.update_one({"id": part_id}, {"$set": update_data})
    await log_audit("part", part_id, "update", changes, admin)
    return await db.parts.find_one({"id": part_id}, {"_id": 0})

@api_router.delete("/admin/parts/{part_id}")
async def delete_part(part_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.parts.update_one({"id": part_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Part not found")
    await log_audit("part", part_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Part archived"}

# ==================== ADMIN ENDPOINTS - AMC ====================

@api_router.get("/admin/amc")
async def list_amc(device_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    query = {"is_deleted": {"$ne": True}}
    if device_id:
        query["device_id"] = device_id
    amc_list = await db.amc.find(query, {"_id": 0}).to_list(1000)
    return amc_list

@api_router.post("/admin/amc")
async def create_amc(amc_data: AMCCreate, admin: dict = Depends(get_current_admin)):
    device = await db.devices.find_one({"id": amc_data.device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    existing = await db.amc.find_one({"device_id": amc_data.device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="AMC already exists for this device")
    
    amc = AMC(**amc_data.model_dump())
    await db.amc.insert_one(amc.model_dump())
    await log_audit("amc", amc.id, "create", {"data": amc_data.model_dump()}, admin)
    return amc.model_dump()

@api_router.get("/admin/amc/{amc_id}")
async def get_amc(amc_id: str, admin: dict = Depends(get_current_admin)):
    amc = await db.amc.find_one({"id": amc_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not amc:
        raise HTTPException(status_code=404, detail="AMC not found")
    return amc

@api_router.put("/admin/amc/{amc_id}")
async def update_amc(amc_id: str, updates: AMCUpdate, admin: dict = Depends(get_current_admin)):
    existing = await db.amc.find_one({"id": amc_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="AMC not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.amc.update_one({"id": amc_id}, {"$set": update_data})
    await log_audit("amc", amc_id, "update", changes, admin)
    return await db.amc.find_one({"id": amc_id}, {"_id": 0})

@api_router.delete("/admin/amc/{amc_id}")
async def delete_amc(amc_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.amc.update_one({"id": amc_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="AMC not found")
    await log_audit("amc", amc_id, "delete", {"is_deleted": True}, admin)
    return {"message": "AMC archived"}

# ==================== AMC V2 CONTRACTS (Enhanced) ====================

def get_amc_status(start_date: str, end_date: str) -> str:
    """Calculate AMC status based on dates"""
    today = get_ist_now().date()
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date() if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date() if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if today < start:
            return "upcoming"
        elif today > end:
            return "expired"
        else:
            return "active"
    except:
        return "unknown"

def get_days_until_expiry(end_date: str) -> Optional[int]:
    """Calculate days until AMC expiry"""
    today = get_ist_now().date()
    try:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date() if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d').date()
        return (end - today).days
    except:
        return None

@api_router.get("/admin/amc-contracts")
async def list_amc_contracts(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    serial: Optional[str] = None,  # Search by device serial number
    asset_tag: Optional[str] = None,  # Search by device asset tag
    q: Optional[str] = None,  # General search (name, company)
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List AMC contracts with serial number search - P0 Fix"""
    query = {"is_deleted": {"$ne": True}}
    if company_id:
        query["company_id"] = company_id
    
    # If searching by serial/asset_tag, first find the device, then find contracts
    if serial or asset_tag:
        device_query = {"is_deleted": {"$ne": True}}
        if serial:
            device_query["serial_number"] = {"$regex": serial, "$options": "i"}
        if asset_tag:
            device_query["asset_tag"] = {"$regex": asset_tag, "$options": "i"}
        
        devices = await db.devices.find(device_query, {"_id": 0, "id": 1}).to_list(100)
        device_ids = [d["id"] for d in devices]
        
        if not device_ids:
            return []  # No devices match, so no contracts
        
        # Find assignments for these devices
        assignments = await db.amc_device_assignments.find({
            "device_id": {"$in": device_ids}
        }, {"_id": 0, "amc_contract_id": 1}).to_list(1000)
        
        contract_ids = list(set([a["amc_contract_id"] for a in assignments]))
        if not contract_ids:
            return []
        
        query["id"] = {"$in": contract_ids}
    
    # General search
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex}
        ]
    
    skip = (page - 1) * limit
    contracts = await db.amc_contracts.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Compute status and enrich for each contract
    result = []
    for contract in contracts:
        status_val = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
        days_left = get_days_until_expiry(contract.get("end_date", ""))
        
        # Get company name
        company = await db.companies.find_one({"id": contract.get("company_id")}, {"_id": 0, "name": 1})
        
        # Get usage stats
        usage_count = await db.amc_usage.count_documents({"amc_contract_id": contract["id"]})
        
        # Get assigned devices count
        devices_count = await db.amc_device_assignments.count_documents({
            "amc_contract_id": contract["id"],
            "status": "active"
        })
        
        contract["status"] = status_val
        contract["days_until_expiry"] = days_left
        contract["company_name"] = company.get("name") if company else "Unknown"
        contract["usage_count"] = usage_count
        contract["assigned_devices_count"] = devices_count
        contract["label"] = contract.get("name")  # SmartSelect compatibility
        
        if status and status_val != status:
            continue
        result.append(contract)
    
    return result

@api_router.post("/admin/amc-contracts")
async def create_amc_contract(data: AMCContractCreate, admin: dict = Depends(get_current_admin)):
    """Create new AMC contract"""
    # Validate company exists
    company = await db.companies.find_one({"id": data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Build contract with defaults
    contract_data = {
        "company_id": data.company_id,
        "name": data.name,
        "amc_type": data.amc_type,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "coverage_includes": data.coverage_includes or AMCCoverageIncludes().model_dump(),
        "exclusions": data.exclusions or AMCExclusions().model_dump(),
        "entitlements": data.entitlements or AMCEntitlements().model_dump(),
        "asset_mapping": data.asset_mapping or AMCAssetMapping().model_dump(),
        "internal_notes": data.internal_notes,
    }
    
    contract = AMCContract(**contract_data)
    await db.amc_contracts.insert_one(contract.model_dump())
    await log_audit("amc_contract", contract.id, "create", {"data": contract_data}, admin)
    
    result = contract.model_dump()
    result["status"] = get_amc_status(result["start_date"], result["end_date"])
    result["company_name"] = company.get("name")
    return result

@api_router.get("/admin/amc-contracts/{contract_id}")
async def get_amc_contract(contract_id: str, admin: dict = Depends(get_current_admin)):
    """Get single AMC contract with details"""
    contract = await db.amc_contracts.find_one({"id": contract_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    # Compute status
    contract["status"] = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
    contract["days_until_expiry"] = get_days_until_expiry(contract.get("end_date", ""))
    
    # Get company details
    company = await db.companies.find_one({"id": contract.get("company_id")}, {"_id": 0})
    contract["company_name"] = company.get("name") if company else "Unknown"
    
    # Get covered assets based on mapping type
    asset_mapping = contract.get("asset_mapping", {})
    mapping_type = asset_mapping.get("mapping_type", "all_company")
    
    if mapping_type == "all_company":
        assets = await db.devices.find(
            {"company_id": contract["company_id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(1000)
    elif mapping_type == "selected_assets":
        asset_ids = asset_mapping.get("selected_asset_ids", [])
        assets = await db.devices.find(
            {"id": {"$in": asset_ids}, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(1000)
    elif mapping_type == "device_types":
        device_types = asset_mapping.get("selected_device_types", [])
        assets = await db.devices.find(
            {"company_id": contract["company_id"], "device_type": {"$in": device_types}, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(1000)
    else:
        assets = []
    
    contract["covered_assets"] = assets
    contract["covered_assets_count"] = len(assets)
    
    # Get usage history
    usage = await db.amc_usage.find({"amc_contract_id": contract_id}, {"_id": 0}).to_list(100)
    contract["usage_history"] = usage
    
    # Calculate usage stats
    onsite_count = len([u for u in usage if u.get("usage_type") == "onsite_visit"])
    remote_count = len([u for u in usage if u.get("usage_type") == "remote_support"])
    pm_count = len([u for u in usage if u.get("usage_type") == "preventive_maintenance"])
    
    contract["usage_stats"] = {
        "onsite_visits_used": onsite_count,
        "remote_support_used": remote_count,
        "preventive_maintenance_used": pm_count
    }
    
    return contract

@api_router.put("/admin/amc-contracts/{contract_id}")
async def update_amc_contract(contract_id: str, updates: AMCContractUpdate, admin: dict = Depends(get_current_admin)):
    """Update AMC contract"""
    existing = await db.amc_contracts.find_one({"id": contract_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    await db.amc_contracts.update_one({"id": contract_id}, {"$set": update_data})
    await log_audit("amc_contract", contract_id, "update", changes, admin)
    
    result = await db.amc_contracts.find_one({"id": contract_id}, {"_id": 0})
    result["status"] = get_amc_status(result.get("start_date", ""), result.get("end_date", ""))
    return result

@api_router.delete("/admin/amc-contracts/{contract_id}")
async def delete_amc_contract(contract_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete AMC contract"""
    result = await db.amc_contracts.update_one({"id": contract_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    await log_audit("amc_contract", contract_id, "delete", {"is_deleted": True}, admin)
    return {"message": "AMC Contract archived"}

@api_router.post("/admin/amc-contracts/{contract_id}/usage")
async def record_amc_usage(
    contract_id: str,
    usage_type: str = Query(..., description="onsite_visit, remote_support, preventive_maintenance"),
    service_id: Optional[str] = None,
    notes: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Record usage against AMC contract"""
    contract = await db.amc_contracts.find_one({"id": contract_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    usage = AMCUsageRecord(
        amc_contract_id=contract_id,
        service_id=service_id,
        usage_type=usage_type,
        usage_date=get_ist_isoformat(),
        notes=notes
    )
    
    await db.amc_usage.insert_one(usage.model_dump())
    return usage.model_dump()

@api_router.get("/admin/amc-contracts/check-coverage/{device_id}")
async def check_amc_coverage(device_id: str, admin: dict = Depends(get_current_admin)):
    """Check if a device is covered under any active AMC"""
    device = await db.devices.find_one({"id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    company_id = device.get("company_id")
    device_type = device.get("device_type")
    
    # Find all active AMC contracts for this company
    contracts = await db.amc_contracts.find(
        {"company_id": company_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)
    
    covered_contracts = []
    for contract in contracts:
        status = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
        if status != "active":
            continue
        
        asset_mapping = contract.get("asset_mapping", {})
        mapping_type = asset_mapping.get("mapping_type", "all_company")
        
        is_covered = False
        if mapping_type == "all_company":
            is_covered = True
        elif mapping_type == "selected_assets":
            is_covered = device_id in asset_mapping.get("selected_asset_ids", [])
        elif mapping_type == "device_types":
            is_covered = device_type in asset_mapping.get("selected_device_types", [])
        
        if is_covered:
            covered_contracts.append({
                "contract_id": contract["id"],
                "contract_name": contract["name"],
                "amc_type": contract.get("amc_type"),
                "coverage_includes": contract.get("coverage_includes"),
                "exclusions": contract.get("exclusions"),
                "end_date": contract.get("end_date"),
                "days_until_expiry": get_days_until_expiry(contract.get("end_date", ""))
            })
    
    return {
        "device_id": device_id,
        "device_info": f"{device.get('brand')} {device.get('model')} ({device.get('serial_number')})",
        "is_covered": len(covered_contracts) > 0,
        "active_contracts": covered_contracts
    }

@api_router.get("/admin/companies-without-amc")
async def get_companies_without_amc(admin: dict = Depends(get_current_admin)):
    """Get list of companies without any active AMC"""
    # Get all companies
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    
    companies_without_amc = []
    for company in companies:
        # Check if company has any active AMC
        contracts = await db.amc_contracts.find(
            {"company_id": company["id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(10)
        
        has_active_amc = False
        for contract in contracts:
            if get_amc_status(contract.get("start_date", ""), contract.get("end_date", "")) == "active":
                has_active_amc = True
                break
        
        if not has_active_amc:
            companies_without_amc.append({
                "id": company["id"],
                "name": company.get("name"),
                "contact_email": company.get("contact_email")
            })
    
    return companies_without_amc

# ==================== ADMIN ENDPOINTS - SITES ====================

@api_router.get("/admin/sites")
async def list_sites(
    company_id: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List all sites with optional search support"""
    query = {"is_deleted": {"$ne": True}}
    if company_id:
        query["company_id"] = company_id
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"city": search_regex},
            {"address": search_regex}
        ]
    
    skip = (page - 1) * limit
    sites = await db.sites.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with company names and counts
    for site in sites:
        company = await db.companies.find_one({"id": site.get("company_id")}, {"_id": 0, "name": 1})
        site["company_name"] = company.get("name") if company else "Unknown"
        site["label"] = site["name"]  # SmartSelect compatibility
        
        # Count deployments and items
        deployments = await db.deployments.find(
            {"site_id": site["id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(100)
        site["deployments_count"] = len(deployments)
        
        # Count total items across deployments
        total_items = sum(len(d.get("items", [])) for d in deployments)
        site["items_count"] = total_items
    
    return sites

@api_router.post("/admin/sites")
async def create_site(data: SiteCreate, admin: dict = Depends(get_current_admin)):
    """Create new site"""
    # Validate company exists
    company = await db.companies.find_one({"id": data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    site = Site(**data.model_dump())
    await db.sites.insert_one(site.model_dump())
    await log_audit("site", site.id, "create", {"data": data.model_dump()}, admin)
    
    result = site.model_dump()
    result["company_name"] = company.get("name")
    result["label"] = result["name"]
    return result

@api_router.post("/admin/sites/quick-create")
async def quick_create_site(data: SiteCreate, admin: dict = Depends(get_current_admin)):
    """Quick create site (for inline creation from dropdowns)"""
    # Validate company exists
    company = await db.companies.find_one({"id": data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if site with same name exists for this company
    existing = await db.sites.find_one(
        {"name": {"$regex": f"^{data.name}$", "$options": "i"}, "company_id": data.company_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if existing:
        existing["label"] = existing["name"]
        existing["company_name"] = company.get("name")
        return existing
    
    site = Site(**data.model_dump())
    await db.sites.insert_one(site.model_dump())
    await log_audit("site", site.id, "quick_create", {"data": data.model_dump()}, admin)
    
    result = site.model_dump()
    result["company_name"] = company.get("name")
    result["label"] = result["name"]
    return result

@api_router.get("/admin/sites/{site_id}")
async def get_site(site_id: str, admin: dict = Depends(get_current_admin)):
    """Get site with full details including deployments"""
    site = await db.sites.find_one({"id": site_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Get company
    company = await db.companies.find_one({"id": site.get("company_id")}, {"_id": 0})
    site["company_name"] = company.get("name") if company else "Unknown"
    
    # Get deployments
    deployments = await db.deployments.find(
        {"site_id": site_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)
    site["deployments"] = deployments
    
    # Aggregate all items
    all_items = []
    for deployment in deployments:
        for item in deployment.get("items", []):
            item["deployment_id"] = deployment["id"]
            item["deployment_name"] = deployment["name"]
            all_items.append(item)
    site["all_items"] = all_items
    
    # Get active AMCs for this site
    amc_contracts = await db.amc_contracts.find(
        {"company_id": site["company_id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)
    
    active_amcs = []
    for contract in amc_contracts:
        status = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
        if status == "active":
            # Check if AMC covers this site
            asset_mapping = contract.get("asset_mapping", {})
            mapping_type = asset_mapping.get("mapping_type", "all_company")
            
            if mapping_type == "all_company":
                active_amcs.append(contract)
            # Could add site-specific AMC mapping here in future
    
    site["active_amcs"] = active_amcs
    
    return site

@api_router.put("/admin/sites/{site_id}")
async def update_site(site_id: str, updates: SiteUpdate, admin: dict = Depends(get_current_admin)):
    """Update site"""
    existing = await db.sites.find_one({"id": site_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Site not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    await db.sites.update_one({"id": site_id}, {"$set": update_data})
    await log_audit("site", site_id, "update", changes, admin)
    
    return await db.sites.find_one({"id": site_id}, {"_id": 0})

@api_router.delete("/admin/sites/{site_id}")
async def delete_site(site_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete site"""
    result = await db.sites.update_one({"id": site_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Site not found")
    await log_audit("site", site_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Site archived"}

# ==================== ADMIN ENDPOINTS - DEPLOYMENTS ====================

@api_router.get("/admin/deployments")
async def list_deployments(
    company_id: Optional[str] = None,
    site_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all deployments"""
    query = {"is_deleted": {"$ne": True}}
    if company_id:
        query["company_id"] = company_id
    if site_id:
        query["site_id"] = site_id
    
    deployments = await db.deployments.find(query, {"_id": 0}).to_list(1000)
    
    # Enrich with company and site names
    for deployment in deployments:
        company = await db.companies.find_one({"id": deployment.get("company_id")}, {"_id": 0, "name": 1})
        site = await db.sites.find_one({"id": deployment.get("site_id")}, {"_id": 0, "name": 1})
        deployment["company_name"] = company.get("name") if company else "Unknown"
        deployment["site_name"] = site.get("name") if site else "Unknown"
        deployment["items_count"] = len(deployment.get("items", []))
    
    return deployments

@api_router.post("/admin/deployments")
async def create_deployment(data: DeploymentCreate, admin: dict = Depends(get_current_admin)):
    """Create new deployment with items"""
    # Validate company and site
    company = await db.companies.find_one({"id": data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    site = await db.sites.find_one({"id": data.site_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Process items - create devices for serialized items
    processed_items = []
    for item_data in data.items:
        item = DeploymentItem(**item_data)
        
        # For serialized items, create device records
        if item.is_serialized and item.serial_numbers:
            linked_device_ids = []
            for serial in item.serial_numbers:
                device_data = {
                    "id": str(uuid.uuid4()),
                    "company_id": data.company_id,
                    "site_id": data.site_id,
                    "deployment_id": "",  # Will be updated after deployment is created
                    "device_type": item.category,
                    "brand": item.brand or "Unknown",
                    "model": item.model or "Unknown",
                    "serial_number": serial,
                    "purchase_date": item.installation_date or data.deployment_date,
                    "warranty_end_date": item.warranty_end_date,
                    "location": item.zone_location,
                    "status": "active",
                    "condition": "new",
                    "is_deleted": False,
                    "created_at": get_ist_isoformat()
                }
                linked_device_ids.append(device_data["id"])
            
            item.linked_device_ids = linked_device_ids
        
        processed_items.append(item.model_dump())
    
    # Create deployment
    deployment = Deployment(
        company_id=data.company_id,
        site_id=data.site_id,
        name=data.name,
        deployment_date=data.deployment_date,
        installed_by=data.installed_by,
        notes=data.notes,
        items=processed_items,
        created_by=admin.get("id", ""),
        created_by_name=admin.get("name", "Admin")
    )
    
    await db.deployments.insert_one(deployment.model_dump())
    
    # Now create the device records for serialized items
    for item_idx, item in enumerate(processed_items):
        if item.get("is_serialized") and item.get("serial_numbers"):
            for i, serial in enumerate(item["serial_numbers"]):
                device_id = item["linked_device_ids"][i] if i < len(item.get("linked_device_ids", [])) else str(uuid.uuid4())
                device_data = {
                    "id": device_id,
                    "company_id": data.company_id,
                    "site_id": data.site_id,
                    "deployment_id": deployment.id,
                    "deployment_item_index": item_idx,
                    "source": "deployment",
                    "device_type": item.get("category"),
                    "brand": item.get("brand") or "Unknown",
                    "model": item.get("model") or "Unknown",
                    "serial_number": serial,
                    "purchase_date": item.get("installation_date") or data.deployment_date,
                    "warranty_end_date": item.get("warranty_end_date"),
                    "location": item.get("zone_location"),
                    "status": "active",
                    "condition": "new",
                    "is_deleted": False,
                    "created_at": get_ist_isoformat()
                }
                await db.devices.insert_one(device_data)
    
    await log_audit("deployment", deployment.id, "create", {"data": data.model_dump()}, admin)
    
    result = deployment.model_dump()
    result["company_name"] = company.get("name")
    result["site_name"] = site.get("name")
    result["items_count"] = len(processed_items)
    return result

@api_router.get("/admin/deployments/{deployment_id}")
async def get_deployment(deployment_id: str, admin: dict = Depends(get_current_admin)):
    """Get deployment with full details"""
    deployment = await db.deployments.find_one({"id": deployment_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Get company and site
    company = await db.companies.find_one({"id": deployment.get("company_id")}, {"_id": 0})
    site = await db.sites.find_one({"id": deployment.get("site_id")}, {"_id": 0})
    deployment["company_name"] = company.get("name") if company else "Unknown"
    deployment["site_name"] = site.get("name") if site else "Unknown"
    
    # Enrich items with AMC coverage info
    for item in deployment.get("items", []):
        if item.get("amc_contract_id"):
            amc = await db.amc_contracts.find_one({"id": item["amc_contract_id"]}, {"_id": 0, "name": 1})
            item["amc_name"] = amc.get("name") if amc else None
        
        # Check if covered by any active AMC
        amc_contracts = await db.amc_contracts.find(
            {"company_id": deployment["company_id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(10)
        
        is_amc_covered = False
        covering_amc = None
        for contract in amc_contracts:
            status = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
            if status == "active":
                mapping = contract.get("asset_mapping", {})
                if mapping.get("mapping_type") == "all_company":
                    is_amc_covered = True
                    covering_amc = contract.get("name")
                    break
                elif mapping.get("mapping_type") == "device_types":
                    if item.get("category") in mapping.get("selected_device_types", []):
                        is_amc_covered = True
                        covering_amc = contract.get("name")
                        break
        
        item["is_amc_covered"] = is_amc_covered
        item["covering_amc"] = covering_amc
    
    return deployment

@api_router.put("/admin/deployments/{deployment_id}")
async def update_deployment(deployment_id: str, updates: DeploymentUpdate, admin: dict = Depends(get_current_admin)):
    """Update deployment"""
    existing = await db.deployments.find_one({"id": deployment_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.deployments.update_one({"id": deployment_id}, {"$set": update_data})
    await log_audit("deployment", deployment_id, "update", update_data, admin)
    
    return await db.deployments.find_one({"id": deployment_id}, {"_id": 0})

@api_router.delete("/admin/deployments/{deployment_id}")
async def delete_deployment(deployment_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete deployment and linked devices"""
    result = await db.deployments.update_one({"id": deployment_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Also soft-delete devices created from this deployment
    await db.devices.update_many(
        {"deployment_id": deployment_id, "source": "deployment"},
        {"$set": {"is_deleted": True}}
    )
    
    await log_audit("deployment", deployment_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Deployment and linked devices archived"}

@api_router.post("/admin/deployments/{deployment_id}/items")
async def add_deployment_item(deployment_id: str, item_data: dict, admin: dict = Depends(get_current_admin)):
    """Add item to existing deployment"""
    deployment = await db.deployments.find_one({"id": deployment_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    item = DeploymentItem(**item_data)
    
    # Handle serialized items
    if item.is_serialized and item.serial_numbers:
        linked_device_ids = []
        for serial in item.serial_numbers:
            device_data = {
                "id": str(uuid.uuid4()),
                "company_id": deployment["company_id"],
                "site_id": deployment["site_id"],
                "deployment_id": deployment_id,
                "source": "deployment",
                "device_type": item.category,
                "category": item.category,
                "brand": item.brand or "Unknown",
                "model": item.model or "Unknown",
                "serial_number": serial,
                "purchase_date": item.installation_date or deployment["deployment_date"],
                "warranty_end_date": item.warranty_end_date,
                "location": item.zone_location,
                "status": "active",
                "condition": "new",
                "is_deleted": False,
                "created_at": get_ist_isoformat()
            }
            await db.devices.insert_one(device_data)
            linked_device_ids.append(device_data["id"])
        
        item.linked_device_ids = linked_device_ids
    
    # Add item to deployment
    await db.deployments.update_one(
        {"id": deployment_id},
        {
            "$push": {"items": item.model_dump()},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    return item.model_dump()

@api_router.put("/admin/deployments/{deployment_id}/items/{item_index}")
async def update_deployment_item(
    deployment_id: str, 
    item_index: int, 
    item_data: dict, 
    admin: dict = Depends(get_current_admin)
):
    """Update an item in a deployment and sync changes to devices"""
    deployment = await db.deployments.find_one({"id": deployment_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    items = deployment.get("items", [])
    if item_index < 0 or item_index >= len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    
    old_item = items[item_index]
    
    # Merge updates with existing item
    updated_item = {**old_item, **{k: v for k, v in item_data.items() if v is not None}}
    
    # Handle serial number changes - sync to devices
    new_serials = item_data.get("serial_numbers", [])
    old_serials = old_item.get("serial_numbers", [])
    old_linked_ids = old_item.get("linked_device_ids", [])
    
    # If serial numbers are being added/updated
    if new_serials and updated_item.get("is_serialized"):
        new_linked_ids = []
        
        for i, serial in enumerate(new_serials):
            if serial:  # Only process non-empty serial numbers
                # Check if this serial was already linked to a device
                if i < len(old_linked_ids) and old_linked_ids[i]:
                    # Update existing device
                    device_id = old_linked_ids[i]
                    await db.devices.update_one(
                        {"id": device_id},
                        {"$set": {
                            "serial_number": serial,
                            "device_type": updated_item.get("category"),
                            "category": updated_item.get("category"),
                            "brand": updated_item.get("brand") or "Unknown",
                            "model": updated_item.get("model") or "Unknown",
                            "warranty_end_date": updated_item.get("warranty_end_date"),
                            "location": updated_item.get("zone_location"),
                            "updated_at": get_ist_isoformat()
                        }}
                    )
                    new_linked_ids.append(device_id)
                else:
                    # Create new device for this serial
                    device_data = {
                        "id": str(uuid.uuid4()),
                        "company_id": deployment["company_id"],
                        "site_id": deployment["site_id"],
                        "deployment_id": deployment_id,
                        "deployment_item_index": item_index,
                        "source": "deployment",
                        "device_type": updated_item.get("category"),
                        "category": updated_item.get("category"),
                        "brand": updated_item.get("brand") or "Unknown",
                        "model": updated_item.get("model") or "Unknown",
                        "serial_number": serial,
                        "purchase_date": updated_item.get("installation_date") or deployment["deployment_date"],
                        "warranty_end_date": updated_item.get("warranty_end_date"),
                        "location": updated_item.get("zone_location"),
                        "status": "active",
                        "condition": "new",
                        "is_deleted": False,
                        "created_at": get_ist_isoformat()
                    }
                    await db.devices.insert_one(device_data)
                    new_linked_ids.append(device_data["id"])
        
        updated_item["linked_device_ids"] = new_linked_ids
        updated_item["serial_numbers"] = new_serials
    
    # Update the item in deployment
    items[item_index] = updated_item
    await db.deployments.update_one(
        {"id": deployment_id},
        {"$set": {
            "items": items,
            "updated_at": get_ist_isoformat()
        }}
    )
    
    await log_audit("deployment", deployment_id, "update_item", {"item_index": item_index, "updates": item_data}, admin)
    
    return {"message": "Item updated successfully", "item": updated_item}

@api_router.post("/admin/deployments/{deployment_id}/sync-devices")
async def sync_deployment_devices(deployment_id: str, admin: dict = Depends(get_current_admin)):
    """Manually sync deployment items to devices collection"""
    deployment = await db.deployments.find_one({"id": deployment_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    created_count = 0
    updated_count = 0
    
    for item_idx, item in enumerate(deployment.get("items", [])):
        if item.get("is_serialized") and item.get("serial_numbers"):
            linked_ids = item.get("linked_device_ids", [])
            new_linked_ids = []
            
            for i, serial in enumerate(item["serial_numbers"]):
                if not serial:  # Skip empty serials
                    continue
                    
                # Check if device already exists for this serial in this deployment
                existing_device = await db.devices.find_one({
                    "deployment_id": deployment_id,
                    "serial_number": serial,
                    "is_deleted": {"$ne": True}
                }, {"_id": 0})
                
                if existing_device:
                    # Update existing device
                    await db.devices.update_one(
                        {"id": existing_device["id"]},
                        {"$set": {
                            "device_type": item.get("category"),
                            "category": item.get("category"),
                            "brand": item.get("brand") or "Unknown",
                            "model": item.get("model") or "Unknown",
                            "warranty_end_date": item.get("warranty_end_date"),
                            "location": item.get("zone_location"),
                            "updated_at": get_ist_isoformat()
                        }}
                    )
                    new_linked_ids.append(existing_device["id"])
                    updated_count += 1
                else:
                    # Create new device
                    device_data = {
                        "id": str(uuid.uuid4()),
                        "company_id": deployment["company_id"],
                        "site_id": deployment["site_id"],
                        "deployment_id": deployment_id,
                        "deployment_item_index": item_idx,
                        "source": "deployment",
                        "device_type": item.get("category"),
                        "category": item.get("category"),
                        "brand": item.get("brand") or "Unknown",
                        "model": item.get("model") or "Unknown",
                        "serial_number": serial,
                        "purchase_date": item.get("installation_date") or deployment.get("deployment_date"),
                        "warranty_end_date": item.get("warranty_end_date"),
                        "location": item.get("zone_location"),
                        "status": "active",
                        "condition": "new",
                        "is_deleted": False,
                        "created_at": get_ist_isoformat()
                    }
                    await db.devices.insert_one(device_data)
                    new_linked_ids.append(device_data["id"])
                    created_count += 1
            
            # Update linked_device_ids in deployment item
            if new_linked_ids:
                await db.deployments.update_one(
                    {"id": deployment_id},
                    {"$set": {f"items.{item_idx}.linked_device_ids": new_linked_ids}}
                )
    
    return {
        "message": f"Sync complete. Created {created_count} devices, updated {updated_count} devices.",
        "created": created_count,
        "updated": updated_count
    }

# ==================== UNIVERSAL SEARCH ====================

@api_router.get("/search")
async def universal_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=10, description="Results per category"),
    admin: dict = Depends(get_current_admin)
):
    """
    Universal search across all entities.
    Returns grouped results from companies, sites, users, assets, deployments, AMCs, and services.
    """
    if not q or len(q.strip()) < 1:
        return {
            "companies": [],
            "sites": [],
            "users": [],
            "assets": [],
            "deployments": [],
            "amcs": [],
            "services": []
        }
    
    query = q.strip()
    # Create case-insensitive regex pattern for partial matching
    regex_pattern = {"$regex": query, "$options": "i"}
    
    results = {
        "companies": [],
        "sites": [],
        "users": [],
        "assets": [],
        "deployments": [],
        "amcs": [],
        "services": [],
        "query": query,
        "total_count": 0
    }
    
    # Search Companies
    companies = await db.companies.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"contact_email": regex_pattern},
            {"gst_number": regex_pattern},
            {"address": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for c in companies:
        results["companies"].append({
            "id": c["id"],
            "type": "company",
            "title": c.get("name"),
            "subtitle": c.get("contact_email") or c.get("address", ""),
            "link": f"/admin/companies",
            "icon": "building"
        })
    
    # Search Sites
    sites = await db.sites.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"address": regex_pattern},
            {"city": regex_pattern},
            {"primary_contact_name": regex_pattern},
            {"contact_number": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for s in sites:
        company = await db.companies.find_one({"id": s.get("company_id")}, {"_id": 0, "name": 1})
        results["sites"].append({
            "id": s["id"],
            "type": "site",
            "title": s.get("name"),
            "subtitle": f"{s.get('city', '')} • {company.get('name', '') if company else ''}",
            "link": f"/admin/sites",
            "icon": "map-pin"
        })
    
    # Search Users
    users = await db.users.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"email": regex_pattern},
            {"phone": regex_pattern},
            {"designation": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for u in users:
        results["users"].append({
            "id": u["id"],
            "type": "user",
            "title": u.get("name"),
            "subtitle": u.get("email") or u.get("phone", ""),
            "link": f"/admin/users",
            "icon": "user"
        })
    
    # Search Assets/Devices
    devices = await db.devices.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"serial_number": regex_pattern},
            {"asset_tag": regex_pattern},
            {"brand": regex_pattern},
            {"model": regex_pattern},
            {"device_type": regex_pattern},
            {"location": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for d in devices:
        company = await db.companies.find_one({"id": d.get("company_id")}, {"_id": 0, "name": 1})
        results["assets"].append({
            "id": d["id"],
            "type": "asset",
            "title": f"{d.get('brand', '')} {d.get('model', '')}".strip() or d.get("serial_number"),
            "subtitle": f"S/N: {d.get('serial_number', '')} • {company.get('name', '') if company else ''}",
            "link": f"/admin/devices",
            "icon": "laptop",
            "serial_number": d.get("serial_number"),
            "asset_tag": d.get("asset_tag")
        })
    
    # Search Deployments
    deployments = await db.deployments.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"installed_by": regex_pattern},
            {"notes": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    # Also search deployment items for serial numbers and categories
    deployment_items_search = await db.deployments.find({
        "is_deleted": {"$ne": True},
        "items": {
            "$elemMatch": {
                "$or": [
                    {"serial_numbers": regex_pattern},
                    {"category": regex_pattern},
                    {"brand": regex_pattern},
                    {"model": regex_pattern}
                ]
            }
        }
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    # Combine and dedupe
    all_deployments = {d["id"]: d for d in deployments}
    for d in deployment_items_search:
        if d["id"] not in all_deployments:
            all_deployments[d["id"]] = d
    
    for d in list(all_deployments.values())[:limit]:
        site = await db.sites.find_one({"id": d.get("site_id")}, {"_id": 0, "name": 1})
        results["deployments"].append({
            "id": d["id"],
            "type": "deployment",
            "title": d.get("name"),
            "subtitle": f"{site.get('name', '') if site else ''} • {len(d.get('items', []))} items",
            "link": f"/admin/deployments",
            "icon": "package"
        })
    
    # Search AMC Contracts
    amcs = await db.amc_contracts.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"amc_type": regex_pattern},
            {"internal_notes": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for a in amcs:
        company = await db.companies.find_one({"id": a.get("company_id")}, {"_id": 0, "name": 1})
        status = get_amc_status(a.get("start_date", ""), a.get("end_date", ""))
        results["amcs"].append({
            "id": a["id"],
            "type": "amc",
            "title": a.get("name"),
            "subtitle": f"{company.get('name', '') if company else ''} • {status.capitalize()}",
            "link": f"/admin/amc-contracts",
            "icon": "file-text",
            "status": status
        })
    
    # Search Service History
    services = await db.service_history.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"ticket_id": regex_pattern},
            {"action_taken": regex_pattern},
            {"problem_reported": regex_pattern},
            {"technician_name": regex_pattern},
            {"notes": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for s in services:
        device = await db.devices.find_one({"id": s.get("device_id")}, {"_id": 0, "brand": 1, "model": 1, "serial_number": 1})
        results["services"].append({
            "id": s["id"],
            "type": "service",
            "title": s.get("action_taken", "")[:50] + ("..." if len(s.get("action_taken", "")) > 50 else ""),
            "subtitle": f"{device.get('brand', '')} {device.get('model', '')} • {s.get('service_type', '')}".strip() if device else s.get("service_type", ""),
            "link": f"/admin/service-history",
            "icon": "wrench",
            "ticket_id": s.get("ticket_id")
        })
    
    # Calculate total count
    results["total_count"] = (
        len(results["companies"]) +
        len(results["sites"]) +
        len(results["users"]) +
        len(results["assets"]) +
        len(results["deployments"]) +
        len(results["amcs"]) +
        len(results["services"])
    )
    
    return results

# ==================== ADMIN ENDPOINTS - SETTINGS ====================

@api_router.get("/admin/settings")
async def get_settings(admin: dict = Depends(get_current_admin)):
    settings = await db.settings.find_one({"id": "settings"}, {"_id": 0})
    if not settings:
        settings = Settings().model_dump()
    return settings

@api_router.put("/admin/settings")
async def update_settings(updates: SettingsUpdate, admin: dict = Depends(get_current_admin)):
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.settings.update_one(
        {"id": "settings"},
        {"$set": update_data},
        upsert=True
    )
    
    return await db.settings.find_one({"id": "settings"}, {"_id": 0})

@api_router.post("/admin/settings/logo")
async def upload_logo(file: UploadFile = File(...), admin: dict = Depends(get_current_admin)):
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    content = await file.read()
    base64_string = base64.b64encode(content).decode()
    logo_base64 = f"data:{file.content_type};base64,{base64_string}"
    
    await db.settings.update_one(
        {"id": "settings"},
        {"$set": {"logo_base64": logo_base64, "updated_at": get_ist_isoformat()}},
        upsert=True
    )
    
    return {"message": "Logo uploaded successfully", "logo_base64": logo_base64}

# ==================== ADMIN ENDPOINTS - LICENSES ====================

def calculate_license_status(end_date: Optional[str], reminder_days: int = 30) -> str:
    """Calculate license status based on end date"""
    if not end_date:
        return "active"  # Perpetual license
    
    try:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        today = get_ist_now().date()
        days_until_expiry = (end - today).days
        
        if days_until_expiry < 0:
            return "expired"
        elif days_until_expiry <= reminder_days:
            return "expiring"
        else:
            return "active"
    except Exception:
        return "active"

@api_router.get("/admin/licenses")
async def list_licenses(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    license_type: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List all licenses with optional filters"""
    query = {"is_deleted": {"$ne": True}}
    
    if company_id:
        query["company_id"] = company_id
    if license_type:
        query["license_type"] = license_type
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"software_name": search_regex},
            {"vendor": search_regex},
            {"license_key": search_regex}
        ]
    
    skip = (page - 1) * limit
    licenses = await db.licenses.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with company names and calculate status
    for lic in licenses:
        company = await db.companies.find_one({"id": lic.get("company_id")}, {"_id": 0, "name": 1})
        lic["company_name"] = company.get("name") if company else "Unknown"
        lic["label"] = lic["software_name"]
        
        # Calculate current status
        lic["status"] = calculate_license_status(
            lic.get("end_date"),
            lic.get("renewal_reminder_days", 30)
        )
        
        # Mask license key
        if lic.get("license_key"):
            key = lic["license_key"]
            if len(key) > 8:
                lic["license_key_masked"] = key[:4] + "****" + key[-4:]
            else:
                lic["license_key_masked"] = "****"
    
    # Filter by status if requested (after calculation)
    if status:
        licenses = [lic for lic in licenses if lic["status"] == status]
    
    return licenses

@api_router.post("/admin/licenses")
async def create_license(data: LicenseCreate, admin: dict = Depends(get_current_admin)):
    """Create new license"""
    # Validate company exists
    company = await db.companies.find_one({"id": data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    license_data = data.model_dump()
    license_data["status"] = calculate_license_status(data.end_date, data.renewal_reminder_days)
    
    lic = License(**license_data)
    await db.licenses.insert_one(lic.model_dump())
    await log_audit("license", lic.id, "create", {"data": data.model_dump()}, admin)
    
    result = lic.model_dump()
    result["company_name"] = company.get("name")
    result["label"] = result["software_name"]
    return result

@api_router.get("/admin/licenses/{license_id}")
async def get_license(license_id: str, admin: dict = Depends(get_current_admin)):
    """Get license details"""
    lic = await db.licenses.find_one({"id": license_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not lic:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get company
    company = await db.companies.find_one({"id": lic.get("company_id")}, {"_id": 0})
    lic["company_name"] = company.get("name") if company else "Unknown"
    
    # Get assigned devices/users details
    if lic.get("assigned_device_ids"):
        devices = await db.devices.find(
            {"id": {"$in": lic["assigned_device_ids"]}, "is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "brand": 1, "model": 1, "serial_number": 1}
        ).to_list(100)
        lic["assigned_devices"] = devices
    
    if lic.get("assigned_user_ids"):
        users = await db.users.find(
            {"id": {"$in": lic["assigned_user_ids"]}, "is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1, "email": 1}
        ).to_list(100)
        lic["assigned_users"] = users
    
    lic["status"] = calculate_license_status(lic.get("end_date"), lic.get("renewal_reminder_days", 30))
    
    return lic

@api_router.put("/admin/licenses/{license_id}")
async def update_license(license_id: str, updates: LicenseUpdate, admin: dict = Depends(get_current_admin)):
    """Update license"""
    existing = await db.licenses.find_one({"id": license_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="License not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    # Recalculate status if dates changed
    end_date = update_data.get("end_date", existing.get("end_date"))
    reminder_days = update_data.get("renewal_reminder_days", existing.get("renewal_reminder_days", 30))
    update_data["status"] = calculate_license_status(end_date, reminder_days)
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    await db.licenses.update_one({"id": license_id}, {"$set": update_data})
    await log_audit("license", license_id, "update", changes, admin)
    
    return await db.licenses.find_one({"id": license_id}, {"_id": 0})

@api_router.delete("/admin/licenses/{license_id}")
async def delete_license(license_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete license"""
    result = await db.licenses.update_one({"id": license_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License not found")
    
    await log_audit("license", license_id, "delete", {"is_deleted": True}, admin)
    return {"message": "License deleted"}

@api_router.get("/admin/licenses/expiring/summary")
async def get_expiring_licenses_summary(admin: dict = Depends(get_current_admin)):
    """Get summary of expiring licenses"""
    licenses = await db.licenses.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    
    today = get_ist_now().date()
    summary = {
        "total": len(licenses),
        "perpetual": 0,
        "active": 0,
        "expiring_7_days": [],
        "expiring_30_days": [],
        "expired": []
    }
    
    for lic in licenses:
        if not lic.get("end_date"):
            summary["perpetual"] += 1
            continue
        
        try:
            end = datetime.strptime(lic["end_date"], "%Y-%m-%d").date()
            days = (end - today).days
            
            company = await db.companies.find_one({"id": lic.get("company_id")}, {"_id": 0, "name": 1})
            
            item = {
                "id": lic["id"],
                "software_name": lic["software_name"],
                "company_name": company.get("name") if company else "Unknown",
                "end_date": lic["end_date"],
                "days_until_expiry": days,
                "seats": lic.get("seats", 1)
            }
            
            if days < 0:
                summary["expired"].append(item)
            elif days <= 7:
                summary["expiring_7_days"].append(item)
            elif days <= 30:
                summary["expiring_30_days"].append(item)
            else:
                summary["active"] += 1
        except Exception:
            continue
    
    return summary

# ==================== ADMIN ENDPOINTS - AMC DEVICE ASSIGNMENTS ====================

@api_router.get("/admin/amc-contracts/{contract_id}/devices")
async def get_amc_assigned_devices(contract_id: str, admin: dict = Depends(get_current_admin)):
    """Get all devices assigned to an AMC contract"""
    # Verify contract exists
    contract = await db.amc_contracts.find_one({"id": contract_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    assignments = await db.amc_device_assignments.find(
        {"amc_contract_id": contract_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Enrich with device details
    for assignment in assignments:
        device = await db.devices.find_one({"id": assignment["device_id"]}, {"_id": 0})
        if device:
            assignment["device_brand"] = device.get("brand")
            assignment["device_model"] = device.get("model")
            assignment["device_serial"] = device.get("serial_number")
            assignment["device_type"] = device.get("device_type")
        
        assignment["status"] = calculate_license_status(assignment.get("coverage_end"))
    
    return {
        "contract": contract,
        "assignments": assignments,
        "total_devices": len(assignments)
    }

@api_router.post("/admin/amc-contracts/{contract_id}/assign-device")
async def assign_device_to_amc(
    contract_id: str,
    data: AMCDeviceAssignmentCreate,
    admin: dict = Depends(get_current_admin)
):
    """Assign a single device to an AMC contract"""
    # Verify contract exists
    contract = await db.amc_contracts.find_one({"id": contract_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    # Verify device exists
    device = await db.devices.find_one({"id": data.device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if already assigned
    existing = await db.amc_device_assignments.find_one({
        "amc_contract_id": contract_id,
        "device_id": data.device_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Device already assigned to this contract")
    
    assignment_data = data.model_dump()
    assignment_data["amc_contract_id"] = contract_id
    assignment_data["created_by"] = admin["id"]
    
    assignment = AMCDeviceAssignment(**assignment_data)
    await db.amc_device_assignments.insert_one(assignment.model_dump())
    
    return assignment.model_dump()

@api_router.post("/admin/amc-contracts/{contract_id}/bulk-assign/preview")
async def preview_bulk_amc_assignment(
    contract_id: str,
    data: AMCBulkAssignmentPreview,
    admin: dict = Depends(get_current_admin)
):
    """Preview bulk device assignment to AMC - validates before actual assignment"""
    # Verify contract exists
    contract = await db.amc_contracts.find_one({"id": contract_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    results = {
        "will_be_assigned": [],
        "already_assigned": [],
        "not_found": [],
        "wrong_company": []
    }
    
    contract_company_id = contract.get("company_id")
    
    for identifier in data.device_identifiers:
        identifier = identifier.strip()
        if not identifier:
            continue
        
        # Search by serial number or asset tag
        device = await db.devices.find_one({
            "is_deleted": {"$ne": True},
            "$or": [
                {"serial_number": {"$regex": f"^{identifier}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{identifier}$", "$options": "i"}}
            ]
        }, {"_id": 0})
        
        if not device:
            results["not_found"].append({"identifier": identifier, "reason": "Device not found"})
            continue
        
        # Check if device belongs to same company
        if device.get("company_id") != contract_company_id:
            results["wrong_company"].append({
                "identifier": identifier,
                "device_id": device["id"],
                "device_company": device.get("company_id"),
                "reason": "Device belongs to different company"
            })
            continue
        
        # Check if already assigned
        existing = await db.amc_device_assignments.find_one({
            "amc_contract_id": contract_id,
            "device_id": device["id"]
        })
        
        if existing:
            results["already_assigned"].append({
                "identifier": identifier,
                "device_id": device["id"],
                "serial_number": device.get("serial_number"),
                "reason": "Already assigned to this contract"
            })
        else:
            results["will_be_assigned"].append({
                "identifier": identifier,
                "device_id": device["id"],
                "serial_number": device.get("serial_number"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "device_type": device.get("device_type")
            })
    
    results["summary"] = {
        "total_input": len(data.device_identifiers),
        "will_assign": len(results["will_be_assigned"]),
        "already_assigned": len(results["already_assigned"]),
        "not_found": len(results["not_found"]),
        "wrong_company": len(results["wrong_company"])
    }
    
    return results

@api_router.post("/admin/amc-contracts/{contract_id}/bulk-assign/confirm")
async def confirm_bulk_amc_assignment(
    contract_id: str,
    data: AMCBulkAssignmentPreview,
    admin: dict = Depends(get_current_admin)
):
    """Confirm and execute bulk device assignment to AMC"""
    # First run preview to get valid devices
    preview = await preview_bulk_amc_assignment(contract_id, data, admin)
    
    assigned = []
    for item in preview["will_be_assigned"]:
        assignment_data = {
            "amc_contract_id": contract_id,
            "device_id": item["device_id"],
            "coverage_start": data.coverage_start,
            "coverage_end": data.coverage_end,
            "coverage_source": "bulk_upload",
            "created_by": admin["id"]
        }
        
        assignment = AMCDeviceAssignment(**assignment_data)
        await db.amc_device_assignments.insert_one(assignment.model_dump())
        assigned.append(assignment.model_dump())
    
    return {
        "assigned_count": len(assigned),
        "assignments": assigned,
        "skipped": {
            "already_assigned": len(preview["already_assigned"]),
            "not_found": len(preview["not_found"]),
            "wrong_company": len(preview["wrong_company"])
        }
    }

@api_router.delete("/admin/amc-contracts/{contract_id}/devices/{device_id}")
async def unassign_device_from_amc(
    contract_id: str,
    device_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Remove device assignment from AMC contract"""
    result = await db.amc_device_assignments.delete_one({
        "amc_contract_id": contract_id,
        "device_id": device_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return {"message": "Device unassigned from contract"}

# ==================== ADMIN DASHBOARD WITH ALERTS ====================

@api_router.get("/admin/dashboard")
async def get_dashboard_stats(admin: dict = Depends(get_current_admin)):
    companies_count = await db.companies.count_documents({"is_deleted": {"$ne": True}})
    users_count = await db.users.count_documents({"is_deleted": {"$ne": True}})
    devices_count = await db.devices.count_documents({"is_deleted": {"$ne": True}})
    parts_count = await db.parts.count_documents({"is_deleted": {"$ne": True}})
    services_count = await db.service_history.count_documents({})
    
    today = get_ist_now().strftime('%Y-%m-%d')
    active_warranties = await db.devices.count_documents({
        "is_deleted": {"$ne": True},
        "warranty_end_date": {"$gte": today}
    })
    
    active_amc = await db.amc.count_documents({
        "is_deleted": {"$ne": True},
        "end_date": {"$gte": today}
    })
    
    recent_devices = await db.devices.find({"is_deleted": {"$ne": True}}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    recent_services = await db.service_history.find({}, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "companies_count": companies_count,
        "users_count": users_count,
        "devices_count": devices_count,
        "parts_count": parts_count,
        "services_count": services_count,
        "active_warranties": active_warranties,
        "expired_warranties": devices_count - active_warranties,
        "active_amc": active_amc,
        "recent_devices": recent_devices,
        "recent_services": recent_services
    }

@api_router.get("/admin/dashboard/alerts")
async def get_dashboard_alerts(admin: dict = Depends(get_current_admin)):
    """Get warranty and AMC expiry alerts"""
    today = get_ist_now()
    
    alerts = {
        "warranty_expiring_7_days": [],
        "warranty_expiring_15_days": [],
        "warranty_expiring_30_days": [],
        "amc_expiring_7_days": [],
        "amc_expiring_15_days": [],
        "amc_expiring_30_days": [],
        "devices_in_repair": [],
        "devices_lost": []
    }
    
    # Get all devices with warranty
    devices = await db.devices.find(
        {"is_deleted": {"$ne": True}, "warranty_end_date": {"$ne": None}},
        {"_id": 0}
    ).to_list(1000)
    
    for device in devices:
        days = days_until_expiry(device.get("warranty_end_date", ""))
        if 0 < days <= 7:
            alerts["warranty_expiring_7_days"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "expiry_date": device.get("warranty_end_date"),
                "days_remaining": days
            })
        elif 7 < days <= 15:
            alerts["warranty_expiring_15_days"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "expiry_date": device.get("warranty_end_date"),
                "days_remaining": days
            })
        elif 15 < days <= 30:
            alerts["warranty_expiring_30_days"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "expiry_date": device.get("warranty_end_date"),
                "days_remaining": days
            })
        
        # Status alerts
        if device.get("status") == "in_repair":
            alerts["devices_in_repair"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number")
            })
        elif device.get("status") == "lost":
            alerts["devices_lost"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number")
            })
    
    # AMC alerts
    amc_list = await db.amc.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    for amc in amc_list:
        days = days_until_expiry(amc.get("end_date", ""))
        device = await db.devices.find_one({"id": amc.get("device_id")}, {"_id": 0, "brand": 1, "model": 1, "serial_number": 1})
        if not device:
            continue
            
        alert_item = {
            "amc_id": amc.get("id"),
            "device_id": amc.get("device_id"),
            "brand": device.get("brand"),
            "model": device.get("model"),
            "serial_number": device.get("serial_number"),
            "expiry_date": amc.get("end_date"),
            "days_remaining": days
        }
        
        if 0 < days <= 7:
            alerts["amc_expiring_7_days"].append(alert_item)
        elif 7 < days <= 15:
            alerts["amc_expiring_15_days"].append(alert_item)
        elif 15 < days <= 30:
            alerts["amc_expiring_30_days"].append(alert_item)
    
    # AMC Contract (v2) alerts
    alerts["amc_contracts_expiring_7_days"] = []
    alerts["amc_contracts_expiring_15_days"] = []
    alerts["amc_contracts_expiring_30_days"] = []
    alerts["companies_without_amc"] = []
    
    contracts = await db.amc_contracts.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    for contract in contracts:
        days = days_until_expiry(contract.get("end_date", ""))
        company = await db.companies.find_one({"id": contract.get("company_id")}, {"_id": 0, "name": 1})
        
        alert_item = {
            "contract_id": contract.get("id"),
            "contract_name": contract.get("name"),
            "company_id": contract.get("company_id"),
            "company_name": company.get("name") if company else "Unknown",
            "amc_type": contract.get("amc_type"),
            "expiry_date": contract.get("end_date"),
            "days_remaining": days
        }
        
        if 0 < days <= 7:
            alerts["amc_contracts_expiring_7_days"].append(alert_item)
        elif 7 < days <= 15:
            alerts["amc_contracts_expiring_15_days"].append(alert_item)
        elif 15 < days <= 30:
            alerts["amc_contracts_expiring_30_days"].append(alert_item)
    
    # Companies without any active AMC contract
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    for company in companies:
        has_active_contract = False
        for contract in contracts:
            if contract.get("company_id") == company["id"]:
                status = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
                if status == "active":
                    has_active_contract = True
                    break
        
        if not has_active_contract:
            alerts["companies_without_amc"].append({
                "company_id": company["id"],
                "company_name": company.get("name"),
                "contact_email": company.get("contact_email")
            })
    
    return alerts

# ==================== COMPANY PORTAL ENDPOINTS ====================

# --- Company Auth ---

@api_router.post("/company/auth/login")
async def company_login(login: CompanyLogin):
    """Company user login"""
    user = await db.company_users.find_one({
        "email": login.email.lower(),
        "is_active": True,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not user or not verify_password(login.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Update last login
    await db.company_users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": get_ist_isoformat()}}
    )
    
    # Create token with user type indicator
    access_token = create_access_token(data={"sub": user["id"], "type": "company_user"})
    
    # Get company info
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0, "name": 1})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "company_id": user["company_id"],
            "company_name": company.get("name") if company else None
        }
    }

@api_router.post("/company/auth/register")
async def company_user_register(data: CompanyUserRegister):
    """Self-registration for company users"""
    # Find company by code
    company = await db.companies.find_one({
        "code": data.company_code.upper(),
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not company:
        raise HTTPException(status_code=404, detail="Invalid company code")
    
    # Check if email already exists
    existing = await db.company_users.find_one({"email": data.email.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user (as viewer by default)
    user = CompanyUser(
        company_id=company["id"],
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        name=data.name,
        phone=data.phone,
        role="company_viewer",
        created_by="self_registration"
    )
    
    await db.company_users.insert_one(user.model_dump())
    
    return {"message": "Registration successful. You can now login.", "email": data.email}

@api_router.get("/company/auth/me")
async def get_company_user_info(user: dict = Depends(get_current_company_user)):
    """Get current company user info"""
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0, "name": 1, "code": 1})
    return {
        **user,
        "company_name": company.get("name") if company else None,
        "company_code": company.get("code") if company else None
    }

# --- Company Dashboard ---

@api_router.get("/company/dashboard")
async def get_company_dashboard(user: dict = Depends(get_current_company_user)):
    """Get company dashboard summary"""
    company_id = user["company_id"]
    today = get_ist_now().date()
    
    # Total devices
    total_devices = await db.devices.count_documents({
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    })
    
    # Get all devices for warranty calculations
    devices = await db.devices.find({
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "id": 1, "warranty_end_date": 1}).to_list(1000)
    
    warranties_30 = 0
    warranties_60 = 0
    warranties_90 = 0
    
    for device in devices:
        end_date = device.get("warranty_end_date")
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                days_left = (end - today).days
                if 0 < days_left <= 30:
                    warranties_30 += 1
                elif 30 < days_left <= 60:
                    warranties_60 += 1
                elif 60 < days_left <= 90:
                    warranties_90 += 1
            except:
                pass
    
    # Active AMC contracts
    active_amc = await db.amc_contracts.count_documents({
        "company_id": company_id,
        "is_deleted": {"$ne": True},
        "end_date": {"$gte": today.isoformat()}
    })
    
    # Open service tickets
    open_tickets = await db.service_tickets.count_documents({
        "company_id": company_id,
        "status": {"$in": ["open", "in_progress"]},
        "is_deleted": {"$ne": True}
    })
    
    # Recent tickets
    recent_tickets = await db.service_tickets.find({
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "total_devices": total_devices,
        "warranties_expiring_30_days": warranties_30,
        "warranties_expiring_60_days": warranties_60,
        "warranties_expiring_90_days": warranties_90,
        "active_amc_contracts": active_amc,
        "open_service_tickets": open_tickets,
        "recent_tickets": recent_tickets
    }

# --- Company Devices (Read-Only) ---

@api_router.get("/company/devices")
async def list_company_devices(
    user: dict = Depends(get_current_company_user),
    search: Optional[str] = None,
    device_type: Optional[str] = None,
    site_id: Optional[str] = None,
    warranty_status: Optional[str] = None
):
    """List all devices for the company (read-only)"""
    company_id = user["company_id"]
    query = {"company_id": company_id, "is_deleted": {"$ne": True}}
    
    if device_type:
        query["device_type"] = device_type
    if site_id:
        query["site_id"] = site_id
    
    devices = await db.devices.find(query, {"_id": 0}).to_list(1000)
    today = get_ist_now().date()
    
    result = []
    for device in devices:
        # Calculate warranty status
        warranty_end = device.get("warranty_end_date")
        if warranty_end:
            try:
                end = datetime.strptime(warranty_end, "%Y-%m-%d").date()
                days_left = (end - today).days
                device["warranty_status"] = "active" if days_left > 0 else "expired"
                device["warranty_days_left"] = max(0, days_left)
            except:
                device["warranty_status"] = "unknown"
                device["warranty_days_left"] = 0
        else:
            device["warranty_status"] = "not_set"
            device["warranty_days_left"] = 0
        
        # Check AMC coverage
        amc_assignment = await db.amc_device_assignments.find_one({
            "device_id": device["id"],
            "status": "active"
        }, {"_id": 0})
        
        if amc_assignment:
            amc_end = amc_assignment.get("coverage_end")
            if amc_end and is_warranty_active(amc_end):
                device["amc_covered"] = True
                device["amc_coverage_end"] = amc_end
            else:
                device["amc_covered"] = False
        else:
            device["amc_covered"] = False
        
        # Get assigned user name
        if device.get("assigned_user_id"):
            assigned_user = await db.users.find_one({"id": device["assigned_user_id"]}, {"_id": 0, "name": 1})
            device["assigned_user_name"] = assigned_user.get("name") if assigned_user else None
        
        # Get site name
        if device.get("site_id"):
            site = await db.sites.find_one({"id": device["site_id"]}, {"_id": 0, "name": 1})
            device["site_name"] = site.get("name") if site else None
        
        # Filter by warranty status if specified
        if warranty_status:
            if warranty_status == "active" and device["warranty_status"] != "active":
                continue
            if warranty_status == "expired" and device["warranty_status"] != "expired":
                continue
            if warranty_status == "expiring_soon" and device.get("warranty_days_left", 0) > 30:
                continue
        
        # Apply search filter
        if search:
            search_lower = search.lower()
            searchable = f"{device.get('serial_number', '')} {device.get('asset_tag', '')} {device.get('brand', '')} {device.get('model', '')}".lower()
            if search_lower not in searchable:
                continue
        
        result.append(device)
    
    return result

@api_router.get("/company/devices/{device_id}")
async def get_company_device(device_id: str, user: dict = Depends(get_current_company_user)):
    """Get single device details (read-only)"""
    device = await db.devices.find_one({
        "id": device_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get parts
    parts = await db.parts.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    # Get service history
    services = await db.service_history.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("service_date", -1).to_list(50)
    
    # Get AMC info
    amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device_id,
        "status": "active"
    }, {"_id": 0})
    
    amc_info = None
    if amc_assignment:
        amc_contract = await db.amc_contracts.find_one({
            "id": amc_assignment["amc_contract_id"]
        }, {"_id": 0})
        if amc_contract:
            amc_info = {
                "contract_name": amc_contract.get("name"),
                "amc_type": amc_contract.get("amc_type"),
                "coverage_start": amc_assignment.get("coverage_start"),
                "coverage_end": amc_assignment.get("coverage_end"),
                "coverage_includes": amc_contract.get("coverage_includes"),
                "entitlements": amc_contract.get("entitlements")
            }
    
    return {
        "device": device,
        "parts": parts,
        "service_history": services,
        "amc_info": amc_info
    }

# --- Consumable Orders ---

@api_router.post("/company/devices/{device_id}/order-consumable")
async def order_consumable(device_id: str, order_data: dict, user: dict = Depends(get_current_company_user)):
    """Order consumables for a printer device - supports multiple items"""
    # Verify device belongs to company
    device = await db.devices.find_one({
        "id": device_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if it's a printer
    device_type = (device.get("device_type") or "").lower()
    if "printer" not in device_type:
        raise HTTPException(status_code=400, detail="Consumable orders are only available for printers")
    
    # Get company details
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0})
    
    # Get site details
    site = None
    if device.get("site_id"):
        site = await db.sites.find_one({"id": device["site_id"]}, {"_id": 0})
    
    # Get consumable order history for this device
    order_history = await db.consumable_orders.find(
        {"device_id": device_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Get service history
    service_history = await db.service_history.find(
        {"device_id": device_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("service_date", -1).limit(5).to_list(5)
    
    # Process order items - support both legacy single item and new multiple items format
    order_items = order_data.get("items", [])
    
    # Legacy support: if no items array but has consumable_type/quantity, create single item
    if not order_items and (order_data.get("quantity") or order_data.get("consumable_type")):
        order_items = [{
            "consumable_id": "legacy",
            "name": order_data.get("consumable_type") or device.get("consumable_type") or "Consumable",
            "consumable_type": order_data.get("consumable_type") or device.get("consumable_type") or "Consumable",
            "model_number": order_data.get("consumable_model") or device.get("consumable_model") or "",
            "brand": device.get("consumable_brand"),
            "quantity": order_data.get("quantity", 1)
        }]
    
    if not order_items:
        raise HTTPException(status_code=400, detail="No items specified in order")
    
    # Calculate total quantity
    total_quantity = sum(item.get("quantity", 1) for item in order_items)
    
    # Create the order
    order = ConsumableOrder(
        company_id=user["company_id"],
        device_id=device_id,
        requested_by=user["id"],
        requested_by_name=user.get("name", "Unknown"),
        requested_by_email=user.get("email", ""),
        # Legacy fields for backward compatibility
        consumable_type=order_items[0].get("consumable_type") if len(order_items) == 1 else "Multiple Items",
        consumable_model=order_items[0].get("model_number") if len(order_items) == 1 else f"{len(order_items)} items",
        quantity=total_quantity,
        # New multi-item support
        items=order_items,
        notes=order_data.get("notes")
    )
    
    await db.consumable_orders.insert_one(order.model_dump())
    
    # Helper function
    def format_date(date_str):
        if not date_str:
            return "N/A"
        try:
            if 'T' in str(date_str):
                return str(date_str).split('T')[0]
            return str(date_str)
        except:
            return str(date_str)
    
    # Build osTicket message with multiple items support
    osticket_message = f"""
<h2>CONSUMABLE ORDER REQUEST</h2>
<p><strong>Order Number:</strong> {order.order_number}</p>
<p><strong>Order Date:</strong> {format_date(order.created_at)}</p>
<p><strong>Total Items:</strong> {len(order_items)} item(s), {total_quantity} unit(s)</p>

<hr>
<h3>CONSUMABLES ORDERED</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #e0f2e9;">
<th>Item</th><th>Type</th><th>Model/Part No.</th><th>Brand</th><th>Color</th><th>Qty</th>
</tr>
"""
    
    for idx, item in enumerate(order_items, 1):
        color_display = item.get("color") or "-"
        brand_display = item.get("brand") or "-"
        osticket_message += f"""
<tr>
<td>{item.get('name', f'Item {idx}')}</td>
<td>{item.get('consumable_type', 'N/A')}</td>
<td><strong>{item.get('model_number', 'N/A')}</strong></td>
<td>{brand_display}</td>
<td>{color_display}</td>
<td><strong>{item.get('quantity', 1)}</strong></td>
</tr>
"""
    
    osticket_message += f"""
</table>
<p><strong>Special Notes:</strong> {order.notes or 'None'}</p>

<hr>
<h3>PRINTER DETAILS</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Serial Number</strong></td><td><strong>{device.get('serial_number', 'N/A')}</strong></td></tr>
<tr><td><strong>Brand</strong></td><td>{device.get('brand', 'N/A')}</td></tr>
<tr><td><strong>Model</strong></td><td>{device.get('model', 'N/A')}</td></tr>
<tr><td><strong>Asset Tag</strong></td><td>{device.get('asset_tag') or 'N/A'}</td></tr>
<tr><td><strong>Location</strong></td><td>{device.get('location') or 'N/A'}</td></tr>
<tr><td><strong>Status</strong></td><td>{device.get('status', 'N/A')}</td></tr>
<tr><td><strong>Condition</strong></td><td>{device.get('condition', 'N/A')}</td></tr>
</table>

<hr>
<h3>COMPANY INFORMATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Company Name</strong></td><td>{company.get('name', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Person</strong></td><td>{company.get('contact_name', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Email</strong></td><td>{company.get('contact_email', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{company.get('contact_phone', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Address</strong></td><td>{company.get('address', 'N/A') if company else 'N/A'}</td></tr>
</table>

<hr>
<h3>ORDERED BY</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Name</strong></td><td>{user.get('name', 'N/A')}</td></tr>
<tr><td><strong>Email</strong></td><td>{user.get('email', 'N/A')}</td></tr>
<tr><td><strong>Phone</strong></td><td>{user.get('phone', 'N/A')}</td></tr>
</table>
"""

    # Add Site Information if available
    if site:
        osticket_message += f"""
<hr>
<h3>DELIVERY LOCATION (Site)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Site Name</strong></td><td>{site.get('name', 'N/A')}</td></tr>
<tr><td><strong>Address</strong></td><td>{site.get('address', 'N/A')}</td></tr>
<tr><td><strong>City</strong></td><td>{site.get('city', 'N/A')}</td></tr>
<tr><td><strong>State</strong></td><td>{site.get('state', 'N/A')}</td></tr>
<tr><td><strong>Pincode</strong></td><td>{site.get('pincode', 'N/A')}</td></tr>
<tr><td><strong>Contact Person</strong></td><td>{site.get('contact_person', 'N/A')}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{site.get('contact_phone', 'N/A')}</td></tr>
</table>
"""

    # Add Order History
    if order_history:
        osticket_message += f"""
<hr>
<h3>PREVIOUS CONSUMABLE ORDERS FOR THIS PRINTER ({len(order_history)} records)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>Order #</th><th>Date</th><th>Item</th><th>Qty</th><th>Status</th>
</tr>
"""
        for hist in order_history:
            if hist.get('order_number') != order.order_number:  # Skip current order
                osticket_message += f"""
<tr>
<td>{hist.get('order_number', 'N/A')}</td>
<td>{format_date(hist.get('created_at'))}</td>
<td>{hist.get('consumable_type', 'N/A')} - {hist.get('consumable_model', 'N/A')}</td>
<td>{hist.get('quantity', 1)}</td>
<td>{hist.get('status', 'N/A').upper()}</td>
</tr>
"""
        osticket_message += "</table>"
    else:
        osticket_message += """
<hr>
<h3>PREVIOUS CONSUMABLE ORDERS</h3>
<p><em>This is the first consumable order for this printer.</em></p>
"""

    # Add Service History
    if service_history:
        osticket_message += f"""
<hr>
<h3>RECENT SERVICE HISTORY ({len(service_history)} records)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>Date</th><th>Service Type</th><th>Problem</th><th>Status</th>
</tr>
"""
        for svc in service_history:
            osticket_message += f"""
<tr>
<td>{format_date(svc.get('service_date'))}</td>
<td>{svc.get('service_type', 'N/A')}</td>
<td>{(svc.get('problem_reported', 'N/A') or 'N/A')[:50]}...</td>
<td>{svc.get('status', 'N/A')}</td>
</tr>
"""
        osticket_message += "</table>"

    osticket_message += f"""
<hr>
<p style="color: #666; font-size: 12px;">
<em>This consumable order was submitted from the Warranty & Asset Tracking Portal.<br>
Order Created: {get_ist_isoformat()}</em>
</p>
"""

    # Create osTicket - build subject for multi-item orders
    if len(order_items) == 1:
        consumable_info = f"{order_items[0].get('name', 'Consumable')} x {order_items[0].get('quantity', 1)}"
    else:
        consumable_info = f"{len(order_items)} items, {total_quantity} units"
    
    osticket_result = await create_osticket(
        email=user.get("email", "noreply@warranty-portal.com"),
        name=user.get("name", "Portal User"),
        subject=f"[{order.order_number}] Consumable Order: {consumable_info}",
        message=osticket_message,
        phone=user.get("phone", "")
    )
    
    osticket_id = osticket_result.get("ticket_id")
    osticket_error = osticket_result.get("error")
    
    # Update order with osTicket ID
    if osticket_id:
        await db.consumable_orders.update_one(
            {"id": order.id},
            {"$set": {"osticket_id": osticket_id}}
        )
    
    return {
        "message": "Consumable order submitted successfully",
        "order_number": order.order_number,
        "id": order.id,
        "items_count": len(order_items),
        "total_quantity": total_quantity,
        "osticket_id": osticket_id,
        "osticket_error": osticket_error
    }

@api_router.get("/company/consumable-orders")
async def list_company_consumable_orders(user: dict = Depends(get_current_company_user)):
    """List consumable orders for the company"""
    orders = await db.consumable_orders.find(
        {"company_id": user["company_id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with device info
    for order in orders:
        device = await db.devices.find_one({"id": order["device_id"]}, {"_id": 0, "serial_number": 1, "brand": 1, "model": 1})
        if device:
            order["device_serial"] = device.get("serial_number")
            order["device_name"] = f"{device.get('brand', '')} {device.get('model', '')}"
    
    return orders

# --- Company AMC Contracts ---

@api_router.get("/company/amc-contracts")
async def list_company_amc_contracts(user: dict = Depends(get_current_company_user)):
    """List all AMC contracts for the company"""
    contracts = await db.amc_contracts.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    today = get_ist_now().date()
    result = []
    
    for contract in contracts:
        end_date = contract.get("end_date")
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                days_left = (end - today).days
                contract["status"] = "active" if days_left > 0 else "expired"
                contract["days_remaining"] = max(0, days_left)
            except:
                contract["status"] = "unknown"
                contract["days_remaining"] = 0
        
        # Count covered devices
        device_count = await db.amc_device_assignments.count_documents({
            "amc_contract_id": contract["id"],
            "status": "active"
        })
        contract["devices_covered"] = device_count
        
        result.append(contract)
    
    return result

# --- Company Service Tickets ---

@api_router.get("/company/tickets")
async def list_company_tickets(
    user: dict = Depends(get_current_company_user),
    status: Optional[str] = None
):
    """List service tickets for the company"""
    query = {
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }
    if status:
        query["status"] = status
    
    tickets = await db.service_tickets.find(query, {"_id": 0}).sort("created_at", -1).to_list(200)
    
    # Enrich with device info
    for ticket in tickets:
        device = await db.devices.find_one({"id": ticket["device_id"]}, {"_id": 0, "serial_number": 1, "brand": 1, "model": 1, "device_type": 1})
        if device:
            ticket["device_info"] = f"{device.get('brand', '')} {device.get('model', '')} ({device.get('serial_number', '')})"
            ticket["device_type"] = device.get("device_type")
    
    return tickets

@api_router.post("/company/tickets")
async def create_company_ticket(data: ServiceTicketCreate, user: dict = Depends(get_current_company_user)):
    """Create a new service ticket"""
    # Verify device belongs to company
    device = await db.devices.find_one({
        "id": data.device_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get ALL related data for comprehensive osTicket message
    # 1. Company details
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0})
    
    # 2. Site details (if device has site_id)
    site = None
    if device.get("site_id"):
        site = await db.sites.find_one({"id": device["site_id"]}, {"_id": 0})
    
    # 3. Assigned user details (if device has assigned_user_id)
    assigned_user = None
    if device.get("assigned_user_id"):
        assigned_user = await db.users.find_one({"id": device["assigned_user_id"]}, {"_id": 0})
    
    # 4. Service history for this device
    service_history = await db.service_history.find(
        {"device_id": device["id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("service_date", -1).limit(10).to_list(10)
    
    # 5. AMC contract details (new system)
    amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device["id"],
        "status": "active"
    }, {"_id": 0})
    
    amc_contract = None
    if amc_assignment:
        amc_contract = await db.amc_contracts.find_one(
            {"id": amc_assignment.get("amc_contract_id")},
            {"_id": 0}
        )
        # Merge assignment dates into contract info
        if amc_contract:
            amc_contract["coverage_start"] = amc_assignment.get("coverage_start")
            amc_contract["coverage_end"] = amc_assignment.get("coverage_end")
    
    # 5b. Legacy AMC (old system - for backward compatibility)
    legacy_amc = await db.amc.find_one({
        "device_id": device["id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    # 6. Deployment details (if device came from deployment)
    deployment = None
    if device.get("deployment_id"):
        deployment = await db.deployments.find_one({"id": device["deployment_id"]}, {"_id": 0})
    
    # 7. Previous tickets for this device (for context)
    previous_tickets = await db.service_tickets.find(
        {"device_id": device["id"], "is_deleted": {"$ne": True}},
        {"_id": 0, "ticket_number": 1, "subject": 1, "status": 1, "created_at": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    # Create the ticket
    ticket = ServiceTicket(
        company_id=user["company_id"],
        device_id=data.device_id,
        created_by=user["id"],
        issue_category=data.issue_category,
        subject=data.subject,
        description=data.description,
        attachments=data.attachments
    )
    
    await db.service_tickets.insert_one(ticket.model_dump())
    
    # 7. Get parts/components for this device
    parts = await db.parts.find(
        {"device_id": device["id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(50)
    
    # Build comprehensive osTicket message
    def format_date(date_str):
        if not date_str:
            return "N/A"
        try:
            if 'T' in str(date_str):
                return str(date_str).split('T')[0]
            return str(date_str)
        except:
            return str(date_str)
    
    # Calculate warranty status
    warranty_status = "Unknown"
    warranty_days_left = "N/A"
    if device.get("warranty_end_date"):
        try:
            end_date = datetime.strptime(device["warranty_end_date"], '%Y-%m-%d')
            today = get_ist_now().replace(tzinfo=None)
            days_left = (end_date.date() - today.date()).days
            if days_left < 0:
                warranty_status = "[EXPIRED]"
                warranty_days_left = f"{abs(days_left)} days ago"
            elif days_left <= 30:
                warranty_status = "[EXPIRING SOON]"
                warranty_days_left = f"{days_left} days remaining"
            else:
                warranty_status = "[ACTIVE]"
                warranty_days_left = f"{days_left} days remaining"
        except:
            pass
    
    osticket_message = f"""
<h2>SERVICE REQUEST FROM WARRANTY PORTAL</h2>
<p><strong>Portal Ticket #:</strong> {ticket.ticket_number}</p>
<p><strong>Issue Category:</strong> {data.issue_category or 'General'}</p>
<p><strong>Priority:</strong> {data.priority if hasattr(data, 'priority') else 'Medium'}</p>

<hr>
<h3>ISSUE DESCRIPTION</h3>
<p>{data.description}</p>

<hr>
<h3>COMPANY INFORMATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Company Name</strong></td><td>{company.get('name', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Company Code</strong></td><td>{company.get('code', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Person</strong></td><td>{company.get('contact_name', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Email</strong></td><td>{company.get('contact_email', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{company.get('contact_phone', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Address</strong></td><td>{company.get('address', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>City</strong></td><td>{company.get('city', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>State</strong></td><td>{company.get('state', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>GST Number</strong></td><td>{company.get('gst_number', 'N/A') if company else 'N/A'}</td></tr>
</table>

<hr>
<h3>TICKET RAISED BY</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Name</strong></td><td>{user.get('name', 'N/A')}</td></tr>
<tr><td><strong>Email</strong></td><td>{user.get('email', 'N/A')}</td></tr>
<tr><td><strong>Phone</strong></td><td>{user.get('phone', 'N/A')}</td></tr>
<tr><td><strong>Role</strong></td><td>{user.get('role', 'N/A')}</td></tr>
</table>

<hr>
<h3>DEVICE INFORMATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Serial Number</strong></td><td><strong>{device.get('serial_number', 'N/A')}</strong></td></tr>
<tr><td><strong>Device Type</strong></td><td>{device.get('device_type', 'N/A')}</td></tr>
<tr><td><strong>Category</strong></td><td>{device.get('category', 'N/A')}</td></tr>
<tr><td><strong>Brand</strong></td><td>{device.get('brand', 'N/A')}</td></tr>
<tr><td><strong>Model</strong></td><td>{device.get('model', 'N/A')}</td></tr>
<tr><td><strong>Asset Tag</strong></td><td>{device.get('asset_tag', 'N/A')}</td></tr>
<tr><td><strong>Condition</strong></td><td>{device.get('condition', 'N/A')}</td></tr>
<tr><td><strong>Status</strong></td><td>{device.get('status', 'N/A')}</td></tr>
<tr><td><strong>Purchase Date</strong></td><td>{format_date(device.get('purchase_date'))}</td></tr>
<tr><td><strong>Purchase Cost</strong></td><td>{device.get('purchase_cost', 'N/A')}</td></tr>
<tr><td><strong>Vendor</strong></td><td>{device.get('vendor', 'N/A')}</td></tr>
<tr><td><strong>Location</strong></td><td>{device.get('location', 'N/A')}</td></tr>
<tr><td><strong>Notes</strong></td><td>{device.get('notes', 'N/A')}</td></tr>
</table>

<hr>
<h3>WARRANTY INFORMATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Warranty Status</strong></td><td><strong>{warranty_status}</strong></td></tr>
<tr><td><strong>Warranty Start</strong></td><td>{format_date(device.get('warranty_start_date'))}</td></tr>
<tr><td><strong>Warranty End</strong></td><td>{format_date(device.get('warranty_end_date'))}</td></tr>
<tr><td><strong>Days Remaining</strong></td><td>{warranty_days_left}</td></tr>
</table>
"""

    # Add Site Information if available
    if site:
        osticket_message += f"""
<hr>
<h3>SITE / LOCATION DETAILS</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Site Name</strong></td><td>{site.get('name', 'N/A')}</td></tr>
<tr><td><strong>Site Code</strong></td><td>{site.get('code', 'N/A')}</td></tr>
<tr><td><strong>Address</strong></td><td>{site.get('address', 'N/A')}</td></tr>
<tr><td><strong>City</strong></td><td>{site.get('city', 'N/A')}</td></tr>
<tr><td><strong>State</strong></td><td>{site.get('state', 'N/A')}</td></tr>
<tr><td><strong>Pincode</strong></td><td>{site.get('pincode', 'N/A')}</td></tr>
<tr><td><strong>Contact Person</strong></td><td>{site.get('contact_person', 'N/A')}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{site.get('contact_phone', 'N/A')}</td></tr>
<tr><td><strong>Contact Email</strong></td><td>{site.get('contact_email', 'N/A')}</td></tr>
</table>
"""

    # Add Assigned User if available
    if assigned_user:
        osticket_message += f"""
<hr>
<h3>ASSIGNED USER (DEVICE USER)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Name</strong></td><td>{assigned_user.get('name', 'N/A')}</td></tr>
<tr><td><strong>Email</strong></td><td>{assigned_user.get('email', 'N/A')}</td></tr>
<tr><td><strong>Phone</strong></td><td>{assigned_user.get('phone', 'N/A')}</td></tr>
<tr><td><strong>Department</strong></td><td>{assigned_user.get('department', 'N/A')}</td></tr>
<tr><td><strong>Designation</strong></td><td>{assigned_user.get('designation', 'N/A')}</td></tr>
</table>
"""

    # Add Parts/Components if available
    if parts:
        osticket_message += f"""
<hr>
<h3>PARTS / COMPONENTS ({len(parts)} items)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>Part Name</th><th>Serial Number</th><th>Replaced Date</th><th>Warranty (Months)</th><th>Warranty Expiry</th><th>Status</th>
</tr>
"""
        for part in parts:
            part_warranty_active = is_warranty_active(part.get("warranty_expiry_date", ""))
            part_status = "[COVERED]" if part_warranty_active else "[EXPIRED]"
            osticket_message += f"""
<tr>
<td>{part.get('part_name', 'N/A')}</td>
<td>{part.get('serial_number', 'N/A')}</td>
<td>{format_date(part.get('replaced_date'))}</td>
<td>{part.get('warranty_months', 'N/A')}</td>
<td>{format_date(part.get('warranty_expiry_date'))}</td>
<td>{part_status}</td>
</tr>
"""
        osticket_message += "</table>"
    else:
        osticket_message += """
<hr>
<h3>PARTS / COMPONENTS</h3>
<p><em>No replacement parts recorded for this device.</em></p>
"""

    # Add AMC Contract if available (new system)
    if amc_contract:
        amc_end = amc_contract.get('coverage_end') or amc_contract.get('end_date', '')
        amc_start = amc_contract.get('coverage_start') or amc_contract.get('start_date', '')
        amc_status = "[ACTIVE]" if is_warranty_active(amc_end) else "[EXPIRED]"
        osticket_message += f"""
<hr>
<h3>AMC CONTRACT DETAILS</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Contract Number</strong></td><td>{amc_contract.get('contract_number', amc_contract.get('name', 'N/A'))}</td></tr>
<tr><td><strong>AMC Status</strong></td><td><strong>{amc_status}</strong></td></tr>
<tr><td><strong>Contract Type</strong></td><td>{amc_contract.get('contract_type', amc_contract.get('amc_type', 'N/A'))}</td></tr>
<tr><td><strong>Coverage Start</strong></td><td>{format_date(amc_start)}</td></tr>
<tr><td><strong>Coverage End</strong></td><td>{format_date(amc_end)}</td></tr>
<tr><td><strong>Coverage Type</strong></td><td>{amc_contract.get('coverage_type', 'N/A')}</td></tr>
<tr><td><strong>Service Visits Allowed</strong></td><td>{amc_contract.get('service_visits', amc_contract.get('visits_allowed', 'N/A'))}</td></tr>
<tr><td><strong>Contract Value</strong></td><td>{amc_contract.get('value', amc_contract.get('contract_value', 'N/A'))}</td></tr>
<tr><td><strong>Coverage Includes</strong></td><td>{', '.join(amc_contract.get('coverage_includes', [])) if amc_contract.get('coverage_includes') else 'N/A'}</td></tr>
</table>
"""
    # Add Legacy AMC if available and no new AMC contract
    elif legacy_amc:
        legacy_amc_status = "[ACTIVE]" if is_warranty_active(legacy_amc.get('end_date', '')) else "[EXPIRED]"
        osticket_message += f"""
<hr>
<h3>AMC DETAILS (Legacy)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>AMC Status</strong></td><td><strong>{legacy_amc_status}</strong></td></tr>
<tr><td><strong>Start Date</strong></td><td>{format_date(legacy_amc.get('start_date'))}</td></tr>
<tr><td><strong>End Date</strong></td><td>{format_date(legacy_amc.get('end_date'))}</td></tr>
<tr><td><strong>Provider</strong></td><td>{legacy_amc.get('provider', 'N/A')}</td></tr>
<tr><td><strong>Coverage Type</strong></td><td>{legacy_amc.get('coverage_type', 'N/A')}</td></tr>
<tr><td><strong>Notes</strong></td><td>{legacy_amc.get('notes', 'N/A')}</td></tr>
</table>
"""
    else:
        osticket_message += """
<hr>
<h3>AMC DETAILS</h3>
<p><em>No active AMC contract found for this device.</em></p>
"""

    # Add Deployment Info if available
    if deployment:
        osticket_message += f"""
<hr>
<h3>DEPLOYMENT INFORMATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Deployment Number</strong></td><td>{deployment.get('deployment_number', 'N/A')}</td></tr>
<tr><td><strong>Deployment Date</strong></td><td>{format_date(deployment.get('deployment_date'))}</td></tr>
<tr><td><strong>PO Number</strong></td><td>{deployment.get('po_number', 'N/A')}</td></tr>
<tr><td><strong>Invoice Number</strong></td><td>{deployment.get('invoice_number', 'N/A')}</td></tr>
<tr><td><strong>Notes</strong></td><td>{deployment.get('notes', 'N/A')}</td></tr>
</table>
"""

    # Add Previous Tickets for this device
    if previous_tickets and len(previous_tickets) > 1:  # More than just the current ticket
        osticket_message += f"""
<hr>
<h3>PREVIOUS TICKETS FOR THIS DEVICE ({len(previous_tickets) - 1} prior)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>Ticket #</th><th>Subject</th><th>Status</th><th>Created</th>
</tr>
"""
        for prev_ticket in previous_tickets:
            if prev_ticket.get('ticket_number') != ticket.ticket_number:  # Exclude current ticket
                osticket_message += f"""
<tr>
<td>{prev_ticket.get('ticket_number', 'N/A')}</td>
<td>{prev_ticket.get('subject', 'N/A')[:50]}{'...' if len(prev_ticket.get('subject', '')) > 50 else ''}</td>
<td>{prev_ticket.get('status', 'N/A').upper()}</td>
<td>{format_date(prev_ticket.get('created_at'))}</td>
</tr>
"""
        osticket_message += "</table>"

    # Add Service History if available
    if service_history:
        osticket_message += f"""
<hr>
<h3>SERVICE HISTORY (Last {len(service_history)} Records)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>Date</th><th>Service Type</th><th>Problem</th><th>Resolution</th><th>Technician</th><th>Status</th>
</tr>
"""
        for svc in service_history:
            problem = svc.get('problem_reported', 'N/A')
            resolution = svc.get('resolution', 'N/A')
            osticket_message += f"""
<tr>
<td>{format_date(svc.get('service_date'))}</td>
<td>{svc.get('service_type', 'N/A')}</td>
<td>{problem[:100] if problem else 'N/A'}{'...' if problem and len(problem) > 100 else ''}</td>
<td>{resolution[:100] if resolution else 'N/A'}{'...' if resolution and len(resolution) > 100 else ''}</td>
<td>{svc.get('technician_name', 'N/A')}</td>
<td>{svc.get('status', 'N/A')}</td>
</tr>
"""
        osticket_message += "</table>"
    else:
        osticket_message += """
<hr>
<h3>SERVICE HISTORY</h3>
<p><em>No previous service records found for this device.</em></p>
"""

    osticket_message += f"""
<hr>
<p style="color: #666; font-size: 12px;">
<em>This ticket was auto-generated from the Warranty & Asset Tracking Portal.<br>
Ticket Created: {get_ist_isoformat()}</em>
</p>
"""
    
    osticket_result = await create_osticket(
        email=user.get("email", "noreply@warranty-portal.com"),
        name=user.get("name", "Portal User"),
        subject=f"[{ticket.ticket_number}] {data.subject}",
        message=osticket_message,
        phone=user.get("phone", "")
    )
    
    osticket_id = osticket_result.get("ticket_id")
    osticket_error = osticket_result.get("error")
    
    # Update ticket with osTicket reference if created successfully
    if osticket_id:
        await db.service_tickets.update_one(
            {"id": ticket.id},
            {"$set": {"osticket_id": osticket_id}}
        )
    
    return {
        "message": "Ticket created successfully", 
        "ticket_number": ticket.ticket_number, 
        "id": ticket.id,
        "osticket_id": osticket_id,
        "osticket_error": osticket_error
    }

@api_router.get("/company/tickets/{ticket_id}")
async def get_company_ticket(ticket_id: str, user: dict = Depends(get_current_company_user)):
    """Get ticket details"""
    ticket = await db.service_tickets.find_one({
        "id": ticket_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get device info
    device = await db.devices.find_one({"id": ticket["device_id"]}, {"_id": 0})
    ticket["device"] = device
    
    # Get creator info
    creator = await db.company_users.find_one({"id": ticket["created_by"]}, {"_id": 0, "name": 1, "email": 1})
    ticket["created_by_name"] = creator.get("name") if creator else "Unknown"
    
    return ticket

@api_router.post("/company/tickets/{ticket_id}/comments")
async def add_ticket_comment(ticket_id: str, data: ServiceTicketComment, user: dict = Depends(get_current_company_user)):
    """Add comment to a ticket"""
    ticket = await db.service_tickets.find_one({
        "id": ticket_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    comment = {
        "id": str(uuid.uuid4()),
        "user_id": user["id"],
        "user_name": user["name"],
        "user_type": "company",
        "comment": data.comment,
        "attachments": data.attachments,
        "created_at": get_ist_isoformat()
    }
    
    await db.service_tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"comments": comment},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    return {"message": "Comment added", "comment": comment}

# --- Company Renewal Requests ---

@api_router.post("/company/renewal-requests")
async def create_renewal_request(data: RenewalRequestCreate, user: dict = Depends(get_current_company_user)):
    """Create a warranty/AMC renewal request"""
    # Verify device/contract belongs to company
    if data.device_id:
        device = await db.devices.find_one({
            "id": data.device_id,
            "company_id": user["company_id"],
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
    
    if data.amc_contract_id:
        contract = await db.amc_contracts.find_one({
            "id": data.amc_contract_id,
            "company_id": user["company_id"],
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        if not contract:
            raise HTTPException(status_code=404, detail="AMC contract not found")
    
    request = RenewalRequest(
        company_id=user["company_id"],
        request_type=data.request_type,
        device_id=data.device_id,
        amc_contract_id=data.amc_contract_id,
        requested_by=user["id"],
        notes=data.notes
    )
    
    await db.renewal_requests.insert_one(request.model_dump())
    
    return {"message": "Renewal request submitted", "request_number": request.request_number}

@api_router.get("/company/renewal-requests")
async def list_renewal_requests(user: dict = Depends(get_current_company_user)):
    """List renewal requests for the company"""
    requests = await db.renewal_requests.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return requests

# --- Company Profile ---

@api_router.get("/company/profile")
async def get_company_profile(user: dict = Depends(get_current_company_user)):
    """Get user profile with company info"""
    company = await db.companies.find_one({
        "id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "name": 1})
    
    # Return user profile data
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "role": user.get("role"),
        "company_id": user.get("company_id"),
        "company_name": company.get("name") if company else "Unknown",
        "created_at": user.get("created_at")
    }

@api_router.put("/company/profile")
async def update_company_profile(
    updates: dict,
    user: dict = Depends(get_current_company_user)
):
    """Update user profile"""
    # Allow updating user's own profile fields
    user_fields = ["name", "phone"]
    password_fields = ["current_password", "new_password"]
    
    # Handle password change
    if updates.get("current_password") and updates.get("new_password"):
        # Verify current password
        stored_user = await db.company_users.find_one({"id": user["id"]})
        if not stored_user or not verify_password(
            updates["current_password"],
            stored_user["password_hash"]
        ):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password
        new_hash = get_password_hash(updates["new_password"])
        await db.company_users.update_one(
            {"id": user["id"]},
            {"$set": {"password_hash": new_hash, "updated_at": get_ist_isoformat()}}
        )
        return {"message": "Password changed successfully"}
    
    # Handle profile update
    update_data = {k: v for k, v in updates.items() if k in user_fields and v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.company_users.update_one(
        {"id": user["id"]},
        {"$set": update_data}
    )
    
    return {"message": "Profile updated successfully"}

# --- Company Deployments/Users (Read-Only) ---

@api_router.get("/company/deployments")
async def list_company_deployments(user: dict = Depends(get_current_company_user)):
    """List deployments for the company"""
    deployments = await db.deployments.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("deployment_date", -1).to_list(100)
    
    for dep in deployments:
        site = await db.sites.find_one({"id": dep.get("site_id")}, {"_id": 0, "name": 1})
        dep["site_name"] = site.get("name") if site else None
        dep["items_count"] = len(dep.get("items", []))
    
    return deployments

@api_router.get("/company/users")
async def list_company_users_contacts(user: dict = Depends(get_current_company_user)):
    """List users/contacts for the company"""
    users = await db.users.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(500)
    
    return users

@api_router.get("/company/sites")
async def list_company_sites(user: dict = Depends(get_current_company_user)):
    """List sites for the company"""
    sites = await db.sites.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    return sites

# --- Admin: Company User Management ---

@api_router.get("/admin/company-users")
async def list_company_users(
    company_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List company portal users (admin only)"""
    query = {"is_deleted": {"$ne": True}}
    if company_id:
        query["company_id"] = company_id
    
    users = await db.company_users.find(query, {"_id": 0, "password_hash": 0}).to_list(500)
    
    # Add company names
    for u in users:
        company = await db.companies.find_one({"id": u["company_id"]}, {"_id": 0, "name": 1})
        u["company_name"] = company.get("name") if company else None
    
    return users

@api_router.post("/admin/company-users")
async def create_company_user(data: CompanyUserCreate, admin: dict = Depends(get_current_admin)):
    """Create company portal user (admin only)"""
    # Check if company exists
    company = await db.companies.find_one({"id": data.company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if email already exists
    existing = await db.company_users.find_one({"email": data.email.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = CompanyUser(
        company_id=data.company_id,
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        name=data.name,
        phone=data.phone,
        role=data.role,
        created_by=admin.get("email")
    )
    
    await db.company_users.insert_one(user.model_dump())
    
    return {"message": "Company user created", "id": user.id}

@api_router.put("/admin/company-users/{user_id}")
async def update_company_user(user_id: str, updates: CompanyUserUpdate, admin: dict = Depends(get_current_admin)):
    """Update company portal user (admin only)"""
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = await db.company_users.update_one({"id": user_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated"}

@api_router.post("/admin/company-users/{user_id}/reset-password")
async def reset_company_user_password(user_id: str, new_password: str, admin: dict = Depends(get_current_admin)):
    """Reset company user password (admin only)"""
    result = await db.company_users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": get_password_hash(new_password)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset successfully"}

@api_router.delete("/admin/company-users/{user_id}")
async def delete_company_user(user_id: str, admin: dict = Depends(get_current_admin)):
    """Delete company portal user (admin only)"""
    result = await db.company_users.update_one({"id": user_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted"}

# ==================== OFFICE SUPPLIES ADMIN ENDPOINTS ====================

@api_router.get("/admin/supply-categories")
async def list_supply_categories(admin: dict = Depends(get_current_admin)):
    """List all supply categories"""
    categories = await db.supply_categories.find(
        {"is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("sort_order", 1).to_list(100)
    return categories

@api_router.post("/admin/supply-categories")
async def create_supply_category(data: SupplyCategoryCreate, admin: dict = Depends(get_current_admin)):
    """Create a new supply category"""
    category = SupplyCategory(**data.model_dump())
    await db.supply_categories.insert_one(category.model_dump())
    return category.model_dump()

@api_router.put("/admin/supply-categories/{category_id}")
async def update_supply_category(category_id: str, data: SupplyCategoryUpdate, admin: dict = Depends(get_current_admin)):
    """Update a supply category"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.supply_categories.update_one(
        {"id": category_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updated = await db.supply_categories.find_one({"id": category_id}, {"_id": 0})
    return updated

@api_router.delete("/admin/supply-categories/{category_id}")
async def delete_supply_category(category_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a supply category"""
    result = await db.supply_categories.update_one(
        {"id": category_id},
        {"$set": {"is_deleted": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}

@api_router.get("/admin/supply-products")
async def list_supply_products(category_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """List all supply products, optionally filtered by category"""
    query = {"is_deleted": {"$ne": True}}
    if category_id:
        query["category_id"] = category_id
    
    products = await db.supply_products.find(query, {"_id": 0}).to_list(500)
    
    # Add category name to each product
    categories = {c["id"]: c["name"] for c in await db.supply_categories.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(100)}
    for product in products:
        product["category_name"] = categories.get(product["category_id"], "Unknown")
    
    return products

@api_router.post("/admin/supply-products")
async def create_supply_product(data: SupplyProductCreate, admin: dict = Depends(get_current_admin)):
    """Create a new supply product"""
    # Verify category exists
    category = await db.supply_categories.find_one({"id": data.category_id, "is_deleted": {"$ne": True}})
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    product = SupplyProduct(**data.model_dump())
    await db.supply_products.insert_one(product.model_dump())
    
    result = product.model_dump()
    result["category_name"] = category["name"]
    return result

@api_router.put("/admin/supply-products/{product_id}")
async def update_supply_product(product_id: str, data: SupplyProductUpdate, admin: dict = Depends(get_current_admin)):
    """Update a supply product"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    # If category is being changed, verify it exists
    if "category_id" in update_data:
        category = await db.supply_categories.find_one({"id": update_data["category_id"], "is_deleted": {"$ne": True}})
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    result = await db.supply_products.update_one(
        {"id": product_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    updated = await db.supply_products.find_one({"id": product_id}, {"_id": 0})
    category = await db.supply_categories.find_one({"id": updated["category_id"]}, {"_id": 0})
    updated["category_name"] = category["name"] if category else "Unknown"
    return updated

@api_router.delete("/admin/supply-products/{product_id}")
async def delete_supply_product(product_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a supply product"""
    result = await db.supply_products.update_one(
        {"id": product_id},
        {"$set": {"is_deleted": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

@api_router.get("/admin/supply-orders")
async def list_supply_orders(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all supply orders with optional filters"""
    query = {"is_deleted": {"$ne": True}}
    if status:
        query["status"] = status
    if company_id:
        query["company_id"] = company_id
    
    orders = await db.supply_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return orders

@api_router.get("/admin/supply-orders/{order_id}")
async def get_supply_order(order_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific supply order"""
    order = await db.supply_orders.find_one({"id": order_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@api_router.put("/admin/supply-orders/{order_id}")
async def update_supply_order(order_id: str, data: dict, admin: dict = Depends(get_current_admin)):
    """Update supply order status and admin notes"""
    allowed_fields = ["status", "admin_notes"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid data to update")
    
    # Add processing info
    update_data["processed_by"] = admin.get("name", admin.get("email"))
    update_data["processed_at"] = get_ist_isoformat()
    
    result = await db.supply_orders.update_one(
        {"id": order_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    updated = await db.supply_orders.find_one({"id": order_id}, {"_id": 0})
    return updated

# ==================== OFFICE SUPPLIES COMPANY ENDPOINTS ====================

@api_router.get("/company/supply-catalog")
async def get_supply_catalog(user: dict = Depends(get_current_company_user)):
    """Get supply catalog (categories with their products) for ordering"""
    # Get active categories
    categories = await db.supply_categories.find(
        {"is_deleted": {"$ne": True}, "is_active": True},
        {"_id": 0}
    ).sort("sort_order", 1).to_list(100)
    
    # Get active products
    products = await db.supply_products.find(
        {"is_deleted": {"$ne": True}, "is_active": True},
        {"_id": 0, "internal_notes": 0}  # Exclude internal notes from company view
    ).to_list(500)
    
    # Group products by category
    products_by_category = {}
    for product in products:
        cat_id = product["category_id"]
        if cat_id not in products_by_category:
            products_by_category[cat_id] = []
        products_by_category[cat_id].append(product)
    
    # Combine categories with their products
    catalog = []
    for category in categories:
        category["products"] = products_by_category.get(category["id"], [])
        if category["products"]:  # Only include categories that have products
            catalog.append(category)
    
    return catalog

@api_router.post("/company/supply-orders")
async def create_supply_order(data: dict, user: dict = Depends(get_current_company_user)):
    """Create a new supply order"""
    items = data.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="No items in order")
    
    delivery = data.get("delivery_location", {})
    if not delivery:
        raise HTTPException(status_code=400, detail="Delivery location is required")
    
    # Get company info
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")
    
    # Validate products and build order items
    order_items = []
    for item in items:
        product = await db.supply_products.find_one(
            {"id": item["product_id"], "is_deleted": {"$ne": True}, "is_active": True},
            {"_id": 0}
        )
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item['product_id']} not found or inactive")
        
        category = await db.supply_categories.find_one({"id": product["category_id"]}, {"_id": 0})
        
        order_items.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "category_name": category["name"] if category else "Unknown",
            "quantity": item.get("quantity", 1),
            "unit": product["unit"]
        })
    
    # Process delivery location
    delivery_location = {"type": delivery.get("type", "existing")}
    
    if delivery.get("type") == "existing" and delivery.get("site_id"):
        site = await db.sites.find_one({"id": delivery["site_id"]}, {"_id": 0})
        if site:
            delivery_location.update({
                "site_id": site["id"],
                "site_name": site["name"],
                "address": site.get("address"),
                "city": site.get("city"),
                "pincode": site.get("pincode"),
                "contact_person": site.get("contact_person"),
                "contact_phone": site.get("contact_phone")
            })
    else:
        # New location
        delivery_location.update({
            "type": "new",
            "address": delivery.get("address"),
            "city": delivery.get("city"),
            "pincode": delivery.get("pincode"),
            "contact_person": delivery.get("contact_person"),
            "contact_phone": delivery.get("contact_phone")
        })
    
    # Create order
    order = SupplyOrder(
        company_id=user["company_id"],
        company_name=company.get("name", "Unknown"),
        requested_by=user["id"],
        requested_by_name=user.get("name", "Unknown"),
        requested_by_email=user.get("email", ""),
        requested_by_phone=user.get("phone"),
        delivery_location=delivery_location,
        items=order_items,
        notes=data.get("notes")
    )
    
    await db.supply_orders.insert_one(order.model_dump())
    
    # Build osTicket message
    items_table = """
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>#</th><th>Item</th><th>Category</th><th>Quantity</th><th>Unit</th>
</tr>
"""
    for idx, item in enumerate(order_items, 1):
        items_table += f"""
<tr>
<td>{idx}</td>
<td><strong>{item['product_name']}</strong></td>
<td>{item['category_name']}</td>
<td><strong>{item['quantity']}</strong></td>
<td>{item['unit']}</td>
</tr>
"""
    items_table += "</table>"
    
    # Format delivery address
    delivery_addr = delivery_location.get("address", "")
    if delivery_location.get("city"):
        delivery_addr += f", {delivery_location['city']}"
    if delivery_location.get("pincode"):
        delivery_addr += f" - {delivery_location['pincode']}"
    
    osticket_message = f"""
<h2>OFFICE SUPPLIES ORDER</h2>
<p><strong>Order Number:</strong> {order.order_number}</p>
<p><strong>Order Type:</strong> Office Supplies</p>
<p><strong>Order Date:</strong> {order.created_at.split('T')[0]}</p>
<p><strong>Status:</strong> REQUESTED</p>

<hr>
<h3>ITEMS ORDERED ({len(order_items)} items)</h3>
{items_table}

<hr>
<h3>DELIVERY LOCATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Location Type</strong></td><td>{delivery_location.get('type', 'N/A').upper()}</td></tr>
{f"<tr><td><strong>Site Name</strong></td><td>{delivery_location.get('site_name', 'N/A')}</td></tr>" if delivery_location.get('site_name') else ""}
<tr><td><strong>Address</strong></td><td>{delivery_addr or 'N/A'}</td></tr>
<tr><td><strong>Contact Person</strong></td><td>{delivery_location.get('contact_person', 'N/A')}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{delivery_location.get('contact_phone', 'N/A')}</td></tr>
</table>

<hr>
<h3>COMPANY INFORMATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Company Name</strong></td><td>{company.get('name', 'N/A')}</td></tr>
<tr><td><strong>Company ID</strong></td><td>{company.get('company_code') or company.get('id', 'N/A')}</td></tr>
<tr><td><strong>Contact Email</strong></td><td>{company.get('contact_email', 'N/A')}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{company.get('contact_phone', 'N/A')}</td></tr>
</table>

<hr>
<h3>REQUESTED BY</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Name</strong></td><td>{user.get('name', 'N/A')}</td></tr>
<tr><td><strong>Email</strong></td><td>{user.get('email', 'N/A')}</td></tr>
<tr><td><strong>Phone</strong></td><td>{user.get('phone', 'N/A')}</td></tr>
</table>

{f"<hr><h3>SPECIAL INSTRUCTIONS / NOTES</h3><p>{order.notes}</p>" if order.notes else ""}

<hr>
<p style="color: #666; font-size: 12px;">
<em>This order was submitted from the Warranty & Asset Tracking Portal.<br>
Order Created: {get_ist_isoformat()}</em>
</p>
"""
    
    # Create osTicket
    osticket_result = await create_osticket(
        email=user.get("email", "noreply@warranty-portal.com"),
        name=user.get("name", "Portal User"),
        subject=f"[{order.order_number}] Office Supplies Order - {company.get('name', 'Company')}",
        message=osticket_message,
        phone=user.get("phone", "")
    )
    
    osticket_id = osticket_result.get("ticket_id")
    osticket_error = osticket_result.get("error")
    
    # Update order with osTicket ID
    if osticket_id:
        await db.supply_orders.update_one(
            {"id": order.id},
            {"$set": {"osticket_id": osticket_id}}
        )
    
    return {
        "message": "Order submitted successfully",
        "order_number": order.order_number,
        "id": order.id,
        "items_count": len(order_items),
        "osticket_id": osticket_id,
        "osticket_error": osticket_error
    }

@api_router.get("/company/supply-orders")
async def list_company_supply_orders(user: dict = Depends(get_current_company_user)):
    """List supply orders for the company"""
    orders = await db.supply_orders.find(
        {"company_id": user["company_id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return orders

# Include the router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Ensure uploads directory exists
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    # Seed default supply categories and products if none exist
    existing_categories = await db.supply_categories.count_documents({})
    if existing_categories == 0:
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
