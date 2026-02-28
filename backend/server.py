"""
Warranty & Asset Tracking Portal - Main Server
==============================================
This is a refactored version with modular architecture.
Models, services, and utilities are now in separate modules.
"""
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query, Body
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from typing import List, Optional, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx
import base64
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
import shutil
import json
import qrcode
from pydantic import BaseModel, Field

# Import from modular structure
from config import ROOT_DIR, UPLOAD_DIR, OSTICKET_URL, OSTICKET_API_KEY, SECRET_KEY, ALGORITHM, IST
from database import db, client
from utils.helpers import get_ist_now, get_ist_isoformat, calculate_warranty_expiry, is_warranty_active, days_until_expiry
from services.auth import (
    verify_password, get_password_hash, create_access_token,
    get_current_admin, get_current_company_user, require_company_admin,
    log_audit, security
)
from services.osticket import create_osticket
from services.seeding import seed_default_masters, seed_default_supplies

# Import all models
from models.auth import Token, AdminUser, AdminLogin, AdminCreate
from models.common import MasterItem, MasterItemCreate, MasterItemUpdate, AuditLog, Settings, SettingsUpdate
from models.company import (
    Company, CompanyCreate, CompanyUpdate,
    User, UserCreate, UserUpdate,
    CompanyUser, CompanyUserCreate, CompanyUserUpdate,
    CompanyUserRegister, CompanyLogin,
    CompanyEmployee, CompanyEmployeeCreate, CompanyEmployeeUpdate
)
from models.device import (
    ConsumableItem, Device, DeviceCreate, DeviceUpdate,
    AssignmentHistory, Part, PartCreate, PartUpdate,
    ConsumableOrderItem, ConsumableOrder
)
from models.service import (
    RenewalRequest, RenewalRequestCreate,
    ServiceAttachment, ServiceHistory, ServiceHistoryCreate, ServiceHistoryUpdate,
    ServicePartUsed
)
from models.amc import (
    AMC, AMCCreate, AMCUpdate,
    AMCCoverageIncludes, AMCExclusions, AMCEntitlements, AMCAssetMapping,
    AMCContract, AMCContractCreate, AMCContractUpdate,
    AMCUsageRecord, AMCDeviceAssignment, AMCDeviceAssignmentCreate,
    AMCBulkAssignmentPreview
)
from models.site import (
    Site, SiteCreate, SiteUpdate,
    DeploymentItem, Deployment, DeploymentCreate, DeploymentUpdate
)
from models.license import License, LicenseCreate, LicenseUpdate
from models.supplies import (
    SupplyCategory, SupplyCategoryCreate, SupplyCategoryUpdate,
    SupplyProduct, SupplyProductCreate, SupplyProductUpdate,
    SupplyOrderItem, SupplyOrderLocation, SupplyOrder
)
from models.subscription import (
    EmailSubscription, EmailSubscriptionCreate, EmailSubscriptionUpdate,
    SubscriptionTicket, SubscriptionTicketCreate
)
from models.internet_service import (
    InternetService, InternetServiceCreate, InternetServiceUpdate
)
from models.device_model import (
    DeviceModel, DeviceModelCreate, DeviceModelUpdate,
    AILookupRequest
)
from services.device_lookup import get_or_create_device_model
from utils.security import limiter, RATE_LIMITS, validate_password_strength, sanitize_input
from utils.tenant_scope import get_admin_org_id, scope_query, get_scoped_query, insert_with_org_id
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from fastapi import Request

# Import tenant middleware
from middleware.tenant import TenantMiddleware, require_tenant, get_optional_tenant, get_tenant_context

# Create the main app
app = FastAPI(title="Warranty & Asset Tracking Portal")
api_router = APIRouter(prefix="/api")

# Add tenant resolution middleware (before other middleware)
app.add_middleware(TenantMiddleware)

# Add rate limiter to app
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Serve uploaded files
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")

# ==================== PUBLIC ENDPOINTS ====================

@api_router.get("/")
async def root():
    return {"message": "Warranty & Asset Tracking Portal API"}

@api_router.get("/security/info")
async def get_security_info():
    """Return public security settings for frontend display"""
    return {
        "password_requirements": {
            "min_length": 8,
            "require_uppercase": True,
            "require_lowercase": True,
            "require_digit": True,
            "require_special": True
        },
        "session_timeout_minutes": 480,
        "rate_limiting": {
            "login_attempts_per_minute": 5,
            "registration_attempts_per_minute": 3
        }
    }

@api_router.get("/settings/public")
async def get_public_settings():
    settings = await db.settings.find_one({"id": "settings"}, {"_id": 0})
    if not settings:
        settings = Settings().model_dump()
    return {
        "logo_url": settings.get("logo_url"),
        "logo_base64": settings.get("logo_base64"),
        "accent_color": settings.get("accent_color", "#0F62FE"),
        "company_name": settings.get("company_name", "Warranty Portal")
    }


# ==================== TENANT CONTEXT ENDPOINT ====================

@api_router.get("/tenant/context")
async def get_tenant_context_api(request: Request):
    """
    Get tenant context from subdomain/header/query param.
    Frontend calls this to get branding and tenant info.
    
    Resolution methods:
    - Production: Subdomain in URL (acme.assetvault.io)
    - Development: X-Tenant-Slug header or ?_tenant=slug query param
    """
    tenant = getattr(request.state, "tenant", None)
    resolution = getattr(request.state, "tenant_resolution", None)
    
    if not tenant:
        return {
            "tenant": None,
            "resolution": resolution,
            "message": "No tenant context. Use subdomain, X-Tenant-Slug header, or _tenant query param."
        }
    
    # Build tenant context response
    branding = tenant.get("branding", {})
    settings = tenant.get("settings", {})
    
    return {
        "tenant": {
            "id": tenant.get("id"),
            "name": tenant.get("name"),
            "slug": tenant.get("slug"),
            "status": tenant.get("status"),
            "branding": {
                "logo_url": branding.get("logo_url"),
                "logo_base64": branding.get("logo_base64"),
                "accent_color": branding.get("accent_color", "#0F62FE"),
                "company_name": branding.get("company_name") or tenant.get("name"),
                "favicon_url": branding.get("favicon_url"),
                "custom_css": branding.get("custom_css")
            },
            "settings": {
                "timezone": settings.get("timezone", "Asia/Kolkata"),
                "currency": settings.get("currency", "INR"),
                "enable_public_portal": settings.get("enable_public_portal", True),
                "enable_ai_features": settings.get("enable_ai_features", True)
            }
        },
        "resolution": resolution
    }


@api_router.get("/tenant/verify/{slug}")
async def verify_tenant_slug(slug: str):
    """
    Public endpoint to verify if a tenant slug exists.
    Used for subdomain validation during signup.
    """
    org = await db.organizations.find_one(
        {"slug": slug.lower(), "is_deleted": {"$ne": True}},
        {"_id": 0, "id": 1, "name": 1, "slug": 1, "status": 1}
    )
    
    if not org:
        return {"exists": False, "slug": slug}
    
    return {
        "exists": True,
        "slug": org.get("slug"),
        "name": org.get("name"),
        "status": org.get("status")
    }


@api_router.get("/public/plans")
async def get_public_plans():
    """
    Public endpoint to get active, public plans for pricing page.
    No authentication required. Plans are managed via Platform Admin.
    """
    from models.plan import DEFAULT_PLANS
    
    plans = await db.plans.find(
        {
            "status": "active",
            "is_public": True,
            "is_deleted": {"$ne": True}
        },
        {"_id": 0, "created_by": 0, "updated_by": 0, "deleted_by": 0, "deleted_at": 0}
    ).sort("display_order", 1).to_list(20)
    
    # If no plans in DB, return defaults
    if not plans:
        return [
            {
                "id": f"default-{i}",
                "name": p["name"],
                "slug": p["slug"],
                "tagline": p.get("tagline", ""),
                "description": p.get("description", ""),
                "price_monthly": p["price_monthly"],
                "price_yearly": p["price_yearly"],
                "currency": "INR",
                "display_order": p["display_order"],
                "is_popular": p.get("is_popular", False),
                "is_trial": p.get("is_trial", False),
                "trial_days": p.get("trial_days", 0),
                "color": p.get("color", "#6366f1"),
                "features": p.get("features", {}),
                "limits": p.get("limits", {}),
                "support_level": p.get("support_level", "community"),
                "response_time_hours": p.get("response_time_hours")
            }
            for i, p in enumerate(DEFAULT_PLANS)
        ]
    
    return plans


@api_router.get("/masters/public")
async def get_public_masters(
    master_type: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """Get active masters for public forms with optional search"""
    query = {"is_active": True}
    if master_type:
        query["type"] = master_type
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"code": search_regex}
        ]
    
    masters = await db.masters.find(query, {"_id": 0}).sort("sort_order", 1).to_list(limit)
    
    # Add label for SmartSelect compatibility
    for m in masters:
        m.get("label", m.get("name", "Unknown")) or m.get("name", "Unknown"); m["label"] = m.get("name", "Unknown")
    
    return masters

@api_router.get("/warranty/search")
async def search_warranty(q: str):
    """
    Search warranty by serial number or asset tag
    Searches both Devices and Parts
    
    P0 FIX - AMC OVERRIDE RULE:
    IF device has ACTIVE AMC:
      → Show AMC coverage (ignore device warranty expiry)
    ELSE:
      → Show device warranty
    """
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Search query too short")
    
    q = q.strip()
    
    # First, search for a Part by serial number
    part = await db.parts.find_one(
        {"$and": [
            {"is_deleted": {"$ne": True}},
            {"serial_number": {"$regex": f"^{q}$", "$options": "i"}}
        ]},
        {"_id": 0}
    )
    
    if part:
        # Found a part - get the parent device info
        device = await db.devices.find_one(
            {"id": part["device_id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
        
        company_name = "Unknown"
        if device:
            company = await db.companies.find_one({"id": device["company_id"], "is_deleted": {"$ne": True}}, {"_id": 0, "name": 1})
            company_name = company.get("name") if company else "Unknown"
        
        # Part warranty status
        part_warranty_active = is_warranty_active(part.get("warranty_expiry_date", ""))
        
        return {
            "search_type": "part",
            "part": {
                "id": part.get("id"),
                "part_type": part.get("part_type"),
                "part_name": part.get("part_name"),
                "brand": part.get("brand"),
                "model_number": part.get("model_number"),
                "serial_number": part.get("serial_number"),
                "capacity": part.get("capacity"),
                "purchase_date": part.get("purchase_date"),
                "replaced_date": part.get("replaced_date"),
                "warranty_months": part.get("warranty_months"),
                "warranty_expiry_date": part.get("warranty_expiry_date"),
                "warranty_active": part_warranty_active,
                "vendor": part.get("vendor")
            },
            "parent_device": {
                "id": device.get("id") if device else None,
                "device_type": device.get("device_type") if device else None,
                "brand": device.get("brand") if device else None,
                "model": device.get("model") if device else None,
                "serial_number": device.get("serial_number") if device else None
            } if device else None,
            "company_name": company_name,
            "coverage_source": "part_warranty",
            "effective_coverage_end": part.get("warranty_expiry_date")
        }
    
    # Search device by serial number or asset tag
    device = await db.devices.find_one(
        {"$and": [
            {"is_deleted": {"$ne": True}},
            {"$or": [
                {"serial_number": {"$regex": f"^{q}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{q}$", "$options": "i"}}
            ]}
        ]},
        {"_id": 0}
    )
    
    if not device:
        raise HTTPException(status_code=404, detail="No records found for this Serial Number / Asset Tag. Please verify the Serial Number or Asset Tag and try again.")
    
    # Check if device is retired/scrapped
    if device.get("status") in ["retired", "scrapped"]:
        return {
            "device": {
                "id": device.get("id"),
                "device_type": device.get("device_type"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "asset_tag": device.get("asset_tag"),
                "status": device.get("status"),
                "message": "This asset is no longer active"
            },
            "company_name": None,
            "assigned_user": None,
            "parts": [],
            "amc": None,
            "amc_contract": None,
            "coverage_source": None,
            "service_count": 0
        }
    
    # Get company info (only name, no sensitive data)
    company = await db.companies.find_one({"id": device["company_id"], "is_deleted": {"$ne": True}}, {"_id": 0, "name": 1})
    company_name = company.get("name") if company else "Unknown"
    
    # Get assigned user (only name, no sensitive data)
    assigned_user = None
    if device.get("assigned_user_id"):
        user = await db.users.find_one({"id": device["assigned_user_id"], "is_deleted": {"$ne": True}}, {"_id": 0, "name": 1})
        assigned_user = user.get("name") if user else None
    
    # Calculate device warranty status
    device_warranty_expiry = device.get("warranty_end_date")
    device_warranty_active = is_warranty_active(device_warranty_expiry) if device_warranty_expiry else False
    
    # P0 FIX: Check AMC from amc_device_assignments JOIN (not old amc collection)
    active_amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device["id"],
        "status": "active"
    }, {"_id": 0})
    
    amc_contract_info = None
    amc_coverage_active = False
    coverage_source = "device_warranty"  # Default
    effective_coverage_end = device_warranty_expiry
    
    if active_amc_assignment:
        # Check if AMC coverage is still valid
        amc_coverage_active = is_warranty_active(active_amc_assignment.get("coverage_end", ""))
        
        if amc_coverage_active:
            # Get full AMC contract details
            amc_contract = await db.amc_contracts.find_one({
                "id": active_amc_assignment["amc_contract_id"],
                "is_deleted": {"$ne": True}
            }, {"_id": 0})
            
            if amc_contract:
                coverage_source = "amc_contract"
                effective_coverage_end = active_amc_assignment.get("coverage_end")
                
                amc_contract_info = {
                    "contract_id": amc_contract["id"],
                    "name": amc_contract.get("name"),
                    "amc_type": amc_contract.get("amc_type"),
                    "coverage_start": active_amc_assignment.get("coverage_start"),
                    "coverage_end": active_amc_assignment.get("coverage_end"),
                    "active": True,
                    "coverage_includes": amc_contract.get("coverage_includes"),
                    "entitlements": amc_contract.get("entitlements")
                }
    
    # Also check legacy AMC collection for backward compatibility
    legacy_amc = await db.amc.find_one({"device_id": device["id"], "is_deleted": {"$ne": True}}, {"_id": 0})
    legacy_amc_info = None
    if legacy_amc:
        legacy_amc_active = is_warranty_active(legacy_amc.get("end_date", ""))
        legacy_amc_info = {
            "start_date": legacy_amc.get("start_date"),
            "end_date": legacy_amc.get("end_date"),
            "active": legacy_amc_active
        }
        
        # If no active AMC contract but legacy AMC is active, use it
        if not amc_coverage_active and legacy_amc_active:
            coverage_source = "legacy_amc"
            effective_coverage_end = legacy_amc.get("end_date")
    
    # Get parts and their warranty status
    parts_cursor = db.parts.find({"device_id": device["id"], "is_deleted": {"$ne": True}}, {"_id": 0})
    parts = []
    async for part in parts_cursor:
        part_warranty_active = is_warranty_active(part.get("warranty_expiry_date", ""))
        parts.append({
            "part_name": part.get("part_name"),
            "replaced_date": part.get("replaced_date"),
            "warranty_months": part.get("warranty_months"),
            "warranty_expiry_date": part.get("warranty_expiry_date"),
            "warranty_active": part_warranty_active
        })
    
    # Get service history count (public sees count, not details)
    service_count = await db.service_history.count_documents({"device_id": device["id"]})
    
    # Determine final warranty status based on AMC OVERRIDE RULE
    # AMC takes priority over device warranty
    final_warranty_active = amc_coverage_active or device_warranty_active
    if amc_coverage_active:
        final_warranty_active = True  # AMC overrides even if device warranty expired
    
    return {
        "search_type": "device",
        "device": {
            "id": device.get("id"),
            "device_type": device.get("device_type"),
            "brand": device.get("brand"),
            "model": device.get("model"),
            "serial_number": device.get("serial_number"),
            "asset_tag": device.get("asset_tag"),
            "purchase_date": device.get("purchase_date"),
            "warranty_end_date": device_warranty_expiry,
            "warranty_active": final_warranty_active,
            "device_warranty_active": device_warranty_active,  # Original device warranty status
            "condition": device.get("condition"),
            "status": device.get("status")
        },
        "company_name": company_name,
        "assigned_user": assigned_user,
        "parts": parts,
        "amc": legacy_amc_info,  # Legacy AMC for backward compatibility
        "amc_contract": amc_contract_info,  # New AMC contract info
        "coverage_source": coverage_source,  # "amc_contract", "legacy_amc", or "device_warranty"
        "effective_coverage_end": effective_coverage_end,
        "service_count": service_count
    }

@api_router.get("/warranty/pdf/{serial_number}")
async def generate_warranty_pdf(serial_number: str):
    """Generate PDF warranty report"""
    device = await db.devices.find_one(
        {"$and": [
            {"is_deleted": {"$ne": True}},
            {"$or": [
                {"serial_number": {"$regex": f"^{serial_number}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{serial_number}$", "$options": "i"}}
            ]}
        ]},
        {"_id": 0}
    )
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    company = await db.companies.find_one({"id": device["company_id"]}, {"_id": 0, "name": 1})
    company_name = company.get("name") if company else "Unknown"
    
    parts_cursor = db.parts.find({"device_id": device["id"], "is_deleted": {"$ne": True}}, {"_id": 0})
    parts = []
    async for part in parts_cursor:
        parts.append(part)
    
    # P0 FIX: Check AMC from amc_device_assignments JOIN (not old amc collection)
    active_amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device["id"],
        "status": "active"
    }, {"_id": 0})
    
    amc_contract_info = None
    if active_amc_assignment:
        # Check if AMC coverage is still valid
        if is_warranty_active(active_amc_assignment.get("coverage_end", "")):
            # Get full AMC contract details
            amc_contract = await db.amc_contracts.find_one({
                "id": active_amc_assignment["amc_contract_id"],
                "is_deleted": {"$ne": True}
            }, {"_id": 0})
            
            if amc_contract:
                amc_contract_info = {
                    "name": amc_contract.get("name"),
                    "amc_type": amc_contract.get("amc_type"),
                    "coverage_start": active_amc_assignment.get("coverage_start"),
                    "coverage_end": active_amc_assignment.get("coverage_end"),
                    "coverage_includes": amc_contract.get("coverage_includes"),
                    "entitlements": amc_contract.get("entitlements")
                }
    
    settings = await db.settings.find_one({"id": "settings"}, {"_id": 0})
    portal_name = settings.get("company_name", "Warranty Portal") if settings else "Warranty Portal"
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=50, leftMargin=50, topMargin=50, bottomMargin=50)
    story = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontSize=18, spaceAfter=20, textColor=colors.HexColor('#0F172A'))
    heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=10, textColor=colors.HexColor('#0F172A'))
    body_style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=10, spaceAfter=5, textColor=colors.HexColor('#64748B'))
    
    story.append(Paragraph(f"{portal_name} - Warranty Report", title_style))
    story.append(Paragraph(f"Generated: {get_ist_now().strftime('%d %B %Y, %H:%M')}", body_style))
    story.append(Spacer(1, 20))
    
    story.append(Paragraph("Device Information", heading_style))
    device_data = [
        ["Device Type", device.get("device_type", "-")],
        ["Brand", device.get("brand", "-")],
        ["Model", device.get("model", "-")],
        ["Serial Number", device.get("serial_number", "-")],
        ["Asset Tag", device.get("asset_tag", "-") or "-"],
        ["Company", company_name],
        ["Purchase Date", device.get("purchase_date", "-")],
        ["Condition", device.get("condition", "-").title()],
        ["Warranty Expiry", device.get("warranty_end_date", "-") or "Not specified"],
        ["Warranty Status", "Active" if is_warranty_active(device.get("warranty_end_date", "")) else "Expired / Not Covered"]
    ]
    
    device_table = Table(device_data, colWidths=[2*inch, 4*inch])
    device_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(device_table)
    story.append(Spacer(1, 20))
    
    if parts:
        story.append(Paragraph("Parts Warranty Status", heading_style))
        parts_data = [["Part Name", "Replaced Date", "Warranty", "Expiry", "Status"]]
        for part in parts:
            status = "Active" if is_warranty_active(part.get("warranty_expiry_date", "")) else "Expired"
            parts_data.append([
                part.get("part_name", "-"),
                part.get("replaced_date", "-"),
                f"{part.get('warranty_months', 0)} months",
                part.get("warranty_expiry_date", "-"),
                status
            ])
        
        parts_table = Table(parts_data, colWidths=[1.5*inch, 1.2*inch, 1*inch, 1.2*inch, 1*inch])
        parts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0F62FE')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ]))
        story.append(parts_table)
        story.append(Spacer(1, 20))
    
    story.append(Paragraph("AMC / Service Coverage", heading_style))
    if amc_contract_info:
        amc_type_display = (amc_contract_info.get("amc_type") or "standard").replace("_", " ").title()
        coverage_includes = amc_contract_info.get("coverage_includes", {})
        
        # Build coverage details string
        coverage_items = []
        if coverage_includes.get("onsite_support"):
            coverage_items.append("Onsite Support")
        if coverage_includes.get("remote_support"):
            coverage_items.append("Remote Support")
        if coverage_includes.get("preventive_maintenance"):
            coverage_items.append("Preventive Maintenance")
        coverage_str = ", ".join(coverage_items) if coverage_items else "Standard Coverage"
        
        # Build entitlements string
        entitlements = amc_contract_info.get("entitlements", {})
        entitlement_items = []
        if entitlements.get("onsite_visits_per_year"):
            visits = entitlements["onsite_visits_per_year"]
            entitlement_items.append(f"{visits} Onsite Visits/Year" if visits != -1 else "Unlimited Onsite Visits")
        if entitlements.get("remote_support_count"):
            remote = entitlements["remote_support_count"]
            entitlement_items.append(f"{remote} Remote Support Sessions" if remote != -1 else "Unlimited Remote Support")
        entitlement_str = ", ".join(entitlement_items) if entitlement_items else "-"
        
        amc_data = [
            ["Contract Name", amc_contract_info.get("name", "-")],
            ["AMC Type", amc_type_display],
            ["Coverage Start", amc_contract_info.get("coverage_start", "-")],
            ["Coverage End", amc_contract_info.get("coverage_end", "-")],
            ["Status", "Active"],
            ["Coverage Includes", coverage_str],
            ["Entitlements", entitlement_str]
        ]
    else:
        amc_data = [["Status", "No active AMC found for this device"]]
    
    amc_table = Table(amc_data, colWidths=[2*inch, 4*inch])
    amc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#0F172A')),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E2E8F0')),
    ]))
    story.append(amc_table)
    story.append(Spacer(1, 30))
    
    footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, textColor=colors.HexColor('#94A3B8'))
    story.append(Paragraph("This document is auto-generated and valid as of the date mentioned above.", footer_style))
    story.append(Paragraph("For any discrepancies, please contact support.", footer_style))
    
    doc.build(story)
    buffer.seek(0)
    
    filename = f"warranty_report_{serial_number}_{get_ist_now().strftime('%Y%m%d')}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

# ==================== DEVICE MODEL CATALOG (AI-POWERED) ====================

@api_router.get("/device-models")
async def list_device_models(
    device_type: Optional[str] = None,
    brand: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    admin: dict = Depends(get_current_admin)
):
    """List device models from catalog"""
    query = {"is_deleted": {"$ne": True}}
    
    if device_type:
        query["device_type"] = device_type
    if brand:
        query["brand"] = {"$regex": f"^{brand}$", "$options": "i"}
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"brand": search_regex},
            {"model": search_regex},
            {"category": search_regex}
        ]
    
    models = await db.device_models.find(query, {"_id": 0}).limit(limit).to_list(limit)
    return models


@api_router.get("/device-models/{model_id}")
async def get_device_model(model_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific device model by ID"""
    model = await db.device_models.find_one(
        {"id": model_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not model:
        raise HTTPException(status_code=404, detail="Device model not found")
    return model


@api_router.post("/device-models/lookup")
async def lookup_device_model(
    request: AILookupRequest,
    force_refresh: bool = Query(default=False),
    admin: dict = Depends(get_current_admin)
):
    """
    AI-powered device model lookup.
    Fetches specifications and compatible consumables for a device.
    Results are cached for future use.
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await get_or_create_device_model(
        db=db,
        device_type=request.device_type,
        brand=request.brand,
        model=request.model,
        force_refresh=force_refresh
    )
    return result


@api_router.post("/device-models")
async def create_device_model(
    model_data: DeviceModelCreate,
    admin: dict = Depends(get_current_admin)
):
    """Manually create a device model entry"""
    # Check for existing
    existing = await db.device_models.find_one({
        "brand": {"$regex": f"^{model_data.brand}$", "$options": "i"},
        "model": {"$regex": f"^{model_data.model}$", "$options": "i"},
        "device_type": model_data.device_type,
        "is_deleted": {"$ne": True}
    })
    
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Device model {model_data.brand} {model_data.model} already exists"
        )
    
    device_model = DeviceModel(
        device_type=model_data.device_type,
        brand=model_data.brand,
        model=model_data.model,
        model_variants=model_data.model_variants,
        category=model_data.category,
        compatible_consumables=model_data.compatible_consumables,
        compatible_upgrades=model_data.compatible_upgrades,
        image_url=model_data.image_url,
        source="manual",
        is_verified=True
    )
    
    if model_data.specifications:
        device_model.specifications = model_data.specifications
    
    await db.device_models.insert_one(device_model.model_dump())
    
    return await db.device_models.find_one({"id": device_model.id}, {"_id": 0})


@api_router.put("/device-models/{model_id}")
async def update_device_model(
    model_id: str,
    updates: DeviceModelUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update a device model"""
    existing = await db.device_models.find_one(
        {"id": model_id, "is_deleted": {"$ne": True}}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Device model not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if update_data:
        update_data["updated_at"] = get_ist_isoformat()
        await db.device_models.update_one({"id": model_id}, {"$set": update_data})
    
    return await db.device_models.find_one({"id": model_id}, {"_id": 0})


@api_router.delete("/device-models/{model_id}")
async def delete_device_model(model_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a device model"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.device_models.update_one(
        {"id": model_id},
        {"$set": {"is_deleted": True}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Device model not found")
    return {"message": "Device model deleted"}


@api_router.post("/device-models/{model_id}/verify")
async def verify_device_model(model_id: str, admin: dict = Depends(get_current_admin)):
    """Mark a device model as admin-verified"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.device_models.update_one(
        {"id": model_id, "is_deleted": {"$ne": True}},
        {"$set": {"is_verified": True, "updated_at": get_ist_isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Device model not found")
    return {"message": "Device model verified"}


@api_router.get("/device-models/consumables/search")
async def search_compatible_consumables(
    device_type: Optional[str] = None,
    brand: Optional[str] = None,
    model: Optional[str] = None,
    consumable_type: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """
    Search for compatible consumables based on device info.
    Used when creating service records to show relevant parts.
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    if not brand and not model:
        raise HTTPException(status_code=400, detail="Brand or model is required")
    
    query = {"is_deleted": {"$ne": True}}
    if device_type:
        query["device_type"] = device_type
    if brand:
        query["brand"] = {"$regex": f"^{brand}$", "$options": "i"}
    if model:
        query["model"] = {"$regex": model, "$options": "i"}
    
    device_model = await db.device_models.find_one(query, {"_id": 0})
    
    if not device_model:
        return {
            "found": False,
            "consumables": [],
            "upgrades": [],
            "message": "No device model found. Try AI lookup first."
        }
    
    consumables = device_model.get("compatible_consumables", [])
    upgrades = device_model.get("compatible_upgrades", [])
    
    # Filter by consumable type if specified
    if consumable_type:
        consumables = [c for c in consumables if c.get("consumable_type", "").lower() == consumable_type.lower()]
        upgrades = [u for u in upgrades if u.get("consumable_type", "").lower() == consumable_type.lower()]
    
    return {
        "found": True,
        "device_model_id": device_model.get("id"),
        "device_info": f"{device_model.get('brand')} {device_model.get('model')}",
        "consumables": consumables,
        "upgrades": upgrades
    }


# ==================== OSTICKET WEBHOOK ====================

# Get webhook secret from environment (set this in osTicket as well)
OSTICKET_WEBHOOK_SECRET = os.environ.get('OSTICKET_WEBHOOK_SECRET', 'change-this-secret-key')


class OsTicketWebhookPayload(BaseModel):
    """Payload from osTicket webhook"""
    ticket_id: str  # osTicket ticket ID
    ticket_number: Optional[str] = None
    status: Optional[str] = None  # open, resolved, closed, etc.
    status_id: Optional[int] = None
    priority: Optional[str] = None
    subject: Optional[str] = None
    last_message: Optional[str] = None
    last_responder: Optional[str] = None
    updated_at: Optional[str] = None
    event_type: Optional[str] = None  # status_change, reply, note, close


@api_router.post("/webhooks/osticket")
async def osticket_webhook(
    payload: OsTicketWebhookPayload,
    secret: str = Query(..., description="Webhook secret for authentication")
):
    """
    Webhook endpoint for osTicket to sync ticket updates back to the portal.
    
    Configure in osTicket:
    1. Go to Admin Panel → Manage → API Keys
    2. Add a new webhook/API integration
    3. Set URL: https://your-domain.com/api/webhooks/osticket?secret=YOUR_SECRET
    4. Trigger on: status change, new reply, ticket closed
    """
    # Verify webhook secret
    if secret != OSTICKET_WEBHOOK_SECRET:
        logger.warning(f"osTicket webhook: Invalid secret received")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    logger.info(f"osTicket webhook received: ticket_id={payload.ticket_id}, event={payload.event_type}, status={payload.status}")
    
    # Find ticket in our system (V2) by source_reference
    ticket = await db.tickets_v2.find_one(
        {"source_reference": payload.ticket_id, "source": "osticket"},
        {"_id": 0}
    )
    
    # Also check quick service requests
    quick_request = None
    if not ticket:
        quick_request = await db.quick_service_requests.find_one(
            {"osticket_id": payload.ticket_id},
            {"_id": 0}
        )
    
    if not ticket and not quick_request:
        if payload.ticket_number:
            ticket = await db.tickets_v2.find_one(
                {"ticket_number": {"$regex": payload.ticket_number, "$options": "i"}},
                {"_id": 0}
            )
        
        if not ticket:
            logger.warning(f"osTicket webhook: Ticket not found for osticket_id={payload.ticket_id}")
            return {"success": False, "message": "Ticket not found in portal"}
    
    update_data = {
        "updated_at": get_ist_isoformat()
    }
    
    # Add the reply/message as a timeline entry if provided
    if payload.last_message and payload.last_responder:
        timeline_entry = {
            "id": str(uuid.uuid4()),
            "type": "comment",
            "description": payload.last_message,
            "user_name": payload.last_responder,
            "is_internal": False,
            "created_at": get_ist_isoformat()
        }
        
        if ticket:
            await db.tickets_v2.update_one(
                {"id": ticket["id"]},
                {
                    "$set": update_data,
                    "$push": {"timeline": timeline_entry}
                }
            )
        elif quick_request:
            await db.quick_service_requests.update_one(
                {"id": quick_request["id"]},
                {"$set": {**update_data, "last_response": payload.last_message}}
            )
    else:
        if ticket:
            await db.tickets_v2.update_one(
                {"id": ticket["id"]},
                {"$set": update_data}
            )
        elif quick_request:
            await db.quick_service_requests.update_one(
                {"id": quick_request["id"]},
                {"$set": update_data}
            )
    
    target = ticket or quick_request
    logger.info(f"osTicket webhook: Updated ticket {target.get('ticket_number', target.get('id'))} with status={new_status}")
    
    return {
        "success": True,
        "message": "Ticket updated successfully",
        "portal_ticket_id": target.get("id"),
        "new_status": new_status
    }


@api_router.get("/webhooks/osticket/test")
async def test_osticket_webhook():
    """Test endpoint to verify webhook is accessible"""
    return {
        "status": "ok",
        "message": "osTicket webhook endpoint is active",
        "webhook_url": "/api/webhooks/osticket?secret=YOUR_SECRET"
    }


# ==================== QR CODE & QUICK SERVICE REQUEST ====================

class QuickServiceRequest(BaseModel):
    """Quick service request without login"""
    name: str
    email: str
    phone: Optional[str] = None
    issue_category: str = "other"  # hardware, software, network, other
    description: str


@api_router.get("/device/{identifier}/qr")
async def generate_device_qr_code(identifier: str):
    """
    Generate a printable PDF with single QR code (1.5 inch x 1.5 inch).
    The QR code links to the public device info page.
    Includes Serial Number and Asset Tag below the QR code.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    
    # Find device by serial number or asset tag
    device = await db.devices.find_one(
        {"$and": [
            {"is_deleted": {"$ne": True}},
            {"$or": [
                {"serial_number": {"$regex": f"^{identifier}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{identifier}$", "$options": "i"}}
            ]}
        ]},
        {"_id": 0, "serial_number": 1, "asset_tag": 1, "brand": 1, "model": 1}
    )
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get frontend URL from environment or use default
    frontend_url = os.environ.get('FRONTEND_URL', '')
    if not frontend_url:
        cors_origins = os.environ.get('CORS_ORIGINS', '')
        if cors_origins and cors_origins != '*':
            frontend_url = cors_origins.split(',')[0].strip()
        else:
            frontend_url = "https://your-portal-url.com"
    
    # Create QR code URL pointing to public device page
    device_url = f"{frontend_url}/device/{device['serial_number']}"
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(device_url)
    qr.make(fit=True)
    
    # Create QR image at high resolution for PDF
    qr_img = qr.make_image(fill_color="black", back_color="white")
    qr_img = qr_img.resize((300, 300), Image.Resampling.LANCZOS)  # High res for PDF
    
    # Convert PIL image to bytes for ReportLab
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_reader = ImageReader(qr_buffer)
    
    # Create PDF
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    page_width, page_height = A4
    
    # QR size: 1.5 inch x 1.5 inch
    qr_size = 1.5 * inch
    label_height = 0.4 * inch  # Space for text below QR
    total_height = qr_size + label_height
    
    # Center the QR code on the page
    x = (page_width - qr_size) / 2
    y = (page_height - total_height) / 2 + label_height
    
    # Draw QR code
    c.drawImage(qr_reader, x, y, width=qr_size, height=qr_size)
    
    # Draw border around QR (for cutting guide)
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.5)
    margin = 5
    c.rect(x - margin, y - label_height - margin, qr_size + 2*margin, total_height + 2*margin)
    
    # Draw labels below QR
    text_x = page_width / 2
    
    # Serial Number (bold)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(text_x, y - 15, f"S/N: {device.get('serial_number', 'N/A')}")
    
    # Asset Tag (if exists)
    if device.get('asset_tag'):
        c.setFont("Helvetica", 9)
        c.drawCentredString(text_x, y - 28, f"Tag: {device['asset_tag']}")
    
    # Device info
    device_info = f"{device.get('brand', '')} {device.get('model', '')}"
    if device_info.strip():
        c.setFont("Helvetica", 8)
        c.setFillColorRGB(0.5, 0.5, 0.5)
        c.drawCentredString(text_x, y - 40, device_info[:40])
    
    c.save()
    pdf_buffer.seek(0)
    
    filename = f"QR_{device.get('serial_number', identifier)}.pdf"
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


class BulkQRRequest(BaseModel):
    """Request body for bulk QR code generation"""
    device_ids: Optional[List[str]] = None  # Specific device IDs
    company_id: Optional[str] = None  # All devices from a company
    site_id: Optional[str] = None  # All devices from a site


@api_router.post("/devices/bulk-qr-pdf")
async def generate_bulk_qr_pdf(
    request: BulkQRRequest,
    admin: dict = Depends(get_current_admin)
):
    """
    Generate a printable A4 PDF with multiple QR codes.
    Each QR code is 1.5 inch x 1.5 inch with Serial Number and Asset Tag.
    A4 paper fits 4 columns x 5 rows = 20 QR codes per page.
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    
    # Build query based on filters
    query = {"is_deleted": {"$ne": True}}
    
    if request.device_ids and len(request.device_ids) > 0:
        query["id"] = {"$in": request.device_ids}
    elif request.site_id:
        query["site_id"] = request.site_id
    elif request.company_id:
        query["company_id"] = request.company_id
    
    # Fetch devices
    devices = await db.devices.find(
        query,
        {"_id": 0, "id": 1, "serial_number": 1, "asset_tag": 1, "brand": 1, "model": 1}
    ).sort("serial_number", 1).to_list(500)
    
    if not devices:
        raise HTTPException(status_code=404, detail="No devices found matching criteria")
    
    # Get frontend URL for QR codes
    frontend_url = os.environ.get('FRONTEND_URL', '')
    if not frontend_url:
        cors_origins = os.environ.get('CORS_ORIGINS', '')
        if cors_origins and cors_origins != '*':
            frontend_url = cors_origins.split(',')[0].strip()
        else:
            frontend_url = "https://your-portal-url.com"
    
    # PDF settings - Fixed 1.5 inch QR codes
    page_width, page_height = A4  # 595 x 842 points (8.27 x 11.69 inches)
    
    # QR code size: 1.5 inch x 1.5 inch
    qr_size = 1.5 * inch  # 108 points
    label_height = 0.35 * inch  # Space for text below QR
    cell_padding = 0.15 * inch  # Padding between cells
    
    cell_width = qr_size + cell_padding
    cell_height = qr_size + label_height + cell_padding
    
    # Calculate grid: how many fit on A4
    margin_x = (page_width - (4 * cell_width)) / 2  # Center 4 columns
    margin_y = 0.5 * inch  # Top/bottom margin
    
    columns = 4  # 4 columns of 1.5 inch QR codes fit on A4 width
    rows_per_page = 5  # 5 rows fit on A4 height
    
    # Create PDF
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    current_row = 0
    current_col = 0
    
    for device in devices:
        # Calculate position
        x = margin_x + (current_col * cell_width)
        y = page_height - margin_y - ((current_row + 1) * cell_height)
        
        # Generate QR code for this device
        device_url = f"{frontend_url}/device/{device['serial_number']}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=10,
            border=1,
        )
        qr.add_data(device_url)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img = qr_img.resize((300, 300), Image.Resampling.LANCZOS)  # High res for print
        
        # Convert PIL image to ReportLab ImageReader
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_reader = ImageReader(qr_buffer)
        
        # Draw QR code (1.5 inch x 1.5 inch)
        qr_x = x + (cell_width - qr_size) / 2
        qr_y = y + label_height
        c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)
        
        # Draw labels below QR
        serial = device.get('serial_number', 'N/A')
        asset_tag = device.get('asset_tag', '')
        text_x = x + cell_width / 2
        
        # Serial Number (bold)
        c.setFont("Helvetica-Bold", 7)
        c.setFillColorRGB(0, 0, 0)
        serial_display = serial if len(serial) <= 20 else serial[:17] + "..."
        c.drawCentredString(text_x, y + label_height - 12, f"S/N: {serial_display}")
        
        # Asset Tag (if exists)
        if asset_tag:
            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            tag_display = asset_tag if len(asset_tag) <= 20 else asset_tag[:17] + "..."
            c.drawCentredString(text_x, y + label_height - 22, f"Tag: {tag_display}")
        
        # Draw cutting guide border
        c.setStrokeColorRGB(0.85, 0.85, 0.85)
        c.setLineWidth(0.5)
        c.rect(x + 2, y + 2, cell_width - 4, cell_height - 4)
        
        # Reset fill color
        c.setFillColorRGB(0, 0, 0)
        
        # Move to next cell
        current_col += 1
        if current_col >= columns:
            current_col = 0
            current_row += 1
            
            # Check if we need a new page
            if current_row >= rows_per_page:
                c.showPage()
                current_row = 0
    
    # Footer with generation info
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(margin_x, 12, f"Generated: {get_ist_now().strftime('%Y-%m-%d %H:%M')} | {len(devices)} QR codes | Size: 1.5\" x 1.5\"")
    
    c.save()
    buffer.seek(0)
    
    # Generate filename
    filename_parts = ["QR_Codes"]
    if request.company_id:
        company = await db.companies.find_one(scope_query({"id": request.company_id}, org_id), {"_id": 0, "name": 1})
        if company:
            filename_parts.append(company["name"].replace(" ", "_")[:20])
    if request.site_id:
        site = await db.sites.find_one(scope_query({"id": request.site_id}, org_id), {"_id": 0, "name": 1})
        if site:
            filename_parts.append(site["name"].replace(" ", "_")[:20])
    
    filename_parts.append(get_ist_now().strftime('%Y%m%d'))
    filename = "_".join(filename_parts) + ".pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@api_router.get("/device/{identifier}/info")
async def get_public_device_info(identifier: str):
    """
    Get public device information including warranty status and service history.
    Used by the QR code scan page.
    """
    # Find device by serial number or asset tag
    device = await db.devices.find_one(
        {"$and": [
            {"is_deleted": {"$ne": True}},
            {"$or": [
                {"serial_number": {"$regex": f"^{identifier}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{identifier}$", "$options": "i"}}
            ]}
        ]},
        {"_id": 0}
    )
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get company info
    company = await db.companies.find_one(
        {"id": device["company_id"], "is_deleted": {"$ne": True}}, 
        {"_id": 0, "name": 1, "id": 1}
    )
    
    # Get assigned user
    assigned_user = None
    if device.get("assigned_user_id"):
        user = await db.users.find_one(
            {"id": device["assigned_user_id"], "is_deleted": {"$ne": True}}, 
            {"_id": 0, "name": 1}
        )
        assigned_user = user.get("name") if user else None
    
    # Get site info
    site_info = None
    if device.get("site_id"):
        site = await db.sites.find_one(
            {"id": device["site_id"], "is_deleted": {"$ne": True}},
            {"_id": 0, "name": 1, "address": 1}
        )
        if site:
            site_info = {"name": site.get("name"), "address": site.get("address")}
    
    # Check warranty status
    device_warranty_active = is_warranty_active(device.get("warranty_end_date", "")) if device.get("warranty_end_date") else False
    
    # Check AMC
    amc_info = None
    active_amc = await db.amc_device_assignments.find_one({
        "device_id": device["id"],
        "status": "active"
    }, {"_id": 0})
    
    if active_amc and is_warranty_active(active_amc.get("coverage_end", "")):
        contract = await db.amc_contracts.find_one(
            {"id": active_amc["amc_contract_id"], "is_deleted": {"$ne": True}},
            {"_id": 0, "name": 1, "amc_type": 1}
        )
        if contract:
            amc_info = {
                "name": contract.get("name"),
                "type": contract.get("amc_type"),
                "coverage_end": active_amc.get("coverage_end"),
                "active": True
            }
    
    # Get recent service history (last 5)
    service_history = await db.service_history.find(
        {"device_id": device["id"]},
        {"_id": 0, "service_date": 1, "service_type": 1, "action_taken": 1, "technician_name": 1}
    ).sort("service_date", -1).limit(5).to_list(5)
    
    # Get parts
    parts = await db.parts.find(
        {"device_id": device["id"], "is_deleted": {"$ne": True}},
        {"_id": 0, "part_name": 1, "warranty_expiry_date": 1}
    ).to_list(20)
    
    for part in parts:
        part["warranty_active"] = is_warranty_active(part.get("warranty_expiry_date", ""))
    
    return {
        "device": {
            "id": device.get("id"),
            "device_type": device.get("device_type"),
            "brand": device.get("brand"),
            "model": device.get("model"),
            "serial_number": device.get("serial_number"),
            "asset_tag": device.get("asset_tag"),
            "purchase_date": device.get("purchase_date"),
            "warranty_end_date": device.get("warranty_end_date"),
            "warranty_active": device_warranty_active or (amc_info is not None),
            "condition": device.get("condition"),
            "status": device.get("status"),
            "location": device.get("location")
        },
        "company": {
            "id": company.get("id") if company else None,
            "name": company.get("name") if company else "Unknown"
        },
        "assigned_user": assigned_user,
        "site": site_info,
        "amc": amc_info,
        "service_history": service_history,
        "parts": parts,
        "service_count": await db.service_history.count_documents({"device_id": device["id"]})
    }


@api_router.post("/device/{identifier}/quick-request")
async def create_quick_service_request(identifier: str, request: QuickServiceRequest):
    """
    Create a quick service request without login.
    This is for urgent issues when users scan QR code and need help immediately.
    """
    # Find device
    device = await db.devices.find_one(
        {"$and": [
            {"is_deleted": {"$ne": True}},
            {"$or": [
                {"serial_number": {"$regex": f"^{identifier}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{identifier}$", "$options": "i"}}
            ]}
        ]},
        {"_id": 0}
    )
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get company info
    company = await db.companies.find_one(
        {"id": device["company_id"], "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "notification_email": 1, "contact_email": 1}
    )
    company_name = company.get("name") if company else "Unknown"
    
    # Create ticket number
    ticket_number = f"QSR-{get_ist_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    # Create the quick service request record
    quick_request = {
        "id": str(uuid.uuid4()),
        "ticket_number": ticket_number,
        "device_id": device["id"],
        "company_id": device["company_id"],
        "requester_name": request.name,
        "requester_email": request.email,
        "requester_phone": request.phone,
        "issue_category": request.issue_category,
        "description": request.description,
        "status": "open",
        "source": "qr_scan",
        "created_at": get_ist_isoformat(),
        "osticket_id": None
    }
    
    # Store in database
    await db.quick_service_requests.insert_one(quick_request)
    
    # Create osTicket if configured
    osticket_result = await create_osticket(
        email=request.email,
        name=request.name,
        subject=f"[Quick Request] {request.issue_category.title()} Issue - {device.get('brand')} {device.get('model')}",
        message=f"""
        <h3>Quick Service Request via QR Scan</h3>
        <p><strong>Ticket:</strong> {ticket_number}</p>
        
        <h4>Requester Details</h4>
        <ul>
            <li><strong>Name:</strong> {request.name}</li>
            <li><strong>Email:</strong> {request.email}</li>
            <li><strong>Phone:</strong> {request.phone or 'Not provided'}</li>
        </ul>
        
        <h4>Device Details</h4>
        <ul>
            <li><strong>Company:</strong> {company_name}</li>
            <li><strong>Device:</strong> {device.get('brand')} {device.get('model')}</li>
            <li><strong>Serial Number:</strong> {device.get('serial_number')}</li>
            <li><strong>Asset Tag:</strong> {device.get('asset_tag') or 'N/A'}</li>
            <li><strong>Location:</strong> {device.get('location') or 'Not specified'}</li>
        </ul>
        
        <h4>Issue Details</h4>
        <ul>
            <li><strong>Category:</strong> {request.issue_category.title()}</li>
            <li><strong>Description:</strong><br/>{request.description}</li>
        </ul>
        
        <p><em>This request was submitted via QR code scan (no login required).</em></p>
        """,
        phone=request.phone or ""
    )
    
    if osticket_result.get("ticket_id"):
        await db.quick_service_requests.update_one(
            {"id": quick_request["id"]},
            {"$set": {"osticket_id": osticket_result["ticket_id"]}}
        )
    
    return {
        "success": True,
        "ticket_number": ticket_number,
        "message": "Your service request has been submitted successfully. Our team will contact you shortly.",
        "osticket_id": osticket_result.get("ticket_id"),
        "device": {
            "brand": device.get("brand"),
            "model": device.get("model"),
            "serial_number": device.get("serial_number")
        }
    }


# ==================== AUTH ENDPOINTS ====================

@api_router.post("/auth/login", response_model=Token)
@limiter.limit(RATE_LIMITS["login"])
async def admin_login(request: Request, login: AdminLogin):
    """
    Admin login with tenant-aware authentication.
    
    If tenant context is present (from subdomain/header), validates that user
    belongs to that tenant. This enforces subdomain-based access control.
    """
    # Get tenant context from middleware
    tenant = getattr(request.state, "tenant", None)
    tenant_id = getattr(request.state, "tenant_id", None)
    
    # Find admin by email
    admin = await db.admins.find_one({"email": login.email}, {"_id": 0})
    if not admin or not verify_password(login.password, admin.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Check if admin has an organization member entry
    org_member_query = {"email": login.email, "is_active": True, "is_deleted": {"$ne": True}}
    
    # If tenant context exists, enforce tenant match
    if tenant_id:
        org_member_query["organization_id"] = tenant_id
    
    org_member = await db.organization_members.find_one(org_member_query, {"_id": 0})
    
    # Tenant-aware validation
    if tenant_id:
        # Tenant context exists - user MUST belong to this tenant
        if not org_member:
            # User exists but not in this tenant - generic error (no information leakage)
            logger.warning(f"Login attempt for user not in tenant: email={login.email}, tenant={tenant.get('slug') if tenant else 'unknown'}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if tenant is accessible
        if tenant and tenant.get("status") in ["suspended", "churned"]:
            raise HTTPException(
                status_code=403, 
                detail=f"This workspace is currently {tenant.get('status')}. Please contact support."
            )
    
    token_data = {"sub": admin["email"]}
    
    if org_member:
        # Include organization context in token
        token_data["organization_id"] = org_member.get("organization_id")
        token_data["org_member_id"] = org_member.get("id")
        token_data["type"] = "org_member"
        token_data["role"] = org_member.get("role", "member")
    
    access_token = create_access_token(data=token_data)
    
    # Include tenant context in response for frontend
    response = {"access_token": access_token, "token_type": "bearer"}
    
    if tenant:
        response["tenant"] = {
            "id": tenant.get("id"),
            "name": tenant.get("name"),
            "slug": tenant.get("slug")
        }
    
    return response

@api_router.get("/auth/me")
async def get_current_admin_info(request: Request, admin: dict = Depends(get_current_admin)):
    """Get current admin info with tenant context"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Get tenant from request state (set by middleware)
    request_tenant = getattr(request.state, "tenant", None)
    
    # Check for organization context
    org_member = await db.organization_members.find_one(
        {"email": admin.get("email"), "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    )
    
    organization = None
    if org_member:
        organization = await db.organizations.find_one(
            {"id": org_member.get("organization_id"), "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
    
    response = {
        "id": admin.get("id"),
        "email": admin.get("email"),
        "name": admin.get("name"),
        "role": admin.get("role"),
        "organization_id": org_member.get("organization_id") if org_member else None,
        "organization_name": organization.get("name") if organization else None,
        "org_role": org_member.get("role") if org_member else None
    }
    
    # Include branding if organization exists
    if organization:
        branding = organization.get("branding", {})
        response["branding"] = {
            "logo_url": branding.get("logo_url"),
            "logo_base64": branding.get("logo_base64"),
            "accent_color": branding.get("accent_color", "#0F62FE"),
            "company_name": branding.get("company_name") or organization.get("name")
        }
        
        # Include feature flags
        default_flags = {
            "watchtower": False,
            "white_labeling": False,
            "api_access": False,
            "advanced_reports": False,
            "sla_management": False,
            "custom_domains": False,
            "email_integration": False,
            "knowledge_base": False,
            "staff_module": True
        }
        current_flags = organization.get("feature_flags", {})
        response["feature_flags"] = {**default_flags, **current_flags}
    
    return response


@api_router.get("/admin/feature-flags")
async def get_tenant_feature_flags(admin: dict = Depends(get_current_admin)):
    """Get feature flags for the current tenant organization"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    organization = await db.organizations.find_one(
        {"id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if not organization:
        raise HTTPException(status_code=404, detail="Organization not found")
    
    # Default flags
    default_flags = {
        "watchtower": False,
        "white_labeling": False,
        "api_access": False,
        "advanced_reports": False,
        "sla_management": False,
        "custom_domains": False,
        "email_integration": False,
        "knowledge_base": False,
        "staff_module": True
    }
    
    current_flags = organization.get("feature_flags", {})
    merged_flags = {**default_flags, **current_flags}
    
    return {
        "organization_id": org_id,
        "organization_name": organization.get("name"),
        "feature_flags": merged_flags
    }


@api_router.post("/auth/setup")
@limiter.limit(RATE_LIMITS["register"])
async def setup_first_admin(request: Request, admin_data: AdminCreate):
    existing = await db.admins.find_one({}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Admin already exists. Use login.")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(admin_data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    admin = AdminUser(
        email=admin_data.email,
        name=admin_data.name,
        password_hash=get_password_hash(admin_data.password)
    )
    await db.admins.insert_one(admin.model_dump())
    
    # Seed default masters
    await seed_default_masters()
    
    return {"message": "Admin created successfully", "email": admin.email}


@api_router.get("/admin/staff")
async def list_admin_staff(admin: dict = Depends(get_current_admin)):
    """List all admin panel users/staff for assignment"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    staff = await db.admins.find(scope_query({"is_deleted": {"$ne": True}}, org_id), {"_id": 0, "password": 0}).to_list(100)
    # Add label for SmartSelect compatibility
    for s in staff:
        s["label"] = s.get("name", s.get("email", "Unknown"))
    return staff


# ==================== MASTER DATA ENDPOINTS ====================

@api_router.get("/admin/masters")
async def list_masters(master_type: Optional[str] = None, include_inactive: bool = False, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {}
    if master_type:
        query["type"] = master_type
    if not include_inactive:
        query["is_active"] = True
    query = scope_query(query, org_id)
    masters = await db.masters.find(query, {"_id": 0}).sort([("type", 1), ("sort_order", 1)]).to_list(1000)
    return masters

@api_router.post("/admin/masters")
async def create_master(item: MasterItemCreate, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Check for duplicate
    existing = await db.masters.find_one(scope_query({"type": item.type, "name": item.name}, org_id), {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail=f"Master item '{item.name}' already exists for type '{item.type}'")
    
    master = MasterItem(**item.model_dump())
    master_dict = master.model_dump()
    master_dict["organization_id"] = org_id
    await db.masters.insert_one(master_dict)
    await log_audit("master", master.id, "create", {"data": item.model_dump()}, admin)
    return master.model_dump()

@api_router.put("/admin/masters/{master_id}")
async def update_master(master_id: str, updates: MasterItemUpdate, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.masters.find_one(scope_query({"id": master_id}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Master item not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # Track changes for audit
    changes = {}
    for k, v in update_data.items():
        if existing.get(k) != v:
            changes[k] = {"old": existing.get(k), "new": v}
    
    result = await db.masters.update_one(scope_query({"id": master_id}, org_id), {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Master item not found")
    
    await log_audit("master", master_id, "update", changes, admin)
    return await db.masters.find_one({"id": master_id}, {"_id": 0})

@api_router.delete("/admin/masters/{master_id}")
async def disable_master(master_id: str, admin: dict = Depends(get_current_admin)):
    """Disable master (soft delete - preserve history)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.masters.update_one(scope_query({"id": master_id}, org_id), {"$set": {"is_active": False}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Master item not found")
    
    await log_audit("master", master_id, "disable", {"is_active": {"old": True, "new": False}}, admin)
    return {"message": "Master item disabled"}

@api_router.post("/admin/masters/seed")
async def seed_masters(admin: dict = Depends(get_current_admin)):
    """Force re-seed default masters"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    await seed_default_masters()
    return {"message": "Default masters seeded"}

@api_router.post("/admin/masters/quick-create")
async def quick_create_master(item: MasterItemCreate, admin: dict = Depends(get_current_admin)):
    """Quick create master item (for inline creation from dropdowns)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Check for duplicate
    existing = await db.masters.find_one(scope_query({"type": item.type, "name": item.name}, org_id), {"_id": 0})
    if existing:
        # Return existing item instead of error (idempotent)
        return existing
    
    # Get next sort order
    last = await db.masters.find_one(scope_query({"type": item.type}, org_id), {"_id": 0}, sort=[("sort_order", -1)])
    next_order = (last.get("sort_order", 0) + 1) if last else 1
    
    master_data = item.model_dump()
    master_data["sort_order"] = next_order
    master = MasterItem(**master_data)
    m_dict = master.model_dump()
    m_dict["organization_id"] = org_id
    await db.masters.insert_one(m_dict)
    await log_audit("master", master.id, "quick_create", {"data": item.model_dump()}, admin)
    
    result = {k: v for k, v in m_dict.items() if k != "_id"}
    # Add label for SmartSelect compatibility
    result.get("label", result.get("name", "Unknown")) or result.get("name", "Unknown"); result["label"] = result.get("name", "Unknown")
    return result

# ==================== ADMIN ENDPOINTS - COMPANIES ====================

@api_router.get("/admin/companies")
async def list_companies(
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List companies with optional search support"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"contact_name": search_regex},
            {"contact_email": search_regex},
            {"gst_number": search_regex}
        ]
    
    skip = (page - 1) * limit
    companies = await db.companies.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Add label field for SmartSelect compatibility
    for c in companies:
        c.get("label", c.get("name", "Unknown")) or c.get("name", "Unknown"); c["label"] = c.get("name", "Unknown")
    
    return companies

@api_router.post("/admin/companies")
async def create_company(company_data: CompanyCreate, admin: dict = Depends(get_current_admin)):
    # Filter out None values to allow Company model defaults to work
    company_dict = {k: v for k, v in company_data.model_dump().items() if v is not None}
    
    # Add organization_id for multi-tenancy
    org_id = await get_admin_org_id(admin.get("email", ""))
    if org_id:
        company_dict["organization_id"] = org_id
    
    company = Company(**company_dict)
    await db.companies.insert_one(company.model_dump())
    await log_audit("company", company.id, "create", {"data": company_data.model_dump()}, admin)
    result = company.model_dump()
    result.get("label", result.get("name", "Unknown")) or result.get("name", "Unknown"); result["label"] = result.get("name", "Unknown")
    return result

@api_router.post("/admin/companies/quick-create")
async def quick_create_company(company_data: CompanyCreate, admin: dict = Depends(get_current_admin)):
    """Quick create company (for inline creation from dropdowns)"""
    # Apply tenant scoping to duplicate check
    org_id = await get_admin_org_id(admin.get("email", ""))
    check_query = {"name": {"$regex": f"^{company_data.name}$", "$options": "i"}, "is_deleted": {"$ne": True}}
    check_query = scope_query(check_query, org_id)
    
    existing = await db.companies.find_one(check_query, {"_id": 0})
    if existing:
        # Return existing instead of error (idempotent)
        existing.get("label", existing.get("name", "Unknown")) or existing.get("name", "Unknown"); existing["label"] = existing.get("name", "Unknown")
        return existing
    
    # Filter out None values to allow Company model defaults to work
    company_dict = {k: v for k, v in company_data.model_dump().items() if v is not None}
    
    # Add organization_id for multi-tenancy
    if org_id:
        company_dict["organization_id"] = org_id
    
    company = Company(**company_dict)
    await db.companies.insert_one(company.model_dump())
    await log_audit("company", company.id, "quick_create", {"data": company_data.model_dump()}, admin)
    
    result = company.model_dump()
    result.get("label", result.get("name", "Unknown")) or result.get("name", "Unknown"); result["label"] = result.get("name", "Unknown")
    return result

@api_router.get("/admin/companies/{company_id}")
async def get_company(company_id: str, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": company_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    company = await db.companies.find_one(query, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@api_router.put("/admin/companies/{company_id}")
async def update_company(company_id: str, updates: CompanyUpdate, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": company_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    existing = await db.companies.find_one(query, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.companies.update_one(query, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    await log_audit("company", company_id, "update", changes, admin)
    return await db.companies.find_one({"id": company_id}, {"_id": 0})

@api_router.delete("/admin/companies/{company_id}")
async def delete_company(company_id: str, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": company_id}
    query = scope_query(query, org_id)
    
    result = await db.companies.update_one(query, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Soft delete related users (also scoped)
    user_query = {"company_id": company_id}
    user_query = scope_query(user_query, org_id)
    await db.users.update_many(user_query, {"$set": {"is_deleted": True}})
    await log_audit("company", company_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Company archived"}


# ==================== COMPANY DOMAIN MANAGEMENT ====================

@api_router.get("/admin/companies/{company_id}/domains")
async def get_company_domains(company_id: str, admin: dict = Depends(get_current_admin)):
    """Get all email domains for a specific company"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    company = await db.companies.find_one(
        {"id": company_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "email_domains": 1}
    )
    
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return company.get("email_domains", [])


@api_router.post("/admin/companies/{company_id}/domains")
async def add_company_domain(company_id: str, data: dict, admin: dict = Depends(get_current_admin)):
    """Add an email domain to a company for ticket routing"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    domain = data.get("domain", "").lower().strip()
    
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")
    
    # Validate domain format
    import re
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*\.[a-zA-Z]{2,}$', domain):
        raise HTTPException(status_code=400, detail="Invalid domain format")
    
    # Check if company exists
    company = await db.companies.find_one(scope_query({"id": company_id, "is_deleted": {"$ne": True}}, org_id))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if domain is already assigned to another company
    existing = await db.companies.find_one({
        "id": {"$ne": company_id},
        "email_domains": domain,
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(
            status_code=400, 
            detail=f"Domain '{domain}' is already assigned to {existing.get('name')}"
        )
    
    # Add domain to company
    current_domains = company.get("email_domains", [])
    if domain in current_domains:
        raise HTTPException(status_code=400, detail="Domain already exists for this company")
    
    await db.companies.update_one(
        {"id": company_id},
        {"$addToSet": {"email_domains": domain}}
    )
    
    await log_audit("company", company_id, "add_domain", {"domain": domain}, admin)
    return {"message": "Domain added", "domain": domain}


@api_router.delete("/admin/companies/{company_id}/domains/{domain}")
async def remove_company_domain(company_id: str, domain: str, admin: dict = Depends(get_current_admin)):
    """Remove an email domain from a company"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    company = await db.companies.find_one(scope_query({"id": company_id, "is_deleted": {"$ne": True}}, org_id))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    domain = domain.lower()
    
    await db.companies.update_one(
        {"id": company_id},
        {"$pull": {"email_domains": domain}}
    )
    
    await log_audit("company", company_id, "remove_domain", {"domain": domain}, admin)
    return {"message": "Domain removed"}


@api_router.get("/admin/company-domains")
async def list_all_company_domains(admin: dict = Depends(get_current_admin)):
    """List all companies with their email domains"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    companies = await db.companies.find(
        scope_query({"is_deleted": {"$ne": True}}, org_id),
        {"_id": 0, "id": 1, "name": 1, "email_domains": 1, "contact_email": 1}
    ).to_list(500)
    
    # Add domain count
    for company in companies:
        company["domain_count"] = len(company.get("email_domains", []))
    
    return companies


# ==================== BULK IMPORT ENDPOINTS ====================

@api_router.post("/admin/bulk-import/companies")
async def bulk_import_companies(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import companies from CSV data"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            # Check required fields
            if not record.get("name"):
                errors.append({"row": idx + 2, "message": "Company name is required"})
                continue
            
            # Check for duplicate company code (field is 'code' in Company model)
            company_code = record.get("company_code") or record.get("code")
            if company_code:
                existing = await db.companies.find_one({
                    "code": company_code,
                    "is_deleted": {"$ne": True}
                })
                if existing:
                    errors.append({"row": idx + 2, "message": f"Company code {company_code} already exists"})
                    continue
            
            company = Company(
                name=record.get("name"),
                code=company_code or f"C{str(uuid.uuid4())[:6].upper()}",
                industry=record.get("industry"),
                contact_name=record.get("contact_name"),
                contact_email=record.get("contact_email"),
                contact_phone=record.get("contact_phone"),
                address=record.get("address"),
                city=record.get("city"),
                state=record.get("state"),
                country=record.get("country", "India"),
                pincode=record.get("pincode"),
                gst_number=record.get("gst_number"),
                notes=record.get("notes"),
                status="active"
            )
            
            company_ins_dict["organization_id"] = org_id
            company_ins_dict = company.model_dump()
            await db.companies.insert_one(company_ins_dict)
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}

@api_router.post("/admin/bulk-import/sites")
async def bulk_import_sites(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import sites from CSV data"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    # Get company mapping by code and name
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    company_by_code = {c.get("code", "").upper(): c["id"] for c in companies if c.get("code")}
    company_by_name = {c["name"].lower(): c["id"] for c in companies}
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            if not record.get("name"):
                errors.append({"row": idx + 2, "message": "Site name is required"})
                continue
            
            # Find company by code or name
            company_id = None
            if record.get("company_code"):
                company_id = company_by_code.get(record["company_code"].upper())
            if not company_id and record.get("company_name"):
                company_id = company_by_name.get(record["company_name"].lower())
            
            if not company_id:
                errors.append({"row": idx + 2, "message": "Company not found"})
                continue
            
            site = Site(
                company_id=company_id,
                name=record.get("name"),
                site_code=record.get("site_code"),
                address=record.get("address"),
                city=record.get("city"),
                state=record.get("state"),
                pincode=record.get("pincode"),
                country=record.get("country", "India"),
                contact_person=record.get("contact_person"),
                contact_phone=record.get("contact_phone"),
                contact_email=record.get("contact_email"),
                notes=record.get("notes"),
                status="active"
            )
            
            site_ins_dict["organization_id"] = org_id
            site_ins_dict = site.model_dump()
            await db.sites.insert_one(site_ins_dict)
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}

@api_router.post("/admin/bulk-import/devices")
async def bulk_import_devices(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import devices from CSV data"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    # Get lookups
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    company_by_code = {c.get("code", "").upper(): c["id"] for c in companies if c.get("code")}
    company_by_name = {c["name"].lower(): c["id"] for c in companies}
    
    # Get employees for lookup
    employees = await db.company_employees.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(10000)
    employee_by_code = {}
    employee_by_email = {}
    for emp in employees:
        if emp.get("employee_code"):
            key = f"{emp['company_id']}_{emp['employee_code'].upper()}"
            employee_by_code[key] = emp["id"]
        if emp.get("email"):
            key = f"{emp['company_id']}_{emp['email'].lower()}"
            employee_by_email[key] = emp["id"]
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            # Required fields
            if not record.get("serial_number"):
                errors.append({"row": idx + 2, "message": "Serial number is required"})
                continue
            if not record.get("brand"):
                errors.append({"row": idx + 2, "message": "Brand is required"})
                continue
            if not record.get("model"):
                errors.append({"row": idx + 2, "message": "Model is required"})
                continue
            
            # Find company
            company_id = None
            if record.get("company_code"):
                company_id = company_by_code.get(record["company_code"].upper())
            if not company_id and record.get("company_name"):
                company_id = company_by_name.get(record["company_name"].lower())
            
            if not company_id:
                errors.append({"row": idx + 2, "message": "Company not found"})
                continue
            
            # Find employee (device user)
            assigned_employee_id = None
            if record.get("employee_code"):
                key = f"{company_id}_{record['employee_code'].upper()}"
                assigned_employee_id = employee_by_code.get(key)
            if not assigned_employee_id and record.get("employee_email"):
                key = f"{company_id}_{record['employee_email'].lower()}"
                assigned_employee_id = employee_by_email.get(key)
            
            # Check for duplicate serial number
            existing = await db.devices.find_one({
                "serial_number": record["serial_number"],
                "is_deleted": {"$ne": True}
            })
            if existing:
                errors.append({"row": idx + 2, "message": f"Serial number {record['serial_number']} already exists"})
                continue
            
            device = Device(
                company_id=company_id,
                assigned_employee_id=assigned_employee_id,
                device_type=record.get("device_type", "Laptop"),
                brand=record.get("brand"),
                model=record.get("model"),
                serial_number=record.get("serial_number"),
                asset_tag=record.get("asset_tag"),
                purchase_date=record.get("purchase_date", get_ist_isoformat().split("T")[0]),
                purchase_cost=float(record["purchase_cost"]) if record.get("purchase_cost") else None,
                vendor=record.get("vendor"),
                warranty_end_date=record.get("warranty_end_date"),
                location=record.get("location"),
                condition=record.get("condition", "good"),
                status=record.get("status", "active"),
                configuration=record.get("configuration"),
                notes=record.get("notes")
            )
            
            device_ins_dict["organization_id"] = org_id
            device_ins_dict = device.model_dump()
            await db.devices.insert_one(device_ins_dict)
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}

@api_router.post("/admin/bulk-import/supply-products")
async def bulk_import_supply_products(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import supply products from CSV data"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    # Get category mapping
    categories = await db.supply_categories.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    category_by_name = {c["name"].lower(): c["id"] for c in categories}
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            if not record.get("name"):
                errors.append({"row": idx + 2, "message": "Product name is required"})
                continue
            
            # Find category
            category_id = None
            if record.get("category"):
                category_id = category_by_name.get(record["category"].lower())
            
            if not category_id:
                # Create category if it doesn't exist
                if record.get("category"):
                    new_cat = SupplyCategory(name=record["category"])
                    new_cat_ins_dict["organization_id"] = org_id
                    new_cat_ins_dict = new_cat.model_dump()
                    await db.supply_categories.insert_one(new_cat_ins_dict)
                    category_id = new_cat.id
                    category_by_name[record["category"].lower()] = category_id
                else:
                    errors.append({"row": idx + 2, "message": "Category is required"})
                    continue
            
            # Parse price if provided
            price = None
            if record.get("price"):
                try:
                    price = float(str(record["price"]).replace(",", "").replace("₹", "").strip())
                except (ValueError, TypeError):
                    pass
            
            product = SupplyProduct(
                category_id=category_id,
                name=record.get("name"),
                description=record.get("description"),
                unit=record.get("unit", "piece"),
                price=price,
                sku=record.get("sku"),
                internal_notes=record.get("internal_notes")
            )
            
            product_ins_dict["organization_id"] = org_id
            product_ins_dict = product.model_dump()
            await db.supply_products.insert_one(product_ins_dict)
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}

@api_router.get("/admin/companies/{company_id}/overview")
async def get_company_overview(company_id: str, admin: dict = Depends(get_current_admin)):
    """Get comprehensive company 360° view with all related data"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Get company details
    company = await db.companies.find_one(scope_query({"id": company_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Get all related data in parallel
    devices_cursor = db.devices.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    devices = await devices_cursor.to_list(500)
    
    # Enrich devices with warranty status
    for device in devices:
        device["warranty_active"] = is_warranty_active(device.get("warranty_end_date", ""))
        # Check AMC status
        amc_assignment = await db.amc_device_assignments.find_one({
            "device_id": device["id"],
            "status": "active"
        }, {"_id": 0})
        if amc_assignment and is_warranty_active(amc_assignment.get("coverage_end", "")):
            device["amc_status"] = "active"
            device["amc_coverage_end"] = amc_assignment.get("coverage_end")
        else:
            device["amc_status"] = "none"
    
    # Get sites
    sites_cursor = db.sites.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    sites = await sites_cursor.to_list(100)
    
    # Get users/contacts
    users_cursor = db.users.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    users = await users_cursor.to_list(500)
    
    # Get deployments
    deployments_cursor = db.deployments.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    deployments = await deployments_cursor.to_list(100)
    for dep in deployments:
        site = await db.sites.find_one({"id": dep.get("site_id")}, {"_id": 0, "name": 1})
        dep["site_name"] = site.get("name") if site else "Unknown"
        dep["items_count"] = len(dep.get("items", []))
    
    # Get licenses
    licenses_cursor = db.licenses.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    licenses = await licenses_cursor.to_list(100)
    for lic in licenses:
        lic["is_expired"] = not is_warranty_active(lic.get("end_date", ""))
    
    # Get AMC contracts
    amc_cursor = db.amc_contracts.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    amc_contracts = await amc_cursor.to_list(50)
    for amc in amc_contracts:
        amc["is_active"] = is_warranty_active(amc.get("end_date", ""))
        # Count devices covered
        device_count = await db.amc_device_assignments.count_documents({
            "amc_contract_id": amc["id"],
            "status": "active"
        })
        amc["devices_covered"] = device_count
    
    # Get service history
    # First get all device IDs for this company
    device_ids = [d["id"] for d in devices]
    services = []
    if device_ids:
        services_cursor = db.service_history.find({
            "device_id": {"$in": device_ids},
            "is_deleted": {"$ne": True}
        }, {"_id": 0}).sort("service_date", -1).limit(100)
        services = await services_cursor.to_list(100)
        for svc in services:
            device = next((d for d in devices if d["id"] == svc.get("device_id")), None)
            if device:
                svc["device_info"] = f"{device.get('brand', '')} {device.get('model', '')} ({device.get('serial_number', '')})"
    
    # Calculate summary stats
    summary = {
        "total_devices": len(devices),
        "active_warranties": sum(1 for d in devices if d.get("warranty_active")),
        "active_amc_devices": sum(1 for d in devices if d.get("amc_status") == "active"),
        "total_sites": len(sites),
        "total_users": len(users),
        "total_deployments": len(deployments),
        "total_licenses": len(licenses),
        "active_licenses": sum(1 for l in licenses if not l.get("is_expired")),
        "total_amc_contracts": len(amc_contracts),
        "active_amc_contracts": sum(1 for a in amc_contracts if a.get("is_active")),
        "total_service_records": len(services)
    }
    
    return {
        "company": company,
        "summary": summary,
        "devices": devices,
        "sites": sites,
        "users": users,
        "deployments": deployments,
        "licenses": licenses,
        "amc_contracts": amc_contracts,
        "services": services
    }

# --- Admin: Manage Company Portal Users ---

@api_router.get("/admin/companies/{company_id}/portal-users")
async def list_company_portal_users(company_id: str, admin: dict = Depends(get_current_admin)):
    """List all portal users for a company"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    company = await db.companies.find_one(scope_query({"id": company_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    users_cursor = db.company_users.find(
        {"company_id": company_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    )
    users = await users_cursor.to_list(100)
    return users

@api_router.post("/admin/companies/{company_id}/portal-users")
async def create_company_portal_user(
    company_id: str,
    user_data: dict,
    admin: dict = Depends(get_current_admin)
):
    """Create a new portal user for a company"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    company = await db.companies.find_one(scope_query({"id": company_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if email already exists
    existing = await db.company_users.find_one(scope_query({"email": user_data.get("email"), "is_deleted": {"$ne": True}}, org_id))
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Validate required fields
    if not user_data.get("name") or not user_data.get("email") or not user_data.get("password"):
        raise HTTPException(status_code=400, detail="Name, email, and password are required")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.get("password", ""))
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Create user
    new_user = {
        "id": str(uuid.uuid4()),
        "company_id": company_id,
        "email": user_data.get("email"),
        "password_hash": get_password_hash(user_data.get("password")),
        "name": user_data.get("name"),
        "phone": user_data.get("phone", ""),
        "role": user_data.get("role", "company_viewer"),
        "is_active": True,
        "is_deleted": False,
        "created_at": get_ist_isoformat(),
        "created_by": f"admin:{admin.get('id')}"
    }
    
    new_user["organization_id"] = org_id
    await db.company_users.insert_one(new_user)
    
    return {"message": "Portal user created successfully", "id": new_user["id"]}

@api_router.delete("/admin/companies/{company_id}/portal-users/{user_id}")
async def delete_company_portal_user(
    company_id: str,
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Delete (soft) a portal user"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.company_users.update_one(
        {"id": user_id, "company_id": company_id},
        {"$set": {"is_deleted": True, "deleted_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Portal user not found")
    
    return {"message": "Portal user deleted"}

@api_router.put("/admin/companies/{company_id}/portal-users/{user_id}/reset-password")
async def reset_portal_user_password(
    company_id: str,
    user_id: str,
    data: dict,
    admin: dict = Depends(get_current_admin)
):
    """Reset a portal user's password with strong validation"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    new_password = data.get("password")
    if not new_password:
        raise HTTPException(status_code=400, detail="Password is required")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    result = await db.company_users.update_one(
        {"id": user_id, "company_id": company_id, "is_deleted": {"$ne": True}},
        {"$set": {
            "password_hash": get_password_hash(new_password),
            "updated_at": get_ist_isoformat()
        }}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Portal user not found")
    
    return {"message": "Password reset successfully"}

# ==================== ADMIN ENDPOINTS - USERS ====================

@api_router.get("/admin/users")
async def list_users(
    company_id: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List users with optional search support"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"email": search_regex},
            {"phone": search_regex},
            {"department": search_regex}
        ]
    
    skip = (page - 1) * limit
    users = await db.users.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Add label field for SmartSelect compatibility (handle missing name field)
    for u in users:
        u["label"] = u.get("name", u.get("email", "Unknown User"))
    
    return users

@api_router.post("/admin/users")
async def create_user(user_data: UserCreate, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    company_query = {"id": user_data.company_id, "is_deleted": {"$ne": True}}
    company_query = scope_query(company_query, org_id)
    
    company = await db.companies.find_one(company_query, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    user_dict = user_data.model_dump()
    if org_id:
        user_dict["organization_id"] = org_id
    
    user = User(**user_dict)
    await db.users.insert_one(user.model_dump())
    await log_audit("user", user.id, "create", {"data": user_data.model_dump()}, admin)
    result = user.model_dump()
    result.get("label", result.get("name", "Unknown")) or result.get("name", "Unknown"); result["label"] = result.get("name", "Unknown")
    return result

@api_router.post("/admin/users/quick-create")
async def quick_create_user(user_data: UserCreate, admin: dict = Depends(get_current_admin)):
    """Quick create user (for inline creation from dropdowns)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    company = await db.companies.find_one(scope_query({"id": user_data.company_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if user with same email exists in same company
    existing = await db.users.find_one(
        {"email": user_data.email, "company_id": user_data.company_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if existing:
        existing.get("label", existing.get("name", "Unknown")) or existing.get("name", "Unknown"); existing["label"] = existing.get("name", "Unknown")
        return existing
    
    user = User(**user_data.model_dump())
    user_ins_dict["organization_id"] = org_id
    user_ins_dict = user.model_dump()
    await db.users.insert_one(user_ins_dict)
    await log_audit("user", user.id, "quick_create", {"data": user_data.model_dump()}, admin)
    
    result = user.model_dump()
    result.get("label", result.get("name", "Unknown")) or result.get("name", "Unknown"); result["label"] = result.get("name", "Unknown")
    return result

@api_router.get("/admin/users/{user_id}")
async def get_user(user_id: str, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    user = await db.users.find_one(scope_query({"id": user_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@api_router.put("/admin/users/{user_id}")
async def update_user(user_id: str, updates: UserUpdate, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.users.find_one(scope_query({"id": user_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.users.update_one(scope_query({"id": user_id}, org_id), {"$set": update_data})
    await log_audit("user", user_id, "update", changes, admin)
    return await db.users.find_one(scope_query({"id": user_id}, org_id), {"_id": 0})

@api_router.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.users.update_one(scope_query({"id": user_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    await log_audit("user", user_id, "delete", {"is_deleted": True}, admin)
    return {"message": "User archived"}


# ==================== ADMIN ENDPOINTS - COMPANY EMPLOYEES ====================

@api_router.get("/admin/company-employees")
async def list_company_employees(
    company_id: Optional[str] = None,
    q: Optional[str] = None,
    is_active: Optional[bool] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List company employees (device users) with optional filters"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    if is_active is not None:
        query["is_active"] = is_active
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"email": search_regex},
            {"employee_id": search_regex},
            {"department": search_regex}
        ]
    
    skip = (page - 1) * limit
    employees = await db.company_employees.find(query, {"_id": 0}).sort("name", 1).skip(skip).limit(limit).to_list(limit)
    total = await db.company_employees.count_documents(query)
    
    # Add company name to each employee
    company_ids = list(set(e.get("company_id") for e in employees if e.get("company_id")))
    companies = {}
    if company_ids:
        companies_cursor = db.companies.find({"id": {"$in": company_ids}}, {"_id": 0, "id": 1, "name": 1})
        async for c in companies_cursor:
            companies[c["id"]] = c["name"]
    
    for emp in employees:
        emp["company_name"] = companies.get(emp.get("company_id"), "Unknown")
        emp.get("label", emp.get("name", "Unknown")) or emp.get("name", "Unknown"); emp["label"] = emp.get("name", "Unknown")  # For SmartSelect
    
    return employees


@api_router.post("/admin/company-employees")
async def create_company_employee(employee: CompanyEmployeeCreate, admin: dict = Depends(get_current_admin)):
    """Create a new company employee"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Verify company exists within tenant
    company = await db.companies.find_one(scope_query({"id": employee.company_id, "is_deleted": {"$ne": True}}, org_id))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    new_employee = CompanyEmployee(**employee.model_dump())
    emp_dict = new_employee.model_dump()
    if org_id:
        emp_dict["organization_id"] = org_id
    await db.company_employees.insert_one(emp_dict)
    await log_audit("company_employee", new_employee.id, "create", {k: v for k, v in emp_dict.items() if k != "_id"}, admin)
    
    result = {k: v for k, v in emp_dict.items() if k != "_id"}
    result["company_name"] = company.get("name")
    return result


@api_router.post("/admin/company-employees/quick-create")
async def quick_create_company_employee(
    data: dict = Body(...),
    admin: dict = Depends(get_current_admin)
):
    """Quick create employee for inline forms - accepts JSON"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    company_id = data.get("company_id")
    name = data.get("name")
    if not company_id or not name:
        raise HTTPException(status_code=400, detail="company_id and name are required")
    
    company = await db.companies.find_one(scope_query({"id": company_id, "is_deleted": {"$ne": True}}, org_id))
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    org_id = admin.get("organization_id")
    new_employee = CompanyEmployee(
        company_id=company_id,
        name=name,
        email=data.get("email"),
        phone=data.get("phone"),
        department=data.get("department")
    )
    emp_dict = new_employee.model_dump()
    if org_id:
        emp_dict["organization_id"] = org_id
    await db.company_employees.insert_one(emp_dict)
    
    result = {k: v for k, v in emp_dict.items() if k != "_id"}
    result["company_name"] = company.get("name")
    result["label"] = name
    return result


@api_router.get("/admin/company-employees/{employee_id}")
async def get_company_employee(employee_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific employee"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    employee = await db.company_employees.find_one(scope_query({"id": employee_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    return employee


@api_router.get("/admin/company-employees/{employee_id}/full-profile")
async def get_company_employee_full_profile(employee_id: str, admin: dict = Depends(get_current_admin)):
    """Get employee with all related data: devices, licenses, subscriptions, service history"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Get employee
    employee = await db.company_employees.find_one(scope_query({"id": employee_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # Get company info
    company = await db.companies.find_one({"id": employee.get("company_id")}, {"_id": 0, "name": 1, "id": 1})
    employee["company_name"] = company.get("name") if company else "Unknown"
    
    # Get assigned devices
    devices = await db.devices.find({
        "assigned_employee_id": employee_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    # Enrich devices with warranty info
    for device in devices:
        # Calculate warranty status
        if device.get("warranty_end_date"):
            try:
                from datetime import datetime
                end_date = datetime.fromisoformat(device["warranty_end_date"].replace("Z", "+00:00"))
                now = datetime.now(end_date.tzinfo) if end_date.tzinfo else datetime.now()
                days_remaining = (end_date - now).days
                device["warranty_days_remaining"] = days_remaining
                device["warranty_status"] = "active" if days_remaining > 30 else ("expiring" if days_remaining > 0 else "expired")
            except:
                device["warranty_status"] = "unknown"
    
    # Get licenses assigned to this employee
    licenses = await db.licenses.find({
        "assigned_to": employee_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    # Get service history for employee's devices
    device_ids = [d.get("id") for d in devices]
    service_history = []
    if device_ids:
        service_history = await db.service_records.find({
            "device_id": {"$in": device_ids},
            "is_deleted": {"$ne": True}
        }, {"_id": 0}).sort("service_date", -1).to_list(50)
    
    # Get tickets raised by or for this employee's devices
    tickets = await db.tickets.find({
        "$or": [
            {"device_id": {"$in": device_ids}},
            {"created_by_email": employee.get("email")}
        ],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("created_at", -1).to_list(20)
    
    # Get email subscriptions for the company (employee might have access)
    subscriptions = await db.email_subscriptions.find({
        "company_id": employee.get("company_id"),
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(20)
    
    # Calculate summary stats
    summary = {
        "total_devices": len(devices),
        "active_devices": len([d for d in devices if d.get("status") == "active"]),
        "devices_under_warranty": len([d for d in devices if d.get("warranty_status") == "active"]),
        "devices_warranty_expiring": len([d for d in devices if d.get("warranty_status") == "expiring"]),
        "total_licenses": len(licenses),
        "active_licenses": len([l for l in licenses if l.get("status") == "active"]),
        "open_tickets": len([t for t in tickets if t.get("status") in ["open", "in_progress"]]),
        "total_service_records": len(service_history)
    }
    
    return {
        "employee": employee,
        "summary": summary,
        "devices": devices,
        "licenses": licenses,
        "subscriptions": subscriptions,
        "service_history": service_history,
        "tickets": tickets
    }


@api_router.put("/admin/company-employees/{employee_id}")
async def update_company_employee(employee_id: str, data: CompanyEmployeeUpdate, admin: dict = Depends(get_current_admin)):
    """Update an employee"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.company_employees.update_one(scope_query({"id": employee_id, "is_deleted": {"$ne": True}}, org_id), {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    await log_audit("company_employee", employee_id, "update", update_data, admin)
    return {"message": "Employee updated"}


@api_router.delete("/admin/company-employees/{employee_id}")
async def delete_company_employee(employee_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete an employee"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.company_employees.update_one(scope_query({"id": employee_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Employee not found")
    await log_audit("company_employee", employee_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Employee archived"}


@api_router.post("/admin/company-employees/bulk-import")
async def bulk_import_company_employees(
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin)
):
    """
    Bulk import company employees from CSV/Excel file.
    Required columns: company_code OR company_name, name
    Optional columns: employee_id, email, phone, department, designation, location
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    import pandas as pd
    
    # Read file
    content = await file.read()
    filename = file.filename.lower()
    
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(BytesIO(content))
        elif filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(BytesIO(content))
        else:
            raise HTTPException(status_code=400, detail="Unsupported file format. Use CSV or Excel.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading file: {str(e)}")
    
    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
    
    # Check required columns
    if 'name' not in df.columns:
        raise HTTPException(status_code=400, detail="Missing required column: name")
    
    if 'company_code' not in df.columns and 'company_name' not in df.columns:
        raise HTTPException(status_code=400, detail="Missing required column: company_code or company_name")
    
    # Build company lookup
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0, "id": 1, "name": 1, "code": 1}).to_list(1000)
    company_by_code = {c["code"].upper(): c for c in companies if c.get("code")}
    company_by_name = {c["name"].lower(): c for c in companies}
    
    results = {"created": 0, "errors": [], "skipped": 0}
    
    for idx, row in df.iterrows():
        row_num = idx + 2  # Excel row (1-indexed + header)
        
        try:
            name = str(row.get('name', '')).strip()
            if not name or name == 'nan':
                results["errors"].append({"row": row_num, "error": "Name is required"})
                continue
            
            # Find company
            company = None
            company_code = str(row.get('company_code', '')).strip().upper()
            company_name = str(row.get('company_name', '')).strip().lower()
            
            if company_code and company_code != 'NAN':
                company = company_by_code.get(company_code)
                if not company:
                    results["errors"].append({"row": row_num, "error": f"Company code '{company_code}' not found"})
                    continue
            elif company_name and company_name != 'nan':
                company = company_by_name.get(company_name)
                if not company:
                    results["errors"].append({"row": row_num, "error": f"Company name '{company_name}' not found"})
                    continue
            else:
                results["errors"].append({"row": row_num, "error": "Company code or name is required"})
                continue
            
            # Create employee
            employee_data = {
                "company_id": company["id"],
                "name": name,
                "employee_id": str(row.get('employee_id', '')).strip() if pd.notna(row.get('employee_id')) else None,
                "email": str(row.get('email', '')).strip() if pd.notna(row.get('email')) else None,
                "phone": str(row.get('phone', '')).strip() if pd.notna(row.get('phone')) else None,
                "department": str(row.get('department', '')).strip() if pd.notna(row.get('department')) else None,
                "designation": str(row.get('designation', '')).strip() if pd.notna(row.get('designation')) else None,
                "location": str(row.get('location', '')).strip() if pd.notna(row.get('location')) else None,
            }
            
            # Clean None values that are empty strings
            employee_data = {k: (v if v and v != 'nan' else None) for k, v in employee_data.items()}
            employee_data["company_id"] = company["id"]  # Ensure company_id is set
            employee_data["name"] = name
            
            new_employee = CompanyEmployee(**employee_data)
            new_employee_ins_dict["organization_id"] = org_id
            new_employee_ins_dict = new_employee.model_dump()
            await db.company_employees.insert_one(new_employee_ins_dict)
            results["created"] += 1
            
        except Exception as e:
            results["errors"].append({"row": row_num, "error": str(e)})
    
    return results


@api_router.get("/admin/company-employees/template/download")
async def download_employee_template(admin: dict = Depends(get_current_admin)):
    """Download CSV template for bulk employee import"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    import csv
    import io
    
    # Create CSV content as string first
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header row
    writer.writerow(['company_code', 'name', 'employee_id', 'email', 'phone', 'department', 'designation', 'location'])
    
    # Sample data rows
    writer.writerow(['ACME001', 'John Smith', 'EMP001', 'john.smith@acme.com', '9876543210', 'IT', 'Senior Engineer', 'Floor 2, Desk 15'])
    writer.writerow(['ACME001', 'Jane Doe', 'EMP002', 'jane.doe@acme.com', '9876543211', 'HR', 'Manager', 'Floor 1, Cabin 3'])
    writer.writerow(['ACME001', 'Bob Wilson', '', 'bob@acme.com', '', 'Sales', '', ''])
    
    # Convert to bytes with UTF-8 BOM for Excel compatibility
    csv_content = output.getvalue()
    buffer = BytesIO()
    buffer.write(b'\xef\xbb\xbf')  # UTF-8 BOM
    buffer.write(csv_content.encode('utf-8'))
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=employee_import_template.csv"}
    )


# ==================== ADMIN ENDPOINTS - DEVICES ====================

@api_router.get("/admin/devices")
async def list_devices(
    company_id: Optional[str] = None, 
    site_id: Optional[str] = None,
    status: Optional[str] = None,
    amc_status: Optional[str] = None,  # Filter by AMC status: active, none, expired
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List devices with AMC status and smart search with synonyms"""
    from utils.synonyms import expand_search_query, get_brand_variants
    
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    if site_id:
        query["site_id"] = site_id
    if status:
        query["status"] = status
    
    # Add search filter with synonym support
    if q and q.strip():
        search_term = q.strip()
        # Get expanded search with synonyms
        synonym_regex = expand_search_query(search_term)
        # Also get brand variants
        brand_variants = get_brand_variants(search_term)
        brand_regex = {"$regex": "|".join(brand_variants), "$options": "i"}
        
        query["$or"] = [
            {"serial_number": {"$regex": search_term, "$options": "i"}},
            {"asset_tag": {"$regex": search_term, "$options": "i"}},
            {"brand": brand_regex},
            {"model": {"$regex": search_term, "$options": "i"}},
            {"device_type": synonym_regex},  # Smart search with synonyms
            {"name": {"$regex": search_term, "$options": "i"}},
            {"display_name": {"$regex": search_term, "$options": "i"}},
            {"notes": synonym_regex}
        ]
    
    skip = (page - 1) * limit
    devices = await db.devices.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich each device with AMC status from amc_device_assignments JOIN
    result = []
    for device in devices:
        # Get company name
        company = await db.companies.find_one({"id": device.get("company_id")}, {"_id": 0, "name": 1})
        device["company_name"] = company.get("name") if company else "Unknown"
        
        # Get assigned user name
        if device.get("assigned_user_id"):
            user = await db.users.find_one({"id": device["assigned_user_id"]}, {"_id": 0, "name": 1})
            device["assigned_user_name"] = user.get("name") if user else None
        
        # JOIN amc_device_assignments to get AMC status
        amc_assignment = await db.amc_device_assignments.find_one({
            "device_id": device["id"],
            "status": "active"
        }, {"_id": 0})
        
        if amc_assignment:
            # Check if coverage is still valid
            coverage_active = is_warranty_active(amc_assignment.get("coverage_end", ""))
            if coverage_active:
                # Get AMC contract details
                amc_contract = await db.amc_contracts.find_one({
                    "id": amc_assignment["amc_contract_id"],
                    "is_deleted": {"$ne": True}
                }, {"_id": 0, "name": 1, "amc_type": 1})
                
                device["amc_status"] = "active"
                device["amc_contract_id"] = amc_assignment["amc_contract_id"]
                device["amc_contract_name"] = amc_contract.get("name") if amc_contract else None
                device["amc_coverage_end"] = amc_assignment.get("coverage_end")
            else:
                device["amc_status"] = "expired"
                device["amc_contract_id"] = amc_assignment["amc_contract_id"]
                device["amc_coverage_end"] = amc_assignment.get("coverage_end")
        else:
            device["amc_status"] = "none"
            device["amc_contract_id"] = None
            device["amc_contract_name"] = None
            device["amc_coverage_end"] = None
        
        # Add SmartSelect label
        device["label"] = f"{device.get('brand', '')} {device.get('model', '')} - {device.get('serial_number', '')}"
        
        # Add deployment info if device was created from deployment
        if device.get("source") == "deployment" and device.get("deployment_id"):
            deployment = await db.deployments.find_one(
                {"id": device["deployment_id"], "is_deleted": {"$ne": True}}, 
                {"_id": 0, "name": 1, "site_id": 1}
            )
            if deployment:
                device["deployment_name"] = deployment.get("name")
                # Get site name
                site = await db.sites.find_one({"id": deployment.get("site_id")}, {"_id": 0, "name": 1})
                device["site_name"] = site.get("name") if site else None
        
        # Filter by AMC status if requested
        if amc_status and device["amc_status"] != amc_status:
            continue
        
        result.append(device)
    
    return result

@api_router.post("/admin/devices")
async def create_device(device_data: DeviceCreate, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    company_query = {"id": device_data.company_id, "is_deleted": {"$ne": True}}
    company_query = scope_query(company_query, org_id)
    
    company = await db.companies.find_one(company_query, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    existing = await db.devices.find_one({"serial_number": device_data.serial_number, "is_deleted": {"$ne": True}}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Serial number already exists")
    
    # Filter out None values to avoid validation errors with default_factory fields
    device_dict = {k: v for k, v in device_data.model_dump().items() if v is not None}
    
    # Add organization_id for multi-tenancy
    if org_id:
        device_dict["organization_id"] = org_id
    
    device = Device(**device_dict)
    await db.devices.insert_one(device.model_dump())
    
    # Log initial assignment if user is assigned
    if device_data.assigned_user_id:
        user = await db.users.find_one({"id": device_data.assigned_user_id}, {"_id": 0, "name": 1})
        assignment = AssignmentHistory(
            device_id=device.id,
            from_user_id=None,
            to_user_id=device_data.assigned_user_id,
            from_user_name=None,
            to_user_name=user.get("name") if user else None,
            reason="Initial assignment",
            changed_by=admin.get("id"),
            changed_by_name=admin.get("name")
        )
        assignment_ins_dict["organization_id"] = org_id
        assignment_ins_dict = assignment.model_dump()
        await db.assignment_history.insert_one(assignment_ins_dict)
    
    await log_audit("device", device.id, "create", {"data": device_data.model_dump()}, admin)
    return device.model_dump()

@api_router.get("/admin/devices/{device_id}")
async def get_device(device_id: str, admin: dict = Depends(get_current_admin)):
    """Get device with full AMC contract details - P0 Fix"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    device = await db.devices.find_one(scope_query({"id": device_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get company details
    company = await db.companies.find_one(scope_query({"id": device.get("company_id")}, org_id), {"_id": 0, "name": 1})
    device["company_name"] = company.get("name") if company else "Unknown"
    
    # Get assigned user details
    if device.get("assigned_user_id"):
        user = await db.users.find_one(scope_query({"id": device["assigned_user_id"]}, org_id), {"_id": 0, "name": 1, "email": 1})
        device["assigned_user_name"] = user.get("name") if user else None
        device["assigned_user_email"] = user.get("email") if user else None
    
    # JOIN amc_device_assignments → amc_contracts for full AMC info
    amc_assignments = await db.amc_device_assignments.find({
        "device_id": device_id
    }, {"_id": 0}).to_list(100)
    
    device["amc_assignments"] = []
    device["active_amc"] = None
    
    for assignment in amc_assignments:
        # Get full contract details
        contract = await db.amc_contracts.find_one({
            "id": assignment["amc_contract_id"],
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        
        if contract:
            coverage_active = is_warranty_active(assignment.get("coverage_end", ""))
            amc_info = {
                "assignment_id": assignment["id"],
                "amc_contract_id": contract["id"],
                "amc_name": contract.get("name"),
                "amc_type": contract.get("amc_type"),
                "coverage_start": assignment.get("coverage_start"),
                "coverage_end": assignment.get("coverage_end"),
                "coverage_active": coverage_active,
                "assignment_status": assignment.get("status"),
                "coverage_includes": contract.get("coverage_includes"),
                "entitlements": contract.get("entitlements")
            }
            device["amc_assignments"].append(amc_info)
            
            # Set active AMC if coverage is current
            if coverage_active and assignment.get("status") == "active" and not device["active_amc"]:
                device["active_amc"] = amc_info
    
    # Compute overall AMC status
    if device["active_amc"]:
        device["amc_status"] = "active"
    elif len(amc_assignments) > 0:
        device["amc_status"] = "expired"
    else:
        device["amc_status"] = "none"
    
    # Get parts
    parts = await db.parts.find({"device_id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    device["parts"] = parts
    
    # Get service history count
    service_count = await db.service_history.count_documents(scope_query({"device_id": device_id}, org_id))
    device["service_count"] = service_count
    
    return device

@api_router.put("/admin/devices/{device_id}")
async def update_device(device_id: str, updates: DeviceUpdate, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.devices.find_one(scope_query({"id": device_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Device not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # Check serial number uniqueness if updating
    if "serial_number" in update_data:
        dup = await db.devices.find_one({
            "serial_number": update_data["serial_number"],
            "id": {"$ne": device_id},
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        if dup:
            raise HTTPException(status_code=400, detail="Serial number already exists")
    
    # Track assignment change
    if "assigned_user_id" in update_data and update_data["assigned_user_id"] != existing.get("assigned_user_id"):
        old_user = None
        new_user = None
        
        if existing.get("assigned_user_id"):
            old_u = await db.users.find_one({"id": existing["assigned_user_id"]}, {"_id": 0, "name": 1})
            old_user = old_u.get("name") if old_u else None
        
        if update_data["assigned_user_id"]:
            new_u = await db.users.find_one({"id": update_data["assigned_user_id"]}, {"_id": 0, "name": 1})
            new_user = new_u.get("name") if new_u else None
        
        assignment = AssignmentHistory(
            device_id=device_id,
            from_user_id=existing.get("assigned_user_id"),
            to_user_id=update_data["assigned_user_id"],
            from_user_name=old_user,
            to_user_name=new_user,
            reason="Reassignment",
            changed_by=admin.get("id"),
            changed_by_name=admin.get("name")
        )
        assignment_ins_dict["organization_id"] = org_id
        assignment_ins_dict = assignment.model_dump()
        await db.assignment_history.insert_one(assignment_ins_dict)
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.devices.update_one({"id": device_id}, {"$set": update_data})
    await log_audit("device", device_id, "update", changes, admin)
    return await db.devices.find_one({"id": device_id}, {"_id": 0})

@api_router.delete("/admin/devices/{device_id}")
async def delete_device(device_id: str, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.devices.update_one(scope_query({"id": device_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Soft delete related data
    await db.parts.update_many(scope_query({"device_id": device_id}, org_id), {"$set": {"is_deleted": True}})
    await db.amc.update_many(scope_query({"device_id": device_id}, org_id), {"$set": {"is_deleted": True}})
    await log_audit("device", device_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Device archived"}

@api_router.get("/admin/devices/{device_id}/assignment-history")
async def get_assignment_history(device_id: str, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    history = await db.assignment_history.find({"device_id": device_id}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return history

@api_router.get("/admin/devices/{device_id}/service-history")
async def get_device_service_history(device_id: str, admin: dict = Depends(get_current_admin)):
    """Get comprehensive service history for a device (service records, tickets, AI chats)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    device = await db.devices.find_one(scope_query({"id": device_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    history = []
    
    # Get service history records
    services = await db.service_history.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("service_date", -1).to_list(100)
    
    for s in services:
        history.append({
            "id": s.get("id"),
            "type": "service_record",
            "service_type": s.get("service_type", "Service"),
            "description": s.get("problem_reported") or s.get("action_taken") or s.get("description", ""),
            "technician": s.get("technician_name"),
            "date": s.get("service_date"),
            "status": s.get("status")
        })
    
    # Get tickets from V2 ticketing system
    v2_tickets = await db.tickets_v2.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for t in v2_tickets:
        history.append({
            "id": t.get("id"),
            "type": "service_ticket",
            "service_type": t.get("help_topic_name", "Service Ticket"),
            "ticket_number": t.get("ticket_number"),
            "description": t.get("subject") or t.get("description"),
            "date": t.get("created_at"),
            "status": t.get("current_stage_name", "New"),
            "priority": t.get("priority_name"),
            "resolved_date": t.get("resolved_at"),
            "assigned_to": t.get("assigned_to_name"),
            "company_name": t.get("company_name")
        })
    
    # Get AI support chat history
    ai_chats = await db.ai_support_history.find({
        "device_id": device_id
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    for chat in ai_chats:
        user_messages = [m.get("content", "")[:100] for m in chat.get("messages", []) if m.get("role") == "user"]
        issue_summary = user_messages[0] if user_messages else "AI Support Chat"
        history.append({
            "id": chat.get("id"),
            "type": "ai_support",
            "service_type": "AI Support Chat",
            "description": issue_summary,
            "resolved_by_ai": chat.get("resolved_by_ai", False),
            "messages_count": len(chat.get("messages", [])),
            "date": chat.get("created_at"),
            "user_name": chat.get("user_name")
        })
    
    # Sort by date (most recent first)
    history.sort(key=lambda x: x.get("date") or "", reverse=True)
    
    return history

@api_router.get("/admin/devices/{device_id}/timeline")
async def get_device_timeline(device_id: str, admin: dict = Depends(get_current_admin)):
    """Get unified timeline for a device (assignments, services, parts, AMC)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    device = await db.devices.find_one(scope_query({"id": device_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    timeline = []
    
    # Purchase event
    timeline.append({
        "type": "purchase",
        "date": device.get("purchase_date"),
        "title": "Device Purchased",
        "description": f"{device.get('brand')} {device.get('model')} added to inventory",
        "icon": "package"
    })
    
    # Assignment history
    assignments = await db.assignment_history.find({"device_id": device_id}, {"_id": 0}).to_list(100)
    for a in assignments:
        from_name = a.get("from_user_name") or "Unassigned"
        to_name = a.get("to_user_name") or "Unassigned"
        timeline.append({
            "type": "assignment",
            "date": a.get("created_at"),
            "title": "Assignment Changed",
            "description": f"{from_name} → {to_name}",
            "changed_by": a.get("changed_by_name"),
            "icon": "user"
        })
    
    # Service history
    services = await db.service_history.find({"device_id": device_id}, {"_id": 0}).to_list(100)
    for s in services:
        timeline.append({
            "type": "service",
            "date": s.get("service_date"),
            "title": s.get("service_type", "Service").replace("_", " ").title(),
            "description": s.get("action_taken"),
            "technician": s.get("technician_name"),
            "icon": "wrench"
        })
    
    # Parts replacements
    parts = await db.parts.find({"device_id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    for p in parts:
        timeline.append({
            "type": "part",
            "date": p.get("replaced_date"),
            "title": f"Part Replaced: {p.get('part_name')}",
            "description": f"Warranty: {p.get('warranty_months')} months",
            "icon": "cpu"
        })
    
    # AMC
    amc_list = await db.amc.find({"device_id": device_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(10)
    for amc in amc_list:
        timeline.append({
            "type": "amc",
            "date": amc.get("start_date"),
            "title": "AMC Started",
            "description": f"Valid until {amc.get('end_date')}",
            "icon": "shield"
        })
    
    # Sort by date descending (handle None dates)
    timeline.sort(key=lambda x: x.get("date") or "", reverse=True)
    
    return timeline

# ==================== SERVICE HISTORY ENDPOINTS ====================

@api_router.get("/admin/services/options")
async def get_service_options():
    """Get all service record enum options for dropdowns"""
    from models.service import (
        SERVICE_CATEGORIES, SERVICE_RESPONSIBILITIES, SERVICE_ROLES,
        OEM_NAMES, OEM_WARRANTY_TYPES, OEM_CASE_RAISED_VIA, 
        OEM_PRIORITY, OEM_CASE_STATUSES, BILLING_IMPACT
    )
    return {
        "service_categories": [
            {"value": "internal_service", "label": "Internal Service (Provided by Us)"},
            {"value": "oem_warranty_service", "label": "OEM Warranty Service (Facilitated)"},
            {"value": "paid_third_party_service", "label": "Paid Third-Party Service"},
            {"value": "inspection_diagnosis", "label": "Inspection / Diagnosis Only"}
        ],
        "service_responsibilities": [
            {"value": "our_team", "label": "Our Team"},
            {"value": "oem", "label": "OEM"},
            {"value": "partner_vendor", "label": "Partner / Vendor"}
        ],
        "service_roles": [
            {"value": "provider", "label": "Provider"},
            {"value": "coordinator_facilitator", "label": "Coordinator / Facilitator"},
            {"value": "observer", "label": "Observer"}
        ],
        "oem_names": OEM_NAMES,
        "oem_warranty_types": OEM_WARRANTY_TYPES,
        "oem_case_raised_via": [
            {"value": "phone", "label": "Phone"},
            {"value": "oem_portal", "label": "OEM Portal"},
            {"value": "email", "label": "Email"},
            {"value": "chat", "label": "Chat"}
        ],
        "oem_priority": [
            {"value": "NBD", "label": "Next Business Day"},
            {"value": "Standard", "label": "Standard"},
            {"value": "Deferred", "label": "Deferred"},
            {"value": "Critical", "label": "Critical/Urgent"}
        ],
        "oem_case_statuses": [
            {"value": "reported_to_oem", "label": "Reported to OEM"},
            {"value": "oem_accepted", "label": "OEM Accepted"},
            {"value": "engineer_assigned", "label": "Engineer Assigned"},
            {"value": "parts_dispatched", "label": "Parts Dispatched"},
            {"value": "visit_scheduled", "label": "Visit Scheduled"},
            {"value": "resolved_by_oem", "label": "Resolved by OEM"},
            {"value": "closed_by_oem", "label": "Closed by OEM"}
        ],
        "billing_impact": [
            {"value": "not_billable", "label": "Not Billable"},
            {"value": "warranty_covered", "label": "Warranty Covered"},
            {"value": "chargeable", "label": "Chargeable"}
        ],
        "service_statuses": [
            {"value": "open", "label": "Open"},
            {"value": "in_progress", "label": "In Progress"},
            {"value": "on_hold", "label": "On Hold"},
            {"value": "completed", "label": "Completed"},
            {"value": "closed", "label": "Closed"}
        ]
    }

@api_router.get("/admin/services")
async def list_services(
    device_id: Optional[str] = None, 
    company_id: Optional[str] = None,
    service_category: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
    admin: dict = Depends(get_current_admin)
):
    """List service records with filters"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {}
    query = scope_query(query, org_id)
    
    if device_id:
        query["device_id"] = device_id
    if company_id:
        query["company_id"] = company_id
    if service_category:
        query["service_category"] = service_category
    if status:
        query["status"] = status
    
    services = await db.service_history.find(query, {"_id": 0}).sort("service_date", -1).to_list(limit)
    return services


# ==================== STAGE TEMPLATE ENDPOINT ====================
@api_router.get("/admin/services/stage-templates")
async def get_stage_templates():
    """Get default stage templates for service records"""
    from models.service import DEFAULT_SERVICE_STAGES, OEM_SERVICE_STAGES
    return {
        "internal": DEFAULT_SERVICE_STAGES,
        "oem": OEM_SERVICE_STAGES
    }


@api_router.post("/admin/services")
async def create_service(service_data: ServiceHistoryCreate, admin: dict = Depends(get_current_admin)):
    from models.service import DEFAULT_SERVICE_STAGES, OEM_SERVICE_STAGES, ServiceStage
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    device_query = {"id": service_data.device_id, "is_deleted": {"$ne": True}}
    device_query = scope_query(device_query, org_id)
    
    device = await db.devices.find_one(device_query, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    service_dict = service_data.model_dump()
    
    # Add organization_id
    if org_id:
        service_dict["organization_id"] = org_id
    
    # ==================== OEM VALIDATION RULES ====================
    is_oem_service = service_dict.get("service_category") == "oem_warranty_service"
    
    if is_oem_service:
        # Validate OEM details are provided
        oem_details = service_dict.get("oem_details")
        if not oem_details:
            raise HTTPException(status_code=400, detail="OEM Service Details are required for OEM Warranty Service")
        
        # Validate required OEM fields
        if not oem_details.get("oem_name"):
            raise HTTPException(status_code=400, detail="OEM Name is required")
        if not oem_details.get("oem_case_number"):
            raise HTTPException(status_code=400, detail="OEM Case/SR Number is required")
        if not oem_details.get("oem_warranty_type"):
            raise HTTPException(status_code=400, detail="OEM Warranty Type is required")
        if not oem_details.get("case_raised_date"):
            raise HTTPException(status_code=400, detail="Case Raised Date is required")
        if not oem_details.get("case_raised_via"):
            raise HTTPException(status_code=400, detail="Case Raised Via is required")
        
        # Auto-set fields for OEM cases
        service_dict["service_responsibility"] = "oem"
        service_dict["service_role"] = "coordinator_facilitator"
        service_dict["billing_impact"] = "warranty_covered"
        service_dict["counts_toward_amc"] = False  # LOCKED - cannot consume AMC
        service_dict["consumes_amc_quota"] = False
        service_dict["amc_covered"] = False
    
    # ==================== INITIALIZE STAGES ====================
    if service_dict.get("initialize_stages", True):
        stage_templates = OEM_SERVICE_STAGES if is_oem_service else DEFAULT_SERVICE_STAGES
        stages = []
        for template in stage_templates:
            stage = {
                "id": str(uuid.uuid4()),
                "stage_key": template["key"],
                "stage_label": template["label"],
                "order": template["order"],
                "status": "pending",
                "timestamp": None,
                "started_at": None,
                "completed_at": None,
                "notes": None,
                "updated_by": None,
                "updated_by_name": None,
                "attachments": [],
                "metadata": None
            }
            # Auto-complete "Request Raised" stage
            if template["key"] == "request_raised":
                stage["status"] = "completed"
                stage["timestamp"] = get_ist_isoformat()
                stage["completed_at"] = get_ist_isoformat()
                stage["updated_by"] = admin.get("id")
                stage["updated_by_name"] = admin.get("name")
            stages.append(stage)
        
        service_dict["stages"] = stages
        service_dict["current_stage"] = "request_raised"
        service_dict["stage_history"] = [{
            "stage_key": "request_raised",
            "action": "completed",
            "timestamp": get_ist_isoformat(),
            "updated_by": admin.get("id"),
            "updated_by_name": admin.get("name")
        }]
    
    # Remove the flag before saving
    service_dict.pop("initialize_stages", None)
    
    service = ServiceHistory(
        **service_dict,
        company_id=device.get("company_id"),
        created_by=admin.get("id"),
        created_by_name=admin.get("name")
    )
    service_ins_dict["organization_id"] = org_id
    service_ins_dict = service.model_dump()
    await db.service_history.insert_one(service_ins_dict)
    await log_audit("service", service.id, "create", {"data": service_data.model_dump()}, admin)
    return service.model_dump()

@api_router.get("/admin/services/{service_id}")
async def get_service(service_id: str, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await db.service_history.find_one(scope_query({"id": service_id}, org_id), {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")
    return service

@api_router.put("/admin/services/{service_id}")
async def update_service(service_id: str, updates: ServiceHistoryUpdate, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.service_history.find_one(scope_query({"id": service_id}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    # ==================== CLOSURE VALIDATION ====================
    # Check if record is already closed (read-only)
    if existing.get("is_closed"):
        raise HTTPException(status_code=400, detail="Closed service records cannot be modified")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # ==================== OEM VALIDATION RULES ====================
    service_category = update_data.get("service_category") or existing.get("service_category")
    
    if service_category == "oem_warranty_service":
        oem_details = update_data.get("oem_details") or existing.get("oem_details")
        
        # Validate OEM details
        if not oem_details:
            raise HTTPException(status_code=400, detail="OEM Service Details are required for OEM Warranty Service")
        if not oem_details.get("oem_case_number"):
            raise HTTPException(status_code=400, detail="OEM Case/SR Number is required")
        
        # Enforce locked fields for OEM cases
        update_data["service_responsibility"] = "oem"
        update_data["service_role"] = "coordinator_facilitator"
        update_data["billing_impact"] = "warranty_covered"
        update_data["counts_toward_amc"] = False
        update_data["consumes_amc_quota"] = False
        update_data["amc_covered"] = False
        
        # Check OEM closure status
        if oem_details.get("oem_case_status") == "closed_by_oem":
            # Require attachment for closure
            attachments = existing.get("attachments", [])
            if len(attachments) == 0:
                raise HTTPException(
                    status_code=400, 
                    detail="OEM service records require at least one attachment (proof) before closure"
                )
    
    # ==================== HANDLE CLOSURE ====================
    if update_data.get("status") == "closed" or (
        service_category == "oem_warranty_service" and 
        update_data.get("oem_details", {}).get("oem_case_status") == "closed_by_oem"
    ):
        # Require service outcome for closure
        service_outcome = update_data.get("service_outcome") or existing.get("service_outcome")
        if not service_outcome or not service_outcome.get("resolution_summary"):
            raise HTTPException(status_code=400, detail="Resolution summary is required for closure")
        
        update_data["is_closed"] = True
        update_data["closed_at"] = get_ist_isoformat()
        update_data["status"] = "closed"
    
    update_data["updated_at"] = get_ist_isoformat()
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.service_history.update_one({"id": service_id}, {"$set": update_data})
    await log_audit("service", service_id, "update", changes, admin)
    return await db.service_history.find_one({"id": service_id}, {"_id": 0})


# ==================== STAGE MANAGEMENT ENDPOINTS ====================
@api_router.put("/admin/services/{service_id}/stages/{stage_key}")
async def update_service_stage(
    service_id: str, 
    stage_key: str, 
    stage_update: dict,
    admin: dict = Depends(get_current_admin)
):
    """Update a specific stage in the service timeline"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await db.service_history.find_one(scope_query({"id": service_id}, org_id), {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    if service.get("is_closed"):
        raise HTTPException(status_code=400, detail="Closed service records cannot be modified")
    
    stages = service.get("stages", [])
    stage_history = service.get("stage_history", [])
    
    # Find the stage to update
    stage_found = False
    for i, stage in enumerate(stages):
        if stage.get("stage_key") == stage_key:
            stage_found = True
            old_status = stage.get("status")
            new_status = stage_update.get("status", old_status)
            
            # Update stage fields
            stage["status"] = new_status
            stage["notes"] = stage_update.get("notes", stage.get("notes"))
            stage["metadata"] = stage_update.get("metadata", stage.get("metadata"))
            stage["updated_by"] = admin.get("id")
            stage["updated_by_name"] = admin.get("name")
            stage["timestamp"] = get_ist_isoformat()
            
            # Handle status transitions
            if new_status == "in_progress" and not stage.get("started_at"):
                stage["started_at"] = get_ist_isoformat()
            elif new_status == "completed" and not stage.get("completed_at"):
                stage["completed_at"] = get_ist_isoformat()
            
            # Add attachments if provided
            if stage_update.get("attachments"):
                existing_attachments = stage.get("attachments", [])
                stage["attachments"] = existing_attachments + stage_update.get("attachments", [])
            
            stages[i] = stage
            
            # Record in history
            stage_history.append({
                "stage_key": stage_key,
                "action": new_status,
                "old_status": old_status,
                "notes": stage_update.get("notes"),
                "timestamp": get_ist_isoformat(),
                "updated_by": admin.get("id"),
                "updated_by_name": admin.get("name")
            })
            break
    
    if not stage_found:
        raise HTTPException(status_code=404, detail=f"Stage '{stage_key}' not found")
    
    # Update current stage to the latest in-progress or completed stage
    current_stage = stage_key
    for stage in sorted(stages, key=lambda x: x.get("order", 0), reverse=True):
        if stage.get("status") in ["in_progress", "completed"]:
            current_stage = stage.get("stage_key")
            break
    
    # Update the service record
    await db.service_history.update_one(
        {"id": service_id},
        {
            "$set": {
                "stages": stages,
                "stage_history": stage_history,
                "current_stage": current_stage,
                "updated_at": get_ist_isoformat()
            }
        }
    )
    
    await log_audit("service", service_id, "stage_update", {
        "stage_key": stage_key,
        "new_status": stage_update.get("status")
    }, admin)
    
    return await db.service_history.find_one(scope_query({"id": service_id}, org_id), {"_id": 0})


@api_router.post("/admin/services/{service_id}/stages")
async def add_custom_stage(
    service_id: str,
    stage_data: dict,
    admin: dict = Depends(get_current_admin)
):
    """Add a custom stage to the service timeline"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await db.service_history.find_one(scope_query({"id": service_id}, org_id), {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    if service.get("is_closed"):
        raise HTTPException(status_code=400, detail="Closed service records cannot be modified")
    
    stages = service.get("stages", [])
    stage_history = service.get("stage_history", [])
    
    # Validate required fields
    if not stage_data.get("stage_label"):
        raise HTTPException(status_code=400, detail="Stage label is required")
    
    # Generate stage key from label if not provided
    stage_key = stage_data.get("stage_key") or stage_data["stage_label"].lower().replace(" ", "_")
    
    # Check for duplicate stage keys
    if any(s.get("stage_key") == stage_key for s in stages):
        raise HTTPException(status_code=400, detail=f"Stage '{stage_key}' already exists")
    
    # Determine order (insert after specified position or at end)
    insert_after = stage_data.get("insert_after_stage")
    max_order = max((s.get("order", 0) for s in stages), default=0)
    
    if insert_after:
        # Find the stage to insert after
        for i, s in enumerate(stages):
            if s.get("stage_key") == insert_after:
                new_order = s.get("order", 0) + 0.5
                break
        else:
            new_order = max_order + 1
    else:
        new_order = max_order + 1
    
    # Create new stage
    new_stage = {
        "id": str(uuid.uuid4()),
        "stage_key": stage_key,
        "stage_label": stage_data["stage_label"],
        "order": new_order,
        "status": stage_data.get("status", "pending"),
        "timestamp": get_ist_isoformat() if stage_data.get("status") == "completed" else None,
        "started_at": get_ist_isoformat() if stage_data.get("status") in ["in_progress", "completed"] else None,
        "completed_at": get_ist_isoformat() if stage_data.get("status") == "completed" else None,
        "notes": stage_data.get("notes"),
        "updated_by": admin.get("id"),
        "updated_by_name": admin.get("name"),
        "attachments": [],
        "metadata": stage_data.get("metadata"),
        "is_custom": True
    }
    
    stages.append(new_stage)
    stages.sort(key=lambda x: x.get("order", 0))
    
    # Record in history
    stage_history.append({
        "stage_key": stage_key,
        "action": "added",
        "timestamp": get_ist_isoformat(),
        "updated_by": admin.get("id"),
        "updated_by_name": admin.get("name")
    })
    
    await db.service_history.update_one(
        {"id": service_id},
        {
            "$set": {
                "stages": stages,
                "stage_history": stage_history,
                "updated_at": get_ist_isoformat()
            }
        }
    )
    
    await log_audit("service", service_id, "stage_add", {"stage_key": stage_key}, admin)
    
    return await db.service_history.find_one(scope_query({"id": service_id}, org_id), {"_id": 0})


@api_router.post("/admin/services/{service_id}/attachments")
async def upload_service_attachment(
    service_id: str, 
    file: UploadFile = File(...),
    admin: dict = Depends(get_current_admin)
):
    """Upload attachment to service record"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await db.service_history.find_one(scope_query({"id": service_id}, org_id), {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    # Validate file type
    allowed_types = ["application/pdf", "image/jpeg", "image/png", "image/jpg"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File type not allowed. Use PDF, JPG, or PNG.")
    
    # Validate file size (5MB max)
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large. Maximum 5MB.")
    
    # Save file
    file_id = str(uuid.uuid4())
    ext = file.filename.split(".")[-1] if "." in file.filename else "bin"
    filename = f"{file_id}.{ext}"
    file_path = UPLOAD_DIR / filename
    
    with open(file_path, "wb") as f:
        f.write(content)
    
    # Create attachment record
    attachment = ServiceAttachment(
        id=file_id,
        filename=filename,
        original_name=file.filename,
        file_type=file.content_type,
        file_size=len(content)
    )
    
    # Add to service record
    attachments = service.get("attachments", [])
    attachments.append(attachment.model_dump())
    
    await db.service_history.update_one(
        {"id": service_id},
        {"$set": {"attachments": attachments}}
    )
    
    await log_audit("service", service_id, "attachment_upload", {"filename": file.filename}, admin)
    return {"message": "Attachment uploaded", "attachment": attachment.model_dump()}

@api_router.delete("/admin/services/{service_id}/attachments/{attachment_id}")
async def delete_service_attachment(service_id: str, attachment_id: str, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await db.service_history.find_one(scope_query({"id": service_id}, org_id), {"_id": 0})
    if not service:
        raise HTTPException(status_code=404, detail="Service record not found")
    
    attachments = service.get("attachments", [])
    attachment = next((a for a in attachments if a.get("id") == attachment_id), None)
    
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Delete file
    file_path = UPLOAD_DIR / attachment.get("filename")
    if file_path.exists():
        file_path.unlink()
    
    # Remove from service record
    attachments = [a for a in attachments if a.get("id") != attachment_id]
    await db.service_history.update_one(
        {"id": service_id},
        {"$set": {"attachments": attachments}}
    )
    
    await log_audit("service", service_id, "attachment_delete", {"attachment_id": attachment_id}, admin)
    return {"message": "Attachment deleted"}

# ==================== ADMIN ENDPOINTS - PARTS ====================

@api_router.get("/admin/parts")
async def list_parts(device_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    if device_id:
        query["device_id"] = device_id
    parts = await db.parts.find(query, {"_id": 0}).to_list(1000)
    return parts

@api_router.post("/admin/parts")
async def create_part(part_data: PartCreate, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    device_query = {"id": part_data.device_id, "is_deleted": {"$ne": True}}
    device_query = scope_query(device_query, org_id)
    
    device = await db.devices.find_one(device_query, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    warranty_expiry = calculate_warranty_expiry(part_data.replaced_date, part_data.warranty_months)
    
    part = Part(
        **part_data.model_dump(),
        warranty_expiry_date=warranty_expiry
    )
    part_dict = part.model_dump()
    if org_id:
        part_dict["organization_id"] = org_id
    
    await db.parts.insert_one(part_dict)
    await log_audit("part", part.id, "create", {"data": part_data.model_dump()}, admin)
    return part.model_dump()

@api_router.get("/admin/parts/{part_id}")
async def get_part(part_id: str, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": part_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    part = await db.parts.find_one(query, {"_id": 0})
    if not part:
        raise HTTPException(status_code=404, detail="Part not found")
    return part

@api_router.put("/admin/parts/{part_id}")
async def update_part(part_id: str, updates: PartUpdate, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": part_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    existing = await db.parts.find_one(query, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Part not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    if "replaced_date" in update_data or "warranty_months" in update_data:
        replaced_date = update_data.get("replaced_date", existing.get("replaced_date"))
        warranty_months = update_data.get("warranty_months", existing.get("warranty_months"))
        update_data["warranty_expiry_date"] = calculate_warranty_expiry(replaced_date, warranty_months)
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.parts.update_one(query, {"$set": update_data})
    await log_audit("part", part_id, "update", changes, admin)
    return await db.parts.find_one({"id": part_id}, {"_id": 0})

@api_router.delete("/admin/parts/{part_id}")
async def delete_part(part_id: str, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": part_id}
    query = scope_query(query, org_id)
    
    result = await db.parts.update_one(query, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Part not found")
    await log_audit("part", part_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Part archived"}

# ==================== ADMIN ENDPOINTS - AMC ====================

@api_router.get("/admin/amc")
async def list_amc(device_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    if device_id:
        query["device_id"] = device_id
    amc_list = await db.amc.find(query, {"_id": 0}).to_list(1000)
    return amc_list

@api_router.post("/admin/amc")
async def create_amc(amc_data: AMCCreate, admin: dict = Depends(get_current_admin)):
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    device_query = {"id": amc_data.device_id, "is_deleted": {"$ne": True}}
    device_query = scope_query(device_query, org_id)
    
    device = await db.devices.find_one(device_query, {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    existing = await db.amc.find_one({"device_id": amc_data.device_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="AMC already exists for this device")
    
    amc = AMC(**amc_data.model_dump())
    amc_ins_dict["organization_id"] = org_id
    amc_ins_dict = amc.model_dump()
    await db.amc.insert_one(amc_ins_dict)
    await log_audit("amc", amc.id, "create", {"data": amc_data.model_dump()}, admin)
    return amc.model_dump()

@api_router.get("/admin/amc/{amc_id}")
async def get_amc(amc_id: str, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    amc = await db.amc.find_one(scope_query({"id": amc_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not amc:
        raise HTTPException(status_code=404, detail="AMC not found")
    return amc

@api_router.put("/admin/amc/{amc_id}")
async def update_amc(amc_id: str, updates: AMCUpdate, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.amc.find_one(scope_query({"id": amc_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="AMC not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.amc.update_one(scope_query({"id": amc_id}, org_id), {"$set": update_data})
    await log_audit("amc", amc_id, "update", changes, admin)
    return await db.amc.find_one(scope_query({"id": amc_id}, org_id), {"_id": 0})

@api_router.delete("/admin/amc/{amc_id}")
async def delete_amc(amc_id: str, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.amc.update_one(scope_query({"id": amc_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="AMC not found")
    await log_audit("amc", amc_id, "delete", {"is_deleted": True}, admin)
    return {"message": "AMC archived"}

# ==================== AMC V2 CONTRACTS (Enhanced) ====================

def get_amc_status(start_date: str, end_date: str) -> str:
    """Calculate AMC status based on dates"""
    today = get_ist_now().date()
    try:
        start = datetime.fromisoformat(start_date.replace('Z', '+00:00')).date() if 'T' in start_date else datetime.strptime(start_date, '%Y-%m-%d').date()
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date() if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d').date()
        
        if today < start:
            return "upcoming"
        elif today > end:
            return "expired"
        else:
            return "active"
    except:
        return "unknown"

def get_days_until_expiry(end_date: str) -> Optional[int]:
    """Calculate days until AMC expiry"""
    today = get_ist_now().date()
    try:
        end = datetime.fromisoformat(end_date.replace('Z', '+00:00')).date() if 'T' in end_date else datetime.strptime(end_date, '%Y-%m-%d').date()
        return (end - today).days
    except:
        return None

@api_router.get("/admin/amc-contracts")
async def list_amc_contracts(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    serial: Optional[str] = None,  # Search by device serial number
    asset_tag: Optional[str] = None,  # Search by device asset tag
    q: Optional[str] = None,  # General search (name, company)
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List AMC contracts with serial number search - P0 Fix"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    query = {"is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    
    # If searching by serial/asset_tag, first find the device, then find contracts
    if serial or asset_tag:
        device_query = {"is_deleted": {"$ne": True}}
        device_query = scope_query(device_query, org_id)
        if serial:
            device_query["serial_number"] = {"$regex": serial, "$options": "i"}
        if asset_tag:
            device_query["asset_tag"] = {"$regex": asset_tag, "$options": "i"}
        
        devices = await db.devices.find(device_query, {"_id": 0, "id": 1}).to_list(100)
        device_ids = [d["id"] for d in devices]
        
        if not device_ids:
            return []  # No devices match, so no contracts
        
        # Find assignments for these devices
        assignments = await db.amc_device_assignments.find({
            "device_id": {"$in": device_ids}
        }, {"_id": 0, "amc_contract_id": 1}).to_list(1000)
        
        contract_ids = list(set([a["amc_contract_id"] for a in assignments]))
        if not contract_ids:
            return []
        
        query["id"] = {"$in": contract_ids}
    
    # General search
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex}
        ]
    
    skip = (page - 1) * limit
    contracts = await db.amc_contracts.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Compute status and enrich for each contract
    result = []
    for contract in contracts:
        status_val = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
        days_left = get_days_until_expiry(contract.get("end_date", ""))
        
        # Get company name
        company = await db.companies.find_one({"id": contract.get("company_id")}, {"_id": 0, "name": 1})
        
        # Get usage stats
        usage_count = await db.amc_usage.count_documents({"amc_contract_id": contract["id"]})
        
        # Get assigned devices count
        devices_count = await db.amc_device_assignments.count_documents({
            "amc_contract_id": contract["id"],
            "status": "active"
        })
        
        contract["status"] = status_val
        contract["days_until_expiry"] = days_left
        contract["company_name"] = company.get("name") if company else "Unknown"
        contract["usage_count"] = usage_count
        contract["assigned_devices_count"] = devices_count
        contract["label"] = contract.get("name")  # SmartSelect compatibility
        
        if status and status_val != status:
            continue
        result.append(contract)
    
    return result

@api_router.post("/admin/amc-contracts")
async def create_amc_contract(data: AMCContractCreate, admin: dict = Depends(get_current_admin)):
    """Create new AMC contract"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    company_query = {"id": data.company_id, "is_deleted": {"$ne": True}}
    company_query = scope_query(company_query, org_id)
    
    # Validate company exists
    company = await db.companies.find_one(company_query, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Build contract with defaults
    contract_data = {
        "company_id": data.company_id,
        "name": data.name,
        "amc_type": data.amc_type,
        "start_date": data.start_date,
        "end_date": data.end_date,
        "coverage_includes": data.coverage_includes or AMCCoverageIncludes().model_dump(),
        "exclusions": data.exclusions or AMCExclusions().model_dump(),
        "entitlements": data.entitlements or AMCEntitlements().model_dump(),
        "asset_mapping": data.asset_mapping or AMCAssetMapping().model_dump(),
        "internal_notes": data.internal_notes,
    }
    
    # Add organization_id for multi-tenancy
    if org_id:
        contract_data["organization_id"] = org_id
    
    contract = AMCContract(**contract_data)
    await db.amc_contracts.insert_one(contract.model_dump())
    await log_audit("amc_contract", contract.id, "create", {"data": contract_data}, admin)
    
    result = contract.model_dump()
    result["status"] = get_amc_status(result["start_date"], result["end_date"])
    result["company_name"] = company.get("name")
    return result

@api_router.get("/admin/amc-contracts/{contract_id}")
async def get_amc_contract(contract_id: str, admin: dict = Depends(get_current_admin)):
    """Get single AMC contract with details"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    contract = await db.amc_contracts.find_one(scope_query({"id": contract_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    # Compute status
    contract["status"] = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
    contract["days_until_expiry"] = get_days_until_expiry(contract.get("end_date", ""))
    
    # Get company details
    company = await db.companies.find_one(scope_query({"id": contract.get("company_id")}, org_id), {"_id": 0})
    contract["company_name"] = company.get("name") if company else "Unknown"
    
    # Get covered assets based on mapping type
    asset_mapping = contract.get("asset_mapping", {})
    mapping_type = asset_mapping.get("mapping_type", "all_company")
    
    if mapping_type == "all_company":
        assets = await db.devices.find(
            {"company_id": contract["company_id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(1000)
    elif mapping_type == "selected_assets":
        asset_ids = asset_mapping.get("selected_asset_ids", [])
        assets = await db.devices.find(
            {"id": {"$in": asset_ids}, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(1000)
    elif mapping_type == "device_types":
        device_types = asset_mapping.get("selected_device_types", [])
        assets = await db.devices.find(
            {"company_id": contract["company_id"], "device_type": {"$in": device_types}, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(1000)
    else:
        assets = []
    
    contract["covered_assets"] = assets
    contract["covered_assets_count"] = len(assets)
    
    # Get usage history
    usage = await db.amc_usage.find({"amc_contract_id": contract_id}, {"_id": 0}).to_list(100)
    contract["usage_history"] = usage
    
    # Calculate usage stats
    onsite_count = len([u for u in usage if u.get("usage_type") == "onsite_visit"])
    remote_count = len([u for u in usage if u.get("usage_type") == "remote_support"])
    pm_count = len([u for u in usage if u.get("usage_type") == "preventive_maintenance"])
    
    contract["usage_stats"] = {
        "onsite_visits_used": onsite_count,
        "remote_support_used": remote_count,
        "preventive_maintenance_used": pm_count
    }
    
    return contract

@api_router.put("/admin/amc-contracts/{contract_id}")
async def update_amc_contract(contract_id: str, updates: AMCContractUpdate, admin: dict = Depends(get_current_admin)):
    """Update AMC contract"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.amc_contracts.find_one(scope_query({"id": contract_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    await db.amc_contracts.update_one(scope_query({"id": contract_id}, org_id), {"$set": update_data})
    await log_audit("amc_contract", contract_id, "update", changes, admin)
    
    result = await db.amc_contracts.find_one(scope_query({"id": contract_id}, org_id), {"_id": 0})
    result["status"] = get_amc_status(result.get("start_date", ""), result.get("end_date", ""))
    return result

@api_router.delete("/admin/amc-contracts/{contract_id}")
async def delete_amc_contract(contract_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete AMC contract"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.amc_contracts.update_one(scope_query({"id": contract_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    await log_audit("amc_contract", contract_id, "delete", {"is_deleted": True}, admin)
    return {"message": "AMC Contract archived"}

@api_router.post("/admin/amc-contracts/{contract_id}/usage")
async def record_amc_usage(
    contract_id: str,
    usage_type: str = Query(..., description="onsite_visit, remote_support, preventive_maintenance"),
    service_id: Optional[str] = None,
    notes: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """Record usage against AMC contract"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    contract = await db.amc_contracts.find_one(scope_query({"id": contract_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    usage = AMCUsageRecord(
        amc_contract_id=contract_id,
        service_id=service_id,
        usage_type=usage_type,
        usage_date=get_ist_isoformat(),
        notes=notes
    )
    
    usage_ins_dict["organization_id"] = org_id
    usage_ins_dict = usage.model_dump()
    await db.amc_usage.insert_one(usage_ins_dict)
    return usage.model_dump()

@api_router.get("/admin/amc-contracts/check-coverage/{device_id}")
async def check_amc_coverage(device_id: str, admin: dict = Depends(get_current_admin)):
    """Check if a device is covered under any active AMC"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    device = await db.devices.find_one(scope_query({"id": device_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    company_id = device.get("company_id")
    device_type = device.get("device_type")
    
    # Find all active AMC contracts for this company
    contracts = await db.amc_contracts.find(
        {"company_id": company_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)
    
    covered_contracts = []
    for contract in contracts:
        status = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
        if status != "active":
            continue
        
        asset_mapping = contract.get("asset_mapping", {})
        mapping_type = asset_mapping.get("mapping_type", "all_company")
        
        is_covered = False
        if mapping_type == "all_company":
            is_covered = True
        elif mapping_type == "selected_assets":
            is_covered = device_id in asset_mapping.get("selected_asset_ids", [])
        elif mapping_type == "device_types":
            is_covered = device_type in asset_mapping.get("selected_device_types", [])
        
        if is_covered:
            covered_contracts.append({
                "contract_id": contract["id"],
                "contract_name": contract["name"],
                "amc_type": contract.get("amc_type"),
                "coverage_includes": contract.get("coverage_includes"),
                "exclusions": contract.get("exclusions"),
                "end_date": contract.get("end_date"),
                "days_until_expiry": get_days_until_expiry(contract.get("end_date", ""))
            })
    
    return {
        "device_id": device_id,
        "device_info": f"{device.get('brand')} {device.get('model')} ({device.get('serial_number')})",
        "is_covered": len(covered_contracts) > 0,
        "active_contracts": covered_contracts
    }

@api_router.get("/admin/companies-without-amc")
async def get_companies_without_amc(admin: dict = Depends(get_current_admin)):
    """Get list of companies without any active AMC"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Get all companies
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    
    companies_without_amc = []
    for company in companies:
        # Check if company has any active AMC
        contracts = await db.amc_contracts.find(
            {"company_id": company["id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(10)
        
        has_active_amc = False
        for contract in contracts:
            if get_amc_status(contract.get("start_date", ""), contract.get("end_date", "")) == "active":
                has_active_amc = True
                break
        
        if not has_active_amc:
            companies_without_amc.append({
                "id": company["id"],
                "name": company.get("name"),
                "contact_email": company.get("contact_email")
            })
    
    return companies_without_amc

# ==================== ADMIN ENDPOINTS - SITES ====================

@api_router.get("/admin/sites")
async def list_sites(
    company_id: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List all sites with optional search support"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"city": search_regex},
            {"address": search_regex}
        ]
    
    skip = (page - 1) * limit
    sites = await db.sites.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with company names and counts
    for site in sites:
        company = await db.companies.find_one({"id": site.get("company_id")}, {"_id": 0, "name": 1})
        site["company_name"] = company.get("name") if company else "Unknown"
        site.get("label", site.get("name", "Unknown")) or site.get("name", "Unknown"); site["label"] = site.get("name", "Unknown")  # SmartSelect compatibility
        
        # Count deployments and items
        deployments = await db.deployments.find(
            {"site_id": site["id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(100)
        site["deployments_count"] = len(deployments)
        
        # Count total items across deployments
        total_items = sum(len(d.get("items", [])) for d in deployments)
        site["items_count"] = total_items
    
    return sites

@api_router.post("/admin/sites")
async def create_site(data: SiteCreate, admin: dict = Depends(get_current_admin)):
    """Create new site"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    company_query = {"id": data.company_id, "is_deleted": {"$ne": True}}
    company_query = scope_query(company_query, org_id)
    
    company = await db.companies.find_one(company_query, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    site_dict = data.model_dump()
    if org_id:
        site_dict["organization_id"] = org_id
    
    site = Site(**site_dict)
    await db.sites.insert_one(site.model_dump())
    await log_audit("site", site.id, "create", {"data": data.model_dump()}, admin)
    
    result = site.model_dump()
    result["company_name"] = company.get("name")
    result.get("label", result.get("name", "Unknown")) or result.get("name", "Unknown"); result["label"] = result.get("name", "Unknown")
    return result

@api_router.post("/admin/sites/quick-create")
async def quick_create_site(data: SiteCreate, admin: dict = Depends(get_current_admin)):
    """Quick create site (for inline creation from dropdowns)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Validate company exists
    company = await db.companies.find_one(scope_query({"id": data.company_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if site with same name exists for this company
    existing = await db.sites.find_one(
        {"name": {"$regex": f"^{data.name}$", "$options": "i"}, "company_id": data.company_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if existing:
        existing.get("label", existing.get("name", "Unknown")) or existing.get("name", "Unknown"); existing["label"] = existing.get("name", "Unknown")
        existing["company_name"] = company.get("name")
        return existing
    
    site = Site(**data.model_dump())
    site_dict = site.model_dump()
    org_id = admin.get("organization_id")
    if org_id:
        site_dict["organization_id"] = org_id
    await db.sites.insert_one(site_dict)
    await log_audit("site", site.id, "quick_create", {"data": data.model_dump()}, admin)
    
    result = {k: v for k, v in site_dict.items() if k != "_id"}
    result["company_name"] = company.get("name")
    result["label"] = result.get("name", "Unknown")
    return result

@api_router.get("/admin/sites/{site_id}")
async def get_site(site_id: str, admin: dict = Depends(get_current_admin)):
    """Get site with full details including deployments"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    site = await db.sites.find_one(scope_query({"id": site_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Get company
    company = await db.companies.find_one(scope_query({"id": site.get("company_id")}, org_id), {"_id": 0})
    site["company_name"] = company.get("name") if company else "Unknown"
    
    # Get deployments
    deployments = await db.deployments.find(
        {"site_id": site_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)
    site["deployments"] = deployments
    
    # Aggregate all items
    all_items = []
    for deployment in deployments:
        for item in deployment.get("items", []):
            item["deployment_id"] = deployment["id"]
            item["deployment_name"] = deployment["name"]
            all_items.append(item)
    site["all_items"] = all_items
    
    # Get active AMCs for this site
    amc_contracts = await db.amc_contracts.find(
        {"company_id": site["company_id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(100)
    
    active_amcs = []
    for contract in amc_contracts:
        status = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
        if status == "active":
            # Check if AMC covers this site
            asset_mapping = contract.get("asset_mapping", {})
            mapping_type = asset_mapping.get("mapping_type", "all_company")
            
            if mapping_type == "all_company":
                active_amcs.append(contract)
            # Could add site-specific AMC mapping here in future
    
    site["active_amcs"] = active_amcs
    
    return site

@api_router.put("/admin/sites/{site_id}")
async def update_site(site_id: str, updates: SiteUpdate, admin: dict = Depends(get_current_admin)):
    """Update site"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.sites.find_one(scope_query({"id": site_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Site not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    await db.sites.update_one(scope_query({"id": site_id}, org_id), {"$set": update_data})
    await log_audit("site", site_id, "update", changes, admin)
    
    return await db.sites.find_one(scope_query({"id": site_id}, org_id), {"_id": 0})

@api_router.delete("/admin/sites/{site_id}")
async def delete_site(site_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete site"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.sites.update_one(scope_query({"id": site_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Site not found")
    await log_audit("site", site_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Site archived"}

# ==================== ADMIN ENDPOINTS - DEPLOYMENTS ====================

@api_router.get("/admin/deployments")
async def list_deployments(
    company_id: Optional[str] = None,
    site_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all deployments"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    if site_id:
        query["site_id"] = site_id
    
    deployments = await db.deployments.find(query, {"_id": 0}).to_list(1000)
    
    # Enrich with company and site names
    for deployment in deployments:
        company = await db.companies.find_one({"id": deployment.get("company_id")}, {"_id": 0, "name": 1})
        site = await db.sites.find_one({"id": deployment.get("site_id")}, {"_id": 0, "name": 1})
        deployment["company_name"] = company.get("name") if company else "Unknown"
        deployment["site_name"] = site.get("name") if site else "Unknown"
        deployment["items_count"] = len(deployment.get("items", []))
    
    return deployments

@api_router.post("/admin/deployments")
async def create_deployment(data: DeploymentCreate, admin: dict = Depends(get_current_admin)):
    """Create new deployment with items"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Validate company and site
    company = await db.companies.find_one(scope_query({"id": data.company_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    site = await db.sites.find_one(scope_query({"id": data.site_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # Process items - create devices for serialized items
    processed_items = []
    for item_data in data.items:
        item = DeploymentItem(**item_data)
        
        # For serialized items, create device records
        if item.is_serialized and item.serial_numbers:
            linked_device_ids = []
            for serial in item.serial_numbers:
                device_data = {
                    "id": str(uuid.uuid4()),
                    "company_id": data.company_id,
                    "site_id": data.site_id,
                    "deployment_id": "",  # Will be updated after deployment is created
                    "device_type": item.category,
                    "brand": item.brand or "Unknown",
                    "model": item.model or "Unknown",
                    "serial_number": serial,
                    "purchase_date": item.installation_date or data.deployment_date,
                    "warranty_end_date": item.warranty_end_date,
                    "location": item.zone_location,
                    "status": "active",
                    "condition": "new",
                    "is_deleted": False,
                    "created_at": get_ist_isoformat()
                }
                linked_device_ids.append(device_data["id"])
            
            item.linked_device_ids = linked_device_ids
        
        processed_items.append(item.model_dump())
    
    # Create deployment
    deployment = Deployment(
        company_id=data.company_id,
        site_id=data.site_id,
        name=data.name,
        deployment_date=data.deployment_date,
        installed_by=data.installed_by,
        notes=data.notes,
        items=processed_items,
        created_by=admin.get("id", ""),
        created_by_name=admin.get("name", "Admin")
    )
    
    deployment_ins_dict["organization_id"] = org_id
    deployment_ins_dict = deployment.model_dump()
    await db.deployments.insert_one(deployment_ins_dict)
    
    # Now create the device records for serialized items
    for item_idx, item in enumerate(processed_items):
        if item.get("is_serialized") and item.get("serial_numbers"):
            for i, serial in enumerate(item["serial_numbers"]):
                device_id = item["linked_device_ids"][i] if i < len(item.get("linked_device_ids", [])) else str(uuid.uuid4())
                device_data = {
                    "id": device_id,
                    "company_id": data.company_id,
                    "site_id": data.site_id,
                    "deployment_id": deployment.id,
                    "deployment_item_index": item_idx,
                    "source": "deployment",
                    "device_type": item.get("category"),
                    "brand": item.get("brand") or "Unknown",
                    "model": item.get("model") or "Unknown",
                    "serial_number": serial,
                    "purchase_date": item.get("installation_date") or data.deployment_date,
                    "warranty_end_date": item.get("warranty_end_date"),
                    "location": item.get("zone_location"),
                    "status": "active",
                    "condition": "new",
                    "is_deleted": False,
                    "created_at": get_ist_isoformat()
                }
                device_data["organization_id"] = org_id
                await db.devices.insert_one(device_data)
    
    await log_audit("deployment", deployment.id, "create", {"data": data.model_dump()}, admin)
    
    result = deployment.model_dump()
    result["company_name"] = company.get("name")
    result["site_name"] = site.get("name")
    result["items_count"] = len(processed_items)
    return result

@api_router.get("/admin/deployments/{deployment_id}")
async def get_deployment(deployment_id: str, admin: dict = Depends(get_current_admin)):
    """Get deployment with full details"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    deployment = await db.deployments.find_one(scope_query({"id": deployment_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Get company and site
    company = await db.companies.find_one(scope_query({"id": deployment.get("company_id")}, org_id), {"_id": 0})
    site = await db.sites.find_one(scope_query({"id": deployment.get("site_id")}, org_id), {"_id": 0})
    deployment["company_name"] = company.get("name") if company else "Unknown"
    deployment["site_name"] = site.get("name") if site else "Unknown"
    
    # Enrich items with AMC coverage info
    for item in deployment.get("items", []):
        if item.get("amc_contract_id"):
            amc = await db.amc_contracts.find_one(scope_query({"id": item["amc_contract_id"]}, org_id), {"_id": 0, "name": 1})
            item["amc_name"] = amc.get("name") if amc else None
        
        # Check if covered by any active AMC
        amc_contracts = await db.amc_contracts.find(
            {"company_id": deployment["company_id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(10)
        
        is_amc_covered = False
        covering_amc = None
        for contract in amc_contracts:
            status = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
            if status == "active":
                mapping = contract.get("asset_mapping", {})
                if mapping.get("mapping_type") == "all_company":
                    is_amc_covered = True
                    covering_amc = contract.get("name")
                    break
                elif mapping.get("mapping_type") == "device_types":
                    if item.get("category") in mapping.get("selected_device_types", []):
                        is_amc_covered = True
                        covering_amc = contract.get("name")
                        break
        
        item["is_amc_covered"] = is_amc_covered
        item["covering_amc"] = covering_amc
    
    return deployment

@api_router.put("/admin/deployments/{deployment_id}")
async def update_deployment(deployment_id: str, updates: DeploymentUpdate, admin: dict = Depends(get_current_admin)):
    """Update deployment"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.deployments.find_one(scope_query({"id": deployment_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.deployments.update_one(scope_query({"id": deployment_id}, org_id), {"$set": update_data})
    await log_audit("deployment", deployment_id, "update", update_data, admin)
    
    return await db.deployments.find_one(scope_query({"id": deployment_id}, org_id), {"_id": 0})

@api_router.delete("/admin/deployments/{deployment_id}")
async def delete_deployment(deployment_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete deployment and linked devices"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.deployments.update_one(scope_query({"id": deployment_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    # Also soft-delete devices created from this deployment
    await db.devices.update_many(
        {"deployment_id": deployment_id, "source": "deployment"},
        {"$set": {"is_deleted": True}}
    )
    
    await log_audit("deployment", deployment_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Deployment and linked devices archived"}

@api_router.post("/admin/deployments/{deployment_id}/items")
async def add_deployment_item(deployment_id: str, item_data: dict, admin: dict = Depends(get_current_admin)):
    """Add item to existing deployment"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    deployment = await db.deployments.find_one(scope_query({"id": deployment_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    item = DeploymentItem(**item_data)
    
    # Handle serialized items
    if item.is_serialized and item.serial_numbers:
        linked_device_ids = []
        for serial in item.serial_numbers:
            device_data = {
                "id": str(uuid.uuid4()),
                "company_id": deployment["company_id"],
                "site_id": deployment["site_id"],
                "deployment_id": deployment_id,
                "source": "deployment",
                "device_type": item.category,
                "category": item.category,
                "brand": item.brand or "Unknown",
                "model": item.model or "Unknown",
                "serial_number": serial,
                "purchase_date": item.installation_date or deployment["deployment_date"],
                "warranty_end_date": item.warranty_end_date,
                "location": item.zone_location,
                "status": "active",
                "condition": "new",
                "is_deleted": False,
                "created_at": get_ist_isoformat()
            }
            device_data["organization_id"] = org_id
            await db.devices.insert_one(device_data)
            linked_device_ids.append(device_data["id"])
        
        item.linked_device_ids = linked_device_ids
    
    # Add item to deployment
    await db.deployments.update_one(
        {"id": deployment_id},
        {
            "$push": {"items": item.model_dump()},
            "$set": {"updated_at": get_ist_isoformat()}
        }
    )
    
    return item.model_dump()

@api_router.put("/admin/deployments/{deployment_id}/items/{item_index}")
async def update_deployment_item(
    deployment_id: str, 
    item_index: int, 
    item_data: dict, 
    admin: dict = Depends(get_current_admin)
):
    """Update an item in a deployment and sync changes to devices"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    deployment = await db.deployments.find_one(scope_query({"id": deployment_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    items = deployment.get("items", [])
    if item_index < 0 or item_index >= len(items):
        raise HTTPException(status_code=404, detail="Item not found")
    
    old_item = items[item_index]
    
    # Merge updates with existing item
    updated_item = {**old_item, **{k: v for k, v in item_data.items() if v is not None}}
    
    # Handle serial number changes - sync to devices
    new_serials = item_data.get("serial_numbers", [])
    old_serials = old_item.get("serial_numbers", [])
    old_linked_ids = old_item.get("linked_device_ids", [])
    
    # If serial numbers are being added/updated
    if new_serials and updated_item.get("is_serialized"):
        new_linked_ids = []
        
        for i, serial in enumerate(new_serials):
            if serial:  # Only process non-empty serial numbers
                # Check if this serial was already linked to a device
                if i < len(old_linked_ids) and old_linked_ids[i]:
                    # Update existing device
                    device_id = old_linked_ids[i]
                    await db.devices.update_one(
                        {"id": device_id},
                        {"$set": {
                            "serial_number": serial,
                            "device_type": updated_item.get("category"),
                            "category": updated_item.get("category"),
                            "brand": updated_item.get("brand") or "Unknown",
                            "model": updated_item.get("model") or "Unknown",
                            "warranty_end_date": updated_item.get("warranty_end_date"),
                            "location": updated_item.get("zone_location"),
                            "updated_at": get_ist_isoformat()
                        }}
                    )
                    new_linked_ids.append(device_id)
                else:
                    # Create new device for this serial
                    device_data = {
                        "id": str(uuid.uuid4()),
                        "company_id": deployment["company_id"],
                        "site_id": deployment["site_id"],
                        "deployment_id": deployment_id,
                        "deployment_item_index": item_index,
                        "source": "deployment",
                        "device_type": updated_item.get("category"),
                        "category": updated_item.get("category"),
                        "brand": updated_item.get("brand") or "Unknown",
                        "model": updated_item.get("model") or "Unknown",
                        "serial_number": serial,
                        "purchase_date": updated_item.get("installation_date") or deployment["deployment_date"],
                        "warranty_end_date": updated_item.get("warranty_end_date"),
                        "location": updated_item.get("zone_location"),
                        "status": "active",
                        "condition": "new",
                        "is_deleted": False,
                        "created_at": get_ist_isoformat()
                    }
                    device_data["organization_id"] = org_id
                    await db.devices.insert_one(device_data)
                    new_linked_ids.append(device_data["id"])
        
        updated_item["linked_device_ids"] = new_linked_ids
        updated_item["serial_numbers"] = new_serials
    
    # Update the item in deployment
    items[item_index] = updated_item
    await db.deployments.update_one(
        {"id": deployment_id},
        {"$set": {
            "items": items,
            "updated_at": get_ist_isoformat()
        }}
    )
    
    await log_audit("deployment", deployment_id, "update_item", {"item_index": item_index, "updates": item_data}, admin)
    
    return {"message": "Item updated successfully", "item": updated_item}

@api_router.post("/admin/deployments/{deployment_id}/sync-devices")
async def sync_deployment_devices(deployment_id: str, admin: dict = Depends(get_current_admin)):
    """Manually sync deployment items to devices collection"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    deployment = await db.deployments.find_one(scope_query({"id": deployment_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not deployment:
        raise HTTPException(status_code=404, detail="Deployment not found")
    
    created_count = 0
    updated_count = 0
    
    for item_idx, item in enumerate(deployment.get("items", [])):
        if item.get("is_serialized") and item.get("serial_numbers"):
            linked_ids = item.get("linked_device_ids", [])
            new_linked_ids = []
            
            for i, serial in enumerate(item["serial_numbers"]):
                if not serial:  # Skip empty serials
                    continue
                    
                # Check if device already exists for this serial in this deployment
                existing_device = await db.devices.find_one({
                    "deployment_id": deployment_id,
                    "serial_number": serial,
                    "is_deleted": {"$ne": True}
                }, {"_id": 0})
                
                if existing_device:
                    # Update existing device
                    await db.devices.update_one(
                        {"id": existing_device["id"]},
                        {"$set": {
                            "device_type": item.get("category"),
                            "category": item.get("category"),
                            "brand": item.get("brand") or "Unknown",
                            "model": item.get("model") or "Unknown",
                            "warranty_end_date": item.get("warranty_end_date"),
                            "location": item.get("zone_location"),
                            "updated_at": get_ist_isoformat()
                        }}
                    )
                    new_linked_ids.append(existing_device["id"])
                    updated_count += 1
                else:
                    # Create new device
                    device_data = {
                        "id": str(uuid.uuid4()),
                        "company_id": deployment["company_id"],
                        "site_id": deployment["site_id"],
                        "deployment_id": deployment_id,
                        "deployment_item_index": item_idx,
                        "source": "deployment",
                        "device_type": item.get("category"),
                        "category": item.get("category"),
                        "brand": item.get("brand") or "Unknown",
                        "model": item.get("model") or "Unknown",
                        "serial_number": serial,
                        "purchase_date": item.get("installation_date") or deployment.get("deployment_date"),
                        "warranty_end_date": item.get("warranty_end_date"),
                        "location": item.get("zone_location"),
                        "status": "active",
                        "condition": "new",
                        "is_deleted": False,
                        "created_at": get_ist_isoformat()
                    }
                    device_data["organization_id"] = org_id
                    await db.devices.insert_one(device_data)
                    new_linked_ids.append(device_data["id"])
                    created_count += 1
            
            # Update linked_device_ids in deployment item
            if new_linked_ids:
                await db.deployments.update_one(
                    {"id": deployment_id},
                    {"$set": {f"items.{item_idx}.linked_device_ids": new_linked_ids}}
                )
    
    return {
        "message": f"Sync complete. Created {created_count} devices, updated {updated_count} devices.",
        "created": created_count,
        "updated": updated_count
    }

# ==================== UNIVERSAL SEARCH ====================

@api_router.get("/search")
async def universal_search(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(5, ge=1, le=10, description="Results per category"),
    admin: dict = Depends(get_current_admin)
):
    """
    Universal search across all entities with smart synonym support.
    Returns grouped results from companies, sites, users, assets, deployments, AMCs, and services.
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    from utils.synonyms import expand_search_query, get_brand_variants
    
    if not q or len(q.strip()) < 1:
        return {
            "companies": [],
            "sites": [],
            "users": [],
            "assets": [],
            "deployments": [],
            "amcs": [],
            "services": []
        }
    
    query = q.strip()
    # Create case-insensitive regex pattern for partial matching
    regex_pattern = {"$regex": query, "$options": "i"}
    
    # Get synonym-expanded search for device types
    synonym_regex = expand_search_query(query)
    
    # Get brand variants
    brand_variants = get_brand_variants(query)
    brand_regex = {"$regex": "|".join(brand_variants), "$options": "i"}
    
    results = {
        "companies": [],
        "sites": [],
        "users": [],
        "assets": [],
        "deployments": [],
        "amcs": [],
        "services": [],
        "query": query,
        "total_count": 0
    }
    
    # Search Companies
    companies = await db.companies.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"contact_email": regex_pattern},
            {"gst_number": regex_pattern},
            {"address": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for c in companies:
        results["companies"].append({
            "id": c["id"],
            "type": "company",
            "title": c.get("name"),
            "subtitle": c.get("contact_email") or c.get("address", ""),
            "link": f"/admin/companies",
            "icon": "building"
        })
    
    # Search Sites
    sites = await db.sites.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"address": regex_pattern},
            {"city": regex_pattern},
            {"primary_contact_name": regex_pattern},
            {"contact_number": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for s in sites:
        company = await db.companies.find_one(scope_query({"id": s.get("company_id")}, org_id), {"_id": 0, "name": 1})
        results["sites"].append({
            "id": s["id"],
            "type": "site",
            "title": s.get("name"),
            "subtitle": f"{s.get('city', '')} • {company.get('name', '') if company else ''}",
            "link": f"/admin/sites",
            "icon": "map-pin"
        })
    
    # Search Users
    users = await db.users.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"email": regex_pattern},
            {"phone": regex_pattern},
            {"designation": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for u in users:
        results["users"].append({
            "id": u["id"],
            "type": "user",
            "title": u.get("name"),
            "subtitle": u.get("email") or u.get("phone", ""),
            "link": f"/admin/users",
            "icon": "user"
        })
    
    # Search Assets/Devices with synonym support
    devices = await db.devices.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"serial_number": regex_pattern},
            {"asset_tag": regex_pattern},
            {"brand": brand_regex},  # Brand with aliases
            {"model": regex_pattern},
            {"device_type": synonym_regex},  # Device type with synonyms
            {"location": regex_pattern},
            {"notes": synonym_regex}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for d in devices:
        company = await db.companies.find_one(scope_query({"id": d.get("company_id")}, org_id), {"_id": 0, "name": 1})
        results["assets"].append({
            "id": d["id"],
            "type": "asset",
            "title": f"{d.get('brand', '')} {d.get('model', '')}".strip() or d.get("serial_number"),
            "subtitle": f"S/N: {d.get('serial_number', '')} • {company.get('name', '') if company else ''}",
            "link": f"/admin/devices",
            "icon": "laptop",
            "serial_number": d.get("serial_number"),
            "asset_tag": d.get("asset_tag")
        })
    
    # Search Deployments
    deployments = await db.deployments.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"installed_by": regex_pattern},
            {"notes": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    # Also search deployment items for serial numbers and categories
    deployment_items_search = await db.deployments.find({
        "is_deleted": {"$ne": True},
        "items": {
            "$elemMatch": {
                "$or": [
                    {"serial_numbers": regex_pattern},
                    {"category": regex_pattern},
                    {"brand": regex_pattern},
                    {"model": regex_pattern}
                ]
            }
        }
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    # Combine and dedupe
    all_deployments = {d["id"]: d for d in deployments}
    for d in deployment_items_search:
        if d["id"] not in all_deployments:
            all_deployments[d["id"]] = d
    
    for d in list(all_deployments.values())[:limit]:
        site = await db.sites.find_one(scope_query({"id": d.get("site_id")}, org_id), {"_id": 0, "name": 1})
        results["deployments"].append({
            "id": d["id"],
            "type": "deployment",
            "title": d.get("name"),
            "subtitle": f"{site.get('name', '') if site else ''} • {len(d.get('items', []))} items",
            "link": f"/admin/deployments",
            "icon": "package"
        })
    
    # Search AMC Contracts
    amcs = await db.amc_contracts.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"name": regex_pattern},
            {"amc_type": regex_pattern},
            {"internal_notes": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for a in amcs:
        company = await db.companies.find_one(scope_query({"id": a.get("company_id")}, org_id), {"_id": 0, "name": 1})
        status = get_amc_status(a.get("start_date", ""), a.get("end_date", ""))
        results["amcs"].append({
            "id": a["id"],
            "type": "amc",
            "title": a.get("name"),
            "subtitle": f"{company.get('name', '') if company else ''} • {status.capitalize()}",
            "link": f"/admin/amc-contracts",
            "icon": "file-text",
            "status": status
        })
    
    # Search Service History
    services = await db.service_history.find({
        "is_deleted": {"$ne": True},
        "$or": [
            {"ticket_id": regex_pattern},
            {"action_taken": regex_pattern},
            {"problem_reported": regex_pattern},
            {"technician_name": regex_pattern},
            {"notes": regex_pattern}
        ]
    }, {"_id": 0}).limit(limit).to_list(limit)
    
    for s in services:
        device = await db.devices.find_one(scope_query({"id": s.get("device_id")}, org_id), {"_id": 0, "brand": 1, "model": 1, "serial_number": 1})
        results["services"].append({
            "id": s["id"],
            "type": "service",
            "title": s.get("action_taken", "")[:50] + ("..." if len(s.get("action_taken", "")) > 50 else ""),
            "subtitle": f"{device.get('brand', '')} {device.get('model', '')} • {s.get('service_type', '')}".strip() if device else s.get("service_type", ""),
            "link": f"/admin/service-history",
            "icon": "wrench",
            "ticket_id": s.get("ticket_id")
        })
    
    # Calculate total count
    results["total_count"] = (
        len(results["companies"]) +
        len(results["sites"]) +
        len(results["users"]) +
        len(results["assets"]) +
        len(results["deployments"]) +
        len(results["amcs"]) +
        len(results["services"])
    )
    
    return results

# ==================== ADMIN ENDPOINTS - SETTINGS ====================

@api_router.get("/admin/settings")
async def get_settings(admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    settings = await db.settings.find_one(scope_query({"id": "settings"}, org_id), {"_id": 0})
    if not settings:
        settings = Settings().model_dump()
    return settings

@api_router.put("/admin/settings")
async def update_settings(updates: SettingsUpdate, admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.settings.update_one(
        {"id": "settings"},
        {"$set": update_data},
        upsert=True
    )
    
    return await db.settings.find_one(scope_query({"id": "settings"}, org_id), {"_id": 0})

@api_router.post("/admin/settings/logo")
async def upload_logo(file: UploadFile = File(...), admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    content = await file.read()
    base64_string = base64.b64encode(content).decode()
    logo_base64 = f"data:{file.content_type};base64,{base64_string}"
    
    await db.settings.update_one(
        {"id": "settings"},
        {"$set": {"logo_base64": logo_base64, "updated_at": get_ist_isoformat()}},
        upsert=True
    )
    
    return {"message": "Logo uploaded successfully", "logo_base64": logo_base64}

# ==================== ADMIN ENDPOINTS - LICENSES ====================

def calculate_license_status(end_date: Optional[str], reminder_days: int = 30) -> str:
    """Calculate license status based on end date"""
    if not end_date:
        return "active"  # Perpetual license
    
    try:
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
        today = get_ist_now().date()
        days_until_expiry = (end - today).days
        
        if days_until_expiry < 0:
            return "expired"
        elif days_until_expiry <= reminder_days:
            return "expiring"
        else:
            return "active"
    except Exception:
        return "active"

@api_router.get("/admin/licenses")
async def list_licenses(
    company_id: Optional[str] = None,
    status: Optional[str] = None,
    license_type: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List all licenses with optional filters"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    if license_type:
        query["license_type"] = license_type
    
    # Add search filter
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"software_name": search_regex},
            {"vendor": search_regex},
            {"license_key": search_regex}
        ]
    
    skip = (page - 1) * limit
    licenses = await db.licenses.find(query, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    
    # Enrich with company names and calculate status
    for lic in licenses:
        company = await db.companies.find_one({"id": lic.get("company_id")}, {"_id": 0, "name": 1})
        lic["company_name"] = company.get("name") if company else "Unknown"
        lic["label"] = lic["software_name"]
        
        # Calculate current status
        lic["status"] = calculate_license_status(
            lic.get("end_date"),
            lic.get("renewal_reminder_days", 30)
        )
        
        # Mask license key
        if lic.get("license_key"):
            key = lic["license_key"]
            if len(key) > 8:
                lic["license_key_masked"] = key[:4] + "****" + key[-4:]
            else:
                lic["license_key_masked"] = "****"
    
    # Filter by status if requested (after calculation)
    if status:
        licenses = [lic for lic in licenses if lic["status"] == status]
    
    return licenses

@api_router.post("/admin/licenses")
async def create_license(data: LicenseCreate, admin: dict = Depends(get_current_admin)):
    """Create new license"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    company_query = {"id": data.company_id, "is_deleted": {"$ne": True}}
    company_query = scope_query(company_query, org_id)
    
    company = await db.companies.find_one(company_query, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    license_data = data.model_dump()
    license_data["status"] = calculate_license_status(data.end_date, data.renewal_reminder_days)
    if org_id:
        license_data["organization_id"] = org_id
    
    lic = License(**license_data)
    await db.licenses.insert_one(lic.model_dump())
    await log_audit("license", lic.id, "create", {"data": data.model_dump()}, admin)
    
    result = lic.model_dump()
    result["company_name"] = company.get("name")
    result["label"] = result["software_name"]
    return result

@api_router.get("/admin/licenses/{license_id}")
async def get_license(license_id: str, admin: dict = Depends(get_current_admin)):
    """Get license details"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    lic = await db.licenses.find_one(scope_query({"id": license_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not lic:
        raise HTTPException(status_code=404, detail="License not found")
    
    # Get company
    company = await db.companies.find_one(scope_query({"id": lic.get("company_id")}, org_id), {"_id": 0})
    lic["company_name"] = company.get("name") if company else "Unknown"
    
    # Get assigned devices/users details
    if lic.get("assigned_device_ids"):
        devices = await db.devices.find(
            {"id": {"$in": lic["assigned_device_ids"]}, "is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "brand": 1, "model": 1, "serial_number": 1}
        ).to_list(100)
        lic["assigned_devices"] = devices
    
    if lic.get("assigned_user_ids"):
        users = await db.users.find(
            {"id": {"$in": lic["assigned_user_ids"]}, "is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "name": 1, "email": 1}
        ).to_list(100)
        lic["assigned_users"] = users
    
    lic["status"] = calculate_license_status(lic.get("end_date"), lic.get("renewal_reminder_days", 30))
    
    return lic

@api_router.put("/admin/licenses/{license_id}")
async def update_license(license_id: str, updates: LicenseUpdate, admin: dict = Depends(get_current_admin)):
    """Update license"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    existing = await db.licenses.find_one(scope_query({"id": license_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="License not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    # Recalculate status if dates changed
    end_date = update_data.get("end_date", existing.get("end_date"))
    reminder_days = update_data.get("renewal_reminder_days", existing.get("renewal_reminder_days", 30))
    update_data["status"] = calculate_license_status(end_date, reminder_days)
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    await db.licenses.update_one(scope_query({"id": license_id}, org_id), {"$set": update_data})
    await log_audit("license", license_id, "update", changes, admin)
    
    return await db.licenses.find_one(scope_query({"id": license_id}, org_id), {"_id": 0})

@api_router.delete("/admin/licenses/{license_id}")
async def delete_license(license_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete license"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.licenses.update_one(scope_query({"id": license_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="License not found")
    
    await log_audit("license", license_id, "delete", {"is_deleted": True}, admin)
    return {"message": "License deleted"}

@api_router.get("/admin/licenses/expiring/summary")
async def get_expiring_licenses_summary(admin: dict = Depends(get_current_admin)):
    """Get summary of expiring licenses"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    licenses = await db.licenses.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    
    today = get_ist_now().date()
    summary = {
        "total": len(licenses),
        "perpetual": 0,
        "active": 0,
        "expiring_7_days": [],
        "expiring_30_days": [],
        "expired": []
    }
    
    for lic in licenses:
        if not lic.get("end_date"):
            summary["perpetual"] += 1
            continue
        
        try:
            end = datetime.strptime(lic["end_date"], "%Y-%m-%d").date()
            days = (end - today).days
            
            company = await db.companies.find_one(scope_query({"id": lic.get("company_id")}, org_id), {"_id": 0, "name": 1})
            
            item = {
                "id": lic["id"],
                "software_name": lic["software_name"],
                "company_name": company.get("name") if company else "Unknown",
                "end_date": lic["end_date"],
                "days_until_expiry": days,
                "seats": lic.get("seats", 1)
            }
            
            if days < 0:
                summary["expired"].append(item)
            elif days <= 7:
                summary["expiring_7_days"].append(item)
            elif days <= 30:
                summary["expiring_30_days"].append(item)
            else:
                summary["active"] += 1
        except Exception:
            continue
    
    return summary

# ==================== ADMIN ENDPOINTS - AMC DEVICE ASSIGNMENTS ====================

@api_router.get("/admin/amc-contracts/{contract_id}/devices")
async def get_amc_assigned_devices(contract_id: str, admin: dict = Depends(get_current_admin)):
    """Get all devices assigned to an AMC contract"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Verify contract exists
    contract = await db.amc_contracts.find_one(scope_query({"id": contract_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    assignments = await db.amc_device_assignments.find(
        {"amc_contract_id": contract_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Enrich with device details
    for assignment in assignments:
        device = await db.devices.find_one(scope_query({"id": assignment["device_id"]}, org_id), {"_id": 0})
        if device:
            assignment["device_brand"] = device.get("brand")
            assignment["device_model"] = device.get("model")
            assignment["device_serial"] = device.get("serial_number")
            assignment["device_type"] = device.get("device_type")
        
        assignment["status"] = calculate_license_status(assignment.get("coverage_end"))
    
    return {
        "contract": contract,
        "assignments": assignments,
        "total_devices": len(assignments)
    }

@api_router.post("/admin/amc-contracts/{contract_id}/assign-device")
async def assign_device_to_amc(
    contract_id: str,
    data: AMCDeviceAssignmentCreate,
    admin: dict = Depends(get_current_admin)
):
    """Assign a single device to an AMC contract"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Verify contract exists
    contract = await db.amc_contracts.find_one(scope_query({"id": contract_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    # Verify device exists
    device = await db.devices.find_one(scope_query({"id": data.device_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if already assigned
    existing = await db.amc_device_assignments.find_one({
        "amc_contract_id": contract_id,
        "device_id": data.device_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Device already assigned to this contract")
    
    assignment_data = data.model_dump()
    assignment_data["amc_contract_id"] = contract_id
    assignment_data["created_by"] = admin["id"]
    
    assignment = AMCDeviceAssignment(**assignment_data)
    assignment_ins_dict["organization_id"] = org_id
    assignment_ins_dict = assignment.model_dump()
    await db.amc_device_assignments.insert_one(assignment_ins_dict)
    
    return assignment.model_dump()

@api_router.post("/admin/amc-contracts/{contract_id}/bulk-assign/preview")
async def preview_bulk_amc_assignment(
    contract_id: str,
    data: AMCBulkAssignmentPreview,
    admin: dict = Depends(get_current_admin)
):
    """Preview bulk device assignment to AMC - validates before actual assignment"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Verify contract exists
    contract = await db.amc_contracts.find_one(scope_query({"id": contract_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not contract:
        raise HTTPException(status_code=404, detail="AMC Contract not found")
    
    results = {
        "will_be_assigned": [],
        "already_assigned": [],
        "not_found": [],
        "wrong_company": []
    }
    
    contract_company_id = contract.get("company_id")
    
    for identifier in data.device_identifiers:
        identifier = identifier.strip()
        if not identifier:
            continue
        
        # Search by serial number or asset tag
        device = await db.devices.find_one({
            "is_deleted": {"$ne": True},
            "$or": [
                {"serial_number": {"$regex": f"^{identifier}$", "$options": "i"}},
                {"asset_tag": {"$regex": f"^{identifier}$", "$options": "i"}}
            ]
        }, {"_id": 0})
        
        if not device:
            results["not_found"].append({"identifier": identifier, "reason": "Device not found"})
            continue
        
        # Check if device belongs to same company
        if device.get("company_id") != contract_company_id:
            results["wrong_company"].append({
                "identifier": identifier,
                "device_id": device["id"],
                "device_company": device.get("company_id"),
                "reason": "Device belongs to different company"
            })
            continue
        
        # Check if already assigned
        existing = await db.amc_device_assignments.find_one({
            "amc_contract_id": contract_id,
            "device_id": device["id"]
        })
        
        if existing:
            results["already_assigned"].append({
                "identifier": identifier,
                "device_id": device["id"],
                "serial_number": device.get("serial_number"),
                "reason": "Already assigned to this contract"
            })
        else:
            results["will_be_assigned"].append({
                "identifier": identifier,
                "device_id": device["id"],
                "serial_number": device.get("serial_number"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "device_type": device.get("device_type")
            })
    
    results["summary"] = {
        "total_input": len(data.device_identifiers),
        "will_assign": len(results["will_be_assigned"]),
        "already_assigned": len(results["already_assigned"]),
        "not_found": len(results["not_found"]),
        "wrong_company": len(results["wrong_company"])
    }
    
    return results

@api_router.post("/admin/amc-contracts/{contract_id}/bulk-assign/confirm")
async def confirm_bulk_amc_assignment(
    contract_id: str,
    data: AMCBulkAssignmentPreview,
    admin: dict = Depends(get_current_admin)
):
    """Confirm and execute bulk device assignment to AMC"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # First run preview to get valid devices
    preview = await preview_bulk_amc_assignment(contract_id, data, admin)
    
    assigned = []
    for item in preview["will_be_assigned"]:
        assignment_data = {
            "amc_contract_id": contract_id,
            "device_id": item["device_id"],
            "coverage_start": data.coverage_start,
            "coverage_end": data.coverage_end,
            "coverage_source": "bulk_upload",
            "created_by": admin["id"]
        }
        
        assignment = AMCDeviceAssignment(**assignment_data)
        assignment_ins_dict["organization_id"] = org_id
        assignment_ins_dict = assignment.model_dump()
        await db.amc_device_assignments.insert_one(assignment_ins_dict)
        assigned.append(assignment.model_dump())
    
    return {
        "assigned_count": len(assigned),
        "assignments": assigned,
        "skipped": {
            "already_assigned": len(preview["already_assigned"]),
            "not_found": len(preview["not_found"]),
            "wrong_company": len(preview["wrong_company"])
        }
    }

@api_router.delete("/admin/amc-contracts/{contract_id}/devices/{device_id}")
async def unassign_device_from_amc(
    contract_id: str,
    device_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Remove device assignment from AMC contract"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.amc_device_assignments.delete_one({
        "amc_contract_id": contract_id,
        "device_id": device_id
    })
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    return {"message": "Device unassigned from contract"}

# ==================== ADMIN DASHBOARD WITH ALERTS ====================

@api_router.get("/admin/dashboard")
async def get_dashboard_stats(admin: dict = Depends(get_current_admin)):
    org_id = await get_admin_org_id(admin.get("email", ""))
    base = {"is_deleted": {"$ne": True}}
    scoped = scope_query(base.copy(), org_id)
    
    companies_count = await db.companies.count_documents(scoped)
    users_count = await db.users.count_documents(scope_query({"is_deleted": {"$ne": True}}, org_id))
    devices_count = await db.devices.count_documents(scope_query({"is_deleted": {"$ne": True}}, org_id))
    parts_count = await db.parts.count_documents(scope_query({"is_deleted": {"$ne": True}}, org_id))
    services_count = await db.service_history.count_documents(scope_query({}, org_id))
    
    today = get_ist_now().strftime('%Y-%m-%d')
    active_warranties = await db.devices.count_documents(scope_query({
        "is_deleted": {"$ne": True},
        "warranty_end_date": {"$gte": today}
    }, org_id))
    
    active_amc = await db.amc.count_documents(scope_query({
        "is_deleted": {"$ne": True},
        "end_date": {"$gte": today}
    }, org_id))
    
    recent_devices = await db.devices.find(scope_query({"is_deleted": {"$ne": True}}, org_id), {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    recent_services = await db.service_history.find(scope_query({}, org_id), {"_id": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "companies_count": companies_count,
        "users_count": users_count,
        "devices_count": devices_count,
        "parts_count": parts_count,
        "services_count": services_count,
        "active_warranties": active_warranties,
        "expired_warranties": devices_count - active_warranties,
        "active_amc": active_amc,
        "recent_devices": recent_devices,
        "recent_services": recent_services
    }

@api_router.get("/admin/dashboard/alerts")
async def get_dashboard_alerts(admin: dict = Depends(get_current_admin)):
    """Get warranty and AMC expiry alerts"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    today = get_ist_now()
    
    alerts = {
        "warranty_expiring_7_days": [],
        "warranty_expiring_15_days": [],
        "warranty_expiring_30_days": [],
        "amc_expiring_7_days": [],
        "amc_expiring_15_days": [],
        "amc_expiring_30_days": [],
        "devices_in_repair": [],
        "devices_lost": []
    }
    
    # Get all devices with warranty - SCOPED
    devices = await db.devices.find(
        scope_query({"is_deleted": {"$ne": True}, "warranty_end_date": {"$ne": None}}, org_id),
        {"_id": 0}
    ).to_list(1000)
    
    for device in devices:
        days = days_until_expiry(device.get("warranty_end_date", ""))
        if 0 < days <= 7:
            alerts["warranty_expiring_7_days"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "expiry_date": device.get("warranty_end_date"),
                "days_remaining": days
            })
        elif 7 < days <= 15:
            alerts["warranty_expiring_15_days"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "expiry_date": device.get("warranty_end_date"),
                "days_remaining": days
            })
        elif 15 < days <= 30:
            alerts["warranty_expiring_30_days"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number"),
                "expiry_date": device.get("warranty_end_date"),
                "days_remaining": days
            })
        
        # Status alerts
        if device.get("status") == "in_repair":
            alerts["devices_in_repair"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number")
            })
        elif device.get("status") == "lost":
            alerts["devices_lost"].append({
                "device_id": device.get("id"),
                "brand": device.get("brand"),
                "model": device.get("model"),
                "serial_number": device.get("serial_number")
            })
    
    # AMC alerts - SCOPED
    amc_list = await db.amc.find(scope_query({"is_deleted": {"$ne": True}}, org_id), {"_id": 0}).to_list(1000)
    for amc in amc_list:
        days = days_until_expiry(amc.get("end_date", ""))
        device = await db.devices.find_one({"id": amc.get("device_id")}, {"_id": 0, "brand": 1, "model": 1, "serial_number": 1})
        if not device:
            continue
            
        alert_item = {
            "amc_id": amc.get("id"),
            "device_id": amc.get("device_id"),
            "brand": device.get("brand"),
            "model": device.get("model"),
            "serial_number": device.get("serial_number"),
            "expiry_date": amc.get("end_date"),
            "days_remaining": days
        }
        
        if 0 < days <= 7:
            alerts["amc_expiring_7_days"].append(alert_item)
        elif 7 < days <= 15:
            alerts["amc_expiring_15_days"].append(alert_item)
        elif 15 < days <= 30:
            alerts["amc_expiring_30_days"].append(alert_item)
    
    # AMC Contract (v2) alerts
    alerts["amc_contracts_expiring_7_days"] = []
    alerts["amc_contracts_expiring_15_days"] = []
    alerts["amc_contracts_expiring_30_days"] = []
    alerts["companies_without_amc"] = []
    
    contracts = await db.amc_contracts.find(scope_query({"is_deleted": {"$ne": True}}, org_id), {"_id": 0}).to_list(1000)
    for contract in contracts:
        days = days_until_expiry(contract.get("end_date", ""))
        company = await db.companies.find_one({"id": contract.get("company_id")}, {"_id": 0, "name": 1})
        
        alert_item = {
            "contract_id": contract.get("id"),
            "contract_name": contract.get("name"),
            "company_id": contract.get("company_id"),
            "company_name": company.get("name") if company else "Unknown",
            "amc_type": contract.get("amc_type"),
            "expiry_date": contract.get("end_date"),
            "days_remaining": days
        }
        
        if 0 < days <= 7:
            alerts["amc_contracts_expiring_7_days"].append(alert_item)
        elif 7 < days <= 15:
            alerts["amc_contracts_expiring_15_days"].append(alert_item)
        elif 15 < days <= 30:
            alerts["amc_contracts_expiring_30_days"].append(alert_item)
    
    # Companies without any active AMC contract - SCOPED
    companies = await db.companies.find(scope_query({"is_deleted": {"$ne": True}}, org_id), {"_id": 0}).to_list(1000)
    for company in companies:
        has_active_contract = False
        for contract in contracts:
            if contract.get("company_id") == company["id"]:
                status = get_amc_status(contract.get("start_date", ""), contract.get("end_date", ""))
                if status == "active":
                    has_active_contract = True
                    break
        
        if not has_active_contract:
            alerts["companies_without_amc"].append({
                "company_id": company["id"],
                "company_name": company.get("name"),
                "contact_email": company.get("contact_email")
            })
    
    return alerts

# ==================== ENGINEER PORTAL ENDPOINTS ====================

from models.engineer import Engineer, EngineerCreate, EngineerUpdate, EngineerLogin
from services.auth import get_current_engineer

# --- Engineer Auth ---

@api_router.post("/engineer/auth/login")
@limiter.limit(RATE_LIMITS["login"])
async def engineer_login(request: Request, login: EngineerLogin):
    """Engineer login with rate limiting (5 attempts/minute per IP)"""
    # First check the legacy engineers collection
    engineer = await db.engineers.find_one(
        {"email": login.email, "is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if engineer and verify_password(login.password, engineer["password_hash"]):
        token = create_access_token(data={"sub": engineer["id"], "type": "engineer"})
        return {
            "access_token": token,
            "token_type": "bearer",
            "engineer": {
                "id": engineer["id"],
                "name": engineer["name"],
                "email": engineer["email"],
                "phone": engineer.get("phone")
            }
        }
    
    # Check staff_users - any active staff with password can login as engineer/technician
    staff_user = await db.staff_users.find_one(
        {"email": login.email, "state": "active", "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    
    if staff_user and staff_user.get("password_hash") and verify_password(login.password, staff_user["password_hash"]):
        # Allow any staff user to login to engineer portal (they can view their assigned visits)
        token = create_access_token(data={"sub": staff_user["id"], "type": "engineer", "staff_user": True})
        return {
            "access_token": token,
            "token_type": "bearer",
            "engineer": {
                "id": staff_user["id"],
                "name": staff_user["name"],
                "email": staff_user["email"],
                "phone": staff_user.get("phone")
            }
        }
    
    raise HTTPException(status_code=401, detail="Invalid email or password")


@api_router.get("/engineer/me")
async def get_engineer_profile(engineer: dict = Depends(get_current_engineer)):
    """Get current engineer profile"""
    return engineer


# --- Admin: Engineer Management ---

@api_router.get("/admin/engineers")
async def list_engineers(admin: dict = Depends(get_current_admin)):
    """List all engineers"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    engineers = await db.engineers.find(
        query,
        {"_id": 0, "password_hash": 0}
    ).sort("name", 1).to_list(100)
    return engineers


@api_router.post("/admin/engineers")
async def create_engineer(engineer_data: EngineerCreate, admin: dict = Depends(get_current_admin)):
    """Create a new engineer"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    # Check if email exists within tenant
    email_query = {"email": engineer_data.email, "is_deleted": {"$ne": True}}
    email_query = scope_query(email_query, org_id)
    existing = await db.engineers.find_one(email_query)
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    engineer = Engineer(
        name=engineer_data.name,
        email=engineer_data.email,
        phone=engineer_data.phone,
        password_hash=get_password_hash(engineer_data.password),
        specialization=engineer_data.specialization,
        skills=engineer_data.skills or [],
        salary=engineer_data.salary,
    )
    if engineer_data.working_hours:
        engineer.working_hours = engineer_data.working_hours
    if engineer_data.holidays:
        engineer.holidays = engineer_data.holidays
    
    # Add organization_id
    engineer_dict = engineer.model_dump()
    if org_id:
        engineer_dict["organization_id"] = org_id
    
    await db.engineers.insert_one(engineer_dict)
    
    result = {k: v for k, v in engineer_dict.items() if k not in ("password_hash", "_id")}
    return result


@api_router.put("/admin/engineers/{engineer_id}")
async def update_engineer(
    engineer_id: str,
    update_data: EngineerUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update engineer"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": engineer_id, "is_deleted": {"$ne": True}}
    query = scope_query(query, org_id)
    
    engineer = await db.engineers.find_one(query)
    if not engineer:
        raise HTTPException(status_code=404, detail="Engineer not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    
    if update_dict:
        await db.engineers.update_one(query, {"$set": update_dict})
    
    return {"success": True}


@api_router.delete("/admin/engineers/{engineer_id}")
async def delete_engineer(engineer_id: str, admin: dict = Depends(get_current_admin)):
    """Delete engineer"""
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"id": engineer_id}
    query = scope_query(query, org_id)
    
    await db.engineers.update_one(
        query,
        {"$set": {"is_deleted": True}}
    )
    return {"success": True}




# ==================== ADMIN ENDPOINTS - EMAIL SUBSCRIPTIONS ====================

# Provider display names
SUBSCRIPTION_PROVIDERS = {
    "google_workspace": "Google Workspace",
    "titan": "Titan Email",
    "microsoft_365": "Microsoft 365",
    "zoho": "Zoho Mail",
    "other": "Other"
}

def calculate_subscription_status(renewal_date: str, reminder_days: int = 30) -> str:
    """Calculate subscription status based on renewal date"""
    if not renewal_date:
        return "active"
    
    from datetime import datetime
    try:
        renewal = datetime.fromisoformat(renewal_date.replace('Z', '+00:00'))
        now = datetime.now(renewal.tzinfo) if renewal.tzinfo else datetime.now()
        days_left = (renewal - now).days
        
        if days_left < 0:
            return "expired"
        elif days_left <= reminder_days:
            return "expiring_soon"
        else:
            return "active"
    except:
        return "active"


@api_router.get("/admin/subscriptions")
async def list_subscriptions(
    company_id: Optional[str] = None,
    provider: Optional[str] = None,
    status: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List email/cloud subscriptions with filters"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    if provider:
        query["provider"] = provider
    
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"domain": search_regex},
            {"admin_email": search_regex},
            {"provider_name": search_regex},
            {"plan_name": search_regex}
        ]
    
    skip = (page - 1) * limit
    subscriptions = await db.email_subscriptions.find(query, {"_id": 0}).sort("renewal_date", 1).skip(skip).limit(limit).to_list(limit)
    
    # Get company names
    company_ids = list(set(s.get("company_id") for s in subscriptions if s.get("company_id")))
    companies = {}
    if company_ids:
        companies_cursor = db.companies.find({"id": {"$in": company_ids}}, {"_id": 0, "id": 1, "name": 1})
        async for c in companies_cursor:
            companies[c["id"]] = c["name"]
    
    # Enrich subscriptions
    for sub in subscriptions:
        sub["company_name"] = companies.get(sub.get("company_id"), "Unknown")
        # Update status based on renewal date
        sub["status"] = calculate_subscription_status(sub.get("renewal_date"), 30)
        # Set provider display name if not set
        if not sub.get("provider_name"):
            sub["provider_name"] = SUBSCRIPTION_PROVIDERS.get(sub.get("provider"), sub.get("provider", "Unknown"))
    
    # Filter by status after calculation
    if status:
        subscriptions = [s for s in subscriptions if s["status"] == status]
    
    return subscriptions


@api_router.post("/admin/subscriptions")
async def create_subscription(data: EmailSubscriptionCreate, admin: dict = Depends(get_current_admin)):
    """Create new email subscription"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Validate company
    company = await db.companies.find_one(scope_query({"id": data.company_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    sub_data = data.model_dump()
    
    # Set provider display name
    if not sub_data.get("provider_name"):
        sub_data["provider_name"] = SUBSCRIPTION_PROVIDERS.get(sub_data.get("provider"), sub_data.get("provider", "Other"))
    
    # Calculate status
    sub_data["status"] = calculate_subscription_status(sub_data.get("renewal_date"), 30)
    
    # Calculate total price if not provided
    if not sub_data.get("total_price") and sub_data.get("price_per_user") and sub_data.get("num_users"):
        multiplier = 12 if sub_data.get("billing_cycle") == "yearly" else 1
        sub_data["total_price"] = sub_data["price_per_user"] * sub_data["num_users"] * multiplier
    
    subscription = EmailSubscription(**sub_data)
    subscription_ins_dict["organization_id"] = org_id
    subscription_ins_dict = subscription.model_dump()
    await db.email_subscriptions.insert_one(subscription_ins_dict)
    await log_audit("email_subscription", subscription.id, "create", sub_data, admin)
    
    result = subscription.model_dump()
    result["company_name"] = company.get("name")
    return result


@api_router.get("/admin/subscriptions/{subscription_id}")
async def get_subscription(subscription_id: str, admin: dict = Depends(get_current_admin)):
    """Get subscription details"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    sub = await db.email_subscriptions.find_one(scope_query({"id": subscription_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Get company
    company = await db.companies.find_one(scope_query({"id": sub.get("company_id")}, org_id), {"_id": 0})
    sub["company_name"] = company.get("name") if company else "Unknown"
    
    # Update status
    sub["status"] = calculate_subscription_status(sub.get("renewal_date"), 30)
    
    # Get related tickets
    tickets = await db.subscription_tickets.find(
        {"subscription_id": subscription_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    sub["recent_tickets"] = tickets
    
    return sub


@api_router.put("/admin/subscriptions/{subscription_id}")
async def update_subscription(subscription_id: str, data: EmailSubscriptionUpdate, admin: dict = Depends(get_current_admin)):
    """Update subscription"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    # Update provider name if provider changed
    if update_data.get("provider") and not update_data.get("provider_name"):
        update_data["provider_name"] = SUBSCRIPTION_PROVIDERS.get(update_data["provider"], update_data["provider"])
    
    # Recalculate total price
    if "price_per_user" in update_data or "num_users" in update_data:
        sub = await db.email_subscriptions.find_one(scope_query({"id": subscription_id}, org_id), {"_id": 0})
        if sub:
            price = update_data.get("price_per_user", sub.get("price_per_user", 0))
            users = update_data.get("num_users", sub.get("num_users", 1))
            cycle = update_data.get("billing_cycle", sub.get("billing_cycle", "yearly"))
            if price and users:
                multiplier = 12 if cycle == "yearly" else 1
                update_data["total_price"] = price * users * multiplier
    
    update_data["updated_at"] = get_ist_isoformat()
    
    result = await db.email_subscriptions.update_one(
        {"id": subscription_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    await log_audit("email_subscription", subscription_id, "update", update_data, admin)
    return {"message": "Subscription updated"}


@api_router.delete("/admin/subscriptions/{subscription_id}")
async def delete_subscription(subscription_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete subscription"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.email_subscriptions.update_one(
        {"id": subscription_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    await log_audit("email_subscription", subscription_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Subscription deleted"}


@api_router.get("/admin/subscriptions/{subscription_id}/tickets")
async def get_subscription_tickets(
    subscription_id: str,
    status: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    admin: dict = Depends(get_current_admin)
):
    """Get tickets for a subscription"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"subscription_id": subscription_id, "is_deleted": {"$ne": True}}
    if status:
        query["status"] = status
    
    tickets = await db.subscription_tickets.find(query, {"_id": 0}).sort("created_at", -1).limit(limit).to_list(limit)
    return tickets


@api_router.post("/admin/subscriptions/{subscription_id}/tickets")
async def create_subscription_ticket_admin(
    subscription_id: str,
    subject: str = Form(...),
    description: str = Form(...),
    issue_type: str = Form("other"),
    priority: str = Form("medium"),
    admin: dict = Depends(get_current_admin)
):
    """Create ticket for subscription issue (admin)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Get subscription
    sub = await db.email_subscriptions.find_one(scope_query({"id": subscription_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Get company
    company = await db.companies.find_one(scope_query({"id": sub.get("company_id")}, org_id), {"_id": 0})
    
    # Generate ticket number
    ticket_number = f"SUB-{get_ist_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    ticket_data = {
        "ticket_number": ticket_number,
        "subscription_id": subscription_id,
        "company_id": sub.get("company_id"),
        "subject": subject,
        "description": description,
        "issue_type": issue_type,
        "priority": priority,
        "status": "open",
        "reported_by": admin.get("id", "admin"),
        "reported_by_name": admin.get("name", "Admin"),
        "reported_by_email": admin.get("email", "")
    }
    
    ticket = SubscriptionTicket(**ticket_data)
    ticket_ins_dict["organization_id"] = org_id
    ticket_ins_dict = ticket.model_dump()
    await db.subscription_tickets.insert_one(ticket_ins_dict)
    
    # Create osTicket
    osticket_result = await create_osticket(
        email=admin.get("email", sub.get("admin_email", "")),
        name=admin.get("name", "Admin"),
        subject=f"[{sub.get('provider_name')}] {subject}",
        message=f"""
        <h3>Email/Cloud Subscription Issue</h3>
        <p><strong>Ticket:</strong> {ticket_number}</p>
        
        <h4>Subscription Details</h4>
        <ul>
            <li><strong>Provider:</strong> {sub.get('provider_name')}</li>
            <li><strong>Domain:</strong> {sub.get('domain')}</li>
            <li><strong>Company:</strong> {company.get('name') if company else 'Unknown'}</li>
            <li><strong>Plan:</strong> {sub.get('plan_name', sub.get('plan_type'))}</li>
            <li><strong>Users:</strong> {sub.get('num_users')}</li>
        </ul>
        
        <h4>Issue Details</h4>
        <ul>
            <li><strong>Type:</strong> {issue_type.replace('_', ' ').title()}</li>
            <li><strong>Priority:</strong> {priority.title()}</li>
            <li><strong>Description:</strong><br/>{description}</li>
        </ul>
        """,
        phone=""
    )
    
    if osticket_result.get("ticket_id"):
        await db.subscription_tickets.update_one(
            {"id": ticket.id},
            {"$set": {"osticket_id": osticket_result["ticket_id"]}}
        )
    
    result = ticket.model_dump()
    result["osticket_id"] = osticket_result.get("ticket_id")
    return result


# --- Subscription User Change Tracking ---

from models.subscription import SubscriptionUserChange, SubscriptionUserChangeCreate

@api_router.get("/admin/subscriptions/{subscription_id}/user-changes")
async def get_subscription_user_changes(
    subscription_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get user change history for a subscription"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Verify subscription exists
    sub = await db.email_subscriptions.find_one(scope_query({"id": subscription_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    changes = await db.subscription_user_changes.find(
        {"subscription_id": subscription_id}
    ).sort("created_at", -1).to_list(500)
    
    # Remove _id from results
    for change in changes:
        change.pop("_id", None)
    
    return changes


@api_router.post("/admin/subscriptions/{subscription_id}/user-changes")
async def add_subscription_user_change(
    subscription_id: str,
    change_data: SubscriptionUserChangeCreate,
    admin: dict = Depends(get_current_admin)
):
    """Add or remove users from a subscription"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Get subscription
    sub = await db.email_subscriptions.find_one(scope_query({"id": subscription_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    current_count = sub.get("num_users", 0)
    
    # Calculate new count
    if change_data.change_type == "add":
        new_count = current_count + change_data.user_count
    elif change_data.change_type == "remove":
        new_count = max(0, current_count - change_data.user_count)
        if change_data.user_count > current_count:
            raise HTTPException(status_code=400, detail=f"Cannot remove {change_data.user_count} users. Current count is {current_count}")
    else:
        raise HTTPException(status_code=400, detail="Invalid change_type. Must be 'add' or 'remove'")
    
    # Create change record
    change = SubscriptionUserChange(
        subscription_id=subscription_id,
        change_type=change_data.change_type,
        user_count=change_data.user_count,
        previous_count=current_count,
        new_count=new_count,
        effective_date=change_data.effective_date,
        reason=change_data.reason,
        notes=change_data.notes,
        changed_by=admin.get("id", "admin"),
        changed_by_name=admin.get("name", "Admin")
    )
    
    change_ins_dict["organization_id"] = org_id
    change_ins_dict = change.model_dump()
    await db.subscription_user_changes.insert_one(change_ins_dict)
    
    # Update subscription user count
    await db.email_subscriptions.update_one(
        {"id": subscription_id},
        {"$set": {"num_users": new_count, "updated_at": get_ist_isoformat()}}
    )
    
    result = change.model_dump()
    result["message"] = f"User count updated from {current_count} to {new_count}"
    return result


@api_router.get("/admin/subscriptions/{subscription_id}/user-summary")
async def get_subscription_user_summary(
    subscription_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get user summary with change history for a subscription"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Get subscription
    sub = await db.email_subscriptions.find_one(scope_query({"id": subscription_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    # Get all changes
    changes = await db.subscription_user_changes.find(
        {"subscription_id": subscription_id}
    ).sort("created_at", 1).to_list(500)
    
    for change in changes:
        change.pop("_id", None)
    
    # Calculate stats
    total_added = sum(c.get("user_count", 0) for c in changes if c.get("change_type") == "add")
    total_removed = sum(c.get("user_count", 0) for c in changes if c.get("change_type") == "remove")
    
    return {
        "subscription_id": subscription_id,
        "current_users": sub.get("num_users", 0),
        "initial_users": sub.get("num_users", 0) - total_added + total_removed,
        "total_added": total_added,
        "total_removed": total_removed,
        "change_count": len(changes),
        "changes": changes
    }


# ==================== ASSET GROUPS & ACCESSORIES ====================

from models.asset_group import (
    AssetGroup, AssetGroupCreate, AssetGroupUpdate,
    Accessory, AccessoryCreate, AccessoryUpdate
)

# --- Asset Groups ---

@api_router.get("/admin/asset-groups")
async def list_asset_groups(
    company_id: str = None,
    group_type: str = None,
    status: str = None,
    limit: int = 100,
    admin: dict = Depends(get_current_admin)
):
    """List all asset groups with optional filters"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    if group_type:
        query["group_type"] = group_type
    if status:
        query["status"] = status
    
    groups = await db.asset_groups.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Enrich with company names and device counts
    for group in groups:
        company = await db.companies.find_one({"id": group.get("company_id")}, {"_id": 0, "name": 1})
        group["company_name"] = company.get("name") if company else "Unknown"
        group["device_count"] = len(group.get("device_ids", []))
        group["accessory_count"] = len(group.get("accessory_ids", []))
    
    return groups


@api_router.post("/admin/asset-groups")
async def create_asset_group(group_data: AssetGroupCreate, admin: dict = Depends(get_current_admin)):
    """Create a new asset group"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    group = AssetGroup(**group_data.model_dump())
    group_ins_dict["organization_id"] = org_id
    group_ins_dict = group.model_dump()
    await db.asset_groups.insert_one(group_ins_dict)
    return group.model_dump()


@api_router.get("/admin/asset-groups/{group_id}")
async def get_asset_group(group_id: str, admin: dict = Depends(get_current_admin)):
    """Get asset group with all linked devices and accessories"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    group = await db.asset_groups.find_one(scope_query({"id": group_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not group:
        raise HTTPException(status_code=404, detail="Asset group not found")
    
    # Get company
    company = await db.companies.find_one(scope_query({"id": group.get("company_id")}, org_id), {"_id": 0, "name": 1})
    group["company_name"] = company.get("name") if company else "Unknown"
    
    # Get linked devices
    device_ids = group.get("device_ids", [])
    devices = []
    if device_ids:
        devices = await db.devices.find({"id": {"$in": device_ids}, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    group["devices"] = devices
    
    # Get linked accessories
    accessory_ids = group.get("accessory_ids", [])
    accessories = []
    if accessory_ids:
        accessories = await db.accessories.find({"id": {"$in": accessory_ids}, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    group["accessories"] = accessories
    
    # Get primary device
    if group.get("primary_device_id"):
        primary = await db.devices.find_one(scope_query({"id": group["primary_device_id"]}, org_id), {"_id": 0})
        group["primary_device"] = primary
    
    return group


@api_router.put("/admin/asset-groups/{group_id}")
async def update_asset_group(group_id: str, update_data: AssetGroupUpdate, admin: dict = Depends(get_current_admin)):
    """Update an asset group"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    group = await db.asset_groups.find_one(scope_query({"id": group_id, "is_deleted": {"$ne": True}}, org_id))
    if not group:
        raise HTTPException(status_code=404, detail="Asset group not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.asset_groups.update_one(scope_query({"id": group_id}, org_id), {"$set": update_dict})
    return {"message": "Asset group updated", "id": group_id}


@api_router.delete("/admin/asset-groups/{group_id}")
async def delete_asset_group(group_id: str, admin: dict = Depends(get_current_admin)):
    """Delete an asset group (soft delete)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.asset_groups.update_one(
        {"id": group_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Asset group not found")
    return {"message": "Asset group deleted"}


@api_router.post("/admin/asset-groups/{group_id}/add-devices")
async def add_devices_to_group(group_id: str, device_ids: List[str], admin: dict = Depends(get_current_admin)):
    """Add devices to an asset group"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    group = await db.asset_groups.find_one(scope_query({"id": group_id, "is_deleted": {"$ne": True}}, org_id))
    if not group:
        raise HTTPException(status_code=404, detail="Asset group not found")
    
    current_ids = set(group.get("device_ids", []))
    current_ids.update(device_ids)
    
    await db.asset_groups.update_one(
        {"id": group_id},
        {"$set": {"device_ids": list(current_ids), "updated_at": get_ist_isoformat()}}
    )
    return {"message": f"Added {len(device_ids)} devices to group"}


@api_router.post("/admin/asset-groups/{group_id}/remove-devices")
async def remove_devices_from_group(group_id: str, device_ids: List[str], admin: dict = Depends(get_current_admin)):
    """Remove devices from an asset group"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    group = await db.asset_groups.find_one(scope_query({"id": group_id, "is_deleted": {"$ne": True}}, org_id))
    if not group:
        raise HTTPException(status_code=404, detail="Asset group not found")
    
    current_ids = set(group.get("device_ids", []))
    current_ids.difference_update(device_ids)
    
    await db.asset_groups.update_one(
        {"id": group_id},
        {"$set": {"device_ids": list(current_ids), "updated_at": get_ist_isoformat()}}
    )
    return {"message": f"Removed devices from group"}


# --- Asset Transfer ---

class AssetTransfer(BaseModel):
    """Record of asset transfer between employees"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    asset_type: str  # "device" or "accessory"
    asset_id: str
    from_employee_id: Optional[str] = None
    from_employee_name: Optional[str] = None
    to_employee_id: Optional[str] = None
    to_employee_name: Optional[str] = None
    transfer_date: str
    reason: Optional[str] = None
    notes: Optional[str] = None
    transferred_by: str  # Admin user ID
    transferred_by_name: str
    created_at: str = Field(default_factory=get_ist_isoformat)


class AssetTransferRequest(BaseModel):
    asset_type: str  # "device" or "accessory"
    asset_id: str
    to_employee_id: Optional[str] = None  # None means unassign
    transfer_date: str
    reason: Optional[str] = None
    notes: Optional[str] = None


@api_router.post("/admin/asset-transfers")
async def transfer_asset(transfer_data: AssetTransferRequest, admin: dict = Depends(get_current_admin)):
    """Transfer an asset (device or accessory) to another employee"""
    
    org_id = await get_admin_org_id(admin.get("email", ""))
    
    # Get current asset info
    if transfer_data.asset_type == "device":
        asset = await db.devices.find_one(scope_query({"id": transfer_data.asset_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
        if not asset:
            raise HTTPException(status_code=404, detail="Device not found")
        from_employee_id = asset.get("assigned_employee_id")
        collection = db.devices
        update_field = "assigned_employee_id"
    elif transfer_data.asset_type == "accessory":
        asset = await db.accessories.find_one(scope_query({"id": transfer_data.asset_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
        if not asset:
            raise HTTPException(status_code=404, detail="Accessory not found")
        from_employee_id = asset.get("assigned_employee_id")
        collection = db.accessories
        update_field = "assigned_employee_id"
    else:
        raise HTTPException(status_code=400, detail="Invalid asset_type. Must be 'device' or 'accessory'")
    
    # Get employee names
    from_employee_name = None
    if from_employee_id:
        from_emp = await db.company_employees.find_one(scope_query({"id": from_employee_id}, org_id), {"_id": 0, "name": 1})
        from_employee_name = from_emp.get("name") if from_emp else None
    
    to_employee_name = None
    if transfer_data.to_employee_id:
        to_emp = await db.company_employees.find_one(scope_query({"id": transfer_data.to_employee_id}, org_id), {"_id": 0, "name": 1})
        if not to_emp:
            raise HTTPException(status_code=404, detail="Target employee not found")
        to_employee_name = to_emp.get("name")
    
    # Create transfer record
    transfer = AssetTransfer(
        asset_type=transfer_data.asset_type,
        asset_id=transfer_data.asset_id,
        from_employee_id=from_employee_id,
        from_employee_name=from_employee_name,
        to_employee_id=transfer_data.to_employee_id,
        to_employee_name=to_employee_name,
        transfer_date=transfer_data.transfer_date,
        reason=transfer_data.reason,
        notes=transfer_data.notes,
        transferred_by=admin.get("id", "admin"),
        transferred_by_name=admin.get("name", "Admin")
    )
    
    transfer_ins_dict["organization_id"] = org_id
    transfer_ins_dict = transfer.model_dump()
    await db.asset_transfers.insert_one(transfer_ins_dict)
    
    # Update the asset
    update_data = {
        update_field: transfer_data.to_employee_id,
        "updated_at": get_ist_isoformat()
    }
    
    # Update status based on assignment
    if transfer_data.asset_type == "accessory":
        update_data["status"] = "assigned" if transfer_data.to_employee_id else "available"
    
    await collection.update_one({"id": transfer_data.asset_id}, {"$set": update_data})
    
    result = transfer.model_dump()
    result["message"] = f"Asset transferred from {from_employee_name or 'Unassigned'} to {to_employee_name or 'Unassigned'}"
    return result


@api_router.get("/admin/asset-transfers")
async def list_asset_transfers(
    asset_type: str = None,
    asset_id: str = None,
    employee_id: str = None,
    limit: int = 100,
    admin: dict = Depends(get_current_admin)
):
    """Get asset transfer history"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {}
    if asset_type:
        query["asset_type"] = asset_type
    if asset_id:
        query["asset_id"] = asset_id
    if employee_id:
        query["$or"] = [
            {"from_employee_id": employee_id},
            {"to_employee_id": employee_id}
        ]
    
    transfers = await db.asset_transfers.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Enrich with asset details
    for t in transfers:
        if t["asset_type"] == "device":
            device = await db.devices.find_one(scope_query({"id": t["asset_id"]}, org_id), {"_id": 0, "brand": 1, "model": 1, "serial_number": 1, "device_type": 1})
            if device:
                t["asset_name"] = f"{device.get('brand', '')} {device.get('model', device.get('device_type', ''))}"
                t["asset_serial"] = device.get("serial_number")
        elif t["asset_type"] == "accessory":
            acc = await db.accessories.find_one(scope_query({"id": t["asset_id"]}, org_id), {"_id": 0, "name": 1, "brand": 1})
            if acc:
                t["asset_name"] = acc.get("name")
    
    return transfers


@api_router.get("/admin/assets/{asset_type}/{asset_id}/transfer-history")
async def get_asset_transfer_history(asset_type: str, asset_id: str, admin: dict = Depends(get_current_admin)):
    """Get transfer history for a specific asset"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    transfers = await db.asset_transfers.find(
        {"asset_type": asset_type, "asset_id": asset_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return transfers


# --- Accessories ---

@api_router.get("/admin/accessories")
async def list_accessories(
    company_id: str = None,
    accessory_type: str = None,
    status: str = None,
    assigned_employee_id: str = None,
    limit: int = 200,
    admin: dict = Depends(get_current_admin)
):
    """List all accessories with optional filters"""
    query = {"is_deleted": {"$ne": True}}
    
    # Apply tenant scoping
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = scope_query(query, org_id)
    
    if company_id:
        query["company_id"] = company_id
    if accessory_type:
        query["accessory_type"] = accessory_type
    if status:
        query["status"] = status
    if assigned_employee_id:
        query["assigned_employee_id"] = assigned_employee_id
    
    accessories = await db.accessories.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Enrich with company and employee names
    for acc in accessories:
        company = await db.companies.find_one({"id": acc.get("company_id")}, {"_id": 0, "name": 1})
        acc["company_name"] = company.get("name") if company else "Unknown"
        
        if acc.get("assigned_employee_id"):
            emp = await db.company_employees.find_one({"id": acc["assigned_employee_id"]}, {"_id": 0, "name": 1})
            acc["assigned_employee_name"] = emp.get("name") if emp else None
    
    return accessories


@api_router.post("/admin/accessories")
async def create_accessory(acc_data: AccessoryCreate, admin: dict = Depends(get_current_admin)):
    """Create a new accessory"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    accessory = Accessory(**acc_data.model_dump())
    accessory_ins_dict["organization_id"] = org_id
    accessory_ins_dict = accessory.model_dump()
    await db.accessories.insert_one(accessory_ins_dict)
    return accessory.model_dump()


@api_router.get("/admin/accessories/{accessory_id}")
async def get_accessory(accessory_id: str, admin: dict = Depends(get_current_admin)):
    """Get accessory details"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    acc = await db.accessories.find_one(scope_query({"id": accessory_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not acc:
        raise HTTPException(status_code=404, detail="Accessory not found")
    return acc


@api_router.put("/admin/accessories/{accessory_id}")
async def update_accessory(accessory_id: str, update_data: AccessoryUpdate, admin: dict = Depends(get_current_admin)):
    """Update an accessory"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    acc = await db.accessories.find_one(scope_query({"id": accessory_id, "is_deleted": {"$ne": True}}, org_id))
    if not acc:
        raise HTTPException(status_code=404, detail="Accessory not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    update_dict["updated_at"] = get_ist_isoformat()
    
    await db.accessories.update_one(scope_query({"id": accessory_id}, org_id), {"$set": update_dict})
    return {"message": "Accessory updated", "id": accessory_id}


@api_router.delete("/admin/accessories/{accessory_id}")
async def delete_accessory(accessory_id: str, admin: dict = Depends(get_current_admin)):
    """Delete an accessory (soft delete)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.accessories.update_one(
        {"id": accessory_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Accessory not found")
    return {"message": "Accessory deleted"}


# --- Renewal Alerts ---

@api_router.get("/admin/renewal-alerts")
async def get_renewal_alerts(
    days: int = 90,
    company_id: str = None,
    admin: dict = Depends(get_current_admin)
):
    """Get all items expiring within specified days (warranties, AMC, licenses, subscriptions)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    from datetime import datetime, timedelta
    
    today = datetime.now().date()
    cutoff_date = (today + timedelta(days=days)).isoformat()
    today_str = today.isoformat()
    
    alerts = {
        "warranties": [],
        "amc_contracts": [],
        "licenses": [],
        "subscriptions": [],
        "summary": {
            "critical": 0,  # < 30 days
            "warning": 0,   # 30-60 days
            "notice": 0     # 60-90 days
        }
    }
    
    # Base query
    base_query = {"is_deleted": {"$ne": True}}
    if company_id:
        base_query["company_id"] = company_id
    
    # 1. Expiring Warranties (Devices)
    warranty_query = {
        **base_query,
        "warranty_end_date": {"$gte": today_str, "$lte": cutoff_date}
    }
    devices = await db.devices.find(warranty_query, {"_id": 0}).to_list(500)
    for d in devices:
        end_date = datetime.fromisoformat(d["warranty_end_date"]).date()
        days_left = (end_date - today).days
        d["days_left"] = days_left
        d["alert_type"] = "critical" if days_left <= 30 else ("warning" if days_left <= 60 else "notice")
        d["item_type"] = "warranty"
        alerts["warranties"].append(d)
        alerts["summary"][d["alert_type"]] += 1
    
    # 2. Expiring AMC Contracts
    amc_query = {
        **base_query,
        "end_date": {"$gte": today_str, "$lte": cutoff_date}
    }
    amcs = await db.amc_contracts.find(amc_query, {"_id": 0}).to_list(200)
    for a in amcs:
        end_date = datetime.fromisoformat(a["end_date"]).date()
        days_left = (end_date - today).days
        a["days_left"] = days_left
        a["alert_type"] = "critical" if days_left <= 30 else ("warning" if days_left <= 60 else "notice")
        a["item_type"] = "amc"
        alerts["amc_contracts"].append(a)
        alerts["summary"][a["alert_type"]] += 1
    
    # 3. Expiring Licenses
    license_query = {
        **base_query,
        "expiry_date": {"$gte": today_str, "$lte": cutoff_date}
    }
    licenses = await db.licenses.find(license_query, {"_id": 0}).to_list(200)
    for l in licenses:
        end_date = datetime.fromisoformat(l["expiry_date"]).date()
        days_left = (end_date - today).days
        l["days_left"] = days_left
        l["alert_type"] = "critical" if days_left <= 30 else ("warning" if days_left <= 60 else "notice")
        l["item_type"] = "license"
        alerts["licenses"].append(l)
        alerts["summary"][l["alert_type"]] += 1
    
    # 4. Expiring Subscriptions
    sub_query = {
        **base_query,
        "renewal_date": {"$gte": today_str, "$lte": cutoff_date}
    }
    subs = await db.email_subscriptions.find(sub_query, {"_id": 0}).to_list(100)
    for s in subs:
        end_date = datetime.fromisoformat(s["renewal_date"]).date()
        days_left = (end_date - today).days
        s["days_left"] = days_left
        s["alert_type"] = "critical" if days_left <= 30 else ("warning" if days_left <= 60 else "notice")
        s["item_type"] = "subscription"
        alerts["subscriptions"].append(s)
        alerts["summary"][s["alert_type"]] += 1
    
    # Sort each by days_left
    alerts["warranties"].sort(key=lambda x: x["days_left"])
    alerts["amc_contracts"].sort(key=lambda x: x["days_left"])
    alerts["licenses"].sort(key=lambda x: x["days_left"])
    alerts["subscriptions"].sort(key=lambda x: x["days_left"])
    
    alerts["total_alerts"] = (
        len(alerts["warranties"]) + 
        len(alerts["amc_contracts"]) + 
        len(alerts["licenses"]) + 
        len(alerts["subscriptions"])
    )
    
    return alerts


# ==================== COMPANY PORTAL ENDPOINTS ====================

# --- Company Auth ---

@api_router.post("/company/auth/login")
@limiter.limit(RATE_LIMITS["login"])
async def company_login(request: Request, login: CompanyLogin):
    """Company user login with rate limiting (5 attempts/minute per IP)"""
    user = await db.company_users.find_one({
        "email": login.email.lower(),
        "is_active": True,
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not user or not verify_password(login.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Update last login
    await db.company_users.update_one(
        {"id": user["id"]},
        {"$set": {"last_login": get_ist_isoformat()}}
    )
    
    # Create token with user type indicator
    access_token = create_access_token(data={"sub": user["id"], "type": "company_user"})
    
    # Get company info
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0, "name": 1})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "company_id": user["company_id"],
            "company_name": company.get("name") if company else None
        }
    }

@api_router.post("/company/auth/register")
@limiter.limit(RATE_LIMITS["register"])
async def company_user_register(request: Request, data: CompanyUserRegister):
    """Self-registration for company users with rate limiting and password validation"""
    # Find company by code
    company = await db.companies.find_one({
        "code": data.company_code.upper(),
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not company:
        raise HTTPException(status_code=404, detail="Invalid company code")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(data.password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    # Check if email already exists
    existing = await db.company_users.find_one({"email": data.email.lower()}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user (as viewer by default)
    user = CompanyUser(
        company_id=company["id"],
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        name=data.name,
        phone=data.phone,
        role="company_viewer",
        created_by="self_registration"
    )
    
    await db.company_users.insert_one(user.model_dump())
    
    return {"message": "Registration successful. You can now login.", "email": data.email}

@api_router.get("/company/auth/me")
async def get_company_user_info(user: dict = Depends(get_current_company_user)):
    """Get current company user info"""
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0, "name": 1, "code": 1})
    return {
        **user,
        "company_name": company.get("name") if company else None,
        "company_code": company.get("code") if company else None
    }

# --- Company Dashboard ---

@api_router.get("/company/dashboard")
async def get_company_dashboard(user: dict = Depends(get_current_company_user)):
    """Get company dashboard summary"""
    company_id = user["company_id"]
    today = get_ist_now().date()
    
    # Total devices
    total_devices = await db.devices.count_documents({
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    })
    
    # Get all devices for warranty calculations
    devices = await db.devices.find({
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "id": 1, "warranty_end_date": 1}).to_list(1000)
    
    warranties_30 = 0
    warranties_60 = 0
    warranties_90 = 0
    
    for device in devices:
        end_date = device.get("warranty_end_date")
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                days_left = (end - today).days
                if 0 < days_left <= 30:
                    warranties_30 += 1
                elif 30 < days_left <= 60:
                    warranties_60 += 1
                elif 60 < days_left <= 90:
                    warranties_90 += 1
            except:
                pass
    
    # Active AMC contracts
    active_amc = await db.amc_contracts.count_documents({
        "company_id": company_id,
        "is_deleted": {"$ne": True},
        "end_date": {"$gte": today.isoformat()}
    })
    
    # Open service tickets (V2)
    open_tickets = await db.tickets_v2.count_documents({
        "company_id": company_id,
        "is_open": True,
        "is_deleted": {"$ne": True}
    })
    
    # Recent tickets (V2)
    recent_tickets = await db.tickets_v2.find({
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "timeline": 0}).sort("created_at", -1).limit(5).to_list(5)
    
    return {
        "total_devices": total_devices,
        "warranties_expiring_30_days": warranties_30,
        "warranties_expiring_60_days": warranties_60,
        "warranties_expiring_90_days": warranties_90,
        "active_amc_contracts": active_amc,
        "open_service_tickets": open_tickets,
        "recent_tickets": recent_tickets
    }

# --- Company Devices (Read-Only) ---

@api_router.get("/company/devices")
async def list_company_devices(
    user: dict = Depends(get_current_company_user),
    search: Optional[str] = None,
    device_type: Optional[str] = None,
    site_id: Optional[str] = None,
    warranty_status: Optional[str] = None
):
    """List all devices for the company (read-only) with smart search"""
    from utils.synonyms import expand_search_query, get_brand_variants
    
    company_id = user["company_id"]
    query = {"company_id": company_id, "is_deleted": {"$ne": True}}
    
    if device_type:
        query["device_type"] = device_type
    if site_id:
        query["site_id"] = site_id
    
    # Smart search with synonyms
    if search and search.strip():
        search_term = search.strip()
        synonym_regex = expand_search_query(search_term)
        brand_variants = get_brand_variants(search_term)
        brand_regex = {"$regex": "|".join(brand_variants), "$options": "i"}
        
        query["$or"] = [
            {"serial_number": {"$regex": search_term, "$options": "i"}},
            {"asset_tag": {"$regex": search_term, "$options": "i"}},
            {"brand": brand_regex},
            {"model": {"$regex": search_term, "$options": "i"}},
            {"device_type": synonym_regex}
        ]
    
    devices = await db.devices.find(query, {"_id": 0}).to_list(1000)
    today = get_ist_now().date()
    
    result = []
    for device in devices:
        # Calculate warranty status
        warranty_end = device.get("warranty_end_date")
        if warranty_end:
            try:
                end = datetime.strptime(warranty_end, "%Y-%m-%d").date()
                days_left = (end - today).days
                device["warranty_status"] = "active" if days_left > 0 else "expired"
                device["warranty_days_left"] = max(0, days_left)
            except:
                device["warranty_status"] = "unknown"
                device["warranty_days_left"] = 0
        else:
            device["warranty_status"] = "not_set"
            device["warranty_days_left"] = 0
        
        # Check AMC coverage
        amc_assignment = await db.amc_device_assignments.find_one({
            "device_id": device["id"],
            "status": "active"
        }, {"_id": 0})
        
        if amc_assignment:
            amc_end = amc_assignment.get("coverage_end")
            if amc_end and is_warranty_active(amc_end):
                device["amc_covered"] = True
                device["amc_coverage_end"] = amc_end
            else:
                device["amc_covered"] = False
        else:
            device["amc_covered"] = False
        
        # Get assigned user name
        if device.get("assigned_user_id"):
            assigned_user = await db.users.find_one({"id": device["assigned_user_id"]}, {"_id": 0, "name": 1})
            device["assigned_user_name"] = assigned_user.get("name") if assigned_user else None
        
        # Get site name
        if device.get("site_id"):
            site = await db.sites.find_one({"id": device["site_id"]}, {"_id": 0, "name": 1})
            device["site_name"] = site.get("name") if site else None
        
        # Filter by warranty status if specified
        if warranty_status:
            if warranty_status == "active" and device["warranty_status"] != "active":
                continue
            if warranty_status == "expired" and device["warranty_status"] != "expired":
                continue
            if warranty_status == "expiring_soon" and device.get("warranty_days_left", 0) > 30:
                continue
        
        # Note: Search filtering is now done at query level with synonym support
        # No need for additional filtering here
        
        # Add category alias for frontend compatibility
        device["category"] = device.get("device_type", "")
        
        result.append(device)
    
    return result

@api_router.get("/company/devices/{device_id}")
async def get_company_device(device_id: str, user: dict = Depends(get_current_company_user)):
    """Get single device details (read-only)"""
    device = await db.devices.find_one({
        "id": device_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get parts
    parts = await db.parts.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    # Get service history from service_history collection
    services = await db.service_history.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("service_date", -1).to_list(50)
    
    # Get tickets for this device (V2)
    tickets = await db.tickets_v2.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "id": 1, "ticket_number": 1, "subject": 1, "current_stage_name": 1, "priority_name": 1, "created_at": 1, "resolved_at": 1, "help_topic_name": 1}).sort("created_at", -1).to_list(50)
    
    # Format tickets as service history entries
    for ticket in tickets:
        services.append({
            "id": ticket.get("id"),
            "type": "service_ticket",
            "service_type": ticket.get("help_topic_name", "Service Ticket"),
            "description": ticket.get("subject", "Service Request"),
            "status": ticket.get("current_stage_name", "New"),
            "priority": ticket.get("priority_name"),
            "ticket_number": ticket.get("ticket_number"),
            "service_date": ticket.get("created_at"),
            "resolved_date": ticket.get("resolved_at")
        })
    
    # Get AI support chat history for this device
    ai_chats = await db.ai_support_history.find({
        "device_id": device_id
    }, {"_id": 0}).sort("created_at", -1).to_list(50)
    
    # Format AI chats as service history entries
    for chat in ai_chats:
        user_messages = [m.get("content", "")[:100] for m in chat.get("messages", []) if m.get("role") == "user"]
        issue_summary = user_messages[0] if user_messages else "AI Support Chat"
        services.append({
            "id": chat.get("id"),
            "type": "ai_support",
            "service_type": "AI Support Chat",
            "description": issue_summary,
            "resolved_by_ai": chat.get("resolved_by_ai", False),
            "messages_count": len(chat.get("messages", [])),
            "service_date": chat.get("created_at"),
            "user_name": chat.get("user_name")
        })
    
    # Sort all service history by date (most recent first)
    services.sort(key=lambda x: x.get("service_date") or x.get("created_at") or "", reverse=True)
    
    # Get AMC info
    amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device_id,
        "status": "active"
    }, {"_id": 0})
    
    amc_info = None
    if amc_assignment:
        amc_contract = await db.amc_contracts.find_one({
            "id": amc_assignment["amc_contract_id"]
        }, {"_id": 0})
        if amc_contract:
            amc_info = {
                "contract_name": amc_contract.get("name"),
                "amc_type": amc_contract.get("amc_type"),
                "coverage_start": amc_assignment.get("coverage_start"),
                "coverage_end": amc_assignment.get("coverage_end"),
                "coverage_includes": amc_contract.get("coverage_includes"),
                "entitlements": amc_contract.get("entitlements")
            }
    
    return {
        "device": device,
        "parts": parts,
        "service_history": services,
        "amc_info": amc_info
    }


@api_router.get("/company/devices/{device_id}/analytics")
async def get_device_analytics(device_id: str, user: dict = Depends(get_current_company_user)):
    """Get comprehensive analytics for a device - tickets, spend, AMC metrics, lifecycle"""
    from datetime import datetime, timedelta
    
    device = await db.devices.find_one({
        "id": device_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Get ALL tickets for this device from V2
    all_tickets = await db.tickets_v2.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "timeline": 0}).sort("created_at", -1).to_list(200)
    
    # Calculate ticket analytics
    total_tickets = len(all_tickets)
    open_tickets = len([t for t in all_tickets if t.get("is_open", True)])
    resolved_tickets = len([t for t in all_tickets if not t.get("is_open", True)])
    
    # Calculate average TAT (Turn Around Time) for resolved tickets
    tat_times = []
    for t in all_tickets:
        if t.get("created_at") and t.get("resolved_at"):
            try:
                created = datetime.fromisoformat(t["created_at"].replace("Z", "+00:00")) if isinstance(t["created_at"], str) else t["created_at"]
                completed = datetime.fromisoformat(t["resolved_at"].replace("Z", "+00:00")) if isinstance(t["resolved_at"], str) else t["resolved_at"]
                tat_hours = (completed - created).total_seconds() / 3600
                tat_times.append(tat_hours)
            except:
                pass
    
    avg_tat_hours = sum(tat_times) / len(tat_times) if tat_times else 0
    
    # Get quotations related to device tickets
    ticket_ids = [t["id"] for t in all_tickets]
    quotations = await db.quotations.find({
        "ticket_id": {"$in": ticket_ids},
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    total_spend = sum(q.get("total_amount", 0) for q in quotations if q.get("status") == "approved")
    pending_quotations = len([q for q in quotations if q.get("status") in ["draft", "sent"]])
    
    # Get parts replaced on this device
    parts_replaced = await db.parts.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    parts_cost = sum(p.get("cost", 0) or p.get("price", 0) or 0 for p in parts_replaced)
    
    # Get service history
    service_history = await db.service_history.find({
        "device_id": device_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("service_date", -1).to_list(100)
    
    # AMC Analytics
    amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device_id,
        "status": "active"
    }, {"_id": 0})
    
    amc_analytics = None
    if amc_assignment:
        amc_contract = await db.amc_contracts.find_one({
            "id": amc_assignment.get("amc_contract_id")
        }, {"_id": 0})
        
        if amc_contract:
            # Calculate AMC coverage metrics
            coverage_start = amc_assignment.get("coverage_start")
            coverage_end = amc_assignment.get("coverage_end")
            
            # Calculate days remaining
            days_remaining = 0
            coverage_percentage = 0
            if coverage_end:
                try:
                    end_date = datetime.fromisoformat(coverage_end.replace("Z", "+00:00")) if isinstance(coverage_end, str) else coverage_end
                    start_date = datetime.fromisoformat(coverage_start.replace("Z", "+00:00")) if isinstance(coverage_start, str) else coverage_start
                    now = datetime.now(end_date.tzinfo) if end_date.tzinfo else datetime.now()
                    days_remaining = max(0, (end_date - now).days)
                    total_days = (end_date - start_date).days if start_date else 365
                    days_used = total_days - days_remaining
                    coverage_percentage = min(100, (days_used / total_days) * 100) if total_days > 0 else 0
                except:
                    pass
            
            # Count preventive maintenance visits
            pm_visits = len([s for s in service_history if s.get("service_type") in ["preventive_maintenance", "PM", "Preventive Maintenance"]])
            
            # Expected PM visits (quarterly = 4 per year)
            pm_schedule = amc_contract.get("pm_schedule", "quarterly")
            expected_pm = 4 if pm_schedule == "quarterly" else 12 if pm_schedule == "monthly" else 2 if pm_schedule == "bi-annual" else 1
            
            amc_analytics = {
                "contract_id": amc_contract.get("id"),
                "contract_name": amc_contract.get("name"),
                "amc_type": amc_contract.get("amc_type"),
                "coverage_start": coverage_start,
                "coverage_end": coverage_end,
                "days_remaining": days_remaining,
                "coverage_percentage": round(coverage_percentage, 1),
                "coverage_includes": amc_contract.get("coverage_includes", []),
                "entitlements": amc_contract.get("entitlements", {}),
                "pm_schedule": pm_schedule,
                "pm_visits_completed": pm_visits,
                "pm_visits_expected": expected_pm,
                "pm_compliance": round((pm_visits / expected_pm) * 100, 1) if expected_pm > 0 else 0,
                "next_pm_due": amc_assignment.get("next_pm_date"),
                "contract_value": amc_contract.get("contract_value", 0),
                "is_active": True
            }
    
    # Build lifecycle events
    lifecycle_events = []
    
    # Device creation/registration
    if device.get("created_at"):
        lifecycle_events.append({
            "type": "device_registered",
            "title": "Device Registered",
            "description": f"{device.get('brand', '')} {device.get('model', '')} added to inventory",
            "date": device.get("created_at"),
            "icon": "laptop"
        })
    
    # Warranty events
    if device.get("warranty_start"):
        lifecycle_events.append({
            "type": "warranty_start",
            "title": "Warranty Started",
            "description": f"Manufacturer warranty began",
            "date": device.get("warranty_start"),
            "icon": "shield"
        })
    
    if device.get("warranty_end"):
        lifecycle_events.append({
            "type": "warranty_end",
            "title": "Warranty Expiry",
            "description": f"Manufacturer warranty ends",
            "date": device.get("warranty_end"),
            "icon": "alert",
            "is_future": True
        })
    
    # AMC enrollment
    if amc_assignment:
        lifecycle_events.append({
            "type": "amc_enrolled",
            "title": "AMC Enrolled",
            "description": f"Enrolled in {amc_analytics.get('contract_name', 'AMC Contract') if amc_analytics else 'AMC'}",
            "date": amc_assignment.get("created_at") or amc_assignment.get("coverage_start"),
            "icon": "file-text"
        })
    
    # Service tickets
    for ticket in all_tickets[:10]:  # Last 10 tickets
        lifecycle_events.append({
            "type": "service_ticket",
            "title": f"Service Ticket #{ticket.get('ticket_number', '')}",
            "description": ticket.get("title") or ticket.get("subject", "Service request"),
            "date": ticket.get("created_at"),
            "status": ticket.get("status"),
            "icon": "ticket"
        })
    
    # Parts replacements
    for part in parts_replaced[:5]:
        lifecycle_events.append({
            "type": "part_replaced",
            "title": f"Part Replaced: {part.get('name', 'Component')}",
            "description": part.get("description", "Component replacement"),
            "date": part.get("created_at") or part.get("replaced_at"),
            "cost": part.get("cost") or part.get("price"),
            "icon": "package"
        })
    
    # Sort lifecycle by date
    lifecycle_events.sort(key=lambda x: x.get("date") or "", reverse=True)
    
    # WatchTower placeholder (will be populated when WatchTower is integrated)
    rmm_data = {
        "integrated": False,
        "message": "WatchTower monitoring agent not installed on this device",
        "placeholder_metrics": {
            "cpu_usage": None,
            "memory_usage": None,
            "disk_usage": None,
            "last_seen": None,
            "os_version": None,
            "uptime": None,
            "installed_software": [],
            "pending_updates": [],
            "alerts": []
        }
    }
    
    return {
        "device": device,
        "ticket_analytics": {
            "total_tickets": total_tickets,
            "open_tickets": open_tickets,
            "resolved_tickets": resolved_tickets,
            "avg_tat_hours": round(avg_tat_hours, 1),
            "avg_tat_display": f"{int(avg_tat_hours)}h {int((avg_tat_hours % 1) * 60)}m" if avg_tat_hours else "N/A",
            "tickets": all_tickets[:20]  # Last 20 tickets
        },
        "financial_summary": {
            "total_spend": total_spend,
            "parts_cost": parts_cost,
            "pending_quotations": pending_quotations,
            "quotations": quotations[:10]
        },
        "parts_replaced": parts_replaced,
        "service_history": service_history[:20],
        "amc_analytics": amc_analytics,
        "lifecycle_events": lifecycle_events[:30],
        "rmm_data": rmm_data
    }


# --- Company Credentials ---

@api_router.get("/company/credentials")
async def get_company_credentials(user: dict = Depends(get_current_company_user)):
    """
    Get all credentials for the company's devices and internet services.
    """
    company_id = user["company_id"]
    credentials = []
    
    # Device credentials
    device_query = {
        "company_id": company_id,
        "is_deleted": {"$ne": True},
        "credentials": {"$ne": None}
    }
    
    devices = await db.devices.find(device_query, {"_id": 0}).to_list(1000)
    for device in devices:
        if device.get("credentials"):
            # Get assigned employee name if any
            emp_name = None
            if device.get("assigned_employee_id"):
                emp = await db.company_employees.find_one({"id": device["assigned_employee_id"]})
                emp_name = emp.get("name") if emp else None
            
            credentials.append({
                "id": device["id"],
                "source_type": "device",
                "source_name": f"{device.get('brand', '')} {device.get('model', '')}".strip(),
                "device_type": device.get("device_type"),
                "serial_number": device.get("serial_number"),
                "asset_tag": device.get("asset_tag"),
                "location": device.get("location"),
                "assigned_to": emp_name,
                "credentials": device.get("credentials"),
                "created_at": device.get("created_at")
            })
    
    # Internet service credentials
    isp_query = {
        "company_id": company_id,
        "is_deleted": {"$ne": True}
    }
    
    services = await db.internet_services.find(isp_query, {"_id": 0}).to_list(100)
    for service in services:
        site_name = None
        if service.get("site_id"):
            site = await db.sites.find_one({"id": service["site_id"]})
            site_name = site.get("name") if site else None
        
        # Extract credential-related fields
        creds = {
            "router_ip": service.get("router_ip"),
            "router_username": service.get("router_username"),
            "router_password": service.get("router_password"),
            "wifi_ssid": service.get("wifi_ssid"),
            "wifi_password": service.get("wifi_password"),
            "pppoe_username": service.get("pppoe_username"),
            "pppoe_password": service.get("pppoe_password"),
            "static_ip": service.get("static_ip"),
            "gateway": service.get("gateway"),
        }
        # Only include if has any credentials
        if any(creds.values()):
            credentials.append({
                "id": service["id"],
                "source_type": "internet",
                "source_name": service.get("provider_name", "ISP"),
                "device_type": service.get("connection_type"),
                "serial_number": service.get("account_number"),
                "location": site_name,
                "plan_name": service.get("plan_name"),
                "speed": service.get("speed_download"),
                "support_phone": service.get("support_phone"),
                "credentials": creds,
                "created_at": service.get("created_at")
            })
    
    return credentials

# --- Consumable Orders ---

@api_router.post("/company/devices/{device_id}/order-consumable")
async def order_consumable(device_id: str, order_data: dict, user: dict = Depends(get_current_company_user)):
    """Order consumables for a printer device - supports multiple items"""
    # Verify device belongs to company
    device = await db.devices.find_one({
        "id": device_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Check if it's a printer
    device_type = (device.get("device_type") or "").lower()
    if "printer" not in device_type:
        raise HTTPException(status_code=400, detail="Consumable orders are only available for printers")
    
    # Get company details
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0})
    
    # Get site details
    site = None
    if device.get("site_id"):
        site = await db.sites.find_one({"id": device["site_id"]}, {"_id": 0})
    
    # Get consumable order history for this device
    order_history = await db.consumable_orders.find(
        {"device_id": device_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    # Get service history
    service_history = await db.service_history.find(
        {"device_id": device_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("service_date", -1).limit(5).to_list(5)
    
    # Process order items - support both legacy single item and new multiple items format
    order_items = order_data.get("items", [])
    
    # Legacy support: if no items array but has consumable_type/quantity, create single item
    if not order_items and (order_data.get("quantity") or order_data.get("consumable_type")):
        order_items = [{
            "consumable_id": "legacy",
            "name": order_data.get("consumable_type") or device.get("consumable_type") or "Consumable",
            "consumable_type": order_data.get("consumable_type") or device.get("consumable_type") or "Consumable",
            "model_number": order_data.get("consumable_model") or device.get("consumable_model") or "",
            "brand": device.get("consumable_brand"),
            "quantity": order_data.get("quantity", 1)
        }]
    
    if not order_items:
        raise HTTPException(status_code=400, detail="No items specified in order")
    
    # Calculate total quantity
    total_quantity = sum(item.get("quantity", 1) for item in order_items)
    
    # Create the order
    order = ConsumableOrder(
        company_id=user["company_id"],
        device_id=device_id,
        requested_by=user["id"],
        requested_by_name=user.get("name", "Unknown"),
        requested_by_email=user.get("email", ""),
        # Legacy fields for backward compatibility
        consumable_type=order_items[0].get("consumable_type") if len(order_items) == 1 else "Multiple Items",
        consumable_model=order_items[0].get("model_number") if len(order_items) == 1 else f"{len(order_items)} items",
        quantity=total_quantity,
        # New multi-item support
        items=order_items,
        notes=order_data.get("notes")
    )
    
    await db.consumable_orders.insert_one(order.model_dump())
    
    # Helper function
    def format_date(date_str):
        if not date_str:
            return "N/A"
        try:
            if 'T' in str(date_str):
                return str(date_str).split('T')[0]
            return str(date_str)
        except:
            return str(date_str)
    
    # Build osTicket message with multiple items support
    osticket_message = f"""
<h2>CONSUMABLE ORDER REQUEST</h2>
<p><strong>Order Number:</strong> {order.order_number}</p>
<p><strong>Order Date:</strong> {format_date(order.created_at)}</p>
<p><strong>Total Items:</strong> {len(order_items)} item(s), {total_quantity} unit(s)</p>

<hr>
<h3>CONSUMABLES ORDERED</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #e0f2e9;">
<th>Item</th><th>Type</th><th>Model/Part No.</th><th>Brand</th><th>Color</th><th>Qty</th>
</tr>
"""
    
    for idx, item in enumerate(order_items, 1):
        color_display = item.get("color") or "-"
        brand_display = item.get("brand") or "-"
        osticket_message += f"""
<tr>
<td>{item.get('name', f'Item {idx}')}</td>
<td>{item.get('consumable_type', 'N/A')}</td>
<td><strong>{item.get('model_number', 'N/A')}</strong></td>
<td>{brand_display}</td>
<td>{color_display}</td>
<td><strong>{item.get('quantity', 1)}</strong></td>
</tr>
"""
    
    osticket_message += f"""
</table>
<p><strong>Special Notes:</strong> {order.notes or 'None'}</p>

<hr>
<h3>PRINTER DETAILS</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Serial Number</strong></td><td><strong>{device.get('serial_number', 'N/A')}</strong></td></tr>
<tr><td><strong>Brand</strong></td><td>{device.get('brand', 'N/A')}</td></tr>
<tr><td><strong>Model</strong></td><td>{device.get('model', 'N/A')}</td></tr>
<tr><td><strong>Asset Tag</strong></td><td>{device.get('asset_tag') or 'N/A'}</td></tr>
<tr><td><strong>Location</strong></td><td>{device.get('location') or 'N/A'}</td></tr>
<tr><td><strong>Status</strong></td><td>{device.get('status', 'N/A')}</td></tr>
<tr><td><strong>Condition</strong></td><td>{device.get('condition', 'N/A')}</td></tr>
</table>

<hr>
<h3>COMPANY INFORMATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Company Name</strong></td><td>{company.get('name', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Person</strong></td><td>{company.get('contact_name', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Email</strong></td><td>{company.get('contact_email', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{company.get('contact_phone', 'N/A') if company else 'N/A'}</td></tr>
<tr><td><strong>Address</strong></td><td>{company.get('address', 'N/A') if company else 'N/A'}</td></tr>
</table>

<hr>
<h3>ORDERED BY</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Name</strong></td><td>{user.get('name', 'N/A')}</td></tr>
<tr><td><strong>Email</strong></td><td>{user.get('email', 'N/A')}</td></tr>
<tr><td><strong>Phone</strong></td><td>{user.get('phone', 'N/A')}</td></tr>
</table>
"""

    # Add Site Information if available
    if site:
        osticket_message += f"""
<hr>
<h3>DELIVERY LOCATION (Site)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Site Name</strong></td><td>{site.get('name', 'N/A')}</td></tr>
<tr><td><strong>Address</strong></td><td>{site.get('address', 'N/A')}</td></tr>
<tr><td><strong>City</strong></td><td>{site.get('city', 'N/A')}</td></tr>
<tr><td><strong>State</strong></td><td>{site.get('state', 'N/A')}</td></tr>
<tr><td><strong>Pincode</strong></td><td>{site.get('pincode', 'N/A')}</td></tr>
<tr><td><strong>Contact Person</strong></td><td>{site.get('contact_person', 'N/A')}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{site.get('contact_phone', 'N/A')}</td></tr>
</table>
"""

    # Add Order History
    if order_history:
        osticket_message += f"""
<hr>
<h3>PREVIOUS CONSUMABLE ORDERS FOR THIS PRINTER ({len(order_history)} records)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>Order #</th><th>Date</th><th>Item</th><th>Qty</th><th>Status</th>
</tr>
"""
        for hist in order_history:
            if hist.get('order_number') != order.order_number:  # Skip current order
                osticket_message += f"""
<tr>
<td>{hist.get('order_number', 'N/A')}</td>
<td>{format_date(hist.get('created_at'))}</td>
<td>{hist.get('consumable_type', 'N/A')} - {hist.get('consumable_model', 'N/A')}</td>
<td>{hist.get('quantity', 1)}</td>
<td>{hist.get('status', 'N/A').upper()}</td>
</tr>
"""
        osticket_message += "</table>"
    else:
        osticket_message += """
<hr>
<h3>PREVIOUS CONSUMABLE ORDERS</h3>
<p><em>This is the first consumable order for this printer.</em></p>
"""

    # Add Service History
    if service_history:
        osticket_message += f"""
<hr>
<h3>RECENT SERVICE HISTORY ({len(service_history)} records)</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>Date</th><th>Service Type</th><th>Problem</th><th>Status</th>
</tr>
"""
        for svc in service_history:
            osticket_message += f"""
<tr>
<td>{format_date(svc.get('service_date'))}</td>
<td>{svc.get('service_type', 'N/A')}</td>
<td>{(svc.get('problem_reported', 'N/A') or 'N/A')[:50]}...</td>
<td>{svc.get('status', 'N/A')}</td>
</tr>
"""
        osticket_message += "</table>"

    osticket_message += f"""
<hr>
<p style="color: #666; font-size: 12px;">
<em>This consumable order was submitted from the Warranty & Asset Tracking Portal.<br>
Order Created: {get_ist_isoformat()}</em>
</p>
"""

    # Create osTicket - build subject for multi-item orders
    if len(order_items) == 1:
        consumable_info = f"{order_items[0].get('name', 'Consumable')} x {order_items[0].get('quantity', 1)}"
    else:
        consumable_info = f"{len(order_items)} items, {total_quantity} units"
    
    osticket_result = await create_osticket(
        email=user.get("email", "noreply@warranty-portal.com"),
        name=user.get("name", "Portal User"),
        subject=f"[{order.order_number}] Consumable Order: {consumable_info}",
        message=osticket_message,
        phone=user.get("phone", "")
    )
    
    osticket_id = osticket_result.get("ticket_id")
    osticket_error = osticket_result.get("error")
    
    # Update order with osTicket ID
    if osticket_id:
        await db.consumable_orders.update_one(
            {"id": order.id},
            {"$set": {"osticket_id": osticket_id}}
        )
    
    # ALSO create in the Enterprise Ticketing System (tickets collection)
    enterprise_ticket_id = str(uuid.uuid4())
    enterprise_ticket = {
        "id": enterprise_ticket_id,
        "ticket_number": order.order_number,  # Use order number as ticket number
        "company_id": user["company_id"],
        "source": "company_portal",
        "device_id": device.get("id"),
        "device_serial": device.get("serial_number"),
        "subject": f"Consumable Order: {consumable_info}",
        "description": f"Consumable order for {device.get('serial_number', 'device')}.\n\nItems: {consumable_info}\n\nNotes: {order_data.get('notes', 'N/A')}",
        "status": "open",
        "priority": "medium",
        "priority_order": 2,
        "requester_id": user.get("id"),
        "requester_name": user.get("name", "Portal User"),
        "requester_email": user.get("email", ""),
        "requester_phone": user.get("phone"),
        "assigned_to": None,
        "assigned_to_name": None,
        "assigned_at": None,
        "department_id": None,
        "help_topic_id": None,
        "category": "consumable_order",
        "tags": ["consumable-order", f"device:{device.get('serial_number', 'unknown')}"],
        "watchers": [],
        "sla_status": None,
        "custom_fields": {
            "order_number": order.order_number,
            "device_serial": device.get("serial_number"),
            "device_type": device.get("device_type"),
            "items_count": len(order_items),
            "total_quantity": total_quantity
        },
        "form_data": None,
        "attachments": [],
        "reply_count": 0,
        "internal_note_count": 0,
        "created_at": get_ist_isoformat(),
        "updated_at": get_ist_isoformat(),
        "first_response_at": None,
        "resolved_at": None,
        "closed_at": None,
        "last_customer_reply_at": None,
        "last_staff_reply_at": None,
        "created_by": user.get("id"),
        "created_by_type": "customer",
        "osticket_id": osticket_id,
        "consumable_order_id": order.id,  # Link to the consumable_orders collection
        "is_deleted": False
    }
    
    await db.tickets.insert_one(enterprise_ticket)
    
    return {
        "message": "Consumable order submitted successfully",
        "order_number": order.order_number,
        "id": order.id,
        "items_count": len(order_items),
        "total_quantity": total_quantity,
        "enterprise_ticket_id": enterprise_ticket_id,
        "osticket_id": osticket_id,
        "osticket_error": osticket_error
    }

@api_router.get("/company/consumable-orders")
async def list_company_consumable_orders(user: dict = Depends(get_current_company_user)):
    """List consumable orders for the company"""
    orders = await db.consumable_orders.find(
        {"company_id": user["company_id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with device info
    for order in orders:
        device = await db.devices.find_one({"id": order["device_id"]}, {"_id": 0, "serial_number": 1, "brand": 1, "model": 1})
        if device:
            order["device_serial"] = device.get("serial_number")
            order["device_name"] = f"{device.get('brand', '')} {device.get('model', '')}"
    
    return orders

# --- Company AMC Contracts ---

@api_router.get("/company/amc-contracts")
async def list_company_amc_contracts(user: dict = Depends(get_current_company_user)):
    """List all AMC contracts for the company"""
    contracts = await db.amc_contracts.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    today = get_ist_now().date()
    result = []
    
    for contract in contracts:
        end_date = contract.get("end_date")
        if end_date:
            try:
                end = datetime.strptime(end_date, "%Y-%m-%d").date()
                days_left = (end - today).days
                contract["status"] = "active" if days_left > 0 else "expired"
                contract["days_remaining"] = max(0, days_left)
            except:
                contract["status"] = "unknown"
                contract["days_remaining"] = 0
        
        # Count covered devices
        device_count = await db.amc_device_assignments.count_documents({
            "amc_contract_id": contract["id"],
            "status": "active"
        })
        contract["devices_covered"] = device_count
        
        result.append(contract)
    
    return result

# --- AI Support Chat ---

class AISupportMessage(BaseModel):
    message: str
    session_id: str
    message_history: list = []
    device_id: Optional[str] = None

class AISupportSummaryRequest(BaseModel):
    messages: list

@api_router.post("/company/ai-support/chat")
async def ai_support_chat(data: AISupportMessage, user: dict = Depends(get_current_company_user)):
    """
    AI-powered support chat for troubleshooting before ticket creation.
    Returns AI response and whether escalation is suggested.
    """
    from services.ai_support import get_ai_response
    
    # Get device context if device_id provided
    device_context = None
    if data.device_id:
        device = await db.devices.find_one({
            "id": data.device_id,
            "company_id": user["company_id"]
        }, {"_id": 0})
        
        if device:
            # Get warranty info
            warranty = await db.warranties.find_one({
                "device_id": data.device_id,
                "is_deleted": {"$ne": True}
            }, {"_id": 0})
            
            # Get recent service tickets for this device (V2)
            recent_tickets = await db.tickets_v2.find({
                "device_id": data.device_id,
                "is_deleted": {"$ne": True}
            }, {"_id": 0, "subject": 1, "current_stage_name": 1, "created_at": 1}).sort("created_at", -1).limit(3).to_list(3)
            
            service_history = ""
            if recent_tickets:
                history_items = [f"{t.get('subject', 'Issue')} ({t.get('current_stage_name', 'New')})" for t in recent_tickets]
                service_history = "; ".join(history_items)
            
            # Build comprehensive device context
            device_context = {
                "device_name": device.get("device_name", ""),
                "device_type": device.get("device_type", ""),
                "serial_number": device.get("serial_number", ""),
                "model": device.get("model", ""),
                "brand": device.get("brand", ""),
                "specifications": device.get("specifications", ""),
                "color_type": device.get("color_type", device.get("printer_type", "")),  # For printers
                "warranty_status": warranty.get("status", "unknown") if warranty else "no warranty",
                "warranty_end_date": warranty.get("end_date", "N/A") if warranty else "N/A",
                "service_history": service_history
            }
    
    # Get AI response
    result = await get_ai_response(
        session_id=f"{user['id']}_{data.session_id}",
        user_message=data.message,
        message_history=data.message_history,
        device_context=device_context
    )
    
    return {
        "response": result["response"],
        "should_escalate": result["should_escalate"],
        "session_id": data.session_id
    }

@api_router.post("/company/ai-support/generate-summary")
async def generate_ai_summary(data: AISupportSummaryRequest, user: dict = Depends(get_current_company_user)):
    """
    Generate ticket subject and description from AI chat history using AI summarization.
    Uses company user context for isolation.
    """
    from services.ai_support import generate_ticket_summary_ai
    
    summary = await generate_ticket_summary_ai(data.messages)
    return summary

class AISupportHistoryRequest(BaseModel):
    device_id: str
    messages: list
    resolved: bool = False
    session_id: str

@api_router.post("/company/ai-support/save-history")
async def save_ai_chat_history(data: AISupportHistoryRequest, user: dict = Depends(get_current_company_user)):
    """
    Save AI chat history to device service history.
    Called when chat ends (resolved or escalated to ticket).
    """
    # Verify device belongs to company
    device = await db.devices.find_one({
        "id": data.device_id,
        "company_id": user["company_id"]
    }, {"_id": 0})
    
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Create AI support history record
    history_record = {
        "id": str(uuid.uuid4()),
        "device_id": data.device_id,
        "company_id": user["company_id"],
        "user_id": user["id"],
        "user_name": user["name"],
        "session_id": data.session_id,
        "messages": data.messages,
        "resolved_by_ai": data.resolved,
        "created_at": get_ist_isoformat(),
        "type": "ai_support_chat"
    }
    
    await db.ai_support_history.insert_one(history_record)
    
    # Also add to device service history for easy lookup
    service_note = {
        "id": str(uuid.uuid4()),
        "type": "ai_support",
        "description": f"AI Support Chat - {'Resolved' if data.resolved else 'Escalated to ticket'}",
        "messages_count": len([m for m in data.messages if m.get('role') == 'user']),
        "resolved": data.resolved,
        "user_name": user["name"],
        "created_at": get_ist_isoformat()
    }
    
    await db.devices.update_one(
        {"id": data.device_id},
        {"$push": {"ai_support_history": service_note}}
    )
    
    return {"success": True, "history_id": history_record["id"]}


# --- Company Email Subscriptions ---

@api_router.get("/company/subscriptions")
async def list_company_subscriptions(user: dict = Depends(get_current_company_user)):
    """List email/cloud subscriptions for the company"""
    subscriptions = await db.email_subscriptions.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("renewal_date", 1).to_list(100)
    
    # Update status based on renewal date
    for sub in subscriptions:
        sub["status"] = calculate_subscription_status(sub.get("renewal_date"), 30)
        if not sub.get("provider_name"):
            sub["provider_name"] = SUBSCRIPTION_PROVIDERS.get(sub.get("provider"), sub.get("provider", "Unknown"))
    
    return subscriptions


@api_router.get("/company/subscriptions/{subscription_id}")
async def get_company_subscription(subscription_id: str, user: dict = Depends(get_current_company_user)):
    """Get subscription details for company portal"""
    sub = await db.email_subscriptions.find_one({
        "id": subscription_id,
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0})
    
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    
    sub["status"] = calculate_subscription_status(sub.get("renewal_date"), 30)
    if not sub.get("provider_name"):
        sub["provider_name"] = SUBSCRIPTION_PROVIDERS.get(sub.get("provider"), sub.get("provider", "Unknown"))
    
    # Get tickets for this subscription
    tickets = await db.subscription_tickets.find({
        "subscription_id": subscription_id,
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("created_at", -1).limit(20).to_list(20)
    sub["tickets"] = tickets
    
    return sub


# --- Company Renewal Requests ---

@api_router.post("/company/renewal-requests")
async def create_renewal_request(data: RenewalRequestCreate, user: dict = Depends(get_current_company_user)):
    """Create a warranty/AMC renewal request"""
    # Verify device/contract belongs to company
    if data.device_id:
        device = await db.devices.find_one({
            "id": data.device_id,
            "company_id": user["company_id"],
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
    
    if data.amc_contract_id:
        contract = await db.amc_contracts.find_one({
            "id": data.amc_contract_id,
            "company_id": user["company_id"],
            "is_deleted": {"$ne": True}
        }, {"_id": 0})
        if not contract:
            raise HTTPException(status_code=404, detail="AMC contract not found")
    
    request = RenewalRequest(
        company_id=user["company_id"],
        request_type=data.request_type,
        device_id=data.device_id,
        amc_contract_id=data.amc_contract_id,
        requested_by=user["id"],
        notes=data.notes
    )
    
    await db.renewal_requests.insert_one(request.model_dump())
    
    return {"message": "Renewal request submitted", "request_number": request.request_number}

@api_router.get("/company/renewal-requests")
async def list_renewal_requests(user: dict = Depends(get_current_company_user)):
    """List renewal requests for the company"""
    requests = await db.renewal_requests.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("created_at", -1).to_list(100)
    
    return requests

# --- Company Profile ---

@api_router.get("/company/profile")
async def get_company_profile(user: dict = Depends(get_current_company_user)):
    """Get user profile with company info"""
    company = await db.companies.find_one({
        "id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0, "name": 1})
    
    # Return user profile data
    return {
        "id": user.get("id"),
        "name": user.get("name"),
        "email": user.get("email"),
        "phone": user.get("phone"),
        "role": user.get("role"),
        "company_id": user.get("company_id"),
        "company_name": company.get("name") if company else "Unknown",
        "created_at": user.get("created_at")
    }

@api_router.put("/company/profile")
async def update_company_profile(
    updates: dict,
    user: dict = Depends(get_current_company_user)
):
    """Update user profile - scoped to user's own record"""
    user_id = user.get("id")
    # Allow updating user's own profile fields
    user_fields = ["name", "phone"]
    password_fields = ["current_password", "new_password"]
    
    # Handle password change
    if updates.get("current_password") and updates.get("new_password"):
        # Validate new password strength
        is_valid, error_msg = validate_password_strength(updates["new_password"])
        if not is_valid:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Verify current password
        stored_user = await db.company_users.find_one({"id": user["id"]})
        if not stored_user or not verify_password(
            updates["current_password"],
            stored_user["password_hash"]
        ):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        
        # Update password
        new_hash = get_password_hash(updates["new_password"])
        await db.company_users.update_one(
            {"id": user["id"]},
            {"$set": {"password_hash": new_hash, "updated_at": get_ist_isoformat()}}
        )
        return {"message": "Password changed successfully"}
    
    # Handle profile update
    update_data = {k: v for k, v in updates.items() if k in user_fields and v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid fields to update")
    
    update_data["updated_at"] = get_ist_isoformat()
    
    await db.company_users.update_one(
        {"id": user["id"]},
        {"$set": update_data}
    )
    
    return {"message": "Profile updated successfully"}

# --- Company Deployments/Users (Read-Only) ---

@api_router.get("/company/deployments")
async def list_company_deployments(user: dict = Depends(get_current_company_user)):
    """List deployments for the company"""
    deployments = await db.deployments.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).sort("deployment_date", -1).to_list(100)
    
    for dep in deployments:
        site = await db.sites.find_one({"id": dep.get("site_id")}, {"_id": 0, "name": 1})
        dep["site_name"] = site.get("name") if site else None
        dep["items_count"] = len(dep.get("items", []))
    
    return deployments

@api_router.get("/company/users")
async def list_company_users_contacts(user: dict = Depends(get_current_company_user)):
    """List users/contacts for the company"""
    users = await db.users.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(500)
    
    return users

@api_router.get("/company/sites")
async def list_company_sites(user: dict = Depends(get_current_company_user)):
    """List sites for the company"""
    sites = await db.sites.find({
        "company_id": user["company_id"],
        "is_deleted": {"$ne": True}
    }, {"_id": 0}).to_list(100)
    
    return sites

# --- Admin: Company User Management ---

@api_router.get("/admin/company-users")
async def list_company_users(
    company_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List company portal users (admin only)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    if company_id:
        query["company_id"] = company_id
    
    users = await db.company_users.find(query, {"_id": 0, "password_hash": 0}).to_list(500)
    
    # Add company names
    for u in users:
        company = await db.companies.find_one(scope_query({"id": u["company_id"]}, org_id), {"_id": 0, "name": 1})
        u["company_name"] = company.get("name") if company else None
    
    return users

@api_router.post("/admin/company-users")
async def create_company_user(data: CompanyUserCreate, admin: dict = Depends(get_current_admin)):
    """Create company portal user (admin only)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Check if company exists
    company = await db.companies.find_one(scope_query({"id": data.company_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    # Check if email already exists
    existing = await db.company_users.find_one(scope_query({"email": data.email.lower()}, org_id), {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = CompanyUser(
        company_id=data.company_id,
        email=data.email.lower(),
        password_hash=get_password_hash(data.password),
        name=data.name,
        phone=data.phone,
        role=data.role,
        created_by=admin.get("email")
    )
    
    user_ins_dict["organization_id"] = org_id
    user_ins_dict = user.model_dump()
    await db.company_users.insert_one(user_ins_dict)
    
    return {"message": "Company user created", "id": user.id}

@api_router.put("/admin/company-users/{user_id}")
async def update_company_user(user_id: str, updates: CompanyUserUpdate, admin: dict = Depends(get_current_admin)):
    """Update company portal user (admin only)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    result = await db.company_users.update_one(scope_query({"id": user_id}, org_id), {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User updated"}

@api_router.post("/admin/company-users/{user_id}/reset-password")
async def reset_company_user_password(user_id: str, new_password: str, admin: dict = Depends(get_current_admin)):
    """Reset company user password (admin only) with strong validation"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Validate password strength
    is_valid, error_msg = validate_password_strength(new_password)
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
    result = await db.company_users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": get_password_hash(new_password)}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "Password reset successfully"}

@api_router.delete("/admin/company-users/{user_id}")
async def delete_company_user(user_id: str, admin: dict = Depends(get_current_admin)):
    """Delete company portal user (admin only)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.company_users.update_one(scope_query({"id": user_id}, org_id), {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {"message": "User deleted"}


# ==================== INTERNET SERVICES / ISP ENDPOINTS ====================

@api_router.get("/admin/internet-services")
async def list_internet_services(
    company_id: Optional[str] = None,
    site_id: Optional[str] = None,
    status: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all internet services/ISP connections"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    if company_id:
        query["company_id"] = company_id
    if site_id:
        query["site_id"] = site_id
    if status:
        query["status"] = status
    
    services = await db.internet_services.find(query).sort("created_at", -1).to_list(1000)
    
    # Enrich with company and site names
    for service in services:
        company = await db.companies.find_one(scope_query({"id": service.get("company_id")}, org_id))
        service["company_name"] = company.get("name") if company else "Unknown"
        if service.get("site_id"):
            site = await db.sites.find_one(scope_query({"id": service["site_id"]}, org_id))
            service["site_name"] = site.get("name") if site else None
        service.pop("_id", None)
    
    return services


@api_router.post("/admin/internet-services")
async def create_internet_service(data: InternetServiceCreate, admin: dict = Depends(get_current_admin)):
    """Create a new internet service record"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = InternetService(**data.model_dump())
    service_ins_dict["organization_id"] = org_id
    service_ins_dict = service.model_dump()
    await db.internet_services.insert_one(service_ins_dict)
    
    result = service.model_dump()
    result.pop("_id", None)
    return result


@api_router.get("/admin/internet-services/{service_id}")
async def get_internet_service(service_id: str, admin: dict = Depends(get_current_admin)):
    """Get internet service details"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    service = await db.internet_services.find_one(scope_query({"id": service_id, "is_deleted": {"$ne": True}}, org_id))
    if not service:
        raise HTTPException(status_code=404, detail="Internet service not found")
    
    company = await db.companies.find_one(scope_query({"id": service.get("company_id")}, org_id))
    service["company_name"] = company.get("name") if company else "Unknown"
    if service.get("site_id"):
        site = await db.sites.find_one(scope_query({"id": service["site_id"]}, org_id))
        service["site_name"] = site.get("name") if site else None
    
    service.pop("_id", None)
    return service


@api_router.put("/admin/internet-services/{service_id}")
async def update_internet_service(service_id: str, data: InternetServiceUpdate, admin: dict = Depends(get_current_admin)):
    """Update internet service"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.internet_services.update_one(
        {"id": service_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Internet service not found")
    
    updated = await db.internet_services.find_one(scope_query({"id": service_id}, org_id))
    updated.pop("_id", None)
    return updated


@api_router.delete("/admin/internet-services/{service_id}")
async def delete_internet_service(service_id: str, admin: dict = Depends(get_current_admin)):
    """Delete internet service"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.internet_services.update_one(
        {"id": service_id},
        {"$set": {"is_deleted": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Internet service not found")
    return {"message": "Internet service deleted"}


# ==================== CREDENTIALS DASHBOARD ENDPOINTS ====================

@api_router.get("/admin/credentials")
async def list_all_credentials(
    company_id: Optional[str] = None,
    credential_type: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """
    Get all credentials across devices and internet services.
    Returns a consolidated view for the credentials dashboard.
    credential_type: device, internet, all
    """
    org_id = await get_admin_org_id(admin.get("email", ""))
    credentials = []
    
    # Device credentials
    if credential_type in [None, "all", "device"]:
        device_query = {"is_deleted": {"$ne": True}, "credentials": {"$ne": None}}
        if company_id:
            device_query["company_id"] = company_id
        
        devices = await db.devices.find(device_query).to_list(1000)
        for device in devices:
            if device.get("credentials"):
                company = await db.companies.find_one(scope_query({"id": device.get("company_id")}, org_id))
                credentials.append({
                    "id": device["id"],
                    "source_type": "device",
                    "source_name": f"{device.get('brand', '')} {device.get('model', '')}".strip(),
                    "device_type": device.get("device_type"),
                    "serial_number": device.get("serial_number"),
                    "company_id": device.get("company_id"),
                    "company_name": company.get("name") if company else "Unknown",
                    "location": device.get("location"),
                    "credentials": device.get("credentials"),
                    "created_at": device.get("created_at")
                })
    
    # Internet service credentials
    if credential_type in [None, "all", "internet"]:
        isp_query = {"is_deleted": {"$ne": True}}
        if company_id:
            isp_query["company_id"] = company_id
        
        services = await db.internet_services.find(isp_query).to_list(1000)
        for service in services:
            company = await db.companies.find_one(scope_query({"id": service.get("company_id")}, org_id))
            site_name = None
            if service.get("site_id"):
                site = await db.sites.find_one(scope_query({"id": service["site_id"]}, org_id))
                site_name = site.get("name") if site else None
            
            # Extract credential-related fields
            creds = {
                "router_ip": service.get("router_ip"),
                "router_username": service.get("router_username"),
                "router_password": service.get("router_password"),
                "wifi_ssid": service.get("wifi_ssid"),
                "wifi_password": service.get("wifi_password"),
                "pppoe_username": service.get("pppoe_username"),
                "pppoe_password": service.get("pppoe_password"),
                "static_ip": service.get("static_ip"),
                "gateway": service.get("gateway"),
            }
            # Only include if has any credentials
            if any(creds.values()):
                credentials.append({
                    "id": service["id"],
                    "source_type": "internet",
                    "source_name": service.get("provider_name", "ISP"),
                    "device_type": service.get("connection_type"),
                    "serial_number": service.get("account_number"),
                    "company_id": service.get("company_id"),
                    "company_name": company.get("name") if company else "Unknown",
                    "site_name": site_name,
                    "location": site_name,
                    "credentials": creds,
                    "plan_name": service.get("plan_name"),
                    "support_phone": service.get("support_phone"),
                    "created_at": service.get("created_at")
                })
    
    return credentials


# ==================== OFFICE SUPPLIES ADMIN ENDPOINTS ====================

@api_router.get("/admin/supply-categories")
async def list_supply_categories(admin: dict = Depends(get_current_admin)):
    """List all supply categories"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    categories = await db.supply_categories.find(
        {"is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("sort_order", 1).to_list(100)
    return categories

@api_router.post("/admin/supply-categories")
async def create_supply_category(data: SupplyCategoryCreate, admin: dict = Depends(get_current_admin)):
    """Create a new supply category"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    category = SupplyCategory(**data.model_dump())
    category_ins_dict["organization_id"] = org_id
    category_ins_dict = category.model_dump()
    await db.supply_categories.insert_one(category_ins_dict)
    return category.model_dump()

@api_router.put("/admin/supply-categories/{category_id}")
async def update_supply_category(category_id: str, data: SupplyCategoryUpdate, admin: dict = Depends(get_current_admin)):
    """Update a supply category"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    result = await db.supply_categories.update_one(
        {"id": category_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updated = await db.supply_categories.find_one(scope_query({"id": category_id}, org_id), {"_id": 0})
    return updated

@api_router.delete("/admin/supply-categories/{category_id}")
async def delete_supply_category(category_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a supply category"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.supply_categories.update_one(
        {"id": category_id},
        {"$set": {"is_deleted": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted"}

@api_router.get("/admin/supply-products")
async def list_supply_products(category_id: Optional[str] = None, admin: dict = Depends(get_current_admin)):
    """List all supply products, optionally filtered by category"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    if category_id:
        query["category_id"] = category_id
    
    products = await db.supply_products.find(query, {"_id": 0}).to_list(500)
    
    # Add category name to each product
    categories = {c["id"]: c["name"] for c in await db.supply_categories.find({}, {"_id": 0, "id": 1, "name": 1}).to_list(100)}
    for product in products:
        product["category_name"] = categories.get(product["category_id"], "Unknown")
    
    return products

@api_router.post("/admin/supply-products")
async def create_supply_product(data: SupplyProductCreate, admin: dict = Depends(get_current_admin)):
    """Create a new supply product"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    # Verify category exists
    category = await db.supply_categories.find_one(scope_query({"id": data.category_id, "is_deleted": {"$ne": True}}, org_id))
    if not category:
        raise HTTPException(status_code=400, detail="Category not found")
    
    product = SupplyProduct(**data.model_dump())
    product_ins_dict["organization_id"] = org_id
    product_ins_dict = product.model_dump()
    await db.supply_products.insert_one(product_ins_dict)
    
    result = product.model_dump()
    result["category_name"] = category["name"]
    return result

@api_router.put("/admin/supply-products/{product_id}")
async def update_supply_product(product_id: str, data: SupplyProductUpdate, admin: dict = Depends(get_current_admin)):
    """Update a supply product"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No data to update")
    
    # If category is being changed, verify it exists
    if "category_id" in update_data:
        category = await db.supply_categories.find_one(scope_query({"id": update_data["category_id"], "is_deleted": {"$ne": True}}, org_id))
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
    
    result = await db.supply_products.update_one(
        {"id": product_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    updated = await db.supply_products.find_one(scope_query({"id": product_id}, org_id), {"_id": 0})
    category = await db.supply_categories.find_one(scope_query({"id": updated["category_id"]}, org_id), {"_id": 0})
    updated["category_name"] = category["name"] if category else "Unknown"
    return updated

@api_router.delete("/admin/supply-products/{product_id}")
async def delete_supply_product(product_id: str, admin: dict = Depends(get_current_admin)):
    """Soft delete a supply product"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    result = await db.supply_products.update_one(
        {"id": product_id},
        {"$set": {"is_deleted": True}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    return {"message": "Product deleted"}

@api_router.post("/admin/supply-products/bulk-delete")
async def bulk_delete_supply_products(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk soft delete supply products"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    product_ids = data.get("product_ids", [])
    if not product_ids:
        raise HTTPException(status_code=400, detail="No products selected")
    
    result = await db.supply_products.update_many(
        {"id": {"$in": product_ids}},
        {"$set": {"is_deleted": True}}
    )
    return {"message": f"{result.modified_count} products deleted"}

@api_router.post("/admin/supply-products/bulk-update")
async def bulk_update_supply_products(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk update supply products (category, status, price)"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    product_ids = data.get("product_ids", [])
    updates = data.get("updates", {})
    
    if not product_ids:
        raise HTTPException(status_code=400, detail="No products selected")
    if not updates:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    # Only allow certain fields to be bulk updated
    allowed_fields = {"category_id", "is_active", "price", "unit"}
    update_data = {k: v for k, v in updates.items() if k in allowed_fields and v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid updates provided")
    
    result = await db.supply_products.update_many(
        {"id": {"$in": product_ids}},
        {"$set": update_data}
    )
    return {"message": f"{result.modified_count} products updated"}

@api_router.get("/admin/supply-orders")
async def list_supply_orders(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List all supply orders with optional filters"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    query = {"is_deleted": {"$ne": True}}
    if status:
        query["status"] = status
    if company_id:
        query["company_id"] = company_id
    
    orders = await db.supply_orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return orders

@api_router.get("/admin/supply-orders/{order_id}")
async def get_supply_order(order_id: str, admin: dict = Depends(get_current_admin)):
    """Get a specific supply order"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    order = await db.supply_orders.find_one(scope_query({"id": order_id, "is_deleted": {"$ne": True}}, org_id), {"_id": 0})
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@api_router.put("/admin/supply-orders/{order_id}")
async def update_supply_order(order_id: str, data: dict, admin: dict = Depends(get_current_admin)):
    """Update supply order status and admin notes"""
    org_id = await get_admin_org_id(admin.get("email", ""))
    allowed_fields = ["status", "admin_notes"]
    update_data = {k: v for k, v in data.items() if k in allowed_fields and v is not None}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No valid data to update")
    
    # Add processing info
    update_data["processed_by"] = admin.get("name", admin.get("email"))
    update_data["processed_at"] = get_ist_isoformat()
    
    result = await db.supply_orders.update_one(
        {"id": order_id, "is_deleted": {"$ne": True}},
        {"$set": update_data}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Order not found")
    
    updated = await db.supply_orders.find_one(scope_query({"id": order_id}, org_id), {"_id": 0})
    return updated

# ==================== OFFICE SUPPLIES COMPANY ENDPOINTS ====================

@api_router.get("/company/supply-catalog")
async def get_supply_catalog(user: dict = Depends(get_current_company_user)):
    """Get supply catalog (categories with their products) for ordering"""
    org_id = user.get("organization_id")
    # Get active categories - scoped by org
    cat_query = {"is_deleted": {"$ne": True}, "is_active": True}
    if org_id:
        cat_query["organization_id"] = org_id
    categories = await db.supply_categories.find(
        cat_query,
        {"_id": 0}
    ).sort("sort_order", 1).to_list(100)
    
    # Get active products - scoped by org
    prod_query = {"is_deleted": {"$ne": True}, "is_active": True}
    if org_id:
        prod_query["organization_id"] = org_id
    products = await db.supply_products.find(
        prod_query,
        {"_id": 0, "internal_notes": 0}  # Exclude internal notes from company view
    ).to_list(500)
    
    # Group products by category
    products_by_category = {}
    for product in products:
        cat_id = product["category_id"]
        if cat_id not in products_by_category:
            products_by_category[cat_id] = []
        products_by_category[cat_id].append(product)
    
    # Combine categories with their products
    catalog = []
    for category in categories:
        category["products"] = products_by_category.get(category["id"], [])
        if category["products"]:  # Only include categories that have products
            catalog.append(category)
    
    return catalog

@api_router.post("/company/supply-orders")
async def create_supply_order(data: dict, user: dict = Depends(get_current_company_user)):
    """Create a new supply order"""
    items = data.get("items", [])
    if not items:
        raise HTTPException(status_code=400, detail="No items in order")
    
    delivery = data.get("delivery_location", {})
    if not delivery:
        raise HTTPException(status_code=400, detail="Delivery location is required")
    
    # Get company info
    company = await db.companies.find_one({"id": user["company_id"]}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=400, detail="Company not found")
    
    # Validate products and build order items
    order_items = []
    for item in items:
        product = await db.supply_products.find_one(
            {"id": item["product_id"], "is_deleted": {"$ne": True}, "is_active": True},
            {"_id": 0}
        )
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item['product_id']} not found or inactive")
        
        category = await db.supply_categories.find_one({"id": product["category_id"]}, {"_id": 0})
        
        order_items.append({
            "product_id": product["id"],
            "product_name": product["name"],
            "category_name": category["name"] if category else "Unknown",
            "quantity": item.get("quantity", 1),
            "unit": product["unit"]
        })
    
    # Process delivery location
    delivery_location = {"type": delivery.get("type", "existing")}
    
    if delivery.get("type") == "existing" and delivery.get("site_id"):
        site = await db.sites.find_one({"id": delivery["site_id"]}, {"_id": 0})
        if site:
            delivery_location.update({
                "site_id": site["id"],
                "site_name": site["name"],
                "address": site.get("address"),
                "city": site.get("city"),
                "pincode": site.get("pincode"),
                "contact_person": site.get("contact_person"),
                "contact_phone": site.get("contact_phone")
            })
    else:
        # New location
        delivery_location.update({
            "type": "new",
            "address": delivery.get("address"),
            "city": delivery.get("city"),
            "pincode": delivery.get("pincode"),
            "contact_person": delivery.get("contact_person"),
            "contact_phone": delivery.get("contact_phone")
        })
    
    # Create order
    order = SupplyOrder(
        company_id=user["company_id"],
        company_name=company.get("name", "Unknown"),
        requested_by=user["id"],
        requested_by_name=user.get("name", "Unknown"),
        requested_by_email=user.get("email", ""),
        requested_by_phone=user.get("phone"),
        delivery_location=delivery_location,
        items=order_items,
        notes=data.get("notes")
    )
    
    await db.supply_orders.insert_one(order.model_dump())
    
    # Build osTicket message
    items_table = """
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr style="background-color: #f0f0f0;">
<th>#</th><th>Item</th><th>Category</th><th>Quantity</th><th>Unit</th>
</tr>
"""
    for idx, item in enumerate(order_items, 1):
        items_table += f"""
<tr>
<td>{idx}</td>
<td><strong>{item['product_name']}</strong></td>
<td>{item['category_name']}</td>
<td><strong>{item['quantity']}</strong></td>
<td>{item['unit']}</td>
</tr>
"""
    items_table += "</table>"
    
    # Format delivery address
    delivery_addr = delivery_location.get("address", "")
    if delivery_location.get("city"):
        delivery_addr += f", {delivery_location['city']}"
    if delivery_location.get("pincode"):
        delivery_addr += f" - {delivery_location['pincode']}"
    
    osticket_message = f"""
<h2>OFFICE SUPPLIES ORDER</h2>
<p><strong>Order Number:</strong> {order.order_number}</p>
<p><strong>Order Type:</strong> Office Supplies</p>
<p><strong>Order Date:</strong> {order.created_at.split('T')[0]}</p>
<p><strong>Status:</strong> REQUESTED</p>

<hr>
<h3>ITEMS ORDERED ({len(order_items)} items)</h3>
{items_table}

<hr>
<h3>DELIVERY LOCATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Location Type</strong></td><td>{delivery_location.get('type', 'N/A').upper()}</td></tr>
{f"<tr><td><strong>Site Name</strong></td><td>{delivery_location.get('site_name', 'N/A')}</td></tr>" if delivery_location.get('site_name') else ""}
<tr><td><strong>Address</strong></td><td>{delivery_addr or 'N/A'}</td></tr>
<tr><td><strong>Contact Person</strong></td><td>{delivery_location.get('contact_person', 'N/A')}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{delivery_location.get('contact_phone', 'N/A')}</td></tr>
</table>

<hr>
<h3>COMPANY INFORMATION</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Company Name</strong></td><td>{company.get('name', 'N/A')}</td></tr>
<tr><td><strong>Company ID</strong></td><td>{company.get('company_code') or company.get('id', 'N/A')}</td></tr>
<tr><td><strong>Contact Email</strong></td><td>{company.get('contact_email', 'N/A')}</td></tr>
<tr><td><strong>Contact Phone</strong></td><td>{company.get('contact_phone', 'N/A')}</td></tr>
</table>

<hr>
<h3>REQUESTED BY</h3>
<table border="1" cellpadding="8" cellspacing="0" style="border-collapse: collapse; width: 100%;">
<tr><td><strong>Name</strong></td><td>{user.get('name', 'N/A')}</td></tr>
<tr><td><strong>Email</strong></td><td>{user.get('email', 'N/A')}</td></tr>
<tr><td><strong>Phone</strong></td><td>{user.get('phone', 'N/A')}</td></tr>
</table>

{f"<hr><h3>SPECIAL INSTRUCTIONS / NOTES</h3><p>{order.notes}</p>" if order.notes else ""}

<hr>
<p style="color: #666; font-size: 12px;">
<em>This order was submitted from the Warranty & Asset Tracking Portal.<br>
Order Created: {get_ist_isoformat()}</em>
</p>
"""
    
    # Create osTicket
    osticket_result = await create_osticket(
        email=user.get("email", "noreply@warranty-portal.com"),
        name=user.get("name", "Portal User"),
        subject=f"[{order.order_number}] Office Supplies Order - {company.get('name', 'Company')}",
        message=osticket_message,
        phone=user.get("phone", "")
    )
    
    osticket_id = osticket_result.get("ticket_id")
    osticket_error = osticket_result.get("error")
    
    # Update order with osTicket ID
    if osticket_id:
        await db.supply_orders.update_one(
            {"id": order.id},
            {"$set": {"osticket_id": osticket_id}}
        )
    
    return {
        "message": "Order submitted successfully",
        "order_number": order.order_number,
        "id": order.id,
        "items_count": len(order_items),
        "osticket_id": osticket_id,
        "osticket_error": osticket_error
    }

@api_router.get("/company/supply-orders")
async def list_company_supply_orders(user: dict = Depends(get_current_company_user)):
    """List supply orders for the company"""
    orders = await db.supply_orders.find(
        {"company_id": user["company_id"], "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    return orders

# Include the router
app.include_router(api_router)

# Include AMC Requests router
from routes.amc_requests import router as amc_requests_router
app.include_router(amc_requests_router, prefix="/api")

# Include AMC Onboarding router
from routes.amc_onboarding import router as amc_onboarding_router, init_db as init_onboarding_db
init_onboarding_db(db)
app.include_router(amc_onboarding_router, prefix="/api")

# Include Organization (Multi-tenancy) router
from routes.organization import router as organization_router, init_db as init_org_db
init_org_db(db)
app.include_router(organization_router, prefix="/api/org", tags=["Organization"])

# Include Platform Admin (Super Admin) router
from routes.platform import router as platform_router, init_db as init_platform_db
init_platform_db(db)
app.include_router(platform_router, prefix="/api/platform", tags=["Platform Admin"])

# Include Billing (Razorpay) router
from routes.billing import router as billing_router, init_db as init_billing_db
init_billing_db(db)
app.include_router(billing_router, prefix="/api/billing", tags=["Billing"])

# Include Static Pages router
from routes.static_pages import router as static_pages_router, init_db as init_static_pages_db
init_static_pages_db(db)
app.include_router(static_pages_router, prefix="/api", tags=["Static Pages"])

# Include WatchTower Integration router
from routes.watchtower import router as watchtower_router, init_watchtower_router
init_watchtower_router(db)
app.include_router(watchtower_router, prefix="/api", tags=["WatchTower Integration"])

# Include MoltBot Integration router
from routes.moltbot import router as moltbot_router
app.include_router(moltbot_router, prefix="/api/admin", tags=["MoltBot Integration"])

# Initialize Email Service for Ticketing
from services.email_service import init_email_service
init_email_service(db)

# Include Knowledge Base router
from routes.knowledge_base import router as kb_router, init_kb_router
init_kb_router(db)
app.include_router(kb_router, prefix="/api", tags=["Knowledge Base"])

# Include Staff Module router
from routes.staff import router as staff_router
app.include_router(staff_router, tags=["Staff Module"])

# Include TGMS router
from routes.tgms import router as tgms_router
app.include_router(tgms_router, tags=["TGMS"])

# ==================== NEW SERVICE MODULE ROUTES ====================
# Problem Master
from routes.problem_master import router as problem_master_router
app.include_router(problem_master_router, tags=["Problem Master"])

# Item Master
from routes.item_master import router as item_master_router
app.include_router(item_master_router, tags=["Item Master"])

# Quotations
from routes.quotations import router as quotations_router
app.include_router(quotations_router, tags=["Quotations"])

# Inventory (Locations & Stock)
from routes.inventory_new import router as inventory_router
app.include_router(inventory_router, tags=["Inventory"])

# Vendor Master
from routes.vendor_master import router as vendor_router
app.include_router(vendor_router, tags=["Vendor Master"])

# Ticketing V2 (New configurable system)
from routes.ticketing_v2 import router as ticketing_v2_router, init_db as init_ticketing_v2_db
init_ticketing_v2_db(db)
app.include_router(ticketing_v2_router, prefix="/api", tags=["Ticketing V2"])

# Email Inbox Integration
from routes.email_inbox import router as email_inbox_router, init_db as init_email_inbox_db
init_email_inbox_db(db)
app.include_router(email_inbox_router, prefix="/api", tags=["Email Inbox"])

from routes.calendar import router as calendar_router, init_db as init_calendar_db
init_calendar_db(db)
app.include_router(calendar_router, prefix="/api", tags=["Calendar"])

from routes.job_acceptance import router as job_acceptance_router, init_db as init_job_acceptance_db
init_job_acceptance_db(db)
app.include_router(job_acceptance_router, prefix="/api", tags=["Job Acceptance"])

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    # Ensure uploads directory exists
    UPLOAD_DIR.mkdir(exist_ok=True)
    
    # Seed default supply categories and products
    await seed_default_supplies()
    
    # Auto-deduplicate and seed ticketing system for all organizations
    try:
        from models.ticketing_v2_seed import generate_seed_data
        orgs = await db.organizations.find({"is_deleted": {"$ne": True}}, {"_id": 0, "id": 1, "name": 1}).to_list(100)
        
        collections_config = [
            ("ticket_priorities", "priorities", "slug"),
            ("ticket_business_hours", "business_hours", "name"),
            ("ticket_sla_policies", "sla_policies", "name"),
            ("ticket_roles", "roles", "slug"),
            ("ticket_teams", "teams", "slug"),
            ("ticket_task_types", "task_types", "slug"),
            ("ticket_forms", "forms", "slug"),
            ("ticket_workflows", "workflows", "slug"),
            ("ticket_help_topics", "help_topics", "slug"),
            ("ticket_canned_responses", "canned_responses", "slug"),
            ("ticket_notification_templates", "notification_templates", "slug"),
        ]
        
        for org in orgs:
            org_id = org.get("id")
            if not org_id:
                continue
            
            # Step 1: Deduplicate existing data
            for coll_name, _, dedup_field in collections_config:
                docs = await db[coll_name].find(
                    {"organization_id": org_id}, {"_id": 0, "id": 1, dedup_field: 1}
                ).to_list(1000)
                seen = {}
                to_delete = []
                for doc in docs:
                    k = doc.get(dedup_field, doc.get("id"))
                    if k in seen:
                        to_delete.append(doc["id"])
                    else:
                        seen[k] = doc["id"]
                if to_delete:
                    await db[coll_name].delete_many({"id": {"$in": to_delete}, "organization_id": org_id})
                    print(f"Deduped {len(to_delete)} items from {coll_name} for org {org.get('name', org_id)}")
            
            # Step 2: Seed missing data
            data = generate_seed_data(org_id)
            seeded_any = False
            for coll_name, collection_key, dedup_field in collections_config:
                items = data.get(collection_key, [])
                if not items:
                    continue
                existing = set()
                async for doc in db[coll_name].find({"organization_id": org_id}, {dedup_field: 1, "_id": 0}):
                    existing.add(doc.get(dedup_field))
                new_items = [i for i in items if i.get(dedup_field) not in existing]
                if new_items:
                    await db[coll_name].insert_many(new_items)
                    seeded_any = True
            if seeded_any:
                print(f"Auto-seeded ticketing system for org: {org.get('name', org_id)}")
    except Exception as e:
        print(f"Ticketing auto-seed error (non-fatal): {e}")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
