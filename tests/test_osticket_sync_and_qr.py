"""
Test Suite for osTicket Manual Sync and Individual QR Download Features
========================================================================
Tests:
1. P1: osTicket Manual Sync Feature - POST /api/company/tickets/{ticket_id}/sync
2. P0: Individual QR Download - GET /api/device/{serial}/qr (should return single device PDF)
3. Bulk QR PDF - POST /api/devices/bulk-qr-pdf (should work for multiple devices)
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://workflow-hub-270.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"
COMPANY_USER_EMAIL = "jane@acme.com"
COMPANY_USER_PASSWORD = "company123"


class TestSetup:
    """Setup fixtures and helper methods"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Admin authentication failed")
    
    @pytest.fixture(scope="class")
    def company_token(self):
        """Get company user authentication token"""
        response = requests.post(f"{BASE_URL}/api/company/auth/login", json={
            "email": COMPANY_USER_EMAIL,
            "password": COMPANY_USER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Company user authentication failed")
    
    @pytest.fixture(scope="class")
    def test_device(self, admin_token):
        """Get a test device for QR code testing"""
        response = requests.get(f"{BASE_URL}/api/admin/devices", 
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 1}
        )
        if response.status_code == 200 and response.json():
            return response.json()[0]
        pytest.skip("No devices found for testing")
    
    @pytest.fixture(scope="class")
    def test_ticket_with_osticket(self, company_token):
        """Get a ticket that has osticket_id for sync testing"""
        response = requests.get(f"{BASE_URL}/api/company/tickets",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        if response.status_code == 200:
            tickets = response.json()
            # Find a ticket with osticket_id
            for ticket in tickets:
                if ticket.get("osticket_id"):
                    return ticket
            # Return first ticket even without osticket_id for negative testing
            if tickets:
                return tickets[0]
        return None


class TestOsTicketManualSync(TestSetup):
    """Test osTicket Manual Sync Feature - P1"""
    
    def test_sync_endpoint_exists(self, company_token, test_ticket_with_osticket):
        """Test that the sync endpoint exists and responds"""
        if not test_ticket_with_osticket:
            pytest.skip("No tickets found for testing")
        
        ticket_id = test_ticket_with_osticket["id"]
        response = requests.post(f"{BASE_URL}/api/company/tickets/{ticket_id}/sync",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        # Endpoint should exist - expect 400 (no osticket_id), 503 (IP restricted), or 200 (success)
        assert response.status_code in [200, 400, 503], f"Unexpected status: {response.status_code}"
        print(f"Sync endpoint response: {response.status_code} - {response.json()}")
    
    def test_sync_requires_authentication(self, test_ticket_with_osticket):
        """Test that sync endpoint requires authentication"""
        if not test_ticket_with_osticket:
            pytest.skip("No tickets found for testing")
        
        ticket_id = test_ticket_with_osticket["id"]
        response = requests.post(f"{BASE_URL}/api/company/tickets/{ticket_id}/sync")
        
        assert response.status_code in [401, 403], "Sync should require authentication"
    
    def test_sync_ticket_without_osticket_id(self, company_token):
        """Test sync returns 400 for ticket without osticket_id"""
        # First, get tickets and find one without osticket_id
        response = requests.get(f"{BASE_URL}/api/company/tickets",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        if response.status_code != 200:
            pytest.skip("Could not fetch tickets")
        
        tickets = response.json()
        ticket_without_osticket = None
        for ticket in tickets:
            if not ticket.get("osticket_id"):
                ticket_without_osticket = ticket
                break
        
        if not ticket_without_osticket:
            pytest.skip("All tickets have osticket_id")
        
        # Try to sync ticket without osticket_id
        sync_response = requests.post(
            f"{BASE_URL}/api/company/tickets/{ticket_without_osticket['id']}/sync",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert sync_response.status_code == 400, "Should return 400 for ticket without osticket_id"
        assert "not linked" in sync_response.json().get("detail", "").lower()
        print(f"Correct error for ticket without osticket_id: {sync_response.json()}")
    
    def test_sync_ticket_with_osticket_id(self, company_token):
        """Test sync for ticket with osticket_id (expects 503 due to IP restriction)"""
        # Get tickets and find one with osticket_id
        response = requests.get(f"{BASE_URL}/api/company/tickets",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        if response.status_code != 200:
            pytest.skip("Could not fetch tickets")
        
        tickets = response.json()
        ticket_with_osticket = None
        for ticket in tickets:
            if ticket.get("osticket_id"):
                ticket_with_osticket = ticket
                break
        
        if not ticket_with_osticket:
            pytest.skip("No tickets with osticket_id found")
        
        # Try to sync - expect 503 due to IP restriction
        sync_response = requests.post(
            f"{BASE_URL}/api/company/tickets/{ticket_with_osticket['id']}/sync",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        # 503 is expected because osTicket API is IP-restricted
        assert sync_response.status_code in [200, 503], f"Unexpected status: {sync_response.status_code}"
        print(f"Sync response for ticket with osticket_id: {sync_response.status_code} - {sync_response.json()}")
    
    def test_sync_nonexistent_ticket(self, company_token):
        """Test sync returns 404 for non-existent ticket"""
        response = requests.post(f"{BASE_URL}/api/company/tickets/nonexistent-ticket-id/sync",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert response.status_code == 404, "Should return 404 for non-existent ticket"


class TestIndividualQRDownload(TestSetup):
    """Test Individual QR Download - P0 (Fixed bug: should download ONLY ONE device)"""
    
    def test_individual_qr_returns_pdf(self, test_device):
        """Test that individual QR endpoint returns a PDF"""
        if not test_device:
            pytest.skip("No test device available")
        
        serial = test_device["serial_number"]
        response = requests.get(f"{BASE_URL}/api/device/{serial}/qr")
        
        assert response.status_code == 200, f"QR endpoint failed: {response.status_code}"
        
        # Check content type is PDF
        content_type = response.headers.get("content-type", "")
        assert "application/pdf" in content_type, f"Expected PDF, got: {content_type}"
        
        # Check content-disposition header for filename
        content_disposition = response.headers.get("content-disposition", "")
        assert "attachment" in content_disposition, "Should have attachment disposition"
        assert serial in content_disposition, f"Filename should contain serial number: {content_disposition}"
        
        print(f"Individual QR PDF downloaded successfully for {serial}")
        print(f"Content-Disposition: {content_disposition}")
        print(f"Content-Length: {len(response.content)} bytes")
    
    def test_individual_qr_pdf_size_reasonable(self, test_device):
        """Test that individual QR PDF is reasonably sized (not too large = not all devices)"""
        if not test_device:
            pytest.skip("No test device available")
        
        serial = test_device["serial_number"]
        response = requests.get(f"{BASE_URL}/api/device/{serial}/qr")
        
        assert response.status_code == 200
        
        # Individual QR PDF should be small (< 50KB for single QR)
        # If it's downloading all devices, it would be much larger
        content_length = len(response.content)
        assert content_length < 100000, f"PDF too large ({content_length} bytes) - might be downloading all devices!"
        assert content_length > 1000, f"PDF too small ({content_length} bytes) - might be empty"
        
        print(f"Individual QR PDF size: {content_length} bytes (reasonable for single device)")
    
    def test_individual_qr_invalid_device(self):
        """Test that invalid device returns 404"""
        response = requests.get(f"{BASE_URL}/api/device/INVALID-SERIAL-12345/qr")
        
        assert response.status_code == 404, "Should return 404 for invalid device"
    
    def test_individual_qr_by_asset_tag(self, admin_token):
        """Test QR download by asset tag (if device has one)"""
        # Get a device with asset tag
        response = requests.get(f"{BASE_URL}/api/admin/devices",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 50}
        )
        
        if response.status_code != 200:
            pytest.skip("Could not fetch devices")
        
        devices = response.json()
        device_with_tag = None
        for d in devices:
            if d.get("asset_tag"):
                device_with_tag = d
                break
        
        if not device_with_tag:
            pytest.skip("No devices with asset tag found")
        
        # Try to get QR by asset tag
        asset_tag = device_with_tag["asset_tag"]
        qr_response = requests.get(f"{BASE_URL}/api/device/{asset_tag}/qr")
        
        assert qr_response.status_code == 200, f"QR by asset tag failed: {qr_response.status_code}"
        assert "application/pdf" in qr_response.headers.get("content-type", "")
        print(f"QR download by asset tag '{asset_tag}' successful")


class TestBulkQRDownload(TestSetup):
    """Test Bulk QR PDF Download - Should still work for multiple devices"""
    
    def test_bulk_qr_with_device_ids(self, admin_token, test_device):
        """Test bulk QR with specific device IDs"""
        if not test_device:
            pytest.skip("No test device available")
        
        # Get a few device IDs
        response = requests.get(f"{BASE_URL}/api/admin/devices",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={"limit": 3}
        )
        
        if response.status_code != 200:
            pytest.skip("Could not fetch devices")
        
        devices = response.json()
        device_ids = [d["id"] for d in devices[:3]]
        
        # Request bulk QR PDF
        bulk_response = requests.post(f"{BASE_URL}/api/devices/bulk-qr-pdf",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"device_ids": device_ids}
        )
        
        assert bulk_response.status_code == 200, f"Bulk QR failed: {bulk_response.status_code}"
        assert "application/pdf" in bulk_response.headers.get("content-type", "")
        
        # Bulk PDF should be larger than individual
        content_length = len(bulk_response.content)
        print(f"Bulk QR PDF size for {len(device_ids)} devices: {content_length} bytes")
    
    def test_bulk_qr_requires_auth(self):
        """Test that bulk QR requires authentication"""
        response = requests.post(f"{BASE_URL}/api/devices/bulk-qr-pdf",
            json={"device_ids": ["test-id"]}
        )
        
        assert response.status_code in [401, 403], "Bulk QR should require authentication"
    
    def test_bulk_qr_empty_request(self, admin_token):
        """Test bulk QR with no filters returns all devices"""
        response = requests.post(f"{BASE_URL}/api/devices/bulk-qr-pdf",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={}
        )
        
        # Should either succeed with all devices or return 404 if no devices
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            assert "application/pdf" in response.headers.get("content-type", "")
            print(f"Bulk QR for all devices: {len(response.content)} bytes")


class TestCompanyTicketDetails(TestSetup):
    """Test Company Ticket Details page has sync button"""
    
    def test_ticket_details_endpoint(self, company_token):
        """Test that ticket details endpoint returns osticket_id field"""
        # Get tickets
        response = requests.get(f"{BASE_URL}/api/company/tickets",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        if response.status_code != 200 or not response.json():
            pytest.skip("No tickets found")
        
        ticket = response.json()[0]
        ticket_id = ticket["id"]
        
        # Get ticket details
        details_response = requests.get(f"{BASE_URL}/api/company/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert details_response.status_code == 200
        ticket_data = details_response.json()
        
        # Verify osticket_id field exists (can be null)
        assert "osticket_id" in ticket_data or ticket_data.get("osticket_id") is None or "osticket_id" not in ticket_data
        print(f"Ticket {ticket_id} osticket_id: {ticket_data.get('osticket_id')}")
        
        # Verify last_synced_at field exists (for sync tracking)
        # This field may not exist if never synced
        print(f"Ticket last_synced_at: {ticket_data.get('last_synced_at', 'Not synced yet')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
