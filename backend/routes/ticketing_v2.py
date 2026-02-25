"""
Ticketing System v2 - API Routes
================================
Complete API for the new workflow-driven ticketing system.
"""

import uuid
import random
import string
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, List, Dict, Any
from pydantic import BaseModel

from models.ticketing_v2 import (
    HelpTopic, TicketForm, TicketWorkflow, WorkflowStage,
    SLAPolicy, TicketPriority, TicketTeam, TicketRole, TaskType,
    CannedResponse, NotificationTemplate, BusinessHours,
    TicketV2, TicketTask, TicketCreateV2, TicketUpdateV2,
    TicketTimelineEntry, TicketContact, StageTransitionRequest
)
from models.ticketing_v2_seed import generate_seed_data
from routes.service_tickets_new import get_current_admin

router = APIRouter()

# Database will be injected
_db = None

def init_db(database):
    global _db
    _db = database


def get_ist_isoformat():
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).isoformat()


async def generate_ticket_number(db, org_id: str) -> str:
    """Generate unique 6-char ticket number"""
    while True:
        number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        exists = await db.tickets_v2.find_one({
            "organization_id": org_id,
            "ticket_number": number
        })
        if not exists:
            return number


# ============================================================
# SEED DATA
# ============================================================

@router.post("/ticketing/seed")
async def seed_ticketing_system(admin: dict = Depends(get_current_admin)):
    """Seed all ticketing system data for the organization"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check if already seeded
    existing = await _db.ticket_help_topics.count_documents({"organization_id": org_id})
    if existing > 0:
        return {"message": f"Ticketing system already seeded ({existing} help topics found)", "seeded": False}
    
    # Generate seed data
    data = generate_seed_data(org_id)
    
    # Insert all data
    counts = {}
    
    if data["priorities"]:
        await _db.ticket_priorities.insert_many(data["priorities"])
        counts["priorities"] = len(data["priorities"])
    
    if data["business_hours"]:
        await _db.ticket_business_hours.insert_many(data["business_hours"])
        counts["business_hours"] = len(data["business_hours"])
    
    if data["sla_policies"]:
        await _db.ticket_sla_policies.insert_many(data["sla_policies"])
        counts["sla_policies"] = len(data["sla_policies"])
    
    if data["roles"]:
        await _db.ticket_roles.insert_many(data["roles"])
        counts["roles"] = len(data["roles"])
    
    if data["teams"]:
        await _db.ticket_teams.insert_many(data["teams"])
        counts["teams"] = len(data["teams"])
    
    if data["task_types"]:
        await _db.ticket_task_types.insert_many(data["task_types"])
        counts["task_types"] = len(data["task_types"])
    
    if data["forms"]:
        await _db.ticket_forms.insert_many(data["forms"])
        counts["forms"] = len(data["forms"])
    
    if data["workflows"]:
        await _db.ticket_workflows.insert_many(data["workflows"])
        counts["workflows"] = len(data["workflows"])
    
    if data["help_topics"]:
        await _db.ticket_help_topics.insert_many(data["help_topics"])
        counts["help_topics"] = len(data["help_topics"])
    
    if data["canned_responses"]:
        await _db.ticket_canned_responses.insert_many(data["canned_responses"])
        counts["canned_responses"] = len(data["canned_responses"])
    
    if data["notification_templates"]:
        await _db.ticket_notification_templates.insert_many(data["notification_templates"])
        counts["notification_templates"] = len(data["notification_templates"])
    
    return {
        "message": "Ticketing system seeded successfully",
        "seeded": True,
        "counts": counts
    }


# ============================================================
# HELP TOPICS
# ============================================================

@router.get("/ticketing/help-topics")
async def list_help_topics(
    category: Optional[str] = None,
    include_inactive: bool = False,
    admin: dict = Depends(get_current_admin)
):
    """List all help topics"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id}
    if not include_inactive:
        query["is_active"] = True
    if category:
        query["category"] = category
    
    topics = await _db.ticket_help_topics.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    return topics


@router.get("/ticketing/help-topics/{topic_id}")
async def get_help_topic(topic_id: str, admin: dict = Depends(get_current_admin)):
    """Get a single help topic with linked form and workflow"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    topic = await _db.ticket_help_topics.find_one(
        {"id": topic_id, "organization_id": org_id},
        {"_id": 0}
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    # Fetch linked form
    if topic.get("form_id"):
        form = await _db.ticket_forms.find_one({"id": topic["form_id"]}, {"_id": 0})
        topic["form"] = form
    
    # Fetch linked workflow
    if topic.get("workflow_id"):
        workflow = await _db.ticket_workflows.find_one({"id": topic["workflow_id"]}, {"_id": 0})
        topic["workflow"] = workflow
    
    return topic


@router.post("/ticketing/help-topics")
async def create_help_topic(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Create a new help topic"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    topic = HelpTopic(
        organization_id=org_id,
        **data
    )
    
    await _db.ticket_help_topics.insert_one(topic.model_dump())
    return topic.model_dump()


@router.put("/ticketing/help-topics/{topic_id}")
async def update_help_topic(topic_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Update a help topic"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    data["updated_at"] = get_ist_isoformat()
    
    result = await _db.ticket_help_topics.update_one(
        {"id": topic_id, "organization_id": org_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    return await _db.ticket_help_topics.find_one({"id": topic_id}, {"_id": 0})


@router.delete("/ticketing/help-topics/{topic_id}")
async def delete_help_topic(topic_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a help topic"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    topic = await _db.ticket_help_topics.find_one({"id": topic_id, "organization_id": org_id})
    if not topic:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    if topic.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot delete system help topic")
    
    await _db.ticket_help_topics.delete_one({"id": topic_id})
    return {"message": "Help topic deleted"}


# ============================================================
# FORMS
# ============================================================

@router.get("/ticketing/forms")
async def list_forms(admin: dict = Depends(get_current_admin)):
    """List all forms"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    forms = await _db.ticket_forms.find(
        {"organization_id": org_id, "is_active": True},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    return forms


@router.get("/ticketing/forms/{form_id}")
async def get_form(form_id: str, admin: dict = Depends(get_current_admin)):
    """Get a single form"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    form = await _db.ticket_forms.find_one({"id": form_id, "organization_id": org_id}, {"_id": 0})
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    return form


@router.put("/ticketing/forms/{form_id}")
async def update_form(form_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Update a form"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    data["updated_at"] = get_ist_isoformat()
    
    result = await _db.ticket_forms.update_one(
        {"id": form_id, "organization_id": org_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return await _db.ticket_forms.find_one({"id": form_id}, {"_id": 0})


# ============================================================
# WORKFLOWS
# ============================================================

@router.get("/ticketing/workflows")
async def list_workflows(admin: dict = Depends(get_current_admin)):
    """List all workflows"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    workflows = await _db.ticket_workflows.find(
        {"organization_id": org_id, "is_active": True},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    return workflows


@router.get("/ticketing/workflows/{workflow_id}")
async def get_workflow(workflow_id: str, admin: dict = Depends(get_current_admin)):
    """Get a single workflow"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    workflow = await _db.ticket_workflows.find_one({"id": workflow_id, "organization_id": org_id}, {"_id": 0})
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/ticketing/workflows/{workflow_id}")
async def update_workflow(workflow_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Update a workflow"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    data["updated_at"] = get_ist_isoformat()
    
    result = await _db.ticket_workflows.update_one(
        {"id": workflow_id, "organization_id": org_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    return await _db.ticket_workflows.find_one({"id": workflow_id}, {"_id": 0})


# ============================================================
# TEAMS
# ============================================================

@router.get("/ticketing/teams")
async def list_teams(admin: dict = Depends(get_current_admin)):
    """List all teams"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    teams = await _db.ticket_teams.find(
        {"organization_id": org_id, "is_active": True},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    return teams


@router.get("/ticketing/teams/{team_id}")
async def get_team(team_id: str, admin: dict = Depends(get_current_admin)):
    """Get a single team"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    team = await _db.ticket_teams.find_one({"id": team_id, "organization_id": org_id}, {"_id": 0})
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    return team


@router.put("/ticketing/teams/{team_id}")
async def update_team(team_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Update a team"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    result = await _db.ticket_teams.update_one(
        {"id": team_id, "organization_id": org_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return await _db.ticket_teams.find_one({"id": team_id}, {"_id": 0})


@router.post("/ticketing/teams/{team_id}/members")
async def add_team_member(team_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Add a member to a team"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    member = {
        "user_id": data.get("user_id"),
        "user_name": data.get("user_name"),
        "user_email": data.get("user_email"),
        "role_id": data.get("role_id"),
        "is_manager": data.get("is_manager", False),
        "added_at": get_ist_isoformat()
    }
    
    result = await _db.ticket_teams.update_one(
        {"id": team_id, "organization_id": org_id},
        {"$push": {"members": member}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Team not found")
    
    return await _db.ticket_teams.find_one({"id": team_id}, {"_id": 0})


# ============================================================
# ROLES
# ============================================================

@router.get("/ticketing/roles")
async def list_roles(admin: dict = Depends(get_current_admin)):
    """List all roles"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    roles = await _db.ticket_roles.find(
        {"organization_id": org_id, "is_active": True},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    return roles


# ============================================================
# TASK TYPES
# ============================================================

@router.get("/ticketing/task-types")
async def list_task_types(admin: dict = Depends(get_current_admin)):
    """List all task types"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    task_types = await _db.ticket_task_types.find(
        {"organization_id": org_id, "is_active": True},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    return task_types


# ============================================================
# SLA POLICIES
# ============================================================

@router.get("/ticketing/sla-policies")
async def list_sla_policies(admin: dict = Depends(get_current_admin)):
    """List all SLA policies"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    policies = await _db.ticket_sla_policies.find(
        {"organization_id": org_id, "is_active": True},
        {"_id": 0}
    ).sort("name", 1).to_list(100)
    return policies


# ============================================================
# PRIORITIES
# ============================================================

@router.get("/ticketing/priorities")
async def list_priorities(admin: dict = Depends(get_current_admin)):
    """List all priorities"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    priorities = await _db.ticket_priorities.find(
        {"organization_id": org_id, "is_active": True},
        {"_id": 0}
    ).sort("order", 1).to_list(100)
    return priorities


# ============================================================
# CANNED RESPONSES
# ============================================================

@router.get("/ticketing/canned-responses")
async def list_canned_responses(
    category: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all canned responses"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_active": True}
    if category:
        query["category"] = category
    
    responses = await _db.ticket_canned_responses.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    return responses


# ============================================================
# TICKETS (NEW)
# ============================================================

@router.get("/ticketing/tickets")
async def list_tickets(
    status: Optional[str] = None,
    help_topic_id: Optional[str] = None,
    priority: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    assigned_team_id: Optional[str] = None,
    is_open: Optional[bool] = None,
    search: Optional[str] = None,
    page: int = 1,
    limit: int = 20,
    admin: dict = Depends(get_current_admin)
):
    """List tickets with filtering"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if help_topic_id:
        query["help_topic_id"] = help_topic_id
    if priority:
        query["priority_name"] = priority
    if assigned_to_id:
        query["assigned_to_id"] = assigned_to_id
    if assigned_team_id:
        query["assigned_team_id"] = assigned_team_id
    if is_open is not None:
        query["is_open"] = is_open
    if search:
        query["$or"] = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"subject": {"$regex": search, "$options": "i"}}
        ]
    
    skip = (page - 1) * limit
    
    tickets = await _db.tickets_v2.find(query, {"_id": 0, "timeline": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await _db.tickets_v2.count_documents(query)
    
    return {
        "tickets": tickets,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.get("/ticketing/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Get a single ticket with full details"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    # Fetch help topic details
    if ticket.get("help_topic_id"):
        topic = await _db.ticket_help_topics.find_one({"id": ticket["help_topic_id"]}, {"_id": 0})
        ticket["help_topic"] = topic
        
        # Fetch form
        if topic and topic.get("form_id"):
            form = await _db.ticket_forms.find_one({"id": topic["form_id"]}, {"_id": 0})
            ticket["form"] = form
        
        # Fetch workflow
        if topic and topic.get("workflow_id"):
            workflow = await _db.ticket_workflows.find_one({"id": topic["workflow_id"]}, {"_id": 0})
            ticket["workflow"] = workflow
    
    # Fetch tasks
    tasks = await _db.ticket_tasks.find(
        {"ticket_id": ticket_id},
        {"_id": 0}
    ).sort("created_at", 1).to_list(100)
    ticket["tasks"] = tasks
    
    return ticket


@router.post("/ticketing/tickets")
async def create_ticket(data: TicketCreateV2, admin: dict = Depends(get_current_admin)):
    """Create a new ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Get help topic
    topic = await _db.ticket_help_topics.find_one(
        {"id": data.help_topic_id, "organization_id": org_id, "is_active": True},
        {"_id": 0}
    )
    if not topic:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    # Generate ticket number
    ticket_number = await generate_ticket_number(_db, org_id)
    
    # Get initial stage from workflow
    current_stage_id = None
    current_stage_name = "New"
    if topic.get("workflow_id"):
        workflow = await _db.ticket_workflows.find_one({"id": topic["workflow_id"]}, {"_id": 0})
        if workflow and workflow.get("stages"):
            for stage in workflow["stages"]:
                if stage.get("stage_type") == "initial":
                    current_stage_id = stage["id"]
                    current_stage_name = stage["name"]
                    break
    
    # Get company name if provided
    company_name = None
    if data.company_id:
        company = await _db.companies.find_one({"id": data.company_id}, {"_id": 0, "name": 1})
        if company:
            company_name = company["name"]
    
    # Get device name if provided
    device_name = None
    if data.device_id:
        device = await _db.devices.find_one({"id": data.device_id}, {"_id": 0, "name": 1, "display_name": 1})
        if device:
            device_name = device.get("display_name") or device.get("name")
    
    # Get priority name
    priority_name = "medium"
    if data.priority_id:
        priority = await _db.ticket_priorities.find_one({"id": data.priority_id}, {"_id": 0, "name": 1})
        if priority:
            priority_name = priority["name"].lower()
    else:
        priority_name = topic.get("default_priority", "medium")
    
    # Build contact
    contact = None
    if data.contact_name or data.contact_email or data.contact_phone:
        contact = {
            "name": data.contact_name or "",
            "email": data.contact_email,
            "phone": data.contact_phone
        }
    
    # Create ticket
    ticket = TicketV2(
        organization_id=org_id,
        ticket_number=ticket_number,
        help_topic_id=data.help_topic_id,
        help_topic_name=topic["name"],
        workflow_id=topic.get("workflow_id"),
        current_stage_id=current_stage_id,
        current_stage_name=current_stage_name,
        subject=data.subject,
        description=data.description,
        form_values=data.form_values,
        company_id=data.company_id,
        company_name=company_name,
        contact=contact,
        device_id=data.device_id,
        device_name=device_name,
        priority_name=priority_name,
        assigned_team_id=topic.get("default_team_id"),
        source=data.source,
        created_by_id=admin.get("id"),
        created_by_name=admin.get("name")
    )
    
    # Get team name
    if ticket.assigned_team_id:
        team = await _db.ticket_teams.find_one({"id": ticket.assigned_team_id}, {"_id": 0, "name": 1})
        if team:
            ticket.assigned_team_name = team["name"]
    
    # Add initial timeline entry
    ticket.timeline = [{
        "id": str(uuid.uuid4()),
        "type": "ticket_created",
        "description": f"Ticket created - {topic['name']}",
        "user_id": admin.get("id"),
        "user_name": admin.get("name"),
        "is_internal": False,
        "created_at": get_ist_isoformat()
    }]
    
    await _db.tickets_v2.insert_one(ticket.model_dump())
    
    # Update help topic ticket count
    await _db.ticket_help_topics.update_one(
        {"id": data.help_topic_id},
        {"$inc": {"ticket_count": 1}}
    )
    
    return ticket.model_dump()


@router.put("/ticketing/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, data: TicketUpdateV2, admin: dict = Depends(get_current_admin)):
    """Update a ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    result = await _db.tickets_v2.update_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return await _db.tickets_v2.find_one({"id": ticket_id}, {"_id": 0, "timeline": 0})


@router.post("/ticketing/tickets/{ticket_id}/assign")
async def assign_ticket(ticket_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Assign a ticket to a user or team"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    update_data = {"updated_at": get_ist_isoformat()}
    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "assignment",
        "user_id": admin.get("id"),
        "user_name": admin.get("name"),
        "is_internal": False,
        "created_at": get_ist_isoformat()
    }
    
    if data.get("assigned_to_id"):
        # Get user details
        user = await _db.organization_members.find_one({"id": data["assigned_to_id"]}, {"_id": 0, "name": 1, "email": 1})
        if user:
            update_data["assigned_to_id"] = data["assigned_to_id"]
            update_data["assigned_to_name"] = user.get("name", user.get("email", ""))
            timeline_entry["description"] = f"Assigned to {update_data['assigned_to_name']}"
    
    if data.get("assigned_team_id"):
        team = await _db.ticket_teams.find_one({"id": data["assigned_team_id"]}, {"_id": 0, "name": 1})
        if team:
            update_data["assigned_team_id"] = data["assigned_team_id"]
            update_data["assigned_team_name"] = team["name"]
            timeline_entry["description"] = f"Assigned to team: {team['name']}"
    
    await _db.tickets_v2.update_one(
        {"id": ticket_id},
        {
            "$set": update_data,
            "$push": {"timeline": timeline_entry}
        }
    )
    
    return await _db.tickets_v2.find_one({"id": ticket_id}, {"_id": 0, "timeline": 0})


@router.post("/ticketing/tickets/{ticket_id}/transition")
async def transition_ticket(ticket_id: str, data: StageTransitionRequest, admin: dict = Depends(get_current_admin)):
    """Transition a ticket to a new stage"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if not ticket.get("workflow_id"):
        raise HTTPException(status_code=400, detail="Ticket has no workflow")
    
    # Get workflow
    workflow = await _db.ticket_workflows.find_one({"id": ticket["workflow_id"]}, {"_id": 0})
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Find current stage and validate transition
    current_stage = None
    target_stage = None
    transition = None
    
    for stage in workflow.get("stages", []):
        if stage["id"] == ticket.get("current_stage_id"):
            current_stage = stage
            # Find the transition
            for t in stage.get("transitions", []):
                if t["id"] == data.transition_id:
                    transition = t
                    # Find target stage
                    for s in workflow.get("stages", []):
                        if s["id"] == t["to_stage_id"]:
                            target_stage = s
                            break
                    break
    
    if not transition or not target_stage:
        raise HTTPException(status_code=400, detail="Invalid transition")
    
    # Update ticket
    update_data = {
        "current_stage_id": target_stage["id"],
        "current_stage_name": target_stage["name"],
        "updated_at": get_ist_isoformat()
    }
    
    # Update field values if provided
    if data.field_values:
        update_data["form_values"] = {**ticket.get("form_values", {}), **data.field_values}
    
    # Check if terminal stage
    if target_stage.get("stage_type") in ["terminal_success", "terminal_failure"]:
        update_data["is_open"] = False
        update_data["closed_at"] = get_ist_isoformat()
        if target_stage.get("stage_type") == "terminal_success":
            update_data["resolved_at"] = get_ist_isoformat()
    
    # Update assigned team if stage has one
    if target_stage.get("assigned_team_id"):
        team = await _db.ticket_teams.find_one({"id": target_stage["assigned_team_id"]}, {"_id": 0, "name": 1})
        if team:
            update_data["assigned_team_id"] = target_stage["assigned_team_id"]
            update_data["assigned_team_name"] = team["name"]
    
    # Create timeline entry
    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "stage_change",
        "description": f"Moved to {target_stage['name']}" + (f" - {data.notes}" if data.notes else ""),
        "details": {
            "from_stage": current_stage["name"] if current_stage else None,
            "to_stage": target_stage["name"],
            "transition_label": transition.get("label")
        },
        "user_id": admin.get("id"),
        "user_name": admin.get("name"),
        "is_internal": False,
        "created_at": get_ist_isoformat()
    }
    
    await _db.tickets_v2.update_one(
        {"id": ticket_id},
        {
            "$set": update_data,
            "$push": {"timeline": timeline_entry}
        }
    )
    
    # Execute entry actions for the new stage
    for action in target_stage.get("entry_actions", []):
        if action.get("action_type") == "create_task":
            # Create task from task type
            task_type_slug = action.get("config", {}).get("task_type_slug")
            if task_type_slug:
                task_type = await _db.ticket_task_types.find_one(
                    {"slug": task_type_slug, "organization_id": org_id},
                    {"_id": 0}
                )
                if task_type:
                    # Calculate due date
                    due_hours = task_type.get("default_due_hours", 24)
                    due_at = (datetime.now(timezone.utc) + timedelta(hours=due_hours)).isoformat()
                    
                    task = TicketTask(
                        organization_id=org_id,
                        ticket_id=ticket_id,
                        ticket_number=ticket["ticket_number"],
                        task_type_id=task_type["id"],
                        task_type_name=task_type["name"],
                        name=task_type["name"],
                        description=task_type.get("description"),
                        assigned_team_id=task_type.get("default_team_id"),
                        due_at=due_at,
                        checklist=[{"id": c["id"], "text": c["text"], "required": c.get("required", False), "completed": False} for c in task_type.get("checklist", [])],
                        created_by_id=admin.get("id")
                    )
                    
                    # Get team name
                    if task.assigned_team_id:
                        team = await _db.ticket_teams.find_one({"id": task.assigned_team_id}, {"_id": 0, "name": 1})
                        if team:
                            task.assigned_team_name = team["name"]
                    
                    await _db.ticket_tasks.insert_one(task.model_dump())
                    
                    # Add task ID to ticket
                    await _db.tickets_v2.update_one(
                        {"id": ticket_id},
                        {"$push": {"task_ids": task.id}}
                    )
    
    return await get_ticket(ticket_id, admin)


@router.post("/ticketing/tickets/{ticket_id}/comment")
async def add_comment(ticket_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Add a comment to a ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "comment",
        "description": data.get("content", ""),
        "user_id": admin.get("id"),
        "user_name": admin.get("name"),
        "is_internal": data.get("is_internal", False),
        "created_at": get_ist_isoformat()
    }
    
    result = await _db.tickets_v2.update_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {
            "$push": {"timeline": timeline_entry},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return timeline_entry


# ============================================================
# TASKS
# ============================================================

@router.get("/ticketing/tasks")
async def list_tasks(
    ticket_id: Optional[str] = None,
    assigned_to_id: Optional[str] = None,
    assigned_team_id: Optional[str] = None,
    status: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List tasks with filtering"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id}
    
    if ticket_id:
        query["ticket_id"] = ticket_id
    if assigned_to_id:
        query["assigned_to_id"] = assigned_to_id
    if assigned_team_id:
        query["assigned_team_id"] = assigned_team_id
    if status:
        query["status"] = status
    
    tasks = await _db.ticket_tasks.find(query, {"_id": 0}).sort("created_at", -1).to_list(100)
    return tasks


@router.get("/ticketing/tasks/{task_id}")
async def get_task(task_id: str, admin: dict = Depends(get_current_admin)):
    """Get a single task"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    task = await _db.ticket_tasks.find_one({"id": task_id, "organization_id": org_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/ticketing/tasks/{task_id}")
async def update_task(task_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Update a task"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    data["updated_at"] = get_ist_isoformat()
    
    result = await _db.ticket_tasks.update_one(
        {"id": task_id, "organization_id": org_id},
        {"$set": data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return await _db.ticket_tasks.find_one({"id": task_id}, {"_id": 0})


@router.post("/ticketing/tasks/{task_id}/complete")
async def complete_task(task_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Complete a task"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    task = await _db.ticket_tasks.find_one({"id": task_id, "organization_id": org_id})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    
    update_data = {
        "status": "completed",
        "completed_at": get_ist_isoformat(),
        "completion_notes": data.get("notes"),
        "completion_values": data.get("values", {}),
        "updated_at": get_ist_isoformat()
    }
    
    await _db.ticket_tasks.update_one({"id": task_id}, {"$set": update_data})
    
    # Add timeline entry to ticket
    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "task_completed",
        "description": f"Task completed: {task['name']}" + (f" - {data.get('notes')}" if data.get('notes') else ""),
        "user_id": admin.get("id"),
        "user_name": admin.get("name"),
        "is_internal": False,
        "created_at": get_ist_isoformat()
    }
    
    await _db.tickets_v2.update_one(
        {"id": task["ticket_id"]},
        {
            "$push": {"timeline": timeline_entry},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    return await _db.ticket_tasks.find_one({"id": task_id}, {"_id": 0})


# ============================================================
# DASHBOARD STATS
# ============================================================

@router.get("/ticketing/stats")
async def get_ticketing_stats(admin: dict = Depends(get_current_admin)):
    """Get ticketing dashboard statistics"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Total tickets
    total = await _db.tickets_v2.count_documents({"organization_id": org_id, "is_deleted": {"$ne": True}})
    open_count = await _db.tickets_v2.count_documents({"organization_id": org_id, "is_open": True, "is_deleted": {"$ne": True}})
    closed_count = await _db.tickets_v2.count_documents({"organization_id": org_id, "is_open": False, "is_deleted": {"$ne": True}})
    
    # By priority
    priority_pipeline = [
        {"$match": {"organization_id": org_id, "is_open": True, "is_deleted": {"$ne": True}}},
        {"$group": {"_id": "$priority_name", "count": {"$sum": 1}}}
    ]
    by_priority = {doc["_id"]: doc["count"] async for doc in _db.tickets_v2.aggregate(priority_pipeline)}
    
    # By help topic
    topic_pipeline = [
        {"$match": {"organization_id": org_id, "is_open": True, "is_deleted": {"$ne": True}}},
        {"$group": {"_id": "$help_topic_name", "count": {"$sum": 1}}}
    ]
    by_topic = {doc["_id"]: doc["count"] async for doc in _db.tickets_v2.aggregate(topic_pipeline)}
    
    # Pending tasks
    pending_tasks = await _db.ticket_tasks.count_documents({
        "organization_id": org_id,
        "status": "pending"
    })
    
    return {
        "total": total,
        "open": open_count,
        "closed": closed_count,
        "by_priority": by_priority,
        "by_topic": by_topic,
        "pending_tasks": pending_tasks
    }
