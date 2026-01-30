"""
Multi-Tenant SaaS Features Test Suite
=====================================
Tests for:
- 5-tier role system (msp_admin, msp_technician, company_admin, company_employee, external_customer)
- Team Members management
- Custom Domains with DNS verification
- Email White-labeling settings
- Technician Assignments
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_USER_EMAIL = "testowner@example.com"
TEST_USER_PASSWORD = "TestPass123!"


class TestMultiTenantFeatures:
    """Test suite for multi-tenant SaaS features"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.token = None
        self.org_id = None
        
    def get_auth_token(self):
        """Get authentication token"""
        if self.token:
            return self.token
            
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return self.token
        return None
    
    # ==================== API Health Check ====================
    
    def test_api_health(self):
        """Test API is accessible"""
        response = self.session.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        print("✓ API health check passed")
    
    # ==================== Team Members API Tests ====================
    
    def test_get_org_members(self):
        """Test GET /api/org/members returns list of members"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/org/members")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/org/members returned {len(data)} members")
        
        # Verify member structure
        if len(data) > 0:
            member = data[0]
            assert "id" in member
            assert "email" in member
            assert "name" in member
            assert "role" in member
            print(f"✓ Member structure validated: {member.get('email')}")
    
    def test_invite_member(self):
        """Test POST /api/org/members/invite creates invitation"""
        self.get_auth_token()
        
        test_email = f"test_invite_{uuid.uuid4().hex[:8]}@example.com"
        
        response = self.session.post(f"{BASE_URL}/api/org/members/invite", json={
            "email": test_email,
            "name": "TEST_Invited_User",
            "role": "msp_technician",
            "phone": "1234567890"
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "invitation_id" in data
        assert data["email"] == test_email
        assert "expires_at" in data
        print(f"✓ Member invitation created: {data['invitation_id']}")
    
    def test_invite_member_duplicate(self):
        """Test duplicate invitation returns error"""
        self.get_auth_token()
        
        test_email = f"test_dup_{uuid.uuid4().hex[:8]}@example.com"
        
        # First invitation
        response1 = self.session.post(f"{BASE_URL}/api/org/members/invite", json={
            "email": test_email,
            "name": "TEST_Dup_User",
            "role": "company_employee"
        })
        assert response1.status_code == 200
        
        # Second invitation (should fail)
        response2 = self.session.post(f"{BASE_URL}/api/org/members/invite", json={
            "email": test_email,
            "name": "TEST_Dup_User",
            "role": "company_employee"
        })
        assert response2.status_code == 400
        print("✓ Duplicate invitation correctly rejected")
    
    # ==================== Custom Domains API Tests ====================
    
    def test_get_custom_domains(self):
        """Test GET /api/org/custom-domains returns list of domains"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/org/custom-domains")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/org/custom-domains returned {len(data)} domains")
    
    def test_create_custom_domain(self):
        """Test POST /api/org/custom-domains creates domain with verification token"""
        self.get_auth_token()
        
        test_domain = f"test-{uuid.uuid4().hex[:8]}.example.com"
        
        response = self.session.post(f"{BASE_URL}/api/org/custom-domains", json={
            "domain": test_domain
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["domain"] == test_domain
        assert "verification_token" in data
        assert data["verification_token"].startswith("aftersales-verify=")
        assert "verification_instructions" in data
        print(f"✓ Custom domain created: {test_domain}")
        print(f"  Verification token: {data['verification_token']}")
    
    def test_create_duplicate_domain(self):
        """Test duplicate domain returns error"""
        self.get_auth_token()
        
        test_domain = f"dup-{uuid.uuid4().hex[:8]}.example.com"
        
        # First creation
        response1 = self.session.post(f"{BASE_URL}/api/org/custom-domains", json={
            "domain": test_domain
        })
        assert response1.status_code == 200
        
        # Second creation (should fail)
        response2 = self.session.post(f"{BASE_URL}/api/org/custom-domains", json={
            "domain": test_domain
        })
        assert response2.status_code == 400
        print("✓ Duplicate domain correctly rejected")
    
    def test_verify_domain_not_found(self):
        """Test domain verification with non-existent domain"""
        self.get_auth_token()
        
        response = self.session.post(f"{BASE_URL}/api/org/custom-domains/verify", json={
            "domain": "nonexistent.example.com"
        })
        
        assert response.status_code == 404
        print("✓ Non-existent domain verification correctly returns 404")
    
    # ==================== Email Settings API Tests ====================
    
    def test_get_email_settings(self):
        """Test GET /api/org/email-settings returns settings"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/org/email-settings")
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify default settings structure
        assert "email_enabled" in data
        assert "smtp_provider" in data
        assert "smtp_port" in data
        assert "smtp_use_tls" in data
        assert "show_powered_by" in data
        print("✓ GET /api/org/email-settings returned settings")
        print(f"  Email enabled: {data.get('email_enabled')}")
    
    def test_update_email_settings(self):
        """Test PUT /api/org/email-settings updates settings"""
        self.get_auth_token()
        
        response = self.session.put(f"{BASE_URL}/api/org/email-settings", json={
            "email_enabled": True,
            "from_email": "test@example.com",
            "from_name": "Test Sender",
            "smtp_provider": "sendgrid",
            "smtp_host": "smtp.sendgrid.net",
            "smtp_port": 587
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email_enabled"] == True
        assert data["from_email"] == "test@example.com"
        assert data["smtp_provider"] == "sendgrid"
        print("✓ Email settings updated successfully")
        
        # Reset settings
        self.session.put(f"{BASE_URL}/api/org/email-settings", json={
            "email_enabled": False
        })
    
    # ==================== Technician Assignments API Tests ====================
    
    def test_get_technician_assignments(self):
        """Test GET /api/org/technician-assignments returns list"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/org/technician-assignments")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/org/technician-assignments returned {len(data)} assignments")
    
    def test_create_technician_assignment_invalid_technician(self):
        """Test assignment with non-existent technician returns error"""
        self.get_auth_token()
        
        response = self.session.post(f"{BASE_URL}/api/org/technician-assignments", json={
            "technician_id": "nonexistent-id",
            "company_id": "some-company-id"
        })
        
        assert response.status_code == 404
        print("✓ Invalid technician assignment correctly returns 404")
    
    # ==================== Role System Tests ====================
    
    def test_role_definitions_in_members(self):
        """Test that members have valid roles from 5-tier system"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/org/members")
        assert response.status_code == 200
        
        valid_roles = ["msp_admin", "msp_technician", "company_admin", "company_employee", "external_customer", "owner", "admin", "member"]
        
        data = response.json()
        for member in data:
            role = member.get("role")
            # Owner/admin are legacy roles that map to msp_admin
            assert role in valid_roles, f"Invalid role: {role}"
        
        print("✓ All member roles are valid")
    
    # ==================== Organization Current API Tests ====================
    
    def test_get_current_organization(self):
        """Test GET /api/org/current returns organization details"""
        self.get_auth_token()
        
        response = self.session.get(f"{BASE_URL}/api/org/current")
        assert response.status_code == 200
        
        data = response.json()
        
        # Check for organization fields or legacy admin indicator
        if data.get("is_legacy_admin"):
            print("✓ Legacy admin detected (expected for some users)")
        else:
            assert "id" in data or "name" in data
            print(f"✓ Current organization retrieved")
    
    # ==================== Subscription API Tests ====================
    
    def test_get_subscription_plans(self):
        """Test GET /api/org/plans returns available plans"""
        response = self.session.get(f"{BASE_URL}/api/org/plans")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        
        # Verify plan structure
        plan = data[0]
        assert "id" in plan
        assert "name" in plan
        assert "limits" in plan
        print(f"✓ GET /api/org/plans returned {len(data)} plans")
        
        # Check for expected plans
        plan_ids = [p["id"] for p in data]
        expected_plans = ["trial", "starter", "professional", "enterprise"]
        for expected in expected_plans:
            assert expected in plan_ids, f"Missing plan: {expected}"
        print("✓ All expected subscription plans present")


class TestRoleBasedAccess:
    """Test role-based access control"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
    
    def test_unauthenticated_access_denied(self):
        """Test that unauthenticated requests are denied"""
        response = self.session.get(f"{BASE_URL}/api/org/members")
        assert response.status_code in [401, 403]
        print("✓ Unauthenticated access correctly denied")
    
    def test_invalid_token_denied(self):
        """Test that invalid tokens are rejected"""
        self.session.headers.update({"Authorization": "Bearer invalid-token"})
        response = self.session.get(f"{BASE_URL}/api/org/members")
        assert response.status_code in [401, 403]
        print("✓ Invalid token correctly rejected")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
