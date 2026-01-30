"""
Subdomain-based Multi-tenancy Tests
====================================
Tests for tenant context resolution, tenant-aware login, and cross-tenant protection.

Tenants:
- acme-corporation: admin@demo.com is owner
- demo-saas: saas@demo.com is owner

Resolution Priority:
1. X-Tenant-Slug header
2. ?_tenant query param
3. Host header subdomain
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestTenantContext:
    """Tests for /api/tenant/context endpoint"""
    
    def test_tenant_context_no_context(self):
        """GET /api/tenant/context without any tenant context should return null tenant"""
        response = requests.get(f"{BASE_URL}/api/tenant/context")
        assert response.status_code == 200
        
        data = response.json()
        assert data["tenant"] is None
        assert data["resolution"] is None
        assert "message" in data
        print(f"✓ No tenant context returns null tenant: {data['message']}")
    
    def test_tenant_context_with_query_param(self):
        """GET /api/tenant/context?_tenant=acme-corporation should return tenant info"""
        response = requests.get(f"{BASE_URL}/api/tenant/context?_tenant=acme-corporation")
        assert response.status_code == 200
        
        data = response.json()
        assert data["tenant"] is not None
        assert data["tenant"]["slug"] == "acme-corporation"
        assert data["tenant"]["name"] == "Acme Corporation"
        assert data["resolution"] == "query_param"
        
        # Verify branding structure
        branding = data["tenant"]["branding"]
        assert "accent_color" in branding
        assert "company_name" in branding
        print(f"✓ Query param resolution works: {data['tenant']['name']}")
    
    def test_tenant_context_with_header(self):
        """GET /api/tenant/context with X-Tenant-Slug header should return tenant info"""
        headers = {"X-Tenant-Slug": "acme-corporation"}
        response = requests.get(f"{BASE_URL}/api/tenant/context", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["tenant"] is not None
        assert data["tenant"]["slug"] == "acme-corporation"
        assert data["resolution"] == "header"
        print(f"✓ Header resolution works: {data['tenant']['name']}")
    
    def test_tenant_context_invalid_slug(self):
        """GET /api/tenant/context?_tenant=nonexistent should return null tenant"""
        response = requests.get(f"{BASE_URL}/api/tenant/context?_tenant=nonexistent")
        assert response.status_code == 200
        
        data = response.json()
        assert data["tenant"] is None
        print("✓ Invalid tenant slug returns null tenant")


class TestTenantVerify:
    """Tests for /api/tenant/verify/{slug} endpoint"""
    
    def test_verify_existing_tenant(self):
        """GET /api/tenant/verify/acme-corporation should return exists=true"""
        response = requests.get(f"{BASE_URL}/api/tenant/verify/acme-corporation")
        assert response.status_code == 200
        
        data = response.json()
        assert data["exists"] is True
        assert data["slug"] == "acme-corporation"
        assert data["name"] == "Acme Corporation"
        print(f"✓ Existing tenant verified: {data['name']}")
    
    def test_verify_nonexistent_tenant(self):
        """GET /api/tenant/verify/nonexistent should return exists=false"""
        response = requests.get(f"{BASE_URL}/api/tenant/verify/nonexistent")
        assert response.status_code == 200
        
        data = response.json()
        assert data["exists"] is False
        assert data["slug"] == "nonexistent"
        print("✓ Nonexistent tenant returns exists=false")
    
    def test_verify_demo_saas_tenant(self):
        """GET /api/tenant/verify/demo-saas should return exists=true"""
        response = requests.get(f"{BASE_URL}/api/tenant/verify/demo-saas")
        assert response.status_code == 200
        
        data = response.json()
        assert data["exists"] is True
        assert data["slug"] == "demo-saas"
        assert data["name"] == "Demo SaaS Tenant"
        print(f"✓ Demo SaaS tenant verified: {data['name']}")


class TestTenantAwareLogin:
    """Tests for tenant-aware login at /api/auth/login"""
    
    def test_login_with_correct_tenant(self):
        """POST /api/auth/login?_tenant=acme-corporation with admin@demo.com should succeed"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login?_tenant=acme-corporation",
            json={"email": "admin@demo.com", "password": "admin123"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print("✓ Tenant-aware login successful for admin@demo.com in acme-corporation")
    
    def test_cross_tenant_login_blocked(self):
        """POST /api/auth/login?_tenant=demo-saas with admin@demo.com should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login?_tenant=demo-saas",
            json={"email": "admin@demo.com", "password": "admin123"}
        )
        assert response.status_code == 401
        
        data = response.json()
        assert data["detail"] == "Invalid credentials"
        print("✓ Cross-tenant login blocked - returns generic 'Invalid credentials'")
    
    def test_login_with_header_tenant(self):
        """POST /api/auth/login with X-Tenant-Slug header should work"""
        headers = {"X-Tenant-Slug": "acme-corporation", "Content-Type": "application/json"}
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            headers=headers,
            json={"email": "admin@demo.com", "password": "admin123"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        print("✓ Login with X-Tenant-Slug header works")
    
    def test_login_without_tenant_context(self):
        """POST /api/auth/login without tenant context should work for valid user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": "admin@demo.com", "password": "admin123"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        print("✓ Login without tenant context works for valid user")
    
    def test_login_invalid_credentials(self):
        """POST /api/auth/login with wrong password should fail"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login?_tenant=acme-corporation",
            json={"email": "admin@demo.com", "password": "wrongpassword"}
        )
        assert response.status_code == 401
        
        data = response.json()
        assert data["detail"] == "Invalid credentials"
        print("✓ Invalid password returns 401")


class TestPlatformRoutes:
    """Tests for platform admin routes - should not be affected by tenant context"""
    
    def test_platform_login_works(self):
        """POST /api/platform/login should work without tenant context"""
        response = requests.post(
            f"{BASE_URL}/api/platform/login",
            json={"email": "superadmin@platform.com", "password": "SuperAdmin@123"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        assert data["admin"]["email"] == "superadmin@platform.com"
        print("✓ Platform login works without tenant context")
    
    def test_platform_login_with_tenant_param_ignored(self):
        """POST /api/platform/login?_tenant=acme-corporation should still work"""
        response = requests.post(
            f"{BASE_URL}/api/platform/login?_tenant=acme-corporation",
            json={"email": "superadmin@platform.com", "password": "SuperAdmin@123"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "access_token" in data
        print("✓ Platform login ignores tenant context")


class TestTenantMiddleware:
    """Tests for tenant middleware behavior"""
    
    def test_public_routes_work_without_tenant(self):
        """Public routes should work without tenant context"""
        # Test root endpoint
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        
        # Test public settings
        response = requests.get(f"{BASE_URL}/api/settings/public")
        assert response.status_code == 200
        
        # Test security info
        response = requests.get(f"{BASE_URL}/api/security/info")
        assert response.status_code == 200
        
        print("✓ Public routes work without tenant context")
    
    def test_public_masters_work_without_tenant(self):
        """GET /api/masters/public should work without tenant"""
        response = requests.get(f"{BASE_URL}/api/masters/public")
        assert response.status_code == 200
        print("✓ Public masters endpoint works")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
