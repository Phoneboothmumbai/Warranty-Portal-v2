"""
Quotation and Workflow Validation Tests
Tests for:
1. Admin Quotation Management (CRUD, send)
2. Strict ticket workflow enforcement
3. Company portal quotations (view, approve/reject)
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"
COMPANY_EMAIL = "testuser@testcompany.com"
COMPANY_PASSWORD = "Test@123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Admin authentication failed")


@pytest.fixture(scope="module")
def company_token():
    """Get company user authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/company/auth/login",
        json={"email": COMPANY_EMAIL, "password": COMPANY_PASSWORD}
    )
    if response.status_code == 200:
        return response.json().get("access_token")
    pytest.skip("Company authentication failed")


class TestAdminQuotations:
    """Admin Quotation Management API Tests"""
    
    def test_list_quotations(self, admin_token):
        """Test listing quotations"""
        response = requests.get(
            f"{BASE_URL}/api/admin/quotations",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "quotations" in data
        assert "total" in data
        assert "page" in data
        print(f"Found {data['total']} quotations")
    
    def test_get_single_quotation(self, admin_token):
        """Test getting a single quotation"""
        # First get list to find a quotation ID
        list_response = requests.get(
            f"{BASE_URL}/api/admin/quotations",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        quotations = list_response.json().get("quotations", [])
        
        if not quotations:
            pytest.skip("No quotations available for testing")
        
        quotation_id = quotations[0]["id"]
        response = requests.get(
            f"{BASE_URL}/api/admin/quotations/{quotation_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == quotation_id
        assert "quotation_number" in data
        assert "items" in data
        assert "total_amount" in data


class TestWorkflowValidation:
    """Strict Ticket Workflow Enforcement Tests"""
    
    def test_cannot_assign_pending_parts_ticket(self, admin_token):
        """Test that tickets in pending_parts status cannot be reassigned"""
        # Get a staff user ID
        staff_response = requests.get(
            f"{BASE_URL}/api/admin/staff/users?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        staff_users = staff_response.json().get("users", [])
        if not staff_users:
            pytest.skip("No staff users available")
        
        staff_id = staff_users[0]["id"]
        
        # Find a pending_parts ticket
        tickets_response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?status=pending_parts&limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        tickets = tickets_response.json().get("tickets", [])
        
        if not tickets:
            pytest.skip("No pending_parts tickets available")
        
        ticket_id = tickets[0]["id"]
        
        # Try to assign - should fail
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"technician_id": staff_id}
        )
        assert response.status_code == 400
        assert "pending parts" in response.json().get("detail", "").lower()
        print("Correctly blocked assignment of pending_parts ticket")
    
    def test_cannot_assign_in_progress_ticket(self, admin_token):
        """Test that tickets in in_progress status cannot be reassigned"""
        # Get a staff user ID
        staff_response = requests.get(
            f"{BASE_URL}/api/admin/staff/users?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        staff_users = staff_response.json().get("users", [])
        if not staff_users:
            pytest.skip("No staff users available")
        
        staff_id = staff_users[0]["id"]
        
        # Find an in_progress ticket
        tickets_response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?status=in_progress&limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        tickets = tickets_response.json().get("tickets", [])
        
        if not tickets:
            pytest.skip("No in_progress tickets available")
        
        ticket_id = tickets[0]["id"]
        
        # Try to assign - should fail
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"technician_id": staff_id}
        )
        assert response.status_code == 400
        assert "in progress" in response.json().get("detail", "").lower()
        print("Correctly blocked assignment of in_progress ticket")
    
    def test_cannot_assign_assigned_ticket(self, admin_token):
        """Test that tickets in assigned status cannot be reassigned"""
        # Get a staff user ID
        staff_response = requests.get(
            f"{BASE_URL}/api/admin/staff/users?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        staff_users = staff_response.json().get("users", [])
        if not staff_users:
            pytest.skip("No staff users available")
        
        staff_id = staff_users[0]["id"]
        
        # Find an assigned ticket
        tickets_response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?status=assigned&limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        tickets = tickets_response.json().get("tickets", [])
        
        if not tickets:
            pytest.skip("No assigned tickets available")
        
        ticket_id = tickets[0]["id"]
        
        # Try to assign - should fail
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"technician_id": staff_id}
        )
        assert response.status_code == 400
        assert "already accepted" in response.json().get("detail", "").lower()
        print("Correctly blocked assignment of assigned ticket")
    
    def test_can_assign_new_ticket(self, admin_token):
        """Test that tickets in new status can be assigned"""
        # Get a staff user ID
        staff_response = requests.get(
            f"{BASE_URL}/api/admin/staff/users?limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        staff_users = staff_response.json().get("users", [])
        if not staff_users:
            pytest.skip("No staff users available")
        
        staff_id = staff_users[0]["id"]
        
        # Find a new ticket
        tickets_response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?status=new&limit=1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        tickets = tickets_response.json().get("tickets", [])
        
        if not tickets:
            pytest.skip("No new tickets available")
        
        ticket_id = tickets[0]["id"]
        
        # Try to assign - should succeed
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/assign",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"technician_id": staff_id}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending_acceptance"
        print("Successfully assigned new ticket")


class TestCompanyQuotations:
    """Company Portal Quotation Tests"""
    
    def test_list_company_quotations(self, company_token):
        """Test listing quotations for company user"""
        response = requests.get(
            f"{BASE_URL}/api/company/quotations",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "quotations" in data
        assert "total" in data
        print(f"Company can see {data['total']} quotations")
    
    def test_company_cannot_see_draft_quotations(self, company_token):
        """Test that company users cannot see draft quotations"""
        response = requests.get(
            f"{BASE_URL}/api/company/quotations",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        quotations = response.json().get("quotations", [])
        
        # All quotations should be sent, approved, or rejected (not draft)
        for q in quotations:
            assert q["status"] in ["sent", "approved", "rejected"], \
                f"Found draft quotation visible to company: {q['quotation_number']}"
        print("Company correctly cannot see draft quotations")
    
    def test_get_company_quotation_detail(self, company_token):
        """Test getting quotation detail for company user"""
        # First get list
        list_response = requests.get(
            f"{BASE_URL}/api/company/quotations",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        quotations = list_response.json().get("quotations", [])
        
        if not quotations:
            pytest.skip("No quotations available for company")
        
        quotation_id = quotations[0]["id"]
        response = requests.get(
            f"{BASE_URL}/api/company/quotations/{quotation_id}",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "internal_notes" not in data, "Internal notes should not be visible to company"
        print("Company can view quotation detail without internal notes")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
