"""
Test suite for Multi-Consumable Order Feature
Tests the new enhancement where:
1. Admin can add multiple consumables per printer (Black Toner, Cyan, Magenta, Yellow etc.)
2. Company users can select specific consumables to order with quantities
3. Backend API supports 'items' array in order-consumable endpoint
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


class TestMultiConsumablesFeature:
    """Test suite for multi-consumable ordering feature"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def company_token(self):
        """Get company user authentication token"""
        response = requests.post(f"{BASE_URL}/api/company/auth/login", json={
            "email": COMPANY_USER_EMAIL,
            "password": COMPANY_USER_PASSWORD
        })
        if response.status_code != 200:
            pytest.skip(f"Company login failed: {response.status_code} - {response.text}")
        return response.json().get("access_token")
    
    @pytest.fixture(scope="class")
    def company_id(self, company_token):
        """Get company ID from company user"""
        response = requests.get(f"{BASE_URL}/api/company/auth/me", headers={
            "Authorization": f"Bearer {company_token}"
        })
        if response.status_code != 200:
            pytest.skip("Failed to get company user info")
        return response.json().get("company_id")
    
    # ==================== ADMIN TESTS - MULTIPLE CONSUMABLES ====================
    
    def test_admin_login(self, admin_token):
        """Test admin can login"""
        assert admin_token is not None
        assert len(admin_token) > 0
        print(f"✓ Admin login successful")
    
    def test_create_printer_with_multiple_consumables(self, admin_token, company_id):
        """Test creating a printer device with multiple consumables (Black, Cyan, Magenta, Yellow)"""
        unique_serial = f"TEST-COLORPRINTER-{uuid.uuid4().hex[:8].upper()}"
        
        # Define multiple consumables for a color printer
        consumables = [
            {
                "id": str(uuid.uuid4()),
                "name": "Black Toner",
                "consumable_type": "Toner Cartridge",
                "model_number": "HP 26A",
                "brand": "HP",
                "color": "Black",
                "notes": "Standard yield - 3100 pages"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Cyan Toner",
                "consumable_type": "Toner Cartridge",
                "model_number": "HP 201A",
                "brand": "HP",
                "color": "Cyan",
                "notes": "Standard yield - 1400 pages"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Magenta Toner",
                "consumable_type": "Toner Cartridge",
                "model_number": "HP 201A",
                "brand": "HP",
                "color": "Magenta",
                "notes": "Standard yield - 1400 pages"
            },
            {
                "id": str(uuid.uuid4()),
                "name": "Yellow Toner",
                "consumable_type": "Toner Cartridge",
                "model_number": "HP 201A",
                "brand": "HP",
                "color": "Yellow",
                "notes": "Standard yield - 1400 pages"
            }
        ]
        
        device_data = {
            "company_id": company_id,
            "device_type": "Printer",
            "brand": "HP",
            "model": "Color LaserJet Pro M254dw",
            "serial_number": unique_serial,
            "asset_tag": f"AST-{uuid.uuid4().hex[:6].upper()}",
            "purchase_date": "2024-01-15",
            "purchase_cost": 45000,
            "vendor": "HP India",
            "warranty_end_date": "2027-01-15",
            "location": "Office Floor 3",
            "condition": "good",
            "status": "active",
            "notes": "Color printer for multi-consumable testing",
            # Multiple consumables array
            "consumables": consumables
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/devices", json=device_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code in [200, 201], f"Failed to create device: {response.text}"
        
        created_device = response.json()
        assert created_device["serial_number"] == unique_serial
        assert created_device["device_type"] == "Printer"
        
        # Verify consumables array was saved
        assert "consumables" in created_device, "consumables field missing from response"
        assert len(created_device["consumables"]) == 4, f"Expected 4 consumables, got {len(created_device.get('consumables', []))}"
        
        # Verify each consumable has required fields
        for consumable in created_device["consumables"]:
            assert "id" in consumable
            assert "name" in consumable
            assert "consumable_type" in consumable
            assert "model_number" in consumable
        
        print(f"✓ Created color printer with {len(created_device['consumables'])} consumables: {unique_serial}")
        
        # Store device ID and consumable IDs for later tests
        TestMultiConsumablesFeature.test_printer_id = created_device["id"]
        TestMultiConsumablesFeature.test_printer_serial = unique_serial
        TestMultiConsumablesFeature.test_consumables = created_device["consumables"]
        
        return created_device
    
    def test_get_device_returns_consumables_array(self, admin_token):
        """Test GET /api/admin/devices/{id} returns device with consumables array"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        
        response = requests.get(f"{BASE_URL}/api/admin/devices/{device_id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to get device: {response.text}"
        
        device = response.json()
        assert "consumables" in device, "consumables field missing from GET response"
        assert isinstance(device["consumables"], list), "consumables should be a list"
        assert len(device["consumables"]) == 4, f"Expected 4 consumables, got {len(device['consumables'])}"
        
        # Verify consumable details
        colors_found = [c.get("color") for c in device["consumables"]]
        assert "Black" in colors_found, "Black toner not found"
        assert "Cyan" in colors_found, "Cyan toner not found"
        assert "Magenta" in colors_found, "Magenta toner not found"
        assert "Yellow" in colors_found, "Yellow toner not found"
        
        print(f"✓ GET device returns consumables array with all 4 colors")
    
    def test_update_device_add_consumable(self, admin_token):
        """Test adding a new consumable to existing printer"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        
        # Get current consumables
        current_consumables = TestMultiConsumablesFeature.test_consumables.copy()
        
        # Add a new consumable (Drum Unit)
        new_consumable = {
            "id": str(uuid.uuid4()),
            "name": "Imaging Drum",
            "consumable_type": "Drum Unit",
            "model_number": "HP 19A",
            "brand": "HP",
            "color": "",
            "notes": "Imaging drum - 12000 pages"
        }
        current_consumables.append(new_consumable)
        
        update_data = {
            "consumables": current_consumables
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/devices/{device_id}", json=update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to update device: {response.text}"
        
        updated_device = response.json()
        assert len(updated_device["consumables"]) == 5, f"Expected 5 consumables after adding drum, got {len(updated_device['consumables'])}"
        
        # Update stored consumables
        TestMultiConsumablesFeature.test_consumables = updated_device["consumables"]
        
        print(f"✓ Successfully added new consumable (Drum Unit) to printer")
    
    def test_update_device_remove_consumable(self, admin_token):
        """Test removing a consumable from printer using X button"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        
        # Get current consumables and remove the drum unit
        current_consumables = TestMultiConsumablesFeature.test_consumables.copy()
        current_consumables = [c for c in current_consumables if c.get("consumable_type") != "Drum Unit"]
        
        update_data = {
            "consumables": current_consumables
        }
        
        response = requests.put(f"{BASE_URL}/api/admin/devices/{device_id}", json=update_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        assert response.status_code == 200, f"Failed to update device: {response.text}"
        
        updated_device = response.json()
        assert len(updated_device["consumables"]) == 4, f"Expected 4 consumables after removal, got {len(updated_device['consumables'])}"
        
        # Update stored consumables
        TestMultiConsumablesFeature.test_consumables = updated_device["consumables"]
        
        print(f"✓ Successfully removed consumable from printer")
    
    # ==================== COMPANY PORTAL TESTS - MULTI-ITEM ORDERING ====================
    
    def test_company_login(self, company_token):
        """Test company user can login"""
        assert company_token is not None
        assert len(company_token) > 0
        print(f"✓ Company user login successful")
    
    def test_company_view_device_with_consumables(self, company_token):
        """Test company user can view device with consumables array"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        
        response = requests.get(f"{BASE_URL}/api/company/devices/{device_id}", headers={
            "Authorization": f"Bearer {company_token}"
        })
        
        assert response.status_code == 200, f"Failed to get device: {response.text}"
        
        data = response.json()
        assert "device" in data
        device = data["device"]
        
        # Verify consumables are visible to company user
        assert "consumables" in device, "consumables field missing from company device view"
        assert len(device["consumables"]) == 4, f"Expected 4 consumables, got {len(device.get('consumables', []))}"
        
        print(f"✓ Company user can view device with {len(device['consumables'])} consumables")
    
    def test_order_multiple_consumables(self, company_token):
        """Test ordering multiple consumables (Black and Cyan) with quantities"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        consumables = TestMultiConsumablesFeature.test_consumables
        
        # Find Black and Cyan consumables
        black_consumable = next((c for c in consumables if c.get("color") == "Black"), None)
        cyan_consumable = next((c for c in consumables if c.get("color") == "Cyan"), None)
        
        assert black_consumable, "Black consumable not found"
        assert cyan_consumable, "Cyan consumable not found"
        
        # Build order with multiple items
        order_data = {
            "items": [
                {
                    "consumable_id": black_consumable["id"],
                    "name": black_consumable["name"],
                    "consumable_type": black_consumable["consumable_type"],
                    "model_number": black_consumable["model_number"],
                    "brand": black_consumable.get("brand"),
                    "color": black_consumable.get("color"),
                    "quantity": 2
                },
                {
                    "consumable_id": cyan_consumable["id"],
                    "name": cyan_consumable["name"],
                    "consumable_type": cyan_consumable["consumable_type"],
                    "model_number": cyan_consumable["model_number"],
                    "brand": cyan_consumable.get("brand"),
                    "color": cyan_consumable.get("color"),
                    "quantity": 1
                }
            ],
            "notes": "Urgent - running low on black and cyan toner"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/devices/{device_id}/order-consumable",
            json=order_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert response.status_code == 200, f"Failed to order consumables: {response.text}"
        
        result = response.json()
        assert "order_number" in result
        assert result["order_number"].startswith("ORD-")
        assert "id" in result
        assert "items_count" in result
        assert result["items_count"] == 2, f"Expected 2 items, got {result.get('items_count')}"
        assert "total_quantity" in result
        assert result["total_quantity"] == 3, f"Expected total quantity 3, got {result.get('total_quantity')}"
        
        print(f"✓ Multi-consumable order created: {result['order_number']}")
        print(f"  Items: {result['items_count']}, Total Qty: {result['total_quantity']}")
        print(f"  osTicket ID: {result.get('osticket_id', 'None (IP restricted)')}")
        
        TestMultiConsumablesFeature.test_order_number = result["order_number"]
        TestMultiConsumablesFeature.test_order_id = result["id"]
    
    def test_order_all_four_consumables(self, company_token):
        """Test ordering all 4 color consumables at once"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        consumables = TestMultiConsumablesFeature.test_consumables
        
        # Build order with all 4 items
        order_items = []
        for consumable in consumables:
            order_items.append({
                "consumable_id": consumable["id"],
                "name": consumable["name"],
                "consumable_type": consumable["consumable_type"],
                "model_number": consumable["model_number"],
                "brand": consumable.get("brand"),
                "color": consumable.get("color"),
                "quantity": 1
            })
        
        order_data = {
            "items": order_items,
            "notes": "Full set of toners needed"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/devices/{device_id}/order-consumable",
            json=order_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert response.status_code == 200, f"Failed to order consumables: {response.text}"
        
        result = response.json()
        assert result["items_count"] == 4, f"Expected 4 items, got {result.get('items_count')}"
        assert result["total_quantity"] == 4, f"Expected total quantity 4, got {result.get('total_quantity')}"
        
        print(f"✓ Full set order created: {result['order_number']} (4 items)")
    
    def test_order_single_consumable_from_multi(self, company_token):
        """Test ordering just one consumable from a printer with multiple defined"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        consumables = TestMultiConsumablesFeature.test_consumables
        
        # Order just the Yellow toner
        yellow_consumable = next((c for c in consumables if c.get("color") == "Yellow"), None)
        assert yellow_consumable, "Yellow consumable not found"
        
        order_data = {
            "items": [
                {
                    "consumable_id": yellow_consumable["id"],
                    "name": yellow_consumable["name"],
                    "consumable_type": yellow_consumable["consumable_type"],
                    "model_number": yellow_consumable["model_number"],
                    "brand": yellow_consumable.get("brand"),
                    "color": yellow_consumable.get("color"),
                    "quantity": 3
                }
            ],
            "notes": "Yellow toner running low"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/devices/{device_id}/order-consumable",
            json=order_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert response.status_code == 200, f"Failed to order consumable: {response.text}"
        
        result = response.json()
        assert result["items_count"] == 1
        assert result["total_quantity"] == 3
        
        print(f"✓ Single item order from multi-consumable printer: {result['order_number']}")
    
    def test_order_empty_items_fails(self, company_token):
        """Test that ordering with empty items array fails"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        
        order_data = {
            "items": [],
            "notes": "Empty order test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/devices/{device_id}/order-consumable",
            json=order_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for empty items, got {response.status_code}"
        
        print(f"✓ Empty items order correctly rejected")
    
    def test_legacy_single_item_order_still_works(self, company_token):
        """Test backward compatibility - legacy single item order format still works"""
        if not hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            pytest.skip("No test printer created")
        
        device_id = TestMultiConsumablesFeature.test_printer_id
        
        # Legacy format without items array
        order_data = {
            "quantity": 2,
            "notes": "Legacy format order test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/devices/{device_id}/order-consumable",
            json=order_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert response.status_code == 200, f"Legacy order failed: {response.text}"
        
        result = response.json()
        assert "order_number" in result
        
        print(f"✓ Legacy single-item order format still works: {result['order_number']}")
    
    def test_order_for_non_printer_fails(self, company_token, admin_token, company_id):
        """Test that ordering consumables for non-printer device fails"""
        # Create a laptop device
        unique_serial = f"TEST-LAPTOP-{uuid.uuid4().hex[:8].upper()}"
        
        device_data = {
            "company_id": company_id,
            "device_type": "Laptop",
            "brand": "Dell",
            "model": "Latitude 5520",
            "serial_number": unique_serial,
            "purchase_date": "2024-01-15",
            "condition": "good",
            "status": "active"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/devices", json=device_data, headers={
            "Authorization": f"Bearer {admin_token}"
        })
        
        if create_response.status_code not in [200, 201]:
            pytest.skip(f"Failed to create test laptop: {create_response.text}")
        
        laptop_id = create_response.json()["id"]
        
        # Try to order consumables for laptop
        order_data = {
            "items": [{"consumable_id": "test", "name": "Test", "consumable_type": "Test", "model_number": "Test", "quantity": 1}],
            "notes": "Test"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/company/devices/{laptop_id}/order-consumable",
            json=order_data,
            headers={"Authorization": f"Bearer {company_token}"}
        )
        
        assert response.status_code == 400, f"Expected 400 for non-printer, got {response.status_code}"
        assert "printer" in response.json().get("detail", "").lower()
        
        print(f"✓ Consumable order correctly rejected for non-printer device")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/devices/{laptop_id}", headers={
            "Authorization": f"Bearer {admin_token}"
        })
    
    # ==================== CLEANUP ====================
    
    def test_cleanup_test_data(self, admin_token):
        """Cleanup test data"""
        if hasattr(TestMultiConsumablesFeature, 'test_printer_id'):
            device_id = TestMultiConsumablesFeature.test_printer_id
            response = requests.delete(f"{BASE_URL}/api/admin/devices/{device_id}", headers={
                "Authorization": f"Bearer {admin_token}"
            })
            if response.status_code == 200:
                print(f"✓ Cleaned up test color printer device")
            else:
                print(f"⚠ Failed to cleanup test printer: {response.status_code}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
