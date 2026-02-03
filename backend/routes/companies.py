"""
Companies management endpoints - includes bulk import and portal users
"""
import uuid
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, Query

from database import db
from models.company import Company, CompanyCreate, CompanyUpdate
from models.site import Site
from models.device import Device
from models.supplies import SupplyCategory, SupplyProduct
from services.auth import get_current_admin, get_password_hash, log_audit
from utils.helpers import get_ist_isoformat, is_warranty_active
from utils.security import validate_password_strength

router = APIRouter(tags=["Companies"])


@router.get("/admin/companies")
async def list_companies(
    q: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    page: int = Query(default=1, ge=1),
    admin: dict = Depends(get_current_admin)
):
    """List companies with optional search support - tenant scoped"""
    # Tenant scoping - only show companies for this organization
    organization_id = admin.get("organization_id")
    query = {"is_deleted": {"$ne": True}}
    
    if organization_id:
        query["organization_id"] = organization_id
    
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
    
    for c in companies:
        c["label"] = c["name"]
    
    return companies


@router.post("/admin/companies")
async def create_company(company_data: CompanyCreate, admin: dict = Depends(get_current_admin)):
    company_dict = {k: v for k, v in company_data.model_dump().items() if v is not None}
    company = Company(**company_dict)
    await db.companies.insert_one(company.model_dump())
    await log_audit("company", company.id, "create", {"data": company_data.model_dump()}, admin)
    result = company.model_dump()
    result["label"] = result["name"]
    return result


@router.post("/admin/companies/quick-create")
async def quick_create_company(company_data: CompanyCreate, admin: dict = Depends(get_current_admin)):
    """Quick create company (for inline creation from dropdowns)"""
    existing = await db.companies.find_one(
        {"name": {"$regex": f"^{company_data.name}$", "$options": "i"}, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if existing:
        existing["label"] = existing["name"]
        return existing
    
    company_dict = {k: v for k, v in company_data.model_dump().items() if v is not None}
    company = Company(**company_dict)
    await db.companies.insert_one(company.model_dump())
    await log_audit("company", company.id, "quick_create", {"data": company_data.model_dump()}, admin)
    
    result = company.model_dump()
    result["label"] = result["name"]
    return result


@router.get("/admin/companies/{company_id}")
async def get_company(company_id: str, admin: dict = Depends(get_current_admin)):
    company = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.put("/admin/companies/{company_id}")
async def update_company(company_id: str, updates: CompanyUpdate, admin: dict = Depends(get_current_admin)):
    existing = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Company not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No updates provided")
    
    changes = {k: {"old": existing.get(k), "new": v} for k, v in update_data.items() if existing.get(k) != v}
    
    result = await db.companies.update_one({"id": company_id}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    await log_audit("company", company_id, "update", changes, admin)
    return await db.companies.find_one({"id": company_id}, {"_id": 0})


@router.delete("/admin/companies/{company_id}")
async def delete_company(company_id: str, admin: dict = Depends(get_current_admin)):
    result = await db.companies.update_one({"id": company_id}, {"$set": {"is_deleted": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    await db.users.update_many({"company_id": company_id}, {"$set": {"is_deleted": True}})
    await log_audit("company", company_id, "delete", {"is_deleted": True}, admin)
    return {"message": "Company archived"}


@router.get("/admin/companies/{company_id}/overview")
async def get_company_overview(company_id: str, admin: dict = Depends(get_current_admin)):
    """Get comprehensive company 360° view with all related data"""
    company = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    devices_cursor = db.devices.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    devices = await devices_cursor.to_list(500)
    
    for device in devices:
        device["warranty_active"] = is_warranty_active(device.get("warranty_end_date", ""))
        amc_assignment = await db.amc_device_assignments.find_one({
            "device_id": device["id"],
            "status": "active"
        }, {"_id": 0})
        if amc_assignment and is_warranty_active(amc_assignment.get("coverage_end", "")):
            device["amc_status"] = "active"
            device["amc_coverage_end"] = amc_assignment.get("coverage_end")
        else:
            device["amc_status"] = "none"
    
    sites = await db.sites.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    users = await db.users.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(500)
    
    deployments = await db.deployments.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    for dep in deployments:
        site = await db.sites.find_one({"id": dep.get("site_id")}, {"_id": 0, "name": 1})
        dep["site_name"] = site.get("name") if site else "Unknown"
        dep["items_count"] = len(dep.get("items", []))
    
    licenses = await db.licenses.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    for lic in licenses:
        lic["is_expired"] = not is_warranty_active(lic.get("end_date", ""))
    
    amc_contracts = await db.amc_contracts.find({"company_id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0}).to_list(50)
    for amc in amc_contracts:
        amc["is_active"] = is_warranty_active(amc.get("end_date", ""))
        device_count = await db.amc_device_assignments.count_documents({
            "amc_contract_id": amc["id"],
            "status": "active"
        })
        amc["devices_covered"] = device_count
    
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


# --- Portal Users Management ---

@router.get("/admin/companies/{company_id}/portal-users")
async def list_company_portal_users(company_id: str, admin: dict = Depends(get_current_admin)):
    """List all portal users for a company"""
    company = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    users_cursor = db.company_users.find(
        {"company_id": company_id, "is_deleted": {"$ne": True}},
        {"_id": 0, "password_hash": 0}
    )
    users = await users_cursor.to_list(100)
    return users


@router.post("/admin/companies/{company_id}/portal-users")
async def create_company_portal_user(
    company_id: str,
    user_data: dict,
    admin: dict = Depends(get_current_admin)
):
    """Create a new portal user for a company"""
    company = await db.companies.find_one({"id": company_id, "is_deleted": {"$ne": True}}, {"_id": 0})
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    
    existing = await db.company_users.find_one({"email": user_data.get("email"), "is_deleted": {"$ne": True}})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    if not user_data.get("name") or not user_data.get("email") or not user_data.get("password"):
        raise HTTPException(status_code=400, detail="Name, email, and password are required")
    
    # Validate password strength
    is_valid, error_msg = validate_password_strength(user_data.get("password", ""))
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)
    
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
    
    await db.company_users.insert_one(new_user)
    return {"message": "Portal user created successfully", "id": new_user["id"]}


@router.delete("/admin/companies/{company_id}/portal-users/{user_id}")
async def delete_company_portal_user(
    company_id: str,
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Delete (soft) a portal user"""
    result = await db.company_users.update_one(
        {"id": user_id, "company_id": company_id},
        {"$set": {"is_deleted": True, "deleted_at": get_ist_isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Portal user not found")
    
    return {"message": "Portal user deleted"}


@router.put("/admin/companies/{company_id}/portal-users/{user_id}/reset-password")
async def reset_portal_user_password(
    company_id: str,
    user_id: str,
    data: dict,
    admin: dict = Depends(get_current_admin)
):
    """Reset a portal user's password with strong validation"""
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


# --- Bulk Import Endpoints ---

@router.post("/admin/bulk-import/companies")
async def bulk_import_companies(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import companies from CSV data"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            if not record.get("name"):
                errors.append({"row": idx + 2, "message": "Company name is required"})
                continue
            
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
            
            await db.companies.insert_one(company.model_dump())
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}


@router.post("/admin/bulk-import/sites")
async def bulk_import_sites(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import sites from CSV data"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
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
            
            await db.sites.insert_one(site.model_dump())
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}


@router.post("/admin/bulk-import/devices")
async def bulk_import_devices(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import devices from CSV data"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    companies = await db.companies.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(1000)
    company_by_code = {c.get("code", "").upper(): c["id"] for c in companies if c.get("code")}
    company_by_name = {c["name"].lower(): c["id"] for c in companies}
    
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
            if not record.get("serial_number"):
                errors.append({"row": idx + 2, "message": "Serial number is required"})
                continue
            if not record.get("brand"):
                errors.append({"row": idx + 2, "message": "Brand is required"})
                continue
            if not record.get("model"):
                errors.append({"row": idx + 2, "message": "Model is required"})
                continue
            
            company_id = None
            if record.get("company_code"):
                company_id = company_by_code.get(record["company_code"].upper())
            if not company_id and record.get("company_name"):
                company_id = company_by_name.get(record["company_name"].lower())
            
            if not company_id:
                errors.append({"row": idx + 2, "message": "Company not found"})
                continue
            
            assigned_employee_id = None
            if record.get("employee_code"):
                key = f"{company_id}_{record['employee_code'].upper()}"
                assigned_employee_id = employee_by_code.get(key)
            if not assigned_employee_id and record.get("employee_email"):
                key = f"{company_id}_{record['employee_email'].lower()}"
                assigned_employee_id = employee_by_email.get(key)
            
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
            
            await db.devices.insert_one(device.model_dump())
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}


@router.post("/admin/bulk-import/supply-products")
async def bulk_import_supply_products(data: dict, admin: dict = Depends(get_current_admin)):
    """Bulk import supply products from CSV data"""
    records = data.get("records", [])
    if not records:
        raise HTTPException(status_code=400, detail="No records provided")
    
    categories = await db.supply_categories.find({"is_deleted": {"$ne": True}}, {"_id": 0}).to_list(100)
    category_by_name = {c["name"].lower(): c["id"] for c in categories}
    
    success_count = 0
    errors = []
    
    for idx, record in enumerate(records):
        try:
            if not record.get("name"):
                errors.append({"row": idx + 2, "message": "Product name is required"})
                continue
            
            category_id = None
            if record.get("category"):
                category_id = category_by_name.get(record["category"].lower())
            
            if not category_id:
                if record.get("category"):
                    new_cat = SupplyCategory(name=record["category"])
                    await db.supply_categories.insert_one(new_cat.model_dump())
                    category_id = new_cat.id
                    category_by_name[record["category"].lower()] = category_id
                else:
                    errors.append({"row": idx + 2, "message": "Category is required"})
                    continue
            
            product = SupplyProduct(
                category_id=category_id,
                name=record.get("name"),
                description=record.get("description"),
                unit=record.get("unit", "piece"),
                internal_notes=record.get("internal_notes")
            )
            
            await db.supply_products.insert_one(product.model_dump())
            success_count += 1
            
        except Exception as e:
            errors.append({"row": idx + 2, "message": str(e)})
    
    return {"success": success_count, "errors": errors}
