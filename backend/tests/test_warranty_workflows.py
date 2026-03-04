"""
Test Suite: Warranty Workflows and Device Warranty Detection
Tests for:
1. GET /api/ticketing/workflows - returns 3 new workflows (oem-warranty, amc-support, non-warranty)
2. OEM Warranty workflow stages
3. AMC workflow stages  
4. Non-Warranty workflow stages
5. GET /api/ticketing/device-warranty-check/{device_id} - warranty type detection
6. POST /api/ticketing/tickets - creates ticket with device_warranty_type auto-detected
7. PUT /api/ticketing/tickets/{id} - OEM tracking fields
8. GET /api/ticketing/help-topics - returns 3 new help topics
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
TEST_EMAIL = "ck@motta.in"
TEST_PASSWORD = "Charu@123@"


class TestWarrantyWorkflows:
    """Test warranty-based workflows"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_workflows_endpoint_returns_3_new_workflows(self):
        """Test GET /api/ticketing/workflows returns the 3 new workflows"""
        response = requests.get(f"{BASE_URL}/api/ticketing/workflows", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        workflows = response.json()
        assert isinstance(workflows, list), "Response should be a list"
        
        # Check for the 3 warranty workflows by slug
        slugs = [w.get('slug') for w in workflows]
        assert 'oem-warranty' in slugs, "oem-warranty workflow not found"
        assert 'amc-support' in slugs, "amc-support workflow not found"
        assert 'non-warranty' in slugs, "non-warranty workflow not found"
        
        print(f"PASS: Found {len(workflows)} workflows including oem-warranty, amc-support, non-warranty")
    
    def test_oem_warranty_workflow_stages(self):
        """Test OEM Warranty workflow has correct stages"""
        response = requests.get(f"{BASE_URL}/api/ticketing/workflows", headers=self.headers)
        assert response.status_code == 200
        
        workflows = response.json()
        oem_workflow = next((w for w in workflows if w.get('slug') == 'oem-warranty'), None)
        assert oem_workflow, "OEM Warranty workflow not found"
        
        stages = oem_workflow.get('stages', [])
        stage_names = [s.get('name') for s in stages]
        
        # Expected stages for OEM Warranty workflow
        expected_stages = [
            "New", "Verified Warranty", "Escalated to OEM", "OEM Case Logged",
            "OEM Engineer Dispatched", "OEM Resolution", "Closed", "Cancelled"
        ]
        
        for stage in expected_stages:
            assert stage in stage_names, f"Stage '{stage}' not found in OEM Warranty workflow"
        
        print(f"PASS: OEM Warranty workflow has {len(stages)} stages: {stage_names}")
    
    def test_amc_workflow_stages(self):
        """Test AMC workflow has correct stages"""
        response = requests.get(f"{BASE_URL}/api/ticketing/workflows", headers=self.headers)
        assert response.status_code == 200
        
        workflows = response.json()
        amc_workflow = next((w for w in workflows if w.get('slug') == 'amc-support'), None)
        assert amc_workflow, "AMC Support workflow not found"
        
        stages = amc_workflow.get('stages', [])
        stage_names = [s.get('name') for s in stages]
        
        # Expected stages for AMC workflow
        expected_stages = [
            "New", "Assigned", "Scheduled", "In Progress", "Diagnosed",
            "Awaiting Parts", "Parts Received", "Fixed On-Site", "Resolved", "Cancelled"
        ]
        
        for stage in expected_stages:
            assert stage in stage_names, f"Stage '{stage}' not found in AMC workflow"
        
        print(f"PASS: AMC Support workflow has {len(stages)} stages: {stage_names}")
    
    def test_non_warranty_workflow_stages(self):
        """Test Non-Warranty workflow has correct stages"""
        response = requests.get(f"{BASE_URL}/api/ticketing/workflows", headers=self.headers)
        assert response.status_code == 200
        
        workflows = response.json()
        nw_workflow = next((w for w in workflows if w.get('slug') == 'non-warranty'), None)
        assert nw_workflow, "Non-Warranty workflow not found"
        
        stages = nw_workflow.get('stages', [])
        stage_names = [s.get('name') for s in stages]
        
        # Expected stages for Non-Warranty workflow
        expected_stages = [
            "New", "Assigned", "Diagnosed", "Quotation Sent", "Customer Approved",
            "Customer Rejected", "Parts Ordered", "In Progress", "Fixed On-Site",
            "Billing Pending", "Resolved", "Cancelled"
        ]
        
        for stage in expected_stages:
            assert stage in stage_names, f"Stage '{stage}' not found in Non-Warranty workflow"
        
        print(f"PASS: Non-Warranty workflow has {len(stages)} stages: {stage_names}")


class TestHelpTopics:
    """Test help topics for warranty workflows"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_help_topics_returns_warranty_topics(self):
        """Test GET /api/ticketing/help-topics returns the 3 warranty help topics"""
        response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=self.headers)
        assert response.status_code == 200
        
        topics = response.json()
        assert isinstance(topics, list)
        
        # Look for the 3 warranty-related help topics
        topic_names = [t.get('name', '').lower() for t in topics]
        
        found_warranty_claim = any('warranty' in n and 'oem' in n for n in topic_names)
        found_amc = any('amc' in n for n in topic_names)
        found_non_warranty = any('non-warranty' in n or ('non' in n and 'warranty' in n) for n in topic_names)
        
        assert found_warranty_claim, "Warranty Claim (OEM) help topic not found"
        assert found_amc, "AMC Support help topic not found"
        assert found_non_warranty, "Non-Warranty Repair help topic not found"
        
        print(f"PASS: Found {len(topics)} help topics including warranty-related ones")


class TestDeviceWarrantyCheck:
    """Test device warranty detection endpoint"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
    
    def test_device_warranty_check_endpoint_exists(self):
        """Test GET /api/ticketing/device-warranty-check/{device_id} endpoint"""
        # First, get a device from the company
        devices_response = requests.get(f"{BASE_URL}/api/admin/devices?limit=5", headers=self.headers)
        
        if devices_response.status_code == 200:
            devices_data = devices_response.json()
            devices = devices_data if isinstance(devices_data, list) else devices_data.get('devices', [])
            
            if devices and len(devices) > 0:
                device_id = devices[0].get('id')
                
                # Test the warranty check endpoint
                response = requests.get(f"{BASE_URL}/api/ticketing/device-warranty-check/{device_id}", headers=self.headers)
                assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
                
                data = response.json()
                # Verify response structure
                assert 'device_id' in data, "Response missing device_id"
                assert 'warranty_type' in data, "Response missing warranty_type"
                assert data['warranty_type'] in ['oem_warranty', 'amc', 'non_warranty'], f"Invalid warranty_type: {data['warranty_type']}"
                
                # Check for suggested workflow/topic
                assert 'suggested_workflow_id' in data or 'suggested_workflow_name' in data, "Response missing suggested_workflow"
                assert 'suggested_help_topic_id' in data or 'suggested_help_topic_name' in data, "Response missing suggested_help_topic"
                
                print(f"PASS: Device warranty check returned: {data.get('warranty_type')} -> {data.get('suggested_help_topic_name')}")
                return
        
        # If no devices, check that endpoint returns 404 for invalid device
        response = requests.get(f"{BASE_URL}/api/ticketing/device-warranty-check/invalid-device-id", headers=self.headers)
        assert response.status_code == 404, f"Expected 404 for invalid device, got {response.status_code}"
        print("PASS: Device warranty check endpoint exists and returns 404 for invalid device")
    
    def test_device_warranty_check_response_structure(self):
        """Test device warranty check returns expected fields"""
        # Get any device
        devices_response = requests.get(f"{BASE_URL}/api/admin/devices?limit=1", headers=self.headers)
        if devices_response.status_code != 200:
            pytest.skip("No devices available for testing")
        
        devices_data = devices_response.json()
        devices = devices_data if isinstance(devices_data, list) else devices_data.get('devices', [])
        
        if not devices:
            pytest.skip("No devices available for testing")
        
        device_id = devices[0].get('id')
        response = requests.get(f"{BASE_URL}/api/ticketing/device-warranty-check/{device_id}", headers=self.headers)
        assert response.status_code == 200
        
        data = response.json()
        
        # Expected fields
        expected_fields = ['device_id', 'warranty_type', 'warranty_type_label', 'managed_by', 'details']
        for field in expected_fields:
            assert field in data, f"Response missing field: {field}"
        
        print(f"PASS: Warranty check response has all expected fields: {list(data.keys())}")


class TestTicketCreationWithWarranty:
    """Test ticket creation with auto-detected warranty type"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token and test data before tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        # Get a help topic
        topics_response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=self.headers)
        if topics_response.status_code == 200:
            topics = topics_response.json()
            if topics:
                self.help_topic_id = topics[0].get('id')
        
        # Get a device
        devices_response = requests.get(f"{BASE_URL}/api/admin/devices?limit=1", headers=self.headers)
        if devices_response.status_code == 200:
            devices_data = devices_response.json()
            devices = devices_data if isinstance(devices_data, list) else devices_data.get('devices', [])
            if devices:
                self.device_id = devices[0].get('id')
    
    def test_ticket_creation_auto_detects_warranty(self):
        """Test POST /api/ticketing/tickets creates ticket with device_warranty_type auto-detected"""
        if not hasattr(self, 'help_topic_id'):
            pytest.skip("No help topic available")
        if not hasattr(self, 'device_id'):
            pytest.skip("No device available")
        
        # Create ticket with device
        payload = {
            "help_topic_id": self.help_topic_id,
            "subject": f"TEST_Warranty_Detection_Ticket_{int(time.time())}",
            "description": "Test ticket for warranty detection",
            "device_id": self.device_id
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/tickets", headers=self.headers, json=payload)
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        
        ticket = response.json()
        
        # Verify ticket has warranty type
        assert 'device_warranty_type' in ticket, "Ticket missing device_warranty_type field"
        assert ticket['device_warranty_type'] in ['oem_warranty', 'amc', 'non_warranty', None], \
            f"Invalid device_warranty_type: {ticket['device_warranty_type']}"
        
        print(f"PASS: Ticket #{ticket.get('ticket_number')} created with warranty type: {ticket.get('device_warranty_type')}")
        
        # Store ticket_id for cleanup or later tests
        self.test_ticket_id = ticket.get('id')


class TestOEMTrackingFields:
    """Test OEM tracking fields on tickets"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Get auth token before tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        })
        assert response.status_code == 200
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}
        
        # Get any ticket for testing
        tickets_response = requests.get(f"{BASE_URL}/api/ticketing/tickets?limit=1", headers=self.headers)
        if tickets_response.status_code == 200:
            data = tickets_response.json()
            tickets = data.get('tickets', [])
            if tickets:
                self.ticket_id = tickets[0].get('id')
    
    def test_ticket_update_accepts_oem_tracking_fields(self):
        """Test PUT /api/ticketing/tickets/{id} accepts OEM tracking fields"""
        if not hasattr(self, 'ticket_id'):
            pytest.skip("No ticket available for testing")
        
        # Update with OEM tracking fields
        oem_data = {
            "oem_case_number": "TEST_CASE_12345",
            "oem_engineer_name": "Test OEM Engineer",
            "oem_engineer_phone": "919876543210",
            "oem_brand_reference": "BRAND_REF_ABC",
            "oem_status": "Case Logged",
            "oem_notes": "Test OEM notes for tracking"
        }
        
        response = requests.put(f"{BASE_URL}/api/ticketing/tickets/{self.ticket_id}", headers=self.headers, json=oem_data)
        assert response.status_code == 200, f"Failed to update ticket: {response.text}"
        
        ticket = response.json()
        
        # Verify OEM fields were saved (they should be in the response)
        # Note: The response may not include all fields, so verify by getting the ticket
        get_response = requests.get(f"{BASE_URL}/api/ticketing/tickets/{self.ticket_id}", headers=self.headers)
        assert get_response.status_code == 200
        
        full_ticket = get_response.json()
        
        assert full_ticket.get('oem_case_number') == oem_data['oem_case_number'], \
            f"oem_case_number not saved. Got: {full_ticket.get('oem_case_number')}"
        assert full_ticket.get('oem_engineer_name') == oem_data['oem_engineer_name'], \
            f"oem_engineer_name not saved"
        assert full_ticket.get('oem_status') == oem_data['oem_status'], \
            f"oem_status not saved"
        
        print(f"PASS: OEM tracking fields saved successfully")
        print(f"  - Case #: {full_ticket.get('oem_case_number')}")
        print(f"  - Engineer: {full_ticket.get('oem_engineer_name')}")
        print(f"  - Status: {full_ticket.get('oem_status')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
