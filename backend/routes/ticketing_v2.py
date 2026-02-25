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
from services.auth import get_current_admin

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
    result = await _db.ticket_forms.update_one({"id": form_id, "organization_id": org_id}, {"$set": data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Form not found")
    return await _db.ticket_forms.find_one({"id": form_id}, {"_id": 0})


@router.post("/ticketing/forms")
async def create_form(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Create a new form"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    form = {"id": str(uuid.uuid4()), "organization_id": org_id, "created_at": get_ist_isoformat(), "updated_at": get_ist_isoformat(), "is_active": True, **data}
    await _db.ticket_forms.insert_one(form)
    return await _db.ticket_forms.find_one({"id": form["id"]}, {"_id": 0})


@router.delete("/ticketing/forms/{form_id}")
async def delete_form(form_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a form"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    await _db.ticket_forms.delete_one({"id": form_id, "organization_id": org_id})
    return {"message": "Deleted"}


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


@router.post("/ticketing/workflows")
async def create_workflow(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Create a new workflow"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    wf = {"id": str(uuid.uuid4()), "organization_id": org_id, "created_at": get_ist_isoformat(), "updated_at": get_ist_isoformat(), "is_active": True, **data}
    await _db.ticket_workflows.insert_one(wf)
    return await _db.ticket_workflows.find_one({"id": wf["id"]}, {"_id": 0})


@router.delete("/ticketing/workflows/{workflow_id}")
async def delete_workflow(workflow_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a workflow"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    await _db.ticket_workflows.delete_one({"id": workflow_id, "organization_id": org_id})
    return {"message": "Deleted"}


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


@router.post("/ticketing/teams")
async def create_team(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    team = {"id": str(uuid.uuid4()), "organization_id": org_id, "created_at": get_ist_isoformat(), "is_active": True, "members": [], **data}
    await _db.ticket_teams.insert_one(team)
    return await _db.ticket_teams.find_one({"id": team["id"]}, {"_id": 0})


@router.delete("/ticketing/teams/{team_id}")
async def delete_team(team_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    await _db.ticket_teams.delete_one({"id": team_id, "organization_id": org_id})
    return {"message": "Deleted"}


# ============================================================
# ROLES
# ============================================================

@router.get("/ticketing/roles")
async def list_roles(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    return await _db.ticket_roles.find({"organization_id": org_id, "is_active": True}, {"_id": 0}).sort("name", 1).to_list(100)


@router.post("/ticketing/roles")
async def create_role(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    role = {"id": str(uuid.uuid4()), "organization_id": org_id, "created_at": get_ist_isoformat(), "is_active": True, "permissions": [], **data}
    await _db.ticket_roles.insert_one(role)
    return await _db.ticket_roles.find_one({"id": role["id"]}, {"_id": 0})


@router.put("/ticketing/roles/{role_id}")
async def update_role(role_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    data["updated_at"] = get_ist_isoformat()
    await _db.ticket_roles.update_one({"id": role_id, "organization_id": org_id}, {"$set": data})
    return await _db.ticket_roles.find_one({"id": role_id}, {"_id": 0})


@router.delete("/ticketing/roles/{role_id}")
async def delete_role(role_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    await _db.ticket_roles.delete_one({"id": role_id, "organization_id": org_id})
    return {"message": "Deleted"}


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


@router.post("/ticketing/sla-policies")
async def create_sla_policy(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    sla = {"id": str(uuid.uuid4()), "organization_id": org_id, "created_at": get_ist_isoformat(), "is_active": True, **data}
    await _db.ticket_sla_policies.insert_one(sla)
    return await _db.ticket_sla_policies.find_one({"id": sla["id"]}, {"_id": 0})


@router.put("/ticketing/sla-policies/{sla_id}")
async def update_sla_policy(sla_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    data["updated_at"] = get_ist_isoformat()
    await _db.ticket_sla_policies.update_one({"id": sla_id, "organization_id": org_id}, {"$set": data})
    return await _db.ticket_sla_policies.find_one({"id": sla_id}, {"_id": 0})


@router.delete("/ticketing/sla-policies/{sla_id}")
async def delete_sla_policy(sla_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    await _db.ticket_sla_policies.delete_one({"id": sla_id, "organization_id": org_id})
    return {"message": "Deleted"}


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


@router.post("/ticketing/priorities")
async def create_priority(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    prio = {"id": str(uuid.uuid4()), "organization_id": org_id, "created_at": get_ist_isoformat(), "is_active": True, **data}
    await _db.ticket_priorities.insert_one(prio)
    return await _db.ticket_priorities.find_one({"id": prio["id"]}, {"_id": 0})


@router.put("/ticketing/priorities/{priority_id}")
async def update_priority(priority_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    data["updated_at"] = get_ist_isoformat()
    await _db.ticket_priorities.update_one({"id": priority_id, "organization_id": org_id}, {"$set": data})
    return await _db.ticket_priorities.find_one({"id": priority_id}, {"_id": 0})


@router.delete("/ticketing/priorities/{priority_id}")
async def delete_priority(priority_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    await _db.ticket_priorities.delete_one({"id": priority_id, "organization_id": org_id})
    return {"message": "Deleted"}


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


@router.post("/ticketing/canned-responses")
async def create_canned_response(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    resp = {"id": str(uuid.uuid4()), "organization_id": org_id, "created_at": get_ist_isoformat(), "is_active": True, **data}
    await _db.ticket_canned_responses.insert_one(resp)
    return await _db.ticket_canned_responses.find_one({"id": resp["id"]}, {"_id": 0})


@router.put("/ticketing/canned-responses/{response_id}")
async def update_canned_response(response_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    data["updated_at"] = get_ist_isoformat()
    await _db.ticket_canned_responses.update_one({"id": response_id, "organization_id": org_id}, {"$set": data})
    return await _db.ticket_canned_responses.find_one({"id": response_id}, {"_id": 0})


@router.delete("/ticketing/canned-responses/{response_id}")
async def delete_canned_response(response_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id: raise HTTPException(status_code=403, detail="Organization context required")
    await _db.ticket_canned_responses.delete_one({"id": response_id, "organization_id": org_id})
    return {"message": "Deleted"}


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
    """Transition a ticket to a new stage with context-specific data"""
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
            for t in stage.get("transitions", []):
                if t["id"] == data.transition_id:
                    transition = t
                    for s in workflow.get("stages", []):
                        if s["id"] == t["to_stage_id"]:
                            target_stage = s
                            break
                    break
    
    if not transition or not target_stage:
        raise HTTPException(status_code=400, detail="Invalid transition")
    
    # Get transition requires_input config
    requires = transition.get("requires_input", "")
    
    # Validate required inputs
    if requires == "assign_engineer" and not data.assigned_to_id:
        raise HTTPException(status_code=400, detail="Please select an engineer/technician to assign")
    if requires == "schedule_visit" and not data.scheduled_at:
        raise HTTPException(status_code=400, detail="Please select a date and time for the visit")
    if requires == "diagnosis" and not data.diagnosis_findings:
        raise HTTPException(status_code=400, detail="Please provide diagnosis findings")
    
    # Update ticket
    update_data = {
        "current_stage_id": target_stage["id"],
        "current_stage_name": target_stage["name"],
        "updated_at": get_ist_isoformat()
    }
    
    # Handle engineer assignment
    if data.assigned_to_id:
        engineer = await _db.engineers.find_one(
            {"id": data.assigned_to_id},
            {"_id": 0, "name": 1, "email": 1, "phone": 1}
        )
        if not engineer:
            # Try organization members
            engineer = await _db.organization_members.find_one(
                {"id": data.assigned_to_id},
                {"_id": 0, "name": 1, "email": 1}
            )
        if engineer:
            update_data["assigned_to_id"] = data.assigned_to_id
            update_data["assigned_to_name"] = engineer.get("name", engineer.get("email", ""))
    
    # Handle visit scheduling
    if data.scheduled_at:
        update_data["scheduled_at"] = data.scheduled_at
        update_data["scheduled_end_at"] = data.scheduled_end_at
        update_data["schedule_notes"] = data.schedule_notes
        # Create a schedule record for calendar
        schedule_record = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "ticket_id": ticket_id,
            "ticket_number": ticket["ticket_number"],
            "engineer_id": ticket.get("assigned_to_id") or data.assigned_to_id,
            "engineer_name": ticket.get("assigned_to_name") or data.assigned_to_name,
            "company_name": ticket.get("company_name"),
            "subject": ticket.get("subject"),
            "scheduled_at": data.scheduled_at,
            "scheduled_end_at": data.scheduled_end_at,
            "notes": data.schedule_notes,
            "status": "scheduled",
            "created_at": get_ist_isoformat()
        }
        await _db.ticket_schedules.insert_one(schedule_record)
    
    # Handle diagnosis
    if data.diagnosis_findings:
        diagnosis_data = {
            "findings": data.diagnosis_findings,
            "recommendation": data.diagnosis_recommendation,
            "diagnosed_by": admin.get("name"),
            "diagnosed_at": get_ist_isoformat()
        }
        update_data["diagnosis"] = diagnosis_data
    
    # Handle parts list
    if data.parts_list:
        update_data["parts_required"] = data.parts_list
    
    # Handle resolution
    if data.resolution_notes:
        update_data["resolution_notes"] = data.resolution_notes
    
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
    
    # Build timeline description
    desc_parts = [f"Moved to {target_stage['name']}"]
    if data.assigned_to_id and update_data.get("assigned_to_name"):
        desc_parts.append(f"Assigned to {update_data['assigned_to_name']}")
    if data.scheduled_at:
        desc_parts.append(f"Scheduled: {data.scheduled_at}")
    if data.diagnosis_findings:
        desc_parts.append(f"Diagnosis: {data.diagnosis_findings[:100]}")
    if data.resolution_notes:
        desc_parts.append(f"Resolution: {data.resolution_notes[:100]}")
    if data.notes:
        desc_parts.append(data.notes)
    
    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "stage_change",
        "description": " | ".join(desc_parts),
        "details": {
            "from_stage": current_stage["name"] if current_stage else None,
            "to_stage": target_stage["name"],
            "transition_label": transition.get("label"),
            "assigned_to": update_data.get("assigned_to_name"),
            "scheduled_at": data.scheduled_at,
            "diagnosis": data.diagnosis_findings,
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
            task_type_slug = action.get("config", {}).get("task_type_slug")
            if task_type_slug:
                task_type = await _db.ticket_task_types.find_one(
                    {"slug": task_type_slug, "organization_id": org_id},
                    {"_id": 0}
                )
                if task_type:
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
                        assigned_to_id=data.assigned_to_id or ticket.get("assigned_to_id"),
                        assigned_to_name=update_data.get("assigned_to_name") or ticket.get("assigned_to_name"),
                        due_at=due_at,
                        checklist=[{"id": c["id"], "text": c["text"], "required": c.get("required", False), "completed": False} for c in task_type.get("checklist", [])],
                        created_by_id=admin.get("id")
                    )
                    
                    if task.assigned_team_id:
                        team = await _db.ticket_teams.find_one({"id": task.assigned_team_id}, {"_id": 0, "name": 1})
                        if team:
                            task.assigned_team_name = team["name"]
                    
                    await _db.ticket_tasks.insert_one(task.model_dump())
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


# ============================================================
# ENGINEERS & CALENDAR
# ============================================================

@router.get("/ticketing/engineers")
async def list_engineers(admin: dict = Depends(get_current_admin)):
    """List all engineers/technicians available for assignment"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Get engineers from engineers collection
    engineers = await _db.engineers.find(
        {"organization_id": org_id, "is_active": {"$ne": False}, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "phone": 1, "specialization": 1, "skills": 1}
    ).to_list(100)
    
    # For each engineer, get their current workload and last visit info
    for eng in engineers:
        # Count open assigned tickets
        eng["open_tickets"] = await _db.tickets_v2.count_documents({
            "organization_id": org_id,
            "assigned_to_id": eng["id"],
            "is_open": True,
            "is_deleted": {"$ne": True}
        })
        
        # Get last scheduled visit
        last_schedule = await _db.ticket_schedules.find_one(
            {"engineer_id": eng["id"], "organization_id": org_id},
            {"_id": 0, "scheduled_at": 1, "ticket_number": 1, "company_name": 1, "status": 1},
            sort=[("scheduled_at", -1)]
        )
        eng["last_visit"] = last_schedule
        
        # Get last assigned ticket for this device/company context
        last_ticket = await _db.tickets_v2.find_one(
            {"assigned_to_id": eng["id"], "organization_id": org_id, "is_deleted": {"$ne": True}},
            {"_id": 0, "ticket_number": 1, "company_name": 1, "subject": 1, "created_at": 1},
            sort=[("created_at", -1)]
        )
        eng["last_ticket"] = last_ticket
    
    return engineers


@router.get("/ticketing/engineers/{engineer_id}/schedule")
async def get_engineer_schedule(
    engineer_id: str,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get an engineer's schedule for calendar view (to avoid clashes)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Default: show next 14 days
    if not date_from:
        now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        date_from = now.strftime("%Y-%m-%d")
    if not date_to:
        from_date = datetime.strptime(date_from, "%Y-%m-%d")
        date_to = (from_date + timedelta(days=14)).strftime("%Y-%m-%d")
    
    # Get scheduled visits from ticket_schedules
    schedules = await _db.ticket_schedules.find({
        "engineer_id": engineer_id,
        "organization_id": org_id,
        "scheduled_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"},
        "status": {"$ne": "cancelled"}
    }, {"_id": 0}).sort("scheduled_at", 1).to_list(100)
    
    # Also check tickets with scheduled_at that don't have schedule records
    scheduled_tickets = await _db.tickets_v2.find({
        "assigned_to_id": engineer_id,
        "organization_id": org_id,
        "scheduled_at": {"$gte": date_from, "$lte": date_to + "T23:59:59"},
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "company_name": 1, "scheduled_at": 1, "scheduled_end_at": 1, "current_stage_name": 1}).to_list(100)
    
    # Get engineer details
    engineer = await _db.engineers.find_one(
        {"id": engineer_id},
        {"_id": 0, "id": 1, "name": 1, "email": 1}
    )
    
    return {
        "engineer": engineer,
        "schedules": schedules,
        "tickets": scheduled_tickets,
        "date_from": date_from,
        "date_to": date_to
    }


@router.get("/ticketing/engineers/{engineer_id}/device-history")
async def get_engineer_device_history(
    engineer_id: str,
    device_id: Optional[str] = None,
    company_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get history of an engineer's visits to a specific device/company"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {
        "assigned_to_id": engineer_id,
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    }
    if device_id:
        query["device_id"] = device_id
    if company_id:
        query["company_id"] = company_id
    
    history = await _db.tickets_v2.find(
        query,
        {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "current_stage_name": 1, 
         "company_name": 1, "scheduled_at": 1, "created_at": 1, "resolved_at": 1, "diagnosis": 1}
    ).sort("created_at", -1).to_list(20)
    
    return history


# ============================================================
# TECHNICIAN DASHBOARD
# ============================================================

@router.get("/ticketing/technician/dashboard")
async def technician_dashboard(admin: dict = Depends(get_current_admin)):
    """Dashboard for field technicians - shows their assigned work"""
    user_id = admin.get("id")
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Get engineer record for this user
    engineer = await _db.engineers.find_one(
        {"$or": [{"id": user_id}, {"email": admin.get("email")}], "organization_id": org_id},
        {"_id": 0}
    )
    engineer_id = engineer["id"] if engineer else user_id
    
    # Assigned tickets
    assigned_tickets = await _db.tickets_v2.find({
        "assigned_to_id": engineer_id,
        "organization_id": org_id,
        "is_open": True,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "timeline": 0}).sort("created_at", -1).to_list(50)
    
    # Assigned tasks
    assigned_tasks = await _db.ticket_tasks.find({
        "assigned_to_id": engineer_id,
        "organization_id": org_id,
        "status": {"$ne": "completed"}
    }, {"_id": 0}).sort("due_at", 1).to_list(50)
    
    # Upcoming scheduled visits
    now = datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat()
    upcoming_schedules = await _db.ticket_schedules.find({
        "engineer_id": engineer_id,
        "organization_id": org_id,
        "scheduled_at": {"$gte": now[:10]},
        "status": {"$ne": "cancelled"}
    }, {"_id": 0}).sort("scheduled_at", 1).to_list(20)
    
    # Stats
    total_assigned = len(assigned_tickets)
    visits_today = len([s for s in upcoming_schedules if s.get("scheduled_at", "").startswith(now[:10])])
    pending_diagnosis = len([t for t in assigned_tickets if t.get("current_stage_name") in ["Visit Scheduled", "Session Scheduled"]])
    completed_this_week = await _db.tickets_v2.count_documents({
        "assigned_to_id": engineer_id,
        "organization_id": org_id,
        "resolved_at": {"$gte": (datetime.now(timezone(timedelta(hours=5, minutes=30))) - timedelta(days=7)).isoformat()},
        "is_deleted": {"$ne": True}
    })
    
    return {
        "engineer": engineer,
        "assigned_tickets": assigned_tickets,
        "assigned_tasks": assigned_tasks,
        "upcoming_schedules": upcoming_schedules,
        "stats": {
            "total_assigned": total_assigned,
            "visits_today": visits_today,
            "pending_diagnosis": pending_diagnosis,
            "completed_this_week": completed_this_week
        }
    }
