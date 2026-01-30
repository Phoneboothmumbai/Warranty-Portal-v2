"""
Platform Admin Routes - Super Admin API Endpoints
==================================================
Routes for platform-level administration (managing all tenants).
Completely separate from organization/tenant routes.
"""
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from typing import Optional, List

from models.platform import (
    PlatformAdmin, PlatformAdminCreate, PlatformAdminUpdate,
    PlatformLogin, PlatformSettings, PlatformSettingsUpdate,
    PlatformAuditLog
)
from models.organization import Organization, SUBSCRIPTION_PLANS, ORGANIZATION_STATUSES
from services.auth import get_password_hash, verify_password, create_access_token
from config import SECRET_KEY, ALGORITHM
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer()

# Database will be injected
_db = None

def init_db(database):
    global _db
    _db = database


# ==================== PLATFORM AUTH ====================

async def get_current_platform_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Get current platform admin from JWT token.
    Platform admins have a different token type than org admins.
    """
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate platform credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        admin_id: str = payload.get("sub")
        token_type: str = payload.get("type")
        
        if admin_id is None or token_type != "platform_admin":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    admin = await _db.platform_admins.find_one(
        {"id": admin_id, "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    )
    
    if not admin:
        raise credentials_exception
    
    return admin


def require_platform_permission(*permissions):
    """Dependency factory to require specific platform permissions"""
    async def check_permission(admin: dict = Depends(get_current_platform_admin)):
        admin_permissions = admin.get("permissions", [])
        
        # Platform owner has all permissions
        if admin.get("role") == "platform_owner" or "all" in admin_permissions:
            return admin
        
        for perm in permissions:
            if perm not in admin_permissions:
                raise HTTPException(
                    status_code=403,
                    detail=f"Permission '{perm}' required"
                )
        
        return admin
    
    return check_permission


async def log_platform_audit(action: str, entity_type: str, entity_id: str, changes: dict, admin: dict, request: Request = None):
    """Log platform-level audit entry"""
    try:
        audit = PlatformAuditLog(
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=changes,
            performed_by=admin.get("id", "unknown"),
            performed_by_name=admin.get("name", "Unknown"),
            performed_by_email=admin.get("email", "unknown"),
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        await _db.platform_audit_logs.insert_one(audit.model_dump())
    except Exception as e:
        logger.error(f"Platform audit log failed: {e}")


# ==================== PUBLIC ENDPOINTS ====================

@router.post("/login")
async def platform_login(login: PlatformLogin):
    """
    Platform super admin login.
    Returns a token with type='platform_admin'.
    """
    admin = await _db.platform_admins.find_one(
        {"email": login.email.lower(), "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not admin or not verify_password(login.password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Update last login
    await _db.platform_admins.update_one(
        {"id": admin["id"]},
        {"$set": {"last_login": get_ist_isoformat()}}
    )
    
    # Create token with platform_admin type
    access_token = create_access_token(
        data={
            "sub": admin["id"],
            "type": "platform_admin",
            "role": admin.get("role", "platform_admin"),
            "email": admin["email"]
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {
            "id": admin["id"],
            "email": admin["email"],
            "name": admin["name"],
            "role": admin.get("role")
        }
    }


@router.post("/setup")
async def setup_first_platform_admin(data: PlatformAdminCreate):
    """
    Initial setup - create the first platform super admin.
    Only works if no platform admins exist.
    """
    existing = await _db.platform_admins.find_one({}, {"_id": 0})
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Platform admin already exists. Use login."
        )
    
    # Create first platform admin as owner
    admin = PlatformAdmin(
        email=data.email.lower(),
        name=data.name,
        password_hash=get_password_hash(data.password),
        role="platform_owner",  # First admin is always owner
        permissions=["all"]
    )
    
    await _db.platform_admins.insert_one(admin.model_dump())
    
    # Initialize platform settings
    settings = PlatformSettings()
    await _db.platform_settings.update_one(
        {"id": "platform_settings"},
        {"$set": settings.model_dump()},
        upsert=True
    )
    
    # Create token
    access_token = create_access_token(
        data={
            "sub": admin.id,
            "type": "platform_admin",
            "role": admin.role,
            "email": admin.email
        }
    )
    
    return {
        "message": "Platform admin created successfully",
        "access_token": access_token,
        "token_type": "bearer",
        "admin": {
            "id": admin.id,
            "email": admin.email,
            "name": admin.name,
            "role": admin.role
        }
    }


@router.get("/me")
async def get_platform_admin_me(admin: dict = Depends(get_current_platform_admin)):
    """Get current platform admin info"""
    return admin


# ==================== ORGANIZATION MANAGEMENT ====================

@router.get("/organizations")
async def list_organizations(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    q: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, le=100),
    admin: dict = Depends(require_platform_permission("view_organizations"))
):
    """List all organizations (tenants) on the platform"""
    query = {"is_deleted": {"$ne": True}}
    
    if status:
        query["status"] = status
    if plan:
        query["subscription.plan"] = plan
    if q:
        query["$or"] = [
            {"name": {"$regex": q, "$options": "i"}},
            {"slug": {"$regex": q, "$options": "i"}},
            {"owner_email": {"$regex": q, "$options": "i"}}
        ]
    
    skip = (page - 1) * limit
    
    organizations = await _db.organizations.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await _db.organizations.count_documents(query)
    
    # Add usage stats for each org
    for org in organizations:
        org["stats"] = {
            "companies": await _db.companies.count_documents({"organization_id": org["id"], "is_deleted": {"$ne": True}}),
            "devices": await _db.devices.count_documents({"organization_id": org["id"], "is_deleted": {"$ne": True}}),
            "users": await _db.company_users.count_documents({"organization_id": org["id"], "is_deleted": {"$ne": True}})
        }
    
    return {
        "organizations": organizations,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }


@router.post("/organizations")
async def create_organization(
    name: str,
    owner_email: str,
    owner_name: str,
    owner_password: str,
    plan: str = "trial",
    request: Request = None,
    admin: dict = Depends(require_platform_permission("manage_organizations"))
):
    """
    Create a new organization (tenant).
    Platform admin can create with any plan.
    """
    import re
    
    # Generate slug
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:50]
    
    # Check if slug exists
    existing = await _db.organizations.find_one({"slug": slug})
    if existing:
        slug = f"{slug}-{str(__import__('uuid').uuid4())[:6]}"
    
    # Check if owner email exists
    existing_member = await _db.organization_members.find_one({"email": owner_email.lower()})
    if existing_member:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Determine status based on plan
    status = "trial" if plan == "trial" else "active"
    trial_ends = None
    if plan == "trial":
        trial_ends = (datetime.now(timezone.utc) + timedelta(days=14)).isoformat()
    
    # Create organization
    from models.organization import Organization, OrganizationMember
    
    org = Organization(
        name=name,
        slug=slug,
        owner_user_id="",
        owner_email=owner_email.lower(),
        status=status,
        subscription={
            "plan": plan,
            "status": status,
            "trial_ends_at": trial_ends,
            "current_period_start": get_ist_isoformat(),
            "current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        }
    )
    
    # Create owner member
    member = OrganizationMember(
        organization_id=org.id,
        email=owner_email.lower(),
        name=owner_name,
        password_hash=get_password_hash(owner_password),
        role="owner",
        permissions=["all"]
    )
    
    org.owner_user_id = member.id
    
    await _db.organizations.insert_one(org.model_dump())
    await _db.organization_members.insert_one(member.model_dump())
    
    # Audit log
    await log_platform_audit(
        action="create_organization",
        entity_type="organization",
        entity_id=org.id,
        changes={"name": name, "plan": plan, "owner_email": owner_email},
        admin=admin,
        request=request
    )
    
    return {
        "message": "Organization created successfully",
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "status": org.status
        },
        "owner": {
            "email": owner_email,
            "name": owner_name
        }
    }


@router.get("/organizations/{org_id}")
async def get_organization_details(
    org_id: str,
    admin: dict = Depends(require_platform_permission("view_organizations"))
):
    """Get detailed information about an organization"""
    org = await _db.organizations.find_one(
        {"id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Get members
    members = await _db.organization_members.find(
        {"organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    
    # Get usage stats
    stats = {
        "companies": await _db.companies.count_documents({"organization_id": org_id, "is_deleted": {"$ne": True}}),
        "devices": await _db.devices.count_documents({"organization_id": org_id, "is_deleted": {"$ne": True}}),
        "users": await _db.company_users.count_documents({"organization_id": org_id, "is_deleted": {"$ne": True}}),
        "tickets": await _db.tickets.count_documents({"organization_id": org_id}),
        "amc_contracts": await _db.amc_contracts.count_documents({"organization_id": org_id, "is_deleted": {"$ne": True}})
    }
    
    # Get plan limits
    plan = org.get("subscription", {}).get("plan", "trial")
    plan_config = SUBSCRIPTION_PLANS.get(plan, {})
    
    return {
        "organization": org,
        "members": members,
        "stats": stats,
        "plan_config": plan_config
    }


@router.put("/organizations/{org_id}")
async def update_organization(
    org_id: str,
    name: Optional[str] = None,
    status: Optional[str] = None,
    plan: Optional[str] = None,
    request: Request = None,
    admin: dict = Depends(require_platform_permission("manage_organizations"))
):
    """Update an organization's details"""
    org = await _db.organizations.find_one({"id": org_id, "is_deleted": {"$ne": True}})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    update_data = {"updated_at": get_ist_isoformat()}
    changes = {}
    
    if name:
        changes["name"] = {"old": org.get("name"), "new": name}
        update_data["name"] = name
    
    if status and status in ORGANIZATION_STATUSES:
        changes["status"] = {"old": org.get("status"), "new": status}
        update_data["status"] = status
    
    if plan and plan in SUBSCRIPTION_PLANS:
        changes["plan"] = {"old": org.get("subscription", {}).get("plan"), "new": plan}
        update_data["subscription.plan"] = plan
        update_data["subscription.plan_changed_at"] = get_ist_isoformat()
    
    if update_data:
        await _db.organizations.update_one({"id": org_id}, {"$set": update_data})
    
    # Audit log
    if changes:
        await log_platform_audit(
            action="update_organization",
            entity_type="organization",
            entity_id=org_id,
            changes=changes,
            admin=admin,
            request=request
        )
    
    return await _db.organizations.find_one({"id": org_id}, {"_id": 0})


@router.post("/organizations/{org_id}/suspend")
async def suspend_organization(
    org_id: str,
    reason: Optional[str] = None,
    request: Request = None,
    admin: dict = Depends(require_platform_permission("manage_organizations"))
):
    """Suspend an organization"""
    org = await _db.organizations.find_one({"id": org_id, "is_deleted": {"$ne": True}})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    await _db.organizations.update_one(
        {"id": org_id},
        {"$set": {
            "status": "suspended",
            "suspended_at": get_ist_isoformat(),
            "suspend_reason": reason,
            "updated_at": get_ist_isoformat()
        }}
    )
    
    # Audit log
    await log_platform_audit(
        action="suspend_organization",
        entity_type="organization",
        entity_id=org_id,
        changes={"status": {"old": org.get("status"), "new": "suspended"}, "reason": reason},
        admin=admin,
        request=request
    )
    
    return {"message": "Organization suspended", "organization_id": org_id}


@router.post("/organizations/{org_id}/reactivate")
async def reactivate_organization(
    org_id: str,
    request: Request = None,
    admin: dict = Depends(require_platform_permission("manage_organizations"))
):
    """Reactivate a suspended organization"""
    org = await _db.organizations.find_one({"id": org_id, "is_deleted": {"$ne": True}})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    new_status = "active" if org.get("subscription", {}).get("plan") != "trial" else "trial"
    
    await _db.organizations.update_one(
        {"id": org_id},
        {"$set": {
            "status": new_status,
            "suspended_at": None,
            "suspend_reason": None,
            "updated_at": get_ist_isoformat()
        }}
    )
    
    # Audit log
    await log_platform_audit(
        action="reactivate_organization",
        entity_type="organization",
        entity_id=org_id,
        changes={"status": {"old": org.get("status"), "new": new_status}},
        admin=admin,
        request=request
    )
    
    return {"message": "Organization reactivated", "organization_id": org_id}


@router.delete("/organizations/{org_id}")
async def delete_organization(
    org_id: str,
    request: Request = None,
    admin: dict = Depends(require_platform_permission("manage_organizations"))
):
    """Soft delete an organization (marks as churned)"""
    org = await _db.organizations.find_one({"id": org_id, "is_deleted": {"$ne": True}})
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    await _db.organizations.update_one(
        {"id": org_id},
        {"$set": {
            "status": "churned",
            "is_deleted": True,
            "deleted_at": get_ist_isoformat(),
            "updated_at": get_ist_isoformat()
        }}
    )
    
    # Audit log
    await log_platform_audit(
        action="delete_organization",
        entity_type="organization",
        entity_id=org_id,
        changes={"status": "churned", "is_deleted": True},
        admin=admin,
        request=request
    )
    
    return {"message": "Organization deleted", "organization_id": org_id}


# ==================== PLATFORM SETTINGS ====================

@router.get("/settings")
async def get_platform_settings(admin: dict = Depends(require_platform_permission("platform_settings"))):
    """Get platform settings"""
    settings = await _db.platform_settings.find_one({"id": "platform_settings"}, {"_id": 0})
    if not settings:
        settings = PlatformSettings().model_dump()
    return settings


@router.put("/settings")
async def update_platform_settings(
    updates: PlatformSettingsUpdate,
    request: Request = None,
    admin: dict = Depends(require_platform_permission("platform_settings"))
):
    """Update platform settings"""
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    update_data["updated_by"] = admin.get("id")
    
    await _db.platform_settings.update_one(
        {"id": "platform_settings"},
        {"$set": update_data},
        upsert=True
    )
    
    # Audit log
    await log_platform_audit(
        action="update_platform_settings",
        entity_type="platform_settings",
        entity_id="platform_settings",
        changes=update_data,
        admin=admin,
        request=request
    )
    
    return await _db.platform_settings.find_one({"id": "platform_settings"}, {"_id": 0})


# ==================== PLATFORM ADMINS MANAGEMENT ====================

@router.get("/admins")
async def list_platform_admins(admin: dict = Depends(require_platform_permission("platform_settings"))):
    """List all platform admins"""
    admins = await _db.platform_admins.find(
        {"is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    return admins


@router.post("/admins")
async def create_platform_admin(
    data: PlatformAdminCreate,
    request: Request = None,
    admin: dict = Depends(require_platform_permission("platform_settings"))
):
    """Create a new platform admin"""
    # Only platform owner can create other admins
    if admin.get("role") != "platform_owner":
        raise HTTPException(status_code=403, detail="Only platform owner can create admins")
    
    existing = await _db.platform_admins.find_one({"email": data.email.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_admin = PlatformAdmin(
        email=data.email.lower(),
        name=data.name,
        password_hash=get_password_hash(data.password),
        role=data.role,
        created_by=admin.get("id")
    )
    
    await _db.platform_admins.insert_one(new_admin.model_dump())
    
    # Audit log
    await log_platform_audit(
        action="create_platform_admin",
        entity_type="platform_admin",
        entity_id=new_admin.id,
        changes={"email": data.email, "role": data.role},
        admin=admin,
        request=request
    )
    
    return {
        "message": "Platform admin created",
        "admin": {
            "id": new_admin.id,
            "email": new_admin.email,
            "name": new_admin.name,
            "role": new_admin.role
        }
    }


# ==================== DASHBOARD STATS ====================

@router.get("/dashboard/stats")
async def get_platform_dashboard_stats(admin: dict = Depends(get_current_platform_admin)):
    """Get platform-wide dashboard statistics"""
    
    # Organization counts by status
    org_by_status = {}
    for status in ORGANIZATION_STATUSES:
        count = await _db.organizations.count_documents({"status": status, "is_deleted": {"$ne": True}})
        org_by_status[status] = count
    
    # Organization counts by plan
    org_by_plan = {}
    for plan in SUBSCRIPTION_PLANS.keys():
        count = await _db.organizations.count_documents({
            "subscription.plan": plan,
            "is_deleted": {"$ne": True}
        })
        org_by_plan[plan] = count
    
    # Total counts
    total_orgs = await _db.organizations.count_documents({"is_deleted": {"$ne": True}})
    total_companies = await _db.companies.count_documents({"is_deleted": {"$ne": True}})
    total_devices = await _db.devices.count_documents({"is_deleted": {"$ne": True}})
    total_users = await _db.company_users.count_documents({"is_deleted": {"$ne": True}})
    
    # Recent organizations
    recent_orgs = await _db.organizations.find(
        {"is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "slug": 1, "status": 1, "created_at": 1, "subscription.plan": 1}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "totals": {
            "organizations": total_orgs,
            "companies": total_companies,
            "devices": total_devices,
            "users": total_users
        },
        "organizations_by_status": org_by_status,
        "organizations_by_plan": org_by_plan,
        "recent_organizations": recent_orgs
    }


# ==================== AUDIT LOGS ====================

@router.get("/audit-logs")
async def get_platform_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=50, le=200),
    admin: dict = Depends(require_platform_permission("platform_settings"))
):
    """Get platform audit logs"""
    query = {}
    if action:
        query["action"] = action
    if entity_type:
        query["entity_type"] = entity_type
    
    skip = (page - 1) * limit
    
    logs = await _db.platform_audit_logs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    total = await _db.platform_audit_logs.count_documents(query)
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }
