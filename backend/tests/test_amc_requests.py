"""
AMC Request System Tests
Tests for AMC packages, requests, company pricing, notifications, and approval workflow
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"
COMPANY_EMAIL = "jane@acme.com"
COMPANY_PASSWORD = "company123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def company_token():
    """Get company user authentication token"""
    response = requests.post(f"{BASE_URL}/api/company/auth/login", json={
        "email": COMPANY_EMAIL,
        "password": COMPANY_PASSWORD
    })
    assert response.status_code == 200, f"Company login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def company_user_info(company_token):
    """Get company user info from login"""
    response = requests.post(f"{BASE_URL}/api/company/auth/login", json={
        "email": COMPANY_EMAIL,
        "password": COMPANY_PASSWORD
    })
    return response.json().get("user", {})


class TestAMCPackagesAdmin:
    """Admin AMC Package CRUD tests"""
    
    def test_list_amc_packages(self, admin_token):
        """Test listing AMC packages as admin"""
        response = requests.get(
            f"{BASE_URL}/api/admin/amc-packages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        packages = response.json()
        assert isinstance(packages, list)
        # Verify existing packages
        assert len(packages) >= 3, "Should have at least 3 seed packages"
        
        # Verify package structure
        for pkg in packages:
            assert "id" in pkg
            assert "name" in pkg
            assert "base_price_per_device" in pkg
            assert "amc_type" in pkg
    
    def test_create_amc_package(self, admin_token):
        """Test creating a new AMC package"""
        test_package = {
            "name": f"TEST_Package_{uuid.uuid4().hex[:8]}",
            "amc_type": "comprehensive",
            "description": "Test package for automated testing",
            "base_price_per_device": 2500.0,
            "duration_months": 12,
            "is_active": True
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/amc-packages",
            json=test_package,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        created = response.json()
        assert created["name"] == test_package["name"]
        assert created["base_price_per_device"] == test_package["base_price_per_device"]
        assert "id" in created
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/admin/amc-packages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        packages = get_response.json()
        found = any(p["id"] == created["id"] for p in packages)
        assert found, "Created package should be in list"
        
        return created["id"]
    
    def test_update_amc_package(self, admin_token):
        """Test updating an AMC package"""
        # First create a package
        test_package = {
            "name": f"TEST_Update_{uuid.uuid4().hex[:8]}",
            "amc_type": "non_comprehensive",
            "base_price_per_device": 1000.0
        }
        create_response = requests.post(
            f"{BASE_URL}/api/admin/amc-packages",
            json=test_package,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        package_id = create_response.json()["id"]
        
        # Update the package
        update_data = {
            "base_price_per_device": 1500.0,
            "description": "Updated description"
        }
        update_response = requests.put(
            f"{BASE_URL}/api/admin/amc-packages/{package_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["base_price_per_device"] == 1500.0
        assert updated["description"] == "Updated description"
    
    def test_delete_amc_package(self, admin_token):
        """Test soft deleting an AMC package"""
        # Create a package to delete
        test_package = {
            "name": f"TEST_Delete_{uuid.uuid4().hex[:8]}",
            "amc_type": "on_call",
            "base_price_per_device": 500.0
        }
        create_response = requests.post(
            f"{BASE_URL}/api/admin/amc-packages",
            json=test_package,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        package_id = create_response.json()["id"]
        
        # Delete the package
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/amc-packages/{package_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        
        # Verify it's not in active list
        list_response = requests.get(
            f"{BASE_URL}/api/admin/amc-packages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        packages = list_response.json()
        found = any(p["id"] == package_id for p in packages)
        assert not found, "Deleted package should not be in active list"


class TestAMCPackagesCompany:
    """Company portal AMC package tests"""
    
    def test_list_available_packages(self, company_token):
        """Test company can see available packages"""
        response = requests.get(
            f"{BASE_URL}/api/company/amc-packages",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        packages = response.json()
        assert isinstance(packages, list)
        assert len(packages) >= 3
        
        # Verify company-specific pricing fields
        for pkg in packages:
            assert "price_per_device" in pkg
            assert "has_custom_pricing" in pkg


class TestCompanyPricing:
    """Company-specific pricing tests"""
    
    def test_set_company_pricing(self, admin_token, company_user_info):
        """Test setting custom pricing for a company"""
        # Get a package ID
        packages_response = requests.get(
            f"{BASE_URL}/api/admin/amc-packages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        package_id = packages_response.json()[0]["id"]
        company_id = company_user_info.get("company_id")
        
        if not company_id:
            pytest.skip("Company ID not available")
        
        pricing_data = {
            "company_id": company_id,
            "package_id": package_id,
            "custom_price_per_device": 1200.0,
            "discount_percentage": 20,
            "notes": "Special pricing for test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/amc-company-pricing",
            json=pricing_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        pricing = response.json()
        assert pricing["custom_price_per_device"] == 1200.0
        assert pricing["discount_percentage"] == 20
    
    def test_list_company_pricing(self, admin_token):
        """Test listing company-specific pricing"""
        response = requests.get(
            f"{BASE_URL}/api/admin/amc-company-pricing",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)


class TestAMCRequestsCompany:
    """Company AMC request tests"""
    
    def test_list_my_requests(self, company_token):
        """Test company can list their AMC requests"""
        response = requests.get(
            f"{BASE_URL}/api/company/amc-requests",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        requests_list = response.json()
        assert isinstance(requests_list, list)
        
        # Verify existing test request
        if len(requests_list) > 0:
            req = requests_list[0]
            assert "id" in req
            assert "status" in req
            assert "amc_type" in req
            assert "device_count" in req
    
    def test_create_amc_request(self, company_token):
        """Test creating a new AMC request"""
        # First get devices
        devices_response = requests.get(
            f"{BASE_URL}/api/company/devices",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        devices = devices_response.json()
        
        if len(devices) == 0:
            pytest.skip("No devices available for testing")
        
        device_ids = [devices[0]["id"]]
        
        request_data = {
            "amc_type": "comprehensive",
            "duration_months": 12,
            "selection_type": "specific",
            "selected_device_ids": device_ids,
            "preferred_start_date": "2026-03-01",
            "special_requirements": "TEST_Request - automated testing",
            "budget_range": "1000-5000"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/amc-requests",
            json=request_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        created = response.json()
        assert created["status"] == "pending_review"
        assert created["amc_type"] == "comprehensive"
        assert created["device_count"] == len(device_ids)
        
        return created["id"]
    
    def test_get_request_details(self, company_token):
        """Test getting AMC request details"""
        # Get list first
        list_response = requests.get(
            f"{BASE_URL}/api/company/amc-requests",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        requests_list = list_response.json()
        
        if len(requests_list) == 0:
            pytest.skip("No requests to test")
        
        request_id = requests_list[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/company/amc-requests/{request_id}",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        detail = response.json()
        assert detail["id"] == request_id
        assert "selected_devices" in detail or detail["selection_type"] != "specific"


class TestAMCRequestsAdmin:
    """Admin AMC request management tests"""
    
    def test_list_all_requests(self, admin_token):
        """Test admin can list all AMC requests"""
        response = requests.get(
            f"{BASE_URL}/api/admin/amc-requests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        requests_list = response.json()
        assert isinstance(requests_list, list)
        
        # Verify enriched data
        if len(requests_list) > 0:
            req = requests_list[0]
            assert "company_name" in req
    
    def test_filter_requests_by_status(self, admin_token):
        """Test filtering requests by status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/amc-requests?status=pending_review",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        requests_list = response.json()
        for req in requests_list:
            assert req["status"] == "pending_review"
    
    def test_get_request_detail_admin(self, admin_token):
        """Test admin can get detailed request info"""
        # Get list first
        list_response = requests.get(
            f"{BASE_URL}/api/admin/amc-requests",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        requests_list = list_response.json()
        
        if len(requests_list) == 0:
            pytest.skip("No requests to test")
        
        request_id = requests_list[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/admin/amc-requests/{request_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        detail = response.json()
        assert "company" in detail
        assert "selected_devices" in detail or detail["selection_type"] != "specific"
    
    def test_update_request_pricing(self, admin_token):
        """Test admin can set pricing on request"""
        # Get a pending request
        list_response = requests.get(
            f"{BASE_URL}/api/admin/amc-requests?status=pending_review",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        requests_list = list_response.json()
        
        if len(requests_list) == 0:
            pytest.skip("No pending requests to test")
        
        request_id = requests_list[0]["id"]
        
        update_data = {
            "price_per_device": 3000.0,
            "total_price": 3000.0,
            "admin_notes": "TEST_Pricing set by automated test"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/amc-requests/{request_id}",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["price_per_device"] == 3000.0
        assert updated["total_price"] == 3000.0
    
    def test_mark_under_review(self, admin_token, company_token):
        """Test marking request as under review"""
        # Create a fresh request
        devices_response = requests.get(
            f"{BASE_URL}/api/company/devices",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        devices = devices_response.json()
        
        if len(devices) == 0:
            pytest.skip("No devices available")
        
        request_data = {
            "amc_type": "non_comprehensive",
            "duration_months": 24,
            "selection_type": "specific",
            "selected_device_ids": [devices[0]["id"]],
            "preferred_start_date": "2026-04-01",
            "special_requirements": "TEST_UnderReview"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/company/amc-requests",
            json=request_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        request_id = create_response.json()["id"]
        
        # Mark as under review
        update_response = requests.put(
            f"{BASE_URL}/api/admin/amc-requests/{request_id}",
            json={"status": "under_review"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "under_review"
    
    def test_request_changes(self, admin_token, company_token):
        """Test requesting changes on a request"""
        # Create a fresh request
        devices_response = requests.get(
            f"{BASE_URL}/api/company/devices",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        devices = devices_response.json()
        
        if len(devices) == 0:
            pytest.skip("No devices available")
        
        request_data = {
            "amc_type": "comprehensive",
            "duration_months": 12,
            "selection_type": "specific",
            "selected_device_ids": [devices[0]["id"]],
            "preferred_start_date": "2026-05-01",
            "special_requirements": "TEST_ChangesRequested"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/company/amc-requests",
            json=request_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        request_id = create_response.json()["id"]
        
        # Request changes
        update_response = requests.put(
            f"{BASE_URL}/api/admin/amc-requests/{request_id}",
            json={
                "status": "changes_requested",
                "changes_requested_note": "Please add more devices to the request"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "changes_requested"
        assert update_response.json()["changes_requested_note"] == "Please add more devices to the request"
    
    def test_reject_request(self, admin_token, company_token):
        """Test rejecting a request"""
        # Create a fresh request
        devices_response = requests.get(
            f"{BASE_URL}/api/company/devices",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        devices = devices_response.json()
        
        if len(devices) == 0:
            pytest.skip("No devices available")
        
        request_data = {
            "amc_type": "on_call",
            "duration_months": 12,
            "selection_type": "specific",
            "selected_device_ids": [devices[0]["id"]],
            "preferred_start_date": "2026-06-01",
            "special_requirements": "TEST_Rejected"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/company/amc-requests",
            json=request_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        request_id = create_response.json()["id"]
        
        # Reject
        update_response = requests.put(
            f"{BASE_URL}/api/admin/amc-requests/{request_id}",
            json={
                "status": "rejected",
                "rejection_reason": "Budget constraints - TEST"
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "rejected"
        assert update_response.json()["rejection_reason"] == "Budget constraints - TEST"


class TestAMCApprovalWorkflow:
    """Test the full approval workflow"""
    
    def test_approve_request_creates_contract(self, admin_token, company_token):
        """Test approving a request creates an AMC contract"""
        # Create a fresh request
        devices_response = requests.get(
            f"{BASE_URL}/api/company/devices",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        devices = devices_response.json()
        
        if len(devices) == 0:
            pytest.skip("No devices available")
        
        request_data = {
            "amc_type": "comprehensive",
            "duration_months": 12,
            "selection_type": "specific",
            "selected_device_ids": [devices[0]["id"]],
            "preferred_start_date": "2026-07-01",
            "special_requirements": "TEST_Approval"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/company/amc-requests",
            json=request_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        request_id = create_response.json()["id"]
        
        # Set pricing first
        pricing_response = requests.put(
            f"{BASE_URL}/api/admin/amc-requests/{request_id}",
            json={
                "price_per_device": 3000.0,
                "total_price": 3000.0
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert pricing_response.status_code == 200
        
        # Approve
        approve_response = requests.post(
            f"{BASE_URL}/api/admin/amc-requests/{request_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert approve_response.status_code == 200
        result = approve_response.json()
        assert "contract_id" in result
        assert result["request"]["status"] == "approved"
        assert result["request"]["approved_contract_id"] is not None


class TestNotifications:
    """Test in-app notifications"""
    
    def test_company_notifications(self, company_token):
        """Test company user can get notifications"""
        response = requests.get(
            f"{BASE_URL}/api/company/notifications",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
    
    def test_admin_notifications(self, admin_token):
        """Test admin can get notifications"""
        response = requests.get(
            f"{BASE_URL}/api/admin/notifications",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
    
    def test_mark_notification_read(self, company_token):
        """Test marking notification as read"""
        # Get notifications
        list_response = requests.get(
            f"{BASE_URL}/api/company/notifications",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        notifications = list_response.json()["notifications"]
        
        if len(notifications) == 0:
            pytest.skip("No notifications to test")
        
        notification_id = notifications[0]["id"]
        
        response = requests.put(
            f"{BASE_URL}/api/company/notifications/{notification_id}/read",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
    
    def test_mark_all_notifications_read(self, company_token):
        """Test marking all notifications as read"""
        response = requests.put(
            f"{BASE_URL}/api/company/notifications/read-all",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200


class TestEdgeCases:
    """Edge case and validation tests"""
    
    def test_create_request_no_devices_fails(self, company_token):
        """Test creating request with no devices fails"""
        request_data = {
            "amc_type": "comprehensive",
            "duration_months": 12,
            "selection_type": "specific",
            "selected_device_ids": [],
            "preferred_start_date": "2026-08-01"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/amc-requests",
            json=request_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 400
    
    def test_approve_already_approved_fails(self, admin_token):
        """Test approving already approved request fails"""
        # Get an approved request
        list_response = requests.get(
            f"{BASE_URL}/api/admin/amc-requests?status=approved",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        requests_list = list_response.json()
        
        if len(requests_list) == 0:
            pytest.skip("No approved requests to test")
        
        request_id = requests_list[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/amc-requests/{request_id}/approve",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
    
    def test_cancel_request(self, company_token):
        """Test company can cancel their request"""
        # Get a pending request
        list_response = requests.get(
            f"{BASE_URL}/api/company/amc-requests",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        requests_list = list_response.json()
        
        # Find a pending request
        pending = [r for r in requests_list if r["status"] in ["pending_review", "under_review", "changes_requested"]]
        
        if len(pending) == 0:
            pytest.skip("No cancellable requests")
        
        request_id = pending[0]["id"]
        
        response = requests.delete(
            f"{BASE_URL}/api/company/amc-requests/{request_id}",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        
        # Verify status changed
        get_response = requests.get(
            f"{BASE_URL}/api/company/amc-requests/{request_id}",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert get_response.json()["status"] == "cancelled"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
