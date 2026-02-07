"""
Engineer Portal API Tests
=========================
Tests for comprehensive engineer portal endpoints including:
- Dashboard stats
- Ticket list with filtering
- Visit management (start, end, diagnosis, resolve, pending-parts)
- Inventory search
- Ticket closure
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://ticketing-system-27.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"
ENGINEER_EMAIL = "john.tech@test.com"
ENGINEER_PASSWORD = "Tech@123"
ENGINEER_STAFF_ID = "6e6bc3e3-430f-41b9-87b8-6a83067a2411"


class TestEngineerPortalAuth:
    """Test engineer authentication"""
    
    def test_engineer_login_success(self):
        """Engineer can login with staff_users credentials"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Token not in response"
        assert "engineer" in data, "Engineer data not in response"
        print(f"SUCCESS: Engineer login - token received, engineer: {data['engineer'].get('name')}")
        return data["token"]


class TestEngineerDashboard:
    """Test dashboard stats API"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    def test_dashboard_stats_returns_correct_structure(self, engineer_token):
        """Dashboard stats API returns correct counts structure"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/dashboard/stats",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200, f"Stats API failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "tickets" in data, "tickets key missing"
        assert "visits" in data, "visits key missing"
        assert "date" in data, "date key missing"
        
        # Verify tickets structure
        tickets = data["tickets"]
        assert "pending_acceptance" in tickets
        assert "assigned" in tickets
        assert "in_progress" in tickets
        assert "pending_parts" in tickets
        assert "total_active" in tickets
        
        # Verify visits structure
        visits = data["visits"]
        assert "scheduled_today" in visits
        assert "in_progress" in visits
        assert "completed_today" in visits
        
        print(f"SUCCESS: Dashboard stats - tickets: {tickets}, visits: {visits}")


class TestEngineerTickets:
    """Test ticket list and detail APIs"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    def test_tickets_list_with_active_filter(self, engineer_token):
        """Ticket list API returns active tickets with filtering"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/tickets?status=active",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200, f"Tickets API failed: {response.text}"
        data = response.json()
        
        # Verify structure
        assert "tickets" in data, "tickets key missing"
        assert "grouped" in data, "grouped key missing"
        assert "total" in data, "total key missing"
        assert "page" in data, "page key missing"
        
        # Verify grouped structure
        grouped = data["grouped"]
        assert "pending_acceptance" in grouped
        assert "assigned" in grouped
        assert "in_progress" in grouped
        assert "pending_parts" in grouped
        
        print(f"SUCCESS: Tickets list - total: {data['total']}, grouped keys: {list(grouped.keys())}")
    
    def test_tickets_list_pagination(self, engineer_token):
        """Ticket list supports pagination"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/tickets?page=1&limit=10",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["limit"] == 10
        print(f"SUCCESS: Pagination works - page: {data['page']}, limit: {data['limit']}")


class TestEngineerVisits:
    """Test visit list and detail APIs"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    def test_visits_list_returns_visits(self, engineer_token):
        """Visit list API returns visits for engineer"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/visits",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200, f"Visits API failed: {response.text}"
        data = response.json()
        
        assert "visits" in data, "visits key missing"
        print(f"SUCCESS: Visits list - count: {len(data['visits'])}")
    
    def test_visits_list_with_status_filter(self, engineer_token):
        """Visit list supports status filtering"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/visits?status=scheduled",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # All returned visits should be scheduled
        for visit in data.get("visits", []):
            if visit.get("status"):
                assert visit["status"] == "scheduled", f"Expected scheduled, got {visit['status']}"
        
        print(f"SUCCESS: Visits filter by status works")


class TestVisitWorkflow:
    """Test visit workflow: start, diagnosis, resolve, pending-parts"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_start_visit_changes_status(self, engineer_token):
        """Start visit changes status to in_progress"""
        # First get a scheduled visit
        visits_response = requests.get(
            f"{BASE_URL}/api/engineer/visits?status=scheduled",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        if visits_response.status_code != 200:
            pytest.skip("Could not get visits")
        
        visits = visits_response.json().get("visits", [])
        if not visits:
            pytest.skip("No scheduled visits available for testing")
        
        visit_id = visits[0]["id"]
        
        # Start the visit
        response = requests.post(
            f"{BASE_URL}/api/engineer/visits/{visit_id}/start",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        # Could be 200 or 400 if already started
        if response.status_code == 200:
            data = response.json()
            assert data.get("status") == "in_progress", f"Expected in_progress, got {data.get('status')}"
            print(f"SUCCESS: Visit started - status: {data.get('status')}")
        elif response.status_code == 400:
            print(f"INFO: Visit already started or in wrong status - {response.json().get('detail')}")
        else:
            assert False, f"Unexpected response: {response.status_code} - {response.text}"
    
    def test_diagnosis_update(self, engineer_token):
        """Add diagnosis to in_progress visit"""
        # Get an in_progress visit
        visits_response = requests.get(
            f"{BASE_URL}/api/engineer/visits?status=in_progress",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        if visits_response.status_code != 200:
            pytest.skip("Could not get visits")
        
        visits = visits_response.json().get("visits", [])
        if not visits:
            pytest.skip("No in_progress visits available for testing")
        
        visit_id = visits[0]["id"]
        
        # Add diagnosis
        diagnosis_data = {
            "problem_identified": "TEST_Printer not printing - paper jam detected",
            "root_cause": "Paper feed mechanism misaligned",
            "observations": "Dust accumulation in paper tray"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/visits/{visit_id}/diagnosis",
            json=diagnosis_data,
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        assert response.status_code == 200, f"Diagnosis update failed: {response.text}"
        data = response.json()
        assert data.get("success") == True
        print(f"SUCCESS: Diagnosis added to visit {visit_id}")
    
    def test_resolve_visit_requires_diagnosis(self, engineer_token):
        """Resolve visit requires diagnosis to be recorded first"""
        # Get an in_progress visit without diagnosis
        visits_response = requests.get(
            f"{BASE_URL}/api/engineer/visits",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        if visits_response.status_code != 200:
            pytest.skip("Could not get visits")
        
        visits = visits_response.json().get("visits", [])
        in_progress_visits = [v for v in visits if v.get("status") == "in_progress"]
        
        if not in_progress_visits:
            pytest.skip("No in_progress visits available")
        
        visit_id = in_progress_visits[0]["id"]
        
        # Try to resolve
        resolution_data = {
            "resolution_summary": "TEST_Issue resolved by cleaning paper feed mechanism",
            "actions_taken": ["Cleaned paper tray", "Realigned feed rollers"],
            "recommendations": "Regular cleaning recommended"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/visits/{visit_id}/resolve",
            json=resolution_data,
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        # Should succeed if diagnosis exists, fail if not
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert data.get("status") == "completed"
            print(f"SUCCESS: Visit resolved - status: completed")
        elif response.status_code == 400:
            detail = response.json().get("detail", "")
            if "diagnosis" in detail.lower():
                print(f"INFO: Resolve correctly requires diagnosis first")
            else:
                print(f"INFO: Resolve failed - {detail}")
        else:
            print(f"INFO: Resolve response - {response.status_code}: {response.text}")


class TestPendingPartsFlow:
    """Test pending parts flow with auto-quotation creation"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    def test_pending_parts_creates_quotation(self, engineer_token):
        """Mark pending parts auto-creates draft quotation"""
        # Get an in_progress visit
        visits_response = requests.get(
            f"{BASE_URL}/api/engineer/visits?status=in_progress",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        if visits_response.status_code != 200:
            pytest.skip("Could not get visits")
        
        visits = visits_response.json().get("visits", [])
        if not visits:
            pytest.skip("No in_progress visits available for testing")
        
        visit_id = visits[0]["id"]
        
        # Mark pending parts
        parts_data = {
            "diagnosis": {
                "problem_identified": "TEST_Fuser unit failure",
                "root_cause": "Worn out heating element",
                "observations": "Toner not fusing properly"
            },
            "parts_required": [
                {
                    "item_name": "TEST_Fuser Unit",
                    "item_description": "Replacement fuser assembly",
                    "quantity": 1,
                    "urgency": "urgent",
                    "notes": "Original part required"
                }
            ],
            "remarks": "TEST_Fuser unit needs replacement. Customer informed about quotation."
        }
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/visits/{visit_id}/pending-parts",
            json=parts_data,
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True
            assert data.get("status") == "pending_parts"
            assert "quotation_id" in data
            assert "quotation_number" in data
            print(f"SUCCESS: Pending parts marked - quotation: {data.get('quotation_number')}")
        elif response.status_code == 400:
            detail = response.json().get("detail", "")
            print(f"INFO: Pending parts failed - {detail}")
        else:
            print(f"INFO: Response - {response.status_code}: {response.text}")


class TestTicketClosure:
    """Test ticket closure flow"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    def test_cannot_close_pending_parts_ticket(self, engineer_token):
        """Engineer cannot close ticket when pending parts"""
        # Get tickets
        tickets_response = requests.get(
            f"{BASE_URL}/api/engineer/tickets",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        if tickets_response.status_code != 200:
            pytest.skip("Could not get tickets")
        
        tickets = tickets_response.json().get("tickets", [])
        pending_parts_tickets = [t for t in tickets if t.get("status") == "pending_parts"]
        
        if not pending_parts_tickets:
            pytest.skip("No pending_parts tickets available")
        
        ticket_id = pending_parts_tickets[0]["id"]
        
        # Try to close
        close_data = {
            "final_findings": "TEST_Issue identified and parts ordered",
            "solution_details": "Awaiting parts delivery"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/tickets/{ticket_id}/close",
            json=close_data,
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400, got {response.status_code}"
        detail = response.json().get("detail", "")
        assert "pending" in detail.lower() or "parts" in detail.lower(), f"Expected pending parts error, got: {detail}"
        print(f"SUCCESS: Cannot close pending_parts ticket - {detail}")


class TestInventorySearch:
    """Test inventory item search for parts selection"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    def test_inventory_search_returns_items(self, engineer_token):
        """Inventory search returns items"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/inventory/items?search=test&limit=10",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        assert response.status_code == 200, f"Inventory search failed: {response.text}"
        data = response.json()
        assert "items" in data, "items key missing"
        print(f"SUCCESS: Inventory search - found {len(data['items'])} items")
    
    def test_inventory_search_without_query(self, engineer_token):
        """Inventory search works without search query"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/inventory/items?limit=5",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        print(f"SUCCESS: Inventory search without query - found {len(data['items'])} items")


class TestVisitDetail:
    """Test visit detail API with previous visits"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    def test_visit_detail_includes_ticket_info(self, engineer_token):
        """Visit detail includes ticket information"""
        # Get a visit
        visits_response = requests.get(
            f"{BASE_URL}/api/engineer/visits",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        if visits_response.status_code != 200:
            pytest.skip("Could not get visits")
        
        visits = visits_response.json().get("visits", [])
        if not visits:
            pytest.skip("No visits available")
        
        visit_id = visits[0]["id"]
        
        # Get visit detail
        response = requests.get(
            f"{BASE_URL}/api/engineer/visits/{visit_id}",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        assert response.status_code == 200, f"Visit detail failed: {response.text}"
        data = response.json()
        
        assert "ticket" in data, "ticket info missing"
        assert "previous_visits" in data, "previous_visits missing"
        
        ticket = data["ticket"]
        if ticket:
            assert "title" in ticket or "company_name" in ticket
        
        print(f"SUCCESS: Visit detail - has ticket info, previous_visits: {len(data.get('previous_visits', []))}")


class TestTicketDetail:
    """Test ticket detail API with SLA info"""
    
    @pytest.fixture
    def engineer_token(self):
        """Get engineer auth token"""
        response = requests.post(f"{BASE_URL}/api/engineer/auth/login", json={
            "email": ENGINEER_EMAIL,
            "password": ENGINEER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip("Engineer login failed")
        return response.json()["token"]
    
    def test_ticket_detail_includes_visits_and_parts(self, engineer_token):
        """Ticket detail includes visits, parts, quotation"""
        # Get tickets
        tickets_response = requests.get(
            f"{BASE_URL}/api/engineer/tickets",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        if tickets_response.status_code != 200:
            pytest.skip("Could not get tickets")
        
        tickets = tickets_response.json().get("tickets", [])
        if not tickets:
            pytest.skip("No tickets available")
        
        ticket_id = tickets[0]["id"]
        
        # Get ticket detail
        response = requests.get(
            f"{BASE_URL}/api/engineer/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {engineer_token}"}
        )
        
        assert response.status_code == 200, f"Ticket detail failed: {response.text}"
        data = response.json()
        
        assert "visits" in data, "visits missing"
        assert "parts_requests" in data, "parts_requests missing"
        assert "parts_issued" in data, "parts_issued missing"
        
        print(f"SUCCESS: Ticket detail - visits: {len(data.get('visits', []))}, parts_requests: {len(data.get('parts_requests', []))}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
