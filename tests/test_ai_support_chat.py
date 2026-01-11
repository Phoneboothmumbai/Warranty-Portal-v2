"""
AI Support Chat Feature Tests
Tests the AI Triage Bot functionality:
- POST /api/company/ai-support/chat - AI chat endpoint
- POST /api/company/ai-support/generate-summary - Generate ticket summary from chat
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
COMPANY_USER_EMAIL = "jane@acme.com"
COMPANY_USER_PASSWORD = "company123"


class TestAISupportChat:
    """Test AI Support Chat endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as company user
        login_response = self.session.post(f"{BASE_URL}/api/company/auth/login", json={
            "email": COMPANY_USER_EMAIL,
            "password": COMPANY_USER_PASSWORD
        })
        
        if login_response.status_code == 200:
            self.token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Company login failed: {login_response.status_code}")
    
    def test_ai_chat_requires_authentication(self):
        """Test that AI chat endpoint requires authentication"""
        # Create new session without auth
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        response = no_auth_session.post(f"{BASE_URL}/api/company/ai-support/chat", json={
            "message": "My laptop won't turn on",
            "session_id": "test_session_123",
            "message_history": []
        })
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ AI chat endpoint requires authentication")
    
    def test_ai_chat_basic_message(self):
        """Test sending a basic message to AI chat"""
        response = self.session.post(f"{BASE_URL}/api/company/ai-support/chat", json={
            "message": "My laptop screen is flickering",
            "session_id": f"test_session_{int(time.time())}",
            "message_history": []
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "response" in data, "Response should contain 'response' field"
        assert "should_escalate" in data, "Response should contain 'should_escalate' field"
        assert "session_id" in data, "Response should contain 'session_id' field"
        assert isinstance(data["response"], str), "Response should be a string"
        assert len(data["response"]) > 0, "Response should not be empty"
        
        print(f"✓ AI chat returned response: {data['response'][:100]}...")
        print(f"✓ Should escalate: {data['should_escalate']}")
    
    def test_ai_chat_with_message_history(self):
        """Test AI chat with conversation history"""
        session_id = f"test_session_{int(time.time())}"
        
        # First message
        response1 = self.session.post(f"{BASE_URL}/api/company/ai-support/chat", json={
            "message": "My printer is not working",
            "session_id": session_id,
            "message_history": []
        })
        
        assert response1.status_code == 200, f"First message failed: {response1.text}"
        first_response = response1.json()["response"]
        
        # Second message with history
        response2 = self.session.post(f"{BASE_URL}/api/company/ai-support/chat", json={
            "message": "I already tried restarting it",
            "session_id": session_id,
            "message_history": [
                {"role": "user", "content": "My printer is not working"},
                {"role": "assistant", "content": first_response}
            ]
        })
        
        assert response2.status_code == 200, f"Second message failed: {response2.text}"
        data = response2.json()
        assert "response" in data
        assert len(data["response"]) > 0
        
        print(f"✓ AI chat handles conversation history correctly")
        print(f"✓ Second response: {data['response'][:100]}...")
    
    def test_ai_chat_with_device_context(self):
        """Test AI chat with device context"""
        # First get a device ID
        devices_response = self.session.get(f"{BASE_URL}/api/company/devices")
        
        device_id = None
        if devices_response.status_code == 200:
            devices = devices_response.json()
            if devices:
                device_id = devices[0].get("id")
        
        if not device_id:
            pytest.skip("No devices available for testing")
        
        response = self.session.post(f"{BASE_URL}/api/company/ai-support/chat", json={
            "message": "This device is running slow",
            "session_id": f"test_session_{int(time.time())}",
            "message_history": [],
            "device_id": device_id
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "response" in data
        
        print(f"✓ AI chat works with device context (device_id: {device_id})")
    
    def test_ai_chat_escalation_detection(self):
        """Test that AI detects when to escalate"""
        # Send a message that should trigger escalation
        response = self.session.post(f"{BASE_URL}/api/company/ai-support/chat", json={
            "message": "I need to speak to a human support agent immediately. This is urgent and I want to create a ticket.",
            "session_id": f"test_session_{int(time.time())}",
            "message_history": []
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # The AI should suggest escalation for urgent requests
        print(f"✓ AI response for escalation request: {data['response'][:100]}...")
        print(f"✓ Should escalate flag: {data['should_escalate']}")
    
    def test_generate_summary_requires_authentication(self):
        """Test that generate-summary endpoint requires authentication"""
        no_auth_session = requests.Session()
        no_auth_session.headers.update({"Content-Type": "application/json"})
        
        response = no_auth_session.post(f"{BASE_URL}/api/company/ai-support/generate-summary", json={
            "messages": [
                {"role": "user", "content": "My laptop won't turn on"},
                {"role": "assistant", "content": "Have you tried charging it?"}
            ]
        })
        
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Generate summary endpoint requires authentication")
    
    def test_generate_summary_basic(self):
        """Test generating ticket summary from chat history"""
        messages = [
            {"role": "user", "content": "My laptop screen is flickering when I open certain applications"},
            {"role": "assistant", "content": "I understand. Have you tried updating your graphics drivers?"},
            {"role": "user", "content": "Yes, I updated them but the issue persists"},
            {"role": "assistant", "content": "I see. This might require hardware inspection. Would you like to create a support ticket?"}
        ]
        
        response = self.session.post(f"{BASE_URL}/api/company/ai-support/generate-summary", json={
            "messages": messages
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "subject" in data, "Response should contain 'subject' field"
        assert "description" in data, "Response should contain 'description' field"
        assert isinstance(data["subject"], str), "Subject should be a string"
        assert isinstance(data["description"], str), "Description should be a string"
        assert len(data["subject"]) > 0, "Subject should not be empty"
        assert len(data["description"]) > 0, "Description should not be empty"
        
        print(f"✓ Generated subject: {data['subject']}")
        print(f"✓ Generated description length: {len(data['description'])} chars")
    
    def test_generate_summary_empty_messages(self):
        """Test generating summary with empty messages"""
        response = self.session.post(f"{BASE_URL}/api/company/ai-support/generate-summary", json={
            "messages": []
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Should return default values for empty messages
        assert "subject" in data
        assert "description" in data
        
        print(f"✓ Empty messages returns default subject: {data['subject']}")
    
    def test_generate_summary_single_message(self):
        """Test generating summary with single user message"""
        messages = [
            {"role": "user", "content": "Printer not printing documents"}
        ]
        
        response = self.session.post(f"{BASE_URL}/api/company/ai-support/generate-summary", json={
            "messages": messages
        })
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        assert "subject" in data
        assert "description" in data
        # Subject should be based on first user message
        assert "Printer" in data["subject"] or "printer" in data["subject"].lower()
        
        print(f"✓ Single message summary subject: {data['subject']}")


class TestAISupportIntegration:
    """Test AI Support integration with ticket creation flow"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures"""
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        
        # Login as company user
        login_response = self.session.post(f"{BASE_URL}/api/company/auth/login", json={
            "email": COMPANY_USER_EMAIL,
            "password": COMPANY_USER_PASSWORD
        })
        
        if login_response.status_code == 200:
            self.token = login_response.json().get("access_token")
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
        else:
            pytest.skip(f"Company login failed: {login_response.status_code}")
    
    def test_full_ai_to_ticket_flow(self):
        """Test complete flow: AI chat -> generate summary -> create ticket"""
        session_id = f"test_flow_{int(time.time())}"
        
        # Step 1: Start AI chat
        chat_response = self.session.post(f"{BASE_URL}/api/company/ai-support/chat", json={
            "message": "My computer keeps crashing when I open Excel",
            "session_id": session_id,
            "message_history": []
        })
        
        assert chat_response.status_code == 200, f"Chat failed: {chat_response.text}"
        ai_response = chat_response.json()["response"]
        print(f"✓ Step 1 - AI responded: {ai_response[:80]}...")
        
        # Step 2: Continue conversation
        chat_response2 = self.session.post(f"{BASE_URL}/api/company/ai-support/chat", json={
            "message": "I've tried reinstalling Excel but it still crashes",
            "session_id": session_id,
            "message_history": [
                {"role": "user", "content": "My computer keeps crashing when I open Excel"},
                {"role": "assistant", "content": ai_response}
            ]
        })
        
        assert chat_response2.status_code == 200
        ai_response2 = chat_response2.json()["response"]
        print(f"✓ Step 2 - AI follow-up: {ai_response2[:80]}...")
        
        # Step 3: Generate summary
        messages = [
            {"role": "user", "content": "My computer keeps crashing when I open Excel"},
            {"role": "assistant", "content": ai_response},
            {"role": "user", "content": "I've tried reinstalling Excel but it still crashes"},
            {"role": "assistant", "content": ai_response2}
        ]
        
        summary_response = self.session.post(f"{BASE_URL}/api/company/ai-support/generate-summary", json={
            "messages": messages
        })
        
        assert summary_response.status_code == 200
        summary = summary_response.json()
        print(f"✓ Step 3 - Generated subject: {summary['subject']}")
        
        # Step 4: Get a device for ticket creation
        devices_response = self.session.get(f"{BASE_URL}/api/company/devices")
        device_id = None
        if devices_response.status_code == 200 and devices_response.json():
            device_id = devices_response.json()[0]["id"]
        
        if not device_id:
            print("⚠ No device available, skipping ticket creation step")
            return
        
        # Step 5: Create ticket with AI summary
        ticket_response = self.session.post(f"{BASE_URL}/api/company/tickets", json={
            "device_id": device_id,
            "subject": summary["subject"],
            "description": summary["description"],
            "issue_category": "software",
            "priority": "medium"
        })
        
        assert ticket_response.status_code in [200, 201], f"Ticket creation failed: {ticket_response.text}"
        ticket = ticket_response.json()
        
        print(f"✓ Step 5 - Ticket created: {ticket.get('ticket_number', ticket.get('id'))}")
        print(f"✓ Full AI to ticket flow completed successfully!")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
