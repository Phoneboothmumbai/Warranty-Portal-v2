"""
Plan Management System Tests
============================
Tests for dynamic plan management including:
- Public plans API (no auth)
- Platform admin plan CRUD
- Plan seeding
- Audit logging
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://mspsaas.preview.emergentagent.com').rstrip('/')

# Platform admin credentials
PLATFORM_ADMIN_EMAIL = "superadmin@platform.com"
PLATFORM_ADMIN_PASSWORD = "SuperAdmin@123"


class TestPublicPlansAPI:
    """Tests for public plans endpoint (no auth required)"""
    
    def test_public_plans_returns_list(self):
        """GET /api/public/plans returns list of plans without auth"""
        response = requests.get(f"{BASE_URL}/api/public/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) >= 1, "Should have at least one plan"
    
    def test_public_plans_structure(self):
        """Verify plan structure has required fields"""
        response = requests.get(f"{BASE_URL}/api/public/plans")
        assert response.status_code == 200
        
        plans = response.json()
        assert len(plans) > 0, "Should have plans"
        
        plan = plans[0]
        # Required fields
        required_fields = ['id', 'name', 'slug', 'price_monthly', 'price_yearly', 
                          'features', 'limits', 'status', 'is_public']
        for field in required_fields:
            assert field in plan, f"Plan missing required field: {field}"
    
    def test_public_plans_only_active_public(self):
        """Public API should only return active, public plans"""
        response = requests.get(f"{BASE_URL}/api/public/plans")
        assert response.status_code == 200
        
        plans = response.json()
        for plan in plans:
            assert plan.get('status') == 'active', f"Plan {plan.get('name')} should be active"
            assert plan.get('is_public') == True, f"Plan {plan.get('name')} should be public"
    
    def test_public_plans_has_default_plans(self):
        """Verify default plans exist: Free Trial, Starter, Professional, Enterprise"""
        response = requests.get(f"{BASE_URL}/api/public/plans")
        assert response.status_code == 200
        
        plans = response.json()
        plan_names = [p.get('name') for p in plans]
        
        expected_plans = ['Free Trial', 'Starter', 'Professional', 'Enterprise']
        for expected in expected_plans:
            assert expected in plan_names, f"Missing expected plan: {expected}"
    
    def test_public_plans_pricing_correct(self):
        """Verify pricing is correct for default plans"""
        response = requests.get(f"{BASE_URL}/api/public/plans")
        assert response.status_code == 200
        
        plans = response.json()
        plans_by_slug = {p.get('slug'): p for p in plans}
        
        # Free Trial should be free
        if 'free-trial' in plans_by_slug:
            assert plans_by_slug['free-trial']['price_monthly'] == 0
            assert plans_by_slug['free-trial']['is_trial'] == True
        
        # Starter should be ₹2,999/month (299900 paise)
        if 'starter' in plans_by_slug:
            assert plans_by_slug['starter']['price_monthly'] == 299900
        
        # Professional should be ₹7,999/month (799900 paise)
        if 'professional' in plans_by_slug:
            assert plans_by_slug['professional']['price_monthly'] == 799900
            assert plans_by_slug['professional']['is_popular'] == True


class TestPlatformAdminAuth:
    """Tests for platform admin authentication"""
    
    @pytest.fixture
    def platform_token(self):
        """Get platform admin token"""
        response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Platform admin login failed: {response.status_code}")
        return response.json().get('access_token')
    
    def test_platform_login_success(self):
        """Platform admin can login successfully"""
        response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        
        data = response.json()
        assert 'access_token' in data, "Response should contain access_token"
        assert data.get('token_type') == 'bearer'
        assert 'admin' in data, "Response should contain admin info"
    
    def test_platform_login_invalid_credentials(self):
        """Invalid credentials should return 401"""
        response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": "wrong@email.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestPlatformPlansAPI:
    """Tests for platform admin plan management APIs"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authenticated headers for platform admin"""
        response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Platform admin login failed")
        token = response.json().get('access_token')
        return {"Authorization": f"Bearer {token}"}
    
    def test_get_platform_plans(self, auth_headers):
        """GET /api/platform/plans returns plans with customer counts"""
        response = requests.get(f"{BASE_URL}/api/platform/plans", headers=auth_headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        plans = response.json()
        assert isinstance(plans, list), "Response should be a list"
        
        # Each plan should have used_by_count
        for plan in plans:
            assert 'used_by_count' in plan, f"Plan {plan.get('name')} missing used_by_count"
            assert isinstance(plan['used_by_count'], int)
    
    def test_get_plan_metadata(self, auth_headers):
        """GET /api/platform/plans/metadata returns feature and limit metadata"""
        response = requests.get(f"{BASE_URL}/api/platform/plans/metadata", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert 'features' in data, "Response should contain features metadata"
        assert 'limits' in data, "Response should contain limits metadata"
        
        # Verify feature metadata structure
        features = data['features']
        assert len(features) > 0, "Should have feature metadata"
        
        # Check a known feature
        if 'ticketing' in features:
            assert 'name' in features['ticketing']
            assert 'category' in features['ticketing']
    
    def test_create_plan(self, auth_headers):
        """POST /api/platform/plans creates a new plan"""
        unique_slug = f"test-plan-{uuid.uuid4().hex[:8]}"
        
        new_plan = {
            "name": "Test Plan",
            "slug": unique_slug,
            "tagline": "For testing purposes",
            "description": "A test plan created by automated tests",
            "price_monthly": 99900,  # ₹999
            "price_yearly": 999000,  # ₹9,990
            "currency": "INR",
            "display_order": 99,
            "is_popular": False,
            "is_public": False,  # Keep hidden
            "color": "#ff0000",
            "status": "draft",
            "features": {
                "ticketing": True,
                "device_management": True
            },
            "limits": {
                "max_companies": 3,
                "max_devices": 50,
                "max_users": 5
            },
            "support_level": "email",
            "response_time_hours": 48,
            "is_trial": False,
            "trial_days": 0
        }
        
        response = requests.post(f"{BASE_URL}/api/platform/plans", json=new_plan, headers=auth_headers)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        created = response.json()
        assert created.get('name') == "Test Plan"
        assert created.get('slug') == unique_slug
        assert created.get('price_monthly') == 99900
        assert 'id' in created, "Created plan should have an ID"
        
        # Cleanup - delete the test plan
        plan_id = created.get('id')
        if plan_id:
            requests.delete(f"{BASE_URL}/api/platform/plans/{plan_id}", headers=auth_headers)
    
    def test_create_plan_duplicate_slug_fails(self, auth_headers):
        """Creating plan with duplicate slug should fail"""
        # Try to create a plan with existing slug
        duplicate_plan = {
            "name": "Duplicate Starter",
            "slug": "starter",  # This slug already exists
            "price_monthly": 0,
            "price_yearly": 0
        }
        
        response = requests.post(f"{BASE_URL}/api/platform/plans", json=duplicate_plan, headers=auth_headers)
        assert response.status_code == 400, "Should reject duplicate slug"
        assert "already exists" in response.json().get('detail', '').lower()
    
    def test_update_plan(self, auth_headers):
        """PUT /api/platform/plans/{id} updates a plan"""
        # First create a test plan
        unique_slug = f"update-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/platform/plans", json={
            "name": "Update Test Plan",
            "slug": unique_slug,
            "price_monthly": 50000,
            "price_yearly": 500000,
            "status": "draft"
        }, headers=auth_headers)
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test plan")
        
        plan_id = create_response.json().get('id')
        
        try:
            # Update the plan
            update_response = requests.put(f"{BASE_URL}/api/platform/plans/{plan_id}", json={
                "name": "Updated Plan Name",
                "price_monthly": 75000,
                "status": "active"
            }, headers=auth_headers)
            
            assert update_response.status_code == 200, f"Update failed: {update_response.text}"
            
            updated = update_response.json()
            assert updated.get('name') == "Updated Plan Name"
            assert updated.get('price_monthly') == 75000
            assert updated.get('status') == "active"
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/platform/plans/{plan_id}", headers=auth_headers)
    
    def test_delete_plan_without_customers(self, auth_headers):
        """DELETE /api/platform/plans/{id} deletes plan without customers"""
        # Create a test plan
        unique_slug = f"delete-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/platform/plans", json={
            "name": "Delete Test Plan",
            "slug": unique_slug,
            "price_monthly": 0,
            "status": "draft"
        }, headers=auth_headers)
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test plan")
        
        plan_id = create_response.json().get('id')
        
        # Delete the plan
        delete_response = requests.delete(f"{BASE_URL}/api/platform/plans/{plan_id}", headers=auth_headers)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Verify it's deleted
        get_response = requests.get(f"{BASE_URL}/api/platform/plans/{plan_id}", headers=auth_headers)
        assert get_response.status_code == 404, "Deleted plan should not be found"
    
    def test_plans_require_auth(self):
        """Platform plans API should require authentication"""
        response = requests.get(f"{BASE_URL}/api/platform/plans")
        assert response.status_code in [401, 403], "Should require authentication"


class TestPlanAuditLogs:
    """Tests for plan audit logging"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authenticated headers for platform admin"""
        response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Platform admin login failed")
        token = response.json().get('access_token')
        return {"Authorization": f"Bearer {token}"}
    
    def test_audit_logs_exist(self, auth_headers):
        """GET /api/platform/audit-logs returns audit logs"""
        response = requests.get(f"{BASE_URL}/api/platform/audit-logs", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert 'logs' in data, "Response should contain logs"
        assert 'total' in data, "Response should contain total count"
    
    def test_plan_changes_create_audit_logs(self, auth_headers):
        """Creating/updating plans should create audit logs"""
        # Create a plan
        unique_slug = f"audit-test-{uuid.uuid4().hex[:8]}"
        create_response = requests.post(f"{BASE_URL}/api/platform/plans", json={
            "name": "Audit Test Plan",
            "slug": unique_slug,
            "price_monthly": 10000,
            "status": "draft"
        }, headers=auth_headers)
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test plan")
        
        plan_id = create_response.json().get('id')
        
        try:
            # Check audit logs for plan creation
            logs_response = requests.get(
                f"{BASE_URL}/api/platform/audit-logs?entity_type=plan",
                headers=auth_headers
            )
            assert logs_response.status_code == 200
            
            logs = logs_response.json().get('logs', [])
            # Find our plan creation log
            create_logs = [l for l in logs if l.get('entity_id') == plan_id and l.get('action') == 'create_plan']
            assert len(create_logs) >= 1, "Should have audit log for plan creation"
        finally:
            # Cleanup
            requests.delete(f"{BASE_URL}/api/platform/plans/{plan_id}", headers=auth_headers)


class TestPlanSeeding:
    """Tests for plan seeding functionality"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get authenticated headers for platform admin"""
        response = requests.post(f"{BASE_URL}/api/platform/login", json={
            "email": PLATFORM_ADMIN_EMAIL,
            "password": PLATFORM_ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Platform admin login failed")
        token = response.json().get('access_token')
        return {"Authorization": f"Bearer {token}"}
    
    def test_seed_plans_when_exist(self, auth_headers):
        """POST /api/platform/plans/seed should skip if plans exist"""
        # Plans already exist from previous seeding
        response = requests.post(f"{BASE_URL}/api/platform/plans/seed", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Should indicate plans already exist
        assert 'already exist' in data.get('message', '').lower() or 'skipping' in data.get('message', '').lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
