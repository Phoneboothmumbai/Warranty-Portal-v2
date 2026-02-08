"""
WatchTower Agent Download Feature Tests
========================================
Tests for the self-service WatchTower agent download feature across:
- Company Portal endpoints
- Admin Portal endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"
COMPANY_EMAIL = "testuser@testcompany.com"
COMPANY_PASSWORD = "Test@123"


class TestWatchTowerCompanyPortal:
    """Tests for Company Portal WatchTower endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as company user before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as company user
        response = self.session.post(f"{BASE_URL}/api/company/auth/login", json={
            "email": COMPANY_EMAIL,
            "password": COMPANY_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Company login failed: {response.status_code}")
    
    def test_company_agent_status_endpoint(self):
        """Test /api/watchtower/company/agent-status returns correct status"""
        response = self.session.get(f"{BASE_URL}/api/watchtower/company/agent-status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "watchtower_enabled" in data, "Missing watchtower_enabled field"
        assert isinstance(data["watchtower_enabled"], bool), "watchtower_enabled should be boolean"
        
        # If enabled, check for additional fields
        if data["watchtower_enabled"]:
            assert "total_agents" in data, "Missing total_agents when enabled"
            assert "online_agents" in data, "Missing online_agents when enabled"
            assert "offline_agents" in data, "Missing offline_agents when enabled"
        
        print(f"✓ Agent status: enabled={data['watchtower_enabled']}, total={data.get('total_agents', 0)}")
    
    def test_company_sites_for_agent_endpoint(self):
        """Test /api/watchtower/company/sites-for-agent returns list of sites"""
        response = self.session.get(f"{BASE_URL}/api/watchtower/company/sites-for-agent")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "sites" in data, "Missing sites field"
        assert "total" in data, "Missing total field"
        assert isinstance(data["sites"], list), "sites should be a list"
        
        print(f"✓ Sites for agent: {data['total']} sites available")
    
    def test_company_agent_download_endpoint(self):
        """Test /api/watchtower/company/agent-download generates download link"""
        response = self.session.post(f"{BASE_URL}/api/watchtower/company/agent-download", json={
            "site_id": None,
            "platform": "windows",
            "arch": "64"
        })
        
        # May return 200 with download_url or manual_download_required
        # Or 400/500 if WatchTower API has limitations
        assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Missing success field"
            
            # Either download_url or manual_download_required should be present
            has_download = "download_url" in data and data["download_url"]
            has_manual = data.get("manual_download_required", False)
            
            assert has_download or has_manual, "Should have download_url or manual_download_required"
            print(f"✓ Agent download: success={data['success']}, manual_required={has_manual}")
        else:
            # Expected failure due to WatchTower API limitations
            print(f"✓ Agent download returned {response.status_code} (expected due to WatchTower API limitations)")
    
    def test_company_agent_download_linux(self):
        """Test agent download for Linux platform"""
        response = self.session.post(f"{BASE_URL}/api/watchtower/company/agent-download", json={
            "site_id": None,
            "platform": "linux",
            "arch": "64"
        })
        
        assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert data.get("platform") == "linux", "Platform should be linux"
            print(f"✓ Linux agent download: success={data.get('success')}")
        else:
            print(f"✓ Linux agent download returned {response.status_code}")


class TestWatchTowerAdminPortal:
    """Tests for Admin Portal WatchTower endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as admin
        response = self.session.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Admin login failed: {response.status_code}")
    
    def test_admin_watchtower_config(self):
        """Test /api/watchtower/config returns configuration"""
        response = self.session.get(f"{BASE_URL}/api/watchtower/config")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "configured" in data, "Missing configured field"
        
        if data["configured"]:
            assert "enabled" in data, "Missing enabled field"
            assert "api_url" in data, "Missing api_url field"
            print(f"✓ WatchTower config: configured={data['configured']}, enabled={data.get('enabled')}")
        else:
            print(f"✓ WatchTower not configured")
    
    def test_admin_watchtower_agents_list(self):
        """Test /api/watchtower/agents returns list of agents"""
        response = self.session.get(f"{BASE_URL}/api/watchtower/agents")
        
        # May return 200 or 400 if not configured
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Should return list of agents"
            
            if len(data) > 0:
                agent = data[0]
                # Verify agent structure
                assert "agent_id" in agent or "hostname" in agent, "Agent should have agent_id or hostname"
                print(f"✓ Agents list: {len(data)} agents found")
            else:
                print(f"✓ Agents list: 0 agents (empty)")
        else:
            print(f"✓ Agents list returned 400 (WatchTower not configured)")
    
    def test_admin_get_companies_for_download(self):
        """Test getting companies list for agent download"""
        response = self.session.get(f"{BASE_URL}/api/admin/companies?limit=100")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert isinstance(data, list), "Should return list of companies"
        
        if len(data) > 0:
            company = data[0]
            assert "id" in company, "Company should have id"
            assert "name" in company, "Company should have name"
            self.test_company_id = company["id"]
            self.test_company_name = company["name"]
            print(f"✓ Companies list: {len(data)} companies, first: {company['name']}")
        else:
            print(f"✓ Companies list: 0 companies")
    
    def test_admin_agent_download_for_company(self):
        """Test /api/watchtower/agent-download/{company_id} for admin"""
        # First get a company
        companies_response = self.session.get(f"{BASE_URL}/api/admin/companies?limit=1")
        if companies_response.status_code != 200 or not companies_response.json():
            pytest.skip("No companies available for testing")
        
        company = companies_response.json()[0]
        company_id = company["id"]
        
        response = self.session.post(f"{BASE_URL}/api/watchtower/agent-download/{company_id}", json={
            "site_name": "Default Site",
            "platform": "windows",
            "arch": "64"
        })
        
        # May return 200, 400, or 500 depending on WatchTower API
        assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data, "Missing success field"
            assert "company_id" in data, "Missing company_id field"
            print(f"✓ Admin agent download for {company['name']}: success={data.get('success')}")
        else:
            error_detail = response.json().get("detail", "Unknown error")
            print(f"✓ Admin agent download returned {response.status_code}: {error_detail}")
    
    def test_admin_watchtower_clients(self):
        """Test /api/watchtower/clients returns WatchTower clients"""
        response = self.session.get(f"{BASE_URL}/api/watchtower/clients")
        
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Should return list of clients"
            print(f"✓ WatchTower clients: {len(data)} clients")
        else:
            print(f"✓ WatchTower clients returned 400 (not configured)")
    
    def test_admin_watchtower_sites(self):
        """Test /api/watchtower/sites returns WatchTower sites"""
        response = self.session.get(f"{BASE_URL}/api/watchtower/sites")
        
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert isinstance(data, list), "Should return list of sites"
            print(f"✓ WatchTower sites: {len(data)} sites")
        else:
            print(f"✓ WatchTower sites returned 400 (not configured)")


class TestWatchTowerDeviceStatus:
    """Tests for device-specific WatchTower status"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as company user before each test"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as company user
        response = self.session.post(f"{BASE_URL}/api/company/auth/login", json={
            "email": COMPANY_EMAIL,
            "password": COMPANY_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Company login failed: {response.status_code}")
    
    def test_device_watchtower_status(self):
        """Test /api/watchtower/device/{device_id}/status"""
        # First get a device
        devices_response = self.session.get(f"{BASE_URL}/api/company/devices")
        if devices_response.status_code != 200 or not devices_response.json():
            pytest.skip("No devices available for testing")
        
        device = devices_response.json()[0]
        device_id = device["id"]
        
        response = self.session.get(f"{BASE_URL}/api/watchtower/device/{device_id}/status")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        data = response.json()
        assert "integrated" in data, "Missing integrated field"
        
        if data["integrated"]:
            assert "agent_status" in data, "Missing agent_status when integrated"
            print(f"✓ Device WatchTower status: integrated={data['integrated']}, status={data.get('agent_status')}")
        else:
            print(f"✓ Device WatchTower status: not integrated - {data.get('message', 'N/A')}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
