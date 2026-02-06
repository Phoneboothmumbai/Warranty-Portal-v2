"""
Vendor API Routes
=================
Vendor management and vendor-item mappings.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin
from models.vendor import (
    VendorMaster, VendorMasterCreate, VendorMasterUpdate,
    VendorItemMapping, VendorItemMappingCreate, VendorItemMappingUpdate
)
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/vendors", tags=["Vendor Master"])


# ==================== VENDORS ====================

@router.get("")
async def list_vendors(
    admin: dict = Depends(get_current_admin),
    vendor_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200)
):
    """List all vendors"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if vendor_type:
        query["vendor_type"] = vendor_type
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}},
            {"contact_name": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.vendor_masters.count_documents(query)
    skip = (page - 1) * limit
    
    vendors = await db.vendor_masters.find(
        query, {"_id": 0}
    ).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "vendors": vendors,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/search")
async def search_vendors(
    q: str = Query(..., min_length=2),
    admin: dict = Depends(get_current_admin),
    limit: int = Query(default=20, le=50)
):
    """Quick search for vendors (for autocomplete)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {
        "organization_id": org_id,
        "is_deleted": {"$ne": True},
        "is_active": True,
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"code": {"$regex": q, "$options": "i"}}
        ]
    }
    
    vendors = await db.vendor_masters.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "code": 1, "contact_name": 1, "contact_phone": 1}
    ).limit(limit).to_list(limit)
    
    return {"vendors": vendors}


@router.get("/{vendor_id}")
async def get_vendor(vendor_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific vendor"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    vendor = await db.vendor_masters.find_one(
        {"id": vendor_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Get item mappings for this vendor
    item_mappings = await db.vendor_item_mappings.find(
        {"vendor_id": vendor_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("item_name", 1).to_list(100)
    
    vendor["item_mappings"] = item_mappings
    
    return vendor


@router.post("")
async def create_vendor(
    data: VendorMasterCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new vendor"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check for duplicate name
    existing = await db.vendor_masters.find_one({
        "organization_id": org_id,
        "name": {"$regex": f"^{data.name}$", "$options": "i"},
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Vendor with this name already exists")
    
    vendor = VendorMaster(
        organization_id=org_id,
        created_by=admin.get("id"),
        **data.model_dump(exclude_none=True)
    )
    
    await db.vendor_masters.insert_one(vendor.model_dump())
    
    return await db.vendor_masters.find_one({"id": vendor.id}, {"_id": 0})


@router.put("/{vendor_id}")
async def update_vendor(
    vendor_id: str,
    data: VendorMasterUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a vendor"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.vendor_masters.find_one({
        "id": vendor_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.vendor_masters.update_one(
        {"id": vendor_id},
        {"$set": update_dict}
    )
    
    return await db.vendor_masters.find_one({"id": vendor_id}, {"_id": 0})


@router.delete("/{vendor_id}")
async def delete_vendor(vendor_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a vendor"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    result = await db.vendor_masters.update_one(
        {"id": vendor_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    return {"success": True, "message": "Vendor deleted"}


# ==================== VENDOR-ITEM MAPPINGS ====================

@router.post("/{vendor_id}/items")
async def add_vendor_item_mapping(
    vendor_id: str,
    data: VendorItemMappingCreate,
    admin: dict = Depends(get_current_admin)
):
    """Add an item to a vendor's catalog with pricing"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Verify vendor exists
    vendor = await db.vendor_masters.find_one(
        {"id": vendor_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1}
    )
    if not vendor:
        raise HTTPException(status_code=404, detail="Vendor not found")
    
    # Verify item exists
    item = await db.item_masters.find_one(
        {"id": data.item_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Check for existing mapping
    existing = await db.vendor_item_mappings.find_one({
        "organization_id": org_id,
        "vendor_id": vendor_id,
        "item_id": data.item_id,
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="This item is already mapped to this vendor")
    
    # Exclude vendor_id and item_id from data since we're setting them explicitly
    mapping_data = data.model_dump(exclude={"vendor_id", "item_id"})
    mapping = VendorItemMapping(
        organization_id=org_id,
        vendor_id=vendor_id,
        item_id=data.item_id,
        vendor_name=vendor["name"],
        item_name=item["name"],
        **mapping_data
    )
    
    await db.vendor_item_mappings.insert_one(mapping.model_dump())
    
    return await db.vendor_item_mappings.find_one({"id": mapping.id}, {"_id": 0})


@router.put("/{vendor_id}/items/{mapping_id}")
async def update_vendor_item_mapping(
    vendor_id: str,
    mapping_id: str,
    data: VendorItemMappingUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a vendor-item mapping"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.vendor_item_mappings.find_one({
        "id": mapping_id,
        "vendor_id": vendor_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # If price changed, add to price history
    if "unit_price" in update_dict and update_dict["unit_price"] != existing.get("unit_price"):
        price_history_entry = {
            "price": existing.get("unit_price"),
            "date": existing.get("updated_at") or existing.get("created_at"),
            "notes": "Price updated"
        }
        await db.vendor_item_mappings.update_one(
            {"id": mapping_id},
            {"$push": {"price_history": price_history_entry}}
        )
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.vendor_item_mappings.update_one(
        {"id": mapping_id},
        {"$set": update_dict}
    )
    
    return await db.vendor_item_mappings.find_one({"id": mapping_id}, {"_id": 0})


@router.delete("/{vendor_id}/items/{mapping_id}")
async def delete_vendor_item_mapping(
    vendor_id: str,
    mapping_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Delete a vendor-item mapping"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    result = await db.vendor_item_mappings.update_one(
        {"id": mapping_id, "vendor_id": vendor_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Mapping not found")
    
    return {"success": True, "message": "Mapping deleted"}


@router.get("/for-item/{item_id}")
async def get_vendors_for_item(
    item_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get all vendors who supply a specific item"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    mappings = await db.vendor_item_mappings.find(
        {
            "organization_id": org_id,
            "item_id": item_id,
            "is_deleted": {"$ne": True},
            "is_active": True
        },
        {"_id": 0}
    ).sort("priority", 1).to_list(20)
    
    return {"vendors": mappings}
