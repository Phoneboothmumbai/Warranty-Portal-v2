"""
Customer Portal API Tests - Multi-tenant portal endpoints testing
Tests for /api/portal/* routes including tenant resolution, login, and data retrieval
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test tenant code and credentials
TEST_TENANT_CODE = "test-company-085831"
TEST_PORTAL_EMAIL = "portal@test.com"
TEST_PORTAL_PASSWORD = "Welcome@123"
INVALID_TENANT_CODE = "invalid-tenant-xyz"


class TestPortalTenantResolution:
    """Test tenant resolution endpoint - public access"""
    
    def test_resolve_valid_tenant(self):
        """Verify valid tenant code returns company info and branding"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "company_id" in data
        assert "company_name" in data
        assert "tenant_code" in data
        assert data["tenant_code"] == TEST_TENANT_CODE
        assert "provider_name" in data
        assert "accent_color" in data
        print(f"✓ Tenant resolved: {data['company_name']}")
    
    def test_resolve_invalid_tenant_returns_404(self):
        """Verify invalid tenant code returns 404"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{INVALID_TENANT_CODE}")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
        print("✓ Invalid tenant returns 404 as expected")


class TestPortalAuthentication:
    """Test portal login endpoint"""
    
    def test_login_valid_credentials(self):
        """Verify valid credentials return token and user"""
        response = requests.post(
            f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/login",
            json={"email": TEST_PORTAL_EMAIL, "password": TEST_PORTAL_PASSWORD}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == TEST_PORTAL_EMAIL
        assert data["user"]["tenant_code"] == TEST_TENANT_CODE
        assert len(data["access_token"]) > 20  # Valid JWT should be longer
        print(f"✓ Login successful for {TEST_PORTAL_EMAIL}")
        return data["access_token"]
    
    def test_login_invalid_email(self):
        """Verify invalid email returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/login",
            json={"email": "invalid@wrong.com", "password": TEST_PORTAL_PASSWORD}
        )
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "invalid" in data["detail"].lower() or "credential" in data["detail"].lower()
        print("✓ Invalid email returns 401 as expected")
    
    def test_login_invalid_password(self):
        """Verify invalid password returns 401"""
        response = requests.post(
            f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/login",
            json={"email": TEST_PORTAL_EMAIL, "password": "wrongpassword123"}
        )
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        print("✓ Invalid password returns 401 as expected")
    
    def test_login_invalid_tenant_returns_404(self):
        """Verify login to invalid tenant returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/portal/tenant/{INVALID_TENANT_CODE}/login",
            json={"email": TEST_PORTAL_EMAIL, "password": TEST_PORTAL_PASSWORD}
        )
        assert response.status_code == 404
        print("✓ Login to invalid tenant returns 404 as expected")


class TestPortalTickets:
    """Test portal tickets endpoint"""
    
    def test_get_tickets_list(self):
        """Verify tickets endpoint returns ticket list"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/tickets")
        assert response.status_code == 200
        
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        assert isinstance(data["tickets"], list)
        
        if len(data["tickets"]) > 0:
            ticket = data["tickets"][0]
            assert "id" in ticket
            assert "ticket_number" in ticket
            assert "subject" in ticket
            assert "status" in ticket
            assert "priority" in ticket
            assert "is_open" in ticket
        
        print(f"✓ Retrieved {len(data['tickets'])} tickets (total: {data['total']})")
    
    def test_filter_open_tickets(self):
        """Verify status filter works for open tickets"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/tickets?status=open")
        assert response.status_code == 200
        
        data = response.json()
        for ticket in data["tickets"]:
            assert ticket["is_open"] == True, f"Ticket {ticket['ticket_number']} should be open"
        print(f"✓ Open tickets filter working ({len(data['tickets'])} tickets)")
    
    def test_filter_closed_tickets(self):
        """Verify status filter works for closed tickets"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/tickets?status=closed")
        assert response.status_code == 200
        
        data = response.json()
        for ticket in data["tickets"]:
            assert ticket["is_open"] == False, f"Ticket {ticket['ticket_number']} should be closed"
        print(f"✓ Closed tickets filter working ({len(data['tickets'])} tickets)")
    
    def test_search_tickets(self):
        """Verify search functionality works"""
        # Search by subject
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/tickets?search=TEST")
        assert response.status_code == 200
        
        data = response.json()
        # Should return tickets with TEST in subject or ticket number
        print(f"✓ Search functionality working ({len(data['tickets'])} results for 'TEST')")
    
    def test_pagination(self):
        """Verify pagination parameters work"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/tickets?page=1&limit=2")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["tickets"]) <= 2
        assert "page" in data
        assert "limit" in data
        print("✓ Pagination working correctly")


class TestPortalDevices:
    """Test portal devices endpoint"""
    
    def test_get_devices_list(self):
        """Verify devices endpoint returns device list"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/devices")
        assert response.status_code == 200
        
        data = response.json()
        assert "devices" in data
        assert "total" in data
        assert isinstance(data["devices"], list)
        
        if len(data["devices"]) > 0:
            device = data["devices"][0]
            assert "id" in device
            assert "serial_number" in device
            assert "brand" in device
            assert "warranty_status" in device
        
        print(f"✓ Retrieved {len(data['devices'])} devices (total: {data['total']})")
    
    def test_search_devices(self):
        """Verify device search works"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/devices?search=Dell")
        assert response.status_code == 200
        
        data = response.json()
        print(f"✓ Device search working ({len(data['devices'])} results for 'Dell')")


class TestPortalContracts:
    """Test portal contracts endpoint"""
    
    def test_get_contracts_list(self):
        """Verify contracts endpoint returns contract list"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/contracts")
        assert response.status_code == 200
        
        data = response.json()
        assert "contracts" in data
        assert "total" in data
        assert "active" in data
        assert "expired" in data
        assert isinstance(data["contracts"], list)
        
        if len(data["contracts"]) > 0:
            contract = data["contracts"][0]
            assert "id" in contract
            assert "name" in contract
            assert "status" in contract
            assert "start_date" in contract
            assert "end_date" in contract
        
        print(f"✓ Retrieved {len(data['contracts'])} contracts (active: {data['active']}, expired: {data['expired']})")


class TestPortalProfile:
    """Test portal profile endpoint"""
    
    def test_get_company_profile(self):
        """Verify profile endpoint returns company info and stats"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/profile")
        assert response.status_code == 200
        
        data = response.json()
        assert "id" in data
        assert "name" in data
        assert "tenant_code" in data
        assert data["tenant_code"] == TEST_TENANT_CODE
        assert "stats" in data
        assert "devices" in data["stats"]
        assert "tickets" in data["stats"]
        assert "contracts" in data["stats"]
        
        print(f"✓ Profile retrieved: {data['name']} (Devices: {data['stats']['devices']}, Tickets: {data['stats']['tickets']})")


class TestPortalAnalytics:
    """Test portal analytics endpoint"""
    
    def test_get_analytics(self):
        """Verify analytics endpoint returns dashboard data"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/analytics")
        assert response.status_code == 200
        
        data = response.json()
        assert "company_name" in data
        assert "summary" in data
        
        # Check summary fields
        summary = data["summary"]
        assert "total_tickets" in summary
        assert "open_tickets" in summary
        assert "closed_tickets" in summary
        assert "total_devices" in summary
        assert "active_contracts" in summary
        assert "sla_compliance" in summary
        
        # Check chart data
        assert "volume_by_day" in data
        assert "stage_distribution" in data
        assert "priority_distribution" in data
        assert "warranty_timeline" in data
        assert "brand_distribution" in data
        assert "recent_tickets" in data
        
        print(f"✓ Analytics retrieved for {data['company_name']}: {summary['total_tickets']} tickets, {summary['total_devices']} devices")
    
    def test_analytics_with_days_param(self):
        """Verify analytics respects days parameter"""
        response = requests.get(f"{BASE_URL}/api/portal/tenant/{TEST_TENANT_CODE}/analytics?days=7")
        assert response.status_code == 200
        
        data = response.json()
        assert "summary" in data
        print(f"✓ Analytics with 7-day filter working")


class TestPortalInvalidTenant:
    """Test all endpoints with invalid tenant code"""
    
    def test_all_endpoints_return_404_for_invalid_tenant(self):
        """Verify all portal endpoints return 404 for invalid tenant"""
        endpoints = [
            f"/api/portal/tenant/{INVALID_TENANT_CODE}",
            f"/api/portal/tenant/{INVALID_TENANT_CODE}/tickets",
            f"/api/portal/tenant/{INVALID_TENANT_CODE}/devices",
            f"/api/portal/tenant/{INVALID_TENANT_CODE}/contracts",
            f"/api/portal/tenant/{INVALID_TENANT_CODE}/profile",
            f"/api/portal/tenant/{INVALID_TENANT_CODE}/analytics",
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code == 404, f"Expected 404 for {endpoint}, got {response.status_code}"
        
        print(f"✓ All {len(endpoints)} endpoints return 404 for invalid tenant")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
