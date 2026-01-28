"""
Enterprise Ticketing System API Routes
Phase 1: Core Foundation
"""
import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase

from models.ticketing import (
    Department, DepartmentCreate, DepartmentUpdate,
    SLAPolicy, SLAPolicyCreate, SLAPolicyUpdate,
    Ticket, TicketCreate, TicketUpdate,
    TicketThreadEntry, TicketReplyCreate,
    TicketCategory, CustomFieldDefinition,
    TicketingStaffProfile, TicketSLAStatus,
    TICKET_STATUSES, TICKET_PRIORITIES, TICKET_SOURCES,
    THREAD_ENTRY_TYPES, SYSTEM_EVENT_TYPES, STAFF_ROLES
)
from utils.helpers import get_ist_isoformat

router = APIRouter(prefix="/ticketing", tags=["Ticketing"])


# ==================== DEPENDENCY INJECTION ====================
# These will be set when the router is included in the main app

_db: AsyncIOMotorDatabase = None
_get_current_admin = None
_get_current_company_user = None
_log_audit = None


def init_ticketing_router(
    database: AsyncIOMotorDatabase,
    admin_dependency,
    company_user_dependency,
    audit_function
):
    """Initialize the ticketing router with dependencies"""
    global _db, _get_current_admin, _get_current_company_user, _log_audit
    _db = database
    _get_current_admin = admin_dependency
    _get_current_company_user = company_user_dependency
    _log_audit = audit_function


def get_db():
    return _db

def get_admin_dependency():
    return _get_current_admin

def get_company_user_dependency():
    return _get_current_company_user


# ==================== ENUMS ENDPOINT ====================

@router.get("/enums")
async def get_ticketing_enums():
    """Get all enum values for ticketing system"""
    return {
        "statuses": [
            {"value": "open", "label": "Open"},
            {"value": "in_progress", "label": "In Progress"},
            {"value": "waiting_on_customer", "label": "Waiting on Customer"},
            {"value": "waiting_on_third_party", "label": "Waiting on Third-Party"},
            {"value": "on_hold", "label": "On Hold"},
            {"value": "resolved", "label": "Resolved"},
            {"value": "closed", "label": "Closed"}
        ],
        "priorities": [
            {"value": "low", "label": "Low"},
            {"value": "medium", "label": "Medium"},
            {"value": "high", "label": "High"},
            {"value": "critical", "label": "Critical"}
        ],
        "sources": [
            {"value": "portal", "label": "Portal"},
            {"value": "email", "label": "Email"},
            {"value": "phone", "label": "Phone"},
            {"value": "manual", "label": "Manual"},
            {"value": "api", "label": "API"},
            {"value": "whatsapp", "label": "WhatsApp"}
        ],
        "staff_roles": [
            {"value": "technician", "label": "Technician"},
            {"value": "senior_technician", "label": "Senior Technician"},
            {"value": "supervisor", "label": "Supervisor"},
            {"value": "admin", "label": "Admin"}
        ]
    }


# ==================== DEPARTMENTS ====================

@router.get("/admin/departments")
async def list_departments(
    include_inactive: bool = False,
    admin: dict = Depends(get_admin_dependency)
):
    """List all departments (admin only)"""
    db = get_db()
    query = {"is_deleted": {"$ne": True}}
    if not include_inactive:
        query["is_active"] = True
    
    departments = await db.ticketing_departments.find(query, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return departments


@router.post("/admin/departments")
async def create_department(
    data: DepartmentCreate,
    admin: dict = Depends(get_admin_dependency)
):
    """Create a new department"""
    db = get_db()
    dept = Department(
        **data.model_dump(),
        created_by=admin.get("id")
    )
    await db.ticketing_departments.insert_one(dept.model_dump())
    await _log_audit("ticketing_department", dept.id, "create", data.model_dump(), admin)
    return dept.model_dump()


@router.get("/admin/departments/{dept_id}")
async def get_department(
    dept_id: str,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Get department by ID"""
    dept = await db.ticketing_departments.find_one(
        {"id": dept_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.put("/admin/departments/{dept_id}")
async def update_department(
    dept_id: str,
    updates: DepartmentUpdate,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Update a department"""
    dept = await db.ticketing_departments.find_one(
        {"id": dept_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.ticketing_departments.update_one({"id": dept_id}, {"$set": update_data})
    await log_audit("ticketing_department", dept_id, "update", update_data, admin)
    
    return await db.ticketing_departments.find_one({"id": dept_id}, {"_id": 0})


@router.delete("/admin/departments/{dept_id}")
async def delete_department(
    dept_id: str,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Soft delete a department"""
    dept = await db.ticketing_departments.find_one(
        {"id": dept_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Check if any open tickets in this department
    open_tickets = await db.tickets.count_documents({
        "department_id": dept_id,
        "status": {"$nin": ["resolved", "closed"]},
        "is_deleted": {"$ne": True}
    })
    if open_tickets > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete department with {open_tickets} open tickets"
        )
    
    await db.ticketing_departments.update_one(
        {"id": dept_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    await log_audit("ticketing_department", dept_id, "delete", {}, admin)
    return {"message": "Department deleted"}


# ==================== SLA POLICIES ====================

@router.get("/admin/sla-policies")
async def list_sla_policies(
    include_inactive: bool = False,
    admin: dict = Depends(lambda: get_current_admin)
):
    """List all SLA policies"""
    query = {"is_deleted": {"$ne": True}}
    if not include_inactive:
        query["is_active"] = True
    
    policies = await db.ticketing_sla_policies.find(query, {"_id": 0}).to_list(100)
    return policies


@router.post("/admin/sla-policies")
async def create_sla_policy(
    data: SLAPolicyCreate,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Create a new SLA policy"""
    policy = SLAPolicy(
        **data.model_dump(),
        created_by=admin.get("id")
    )
    
    # If this is set as default, unset other defaults
    if data.is_default:
        await db.ticketing_sla_policies.update_many(
            {"is_default": True},
            {"$set": {"is_default": False}}
        )
    
    await db.ticketing_sla_policies.insert_one(policy.model_dump())
    await log_audit("ticketing_sla_policy", policy.id, "create", data.model_dump(), admin)
    return policy.model_dump()


@router.get("/admin/sla-policies/{policy_id}")
async def get_sla_policy(
    policy_id: str,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Get SLA policy by ID"""
    policy = await db.ticketing_sla_policies.find_one(
        {"id": policy_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")
    return policy


@router.put("/admin/sla-policies/{policy_id}")
async def update_sla_policy(
    policy_id: str,
    updates: SLAPolicyUpdate,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Update an SLA policy"""
    policy = await db.ticketing_sla_policies.find_one(
        {"id": policy_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    # Handle default flag
    if update_data.get("is_default"):
        await db.ticketing_sla_policies.update_many(
            {"is_default": True, "id": {"$ne": policy_id}},
            {"$set": {"is_default": False}}
        )
    
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.ticketing_sla_policies.update_one({"id": policy_id}, {"$set": update_data})
    await log_audit("ticketing_sla_policy", policy_id, "update", update_data, admin)
    
    return await db.ticketing_sla_policies.find_one({"id": policy_id}, {"_id": 0})


@router.delete("/admin/sla-policies/{policy_id}")
async def delete_sla_policy(
    policy_id: str,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Soft delete an SLA policy"""
    policy = await db.ticketing_sla_policies.find_one(
        {"id": policy_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")
    
    await db.ticketing_sla_policies.update_one(
        {"id": policy_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    await log_audit("ticketing_sla_policy", policy_id, "delete", {}, admin)
    return {"message": "SLA Policy deleted"}


# ==================== CATEGORIES ====================

@router.get("/admin/categories")
async def list_categories(
    admin: dict = Depends(lambda: get_current_admin)
):
    """List all ticket categories"""
    categories = await db.ticketing_categories.find(
        {"is_deleted": {"$ne": True}}, {"_id": 0}
    ).sort("sort_order", 1).to_list(100)
    return categories


@router.post("/admin/categories")
async def create_category(
    data: dict,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Create a ticket category"""
    category = TicketCategory(
        name=data.get("name"),
        description=data.get("description"),
        parent_id=data.get("parent_id"),
        auto_department_id=data.get("auto_department_id"),
        auto_priority=data.get("auto_priority"),
        sort_order=data.get("sort_order", 0)
    )
    await db.ticketing_categories.insert_one(category.model_dump())
    await log_audit("ticketing_category", category.id, "create", data, admin)
    return category.model_dump()


@router.put("/admin/categories/{category_id}")
async def update_category(
    category_id: str,
    data: dict,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Update a ticket category"""
    category = await db.ticketing_categories.find_one(
        {"id": category_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {k: v for k, v in data.items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.ticketing_categories.update_one({"id": category_id}, {"$set": update_data})
    return await db.ticketing_categories.find_one({"id": category_id}, {"_id": 0})


@router.delete("/admin/categories/{category_id}")
async def delete_category(
    category_id: str,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Soft delete a category"""
    await db.ticketing_categories.update_one(
        {"id": category_id},
        {"$set": {"is_deleted": True}}
    )
    return {"message": "Category deleted"}


# ==================== TICKETS - ADMIN ====================

@router.get("/admin/tickets")
async def list_tickets_admin(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    department_id: Optional[str] = None,
    assigned_to: Optional[str] = None,
    company_id: Optional[str] = None,
    unassigned: bool = False,
    search: Optional[str] = None,
    limit: int = Query(50, le=200),
    skip: int = 0,
    admin: dict = Depends(lambda: get_current_admin)
):
    """List tickets with filters (admin view)"""
    query = {"is_deleted": {"$ne": True}}
    
    if status:
        query["status"] = status
    if priority:
        query["priority"] = priority
    if department_id:
        query["department_id"] = department_id
    if assigned_to:
        query["assigned_to"] = assigned_to
    if company_id:
        query["company_id"] = company_id
    if unassigned:
        query["assigned_to"] = None
    if search:
        query["$or"] = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"subject": {"$regex": search, "$options": "i"}},
            {"requester_name": {"$regex": search, "$options": "i"}},
            {"requester_email": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.tickets.count_documents(query)
    tickets = await db.tickets.find(query, {"_id": 0}).sort(
        [("priority_order", -1), ("created_at", -1)]
    ).skip(skip).limit(limit).to_list(limit)
    
    return {
        "tickets": tickets,
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.post("/admin/tickets")
async def create_ticket_admin(
    data: TicketCreate,
    requester_id: str = Query(..., description="Company user ID of requester"),
    admin: dict = Depends(lambda: get_current_admin)
):
    """Create a ticket on behalf of a customer (admin)"""
    # Get requester info
    requester = await db.company_users.find_one(
        {"id": requester_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not requester:
        raise HTTPException(status_code=404, detail="Requester not found")
    
    # Get department defaults
    sla_policy = None
    if data.department_id:
        dept = await db.ticketing_departments.find_one(
            {"id": data.department_id, "is_deleted": {"$ne": True}}, {"_id": 0}
        )
        if dept and dept.get("default_sla_id"):
            sla_policy = await db.ticketing_sla_policies.find_one(
                {"id": dept["default_sla_id"]}, {"_id": 0}
            )
    
    # If no department SLA, use default
    if not sla_policy:
        sla_policy = await db.ticketing_sla_policies.find_one(
            {"is_default": True, "is_deleted": {"$ne": True}}, {"_id": 0}
        )
    
    # Calculate SLA due times
    sla_status = None
    if sla_policy:
        sla_status = calculate_sla_due_times(sla_policy, data.priority)
    
    # Create ticket
    ticket = Ticket(
        **data.model_dump(),
        company_id=requester.get("company_id"),
        requester_id=requester_id,
        requester_name=requester.get("name", "Unknown"),
        requester_email=requester.get("email", ""),
        requester_phone=requester.get("phone"),
        sla_status=sla_status,
        created_by=admin.get("id"),
        created_by_type="staff"
    )
    
    # Set priority order for sorting
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ticket_dict = ticket.model_dump()
    ticket_dict["priority_order"] = priority_order.get(data.priority, 2)
    
    await db.tickets.insert_one(ticket_dict)
    
    # Create system event in thread
    await create_thread_entry(
        ticket.id,
        "system_event",
        author_id=admin.get("id"),
        author_name=admin.get("name"),
        author_type="admin",
        event_type="ticket_created",
        event_data={"created_by_staff": True}
    )
    
    await log_audit("ticket", ticket.id, "create", data.model_dump(), admin)
    return ticket_dict


@router.get("/admin/tickets/{ticket_id}")
async def get_ticket_admin(
    ticket_id: str,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Get ticket details with thread"""
    ticket = await db.tickets.find_one(
        {"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get thread entries
    thread = await db.ticket_thread.find(
        {"ticket_id": ticket_id, "is_hidden": {"$ne": True}}, {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    # Get department info
    department = None
    if ticket.get("department_id"):
        department = await db.ticketing_departments.find_one(
            {"id": ticket["department_id"]}, {"_id": 0, "name": 1, "id": 1}
        )
    
    return {
        **ticket,
        "thread": thread,
        "department": department
    }


@router.put("/admin/tickets/{ticket_id}")
async def update_ticket_admin(
    ticket_id: str,
    updates: TicketUpdate,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Update ticket (admin)"""
    ticket = await db.tickets.find_one(
        {"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    # Track changes for audit
    changes = []
    
    # Handle status change
    if "status" in update_data and update_data["status"] != ticket.get("status"):
        old_status = ticket.get("status")
        new_status = update_data["status"]
        changes.append(("status", old_status, new_status))
        
        # Handle SLA pause/resume
        sla_status = ticket.get("sla_status") or {}
        if new_status in ["waiting_on_customer", "waiting_on_third_party"]:
            sla_status["is_paused"] = True
            sla_status["paused_at"] = get_ist_isoformat()
        elif old_status in ["waiting_on_customer", "waiting_on_third_party"]:
            # Resume SLA
            if sla_status.get("paused_at"):
                paused_duration = (
                    datetime.now() - datetime.fromisoformat(sla_status["paused_at"].replace("Z", "+00:00"))
                ).total_seconds()
                sla_status["total_paused_seconds"] = sla_status.get("total_paused_seconds", 0) + int(paused_duration)
            sla_status["is_paused"] = False
            sla_status["paused_at"] = None
        
        # Handle resolution
        if new_status == "resolved":
            update_data["resolved_at"] = get_ist_isoformat()
            sla_status["resolved_at"] = get_ist_isoformat()
            sla_status["resolution_met"] = not sla_status.get("resolution_breached", False)
        
        # Handle closure
        if new_status == "closed":
            update_data["closed_at"] = get_ist_isoformat()
        
        # Handle reopen
        if old_status in ["resolved", "closed"] and new_status not in ["resolved", "closed"]:
            update_data["resolved_at"] = None
            update_data["closed_at"] = None
        
        update_data["sla_status"] = sla_status
        
        # Log status change event
        await create_thread_entry(
            ticket_id,
            "system_event",
            author_id=admin.get("id"),
            author_name=admin.get("name"),
            author_type="admin",
            event_type="status_changed",
            event_data={"old": old_status, "new": new_status}
        )
    
    # Handle priority change
    if "priority" in update_data and update_data["priority"] != ticket.get("priority"):
        old_priority = ticket.get("priority")
        new_priority = update_data["priority"]
        changes.append(("priority", old_priority, new_priority))
        
        # Update priority order
        priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
        update_data["priority_order"] = priority_order.get(new_priority, 2)
        
        await create_thread_entry(
            ticket_id,
            "system_event",
            author_id=admin.get("id"),
            author_name=admin.get("name"),
            author_type="admin",
            event_type="priority_changed",
            event_data={"old": old_priority, "new": new_priority}
        )
    
    # Handle assignment change
    if "assigned_to" in update_data and update_data["assigned_to"] != ticket.get("assigned_to"):
        old_assignee = ticket.get("assigned_to")
        new_assignee = update_data["assigned_to"]
        
        # Get assignee name
        assignee_name = None
        if new_assignee:
            assignee = await db.admin_users.find_one({"id": new_assignee}, {"name": 1})
            assignee_name = assignee.get("name") if assignee else None
        
        update_data["assigned_to_name"] = assignee_name
        update_data["assigned_at"] = get_ist_isoformat() if new_assignee else None
        
        event_type = "assigned" if not old_assignee else "reassigned"
        await create_thread_entry(
            ticket_id,
            "system_event",
            author_id=admin.get("id"),
            author_name=admin.get("name"),
            author_type="admin",
            event_type=event_type,
            event_data={
                "old": old_assignee,
                "new": new_assignee,
                "assignee_name": assignee_name
            }
        )
    
    # Handle department change
    if "department_id" in update_data and update_data["department_id"] != ticket.get("department_id"):
        await create_thread_entry(
            ticket_id,
            "system_event",
            author_id=admin.get("id"),
            author_name=admin.get("name"),
            author_type="admin",
            event_type="department_changed",
            event_data={
                "old": ticket.get("department_id"),
                "new": update_data["department_id"]
            }
        )
    
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    await log_audit("ticket", ticket_id, "update", {"changes": changes}, admin)
    
    return await db.tickets.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/admin/tickets/{ticket_id}/reply")
async def reply_to_ticket_admin(
    ticket_id: str,
    reply: TicketReplyCreate,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Add a reply or internal note to a ticket (admin)"""
    ticket = await db.tickets.find_one(
        {"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    entry_type = "internal_note" if reply.is_internal else "technician_reply"
    
    entry = await create_thread_entry(
        ticket_id,
        entry_type,
        author_id=admin.get("id"),
        author_name=admin.get("name"),
        author_type=admin.get("role", "admin"),
        content=reply.content,
        attachments=reply.attachments,
        is_internal=reply.is_internal
    )
    
    # Update ticket counts and timestamps
    update_data = {"updated_at": get_ist_isoformat()}
    if reply.is_internal:
        update_data["internal_note_count"] = ticket.get("internal_note_count", 0) + 1
    else:
        update_data["reply_count"] = ticket.get("reply_count", 0) + 1
        update_data["last_staff_reply_at"] = get_ist_isoformat()
        
        # Check if this is first response (for SLA)
        if not ticket.get("first_response_at"):
            update_data["first_response_at"] = get_ist_isoformat()
            sla_status = ticket.get("sla_status") or {}
            sla_status["first_response_at"] = get_ist_isoformat()
            sla_status["response_met"] = not sla_status.get("response_breached", False)
            update_data["sla_status"] = sla_status
    
    await db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    
    return entry


@router.post("/admin/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assignee_id: str,
    admin: dict = Depends(lambda: get_current_admin)
):
    """Assign or reassign a ticket"""
    ticket = await db.tickets.find_one(
        {"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get assignee
    assignee = await db.admin_users.find_one(
        {"id": assignee_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    old_assignee = ticket.get("assigned_to")
    event_type = "assigned" if not old_assignee else "reassigned"
    
    await db.tickets.update_one(
        {"id": ticket_id},
        {"$set": {
            "assigned_to": assignee_id,
            "assigned_to_name": assignee.get("name"),
            "assigned_at": get_ist_isoformat(),
            "updated_at": get_ist_isoformat()
        }}
    )
    
    await create_thread_entry(
        ticket_id,
        "system_event",
        author_id=admin.get("id"),
        author_name=admin.get("name"),
        author_type="admin",
        event_type=event_type,
        event_data={
            "old": old_assignee,
            "new": assignee_id,
            "assignee_name": assignee.get("name")
        }
    )
    
    return {"message": f"Ticket {event_type}", "assigned_to": assignee.get("name")}


# ==================== TICKETS - CUSTOMER PORTAL ====================

@router.get("/portal/tickets")
async def list_tickets_customer(
    status: Optional[str] = None,
    limit: int = Query(20, le=100),
    user: dict = Depends(lambda: get_current_company_user)
):
    """List tickets for current customer"""
    query = {
        "company_id": user.get("company_id"),
        "requester_id": user.get("id"),
        "is_deleted": {"$ne": True}
    }
    if status:
        query["status"] = status
    
    tickets = await db.tickets.find(
        query,
        {"_id": 0, "internal_note_count": 0}  # Hide internal note count from customer
    ).sort("created_at", -1).limit(limit).to_list(limit)
    
    return tickets


@router.post("/portal/tickets")
async def create_ticket_customer(
    data: TicketCreate,
    user: dict = Depends(lambda: get_current_company_user)
):
    """Create a ticket (customer portal)"""
    # Get department defaults if specified
    sla_policy = None
    if data.department_id:
        dept = await db.ticketing_departments.find_one(
            {"id": data.department_id, "is_deleted": {"$ne": True}, "is_public": True}, 
            {"_id": 0}
        )
        if dept and dept.get("default_sla_id"):
            sla_policy = await db.ticketing_sla_policies.find_one(
                {"id": dept["default_sla_id"]}, {"_id": 0}
            )
    
    # If no department SLA, use default
    if not sla_policy:
        sla_policy = await db.ticketing_sla_policies.find_one(
            {"is_default": True, "is_deleted": {"$ne": True}}, {"_id": 0}
        )
    
    # Calculate SLA due times
    sla_status = None
    if sla_policy:
        sla_status = calculate_sla_due_times(sla_policy, data.priority)
    
    # Create ticket
    ticket = Ticket(
        **data.model_dump(),
        company_id=user.get("company_id"),
        requester_id=user.get("id"),
        requester_name=user.get("name", "Unknown"),
        requester_email=user.get("email", ""),
        requester_phone=user.get("phone"),
        sla_status=sla_status,
        created_by=user.get("id"),
        created_by_type="customer"
    )
    
    # Set priority order
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ticket_dict = ticket.model_dump()
    ticket_dict["priority_order"] = priority_order.get(data.priority, 2)
    
    await db.tickets.insert_one(ticket_dict)
    
    # Create system event
    await create_thread_entry(
        ticket.id,
        "system_event",
        author_id=user.get("id"),
        author_name=user.get("name"),
        author_type="customer",
        event_type="ticket_created",
        event_data={}
    )
    
    return ticket_dict


@router.get("/portal/tickets/{ticket_id}")
async def get_ticket_customer(
    ticket_id: str,
    user: dict = Depends(lambda: get_current_company_user)
):
    """Get ticket details (customer view - no internal notes)"""
    ticket = await db.tickets.find_one(
        {
            "id": ticket_id,
            "company_id": user.get("company_id"),
            "requester_id": user.get("id"),
            "is_deleted": {"$ne": True}
        },
        {"_id": 0, "internal_note_count": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get thread entries (exclude internal notes)
    thread = await db.ticket_thread.find(
        {
            "ticket_id": ticket_id,
            "is_internal": {"$ne": True},
            "is_hidden": {"$ne": True}
        },
        {"_id": 0}
    ).sort("created_at", 1).to_list(500)
    
    return {
        **ticket,
        "thread": thread
    }


@router.post("/portal/tickets/{ticket_id}/reply")
async def reply_to_ticket_customer(
    ticket_id: str,
    reply: TicketReplyCreate,
    user: dict = Depends(lambda: get_current_company_user)
):
    """Add a reply to a ticket (customer)"""
    ticket = await db.tickets.find_one(
        {
            "id": ticket_id,
            "company_id": user.get("company_id"),
            "requester_id": user.get("id"),
            "is_deleted": {"$ne": True}
        },
        {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Customers cannot create internal notes
    entry = await create_thread_entry(
        ticket_id,
        "customer_message",
        author_id=user.get("id"),
        author_name=user.get("name"),
        author_type="customer",
        author_email=user.get("email"),
        content=reply.content,
        attachments=reply.attachments,
        is_internal=False
    )
    
    # Update ticket
    update_data = {
        "updated_at": get_ist_isoformat(),
        "last_customer_reply_at": get_ist_isoformat(),
        "reply_count": ticket.get("reply_count", 0) + 1
    }
    
    # If ticket was waiting on customer, move to open
    if ticket.get("status") == "waiting_on_customer":
        update_data["status"] = "open"
        # Resume SLA
        sla_status = ticket.get("sla_status") or {}
        if sla_status.get("paused_at"):
            paused_duration = (
                datetime.now() - datetime.fromisoformat(sla_status["paused_at"].replace("Z", "+00:00"))
            ).total_seconds()
            sla_status["total_paused_seconds"] = sla_status.get("total_paused_seconds", 0) + int(paused_duration)
        sla_status["is_paused"] = False
        sla_status["paused_at"] = None
        update_data["sla_status"] = sla_status
    
    await db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    
    return entry


# ==================== DASHBOARD & STATS ====================

@router.get("/admin/dashboard")
async def get_ticketing_dashboard(
    admin: dict = Depends(lambda: get_current_admin)
):
    """Get ticketing dashboard stats"""
    # Count by status
    status_counts = {}
    for status in TICKET_STATUSES:
        count = await db.tickets.count_documents({
            "status": status,
            "is_deleted": {"$ne": True}
        })
        status_counts[status] = count
    
    # Count by priority
    priority_counts = {}
    for priority in TICKET_PRIORITIES:
        count = await db.tickets.count_documents({
            "priority": priority,
            "status": {"$nin": ["resolved", "closed"]},
            "is_deleted": {"$ne": True}
        })
        priority_counts[priority] = count
    
    # Unassigned count
    unassigned = await db.tickets.count_documents({
        "assigned_to": None,
        "status": {"$nin": ["resolved", "closed"]},
        "is_deleted": {"$ne": True}
    })
    
    # SLA breached count
    sla_breached = await db.tickets.count_documents({
        "$or": [
            {"sla_status.response_breached": True},
            {"sla_status.resolution_breached": True}
        ],
        "status": {"$nin": ["resolved", "closed"]},
        "is_deleted": {"$ne": True}
    })
    
    # Total open
    total_open = await db.tickets.count_documents({
        "status": {"$nin": ["resolved", "closed"]},
        "is_deleted": {"$ne": True}
    })
    
    return {
        "total_open": total_open,
        "unassigned": unassigned,
        "sla_breached": sla_breached,
        "by_status": status_counts,
        "by_priority": priority_counts
    }


# ==================== HELPER FUNCTIONS ====================

async def create_thread_entry(
    ticket_id: str,
    entry_type: str,
    author_id: str,
    author_name: str,
    author_type: str,
    content: str = None,
    attachments: list = None,
    is_internal: bool = False,
    event_type: str = None,
    event_data: dict = None,
    author_email: str = None
) -> dict:
    """Create a thread entry"""
    entry = TicketThreadEntry(
        ticket_id=ticket_id,
        entry_type=entry_type,
        content=content,
        author_id=author_id,
        author_name=author_name,
        author_type=author_type,
        author_email=author_email,
        attachments=attachments or [],
        is_internal=is_internal,
        event_type=event_type,
        event_data=event_data
    )
    entry_dict = entry.model_dump()
    await db.ticket_thread.insert_one(entry_dict)
    return entry_dict


def calculate_sla_due_times(sla_policy: dict, priority: str) -> dict:
    """Calculate SLA due times based on policy and priority"""
    now = datetime.now()
    
    # Get priority multiplier
    multipliers = sla_policy.get("priority_multipliers", {})
    multiplier = multipliers.get(priority, 1.0)
    
    # Calculate response due time
    response_hours = sla_policy.get("response_time_hours", 4) * multiplier
    response_due = now + timedelta(hours=response_hours)
    
    # Calculate resolution due time
    resolution_hours = sla_policy.get("resolution_time_hours", 24) * multiplier
    resolution_due = now + timedelta(hours=resolution_hours)
    
    return {
        "sla_policy_id": sla_policy.get("id"),
        "sla_policy_name": sla_policy.get("name"),
        "response_due_at": response_due.isoformat(),
        "resolution_due_at": resolution_due.isoformat(),
        "response_met": None,
        "resolution_met": None,
        "first_response_at": None,
        "resolved_at": None,
        "is_paused": False,
        "paused_at": None,
        "total_paused_seconds": 0,
        "response_breached": False,
        "resolution_breached": False,
        "escalated": False
    }


# ==================== PUBLIC DEPARTMENTS (for customer portal) ====================

@router.get("/portal/departments")
async def list_departments_public(
    user: dict = Depends(lambda: get_current_company_user)
):
    """List public departments for ticket creation"""
    departments = await db.ticketing_departments.find(
        {
            "is_deleted": {"$ne": True},
            "is_active": True,
            "is_public": True,
            "$or": [
                {"company_id": None},
                {"company_id": user.get("company_id")}
            ]
        },
        {"_id": 0, "id": 1, "name": 1, "description": 1}
    ).sort("sort_order", 1).to_list(50)
    return departments
