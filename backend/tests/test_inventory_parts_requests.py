"""
Tests for Inventory Management and Parts Requests APIs
========================================================
- Admin Inventory API: list, adjust, history
- Item Master bulk CSV upload with duplicate detection
- Admin Parts Requests: list, filter by status, update status
"""

import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"


class TestAuth:
    """Get authentication token for testing."""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token."""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        token = data.get("access_token")
        assert token, "No access_token in response"
        return token

    @pytest.fixture(scope="class")
    def auth_headers(self, admin_token):
        """Headers with authentication."""
        return {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json"
        }


class TestInventoryAPI(TestAuth):
    """Tests for Inventory management endpoints."""

    def test_list_inventory(self, auth_headers):
        """GET /api/admin/inventory - List inventory items."""
        response = requests.get(f"{BASE_URL}/api/admin/inventory", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        items = data["items"]
        if items:
            item = items[0]
            assert "id" in item
            assert "name" in item
            assert "quantity_in_stock" in item
            assert "total_purchased" in item
            assert "total_used" in item
            print(f"Found {len(items)} inventory items")

    def test_inventory_search(self, auth_headers):
        """GET /api/admin/inventory?search=... - Search inventory."""
        response = requests.get(f"{BASE_URL}/api/admin/inventory?search=cat6", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        items = data.get("items", [])
        # Search should filter results
        for item in items:
            assert "cat6" in item["name"].lower() or "cat6" in (item.get("sku") or "").lower()
        print(f"Search returned {len(items)} items")

    def test_stock_adjustment_purchase(self, auth_headers):
        """POST /api/admin/inventory/adjust - Add stock via purchase."""
        # First get an inventory item
        list_response = requests.get(f"{BASE_URL}/api/admin/inventory", headers=auth_headers)
        items = list_response.json().get("items", [])
        if not items:
            pytest.skip("No inventory items to test adjustment")
        
        product_id = items[0]["id"]
        original_stock = items[0]["quantity_in_stock"]
        
        # Make adjustment
        response = requests.post(
            f"{BASE_URL}/api/admin/inventory/adjust",
            headers=auth_headers,
            json={
                "product_id": product_id,
                "quantity": 2,
                "type": "purchase",
                "unit_cost": 100,
                "notes": "Test adjustment via pytest"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert "inventory" in data
        assert data["inventory"]["quantity_in_stock"] == original_stock + 2
        assert "message" in data
        print(f"Stock adjusted from {original_stock} to {original_stock + 2}")

    def test_stock_adjustment_return(self, auth_headers):
        """POST /api/admin/inventory/adjust - Add stock via return."""
        list_response = requests.get(f"{BASE_URL}/api/admin/inventory", headers=auth_headers)
        items = list_response.json().get("items", [])
        if not items:
            pytest.skip("No inventory items")
        
        product_id = items[0]["id"]
        
        response = requests.post(
            f"{BASE_URL}/api/admin/inventory/adjust",
            headers=auth_headers,
            json={
                "product_id": product_id,
                "quantity": 1,
                "type": "return",
                "notes": "Return test"
            }
        )
        assert response.status_code == 200
        assert "inventory" in response.json()

    def test_inventory_history(self, auth_headers):
        """GET /api/admin/inventory/{product_id}/history - Get transaction history."""
        list_response = requests.get(f"{BASE_URL}/api/admin/inventory", headers=auth_headers)
        items = list_response.json().get("items", [])
        if not items:
            pytest.skip("No inventory items")
        
        product_id = items[0]["id"]
        
        response = requests.get(f"{BASE_URL}/api/admin/inventory/{product_id}/history", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "product" in data
        assert "inventory" in data
        assert "transactions" in data
        
        product = data["product"]
        assert product["id"] == product_id
        
        inventory = data["inventory"]
        assert "quantity_in_stock" in inventory
        assert "total_purchased" in inventory
        assert "total_used" in inventory
        
        print(f"Product: {product['name']}, Stock: {inventory['quantity_in_stock']}, Transactions: {len(data['transactions'])}")

    def test_inventory_history_with_ticket_details(self, auth_headers):
        """Verify transaction history includes ticket details for 'used' transactions."""
        list_response = requests.get(f"{BASE_URL}/api/admin/inventory", headers=auth_headers)
        items = list_response.json().get("items", [])
        
        for item in items:
            hist_response = requests.get(f"{BASE_URL}/api/admin/inventory/{item['id']}/history", headers=auth_headers)
            if hist_response.status_code == 200:
                txns = hist_response.json().get("transactions", [])
                used_txns = [t for t in txns if t["type"] == "used"]
                for txn in used_txns:
                    # Used transactions should have ticket_id and potentially ticket_details
                    if txn.get("ticket_id"):
                        assert "ticket_details" in txn or txn.get("ticket_number"), "Used transactions should have ticket info"
                        print(f"Found used transaction with job details: {txn.get('reference')}")
                        return
        print("No 'used' transactions found to verify ticket details")


class TestBulkUploadAPI(TestAuth):
    """Tests for Item Master bulk CSV upload."""

    def test_download_sample_csv(self, admin_token):
        """GET /api/admin/item-master/bulk-upload/sample - Download sample CSV."""
        response = requests.get(
            f"{BASE_URL}/api/admin/item-master/bulk-upload/sample",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("Content-Type", "")
        
        content = response.text
        assert "name,sku,category" in content
        assert "initial_stock" in content
        assert "reorder_level" in content
        print("Sample CSV downloaded successfully")

    def test_bulk_upload_creates_products(self, admin_token):
        """POST /api/admin/item-master/bulk-upload - Upload new products."""
        csv_content = """name,sku,category,part_number,brand,manufacturer,description,unit_price,gst_slab,hsn_code,unit_of_measure,initial_stock,reorder_level
TEST_UNIQUE_PRODUCT_XYZ123,TEST-SKU-XYZ123,Security,TXYZ123,TestBrand,TestMfg,Test Product,500,18,85258090,unit,10,5"""
        
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = requests.post(
            f"{BASE_URL}/api/admin/item-master/bulk-upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert "created" in data
        assert "skipped" in data
        assert "errors" in data
        print(f"Bulk upload: {data['created']} created, {data['skipped']} skipped")

    def test_bulk_upload_duplicate_sku_detection(self, admin_token):
        """POST /api/admin/item-master/bulk-upload - Duplicate SKU rejected."""
        # First get an existing product with SKU
        list_resp = requests.get(
            f"{BASE_URL}/api/admin/item-master/products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        products = list_resp.json().get("products", [])
        existing_sku = None
        for p in products:
            if p.get("sku"):
                existing_sku = p["sku"]
                break
        
        if not existing_sku:
            pytest.skip("No products with SKU to test duplicate detection")
        
        csv_content = f"""name,sku,category,part_number,brand,manufacturer,description,unit_price,gst_slab,hsn_code,unit_of_measure,initial_stock,reorder_level
Duplicate Test Product,{existing_sku},Security,DUP123,TestBrand,TestMfg,Duplicate test,500,18,85258090,unit,0,5"""
        
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        response = requests.post(
            f"{BASE_URL}/api/admin/item-master/bulk-upload",
            headers={"Authorization": f"Bearer {admin_token}"},
            files=files
        )
        assert response.status_code == 200
        data = response.json()
        assert data["skipped"] > 0 or len(data.get("errors", [])) > 0
        # Check error reason mentions duplicate
        errors = data.get("errors", [])
        if errors:
            assert any("duplicate" in str(e.get("reason", "")).lower() for e in errors)
        print(f"Duplicate SKU correctly rejected: {data['errors']}")


class TestPartsRequestsAPI(TestAuth):
    """Tests for Admin Parts Requests management."""

    def test_list_parts_requests(self, auth_headers):
        """GET /api/admin/parts-requests - List all parts requests."""
        response = requests.get(f"{BASE_URL}/api/admin/parts-requests", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "parts_requests" in data
        assert "total" in data
        
        requests_list = data["parts_requests"]
        if requests_list:
            pr = requests_list[0]
            assert "id" in pr
            assert "status" in pr
            assert "items" in pr
            assert "engineer_name" in pr
            print(f"Found {len(requests_list)} parts requests")

    def test_filter_parts_requests_by_status(self, auth_headers):
        """GET /api/admin/parts-requests?status=... - Filter by status."""
        # Get all first to know what statuses exist
        all_resp = requests.get(f"{BASE_URL}/api/admin/parts-requests", headers=auth_headers)
        all_prs = all_resp.json().get("parts_requests", [])
        
        if not all_prs:
            pytest.skip("No parts requests to test filtering")
        
        # Get unique statuses
        statuses = set(pr["status"] for pr in all_prs)
        
        for status in statuses:
            response = requests.get(f"{BASE_URL}/api/admin/parts-requests?status={status}", headers=auth_headers)
            assert response.status_code == 200
            filtered = response.json().get("parts_requests", [])
            for pr in filtered:
                assert pr["status"] == status
            print(f"Filter by '{status}': {len(filtered)} results")

    def test_parts_request_has_items_detail(self, auth_headers):
        """Verify parts requests contain items with pricing details."""
        response = requests.get(f"{BASE_URL}/api/admin/parts-requests", headers=auth_headers)
        prs = response.json().get("parts_requests", [])
        
        if not prs:
            pytest.skip("No parts requests")
        
        for pr in prs[:3]:  # Check first 3
            items = pr.get("items", [])
            assert isinstance(items, list)
            for item in items:
                assert "product_name" in item
                assert "quantity" in item
                assert "unit_price" in item
                assert "gst_amount" in item
                assert "line_total" in item
            
            # Check totals
            assert "subtotal" in pr
            assert "total_gst" in pr
            assert "grand_total" in pr
        print("Parts request items verified")

    def test_parts_request_status_advancement(self, auth_headers):
        """PUT /api/admin/parts-requests/{id}/status - Update status."""
        # Get a parts request
        list_resp = requests.get(f"{BASE_URL}/api/admin/parts-requests", headers=auth_headers)
        prs = list_resp.json().get("parts_requests", [])
        
        if not prs:
            pytest.skip("No parts requests to test status update")
        
        # Find one that's not delivered
        pr = None
        for p in prs:
            if p["status"] != "delivered":
                pr = p
                break
        
        if not pr:
            pytest.skip("All parts requests already delivered")
        
        pr_id = pr["id"]
        current_status = pr["status"]
        
        # Status progression: pending -> quoted -> approved -> procured -> delivered
        status_order = ["pending", "quoted", "approved", "procured", "delivered"]
        current_idx = status_order.index(current_status)
        if current_idx < len(status_order) - 1:
            next_status = status_order[current_idx + 1]
            
            response = requests.put(
                f"{BASE_URL}/api/admin/parts-requests/{pr_id}/status?status={next_status}",
                headers=auth_headers
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == next_status
            print(f"Status updated from '{current_status}' to '{next_status}'")

    def test_parts_request_engineer_info(self, auth_headers):
        """Verify parts requests show engineer information."""
        response = requests.get(f"{BASE_URL}/api/admin/parts-requests", headers=auth_headers)
        prs = response.json().get("parts_requests", [])
        
        for pr in prs[:3]:
            assert "engineer_name" in pr, "Parts request should have engineer_name"
            assert "engineer_id" in pr, "Parts request should have engineer_id"
            if pr.get("quotation_id"):
                print(f"Parts request {pr['id']} has linked quotation: {pr['quotation_id']}")


class TestItemMasterProducts(TestAuth):
    """Additional tests for Item Master products."""

    def test_list_products(self, auth_headers):
        """GET /api/admin/item-master/products - List products."""
        response = requests.get(f"{BASE_URL}/api/admin/item-master/products", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "products" in data
        print(f"Found {len(data['products'])} products")

    def test_list_categories(self, auth_headers):
        """GET /api/admin/item-master/categories - List categories."""
        response = requests.get(f"{BASE_URL}/api/admin/item-master/categories", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        print(f"Found {len(data['categories'])} categories")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
