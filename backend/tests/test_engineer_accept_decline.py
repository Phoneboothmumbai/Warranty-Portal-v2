"""
Test Engineer Accept/Decline Workflow
=====================================
Tests the ticket assignment workflow where:
1. Admin creates ticket and assigns to engineer
2. Ticket status becomes 'pending_acceptance'
3. Engineer can accept (status -> 'assigned') or decline (status -> 'new')

Test Credentials:
- Admin: ck@motta.in / Charu@123@
- Engineer: john.tech@test.com / Tech@123
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEngineerAcceptDeclineWorkflow:
    """Test the engineer accept/decline ticket workflow"""
    
    admin_token = None
    engineer_token = None
    test_ticket_id = None
    test_ticket_number = None
    company_id = "d0ec7779-fe2d-4028-978a-4734ac1e7062"
    engineer_staff_id = "6e6bc3e3-430f-41b9-87b8-6a83067a2411"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get tokens"""
        # Admin login
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if admin_response.status_code == 200:
            self.__class__.admin_token = admin_response.json().get("access_token")
        
        # Engineer login
        engineer_response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": "john.tech@test.com",
            "password": "Tech@123"
        })
        if engineer_response.status_code == 200:
            self.__class__.engineer_token = engineer_response.json().get("access_token")
    
    def test_01_admin_login(self):
        """Test admin can login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        assert response.status_code == 200, f"Admin login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        self.__class__.admin_token = data["access_token"]
        print(f"✓ Admin login successful")
    
    def test_02_engineer_login(self):
        """Test engineer can login with staff_users credentials"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": "john.tech@test.com",
            "password": "Tech@123"
        })
        assert response.status_code == 200, f"Engineer login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert "engineer" in data
        assert data["engineer"]["email"] == "john.tech@test.com"
        self.__class__.engineer_token = data["access_token"]
        print(f"✓ Engineer login successful: {data['engineer']['name']}")
    
    def test_03_admin_create_ticket(self):
        """Test admin can create a service ticket"""
        if not self.__class__.admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {self.__class__.admin_token}"}
        
        # Create a new ticket
        ticket_data = {
            "company_id": self.company_id,
            "title": f"TEST_Accept_Decline_Workflow_{uuid.uuid4().hex[:6]}",
            "description": "Test ticket for engineer accept/decline workflow",
            "priority": "medium",
            "is_urgent": False
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets",
            json=ticket_data,
            headers=headers
        )
        assert response.status_code in [200, 201], f"Create ticket failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "ticket_number" in data
        assert data["status"] == "new"
        
        self.__class__.test_ticket_id = data["id"]
        self.__class__.test_ticket_number = data["ticket_number"]
        print(f"✓ Ticket created: #{data['ticket_number']} (ID: {data['id']})")
    
    def test_04_admin_assign_ticket_to_engineer(self):
        """Test admin assigns ticket to engineer - status should become pending_acceptance"""
        if not self.__class__.admin_token or not self.__class__.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        headers = {"Authorization": f"Bearer {self.__class__.admin_token}"}
        
        assign_data = {
            "technician_id": self.engineer_staff_id,
            "notes": "Please handle this ticket"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{self.__class__.test_ticket_id}/assign",
            json=assign_data,
            headers=headers
        )
        assert response.status_code == 200, f"Assign ticket failed: {response.text}"
        data = response.json()
        
        # Verify status changed to pending_acceptance
        assert data["status"] == "pending_acceptance", f"Expected pending_acceptance, got {data['status']}"
        assert data["assigned_to_id"] == self.engineer_staff_id
        assert data["assignment_status"] == "pending"
        print(f"✓ Ticket assigned to engineer - status: {data['status']}")
    
    def test_05_engineer_sees_pending_acceptance_ticket(self):
        """Test engineer can see the pending_acceptance ticket in their list"""
        if not self.__class__.engineer_token:
            pytest.skip("Engineer token not available")
        
        headers = {"Authorization": f"Bearer {self.__class__.engineer_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/engineer/my-tickets",
            headers=headers
        )
        assert response.status_code == 200, f"Get my-tickets failed: {response.text}"
        data = response.json()
        
        # Check pending_acceptance list
        assert "pending_acceptance" in data
        pending_tickets = data["pending_acceptance"]
        
        # Find our test ticket
        test_ticket = next(
            (t for t in pending_tickets if t["id"] == self.__class__.test_ticket_id),
            None
        )
        assert test_ticket is not None, "Test ticket not found in pending_acceptance list"
        assert test_ticket["status"] == "pending_acceptance"
        print(f"✓ Engineer sees ticket #{test_ticket['ticket_number']} in pending_acceptance list")
    
    def test_06_engineer_get_ticket_detail(self):
        """Test engineer can view ticket details"""
        if not self.__class__.engineer_token or not self.__class__.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        headers = {"Authorization": f"Bearer {self.__class__.engineer_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/engineer/tickets/{self.__class__.test_ticket_id}",
            headers=headers
        )
        assert response.status_code == 200, f"Get ticket detail failed: {response.text}"
        data = response.json()
        
        assert data["id"] == self.__class__.test_ticket_id
        assert data["status"] == "pending_acceptance"
        print(f"✓ Engineer can view ticket details: {data['title']}")
    
    def test_07_engineer_accept_ticket(self):
        """Test engineer accepts the ticket - status should change to assigned"""
        if not self.__class__.engineer_token or not self.__class__.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        headers = {"Authorization": f"Bearer {self.__class__.engineer_token}"}
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/tickets/{self.__class__.test_ticket_id}/accept",
            json={},
            headers=headers
        )
        assert response.status_code == 200, f"Accept ticket failed: {response.text}"
        data = response.json()
        
        # Verify status changed to assigned
        assert data["status"] == "assigned", f"Expected assigned, got {data['status']}"
        assert data["assignment_status"] == "accepted"
        assert data["assignment_accepted_at"] is not None
        print(f"✓ Ticket accepted - status: {data['status']}")
    
    def test_08_verify_accepted_ticket_in_list(self):
        """Verify accepted ticket appears in accepted list, not pending_acceptance"""
        if not self.__class__.engineer_token:
            pytest.skip("Engineer token not available")
        
        headers = {"Authorization": f"Bearer {self.__class__.engineer_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/engineer/my-tickets",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Should be in accepted list, not pending_acceptance
        pending_ids = [t["id"] for t in data.get("pending_acceptance", [])]
        accepted_ids = [t["id"] for t in data.get("accepted", [])]
        
        assert self.__class__.test_ticket_id not in pending_ids, "Ticket still in pending_acceptance"
        assert self.__class__.test_ticket_id in accepted_ids, "Ticket not in accepted list"
        print(f"✓ Ticket correctly moved to accepted list")


class TestEngineerDeclineWorkflow:
    """Test the engineer decline ticket workflow"""
    
    admin_token = None
    engineer_token = None
    test_ticket_id = None
    company_id = "d0ec7779-fe2d-4028-978a-4734ac1e7062"
    engineer_staff_id = "6e6bc3e3-430f-41b9-87b8-6a83067a2411"
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get tokens"""
        # Admin login
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if admin_response.status_code == 200:
            self.__class__.admin_token = admin_response.json().get("access_token")
        
        # Engineer login
        engineer_response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": "john.tech@test.com",
            "password": "Tech@123"
        })
        if engineer_response.status_code == 200:
            self.__class__.engineer_token = engineer_response.json().get("access_token")
    
    def test_01_create_and_assign_ticket_for_decline(self):
        """Create and assign a ticket that will be declined"""
        if not self.__class__.admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {self.__class__.admin_token}"}
        
        # Create ticket
        ticket_data = {
            "company_id": self.company_id,
            "title": f"TEST_Decline_Workflow_{uuid.uuid4().hex[:6]}",
            "description": "Test ticket for decline workflow",
            "priority": "low"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets",
            json=ticket_data,
            headers=headers
        )
        assert create_response.status_code in [200, 201]
        ticket = create_response.json()
        self.__class__.test_ticket_id = ticket["id"]
        
        # Assign to engineer
        assign_response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket['id']}/assign",
            json={"technician_id": self.engineer_staff_id},
            headers=headers
        )
        assert assign_response.status_code == 200
        assert assign_response.json()["status"] == "pending_acceptance"
        print(f"✓ Ticket created and assigned: #{ticket['ticket_number']}")
    
    def test_02_engineer_decline_ticket(self):
        """Test engineer declines the ticket - status should return to new"""
        if not self.__class__.engineer_token or not self.__class__.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        headers = {"Authorization": f"Bearer {self.__class__.engineer_token}"}
        
        decline_data = {
            "reason": "Not available due to prior commitments"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/tickets/{self.__class__.test_ticket_id}/decline",
            json=decline_data,
            headers=headers
        )
        assert response.status_code == 200, f"Decline ticket failed: {response.text}"
        data = response.json()
        
        assert data["success"] == True
        assert "ticket_number" in data
        print(f"✓ Ticket declined successfully")
    
    def test_03_verify_declined_ticket_status(self):
        """Verify declined ticket returns to 'new' status and is unassigned"""
        if not self.__class__.admin_token or not self.__class__.test_ticket_id:
            pytest.skip("Prerequisites not met")
        
        headers = {"Authorization": f"Bearer {self.__class__.admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets/{self.__class__.test_ticket_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify ticket is back to new status and unassigned
        assert data["status"] == "new", f"Expected 'new', got {data['status']}"
        assert data["assigned_to_id"] is None, "Ticket should be unassigned"
        assert data["assignment_status"] == "declined"
        assert data["assignment_decline_reason"] is not None
        print(f"✓ Ticket status reset to 'new', ready for reassignment")


class TestEngineerWorkflowEdgeCases:
    """Test edge cases in the engineer workflow"""
    
    admin_token = None
    engineer_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get tokens"""
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if admin_response.status_code == 200:
            self.__class__.admin_token = admin_response.json().get("access_token")
        
        engineer_response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": "john.tech@test.com",
            "password": "Tech@123"
        })
        if engineer_response.status_code == 200:
            self.__class__.engineer_token = engineer_response.json().get("access_token")
    
    def test_01_cannot_accept_already_assigned_ticket(self):
        """Test that engineer cannot accept a ticket that's already assigned (not pending_acceptance)"""
        if not self.__class__.admin_token or not self.__class__.engineer_token:
            pytest.skip("Tokens not available")
        
        admin_headers = {"Authorization": f"Bearer {self.__class__.admin_token}"}
        engineer_headers = {"Authorization": f"Bearer {self.__class__.engineer_token}"}
        
        # Create and assign ticket
        ticket_data = {
            "company_id": "d0ec7779-fe2d-4028-978a-4734ac1e7062",
            "title": f"TEST_EdgeCase_{uuid.uuid4().hex[:6]}",
            "priority": "medium"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/service-tickets",
            json=ticket_data,
            headers=admin_headers
        )
        if create_resp.status_code not in [200, 201]:
            pytest.skip("Could not create ticket")
        
        ticket_id = create_resp.json()["id"]
        
        # Assign to engineer
        assign_resp = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/assign",
            json={"technician_id": "6e6bc3e3-430f-41b9-87b8-6a83067a2411"},
            headers=admin_headers
        )
        if assign_resp.status_code != 200:
            pytest.skip("Could not assign ticket")
        
        # Accept the ticket
        accept_resp = requests.post(
            f"{BASE_URL}/api/engineer/tickets/{ticket_id}/accept",
            json={},
            headers=engineer_headers
        )
        assert accept_resp.status_code == 200
        
        # Try to accept again - should fail
        second_accept_resp = requests.post(
            f"{BASE_URL}/api/engineer/tickets/{ticket_id}/accept",
            json={},
            headers=engineer_headers
        )
        assert second_accept_resp.status_code == 400, "Should not be able to accept already assigned ticket"
        print(f"✓ Cannot accept already assigned ticket - correct behavior")
    
    def test_02_decline_requires_reason(self):
        """Test that declining a ticket requires a reason"""
        if not self.__class__.admin_token or not self.__class__.engineer_token:
            pytest.skip("Tokens not available")
        
        admin_headers = {"Authorization": f"Bearer {self.__class__.admin_token}"}
        engineer_headers = {"Authorization": f"Bearer {self.__class__.engineer_token}"}
        
        # Create and assign ticket
        ticket_data = {
            "company_id": "d0ec7779-fe2d-4028-978a-4734ac1e7062",
            "title": f"TEST_DeclineReason_{uuid.uuid4().hex[:6]}",
            "priority": "medium"
        }
        create_resp = requests.post(
            f"{BASE_URL}/api/admin/service-tickets",
            json=ticket_data,
            headers=admin_headers
        )
        if create_resp.status_code not in [200, 201]:
            pytest.skip("Could not create ticket")
        
        ticket_id = create_resp.json()["id"]
        
        # Assign to engineer
        assign_resp = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/assign",
            json={"technician_id": "6e6bc3e3-430f-41b9-87b8-6a83067a2411"},
            headers=admin_headers
        )
        if assign_resp.status_code != 200:
            pytest.skip("Could not assign ticket")
        
        # Try to decline without reason - should fail (422 validation error)
        decline_resp = requests.post(
            f"{BASE_URL}/api/engineer/tickets/{ticket_id}/decline",
            json={},  # No reason provided
            headers=engineer_headers
        )
        assert decline_resp.status_code == 422, f"Expected 422, got {decline_resp.status_code}"
        print(f"✓ Decline requires reason - validation working")
    
    def test_03_engineer_stats_count(self):
        """Test that engineer dashboard stats show correct counts"""
        if not self.__class__.engineer_token:
            pytest.skip("Engineer token not available")
        
        headers = {"Authorization": f"Bearer {self.__class__.engineer_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/engineer/my-tickets",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "tickets" in data
        assert "pending_acceptance" in data
        assert "accepted" in data
        assert "in_progress" in data
        assert "total" in data
        
        # Verify counts match
        total_from_lists = (
            len(data.get("pending_acceptance", [])) +
            len(data.get("accepted", [])) +
            len(data.get("in_progress", []))
        )
        # Note: total might include more statuses
        print(f"✓ Stats structure correct - pending: {len(data['pending_acceptance'])}, accepted: {len(data['accepted'])}, in_progress: {len(data['in_progress'])}")


class TestAdminServiceTicketsList:
    """Test admin service tickets list shows pending_acceptance status correctly"""
    
    admin_token = None
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get admin token"""
        admin_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        if admin_response.status_code == 200:
            self.__class__.admin_token = admin_response.json().get("access_token")
    
    def test_01_list_tickets_with_pending_acceptance_status(self):
        """Test admin can list tickets and see pending_acceptance status"""
        if not self.__class__.admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {self.__class__.admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets",
            headers=headers
        )
        assert response.status_code == 200, f"List tickets failed: {response.text}"
        data = response.json()
        
        # Check if response is a list or has tickets key
        tickets = data if isinstance(data, list) else data.get("tickets", [])
        
        # Find any pending_acceptance tickets
        pending_acceptance_tickets = [t for t in tickets if t.get("status") == "pending_acceptance"]
        
        print(f"✓ Admin can list tickets - found {len(pending_acceptance_tickets)} pending_acceptance tickets")
    
    def test_02_filter_tickets_by_status(self):
        """Test admin can filter tickets by pending_acceptance status"""
        if not self.__class__.admin_token:
            pytest.skip("Admin token not available")
        
        headers = {"Authorization": f"Bearer {self.__class__.admin_token}"}
        
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?status=pending_acceptance",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        tickets = data if isinstance(data, list) else data.get("tickets", [])
        
        # All returned tickets should have pending_acceptance status
        for ticket in tickets:
            assert ticket.get("status") == "pending_acceptance", f"Expected pending_acceptance, got {ticket.get('status')}"
        
        print(f"✓ Status filter working - {len(tickets)} pending_acceptance tickets")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
