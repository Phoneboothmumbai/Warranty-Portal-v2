"""
Staff Module API Tests
======================
Tests for:
- Staff Module initialization (creates default permissions and roles)
- Users CRUD + FSM state transitions
- Departments CRUD
- Roles CRUD
- Permission Matrix
- Permissions listing
- Audit logs
- API authentication
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "Admin@123!"


class TestStaffModuleAuth:
    """Test authentication for staff endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_staff_endpoints_require_auth(self):
        """Test that staff endpoints require authentication"""
        endpoints = [
            "/api/admin/staff/users",
            "/api/admin/staff/departments",
            "/api/admin/staff/roles",
            "/api/admin/staff/permissions",
            "/api/admin/staff/audit-logs"
        ]
        
        for endpoint in endpoints:
            response = requests.get(f"{BASE_URL}{endpoint}")
            assert response.status_code in [401, 403], f"Endpoint {endpoint} should require auth, got {response.status_code}"
            print(f"✓ {endpoint} requires authentication")


class TestStaffModuleInitialization:
    """Test Staff Module initialization"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_initialize_staff_module(self, headers):
        """Test initializing the staff module creates default permissions and roles"""
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/initialize",
            headers=headers
        )
        # Should succeed or return already initialized
        assert response.status_code in [200, 400], f"Initialize failed: {response.text}"
        print(f"✓ Staff module initialization: {response.status_code}")
    
    def test_default_permissions_created(self, headers):
        """Test that default permissions are created after initialization"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/permissions",
            headers=headers
        )
        assert response.status_code == 200, f"Get permissions failed: {response.text}"
        
        data = response.json()
        permissions = data.get("permissions", [])
        
        # Should have at least 40+ default permissions
        assert len(permissions) >= 40, f"Expected at least 40 permissions, got {len(permissions)}"
        
        # Check for expected categories
        categories = set(p.get("category") for p in permissions)
        expected_categories = {"Staff", "Inventory", "Service", "AMC", "Company", "Reports", "Settings"}
        assert expected_categories.issubset(categories), f"Missing categories: {expected_categories - categories}"
        
        print(f"✓ {len(permissions)} permissions created across {len(categories)} categories")
    
    def test_default_roles_created(self, headers):
        """Test that default roles are created after initialization"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/roles",
            headers=headers
        )
        assert response.status_code == 200, f"Get roles failed: {response.text}"
        
        data = response.json()
        roles = data.get("roles", [])
        
        # Should have 5 default roles
        role_names = [r.get("name") for r in roles]
        expected_roles = ["Administrator", "Manager", "Technician", "Support Agent", "Viewer"]
        
        for expected in expected_roles:
            assert expected in role_names, f"Missing default role: {expected}"
        
        print(f"✓ Default roles created: {role_names}")


class TestStaffUsers:
    """Test Staff Users CRUD and FSM state transitions"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_user_id(self, headers):
        """Create a test user and return its ID"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_user_{unique_id}@example.com",
            "name": f"TEST User {unique_id}",
            "password": "TestPass123!",
            "phone": "+91-9876543210",
            "employee_id": f"EMP-{unique_id}",
            "job_title": "Test Engineer",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        
        if response.status_code == 200:
            data = response.json()
            user = data.get("user", data)
            return user.get("id")
        return None
    
    def test_list_users(self, headers):
        """Test listing staff users"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers
        )
        assert response.status_code == 200, f"List users failed: {response.text}"
        
        data = response.json()
        assert "users" in data, "Response should contain 'users' key"
        # Pagination fields are at root level
        assert "total" in data, "Response should contain 'total' key"
        assert "page" in data, "Response should contain 'page' key"
        
        print(f"✓ Listed {len(data['users'])} users")
    
    def test_create_user(self, headers):
        """Test creating a new staff user"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_newuser_{unique_id}@example.com",
            "name": f"TEST New User {unique_id}",
            "password": "TestPass123!",
            "phone": "+91-9876543210",
            "employee_id": f"EMP-{unique_id}",
            "job_title": "Test Engineer",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        assert response.status_code == 200, f"Create user failed: {response.text}"
        
        data = response.json()
        user = data.get("user", data)
        assert user.get("email") == user_data["email"].lower() or user.get("email") == user_data["email"]
        assert user.get("name") == user_data["name"]
        assert "id" in user
        # User with password should be active
        assert user.get("state") in ["active", "created"]
        
        print(f"✓ Created user: {user.get('name')} with state: {user.get('state')}")
        return user.get("id")
    
    def test_create_user_without_password_sends_invite(self, headers):
        """Test creating user without password creates invite"""
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_invite_{unique_id}@example.com",
            "name": f"TEST Invite User {unique_id}",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        assert response.status_code == 200, f"Create invite user failed: {response.text}"
        
        data = response.json()
        user = data.get("user", data)
        # User without password should be in created state
        assert user.get("state") == "created"
        
        print(f"✓ Created invite user: {user.get('name')} with state: {user.get('state')}")
    
    def test_update_user(self, headers, test_user_id):
        """Test updating a staff user"""
        if not test_user_id:
            pytest.skip("No test user created")
        
        update_data = {
            "name": "TEST Updated User Name",
            "job_title": "Senior Test Engineer"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/staff/users/{test_user_id}",
            headers=headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update user failed: {response.text}"
        
        data = response.json()
        user = data.get("user", data)
        assert user.get("name") == update_data["name"]
        assert user.get("job_title") == update_data["job_title"]
        
        print(f"✓ Updated user: {user.get('name')}")
    
    def test_get_user_by_id(self, headers, test_user_id):
        """Test getting a specific user by ID"""
        if not test_user_id:
            pytest.skip("No test user created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/users/{test_user_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Get user failed: {response.text}"
        
        user = response.json()
        assert user.get("id") == test_user_id
        
        print(f"✓ Got user: {user.get('name')}")
    
    def test_user_state_transition_activate(self, headers):
        """Test activating a user (CREATED -> ACTIVE)"""
        # First create a user without password (will be in CREATED state)
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_activate_{unique_id}@example.com",
            "name": f"TEST Activate User {unique_id}",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test user")
        
        data = create_response.json()
        user = data.get("user", data)
        user_id = user.get("id")
        
        # Now activate the user
        transition_data = {
            "new_state": "active",
            "reason": "Test activation"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/users/{user_id}/state",
            headers=headers,
            json=transition_data
        )
        assert response.status_code == 200, f"Activate user failed: {response.text}"
        
        updated_data = response.json()
        updated_user = updated_data.get("user", updated_data)
        assert updated_user.get("state") == "active"
        
        print(f"✓ Activated user: {updated_user.get('name')}")
    
    def test_user_state_transition_suspend(self, headers):
        """Test suspending a user (ACTIVE -> SUSPENDED)"""
        # First create an active user
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_suspend_{unique_id}@example.com",
            "name": f"TEST Suspend User {unique_id}",
            "password": "TestPass123!",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test user")
        
        data = create_response.json()
        user = data.get("user", data)
        user_id = user.get("id")
        
        # Now suspend the user
        transition_data = {
            "new_state": "suspended",
            "reason": "Test suspension"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/users/{user_id}/state",
            headers=headers,
            json=transition_data
        )
        assert response.status_code == 200, f"Suspend user failed: {response.text}"
        
        updated_data = response.json()
        updated_user = updated_data.get("user", updated_data)
        assert updated_user.get("state") == "suspended"
        
        print(f"✓ Suspended user: {updated_user.get('name')}")
    
    def test_user_state_transition_reactivate(self, headers):
        """Test reactivating a suspended user (SUSPENDED -> ACTIVE)"""
        # First create and suspend a user
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_reactivate_{unique_id}@example.com",
            "name": f"TEST Reactivate User {unique_id}",
            "password": "TestPass123!",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test user")
        
        data = create_response.json()
        user = data.get("user", data)
        user_id = user.get("id")
        
        # Suspend first
        requests.post(
            f"{BASE_URL}/api/admin/staff/users/{user_id}/state",
            headers=headers,
            json={"new_state": "suspended", "reason": "Test suspension"}
        )
        
        # Now reactivate
        transition_data = {
            "new_state": "active",
            "reason": "Test reactivation"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/users/{user_id}/state",
            headers=headers,
            json=transition_data
        )
        assert response.status_code == 200, f"Reactivate user failed: {response.text}"
        
        updated_data = response.json()
        updated_user = updated_data.get("user", updated_data)
        assert updated_user.get("state") == "active"
        
        print(f"✓ Reactivated user: {updated_user.get('name')}")
    
    def test_user_state_transition_archive(self, headers):
        """Test archiving a user (ACTIVE -> ARCHIVED)"""
        # First create an active user
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_archive_{unique_id}@example.com",
            "name": f"TEST Archive User {unique_id}",
            "password": "TestPass123!",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test user")
        
        data = create_response.json()
        user = data.get("user", data)
        user_id = user.get("id")
        
        # Now archive the user
        transition_data = {
            "new_state": "archived",
            "reason": "Test archival"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/users/{user_id}/state",
            headers=headers,
            json=transition_data
        )
        assert response.status_code == 200, f"Archive user failed: {response.text}"
        
        updated_data = response.json()
        updated_user = updated_data.get("user", updated_data)
        assert updated_user.get("state") == "archived"
        
        print(f"✓ Archived user: {updated_user.get('name')}")
    
    def test_invalid_state_transition(self, headers):
        """Test that invalid state transitions are rejected"""
        # Create an archived user
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_invalid_{unique_id}@example.com",
            "name": f"TEST Invalid Transition {unique_id}",
            "password": "TestPass123!",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test user")
        
        data = create_response.json()
        user = data.get("user", data)
        user_id = user.get("id")
        
        # Archive the user
        requests.post(
            f"{BASE_URL}/api/admin/staff/users/{user_id}/state",
            headers=headers,
            json={"new_state": "archived", "reason": "Test archival"}
        )
        
        # Try to reactivate archived user (should fail)
        transition_data = {
            "new_state": "active",
            "reason": "Invalid reactivation attempt"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/users/{user_id}/state",
            headers=headers,
            json=transition_data
        )
        # Should fail - archived users cannot be reactivated
        assert response.status_code in [400, 422], f"Invalid transition should fail, got {response.status_code}"
        
        print(f"✓ Invalid state transition correctly rejected")


class TestDepartments:
    """Test Departments CRUD"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_dept_id(self, headers):
        """Create a test department and return its ID"""
        unique_id = str(uuid.uuid4())[:8]
        dept_data = {
            "name": f"TEST Department {unique_id}",
            "code": f"TD{unique_id[:4]}",
            "description": "Test department for testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/departments",
            headers=headers,
            json=dept_data
        )
        
        if response.status_code == 200:
            data = response.json()
            dept = data.get("department", data)
            return dept.get("id")
        return None
    
    def test_list_departments(self, headers):
        """Test listing departments"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/departments",
            headers=headers
        )
        assert response.status_code == 200, f"List departments failed: {response.text}"
        
        data = response.json()
        assert "departments" in data, "Response should contain 'departments' key"
        
        print(f"✓ Listed {len(data['departments'])} departments")
    
    def test_create_department(self, headers):
        """Test creating a new department"""
        unique_id = str(uuid.uuid4())[:8]
        dept_data = {
            "name": f"TEST Engineering {unique_id}",
            "code": f"ENG{unique_id[:4]}",
            "description": "Engineering department"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/departments",
            headers=headers,
            json=dept_data
        )
        assert response.status_code == 200, f"Create department failed: {response.text}"
        
        data = response.json()
        dept = data.get("department", data)
        assert dept.get("name") == dept_data["name"]
        assert dept.get("code") == dept_data["code"]
        assert "id" in dept
        
        print(f"✓ Created department: {dept.get('name')}")
        return dept.get("id")
    
    def test_update_department(self, headers, test_dept_id):
        """Test updating a department"""
        if not test_dept_id:
            pytest.skip("No test department created")
        
        update_data = {
            "name": "TEST Updated Department",
            "description": "Updated description"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/staff/departments/{test_dept_id}",
            headers=headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update department failed: {response.text}"
        
        data = response.json()
        dept = data.get("department", data)
        assert dept.get("name") == update_data["name"]
        
        print(f"✓ Updated department: {dept.get('name')}")
    
    def test_delete_department(self, headers):
        """Test deleting a department"""
        # First create a department to delete
        unique_id = str(uuid.uuid4())[:8]
        dept_data = {
            "name": f"TEST Delete Dept {unique_id}",
            "code": f"DEL{unique_id[:4]}"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/departments",
            headers=headers,
            json=dept_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test department")
        
        data = create_response.json()
        dept = data.get("department", data)
        dept_id = dept.get("id")
        
        # Now delete it
        response = requests.delete(
            f"{BASE_URL}/api/admin/staff/departments/{dept_id}",
            headers=headers
        )
        assert response.status_code in [200, 204], f"Delete department failed: {response.text}"
        
        print(f"✓ Deleted department")


class TestRoles:
    """Test Roles CRUD"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    @pytest.fixture(scope="class")
    def test_role_id(self, headers):
        """Create a test role and return its ID"""
        unique_id = str(uuid.uuid4())[:8]
        role_data = {
            "name": f"TEST Role {unique_id}",
            "description": "Test role for testing",
            "level": 50
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/roles",
            headers=headers,
            json=role_data
        )
        
        if response.status_code == 200:
            data = response.json()
            role = data.get("role", data)
            return role.get("id")
        return None
    
    def test_list_roles(self, headers):
        """Test listing roles"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/roles",
            headers=headers
        )
        assert response.status_code == 200, f"List roles failed: {response.text}"
        
        data = response.json()
        assert "roles" in data, "Response should contain 'roles' key"
        
        print(f"✓ Listed {len(data['roles'])} roles")
    
    def test_create_role(self, headers):
        """Test creating a new role"""
        unique_id = str(uuid.uuid4())[:8]
        role_data = {
            "name": f"TEST Custom Role {unique_id}",
            "description": "Custom role for testing",
            "level": 75,
            "is_default": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/roles",
            headers=headers,
            json=role_data
        )
        assert response.status_code == 200, f"Create role failed: {response.text}"
        
        data = response.json()
        role = data.get("role", data)
        assert role.get("name") == role_data["name"]
        assert role.get("level") == role_data["level"]
        assert "id" in role
        
        print(f"✓ Created role: {role.get('name')}")
        return role.get("id")
    
    def test_update_role(self, headers, test_role_id):
        """Test updating a role"""
        if not test_role_id:
            pytest.skip("No test role created")
        
        update_data = {
            "name": "TEST Updated Role",
            "description": "Updated description",
            "level": 60
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/staff/roles/{test_role_id}",
            headers=headers,
            json=update_data
        )
        assert response.status_code == 200, f"Update role failed: {response.text}"
        
        data = response.json()
        role = data.get("role", data)
        assert role.get("name") == update_data["name"]
        
        print(f"✓ Updated role: {role.get('name')}")
    
    def test_delete_custom_role(self, headers):
        """Test deleting a custom role"""
        # First create a role to delete
        unique_id = str(uuid.uuid4())[:8]
        role_data = {
            "name": f"TEST Delete Role {unique_id}",
            "description": "Role to be deleted",
            "level": 80
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/roles",
            headers=headers,
            json=role_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test role")
        
        data = create_response.json()
        role = data.get("role", data)
        role_id = role.get("id")
        
        # Now delete it
        response = requests.delete(
            f"{BASE_URL}/api/admin/staff/roles/{role_id}",
            headers=headers
        )
        assert response.status_code in [200, 204], f"Delete role failed: {response.text}"
        
        print(f"✓ Deleted custom role")
    
    def test_cannot_delete_system_role(self, headers):
        """Test that system roles cannot be deleted"""
        # Get the Administrator role (system role)
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/roles",
            headers=headers
        )
        
        if response.status_code != 200:
            pytest.skip("Could not get roles")
        
        roles = response.json().get("roles", [])
        admin_role = next((r for r in roles if r.get("name") == "Administrator" and r.get("is_system")), None)
        
        if not admin_role:
            pytest.skip("Administrator role not found")
        
        # Try to delete system role
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/staff/roles/{admin_role.get('id')}",
            headers=headers
        )
        # Should fail
        assert delete_response.status_code in [400, 403, 422], f"System role deletion should fail, got {delete_response.status_code}"
        
        print(f"✓ System role deletion correctly prevented")


class TestPermissionMatrix:
    """Test Permission Matrix functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_list_permissions(self, headers):
        """Test listing all permissions"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/permissions",
            headers=headers
        )
        assert response.status_code == 200, f"List permissions failed: {response.text}"
        
        data = response.json()
        assert "permissions" in data, "Response should contain 'permissions' key"
        
        permissions = data["permissions"]
        assert len(permissions) > 0, "Should have at least some permissions"
        
        # Check permission structure
        if permissions:
            perm = permissions[0]
            assert "module" in perm
            assert "resource" in perm
            assert "action" in perm
            assert "name" in perm
        
        print(f"✓ Listed {len(permissions)} permissions")
    
    def test_assign_permissions_to_role(self, headers):
        """Test assigning permissions to a role"""
        # First create a test role
        unique_id = str(uuid.uuid4())[:8]
        role_data = {
            "name": f"TEST Perm Role {unique_id}",
            "description": "Role for permission testing",
            "level": 70
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/roles",
            headers=headers,
            json=role_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test role")
        
        data = create_response.json()
        role = data.get("role", data)
        role_id = role.get("id")
        
        # Get some permissions to assign
        perm_response = requests.get(
            f"{BASE_URL}/api/admin/staff/permissions",
            headers=headers
        )
        
        if perm_response.status_code != 200:
            pytest.skip("Could not get permissions")
        
        permissions = perm_response.json().get("permissions", [])
        if len(permissions) < 3:
            pytest.skip("Not enough permissions to test")
        
        # Assign first 3 permissions
        permission_ids = [p.get("id") for p in permissions[:3]]
        
        assign_data = {
            "permission_ids": permission_ids,
            "visibility_scope": "global"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/roles/{role_id}/permissions",
            headers=headers,
            json=assign_data
        )
        assert response.status_code == 200, f"Assign permissions failed: {response.text}"
        
        # Verify permissions were assigned
        role_response = requests.get(
            f"{BASE_URL}/api/admin/staff/roles/{role_id}",
            headers=headers
        )
        
        if role_response.status_code == 200:
            role = role_response.json()
            role_perms = role.get("permissions", [])
            assert len(role_perms) >= 3, f"Expected at least 3 permissions, got {len(role_perms)}"
        
        print(f"✓ Assigned {len(permission_ids)} permissions to role")
    
    def test_remove_permissions_from_role(self, headers):
        """Test removing permissions from a role"""
        # First create a test role with permissions
        unique_id = str(uuid.uuid4())[:8]
        role_data = {
            "name": f"TEST Remove Perm Role {unique_id}",
            "description": "Role for permission removal testing",
            "level": 70
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/staff/roles",
            headers=headers,
            json=role_data
        )
        
        if create_response.status_code != 200:
            pytest.skip("Could not create test role")
        
        data = create_response.json()
        role = data.get("role", data)
        role_id = role.get("id")
        
        # Get some permissions
        perm_response = requests.get(
            f"{BASE_URL}/api/admin/staff/permissions",
            headers=headers
        )
        
        if perm_response.status_code != 200:
            pytest.skip("Could not get permissions")
        
        permissions = perm_response.json().get("permissions", [])
        if len(permissions) < 3:
            pytest.skip("Not enough permissions to test")
        
        # Assign permissions first
        permission_ids = [p.get("id") for p in permissions[:3]]
        requests.post(
            f"{BASE_URL}/api/admin/staff/roles/{role_id}/permissions",
            headers=headers,
            json={"permission_ids": permission_ids, "visibility_scope": "global"}
        )
        
        # Now remove one permission (assign only 2)
        new_permission_ids = permission_ids[:2]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/staff/roles/{role_id}/permissions",
            headers=headers,
            json={"permission_ids": new_permission_ids, "visibility_scope": "global"}
        )
        assert response.status_code == 200, f"Update permissions failed: {response.text}"
        
        print(f"✓ Updated role permissions")


class TestAuditLogs:
    """Test Audit Logs functionality"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_list_audit_logs(self, headers):
        """Test listing audit logs"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/audit-logs",
            headers=headers
        )
        assert response.status_code == 200, f"List audit logs failed: {response.text}"
        
        data = response.json()
        assert "logs" in data, "Response should contain 'logs' key"
        
        print(f"✓ Listed {len(data['logs'])} audit logs")
    
    def test_audit_logs_contain_user_actions(self, headers):
        """Test that audit logs contain user creation actions"""
        # First create a user to generate audit log
        unique_id = str(uuid.uuid4())[:8]
        user_data = {
            "email": f"TEST_audit_{unique_id}@example.com",
            "name": f"TEST Audit User {unique_id}",
            "password": "TestPass123!",
            "department_ids": [],
            "role_ids": [],
            "assigned_company_ids": []
        }
        
        requests.post(
            f"{BASE_URL}/api/admin/staff/users",
            headers=headers,
            json=user_data
        )
        
        # Now check audit logs
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/audit-logs",
            headers=headers
        )
        
        if response.status_code != 200:
            pytest.skip("Could not get audit logs")
        
        logs = response.json().get("logs", [])
        
        # Check for user creation log
        user_logs = [l for l in logs if l.get("entity_type") == "user" and l.get("action") == "create"]
        assert len(user_logs) > 0, "Should have user creation audit logs"
        
        # Check log structure
        if user_logs:
            log = user_logs[0]
            assert "timestamp" in log
            assert "performed_by_name" in log
            assert "changes" in log
        
        print(f"✓ Found {len(user_logs)} user creation audit logs")
    
    def test_audit_logs_filter_by_entity_type(self, headers):
        """Test filtering audit logs by entity type"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/audit-logs?entity_type=user",
            headers=headers
        )
        assert response.status_code == 200, f"Filter audit logs failed: {response.text}"
        
        data = response.json()
        logs = data.get("logs", [])
        
        # All logs should be for users
        for log in logs:
            assert log.get("entity_type") == "user", f"Expected user logs, got {log.get('entity_type')}"
        
        print(f"✓ Filtered audit logs by entity type: {len(logs)} user logs")


class TestUserFilters:
    """Test user listing filters"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def headers(self, auth_token):
        """Get headers with auth token"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_filter_users_by_state(self, headers):
        """Test filtering users by state"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/users?state=active",
            headers=headers
        )
        assert response.status_code == 200, f"Filter users failed: {response.text}"
        
        data = response.json()
        users = data.get("users", [])
        
        # All users should be active
        for user in users:
            assert user.get("state") == "active", f"Expected active users, got {user.get('state')}"
        
        print(f"✓ Filtered users by state: {len(users)} active users")
    
    def test_search_users(self, headers):
        """Test searching users by name/email"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/users?search=TEST",
            headers=headers
        )
        assert response.status_code == 200, f"Search users failed: {response.text}"
        
        data = response.json()
        users = data.get("users", [])
        
        print(f"✓ Search users: found {len(users)} users matching 'TEST'")
    
    def test_pagination(self, headers):
        """Test user listing pagination"""
        response = requests.get(
            f"{BASE_URL}/api/admin/staff/users?page=1&limit=5",
            headers=headers
        )
        assert response.status_code == 200, f"Pagination failed: {response.text}"
        
        data = response.json()
        # Pagination fields are at root level
        assert "page" in data
        assert "limit" in data
        assert "total" in data
        
        users = data.get("users", [])
        assert len(users) <= 5, f"Expected max 5 users, got {len(users)}"
        
        print(f"✓ Pagination working: page {data.get('page')}, {len(users)} users")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
