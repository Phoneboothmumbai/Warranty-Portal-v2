"""
osTicket webhook endpoints
"""
import os
import uuid
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
import logging

from database import db
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Webhooks"])

OSTICKET_WEBHOOK_SECRET = os.environ.get('OSTICKET_WEBHOOK_SECRET', 'change-this-secret-key')


class OsTicketWebhookPayload(BaseModel):
    """Payload from osTicket webhook"""
    ticket_id: str
    ticket_number: Optional[str] = None
    status: Optional[str] = None
    status_id: Optional[int] = None
    priority: Optional[str] = None
    subject: Optional[str] = None
    last_message: Optional[str] = None
    last_responder: Optional[str] = None
    updated_at: Optional[str] = None
    event_type: Optional[str] = None


@router.post("/webhooks/osticket")
async def osticket_webhook(
    payload: OsTicketWebhookPayload,
    secret: str = Query(..., description="Webhook secret for authentication")
):
    """Webhook endpoint for osTicket to sync ticket updates back to the portal."""
    if secret != OSTICKET_WEBHOOK_SECRET:
        logger.warning(f"osTicket webhook: Invalid secret received")
        raise HTTPException(status_code=401, detail="Invalid webhook secret")
    
    logger.info(f"osTicket webhook received: ticket_id={payload.ticket_id}, event={payload.event_type}, status={payload.status}")
    
    ticket = await db.service_tickets.find_one(
        {"osticket_id": payload.ticket_id},
        {"_id": 0}
    )
    
    quick_request = None
    if not ticket:
        quick_request = await db.quick_service_requests.find_one(
            {"osticket_id": payload.ticket_id},
            {"_id": 0}
        )
    
    if not ticket and not quick_request:
        if payload.ticket_number:
            ticket = await db.service_tickets.find_one(
                {"ticket_number": {"$regex": payload.ticket_number, "$options": "i"}},
                {"_id": 0}
            )
        
        if not ticket:
            logger.warning(f"osTicket webhook: Ticket not found for osticket_id={payload.ticket_id}")
            return {"success": False, "message": "Ticket not found in portal"}
    
    status_mapping = {
        "open": "open",
        "new": "open",
        "in progress": "in_progress",
        "in-progress": "in_progress",
        "pending": "pending",
        "on hold": "on_hold",
        "resolved": "resolved",
        "closed": "closed",
        "answered": "in_progress",
        "overdue": "overdue"
    }
    
    new_status = status_mapping.get(payload.status.lower() if payload.status else "", None)
    
    update_data = {
        "updated_at": get_ist_isoformat()
    }
    
    if new_status:
        update_data["status"] = new_status
        
        if new_status == "resolved":
            update_data["resolved_at"] = get_ist_isoformat()
        elif new_status == "closed":
            update_data["closed_at"] = get_ist_isoformat()
    
    if payload.last_message and payload.last_responder:
        comment = {
            "id": str(uuid.uuid4()),
            "text": payload.last_message,
            "author": payload.last_responder,
            "author_type": "osticket_staff",
            "created_at": get_ist_isoformat(),
            "source": "osticket_webhook"
        }
        
        if ticket:
            await db.service_tickets.update_one(
                {"id": ticket["id"]},
                {
                    "$set": update_data,
                    "$push": {"comments": comment}
                }
            )
        elif quick_request:
            await db.quick_service_requests.update_one(
                {"id": quick_request["id"]},
                {"$set": {**update_data, "last_response": payload.last_message}}
            )
    else:
        if ticket:
            await db.service_tickets.update_one(
                {"id": ticket["id"]},
                {"$set": update_data}
            )
        elif quick_request:
            await db.quick_service_requests.update_one(
                {"id": quick_request["id"]},
                {"$set": update_data}
            )
    
    target = ticket or quick_request
    logger.info(f"osTicket webhook: Updated ticket {target.get('ticket_number', target.get('id'))} with status={new_status}")
    
    return {
        "success": True,
        "message": "Ticket updated successfully",
        "portal_ticket_id": target.get("id"),
        "new_status": new_status
    }


@router.get("/webhooks/osticket/test")
async def test_osticket_webhook():
    """Test endpoint to verify webhook is accessible"""
    return {
        "status": "ok",
        "message": "osTicket webhook endpoint is active",
        "webhook_url": "/api/webhooks/osticket?secret=YOUR_SECRET"
    }
