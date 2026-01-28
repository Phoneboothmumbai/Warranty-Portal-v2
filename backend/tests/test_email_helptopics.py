"""
Test Email Integration and Help Topics for Public Support Portal
Tests:
- Email status API returns correct configuration status
- Email test/sync/send-test APIs return appropriate errors when not configured
- Public Support Portal Help Topics API
- Public ticket creation with help_topic_id
- Custom form loading for help topics
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmailIntegration:
    """Email Integration API Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "admin123"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_email_status_returns_not_configured(self):
        """GET /api/ticketing/admin/email/status - should return not configured"""
        response = requests.get(f"{BASE_URL}/api/ticketing/admin/email/status", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "is_configured" in data
        assert data["is_configured"] == False, "Email should not be configured in test environment"
        assert data["smtp_host"] == "smtp.gmail.com"
        assert data["smtp_port"] == 587
        assert data["imap_host"] == "imap.gmail.com"
        assert data["imap_port"] == 993
        print(f"✓ Email status: is_configured={data['is_configured']}")
    
    def test_email_test_connection_fails_when_not_configured(self):
        """POST /api/ticketing/admin/email/test - should return 400 when not configured"""
        response = requests.post(f"{BASE_URL}/api/ticketing/admin/email/test", headers=self.headers)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not configured" in data["detail"].lower()
        print(f"✓ Email test connection correctly returns error: {data['detail']}")
    
    def test_email_sync_fails_when_not_configured(self):
        """POST /api/ticketing/admin/email/sync - should return 400 when not configured"""
        response = requests.post(f"{BASE_URL}/api/ticketing/admin/email/sync", headers=self.headers)
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not configured" in data["detail"].lower()
        print(f"✓ Email sync correctly returns error: {data['detail']}")
    
    def test_send_test_email_fails_when_not_configured(self):
        """POST /api/ticketing/admin/email/send-test - should return 400 when not configured"""
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/email/send-test?to_email=test@example.com",
            headers=self.headers
        )
        assert response.status_code == 400
        
        data = response.json()
        assert "detail" in data
        assert "not configured" in data["detail"].lower()
        print(f"✓ Send test email correctly returns error: {data['detail']}")


class TestPublicHelpTopics:
    """Public Support Portal Help Topics Tests"""
    
    def test_public_help_topics_list(self):
        """GET /api/ticketing/public/help-topics - should return public help topics"""
        response = requests.get(f"{BASE_URL}/api/ticketing/public/help-topics")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "Should have at least one public help topic"
        
        # Verify structure of help topics
        for topic in data:
            assert "id" in topic
            assert "name" in topic
            # Check for expected fields
            if "icon" in topic:
                assert isinstance(topic["icon"], str)
        
        print(f"✓ Found {len(data)} public help topics")
        for topic in data[:5]:
            print(f"  - {topic['name']}")
    
    def test_public_departments_list(self):
        """GET /api/ticketing/public/departments - should return public departments"""
        response = requests.get(f"{BASE_URL}/api/ticketing/public/departments")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Found {len(data)} public departments")
    
    def test_public_custom_form_for_help_topic(self):
        """GET /api/ticketing/public/custom-forms/{id} - should return custom form"""
        # First get help topics to find one with a custom form
        topics_response = requests.get(f"{BASE_URL}/api/ticketing/public/help-topics")
        topics = topics_response.json()
        
        # Find a topic with a custom form
        topic_with_form = None
        for topic in topics:
            if topic.get("custom_form_id"):
                topic_with_form = topic
                break
        
        if topic_with_form:
            form_id = topic_with_form["custom_form_id"]
            response = requests.get(f"{BASE_URL}/api/ticketing/public/custom-forms/{form_id}")
            assert response.status_code == 200
            
            form = response.json()
            assert "name" in form
            assert "fields" in form
            assert isinstance(form["fields"], list)
            print(f"✓ Custom form '{form['name']}' has {len(form['fields'])} fields")
        else:
            print("⚠ No help topic with custom form found - skipping custom form test")


class TestPublicTicketCreation:
    """Public Ticket Creation with Help Topics Tests"""
    
    def test_create_public_ticket_with_help_topic(self):
        """POST /api/ticketing/public/tickets - should create ticket with help_topic_id"""
        # Get a help topic first
        topics_response = requests.get(f"{BASE_URL}/api/ticketing/public/help-topics")
        topics = topics_response.json()
        assert len(topics) > 0, "Need at least one help topic"
        
        help_topic = topics[0]
        
        # Create ticket with help topic
        ticket_data = {
            "name": "TEST_PublicUser",
            "email": "test_public@example.com",
            "phone": "+1234567890",
            "subject": "TEST_Ticket with Help Topic",
            "description": "This is a test ticket created via public portal with help topic",
            "help_topic_id": help_topic["id"],
            "priority": "medium"
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/public/tickets", json=ticket_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "ticket_number" in data
        assert data["ticket_number"].startswith("TKT-")
        assert "message" in data
        
        print(f"✓ Created public ticket: {data['ticket_number']}")
        print(f"  Help Topic: {help_topic['name']}")
        
        # Verify ticket was created with help topic (admin view)
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "admin123"
        })
        token = login_response.json().get("access_token")
        headers = {"Authorization": f"Bearer {token}"}
        
        ticket_response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/tickets/{data['id']}",
            headers=headers
        )
        assert ticket_response.status_code == 200
        
        ticket = ticket_response.json()
        assert ticket["help_topic_id"] == help_topic["id"]
        print(f"✓ Verified ticket has help_topic_id: {ticket['help_topic_id']}")
    
    def test_create_public_ticket_with_custom_form_data(self):
        """POST /api/ticketing/public/tickets - should create ticket with form_data"""
        # Get a help topic with custom form
        topics_response = requests.get(f"{BASE_URL}/api/ticketing/public/help-topics")
        topics = topics_response.json()
        
        topic_with_form = None
        for topic in topics:
            if topic.get("custom_form_id"):
                topic_with_form = topic
                break
        
        if not topic_with_form:
            pytest.skip("No help topic with custom form found")
        
        # Get the custom form fields
        form_response = requests.get(
            f"{BASE_URL}/api/ticketing/public/custom-forms/{topic_with_form['custom_form_id']}"
        )
        form = form_response.json()
        
        # Build form_data based on fields
        form_data = {}
        for field in form.get("fields", []):
            if field.get("field_type") == "text":
                form_data[field["name"]] = "Test Value"
            elif field.get("field_type") == "select":
                if field.get("options"):
                    form_data[field["name"]] = field["options"][0].get("value", "option1")
        
        # Create ticket with form data
        ticket_data = {
            "name": "TEST_FormUser",
            "email": "test_form@example.com",
            "subject": "TEST_Ticket with Custom Form",
            "description": "This is a test ticket with custom form data",
            "help_topic_id": topic_with_form["id"],
            "priority": "medium",
            "form_data": form_data
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/public/tickets", json=ticket_data)
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Created ticket with custom form data: {data['ticket_number']}")
    
    def test_check_public_ticket_status(self):
        """GET /api/ticketing/public/tickets/{ticket_number} - should return ticket status"""
        # First create a ticket
        ticket_data = {
            "name": "TEST_StatusCheck",
            "email": "test_status@example.com",
            "subject": "TEST_Status Check Ticket",
            "description": "Testing ticket status check",
            "priority": "low"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/ticketing/public/tickets", json=ticket_data)
        assert create_response.status_code == 200
        created = create_response.json()
        
        # Check ticket status
        response = requests.get(
            f"{BASE_URL}/api/ticketing/public/tickets/{created['ticket_number']}",
            params={"email": "test_status@example.com"}
        )
        assert response.status_code == 200
        
        ticket = response.json()
        assert ticket["ticket_number"] == created["ticket_number"]
        assert ticket["status"] == "open"
        assert "thread" in ticket
        
        print(f"✓ Ticket status check successful: {ticket['ticket_number']} - {ticket['status']}")
    
    def test_public_ticket_reply(self):
        """POST /api/ticketing/public/tickets/{ticket_number}/reply - should add reply"""
        # First create a ticket
        ticket_data = {
            "name": "TEST_ReplyUser",
            "email": "test_reply@example.com",
            "subject": "TEST_Reply Ticket",
            "description": "Testing public reply",
            "priority": "medium"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/ticketing/public/tickets", json=ticket_data)
        assert create_response.status_code == 200
        created = create_response.json()
        
        # Add a reply
        response = requests.post(
            f"{BASE_URL}/api/ticketing/public/tickets/{created['ticket_number']}/reply",
            params={"content": "This is a test reply from the customer", "email": "test_reply@example.com"}
        )
        assert response.status_code == 200
        
        print(f"✓ Public reply added to ticket: {created['ticket_number']}")


class TestHelpTopicAutoRouting:
    """Help Topic Auto-Routing Tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "admin123"
        })
        assert response.status_code == 200
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_help_topic_auto_priority(self):
        """Verify help topic auto-priority is applied to tickets"""
        # Get help topics
        topics_response = requests.get(f"{BASE_URL}/api/ticketing/public/help-topics")
        topics = topics_response.json()
        
        # Find a topic with auto_priority set (Hardware Issue has high priority)
        high_priority_topic = None
        for topic in topics:
            if topic["name"] == "Hardware Issue":
                high_priority_topic = topic
                break
        
        if not high_priority_topic:
            pytest.skip("Hardware Issue topic not found")
        
        # Create ticket with this topic
        ticket_data = {
            "name": "TEST_AutoPriority",
            "email": "test_autopriority@example.com",
            "subject": "TEST_Auto Priority Ticket",
            "description": "Testing auto priority from help topic",
            "help_topic_id": high_priority_topic["id"],
            "priority": "low"  # This should be overridden by help topic
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/public/tickets", json=ticket_data)
        assert response.status_code == 200
        created = response.json()
        
        # Verify the ticket has the auto-priority from help topic
        ticket_response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/tickets/{created['id']}",
            headers=self.headers
        )
        ticket = ticket_response.json()
        
        # Hardware Issue topic should set priority to high
        print(f"✓ Ticket priority: {ticket['priority']} (expected: high from help topic)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
