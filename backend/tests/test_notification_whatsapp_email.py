"""
WhatsApp and Email Notification Feature Tests
==============================================
Tests for:
- Settings page phone number and email list fields
- Settings save/load functionality
- POST /api/ticketing/tickets/{id}/send-notification endpoint
- Correct phone/email routing based on notification type
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')

# Session-level fixtures to avoid rate limiting
@pytest.fixture(scope="module")
def auth_token():
    """Login once and share token across all tests"""
    login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "ck@motta.in",
        "password": "Charu@123@"
    })
    assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
    return login_resp.json().get("access_token")


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Auth headers for all requests"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def test_ticket(auth_headers):
    """Get a ticket to use for testing"""
    tickets_resp = requests.get(f"{BASE_URL}/api/ticketing/tickets?limit=1", headers=auth_headers)
    assert tickets_resp.status_code == 200
    tickets_data = tickets_resp.json()
    tickets = tickets_data.get("tickets", [])
    assert len(tickets) > 0, "No tickets found for testing"
    return tickets[0]


@pytest.fixture(scope="module")
def assigned_ticket(auth_headers):
    """Get an assigned ticket to use for testing"""
    tickets_resp = requests.get(f"{BASE_URL}/api/ticketing/tickets?assigned=true&limit=1", headers=auth_headers)
    assert tickets_resp.status_code == 200
    tickets_data = tickets_resp.json()
    tickets = tickets_data.get("tickets", [])
    if not tickets:
        pytest.skip("No assigned tickets found")
    return tickets[0]


class TestSettingsPhoneEmailFields:
    """Test Settings API for phone numbers and email lists"""

    def test_get_settings_returns_phone_fields(self, auth_headers):
        """Settings API should return all team phone number fields"""
        resp = requests.get(f"{BASE_URL}/api/admin/settings", headers=auth_headers)
        assert resp.status_code == 200, f"Failed to get settings: {resp.text}"
        data = resp.json()
        
        # Verify all phone fields exist
        assert "billing_team_phone" in data, "Missing billing_team_phone field"
        assert "parts_order_phone" in data, "Missing parts_order_phone field"
        assert "quote_team_phone" in data, "Missing quote_team_phone field"
        assert "backend_team_phone" in data, "Missing backend_team_phone field"
        print(f"PASS: Settings contains all phone fields")

    def test_get_settings_returns_email_list_fields(self, auth_headers):
        """Settings API should return all team email list fields"""
        resp = requests.get(f"{BASE_URL}/api/admin/settings", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        
        # Verify all email list fields exist
        assert "billing_emails" in data, "Missing billing_emails field"
        assert "parts_order_emails" in data, "Missing parts_order_emails field"
        assert "quote_team_emails" in data, "Missing quote_team_emails field"
        print(f"PASS: Settings contains all email list fields")

    def test_save_and_load_all_phone_numbers(self, auth_headers):
        """Test saving all phone numbers to settings"""
        test_settings = {
            "billing_team_phone": "919111111111",
            "parts_order_phone": "919222222222",
            "quote_team_phone": "919333333333",
            "backend_team_phone": "919444444444"
        }
        resp = requests.put(f"{BASE_URL}/api/admin/settings", headers=auth_headers, json=test_settings)
        assert resp.status_code == 200, f"Failed to save settings: {resp.text}"
        
        # Verify saved
        get_resp = requests.get(f"{BASE_URL}/api/admin/settings", headers=auth_headers)
        data = get_resp.json()
        
        assert data.get("billing_team_phone") == "919111111111"
        assert data.get("parts_order_phone") == "919222222222"
        assert data.get("quote_team_phone") == "919333333333"
        assert data.get("backend_team_phone") == "919444444444"
        print(f"PASS: All phone numbers saved and retrieved correctly")

    def test_save_and_load_all_email_lists(self, auth_headers):
        """Test saving all email lists to settings"""
        test_settings = {
            "billing_emails": ["billing@test.com", "billing2@test.com"],
            "parts_order_emails": ["parts@test.com"],
            "quote_team_emails": ["quote@test.com", "quote2@test.com"]
        }
        resp = requests.put(f"{BASE_URL}/api/admin/settings", headers=auth_headers, json=test_settings)
        assert resp.status_code == 200
        
        # Verify saved
        get_resp = requests.get(f"{BASE_URL}/api/admin/settings", headers=auth_headers)
        data = get_resp.json()
        
        assert data.get("billing_emails") == ["billing@test.com", "billing2@test.com"]
        assert data.get("parts_order_emails") == ["parts@test.com"]
        assert data.get("quote_team_emails") == ["quote@test.com", "quote2@test.com"]
        print(f"PASS: All email lists saved and retrieved correctly")


class TestNotificationEndpoint:
    """Test /api/ticketing/tickets/{id}/send-notification endpoint"""

    def test_send_notification_assigned_type(self, auth_headers, assigned_ticket):
        """Test sending 'assigned' notification type"""
        ticket_id = assigned_ticket["id"]
        
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/send-notification",
            headers=auth_headers,
            json={"notification_type": "assigned"}
        )
        assert resp.status_code == 200, f"Notification failed: {resp.text}"
        data = resp.json()
        
        # Verify response structure
        assert data["success"] == True
        assert "wa_phone" in data
        assert "wa_message" in data
        assert "email_to" in data
        assert data["notification_type"] == "assigned"
        
        # Message should mention job assignment
        assert "Job Assignment" in data["wa_message"]
        print(f"PASS: Assigned notification works. Phone: {data['wa_phone']}")

    def test_send_notification_billing_type(self, auth_headers, test_ticket):
        """Test sending 'billing' notification type"""
        ticket_id = test_ticket["id"]
        
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/send-notification",
            headers=auth_headers,
            json={"notification_type": "billing"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["success"] == True
        assert data["notification_type"] == "billing"
        assert "Billing Pending" in data["wa_message"]
        assert data["wa_phone"] == "919111111111", f"Expected billing phone, got {data['wa_phone']}"
        print(f"PASS: Billing notification uses correct phone")

    def test_send_notification_awaiting_parts_type(self, auth_headers, test_ticket):
        """Test sending 'awaiting_parts' notification type"""
        ticket_id = test_ticket["id"]
        
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/send-notification",
            headers=auth_headers,
            json={"notification_type": "awaiting_parts"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["success"] == True
        assert data["notification_type"] == "awaiting_parts"
        assert "Parts Required" in data["wa_message"]
        assert data["wa_phone"] == "919222222222", f"Expected parts phone, got {data['wa_phone']}"
        print(f"PASS: Awaiting parts notification uses correct phone")

    def test_send_notification_quote_type(self, auth_headers, test_ticket):
        """Test sending 'quote' notification type"""
        ticket_id = test_ticket["id"]
        
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/send-notification",
            headers=auth_headers,
            json={"notification_type": "quote"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["success"] == True
        assert data["notification_type"] == "quote"
        assert "Quotation Required" in data["wa_message"]
        assert data["wa_phone"] == "919333333333", f"Expected quote phone, got {data['wa_phone']}"
        print(f"PASS: Quote notification uses correct phone")

    def test_send_notification_general_type(self, auth_headers, test_ticket):
        """Test sending 'general' notification type"""
        ticket_id = test_ticket["id"]
        
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/send-notification",
            headers=auth_headers,
            json={"notification_type": "general"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert data["success"] == True
        assert data["notification_type"] == "general"
        assert "Ticket Update" in data["wa_message"]
        assert data["wa_phone"] == "919444444444", f"Expected backend phone, got {data['wa_phone']}"
        print(f"PASS: General notification uses correct phone")

    def test_notification_adds_timeline_entry(self, auth_headers, test_ticket):
        """Test that sending notification adds a timeline entry"""
        ticket_id = test_ticket["id"]
        
        # Get ticket timeline count before
        ticket_resp = requests.get(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}", headers=auth_headers)
        before_timeline = ticket_resp.json().get("timeline", [])
        before_count = len(before_timeline)
        
        # Send notification
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/send-notification",
            headers=auth_headers,
            json={"notification_type": "general"}
        )
        assert resp.status_code == 200
        
        # Get ticket timeline count after
        ticket_resp = requests.get(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}", headers=auth_headers)
        after_timeline = ticket_resp.json().get("timeline", [])
        after_count = len(after_timeline)
        
        assert after_count > before_count, "Timeline entry not added"
        
        # Check the latest timeline entry
        latest_entry = after_timeline[-1]
        assert latest_entry.get("type") == "notification"
        print(f"PASS: Notification adds timeline entry")

    def test_notification_invalid_ticket_id_returns_404(self, auth_headers):
        """Test that sending notification to non-existent ticket returns 404"""
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/nonexistent-id-12345/send-notification",
            headers=auth_headers,
            json={"notification_type": "general"}
        )
        assert resp.status_code == 404
        print(f"PASS: Invalid ticket ID returns 404")

    def test_notification_unauthorized_returns_401_or_403(self):
        """Test that notification without auth returns 401/403"""
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/any-id/send-notification",
            json={"notification_type": "general"}
            # No auth header
        )
        assert resp.status_code in [401, 403]
        print(f"PASS: Unauthorized request returns {resp.status_code}")


class TestNotificationEmailMapping:
    """Test that notification types return correct email addresses from settings"""

    def test_billing_notification_has_correct_email(self, auth_headers, test_ticket):
        """Billing notification should use billing_emails from settings"""
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{test_ticket['id']}/send-notification",
            headers=auth_headers,
            json={"notification_type": "billing"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "billing@test.com" in data["email_to"] or "billing2@test.com" in data["email_to"]
        print(f"PASS: Billing uses correct emails: {data['email_to']}")

    def test_parts_notification_has_correct_email(self, auth_headers, test_ticket):
        """Parts notification should use parts_order_emails from settings"""
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{test_ticket['id']}/send-notification",
            headers=auth_headers,
            json={"notification_type": "awaiting_parts"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "parts@test.com" in data["email_to"]
        print(f"PASS: Parts uses correct emails: {data['email_to']}")

    def test_quote_notification_has_correct_email(self, auth_headers, test_ticket):
        """Quote notification should use quote_team_emails from settings"""
        resp = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{test_ticket['id']}/send-notification",
            headers=auth_headers,
            json={"notification_type": "quote"}
        )
        assert resp.status_code == 200
        data = resp.json()
        
        assert "quote@test.com" in data["email_to"] or "quote2@test.com" in data["email_to"]
        print(f"PASS: Quote uses correct emails: {data['email_to']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
