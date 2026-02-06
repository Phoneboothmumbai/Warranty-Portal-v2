"""
Service & Inventory Module Tests
================================
Comprehensive tests for the new MSP-grade Service & Inventory Module:
- Problem Master API
- Item Master API
- Inventory Location API
- Stock Ledger API
- Vendor Master API
- Service Tickets (New) API
- Service Visits API
- Ticket Parts API

Test credentials: ck@motta.in / Charu@123@
Key IDs:
- Company ID: 7bf0f993-706d-45bf-8704-ded6d7fecda8
- Location ID: 5380e220-812e-4bec-8585-82650c5c426e
- Item ID: 2c4c2427-1efa-4a50-ba52-f33f7917a4d5
- Staff/Engineer ID: acd161f1-a3e6-4514-9c14-092b19a4b5c3
"""
import pytest
import requests
import os
import uuid
from datetime import datetime

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"

# Key IDs from context
COMPANY_ID = "7bf0f993-706d-45bf-8704-ded6d7fecda8"
LOCATION_ID = "5380e220-812e-4bec-8585-82650c5c426e"
ITEM_ID = "2c4c2427-1efa-4a50-ba52-f33f7917a4d5"
STAFF_ID = "acd161f1-a3e6-4514-9c14-092b19a4b5c3"


@pytest.fixture(scope="module")
def auth_token():
    """Get authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    assert "access_token" in data, f"No access_token in response: {data}"
    return data["access_token"]


@pytest.fixture(scope="module")
def auth_headers(auth_token):
    """Get headers with auth token"""
    return {
        "Authorization": f"Bearer {auth_token}",
        "Content-Type": "application/json"
    }


# ==================== PROBLEM MASTER TESTS ====================

class TestProblemMasterAPI:
    """Tests for Problem Master CRUD operations"""
    
    created_problem_id = None
    
    def test_list_problem_categories(self, auth_headers):
        """GET /api/admin/problems/categories - Get problem categories"""
        response = requests.get(f"{BASE_URL}/api/admin/problems/categories", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) > 0
        print(f"✓ Found {len(data['categories'])} problem categories")
    
    def test_seed_default_problems(self, auth_headers):
        """POST /api/admin/problems/seed - Seed default problems"""
        response = requests.post(f"{BASE_URL}/api/admin/problems/seed", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "success" in data
        print(f"✓ Seed result: {data.get('message', 'OK')}")
    
    def test_list_problems(self, auth_headers):
        """GET /api/admin/problems - List all problems"""
        response = requests.get(f"{BASE_URL}/api/admin/problems", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "problems" in data
        assert "total" in data
        print(f"✓ Found {data['total']} problems")
    
    def test_create_problem(self, auth_headers):
        """POST /api/admin/problems - Create a new problem type"""
        problem_data = {
            "name": f"TEST_Problem_{uuid.uuid4().hex[:8]}",
            "code": f"TST-{uuid.uuid4().hex[:4].upper()}",
            "description": "Test problem type for automated testing",
            "category": "hardware",
            "default_priority": "high",
            "requires_onsite": True,
            "requires_parts": True
        }
        response = requests.post(f"{BASE_URL}/api/admin/problems", json=problem_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == problem_data["name"]
        TestProblemMasterAPI.created_problem_id = data["id"]
        print(f"✓ Created problem: {data['name']} (ID: {data['id']})")
    
    def test_get_problem(self, auth_headers):
        """GET /api/admin/problems/{id} - Get specific problem"""
        if not TestProblemMasterAPI.created_problem_id:
            pytest.skip("No problem created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/problems/{TestProblemMasterAPI.created_problem_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == TestProblemMasterAPI.created_problem_id
        print(f"✓ Retrieved problem: {data['name']}")
    
    def test_update_problem(self, auth_headers):
        """PUT /api/admin/problems/{id} - Update problem"""
        if not TestProblemMasterAPI.created_problem_id:
            pytest.skip("No problem created")
        
        update_data = {
            "description": "Updated description for testing",
            "default_priority": "critical"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/problems/{TestProblemMasterAPI.created_problem_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["default_priority"] == "critical"
        print(f"✓ Updated problem priority to: {data['default_priority']}")
    
    def test_delete_problem(self, auth_headers):
        """DELETE /api/admin/problems/{id} - Soft delete problem"""
        if not TestProblemMasterAPI.created_problem_id:
            pytest.skip("No problem created")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/problems/{TestProblemMasterAPI.created_problem_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✓ Deleted problem successfully")


# ==================== ITEM MASTER TESTS ====================

class TestItemMasterAPI:
    """Tests for Item Master CRUD operations"""
    
    created_item_id = None
    
    def test_list_item_categories(self, auth_headers):
        """GET /api/admin/items/categories - Get item categories"""
        response = requests.get(f"{BASE_URL}/api/admin/items/categories", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "categories" in data
        print(f"✓ Found {len(data['categories'])} item categories")
    
    def test_create_item(self, auth_headers):
        """POST /api/admin/items - Create a new item"""
        item_data = {
            "name": f"TEST_Item_{uuid.uuid4().hex[:8]}",
            "sku": f"TST-SKU-{uuid.uuid4().hex[:6].upper()}",
            "part_number": f"PN-{uuid.uuid4().hex[:8]}",
            "category": "part",
            "brand": "Test Brand",
            "model": "Test Model",
            "unit_price": 1500.00,
            "cost_price": 1000.00,
            "unit_of_measure": "piece",
            "reorder_level": 5,
            "reorder_quantity": 10,
            "gst_rate": 18
        }
        response = requests.post(f"{BASE_URL}/api/admin/items", json=item_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == item_data["name"]
        TestItemMasterAPI.created_item_id = data["id"]
        print(f"✓ Created item: {data['name']} (SKU: {data['sku']})")
    
    def test_list_items(self, auth_headers):
        """GET /api/admin/items - List all items"""
        response = requests.get(f"{BASE_URL}/api/admin/items", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        assert "total" in data
        print(f"✓ Found {data['total']} items")
    
    def test_search_items(self, auth_headers):
        """GET /api/admin/items/search - Search items"""
        response = requests.get(f"{BASE_URL}/api/admin/items/search?q=TEST", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"✓ Search returned {len(data['items'])} items")
    
    def test_get_item(self, auth_headers):
        """GET /api/admin/items/{id} - Get specific item"""
        if not TestItemMasterAPI.created_item_id:
            pytest.skip("No item created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/items/{TestItemMasterAPI.created_item_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == TestItemMasterAPI.created_item_id
        print(f"✓ Retrieved item: {data['name']}")
    
    def test_update_item(self, auth_headers):
        """PUT /api/admin/items/{id} - Update item"""
        if not TestItemMasterAPI.created_item_id:
            pytest.skip("No item created")
        
        update_data = {
            "unit_price": 1800.00,
            "reorder_level": 10
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/items/{TestItemMasterAPI.created_item_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["unit_price"] == 1800.00
        print(f"✓ Updated item price to: {data['unit_price']}")
    
    def test_get_item_stock(self, auth_headers):
        """GET /api/admin/items/{id}/stock - Get item stock levels"""
        # Use the provided ITEM_ID from context
        response = requests.get(
            f"{BASE_URL}/api/admin/items/{ITEM_ID}/stock",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "item_id" in data
        assert "total_stock" in data
        print(f"✓ Item stock: {data['total_stock']} units")
    
    def test_delete_item(self, auth_headers):
        """DELETE /api/admin/items/{id} - Soft delete item"""
        if not TestItemMasterAPI.created_item_id:
            pytest.skip("No item created")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/items/{TestItemMasterAPI.created_item_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✓ Deleted item successfully")


# ==================== INVENTORY LOCATION TESTS ====================

class TestInventoryLocationAPI:
    """Tests for Inventory Location CRUD operations"""
    
    created_location_id = None
    
    def test_list_location_types(self, auth_headers):
        """GET /api/admin/inventory/locations/types - Get location types"""
        response = requests.get(f"{BASE_URL}/api/admin/inventory/locations/types", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "types" in data
        print(f"✓ Found {len(data['types'])} location types")
    
    def test_create_location(self, auth_headers):
        """POST /api/admin/inventory/locations - Create a new location"""
        location_data = {
            "name": f"TEST_Warehouse_{uuid.uuid4().hex[:8]}",
            "code": f"WH-{uuid.uuid4().hex[:4].upper()}",
            "location_type": "warehouse",
            "address": "123 Test Street",
            "city": "Mumbai",
            "state": "Maharashtra",
            "pincode": "400001",
            "contact_name": "Test Manager",
            "contact_phone": "9876543210"
        }
        response = requests.post(f"{BASE_URL}/api/admin/inventory/locations", json=location_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == location_data["name"]
        TestInventoryLocationAPI.created_location_id = data["id"]
        print(f"✓ Created location: {data['name']} (Code: {data['code']})")
    
    def test_list_locations(self, auth_headers):
        """GET /api/admin/inventory/locations - List all locations"""
        response = requests.get(f"{BASE_URL}/api/admin/inventory/locations", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "locations" in data
        assert "total" in data
        print(f"✓ Found {data['total']} locations")
    
    def test_get_location(self, auth_headers):
        """GET /api/admin/inventory/locations/{id} - Get specific location"""
        if not TestInventoryLocationAPI.created_location_id:
            pytest.skip("No location created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/inventory/locations/{TestInventoryLocationAPI.created_location_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == TestInventoryLocationAPI.created_location_id
        print(f"✓ Retrieved location: {data['name']}")
    
    def test_update_location(self, auth_headers):
        """PUT /api/admin/inventory/locations/{id} - Update location"""
        if not TestInventoryLocationAPI.created_location_id:
            pytest.skip("No location created")
        
        update_data = {
            "contact_name": "Updated Manager",
            "is_default": False
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/inventory/locations/{TestInventoryLocationAPI.created_location_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["contact_name"] == "Updated Manager"
        print(f"✓ Updated location contact to: {data['contact_name']}")
    
    def test_delete_location(self, auth_headers):
        """DELETE /api/admin/inventory/locations/{id} - Soft delete location"""
        if not TestInventoryLocationAPI.created_location_id:
            pytest.skip("No location created")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/inventory/locations/{TestInventoryLocationAPI.created_location_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✓ Deleted location successfully")


# ==================== STOCK LEDGER TESTS ====================

class TestStockLedgerAPI:
    """Tests for Stock Ledger operations"""
    
    test_item_id = None
    test_location_id = None
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, auth_headers):
        """Create test item and location for stock tests"""
        # Create test item
        item_data = {
            "name": f"TEST_StockItem_{uuid.uuid4().hex[:8]}",
            "sku": f"STK-{uuid.uuid4().hex[:6].upper()}",
            "category": "part",
            "unit_price": 500.00,
            "cost_price": 300.00
        }
        response = requests.post(f"{BASE_URL}/api/admin/items", json=item_data, headers=auth_headers)
        if response.status_code == 200:
            TestStockLedgerAPI.test_item_id = response.json()["id"]
        
        # Create test location
        location_data = {
            "name": f"TEST_StockLoc_{uuid.uuid4().hex[:8]}",
            "code": f"SL-{uuid.uuid4().hex[:4].upper()}",
            "location_type": "warehouse"
        }
        response = requests.post(f"{BASE_URL}/api/admin/inventory/locations", json=location_data, headers=auth_headers)
        if response.status_code == 200:
            TestStockLedgerAPI.test_location_id = response.json()["id"]
    
    def test_stock_adjustment_positive(self, auth_headers):
        """POST /api/admin/inventory/stock/adjustment - Add stock"""
        if not TestStockLedgerAPI.test_item_id or not TestStockLedgerAPI.test_location_id:
            pytest.skip("Test data not created")
        
        adjustment_data = {
            "item_id": TestStockLedgerAPI.test_item_id,
            "location_id": TestStockLedgerAPI.test_location_id,
            "quantity": 50,
            "reason": "Initial stock for testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/inventory/stock/adjustment",
            json=adjustment_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✓ Added 50 units to stock")
    
    def test_get_stock_levels(self, auth_headers):
        """GET /api/admin/inventory/stock - Get stock levels"""
        response = requests.get(f"{BASE_URL}/api/admin/inventory/stock", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "stock_levels" in data
        print(f"✓ Found {len(data['stock_levels'])} stock entries")
    
    def test_get_stock_by_location(self, auth_headers):
        """GET /api/admin/inventory/stock/location/{id} - Get stock by location"""
        if not TestStockLedgerAPI.test_location_id:
            pytest.skip("Test location not created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/inventory/stock/location/{TestStockLedgerAPI.test_location_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "items" in data
        print(f"✓ Location has {len(data['items'])} items in stock")
    
    def test_get_stock_ledger(self, auth_headers):
        """GET /api/admin/inventory/ledger - Get stock ledger entries"""
        response = requests.get(f"{BASE_URL}/api/admin/inventory/ledger", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "entries" in data
        print(f"✓ Found {len(data['entries'])} ledger entries")
    
    def test_stock_adjustment_negative(self, auth_headers):
        """POST /api/admin/inventory/stock/adjustment - Remove stock"""
        if not TestStockLedgerAPI.test_item_id or not TestStockLedgerAPI.test_location_id:
            pytest.skip("Test data not created")
        
        adjustment_data = {
            "item_id": TestStockLedgerAPI.test_item_id,
            "location_id": TestStockLedgerAPI.test_location_id,
            "quantity": -10,
            "reason": "Stock adjustment for testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/inventory/stock/adjustment",
            json=adjustment_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✓ Removed 10 units from stock")


# ==================== VENDOR MASTER TESTS ====================

class TestVendorMasterAPI:
    """Tests for Vendor Master CRUD operations"""
    
    created_vendor_id = None
    
    def test_create_vendor(self, auth_headers):
        """POST /api/admin/vendors - Create a new vendor"""
        vendor_data = {
            "name": f"TEST_Vendor_{uuid.uuid4().hex[:8]}",
            "code": f"VND-{uuid.uuid4().hex[:4].upper()}",
            "vendor_type": "supplier",
            "contact_name": "Test Contact",
            "contact_email": "vendor@test.com",
            "contact_phone": "9876543210",
            "address": "456 Vendor Street",
            "city": "Delhi",
            "state": "Delhi",
            "pincode": "110001",
            "gst_number": "22AAAAA0000A1Z5",
            "payment_terms": "net_30",
            "credit_limit": 100000,
            "credit_days": 30
        }
        response = requests.post(f"{BASE_URL}/api/admin/vendors", json=vendor_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["name"] == vendor_data["name"]
        TestVendorMasterAPI.created_vendor_id = data["id"]
        print(f"✓ Created vendor: {data['name']} (Code: {data['code']})")
    
    def test_list_vendors(self, auth_headers):
        """GET /api/admin/vendors - List all vendors"""
        response = requests.get(f"{BASE_URL}/api/admin/vendors", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "vendors" in data
        assert "total" in data
        print(f"✓ Found {data['total']} vendors")
    
    def test_search_vendors(self, auth_headers):
        """GET /api/admin/vendors/search - Search vendors"""
        response = requests.get(f"{BASE_URL}/api/admin/vendors/search?q=TEST", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "vendors" in data
        print(f"✓ Search returned {len(data['vendors'])} vendors")
    
    def test_get_vendor(self, auth_headers):
        """GET /api/admin/vendors/{id} - Get specific vendor"""
        if not TestVendorMasterAPI.created_vendor_id:
            pytest.skip("No vendor created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/vendors/{TestVendorMasterAPI.created_vendor_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == TestVendorMasterAPI.created_vendor_id
        print(f"✓ Retrieved vendor: {data['name']}")
    
    def test_update_vendor(self, auth_headers):
        """PUT /api/admin/vendors/{id} - Update vendor"""
        if not TestVendorMasterAPI.created_vendor_id:
            pytest.skip("No vendor created")
        
        update_data = {
            "credit_limit": 150000,
            "rating": 4
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/vendors/{TestVendorMasterAPI.created_vendor_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["credit_limit"] == 150000
        print(f"✓ Updated vendor credit limit to: {data['credit_limit']}")
    
    def test_add_vendor_item_mapping(self, auth_headers):
        """POST /api/admin/vendors/{id}/items - Add item to vendor catalog"""
        if not TestVendorMasterAPI.created_vendor_id:
            pytest.skip("No vendor created")
        
        mapping_data = {
            "vendor_id": TestVendorMasterAPI.created_vendor_id,
            "item_id": ITEM_ID,
            "unit_price": 950.00,
            "min_order_quantity": 5,
            "lead_time_days": 7,
            "is_preferred": True
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/vendors/{TestVendorMasterAPI.created_vendor_id}/items",
            json=mapping_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        print(f"✓ Added item mapping to vendor")
    
    def test_get_vendors_for_item(self, auth_headers):
        """GET /api/admin/vendors/for-item/{item_id} - Get vendors for item"""
        response = requests.get(
            f"{BASE_URL}/api/admin/vendors/for-item/{ITEM_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "vendors" in data
        print(f"✓ Found {len(data['vendors'])} vendors for item")
    
    def test_delete_vendor(self, auth_headers):
        """DELETE /api/admin/vendors/{id} - Soft delete vendor"""
        if not TestVendorMasterAPI.created_vendor_id:
            pytest.skip("No vendor created")
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/vendors/{TestVendorMasterAPI.created_vendor_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✓ Deleted vendor successfully")


# ==================== SERVICE TICKETS (NEW) TESTS ====================

class TestServiceTicketsNewAPI:
    """Tests for Service Tickets (New) API - Full ticket lifecycle"""
    
    created_ticket_id = None
    
    def test_get_ticket_statuses(self, auth_headers):
        """GET /api/admin/service-tickets/statuses - Get all statuses"""
        response = requests.get(f"{BASE_URL}/api/admin/service-tickets/statuses", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "statuses" in data
        assert len(data["statuses"]) == 7  # new, assigned, in_progress, pending_parts, completed, closed, cancelled
        print(f"✓ Found {len(data['statuses'])} ticket statuses")
    
    def test_create_ticket(self, auth_headers):
        """POST /api/admin/service-tickets - Create a new ticket"""
        ticket_data = {
            "company_id": COMPANY_ID,
            "title": f"TEST_Ticket_{uuid.uuid4().hex[:8]}",
            "description": "Test ticket for automated testing",
            "priority": "high",
            "contact_name": "Test Contact",
            "contact_phone": "9876543210",
            "source": "manual",
            "is_urgent": False
        }
        response = requests.post(f"{BASE_URL}/api/admin/service-tickets", json=ticket_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert "ticket_number" in data
        assert data["status"] == "new"
        assert len(data["ticket_number"]) == 6  # 6-char alphanumeric
        TestServiceTicketsNewAPI.created_ticket_id = data["id"]
        print(f"✓ Created ticket: {data['ticket_number']} (Status: {data['status']})")
    
    def test_list_tickets(self, auth_headers):
        """GET /api/admin/service-tickets - List all tickets"""
        response = requests.get(f"{BASE_URL}/api/admin/service-tickets", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "tickets" in data
        assert "total" in data
        print(f"✓ Found {data['total']} tickets")
    
    def test_get_ticket_stats(self, auth_headers):
        """GET /api/admin/service-tickets/stats - Get ticket statistics"""
        response = requests.get(f"{BASE_URL}/api/admin/service-tickets/stats", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total" in data
        assert "open" in data
        assert "closed" in data
        assert "by_status" in data
        print(f"✓ Stats: Total={data['total']}, Open={data['open']}, Closed={data['closed']}")
    
    def test_get_ticket(self, auth_headers):
        """GET /api/admin/service-tickets/{id} - Get specific ticket"""
        if not TestServiceTicketsNewAPI.created_ticket_id:
            pytest.skip("No ticket created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/service-tickets/{TestServiceTicketsNewAPI.created_ticket_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == TestServiceTicketsNewAPI.created_ticket_id
        assert "visits" in data
        assert "part_requests" in data
        print(f"✓ Retrieved ticket: {data['ticket_number']}")
    
    def test_update_ticket(self, auth_headers):
        """PUT /api/admin/service-tickets/{id} - Update ticket"""
        if not TestServiceTicketsNewAPI.created_ticket_id:
            pytest.skip("No ticket created")
        
        update_data = {
            "priority": "critical",
            "is_urgent": True
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/service-tickets/{TestServiceTicketsNewAPI.created_ticket_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["priority"] == "critical"
        assert data["is_urgent"] == True
        print(f"✓ Updated ticket priority to: {data['priority']}")
    
    def test_assign_ticket(self, auth_headers):
        """POST /api/admin/service-tickets/{id}/assign - Assign ticket to technician"""
        if not TestServiceTicketsNewAPI.created_ticket_id:
            pytest.skip("No ticket created")
        
        assign_data = {
            "technician_id": STAFF_ID,
            "notes": "Assigned for testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{TestServiceTicketsNewAPI.created_ticket_id}/assign",
            json=assign_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "assigned"
        assert data["assigned_to_id"] == STAFF_ID
        print(f"✓ Assigned ticket to: {data['assigned_to_name']}")
    
    def test_start_work(self, auth_headers):
        """POST /api/admin/service-tickets/{id}/start - Start work on ticket"""
        if not TestServiceTicketsNewAPI.created_ticket_id:
            pytest.skip("No ticket created")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{TestServiceTicketsNewAPI.created_ticket_id}/start",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "in_progress"
        print(f"✓ Started work on ticket (Status: {data['status']})")
    
    def test_add_comment(self, auth_headers):
        """POST /api/admin/service-tickets/{id}/comments - Add comment"""
        if not TestServiceTicketsNewAPI.created_ticket_id:
            pytest.skip("No ticket created")
        
        comment_data = {
            "text": "Test comment for automated testing",
            "is_internal": True
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{TestServiceTicketsNewAPI.created_ticket_id}/comments",
            json=comment_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✓ Added comment to ticket")
    
    def test_complete_ticket(self, auth_headers):
        """POST /api/admin/service-tickets/{id}/complete - Complete ticket"""
        if not TestServiceTicketsNewAPI.created_ticket_id:
            pytest.skip("No ticket created")
        
        complete_data = {
            "resolution_summary": "Issue resolved during testing",
            "resolution_type": "fixed"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{TestServiceTicketsNewAPI.created_ticket_id}/complete",
            json=complete_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "completed"
        print(f"✓ Completed ticket (Status: {data['status']})")
    
    def test_close_ticket(self, auth_headers):
        """POST /api/admin/service-tickets/{id}/close - Close ticket"""
        if not TestServiceTicketsNewAPI.created_ticket_id:
            pytest.skip("No ticket created")
        
        close_data = {
            "closure_notes": "Closed after testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{TestServiceTicketsNewAPI.created_ticket_id}/close",
            json=close_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "closed"
        print(f"✓ Closed ticket (Status: {data['status']})")
    
    def test_ticket_lifecycle_cancel(self, auth_headers):
        """Test ticket cancellation flow"""
        # Create a new ticket
        ticket_data = {
            "company_id": COMPANY_ID,
            "title": f"TEST_CancelTicket_{uuid.uuid4().hex[:8]}",
            "description": "Ticket to be cancelled",
            "priority": "low"
        }
        response = requests.post(f"{BASE_URL}/api/admin/service-tickets", json=ticket_data, headers=auth_headers)
        assert response.status_code == 200
        ticket_id = response.json()["id"]
        
        # Cancel the ticket
        cancel_data = {
            "cancellation_reason": "Cancelled for testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/service-tickets/{ticket_id}/cancel",
            json=cancel_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "cancelled"
        print(f"✓ Cancelled ticket (Status: {data['status']})")


# ==================== SERVICE VISITS TESTS ====================

class TestServiceVisitsAPI:
    """Tests for Service Visits API - Multi-visit with timer"""
    
    created_visit_id = None
    test_ticket_id = None
    
    @pytest.fixture(autouse=True)
    def setup_ticket(self, auth_headers):
        """Create a ticket for visit tests"""
        ticket_data = {
            "company_id": COMPANY_ID,
            "title": f"TEST_VisitTicket_{uuid.uuid4().hex[:8]}",
            "description": "Ticket for visit testing",
            "priority": "medium",
            "assigned_to_id": STAFF_ID
        }
        response = requests.post(f"{BASE_URL}/api/admin/service-tickets", json=ticket_data, headers=auth_headers)
        if response.status_code == 200:
            TestServiceVisitsAPI.test_ticket_id = response.json()["id"]
    
    def test_create_visit(self, auth_headers):
        """POST /api/admin/visits - Create a new visit"""
        if not TestServiceVisitsAPI.test_ticket_id:
            pytest.skip("No ticket created")
        
        visit_data = {
            "ticket_id": TestServiceVisitsAPI.test_ticket_id,
            "technician_id": STAFF_ID,
            "scheduled_date": datetime.now().strftime("%Y-%m-%d"),
            "scheduled_time_from": "10:00",
            "scheduled_time_to": "12:00",
            "purpose": "Initial diagnosis"
        }
        response = requests.post(f"{BASE_URL}/api/admin/visits", json=visit_data, headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["status"] == "scheduled"
        assert data["visit_number"] == 1
        TestServiceVisitsAPI.created_visit_id = data["id"]
        print(f"✓ Created visit #{data['visit_number']} (Status: {data['status']})")
    
    def test_list_visits(self, auth_headers):
        """GET /api/admin/visits - List all visits"""
        response = requests.get(f"{BASE_URL}/api/admin/visits", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "visits" in data
        assert "total" in data
        print(f"✓ Found {data['total']} visits")
    
    def test_get_todays_visits(self, auth_headers):
        """GET /api/admin/visits/today - Get today's visits"""
        response = requests.get(f"{BASE_URL}/api/admin/visits/today", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "visits" in data
        assert "date" in data
        print(f"✓ Found {len(data['visits'])} visits for today")
    
    def test_get_technician_visits(self, auth_headers):
        """GET /api/admin/visits/technician/{id} - Get technician's visits"""
        response = requests.get(
            f"{BASE_URL}/api/admin/visits/technician/{STAFF_ID}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "visits" in data
        print(f"✓ Found {len(data['visits'])} visits for technician")
    
    def test_get_visit(self, auth_headers):
        """GET /api/admin/visits/{id} - Get specific visit"""
        if not TestServiceVisitsAPI.created_visit_id:
            pytest.skip("No visit created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/visits/{TestServiceVisitsAPI.created_visit_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == TestServiceVisitsAPI.created_visit_id
        assert "ticket" in data
        print(f"✓ Retrieved visit #{data['visit_number']}")
    
    def test_update_visit(self, auth_headers):
        """PUT /api/admin/visits/{id} - Update visit"""
        if not TestServiceVisitsAPI.created_visit_id:
            pytest.skip("No visit created")
        
        update_data = {
            "purpose": "Updated purpose for testing",
            "scheduled_time_from": "11:00"
        }
        response = requests.put(
            f"{BASE_URL}/api/admin/visits/{TestServiceVisitsAPI.created_visit_id}",
            json=update_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["purpose"] == "Updated purpose for testing"
        print(f"✓ Updated visit purpose")
    
    def test_start_timer(self, auth_headers):
        """POST /api/admin/visits/{id}/start-timer - Start visit timer"""
        if not TestServiceVisitsAPI.created_visit_id:
            pytest.skip("No visit created")
        
        response = requests.post(
            f"{BASE_URL}/api/admin/visits/{TestServiceVisitsAPI.created_visit_id}/start-timer",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["start_time"] is not None
        print(f"✓ Started timer (Status: {data['status']})")
    
    def test_add_action(self, auth_headers):
        """POST /api/admin/visits/{id}/add-action - Add action to visit"""
        if not TestServiceVisitsAPI.created_visit_id:
            pytest.skip("No visit created")
        
        action_data = {
            "action": "Diagnosed the issue"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/visits/{TestServiceVisitsAPI.created_visit_id}/add-action",
            json=action_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        print(f"✓ Added action to visit")
    
    def test_stop_timer(self, auth_headers):
        """POST /api/admin/visits/{id}/stop-timer - Stop visit timer"""
        if not TestServiceVisitsAPI.created_visit_id:
            pytest.skip("No visit created")
        
        stop_data = {
            "diagnostics": "Found hardware issue",
            "actions_taken": ["Diagnosed issue", "Replaced component"],
            "work_summary": "Completed repair",
            "outcome": "resolved",
            "customer_name": "Test Customer"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/visits/{TestServiceVisitsAPI.created_visit_id}/stop-timer",
            json=stop_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "completed"
        assert data["end_time"] is not None
        assert data["duration_minutes"] >= 0
        print(f"✓ Stopped timer (Duration: {data['duration_minutes']} minutes)")


# ==================== TICKET PARTS TESTS ====================

class TestTicketPartsAPI:
    """Tests for Ticket Parts API - Parts request workflow"""
    
    test_ticket_id = None
    test_item_id = None
    test_location_id = None
    created_request_id = None
    created_issue_id = None
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self, auth_headers):
        """Create test data for parts tests"""
        # Create test ticket
        ticket_data = {
            "company_id": COMPANY_ID,
            "title": f"TEST_PartsTicket_{uuid.uuid4().hex[:8]}",
            "description": "Ticket for parts testing",
            "priority": "high",
            "assigned_to_id": STAFF_ID
        }
        response = requests.post(f"{BASE_URL}/api/admin/service-tickets", json=ticket_data, headers=auth_headers)
        if response.status_code == 200:
            TestTicketPartsAPI.test_ticket_id = response.json()["id"]
            # Start work on ticket
            requests.post(f"{BASE_URL}/api/admin/service-tickets/{TestTicketPartsAPI.test_ticket_id}/start", headers=auth_headers)
        
        # Create test item
        item_data = {
            "name": f"TEST_PartsItem_{uuid.uuid4().hex[:8]}",
            "sku": f"PRT-{uuid.uuid4().hex[:6].upper()}",
            "category": "part",
            "unit_price": 500.00,
            "cost_price": 300.00
        }
        response = requests.post(f"{BASE_URL}/api/admin/items", json=item_data, headers=auth_headers)
        if response.status_code == 200:
            TestTicketPartsAPI.test_item_id = response.json()["id"]
        
        # Create test location
        location_data = {
            "name": f"TEST_PartsLoc_{uuid.uuid4().hex[:8]}",
            "code": f"PL-{uuid.uuid4().hex[:4].upper()}",
            "location_type": "warehouse"
        }
        response = requests.post(f"{BASE_URL}/api/admin/inventory/locations", json=location_data, headers=auth_headers)
        if response.status_code == 200:
            TestTicketPartsAPI.test_location_id = response.json()["id"]
            
            # Add stock to location
            if TestTicketPartsAPI.test_item_id:
                adjustment_data = {
                    "item_id": TestTicketPartsAPI.test_item_id,
                    "location_id": TestTicketPartsAPI.test_location_id,
                    "quantity": 100,
                    "reason": "Initial stock for parts testing"
                }
                requests.post(f"{BASE_URL}/api/admin/inventory/stock/adjustment", json=adjustment_data, headers=auth_headers)
    
    def test_create_part_request(self, auth_headers):
        """POST /api/admin/ticket-parts/requests - Create parts request"""
        if not TestTicketPartsAPI.test_ticket_id or not TestTicketPartsAPI.test_item_id:
            pytest.skip("Test data not created")
        
        request_data = {
            "ticket_id": TestTicketPartsAPI.test_ticket_id,
            "item_id": TestTicketPartsAPI.test_item_id,
            "quantity_requested": 2,
            "request_notes": "Need parts for repair",
            "urgency": "urgent"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/ticket-parts/requests",
            json=request_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["status"] == "requested"
        assert data["quantity_requested"] == 2
        TestTicketPartsAPI.created_request_id = data["id"]
        print(f"✓ Created parts request (Status: {data['status']})")
    
    def test_list_part_requests(self, auth_headers):
        """GET /api/admin/ticket-parts/requests - List parts requests"""
        response = requests.get(f"{BASE_URL}/api/admin/ticket-parts/requests", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "requests" in data
        assert "total" in data
        print(f"✓ Found {data['total']} parts requests")
    
    def test_get_pending_requests(self, auth_headers):
        """GET /api/admin/ticket-parts/requests/pending - Get pending requests"""
        response = requests.get(f"{BASE_URL}/api/admin/ticket-parts/requests/pending", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "requests" in data
        print(f"✓ Found {len(data['requests'])} pending requests")
    
    def test_get_part_request(self, auth_headers):
        """GET /api/admin/ticket-parts/requests/{id} - Get specific request"""
        if not TestTicketPartsAPI.created_request_id:
            pytest.skip("No request created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/ticket-parts/requests/{TestTicketPartsAPI.created_request_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == TestTicketPartsAPI.created_request_id
        print(f"✓ Retrieved parts request")
    
    def test_approve_part_request(self, auth_headers):
        """POST /api/admin/ticket-parts/requests/{id}/approve - Approve request"""
        if not TestTicketPartsAPI.created_request_id:
            pytest.skip("No request created")
        
        approval_data = {
            "approved": True,
            "quantity_approved": 2,
            "notes": "Approved for testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/ticket-parts/requests/{TestTicketPartsAPI.created_request_id}/approve",
            json=approval_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["status"] == "approved"
        assert data["quantity_approved"] == 2
        print(f"✓ Approved parts request (Qty: {data['quantity_approved']})")
    
    def test_issue_part(self, auth_headers):
        """POST /api/admin/ticket-parts/issues - Issue parts to ticket"""
        if not TestTicketPartsAPI.test_ticket_id or not TestTicketPartsAPI.test_item_id or not TestTicketPartsAPI.test_location_id:
            pytest.skip("Test data not created")
        
        issue_data = {
            "ticket_id": TestTicketPartsAPI.test_ticket_id,
            "part_request_id": TestTicketPartsAPI.created_request_id,
            "item_id": TestTicketPartsAPI.test_item_id,
            "quantity_issued": 2,
            "issued_from_location_id": TestTicketPartsAPI.test_location_id,
            "received_by_id": STAFF_ID,
            "is_billable": True,
            "notes": "Issued for testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/ticket-parts/issues",
            json=issue_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "id" in data
        assert data["quantity_issued"] == 2
        TestTicketPartsAPI.created_issue_id = data["id"]
        print(f"✓ Issued {data['quantity_issued']} parts to ticket")
    
    def test_list_part_issues(self, auth_headers):
        """GET /api/admin/ticket-parts/issues - List parts issued"""
        response = requests.get(f"{BASE_URL}/api/admin/ticket-parts/issues", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "issues" in data
        assert "total" in data
        print(f"✓ Found {data['total']} parts issued")
    
    def test_get_part_issue(self, auth_headers):
        """GET /api/admin/ticket-parts/issues/{id} - Get specific issue"""
        if not TestTicketPartsAPI.created_issue_id:
            pytest.skip("No issue created")
        
        response = requests.get(
            f"{BASE_URL}/api/admin/ticket-parts/issues/{TestTicketPartsAPI.created_issue_id}",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["id"] == TestTicketPartsAPI.created_issue_id
        print(f"✓ Retrieved parts issue")
    
    def test_return_part(self, auth_headers):
        """POST /api/admin/ticket-parts/issues/{id}/return - Return unused parts"""
        if not TestTicketPartsAPI.created_issue_id or not TestTicketPartsAPI.test_location_id:
            pytest.skip("Test data not created")
        
        return_data = {
            "quantity_returned": 1,
            "return_location_id": TestTicketPartsAPI.test_location_id,
            "return_reason": "Unused part returned"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/ticket-parts/issues/{TestTicketPartsAPI.created_issue_id}/return",
            json=return_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["quantity_returned"] == 1
        assert data["quantity_used"] == 1  # 2 issued - 1 returned
        print(f"✓ Returned 1 part (Used: {data['quantity_used']})")


# ==================== STOCK TRANSFER TEST ====================

class TestStockTransferAPI:
    """Tests for Stock Transfer operations"""
    
    def test_stock_transfer(self, auth_headers):
        """POST /api/admin/inventory/stock/transfer - Transfer stock between locations"""
        # Create source location
        source_loc_data = {
            "name": f"TEST_SourceLoc_{uuid.uuid4().hex[:8]}",
            "code": f"SRC-{uuid.uuid4().hex[:4].upper()}",
            "location_type": "warehouse"
        }
        response = requests.post(f"{BASE_URL}/api/admin/inventory/locations", json=source_loc_data, headers=auth_headers)
        assert response.status_code == 200
        source_loc_id = response.json()["id"]
        
        # Create destination location
        dest_loc_data = {
            "name": f"TEST_DestLoc_{uuid.uuid4().hex[:8]}",
            "code": f"DST-{uuid.uuid4().hex[:4].upper()}",
            "location_type": "van"
        }
        response = requests.post(f"{BASE_URL}/api/admin/inventory/locations", json=dest_loc_data, headers=auth_headers)
        assert response.status_code == 200
        dest_loc_id = response.json()["id"]
        
        # Create test item
        item_data = {
            "name": f"TEST_TransferItem_{uuid.uuid4().hex[:8]}",
            "sku": f"TRF-{uuid.uuid4().hex[:6].upper()}",
            "category": "part"
        }
        response = requests.post(f"{BASE_URL}/api/admin/items", json=item_data, headers=auth_headers)
        assert response.status_code == 200
        item_id = response.json()["id"]
        
        # Add stock to source location
        adjustment_data = {
            "item_id": item_id,
            "location_id": source_loc_id,
            "quantity": 50,
            "reason": "Initial stock for transfer test"
        }
        response = requests.post(f"{BASE_URL}/api/admin/inventory/stock/adjustment", json=adjustment_data, headers=auth_headers)
        assert response.status_code == 200
        
        # Transfer stock
        transfer_data = {
            "item_id": item_id,
            "from_location_id": source_loc_id,
            "to_location_id": dest_loc_id,
            "quantity": 20,
            "notes": "Transfer for testing"
        }
        response = requests.post(
            f"{BASE_URL}/api/admin/inventory/stock/transfer",
            json=transfer_data,
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data["success"] == True
        assert "transfer_id" in data
        print(f"✓ Transferred 20 units between locations")
        
        # Verify stock at destination
        response = requests.get(
            f"{BASE_URL}/api/admin/inventory/stock/location/{dest_loc_id}",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) > 0
        print(f"✓ Verified stock at destination location")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
