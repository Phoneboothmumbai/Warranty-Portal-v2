"""
Ticketing Configuration Routes
API endpoints for managing service ticket configuration
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Header
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import jwt
import os

from database import db
from models.ticketing_config import (
    ServiceMasterCreate, ServiceMasterUpdate, ServiceMasterResponse, ServiceMasterType,
    HelpTopicCreate, HelpTopicUpdate, HelpTopicResponse,
    WorkflowRuleCreate, WorkflowRuleUpdate, WorkflowRuleResponse,
    NotificationSettingCreate, NotificationSettingUpdate, NotificationSettingResponse,
    ApprovalSettingCreate, ApprovalSettingResponse
)

router = APIRouter(prefix="/ticketing-config", tags=["Ticketing Configuration"])

JWT_SECRET = os.environ.get("JWT_SECRET", "your-secret-key-here")

async def get_admin_from_token(authorization: str = Header(None)):
    """Extract admin from JWT token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header required")
    
    try:
        token = authorization.replace("Bearer ", "")
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        
        # Handle different token types
        token_type = payload.get("type", "admin")
        organization_id = payload.get("organization_id")
        
        if token_type == "org_member":
            # This is an organization member (admin panel user)
            member_id = payload.get("org_member_id")
            email = payload.get("sub")
            
            return {
                "id": member_id,
                "email": email,
                "organization_id": organization_id,
                "role": payload.get("role"),
                "name": email  # Fallback
            }
        else:
            # Legacy admin token
            admin_id = payload.get("sub")
            admin = await db.admins.find_one({"id": admin_id})
            
            if admin:
                return {
                    "id": admin["id"],
                    "organization_id": admin.get("organization_id"),
                    "email": admin.get("email"),
                    "name": admin.get("name")
                }
            
            # Try by email
            admin = await db.admins.find_one({"email": admin_id})
            if admin:
                return {
                    "id": admin.get("id", admin_id),
                    "organization_id": admin.get("organization_id", organization_id),
                    "email": admin.get("email", admin_id),
                    "name": admin.get("name", admin_id)
                }
            
            # Return payload data as fallback
            return {
                "id": admin_id,
                "email": admin_id,
                "organization_id": organization_id,
                "name": admin_id
            }
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# =============================================================================
# SERVICE MASTERS
# =============================================================================

@router.get("/masters")
async def list_service_masters(
    master_type: Optional[ServiceMasterType] = None,
    is_active: Optional[bool] = None,
    admin: dict = Depends(get_admin_from_token)
):
    """List all service masters, optionally filtered by type"""
    query = {"organization_id": admin["organization_id"]}
    
    if master_type:
        query["master_type"] = master_type.value
    if is_active is not None:
        query["is_active"] = is_active
    
    masters = await db.service_masters.find(query, {"_id": 0}).sort("sort_order", 1).to_list(500)
    
    return {"masters": masters}


@router.post("/masters")
async def create_service_master(
    data: ServiceMasterCreate,
    admin: dict = Depends(get_admin_from_token)
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
    
    # Return clean response without datetime objects
    return {"id": master_id, "message": "Service master created"}


@router.put("/masters/{master_id}")
async def update_service_master(
    master_id: str,
    data: ServiceMasterUpdate,
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
):
    """List all help topics"""
    query = {"organization_id": admin["organization_id"]}
    
    if is_active is not None:
        query["is_active"] = is_active
    if is_public is not None:
        query["is_public"] = is_public
    
    topics = await db.help_topics.find(query, {"_id": 0}).sort("sort_order", 1).to_list(200)
    
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
):
    """List all workflow rules"""
    query = {"organization_id": admin["organization_id"]}
    
    if trigger:
        query["trigger"] = trigger
    if is_active is not None:
        query["is_active"] = is_active
    
    rules = await db.workflow_rules.find(query, {"_id": 0}).sort("sort_order", 1).to_list(200)
    
    return {
        "rules": [{**r, "id": str(r.get("_id", r.get("id")))} for r in rules]
    }


@router.get("/workflow-rules/{rule_id}")
async def get_workflow_rule(
    rule_id: str,
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
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
    admin: dict = Depends(get_admin_from_token)
):
    """Delete an approval setting"""
    result = await db.approval_settings.delete_one({
        "id": setting_id,
        "organization_id": admin["organization_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Approval setting not found")
    
    return {"message": "Approval setting deleted"}



# =============================================================================
# CANNED RESPONSES
# =============================================================================

class CannedResponseCreate(BaseModel):
    title: str
    category: Optional[str] = None
    department_id: Optional[str] = None
    content: str
    is_personal: bool = False
    is_active: bool = True
    sort_order: int = 0

class CannedResponseUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    department_id: Optional[str] = None
    content: Optional[str] = None
    is_personal: Optional[bool] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

from pydantic import BaseModel


@router.get("/canned-responses")
async def list_canned_responses(
    category: Optional[str] = None,
    department_id: Optional[str] = None,
    include_personal: bool = True,
    admin: dict = Depends(get_admin_from_token)
):
    """List all canned responses"""
    query = {"organization_id": admin["organization_id"]}
    
    if category:
        query["category"] = category
    if department_id:
        query["department_id"] = department_id
    
    # Filter personal responses
    if not include_personal:
        query["$or"] = [
            {"is_personal": False},
            {"is_personal": {"$exists": False}}
        ]
    else:
        # Include personal responses only for the current user
        query["$or"] = [
            {"is_personal": False},
            {"is_personal": {"$exists": False}},
            {"created_by": admin["id"]}
        ]
    
    responses = await db.canned_responses.find(query, {"_id": 0}).sort("sort_order", 1).to_list(500)
    
    # Get unique categories
    all_responses = await db.canned_responses.find(
        {"organization_id": admin["organization_id"]},
        {"category": 1}
    ).to_list(500)
    categories = list(set([r.get("category") for r in all_responses if r.get("category")]))
    
    return {"responses": responses, "categories": categories}


@router.get("/canned-responses/{response_id}")
async def get_canned_response(
    response_id: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Get a single canned response"""
    response = await db.canned_responses.find_one({
        "id": response_id,
        "organization_id": admin["organization_id"]
    }, {"_id": 0})
    
    if not response:
        raise HTTPException(status_code=404, detail="Canned response not found")
    
    return response


@router.post("/canned-responses")
async def create_canned_response(
    data: CannedResponseCreate,
    admin: dict = Depends(get_admin_from_token)
):
    """Create a new canned response"""
    response_id = str(uuid.uuid4())
    
    response = {
        "id": response_id,
        "organization_id": admin["organization_id"],
        "title": data.title,
        "category": data.category,
        "department_id": data.department_id,
        "content": data.content,
        "is_personal": data.is_personal,
        "is_active": data.is_active,
        "sort_order": data.sort_order,
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["id"],
        "created_by_name": admin.get("name", admin.get("email"))
    }
    
    await db.canned_responses.insert_one(response)
    
    return {"id": response_id, "message": "Canned response created"}


@router.put("/canned-responses/{response_id}")
async def update_canned_response(
    response_id: str,
    data: CannedResponseUpdate,
    admin: dict = Depends(get_admin_from_token)
):
    """Update a canned response"""
    response = await db.canned_responses.find_one({
        "id": response_id,
        "organization_id": admin["organization_id"]
    })
    
    if not response:
        raise HTTPException(status_code=404, detail="Canned response not found")
    
    # Check if personal and belongs to another user
    if response.get("is_personal") and response.get("created_by") != admin["id"]:
        raise HTTPException(status_code=403, detail="Cannot edit another user's personal response")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin["id"]
    
    await db.canned_responses.update_one(
        {"id": response_id},
        {"$set": update_data}
    )
    
    return {"message": "Canned response updated"}


@router.delete("/canned-responses/{response_id}")
async def delete_canned_response(
    response_id: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Delete a canned response"""
    response = await db.canned_responses.find_one({
        "id": response_id,
        "organization_id": admin["organization_id"]
    })
    
    if not response:
        raise HTTPException(status_code=404, detail="Canned response not found")
    
    # Check if personal and belongs to another user
    if response.get("is_personal") and response.get("created_by") != admin["id"]:
        raise HTTPException(status_code=403, detail="Cannot delete another user's personal response")
    
    await db.canned_responses.delete_one({"id": response_id})
    
    return {"message": "Canned response deleted"}


# =============================================================================
# SLA POLICIES
# =============================================================================

class SLAPolicyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    is_default: bool = False
    
    # Response time
    response_time_hours: int = 4
    response_time_business_hours: bool = True
    
    # Resolution time
    resolution_time_hours: int = 24
    resolution_time_business_hours: bool = True
    
    # Grace period
    grace_period_hours: int = 0
    
    # Priority multipliers (lower = faster)
    priority_multipliers: Optional[dict] = None  # e.g., {"critical": 0.25, "high": 0.5, "medium": 1, "low": 2}
    
    # Escalation
    escalation_enabled: bool = True
    escalation_after_hours: int = 2  # Hours before breach to escalate
    escalate_to_user_id: Optional[str] = None
    escalate_to_role: Optional[str] = None
    
    # Business hours
    business_hours_start: str = "09:00"  # HH:MM
    business_hours_end: str = "18:00"
    business_days: List[int] = [1, 2, 3, 4, 5]  # Monday=1, Sunday=7


class SLAPolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None
    response_time_hours: Optional[int] = None
    response_time_business_hours: Optional[bool] = None
    resolution_time_hours: Optional[int] = None
    resolution_time_business_hours: Optional[bool] = None
    grace_period_hours: Optional[int] = None
    priority_multipliers: Optional[dict] = None
    escalation_enabled: Optional[bool] = None
    escalation_after_hours: Optional[int] = None
    escalate_to_user_id: Optional[str] = None
    escalate_to_role: Optional[str] = None
    business_hours_start: Optional[str] = None
    business_hours_end: Optional[str] = None
    business_days: Optional[List[int]] = None


@router.get("/sla-policies")
async def list_sla_policies(
    is_active: Optional[bool] = None,
    admin: dict = Depends(get_admin_from_token)
):
    """List all SLA policies"""
    query = {"organization_id": admin["organization_id"]}
    
    if is_active is not None:
        query["is_active"] = is_active
    
    policies = await db.sla_policies.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    
    return {"policies": policies}


@router.get("/sla-policies/{policy_id}")
async def get_sla_policy(
    policy_id: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Get a single SLA policy"""
    policy = await db.sla_policies.find_one({
        "id": policy_id,
        "organization_id": admin["organization_id"]
    }, {"_id": 0})
    
    if not policy:
        raise HTTPException(status_code=404, detail="SLA policy not found")
    
    return policy


@router.post("/sla-policies")
async def create_sla_policy(
    data: SLAPolicyCreate,
    admin: dict = Depends(get_admin_from_token)
):
    """Create a new SLA policy"""
    policy_id = str(uuid.uuid4())
    
    # If this is being set as default, unset other defaults
    if data.is_default:
        await db.sla_policies.update_many(
            {"organization_id": admin["organization_id"]},
            {"$set": {"is_default": False}}
        )
    
    policy = {
        "id": policy_id,
        "organization_id": admin["organization_id"],
        **data.dict(),
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["id"]
    }
    
    await db.sla_policies.insert_one(policy)
    
    return {"id": policy_id, "message": "SLA policy created"}


@router.put("/sla-policies/{policy_id}")
async def update_sla_policy(
    policy_id: str,
    data: SLAPolicyUpdate,
    admin: dict = Depends(get_admin_from_token)
):
    """Update an SLA policy"""
    policy = await db.sla_policies.find_one({
        "id": policy_id,
        "organization_id": admin["organization_id"]
    })
    
    if not policy:
        raise HTTPException(status_code=404, detail="SLA policy not found")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    
    # If setting as default, unset others
    if update_data.get("is_default"):
        await db.sla_policies.update_many(
            {"organization_id": admin["organization_id"], "id": {"$ne": policy_id}},
            {"$set": {"is_default": False}}
        )
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin["id"]
    
    await db.sla_policies.update_one(
        {"id": policy_id},
        {"$set": update_data}
    )
    
    return {"message": "SLA policy updated"}


@router.delete("/sla-policies/{policy_id}")
async def delete_sla_policy(
    policy_id: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Delete an SLA policy"""
    result = await db.sla_policies.delete_one({
        "id": policy_id,
        "organization_id": admin["organization_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="SLA policy not found")
    
    return {"message": "SLA policy deleted"}


@router.post("/sla-policies/seed-defaults")
async def seed_default_sla_policies(
    admin: dict = Depends(get_admin_from_token)
):
    """Seed default SLA policies"""
    org_id = admin["organization_id"]
    
    existing = await db.sla_policies.count_documents({"organization_id": org_id})
    if existing > 0:
        return {"message": "Defaults already exist", "count": existing}
    
    defaults = [
        {
            "name": "Critical - 1 Hour Response",
            "description": "For critical issues requiring immediate attention",
            "response_time_hours": 1,
            "resolution_time_hours": 4,
            "priority_multipliers": {"critical": 0.25, "high": 0.5, "medium": 1, "low": 2},
            "escalation_enabled": True,
            "escalation_after_hours": 1
        },
        {
            "name": "Standard - 4 Hour Response",
            "description": "Default SLA for normal tickets",
            "response_time_hours": 4,
            "resolution_time_hours": 24,
            "is_default": True,
            "priority_multipliers": {"critical": 0.25, "high": 0.5, "medium": 1, "low": 2}
        },
        {
            "name": "Extended - 8 Hour Response",
            "description": "For low priority or non-urgent issues",
            "response_time_hours": 8,
            "resolution_time_hours": 48,
            "priority_multipliers": {"critical": 0.5, "high": 0.75, "medium": 1, "low": 1.5}
        }
    ]
    
    for d in defaults:
        d["id"] = str(uuid.uuid4())
        d["organization_id"] = org_id
        d["is_active"] = True
        d["response_time_business_hours"] = True
        d["resolution_time_business_hours"] = True
        d["grace_period_hours"] = 0
        d["business_hours_start"] = "09:00"
        d["business_hours_end"] = "18:00"
        d["business_days"] = [1, 2, 3, 4, 5]
        d["created_at"] = datetime.now(timezone.utc)
    
    await db.sla_policies.insert_many(defaults)
    
    return {"message": "Default SLA policies created", "count": len(defaults)}


# =============================================================================
# DEPARTMENTS
# =============================================================================

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    email: Optional[str] = None
    manager_id: Optional[str] = None
    sla_policy_id: Optional[str] = None
    is_active: bool = True
    is_public: bool = True  # Visible in customer portal
    auto_assign_tickets: bool = False
    signature: Optional[str] = None  # Email signature
    sort_order: int = 0


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    email: Optional[str] = None
    manager_id: Optional[str] = None
    sla_policy_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    auto_assign_tickets: Optional[bool] = None
    signature: Optional[str] = None
    sort_order: Optional[int] = None


@router.get("/departments")
async def list_departments(
    is_active: Optional[bool] = None,
    is_public: Optional[bool] = None,
    admin: dict = Depends(get_admin_from_token)
):
    """List all departments"""
    query = {"organization_id": admin["organization_id"]}
    
    if is_active is not None:
        query["is_active"] = is_active
    if is_public is not None:
        query["is_public"] = is_public
    
    departments = await db.departments.find(query, {"_id": 0}).sort("sort_order", 1).to_list(100)
    
    # Get member counts
    for dept in departments:
        dept["member_count"] = await db.staff_users.count_documents({
            "organization_id": admin["organization_id"],
            "department_id": dept["id"],
            "is_deleted": {"$ne": True}
        })
        
        # Get ticket counts
        dept["open_tickets"] = await db.service_tickets_new.count_documents({
            "organization_id": admin["organization_id"],
            "department_id": dept["id"],
            "status": {"$nin": ["closed", "cancelled"]},
            "is_deleted": {"$ne": True}
        })
    
    return {"departments": departments}


@router.get("/departments/{dept_id}")
async def get_department(
    dept_id: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Get a single department with details"""
    dept = await db.departments.find_one({
        "id": dept_id,
        "organization_id": admin["organization_id"]
    }, {"_id": 0})
    
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    # Get members
    members = await db.staff_users.find({
        "organization_id": admin["organization_id"],
        "department_id": dept_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "password_hash": 0}).to_list(100)
    
    dept["members"] = members
    
    # Get manager details if set
    if dept.get("manager_id"):
        manager = await db.staff_users.find_one(
            {"id": dept["manager_id"]},
            {"_id": 0, "name": 1, "email": 1, "id": 1}
        )
        dept["manager"] = manager
    
    return dept


@router.post("/departments")
async def create_department(
    data: DepartmentCreate,
    admin: dict = Depends(get_admin_from_token)
):
    """Create a new department"""
    dept_id = str(uuid.uuid4())
    
    dept = {
        "id": dept_id,
        "organization_id": admin["organization_id"],
        **data.dict(),
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["id"]
    }
    
    await db.departments.insert_one(dept)
    
    return {"id": dept_id, "message": "Department created"}


@router.put("/departments/{dept_id}")
async def update_department(
    dept_id: str,
    data: DepartmentUpdate,
    admin: dict = Depends(get_admin_from_token)
):
    """Update a department"""
    dept = await db.departments.find_one({
        "id": dept_id,
        "organization_id": admin["organization_id"]
    })
    
    if not dept:
        raise HTTPException(status_code=404, detail="Department not found")
    
    update_data = {k: v for k, v in data.dict().items() if v is not None}
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin["id"]
    
    await db.departments.update_one(
        {"id": dept_id},
        {"$set": update_data}
    )
    
    return {"message": "Department updated"}


@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Delete a department"""
    # Check if department has members
    member_count = await db.staff_users.count_documents({
        "organization_id": admin["organization_id"],
        "department_id": dept_id,
        "is_deleted": {"$ne": True}
    })
    
    if member_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete department with {member_count} members. Reassign members first."
        )
    
    result = await db.departments.delete_one({
        "id": dept_id,
        "organization_id": admin["organization_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Department not found")
    
    return {"message": "Department deleted"}


@router.post("/departments/seed-defaults")
async def seed_default_departments(
    admin: dict = Depends(get_admin_from_token)
):
    """Seed default departments"""
    org_id = admin["organization_id"]
    
    existing = await db.departments.count_documents({"organization_id": org_id})
    if existing > 0:
        return {"message": "Defaults already exist", "count": existing}
    
    defaults = [
        {
            "name": "Support",
            "description": "General support and customer service",
            "is_public": True
        },
        {
            "name": "Technical",
            "description": "Technical support and troubleshooting",
            "is_public": True
        },
        {
            "name": "Field Service",
            "description": "On-site service and repairs",
            "is_public": False
        },
        {
            "name": "Billing",
            "description": "Billing and payment inquiries",
            "is_public": True
        }
    ]
    
    for d in defaults:
        d["id"] = str(uuid.uuid4())
        d["organization_id"] = org_id
        d["is_active"] = True
        d["sort_order"] = 0
        d["created_at"] = datetime.now(timezone.utc)
    
    await db.departments.insert_many(defaults)
    
    return {"message": "Default departments created", "count": len(defaults)}


# =============================================================================
# CUSTOM FORMS
# =============================================================================

class CustomFormCreate(BaseModel):
    name: str
    description: Optional[str] = None
    form_type: str = "ticket"  # ticket, visit, device, etc.
    fields: List[dict] = []
    is_active: bool = True


class CustomFormUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    form_type: Optional[str] = None
    fields: Optional[List[dict]] = None
    is_active: Optional[bool] = None


@router.get("/custom-forms")
async def list_custom_forms(
    form_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    admin: dict = Depends(get_admin_from_token)
):
    """List all custom forms"""
    query = {"organization_id": admin["organization_id"]}
    
    if form_type:
        query["form_type"] = form_type
    if is_active is not None:
        query["is_active"] = is_active
    
    forms = await db.custom_forms.find(query, {"_id": 0}).sort("name", 1).to_list(100)
    
    return {"forms": forms}


@router.get("/custom-forms/{form_id}")
async def get_custom_form(
    form_id: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Get a single custom form"""
    form = await db.custom_forms.find_one({
        "id": form_id,
        "organization_id": admin["organization_id"]
    }, {"_id": 0})
    
    if not form:
        raise HTTPException(status_code=404, detail="Custom form not found")
    
    return form


@router.post("/custom-forms")
async def create_custom_form(
    data: CustomFormCreate,
    admin: dict = Depends(get_admin_from_token)
):
    """Create a new custom form"""
    form_id = str(uuid.uuid4())
    
    # Add IDs to fields if not present
    fields = []
    for i, field in enumerate(data.fields):
        if not field.get("id"):
            field["id"] = str(uuid.uuid4())
        if "sort_order" not in field:
            field["sort_order"] = i
        fields.append(field)
    
    form = {
        "id": form_id,
        "organization_id": admin["organization_id"],
        "name": data.name,
        "description": data.description,
        "form_type": data.form_type,
        "fields": fields,
        "is_active": data.is_active,
        "created_at": datetime.now(timezone.utc),
        "created_by": admin["id"]
    }
    
    await db.custom_forms.insert_one(form)
    
    return {"id": form_id, "message": "Custom form created"}


@router.put("/custom-forms/{form_id}")
async def update_custom_form(
    form_id: str,
    data: CustomFormUpdate,
    admin: dict = Depends(get_admin_from_token)
):
    """Update a custom form"""
    form = await db.custom_forms.find_one({
        "id": form_id,
        "organization_id": admin["organization_id"]
    })
    
    if not form:
        raise HTTPException(status_code=404, detail="Custom form not found")
    
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.description is not None:
        update_data["description"] = data.description
    if data.form_type is not None:
        update_data["form_type"] = data.form_type
    if data.is_active is not None:
        update_data["is_active"] = data.is_active
    if data.fields is not None:
        # Add IDs to fields if not present
        fields = []
        for i, field in enumerate(data.fields):
            if not field.get("id"):
                field["id"] = str(uuid.uuid4())
            if "sort_order" not in field:
                field["sort_order"] = i
            fields.append(field)
        update_data["fields"] = fields
    
    update_data["updated_at"] = datetime.now(timezone.utc)
    update_data["updated_by"] = admin["id"]
    
    await db.custom_forms.update_one(
        {"id": form_id},
        {"$set": update_data}
    )
    
    return {"message": "Custom form updated"}


@router.delete("/custom-forms/{form_id}")
async def delete_custom_form(
    form_id: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Delete a custom form"""
    result = await db.custom_forms.delete_one({
        "id": form_id,
        "organization_id": admin["organization_id"]
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Custom form not found")
    
    return {"message": "Custom form deleted"}
