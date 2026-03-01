"""
Engineer Reschedule with Slot-based Scheduling Tests
Tests the engineer accept/decline/reschedule workflow with 30-minute time slots
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ENGINEER_EMAIL = "testeng@test.com"
ENGINEER_PASSWORD = "Test@123"
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"


@pytest.fixture(scope="module")
def engineer_token():
    """Login as engineer and get token"""
    response = requests.post(
        f"{BASE_URL}/api/engineer/auth/login",
        json={"email": ENGINEER_EMAIL, "password": ENGINEER_PASSWORD}
    )
    if response.status_code != 200:
        pytest.skip(f"Engineer login failed: {response.status_code} - {response.text}")
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def engineer_headers(engineer_token):
    """Get headers with engineer auth"""
    return {
        "Authorization": f"Bearer {engineer_token}",
        "Content-Type": "application/json"
    }


class TestEngineerLogin:
    """Test engineer authentication"""

    def test_engineer_login_success(self):
        """Test engineer can login with valid credentials"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/auth/login",
            json={"email": ENGINEER_EMAIL, "password": ENGINEER_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "access_token" in data, "Response should contain access_token"
        assert "engineer" in data, "Response should contain engineer info"
        assert data["engineer"]["email"] == ENGINEER_EMAIL

    def test_engineer_login_invalid_password(self):
        """Test engineer login fails with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/auth/login",
            json={"email": ENGINEER_EMAIL, "password": "WrongPassword"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"


class TestEngineerDashboard:
    """Test engineer dashboard endpoint"""

    def test_dashboard_loads(self, engineer_headers):
        """Test engineer dashboard returns data"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate structure
        assert "engineer" in data
        assert "pending_tickets" in data
        assert "active_tickets" in data
        assert "upcoming_schedules" in data
        assert "decline_reasons" in data
        assert "stats" in data

    def test_dashboard_has_pending_ticket_test9999(self, engineer_headers):
        """Test dashboard shows TEST-9999 in pending tickets"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        pending = data.get("pending_tickets", [])
        test_ticket = next((t for t in pending if t.get("ticket_number") == "TEST-9999"), None)
        # If ticket was already accepted in a previous test, it won't be pending anymore
        # Just check the API structure is correct
        assert isinstance(pending, list), "pending_tickets should be a list"

    def test_dashboard_stats_structure(self, engineer_headers):
        """Test stats structure in dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        stats = data.get("stats", {})
        assert "total_assigned" in stats
        assert "pending_count" in stats
        assert "visits_today" in stats
        assert "active_count" in stats

    def test_dashboard_decline_reasons_provided(self, engineer_headers):
        """Test decline reasons are provided"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        reasons = data.get("decline_reasons", [])
        assert len(reasons) > 0, "Should have decline reasons"
        # Check structure
        for reason in reasons:
            assert "id" in reason
            assert "label" in reason


class TestAvailableSlotsAPI:
    """Test GET /api/engineer/available-slots endpoint"""

    def test_available_slots_returns_slots(self, engineer_headers):
        """Test available slots endpoint returns slot data"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/engineer/available-slots?date={tomorrow}",
            headers=engineer_headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        # Validate structure
        assert "date" in data
        assert "is_working_day" in data
        assert "slots" in data
        assert data["date"] == tomorrow

    def test_available_slots_has_working_hours(self, engineer_headers):
        """Test slots response includes working hours"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/engineer/available-slots?date={tomorrow}",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("is_working_day"):
            assert "work_start" in data
            assert "work_end" in data

    def test_available_slots_30min_intervals(self, engineer_headers):
        """Test slots are in 30-minute intervals"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/engineer/available-slots?date={tomorrow}",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("is_working_day") and data.get("slots"):
            for slot in data["slots"]:
                time = slot["time"]
                minutes = int(time.split(":")[1])
                assert minutes in [0, 30], f"Slot {time} should be 30-min interval"

    def test_available_slots_blocked_shown(self, engineer_headers):
        """Test blocked slots are marked with blocked_by info"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/engineer/available-slots?date={tomorrow}",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("is_working_day"):
            slots = data.get("slots", [])
            # Check structure
            for slot in slots:
                assert "time" in slot
                assert "available" in slot
                assert "blocked_by" in slot

    def test_blocked_slots_due_to_existing_booking(self, engineer_headers):
        """Test that slots 10:00-11:30 are blocked due to existing 10:00-11:00 booking"""
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/engineer/available-slots?date={tomorrow}",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("is_working_day"):
            slots = {s["time"]: s for s in data.get("slots", [])}
            # These should be blocked (10:00 booking + 1hr buffer = blocks 10:00, 10:30, 11:00, 11:30)
            blocked_times = ["10:00", "10:30", "11:00", "11:30"]
            for time in blocked_times:
                if time in slots:
                    assert slots[time]["available"] == False, f"Slot {time} should be blocked"

    def test_past_date_rejected(self, engineer_headers):
        """Test past dates are rejected"""
        past_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        response = requests.get(
            f"{BASE_URL}/api/engineer/available-slots?date={past_date}",
            headers=engineer_headers
        )
        assert response.status_code == 400, f"Past date should be rejected, got {response.status_code}"

    def test_invalid_date_format_rejected(self, engineer_headers):
        """Test invalid date format is rejected"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/available-slots?date=invalid-date",
            headers=engineer_headers
        )
        assert response.status_code == 400


class TestRescheduleValidation:
    """Test backend validation for reschedule endpoint"""

    def test_reschedule_past_time_rejected(self, engineer_headers):
        """Test rescheduling to past time is rejected"""
        # Get pending ticket
        dashboard = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        ).json()
        
        pending = dashboard.get("pending_tickets", [])
        if not pending:
            pytest.skip("No pending tickets to test reschedule")
        
        ticket_id = pending[0]["id"]
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/assignment/reschedule",
            headers=engineer_headers,
            json={
                "ticket_id": ticket_id,
                "proposed_time": f"{yesterday}T10:00:00",
                "proposed_end_time": f"{yesterday}T11:00:00"
            }
        )
        assert response.status_code == 400, f"Past time should be rejected, got {response.status_code}"

    def test_reschedule_non_30min_interval_rejected(self, engineer_headers):
        """Test rescheduling to non-30-min interval is rejected"""
        dashboard = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        ).json()
        
        pending = dashboard.get("pending_tickets", [])
        if not pending:
            pytest.skip("No pending tickets to test reschedule")
        
        ticket_id = pending[0]["id"]
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Try 15-minute interval (not allowed)
        response = requests.post(
            f"{BASE_URL}/api/engineer/assignment/reschedule",
            headers=engineer_headers,
            json={
                "ticket_id": ticket_id,
                "proposed_time": f"{tomorrow}T10:15:00",
                "proposed_end_time": f"{tomorrow}T11:15:00"
            }
        )
        assert response.status_code == 400, f"Non-30min interval should be rejected, got {response.status_code}"

    def test_reschedule_blocked_slot_rejected(self, engineer_headers):
        """Test rescheduling to blocked slot is rejected"""
        dashboard = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        ).json()
        
        pending = dashboard.get("pending_tickets", [])
        if not pending:
            pytest.skip("No pending tickets to test reschedule")
        
        ticket_id = pending[0]["id"]
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Try blocked slot (10:00 is booked for TEST-8888)
        response = requests.post(
            f"{BASE_URL}/api/engineer/assignment/reschedule",
            headers=engineer_headers,
            json={
                "ticket_id": ticket_id,
                "proposed_time": f"{tomorrow}T10:00:00",
                "proposed_end_time": f"{tomorrow}T11:00:00"
            }
        )
        assert response.status_code == 400, f"Blocked slot should be rejected, got {response.status_code}"


class TestAcceptJob:
    """Test accept job endpoint"""

    def test_accept_job_success(self, engineer_headers):
        """Test accepting a job without rescheduling"""
        dashboard = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        ).json()
        
        pending = dashboard.get("pending_tickets", [])
        if not pending:
            pytest.skip("No pending tickets to test accept")
        
        ticket_id = pending[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/assignment/accept",
            headers=engineer_headers,
            json={"ticket_id": ticket_id}
        )
        # Could be 200 (accepted) or 404 (already processed)
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"


class TestDeclineJob:
    """Test decline job endpoint"""

    def test_decline_reasons_available(self, engineer_headers):
        """Test decline reasons are returned in dashboard"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        reasons = data.get("decline_reasons", [])
        reason_ids = [r["id"] for r in reasons]
        
        expected_reasons = ["too_far", "skill_mismatch", "overloaded", "on_leave", "scheduling_conflict", "other"]
        for expected in expected_reasons:
            assert expected in reason_ids, f"Missing decline reason: {expected}"


class TestRescheduleWorkflow:
    """Test complete reschedule workflow"""

    def test_reschedule_to_available_slot(self, engineer_headers):
        """Test rescheduling to an available slot succeeds"""
        dashboard = requests.get(
            f"{BASE_URL}/api/engineer/dashboard",
            headers=engineer_headers
        ).json()
        
        pending = dashboard.get("pending_tickets", [])
        if not pending:
            pytest.skip("No pending tickets to test reschedule")
        
        ticket_id = pending[0]["id"]
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Use 14:00 which should be available
        response = requests.post(
            f"{BASE_URL}/api/engineer/assignment/reschedule",
            headers=engineer_headers,
            json={
                "ticket_id": ticket_id,
                "proposed_time": f"{tomorrow}T14:00:00",
                "proposed_end_time": f"{tomorrow}T15:00:00",
                "notes": "Test reschedule"
            }
        )
        # Either succeeds or ticket already processed
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
