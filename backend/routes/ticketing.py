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
_db: AsyncIOMotorDatabase = None
_get_current_admin = None
_get_current_company_user = None
_log_audit = None


def init_ticketing_router(database, admin_dependency, company_user_dependency, audit_function):
    """Initialize the ticketing router with dependencies"""
    global _db, _get_current_admin, _get_current_company_user, _log_audit
    _db = database
    _get_current_admin = admin_dependency
    _get_current_company_user = company_user_dependency
    _log_audit = audit_function


def get_admin_dep():
    return _get_current_admin

def get_company_user_dep():
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
async def list_departments(include_inactive: bool = False, admin: dict = Depends(get_admin_dep)):
    """List all departments (admin only)"""
    query = {"is_deleted": {"$ne": True}}
    if not include_inactive:
        query["is_active"] = True
    departments = await _db.ticketing_departments.find(query, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return departments


@router.post("/admin/departments")
async def create_department(data: DepartmentCreate, admin: dict = Depends(get_admin_dep)):
    """Create a new department"""
    dept = Department(**data.model_dump(), created_by=admin.get("id"))
    await _db.ticketing_departments.insert_one(dept.model_dump())
    await _log_audit("ticketing_department", dept.id, "create", data.model_dump(), admin)
    return dept.model_dump()


@router.get("/admin/departments/{dept_id}")
async def get_department(dept_id: str, admin: dict = Depends(get_admin_dep)):
    """Get department by ID"""
    dept = await _db.ticketing_departments.find_one({"id": dept_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.put("/admin/departments/{dept_id}")
async def update_department(dept_id: str, updates: DepartmentUpdate, admin: dict = Depends(get_admin_dep)):
    """Update a department"""
    dept = await _db.ticketing_departments.find_one({"id": dept_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.ticketing_departments.update_one({"id": dept_id}, {"$set": update_data})
    await _log_audit("ticketing_department", dept_id, "update", update_data, admin)
    return await _db.ticketing_departments.find_one({"id": dept_id}, {"_id": 0})


@router.delete("/admin/departments/{dept_id}")
async def delete_department(dept_id: str, admin: dict = Depends(get_admin_dep)):
    """Soft delete a department"""
    dept = await _db.ticketing_departments.find_one({"id": dept_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    open_tickets = await _db.tickets.count_documents({
        "department_id": dept_id, "status": {"$nin": ["resolved", "closed"]}, "is_deleted": {"$ne": True}
    })
    if open_tickets > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete department with {open_tickets} open tickets")
    
    await _db.ticketing_departments.update_one({"id": dept_id}, {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}})
    await _log_audit("ticketing_department", dept_id, "delete", {}, admin)
    return {"message": "Department deleted"}


# ==================== SLA POLICIES ====================

@router.get("/admin/sla-policies")
async def list_sla_policies(include_inactive: bool = False, admin: dict = Depends(get_admin_dep)):
    """List all SLA policies"""
    query = {"is_deleted": {"$ne": True}}
    if not include_inactive:
        query["is_active"] = True
    return await _db.ticketing_sla_policies.find(query, {"_id": 0}).to_list(100)


@router.post("/admin/sla-policies")
async def create_sla_policy(data: SLAPolicyCreate, admin: dict = Depends(get_admin_dep)):
    """Create a new SLA policy"""
    policy = SLAPolicy(**data.model_dump(), created_by=admin.get("id"))
    
    if data.is_default:
        await _db.ticketing_sla_policies.update_many({"is_default": True}, {"$set": {"is_default": False}})
    
    await _db.ticketing_sla_policies.insert_one(policy.model_dump())
    await _log_audit("ticketing_sla_policy", policy.id, "create", data.model_dump(), admin)
    return policy.model_dump()


@router.get("/admin/sla-policies/{policy_id}")
async def get_sla_policy(policy_id: str, admin: dict = Depends(get_admin_dep)):
    """Get SLA policy by ID"""
    policy = await _db.ticketing_sla_policies.find_one({"id": policy_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")
    return policy


@router.put("/admin/sla-policies/{policy_id}")
async def update_sla_policy(policy_id: str, updates: SLAPolicyUpdate, admin: dict = Depends(get_admin_dep)):
    """Update an SLA policy"""
    policy = await _db.ticketing_sla_policies.find_one({"id": policy_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data.get("is_default"):
        await _db.ticketing_sla_policies.update_many({"is_default": True, "id": {"$ne": policy_id}}, {"$set": {"is_default": False}})
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.ticketing_sla_policies.update_one({"id": policy_id}, {"$set": update_data})
    await _log_audit("ticketing_sla_policy", policy_id, "update", update_data, admin)
    return await _db.ticketing_sla_policies.find_one({"id": policy_id}, {"_id": 0})


@router.delete("/admin/sla-policies/{policy_id}")
async def delete_sla_policy(policy_id: str, admin: dict = Depends(get_admin_dep)):
    """Soft delete an SLA policy"""
    policy = await _db.ticketing_sla_policies.find_one({"id": policy_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")
    
    await _db.ticketing_sla_policies.update_one({"id": policy_id}, {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}})
    await _log_audit("ticketing_sla_policy", policy_id, "delete", {}, admin)
    return {"message": "SLA Policy deleted"}


# ==================== CATEGORIES ====================

@router.get("/admin/categories")
async def list_categories(admin: dict = Depends(get_admin_dep)):
    """List all ticket categories"""
    return await _db.ticketing_categories.find({"is_deleted": {"$ne": True}}, {"_id": 0}).sort("sort_order", 1).to_list(100)


@router.post("/admin/categories")
async def create_category(data: dict, admin: dict = Depends(get_admin_dep)):
    """Create a ticket category"""
    category = TicketCategory(
        name=data.get("name"), description=data.get("description"), parent_id=data.get("parent_id"),
        auto_department_id=data.get("auto_department_id"), auto_priority=data.get("auto_priority"),
        sort_order=data.get("sort_order", 0)
    )
    await _db.ticketing_categories.insert_one(category.model_dump())
    await _log_audit("ticketing_category", category.id, "create", data, admin)
    return category.model_dump()


@router.put("/admin/categories/{category_id}")
async def update_category(category_id: str, data: dict, admin: dict = Depends(get_admin_dep)):
    """Update a ticket category"""
    category = await _db.ticketing_categories.find_one({"id": category_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {k: v for k, v in data.items() if v is not None}
    await _db.ticketing_categories.update_one({"id": category_id}, {"$set": update_data})
    return await _db.ticketing_categories.find_one({"id": category_id}, {"_id": 0})


@router.delete("/admin/categories/{category_id}")
async def delete_category(category_id: str, admin: dict = Depends(get_admin_dep)):
    """Soft delete a category"""
    await _db.ticketing_categories.update_one({"id": category_id}, {"$set": {"is_deleted": True}})
    return {"message": "Category deleted"}


# ==================== TICKETS - ADMIN ====================

@router.get("/admin/tickets")
async def list_tickets_admin(
    status: Optional[str] = None, priority: Optional[str] = None, department_id: Optional[str] = None,
    assigned_to: Optional[str] = None, company_id: Optional[str] = None, unassigned: bool = False,
    search: Optional[str] = None, limit: int = Query(50, le=200), skip: int = 0,
    admin: dict = Depends(get_admin_dep)
):
    """List tickets with filters (admin view)"""
    query = {"is_deleted": {"$ne": True}}
    if status: query["status"] = status
    if priority: query["priority"] = priority
    if department_id: query["department_id"] = department_id
    if assigned_to: query["assigned_to"] = assigned_to
    if company_id: query["company_id"] = company_id
    if unassigned: query["assigned_to"] = None
    if search:
        query["$or"] = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"subject": {"$regex": search, "$options": "i"}},
            {"requester_name": {"$regex": search, "$options": "i"}},
            {"requester_email": {"$regex": search, "$options": "i"}}
        ]
    
    total = await _db.tickets.count_documents(query)
    tickets = await _db.tickets.find(query, {"_id": 0}).sort([("priority_order", -1), ("created_at", -1)]).skip(skip).limit(limit).to_list(limit)
    return {"tickets": tickets, "total": total, "limit": limit, "skip": skip}


@router.post("/admin/tickets")
async def create_ticket_admin(
    data: TicketCreate, requester_id: str = Query(..., description="Company user ID of requester"),
    admin: dict = Depends(get_admin_dep)
):
    """Create a ticket on behalf of a customer (admin)"""
    requester = await _db.company_users.find_one({"id": requester_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not requester:
        raise HTTPException(status_code=404, detail="Requester not found")
    
    sla_policy = None
    if data.department_id:
        dept = await _db.ticketing_departments.find_one({"id": data.department_id, "is_deleted": {"$ne": True}}, {"_id": 0})
        if dept and dept.get("default_sla_id"):
            sla_policy = await _db.ticketing_sla_policies.find_one({"id": dept["default_sla_id"]}, {"_id": 0})
    if not sla_policy:
        sla_policy = await _db.ticketing_sla_policies.find_one({"is_default": True, "is_deleted": {"$ne": True}}, {"_id": 0})
    
    sla_status = calculate_sla_due_times(sla_policy, data.priority) if sla_policy else None
    
    ticket = Ticket(
        **data.model_dump(), company_id=requester.get("company_id"), requester_id=requester_id,
        requester_name=requester.get("name", "Unknown"), requester_email=requester.get("email", ""),
        requester_phone=requester.get("phone"), sla_status=sla_status,
        created_by=admin.get("id"), created_by_type="staff"
    )
    
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ticket_dict = ticket.model_dump()
    ticket_dict["priority_order"] = priority_order.get(data.priority, 2)
    
    await _db.tickets.insert_one(ticket_dict)
    await create_thread_entry(ticket.id, "system_event", admin.get("id"), admin.get("name"), "admin", event_type="ticket_created", event_data={"created_by_staff": True})
    await _log_audit("ticket", ticket.id, "create", data.model_dump(), admin)
    return ticket_dict


@router.get("/admin/tickets/{ticket_id}")
async def get_ticket_admin(ticket_id: str, admin: dict = Depends(get_admin_dep)):
    """Get ticket details with thread"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    thread = await _db.ticket_thread.find({"ticket_id": ticket_id, "is_hidden": {"$ne": True}}, {"_id": 0}).sort("created_at", 1).to_list(500)
    department = None
    if ticket.get("department_id"):
        department = await _db.ticketing_departments.find_one({"id": ticket["department_id"]}, {"_id": 0, "name": 1, "id": 1})
    
    return {**ticket, "thread": thread, "department": department}


@router.put("/admin/tickets/{ticket_id}")
async def update_ticket_admin(ticket_id: str, updates: TicketUpdate, admin: dict = Depends(get_admin_dep)):
    """Update ticket (admin)"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    changes = []
    
    # Handle status change
    if "status" in update_data and update_data["status"] != ticket.get("status"):
        old_status, new_status = ticket.get("status"), update_data["status"]
        changes.append(("status", old_status, new_status))
        
        sla_status = ticket.get("sla_status") or {}
        if new_status in ["waiting_on_customer", "waiting_on_third_party"]:
            sla_status["is_paused"], sla_status["paused_at"] = True, get_ist_isoformat()
        elif old_status in ["waiting_on_customer", "waiting_on_third_party"]:
            if sla_status.get("paused_at"):
                paused_duration = (datetime.now() - datetime.fromisoformat(sla_status["paused_at"].replace("Z", "+00:00"))).total_seconds()
                sla_status["total_paused_seconds"] = sla_status.get("total_paused_seconds", 0) + int(paused_duration)
            sla_status["is_paused"], sla_status["paused_at"] = False, None
        
        if new_status == "resolved":
            update_data["resolved_at"] = get_ist_isoformat()
            sla_status["resolved_at"] = get_ist_isoformat()
            sla_status["resolution_met"] = not sla_status.get("resolution_breached", False)
        if new_status == "closed":
            update_data["closed_at"] = get_ist_isoformat()
        if old_status in ["resolved", "closed"] and new_status not in ["resolved", "closed"]:
            update_data["resolved_at"], update_data["closed_at"] = None, None
        
        update_data["sla_status"] = sla_status
        await create_thread_entry(ticket_id, "system_event", admin.get("id"), admin.get("name"), "admin", event_type="status_changed", event_data={"old": old_status, "new": new_status})
    
    # Handle priority change
    if "priority" in update_data and update_data["priority"] != ticket.get("priority"):
        old_priority, new_priority = ticket.get("priority"), update_data["priority"]
        changes.append(("priority", old_priority, new_priority))
        update_data["priority_order"] = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(new_priority, 2)
        await create_thread_entry(ticket_id, "system_event", admin.get("id"), admin.get("name"), "admin", event_type="priority_changed", event_data={"old": old_priority, "new": new_priority})
    
    # Handle assignment change
    if "assigned_to" in update_data and update_data["assigned_to"] != ticket.get("assigned_to"):
        old_assignee, new_assignee = ticket.get("assigned_to"), update_data["assigned_to"]
        assignee_name = None
        if new_assignee:
            assignee = await _db.admin_users.find_one({"id": new_assignee}, {"name": 1})
            assignee_name = assignee.get("name") if assignee else None
        update_data["assigned_to_name"] = assignee_name
        update_data["assigned_at"] = get_ist_isoformat() if new_assignee else None
        event_type = "assigned" if not old_assignee else "reassigned"
        await create_thread_entry(ticket_id, "system_event", admin.get("id"), admin.get("name"), "admin", event_type=event_type, event_data={"old": old_assignee, "new": new_assignee, "assignee_name": assignee_name})
    
    # Handle department change
    if "department_id" in update_data and update_data["department_id"] != ticket.get("department_id"):
        await create_thread_entry(ticket_id, "system_event", admin.get("id"), admin.get("name"), "admin", event_type="department_changed", event_data={"old": ticket.get("department_id"), "new": update_data["department_id"]})
    
    update_data["updated_at"] = get_ist_isoformat()
    await _db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    await _log_audit("ticket", ticket_id, "update", {"changes": changes}, admin)
    return await _db.tickets.find_one({"id": ticket_id}, {"_id": 0})


@router.post("/admin/tickets/{ticket_id}/reply")
async def reply_to_ticket_admin(ticket_id: str, reply: TicketReplyCreate, admin: dict = Depends(get_admin_dep)):
    """Add a reply or internal note to a ticket (admin)"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    entry_type = "internal_note" if reply.is_internal else "technician_reply"
    entry = await create_thread_entry(ticket_id, entry_type, admin.get("id"), admin.get("name"), admin.get("role", "admin"), content=reply.content, attachments=reply.attachments, is_internal=reply.is_internal)
    
    update_data = {"updated_at": get_ist_isoformat()}
    if reply.is_internal:
        update_data["internal_note_count"] = ticket.get("internal_note_count", 0) + 1
    else:
        update_data["reply_count"] = ticket.get("reply_count", 0) + 1
        update_data["last_staff_reply_at"] = get_ist_isoformat()
        if not ticket.get("first_response_at"):
            update_data["first_response_at"] = get_ist_isoformat()
            sla_status = ticket.get("sla_status") or {}
            sla_status["first_response_at"] = get_ist_isoformat()
            sla_status["response_met"] = not sla_status.get("response_breached", False)
            update_data["sla_status"] = sla_status
    
    await _db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    return entry


@router.post("/admin/tickets/{ticket_id}/assign")
async def assign_ticket(ticket_id: str, assignee_id: str, admin: dict = Depends(get_admin_dep)):
    """Assign or reassign a ticket"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    assignee = await _db.admin_users.find_one({"id": assignee_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not assignee:
        raise HTTPException(status_code=404, detail="Assignee not found")
    
    old_assignee = ticket.get("assigned_to")
    event_type = "assigned" if not old_assignee else "reassigned"
    
    await _db.tickets.update_one({"id": ticket_id}, {"$set": {"assigned_to": assignee_id, "assigned_to_name": assignee.get("name"), "assigned_at": get_ist_isoformat(), "updated_at": get_ist_isoformat()}})
    await create_thread_entry(ticket_id, "system_event", admin.get("id"), admin.get("name"), "admin", event_type=event_type, event_data={"old": old_assignee, "new": assignee_id, "assignee_name": assignee.get("name")})
    
    return {"message": f"Ticket {event_type}", "assigned_to": assignee.get("name")}


# ==================== TICKETS - CUSTOMER PORTAL ====================

@router.get("/portal/tickets")
async def list_tickets_customer(status: Optional[str] = None, limit: int = Query(20, le=100), user: dict = Depends(get_company_user_dep)):
    """List tickets for current customer"""
    query = {"company_id": user.get("company_id"), "requester_id": user.get("id"), "is_deleted": {"$ne": True}}
    if status:
        query["status"] = status
    return await _db.tickets.find(query, {"_id": 0, "internal_note_count": 0}).sort("created_at", -1).limit(limit).to_list(limit)


@router.post("/portal/tickets")
async def create_ticket_customer(data: TicketCreate, user: dict = Depends(get_company_user_dep)):
    """Create a ticket (customer portal)"""
    sla_policy = None
    if data.department_id:
        dept = await _db.ticketing_departments.find_one({"id": data.department_id, "is_deleted": {"$ne": True}, "is_public": True}, {"_id": 0})
        if dept and dept.get("default_sla_id"):
            sla_policy = await _db.ticketing_sla_policies.find_one({"id": dept["default_sla_id"]}, {"_id": 0})
    if not sla_policy:
        sla_policy = await _db.ticketing_sla_policies.find_one({"is_default": True, "is_deleted": {"$ne": True}}, {"_id": 0})
    
    sla_status = calculate_sla_due_times(sla_policy, data.priority) if sla_policy else None
    
    ticket = Ticket(
        **data.model_dump(), company_id=user.get("company_id"), requester_id=user.get("id"),
        requester_name=user.get("name", "Unknown"), requester_email=user.get("email", ""),
        requester_phone=user.get("phone"), sla_status=sla_status, created_by=user.get("id"), created_by_type="customer"
    )
    
    ticket_dict = ticket.model_dump()
    ticket_dict["priority_order"] = {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(data.priority, 2)
    
    await _db.tickets.insert_one(ticket_dict)
    await create_thread_entry(ticket.id, "system_event", user.get("id"), user.get("name"), "customer", event_type="ticket_created", event_data={})
    return ticket_dict


@router.get("/portal/tickets/{ticket_id}")
async def get_ticket_customer(ticket_id: str, user: dict = Depends(get_company_user_dep)):
    """Get ticket details (customer view - no internal notes)"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "company_id": user.get("company_id"), "requester_id": user.get("id"), "is_deleted": {"$ne": True}}, {"_id": 0, "internal_note_count": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    thread = await _db.ticket_thread.find({"ticket_id": ticket_id, "is_internal": {"$ne": True}, "is_hidden": {"$ne": True}}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return {**ticket, "thread": thread}


@router.post("/portal/tickets/{ticket_id}/reply")
async def reply_to_ticket_customer(ticket_id: str, reply: TicketReplyCreate, user: dict = Depends(get_company_user_dep)):
    """Add a reply to a ticket (customer)"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "company_id": user.get("company_id"), "requester_id": user.get("id"), "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    entry = await create_thread_entry(ticket_id, "customer_message", user.get("id"), user.get("name"), "customer", author_email=user.get("email"), content=reply.content, attachments=reply.attachments, is_internal=False)
    
    update_data = {"updated_at": get_ist_isoformat(), "last_customer_reply_at": get_ist_isoformat(), "reply_count": ticket.get("reply_count", 0) + 1}
    if ticket.get("status") == "waiting_on_customer":
        update_data["status"] = "open"
        sla_status = ticket.get("sla_status") or {}
        if sla_status.get("paused_at"):
            paused_duration = (datetime.now() - datetime.fromisoformat(sla_status["paused_at"].replace("Z", "+00:00"))).total_seconds()
            sla_status["total_paused_seconds"] = sla_status.get("total_paused_seconds", 0) + int(paused_duration)
        sla_status["is_paused"], sla_status["paused_at"] = False, None
        update_data["sla_status"] = sla_status
    
    await _db.tickets.update_one({"id": ticket_id}, {"$set": update_data})
    return entry


# ==================== DASHBOARD & STATS ====================

@router.get("/admin/dashboard")
async def get_ticketing_dashboard(admin: dict = Depends(get_admin_dep)):
    """Get ticketing dashboard stats"""
    status_counts = {}
    for status in TICKET_STATUSES:
        status_counts[status] = await _db.tickets.count_documents({"status": status, "is_deleted": {"$ne": True}})
    
    priority_counts = {}
    for priority in TICKET_PRIORITIES:
        priority_counts[priority] = await _db.tickets.count_documents({"priority": priority, "status": {"$nin": ["resolved", "closed"]}, "is_deleted": {"$ne": True}})
    
    unassigned = await _db.tickets.count_documents({"assigned_to": None, "status": {"$nin": ["resolved", "closed"]}, "is_deleted": {"$ne": True}})
    sla_breached = await _db.tickets.count_documents({"$or": [{"sla_status.response_breached": True}, {"sla_status.resolution_breached": True}], "status": {"$nin": ["resolved", "closed"]}, "is_deleted": {"$ne": True}})
    total_open = await _db.tickets.count_documents({"status": {"$nin": ["resolved", "closed"]}, "is_deleted": {"$ne": True}})
    
    return {"total_open": total_open, "unassigned": unassigned, "sla_breached": sla_breached, "by_status": status_counts, "by_priority": priority_counts}


# ==================== HELPER FUNCTIONS ====================

async def create_thread_entry(ticket_id, entry_type, author_id, author_name, author_type, content=None, attachments=None, is_internal=False, event_type=None, event_data=None, author_email=None):
    """Create a thread entry"""
    entry = TicketThreadEntry(
        ticket_id=ticket_id, entry_type=entry_type, content=content, author_id=author_id,
        author_name=author_name, author_type=author_type, author_email=author_email,
        attachments=attachments or [], is_internal=is_internal, event_type=event_type, event_data=event_data
    )
    entry_dict = entry.model_dump()
    await _db.ticket_thread.insert_one(entry_dict)
    return entry_dict


def calculate_sla_due_times(sla_policy, priority):
    """Calculate SLA due times based on policy and priority"""
    now = datetime.now()
    multipliers = sla_policy.get("priority_multipliers", {})
    multiplier = multipliers.get(priority, 1.0)
    
    response_hours = sla_policy.get("response_time_hours", 4) * multiplier
    resolution_hours = sla_policy.get("resolution_time_hours", 24) * multiplier
    
    return {
        "sla_policy_id": sla_policy.get("id"), "sla_policy_name": sla_policy.get("name"),
        "response_due_at": (now + timedelta(hours=response_hours)).isoformat(),
        "resolution_due_at": (now + timedelta(hours=resolution_hours)).isoformat(),
        "response_met": None, "resolution_met": None, "first_response_at": None, "resolved_at": None,
        "is_paused": False, "paused_at": None, "total_paused_seconds": 0,
        "response_breached": False, "resolution_breached": False, "escalated": False
    }


# ==================== PUBLIC DEPARTMENTS (for customer portal) ====================

@router.get("/portal/departments")
async def list_departments_public(user: dict = Depends(get_company_user_dep)):
    """List public departments for ticket creation"""
    return await _db.ticketing_departments.find(
        {"is_deleted": {"$ne": True}, "is_active": True, "is_public": True, "$or": [{"company_id": None}, {"company_id": user.get("company_id")}]},
        {"_id": 0, "id": 1, "name": 1, "description": 1}
    ).sort("sort_order", 1).to_list(50)
