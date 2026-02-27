"""
Quotation API Tests - Item Master Integration
==============================================
Tests for the new Quotation CRUD APIs including:
1. Admin Quotation CRUD (POST, GET, PUT, DELETE, SEND)
2. GST calculation correctness (per-line and totals)
3. Company quotation view and approval/rejection
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
ADMIN_API = f"{BASE_URL}/api/admin/quotations"
COMPANY_API = f"{BASE_URL}/api/company/quotations"
ITEM_MASTER_API = f"{BASE_URL}/api/admin/item-master"

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"

@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code != 200:
        pytest.skip("Admin authentication failed")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def headers(admin_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {admin_token}", "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def item_master_products(headers):
    """Get products from Item Master to use in quotation tests"""
    response = requests.get(f"{ITEM_MASTER_API}/products?limit=10", headers=headers)
    if response.status_code == 200:
        products = response.json().get("products", [])
        if products:
            return products
    pytest.skip("No Item Master products available for testing")


# =============================================================================
# ADMIN QUOTATION CRUD TESTS
# =============================================================================

class TestAdminQuotationCRUD:
    """Admin Quotation CRUD API Tests"""
    
    def test_create_quotation_with_line_items(self, headers, item_master_products):
        """Test creating a quotation with items from Item Master and auto GST calc"""
        # Use first 2 products from Item Master
        products = item_master_products[:2]
        
        items = []
        for prod in products:
            items.append({
                "product_id": prod["id"],
                "product_name": prod["name"],
                "sku": prod.get("sku", ""),
                "hsn_code": prod.get("hsn_code", ""),
                "quantity": 2,
                "unit_price": prod.get("unit_price", 1000),
                "gst_slab": prod.get("gst_slab", 18),
                "description": "Test item"
            })
        
        payload = {
            "ticket_id": "test-ticket-123",
            "ticket_number": "TKT-TEST-001",
            "company_id": "test-company-123",
            "company_name": "Test Company",
            "items": items,
            "notes": "TEST_Quotation notes",
            "terms_and_conditions": "Payment due within 30 days",
            "valid_days": 30
        }
        
        response = requests.post(ADMIN_API, headers=headers, json=payload)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        data = response.json()
        assert "id" in data
        assert "quotation_number" in data
        assert data["quotation_number"].startswith("QT-")
        assert data["status"] == "draft"
        assert len(data["items"]) == len(items)
        
        # Verify GST calculation
        assert "subtotal" in data
        assert "total_gst" in data
        assert "grand_total" in data
        assert data["grand_total"] == data["subtotal"] + data["total_gst"]
        
        # Store for later tests
        TestAdminQuotationCRUD.created_quotation_id = data["id"]
        TestAdminQuotationCRUD.created_quotation_number = data["quotation_number"]
        
        print(f"Created quotation: {data['quotation_number']}")
        print(f"Subtotal: {data['subtotal']}, GST: {data['total_gst']}, Grand Total: {data['grand_total']}")
    
    def test_create_quotation_requires_items(self, headers):
        """Test that quotation creation fails without items"""
        payload = {
            "ticket_id": "test-ticket-123",
            "items": [],
            "notes": "Should fail"
        }
        
        response = requests.post(ADMIN_API, headers=headers, json=payload)
        assert response.status_code == 400
        assert "item" in response.json().get("detail", "").lower()
    
    def test_list_quotations(self, headers):
        """Test listing quotations with pagination"""
        response = requests.get(ADMIN_API, headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "quotations" in data
        assert "total" in data
        assert "page" in data
        
        # Should contain our created quotation
        quotations = data["quotations"]
        assert len(quotations) > 0
        
        # Check quotation structure
        q = quotations[0]
        assert "id" in q
        assert "quotation_number" in q
        assert "status" in q
        assert "items" in q
        
        print(f"Found {data['total']} quotations")
    
    def test_get_single_quotation(self, headers):
        """Test getting a single quotation by ID"""
        quotation_id = getattr(TestAdminQuotationCRUD, 'created_quotation_id', None)
        if not quotation_id:
            pytest.skip("No test quotation created")
        
        response = requests.get(f"{ADMIN_API}/{quotation_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == quotation_id
        assert "items" in data
        assert "subtotal" in data
        assert "total_gst" in data
        assert "grand_total" in data
        
        # Verify each line item has GST calculated
        for item in data["items"]:
            assert "gst_amount" in item
            assert "line_total" in item
            
            # Verify GST calculation: line_total = (unit_price * quantity) + gst_amount
            expected_base = item["unit_price"] * item["quantity"]
            expected_gst = expected_base * item["gst_slab"] / 100
            assert abs(item["gst_amount"] - expected_gst) < 0.01, f"GST mismatch: {item['gst_amount']} vs {expected_gst}"
    
    def test_update_draft_quotation(self, headers, item_master_products):
        """Test updating a draft quotation"""
        quotation_id = getattr(TestAdminQuotationCRUD, 'created_quotation_id', None)
        if not quotation_id:
            pytest.skip("No test quotation created")
        
        # Update with different items
        products = item_master_products[:1]
        new_items = [{
            "product_id": products[0]["id"],
            "product_name": products[0]["name"],
            "quantity": 5,
            "unit_price": 2000,
            "gst_slab": 18
        }]
        
        payload = {
            "items": new_items,
            "notes": "Updated TEST_Quotation notes"
        }
        
        response = requests.put(f"{ADMIN_API}/{quotation_id}", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["items"]) == 1
        assert data["items"][0]["quantity"] == 5
        assert data["notes"] == "Updated TEST_Quotation notes"
        
        # Verify recalculated totals
        expected_subtotal = 2000 * 5
        expected_gst = expected_subtotal * 18 / 100
        assert data["subtotal"] == expected_subtotal
        assert data["total_gst"] == expected_gst
        assert data["grand_total"] == expected_subtotal + expected_gst
    
    def test_send_quotation(self, headers):
        """Test sending a draft quotation"""
        quotation_id = getattr(TestAdminQuotationCRUD, 'created_quotation_id', None)
        if not quotation_id:
            pytest.skip("No test quotation created")
        
        response = requests.post(f"{ADMIN_API}/{quotation_id}/send", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "sent"
        assert "sent_at" in data
        
        print(f"Quotation sent: {data['quotation_number']}")
    
    def test_cannot_update_sent_quotation(self, headers):
        """Test that sent quotation cannot be edited"""
        quotation_id = getattr(TestAdminQuotationCRUD, 'created_quotation_id', None)
        if not quotation_id:
            pytest.skip("No test quotation created")
        
        payload = {"notes": "Should fail"}
        response = requests.put(f"{ADMIN_API}/{quotation_id}", headers=headers, json=payload)
        assert response.status_code == 400
        assert "draft" in response.json().get("detail", "").lower()
    
    def test_cannot_send_already_sent_quotation(self, headers):
        """Test that already sent quotation cannot be sent again"""
        quotation_id = getattr(TestAdminQuotationCRUD, 'created_quotation_id', None)
        if not quotation_id:
            pytest.skip("No test quotation created")
        
        response = requests.post(f"{ADMIN_API}/{quotation_id}/send", headers=headers)
        assert response.status_code == 400
        assert "already sent" in response.json().get("detail", "").lower()


# =============================================================================
# GST CALCULATION TESTS
# =============================================================================

class TestGSTCalculation:
    """Test GST calculation correctness"""
    
    def test_gst_calculation_per_line_item(self, headers):
        """Test that GST is calculated correctly per line item"""
        items = [
            {"product_name": "Item 1", "quantity": 1, "unit_price": 1000, "gst_slab": 18},
            {"product_name": "Item 2", "quantity": 2, "unit_price": 500, "gst_slab": 12},
            {"product_name": "Item 3", "quantity": 3, "unit_price": 200, "gst_slab": 5},
        ]
        
        payload = {
            "ticket_id": "gst-test-ticket",
            "items": items,
            "notes": "GST calculation test"
        }
        
        response = requests.post(ADMIN_API, headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        
        # Verify each line item GST
        # Item 1: 1000 * 1 = 1000 base, GST 18% = 180, total = 1180
        assert data["items"][0]["gst_amount"] == 180
        assert data["items"][0]["line_total"] == 1180
        
        # Item 2: 500 * 2 = 1000 base, GST 12% = 120, total = 1120
        assert data["items"][1]["gst_amount"] == 120
        assert data["items"][1]["line_total"] == 1120
        
        # Item 3: 200 * 3 = 600 base, GST 5% = 30, total = 630
        assert data["items"][2]["gst_amount"] == 30
        assert data["items"][2]["line_total"] == 630
        
        # Verify totals
        expected_subtotal = 1000 + 1000 + 600  # 2600
        expected_gst = 180 + 120 + 30  # 330
        expected_grand = 2600 + 330  # 2930
        
        assert data["subtotal"] == expected_subtotal
        assert data["total_gst"] == expected_gst
        assert data["grand_total"] == expected_grand
        
        # Cleanup - delete this test quotation
        requests.delete(f"{ADMIN_API}/{data['id']}", headers=headers)
        
        print(f"GST calculation verified: Subtotal={expected_subtotal}, GST={expected_gst}, Grand Total={expected_grand}")
    
    def test_gst_zero_slab(self, headers):
        """Test that 0% GST is handled correctly"""
        items = [
            {"product_name": "Zero GST Item", "quantity": 1, "unit_price": 1000, "gst_slab": 0}
        ]
        
        payload = {"ticket_id": "gst-zero-test", "items": items}
        
        response = requests.post(ADMIN_API, headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"][0]["gst_amount"] == 0
        assert data["items"][0]["line_total"] == 1000
        assert data["total_gst"] == 0
        assert data["grand_total"] == 1000
        
        requests.delete(f"{ADMIN_API}/{data['id']}", headers=headers)
    
    def test_gst_28_percent_slab(self, headers):
        """Test 28% GST calculation"""
        items = [
            {"product_name": "High GST Item", "quantity": 1, "unit_price": 1000, "gst_slab": 28}
        ]
        
        payload = {"ticket_id": "gst-28-test", "items": items}
        
        response = requests.post(ADMIN_API, headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["items"][0]["gst_amount"] == 280
        assert data["items"][0]["line_total"] == 1280
        assert data["total_gst"] == 280
        assert data["grand_total"] == 1280
        
        requests.delete(f"{ADMIN_API}/{data['id']}", headers=headers)


# =============================================================================
# COMPANY QUOTATION TESTS
# =============================================================================

class TestCompanyQuotations:
    """Test company portal quotation endpoints"""
    
    @pytest.fixture
    def company_token(self):
        """Try to get company user token (may not exist in all envs)"""
        # First try with known test credentials
        response = requests.post(f"{BASE_URL}/api/company/auth/login", json={
            "email": "testuser@testcompany.com",
            "password": "Test@123"
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        
        # If no company user, skip these tests
        pytest.skip("Company user authentication not available")
    
    def test_company_list_quotations_endpoint_exists(self, headers):
        """Test that company quotations endpoint is accessible (admin can't access it)"""
        response = requests.get(COMPANY_API, headers=headers)
        # Should return 403 for admin or 401 if wrong auth
        # This verifies the endpoint exists and has auth
        assert response.status_code in [401, 403, 422]
    
    def test_company_respond_endpoint_exists(self, headers):
        """Test that company respond endpoint exists"""
        # Try with invalid ID - should return auth error, not 404
        response = requests.post(
            f"{COMPANY_API}/fake-id/respond",
            headers=headers,
            params={"approved": True}
        )
        # Should return 403 for admin user
        assert response.status_code in [401, 403, 422]


# =============================================================================
# QUOTATION DELETION TESTS
# =============================================================================

class TestQuotationDeletion:
    """Test quotation deletion"""
    
    def test_delete_quotation(self, headers):
        """Test deleting a quotation"""
        # Create a quotation to delete
        items = [{"product_name": "Delete Test", "quantity": 1, "unit_price": 100, "gst_slab": 18}]
        create_response = requests.post(ADMIN_API, headers=headers, json={"items": items})
        assert create_response.status_code == 200
        
        quotation_id = create_response.json()["id"]
        
        # Delete it
        response = requests.delete(f"{ADMIN_API}/{quotation_id}", headers=headers)
        assert response.status_code == 200
        assert response.json().get("success") is True
        
        # Verify it's gone (soft deleted)
        get_response = requests.get(f"{ADMIN_API}/{quotation_id}", headers=headers)
        assert get_response.status_code == 404
    
    def test_delete_nonexistent_quotation(self, headers):
        """Test deleting non-existent quotation returns 404"""
        response = requests.delete(f"{ADMIN_API}/nonexistent-id-12345", headers=headers)
        assert response.status_code == 404


# =============================================================================
# ITEM MASTER INTEGRATION TESTS
# =============================================================================

class TestItemMasterIntegration:
    """Test Item Master integration with quotations"""
    
    def test_product_suggestions_for_quotation(self, headers):
        """Test getting product suggestions for quotation"""
        # Get products with bundles
        products_response = requests.get(f"{ITEM_MASTER_API}/products", headers=headers)
        products = products_response.json().get("products", [])
        
        if not products:
            pytest.skip("No products available")
        
        # Try to get suggestions for first product
        product_id = products[0]["id"]
        response = requests.get(f"{ITEM_MASTER_API}/products/{product_id}/suggestions", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestions" in data
        
        print(f"Product {products[0]['name']} has {len(data['suggestions'])} suggestions")


# =============================================================================
# CLEANUP
# =============================================================================

class TestCleanup:
    """Cleanup test data"""
    
    def test_cleanup_test_quotation(self, headers):
        """Delete the test quotation created during tests"""
        quotation_id = getattr(TestAdminQuotationCRUD, 'created_quotation_id', None)
        if quotation_id:
            requests.delete(f"{ADMIN_API}/{quotation_id}", headers=headers)
            print(f"Cleaned up test quotation: {quotation_id}")
