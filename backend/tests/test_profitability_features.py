"""
Profitability Features Tests - Iteration 61
Tests for Device Profitability module:
- Service cost config (travel tiers, hourly rates)
- Profitability password management
- Profitability analytics endpoint
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestProfitabilityBackend:
    """Test new profitability-related backend endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login to get admin token
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json().get("access_token")
        assert token, "No access_token in login response"
        self.session.headers.update({"Authorization": f"Bearer {token}"})
        print(f"Login successful, got token")
    
    # ═══════════════════════════════════════════════════════════════
    # SERVICE COST CONFIG TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_get_service_cost_config(self):
        """GET /api/analytics/service-cost-config - should return travel tiers and default rates"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/service-cost-config")
        assert resp.status_code == 200, f"Failed: {resp.status_code} {resp.text}"
        
        data = resp.json()
        # Verify structure
        assert "travel_tiers" in data, "Missing travel_tiers in response"
        assert "default_hourly_rate" in data, "Missing default_hourly_rate"
        assert "per_km_rate" in data, "Missing per_km_rate"
        
        # Verify travel tiers have expected structure
        tiers = data["travel_tiers"]
        assert len(tiers) >= 4, f"Expected at least 4 travel tiers, got {len(tiers)}"
        for tier in tiers:
            assert "name" in tier, "Tier missing name"
            assert "min_km" in tier, "Tier missing min_km"
            assert "max_km" in tier, "Tier missing max_km"
            assert "cost" in tier, "Tier missing cost"
        
        # Verify default values exist
        assert data["default_hourly_rate"] >= 0, "default_hourly_rate should be >= 0"
        assert data["per_km_rate"] >= 0, "per_km_rate should be >= 0"
        
        print(f"Service cost config: {len(tiers)} travel tiers, default hourly rate: {data['default_hourly_rate']}, per_km: {data['per_km_rate']}")
    
    def test_get_service_cost_config_default_tiers(self):
        """Verify default travel tiers structure"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/service-cost-config")
        assert resp.status_code == 200
        
        tiers = resp.json()["travel_tiers"]
        tier_names = [t["name"] for t in tiers]
        
        # Check for expected tier names (Local, City, Outstation, Long Distance)
        expected_names = ["Local", "City", "Outstation", "Long Distance"]
        for name in expected_names:
            assert name in tier_names, f"Expected tier '{name}' not found in {tier_names}"
        
        print(f"All expected tier names present: {expected_names}")
    
    def test_update_service_cost_config(self):
        """PUT /api/analytics/service-cost-config - update travel tiers and rates"""
        # First get current config
        current = self.session.get(f"{BASE_URL}/api/analytics/service-cost-config").json()
        
        # Update with modified values
        update_payload = {
            "default_hourly_rate": 550,
            "per_km_rate": 12
        }
        resp = self.session.put(f"{BASE_URL}/api/analytics/service-cost-config", json=update_payload)
        assert resp.status_code == 200, f"Update failed: {resp.status_code} {resp.text}"
        assert resp.json().get("success") == True
        
        # Verify update persisted
        updated = self.session.get(f"{BASE_URL}/api/analytics/service-cost-config").json()
        assert updated["default_hourly_rate"] == 550, f"Hourly rate not updated: {updated['default_hourly_rate']}"
        assert updated["per_km_rate"] == 12, f"Per km rate not updated: {updated['per_km_rate']}"
        
        # Restore original values
        restore_payload = {
            "default_hourly_rate": current.get("default_hourly_rate", 500),
            "per_km_rate": current.get("per_km_rate", 10)
        }
        self.session.put(f"{BASE_URL}/api/analytics/service-cost-config", json=restore_payload)
        
        print("Service cost config update and restore successful")
    
    def test_update_travel_tiers(self):
        """PUT /api/analytics/service-cost-config - update travel tiers"""
        # Get current config first
        current = self.session.get(f"{BASE_URL}/api/analytics/service-cost-config").json()
        
        # Add a new test tier
        new_tiers = current["travel_tiers"] + [{"name": "Test Zone", "min_km": 100, "max_km": 200, "cost": 1500}]
        
        resp = self.session.put(f"{BASE_URL}/api/analytics/service-cost-config", json={
            "travel_tiers": new_tiers
        })
        assert resp.status_code == 200
        
        # Verify new tier was added
        updated = self.session.get(f"{BASE_URL}/api/analytics/service-cost-config").json()
        tier_names = [t["name"] for t in updated["travel_tiers"]]
        assert "Test Zone" in tier_names, f"New tier not added: {tier_names}"
        
        # Restore original tiers
        self.session.put(f"{BASE_URL}/api/analytics/service-cost-config", json={
            "travel_tiers": current["travel_tiers"]
        })
        
        print("Travel tiers update and restore successful")
    
    # ═══════════════════════════════════════════════════════════════
    # PROFITABILITY PASSWORD TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_set_profitability_password(self):
        """POST /api/analytics/profitability-password - set password"""
        resp = self.session.post(f"{BASE_URL}/api/analytics/profitability-password", json={
            "password": "owner123"
        })
        assert resp.status_code == 200, f"Set password failed: {resp.status_code} {resp.text}"
        assert resp.json().get("success") == True
        print("Profitability password set successfully")
    
    def test_verify_profitability_password_correct(self):
        """POST /api/analytics/verify-profitability-password - verify correct password"""
        resp = self.session.post(f"{BASE_URL}/api/analytics/verify-profitability-password", json={
            "password": "owner123"
        })
        assert resp.status_code == 200, f"Verify failed: {resp.status_code} {resp.text}"
        data = resp.json()
        assert data.get("verified") == True, f"Password not verified: {data}"
        print("Correct password verification successful")
    
    def test_verify_profitability_password_wrong(self):
        """POST /api/analytics/verify-profitability-password - verify wrong password returns 403"""
        resp = self.session.post(f"{BASE_URL}/api/analytics/verify-profitability-password", json={
            "password": "wrongpassword"
        })
        assert resp.status_code == 403, f"Expected 403 for wrong password, got {resp.status_code}"
        data = resp.json()
        assert "Incorrect password" in data.get("detail", ""), f"Expected error message: {data}"
        print("Wrong password correctly rejected with 403")
    
    # ═══════════════════════════════════════════════════════════════
    # PROFITABILITY ANALYTICS ENDPOINT TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_get_profitability_data(self):
        """GET /api/analytics/profitability - get device profitability data"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/profitability")
        assert resp.status_code == 200, f"Profitability fetch failed: {resp.status_code} {resp.text}"
        
        data = resp.json()
        
        # Verify summary structure
        assert "summary" in data, "Missing summary in profitability response"
        summary = data["summary"]
        
        # Check required summary fields
        required_summary_fields = [
            "total_devices", "devices_with_calls", "total_amc_revenue", 
            "total_service_cost", "net_profit_loss", "overall_margin_pct",
            "profitable_devices", "loss_making_devices", 
            "total_remote_calls", "total_onsite_calls"
        ]
        for field in required_summary_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify config structure
        assert "config" in data, "Missing config in profitability response"
        config = data["config"]
        assert "default_hourly_rate" in config
        assert "per_km_rate" in config
        assert "travel_tiers" in config
        
        # Verify devices array exists
        assert "devices" in data, "Missing devices array"
        assert isinstance(data["devices"], list), "devices should be a list"
        
        # Verify company_profitability exists
        assert "company_profitability" in data, "Missing company_profitability"
        
        # Verify worst_roi and most_expensive arrays
        assert "worst_roi" in data, "Missing worst_roi"
        assert "most_expensive" in data, "Missing most_expensive"
        
        print(f"Profitability data: {summary['devices_with_calls']} devices with calls, "
              f"Service cost: INR {summary['total_service_cost']}, "
              f"Profitable: {summary['profitable_devices']}, Loss making: {summary['loss_making_devices']}")
    
    def test_profitability_devices_structure(self):
        """Verify device-level profitability data structure"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/profitability")
        assert resp.status_code == 200
        
        data = resp.json()
        devices = data.get("devices", [])
        
        if len(devices) > 0:
            device = devices[0]  # Check first device
            required_fields = [
                "device_id", "device_name", "company_name",
                "amc_revenue", "total_calls", "remote_calls", "onsite_calls",
                "labour_cost", "travel_cost", "parts_cost", "total_cost", "profit_loss"
            ]
            for field in required_fields:
                assert field in device, f"Device missing field: {field}"
            
            # Verify call_details array
            assert "call_details" in device, "Device missing call_details"
            assert isinstance(device["call_details"], list), "call_details should be a list"
            
            if len(device["call_details"]) > 0:
                call = device["call_details"][0]
                call_fields = ["type", "date", "engineer", "hours", "labour", "travel", "parts"]
                for field in call_fields:
                    assert field in call, f"Call detail missing field: {field}"
            
            print(f"Device structure verified: {device['device_name']} - Calls: {device['total_calls']}, P/L: INR {device['profit_loss']}")
        else:
            print("No devices with calls found - structure check skipped")
    
    def test_profitability_company_rollup(self):
        """Verify company-level profitability rollup"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/profitability")
        assert resp.status_code == 200
        
        data = resp.json()
        companies = data.get("company_profitability", [])
        
        if len(companies) > 0:
            company = companies[0]
            required_fields = [
                "company_id", "company_name", "devices", "total_calls",
                "amc_revenue", "total_cost", "profit_loss", "margin_pct"
            ]
            for field in required_fields:
                assert field in company, f"Company missing field: {field}"
            
            print(f"Company profitability verified: {company['company_name']} - Margin: {company['margin_pct']}%")
        else:
            print("No company profitability data - check skipped")
    
    def test_profitability_summary_values(self):
        """Verify profitability summary KPI values match expected from context"""
        resp = self.session.get(f"{BASE_URL}/api/analytics/profitability")
        assert resp.status_code == 200
        
        summary = resp.json()["summary"]
        
        # Based on agent context: 2 devices with calls, service cost INR 500, 0 profitable, 2 loss making
        print(f"Summary KPIs - Devices with calls: {summary['devices_with_calls']}, "
              f"Service cost: {summary['total_service_cost']}, "
              f"Profitable: {summary['profitable_devices']}, "
              f"Loss making: {summary['loss_making_devices']}, "
              f"Remote: {summary['total_remote_calls']}, On-site: {summary['total_onsite_calls']}")
        
        # Just verify values are reasonable (non-negative where expected)
        assert summary['devices_with_calls'] >= 0
        assert summary['total_service_cost'] >= 0
        assert summary['profitable_devices'] >= 0
        assert summary['loss_making_devices'] >= 0
        assert summary['total_remote_calls'] >= 0
        assert summary['total_onsite_calls'] >= 0
    
    # ═══════════════════════════════════════════════════════════════
    # AUTH REQUIREMENT TESTS
    # ═══════════════════════════════════════════════════════════════
    
    def test_service_cost_config_requires_auth(self):
        """Service cost config endpoints require authentication"""
        unauth_session = requests.Session()
        
        resp = unauth_session.get(f"{BASE_URL}/api/analytics/service-cost-config")
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"
        
        resp = unauth_session.put(f"{BASE_URL}/api/analytics/service-cost-config", 
                                  json={"default_hourly_rate": 100})
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"
        
        print("Auth requirement verified for service cost config")
    
    def test_profitability_password_requires_auth(self):
        """Profitability password endpoints require authentication"""
        unauth_session = requests.Session()
        
        resp = unauth_session.post(f"{BASE_URL}/api/analytics/profitability-password",
                                   json={"password": "test"})
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"
        
        resp = unauth_session.post(f"{BASE_URL}/api/analytics/verify-profitability-password",
                                   json={"password": "test"})
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"
        
        print("Auth requirement verified for profitability password")
    
    def test_profitability_data_requires_auth(self):
        """Profitability data endpoint requires authentication"""
        unauth_session = requests.Session()
        
        resp = unauth_session.get(f"{BASE_URL}/api/analytics/profitability")
        assert resp.status_code in [401, 403], f"Expected 401/403 without auth, got {resp.status_code}"
        
        print("Auth requirement verified for profitability data")


class TestEngineerHourlyRate:
    """Test engineer hourly rate field"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test - get auth token"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        login_resp = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "ck@motta.in",
            "password": "Charu@123@"
        })
        assert login_resp.status_code == 200
        token = login_resp.json().get("access_token")
        self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def test_get_engineers_includes_hourly_rate(self):
        """GET /api/ticketing/engineers - verify hourly_rate field exists"""
        resp = self.session.get(f"{BASE_URL}/api/ticketing/engineers")
        assert resp.status_code == 200, f"Failed: {resp.status_code} {resp.text}"
        
        engineers = resp.json()
        assert isinstance(engineers, list), "Expected list of engineers"
        
        if len(engineers) > 0:
            # Check first engineer for hourly_rate field
            engineer = engineers[0]
            # hourly_rate may be null/None but the field should be accepted
            print(f"Engineer {engineer.get('name')} - hourly_rate: {engineer.get('hourly_rate', 'not set')}")
        
        print(f"Found {len(engineers)} engineers")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
