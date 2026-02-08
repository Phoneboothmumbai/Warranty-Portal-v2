"""
MoltBot Integration Routes
Webhook integration for auto-creating tickets from MoltBot messages
and sending ticket updates back to customers via MoltBot
"""
from fastapi import APIRouter, Depends, HTTPException, Request, Header, BackgroundTasks
from typing import Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel
import uuid
import os
import httpx
import logging

from database import db
from routes.ticketing_config import get_admin_from_token

router = APIRouter(prefix="/moltbot", tags=["moltbot"])
logger = logging.getLogger(__name__)


# =============================================================================
# MODELS
# =============================================================================

class MoltBotConfig(BaseModel):
    """MoltBot configuration for an organization"""
    api_key: str
    webhook_secret: Optional[str] = None
    enabled: bool = True
    auto_create_tickets: bool = True
    default_help_topic_id: Optional[str] = None
    default_priority: str = "medium"
    notification_channels: List[str] = ["webhook"]  # webhook, whatsapp, telegram


class MoltBotWebhookPayload(BaseModel):
    """Incoming webhook payload from MoltBot"""
    event_type: str  # message_received, contact_created, etc.
    message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    sender_name: Optional[str] = None
    sender_phone: Optional[str] = None
    sender_email: Optional[str] = None
    message_content: Optional[str] = None
    channel: Optional[str] = None  # whatsapp, telegram, etc.
    timestamp: Optional[str] = None
    metadata: Optional[dict] = None


class MoltBotMessage(BaseModel):
    """Message to send via MoltBot"""
    recipient_phone: Optional[str] = None
    recipient_email: Optional[str] = None
    channel: str = "whatsapp"
    message: str
    ticket_id: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def send_moltbot_message(org_id: str, message_data: dict):
    """Send message via MoltBot API"""
    config = await db.moltbot_config.find_one({"organization_id": org_id})
    if not config or not config.get("enabled"):
        logger.warning(f"MoltBot not configured or disabled for org {org_id}")
        return False
    
    api_key = config.get("api_key")
    if not api_key:
        logger.warning(f"MoltBot API key not found for org {org_id}")
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.moltbot.com/v1/messages/send",  # Replace with actual MoltBot API endpoint
                headers={"Authorization": f"Bearer {api_key}"},
                json=message_data,
                timeout=30.0
            )
            response.raise_for_status()
            return True
    except Exception as e:
        logger.error(f"Failed to send MoltBot message: {e}")
        return False


# =============================================================================
# CONFIGURATION ENDPOINTS
# =============================================================================

@router.get("/config")
async def get_moltbot_config(admin: dict = Depends(get_admin_from_token)):
    """Get MoltBot configuration for the organization"""
    org_id = admin.get("organization_id")
    
    config = await db.moltbot_config.find_one(
        {"organization_id": org_id},
        {"_id": 0, "api_key": 0}  # Don't expose API key
    )
    
    if not config:
        return {
            "configured": False,
            "enabled": False,
            "auto_create_tickets": False
        }
    
    config["configured"] = True
    config["has_api_key"] = bool(await db.moltbot_config.find_one(
        {"organization_id": org_id, "api_key": {"$exists": True, "$ne": ""}}
    ))
    
    return config


@router.post("/config")
async def save_moltbot_config(
    data: MoltBotConfig,
    admin: dict = Depends(get_admin_from_token)
):
    """Save MoltBot configuration"""
    org_id = admin.get("organization_id")
    
    existing = await db.moltbot_config.find_one({"organization_id": org_id})
    
    config_data = {
        "organization_id": org_id,
        "enabled": data.enabled,
        "auto_create_tickets": data.auto_create_tickets,
        "default_help_topic_id": data.default_help_topic_id,
        "default_priority": data.default_priority,
        "notification_channels": data.notification_channels,
        "updated_at": datetime.now(timezone.utc),
        "updated_by": admin["id"]
    }
    
    # Only update API key if provided
    if data.api_key and data.api_key != "****":
        config_data["api_key"] = data.api_key
    
    if data.webhook_secret:
        config_data["webhook_secret"] = data.webhook_secret
    
    if existing:
        await db.moltbot_config.update_one(
            {"organization_id": org_id},
            {"$set": config_data}
        )
    else:
        config_data["id"] = str(uuid.uuid4())
        config_data["created_at"] = datetime.now(timezone.utc)
        await db.moltbot_config.insert_one(config_data)
    
    return {"message": "MoltBot configuration saved", "enabled": data.enabled}


@router.delete("/config")
async def delete_moltbot_config(admin: dict = Depends(get_admin_from_token)):
    """Delete MoltBot configuration"""
    org_id = admin.get("organization_id")
    
    result = await db.moltbot_config.delete_one({"organization_id": org_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Configuration not found")
    
    return {"message": "MoltBot configuration deleted"}


# =============================================================================
# WEBHOOK ENDPOINTS
# =============================================================================

@router.post("/webhook/{org_id}")
async def moltbot_webhook(
    org_id: str,
    payload: MoltBotWebhookPayload,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    Receive webhook events from MoltBot.
    This endpoint is called by MoltBot when a message is received.
    Smart ticket creation: Ask customer before creating ticket.
    """
    # Get organization config
    config = await db.moltbot_config.find_one({"organization_id": org_id})
    
    if not config:
        raise HTTPException(status_code=404, detail="MoltBot not configured for this organization")
    
    if not config.get("enabled"):
        raise HTTPException(status_code=400, detail="MoltBot integration disabled")
    
    # Verify webhook secret if configured
    webhook_secret = config.get("webhook_secret")
    if webhook_secret:
        provided_secret = request.headers.get("X-MoltBot-Secret")
        if provided_secret != webhook_secret:
            raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    # Log the webhook event
    event_log = {
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "event_type": payload.event_type,
        "payload": payload.dict(),
        "received_at": datetime.now(timezone.utc),
        "processed": False
    }
    await db.moltbot_events.insert_one(event_log)
    
    # Process event based on type
    if payload.event_type == "message_received":
        # Smart ticket flow - check conversation state
        background_tasks.add_task(
            handle_incoming_message,
            org_id,
            payload,
            event_log["id"]
        )
    
    return {"status": "received", "event_id": event_log["id"]}


async def handle_incoming_message(org_id: str, payload: MoltBotWebhookPayload, event_id: str):
    """
    Smart message handling:
    1. Check if there's an ongoing conversation/ticket
    2. If new conversation, ask if they want to create a ticket
    3. Collect details before creating ticket
    4. Only create ticket after confirmation
    """
    try:
        config = await db.moltbot_config.find_one({"organization_id": org_id})
        conversation_id = payload.conversation_id or f"{payload.sender_phone}_{org_id}"
        
        # Check conversation state
        conversation = await db.moltbot_conversations.find_one({
            "conversation_id": conversation_id,
            "organization_id": org_id
        })
        
        message_lower = (payload.message_content or "").lower().strip()
        
        if not conversation:
            # New conversation - greet and ask intent
            conversation = {
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "organization_id": org_id,
                "sender_phone": payload.sender_phone,
                "sender_email": payload.sender_email,
                "sender_name": payload.sender_name,
                "channel": payload.channel,
                "state": "greeting",
                "ticket_data": {},
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc)
            }
            await db.moltbot_conversations.insert_one(conversation)
            
            # Send greeting
            await send_moltbot_message(org_id, {
                "recipient": payload.sender_phone or payload.sender_email,
                "channel": payload.channel,
                "message": f"👋 Hello{' ' + payload.sender_name if payload.sender_name else ''}! Welcome to our support.\n\nHow can I help you today?\n\n1️⃣ Report an issue / Create a support ticket\n2️⃣ Check existing ticket status\n3️⃣ General inquiry\n\nPlease reply with 1, 2, or 3."
            })
            
        elif conversation.get("state") == "greeting":
            # User responded to greeting
            if message_lower in ["1", "one", "issue", "ticket", "problem", "help"]:
                await db.moltbot_conversations.update_one(
                    {"id": conversation["id"]},
                    {"$set": {"state": "collecting_name", "updated_at": datetime.now(timezone.utc)}}
                )
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": "I'll help you create a support ticket. Let me collect some details.\n\n📝 Please provide your **full name**:"
                })
                
            elif message_lower in ["2", "two", "status", "check"]:
                await db.moltbot_conversations.update_one(
                    {"id": conversation["id"]},
                    {"$set": {"state": "checking_status", "updated_at": datetime.now(timezone.utc)}}
                )
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": "📋 Please provide your **ticket number** (e.g., TKT-123456):"
                })
                
            elif message_lower in ["3", "three", "inquiry", "question"]:
                await db.moltbot_conversations.update_one(
                    {"id": conversation["id"]},
                    {"$set": {"state": "general_inquiry", "updated_at": datetime.now(timezone.utc)}}
                )
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": "💬 Please describe your inquiry and our team will get back to you:\n\n(Type your question or message)"
                })
            else:
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": "Please reply with:\n1️⃣ for creating a support ticket\n2️⃣ for checking ticket status\n3️⃣ for general inquiry"
                })
                
        elif conversation.get("state") == "collecting_name":
            # Save name and ask for issue
            await db.moltbot_conversations.update_one(
                {"id": conversation["id"]},
                {"$set": {
                    "state": "collecting_issue",
                    "ticket_data.customer_name": payload.message_content,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            await send_moltbot_message(org_id, {
                "recipient": payload.sender_phone or payload.sender_email,
                "channel": payload.channel,
                "message": f"Thanks, {payload.message_content}! 👍\n\n🔧 Please describe your **issue or problem** in detail:"
            })
            
        elif conversation.get("state") == "collecting_issue":
            # Save issue and ask for confirmation
            ticket_data = conversation.get("ticket_data", {})
            ticket_data["issue_description"] = payload.message_content
            
            await db.moltbot_conversations.update_one(
                {"id": conversation["id"]},
                {"$set": {
                    "state": "confirming_ticket",
                    "ticket_data": ticket_data,
                    "updated_at": datetime.now(timezone.utc)
                }}
            )
            
            await send_moltbot_message(org_id, {
                "recipient": payload.sender_phone or payload.sender_email,
                "channel": payload.channel,
                "message": f"📋 **Ticket Summary**\n\n👤 Name: {ticket_data.get('customer_name')}\n📞 Contact: {payload.sender_phone or payload.sender_email}\n🔧 Issue: {payload.message_content[:200]}{'...' if len(payload.message_content) > 200 else ''}\n\n✅ Should I create this ticket? Reply **YES** to confirm or **NO** to cancel."
            })
            
        elif conversation.get("state") == "confirming_ticket":
            if message_lower in ["yes", "y", "confirm", "ok", "proceed"]:
                # Create the ticket
                ticket_data = conversation.get("ticket_data", {})
                ticket_id = str(uuid.uuid4())
                ticket_number = f"TKT{datetime.now().strftime('%y%m%d')}{str(uuid.uuid4())[:4].upper()}"
                
                ticket = {
                    "id": ticket_id,
                    "ticket_number": ticket_number,
                    "organization_id": org_id,
                    "title": f"Support Request from {ticket_data.get('customer_name', 'Customer')}",
                    "description": ticket_data.get("issue_description", ""),
                    "status": "new",
                    "priority": config.get("default_priority", "medium"),
                    "source": f"moltbot_{payload.channel or 'chat'}",
                    "contact_name": ticket_data.get("customer_name"),
                    "contact_phone": payload.sender_phone,
                    "contact_email": payload.sender_email,
                    "moltbot_conversation_id": conversation_id,
                    "created_at": datetime.now(timezone.utc),
                    "created_via": "moltbot_smart_flow",
                    "is_deleted": False
                }
                
                await db.service_tickets_new.insert_one(ticket)
                
                # Update conversation
                await db.moltbot_conversations.update_one(
                    {"id": conversation["id"]},
                    {"$set": {
                        "state": "ticket_created",
                        "ticket_id": ticket_id,
                        "ticket_number": ticket_number,
                        "updated_at": datetime.now(timezone.utc)
                    }}
                )
                
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": f"✅ **Ticket Created Successfully!**\n\n🎫 Ticket Number: **{ticket_number}**\n\nOur support team will review your request and get back to you shortly.\n\nYou can reply to this chat to add more information to your ticket."
                })
                
                # Mark event as processed
                await db.moltbot_events.update_one(
                    {"id": event_id},
                    {"$set": {
                        "processed": True,
                        "processed_at": datetime.now(timezone.utc),
                        "ticket_id": ticket_id,
                        "ticket_number": ticket_number
                    }}
                )
                
                logger.info(f"Created ticket {ticket_number} via MoltBot smart flow")
                
            elif message_lower in ["no", "n", "cancel", "stop"]:
                # Reset conversation
                await db.moltbot_conversations.update_one(
                    {"id": conversation["id"]},
                    {"$set": {
                        "state": "greeting",
                        "ticket_data": {},
                        "updated_at": datetime.now(timezone.utc)
                    }}
                )
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": "❌ Ticket creation cancelled.\n\nIs there anything else I can help you with?\n\n1️⃣ Report an issue\n2️⃣ Check ticket status\n3️⃣ General inquiry"
                })
            else:
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": "Please reply **YES** to create the ticket or **NO** to cancel."
                })
                
        elif conversation.get("state") == "ticket_created":
            # Add message to existing ticket
            ticket_id = conversation.get("ticket_id")
            if ticket_id:
                # Add as a comment/note to the ticket
                await db.ticket_comments.insert_one({
                    "id": str(uuid.uuid4()),
                    "ticket_id": ticket_id,
                    "organization_id": org_id,
                    "content": payload.message_content,
                    "author_name": conversation.get("sender_name") or "Customer",
                    "author_type": "customer",
                    "source": "moltbot",
                    "created_at": datetime.now(timezone.utc)
                })
                
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": f"📝 Your message has been added to ticket **{conversation.get('ticket_number')}**.\n\nOur team will review it shortly."
                })
                
        elif conversation.get("state") == "checking_status":
            # Look up ticket by number
            ticket = await db.service_tickets_new.find_one({
                "ticket_number": payload.message_content.upper().strip(),
                "organization_id": org_id
            })
            
            if ticket:
                status_emoji = {
                    "new": "🆕",
                    "pending_acceptance": "⏳",
                    "assigned": "👤",
                    "in_progress": "🔧",
                    "pending_parts": "📦",
                    "completed": "✅",
                    "closed": "🔒"
                }.get(ticket.get("status"), "📋")
                
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": f"📋 **Ticket Status**\n\n🎫 Number: {ticket.get('ticket_number')}\n{status_emoji} Status: {ticket.get('status', 'Unknown').replace('_', ' ').title()}\n📅 Created: {ticket.get('created_at', 'N/A')}\n\nNeed more help? Reply with:\n1️⃣ Create new ticket\n3️⃣ General inquiry"
                })
            else:
                await send_moltbot_message(org_id, {
                    "recipient": payload.sender_phone or payload.sender_email,
                    "channel": payload.channel,
                    "message": "❌ Ticket not found. Please check the ticket number and try again.\n\nExample format: TKT240209ABCD"
                })
            
            # Reset to greeting state
            await db.moltbot_conversations.update_one(
                {"id": conversation["id"]},
                {"$set": {"state": "greeting", "updated_at": datetime.now(timezone.utc)}}
            )
            
        elif conversation.get("state") == "general_inquiry":
            # Log inquiry and respond
            await db.moltbot_inquiries.insert_one({
                "id": str(uuid.uuid4()),
                "organization_id": org_id,
                "sender_phone": payload.sender_phone,
                "sender_email": payload.sender_email,
                "sender_name": payload.sender_name,
                "inquiry": payload.message_content,
                "channel": payload.channel,
                "created_at": datetime.now(timezone.utc)
            })
            
            await send_moltbot_message(org_id, {
                "recipient": payload.sender_phone or payload.sender_email,
                "channel": payload.channel,
                "message": "📩 Thank you for your inquiry! Our team will review and respond soon.\n\nWould you like to create a support ticket for tracking? Reply **YES** or continue chatting."
            })
            
            await db.moltbot_conversations.update_one(
                {"id": conversation["id"]},
                {"$set": {"state": "greeting", "updated_at": datetime.now(timezone.utc)}}
            )
        
    except Exception as e:
        logger.error(f"Error handling MoltBot message: {e}")
        await db.moltbot_events.update_one(
            {"id": event_id},
            {"$set": {
                "processed": False,
                "error": str(e),
                "error_at": datetime.now(timezone.utc)
            }}
        )


# =============================================================================
# MESSAGE SENDING ENDPOINTS
# =============================================================================

@router.post("/send-message")
async def send_message(
    data: MoltBotMessage,
    admin: dict = Depends(get_admin_from_token)
):
    """Send a message to a customer via MoltBot"""
    org_id = admin.get("organization_id")
    
    config = await db.moltbot_config.find_one({"organization_id": org_id})
    if not config or not config.get("enabled"):
        raise HTTPException(status_code=400, detail="MoltBot not configured or disabled")
    
    message_data = {
        "channel": data.channel,
        "message": data.message
    }
    
    if data.recipient_phone:
        message_data["recipient"] = data.recipient_phone
    elif data.recipient_email:
        message_data["recipient"] = data.recipient_email
    else:
        raise HTTPException(status_code=400, detail="Recipient phone or email required")
    
    success = await send_moltbot_message(org_id, message_data)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send message via MoltBot")
    
    # Log the sent message
    await db.moltbot_messages.insert_one({
        "id": str(uuid.uuid4()),
        "organization_id": org_id,
        "ticket_id": data.ticket_id,
        "direction": "outbound",
        "recipient": data.recipient_phone or data.recipient_email,
        "channel": data.channel,
        "message": data.message,
        "sent_at": datetime.now(timezone.utc),
        "sent_by": admin["id"]
    })
    
    return {"status": "sent", "message": "Message sent successfully"}


@router.post("/tickets/{ticket_id}/notify-customer")
async def notify_customer_via_moltbot(
    ticket_id: str,
    message: str,
    admin: dict = Depends(get_admin_from_token)
):
    """Send ticket update notification to customer via MoltBot"""
    org_id = admin.get("organization_id")
    
    # Get ticket
    ticket = await db.service_tickets_new.find_one({
        "id": ticket_id,
        "organization_id": org_id
    })
    
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    recipient = ticket.get("contact_phone") or ticket.get("contact_email")
    if not recipient:
        raise HTTPException(status_code=400, detail="No contact information on ticket")
    
    # Get channel from ticket if it was created via MoltBot
    channel = "whatsapp"  # Default
    if ticket.get("source", "").startswith("moltbot_"):
        channel = ticket["source"].replace("moltbot_", "")
    
    success = await send_moltbot_message(org_id, {
        "recipient": recipient,
        "channel": channel,
        "message": message
    })
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send notification")
    
    return {"status": "sent", "recipient": recipient, "channel": channel}


# =============================================================================
# EVENT LOG ENDPOINTS
# =============================================================================

@router.get("/events")
async def list_moltbot_events(
    limit: int = 50,
    processed: Optional[bool] = None,
    admin: dict = Depends(get_admin_from_token)
):
    """List MoltBot webhook events"""
    org_id = admin.get("organization_id")
    
    query = {"organization_id": org_id}
    if processed is not None:
        query["processed"] = processed
    
    events = await db.moltbot_events.find(
        query,
        {"_id": 0}
    ).sort("received_at", -1).limit(limit).to_list(limit)
    
    return {"events": events}


@router.get("/messages")
async def list_moltbot_messages(
    ticket_id: Optional[str] = None,
    limit: int = 50,
    admin: dict = Depends(get_admin_from_token)
):
    """List MoltBot messages sent/received"""
    org_id = admin.get("organization_id")
    
    query = {"organization_id": org_id}
    if ticket_id:
        query["ticket_id"] = ticket_id
    
    messages = await db.moltbot_messages.find(
        query,
        {"_id": 0}
    ).sort("sent_at", -1).limit(limit).to_list(limit)
    
    return {"messages": messages}



@router.get("/conversations")
async def list_moltbot_conversations(
    state: Optional[str] = None,
    limit: int = 50,
    admin: dict = Depends(get_admin_from_token)
):
    """List MoltBot conversations"""
    org_id = admin.get("organization_id")
    
    query = {"organization_id": org_id}
    if state:
        query["state"] = state
    
    conversations = await db.moltbot_conversations.find(
        query,
        {"_id": 0}
    ).sort("updated_at", -1).limit(limit).to_list(limit)
    
    return {"conversations": conversations}
