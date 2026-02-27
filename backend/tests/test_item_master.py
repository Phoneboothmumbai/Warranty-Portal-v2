"""
Item Master Module API Tests
============================
Tests for Categories, Products, Bundles CRUD operations
Including GST slabs and product suggestions endpoints.
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')
API = f"{BASE_URL}/api/admin/item-master"

@pytest.fixture(scope="module")
def auth_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "ck@motta.in",
        "password": "Charu@123@"
    })
    if response.status_code != 200:
        pytest.skip("Authentication failed")
    return response.json().get("access_token")


@pytest.fixture(scope="module")
def headers(auth_token):
    """Headers with auth token"""
    return {"Authorization": f"Bearer {auth_token}", "Content-Type": "application/json"}


class TestGSTSlabs:
    """Test GST Slabs endpoint"""
    
    def test_get_gst_slabs(self, headers):
        """Should return all 5 GST slabs (0, 5, 12, 18, 28)"""
        response = requests.get(f"{API}/gst-slabs", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "slabs" in data
        slabs = data["slabs"]
        assert len(slabs) == 5
        
        slab_values = [s["value"] for s in slabs]
        assert slab_values == [0, 5, 12, 18, 28]


class TestCategories:
    """Test Categories CRUD operations"""
    
    def test_list_categories(self, headers):
        """Should list existing categories (Security, Networking)"""
        response = requests.get(f"{API}/categories", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "categories" in data
        categories = data["categories"]
        assert len(categories) >= 2
        
        names = [c["name"] for c in categories]
        assert "Security" in names
        assert "Networking" in names
    
    def test_create_category(self, headers):
        """Should create a new category"""
        payload = {
            "name": "TEST_Electrical",
            "description": "Test category for electrical equipment",
            "sort_order": 99
        }
        response = requests.post(f"{API}/categories", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_Electrical"
        assert data["description"] == "Test category for electrical equipment"
        assert "id" in data
        
        # Store ID for cleanup
        TestCategories.created_category_id = data["id"]
    
    def test_create_duplicate_category_fails(self, headers):
        """Should reject duplicate category name"""
        payload = {"name": "Security", "description": "Duplicate"}
        response = requests.post(f"{API}/categories", headers=headers, json=payload)
        assert response.status_code == 400
        assert "already exists" in response.json().get("detail", "").lower()
    
    def test_update_category(self, headers):
        """Should update existing category"""
        cat_id = getattr(TestCategories, 'created_category_id', None)
        if not cat_id:
            pytest.skip("No test category created")
        
        payload = {"name": "TEST_Electrical Updated", "description": "Updated description"}
        response = requests.put(f"{API}/categories/{cat_id}", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_Electrical Updated"
        assert data["description"] == "Updated description"
    
    def test_delete_category(self, headers):
        """Should delete test category"""
        cat_id = getattr(TestCategories, 'created_category_id', None)
        if not cat_id:
            pytest.skip("No test category created")
        
        response = requests.delete(f"{API}/categories/{cat_id}", headers=headers)
        assert response.status_code == 200
        assert response.json().get("success") is True
    
    def test_delete_category_with_products_fails(self, headers):
        """Should fail to delete category with linked products"""
        # Get Security category ID (has products)
        response = requests.get(f"{API}/categories", headers=headers)
        categories = response.json().get("categories", [])
        security_cat = next((c for c in categories if c["name"] == "Security"), None)
        
        if not security_cat:
            pytest.skip("Security category not found")
        
        response = requests.delete(f"{API}/categories/{security_cat['id']}", headers=headers)
        assert response.status_code == 400
        assert "product" in response.json().get("detail", "").lower()


class TestProducts:
    """Test Products CRUD operations"""
    
    def test_list_products(self, headers):
        """Should list existing products"""
        response = requests.get(f"{API}/products", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "products" in data
        assert "total" in data
        
        products = data["products"]
        assert len(products) >= 4
        
        names = [p["name"] for p in products]
        assert "Hikvision 2MP Dome Camera" in names
        assert "Hikvision 8Ch NVR" in names
        assert "WD Purple 2TB HDD" in names
        assert "TP-Link 8-Port POE Switch" in names
    
    def test_filter_products_by_category(self, headers):
        """Should filter products by category"""
        # Get Security category ID
        cat_response = requests.get(f"{API}/categories", headers=headers)
        categories = cat_response.json().get("categories", [])
        security_cat = next((c for c in categories if c["name"] == "Security"), None)
        
        if not security_cat:
            pytest.skip("Security category not found")
        
        response = requests.get(f"{API}/products", headers=headers, params={"category_id": security_cat["id"]})
        assert response.status_code == 200
        
        products = response.json().get("products", [])
        assert len(products) >= 3  # Camera, NVR, HDD
        
        for p in products:
            assert p.get("category_id") == security_cat["id"]
    
    def test_search_products_by_name(self, headers):
        """Should search products by name"""
        response = requests.get(f"{API}/products", headers=headers, params={"search": "Hikvision"})
        assert response.status_code == 200
        
        products = response.json().get("products", [])
        assert len(products) >= 2  # Camera and NVR
        
        for p in products:
            assert "hikvision" in p["name"].lower()
    
    def test_create_product(self, headers):
        """Should create a new product with all fields"""
        # Get category ID first
        cat_response = requests.get(f"{API}/categories", headers=headers)
        categories = cat_response.json().get("categories", [])
        networking_cat = next((c for c in categories if c["name"] == "Networking"), None)
        
        if not networking_cat:
            pytest.skip("Networking category not found")
        
        payload = {
            "category_id": networking_cat["id"],
            "name": "TEST_Router 5G",
            "sku": "TEST-RTR-5G",
            "part_number": "RTR-5G-001",
            "brand": "Test Brand",
            "manufacturer": "Test Manufacturer",
            "description": "Test router for testing",
            "unit_price": 5000.0,
            "gst_slab": 18,
            "hsn_code": "85176290",
            "unit_of_measure": "unit"
        }
        response = requests.post(f"{API}/products", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_Router 5G"
        assert data["sku"] == "TEST-RTR-5G"
        assert data["unit_price"] == 5000.0
        assert data["gst_slab"] == 18
        assert "id" in data
        
        TestProducts.created_product_id = data["id"]
    
    def test_create_product_with_invalid_gst_fails(self, headers):
        """Should reject invalid GST slab"""
        cat_response = requests.get(f"{API}/categories", headers=headers)
        categories = cat_response.json().get("categories", [])
        if not categories:
            pytest.skip("No categories found")
        
        payload = {
            "category_id": categories[0]["id"],
            "name": "TEST_Invalid GST",
            "unit_price": 1000,
            "gst_slab": 15  # Invalid - should be 0, 5, 12, 18, or 28
        }
        response = requests.post(f"{API}/products", headers=headers, json=payload)
        assert response.status_code == 400
        assert "gst" in response.json().get("detail", "").lower()
    
    def test_create_duplicate_sku_fails(self, headers):
        """Should reject duplicate SKU"""
        cat_response = requests.get(f"{API}/categories", headers=headers)
        categories = cat_response.json().get("categories", [])
        if not categories:
            pytest.skip("No categories found")
        
        payload = {
            "category_id": categories[0]["id"],
            "name": "TEST_Duplicate SKU",
            "sku": "HIK-2MP-DOME"  # Existing SKU
        }
        response = requests.post(f"{API}/products", headers=headers, json=payload)
        assert response.status_code == 400
        assert "sku" in response.json().get("detail", "").lower()
    
    def test_get_single_product(self, headers):
        """Should get single product by ID"""
        product_id = getattr(TestProducts, 'created_product_id', None)
        if not product_id:
            # Use existing product
            response = requests.get(f"{API}/products", headers=headers)
            products = response.json().get("products", [])
            if products:
                product_id = products[0]["id"]
            else:
                pytest.skip("No products found")
        
        response = requests.get(f"{API}/products/{product_id}", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "name" in data
        assert "unit_price" in data
    
    def test_update_product(self, headers):
        """Should update product"""
        product_id = getattr(TestProducts, 'created_product_id', None)
        if not product_id:
            pytest.skip("No test product created")
        
        payload = {"name": "TEST_Router 5G Updated", "unit_price": 5500.0}
        response = requests.put(f"{API}/products/{product_id}", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "TEST_Router 5G Updated"
        assert data["unit_price"] == 5500.0
    
    def test_delete_product(self, headers):
        """Should delete test product"""
        product_id = getattr(TestProducts, 'created_product_id', None)
        if not product_id:
            pytest.skip("No test product created")
        
        response = requests.delete(f"{API}/products/{product_id}", headers=headers)
        assert response.status_code == 200
        assert response.json().get("success") is True
        
        # Verify deletion (should return 404)
        response = requests.get(f"{API}/products/{product_id}", headers=headers)
        assert response.status_code == 404


class TestBundles:
    """Test Bundles CRUD operations"""
    
    def test_list_bundles(self, headers):
        """Should list existing bundles with enriched product data"""
        response = requests.get(f"{API}/bundles", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "bundles" in data
        
        bundles = data["bundles"]
        assert len(bundles) >= 1
        
        # Check first bundle has enriched data
        bundle = bundles[0]
        assert "source_product" in bundle
        assert "recommended_products" in bundle
        assert bundle["source_product"].get("name") == "Hikvision 2MP Dome Camera"
    
    def test_create_bundle(self, headers):
        """Should create a new bundle"""
        # Get products to create bundle
        response = requests.get(f"{API}/products", headers=headers)
        products = response.json().get("products", [])
        
        if len(products) < 2:
            pytest.skip("Need at least 2 products to create bundle")
        
        # Use NVR as source (doesn't have bundle yet)
        nvr = next((p for p in products if "NVR" in p["name"]), None)
        if not nvr:
            pytest.skip("NVR product not found")
        
        # Check if bundle already exists for NVR
        bundles_response = requests.get(f"{API}/bundles", headers=headers)
        existing_bundles = bundles_response.json().get("bundles", [])
        nvr_bundle = next((b for b in existing_bundles if b["source_product_id"] == nvr["id"]), None)
        
        if nvr_bundle:
            # Delete existing test bundle
            requests.delete(f"{API}/bundles/{nvr_bundle['id']}", headers=headers)
        
        other_products = [p for p in products if p["id"] != nvr["id"]][:2]
        
        payload = {
            "source_product_id": nvr["id"],
            "recommended_product_ids": [p["id"] for p in other_products],
            "description": "TEST_NVR bundle recommendations"
        }
        response = requests.post(f"{API}/bundles", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["source_product_id"] == nvr["id"]
        assert len(data["recommended_product_ids"]) == 2
        assert "id" in data
        
        TestBundles.created_bundle_id = data["id"]
    
    def test_create_duplicate_bundle_fails(self, headers):
        """Should fail to create duplicate bundle for same source product"""
        # Try to create another bundle for same product
        bundles_response = requests.get(f"{API}/bundles", headers=headers)
        bundles = bundles_response.json().get("bundles", [])
        
        if not bundles:
            pytest.skip("No bundles exist")
        
        existing_bundle = bundles[0]
        
        # Get other product IDs
        products_response = requests.get(f"{API}/products", headers=headers)
        products = products_response.json().get("products", [])
        other_ids = [p["id"] for p in products if p["id"] != existing_bundle["source_product_id"]][:1]
        
        if not other_ids:
            pytest.skip("No other products available")
        
        payload = {
            "source_product_id": existing_bundle["source_product_id"],
            "recommended_product_ids": other_ids
        }
        response = requests.post(f"{API}/bundles", headers=headers, json=payload)
        assert response.status_code == 400
        assert "already exists" in response.json().get("detail", "").lower()
    
    def test_update_bundle(self, headers):
        """Should update bundle"""
        bundle_id = getattr(TestBundles, 'created_bundle_id', None)
        if not bundle_id:
            pytest.skip("No test bundle created")
        
        payload = {"description": "TEST_Updated description"}
        response = requests.put(f"{API}/bundles/{bundle_id}", headers=headers, json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert data["description"] == "TEST_Updated description"
    
    def test_delete_bundle(self, headers):
        """Should delete test bundle"""
        bundle_id = getattr(TestBundles, 'created_bundle_id', None)
        if not bundle_id:
            pytest.skip("No test bundle created")
        
        response = requests.delete(f"{API}/bundles/{bundle_id}", headers=headers)
        assert response.status_code == 200
        assert response.json().get("success") is True


class TestProductSuggestions:
    """Test product suggestions endpoint for quotation integration"""
    
    def test_get_suggestions_for_bundled_product(self, headers):
        """Should return suggestions for product with bundle"""
        # Get camera product ID (has bundle)
        response = requests.get(f"{API}/products", headers=headers)
        products = response.json().get("products", [])
        camera = next((p for p in products if "Dome Camera" in p["name"]), None)
        
        if not camera:
            pytest.skip("Camera product not found")
        
        response = requests.get(f"{API}/products/{camera['id']}/suggestions", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestions" in data
        
        suggestions = data["suggestions"]
        assert len(suggestions) >= 3  # NVR, HDD, POE Switch
        
        suggestion_names = [s["name"] for s in suggestions]
        assert "Hikvision 8Ch NVR" in suggestion_names
        assert "WD Purple 2TB HDD" in suggestion_names
        assert "TP-Link 8-Port POE Switch" in suggestion_names
        
        # Should include bundle description
        assert "bundle_description" in data
    
    def test_get_suggestions_for_unbundled_product(self, headers):
        """Should return empty suggestions for product without bundle"""
        # Get POE Switch (doesn't have its own bundle)
        response = requests.get(f"{API}/products", headers=headers)
        products = response.json().get("products", [])
        poe_switch = next((p for p in products if "POE Switch" in p["name"]), None)
        
        if not poe_switch:
            pytest.skip("POE Switch product not found")
        
        response = requests.get(f"{API}/products/{poe_switch['id']}/suggestions", headers=headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "suggestions" in data
        assert len(data["suggestions"]) == 0  # No bundle for this product


class TestProductValidations:
    """Test various product field validations"""
    
    def test_gst_calculation_values(self, headers):
        """Verify product GST values are correct"""
        response = requests.get(f"{API}/products", headers=headers)
        products = response.json().get("products", [])
        
        for product in products:
            assert product["gst_slab"] in [0, 5, 12, 18, 28]
            
            # Verify price is non-negative
            assert product["unit_price"] >= 0
    
    def test_product_has_required_fields(self, headers):
        """Verify products have all required fields"""
        response = requests.get(f"{API}/products", headers=headers)
        products = response.json().get("products", [])
        
        required_fields = ["id", "name", "category_id", "unit_price", "gst_slab"]
        for product in products:
            for field in required_fields:
                assert field in product, f"Missing field: {field}"
