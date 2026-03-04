"""
Project Management Module
=========================
Template-driven project management with auto-generated subtasks.
Supports: Projects → Tasks (from templates) → Subtasks (auto-created)
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional, List
import uuid
import logging

router = APIRouter(prefix="/projects", tags=["Project Management"])
_db = None
logger = logging.getLogger("projects")


def init_db(database):
    global _db
    _db = database


from services.auth import get_current_admin


# ══════════════════════════════════════════════════════════
# MODELS
# ══════════════════════════════════════════════════════════

class SubtaskTemplateItem(BaseModel):
    name: str
    description: str = ""
    order: int
    estimated_hours: float = 0
    is_mandatory: bool = True

class TaskTemplateCreate(BaseModel):
    name: str
    description: str = ""
    category: str = ""
    subtasks: List[SubtaskTemplateItem] = []

class TaskTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    subtasks: Optional[List[SubtaskTemplateItem]] = None

class ProjectCreate(BaseModel):
    name: str
    company_id: str
    description: str = ""
    start_date: str = ""
    end_date: str = ""
    priority: str = "medium"

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    priority: Optional[str] = None

class TaskCreate(BaseModel):
    template_id: str
    name: str = ""
    assigned_to: str = ""
    start_date: str = ""
    due_date: str = ""
    remarks: str = ""

class SubtaskUpdate(BaseModel):
    status: Optional[str] = None
    remarks: Optional[str] = None
    assigned_to: Optional[str] = None
    actual_hours: Optional[float] = None


# ══════════════════════════════════════════════════════════
# TASK TEMPLATES (Master Configuration)
# ══════════════════════════════════════════════════════════

@router.get("/templates")
async def list_templates(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    templates = await _db.project_templates.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("name", 1).to_list(200)
    return templates


@router.post("/templates")
async def create_template(data: TaskTemplateCreate, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    template = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "name": data.name,
        "description": data.description,
        "category": data.category,
        "subtasks": [s.dict() for s in data.subtasks],
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin.get("email", ""),
    }
    await _db.project_templates.insert_one(template)
    template.pop("_id", None)
    return template


@router.put("/templates/{template_id}")
async def update_template(template_id: str, data: TaskTemplateUpdate, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    update = {}
    if data.name is not None: update["name"] = data.name
    if data.description is not None: update["description"] = data.description
    if data.category is not None: update["category"] = data.category
    if data.subtasks is not None: update["subtasks"] = [s.dict() for s in data.subtasks]
    if update:
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.project_templates.update_one(
            {"id": template_id, "organization_id": org_id}, {"$set": update}
        )
    return {"success": True}


@router.delete("/templates/{template_id}")
async def delete_template(template_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    await _db.project_templates.update_one(
        {"id": template_id, "organization_id": org_id},
        {"$set": {"is_deleted": True}}
    )
    return {"success": True}


# ══════════════════════════════════════════════════════════
# SEED DEFAULT TEMPLATES
# ══════════════════════════════════════════════════════════

@router.post("/templates/seed-defaults")
async def seed_default_templates(admin: dict = Depends(get_current_admin)):
    """Seed default MSP task templates if none exist"""
    org_id = admin.get("organization_id")
    count = await _db.project_templates.count_documents({"organization_id": org_id, "is_deleted": {"$ne": True}})
    if count > 0:
        return {"message": f"{count} templates already exist", "seeded": 0}

    defaults = [
        {
            "name": "CCTV Installation",
            "category": "Security",
            "description": "End-to-end CCTV surveillance system deployment",
            "subtasks": [
                {"name": "Site Survey & Assessment", "description": "Visit site, assess camera positions, coverage areas, cable routes", "order": 1, "estimated_hours": 4, "is_mandatory": True},
                {"name": "Drawing & Design", "description": "Create camera layout drawing, cable routing diagram, equipment list", "order": 2, "estimated_hours": 3, "is_mandatory": True},
                {"name": "Quotation Preparation", "description": "Prepare detailed quotation with equipment, labour, and material costs", "order": 3, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Quotation Approval", "description": "Client reviews and approves quotation, PO received", "order": 4, "estimated_hours": 0, "is_mandatory": True},
                {"name": "Material Procurement", "description": "Order cameras, NVR/DVR, cables, connectors, mounts, switches", "order": 5, "estimated_hours": 0, "is_mandatory": True},
                {"name": "Cabling & Wiring", "description": "Run ethernet/coax cables, install conduits, terminate connections", "order": 6, "estimated_hours": 8, "is_mandatory": True},
                {"name": "Equipment Installation", "description": "Mount cameras, install NVR/DVR, switches, configure network", "order": 7, "estimated_hours": 6, "is_mandatory": True},
                {"name": "Configuration & Setup", "description": "Configure recording schedules, motion detection, remote access, alerts", "order": 8, "estimated_hours": 4, "is_mandatory": True},
                {"name": "Testing & Commissioning", "description": "Test all cameras, playback, remote viewing, night vision, alerts", "order": 9, "estimated_hours": 3, "is_mandatory": True},
                {"name": "Client Handover & Training", "description": "Demo to client, handover credentials, user training, sign-off", "order": 10, "estimated_hours": 2, "is_mandatory": True},
            ]
        },
        {
            "name": "Server Deployment",
            "category": "Infrastructure",
            "description": "Physical or virtual server setup and migration",
            "subtasks": [
                {"name": "Requirements Assessment", "description": "Gather workload requirements, capacity planning, licensing needs", "order": 1, "estimated_hours": 3, "is_mandatory": True},
                {"name": "Architecture Design", "description": "Design server architecture, network topology, storage layout, HA/DR plan", "order": 2, "estimated_hours": 4, "is_mandatory": True},
                {"name": "Quotation & Approval", "description": "Quote hardware/software/services, get client approval", "order": 3, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Hardware Procurement", "description": "Order server hardware, rack, UPS, storage, licenses", "order": 4, "estimated_hours": 0, "is_mandatory": True},
                {"name": "Rack & Physical Setup", "description": "Install server in rack, cable management, power, network connectivity", "order": 5, "estimated_hours": 4, "is_mandatory": True},
                {"name": "OS & Base Configuration", "description": "Install OS, drivers, firmware updates, base hardening", "order": 6, "estimated_hours": 3, "is_mandatory": True},
                {"name": "Application & Service Setup", "description": "Install and configure applications, services, AD, DNS, DHCP", "order": 7, "estimated_hours": 6, "is_mandatory": True},
                {"name": "Data Migration", "description": "Migrate data from old server, verify integrity, test access", "order": 8, "estimated_hours": 8, "is_mandatory": True},
                {"name": "Backup Configuration", "description": "Configure backup jobs, test restore, set retention policy", "order": 9, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Testing & Go-Live", "description": "Full system testing, user acceptance, cutover to production", "order": 10, "estimated_hours": 4, "is_mandatory": True},
                {"name": "Documentation & Handover", "description": "Create runbook, topology diagrams, credentials doc, admin training", "order": 11, "estimated_hours": 3, "is_mandatory": True},
            ]
        },
        {
            "name": "Computer/Workstation Deployment",
            "category": "Endpoints",
            "description": "End-user computer setup and deployment",
            "subtasks": [
                {"name": "Inventory & Audit", "description": "Audit existing machines, identify replacements, gather user requirements", "order": 1, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Procurement", "description": "Order hardware, peripherals, software licenses", "order": 2, "estimated_hours": 0, "is_mandatory": True},
                {"name": "OS Imaging & Setup", "description": "Image machines with standard OS build, install drivers", "order": 3, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Software Installation", "description": "Install business applications, office suite, security software", "order": 4, "estimated_hours": 1.5, "is_mandatory": True},
                {"name": "Domain Join & Policy", "description": "Join to domain, apply group policies, configure user profiles", "order": 5, "estimated_hours": 1, "is_mandatory": True},
                {"name": "Data Migration", "description": "Transfer user files, email profiles, bookmarks from old machine", "order": 6, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Peripheral Setup", "description": "Connect printers, scanners, dual monitors, docking stations", "order": 7, "estimated_hours": 0.5, "is_mandatory": True},
                {"name": "User Handover", "description": "Deliver to user, verify everything works, quick training", "order": 8, "estimated_hours": 0.5, "is_mandatory": True},
            ]
        },
        {
            "name": "Network Setup",
            "category": "Networking",
            "description": "LAN/WAN/WiFi network infrastructure deployment",
            "subtasks": [
                {"name": "Site Survey", "description": "Assess premises, measure distances, identify switch/AP locations", "order": 1, "estimated_hours": 3, "is_mandatory": True},
                {"name": "Network Design", "description": "Design network topology, VLAN plan, IP scheme, WiFi coverage map", "order": 2, "estimated_hours": 4, "is_mandatory": True},
                {"name": "Quotation & Approval", "description": "Quote switches, APs, cables, labour; get client approval", "order": 3, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Material Procurement", "description": "Order switches, access points, cables, patch panels, racks", "order": 4, "estimated_hours": 0, "is_mandatory": True},
                {"name": "Structured Cabling", "description": "Run cables, terminate patch panels, label all points", "order": 5, "estimated_hours": 12, "is_mandatory": True},
                {"name": "Equipment Installation", "description": "Mount switches, APs, configure VLANs, routing, DHCP", "order": 6, "estimated_hours": 6, "is_mandatory": True},
                {"name": "WiFi Configuration", "description": "Configure SSIDs, security, roaming, guest network", "order": 7, "estimated_hours": 3, "is_mandatory": False},
                {"name": "Firewall & Security", "description": "Configure firewall rules, IDS/IPS, VPN, content filtering", "order": 8, "estimated_hours": 4, "is_mandatory": True},
                {"name": "Testing & Certification", "description": "Cable testing, speed tests, coverage verification, stress testing", "order": 9, "estimated_hours": 3, "is_mandatory": True},
                {"name": "Documentation & Handover", "description": "Network diagram, IP allocation sheet, admin credentials, training", "order": 10, "estimated_hours": 2, "is_mandatory": True},
            ]
        },
        {
            "name": "Firewall Deployment",
            "category": "Security",
            "description": "Network firewall/UTM appliance installation and configuration",
            "subtasks": [
                {"name": "Requirements Gathering", "description": "Assess network zones, access policies, VPN requirements", "order": 1, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Quotation & Approval", "description": "Quote firewall appliance, licensing, professional services", "order": 2, "estimated_hours": 1, "is_mandatory": True},
                {"name": "Pre-Configuration", "description": "Stage firewall, configure interfaces, zones, base policies", "order": 3, "estimated_hours": 3, "is_mandatory": True},
                {"name": "Installation & Cutover", "description": "Physical install, connect WAN/LAN, cutover from old firewall", "order": 4, "estimated_hours": 4, "is_mandatory": True},
                {"name": "Policy Configuration", "description": "Set up access rules, NAT, content filtering, threat prevention", "order": 5, "estimated_hours": 4, "is_mandatory": True},
                {"name": "VPN Setup", "description": "Configure site-to-site and remote access VPNs", "order": 6, "estimated_hours": 3, "is_mandatory": False},
                {"name": "Testing & Validation", "description": "Test all policies, VPN tunnels, failover, logging", "order": 7, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Documentation & Handover", "description": "Document rules, topology, credentials, admin training", "order": 8, "estimated_hours": 2, "is_mandatory": True},
            ]
        },
    ]

    seeded = 0
    for tmpl in defaults:
        doc = {
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "name": tmpl["name"],
            "description": tmpl["description"],
            "category": tmpl["category"],
            "subtasks": tmpl["subtasks"],
            "is_deleted": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": "system",
        }
        await _db.project_templates.insert_one(doc)
        seeded += 1

    return {"message": f"Seeded {seeded} default templates", "seeded": seeded}


# ══════════════════════════════════════════════════════════
# STAFF LIST (for task assignment dropdowns - must be before /{project_id})
# ══════════════════════════════════════════════════════════

@router.get("/staff-list")
async def staff_list(admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    staff = await _db.staff.find(
        {"organization_id": org_id, "isActive": True, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "email": 1}
    ).to_list(200)
    members = await _db.org_members.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "email": 1}
    ).to_list(50)
    return {"staff": staff, "members": members}


# ══════════════════════════════════════════════════════════
# PROJECTS
# ══════════════════════════════════════════════════════════

@router.get("")
async def list_projects(
    admin: dict = Depends(get_current_admin),
    status: Optional[str] = Query(None),
    company_id: Optional[str] = Query(None),
):
    org_id = admin.get("organization_id")
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    if status: query["status"] = status
    if company_id: query["company_id"] = company_id

    projects = await _db.projects.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)

    # Enrich with company names and task progress
    company_ids = list({p.get("company_id") for p in projects if p.get("company_id")})
    company_map = {}
    if company_ids:
        companies = await _db.companies.find(
            {"id": {"$in": company_ids}}, {"_id": 0, "id": 1, "name": 1}
        ).to_list(500)
        company_map = {c["id"]: c["name"] for c in companies}

    for p in projects:
        p["company_name"] = company_map.get(p.get("company_id"), "")
        tasks = await _db.project_tasks.find(
            {"project_id": p["id"], "is_deleted": {"$ne": True}}, {"_id": 0, "id": 1, "status": 1}
        ).to_list(500)
        subtasks = await _db.project_subtasks.find(
            {"project_id": p["id"], "is_deleted": {"$ne": True}}, {"_id": 0, "status": 1}
        ).to_list(5000)
        p["task_count"] = len(tasks)
        p["subtask_count"] = len(subtasks)
        p["completed_subtasks"] = sum(1 for s in subtasks if s.get("status") == "completed")
        p["progress"] = round(p["completed_subtasks"] / max(len(subtasks), 1) * 100)

    return projects


@router.post("")
async def create_project(data: ProjectCreate, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    project = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "name": data.name,
        "company_id": data.company_id,
        "description": data.description,
        "status": "planning",
        "priority": data.priority,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "is_deleted": False,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin.get("email", ""),
    }
    await _db.projects.insert_one(project)
    project.pop("_id", None)
    return project


@router.get("/{project_id}")
async def get_project(project_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    project = await _db.projects.find_one(
        {"id": project_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Enrich
    company = await _db.companies.find_one(
        {"id": project.get("company_id")}, {"_id": 0, "name": 1}
    )
    project["company_name"] = (company or {}).get("name", "")

    # Load tasks with subtasks
    tasks = await _db.project_tasks.find(
        {"project_id": project_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).sort("created_at", 1).to_list(500)

    staff_ids = list({t.get("assigned_to") for t in tasks if t.get("assigned_to")})

    subtasks_all = await _db.project_subtasks.find(
        {"project_id": project_id, "is_deleted": {"$ne": True}}, {"_id": 0}
    ).sort("order", 1).to_list(5000)

    # Collect staff IDs from subtasks too
    staff_ids += [s.get("assigned_to") for s in subtasks_all if s.get("assigned_to")]
    staff_ids += [s.get("completed_by") for s in subtasks_all if s.get("completed_by")]
    staff_ids = list(set(filter(None, staff_ids)))

    staff_map = {}
    if staff_ids:
        staff_docs = await _db.staff.find(
            {"id": {"$in": staff_ids}}, {"_id": 0, "id": 1, "name": 1}
        ).to_list(200)
        staff_map = {s["id"]: s["name"] for s in staff_docs}

    # Also check org_members for admin users
    if staff_ids:
        members = await _db.org_members.find(
            {"id": {"$in": staff_ids}}, {"_id": 0, "id": 1, "name": 1, "email": 1}
        ).to_list(200)
        for m in members:
            if m["id"] not in staff_map:
                staff_map[m["id"]] = m.get("name", m.get("email", ""))

    subtask_map = {}
    for s in subtasks_all:
        s["assigned_to_name"] = staff_map.get(s.get("assigned_to"), "")
        s["completed_by_name"] = staff_map.get(s.get("completed_by"), "")
        subtask_map.setdefault(s["task_id"], []).append(s)

    for t in tasks:
        t["assigned_to_name"] = staff_map.get(t.get("assigned_to"), "")
        t["subtasks"] = subtask_map.get(t["id"], [])
        total = len(t["subtasks"])
        done = sum(1 for s in t["subtasks"] if s.get("status") == "completed")
        t["progress"] = round(done / max(total, 1) * 100)
        t["subtask_count"] = total
        t["completed_subtasks"] = done

    project["tasks"] = tasks
    total_st = len(subtasks_all)
    done_st = sum(1 for s in subtasks_all if s.get("status") == "completed")
    project["progress"] = round(done_st / max(total_st, 1) * 100)
    project["subtask_count"] = total_st
    project["completed_subtasks"] = done_st

    return project


@router.put("/{project_id}")
async def update_project(project_id: str, data: ProjectUpdate, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    update = {}
    for k, v in data.dict(exclude_none=True).items():
        update[k] = v
    if update:
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.projects.update_one(
            {"id": project_id, "organization_id": org_id}, {"$set": update}
        )
    return {"success": True}


@router.delete("/{project_id}")
async def delete_project(project_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    await _db.projects.update_one(
        {"id": project_id, "organization_id": org_id},
        {"$set": {"is_deleted": True}}
    )
    return {"success": True}


# ══════════════════════════════════════════════════════════
# TASKS (Main tasks within a project — from templates)
# ══════════════════════════════════════════════════════════

@router.post("/{project_id}/tasks")
async def add_task_to_project(project_id: str, data: TaskCreate, admin: dict = Depends(get_current_admin)):
    """Add a task from a template → auto-generates all subtasks"""
    org_id = admin.get("organization_id")

    project = await _db.projects.find_one(
        {"id": project_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1}
    )
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    template = await _db.project_templates.find_one(
        {"id": data.template_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    task_id = str(uuid.uuid4())
    task_name = data.name or template["name"]
    now = datetime.now(timezone.utc).isoformat()

    task = {
        "id": task_id,
        "project_id": project_id,
        "organization_id": org_id,
        "template_id": data.template_id,
        "template_name": template["name"],
        "name": task_name,
        "status": "pending",
        "assigned_to": data.assigned_to,
        "start_date": data.start_date,
        "due_date": data.due_date,
        "remarks": data.remarks,
        "is_deleted": False,
        "created_at": now,
        "created_by": admin.get("email", ""),
    }
    await _db.project_tasks.insert_one(task)

    # Auto-create subtasks from template
    subtasks_created = []
    for st in sorted(template.get("subtasks", []), key=lambda x: x.get("order", 0)):
        subtask = {
            "id": str(uuid.uuid4()),
            "task_id": task_id,
            "project_id": project_id,
            "organization_id": org_id,
            "name": st["name"],
            "description": st.get("description", ""),
            "order": st.get("order", 0),
            "estimated_hours": st.get("estimated_hours", 0),
            "is_mandatory": st.get("is_mandatory", True),
            "status": "pending",
            "assigned_to": "",
            "actual_hours": 0,
            "remarks": "",
            "started_at": None,
            "completed_at": None,
            "completed_by": None,
            "is_deleted": False,
            "created_at": now,
        }
        await _db.project_subtasks.insert_one(subtask)
        subtask.pop("_id", None)
        subtasks_created.append(subtask)

    task.pop("_id", None)
    task["subtasks"] = subtasks_created

    # Auto-activate project if in planning
    await _db.projects.update_one(
        {"id": project_id, "status": "planning"}, {"$set": {"status": "active"}}
    )

    return task


@router.put("/{project_id}/tasks/{task_id}")
async def update_task(project_id: str, task_id: str, data: dict, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    allowed = {"name", "status", "assigned_to", "start_date", "due_date", "remarks"}
    update = {k: v for k, v in data.items() if k in allowed}
    if "status" in update and update["status"] == "completed":
        update["completed_at"] = datetime.now(timezone.utc).isoformat()
        update["completed_by"] = admin.get("email", "")
    if update:
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.project_tasks.update_one(
            {"id": task_id, "project_id": project_id, "organization_id": org_id},
            {"$set": update}
        )
    return {"success": True}


@router.delete("/{project_id}/tasks/{task_id}")
async def delete_task(project_id: str, task_id: str, admin: dict = Depends(get_current_admin)):
    org_id = admin.get("organization_id")
    await _db.project_tasks.update_one(
        {"id": task_id, "project_id": project_id, "organization_id": org_id},
        {"$set": {"is_deleted": True}}
    )
    await _db.project_subtasks.update_many(
        {"task_id": task_id, "organization_id": org_id},
        {"$set": {"is_deleted": True}}
    )
    return {"success": True}


# ══════════════════════════════════════════════════════════
# SUBTASKS (Auto-generated, individually completable)
# ══════════════════════════════════════════════════════════

@router.put("/{project_id}/tasks/{task_id}/subtasks/{subtask_id}")
async def update_subtask(
    project_id: str, task_id: str, subtask_id: str,
    data: SubtaskUpdate, admin: dict = Depends(get_current_admin)
):
    org_id = admin.get("organization_id")
    update = {}
    if data.status is not None:
        update["status"] = data.status
        if data.status == "in-progress" and not update.get("started_at"):
            update["started_at"] = datetime.now(timezone.utc).isoformat()
        if data.status == "completed":
            update["completed_at"] = datetime.now(timezone.utc).isoformat()
            update["completed_by"] = admin.get("org_member_id", admin.get("email", ""))
    if data.remarks is not None:
        update["remarks"] = data.remarks
    if data.assigned_to is not None:
        update["assigned_to"] = data.assigned_to
    if data.actual_hours is not None:
        update["actual_hours"] = data.actual_hours

    if update:
        update["updated_at"] = datetime.now(timezone.utc).isoformat()
        await _db.project_subtasks.update_one(
            {"id": subtask_id, "task_id": task_id, "organization_id": org_id},
            {"$set": update}
        )

    # Check if all subtasks complete → auto-complete the parent task
    all_subtasks = await _db.project_subtasks.find(
        {"task_id": task_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "status": 1, "is_mandatory": 1}
    ).to_list(100)
    mandatory = [s for s in all_subtasks if s.get("is_mandatory", True)]
    if mandatory and all(s["status"] == "completed" for s in mandatory):
        await _db.project_tasks.update_one(
            {"id": task_id, "organization_id": org_id},
            {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
        )

    # Check if all tasks complete → auto-complete the project
    all_tasks = await _db.project_tasks.find(
        {"project_id": project_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "status": 1}
    ).to_list(500)
    if all_tasks and all(t["status"] == "completed" for t in all_tasks):
        await _db.projects.update_one(
            {"id": project_id, "organization_id": org_id},
            {"$set": {"status": "completed", "completed_at": datetime.now(timezone.utc).isoformat()}}
        )

    return {"success": True}
