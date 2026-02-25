"""
Organization Calendar API Routes
=================================
Central calendar: org holidays, standard/emergency working hours,
and aggregated technician schedules.
"""

import uuid
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from services.auth import get_current_admin, get_current_engineer

router = APIRouter()
_db = None

def init_db(database):
    global _db
    _db = database


# ── Models ──────────────────────────────────────────────────────

class OrgHoliday(BaseModel):
    name: str
    date: str  # YYYY-MM-DD
    type: str = "public"  # public, company, optional

class OrgHolidayCreate(BaseModel):
    name: str
    date: str
    type: str = "public"

class StandardHours(BaseModel):
    monday: Dict = Field(default_factory=lambda: {"is_working": True, "start": "09:00", "end": "18:00"})
    tuesday: Dict = Field(default_factory=lambda: {"is_working": True, "start": "09:00", "end": "18:00"})
    wednesday: Dict = Field(default_factory=lambda: {"is_working": True, "start": "09:00", "end": "18:00"})
    thursday: Dict = Field(default_factory=lambda: {"is_working": True, "start": "09:00", "end": "18:00"})
    friday: Dict = Field(default_factory=lambda: {"is_working": True, "start": "09:00", "end": "18:00"})
    saturday: Dict = Field(default_factory=lambda: {"is_working": True, "start": "09:00", "end": "14:00"})
    sunday: Dict = Field(default_factory=lambda: {"is_working": False, "start": "09:00", "end": "18:00"})

class EmergencyHours(BaseModel):
    date: str  # YYYY-MM-DD
    reason: str
    start: str  # HH:MM
    end: str    # HH:MM

class EmergencyHoursCreate(BaseModel):
    date: str
    reason: str
    start: str
    end: str


# ── Org Holidays ────────────────────────────────────────────────

@router.get("/calendar/holidays")
async def list_holidays(
    year: Optional[int] = None,
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    query = {"organization_id": org_id}
    if year:
        query["date"] = {"$gte": f"{year}-01-01", "$lte": f"{year}-12-31"}

    holidays = await _db.org_holidays.find(query, {"_id": 0}).sort("date", 1).to_list(500)
    return holidays


@router.post("/calendar/holidays")
async def create_holiday(
    data: OrgHolidayCreate,
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    existing = await _db.org_holidays.find_one(
        {"organization_id": org_id, "date": data.date}, {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Holiday already exists for this date")

    holiday = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "name": data.name,
        "date": data.date,
        "type": data.type,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await _db.org_holidays.insert_one(holiday)
    return {k: v for k, v in holiday.items() if k != "_id"}


@router.delete("/calendar/holidays/{holiday_id}")
async def delete_holiday(
    holiday_id: str,
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    result = await _db.org_holidays.delete_one({"id": holiday_id, "organization_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Holiday not found")
    return {"status": "deleted"}


# ── Standard Working Hours ──────────────────────────────────────

@router.get("/calendar/standard-hours")
async def get_standard_hours(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    doc = await _db.org_standard_hours.find_one({"organization_id": org_id}, {"_id": 0})
    if not doc:
        return StandardHours().model_dump()
    return {k: v for k, v in doc.items() if k not in ("organization_id", "id")}


@router.put("/calendar/standard-hours")
async def update_standard_hours(
    data: StandardHours,
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    update = data.model_dump()
    update["organization_id"] = org_id
    update["updated_at"] = datetime.now(timezone.utc).isoformat()

    await _db.org_standard_hours.update_one(
        {"organization_id": org_id},
        {"$set": update},
        upsert=True
    )
    return update


# ── Emergency Working Hours ─────────────────────────────────────

@router.get("/calendar/emergency-hours")
async def list_emergency_hours(
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    query = {"organization_id": org_id}
    if date_from and date_to:
        query["date"] = {"$gte": date_from, "$lte": date_to}

    items = await _db.org_emergency_hours.find(query, {"_id": 0}).sort("date", 1).to_list(200)
    return items


@router.post("/calendar/emergency-hours")
async def create_emergency_hours(
    data: EmergencyHoursCreate,
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    entry = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "date": data.date,
        "reason": data.reason,
        "start": data.start,
        "end": data.end,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await _db.org_emergency_hours.insert_one(entry)
    return {k: v for k, v in entry.items() if k != "_id"}


@router.delete("/calendar/emergency-hours/{entry_id}")
async def delete_emergency_hours(
    entry_id: str,
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    result = await _db.org_emergency_hours.delete_one({"id": entry_id, "organization_id": org_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Entry not found")
    return {"status": "deleted"}


# ── Aggregated Calendar View ────────────────────────────────────

@router.get("/calendar/events")
async def get_calendar_events(
    date_from: str = Query(..., description="YYYY-MM-DD"),
    date_to: str = Query(..., description="YYYY-MM-DD"),
    engineer_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Get all calendar events: holidays, emergency hours, and all technician schedules."""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    events = []

    # 1. Org holidays in range
    holidays = await _db.org_holidays.find(
        {"organization_id": org_id, "date": {"$gte": date_from, "$lte": date_to}},
        {"_id": 0}
    ).to_list(200)
    for h in holidays:
        events.append({
            "id": h["id"], "type": "holiday",
            "title": h["name"], "date": h["date"],
            "all_day": True, "color": "#ef4444",
            "holiday_type": h.get("type", "public"),
        })

    # 2. Emergency hours in range
    emergency = await _db.org_emergency_hours.find(
        {"organization_id": org_id, "date": {"$gte": date_from, "$lte": date_to}},
        {"_id": 0}
    ).to_list(200)
    for e in emergency:
        events.append({
            "id": e["id"], "type": "emergency_hours",
            "title": f"Emergency: {e['reason']}",
            "date": e["date"], "start_time": e["start"], "end_time": e["end"],
            "all_day": False, "color": "#f59e0b",
        })

    # 3. Technician schedules from ticket_schedules + tickets_v2
    sched_query = {
        "organization_id": org_id,
        "scheduled_at": {"$gte": f"{date_from}T00:00:00", "$lte": f"{date_to}T23:59:59"},
        "status": {"$ne": "cancelled"},
    }
    if engineer_id:
        sched_query["engineer_id"] = engineer_id

    schedules = await _db.ticket_schedules.find(
        sched_query, {"_id": 0}
    ).sort("scheduled_at", 1).to_list(500)

    for s in schedules:
        events.append({
            "id": s.get("id", ""),
            "type": "schedule",
            "title": f"#{s.get('ticket_number', '')} - {s.get('company_name') or s.get('subject', 'Visit')}",
            "date": s.get("scheduled_at", "")[:10],
            "start_time": s.get("scheduled_at", "")[11:16],
            "end_time": (s.get("scheduled_end_at") or "")[11:16] or None,
            "all_day": False,
            "color": "#3b82f6",
            "engineer_id": s.get("engineer_id"),
            "engineer_name": s.get("engineer_name", ""),
            "ticket_number": s.get("ticket_number"),
            "company_name": s.get("company_name"),
        })

    # Also fetch from tickets_v2 with scheduled_at
    ticket_query = {
        "organization_id": org_id,
        "scheduled_at": {"$gte": f"{date_from}T00:00:00", "$lte": f"{date_to}T23:59:59"},
        "is_deleted": {"$ne": True},
    }
    if engineer_id:
        ticket_query["assigned_to_id"] = engineer_id

    tickets = await _db.tickets_v2.find(
        ticket_query,
        {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "company_name": 1,
         "scheduled_at": 1, "scheduled_end_at": 1, "assigned_to_id": 1, "assigned_to_name": 1,
         "current_stage_name": 1, "priority": 1}
    ).sort("scheduled_at", 1).to_list(500)

    existing_schedule_tickets = {s.get("ticket_number") for s in schedules}
    for t in tickets:
        if t.get("ticket_number") in existing_schedule_tickets:
            continue
        events.append({
            "id": t.get("id", ""),
            "type": "ticket",
            "title": f"#{t.get('ticket_number', '')} - {t.get('company_name') or t.get('subject', '')}",
            "date": t.get("scheduled_at", "")[:10],
            "start_time": t.get("scheduled_at", "")[11:16],
            "end_time": (t.get("scheduled_end_at") or "")[11:16] or None,
            "all_day": False,
            "color": "#8b5cf6",
            "engineer_id": t.get("assigned_to_id"),
            "engineer_name": t.get("assigned_to_name", ""),
            "ticket_number": t.get("ticket_number"),
            "company_name": t.get("company_name"),
            "stage": t.get("current_stage_name"),
            "priority": t.get("priority"),
        })

    # 4. Get all engineers for sidebar/filter
    engineers = await _db.engineers.find(
        {"organization_id": org_id, "is_active": {"$ne": False}, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "specialization": 1}
    ).to_list(100)

    return {
        "events": events,
        "engineers": engineers,
        "date_from": date_from,
        "date_to": date_to,
    }


# ── Engineer's own calendar ─────────────────────────────────────

@router.get("/calendar/my-schedule")
async def get_my_schedule(
    date_from: str = Query(...),
    date_to: str = Query(...),
    admin: dict = Depends(get_current_admin)
):
    """Get current user's schedule - for technician's personal calendar."""
    org_id = admin.get("organization_id")
    user_email = admin.get("email", admin.get("sub", ""))

    # Find engineer by email
    engineer = await _db.engineers.find_one(
        {"email": user_email, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "working_hours": 1, "holidays": 1}
    )
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer profile not found")

    eng_id = engineer["id"]

    # Get org holidays
    holidays = await _db.org_holidays.find(
        {"organization_id": org_id, "date": {"$gte": date_from, "$lte": date_to}},
        {"_id": 0}
    ).to_list(200)

    # Get personal schedules
    schedules = await _db.ticket_schedules.find({
        "engineer_id": eng_id,
        "organization_id": org_id,
        "scheduled_at": {"$gte": f"{date_from}T00:00:00", "$lte": f"{date_to}T23:59:59"},
        "status": {"$ne": "cancelled"},
    }, {"_id": 0}).sort("scheduled_at", 1).to_list(200)

    tickets = await _db.tickets_v2.find({
        "assigned_to_id": eng_id,
        "organization_id": org_id,
        "scheduled_at": {"$gte": f"{date_from}T00:00:00", "$lte": f"{date_to}T23:59:59"},
        "is_deleted": {"$ne": True},
    }, {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "company_name": 1,
        "scheduled_at": 1, "scheduled_end_at": 1, "current_stage_name": 1, "priority": 1}
    ).sort("scheduled_at", 1).to_list(200)

    events = []
    for h in holidays:
        events.append({
            "id": h["id"], "type": "holiday", "title": h["name"],
            "date": h["date"], "all_day": True, "color": "#ef4444",
        })
    for h in (engineer.get("holidays") or []):
        if date_from <= h <= date_to:
            events.append({
                "id": f"personal-{h}", "type": "personal_holiday",
                "title": "Personal Holiday", "date": h,
                "all_day": True, "color": "#f97316",
            })

    existing = set()
    for s in schedules:
        events.append({
            "id": s.get("id", ""), "type": "schedule",
            "title": f"#{s.get('ticket_number', '')} - {s.get('company_name') or 'Visit'}",
            "date": s.get("scheduled_at", "")[:10],
            "start_time": s.get("scheduled_at", "")[11:16],
            "end_time": (s.get("scheduled_end_at") or "")[11:16] or None,
            "all_day": False, "color": "#3b82f6",
            "ticket_number": s.get("ticket_number"),
            "company_name": s.get("company_name"),
        })
        existing.add(s.get("ticket_number"))

    for t in tickets:
        if t.get("ticket_number") in existing:
            continue
        events.append({
            "id": t.get("id", ""), "type": "ticket",
            "title": f"#{t.get('ticket_number', '')} - {t.get('company_name') or t.get('subject', '')}",
            "date": t.get("scheduled_at", "")[:10],
            "start_time": t.get("scheduled_at", "")[11:16],
            "end_time": (t.get("scheduled_end_at") or "")[11:16] or None,
            "all_day": False, "color": "#8b5cf6",
            "ticket_number": t.get("ticket_number"),
            "company_name": t.get("company_name"),
            "stage": t.get("current_stage_name"),
            "priority": t.get("priority"),
        })

    return {
        "engineer": engineer,
        "events": events,
        "working_hours": engineer.get("working_hours", {}),
        "date_from": date_from,
        "date_to": date_to,
    }
