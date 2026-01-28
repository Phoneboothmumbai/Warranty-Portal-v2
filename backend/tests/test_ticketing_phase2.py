"""
Test Suite for Enterprise Ticketing System - Phase 2
Tests Admin Ticketing Settings (Departments, SLA Policies, Categories) and Public Ticket Portal
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


class TestTicketingEnums(TestSetup):
    """Test ticketing enum endpoints"""
    
    def test_get_ticketing_enums(self, admin_headers):
        """Test GET /api/ticketing/enums returns all enum values"""
        response = requests.get(f"{BASE_URL}/api/ticketing/enums", headers=admin_headers)
        assert response.status_code == 200, f"Failed to get enums: {response.text}"
        data = response.json()
        
        # Verify all enum categories exist
        assert "statuses" in data, "Missing statuses enum"
        assert "priorities" in data, "Missing priorities enum"
        assert "sources" in data, "Missing sources enum"
        assert "staff_roles" in data, "Missing staff_roles enum"
        
        # Verify statuses contain expected values
        status_values = [s["value"] for s in data["statuses"]]
        assert "open" in status_values
        assert "in_progress" in status_values
        assert "resolved" in status_values
        assert "closed" in status_values
        
        print(f"SUCCESS: Ticketing enums returned with {len(data['statuses'])} statuses, {len(data['priorities'])} priorities")


class TestAdminDepartments(TestSetup):
    """Test Admin Department CRUD operations"""
    
    def test_list_departments(self, admin_headers):
        """Test GET /api/ticketing/admin/departments"""
        response = requests.get(f"{BASE_URL}/api/ticketing/admin/departments", headers=admin_headers)
        assert response.status_code == 200, f"Failed to list departments: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(data)} departments")
        return data
    
    def test_list_departments_include_inactive(self, admin_headers):
        """Test GET /api/ticketing/admin/departments with include_inactive=true"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/departments?include_inactive=true", 
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to list departments: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(data)} departments (including inactive)")
    
    def test_create_department(self, admin_headers):
        """Test POST /api/ticketing/admin/departments"""
        dept_data = {
            "name": f"TEST_Dept_{uuid.uuid4().hex[:6]}",
            "description": "Test department for automated testing",
            "default_priority": "medium",
            "is_public": True,
            "sort_order": 99
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/departments",
            headers=admin_headers,
            json=dept_data
        )
        assert response.status_code == 200, f"Failed to create department: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data, "Missing id in response"
        assert data["name"] == dept_data["name"], "Name mismatch"
        assert data["description"] == dept_data["description"], "Description mismatch"
        assert data["default_priority"] == "medium", "Priority mismatch"
        assert data["is_public"] == True, "is_public mismatch"
        
        print(f"SUCCESS: Created department {data['name']} with id {data['id']}")
        return data
    
    def test_get_department_by_id(self, admin_headers):
        """Test GET /api/ticketing/admin/departments/{dept_id}"""
        # First create a department
        dept_data = {
            "name": f"TEST_GetDept_{uuid.uuid4().hex[:6]}",
            "description": "Test department for get by id",
            "default_priority": "high",
            "is_public": False
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/departments",
            headers=admin_headers,
            json=dept_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        dept_id = created["id"]
        
        # Get by ID
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/departments/{dept_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get department: {response.text}"
        data = response.json()
        assert data["id"] == dept_id, "ID mismatch"
        assert data["name"] == dept_data["name"], "Name mismatch"
        
        print(f"SUCCESS: Retrieved department {data['name']} by ID")
    
    def test_update_department(self, admin_headers):
        """Test PUT /api/ticketing/admin/departments/{dept_id}"""
        # First create a department
        dept_data = {
            "name": f"TEST_UpdateDept_{uuid.uuid4().hex[:6]}",
            "description": "Original description",
            "default_priority": "low"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/departments",
            headers=admin_headers,
            json=dept_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        dept_id = created["id"]
        
        # Update department
        update_data = {
            "description": "Updated description",
            "default_priority": "critical",
            "is_public": True
        }
        response = requests.put(
            f"{BASE_URL}/api/ticketing/admin/departments/{dept_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Failed to update department: {response.text}"
        data = response.json()
        
        assert data["description"] == "Updated description", "Description not updated"
        assert data["default_priority"] == "critical", "Priority not updated"
        assert data["is_public"] == True, "is_public not updated"
        
        print(f"SUCCESS: Updated department {data['name']}")
    
    def test_delete_department(self, admin_headers):
        """Test DELETE /api/ticketing/admin/departments/{dept_id}"""
        # First create a department
        dept_data = {
            "name": f"TEST_DeleteDept_{uuid.uuid4().hex[:6]}",
            "description": "Department to be deleted"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/departments",
            headers=admin_headers,
            json=dept_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        dept_id = created["id"]
        
        # Delete department
        response = requests.delete(
            f"{BASE_URL}/api/ticketing/admin/departments/{dept_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to delete department: {response.text}"
        
        # Verify deletion (should return 404)
        get_response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/departments/{dept_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404, "Department should be deleted"
        
        print(f"SUCCESS: Deleted department {dept_id}")


class TestAdminSLAPolicies(TestSetup):
    """Test Admin SLA Policy CRUD operations"""
    
    def test_list_sla_policies(self, admin_headers):
        """Test GET /api/ticketing/admin/sla-policies"""
        response = requests.get(f"{BASE_URL}/api/ticketing/admin/sla-policies", headers=admin_headers)
        assert response.status_code == 200, f"Failed to list SLA policies: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(data)} SLA policies")
        return data
    
    def test_list_sla_policies_include_inactive(self, admin_headers):
        """Test GET /api/ticketing/admin/sla-policies with include_inactive=true"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/sla-policies?include_inactive=true",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to list SLA policies: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(data)} SLA policies (including inactive)")
    
    def test_create_sla_policy(self, admin_headers):
        """Test POST /api/ticketing/admin/sla-policies"""
        sla_data = {
            "name": f"TEST_SLA_{uuid.uuid4().hex[:6]}",
            "description": "Test SLA policy for automated testing",
            "response_time_hours": 2,
            "resolution_time_hours": 8,
            "response_time_business_hours": True,
            "resolution_time_business_hours": True,
            "business_hours_start": "09:00",
            "business_hours_end": "18:00",
            "business_days": [1, 2, 3, 4, 5],
            "is_default": False
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/sla-policies",
            headers=admin_headers,
            json=sla_data
        )
        assert response.status_code == 200, f"Failed to create SLA policy: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data, "Missing id in response"
        assert data["name"] == sla_data["name"], "Name mismatch"
        assert data["response_time_hours"] == 2, "Response time mismatch"
        assert data["resolution_time_hours"] == 8, "Resolution time mismatch"
        assert data["business_hours_start"] == "09:00", "Business hours start mismatch"
        assert data["business_hours_end"] == "18:00", "Business hours end mismatch"
        
        print(f"SUCCESS: Created SLA policy {data['name']} with id {data['id']}")
        return data
    
    def test_get_sla_policy_by_id(self, admin_headers):
        """Test GET /api/ticketing/admin/sla-policies/{policy_id}"""
        # First create an SLA policy
        sla_data = {
            "name": f"TEST_GetSLA_{uuid.uuid4().hex[:6]}",
            "response_time_hours": 4,
            "resolution_time_hours": 24
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/sla-policies",
            headers=admin_headers,
            json=sla_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        policy_id = created["id"]
        
        # Get by ID
        response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/sla-policies/{policy_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to get SLA policy: {response.text}"
        data = response.json()
        assert data["id"] == policy_id, "ID mismatch"
        assert data["name"] == sla_data["name"], "Name mismatch"
        
        print(f"SUCCESS: Retrieved SLA policy {data['name']} by ID")
    
    def test_update_sla_policy(self, admin_headers):
        """Test PUT /api/ticketing/admin/sla-policies/{policy_id}"""
        # First create an SLA policy
        sla_data = {
            "name": f"TEST_UpdateSLA_{uuid.uuid4().hex[:6]}",
            "response_time_hours": 4,
            "resolution_time_hours": 24
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/sla-policies",
            headers=admin_headers,
            json=sla_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        policy_id = created["id"]
        
        # Update SLA policy
        update_data = {
            "response_time_hours": 1,
            "resolution_time_hours": 4,
            "description": "Updated SLA policy"
        }
        response = requests.put(
            f"{BASE_URL}/api/ticketing/admin/sla-policies/{policy_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Failed to update SLA policy: {response.text}"
        data = response.json()
        
        assert data["response_time_hours"] == 1, "Response time not updated"
        assert data["resolution_time_hours"] == 4, "Resolution time not updated"
        assert data["description"] == "Updated SLA policy", "Description not updated"
        
        print(f"SUCCESS: Updated SLA policy {data['name']}")
    
    def test_delete_sla_policy(self, admin_headers):
        """Test DELETE /api/ticketing/admin/sla-policies/{policy_id}"""
        # First create an SLA policy
        sla_data = {
            "name": f"TEST_DeleteSLA_{uuid.uuid4().hex[:6]}",
            "response_time_hours": 4,
            "resolution_time_hours": 24
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/sla-policies",
            headers=admin_headers,
            json=sla_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        policy_id = created["id"]
        
        # Delete SLA policy
        response = requests.delete(
            f"{BASE_URL}/api/ticketing/admin/sla-policies/{policy_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to delete SLA policy: {response.text}"
        
        # Verify deletion (should return 404)
        get_response = requests.get(
            f"{BASE_URL}/api/ticketing/admin/sla-policies/{policy_id}",
            headers=admin_headers
        )
        assert get_response.status_code == 404, "SLA policy should be deleted"
        
        print(f"SUCCESS: Deleted SLA policy {policy_id}")


class TestAdminCategories(TestSetup):
    """Test Admin Category CRUD operations"""
    
    def test_list_categories(self, admin_headers):
        """Test GET /api/ticketing/admin/categories"""
        response = requests.get(f"{BASE_URL}/api/ticketing/admin/categories", headers=admin_headers)
        assert response.status_code == 200, f"Failed to list categories: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(data)} categories")
        return data
    
    def test_create_category(self, admin_headers):
        """Test POST /api/ticketing/admin/categories"""
        cat_data = {
            "name": f"TEST_Cat_{uuid.uuid4().hex[:6]}",
            "description": "Test category for automated testing",
            "auto_priority": "high",
            "sort_order": 99
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/categories",
            headers=admin_headers,
            json=cat_data
        )
        assert response.status_code == 200, f"Failed to create category: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data, "Missing id in response"
        assert data["name"] == cat_data["name"], "Name mismatch"
        assert data["description"] == cat_data["description"], "Description mismatch"
        assert data["auto_priority"] == "high", "Auto priority mismatch"
        
        print(f"SUCCESS: Created category {data['name']} with id {data['id']}")
        return data
    
    def test_create_category_with_auto_department(self, admin_headers):
        """Test creating category with auto-routing to department"""
        # First get a department
        dept_response = requests.get(f"{BASE_URL}/api/ticketing/admin/departments", headers=admin_headers)
        assert dept_response.status_code == 200
        departments = dept_response.json()
        
        if len(departments) > 0:
            dept_id = departments[0]["id"]
            cat_data = {
                "name": f"TEST_AutoRouteCat_{uuid.uuid4().hex[:6]}",
                "description": "Category with auto-routing",
                "auto_department_id": dept_id,
                "auto_priority": "medium"
            }
            response = requests.post(
                f"{BASE_URL}/api/ticketing/admin/categories",
                headers=admin_headers,
                json=cat_data
            )
            assert response.status_code == 200, f"Failed to create category: {response.text}"
            data = response.json()
            assert data["auto_department_id"] == dept_id, "Auto department not set"
            print(f"SUCCESS: Created category with auto-routing to department {dept_id}")
        else:
            print("SKIP: No departments available for auto-routing test")
    
    def test_update_category(self, admin_headers):
        """Test PUT /api/ticketing/admin/categories/{category_id}"""
        # First create a category
        cat_data = {
            "name": f"TEST_UpdateCat_{uuid.uuid4().hex[:6]}",
            "description": "Original description"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/categories",
            headers=admin_headers,
            json=cat_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        cat_id = created["id"]
        
        # Update category
        update_data = {
            "description": "Updated description",
            "auto_priority": "critical"
        }
        response = requests.put(
            f"{BASE_URL}/api/ticketing/admin/categories/{cat_id}",
            headers=admin_headers,
            json=update_data
        )
        assert response.status_code == 200, f"Failed to update category: {response.text}"
        data = response.json()
        
        assert data["description"] == "Updated description", "Description not updated"
        assert data["auto_priority"] == "critical", "Auto priority not updated"
        
        print(f"SUCCESS: Updated category {data['name']}")
    
    def test_delete_category(self, admin_headers):
        """Test DELETE /api/ticketing/admin/categories/{category_id}"""
        # First create a category
        cat_data = {
            "name": f"TEST_DeleteCat_{uuid.uuid4().hex[:6]}",
            "description": "Category to be deleted"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/admin/categories",
            headers=admin_headers,
            json=cat_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        cat_id = created["id"]
        
        # Delete category
        response = requests.delete(
            f"{BASE_URL}/api/ticketing/admin/categories/{cat_id}",
            headers=admin_headers
        )
        assert response.status_code == 200, f"Failed to delete category: {response.text}"
        
        print(f"SUCCESS: Deleted category {cat_id}")


class TestPublicTicketPortal(TestSetup):
    """Test Public Ticket Portal (No Auth Required)"""
    
    def test_get_public_departments(self):
        """Test GET /api/ticketing/public/departments (no auth)"""
        response = requests.get(f"{BASE_URL}/api/ticketing/public/departments")
        assert response.status_code == 200, f"Failed to get public departments: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(data)} public departments")
        return data
    
    def test_get_public_categories(self):
        """Test GET /api/ticketing/public/categories (no auth)"""
        response = requests.get(f"{BASE_URL}/api/ticketing/public/categories")
        assert response.status_code == 200, f"Failed to get public categories: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"SUCCESS: Listed {len(data)} public categories")
        return data
    
    def test_create_public_ticket(self):
        """Test POST /api/ticketing/public/tickets (no auth)"""
        ticket_data = {
            "name": "TEST_Public User",
            "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
            "phone": "+1-555-123-4567",
            "subject": f"TEST_Public Ticket {uuid.uuid4().hex[:6]}",
            "description": "This is a test ticket created from the public portal for automated testing.",
            "priority": "medium"
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/public/tickets",
            json=ticket_data
        )
        assert response.status_code == 200, f"Failed to create public ticket: {response.text}"
        data = response.json()
        
        # Verify response data
        assert "id" in data, "Missing id in response"
        assert "ticket_number" in data, "Missing ticket_number in response"
        assert data["ticket_number"].startswith("TKT-"), "Invalid ticket number format"
        assert data["subject"] == ticket_data["subject"], "Subject mismatch"
        assert data["status"] == "open", "Status should be open"
        assert "message" in data, "Missing success message"
        
        print(f"SUCCESS: Created public ticket {data['ticket_number']}")
        return data, ticket_data["email"]
    
    def test_create_public_ticket_with_department(self):
        """Test creating public ticket with department selection"""
        # Get public departments
        dept_response = requests.get(f"{BASE_URL}/api/ticketing/public/departments")
        departments = dept_response.json()
        
        ticket_data = {
            "name": "TEST_Public User with Dept",
            "email": f"test_{uuid.uuid4().hex[:6]}@example.com",
            "subject": f"TEST_Ticket with Department {uuid.uuid4().hex[:6]}",
            "description": "Test ticket with department selection",
            "priority": "high"
        }
        
        if len(departments) > 0:
            ticket_data["department_id"] = departments[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/public/tickets",
            json=ticket_data
        )
        assert response.status_code == 200, f"Failed to create public ticket: {response.text}"
        data = response.json()
        assert "ticket_number" in data
        print(f"SUCCESS: Created public ticket with department: {data['ticket_number']}")
    
    def test_create_public_ticket_invalid_email(self):
        """Test creating public ticket with invalid email"""
        ticket_data = {
            "name": "TEST_Invalid Email User",
            "email": "invalid-email",
            "subject": "Test Invalid Email",
            "description": "This should fail due to invalid email"
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/public/tickets",
            json=ticket_data
        )
        assert response.status_code == 400, f"Should fail with invalid email: {response.text}"
        print("SUCCESS: Invalid email correctly rejected")
    
    def test_check_public_ticket_status(self):
        """Test GET /api/ticketing/public/tickets/{ticket_number}"""
        # First create a ticket
        email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        ticket_data = {
            "name": "TEST_Status Check User",
            "email": email,
            "subject": f"TEST_Status Check Ticket {uuid.uuid4().hex[:6]}",
            "description": "Test ticket for status check"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/public/tickets",
            json=ticket_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        ticket_number = created["ticket_number"]
        
        # Check status
        response = requests.get(
            f"{BASE_URL}/api/ticketing/public/tickets/{ticket_number}",
            params={"email": email}
        )
        assert response.status_code == 200, f"Failed to check ticket status: {response.text}"
        data = response.json()
        
        assert data["ticket_number"] == ticket_number, "Ticket number mismatch"
        assert data["status"] == "open", "Status should be open"
        assert "thread" in data, "Missing thread in response"
        
        print(f"SUCCESS: Retrieved ticket status for {ticket_number}")
    
    def test_check_ticket_status_wrong_email(self):
        """Test checking ticket status with wrong email"""
        # First create a ticket
        email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        ticket_data = {
            "name": "TEST_Wrong Email User",
            "email": email,
            "subject": f"TEST_Wrong Email Ticket {uuid.uuid4().hex[:6]}",
            "description": "Test ticket for wrong email check"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/public/tickets",
            json=ticket_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        ticket_number = created["ticket_number"]
        
        # Try to check with wrong email
        response = requests.get(
            f"{BASE_URL}/api/ticketing/public/tickets/{ticket_number}",
            params={"email": "wrong@example.com"}
        )
        assert response.status_code == 404, f"Should fail with wrong email: {response.text}"
        print("SUCCESS: Wrong email correctly rejected for ticket status check")
    
    def test_reply_to_public_ticket(self):
        """Test POST /api/ticketing/public/tickets/{ticket_number}/reply"""
        # First create a ticket
        email = f"test_{uuid.uuid4().hex[:6]}@example.com"
        ticket_data = {
            "name": "TEST_Reply User",
            "email": email,
            "subject": f"TEST_Reply Ticket {uuid.uuid4().hex[:6]}",
            "description": "Test ticket for reply"
        }
        create_response = requests.post(
            f"{BASE_URL}/api/ticketing/public/tickets",
            json=ticket_data
        )
        assert create_response.status_code == 200
        created = create_response.json()
        ticket_number = created["ticket_number"]
        
        # Add reply
        response = requests.post(
            f"{BASE_URL}/api/ticketing/public/tickets/{ticket_number}/reply",
            params={"content": "This is a test reply from the customer", "email": email}
        )
        assert response.status_code == 200, f"Failed to add reply: {response.text}"
        data = response.json()
        assert "message" in data, "Missing success message"
        
        # Verify reply in thread
        status_response = requests.get(
            f"{BASE_URL}/api/ticketing/public/tickets/{ticket_number}",
            params={"email": email}
        )
        assert status_response.status_code == 200
        status_data = status_response.json()
        
        # Check thread has the reply
        thread = status_data.get("thread", [])
        customer_replies = [e for e in thread if e.get("entry_type") == "customer_message"]
        assert len(customer_replies) > 0, "Reply not found in thread"
        
        print(f"SUCCESS: Added reply to ticket {ticket_number}")
    
    def test_check_existing_ticket(self):
        """Test checking status of existing test ticket TKT-20260128-F2C266"""
        ticket_number = "TKT-20260128-F2C266"
        email = "testuser@example.com"
        
        response = requests.get(
            f"{BASE_URL}/api/ticketing/public/tickets/{ticket_number}",
            params={"email": email}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"SUCCESS: Found existing ticket {ticket_number} with status: {data.get('status')}")
        else:
            print(f"INFO: Existing test ticket not found (may have been cleaned up)")


class TestAdminTicketDashboard(TestSetup):
    """Test Admin Ticketing Dashboard"""
    
    def test_get_ticketing_dashboard(self, admin_headers):
        """Test GET /api/ticketing/admin/dashboard"""
        response = requests.get(f"{BASE_URL}/api/ticketing/admin/dashboard", headers=admin_headers)
        assert response.status_code == 200, f"Failed to get dashboard: {response.text}"
        data = response.json()
        
        # Verify dashboard structure
        assert "total_open" in data, "Missing total_open"
        assert "unassigned" in data, "Missing unassigned"
        assert "sla_breached" in data, "Missing sla_breached"
        assert "by_status" in data, "Missing by_status"
        assert "by_priority" in data, "Missing by_priority"
        
        print(f"SUCCESS: Dashboard shows {data['total_open']} open tickets, {data['unassigned']} unassigned")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
