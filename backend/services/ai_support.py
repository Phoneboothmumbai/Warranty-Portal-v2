"""
AI Support Triage Service
Handles AI-powered troubleshooting before ticket creation
"""
import logging
import os
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

from emergentintegrations.llm.chat import LlmChat, UserMessage

logger = logging.getLogger(__name__)

EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

# System prompt for IT support triage - LIMITED to simple issues only
SYSTEM_PROMPT_TEMPLATE = """You are an AI IT Support Assistant. You ONLY help with SIMPLE, BASIC troubleshooting.

DEVICE INFORMATION (from our database):
{device_info}

CRITICAL RULES:

1. VERIFY USER CLAIMS AGAINST DEVICE SPECS:
   - If device specs contradict user's claim, politely point it out
   - Example: If it's a black-only printer and user says "printing red" - say "I see this is a monochrome (black-only) printer, so it cannot print in color. Can you describe what you're seeing differently?"
   - Don't assume user is always right - verify against known device capabilities

2. ONE SOLUTION AT A TIME:
   - Give only ONE troubleshooting step
   - Wait for user to try it and report back
   - Then give next step if needed
   - Never give a list of multiple solutions

3. SIMPLE SOLUTIONS ONLY:
   - Restart device
   - Check cables/connections  
   - Check power
   - Check paper/ink levels (for printers)
   - Clear browser cache
   - Check Wi-Fi connection

4. IMMEDIATELY ESCALATE (Say "This needs our technical team"):
   - Hardware damage or defects
   - Software installation
   - Driver issues
   - Data recovery
   - Error codes
   - Performance issues
   - Crashes/Blue screens
   - Network configuration
   - Anything beyond 2-3 basic steps

RESPONSE STYLE:
- Short responses (2-3 sentences max)
- Ask ONE question or give ONE step
- Be conversational and helpful
- If user's claim seems off, verify it politely

NEVER:
- Give multiple solutions at once
- Give technical/advanced instructions
- Trust user claims that contradict device specs"""


def build_system_prompt(device_context: dict = None) -> str:
    """Build system prompt with device information."""
    if not device_context:
        device_info = "No device selected - general troubleshooting only."
    else:
        # Build detailed device info string
        parts = []
        parts.append(f"Device Type: {device_context.get('device_type', 'Unknown')}")
        parts.append(f"Brand: {device_context.get('brand', 'Unknown')}")
        parts.append(f"Model: {device_context.get('model', 'Unknown')}")
        parts.append(f"Serial Number: {device_context.get('serial_number', 'Unknown')}")
        
        # Add specifications if available
        if device_context.get('specifications'):
            parts.append(f"Specifications: {device_context.get('specifications')}")
        
        # Printer-specific info
        if 'printer' in device_context.get('device_type', '').lower():
            color_type = device_context.get('color_type', 'Unknown')
            parts.append(f"Printer Type: {color_type}")
            if 'mono' in color_type.lower() or 'black' in color_type.lower():
                parts.append("NOTE: This is a BLACK-ONLY printer - cannot print colors!")
        
        # Warranty info
        parts.append(f"Warranty Status: {device_context.get('warranty_status', 'Unknown')}")
        if device_context.get('warranty_end_date'):
            parts.append(f"Warranty Expires: {device_context.get('warranty_end_date')}")
        
        # Service history
        if device_context.get('service_history'):
            parts.append(f"Recent Issues: {device_context.get('service_history')}")
        
        device_info = "\n".join(parts)
    
    return SYSTEM_PROMPT_TEMPLATE.format(device_info=device_info)


async def get_ai_response(
    session_id: str,
    user_message: str,
    message_history: list,
    device_context: Optional[dict] = None
) -> dict:
    """
    Get AI response for support chat.
    
    Args:
        session_id: Unique session identifier
        user_message: Current user message
        message_history: Previous messages in conversation
        device_context: Optional device/warranty info for context
    
    Returns:
        dict with 'response' and 'should_escalate' flag
    """
    if not EMERGENT_LLM_KEY:
        logger.error("EMERGENT_LLM_KEY not configured")
        return {
            "response": "AI support is temporarily unavailable. Please create a ticket directly.",
            "should_escalate": True,
            "error": "AI not configured"
        }
    
    try:
        # Build context-aware system message
        system_message = SYSTEM_PROMPT
        
        if device_context:
            device_info = f"""

DEVICE CONTEXT (User selected this device):
- Device: {device_context.get('device_name', 'N/A')} ({device_context.get('device_type', 'N/A')})
- Serial Number: {device_context.get('serial_number', 'N/A')}
- Model: {device_context.get('model', 'N/A')}
- Warranty Status: {device_context.get('warranty_status', 'Unknown')}
- Warranty Expires: {device_context.get('warranty_end_date', 'N/A')}

Use this information to provide relevant troubleshooting for this specific device."""
            system_message += device_info
        
        # Initialize chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=session_id,
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")
        
        # Add message history to chat context
        for msg in message_history:
            if msg.get("role") == "user":
                await chat.send_message(UserMessage(text=msg["content"]))
            # Assistant messages are automatically tracked
        
        # Send current message
        msg = UserMessage(text=user_message)
        response = await chat.send_message(msg)
        
        # Check if AI suggests escalation - more aggressive detection
        escalation_phrases = [
            "create a support ticket",
            "create a ticket",
            "technical team",
            "escalate",
            "human support",
            "further attention",
            "service technician",
            "requires assistance",
            "experts will help",
            "our team",
            "support team"
        ]
        should_escalate = any(phrase in response.lower() for phrase in escalation_phrases)
        
        return {
            "response": response,
            "should_escalate": should_escalate,
            "error": None
        }
        
    except Exception as e:
        logger.error(f"AI support error: {str(e)}")
        return {
            "response": "I'm having trouble processing your request. Would you like to create a support ticket instead?",
            "should_escalate": True,
            "error": str(e)
        }


def generate_ticket_summary(messages: list) -> dict:
    """
    Generate ticket subject and description from chat history.
    
    Args:
        messages: List of chat messages
    
    Returns:
        dict with 'subject' and 'description'
    """
    if not messages:
        return {"subject": "Support Request", "description": ""}
    
    # Get first user message as base for subject
    first_user_msg = next((m["content"] for m in messages if m["role"] == "user"), "")
    
    # Truncate for subject (max 100 chars)
    subject = first_user_msg[:100]
    if len(first_user_msg) > 100:
        subject = subject.rsplit(' ', 1)[0] + "..."
    
    # Build description from conversation
    description_parts = ["**AI Troubleshooting Attempted:**\n"]
    for msg in messages:
        role = "User" if msg["role"] == "user" else "AI Assistant"
        description_parts.append(f"**{role}:** {msg['content']}\n")
    
    description_parts.append("\n---\n*Issue could not be resolved via AI troubleshooting.*")
    
    return {
        "subject": subject or "Support Request",
        "description": "\n".join(description_parts)
    }
