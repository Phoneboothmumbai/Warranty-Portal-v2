#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class AdminFeaturesTester:
    def __init__(self, base_url="https://ticket-system-82.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {}

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

    def test_admin_login(self):
        """Test admin login with demo credentials"""
        self.log("\n=== Testing Admin Login Flow ===")
        
        # Login with demo credentials
        login_data = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        success, response = self.run_test("Admin Login", "POST", "auth/login", 200, login_data)
        if not success:
            return False
        
        self.token = response.get('access_token')
        if not self.token:
            self.log("❌ No access token received")
            return False
        
        # Test auth/me endpoint
        success, response = self.run_test("Get Admin Info", "GET", "auth/me", 200)
        if success:
            self.log(f"✅ Logged in as: {response.get('name')} ({response.get('email')})")
        
        return success

    def test_master_data_management(self):
        """Test Master Data Management features"""
        self.log("\n=== Testing Master Data Management ===")
        
        # Test getting different master data types
        master_types = ['device_type', 'part_type', 'service_type', 'condition', 'brand']
        
        for master_type in master_types:
            success, response = self.run_test(
                f"Get {master_type.replace('_', ' ').title()}s", 
                "GET", 
                f"admin/masters?master_type={master_type}", 
                200
            )
            if not success:
                return False
            
            # Verify we have some default data
            if len(response) == 0:
                self.log(f"⚠️  No {master_type} items found")
        
        # Test adding a new brand (Samsung Test)
        brand_data = {
            "type": "brand",
            "name": f"Samsung Test {datetime.now().strftime('%H%M%S')}",
            "code": f"SAMSUNG_TEST_{datetime.now().strftime('%H%M%S')}",
            "description": "Test brand for admin features",
            "is_active": True,
            "sort_order": 50
        }
        
        success, response = self.run_test("Add New Brand", "POST", "admin/masters", 200, brand_data)
        if not success:
            return False
        
        brand_id = response.get('id')
        self.test_data['brand_id'] = brand_id
        
        # Test editing the brand
        update_data = {
            "description": "Updated Samsung test brand",
            "sort_order": 60
        }
        
        success, _ = self.run_test("Edit Brand", "PUT", f"admin/masters/{brand_id}", 200, update_data)
        if not success:
            return False
        
        # Test disabling the brand
        success, _ = self.run_test("Disable Brand", "DELETE", f"admin/masters/{brand_id}", 200)
        
        return success

    def test_service_history_features(self):
        """Test Service History features"""
        self.log("\n=== Testing Service History Features ===")
        
        # First, we need a device to create service history for
        # Create a company first
        company_data = {
            "name": f"Test Company {datetime.now().strftime('%H%M%S')}",
            "contact_name": "John Doe",
            "contact_email": "john@testcompany.com",
            "contact_phone": "+91-9876543210"
        }
        
        success, response = self.run_test("Create Company", "POST", "admin/companies", 200, company_data)
        if not success:
            return False
        
        company_id = response.get('id')
        
        # Create a device
        device_data = {
            "company_id": company_id,
            "device_type": "Laptop",
            "brand": "Dell",
            "model": "Latitude 5520",
            "serial_number": f"DL{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "purchase_date": "2024-01-15",
            "warranty_end_date": "2027-01-15",
            "status": "active"
        }
        
        success, response = self.run_test("Create Device", "POST", "admin/devices", 200, device_data)
        if not success:
            return False
        
        device_id = response.get('id')
        
        # Test adding a new service record
        service_data = {
            "device_id": device_id,
            "service_date": "2024-12-15",
            "service_type": "repair",
            "problem_reported": "Device not booting properly",
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
        
        success, response = self.run_test("Add Service Record", "POST", "admin/services", 200, service_data)
        if not success:
            return False
        
        service_id = response.get('id')
        
        # Test filtering by device
        success, response = self.run_test("Filter Services by Device", "GET", f"admin/services?device_id={device_id}", 200)
        if not success:
            return False
        
        # Verify we get the service we just created
        if len(response) == 0:
            self.log("❌ No services found for device")
            return False
        
        # Test timeline view
        success, response = self.run_test("Device Timeline", "GET", f"admin/devices/{device_id}/timeline", 200)
        if not success:
            return False
        
        # Verify timeline has entries
        if len(response) == 0:
            self.log("❌ No timeline entries found")
            return False
        
        self.log(f"✅ Timeline has {len(response)} entries")
        
        return True

    def test_dashboard_with_alerts(self):
        """Test Dashboard with Alerts"""
        self.log("\n=== Testing Dashboard with Alerts ===")
        
        # Test dashboard stats
        success, response = self.run_test("Dashboard Stats", "GET", "admin/dashboard", 200)
        if not success:
            return False
        
        # Verify stats structure
        required_stats = ['companies_count', 'users_count', 'devices_count', 'parts_count', 'services_count', 'active_warranties', 'active_amc']
        for stat in required_stats:
            if stat not in response:
                self.log(f"❌ Missing stat: {stat}")
                return False
        
        self.log(f"✅ Dashboard stats: {response['devices_count']} devices, {response['companies_count']} companies, {response['services_count']} services")
        
        # Test alerts section
        success, response = self.run_test("Dashboard Alerts", "GET", "admin/dashboard/alerts", 200)
        if not success:
            return False
        
        # Verify alerts structure
        required_alerts = ['warranty_expiring_7_days', 'warranty_expiring_15_days', 'warranty_expiring_30_days', 'amc_expiring_7_days', 'devices_in_repair']
        for alert in required_alerts:
            if alert not in response:
                self.log(f"❌ Missing alert type: {alert}")
                return False
        
        self.log("✅ All alert types present in response")
        
        return True

    def test_devices_with_master_data(self):
        """Test Devices page with Master Data integration"""
        self.log("\n=== Testing Devices with Master Data Integration ===")
        
        # Test getting devices list
        success, response = self.run_test("List Devices", "GET", "admin/devices", 200)
        if not success:
            return False
        
        # Test filtering by company (if we have devices)
        if len(response) > 0:
            device = response[0]
            company_id = device.get('company_id')
            if company_id:
                success, filtered_response = self.run_test("Filter Devices by Company", "GET", f"admin/devices?company_id={company_id}", 200)
                if not success:
                    return False
        
        # Test filtering by status
        success, _ = self.run_test("Filter Devices by Status", "GET", "admin/devices?status=active", 200)
        if not success:
            return False
        
        # Test that master data is available for device creation
        success, masters = self.run_test("Get Device Types for Dropdown", "GET", "admin/masters?master_type=device_type", 200)
        if not success:
            return False
        
        if len(masters) == 0:
            self.log("❌ No device types available for dropdown")
            return False
        
        success, brands = self.run_test("Get Brands for Dropdown", "GET", "admin/masters?master_type=brand", 200)
        if not success:
            return False
        
        if len(brands) == 0:
            self.log("❌ No brands available for dropdown")
            return False
        
        self.log(f"✅ Master data available: {len(masters)} device types, {len(brands)} brands")
        
        return True

    def run_admin_features_test(self):
        """Run all admin features tests"""
        self.log("🚀 Starting Admin Features Test")
        self.log(f"Base URL: {self.base_url}")
        
        test_results = []
        
        # Run tests in order
        tests = [
            ("Admin Login Flow", self.test_admin_login),
            ("Master Data Management", self.test_master_data_management),
            ("Service History Features", self.test_service_history_features),
            ("Dashboard with Alerts", self.test_dashboard_with_alerts),
            ("Devices with Master Data", self.test_devices_with_master_data)
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
        self.log(f"\n📊 Admin Features Test Summary:")
        self.log(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        self.log(f"\n📋 Test Results:")
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {status} - {test_name}")
        
        return self.tests_passed, self.tests_run, test_results

def main():
    tester = AdminFeaturesTester()
    passed, total, results = tester.run_admin_features_test()
    
    # Return appropriate exit code
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())