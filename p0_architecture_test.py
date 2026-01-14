#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta

class P0ArchitectureFixesTester:
    def __init__(self, base_url="https://track-warranty.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.issues_found = []

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def log_issue(self, issue):
        self.issues_found.append(issue)
        self.log(f"❌ ISSUE: {issue}")

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

    def authenticate(self):
        """Authenticate with demo admin credentials"""
        self.log("🔐 Authenticating with demo admin credentials...")
        
        login_data = {
            "email": "admin@demo.com",
            "password": "admin123"
        }
        
        success, response = self.run_test("Demo Admin Login", "POST", "auth/login", 200, login_data)
        if not success:
            return False
        
        self.token = response.get('access_token')
        if not self.token:
            self.log("❌ No access token received")
            return False
        
        self.log("✅ Authentication successful")
        return True

    def test_device_list_api_with_amc_status(self):
        """Test 1: Device List API with AMC Status"""
        self.log("\n=== Test 1: Device List API with AMC Status ===")
        
        success, response = self.run_test("Device List with AMC Status", "GET", "admin/devices?limit=5", 200)
        if not success:
            return False
        
        if not isinstance(response, list):
            self.log_issue("Device list should return an array")
            return False
        
        if len(response) == 0:
            self.log_issue("No devices found in the system")
            return False
        
        # Check each device for required AMC fields
        for i, device in enumerate(response):
            device_id = device.get('id', f'device_{i}')
            
            # Required fields from review request
            required_fields = ['amc_status', 'company_name', 'label']
            for field in required_fields:
                if field not in device:
                    self.log_issue(f"Device {device_id} missing required field '{field}'")
                    return False
            
            # Validate amc_status values
            amc_status = device.get('amc_status')
            if amc_status not in ['active', 'none', 'expired']:
                self.log_issue(f"Device {device_id} has invalid amc_status: {amc_status}")
                return False
            
            # Optional fields that should be present if AMC is assigned
            if amc_status == 'active':
                optional_fields = ['amc_contract_name', 'amc_coverage_end']
                for field in optional_fields:
                    if field not in device:
                        self.log(f"⚠️  Device {device_id} with active AMC missing optional field '{field}'")
        
        self.log("✅ Device List API with AMC Status - All checks passed")
        return True

    def test_device_detail_api_with_full_amc_info(self):
        """Test 2: Device Detail API with Full AMC Info"""
        self.log("\n=== Test 2: Device Detail API with Full AMC Info ===")
        
        # First get a device ID
        success, devices = self.run_test("Get Devices for Detail Test", "GET", "admin/devices?limit=1", 200)
        if not success or not devices:
            self.log_issue("Could not get devices for detail test")
            return False
        
        device_id = devices[0].get('id')
        if not device_id:
            self.log_issue("Device missing ID field")
            return False
        
        # Get device details
        success, device_detail = self.run_test("Device Detail with AMC Info", "GET", f"admin/devices/{device_id}", 200)
        if not success:
            return False
        
        # Required fields from review request
        required_fields = ['amc_status']
        for field in required_fields:
            if field not in device_detail:
                self.log_issue(f"Device detail missing required field '{field}'")
                return False
        
        # Check for AMC assignments array
        if 'amc_assignments' in device_detail:
            assignments = device_detail['amc_assignments']
            if isinstance(assignments, list) and len(assignments) > 0:
                # Verify assignment structure
                assignment = assignments[0]
                assignment_fields = ['amc_contract_id', 'coverage_start', 'coverage_end']
                for field in assignment_fields:
                    if field not in assignment:
                        self.log_issue(f"AMC assignment missing field '{field}'")
                        return False
                self.log("✅ AMC assignments array structure is valid")
        
        # Check for active_amc object if device has active AMC
        if device_detail.get('amc_status') == 'active':
            if 'active_amc' in device_detail:
                active_amc = device_detail['active_amc']
                if isinstance(active_amc, dict):
                    self.log("✅ active_amc object present for device with active AMC")
                else:
                    self.log("⚠️  active_amc should be an object")
            else:
                self.log("⚠️  Device with active AMC missing active_amc object")
        
        # Check for parts array
        if 'parts' not in device_detail:
            self.log_issue("Device detail missing parts array")
            return False
        
        self.log("✅ Device Detail API with Full AMC Info - All checks passed")
        return True

    def test_amc_contracts_search_by_serial(self):
        """Test 3: AMC Contracts Search by Serial Number"""
        self.log("\n=== Test 3: AMC Contracts Search by Serial Number ===")
        
        # First get a device serial number
        success, devices = self.run_test("Get Devices for Serial Search", "GET", "admin/devices?limit=5", 200)
        if not success or not devices:
            self.log_issue("Could not get devices for serial search test")
            return False
        
        test_serial = None
        for device in devices:
            if device.get('serial_number'):
                test_serial = device['serial_number']
                break
        
        if not test_serial:
            self.log_issue("No device with serial number found")
            return False
        
        # Search AMC contracts by serial number
        success, amc_contracts = self.run_test("AMC Contracts Search by Serial", "GET", f"admin/amc-contracts?serial={test_serial}", 200)
        if not success:
            return False
        
        # Response should be an array (may be empty if no AMC assigned)
        if not isinstance(amc_contracts, list):
            self.log_issue("AMC contracts search should return an array")
            return False
        
        # If contracts found, verify structure
        if len(amc_contracts) > 0:
            contract = amc_contracts[0]
            required_fields = ['id', 'name', 'amc_type', 'start_date', 'end_date']
            for field in required_fields:
                if field not in contract:
                    self.log_issue(f"AMC contract missing field '{field}'")
                    return False
            self.log(f"✅ Found {len(amc_contracts)} AMC contract(s) for serial {test_serial}")
        else:
            self.log(f"ℹ️  No AMC contracts found for serial {test_serial} (this is OK)")
        
        self.log("✅ AMC Contracts Search by Serial Number - All checks passed")
        return True

    def test_warranty_search_with_amc_override(self):
        """Test 4: Warranty Search with AMC Override Rule"""
        self.log("\n=== Test 4: Warranty Search with AMC Override Rule ===")
        
        # Get a device serial number
        success, devices = self.run_test("Get Devices for Warranty Search", "GET", "admin/devices?limit=5", 200)
        if not success or not devices:
            self.log_issue("Could not get devices for warranty search test")
            return False
        
        test_serial = None
        for device in devices:
            if device.get('serial_number'):
                test_serial = device['serial_number']
                break
        
        if not test_serial:
            self.log_issue("No device with serial number found")
            return False
        
        # Test warranty search
        success, warranty_response = self.run_test("Warranty Search with AMC Override", "GET", f"warranty/search?q={test_serial}", 200)
        if not success:
            return False
        
        # Verify required fields from review request
        required_fields = ['device', 'coverage_source']
        for field in required_fields:
            if field not in warranty_response:
                self.log_issue(f"Warranty search response missing field '{field}'")
                return False
        
        # Verify device object structure
        device_obj = warranty_response.get('device', {})
        device_fields = ['warranty_active', 'device_warranty_active']
        for field in device_fields:
            if field not in device_obj:
                self.log_issue(f"Warranty search device object missing field '{field}'")
                return False
        
        # Verify coverage_source values
        coverage_source = warranty_response.get('coverage_source')
        valid_sources = ['amc_contract', 'legacy_amc', 'device_warranty']
        if coverage_source not in valid_sources:
            self.log_issue(f"Invalid coverage_source: {coverage_source}. Expected one of {valid_sources}")
            return False
        
        # If AMC contract is the source, verify amc_contract object
        if coverage_source == 'amc_contract':
            amc_contract = warranty_response.get('amc_contract')
            if not amc_contract:
                self.log_issue("Missing amc_contract object when coverage_source is amc_contract")
                return False
            
            amc_fields = ['name', 'amc_type', 'coverage_start', 'coverage_end', 'active']
            for field in amc_fields:
                if field not in amc_contract:
                    self.log_issue(f"AMC contract object missing field '{field}'")
                    return False
            
            if not amc_contract.get('active'):
                self.log_issue("AMC contract should be active when used as coverage source")
                return False
            
            self.log("✅ AMC contract object structure is valid")
        
        self.log(f"✅ Warranty search for {test_serial}: coverage_source={coverage_source}")
        self.log("✅ Warranty Search with AMC Override Rule - All checks passed")
        return True

    def test_amc_override_logic(self):
        """Test 5: Test AMC Override Logic"""
        self.log("\n=== Test 5: Test AMC Override Logic ===")
        
        # Get all devices to find one with active AMC
        success, devices = self.run_test("Get All Devices for Override Test", "GET", "admin/devices", 200)
        if not success:
            return False
        
        amc_device_found = False
        for device in devices:
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
                        
                        # AMC Override Rule: If AMC is active, warranty_active should be True
                        if coverage_source == 'amc_contract':
                            if not warranty_active:
                                self.log_issue(f"AMC Override Logic failed for {device_serial}: warranty_active should be True when AMC is active")
                                return False
                            
                            self.log(f"✅ AMC Override working for {device_serial}: warranty_active={warranty_active}, device_warranty_active={device_warranty_active}")
                            amc_device_found = True
                            break
        
        if not amc_device_found:
            self.log("ℹ️  No devices with active AMC found to test override logic")
        
        self.log("✅ AMC Override Logic - All checks passed")
        return True

    def test_amc_filter_on_devices(self):
        """Test 6: Test AMC Filter on Devices"""
        self.log("\n=== Test 6: Test AMC Filter on Devices ===")
        
        # Test active AMC filter
        success, active_amc_devices = self.run_test("Filter Devices with Active AMC", "GET", "admin/devices?amc_status=active", 200)
        if not success:
            return False
        
        if not isinstance(active_amc_devices, list):
            self.log_issue("AMC filter should return an array")
            return False
        
        # Verify all returned devices have active AMC
        for device in active_amc_devices:
            if device.get('amc_status') != 'active':
                self.log_issue(f"Device with amc_status={device.get('amc_status')} returned in active AMC filter")
                return False
        
        self.log(f"✅ Active AMC filter returned {len(active_amc_devices)} devices")
        
        # Test no AMC filter
        success, no_amc_devices = self.run_test("Filter Devices with No AMC", "GET", "admin/devices?amc_status=none", 200)
        if not success:
            return False
        
        if not isinstance(no_amc_devices, list):
            self.log_issue("AMC filter should return an array")
            return False
        
        # Verify all returned devices have no AMC
        for device in no_amc_devices:
            if device.get('amc_status') != 'none':
                self.log_issue(f"Device with amc_status={device.get('amc_status')} returned in no AMC filter")
                return False
        
        self.log(f"✅ No AMC filter returned {len(no_amc_devices)} devices")
        
        # Test expired AMC filter
        success, expired_amc_devices = self.run_test("Filter Devices with Expired AMC", "GET", "admin/devices?amc_status=expired", 200)
        if not success:
            return False
        
        self.log(f"✅ Expired AMC filter returned {len(expired_amc_devices)} devices")
        
        self.log("✅ AMC Filter on Devices - All checks passed")
        return True

    def run_all_tests(self):
        """Run all P0 Critical Architecture Fixes tests"""
        self.log("🚀 Starting P0 Critical Architecture Fixes Tests")
        self.log(f"Base URL: {self.base_url}")
        
        # Authenticate first
        if not self.authenticate():
            self.log("❌ Authentication failed - cannot proceed with tests")
            return False
        
        test_results = []
        
        # Run all tests
        tests = [
            ("Device List API with AMC Status", self.test_device_list_api_with_amc_status),
            ("Device Detail API with Full AMC Info", self.test_device_detail_api_with_full_amc_info),
            ("AMC Contracts Search by Serial Number", self.test_amc_contracts_search_by_serial),
            ("Warranty Search with AMC Override Rule", self.test_warranty_search_with_amc_override),
            ("AMC Override Logic", self.test_amc_override_logic),
            ("AMC Filter on Devices", self.test_amc_filter_on_devices)
        ]
        
        for test_name, test_func in tests:
            try:
                result = test_func()
                test_results.append((test_name, result))
                if not result:
                    self.log(f"⚠️  {test_name} failed")
            except Exception as e:
                self.log(f"💥 {test_name} crashed: {str(e)}")
                test_results.append((test_name, False))
        
        # Print summary
        self.log(f"\n📊 Test Summary:")
        self.log(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        self.log(f"Success rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        self.log(f"\n📋 Test Results:")
        for test_name, result in test_results:
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"  {status} - {test_name}")
        
        # Print issues found
        if self.issues_found:
            self.log(f"\n🚨 Issues Found ({len(self.issues_found)}):")
            for i, issue in enumerate(self.issues_found, 1):
                self.log(f"  {i}. {issue}")
        else:
            self.log(f"\n🎉 No critical issues found!")
        
        return len(self.issues_found) == 0

def main():
    tester = P0ArchitectureFixesTester()
    success = tester.run_all_tests()
    
    # Return appropriate exit code
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())