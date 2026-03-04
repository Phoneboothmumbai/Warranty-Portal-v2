"""
Analytics Engine - Comprehensive analytics for Warranty & Asset Tracking Portal
Covers 10 modules: Ticket Intelligence, Workforce, Financial, Client Health,
Asset Intelligence, SLA Compliance, Workflow, Inventory, Contracts, Operational Intelligence
"""
from fastapi import APIRouter, Depends, Query
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import time, logging

router = APIRouter(prefix="/analytics", tags=["Analytics"])
_db = None
logger = logging.getLogger("analytics")

# Simple in-memory cache with TTL
_cache = {}
CACHE_TTL = 300  # 5 minutes

def init_db(database):
    global _db
    _db = database

def _cached(key, ttl=CACHE_TTL):
    if key in _cache:
        data, ts = _cache[key]
        if time.time() - ts < ttl:
            return data
    return None

def _set_cache(key, data):
    _cache[key] = (data, time.time())

# Auth dependency
from services.auth import get_current_admin

def _parse_dates(days_back: int):
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=days_back)
    return start.isoformat(), now.isoformat()


# ══════════════════════════════════════════════════════════
# 1. TICKET INTELLIGENCE
# ══════════════════════════════════════════════════════════

@router.get("/tickets")
async def ticket_intelligence(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    cache_key = f"ticket_intel:{org_id}:{days}"
    cached = _cached(cache_key)
    if cached:
        return cached

    start_iso, _ = _parse_dates(days)
    base_filter = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    all_tickets = await _db.tickets_v2.find(base_filter, {"_id": 0}).to_list(5000)
    period_tickets = [t for t in all_tickets if t.get("created_at", "") >= start_iso]

    # Volume by day
    volume_by_day = defaultdict(int)
    for t in period_tickets:
        day = t.get("created_at", "")[:10]
        volume_by_day[day] += 1

    # Stage distribution
    stage_dist = defaultdict(int)
    for t in all_tickets:
        if t.get("is_open"):
            stage_dist[t.get("current_stage_name", "Unknown")] += 1

    # Priority distribution
    priority_dist = defaultdict(int)
    for t in period_tickets:
        priority_dist[t.get("priority_name", "medium")] += 1

    # Help topic breakdown
    topic_dist = defaultdict(int)
    for t in period_tickets:
        topic_dist[t.get("help_topic_name", "Unknown")] += 1

    # Source analysis
    source_dist = defaultdict(int)
    for t in period_tickets:
        source_dist[t.get("source", "web")] += 1

    # Resolution time (for closed tickets)
    resolution_times = []
    for t in all_tickets:
        if t.get("closed_at") and t.get("created_at"):
            try:
                created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                closed = datetime.fromisoformat(t["closed_at"].replace("Z", "+00:00"))
                hours = (closed - created).total_seconds() / 3600
                resolution_times.append(hours)
            except Exception:
                pass

    avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else 0
    resolution_times.sort()
    p95 = resolution_times[int(len(resolution_times) * 0.95)] if resolution_times else 0

    # First response time
    response_times = []
    for t in all_tickets:
        if t.get("first_response_at") and t.get("created_at"):
            try:
                created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                responded = datetime.fromisoformat(t["first_response_at"].replace("Z", "+00:00"))
                hours = (responded - created).total_seconds() / 3600
                response_times.append(hours)
            except Exception:
                pass

    avg_first_response = sum(response_times) / len(response_times) if response_times else 0

    # Heat map (day of week x hour)
    heatmap = defaultdict(lambda: defaultdict(int))
    for t in period_tickets:
        try:
            dt = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
            heatmap[dt.strftime("%a")][dt.hour] += 1
        except Exception:
            pass

    # Reopen rate (tickets that were closed then reopened)
    reopen_count = sum(1 for t in all_tickets if t.get("closed_at") and t.get("is_open"))

    # Unassigned vs assigned
    unassigned = sum(1 for t in all_tickets if t.get("is_open") and not t.get("assigned_to_id"))
    assigned = sum(1 for t in all_tickets if t.get("is_open") and t.get("assigned_to_id"))

    result = {
        "summary": {
            "total_tickets": len(all_tickets),
            "period_tickets": len(period_tickets),
            "open_tickets": sum(1 for t in all_tickets if t.get("is_open")),
            "closed_tickets": sum(1 for t in all_tickets if not t.get("is_open")),
            "unassigned": unassigned,
            "assigned": assigned,
            "avg_resolution_hours": round(avg_resolution, 1),
            "p95_resolution_hours": round(p95, 1),
            "avg_first_response_hours": round(avg_first_response, 1),
            "reopen_rate": round(reopen_count / max(len(all_tickets), 1) * 100, 1),
        },
        "volume_by_day": [{"date": k, "count": v} for k, v in sorted(volume_by_day.items())],
        "stage_distribution": [{"name": k, "count": v} for k, v in sorted(stage_dist.items(), key=lambda x: -x[1])],
        "priority_distribution": [{"name": k, "count": v} for k, v in priority_dist.items()],
        "topic_distribution": [{"name": k, "count": v} for k, v in sorted(topic_dist.items(), key=lambda x: -x[1])[:15]],
        "source_distribution": [{"name": k, "count": v} for k, v in source_dist.items()],
        "heatmap": {day: dict(hours) for day, hours in heatmap.items()},
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 2. WORKFORCE PERFORMANCE
# ══════════════════════════════════════════════════════════

@router.get("/workforce")
async def workforce_performance(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    cache_key = f"workforce:{org_id}:{days}"
    cached = _cached(cache_key)
    if cached:
        return cached

    start_iso, _ = _parse_dates(days)
    base = {"organization_id": org_id, "is_deleted": {"$ne": True}}

    engineers = await _db.engineers.find(
        {**base, "is_active": True}, {"_id": 0, "id": 1, "name": 1, "email": 1, "phone": 1}
    ).to_list(200)

    all_tickets = await _db.tickets_v2.find(base, {"_id": 0}).to_list(5000)
    visits = await _db.service_visits_new.find({"organization_id": org_id}, {"_id": 0}).to_list(2000)
    parts_reqs = await _db.parts_requests.find({"organization_id": org_id}, {"_id": 0}).to_list(1000)
    sla_logs = await _db.assignment_sla_logs.find({"organization_id": org_id}, {"_id": 0}).to_list(1000)

    eng_map = {e["id"]: e["name"] for e in engineers}
    scorecards = []

    for eng in engineers:
        eid = eng["id"]
        assigned = [t for t in all_tickets if t.get("assigned_to_id") == eid]
        period_assigned = [t for t in assigned if t.get("created_at", "") >= start_iso]
        closed = [t for t in assigned if not t.get("is_open")]
        eng_visits = [v for v in visits if v.get("technician_id") == eid]
        eng_parts = [p for p in parts_reqs if p.get("engineer_id") == eid]
        eng_sla = [s for s in sla_logs if s.get("engineer_id") == eid]

        # Resolution times
        res_times = []
        for t in closed:
            if t.get("closed_at") and t.get("assigned_at"):
                try:
                    a = datetime.fromisoformat(t["assigned_at"].replace("Z", "+00:00"))
                    c = datetime.fromisoformat(t["closed_at"].replace("Z", "+00:00"))
                    res_times.append((c - a).total_seconds() / 3600)
                except Exception:
                    pass

        # SLA response times
        resp_times = []
        for s in eng_sla:
            if s.get("responded_at") and s.get("assigned_at"):
                try:
                    a = datetime.fromisoformat(s["assigned_at"].replace("Z", "+00:00"))
                    r = datetime.fromisoformat(s["responded_at"].replace("Z", "+00:00"))
                    resp_times.append((r - a).total_seconds() / 60)
                except Exception:
                    pass

        # Visit hours
        total_visit_hours = sum((v.get("duration_minutes") or 0) / 60 for v in eng_visits)

        # First time fix rate
        tickets_with_one_visit = 0
        for t in closed:
            t_visits = [v for v in eng_visits if v.get("ticket_id") == t.get("id")]
            if len(t_visits) == 1:
                tickets_with_one_visit += 1

        parts_cost = sum(p.get("grand_total", 0) for p in eng_parts)

        scorecards.append({
            "id": eid,
            "name": eng["name"],
            "total_assigned": len(assigned),
            "period_assigned": len(period_assigned),
            "closed": len(closed),
            "open": len(assigned) - len(closed),
            "avg_resolution_hours": round(sum(res_times) / max(len(res_times), 1), 1),
            "avg_response_minutes": round(sum(resp_times) / max(len(resp_times), 1), 1),
            "total_visits": len(eng_visits),
            "total_visit_hours": round(total_visit_hours, 1),
            "first_time_fix_rate": round(tickets_with_one_visit / max(len(closed), 1) * 100, 1),
            "parts_requests": len(eng_parts),
            "parts_cost": round(parts_cost, 2),
        })

    # Workload distribution
    workload = [{"name": s["name"], "open": s["open"], "closed": s["closed"]} for s in scorecards]

    result = {
        "summary": {
            "total_engineers": len(engineers),
            "total_assigned_tickets": sum(s["total_assigned"] for s in scorecards),
            "avg_tickets_per_engineer": round(sum(s["total_assigned"] for s in scorecards) / max(len(engineers), 1), 1),
            "total_visits": sum(s["total_visits"] for s in scorecards),
            "avg_first_time_fix": round(sum(s["first_time_fix_rate"] for s in scorecards) / max(len(scorecards), 1), 1),
        },
        "scorecards": sorted(scorecards, key=lambda x: -x["total_assigned"]),
        "workload_distribution": workload,
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 3. FINANCIAL ANALYTICS
# ══════════════════════════════════════════════════════════

@router.get("/financial")
async def financial_analytics(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    cache_key = f"financial:{org_id}:{days}"
    cached = _cached(cache_key)
    if cached:
        return cached

    start_iso, _ = _parse_dates(days)

    quotations = await _db.quotations.find(
        {"organization_id": org_id}, {"_id": 0}
    ).to_list(5000)
    pending_bills = await _db.pending_bills.find(
        {"organization_id": org_id}, {"_id": 0}
    ).to_list(1000)
    parts_reqs = await _db.parts_requests.find(
        {"organization_id": org_id}, {"_id": 0}
    ).to_list(1000)
    amc_contracts = await _db.amc_contracts.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(500)
    approvals = await _db.quotation_approvals.find(
        {"organization_id": org_id}, {"_id": 0}
    ).to_list(1000)

    # Quotation pipeline
    q_status = defaultdict(int)
    q_amounts = defaultdict(float)
    for q in quotations:
        status = q.get("status", "draft")
        q_status[status] += 1
        q_amounts[status] += q.get("total_amount", 0)

    total_quoted = sum(q.get("total_amount", 0) for q in quotations)
    total_approved = sum(q.get("total_amount", 0) for q in quotations if q.get("status") == "approved")
    conversion_rate = len([q for q in quotations if q.get("status") == "approved"]) / max(len(quotations), 1) * 100

    # Parts cost
    total_parts_cost = sum(p.get("grand_total", 0) for p in parts_reqs)
    parts_by_status = defaultdict(float)
    for p in parts_reqs:
        parts_by_status[p.get("status", "pending")] += p.get("grand_total", 0)

    # Pending bills aging
    now = datetime.now(timezone.utc)
    aging_buckets = {"0-30": 0, "31-60": 0, "61-90": 0, "90+": 0}
    for b in pending_bills:
        try:
            created = datetime.fromisoformat(b.get("created_at", "").replace("Z", "+00:00"))
            age = (now - created).days
            if age <= 30:
                aging_buckets["0-30"] += b.get("grand_total", 0)
            elif age <= 60:
                aging_buckets["31-60"] += b.get("grand_total", 0)
            elif age <= 90:
                aging_buckets["61-90"] += b.get("grand_total", 0)
            else:
                aging_buckets["90+"] += b.get("grand_total", 0)
        except Exception:
            aging_buckets["0-30"] += b.get("grand_total", 0)

    # Revenue by month (from quotations)
    revenue_by_month = defaultdict(float)
    for q in quotations:
        if q.get("status") == "approved":
            month = q.get("created_at", "")[:7]
            revenue_by_month[month] += q.get("total_amount", 0)

    # AMC revenue
    amc_total = 0
    for c in amc_contracts:
        pkg = c.get("custom_price") or 0
        amc_total += pkg

    result = {
        "summary": {
            "total_quoted": round(total_quoted, 2),
            "total_approved": round(total_approved, 2),
            "conversion_rate": round(conversion_rate, 1),
            "total_parts_cost": round(total_parts_cost, 2),
            "pending_bills_total": round(sum(b.get("grand_total", 0) for b in pending_bills), 2),
            "active_amc_contracts": len([c for c in amc_contracts if c.get("end_date", "") >= now.strftime("%Y-%m-%d")]),
        },
        "quotation_pipeline": [{"status": k, "count": q_status[k], "amount": round(q_amounts[k], 2)} for k in q_status],
        "revenue_by_month": [{"month": k, "amount": round(v, 2)} for k, v in sorted(revenue_by_month.items())],
        "parts_by_status": [{"status": k, "amount": round(v, 2)} for k, v in parts_by_status.items()],
        "aging_buckets": [{"bucket": k, "amount": round(v, 2)} for k, v in aging_buckets.items()],
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 4. CLIENT HEALTH SCORE
# ══════════════════════════════════════════════════════════

@router.get("/clients")
async def client_health(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    cache_key = f"clients:{org_id}:{days}"
    cached = _cached(cache_key)
    if cached:
        return cached

    companies = await _db.companies.find(
        {"organization_id": org_id}, {"_id": 0, "id": 1, "name": 1, "amc_status": 1}
    ).to_list(500)
    all_tickets = await _db.tickets_v2.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(5000)
    devices = await _db.devices.find(
        {"organization_id": org_id}, {"_id": 0, "id": 1, "company_id": 1}
    ).to_list(5000)
    quotations = await _db.quotations.find(
        {"organization_id": org_id}, {"_id": 0, "company_id": 1, "total_amount": 1, "status": 1}
    ).to_list(5000)

    start_iso, _ = _parse_dates(days)
    company_scores = []

    for comp in companies:
        cid = comp["id"]
        c_tickets = [t for t in all_tickets if t.get("company_id") == cid]
        c_period = [t for t in c_tickets if t.get("created_at", "") >= start_iso]
        c_open = [t for t in c_tickets if t.get("is_open")]
        c_devices = [d for d in devices if d.get("company_id") == cid]
        c_quotes = [q for q in quotations if q.get("company_id") == cid]
        c_approved = sum(q.get("total_amount", 0) for q in c_quotes if q.get("status") == "approved")
        c_pending = sum(q.get("total_amount", 0) for q in c_quotes if q.get("status") in ("sent", "draft", "pending"))

        # SLA breach count
        sla_breaches = sum(1 for t in c_tickets if t.get("sla_breached"))

        # Health score (0-100): lower tickets, fewer breaches, more devices = healthier
        ticket_ratio = len(c_period) / max(len(c_devices), 1)
        breach_ratio = sla_breaches / max(len(c_tickets), 1)
        health = max(0, min(100, int(100 - ticket_ratio * 20 - breach_ratio * 30)))

        # Topic breakdown for this company
        topic_breakdown = defaultdict(int)
        for t in c_period:
            topic_breakdown[t.get("help_topic_name", "Other")] += 1

        company_scores.append({
            "id": cid,
            "name": comp["name"],
            "amc_status": comp.get("amc_status", "none"),
            "device_count": len(c_devices),
            "total_tickets": len(c_tickets),
            "period_tickets": len(c_period),
            "open_tickets": len(c_open),
            "sla_breaches": sla_breaches,
            "health_score": health,
            "revenue": round(c_approved, 2),
            "pending_amount": round(c_pending, 2),
            "ticket_to_device_ratio": round(ticket_ratio, 2),
            "top_topics": sorted(topic_breakdown.items(), key=lambda x: -x[1])[:5],
        })

    result = {
        "summary": {
            "total_companies": len(companies),
            "avg_health_score": round(sum(c["health_score"] for c in company_scores) / max(len(company_scores), 1), 1),
            "at_risk_companies": len([c for c in company_scores if c["health_score"] < 50]),
            "total_devices_managed": sum(c["device_count"] for c in company_scores),
        },
        "companies": sorted(company_scores, key=lambda x: x["health_score"]),
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 5. ASSET INTELLIGENCE
# ══════════════════════════════════════════════════════════

@router.get("/assets")
async def asset_intelligence(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    cache_key = f"assets:{org_id}"
    cached = _cached(cache_key)
    if cached:
        return cached

    devices = await _db.devices.find(
        {"organization_id": org_id}, {"_id": 0}
    ).to_list(10000)
    service_hist = await _db.service_history.find(
        {"organization_id": org_id} if "organization_id" in (await _db.service_history.find_one({}) or {}) else {},
        {"_id": 0}
    ).to_list(5000)
    all_tickets = await _db.tickets_v2.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0, "device_id": 1, "device_name": 1}
    ).to_list(5000)

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_dt = datetime.now(timezone.utc)

    # Warranty expiry timeline
    expiry_30 = 0
    expiry_60 = 0
    expiry_90 = 0
    expired = 0
    active_warranty = 0
    for d in devices:
        we = d.get("warranty_end_date", "")
        if not we:
            continue
        try:
            we_dt = datetime.strptime(str(we)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_left = (we_dt - now_dt).days
            if days_left < 0:
                expired += 1
            elif days_left <= 30:
                expiry_30 += 1
            elif days_left <= 60:
                expiry_60 += 1
            elif days_left <= 90:
                expiry_90 += 1
            else:
                active_warranty += 1
        except Exception:
            pass

    # Brand/model distribution
    brand_dist = defaultdict(int)
    model_dist = defaultdict(int)
    type_dist = defaultdict(int)
    status_dist = defaultdict(int)
    for d in devices:
        brand_dist[d.get("brand", "Unknown")] += 1
        model_dist[f"{d.get('brand','')}/{d.get('model','')}"] += 1
        type_dist[d.get("device_type", "Unknown")] += 1
        status_dist[d.get("status", "unknown")] += 1

    # Failure rate (tickets per device)
    device_ticket_count = defaultdict(int)
    for t in all_tickets:
        if t.get("device_id"):
            device_ticket_count[t["device_id"]] += 1

    failure_by_brand = defaultdict(lambda: {"tickets": 0, "devices": 0})
    for d in devices:
        brand = d.get("brand", "Unknown")
        failure_by_brand[brand]["devices"] += 1
        failure_by_brand[brand]["tickets"] += device_ticket_count.get(d["id"], 0)

    # Age distribution
    age_buckets = {"<1yr": 0, "1-2yr": 0, "2-3yr": 0, "3-4yr": 0, "4-5yr": 0, "5yr+": 0}
    for d in devices:
        pd_str = d.get("purchase_date", "")
        if not pd_str:
            continue
        try:
            pd_dt = datetime.strptime(str(pd_str)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            age_years = (now_dt - pd_dt).days / 365
            if age_years < 1:
                age_buckets["<1yr"] += 1
            elif age_years < 2:
                age_buckets["1-2yr"] += 1
            elif age_years < 3:
                age_buckets["2-3yr"] += 1
            elif age_years < 4:
                age_buckets["3-4yr"] += 1
            elif age_years < 5:
                age_buckets["4-5yr"] += 1
            else:
                age_buckets["5yr+"] += 1
        except Exception:
            pass

    result = {
        "summary": {
            "total_devices": len(devices),
            "active_warranty": active_warranty,
            "expired_warranty": expired,
            "expiring_30d": expiry_30,
            "expiring_60d": expiry_60,
            "expiring_90d": expiry_90,
            "devices_with_tickets": len(device_ticket_count),
        },
        "warranty_timeline": [
            {"label": "Expired", "count": expired},
            {"label": "0-30 days", "count": expiry_30},
            {"label": "31-60 days", "count": expiry_60},
            {"label": "61-90 days", "count": expiry_90},
            {"label": "Active (90d+)", "count": active_warranty},
        ],
        "brand_distribution": [{"name": k, "count": v} for k, v in sorted(brand_dist.items(), key=lambda x: -x[1])[:15]],
        "type_distribution": [{"name": k, "count": v} for k, v in type_dist.items()],
        "status_distribution": [{"name": k, "count": v} for k, v in status_dist.items()],
        "age_distribution": [{"bucket": k, "count": v} for k, v in age_buckets.items()],
        "failure_by_brand": [
            {"brand": k, "devices": v["devices"], "tickets": v["tickets"],
             "rate": round(v["tickets"] / max(v["devices"], 1) * 100, 1)}
            for k, v in sorted(failure_by_brand.items(), key=lambda x: -x[1]["tickets"])[:10]
        ],
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 6. SLA COMPLIANCE
# ══════════════════════════════════════════════════════════

@router.get("/sla")
async def sla_compliance(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    cache_key = f"sla:{org_id}:{days}"
    cached = _cached(cache_key)
    if cached:
        return cached

    all_tickets = await _db.tickets_v2.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(5000)
    sla_policies = await _db.ticket_sla_policies.find(
        {"organization_id": org_id}, {"_id": 0}
    ).to_list(100)

    start_iso, _ = _parse_dates(days)
    period = [t for t in all_tickets if t.get("created_at", "") >= start_iso]

    total = len(period)
    breached = sum(1 for t in period if t.get("sla_breached"))
    overdue = sum(1 for t in period if t.get("is_overdue"))
    escalated = sum(1 for t in period if t.get("is_escalated"))

    # Breach by priority
    breach_by_priority = defaultdict(lambda: {"total": 0, "breached": 0})
    for t in period:
        p = t.get("priority_name", "medium")
        breach_by_priority[p]["total"] += 1
        if t.get("sla_breached"):
            breach_by_priority[p]["breached"] += 1

    # Breach by team
    breach_by_team = defaultdict(lambda: {"total": 0, "breached": 0})
    for t in period:
        team = t.get("assigned_team_name", "Unassigned")
        breach_by_team[team]["total"] += 1
        if t.get("sla_breached"):
            breach_by_team[team]["breached"] += 1

    # Breach trend by week
    breach_by_week = defaultdict(lambda: {"total": 0, "breached": 0})
    for t in period:
        try:
            dt = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
            week = dt.strftime("%Y-W%W")
            breach_by_week[week]["total"] += 1
            if t.get("sla_breached"):
                breach_by_week[week]["breached"] += 1
        except Exception:
            pass

    result = {
        "summary": {
            "total_tickets": total,
            "sla_compliant": total - breached,
            "sla_breached": breached,
            "compliance_rate": round((total - breached) / max(total, 1) * 100, 1),
            "overdue": overdue,
            "escalated": escalated,
        },
        "breach_by_priority": [
            {"priority": k, "total": v["total"], "breached": v["breached"],
             "rate": round(v["breached"] / max(v["total"], 1) * 100, 1)}
            for k, v in breach_by_priority.items()
        ],
        "breach_by_team": [
            {"team": k, "total": v["total"], "breached": v["breached"],
             "rate": round(v["breached"] / max(v["total"], 1) * 100, 1)}
            for k, v in breach_by_team.items()
        ],
        "breach_trend": [
            {"week": k, "total": v["total"], "breached": v["breached"],
             "rate": round(v["breached"] / max(v["total"], 1) * 100, 1)}
            for k, v in sorted(breach_by_week.items())
        ],
        "sla_policies_count": len(sla_policies),
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 7. WORKFLOW ANALYTICS
# ══════════════════════════════════════════════════════════

@router.get("/workflows")
async def workflow_analytics(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    cache_key = f"workflows:{org_id}"
    cached = _cached(cache_key)
    if cached:
        return cached

    workflows = await _db.ticket_workflows.find(
        {"organization_id": org_id, "is_active": True}, {"_id": 0}
    ).to_list(100)
    all_tickets = await _db.tickets_v2.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "workflow_id": 1, "current_stage_name": 1, "current_stage_id": 1,
         "is_open": 1, "created_at": 1, "closed_at": 1, "timeline": 1, "device_warranty_type": 1}
    ).to_list(5000)

    wf_analytics = []
    for wf in workflows:
        wf_tickets = [t for t in all_tickets if t.get("workflow_id") == wf["id"]]
        stages = wf.get("stages", [])

        # Stage backlog
        stage_backlog = defaultdict(int)
        for t in wf_tickets:
            if t.get("is_open"):
                stage_backlog[t.get("current_stage_name", "?")] += 1

        # Stage cycle times from timeline
        stage_times = defaultdict(list)
        for t in wf_tickets:
            timeline = t.get("timeline", [])
            for i, ev in enumerate(timeline):
                if ev.get("type") == "stage_changed" and i > 0:
                    try:
                        prev_ts = datetime.fromisoformat(timeline[i - 1].get("timestamp", "").replace("Z", "+00:00"))
                        curr_ts = datetime.fromisoformat(ev.get("timestamp", "").replace("Z", "+00:00"))
                        prev_stage = ev.get("description", "").split("→")[0].strip().replace("Stage changed: ", "")
                        hours = (curr_ts - prev_ts).total_seconds() / 3600
                        if hours > 0:
                            stage_times[prev_stage].append(hours)
                    except Exception:
                        pass

        wf_analytics.append({
            "id": wf["id"],
            "name": wf["name"],
            "total_tickets": len(wf_tickets),
            "open_tickets": sum(1 for t in wf_tickets if t.get("is_open")),
            "closed_tickets": sum(1 for t in wf_tickets if not t.get("is_open")),
            "stages_count": len(stages),
            "stage_backlog": [{"stage": s.get("name", "?"), "count": stage_backlog.get(s.get("name"), 0), "order": s.get("order", 0)} for s in sorted(stages, key=lambda x: x.get("order", 0))],
            "stage_cycle_times": [{"stage": k, "avg_hours": round(sum(v) / len(v), 1), "count": len(v)} for k, v in stage_times.items()],
        })

    # Warranty type distribution
    warranty_dist = defaultdict(int)
    for t in all_tickets:
        warranty_dist[t.get("device_warranty_type", "unknown")] += 1

    result = {
        "summary": {
            "total_workflows": len(workflows),
            "total_active_tickets": sum(w["open_tickets"] for w in wf_analytics),
        },
        "workflows": wf_analytics,
        "warranty_type_distribution": [{"type": k, "count": v} for k, v in warranty_dist.items()],
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 8. INVENTORY & PARTS
# ══════════════════════════════════════════════════════════

@router.get("/inventory")
async def inventory_analytics(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    cache_key = f"inventory:{org_id}"
    cached = _cached(cache_key)
    if cached:
        return cached

    inventory = await _db.inventory.find({"organization_id": org_id}, {"_id": 0}).to_list(1000)
    products = await _db.item_products.find({"organization_id": org_id, "is_active": True}, {"_id": 0}).to_list(1000)
    transactions = await _db.inventory_transactions.find({"organization_id": org_id}, {"_id": 0}).to_list(5000)
    ledger = await _db.stock_ledger.find({"organization_id": org_id}, {"_id": 0}).to_list(5000)
    part_reqs = await _db.ticket_part_requests.find({"organization_id": org_id}, {"_id": 0}).to_list(1000)

    product_map = {p["id"]: p.get("name", "?") for p in products}

    # Stock levels vs reorder
    stock_alerts = []
    for inv in inventory:
        pid = inv.get("product_id")
        stock = inv.get("quantity_in_stock", 0)
        reorder = inv.get("reorder_level", 0)
        if stock <= reorder:
            stock_alerts.append({
                "product": product_map.get(pid, pid),
                "stock": stock,
                "reorder_level": reorder,
                "deficit": reorder - stock,
            })

    # Top consumed items
    consumption = defaultdict(int)
    for tx in transactions:
        if tx.get("type") in ("issue", "consume", "out"):
            consumption[tx.get("product_name", "?")] += tx.get("quantity", 0)

    # Transaction volume by month
    tx_by_month = defaultdict(lambda: {"in": 0, "out": 0})
    for tx in transactions:
        month = tx.get("created_at", "")[:7]
        if tx.get("type") in ("receive", "purchase", "in"):
            tx_by_month[month]["in"] += tx.get("quantity", 0)
        else:
            tx_by_month[month]["out"] += tx.get("quantity", 0)

    # Parts request status
    pr_status = defaultdict(int)
    for pr in part_reqs:
        pr_status[pr.get("status", "pending")] += 1

    result = {
        "summary": {
            "total_products": len(products),
            "total_stock_items": len(inventory),
            "low_stock_alerts": len(stock_alerts),
            "total_transactions": len(transactions),
            "pending_part_requests": pr_status.get("pending", 0) + pr_status.get("requested", 0),
        },
        "stock_alerts": sorted(stock_alerts, key=lambda x: -x["deficit"])[:20],
        "top_consumed": [{"item": k, "quantity": v} for k, v in sorted(consumption.items(), key=lambda x: -x[1])[:15]],
        "transaction_trend": [{"month": k, **v} for k, v in sorted(tx_by_month.items())],
        "part_request_status": [{"status": k, "count": v} for k, v in pr_status.items()],
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 9. CONTRACT & AMC
# ══════════════════════════════════════════════════════════

@router.get("/contracts")
async def contract_analytics(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    cache_key = f"contracts:{org_id}"
    cached = _cached(cache_key)
    if cached:
        return cached

    contracts = await _db.amc_contracts.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(500)
    assignments = await _db.amc_device_assignments.find(
        {"organization_id": org_id}, {"_id": 0}
    ).to_list(5000)
    devices = await _db.devices.find(
        {"organization_id": org_id}, {"_id": 0, "id": 1, "company_id": 1}
    ).to_list(10000)
    companies = await _db.companies.find(
        {"organization_id": org_id}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(500)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    now_dt = datetime.now(timezone.utc)

    company_map = {c["id"]: c["name"] for c in companies}

    active = [c for c in contracts if c.get("end_date", "") >= now_str]
    expired = [c for c in contracts if c.get("end_date", "") < now_str]

    # Type distribution
    type_dist = defaultdict(int)
    for c in contracts:
        type_dist[c.get("amc_type", "unknown")] += 1

    # Expiry pipeline
    expiry_30 = 0
    expiry_60 = 0
    expiry_90 = 0
    for c in active:
        try:
            end = datetime.strptime(c["end_date"][:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_left = (end - now_dt).days
            if days_left <= 30:
                expiry_30 += 1
            elif days_left <= 60:
                expiry_60 += 1
            elif days_left <= 90:
                expiry_90 += 1
        except Exception:
            pass

    # Coverage analysis
    covered_devices = set()
    for a in assignments:
        if a.get("status") == "active":
            covered_devices.add(a.get("device_id"))

    total_devices = len(devices)

    # Contracts by company
    contracts_by_company = defaultdict(int)
    for c in contracts:
        cid = c.get("company_id")
        contracts_by_company[company_map.get(cid, cid)] += 1

    result = {
        "summary": {
            "total_contracts": len(contracts),
            "active_contracts": len(active),
            "expired_contracts": len(expired),
            "expiring_30d": expiry_30,
            "expiring_60d": expiry_60,
            "expiring_90d": expiry_90,
            "devices_covered": len(covered_devices),
            "total_devices": total_devices,
            "coverage_rate": round(len(covered_devices) / max(total_devices, 1) * 100, 1),
        },
        "type_distribution": [{"type": k, "count": v} for k, v in type_dist.items()],
        "expiry_pipeline": [
            {"label": "Expiring 0-30d", "count": expiry_30},
            {"label": "Expiring 31-60d", "count": expiry_60},
            {"label": "Expiring 61-90d", "count": expiry_90},
            {"label": "Active (90d+)", "count": len(active) - expiry_30 - expiry_60 - expiry_90},
        ],
        "by_company": [{"company": k, "count": v} for k, v in sorted(contracts_by_company.items(), key=lambda x: -x[1])[:15]],
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# 10. OPERATIONAL INTELLIGENCE
# ══════════════════════════════════════════════════════════

@router.get("/operational")
async def operational_intelligence(
    days: int = Query(90, ge=7, le=365),
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    cache_key = f"operational:{org_id}:{days}"
    cached = _cached(cache_key)
    if cached:
        return cached

    start_iso, _ = _parse_dates(days)
    all_tickets = await _db.tickets_v2.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).to_list(5000)
    devices = await _db.devices.find(
        {"organization_id": org_id}, {"_id": 0, "id": 1, "warranty_end_date": 1, "company_id": 1, "brand": 1}
    ).to_list(10000)
    contracts = await _db.amc_contracts.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "company_id": 1, "end_date": 1, "name": 1}
    ).to_list(500)
    companies = await _db.companies.find(
        {"organization_id": org_id}, {"_id": 0, "id": 1, "name": 1}
    ).to_list(500)

    company_map = {c["id"]: c["name"] for c in companies}
    now_dt = datetime.now(timezone.utc)

    # Weekly ticket trend for prediction
    weekly_volumes = defaultdict(int)
    for t in all_tickets:
        try:
            dt = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
            week = dt.strftime("%Y-W%W")
            weekly_volumes[week] += 1
        except Exception:
            pass

    sorted_weeks = sorted(weekly_volumes.items())
    volumes = [v for _, v in sorted_weeks]

    # Simple linear trend prediction
    predicted_next = 0
    trend_direction = "stable"
    if len(volumes) >= 4:
        recent = volumes[-4:]
        avg_recent = sum(recent) / len(recent)
        older = volumes[-8:-4] if len(volumes) >= 8 else volumes[:len(volumes) // 2]
        avg_older = sum(older) / max(len(older), 1)
        predicted_next = int(avg_recent + (avg_recent - avg_older) * 0.5)
        if avg_recent > avg_older * 1.1:
            trend_direction = "increasing"
        elif avg_recent < avg_older * 0.9:
            trend_direction = "decreasing"

    # Anomaly detection (company with unusual ticket spike)
    company_weekly = defaultdict(lambda: defaultdict(int))
    for t in all_tickets:
        if t.get("company_id"):
            try:
                dt = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00"))
                week = dt.strftime("%Y-W%W")
                company_weekly[t["company_id"]][week] += 1
            except Exception:
                pass

    anomalies = []
    for cid, weeks in company_weekly.items():
        if len(weeks) < 3:
            continue
        vals = list(weeks.values())
        avg_val = sum(vals) / len(vals)
        if avg_val == 0:
            continue
        latest_week = sorted(weeks.keys())[-1]
        latest_val = weeks[latest_week]
        if latest_val > avg_val * 2 and latest_val > 3:
            anomalies.append({
                "company": company_map.get(cid, cid),
                "current_week_tickets": latest_val,
                "avg_weekly_tickets": round(avg_val, 1),
                "spike_factor": round(latest_val / avg_val, 1),
            })

    # Recommendations
    recommendations = []
    for d in devices:
        we = d.get("warranty_end_date", "")
        if we:
            try:
                we_dt = datetime.strptime(str(we)[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
                days_left = (we_dt - now_dt).days
                if 0 < days_left <= 30:
                    cname = company_map.get(d.get("company_id"), "Unknown")
                    recommendations.append({
                        "type": "warranty_expiring",
                        "message": f"{d.get('brand', '')} device warranty expiring in {days_left}d for {cname}",
                        "action": "Send AMC renewal offer",
                        "priority": "high" if days_left <= 7 else "medium",
                    })
            except Exception:
                pass

    for c in contracts:
        try:
            end = datetime.strptime(c["end_date"][:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
            days_left = (end - now_dt).days
            if 0 < days_left <= 30:
                cname = company_map.get(c.get("company_id"), "Unknown")
                recommendations.append({
                    "type": "contract_expiring",
                    "message": f"AMC '{c.get('name','')}' expiring in {days_left}d for {cname}",
                    "action": "Initiate renewal conversation",
                    "priority": "high",
                })
        except Exception:
            pass

    # Topic clustering (most common issues)
    topic_counts = defaultdict(int)
    for t in all_tickets:
        if t.get("created_at", "") >= start_iso:
            topic_counts[t.get("help_topic_name", "Other")] += 1

    result = {
        "summary": {
            "trend_direction": trend_direction,
            "predicted_next_week": max(predicted_next, 0),
            "anomalies_detected": len(anomalies),
            "recommendations_count": len(recommendations),
        },
        "weekly_trend": [{"week": k, "count": v} for k, v in sorted_weeks[-12:]],
        "anomalies": anomalies[:10],
        "recommendations": sorted(recommendations, key=lambda x: 0 if x["priority"] == "high" else 1)[:20],
        "top_issues": [{"topic": k, "count": v} for k, v in sorted(topic_counts.items(), key=lambda x: -x[1])[:10]],
    }
    _set_cache(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY (aggregated top-level KPIs)
# ══════════════════════════════════════════════════════════

@router.get("/executive-summary")
async def executive_summary(
    days: int = Query(30, ge=1, le=365),
    admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    cache_key = f"exec:{org_id}:{days}"
    cached = _cached(cache_key)
    if cached:
        return cached

    start_iso, _ = _parse_dates(days)
    prev_start = (datetime.now(timezone.utc) - timedelta(days=days * 2)).isoformat()

    base = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    all_tickets = await _db.tickets_v2.find(base, {"_id": 0}).to_list(5000)
    devices = await _db.devices.find({"organization_id": org_id}, {"_id": 0, "id": 1}).to_list(10000)
    companies = await _db.companies.find({"organization_id": org_id}, {"_id": 0, "id": 1}).to_list(500)
    engineers = await _db.engineers.find({"organization_id": org_id, "is_active": True}, {"_id": 0, "id": 1}).to_list(200)
    quotations = await _db.quotations.find({"organization_id": org_id}, {"_id": 0}).to_list(5000)
    contracts = await _db.amc_contracts.find({**base}, {"_id": 0}).to_list(500)

    current = [t for t in all_tickets if t.get("created_at", "") >= start_iso]
    previous = [t for t in all_tickets if prev_start <= t.get("created_at", "") < start_iso]

    # Calculate change percentages
    def pct_change(curr, prev):
        if prev == 0:
            return 100 if curr > 0 else 0
        return round((curr - prev) / prev * 100, 1)

    current_closed = sum(1 for t in current if not t.get("is_open"))
    prev_closed = sum(1 for t in previous if not t.get("is_open"))

    current_revenue = sum(q.get("total_amount", 0) for q in quotations if q.get("status") == "approved" and q.get("created_at", "") >= start_iso)
    prev_revenue = sum(q.get("total_amount", 0) for q in quotations if q.get("status") == "approved" and prev_start <= q.get("created_at", "") < start_iso)

    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    result = {
        "kpis": [
            {"label": "Open Tickets", "value": sum(1 for t in all_tickets if t.get("is_open")), "change": pct_change(len(current), len(previous)), "type": "warning"},
            {"label": "Resolved This Period", "value": current_closed, "change": pct_change(current_closed, prev_closed), "type": "success"},
            {"label": "New Tickets", "value": len(current), "change": pct_change(len(current), len(previous)), "type": "info"},
            {"label": "Revenue", "value": round(current_revenue, 2), "change": pct_change(current_revenue, prev_revenue), "type": "success", "prefix": "INR"},
            {"label": "Active Devices", "value": len(devices), "type": "neutral"},
            {"label": "Companies", "value": len(companies), "type": "neutral"},
            {"label": "Active Engineers", "value": len(engineers), "type": "neutral"},
            {"label": "Active Contracts", "value": len([c for c in contracts if c.get("end_date", "") >= now_str]), "type": "neutral"},
        ],
        "period_days": days,
    }
    _set_cache(cache_key, result)
    return result
