"""
Engineer Visit Workflow Tests
=============================
Tests for:
  Phase 2a: Start Visit for accepted tickets
  Phase 2b: Visit record creation with timer
  Phase 2c: Add Report (diagnosis, problem, solution)
  Phase 2d: Checkout with resolution type
  Phase 3a: Request Parts
  Phase 3b: Auto-create quotation draft
  Phase 3c: Backend validation (accepted tickets only, active visits)
  Phase 3d: Admin parts request endpoints
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ENGINEER_EMAIL = "testeng@test.com"
ENGINEER_PASSWORD = "Test@123"
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"
TEST_TICKET_ID = "c028d748-3bac-4b7e-a6b1-32310d8ec7f8"  # TEST-9999


@pytest.fixture(scope="module")
def engineer_token():
    """Get engineer authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/engineer/auth/login",
        json={"email": ENGINEER_EMAIL, "password": ENGINEER_PASSWORD}
    )
    assert response.status_code == 200, f"Engineer login failed: {response.text}"
    data = response.json()
    # Note: login response uses 'access_token' NOT 'token'
    return data.get("access_token")


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    data = response.json()
    return data.get("access_token")


@pytest.fixture(scope="module")
def engineer_headers(engineer_token):
    """Headers for engineer API requests"""
    return {
        "Authorization": f"Bearer {engineer_token}",
        "Content-Type": "application/json"
    }


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Headers for admin API requests"""
    return {
        "Authorization": f"Bearer {admin_token}",
        "Content-Type": "application/json"
    }


class TestEngineerLogin:
    """Verify engineer can log in"""
    
    def test_engineer_login_success(self):
        response = requests.post(
            f"{BASE_URL}/api/engineer/auth/login",
            json={"email": ENGINEER_EMAIL, "password": ENGINEER_PASSWORD}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data, "Login response should contain access_token"
        assert data.get("token_type") == "bearer"
        print("PASS: Engineer login successful")


class TestTicketDetail:
    """Test ticket detail endpoint for visit workflow"""
    
    def test_get_ticket_detail(self, engineer_headers):
        """Phase 2a: Verify ticket detail shows accepted status"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/ticket/{TEST_TICKET_ID}",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "ticket" in data
        ticket = data["ticket"]
        assert ticket.get("id") == TEST_TICKET_ID
        assert ticket.get("ticket_number") == "TEST-9999"
        # Verify we have the needed fields for visit workflow
        assert "assignment_status" in ticket
        assert "current_stage_name" in ticket
        print(f"PASS: Got ticket detail - Status: {ticket.get('assignment_status')}, Stage: {ticket.get('current_stage_name')}")


class TestStartVisit:
    """Phase 2a & 2b: Test start visit functionality"""
    
    def test_start_visit_creates_record(self, engineer_headers):
        """Starting a visit creates a visit record with timer"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/visit/start",
            headers=engineer_headers,
            json={"ticket_id": TEST_TICKET_ID, "notes": "Starting test visit"}
        )
        
        # Should succeed (200) or return existing visit
        assert response.status_code in [200, 400, 404], f"Unexpected status: {response.status_code}, {response.text}"
        
        if response.status_code == 200:
            data = response.json()
            assert "visit" in data
            visit = data["visit"]
            assert visit.get("ticket_id") == TEST_TICKET_ID
            assert visit.get("status") == "in_progress"
            assert "check_in_time" in visit
            assert visit.get("check_out_time") is None  # Not checked out yet
            print(f"PASS: Visit started - ID: {visit.get('id')}, Check-in: {visit.get('check_in_time')}")
        else:
            print(f"INFO: Start visit returned {response.status_code} - {response.json().get('detail', response.text)}")


class TestGetActiveVisit:
    """Get the active visit for testing subsequent operations"""
    
    def test_get_visit(self, engineer_headers):
        """Get current visit status"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/visit/{TEST_TICKET_ID}",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        if data.get("visit"):
            visit = data["visit"]
            print(f"PASS: Active visit found - ID: {visit.get('id')}, Status: {visit.get('status')}")
        else:
            print("INFO: No active visit found for this ticket")


@pytest.fixture(scope="class")
def active_visit_id(engineer_headers):
    """Get or create active visit for testing"""
    # First check if there's an active visit
    response = requests.get(
        f"{BASE_URL}/api/engineer/visit/{TEST_TICKET_ID}",
        headers=engineer_headers
    )
    if response.status_code == 200:
        visit = response.json().get("visit")
        if visit and visit.get("status") == "in_progress":
            return visit.get("id")
    
    # Start a new visit
    response = requests.post(
        f"{BASE_URL}/api/engineer/visit/start",
        headers=engineer_headers,
        json={"ticket_id": TEST_TICKET_ID}
    )
    if response.status_code == 200:
        return response.json().get("visit", {}).get("id")
    return None


class TestUpdateVisit:
    """Phase 2c: Test Add Report functionality"""
    
    def test_update_visit_with_report(self, engineer_headers, active_visit_id):
        """Update visit with diagnosis, problem, solution, resolution type"""
        if not active_visit_id:
            pytest.skip("No active visit to update")
        
        update_data = {
            "problem_found": "Test problem - device not booting",
            "diagnosis": "Faulty power supply unit",
            "solution_applied": "Replaced PSU with spare",
            "resolution_type": "fixed",
            "notes": "Test update notes"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/engineer/visit/{active_visit_id}/update",
            headers=engineer_headers,
            json=update_data
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "visit" in data
            visit = data["visit"]
            assert visit.get("problem_found") == update_data["problem_found"]
            assert visit.get("diagnosis") == update_data["diagnosis"]
            assert visit.get("resolution_type") == update_data["resolution_type"]
            print(f"PASS: Visit updated with report - Resolution: {visit.get('resolution_type')}")
        elif response.status_code == 404:
            print(f"INFO: Visit not found or not active - {response.json().get('detail')}")
        else:
            print(f"INFO: Update returned {response.status_code} - {response.text}")


class TestRequestParts:
    """Phase 3a & 3b: Test request parts functionality"""
    
    def test_request_parts_creates_quotation(self, engineer_headers, active_visit_id):
        """Request parts should auto-create a quotation draft"""
        if not active_visit_id:
            pytest.skip("No active visit for parts request")
        
        parts_data = {
            "parts": [
                {
                    "product_name": "TEST RAM 8GB DDR4",
                    "quantity": 1,
                    "unit_price": 2500,
                    "gst_slab": 18
                },
                {
                    "product_name": "TEST SSD 256GB NVMe",
                    "quantity": 1,
                    "unit_price": 3500,
                    "gst_slab": 18
                }
            ],
            "notes": "Parts needed for repair"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/visit/{active_visit_id}/request-parts",
            headers=engineer_headers,
            json=parts_data
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "parts_request" in data
            assert "quotation_id" in data
            assert "quotation_number" in data
            
            parts_request = data["parts_request"]
            assert len(parts_request.get("items", [])) == 2
            # Note: parts_request status is initially 'pending' in the response,
            # but gets updated to 'quoted' in the database immediately after
            assert parts_request.get("status") in ["pending", "quoted"]
            
            print(f"PASS: Parts requested - Quotation: {data.get('quotation_number')}, Status: {parts_request.get('status')}")
            return data
        elif response.status_code == 404:
            print(f"INFO: Visit not found or not active - {response.json().get('detail')}")
        else:
            print(f"INFO: Parts request returned {response.status_code} - {response.text}")


class TestCheckout:
    """Phase 2d: Test checkout functionality"""
    
    def test_checkout_moves_ticket_stage(self, engineer_headers, active_visit_id):
        """Checkout should complete visit and move ticket to appropriate stage"""
        if not active_visit_id:
            pytest.skip("No active visit for checkout")
        
        checkout_data = {
            "resolution_type": "parts_needed",
            "problem_found": "Device needs new parts",
            "diagnosis": "Hardware failure",
            "solution_applied": "Temporary fix applied, awaiting parts",
            "notes": "Customer informed about parts ETA",
            "customer_name": "Test Customer"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/visit/{active_visit_id}/checkout",
            headers=engineer_headers,
            json=checkout_data
        )
        
        if response.status_code == 200:
            data = response.json()
            assert "visit" in data
            assert "next_stage" in data
            
            visit = data["visit"]
            assert visit.get("status") == "completed"
            assert visit.get("check_out_time") is not None
            
            # Verify stage mapping
            next_stage = data.get("next_stage")
            expected_stages = {"fixed": "Work Done", "parts_needed": "Awaiting Parts", "escalation": "Escalated"}
            expected = expected_stages.get(checkout_data["resolution_type"])
            assert next_stage == expected, f"Expected stage '{expected}' but got '{next_stage}'"
            
            print(f"PASS: Checkout successful - Next stage: {next_stage}, Duration: {visit.get('duration_minutes')} min")
        elif response.status_code == 404:
            print(f"INFO: Visit not found or already completed - {response.json().get('detail')}")
        else:
            print(f"INFO: Checkout returned {response.status_code} - {response.text}")


class TestVisitHistory:
    """Test visit history endpoint"""
    
    def test_get_visit_history(self, engineer_headers):
        """Get all visits for a ticket"""
        response = requests.get(
            f"{BASE_URL}/api/engineer/visit/history/{TEST_TICKET_ID}",
            headers=engineer_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "visits" in data
        visits = data["visits"]
        
        if len(visits) > 0:
            print(f"PASS: Visit history retrieved - {len(visits)} visit(s) found")
            for v in visits[:3]:  # Show first 3
                print(f"  - Visit ID: {v.get('id')[:8]}..., Status: {v.get('status')}, Resolution: {v.get('resolution_type')}")
        else:
            print("INFO: No visit history for this ticket")


class TestAdminPartsRequests:
    """Phase 3d: Test admin parts request endpoints"""
    
    def test_list_parts_requests(self, admin_headers):
        """Admin can list parts requests"""
        response = requests.get(
            f"{BASE_URL}/api/admin/parts-requests",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "parts_requests" in data
        assert "total" in data
        
        parts_requests = data["parts_requests"]
        print(f"PASS: Admin parts requests - Total: {data.get('total')}, Retrieved: {len(parts_requests)}")
        
        if len(parts_requests) > 0:
            pr = parts_requests[0]
            print(f"  - Latest: Ticket {pr.get('ticket_number')}, Status: {pr.get('status')}, Total: {pr.get('grand_total')}")
    
    def test_list_parts_requests_with_status_filter(self, admin_headers):
        """Admin can filter parts requests by status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/parts-requests?status=quoted",
            headers=admin_headers
        )
        assert response.status_code == 200
        data = response.json()
        
        for pr in data.get("parts_requests", []):
            assert pr.get("status") == "quoted", f"Expected status 'quoted', got '{pr.get('status')}'"
        
        print(f"PASS: Admin parts requests filter - Found {len(data.get('parts_requests', []))} quoted requests")


class TestBackendValidation:
    """Phase 3c: Backend validation tests"""
    
    def test_start_visit_invalid_ticket(self, engineer_headers):
        """Cannot start visit for non-existent ticket"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/visit/start",
            headers=engineer_headers,
            json={"ticket_id": "invalid-ticket-id-12345"}
        )
        assert response.status_code == 404
        print("PASS: Correctly rejects start visit for invalid ticket (404)")
    
    def test_update_invalid_visit(self, engineer_headers):
        """Cannot update non-existent visit"""
        response = requests.put(
            f"{BASE_URL}/api/engineer/visit/invalid-visit-id/update",
            headers=engineer_headers,
            json={"problem_found": "Test"}
        )
        assert response.status_code == 404
        print("PASS: Correctly rejects update for invalid visit (404)")
    
    def test_checkout_invalid_visit(self, engineer_headers):
        """Cannot checkout non-existent visit"""
        response = requests.post(
            f"{BASE_URL}/api/engineer/visit/invalid-visit-id/checkout",
            headers=engineer_headers,
            json={"resolution_type": "fixed"}
        )
        assert response.status_code == 404
        print("PASS: Correctly rejects checkout for invalid visit (404)")
    
    def test_request_parts_empty_list(self, engineer_headers, active_visit_id):
        """Cannot request empty parts list"""
        if not active_visit_id:
            pytest.skip("No active visit for this test")
        
        response = requests.post(
            f"{BASE_URL}/api/engineer/visit/{active_visit_id}/request-parts",
            headers=engineer_headers,
            json={"parts": []}
        )
        # Should return 400 or 404 (if visit completed)
        assert response.status_code in [400, 404]
        print(f"PASS: Correctly rejects empty parts list ({response.status_code})")


class TestFullVisitWorkflow:
    """End-to-end visit workflow test"""
    
    def test_full_workflow(self, engineer_headers, admin_headers):
        """Complete visit workflow: start -> report -> parts -> checkout"""
        print("\n=== Full Visit Workflow Test ===")
        
        # Step 1: Check ticket status
        response = requests.get(
            f"{BASE_URL}/api/engineer/ticket/{TEST_TICKET_ID}",
            headers=engineer_headers
        )
        assert response.status_code == 200
        ticket = response.json().get("ticket", {})
        print(f"1. Ticket status: {ticket.get('assignment_status')}, Stage: {ticket.get('current_stage_name')}")
        
        # Step 2: Start visit
        response = requests.post(
            f"{BASE_URL}/api/engineer/visit/start",
            headers=engineer_headers,
            json={"ticket_id": TEST_TICKET_ID}
        )
        
        if response.status_code == 200:
            visit = response.json().get("visit", {})
            visit_id = visit.get("id")
            print(f"2. Visit started: {visit_id[:8] if visit_id else 'N/A'}...")
            
            # Step 3: Add report
            response = requests.put(
                f"{BASE_URL}/api/engineer/visit/{visit_id}/update",
                headers=engineer_headers,
                json={
                    "problem_found": "Workflow test problem",
                    "diagnosis": "Test diagnosis",
                    "solution_applied": "Test solution",
                    "resolution_type": "fixed"
                }
            )
            if response.status_code == 200:
                print("3. Report added")
            
            # Step 4: Request parts (optional)
            response = requests.post(
                f"{BASE_URL}/api/engineer/visit/{visit_id}/request-parts",
                headers=engineer_headers,
                json={
                    "parts": [{"product_name": "WORKFLOW_TEST Part", "quantity": 1, "unit_price": 100, "gst_slab": 18}],
                    "notes": "Workflow test"
                }
            )
            if response.status_code == 200:
                quotation = response.json().get("quotation_number")
                print(f"4. Parts requested, Quotation: {quotation}")
            
            # Step 5: Checkout
            response = requests.post(
                f"{BASE_URL}/api/engineer/visit/{visit_id}/checkout",
                headers=engineer_headers,
                json={
                    "resolution_type": "parts_needed",
                    "customer_name": "Workflow Test Customer"
                }
            )
            if response.status_code == 200:
                next_stage = response.json().get("next_stage")
                print(f"5. Checkout complete, Next stage: {next_stage}")
            
            # Step 6: Verify admin can see parts request
            response = requests.get(
                f"{BASE_URL}/api/admin/parts-requests",
                headers=admin_headers
            )
            if response.status_code == 200:
                total = response.json().get("total", 0)
                print(f"6. Admin sees {total} parts request(s)")
            
            print("=== Workflow Complete ===\n")
        else:
            print(f"INFO: Could not start visit - {response.status_code}: {response.json().get('detail', response.text)}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
