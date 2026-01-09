"""
Office Supplies Feature Tests
Tests for:
- Admin supply categories CRUD
- Admin supply products CRUD
- Company supply catalog
- Company supply orders
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data tracking for cleanup
created_categories = []
created_products = []
created_orders = []


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "admin@demo.com",
        "password": "admin123"
    })
    assert response.status_code == 200, f"Admin login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def company_token():
    """Get company user authentication token"""
    response = requests.post(f"{BASE_URL}/api/company/auth/login", json={
        "email": "jane@acme.com",
        "password": "company123"
    })
    assert response.status_code == 200, f"Company login failed: {response.text}"
    return response.json()["access_token"]


@pytest.fixture(scope="module")
def company_user_info():
    """Get company user info"""
    response = requests.post(f"{BASE_URL}/api/company/auth/login", json={
        "email": "jane@acme.com",
        "password": "company123"
    })
    return response.json().get("user", {})


class TestAdminSupplyCategories:
    """Admin supply category management tests"""
    
    def test_get_supply_categories_returns_seeded_data(self, admin_token):
        """GET /api/admin/supply-categories returns seeded categories"""
        response = requests.get(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        categories = response.json()
        assert isinstance(categories, list)
        
        # Check for seeded categories
        category_names = [c["name"] for c in categories]
        assert "Stationery" in category_names, "Seeded 'Stationery' category not found"
        assert "Printer Consumables" in category_names, "Seeded 'Printer Consumables' category not found"
        
        # Verify category structure
        for cat in categories:
            assert "id" in cat
            assert "name" in cat
            assert "is_active" in cat
    
    def test_create_supply_category(self, admin_token):
        """POST /api/admin/supply-categories creates new category"""
        test_name = f"TEST_Category_{uuid.uuid4().hex[:6]}"
        response = requests.post(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "name": test_name,
                "icon": "🧪",
                "description": "Test category for automated testing",
                "sort_order": 99
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == test_name
        assert data["icon"] == "🧪"
        assert data["description"] == "Test category for automated testing"
        assert data["sort_order"] == 99
        assert "id" in data
        
        created_categories.append(data["id"])
        
        # Verify persistence with GET
        get_response = requests.get(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert get_response.status_code == 200
        categories = get_response.json()
        found = any(c["id"] == data["id"] for c in categories)
        assert found, "Created category not found in list"
    
    def test_update_supply_category(self, admin_token):
        """PUT /api/admin/supply-categories/{id} updates category"""
        # First create a category
        test_name = f"TEST_UpdateCat_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": test_name, "icon": "📦"}
        )
        assert create_response.status_code == 200
        category_id = create_response.json()["id"]
        created_categories.append(category_id)
        
        # Update the category
        updated_name = f"TEST_Updated_{uuid.uuid4().hex[:6]}"
        update_response = requests.put(
            f"{BASE_URL}/api/admin/supply-categories/{category_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": updated_name, "icon": "📁", "description": "Updated description"}
        )
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data["name"] == updated_name
        assert data["icon"] == "📁"
        assert data["description"] == "Updated description"
    
    def test_delete_supply_category(self, admin_token):
        """DELETE /api/admin/supply-categories/{id} soft deletes category"""
        # Create a category to delete
        test_name = f"TEST_DeleteCat_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": test_name}
        )
        assert create_response.status_code == 200
        category_id = create_response.json()["id"]
        
        # Delete the category
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/supply-categories/{category_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Category deleted"
        
        # Verify it's no longer in the list
        get_response = requests.get(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = get_response.json()
        found = any(c["id"] == category_id for c in categories)
        assert not found, "Deleted category still appears in list"


class TestAdminSupplyProducts:
    """Admin supply product management tests"""
    
    def test_get_supply_products_returns_seeded_data(self, admin_token):
        """GET /api/admin/supply-products returns seeded products"""
        response = requests.get(
            f"{BASE_URL}/api/admin/supply-products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        products = response.json()
        assert isinstance(products, list)
        assert len(products) >= 16, f"Expected at least 16 seeded products, got {len(products)}"
        
        # Check for some seeded products
        product_names = [p["name"] for p in products]
        assert "A4 Paper (500 sheets)" in product_names, "Seeded 'A4 Paper' product not found"
        assert "Printer Ink - Black" in product_names, "Seeded 'Printer Ink - Black' product not found"
        
        # Verify product structure
        for product in products:
            assert "id" in product
            assert "name" in product
            assert "category_id" in product
            assert "unit" in product
            assert "is_active" in product
    
    def test_create_supply_product(self, admin_token):
        """POST /api/admin/supply-products creates new product"""
        # Get a category ID first
        cat_response = requests.get(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = cat_response.json()
        category_id = categories[0]["id"]
        
        test_name = f"TEST_Product_{uuid.uuid4().hex[:6]}"
        response = requests.post(
            f"{BASE_URL}/api/admin/supply-products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "category_id": category_id,
                "name": test_name,
                "description": "Test product for automated testing",
                "unit": "box",
                "internal_notes": "Test internal notes"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == test_name
        assert data["category_id"] == category_id
        assert data["unit"] == "box"
        assert data["description"] == "Test product for automated testing"
        assert "id" in data
        assert "category_name" in data
        
        created_products.append(data["id"])
        
        # Verify persistence
        get_response = requests.get(
            f"{BASE_URL}/api/admin/supply-products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        products = get_response.json()
        found = any(p["id"] == data["id"] for p in products)
        assert found, "Created product not found in list"
    
    def test_update_supply_product(self, admin_token):
        """PUT /api/admin/supply-products/{id} updates product"""
        # Get a category ID
        cat_response = requests.get(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = cat_response.json()
        category_id = categories[0]["id"]
        
        # Create a product
        test_name = f"TEST_UpdateProd_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/supply-products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": category_id, "name": test_name, "unit": "piece"}
        )
        assert create_response.status_code == 200
        product_id = create_response.json()["id"]
        created_products.append(product_id)
        
        # Update the product
        updated_name = f"TEST_Updated_{uuid.uuid4().hex[:6]}"
        update_response = requests.put(
            f"{BASE_URL}/api/admin/supply-products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"name": updated_name, "unit": "pack", "description": "Updated description"}
        )
        assert update_response.status_code == 200
        
        data = update_response.json()
        assert data["name"] == updated_name
        assert data["unit"] == "pack"
        assert data["description"] == "Updated description"
    
    def test_toggle_product_status(self, admin_token):
        """PUT /api/admin/supply-products/{id} can toggle is_active"""
        # Get a category ID
        cat_response = requests.get(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = cat_response.json()
        category_id = categories[0]["id"]
        
        # Create a product
        test_name = f"TEST_ToggleProd_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/supply-products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": category_id, "name": test_name}
        )
        product_id = create_response.json()["id"]
        created_products.append(product_id)
        
        # Disable the product
        update_response = requests.put(
            f"{BASE_URL}/api/admin/supply-products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False}
        )
        assert update_response.status_code == 200
        assert update_response.json()["is_active"] == False
        
        # Re-enable the product
        update_response = requests.put(
            f"{BASE_URL}/api/admin/supply-products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": True}
        )
        assert update_response.status_code == 200
        assert update_response.json()["is_active"] == True
    
    def test_delete_supply_product(self, admin_token):
        """DELETE /api/admin/supply-products/{id} soft deletes product"""
        # Get a category ID
        cat_response = requests.get(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = cat_response.json()
        category_id = categories[0]["id"]
        
        # Create a product to delete
        test_name = f"TEST_DeleteProd_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/supply-products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": category_id, "name": test_name}
        )
        product_id = create_response.json()["id"]
        
        # Delete the product
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/supply-products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert delete_response.status_code == 200
        assert delete_response.json()["message"] == "Product deleted"
        
        # Verify it's no longer in the list
        get_response = requests.get(
            f"{BASE_URL}/api/admin/supply-products",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        products = get_response.json()
        found = any(p["id"] == product_id for p in products)
        assert not found, "Deleted product still appears in list"


class TestCompanySupplyCatalog:
    """Company supply catalog tests"""
    
    def test_get_supply_catalog(self, company_token):
        """GET /api/company/supply-catalog returns categories with products"""
        response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        
        catalog = response.json()
        assert isinstance(catalog, list)
        assert len(catalog) >= 2, "Expected at least 2 categories in catalog"
        
        # Verify catalog structure
        for category in catalog:
            assert "id" in category
            assert "name" in category
            assert "products" in category
            assert isinstance(category["products"], list)
            assert len(category["products"]) > 0, f"Category {category['name']} has no products"
            
            # Verify product structure (should not include internal_notes)
            for product in category["products"]:
                assert "id" in product
                assert "name" in product
                assert "unit" in product
                assert "internal_notes" not in product, "internal_notes should not be exposed to company users"
    
    def test_catalog_excludes_inactive_products(self, admin_token, company_token):
        """Catalog should not include inactive products"""
        # Get a category ID
        cat_response = requests.get(
            f"{BASE_URL}/api/admin/supply-categories",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        categories = cat_response.json()
        category_id = categories[0]["id"]
        
        # Create an inactive product
        test_name = f"TEST_InactiveProd_{uuid.uuid4().hex[:6]}"
        create_response = requests.post(
            f"{BASE_URL}/api/admin/supply-products",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"category_id": category_id, "name": test_name}
        )
        product_id = create_response.json()["id"]
        created_products.append(product_id)
        
        # Disable the product
        requests.put(
            f"{BASE_URL}/api/admin/supply-products/{product_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"is_active": False}
        )
        
        # Check catalog - inactive product should not appear
        catalog_response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        catalog = catalog_response.json()
        
        all_product_ids = []
        for cat in catalog:
            all_product_ids.extend([p["id"] for p in cat["products"]])
        
        assert product_id not in all_product_ids, "Inactive product should not appear in catalog"


class TestCompanySupplyOrders:
    """Company supply order tests"""
    
    def test_create_supply_order_with_existing_site(self, company_token):
        """POST /api/company/supply-orders creates order with existing site delivery"""
        # Get catalog to get product IDs
        catalog_response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        catalog = catalog_response.json()
        
        # Get first product from first category
        product = catalog[0]["products"][0]
        
        # Get company sites
        sites_response = requests.get(
            f"{BASE_URL}/api/company/sites",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        sites = sites_response.json()
        
        # Create order
        order_data = {
            "items": [
                {"product_id": product["id"], "quantity": 5}
            ],
            "delivery_location": {
                "type": "existing",
                "site_id": sites[0]["id"] if sites else None
            },
            "notes": "Test order - automated testing"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"},
            json=order_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "order_number" in data
        assert data["order_number"].startswith("SUP-")
        assert "id" in data
        assert data["items_count"] == 1
        assert "message" in data
        
        created_orders.append(data["id"])
        
        # Verify order appears in list
        orders_response = requests.get(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        orders = orders_response.json()
        found = any(o["id"] == data["id"] for o in orders)
        assert found, "Created order not found in orders list"
    
    def test_create_supply_order_with_new_location(self, company_token):
        """POST /api/company/supply-orders creates order with new delivery location"""
        # Get catalog
        catalog_response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        catalog = catalog_response.json()
        
        # Get multiple products
        products = []
        for cat in catalog[:2]:
            if cat["products"]:
                products.append(cat["products"][0])
        
        # Create order with new location
        order_data = {
            "items": [
                {"product_id": p["id"], "quantity": 2} for p in products
            ],
            "delivery_location": {
                "type": "new",
                "address": "123 Test Street",
                "city": "Test City",
                "pincode": "123456",
                "contact_person": "Test Contact",
                "contact_phone": "9876543210"
            },
            "notes": "Test order with new location"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"},
            json=order_data
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["items_count"] == len(products)
        created_orders.append(data["id"])
    
    def test_create_order_empty_items_rejected(self, company_token):
        """POST /api/company/supply-orders rejects empty items"""
        order_data = {
            "items": [],
            "delivery_location": {"type": "new", "address": "Test"}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"},
            json=order_data
        )
        assert response.status_code == 400
        assert "No items" in response.json()["detail"]
    
    def test_create_order_missing_delivery_rejected(self, company_token):
        """POST /api/company/supply-orders rejects missing delivery location"""
        # Get a product
        catalog_response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        catalog = catalog_response.json()
        product = catalog[0]["products"][0]
        
        order_data = {
            "items": [{"product_id": product["id"], "quantity": 1}],
            "delivery_location": {}
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"},
            json=order_data
        )
        assert response.status_code == 400
    
    def test_get_company_supply_orders(self, company_token):
        """GET /api/company/supply-orders returns company's orders"""
        response = requests.get(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        assert response.status_code == 200
        
        orders = response.json()
        assert isinstance(orders, list)
        
        # Verify order structure
        if orders:
            order = orders[0]
            assert "id" in order
            assert "order_number" in order
            assert "status" in order
            assert "items" in order
            assert "delivery_location" in order
            assert "created_at" in order


class TestAdminSupplyOrders:
    """Admin supply order management tests"""
    
    def test_get_all_supply_orders(self, admin_token):
        """GET /api/admin/supply-orders returns all orders"""
        response = requests.get(
            f"{BASE_URL}/api/admin/supply-orders",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        orders = response.json()
        assert isinstance(orders, list)
    
    def test_get_supply_order_by_id(self, admin_token, company_token):
        """GET /api/admin/supply-orders/{id} returns specific order"""
        # First create an order
        catalog_response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        catalog = catalog_response.json()
        product = catalog[0]["products"][0]
        
        create_response = requests.post(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"},
            json={
                "items": [{"product_id": product["id"], "quantity": 1}],
                "delivery_location": {"type": "new", "address": "Test", "contact_person": "Test", "contact_phone": "123"}
            }
        )
        order_id = create_response.json()["id"]
        created_orders.append(order_id)
        
        # Get the order by ID
        response = requests.get(
            f"{BASE_URL}/api/admin/supply-orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        order = response.json()
        assert order["id"] == order_id
        assert "company_name" in order
        assert "requested_by_name" in order
        assert "items" in order
    
    def test_update_supply_order_status(self, admin_token, company_token):
        """PUT /api/admin/supply-orders/{id} updates order status"""
        # Create an order
        catalog_response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        catalog = catalog_response.json()
        product = catalog[0]["products"][0]
        
        create_response = requests.post(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"},
            json={
                "items": [{"product_id": product["id"], "quantity": 1}],
                "delivery_location": {"type": "new", "address": "Test", "contact_person": "Test", "contact_phone": "123"}
            }
        )
        order_id = create_response.json()["id"]
        created_orders.append(order_id)
        
        # Update status to approved
        update_response = requests.put(
            f"{BASE_URL}/api/admin/supply-orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "approved"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "approved"
        
        # Update status to processing
        update_response = requests.put(
            f"{BASE_URL}/api/admin/supply-orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "processing"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "processing"
        
        # Update status to delivered
        update_response = requests.put(
            f"{BASE_URL}/api/admin/supply-orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"status": "delivered"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["status"] == "delivered"
    
    def test_update_supply_order_admin_notes(self, admin_token, company_token):
        """PUT /api/admin/supply-orders/{id} updates admin notes"""
        # Create an order
        catalog_response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        catalog = catalog_response.json()
        product = catalog[0]["products"][0]
        
        create_response = requests.post(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"},
            json={
                "items": [{"product_id": product["id"], "quantity": 1}],
                "delivery_location": {"type": "new", "address": "Test", "contact_person": "Test", "contact_phone": "123"}
            }
        )
        order_id = create_response.json()["id"]
        created_orders.append(order_id)
        
        # Update admin notes
        update_response = requests.put(
            f"{BASE_URL}/api/admin/supply-orders/{order_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={"admin_notes": "Test admin notes - vendor contacted"}
        )
        assert update_response.status_code == 200
        assert update_response.json()["admin_notes"] == "Test admin notes - vendor contacted"
    
    def test_filter_orders_by_status(self, admin_token):
        """GET /api/admin/supply-orders?status=requested filters by status"""
        response = requests.get(
            f"{BASE_URL}/api/admin/supply-orders?status=requested",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        
        orders = response.json()
        for order in orders:
            assert order["status"] == "requested"


class TestOsTicketIntegration:
    """osTicket integration tests (IP-restricted, may return null)"""
    
    def test_order_creates_osticket_attempt(self, company_token):
        """Order creation attempts osTicket creation (may fail due to IP restriction)"""
        # Get catalog
        catalog_response = requests.get(
            f"{BASE_URL}/api/company/supply-catalog",
            headers={"Authorization": f"Bearer {company_token}"}
        )
        catalog = catalog_response.json()
        product = catalog[0]["products"][0]
        
        # Create order
        response = requests.post(
            f"{BASE_URL}/api/company/supply-orders",
            headers={"Authorization": f"Bearer {company_token}"},
            json={
                "items": [{"product_id": product["id"], "quantity": 3}],
                "delivery_location": {"type": "new", "address": "Test", "contact_person": "Test", "contact_phone": "123"},
                "notes": "Test osTicket integration"
            }
        )
        assert response.status_code == 200
        
        data = response.json()
        created_orders.append(data["id"])
        
        # osTicket ID may be null due to IP restriction - this is expected
        # Just verify the response structure includes osticket fields
        assert "osticket_id" in data or "osticket_error" in data


# Cleanup fixture
@pytest.fixture(scope="module", autouse=True)
def cleanup(admin_token):
    """Cleanup test data after all tests"""
    yield
    
    # Note: Soft delete is used, so data remains in DB but is_deleted=True
    # This is acceptable for test data with TEST_ prefix
    print(f"\nTest data created: {len(created_categories)} categories, {len(created_products)} products, {len(created_orders)} orders")
