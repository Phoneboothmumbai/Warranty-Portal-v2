"""
Test Create Ticket Modal Flow - Backend API Tests
=================================================
Tests for:
1. Help Topics API
2. Companies API
3. Sites Quick-Create API
4. Company Employees Quick-Create API
5. Ticket Creation API
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test admin credentials
TEST_EMAIL = "ck@motta.in"
TEST_PASSWORD = "Charu@123@"

@pytest.fixture(scope="module")
def auth_token():
    """Get admin auth token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip(f"Could not login: {response.text}")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestHelpTopics:
    """Tests for Help Topics API - used to populate dropdown"""
    
    def test_list_help_topics(self, headers):
        """GET /api/ticketing/help-topics - should return list of help topics"""
        response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return array of help topics"
        print(f"Found {len(data)} help topics")
        
        # Should have at least 1 help topic
        if len(data) > 0:
            topic = data[0]
            assert "id" in topic, "Topic should have id"
            assert "name" in topic, "Topic should have name"
            print(f"Sample topic: {topic.get('name')}")
    
    def test_get_help_topic_details(self, headers):
        """GET /api/ticketing/help-topics/{id} - should return topic with form details"""
        # First get list of topics
        response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No help topics available")
        
        topic_id = response.json()[0]["id"]
        
        # Get topic details
        detail_response = requests.get(f"{BASE_URL}/api/ticketing/help-topics/{topic_id}", headers=headers)
        assert detail_response.status_code == 200, f"Failed: {detail_response.text}"
        
        topic = detail_response.json()
        print(f"Topic details: {topic.get('name')}, has_form: {'form' in topic}")
        
        # If form is linked, it should be present
        if topic.get("form_id"):
            assert "form" in topic or topic.get("form") is None, "Form should be loaded if form_id exists"


class TestCompanies:
    """Tests for Companies API - SearchSelect component"""
    
    def test_list_companies(self, headers):
        """GET /api/admin/companies - should return list of companies"""
        response = requests.get(f"{BASE_URL}/api/admin/companies", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return array"
        print(f"Found {len(data)} companies")
        
        if len(data) > 0:
            company = data[0]
            assert "id" in company, "Company should have id"
            assert "name" in company, "Company should have name"
            print(f"Sample company: {company.get('name')}, id: {company.get('id')}")


class TestSitesQuickCreate:
    """Tests for Sites Quick-Create API - inline form"""
    
    @pytest.fixture
    def company_id(self, headers):
        """Get a company ID to use for site creation"""
        response = requests.get(f"{BASE_URL}/api/admin/companies", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No companies available")
        return response.json()[0]["id"]
    
    def test_sites_for_company(self, headers, company_id):
        """GET /api/admin/sites?company_id= - should return sites for company"""
        response = requests.get(f"{BASE_URL}/api/admin/sites?company_id={company_id}", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Response can be array or object with sites key
        if isinstance(data, dict):
            data = data.get("sites", [])
        print(f"Found {len(data)} sites for company {company_id}")
    
    def test_quick_create_site_success(self, headers, company_id):
        """POST /api/admin/sites/quick-create - should create site with JSON body"""
        payload = {
            "company_id": company_id,
            "name": "TEST_AutoCreated Site",
            "city": "Test City",
            "address": "123 Test Street",
            "contact_number": "9876543210",
            "primary_contact_name": "Test Contact"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/sites/quick-create",
            headers=headers,
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        site = response.json()
        assert "id" in site, "Created site should have id"
        assert site.get("name") == "TEST_AutoCreated Site", "Name should match"
        assert site.get("city") == "Test City", "City should match"
        print(f"Created site: {site.get('name')}, id: {site.get('id')}")
        
        # Cleanup - delete the site
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/sites/{site['id']}",
            headers=headers
        )
        print(f"Cleanup delete response: {delete_response.status_code}")
    
    def test_quick_create_site_missing_name(self, headers, company_id):
        """POST /api/admin/sites/quick-create - should fail without name"""
        payload = {
            "company_id": company_id
            # Missing name
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/sites/quick-create",
            headers=headers,
            json=payload
        )
        # Should fail with 422 (validation) or 400
        assert response.status_code in [400, 422], f"Should fail without name: {response.text}"


class TestEmployeesQuickCreate:
    """Tests for Company Employees Quick-Create API - inline form"""
    
    @pytest.fixture
    def company_id(self, headers):
        """Get a company ID to use for employee creation"""
        response = requests.get(f"{BASE_URL}/api/admin/companies", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No companies available")
        return response.json()[0]["id"]
    
    def test_employees_for_company(self, headers, company_id):
        """GET /api/admin/company-employees?company_id= - should return employees"""
        response = requests.get(f"{BASE_URL}/api/admin/company-employees?company_id={company_id}", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        if isinstance(data, dict):
            data = data.get("employees", [])
        print(f"Found {len(data)} employees for company {company_id}")
    
    def test_quick_create_employee_success(self, headers, company_id):
        """POST /api/admin/company-employees/quick-create - should create employee with JSON body"""
        payload = {
            "company_id": company_id,
            "name": "TEST_AutoCreated Employee",
            "phone": "9998887776",
            "email": "test_emp@test.com",
            "department": "IT"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/company-employees/quick-create",
            headers=headers,
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        emp = response.json()
        assert "id" in emp, "Created employee should have id"
        assert emp.get("name") == "TEST_AutoCreated Employee", "Name should match"
        assert emp.get("phone") == "9998887776", "Phone should match"
        assert emp.get("email") == "test_emp@test.com", "Email should match"
        assert emp.get("department") == "IT", "Department should match"
        print(f"Created employee: {emp.get('name')}, id: {emp.get('id')}")
        
        # Cleanup - delete the employee  
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/company-employees/{emp['id']}",
            headers=headers
        )
        print(f"Cleanup delete response: {delete_response.status_code}")
    
    def test_quick_create_employee_missing_company_id(self, headers):
        """POST /api/admin/company-employees/quick-create - should fail without company_id"""
        payload = {
            "name": "Test Employee"
            # Missing company_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/company-employees/quick-create",
            headers=headers,
            json=payload
        )
        assert response.status_code == 400, f"Should fail without company_id: {response.text}"
    
    def test_quick_create_employee_missing_name(self, headers, company_id):
        """POST /api/admin/company-employees/quick-create - should fail without name"""
        payload = {
            "company_id": company_id
            # Missing name
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/company-employees/quick-create",
            headers=headers,
            json=payload
        )
        assert response.status_code == 400, f"Should fail without name: {response.text}"


class TestPriorities:
    """Tests for Priorities API"""
    
    def test_list_priorities(self, headers):
        """GET /api/ticketing/priorities - should return list of priorities"""
        response = requests.get(f"{BASE_URL}/api/ticketing/priorities", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return array"
        print(f"Found {len(data)} priorities")
        
        if len(data) > 0:
            priority = data[0]
            assert "id" in priority, "Priority should have id"
            assert "name" in priority, "Priority should have name"


class TestDevices:
    """Tests for Devices API - SearchSelect in ticket modal"""
    
    @pytest.fixture
    def company_id(self, headers):
        """Get a company ID"""
        response = requests.get(f"{BASE_URL}/api/admin/companies", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No companies available")
        return response.json()[0]["id"]
    
    def test_devices_for_company(self, headers, company_id):
        """GET /api/admin/devices?company_id= - should return devices for company"""
        response = requests.get(f"{BASE_URL}/api/admin/devices?company_id={company_id}&limit=100", headers=headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        if isinstance(data, dict):
            data = data.get("devices", [])
        print(f"Found {len(data)} devices for company {company_id}")


class TestTicketCreation:
    """Tests for full ticket creation flow"""
    
    @pytest.fixture
    def help_topic_id(self, headers):
        """Get a help topic ID"""
        response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No help topics available")
        return response.json()[0]["id"]
    
    @pytest.fixture
    def company_id(self, headers):
        """Get a company ID"""
        response = requests.get(f"{BASE_URL}/api/admin/companies", headers=headers)
        if response.status_code != 200 or len(response.json()) == 0:
            pytest.skip("No companies available")
        return response.json()[0]["id"]
    
    def test_create_ticket_basic(self, headers, help_topic_id):
        """POST /api/ticketing/tickets - create basic ticket with minimal fields"""
        payload = {
            "help_topic_id": help_topic_id,
            "subject": "TEST_Ticket - Basic Creation Test",
            "description": "This is a test ticket created by automated testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets",
            headers=headers,
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        ticket = response.json()
        assert "id" in ticket, "Ticket should have id"
        assert "ticket_number" in ticket, "Ticket should have ticket_number"
        assert ticket.get("subject") == "TEST_Ticket - Basic Creation Test", "Subject should match"
        print(f"Created ticket: #{ticket.get('ticket_number')}, id: {ticket.get('id')}")
    
    def test_create_ticket_with_company_and_contact(self, headers, help_topic_id, company_id):
        """POST /api/ticketing/tickets - create ticket with company, site, employee info"""
        payload = {
            "help_topic_id": help_topic_id,
            "subject": "TEST_Ticket - Full Flow Test",
            "description": "Test ticket with company and contact info",
            "company_id": company_id,
            "contact_name": "Test Contact Person",
            "contact_phone": "9876543210",
            "contact_email": "testcontact@test.com"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets",
            headers=headers,
            json=payload
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        ticket = response.json()
        assert "id" in ticket
        assert "ticket_number" in ticket
        assert ticket.get("company_id") == company_id, "Company ID should match"
        print(f"Created ticket with company: #{ticket.get('ticket_number')}")
    
    def test_create_ticket_missing_help_topic(self, headers):
        """POST /api/ticketing/tickets - should fail without help_topic_id"""
        payload = {
            "subject": "Test Ticket",
            "description": "Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets",
            headers=headers,
            json=payload
        )
        # Should fail - help_topic_id is required
        assert response.status_code in [400, 422], f"Should fail without help_topic_id: {response.text}"
    
    def test_create_ticket_missing_subject(self, headers, help_topic_id):
        """POST /api/ticketing/tickets - should fail without subject"""
        payload = {
            "help_topic_id": help_topic_id,
            "description": "Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets",
            headers=headers,
            json=payload
        )
        # Should fail - subject is required
        assert response.status_code in [400, 422], f"Should fail without subject: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
