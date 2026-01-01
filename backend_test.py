#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class WarrantyPortalTester:
    def __init__(self, base_url="https://warranty-portal-1.preview.emergentagent.com/api"):
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
            'amc_id': None
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

    def run_all_tests(self):
        """Run all tests in sequence"""
        self.log("🚀 Starting Warranty Portal API Tests")
        self.log(f"Base URL: {self.base_url}")
        
        test_results = []
        
        # Run tests in order
        tests = [
            ("Basic Endpoints", self.test_basic_endpoints),
            ("Admin Setup & Auth", self.test_admin_setup_and_auth),
            ("Company CRUD", self.test_company_crud),
            ("User CRUD", self.test_user_crud),
            ("Device CRUD", self.test_device_crud),
            ("Parts CRUD", self.test_parts_crud),
            ("AMC CRUD", self.test_amc_crud),
            ("Warranty Search", self.test_warranty_search),
            ("PDF Generation", self.test_pdf_generation),
            ("Dashboard Stats", self.test_dashboard_stats),
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