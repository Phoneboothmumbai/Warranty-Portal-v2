"""
Staff Module API Routes
=======================
Endpoints for managing:
- Staff Users (CRUD + FSM state transitions)
- Departments
- Roles
- Permissions
- Audit Logs
"""
import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query, Request
from services.auth import get_current_admin
from services.staff_service import StaffService, PermissionDeniedError, StateTransitionError
from models.staff import (
    StaffUserCreate, StaffUserUpdate, StaffUserStateTransition, SensitiveDataUpdate,
    DepartmentCreate, DepartmentUpdate,
    RoleCreate, RoleUpdate, RolePermissionAssignment,
    PermissionCreate, PermissionUpdate,
    StaffUser, Department, Role, Permission, UserState
)
from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/admin/staff", tags=["Staff Module"])


# ==================== USERS ====================

@router.get("/users")
async def list_users(
    admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    state: Optional[str] = None,
    user_type: Optional[str] = None,
    department_id: Optional[str] = None,
    role_id: Optional[str] = None,
    search: Optional[str] = None
):
    """List staff users with filtering"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Build query
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    
    if state:
        query["state"] = state
    if user_type:
        query["user_type"] = user_type
    if department_id:
        query["department_ids"] = department_id
    if role_id:
        query["role_ids"] = role_id
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"email": {"$regex": search, "$options": "i"}},
            {"employee_id": {"$regex": search, "$options": "i"}}
        ]
    
    # Get total count
    total = await db.staff_users.count_documents(query)
    
    # Get paginated results
    skip = (page - 1) * limit
    users = await db.staff_users.find(
        query,
        {"_id": 0, "password_hash": 0, "invite_token": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
    
    # Enrich with role and department names
    for user in users:
        role_ids = user.get("role_ids", [])
        if role_ids:
            roles = await db.staff_roles.find(
                {"id": {"$in": role_ids}},
                {"_id": 0, "id": 1, "name": 1}
            ).to_list(None)
            user["roles"] = roles
        
        dept_ids = user.get("department_ids", [])
        if dept_ids:
            depts = await db.staff_departments.find(
                {"id": {"$in": dept_ids}},
                {"_id": 0, "id": 1, "name": 1}
            ).to_list(None)
            user["departments"] = depts
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


@router.post("/users")
async def create_user(
    user_data: StaffUserCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new staff user"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    try:
        user = await StaffService.create_user(
            organization_id=org_id,
            user_data=user_data.model_dump(),
            performed_by=admin
        )
        return {"success": True, "user": user}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}")
async def get_user(
    user_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get user details with roles and permissions"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    user = await StaffService.get_user_with_permissions(user_id, org_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.put("/users/{user_id}")
async def update_user(
    user_id: str,
    update_data: StaffUserUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update user details"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Get existing user
    existing = await db.staff_users.find_one(
        {"id": user_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Build update
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    # Track changes for audit
    changes = {}
    for key, new_val in update_dict.items():
        if key != "updated_at" and existing.get(key) != new_val:
            changes[key] = {"before": existing.get(key), "after": new_val}
    
    await db.staff_users.update_one(
        {"id": user_id},
        {"$set": update_dict}
    )
    
    # Audit log
    if changes:
        await StaffService.log_audit(
            organization_id=org_id,
            entity_type="user",
            entity_id=user_id,
            entity_name=existing.get("name"),
            action="update",
            changes=changes,
            performed_by=admin
        )
    
    # Return updated user
    user = await db.staff_users.find_one(
        {"id": user_id},
        {"_id": 0, "password_hash": 0}
    )
    return {"success": True, "user": user}


@router.post("/users/{user_id}/state")
async def change_user_state(
    user_id: str,
    transition: StaffUserStateTransition,
    admin: dict = Depends(get_current_admin)
):
    """Change user state (activate, suspend, archive)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    try:
        user = await StaffService.transition_user_state(
            user_id=user_id,
            organization_id=org_id,
            new_state=transition.new_state,
            reason=transition.reason,
            performed_by=admin
        )
        return {"success": True, "user": user}
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/users/{user_id}")
async def archive_user(
    user_id: str,
    reason: str = Query(..., min_length=1),
    admin: dict = Depends(get_current_admin)
):
    """Archive a user (soft delete)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    try:
        # Transition to archived state
        user = await StaffService.transition_user_state(
            user_id=user_id,
            organization_id=org_id,
            new_state=UserState.ARCHIVED.value,
            reason=reason,
            performed_by=admin
        )
        
        # Also mark as deleted
        await db.staff_users.update_one(
            {"id": user_id},
            {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
        )
        
        return {"success": True, "message": "User archived successfully"}
    except StateTransitionError as e:
        raise HTTPException(status_code=400, detail=e.message)


# ==================== DEPARTMENTS ====================

@router.get("/departments")
async def list_departments(
    admin: dict = Depends(get_current_admin),
    include_inactive: bool = False
):
    """List all departments"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    if not include_inactive:
        query["is_active"] = True
    
    departments = await db.staff_departments.find(
        query,
        {"_id": 0}
    ).sort("name", 1).to_list(None)
    
    # Add user count for each department
    for dept in departments:
        count = await db.staff_users.count_documents({
            "organization_id": org_id,
            "department_ids": dept["id"],
            "is_deleted": {"$ne": True}
        })
        dept["user_count"] = count
    
    return {"departments": departments}


@router.post("/departments")
async def create_department(
    dept_data: DepartmentCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new department"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check for duplicate name
    existing = await db.staff_departments.find_one({
        "organization_id": org_id,
        "name": dept_data.name,
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Department with this name already exists")
    
    dept = Department(
        organization_id=org_id,
        name=dept_data.name,
        code=dept_data.code,
        description=dept_data.description,
        parent_id=dept_data.parent_id,
        manager_id=dept_data.manager_id,
        created_by=admin.get("id")
    )
    
    await db.staff_departments.insert_one(dept.model_dump())
    
    # Audit log
    await StaffService.log_audit(
        organization_id=org_id,
        entity_type="department",
        entity_id=dept.id,
        entity_name=dept.name,
        action="create",
        changes={"created": True},
        performed_by=admin
    )
    
    return {"success": True, "department": dept.model_dump()}


@router.put("/departments/{dept_id}")
async def update_department(
    dept_id: str,
    update_data: DepartmentUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update department"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.staff_departments.find_one(
        {"id": dept_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Department not found")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    # Track changes
    changes = {}
    for key, new_val in update_dict.items():
        if key != "updated_at" and existing.get(key) != new_val:
            changes[key] = {"before": existing.get(key), "after": new_val}
    
    await db.staff_departments.update_one(
        {"id": dept_id},
        {"$set": update_dict}
    )
    
    if changes:
        await StaffService.log_audit(
            organization_id=org_id,
            entity_type="department",
            entity_id=dept_id,
            entity_name=existing.get("name"),
            action="update",
            changes=changes,
            performed_by=admin
        )
    
    dept = await db.staff_departments.find_one({"id": dept_id}, {"_id": 0})
    return {"success": True, "department": dept}


@router.delete("/departments/{dept_id}")
async def delete_department(
    dept_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Delete department (only if no users)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check for users in department
    user_count = await db.staff_users.count_documents({
        "organization_id": org_id,
        "department_ids": dept_id,
        "is_deleted": {"$ne": True}
    })
    
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete department with {user_count} user(s). Reassign users first."
        )
    
    # Soft delete
    await db.staff_departments.update_one(
        {"id": dept_id, "organization_id": org_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    await StaffService.log_audit(
        organization_id=org_id,
        entity_type="department",
        entity_id=dept_id,
        action="delete",
        changes={"deleted": True},
        performed_by=admin
    )
    
    return {"success": True, "message": "Department deleted"}


# ==================== ROLES ====================

@router.get("/roles")
async def list_roles(
    admin: dict = Depends(get_current_admin),
    include_system: bool = True
):
    """List all roles"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    if not include_system:
        query["is_system"] = {"$ne": True}
    
    roles = await db.staff_roles.find(
        query,
        {"_id": 0}
    ).sort("level", 1).to_list(None)
    
    # Add user count for each role
    for role in roles:
        count = await db.staff_users.count_documents({
            "organization_id": org_id,
            "role_ids": role["id"],
            "is_deleted": {"$ne": True}
        })
        role["user_count"] = count
    
    return {"roles": roles}


@router.post("/roles")
async def create_role(
    role_data: RoleCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a new role (starts with zero permissions)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check for duplicate name
    existing = await db.staff_roles.find_one({
        "organization_id": org_id,
        "name": role_data.name,
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Role with this name already exists")
    
    role = Role(
        organization_id=org_id,
        name=role_data.name,
        description=role_data.description,
        level=role_data.level,
        is_default=role_data.is_default,
        permissions=[],  # Starts with zero permissions
        created_by=admin.get("id")
    )
    
    await db.staff_roles.insert_one(role.model_dump())
    
    await StaffService.log_audit(
        organization_id=org_id,
        entity_type="role",
        entity_id=role.id,
        entity_name=role.name,
        action="create",
        changes={"created": True, "level": role.level},
        performed_by=admin
    )
    
    return {"success": True, "role": role.model_dump()}


@router.get("/roles/{role_id}")
async def get_role(
    role_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Get role with permissions"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    role = await db.staff_roles.find_one(
        {"id": role_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    return role


@router.put("/roles/{role_id}")
async def update_role(
    role_id: str,
    update_data: RoleUpdate,
    admin: dict = Depends(get_current_admin)
):
    """Update role details"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    existing = await db.staff_roles.find_one(
        {"id": role_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not existing:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if existing.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot modify system roles")
    
    update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
    if not update_dict:
        raise HTTPException(status_code=400, detail="No fields to update")
    
    update_dict["updated_at"] = get_ist_isoformat()
    
    changes = {}
    for key, new_val in update_dict.items():
        if key != "updated_at" and existing.get(key) != new_val:
            changes[key] = {"before": existing.get(key), "after": new_val}
    
    await db.staff_roles.update_one(
        {"id": role_id},
        {"$set": update_dict}
    )
    
    if changes:
        await StaffService.log_audit(
            organization_id=org_id,
            entity_type="role",
            entity_id=role_id,
            entity_name=existing.get("name"),
            action="update",
            changes=changes,
            performed_by=admin
        )
    
    role = await db.staff_roles.find_one({"id": role_id}, {"_id": 0})
    return {"success": True, "role": role}


@router.post("/roles/{role_id}/permissions")
async def assign_role_permissions(
    role_id: str,
    assignment: RolePermissionAssignment,
    admin: dict = Depends(get_current_admin)
):
    """Assign permissions to a role"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    role = await db.staff_roles.find_one(
        {"id": role_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    # Get permissions to add
    permissions = await db.staff_permissions.find(
        {"id": {"$in": assignment.permission_ids}, "organization_id": org_id},
        {"_id": 0}
    ).to_list(None)
    
    if not permissions:
        raise HTTPException(status_code=400, detail="No valid permissions found")
    
    # Build new permission entries
    before_perms = role.get("permissions", [])
    existing_codes = {p.get("permission_code") for p in before_perms}
    
    new_perms = list(before_perms)
    added = []
    for perm in permissions:
        code = f"{perm['module']}.{perm['resource']}.{perm['action']}"
        if code not in existing_codes:
            new_perms.append({
                "permission_id": perm["id"],
                "permission_code": code,
                "visibility_scope": assignment.visibility_scope,
                "valid_from": assignment.valid_from,
                "valid_until": assignment.valid_until
            })
            added.append(code)
    
    await db.staff_roles.update_one(
        {"id": role_id},
        {"$set": {"permissions": new_perms, "updated_at": get_ist_isoformat()}}
    )
    
    await StaffService.log_audit(
        organization_id=org_id,
        entity_type="role",
        entity_id=role_id,
        entity_name=role.get("name"),
        action="permissions_added",
        changes={
            "permissions_added": added,
            "before_count": len(before_perms),
            "after_count": len(new_perms)
        },
        performed_by=admin
    )
    
    role = await db.staff_roles.find_one({"id": role_id}, {"_id": 0})
    return {"success": True, "role": role, "added": added}


@router.delete("/roles/{role_id}/permissions")
async def remove_role_permissions(
    role_id: str,
    permission_ids: List[str] = Query(...),
    admin: dict = Depends(get_current_admin)
):
    """Remove permissions from a role"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    role = await db.staff_roles.find_one(
        {"id": role_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    before_perms = role.get("permissions", [])
    new_perms = [p for p in before_perms if p.get("permission_id") not in permission_ids]
    removed = [p.get("permission_code") for p in before_perms if p.get("permission_id") in permission_ids]
    
    await db.staff_roles.update_one(
        {"id": role_id},
        {"$set": {"permissions": new_perms, "updated_at": get_ist_isoformat()}}
    )
    
    await StaffService.log_audit(
        organization_id=org_id,
        entity_type="role",
        entity_id=role_id,
        entity_name=role.get("name"),
        action="permissions_removed",
        changes={
            "permissions_removed": removed,
            "before_count": len(before_perms),
            "after_count": len(new_perms)
        },
        performed_by=admin
    )
    
    role = await db.staff_roles.find_one({"id": role_id}, {"_id": 0})
    return {"success": True, "role": role, "removed": removed}


@router.delete("/roles/{role_id}")
async def delete_role(
    role_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Delete role (only if no active users)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    role = await db.staff_roles.find_one(
        {"id": role_id, "organization_id": org_id, "is_deleted": {"$ne": True}},
        {"_id": 0}
    )
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
    
    if role.get("is_system"):
        raise HTTPException(status_code=400, detail="Cannot delete system roles")
    
    # Check for users with this role
    user_count = await db.staff_users.count_documents({
        "organization_id": org_id,
        "role_ids": role_id,
        "state": {"$ne": UserState.ARCHIVED.value},
        "is_deleted": {"$ne": True}
    })
    
    if user_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete role with {user_count} active user(s). Reassign users first."
        )
    
    await db.staff_roles.update_one(
        {"id": role_id},
        {"$set": {"is_deleted": True, "updated_at": get_ist_isoformat()}}
    )
    
    await StaffService.log_audit(
        organization_id=org_id,
        entity_type="role",
        entity_id=role_id,
        entity_name=role.get("name"),
        action="delete",
        changes={"deleted": True},
        performed_by=admin
    )
    
    return {"success": True, "message": "Role deleted"}


# ==================== PERMISSIONS ====================

@router.get("/permissions")
async def list_permissions(
    admin: dict = Depends(get_current_admin),
    module: Optional[str] = None,
    category: Optional[str] = None
):
    """List all permissions"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id, "is_deleted": {"$ne": True}}
    if module:
        query["module"] = module
    if category:
        query["category"] = category
    
    permissions = await db.staff_permissions.find(
        query,
        {"_id": 0}
    ).sort([("category", 1), ("module", 1), ("resource", 1)]).to_list(None)
    
    # Auto-initialize if no permissions exist
    if not permissions and not module and not category:
        logger.info(f"No permissions found for org {org_id}, auto-initializing...")
        await StaffService.initialize_organization_staff(org_id, admin)
        permissions = await db.staff_permissions.find(
            {"organization_id": org_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).sort([("category", 1), ("module", 1), ("resource", 1)]).to_list(None)
    
    # Group by category
    grouped = {}
    for perm in permissions:
        cat = perm.get("category", "Other")
        if cat not in grouped:
            grouped[cat] = []
        grouped[cat].append(perm)
    
    return {"permissions": permissions, "grouped": grouped}


@router.post("/permissions")
async def create_permission(
    perm_data: PermissionCreate,
    admin: dict = Depends(get_current_admin)
):
    """Create a custom permission"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    # Check for duplicate
    existing = await db.staff_permissions.find_one({
        "organization_id": org_id,
        "module": perm_data.module,
        "resource": perm_data.resource,
        "action": perm_data.action,
        "is_deleted": {"$ne": True}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Permission already exists")
    
    perm = Permission(
        organization_id=org_id,
        module=perm_data.module,
        resource=perm_data.resource,
        action=perm_data.action,
        name=perm_data.name,
        description=perm_data.description,
        category=perm_data.category,
        is_system=False
    )
    
    await db.staff_permissions.insert_one(perm.model_dump())
    
    await StaffService.log_audit(
        organization_id=org_id,
        entity_type="permission",
        entity_id=perm.id,
        entity_name=perm.name,
        action="create",
        changes={"code": f"{perm.module}.{perm.resource}.{perm.action}"},
        performed_by=admin
    )
    
    return {"success": True, "permission": perm.model_dump()}


# ==================== AUDIT LOGS ====================

@router.get("/audit-logs")
async def list_audit_logs(
    admin: dict = Depends(get_current_admin),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=200),
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    performed_by_id: Optional[str] = None,
    severity: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None
):
    """List audit logs (read-only)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    query = {"organization_id": org_id}
    
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if action:
        query["action"] = action
    if performed_by_id:
        query["performed_by_id"] = performed_by_id
    if severity:
        query["severity"] = severity
    if from_date:
        query["timestamp"] = {"$gte": from_date}
    if to_date:
        if "timestamp" in query:
            query["timestamp"]["$lte"] = to_date
        else:
            query["timestamp"] = {"$lte": to_date}
    
    total = await db.staff_audit_logs.count_documents(query)
    skip = (page - 1) * limit
    
    logs = await db.staff_audit_logs.find(
        query,
        {"_id": 0}
    ).sort("timestamp", -1).skip(skip).limit(limit).to_list(None)
    
    return {
        "logs": logs,
        "total": total,
        "page": page,
        "limit": limit,
        "pages": (total + limit - 1) // limit
    }


# ==================== INITIALIZATION ====================

@router.post("/initialize")
async def initialize_staff_module(
    admin: dict = Depends(get_current_admin)
):
    """Initialize staff module for the organization (creates default permissions & roles)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    
    await StaffService.initialize_organization_staff(org_id, admin)
    
    return {"success": True, "message": "Staff module initialized with default permissions and roles"}
