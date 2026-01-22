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

4. WHEN YOU CANNOT HELP - USE THIS EXACT MESSAGE:
   When the issue is complex or beyond basic troubleshooting, say EXACTLY:
   "This needs assistance from our technical team. Please click the 'Create Ticket' button below to connect with our tech support team."

   Use this message for:
   - Hardware damage or defects
   - Software installation
   - Driver issues
   - Data recovery
   - Error codes
   - Performance issues
   - Crashes/Blue screens
   - Network configuration
   - Anything beyond 2-3 basic steps
   - When basic steps don't work

RESPONSE STYLE:
- Short responses (2-3 sentences max)
- Ask ONE question or give ONE step
- Be conversational and helpful
- If user's claim seems off, verify it politely

NEVER:
- Give multiple solutions at once
- Give technical/advanced instructions
- Trust user claims that contradict device specs
- Try to solve complex problems yourself"""


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
        # Build system message with device context
        system_message = build_system_prompt(device_context)
        
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
        
        # Check if AI suggests escalation
        escalation_phrases = [
            "create ticket",
            "click the",
            "button below",
            "technical team",
            "tech support team",
            "support team",
            "needs assistance"
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


async def generate_ticket_summary_ai(messages: list) -> dict:
    """
    Use AI to generate a concise ticket subject and description from chat history.
    
    Args:
        messages: List of chat messages
    
    Returns:
        dict with 'subject' and 'description'
    """
    if not messages:
        return {"subject": "Support Request", "description": ""}
    
    if not EMERGENT_LLM_KEY:
        # Fallback to simple summary
        return generate_ticket_summary_simple(messages)
    
    try:
        import uuid
        import json
        
        # Build conversation text for AI
        conversation = "\n".join([
            f"{'User' if m['role'] == 'user' else 'AI'}: {m['content']}" 
            for m in messages
        ])
        
        summary_prompt = f"""Analyze this IT support conversation and generate a ticket summary.

CONVERSATION:
{conversation}

Generate a JSON response with:
1. "subject": A short, clear ticket subject (max 80 characters) describing the main issue
2. "problem_summary": Brief description of what the user's problem is (2-3 sentences)
3. "troubleshooting_done": What troubleshooting steps were already attempted (bullet points)
4. "current_status": Current state of the issue
5. "suggested_action": What the support team should focus on

Return ONLY valid JSON, no other text."""

        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=str(uuid.uuid4()),
            system_message="You are a technical support analyst. Generate concise ticket summaries from support conversations. Return only valid JSON."
        ).with_model("openai", "gpt-4o-mini").with_params(temperature=0.1)
        
        response = await chat.send_message(UserMessage(text=summary_prompt))
        
        # Clean response if it has markdown
        response_text = response.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        
        summary_data = json.loads(response_text)
        
        # Build formatted description
        description = f"""## Problem Summary
{summary_data.get('problem_summary', 'User reported an issue.')}

## Troubleshooting Already Attempted
{summary_data.get('troubleshooting_done', '- AI troubleshooting was attempted but did not resolve the issue.')}

## Current Status
{summary_data.get('current_status', 'Issue unresolved, requires technical support.')}

## Suggested Next Steps
{summary_data.get('suggested_action', 'Please investigate and assist the user.')}

---
*This ticket was auto-generated from an AI support chat session.*"""
        
        return {
            "subject": summary_data.get("subject", "Support Request")[:100],
            "description": description
        }
        
    except Exception as e:
        logger.error(f"AI summary generation error: {e}")
        # Fallback to simple summary
        return generate_ticket_summary_simple(messages)


def generate_ticket_summary_simple(messages: list) -> dict:
    """
    Generate a simple ticket summary without AI (fallback).
    
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
    
    # Get user issues (all user messages)
    user_issues = [m["content"] for m in messages if m["role"] == "user"]
    
    # Get AI suggestions (last AI message usually has the key info)
    ai_messages = [m["content"] for m in messages if m["role"] == "assistant"]
    last_ai_msg = ai_messages[-1] if ai_messages else ""
    
    # Build concise description
    description = f"""## User's Issue
{chr(10).join(['- ' + issue for issue in user_issues[:3]])}

## AI Troubleshooting Summary
{len(ai_messages)} AI responses were provided during the chat session.

Last AI suggestion: {last_ai_msg[:300]}{'...' if len(last_ai_msg) > 300 else ''}

## Status
Issue could not be resolved via AI troubleshooting and requires technical support.

---
*This ticket was auto-generated from an AI support chat session.*"""
    
    return {
        "subject": subject or "Support Request",
        "description": description
    }


def generate_ticket_summary(messages: list) -> dict:
    """
    Synchronous wrapper - Generate ticket subject and description from chat history.
    For async AI summary, use generate_ticket_summary_ai instead.
    
    Args:
        messages: List of chat messages
    
    Returns:
        dict with 'subject' and 'description'
    """
    # Use simple summary for sync calls
    return generate_ticket_summary_simple(messages)
