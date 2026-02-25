"""
Ticketing System V2 API Tests
=============================
Tests for the new workflow-driven ticketing system.
"""

import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL')
if BASE_URL:
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
TEST_EMAIL = "ck@motta.in"
TEST_PASSWORD = "Charu@123@"


@pytest.fixture(scope="session")
def auth_headers():
    """Login and get authentication headers"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    })
    assert response.status_code == 200, f"Login failed: {response.text}"
    data = response.json()
    token = data.get("access_token")
    assert token, "No access_token in response"
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


class TestAuthentication:
    """Verify authentication"""
    
    def test_login_works(self, auth_headers):
        """Verify we can login"""
        assert auth_headers is not None
        assert "Authorization" in auth_headers
        print(f"✓ Authentication successful")


class TestHelpTopics:
    """Test Help Topics endpoints - master data for ticket creation"""
    
    def test_list_help_topics(self, auth_headers):
        """GET /api/ticketing/help-topics - should return seeded help topics"""
        response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        topics = response.json()
        assert isinstance(topics, list), "Expected list of topics"
        assert len(topics) >= 10, f"Expected at least 10 help topics, got {len(topics)}"
        
        # Verify topic structure
        if topics:
            topic = topics[0]
            assert "id" in topic, "Topic missing id"
            assert "name" in topic, "Topic missing name"
            assert "slug" in topic, "Topic missing slug"
            
        topic_names = [t["name"] for t in topics]
        print(f"✓ Found {len(topics)} help topics: {topic_names[:5]}...")
        
    def test_get_single_help_topic(self, auth_headers):
        """GET /api/ticketing/help-topics/{id} - get topic with form and workflow"""
        list_response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=auth_headers)
        topics = list_response.json()
        assert len(topics) > 0, "No topics found"
        
        topic_id = topics[0]["id"]
        response = requests.get(f"{BASE_URL}/api/ticketing/help-topics/{topic_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        topic = response.json()
        assert topic["id"] == topic_id
        print(f"✓ Got topic '{topic['name']}' with form: {topic.get('form_id') is not None}, workflow: {topic.get('workflow_id') is not None}")


class TestForms:
    """Test Forms endpoints - custom form templates"""
    
    def test_list_forms(self, auth_headers):
        """GET /api/ticketing/forms - should return forms"""
        response = requests.get(f"{BASE_URL}/api/ticketing/forms", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        forms = response.json()
        assert isinstance(forms, list), "Expected list of forms"
        
        if forms:
            form = forms[0]
            assert "id" in form
            assert "name" in form
            assert "fields" in form
            print(f"✓ Found {len(forms)} forms, first form '{form['name']}' has {len(form.get('fields', []))} fields")
        else:
            print("✓ Forms endpoint working (no forms found)")


class TestWorkflows:
    """Test Workflows endpoints - workflow templates with stages"""
    
    def test_list_workflows(self, auth_headers):
        """GET /api/ticketing/workflows - should return workflows with stages"""
        response = requests.get(f"{BASE_URL}/api/ticketing/workflows", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        workflows = response.json()
        assert isinstance(workflows, list), "Expected list of workflows"
        
        if workflows:
            workflow = workflows[0]
            assert "id" in workflow
            assert "name" in workflow
            assert "stages" in workflow
            stages = workflow.get("stages", [])
            print(f"✓ Found {len(workflows)} workflows, first workflow '{workflow['name']}' has {len(stages)} stages")


class TestTeams:
    """Test Teams endpoints"""
    
    def test_list_teams(self, auth_headers):
        """GET /api/ticketing/teams - should return teams"""
        response = requests.get(f"{BASE_URL}/api/ticketing/teams", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        teams = response.json()
        assert isinstance(teams, list), "Expected list of teams"
        
        if teams:
            team = teams[0]
            assert "id" in team
            assert "name" in team
            print(f"✓ Found {len(teams)} teams: {[t['name'] for t in teams[:4]]}...")


class TestRoles:
    """Test Roles endpoints"""
    
    def test_list_roles(self, auth_headers):
        """GET /api/ticketing/roles - should return roles"""
        response = requests.get(f"{BASE_URL}/api/ticketing/roles", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        roles = response.json()
        assert isinstance(roles, list), "Expected list of roles"
        
        if roles:
            role = roles[0]
            assert "id" in role
            assert "name" in role
            assert "permissions" in role
            print(f"✓ Found {len(roles)} roles: {[r['name'] for r in roles[:4]]}...")


class TestSLAPolicies:
    """Test SLA Policies endpoints"""
    
    def test_list_sla_policies(self, auth_headers):
        """GET /api/ticketing/sla-policies - should return SLA policies"""
        response = requests.get(f"{BASE_URL}/api/ticketing/sla-policies", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        policies = response.json()
        assert isinstance(policies, list), "Expected list of policies"
        
        if policies:
            policy = policies[0]
            assert "id" in policy
            assert "name" in policy
            print(f"✓ Found {len(policies)} SLA policies: {[p['name'] for p in policies]}")


class TestPriorities:
    """Test Priorities endpoints"""
    
    def test_list_priorities(self, auth_headers):
        """GET /api/ticketing/priorities - should return priorities"""
        response = requests.get(f"{BASE_URL}/api/ticketing/priorities", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        priorities = response.json()
        assert isinstance(priorities, list), "Expected list of priorities"
        
        if priorities:
            priority = priorities[0]
            assert "id" in priority
            assert "name" in priority
            print(f"✓ Found {len(priorities)} priorities: {[p['name'] for p in priorities]}")


class TestCannedResponses:
    """Test Canned Responses endpoints"""
    
    def test_list_canned_responses(self, auth_headers):
        """GET /api/ticketing/canned-responses - should return canned responses"""
        response = requests.get(f"{BASE_URL}/api/ticketing/canned-responses", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        responses_list = response.json()
        assert isinstance(responses_list, list), "Expected list of canned responses"
        
        if responses_list:
            canned = responses_list[0]
            assert "id" in canned
            assert "name" in canned
            assert "body" in canned
            print(f"✓ Found {len(responses_list)} canned responses")
        else:
            print("✓ Canned responses endpoint working (no responses found)")


class TestTickets:
    """Test Ticket CRUD operations"""
    
    @pytest.fixture(scope="class")
    def help_topic_id(self, auth_headers):
        """Get a help topic ID for ticket creation"""
        response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=auth_headers)
        topics = response.json()
        assert len(topics) > 0, "No help topics available"
        return topics[0]["id"]
    
    def test_list_tickets(self, auth_headers):
        """GET /api/ticketing/tickets - list tickets with pagination"""
        response = requests.get(f"{BASE_URL}/api/ticketing/tickets", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        data = response.json()
        assert "tickets" in data, "Missing tickets field"
        assert "total" in data, "Missing total field"
        assert "page" in data, "Missing page field"
        assert "pages" in data, "Missing pages field"
        
        print(f"✓ Tickets list: {len(data['tickets'])} tickets, total: {data['total']}, pages: {data['pages']}")
    
    def test_create_ticket(self, auth_headers, help_topic_id):
        """POST /api/ticketing/tickets - create a new ticket"""
        ticket_data = {
            "help_topic_id": help_topic_id,
            "subject": "TEST_V2_Ticket - Automated Test",
            "description": "This is an automated test ticket for V2 ticketing system",
            "contact_name": "Test User",
            "contact_email": "test@example.com",
            "contact_phone": "+1234567890"
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/tickets", 
                                headers=auth_headers, 
                                json=ticket_data)
        assert response.status_code == 200, f"Failed to create ticket: {response.text}"
        
        ticket = response.json()
        assert "id" in ticket, "Ticket missing id"
        assert "ticket_number" in ticket, "Ticket missing ticket_number"
        assert ticket["subject"] == ticket_data["subject"]
        assert ticket["is_open"] == True
        
        print(f"✓ Created ticket #{ticket['ticket_number']}, id: {ticket['id']}")
        return ticket
    
    def test_get_ticket_detail(self, auth_headers, help_topic_id):
        """GET /api/ticketing/tickets/{id} - get ticket with workflow, tasks, timeline"""
        # First create a ticket
        ticket_data = {
            "help_topic_id": help_topic_id,
            "subject": "TEST_V2_Detail - Get Detail Test",
            "description": "Testing ticket detail retrieval",
            "contact_name": "Detail Test"
        }
        create_response = requests.post(f"{BASE_URL}/api/ticketing/tickets", 
                                       headers=auth_headers, 
                                       json=ticket_data)
        created_ticket = create_response.json()
        ticket_id = created_ticket["id"]
        
        # Get ticket detail
        response = requests.get(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        ticket = response.json()
        assert ticket["id"] == ticket_id
        assert "timeline" in ticket, "Ticket missing timeline"
        
        # Check timeline has creation entry
        timeline = ticket.get("timeline", [])
        assert len(timeline) >= 1, "Timeline should have at least creation entry"
        
        print(f"✓ Got ticket detail #{ticket['ticket_number']}, timeline entries: {len(timeline)}")


class TestTicketComments:
    """Test adding comments to tickets"""
    
    @pytest.fixture(scope="class")
    def test_ticket(self, auth_headers):
        """Create a ticket for comment tests"""
        topics_response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=auth_headers)
        topics = topics_response.json()
        
        ticket_data = {
            "help_topic_id": topics[0]["id"],
            "subject": "TEST_V2_Comment - Comment Test Ticket",
            "description": "Testing comments functionality",
            "contact_name": "Comment Tester"
        }
        response = requests.post(f"{BASE_URL}/api/ticketing/tickets", headers=auth_headers, json=ticket_data)
        return response.json()
    
    def test_add_comment(self, auth_headers, test_ticket):
        """POST /api/ticketing/tickets/{id}/comment - add comment to ticket"""
        ticket_id = test_ticket["id"]
        
        comment_data = {
            "content": "This is a test comment from automated testing",
            "is_internal": False
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/comment", 
                                headers=auth_headers, 
                                json=comment_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        comment = response.json()
        assert "id" in comment
        assert comment["description"] == comment_data["content"]
        
        print(f"✓ Added comment to ticket #{test_ticket['ticket_number']}")
    
    def test_add_internal_comment(self, auth_headers, test_ticket):
        """POST /api/ticketing/tickets/{id}/comment - add internal note"""
        ticket_id = test_ticket["id"]
        
        comment_data = {
            "content": "This is an internal note - not visible to customer",
            "is_internal": True
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/comment", 
                                headers=auth_headers, 
                                json=comment_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        comment = response.json()
        assert comment["is_internal"] == True
        
        print(f"✓ Added internal note to ticket #{test_ticket['ticket_number']}")


class TestTicketTransitions:
    """Test ticket stage transitions"""
    
    def test_transition_ticket(self, auth_headers):
        """POST /api/ticketing/tickets/{id}/transition - move ticket to next stage"""
        # Get help topics with workflow
        topics_response = requests.get(f"{BASE_URL}/api/ticketing/help-topics", headers=auth_headers)
        topics = topics_response.json()
        
        # Find a topic with a workflow
        topic_with_workflow = None
        for topic in topics:
            if topic.get("workflow_id"):
                topic_with_workflow = topic
                break
        
        if not topic_with_workflow:
            pytest.skip("No help topics with workflows found")
        
        # Create ticket
        ticket_data = {
            "help_topic_id": topic_with_workflow["id"],
            "subject": "TEST_V2_Transition - Transition Test Ticket",
            "description": "Testing transitions",
            "contact_name": "Transition Tester"
        }
        create_response = requests.post(f"{BASE_URL}/api/ticketing/tickets", headers=auth_headers, json=ticket_data)
        ticket = create_response.json()
        ticket_id = ticket["id"]
        
        # Get ticket with full workflow to find available transitions
        detail_response = requests.get(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}", headers=auth_headers)
        ticket_detail = detail_response.json()
        
        workflow = ticket_detail.get("workflow")
        if not workflow or not workflow.get("stages"):
            pytest.skip("Ticket has no workflow stages")
        
        # Find current stage and its transitions
        current_stage_id = ticket_detail.get("current_stage_id")
        current_stage = None
        for stage in workflow["stages"]:
            if stage["id"] == current_stage_id:
                current_stage = stage
                break
        
        if not current_stage or not current_stage.get("transitions"):
            print(f"✓ Ticket at stage '{ticket_detail.get('current_stage_name')}' with no transitions - valid state")
            return
        
        # Get first transition
        transition = current_stage["transitions"][0]
        
        # Execute transition
        transition_data = {
            "transition_id": transition["id"],
            "notes": "Automated test transition"
        }
        
        response = requests.post(f"{BASE_URL}/api/ticketing/tickets/{ticket_id}/transition", 
                                headers=auth_headers, 
                                json=transition_data)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        updated_ticket = response.json()
        print(f"✓ Transitioned ticket from '{ticket_detail.get('current_stage_name')}' to '{updated_ticket.get('current_stage_name')}'")


class TestTicketStats:
    """Test ticketing statistics endpoint"""
    
    def test_get_stats(self, auth_headers):
        """GET /api/ticketing/stats - get ticket statistics"""
        response = requests.get(f"{BASE_URL}/api/ticketing/stats", headers=auth_headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        
        stats = response.json()
        assert "total" in stats, "Stats missing total"
        assert "open" in stats, "Stats missing open count"
        assert "closed" in stats, "Stats missing closed count"
        
        print(f"✓ Stats: Total={stats['total']}, Open={stats['open']}, Closed={stats['closed']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
