"""
Test Suite for Bulk Import APIs and Office Supplies Search Feature
Tests:
- POST /api/admin/bulk-import/companies
- POST /api/admin/bulk-import/sites
- POST /api/admin/bulk-import/devices
- POST /api/admin/bulk-import/supply-products
- Office Supplies search functionality
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"
COMPANY_USER_EMAIL = "jane@acme.com"
COMPANY_USER_PASSWORD = "company123"


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def company_token():
    """Get company user authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": COMPANY_USER_EMAIL,
        "password": COMPANY_USER_PASSWORD
    })
    assert response.status_code == 200, f"Company login failed: {response.text}"
    return response.json().get("token")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Admin auth headers"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def company_headers(company_token):
    """Company user auth headers"""
    return {"Authorization": f"Bearer {company_token}", "Content-Type": "application/json"}


class TestBulkImportCompanies:
    """Test bulk import companies endpoint"""
    
    def test_bulk_import_companies_success(self, admin_headers):
        """Test successful bulk import of companies"""
        unique_id = str(uuid.uuid4())[:6].upper()
        records = [
            {
                "name": f"TEST_BulkCompany1_{unique_id}",
                "company_code": f"BULK1{unique_id}",
                "industry": "Technology",
                "contact_name": "John Bulk",
                "contact_email": f"john.bulk1.{unique_id}@test.com",
                "contact_phone": "9876543210",
                "address": "123 Bulk Street",
                "city": "Mumbai",
                "state": "Maharashtra",
                "pincode": "400001"
            },
            {
                "name": f"TEST_BulkCompany2_{unique_id}",
                "company_code": f"BULK2{unique_id}",
                "industry": "Manufacturing",
                "contact_name": "Jane Bulk",
                "contact_email": f"jane.bulk2.{unique_id}@test.com",
                "contact_phone": "9876543211"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/companies",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Bulk import failed: {response.text}"
        data = response.json()
        assert "success" in data
        assert "errors" in data
        assert data["success"] == 2, f"Expected 2 successful imports, got {data['success']}"
        assert len(data["errors"]) == 0, f"Unexpected errors: {data['errors']}"
    
    def test_bulk_import_companies_missing_name(self, admin_headers):
        """Test bulk import with missing required field (name)"""
        records = [
            {
                "company_code": "NONAME001",
                "contact_name": "No Name Contact"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/companies",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 0
        assert len(data["errors"]) == 1
        assert "name" in data["errors"][0]["message"].lower() or "required" in data["errors"][0]["message"].lower()
    
    def test_bulk_import_companies_duplicate_code(self, admin_headers):
        """Test bulk import with duplicate company code"""
        unique_id = str(uuid.uuid4())[:6].upper()
        
        # First import
        records = [{"name": f"TEST_DupCode_{unique_id}", "company_code": f"DUP{unique_id}"}]
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/companies",
            json={"records": records},
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Second import with same code
        records = [{"name": f"TEST_DupCode2_{unique_id}", "company_code": f"DUP{unique_id}"}]
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/companies",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 0
        assert len(data["errors"]) == 1
        assert "already exists" in data["errors"][0]["message"].lower()
    
    def test_bulk_import_companies_empty_records(self, admin_headers):
        """Test bulk import with empty records array"""
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/companies",
            json={"records": []},
            headers=admin_headers
        )
        
        assert response.status_code == 400
        assert "no records" in response.json().get("detail", "").lower()


class TestBulkImportSites:
    """Test bulk import sites endpoint"""
    
    def test_bulk_import_sites_success(self, admin_headers):
        """Test successful bulk import of sites"""
        unique_id = str(uuid.uuid4())[:6].upper()
        
        # First get a company to use
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers=admin_headers
        )
        assert companies_response.status_code == 200
        companies = companies_response.json()
        assert len(companies) > 0, "No companies found for site import test"
        
        company = companies[0]
        
        records = [
            {
                "name": f"TEST_BulkSite1_{unique_id}",
                "company_code": company.get("company_code"),
                "site_type": "office",
                "address": "456 Bulk Site Road",
                "city": "Pune",
                "state": "Maharashtra",
                "pincode": "411001",
                "contact_name": "Site Contact",
                "contact_phone": "9876543212"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/sites",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Bulk import sites failed: {response.text}"
        data = response.json()
        assert "success" in data
        assert "errors" in data
        assert data["success"] >= 1, f"Expected at least 1 successful import, got {data['success']}"
    
    def test_bulk_import_sites_missing_name(self, admin_headers):
        """Test bulk import sites with missing required field"""
        records = [
            {
                "company_code": "ACME",
                "site_type": "office"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/sites",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 0
        assert len(data["errors"]) >= 1
    
    def test_bulk_import_sites_invalid_company(self, admin_headers):
        """Test bulk import sites with non-existent company"""
        unique_id = str(uuid.uuid4())[:6].upper()
        records = [
            {
                "name": f"TEST_InvalidCompanySite_{unique_id}",
                "company_code": "NONEXISTENT999",
                "site_type": "office"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/sites",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 0
        assert len(data["errors"]) >= 1
        assert "company" in data["errors"][0]["message"].lower() or "not found" in data["errors"][0]["message"].lower()


class TestBulkImportDevices:
    """Test bulk import devices endpoint"""
    
    def test_bulk_import_devices_success(self, admin_headers):
        """Test successful bulk import of devices"""
        unique_id = str(uuid.uuid4())[:6].upper()
        
        # Get a company
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers=admin_headers
        )
        assert companies_response.status_code == 200
        companies = companies_response.json()
        assert len(companies) > 0
        
        company = companies[0]
        
        records = [
            {
                "company_code": company.get("company_code"),
                "device_type": "Laptop",
                "brand": "Dell",
                "model": "Latitude 5520",
                "serial_number": f"BULK-SN-{unique_id}",
                "asset_tag": f"BULK-AT-{unique_id}",
                "purchase_date": "2024-01-15",
                "warranty_end_date": "2027-01-15",
                "condition": "good",
                "status": "active"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/devices",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Bulk import devices failed: {response.text}"
        data = response.json()
        assert "success" in data
        assert "errors" in data
        assert data["success"] >= 1, f"Expected at least 1 successful import, got {data['success']}"
    
    def test_bulk_import_devices_missing_serial(self, admin_headers):
        """Test bulk import devices with missing serial number"""
        records = [
            {
                "company_code": "ACME",
                "device_type": "Laptop",
                "brand": "HP"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/devices",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 0
        assert len(data["errors"]) >= 1
    
    def test_bulk_import_devices_duplicate_serial(self, admin_headers):
        """Test bulk import devices with duplicate serial number"""
        unique_id = str(uuid.uuid4())[:6].upper()
        
        # Get a company
        companies_response = requests.get(
            f"{BASE_URL}/api/admin/companies",
            headers=admin_headers
        )
        companies = companies_response.json()
        company = companies[0]
        
        # First import
        records = [
            {
                "company_code": company.get("company_code"),
                "device_type": "Laptop",
                "brand": "Dell",
                "model": "Test",
                "serial_number": f"DUP-SN-{unique_id}"
            }
        ]
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/devices",
            json={"records": records},
            headers=admin_headers
        )
        assert response.status_code == 200
        
        # Second import with same serial
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/devices",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 0
        assert len(data["errors"]) >= 1
        assert "already exists" in data["errors"][0]["message"].lower()


class TestBulkImportSupplyProducts:
    """Test bulk import supply products endpoint"""
    
    def test_bulk_import_supply_products_success(self, admin_headers):
        """Test successful bulk import of supply products"""
        unique_id = str(uuid.uuid4())[:6].upper()
        
        records = [
            {
                "name": f"TEST_BulkProduct1_{unique_id}",
                "category": "Stationery",
                "description": "Test bulk product 1",
                "unit": "piece"
            },
            {
                "name": f"TEST_BulkProduct2_{unique_id}",
                "category": "Printer Consumables",
                "description": "Test bulk product 2",
                "unit": "cartridge"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/supply-products",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Bulk import supply products failed: {response.text}"
        data = response.json()
        assert "success" in data
        assert "errors" in data
        assert data["success"] == 2, f"Expected 2 successful imports, got {data['success']}"
    
    def test_bulk_import_supply_products_new_category(self, admin_headers):
        """Test bulk import creates new category if not exists"""
        unique_id = str(uuid.uuid4())[:6].upper()
        
        records = [
            {
                "name": f"TEST_NewCatProduct_{unique_id}",
                "category": f"TEST_NewCategory_{unique_id}",
                "description": "Product with new category",
                "unit": "box"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/supply-products",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Bulk import failed: {response.text}"
        data = response.json()
        assert data["success"] == 1, "Should auto-create category and import product"
    
    def test_bulk_import_supply_products_missing_name(self, admin_headers):
        """Test bulk import supply products with missing name"""
        records = [
            {
                "category": "Stationery",
                "description": "No name product"
            }
        ]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/supply-products",
            json={"records": records},
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == 0
        assert len(data["errors"]) >= 1
        assert "name" in data["errors"][0]["message"].lower() or "required" in data["errors"][0]["message"].lower()


class TestOfficeSuppliesSearch:
    """Test Office Supplies search functionality"""
    
    def test_supply_catalog_returns_products(self, company_headers):
        """Test that supply catalog returns products"""
        response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers=company_headers
        )
        
        assert response.status_code == 200, f"Failed to get catalog: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Catalog should be a list of categories"
        assert len(data) > 0, "Catalog should have at least one category"
        
        # Check structure
        for category in data:
            assert "id" in category
            assert "name" in category
            assert "products" in category
            assert isinstance(category["products"], list)
    
    def test_supply_catalog_has_searchable_products(self, company_headers):
        """Test that catalog has products with searchable fields"""
        response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers=company_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find products
        all_products = []
        for category in data:
            all_products.extend(category.get("products", []))
        
        assert len(all_products) > 0, "Should have products in catalog"
        
        # Check product structure for search
        for product in all_products[:5]:  # Check first 5
            assert "id" in product
            assert "name" in product
            # Description is optional but should be present if exists
            if "description" in product:
                assert isinstance(product["description"], (str, type(None)))


class TestBulkImportAuth:
    """Test bulk import authentication requirements"""
    
    def test_bulk_import_requires_admin_auth(self):
        """Test that bulk import endpoints require admin authentication"""
        endpoints = [
            "/api/admin/bulk-import/companies",
            "/api/admin/bulk-import/sites",
            "/api/admin/bulk-import/devices",
            "/api/admin/bulk-import/supply-products"
        ]
        
        for endpoint in endpoints:
            response = requests.post(
                f"{BASE_URL}{endpoint}",
                json={"records": []},
                headers={"Content-Type": "application/json"}
            )
            assert response.status_code in [401, 403], f"{endpoint} should require auth"
    
    def test_bulk_import_rejects_company_user(self, company_headers):
        """Test that bulk import rejects company user auth"""
        response = requests.post(
            f"{BASE_URL}/api/admin/bulk-import/companies",
            json={"records": [{"name": "Test"}]},
            headers=company_headers
        )
        
        assert response.status_code in [401, 403], "Company user should not access admin bulk import"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
