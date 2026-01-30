"""
Multi-Tenant Authentication Tests
=================================
Tests for admin authentication with organization_id in JWT tokens
and tenant-scoped API endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"
EXPECTED_ORG_ID = "112068e7-d4ec-4516-beff-8d3087c51868"


class TestAdminAuthentication:
    """Test admin login returns JWT with organization_id"""
    
    def test_admin_login_returns_token(self):
        """Admin login should return access_token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert "access_token" in data, "Response missing access_token"
        assert "token_type" in data, "Response missing token_type"
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 50, "Token seems too short"
    
    def test_admin_token_contains_organization_id(self):
        """JWT token should contain organization_id for multi-tenant admin"""
        import base64
        import json
        
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        
        token = response.json()["access_token"]
        
        # Decode JWT payload (middle part)
        payload_b64 = token.split('.')[1]
        # Add padding if needed
        payload_b64 += '=' * (4 - len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64))
        
        # Verify organization_id is present
        assert "organization_id" in payload, "Token missing organization_id"
        assert payload["organization_id"] == EXPECTED_ORG_ID, f"Wrong org_id: {payload['organization_id']}"
        
        # Verify org_member_id is present
        assert "org_member_id" in payload, "Token missing org_member_id"
        assert len(payload["org_member_id"]) > 0, "org_member_id is empty"
        
        # Verify type is org_member
        assert payload.get("type") == "org_member", f"Wrong type: {payload.get('type')}"
        
        # Verify role is present
        assert "role" in payload, "Token missing role"
        assert payload["role"] in ["owner", "admin", "member"], f"Invalid role: {payload['role']}"


class TestAuthMeEndpoint:
    """Test /api/auth/me returns organization context"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_auth_me_returns_organization_id(self, auth_token):
        """GET /api/auth/me should return organization_id"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "organization_id" in data, "Response missing organization_id"
        assert data["organization_id"] == EXPECTED_ORG_ID
    
    def test_auth_me_returns_organization_name(self, auth_token):
        """GET /api/auth/me should return organization_name"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "organization_name" in data, "Response missing organization_name"
        assert data["organization_name"] is not None, "organization_name is null"
        assert len(data["organization_name"]) > 0, "organization_name is empty"
    
    def test_auth_me_returns_org_role(self, auth_token):
        """GET /api/auth/me should return org_role"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "org_role" in data, "Response missing org_role"
        assert data["org_role"] in ["owner", "admin", "member"], f"Invalid org_role: {data['org_role']}"


class TestOrgUsageEndpoint:
    """Test /api/org/usage returns tenant usage stats"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_org_usage_returns_usage_stats(self, auth_token):
        """GET /api/org/usage should return usage statistics"""
        response = requests.get(
            f"{BASE_URL}/api/org/usage",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "usage" in data, "Response missing usage"
        
        usage = data["usage"]
        assert "companies" in usage, "Usage missing companies count"
        assert "devices" in usage, "Usage missing devices count"
        assert "users" in usage, "Usage missing users count"
        assert "tickets_this_month" in usage, "Usage missing tickets_this_month"
        
        # Verify counts are integers
        assert isinstance(usage["companies"], int)
        assert isinstance(usage["devices"], int)
        assert isinstance(usage["users"], int)
    
    def test_org_usage_returns_limits(self, auth_token):
        """GET /api/org/usage should return plan limits"""
        response = requests.get(
            f"{BASE_URL}/api/org/usage",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "limits" in data, "Response missing limits"
        assert "plan" in data, "Response missing plan"
        
        limits = data["limits"]
        assert "companies" in limits, "Limits missing companies"
        assert "devices" in limits, "Limits missing devices"


class TestOrgCurrentEndpoint:
    """Test /api/org/current returns tenant organization data"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_org_current_returns_organization(self, auth_token):
        """GET /api/org/current should return organization details"""
        response = requests.get(
            f"{BASE_URL}/api/org/current",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "id" in data, "Response missing id"
        assert "name" in data, "Response missing name"
        assert data["id"] == EXPECTED_ORG_ID, f"Wrong org id: {data['id']}"
    
    def test_org_current_returns_usage(self, auth_token):
        """GET /api/org/current should include usage stats"""
        response = requests.get(
            f"{BASE_URL}/api/org/current",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "usage" in data, "Response missing usage"
        
        usage = data["usage"]
        assert "companies" in usage
        assert "devices" in usage
        assert "users" in usage
    
    def test_org_current_returns_plan_limits(self, auth_token):
        """GET /api/org/current should include plan limits"""
        response = requests.get(
            f"{BASE_URL}/api/org/current",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "plan_limits" in data, "Response missing plan_limits"
        assert "plan_features" in data, "Response missing plan_features"


class TestTenantScopedCompanies:
    """Test /api/admin/companies is scoped to tenant organization_id"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_companies_list_returns_data(self, auth_token):
        """GET /api/admin/companies should return companies"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "No companies returned"
    
    def test_companies_are_scoped_to_organization(self, auth_token):
        """All returned companies should belong to the admin's organization"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies?limit=50",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        companies = response.json()
        
        # Verify all companies have the correct organization_id
        for company in companies:
            org_id = company.get("organization_id")
            # Companies should either have the expected org_id or no org_id (legacy)
            if org_id:
                assert org_id == EXPECTED_ORG_ID, f"Company {company.get('name')} has wrong org_id: {org_id}"


class TestTenantScopedDevices:
    """Test /api/admin/devices is scoped to tenant organization_id"""
    
    @pytest.fixture
    def auth_token(self):
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        return response.json()["access_token"]
    
    def test_devices_list_returns_data(self, auth_token):
        """GET /api/admin/devices should return devices"""
        response = requests.get(
            f"{BASE_URL}/api/admin/devices",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) > 0, "No devices returned"
    
    def test_devices_are_scoped_to_organization(self, auth_token):
        """All returned devices should belong to the admin's organization"""
        response = requests.get(
            f"{BASE_URL}/api/admin/devices?limit=50",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        
        devices = response.json()
        
        # Verify all devices have the correct organization_id
        for device in devices:
            org_id = device.get("organization_id")
            # Devices should either have the expected org_id or no org_id (legacy)
            if org_id:
                assert org_id == EXPECTED_ORG_ID, f"Device {device.get('serial_number')} has wrong org_id: {org_id}"


class TestInvalidAuthentication:
    """Test authentication error handling"""
    
    def test_invalid_credentials_returns_401(self):
        """Invalid credentials should return 401"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "wrong@email.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
    
    def test_missing_token_returns_401(self):
        """Missing auth token should return 401/403"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code in [401, 403]
    
    def test_invalid_token_returns_401(self):
        """Invalid auth token should return 401"""
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        assert response.status_code == 401


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
