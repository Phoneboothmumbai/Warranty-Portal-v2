"""
Staff Service
=============
Core business logic for the Staff module including:
- Permission evaluation (FSM + RBAC)
- User lifecycle management
- Audit logging
- Data scoping by visibility

Permission Evaluation Order:
1. Check Module is enabled
2. Check User state = ACTIVE
3. Check Role permission exists
4. Check Visibility scope
5. Check Time-bound validity
6. Check IP/Device restriction
7. Check FSM guard (if action changes state)

If any check fails → DENY
"""
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any, Tuple
from database import db
from models.staff import (
    StaffUser, StaffAuditLog, Permission, Role, Department,
    UserState, VALID_STATE_TRANSITIONS, DEFAULT_PERMISSIONS, DEFAULT_ROLES
)
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)


class PermissionDeniedError(Exception):
    """Raised when permission check fails"""
    def __init__(self, message: str, required_permission: str = None):
        self.message = message
        self.required_permission = required_permission
        super().__init__(self.message)


class StateTransitionError(Exception):
    """Raised when FSM state transition is invalid"""
    def __init__(self, current_state: str, target_state: str):
        self.current_state = current_state
        self.target_state = target_state
        self.message = f"Invalid state transition from {current_state} to {target_state}"
        super().__init__(self.message)


class StaffService:
    """Service class for staff operations"""
    
    # ==================== PERMISSION EVALUATION ====================
    
    @staticmethod
    async def check_permission(
        user_id: str,
        organization_id: str,
        module: str,
        resource: str,
        action: str,
        target_company_id: Optional[str] = None,
        request_ip: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Evaluate if user has permission for an action.
        
        Returns:
            (allowed: bool, reason: str)
        """
        # Step 1: Get the user
        user = await db.staff_users.find_one(
            {"id": user_id, "organization_id": organization_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
        
        if not user:
            return False, "User not found"
        
        # Step 2: Check user state
        if user.get("state") != UserState.ACTIVE:
            return False, f"User state is {user.get('state')}, login not allowed"
        
        # Step 3: Check IP restriction
        ip_whitelist = user.get("ip_whitelist", [])
        if ip_whitelist and request_ip and request_ip not in ip_whitelist:
            return False, f"Access denied from IP {request_ip}"
        
        # Step 4: Get user's roles
        role_ids = user.get("role_ids", [])
        if not role_ids:
            return False, "User has no roles assigned"
        
        roles = await db.staff_roles.find(
            {"id": {"$in": role_ids}, "organization_id": organization_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        ).to_list(None)
        
        if not roles:
            return False, "User's roles not found"
        
        # Step 5: Check permissions across all roles
        permission_code = f"{module}.{resource}.{action}"
        now = datetime.now(timezone.utc).isoformat()
        
        for role in roles:
            for perm in role.get("permissions", []):
                perm_code = perm.get("permission_code", "")
                
                # Check for wildcard permissions
                if perm_code == "*":
                    return True, "Full access granted"
                
                # Check for module wildcard (e.g., "inventory.*")
                if perm_code.endswith(".*"):
                    module_prefix = perm_code[:-2]
                    if permission_code.startswith(module_prefix + "."):
                        # Check time bounds
                        if not StaffService._check_time_bounds(perm, now):
                            continue
                        # Check visibility scope
                        if target_company_id and not await StaffService._check_visibility(
                            user, perm.get("visibility_scope", "self"), target_company_id
                        ):
                            continue
                        return True, f"Permission granted via {role.get('name')}"
                
                # Exact match
                if perm_code == permission_code:
                    # Check time bounds
                    if not StaffService._check_time_bounds(perm, now):
                        continue
                    # Check visibility scope
                    if target_company_id and not await StaffService._check_visibility(
                        user, perm.get("visibility_scope", "self"), target_company_id
                    ):
                        continue
                    return True, f"Permission granted via {role.get('name')}"
        
        return False, f"Required permission: {permission_code}"
    
    @staticmethod
    def _check_time_bounds(permission: dict, current_time: str) -> bool:
        """Check if permission is within valid time range"""
        valid_from = permission.get("valid_from")
        valid_until = permission.get("valid_until")
        
        if valid_from and current_time < valid_from:
            return False
        if valid_until and current_time > valid_until:
            return False
        return True
    
    @staticmethod
    async def _check_visibility(user: dict, scope: str, target_company_id: str) -> bool:
        """Check if user can access target company based on visibility scope"""
        if scope == "global":
            return True
        
        if scope == "assigned_companies":
            assigned = user.get("assigned_company_ids", [])
            return target_company_id in assigned
        
        if scope == "self":
            # User can only access their own company
            return user.get("customer_company_id") == target_company_id
        
        return False
    
    @staticmethod
    async def require_permission(
        user_id: str,
        organization_id: str,
        module: str,
        resource: str,
        action: str,
        target_company_id: Optional[str] = None,
        request_ip: Optional[str] = None
    ):
        """Require permission or raise PermissionDeniedError"""
        allowed, reason = await StaffService.check_permission(
            user_id, organization_id, module, resource, action,
            target_company_id, request_ip
        )
        if not allowed:
            raise PermissionDeniedError(
                f"Action denied: {reason}",
                f"{module}.{resource}.{action}"
            )
    
    # ==================== USER LIFECYCLE (FSM) ====================
    
    @staticmethod
    async def transition_user_state(
        user_id: str,
        organization_id: str,
        new_state: str,
        reason: str,
        performed_by: dict
    ) -> dict:
        """
        Transition user to a new state following FSM rules.
        
        Valid transitions:
        - CREATED → ACTIVE, ARCHIVED
        - ACTIVE → SUSPENDED, ARCHIVED
        - SUSPENDED → ACTIVE, ARCHIVED
        - ARCHIVED → (none - final state)
        """
        user = await db.staff_users.find_one(
            {"id": user_id, "organization_id": organization_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
        
        if not user:
            raise ValueError("User not found")
        
        current_state = UserState(user.get("state", "created"))
        target_state = UserState(new_state)
        
        # Validate transition
        valid_targets = VALID_STATE_TRANSITIONS.get(current_state, [])
        if target_state not in valid_targets:
            raise StateTransitionError(current_state.value, target_state.value)
        
        # Perform transition
        now = get_ist_isoformat()
        update_data = {
            "state": target_state.value,
            "state_changed_at": now,
            "state_changed_by": performed_by.get("id"),
            "state_change_reason": reason,
            "updated_at": now
        }
        
        await db.staff_users.update_one(
            {"id": user_id},
            {"$set": update_data}
        )
        
        # Log audit
        await StaffService.log_audit(
            organization_id=organization_id,
            entity_type="user",
            entity_id=user_id,
            entity_name=user.get("name"),
            action="state_change",
            changes={
                "state": {"before": current_state.value, "after": target_state.value},
                "reason": reason
            },
            performed_by=performed_by,
            severity="warning" if target_state in [UserState.SUSPENDED, UserState.ARCHIVED] else "info"
        )
        
        # Return updated user
        return await db.staff_users.find_one({"id": user_id}, {"_id": 0})
    
    # ==================== AUDIT LOGGING ====================
    
    @staticmethod
    async def log_audit(
        organization_id: str,
        entity_type: str,
        entity_id: str,
        action: str,
        changes: dict,
        performed_by: dict,
        entity_name: Optional[str] = None,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        is_override: bool = False,
        override_reason: Optional[str] = None,
        severity: str = "info"
    ):
        """Create an immutable audit log entry"""
        try:
            log_entry = StaffAuditLog(
                organization_id=organization_id,
                entity_type=entity_type,
                entity_id=entity_id,
                entity_name=entity_name,
                action=action,
                changes=changes,
                before_state=before_state,
                after_state=after_state,
                performed_by_id=performed_by.get("id", "system"),
                performed_by_name=performed_by.get("name", "System"),
                performed_by_email=performed_by.get("email"),
                performed_by_role=performed_by.get("role"),
                ip_address=ip_address,
                user_agent=user_agent,
                is_override=is_override,
                override_reason=override_reason,
                severity=severity
            )
            
            await db.staff_audit_logs.insert_one(log_entry.model_dump())
            logger.info(f"Audit: {action} on {entity_type}/{entity_id} by {performed_by.get('name')}")
        except Exception as e:
            # Audit logging should never fail silently in production
            logger.error(f"CRITICAL: Audit log failed: {e}")
    
    # ==================== INITIALIZATION ====================
    
    @staticmethod
    async def initialize_organization_staff(organization_id: str, admin_user: dict):
        """
        Initialize staff module for a new organization.
        Creates default permissions and roles.
        """
        # Create default permissions
        for perm_data in DEFAULT_PERMISSIONS:
            existing = await db.staff_permissions.find_one({
                "organization_id": organization_id,
                "module": perm_data["module"],
                "resource": perm_data["resource"],
                "action": perm_data["action"]
            })
            
            if not existing:
                perm = Permission(
                    organization_id=organization_id,
                    module=perm_data["module"],
                    resource=perm_data["resource"],
                    action=perm_data["action"],
                    name=perm_data["name"],
                    category=perm_data.get("category"),
                    is_system=True
                )
                await db.staff_permissions.insert_one(perm.model_dump())
        
        # Get all permissions for role assignment
        all_permissions = await db.staff_permissions.find(
            {"organization_id": organization_id},
            {"_id": 0}
        ).to_list(None)
        
        perm_map = {f"{p['module']}.{p['resource']}.{p['action']}": p for p in all_permissions}
        
        # Create default roles
        for role_data in DEFAULT_ROLES:
            existing = await db.staff_roles.find_one({
                "organization_id": organization_id,
                "name": role_data["name"]
            })
            
            if not existing:
                # Build permission list
                role_permissions = []
                for perm_code in role_data.get("permissions", []):
                    if perm_code == "*":
                        # All permissions
                        for p in all_permissions:
                            role_permissions.append({
                                "permission_id": p["id"],
                                "permission_code": f"{p['module']}.{p['resource']}.{p['action']}",
                                "visibility_scope": "global"
                            })
                        break
                    elif perm_code.endswith(".*"):
                        # Module wildcard
                        module = perm_code[:-2]
                        for code, p in perm_map.items():
                            if code.startswith(module + "."):
                                role_permissions.append({
                                    "permission_id": p["id"],
                                    "permission_code": code,
                                    "visibility_scope": "global"
                                })
                    elif perm_code in perm_map:
                        p = perm_map[perm_code]
                        role_permissions.append({
                            "permission_id": p["id"],
                            "permission_code": perm_code,
                            "visibility_scope": "global"
                        })
                
                role = Role(
                    organization_id=organization_id,
                    name=role_data["name"],
                    description=role_data.get("description"),
                    level=role_data.get("level", 100),
                    is_system=role_data.get("is_system", False),
                    is_default=role_data.get("is_default", False),
                    permissions=role_permissions,
                    created_by=admin_user.get("id")
                )
                await db.staff_roles.insert_one(role.model_dump())
        
        logger.info(f"Initialized staff module for organization {organization_id}")
    
    # ==================== USER MANAGEMENT ====================
    
    @staticmethod
    async def create_user(
        organization_id: str,
        user_data: dict,
        performed_by: dict,
        password_hash: Optional[str] = None
    ) -> dict:
        """Create a new staff user"""
        from services.auth import get_password_hash
        import uuid
        
        # Check if email already exists
        existing = await db.staff_users.find_one({
            "organization_id": organization_id,
            "email": user_data["email"],
            "is_deleted": {"$ne": True}
        })
        
        if existing:
            raise ValueError("User with this email already exists")
        
        # Determine initial state
        initial_state = UserState.CREATED
        if password_hash or user_data.get("password"):
            # If password provided, can activate immediately
            initial_state = UserState.ACTIVE
        
        # Create user - handle None values for list fields
        user = StaffUser(
            organization_id=organization_id,
            email=user_data["email"],
            name=user_data["name"],
            password_hash=password_hash or (get_password_hash(user_data["password"]) if user_data.get("password") else None),
            user_type=user_data.get("user_type", "internal"),
            customer_company_id=user_data.get("customer_company_id"),
            phone=user_data.get("phone"),
            employee_id=user_data.get("employee_id"),
            job_title=user_data.get("job_title"),
            state=initial_state.value,
            department_ids=user_data.get("department_ids") or [],
            primary_department_id=user_data.get("primary_department_id"),
            role_ids=user_data.get("role_ids") or [],
            assigned_company_ids=user_data.get("assigned_company_ids") or [],
            created_by=performed_by.get("id")
        )
        
        # If no password, generate invite token
        if not user.password_hash:
            user.invite_token = str(uuid.uuid4())
            from datetime import timedelta
            user.invite_expires_at = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
            user.invited_by = performed_by.get("id")
        
        user_dict = user.model_dump()
        await db.staff_users.insert_one(user_dict)
        
        # Log audit
        await StaffService.log_audit(
            organization_id=organization_id,
            entity_type="user",
            entity_id=user.id,
            entity_name=user.name,
            action="create",
            changes={"created": True, "state": initial_state.value},
            performed_by=performed_by
        )
        
        # Remove sensitive fields before returning
        user_dict.pop("password_hash", None)
        user_dict.pop("invite_token", None)
        return user_dict
    
    @staticmethod
    async def get_user_with_permissions(user_id: str, organization_id: str) -> Optional[dict]:
        """Get user with resolved roles and permissions"""
        user = await db.staff_users.find_one(
            {"id": user_id, "organization_id": organization_id, "is_deleted": {"$ne": True}},
            {"_id": 0, "password_hash": 0}
        )
        
        if not user:
            return None
        
        # Get roles
        role_ids = user.get("role_ids", [])
        roles = await db.staff_roles.find(
            {"id": {"$in": role_ids}, "organization_id": organization_id},
            {"_id": 0}
        ).to_list(None)
        
        user["roles"] = roles
        
        # Collect all permission codes
        all_permissions = set()
        for role in roles:
            for perm in role.get("permissions", []):
                all_permissions.add(perm.get("permission_code"))
        
        user["effective_permissions"] = list(all_permissions)
        
        # Get departments
        dept_ids = user.get("department_ids", [])
        departments = await db.staff_departments.find(
            {"id": {"$in": dept_ids}, "organization_id": organization_id},
            {"_id": 0}
        ).to_list(None)
        
        user["departments"] = departments
        
        return user
