"""
Ticketing Configuration Routes
API endpoints for managing service ticket configuration
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional, List
from datetime import datetime, timezone
import uuid

from database import db
from models.ticketing_config import (
    ServiceMasterCreate, ServiceMasterUpdate, ServiceMasterResponse, ServiceMasterType,
    HelpTopicCreate, HelpTopicUpdate, HelpTopicResponse,
    WorkflowRuleCreate, WorkflowRuleUpdate, WorkflowRuleResponse,
    NotificationSettingCreate, NotificationSettingUpdate, NotificationSettingResponse,
    ApprovalSettingCreate, ApprovalSettingResponse
)

router = APIRouter(prefix="/ticketing-config", tags=["Ticketing Configuration"])


# =============================================================================
# SERVICE MASTERS
# =============================================================================

@router.get("/masters")
async def list_service_masters(
    master_type: Optional[ServiceMasterType] = None,
    is_active: Optional[bool] = None,
    admin: dict = Depends(lambda: None)
):
    """List all service masters, optionally filtered by type"""
    query = {"organization_id": admin["organization_id"]}
    
    if master_type:
        query["master_type"] = master_type.value
    if is_active is not None:
        query["is_active"] = is_active
    
    masters = await db.service_masters.find(query).sort("sort_order", 1).to_list(500)
    
    return {
        "masters": [{**m, "id": str(m["_id"])} for m in masters if "_id" in m]
    }


@router.post("/masters")
async def create_service_master(
    data: ServiceMasterCreate,
    admin: dict = Depends(lambda: None)
):
    """Create a new service master"""
    master_id = str(uuid.uuid4())
    
    # Generate code if not provided
    code = data.code or data.name.upper().replace(" ", "_")[:20]
    
    master = {
        "id": master_id,
        "organization_id": admin["organization_id"],
        "master_type": data.master_type.value,
        "name": data.name,
        "code": code,
        "description": data.description,
        "color": data.color,
        "icon": data.icon,
        "sort_order": data.sort_order,
        "is_active": data.is_active,
        "is_default": data.is_default,
        "is_system": False,
        "metadata": data.metadata,
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["id"]
    }
    
    await db.service_masters.insert_one(master)
    
    return {"id": master_id, "message": "Service master created", **master}


@router.put("/masters/{master_id}")
async def update_service_master(
    master_id: str,
    data: ServiceMasterUpdate,
    admin: dict = Depends(lambda: None)
):
    """Update a service master"""
    master = await db.service_masters.find_one({
        "id": master_id,
        "organization_id": admin["organization_id"]
    })
    
    if not master:
        raise HTTPException(status_code=404, detail="Service master not found")
    
    if master.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot modify system masters")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin["id"]
    
    await db.service_masters.update_one(
        {"id": master_id},
        {"$set": update_data}
    )
    
    return {"message": "Service master updated"}


@router.delete("/masters/{master_id}")
async def delete_service_master(
    master_id: str,
    admin: dict = Depends(lambda: None)
):
    """Delete a service master"""
    master = await db.service_masters.find_one({
        "id": master_id,
        "organization_id": admin["organization_id"]
    })
    
    if not master:
        raise HTTPException(status_code=404, detail="Service master not found")
    
    if master.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot delete system masters")
    
    await db.service_masters.delete_one({"id": master_id})
    
    return {"message": "Service master deleted"}


@router.post("/masters/seed-defaults")
async def seed_default_masters(
    admin: dict = Depends(lambda: None)
):
    """Seed default service masters for the organization"""
    org_id = admin["organization_id"]
    
    # Check if already seeded
    existing = await db.service_masters.count_documents({"organization_id": org_id})
    if existing > 0:
        return {"message": "Defaults already exist", "count": existing}
    
    defaults = [
        # Ticket Statuses
        {"master_type": "ticket_status", "name": "New", "code": "NEW", "color": "#6B7280", "sort_order": 1, "is_default": True},
        {"master_type": "ticket_status", "name": "Assigned", "code": "ASSIGNED", "color": "#3B82F6", "sort_order": 2},
        {"master_type": "ticket_status", "name": "In Progress", "code": "IN_PROGRESS", "color": "#F59E0B", "sort_order": 3},
        {"master_type": "ticket_status", "name": "Pending Parts", "code": "PENDING_PARTS", "color": "#F97316", "sort_order": 4},
        {"master_type": "ticket_status", "name": "Completed", "code": "COMPLETED", "color": "#10B981", "sort_order": 5},
        {"master_type": "ticket_status", "name": "Closed", "code": "CLOSED", "color": "#059669", "sort_order": 6},
        {"master_type": "ticket_status", "name": "Cancelled", "code": "CANCELLED", "color": "#EF4444", "sort_order": 7},
        
        # Priorities
        {"master_type": "priority", "name": "Low", "code": "LOW", "color": "#6B7280", "sort_order": 1},
        {"master_type": "priority", "name": "Medium", "code": "MEDIUM", "color": "#F59E0B", "sort_order": 2, "is_default": True},
        {"master_type": "priority", "name": "High", "code": "HIGH", "color": "#F97316", "sort_order": 3},
        {"master_type": "priority", "name": "Critical", "code": "CRITICAL", "color": "#EF4444", "sort_order": 4},
        
        # Visit Types
        {"master_type": "visit_type", "name": "On-Site", "code": "ONSITE", "sort_order": 1, "is_default": True},
        {"master_type": "visit_type", "name": "Remote", "code": "REMOTE", "sort_order": 2},
        {"master_type": "visit_type", "name": "Pickup", "code": "PICKUP", "sort_order": 3},
        {"master_type": "visit_type", "name": "Delivery", "code": "DELIVERY", "sort_order": 4},
        
        # Service Categories
        {"master_type": "service_category", "name": "Warranty", "code": "WARRANTY", "color": "#10B981", "sort_order": 1},
        {"master_type": "service_category", "name": "AMC", "code": "AMC", "color": "#3B82F6", "sort_order": 2},
        {"master_type": "service_category", "name": "Chargeable", "code": "CHARGEABLE", "color": "#F59E0B", "sort_order": 3},
        {"master_type": "service_category", "name": "Free Service", "code": "FREE", "color": "#8B5CF6", "sort_order": 4},
        
        # Resolution Types
        {"master_type": "resolution_type", "name": "Fixed", "code": "FIXED", "sort_order": 1, "is_default": True},
        {"master_type": "resolution_type", "name": "Replaced", "code": "REPLACED", "sort_order": 2},
        {"master_type": "resolution_type", "name": "Workaround", "code": "WORKAROUND", "sort_order": 3},
        {"master_type": "resolution_type", "name": "Not Reproducible", "code": "NOT_REPRO", "sort_order": 4},
        {"master_type": "resolution_type", "name": "Duplicate", "code": "DUPLICATE", "sort_order": 5},
        {"master_type": "resolution_type", "name": "Won't Fix", "code": "WONT_FIX", "sort_order": 6},
        
        # Problem Types
        {"master_type": "problem_type", "name": "Hardware Issue", "code": "HARDWARE", "sort_order": 1},
        {"master_type": "problem_type", "name": "Software Issue", "code": "SOFTWARE", "sort_order": 2},
        {"master_type": "problem_type", "name": "Network Issue", "code": "NETWORK", "sort_order": 3},
        {"master_type": "problem_type", "name": "CCTV Issue", "code": "CCTV", "sort_order": 4},
        {"master_type": "problem_type", "name": "Printer Issue", "code": "PRINTER", "sort_order": 5},
        {"master_type": "problem_type", "name": "Installation", "code": "INSTALLATION", "sort_order": 6},
        {"master_type": "problem_type", "name": "Maintenance", "code": "MAINTENANCE", "sort_order": 7},
        {"master_type": "problem_type", "name": "Other", "code": "OTHER", "sort_order": 99},
    ]
    
    for d in defaults:
        d["id"] = str(uuid.uuid4())
        d["organization_id"] = org_id
        d["is_active"] = True
        d["is_system"] = True
        d["created_at"] = datetime.now(timezone.utc)
    
    await db.service_masters.insert_many(defaults)
    
    return {"message": "Default masters created", "count": len(defaults)}


# =============================================================================
# HELP TOPICS
# =============================================================================

@router.get("/help-topics")
async def list_help_topics(
    is_active: Optional[bool] = None,
    is_public: Optional[bool] = None,
    admin: dict = Depends(lambda: None)
):
    """List all help topics"""
    query = {"organization_id": admin["organization_id"]}
    
    if is_active is not None:
        query["is_active"] = is_active
    if is_public is not None:
        query["is_public"] = is_public
    
    topics = await db.help_topics.find(query).sort("sort_order", 1).to_list(200)
    
    # Build hierarchy
    topic_map = {}
    root_topics = []
    
    for t in topics:
        t["id"] = str(t.get("_id", t.get("id")))
        t["children"] = []
        topic_map[t["id"]] = t
    
    for t in topics:
        parent_id = t.get("parent_topic_id")
        if parent_id and parent_id in topic_map:
            topic_map[parent_id]["children"].append(t)
        else:
            root_topics.append(t)
    
    return {"topics": root_topics}


@router.get("/help-topics/{topic_id}")
async def get_help_topic(
    topic_id: str,
    admin: dict = Depends(lambda: None)
):
    """Get a single help topic with its form configuration"""
    topic = await db.help_topics.find_one({
        "id": topic_id,
        "organization_id": admin["organization_id"]
    })
    
    if not topic:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    topic["id"] = str(topic.get("_id", topic.get("id")))
    return topic


@router.post("/help-topics")
async def create_help_topic(
    data: HelpTopicCreate,
    admin: dict = Depends(lambda: None)
):
    """Create a new help topic"""
    topic_id = str(uuid.uuid4())
    
    topic = {
        "id": topic_id,
        "organization_id": admin["organization_id"],
        **data.dict(),
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["id"]
    }
    
    await db.help_topics.insert_one(topic)
    
    return {"id": topic_id, "message": "Help topic created"}


@router.put("/help-topics/{topic_id}")
async def update_help_topic(
    topic_id: str,
    data: HelpTopicUpdate,
    admin: dict = Depends(lambda: None)
):
    """Update a help topic"""
    topic = await db.help_topics.find_one({
        "id": topic_id,
        "organization_id": admin["organization_id"]
    })
    
    if not topic:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin["id"]
    
    await db.help_topics.update_one(
        {"id": topic_id},
        {"$set": update_data}
    )
    
    return {"message": "Help topic updated"}


@router.delete("/help-topics/{topic_id}")
async def delete_help_topic(
    topic_id: str,
    admin: dict = Depends(lambda: None)
):
    """Delete a help topic"""
    result = await db.help_topics.delete_one({
        "id": topic_id,
        "organization_id": admin["organization_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    # Also unlink any child topics
    await db.help_topics.update_many(
        {"parent_topic_id": topic_id},
        {"$set": {"parent_topic_id": None}}
    )
    
    return {"message": "Help topic deleted"}


@router.put("/help-topics/{topic_id}/form")
async def update_help_topic_form(
    topic_id: str,
    custom_fields: List[dict],
    admin: dict = Depends(lambda: None)
):
    """Update just the custom form fields of a help topic"""
    result = await db.help_topics.update_one(
        {"id": topic_id, "organization_id": admin["organization_id"]},
        {"$set": {
            "custom_fields": custom_fields,
            "updated_at": datetime.now(timezone.utc)
        }}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Help topic not found")
    
    return {"message": "Form updated"}


# =============================================================================
# WORKFLOW RULES
# =============================================================================

@router.get("/workflow-rules")
async def list_workflow_rules(
    trigger: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: dict = Depends(lambda: None)
):
    """List all workflow rules"""
    query = {"organization_id": admin["organization_id"]}
    
    if trigger:
        query["trigger"] = trigger
    if is_active is not None:
        query["is_active"] = is_active
    
    rules = await db.workflow_rules.find(query).sort("sort_order", 1).to_list(200)
    
    return {
        "rules": [{**r, "id": str(r.get("_id", r.get("id")))} for r in rules]
    }


@router.get("/workflow-rules/{rule_id}")
async def get_workflow_rule(
    rule_id: str,
    admin: dict = Depends(lambda: None)
):
    """Get a single workflow rule"""
    rule = await db.workflow_rules.find_one({
        "id": rule_id,
        "organization_id": admin["organization_id"]
    })
    
    if not rule:
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    
    rule["id"] = str(rule.get("_id", rule.get("id")))
    return rule


@router.post("/workflow-rules")
async def create_workflow_rule(
    data: WorkflowRuleCreate,
    admin: dict = Depends(lambda: None)
):
    """Create a new workflow rule"""
    rule_id = str(uuid.uuid4())
    
    rule = {
        "id": rule_id,
        "organization_id": admin["organization_id"],
        "name": data.name,
        "description": data.description,
        "trigger": data.trigger.value,
        "conditions": [c.dict() for c in data.conditions],
        "condition_logic": data.condition_logic,
        "actions": [a.dict() for a in data.actions],
        "is_active": data.is_active,
        "sort_order": data.sort_order,
        "stop_processing": data.stop_processing,
        "execution_count": 0,
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["id"]
    }
    
    await db.workflow_rules.insert_one(rule)
    
    return {"id": rule_id, "message": "Workflow rule created"}


@router.put("/workflow-rules/{rule_id}")
async def update_workflow_rule(
    rule_id: str,
    data: WorkflowRuleUpdate,
    admin: dict = Depends(lambda: None)
):
    """Update a workflow rule"""
    rule = await db.workflow_rules.find_one({
        "id": rule_id,
        "organization_id": admin["organization_id"]
    })
    
    if not rule:
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.description is not None:
        update_data["description"] = data.description
    if data.trigger is not None:
        update_data["trigger"] = data.trigger.value
    if data.conditions is not None:
        update_data["conditions"] = [c.dict() for c in data.conditions]
    if data.condition_logic is not None:
        update_data["condition_logic"] = data.condition_logic
    if data.actions is not None:
        update_data["actions"] = [a.dict() for a in data.actions]
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    if data.sort_order is not None:
        update_data["sort_order"] = data.sort_order
    if data.stop_processing is not None:
        update_data["stop_processing"] = data.stop_processing
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin["id"]
    
    await db.workflow_rules.update_one(
        {"id": rule_id},
        {"$set": update_data}
    )
    
    return {"message": "Workflow rule updated"}


@router.delete("/workflow-rules/{rule_id}")
async def delete_workflow_rule(
    rule_id: str,
    admin: dict = Depends(lambda: None)
):
    """Delete a workflow rule"""
    result = await db.workflow_rules.delete_one({
        "id": rule_id,
        "organization_id": admin["organization_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Workflow rule not found")
    
    return {"message": "Workflow rule deleted"}


@router.post("/workflow-rules/reorder")
async def reorder_workflow_rules(
    rule_ids: List[str],
    admin: dict = Depends(lambda: None)
):
    """Reorder workflow rules"""
    for i, rule_id in enumerate(rule_ids):
        await db.workflow_rules.update_one(
            {"id": rule_id, "organization_id": admin["organization_id"]},
            {"$set": {"sort_order": i}}
        )
    
    return {"message": "Rules reordered"}


# =============================================================================
# NOTIFICATION SETTINGS
# =============================================================================

@router.get("/notifications")
async def list_notification_settings(
    admin: dict = Depends(lambda: None)
):
    """List all notification settings"""
    settings = await db.notification_settings.find({
        "organization_id": admin["organization_id"]
    }).to_list(100)
    
    return {
        "settings": [{**s, "id": str(s.get("_id", s.get("id")))} for s in settings]
    }


@router.post("/notifications")
async def create_notification_setting(
    data: NotificationSettingCreate,
    admin: dict = Depends(lambda: None)
):
    """Create or update notification setting for an event"""
    setting_id = str(uuid.uuid4())
    
    # Check if setting for this event already exists
    existing = await db.notification_settings.find_one({
        "organization_id": admin["organization_id"],
        "event": data.event.value
    })
    
    setting_data = {
        "organization_id": admin["organization_id"],
        "event": data.event.value,
        "channels": [c.value for c in data.channels],
        "recipients": [r.value for r in data.recipients],
        "specific_user_ids": data.specific_user_ids,
        "specific_emails": data.specific_emails,
        "is_active": data.is_active,
        "email_subject": data.email_subject,
        "email_template": data.email_template,
        "sms_template": data.sms_template,
        "conditions": [c.dict() for c in data.conditions] if data.conditions else None,
        "updated_at": datetime.now(timezone.utc)
    }
    
    if existing:
        await db.notification_settings.update_one(
            {"id": existing["id"]},
            {"$set": setting_data}
        )
        return {"id": existing["id"], "message": "Notification setting updated"}
    else:
        setting_data["id"] = setting_id
        setting_data["created_at"] = datetime.now(timezone.utc)
        await db.notification_settings.insert_one(setting_data)
        return {"id": setting_id, "message": "Notification setting created"}


@router.put("/notifications/{setting_id}")
async def update_notification_setting(
    setting_id: str,
    data: NotificationSettingUpdate,
    admin: dict = Depends(lambda: None)
):
    """Update a notification setting"""
    update_data = {}
    
    if data.channels is not None:
        update_data["channels"] = [c.value for c in data.channels]
    if data.recipients is not None:
        update_data["recipients"] = [r.value for r in data.recipients]
    if data.specific_user_ids is not None:
        update_data["specific_user_ids"] = data.specific_user_ids
    if data.specific_emails is not None:
        update_data["specific_emails"] = data.specific_emails
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    if data.email_subject is not None:
        update_data["email_subject"] = data.email_subject
    if data.email_template is not None:
        update_data["email_template"] = data.email_template
    if data.sms_template is not None:
        update_data["sms_template"] = data.sms_template
    if data.conditions is not None:
        update_data["conditions"] = [c.dict() for c in data.conditions]
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    
    result = await db.notification_settings.update_one(
        {"id": setting_id, "organization_id": admin["organization_id"]},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification setting not found")
    
    return {"message": "Notification setting updated"}


@router.delete("/notifications/{setting_id}")
async def delete_notification_setting(
    setting_id: str,
    admin: dict = Depends(lambda: None)
):
    """Delete a notification setting"""
    result = await db.notification_settings.delete_one({
        "id": setting_id,
        "organization_id": admin["organization_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Notification setting not found")
    
    return {"message": "Notification setting deleted"}


@router.post("/notifications/seed-defaults")
async def seed_default_notifications(
    admin: dict = Depends(lambda: None)
):
    """Seed default notification settings"""
    org_id = admin["organization_id"]
    
    existing = await db.notification_settings.count_documents({"organization_id": org_id})
    if existing > 0:
        return {"message": "Defaults already exist", "count": existing}
    
    defaults = [
        {
            "event": "ticket_created",
            "channels": ["email", "in_app"],
            "recipients": ["company_contact", "assigned_technician"],
            "is_active": True,
            "email_subject": "New Service Ticket #{ticket_number}"
        },
        {
            "event": "ticket_assigned",
            "channels": ["email", "in_app"],
            "recipients": ["assigned_technician"],
            "is_active": True,
            "email_subject": "Ticket #{ticket_number} Assigned to You"
        },
        {
            "event": "ticket_completed",
            "channels": ["email"],
            "recipients": ["company_contact", "ticket_creator"],
            "is_active": True,
            "email_subject": "Ticket #{ticket_number} Completed"
        },
        {
            "event": "sla_warning",
            "channels": ["email", "in_app"],
            "recipients": ["assigned_technician", "managers"],
            "is_active": True,
            "email_subject": "SLA Warning: Ticket #{ticket_number}"
        },
        {
            "event": "sla_breached",
            "channels": ["email", "in_app"],
            "recipients": ["assigned_technician", "managers"],
            "is_active": True,
            "email_subject": "SLA Breached: Ticket #{ticket_number}"
        },
    ]
    
    for d in defaults:
        d["id"] = str(uuid.uuid4())
        d["organization_id"] = org_id
        d["created_at"] = datetime.now(timezone.utc)
    
    await db.notification_settings.insert_many(defaults)
    
    return {"message": "Default notifications created", "count": len(defaults)}


# =============================================================================
# APPROVAL SETTINGS
# =============================================================================

@router.get("/approvals")
async def list_approval_settings(
    admin: dict = Depends(lambda: None)
):
    """List all approval settings"""
    settings = await db.approval_settings.find({
        "organization_id": admin["organization_id"]
    }).to_list(50)
    
    return {
        "settings": [{**s, "id": str(s.get("_id", s.get("id")))} for s in settings]
    }


@router.post("/approvals")
async def create_approval_setting(
    data: ApprovalSettingCreate,
    admin: dict = Depends(lambda: None)
):
    """Create an approval setting"""
    setting_id = str(uuid.uuid4())
    
    setting = {
        "id": setting_id,
        "organization_id": admin["organization_id"],
        **data.dict(),
        "approval_type": data.approval_type.value,
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["id"]
    }
    
    await db.approval_settings.insert_one(setting)
    
    return {"id": setting_id, "message": "Approval setting created"}


@router.delete("/approvals/{setting_id}")
async def delete_approval_setting(
    setting_id: str,
    admin: dict = Depends(lambda: None)
):
    """Delete an approval setting"""
    result = await db.approval_settings.delete_one({
        "id": setting_id,
        "organization_id": admin["organization_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Approval setting not found")
    
    return {"message": "Approval setting deleted"}
