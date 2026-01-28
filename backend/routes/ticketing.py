"""
Enterprise Ticketing System API Routes
Phase 2: Advanced Features - Help Topics, Custom Forms, Collaboration, Canned Responses
Phase 3: Email Integration - SMTP notifications and IMAP sync
"""
import uuid
import re
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
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


# ==================== HELP TOPICS (Replaces Categories) ====================

@router.get("/admin/help-topics")
async def list_help_topics(include_inactive: bool = False, admin: dict = Depends(get_current_admin)):
    """List all help topics"""
    query = {"is_deleted": {"$ne": True}}
    if not include_inactive:
        query["is_active"] = True
    topics = await _db.ticketing_help_topics.find(query, {"_id": 0}).sort("sort_order", 1).to_list(100)
    return topics


@router.post("/admin/help-topics")
async def create_help_topic(data: HelpTopicCreate, admin: dict = Depends(get_current_admin)):
    """Create a new help topic"""
    topic = HelpTopic(**data.model_dump(), created_by=admin.get("id"))
    await _db.ticketing_help_topics.insert_one(topic.model_dump())
    await _log_audit("help_topic", topic.id, "create", data.model_dump(), admin)
    return topic.model_dump()


@router.get("/admin/help-topics/{topic_id}")
async def get_help_topic(topic_id: str, admin: dict = Depends(get_current_admin)):
    """Get help topic by ID"""
    topic = await _db.ticketing_help_topics.find_one({"id": topic_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not topic:
        raise HTTPException(status_code=404, detail="Help topic not found")
    return topic


@router.put("/admin/help-topics/{topic_id}")
async def update_help_topic(topic_id: str, updates: HelpTopicUpdate, admin: dict = Depends(get_current_admin)):
    """Update a help topic"""
    topic = await _db.ticketing_help_topics.find_one({"id": topic_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not topic:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.ticketing_help_topics.update_one({"id": topic_id}, {"$set": update_data})
    await _log_audit("help_topic", topic_id, "update", update_data, admin)
    return await _db.ticketing_help_topics.find_one({"id": topic_id}, {"_id": 0})


@router.delete("/admin/help-topics/{topic_id}")
async def delete_help_topic(topic_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a help topic"""
    topic = await _db.ticketing_help_topics.find_one({"id": topic_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not topic:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    await _db.ticketing_help_topics.update_one({"id": topic_id}, {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}})
    await _log_audit("help_topic", topic_id, "delete", {}, admin)
    return {"message": "Help topic deleted"}


@router.get("/portal/help-topics")
async def list_help_topics_public(user: dict = Depends(get_current_company_user)):
    """List public help topics for ticket creation"""
    return await _db.ticketing_help_topics.find(
        {"is_deleted": {"$ne": True}, "is_active": True, "is_public": True},
        {"_id": 0, "id": 1, "name": 1, "description": 1, "icon": 1, "custom_form_id": 1}
    ).sort("sort_order", 1).to_list(50)


@router.get("/public/help-topics")
async def list_help_topics_for_public():
    """List public help topics for anonymous ticket creation"""
    return await _db.ticketing_help_topics.find(
        {"is_deleted": {"$ne": True}, "is_active": True, "is_public": True, "company_id": None},
        {"_id": 0, "id": 1, "name": 1, "description": 1, "icon": 1, "custom_form_id": 1}
    ).sort("sort_order", 1).to_list(50)


# ==================== CUSTOM FORMS ====================

@router.get("/admin/custom-forms")
async def list_custom_forms(admin: dict = Depends(get_current_admin)):
    """List all custom forms"""
    forms = await _db.ticketing_custom_forms.find({"is_deleted": {"$ne": True}}, {"_id": 0}).sort("name", 1).to_list(100)
    return forms


@router.post("/admin/custom-forms")
async def create_custom_form(data: CustomFormCreate, admin: dict = Depends(get_current_admin)):
    """Create a new custom form"""
    # Process fields to add IDs if missing
    fields = []
    for i, field_data in enumerate(data.fields):
        field = CustomFormField(
            id=field_data.get("id", str(uuid.uuid4())),
            name=field_data.get("name", f"field_{i}"),
            label=field_data.get("label", f"Field {i}"),
            field_type=field_data.get("field_type", "text"),
            options=field_data.get("options", []),
            required=field_data.get("required", False),
            placeholder=field_data.get("placeholder"),
            help_text=field_data.get("help_text"),
            default_value=field_data.get("default_value"),
            width=field_data.get("width", "full"),
            visible_to_customer=field_data.get("visible_to_customer", True),
            editable_by_customer=field_data.get("editable_by_customer", True),
            sort_order=field_data.get("sort_order", i)
        )
        fields.append(field.model_dump())
    
    form = CustomForm(
        name=data.name,
        description=data.description,
        fields=fields,
        created_by=admin.get("id")
    )
    await _db.ticketing_custom_forms.insert_one(form.model_dump())
    await _log_audit("custom_form", form.id, "create", {"name": data.name}, admin)
    return form.model_dump()


@router.get("/admin/custom-forms/{form_id}")
async def get_custom_form(form_id: str, admin: dict = Depends(get_current_admin)):
    """Get custom form by ID"""
    form = await _db.ticketing_custom_forms.find_one({"id": form_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Custom form not found")
    return form


@router.put("/admin/custom-forms/{form_id}")
async def update_custom_form(form_id: str, updates: CustomFormUpdate, admin: dict = Depends(get_current_admin)):
    """Update a custom form - increments version if fields change"""
    form = await _db.ticketing_custom_forms.find_one({"id": form_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Custom form not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    # If fields are being updated, increment version
    if "fields" in update_data:
        update_data["version"] = form.get("version", 1) + 1
        # Process fields
        fields = []
        for i, field_data in enumerate(update_data["fields"]):
            field = CustomFormField(
                id=field_data.get("id", str(uuid.uuid4())),
                name=field_data.get("name", f"field_{i}"),
                label=field_data.get("label", f"Field {i}"),
                field_type=field_data.get("field_type", "text"),
                options=field_data.get("options", []),
                required=field_data.get("required", False),
                placeholder=field_data.get("placeholder"),
                help_text=field_data.get("help_text"),
                default_value=field_data.get("default_value"),
                width=field_data.get("width", "full"),
                visible_to_customer=field_data.get("visible_to_customer", True),
                editable_by_customer=field_data.get("editable_by_customer", True),
                sort_order=field_data.get("sort_order", i)
            )
            fields.append(field.model_dump())
        update_data["fields"] = fields
    
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.ticketing_custom_forms.update_one({"id": form_id}, {"$set": update_data})
    await _log_audit("custom_form", form_id, "update", update_data, admin)
    return await _db.ticketing_custom_forms.find_one({"id": form_id}, {"_id": 0})


@router.delete("/admin/custom-forms/{form_id}")
async def delete_custom_form(form_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a custom form"""
    form = await _db.ticketing_custom_forms.find_one({"id": form_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Custom form not found")
    
    # Check if any help topics use this form
    topics_using = await _db.ticketing_help_topics.count_documents({"custom_form_id": form_id, "is_deleted": {"$ne": True}})
    if topics_using > 0:
        raise HTTPException(status_code=400, detail=f"Cannot delete form - {topics_using} help topics are using it")
    
    await _db.ticketing_custom_forms.update_one({"id": form_id}, {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}})
    return {"message": "Custom form deleted"}


@router.get("/portal/custom-forms/{form_id}")
async def get_custom_form_public(form_id: str, user: dict = Depends(get_current_company_user)):
    """Get custom form for ticket creation (customer view)"""
    form = await _db.ticketing_custom_forms.find_one({"id": form_id, "is_deleted": {"$ne": True}, "is_active": True}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Custom form not found")
    
    # Filter fields to only show customer-visible fields
    form["fields"] = [f for f in form.get("fields", []) if f.get("visible_to_customer", True)]
    return form


@router.get("/public/custom-forms/{form_id}")
async def get_custom_form_for_public(form_id: str):
    """Get custom form for anonymous ticket creation"""
    form = await _db.ticketing_custom_forms.find_one({"id": form_id, "is_deleted": {"$ne": True}, "is_active": True}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Custom form not found")
    
    # Filter fields to only show customer-visible fields
    form["fields"] = [f for f in form.get("fields", []) if f.get("visible_to_customer", True)]
    return form


# ==================== CANNED RESPONSES ====================

@router.get("/admin/canned-responses")
async def list_canned_responses(
    department_id: Optional[str] = None,
    category: Optional[str] = None,
    search: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List canned responses - includes personal + shared"""
    query = {"is_deleted": {"$ne": True}, "is_active": True}
    
    # Show personal responses only to creator, shared responses to everyone
    query["$or"] = [
        {"is_personal": False},
        {"is_personal": True, "created_by": admin.get("id")}
    ]
    
    if department_id:
        query["$and"] = query.get("$and", [])
        query["$and"].append({"$or": [{"department_id": department_id}, {"department_id": None}]})
    if category:
        query["category"] = category
    if search:
        query["$and"] = query.get("$and", [])
        query["$and"].append({"$or": [
            {"title": {"$regex": search, "$options": "i"}},
            {"content": {"$regex": search, "$options": "i"}}
        ]})
    
    responses = await _db.ticketing_canned_responses.find(query, {"_id": 0}).sort([("usage_count", -1), ("title", 1)]).to_list(100)
    return responses


@router.post("/admin/canned-responses")
async def create_canned_response(data: CannedResponseCreate, admin: dict = Depends(get_current_admin)):
    """Create a canned response"""
    response = CannedResponse(**data.model_dump(), created_by=admin.get("id"))
    await _db.ticketing_canned_responses.insert_one(response.model_dump())
    await _log_audit("canned_response", response.id, "create", {"title": data.title}, admin)
    return response.model_dump()


@router.get("/admin/canned-responses/{response_id}")
async def get_canned_response(response_id: str, admin: dict = Depends(get_current_admin)):
    """Get canned response by ID"""
    response = await _db.ticketing_canned_responses.find_one({"id": response_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not response:
        raise HTTPException(status_code=404, detail="Canned response not found")
    
    # Check permission for personal responses
    if response.get("is_personal") and response.get("created_by") != admin.get("id"):
        raise HTTPException(status_code=403, detail="Cannot access this personal response")
    
    return response


@router.put("/admin/canned-responses/{response_id}")
async def update_canned_response(response_id: str, updates: CannedResponseUpdate, admin: dict = Depends(get_current_admin)):
    """Update a canned response"""
    response = await _db.ticketing_canned_responses.find_one({"id": response_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not response:
        raise HTTPException(status_code=404, detail="Canned response not found")
    
    # Check permission
    if response.get("is_personal") and response.get("created_by") != admin.get("id"):
        raise HTTPException(status_code=403, detail="Cannot edit this personal response")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.ticketing_canned_responses.update_one({"id": response_id}, {"$set": update_data})
    return await _db.ticketing_canned_responses.find_one({"id": response_id}, {"_id": 0})


@router.delete("/admin/canned-responses/{response_id}")
async def delete_canned_response(response_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a canned response"""
    response = await _db.ticketing_canned_responses.find_one({"id": response_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not response:
        raise HTTPException(status_code=404, detail="Canned response not found")
    
    # Check permission
    if response.get("is_personal") and response.get("created_by") != admin.get("id"):
        raise HTTPException(status_code=403, detail="Cannot delete this personal response")
    
    await _db.ticketing_canned_responses.update_one({"id": response_id}, {"$set": {"is_deleted": True}})
    return {"message": "Canned response deleted"}


@router.post("/admin/canned-responses/{response_id}/use")
async def use_canned_response(response_id: str, ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Apply a canned response to a ticket - returns processed content with variables replaced"""
    response = await _db.ticketing_canned_responses.find_one({"id": response_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not response:
        raise HTTPException(status_code=404, detail="Canned response not found")
    
    ticket = await _db.tickets.find_one({"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Get related data for variable replacement
    department = None
    if ticket.get("department_id"):
        department = await _db.ticketing_departments.find_one({"id": ticket["department_id"]}, {"_id": 0})
    
    # Replace variables in content
    content = response.get("content", "")
    variables = {
        "{{customer_name}}": ticket.get("requester_name", "Customer"),
        "{{ticket_id}}": ticket.get("id", ""),
        "{{ticket_number}}": ticket.get("ticket_number", ""),
        "{{subject}}": ticket.get("subject", ""),
        "{{department_name}}": department.get("name", "Support") if department else "Support",
        "{{assigned_to}}": ticket.get("assigned_to_name", "Our team"),
        "{{sla_due}}": ticket.get("sla_status", {}).get("resolution_due_at", "N/A") if ticket.get("sla_status") else "N/A"
    }
    
    for var, value in variables.items():
        content = content.replace(var, str(value))
    
    # Update usage stats
    await _db.ticketing_canned_responses.update_one(
        {"id": response_id},
        {"$inc": {"usage_count": 1}, "$set": {"last_used_at": get_ist_isoformat()}}
    )
    
    return {"content": content, "original_content": response.get("content")}


# ==================== TICKET PARTICIPANTS (CC/Collaboration) ====================

@router.get("/admin/tickets/{ticket_id}/participants")
async def list_ticket_participants(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """List all participants on a ticket"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    participants = await _db.ticket_participants.find(
        {"ticket_id": ticket_id, "is_active": True},
        {"_id": 0}
    ).sort("added_at", 1).to_list(50)
    
    return participants


@router.post("/admin/tickets/{ticket_id}/participants")
async def add_ticket_participant(ticket_id: str, data: AddParticipantRequest, admin: dict = Depends(get_current_admin)):
    """Add a participant (CC) to a ticket"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check if participant already exists
    existing = await _db.ticket_participants.find_one({
        "ticket_id": ticket_id,
        "email": {"$regex": f"^{re.escape(data.email)}$", "$options": "i"},
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="Participant already added to this ticket")
    
    # Check if this is an internal user
    internal_user = await _db.company_users.find_one(
        {"email": {"$regex": f"^{re.escape(data.email)}$", "$options": "i"}, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    participant = TicketParticipant(
        ticket_id=ticket_id,
        user_id=internal_user.get("id") if internal_user else None,
        name=data.name,
        email=data.email,
        phone=data.phone,
        participant_type=data.participant_type,
        is_external=internal_user is None,
        can_reply=data.can_reply,
        added_by=admin.get("id"),
        added_by_name=admin.get("name", "Admin")
    )
    
    await _db.ticket_participants.insert_one(participant.model_dump())
    
    # Update ticket participant count
    await _db.tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"participant_ids": participant.id},
            "$inc": {"participant_count": 1},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    # Log event
    await create_thread_entry(
        ticket_id, "system_event", admin.get("id"), admin.get("name"), "admin",
        event_type="participant_added",
        event_data={"name": data.name, "email": data.email, "type": data.participant_type}
    )
    
    return participant.model_dump()


@router.delete("/admin/tickets/{ticket_id}/participants/{participant_id}")
async def remove_ticket_participant(ticket_id: str, participant_id: str, admin: dict = Depends(get_current_admin)):
    """Remove a participant from a ticket"""
    participant = await _db.ticket_participants.find_one(
        {"id": participant_id, "ticket_id": ticket_id, "is_active": True},
        {"_id": 0}
    )
    if not participant:
        raise HTTPException(status_code=404, detail="Participant not found")
    
    await _db.ticket_participants.update_one(
        {"id": participant_id},
        {"$set": {"is_active": False, "removed_at": get_ist_isoformat()}}
    )
    
    # Update ticket
    await _db.tickets.update_one(
        {"id": ticket_id},
        {
            "$pull": {"participant_ids": participant_id},
            "$inc": {"participant_count": -1},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    # Log event
    await create_thread_entry(
        ticket_id, "system_event", admin.get("id"), admin.get("name"), "admin",
        event_type="participant_removed",
        event_data={"name": participant.get("name"), "email": participant.get("email")}
    )
    
    return {"message": "Participant removed"}


@router.post("/portal/tickets/{ticket_id}/participants")
async def add_ticket_participant_customer(ticket_id: str, data: AddParticipantRequest, user: dict = Depends(get_current_company_user)):
    """Add a participant (CC) to own ticket - customer portal"""
    ticket = await _db.tickets.find_one({
        "id": ticket_id,
        "requester_id": user.get("id"),
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Check if participant already exists
    existing = await _db.ticket_participants.find_one({
        "ticket_id": ticket_id,
        "email": {"$regex": f"^{re.escape(data.email)}$", "$options": "i"},
        "is_active": True
    })
    if existing:
        raise HTTPException(status_code=400, detail="Participant already added")
    
    participant = TicketParticipant(
        ticket_id=ticket_id,
        name=data.name,
        email=data.email,
        phone=data.phone,
        participant_type="cc",
        is_external=True,  # Customers can only add external participants
        can_reply=True,
        can_view_internal_notes=False,
        added_by=user.get("id"),
        added_by_name=user.get("name", "Customer")
    )
    
    await _db.ticket_participants.insert_one(participant.model_dump())
    
    # Update ticket
    await _db.tickets.update_one(
        {"id": ticket_id},
        {
            "$push": {"participant_ids": participant.id},
            "$inc": {"participant_count": 1},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    # Log event
    await create_thread_entry(
        ticket_id, "system_event", user.get("id"), user.get("name"), "customer",
        event_type="participant_added",
        event_data={"name": data.name, "email": data.email}
    )
    
    return participant.model_dump()


# ==================== TICKETS - ADMIN ====================

@router.get("/admin/tickets")
async def list_tickets_admin(
    status: Optional[str] = None, priority: Optional[str] = None, department_id: Optional[str] = None,
    help_topic_id: Optional[str] = None, assigned_to: Optional[str] = None, company_id: Optional[str] = None,
    unassigned: bool = False, search: Optional[str] = None, limit: int = Query(50, le=200), skip: int = 0,
    admin: dict = Depends(get_current_admin)
):
    """List tickets with filters (admin view)"""
    query = {"is_deleted": {"$ne": True}}
    if status: query["status"] = status
    if priority: query["priority"] = priority
    if department_id: query["department_id"] = department_id
    if help_topic_id: query["help_topic_id"] = help_topic_id
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
    """Create a ticket on behalf of a customer (admin) with Help Topic auto-routing"""
    requester = await _db.company_users.find_one({"id": requester_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not requester:
        raise HTTPException(status_code=404, detail="Requester not found")
    
    # Help Topic auto-routing
    help_topic = None
    department_id = data.department_id
    priority = data.priority
    sla_id = None
    auto_assign_to = None
    
    if data.help_topic_id:
        help_topic = await _db.ticketing_help_topics.find_one({"id": data.help_topic_id, "is_deleted": {"$ne": True}}, {"_id": 0})
        if help_topic:
            # Apply auto-routing from help topic
            if not department_id and help_topic.get("auto_department_id"):
                department_id = help_topic["auto_department_id"]
            if help_topic.get("auto_priority"):
                priority = help_topic["auto_priority"]
            if help_topic.get("auto_sla_id"):
                sla_id = help_topic["auto_sla_id"]
            if help_topic.get("auto_assign_to"):
                auto_assign_to = help_topic["auto_assign_to"]
    
    # Get SLA policy
    sla_policy = None
    if sla_id:
        sla_policy = await _db.ticketing_sla_policies.find_one({"id": sla_id}, {"_id": 0})
    elif department_id:
        dept = await _db.ticketing_departments.find_one({"id": department_id, "is_deleted": {"$ne": True}}, {"_id": 0})
        if dept and dept.get("default_sla_id"):
            sla_policy = await _db.ticketing_sla_policies.find_one({"id": dept["default_sla_id"]}, {"_id": 0})
    if not sla_policy:
        sla_policy = await _db.ticketing_sla_policies.find_one({"is_default": True, "is_deleted": {"$ne": True}}, {"_id": 0})
    
    sla_status = calculate_sla_due_times(sla_policy, priority) if sla_policy else None
    
    # Process custom form data if provided
    form_data_snapshot = None
    if data.form_data and data.help_topic_id:
        form = await _db.ticketing_custom_forms.find_one({"id": help_topic.get("custom_form_id") if help_topic else None}, {"_id": 0})
        if form:
            form_data_snapshot = {
                "form_id": form.get("id"),
                "form_name": form.get("name"),
                "form_version": form.get("version", 1),
                "fields": form.get("fields", []),
                "values": data.form_data,
                "submitted_at": get_ist_isoformat()
            }
    
    # Get assignee name if auto-assigned
    assigned_to_name = None
    if auto_assign_to:
        assignee = await _db.admin_users.find_one({"id": auto_assign_to}, {"name": 1})
        assigned_to_name = assignee.get("name") if assignee else None
    
    ticket_data = data.model_dump()
    ticket_data.pop("participants", None)  # Handle separately
    ticket_data.pop("form_data", None)  # Already processed
    ticket_data.pop("department_id", None)  # Override with auto-routed value
    ticket_data.pop("priority", None)  # Override with auto-routed value
    
    ticket = Ticket(
        **ticket_data,
        company_id=requester.get("company_id"),
        requester_id=requester_id,
        requester_name=requester.get("name", "Unknown"),
        requester_email=requester.get("email", ""),
        requester_phone=requester.get("phone"),
        department_id=department_id,
        priority=priority,
        assigned_to=auto_assign_to,
        assigned_to_name=assigned_to_name,
        assigned_at=get_ist_isoformat() if auto_assign_to else None,
        sla_status=sla_status,
        form_data=form_data_snapshot,
        created_by=admin.get("id"),
        created_by_type="staff"
    )
    
    priority_order = {"critical": 4, "high": 3, "medium": 2, "low": 1}
    ticket_dict = ticket.model_dump()
    ticket_dict["priority_order"] = priority_order.get(priority, 2)
    
    await _db.tickets.insert_one(ticket_dict)
    
    # Add initial participants if provided
    if data.participants:
        for p in data.participants:
            participant = TicketParticipant(
                ticket_id=ticket.id,
                name=p.get("name", ""),
                email=p.get("email", ""),
                phone=p.get("phone"),
                participant_type="cc",
                is_external=True,
                can_reply=True,
                added_by=admin.get("id"),
                added_by_name=admin.get("name", "Admin")
            )
            await _db.ticket_participants.insert_one(participant.model_dump())
            await _db.tickets.update_one(
                {"id": ticket.id},
                {"$push": {"participant_ids": participant.id}, "$inc": {"participant_count": 1}}
            )
    
    await create_thread_entry(ticket.id, "system_event", admin.get("id"), admin.get("name"), "admin", event_type="ticket_created", event_data={"created_by_staff": True, "help_topic": help_topic.get("name") if help_topic else None})
    await _log_audit("ticket", ticket.id, "create", data.model_dump(), admin)
    return await _db.tickets.find_one({"id": ticket.id}, {"_id": 0})


@router.get("/admin/tickets/{ticket_id}")
async def get_ticket_admin(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Get ticket details with thread, participants, and help topic"""
    ticket = await _db.tickets.find_one({"id": ticket_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    thread = await _db.ticket_thread.find({"ticket_id": ticket_id, "is_hidden": {"$ne": True}}, {"_id": 0}).sort("created_at", 1).to_list(500)
    
    department = None
    if ticket.get("department_id"):
        department = await _db.ticketing_departments.find_one({"id": ticket["department_id"]}, {"_id": 0, "name": 1, "id": 1})
    
    help_topic = None
    if ticket.get("help_topic_id"):
        help_topic = await _db.ticketing_help_topics.find_one({"id": ticket["help_topic_id"]}, {"_id": 0, "name": 1, "id": 1, "icon": 1})
    
    participants = await _db.ticket_participants.find(
        {"ticket_id": ticket_id, "is_active": True}, {"_id": 0}
    ).to_list(50)
    
    return {**ticket, "thread": thread, "department": department, "help_topic": help_topic, "participants": participants}


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
async def reply_to_ticket_admin(ticket_id: str, reply: TicketReplyCreate, background_tasks: BackgroundTasks, admin: dict = Depends(get_current_admin)):
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
        
        # Send email notification (non-internal replies only)
        from services.email_service import get_email_service
        email_service = get_email_service()
        if email_service and email_service.is_configured():
            async def send_notification():
                await email_service.send_ticket_notification(ticket, "reply_added", reply.content)
            background_tasks.add_task(send_notification)
    
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
    help_topic_id: Optional[str] = None
    department_id: Optional[str] = None
    priority: str = "medium"
    category: Optional[str] = None
    form_data: Optional[dict] = None
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
    """Create a ticket from the public portal (no authentication required) with Help Topic support"""
    # Validate email format
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    if not re.match(email_regex, data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    # Help Topic auto-routing
    help_topic = None
    department_id = data.department_id
    priority = data.priority
    sla_id = None
    auto_assign_to = None
    form_data_snapshot = None
    
    if data.help_topic_id:
        help_topic = await _db.ticketing_help_topics.find_one(
            {"id": data.help_topic_id, "is_deleted": {"$ne": True}, "is_public": True},
            {"_id": 0}
        )
        if help_topic:
            # Apply auto-routing from help topic
            if not department_id and help_topic.get("auto_department_id"):
                department_id = help_topic["auto_department_id"]
            if help_topic.get("auto_priority"):
                priority = help_topic["auto_priority"]
            if help_topic.get("auto_sla_id"):
                sla_id = help_topic["auto_sla_id"]
            if help_topic.get("auto_assign_to"):
                auto_assign_to = help_topic["auto_assign_to"]
            
            # Process custom form data if provided
            if data.form_data and help_topic.get("custom_form_id"):
                form = await _db.ticketing_custom_forms.find_one(
                    {"id": help_topic["custom_form_id"]},
                    {"_id": 0}
                )
                if form:
                    form_data_snapshot = {
                        "form_id": form.get("id"),
                        "form_name": form.get("name"),
                        "form_version": form.get("version", 1),
                        "fields": form.get("fields", []),
                        "values": data.form_data,
                        "submitted_at": get_ist_isoformat()
                    }
    
    # Get SLA policy
    sla_policy = None
    if sla_id:
        sla_policy = await _db.ticketing_sla_policies.find_one({"id": sla_id}, {"_id": 0})
    elif department_id:
        dept = await _db.ticketing_departments.find_one(
            {"id": department_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
        if dept and dept.get("default_sla_id"):
            sla_policy = await _db.ticketing_sla_policies.find_one({"id": dept["default_sla_id"]}, {"_id": 0})
    
    if not sla_policy:
        sla_policy = await _db.ticketing_sla_policies.find_one(
            {"is_default": True, "is_deleted": {"$ne": True}}, {"_id": 0}
        )
    
    sla_status = calculate_sla_due_times(sla_policy, priority) if sla_policy else None
    
    # Get assignee name if auto-assigned
    assigned_to_name = None
    if auto_assign_to:
        assignee = await _db.admin_users.find_one({"id": auto_assign_to}, {"name": 1})
        assigned_to_name = assignee.get("name") if assignee else None
    
    # Create ticket
    ticket_id = str(uuid.uuid4())
    ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    ticket = {
        "id": ticket_id,
        "ticket_number": ticket_number,
        "company_id": "PUBLIC",
        "source": "portal",
        "help_topic_id": data.help_topic_id,
        "department_id": department_id,
        "subject": data.subject,
        "description": data.description,
        "status": "open",
        "priority": priority,
        "priority_order": {"critical": 4, "high": 3, "medium": 2, "low": 1}.get(priority, 2),
        "requester_id": "public",
        "requester_name": data.name,
        "requester_email": data.email,
        "requester_phone": data.phone,
        "assigned_to": auto_assign_to,
        "assigned_to_name": assigned_to_name,
        "assigned_at": get_ist_isoformat() if auto_assign_to else None,
        "watchers": [],
        "sla_status": sla_status,
        "tags": [],
        "category": data.category,
        "form_data": form_data_snapshot,
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
        event_type="ticket_created", event_data={"source": "public_portal", "help_topic": help_topic.get("name") if help_topic else None},
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





# ==================== EMAIL INTEGRATION ====================

class EmailConfigUpdate(BaseModel):
    """Update email configuration"""
    smtp_host: Optional[str] = None
    smtp_port: Optional[int] = None
    imap_host: Optional[str] = None
    imap_port: Optional[int] = None
    email_user: Optional[str] = None
    email_password: Optional[str] = None
    email_from_name: Optional[str] = None
    email_reply_to: Optional[str] = None


@router.get("/admin/email/status")
async def get_email_status(admin: dict = Depends(get_current_admin)):
    """Get email integration status"""
    import os
    
    email_user = os.environ.get("EMAIL_USER", "")
    is_configured = bool(email_user and os.environ.get("EMAIL_PASSWORD"))
    
    return {
        "is_configured": is_configured,
        "email_user": email_user if is_configured else None,
        "smtp_host": os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        "smtp_port": int(os.environ.get("SMTP_PORT", "587")),
        "imap_host": os.environ.get("IMAP_HOST", "imap.gmail.com"),
        "imap_port": int(os.environ.get("IMAP_PORT", "993")),
        "email_from_name": os.environ.get("EMAIL_FROM_NAME", "Support Team")
    }


@router.post("/admin/email/test")
async def test_email_connection(admin: dict = Depends(get_current_admin)):
    """Test email SMTP and IMAP connections"""
    from services.email_service import get_email_service
    
    email_service = get_email_service()
    if not email_service or not email_service.is_configured():
        raise HTTPException(status_code=400, detail="Email not configured. Set EMAIL_USER and EMAIL_PASSWORD environment variables.")
    
    results = {"smtp": False, "imap": False, "errors": []}
    
    # Test SMTP
    try:
        smtp_conn = email_service._create_smtp_connection()
        if smtp_conn:
            smtp_conn.quit()
            results["smtp"] = True
        else:
            results["errors"].append("SMTP connection failed")
    except Exception as e:
        results["errors"].append(f"SMTP error: {str(e)}")
    
    # Test IMAP
    try:
        imap_conn = email_service._create_imap_connection()
        if imap_conn:
            imap_conn.logout()
            results["imap"] = True
        else:
            results["errors"].append("IMAP connection failed")
    except Exception as e:
        results["errors"].append(f"IMAP error: {str(e)}")
    
    return results


@router.post("/admin/email/sync")
async def sync_emails_manual(background_tasks: BackgroundTasks, admin: dict = Depends(get_current_admin)):
    """Manually trigger email sync to fetch and process new emails"""
    from services.email_service import get_email_service
    
    email_service = get_email_service()
    if not email_service or not email_service.is_configured():
        raise HTTPException(status_code=400, detail="Email not configured")
    
    # Run sync in background
    async def do_sync():
        return await email_service.sync_emails()
    
    # For manual sync, run synchronously to return results
    stats = await email_service.sync_emails()
    
    return {
        "message": "Email sync completed",
        "stats": stats
    }


@router.post("/admin/email/send-test")
async def send_test_email(to_email: str = Query(...), admin: dict = Depends(get_current_admin)):
    """Send a test email to verify SMTP configuration"""
    from services.email_service import get_email_service
    
    email_service = get_email_service()
    if not email_service or not email_service.is_configured():
        raise HTTPException(status_code=400, detail="Email not configured")
    
    success = await email_service.send_email(
        to_email,
        "Test Email from Support Portal",
        """
        <p>Hello,</p>
        <p>This is a test email to verify that the email integration is working correctly.</p>
        <p>If you received this email, the SMTP configuration is working.</p>
        <div class="ticket-info">
            <p><strong>Test Status:</strong> Success</p>
            <p><strong>Sent At:</strong> """ + get_ist_isoformat() + """</p>
        </div>
        <p>Best regards,<br>Support Portal</p>
        """
    )
    
    if success:
        return {"message": f"Test email sent to {to_email}"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send test email")

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
