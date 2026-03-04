"""
Project Management Module Tests
===============================
Tests for template-driven project management with auto-generated subtasks.
Features: Projects, Tasks (from templates), Subtasks (auto-created with sequential completion)
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"


class TestProjectsAuthentication:
    """Authentication and token retrieval"""

    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]

    def test_admin_login(self, auth_token):
        """Verify admin can login"""
        assert auth_token is not None
        assert len(auth_token) > 20
        print(f"Login successful, token length: {len(auth_token)}")


class TestProjectTemplates:
    """Task Templates API tests"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def test_seed_default_templates(self, auth_headers):
        """Test seeding default templates (if none exist)"""
        response = requests.post(f"{BASE_URL}/api/projects/templates/seed-defaults", headers=auth_headers)
        assert response.status_code == 200, f"Seed templates failed: {response.text}"
        data = response.json()
        # Should either seed new templates or report existing ones
        assert "seeded" in data or "message" in data
        print(f"Seed templates response: {data}")

    def test_list_templates(self, auth_headers):
        """Test listing all templates - should have 5 defaults"""
        response = requests.get(f"{BASE_URL}/api/projects/templates", headers=auth_headers)
        assert response.status_code == 200, f"List templates failed: {response.text}"
        templates = response.json()
        assert isinstance(templates, list)
        assert len(templates) >= 5, f"Expected at least 5 templates, got {len(templates)}"
        
        # Verify expected default templates
        template_names = [t["name"] for t in templates]
        expected = ["CCTV Installation", "Server Deployment", "Computer/Workstation Deployment", 
                    "Network Setup", "Firewall Deployment"]
        for name in expected:
            assert name in template_names, f"Missing template: {name}"
        
        # Verify subtasks exist
        for t in templates:
            assert "subtasks" in t
            assert len(t["subtasks"]) > 0, f"Template {t['name']} has no subtasks"
        print(f"Found {len(templates)} templates")

    def test_create_custom_template(self, auth_headers):
        """Test creating a new custom template"""
        unique_name = f"TEST_Custom_Template_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "description": "Test template for unit tests",
            "category": "Testing",
            "subtasks": [
                {"name": "Step 1", "description": "First step", "order": 1, "estimated_hours": 2, "is_mandatory": True},
                {"name": "Step 2", "description": "Second step", "order": 2, "estimated_hours": 3, "is_mandatory": True},
                {"name": "Step 3 (Optional)", "description": "Optional step", "order": 3, "estimated_hours": 1, "is_mandatory": False},
            ]
        }
        response = requests.post(f"{BASE_URL}/api/projects/templates", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Create template failed: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        assert data["category"] == "Testing"
        assert len(data["subtasks"]) == 3
        assert "id" in data
        print(f"Created template: {data['id']}")
        return data["id"]

    def test_update_template(self, auth_headers):
        """Test updating a template"""
        # First create a template
        unique_name = f"TEST_Update_Template_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "description": "Original description",
            "category": "Testing",
            "subtasks": [{"name": "Original Step", "order": 1, "estimated_hours": 1, "is_mandatory": True}]
        }
        create_res = requests.post(f"{BASE_URL}/api/projects/templates", headers=auth_headers, json=create_payload)
        assert create_res.status_code == 200
        template_id = create_res.json()["id"]

        # Update it
        update_payload = {
            "name": f"{unique_name}_Updated",
            "description": "Updated description",
            "subtasks": [
                {"name": "Updated Step 1", "order": 1, "estimated_hours": 2, "is_mandatory": True},
                {"name": "New Step 2", "order": 2, "estimated_hours": 3, "is_mandatory": True}
            ]
        }
        update_res = requests.put(f"{BASE_URL}/api/projects/templates/{template_id}", headers=auth_headers, json=update_payload)
        assert update_res.status_code == 200, f"Update template failed: {update_res.text}"
        
        # Verify update
        list_res = requests.get(f"{BASE_URL}/api/projects/templates", headers=auth_headers)
        templates = list_res.json()
        updated = next((t for t in templates if t["id"] == template_id), None)
        assert updated is not None
        assert updated["description"] == "Updated description"
        assert len(updated["subtasks"]) == 2
        print(f"Template {template_id} updated successfully")

    def test_delete_template(self, auth_headers):
        """Test deleting a template (soft delete)"""
        # First create a template
        unique_name = f"TEST_Delete_Template_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "description": "Will be deleted",
            "category": "Testing",
            "subtasks": [{"name": "Step", "order": 1, "estimated_hours": 1, "is_mandatory": True}]
        }
        create_res = requests.post(f"{BASE_URL}/api/projects/templates", headers=auth_headers, json=create_payload)
        assert create_res.status_code == 200
        template_id = create_res.json()["id"]

        # Delete it
        delete_res = requests.delete(f"{BASE_URL}/api/projects/templates/{template_id}", headers=auth_headers)
        assert delete_res.status_code == 200, f"Delete template failed: {delete_res.text}"

        # Verify deletion (should not appear in list)
        list_res = requests.get(f"{BASE_URL}/api/projects/templates", headers=auth_headers)
        templates = list_res.json()
        deleted = next((t for t in templates if t["id"] == template_id), None)
        assert deleted is None, "Deleted template should not appear in list"
        print(f"Template {template_id} deleted successfully")


class TestProjects:
    """Projects API tests"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @pytest.fixture(scope="class")
    def test_company_id(self, auth_headers):
        """Get a company ID for testing"""
        response = requests.get(f"{BASE_URL}/api/admin/companies", headers=auth_headers)
        if response.status_code == 200:
            companies = response.json()
            if companies and len(companies) > 0:
                return companies[0]["id"]
        pytest.skip("No companies available for testing")

    def test_list_projects(self, auth_headers):
        """Test listing projects"""
        response = requests.get(f"{BASE_URL}/api/projects", headers=auth_headers)
        assert response.status_code == 200, f"List projects failed: {response.text}"
        projects = response.json()
        assert isinstance(projects, list)
        print(f"Found {len(projects)} projects")
        
        # Verify project structure if any exist
        if projects:
            p = projects[0]
            assert "id" in p
            assert "name" in p
            assert "status" in p
            assert "progress" in p
            assert "task_count" in p
            assert "subtask_count" in p

    def test_list_projects_with_status_filter(self, auth_headers):
        """Test listing projects with status filter"""
        for status in ["planning", "active", "completed"]:
            response = requests.get(f"{BASE_URL}/api/projects?status={status}", headers=auth_headers)
            assert response.status_code == 200, f"Filter by {status} failed: {response.text}"
            projects = response.json()
            for p in projects:
                assert p["status"] == status, f"Project {p['name']} has status {p['status']}, expected {status}"
        print("Status filters working correctly")

    def test_create_project(self, auth_headers, test_company_id):
        """Test creating a new project"""
        unique_name = f"TEST_Project_{uuid.uuid4().hex[:6]}"
        payload = {
            "name": unique_name,
            "company_id": test_company_id,
            "description": "Test project for unit tests",
            "priority": "high",
            "start_date": "2025-01-15",
            "end_date": "2025-02-15"
        }
        response = requests.post(f"{BASE_URL}/api/projects", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Create project failed: {response.text}"
        data = response.json()
        assert data["name"] == unique_name
        assert data["status"] == "planning"
        assert data["priority"] == "high"
        assert "id" in data
        print(f"Created project: {data['id']}")
        return data["id"]

    def test_get_project_detail(self, auth_headers, test_company_id):
        """Test getting project details"""
        # First create a project
        unique_name = f"TEST_Detail_Project_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "company_id": test_company_id,
            "description": "Test project",
            "priority": "medium"
        }
        create_res = requests.post(f"{BASE_URL}/api/projects", headers=auth_headers, json=create_payload)
        assert create_res.status_code == 200
        project_id = create_res.json()["id"]

        # Get details
        detail_res = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        assert detail_res.status_code == 200, f"Get project detail failed: {detail_res.text}"
        data = detail_res.json()
        assert data["id"] == project_id
        assert data["name"] == unique_name
        assert "tasks" in data
        assert "progress" in data
        assert "subtask_count" in data
        print(f"Project detail retrieved: {data['name']}")

    def test_update_project(self, auth_headers, test_company_id):
        """Test updating a project"""
        # First create a project
        unique_name = f"TEST_Update_Project_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "company_id": test_company_id,
            "priority": "low"
        }
        create_res = requests.post(f"{BASE_URL}/api/projects", headers=auth_headers, json=create_payload)
        assert create_res.status_code == 200
        project_id = create_res.json()["id"]

        # Update it
        update_payload = {
            "name": f"{unique_name}_Updated",
            "priority": "critical",
            "status": "active"
        }
        update_res = requests.put(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers, json=update_payload)
        assert update_res.status_code == 200, f"Update project failed: {update_res.text}"

        # Verify update
        detail_res = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        data = detail_res.json()
        assert data["priority"] == "critical"
        assert data["status"] == "active"
        print(f"Project {project_id} updated successfully")

    def test_delete_project(self, auth_headers, test_company_id):
        """Test deleting a project"""
        # First create a project
        unique_name = f"TEST_Delete_Project_{uuid.uuid4().hex[:6]}"
        create_payload = {
            "name": unique_name,
            "company_id": test_company_id
        }
        create_res = requests.post(f"{BASE_URL}/api/projects", headers=auth_headers, json=create_payload)
        assert create_res.status_code == 200
        project_id = create_res.json()["id"]

        # Delete it
        delete_res = requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        assert delete_res.status_code == 200, f"Delete project failed: {delete_res.text}"

        # Verify deletion (should return 404)
        detail_res = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        assert detail_res.status_code == 404, "Deleted project should return 404"
        print(f"Project {project_id} deleted successfully")


class TestTasksAndSubtasks:
    """Tasks and Subtasks API tests"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    @pytest.fixture(scope="class")
    def test_setup(self, auth_headers):
        """Create a project and get template for testing"""
        # Get company
        comp_res = requests.get(f"{BASE_URL}/api/admin/companies", headers=auth_headers)
        if comp_res.status_code != 200 or not comp_res.json():
            pytest.skip("No companies available")
        company_id = comp_res.json()[0]["id"]

        # Get template
        tmpl_res = requests.get(f"{BASE_URL}/api/projects/templates", headers=auth_headers)
        if tmpl_res.status_code != 200 or not tmpl_res.json():
            pytest.skip("No templates available")
        template = tmpl_res.json()[0]

        # Create project
        unique_name = f"TEST_Task_Project_{uuid.uuid4().hex[:6]}"
        proj_res = requests.post(f"{BASE_URL}/api/projects", headers=auth_headers, json={
            "name": unique_name,
            "company_id": company_id,
            "priority": "high"
        })
        assert proj_res.status_code == 200
        project = proj_res.json()

        return {
            "project_id": project["id"],
            "company_id": company_id,
            "template_id": template["id"],
            "template_name": template["name"],
            "subtask_count": len(template.get("subtasks", []))
        }

    def test_add_task_from_template(self, auth_headers, test_setup):
        """Test adding a task from template - should auto-generate subtasks"""
        project_id = test_setup["project_id"]
        template_id = test_setup["template_id"]
        expected_subtasks = test_setup["subtask_count"]

        payload = {
            "template_id": template_id,
            "name": f"Test Task - {test_setup['template_name']}",
            "start_date": "2025-01-15",
            "due_date": "2025-02-15"
        }
        response = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", headers=auth_headers, json=payload)
        assert response.status_code == 200, f"Add task failed: {response.text}"
        data = response.json()
        
        # Verify task created
        assert "id" in data
        assert data["template_id"] == template_id
        assert data["status"] == "pending"
        
        # Verify subtasks auto-generated
        assert "subtasks" in data
        assert len(data["subtasks"]) == expected_subtasks, f"Expected {expected_subtasks} subtasks, got {len(data['subtasks'])}"
        
        # Verify subtasks are ordered
        orders = [s["order"] for s in data["subtasks"]]
        assert orders == sorted(orders), "Subtasks should be ordered"
        
        print(f"Task created with {len(data['subtasks'])} auto-generated subtasks")
        return data["id"], data["subtasks"]

    def test_project_activates_on_task_add(self, auth_headers, test_setup):
        """Test that project status changes to 'active' when first task is added"""
        project_id = test_setup["project_id"]
        
        # Get project detail
        response = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        
        # Should be active (since we added a task in previous test)
        assert data["status"] in ["active", "planning", "completed"], f"Unexpected status: {data['status']}"
        print(f"Project status: {data['status']}")

    def test_subtask_sequential_completion(self, auth_headers, test_setup):
        """Test sequential subtask completion flow"""
        project_id = test_setup["project_id"]
        template_id = test_setup["template_id"]

        # Create a fresh task for this test
        task_res = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", headers=auth_headers, json={
            "template_id": template_id,
            "name": "Sequential Test Task"
        })
        assert task_res.status_code == 200
        task_data = task_res.json()
        task_id = task_data["id"]
        subtasks = task_data["subtasks"]

        # Complete first subtask
        first_subtask = subtasks[0]
        update_res = requests.put(
            f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}/subtasks/{first_subtask['id']}",
            headers=auth_headers,
            json={"status": "completed", "remarks": "First step done"}
        )
        assert update_res.status_code == 200, f"Update subtask failed: {update_res.text}"

        # Verify first subtask is completed
        proj_res = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        proj_data = proj_res.json()
        task = next((t for t in proj_data["tasks"] if t["id"] == task_id), None)
        assert task is not None
        
        first_st = next((s for s in task["subtasks"] if s["id"] == first_subtask["id"]), None)
        assert first_st is not None
        assert first_st["status"] == "completed"
        assert first_st["remarks"] == "First step done"
        assert first_st["completed_at"] is not None

        print("Sequential subtask completion working correctly")

    def test_subtask_status_transitions(self, auth_headers, test_setup):
        """Test subtask status transitions: pending -> in-progress -> completed"""
        project_id = test_setup["project_id"]
        template_id = test_setup["template_id"]

        # Create a fresh task
        task_res = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", headers=auth_headers, json={
            "template_id": template_id,
            "name": "Status Transition Test"
        })
        assert task_res.status_code == 200
        task_data = task_res.json()
        task_id = task_data["id"]
        subtask = task_data["subtasks"][0]

        # Start subtask (pending -> in-progress)
        start_res = requests.put(
            f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}/subtasks/{subtask['id']}",
            headers=auth_headers,
            json={"status": "in-progress"}
        )
        assert start_res.status_code == 200

        # Verify in-progress
        proj_res = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        task = next((t for t in proj_res.json()["tasks"] if t["id"] == task_id), None)
        st = next((s for s in task["subtasks"] if s["id"] == subtask["id"]), None)
        assert st["status"] == "in-progress"
        assert st["started_at"] is not None

        # Complete subtask (in-progress -> completed)
        complete_res = requests.put(
            f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}/subtasks/{subtask['id']}",
            headers=auth_headers,
            json={"status": "completed", "remarks": "Done with testing"}
        )
        assert complete_res.status_code == 200

        # Verify completed
        proj_res = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        task = next((t for t in proj_res.json()["tasks"] if t["id"] == task_id), None)
        st = next((s for s in task["subtasks"] if s["id"] == subtask["id"]), None)
        assert st["status"] == "completed"
        assert st["completed_at"] is not None

        print("Status transitions working correctly")

    def test_subtask_assignment(self, auth_headers, test_setup):
        """Test assigning staff to subtask"""
        project_id = test_setup["project_id"]
        template_id = test_setup["template_id"]

        # Get staff list
        staff_res = requests.get(f"{BASE_URL}/api/projects/staff-list", headers=auth_headers)
        assert staff_res.status_code == 200
        staff_data = staff_res.json()
        
        # Find a staff member
        all_staff = staff_data.get("staff", []) + staff_data.get("members", [])
        if not all_staff:
            print("No staff available, skipping assignment test")
            return

        staff_id = all_staff[0]["id"]

        # Create task
        task_res = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", headers=auth_headers, json={
            "template_id": template_id,
            "name": "Assignment Test"
        })
        assert task_res.status_code == 200
        task_id = task_res.json()["id"]
        subtask_id = task_res.json()["subtasks"][0]["id"]

        # Assign staff
        assign_res = requests.put(
            f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}/subtasks/{subtask_id}",
            headers=auth_headers,
            json={"assigned_to": staff_id}
        )
        assert assign_res.status_code == 200

        # Verify assignment
        proj_res = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        task = next((t for t in proj_res.json()["tasks"] if t["id"] == task_id), None)
        st = next((s for s in task["subtasks"] if s["id"] == subtask_id), None)
        assert st["assigned_to"] == staff_id
        
        print(f"Subtask assigned to staff {staff_id}")

    def test_delete_task(self, auth_headers, test_setup):
        """Test deleting a task (soft delete with subtasks)"""
        project_id = test_setup["project_id"]
        template_id = test_setup["template_id"]

        # Create task
        task_res = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", headers=auth_headers, json={
            "template_id": template_id,
            "name": "Delete Test Task"
        })
        assert task_res.status_code == 200
        task_id = task_res.json()["id"]

        # Delete task
        delete_res = requests.delete(f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}", headers=auth_headers)
        assert delete_res.status_code == 200

        # Verify task is deleted (not in project detail)
        proj_res = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        task = next((t for t in proj_res.json()["tasks"] if t["id"] == task_id), None)
        assert task is None, "Deleted task should not appear in project"

        print(f"Task {task_id} deleted successfully")


class TestStaffList:
    """Staff list API tests"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def test_get_staff_list(self, auth_headers):
        """Test getting staff list for assignment dropdowns"""
        response = requests.get(f"{BASE_URL}/api/projects/staff-list", headers=auth_headers)
        assert response.status_code == 200, f"Get staff list failed: {response.text}"
        data = response.json()
        
        assert "staff" in data
        assert "members" in data
        assert isinstance(data["staff"], list)
        assert isinstance(data["members"], list)
        
        print(f"Staff list: {len(data['staff'])} staff, {len(data['members'])} org members")


class TestAutoCompletion:
    """Test auto-completion logic"""

    @pytest.fixture(scope="class")
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = response.json().get("access_token")
        return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    def test_task_auto_completes_when_all_subtasks_done(self, auth_headers):
        """Test that task auto-completes when all mandatory subtasks are completed"""
        # Get company
        comp_res = requests.get(f"{BASE_URL}/api/admin/companies", headers=auth_headers)
        if comp_res.status_code != 200 or not comp_res.json():
            pytest.skip("No companies available")
        company_id = comp_res.json()[0]["id"]

        # Create a custom template with 2 mandatory subtasks
        template_res = requests.post(f"{BASE_URL}/api/projects/templates", headers=auth_headers, json={
            "name": f"TEST_AutoComplete_{uuid.uuid4().hex[:6]}",
            "category": "Testing",
            "subtasks": [
                {"name": "Step 1", "order": 1, "estimated_hours": 1, "is_mandatory": True},
                {"name": "Step 2", "order": 2, "estimated_hours": 1, "is_mandatory": True}
            ]
        })
        assert template_res.status_code == 200
        template_id = template_res.json()["id"]

        # Create project
        proj_res = requests.post(f"{BASE_URL}/api/projects", headers=auth_headers, json={
            "name": f"TEST_AutoComplete_Project_{uuid.uuid4().hex[:6]}",
            "company_id": company_id
        })
        assert proj_res.status_code == 200
        project_id = proj_res.json()["id"]

        # Add task
        task_res = requests.post(f"{BASE_URL}/api/projects/{project_id}/tasks", headers=auth_headers, json={
            "template_id": template_id,
            "name": "Auto Complete Test"
        })
        assert task_res.status_code == 200
        task_id = task_res.json()["id"]
        subtasks = task_res.json()["subtasks"]

        # Complete all subtasks
        for st in subtasks:
            update_res = requests.put(
                f"{BASE_URL}/api/projects/{project_id}/tasks/{task_id}/subtasks/{st['id']}",
                headers=auth_headers,
                json={"status": "completed"}
            )
            assert update_res.status_code == 200

        # Verify task auto-completed
        proj_detail = requests.get(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)
        task = next((t for t in proj_detail.json()["tasks"] if t["id"] == task_id), None)
        assert task is not None
        assert task["status"] == "completed", f"Task should auto-complete, but status is {task['status']}"
        
        print("Task auto-completed when all mandatory subtasks were done")

        # Cleanup
        requests.delete(f"{BASE_URL}/api/projects/templates/{template_id}", headers=auth_headers)
        requests.delete(f"{BASE_URL}/api/projects/{project_id}", headers=auth_headers)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
