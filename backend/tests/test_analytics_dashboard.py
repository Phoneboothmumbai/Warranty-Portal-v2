"""
Analytics Dashboard API Tests
Tests all 11 analytics endpoints for the Enterprise Warranty & Asset Tracking Portal:
- Executive Summary, Tickets, Workforce, Financial, Clients, Assets, SLA, Workflows, Inventory, Contracts, Operational Intelligence
"""

import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://asset-lifecycle-mgmt-1.preview.emergentagent.com').rstrip('/')

# Test credentials
ADMIN_EMAIL = "ck@motta.in"
ADMIN_PASSWORD = "Charu@123@"

class TestAnalyticsDashboard:
    """Test suite for Analytics Dashboard API endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Get authentication token for admin user"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "access_token" in data, "No access_token in response"
        return data["access_token"]
    
    @pytest.fixture(scope="class")
    def auth_headers(self, auth_token):
        """Auth headers for API requests"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }

    # ==================== Executive Summary Tests ====================
    def test_executive_summary_endpoint(self, auth_headers):
        """Test /api/analytics/executive-summary returns valid data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-summary?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify 8 KPI cards exist
        assert "kpis" in data, "Missing 'kpis' in response"
        kpis = data["kpis"]
        assert len(kpis) == 8, f"Expected 8 KPIs, got {len(kpis)}"
        
        # Check expected KPI labels
        expected_labels = ["Open Tickets", "Resolved This Period", "New Tickets", "Revenue", 
                          "Active Devices", "Companies", "Active Engineers", "Active Contracts"]
        actual_labels = [k["label"] for k in kpis]
        for label in expected_labels:
            assert label in actual_labels, f"Missing KPI: {label}"
        
        # Verify each KPI has value field
        for kpi in kpis:
            assert "value" in kpi, f"KPI {kpi.get('label')} missing value"
            assert "type" in kpi, f"KPI {kpi.get('label')} missing type"
        
        print(f"✓ Executive Summary: {len(kpis)} KPIs returned")

    # ==================== Ticket Intelligence Tests ====================
    def test_tickets_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/tickets returns ticket intelligence data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/tickets?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary fields
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_summary_fields = ["total_tickets", "period_tickets", "open_tickets", "closed_tickets",
                                   "unassigned", "assigned", "avg_resolution_hours", "p95_resolution_hours",
                                   "avg_first_response_hours", "reopen_rate"]
        for field in expected_summary_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify chart data arrays
        assert "volume_by_day" in data, "Missing volume_by_day"
        assert "stage_distribution" in data, "Missing stage_distribution"
        assert "priority_distribution" in data, "Missing priority_distribution"
        assert "topic_distribution" in data, "Missing topic_distribution"
        assert "source_distribution" in data, "Missing source_distribution"
        
        print(f"✓ Tickets Analytics: {summary['total_tickets']} total tickets, {summary['open_tickets']} open")

    # ==================== Workforce Performance Tests ====================
    def test_workforce_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/workforce returns workforce data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/workforce?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary fields (5 KPIs)
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_fields = ["total_engineers", "total_assigned_tickets", "avg_tickets_per_engineer",
                          "total_visits", "avg_first_time_fix"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify scorecards and workload
        assert "scorecards" in data, "Missing scorecards"
        assert "workload_distribution" in data, "Missing workload_distribution"
        
        # Verify scorecard structure
        if data["scorecards"]:
            scorecard = data["scorecards"][0]
            required_fields = ["name", "total_assigned", "closed", "avg_resolution_hours", 
                              "first_time_fix_rate", "parts_cost"]
            for field in required_fields:
                assert field in scorecard, f"Scorecard missing field: {field}"
        
        print(f"✓ Workforce Analytics: {summary['total_engineers']} engineers, {summary['total_visits']} visits")

    # ==================== Financial Analytics Tests ====================
    def test_financial_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/financial returns financial data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/financial?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary (6 KPIs)
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_fields = ["total_quoted", "total_approved", "conversion_rate",
                          "total_parts_cost", "pending_bills_total", "active_amc_contracts"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify chart data
        assert "quotation_pipeline" in data, "Missing quotation_pipeline"
        assert "revenue_by_month" in data, "Missing revenue_by_month"
        assert "aging_buckets" in data, "Missing aging_buckets"
        
        print(f"✓ Financial Analytics: Total quoted ₹{summary['total_quoted']}, Approved ₹{summary['total_approved']}")

    # ==================== Client Health Tests ====================
    def test_clients_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/clients returns client health data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/clients?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary (4 KPIs)
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_fields = ["total_companies", "avg_health_score", "at_risk_companies", "total_devices_managed"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify companies list with health scores
        assert "companies" in data, "Missing companies list"
        if data["companies"]:
            company = data["companies"][0]
            assert "health_score" in company, "Company missing health_score"
            assert "device_count" in company, "Company missing device_count"
            assert "total_tickets" in company, "Company missing total_tickets"
        
        print(f"✓ Clients Analytics: {summary['total_companies']} companies, avg health score {summary['avg_health_score']}")

    # ==================== Asset Intelligence Tests ====================
    def test_assets_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/assets returns asset intelligence data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/assets",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary (7 KPIs)
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_fields = ["total_devices", "active_warranty", "expired_warranty",
                          "expiring_30d", "expiring_60d", "expiring_90d", "devices_with_tickets"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify chart data
        assert "warranty_timeline" in data, "Missing warranty_timeline"
        assert "brand_distribution" in data, "Missing brand_distribution"
        assert "age_distribution" in data, "Missing age_distribution"
        assert "failure_by_brand" in data, "Missing failure_by_brand"
        
        print(f"✓ Assets Analytics: {summary['total_devices']} devices, {summary['active_warranty']} with active warranty")

    # ==================== SLA Compliance Tests ====================
    def test_sla_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/sla returns SLA compliance data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/sla?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_fields = ["total_tickets", "sla_compliant", "sla_breached", 
                          "compliance_rate", "overdue", "escalated"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify breach data
        assert "breach_by_priority" in data, "Missing breach_by_priority"
        assert "breach_by_team" in data, "Missing breach_by_team"
        
        print(f"✓ SLA Analytics: {summary['compliance_rate']}% compliance rate, {summary['sla_breached']} breached")

    # ==================== Workflow Analytics Tests ====================
    def test_workflows_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/workflows returns workflow data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/workflows",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        assert "total_workflows" in summary, "Missing total_workflows"
        assert "total_active_tickets" in summary, "Missing total_active_tickets"
        
        # Verify workflows list with stage backlog
        assert "workflows" in data, "Missing workflows list"
        if data["workflows"]:
            workflow = data["workflows"][0]
            assert "name" in workflow, "Workflow missing name"
            assert "stage_backlog" in workflow, "Workflow missing stage_backlog"
            assert "open_tickets" in workflow, "Workflow missing open_tickets"
        
        print(f"✓ Workflows Analytics: {summary['total_workflows']} workflows, {summary['total_active_tickets']} active tickets")

    # ==================== Inventory Analytics Tests ====================
    def test_inventory_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/inventory returns inventory data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/inventory",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary (5 KPIs)
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_fields = ["total_products", "total_stock_items", "low_stock_alerts",
                          "total_transactions", "pending_part_requests"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify data arrays
        assert "stock_alerts" in data, "Missing stock_alerts"
        assert "top_consumed" in data, "Missing top_consumed"
        assert "transaction_trend" in data, "Missing transaction_trend"
        
        print(f"✓ Inventory Analytics: {summary['total_products']} products, {summary['low_stock_alerts']} alerts")

    # ==================== Contract Analytics Tests ====================
    def test_contracts_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/contracts returns contract data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/contracts",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_fields = ["total_contracts", "active_contracts", "expired_contracts",
                          "expiring_30d", "coverage_rate"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify chart data
        assert "type_distribution" in data, "Missing type_distribution"
        assert "expiry_pipeline" in data, "Missing expiry_pipeline"
        assert "by_company" in data, "Missing by_company"
        
        print(f"✓ Contracts Analytics: {summary['total_contracts']} contracts, {summary['active_contracts']} active")

    # ==================== Operational Intelligence Tests ====================
    def test_operational_analytics_endpoint(self, auth_headers):
        """Test /api/analytics/operational returns AI insights data"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/operational?days=90",
            headers=auth_headers
        )
        assert response.status_code == 200, f"Failed: {response.status_code} - {response.text}"
        data = response.json()
        
        # Verify summary
        assert "summary" in data, "Missing 'summary' in response"
        summary = data["summary"]
        expected_fields = ["trend_direction", "predicted_next_week", "anomalies_detected",
                          "recommendations_count"]
        for field in expected_fields:
            assert field in summary, f"Missing summary field: {field}"
        
        # Verify chart data
        assert "weekly_trend" in data, "Missing weekly_trend"
        assert "anomalies" in data, "Missing anomalies"
        assert "recommendations" in data, "Missing recommendations"
        assert "top_issues" in data, "Missing top_issues"
        
        print(f"✓ Operational Intelligence: Trend {summary['trend_direction']}, {summary['anomalies_detected']} anomalies")

    # ==================== Period Selector Tests ====================
    def test_period_selector_7_days(self, auth_headers):
        """Test analytics with 7-day period"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-summary?days=7",
            headers=auth_headers
        )
        assert response.status_code == 200, f"7-day period failed: {response.text}"
        data = response.json()
        assert "kpis" in data
        print("✓ Period 7 days: Works correctly")

    def test_period_selector_30_days(self, auth_headers):
        """Test analytics with 30-day period"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-summary?days=30",
            headers=auth_headers
        )
        assert response.status_code == 200, f"30-day period failed: {response.text}"
        data = response.json()
        assert "kpis" in data
        print("✓ Period 30 days: Works correctly")

    def test_period_selector_90_days(self, auth_headers):
        """Test analytics with 90-day period"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-summary?days=90",
            headers=auth_headers
        )
        assert response.status_code == 200, f"90-day period failed: {response.text}"
        data = response.json()
        assert "kpis" in data
        print("✓ Period 90 days: Works correctly")

    def test_period_selector_365_days(self, auth_headers):
        """Test analytics with 365-day period"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-summary?days=365",
            headers=auth_headers
        )
        assert response.status_code == 200, f"365-day period failed: {response.text}"
        data = response.json()
        assert "kpis" in data
        print("✓ Period 365 days: Works correctly")

    # ==================== Authorization Tests ====================
    def test_analytics_requires_auth(self):
        """Test that analytics endpoints require authentication"""
        response = requests.get(
            f"{BASE_URL}/api/analytics/executive-summary?days=30",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Auth required: Correctly returns 401/403 without token")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
