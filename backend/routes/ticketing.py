"""
Enterprise Ticketing System API Routes
Phase 2: Advanced Features - Help Topics, Custom Forms, Collaboration, Canned Responses
"""
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel

from models.ticketing import (
    Department, DepartmentCreate, DepartmentUpdate,
    SLAPolicy, SLAPolicyCreate, SLAPolicyUpdate,
    Ticket, TicketCreate, TicketUpdate,
    TicketThreadEntry, TicketReplyCreate,
    TicketCategory, CustomFieldDefinition,
    TicketingStaffProfile, TicketSLAStatus,
    HelpTopic, HelpTopicCreate, HelpTopicUpdate,
    CustomForm, CustomFormCreate, CustomFormUpdate, CustomFormField,
    TicketParticipant, AddParticipantRequest,
    CannedResponse, CannedResponseCreate, CannedResponseUpdate,
    TicketFormData,
    TICKET_STATUSES, TICKET_PRIORITIES, TICKET_SOURCES,
    THREAD_ENTRY_TYPES, SYSTEM_EVENT_TYPES, STAFF_ROLES
)
from utils.helpers import get_ist_isoformat

router = APIRouter(prefix="/ticketing", tags=["Ticketing"])


# ==================== DEPENDENCY INJECTION ====================
_db: AsyncIOMotorDatabase = None
_log_audit = None

# These will be imported directly from services.auth
from services.auth import get_current_admin, get_current_company_user


def init_ticketing_router(database, admin_dependency, company_user_dependency, audit_function):
    """Initialize the ticketing router with dependencies"""
    global _db, _log_audit
    _db = database
    _log_audit = audit_function


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
async def list_departments(include_inactive: bool = False, admin: dict = Depends(get_current_admin)):
    """List all departments (admin only)"""
    query = {"is_deleted": {"$ne": True}}
    if not include_inactive:
        query["is_active"] = True
    departments = await _db.ticketing_departments.find(query, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return departments


@router.post("/admin/departments")
async def create_department(data: DepartmentCreate, admin: dict = Depends(get_current_admin)):
    """Create a new department"""
    dept = Department(**data.model_dump(), created_by=admin.get("id"))
    await _db.ticketing_departments.insert_one(dept.model_dump())
    await _log_audit("ticketing_department", dept.id, "create", data.model_dump(), admin)
    return dept.model_dump()


@router.get("/admin/departments/{dept_id}")
async def get_department(dept_id: str, admin: dict = Depends(get_current_admin)):
    """Get department by ID"""
    dept = await _db.ticketing_departments.find_one({"id": dept_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    return dept


@router.put("/admin/departments/{dept_id}")
async def update_department(dept_id: str, updates: DepartmentUpdate, admin: dict = Depends(get_current_admin)):
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
async def delete_department(dept_id: str, admin: dict = Depends(get_current_admin)):
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
async def list_sla_policies(include_inactive: bool = False, admin: dict = Depends(get_current_admin)):
    """List all SLA policies"""
    query = {"is_deleted": {"$ne": True}}
    if not include_inactive:
        query["is_active"] = True
    return await _db.ticketing_sla_policies.find(query, {"_id": 0}).to_list(100)


@router.post("/admin/sla-policies")
async def create_sla_policy(data: SLAPolicyCreate, admin: dict = Depends(get_current_admin)):
    """Create a new SLA policy"""
    policy_data = {k: v for k, v in data.model_dump().items() if v is not None}
    policy = SLAPolicy(**policy_data, created_by=admin.get("id"))
    
    if data.is_default:
        await _db.ticketing_sla_policies.update_many({"is_default": True}, {"$set": {"is_default": False}})
    
    await _db.ticketing_sla_policies.insert_one(policy.model_dump())
    await _log_audit("ticketing_sla_policy", policy.id, "create", data.model_dump(), admin)
    return policy.model_dump()


@router.get("/admin/sla-policies/{policy_id}")
async def get_sla_policy(policy_id: str, admin: dict = Depends(get_current_admin)):
    """Get SLA policy by ID"""
    policy = await _db.ticketing_sla_policies.find_one({"id": policy_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")
    return policy


@router.put("/admin/sla-policies/{policy_id}")
async def update_sla_policy(policy_id: str, updates: SLAPolicyUpdate, admin: dict = Depends(get_current_admin)):
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
async def delete_sla_policy(policy_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete an SLA policy"""
    policy = await _db.ticketing_sla_policies.find_one({"id": policy_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not policy:
        raise HTTPException(status_code=404, detail="SLA Policy not found")
    
    await _db.ticketing_sla_policies.update_one({"id": policy_id}, {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}})
    await _log_audit("ticketing_sla_policy", policy_id, "delete", {}, admin)
    return {"message": "SLA Policy deleted"}


# ==================== CATEGORIES ====================

@router.get("/admin/categories")
async def list_categories(admin: dict = Depends(get_current_admin)):
    """List all ticket categories"""
    return await _db.ticketing_categories.find({"is_deleted": {"$ne": True}}, {"_id": 0}).sort("sort_order", 1).to_list(100)


@router.post("/admin/categories")
async def create_category(data: dict, admin: dict = Depends(get_current_admin)):
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
async def update_category(category_id: str, data: dict, admin: dict = Depends(get_current_admin)):
    """Update a ticket category"""
    category = await _db.ticketing_categories.find_one({"id": category_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {k: v for k, v in data.items() if v is not None}
    await _db.ticketing_categories.update_one({"id": category_id}, {"$set": update_data})
    return await _db.ticketing_categories.find_one({"id": category_id}, {"_id": 0})


@router.delete("/admin/categories/{category_id}")
async def delete_category(category_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a category"""
    await _db.ticketing_categories.update_one({"id": category_id}, {"$set": {"is_deleted": True}})
    return {"message": "Category deleted"}


# ==================== TICKETS - ADMIN ====================

@router.get("/admin/tickets")
async def list_tickets_admin(
    status: Optional[str] = None, priority: Optional[str] = None, department_id: Optional[str] = None,
    assigned_to: Optional[str] = None, company_id: Optional[str] = None, unassigned: bool = False,
    search: Optional[str] = None, limit: int = Query(50, le=200), skip: int = 0,
    admin: dict = Depends(get_current_admin)
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
    admin: dict = Depends(get_current_admin)
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
    return await _db.tickets.find_one({"id": ticket.id}, {"_id": 0})


@router.get("/admin/tickets/{ticket_id}")
async def get_ticket_admin(ticket_id: str, admin: dict = Depends(get_current_admin)):
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
async def update_ticket_admin(ticket_id: str, updates: TicketUpdate, admin: dict = Depends(get_current_admin)):
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
async def reply_to_ticket_admin(ticket_id: str, reply: TicketReplyCreate, admin: dict = Depends(get_current_admin)):
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
async def assign_ticket(ticket_id: str, assignee_id: str, admin: dict = Depends(get_current_admin)):
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
async def list_tickets_customer(status: Optional[str] = None, limit: int = Query(20, le=100), user: dict = Depends(get_current_company_user)):
    """List tickets for current customer"""
    query = {"company_id": user.get("company_id"), "requester_id": user.get("id"), "is_deleted": {"$ne": True}}
    if status:
        query["status"] = status
    return await _db.tickets.find(query, {"_id": 0, "internal_note_count": 0}).sort("created_at", -1).limit(limit).to_list(limit)


@router.post("/portal/tickets")
async def create_ticket_customer(data: TicketCreate, user: dict = Depends(get_current_company_user)):
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
    return await _db.tickets.find_one({"id": ticket.id}, {"_id": 0})


@router.get("/portal/tickets/{ticket_id}")
async def get_ticket_customer(ticket_id: str, user: dict = Depends(get_current_company_user)):
    """Get ticket details (customer view - no internal notes)"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "company_id": user.get("company_id"), "requester_id": user.get("id"), "is_deleted": {"$ne": True}}, {"_id": 0, "internal_note_count": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    thread = await _db.ticket_thread.find({"ticket_id": ticket_id, "is_internal": {"$ne": True}, "is_hidden": {"$ne": True}}, {"_id": 0}).sort("created_at", 1).to_list(500)
    return {**ticket, "thread": thread}


@router.post("/portal/tickets/{ticket_id}/reply")
async def reply_to_ticket_customer(ticket_id: str, reply: TicketReplyCreate, user: dict = Depends(get_current_company_user)):
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
async def get_ticketing_dashboard(admin: dict = Depends(get_current_admin)):
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
    return await _db.ticket_thread.find_one({"id": entry.id}, {"_id": 0})


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
async def list_departments_public(user: dict = Depends(get_current_company_user)):
    """List public departments for ticket creation"""
    return await _db.ticketing_departments.find(
        {"is_deleted": {"$ne": True}, "is_active": True, "is_public": True, "$or": [{"company_id": None}, {"company_id": user.get("company_id")}]},
        {"_id": 0, "id": 1, "name": 1, "description": 1}
    ).sort("sort_order", 1).to_list(50)


# ==================== PUBLIC TICKET PORTAL (No Auth Required) ====================

class PublicTicketCreate(BaseModel):
    """Create ticket from public portal - no auth required"""
    name: str
    email: str
    phone: Optional[str] = None
    subject: str
    description: str
    department_id: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    attachments: List[dict] = []


@router.get("/public/departments")
async def list_departments_for_public():
    """List public departments for anonymous ticket creation"""
    return await _db.ticketing_departments.find(
        {"is_deleted": {"$ne": True}, "is_active": True, "is_public": True, "company_id": None},
        {"_id": 0, "id": 1, "name": 1, "description": 1}
    ).sort("sort_order", 1).to_list(50)


@router.get("/public/categories")
async def list_categories_for_public():
    """List categories for anonymous ticket creation"""
    return await _db.ticketing_categories.find(
        {"is_deleted": {"$ne": True}, "is_active": True, "company_id": None},
        {"_id": 0, "id": 1, "name": 1, "description": 1, "auto_department_id": 1, "auto_priority": 1}
    ).sort("sort_order", 1).to_list(50)


@router.post("/public/tickets")
async def create_public_ticket(data: PublicTicketCreate):
    """Create a ticket from the public portal (no authentication required)"""
    # Validate email format
    import re
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Get department and SLA
    sla_policy = None
    dept = None
    if data.department_id:
        dept = await _db.ticketing_departments.find_one(
            {"id": data.department_id, "is_deleted": {"$ne": True}, "is_public": True, "company_id": None},
            {"_id": 0}
        )
        if dept and dept.get("default_sla_id"):
            sla_policy = await _db.ticketing_sla_policies.find_one({"id": dept["default_sla_id"]}, {"_id": 0})
    
    if not sla_policy:
        sla_policy = await _db.ticketing_sla_policies.find_one(
            {"is_default": True, "is_deleted": {"$ne": True}}, {"_id": 0}
        )
    
    sla_status = calculate_sla_due_times(sla_policy, data.priority) if sla_policy else None
    
    # Create ticket
    ticket_id = str(uuid.uuid4())
    ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    ticket = {
        "id": ticket_id,
        "ticket_number": ticket_number,
        "company_id": "PUBLIC",  # Special marker for public tickets
        "source": "portal",
        "department_id": data.department_id,
        "subject": data.subject,
        "description": data.description,
        "status": "open",
        "priority": data.priority,
        "priority_order": {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(data.priority, 2),
        "requester_id": "public",
        "requester_name": data.name,
        "requester_email": data.email,
        "requester_phone": data.phone,
        "assigned_to": None,
        "assigned_to_name": None,
        "assigned_at": None,
        "watchers": [],
        "sla_status": sla_status,
        "tags": [],
        "category": data.category,
        "custom_fields": {},
        "device_id": None,
        "service_id": None,
        "attachments": data.attachments,
        "reply_count": 0,
        "internal_note_count": 0,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "first_response_at": None,
        "resolved_at": None,
        "closed_at": None,
        "last_customer_reply_at": None,
        "last_staff_reply_at": None,
        "created_by": "public",
        "created_by_type": "customer",
        "is_deleted": False
    }
    
    await _db.tickets.insert_one(ticket)
    
    # Create initial thread entry
    await create_thread_entry(
        ticket_id, "system_event", "public", data.name, "customer",
        event_type="ticket_created", event_data={"source": "public_portal"},
        author_email=data.email
    )
    
    # Return ticket info (excluding internal fields)
    return {
        "id": ticket_id,
        "ticket_number": ticket_number,
        "subject": data.subject,
        "status": "open",
        "created_at": ticket["created_at"],
        "message": "Your ticket has been submitted successfully. Please save your ticket number for future reference."
    }


@router.get("/public/tickets/{ticket_number}")
async def get_public_ticket_status(ticket_number: str, email: str = Query(..., description="Email used when creating the ticket")):
    """Check status of a public ticket by ticket number and email"""
    ticket = await _db.tickets.find_one(
        {
            "ticket_number": ticket_number,
            "requester_email": {"$regex": f"^{re.escape(email)}$", "$options": "i"},
            "is_deleted": {"$ne": True}
        },
        {"_id": 0, "internal_note_count": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found. Please check your ticket number and email.")
    
    # Get public thread entries (exclude internal notes)
    thread = await _db.ticket_thread.find(
        {"ticket_id": ticket["id"], "is_internal": {"$ne": True}, "is_hidden": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    
    # Get department name
    department = None
    if ticket.get("department_id"):
        department = await _db.ticketing_departments.find_one(
            {"id": ticket["department_id"]}, {"_id": 0, "name": 1}
        )
    
    return {
        **ticket,
        "thread": thread,
        "department_name": department.get("name") if department else None
    }


@router.post("/public/tickets/{ticket_number}/reply")
async def reply_to_public_ticket(ticket_number: str, content: str = Query(...), email: str = Query(...)):
    """Add a reply to a public ticket"""
    ticket = await _db.tickets.find_one(
        {
            "ticket_number": ticket_number,
            "requester_email": {"$regex": f"^{re.escape(email)}$", "$options": "i"},
            "is_deleted": {"$ne": True}
        },
        {"_id": 0}
    )
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if ticket.get("status") in ["closed"]:
        raise HTTPException(status_code=400, detail="Cannot reply to a closed ticket")
    
    # Create reply entry
    entry = await create_thread_entry(
        ticket["id"], "customer_message", "public", ticket.get("requester_name", "Customer"), "customer",
        content=content, is_internal=False, author_email=email
    )
    
    # Update ticket
    update_data = {
        "updated_at": get_ist_isoformat(),
        "last_customer_reply_at": get_ist_isoformat(),
        "reply_count": ticket.get("reply_count", 0) + 1
    }
    
    # If waiting on customer, reopen
    if ticket.get("status") == "waiting_on_customer":
        update_data["status"] = "open"
        sla_status = ticket.get("sla_status") or {}
        if sla_status.get("paused_at"):
            paused_duration = (datetime.now() - datetime.fromisoformat(sla_status["paused_at"].replace("Z", "+00:00"))).total_seconds()
            sla_status["total_paused_seconds"] = sla_status.get("total_paused_seconds", 0) + int(paused_duration)
        sla_status["is_paused"], sla_status["paused_at"] = False, None
        update_data["sla_status"] = sla_status
    
    await _db.tickets.update_one({"id": ticket["id"]}, {"$set": update_data})
    
    return {"message": "Reply added successfully", "entry_id": entry.get("id")}
