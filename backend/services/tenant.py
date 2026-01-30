"""
Tenant Middleware - Multi-tenancy enforcement
=============================================
This middleware extracts the organization_id from the authenticated user
and makes it available throughout the request lifecycle.
"""
import logging
from typing import Optional
from fastapi import HTTPException, Depends, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from contextvars import ContextVar

from config import SECRET_KEY, ALGORITHM
from database import db

logger = logging.getLogger(__name__)

# Context variable to store current tenant info
current_org_id: ContextVar[Optional[str]] = ContextVar('current_org_id', default=None)
current_org: ContextVar[Optional[dict]] = ContextVar('current_org', default=None)

security = HTTPBearer()


async def get_org_id_from_admin(admin_email: str) -> Optional[str]:
    """
    Get organization_id for an admin user.
    Used to scope admin queries to their organization.
    """
    # Check if admin has an organization member entry
    org_member = await db.organization_members.find_one(
        {"email": admin_email, "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if org_member:
        return org_member.get("organization_id")
    
    return None


def add_tenant_filter(query: dict, org_id: Optional[str]) -> dict:
    """
    Add organization_id filter to a query if org_id is available.
    For backward compatibility, returns original query if no org_id.
    """
    if org_id:
        return {**query, "organization_id": org_id}
    return query


async def get_tenant_scoped_query(query: dict, admin: dict) -> dict:
    """
    Get a tenant-scoped query based on admin's organization.
    """
    org_id = await get_org_id_from_admin(admin.get("email", ""))
    return add_tenant_filter(query, org_id)


class TenantContext:
    """
    Tenant context manager for multi-tenancy.
    Provides organization-scoped database queries.
    """
    
    def __init__(self, organization_id: str, organization: dict = None):
        self.organization_id = organization_id
        self.organization = organization
    
    def get_query_filter(self) -> dict:
        """Get MongoDB query filter for tenant scoping"""
        return {"organization_id": self.organization_id}
    
    def scope_query(self, query: dict) -> dict:
        """Add organization_id filter to an existing query"""
        return {**query, "organization_id": self.organization_id}
    
    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled for this organization's plan"""
        if not self.organization:
            return False
        
        subscription = self.organization.get("subscription", {})
        plan = subscription.get("plan", "trial")
        
        from models.organization import SUBSCRIPTION_PLANS
        plan_config = SUBSCRIPTION_PLANS.get(plan, {})
        features = plan_config.get("features", [])
        
        return "all" in features or feature in features
    
    def check_limit(self, resource: str, current_count: int) -> tuple[bool, int]:
        """
        Check if organization is within limits for a resource.
        Returns (is_within_limit, max_limit)
        """
        if not self.organization:
            return False, 0
        
        subscription = self.organization.get("subscription", {})
        plan = subscription.get("plan", "trial")
        
        from models.organization import SUBSCRIPTION_PLANS
        plan_config = SUBSCRIPTION_PLANS.get(plan, {})
        limits = plan_config.get("limits", {})
        
        max_limit = limits.get(resource, 0)
        
        # -1 means unlimited
        if max_limit == -1:
            return True, -1
        
        return current_count < max_limit, max_limit


def get_tenant_context() -> TenantContext:
    """Get current tenant context from context variable"""
    org_id = current_org_id.get()
    org = current_org.get()
    
    if not org_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context not available"
        )
    
    return TenantContext(org_id, org)


async def get_org_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Extract organization info from JWT token.
    This is used for organization member (admin) authentication.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        org_id: str = payload.get("organization_id")
        user_type: str = payload.get("type")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # For backward compatibility: if no org_id in token, check if it's a legacy admin
    if not org_id:
        # Check legacy admins table
        admin = await db.admins.find_one({"email": payload.get("sub")}, {"_id": 0})
        if admin:
            # Legacy admin - they'll need to be migrated to an organization
            return {
                "user": admin,
                "organization_id": None,
                "organization": None,
                "is_legacy_admin": True
            }
        raise credentials_exception
    
    # Get organization member
    member = await db.organization_members.find_one(
        {"id": user_id, "organization_id": org_id, "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    )
    
    if not member:
        raise credentials_exception
    
    # Get organization
    organization = await db.organizations.find_one(
        {"id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization not found or inactive"
        )
    
    # Check organization status
    if organization.get("status") in ["suspended", "cancelled", "churned"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Organization is {organization.get('status')}. Please contact support."
        )
    
    # Set context variables
    current_org_id.set(org_id)
    current_org.set(organization)
    
    return {
        "user": member,
        "organization_id": org_id,
        "organization": organization,
        "is_legacy_admin": False
    }


async def get_current_org_member(auth_info: dict = Depends(get_org_from_token)) -> dict:
    """
    Get current authenticated organization member.
    Use this as a dependency for org-admin routes.
    """
    if auth_info.get("is_legacy_admin"):
        # Return legacy admin for backward compatibility
        return auth_info["user"]
    
    return auth_info["user"]


async def get_current_organization(auth_info: dict = Depends(get_org_from_token)) -> dict:
    """
    Get current organization.
    Use this as a dependency when you need org info.
    """
    org = auth_info.get("organization")
    if not org and not auth_info.get("is_legacy_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Organization not found"
        )
    return org


def require_org_role(*allowed_roles):
    """
    Dependency factory to require specific organization roles.
    Usage: @router.get("/", dependencies=[Depends(require_org_role("owner", "admin"))])
    """
    async def check_role(auth_info: dict = Depends(get_org_from_token)):
        if auth_info.get("is_legacy_admin"):
            return auth_info["user"]  # Legacy admins have full access
        
        user = auth_info.get("user", {})
        user_role = user.get("role", "")
        
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{user_role}' not authorized. Required: {', '.join(allowed_roles)}"
            )
        
        return user
    
    return check_role


def require_feature(feature_name: str):
    """
    Dependency factory to require a specific feature.
    Usage: @router.get("/", dependencies=[Depends(require_feature("sla_management"))])
    """
    async def check_feature(auth_info: dict = Depends(get_org_from_token)):
        if auth_info.get("is_legacy_admin"):
            return True  # Legacy admins have access to all features
        
        org = auth_info.get("organization", {})
        subscription = org.get("subscription", {})
        plan = subscription.get("plan", "trial")
        
        from models.organization import SUBSCRIPTION_PLANS
        plan_config = SUBSCRIPTION_PLANS.get(plan, {})
        features = plan_config.get("features", [])
        
        if "all" not in features and feature_name not in features:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Feature '{feature_name}' not available on {plan_config.get('name', plan)} plan. Please upgrade."
            )
        
        return True
    
    return check_feature


async def check_resource_limit(resource: str, current_count: int, auth_info: dict) -> None:
    """
    Check if organization is within limits for a resource.
    Raises HTTPException if limit exceeded.
    """
    if auth_info.get("is_legacy_admin"):
        return  # Legacy admins have no limits
    
    org = auth_info.get("organization", {})
    subscription = org.get("subscription", {})
    plan = subscription.get("plan", "trial")
    
    from models.organization import SUBSCRIPTION_PLANS
    plan_config = SUBSCRIPTION_PLANS.get(plan, {})
    limits = plan_config.get("limits", {})
    
    max_limit = limits.get(resource, 0)
    
    # -1 means unlimited
    if max_limit == -1:
        return
    
    if current_count >= max_limit:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Limit reached: {resource} ({current_count}/{max_limit}). Please upgrade your plan."
        )


# ==================== COMPANY USER TENANT CONTEXT ====================

async def get_org_from_company_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    """
    Get organization context from a company portal user.
    Company users belong to a company, which belongs to an organization.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        user_type: str = payload.get("type")
        
        if user_id is None or user_type != "company_user":
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Get company user
    user = await db.company_users.find_one(
        {"id": user_id, "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    )
    
    if not user:
        raise credentials_exception
    
    # Get company
    company = await db.companies.find_one(
        {"id": user.get("company_id"), "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not company:
        raise credentials_exception
    
    # Get organization (if exists)
    org_id = company.get("organization_id")
    organization = None
    
    if org_id:
        organization = await db.organizations.find_one(
            {"id": org_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
        
        # Check organization status
        if organization and organization.get("status") in ["suspended", "cancelled", "churned"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Service temporarily unavailable. Please contact support."
            )
        
        # Set context variables
        current_org_id.set(org_id)
        current_org.set(organization)
    
    return {
        "user": user,
        "company": company,
        "organization_id": org_id,
        "organization": organization
    }
