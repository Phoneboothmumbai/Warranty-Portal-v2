"""
Customer Portal API — Multi-tenant portal endpoints
Provides public tenant resolution, company-scoped analytics, and portal management.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from collections import defaultdict
from typing import Optional
import logging

router = APIRouter(prefix="/portal", tags=["Customer Portal"])
_db = None
logger = logging.getLogger("portal")

def init_db(database):
    global _db
    _db = database

# Auth dependency
from services.auth import get_current_admin


# ══════════════════════════════════════════════════════════
# PUBLIC: Tenant Resolution (no auth needed)
# ══════════════════════════════════════════════════════════

@router.get("/tenant/{tenant_code}")
async def resolve_tenant(tenant_code: str):
    """Public endpoint: resolve tenant_code to company branding/config"""
    company = await _db.companies.find_one(
        {"tenant_code": tenant_code, "portal_enabled": True},
        {"_id": 0, "id": 1, "name": 1, "tenant_code": 1,
         "portal_theme": 1, "contact_email": 1, "address": 1,
         "logo_url": 1, "logo_base64": 1}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Portal not found")

    # Get the org settings for branding fallback
    org_id = (await _db.companies.find_one(
        {"tenant_code": tenant_code}, {"_id": 0, "organization_id": 1}
    ) or {}).get("organization_id")

    settings = await _db.settings.find_one(
        {"organization_id": org_id}, {"_id": 0, "company_name": 1, "logo_base64": 1, "logo_url": 1, "accent_color": 1}
    ) if org_id else None

    return {
        "company_id": company["id"],
        "company_name": company["name"],
        "tenant_code": company["tenant_code"],
        "portal_theme": company.get("portal_theme", {}),
        "logo_url": company.get("logo_url") or company.get("logo_base64") or (settings or {}).get("logo_base64") or (settings or {}).get("logo_url"),
        "provider_name": (settings or {}).get("company_name", "aftersales.support"),
        "accent_color": (settings or {}).get("accent_color", "#0F62FE"),
    }


# ══════════════════════════════════════════════════════════
# COMPANY AUTH: Login for tenant-specific portal
# ══════════════════════════════════════════════════════════

class TenantLoginRequest(BaseModel):
    email: str
    password: str

@router.post("/tenant/{tenant_code}/login")
async def tenant_login(tenant_code: str, req: TenantLoginRequest):
    """Login to a company-specific portal"""
    company = await _db.companies.find_one(
        {"tenant_code": tenant_code, "portal_enabled": True},
        {"_id": 0, "id": 1, "organization_id": 1}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Portal not found")

    import bcrypt, jwt, os
    user = await _db.company_portal_users.find_one(
        {"company_id": company["id"], "email": req.email, "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not user:
        # Fallback: check company_employees with password
        user = await _db.company_employees.find_one(
            {"company_id": company["id"], "email": req.email, "is_active": True, "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
    if not user or not user.get("password_hash"):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not bcrypt.checkpw(req.password.encode(), user["password_hash"].encode()):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = jwt.encode(
        {"sub": user["id"], "company_id": company["id"], "org_id": company["organization_id"],
         "tenant_code": tenant_code, "type": "portal_user",
         "exp": datetime.now(timezone.utc) + timedelta(hours=24)},
        os.environ.get("JWT_SECRET", "your-secret-key"), algorithm="HS256"
    )
    return {
        "access_token": token,
        "user": {
            "id": user["id"], "name": user["name"], "email": user["email"],
            "company_id": company["id"], "tenant_code": tenant_code,
        }
    }


# ══════════════════════════════════════════════════════════
# PORTAL USER: Get current user + company data
# ══════════════════════════════════════════════════════════

async def get_portal_user(authorization: str = Depends(lambda: None)):
    """Dependency to extract portal user from JWT"""
    from fastapi import Request
    # This is handled by the route-level token extraction
    pass

@router.get("/tenant/{tenant_code}/me")
async def get_portal_me(tenant_code: str):
    """Get current portal user info"""
    from fastapi import Request
    # We'll rely on the company auth system
    pass


# ══════════════════════════════════════════════════════════
# COMPANY ANALYTICS (for portal users)
# ══════════════════════════════════════════════════════════

@router.get("/tenant/{tenant_code}/analytics")
async def company_analytics(tenant_code: str, days: int = Query(30, ge=1, le=365)):
    """Company-scoped analytics — public after tenant resolution"""
    company = await _db.companies.find_one(
        {"tenant_code": tenant_code, "portal_enabled": True},
        {"_id": 0, "id": 1, "organization_id": 1, "name": 1}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Portal not found")

    cid = company["id"]
    org_id = company["organization_id"]
    start_iso = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    now_dt = datetime.now(timezone.utc)
    now_str = now_dt.strftime("%Y-%m-%d")

    # Tickets
    tickets = await _db.tickets_v2.find(
        {"organization_id": org_id, "company_id": cid, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(5000)
    period_tickets = [t for t in tickets if t.get("created_at", "") >= start_iso]

    open_t = sum(1 for t in tickets if t.get("is_open"))
    closed_t = sum(1 for t in tickets if not t.get("is_open"))

    # Resolution times
    res_times = []
    for t in tickets:
        if t.get("closed_at") and t.get("created_at"):
            try:
                c = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                cl = datetime.fromisoformat(t["closed_at"].replace("Z", "+00:00"))
                res_times.append((cl - c).total_seconds() / 3600)
            except Exception:
                pass

    avg_resolution = round(sum(res_times) / max(len(res_times), 1), 1)

    # Volume by day
    volume_by_day = defaultdict(int)
    for t in period_tickets:
        volume_by_day[t.get("created_at", "")[:10]] += 1

    # Stage distribution
    stage_dist = defaultdict(int)
    for t in tickets:
        if t.get("is_open"):
            stage_dist[t.get("current_stage_name", "Open")] += 1

    # Priority distribution
    priority_dist = defaultdict(int)
    for t in period_tickets:
        priority_dist[t.get("priority_name", "medium")] += 1

    # Topic distribution
    topic_dist = defaultdict(int)
    for t in period_tickets:
        topic_dist[t.get("help_topic_name", "Other")] += 1

    # Devices
    devices = await _db.devices.find(
        {"organization_id": org_id, "company_id": cid}, {"_id": 0}
    ).to_list(5000)

    # Warranty status
    active_warranty = expired = exp_30 = exp_60 = exp_90 = 0
    for d in devices:
        we = d.get("warranty_end_date", "")
        if not we:
            continue
        try:
            we_dt = datetime.strptime(str(we)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            dl = (we_dt - now_dt).days
            if dl < 0:
                expired += 1
            elif dl <= 30:
                exp_30 += 1
            elif dl <= 60:
                exp_60 += 1
            elif dl <= 90:
                exp_90 += 1
            else:
                active_warranty += 1
        except Exception:
            pass

    # AMC contracts
    contracts = await _db.amc_contracts.find(
        {"organization_id": org_id, "company_id": cid, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)
    active_contracts = len([c for c in contracts if c.get("end_date", "") >= now_str])

    # SLA
    breached = sum(1 for t in tickets if t.get("sla_breached"))
    compliance = round((len(tickets) - breached) / max(len(tickets), 1) * 100, 1)

    # Brand distribution
    brand_dist = defaultdict(int)
    for d in devices:
        brand_dist[d.get("brand", "Unknown")] += 1

    # Recent tickets
    recent = sorted(tickets, key=lambda t: t.get("created_at", ""), reverse=True)[:5]
    recent_list = [{
        "id": t.get("id"), "ticket_number": t.get("ticket_number"),
        "subject": t.get("subject"), "status": t.get("current_stage_name", "Open"),
        "priority": t.get("priority_name", "medium"), "created": t.get("created_at", "")[:10],
        "is_open": t.get("is_open"),
    } for t in recent]

    return {
        "company_name": company["name"],
        "summary": {
            "total_tickets": len(tickets),
            "open_tickets": open_t,
            "closed_tickets": closed_t,
            "period_tickets": len(period_tickets),
            "avg_resolution_hours": avg_resolution,
            "total_devices": len(devices),
            "active_warranty": active_warranty,
            "expired_warranty": expired,
            "expiring_30d": exp_30,
            "active_contracts": active_contracts,
            "sla_compliance": compliance,
        },
        "volume_by_day": [{"date": k, "count": v} for k, v in sorted(volume_by_day.items())],
        "stage_distribution": [{"name": k, "count": v} for k, v in sorted(stage_dist.items(), key=lambda x: -x[1])],
        "priority_distribution": [{"name": k, "count": v} for k, v in priority_dist.items()],
        "topic_distribution": [{"name": k, "count": v} for k, v in sorted(topic_dist.items(), key=lambda x: -x[1])[:10]],
        "warranty_timeline": [
            {"label": "Expired", "count": expired},
            {"label": "0-30 days", "count": exp_30},
            {"label": "31-60 days", "count": exp_60},
            {"label": "61-90 days", "count": exp_90},
            {"label": "Active", "count": active_warranty},
        ],
        "brand_distribution": [{"name": k, "count": v} for k, v in sorted(brand_dist.items(), key=lambda x: -x[1])[:10]],
        "recent_tickets": recent_list,
    }


# ══════════════════════════════════════════════════════════
# COMPANY DATA ENDPOINTS (for portal sub-pages)
# ══════════════════════════════════════════════════════════

async def _resolve_company(tenant_code: str):
    """Helper to resolve tenant_code -> company doc"""
    company = await _db.companies.find_one(
        {"tenant_code": tenant_code, "portal_enabled": True},
        {"_id": 0, "id": 1, "organization_id": 1, "name": 1}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Portal not found")
    return company


@router.get("/tenant/{tenant_code}/tickets")
async def company_tickets(
    tenant_code: str,
    status: Optional[str] = Query(None, description="open|closed|all"),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Full ticket list for a company portal"""
    company = await _resolve_company(tenant_code)
    cid, org_id = company["id"], company["organization_id"]

    query = {"organization_id": org_id, "company_id": cid, "is_deleted": {"$ne": True}}
    if status == "open":
        query["is_open"] = True
    elif status == "closed":
        query["is_open"] = False

    if search:
        query["$or"] = [
            {"subject": {"$regex": search, "$options": "i"}},
            {"ticket_number": {"$regex": search, "$options": "i"}},
        ]

    total = await _db.tickets_v2.count_documents(query)
    skip = (page - 1) * limit
    tickets_cursor = _db.tickets_v2.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit)
    tickets = await tickets_cursor.to_list(limit)

    # Enrich with staff name for assigned engineer
    staff_ids = list({t.get("assigned_to") for t in tickets if t.get("assigned_to")})
    staff_map = {}
    if staff_ids:
        staff_docs = await _db.staff.find(
            {"id": {"$in": staff_ids}}, {"_id": 0, "id": 1, "name": 1}
        ).to_list(100)
        staff_map = {s["id"]: s["name"] for s in staff_docs}

    result = []
    for t in tickets:
        result.append({
            "id": t.get("id"),
            "ticket_number": t.get("ticket_number"),
            "subject": t.get("subject"),
            "description": t.get("description", ""),
            "status": t.get("current_stage_name", "Open"),
            "priority": t.get("priority_name", "medium"),
            "help_topic": t.get("help_topic_name", ""),
            "is_open": t.get("is_open", True),
            "assigned_to": staff_map.get(t.get("assigned_to"), "Unassigned"),
            "created_at": t.get("created_at", ""),
            "updated_at": t.get("updated_at", ""),
            "closed_at": t.get("closed_at"),
            "sla_breached": t.get("sla_breached", False),
        })

    return {"tickets": result, "total": total, "page": page, "limit": limit}


@router.get("/tenant/{tenant_code}/devices")
async def company_devices(
    tenant_code: str,
    search: Optional[str] = Query(None),
    warranty: Optional[str] = Query(None, description="active|expired|expiring"),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
):
    """Full device list for a company portal"""
    company = await _resolve_company(tenant_code)
    cid, org_id = company["id"], company["organization_id"]
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    query = {"organization_id": org_id, "company_id": cid}
    if search:
        query["$or"] = [
            {"serial_number": {"$regex": search, "$options": "i"}},
            {"brand": {"$regex": search, "$options": "i"}},
            {"model": {"$regex": search, "$options": "i"}},
            {"hostname": {"$regex": search, "$options": "i"}},
        ]

    total = await _db.devices.count_documents(query)
    skip = (page - 1) * limit
    devices = await _db.devices.find(
        query, {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)

    result = []
    for d in devices:
        we = d.get("warranty_end_date", "")
        w_status = "unknown"
        if we:
            try:
                we_dt = datetime.strptime(str(we)[:10], "%Y-%m-%d")
                days_left = (we_dt - datetime.strptime(now_str, "%Y-%m-%d")).days
                if days_left < 0:
                    w_status = "expired"
                elif days_left <= 30:
                    w_status = "expiring"
                else:
                    w_status = "active"
            except Exception:
                pass

        if warranty and w_status != warranty:
            continue

        result.append({
            "id": d.get("id"),
            "serial_number": d.get("serial_number", ""),
            "brand": d.get("brand", ""),
            "model": d.get("model", ""),
            "hostname": d.get("hostname", ""),
            "device_type": d.get("device_type", d.get("type", "")),
            "os": d.get("os", ""),
            "warranty_start_date": d.get("warranty_start_date", ""),
            "warranty_end_date": we,
            "warranty_status": w_status,
            "site_name": d.get("site_name", ""),
            "assigned_user": d.get("assigned_user", d.get("user_name", "")),
            "status": d.get("status", "active"),
            "created_at": d.get("created_at", ""),
        })

    return {"devices": result, "total": total, "page": page, "limit": limit}


@router.get("/tenant/{tenant_code}/contracts")
async def company_contracts(tenant_code: str):
    """AMC contracts for a company portal"""
    company = await _resolve_company(tenant_code)
    cid, org_id = company["id"], company["organization_id"]
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    contracts = await _db.amc_contracts.find(
        {"organization_id": org_id, "company_id": cid, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(200)

    result = []
    for c in contracts:
        end = c.get("end_date", "")
        status = "expired"
        if end >= now_str:
            status = "active"

        # Count devices in contract
        device_count = 0
        if c.get("device_ids"):
            device_count = len(c["device_ids"])
        elif c.get("id"):
            device_count = await _db.devices.count_documents({
                "organization_id": org_id, "company_id": cid,
                "amc_contract_id": c["id"]
            })

        result.append({
            "id": c.get("id"),
            "contract_number": c.get("contract_number", c.get("id", "")[:8]),
            "name": c.get("name", c.get("contract_name", "AMC Contract")),
            "type": c.get("contract_type", c.get("type", "AMC")),
            "start_date": c.get("start_date", ""),
            "end_date": end,
            "status": status,
            "device_count": device_count,
            "value": c.get("total_value", c.get("contract_value", 0)),
            "sla_type": c.get("sla_type", ""),
            "coverage": c.get("coverage_type", c.get("coverage", "")),
        })

    active = sum(1 for r in result if r["status"] == "active")
    expired = sum(1 for r in result if r["status"] == "expired")
    return {"contracts": result, "total": len(result), "active": active, "expired": expired}


@router.get("/tenant/{tenant_code}/profile")
async def company_profile(tenant_code: str):
    """Company profile info for portal"""
    company = await _db.companies.find_one(
        {"tenant_code": tenant_code, "portal_enabled": True},
        {"_id": 0, "id": 1, "name": 1, "contact_email": 1, "contact_name": 1,
         "contact_phone": 1, "address": 1, "city": 1, "state": 1, "pincode": 1,
         "gst_number": 1, "tenant_code": 1, "portal_welcome_message": 1}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Portal not found")

    org_id = (await _db.companies.find_one(
        {"tenant_code": tenant_code}, {"_id": 0, "organization_id": 1}
    ) or {}).get("organization_id")

    # Count summary stats
    cid = company["id"]
    device_count = await _db.devices.count_documents({"organization_id": org_id, "company_id": cid})
    ticket_count = await _db.tickets_v2.count_documents({"organization_id": org_id, "company_id": cid, "is_deleted": {"$ne": True}})
    contract_count = await _db.amc_contracts.count_documents({"organization_id": org_id, "company_id": cid, "is_deleted": {"$ne": True}})

    return {
        **company,
        "stats": {
            "devices": device_count,
            "tickets": ticket_count,
            "contracts": contract_count,
        }
    }



# ══════════════════════════════════════════════════════════
# ADMIN: Portal Management per company
# ══════════════════════════════════════════════════════════

class PortalSettings(BaseModel):
    portal_enabled: Optional[bool] = None
    tenant_code: Optional[str] = None
    portal_theme: Optional[dict] = None
    portal_welcome_message: Optional[str] = None

@router.get("/admin/companies")
async def list_portal_companies(admin: dict = Depends(get_current_admin)):
    """List all companies with their portal status"""
    org_id = admin.get("organization_id")
    companies = await _db.companies.find(
        {"organization_id": org_id},
        {"_id": 0, "id": 1, "name": 1, "tenant_code": 1, "portal_enabled": 1,
         "portal_theme": 1, "contact_email": 1, "portal_welcome_message": 1}
    ).to_list(500)
    return companies


@router.put("/admin/companies/{company_id}/settings")
async def update_portal_settings(
    company_id: str,
    settings: PortalSettings,
    admin: dict = Depends(get_current_admin)
):
    """Update portal settings for a company"""
    org_id = admin.get("organization_id")
    company = await _db.companies.find_one(
        {"id": company_id, "organization_id": org_id}, {"_id": 0, "id": 1}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    update = {}
    if settings.portal_enabled is not None:
        update["portal_enabled"] = settings.portal_enabled
    if settings.tenant_code is not None:
        # Check uniqueness
        existing = await _db.companies.find_one(
            {"tenant_code": settings.tenant_code, "id": {"$ne": company_id}},
            {"_id": 0, "id": 1}
        )
        if existing:
            raise HTTPException(status_code=400, detail="Tenant code already in use")
        update["tenant_code"] = settings.tenant_code
    if settings.portal_theme is not None:
        update["portal_theme"] = settings.portal_theme
    if settings.portal_welcome_message is not None:
        update["portal_welcome_message"] = settings.portal_welcome_message

    if update:
        await _db.companies.update_one({"id": company_id}, {"$set": update})
    return {"success": True}


@router.post("/admin/companies/{company_id}/create-portal-user")
async def create_portal_user_for_company(
    company_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Create a default portal admin user for a company using the company's contact info"""
    import bcrypt, uuid
    org_id = admin.get("organization_id")
    company = await _db.companies.find_one(
        {"id": company_id, "organization_id": org_id},
        {"_id": 0, "id": 1, "name": 1, "contact_email": 1, "contact_name": 1}
    )
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    email = company.get("contact_email")
    if not email:
        raise HTTPException(status_code=400, detail="Company has no contact email")

    # Check if user already exists
    existing = await _db.company_portal_users.find_one(
        {"company_id": company_id, "email": email}, {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Portal user already exists for this email")

    # Generate password
    default_pw = "Welcome@123"
    pw_hash = bcrypt.hashpw(default_pw.encode(), bcrypt.gensalt()).decode()

    user = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "organization_id": org_id,
        "name": company.get("contact_name", "Admin"),
        "email": email,
        "password_hash": pw_hash,
        "role": "admin",
        "is_active": True,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await _db.company_portal_users.insert_one(user)

    return {
        "success": True,
        "user_id": user["id"],
        "email": email,
        "default_password": default_pw,
        "message": f"Portal user created for {email}. Default password: {default_pw}"
    }
