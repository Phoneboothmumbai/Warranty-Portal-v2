"""
Public endpoints - Warranty search, public settings, masters
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import inch
from fastapi.responses import StreamingResponse

from database import db
from models.common import Settings
from utils.helpers import get_ist_now, is_warranty_active

router = APIRouter(tags=["Public"])


@router.get("/")
async def root():
    return {"message": "Warranty & Asset Tracking Portal API"}


@router.get("/settings/public")
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


@router.get("/masters/public")
async def get_public_masters(
    master_type: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = Query(default=50, le=200)
):
    """Get active masters for public forms with optional search"""
    query = {"is_active": True}
    if master_type:
        query["type"] = master_type
    
    if q and q.strip():
        search_regex = {"$regex": q.strip(), "$options": "i"}
        query["$or"] = [
            {"name": search_regex},
            {"code": search_regex}
        ]
    
    masters = await db.masters.find(query, {"_id": 0}).sort("sort_order", 1).to_list(limit)
    
    for m in masters:
        m["label"] = m["name"]
    
    return masters


@router.get("/warranty/search")
async def search_warranty(q: str):
    """
    Search warranty by serial number or asset tag
    Searches both Devices and Parts
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
        device = await db.devices.find_one(
            {"id": part["device_id"], "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
        
        company_name = "Unknown"
        if device:
            company = await db.companies.find_one({"id": device["company_id"], "is_deleted": {"$ne": True}}, {"_id": 0, "name": 1})
            company_name = company.get("name") if company else "Unknown"
        
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
    
    company = await db.companies.find_one({"id": device["company_id"], "is_deleted": {"$ne": True}}, {"_id": 0, "name": 1})
    company_name = company.get("name") if company else "Unknown"
    
    assigned_user = None
    if device.get("assigned_user_id"):
        user = await db.users.find_one({"id": device["assigned_user_id"], "is_deleted": {"$ne": True}}, {"_id": 0, "name": 1})
        assigned_user = user.get("name") if user else None
    
    device_warranty_expiry = device.get("warranty_end_date")
    device_warranty_active = is_warranty_active(device_warranty_expiry) if device_warranty_expiry else False
    
    active_amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device["id"],
        "status": "active"
    }, {"_id": 0})
    
    amc_contract_info = None
    amc_coverage_active = False
    coverage_source = "device_warranty"
    effective_coverage_end = device_warranty_expiry
    
    if active_amc_assignment:
        amc_coverage_active = is_warranty_active(active_amc_assignment.get("coverage_end", ""))
        
        if amc_coverage_active:
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
    
    legacy_amc = await db.amc.find_one({"device_id": device["id"], "is_deleted": {"$ne": True}}, {"_id": 0})
    legacy_amc_info = None
    if legacy_amc:
        legacy_amc_active = is_warranty_active(legacy_amc.get("end_date", ""))
        legacy_amc_info = {
            "start_date": legacy_amc.get("start_date"),
            "end_date": legacy_amc.get("end_date"),
            "active": legacy_amc_active
        }
        
        if not amc_coverage_active and legacy_amc_active:
            coverage_source = "legacy_amc"
            effective_coverage_end = legacy_amc.get("end_date")
    
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
    
    service_count = await db.service_history.count_documents({"device_id": device["id"]})
    
    final_warranty_active = amc_coverage_active or device_warranty_active
    if amc_coverage_active:
        final_warranty_active = True
    
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
            "device_warranty_active": device_warranty_active,
            "condition": device.get("condition"),
            "status": device.get("status")
        },
        "company_name": company_name,
        "assigned_user": assigned_user,
        "parts": parts,
        "amc": legacy_amc_info,
        "amc_contract": amc_contract_info,
        "coverage_source": coverage_source,
        "effective_coverage_end": effective_coverage_end,
        "service_count": service_count
    }


@router.get("/warranty/pdf/{serial_number}")
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
    
    active_amc_assignment = await db.amc_device_assignments.find_one({
        "device_id": device["id"],
        "status": "active"
    }, {"_id": 0})
    
    amc_contract_info = None
    if active_amc_assignment:
        if is_warranty_active(active_amc_assignment.get("coverage_end", "")):
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
        
        coverage_items = []
        if coverage_includes.get("onsite_support"):
            coverage_items.append("Onsite Support")
        if coverage_includes.get("remote_support"):
            coverage_items.append("Remote Support")
        if coverage_includes.get("preventive_maintenance"):
            coverage_items.append("Preventive Maintenance")
        coverage_str = ", ".join(coverage_items) if coverage_items else "Standard Coverage"
        
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
