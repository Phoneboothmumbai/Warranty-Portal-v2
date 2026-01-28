"""
Test Suite for Service History / Technician Panel OEM Service Records
=====================================================================
Tests the following features:
- GET /api/admin/services/options - dropdown options
- POST /api/admin/services - create internal and OEM service records
- GET /api/admin/services - list services with filters
- PUT /api/admin/services/{id} - update service records
- OEM validation rules and auto-locking
- Service closure with outcome
"""
import pytest
import requests
import os
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"


class TestServiceOptions:
    """Test GET /api/admin/services/options - dropdown options endpoint"""
    
    def test_get_service_options_returns_all_dropdowns(self):
        """Service options endpoint returns all required dropdown data"""
        response = requests.get(f"{BASE_URL}/api/admin/services/options")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify all required dropdown keys exist
        assert "service_categories" in data, "Missing service_categories"
        assert "service_responsibilities" in data, "Missing service_responsibilities"
        assert "service_roles" in data, "Missing service_roles"
        assert "oem_names" in data, "Missing oem_names"
        assert "oem_warranty_types" in data, "Missing oem_warranty_types"
        assert "oem_case_raised_via" in data, "Missing oem_case_raised_via"
        assert "oem_priority" in data, "Missing oem_priority"
        assert "oem_case_statuses" in data, "Missing oem_case_statuses"
        assert "billing_impact" in data, "Missing billing_impact"
        assert "service_statuses" in data, "Missing service_statuses"
        
        # Verify service_categories has expected values
        categories = [c["value"] for c in data["service_categories"]]
        assert "internal_service" in categories
        assert "oem_warranty_service" in categories
        assert "paid_third_party_service" in categories
        assert "inspection_diagnosis" in categories
        
        # Verify OEM names list
        assert len(data["oem_names"]) > 0
        assert "Dell" in data["oem_names"]
        assert "HP" in data["oem_names"]
        assert "Lenovo" in data["oem_names"]
        
        print("✓ Service options endpoint returns all dropdown data correctly")


class TestServiceCRUD:
    """Test Service CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and device ID"""
        # Login
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a device for testing
        devices_response = requests.get(f"{BASE_URL}/api/admin/devices", headers=self.headers)
        assert devices_response.status_code == 200, f"Failed to get devices: {devices_response.text}"
        devices = devices_response.json()
        assert len(devices) > 0, "No devices found for testing"
        self.device = devices[0]
        self.device_id = self.device["id"]
        
        yield
        
        # Cleanup - delete test services
        services_response = requests.get(f"{BASE_URL}/api/admin/services", headers=self.headers)
        if services_response.status_code == 200:
            for service in services_response.json():
                if service.get("notes", "").startswith("TEST_"):
                    requests.delete(f"{BASE_URL}/api/admin/services/{service['id']}", headers=self.headers)
    
    def test_create_internal_service_minimal_fields(self):
        """Create internal service record with minimal required fields"""
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Replaced faulty component",
            "notes": "TEST_internal_minimal"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["device_id"] == self.device_id
        assert data["service_category"] == "internal_service"  # Default
        assert data["service_responsibility"] == "our_team"  # Default
        assert data["counts_toward_amc"] == True  # Default for internal
        assert "id" in data
        
        print("✓ Internal service created with minimal fields")
        return data["id"]
    
    def test_create_oem_warranty_service_with_oem_details(self):
        """Create OEM warranty service record with required OEM details"""
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Coordinated with Dell for motherboard replacement",
            "service_category": "oem_warranty_service",
            "oem_details": {
                "oem_name": "Dell",
                "oem_case_number": "SR123456789",
                "oem_warranty_type": "ProSupport",
                "case_raised_date": datetime.now().strftime("%Y-%m-%d"),
                "case_raised_via": "phone",
                "oem_priority": "NBD",
                "oem_case_status": "reported_to_oem"
            },
            "notes": "TEST_oem_service"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["service_category"] == "oem_warranty_service"
        assert data["service_responsibility"] == "oem"  # Auto-locked
        assert data["service_role"] == "coordinator_facilitator"  # Auto-locked
        assert data["billing_impact"] == "warranty_covered"  # Auto-locked
        assert data["counts_toward_amc"] == False  # Auto-locked for OEM
        
        # Verify OEM details
        assert data["oem_details"]["oem_name"] == "Dell"
        assert data["oem_details"]["oem_case_number"] == "SR123456789"
        assert data["oem_details"]["oem_warranty_type"] == "ProSupport"
        
        print("✓ OEM warranty service created with auto-locked fields")
        return data["id"]
    
    def test_oem_service_requires_oem_details(self):
        """OEM service without oem_details should fail validation"""
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Missing OEM details",
            "service_category": "oem_warranty_service",
            # Missing oem_details
            "notes": "TEST_oem_missing_details"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "OEM Service Details are required" in response.json().get("detail", "")
        
        print("✓ OEM service validation correctly rejects missing oem_details")
    
    def test_oem_service_requires_oem_name(self):
        """OEM service requires oem_name field"""
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Missing OEM name",
            "service_category": "oem_warranty_service",
            "oem_details": {
                # Missing oem_name
                "oem_case_number": "SR123456789",
                "oem_warranty_type": "Standard",
                "case_raised_date": datetime.now().strftime("%Y-%m-%d"),
                "case_raised_via": "phone"
            },
            "notes": "TEST_oem_missing_name"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "OEM Name is required" in response.json().get("detail", "")
        
        print("✓ OEM service validation correctly rejects missing oem_name")
    
    def test_oem_service_requires_case_number(self):
        """OEM service requires oem_case_number field"""
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Missing case number",
            "service_category": "oem_warranty_service",
            "oem_details": {
                "oem_name": "Dell",
                # Missing oem_case_number
                "oem_warranty_type": "Standard",
                "case_raised_date": datetime.now().strftime("%Y-%m-%d"),
                "case_raised_via": "phone"
            },
            "notes": "TEST_oem_missing_case"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "OEM Case/SR Number is required" in response.json().get("detail", "")
        
        print("✓ OEM service validation correctly rejects missing oem_case_number")
    
    def test_oem_service_requires_warranty_type(self):
        """OEM service requires oem_warranty_type field"""
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Missing warranty type",
            "service_category": "oem_warranty_service",
            "oem_details": {
                "oem_name": "Dell",
                "oem_case_number": "SR123456789",
                # Missing oem_warranty_type
                "case_raised_date": datetime.now().strftime("%Y-%m-%d"),
                "case_raised_via": "phone"
            },
            "notes": "TEST_oem_missing_warranty_type"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "OEM Warranty Type is required" in response.json().get("detail", "")
        
        print("✓ OEM service validation correctly rejects missing oem_warranty_type")
    
    def test_oem_service_requires_case_raised_date(self):
        """OEM service requires case_raised_date field"""
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Missing case raised date",
            "service_category": "oem_warranty_service",
            "oem_details": {
                "oem_name": "Dell",
                "oem_case_number": "SR123456789",
                "oem_warranty_type": "Standard",
                # Missing case_raised_date
                "case_raised_via": "phone"
            },
            "notes": "TEST_oem_missing_raised_date"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "Case Raised Date is required" in response.json().get("detail", "")
        
        print("✓ OEM service validation correctly rejects missing case_raised_date")
    
    def test_oem_service_requires_case_raised_via(self):
        """OEM service requires case_raised_via field"""
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Missing case raised via",
            "service_category": "oem_warranty_service",
            "oem_details": {
                "oem_name": "Dell",
                "oem_case_number": "SR123456789",
                "oem_warranty_type": "Standard",
                "case_raised_date": datetime.now().strftime("%Y-%m-%d")
                # Missing case_raised_via
            },
            "notes": "TEST_oem_missing_raised_via"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "Case Raised Via is required" in response.json().get("detail", "")
        
        print("✓ OEM service validation correctly rejects missing case_raised_via")


class TestServiceFilters:
    """Test service listing with filters"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_list_services_no_filter(self):
        """List all services without filters"""
        response = requests.get(f"{BASE_URL}/api/admin/services", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Listed {len(data)} services without filters")
    
    def test_list_services_filter_by_category(self):
        """List services filtered by service_category"""
        response = requests.get(
            f"{BASE_URL}/api/admin/services?service_category=internal_service", 
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        # Verify all returned services have the correct category
        for service in data:
            assert service.get("service_category") == "internal_service", \
                f"Expected internal_service, got {service.get('service_category')}"
        
        print(f"✓ Listed {len(data)} internal services with category filter")
    
    def test_list_services_filter_by_status(self):
        """List services filtered by status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/services?status=open", 
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        # Verify all returned services have the correct status
        for service in data:
            assert service.get("status") == "open", \
                f"Expected open, got {service.get('status')}"
        
        print(f"✓ Listed {len(data)} open services with status filter")
    
    def test_list_services_filter_by_device(self):
        """List services filtered by device_id"""
        # First get a device
        devices_response = requests.get(f"{BASE_URL}/api/admin/devices", headers=self.headers)
        assert devices_response.status_code == 200
        devices = devices_response.json()
        if len(devices) == 0:
            pytest.skip("No devices available for testing")
        
        device_id = devices[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/admin/services?device_id={device_id}", 
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        # Verify all returned services have the correct device_id
        for service in data:
            assert service.get("device_id") == device_id, \
                f"Expected {device_id}, got {service.get('device_id')}"
        
        print(f"✓ Listed {len(data)} services for device {device_id}")


class TestServiceUpdate:
    """Test service update operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and create test service"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a device
        devices_response = requests.get(f"{BASE_URL}/api/admin/devices", headers=self.headers)
        assert devices_response.status_code == 200
        devices = devices_response.json()
        assert len(devices) > 0, "No devices found"
        self.device_id = devices[0]["id"]
        
        # Create a test service
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Initial action",
            "notes": "TEST_update_test"
        }
        create_response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert create_response.status_code == 200
        self.service_id = create_response.json()["id"]
        
        yield
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/services/{self.service_id}", headers=self.headers)
    
    def test_update_service_basic_fields(self):
        """Update basic service fields"""
        update_data = {
            "action_taken": "TEST_Updated action taken",
            "status": "in_progress",
            "technician_name": "John Doe"
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/services/{self.service_id}", 
            json=update_data, 
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["action_taken"] == "TEST_Updated action taken"
        assert data["status"] == "in_progress"
        assert data["technician_name"] == "John Doe"
        
        print("✓ Service basic fields updated successfully")
    
    def test_update_service_to_oem_category(self):
        """Update service to OEM category with OEM details"""
        update_data = {
            "service_category": "oem_warranty_service",
            "oem_details": {
                "oem_name": "HP",
                "oem_case_number": "CASE-987654",
                "oem_warranty_type": "NBD",
                "case_raised_date": datetime.now().strftime("%Y-%m-%d"),
                "case_raised_via": "oem_portal",
                "oem_priority": "Standard",
                "oem_case_status": "oem_accepted"
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/services/{self.service_id}", 
            json=update_data, 
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["service_category"] == "oem_warranty_service"
        assert data["service_responsibility"] == "oem"  # Auto-locked
        assert data["counts_toward_amc"] == False  # Auto-locked
        assert data["oem_details"]["oem_name"] == "HP"
        
        print("✓ Service updated to OEM category with auto-locked fields")


class TestServiceClosure:
    """Test service closure with outcome"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token and create test service"""
        login_response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert login_response.status_code == 200, f"Login failed: {login_response.text}"
        self.token = login_response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Get a device
        devices_response = requests.get(f"{BASE_URL}/api/admin/devices", headers=self.headers)
        assert devices_response.status_code == 200
        devices = devices_response.json()
        assert len(devices) > 0, "No devices found"
        self.device_id = devices[0]["id"]
        
        # Create a test service
        service_data = {
            "device_id": self.device_id,
            "service_date": datetime.now().strftime("%Y-%m-%d"),
            "service_type": "Repair",
            "action_taken": "TEST_Closure test action",
            "notes": "TEST_closure_test"
        }
        create_response = requests.post(f"{BASE_URL}/api/admin/services", json=service_data, headers=self.headers)
        assert create_response.status_code == 200
        self.service_id = create_response.json()["id"]
        
        yield
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/services/{self.service_id}", headers=self.headers)
    
    def test_close_service_requires_resolution_summary(self):
        """Closing service requires resolution_summary in service_outcome"""
        update_data = {
            "status": "closed"
            # Missing service_outcome with resolution_summary
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/services/{self.service_id}", 
            json=update_data, 
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "Resolution summary is required" in response.json().get("detail", "")
        
        print("✓ Service closure correctly requires resolution_summary")
    
    def test_close_service_with_outcome(self):
        """Close service with proper service_outcome"""
        update_data = {
            "status": "closed",
            "service_outcome": {
                "resolution_summary": "TEST_Issue resolved by replacing faulty RAM module",
                "part_replaced": "RAM 8GB DDR4",
                "cost_incurred": 0,
                "closed_by": "Our Team",
                "closure_date": datetime.now().strftime("%Y-%m-%d")
            }
        }
        
        response = requests.put(
            f"{BASE_URL}/api/admin/services/{self.service_id}", 
            json=update_data, 
            headers=self.headers
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["status"] == "closed"
        assert data["is_closed"] == True
        assert data["closed_at"] is not None
        assert data["service_outcome"]["resolution_summary"] == "TEST_Issue resolved by replacing faulty RAM module"
        
        print("✓ Service closed successfully with outcome")
    
    def test_closed_service_cannot_be_modified(self):
        """Closed service records cannot be modified"""
        # First close the service
        close_data = {
            "status": "closed",
            "service_outcome": {
                "resolution_summary": "TEST_Closed for modification test",
                "closed_by": "Our Team",
                "closure_date": datetime.now().strftime("%Y-%m-%d")
            }
        }
        close_response = requests.put(
            f"{BASE_URL}/api/admin/services/{self.service_id}", 
            json=close_data, 
            headers=self.headers
        )
        assert close_response.status_code == 200
        
        # Try to modify closed service
        update_data = {
            "action_taken": "TEST_Trying to modify closed service"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/services/{self.service_id}", 
            json=update_data, 
            headers=self.headers
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "Closed service records cannot be modified" in response.json().get("detail", "")
        
        print("✓ Closed service correctly rejects modifications")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
