"""
AMC Onboarding Models - Multi-step wizard for comprehensive AMC setup
"""
import uuid
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
from utils.helpers import get_ist_isoformat


# ==================== ENBOARDING STATUS ====================

ONBOARDING_STATUSES = [
    "draft",           # Company is still filling
    "submitted",       # Company submitted, pending admin review
    "changes_requested", # Admin requested changes
    "approved",        # Admin approved, ready to convert to AMC
    "converted"        # Converted to active AMC contract
]


# ==================== STEP 1: Company & Contract Details ====================

class CompanyContractDetails(BaseModel):
    """Step 1: Company identity, billing, and legal clarity"""
    company_name_legal: Optional[str] = None
    brand_trade_name: Optional[str] = None
    registered_address: Optional[str] = None
    office_addresses: List[dict] = Field(default_factory=list)  # [{name, address, city, pincode}]
    gst_number: Optional[str] = None
    billing_address: Optional[str] = None
    po_amc_reference: Optional[str] = None
    amc_start_date: Optional[str] = None
    amc_end_date: Optional[str] = None
    contracted_user_count: Optional[int] = None
    contracted_device_count: Optional[int] = None
    amc_type: Optional[str] = None  # per_user, per_device, hybrid
    
    # Contacts
    primary_spoc: Optional[dict] = None  # {name, email, mobile}
    escalation_contact: Optional[dict] = None  # {name, email, mobile}
    billing_contact: Optional[dict] = None  # {name, email, mobile}


# ==================== STEP 2: Office Environment ====================

class OfficeEnvironment(BaseModel):
    """Step 2: Office environment snapshot"""
    office_type: Optional[str] = None  # corporate, coworking, factory, retail
    working_days: List[str] = Field(default_factory=list)  # ["monday", "tuesday", ...]
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    total_employees: Optional[int] = None
    it_usage_nature: Optional[str] = None  # basic, business_apps, heavy


# ==================== STEP 3: Device Categories ====================

class DeviceCategories(BaseModel):
    """Step 3: Device category selection"""
    has_desktops: bool = False
    has_laptops: bool = False
    has_apple_devices: bool = False
    has_servers: bool = False
    has_network_devices: bool = False
    has_printers: bool = False
    has_cctv: bool = False
    has_wifi_aps: bool = False
    has_ups: bool = False
    other_devices: Optional[str] = None


# ==================== STEP 4: Device Inventory ====================

class DeviceInventoryItem(BaseModel):
    """Individual device in inventory"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_type: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    configuration: Optional[str] = None  # RAM, Storage, CPU
    os_version: Optional[str] = None
    purchase_date: Optional[str] = None
    warranty_status: Optional[str] = None  # under_oem, extended, expired
    condition: Optional[str] = None  # working, intermittent, faulty
    assigned_user: Optional[str] = None
    department: Optional[str] = None
    physical_location: Optional[str] = None


class DeviceInventory(BaseModel):
    """Step 4: Device inventory collection"""
    devices: List[dict] = Field(default_factory=list)  # List of DeviceInventoryItem dicts


# ==================== STEP 5: Server & Network Infrastructure ====================

class NetworkInfrastructure(BaseModel):
    """Step 5: Server, Network & Critical Infra"""
    # Network
    internet_providers: List[str] = Field(default_factory=list)
    bandwidth: Optional[str] = None
    has_static_ip: Optional[bool] = None
    router_firewall_brand: Optional[str] = None
    router_firewall_model: Optional[str] = None
    switch_count: Optional[int] = None
    vlans: Optional[str] = None
    wifi_controller: Optional[str] = None
    
    # Servers
    has_servers: bool = False
    servers: List[dict] = Field(default_factory=list)  # [{type, os, roles, backup_status, last_backup}]
    
    # Backup acknowledgment
    backup_responsibility_acknowledged: bool = False


# ==================== STEP 6: Software & Access ====================

class SoftwareAccess(BaseModel):
    """Step 6: Software & Access Information"""
    email_platform: Optional[str] = None  # google, microsoft, other
    admin_access_available: Optional[bool] = None
    domain_names: List[str] = Field(default_factory=list)
    licenses: List[dict] = Field(default_factory=list)  # [{name, type, count}]
    has_vpn: Optional[bool] = None
    has_password_manager: Optional[bool] = None
    additional_software: Optional[str] = None


# ==================== STEP 7: Vendor Handover ====================

class VendorHandover(BaseModel):
    """Step 7: Existing IT Vendor Handover"""
    previous_vendor_name: Optional[str] = None
    previous_vendor_contact: Optional[str] = None
    
    # Handover checklist
    has_network_diagram: Optional[bool] = None
    has_ip_details: Optional[bool] = None
    has_server_credentials: Optional[bool] = None
    has_firewall_access: Optional[bool] = None
    has_isp_details: Optional[bool] = None
    has_asset_list: Optional[bool] = None
    has_open_issues_list: Optional[bool] = None
    
    # Acknowledgment
    missing_info_acknowledged: bool = False
    handover_notes: Optional[str] = None


# ==================== STEP 8: Scope Confirmation ====================

class ScopeConfirmation(BaseModel):
    """Step 8: AMC Scope Confirmation & Guardrails"""
    devices_limited_to_listed: bool = False
    new_devices_chargeable: bool = False
    installations_chargeable: bool = False
    unsupported_devices_excluded: bool = False
    onsite_waiting_billable: bool = False
    reopened_tickets_new: bool = False
    information_accuracy_confirmed: bool = False
    additional_terms: Optional[str] = None


# ==================== MAIN ONBOARDING MODEL ====================

class AMCOnboarding(BaseModel):
    """Main AMC Onboarding document"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    company_name: Optional[str] = None
    
    # Status
    status: str = "draft"  # draft, submitted, changes_requested, approved, converted
    current_step: int = 1  # Track progress (1-9)
    
    # Step data
    step1_company_contract: Optional[dict] = None
    step2_office_environment: Optional[dict] = None
    step3_device_categories: Optional[dict] = None
    step4_device_inventory: Optional[dict] = None
    step5_network_infra: Optional[dict] = None
    step6_software_access: Optional[dict] = None
    step7_vendor_handover: Optional[dict] = None
    step8_scope_confirmation: Optional[dict] = None
    
    # Admin feedback (for changes_requested)
    admin_feedback: Optional[str] = None
    feedback_given_at: Optional[str] = None
    feedback_given_by: Optional[str] = None
    
    # Converted AMC reference
    converted_amc_id: Optional[str] = None
    
    # Audit
    created_by: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    submitted_at: Optional[str] = None
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None


class AMCOnboardingUpdate(BaseModel):
    """Update model for saving draft/step data"""
    current_step: Optional[int] = None
    step1_company_contract: Optional[dict] = None
    step2_office_environment: Optional[dict] = None
    step3_device_categories: Optional[dict] = None
    step4_device_inventory: Optional[dict] = None
    step5_network_infra: Optional[dict] = None
    step6_software_access: Optional[dict] = None
    step7_vendor_handover: Optional[dict] = None
    step8_scope_confirmation: Optional[dict] = None
