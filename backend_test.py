#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class WarrantyPortalTester:
    def __init__(self, base_url="https://devicetrack-hub.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {
            'admin_id': None,
            'company_id': None,
            'user_id': None,
            'device_id': None,
            'part_id': None,
            'amc_id': None,
            'amc_contract_id': None,
            'service_id': None,
            'master_id': None,
            'serial_number': None
        }

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        test_headers = {'Content-Type': 'application/json'}
        if self.token:
            test_headers['Authorization'] = f'Bearer {self.token}'
        if headers:
            test_headers.update(headers)

        self.tests_run += 1
        self.log(f"🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=test_headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=test_headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=test_headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=test_headers, timeout=10)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                self.log(f"✅ {name} - Status: {response.status_code}")
                try:
                    return True, response.json() if response.content else {}
                except:
                    return True, {}
            else:
                self.log(f"❌ {name} - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json().get('detail', 'No detail')
                    self.log(f"   Error: {error_detail}")
                except:
                    self.log(f"   Response: {response.text[:200]}")
                return False, {}

        except Exception as e:
            self.log(f"❌ {name} - Error: {str(e)}")
            return False, {}

    def test_basic_endpoints(self):
        """Test basic public endpoints"""
        self.log("\n=== Testing Basic Endpoints ===")
        
        # Test root endpoint
        success, _ = self.run_test("Root API", "GET", "", 200)
        
        # Test public settings
        success, _ = self.run_test("Public Settings", "GET", "settings/public", 200)
        
        return success

    def test_admin_setup_and_auth(self):
        """Test admin setup and authentication"""
        self.log("\n=== Testing Admin Setup & Auth ===")
        
        # Create admin account
        admin_data = {
            "name": "Test Admin",
            "email": f"admin_{datetime.now().strftime('%H%M%S')}@test.com",
            "password": "TestPass123!"
        }
        
        success, response = self.run_test("Admin Setup", "POST", "auth/setup", 200, admin_data)
        if not success:
            return False
        
        # Login with created admin
        login_data = {
            "email": admin_data["email"],
            "password": admin_data["password"]
        }
        
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, login_data)
        if not success:
            return False
        
        self.token = response.get('access_token')
        if not self.token:
            self.log("❌ No access token received")
            return False
        
        # Test auth/me endpoint
        success, response = self.run_test("Get Current Admin", "GET", "auth/me", 200)
        if success:
            self.test_data['admin_id'] = response.get('id')
        
        return success

    def test_company_crud(self):
        """Test company CRUD operations"""
        self.log("\n=== Testing Company CRUD ===")
        
        # Create company
        company_data = {
            "name": f"Test Company {datetime.now().strftime('%H%M%S')}",
            "gst_number": "29ABCDE1234F1Z5",
            "address": "123 Test Street, Test City",
            "contact_name": "John Doe",
            "contact_email": "john@testcompany.com",
            "contact_phone": "+91-9876543210",
            "amc_status": "active",
            "notes": "Test company for warranty portal"
        }
        
        success, response = self.run_test("Create Company", "POST", "admin/companies", 200, company_data)
        if not success:
            return False
        
        self.test_data['company_id'] = response.get('id')
        
        # List companies
        success, _ = self.run_test("List Companies", "GET", "admin/companies", 200)
        if not success:
            return False
        
        # Get specific company
        success, _ = self.run_test("Get Company", "GET", f"admin/companies/{self.test_data['company_id']}", 200)
        if not success:
            return False
        
        # Update company
        update_data = {"notes": "Updated test company"}
        success, _ = self.run_test("Update Company", "PUT", f"admin/companies/{self.test_data['company_id']}", 200, update_data)
        
        return success

    def test_user_crud(self):
        """Test user CRUD operations"""
        self.log("\n=== Testing User CRUD ===")
        
        if not self.test_data['company_id']:
            self.log("❌ No company ID available for user tests")
            return False
        
        # Create user
        user_data = {
            "company_id": self.test_data['company_id'],
            "name": "Test User",
            "email": f"user_{datetime.now().strftime('%H%M%S')}@test.com",
            "phone": "+91-9876543211",
            "role": "employee",
            "status": "active"
        }
        
        success, response = self.run_test("Create User", "POST", "admin/users", 200, user_data)
        if not success:
            return False
        
        self.test_data['user_id'] = response.get('id')
        
        # List users
        success, _ = self.run_test("List Users", "GET", "admin/users", 200)
        if not success:
            return False
        
        # Get specific user
        success, _ = self.run_test("Get User", "GET", f"admin/users/{self.test_data['user_id']}", 200)
        if not success:
            return False
        
        # Update user
        update_data = {"phone": "+91-9876543299"}
        success, _ = self.run_test("Update User", "PUT", f"admin/users/{self.test_data['user_id']}", 200, update_data)
        
        return success

    def test_device_crud(self):
        """Test device CRUD operations"""
        self.log("\n=== Testing Device CRUD ===")
        
        if not self.test_data['company_id']:
            self.log("❌ No company ID available for device tests")
            return False
        
        # Create device
        device_data = {
            "company_id": self.test_data['company_id'],
            "assigned_user_id": self.test_data['user_id'],
            "device_type": "Laptop",
            "brand": "Dell",
            "model": "Latitude 5520",
            "serial_number": f"DL{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "asset_tag": f"AST{datetime.now().strftime('%H%M%S')}",
            "purchase_date": "2024-01-15",
            "warranty_end_date": "2027-01-15",
            "status": "active"
        }
        
        success, response = self.run_test("Create Device", "POST", "admin/devices", 200, device_data)
        if not success:
            return False
        
        self.test_data['device_id'] = response.get('id')
        self.test_data['serial_number'] = device_data['serial_number']
        
        # List devices
        success, _ = self.run_test("List Devices", "GET", "admin/devices", 200)
        if not success:
            return False
        
        # Get specific device
        success, _ = self.run_test("Get Device", "GET", f"admin/devices/{self.test_data['device_id']}", 200)
        if not success:
            return False
        
        # Update device
        update_data = {"status": "active"}
        success, _ = self.run_test("Update Device", "PUT", f"admin/devices/{self.test_data['device_id']}", 200, update_data)
        
        return success

    def test_parts_crud(self):
        """Test parts CRUD operations"""
        self.log("\n=== Testing Parts CRUD ===")
        
        if not self.test_data['device_id']:
            self.log("❌ No device ID available for parts tests")
            return False
        
        # Create part
        part_data = {
            "device_id": self.test_data['device_id'],
            "part_name": "Keyboard",
            "replaced_date": "2024-06-15",
            "warranty_months": 6,
            "notes": "Replaced due to key malfunction"
        }
        
        success, response = self.run_test("Create Part", "POST", "admin/parts", 200, part_data)
        if not success:
            return False
        
        self.test_data['part_id'] = response.get('id')
        
        # List parts
        success, _ = self.run_test("List Parts", "GET", "admin/parts", 200)
        if not success:
            return False
        
        # Get specific part
        success, _ = self.run_test("Get Part", "GET", f"admin/parts/{self.test_data['part_id']}", 200)
        if not success:
            return False
        
        # Update part
        update_data = {"warranty_months": 12}
        success, _ = self.run_test("Update Part", "PUT", f"admin/parts/{self.test_data['part_id']}", 200, update_data)
        
        return success

    def test_amc_crud(self):
        """Test AMC CRUD operations"""
        self.log("\n=== Testing AMC CRUD ===")
        
        if not self.test_data['device_id']:
            self.log("❌ No device ID available for AMC tests")
            return False
        
        # Create AMC
        today = datetime.now().date()
        next_year = today + timedelta(days=365)
        
        amc_data = {
            "device_id": self.test_data['device_id'],
            "start_date": today.isoformat(),
            "end_date": next_year.isoformat(),
            "notes": "Annual maintenance contract for laptop"
        }
        
        success, response = self.run_test("Create AMC", "POST", "admin/amc", 200, amc_data)
        if not success:
            return False
        
        self.test_data['amc_id'] = response.get('id')
        
        # List AMC
        success, _ = self.run_test("List AMC", "GET", "admin/amc", 200)
        if not success:
            return False
        
        # Get specific AMC
        success, _ = self.run_test("Get AMC", "GET", f"admin/amc/{self.test_data['amc_id']}", 200)
        if not success:
            return False
        
        # Update AMC
        update_data = {"notes": "Updated AMC contract"}
        success, _ = self.run_test("Update AMC", "PUT", f"admin/amc/{self.test_data['amc_id']}", 200, update_data)
        
        return success

    def test_warranty_search(self):
        """Test public warranty search functionality"""
        self.log("\n=== Testing Warranty Search ===")
        
        if not self.test_data.get('serial_number'):
            self.log("❌ No serial number available for warranty search")
            return False
        
        # Test warranty search by serial number
        success, response = self.run_test(
            "Warranty Search", 
            "GET", 
            f"warranty/search?q={self.test_data['serial_number']}", 
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['device', 'company_name', 'parts', 'amc']
            for field in required_fields:
                if field not in response:
                    self.log(f"❌ Missing field '{field}' in warranty search response")
                    return False
            
            self.log("✅ Warranty search response structure is valid")
        
        return success

    def test_pdf_generation(self):
        """Test PDF generation"""
        self.log("\n=== Testing PDF Generation ===")
        
        if not self.test_data.get('serial_number'):
            self.log("❌ No serial number available for PDF generation")
            return False
        
        # Test PDF generation
        url = f"{self.base_url}/warranty/pdf/{self.test_data['serial_number']}"
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200 and response.headers.get('content-type') == 'application/pdf':
                self.tests_run += 1
                self.tests_passed += 1
                self.log("✅ PDF Generation - Status: 200, Content-Type: application/pdf")
                return True
            else:
                self.tests_run += 1
                self.log(f"❌ PDF Generation - Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
                return False
        except Exception as e:
            self.tests_run += 1
            self.log(f"❌ PDF Generation - Error: {str(e)}")
            return False

    def test_dashboard_stats(self):
        """Test dashboard statistics"""
        self.log("\n=== Testing Dashboard Stats ===")
        
        success, response = self.run_test("Dashboard Stats", "GET", "admin/dashboard", 200)
        
        if success:
            # Verify response structure
            required_fields = ['companies_count', 'users_count', 'devices_count', 'parts_count', 'active_warranties', 'expired_warranties', 'active_amc']
            for field in required_fields:
                if field not in response:
                    self.log(f"❌ Missing field '{field}' in dashboard response")
                    return False
            
            self.log("✅ Dashboard stats structure is valid")
        
        return success

    def test_settings_crud(self):
        """Test settings CRUD operations"""
        self.log("\n=== Testing Settings CRUD ===")
        
        # Get settings
        success, _ = self.run_test("Get Settings", "GET", "admin/settings", 200)
        if not success:
            return False
        
        # Update settings
        settings_data = {
            "company_name": "Test Warranty Portal",
            "accent_color": "#059669"
        }
        
        success, _ = self.run_test("Update Settings", "PUT", "admin/settings", 200, settings_data)
        
        return success

    def test_master_data_crud(self):
        """Test Master Data CRUD operations"""
        self.log("\n=== Testing Master Data CRUD ===")
        
        # Test getting all masters
        success, response = self.run_test("List All Masters", "GET", "admin/masters", 200)
        if not success:
            return False
        
        # Test getting masters by type
        success, _ = self.run_test("List Device Types", "GET", "admin/masters?master_type=device_type", 200)
        if not success:
            return False
        
        success, _ = self.run_test("List Brands", "GET", "admin/masters?master_type=brand", 200)
        if not success:
            return False
        
        success, _ = self.run_test("List Service Types", "GET", "admin/masters?master_type=service_type", 200)
        if not success:
            return False
        
        # Create a new master item (Brand)
        master_data = {
            "type": "brand",
            "name": f"Samsung Test {datetime.now().strftime('%H%M%S')}",
            "code": f"SAMSUNG_TEST_{datetime.now().strftime('%H%M%S')}",
            "description": "Test brand for warranty portal",
            "is_active": True,
            "sort_order": 50
        }
        
        success, response = self.run_test("Create Master Item", "POST", "admin/masters", 200, master_data)
        if not success:
            return False
        
        master_id = response.get('id')
        self.test_data['master_id'] = master_id
        
        # Update master item
        update_data = {
            "description": "Updated test brand description",
            "sort_order": 60
        }
        
        success, _ = self.run_test("Update Master Item", "PUT", f"admin/masters/{master_id}", 200, update_data)
        if not success:
            return False
        
        # Disable master item (soft delete)
        success, _ = self.run_test("Disable Master Item", "DELETE", f"admin/masters/{master_id}", 200)
        
        return success

    def test_service_history_crud(self):
        """Test Service History CRUD operations"""
        self.log("\n=== Testing Service History CRUD ===")
        
        if not self.test_data['device_id']:
            self.log("❌ No device ID available for service history tests")
            return False
        
        # Create service record
        service_data = {
            "device_id": self.test_data['device_id'],
            "service_date": "2024-12-15",
            "service_type": "repair",
            "problem_reported": "Laptop not booting properly",
            "action_taken": "Replaced faulty RAM module and updated BIOS",
            "parts_involved": [
                {
                    "part_name": "RAM",
                    "old_part": "8GB DDR4",
                    "new_part": "16GB DDR4",
                    "warranty_started": "2024-12-15"
                }
            ],
            "warranty_impact": "started",
            "technician_name": "John Smith",
            "ticket_id": f"TKT{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "notes": "Customer reported slow performance. Diagnosed RAM issue."
        }
        
        success, response = self.run_test("Create Service Record", "POST", "admin/services", 200, service_data)
        if not success:
            return False
        
        service_id = response.get('id')
        self.test_data['service_id'] = service_id
        
        # List all services
        success, _ = self.run_test("List All Services", "GET", "admin/services", 200)
        if not success:
            return False
        
        # List services for specific device
        success, _ = self.run_test("List Device Services", "GET", f"admin/services?device_id={self.test_data['device_id']}", 200)
        if not success:
            return False
        
        # Get specific service
        success, _ = self.run_test("Get Service Record", "GET", f"admin/services/{service_id}", 200)
        if not success:
            return False
        
        # Update service record
        update_data = {
            "notes": "Updated service notes - customer satisfied with repair",
            "warranty_impact": "extended"
        }
        
        success, _ = self.run_test("Update Service Record", "PUT", f"admin/services/{service_id}", 200, update_data)
        
        return success

    def test_dashboard_alerts(self):
        """Test Dashboard Alerts API"""
        self.log("\n=== Testing Dashboard Alerts ===")
        
        # Test dashboard alerts endpoint
        success, response = self.run_test("Dashboard Alerts", "GET", "admin/dashboard/alerts", 200)
        
        if success:
            # Verify response structure
            required_fields = [
                'warranty_expiring_7_days', 
                'warranty_expiring_15_days', 
                'warranty_expiring_30_days',
                'amc_expiring_7_days',
                'amc_expiring_15_days',
                'amc_expiring_30_days',
                'devices_in_repair'
            ]
            for field in required_fields:
                if field not in response:
                    self.log(f"❌ Missing field '{field}' in dashboard alerts response")
                    return False
            
            self.log("✅ Dashboard alerts structure is valid")
        
        return success

    def test_device_timeline(self):
        """Test Device Timeline API"""
        self.log("\n=== Testing Device Timeline ===")
        
        if not self.test_data['device_id']:
            self.log("❌ No device ID available for timeline tests")
            return False
        
        # Test device timeline
        success, response = self.run_test("Device Timeline", "GET", f"admin/devices/{self.test_data['device_id']}/timeline", 200)
        
        if success:
            # Verify response is a list
            if not isinstance(response, list):
                self.log("❌ Timeline response should be a list")
                return False
            
            # Check if timeline has entries (should have at least purchase event)
            if len(response) == 0:
                self.log("❌ Timeline should have at least one entry")
                return False
            
            # Verify timeline entry structure
            for entry in response:
                required_fields = ['type', 'date', 'title', 'description']
                for field in required_fields:
                    if field not in entry:
                        self.log(f"❌ Missing field '{field}' in timeline entry")
                        return False
            
            self.log("✅ Device timeline structure is valid")
        
        return success

    def test_admin_login_with_demo_credentials(self):
        """Test admin login with demo credentials from review request"""
        self.log("\n=== Testing Admin Login with Demo Credentials ===")
        
        # First, create the demo admin if it doesn't exist
        demo_admin_data = {
            "name": "Demo Admin",
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        # Try to create demo admin (might fail if already exists, that's OK)
        self.run_test("Create Demo Admin", "POST", "auth/setup", 200, demo_admin_data)
        
        # Login with demo credentials
        login_data = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        success, response = self.run_test("Demo Admin Login", "POST", "auth/login", 200, login_data)
        if not success:
            return False
        
        demo_token = response.get('access_token')
        if not demo_token:
            self.log("❌ No access token received for demo admin")
            return False
        
        # Set the demo token as the main token for subsequent tests
        self.token = demo_token
        
        # Test auth/me endpoint with demo credentials
        success, response = self.run_test("Get Demo Admin Info", "GET", "auth/me", 200)
        if success:
            if response.get('email') != 'admin@demo.com':
                self.log("❌ Demo admin email mismatch")
                success = False
            else:
                self.test_data['admin_id'] = response.get('id')
        
        return success

    def test_amc_contracts_v2_crud(self):
        """Test AMC Contracts v2 CRUD operations"""
        self.log("\n=== Testing AMC Contracts v2 CRUD ===")
        
        if not self.test_data['company_id']:
            self.log("❌ No company ID available for AMC contracts tests")
            return False
        
        # List all AMC contracts (should be empty initially)
        success, response = self.run_test("List AMC Contracts", "GET", "admin/amc-contracts", 200)
        if not success:
            return False
        
        # Create new AMC contract
        contract_data = {
            "company_id": self.test_data['company_id'],
            "name": "Test AMC 2025-26",
            "amc_type": "comprehensive",
            "start_date": "2025-01-01",
            "end_date": "2025-12-31",
            "coverage_includes": {
                "onsite_support": True,
                "remote_support": True,
                "preventive_maintenance": True
            },
            "exclusions": {
                "hardware_parts": True,
                "consumables": True
            },
            "asset_mapping": {
                "mapping_type": "all_company",
                "selected_asset_ids": [],
                "selected_device_types": []
            }
        }
        
        success, response = self.run_test("Create AMC Contract", "POST", "admin/amc-contracts", 200, contract_data)
        if not success:
            return False
        
        contract_id = response.get('id')
        self.test_data['amc_contract_id'] = contract_id
        
        # Verify contract has computed status
        if 'status' not in response:
            self.log("❌ AMC contract response missing computed status")
            return False
        
        # Get specific AMC contract with covered assets
        success, response = self.run_test("Get AMC Contract Details", "GET", f"admin/amc-contracts/{contract_id}", 200)
        if not success:
            return False
        
        # Verify response structure
        required_fields = ['covered_assets', 'covered_assets_count', 'usage_history', 'usage_stats']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ Missing field '{field}' in AMC contract details")
                return False
        
        # Update AMC contract
        update_data = {
            "name": "Updated Test AMC 2025-26",
            "internal_notes": "Updated contract for testing"
        }
        
        success, _ = self.run_test("Update AMC Contract", "PUT", f"admin/amc-contracts/{contract_id}", 200, update_data)
        
        return success

    def test_amc_coverage_check(self):
        """Test AMC coverage check for devices"""
        self.log("\n=== Testing AMC Coverage Check ===")
        
        if not self.test_data['device_id']:
            self.log("❌ No device ID available for coverage check")
            return False
        
        # Check AMC coverage for device
        success, response = self.run_test("Check AMC Coverage", "GET", f"admin/amc-contracts/check-coverage/{self.test_data['device_id']}", 200)
        if not success:
            return False
        
        # Verify response structure
        required_fields = ['device_id', 'device_info', 'is_covered', 'active_contracts']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ Missing field '{field}' in coverage check response")
                return False
        
        # If we created an AMC contract for all company devices, this should be covered
        if self.test_data.get('amc_contract_id') and not response.get('is_covered'):
            self.log("⚠️  Device should be covered by AMC contract but shows as not covered")
        
        return success

    def test_companies_without_amc(self):
        """Test companies without AMC endpoint"""
        self.log("\n=== Testing Companies Without AMC ===")
        
        # Get companies without active AMC
        success, response = self.run_test("Companies Without AMC", "GET", "admin/companies-without-amc", 200)
        if not success:
            return False
        
        # Verify response is a list
        if not isinstance(response, list):
            self.log("❌ Companies without AMC response should be a list")
            return False
        
        # If response has items, verify structure
        if len(response) > 0:
            required_fields = ['id', 'name', 'contact_email']
            for field in required_fields:
                if field not in response[0]:
                    self.log(f"❌ Missing field '{field}' in companies without AMC response")
                    return False
        
        return success

    def test_dashboard_alerts_with_amc_contracts(self):
        """Test Dashboard Alerts API with AMC contracts alerts"""
        self.log("\n=== Testing Dashboard Alerts with AMC Contracts ===")
        
        # Test dashboard alerts endpoint
        success, response = self.run_test("Dashboard Alerts with AMC Contracts", "GET", "admin/dashboard/alerts", 200)
        
        if success:
            # Verify response structure includes new AMC contract fields
            required_fields = [
                'warranty_expiring_7_days', 
                'warranty_expiring_15_days', 
                'warranty_expiring_30_days',
                'amc_expiring_7_days',
                'amc_expiring_15_days',
                'amc_expiring_30_days',
                'amc_contracts_expiring_7_days',
                'amc_contracts_expiring_15_days',
                'amc_contracts_expiring_30_days',
                'companies_without_amc',
                'devices_in_repair'
            ]
            for field in required_fields:
                if field not in response:
                    self.log(f"❌ Missing field '{field}' in dashboard alerts response")
                    return False
            
            self.log("✅ Dashboard alerts structure with AMC contracts is valid")
        
        return success

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Warranty Portal API Tests")
        self.log(f"Base URL: {self.base_url}")
        
        test_results = []
        
        # Run tests in order
        tests = [
            ("Basic Endpoints", self.test_basic_endpoints),
            ("Admin Setup & Auth", self.test_admin_setup_and_auth),
            ("Demo Admin Login", self.test_admin_login_with_demo_credentials),
            ("Master Data CRUD", self.test_master_data_crud),
            ("Company CRUD", self.test_company_crud),
            ("User CRUD", self.test_user_crud),
            ("Device CRUD", self.test_device_crud),
            ("Service History CRUD", self.test_service_history_crud),
            ("Parts CRUD", self.test_parts_crud),
            ("AMC CRUD", self.test_amc_crud),
            ("Device Timeline", self.test_device_timeline),
            ("Warranty Search", self.test_warranty_search),
            ("PDF Generation", self.test_pdf_generation),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Dashboard Alerts", self.test_dashboard_alerts),
            ("Settings CRUD", self.test_settings_crud)
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results.append((test_name, result))
                if not result:
                    self.log(f"⚠️  {test_name} failed - continuing with remaining tests")
            except Exception as e:
                self.log(f"💥 {test_name} crashed: {str(e)}")
                test_results.append((test_name, False))
        
        # Print summary
        self.log(f"\n📊 Test Summary:")
        self.log(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        self.log(f"\n📋 Test Results by Category:")
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {status} - {test_name}")
        
        return self.tests_passed, self.tests_run, test_results

def main():
    tester = WarrantyPortalTester()
    passed, total, results = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())