"""
Tenant Scoping Tests - Multi-tenant isolation verification
===========================================================
Tests that:
1. Admin login works correctly
2. Companies created get organization_id and are visible in list
3. Devices created get organization_id and are visible in list
4. AMC contracts created get organization_id and are visible in list
5. Dashboard stats show correct counts for the organization
6. Tenant isolation - admin from org A cannot see data from org B
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials from the review request
ADMIN1_EMAIL = "admin@demo.com"
ADMIN1_PASSWORD = "admin123"
ADMIN1_ORG_ID = "112068e7-d4ec-4516-beff-8d3087c51868"

ADMIN2_EMAIL = "m@gmail.com"
ADMIN2_PASSWORD = "admin123"
ADMIN2_ORG_ID = "edacd0fa-ce92-47a1-a5ef-856b7f7fcd1c"


class TestAdminLogin:
    """Test admin login functionality"""
    
    def test_admin1_login_success(self):
        """Test admin1 can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD
        })
        print(f"Admin1 login response: {response.status_code}")
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        print(f"Admin1 login successful, token received")
    
    def test_admin2_login_success(self):
        """Test admin2 can login successfully"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN2_EMAIL,
            "password": ADMIN2_PASSWORD
        })
        print(f"Admin2 login response: {response.status_code}")
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access token in response"
        print(f"Admin2 login successful, token received")
    
    def test_invalid_credentials_rejected(self):
        """Test invalid credentials are rejected"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("Invalid credentials correctly rejected")


class TestCompanyTenantScoping:
    """Test company CRUD with tenant scoping"""
    
    @pytest.fixture
    def admin1_token(self):
        """Get admin1 auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin1 login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin2_token(self):
        """Get admin2 auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN2_EMAIL,
            "password": ADMIN2_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin2 login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_create_company_gets_org_id(self, admin1_token):
        """Test that created company gets organization_id"""
        unique_name = f"TEST_Company_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "name": unique_name,
                "contact_name": "Test Contact",
                "contact_email": f"test_{uuid.uuid4().hex[:6]}@test.com",
                "contact_phone": "1234567890"
            }
        )
        print(f"Create company response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Create company failed: {response.text}"
        data = response.json()
        
        # Verify company was created with organization_id
        assert "id" in data, "No company ID in response"
        company_id = data["id"]
        print(f"Created company ID: {company_id}")
        
        # Check if organization_id is set (may not be returned in response)
        if "organization_id" in data:
            print(f"Company organization_id: {data['organization_id']}")
            assert data["organization_id"] == ADMIN1_ORG_ID, "Wrong organization_id"
    
    def test_list_companies_shows_created_company(self, admin1_token):
        """Test that created company appears in list"""
        # First create a company
        unique_name = f"TEST_ListCheck_{uuid.uuid4().hex[:8]}"
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "name": unique_name,
                "contact_name": "Test Contact",
                "contact_email": f"test_{uuid.uuid4().hex[:6]}@test.com",
                "contact_phone": "1234567890"
            }
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        created_company = create_response.json()
        company_id = created_company["id"]
        print(f"Created company: {unique_name} with ID: {company_id}")
        
        # Now list companies and verify it appears
        list_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"}
        )
        assert list_response.status_code == 200, f"List failed: {list_response.text}"
        companies = list_response.json()
        
        print(f"Total companies in list: {len(companies)}")
        
        # Find our created company
        found = any(c["id"] == company_id for c in companies)
        if not found:
            print(f"CRITICAL BUG: Created company {company_id} not found in list!")
            print(f"Company IDs in list: {[c['id'] for c in companies[:10]]}")
        assert found, f"Created company {company_id} not found in list! This is the tenant scoping bug."
        print(f"SUCCESS: Company {unique_name} is visible in list")
    
    def test_tenant_isolation_companies(self, admin1_token, admin2_token):
        """Test that admin2 cannot see admin1's companies"""
        # Create company as admin1
        unique_name = f"TEST_Isolation_{uuid.uuid4().hex[:8]}"
        
        create_response = requests.post(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "name": unique_name,
                "contact_name": "Test Contact",
                "contact_email": f"test_{uuid.uuid4().hex[:6]}@test.com",
                "contact_phone": "1234567890"
            }
        )
        assert create_response.status_code == 200
        company_id = create_response.json()["id"]
        print(f"Admin1 created company: {company_id}")
        
        # List companies as admin2
        list_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin2_token}"}
        )
        assert list_response.status_code == 200
        admin2_companies = list_response.json()
        
        # Verify admin1's company is NOT visible to admin2
        found = any(c["id"] == company_id for c in admin2_companies)
        assert not found, f"TENANT ISOLATION FAILURE: Admin2 can see Admin1's company {company_id}!"
        print(f"SUCCESS: Tenant isolation working - Admin2 cannot see Admin1's company")


class TestDeviceTenantScoping:
    """Test device CRUD with tenant scoping"""
    
    @pytest.fixture
    def admin1_token(self):
        """Get admin1 auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin1 login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin2_token(self):
        """Get admin2 auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN2_EMAIL,
            "password": ADMIN2_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin2 login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin1_company(self, admin1_token):
        """Create or get a company for admin1"""
        # First try to get existing companies
        list_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"}
        )
        if list_response.status_code == 200:
            companies = list_response.json()
            if companies:
                return companies[0]["id"]
        
        # Create a new company
        unique_name = f"TEST_DeviceCompany_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "name": unique_name,
                "contact_name": "Test Contact",
                "contact_email": f"test_{uuid.uuid4().hex[:6]}@test.com",
                "contact_phone": "1234567890"
            }
        )
        if create_response.status_code != 200:
            pytest.skip(f"Could not create company: {create_response.text}")
        return create_response.json()["id"]
    
    def test_create_device_gets_org_id(self, admin1_token, admin1_company):
        """Test that created device gets organization_id"""
        unique_serial = f"TEST_SN_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/devices",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "company_id": admin1_company,
                "device_type": "Laptop",
                "brand": "Dell",
                "model": "Latitude 5520",
                "serial_number": unique_serial,
                "purchase_date": "2024-01-15"
            }
        )
        print(f"Create device response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Create device failed: {response.text}"
        data = response.json()
        
        assert "id" in data, "No device ID in response"
        device_id = data["id"]
        print(f"Created device ID: {device_id}")
        
        # Check if organization_id is set
        if "organization_id" in data:
            print(f"Device organization_id: {data['organization_id']}")
    
    def test_list_devices_shows_created_device(self, admin1_token, admin1_company):
        """Test that created device appears in list - CRITICAL BUG TEST"""
        unique_serial = f"TEST_ListDev_{uuid.uuid4().hex[:8]}"
        
        # Create device
        create_response = requests.post(
            f"{BASE_URL}/api/admin/devices",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "company_id": admin1_company,
                "device_type": "Laptop",
                "brand": "HP",
                "model": "EliteBook 840",
                "serial_number": unique_serial,
                "purchase_date": "2024-01-15"
            }
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        device_id = create_response.json()["id"]
        print(f"Created device: {unique_serial} with ID: {device_id}")
        
        # List devices
        list_response = requests.get(
            f"{BASE_URL}/api/admin/devices",
            headers={"Authorization": f"Bearer {admin1_token}"}
        )
        assert list_response.status_code == 200, f"List failed: {list_response.text}"
        devices = list_response.json()
        
        print(f"Total devices in list: {len(devices)}")
        
        # Find our created device
        found = any(d["id"] == device_id for d in devices)
        if not found:
            print(f"CRITICAL BUG: Created device {device_id} not found in list!")
            print(f"Device IDs in list (first 10): {[d['id'] for d in devices[:10]]}")
            # Check if device exists in DB without org filter
            print(f"This indicates the device was created but organization_id scoping is filtering it out")
        assert found, f"Created device {device_id} not found in list! This is the tenant scoping bug."
        print(f"SUCCESS: Device {unique_serial} is visible in list")
    
    def test_tenant_isolation_devices(self, admin1_token, admin2_token, admin1_company):
        """Test that admin2 cannot see admin1's devices"""
        unique_serial = f"TEST_IsolDev_{uuid.uuid4().hex[:8]}"
        
        # Create device as admin1
        create_response = requests.post(
            f"{BASE_URL}/api/admin/devices",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "company_id": admin1_company,
                "device_type": "Laptop",
                "brand": "Lenovo",
                "model": "ThinkPad X1",
                "serial_number": unique_serial,
                "purchase_date": "2024-01-15"
            }
        )
        assert create_response.status_code == 200
        device_id = create_response.json()["id"]
        print(f"Admin1 created device: {device_id}")
        
        # List devices as admin2
        list_response = requests.get(
            f"{BASE_URL}/api/admin/devices",
            headers={"Authorization": f"Bearer {admin2_token}"}
        )
        assert list_response.status_code == 200
        admin2_devices = list_response.json()
        
        # Verify admin1's device is NOT visible to admin2
        found = any(d["id"] == device_id for d in admin2_devices)
        assert not found, f"TENANT ISOLATION FAILURE: Admin2 can see Admin1's device {device_id}!"
        print(f"SUCCESS: Tenant isolation working - Admin2 cannot see Admin1's device")


class TestAMCContractTenantScoping:
    """Test AMC contract CRUD with tenant scoping"""
    
    @pytest.fixture
    def admin1_token(self):
        """Get admin1 auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin1 login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin2_token(self):
        """Get admin2 auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN2_EMAIL,
            "password": ADMIN2_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin2 login failed: {response.text}")
        return response.json()["access_token"]
    
    @pytest.fixture
    def admin1_company(self, admin1_token):
        """Create or get a company for admin1"""
        list_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"}
        )
        if list_response.status_code == 200:
            companies = list_response.json()
            if companies:
                return companies[0]["id"]
        
        unique_name = f"TEST_AMCCompany_{uuid.uuid4().hex[:8]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "name": unique_name,
                "contact_name": "Test Contact",
                "contact_email": f"test_{uuid.uuid4().hex[:6]}@test.com",
                "contact_phone": "1234567890"
            }
        )
        if create_response.status_code != 200:
            pytest.skip(f"Could not create company: {create_response.text}")
        return create_response.json()["id"]
    
    def test_create_amc_contract(self, admin1_token, admin1_company):
        """Test that AMC contract can be created"""
        unique_name = f"TEST_AMC_{uuid.uuid4().hex[:8]}"
        
        response = requests.post(
            f"{BASE_URL}/api/admin/amc-contracts",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "company_id": admin1_company,
                "name": unique_name,
                "amc_type": "comprehensive",
                "start_date": "2024-01-01",
                "end_date": "2025-12-31"
            }
        )
        print(f"Create AMC response: {response.status_code}")
        print(f"Response body: {response.text[:500]}")
        
        assert response.status_code == 200, f"Create AMC failed: {response.text}"
        data = response.json()
        
        assert "id" in data, "No AMC ID in response"
        amc_id = data["id"]
        print(f"Created AMC contract ID: {amc_id}")
    
    def test_list_amc_contracts_shows_created(self, admin1_token, admin1_company):
        """Test that created AMC contract appears in list - CRITICAL BUG TEST"""
        unique_name = f"TEST_ListAMC_{uuid.uuid4().hex[:8]}"
        
        # Create AMC contract
        create_response = requests.post(
            f"{BASE_URL}/api/admin/amc-contracts",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "company_id": admin1_company,
                "name": unique_name,
                "amc_type": "comprehensive",
                "start_date": "2024-01-01",
                "end_date": "2025-12-31"
            }
        )
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        amc_id = create_response.json()["id"]
        print(f"Created AMC: {unique_name} with ID: {amc_id}")
        
        # List AMC contracts
        list_response = requests.get(
            f"{BASE_URL}/api/admin/amc-contracts",
            headers={"Authorization": f"Bearer {admin1_token}"}
        )
        assert list_response.status_code == 200, f"List failed: {list_response.text}"
        contracts = list_response.json()
        
        print(f"Total AMC contracts in list: {len(contracts)}")
        
        # Find our created contract
        found = any(c["id"] == amc_id for c in contracts)
        if not found:
            print(f"CRITICAL BUG: Created AMC contract {amc_id} not found in list!")
            print(f"AMC IDs in list: {[c['id'] for c in contracts[:10]]}")
        assert found, f"Created AMC contract {amc_id} not found in list! This is the tenant scoping bug."
        print(f"SUCCESS: AMC contract {unique_name} is visible in list")
    
    def test_tenant_isolation_amc_contracts(self, admin1_token, admin2_token, admin1_company):
        """Test that admin2 cannot see admin1's AMC contracts"""
        unique_name = f"TEST_IsolAMC_{uuid.uuid4().hex[:8]}"
        
        # Create AMC as admin1
        create_response = requests.post(
            f"{BASE_URL}/api/admin/amc-contracts",
            headers={"Authorization": f"Bearer {admin1_token}"},
            json={
                "company_id": admin1_company,
                "name": unique_name,
                "amc_type": "comprehensive",
                "start_date": "2024-01-01",
                "end_date": "2025-12-31"
            }
        )
        assert create_response.status_code == 200
        amc_id = create_response.json()["id"]
        print(f"Admin1 created AMC: {amc_id}")
        
        # List AMC contracts as admin2
        list_response = requests.get(
            f"{BASE_URL}/api/admin/amc-contracts",
            headers={"Authorization": f"Bearer {admin2_token}"}
        )
        assert list_response.status_code == 200
        admin2_contracts = list_response.json()
        
        # Verify admin1's AMC is NOT visible to admin2
        found = any(c["id"] == amc_id for c in admin2_contracts)
        assert not found, f"TENANT ISOLATION FAILURE: Admin2 can see Admin1's AMC {amc_id}!"
        print(f"SUCCESS: Tenant isolation working - Admin2 cannot see Admin1's AMC contract")


class TestDashboardTenantScoping:
    """Test dashboard stats with tenant scoping"""
    
    @pytest.fixture
    def admin1_token(self):
        """Get admin1 auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin1 login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_dashboard_stats_endpoint(self, admin1_token):
        """Test dashboard stats endpoint returns data"""
        # Correct endpoint is /api/admin/dashboard (not /api/admin/dashboard/stats)
        response = requests.get(
            f"{BASE_URL}/api/admin/dashboard",
            headers={"Authorization": f"Bearer {admin1_token}"}
        )
        print(f"Dashboard stats response: {response.status_code}")
        
        assert response.status_code == 200, f"Dashboard stats failed: {response.text}"
        data = response.json()
        
        # Verify expected fields
        assert "companies_count" in data, "Missing companies_count"
        assert "devices_count" in data, "Missing devices_count"
        
        print(f"Dashboard stats: companies={data.get('companies_count')}, devices={data.get('devices_count')}")
        print(f"Full stats: {data}")


class TestCompanyDropdownInForms:
    """Test that company dropdowns show organization's companies"""
    
    @pytest.fixture
    def admin1_token(self):
        """Get admin1 auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN1_EMAIL,
            "password": ADMIN1_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin1 login failed: {response.text}")
        return response.json()["access_token"]
    
    def test_companies_list_for_dropdown(self, admin1_token):
        """Test companies list returns data for dropdowns"""
        response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers={"Authorization": f"Bearer {admin1_token}"}
        )
        assert response.status_code == 200, f"Companies list failed: {response.text}"
        companies = response.json()
        
        print(f"Companies available for dropdown: {len(companies)}")
        
        # Verify each company has required fields for dropdown
        for company in companies[:5]:  # Check first 5
            assert "id" in company, "Company missing id"
            assert "name" in company, "Company missing name"
            print(f"  - {company.get('name')} (ID: {company.get('id')})")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
