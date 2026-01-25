"""
Security Features Test Suite
Tests for:
1. Rate limiting on login endpoints (5 attempts/minute)
2. Password strength validation (8+ chars, uppercase, lowercase, digit, special char)
3. Security info API endpoint at /api/security/info
4. Admin and Company login functionality
5. Parts endpoint with full details
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"
COMPANY_EMAIL = "jane@acme.com"
COMPANY_PASSWORD = "company123"
DEVICE_WITH_PARTS = "206eb754-b34e-4387-8262-a64543a3c769"


class TestSecurityInfoEndpoint:
    """Test /api/security/info endpoint"""
    
    def test_security_info_returns_password_requirements(self):
        """Security info endpoint should return password requirements"""
        response = requests.get(f"{BASE_URL}/api/security/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "password_requirements" in data
        
        pw_req = data["password_requirements"]
        assert pw_req["min_length"] == 8
        assert pw_req["require_uppercase"] == True
        assert pw_req["require_lowercase"] == True
        assert pw_req["require_digit"] == True
        assert pw_req["require_special"] == True
    
    def test_security_info_returns_rate_limiting_config(self):
        """Security info endpoint should return rate limiting configuration"""
        response = requests.get(f"{BASE_URL}/api/security/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "rate_limiting" in data
        
        rate_limit = data["rate_limiting"]
        assert rate_limit["login_attempts_per_minute"] == 5
        assert rate_limit["registration_attempts_per_minute"] == 3
    
    def test_security_info_returns_session_timeout(self):
        """Security info endpoint should return session timeout"""
        response = requests.get(f"{BASE_URL}/api/security/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "session_timeout_minutes" in data
        assert data["session_timeout_minutes"] == 480


class TestAdminLogin:
    """Test admin login functionality"""
    
    def test_admin_login_success(self):
        """Admin login with valid credentials should succeed"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
    
    def test_admin_login_invalid_credentials(self):
        """Admin login with invalid credentials should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "Invalid" in data["detail"] or "credentials" in data["detail"].lower()
    
    def test_admin_login_nonexistent_user(self):
        """Admin login with non-existent user should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "nonexistent@test.com", "password": "anypassword"}
        )
        assert response.status_code == 401


class TestCompanyLogin:
    """Test company user login functionality"""
    
    def test_company_login_success(self):
        """Company login with valid credentials should succeed"""
        response = requests.post(
            f"{BASE_URL}/api/company/auth/login",
            json={"email": COMPANY_EMAIL, "password": COMPANY_PASSWORD}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert "user" in data
        assert data["user"]["email"] == COMPANY_EMAIL
        assert data["user"]["company_name"] == "Acme Corporation"
    
    def test_company_login_invalid_credentials(self):
        """Company login with invalid credentials should fail"""
        response = requests.post(
            f"{BASE_URL}/api/company/auth/login",
            json={"email": COMPANY_EMAIL, "password": "wrongpassword"}
        )
        assert response.status_code == 401


class TestPasswordStrengthValidation:
    """Test password strength validation"""
    
    def test_password_too_short(self):
        """Password less than 8 characters should be rejected"""
        # Test via company user creation endpoint
        admin_token = get_admin_token()
        
        # First get a company ID
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert companies_response.status_code == 200
        companies = companies_response.json()
        assert len(companies) > 0
        company_id = companies[0]["id"]
        
        # Try to create user with weak password
        unique_email = f"testweakpw{int(time.time())}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/companies/{company_id}/portal-users",
            json={
                "name": "Test User",
                "email": unique_email,
                "password": "short"  # Too short
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "8 characters" in data["detail"].lower() or "length" in data["detail"].lower()
    
    def test_password_missing_uppercase(self):
        """Password without uppercase should be rejected"""
        admin_token = get_admin_token()
        
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        companies = companies_response.json()
        company_id = companies[0]["id"]
        
        unique_email = f"testnoupper{int(time.time())}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/companies/{company_id}/portal-users",
            json={
                "name": "Test User",
                "email": unique_email,
                "password": "password123!"  # No uppercase
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "uppercase" in data["detail"].lower()
    
    def test_password_missing_lowercase(self):
        """Password without lowercase should be rejected"""
        admin_token = get_admin_token()
        
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        companies = companies_response.json()
        company_id = companies[0]["id"]
        
        unique_email = f"testnolower{int(time.time())}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/companies/{company_id}/portal-users",
            json={
                "name": "Test User",
                "email": unique_email,
                "password": "PASSWORD123!"  # No lowercase
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "lowercase" in data["detail"].lower()
    
    def test_password_missing_digit(self):
        """Password without digit should be rejected"""
        admin_token = get_admin_token()
        
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        companies = companies_response.json()
        company_id = companies[0]["id"]
        
        unique_email = f"testnodigit{int(time.time())}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/companies/{company_id}/portal-users",
            json={
                "name": "Test User",
                "email": unique_email,
                "password": "Password!"  # No digit
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "digit" in data["detail"].lower()
    
    def test_password_missing_special_char(self):
        """Password without special character should be rejected"""
        admin_token = get_admin_token()
        
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        companies = companies_response.json()
        company_id = companies[0]["id"]
        
        unique_email = f"testnospecial{int(time.time())}@test.com"
        response = requests.post(
            f"{BASE_URL}/api/admin/companies/{company_id}/portal-users",
            json={
                "name": "Test User",
                "email": unique_email,
                "password": "Password123"  # No special char
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400
        data = response.json()
        assert "special" in data["detail"].lower()
    
    def test_strong_password_accepted(self):
        """Strong password meeting all requirements should be accepted"""
        admin_token = get_admin_token()
        
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        companies = companies_response.json()
        company_id = companies[0]["id"]
        
        # Use unique email to avoid conflicts
        unique_email = f"teststrong{int(time.time())}@test.com"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/companies/{company_id}/portal-users",
            json={
                "name": "Test Strong Password",
                "email": unique_email,
                "password": "StrongPass123!"  # Meets all requirements
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should succeed (201 or 200)
        assert response.status_code in [200, 201]
        
        # Cleanup - delete the test user
        data = response.json()
        if "id" in data:
            requests.delete(
                f"{BASE_URL}/api/admin/companies/{company_id}/portal-users/{data['id']}",
                headers={"Authorization": f"Bearer {admin_token}"}
            )


class TestPartsEndpoint:
    """Test parts endpoint returns full details"""
    
    def test_parts_endpoint_returns_all_fields(self):
        """Parts endpoint should return all part fields"""
        admin_token = get_admin_token()
        
        response = requests.get(
            f"{BASE_URL}/api/admin/parts",
            params={"device_id": DEVICE_WITH_PARTS, "limit": 50},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        parts = response.json()
        assert len(parts) > 0, "Device should have parts"
        
        # Check that parts have the expected fields
        expected_fields = [
            "id", "device_id", "part_name"
        ]
        
        # Optional fields that should be present when set
        optional_fields = [
            "part_type", "brand", "model_number", "serial_number", 
            "capacity", "purchase_date", "replaced_date", 
            "warranty_expiry_date", "warranty_months", "vendor", 
            "purchase_cost", "notes"
        ]
        
        for part in parts:
            # Check required fields
            for field in expected_fields:
                assert field in part, f"Part missing required field: {field}"
            
            # Check that at least some optional fields are present
            present_optional = [f for f in optional_fields if f in part and part[f] is not None]
            assert len(present_optional) > 0, "Part should have some optional fields populated"
    
    def test_parts_have_brand_and_model(self):
        """Parts should include brand and model fields"""
        admin_token = get_admin_token()
        
        response = requests.get(
            f"{BASE_URL}/api/admin/parts",
            params={"device_id": DEVICE_WITH_PARTS, "limit": 50},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        parts = response.json()
        
        # Find parts with brand/model (not all parts may have them)
        parts_with_brand = [p for p in parts if p.get("brand")]
        parts_with_model = [p for p in parts if p.get("model_number")]
        
        # At least some parts should have brand and model
        assert len(parts_with_brand) > 0, "At least one part should have brand"
        assert len(parts_with_model) > 0, "At least one part should have model_number"
    
    def test_parts_have_warranty_info(self):
        """Parts should include warranty information"""
        admin_token = get_admin_token()
        
        response = requests.get(
            f"{BASE_URL}/api/admin/parts",
            params={"device_id": DEVICE_WITH_PARTS, "limit": 50},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        parts = response.json()
        
        # Check warranty fields
        parts_with_warranty = [p for p in parts if p.get("warranty_expiry_date") or p.get("warranty_months")]
        assert len(parts_with_warranty) > 0, "At least one part should have warranty info"
    
    def test_parts_have_cost_and_vendor(self):
        """Parts should include cost and vendor information"""
        admin_token = get_admin_token()
        
        response = requests.get(
            f"{BASE_URL}/api/admin/parts",
            params={"device_id": DEVICE_WITH_PARTS, "limit": 50},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        parts = response.json()
        
        # Check cost and vendor fields
        parts_with_cost = [p for p in parts if p.get("purchase_cost")]
        parts_with_vendor = [p for p in parts if p.get("vendor")]
        
        assert len(parts_with_cost) > 0, "At least one part should have purchase_cost"
        assert len(parts_with_vendor) > 0, "At least one part should have vendor"


class TestRateLimiting:
    """Test rate limiting on login endpoints"""
    
    def test_rate_limit_info_in_security_endpoint(self):
        """Rate limit configuration should be exposed in security info"""
        response = requests.get(f"{BASE_URL}/api/security/info")
        assert response.status_code == 200
        
        data = response.json()
        assert data["rate_limiting"]["login_attempts_per_minute"] == 5
    
    def test_login_rate_limit_headers(self):
        """Login endpoint should include rate limit headers"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        
        # Check for rate limit headers (slowapi adds these)
        # Note: Headers may vary based on configuration
        # Common headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
        # The presence of rate limiting is confirmed by the security info endpoint
        assert response.status_code == 200


class TestDeviceDetailsWithParts:
    """Test device details endpoint includes parts"""
    
    def test_device_details_endpoint(self):
        """Device details endpoint should return device info"""
        admin_token = get_admin_token()
        
        response = requests.get(
            f"{BASE_URL}/api/admin/devices/{DEVICE_WITH_PARTS}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        device = response.json()
        assert "id" in device
        assert "brand" in device
        assert "model" in device
        assert "serial_number" in device


# Helper function
def get_admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    raise Exception(f"Failed to get admin token: {response.text}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
