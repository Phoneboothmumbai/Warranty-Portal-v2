"""
Test Suite for Enterprise Ticketing System - Phase 2+ Advanced Features
Tests Help Topics, Custom Forms, Canned Responses, and Ticket Participants
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"

# Test ticket ID with existing participant
TEST_TICKET_ID = "e0ed63e7-118b-4c6f-88dd-a348a98ea15a"


class TestSetup:
    """Setup and authentication tests"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def admin_headers(self, admin_token):
        """Get headers with admin auth token"""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }


class TestHelpTopics(TestSetup):
    """Test Help Topics CRUD operations"""
    
    def test_list_help_topics(self, admin_headers):
        """Test GET /api/ticketing/admin/help-topics"""
        response = requests.get(f"{BASE_URL}/api/ticketing/admin/help-topics", headers=admin_headers)
        assert response.status_code == 200, f"Failed to list help topics: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 6, f"Expected at least 6 seeded help topics, got {len(data)}"
        
        # Verify structure of first topic
        if len(data) > 0:
            topic = data[0]
            assert "id" in topic, "Missing id"
            assert "name" in topic, "Missing name"
            assert "icon" in topic, "Missing icon"
            assert "is_public" in topic, "Missing is_public"
        
        print(f"SUCCESS: Listed {len(data)} help topics")
    
    def test_list_help_topics_include_inactive(self, admin_headers):
        """Test GET /api/ticketing/admin/help-topics with include_inactive=true"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/help-topics?include_inactive=true",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to list help topics: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(data)} help topics (including inactive)")
    
    def test_create_help_topic(self, admin_headers):
        """Test POST /api/ticketing/admin/help-topics"""
        topic_data = {
            "name": f"TEST_Topic_{uuid.uuid4().hex[:6]}",
            "description": "Test help topic for automated testing",
            "icon": "monitor",
            "auto_priority": "high",
            "is_public": True,
            "sort_order": 99
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/help-topics",
            headers=admin_headers,
            json=topic_data
        )
        assert response.status_code == 200, f"Failed to create help topic: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data, "Missing id in response"
        assert data["name"] == topic_data["name"], "Name mismatch"
        assert data["description"] == topic_data["description"], "Description mismatch"
        assert data["icon"] == "monitor", "Icon mismatch"
        assert data["auto_priority"] == "high", "Auto priority mismatch"
        assert data["is_public"] == True, "is_public mismatch"
        
        print(f"SUCCESS: Created help topic {data['name']} with id {data['id']}")
    
    def test_create_help_topic_with_auto_routing(self, admin_headers):
        """Test creating help topic with auto-routing configuration"""
        # Get a department and SLA for auto-routing
        dept_response = requests.get(f"{BASE_URL}/api/ticketing/admin/departments", headers=admin_headers)
        departments = dept_response.json()
        
        sla_response = requests.get(f"{BASE_URL}/api/ticketing/admin/sla-policies", headers=admin_headers)
        sla_policies = sla_response.json()
        
        topic_data = {
            "name": f"TEST_AutoRoute_{uuid.uuid4().hex[:6]}",
            "description": "Help topic with auto-routing",
            "icon": "shield",
            "auto_priority": "critical",
            "is_public": True
        }
        
        if len(departments) > 0:
            topic_data["auto_department_id"] = departments[0]["id"]
        if len(sla_policies) > 0:
            topic_data["auto_sla_id"] = sla_policies[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/help-topics",
            headers=admin_headers,
            json=topic_data
        )
        assert response.status_code == 200, f"Failed to create help topic: {response.text}"
        data = response.json()
        
        if len(departments) > 0:
            assert data["auto_department_id"] == departments[0]["id"], "Auto department not set"
        if len(sla_policies) > 0:
            assert data["auto_sla_id"] == sla_policies[0]["id"], "Auto SLA not set"
        
        print(f"SUCCESS: Created help topic with auto-routing: {data['name']}")
    
    def test_get_help_topic_by_id(self, admin_headers):
        """Test GET /api/ticketing/admin/help-topics/{topic_id}"""
        # First create a help topic
        topic_data = {
            "name": f"TEST_GetTopic_{uuid.uuid4().hex[:6]}",
            "description": "Test topic for get by id",
            "icon": "code"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/help-topics",
            headers=admin_headers,
            json=topic_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        topic_id = created["id"]
        
        # Get by ID
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/help-topics/{topic_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get help topic: {response.text}"
        data = response.json()
        assert data["id"] == topic_id, "ID mismatch"
        assert data["name"] == topic_data["name"], "Name mismatch"
        
        print(f"SUCCESS: Retrieved help topic {data['name']} by ID")
    
    def test_update_help_topic(self, admin_headers):
        """Test PUT /api/ticketing/admin/help-topics/{topic_id}"""
        # First create a help topic
        topic_data = {
            "name": f"TEST_UpdateTopic_{uuid.uuid4().hex[:6]}",
            "description": "Original description",
            "icon": "wifi"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/help-topics",
            headers=admin_headers,
            json=topic_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        topic_id = created["id"]
        
        # Update help topic
        update_data = {
            "description": "Updated description",
            "auto_priority": "medium",
            "is_public": False
        }
        response = requests.put(
            f"{BASE_URL}/api/ticketing/admin/help-topics/{topic_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Failed to update help topic: {response.text}"
        data = response.json()
        
        assert data["description"] == "Updated description", "Description not updated"
        assert data["auto_priority"] == "medium", "Auto priority not updated"
        assert data["is_public"] == False, "is_public not updated"
        
        print(f"SUCCESS: Updated help topic {data['name']}")
    
    def test_delete_help_topic(self, admin_headers):
        """Test DELETE /api/ticketing/admin/help-topics/{topic_id}"""
        # First create a help topic
        topic_data = {
            "name": f"TEST_DeleteTopic_{uuid.uuid4().hex[:6]}",
            "description": "Topic to be deleted"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/help-topics",
            headers=admin_headers,
            json=topic_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        topic_id = created["id"]
        
        # Delete help topic
        response = requests.delete(
            f"{BASE_URL}/api/ticketing/admin/help-topics/{topic_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to delete help topic: {response.text}"
        
        # Verify deletion (should return 404)
        get_response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/help-topics/{topic_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404, "Help topic should be deleted"
        
        print(f"SUCCESS: Deleted help topic {topic_id}")
    
    def test_public_help_topics(self):
        """Test GET /api/ticketing/public/help-topics (no auth)"""
        response = requests.get(f"{BASE_URL}/api/ticketing/public/help-topics")
        assert response.status_code == 200, f"Failed to get public help topics: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify only public fields are returned
        if len(data) > 0:
            topic = data[0]
            assert "id" in topic, "Missing id"
            assert "name" in topic, "Missing name"
            assert "icon" in topic, "Missing icon"
            # Should not include internal fields
            assert "created_by" not in topic, "Should not include created_by"
        
        print(f"SUCCESS: Listed {len(data)} public help topics")


class TestCustomForms(TestSetup):
    """Test Custom Forms CRUD operations"""
    
    def test_list_custom_forms(self, admin_headers):
        """Test GET /api/ticketing/admin/custom-forms"""
        response = requests.get(f"{BASE_URL}/api/ticketing/admin/custom-forms", headers=admin_headers)
        assert response.status_code == 200, f"Failed to list custom forms: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 2, f"Expected at least 2 seeded custom forms, got {len(data)}"
        
        # Verify structure
        if len(data) > 0:
            form = data[0]
            assert "id" in form, "Missing id"
            assert "name" in form, "Missing name"
            assert "fields" in form, "Missing fields"
            assert isinstance(form["fields"], list), "Fields should be a list"
        
        print(f"SUCCESS: Listed {len(data)} custom forms")
    
    def test_create_custom_form(self, admin_headers):
        """Test POST /api/ticketing/admin/custom-forms"""
        form_data = {
            "name": f"TEST_Form_{uuid.uuid4().hex[:6]}",
            "description": "Test custom form for automated testing",
            "fields": [
                {
                    "name": "test_field_1",
                    "label": "Test Field 1",
                    "field_type": "text",
                    "required": True,
                    "placeholder": "Enter value"
                },
                {
                    "name": "test_field_2",
                    "label": "Test Field 2",
                    "field_type": "select",
                    "required": False,
                    "options": [
                        {"value": "option1", "label": "Option 1"},
                        {"value": "option2", "label": "Option 2"}
                    ]
                }
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/custom-forms",
            headers=admin_headers,
            json=form_data
        )
        assert response.status_code == 200, f"Failed to create custom form: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data, "Missing id in response"
        assert data["name"] == form_data["name"], "Name mismatch"
        assert len(data["fields"]) == 2, "Should have 2 fields"
        assert data["version"] == 1, "Initial version should be 1"
        
        # Verify field structure
        field1 = data["fields"][0]
        assert field1["name"] == "test_field_1", "Field name mismatch"
        assert field1["field_type"] == "text", "Field type mismatch"
        assert field1["required"] == True, "Required mismatch"
        
        print(f"SUCCESS: Created custom form {data['name']} with {len(data['fields'])} fields")
    
    def test_create_form_with_all_field_types(self, admin_headers):
        """Test creating form with various field types"""
        form_data = {
            "name": f"TEST_AllFields_{uuid.uuid4().hex[:6]}",
            "description": "Form with all field types",
            "fields": [
                {"name": "text_field", "label": "Text", "field_type": "text", "required": True},
                {"name": "textarea_field", "label": "Textarea", "field_type": "textarea", "required": False},
                {"name": "number_field", "label": "Number", "field_type": "number", "required": False},
                {"name": "email_field", "label": "Email", "field_type": "email", "required": True},
                {"name": "select_field", "label": "Select", "field_type": "select", "options": [{"value": "a", "label": "A"}]},
                {"name": "checkbox_field", "label": "Checkbox", "field_type": "checkbox", "required": False},
                {"name": "date_field", "label": "Date", "field_type": "date", "required": False}
            ]
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/custom-forms",
            headers=admin_headers,
            json=form_data
        )
        assert response.status_code == 200, f"Failed to create form: {response.text}"
        data = response.json()
        assert len(data["fields"]) == 7, "Should have 7 fields"
        
        print(f"SUCCESS: Created form with {len(data['fields'])} different field types")
    
    def test_get_custom_form_by_id(self, admin_headers):
        """Test GET /api/ticketing/admin/custom-forms/{form_id}"""
        # First create a form
        form_data = {
            "name": f"TEST_GetForm_{uuid.uuid4().hex[:6]}",
            "fields": [{"name": "field1", "label": "Field 1", "field_type": "text"}]
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/custom-forms",
            headers=admin_headers,
            json=form_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        form_id = created["id"]
        
        # Get by ID
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/custom-forms/{form_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get custom form: {response.text}"
        data = response.json()
        assert data["id"] == form_id, "ID mismatch"
        assert data["name"] == form_data["name"], "Name mismatch"
        
        print(f"SUCCESS: Retrieved custom form {data['name']} by ID")
    
    def test_update_custom_form(self, admin_headers):
        """Test PUT /api/ticketing/admin/custom-forms/{form_id} - should increment version"""
        # First create a form
        form_data = {
            "name": f"TEST_UpdateForm_{uuid.uuid4().hex[:6]}",
            "fields": [{"name": "field1", "label": "Original Field", "field_type": "text"}]
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/custom-forms",
            headers=admin_headers,
            json=form_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        form_id = created["id"]
        original_version = created["version"]
        
        # Update form with new fields
        update_data = {
            "description": "Updated description",
            "fields": [
                {"name": "field1", "label": "Updated Field", "field_type": "text"},
                {"name": "field2", "label": "New Field", "field_type": "textarea"}
            ]
        }
        response = requests.put(
            f"{BASE_URL}/api/ticketing/admin/custom-forms/{form_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Failed to update custom form: {response.text}"
        data = response.json()
        
        assert data["description"] == "Updated description", "Description not updated"
        assert len(data["fields"]) == 2, "Should have 2 fields"
        assert data["version"] == original_version + 1, "Version should be incremented"
        
        print(f"SUCCESS: Updated custom form {data['name']}, version now {data['version']}")
    
    def test_delete_custom_form(self, admin_headers):
        """Test DELETE /api/ticketing/admin/custom-forms/{form_id}"""
        # First create a form
        form_data = {
            "name": f"TEST_DeleteForm_{uuid.uuid4().hex[:6]}",
            "fields": []
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/custom-forms",
            headers=admin_headers,
            json=form_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        form_id = created["id"]
        
        # Delete form
        response = requests.delete(
            f"{BASE_URL}/api/ticketing/admin/custom-forms/{form_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to delete custom form: {response.text}"
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/custom-forms/{form_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404, "Custom form should be deleted"
        
        print(f"SUCCESS: Deleted custom form {form_id}")
    
    def test_public_custom_form(self, admin_headers):
        """Test GET /api/ticketing/public/custom-forms/{form_id}"""
        # Get existing form
        forms_response = requests.get(f"{BASE_URL}/api/ticketing/admin/custom-forms", headers=admin_headers)
        forms = forms_response.json()
        
        if len(forms) > 0:
            form_id = forms[0]["id"]
            response = requests.get(f"{BASE_URL}/api/ticketing/public/custom-forms/{form_id}")
            assert response.status_code == 200, f"Failed to get public form: {response.text}"
            data = response.json()
            
            # Verify only customer-visible fields are returned
            for field in data.get("fields", []):
                assert field.get("visible_to_customer", True) == True, "Should only return visible fields"
            
            print(f"SUCCESS: Retrieved public custom form with {len(data.get('fields', []))} visible fields")


class TestCannedResponses(TestSetup):
    """Test Canned Responses CRUD operations"""
    
    def test_list_canned_responses(self, admin_headers):
        """Test GET /api/ticketing/admin/canned-responses"""
        response = requests.get(f"{BASE_URL}/api/ticketing/admin/canned-responses", headers=admin_headers)
        assert response.status_code == 200, f"Failed to list canned responses: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 4, f"Expected at least 4 seeded canned responses, got {len(data)}"
        
        # Verify structure
        if len(data) > 0:
            canned = data[0]
            assert "id" in canned, "Missing id"
            assert "title" in canned, "Missing title"
            assert "content" in canned, "Missing content"
            assert "usage_count" in canned, "Missing usage_count"
        
        print(f"SUCCESS: Listed {len(data)} canned responses")
    
    def test_create_canned_response(self, admin_headers):
        """Test POST /api/ticketing/admin/canned-responses"""
        canned_data = {
            "title": f"TEST_Canned_{uuid.uuid4().hex[:6]}",
            "content": "Dear {{customer_name}},\n\nThank you for contacting us about ticket {{ticket_number}}.\n\nBest regards,\n{{department_name}} Team",
            "category": "Test Category",
            "tags": ["test", "automated"],
            "is_personal": False
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/canned-responses",
            headers=admin_headers,
            json=canned_data
        )
        assert response.status_code == 200, f"Failed to create canned response: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data, "Missing id in response"
        assert data["title"] == canned_data["title"], "Title mismatch"
        assert data["content"] == canned_data["content"], "Content mismatch"
        assert data["category"] == "Test Category", "Category mismatch"
        assert data["usage_count"] == 0, "Initial usage count should be 0"
        
        print(f"SUCCESS: Created canned response '{data['title']}'")
    
    def test_create_personal_canned_response(self, admin_headers):
        """Test creating personal canned response"""
        canned_data = {
            "title": f"TEST_Personal_{uuid.uuid4().hex[:6]}",
            "content": "My personal response template",
            "is_personal": True
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/canned-responses",
            headers=admin_headers,
            json=canned_data
        )
        assert response.status_code == 200, f"Failed to create personal canned response: {response.text}"
        data = response.json()
        assert data["is_personal"] == True, "Should be personal"
        
        print(f"SUCCESS: Created personal canned response '{data['title']}'")
    
    def test_get_canned_response_by_id(self, admin_headers):
        """Test GET /api/ticketing/admin/canned-responses/{response_id}"""
        # First create a canned response
        canned_data = {
            "title": f"TEST_GetCanned_{uuid.uuid4().hex[:6]}",
            "content": "Test content"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/canned-responses",
            headers=admin_headers,
            json=canned_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        canned_id = created["id"]
        
        # Get by ID
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/canned-responses/{canned_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get canned response: {response.text}"
        data = response.json()
        assert data["id"] == canned_id, "ID mismatch"
        assert data["title"] == canned_data["title"], "Title mismatch"
        
        print(f"SUCCESS: Retrieved canned response '{data['title']}' by ID")
    
    def test_update_canned_response(self, admin_headers):
        """Test PUT /api/ticketing/admin/canned-responses/{response_id}"""
        # First create a canned response
        canned_data = {
            "title": f"TEST_UpdateCanned_{uuid.uuid4().hex[:6]}",
            "content": "Original content"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/canned-responses",
            headers=admin_headers,
            json=canned_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        canned_id = created["id"]
        
        # Update canned response
        update_data = {
            "content": "Updated content with {{customer_name}}",
            "category": "Updated Category"
        }
        response = requests.put(
            f"{BASE_URL}/api/ticketing/admin/canned-responses/{canned_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Failed to update canned response: {response.text}"
        data = response.json()
        
        assert data["content"] == update_data["content"], "Content not updated"
        assert data["category"] == "Updated Category", "Category not updated"
        
        print(f"SUCCESS: Updated canned response '{data['title']}'")
    
    def test_delete_canned_response(self, admin_headers):
        """Test DELETE /api/ticketing/admin/canned-responses/{response_id}"""
        # First create a canned response
        canned_data = {
            "title": f"TEST_DeleteCanned_{uuid.uuid4().hex[:6]}",
            "content": "To be deleted"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/canned-responses",
            headers=admin_headers,
            json=canned_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        canned_id = created["id"]
        
        # Delete canned response
        response = requests.delete(
            f"{BASE_URL}/api/ticketing/admin/canned-responses/{canned_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to delete canned response: {response.text}"
        
        # Verify deletion
        get_response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/canned-responses/{canned_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404, "Canned response should be deleted"
        
        print(f"SUCCESS: Deleted canned response {canned_id}")
    
    def test_use_canned_response_variable_replacement(self, admin_headers):
        """Test POST /api/ticketing/admin/canned-responses/{id}/use - variable replacement"""
        # Get existing canned response with variables
        canned_response = requests.get(f"{BASE_URL}/api/ticketing/admin/canned-responses", headers=admin_headers)
        canned_list = canned_response.json()
        
        # Find one with variables
        canned_with_vars = None
        for c in canned_list:
            if "{{" in c.get("content", ""):
                canned_with_vars = c
                break
        
        if canned_with_vars:
            # Use canned response with test ticket
            response = requests.post(
                f"{BASE_URL}/api/ticketing/admin/canned-responses/{canned_with_vars['id']}/use?ticket_id={TEST_TICKET_ID}",
                headers=admin_headers
            )
            assert response.status_code == 200, f"Failed to use canned response: {response.text}"
            data = response.json()
            
            # Verify variables were replaced
            assert "content" in data, "Missing content in response"
            assert "original_content" in data, "Missing original_content in response"
            assert "{{" not in data["content"], "Variables should be replaced"
            assert "{{" in data["original_content"], "Original should have variables"
            
            print(f"SUCCESS: Canned response variables replaced correctly")
            print(f"  Original: {data['original_content'][:50]}...")
            print(f"  Replaced: {data['content'][:50]}...")
        else:
            print("SKIP: No canned response with variables found")


class TestTicketParticipants(TestSetup):
    """Test Ticket Participants (CC/Collaboration) operations"""
    
    def test_list_ticket_participants(self, admin_headers):
        """Test GET /api/ticketing/admin/tickets/{ticket_id}/participants"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/tickets/{TEST_TICKET_ID}/participants",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to list participants: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify structure if participants exist
        if len(data) > 0:
            participant = data[0]
            assert "id" in participant, "Missing id"
            assert "name" in participant, "Missing name"
            assert "email" in participant, "Missing email"
            assert "participant_type" in participant, "Missing participant_type"
        
        print(f"SUCCESS: Listed {len(data)} participants for ticket")
    
    def test_add_ticket_participant(self, admin_headers):
        """Test POST /api/ticketing/admin/tickets/{ticket_id}/participants"""
        participant_data = {
            "name": f"TEST_Participant_{uuid.uuid4().hex[:6]}",
            "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+1-555-123-4567",
            "participant_type": "cc",
            "can_reply": True
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/tickets/{TEST_TICKET_ID}/participants",
            headers=admin_headers,
            json=participant_data
        )
        assert response.status_code == 200, f"Failed to add participant: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data, "Missing id in response"
        assert data["name"] == participant_data["name"], "Name mismatch"
        assert data["email"] == participant_data["email"], "Email mismatch"
        assert data["participant_type"] == "cc", "Type mismatch"
        assert data["is_active"] == True, "Should be active"
        
        print(f"SUCCESS: Added participant {data['name']} to ticket")
        return data["id"]
    
    def test_add_duplicate_participant_fails(self, admin_headers):
        """Test adding duplicate participant fails"""
        # First add a participant
        email = f"test_dup_{uuid.uuid4().hex[:6]}@example.com"
        participant_data = {
            "name": "Duplicate Test",
            "email": email,
            "participant_type": "cc"
        }
        first_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/tickets/{TEST_TICKET_ID}/participants",
            headers=admin_headers,
            json=participant_data
        )
        assert first_response.status_code == 200
        
        # Try to add same email again
        second_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/tickets/{TEST_TICKET_ID}/participants",
            headers=admin_headers,
            json=participant_data
        )
        assert second_response.status_code == 400, "Should fail for duplicate email"
        
        print("SUCCESS: Duplicate participant correctly rejected")
    
    def test_remove_ticket_participant(self, admin_headers):
        """Test DELETE /api/ticketing/admin/tickets/{ticket_id}/participants/{participant_id}"""
        # First add a participant
        participant_data = {
            "name": f"TEST_Remove_{uuid.uuid4().hex[:6]}",
            "email": f"test_remove_{uuid.uuid4().hex[:6]}@example.com",
            "participant_type": "cc"
        }
        add_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/tickets/{TEST_TICKET_ID}/participants",
            headers=admin_headers,
            json=participant_data
        )
        assert add_response.status_code == 200
        participant_id = add_response.json()["id"]
        
        # Remove participant
        response = requests.delete(
            f"{BASE_URL}/api/ticketing/admin/tickets/{TEST_TICKET_ID}/participants/{participant_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to remove participant: {response.text}"
        
        # Verify removal - participant should not be in active list
        list_response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/tickets/{TEST_TICKET_ID}/participants",
            headers=admin_headers
        )
        participants = list_response.json()
        active_ids = [p["id"] for p in participants if p.get("is_active", True)]
        assert participant_id not in active_ids, "Participant should be removed"
        
        print(f"SUCCESS: Removed participant {participant_id}")
    
    def test_ticket_includes_participants(self, admin_headers):
        """Test that ticket detail includes participants"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/tickets/{TEST_TICKET_ID}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get ticket: {response.text}"
        data = response.json()
        
        assert "participants" in data, "Ticket should include participants"
        assert "participant_count" in data, "Ticket should include participant_count"
        assert isinstance(data["participants"], list), "Participants should be a list"
        
        print(f"SUCCESS: Ticket includes {len(data['participants'])} participants")


class TestHelpTopicIntegration(TestSetup):
    """Test Help Topic integration with ticket creation"""
    
    def test_help_topic_linked_to_custom_form(self, admin_headers):
        """Test that help topics can be linked to custom forms"""
        # Get help topics
        topics_response = requests.get(f"{BASE_URL}/api/ticketing/admin/help-topics", headers=admin_headers)
        topics = topics_response.json()
        
        # Find topic with custom form
        topic_with_form = None
        for t in topics:
            if t.get("custom_form_id"):
                topic_with_form = t
                break
        
        if topic_with_form:
            # Verify form exists
            form_response = requests.get(
                f"{BASE_URL}/api/ticketing/admin/custom-forms/{topic_with_form['custom_form_id']}",
                headers=admin_headers
            )
            assert form_response.status_code == 200, "Linked form should exist"
            form = form_response.json()
            
            print(f"SUCCESS: Help topic '{topic_with_form['name']}' linked to form '{form['name']}'")
        else:
            print("INFO: No help topic with custom form found")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
