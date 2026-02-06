"""
Item Master API Routes
======================
CRUD operations for parts/items catalog.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin
from models.item_master import ItemMaster, ItemMasterCreate, ItemMasterUpdate
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/items", tags=["Item Master"])


@router.get("")
async def list_items(
    admin: dict = Depends(get_current_admin),
    category: Optional[str] = None,
    brand: Optional[str] = None,
    is_active: Optional[bool] = None,
    is_serialized: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200)
):
    """List all items in catalog"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if category:
        query["category"] = category
    if brand:
        query["brand"] = {"$regex": brand, "$options": "i"}
    if is_active is not None:
        query["is_active"] = is_active
    if is_serialized is not None:
        query["is_serialized"] = is_serialized
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"sku": {"$regex": search, "$options": "i"}},
            {"part_number": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.item_masters.count_documents(query)
    skip = (page - 1) * limit
    
    items = await db.item_masters.find(
        query, {"_id": 0}
    ).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.get("/categories")
async def get_item_categories(admin: dict = Depends(get_current_admin)):
    """Get list of item categories"""
    return {
        "categories": [
            {"value": "part", "label": "Part/Spare"},
            {"value": "consumable", "label": "Consumable"},
            {"value": "accessory", "label": "Accessory"},
            {"value": "spare", "label": "Spare Part"},
            {"value": "tool", "label": "Tool"},
            {"value": "equipment", "label": "Equipment"}
        ]
    }


@router.get("/search")
async def search_items(
    q: str = Query(..., min_length=2),
    admin: dict = Depends(get_current_admin),
    limit: int = Query(default=20, le=50)
):
    """Quick search for items (for autocomplete)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {
        "organization_id": org_id,
        "is_deleted": {"$ne": True},
        "is_active": True,
        "$or": [
            {"name": {"$regex": q, "$options": "i"}},
            {"sku": {"$regex": q, "$options": "i"}},
            {"part_number": {"$regex": q, "$options": "i"}}
        ]
    }
    
    items = await db.item_masters.find(
        query,
        {"_id": 0, "id": 1, "name": 1, "sku": 1, "category": 1, "brand": 1, "unit_price": 1, "cost_price": 1}
    ).limit(limit).to_list(limit)
    
    return {"items": items}


@router.get("/{item_id}")
async def get_item(item_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific item"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    item = await db.item_masters.find_one(
        {"id": item_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get vendor mappings for this item
    vendor_mappings = await db.vendor_item_mappings.find(
        {"item_id": item_id, "organization_id": org_id, "is_deleted": {"$ne": True}, "is_active": True},
        {"_id": 0}
    ).sort("priority", 1).to_list(10)
    
    item["vendor_mappings"] = vendor_mappings
    
    return item


@router.post("")
async def create_item(
    data: ItemMasterCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new item"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check for duplicate SKU if provided
    if data.sku:
        existing = await db.item_masters.find_one({
            "organization_id": org_id,
            "sku": {"$regex": f"^{data.sku}$", "$options": "i"},
            "is_deleted": {"$ne": True}
        })
        if existing:
            raise HTTPException(status_code=400, detail="Item with this SKU already exists")
    
    item = ItemMaster(
        organization_id=org_id,
        created_by=admin.get("id"),
        **data.model_dump(exclude_none=True)
    )
    
    await db.item_masters.insert_one(item.model_dump())
    
    return await db.item_masters.find_one({"id": item.id}, {"_id": 0})


@router.put("/{item_id}")
async def update_item(
    item_id: str,
    data: ItemMasterUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update an item"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.item_masters.find_one({
        "id": item_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.item_masters.update_one(
        {"id": item_id},
        {"$set": update_dict}
    )
    
    return await db.item_masters.find_one({"id": item_id}, {"_id": 0})


@router.delete("/{item_id}")
async def delete_item(item_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete an item"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    result = await db.item_masters.update_one(
        {"id": item_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"success": True, "message": "Item deleted"}


@router.get("/{item_id}/stock")
async def get_item_stock(item_id: str, admin: dict = Depends(get_current_admin)):
    """Get stock levels for an item across all locations"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Get item details
    item = await db.item_masters.find_one(
        {"id": item_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "sku": 1}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Calculate stock from ledger
    pipeline = [
        {"$match": {"organization_id": org_id, "item_id": item_id}},
        {"$group": {
            "_id": "$location_id",
            "total_in": {"$sum": "$qty_in"},
            "total_out": {"$sum": "$qty_out"},
            "location_name": {"$first": "$location_name"}
        }},
        {"$project": {
            "location_id": "$_id",
            "location_name": 1,
            "current_stock": {"$subtract": ["$total_in", "$total_out"]}
        }}
    ]
    
    stock_levels = await db.stock_ledger.aggregate(pipeline).to_list(100)
    
    # Calculate totals
    total_stock = sum(s.get("current_stock", 0) for s in stock_levels)
    
    return {
        "item_id": item_id,
        "item_name": item.get("name"),
        "item_sku": item.get("sku"),
        "total_stock": total_stock,
        "stock_by_location": stock_levels
    }
