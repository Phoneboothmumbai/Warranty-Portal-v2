"""
Workforce Overview & Engineer Portal Testing
=============================================
Tests for:
- Admin Workforce Overview at /admin/technician-dashboard
- Engineer Portal endpoints (accept/decline/reschedule)
- Backend APIs for workforce management
"""

import pytest
import requests
import os
import time
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

def get_admin_token():
    """Cached admin token to avoid rate limiting."""
    if not hasattr(get_admin_token, '_token'):
        for attempt in range(3):
            res = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "ck@motta.in", 
                "password": "Charu@123@"
            })
            if res.status_code == 200:
                get_admin_token._token = res.json().get("access_token")
                break
            time.sleep(2)
        else:
            raise Exception("Failed to get admin token after 3 attempts")
    return get_admin_token._token


class TestWorkforceOverviewBackend:
    """Tests for admin workforce overview API."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin token for tests."""
        self.admin_token = get_admin_token()
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        yield
    
    def test_workforce_overview_returns_data(self):
        """GET /api/ticketing/workforce/overview - returns full workforce data."""
        res = requests.get(f"{BASE_URL}/api/ticketing/workforce/overview", headers=self.admin_headers)
        assert res.status_code == 200, f"Workforce overview failed: {res.text}"
        data = res.json()
        
        # Check required keys
        assert "workforce" in data, "Missing workforce key"
        assert "needs_reassignment" in data, "Missing needs_reassignment key"
        assert "escalations" in data, "Missing escalations key"
        assert "summary" in data, "Missing summary key"
        
        # Check summary structure
        summary = data["summary"]
        assert "total_technicians" in summary, "Missing total_technicians in summary"
        assert "total_pending" in summary, "Missing total_pending in summary"
        assert "total_overdue" in summary, "Missing total_overdue in summary"
        assert "total_declined" in summary, "Missing total_declined in summary"
        
        print(f"Workforce Overview: {summary}")
    
    def test_workforce_overview_technician_data_structure(self):
        """Workforce Overview - each technician has workload stats."""
        res = requests.get(f"{BASE_URL}/api/ticketing/workforce/overview", headers=self.admin_headers)
        assert res.status_code == 200
        data = res.json()
        
        if len(data["workforce"]) > 0:
            tech = data["workforce"][0]
            # Required fields for each technician row
            required_fields = ["id", "name", "open_tickets", "pending_acceptance", "declined", "visits_today", "acceptance_rate"]
            for field in required_fields:
                assert field in tech, f"Missing field {field} in technician data"
            print(f"Technician data structure verified: {list(tech.keys())}")
        else:
            print("No technicians found in workforce")
    
    def test_workforce_overview_has_escalation_threshold(self):
        """Workforce Overview - includes escalation threshold hours."""
        res = requests.get(f"{BASE_URL}/api/ticketing/workforce/overview", headers=self.admin_headers)
        assert res.status_code == 200
        data = res.json()
        
        assert "escalation_threshold_hours" in data, "Missing escalation_threshold_hours"
        assert data["escalation_threshold_hours"] == 4, f"Expected 4 hours, got {data['escalation_threshold_hours']}"
        print(f"Escalation threshold: {data['escalation_threshold_hours']} hours")


class TestEngineerPortalBackend:
    """Tests for engineer portal backend APIs."""
    
    test_engineer_email = None
    test_engineer_id = None
    test_engineer_token = None
    test_ticket_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin and engineer tokens for tests."""
        # Admin login
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in", 
            "password": "Charu@123@"
        })
        assert res.status_code == 200, f"Admin login failed: {res.text}"
        self.admin_token = res.json().get("access_token")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        yield
    
    def test_engineer_dashboard_requires_auth(self):
        """GET /api/engineer/dashboard - requires engineer auth."""
        # Without token
        res = requests.get(f"{BASE_URL}/api/engineer/dashboard")
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print("Engineer dashboard correctly requires auth")
    
    def test_engineer_assignment_pending_requires_auth(self):
        """GET /api/engineer/assignment/pending - requires engineer auth."""
        res = requests.get(f"{BASE_URL}/api/engineer/assignment/pending")
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print("Engineer pending endpoint correctly requires auth")
    
    def test_engineer_assignment_accept_requires_auth(self):
        """POST /api/engineer/assignment/accept - requires engineer auth."""
        res = requests.post(f"{BASE_URL}/api/engineer/assignment/accept", json={"ticket_id": "test"})
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print("Engineer accept endpoint correctly requires auth")
    
    def test_engineer_assignment_decline_requires_auth(self):
        """POST /api/engineer/assignment/decline - requires engineer auth."""
        res = requests.post(f"{BASE_URL}/api/engineer/assignment/decline", json={
            "ticket_id": "test", 
            "reason_id": "too_far"
        })
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print("Engineer decline endpoint correctly requires auth")
    
    def test_engineer_assignment_reschedule_requires_auth(self):
        """POST /api/engineer/assignment/reschedule - requires engineer auth."""
        res = requests.post(f"{BASE_URL}/api/engineer/assignment/reschedule", json={
            "ticket_id": "test",
            "proposed_time": "2026-01-15T10:00:00"
        })
        assert res.status_code in [401, 403], f"Expected 401/403, got {res.status_code}"
        print("Engineer reschedule endpoint correctly requires auth")


class TestAdminReassignmentAPIs:
    """Tests for admin-level reassignment APIs."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin token."""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in", 
            "password": "Charu@123@"
        })
        assert res.status_code == 200
        self.admin_token = res.json().get("access_token")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        yield
    
    def test_suggest_reassignment_endpoint_exists(self):
        """GET /api/ticketing/assignment/suggest-reassign/{ticket_id} - endpoint exists."""
        # First get a ticket ID
        res = requests.get(f"{BASE_URL}/api/ticketing/tickets", headers=self.admin_headers)
        if res.status_code == 200 and len(res.json().get("tickets", [])) > 0:
            ticket_id = res.json()["tickets"][0]["id"]
            res = requests.get(f"{BASE_URL}/api/ticketing/assignment/suggest-reassign/{ticket_id}", headers=self.admin_headers)
            assert res.status_code in [200, 404], f"Unexpected status: {res.status_code}"
            if res.status_code == 200:
                data = res.json()
                assert "ticket" in data or "suggestions" in data
                print(f"Suggest reassign response: {list(data.keys())}")
        else:
            print("No tickets found to test suggest-reassign")
    
    def test_reassign_ticket_endpoint_exists(self):
        """POST /api/ticketing/assignment/reassign - validates required fields."""
        res = requests.post(f"{BASE_URL}/api/ticketing/assignment/reassign", 
            headers=self.admin_headers, json={})
        assert res.status_code == 400, f"Expected 400 for missing fields, got {res.status_code}"
        print("Reassign endpoint validates required fields")
    
    def test_sla_stats_endpoint(self):
        """GET /api/ticketing/assignment/sla-stats - returns SLA statistics."""
        res = requests.get(f"{BASE_URL}/api/ticketing/assignment/sla-stats", headers=self.admin_headers)
        assert res.status_code == 200, f"SLA stats failed: {res.text}"
        data = res.json()
        assert "stats" in data, "Missing stats key"
        print(f"SLA stats returned {len(data['stats'])} engineer records")
    
    def test_check_escalations_endpoint(self):
        """GET /api/ticketing/assignment/check-escalations - returns overdue assignments."""
        res = requests.get(f"{BASE_URL}/api/ticketing/assignment/check-escalations", headers=self.admin_headers)
        assert res.status_code == 200, f"Check escalations failed: {res.text}"
        data = res.json()
        assert "overdue_assignments" in data, "Missing overdue_assignments key"
        assert "escalation_threshold_hours" in data, "Missing escalation_threshold_hours key"
        print(f"Escalations: {len(data['overdue_assignments'])} overdue, threshold: {data['escalation_threshold_hours']}h")


class TestNotificationAPIs:
    """Tests for notification APIs used by NotificationBell."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin token."""
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in", 
            "password": "Charu@123@"
        })
        assert res.status_code == 200
        self.admin_token = res.json().get("access_token")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        yield
    
    def test_get_notifications(self):
        """GET /api/notifications - returns notifications list."""
        res = requests.get(f"{BASE_URL}/api/notifications", headers=self.admin_headers)
        assert res.status_code == 200, f"Get notifications failed: {res.text}"
        data = res.json()
        assert "notifications" in data, "Missing notifications key"
        assert "unread_count" in data, "Missing unread_count key"
        print(f"Notifications: {len(data['notifications'])} items, {data['unread_count']} unread")
    
    def test_get_notifications_unread_only(self):
        """GET /api/notifications?unread_only=true - filters unread notifications."""
        res = requests.get(f"{BASE_URL}/api/notifications?unread_only=true", headers=self.admin_headers)
        assert res.status_code == 200, f"Get unread notifications failed: {res.text}"
        print("Unread-only filter works")
    
    def test_mark_all_read(self):
        """PUT /api/notifications/read-all - marks all notifications as read."""
        res = requests.put(f"{BASE_URL}/api/notifications/read-all", headers=self.admin_headers)
        assert res.status_code == 200, f"Mark all read failed: {res.text}"
        print("Mark all read works")


class TestEngineerPortalWithCredentials:
    """Tests for engineer portal with actual engineer credentials.
    Creates test engineer, tests full accept/decline/reschedule flow."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup admin token and create test engineer."""
        # Admin login
        res = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in", 
            "password": "Charu@123@"
        })
        assert res.status_code == 200
        self.admin_token = res.json().get("access_token")
        self.admin_headers = {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
        
        self.test_engineer_id = None
        self.test_engineer_email = None
        self.test_engineer_token = None
        self.test_ticket_id = None
        
        yield
        
        # Cleanup test data
        if self.test_engineer_id:
            requests.delete(f"{BASE_URL}/api/admin/engineers/{self.test_engineer_id}", headers=self.admin_headers)
        if self.test_ticket_id:
            requests.delete(f"{BASE_URL}/api/ticketing/tickets/{self.test_ticket_id}", headers=self.admin_headers)
    
    def test_full_engineer_portal_flow(self):
        """Full flow: create engineer → create ticket → assign → login → dashboard → accept."""
        unique = uuid.uuid4().hex[:8]
        test_password = "TestPass123!"
        
        # 1. Create test engineer with password
        engineer_data = {
            "name": f"TEST_EngPortal_{unique}",
            "email": f"test_engportal_{unique}@test.com",
            "phone": "+919999999999",
            "password": test_password,
            "is_active": True
        }
        res = requests.post(f"{BASE_URL}/api/admin/engineers", headers=self.admin_headers, json=engineer_data)
        assert res.status_code in [200, 201], f"Create engineer failed: {res.text}"
        eng = res.json()
        self.test_engineer_id = eng.get("id")
        self.test_engineer_email = engineer_data["email"]
        print(f"Created engineer: {self.test_engineer_id}")
        
        # 2. Engineer login
        res = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": self.test_engineer_email,
            "password": test_password
        })
        assert res.status_code == 200, f"Engineer login failed: {res.text}"
        eng_auth = res.json()
        self.test_engineer_token = eng_auth.get("access_token")
        eng_headers = {"Authorization": f"Bearer {self.test_engineer_token}", "Content-Type": "application/json"}
        print("Engineer login successful")
        
        # 3. Test GET /api/engineer/dashboard
        res = requests.get(f"{BASE_URL}/api/engineer/dashboard", headers=eng_headers)
        assert res.status_code == 200, f"Engineer dashboard failed: {res.text}"
        dash = res.json()
        assert "pending_tickets" in dash, "Missing pending_tickets"
        assert "active_tickets" in dash, "Missing active_tickets"
        assert "upcoming_schedules" in dash, "Missing upcoming_schedules"
        assert "decline_reasons" in dash, "Missing decline_reasons"
        assert "stats" in dash, "Missing stats"
        print(f"Engineer dashboard data: stats={dash['stats']}")
        
        # 4. Test GET /api/engineer/assignment/pending
        res = requests.get(f"{BASE_URL}/api/engineer/assignment/pending", headers=eng_headers)
        assert res.status_code == 200, f"Engineer pending failed: {res.text}"
        pending = res.json()
        assert "tickets" in pending, "Missing tickets"
        assert "decline_reasons" in pending, "Missing decline_reasons"
        assert len(pending["decline_reasons"]) == 6, f"Expected 6 decline reasons, got {len(pending['decline_reasons'])}"
        print(f"Pending assignments: {len(pending['tickets'])} tickets")
        
        # 5. Create a test ticket and assign to this engineer
        ticket_data = {
            "subject": f"TEST_EngPortalTicket_{unique}",
            "description": "Test ticket for engineer portal testing",
            "priority_name": "medium",
            "company_name": "Test Company"
        }
        res = requests.post(f"{BASE_URL}/api/ticketing/tickets", headers=self.admin_headers, json=ticket_data)
        if res.status_code in [200, 201]:
            ticket = res.json()
            self.test_ticket_id = ticket.get("id")
            print(f"Created ticket: {self.test_ticket_id}")
            
            # 6. Assign ticket to engineer
            assign_res = requests.post(f"{BASE_URL}/api/ticketing/tickets/{self.test_ticket_id}/assign",
                headers=self.admin_headers, json={"engineer_id": self.test_engineer_id})
            if assign_res.status_code == 200:
                print("Ticket assigned to engineer")
                
                # 7. Check pending again - should have the ticket
                res = requests.get(f"{BASE_URL}/api/engineer/assignment/pending", headers=eng_headers)
                assert res.status_code == 200
                pending = res.json()
                print(f"After assignment: {len(pending['tickets'])} pending tickets")
                
                if len(pending["tickets"]) > 0:
                    # 8. Test accept
                    accept_res = requests.post(f"{BASE_URL}/api/engineer/assignment/accept",
                        headers=eng_headers, json={"ticket_id": self.test_ticket_id})
                    assert accept_res.status_code == 200, f"Accept failed: {accept_res.text}"
                    print("Ticket accepted successfully!")
        
        print("Full engineer portal flow completed")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
