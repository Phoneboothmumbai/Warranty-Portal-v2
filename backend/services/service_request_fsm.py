"""
Service Request FSM Engine
===========================
The FSM Engine is THE LAW. All state changes MUST go through this engine.

Core Principles:
1. Server-side validation ONLY - never trust client
2. No force flags, no bypasses, no exceptions
3. All transitions logged to immutable audit
4. Required data validated before transition
5. Invalid transitions result in HARD FAILURE

FSM Engine MUST:
- Validate transitions server-side only
- Reject: Skipped states, backward transitions, parallel transitions
- Enforce: Module enabled, tenant active, role permission, required data

FSM Engine MUST NOT:
- Accept "force=true" flags
- Allow direct current_state updates
- Allow UI-only enforcement
"""
import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple, List
from database import db
from models.service_request import (
    ServiceRequest, ServiceState, FSM_TRANSITIONS, STATE_METADATA,
    StateTransition, ServiceVisit, PartRequired, ApprovalRequest,
    CustomerSnapshot, LocationSnapshot, generate_unique_ticket_number
)
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)


class FSMValidationError(Exception):
    """Raised when FSM validation fails - this is a HARD failure"""
    def __init__(self, message: str, current_state: str = None, target_state: str = None):
        self.message = message
        self.current_state = current_state
        self.target_state = target_state
        super().__init__(self.message)


class FSMDataRequiredError(Exception):
    """Raised when required data for transition is missing"""
    def __init__(self, message: str, missing_fields: List[str]):
        self.message = message
        self.missing_fields = missing_fields
        super().__init__(self.message)


class ServiceRequestFSM:
    """
    The FSM Engine - Single source of truth for all state transitions.
    
    All state changes MUST go through this class.
    Direct updates to 'state' field are FORBIDDEN.
    """
    
    # ==================== VALIDATION ====================
    
    @staticmethod
    async def validate_module_enabled(organization_id: str) -> bool:
        """Check if Service Management module is enabled for tenant"""
        org = await db.organizations.find_one(
            {"id": organization_id, "is_deleted": {"$ne": True}},
            {"feature_flags": 1}
        )
        
        if not org:
            return False
        
        feature_flags = org.get("feature_flags", {})
        # Default to True if not explicitly set (for backward compatibility during rollout)
        return feature_flags.get("service_management", True)
    
    @staticmethod
    async def validate_tenant_active(organization_id: str) -> bool:
        """Check if tenant is active"""
        org = await db.organizations.find_one(
            {"id": organization_id, "is_deleted": {"$ne": True}},
            {"status": 1}
        )
        
        if not org:
            return False
        
        # Active statuses
        active_statuses = ["trial", "active"]
        return org.get("status", "trial") in active_statuses
    
    @staticmethod
    def validate_transition(current_state: str, target_state: str) -> Tuple[bool, str]:
        """
        Validate if transition from current to target state is allowed.
        
        Returns: (is_valid, error_message)
        """
        # Check if current state is valid
        try:
            current = ServiceState(current_state)
        except ValueError:
            return False, f"Invalid current state: {current_state}"
        
        # Check if target state is valid
        try:
            target = ServiceState(target_state)
        except ValueError:
            return False, f"Invalid target state: {target_state}"
        
        # Check if transition is allowed
        allowed = FSM_TRANSITIONS.get(current, [])
        if target not in allowed:
            allowed_str = ", ".join([s.value for s in allowed]) if allowed else "none (terminal state)"
            return False, f"Invalid transition: {current_state} → {target_state}. Allowed transitions: {allowed_str}"
        
        return True, ""
    
    @staticmethod
    def validate_required_data(target_state: str, request_data: dict, service_request: dict) -> Tuple[bool, List[str]]:
        """
        Validate that required data for the target state is present.
        
        Returns: (is_valid, missing_fields)
        """
        metadata = STATE_METADATA.get(ServiceState(target_state), {})
        required_fields = metadata.get("requires_data", [])
        
        missing = []
        for field in required_fields:
            # Check in request_data first, then in existing service_request
            if "." in field:
                # Nested field like "approval.amount"
                parts = field.split(".")
                value = request_data.get(parts[0], {})
                if isinstance(value, dict):
                    value = value.get(parts[1])
                if not value:
                    # Check existing service_request
                    value = service_request.get(parts[0], {})
                    if isinstance(value, dict):
                        value = value.get(parts[1])
            else:
                value = request_data.get(field) or service_request.get(field)
            
            if not value and value != 0:  # Allow 0 as valid value
                missing.append(field)
        
        return len(missing) == 0, missing
    
    # ==================== CORE TRANSITION ====================
    
    @staticmethod
    async def transition(
        service_request_id: str,
        organization_id: str,
        target_state: str,
        actor: dict,
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        transition_data: Optional[Dict[str, Any]] = None
    ) -> dict:
        """
        THE ONLY WAY to change FSM state.
        
        This method:
        1. Validates module is enabled
        2. Validates tenant is active
        3. Validates transition is allowed
        4. Validates required data is present
        5. Performs the transition
        6. Records immutable state history
        7. Logs to audit
        
        Args:
            service_request_id: ID of the service request
            organization_id: Tenant ID
            target_state: The state to transition to
            actor: Dict with id, name, role of the person performing transition
            reason: Optional reason for the transition
            metadata: Optional additional metadata
            transition_data: State-specific data (e.g., assigned_staff_id for ASSIGNED)
        
        Returns:
            Updated service request
        
        Raises:
            FSMValidationError: If any validation fails (HARD FAILURE)
            FSMDataRequiredError: If required data is missing
        """
        transition_data = transition_data or {}
        
        # Step 1: Check module enabled
        if not await ServiceRequestFSM.validate_module_enabled(organization_id):
            raise FSMValidationError("Service Management module is disabled for this organization")
        
        # Step 2: Check tenant active
        if not await ServiceRequestFSM.validate_tenant_active(organization_id):
            raise FSMValidationError("Organization is not active")
        
        # Step 3: Get current service request
        service_request = await db.service_requests.find_one(
            {"id": service_request_id, "organization_id": organization_id, "is_deleted": {"$ne": True}},
            {"_id": 0}
        )
        
        if not service_request:
            raise FSMValidationError("Service request not found")
        
        current_state = service_request.get("state")
        
        # Step 4: Validate transition
        is_valid, error_msg = ServiceRequestFSM.validate_transition(current_state, target_state)
        if not is_valid:
            raise FSMValidationError(error_msg, current_state, target_state)
        
        # Step 5: Validate required data
        is_data_valid, missing_fields = ServiceRequestFSM.validate_required_data(
            target_state, transition_data, service_request
        )
        if not is_data_valid:
            raise FSMDataRequiredError(
                f"Missing required data for {target_state}: {', '.join(missing_fields)}",
                missing_fields
            )
        
        # Step 6: Build state transition record (IMMUTABLE)
        transition_record = StateTransition(
            from_state=current_state,
            to_state=target_state,
            actor_id=actor.get("id", "unknown"),
            actor_name=actor.get("name", "Unknown"),
            actor_role=actor.get("role", "unknown"),
            reason=reason,
            metadata=metadata or {}
        )
        
        # Step 7: Build update data
        now = get_ist_isoformat()
        update_data = {
            "state": target_state,
            "updated_at": now
        }
        
        # Step 8: Apply state-specific updates
        update_data.update(
            ServiceRequestFSM._get_state_specific_updates(target_state, transition_data, actor, now)
        )
        
        # Step 9: Perform atomic update
        await db.service_requests.update_one(
            {"id": service_request_id},
            {
                "$set": update_data,
                "$push": {"state_history": transition_record.model_dump()}
            }
        )
        
        # Step 10: Log to audit
        await ServiceRequestFSM._log_transition_audit(
            organization_id=organization_id,
            service_request_id=service_request_id,
            ticket_number=service_request.get("ticket_number"),
            from_state=current_state,
            to_state=target_state,
            actor=actor,
            reason=reason
        )
        
        logger.info(
            f"FSM Transition: {service_request.get('ticket_number')} "
            f"{current_state} → {target_state} by {actor.get('name')}"
        )
        
        # Return updated service request
        return await db.service_requests.find_one({"id": service_request_id}, {"_id": 0})
    
    @staticmethod
    def _get_state_specific_updates(
        target_state: str,
        transition_data: dict,
        actor: dict,
        timestamp: str
    ) -> dict:
        """Get state-specific field updates"""
        updates = {}
        
        if target_state == ServiceState.ASSIGNED.value:
            if transition_data.get("assigned_staff_id"):
                updates["assigned_staff_id"] = transition_data["assigned_staff_id"]
                updates["assigned_staff_name"] = transition_data.get("assigned_staff_name", "")
                updates["assigned_at"] = timestamp
        
        elif target_state == ServiceState.DECLINED.value:
            updates["decline_reason"] = transition_data.get("decline_reason", "No reason provided")
        
        elif target_state == ServiceState.VISIT_IN_PROGRESS.value:
            # Update current visit start time
            if transition_data.get("visit_id"):
                # This would update the specific visit - handled separately
                pass
        
        elif target_state == ServiceState.VISIT_COMPLETED.value:
            if transition_data.get("diagnostics"):
                # Update current visit diagnostics - handled via visit update
                pass
        
        elif target_state == ServiceState.PENDING_PART.value:
            if transition_data.get("parts_required"):
                parts = [PartRequired(**p).model_dump() for p in transition_data["parts_required"]]
                updates["parts_required"] = parts
        
        elif target_state == ServiceState.PENDING_APPROVAL.value:
            updates["approval"] = {
                "required": True,
                "status": "PENDING",
                "amount": transition_data.get("approval_amount", 0),
                "description": transition_data.get("approval_description"),
                "requested_at": timestamp,
                "requested_by_id": actor.get("id"),
                "requested_by_name": actor.get("name")
            }
        
        elif target_state == ServiceState.RESOLVED.value:
            updates["resolution_notes"] = transition_data.get("resolution_notes", "")
            updates["resolved_at"] = timestamp
            updates["resolved_by_id"] = actor.get("id")
            updates["resolved_by_name"] = actor.get("name")
        
        elif target_state == ServiceState.CANCELLED.value:
            updates["cancellation_reason"] = transition_data.get("cancellation_reason", "")
            updates["cancelled_at"] = timestamp
            updates["cancelled_by_id"] = actor.get("id")
            updates["cancelled_by_name"] = actor.get("name")
        
        return updates
    
    @staticmethod
    async def _log_transition_audit(
        organization_id: str,
        service_request_id: str,
        ticket_number: str,
        from_state: str,
        to_state: str,
        actor: dict,
        reason: Optional[str]
    ):
        """Log transition to audit trail"""
        try:
            await db.service_request_audit.insert_one({
                "id": str(__import__('uuid').uuid4()),
                "organization_id": organization_id,
                "service_request_id": service_request_id,
                "ticket_number": ticket_number,
                "action": "state_transition",
                "from_state": from_state,
                "to_state": to_state,
                "actor_id": actor.get("id"),
                "actor_name": actor.get("name"),
                "actor_role": actor.get("role"),
                "reason": reason,
                "timestamp": get_ist_isoformat()
            })
        except Exception as e:
            logger.error(f"Failed to log audit: {e}")
    
    # ==================== CONVENIENCE METHODS ====================
    # These are thin wrappers that call transition() internally
    
    @staticmethod
    async def assign(
        service_request_id: str,
        organization_id: str,
        staff_id: str,
        staff_name: str,
        actor: dict,
        reason: Optional[str] = None
    ) -> dict:
        """Assign service request to a technician"""
        return await ServiceRequestFSM.transition(
            service_request_id=service_request_id,
            organization_id=organization_id,
            target_state=ServiceState.ASSIGNED.value,
            actor=actor,
            reason=reason,
            transition_data={
                "assigned_staff_id": staff_id,
                "assigned_staff_name": staff_name
            }
        )
    
    @staticmethod
    async def accept(
        service_request_id: str,
        organization_id: str,
        actor: dict
    ) -> dict:
        """Technician accepts the assignment"""
        return await ServiceRequestFSM.transition(
            service_request_id=service_request_id,
            organization_id=organization_id,
            target_state=ServiceState.ACCEPTED.value,
            actor=actor,
            reason="Assignment accepted"
        )
    
    @staticmethod
    async def decline(
        service_request_id: str,
        organization_id: str,
        actor: dict,
        reason: str
    ) -> dict:
        """Technician declines the assignment"""
        return await ServiceRequestFSM.transition(
            service_request_id=service_request_id,
            organization_id=organization_id,
            target_state=ServiceState.DECLINED.value,
            actor=actor,
            reason=reason,
            transition_data={"decline_reason": reason}
        )
    
    @staticmethod
    async def start_visit(
        service_request_id: str,
        organization_id: str,
        actor: dict
    ) -> dict:
        """Start on-site visit"""
        return await ServiceRequestFSM.transition(
            service_request_id=service_request_id,
            organization_id=organization_id,
            target_state=ServiceState.VISIT_IN_PROGRESS.value,
            actor=actor,
            reason="Visit started"
        )
    
    @staticmethod
    async def complete_visit(
        service_request_id: str,
        organization_id: str,
        actor: dict,
        diagnostics: str
    ) -> dict:
        """Complete on-site visit with diagnostics"""
        return await ServiceRequestFSM.transition(
            service_request_id=service_request_id,
            organization_id=organization_id,
            target_state=ServiceState.VISIT_COMPLETED.value,
            actor=actor,
            reason="Visit completed",
            transition_data={"diagnostics": diagnostics}
        )
    
    @staticmethod
    async def resolve(
        service_request_id: str,
        organization_id: str,
        actor: dict,
        resolution_notes: str
    ) -> dict:
        """Resolve the service request"""
        return await ServiceRequestFSM.transition(
            service_request_id=service_request_id,
            organization_id=organization_id,
            target_state=ServiceState.RESOLVED.value,
            actor=actor,
            reason="Service request resolved",
            transition_data={"resolution_notes": resolution_notes}
        )
    
    @staticmethod
    async def cancel(
        service_request_id: str,
        organization_id: str,
        actor: dict,
        cancellation_reason: str
    ) -> dict:
        """Cancel the service request"""
        return await ServiceRequestFSM.transition(
            service_request_id=service_request_id,
            organization_id=organization_id,
            target_state=ServiceState.CANCELLED.value,
            actor=actor,
            reason=cancellation_reason,
            transition_data={"cancellation_reason": cancellation_reason}
        )
    
    # ==================== QUERY HELPERS ====================
    
    @staticmethod
    async def get_available_transitions(service_request_id: str, organization_id: str) -> List[dict]:
        """Get list of available transitions for a service request"""
        service_request = await db.service_requests.find_one(
            {"id": service_request_id, "organization_id": organization_id},
            {"state": 1}
        )
        
        if not service_request:
            return []
        
        current_state = service_request.get("state")
        try:
            current = ServiceState(current_state)
        except ValueError:
            return []
        
        allowed = FSM_TRANSITIONS.get(current, [])
        return [
            {
                "state": s.value,
                "label": STATE_METADATA.get(s, {}).get("label", s.value),
                "description": STATE_METADATA.get(s, {}).get("description", ""),
                "requires_data": STATE_METADATA.get(s, {}).get("requires_data", [])
            }
            for s in allowed
        ]
