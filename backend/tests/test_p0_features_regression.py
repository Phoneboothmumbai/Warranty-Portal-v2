"""
P0 Features Regression Tests - Iteration 59
Tests for:
1. Engineer Workflow Sync (workflow progress bar, stage transitions)
2. Customer Quotation Approval via Email (send email, public approval)
3. Help Topic → Form Linking (all 43 topics have form_id)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://service-hub-522.preview.emergentagent.com')
BASE_URL = BASE_URL.rstrip('/')

# Test Credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"
ENGINEER_EMAIL = "test_engineer_1bfa72f0@test.com"
ENGINEER_PASSWORD = "Test@123"

# Test Data
TEST_TICKET_WITH_WORKFLOW = "f97314a0-322d-48a0-a179-dc0a1693117a"
TEST_TICKET_FOR_QUOTATION = "c028d748-3bac-4b7e-a6b1-32310d8ec7f8"


class TestAdminAuth:
    """Admin authentication tests"""
    
    def test_admin_login_success(self):
        """Admin can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print(f"✓ Admin login successful, token obtained")


class TestEngineerAuth:
    """Engineer authentication tests"""
    
    def test_engineer_login_success(self):
        """Engineer can login successfully"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/auth/login",
            json={"email": ENGINEER_EMAIL, "password": ENGINEER_PASSWORD}
        )
        assert response.status_code == 200, f"Engineer login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "engineer" in data
        assert data["engineer"]["email"] == ENGINEER_EMAIL
        print(f"✓ Engineer login successful: {data['engineer']['name']}")


class TestEngineerWorkflowSync:
    """Engineer Workflow Progress Bar & Stage Transitions tests"""
    
    @pytest.fixture
    def engineer_token(self):
        response = requests.post(
            f"{BASE_URL}/api/engineer/auth/login",
            json={"email": ENGINEER_EMAIL, "password": ENGINEER_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_engineer_ticket_workflow_endpoint(self, engineer_token):
        """GET /api/engineer/ticket/{ticket_id}/workflow returns workflow data"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/ticket/{TEST_TICKET_WITH_WORKFLOW}/workflow",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200, f"Workflow fetch failed: {response.text}"
        data = response.json()
        
        # Verify workflow structure
        assert "workflow_name" in data, "Missing workflow_name"
        assert "stages" in data, "Missing stages"
        assert "current_stage_id" in data, "Missing current_stage_id"
        assert "current_stage_name" in data, "Missing current_stage_name"
        assert "transitions" in data, "Missing transitions"
        
        # Verify stages structure
        assert len(data["stages"]) > 0, "No stages found"
        print(f"✓ Workflow '{data['workflow_name']}' has {len(data['stages'])} stages")
        print(f"  Current stage: {data['current_stage_name']}")
        print(f"  Available transitions: {len(data['transitions'])}")
        
        # Verify each stage has required fields
        for stage in data["stages"]:
            assert "id" in stage
            assert "name" in stage
            assert "stage_type" in stage
            assert "order" in stage
    
    def test_workflow_has_correct_stages_for_onsite_support(self, engineer_token):
        """Verify On-Site Technical Support workflow has expected stages"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/ticket/{TEST_TICKET_WITH_WORKFLOW}/workflow",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Expected stages for On-Site Technical Support
        expected_stages = [
            "New", "Assigned", "Visit Scheduled", "Diagnosed",
            "Fixed On-Site", "Parts Required", "Quote Sent", "Quote Approved",
            "Parts Ordered", "Parts Received", "Installation Scheduled", "Closed", "Cancelled"
        ]
        
        actual_stages = [s["name"] for s in data["stages"]]
        
        # Verify all expected stages exist
        for expected in expected_stages:
            assert expected in actual_stages, f"Missing stage: {expected}"
        
        print(f"✓ All {len(expected_stages)} expected stages present")
    
    def test_workflow_transitions_available(self, engineer_token):
        """Verify transitions are correctly returned"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/ticket/{TEST_TICKET_WITH_WORKFLOW}/workflow",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Transitions should have required fields
        for transition in data["transitions"]:
            assert "id" in transition
            assert "label" in transition
            assert "to_stage_id" in transition
            assert "to_stage_name" in transition
        
        print(f"✓ {len(data['transitions'])} valid transitions available")


class TestQuotationApprovalEmail:
    """Customer Quotation Approval via Email tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_send_quotation_email_endpoint(self, admin_token):
        """POST /api/ticketing/tickets/{ticket_id}/send-quotation-email works"""
        response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{TEST_TICKET_FOR_QUOTATION}/send-quotation-email",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "customer_email": "test_regression@example.com",
                "customer_name": "Regression Test",
                "quotation_details": "Regression test quotation"
            }
        )
        assert response.status_code == 200, f"Send quotation failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert data.get("success") == True, "success should be True"
        assert "approval_token" in data, "Missing approval_token"
        assert "approve_url" in data, "Missing approve_url"
        assert "reject_url" in data, "Missing reject_url"
        assert "customer_email" in data, "Missing customer_email"
        
        # Verify URLs contain the token
        assert data["approval_token"] in data["approve_url"]
        assert data["approval_token"] in data["reject_url"]
        
        print(f"✓ Quotation email sent, token: {data['approval_token'][:20]}...")
        print(f"  Email sent: {data.get('email_sent', False)} (SMTP may not be configured)")
        
        return data["approval_token"]
    
    def test_quotation_public_approval_endpoint(self, admin_token):
        """GET /api/ticketing/quotation-response/{token}?action=approve works"""
        # First create a new token
        send_response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{TEST_TICKET_FOR_QUOTATION}/send-quotation-email",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "customer_email": "approval_test@example.com",
                "customer_name": "Approval Test"
            }
        )
        assert send_response.status_code == 200
        token = send_response.json()["approval_token"]
        
        # Now test the public approval endpoint
        response = requests.get(
            f"{BASE_URL}/api/ticketing/quotation-response/{token}",
            params={"action": "approve"}
        )
        assert response.status_code == 200, f"Approval failed: {response.text}"
        
        # Response should be HTML
        assert "Quotation Approved" in response.text
        print("✓ Public quotation approval endpoint works")
    
    def test_quotation_public_rejection_endpoint(self, admin_token):
        """GET /api/ticketing/quotation-response/{token}?action=reject works"""
        # Create a new token
        send_response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{TEST_TICKET_FOR_QUOTATION}/send-quotation-email",
            headers={
                "Authorization": f"Bearer {admin_token}",
                "Content-Type": "application/json"
            },
            json={
                "customer_email": "reject_test@example.com",
                "customer_name": "Reject Test"
            }
        )
        assert send_response.status_code == 200
        token = send_response.json()["approval_token"]
        
        # Test rejection
        response = requests.get(
            f"{BASE_URL}/api/ticketing/quotation-response/{token}",
            params={"action": "reject"}
        )
        assert response.status_code == 200
        assert "Quotation Rejected" in response.text
        print("✓ Public quotation rejection endpoint works")
    
    def test_quotation_invalid_token(self):
        """Invalid token returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/quotation-response/invalid-token-12345",
            params={"action": "approve"}
        )
        assert response.status_code == 404
        assert "Invalid or Expired Link" in response.text
        print("✓ Invalid token correctly returns 404")
    
    def test_quotation_already_responded(self, admin_token):
        """Already responded token returns appropriate message"""
        # The existing used token
        token = "85c02323-c34f-4bef-a709-255946bb9980"
        response = requests.get(
            f"{BASE_URL}/api/ticketing/quotation-response/{token}",
            params={"action": "approve"}
        )
        # Should return 200 with "Already Responded" message
        assert "Already Responded" in response.text
        print("✓ Already responded token handled correctly")


class TestHelpTopicFormLinking:
    """Help Topic → Form Linking tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_all_help_topics_have_form_id(self, admin_token):
        """All 43 help topics should have form_id linked"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/help-topics",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Failed to fetch help topics: {response.text}"
        topics = response.json()
        
        # Verify we have 43 topics
        assert len(topics) >= 43, f"Expected 43+ topics, got {len(topics)}"
        
        # Verify each topic has form_id
        topics_without_form = []
        for topic in topics:
            if not topic.get("form_id"):
                topics_without_form.append(topic.get("name", "Unknown"))
        
        assert len(topics_without_form) == 0, f"Topics without form_id: {topics_without_form}"
        print(f"✓ All {len(topics)} help topics have form_id linked")
    
    def test_help_topic_detail_includes_form(self, admin_token):
        """Help topic detail endpoint returns linked form with fields"""
        # First get a topic ID
        response = requests.get(
            f"{BASE_URL}/api/ticketing/help-topics?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        topics = response.json()
        assert len(topics) > 0
        topic_id = topics[0]["id"]
        topic_name = topics[0]["name"]
        
        # Get topic detail
        detail_response = requests.get(
            f"{BASE_URL}/api/ticketing/help-topics/{topic_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert detail_response.status_code == 200, f"Failed to fetch topic detail: {detail_response.text}"
        detail = detail_response.json()
        
        # Verify form is included
        assert "form" in detail, "Missing form in topic detail"
        assert detail["form"] is not None, "Form should not be None"
        
        form = detail["form"]
        assert "id" in form, "Form missing id"
        assert "name" in form, "Form missing name"
        assert "fields" in form, "Form missing fields"
        
        print(f"✓ Topic '{topic_name}' has form '{form['name']}' with {len(form.get('fields', []))} fields")


class TestAdminTicketDashboard:
    """Admin Ticket Dashboard tests"""
    
    @pytest.fixture
    def admin_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        return response.json()["access_token"]
    
    def test_tickets_list_endpoint(self, admin_token):
        """GET /api/ticketing/tickets returns ticket list with filters"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 20}
        )
        assert response.status_code == 200, f"Failed to fetch tickets: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "tickets" in data, "Missing tickets array"
        assert "total" in data, "Missing total count"
        
        print(f"✓ Tickets endpoint returns {len(data['tickets'])} tickets (total: {data['total']})")
    
    def test_tickets_filter_by_stage(self, admin_token):
        """Tickets can be filtered by stage"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"stage": "New", "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned tickets should be in "New" stage
        for ticket in data.get("tickets", []):
            assert ticket.get("current_stage_name") == "New", f"Ticket {ticket.get('ticket_number')} not in New stage"
        
        print(f"✓ Stage filter works: {len(data.get('tickets', []))} tickets in 'New' stage")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
