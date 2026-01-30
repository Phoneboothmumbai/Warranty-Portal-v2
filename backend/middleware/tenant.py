"""
Tenant Resolution Middleware
============================
Resolves tenant (organization) from subdomain or host header.
This is the foundational piece for subdomain-based multi-tenancy.

Resolution Priority:
- Production: Host header only
- Local/Staging/Preview: Header injection → Query param → Host header
"""
import os
import logging
from typing import Optional, Tuple
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response, JSONResponse
from database import db

logger = logging.getLogger(__name__)

# Environment detection
ENVIRONMENT = os.environ.get("ENVIRONMENT", "development")
IS_PRODUCTION = ENVIRONMENT == "production"

# Main platform domain (where platform admin lives)
# In production this would be like "app.assetvault.io"
PLATFORM_DOMAIN = os.environ.get("PLATFORM_DOMAIN", "app.assetvault.io")

# Known preview/development domains that should use fallback resolution
PREVIEW_DOMAINS = [
    "localhost",
    "127.0.0.1",
    ".preview.emergentagent.com",
    ".vercel.app",
    ".ngrok.io"
]


def is_preview_domain(host: str) -> bool:
    """Check if the host is a known preview/development domain"""
    for domain in PREVIEW_DOMAINS:
        if domain.startswith("."):
            if domain[1:] in host:
                return True
        elif domain in host:
            return True
    return False


def extract_subdomain(host: str) -> Optional[str]:
    """
    Extract subdomain from host.
    Examples:
    - acme.assetvault.io → acme
    - acme.app.assetvault.io → acme
    - localhost:3000 → None
    - app.assetvault.io → None (this is platform domain)
    """
    if not host:
        return None
    
    # Remove port if present
    host = host.split(":")[0].lower()
    
    # Skip if it's a known preview domain without subdomain
    if host == "localhost" or host == "127.0.0.1":
        return None
    
    # For preview.emergentagent.com domains
    if ".preview.emergentagent.com" in host:
        # mspportal.preview.emergentagent.com - no tenant subdomain
        # acme.mspportal.preview.emergentagent.com - acme is tenant
        parts = host.replace(".preview.emergentagent.com", "").split(".")
        if len(parts) > 1:
            return parts[0]  # First part is tenant subdomain
        return None
    
    # Standard subdomain extraction
    # acme.assetvault.io → acme
    parts = host.split(".")
    
    # If it looks like: subdomain.domain.tld (3+ parts)
    if len(parts) >= 3:
        potential_subdomain = parts[0]
        
        # Skip common non-tenant subdomains
        skip_subdomains = ["www", "app", "api", "admin", "platform", "mail", "ftp"]
        if potential_subdomain in skip_subdomains:
            return None
        
        return potential_subdomain
    
    return None


async def resolve_tenant_from_slug(slug: str) -> Optional[dict]:
    """Look up tenant organization by slug"""
    if not slug:
        return None
    
    org = await db.organizations.find_one(
        {"slug": slug.lower(), "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    return org


async def resolve_tenant(request: Request) -> Tuple[Optional[dict], Optional[str]]:
    """
    Resolve tenant based on request context.
    
    Returns:
        Tuple of (organization dict or None, resolution method or None)
    
    Resolution priority (non-production):
        1. X-Tenant-Slug header (for testing)
        2. _tenant query param (for browser testing)
        3. Host header subdomain
    
    Resolution in production:
        1. Host header subdomain only
    """
    host = request.headers.get("host", "")
    
    # Check if this is a platform admin request (no tenant needed)
    path = request.url.path
    if path.startswith("/api/platform"):
        return None, "platform_route"
    
    # Non-production: Allow header/query param overrides
    if not IS_PRODUCTION or is_preview_domain(host):
        # 1. Header injection (highest priority for testing)
        tenant_slug = request.headers.get("x-tenant-slug")
        if tenant_slug:
            org = await resolve_tenant_from_slug(tenant_slug)
            if org:
                return org, "header"
            logger.warning(f"Tenant not found for header slug: {tenant_slug}")
        
        # 2. Query param (for browser testing)
        tenant_param = request.query_params.get("_tenant")
        if tenant_param:
            org = await resolve_tenant_from_slug(tenant_param)
            if org:
                return org, "query_param"
            logger.warning(f"Tenant not found for query param: {tenant_param}")
    
    # 3. Host header subdomain (production method)
    subdomain = extract_subdomain(host)
    if subdomain:
        org = await resolve_tenant_from_slug(subdomain)
        if org:
            return org, "subdomain"
        # In production, unknown subdomain is an error
        # In dev, we might not have a subdomain configured
        if IS_PRODUCTION:
            logger.error(f"Unknown tenant subdomain: {subdomain}")
    
    return None, None


class TenantMiddleware(BaseHTTPMiddleware):
    """
    Middleware that resolves tenant from request and attaches to request state.
    
    Usage in routes:
        tenant = request.state.tenant  # Organization dict or None
        tenant_id = request.state.tenant_id  # Organization ID or None
    """
    
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip tenant resolution for certain paths
        path = request.url.path
        
        # Public routes that don't need tenant context
        public_prefixes = [
            "/api/platform",  # Platform admin routes
            "/api/auth/setup",  # Initial setup
            "/api/settings/public",  # Public settings
            "/api/masters/public",  # Public masters
            "/api/signup",  # Public signup
            "/api/security/info",  # Security info
            "/api/static-pages",  # Static pages
            "/uploads",  # Static files
            "/docs",  # API docs
            "/openapi.json",
        ]
        
        skip_tenant = any(path.startswith(prefix) for prefix in public_prefixes)
        
        if skip_tenant:
            request.state.tenant = None
            request.state.tenant_id = None
            request.state.tenant_slug = None
            request.state.tenant_resolution = None
            return await call_next(request)
        
        # Resolve tenant
        tenant, resolution_method = await resolve_tenant(request)
        
        # Attach to request state
        request.state.tenant = tenant
        request.state.tenant_id = tenant.get("id") if tenant else None
        request.state.tenant_slug = tenant.get("slug") if tenant else None
        request.state.tenant_resolution = resolution_method
        
        # Check tenant status if resolved
        if tenant:
            status = tenant.get("status")
            if status == "suspended":
                return JSONResponse(
                    status_code=403,
                    content={
                        "error": "tenant_suspended",
                        "message": "This workspace has been suspended. Please contact support.",
                        "tenant_name": tenant.get("name")
                    }
                )
            elif status == "churned":
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": "tenant_not_found",
                        "message": "This workspace no longer exists."
                    }
                )
        
        return await call_next(request)


# Dependency for routes that require tenant context
async def require_tenant(request: Request) -> dict:
    """
    FastAPI dependency that requires a valid tenant.
    Use this for routes that must have tenant context.
    """
    tenant = getattr(request.state, "tenant", None)
    
    if not tenant:
        # Check if we're in a preview environment
        host = request.headers.get("host", "")
        if is_preview_domain(host):
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "tenant_required",
                    "message": "Tenant context required. Use X-Tenant-Slug header or _tenant query param.",
                    "hint": "Add ?_tenant=acme-corporation to the URL or set X-Tenant-Slug header"
                }
            )
        raise HTTPException(
            status_code=404,
            detail={
                "error": "workspace_not_found",
                "message": "This workspace does not exist. Please check the URL."
            }
        )
    
    return tenant


async def get_optional_tenant(request: Request) -> Optional[dict]:
    """
    FastAPI dependency that returns tenant if available, None otherwise.
    Use this for routes that can work with or without tenant context.
    """
    return getattr(request.state, "tenant", None)


# Helper function to get tenant context for API responses
def get_tenant_context(tenant: Optional[dict]) -> dict:
    """
    Get a safe tenant context dict for API responses.
    Includes only public tenant information.
    """
    if not tenant:
        return {}
    
    branding = tenant.get("branding", {})
    
    return {
        "tenant_id": tenant.get("id"),
        "tenant_name": tenant.get("name"),
        "tenant_slug": tenant.get("slug"),
        "branding": {
            "logo_url": branding.get("logo_url"),
            "logo_base64": branding.get("logo_base64"),
            "accent_color": branding.get("accent_color", "#0F62FE"),
            "company_name": branding.get("company_name") or tenant.get("name"),
            "favicon_url": branding.get("favicon_url")
        }
    }
