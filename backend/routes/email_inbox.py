"""
Email Inbox Integration for Ticketing V2
=========================================
IMAP/SMTP email fetching and sending.
Incoming emails create or thread into tickets.
"""
import imaplib
import smtplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from email.utils import parseaddr
import re
import uuid
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Body
from services.auth import get_current_admin

logger = logging.getLogger(__name__)

router = APIRouter()
_db = None
_poll_task = None

def init_db(db):
    global _db
    _db = db

def get_ist_isoformat():
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat()


# ============================================================
# EMAIL INBOX CONFIGURATION
# ============================================================

@router.get("/ticketing/email-inbox")
async def get_email_config(admin: dict = Depends(get_current_admin)):
    """Get email inbox configuration"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")
    config = await _db.ticket_email_config.find_one(
        {"organization_id": org_id},
        {"_id": 0, "imap_password": 0, "smtp_password": 0}
    )
    if not config:
        return {"configured": False}
    config["configured"] = True
    # Mask passwords
    config["imap_password_set"] = True
    config["smtp_password_set"] = True
    return config


@router.post("/ticketing/email-inbox/configure")
async def configure_email(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Configure email inbox (IMAP + SMTP)"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    config = {
        "organization_id": org_id,
        "email_address": data.get("email_address"),
        "display_name": data.get("display_name", ""),
        # IMAP settings
        "imap_host": data.get("imap_host"),
        "imap_port": int(data.get("imap_port", 993)),
        "imap_username": data.get("imap_username") or data.get("email_address"),
        "imap_password": data.get("imap_password"),
        "imap_use_ssl": data.get("imap_use_ssl", True),
        "imap_folder": data.get("imap_folder", "INBOX"),
        # SMTP settings
        "smtp_host": data.get("smtp_host"),
        "smtp_port": int(data.get("smtp_port", 587)),
        "smtp_username": data.get("smtp_username") or data.get("email_address"),
        "smtp_password": data.get("smtp_password"),
        "smtp_use_tls": data.get("smtp_use_tls", True),
        # Polling
        "poll_interval_minutes": int(data.get("poll_interval_minutes", 5)),
        "is_active": data.get("is_active", True),
        "auto_create_tickets": data.get("auto_create_tickets", True),
        "default_help_topic_id": data.get("default_help_topic_id", ""),
        # Metadata
        "updated_at": get_ist_isoformat(),
        "updated_by": admin.get("name"),
    }

    existing = await _db.ticket_email_config.find_one({"organization_id": org_id})
    if existing:
        # Preserve passwords if not provided
        if not config["imap_password"]:
            config["imap_password"] = existing.get("imap_password")
        if not config["smtp_password"]:
            config["smtp_password"] = existing.get("smtp_password")
        config["id"] = existing.get("id", str(uuid.uuid4()))
        await _db.ticket_email_config.update_one(
            {"organization_id": org_id},
            {"$set": config}
        )
    else:
        config["id"] = str(uuid.uuid4())
        config["created_at"] = get_ist_isoformat()
        config["last_sync_at"] = None
        config["last_sync_status"] = None
        config["total_emails_fetched"] = 0
        config["total_tickets_created"] = 0
        await _db.ticket_email_config.insert_one(config)

    return {"message": "Email inbox configured successfully", "id": config["id"]}


@router.post("/ticketing/email-inbox/test")
async def test_email_connection(data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Test IMAP and SMTP connections"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    results = {"imap": {"status": "untested"}, "smtp": {"status": "untested"}}

    # Get stored passwords if not provided
    existing = await _db.ticket_email_config.find_one({"organization_id": org_id})
    imap_password = data.get("imap_password") or (existing.get("imap_password") if existing else None)
    smtp_password = data.get("smtp_password") or (existing.get("smtp_password") if existing else None)

    # Test IMAP
    if data.get("imap_host"):
        try:
            imap_host = data.get("imap_host")
            imap_port = int(data.get("imap_port", 993))
            imap_user = data.get("imap_username") or data.get("email_address")
            use_ssl = data.get("imap_use_ssl", True)

            if use_ssl:
                conn = imaplib.IMAP4_SSL(imap_host, imap_port, timeout=10)
            else:
                conn = imaplib.IMAP4(imap_host, imap_port, timeout=10)

            conn.login(imap_user, imap_password)
            status, folders = conn.list()
            folder = data.get("imap_folder", "INBOX")
            conn.select(folder, readonly=True)
            _, msg_nums = conn.search(None, "ALL")
            total = len(msg_nums[0].split()) if msg_nums[0] else 0
            conn.logout()

            results["imap"] = {"status": "success", "message": f"Connected. {total} emails in {folder}", "email_count": total}
        except Exception as e:
            results["imap"] = {"status": "error", "message": str(e)}

    # Test SMTP
    if data.get("smtp_host"):
        try:
            smtp_host = data.get("smtp_host")
            smtp_port = int(data.get("smtp_port", 587))
            smtp_user = data.get("smtp_username") or data.get("email_address")
            use_tls = data.get("smtp_use_tls", True)

            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=10)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port, timeout=10)
                if use_tls:
                    server.starttls()

            server.login(smtp_user, smtp_password)
            server.quit()
            results["smtp"] = {"status": "success", "message": "Connected and authenticated"}
        except Exception as e:
            results["smtp"] = {"status": "error", "message": str(e)}

    return results


@router.post("/ticketing/email-inbox/sync")
async def trigger_email_sync(admin: dict = Depends(get_current_admin)):
    """Manually trigger email sync"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    config = await _db.ticket_email_config.find_one({"organization_id": org_id})
    if not config:
        raise HTTPException(status_code=400, detail="Email inbox not configured")

    result = await fetch_and_process_emails(config)
    return result


@router.get("/ticketing/email-inbox/logs")
async def get_sync_logs(admin: dict = Depends(get_current_admin)):
    """Get email sync history"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    logs = await _db.ticket_email_sync_log.find(
        {"organization_id": org_id},
        {"_id": 0}
    ).sort("synced_at", -1).limit(20).to_list(20)
    return logs


# ============================================================
# EMAIL PROCESSING ENGINE
# ============================================================

def decode_email_header(header_val):
    """Decode email header value"""
    if not header_val:
        return ""
    decoded_parts = decode_header(header_val)
    result = []
    for part, charset in decoded_parts:
        if isinstance(part, bytes):
            result.append(part.decode(charset or 'utf-8', errors='replace'))
        else:
            result.append(str(part))
    return " ".join(result)


def extract_email_body(msg):
    """Extract plain text body from email"""
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            ct = part.get_content_type()
            cd = str(part.get("Content-Disposition", ""))
            if ct == "text/plain" and "attachment" not in cd:
                payload = part.get_payload(decode=True)
                if payload:
                    charset = part.get_content_charset() or 'utf-8'
                    body = payload.decode(charset, errors='replace')
                    break
        if not body:
            for part in msg.walk():
                if part.get_content_type() == "text/html" and "attachment" not in str(part.get("Content-Disposition", "")):
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or 'utf-8'
                        body = payload.decode(charset, errors='replace')
                        body = re.sub(r'<[^>]+>', '', body)
                        break
    else:
        payload = msg.get_payload(decode=True)
        if payload:
            charset = msg.get_content_charset() or 'utf-8'
            body = payload.decode(charset, errors='replace')
    return body.strip()


def extract_ticket_number_from_subject(subject):
    """Extract ticket number from subject like [Ticket #ABC123]"""
    match = re.search(r'\[Ticket #([A-Z0-9]+)\]', subject)
    return match.group(1) if match else None


async def fetch_and_process_emails(config):
    """Fetch emails via IMAP and create/update tickets"""
    org_id = config["organization_id"]
    results = {"fetched": 0, "new_tickets": 0, "updated_tickets": 0, "errors": []}

    try:
        # Connect to IMAP
        if config.get("imap_use_ssl", True):
            conn = imaplib.IMAP4_SSL(config["imap_host"], config.get("imap_port", 993), timeout=30)
        else:
            conn = imaplib.IMAP4(config["imap_host"], config.get("imap_port", 993), timeout=30)

        conn.login(config.get("imap_username") or config["email_address"], config["imap_password"])
        conn.select(config.get("imap_folder", "INBOX"))

        # Search for unseen emails
        _, msg_nums = conn.search(None, "UNSEEN")
        email_ids = msg_nums[0].split() if msg_nums[0] else []

        for email_id in email_ids[-50:]:  # Process max 50 per sync
            try:
                _, msg_data = conn.fetch(email_id, "(RFC822)")
                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)

                subject = decode_email_header(msg.get("Subject", ""))
                from_name, from_email = parseaddr(msg.get("From", ""))
                from_name = decode_email_header(from_name) or from_email
                message_id = msg.get("Message-ID", "")
                in_reply_to = msg.get("In-Reply-To", "")
                date_str = msg.get("Date", "")
                body = extract_email_body(msg)

                results["fetched"] += 1

                # Check if this is a reply to an existing ticket
                ticket_number = extract_ticket_number_from_subject(subject)
                existing_ticket = None

                if ticket_number:
                    existing_ticket = await _db.tickets_v2.find_one({
                        "ticket_number": ticket_number,
                        "organization_id": org_id,
                        "is_deleted": {"$ne": True}
                    })

                if not existing_ticket and in_reply_to:
                    existing_ticket = await _db.tickets_v2.find_one({
                        "email_message_ids": in_reply_to,
                        "organization_id": org_id,
                        "is_deleted": {"$ne": True}
                    })

                if existing_ticket:
                    # Thread into existing ticket as a comment
                    timeline_entry = {
                        "id": str(uuid.uuid4()),
                        "type": "comment",
                        "description": body[:2000],
                        "user_name": from_name,
                        "user_email": from_email,
                        "is_internal": False,
                        "source": "email",
                        "created_at": get_ist_isoformat()
                    }
                    await _db.tickets_v2.update_one(
                        {"id": existing_ticket["id"]},
                        {
                            "$push": {
                                "timeline": timeline_entry,
                                "email_message_ids": message_id
                            },
                            "$set": {"updated_at": get_ist_isoformat()}
                        }
                    )
                    results["updated_tickets"] += 1

                elif config.get("auto_create_tickets", True):
                    # Create new ticket from email
                    ticket_num = ''.join([chr(65 + (ord(c) % 26)) if i % 2 == 0 else c for i, c in enumerate(str(uuid.uuid4())[:6].upper())])

                    # Find default help topic
                    help_topic = None
                    if config.get("default_help_topic_id"):
                        help_topic = await _db.ticket_help_topics.find_one(
                            {"id": config["default_help_topic_id"]},
                            {"_id": 0}
                        )
                    if not help_topic:
                        help_topic = await _db.ticket_help_topics.find_one(
                            {"organization_id": org_id, "is_active": True},
                            {"_id": 0}
                        )

                    new_ticket = {
                        "id": str(uuid.uuid4()),
                        "organization_id": org_id,
                        "ticket_number": ticket_num,
                        "subject": subject or "Email inquiry",
                        "description": body[:5000],
                        "source": "email",
                        "source_email": from_email,
                        "help_topic_id": help_topic["id"] if help_topic else None,
                        "help_topic_name": help_topic["name"] if help_topic else "General",
                        "contact": {
                            "name": from_name,
                            "email": from_email,
                        },
                        "is_open": True,
                        "form_values": {},
                        "tags": ["email"],
                        "timeline": [{
                            "id": str(uuid.uuid4()),
                            "type": "ticket_created",
                            "description": f"Ticket created from email by {from_name} ({from_email})",
                            "user_name": from_name,
                            "is_internal": False,
                            "created_at": get_ist_isoformat()
                        }],
                        "email_message_ids": [message_id],
                        "task_ids": [],
                        "created_at": get_ist_isoformat(),
                        "updated_at": get_ist_isoformat(),
                        "is_deleted": False,
                    }

                    # Set workflow if help topic has one
                    if help_topic and help_topic.get("workflow_id"):
                        workflow = await _db.ticket_workflows.find_one(
                            {"id": help_topic["workflow_id"]},
                            {"_id": 0}
                        )
                        if workflow:
                            new_ticket["workflow_id"] = workflow["id"]
                            initial_stage = next(
                                (s for s in sorted(workflow.get("stages", []), key=lambda x: x["order"])
                                 if s.get("stage_type") == "initial"),
                                workflow["stages"][0] if workflow.get("stages") else None
                            )
                            if initial_stage:
                                new_ticket["current_stage_id"] = initial_stage["id"]
                                new_ticket["current_stage_name"] = initial_stage["name"]

                    await _db.tickets_v2.insert_one(new_ticket)

                    # Update help topic ticket count
                    if help_topic:
                        await _db.ticket_help_topics.update_one(
                            {"id": help_topic["id"]},
                            {"$inc": {"ticket_count": 1}}
                        )

                    results["new_tickets"] += 1

                # Mark email as seen
                conn.store(email_id, '+FLAGS', '\\Seen')

            except Exception as e:
                results["errors"].append(f"Email processing error: {str(e)[:100]}")
                logger.error(f"Email processing error: {e}")

        conn.logout()

        # Update config with sync status
        await _db.ticket_email_config.update_one(
            {"organization_id": org_id},
            {"$set": {
                "last_sync_at": get_ist_isoformat(),
                "last_sync_status": "success",
                "last_sync_results": results,
            }, "$inc": {
                "total_emails_fetched": results["fetched"],
                "total_tickets_created": results["new_tickets"],
            }}
        )

        # Log sync
        await _db.ticket_email_sync_log.insert_one({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "synced_at": get_ist_isoformat(),
            "status": "success",
            "fetched": results["fetched"],
            "new_tickets": results["new_tickets"],
            "updated_tickets": results["updated_tickets"],
            "errors": results["errors"],
        })

    except Exception as e:
        results["errors"].append(str(e))
        logger.error(f"Email sync error: {e}")

        await _db.ticket_email_config.update_one(
            {"organization_id": org_id},
            {"$set": {
                "last_sync_at": get_ist_isoformat(),
                "last_sync_status": "error",
                "last_sync_error": str(e)[:500],
            }}
        )

        await _db.ticket_email_sync_log.insert_one({
            "id": str(uuid.uuid4()),
            "organization_id": org_id,
            "synced_at": get_ist_isoformat(),
            "status": "error",
            "error": str(e)[:500],
        })

    return results


# ============================================================
# SEND EMAIL REPLY
# ============================================================

@router.post("/ticketing/tickets/{ticket_id}/email-reply")
async def send_email_reply(ticket_id: str, data: dict = Body(...), admin: dict = Depends(get_current_admin)):
    """Send email reply from a ticket"""
    org_id = admin.get("organization_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Organization context required")

    ticket = await _db.tickets_v2.find_one(
        {"id": ticket_id, "organization_id": org_id, "is_deleted": {"$ne": True}}
    )
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    config = await _db.ticket_email_config.find_one({"organization_id": org_id})
    if not config:
        raise HTTPException(status_code=400, detail="Email inbox not configured")

    to_email = data.get("to_email") or ticket.get("source_email") or ticket.get("contact", {}).get("email")
    if not to_email:
        raise HTTPException(status_code=400, detail="No recipient email address")

    body_text = data.get("body", "")
    if not body_text:
        raise HTTPException(status_code=400, detail="Email body required")

    try:
        msg = MIMEMultipart()
        msg["From"] = f"{config.get('display_name', '')} <{config['email_address']}>"
        msg["To"] = to_email
        msg["Subject"] = f"Re: [Ticket #{ticket['ticket_number']}] {ticket.get('subject', '')}"

        # Add reference headers for threading
        if ticket.get("email_message_ids"):
            msg["In-Reply-To"] = ticket["email_message_ids"][-1]
            msg["References"] = " ".join(ticket["email_message_ids"])

        message_id = f"<ticket-{ticket_id}-{uuid.uuid4()}@{config['email_address'].split('@')[1]}>"
        msg["Message-ID"] = message_id

        msg.attach(MIMEText(body_text, "plain"))

        # Send via SMTP
        smtp_port = config.get("smtp_port", 587)
        if smtp_port == 465:
            server = smtplib.SMTP_SSL(config["smtp_host"], smtp_port, timeout=15)
        else:
            server = smtplib.SMTP(config["smtp_host"], smtp_port, timeout=15)
            if config.get("smtp_use_tls", True):
                server.starttls()

        server.login(config.get("smtp_username") or config["email_address"], config["smtp_password"])
        server.send_message(msg)
        server.quit()

        # Add to ticket timeline
        timeline_entry = {
            "id": str(uuid.uuid4()),
            "type": "comment",
            "description": f"Email sent to {to_email}: {body_text[:500]}",
            "user_name": admin.get("name"),
            "is_internal": False,
            "source": "email_sent",
            "created_at": get_ist_isoformat()
        }
        await _db.tickets_v2.update_one(
            {"id": ticket_id},
            {
                "$push": {"timeline": timeline_entry, "email_message_ids": message_id},
                "$set": {"updated_at": get_ist_isoformat()}
            }
        )

        return {"message": "Email sent successfully", "to": to_email}

    except Exception as e:
        logger.error(f"SMTP send error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to send email: {str(e)}")
