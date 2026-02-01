"""
Platform Dashboard Stats API Tests
Tests for /api/platform/dashboard/stats endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestPlatformDashboardStats:
    """Tests for Platform Dashboard Stats API"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get platform admin token"""
        # Login as platform admin
        login_response = requests.post(
            f"{BASE_URL}/api/platform/login",
            json={
                "email": "superadmin@platform.com",
                "password": "admin123"
            }
        )
        assert login_response.status_code == 200, f"Platform login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_platform_login_success(self):
        """Test platform admin login with correct credentials"""
        response = requests.post(
            f"{BASE_URL}/api/platform/login",
            json={
                "email": "superadmin@platform.com",
                "password": "admin123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["admin"]["email"] == "superadmin@platform.com"
        print("SUCCESS: Platform login works with superadmin@platform.com / admin123")
    
    def test_platform_login_invalid_credentials(self):
        """Test platform admin login with wrong credentials"""
        response = requests.post(
            f"{BASE_URL}/api/platform/login",
            json={
                "email": "superadmin@platform.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
        print("SUCCESS: Invalid credentials return 401")
    
    def test_dashboard_stats_endpoint_exists(self):
        """Test that dashboard stats endpoint exists and returns data"""
        response = requests.get(
            f"{BASE_URL}/api/platform/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "totals" in data
        assert "revenue" in data
        assert "growth" in data
        assert "organizations_by_status" in data
        assert "organizations_by_plan" in data
        assert "recent_organizations" in data
        print("SUCCESS: Dashboard stats endpoint returns correct structure")
    
    def test_dashboard_stats_totals(self):
        """Test that totals section has correct fields"""
        response = requests.get(
            f"{BASE_URL}/api/platform/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        totals = data["totals"]
        assert "organizations" in totals
        assert "companies" in totals
        assert "devices" in totals
        assert "users" in totals
        assert "tickets" in totals
        
        # Verify organizations count is 6
        assert totals["organizations"] == 6, f"Expected 6 organizations, got {totals['organizations']}"
        print(f"SUCCESS: Total organizations = {totals['organizations']}")
    
    def test_dashboard_stats_organizations_by_status(self):
        """Test organizations by status shows trial count"""
        response = requests.get(
            f"{BASE_URL}/api/platform/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        org_by_status = data["organizations_by_status"]
        assert "trial" in org_by_status
        assert "active" in org_by_status
        
        # Verify trial count is 5
        assert org_by_status["trial"] == 5, f"Expected 5 trial orgs, got {org_by_status['trial']}"
        print(f"SUCCESS: Trial organizations = {org_by_status['trial']}")
    
    def test_dashboard_stats_organizations_by_plan(self):
        """Test organizations by plan shows correct counts"""
        response = requests.get(
            f"{BASE_URL}/api/platform/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        org_by_plan = data["organizations_by_plan"]
        assert "trial" in org_by_plan
        assert "starter" in org_by_plan
        assert "professional" in org_by_plan
        assert "enterprise" in org_by_plan
        
        # Verify trial plan count is 6
        assert org_by_plan["trial"] == 6, f"Expected 6 trial plan orgs, got {org_by_plan['trial']}"
        print(f"SUCCESS: Organizations with trial plan = {org_by_plan['trial']}")
    
    def test_dashboard_stats_recent_organizations(self):
        """Test recent organizations list"""
        response = requests.get(
            f"{BASE_URL}/api/platform/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        recent_orgs = data["recent_organizations"]
        assert isinstance(recent_orgs, list)
        assert len(recent_orgs) <= 5  # Should return max 5 recent orgs
        
        if len(recent_orgs) > 0:
            org = recent_orgs[0]
            assert "id" in org
            assert "name" in org
            assert "slug" in org
            assert "status" in org
            assert "created_at" in org
        print(f"SUCCESS: Recent organizations returned {len(recent_orgs)} items")
    
    def test_dashboard_stats_requires_auth(self):
        """Test that dashboard stats requires authentication"""
        response = requests.get(f"{BASE_URL}/api/platform/dashboard/stats")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("SUCCESS: Dashboard stats requires authentication")
    
    def test_dashboard_stats_revenue_section(self):
        """Test revenue section in dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/platform/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        revenue = data["revenue"]
        assert "mrr" in revenue
        assert "arr" in revenue
        assert "paid_organizations" in revenue
        print(f"SUCCESS: Revenue section - MRR: {revenue['mrr']}, ARR: {revenue['arr']}")
    
    def test_dashboard_stats_growth_section(self):
        """Test growth section in dashboard stats"""
        response = requests.get(
            f"{BASE_URL}/api/platform/dashboard/stats",
            headers=self.headers
        )
        assert response.status_code == 200
        data = response.json()
        
        growth = data["growth"]
        assert "new_this_month" in growth
        assert "trial_conversion_rate" in growth
        print(f"SUCCESS: Growth section - New this month: {growth['new_this_month']}, Conversion rate: {growth['trial_conversion_rate']}%")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
