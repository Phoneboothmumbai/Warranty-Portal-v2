"""
Test Company Employees Feature
Tests for:
1. Company Employees CRUD API
2. Bulk Import via CSV
3. Template Download
4. Device form integration with assigned_employee_id
5. Configuration field for Laptops/Desktops/Tablets
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://device-manager-50.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "admin@demo.com"
ADMIN_PASSWORD = "admin123"


class TestCompanyEmployeesAPI:
    """Test Company Employees CRUD operations"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_01_list_company_employees(self):
        """Test GET /api/admin/company-employees - List employees"""
        response = self.session.get(f"{BASE_URL}/api/admin/company-employees")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✅ List company employees: {len(data)} employees found")
    
    def test_02_list_employees_with_company_filter(self):
        """Test GET /api/admin/company-employees with company_id filter"""
        # First get a company
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies", params={"limit": 1})
        assert companies_response.status_code == 200
        
        companies = companies_response.json()
        if not companies:
            pytest.skip("No companies found")
        
        company_id = companies[0]["id"]
        
        # Filter employees by company
        response = self.session.get(f"{BASE_URL}/api/admin/company-employees", params={"company_id": company_id})
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        print(f"✅ List employees for company {company_id}: {len(data)} employees")
    
    def test_03_create_company_employee(self):
        """Test POST /api/admin/company-employees - Create employee"""
        # Get a company first
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies", params={"limit": 1})
        companies = companies_response.json()
        if not companies:
            pytest.skip("No companies found")
        
        company_id = companies[0]["id"]
        
        # Create employee
        employee_data = {
            "company_id": company_id,
            "name": "TEST_John Smith",
            "email": "test_john@example.com",
            "phone": "9876543210",
            "department": "IT",
            "designation": "Software Engineer",
            "location": "Floor 2, Desk 15"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/company-employees", json=employee_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_John Smith"
        assert data["email"] == "test_john@example.com"
        assert data["department"] == "IT"
        assert "id" in data
        
        # Store for later tests
        self.__class__.created_employee_id = data["id"]
        print(f"✅ Created employee: {data['name']} (ID: {data['id']})")
    
    def test_04_get_company_employee(self):
        """Test GET /api/admin/company-employees/{id} - Get single employee"""
        if not hasattr(self.__class__, 'created_employee_id'):
            pytest.skip("No employee created in previous test")
        
        employee_id = self.__class__.created_employee_id
        response = self.session.get(f"{BASE_URL}/api/admin/company-employees/{employee_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == employee_id
        assert data["name"] == "TEST_John Smith"
        print(f"✅ Get employee: {data['name']}")
    
    def test_05_update_company_employee(self):
        """Test PUT /api/admin/company-employees/{id} - Update employee"""
        if not hasattr(self.__class__, 'created_employee_id'):
            pytest.skip("No employee created in previous test")
        
        employee_id = self.__class__.created_employee_id
        update_data = {
            "designation": "Senior Software Engineer",
            "department": "Engineering"
        }
        
        response = self.session.put(f"{BASE_URL}/api/admin/company-employees/{employee_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/admin/company-employees/{employee_id}")
        data = get_response.json()
        assert data["designation"] == "Senior Software Engineer"
        assert data["department"] == "Engineering"
        print(f"✅ Updated employee designation and department")
    
    def test_06_quick_create_employee(self):
        """Test POST /api/admin/company-employees/quick-create - Quick create via form data"""
        # Get a company first
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies", params={"limit": 1})
        companies = companies_response.json()
        if not companies:
            pytest.skip("No companies found")
        
        company_id = companies[0]["id"]
        
        # Quick create uses form data, not JSON
        form_data = {
            "company_id": company_id,
            "name": "TEST_Quick Employee",
            "email": "test_quick@example.com",
            "department": "Sales"
        }
        
        # Remove Content-Type header for form data
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.post(f"{BASE_URL}/api/admin/company-employees/quick-create", data=form_data, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["name"] == "TEST_Quick Employee"
        assert "label" in data  # Should have label for SmartSelect
        
        self.__class__.quick_created_employee_id = data["id"]
        print(f"✅ Quick created employee: {data['name']}")
    
    def test_07_download_template(self):
        """Test GET /api/admin/company-employees/template/download - Download CSV template"""
        response = self.session.get(f"{BASE_URL}/api/admin/company-employees/template/download")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        
        content = response.content.decode('utf-8-sig')  # Handle BOM
        assert "company_code" in content
        assert "name" in content
        assert "employee_id" in content
        assert "email" in content
        assert "department" in content
        print(f"✅ Downloaded CSV template ({len(content)} bytes)")
    
    def test_08_bulk_import_employees(self):
        """Test POST /api/admin/company-employees/bulk-import - Bulk import via CSV"""
        # Get a company first
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies", params={"limit": 1})
        companies = companies_response.json()
        if not companies:
            pytest.skip("No companies found")
        
        company_code = companies[0].get("code", "ACME001")
        
        # Create CSV content
        csv_content = f"""company_code,name,employee_id,email,phone,department,designation,location
{company_code},TEST_Bulk Employee 1,BULK001,bulk1@test.com,1234567890,IT,Developer,Floor 1
{company_code},TEST_Bulk Employee 2,BULK002,bulk2@test.com,1234567891,HR,Manager,Floor 2
"""
        
        # Upload as file
        files = {
            'file': ('employees.csv', io.BytesIO(csv_content.encode('utf-8')), 'text/csv')
        }
        headers = {"Authorization": f"Bearer {self.token}"}
        
        response = requests.post(f"{BASE_URL}/api/admin/company-employees/bulk-import", files=files, headers=headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "created" in data
        print(f"✅ Bulk import: {data.get('created', 0)} employees created, {len(data.get('errors', []))} errors")
    
    def test_09_delete_company_employee(self):
        """Test DELETE /api/admin/company-employees/{id} - Delete employee"""
        if not hasattr(self.__class__, 'created_employee_id'):
            pytest.skip("No employee created in previous test")
        
        employee_id = self.__class__.created_employee_id
        response = self.session.delete(f"{BASE_URL}/api/admin/company-employees/{employee_id}")
        assert response.status_code == 200
        
        # Verify deletion (should return 404)
        get_response = self.session.get(f"{BASE_URL}/api/admin/company-employees/{employee_id}")
        assert get_response.status_code == 404
        print(f"✅ Deleted employee: {employee_id}")
    
    def test_10_cleanup_test_employees(self):
        """Cleanup - Delete all TEST_ prefixed employees"""
        response = self.session.get(f"{BASE_URL}/api/admin/company-employees", params={"limit": 500})
        employees = response.json()
        
        deleted_count = 0
        for emp in employees:
            if emp.get("name", "").startswith("TEST_"):
                del_response = self.session.delete(f"{BASE_URL}/api/admin/company-employees/{emp['id']}")
                if del_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✅ Cleanup: Deleted {deleted_count} test employees")


class TestDeviceWithEmployeeAndConfiguration:
    """Test Device form with new fields: assigned_employee_id and configuration"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get token
        login_response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {token}"})
            self.token = token
        else:
            pytest.skip(f"Login failed: {login_response.status_code}")
    
    def test_01_create_device_with_configuration(self):
        """Test creating a Laptop device with configuration field"""
        # Get a company first
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies", params={"limit": 1})
        companies = companies_response.json()
        if not companies:
            pytest.skip("No companies found")
        
        company_id = companies[0]["id"]
        
        # Create device with configuration
        device_data = {
            "company_id": company_id,
            "device_type": "Laptop",
            "brand": "Dell",
            "model": "Latitude 5520",
            "serial_number": f"TEST-CONFIG-{os.urandom(4).hex().upper()}",
            "purchase_date": "2024-01-15",
            "configuration": "Intel i7-12700H, 16GB RAM, 512GB SSD, Windows 11 Pro"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/devices", json=device_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["configuration"] == device_data["configuration"]
        assert data["device_type"] == "Laptop"
        
        self.__class__.device_with_config_id = data["id"]
        print(f"✅ Created Laptop with configuration: {data['serial_number']}")
    
    def test_02_create_device_with_employee(self):
        """Test creating a device with assigned_employee_id"""
        # Get a company first
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies", params={"limit": 1})
        companies = companies_response.json()
        if not companies:
            pytest.skip("No companies found")
        
        company_id = companies[0]["id"]
        
        # Create an employee first
        employee_data = {
            "company_id": company_id,
            "name": "TEST_Device User",
            "email": "test_device_user@example.com",
            "department": "IT"
        }
        emp_response = self.session.post(f"{BASE_URL}/api/admin/company-employees", json=employee_data)
        assert emp_response.status_code == 200
        employee_id = emp_response.json()["id"]
        self.__class__.test_employee_id = employee_id
        
        # Create device with assigned employee
        device_data = {
            "company_id": company_id,
            "device_type": "Desktop",
            "brand": "HP",
            "model": "ProDesk 400",
            "serial_number": f"TEST-EMP-{os.urandom(4).hex().upper()}",
            "purchase_date": "2024-02-20",
            "assigned_employee_id": employee_id,
            "configuration": "Intel i5-12400, 8GB RAM, 256GB SSD"
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/devices", json=device_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data["assigned_employee_id"] == employee_id
        assert data["configuration"] == device_data["configuration"]
        
        self.__class__.device_with_employee_id = data["id"]
        print(f"✅ Created Desktop with assigned employee: {data['serial_number']}")
    
    def test_03_update_device_configuration(self):
        """Test updating device configuration"""
        if not hasattr(self.__class__, 'device_with_config_id'):
            pytest.skip("No device created in previous test")
        
        device_id = self.__class__.device_with_config_id
        update_data = {
            "configuration": "Intel i7-12700H, 32GB RAM, 1TB SSD, Windows 11 Pro (Upgraded)"
        }
        
        response = self.session.put(f"{BASE_URL}/api/admin/devices/{device_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/admin/devices/{device_id}")
        data = get_response.json()
        assert "32GB RAM" in data["configuration"]
        print(f"✅ Updated device configuration")
    
    def test_04_update_device_employee_assignment(self):
        """Test updating device assigned employee"""
        if not hasattr(self.__class__, 'device_with_employee_id'):
            pytest.skip("No device created in previous test")
        
        device_id = self.__class__.device_with_employee_id
        
        # Create another employee
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies", params={"limit": 1})
        company_id = companies_response.json()[0]["id"]
        
        new_emp_data = {
            "company_id": company_id,
            "name": "TEST_New Device User",
            "department": "Finance"
        }
        new_emp_response = self.session.post(f"{BASE_URL}/api/admin/company-employees", json=new_emp_data)
        new_employee_id = new_emp_response.json()["id"]
        self.__class__.new_test_employee_id = new_employee_id
        
        # Update device assignment
        update_data = {
            "assigned_employee_id": new_employee_id
        }
        
        response = self.session.put(f"{BASE_URL}/api/admin/devices/{device_id}", json=update_data)
        assert response.status_code == 200
        
        # Verify update
        get_response = self.session.get(f"{BASE_URL}/api/admin/devices/{device_id}")
        data = get_response.json()
        assert data["assigned_employee_id"] == new_employee_id
        print(f"✅ Updated device employee assignment")
    
    def test_05_printer_should_not_have_configuration(self):
        """Test that Printer device type doesn't require configuration (it's optional)"""
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies", params={"limit": 1})
        companies = companies_response.json()
        if not companies:
            pytest.skip("No companies found")
        
        company_id = companies[0]["id"]
        
        # Create printer without configuration
        device_data = {
            "company_id": company_id,
            "device_type": "Printer",
            "brand": "HP",
            "model": "LaserJet Pro M404",
            "serial_number": f"TEST-PRINTER-{os.urandom(4).hex().upper()}",
            "purchase_date": "2024-03-01"
            # No configuration field - should work fine
        }
        
        response = self.session.post(f"{BASE_URL}/api/admin/devices", json=device_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("configuration") is None or data.get("configuration") == ""
        
        self.__class__.printer_device_id = data["id"]
        print(f"✅ Created Printer without configuration: {data['serial_number']}")
    
    def test_06_cleanup_test_devices(self):
        """Cleanup - Delete test devices and employees"""
        # Delete devices
        for attr in ['device_with_config_id', 'device_with_employee_id', 'printer_device_id']:
            if hasattr(self.__class__, attr):
                device_id = getattr(self.__class__, attr)
                self.session.delete(f"{BASE_URL}/api/admin/devices/{device_id}")
        
        # Delete employees
        for attr in ['test_employee_id', 'new_test_employee_id']:
            if hasattr(self.__class__, attr):
                emp_id = getattr(self.__class__, attr)
                self.session.delete(f"{BASE_URL}/api/admin/company-employees/{emp_id}")
        
        print(f"✅ Cleanup: Deleted test devices and employees")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
