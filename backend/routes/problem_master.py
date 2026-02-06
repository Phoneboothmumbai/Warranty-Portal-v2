"""
Problem Master API Routes
=========================
CRUD operations for problem types/categories.
"""
import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from services.auth import get_current_admin
from models.problem_master import (
    ProblemMaster, ProblemMasterCreate, ProblemMasterUpdate, DEFAULT_PROBLEMS
)
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/problems", tags=["Problem Master"])


@router.get("")
async def list_problems(
    admin: dict = Depends(get_current_admin),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500)
):
    """List all problem types"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if category:
        query["category"] = category
    if is_active is not None:
        query["is_active"] = is_active
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"code": {"$regex": search, "$options": "i"}}
        ]
    
    problems = await db.problem_masters.find(
        query, {"_id": 0}
    ).sort("sort_order", 1).to_list(limit)
    
    return {"problems": problems, "total": len(problems)}


@router.get("/categories")
async def get_problem_categories(admin: dict = Depends(get_current_admin)):
    """Get list of problem categories"""
    return {
        "categories": [
            {"value": "hardware", "label": "Hardware"},
            {"value": "software", "label": "Software"},
            {"value": "network", "label": "Network"},
            {"value": "peripheral", "label": "Peripheral"},
            {"value": "maintenance", "label": "Maintenance"},
            {"value": "installation", "label": "Installation"},
            {"value": "support", "label": "Support"},
            {"value": "other", "label": "Other"}
        ]
    }


@router.get("/{problem_id}")
async def get_problem(problem_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific problem type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    problem = await db.problem_masters.find_one(
        {"id": problem_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not problem:
        raise HTTPException(status_code=404, detail="Problem type not found")
    
    return problem


@router.post("")
async def create_problem(
    data: ProblemMasterCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new problem type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check for duplicate name
    existing = await db.problem_masters.find_one({
        "organization_id": org_id,
        "name": {"$regex": f"^{data.name}$", "$options": "i"},
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Problem type with this name already exists")
    
    problem = ProblemMaster(
        organization_id=org_id,
        created_by=admin.get("id"),
        **data.model_dump()
    )
    
    await db.problem_masters.insert_one(problem.model_dump())
    
    return await db.problem_masters.find_one({"id": problem.id}, {"_id": 0})


@router.put("/{problem_id}")
async def update_problem(
    problem_id: str,
    data: ProblemMasterUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a problem type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.problem_masters.find_one({
        "id": problem_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if not existing:
        raise HTTPException(status_code=404, detail="Problem type not found")
    
    update_dict = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.problem_masters.update_one(
        {"id": problem_id},
        {"$set": update_dict}
    )
    
    return await db.problem_masters.find_one({"id": problem_id}, {"_id": 0})


@router.delete("/{problem_id}")
async def delete_problem(problem_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a problem type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    result = await db.problem_masters.update_one(
        {"id": problem_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Problem type not found")
    
    return {"success": True, "message": "Problem type deleted"}


@router.post("/seed")
async def seed_default_problems(admin: dict = Depends(get_current_admin)):
    """Seed default problem types for the organization"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check if already seeded
    existing_count = await db.problem_masters.count_documents({
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if existing_count > 0:
        return {"success": False, "message": f"Problems already exist ({existing_count}). Skipping seed."}
    
    # Seed default problems
    created = 0
    for idx, prob_data in enumerate(DEFAULT_PROBLEMS):
        problem = ProblemMaster(
            organization_id=org_id,
            sort_order=idx * 10,
            created_by=admin.get("id"),
            **prob_data
        )
        await db.problem_masters.insert_one(problem.model_dump())
        created += 1
    
    return {"success": True, "message": f"Created {created} default problem types"}
