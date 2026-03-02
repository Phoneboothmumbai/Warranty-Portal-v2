"""
Test: Admin Ticket Dashboard V2 - Two-section layout with assigned/unassigned filters
=====================================================================================
Tests the redesigned /admin/service-requests page features:
- GET /api/ticketing/tickets with 'assigned' filter (true/false)
- GET /api/ticketing/tickets with 'status' filter (stage name)
- GET /api/ticketing/stats returns 'unassigned' count and 'by_stage' breakdown
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from review_request
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    if response.status_code == 200:
        data = response.json()
        # Token key is 'access_token' per agent_to_agent_context_note
        return data.get("access_token") or data.get("token")
    pytest.skip(f"Auth failed with status {response.status_code}")


@pytest.fixture(scope="module")
def auth_headers(admin_token):
    """Headers with authorization"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestTicketingStatsEndpoint:
    """Test GET /api/ticketing/stats returns new fields"""

    def test_stats_returns_unassigned_count(self, auth_headers):
        """Stats should include 'unassigned' count"""
        response = requests.get(f"{BASE_URL}/api/ticketing/stats", headers=auth_headers)
        assert response.status_code == 200, f"Stats endpoint failed: {response.text}"
        
        data = response.json()
        # Verify 'unassigned' field exists
        assert "unassigned" in data, f"Missing 'unassigned' in stats: {data.keys()}"
        assert isinstance(data["unassigned"], int), f"unassigned should be int, got {type(data['unassigned'])}"
        print(f"✓ Stats 'unassigned' count: {data['unassigned']}")

    def test_stats_returns_by_stage(self, auth_headers):
        """Stats should include 'by_stage' breakdown for filter pills"""
        response = requests.get(f"{BASE_URL}/api/ticketing/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        # Verify 'by_stage' field exists
        assert "by_stage" in data, f"Missing 'by_stage' in stats: {data.keys()}"
        assert isinstance(data["by_stage"], dict), f"by_stage should be dict, got {type(data['by_stage'])}"
        
        # Log stage breakdown
        print(f"✓ Stats 'by_stage' breakdown: {data['by_stage']}")
        
    def test_stats_returns_all_required_fields(self, auth_headers):
        """Stats should have total, open, closed, unassigned, by_priority, by_topic, by_stage"""
        response = requests.get(f"{BASE_URL}/api/ticketing/stats", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        required_fields = ["total", "open", "closed", "unassigned", "by_priority", "by_topic", "by_stage"]
        for field in required_fields:
            assert field in data, f"Missing field '{field}' in stats"
        
        print(f"✓ All required stats fields present: total={data['total']}, open={data['open']}, closed={data['closed']}, unassigned={data['unassigned']}")


class TestTicketsAssignedFilter:
    """Test GET /api/ticketing/tickets with 'assigned' query param"""

    def test_list_unassigned_tickets(self, auth_headers):
        """assigned=false should return only tickets without assigned_to_name"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"assigned": "false", "limit": "50"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "tickets" in data, f"Response missing 'tickets' key"
        
        unassigned_tickets = data["tickets"]
        print(f"✓ Unassigned tickets returned: {len(unassigned_tickets)}")
        
        # Verify all returned tickets have no assigned_to_name
        for ticket in unassigned_tickets:
            assigned_to = ticket.get("assigned_to_name")
            assert assigned_to is None or assigned_to == "", \
                f"Ticket {ticket.get('ticket_number')} has assigned_to_name='{assigned_to}' but should be unassigned"
        
        print(f"✓ All {len(unassigned_tickets)} unassigned tickets verified (no assigned_to_name)")

    def test_list_assigned_tickets(self, auth_headers):
        """assigned=true should return only tickets with assigned_to_name"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"assigned": "true", "limit": "50"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "tickets" in data
        
        assigned_tickets = data["tickets"]
        total_assigned = data.get("total", len(assigned_tickets))
        print(f"✓ Assigned tickets returned: {len(assigned_tickets)} (total: {total_assigned})")
        
        # Verify all returned tickets have assigned_to_name
        for ticket in assigned_tickets:
            assigned_to = ticket.get("assigned_to_name")
            assert assigned_to is not None and assigned_to != "", \
                f"Ticket {ticket.get('ticket_number')} has no assigned_to_name but should be assigned"
        
        print(f"✓ All {len(assigned_tickets)} assigned tickets verified (have assigned_to_name)")

    def test_assigned_tickets_pagination(self, auth_headers):
        """Assigned tickets section should support pagination"""
        # Page 1
        response1 = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"assigned": "true", "page": "1", "limit": "5"},
            headers=auth_headers
        )
        assert response1.status_code == 200
        data1 = response1.json()
        
        assert "page" in data1, "Missing 'page' in response"
        assert "pages" in data1, "Missing 'pages' in response"
        assert "total" in data1, "Missing 'total' in response"
        
        print(f"✓ Pagination works: page={data1['page']}, pages={data1['pages']}, total={data1['total']}")


class TestTicketsStatusFilter:
    """Test GET /api/ticketing/tickets with 'status' query param (stage filter)"""

    def test_filter_by_stage_new(self, auth_headers):
        """status=New should filter by current_stage_name"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"status": "New", "limit": "50"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        tickets = data.get("tickets", [])
        
        # All returned tickets should have current_stage_name = "New"
        for ticket in tickets:
            stage = ticket.get("current_stage_name")
            assert stage == "New", f"Ticket {ticket.get('ticket_number')} has stage '{stage}', expected 'New'"
        
        print(f"✓ Status filter 'New' works: {len(tickets)} tickets returned")

    def test_filter_by_stage_assigned(self, auth_headers):
        """status=Assigned should filter by current_stage_name"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"status": "Assigned", "limit": "50"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        tickets = data.get("tickets", [])
        
        for ticket in tickets:
            stage = ticket.get("current_stage_name")
            assert stage == "Assigned", f"Ticket {ticket.get('ticket_number')} has stage '{stage}', expected 'Assigned'"
        
        print(f"✓ Status filter 'Assigned' works: {len(tickets)} tickets returned")

    def test_filter_by_stage_in_progress(self, auth_headers):
        """status='In Progress' should filter by current_stage_name"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"status": "In Progress", "limit": "50"},
            headers=auth_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        tickets = data.get("tickets", [])
        
        for ticket in tickets:
            stage = ticket.get("current_stage_name")
            assert stage == "In Progress", f"Ticket {ticket.get('ticket_number')} has stage '{stage}', expected 'In Progress'"
        
        print(f"✓ Status filter 'In Progress' works: {len(tickets)} tickets returned")

    def test_combined_assigned_and_status_filter(self, auth_headers):
        """Combining assigned=true with status filter should work"""
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"assigned": "true", "status": "In Progress", "limit": "50"},
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        tickets = data.get("tickets", [])
        
        for ticket in tickets:
            # Should be assigned
            assert ticket.get("assigned_to_name"), f"Ticket {ticket.get('ticket_number')} should be assigned"
            # Should have status "In Progress"
            assert ticket.get("current_stage_name") == "In Progress", \
                f"Ticket {ticket.get('ticket_number')} stage is {ticket.get('current_stage_name')}"
        
        print(f"✓ Combined filter (assigned + status) works: {len(tickets)} tickets")


class TestTicketsSearchFilter:
    """Test GET /api/ticketing/tickets with 'search' query param"""

    def test_search_filters_both_sections(self, auth_headers):
        """Search should work with assigned filter"""
        # First get any ticket number
        response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"limit": "1"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("tickets"):
            ticket_number = data["tickets"][0].get("ticket_number", "")
            if ticket_number:
                # Search for this ticket
                search_response = requests.get(
                    f"{BASE_URL}/api/ticketing/tickets",
                    params={"search": ticket_number, "limit": "50"},
                    headers=auth_headers
                )
                assert search_response.status_code == 200
                search_data = search_response.json()
                
                # Should find at least the ticket we searched for
                found = any(t.get("ticket_number") == ticket_number for t in search_data.get("tickets", []))
                assert found, f"Search for '{ticket_number}' should find the ticket"
                print(f"✓ Search filter works: found ticket {ticket_number}")
        else:
            print("⚠ No tickets to test search with")


class TestDataIntegrity:
    """Verify stats match actual ticket counts"""

    def test_unassigned_count_matches(self, auth_headers):
        """Stats unassigned count should match actual unassigned tickets"""
        # Get stats
        stats_response = requests.get(f"{BASE_URL}/api/ticketing/stats", headers=auth_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        
        # Get unassigned tickets
        tickets_response = requests.get(
            f"{BASE_URL}/api/ticketing/tickets",
            params={"assigned": "false", "limit": "100"},
            headers=auth_headers
        )
        assert tickets_response.status_code == 200
        tickets_data = tickets_response.json()
        
        # Compare - use total from tickets response if available, else count
        actual_unassigned = tickets_data.get("total", len(tickets_data.get("tickets", [])))
        stats_unassigned = stats.get("unassigned", 0)
        
        # Allow small discrepancy due to concurrent changes
        assert abs(stats_unassigned - actual_unassigned) <= 2, \
            f"Stats unassigned ({stats_unassigned}) doesn't match actual ({actual_unassigned})"
        
        print(f"✓ Unassigned count matches: stats={stats_unassigned}, actual={actual_unassigned}")

    def test_stage_counts_match(self, auth_headers):
        """Stats by_stage counts should match filtered ticket counts"""
        # Get stats
        stats_response = requests.get(f"{BASE_URL}/api/ticketing/stats", headers=auth_headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        by_stage = stats.get("by_stage", {})
        
        # Test first stage found
        if by_stage:
            stage_name = list(by_stage.keys())[0]
            expected_count = by_stage[stage_name]
            
            # Get tickets with this stage
            tickets_response = requests.get(
                f"{BASE_URL}/api/ticketing/tickets",
                params={"status": stage_name, "limit": "100"},
                headers=auth_headers
            )
            assert tickets_response.status_code == 200
            tickets_data = tickets_response.json()
            actual_count = tickets_data.get("total", len(tickets_data.get("tickets", [])))
            
            # Allow small discrepancy
            assert abs(expected_count - actual_count) <= 2, \
                f"Stage '{stage_name}' count mismatch: stats={expected_count}, actual={actual_count}"
            
            print(f"✓ Stage '{stage_name}' count matches: stats={expected_count}, actual={actual_count}")
        else:
            print("⚠ No stages in by_stage to verify")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
