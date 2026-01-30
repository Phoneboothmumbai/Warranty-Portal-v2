#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class WarrantyPortalTester:
    def __init__(self, base_url="https://mspsaas.preview.emergentagent.com/api"):
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
            'serial_number': None,
            'site_id': None,
            'deployment_id': None
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

    def test_sites_crud(self):
        """Test Sites CRUD operations"""
        self.log("\n=== Testing Sites CRUD ===")
        
        if not self.test_data['company_id']:
            self.log("❌ No company ID available for sites tests")
            return False
        
        # Create site
        site_data = {
            "company_id": self.test_data['company_id'],
            "name": "Wadhwa 1620 – Mulund",
            "site_type": "site_project",
            "address": "Plot 1620, Mulund West",
            "city": "Mumbai",
            "primary_contact_name": "Site Manager",
            "contact_number": "+91 9876543210",
            "contact_email": "sitemanager@wadhwa.com",
            "notes": "Test site for deployment testing"
        }
        
        success, response = self.run_test("Create Site", "POST", "admin/sites", 200, site_data)
        if not success:
            return False
        
        self.test_data['site_id'] = response.get('id')
        
        # List all sites
        success, _ = self.run_test("List All Sites", "GET", "admin/sites", 200)
        if not success:
            return False
        
        # Get specific site
        success, response = self.run_test("Get Site Details", "GET", f"admin/sites/{self.test_data['site_id']}", 200)
        if not success:
            return False
        
        # Verify site response structure
        required_fields = ['id', 'company_id', 'name', 'site_type', 'address', 'city']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ Missing field '{field}' in site response")
                return False
        
        # Update site
        update_data = {
            "notes": "Updated site notes for testing",
            "contact_email": "updated@wadhwa.com"
        }
        
        success, _ = self.run_test("Update Site", "PUT", f"admin/sites/{self.test_data['site_id']}", 200, update_data)
        
        return success

    def test_deployments_crud(self):
        """Test Deployments CRUD operations"""
        self.log("\n=== Testing Deployments CRUD ===")
        
        if not self.test_data['company_id'] or not self.test_data['site_id']:
            self.log("❌ No company ID or site ID available for deployments tests")
            return False
        
        # Create deployment with items
        deployment_data = {
            "company_id": self.test_data['company_id'],
            "site_id": self.test_data['site_id'],
            "name": "Phase 1 CCTV Installation",
            "deployment_date": "2025-01-01",
            "installed_by": "Internal Team",
            "notes": "Test deployment for CCTV system",
            "items": [
                {
                    "item_type": "device",
                    "category": "CCTV Camera",
                    "brand": "Hikvision",
                    "model": "DS-2CD2H43G2-IZS",
                    "quantity": 4,
                    "is_serialized": True,
                    "serial_numbers": ["CAM001", "CAM002", "CAM003", "CAM004"],
                    "zone_location": "Floor 1 - Lobby",
                    "warranty_type": "manufacturer",
                    "warranty_start_date": "2025-01-01",
                    "warranty_end_date": "2027-12-31"
                },
                {
                    "item_type": "infrastructure",
                    "category": "NVR",
                    "brand": "Hikvision",
                    "model": "DS-7608NI",
                    "quantity": 1,
                    "is_serialized": True,
                    "serial_numbers": ["NVR001"],
                    "zone_location": "Server Room",
                    "warranty_type": "manufacturer",
                    "warranty_start_date": "2025-01-01",
                    "warranty_end_date": "2027-12-31"
                }
            ]
        }
        
        success, response = self.run_test("Create Deployment", "POST", "admin/deployments", 200, deployment_data)
        if not success:
            return False
        
        self.test_data['deployment_id'] = response.get('id')
        
        # Verify deployment response structure
        required_fields = ['id', 'company_id', 'site_id', 'name', 'deployment_date', 'items']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ Missing field '{field}' in deployment response")
                return False
        
        # Verify items structure
        items = response.get('items', [])
        if len(items) != 2:
            self.log(f"❌ Expected 2 deployment items, got {len(items)}")
            return False
        
        # List all deployments
        success, _ = self.run_test("List All Deployments", "GET", "admin/deployments", 200)
        if not success:
            return False
        
        # Get specific deployment with full item details
        success, response = self.run_test("Get Deployment Details", "GET", f"admin/deployments/{self.test_data['deployment_id']}", 200)
        if not success:
            return False
        
        # Verify full deployment details
        if 'items' not in response or len(response['items']) == 0:
            self.log("❌ Deployment details should include items")
            return False
        
        # Update deployment
        update_data = {
            "notes": "Updated deployment notes - installation completed successfully",
            "installed_by": "External Vendor"
        }
        
        success, _ = self.run_test("Update Deployment", "PUT", f"admin/deployments/{self.test_data['deployment_id']}", 200, update_data)
        
        return success

    def test_device_auto_creation_from_deployment(self):
        """Test that devices are auto-created from deployment items"""
        self.log("\n=== Testing Device Auto-Creation from Deployment ===")
        
        if not self.test_data['deployment_id']:
            self.log("❌ No deployment ID available for device auto-creation test")
            return False
        
        # Get all devices and check for auto-created ones
        success, response = self.run_test("List All Devices (Check Auto-Creation)", "GET", "admin/devices", 200)
        if not success:
            return False
        
        # Look for devices with our deployment_id and site_id
        auto_created_devices = []
        expected_serials = ["CAM001", "CAM002", "CAM003", "CAM004", "NVR001"]
        
        for device in response:
            if device.get('serial_number') in expected_serials:
                auto_created_devices.append(device)
        
        if len(auto_created_devices) != 5:
            self.log(f"❌ Expected 5 auto-created devices, found {len(auto_created_devices)}")
            return False
        
        # Verify auto-created devices have correct properties
        for device in auto_created_devices:
            required_fields = ['id', 'company_id', 'serial_number', 'device_type', 'brand', 'model']
            for field in required_fields:
                if field not in device:
                    self.log(f"❌ Auto-created device missing field '{field}'")
                    return False
            
            # Check if device has site_id and deployment_id populated (if supported)
            if 'site_id' in device and device['site_id'] != self.test_data['site_id']:
                self.log(f"⚠️  Auto-created device site_id mismatch: expected {self.test_data['site_id']}, got {device.get('site_id')}")
        
        self.log(f"✅ Successfully verified {len(auto_created_devices)} auto-created devices")
        
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

    def test_license_crud_apis(self):
        """Test License CRUD APIs for Phase 2B"""
        self.log("\n=== Testing License CRUD APIs (Phase 2B) ===")
        
        if not self.test_data['company_id']:
            self.log("❌ No company ID available for license tests")
            return False
        
        # Test 1: Create a subscription license
        subscription_license_data = {
            "company_id": self.test_data['company_id'],
            "software_name": "Microsoft Office 365",
            "vendor": "Microsoft",
            "license_type": "subscription",
            "license_key": "XXXXX-XXXXX-XXXXX-XXXXX",
            "seats": 10,
            "start_date": "2026-01-01",
            "end_date": "2027-01-01",
            "purchase_cost": 15000,
            "renewal_cost": 12000,
            "auto_renew": True,
            "renewal_reminder_days": 30
        }
        
        success, response = self.run_test("Create Subscription License", "POST", "admin/licenses", 200, subscription_license_data)
        if not success:
            return False
        
        subscription_license_id = response.get('id')
        self.test_data['subscription_license_id'] = subscription_license_id
        
        # Verify response includes label field for SmartSelect
        if 'label' not in response:
            self.log("❌ License response missing 'label' field for SmartSelect")
            return False
        
        # Verify response includes calculated status
        if 'status' not in response:
            self.log("❌ License response missing calculated 'status' field")
            return False
        
        # Test 2: Create a perpetual license
        perpetual_license_data = {
            "company_id": self.test_data['company_id'],
            "software_name": "Adobe Photoshop CS6",
            "vendor": "Adobe",
            "license_type": "perpetual",
            "license_key": "YYYYY-YYYYY-YYYYY-YYYYY",
            "seats": 5,
            "start_date": "2025-01-01",
            "end_date": None,  # Perpetual license
            "purchase_cost": 25000,
            "auto_renew": False
        }
        
        success, response = self.run_test("Create Perpetual License", "POST", "admin/licenses", 200, perpetual_license_data)
        if not success:
            return False
        
        perpetual_license_id = response.get('id')
        self.test_data['perpetual_license_id'] = perpetual_license_id
        
        # Test 3: List all licenses
        success, response = self.run_test("List All Licenses", "GET", "admin/licenses", 200)
        if not success:
            return False
        
        # Verify licenses include required fields
        if len(response) > 0:
            license_item = response[0]
            required_fields = ['id', 'software_name', 'vendor', 'license_type', 'status', 'label', 'company_name']
            for field in required_fields:
                if field not in license_item:
                    self.log(f"❌ License list item missing field '{field}'")
                    return False
        
        # Test 4: List licenses with filters
        success, _ = self.run_test("List Active Licenses", "GET", "admin/licenses?status=active", 200)
        if not success:
            return False
        
        success, _ = self.run_test("List Subscription Licenses", "GET", "admin/licenses?license_type=subscription", 200)
        if not success:
            return False
        
        # Test 5: Get specific license details
        success, response = self.run_test("Get License Details", "GET", f"admin/licenses/{subscription_license_id}", 200)
        if not success:
            return False
        
        # Verify detailed response structure
        required_fields = ['id', 'software_name', 'vendor', 'license_type', 'seats', 'status', 'company_name']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ License details missing field '{field}'")
                return False
        
        # Test 6: Update license
        update_data = {
            "seats": 15,
            "renewal_cost": 13000,
            "notes": "Updated license for testing"
        }
        
        success, response = self.run_test("Update License", "PUT", f"admin/licenses/{subscription_license_id}", 200, update_data)
        if not success:
            return False
        
        # Test 7: Get expiring licenses summary
        success, response = self.run_test("Get Expiring Licenses Summary", "GET", "admin/licenses/expiring/summary", 200)
        if not success:
            return False
        
        # Verify summary structure
        required_fields = ['total', 'perpetual', 'active', 'expiring_7_days', 'expiring_30_days', 'expired']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ Expiring licenses summary missing field '{field}'")
                return False
        
        self.log("✅ All License CRUD APIs working correctly")
        return True

    def test_amc_device_assignment_apis(self):
        """Test AMC Device Assignment APIs for Phase 2B"""
        self.log("\n=== Testing AMC Device Assignment APIs (Phase 2B) ===")
        
        if not self.test_data.get('amc_contract_id') or not self.test_data.get('device_id'):
            self.log("❌ No AMC contract ID or device ID available for assignment tests")
            return False
        
        contract_id = self.test_data['amc_contract_id']
        device_id = self.test_data['device_id']
        
        # Test 1: Get assigned devices (should be empty initially)
        success, response = self.run_test("Get AMC Assigned Devices", "GET", f"admin/amc-contracts/{contract_id}/devices", 200)
        if not success:
            return False
        
        # Verify response structure
        required_fields = ['contract', 'assignments', 'total_devices']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ AMC assigned devices response missing field '{field}'")
                return False
        
        # Test 2: Assign single device to AMC contract
        assignment_data = {
            "amc_contract_id": contract_id,
            "device_id": device_id,
            "coverage_start": "2026-01-01",
            "coverage_end": "2027-01-01"
        }
        
        success, response = self.run_test("Assign Device to AMC", "POST", f"admin/amc-contracts/{contract_id}/assign-device", 200, assignment_data)
        if not success:
            return False
        
        # Verify assignment response
        required_fields = ['id', 'amc_contract_id', 'device_id', 'coverage_start', 'coverage_end']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ Device assignment response missing field '{field}'")
                return False
        
        # Test 3: Get assigned devices again (should have 1 device now)
        success, response = self.run_test("Get AMC Assigned Devices After Assignment", "GET", f"admin/amc-contracts/{contract_id}/devices", 200)
        if not success:
            return False
        
        if response.get('total_devices') != 1:
            self.log(f"❌ Expected 1 assigned device, got {response.get('total_devices')}")
            return False
        
        # Verify assignment includes device details
        assignments = response.get('assignments', [])
        if len(assignments) > 0:
            assignment = assignments[0]
            device_fields = ['device_brand', 'device_model', 'device_serial', 'device_type']
            for field in device_fields:
                if field not in assignment:
                    self.log(f"❌ Assignment missing device field '{field}'")
                    return False
        
        # Test 4: Preview bulk assignment
        # Create additional test device for bulk assignment
        device_data = {
            "company_id": self.test_data['company_id'],
            "device_type": "Desktop",
            "brand": "HP",
            "model": "EliteDesk 800",
            "serial_number": f"HP{datetime.now().strftime('%Y%m%d%H%M%S')}BULK",
            "asset_tag": f"BULK{datetime.now().strftime('%H%M%S')}",
            "purchase_date": "2024-01-15",
            "warranty_end_date": "2027-01-15",
            "status": "active"
        }
        
        success, device_response = self.run_test("Create Device for Bulk Assignment", "POST", "admin/devices", 200, device_data)
        if not success:
            return False
        
        bulk_device_id = device_response.get('id')
        bulk_serial = device_data['serial_number']
        
        # Preview bulk assignment
        bulk_preview_data = {
            "amc_contract_id": contract_id,
            "device_identifiers": [bulk_serial, "NONEXISTENT123"],
            "coverage_start": "2026-01-01",
            "coverage_end": "2027-01-01"
        }
        
        success, response = self.run_test("Preview Bulk AMC Assignment", "POST", f"admin/amc-contracts/{contract_id}/bulk-assign/preview", 200, bulk_preview_data)
        if not success:
            return False
        
        # Verify preview response structure
        required_fields = ['will_be_assigned', 'already_assigned', 'not_found', 'wrong_company', 'summary']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ Bulk assignment preview missing field '{field}'")
                return False
        
        # Verify summary structure
        summary = response.get('summary', {})
        summary_fields = ['total_input', 'will_assign', 'already_assigned', 'not_found', 'wrong_company']
        for field in summary_fields:
            if field not in summary:
                self.log(f"❌ Bulk assignment summary missing field '{field}'")
                return False
        
        # Should have 1 device to assign and 1 not found
        if summary.get('will_assign') != 1:
            self.log(f"❌ Expected 1 device to assign, got {summary.get('will_assign')}")
            return False
        
        if summary.get('not_found') != 1:
            self.log(f"❌ Expected 1 device not found, got {summary.get('not_found')}")
            return False
        
        # Test 5: Confirm bulk assignment
        success, response = self.run_test("Confirm Bulk AMC Assignment", "POST", f"admin/amc-contracts/{contract_id}/bulk-assign/confirm", 200, bulk_preview_data)
        if not success:
            return False
        
        # Verify bulk assignment response
        required_fields = ['assigned_count', 'assignments', 'skipped']
        for field in required_fields:
            if field not in response:
                self.log(f"❌ Bulk assignment confirmation missing field '{field}'")
                return False
        
        if response.get('assigned_count') != 1:
            self.log(f"❌ Expected 1 device assigned, got {response.get('assigned_count')}")
            return False
        
        # Test 6: Verify total assigned devices is now 2
        success, response = self.run_test("Get AMC Assigned Devices Final Check", "GET", f"admin/amc-contracts/{contract_id}/devices", 200)
        if not success:
            return False
        
        if response.get('total_devices') != 2:
            self.log(f"❌ Expected 2 total assigned devices, got {response.get('total_devices')}")
            return False
        
        self.log("✅ All AMC Device Assignment APIs working correctly")
        return True

    def test_p0_critical_architecture_fixes(self):
        """Test P0 Critical Architecture Fixes for AMC Status and Warranty Override"""
        self.log("\n=== Testing P0 Critical Architecture Fixes ===")
        
        # Ensure we have demo admin credentials
        if not self.token:
            self.log("❌ No authentication token available")
            return False
        
        # Store test device serial for later use
        test_device_serial = None
        
        # Test 1: Device List API with AMC Status
        self.log("🔍 Testing Device List API with AMC Status...")
        success, response = self.run_test("Device List with AMC Status", "GET", "admin/devices?limit=5", 200)
        if not success:
            return False
        
        # Verify each device has AMC status fields
        if not isinstance(response, list) or len(response) == 0:
            self.log("❌ Device list should return an array with devices")
            return False
        
        for device in response:
            required_fields = ['amc_status', 'company_name', 'label']
            for field in required_fields:
                if field not in device:
                    self.log(f"❌ Device missing required field '{field}'")
                    return False
            
            # Check AMC status values
            if device['amc_status'] not in ['active', 'none', 'expired']:
                self.log(f"❌ Invalid amc_status value: {device['amc_status']}")
                return False
            
            # Store a device serial for later tests
            if not test_device_serial and device.get('serial_number'):
                test_device_serial = device['serial_number']
        
        self.log("✅ Device List API includes AMC status correctly")
        
        # Test 2: Device Detail API with Full AMC Info
        if test_device_serial:
            # Get device ID first
            device_id = None
            for device in response:
                if device.get('serial_number') == test_device_serial:
                    device_id = device.get('id')
                    break
            
            if device_id:
                self.log("🔍 Testing Device Detail API with Full AMC Info...")
                success, device_detail = self.run_test("Device Detail with AMC Info", "GET", f"admin/devices/{device_id}", 200)
                if not success:
                    return False
                
                # Verify device detail includes AMC fields
                required_fields = ['amc_status']
                for field in required_fields:
                    if field not in device_detail:
                        self.log(f"❌ Device detail missing field '{field}'")
                        return False
                
                # Check if device has AMC assignments
                if 'amc_assignments' in device_detail:
                    assignments = device_detail['amc_assignments']
                    if isinstance(assignments, list) and len(assignments) > 0:
                        # Verify assignment structure
                        assignment = assignments[0]
                        assignment_fields = ['amc_contract_id', 'coverage_start', 'coverage_end']
                        for field in assignment_fields:
                            if field not in assignment:
                                self.log(f"❌ AMC assignment missing field '{field}'")
                                return False
                
                self.log("✅ Device Detail API includes full AMC info correctly")
        
        # Test 3: AMC Contracts Search by Serial Number
        if test_device_serial:
            self.log("🔍 Testing AMC Contracts Search by Serial Number...")
            success, amc_response = self.run_test("AMC Contracts Search by Serial", "GET", f"admin/amc-contracts?serial={test_device_serial}", 200)
            if not success:
                return False
            
            # Response should be a list (may be empty if no AMC assigned)
            if not isinstance(amc_response, list):
                self.log("❌ AMC contracts search should return an array")
                return False
            
            self.log("✅ AMC Contracts Search by Serial Number working correctly")
        
        # Test 4: Warranty Search with AMC Override Rule
        if test_device_serial:
            self.log("🔍 Testing Warranty Search with AMC Override Rule...")
            success, warranty_response = self.run_test("Warranty Search with AMC Override", "GET", f"warranty/search?q={test_device_serial}", 200)
            if not success:
                return False
            
            # Verify warranty response structure
            required_fields = ['device', 'coverage_source']
            for field in required_fields:
                if field not in warranty_response:
                    self.log(f"❌ Warranty search response missing field '{field}'")
                    return False
            
            # Verify device object has warranty fields
            device_obj = warranty_response.get('device', {})
            device_fields = ['warranty_active', 'device_warranty_active']
            for field in device_fields:
                if field not in device_obj:
                    self.log(f"❌ Warranty search device object missing field '{field}'")
                    return False
            
            # Check coverage source
            coverage_source = warranty_response.get('coverage_source')
            if coverage_source not in ['amc_contract', 'legacy_amc', 'device_warranty']:
                self.log(f"❌ Invalid coverage_source: {coverage_source}")
                return False
            
            # If AMC contract is active, verify amc_contract object
            if coverage_source == 'amc_contract':
                amc_contract = warranty_response.get('amc_contract')
                if not amc_contract:
                    self.log("❌ Missing amc_contract object when coverage_source is amc_contract")
                    return False
                
                amc_fields = ['name', 'amc_type', 'coverage_start', 'coverage_end', 'active']
                for field in amc_fields:
                    if field not in amc_contract:
                        self.log(f"❌ AMC contract object missing field '{field}'")
                        return False
                
                if not amc_contract.get('active'):
                    self.log("❌ AMC contract should be active when used as coverage source")
                    return False
            
            self.log("✅ Warranty Search with AMC Override Rule working correctly")
        
        # Test 5: Test AMC Filter on Devices
        self.log("🔍 Testing AMC Filter on Devices...")
        
        # Test active AMC filter
        success, active_amc_devices = self.run_test("Filter Devices with Active AMC", "GET", "admin/devices?amc_status=active", 200)
        if not success:
            return False
        
        if not isinstance(active_amc_devices, list):
            self.log("❌ AMC filter should return an array")
            return False
        
        # Verify all returned devices have active AMC
        for device in active_amc_devices:
            if device.get('amc_status') != 'active':
                self.log(f"❌ Device with amc_status={device.get('amc_status')} returned in active AMC filter")
                return False
        
        # Test no AMC filter
        success, no_amc_devices = self.run_test("Filter Devices with No AMC", "GET", "admin/devices?amc_status=none", 200)
        if not success:
            return False
        
        if not isinstance(no_amc_devices, list):
            self.log("❌ AMC filter should return an array")
            return False
        
        # Verify all returned devices have no AMC
        for device in no_amc_devices:
            if device.get('amc_status') != 'none':
                self.log(f"❌ Device with amc_status={device.get('amc_status')} returned in no AMC filter")
                return False
        
        self.log("✅ AMC Filter on Devices working correctly")
        
        # Test 6: Verify AMC Override Logic
        self.log("🔍 Testing AMC Override Logic...")
        
        # Find a device with expired warranty but active AMC (if any)
        all_devices_success, all_devices = self.run_test("Get All Devices for Override Test", "GET", "admin/devices", 200)
        if all_devices_success:
            for device in all_devices:
                if device.get('amc_status') == 'active':
                    device_serial = device.get('serial_number')
                    if device_serial:
                        # Test warranty search for this device
                        success, override_test = self.run_test("Test AMC Override Logic", "GET", f"warranty/search?q={device_serial}", 200)
                        if success:
                            device_obj = override_test.get('device', {})
                            warranty_active = device_obj.get('warranty_active')
                            device_warranty_active = device_obj.get('device_warranty_active')
                            coverage_source = override_test.get('coverage_source')
                            
                            # If AMC is active, warranty_active should be True regardless of device warranty
                            if coverage_source == 'amc_contract' and not warranty_active:
                                self.log("❌ AMC Override Logic failed: warranty_active should be True when AMC is active")
                                return False
                            
                            self.log("✅ AMC Override Logic working correctly")
                            break
        
        self.log("✅ All P0 Critical Architecture Fixes tests passed")
        return True

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Warranty Portal API Tests")
        self.log(f"Base URL: {self.base_url}")
        
        test_results = []
        
        # Run tests in order
        tests = [
            ("Basic Endpoints", self.test_basic_endpoints),
            ("Demo Admin Login", self.test_admin_login_with_demo_credentials),
            ("P0 Critical Architecture Fixes", self.test_p0_critical_architecture_fixes),
            ("Master Data CRUD", self.test_master_data_crud),
            ("Company CRUD", self.test_company_crud),
            ("User CRUD", self.test_user_crud),
            ("Device CRUD", self.test_device_crud),
            ("Sites CRUD", self.test_sites_crud),
            ("Deployments CRUD", self.test_deployments_crud),
            ("Device Auto-Creation from Deployment", self.test_device_auto_creation_from_deployment),
            ("Service History CRUD", self.test_service_history_crud),
            ("Parts CRUD", self.test_parts_crud),
            ("AMC CRUD", self.test_amc_crud),
            ("AMC Contracts v2 CRUD", self.test_amc_contracts_v2_crud),
            ("AMC Coverage Check", self.test_amc_coverage_check),
            ("Companies Without AMC", self.test_companies_without_amc),
            ("License CRUD APIs (Phase 2B)", self.test_license_crud_apis),
            ("AMC Device Assignment APIs (Phase 2B)", self.test_amc_device_assignment_apis),
            ("Device Timeline", self.test_device_timeline),
            ("Warranty Search", self.test_warranty_search),
            ("PDF Generation", self.test_pdf_generation),
            ("Dashboard Stats", self.test_dashboard_stats),
            ("Dashboard Alerts", self.test_dashboard_alerts),
            ("Dashboard Alerts with AMC Contracts", self.test_dashboard_alerts_with_amc_contracts),
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