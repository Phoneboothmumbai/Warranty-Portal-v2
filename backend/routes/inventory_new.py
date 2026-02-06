"""
Inventory API Routes
====================
Inventory Location and Stock management.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin
from models.inventory import (
    InventoryLocation, InventoryLocationCreate, InventoryLocationUpdate,
    StockLedger, StockLedgerCreate, StockTransferRequest, StockAdjustmentRequest,
    LocationType, StockTransactionType
)
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/inventory", tags=["Inventory"])


# ==================== LOCATIONS ====================

@router.get("/locations")
async def list_locations(
    admin: dict = Depends(get_current_admin),
    location_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """List all inventory locations"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if location_type:
        query["location_type"] = location_type
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    locations = await db.inventory_locations.find(
        query, {"_id": 0}
    ).sort("name", 1).to_list(limit)
    
    return {"locations": locations, "total": len(locations)}


@router.get("/locations/types")
async def get_location_types(admin: dict = Depends(get_current_admin)):
    """Get list of location types"""
    return {
        "types": [
            {"value": "warehouse", "label": "Warehouse/Godown"},
            {"value": "van", "label": "Technician Van"},
            {"value": "office", "label": "Office"},
            {"value": "site", "label": "Customer Site"},
            {"value": "repair", "label": "Repair Center"},
            {"value": "quarantine", "label": "Quarantine"},
            {"value": "transit", "label": "In Transit"}
        ]
    }


@router.get("/locations/{location_id}")
async def get_location(location_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific location"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    location = await db.inventory_locations.find_one(
        {"id": location_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return location


@router.post("/locations")
async def create_location(
    data: InventoryLocationCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new inventory location"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check for duplicate name
    existing = await db.inventory_locations.find_one({
        "organization_id": org_id,
        "name": {"$regex": f"^{data.name}$", "$options": "i"},
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Location with this name already exists")
    
    # Get assigned user name if provided
    assigned_user_name = None
    if data.assigned_user_id:
        user = await db.staff_users.find_one(
            {"id": data.assigned_user_id, "organization_id": org_id},
            {"name": 1}
        ) or await db.organization_members.find_one(
            {"id": data.assigned_user_id},
            {"name": 1}
        )
        assigned_user_name = user.get("name") if user else None
    
    location = InventoryLocation(
        organization_id=org_id,
        assigned_user_name=assigned_user_name,
        created_by=admin.get("id"),
        **data.model_dump()
    )
    
    await db.inventory_locations.insert_one(location.model_dump())
    
    return await db.inventory_locations.find_one({"id": location.id}, {"_id": 0})


@router.put("/locations/{location_id}")
async def update_location(
    location_id: str,
    data: InventoryLocationUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update an inventory location"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.inventory_locations.find_one({
        "id": location_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    # Get assigned user name if changing
    if "assigned_user_id" in update_dict and update_dict["assigned_user_id"]:
        user = await db.staff_users.find_one(
            {"id": update_dict["assigned_user_id"], "organization_id": org_id},
            {"name": 1}
        ) or await db.organization_members.find_one(
            {"id": update_dict["assigned_user_id"]},
            {"name": 1}
        )
        update_dict["assigned_user_name"] = user.get("name") if user else None
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.inventory_locations.update_one(
        {"id": location_id},
        {"$set": update_dict}
    )
    
    return await db.inventory_locations.find_one({"id": location_id}, {"_id": 0})


@router.delete("/locations/{location_id}")
async def delete_location(location_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a location"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check if location has stock
    stock_count = await db.stock_ledger.count_documents({
        "organization_id": org_id,
        "location_id": location_id
    })
    
    if stock_count > 0:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete location with stock movements. Transfer stock first."
        )
    
    result = await db.inventory_locations.update_one(
        {"id": location_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return {"success": True, "message": "Location deleted"}


# ==================== STOCK LEVELS ====================

@router.get("/stock")
async def get_stock_levels(
    admin: dict = Depends(get_current_admin),
    location_id: Optional[str] = None,
    item_id: Optional[str] = None,
    low_stock_only: bool = False,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200)
):
    """Get current stock levels (calculated from ledger)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Build aggregation pipeline
    match_stage = {"organization_id": org_id}
    if location_id:
        match_stage["location_id"] = location_id
    if item_id:
        match_stage["item_id"] = item_id
    
    pipeline = [
        {"$match": match_stage},
        {"$group": {
            "_id": {"item_id": "$item_id", "location_id": "$location_id"},
            "item_name": {"$first": "$item_name"},
            "location_name": {"$first": "$location_name"},
            "total_in": {"$sum": "$qty_in"},
            "total_out": {"$sum": "$qty_out"}
        }},
        {"$project": {
            "item_id": "$_id.item_id",
            "location_id": "$_id.location_id",
            "item_name": 1,
            "location_name": 1,
            "current_stock": {"$subtract": ["$total_in", "$total_out"]}
        }},
        {"$sort": {"item_name": 1, "location_name": 1}}
    ]
    
    # Get results
    stock_levels = await db.stock_ledger.aggregate(pipeline).to_list(1000)
    
    # Enrich with reorder level info if low_stock_only
    if low_stock_only:
        # Get item reorder levels
        item_ids = list(set(s["item_id"] for s in stock_levels))
        items = await db.item_masters.find(
            {"id": {"$in": item_ids}, "organization_id": org_id},
            {"_id": 0, "id": 1, "reorder_level": 1}
        ).to_list(len(item_ids))
        
        reorder_map = {i["id"]: i.get("reorder_level", 0) for i in items}
        
        # Filter to low stock only
        stock_levels = [
            s for s in stock_levels
            if s["current_stock"] <= reorder_map.get(s["item_id"], 0)
        ]
    
    # Paginate
    total = len(stock_levels)
    start = (page - 1) * limit
    end = start + limit
    paginated = stock_levels[start:end]
    
    return {
        "stock_levels": paginated,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit if total > 0 else 0
    }


@router.get("/stock/location/{location_id}")
async def get_stock_by_location(
    location_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get all stock in a specific location"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Get location details
    location = await db.inventory_locations.find_one(
        {"id": location_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "location_type": 1}
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Calculate stock from ledger
    pipeline = [
        {"$match": {"organization_id": org_id, "location_id": location_id}},
        {"$group": {
            "_id": "$item_id",
            "item_name": {"$first": "$item_name"},
            "total_in": {"$sum": "$qty_in"},
            "total_out": {"$sum": "$qty_out"}
        }},
        {"$project": {
            "item_id": "$_id",
            "item_name": 1,
            "current_stock": {"$subtract": ["$total_in", "$total_out"]}
        }},
        {"$match": {"current_stock": {"$gt": 0}}},
        {"$sort": {"item_name": 1}}
    ]
    
    stock_items = await db.stock_ledger.aggregate(pipeline).to_list(500)
    
    return {
        "location": location,
        "location_id": location_id,
        "items": stock_items,
        "total_items": len(stock_items)
    }


# ==================== STOCK TRANSACTIONS ====================

@router.post("/stock/transfer")
async def transfer_stock(
    data: StockTransferRequest,
    admin: dict = Depends(get_current_admin)
):
    """Transfer stock between locations"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Validate quantity
    if data.quantity <= 0:
        raise HTTPException(status_code=400, detail="Quantity must be positive")
    
    # Get item details
    item = await db.item_masters.find_one(
        {"id": data.item_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "is_serialized": 1}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Validate serial numbers for serialized items
    if item.get("is_serialized") and (not data.serial_numbers or len(data.serial_numbers) != data.quantity):
        raise HTTPException(
            status_code=400,
            detail=f"Serial numbers required for serialized item. Expected {data.quantity} serial numbers."
        )
    
    # Get location details
    from_location = await db.inventory_locations.find_one(
        {"id": data.from_location_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1}
    )
    if not from_location:
        raise HTTPException(status_code=404, detail="Source location not found")
    
    to_location = await db.inventory_locations.find_one(
        {"id": data.to_location_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1}
    )
    if not to_location:
        raise HTTPException(status_code=404, detail="Destination location not found")
    
    # Check available stock at source
    pipeline = [
        {"$match": {"organization_id": org_id, "item_id": data.item_id, "location_id": data.from_location_id}},
        {"$group": {
            "_id": None,
            "total_in": {"$sum": "$qty_in"},
            "total_out": {"$sum": "$qty_out"}
        }},
        {"$project": {
            "current_stock": {"$subtract": ["$total_in", "$total_out"]}
        }}
    ]
    stock_result = await db.stock_ledger.aggregate(pipeline).to_list(1)
    current_stock = stock_result[0]["current_stock"] if stock_result else 0
    
    if current_stock < data.quantity:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient stock. Available: {current_stock}, Requested: {data.quantity}"
        )
    
    # Create transfer entries (OUT from source, IN to destination)
    transfer_id = str(__import__('uuid').uuid4())
    now = get_ist_isoformat()
    
    # OUT entry
    out_entry = StockLedger(
        organization_id=org_id,
        item_id=data.item_id,
        item_name=item["name"],
        location_id=data.from_location_id,
        location_name=from_location["name"],
        qty_out=data.quantity,
        serial_numbers=data.serial_numbers or [],
        transaction_type=StockTransactionType.TRANSFER_OUT.value,
        reference_type="transfer",
        reference_id=transfer_id,
        from_location_id=data.from_location_id,
        to_location_id=data.to_location_id,
        notes=data.notes,
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", ""),
        running_balance=current_stock - data.quantity
    )
    
    # IN entry
    in_entry = StockLedger(
        organization_id=org_id,
        item_id=data.item_id,
        item_name=item["name"],
        location_id=data.to_location_id,
        location_name=to_location["name"],
        qty_in=data.quantity,
        serial_numbers=data.serial_numbers or [],
        transaction_type=StockTransactionType.TRANSFER_IN.value,
        reference_type="transfer",
        reference_id=transfer_id,
        from_location_id=data.from_location_id,
        to_location_id=data.to_location_id,
        notes=data.notes,
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", "")
    )
    
    await db.stock_ledger.insert_many([out_entry.model_dump(), in_entry.model_dump()])
    
    return {
        "success": True,
        "message": f"Transferred {data.quantity} x {item['name']} from {from_location['name']} to {to_location['name']}",
        "transfer_id": transfer_id
    }


@router.post("/stock/adjustment")
async def adjust_stock(
    data: StockAdjustmentRequest,
    admin: dict = Depends(get_current_admin)
):
    """Adjust stock (positive or negative)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    if data.quantity == 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be zero")
    
    # Get item details
    item = await db.item_masters.find_one(
        {"id": data.item_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "is_serialized": 1}
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Get location details
    location = await db.inventory_locations.find_one(
        {"id": data.location_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "allows_negative": 1}
    )
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    # Check current stock for negative adjustments
    if data.quantity < 0:
        pipeline = [
            {"$match": {"organization_id": org_id, "item_id": data.item_id, "location_id": data.location_id}},
            {"$group": {
                "_id": None,
                "total_in": {"$sum": "$qty_in"},
                "total_out": {"$sum": "$qty_out"}
            }},
            {"$project": {
                "current_stock": {"$subtract": ["$total_in", "$total_out"]}
            }}
        ]
        stock_result = await db.stock_ledger.aggregate(pipeline).to_list(1)
        current_stock = stock_result[0]["current_stock"] if stock_result else 0
        
        if not location.get("allows_negative", False) and current_stock + data.quantity < 0:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock. Available: {current_stock}, Adjustment: {data.quantity}"
            )
    
    # Determine transaction type
    if data.quantity > 0:
        transaction_type = StockTransactionType.ADJUSTMENT_IN.value
        qty_in = data.quantity
        qty_out = 0
    else:
        transaction_type = StockTransactionType.ADJUSTMENT_OUT.value
        qty_in = 0
        qty_out = abs(data.quantity)
    
    # Create ledger entry
    entry = StockLedger(
        organization_id=org_id,
        item_id=data.item_id,
        item_name=item["name"],
        location_id=data.location_id,
        location_name=location["name"],
        qty_in=qty_in,
        qty_out=qty_out,
        serial_numbers=data.serial_numbers or [],
        transaction_type=transaction_type,
        reference_type="adjustment",
        notes=f"Reason: {data.reason}. {data.notes or ''}".strip(),
        created_by_id=admin.get("id", ""),
        created_by_name=admin.get("name", "")
    )
    
    await db.stock_ledger.insert_one(entry.model_dump())
    
    return {
        "success": True,
        "message": f"Adjusted stock by {data.quantity} for {item['name']} at {location['name']}",
        "ledger_entry_id": entry.id
    }


@router.get("/ledger")
async def get_stock_ledger(
    admin: dict = Depends(get_current_admin),
    item_id: Optional[str] = None,
    location_id: Optional[str] = None,
    transaction_type: Optional[str] = None,
    reference_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200)
):
    """Get stock ledger entries"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id}
    
    if item_id:
        query["item_id"] = item_id
    if location_id:
        query["location_id"] = location_id
    if transaction_type:
        query["transaction_type"] = transaction_type
    if reference_type:
        query["reference_type"] = reference_type
    if from_date:
        query["created_at"] = {"$gte": from_date}
    if to_date:
        if "created_at" in query:
            query["created_at"]["$lte"] = to_date
        else:
            query["created_at"] = {"$lte": to_date}
    
    total = await db.stock_ledger.count_documents(query)
    skip = (page - 1) * limit
    
    entries = await db.stock_ledger.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    return {
        "entries": entries,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }
