#!/usr/bin/env python3

import requests
import json
from datetime import datetime

class AMCContractsV2Tester:
    def __init__(self, base_url="https://warranty-tracker-23.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.token = None
        self.test_data = {}

    def log(self, message):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")

    def login(self):
        """Login with demo admin credentials"""
        login_data = {"email": "admin@demo.com", "password": "admin123"}
        response = requests.post(f"{self.base_url}/auth/login", json=login_data)
        if response.status_code == 200:
            self.token = response.json()['access_token']
            self.log("✅ Successfully logged in with demo admin credentials")
            return True
        else:
            self.log(f"❌ Login failed: {response.status_code}")
            return False

    def get_headers(self):
        return {'Authorization': f'Bearer {self.token}', 'Content-Type': 'application/json'}

    def test_amc_contracts_list(self):
        """Test GET /api/admin/amc-contracts"""
        self.log("\n🔍 Testing GET /api/admin/amc-contracts")
        response = requests.get(f"{self.base_url}/admin/amc-contracts", headers=self.get_headers())
        
        if response.status_code == 200:
            contracts = response.json()
            self.log(f"✅ List AMC Contracts - Found {len(contracts)} contracts")
            
            # Verify structure
            if contracts:
                contract = contracts[0]
                required_fields = ['id', 'company_id', 'name', 'amc_type', 'start_date', 'end_date', 'status', 'company_name']
                missing_fields = [f for f in required_fields if f not in contract]
                if missing_fields:
                    self.log(f"❌ Missing fields in contract: {missing_fields}")
                    return False
                else:
                    self.log("✅ Contract structure is valid")
            return True
        else:
            self.log(f"❌ List AMC Contracts failed: {response.status_code}")
            return False

    def test_create_amc_contract(self):
        """Test POST /api/admin/amc-contracts"""
        self.log("\n🔍 Testing POST /api/admin/amc-contracts")
        
        # Get a company ID first
        companies_response = requests.get(f"{self.base_url}/admin/companies", headers=self.get_headers())
        if companies_response.status_code != 200:
            self.log("❌ Failed to get companies for contract creation")
            return False
        
        companies = companies_response.json()
        if not companies:
            self.log("❌ No companies available for contract creation")
            return False
        
        company_id = companies[0]['id']
        self.test_data['company_id'] = company_id
        
        # Create contract as specified in review request
        contract_data = {
            "company_id": company_id,
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
        
        response = requests.post(f"{self.base_url}/admin/amc-contracts", json=contract_data, headers=self.get_headers())
        
        if response.status_code == 200:
            contract = response.json()
            self.test_data['contract_id'] = contract['id']
            self.log(f"✅ Create AMC Contract - Created contract: {contract['name']}")
            self.log(f"   Contract ID: {contract['id']}")
            self.log(f"   Status: {contract.get('status')}")
            return True
        else:
            self.log(f"❌ Create AMC Contract failed: {response.status_code}")
            try:
                error = response.json().get('detail', 'Unknown error')
                self.log(f"   Error: {error}")
            except:
                self.log(f"   Response: {response.text}")
            return False

    def test_get_amc_contract_details(self):
        """Test GET /api/admin/amc-contracts/{id}"""
        if 'contract_id' not in self.test_data:
            self.log("❌ No contract ID available for details test")
            return False
        
        self.log(f"\n🔍 Testing GET /api/admin/amc-contracts/{self.test_data['contract_id']}")
        response = requests.get(f"{self.base_url}/admin/amc-contracts/{self.test_data['contract_id']}", headers=self.get_headers())
        
        if response.status_code == 200:
            contract = response.json()
            self.log("✅ Get AMC Contract Details - Success")
            
            # Verify covered assets are included
            required_fields = ['covered_assets', 'covered_assets_count', 'usage_history', 'usage_stats']
            missing_fields = [f for f in required_fields if f not in contract]
            if missing_fields:
                self.log(f"❌ Missing fields in contract details: {missing_fields}")
                return False
            
            self.log(f"   Covered Assets: {contract['covered_assets_count']}")
            self.log(f"   Usage History: {len(contract['usage_history'])} records")
            return True
        else:
            self.log(f"❌ Get AMC Contract Details failed: {response.status_code}")
            return False

    def test_update_amc_contract(self):
        """Test PUT /api/admin/amc-contracts/{id}"""
        if 'contract_id' not in self.test_data:
            self.log("❌ No contract ID available for update test")
            return False
        
        self.log(f"\n🔍 Testing PUT /api/admin/amc-contracts/{self.test_data['contract_id']}")
        
        update_data = {
            "name": "Updated Test AMC 2025-26",
            "internal_notes": "Updated via API test"
        }
        
        response = requests.put(f"{self.base_url}/admin/amc-contracts/{self.test_data['contract_id']}", json=update_data, headers=self.get_headers())
        
        if response.status_code == 200:
            contract = response.json()
            self.log("✅ Update AMC Contract - Success")
            self.log(f"   Updated Name: {contract['name']}")
            return True
        else:
            self.log(f"❌ Update AMC Contract failed: {response.status_code}")
            return False

    def test_check_coverage(self):
        """Test GET /api/admin/amc-contracts/check-coverage/{device_id}"""
        self.log("\n🔍 Testing GET /api/admin/amc-contracts/check-coverage/{device_id}")
        
        # Get a device ID
        devices_response = requests.get(f"{self.base_url}/admin/devices", headers=self.get_headers())
        if devices_response.status_code != 200:
            self.log("❌ Failed to get devices for coverage test")
            return False
        
        devices = devices_response.json()
        if not devices:
            self.log("❌ No devices available for coverage test")
            return False
        
        device_id = devices[0]['id']
        response = requests.get(f"{self.base_url}/admin/amc-contracts/check-coverage/{device_id}", headers=self.get_headers())
        
        if response.status_code == 200:
            coverage = response.json()
            self.log("✅ Check AMC Coverage - Success")
            self.log(f"   Device: {coverage['device_info']}")
            self.log(f"   Is Covered: {coverage['is_covered']}")
            self.log(f"   Active Contracts: {len(coverage['active_contracts'])}")
            
            # Verify structure
            required_fields = ['device_id', 'device_info', 'is_covered', 'active_contracts']
            missing_fields = [f for f in required_fields if f not in coverage]
            if missing_fields:
                self.log(f"❌ Missing fields in coverage response: {missing_fields}")
                return False
            
            return True
        else:
            self.log(f"❌ Check AMC Coverage failed: {response.status_code}")
            return False

    def test_companies_without_amc(self):
        """Test GET /api/admin/companies-without-amc"""
        self.log("\n🔍 Testing GET /api/admin/companies-without-amc")
        response = requests.get(f"{self.base_url}/admin/companies-without-amc", headers=self.get_headers())
        
        if response.status_code == 200:
            companies = response.json()
            self.log(f"✅ Companies Without AMC - Found {len(companies)} companies")
            
            # Verify structure if there are companies
            if companies:
                company = companies[0]
                required_fields = ['id', 'name', 'contact_email']
                missing_fields = [f for f in required_fields if f not in company]
                if missing_fields:
                    self.log(f"❌ Missing fields in company: {missing_fields}")
                    return False
            
            return True
        else:
            self.log(f"❌ Companies Without AMC failed: {response.status_code}")
            return False

    def test_dashboard_alerts(self):
        """Test GET /api/admin/dashboard/alerts with AMC contract alerts"""
        self.log("\n🔍 Testing GET /api/admin/dashboard/alerts (AMC contract alerts)")
        response = requests.get(f"{self.base_url}/admin/dashboard/alerts", headers=self.get_headers())
        
        if response.status_code == 200:
            alerts = response.json()
            self.log("✅ Dashboard Alerts - Success")
            
            # Check for AMC contract specific alerts
            amc_contract_fields = [
                'amc_contracts_expiring_7_days',
                'amc_contracts_expiring_15_days', 
                'amc_contracts_expiring_30_days',
                'companies_without_amc'
            ]
            
            missing_fields = [f for f in amc_contract_fields if f not in alerts]
            if missing_fields:
                self.log(f"❌ Missing AMC contract alert fields: {missing_fields}")
                return False
            
            # Log counts
            for field in amc_contract_fields:
                count = len(alerts[field]) if isinstance(alerts[field], list) else 'N/A'
                self.log(f"   {field}: {count}")
            
            return True
        else:
            self.log(f"❌ Dashboard Alerts failed: {response.status_code}")
            return False

    def run_all_tests(self):
        """Run all AMC Contracts v2 tests"""
        self.log("🚀 Starting AMC Contracts v2 API Tests")
        self.log(f"Base URL: {self.base_url}")
        
        if not self.login():
            return False
        
        tests = [
            ("List AMC Contracts", self.test_amc_contracts_list),
            ("Create AMC Contract", self.test_create_amc_contract),
            ("Get AMC Contract Details", self.test_get_amc_contract_details),
            ("Update AMC Contract", self.test_update_amc_contract),
            ("Check AMC Coverage", self.test_check_coverage),
            ("Companies Without AMC", self.test_companies_without_amc),
            ("Dashboard Alerts", self.test_dashboard_alerts)
        ]
        
        passed = 0
        total = len(tests)
        
        for test_name, test_func in tests:
            try:
                if test_func():
                    passed += 1
                    self.log(f"✅ {test_name} - PASSED")
                else:
                    self.log(f"❌ {test_name} - FAILED")
            except Exception as e:
                self.log(f"💥 {test_name} - ERROR: {str(e)}")
        
        self.log(f"\n📊 AMC Contracts v2 Test Summary:")
        self.log(f"Tests passed: {passed}/{total}")
        self.log(f"Success rate: {(passed/total*100):.1f}%")
        
        return passed == total

if __name__ == "__main__":
    tester = AMCContractsV2Tester()
    success = tester.run_all_tests()
    exit(0 if success else 1)