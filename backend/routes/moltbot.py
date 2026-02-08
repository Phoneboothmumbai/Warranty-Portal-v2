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
    if payload.event_type == "message_received" and config.get("auto_create_tickets"):
        # Auto-create ticket from message
        background_tasks.add_task(
            create_ticket_from_message,
            org_id,
            payload,
            event_log["id"]
        )
    
    return {"status": "received", "event_id": event_log["id"]}


async def create_ticket_from_message(org_id: str, payload: MoltBotWebhookPayload, event_id: str):
    """Background task to create ticket from MoltBot message"""
    try:
        config = await db.moltbot_config.find_one({"organization_id": org_id})
        
        # Find or create contact
        contact = None
        if payload.sender_phone:
            contact = await db.contacts.find_one({
                "organization_id": org_id,
                "phone": payload.sender_phone
            })
        elif payload.sender_email:
            contact = await db.contacts.find_one({
                "organization_id": org_id,
                "email": payload.sender_email
            })
        
        # Create ticket
        ticket_id = str(uuid.uuid4())
        ticket_number = f"MB{datetime.now().strftime('%y%m%d')}{str(uuid.uuid4())[:4].upper()}"
        
        ticket = {
            "id": ticket_id,
            "ticket_number": ticket_number,
            "organization_id": org_id,
            "title": f"Message from {payload.sender_name or payload.sender_phone or 'Customer'}",
            "description": payload.message_content or "",
            "status": "new",
            "priority": config.get("default_priority", "medium"),
            "source": f"moltbot_{payload.channel or 'message'}",
            "help_topic_id": config.get("default_help_topic_id"),
            "contact_id": contact["id"] if contact else None,
            "contact_name": payload.sender_name or contact.get("name") if contact else None,
            "contact_phone": payload.sender_phone,
            "contact_email": payload.sender_email,
            "moltbot_conversation_id": payload.conversation_id,
            "moltbot_message_id": payload.message_id,
            "created_at": datetime.now(timezone.utc),
            "created_via": "moltbot_webhook",
            "is_deleted": False
        }
        
        await db.service_tickets_new.insert_one(ticket)
        
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
        
        logger.info(f"Created ticket {ticket_number} from MoltBot message")
        
        # Send acknowledgement back to customer
        if payload.sender_phone or payload.sender_email:
            await send_moltbot_message(org_id, {
                "recipient": payload.sender_phone or payload.sender_email,
                "channel": payload.channel,
                "message": f"Thank you for contacting us! Your ticket number is {ticket_number}. We will get back to you shortly."
            })
        
    except Exception as e:
        logger.error(f"Failed to create ticket from MoltBot message: {e}")
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
