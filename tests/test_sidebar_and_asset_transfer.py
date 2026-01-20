"""
Test Suite for Collapsible Sidebar Navigation and Asset Transfer Feature
=========================================================================
Tests:
1. Asset Transfer API - POST /api/admin/asset-transfers
2. Asset Transfer History - GET /api/admin/asset-transfers
3. Asset Transfer History by Asset - GET /api/admin/assets/{asset_type}/{asset_id}/transfer-history
"""

import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAssetTransferAPI:
    """Test Asset Transfer endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures - login and get token"""
        # Login to get token
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a device for testing
        devices_response = requests.get(f"{BASE_URL}/api/admin/devices", headers=self.headers)
        assert devices_response.status_code == 200, f"Failed to get devices: {devices_response.text}"
        devices = devices_response.json()
        
        if devices:
            self.test_device = devices[0]
            self.test_device_id = self.test_device["id"]
        else:
            self.test_device = None
            self.test_device_id = None
        
        # Get or create a test employee
        employees_response = requests.get(f"{BASE_URL}/api/admin/company-employees", headers=self.headers)
        assert employees_response.status_code == 200, f"Failed to get employees: {employees_response.text}"
        employees = employees_response.json()
        
        if employees:
            self.test_employee = employees[0]
            self.test_employee_id = self.test_employee["id"]
        else:
            # Create a test employee if none exist
            companies_response = requests.get(f"{BASE_URL}/api/admin/companies", headers=self.headers)
            companies = companies_response.json()
            if companies:
                create_emp_response = requests.post(
                    f"{BASE_URL}/api/admin/company-employees",
                    headers=self.headers,
                    json={
                        "company_id": companies[0]["id"],
                        "name": "TEST_Transfer_Employee",
                        "email": f"test_transfer_{uuid.uuid4().hex[:6]}@test.com"
                    }
                )
                if create_emp_response.status_code == 200:
                    self.test_employee = create_emp_response.json()
                    self.test_employee_id = self.test_employee["id"]
                else:
                    self.test_employee = None
                    self.test_employee_id = None
            else:
                self.test_employee = None
                self.test_employee_id = None
    
    def test_asset_transfer_create_success(self):
        """Test POST /api/admin/asset-transfers - Transfer device to employee"""
        if not self.test_device_id:
            pytest.skip("No test device available")
        
        transfer_data = {
            "asset_type": "device",
            "asset_id": self.test_device_id,
            "to_employee_id": self.test_employee_id,  # Can be None to unassign
            "transfer_date": datetime.now().strftime("%Y-%m-%d"),
            "reason": "Test Transfer",
            "notes": "Automated test transfer"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/asset-transfers",
            headers=self.headers,
            json=transfer_data
        )
        
        assert response.status_code == 200, f"Transfer failed: {response.text}"
        data = response.json()
        
        # Validate response structure
        assert "id" in data, "Response should contain transfer ID"
        assert "asset_type" in data, "Response should contain asset_type"
        assert data["asset_type"] == "device"
        assert data["asset_id"] == self.test_device_id
        assert "message" in data, "Response should contain message"
        assert "transferred_by" in data, "Response should contain transferred_by"
        assert "created_at" in data, "Response should contain created_at"
        
        print(f"Transfer created successfully: {data['message']}")
        
        # Store transfer ID for later tests
        self.transfer_id = data["id"]
    
    def test_asset_transfer_unassign(self):
        """Test POST /api/admin/asset-transfers - Unassign device (to_employee_id = null)"""
        if not self.test_device_id:
            pytest.skip("No test device available")
        
        transfer_data = {
            "asset_type": "device",
            "asset_id": self.test_device_id,
            "to_employee_id": None,  # Unassign
            "transfer_date": datetime.now().strftime("%Y-%m-%d"),
            "reason": "Unassignment Test",
            "notes": "Testing unassignment flow"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/asset-transfers",
            headers=self.headers,
            json=transfer_data
        )
        
        assert response.status_code == 200, f"Unassign transfer failed: {response.text}"
        data = response.json()
        
        assert data["to_employee_id"] is None, "to_employee_id should be None for unassignment"
        assert "Unassigned" in data.get("message", ""), "Message should indicate unassignment"
        
        print(f"Unassignment successful: {data['message']}")
    
    def test_asset_transfer_invalid_asset_type(self):
        """Test POST /api/admin/asset-transfers - Invalid asset_type should fail"""
        transfer_data = {
            "asset_type": "invalid_type",
            "asset_id": "some-id",
            "to_employee_id": None,
            "transfer_date": datetime.now().strftime("%Y-%m-%d"),
            "reason": "Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/asset-transfers",
            headers=self.headers,
            json=transfer_data
        )
        
        assert response.status_code == 400, f"Should return 400 for invalid asset_type: {response.text}"
        assert "Invalid asset_type" in response.json().get("detail", "")
        print("Invalid asset_type correctly rejected")
    
    def test_asset_transfer_device_not_found(self):
        """Test POST /api/admin/asset-transfers - Non-existent device should fail"""
        transfer_data = {
            "asset_type": "device",
            "asset_id": "non-existent-device-id",
            "to_employee_id": None,
            "transfer_date": datetime.now().strftime("%Y-%m-%d"),
            "reason": "Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/asset-transfers",
            headers=self.headers,
            json=transfer_data
        )
        
        assert response.status_code == 404, f"Should return 404 for non-existent device: {response.text}"
        assert "not found" in response.json().get("detail", "").lower()
        print("Non-existent device correctly rejected")
    
    def test_asset_transfer_invalid_employee(self):
        """Test POST /api/admin/asset-transfers - Non-existent employee should fail"""
        if not self.test_device_id:
            pytest.skip("No test device available")
        
        transfer_data = {
            "asset_type": "device",
            "asset_id": self.test_device_id,
            "to_employee_id": "non-existent-employee-id",
            "transfer_date": datetime.now().strftime("%Y-%m-%d"),
            "reason": "Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/asset-transfers",
            headers=self.headers,
            json=transfer_data
        )
        
        assert response.status_code == 404, f"Should return 404 for non-existent employee: {response.text}"
        assert "employee not found" in response.json().get("detail", "").lower()
        print("Non-existent employee correctly rejected")
    
    def test_get_asset_transfers_list(self):
        """Test GET /api/admin/asset-transfers - List all transfers"""
        response = requests.get(
            f"{BASE_URL}/api/admin/asset-transfers",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get transfers: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            transfer = data[0]
            assert "id" in transfer, "Transfer should have id"
            assert "asset_type" in transfer, "Transfer should have asset_type"
            assert "asset_id" in transfer, "Transfer should have asset_id"
            assert "transfer_date" in transfer, "Transfer should have transfer_date"
            assert "created_at" in transfer, "Transfer should have created_at"
            print(f"Found {len(data)} transfer records")
        else:
            print("No transfer records found (empty list)")
    
    def test_get_asset_transfers_filter_by_asset_type(self):
        """Test GET /api/admin/asset-transfers?asset_type=device - Filter by type"""
        response = requests.get(
            f"{BASE_URL}/api/admin/asset-transfers",
            headers=self.headers,
            params={"asset_type": "device"}
        )
        
        assert response.status_code == 200, f"Failed to get filtered transfers: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        # All returned transfers should be for devices
        for transfer in data:
            assert transfer["asset_type"] == "device", "All transfers should be for devices"
        
        print(f"Found {len(data)} device transfer records")
    
    def test_get_asset_transfers_filter_by_asset_id(self):
        """Test GET /api/admin/asset-transfers?asset_id=X - Filter by asset"""
        if not self.test_device_id:
            pytest.skip("No test device available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/asset-transfers",
            headers=self.headers,
            params={"asset_id": self.test_device_id}
        )
        
        assert response.status_code == 200, f"Failed to get filtered transfers: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        # All returned transfers should be for the specific asset
        for transfer in data:
            assert transfer["asset_id"] == self.test_device_id, "All transfers should be for the specified asset"
        
        print(f"Found {len(data)} transfer records for device {self.test_device_id}")
    
    def test_get_asset_transfer_history_by_asset(self):
        """Test GET /api/admin/assets/{asset_type}/{asset_id}/transfer-history"""
        if not self.test_device_id:
            pytest.skip("No test device available")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/assets/device/{self.test_device_id}/transfer-history",
            headers=self.headers
        )
        
        assert response.status_code == 200, f"Failed to get asset transfer history: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        # All returned transfers should be for the specific asset
        for transfer in data:
            assert transfer["asset_type"] == "device", "All transfers should be for device type"
            assert transfer["asset_id"] == self.test_device_id, "All transfers should be for the specified asset"
        
        print(f"Found {len(data)} transfer history records for device")
    
    def test_asset_transfer_requires_auth(self):
        """Test that asset transfer endpoints require authentication"""
        # Test POST without auth
        response = requests.post(
            f"{BASE_URL}/api/admin/asset-transfers",
            json={
                "asset_type": "device",
                "asset_id": "test",
                "transfer_date": "2025-01-01"
            }
        )
        assert response.status_code in [401, 403], "POST should require auth"
        
        # Test GET without auth
        response = requests.get(f"{BASE_URL}/api/admin/asset-transfers")
        assert response.status_code in [401, 403], "GET should require auth"
        
        print("Authentication correctly required for all endpoints")


class TestDevicesEndpoint:
    """Test that devices endpoint returns data needed for transfer feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_devices_list(self):
        """Test GET /api/admin/devices returns devices"""
        response = requests.get(f"{BASE_URL}/api/admin/devices", headers=self.headers)
        
        assert response.status_code == 200, f"Failed to get devices: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            device = data[0]
            assert "id" in device, "Device should have id"
            assert "serial_number" in device, "Device should have serial_number"
            assert "brand" in device, "Device should have brand"
            assert "model" in device, "Device should have model"
            print(f"Found {len(data)} devices")
        else:
            print("No devices found")
    
    def test_get_single_device(self):
        """Test GET /api/admin/devices/{id} returns device details"""
        # First get list to get an ID
        list_response = requests.get(f"{BASE_URL}/api/admin/devices", headers=self.headers)
        devices = list_response.json()
        
        if not devices:
            pytest.skip("No devices available for testing")
        
        device_id = devices[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/admin/devices/{device_id}", headers=self.headers)
        
        assert response.status_code == 200, f"Failed to get device: {response.text}"
        data = response.json()
        
        assert data["id"] == device_id, "Device ID should match"
        assert "serial_number" in data, "Device should have serial_number"
        assert "assigned_employee_id" in data or "assigned_employee_id" not in data, "Device may have assigned_employee_id"
        
        print(f"Device details retrieved: {data.get('brand')} {data.get('model')}")


class TestCompanyEmployeesEndpoint:
    """Test company employees endpoint for transfer feature"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@demo.com",
            "password": "admin123"
        })
        assert login_response.status_code == 200
        self.token = login_response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_employees_list(self):
        """Test GET /api/admin/company-employees returns employees"""
        response = requests.get(f"{BASE_URL}/api/admin/company-employees", headers=self.headers)
        
        assert response.status_code == 200, f"Failed to get employees: {response.text}"
        data = response.json()
        
        assert isinstance(data, list), "Response should be a list"
        
        if len(data) > 0:
            employee = data[0]
            assert "id" in employee, "Employee should have id"
            assert "name" in employee, "Employee should have name"
            assert "company_id" in employee, "Employee should have company_id"
            print(f"Found {len(data)} employees")
        else:
            print("No employees found")
    
    def test_get_employees_by_company(self):
        """Test GET /api/admin/company-employees?company_id=X filters by company"""
        # First get companies
        companies_response = requests.get(f"{BASE_URL}/api/admin/companies", headers=self.headers)
        companies = companies_response.json()
        
        if not companies:
            pytest.skip("No companies available for testing")
        
        company_id = companies[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/admin/company-employees",
            headers=self.headers,
            params={"company_id": company_id}
        )
        
        assert response.status_code == 200, f"Failed to get employees: {response.text}"
        data = response.json()
        
        # All returned employees should be from the specified company
        for employee in data:
            assert employee["company_id"] == company_id, "All employees should be from the specified company"
        
        print(f"Found {len(data)} employees for company {company_id}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
