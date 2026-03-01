"""
Job Acceptance & Notification System
======================================
Handles technician accept/decline workflow, in-app notifications,
smart reassignment, and acceptance SLA tracking.
"""

import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from typing import Optional, List
from pydantic import BaseModel
from services.auth import get_current_admin, get_current_engineer

router = APIRouter()
_db = None

def init_db(database):
    global _db
    _db = database

IST = timezone(timedelta(hours=5, minutes=30))
def now_ist(): return datetime.now(IST).isoformat()

DECLINE_REASONS = [
    {"id": "too_far", "label": "Too far / Location issue"},
    {"id": "skill_mismatch", "label": "Skill mismatch"},
    {"id": "overloaded", "label": "Already overloaded"},
    {"id": "on_leave", "label": "On leave / Unavailable"},
    {"id": "scheduling_conflict", "label": "Scheduling conflict"},
    {"id": "other", "label": "Other"},
]

AUTO_ESCALATION_HOURS = 4  # hours before auto-escalation


# ── Models ──

class AcceptJobRequest(BaseModel):
    ticket_id: str
    proposed_time: Optional[str] = None  # For "accept but reschedule"

class DeclineJobRequest(BaseModel):
    ticket_id: str
    reason_id: str
    reason_detail: Optional[str] = None

class RescheduleJobRequest(BaseModel):
    ticket_id: str
    proposed_time: str  # ISO datetime
    proposed_end_time: Optional[str] = None
    notes: Optional[str] = None


# ── Notification Helpers ──

async def create_notification(org_id: str, notif_type: str, title: str, message: str,
                               target_roles: list = None, target_user_ids: list = None,
                               ticket_id: str = None, metadata: dict = None):
    """Create an in-app notification."""
    notif = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "type": notif_type,
        "title": title,
        "message": message,
        "target_roles": target_roles or ["admin", "back_office"],
        "target_user_ids": target_user_ids or [],
        "ticket_id": ticket_id,
        "metadata": metadata or {},
        "is_read": False,
        "created_at": now_ist(),
    }
    await _db.notifications.insert_one(notif)
    return {k: v for k, v in notif.items() if k != "_id"}


# ── Technician Accept/Decline (Admin auth — for Technician Dashboard) ──

@router.get("/ticketing/assignment/pending")
async def get_pending_assignments(admin: dict = Depends(get_current_admin)):
    """Get tickets pending acceptance for the current technician."""
    user_id = admin.get("id")
    org_id = admin.get("organization_id")
    email = admin.get("email", "")

    engineer = await _db.engineers.find_one(
        {"$or": [{"id": user_id}, {"email": email}], "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1}
    )
    eng_id = engineer["id"] if engineer else user_id

    tickets = await _db.tickets_v2.find({
        "assigned_to_id": eng_id,
        "organization_id": org_id,
        "assignment_status": "pending",
        "is_open": True,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "timeline": 0}).sort("assigned_at", -1).to_list(50)

    return {"tickets": tickets, "decline_reasons": DECLINE_REASONS}


@router.post("/ticketing/assignment/accept")
async def accept_assignment(data: AcceptJobRequest, admin: dict = Depends(get_current_admin)):
    """Technician accepts an assigned job."""
    org_id = admin.get("organization_id")
    user_id = admin.get("id")
    user_name = admin.get("name", admin.get("email", ""))

    engineer = await _db.engineers.find_one(
        {"$or": [{"id": user_id}, {"email": admin.get("email")}], "organization_id": org_id},
        {"_id": 0, "id": 1, "name": 1}
    )
    eng_id = engineer["id"] if engineer else user_id
    eng_name = engineer.get("name", user_name) if engineer else user_name

    ticket = await _db.tickets_v2.find_one(
        {"id": data.ticket_id, "organization_id": org_id, "assigned_to_id": eng_id,
         "assignment_status": "pending", "is_deleted": {"$ne": True}}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Pending assignment not found")

    update = {
        "assignment_status": "accepted",
        "assignment_responded_at": now_ist(),
        "updated_at": now_ist(),
    }

    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "assignment_accepted",
        "description": f"{eng_name} accepted the assignment",
        "user_name": eng_name,
        "created_at": now_ist(),
    }

    # If proposing a different time (accept but reschedule)
    if data.proposed_time:
        update["scheduled_at"] = data.proposed_time
        timeline_entry["description"] += f" (rescheduled to {data.proposed_time})"
        # Update schedule record
        await _db.ticket_schedules.update_many(
            {"ticket_id": data.ticket_id, "engineer_id": eng_id, "status": "scheduled"},
            {"$set": {"scheduled_at": data.proposed_time, "status": "accepted"}}
        )
    else:
        # Update existing schedules or create one if none exist
        existing_schedules = await _db.ticket_schedules.count_documents(
            {"ticket_id": data.ticket_id, "engineer_id": eng_id, "status": {"$ne": "cancelled"}}
        )
        if existing_schedules > 0:
            await _db.ticket_schedules.update_many(
                {"ticket_id": data.ticket_id, "engineer_id": eng_id, "status": "scheduled"},
                {"$set": {"status": "accepted"}}
            )
        else:
            # Create a schedule record so it appears on calendar
            sched_time = ticket.get("scheduled_at") or now_ist()
            sched_end = ticket.get("scheduled_end_at")
            if not sched_end:
                try:
                    from datetime import datetime as dt_cls
                    st = dt_cls.fromisoformat(sched_time.replace("Z", "+00:00"))
                    sched_end = (st + timedelta(hours=1)).isoformat()
                except Exception:
                    sched_end = None
            await _db.ticket_schedules.insert_one({
                "id": str(uuid.uuid4()),
                "organization_id": org_id,
                "ticket_id": data.ticket_id,
                "ticket_number": ticket.get("ticket_number"),
                "engineer_id": eng_id,
                "engineer_name": eng_name,
                "company_name": ticket.get("company_name"),
                "subject": ticket.get("subject"),
                "scheduled_at": sched_time,
                "scheduled_end_at": sched_end,
                "status": "accepted",
                "created_at": now_ist(),
            })

    await _db.tickets_v2.update_one(
        {"id": data.ticket_id},
        {"$set": update, "$push": {"timeline": timeline_entry}}
    )

    # Track acceptance SLA
    assigned_at = ticket.get("assigned_at")
    if assigned_at:
        await _db.assignment_sla_logs.insert_one({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "engineer_id": eng_id,
            "engineer_name": eng_name,
            "ticket_id": data.ticket_id,
            "ticket_number": ticket.get("ticket_number"),
            "assigned_at": assigned_at,
            "responded_at": now_ist(),
            "response": "accepted",
            "created_at": now_ist(),
        })

    return {"status": "accepted", "ticket_id": data.ticket_id}


@router.post("/ticketing/assignment/decline")
async def decline_assignment(data: DeclineJobRequest, admin: dict = Depends(get_current_admin)):
    """Technician declines an assigned job."""
    org_id = admin.get("organization_id")
    user_id = admin.get("id")
    user_name = admin.get("name", admin.get("email", ""))

    engineer = await _db.engineers.find_one(
        {"$or": [{"id": user_id}, {"email": admin.get("email")}], "organization_id": org_id},
        {"_id": 0, "id": 1, "name": 1}
    )
    eng_id = engineer["id"] if engineer else user_id
    eng_name = engineer.get("name", user_name) if engineer else user_name

    ticket = await _db.tickets_v2.find_one(
        {"id": data.ticket_id, "organization_id": org_id, "assigned_to_id": eng_id,
         "assignment_status": "pending", "is_deleted": {"$ne": True}}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Pending assignment not found")

    reason_label = next((r["label"] for r in DECLINE_REASONS if r["id"] == data.reason_id), data.reason_id)

    update = {
        "assignment_status": "declined",
        "assignment_responded_at": now_ist(),
        "decline_reason": data.reason_id,
        "decline_reason_label": reason_label,
        "decline_detail": data.reason_detail,
        "updated_at": now_ist(),
    }

    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "assignment_declined",
        "description": f"{eng_name} declined: {reason_label}" + (f" — {data.reason_detail}" if data.reason_detail else ""),
        "user_name": eng_name,
        "created_at": now_ist(),
    }

    await _db.tickets_v2.update_one(
        {"id": data.ticket_id},
        {"$set": update, "$push": {"timeline": timeline_entry}}
    )

    # Cancel related schedules
    await _db.ticket_schedules.update_many(
        {"ticket_id": data.ticket_id, "engineer_id": eng_id},
        {"$set": {"status": "cancelled"}}
    )

    # Create notification for back office
    await create_notification(
        org_id=org_id,
        notif_type="assignment_declined",
        title=f"Job Declined — #{ticket.get('ticket_number')}",
        message=f"{eng_name} declined ticket #{ticket.get('ticket_number')} ({ticket.get('subject', '')[:60]}). Reason: {reason_label}. Please reassign.",
        ticket_id=data.ticket_id,
        metadata={
            "engineer_id": eng_id,
            "engineer_name": eng_name,
            "ticket_number": ticket.get("ticket_number"),
            "reason_id": data.reason_id,
            "reason_label": reason_label,
            "reason_detail": data.reason_detail,
        }
    )

    # Track SLA
    assigned_at = ticket.get("assigned_at")
    if assigned_at:
        await _db.assignment_sla_logs.insert_one({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "engineer_id": eng_id,
            "engineer_name": eng_name,
            "ticket_id": data.ticket_id,
            "ticket_number": ticket.get("ticket_number"),
            "assigned_at": assigned_at,
            "responded_at": now_ist(),
            "response": "declined",
            "reason_id": data.reason_id,
            "created_at": now_ist(),
        })

    return {"status": "declined", "ticket_id": data.ticket_id}


@router.post("/ticketing/assignment/reschedule")
async def reschedule_assignment(data: RescheduleJobRequest, admin: dict = Depends(get_current_admin)):
    """Technician accepts but proposes a different time."""
    org_id = admin.get("organization_id")
    user_id = admin.get("id")
    user_name = admin.get("name", admin.get("email", ""))

    engineer = await _db.engineers.find_one(
        {"$or": [{"id": user_id}, {"email": admin.get("email")}], "organization_id": org_id},
        {"_id": 0, "id": 1, "name": 1}
    )
    eng_id = engineer["id"] if engineer else user_id
    eng_name = engineer.get("name", user_name) if engineer else user_name

    ticket = await _db.tickets_v2.find_one(
        {"id": data.ticket_id, "organization_id": org_id, "assigned_to_id": eng_id,
         "assignment_status": "pending", "is_deleted": {"$ne": True}}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Pending assignment not found")

    update = {
        "assignment_status": "accepted",
        "assignment_responded_at": now_ist(),
        "scheduled_at": data.proposed_time,
        "scheduled_end_at": data.proposed_end_time,
        "schedule_notes": data.notes,
        "updated_at": now_ist(),
    }

    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "assignment_rescheduled",
        "description": f"{eng_name} accepted & rescheduled to {data.proposed_time[:16]}",
        "user_name": eng_name,
        "created_at": now_ist(),
    }

    await _db.tickets_v2.update_one(
        {"id": data.ticket_id},
        {"$set": update, "$push": {"timeline": timeline_entry}}
    )

    # Update or create schedule record
    await _db.ticket_schedules.update_many(
        {"ticket_id": data.ticket_id, "engineer_id": eng_id},
        {"$set": {"status": "cancelled"}}
    )
    schedule_record = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "ticket_id": data.ticket_id,
        "ticket_number": ticket.get("ticket_number"),
        "engineer_id": eng_id,
        "engineer_name": eng_name,
        "company_name": ticket.get("company_name"),
        "subject": ticket.get("subject"),
        "scheduled_at": data.proposed_time,
        "scheduled_end_at": data.proposed_end_time,
        "notes": data.notes,
        "status": "accepted",
        "created_at": now_ist(),
    }
    await _db.ticket_schedules.insert_one(schedule_record)

    return {"status": "rescheduled", "ticket_id": data.ticket_id}


# ── Notifications ──

@router.get("/notifications")
async def get_notifications(
    unread_only: bool = False,
    limit: int = 30,
    admin: dict = Depends(get_current_admin)
):
    """Get notifications for current admin."""
    org_id = admin.get("organization_id")
    query = {"organization_id": org_id}
    if unread_only:
        query["is_read"] = False

    notifs = await _db.notifications.find(
        query, {"_id": 0}
    ).sort("created_at", -1).to_list(limit)

    unread_count = await _db.notifications.count_documents(
        {"organization_id": org_id, "is_read": False}
    )

    return {"notifications": notifs, "unread_count": unread_count}


@router.put("/notifications/{notif_id}/read")
async def mark_notification_read(notif_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    await _db.notifications.update_one(
        {"id": notif_id, "organization_id": org_id},
        {"$set": {"is_read": True, "read_at": now_ist()}}
    )
    return {"status": "read"}


@router.put("/notifications/read-all")
async def mark_all_read(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    await _db.notifications.update_many(
        {"organization_id": org_id, "is_read": False},
        {"$set": {"is_read": True, "read_at": now_ist()}}
    )
    return {"status": "all_read"}


# ── Smart Reassignment ──

@router.get("/ticketing/assignment/suggest-reassign/{ticket_id}")
async def suggest_reassignment(ticket_id: str, admin: dict = Depends(get_current_admin)):
    """Suggest best available technicians for reassignment based on skills, workload, and availability."""
    org_id = admin.get("organization_id")

    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id},
        {"_id": 0, "id": 1, "assigned_to_id": 1, "subject": 1, "ticket_number": 1,
         "help_topic_name": 1, "company_name": 1, "scheduled_at": 1}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    declined_by = ticket.get("assigned_to_id", "")

    # Get all active engineers except the one who declined
    engineers = await _db.engineers.find(
        {"organization_id": org_id, "is_active": {"$ne": False}, "is_deleted": {"$ne": True},
         "id": {"$ne": declined_by}},
        {"_id": 0, "id": 1, "name": 1, "specialization": 1, "skills": 1, "working_hours": 1, "holidays": 1}
    ).to_list(50)

    suggestions = []
    for eng in engineers:
        # Score: lower is better
        score = 50  # base

        # Check workload (fewer open tickets = better)
        open_tickets = await _db.tickets_v2.count_documents({
            "assigned_to_id": eng["id"], "organization_id": org_id,
            "is_open": True, "is_deleted": {"$ne": True}
        })
        score += open_tickets * 10

        # Check if scheduled date is a working day for this engineer
        sched_date = (ticket.get("scheduled_at") or "")[:10]
        if sched_date:
            from datetime import datetime as dt_cls
            try:
                day_name = dt_cls.strptime(sched_date, "%Y-%m-%d").strftime("%A").lower()
                wh = eng.get("working_hours", {})
                day_sched = wh.get(day_name, {})
                if not day_sched.get("is_working", True):
                    score += 100  # big penalty
                if sched_date in (eng.get("holidays") or []):
                    score += 200  # huge penalty
            except ValueError:
                pass

        # Check pending + declined assignments for responsiveness
        recent_declines = await _db.assignment_sla_logs.count_documents({
            "engineer_id": eng["id"], "response": "declined",
            "created_at": {"$gte": (datetime.now(IST) - timedelta(days=30)).isoformat()}
        })
        score += recent_declines * 15

        # Check specialization match with help topic
        if eng.get("specialization") and ticket.get("help_topic_name"):
            if eng["specialization"].lower() in ticket["help_topic_name"].lower():
                score -= 20  # bonus

        suggestions.append({
            "engineer_id": eng["id"],
            "name": eng["name"],
            "specialization": eng.get("specialization"),
            "skills": eng.get("skills", []),
            "open_tickets": open_tickets,
            "recent_declines": recent_declines,
            "score": score,
            "available_on_date": score < 150,  # rough heuristic
        })

    suggestions.sort(key=lambda x: x["score"])

    return {"ticket": ticket, "suggestions": suggestions}


@router.post("/ticketing/assignment/reassign")
async def reassign_ticket(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Reassign a declined ticket to a new technician."""
    org_id = admin.get("organization_id")
    ticket_id = data.get("ticket_id")
    new_engineer_id = data.get("engineer_id")
    scheduled_at = data.get("scheduled_at")
    scheduled_end_at = data.get("scheduled_end_at")

    if not ticket_id or not new_engineer_id:
        raise HTTPException(status_code=400, detail="ticket_id and engineer_id required")

    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    engineer = await _db.engineers.find_one(
        {"id": new_engineer_id, "organization_id": org_id},
        {"_id": 0, "id": 1, "name": 1, "email": 1}
    )
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found")

    old_name = ticket.get("assigned_to_name", "Unassigned")

    update = {
        "assigned_to_id": new_engineer_id,
        "assigned_to_name": engineer["name"],
        "assignment_status": "pending",
        "assigned_at": now_ist(),
        "assignment_responded_at": None,
        "decline_reason": None,
        "decline_reason_label": None,
        "decline_detail": None,
        "updated_at": now_ist(),
    }

    if scheduled_at:
        update["scheduled_at"] = scheduled_at
        update["scheduled_end_at"] = scheduled_end_at

    timeline_entry = {
        "id": str(uuid.uuid4()),
        "type": "reassignment",
        "description": f"Reassigned from {old_name} to {engineer['name']}",
        "user_name": admin.get("name", admin.get("email", "")),
        "created_at": now_ist(),
    }

    await _db.tickets_v2.update_one(
        {"id": ticket_id},
        {"$set": update, "$push": {"timeline": timeline_entry}}
    )

    # Create new schedule if time provided
    if scheduled_at:
        await _db.ticket_schedules.insert_one({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "ticket_id": ticket_id,
            "ticket_number": ticket.get("ticket_number"),
            "engineer_id": new_engineer_id,
            "engineer_name": engineer["name"],
            "company_name": ticket.get("company_name"),
            "subject": ticket.get("subject"),
            "scheduled_at": scheduled_at,
            "scheduled_end_at": scheduled_end_at,
            "status": "scheduled",
            "created_at": now_ist(),
        })

    return {"status": "reassigned", "ticket_id": ticket_id, "new_engineer": engineer["name"]}


# ── Acceptance SLA Tracking ──

@router.get("/ticketing/assignment/sla-stats")
async def assignment_sla_stats(admin: dict = Depends(get_current_admin)):
    """Get acceptance SLA stats across all engineers."""
    org_id = admin.get("organization_id")

    engineers = await _db.engineers.find(
        {"organization_id": org_id, "is_active": {"$ne": False}, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1}
    ).to_list(50)

    stats = []
    for eng in engineers:
        logs = await _db.assignment_sla_logs.find(
            {"engineer_id": eng["id"], "organization_id": org_id},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)

        total = len(logs)
        accepted = len([entry for entry in logs if entry.get("response") == "accepted"])
        declined = len([entry for entry in logs if entry.get("response") == "declined"])

        # Calculate avg response time
        response_times = []
        for log in logs:
            if log.get("assigned_at") and log.get("responded_at"):
                try:
                    a = datetime.fromisoformat(log["assigned_at"])
                    r = datetime.fromisoformat(log["responded_at"])
                    diff_mins = (r - a).total_seconds() / 60
                    response_times.append(diff_mins)
                except (ValueError, TypeError):
                    pass

        avg_response = sum(response_times) / len(response_times) if response_times else None

        # Get decline reasons breakdown
        reasons = {}
        for log in logs:
            if log.get("response") == "declined" and log.get("reason_id"):
                reasons[log["reason_id"]] = reasons.get(log["reason_id"], 0) + 1

        stats.append({
            "engineer_id": eng["id"],
            "name": eng["name"],
            "total_assignments": total,
            "accepted": accepted,
            "declined": declined,
            "acceptance_rate": round(accepted / total * 100, 1) if total > 0 else None,
            "avg_response_minutes": round(avg_response, 1) if avg_response else None,
            "decline_reasons": reasons,
        })

    return {"stats": stats}


# ── Auto-Escalation Check ──

@router.get("/ticketing/assignment/check-escalations")
async def check_escalations(admin: dict = Depends(get_current_admin)):
    """Check for pending assignments that have exceeded the response time limit."""
    org_id = admin.get("organization_id")

    cutoff = (datetime.now(IST) - timedelta(hours=AUTO_ESCALATION_HOURS)).isoformat()

    overdue = await _db.tickets_v2.find({
        "organization_id": org_id,
        "assignment_status": "pending",
        "assigned_at": {"$lte": cutoff},
        "is_open": True,
        "is_deleted": {"$ne": True},
    }, {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "assigned_to_id": 1,
        "assigned_to_name": 1, "assigned_at": 1, "company_name": 1}).to_list(50)

    return {
        "overdue_assignments": overdue,
        "escalation_threshold_hours": AUTO_ESCALATION_HOURS,
        "count": len(overdue)
    }


# ═══════════════════════════════════════════════════════════════
# ENGINEER PORTAL ENDPOINTS (uses get_current_engineer auth)
# ═══════════════════════════════════════════════════════════════

async def _resolve_engineer(user: dict):
    """Resolve engineer record from auth token data.
    Returns profile with all_ids list for cross-collection ID matching."""
    eng_id = user.get("id")
    email = user.get("email", user.get("sub", ""))
    
    all_ids = set()
    profile = None
    
    # Check engineers collection
    engineer = await _db.engineers.find_one(
        {"$or": [{"id": eng_id}, {"email": email}], "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "organization_id": 1}
    )
    if engineer:
        all_ids.add(engineer["id"])
        profile = engineer
    
    # Check staff_users collection
    staff = await _db.staff_users.find_one(
        {"$or": [{"id": eng_id}, {"email": email}], "state": "active", "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "organization_id": 1}
    )
    if staff:
        all_ids.add(staff["id"])
        if not profile:
            profile = staff
    
    # Check organization_members too (tickets can be assigned to org members)
    org_member = await _db.organization_members.find_one(
        {"$or": [{"id": eng_id}, {"email": email}], "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "email": 1, "organization_id": 1}
    )
    if org_member:
        all_ids.add(org_member["id"])
        if not profile:
            profile = org_member
    
    if not profile:
        raise HTTPException(status_code=404, detail="Engineer profile not found")
    
    profile["all_ids"] = list(all_ids)
    return profile


@router.get("/engineer/assignment/pending")
async def engineer_get_pending(engineer: dict = Depends(get_current_engineer)):
    """Get pending assignments for logged-in engineer."""
    eng = await _resolve_engineer(engineer)
    tickets = await _db.tickets_v2.find({
        "assigned_to_id": {"$in": eng["all_ids"]},
        "organization_id": eng["organization_id"],
        "assignment_status": "pending",
        "is_open": True,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "timeline": 0}).sort("assigned_at", -1).to_list(50)
    return {"tickets": tickets, "decline_reasons": DECLINE_REASONS}


@router.post("/engineer/assignment/accept")
async def engineer_accept(data: AcceptJobRequest, engineer: dict = Depends(get_current_engineer)):
    """Engineer accepts job."""
    eng = await _resolve_engineer(engineer)
    ticket = await _db.tickets_v2.find_one({
        "id": data.ticket_id, "assigned_to_id": eng["id"],
        "assignment_status": "pending", "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Pending assignment not found")

    update = {
        "assignment_status": "accepted",
        "assignment_responded_at": now_ist(),
        "updated_at": now_ist(),
    }
    timeline_entry = {
        "id": str(uuid.uuid4()), "type": "assignment_accepted",
        "description": f"{eng['name']} accepted the assignment",
        "user_name": eng["name"], "created_at": now_ist(),
    }
    if data.proposed_time:
        update["scheduled_at"] = data.proposed_time
        timeline_entry["description"] += f" (rescheduled to {data.proposed_time[:16]})"

    await _db.tickets_v2.update_one(
        {"id": data.ticket_id},
        {"$set": update, "$push": {"timeline": timeline_entry}}
    )
    # Update existing schedules or create one if none exist
    existing_schedules = await _db.ticket_schedules.count_documents(
        {"ticket_id": data.ticket_id, "engineer_id": eng["id"], "status": {"$ne": "cancelled"}}
    )
    if existing_schedules > 0:
        await _db.ticket_schedules.update_many(
            {"ticket_id": data.ticket_id, "engineer_id": eng["id"], "status": "scheduled"},
            {"$set": {"status": "accepted"}}
        )
    else:
        # Create a schedule record so it shows in calendar
        sched_time = data.proposed_time or ticket.get("scheduled_at") or now_ist()
        sched_end = ticket.get("scheduled_end_at")
        if not sched_end and sched_time:
            try:
                from datetime import datetime as dt_cls
                st = dt_cls.fromisoformat(sched_time.replace("Z", "+00:00"))
                sched_end = (st + timedelta(hours=1)).isoformat()
            except Exception:
                sched_end = None
        await _db.ticket_schedules.insert_one({
            "id": str(uuid.uuid4()),
            "organization_id": eng["organization_id"],
            "ticket_id": data.ticket_id,
            "ticket_number": ticket.get("ticket_number"),
            "engineer_id": eng["id"],
            "engineer_name": eng["name"],
            "company_name": ticket.get("company_name"),
            "subject": ticket.get("subject"),
            "scheduled_at": sched_time,
            "scheduled_end_at": sched_end,
            "status": "accepted",
            "created_at": now_ist(),
        })
    # SLA log
    if ticket.get("assigned_at"):
        await _db.assignment_sla_logs.insert_one({
            "id": str(uuid.uuid4()), "organization_id": eng["organization_id"],
            "engineer_id": eng["id"], "engineer_name": eng["name"],
            "ticket_id": data.ticket_id, "ticket_number": ticket.get("ticket_number"),
            "assigned_at": ticket["assigned_at"], "responded_at": now_ist(),
            "response": "accepted", "created_at": now_ist(),
        })
    return {"status": "accepted", "ticket_id": data.ticket_id}


@router.post("/engineer/assignment/decline")
async def engineer_decline(data: DeclineJobRequest, engineer: dict = Depends(get_current_engineer)):
    """Engineer declines job."""
    eng = await _resolve_engineer(engineer)
    ticket = await _db.tickets_v2.find_one({
        "id": data.ticket_id, "assigned_to_id": eng["id"],
        "assignment_status": "pending", "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Pending assignment not found")

    reason_label = next((r["label"] for r in DECLINE_REASONS if r["id"] == data.reason_id), data.reason_id)

    update = {
        "assignment_status": "declined",
        "assignment_responded_at": now_ist(),
        "decline_reason": data.reason_id,
        "decline_reason_label": reason_label,
        "decline_detail": data.reason_detail,
        "updated_at": now_ist(),
    }
    timeline_entry = {
        "id": str(uuid.uuid4()), "type": "assignment_declined",
        "description": f"{eng['name']} declined: {reason_label}" + (f" — {data.reason_detail}" if data.reason_detail else ""),
        "user_name": eng["name"], "created_at": now_ist(),
    }
    await _db.tickets_v2.update_one(
        {"id": data.ticket_id},
        {"$set": update, "$push": {"timeline": timeline_entry}}
    )
    await _db.ticket_schedules.update_many(
        {"ticket_id": data.ticket_id, "engineer_id": eng["id"]},
        {"$set": {"status": "cancelled"}}
    )
    await create_notification(
        org_id=eng["organization_id"], notif_type="assignment_declined",
        title=f"Job Declined — #{ticket.get('ticket_number')}",
        message=f"{eng['name']} declined #{ticket.get('ticket_number')} ({ticket.get('subject', '')[:60]}). Reason: {reason_label}. Please reassign.",
        ticket_id=data.ticket_id,
        metadata={"engineer_id": eng["id"], "engineer_name": eng["name"],
                  "ticket_number": ticket.get("ticket_number"), "reason_id": data.reason_id,
                  "reason_label": reason_label, "reason_detail": data.reason_detail},
    )
    if ticket.get("assigned_at"):
        await _db.assignment_sla_logs.insert_one({
            "id": str(uuid.uuid4()), "organization_id": eng["organization_id"],
            "engineer_id": eng["id"], "engineer_name": eng["name"],
            "ticket_id": data.ticket_id, "ticket_number": ticket.get("ticket_number"),
            "assigned_at": ticket["assigned_at"], "responded_at": now_ist(),
            "response": "declined", "reason_id": data.reason_id, "created_at": now_ist(),
        })
    return {"status": "declined", "ticket_id": data.ticket_id}


@router.post("/engineer/assignment/reschedule")
async def engineer_reschedule(data: RescheduleJobRequest, engineer: dict = Depends(get_current_engineer)):
    """Engineer accepts but proposes different time."""
    eng = await _resolve_engineer(engineer)
    ticket = await _db.tickets_v2.find_one({
        "id": data.ticket_id, "assigned_to_id": eng["id"],
        "assignment_status": "pending", "is_deleted": {"$ne": True}
    })
    if not ticket:
        raise HTTPException(status_code=404, detail="Pending assignment not found")

    update = {
        "assignment_status": "accepted",
        "assignment_responded_at": now_ist(),
        "scheduled_at": data.proposed_time,
        "scheduled_end_at": data.proposed_end_time,
        "schedule_notes": data.notes,
        "updated_at": now_ist(),
    }
    timeline_entry = {
        "id": str(uuid.uuid4()), "type": "assignment_rescheduled",
        "description": f"{eng['name']} accepted & rescheduled to {data.proposed_time[:16]}",
        "user_name": eng["name"], "created_at": now_ist(),
    }
    await _db.tickets_v2.update_one(
        {"id": data.ticket_id},
        {"$set": update, "$push": {"timeline": timeline_entry}}
    )
    await _db.ticket_schedules.update_many(
        {"ticket_id": data.ticket_id, "engineer_id": eng["id"]},
        {"$set": {"status": "cancelled"}}
    )
    await _db.ticket_schedules.insert_one({
        "id": str(uuid.uuid4()), "organization_id": eng["organization_id"],
        "ticket_id": data.ticket_id, "ticket_number": ticket.get("ticket_number"),
        "engineer_id": eng["id"], "engineer_name": eng["name"],
        "company_name": ticket.get("company_name"), "subject": ticket.get("subject"),
        "scheduled_at": data.proposed_time, "scheduled_end_at": data.proposed_end_time,
        "notes": data.notes, "status": "accepted", "created_at": now_ist(),
    })
    return {"status": "rescheduled", "ticket_id": data.ticket_id}


@router.get("/engineer/dashboard")
async def engineer_dashboard(engineer: dict = Depends(get_current_engineer)):
    """Engineer's own dashboard data."""
    eng = await _resolve_engineer(engineer)
    org_id = eng["organization_id"]
    eng_id = eng["id"]

    # Pending acceptance
    pending = await _db.tickets_v2.find({
        "assigned_to_id": eng_id, "organization_id": org_id,
        "assignment_status": "pending", "is_open": True, "is_deleted": {"$ne": True}
    }, {"_id": 0, "timeline": 0}).sort("assigned_at", -1).to_list(20)

    # Accepted / active tickets
    active = await _db.tickets_v2.find({
        "assigned_to_id": eng_id, "organization_id": org_id,
        "is_open": True, "is_deleted": {"$ne": True},
        "assignment_status": {"$ne": "pending"}
    }, {"_id": 0, "timeline": 0}).sort("updated_at", -1).to_list(30)

    # Upcoming schedules
    from datetime import datetime as dt_cls
    now = dt_cls.now(IST).isoformat()
    schedules = await _db.ticket_schedules.find({
        "engineer_id": eng_id, "organization_id": org_id,
        "scheduled_at": {"$gte": now}, "status": {"$nin": ["cancelled"]}
    }, {"_id": 0}).sort("scheduled_at", 1).to_list(10)

    # Stats
    total_assigned = await _db.tickets_v2.count_documents({
        "assigned_to_id": eng_id, "organization_id": org_id,
        "is_open": True, "is_deleted": {"$ne": True}
    })
    today_str = dt_cls.now(IST).strftime("%Y-%m-%d")
    visits_today = await _db.ticket_schedules.count_documents({
        "engineer_id": eng_id, "organization_id": org_id,
        "scheduled_at": {"$gte": f"{today_str}T00:00:00", "$lte": f"{today_str}T23:59:59"},
        "status": {"$nin": ["cancelled"]}
    })

    return {
        "engineer": {"id": eng_id, "name": eng["name"]},
        "pending_tickets": pending,
        "active_tickets": active,
        "upcoming_schedules": schedules,
        "decline_reasons": DECLINE_REASONS,
        "stats": {
            "total_assigned": total_assigned,
            "pending_count": len(pending),
            "visits_today": visits_today,
            "active_count": len(active),
        }
    }



@router.get("/engineer/ticket/{ticket_id}")
async def engineer_ticket_detail(ticket_id: str, engineer: dict = Depends(get_current_engineer)):
    """Get full ticket details for an engineer - includes customer, device, repair history."""
    eng = await _resolve_engineer(engineer)
    org_id = eng["organization_id"]
    eng_id = eng["id"]

    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "assigned_to_id": eng_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found or not assigned to you")

    # Fetch company details
    company = None
    if ticket.get("company_id"):
        company = await _db.companies.find_one(
            {"id": ticket["company_id"]}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "email": 1, "address": 1, "city": 1, "state": 1}
        )

    # Fetch site details
    site = None
    if ticket.get("site_id"):
        site = await _db.sites.find_one(
            {"id": ticket["site_id"]}, {"_id": 0, "id": 1, "name": 1, "address": 1, "city": 1, "state": 1, "pincode": 1, "contact_name": 1, "contact_phone": 1}
        )

    # Fetch employee/contact details
    employee = None
    if ticket.get("employee_id"):
        employee = await _db.employees.find_one(
            {"id": ticket["employee_id"]}, {"_id": 0, "id": 1, "name": 1, "phone": 1, "email": 1, "designation": 1}
        )

    # Fetch device details
    device = None
    if ticket.get("device_id"):
        device = await _db.devices.find_one(
            {"id": ticket["device_id"]},
            {"_id": 0, "id": 1, "name": 1, "model": 1, "serial_number": 1, "manufacturer": 1,
             "device_type": 1, "warranty_end_date": 1, "warranty_status": 1, "purchase_date": 1,
             "ip_address": 1, "mac_address": 1, "location": 1, "notes": 1}
        )

    # Fetch repair/service history for this device or company
    repair_history = []
    history_query = {"organization_id": org_id, "is_deleted": {"$ne": True}, "id": {"$ne": ticket_id}}
    if ticket.get("device_id"):
        history_query["device_id"] = ticket["device_id"]
    elif ticket.get("company_id"):
        history_query["company_id"] = ticket["company_id"]
    
    if "device_id" in history_query or "company_id" in history_query:
        history_tickets = await _db.tickets_v2.find(
            history_query,
            {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "current_stage_name": 1,
             "priority_name": 1, "is_open": 1, "created_at": 1, "resolved_at": 1,
             "assigned_to_name": 1, "description": 1}
        ).sort("created_at", -1).to_list(20)
        repair_history = history_tickets

    # Fetch schedules for this ticket
    schedules = await _db.ticket_schedules.find(
        {"ticket_id": ticket_id, "organization_id": org_id, "status": {"$ne": "cancelled"}},
        {"_id": 0}
    ).sort("scheduled_at", -1).to_list(20)

    return {
        "ticket": ticket,
        "company": company,
        "site": site,
        "employee": employee,
        "device": device,
        "repair_history": repair_history,
        "schedules": schedules,
    }


# ── Admin Workforce Overview ──

@router.get("/ticketing/workforce/overview")
async def workforce_overview(admin: dict = Depends(get_current_admin)):
    """Admin-level workforce overview: all technicians, workloads, SLA, escalations."""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    engineers = await _db.engineers.find(
        {"organization_id": org_id, "is_active": {"$ne": False}, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    ).to_list(50)

    from datetime import datetime as dt_cls
    now = dt_cls.now(IST)
    today_str = now.strftime("%Y-%m-%d")
    cutoff = (now - timedelta(hours=AUTO_ESCALATION_HOURS)).isoformat()

    workforce = []
    total_pending = 0
    total_overdue = 0

    for eng in engineers:
        eid = eng["id"]

        open_count = await _db.tickets_v2.count_documents({
            "assigned_to_id": eid, "organization_id": org_id,
            "is_open": True, "is_deleted": {"$ne": True}
        })
        pending_count = await _db.tickets_v2.count_documents({
            "assigned_to_id": eid, "organization_id": org_id,
            "assignment_status": "pending", "is_open": True, "is_deleted": {"$ne": True}
        })
        declined_count = await _db.tickets_v2.count_documents({
            "assigned_to_id": eid, "organization_id": org_id,
            "assignment_status": "declined", "is_deleted": {"$ne": True}
        })
        visits_today = await _db.ticket_schedules.count_documents({
            "engineer_id": eid, "organization_id": org_id,
            "scheduled_at": {"$gte": f"{today_str}T00:00:00", "$lte": f"{today_str}T23:59:59"},
            "status": {"$nin": ["cancelled"]}
        })

        # SLA
        sla_logs = await _db.assignment_sla_logs.find(
            {"engineer_id": eid, "organization_id": org_id}, {"_id": 0}
        ).sort("created_at", -1).to_list(50)
        total_sla = len(sla_logs)
        accepted_sla = len([s for s in sla_logs if s.get("response") == "accepted"])
        acceptance_rate = round(accepted_sla / total_sla * 100, 1) if total_sla > 0 else None

        # Overdue pending
        overdue = await _db.tickets_v2.count_documents({
            "assigned_to_id": eid, "organization_id": org_id,
            "assignment_status": "pending", "assigned_at": {"$lte": cutoff},
            "is_open": True, "is_deleted": {"$ne": True}
        })

        total_pending += pending_count
        total_overdue += overdue

        workforce.append({
            "id": eid,
            "name": eng.get("name"),
            "email": eng.get("email"),
            "specialization": eng.get("specialization"),
            "is_active": eng.get("is_active", True),
            "open_tickets": open_count,
            "pending_acceptance": pending_count,
            "declined": declined_count,
            "visits_today": visits_today,
            "acceptance_rate": acceptance_rate,
            "overdue_pending": overdue,
            "salary": eng.get("salary"),
        })

    # Tickets needing reassignment (declined + unassigned)
    needs_reassignment = await _db.tickets_v2.find({
        "organization_id": org_id,
        "assignment_status": "declined",
        "is_open": True,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "company_name": 1,
        "assigned_to_name": 1, "decline_reason_label": 1, "decline_detail": 1,
        "updated_at": 1, "priority_name": 1}).sort("updated_at", -1).to_list(20)

    # Overdue escalations
    escalations = await _db.tickets_v2.find({
        "organization_id": org_id,
        "assignment_status": "pending",
        "assigned_at": {"$lte": cutoff},
        "is_open": True,
        "is_deleted": {"$ne": True},
    }, {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "company_name": 1,
        "assigned_to_id": 1, "assigned_to_name": 1, "assigned_at": 1,
        "priority_name": 1}).sort("assigned_at", 1).to_list(20)

    return {
        "workforce": workforce,
        "needs_reassignment": needs_reassignment,
        "escalations": escalations,
        "summary": {
            "total_technicians": len(workforce),
            "total_pending": total_pending,
            "total_overdue": total_overdue,
            "total_declined": len(needs_reassignment),
        },
        "escalation_threshold_hours": AUTO_ESCALATION_HOURS,
    }
