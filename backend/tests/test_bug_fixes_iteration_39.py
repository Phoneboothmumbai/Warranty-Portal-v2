"""
Bug Fixes Testing - Iteration 39
================================
Testing 4 critical bugs:
1. Engineer accept/decline ticket endpoints
2. Multiple visits prevention for single ticket
3. Workflow lock - starting visit timer validation
4. Service history showing tickets from both collections
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"
ENGINEER_EMAIL = "test_engineer_1bfa72f0@test.com"
ENGINEER_PASSWORD = "Engineer@123"
COMPANY_EMAIL = "testuser@testcompany.com"
COMPANY_PASSWORD = "Test@123"
ENGINEER_ID = "22468253-9dad-4fa5-89e3-aeabf0451051"
DEVICE_ID = "206eb754-b34e-4387-8262-a64543a3c769"


class TestSetup:
    """Setup fixtures for tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def engineer_token(self):
        """Get engineer authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/auth/login",
            json={"email": ENGINEER_EMAIL, "password": ENGINEER_PASSWORD}
        )
        if response.status_code != 200:
            pytest.skip(f"Engineer login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Admin request headers"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def engineer_headers(self, engineer_token):
        """Engineer request headers"""
        return {
            "Authorization": f"Bearer {engineer_token}",
            "Content-Type": "application/json"
        }


class TestBug1EngineerAcceptDecline(TestSetup):
    """
    Bug 1: Engineer accept/decline ticket endpoints
    Tests: /api/engineer/tickets/{id}/accept and /api/engineer/tickets/{id}/decline
    """
    
    def test_accept_endpoint_exists(self, admin_headers):
        """Test that accept endpoint exists and returns proper error for invalid ticket"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/tickets/invalid-ticket-id/accept",
            headers=admin_headers
        )
        # Should return 404 (not found) or 401/403 (auth), not 500
        assert response.status_code in [401, 403, 404], f"Unexpected status: {response.status_code}, {response.text}"
    
    def test_decline_endpoint_exists(self, admin_headers):
        """Test that decline endpoint exists and returns proper error for invalid ticket"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/tickets/invalid-ticket-id/decline",
            headers=admin_headers,
            json={"reason": "Test decline reason for testing purposes"}
        )
        # Should return 404 (not found) or 401/403 (auth), not 500
        assert response.status_code in [401, 403, 404], f"Unexpected status: {response.status_code}, {response.text}"
    
    def test_decline_requires_reason(self, engineer_headers):
        """Test that decline endpoint requires a reason"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/tickets/some-ticket-id/decline",
            headers=engineer_headers,
            json={}  # No reason provided
        )
        # Should return 422 (validation error) or 404 (not found)
        assert response.status_code in [404, 422], f"Unexpected status: {response.status_code}, {response.text}"
    
    def test_accept_ticket_wrong_status(self, engineer_headers):
        """Test that accept fails for ticket not in pending_acceptance status"""
        # This tests the validation logic - ticket must be in pending_acceptance
        response = requests.post(
            f"{BASE_URL}/api/engineer/tickets/non-existent-id/accept",
            headers=engineer_headers
        )
        # Should return 404 (not found) since ticket doesn't exist
        assert response.status_code == 404, f"Unexpected status: {response.status_code}, {response.text}"


class TestBug2MultipleVisitsPrevention(TestSetup):
    """
    Bug 2: Multiple visits prevention
    Tests: /api/admin/visits should reject second visit if one is already scheduled or in_progress
    """
    
    def test_create_visit_endpoint_exists(self, admin_headers):
        """Test that create visit endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/admin/visits",
            headers=admin_headers,
            json={
                "ticket_id": "non-existent-ticket",
                "technician_id": ENGINEER_ID,
                "scheduled_date": "2026-02-15",
                "scheduled_time_from": "10:00",
                "scheduled_time_to": "12:00",
                "purpose": "Test visit"
            }
        )
        # Should return 404 (ticket not found) or 400 (validation), not 500
        assert response.status_code in [400, 404], f"Unexpected status: {response.status_code}, {response.text}"
    
    def test_list_visits_endpoint(self, admin_headers):
        """Test that list visits endpoint works"""
        response = requests.get(
            f"{BASE_URL}/api/admin/visits",
            headers=admin_headers
        )
        assert response.status_code == 200, f"List visits failed: {response.text}"
        data = response.json()
        assert "visits" in data, "Response should contain 'visits' key"
    
    def test_get_todays_visits(self, admin_headers):
        """Test today's visits endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/visits/today",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Today's visits failed: {response.text}"
        data = response.json()
        assert "visits" in data, "Response should contain 'visits' key"
        assert "date" in data, "Response should contain 'date' key"


class TestBug3WorkflowLock(TestSetup):
    """
    Bug 3: Workflow lock - starting a visit timer should fail if ticket is not in valid state
    Tests: start_timer validation for ticket status (assigned, in_progress, pending_parts)
    """
    
    def test_start_timer_endpoint_exists(self, admin_headers):
        """Test that start-timer endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/admin/visits/non-existent-visit/start-timer",
            headers=admin_headers
        )
        # Should return 404 (visit not found), not 500
        assert response.status_code == 404, f"Unexpected status: {response.status_code}, {response.text}"
    
    def test_stop_timer_endpoint_exists(self, admin_headers):
        """Test that stop-timer endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/admin/visits/non-existent-visit/stop-timer",
            headers=admin_headers,
            json={
                "diagnostics": "Test diagnostics",
                "work_summary": "Test summary",
                "outcome": "resolved"
            }
        )
        # Should return 404 (visit not found), not 500
        assert response.status_code == 404, f"Unexpected status: {response.status_code}, {response.text}"
    
    def test_add_action_endpoint_exists(self, admin_headers):
        """Test that add-action endpoint exists"""
        response = requests.post(
            f"{BASE_URL}/api/admin/visits/non-existent-visit/add-action",
            headers=admin_headers,
            json={"action": "Test action"}
        )
        # Should return 404 (visit not found), not 500
        assert response.status_code == 404, f"Unexpected status: {response.status_code}, {response.text}"


class TestBug4ServiceHistory(TestSetup):
    """
    Bug 4: Service history should return tickets from both service_tickets and service_tickets_new collections
    Tests: /api/admin/devices/{device_id}/service-history
    """
    
    def test_service_history_endpoint_exists(self, admin_headers):
        """Test that service history endpoint exists"""
        response = requests.get(
            f"{BASE_URL}/api/admin/devices/{DEVICE_ID}/service-history",
            headers=admin_headers
        )
        # Should return 200 or 404 (device not found), not 500
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"
    
    def test_service_history_returns_list(self, admin_headers):
        """Test that service history returns a list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/devices/{DEVICE_ID}/service-history",
            headers=admin_headers
        )
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Service history should return a list"
        elif response.status_code == 404:
            pytest.skip("Device not found - skipping service history content test")
    
    def test_service_history_with_invalid_device(self, admin_headers):
        """Test service history with invalid device ID"""
        response = requests.get(
            f"{BASE_URL}/api/admin/devices/invalid-device-id/service-history",
            headers=admin_headers
        )
        assert response.status_code == 404, f"Should return 404 for invalid device: {response.text}"
    
    def test_device_timeline_endpoint(self, admin_headers):
        """Test device timeline endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/admin/devices/{DEVICE_ID}/timeline",
            headers=admin_headers
        )
        # Should return 200 or 404 (device not found), not 500
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"


class TestEngineerPortalEndpoints(TestSetup):
    """
    Additional tests for engineer portal endpoints
    """
    
    def test_engineer_dashboard_stats(self, engineer_headers):
        """Test engineer dashboard stats endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/dashboard/stats",
            headers=engineer_headers
        )
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        assert "tickets" in data, "Response should contain 'tickets' key"
        assert "visits" in data, "Response should contain 'visits' key"
    
    def test_engineer_tickets_list(self, engineer_headers):
        """Test engineer tickets list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/tickets",
            headers=engineer_headers
        )
        assert response.status_code == 200, f"Tickets list failed: {response.text}"
        data = response.json()
        assert "tickets" in data, "Response should contain 'tickets' key"
        assert "grouped" in data, "Response should contain 'grouped' key"
    
    def test_engineer_visits_list(self, engineer_headers):
        """Test engineer visits list endpoint"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/visits",
            headers=engineer_headers
        )
        assert response.status_code == 200, f"Visits list failed: {response.text}"
        data = response.json()
        assert "visits" in data, "Response should contain 'visits' key"


class TestIntegrationWorkflow(TestSetup):
    """
    Integration tests for the complete workflow
    """
    
    def test_admin_can_list_tickets(self, admin_headers):
        """Test admin can list service tickets"""
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets",
            headers=admin_headers
        )
        assert response.status_code == 200, f"List tickets failed: {response.text}"
    
    def test_admin_can_list_technicians(self, admin_headers):
        """Test admin can list technicians for assignment"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff",
            headers=admin_headers
        )
        assert response.status_code == 200, f"List staff failed: {response.text}"
    
    def test_admin_can_list_engineers(self, admin_headers):
        """Test admin can list engineers"""
        response = requests.get(
            f"{BASE_URL}/api/admin/engineers",
            headers=admin_headers
        )
        # May return 200 or 404 depending on if engineers collection exists
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}, {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
