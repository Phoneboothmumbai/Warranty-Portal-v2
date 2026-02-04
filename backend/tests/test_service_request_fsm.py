"""
Service Request FSM Module Tests
=================================
Tests for the 13-state FSM-driven service request management system.

FSM States: CREATED, ASSIGNED, DECLINED, ACCEPTED, VISIT_IN_PROGRESS, 
VISIT_COMPLETED, PENDING_PART, PENDING_APPROVAL, REPAIR_IN_PROGRESS, 
QC_PENDING, READY_FOR_RETURN, RESOLVED, CANCELLED

Test Coverage:
- Create service request (returns ticket_number, state=CREATED)
- List service requests with pagination
- Get statistics by state
- Get all FSM states with metadata
- Get single request with available_transitions
- FSM state transitions (valid and invalid)
- Convenience endpoints (assign, accept, decline, start-visit, complete-visit, resolve, cancel)
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "Admin@123!"


class TestServiceRequestFSM:
    """Service Request FSM API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Authentication failed: {response.status_code}")
        
        yield
        
        # Cleanup - delete test service requests
        self._cleanup_test_data()
    
    def _cleanup_test_data(self):
        """Clean up test data created during tests"""
        try:
            # Get all service requests with TEST_ prefix in title
            response = self.session.get(f"{BASE_URL}/api/admin/service-requests?search=TEST_&limit=100")
            if response.status_code == 200:
                data = response.json()
                for req in data.get("service_requests", []):
                    if req.get("title", "").startswith("TEST_"):
                        self.session.delete(f"{BASE_URL}/api/admin/service-requests/{req['id']}")
        except Exception as e:
            print(f"Cleanup error: {e}")
    
    # ==================== AUTHENTICATION TESTS ====================
    
    def test_service_requests_require_auth(self):
        """Service request endpoints require authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        response = no_auth_session.get(f"{BASE_URL}/api/admin/service-requests")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Service request endpoints require authentication")
    
    # ==================== GET STATES TESTS ====================
    
    def test_get_all_fsm_states(self):
        """GET /api/admin/service-requests/states - Get all FSM states with metadata"""
        response = self.session.get(f"{BASE_URL}/api/admin/service-requests/states")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "states" in data, "Response should contain 'states'"
        
        states = data["states"]
        assert len(states) == 13, f"Expected 13 states, got {len(states)}"
        
        # Verify all expected states are present
        expected_states = [
            "CREATED", "ASSIGNED", "DECLINED", "ACCEPTED", "VISIT_IN_PROGRESS",
            "VISIT_COMPLETED", "PENDING_PART", "PENDING_APPROVAL", "REPAIR_IN_PROGRESS",
            "QC_PENDING", "READY_FOR_RETURN", "RESOLVED", "CANCELLED"
        ]
        
        state_values = [s["value"] for s in states]
        for expected in expected_states:
            assert expected in state_values, f"Missing state: {expected}"
        
        # Verify state metadata structure
        for state in states:
            assert "value" in state, "State should have 'value'"
            assert "label" in state, "State should have 'label'"
            assert "description" in state, "State should have 'description'"
            assert "color" in state, "State should have 'color'"
            assert "is_terminal" in state, "State should have 'is_terminal'"
        
        print(f"✓ All 13 FSM states returned with metadata: {state_values}")
    
    # ==================== CREATE SERVICE REQUEST TESTS ====================
    
    def test_create_service_request_basic(self):
        """POST /api/admin/service-requests - Create basic service request"""
        payload = {
            "title": "TEST_Basic Service Request",
            "description": "Test description for basic service request",
            "category": "repair",
            "priority": "medium"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        
        service_request = data.get("service_request")
        assert service_request is not None, "Response should contain service_request"
        
        # Verify ticket_number is generated (6-char alphanumeric)
        ticket_number = service_request.get("ticket_number")
        assert ticket_number is not None, "Service request should have ticket_number"
        assert len(ticket_number) == 6, f"Ticket number should be 6 chars, got {len(ticket_number)}"
        
        # Verify initial state is CREATED
        assert service_request.get("state") == "CREATED", f"Initial state should be CREATED, got {service_request.get('state')}"
        
        # Verify state_history has initial entry
        state_history = service_request.get("state_history", [])
        assert len(state_history) >= 1, "Should have at least one state history entry"
        assert state_history[0].get("to_state") == "CREATED", "First history entry should be CREATED"
        
        print(f"✓ Created service request with ticket: {ticket_number}, state: CREATED")
        return service_request
    
    def test_create_service_request_with_customer(self):
        """POST /api/admin/service-requests - Create with customer details"""
        payload = {
            "title": "TEST_Service Request with Customer",
            "description": "Test with customer snapshot",
            "category": "maintenance",
            "priority": "high",
            "customer_name": "John Test",
            "customer_email": "john.test@example.com",
            "customer_mobile": "9876543210",
            "customer_company_name": "Test Corp"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        service_request = data.get("service_request")
        
        # Verify customer snapshot
        customer_snapshot = service_request.get("customer_snapshot")
        assert customer_snapshot is not None, "Should have customer_snapshot"
        assert customer_snapshot.get("name") == "John Test"
        assert customer_snapshot.get("email") == "john.test@example.com"
        assert customer_snapshot.get("mobile") == "9876543210"
        
        print(f"✓ Created service request with customer snapshot: {customer_snapshot.get('name')}")
    
    def test_create_service_request_with_location(self):
        """POST /api/admin/service-requests - Create with location details"""
        payload = {
            "title": "TEST_Service Request with Location",
            "description": "Test with location snapshot",
            "category": "installation",
            "priority": "urgent",
            "location_address": "123 Test Street",
            "location_city": "Mumbai",
            "location_pincode": "400001"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        service_request = data.get("service_request")
        
        # Verify location snapshot
        location_snapshot = service_request.get("location_snapshot")
        assert location_snapshot is not None, "Should have location_snapshot"
        assert location_snapshot.get("address") == "123 Test Street"
        assert location_snapshot.get("city") == "Mumbai"
        
        print(f"✓ Created service request with location: {location_snapshot.get('address')}")
    
    # ==================== LIST SERVICE REQUESTS TESTS ====================
    
    def test_list_service_requests(self):
        """GET /api/admin/service-requests - List with pagination"""
        response = self.session.get(f"{BASE_URL}/api/admin/service-requests")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "service_requests" in data, "Response should contain 'service_requests'"
        assert "total" in data, "Response should contain 'total'"
        assert "page" in data, "Response should contain 'page'"
        assert "limit" in data, "Response should contain 'limit'"
        assert "pages" in data, "Response should contain 'pages'"
        
        print(f"✓ Listed service requests: {data.get('total')} total, page {data.get('page')}/{data.get('pages')}")
    
    def test_list_service_requests_with_filters(self):
        """GET /api/admin/service-requests - List with state and priority filters"""
        # Create a test request first
        self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Filter Test Request",
            "priority": "high"
        })
        
        # Filter by priority
        response = self.session.get(f"{BASE_URL}/api/admin/service-requests?priority=high")
        assert response.status_code == 200
        
        data = response.json()
        for req in data.get("service_requests", []):
            assert req.get("priority") == "high", "All results should have high priority"
        
        # Filter by state
        response = self.session.get(f"{BASE_URL}/api/admin/service-requests?state=CREATED")
        assert response.status_code == 200
        
        data = response.json()
        for req in data.get("service_requests", []):
            assert req.get("state") == "CREATED", "All results should be in CREATED state"
        
        print("✓ Filtering by state and priority works correctly")
    
    def test_list_service_requests_search(self):
        """GET /api/admin/service-requests - Search by ticket/title"""
        # Create a test request
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Unique Search Term XYZ123"
        })
        
        if create_response.status_code == 200:
            # Search by title
            response = self.session.get(f"{BASE_URL}/api/admin/service-requests?search=XYZ123")
            assert response.status_code == 200
            
            data = response.json()
            assert data.get("total", 0) >= 1, "Should find at least one result"
            
            print("✓ Search functionality works correctly")
    
    # ==================== GET STATS TESTS ====================
    
    def test_get_service_request_stats(self):
        """GET /api/admin/service-requests/stats - Get statistics by state"""
        response = self.session.get(f"{BASE_URL}/api/admin/service-requests/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "total" in data, "Response should contain 'total'"
        assert "open" in data, "Response should contain 'open'"
        assert "closed" in data, "Response should contain 'closed'"
        assert "by_state" in data, "Response should contain 'by_state'"
        
        # Verify open + closed = total (approximately, accounting for other states)
        by_state = data.get("by_state", {})
        resolved = by_state.get("RESOLVED", 0)
        cancelled = by_state.get("CANCELLED", 0)
        assert data.get("closed") == resolved + cancelled, "Closed should equal RESOLVED + CANCELLED"
        
        print(f"✓ Stats: Total={data.get('total')}, Open={data.get('open')}, Closed={data.get('closed')}")
    
    # ==================== GET SINGLE REQUEST TESTS ====================
    
    def test_get_service_request_detail(self):
        """GET /api/admin/service-requests/{id} - Get single request with available_transitions"""
        # Create a test request first
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Detail Request"
        })
        assert create_response.status_code == 200
        
        service_request = create_response.json().get("service_request")
        request_id = service_request.get("id")
        
        # Get detail
        response = self.session.get(f"{BASE_URL}/api/admin/service-requests/{request_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert data.get("id") == request_id, "Should return correct request"
        assert "available_transitions" in data, "Should include available_transitions"
        assert "state_metadata" in data, "Should include state_metadata"
        
        # For CREATED state, should have ASSIGNED and CANCELLED as available transitions
        available = [t.get("state") for t in data.get("available_transitions", [])]
        assert "ASSIGNED" in available, "CREATED should allow transition to ASSIGNED"
        assert "CANCELLED" in available, "CREATED should allow transition to CANCELLED"
        
        print(f"✓ Got request detail with available transitions: {available}")
    
    def test_get_nonexistent_request(self):
        """GET /api/admin/service-requests/{id} - 404 for non-existent request"""
        response = self.session.get(f"{BASE_URL}/api/admin/service-requests/nonexistent-id-12345")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Returns 404 for non-existent request")
    
    # ==================== FSM TRANSITION TESTS ====================
    
    def test_transition_created_to_assigned(self):
        """POST /api/admin/service-requests/{id}/transition - CREATED -> ASSIGNED"""
        # Create request
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Transition to Assigned"
        })
        service_request = create_response.json().get("service_request")
        request_id = service_request.get("id")
        
        # Transition to ASSIGNED
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ASSIGNED",
            "assigned_staff_id": "test-staff-id-123",
            "reason": "Assigning to technician"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True
        assert data.get("service_request", {}).get("state") == "ASSIGNED"
        
        print("✓ Transition CREATED -> ASSIGNED successful")
    
    def test_transition_assigned_to_accepted(self):
        """POST /api/admin/service-requests/{id}/transition - ASSIGNED -> ACCEPTED"""
        # Create and assign
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Transition to Accepted"
        })
        service_request = create_response.json().get("service_request")
        request_id = service_request.get("id")
        
        # Assign
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ASSIGNED",
            "assigned_staff_id": "test-staff-id-123"
        })
        
        # Accept
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ACCEPTED",
            "reason": "Assignment accepted"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "ACCEPTED"
        
        print("✓ Transition ASSIGNED -> ACCEPTED successful")
    
    def test_transition_assigned_to_declined(self):
        """POST /api/admin/service-requests/{id}/transition - ASSIGNED -> DECLINED"""
        # Create and assign
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Transition to Declined"
        })
        service_request = create_response.json().get("service_request")
        request_id = service_request.get("id")
        
        # Assign
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ASSIGNED",
            "assigned_staff_id": "test-staff-id-123"
        })
        
        # Decline
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "DECLINED",
            "decline_reason": "Not available this week",
            "reason": "Technician declined"
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "DECLINED"
        
        print("✓ Transition ASSIGNED -> DECLINED successful")
    
    def test_full_happy_path_to_resolved(self):
        """Test full FSM flow: CREATED -> ASSIGNED -> ACCEPTED -> VISIT_IN_PROGRESS -> VISIT_COMPLETED -> RESOLVED"""
        # Create
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Full Happy Path"
        })
        service_request = create_response.json().get("service_request")
        request_id = service_request.get("id")
        
        # CREATED -> ASSIGNED
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ASSIGNED",
            "assigned_staff_id": "test-staff-id-123"
        })
        assert response.status_code == 200
        assert response.json().get("service_request", {}).get("state") == "ASSIGNED"
        
        # ASSIGNED -> ACCEPTED
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ACCEPTED"
        })
        assert response.status_code == 200
        assert response.json().get("service_request", {}).get("state") == "ACCEPTED"
        
        # ACCEPTED -> VISIT_IN_PROGRESS
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "VISIT_IN_PROGRESS"
        })
        assert response.status_code == 200
        assert response.json().get("service_request", {}).get("state") == "VISIT_IN_PROGRESS"
        
        # VISIT_IN_PROGRESS -> VISIT_COMPLETED
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "VISIT_COMPLETED",
            "diagnostics": "Found faulty component, replaced successfully"
        })
        assert response.status_code == 200
        assert response.json().get("service_request", {}).get("state") == "VISIT_COMPLETED"
        
        # VISIT_COMPLETED -> RESOLVED
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "RESOLVED",
            "resolution_notes": "Issue resolved, device working normally"
        })
        assert response.status_code == 200
        
        final_state = response.json().get("service_request", {})
        assert final_state.get("state") == "RESOLVED"
        assert final_state.get("resolution_notes") == "Issue resolved, device working normally"
        
        # Verify state history has all transitions
        state_history = final_state.get("state_history", [])
        states_in_history = [h.get("to_state") for h in state_history]
        expected_states = ["CREATED", "ASSIGNED", "ACCEPTED", "VISIT_IN_PROGRESS", "VISIT_COMPLETED", "RESOLVED"]
        for expected in expected_states:
            assert expected in states_in_history, f"Missing {expected} in state history"
        
        print("✓ Full happy path CREATED -> RESOLVED completed successfully")
    
    def test_cancel_from_any_state(self):
        """Test cancellation from various states"""
        # Create and cancel from CREATED
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Cancel from Created"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "CANCELLED",
            "cancellation_reason": "Customer cancelled request"
        })
        assert response.status_code == 200
        assert response.json().get("service_request", {}).get("state") == "CANCELLED"
        
        print("✓ Cancellation from CREATED state works")
        
        # Create, assign, and cancel from ASSIGNED
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Cancel from Assigned"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ASSIGNED",
            "assigned_staff_id": "test-staff-id-123"
        })
        
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "CANCELLED",
            "cancellation_reason": "No longer needed"
        })
        assert response.status_code == 200
        assert response.json().get("service_request", {}).get("state") == "CANCELLED"
        
        print("✓ Cancellation from ASSIGNED state works")
    
    # ==================== INVALID TRANSITION TESTS ====================
    
    def test_invalid_transition_rejected(self):
        """Invalid transitions should be rejected (e.g., CREATED -> ACCEPTED)"""
        # Create request
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Invalid Transition"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        # Try invalid transition: CREATED -> ACCEPTED (should fail, must go through ASSIGNED first)
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ACCEPTED"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        assert "Invalid transition" in response.json().get("detail", "")
        
        print("✓ Invalid transition CREATED -> ACCEPTED correctly rejected")
    
    def test_invalid_transition_from_resolved(self):
        """Cannot transition from terminal state RESOLVED"""
        # Create and go to RESOLVED
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Resolved Terminal"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        # Quick path to RESOLVED
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ASSIGNED", "assigned_staff_id": "test-staff"
        })
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ACCEPTED"
        })
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "VISIT_IN_PROGRESS"
        })
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "VISIT_COMPLETED", "diagnostics": "Done"
        })
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "RESOLVED", "resolution_notes": "Fixed"
        })
        
        # Try to transition from RESOLVED
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ACCEPTED"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print("✓ Cannot transition from terminal state RESOLVED")
    
    def test_invalid_transition_from_cancelled(self):
        """Cannot transition from terminal state CANCELLED"""
        # Create and cancel
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Cancelled Terminal"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "CANCELLED", "cancellation_reason": "Test"
        })
        
        # Try to transition from CANCELLED
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/transition", json={
            "target_state": "ASSIGNED", "assigned_staff_id": "test"
        })
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        
        print("✓ Cannot transition from terminal state CANCELLED")
    
    # ==================== CONVENIENCE ENDPOINT TESTS ====================
    
    def test_assign_endpoint(self):
        """POST /api/admin/service-requests/{id}/assign - Convenience endpoint"""
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Assign Endpoint"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        response = self.session.post(
            f"{BASE_URL}/api/admin/service-requests/{request_id}/assign?staff_id=test-staff-123"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "ASSIGNED"
        
        print("✓ /assign convenience endpoint works")
    
    def test_accept_endpoint(self):
        """POST /api/admin/service-requests/{id}/accept - Convenience endpoint"""
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Accept Endpoint"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        # First assign
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/assign?staff_id=test-staff")
        
        # Then accept
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/accept")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "ACCEPTED"
        
        print("✓ /accept convenience endpoint works")
    
    def test_decline_endpoint(self):
        """POST /api/admin/service-requests/{id}/decline - Convenience endpoint"""
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Decline Endpoint"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        # First assign
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/assign?staff_id=test-staff")
        
        # Then decline
        response = self.session.post(
            f"{BASE_URL}/api/admin/service-requests/{request_id}/decline?reason=Not%20available"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "DECLINED"
        
        print("✓ /decline convenience endpoint works")
    
    def test_start_visit_endpoint(self):
        """POST /api/admin/service-requests/{id}/start-visit - Convenience endpoint"""
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Start Visit Endpoint"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        # Setup: assign and accept
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/assign?staff_id=test-staff")
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/accept")
        
        # Start visit
        response = self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/start-visit")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "VISIT_IN_PROGRESS"
        
        print("✓ /start-visit convenience endpoint works")
    
    def test_complete_visit_endpoint(self):
        """POST /api/admin/service-requests/{id}/complete-visit - Convenience endpoint"""
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Complete Visit Endpoint"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        # Setup: assign, accept, start visit
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/assign?staff_id=test-staff")
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/accept")
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/start-visit")
        
        # Complete visit
        response = self.session.post(
            f"{BASE_URL}/api/admin/service-requests/{request_id}/complete-visit?diagnostics=Found%20issue"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "VISIT_COMPLETED"
        
        print("✓ /complete-visit convenience endpoint works")
    
    def test_resolve_endpoint(self):
        """POST /api/admin/service-requests/{id}/resolve - Convenience endpoint"""
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Resolve Endpoint"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        # Setup: full path to VISIT_COMPLETED
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/assign?staff_id=test-staff")
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/accept")
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/start-visit")
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/complete-visit?diagnostics=Done")
        
        # Resolve
        response = self.session.post(
            f"{BASE_URL}/api/admin/service-requests/{request_id}/resolve?resolution_notes=Issue%20fixed"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "RESOLVED"
        
        print("✓ /resolve convenience endpoint works")
    
    def test_cancel_endpoint(self):
        """POST /api/admin/service-requests/{id}/cancel - Convenience endpoint"""
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_Cancel Endpoint"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        # Cancel
        response = self.session.post(
            f"{BASE_URL}/api/admin/service-requests/{request_id}/cancel?cancellation_reason=Customer%20request"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert response.json().get("service_request", {}).get("state") == "CANCELLED"
        
        print("✓ /cancel convenience endpoint works")
    
    # ==================== STATE HISTORY TESTS ====================
    
    def test_state_history_endpoint(self):
        """GET /api/admin/service-requests/{id}/history - Get state transition history"""
        # Create and do some transitions
        create_response = self.session.post(f"{BASE_URL}/api/admin/service-requests", json={
            "title": "TEST_History Endpoint"
        })
        request_id = create_response.json().get("service_request", {}).get("id")
        
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/assign?staff_id=test-staff")
        self.session.post(f"{BASE_URL}/api/admin/service-requests/{request_id}/accept")
        
        # Get history
        response = self.session.get(f"{BASE_URL}/api/admin/service-requests/{request_id}/history")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "history" in data, "Response should contain 'history'"
        assert "ticket_number" in data, "Response should contain 'ticket_number'"
        
        history = data.get("history", [])
        assert len(history) >= 3, f"Should have at least 3 history entries, got {len(history)}"
        
        print(f"✓ State history endpoint returns {len(history)} entries")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
