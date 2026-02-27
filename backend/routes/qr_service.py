"""
QR Code generation and Quick Service Request endpoints
"""
import os
import uuid
import qrcode
from io import BytesIO
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from database import db
from services.auth import get_current_admin
from services.osticket import create_osticket
from utils.helpers import get_ist_now, get_ist_isoformat, is_warranty_active

router = APIRouter(tags=["QR & Quick Service"])


class QuickServiceRequest(BaseModel):
    """Quick service request without login"""
    name: str
    email: str
    phone: Optional[str] = None
    issue_category: str = "other"
    description: str


class BulkQRRequest(BaseModel):
    """Request body for bulk QR code generation"""
    device_ids: Optional[List[str]] = None
    company_id: Optional[str] = None
    site_id: Optional[str] = None


@router.get("/device/{identifier}/qr")
async def generate_device_qr_code(identifier: str):
    """Generate a printable PDF with single QR code (1.5 inch x 1.5 inch)."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    
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
    
    frontend_url = os.environ.get('FRONTEND_URL', '')
    if not frontend_url:
        cors_origins = os.environ.get('CORS_ORIGINS', '')
        if cors_origins and cors_origins != '*':
            frontend_url = cors_origins.split(',')[0].strip()
        else:
            frontend_url = "https://your-portal-url.com"
    
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
    qr_img = qr_img.resize((300, 300), Image.Resampling.LANCZOS)
    
    qr_buffer = BytesIO()
    qr_img.save(qr_buffer, format='PNG')
    qr_buffer.seek(0)
    qr_reader = ImageReader(qr_buffer)
    
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=A4)
    page_width, page_height = A4
    
    qr_size = 1.5 * inch
    label_height = 0.4 * inch
    total_height = qr_size + label_height
    
    x = (page_width - qr_size) / 2
    y = (page_height - total_height) / 2 + label_height
    
    c.drawImage(qr_reader, x, y, width=qr_size, height=qr_size)
    
    c.setStrokeColorRGB(0.8, 0.8, 0.8)
    c.setLineWidth(0.5)
    margin = 5
    c.rect(x - margin, y - label_height - margin, qr_size + 2*margin, total_height + 2*margin)
    
    text_x = page_width / 2
    
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(text_x, y - 15, f"S/N: {device.get('serial_number', 'N/A')}")
    
    if device.get('asset_tag'):
        c.setFont("Helvetica", 9)
        c.drawCentredString(text_x, y - 28, f"Tag: {device['asset_tag']}")
    
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


@router.post("/devices/bulk-qr-pdf")
async def generate_bulk_qr_pdf(
    request: BulkQRRequest,
    admin: dict = Depends(get_current_admin)
):
    """Generate a printable A4 PDF with multiple QR codes."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from PIL import Image
    
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    query = {"is_deleted": {"$ne": True}, "organization_id": org_id}
    
    if request.device_ids and len(request.device_ids) > 0:
        query["id"] = {"$in": request.device_ids}
    elif request.site_id:
        query["site_id"] = request.site_id
    elif request.company_id:
        query["company_id"] = request.company_id
    
    devices = await db.devices.find(
        query,
        {"_id": 0, "id": 1, "serial_number": 1, "asset_tag": 1, "brand": 1, "model": 1}
    ).sort("serial_number", 1).to_list(500)
    
    if not devices:
        raise HTTPException(status_code=404, detail="No devices found matching criteria")
    
    frontend_url = os.environ.get('FRONTEND_URL', '')
    if not frontend_url:
        cors_origins = os.environ.get('CORS_ORIGINS', '')
        if cors_origins and cors_origins != '*':
            frontend_url = cors_origins.split(',')[0].strip()
        else:
            frontend_url = "https://your-portal-url.com"
    
    page_width, page_height = A4
    
    qr_size = 1.5 * inch
    label_height = 0.35 * inch
    cell_padding = 0.15 * inch
    
    cell_width = qr_size + cell_padding
    cell_height = qr_size + label_height + cell_padding
    
    margin_x = (page_width - (4 * cell_width)) / 2
    margin_y = 0.5 * inch
    
    columns = 4
    rows_per_page = 5
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    
    current_row = 0
    current_col = 0
    
    for device in devices:
        x = margin_x + (current_col * cell_width)
        y = page_height - margin_y - ((current_row + 1) * cell_height)
        
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
        qr_img = qr_img.resize((300, 300), Image.Resampling.LANCZOS)
        
        qr_buffer = BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_reader = ImageReader(qr_buffer)
        
        qr_x = x + (cell_width - qr_size) / 2
        qr_y = y + label_height
        c.drawImage(qr_reader, qr_x, qr_y, width=qr_size, height=qr_size)
        
        serial = device.get('serial_number', 'N/A')
        asset_tag = device.get('asset_tag', '')
        text_x = x + cell_width / 2
        
        c.setFont("Helvetica-Bold", 7)
        c.setFillColorRGB(0, 0, 0)
        serial_display = serial if len(serial) <= 20 else serial[:17] + "..."
        c.drawCentredString(text_x, y + label_height - 12, f"S/N: {serial_display}")
        
        if asset_tag:
            c.setFont("Helvetica", 6)
            c.setFillColorRGB(0.3, 0.3, 0.3)
            tag_display = asset_tag if len(asset_tag) <= 20 else asset_tag[:17] + "..."
            c.drawCentredString(text_x, y + label_height - 22, f"Tag: {tag_display}")
        
        c.setStrokeColorRGB(0.85, 0.85, 0.85)
        c.setLineWidth(0.5)
        c.rect(x + 2, y + 2, cell_width - 4, cell_height - 4)
        
        c.setFillColorRGB(0, 0, 0)
        
        current_col += 1
        if current_col >= columns:
            current_col = 0
            current_row += 1
            
            if current_row >= rows_per_page:
                c.showPage()
                current_row = 0
    
    c.setFont("Helvetica", 7)
    c.setFillColorRGB(0.5, 0.5, 0.5)
    c.drawString(margin_x, 12, f"Generated: {get_ist_now().strftime('%Y-%m-%d %H:%M')} | {len(devices)} QR codes | Size: 1.5\" x 1.5\"")
    
    c.save()
    buffer.seek(0)
    
    filename_parts = ["QR_Codes"]
    if request.company_id:
        company = await db.companies.find_one({"id": request.company_id}, {"_id": 0, "name": 1})
        if company:
            filename_parts.append(company["name"].replace(" ", "_")[:20])
    if request.site_id:
        site = await db.sites.find_one({"id": request.site_id}, {"_id": 0, "name": 1})
        if site:
            filename_parts.append(site["name"].replace(" ", "_")[:20])
    
    filename_parts.append(get_ist_now().strftime('%Y%m%d'))
    filename = "_".join(filename_parts) + ".pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@router.get("/device/{identifier}/info")
async def get_public_device_info(identifier: str):
    """Get public device information including warranty status and service history."""
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
    
    company = await db.companies.find_one(
        {"id": device["company_id"], "is_deleted": {"$ne": True}}, 
        {"_id": 0, "name": 1, "id": 1}
    )
    
    assigned_user = None
    if device.get("assigned_user_id"):
        user = await db.users.find_one(
            {"id": device["assigned_user_id"], "is_deleted": {"$ne": True}}, 
            {"_id": 0, "name": 1}
        )
        assigned_user = user.get("name") if user else None
    
    site_info = None
    if device.get("site_id"):
        site = await db.sites.find_one(
            {"id": device["site_id"], "is_deleted": {"$ne": True}},
            {"_id": 0, "name": 1, "address": 1}
        )
        if site:
            site_info = {"name": site.get("name"), "address": site.get("address")}
    
    device_warranty_active = is_warranty_active(device.get("warranty_end_date", "")) if device.get("warranty_end_date") else False
    
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
    
    service_history = await db.service_history.find(
        {"device_id": device["id"]},
        {"_id": 0, "service_date": 1, "service_type": 1, "action_taken": 1, "technician_name": 1}
    ).sort("service_date", -1).limit(5).to_list(5)
    
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


@router.post("/device/{identifier}/quick-request")
async def create_quick_service_request(identifier: str, request: QuickServiceRequest):
    """Create a quick service request without login."""
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
    
    company = await db.companies.find_one(
        {"id": device["company_id"], "is_deleted": {"$ne": True}},
        {"_id": 0, "name": 1, "notification_email": 1, "contact_email": 1}
    )
    company_name = company.get("name") if company else "Unknown"
    
    ticket_number = f"QSR-{get_ist_now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
    
    quick_request_data = {
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
    
    await db.quick_service_requests.insert_one(quick_request_data)
    
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
            {"id": quick_request_data["id"]},
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
