"""
Ticket Types Routes
===================
API endpoints for managing ticket types and their workflows.
"""
import uuid
import re
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List
from models.ticket_types import (
    TicketType, TicketTypeCreate, TicketTypeUpdate,
    WorkflowStatus, CustomField, get_default_ticket_types
)
from routes.service_tickets_new import get_current_admin
from utils.helpers import get_ist_isoformat

router = APIRouter()

# Database will be injected
_db = None

def init_db(database):
    global _db
    _db = database


# ==================== TICKET TYPES CRUD ====================

@router.get("/ticket-types")
async def list_ticket_types(
    category: Optional[str] = None,
    include_inactive: bool = False,
    admin: dict = Depends(get_current_admin)
):
    """List all ticket types for the organization"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if not include_inactive:
        query["is_active"] = True
    
    if category:
        query["category"] = category
    
    ticket_types = await _db.ticket_types.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    
    # Add ticket count for each type
    for tt in ticket_types:
        tt["ticket_count"] = await _db.service_tickets_new.count_documents({
            "organization_id": org_id,
            "ticket_type_id": tt["id"],
            "is_deleted": {"$ne": True}
        })
    
    return ticket_types


@router.get("/ticket-types/{type_id}")
async def get_ticket_type(
    type_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get a single ticket type with full details"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket_type = await _db.ticket_types.find_one(
        {"id": type_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    
    # Add ticket count
    ticket_type["ticket_count"] = await _db.service_tickets_new.count_documents({
        "organization_id": org_id,
        "ticket_type_id": type_id,
        "is_deleted": {"$ne": True}
    })
    
    return ticket_type


@router.get("/ticket-types/by-slug/{slug}")
async def get_ticket_type_by_slug(
    slug: str,
    admin: dict = Depends(get_current_admin)
):
    """Get a ticket type by slug"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket_type = await _db.ticket_types.find_one(
        {"slug": slug, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    
    return ticket_type


@router.post("/ticket-types")
async def create_ticket_type(
    data: TicketTypeCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new ticket type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Generate slug if not provided
    slug = data.slug or re.sub(r'[^a-z0-9]+', '-', data.name.lower()).strip('-')
    
    # Check if slug exists
    existing = await _db.ticket_types.find_one({
        "slug": slug,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Ticket type with this slug already exists")
    
    # Create default workflow statuses
    default_statuses = [
        WorkflowStatus(name="New", slug="new", color="#6B7280", order=0, is_initial=True, can_transition_to=["in_progress", "closed"]).model_dump(),
        WorkflowStatus(name="In Progress", slug="in_progress", color="#3B82F6", order=1, can_transition_to=["resolved", "closed"]).model_dump(),
        WorkflowStatus(name="Resolved", slug="resolved", color="#22C55E", order=2, can_transition_to=["closed"]).model_dump(),
        WorkflowStatus(name="Closed", slug="closed", color="#10B981", order=3, is_terminal=True, is_success=True).model_dump()
    ]
    
    ticket_type = TicketType(
        organization_id=org_id,
        name=data.name,
        slug=slug,
        description=data.description,
        icon=data.icon,
        color=data.color,
        category=data.category,
        default_priority=data.default_priority,
        requires_device=data.requires_device,
        requires_company=data.requires_company,
        requires_contact=data.requires_contact,
        workflow_statuses=default_statuses,
        created_by_id=admin.get("id")
    )
    
    await _db.ticket_types.insert_one(ticket_type.model_dump())
    
    return ticket_type.model_dump()


@router.put("/ticket-types/{type_id}")
async def update_ticket_type(
    type_id: str,
    data: TicketTypeUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a ticket type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket_type = await _db.ticket_types.find_one({
        "id": type_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    
    # Prepare update data
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    update_data["updated_by_id"] = admin.get("id")
    
    await _db.ticket_types.update_one(
        {"id": type_id},
        {"$set": update_data}
    )
    
    return await _db.ticket_types.find_one({"id": type_id}, {"_id": 0})


@router.delete("/ticket-types/{type_id}")
async def delete_ticket_type(
    type_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Soft delete a ticket type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket_type = await _db.ticket_types.find_one({
        "id": type_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    
    if ticket_type.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot delete system ticket type")
    
    # Check if tickets exist with this type
    ticket_count = await _db.service_tickets_new.count_documents({
        "organization_id": org_id,
        "ticket_type_id": type_id,
        "is_deleted": {"$ne": True}
    })
    
    if ticket_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete ticket type. {ticket_count} tickets are using it. Deactivate instead."
        )
    
    await _db.ticket_types.update_one(
        {"id": type_id},
        {"$set": {
            "is_deleted": True,
            "deleted_at": get_ist_isoformat(),
            "deleted_by_id": admin.get("id")
        }}
    )
    
    return {"message": "Ticket type deleted"}


# ==================== WORKFLOW STATUS MANAGEMENT ====================

@router.put("/ticket-types/{type_id}/workflow")
async def update_workflow_statuses(
    type_id: str,
    statuses: List[dict],
    admin: dict = Depends(get_current_admin)
):
    """Update the workflow statuses for a ticket type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket_type = await _db.ticket_types.find_one({
        "id": type_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    
    # Validate statuses
    has_initial = any(s.get("is_initial") for s in statuses)
    has_terminal = any(s.get("is_terminal") for s in statuses)
    
    if not has_initial:
        raise HTTPException(status_code=400, detail="Workflow must have at least one initial status")
    if not has_terminal:
        raise HTTPException(status_code=400, detail="Workflow must have at least one terminal status")
    
    # Ensure each status has an ID
    for status in statuses:
        if not status.get("id"):
            status["id"] = str(uuid.uuid4())
    
    await _db.ticket_types.update_one(
        {"id": type_id},
        {"$set": {
            "workflow_statuses": statuses,
            "updated_at": get_ist_isoformat(),
            "updated_by_id": admin.get("id")
        }}
    )
    
    return await _db.ticket_types.find_one({"id": type_id}, {"_id": 0})


@router.post("/ticket-types/{type_id}/workflow/status")
async def add_workflow_status(
    type_id: str,
    status: dict,
    admin: dict = Depends(get_current_admin)
):
    """Add a new status to a ticket type's workflow"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket_type = await _db.ticket_types.find_one({
        "id": type_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    
    # Check for duplicate slug
    existing_slugs = [s.get("slug") for s in ticket_type.get("workflow_statuses", [])]
    if status.get("slug") in existing_slugs:
        raise HTTPException(status_code=400, detail="Status slug already exists")
    
    # Add ID and order
    status["id"] = str(uuid.uuid4())
    status["order"] = len(ticket_type.get("workflow_statuses", []))
    
    await _db.ticket_types.update_one(
        {"id": type_id},
        {
            "$push": {"workflow_statuses": status},
            "$set": {"updated_at": get_ist_isoformat(), "updated_by_id": admin.get("id")}
        }
    )
    
    return await _db.ticket_types.find_one({"id": type_id}, {"_id": 0})


# ==================== CUSTOM FIELDS MANAGEMENT ====================

@router.put("/ticket-types/{type_id}/fields")
async def update_custom_fields(
    type_id: str,
    fields: List[dict],
    admin: dict = Depends(get_current_admin)
):
    """Update custom fields for a ticket type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket_type = await _db.ticket_types.find_one({
        "id": type_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    
    # Ensure each field has an ID
    for field in fields:
        if not field.get("id"):
            field["id"] = str(uuid.uuid4())
    
    await _db.ticket_types.update_one(
        {"id": type_id},
        {"$set": {
            "custom_fields": fields,
            "updated_at": get_ist_isoformat(),
            "updated_by_id": admin.get("id")
        }}
    )
    
    return await _db.ticket_types.find_one({"id": type_id}, {"_id": 0})


@router.post("/ticket-types/{type_id}/fields")
async def add_custom_field(
    type_id: str,
    field: dict,
    admin: dict = Depends(get_current_admin)
):
    """Add a custom field to a ticket type"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket_type = await _db.ticket_types.find_one({
        "id": type_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    if not ticket_type:
        raise HTTPException(status_code=404, detail="Ticket type not found")
    
    # Check for duplicate slug
    existing_slugs = [f.get("slug") for f in ticket_type.get("custom_fields", [])]
    if field.get("slug") in existing_slugs:
        raise HTTPException(status_code=400, detail="Field slug already exists")
    
    # Add ID and order
    field["id"] = str(uuid.uuid4())
    field["order"] = len(ticket_type.get("custom_fields", []))
    
    await _db.ticket_types.update_one(
        {"id": type_id},
        {
            "$push": {"custom_fields": field},
            "$set": {"updated_at": get_ist_isoformat(), "updated_by_id": admin.get("id")}
        }
    )
    
    return await _db.ticket_types.find_one({"id": type_id}, {"_id": 0})


# ==================== SEED DEFAULT TYPES ====================

@router.post("/ticket-types/seed")
async def seed_default_ticket_types(
    admin: dict = Depends(get_current_admin)
):
    """Seed all default ticket types for the organization"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check if already seeded
    existing_count = await _db.ticket_types.count_documents({
        "organization_id": org_id,
        "is_system": True,
        "is_deleted": {"$ne": True}
    })
    
    if existing_count > 0:
        return {
            "message": f"Ticket types already seeded ({existing_count} system types found)",
            "seeded": 0
        }
    
    # Get default types
    default_types = get_default_ticket_types(org_id)
    
    # Insert all
    for tt in default_types:
        tt["created_by_id"] = admin.get("id")
        await _db.ticket_types.insert_one(tt)
    
    return {
        "message": f"Successfully seeded {len(default_types)} ticket types",
        "seeded": len(default_types),
        "types": [{"name": t["name"], "slug": t["slug"], "category": t["category"]} for t in default_types]
    }


# ==================== PUBLIC ENDPOINT FOR TICKET CREATION ====================

@router.get("/public/ticket-types")
async def get_public_ticket_types(
    organization_id: str
):
    """
    Get active ticket types for public ticket submission (no auth required).
    Only returns types that are enabled for customer portal.
    """
    ticket_types = await _db.ticket_types.find(
        {
            "organization_id": organization_id,
            "is_active": True,
            "enable_customer_portal": True,
            "is_deleted": {"$ne": True}
        },
        {
            "_id": 0,
            "id": 1,
            "name": 1,
            "slug": 1,
            "description": 1,
            "icon": 1,
            "color": 1,
            "category": 1,
            "custom_fields": 1,
            "requires_device": 1,
            "requires_company": 1,
            "requires_contact": 1
        }
    ).sort("name", 1).to_list(50)
    
    return ticket_types


# ==================== CATEGORIES ====================

@router.get("/ticket-type-categories")
async def get_ticket_type_categories(
    admin: dict = Depends(get_current_admin)
):
    """Get all available ticket type categories"""
    return [
        {"slug": "support", "name": "Support", "icon": "headphones", "color": "#EF4444"},
        {"slug": "sales", "name": "Sales", "icon": "trending-up", "color": "#10B981"},
        {"slug": "operations", "name": "Operations", "icon": "settings", "color": "#F59E0B"},
        {"slug": "finance", "name": "Finance", "icon": "dollar-sign", "color": "#8B5CF6"},
        {"slug": "hr", "name": "HR", "icon": "users", "color": "#EC4899"},
        {"slug": "general", "name": "General", "icon": "inbox", "color": "#3B82F6"}
    ]
