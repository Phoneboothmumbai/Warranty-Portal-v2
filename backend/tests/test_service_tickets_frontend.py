"""
Service Tickets Frontend Integration Tests
==========================================
Tests for the unified Service Tickets system with 7-state workflow.
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ck@motta.in"
TEST_PASSWORD = "Charu@123@"

# Test data IDs from context
COMPANY_ID = "7bf0f993-706d-45bf-8704-ded6d7fecda8"
STAFF_ID = "acd161f1-a3e6-4514-9c14-092b19a4b5c3"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD}
    )
    assert response.status_code == 200, f"Login failed: {response.text}"
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


class TestServiceTicketsAPI:
    """Service Tickets API Tests"""
    
    def test_list_tickets(self, headers):
        """Test listing service tickets"""
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?page=1&limit=10",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        assert isinstance(data["tickets"], list)
        print(f"Found {data['total']} total tickets")
    
    def test_get_stats(self, headers):
        """Test getting ticket statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets/stats",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "open" in data
        assert "closed" in data
        assert "urgent" in data
        assert "by_status" in data
        assert "by_priority" in data
        print(f"Stats: Total={data['total']}, Open={data['open']}, Closed={data['closed']}, Urgent={data['urgent']}")
    
    def test_get_statuses(self, headers):
        """Test getting all ticket statuses (7 states)"""
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets/statuses",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "statuses" in data
        statuses = data["statuses"]
        assert len(statuses) == 7, f"Expected 7 statuses, got {len(statuses)}"
        
        expected_statuses = ["new", "assigned", "in_progress", "pending_parts", "completed", "closed", "cancelled"]
        actual_statuses = [s["value"] for s in statuses]
        for expected in expected_statuses:
            assert expected in actual_statuses, f"Missing status: {expected}"
        print(f"All 7 statuses present: {actual_statuses}")
    
    def test_filter_by_status(self, headers):
        """Test filtering tickets by status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?status=in_progress&limit=5",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        for ticket in data.get("tickets", []):
            assert ticket["status"] == "in_progress", f"Expected in_progress, got {ticket['status']}"
        print(f"Filter by status working - found {len(data.get('tickets', []))} in_progress tickets")
    
    def test_filter_by_priority(self, headers):
        """Test filtering tickets by priority"""
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?priority=high&limit=5",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        for ticket in data.get("tickets", []):
            assert ticket["priority"] == "high", f"Expected high, got {ticket['priority']}"
        print(f"Filter by priority working - found {len(data.get('tickets', []))} high priority tickets")


class TestTicketLifecycle:
    """Test full ticket lifecycle: NEW -> ASSIGNED -> IN_PROGRESS -> COMPLETED -> CLOSED"""
    
    @pytest.fixture(scope="class")
    def created_ticket(self, headers):
        """Create a test ticket"""
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets",
            headers=headers,
            json={
                "company_id": COMPANY_ID,
                "title": f"TEST_Lifecycle_Ticket_{int(time.time())}",
                "description": "Test ticket for lifecycle testing",
                "priority": "medium"
            }
        )
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        ticket = response.json()
        assert ticket["status"] == "new"
        assert ticket["ticket_number"] is not None
        print(f"Created ticket: {ticket['ticket_number']}")
        return ticket
    
    def test_01_create_ticket(self, created_ticket):
        """Test ticket creation"""
        assert created_ticket["status"] == "new"
        assert created_ticket["company_name"] == "Acme Corporation"
        assert "TEST_Lifecycle_Ticket_" in created_ticket["title"]
        print(f"Ticket {created_ticket['ticket_number']} created with status: {created_ticket['status']}")
    
    def test_02_assign_ticket(self, headers, created_ticket):
        """Test assigning ticket to technician"""
        ticket_id = created_ticket["id"]
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/assign",
            headers=headers,
            json={"technician_id": STAFF_ID}
        )
        assert response.status_code == 200, f"Failed to assign: {response.text}"
        data = response.json()
        assert data["status"] == "assigned"
        assert data["assigned_to_name"] is not None
        print(f"Ticket assigned to: {data['assigned_to_name']}")
    
    def test_03_start_work(self, headers, created_ticket):
        """Test starting work on ticket"""
        ticket_id = created_ticket["id"]
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/start",
            headers=headers
        )
        assert response.status_code == 200, f"Failed to start: {response.text}"
        data = response.json()
        assert data["status"] == "in_progress"
        print(f"Ticket status changed to: {data['status']}")
    
    def test_04_complete_ticket(self, headers, created_ticket):
        """Test completing ticket"""
        ticket_id = created_ticket["id"]
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/complete",
            headers=headers,
            json={
                "resolution_summary": "Issue resolved during testing",
                "resolution_type": "fixed"
            }
        )
        assert response.status_code == 200, f"Failed to complete: {response.text}"
        data = response.json()
        assert data["status"] == "completed"
        print(f"Ticket status changed to: {data['status']}")
    
    def test_05_close_ticket(self, headers, created_ticket):
        """Test closing ticket"""
        ticket_id = created_ticket["id"]
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/close",
            headers=headers,
            json={"closure_notes": "Closed after testing"}
        )
        assert response.status_code == 200, f"Failed to close: {response.text}"
        data = response.json()
        assert data["status"] == "closed"
        print(f"Ticket status changed to: {data['status']}")
    
    def test_06_verify_status_history(self, headers, created_ticket):
        """Verify status history contains all transitions"""
        ticket_id = created_ticket["id"]
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        
        status_history = data.get("status_history", [])
        assert len(status_history) >= 5, f"Expected at least 5 status changes, got {len(status_history)}"
        
        # Verify transitions
        statuses = [h.get("to_status") for h in status_history]
        expected_transitions = ["new", "assigned", "in_progress", "completed", "closed"]
        for expected in expected_transitions:
            assert expected in statuses, f"Missing status transition: {expected}"
        print(f"Status history verified: {statuses}")


class TestOldRoutesRemoved:
    """Test that old ticketing routes return 404"""
    
    def test_old_ticketing_tickets_route(self, headers):
        """Test /api/ticketing/tickets returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("OLD route /api/ticketing/tickets correctly returns 404")
    
    def test_old_admin_tickets_route(self, headers):
        """Test /api/admin/tickets returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin/tickets",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("OLD route /api/admin/tickets correctly returns 404")
    
    def test_old_ticketing_settings_route(self, headers):
        """Test /api/admin/ticketing-settings returns 404"""
        response = requests.get(
            f"{BASE_URL}/api/admin/ticketing-settings",
            headers=headers
        )
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("OLD route /api/admin/ticketing-settings correctly returns 404")


class TestTicketCRUD:
    """Test ticket CRUD operations"""
    
    def test_get_ticket_by_id(self, headers):
        """Test getting a specific ticket by ID"""
        # First get a ticket from the list
        list_response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?limit=1",
            headers=headers
        )
        assert list_response.status_code == 200
        tickets = list_response.json().get("tickets", [])
        
        if tickets:
            ticket_id = tickets[0]["id"]
            response = requests.get(
                f"{BASE_URL}/api/admin/service-tickets/{ticket_id}",
                headers=headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == ticket_id
            assert "visits" in data  # Should include visits
            assert "part_requests" in data  # Should include part requests
            print(f"Got ticket {data['ticket_number']} with {len(data.get('visits', []))} visits")
    
    def test_update_ticket(self, headers):
        """Test updating a ticket"""
        # Create a ticket first
        create_response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets",
            headers=headers,
            json={
                "company_id": COMPANY_ID,
                "title": f"TEST_Update_Ticket_{int(time.time())}",
                "priority": "low"
            }
        )
        assert create_response.status_code == 200
        ticket = create_response.json()
        ticket_id = ticket["id"]
        
        # Update the ticket
        update_response = requests.put(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}",
            headers=headers,
            json={
                "title": "Updated Title",
                "priority": "high",
                "description": "Updated description"
            }
        )
        assert update_response.status_code == 200
        updated = update_response.json()
        assert updated["title"] == "Updated Title"
        assert updated["priority"] == "high"
        print(f"Ticket {ticket['ticket_number']} updated successfully")
    
    def test_add_comment(self, headers):
        """Test adding a comment to a ticket"""
        # Get a ticket
        list_response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets?limit=1",
            headers=headers
        )
        tickets = list_response.json().get("tickets", [])
        
        if tickets:
            ticket_id = tickets[0]["id"]
            response = requests.post(
                f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/comments",
                headers=headers,
                json={
                    "text": "Test comment from pytest",
                    "is_internal": True
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "comment" in data
            print(f"Comment added to ticket successfully")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
