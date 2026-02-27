"""
AMC Request endpoints - Self-service AMC requests from company portal
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query

from database import db
from models.amc import (
    AMCPackage, AMCPackageCreate, AMCCompanyPricing,
    AMCRequest, AMCRequestCreate, AMCRequestUpdate, AMCRequestAdminUpdate,
    AMCContract, AMCContractCreate, InAppNotification
)
from services.auth import get_current_admin, get_current_company_user
from utils.helpers import get_ist_isoformat, calculate_warranty_expiry

router = APIRouter(tags=["AMC Requests"])


# ==================== AMC PACKAGES (Admin) ====================

@router.get("/admin/amc-packages")
async def list_amc_packages(
    include_inactive: bool = False,
    admin: dict = Depends(get_current_admin)
):
    """List all AMC packages"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    query = {"is_deleted": {"$ne": True}, "organization_id": org_id}
    if not include_inactive:
        query["is_active"] = True
    
    packages = await db.amc_packages.find(query, {"_id": 0}).to_list(100)
    return packages


@router.post("/admin/amc-packages")
async def create_amc_package(
    package: AMCPackageCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new AMC package"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    package_data = package.model_dump()
    if package_data.get("coverage_includes") is None:
        package_data["coverage_includes"] = {}
    if package_data.get("exclusions") is None:
        package_data["exclusions"] = {}
    if package_data.get("entitlements") is None:
        package_data["entitlements"] = {}
    
    new_package = AMCPackage(**package_data)
    pkg_dict = new_package.model_dump()
    pkg_dict["organization_id"] = org_id
    await db.amc_packages.insert_one(pkg_dict)
    del pkg_dict["_id"]
    return pkg_dict


@router.put("/admin/amc-packages/{package_id}")
async def update_amc_package(
    package_id: str,
    updates: dict,
    admin: dict = Depends(get_current_admin)
):
    """Update an AMC package"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    existing = await db.amc_packages.find_one({"id": package_id, "organization_id": org_id, "is_deleted": {"$ne": True}})
    if not existing:
        raise HTTPException(status_code=404, detail="Package not found")
    
    updates["updated_at"] = get_ist_isoformat()
    await db.amc_packages.update_one({"id": package_id, "organization_id": org_id}, {"$set": updates})
    return await db.amc_packages.find_one({"id": package_id, "organization_id": org_id}, {"_id": 0})


@router.delete("/admin/amc-packages/{package_id}")
async def delete_amc_package(package_id: str, admin: dict = Depends(get_current_admin)):
    """Delete (soft) an AMC package"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    result = await db.amc_packages.update_one(
        {"id": package_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Package not found")
    return {"message": "Package deleted"}


# ==================== COMPANY PRICING (Admin) ====================

@router.get("/admin/amc-company-pricing")
async def list_company_pricing(
    company_id: Optional[str] = None,
    admin: dict = Depends(get_current_admin)
):
    """List company-specific pricing"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    query = {"is_active": True, "organization_id": org_id}
    if company_id:
        query["company_id"] = company_id
    
    pricing = await db.amc_company_pricing.find(query, {"_id": 0}).to_list(500)
    return pricing


@router.post("/admin/amc-company-pricing")
async def set_company_pricing(
    pricing_data: dict,
    admin: dict = Depends(get_current_admin)
):
    """Set custom pricing for a company"""
    # Check if pricing already exists for this company+package
    existing = await db.amc_company_pricing.find_one({
        "company_id": pricing_data["company_id"],
        "package_id": pricing_data["package_id"],
        "is_active": True
    })
    
    if existing:
        # Update existing
        await db.amc_company_pricing.update_one(
            {"id": existing["id"]},
            {"$set": {
                "custom_price_per_device": pricing_data.get("custom_price_per_device", existing["custom_price_per_device"]),
                "discount_percentage": pricing_data.get("discount_percentage", 0),
                "notes": pricing_data.get("notes"),
                "updated_at": get_ist_isoformat()
            }}
        )
        return await db.amc_company_pricing.find_one({"id": existing["id"]}, {"_id": 0})
    else:
        # Create new
        new_pricing = AMCCompanyPricing(
            company_id=pricing_data["company_id"],
            package_id=pricing_data["package_id"],
            custom_price_per_device=pricing_data.get("custom_price_per_device", 0),
            discount_percentage=pricing_data.get("discount_percentage", 0),
            notes=pricing_data.get("notes")
        )
        await db.amc_company_pricing.insert_one(new_pricing.model_dump())
        return new_pricing.model_dump()


# ==================== AMC REQUESTS (Admin) ====================

@router.get("/admin/amc-requests")
async def list_amc_requests(
    status: Optional[str] = None,
    company_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    admin: dict = Depends(get_current_admin)
):
    """List all AMC requests with filters"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    query = {"organization_id": org_id}
    if status:
        query["status"] = status
    if company_id:
        query["company_id"] = company_id
    
    requests = await db.amc_requests.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    
    # Enrich with company info
    for req in requests:
        company = await db.companies.find_one({"id": req["company_id"]}, {"_id": 0, "name": 1})
        req["company_name"] = company.get("name") if company else "Unknown"
        
        # Get device count if specific devices selected
        if req.get("selected_device_ids"):
            req["device_count"] = len(req["selected_device_ids"])
    
    return requests


@router.get("/admin/amc-requests/{request_id}")
async def get_amc_request_admin(
    request_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get AMC request details with full device info"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    amc_request = await db.amc_requests.find_one({"id": request_id, "organization_id": org_id}, {"_id": 0})
    if not amc_request:
        raise HTTPException(status_code=404, detail="AMC Request not found")
    
    # Get company info
    company = await db.companies.find_one({"id": amc_request["company_id"]}, {"_id": 0})
    amc_request["company"] = company
    
    # Get selected devices
    if amc_request.get("selected_device_ids"):
        devices = await db.devices.find(
            {"id": {"$in": amc_request["selected_device_ids"]}, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(500)
        amc_request["selected_devices"] = devices
    
    # Get package info
    if amc_request.get("package_id"):
        package = await db.amc_packages.find_one({"id": amc_request["package_id"]}, {"_id": 0})
        amc_request["package"] = package
    
    return amc_request


@router.put("/admin/amc-requests/{request_id}")
async def update_amc_request_admin(
    request_id: str,
    updates: AMCRequestAdminUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Admin update AMC request (approve, reject, set pricing, etc.)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    amc_request = await db.amc_requests.find_one({"id": request_id, "organization_id": org_id}, {"_id": 0})
    if not amc_request:
        raise HTTPException(status_code=404, detail="AMC Request not found")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    # Track review
    if updates.status and updates.status != amc_request.get("status"):
        update_data["reviewed_by"] = admin.get("id")
        update_data["reviewed_at"] = get_ist_isoformat()
        
        # Create notification for company user
        notification_title = ""
        notification_message = ""
        notification_type = "info"
        
        if updates.status == "approved":
            notification_title = "AMC Request Approved"
            notification_message = f"Your AMC request has been approved. Total: ₹{updates.total_price or amc_request.get('total_price', 0):,.0f}"
            notification_type = "success"
        elif updates.status == "rejected":
            notification_title = "AMC Request Rejected"
            notification_message = f"Your AMC request has been rejected. Reason: {updates.rejection_reason or 'Not specified'}"
            notification_type = "error"
        elif updates.status == "changes_requested":
            notification_title = "AMC Request - Changes Needed"
            notification_message = f"Your AMC request needs revision: {updates.changes_requested_note or 'Please review'}"
            notification_type = "warning"
        elif updates.status == "under_review":
            notification_title = "AMC Request Under Review"
            notification_message = "Your AMC request is now being reviewed by our team."
            notification_type = "info"
        
        if notification_title:
            notification = InAppNotification(
                user_id=amc_request["requested_by_user_id"],
                user_type="company_user",
                title=notification_title,
                message=notification_message,
                notification_type=notification_type,
                related_entity_type="amc_request",
                related_entity_id=request_id,
                link=f"/company/amc-requests/{request_id}"
            )
            await db.notifications.insert_one(notification.model_dump())
    
    await db.amc_requests.update_one({"id": request_id, "organization_id": org_id}, {"$set": update_data})
    return await db.amc_requests.find_one({"id": request_id, "organization_id": org_id}, {"_id": 0})


@router.post("/admin/amc-requests/{request_id}/approve")
async def approve_amc_request(
    request_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Approve AMC request and create AMC contract"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    amc_request = await db.amc_requests.find_one({"id": request_id, "organization_id": org_id}, {"_id": 0})
    if not amc_request:
        raise HTTPException(status_code=404, detail="AMC Request not found")
    
    if amc_request.get("status") == "approved":
        raise HTTPException(status_code=400, detail="Request already approved")
    
    # Calculate end date based on duration
    from dateutil.relativedelta import relativedelta
    from datetime import datetime
    
    start_date = datetime.strptime(amc_request["preferred_start_date"], "%Y-%m-%d")
    end_date = start_date + relativedelta(months=amc_request.get("duration_months", 12)) - relativedelta(days=1)
    
    # Create AMC Contract
    contract = AMCContract(
        company_id=amc_request["company_id"],
        name=f"AMC - {amc_request.get('amc_type', 'Comprehensive').title()} ({amc_request.get('duration_months', 12)} months)",
        amc_type=amc_request.get("amc_type", "comprehensive"),
        start_date=amc_request["preferred_start_date"],
        end_date=end_date.strftime("%Y-%m-%d"),
        internal_notes=f"Created from AMC Request #{request_id[:8]}. Price: ₹{amc_request.get('total_price', 0):,.0f}"
    )
    
    await db.amc_contracts.insert_one(contract.model_dump())
    
    # Update request status
    await db.amc_requests.update_one(
        {"id": request_id},
        {"$set": {
            "status": "approved",
            "approved_contract_id": contract.id,
            "reviewed_by": admin.get("id"),
            "reviewed_at": get_ist_isoformat(),
            "updated_at": get_ist_isoformat()
        }}
    )
    
    # Create notification
    notification = InAppNotification(
        user_id=amc_request["requested_by_user_id"],
        user_type="company_user",
        title="AMC Request Approved! 🎉",
        message=f"Your AMC request has been approved. Contract period: {amc_request['preferred_start_date']} to {end_date.strftime('%Y-%m-%d')}",
        notification_type="success",
        related_entity_type="amc_request",
        related_entity_id=request_id,
        link=f"/company/amc-requests/{request_id}"
    )
    await db.notifications.insert_one(notification.model_dump())
    
    return {
        "message": "AMC Request approved and contract created",
        "contract_id": contract.id,
        "request": await db.amc_requests.find_one({"id": request_id}, {"_id": 0})
    }


# ==================== COMPANY PORTAL ENDPOINTS ====================

@router.get("/company/amc-packages")
async def get_available_packages(user: dict = Depends(get_current_company_user)):
    """Get available AMC packages for company portal (with company-specific pricing)"""
    company_id = user["company_id"]
    
    # Get all active packages
    packages = await db.amc_packages.find(
        {"is_active": True, "is_deleted": {"$ne": True}},
        {"_id": 0}
    ).to_list(50)
    
    # Get company-specific pricing
    company_pricing = await db.amc_company_pricing.find(
        {"company_id": company_id, "is_active": True},
        {"_id": 0}
    ).to_list(50)
    
    pricing_map = {p["package_id"]: p for p in company_pricing}
    
    # Apply company pricing to packages
    for package in packages:
        if package["id"] in pricing_map:
            custom = pricing_map[package["id"]]
            package["price_per_device"] = custom["custom_price_per_device"]
            package["discount_percentage"] = custom.get("discount_percentage", 0)
            package["has_custom_pricing"] = True
        else:
            package["price_per_device"] = package.get("base_price_per_device", 0)
            package["has_custom_pricing"] = False
    
    return packages


@router.get("/company/amc-requests")
async def get_my_amc_requests(user: dict = Depends(get_current_company_user)):
    """Get company's AMC requests"""
    company_id = user["company_id"]
    
    requests = await db.amc_requests.find(
        {"company_id": company_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    # Enrich with package info
    for req in requests:
        if req.get("package_id"):
            package = await db.amc_packages.find_one({"id": req["package_id"]}, {"_id": 0, "name": 1})
            req["package_name"] = package.get("name") if package else None
    
    return requests


@router.get("/company/amc-requests/{request_id}")
async def get_my_amc_request(request_id: str, user: dict = Depends(get_current_company_user)):
    """Get specific AMC request details"""
    company_id = user["company_id"]
    
    amc_request = await db.amc_requests.find_one(
        {"id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not amc_request:
        raise HTTPException(status_code=404, detail="AMC Request not found")
    
    # Get selected devices
    if amc_request.get("selected_device_ids"):
        devices = await db.devices.find(
            {"id": {"$in": amc_request["selected_device_ids"]}, "is_deleted": {"$ne": True}},
            {"_id": 0, "id": 1, "brand": 1, "model": 1, "serial_number": 1, "device_type": 1}
        ).to_list(500)
        amc_request["selected_devices"] = devices
    
    # Get package info
    if amc_request.get("package_id"):
        package = await db.amc_packages.find_one({"id": amc_request["package_id"]}, {"_id": 0})
        amc_request["package"] = package
    
    return amc_request


@router.post("/company/amc-requests")
async def create_amc_request(
    request_data: AMCRequestCreate,
    user: dict = Depends(get_current_company_user)
):
    """Create new AMC request from company portal"""
    company_id = user["company_id"]
    
    # Validate device selection
    device_count = 0
    if request_data.selection_type == "specific":
        if not request_data.selected_device_ids:
            raise HTTPException(status_code=400, detail="Please select at least one device")
        # Verify devices belong to this company
        devices = await db.devices.find({
            "id": {"$in": request_data.selected_device_ids},
            "company_id": company_id,
            "is_deleted": {"$ne": True}
        }).to_list(500)
        device_count = len(devices)
        if device_count == 0:
            raise HTTPException(status_code=400, detail="No valid devices selected")
    elif request_data.selection_type == "all":
        device_count = await db.devices.count_documents({
            "company_id": company_id,
            "is_deleted": {"$ne": True}
        })
    elif request_data.selection_type == "by_category":
        if not request_data.selected_categories:
            raise HTTPException(status_code=400, detail="Please select at least one category")
        device_count = await db.devices.count_documents({
            "company_id": company_id,
            "device_type": {"$in": request_data.selected_categories},
            "is_deleted": {"$ne": True}
        })
    
    # Create AMC Request
    amc_request = AMCRequest(
        company_id=company_id,
        requested_by_user_id=user["id"],
        requested_by_name=user.get("name", "Unknown"),
        package_id=request_data.package_id,
        amc_type=request_data.amc_type,
        duration_months=request_data.duration_months,
        selection_type=request_data.selection_type,
        selected_device_ids=request_data.selected_device_ids,
        selected_categories=request_data.selected_categories,
        device_count=device_count,
        preferred_start_date=request_data.preferred_start_date,
        special_requirements=request_data.special_requirements,
        budget_range=request_data.budget_range
    )
    
    await db.amc_requests.insert_one(amc_request.model_dump())
    
    # Create notification for admins
    admins = await db.admins.find({}, {"_id": 0, "id": 1}).to_list(10)
    company = await db.companies.find_one({"id": company_id}, {"_id": 0, "name": 1})
    
    for admin in admins:
        notification = InAppNotification(
            user_id=admin["id"],
            user_type="admin",
            title="New AMC Request",
            message=f"{company.get('name', 'A company')} has submitted an AMC request for {device_count} devices.",
            notification_type="info",
            related_entity_type="amc_request",
            related_entity_id=amc_request.id,
            link=f"/admin/amc-requests/{amc_request.id}"
        )
        await db.notifications.insert_one(notification.model_dump())
    
    return amc_request.model_dump()


@router.put("/company/amc-requests/{request_id}")
async def update_my_amc_request(
    request_id: str,
    updates: AMCRequestUpdate,
    user: dict = Depends(get_current_company_user)
):
    """Update AMC request (only if status allows)"""
    company_id = user["company_id"]
    
    amc_request = await db.amc_requests.find_one(
        {"id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not amc_request:
        raise HTTPException(status_code=404, detail="AMC Request not found")
    
    # Only allow updates if pending or changes requested
    if amc_request.get("status") not in ["pending_review", "changes_requested"]:
        raise HTTPException(status_code=400, detail="Cannot modify request in current status")
    
    update_data = {k: v for k, v in updates.model_dump().items() if v is not None}
    update_data["updated_at"] = get_ist_isoformat()
    
    # Reset to pending if it was changes_requested
    if amc_request.get("status") == "changes_requested":
        update_data["status"] = "pending_review"
    
    await db.amc_requests.update_one({"id": request_id}, {"$set": update_data})
    return await db.amc_requests.find_one({"id": request_id}, {"_id": 0})


@router.delete("/company/amc-requests/{request_id}")
async def cancel_my_amc_request(request_id: str, user: dict = Depends(get_current_company_user)):
    """Cancel AMC request"""
    company_id = user["company_id"]
    
    amc_request = await db.amc_requests.find_one(
        {"id": request_id, "company_id": company_id},
        {"_id": 0}
    )
    
    if not amc_request:
        raise HTTPException(status_code=404, detail="AMC Request not found")
    
    if amc_request.get("status") in ["approved"]:
        raise HTTPException(status_code=400, detail="Cannot cancel approved request")
    
    await db.amc_requests.update_one(
        {"id": request_id},
        {"$set": {"status": "cancelled", "updated_at": get_ist_isoformat()}}
    )
    
    return {"message": "AMC Request cancelled"}


# ==================== NOTIFICATIONS ====================

@router.get("/company/notifications")
async def get_company_notifications(
    unread_only: bool = False,
    limit: int = Query(default=20, le=100),
    user: dict = Depends(get_current_company_user)
):
    """Get notifications for company user"""
    query = {"user_id": user["id"], "user_type": "company_user"}
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    unread_count = await db.notifications.count_documents({"user_id": user["id"], "user_type": "company_user", "is_read": False})
    
    return {"notifications": notifications, "unread_count": unread_count}


@router.put("/company/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str, user: dict = Depends(get_current_company_user)):
    """Mark notification as read"""
    await db.notifications.update_one(
        {"id": notification_id, "user_id": user["id"]},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}


@router.put("/company/notifications/read-all")
async def mark_all_notifications_read(user: dict = Depends(get_current_company_user)):
    """Mark all notifications as read"""
    await db.notifications.update_many(
        {"user_id": user["id"], "user_type": "company_user"},
        {"$set": {"is_read": True}}
    )
    return {"message": "All notifications marked as read"}


@router.get("/admin/notifications")
async def get_admin_notifications(
    unread_only: bool = False,
    limit: int = Query(default=20, le=100),
    admin: dict = Depends(get_current_admin)
):
    """Get notifications for admin"""
    query = {"user_id": admin["id"], "user_type": "admin"}
    if unread_only:
        query["is_read"] = False
    
    notifications = await db.notifications.find(query, {"_id": 0}).sort("created_at", -1).to_list(limit)
    unread_count = await db.notifications.count_documents({"user_id": admin["id"], "user_type": "admin", "is_read": False})
    
    return {"notifications": notifications, "unread_count": unread_count}


@router.put("/admin/notifications/{notification_id}/read")
async def mark_admin_notification_read(notification_id: str, admin: dict = Depends(get_current_admin)):
    """Mark admin notification as read"""
    await db.notifications.update_one(
        {"id": notification_id, "user_id": admin["id"]},
        {"$set": {"is_read": True}}
    )
    return {"message": "Marked as read"}
