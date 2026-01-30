"""
Platform Super Admin API Tests
==============================
Tests for platform-level administration endpoints including:
- Platform login/authentication
- Dashboard stats with revenue metrics
- Organizations management (CRUD, plan changes)
- Platform admins management
- Audit logs
- Platform settings
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
PLATFORM_ADMIN_EMAIL = "superadmin@platform.com"
PLATFORM_ADMIN_PASSWORD = "SuperAdmin@123"


class TestPlatformAuth:
    """Platform authentication tests"""
    
    def test_platform_login_success(self):
        """Test successful platform admin login"""
        response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data
        assert "token_type" in data
        assert "admin" in data
        assert data["token_type"] == "bearer"
        
        # Verify admin data
        assert data["admin"]["email"] == PLATFORM_ADMIN_EMAIL
        assert "id" in data["admin"]
        assert "name" in data["admin"]
        assert "role" in data["admin"]
        print(f"SUCCESS: Platform login - Admin: {data['admin']['name']}, Role: {data['admin']['role']}")
    
    def test_platform_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": "wrong@platform.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        print("SUCCESS: Invalid credentials correctly rejected")
    
    def test_platform_me_endpoint(self):
        """Test /me endpoint returns current admin info"""
        # First login
        login_response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        token = login_response.json()["access_token"]
        
        # Get current admin info
        response = requests.get(f"{BASE_URL}/api/platform/me", headers={
            "Authorization": f"Bearer {token}"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == PLATFORM_ADMIN_EMAIL
        print(f"SUCCESS: /me endpoint - Admin: {data['name']}")


class TestPlatformDashboard:
    """Dashboard stats tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_dashboard_stats_returns_revenue_metrics(self):
        """Test dashboard stats includes MRR, ARR, growth metrics"""
        response = requests.get(f"{BASE_URL}/api/platform/dashboard/stats", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify totals section
        assert "totals" in data
        assert "organizations" in data["totals"]
        assert "companies" in data["totals"]
        assert "devices" in data["totals"]
        assert "users" in data["totals"]
        assert "tickets" in data["totals"]
        
        # Verify revenue section (MRR/ARR)
        assert "revenue" in data
        assert "mrr" in data["revenue"]
        assert "arr" in data["revenue"]
        assert "paid_organizations" in data["revenue"]
        
        # Verify growth section
        assert "growth" in data
        assert "new_this_month" in data["growth"]
        assert "trial_conversion_rate" in data["growth"]
        
        # Verify organizations breakdown
        assert "organizations_by_status" in data
        assert "organizations_by_plan" in data
        
        # Verify recent organizations
        assert "recent_organizations" in data
        
        print(f"SUCCESS: Dashboard stats - MRR: ₹{data['revenue']['mrr']}, ARR: ₹{data['revenue']['arr']}")
        print(f"  Organizations: {data['totals']['organizations']}, Conversion Rate: {data['growth']['trial_conversion_rate']}%")
    
    def test_dashboard_stats_unauthorized(self):
        """Test dashboard stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/platform/dashboard/stats")
        assert response.status_code in [401, 403]
        print("SUCCESS: Dashboard stats correctly requires authentication")


class TestPlatformOrganizations:
    """Organizations management tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_organizations(self):
        """Test listing all organizations"""
        response = requests.get(f"{BASE_URL}/api/platform/organizations", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "organizations" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        
        # Verify organization structure if any exist
        if data["organizations"]:
            org = data["organizations"][0]
            assert "id" in org
            assert "name" in org
            assert "status" in org
            assert "subscription" in org
            assert "stats" in org  # Usage stats
            print(f"SUCCESS: Listed {len(data['organizations'])} organizations (total: {data['total']})")
        else:
            print("SUCCESS: Organizations list returned (empty)")
    
    def test_list_organizations_with_status_filter(self):
        """Test filtering organizations by status"""
        response = requests.get(f"{BASE_URL}/api/platform/organizations?status=active", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned orgs should have active status
        for org in data["organizations"]:
            assert org["status"] == "active"
        print(f"SUCCESS: Status filter works - {len(data['organizations'])} active organizations")
    
    def test_get_organization_details(self):
        """Test getting detailed organization info"""
        # First get list to find an org
        list_response = requests.get(f"{BASE_URL}/api/platform/organizations", headers=self.headers)
        orgs = list_response.json()["organizations"]
        
        if not orgs:
            pytest.skip("No organizations to test")
        
        org_id = orgs[0]["id"]
        response = requests.get(f"{BASE_URL}/api/platform/organizations/{org_id}", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "organization" in data
        assert "members" in data
        assert "stats" in data
        assert "plan_config" in data
        
        # Verify stats structure
        assert "companies" in data["stats"]
        assert "devices" in data["stats"]
        assert "users" in data["stats"]
        
        print(f"SUCCESS: Got details for '{data['organization']['name']}' - {len(data['members'])} members")
    
    def test_update_organization_plan(self):
        """Test changing organization plan"""
        # First get list to find an org
        list_response = requests.get(f"{BASE_URL}/api/platform/organizations", headers=self.headers)
        orgs = list_response.json()["organizations"]
        
        if not orgs:
            pytest.skip("No organizations to test")
        
        org_id = orgs[0]["id"]
        original_plan = orgs[0].get("subscription", {}).get("plan", "trial")
        
        # Change to professional plan
        new_plan = "professional" if original_plan != "professional" else "starter"
        response = requests.put(
            f"{BASE_URL}/api/platform/organizations/{org_id}",
            params={"plan": new_plan},
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["subscription"]["plan"] == new_plan
        
        # Verify change persisted
        get_response = requests.get(f"{BASE_URL}/api/platform/organizations/{org_id}", headers=self.headers)
        assert get_response.json()["organization"]["subscription"]["plan"] == new_plan
        
        # Restore original plan
        requests.put(
            f"{BASE_URL}/api/platform/organizations/{org_id}",
            params={"plan": original_plan},
            headers=self.headers
        )
        
        print(f"SUCCESS: Plan change works - Changed from {original_plan} to {new_plan} and back")
    
    def test_organization_not_found(self):
        """Test 404 for non-existent organization"""
        response = requests.get(f"{BASE_URL}/api/platform/organizations/non-existent-id", headers=self.headers)
        assert response.status_code == 404
        print("SUCCESS: 404 returned for non-existent organization")


class TestPlatformAdmins:
    """Platform admins management tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_platform_admins(self):
        """Test listing all platform admins"""
        response = requests.get(f"{BASE_URL}/api/platform/admins", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) >= 1  # At least the super admin
        
        # Verify admin structure
        admin = data[0]
        assert "id" in admin
        assert "email" in admin
        assert "name" in admin
        assert "role" in admin
        assert "password_hash" not in admin  # Should not expose password
        
        print(f"SUCCESS: Listed {len(data)} platform admins")


class TestPlatformAuditLogs:
    """Audit logs tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_audit_logs(self):
        """Test getting audit logs"""
        response = requests.get(f"{BASE_URL}/api/platform/audit-logs", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "total" in data
        assert "page" in data
        assert "pages" in data
        
        print(f"SUCCESS: Audit logs - {data['total']} total entries")
    
    def test_audit_logs_with_action_filter(self):
        """Test filtering audit logs by action"""
        response = requests.get(
            f"{BASE_URL}/api/platform/audit-logs?action=update_organization",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned logs should have the specified action
        for log in data["logs"]:
            assert log["action"] == "update_organization"
        
        print(f"SUCCESS: Action filter works - {len(data['logs'])} update_organization logs")
    
    def test_audit_logs_with_entity_type_filter(self):
        """Test filtering audit logs by entity type"""
        response = requests.get(
            f"{BASE_URL}/api/platform/audit-logs?entity_type=organization",
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # All returned logs should have the specified entity type
        for log in data["logs"]:
            assert log["entity_type"] == "organization"
        
        print(f"SUCCESS: Entity type filter works - {len(data['logs'])} organization logs")


class TestPlatformSettings:
    """Platform settings tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before each test"""
        login_response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_platform_settings(self):
        """Test getting platform settings"""
        response = requests.get(f"{BASE_URL}/api/platform/settings", headers=self.headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify settings structure
        assert "id" in data
        assert "platform_name" in data
        assert "default_trial_days" in data
        assert "allow_self_signup" in data
        
        print(f"SUCCESS: Platform settings - Name: {data['platform_name']}, Trial Days: {data['default_trial_days']}")
    
    def test_update_platform_settings(self):
        """Test updating platform settings"""
        # Get current settings
        get_response = requests.get(f"{BASE_URL}/api/platform/settings", headers=self.headers)
        original_settings = get_response.json()
        original_trial_days = original_settings.get("default_trial_days", 14)
        
        # Update trial days
        new_trial_days = 21 if original_trial_days != 21 else 14
        response = requests.put(
            f"{BASE_URL}/api/platform/settings",
            json={"default_trial_days": new_trial_days},
            headers=self.headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["default_trial_days"] == new_trial_days
        
        # Restore original
        requests.put(
            f"{BASE_URL}/api/platform/settings",
            json={"default_trial_days": original_trial_days},
            headers=self.headers
        )
        
        print(f"SUCCESS: Settings update works - Changed trial days from {original_trial_days} to {new_trial_days}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
