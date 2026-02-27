"""
Item Master Models
==================
Categories, Products (with pricing/GST), and Product Bundles.
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from utils.helpers import get_ist_isoformat


# ── Category ──────────────────────────────────────────────

class ItemCategory(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    name: str
    description: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    sort_order: int = 0
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class ItemCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    sort_order: int = 0


class ItemCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


# ── Product ───────────────────────────────────────────────

GST_SLABS = [0, 5, 12, 18, 28]

class ItemProduct(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    category_id: str

    name: str
    sku: Optional[str] = None
    part_number: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None

    unit_price: float = 0
    gst_slab: int = 18          # 0, 5, 12, 18, 28
    hsn_code: Optional[str] = None
    unit_of_measure: str = "unit"

    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    created_by: Optional[str] = None


class ItemProductCreate(BaseModel):
    category_id: str
    name: str
    sku: Optional[str] = None
    part_number: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    unit_price: float = 0
    gst_slab: int = 18
    hsn_code: Optional[str] = None
    unit_of_measure: str = "unit"


class ItemProductUpdate(BaseModel):
    category_id: Optional[str] = None
    name: Optional[str] = None
    sku: Optional[str] = None
    part_number: Optional[str] = None
    brand: Optional[str] = None
    manufacturer: Optional[str] = None
    description: Optional[str] = None
    unit_price: Optional[float] = None
    gst_slab: Optional[int] = None
    hsn_code: Optional[str] = None
    unit_of_measure: Optional[str] = None
    is_active: Optional[bool] = None


# ── Bundle ────────────────────────────────────────────────

class ItemBundle(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    organization_id: str
    source_product_id: str              # "When this product is picked…"
    recommended_product_ids: List[str] = Field(default_factory=list)  # "…suggest these"
    description: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)


class ItemBundleCreate(BaseModel):
    source_product_id: str
    recommended_product_ids: List[str]
    description: Optional[str] = None


class ItemBundleUpdate(BaseModel):
    recommended_product_ids: Optional[List[str]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
