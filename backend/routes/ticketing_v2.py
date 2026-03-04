"""
Ticketing System v2 - API Routes
================================
Complete API for the new workflow-driven ticketing system.
"""

import uuid
import random
import string
import os
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

@router.post("/ticketing/deduplicate")
async def deduplicate_ticketing_data(admin: dict = Depends(get_current_admin)):
    """Remove duplicate seed data by keeping only one entry per slug"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    collections = [
        ("ticket_help_topics", "slug"), ("ticket_forms", "slug"), ("ticket_workflows", "slug"),
        ("ticket_teams", "slug"), ("ticket_roles", "slug"), ("ticket_sla_policies", "name"),
        ("ticket_canned_responses", "slug"), ("ticket_priorities", "slug"),
        ("ticket_task_types", "slug"), ("ticket_notification_templates", "slug"),
        ("ticket_business_hours", "name"),
    ]
    removed = {}
    for coll_name, key_field in collections:
        coll = _db[coll_name]
        docs = await coll.find({"organization_id": org_id}, {"_id": 0, "id": 1, key_field: 1, "created_at": 1}).to_list(1000)
        seen = {}
        to_delete = []
        for doc in docs:
            k = doc.get(key_field, doc.get("id"))
            if k in seen:
                to_delete.append(doc["id"])
            else:
                seen[k] = doc["id"]
        if to_delete:
            await coll.delete_many({"id": {"$in": to_delete}, "organization_id": org_id})
            removed[coll_name] = len(to_delete)
    
    return {"message": "Deduplication complete", "removed": removed}


@router.post("/ticketing/seed")
async def seed_ticketing_system(admin: dict = Depends(get_current_admin)):
    """Seed all ticketing system data for the organization"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check if already seeded by looking for help topics with known slugs
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
# HELP TOPIC CATEGORIES (Master)
# ============================================================

@router.get("/ticketing/help-topic-categories")
async def list_help_topic_categories(admin: dict = Depends(get_current_admin)):
    """List all help topic categories"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    cats = await _db.help_topic_categories.find(
        {"organization_id": org_id}, {"_id": 0}
    ).sort("order", 1).to_list(50)
    return cats


@router.post("/ticketing/help-topic-categories")
async def create_help_topic_category(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Create a help topic category"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    cat = {
        "id": str(uuid.uuid4()), "organization_id": org_id,
        "name": data["name"], "slug": data.get("slug", data["name"].lower().replace(" ", "-")),
        "description": data.get("description"), "icon": data.get("icon", "folder"),
        "color": data.get("color", "#6B7280"), "order": data.get("order", 0),
        "is_active": True, "created_at": get_ist_isoformat()
    }
    await _db.help_topic_categories.insert_one(cat)
    return {k: v for k, v in cat.items() if k != "_id"}


@router.put("/ticketing/help-topic-categories/{cat_id}")
async def update_help_topic_category(cat_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Update a help topic category"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    update = {k: v for k, v in data.items() if k not in ("id", "organization_id", "_id")}
    await _db.help_topic_categories.update_one(
        {"id": cat_id, "organization_id": org_id}, {"$set": update}
    )
    return await _db.help_topic_categories.find_one({"id": cat_id}, {"_id": 0})


@router.delete("/ticketing/help-topic-categories/{cat_id}")
async def delete_help_topic_category(cat_id: str, admin: dict = Depends(get_current_admin)):
    """Delete a help topic category"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    await _db.help_topic_categories.delete_one({"id": cat_id, "organization_id": org_id})
    return {"message": "Deleted"}


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
# DEVICE WARRANTY DETECTION
# ============================================================

@router.get("/ticketing/device-warranty-check/{device_id}")
async def check_device_warranty(device_id: str, admin: dict = Depends(get_current_admin)):
    """Check device warranty/AMC status and suggest appropriate workflow.
    Returns: { warranty_type, suggested_workflow_id, suggested_help_topic_id, details }
    """
    from datetime import datetime, timezone, timedelta
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    device = await _db.devices.find_one(
        {"id": device_id, "organization_id": org_id},
        {"_id": 0}
    )
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    warranty_type = "non_warranty"
    details = {}

    # Check AMC first (higher priority)
    amc = await _db.amc_contracts.find_one(
        {"organization_id": org_id, "device_id": device_id, "status": "active"},
        {"_id": 0}
    )
    if not amc:
        # Check if device's company has an AMC covering this device type
        amc = await _db.amc_contracts.find_one(
            {"organization_id": org_id, "company_id": device.get("company_id"), "status": "active"},
            {"_id": 0}
        )

    if amc:
        end_date = amc.get("end_date") or amc.get("amc_end_date")
        if end_date:
            try:
                end_dt = datetime.fromisoformat(str(end_date).replace('Z', '+00:00'))
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
                if end_dt > now:
                    warranty_type = "amc"
                    details = {"amc_contract_id": amc.get("id"), "amc_end_date": str(end_date), "amc_provider": amc.get("provider_name") or "MSP"}
            except (ValueError, TypeError):
                pass

    # If not AMC, check brand warranty
    if warranty_type == "non_warranty" and device.get("warranty_end_date"):
        try:
            wdate = str(device["warranty_end_date"])
            w_dt = datetime.fromisoformat(wdate.replace('Z', '+00:00'))
            if w_dt.tzinfo is None:
                w_dt = w_dt.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
            if w_dt > now:
                warranty_type = "oem_warranty"
                details = {
                    "warranty_end_date": wdate,
                    "brand": device.get("brand", ""),
                    "model": device.get("model", ""),
                    "serial_number": device.get("serial_number", "")
                }
        except (ValueError, TypeError):
            pass

    if warranty_type == "non_warranty":
        details = {"reason": "No active warranty or AMC found"}

    # Find matching workflow and help topic
    slug_map = {
        "oem_warranty": "oem-warranty",
        "amc": "amc-support",
        "non_warranty": "non-warranty"
    }
    slug = slug_map.get(warranty_type)

    workflow = await _db.ticket_workflows.find_one(
        {"organization_id": org_id, "slug": slug, "is_active": True},
        {"_id": 0, "id": 1, "name": 1}
    )
    topic = await _db.ticket_help_topics.find_one(
        {"organization_id": org_id, "workflow_id": workflow["id"] if workflow else None, "is_active": True},
        {"_id": 0, "id": 1, "name": 1}
    ) if workflow else None

    return {
        "device_id": device_id,
        "warranty_type": warranty_type,
        "warranty_type_label": {"oem_warranty": "Brand Warranty / ADP", "amc": "AMC Contract", "non_warranty": "Non-Warranty"}[warranty_type],
        "managed_by": {"oem_warranty": "OEM (Brand)", "amc": "MSP (Your Team)", "non_warranty": "MSP (Your Team)"}[warranty_type],
        "suggested_workflow_id": workflow["id"] if workflow else None,
        "suggested_workflow_name": workflow["name"] if workflow else None,
        "suggested_help_topic_id": topic["id"] if topic else None,
        "suggested_help_topic_name": topic["name"] if topic else None,
        "details": details
    }


@router.post("/ticketing/seed-warranty-workflows")
async def seed_warranty_workflows(admin: dict = Depends(get_current_admin)):
    """Create the 3 standard warranty-based workflows and corresponding help topics."""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    created = {"workflows": [], "help_topics": []}

    # Helper to create stages
    def make_stage(name, slug, stype, order, transitions=None):
        return {
            "id": str(uuid.uuid4()), "name": name, "slug": slug,
            "stage_type": stype, "order": order,
            "transitions": transitions or [], "entry_actions": [],
            "assigned_team_id": None, "color": "#6B7280"
        }

    def make_trans(label, to_id, color="primary", requires_input=""):
        return {
            "id": str(uuid.uuid4()), "to_stage_id": to_id,
            "label": label, "color": color, "requires_input": requires_input, "order": 0
        }

    # ── 1. OEM WARRANTY WORKFLOW ──
    existing = await _db.ticket_workflows.find_one({"organization_id": org_id, "slug": "oem-warranty"})
    if not existing:
        s = [None] * 8
        ids = [str(uuid.uuid4()) for _ in range(8)]
        s[0] = make_stage("New", "new", "initial", 0)
        s[0]["id"] = ids[0]
        s[1] = make_stage("Verified Warranty", "verified_warranty", "in_progress", 1)
        s[1]["id"] = ids[1]
        s[2] = make_stage("Escalated to OEM", "escalated_to_oem", "in_progress", 2)
        s[2]["id"] = ids[2]
        s[3] = make_stage("OEM Case Logged", "oem_case_logged", "waiting", 3)
        s[3]["id"] = ids[3]
        s[4] = make_stage("OEM Engineer Dispatched", "oem_engineer_dispatched", "in_progress", 4)
        s[4]["id"] = ids[4]
        s[5] = make_stage("OEM Resolution", "oem_resolution", "in_progress", 5)
        s[5]["id"] = ids[5]
        s[6] = make_stage("Closed", "closed", "terminal_success", 6)
        s[6]["id"] = ids[6]
        s[7] = make_stage("Cancelled", "cancelled", "terminal_failure", 7)
        s[7]["id"] = ids[7]

        s[0]["transitions"] = [make_trans("Verify Warranty", ids[1], "primary")]
        s[1]["transitions"] = [make_trans("Escalate to OEM", ids[2], "warning"), make_trans("Cancel", ids[7], "danger")]
        s[2]["transitions"] = [make_trans("Log OEM Case", ids[3], "primary")]
        s[3]["transitions"] = [make_trans("OEM Dispatched Engineer", ids[4], "primary")]
        s[4]["transitions"] = [make_trans("OEM Resolved", ids[5], "success"), make_trans("Back to OEM", ids[3], "warning")]
        s[5]["transitions"] = [make_trans("Close Ticket", ids[6], "success")]

        wf = {
            "id": str(uuid.uuid4()), "organization_id": org_id,
            "name": "OEM Warranty Workflow", "slug": "oem-warranty",
            "description": "For devices under brand warranty or ADP. Coordinated with OEM.",
            "stages": s, "is_active": True, "is_system": False,
            "created_at": get_ist_isoformat(), "updated_at": get_ist_isoformat()
        }
        await _db.ticket_workflows.insert_one(wf)
        created["workflows"].append({"id": wf["id"], "name": wf["name"]})

        # Create matching help topic
        ht = {
            "id": str(uuid.uuid4()), "organization_id": org_id,
            "name": "Warranty Claim (OEM)", "slug": "warranty-claim-oem",
            "description": "Device under brand warranty or ADP plan. Managed by OEM.",
            "icon": "shield", "color": "#F59E0B", "category": "support",
            "workflow_id": wf["id"], "default_priority": "high",
            "require_device": True, "is_active": True, "is_public": True,
            "created_at": get_ist_isoformat(), "updated_at": get_ist_isoformat()
        }
        await _db.ticket_help_topics.insert_one(ht)
        created["help_topics"].append({"id": ht["id"], "name": ht["name"]})

    # ── 2. AMC WORKFLOW ──
    existing = await _db.ticket_workflows.find_one({"organization_id": org_id, "slug": "amc-support"})
    if not existing:
        ids = [str(uuid.uuid4()) for _ in range(10)]
        s = []
        s.append({**make_stage("New", "new", "initial", 0), "id": ids[0]})
        s.append({**make_stage("Assigned", "assigned", "in_progress", 1), "id": ids[1]})
        s.append({**make_stage("Scheduled", "scheduled", "in_progress", 2), "id": ids[2]})
        s.append({**make_stage("In Progress", "in_progress", "in_progress", 3), "id": ids[3]})
        s.append({**make_stage("Diagnosed", "diagnosed", "in_progress", 4), "id": ids[4]})
        s.append({**make_stage("Awaiting Parts", "awaiting_parts", "waiting", 5), "id": ids[5]})
        s.append({**make_stage("Parts Received", "parts_received", "in_progress", 6), "id": ids[6]})
        s.append({**make_stage("Fixed On-Site", "fixed_onsite", "in_progress", 7), "id": ids[7]})
        s.append({**make_stage("Resolved", "resolved", "terminal_success", 8), "id": ids[8]})
        s.append({**make_stage("Cancelled", "cancelled", "terminal_failure", 9), "id": ids[9]})

        s[0]["transitions"] = [make_trans("Assign Engineer", ids[1], "primary", "assign_engineer")]
        s[1]["transitions"] = [make_trans("Schedule Visit", ids[2], "primary", "schedule_visit"), make_trans("Start Work", ids[3], "success")]
        s[2]["transitions"] = [make_trans("Start Work", ids[3], "success")]
        s[3]["transitions"] = [make_trans("Record Diagnosis", ids[4], "primary", "diagnosis"), make_trans("Fixed On-Site", ids[7], "success", "resolution")]
        s[4]["transitions"] = [make_trans("Request Parts", ids[5], "warning", "parts_list"), make_trans("Fixed On-Site", ids[7], "success", "resolution"), make_trans("Create Quotation", ids[5], "primary", "quotation")]
        s[5]["transitions"] = [make_trans("Parts Received", ids[6], "success")]
        s[6]["transitions"] = [make_trans("Resume Work", ids[3], "primary")]
        s[7]["transitions"] = [make_trans("Mark Resolved", ids[8], "success")]

        wf = {
            "id": str(uuid.uuid4()), "organization_id": org_id,
            "name": "AMC Support Workflow", "slug": "amc-support",
            "description": "For devices under AMC contract. Managed by MSP team.",
            "stages": s, "is_active": True, "is_system": False,
            "created_at": get_ist_isoformat(), "updated_at": get_ist_isoformat()
        }
        await _db.ticket_workflows.insert_one(wf)
        created["workflows"].append({"id": wf["id"], "name": wf["name"]})

        ht = {
            "id": str(uuid.uuid4()), "organization_id": org_id,
            "name": "AMC Support", "slug": "amc-support",
            "description": "Device under Annual Maintenance Contract. Managed by MSP.",
            "icon": "wrench", "color": "#10B981", "category": "support",
            "workflow_id": wf["id"], "default_priority": "medium",
            "require_device": True, "is_active": True, "is_public": True,
            "created_at": get_ist_isoformat(), "updated_at": get_ist_isoformat()
        }
        await _db.ticket_help_topics.insert_one(ht)
        created["help_topics"].append({"id": ht["id"], "name": ht["name"]})

    # ── 3. NON-WARRANTY WORKFLOW ──
    existing = await _db.ticket_workflows.find_one({"organization_id": org_id, "slug": "non-warranty"})
    if not existing:
        ids = [str(uuid.uuid4()) for _ in range(12)]
        s = []
        s.append({**make_stage("New", "new", "initial", 0), "id": ids[0]})
        s.append({**make_stage("Assigned", "assigned", "in_progress", 1), "id": ids[1]})
        s.append({**make_stage("Diagnosed", "diagnosed", "in_progress", 2), "id": ids[2]})
        s.append({**make_stage("Quotation Sent", "quotation_sent", "waiting", 3), "id": ids[3]})
        s.append({**make_stage("Customer Approved", "customer_approved", "in_progress", 4), "id": ids[4]})
        s.append({**make_stage("Customer Rejected", "customer_rejected", "terminal_failure", 5), "id": ids[5]})
        s.append({**make_stage("Parts Ordered", "parts_ordered", "waiting", 6), "id": ids[6]})
        s.append({**make_stage("In Progress", "in_progress", "in_progress", 7), "id": ids[7]})
        s.append({**make_stage("Fixed On-Site", "fixed_onsite", "in_progress", 8), "id": ids[8]})
        s.append({**make_stage("Billing Pending", "billing_pending", "waiting", 9), "id": ids[9]})
        s.append({**make_stage("Resolved", "resolved", "terminal_success", 10), "id": ids[10]})
        s.append({**make_stage("Cancelled", "cancelled", "terminal_failure", 11), "id": ids[11]})

        s[0]["transitions"] = [make_trans("Assign Engineer", ids[1], "primary", "assign_engineer")]
        s[1]["transitions"] = [make_trans("Record Diagnosis", ids[2], "primary", "diagnosis")]
        s[2]["transitions"] = [make_trans("Send Quotation", ids[3], "primary", "quotation"), make_trans("Cancel", ids[11], "danger")]
        s[3]["transitions"] = [make_trans("Customer Approved", ids[4], "success"), make_trans("Customer Rejected", ids[5], "danger")]
        s[4]["transitions"] = [make_trans("Order Parts", ids[6], "primary", "parts_list"), make_trans("Start Work", ids[7], "success")]
        s[6]["transitions"] = [make_trans("Parts Received - Start Work", ids[7], "success")]
        s[7]["transitions"] = [make_trans("Fixed On-Site", ids[8], "success", "resolution")]
        s[8]["transitions"] = [make_trans("Generate Bill", ids[9], "primary")]
        s[9]["transitions"] = [make_trans("Mark Resolved", ids[10], "success")]

        wf = {
            "id": str(uuid.uuid4()), "organization_id": org_id,
            "name": "Non-Warranty Workflow", "slug": "non-warranty",
            "description": "For out-of-warranty devices. Requires quotation and customer approval.",
            "stages": s, "is_active": True, "is_system": False,
            "created_at": get_ist_isoformat(), "updated_at": get_ist_isoformat()
        }
        await _db.ticket_workflows.insert_one(wf)
        created["workflows"].append({"id": wf["id"], "name": wf["name"]})

        ht = {
            "id": str(uuid.uuid4()), "organization_id": org_id,
            "name": "Non-Warranty Repair", "slug": "non-warranty-repair",
            "description": "Device out of warranty. Customer pays for parts and service.",
            "icon": "alert-triangle", "color": "#EF4444", "category": "support",
            "workflow_id": wf["id"], "default_priority": "medium",
            "require_device": True, "is_active": True, "is_public": True,
            "created_at": get_ist_isoformat(), "updated_at": get_ist_isoformat()
        }
        await _db.ticket_help_topics.insert_one(ht)
        created["help_topics"].append({"id": ht["id"], "name": ht["name"]})

    return {
        "message": f"Created {len(created['workflows'])} workflows and {len(created['help_topics'])} help topics",
        "created": created
    }


@router.post("/ticketing/seed-comprehensive-topics")
async def seed_comprehensive_topics(admin: dict = Depends(get_current_admin)):
    """Seed comprehensive help topic categories and topics covering all MSP/warranty scenarios.
    Fully master-driven — everything is editable after creation.
    """
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    # Get existing workflows for linking
    workflows = {}
    async for wf in _db.ticket_workflows.find({"organization_id": org_id}, {"_id": 0, "id": 1, "slug": 1}):
        workflows[wf["slug"]] = wf["id"]

    # Get existing forms for linking
    forms = {}
    async for f in _db.ticket_forms.find({"organization_id": org_id}, {"_id": 0, "id": 1, "slug": 1}):
        forms[f["slug"]] = f["id"]

    stats = {"categories": 0, "topics": 0, "skipped": 0}

    # ── CATEGORIES ──
    category_defs = [
        {"name": "Hardware & Devices", "slug": "hardware", "icon": "monitor", "color": "#3B82F6", "order": 1,
         "description": "Hardware repairs, device issues, component failures"},
        {"name": "Software & OS", "slug": "software", "icon": "code", "color": "#8B5CF6", "order": 2,
         "description": "Software installation, OS issues, driver problems"},
        {"name": "Network & Connectivity", "slug": "network", "icon": "wifi", "color": "#06B6D4", "order": 3,
         "description": "Network, internet, WiFi, VPN issues"},
        {"name": "Peripherals & Accessories", "slug": "peripherals", "icon": "printer", "color": "#F59E0B", "order": 4,
         "description": "Printers, scanners, monitors, docking stations"},
        {"name": "Service Requests", "slug": "service", "icon": "wrench", "color": "#10B981", "order": 5,
         "description": "Installation, relocation, upgrades, setup"},
        {"name": "Warranty & AMC", "slug": "warranty", "icon": "shield", "color": "#EF4444", "order": 6,
         "description": "Warranty claims, AMC support, OEM coordination"},
        {"name": "Commercial & Billing", "slug": "commercial", "icon": "receipt", "color": "#EC4899", "order": 7,
         "description": "Quotations, billing, AMC renewals, invoicing"},
        {"name": "General", "slug": "general", "icon": "help-circle", "color": "#6B7280", "order": 8,
         "description": "General inquiries, feedback, complaints"},
    ]

    cat_ids = {}
    for cdef in category_defs:
        existing = await _db.help_topic_categories.find_one(
            {"organization_id": org_id, "slug": cdef["slug"]}
        )
        if existing:
            cat_ids[cdef["slug"]] = existing["id"]
        else:
            cdef["id"] = str(uuid.uuid4())
            cdef["organization_id"] = org_id
            cdef["is_active"] = True
            cdef["created_at"] = get_ist_isoformat()
            await _db.help_topic_categories.insert_one(cdef)
            cat_ids[cdef["slug"]] = cdef["id"]
            stats["categories"] += 1

    # Default workflow mapping by category
    wf_map = {
        "hardware": workflows.get("amc-support") or workflows.get("onsite_support_workflow"),
        "software": workflows.get("remote_support_workflow") or workflows.get("simple_support_workflow"),
        "network": workflows.get("remote_support_workflow") or workflows.get("simple_support_workflow"),
        "peripherals": workflows.get("amc-support") or workflows.get("onsite_support_workflow"),
        "service": workflows.get("onsite_support_workflow") or workflows.get("amc-support"),
        "warranty": workflows.get("oem-warranty"),
        "commercial": workflows.get("sales_pipeline_workflow") or workflows.get("simple_support_workflow"),
        "general": workflows.get("simple_support_workflow"),
    }

    # ── TOPICS ──
    topic_defs = [
        # Hardware & Devices
        {"name": "Laptop Repair", "slug": "laptop-repair", "cat": "hardware", "desc": "Laptop hardware issues - screen, keyboard, motherboard, battery",
         "icon": "laptop", "require_device": True, "priority": "high",
         "tags": ["laptop", "screen", "keyboard", "motherboard", "battery", "hinge", "charging"]},
        {"name": "Desktop Repair", "slug": "desktop-repair", "cat": "hardware", "desc": "Desktop/PC hardware issues - power supply, motherboard, RAM, storage",
         "icon": "monitor", "require_device": True, "priority": "high",
         "tags": ["desktop", "pc", "power supply", "ram", "storage", "motherboard"]},
        {"name": "Server Issue", "slug": "server-issue", "cat": "hardware", "desc": "Server hardware failures, RAID issues, component replacement",
         "icon": "server", "require_device": True, "priority": "critical",
         "tags": ["server", "raid", "hard drive", "memory", "power", "fan"]},
        {"name": "Tablet / Mobile Device", "slug": "tablet-mobile", "cat": "hardware", "desc": "Tablet or mobile device repair and issues",
         "icon": "smartphone", "require_device": True, "priority": "medium",
         "tags": ["tablet", "mobile", "ipad", "screen crack", "battery"]},
        {"name": "Data Recovery", "slug": "data-recovery", "cat": "hardware", "desc": "Hard drive failure, data recovery, backup restoration",
         "icon": "hard-drive", "require_device": True, "priority": "critical",
         "tags": ["data", "recovery", "hard drive", "backup", "restore", "deleted"]},

        # Software & OS
        {"name": "OS Crash / Blue Screen", "slug": "os-crash", "cat": "software", "desc": "Operating system crash, BSOD, boot failure",
         "icon": "alert-circle", "require_device": True, "priority": "high",
         "tags": ["crash", "bsod", "blue screen", "boot", "startup", "windows", "os"]},
        {"name": "Software Installation", "slug": "software-install", "cat": "software", "desc": "Install, update, or configure software applications",
         "icon": "download", "require_device": True, "priority": "medium",
         "tags": ["install", "software", "application", "update", "license", "activation"]},
        {"name": "Virus / Malware", "slug": "virus-malware", "cat": "software", "desc": "Virus infection, malware removal, security threats",
         "icon": "shield-alert", "require_device": True, "priority": "high",
         "tags": ["virus", "malware", "ransomware", "infection", "security", "antivirus"]},
        {"name": "Performance Issue", "slug": "performance-issue", "cat": "software", "desc": "Slow system, hanging, high CPU/memory usage",
         "icon": "activity", "require_device": True, "priority": "medium",
         "tags": ["slow", "hanging", "performance", "lag", "freeze", "cpu", "memory"]},
        {"name": "Email Configuration", "slug": "email-config", "cat": "software", "desc": "Email client setup, Outlook configuration, email sync issues",
         "icon": "mail", "require_device": True, "priority": "medium",
         "tags": ["email", "outlook", "gmail", "mail", "sync", "configuration"]},
        {"name": "OS Re-installation", "slug": "os-reinstall", "cat": "software", "desc": "Fresh OS installation, format and reinstall",
         "icon": "refresh-cw", "require_device": True, "priority": "medium",
         "tags": ["reinstall", "format", "fresh install", "os", "windows", "recovery"]},

        # Network & Connectivity
        {"name": "Internet Not Working", "slug": "internet-down", "cat": "network", "desc": "No internet connection, slow browsing, DNS issues",
         "icon": "wifi-off", "require_device": False, "priority": "high",
         "tags": ["internet", "wifi", "connection", "dns", "browsing", "no network"]},
        {"name": "VPN Issue", "slug": "vpn-issue", "cat": "network", "desc": "VPN connection failure, slow VPN, configuration",
         "icon": "lock", "require_device": True, "priority": "high",
         "tags": ["vpn", "remote access", "connection", "tunnel", "firewall"]},
        {"name": "Network Setup", "slug": "network-setup", "cat": "network", "desc": "LAN configuration, switch setup, cabling",
         "icon": "git-branch", "require_device": False, "priority": "medium",
         "tags": ["lan", "switch", "cable", "ethernet", "network setup", "ip address"]},
        {"name": "Firewall / Security", "slug": "firewall-security", "cat": "network", "desc": "Firewall configuration, security policies, access control",
         "icon": "shield", "require_device": False, "priority": "high",
         "tags": ["firewall", "security", "access", "block", "policy", "port"]},

        # Peripherals & Accessories
        {"name": "Printer Issue", "slug": "printer-issue", "cat": "peripherals", "desc": "Printer not printing, paper jam, toner replacement",
         "icon": "printer", "require_device": True, "priority": "medium",
         "tags": ["printer", "print", "jam", "toner", "ink", "cartridge", "paper"]},
        {"name": "Monitor / Display", "slug": "monitor-issue", "cat": "peripherals", "desc": "Monitor not working, display flicker, resolution issues",
         "icon": "monitor", "require_device": True, "priority": "medium",
         "tags": ["monitor", "display", "screen", "flicker", "resolution", "hdmi"]},
        {"name": "UPS / Power", "slug": "ups-power", "cat": "peripherals", "desc": "UPS failure, battery replacement, power issues",
         "icon": "battery", "require_device": True, "priority": "high",
         "tags": ["ups", "power", "battery", "backup", "surge", "electricity"]},
        {"name": "CCTV / Surveillance", "slug": "cctv-surveillance", "cat": "peripherals", "desc": "CCTV camera issues, DVR/NVR problems, recording failure",
         "icon": "camera", "require_device": True, "priority": "high",
         "tags": ["cctv", "camera", "dvr", "nvr", "recording", "surveillance", "video"]},
        {"name": "Scanner / Copier", "slug": "scanner-copier", "cat": "peripherals", "desc": "Scanner not working, copier issues, document feeder problems",
         "icon": "scan", "require_device": True, "priority": "medium",
         "tags": ["scanner", "copier", "scan", "copy", "document", "feeder"]},
        {"name": "Access Control / Biometric", "slug": "access-control", "cat": "peripherals", "desc": "Biometric device, access control, attendance system",
         "icon": "fingerprint", "require_device": True, "priority": "medium",
         "tags": ["biometric", "fingerprint", "access control", "attendance", "door lock"]},

        # Service Requests
        {"name": "New Installation / Setup", "slug": "new-installation", "cat": "service", "desc": "Fresh device setup, workstation configuration, deployment",
         "icon": "box", "require_device": False, "priority": "medium",
         "tags": ["install", "setup", "new", "deployment", "configuration", "workstation"]},
        {"name": "Device Relocation", "slug": "device-relocation", "cat": "service", "desc": "Moving equipment between sites, offices, or floors",
         "icon": "truck", "require_device": True, "priority": "low",
         "tags": ["relocation", "move", "shift", "transfer", "site change"]},
        {"name": "Asset Disposal", "slug": "asset-disposal", "cat": "service", "desc": "End-of-life device handling, data wiping, disposal",
         "icon": "trash-2", "require_device": True, "priority": "low",
         "tags": ["disposal", "decommission", "end of life", "scrap", "data wipe"]},
        {"name": "Upgrade Request", "slug": "upgrade-request", "cat": "service", "desc": "RAM upgrade, SSD upgrade, OS upgrade",
         "icon": "arrow-up-circle", "require_device": True, "priority": "medium",
         "tags": ["upgrade", "ram", "ssd", "memory", "storage", "os upgrade"]},
        {"name": "Preventive Maintenance", "slug": "preventive-maintenance", "cat": "service", "desc": "Scheduled maintenance, cleaning, health check",
         "icon": "calendar", "require_device": True, "priority": "low",
         "tags": ["maintenance", "preventive", "cleaning", "health check", "scheduled"]},

        # Warranty & AMC (these link to existing warranty workflows)
        # Note: AMC Support, Non-Warranty Repair, Warranty Claim (OEM) already exist

        # Commercial & Billing
        {"name": "AMC Renewal", "slug": "amc-renewal", "cat": "commercial", "desc": "AMC contract renewal request",
         "icon": "refresh-cw", "require_device": False, "priority": "medium",
         "tags": ["amc", "renewal", "contract", "annual", "maintenance"]},
        {"name": "Billing Dispute", "slug": "billing-dispute", "cat": "commercial", "desc": "Invoice queries, payment issues, billing corrections",
         "icon": "alert-triangle", "require_device": False, "priority": "medium",
         "tags": ["billing", "invoice", "payment", "dispute", "correction", "credit"]},

        # General (some already exist: General Inquiry, Feedback, Complaint)
        {"name": "Escalation", "slug": "escalation", "cat": "general", "desc": "Escalate an existing issue to management",
         "icon": "arrow-up", "require_device": False, "priority": "critical",
         "tags": ["escalation", "urgent", "management", "priority", "sla breach"]},
        {"name": "Training Request", "slug": "training-request", "cat": "general", "desc": "Request training for software or hardware",
         "icon": "book-open", "require_device": False, "priority": "low",
         "tags": ["training", "education", "learn", "guide", "how to"]},
    ]

    for tdef in topic_defs:
        existing = await _db.ticket_help_topics.find_one(
            {"organization_id": org_id, "slug": tdef["slug"]}
        )
        if existing:
            stats["skipped"] += 1
            continue

        cat_slug = tdef.pop("cat")
        topic = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "name": tdef["name"],
            "slug": tdef["slug"],
            "description": tdef.get("desc", ""),
            "icon": tdef.get("icon", "ticket"),
            "color": next((c["color"] for c in category_defs if c["slug"] == cat_slug), "#3B82F6"),
            "category": cat_slug,
            "category_id": cat_ids.get(cat_slug),
            "parent_id": None,
            "workflow_id": wf_map.get(cat_slug),
            "form_id": None,
            "default_priority": tdef.get("priority", "medium"),
            "require_device": tdef.get("require_device", False),
            "require_company": True,
            "require_contact": True,
            "auto_assign": False,
            "assignment_method": "manual",
            "tags": tdef.get("tags", []),
            "is_public": True,
            "is_active": True,
            "is_system": False,
            "ticket_count": 0,
            "created_at": get_ist_isoformat(),
            "updated_at": get_ist_isoformat(),
        }
        await _db.ticket_help_topics.insert_one(topic)
        stats["topics"] += 1

    # Update existing topics to have category_ids
    for cat_slug, cat_id in cat_ids.items():
        await _db.ticket_help_topics.update_many(
            {"organization_id": org_id, "category": cat_slug, "category_id": None},
            {"$set": {"category_id": cat_id}}
        )

    return {
        "message": f"Created {stats['categories']} categories, {stats['topics']} topics ({stats['skipped']} already existed)",
        "stats": stats,
        "categories": list(cat_ids.keys())
    }


@router.post("/ticketing/auto-link-forms")
async def auto_link_forms_to_topics(admin: dict = Depends(get_current_admin)):
    """Automatically link forms to help topics based on category/name matching."""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    # Build form lookup
    forms = {}
    async for f in _db.ticket_forms.find({"organization_id": org_id}, {"_id": 0, "id": 1, "slug": 1, "name": 1}):
        forms[f.get("slug", "")] = f["id"]
        forms[f["name"].lower()] = f["id"]

    # Mapping rules: topic category/slug -> form slug
    form_map = {
        # Hardware topics -> On-Site Support Form
        "hardware": forms.get("onsite_support_form"),
        "laptop-repair": forms.get("onsite_support_form"),
        "desktop-repair": forms.get("onsite_support_form"),
        "server-issue": forms.get("onsite_support_form"),
        "tablet-mobile": forms.get("onsite_support_form"),
        "data-recovery": forms.get("onsite_support_form"),
        # Software -> Remote Support Form
        "software": forms.get("remote_support_form"),
        "os-crash": forms.get("remote_support_form"),
        "software-install": forms.get("remote_support_form"),
        "virus-malware": forms.get("remote_support_form"),
        "performance-issue": forms.get("remote_support_form"),
        "email-config": forms.get("remote_support_form"),
        "os-reinstall": forms.get("onsite_support_form"),
        # Network -> Remote Support Form
        "network": forms.get("remote_support_form"),
        "internet-down": forms.get("remote_support_form"),
        "vpn-issue": forms.get("remote_support_form"),
        "network-setup": forms.get("onsite_support_form"),
        "firewall-security": forms.get("remote_support_form"),
        # Peripherals -> On-Site Support Form
        "peripherals": forms.get("onsite_support_form"),
        "printer-issue": forms.get("onsite_support_form"),
        "monitor-issue": forms.get("onsite_support_form"),
        "ups-power": forms.get("onsite_support_form"),
        "cctv-surveillance": forms.get("onsite_support_form"),
        "scanner-copier": forms.get("onsite_support_form"),
        "access-control": forms.get("onsite_support_form"),
        # Service -> Installation Form
        "new-installation": forms.get("installation_form"),
        "upgrade-request": forms.get("onsite_support_form"),
        "preventive-maintenance": forms.get("onsite_support_form"),
        "device-relocation": forms.get("installation_form"),
        "asset-disposal": forms.get("general_inquiry_form"),
        # Warranty -> Warranty Claim Form
        "warranty-claim-oem": forms.get("warranty_claim_form"),
        "amc-support": forms.get("warranty_claim_form"),
        "non-warranty-repair": forms.get("warranty_claim_form"),
        # Commercial
        "amc-renewal": forms.get("quote_request_form"),
        "billing-dispute": forms.get("complaint_form"),
        # General
        "escalation": forms.get("complaint_form"),
        "training-request": forms.get("general_inquiry_form"),
        "general-inquiry": forms.get("general_inquiry_form"),
        "feedback": forms.get("feedback_form"),
        "complaint": forms.get("complaint_form"),
    }

    updated = 0
    async for topic in _db.ticket_help_topics.find(
        {"organization_id": org_id, "$or": [{"form_id": None}, {"form_id": ""}, {"form_id": {"$exists": False}}]},
        {"_id": 0, "id": 1, "slug": 1, "category": 1}
    ):
        form_id = form_map.get(topic.get("slug")) or form_map.get(topic.get("category"))
        if form_id:
            await _db.ticket_help_topics.update_one(
                {"id": topic["id"]},
                {"$set": {"form_id": form_id}}
            )
            updated += 1

    return {"message": f"Linked forms to {updated} help topics"}

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
    assigned: Optional[bool] = None,
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
    if status:
        query["current_stage_name"] = status
    if assigned is not None:
        if assigned:
            query["assigned_to_id"] = {"$ne": None}
            query["assigned_to_name"] = {"$ne": None}
        else:
            query["$or"] = [
                {"assigned_to_id": None},
                {"assigned_to_id": {"$exists": False}},
                {"assigned_to_name": None},
                {"assigned_to_name": {"$exists": False}}
            ]
    if search:
        search_conditions = [
            {"ticket_number": {"$regex": search, "$options": "i"}},
            {"subject": {"$regex": search, "$options": "i"}}
        ]
        if "$or" in query:
            query["$and"] = [{"$or": query.pop("$or")}, {"$or": search_conditions}]
        else:
            query["$or"] = search_conditions
    
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


@router.get("/ticketing/tickets/{ticket_id}/full")
async def get_ticket_full(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Get ticket with company, site, employee, device, repair history for calendar/detail views"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    company = None
    if ticket.get("company_id"):
        company = await _db.companies.find_one({"id": ticket["company_id"]}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "email": 1, "address": 1, "city": 1, "state": 1})

    site = None
    if ticket.get("site_id"):
        site = await _db.sites.find_one({"id": ticket["site_id"]}, {"_id": 0, "id": 1, "name": 1, "address": 1, "city": 1, "state": 1, "pincode": 1, "contact_name": 1, "contact_phone": 1})

    employee = None
    if ticket.get("employee_id"):
        employee = await _db.company_employees.find_one({"id": ticket["employee_id"]}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "email": 1, "designation": 1, "department": 1})

    device = None
    if ticket.get("device_id"):
        device = await _db.devices.find_one({"id": ticket["device_id"]}, {"_id": 0, "id": 1, "name": 1, "model": 1, "serial_number": 1, "manufacturer": 1, "device_type": 1, "warranty_end_date": 1, "warranty_status": 1, "purchase_date": 1, "ip_address": 1, "notes": 1})

    repair_history = []
    hq = {"organization_id": org_id, "is_deleted": {"$ne": True}, "id": {"$ne": ticket_id}}
    if ticket.get("device_id"):
        hq["device_id"] = ticket["device_id"]
    elif ticket.get("company_id"):
        hq["company_id"] = ticket["company_id"]
    if "device_id" in hq or "company_id" in hq:
        repair_history = await _db.tickets_v2.find(hq, {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "current_stage_name": 1, "priority_name": 1, "is_open": 1, "created_at": 1, "resolved_at": 1, "assigned_to_name": 1}).sort("created_at", -1).to_list(20)

    schedules = await _db.ticket_schedules.find({"ticket_id": ticket_id, "organization_id": org_id}, {"_id": 0}).sort("scheduled_at", -1).to_list(10)

    return {"ticket": ticket, "company": company, "site": site, "employee": employee, "device": device, "repair_history": repair_history, "schedules": schedules}




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
    
    # Get site name if provided
    site_name = data.site_name
    if data.site_id and not site_name:
        site = await _db.sites.find_one({"id": data.site_id}, {"_id": 0, "name": 1, "address": 1, "city": 1})
        if site:
            site_name = site.get("name", "")
            if site.get("city"):
                site_name += f", {site['city']}"
    
    # Get employee name if provided
    employee_name = data.employee_name
    if data.employee_id and not employee_name:
        emp = await _db.company_employees.find_one({"id": data.employee_id}, {"_id": 0, "name": 1})
        if emp:
            employee_name = emp.get("name")
    
    # Get device name if provided
    device_name = None
    device_warranty_type = None
    if data.device_id:
        device = await _db.devices.find_one({"id": data.device_id}, {"_id": 0, "name": 1, "display_name": 1, "brand": 1, "model": 1, "serial_number": 1, "warranty_end_date": 1, "company_id": 1})
        if device:
            device_name = device.get("display_name") or f"{device.get('brand','')} {device.get('model','')}".strip() or device.get("name")
            
            # Auto-detect warranty type
            from datetime import datetime as dt_cls, timezone as tz_cls, timedelta as td_cls
            now = dt_cls.now(tz_cls(td_cls(hours=5, minutes=30)))
            
            # Check AMC
            amc = await _db.amc_contracts.find_one(
                {"organization_id": org_id, "$or": [{"device_id": data.device_id}, {"company_id": device.get("company_id")}], "status": "active"},
                {"_id": 0, "end_date": 1, "amc_end_date": 1}
            )
            if amc:
                end_date = amc.get("end_date") or amc.get("amc_end_date")
                if end_date:
                    try:
                        end_dt = dt_cls.fromisoformat(str(end_date).replace('Z', '+00:00'))
                        if end_dt.tzinfo is None:
                            end_dt = end_dt.replace(tzinfo=tz_cls(td_cls(hours=5, minutes=30)))
                        if end_dt > now:
                            device_warranty_type = "amc"
                    except (ValueError, TypeError):
                        pass
            
            # Check brand warranty
            if not device_warranty_type and device.get("warranty_end_date"):
                try:
                    w_dt = dt_cls.fromisoformat(str(device["warranty_end_date"]).replace('Z', '+00:00'))
                    if w_dt.tzinfo is None:
                        w_dt = w_dt.replace(tzinfo=tz_cls(td_cls(hours=5, minutes=30)))
                    if w_dt > now:
                        device_warranty_type = "oem_warranty"
                except (ValueError, TypeError):
                    pass
            
            if not device_warranty_type:
                device_warranty_type = "non_warranty"
    
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
        site_id=data.site_id,
        site_name=site_name,
        custom_location=data.custom_location,
        employee_id=data.employee_id,
        employee_name=employee_name,
        contact=contact,
        device_id=data.device_id,
        device_name=device_name,
        device_description=data.device_description,
        device_warranty_type=device_warranty_type,
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
        # Get user details - check engineers first, then org members
        user = await _db.engineers.find_one({"id": data["assigned_to_id"]}, {"_id": 0, "name": 1, "email": 1})
        if not user:
            user = await _db.organization_members.find_one({"id": data["assigned_to_id"]}, {"_id": 0, "name": 1, "email": 1})
        if user:
            update_data["assigned_to_id"] = data["assigned_to_id"]
            update_data["assigned_to_name"] = user.get("name", user.get("email", ""))
            update_data["assignment_status"] = "pending"
            update_data["assigned_at"] = get_ist_isoformat()
            update_data["assignment_responded_at"] = None
            timeline_entry["description"] = f"Assigned to {update_data['assigned_to_name']} (pending acceptance)"
    
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
            # Try staff_users
            engineer = await _db.staff_users.find_one(
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
            update_data["assignment_status"] = "pending"
            update_data["assigned_at"] = get_ist_isoformat()
            update_data["assignment_responded_at"] = None
    
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
    
    base_q = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    # Total tickets
    total = await _db.tickets_v2.count_documents(base_q)
    open_count = await _db.tickets_v2.count_documents({**base_q, "is_open": True})
    closed_count = await _db.tickets_v2.count_documents({**base_q, "is_open": False})
    
    # Unassigned count
    unassigned_count = await _db.tickets_v2.count_documents({
        **base_q,
        "$or": [
            {"assigned_to_id": None},
            {"assigned_to_id": {"$exists": False}},
            {"assigned_to_name": None},
            {"assigned_to_name": {"$exists": False}}
        ]
    })
    
    # By priority
    priority_pipeline = [
        {"$match": {**base_q, "is_open": True}},
        {"$group": {"_id": "$priority_name", "count": {"$sum": 1}}}
    ]
    by_priority = {doc["_id"]: doc["count"] async for doc in _db.tickets_v2.aggregate(priority_pipeline)}
    
    # By help topic
    topic_pipeline = [
        {"$match": {**base_q, "is_open": True}},
        {"$group": {"_id": "$help_topic_name", "count": {"$sum": 1}}}
    ]
    by_topic = {doc["_id"]: doc["count"] async for doc in _db.tickets_v2.aggregate(topic_pipeline)}
    
    # By stage (for filter pills)
    stage_pipeline = [
        {"$match": {**base_q, "is_deleted": {"$ne": True}}},
        {"$group": {"_id": "$current_stage_name", "count": {"$sum": 1}}}
    ]
    by_stage = {doc["_id"]: doc["count"] async for doc in _db.tickets_v2.aggregate(stage_pipeline)}
    
    # Pending tasks
    pending_tasks = await _db.ticket_tasks.count_documents({
        "organization_id": org_id,
        "status": "pending"
    })
    
    return {
        "total": total,
        "open": open_count,
        "closed": closed_count,
        "unassigned": unassigned_count,
        "by_priority": by_priority,
        "by_topic": by_topic,
        "by_stage": by_stage,
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
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    
    # Also include staff_users who can be assigned (technicians/field engineers)
    existing_emails = {e.get("email") for e in engineers}
    staff_engineers = await _db.staff_users.find(
        {"organization_id": org_id, "state": "active", "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    for s in staff_engineers:
        if s.get("email") not in existing_emails:
            s["is_active"] = True
            s["source"] = "staff_user"
            engineers.append(s)
    
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


@router.get("/ticketing/engineers/{engineer_id}/available-slots")
async def get_available_slots(
    engineer_id: str,
    date: str = Query(..., description="Date in YYYY-MM-DD format"),
    admin: dict = Depends(get_current_admin)
):
    """Get available 30-min time slots for an engineer on a given date.
    Each existing booking blocks its start time + 1 hour (buffer).
    """
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    # Get engineer details including working hours and holidays
    engineer = await _db.engineers.find_one(
        {"id": engineer_id, "organization_id": org_id},
        {"_id": 0, "id": 1, "name": 1, "working_hours": 1, "holidays": 1}
    )
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found")

    # Check if date is a holiday
    holidays = engineer.get("holidays", [])
    if date in holidays:
        return {"date": date, "is_holiday": True, "is_working_day": False, "slots": [], "message": "This is a holiday for this technician"}

    # Check working hours for the day of week
    from datetime import datetime as dt_cls
    date_obj = dt_cls.strptime(date, "%Y-%m-%d")
    day_name = date_obj.strftime("%A").lower()

    working_hours = engineer.get("working_hours", {})
    if not working_hours:
        # Default working hours if not configured
        working_hours = {
            "monday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "tuesday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "wednesday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "thursday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "friday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "saturday": {"is_working": True, "start": "09:00", "end": "14:00"},
            "sunday": {"is_working": False, "start": "09:00", "end": "18:00"},
        }
    day_schedule = working_hours.get(day_name, {"is_working": True, "start": "09:00", "end": "18:00"})

    if not day_schedule.get("is_working", False):
        return {"date": date, "is_holiday": False, "is_working_day": False, "slots": [], "message": f"Not a working day ({day_name.title()})"}

    work_start = day_schedule.get("start", "09:00")
    work_end = day_schedule.get("end", "18:00")

    # Parse working hours into minutes from midnight
    ws_h, ws_m = map(int, work_start.split(":"))
    we_h, we_m = map(int, work_end.split(":"))
    work_start_mins = ws_h * 60 + ws_m
    work_end_mins = we_h * 60 + we_m

    # Generate 30-min slots within working hours
    all_slots = []
    t = work_start_mins
    while t < work_end_mins:
        h, m = divmod(t, 60)
        all_slots.append(f"{h:02d}:{m:02d}")
        t += 30

    # Get existing bookings for this date
    date_start = f"{date}T00:00:00"
    date_end = f"{date}T23:59:59"

    schedules = await _db.ticket_schedules.find({
        "engineer_id": engineer_id,
        "organization_id": org_id,
        "scheduled_at": {"$gte": date_start, "$lte": date_end},
        "status": {"$ne": "cancelled"}
    }, {"_id": 0, "scheduled_at": 1, "scheduled_end_at": 1, "ticket_number": 1, "company_name": 1, "subject": 1}).to_list(100)

    scheduled_tickets = await _db.tickets_v2.find({
        "assigned_to_id": engineer_id,
        "organization_id": org_id,
        "scheduled_at": {"$gte": date_start, "$lte": date_end},
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "scheduled_at": 1, "scheduled_end_at": 1, "ticket_number": 1, "company_name": 1, "subject": 1}).to_list(100)

    # Collect all booked time ranges (start_mins, end_mins_with_buffer)
    blocked_ranges = []
    bookings_info = []
    for booking in schedules + scheduled_tickets:
        sched_at = booking.get("scheduled_at", "")
        if not sched_at or not sched_at.startswith(date):
            continue
        # Parse start time
        try:
            time_part = sched_at[11:16]  # HH:MM
            bh, bm = map(int, time_part.split(":"))
            booking_start = bh * 60 + bm
        except (ValueError, IndexError):
            continue

        # Parse end time if available, else assume booking_start + 1hr
        sched_end = booking.get("scheduled_end_at", "")
        if sched_end and sched_end.startswith(date):
            try:
                eh, em = map(int, sched_end[11:16].split(":"))
                booking_end = eh * 60 + em
            except (ValueError, IndexError):
                booking_end = booking_start + 60
        else:
            booking_end = booking_start + 60

        # Block from booking_start to booking_end + 60 mins (1hr gap)
        blocked_end = booking_end + 60
        blocked_ranges.append((booking_start, blocked_end))
        bookings_info.append({
            "time": time_part,
            "ticket_number": booking.get("ticket_number", ""),
            "company_name": booking.get("company_name", ""),
            "subject": booking.get("subject", ""),
            "start_mins": booking_start,
            "end_mins": booking_end
        })

    # Build slot list with availability
    slots = []
    for slot_time in all_slots:
        sh, sm = map(int, slot_time.split(":"))
        slot_mins = sh * 60 + sm

        available = True
        blocked_by = None
        for bstart, bend in blocked_ranges:
            if bstart <= slot_mins < bend:
                available = False
                # Find which booking blocked it
                for bi in bookings_info:
                    if bi["start_mins"] <= slot_mins < bi["end_mins"] + 60:
                        blocked_by = f"#{bi['ticket_number']} - {bi['company_name'] or bi['subject']}"
                        break
                break

        slots.append({
            "time": slot_time,
            "available": available,
            "blocked_by": blocked_by
        })

    return {
        "date": date,
        "is_holiday": False,
        "is_working_day": True,
        "work_start": work_start,
        "work_end": work_end,
        "slots": slots,
        "bookings": bookings_info
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


# ============================================================
# TICKET NOTIFICATIONS (WhatsApp + Email)
# ============================================================

@router.post("/ticketing/tickets/{ticket_id}/send-notification")
async def send_ticket_notification(
    ticket_id: str,
    data: dict = Body(...),
    admin: dict = Depends(get_current_admin)
):
    """Send email notification for a ticket based on current stage.
    Body: { "notification_type": "assigned|awaiting_parts|billing|quote|general" }
    Returns: { "success": true, "wa_phone": "...", "wa_message": "..." } for WhatsApp link generation on frontend.
    """
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import logging
    logger = logging.getLogger("ticketing")

    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "timeline": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    notification_type = data.get("notification_type", "general")

    # Get settings for phone numbers and emails
    settings = await _db.settings.find_one(
        {"organization_id": org_id}, {"_id": 0}
    )
    if not settings:
        settings = {}

    # Get engineer phone if assigned
    engineer_phone = None
    eng = None
    if ticket.get("assigned_to_id"):
        # Check engineers collection first, then staff_users
        eng = await _db.engineers.find_one(
            {"id": ticket["assigned_to_id"], "organization_id": org_id},
            {"_id": 0, "phone": 1, "name": 1, "email": 1}
        )
        if not eng or not eng.get("phone"):
            eng2 = await _db.staff_users.find_one(
                {"id": ticket["assigned_to_id"], "organization_id": org_id},
                {"_id": 0, "phone": 1, "name": 1, "email": 1}
            )
            if eng2:
                engineer_phone = eng2.get("phone")
                if not eng:
                    eng = eng2
            elif eng:
                engineer_phone = eng.get("phone")
        else:
            engineer_phone = eng.get("phone")

    # Build message content based on notification type
    ticket_num = ticket.get("ticket_number", "")
    subject = ticket.get("subject", "")
    company = ticket.get("company_name", "N/A")
    site = ticket.get("site_name") or "N/A"
    contact_name = ticket.get("contact_name") or ticket.get("employee_name") or "N/A"
    contact_phone = ticket.get("contact_phone") or "N/A"
    stage = ticket.get("current_stage_name", "")
    engineer_name = ticket.get("assigned_to_name") or "Unassigned"
    priority = ticket.get("priority_name", "medium")
    description = ticket.get("description") or ""
    scheduled_at = ticket.get("scheduled_at") or ""

    # Diagnosis info
    diag = ticket.get("diagnosis") or {}
    diag_text = diag.get("findings", "") if diag else ""

    # Parts info
    parts = ticket.get("parts_required") or []
    parts_text = ", ".join([f"{p.get('name','')} x{p.get('quantity',1)}" for p in parts]) if parts else "None"

    wa_phone = ""
    wa_message = ""
    email_to = []
    email_subject = ""
    email_html = ""

    if notification_type == "assigned":
        wa_phone = engineer_phone or ""
        wa_message = (
            f"*Job Assignment - #{ticket_num}*\n\n"
            f"Subject: {subject}\n"
            f"Company: {company}\n"
            f"Site: {site}\n"
            f"Contact: {contact_name}\n"
            f"Contact Phone: {contact_phone}\n"
            f"Priority: {priority}\n"
            f"Stage: {stage}\n"
        )
        if scheduled_at:
            wa_message += f"Scheduled: {scheduled_at}\n"
        if description:
            wa_message += f"\nDescription: {description[:200]}\n"
        wa_message += f"\nPlease check your portal for full details."

        email_to = [eng.get("email")] if eng and eng.get("email") else []
        email_subject = f"Job Assignment: #{ticket_num} - {company}"
        email_html = _build_notification_email(ticket, "assigned", engineer_name)

    elif notification_type == "awaiting_parts":
        wa_phone = settings.get("parts_order_phone", "")
        wa_message = (
            f"*Parts Required - Job #{ticket_num}*\n\n"
            f"Company: {company}\n"
            f"Engineer: {engineer_name}\n"
            f"Stage: {stage}\n\n"
            f"Parts Needed:\n{parts_text}\n"
        )
        if diag_text:
            wa_message += f"\nDiagnosis: {diag_text[:200]}\n"
        wa_message += f"\nPlease arrange parts and update the portal."

        email_to = settings.get("parts_order_emails", []) or []
        email_subject = f"Parts Required: Job #{ticket_num} - {company}"
        email_html = _build_notification_email(ticket, "awaiting_parts", engineer_name)

    elif notification_type == "billing":
        wa_phone = settings.get("billing_team_phone", "")
        wa_message = (
            f"*Billing Pending - Job #{ticket_num}*\n\n"
            f"Company: {company}\n"
            f"Engineer: {engineer_name}\n"
            f"Parts Used:\n{parts_text}\n\n"
            f"Please generate invoice and update the portal."
        )
        email_to = settings.get("billing_emails", []) or []
        email_subject = f"Billing Pending: Job #{ticket_num} - {company}"
        email_html = _build_notification_email(ticket, "billing", engineer_name)

    elif notification_type == "quote":
        wa_phone = settings.get("quote_team_phone", "")
        wa_message = (
            f"*Quotation Required - Job #{ticket_num}*\n\n"
            f"Company: {company}\n"
            f"Contact: {contact_name} ({contact_phone})\n"
            f"Engineer: {engineer_name}\n\n"
            f"Parts/Items:\n{parts_text}\n\n"
            f"Please prepare quotation and update the portal."
        )
        email_to = settings.get("quote_team_emails", []) or []
        email_subject = f"Quotation Required: Job #{ticket_num} - {company}"
        email_html = _build_notification_email(ticket, "quote", engineer_name)

    else:  # general
        wa_phone = settings.get("backend_team_phone", "")
        wa_message = (
            f"*Ticket Update - #{ticket_num}*\n\n"
            f"Subject: {subject}\n"
            f"Company: {company}\n"
            f"Stage: {stage}\n"
            f"Engineer: {engineer_name}\n"
            f"Priority: {priority}\n\n"
            f"Please check the portal for details."
        )
        email_to = settings.get("billing_emails", []) or []
        email_subject = f"Ticket Update: #{ticket_num} - {stage}"
        email_html = _build_notification_email(ticket, "general", engineer_name)

    # Send email if we have recipients and SMTP is configured
    email_sent = False
    if email_to:
        try:
            smtp_settings = await _db.settings.find_one(
                {"organization_id": org_id},
                {"_id": 0, "smtp_host": 1, "smtp_port": 1, "smtp_user": 1, "smtp_pass": 1, "smtp_from": 1}
            )
            if smtp_settings and smtp_settings.get("smtp_host"):
                msg = MIMEMultipart("alternative")
                msg["Subject"] = email_subject
                msg["From"] = smtp_settings.get("smtp_from", smtp_settings.get("smtp_user", ""))
                msg["To"] = ", ".join(email_to)
                msg.attach(MIMEText(email_html, "html"))

                with smtplib.SMTP(smtp_settings["smtp_host"], int(smtp_settings.get("smtp_port", 587)), timeout=10) as server:
                    server.starttls()
                    server.login(smtp_settings["smtp_user"], smtp_settings["smtp_pass"])
                    server.send_message(msg)
                email_sent = True
                logger.info(f"Notification email sent to {email_to} for ticket {ticket_num}")
            else:
                logger.info("SMTP not configured, skipping email")
        except Exception as e:
            logger.warning(f"Failed to send notification email: {e}")

    # Add timeline entry
    await _db.tickets_v2.update_one(
        {"id": ticket_id},
        {
            "$push": {"timeline": {
                "id": str(uuid.uuid4()),
                "type": "notification",
                "description": f"Notification sent ({notification_type}){' - Email sent to ' + ', '.join(email_to) if email_sent else ''}",
                "user_name": admin.get("name", "Admin"),
                "is_internal": True,
                "created_at": get_ist_isoformat()
            }},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )

    return {
        "success": True,
        "wa_phone": wa_phone or "",
        "wa_message": wa_message,
        "email_sent": email_sent,
        "email_to": email_to,
        "notification_type": notification_type
    }


def _build_notification_email(ticket: dict, ntype: str, engineer_name: str) -> str:
    """Build HTML email for ticket notifications."""
    ticket_num = ticket.get("ticket_number", "")
    subject = ticket.get("subject", "")
    company = ticket.get("company_name", "N/A")
    site = ticket.get("site_name") or "N/A"
    contact_name = ticket.get("contact_name") or ticket.get("employee_name") or "N/A"
    contact_phone = ticket.get("contact_phone") or "N/A"
    stage = ticket.get("current_stage_name", "")
    priority = ticket.get("priority_name", "medium")
    description = ticket.get("description") or "N/A"

    parts = ticket.get("parts_required") or []
    parts_html = ""
    if parts:
        parts_html = "<h3 style='margin-top:16px'>Parts:</h3><ul>"
        for p in parts:
            parts_html += f"<li>{p.get('name','')} x {p.get('quantity',1)}{' - ' + p.get('notes','') if p.get('notes') else ''}</li>"
        parts_html += "</ul>"

    diag = ticket.get("diagnosis") or {}
    diag_html = ""
    if diag.get("findings"):
        diag_html = f"<h3 style='margin-top:16px'>Diagnosis:</h3><p>{diag['findings']}</p>"

    titles = {
        "assigned": "Job Assignment Notification",
        "awaiting_parts": "Parts Required Notification",
        "billing": "Billing Pending Notification",
        "quote": "Quotation Required Notification",
        "general": "Ticket Update Notification"
    }

    return f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto">
        <h2 style="color:#0F62FE">{titles.get(ntype, 'Ticket Notification')}</h2>
        <table style="width:100%;margin:16px 0;border-collapse:collapse">
            <tr><td style="padding:4px 8px;font-weight:bold;width:140px">Job #</td><td style="padding:4px 8px">{ticket_num}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold">Subject</td><td style="padding:4px 8px">{subject}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold">Company</td><td style="padding:4px 8px">{company}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold">Site</td><td style="padding:4px 8px">{site}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold">Contact</td><td style="padding:4px 8px">{contact_name} ({contact_phone})</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold">Engineer</td><td style="padding:4px 8px">{engineer_name}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold">Stage</td><td style="padding:4px 8px">{stage}</td></tr>
            <tr><td style="padding:4px 8px;font-weight:bold">Priority</td><td style="padding:4px 8px">{priority}</td></tr>
        </table>
        <p><strong>Description:</strong> {description[:500]}</p>
        {diag_html}
        {parts_html}
        <p style="margin-top:16px;color:#64748b;font-size:13px">Please check the portal for full details and take necessary action.</p>
    </div>
    """


# ============================================================
# CUSTOMER QUOTATION APPROVAL (Public - No Auth)
# ============================================================

@router.post("/ticketing/tickets/{ticket_id}/send-quotation-email")
async def send_quotation_approval_email(
    ticket_id: str,
    data: dict = Body(...),
    admin: dict = Depends(get_current_admin)
):
    """Send quotation approval email to customer with approve/deny buttons.
    Body: { "customer_email": "...", "customer_name": "...", "quotation_details": "..." }
    """
    import smtplib, hashlib, hmac
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id},
        {"_id": 0, "timeline": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    customer_email = data.get("customer_email", "")
    customer_name = data.get("customer_name", ticket.get("contact_name") or "Customer")

    if not customer_email:
        raise HTTPException(status_code=400, detail="Customer email is required")

    # Create approval token (store in DB for validation)
    approval_token = str(uuid.uuid4())
    await _db.quotation_approvals.insert_one({
        "token": approval_token,
        "ticket_id": ticket_id,
        "organization_id": org_id,
        "customer_email": customer_email,
        "status": "pending",
        "created_at": get_ist_isoformat(),
        "expires_at": (datetime.now(timezone(timedelta(hours=5, minutes=30))) + timedelta(days=7)).isoformat(),
    })

    # Build quotation details
    ticket_num = ticket.get("ticket_number", "")
    subject = ticket.get("subject", "")
    company = ticket.get("company_name", "")
    parts = ticket.get("parts_required") or []
    parts_html = ""
    total = 0
    if parts:
        parts_html = "<table style='width:100%;border-collapse:collapse;margin:16px 0'>"
        parts_html += "<tr style='background:#f8fafc'><th style='text-align:left;padding:8px;border:1px solid #e2e8f0'>Item</th><th style='text-align:center;padding:8px;border:1px solid #e2e8f0'>Qty</th><th style='text-align:right;padding:8px;border:1px solid #e2e8f0'>Price</th><th style='text-align:right;padding:8px;border:1px solid #e2e8f0'>Total</th></tr>"
        for p in parts:
            qty = p.get('quantity', 1)
            price = p.get('unit_price', 0)
            line_total = qty * price
            total += line_total
            parts_html += f"<tr><td style='padding:8px;border:1px solid #e2e8f0'>{p.get('name','')}</td><td style='text-align:center;padding:8px;border:1px solid #e2e8f0'>{qty}</td><td style='text-align:right;padding:8px;border:1px solid #e2e8f0'>Rs.{price:,.2f}</td><td style='text-align:right;padding:8px;border:1px solid #e2e8f0'>Rs.{line_total:,.2f}</td></tr>"
        parts_html += f"<tr style='font-weight:bold;background:#f8fafc'><td colspan='3' style='text-align:right;padding:8px;border:1px solid #e2e8f0'>Total</td><td style='text-align:right;padding:8px;border:1px solid #e2e8f0'>Rs.{total:,.2f}</td></tr></table>"

    additional = data.get("quotation_details", "")

    # Get the base URL from settings or use the org domain
    settings = await _db.settings.find_one({"organization_id": org_id}, {"_id": 0})
    base_url = os.environ.get("BASE_URL", "")
    if not base_url:
        # Fallback to the request origin
        base_url = ""

    approve_url = f"{base_url}/api/ticketing/quotation-response/{approval_token}?action=approve"
    reject_url = f"{base_url}/api/ticketing/quotation-response/{approval_token}?action=reject"

    html = f"""
    <div style="font-family:sans-serif;max-width:600px;margin:0 auto;background:#fff;padding:24px">
        <h2 style="color:#0F62FE;margin-bottom:8px">Quotation for Approval</h2>
        <p style="color:#64748b;margin-top:0">Job #{ticket_num} - {subject}</p>
        
        <table style="width:100%;margin:16px 0;border-collapse:collapse">
            <tr><td style="padding:6px 0;color:#64748b;width:120px">Company</td><td style="padding:6px 0;font-weight:500">{company}</td></tr>
            <tr><td style="padding:6px 0;color:#64748b">Ticket #</td><td style="padding:6px 0;font-weight:500">{ticket_num}</td></tr>
            <tr><td style="padding:6px 0;color:#64748b">Subject</td><td style="padding:6px 0;font-weight:500">{subject}</td></tr>
        </table>

        {parts_html if parts_html else '<p style="color:#64748b">No itemized pricing available. Please see details below.</p>'}
        
        {f'<div style="background:#f8fafc;padding:16px;border-radius:8px;margin:16px 0"><p style="margin:0;color:#334155">{additional}</p></div>' if additional else ''}

        <div style="margin:32px 0;text-align:center">
            <a href="{approve_url}" style="display:inline-block;padding:12px 32px;background:#10B981;color:white;text-decoration:none;border-radius:8px;font-weight:600;margin-right:16px">Approve Quotation</a>
            <a href="{reject_url}" style="display:inline-block;padding:12px 32px;background:#EF4444;color:white;text-decoration:none;border-radius:8px;font-weight:600">Reject Quotation</a>
        </div>

        <p style="font-size:12px;color:#94a3b8;text-align:center">This link expires in 7 days. Please respond at the earliest.</p>
        <hr style="border:none;border-top:1px solid #e2e8f0;margin:24px 0" />
        <p style="font-size:12px;color:#94a3b8;text-align:center">Powered by aftersales.support</p>
    </div>
    """

    # Send email
    email_sent = False
    try:
        smtp_settings = await _db.settings.find_one(
            {"organization_id": org_id},
            {"_id": 0, "smtp_host": 1, "smtp_port": 1, "smtp_user": 1, "smtp_pass": 1, "smtp_from": 1}
        )
        if smtp_settings and smtp_settings.get("smtp_host"):
            msg = MIMEMultipart("alternative")
            msg["Subject"] = f"Quotation Approval Required - Job #{ticket_num}"
            msg["From"] = smtp_settings.get("smtp_from", smtp_settings.get("smtp_user", ""))
            msg["To"] = customer_email
            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(smtp_settings["smtp_host"], int(smtp_settings.get("smtp_port", 587)), timeout=10) as server:
                server.starttls()
                server.login(smtp_settings["smtp_user"], smtp_settings["smtp_pass"])
                server.send_message(msg)
            email_sent = True
    except Exception as e:
        import logging
        logging.getLogger("ticketing").warning(f"Failed to send quotation email: {e}")

    # Add timeline entry
    await _db.tickets_v2.update_one(
        {"id": ticket_id},
        {"$push": {"timeline": {
            "id": str(uuid.uuid4()),
            "type": "quotation_sent",
            "description": f"Quotation approval email sent to {customer_email}" + (" (delivered)" if email_sent else " (SMTP not configured - use approval links manually)"),
            "user_name": admin.get("name", "Admin"),
            "is_internal": False,
            "created_at": get_ist_isoformat()
        }}, "$set": {"updated_at": get_ist_isoformat()}}
    )

    return {
        "success": True,
        "email_sent": email_sent,
        "approval_token": approval_token,
        "approve_url": approve_url,
        "reject_url": reject_url,
        "customer_email": customer_email
    }


@router.get("/ticketing/quotation-response/{token}")
async def quotation_response(token: str, action: str = Query(...)):
    """Public endpoint - customer clicks approve/reject link from email.
    No authentication required. Returns HTML confirmation page.
    """
    from fastapi.responses import HTMLResponse
    
    if action not in ("approve", "reject"):
        return HTMLResponse("<h2>Invalid action</h2>", status_code=400)

    approval = await _db.quotation_approvals.find_one({"token": token}, {"_id": 0})
    if not approval:
        return HTMLResponse("""
        <div style="font-family:sans-serif;max-width:500px;margin:80px auto;text-align:center">
            <h2 style="color:#EF4444">Invalid or Expired Link</h2>
            <p style="color:#64748b">This quotation approval link is no longer valid.</p>
        </div>
        """, status_code=404)

    # Check if already responded
    if approval.get("status") != "pending":
        return HTMLResponse(f"""
        <div style="font-family:sans-serif;max-width:500px;margin:80px auto;text-align:center">
            <h2 style="color:#F59E0B">Already Responded</h2>
            <p style="color:#64748b">You have already {approval['status']} this quotation.</p>
        </div>
        """)

    # Check expiry
    if approval.get("expires_at"):
        try:
            exp = datetime.fromisoformat(approval["expires_at"])
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone(timedelta(hours=5, minutes=30)))
            if datetime.now(timezone(timedelta(hours=5, minutes=30))) > exp:
                return HTMLResponse("""
                <div style="font-family:sans-serif;max-width:500px;margin:80px auto;text-align:center">
                    <h2 style="color:#EF4444">Link Expired</h2>
                    <p style="color:#64748b">This approval link has expired. Please contact the service team.</p>
                </div>
                """)
        except (ValueError, TypeError):
            pass

    # Update approval status
    new_status = "approved" if action == "approve" else "rejected"
    await _db.quotation_approvals.update_one(
        {"token": token},
        {"$set": {"status": new_status, "responded_at": get_ist_isoformat()}}
    )

    # Update ticket stage
    ticket_id = approval["ticket_id"]
    org_id = approval["organization_id"]

    ticket = await _db.tickets_v2.find_one({"id": ticket_id}, {"_id": 0, "workflow": 1, "current_stage_id": 1})

    # Find appropriate stage based on action
    new_stage_name = "Customer Approved" if action == "approve" else "Customer Rejected"
    new_stage_id = None
    if ticket and ticket.get("workflow"):
        for stage in ticket["workflow"].get("stages", []):
            if stage.get("name") == new_stage_name or stage.get("slug") == new_stage_name.lower().replace(" ", "_"):
                new_stage_id = stage["id"]
                break

    update_data = {
        "current_stage_name": new_stage_name,
        "is_open": action == "approve",
        "updated_at": get_ist_isoformat()
    }
    if new_stage_id:
        update_data["current_stage_id"] = new_stage_id

    await _db.tickets_v2.update_one(
        {"id": ticket_id},
        {
            "$set": update_data,
            "$push": {"timeline": {
                "id": str(uuid.uuid4()),
                "type": "quotation_response",
                "description": f"Customer {new_status} the quotation via email",
                "user_name": approval.get("customer_email", "Customer"),
                "is_internal": False,
                "created_at": get_ist_isoformat()
            }}
        }
    )

    # HTML response
    if action == "approve":
        html = """
        <div style="font-family:sans-serif;max-width:500px;margin:80px auto;text-align:center">
            <div style="background:#ECFDF5;border-radius:50%;width:80px;height:80px;display:flex;align-items:center;justify-content:center;margin:0 auto 24px">
                <svg width="40" height="40" fill="none" stroke="#10B981" stroke-width="2" viewBox="0 0 24 24"><path d="M5 13l4 4L19 7"/></svg>
            </div>
            <h2 style="color:#10B981;margin-bottom:8px">Quotation Approved!</h2>
            <p style="color:#64748b">Thank you for approving the quotation. Our team will proceed with the work immediately.</p>
            <p style="color:#94a3b8;font-size:13px;margin-top:24px">You may close this window.</p>
        </div>
        """
    else:
        html = """
        <div style="font-family:sans-serif;max-width:500px;margin:80px auto;text-align:center">
            <div style="background:#FEF2F2;border-radius:50%;width:80px;height:80px;display:flex;align-items:center;justify-content:center;margin:0 auto 24px">
                <svg width="40" height="40" fill="none" stroke="#EF4444" stroke-width="2" viewBox="0 0 24 24"><path d="M18 6L6 18M6 6l12 12"/></svg>
            </div>
            <h2 style="color:#EF4444;margin-bottom:8px">Quotation Rejected</h2>
            <p style="color:#64748b">The quotation has been rejected. Our team will reach out for further discussion.</p>
            <p style="color:#94a3b8;font-size:13px;margin-top:24px">You may close this window.</p>
        </div>
        """

    return HTMLResponse(html)
