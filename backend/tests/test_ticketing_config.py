"""
Ticketing Configuration API Tests
Tests for: Canned Responses, SLA Policies, Departments, Custom Forms
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTicketingConfigAPIs:
    """Test suite for Ticketing Configuration APIs"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "ck@motta.in", "password": "Charu@123@"}
        )
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        token = login_response.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Store created IDs for cleanup
        self.created_canned_ids = []
        self.created_sla_ids = []
        self.created_dept_ids = []
        self.created_form_ids = []
        
        yield
        
        # Cleanup created test data
        for canned_id in self.created_canned_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/admin/ticketing-config/canned-responses/{canned_id}")
            except:
                pass
        for sla_id in self.created_sla_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/admin/ticketing-config/sla-policies/{sla_id}")
            except:
                pass
        for dept_id in self.created_dept_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/admin/ticketing-config/departments/{dept_id}")
            except:
                pass
        for form_id in self.created_form_ids:
            try:
                self.session.delete(f"{BASE_URL}/api/admin/ticketing-config/custom-forms/{form_id}")
            except:
                pass

    # ==================== CANNED RESPONSES TESTS ====================
    
    def test_list_canned_responses(self):
        """Test listing canned responses"""
        response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/canned-responses")
        assert response.status_code == 200
        data = response.json()
        assert "responses" in data
        assert "categories" in data
        assert isinstance(data["responses"], list)
        print(f"✓ List canned responses: {len(data['responses'])} responses found")
    
    def test_create_canned_response(self):
        """Test creating a canned response"""
        payload = {
            "title": f"TEST_Canned_{uuid.uuid4().hex[:8]}",
            "category": "Test Category",
            "content": "Hello {{customer_name}}, your ticket {{ticket_number}} has been received.",
            "is_personal": False,
            "is_active": True
        }
        response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/canned-responses",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Canned response created"
        self.created_canned_ids.append(data["id"])
        print(f"✓ Create canned response: {data['id']}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/canned-responses/{data['id']}")
        assert get_response.status_code == 200
        canned = get_response.json()
        assert canned["title"] == payload["title"]
        assert canned["content"] == payload["content"]
        assert canned["category"] == payload["category"]
        print(f"✓ Verified canned response data persisted correctly")
    
    def test_update_canned_response(self):
        """Test updating a canned response"""
        # Create first
        create_payload = {
            "title": f"TEST_Update_{uuid.uuid4().hex[:8]}",
            "category": "Original",
            "content": "Original content",
            "is_active": True
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/canned-responses",
            json=create_payload
        )
        assert create_response.status_code == 200
        canned_id = create_response.json()["id"]
        self.created_canned_ids.append(canned_id)
        
        # Update
        update_payload = {
            "title": "Updated Title",
            "content": "Updated content with {{ticket_number}}"
        }
        update_response = self.session.put(
            f"{BASE_URL}/api/admin/ticketing-config/canned-responses/{canned_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        assert update_response.json()["message"] == "Canned response updated"
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/canned-responses/{canned_id}")
        assert get_response.status_code == 200
        canned = get_response.json()
        assert canned["title"] == "Updated Title"
        assert canned["content"] == "Updated content with {{ticket_number}}"
        print(f"✓ Update canned response verified")
    
    def test_delete_canned_response(self):
        """Test deleting a canned response"""
        # Create first
        create_payload = {
            "title": f"TEST_Delete_{uuid.uuid4().hex[:8]}",
            "content": "To be deleted"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/canned-responses",
            json=create_payload
        )
        assert create_response.status_code == 200
        canned_id = create_response.json()["id"]
        
        # Delete
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/ticketing-config/canned-responses/{canned_id}")
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/canned-responses/{canned_id}")
        assert get_response.status_code == 404
        print(f"✓ Delete canned response verified")

    # ==================== SLA POLICIES TESTS ====================
    
    def test_list_sla_policies(self):
        """Test listing SLA policies"""
        response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/sla-policies")
        assert response.status_code == 200
        data = response.json()
        assert "policies" in data
        assert isinstance(data["policies"], list)
        print(f"✓ List SLA policies: {len(data['policies'])} policies found")
    
    def test_create_sla_policy(self):
        """Test creating an SLA policy"""
        payload = {
            "name": f"TEST_SLA_{uuid.uuid4().hex[:8]}",
            "description": "Test SLA policy",
            "response_time_hours": 2,
            "resolution_time_hours": 8,
            "response_time_business_hours": True,
            "resolution_time_business_hours": True,
            "escalation_enabled": True,
            "escalation_after_hours": 1,
            "is_active": True,
            "is_default": False
        }
        response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/sla-policies",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "SLA policy created"
        self.created_sla_ids.append(data["id"])
        print(f"✓ Create SLA policy: {data['id']}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/sla-policies/{data['id']}")
        assert get_response.status_code == 200
        sla = get_response.json()
        assert sla["name"] == payload["name"]
        assert sla["response_time_hours"] == payload["response_time_hours"]
        assert sla["resolution_time_hours"] == payload["resolution_time_hours"]
        print(f"✓ Verified SLA policy data persisted correctly")
    
    def test_update_sla_policy(self):
        """Test updating an SLA policy"""
        # Create first
        create_payload = {
            "name": f"TEST_SLA_Update_{uuid.uuid4().hex[:8]}",
            "response_time_hours": 4,
            "resolution_time_hours": 24,
            "is_active": True
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/sla-policies",
            json=create_payload
        )
        assert create_response.status_code == 200
        sla_id = create_response.json()["id"]
        self.created_sla_ids.append(sla_id)
        
        # Update
        update_payload = {
            "name": "Updated SLA Name",
            "response_time_hours": 1,
            "resolution_time_hours": 4
        }
        update_response = self.session.put(
            f"{BASE_URL}/api/admin/ticketing-config/sla-policies/{sla_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/sla-policies/{sla_id}")
        assert get_response.status_code == 200
        sla = get_response.json()
        assert sla["name"] == "Updated SLA Name"
        assert sla["response_time_hours"] == 1
        assert sla["resolution_time_hours"] == 4
        print(f"✓ Update SLA policy verified")
    
    def test_delete_sla_policy(self):
        """Test deleting an SLA policy"""
        # Create first
        create_payload = {
            "name": f"TEST_SLA_Delete_{uuid.uuid4().hex[:8]}",
            "response_time_hours": 4,
            "resolution_time_hours": 24
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/sla-policies",
            json=create_payload
        )
        assert create_response.status_code == 200
        sla_id = create_response.json()["id"]
        
        # Delete
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/ticketing-config/sla-policies/{sla_id}")
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/sla-policies/{sla_id}")
        assert get_response.status_code == 404
        print(f"✓ Delete SLA policy verified")

    # ==================== DEPARTMENTS TESTS ====================
    
    def test_list_departments(self):
        """Test listing departments"""
        response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/departments")
        assert response.status_code == 200
        data = response.json()
        assert "departments" in data
        assert isinstance(data["departments"], list)
        print(f"✓ List departments: {len(data['departments'])} departments found")
    
    def test_create_department(self):
        """Test creating a department"""
        payload = {
            "name": f"TEST_Dept_{uuid.uuid4().hex[:8]}",
            "description": "Test department",
            "email": "test@example.com",
            "is_active": True,
            "is_public": True
        }
        response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/departments",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Department created"
        self.created_dept_ids.append(data["id"])
        print(f"✓ Create department: {data['id']}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/departments/{data['id']}")
        assert get_response.status_code == 200
        dept = get_response.json()
        assert dept["name"] == payload["name"]
        assert dept["description"] == payload["description"]
        assert dept["email"] == payload["email"]
        print(f"✓ Verified department data persisted correctly")
    
    def test_update_department(self):
        """Test updating a department"""
        # Create first
        create_payload = {
            "name": f"TEST_Dept_Update_{uuid.uuid4().hex[:8]}",
            "description": "Original description",
            "is_active": True
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/departments",
            json=create_payload
        )
        assert create_response.status_code == 200
        dept_id = create_response.json()["id"]
        self.created_dept_ids.append(dept_id)
        
        # Update
        update_payload = {
            "name": "Updated Department Name",
            "description": "Updated description"
        }
        update_response = self.session.put(
            f"{BASE_URL}/api/admin/ticketing-config/departments/{dept_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/departments/{dept_id}")
        assert get_response.status_code == 200
        dept = get_response.json()
        assert dept["name"] == "Updated Department Name"
        assert dept["description"] == "Updated description"
        print(f"✓ Update department verified")
    
    def test_delete_department(self):
        """Test deleting a department"""
        # Create first
        create_payload = {
            "name": f"TEST_Dept_Delete_{uuid.uuid4().hex[:8]}",
            "description": "To be deleted"
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/departments",
            json=create_payload
        )
        assert create_response.status_code == 200
        dept_id = create_response.json()["id"]
        
        # Delete
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/ticketing-config/departments/{dept_id}")
        assert delete_response.status_code == 200
        
        # Verify deleted - list should not contain it
        list_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/departments")
        assert list_response.status_code == 200
        depts = list_response.json()["departments"]
        assert not any(d["id"] == dept_id for d in depts)
        print(f"✓ Delete department verified")

    # ==================== CUSTOM FORMS TESTS ====================
    
    def test_list_custom_forms(self):
        """Test listing custom forms"""
        response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/custom-forms")
        assert response.status_code == 200
        data = response.json()
        assert "forms" in data
        assert isinstance(data["forms"], list)
        print(f"✓ List custom forms: {len(data['forms'])} forms found")
    
    def test_create_custom_form(self):
        """Test creating a custom form"""
        payload = {
            "name": f"TEST_Form_{uuid.uuid4().hex[:8]}",
            "description": "Test custom form",
            "form_type": "ticket",
            "fields": [
                {
                    "field_type": "text",
                    "label": "Serial Number",
                    "placeholder": "Enter serial number",
                    "validation": {"required": True}
                },
                {
                    "field_type": "select",
                    "label": "Issue Type",
                    "options": [
                        {"label": "Hardware", "value": "hardware"},
                        {"label": "Software", "value": "software"}
                    ],
                    "validation": {"required": True}
                }
            ],
            "is_active": True
        }
        response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/custom-forms",
            json=payload
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["message"] == "Custom form created"
        self.created_form_ids.append(data["id"])
        print(f"✓ Create custom form: {data['id']}")
        
        # Verify by GET
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/custom-forms/{data['id']}")
        assert get_response.status_code == 200
        form = get_response.json()
        assert form["name"] == payload["name"]
        assert form["form_type"] == payload["form_type"]
        assert len(form["fields"]) == 2
        print(f"✓ Verified custom form data persisted correctly")
    
    def test_update_custom_form(self):
        """Test updating a custom form"""
        # Create first
        create_payload = {
            "name": f"TEST_Form_Update_{uuid.uuid4().hex[:8]}",
            "form_type": "ticket",
            "fields": [{"field_type": "text", "label": "Original Field"}],
            "is_active": True
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/custom-forms",
            json=create_payload
        )
        assert create_response.status_code == 200
        form_id = create_response.json()["id"]
        self.created_form_ids.append(form_id)
        
        # Update
        update_payload = {
            "name": "Updated Form Name",
            "fields": [
                {"field_type": "text", "label": "Updated Field"},
                {"field_type": "number", "label": "New Number Field"}
            ]
        }
        update_response = self.session.put(
            f"{BASE_URL}/api/admin/ticketing-config/custom-forms/{form_id}",
            json=update_payload
        )
        assert update_response.status_code == 200
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/custom-forms/{form_id}")
        assert get_response.status_code == 200
        form = get_response.json()
        assert form["name"] == "Updated Form Name"
        assert len(form["fields"]) == 2
        print(f"✓ Update custom form verified")
    
    def test_delete_custom_form(self):
        """Test deleting a custom form"""
        # Create first
        create_payload = {
            "name": f"TEST_Form_Delete_{uuid.uuid4().hex[:8]}",
            "form_type": "ticket",
            "fields": []
        }
        create_response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/custom-forms",
            json=create_payload
        )
        assert create_response.status_code == 200
        form_id = create_response.json()["id"]
        
        # Delete
        delete_response = self.session.delete(f"{BASE_URL}/api/admin/ticketing-config/custom-forms/{form_id}")
        assert delete_response.status_code == 200
        
        # Verify deleted
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/custom-forms/{form_id}")
        assert get_response.status_code == 404
        print(f"✓ Delete custom form verified")

    # ==================== SEED DEFAULTS TESTS ====================
    
    def test_seed_sla_defaults_idempotent(self):
        """Test that seeding SLA defaults is idempotent"""
        # First call
        response1 = self.session.post(f"{BASE_URL}/api/admin/ticketing-config/sla-policies/seed-defaults")
        assert response1.status_code == 200
        
        # Second call should return "already exist"
        response2 = self.session.post(f"{BASE_URL}/api/admin/ticketing-config/sla-policies/seed-defaults")
        assert response2.status_code == 200
        data = response2.json()
        assert "already exist" in data.get("message", "").lower() or "count" in data
        print(f"✓ SLA seed defaults is idempotent")
    
    def test_seed_departments_defaults_idempotent(self):
        """Test that seeding department defaults is idempotent"""
        # First call
        response1 = self.session.post(f"{BASE_URL}/api/admin/ticketing-config/departments/seed-defaults")
        assert response1.status_code == 200
        
        # Second call should return "already exist"
        response2 = self.session.post(f"{BASE_URL}/api/admin/ticketing-config/departments/seed-defaults")
        assert response2.status_code == 200
        data = response2.json()
        assert "already exist" in data.get("message", "").lower() or "count" in data
        print(f"✓ Departments seed defaults is idempotent")

    # ==================== EDGE CASES ====================
    
    def test_canned_response_with_variables(self):
        """Test canned response with template variables"""
        payload = {
            "title": f"TEST_Variables_{uuid.uuid4().hex[:8]}",
            "content": "Dear {{customer_name}}, Ticket #{{ticket_number}} for {{subject}} has been updated. Status: {{status}}",
            "is_active": True
        }
        response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/canned-responses",
            json=payload
        )
        assert response.status_code == 200
        canned_id = response.json()["id"]
        self.created_canned_ids.append(canned_id)
        
        # Verify content preserved
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/canned-responses/{canned_id}")
        assert get_response.status_code == 200
        assert "{{customer_name}}" in get_response.json()["content"]
        assert "{{ticket_number}}" in get_response.json()["content"]
        print(f"✓ Canned response with variables preserved correctly")
    
    def test_sla_policy_with_priority_multipliers(self):
        """Test SLA policy with priority multipliers"""
        payload = {
            "name": f"TEST_SLA_Multipliers_{uuid.uuid4().hex[:8]}",
            "response_time_hours": 4,
            "resolution_time_hours": 24,
            "priority_multipliers": {
                "critical": 0.25,
                "high": 0.5,
                "medium": 1,
                "low": 2
            },
            "is_active": True
        }
        response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/sla-policies",
            json=payload
        )
        assert response.status_code == 200
        sla_id = response.json()["id"]
        self.created_sla_ids.append(sla_id)
        
        # Verify multipliers preserved
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/sla-policies/{sla_id}")
        assert get_response.status_code == 200
        sla = get_response.json()
        assert sla["priority_multipliers"]["critical"] == 0.25
        assert sla["priority_multipliers"]["high"] == 0.5
        print(f"✓ SLA policy with priority multipliers preserved correctly")
    
    def test_custom_form_with_complex_fields(self):
        """Test custom form with various field types"""
        payload = {
            "name": f"TEST_Complex_Form_{uuid.uuid4().hex[:8]}",
            "form_type": "ticket",
            "fields": [
                {"field_type": "text", "label": "Text Field", "validation": {"required": True}},
                {"field_type": "textarea", "label": "Description"},
                {"field_type": "number", "label": "Quantity"},
                {"field_type": "email", "label": "Contact Email"},
                {"field_type": "select", "label": "Category", "options": [
                    {"label": "Option A", "value": "a"},
                    {"label": "Option B", "value": "b"}
                ]},
                {"field_type": "date", "label": "Due Date"},
                {"field_type": "checkbox", "label": "Urgent"}
            ],
            "is_active": True
        }
        response = self.session.post(
            f"{BASE_URL}/api/admin/ticketing-config/custom-forms",
            json=payload
        )
        assert response.status_code == 200
        form_id = response.json()["id"]
        self.created_form_ids.append(form_id)
        
        # Verify all fields preserved
        get_response = self.session.get(f"{BASE_URL}/api/admin/ticketing-config/custom-forms/{form_id}")
        assert get_response.status_code == 200
        form = get_response.json()
        assert len(form["fields"]) == 7
        field_types = [f["field_type"] for f in form["fields"]]
        assert "text" in field_types
        assert "select" in field_types
        assert "date" in field_types
        print(f"✓ Custom form with complex fields preserved correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
