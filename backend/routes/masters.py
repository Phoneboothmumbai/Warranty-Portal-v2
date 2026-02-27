"""
Master data endpoints - Device types, brands, etc.
Tenant-scoped: All queries filtered by organization_id.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from database import db
from models.common import MasterItem, MasterItemCreate, MasterItemUpdate
from services.auth import get_current_admin
from services.seeding import seed_default_masters
from utils.helpers import get_ist_isoformat

router = APIRouter(tags=["Master Data"])


def _require_org(admin: dict) -> str:
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    return org_id


@router.get("/admin/masters")
async def list_masters(master_type: Optional[str] = None, include_inactive: bool = False, admin: dict = Depends(get_current_admin)):
    org_id = _require_org(admin)
    query = {"organization_id": org_id}
    if master_type:
        query["type"] = master_type
    if not include_inactive:
        query["is_active"] = True
    masters = await db.masters.find(query, {"_id": 0}).sort("sort_order", 1).to_list(1000)
    return masters


@router.post("/admin/masters")
async def create_master(item: MasterItemCreate, admin: dict = Depends(get_current_admin)):
    org_id = _require_org(admin)
    master = MasterItem(
        type=item.type,
        name=item.name,
        code=item.code,
        is_active=item.is_active,
        sort_order=item.sort_order
    )
    master_dict = master.model_dump()
    master_dict["organization_id"] = org_id
    await db.masters.insert_one(master_dict)
    del master_dict["_id"]
    return master_dict


@router.put("/admin/masters/{master_id}")
async def update_master(master_id: str, updates: MasterItemUpdate, admin: dict = Depends(get_current_admin)):
    org_id = _require_org(admin)
    existing = await db.masters.find_one({"id": master_id, "organization_id": org_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Master item not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = get_ist_isoformat()
        await db.masters.update_one({"id": master_id, "organization_id": org_id}, {"$set": update_data})
    
    updated = await db.masters.find_one({"id": master_id, "organization_id": org_id}, {"_id": 0})
    return updated


@router.delete("/admin/masters/{master_id}")
async def disable_master(master_id: str, admin: dict = Depends(get_current_admin)):
    org_id = _require_org(admin)
    existing = await db.masters.find_one({"id": master_id, "organization_id": org_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Master item not found")
    
    await db.masters.update_one({"id": master_id, "organization_id": org_id}, {"$set": {"is_active": False}})
    return {"message": "Master item disabled"}


@router.post("/admin/masters/seed")
async def seed_masters(admin: dict = Depends(get_current_admin)):
    _require_org(admin)
    await seed_default_masters()
    return {"message": "Default master data seeded"}


@router.post("/admin/masters/quick-create")
async def quick_create_master(item: MasterItemCreate, admin: dict = Depends(get_current_admin)):
    org_id = _require_org(admin)
    existing = await db.masters.find_one({"type": item.type, "name": item.name, "organization_id": org_id})
    if existing:
        return {k: v for k, v in existing.items() if k != "_id"}
    
    master = MasterItem(
        type=item.type,
        name=item.name,
        code=item.code or item.name.upper().replace(" ", "_"),
        is_active=True,
        sort_order=item.sort_order or 99
    )
    master_dict = master.model_dump()
    master_dict["organization_id"] = org_id
    await db.masters.insert_one(master_dict)
    result = {k: v for k, v in master_dict.items() if k != "_id"}
    result["label"] = result["name"]
    return result
