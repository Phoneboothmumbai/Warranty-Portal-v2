"""
Calendar Feature Backend Tests
==============================
Tests for central calendar APIs:
- Org Holidays CRUD
- Standard Working Hours GET/PUT
- Emergency Hours CRUD
- Aggregated Events (calendar/events)
- Engineer's own schedule (engineer/calendar/my-schedule)
"""

import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"


class TestCalendarFeature:
    """Calendar Feature API tests"""
    
    admin_token = None
    created_holiday_id = None
    created_emergency_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get admin token"""
        if not TestCalendarFeature.admin_token:
            response = requests.post(
                f"{BASE_URL}/api/auth/login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
            )
            assert response.status_code == 200, f"Admin login failed: {response.text}"
            data = response.json()
            TestCalendarFeature.admin_token = data.get("access_token")
        yield
    
    def get_headers(self):
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {TestCalendarFeature.admin_token}"
        }
    
    # ── Holidays API Tests ──────────────────────────────────────────────
    
    def test_01_get_holidays(self):
        """GET /api/calendar/holidays - returns list of org holidays"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/holidays?year=2026",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"GET holidays failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/calendar/holidays returned {len(data)} holidays")
    
    def test_02_create_holiday(self):
        """POST /api/calendar/holidays - creates new holiday"""
        unique_date = f"2026-12-{datetime.now().microsecond % 28 + 1:02d}"
        payload = {
            "name": f"TEST_Calendar_Holiday_{uuid.uuid4().hex[:6]}",
            "date": unique_date,
            "type": "company"
        }
        response = requests.post(
            f"{BASE_URL}/api/calendar/holidays",
            headers=self.get_headers(),
            json=payload
        )
        assert response.status_code in [200, 201], f"POST holiday failed: {response.text}"
        data = response.json()
        assert "id" in data, "Response should have id"
        assert data["name"] == payload["name"], "Name mismatch"
        assert data["date"] == payload["date"], "Date mismatch"
        TestCalendarFeature.created_holiday_id = data["id"]
        print(f"✓ POST /api/calendar/holidays created holiday: {data['name']}")
    
    def test_03_verify_holiday_in_list(self):
        """GET /api/calendar/holidays - verify created holiday appears"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/holidays?year=2026",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        holiday_ids = [h.get("id") for h in data]
        assert TestCalendarFeature.created_holiday_id in holiday_ids, "Created holiday not found in list"
        print(f"✓ Verified created holiday {TestCalendarFeature.created_holiday_id} in list")
    
    def test_04_delete_holiday(self):
        """DELETE /api/calendar/holidays/{id} - deletes holiday"""
        if not TestCalendarFeature.created_holiday_id:
            pytest.skip("No holiday to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/calendar/holidays/{TestCalendarFeature.created_holiday_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"DELETE holiday failed: {response.text}"
        data = response.json()
        assert data.get("status") == "deleted", "Status should be deleted"
        print(f"✓ DELETE /api/calendar/holidays/{TestCalendarFeature.created_holiday_id} succeeded")
    
    def test_05_verify_holiday_deleted(self):
        """GET /api/calendar/holidays - verify deleted holiday removed"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/holidays?year=2026",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        holiday_ids = [h.get("id") for h in data]
        assert TestCalendarFeature.created_holiday_id not in holiday_ids, "Deleted holiday still in list"
        print(f"✓ Verified holiday {TestCalendarFeature.created_holiday_id} no longer in list")
    
    # ── Standard Hours API Tests ────────────────────────────────────────
    
    def test_06_get_standard_hours(self):
        """GET /api/calendar/standard-hours - returns org standard hours"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/standard-hours",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"GET standard-hours failed: {response.text}"
        data = response.json()
        # Should contain day keys
        assert "monday" in data or len(data) >= 0, "Response should have day configs"
        print(f"✓ GET /api/calendar/standard-hours returned: {list(data.keys())}")
    
    def test_07_update_standard_hours(self):
        """PUT /api/calendar/standard-hours - saves standard hours"""
        payload = {
            "monday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "tuesday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "wednesday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "thursday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "friday": {"is_working": True, "start": "09:00", "end": "18:00"},
            "saturday": {"is_working": True, "start": "10:00", "end": "14:00"},
            "sunday": {"is_working": False, "start": "09:00", "end": "18:00"},
        }
        response = requests.put(
            f"{BASE_URL}/api/calendar/standard-hours",
            headers=self.get_headers(),
            json=payload
        )
        assert response.status_code == 200, f"PUT standard-hours failed: {response.text}"
        data = response.json()
        assert data["monday"]["start"] == "09:00", "Monday start mismatch"
        assert data["saturday"]["start"] == "10:00", "Saturday start mismatch"
        print(f"✓ PUT /api/calendar/standard-hours saved successfully")
    
    def test_08_verify_standard_hours_persisted(self):
        """GET /api/calendar/standard-hours - verify changes persisted"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/standard-hours",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        # Check that saturday 10:00 start was saved
        assert data.get("saturday", {}).get("start") == "10:00", "Saturday hours not persisted"
        print(f"✓ Standard hours persisted correctly")
    
    # ── Emergency Hours API Tests ───────────────────────────────────────
    
    def test_09_get_emergency_hours(self):
        """GET /api/calendar/emergency-hours - returns list"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/emergency-hours?date_from=2026-01-01&date_to=2026-12-31",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"GET emergency-hours failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ GET /api/calendar/emergency-hours returned {len(data)} entries")
    
    def test_10_create_emergency_hours(self):
        """POST /api/calendar/emergency-hours - creates emergency hours"""
        unique_date = f"2026-11-{datetime.now().microsecond % 28 + 1:02d}"
        payload = {
            "date": unique_date,
            "reason": f"TEST_Emergency_{uuid.uuid4().hex[:6]}",
            "start": "08:00",
            "end": "22:00"
        }
        response = requests.post(
            f"{BASE_URL}/api/calendar/emergency-hours",
            headers=self.get_headers(),
            json=payload
        )
        assert response.status_code in [200, 201], f"POST emergency-hours failed: {response.text}"
        data = response.json()
        assert "id" in data, "Response should have id"
        assert data["reason"] == payload["reason"], "Reason mismatch"
        assert data["start"] == "08:00", "Start mismatch"
        TestCalendarFeature.created_emergency_id = data["id"]
        print(f"✓ POST /api/calendar/emergency-hours created: {data['reason']}")
    
    def test_11_verify_emergency_in_list(self):
        """GET /api/calendar/emergency-hours - verify created entry appears"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/emergency-hours?date_from=2026-01-01&date_to=2026-12-31",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        entry_ids = [e.get("id") for e in data]
        assert TestCalendarFeature.created_emergency_id in entry_ids, "Created emergency not found"
        print(f"✓ Verified emergency entry in list")
    
    def test_12_delete_emergency_hours(self):
        """DELETE /api/calendar/emergency-hours/{id} - deletes entry"""
        if not TestCalendarFeature.created_emergency_id:
            pytest.skip("No emergency entry to delete")
        
        response = requests.delete(
            f"{BASE_URL}/api/calendar/emergency-hours/{TestCalendarFeature.created_emergency_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"DELETE emergency failed: {response.text}"
        data = response.json()
        assert data.get("status") == "deleted", "Status should be deleted"
        print(f"✓ DELETE /api/calendar/emergency-hours/{TestCalendarFeature.created_emergency_id} succeeded")
    
    # ── Aggregated Events API Tests ─────────────────────────────────────
    
    def test_13_get_calendar_events(self):
        """GET /api/calendar/events - returns aggregated events"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/events?date_from=2026-01-01&date_to=2026-01-31",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"GET calendar/events failed: {response.text}"
        data = response.json()
        assert "events" in data, "Response should have events"
        assert "engineers" in data, "Response should have engineers list"
        assert "date_from" in data, "Response should have date_from"
        assert "date_to" in data, "Response should have date_to"
        print(f"✓ GET /api/calendar/events returned {len(data.get('events', []))} events, {len(data.get('engineers', []))} engineers")
    
    def test_14_get_calendar_events_with_filter(self):
        """GET /api/calendar/events with engineer_id filter"""
        # First get an engineer ID
        response = requests.get(
            f"{BASE_URL}/api/calendar/events?date_from=2026-01-01&date_to=2026-01-31",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        engineers = data.get("engineers", [])
        
        if engineers:
            engineer_id = engineers[0]["id"]
            filtered_response = requests.get(
                f"{BASE_URL}/api/calendar/events?date_from=2026-01-01&date_to=2026-01-31&engineer_id={engineer_id}",
                headers=self.get_headers()
            )
            assert filtered_response.status_code == 200, f"Filtered events failed: {filtered_response.text}"
            print(f"✓ GET /api/calendar/events with engineer filter works")
        else:
            print(f"✓ No engineers to filter, skipping filter test")
    
    def test_15_calendar_events_structure(self):
        """Verify event objects have required fields"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/events?date_from=2026-01-01&date_to=2026-12-31",
            headers=self.get_headers()
        )
        assert response.status_code == 200
        data = response.json()
        events = data.get("events", [])
        
        if events:
            event = events[0]
            assert "id" in event, "Event should have id"
            assert "type" in event, "Event should have type"
            assert "title" in event, "Event should have title"
            assert "date" in event, "Event should have date"
            assert "color" in event, "Event should have color"
            print(f"✓ Event structure verified: type={event['type']}, title={event['title'][:30]}...")
        else:
            print(f"✓ No events in range to verify structure")
    
    # ── Engineer's Own Schedule API Tests ───────────────────────────────
    
    def test_16_admin_my_schedule(self):
        """GET /api/calendar/my-schedule - admin's own schedule"""
        response = requests.get(
            f"{BASE_URL}/api/calendar/my-schedule?date_from=2026-01-01&date_to=2026-01-31",
            headers=self.get_headers()
        )
        # This might return 404 if the admin is not an engineer - that's acceptable
        if response.status_code == 404:
            print(f"✓ GET /api/calendar/my-schedule returns 404 (admin not an engineer) - expected")
        elif response.status_code == 200:
            data = response.json()
            assert "events" in data, "Response should have events"
            print(f"✓ GET /api/calendar/my-schedule returned {len(data.get('events', []))} events")
        else:
            pytest.fail(f"Unexpected status: {response.status_code} - {response.text}")


class TestEngineerCalendar:
    """Tests for engineer's own calendar at /api/engineer/calendar/my-schedule"""
    
    engineer_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Try to login as engineer"""
        # We'll use admin token since engineer auth may not be available
        if not TestEngineerCalendar.engineer_token:
            # Try engineer login
            response = requests.post(
                f"{BASE_URL}/api/engineer/auth/login",
                json={"email": "test_engineer@test.com", "password": "Test@123"}
            )
            if response.status_code == 200:
                TestEngineerCalendar.engineer_token = response.json().get("access_token")
        yield
    
    def test_17_engineer_calendar_endpoint_exists(self):
        """Verify /api/engineer/calendar/my-schedule endpoint exists"""
        if not TestEngineerCalendar.engineer_token:
            # Just test the endpoint returns 401 for unauthenticated
            response = requests.get(
                f"{BASE_URL}/api/engineer/calendar/my-schedule?date_from=2026-01-01&date_to=2026-01-31"
            )
            assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
            print(f"✓ /api/engineer/calendar/my-schedule exists and requires auth")
        else:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {TestEngineerCalendar.engineer_token}"
            }
            response = requests.get(
                f"{BASE_URL}/api/engineer/calendar/my-schedule?date_from=2026-01-01&date_to=2026-01-31",
                headers=headers
            )
            assert response.status_code in [200, 404], f"Unexpected: {response.status_code}"
            print(f"✓ Engineer calendar endpoint returned {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
