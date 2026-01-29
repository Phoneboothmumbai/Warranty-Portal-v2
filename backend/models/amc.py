"""
AMC (Annual Maintenance Contract) related models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
from utils.helpers import get_ist_isoformat


class AMC(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_id: str
    start_date: str
    end_date: str
    notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class AMCCreate(BaseModel):
    device_id: str
    start_date: str
    end_date: str
    notes: Optional[str] = None


class AMCUpdate(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    notes: Optional[str] = None


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
    onsite_visits_per_year: Optional[int] = None
    remote_support_type: str = "unlimited"
    remote_support_count: Optional[int] = None
    preventive_maintenance_frequency: str = "quarterly"


class AMCAssetMapping(BaseModel):
    mapping_type: str = "all_company"
    selected_asset_ids: List[str] = []
    selected_device_types: List[str] = []


class AMCDocument(BaseModel):
    """Document attached to an AMC Contract"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # Display name
    document_type: str = "other"  # sla, nda, amc_contract, quote, invoice, other
    file_url: str  # URL or base64 data
    file_name: str  # Original filename
    file_size: Optional[int] = None  # File size in bytes
    uploaded_at: str = Field(default_factory=get_ist_isoformat)
    uploaded_by: Optional[str] = None
    notes: Optional[str] = None


class AMCContract(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    name: str
    amc_type: str = "comprehensive"
    start_date: str
    end_date: str
    coverage_includes: dict = Field(default_factory=lambda: AMCCoverageIncludes().model_dump())
    exclusions: dict = Field(default_factory=lambda: AMCExclusions().model_dump())
    entitlements: dict = Field(default_factory=lambda: AMCEntitlements().model_dump())
    asset_mapping: dict = Field(default_factory=lambda: AMCAssetMapping().model_dump())
    internal_notes: Optional[str] = None
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


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


class AMCUsageRecord(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amc_contract_id: str
    service_id: Optional[str] = None
    usage_type: str
    usage_date: str
    notes: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)


class AMCDeviceAssignment(BaseModel):
    """Join table for AMC Contract to Device assignments"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    amc_contract_id: str
    device_id: str
    coverage_start: str
    coverage_end: str
    coverage_source: str = "manual"
    status: str = "active"
    notes: Optional[str] = None
    created_at: str = Field(default_factory=get_ist_isoformat)
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
    device_identifiers: List[str]
    coverage_start: str
    coverage_end: str


# ==================== AMC REQUEST MODELS ====================

class AMCPackage(BaseModel):
    """AMC Package/Plan definition with pricing"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Basic", "Standard", "Premium"
    amc_type: str = "comprehensive"  # comprehensive, non_comprehensive, on_call
    description: Optional[str] = None
    base_price_per_device: float = 0  # Default price per device/year
    coverage_includes: dict = Field(default_factory=lambda: AMCCoverageIncludes().model_dump())
    exclusions: dict = Field(default_factory=lambda: AMCExclusions().model_dump())
    entitlements: dict = Field(default_factory=lambda: AMCEntitlements().model_dump())
    duration_months: int = 12  # 12, 24, 36
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class AMCPackageCreate(BaseModel):
    name: str
    amc_type: str = "comprehensive"
    description: Optional[str] = None
    base_price_per_device: float = 0
    coverage_includes: Optional[dict] = None
    exclusions: Optional[dict] = None
    entitlements: Optional[dict] = None
    duration_months: int = 12
    is_active: bool = True


class AMCCompanyPricing(BaseModel):
    """Company-specific pricing for AMC packages"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    package_id: str
    custom_price_per_device: float  # Override price for this company
    discount_percentage: float = 0
    notes: Optional[str] = None
    is_active: bool = True
    created_at: str = Field(default_factory=get_ist_isoformat)


class AMCRequest(BaseModel):
    """AMC Request from company user"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    requested_by_user_id: str
    requested_by_name: str
    
    # Package selection
    package_id: Optional[str] = None
    amc_type: str = "comprehensive"  # comprehensive, non_comprehensive, on_call
    duration_months: int = 12  # 12, 24, 36
    
    # Device selection
    selection_type: str = "specific"  # specific, all, by_category
    selected_device_ids: List[str] = []
    selected_categories: List[str] = []  # If selection_type is by_category
    device_count: int = 0
    
    # Preferences
    preferred_start_date: str
    special_requirements: Optional[str] = None
    budget_range: Optional[str] = None
    
    # Pricing (set by admin)
    quoted_price: Optional[float] = None
    price_per_device: Optional[float] = None
    total_price: Optional[float] = None
    
    # Status workflow
    status: str = "pending_review"  # pending_review, under_review, approved, rejected, changes_requested, cancelled
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    changes_requested_note: Optional[str] = None
    
    # Approval tracking
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    approved_contract_id: Optional[str] = None  # Link to created AMC contract
    
    # Payment tracking
    payment_status: str = "unpaid"  # unpaid, paid, partial
    payment_date: Optional[str] = None
    payment_notes: Optional[str] = None
    
    # Timestamps
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class AMCRequestCreate(BaseModel):
    """Create AMC Request (from company portal)"""
    package_id: Optional[str] = None
    amc_type: str = "comprehensive"
    duration_months: int = 12
    selection_type: str = "specific"
    selected_device_ids: List[str] = []
    selected_categories: List[str] = []
    preferred_start_date: str
    special_requirements: Optional[str] = None
    budget_range: Optional[str] = None


class AMCRequestUpdate(BaseModel):
    """Update AMC Request (by company user for revision)"""
    package_id: Optional[str] = None
    amc_type: Optional[str] = None
    duration_months: Optional[int] = None
    selection_type: Optional[str] = None
    selected_device_ids: Optional[List[str]] = None
    selected_categories: Optional[List[str]] = None
    preferred_start_date: Optional[str] = None
    special_requirements: Optional[str] = None
    budget_range: Optional[str] = None


class AMCRequestAdminUpdate(BaseModel):
    """Admin actions on AMC Request"""
    status: Optional[str] = None
    quoted_price: Optional[float] = None
    price_per_device: Optional[float] = None
    total_price: Optional[float] = None
    admin_notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    changes_requested_note: Optional[str] = None
    payment_status: Optional[str] = None
    payment_date: Optional[str] = None
    payment_notes: Optional[str] = None


class InAppNotification(BaseModel):
    """In-app notification for users"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    user_type: str  # admin, company_user, engineer
    title: str
    message: str
    link: Optional[str] = None  # URL to navigate to
    notification_type: str = "info"  # info, success, warning, error
    related_entity_type: Optional[str] = None  # amc_request, ticket, etc.
    related_entity_id: Optional[str] = None
    is_read: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
