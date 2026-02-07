"""
Test Device Dashboard and Company Service Tickets APIs
Tests for:
- Company Service Tickets API (/api/company/service-tickets)
- Device Analytics API (/api/company/devices/:id/analytics)
- Create Service Ticket from Company Portal
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
COMPANY_USER = {"email": "testuser@testcompany.com", "password": "Test@123"}
ADMIN_USER = {"email": "ck@motta.in", "password": "Charu@123@"}

# Test device ID from context
TEST_DEVICE_ID = "206eb754-b34e-4387-8262-a64543a3c769"


class TestCompanyAuth:
    """Test company user authentication"""
    
    @pytest.fixture(scope="class")
    def company_token(self):
        """Get company user auth token"""
        response = requests.post(f"{BASE_URL}/api/company/auth/login", json=COMPANY_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Company auth failed: {response.status_code} - {response.text}")
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin auth failed: {response.status_code} - {response.text}")
    
    def test_company_login(self):
        """Test company user can login"""
        response = requests.post(f"{BASE_URL}/api/company/auth/login", json=COMPANY_USER)
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        print(f"✓ Company login successful")


class TestCompanyServiceTickets:
    """Test Company Service Tickets API"""
    
    @pytest.fixture(scope="class")
    def company_token(self):
        """Get company user auth token"""
        response = requests.post(f"{BASE_URL}/api/company/auth/login", json=COMPANY_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Company auth failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def headers(self, company_token):
        return {"Authorization": f"Bearer {company_token}"}
    
    def test_list_company_tickets(self, headers):
        """Test listing company service tickets"""
        response = requests.get(f"{BASE_URL}/api/company/service-tickets", headers=headers)
        assert response.status_code == 200, f"Failed to list tickets: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "tickets" in data
        assert "total" in data
        assert "page" in data
        assert "limit" in data
        assert isinstance(data["tickets"], list)
        print(f"✓ Listed {len(data['tickets'])} company tickets (total: {data['total']})")
    
    def test_list_tickets_with_status_filter(self, headers):
        """Test filtering tickets by status"""
        response = requests.get(f"{BASE_URL}/api/company/service-tickets?status=new", headers=headers)
        assert response.status_code == 200, f"Failed to filter tickets: {response.text}"
        data = response.json()
        
        # All returned tickets should have status 'new'
        for ticket in data.get("tickets", []):
            assert ticket.get("status") == "new", f"Ticket {ticket.get('id')} has wrong status"
        print(f"✓ Status filter working - found {len(data['tickets'])} 'new' tickets")
    
    def test_list_tickets_with_search(self, headers):
        """Test searching tickets"""
        response = requests.get(f"{BASE_URL}/api/company/service-tickets?search=test", headers=headers)
        assert response.status_code == 200, f"Failed to search tickets: {response.text}"
        data = response.json()
        assert isinstance(data["tickets"], list)
        print(f"✓ Search working - found {len(data['tickets'])} tickets matching 'test'")
    
    def test_create_service_ticket(self, headers):
        """Test creating a new service ticket from company portal"""
        ticket_data = {
            "title": f"TEST_Ticket_{uuid.uuid4().hex[:6]}",
            "description": "Test ticket created from company portal for testing",
            "priority": "medium",
            "contact_name": "Test User",
            "contact_phone": "+91 9876543210"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/service-tickets",
            headers=headers,
            params=ticket_data  # API uses query params
        )
        
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        data = response.json()
        
        # Verify ticket was created
        assert "id" in data
        assert "ticket_number" in data
        assert data["title"] == ticket_data["title"]
        assert data["status"] == "new"
        assert data["created_by_type"] == "company_user"
        
        print(f"✓ Created ticket #{data['ticket_number']} with ID {data['id']}")
        return data["id"]
    
    def test_create_ticket_with_device(self, headers):
        """Test creating a ticket with device pre-selected"""
        ticket_data = {
            "device_id": TEST_DEVICE_ID,
            "title": f"TEST_Device_Ticket_{uuid.uuid4().hex[:6]}",
            "description": "Test ticket for specific device",
            "priority": "high"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/service-tickets",
            headers=headers,
            params=ticket_data
        )
        
        assert response.status_code == 200, f"Failed to create device ticket: {response.text}"
        data = response.json()
        
        assert data["device_id"] == TEST_DEVICE_ID
        assert data.get("device_serial") is not None or data.get("device_brand") is not None
        print(f"✓ Created device ticket #{data['ticket_number']} for device {TEST_DEVICE_ID}")
        return data["id"]
    
    def test_get_ticket_detail(self, headers):
        """Test getting ticket detail"""
        # First create a ticket
        ticket_data = {
            "title": f"TEST_Detail_{uuid.uuid4().hex[:6]}",
            "description": "Test ticket for detail view"
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/company/service-tickets",
            headers=headers,
            params=ticket_data
        )
        assert create_response.status_code == 200
        ticket_id = create_response.json()["id"]
        
        # Get ticket detail
        response = requests.get(f"{BASE_URL}/api/company/service-tickets/{ticket_id}", headers=headers)
        assert response.status_code == 200, f"Failed to get ticket detail: {response.text}"
        data = response.json()
        
        # Verify ticket data
        assert data["id"] == ticket_id
        assert data["title"] == ticket_data["title"]
        assert "status" in data
        assert "created_at" in data
        print(f"✓ Got ticket detail for #{data['ticket_number']}")
    
    def test_get_nonexistent_ticket(self, headers):
        """Test getting a non-existent ticket returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/company/service-tickets/{fake_id}", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent ticket returns 404")


class TestDeviceAnalytics:
    """Test Device Analytics API for Device Dashboard"""
    
    @pytest.fixture(scope="class")
    def company_token(self):
        """Get company user auth token"""
        response = requests.post(f"{BASE_URL}/api/company/auth/login", json=COMPANY_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Company auth failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def headers(self, company_token):
        return {"Authorization": f"Bearer {company_token}"}
    
    def test_get_device_analytics(self, headers):
        """Test getting comprehensive device analytics"""
        response = requests.get(f"{BASE_URL}/api/company/devices/{TEST_DEVICE_ID}/analytics", headers=headers)
        assert response.status_code == 200, f"Failed to get device analytics: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "device" in data, "Missing device info"
        assert "ticket_analytics" in data, "Missing ticket analytics"
        assert "financial_summary" in data, "Missing financial summary"
        assert "lifecycle_events" in data, "Missing lifecycle events"
        assert "rmm_data" in data, "Missing RMM data"
        
        print(f"✓ Got device analytics for {data['device'].get('brand')} {data['device'].get('model')}")
        return data
    
    def test_device_analytics_ticket_data(self, headers):
        """Test ticket analytics in device dashboard"""
        response = requests.get(f"{BASE_URL}/api/company/devices/{TEST_DEVICE_ID}/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        ticket_analytics = data.get("ticket_analytics", {})
        
        # Verify ticket analytics structure
        assert "total_tickets" in ticket_analytics
        assert "open_tickets" in ticket_analytics
        assert "resolved_tickets" in ticket_analytics
        assert "avg_tat_hours" in ticket_analytics
        assert "avg_tat_display" in ticket_analytics
        assert "tickets" in ticket_analytics
        
        print(f"✓ Ticket analytics: {ticket_analytics['total_tickets']} total, {ticket_analytics['open_tickets']} open")
    
    def test_device_analytics_financial_summary(self, headers):
        """Test financial summary in device dashboard"""
        response = requests.get(f"{BASE_URL}/api/company/devices/{TEST_DEVICE_ID}/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        financial = data.get("financial_summary", {})
        
        # Verify financial summary structure
        assert "total_spend" in financial
        assert "parts_cost" in financial
        assert "pending_quotations" in financial
        
        print(f"✓ Financial summary: Total spend ₹{financial['total_spend']}, Parts ₹{financial['parts_cost']}")
    
    def test_device_analytics_amc_data(self, headers):
        """Test AMC analytics in device dashboard"""
        response = requests.get(f"{BASE_URL}/api/company/devices/{TEST_DEVICE_ID}/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        amc_analytics = data.get("amc_analytics")
        
        if amc_analytics:
            # Verify AMC analytics structure
            assert "contract_name" in amc_analytics
            assert "amc_type" in amc_analytics
            assert "coverage_start" in amc_analytics
            assert "coverage_end" in amc_analytics
            assert "days_remaining" in amc_analytics
            assert "pm_compliance" in amc_analytics
            assert "pm_visits_completed" in amc_analytics
            assert "pm_visits_expected" in amc_analytics
            
            print(f"✓ AMC active: {amc_analytics['contract_name']}, {amc_analytics['days_remaining']} days remaining")
            print(f"  PM Compliance: {amc_analytics['pm_compliance']}% ({amc_analytics['pm_visits_completed']}/{amc_analytics['pm_visits_expected']} visits)")
        else:
            print("✓ No AMC enrolled for this device")
    
    def test_device_analytics_lifecycle_events(self, headers):
        """Test lifecycle events in device dashboard"""
        response = requests.get(f"{BASE_URL}/api/company/devices/{TEST_DEVICE_ID}/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        lifecycle = data.get("lifecycle_events", [])
        
        # Verify lifecycle events structure
        assert isinstance(lifecycle, list)
        
        if lifecycle:
            event = lifecycle[0]
            assert "type" in event
            assert "title" in event
            assert "date" in event
            
            event_types = [e.get("type") for e in lifecycle]
            print(f"✓ Lifecycle events: {len(lifecycle)} events")
            print(f"  Event types: {set(event_types)}")
        else:
            print("✓ No lifecycle events recorded")
    
    def test_device_analytics_rmm_placeholder(self, headers):
        """Test RMM placeholder in device dashboard"""
        response = requests.get(f"{BASE_URL}/api/company/devices/{TEST_DEVICE_ID}/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        rmm_data = data.get("rmm_data", {})
        
        # Verify RMM placeholder structure
        assert "integrated" in rmm_data
        assert rmm_data["integrated"] == False  # Should be placeholder
        assert "message" in rmm_data
        
        print(f"✓ RMM placeholder: integrated={rmm_data['integrated']}")
    
    def test_device_analytics_parts_replaced(self, headers):
        """Test parts replaced data in device dashboard"""
        response = requests.get(f"{BASE_URL}/api/company/devices/{TEST_DEVICE_ID}/analytics", headers=headers)
        assert response.status_code == 200
        data = response.json()
        
        parts = data.get("parts_replaced", [])
        
        assert isinstance(parts, list)
        print(f"✓ Parts replaced: {len(parts)} parts")
    
    def test_nonexistent_device_analytics(self, headers):
        """Test getting analytics for non-existent device returns 404"""
        fake_id = str(uuid.uuid4())
        response = requests.get(f"{BASE_URL}/api/company/devices/{fake_id}/analytics", headers=headers)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print("✓ Non-existent device returns 404")


class TestCompanyDevices:
    """Test Company Devices API"""
    
    @pytest.fixture(scope="class")
    def company_token(self):
        """Get company user auth token"""
        response = requests.post(f"{BASE_URL}/api/company/auth/login", json=COMPANY_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Company auth failed: {response.status_code}")
    
    @pytest.fixture(scope="class")
    def headers(self, company_token):
        return {"Authorization": f"Bearer {company_token}"}
    
    def test_list_company_devices(self, headers):
        """Test listing company devices"""
        response = requests.get(f"{BASE_URL}/api/company/devices", headers=headers)
        assert response.status_code == 200, f"Failed to list devices: {response.text}"
        data = response.json()
        
        assert "devices" in data or isinstance(data, list)
        devices = data.get("devices", data) if isinstance(data, dict) else data
        print(f"✓ Listed {len(devices)} company devices")
    
    def test_get_device_detail(self, headers):
        """Test getting device detail"""
        response = requests.get(f"{BASE_URL}/api/company/devices/{TEST_DEVICE_ID}", headers=headers)
        assert response.status_code == 200, f"Failed to get device: {response.text}"
        data = response.json()
        
        # API returns {"device": {...}, "parts": [...]}
        device = data.get("device", data)  # Handle both formats
        
        assert device["id"] == TEST_DEVICE_ID
        assert "serial_number" in device
        assert "brand" in device
        assert "model" in device
        print(f"✓ Got device: {device.get('brand')} {device.get('model')} ({device.get('serial_number')})")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json=ADMIN_USER)
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip(f"Admin auth failed: {response.status_code}")
    
    def test_cleanup_test_tickets(self, admin_token):
        """Cleanup TEST_ prefixed tickets"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get all tickets
        response = requests.get(f"{BASE_URL}/api/admin/service-tickets?limit=100", headers=headers)
        if response.status_code == 200:
            data = response.json()
            tickets = data.get("tickets", [])
            
            test_tickets = [t for t in tickets if t.get("title", "").startswith("TEST_")]
            print(f"Found {len(test_tickets)} test tickets to cleanup")
            
            # Note: Actual deletion would require delete endpoint
            # For now, just report
        print("✓ Cleanup check complete")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
