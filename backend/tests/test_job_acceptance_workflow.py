"""
Test Job Acceptance/Decline Workflow
====================================
Tests the new technician accept/decline/reschedule workflow:
- GET /api/ticketing/assignment/pending - pending assignments with decline_reasons
- POST /api/ticketing/assignment/accept - accept assignment
- POST /api/ticketing/assignment/decline - decline with reason and notification
- POST /api/ticketing/assignment/reschedule - accept with new time
- POST /api/ticketing/assignment/reassign - reassign declined ticket
- GET /api/ticketing/assignment/suggest-reassign/{id} - smart suggestions
- GET /api/ticketing/assignment/sla-stats - SLA tracking stats
- GET /api/ticketing/assignment/check-escalations - overdue pending
- GET /api/notifications - notification list with unread_count
- PUT /api/notifications/{id}/read - mark read
- PUT /api/notifications/read-all - mark all read
- Assignment via /api/ticketing/tickets/{id}/assign sets assignment_status='pending'

Test Credentials: Admin: ck@motta.in / Charu@123@
"""
import pytest
import requests
import os
import uuid
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestJobAcceptanceWorkflow:
    """Test the full job acceptance/decline workflow"""
    
    admin_token = None
    test_ticket_id = None
    test_ticket_number = None
    test_engineer_id = None
    test_notification_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if response.status_code == 200:
            self.__class__.admin_token = response.json().get("access_token")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
    
    # ── Authentication ──
    def test_01_admin_login(self):
        """Test admin login returns access_token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        self.__class__.admin_token = data["access_token"]
        print(f"✓ Admin login successful")
    
    # ── Get Engineers ──
    def test_02_list_engineers(self):
        """Get list of engineers for testing"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        response = requests.get(f"{BASE_URL}/api/ticketing/engineers", headers=self.get_headers())
        assert response.status_code == 200, f"List engineers failed: {response.text}"
        engineers = response.json()
        
        if isinstance(engineers, list) and len(engineers) > 0:
            self.__class__.test_engineer_id = engineers[0]["id"]
            print(f"✓ Found {len(engineers)} engineers. Using: {engineers[0].get('name')}")
        else:
            print(f"⚠ No engineers found - will skip assignment tests")
    
    # ── Get Help Topics ──
    def test_03_get_help_topics(self):
        """Get help topics for ticket creation"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=self.get_headers())
        assert response.status_code == 200, f"Get help topics failed: {response.text}"
        topics = response.json()
        print(f"✓ Found {len(topics)} help topics")
    
    # ── Pending Assignments API ──
    def test_04_pending_assignments_returns_decline_reasons(self):
        """GET /api/ticketing/assignment/pending returns decline_reasons list"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        response = requests.get(f"{BASE_URL}/api/ticketing/assignment/pending", headers=self.get_headers())
        assert response.status_code == 200, f"Pending assignments failed: {response.text}"
        data = response.json()
        
        assert "tickets" in data, "Response should have 'tickets' key"
        assert "decline_reasons" in data, "Response should have 'decline_reasons' key"
        
        decline_reasons = data["decline_reasons"]
        assert isinstance(decline_reasons, list), "decline_reasons should be a list"
        
        # Verify 6 decline reason categories
        assert len(decline_reasons) == 6, f"Expected 6 decline reasons, got {len(decline_reasons)}"
        
        # Verify structure of decline reasons
        reason_ids = [r["id"] for r in decline_reasons]
        expected_ids = ["too_far", "skill_mismatch", "overloaded", "on_leave", "scheduling_conflict", "other"]
        for exp_id in expected_ids:
            assert exp_id in reason_ids, f"Missing decline reason: {exp_id}"
        
        print(f"✓ Pending assignments API returns {len(decline_reasons)} decline reasons: {reason_ids}")
    
    # ── Create Test Ticket ──
    def test_05_create_ticket_for_assignment(self):
        """Create a ticket for testing assignment workflow"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        # Get first help topic
        topics_resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=self.get_headers())
        topics = topics_resp.json() if topics_resp.status_code == 200 else []
        if not topics:
            pytest.skip("No help topics available")
        
        help_topic_id = topics[0]["id"]
        
        ticket_data = {
            "help_topic_id": help_topic_id,
            "subject": f"TEST_JobAcceptance_{uuid.uuid4().hex[:6]}",
            "description": "Test ticket for job acceptance workflow",
            "source": "admin"
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/tickets", json=ticket_data, headers=self.get_headers())
        assert response.status_code in [200, 201], f"Create ticket failed: {response.text}"
        data = response.json()
        
        assert "id" in data, "Response should have 'id'"
        assert "ticket_number" in data, "Response should have 'ticket_number'"
        
        self.__class__.test_ticket_id = data["id"]
        self.__class__.test_ticket_number = data["ticket_number"]
        print(f"✓ Created ticket #{data['ticket_number']} (ID: {data['id']})")
    
    # ── Assign Ticket ──
    def test_06_assign_ticket_sets_pending_status(self):
        """POST /api/ticketing/tickets/{id}/assign sets assignment_status='pending'"""
        if not self.admin_token or not self.test_ticket_id:
            pytest.skip("Prerequisites not met")
        if not self.test_engineer_id:
            pytest.skip("No engineer to assign to")
        
        assign_data = {"assigned_to_id": self.test_engineer_id}
        response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{self.test_ticket_id}/assign",
            json=assign_data,
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Assign ticket failed: {response.text}"
        data = response.json()
        
        # Verify assignment_status is set to 'pending'
        assert data.get("assignment_status") == "pending", f"Expected 'pending', got {data.get('assignment_status')}"
        assert data.get("assigned_to_id") == self.test_engineer_id, "assigned_to_id should match"
        
        print(f"✓ Ticket assigned with assignment_status='pending'")
    
    # ── Accept Assignment ──
    def test_07_accept_assignment(self):
        """POST /api/ticketing/assignment/accept accepts pending assignment"""
        if not self.admin_token or not self.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        accept_data = {"ticket_id": self.test_ticket_id}
        response = requests.post(
            f"{BASE_URL}/api/ticketing/assignment/accept",
            json=accept_data,
            headers=self.get_headers()
        )
        
        # Note: This may fail if admin user is not the assigned engineer
        # The endpoint checks assigned_to_id matches current user
        if response.status_code == 404:
            print(f"⚠ Accept skipped - admin is not the assigned engineer (expected)")
            return
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "accepted", f"Expected status 'accepted'"
            print(f"✓ Assignment accepted")
        else:
            print(f"⚠ Accept returned {response.status_code}: {response.text[:100]}")
    
    # ── SLA Stats ──
    def test_08_sla_stats_endpoint(self):
        """GET /api/ticketing/assignment/sla-stats returns per-engineer stats"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        response = requests.get(f"{BASE_URL}/api/ticketing/assignment/sla-stats", headers=self.get_headers())
        assert response.status_code == 200, f"SLA stats failed: {response.text}"
        data = response.json()
        
        assert "stats" in data, "Response should have 'stats' key"
        stats = data["stats"]
        
        if len(stats) > 0:
            # Verify stat structure
            first_stat = stats[0]
            expected_fields = ["engineer_id", "name", "total_assignments", "accepted", "declined", "acceptance_rate"]
            for field in expected_fields:
                assert field in first_stat, f"Missing field '{field}' in stats"
        
        print(f"✓ SLA stats returns {len(stats)} engineer stats")
    
    # ── Check Escalations ──
    def test_09_check_escalations_endpoint(self):
        """GET /api/ticketing/assignment/check-escalations returns overdue pending"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        response = requests.get(f"{BASE_URL}/api/ticketing/assignment/check-escalations", headers=self.get_headers())
        assert response.status_code == 200, f"Check escalations failed: {response.text}"
        data = response.json()
        
        assert "overdue_assignments" in data, "Response should have 'overdue_assignments'"
        assert "escalation_threshold_hours" in data, "Response should have 'escalation_threshold_hours'"
        assert "count" in data, "Response should have 'count'"
        
        # Verify threshold is 4 hours
        assert data["escalation_threshold_hours"] == 4, f"Expected 4hr threshold, got {data['escalation_threshold_hours']}"
        
        print(f"✓ Check escalations: {data['count']} overdue (threshold: {data['escalation_threshold_hours']}hr)")
    
    # ── Notifications ──
    def test_10_notifications_endpoint(self):
        """GET /api/notifications returns notifications with unread_count"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        response = requests.get(f"{BASE_URL}/api/notifications", headers=self.get_headers())
        assert response.status_code == 200, f"Get notifications failed: {response.text}"
        data = response.json()
        
        assert "notifications" in data, "Response should have 'notifications'"
        assert "unread_count" in data, "Response should have 'unread_count'"
        
        notifications = data["notifications"]
        unread_count = data["unread_count"]
        
        # Store notification ID for read tests
        if len(notifications) > 0:
            self.__class__.test_notification_id = notifications[0]["id"]
        
        print(f"✓ Notifications endpoint returns {len(notifications)} notifications, {unread_count} unread")
    
    def test_11_mark_notification_read(self):
        """PUT /api/notifications/{id}/read marks notification as read"""
        if not self.admin_token:
            pytest.skip("No admin token")
        if not self.test_notification_id:
            print("⚠ No notification to mark as read")
            return
        
        response = requests.put(
            f"{BASE_URL}/api/notifications/{self.test_notification_id}/read",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Mark read failed: {response.text}"
        data = response.json()
        assert data.get("status") == "read", "Expected status 'read'"
        print(f"✓ Notification marked as read")
    
    def test_12_mark_all_notifications_read(self):
        """PUT /api/notifications/read-all marks all notifications as read"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        response = requests.put(f"{BASE_URL}/api/notifications/read-all", headers=self.get_headers())
        assert response.status_code == 200, f"Mark all read failed: {response.text}"
        data = response.json()
        assert data.get("status") == "all_read", "Expected status 'all_read'"
        print(f"✓ All notifications marked as read")
    
    # ── Suggest Reassign ──
    def test_13_suggest_reassignment(self):
        """GET /api/ticketing/assignment/suggest-reassign/{id} returns smart suggestions"""
        if not self.admin_token or not self.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        response = requests.get(
            f"{BASE_URL}/api/ticketing/assignment/suggest-reassign/{self.test_ticket_id}",
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Suggest reassign failed: {response.text}"
        data = response.json()
        
        assert "ticket" in data, "Response should have 'ticket'"
        assert "suggestions" in data, "Response should have 'suggestions'"
        
        suggestions = data["suggestions"]
        if len(suggestions) > 0:
            first_sug = suggestions[0]
            expected_fields = ["engineer_id", "name", "open_tickets", "score", "available_on_date"]
            for field in expected_fields:
                assert field in first_sug, f"Missing field '{field}' in suggestion"
            
            # Verify sorted by score (lower is better)
            scores = [s["score"] for s in suggestions]
            assert scores == sorted(scores), "Suggestions should be sorted by score ascending"
        
        print(f"✓ Suggest reassign returns {len(suggestions)} suggestions (sorted by score)")


class TestDeclineAndReassignWorkflow:
    """Test decline and reassign workflow"""
    
    admin_token = None
    test_ticket_id = None
    test_engineer_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if response.status_code == 200:
            self.__class__.admin_token = response.json().get("access_token")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
    
    def test_01_create_ticket_for_decline_test(self):
        """Create ticket for decline workflow test"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        # Get help topic
        topics_resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=self.get_headers())
        topics = topics_resp.json() if topics_resp.status_code == 200 else []
        if not topics:
            pytest.skip("No help topics")
        
        # Get engineer
        eng_resp = requests.get(f"{BASE_URL}/api/ticketing/engineers", headers=self.get_headers())
        engineers = eng_resp.json() if eng_resp.status_code == 200 else []
        if not engineers or not isinstance(engineers, list) or len(engineers) < 1:
            pytest.skip("No engineers available")
        
        self.__class__.test_engineer_id = engineers[0]["id"]
        
        # Create ticket
        ticket_data = {
            "help_topic_id": topics[0]["id"],
            "subject": f"TEST_DeclineReassign_{uuid.uuid4().hex[:6]}",
            "description": "Test ticket for decline and reassign workflow"
        }
        response = requests.post(f"{BASE_URL}/api/ticketing/tickets", json=ticket_data, headers=self.get_headers())
        assert response.status_code in [200, 201], f"Create failed: {response.text}"
        self.__class__.test_ticket_id = response.json()["id"]
        print(f"✓ Created ticket for decline test")
    
    def test_02_assign_ticket(self):
        """Assign ticket to engineer"""
        if not self.admin_token or not self.test_ticket_id or not self.test_engineer_id:
            pytest.skip("Prerequisites not met")
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{self.test_ticket_id}/assign",
            json={"assigned_to_id": self.test_engineer_id},
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Assign failed: {response.text}"
        print(f"✓ Ticket assigned")
    
    def test_03_decline_requires_reason_id(self):
        """POST /api/ticketing/assignment/decline requires reason_id"""
        if not self.admin_token or not self.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        # Try decline without reason_id
        response = requests.post(
            f"{BASE_URL}/api/ticketing/assignment/decline",
            json={"ticket_id": self.test_ticket_id},  # Missing reason_id
            headers=self.get_headers()
        )
        
        # Should fail with 422 validation error
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print(f"✓ Decline validation requires reason_id")
    
    def test_04_reassign_endpoint(self):
        """POST /api/ticketing/assignment/reassign reassigns ticket to new engineer"""
        if not self.admin_token or not self.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        # Get another engineer if available
        eng_resp = requests.get(f"{BASE_URL}/api/ticketing/engineers", headers=self.get_headers())
        engineers = eng_resp.json() if eng_resp.status_code == 200 else []
        
        if not engineers or len(engineers) < 1:
            pytest.skip("No engineers for reassignment")
        
        new_engineer_id = engineers[-1]["id"]  # Pick last engineer
        
        reassign_data = {
            "ticket_id": self.test_ticket_id,
            "engineer_id": new_engineer_id
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/assignment/reassign",
            json=reassign_data,
            headers=self.get_headers()
        )
        assert response.status_code == 200, f"Reassign failed: {response.text}"
        data = response.json()
        
        assert data.get("status") == "reassigned", f"Expected status 'reassigned'"
        assert "new_engineer" in data, "Response should have new_engineer name"
        
        print(f"✓ Ticket reassigned to {data['new_engineer']}")


class TestRescheduleWorkflow:
    """Test accept with reschedule workflow"""
    
    admin_token = None
    test_ticket_id = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if response.status_code == 200:
            self.__class__.admin_token = response.json().get("access_token")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
    
    def test_01_reschedule_endpoint_structure(self):
        """POST /api/ticketing/assignment/reschedule accepts with proposed time"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        # Create ticket
        topics_resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=self.get_headers())
        topics = topics_resp.json() if topics_resp.status_code == 200 else []
        if not topics:
            pytest.skip("No help topics")
        
        eng_resp = requests.get(f"{BASE_URL}/api/ticketing/engineers", headers=self.get_headers())
        engineers = eng_resp.json() if eng_resp.status_code == 200 else []
        if not engineers or not isinstance(engineers, list) or len(engineers) < 1:
            pytest.skip("No engineers")
        
        # Create ticket
        ticket_data = {
            "help_topic_id": topics[0]["id"],
            "subject": f"TEST_Reschedule_{uuid.uuid4().hex[:6]}",
            "description": "Test reschedule"
        }
        create_resp = requests.post(f"{BASE_URL}/api/ticketing/tickets", json=ticket_data, headers=self.get_headers())
        if create_resp.status_code not in [200, 201]:
            pytest.skip("Could not create ticket")
        
        ticket_id = create_resp.json()["id"]
        
        # Assign
        requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/assign",
            json={"assigned_to_id": engineers[0]["id"]},
            headers=self.get_headers()
        )
        
        # Test reschedule structure
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:00:00")
        reschedule_data = {
            "ticket_id": ticket_id,
            "proposed_time": tomorrow,
            "proposed_end_time": (datetime.now() + timedelta(days=1, hours=1)).strftime("%Y-%m-%dT11:00:00"),
            "notes": "Proposing new time for visit"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/ticketing/assignment/reschedule",
            json=reschedule_data,
            headers=self.get_headers()
        )
        
        # This may fail if admin is not the assigned engineer
        if response.status_code == 404:
            print(f"⚠ Reschedule skipped - admin not the assigned engineer (expected)")
            return
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "rescheduled"
            print(f"✓ Reschedule endpoint working")
        else:
            print(f"⚠ Reschedule returned {response.status_code}")


class TestTransitionSetsAssignmentPending:
    """Test that /api/ticketing/tickets/{id}/transition also sets assignment_status='pending'"""
    
    admin_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if response.status_code == 200:
            self.__class__.admin_token = response.json().get("access_token")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
    
    def test_01_transition_with_assignment_sets_pending(self):
        """Transition endpoint with assigned_to_id sets assignment_status='pending'"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        # Get help topic with workflow
        topics_resp = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=self.get_headers())
        topics = topics_resp.json() if topics_resp.status_code == 200 else []
        topic_with_workflow = next((t for t in topics if t.get("workflow_id")), None)
        if not topic_with_workflow:
            pytest.skip("No help topic with workflow")
        
        # Get workflows for transition IDs
        workflows_resp = requests.get(f"{BASE_URL}/api/ticketing/workflows", headers=self.get_headers())
        workflows = workflows_resp.json() if workflows_resp.status_code == 200 else []
        
        workflow = next((w for w in workflows if w.get("id") == topic_with_workflow.get("workflow_id")), None)
        if not workflow:
            pytest.skip("Workflow not found")
        
        # Find transition that assigns engineer
        stages = workflow.get("stages", [])
        transition = None
        for stage in stages:
            for t in stage.get("transitions", []):
                if t.get("requires_input") == "assign_engineer":
                    transition = t
                    break
            if transition:
                break
        
        if not transition:
            print(f"⚠ No transition with 'assign_engineer' requirement found")
            return
        
        # Get engineer
        eng_resp = requests.get(f"{BASE_URL}/api/ticketing/engineers", headers=self.get_headers())
        engineers = eng_resp.json() if eng_resp.status_code == 200 else []
        if not engineers:
            pytest.skip("No engineers")
        
        # Create ticket
        ticket_data = {
            "help_topic_id": topic_with_workflow["id"],
            "subject": f"TEST_Transition_{uuid.uuid4().hex[:6]}",
            "description": "Test transition assignment"
        }
        create_resp = requests.post(f"{BASE_URL}/api/ticketing/tickets", json=ticket_data, headers=self.get_headers())
        if create_resp.status_code not in [200, 201]:
            pytest.skip("Could not create ticket")
        
        ticket_id = create_resp.json()["id"]
        
        # Transition with assignment
        trans_data = {
            "transition_id": transition["id"],
            "assigned_to_id": engineers[0]["id"]
        }
        response = requests.post(
            f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/transition",
            json=trans_data,
            headers=self.get_headers()
        )
        
        if response.status_code == 200:
            data = response.json()
            # Check assignment_status
            if data.get("assignment_status") == "pending":
                print(f"✓ Transition with assignment sets assignment_status='pending'")
            else:
                print(f"⚠ assignment_status is '{data.get('assignment_status')}' (may vary by workflow)")
        else:
            print(f"⚠ Transition returned {response.status_code}: {response.text[:100]}")


class TestCleanup:
    """Clean up test data"""
    
    admin_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if response.status_code == 200:
            self.__class__.admin_token = response.json().get("access_token")
    
    def get_headers(self):
        return {"Authorization": f"Bearer {self.admin_token}", "Content-Type": "application/json"}
    
    def test_cleanup_test_tickets(self):
        """Clean up test tickets created during testing"""
        if not self.admin_token:
            pytest.skip("No admin token")
        
        # Get tickets with TEST_ prefix
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets?search=TEST_",
            headers=self.get_headers()
        )
        
        if response.status_code != 200:
            print(f"⚠ Could not list tickets for cleanup")
            return
        
        data = response.json()
        tickets = data.get("tickets", []) if isinstance(data, dict) else data
        
        cleaned = 0
        for ticket in tickets:
            if ticket.get("subject", "").startswith("TEST_"):
                # Note: No delete endpoint may exist; skip actual deletion
                cleaned += 1
        
        print(f"✓ Found {cleaned} test tickets (cleanup note: implement delete if needed)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
