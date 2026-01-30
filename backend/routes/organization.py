"""
Organization Routes - Multi-tenancy API endpoints
=================================================
Endpoints for organization management, signup, billing, and settings.
"""
import re
import uuid
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from models.organization import (
    Organization, OrganizationCreate, OrganizationUpdate,
    OrganizationMember, OrganizationMemberCreate, OrganizationMemberUpdate,
    OrganizationInvitation, OrganizationBrandingUpdate, OrganizationSettingsUpdate,
    SUBSCRIPTION_PLANS, ORGANIZATION_STATUSES
)
from services.auth import get_password_hash, verify_password, create_access_token
from services.tenant import (
    get_org_from_token, get_current_org_member, get_current_organization,
    require_org_role, check_resource_limit
)
from utils.helpers import get_ist_isoformat

router = APIRouter()

# Database will be injected
_db = None

def init_db(database):
    global _db
    _db = database


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from organization name"""
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    return slug[:50]  # Limit length


# ==================== PUBLIC ENDPOINTS ====================

@router.get("/plans")
async def list_subscription_plans():
    """List available subscription plans (public)"""
    plans = []
    for key, plan in SUBSCRIPTION_PLANS.items():
        plans.append({
            "id": key,
            "name": plan["name"],
            "price_monthly": plan["price_monthly"],
            "price_yearly": plan["price_yearly"],
            "limits": plan["limits"],
            "features": plan["features"],
            "trial_days": plan.get("trial_days")
        })
    return plans


@router.post("/signup")
async def signup_organization(data: OrganizationCreate):
    """
    Public endpoint to create a new organization (tenant).
    Creates the organization and the owner admin user.
    """
    # Validate slug format
    slug = generate_slug(data.slug or data.name)
    
    # Check if slug is taken
    existing = await _db.organizations.find_one({"slug": slug}, {"_id": 0})
    if existing:
        # Try to make it unique
        slug = f"{slug}-{str(uuid.uuid4())[:6]}"
    
    # Check if owner email is already used
    existing_member = await _db.organization_members.find_one(
        {"email": data.owner_email.lower()},
        {"_id": 0}
    )
    if existing_member:
        raise HTTPException(
            status_code=400,
            detail="Email already registered. Please login or use a different email."
        )
    
    # Calculate trial end date (14 days from now)
    trial_ends = datetime.now(timezone.utc) + timedelta(days=14)
    
    # Create organization
    org = Organization(
        name=data.name,
        slug=slug,
        owner_user_id="",  # Will be updated after creating member
        owner_email=data.owner_email.lower(),
        status="trial",
        subscription={
            "plan": "trial",
            "status": "trial",
            "trial_ends_at": trial_ends.isoformat(),
            "current_period_start": get_ist_isoformat(),
            "current_period_end": trial_ends.isoformat()
        },
        phone=data.phone,
        industry=data.industry,
        company_size=data.company_size
    )
    
    # Create owner member
    member = OrganizationMember(
        organization_id=org.id,
        email=data.owner_email.lower(),
        name=data.owner_name,
        password_hash=get_password_hash(data.owner_password),
        phone=data.phone,
        role="owner",
        permissions=["all"]  # Owner has all permissions
    )
    
    # Update organization with owner ID
    org.owner_user_id = member.id
    
    # Save to database
    await _db.organizations.insert_one(org.model_dump())
    await _db.organization_members.insert_one(member.model_dump())
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": member.id,
            "organization_id": org.id,
            "type": "org_member",
            "role": member.role
        }
    )
    
    return {
        "message": "Organization created successfully",
        "organization": {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "status": org.status,
            "trial_ends_at": org.subscription.get("trial_ends_at") if isinstance(org.subscription, dict) else None
        },
        "user": {
            "id": member.id,
            "email": member.email,
            "name": member.name,
            "role": member.role
        },
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login")
async def login_organization_member(email: str, password: str):
    """Login for organization members (admins)"""
    member = await _db.organization_members.find_one(
        {"email": email.lower(), "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not member or not verify_password(password, member.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Get organization
    org = await _db.organizations.find_one(
        {"id": member["organization_id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not org:
        raise HTTPException(status_code=401, detail="Organization not found")
    
    # Check org status
    if org.get("status") in ["suspended", "cancelled", "churned"]:
        raise HTTPException(
            status_code=403,
            detail=f"Organization is {org.get('status')}. Please contact support."
        )
    
    # Update last login
    await _db.organization_members.update_one(
        {"id": member["id"]},
        {"$set": {"last_login": get_ist_isoformat()}}
    )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": member["id"],
            "organization_id": org["id"],
            "type": "org_member",
            "role": member.get("role", "member")
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "organization": {
            "id": org["id"],
            "name": org["name"],
            "slug": org["slug"],
            "status": org["status"]
        },
        "user": {
            "id": member["id"],
            "email": member["email"],
            "name": member["name"],
            "role": member.get("role", "member")
        }
    }


# ==================== ORGANIZATION MANAGEMENT ====================

@router.get("/current")
async def get_current_org(auth_info: dict = Depends(get_org_from_token)):
    """Get current organization details"""
    if auth_info.get("is_legacy_admin"):
        return {"is_legacy_admin": True, "message": "Please migrate to organization model"}
    
    org = auth_info.get("organization", {})
    
    # Get usage stats
    companies_count = await _db.companies.count_documents({
        "organization_id": org["id"],
        "is_deleted": {"$ne": True}
    })
    devices_count = await _db.devices.count_documents({
        "organization_id": org["id"],
        "is_deleted": {"$ne": True}
    })
    users_count = await _db.company_users.count_documents({
        "organization_id": org["id"],
        "is_deleted": {"$ne": True}
    })
    
    # Add usage to response
    org["usage"] = {
        "companies": companies_count,
        "devices": devices_count,
        "users": users_count
    }
    
    # Get plan limits
    plan = org.get("subscription", {}).get("plan", "trial")
    plan_config = SUBSCRIPTION_PLANS.get(plan, {})
    org["plan_limits"] = plan_config.get("limits", {})
    org["plan_features"] = plan_config.get("features", [])
    
    return org


@router.put("/current")
async def update_current_org(
    updates: OrganizationUpdate,
    member: dict = Depends(require_org_role("owner", "admin")),
    auth_info: dict = Depends(get_org_from_token)
):
    """Update current organization details"""
    org = auth_info.get("organization", {})
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.organizations.update_one(
        {"id": org["id"]},
        {"$set": update_data}
    )
    
    return await _db.organizations.find_one({"id": org["id"]}, {"_id": 0})


@router.put("/current/branding")
async def update_org_branding(
    branding: OrganizationBrandingUpdate,
    member: dict = Depends(require_org_role("owner", "admin")),
    auth_info: dict = Depends(get_org_from_token)
):
    """Update organization branding settings"""
    org = auth_info.get("organization", {})
    
    update_data = {f"branding.{k}": v for k, v in branding.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.organizations.update_one(
        {"id": org["id"]},
        {"$set": update_data}
    )
    
    updated = await _db.organizations.find_one({"id": org["id"]}, {"_id": 0})
    return updated.get("branding", {})


@router.put("/current/settings")
async def update_org_settings(
    settings: OrganizationSettingsUpdate,
    member: dict = Depends(require_org_role("owner", "admin")),
    auth_info: dict = Depends(get_org_from_token)
):
    """Update organization settings"""
    org = auth_info.get("organization", {})
    
    update_data = {f"settings.{k}": v for k, v in settings.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await _db.organizations.update_one(
        {"id": org["id"]},
        {"$set": update_data}
    )
    
    updated = await _db.organizations.find_one({"id": org["id"]}, {"_id": 0})
    return updated.get("settings", {})


# ==================== TEAM MEMBERS ====================

@router.get("/members")
async def list_org_members(
    auth_info: dict = Depends(get_org_from_token)
):
    """List all members of the organization"""
    org = auth_info.get("organization", {})
    
    members = await _db.organization_members.find(
        {"organization_id": org["id"], "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    ).to_list(100)
    
    return members


@router.post("/members/invite")
async def invite_member(
    data: OrganizationMemberCreate,
    member: dict = Depends(require_org_role("owner", "admin")),
    auth_info: dict = Depends(get_org_from_token)
):
    """Invite a new member to the organization"""
    org = auth_info.get("organization", {})
    
    # Check if email already exists
    existing = await _db.organization_members.find_one(
        {"email": data.email.lower(), "organization_id": org["id"]},
        {"_id": 0}
    )
    if existing:
        raise HTTPException(status_code=400, detail="User already exists in this organization")
    
    # Check existing invitation
    existing_invite = await _db.organization_invitations.find_one(
        {"email": data.email.lower(), "organization_id": org["id"], "status": "pending"},
        {"_id": 0}
    )
    if existing_invite:
        raise HTTPException(status_code=400, detail="Invitation already sent to this email")
    
    # Create invitation
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    invitation = OrganizationInvitation(
        organization_id=org["id"],
        email=data.email.lower(),
        role=data.role,
        permissions=data.permissions or ["view_all"],
        invited_by=member["id"],
        invited_by_name=member.get("name", "Unknown"),
        expires_at=expires_at.isoformat()
    )
    
    await _db.organization_invitations.insert_one(invitation.model_dump())
    
    # TODO: Send invitation email
    
    return {
        "message": "Invitation sent",
        "invitation_id": invitation.id,
        "email": invitation.email,
        "expires_at": invitation.expires_at
    }


@router.post("/members/accept-invite")
async def accept_invitation(token: str, name: str, password: str):
    """Accept an invitation and create account"""
    # Find invitation
    invitation = await _db.organization_invitations.find_one(
        {"invite_token": token, "status": "pending"},
        {"_id": 0}
    )
    
    if not invitation:
        raise HTTPException(status_code=404, detail="Invitation not found or expired")
    
    # Check expiry
    expires_at = datetime.fromisoformat(invitation["expires_at"].replace("Z", "+00:00"))
    if datetime.now(timezone.utc) > expires_at:
        await _db.organization_invitations.update_one(
            {"id": invitation["id"]},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=400, detail="Invitation has expired")
    
    # Create member
    member = OrganizationMember(
        organization_id=invitation["organization_id"],
        email=invitation["email"],
        name=name,
        password_hash=get_password_hash(password),
        role=invitation["role"],
        permissions=invitation.get("permissions", ["view_all"]),
        invited_by=invitation["invited_by"]
    )
    
    await _db.organization_members.insert_one(member.model_dump())
    
    # Update invitation
    await _db.organization_invitations.update_one(
        {"id": invitation["id"]},
        {"$set": {"status": "accepted", "accepted_at": get_ist_isoformat()}}
    )
    
    # Get organization
    org = await _db.organizations.find_one(
        {"id": invitation["organization_id"]},
        {"_id": 0}
    )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": member.id,
            "organization_id": org["id"],
            "type": "org_member",
            "role": member.role
        }
    )
    
    return {
        "message": "Welcome to the team!",
        "access_token": access_token,
        "token_type": "bearer",
        "organization": {
            "id": org["id"],
            "name": org["name"]
        },
        "user": {
            "id": member.id,
            "email": member.email,
            "name": member.name,
            "role": member.role
        }
    }


@router.put("/members/{member_id}")
async def update_member(
    member_id: str,
    updates: OrganizationMemberUpdate,
    current_member: dict = Depends(require_org_role("owner", "admin")),
    auth_info: dict = Depends(get_org_from_token)
):
    """Update a member's details"""
    org = auth_info.get("organization", {})
    
    # Find member
    target = await _db.organization_members.find_one(
        {"id": member_id, "organization_id": org["id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Can't change owner's role
    if target.get("role") == "owner" and updates.role and updates.role != "owner":
        raise HTTPException(status_code=400, detail="Cannot change owner's role")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if update_data:
        await _db.organization_members.update_one(
            {"id": member_id},
            {"$set": update_data}
        )
    
    return await _db.organization_members.find_one(
        {"id": member_id},
        {"_id": 0, "password_hash": 0}
    )


@router.delete("/members/{member_id}")
async def remove_member(
    member_id: str,
    current_member: dict = Depends(require_org_role("owner", "admin")),
    auth_info: dict = Depends(get_org_from_token)
):
    """Remove a member from the organization"""
    org = auth_info.get("organization", {})
    
    # Find member
    target = await _db.organization_members.find_one(
        {"id": member_id, "organization_id": org["id"]},
        {"_id": 0}
    )
    
    if not target:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Can't remove owner
    if target.get("role") == "owner":
        raise HTTPException(status_code=400, detail="Cannot remove organization owner")
    
    # Can't remove yourself (use leave instead)
    if member_id == current_member.get("id"):
        raise HTTPException(status_code=400, detail="Cannot remove yourself. Use leave organization instead.")
    
    # Soft delete
    await _db.organization_members.update_one(
        {"id": member_id},
        {"$set": {"is_deleted": True, "is_active": False}}
    )
    
    return {"message": "Member removed"}


# ==================== SUBSCRIPTION & BILLING ====================

@router.get("/subscription")
async def get_subscription(auth_info: dict = Depends(get_org_from_token)):
    """Get current subscription details"""
    org = auth_info.get("organization", {})
    subscription = org.get("subscription", {})
    
    plan = subscription.get("plan", "trial")
    plan_config = SUBSCRIPTION_PLANS.get(plan, {})
    
    return {
        "subscription": subscription,
        "plan": plan_config,
        "status": org.get("status")
    }


@router.post("/subscription/upgrade")
async def upgrade_subscription(
    plan: str,
    billing_cycle: str = "monthly",
    member: dict = Depends(require_org_role("owner")),
    auth_info: dict = Depends(get_org_from_token)
):
    """Upgrade subscription plan"""
    org = auth_info.get("organization", {})
    
    if plan not in SUBSCRIPTION_PLANS:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    if plan == "enterprise":
        raise HTTPException(
            status_code=400,
            detail="Enterprise plan requires contacting sales. Please reach out to sales@yourcompany.com"
        )
    
    # TODO: Integrate with Stripe/Razorpay for actual payment
    # For now, just update the plan
    
    await _db.organizations.update_one(
        {"id": org["id"]},
        {"$set": {
            "status": "active",
            "subscription.plan": plan,
            "subscription.status": "active",
            "subscription.billing_cycle": billing_cycle,
            "subscription.plan_changed_at": get_ist_isoformat(),
            "updated_at": get_ist_isoformat()
        }}
    )
    
    return {
        "message": f"Upgraded to {SUBSCRIPTION_PLANS[plan]['name']} plan",
        "plan": plan
    }


@router.get("/usage")
async def get_usage_stats(auth_info: dict = Depends(get_org_from_token)):
    """Get current usage statistics"""
    org = auth_info.get("organization", {})
    org_id = org["id"]
    
    # Get counts
    companies = await _db.companies.count_documents({
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    devices = await _db.devices.count_documents({
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    users = await _db.company_users.count_documents({
        "organization_id": org_id,
        "is_deleted": {"$ne": True}
    })
    
    # Get tickets this month
    from datetime import datetime
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    tickets_this_month = await _db.tickets.count_documents({
        "organization_id": org_id,
        "created_at": {"$gte": month_start.isoformat()}
    })
    
    # Get plan limits
    plan = org.get("subscription", {}).get("plan", "trial")
    plan_config = SUBSCRIPTION_PLANS.get(plan, {})
    limits = plan_config.get("limits", {})
    
    return {
        "usage": {
            "companies": companies,
            "devices": devices,
            "users": users,
            "tickets_this_month": tickets_this_month
        },
        "limits": limits,
        "plan": plan
    }
