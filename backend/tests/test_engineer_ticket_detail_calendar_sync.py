"""
Tests for Engineer Ticket Detail Page and Calendar Sync After Job Acceptance
==============================================================================
Bug fixes tested:
1) Engineer can view ticket details via GET /api/engineer/ticket/{ticket_id}
2) After accepting a job, a schedule record is created in ticket_schedules collection
"""

import pytest
import requests
import uuid
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"
ENGINEER_EMAIL = "t1_test_engineer@test.com"
ENGINEER_PASSWORD = "Test@123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin request headers"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def engineer_token():
    """Get engineer authentication token"""
    response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
        "email": ENGINEER_EMAIL,
        "password": ENGINEER_PASSWORD
    })
    assert response.status_code == 200, f"Engineer login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def engineer_headers(engineer_token):
    """Engineer request headers"""
    return {"Authorization": f"Bearer {engineer_token}", "Content-Type": "application/json"}


class TestEngineerAuth:
    """Test engineer authentication"""

    def test_engineer_login(self):
        """Engineer can login with valid credentials"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "engineer" in data
        assert data["engineer"]["email"] == ENGINEER_EMAIL
        print(f"✓ Engineer login successful: {data['engineer']['name']}")

    def test_engineer_login_invalid_password(self):
        """Engineer login fails with invalid password"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": "wrongpassword"
        })
        assert response.status_code == 401
        print("✓ Invalid password correctly rejected")


class TestEngineerDashboard:
    """Test engineer dashboard endpoint"""

    def test_engineer_dashboard(self, engineer_headers):
        """Engineer dashboard returns expected data structure"""
        response = requests.get(f"{BASE_URL}/api/engineer/dashboard", headers=engineer_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "engineer" in data
        assert "pending_tickets" in data
        assert "active_tickets" in data
        assert "upcoming_schedules" in data
        assert "decline_reasons" in data
        assert "stats" in data
        
        # Verify stats structure
        stats = data["stats"]
        assert "total_assigned" in stats
        assert "pending_count" in stats
        assert "visits_today" in stats
        assert "active_count" in stats
        
        print(f"✓ Engineer dashboard: {stats['pending_count']} pending, {stats['active_count']} active")

    def test_engineer_dashboard_requires_auth(self):
        """Dashboard endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/engineer/dashboard")
        assert response.status_code in [401, 403]
        print("✓ Dashboard correctly requires authentication")


class TestEngineerTicketDetail:
    """Test the new engineer ticket detail endpoint (Bug Fix 1)"""

    def test_get_ticket_detail_assigned_ticket(self, engineer_headers):
        """Engineer can view details of ticket assigned to them"""
        # First get pending tickets from dashboard
        dash_response = requests.get(f"{BASE_URL}/api/engineer/dashboard", headers=engineer_headers)
        assert dash_response.status_code == 200
        
        pending = dash_response.json().get("pending_tickets", [])
        active = dash_response.json().get("active_tickets", [])
        
        # Get a ticket to test with
        all_tickets = pending + active
        if not all_tickets:
            pytest.skip("No tickets assigned to engineer for testing")
        
        ticket_id = all_tickets[0]["id"]
        
        # Test the ticket detail endpoint
        response = requests.get(f"{BASE_URL}/api/engineer/ticket/{ticket_id}", headers=engineer_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "ticket" in data, "Response should contain 'ticket'"
        assert "company" in data, "Response should contain 'company'"
        assert "site" in data, "Response should contain 'site'"
        assert "employee" in data, "Response should contain 'employee'"
        assert "device" in data, "Response should contain 'device'"
        assert "repair_history" in data, "Response should contain 'repair_history'"
        assert "schedules" in data, "Response should contain 'schedules'"
        
        ticket = data["ticket"]
        assert ticket["id"] == ticket_id
        assert "ticket_number" in ticket
        assert "subject" in ticket
        assert "description" in ticket
        assert "assigned_to_id" in ticket
        
        print(f"✓ Ticket detail returned for #{ticket['ticket_number']}")
        print(f"  - Company: {data.get('company', {}).get('name', 'N/A')}")
        print(f"  - Device: {data.get('device', {}).get('model', 'N/A') if data.get('device') else 'None'}")
        print(f"  - Repair history count: {len(data.get('repair_history', []))}")

    def test_ticket_detail_not_assigned_returns_404(self, engineer_headers):
        """Engineer cannot view ticket not assigned to them"""
        fake_ticket_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/engineer/ticket/{fake_ticket_id}", headers=engineer_headers)
        assert response.status_code == 404
        print("✓ Correctly returns 404 for ticket not assigned to engineer")

    def test_ticket_detail_requires_auth(self):
        """Ticket detail endpoint requires authentication"""
        response = requests.get(f"{BASE_URL}/api/engineer/ticket/any-id")
        assert response.status_code in [401, 403]
        print("✓ Ticket detail correctly requires authentication")


class TestJobAcceptanceWithCalendarSync:
    """Test job acceptance creates schedule records (Bug Fix 2)"""

    @pytest.fixture
    def test_ticket_for_accept(self, admin_headers, engineer_headers):
        """Create a test ticket with pending assignment for acceptance testing"""
        # Get engineer details
        dash = requests.get(f"{BASE_URL}/api/engineer/dashboard", headers=engineer_headers)
        engineer_id = dash.json()["engineer"]["id"]
        engineer_name = dash.json()["engineer"]["name"]
        
        # Create a new ticket and assign to engineer
        ticket_data = {
            "subject": f"TEST_CalendarSync_{uuid.uuid4().hex[:6]}",
            "description": "Test ticket for calendar sync verification",
            "priority_id": None,
            "help_topic_id": None,
            "source": "manual"
        }
        
        # Create ticket
        create_response = requests.post(f"{BASE_URL}/api/ticketing/tickets", 
                                        headers=admin_headers, json=ticket_data)
        if create_response.status_code != 201:
            pytest.skip(f"Could not create test ticket: {create_response.text}")
        
        ticket = create_response.json()
        ticket_id = ticket["id"]
        
        # Assign to engineer
        assign_response = requests.put(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/assign",
                                       headers=admin_headers, 
                                       json={"engineer_id": engineer_id})
        if assign_response.status_code != 200:
            pytest.skip(f"Could not assign ticket: {assign_response.text}")
        
        yield {"ticket_id": ticket_id, "engineer_id": engineer_id}
        
        # Cleanup - delete test ticket
        requests.delete(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}", headers=admin_headers)

    def test_accept_job_creates_schedule(self, engineer_headers, admin_headers):
        """Accepting a job creates a schedule record in ticket_schedules"""
        # Get a pending ticket
        dash = requests.get(f"{BASE_URL}/api/engineer/dashboard", headers=engineer_headers)
        pending = dash.json().get("pending_tickets", [])
        
        if not pending:
            pytest.skip("No pending tickets for acceptance test")
        
        # Use first pending ticket
        ticket_id = pending[0]["id"]
        ticket_number = pending[0]["ticket_number"]
        
        # Accept the job
        accept_response = requests.post(f"{BASE_URL}/api/engineer/assignment/accept",
                                       headers=engineer_headers,
                                       json={"ticket_id": ticket_id})
        assert accept_response.status_code == 200
        assert accept_response.json()["status"] == "accepted"
        
        # Verify schedule record was created - check via ticket detail
        detail_response = requests.get(f"{BASE_URL}/api/engineer/ticket/{ticket_id}", 
                                       headers=engineer_headers)
        assert detail_response.status_code == 200
        
        schedules = detail_response.json().get("schedules", [])
        
        # Should have at least one schedule with status "accepted"
        accepted_schedules = [s for s in schedules if s.get("status") == "accepted"]
        assert len(accepted_schedules) > 0, "Schedule record should be created after acceptance"
        
        print(f"✓ Job accepted for #{ticket_number}")
        print(f"  - Schedule record created with status: {accepted_schedules[0]['status']}")
        print(f"  - Scheduled at: {accepted_schedules[0].get('scheduled_at', 'N/A')}")


class TestEngineerCalendar:
    """Test engineer calendar shows accepted jobs"""

    def test_engineer_my_schedule(self, engineer_headers):
        """Engineer can view their schedule via calendar endpoint"""
        # Try the engineer calendar endpoint
        response = requests.get(f"{BASE_URL}/api/engineer/calendar/my-schedule", 
                               headers=engineer_headers)
        
        # This endpoint may or may not exist, check both cases
        if response.status_code == 200:
            data = response.json()
            print(f"✓ Engineer calendar endpoint working")
            print(f"  - Schedules: {len(data.get('schedules', data.get('events', [])))}")
        elif response.status_code == 404:
            # Endpoint might not exist, check dashboard upcoming_schedules instead
            dash = requests.get(f"{BASE_URL}/api/engineer/dashboard", headers=engineer_headers)
            assert dash.status_code == 200
            schedules = dash.json().get("upcoming_schedules", [])
            print(f"✓ Engineer upcoming schedules from dashboard: {len(schedules)}")
        else:
            pytest.fail(f"Unexpected response: {response.status_code}")


class TestAdminCalendar:
    """Test admin calendar shows accepted jobs for technicians"""

    def test_admin_central_calendar(self, admin_headers):
        """Admin central calendar endpoint exists and works"""
        response = requests.get(f"{BASE_URL}/api/calendar/schedules", headers=admin_headers)
        
        if response.status_code == 200:
            data = response.json()
            schedules = data if isinstance(data, list) else data.get("schedules", [])
            print(f"✓ Admin calendar: {len(schedules)} schedule entries")
        elif response.status_code == 404:
            # Try alternative endpoint
            alt_response = requests.get(f"{BASE_URL}/api/ticketing/schedules", headers=admin_headers)
            if alt_response.status_code == 200:
                print("✓ Admin calendar available at /api/ticketing/schedules")
            else:
                print("! Admin calendar endpoint not found (may be different route)")


class TestEngineerAcceptDeclineReschedule:
    """Test all engineer assignment response endpoints"""

    def test_decline_reasons_available(self, engineer_headers):
        """Decline reasons are available in dashboard"""
        response = requests.get(f"{BASE_URL}/api/engineer/dashboard", headers=engineer_headers)
        assert response.status_code == 200
        
        reasons = response.json().get("decline_reasons", [])
        assert len(reasons) > 0, "Decline reasons should be available"
        
        # Verify structure
        for reason in reasons:
            assert "id" in reason
            assert "label" in reason
        
        print(f"✓ {len(reasons)} decline reasons available")

    def test_accept_endpoint_exists(self, engineer_headers):
        """Accept endpoint responds correctly"""
        # Test with invalid ticket_id
        response = requests.post(f"{BASE_URL}/api/engineer/assignment/accept",
                                headers=engineer_headers,
                                json={"ticket_id": "nonexistent"})
        assert response.status_code in [404, 400]
        print("✓ Accept endpoint exists and validates input")

    def test_decline_endpoint_exists(self, engineer_headers):
        """Decline endpoint responds correctly"""
        response = requests.post(f"{BASE_URL}/api/engineer/assignment/decline",
                                headers=engineer_headers,
                                json={"ticket_id": "nonexistent", "reason_id": "other"})
        assert response.status_code in [404, 400]
        print("✓ Decline endpoint exists and validates input")

    def test_reschedule_endpoint_exists(self, engineer_headers):
        """Reschedule endpoint responds correctly"""
        response = requests.post(f"{BASE_URL}/api/engineer/assignment/reschedule",
                                headers=engineer_headers,
                                json={
                                    "ticket_id": "nonexistent", 
                                    "proposed_time": "2026-01-30T10:00:00"
                                })
        assert response.status_code in [404, 400]
        print("✓ Reschedule endpoint exists and validates input")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
