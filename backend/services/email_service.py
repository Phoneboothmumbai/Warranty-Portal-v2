"""
Email Service for Ticketing System
- SMTP: Send notifications to ticket participants
- IMAP: Receive emails and create/sync tickets
"""
import os
import re
import uuid
import smtplib
import imaplib
import email
import asyncio
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import decode_header
from datetime import datetime
from typing import Optional, List, Dict, Any
from motor.motor_asyncio import AsyncIOMotorDatabase

from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)

# Email configuration from environment
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
IMAP_HOST = os.environ.get("IMAP_HOST", "imap.gmail.com")
IMAP_PORT = int(os.environ.get("IMAP_PORT", "993"))
EMAIL_USER = os.environ.get("EMAIL_USER", "")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD", "")  # App Password for Google Workspace
EMAIL_FROM_NAME = os.environ.get("EMAIL_FROM_NAME", "Support Team")
EMAIL_REPLY_TO = os.environ.get("EMAIL_REPLY_TO", "")
SYSTEM_BASE_URL = os.environ.get("SYSTEM_BASE_URL", "https://support.example.com")


class EmailService:
    """Handles email sending (SMTP) and receiving (IMAP) for ticketing"""
    
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db
        self._smtp_connected = False
        self._imap_connected = False
    
    def is_configured(self) -> bool:
        """Check if email credentials are configured"""
        return bool(EMAIL_USER and EMAIL_PASSWORD)
    
    # ==================== SMTP - SENDING EMAILS ====================
    
    def _create_smtp_connection(self):
        """Create SMTP connection with TLS"""
        try:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            return server
        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            return None
    
    def _build_html_email(self, subject: str, body_html: str) -> str:
        """Build HTML email template"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #0F62FE, #0043CE); color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
                .header h1 {{ margin: 0; font-size: 20px; }}
                .content {{ background: #f8fafc; padding: 20px; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px; }}
                .ticket-info {{ background: white; padding: 15px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #0F62FE; }}
                .footer {{ text-align: center; font-size: 12px; color: #64748b; margin-top: 20px; padding-top: 20px; border-top: 1px solid #e2e8f0; }}
                .btn {{ display: inline-block; background: #0F62FE; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; margin-top: 15px; }}
                .btn:hover {{ background: #0043CE; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{subject}</h1>
                </div>
                <div class="content">
                    {body_html}
                </div>
                <div class="footer">
                    <p>This is an automated message from the Support Portal.</p>
                    <p>Please do not reply directly to this email. Use the support portal to respond.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def send_email(self, to_email: str, subject: str, body_html: str, reply_to: Optional[str] = None) -> bool:
        """Send an email via SMTP"""
        if not self.is_configured():
            logger.warning("Email not configured, skipping send")
            return False
        
        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{EMAIL_FROM_NAME} <{EMAIL_USER}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            msg['Reply-To'] = reply_to or EMAIL_REPLY_TO or EMAIL_USER
            
            # Plain text version
            plain_text = re.sub(r'<[^>]+>', '', body_html)
            msg.attach(MIMEText(plain_text, 'plain'))
            
            # HTML version
            html_content = self._build_html_email(subject, body_html)
            msg.attach(MIMEText(html_content, 'html'))
            
            server = self._create_smtp_connection()
            if server:
                server.send_message(msg)
                server.quit()
                logger.info(f"Email sent to {to_email}: {subject}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
    
    async def send_ticket_notification(self, ticket: dict, event_type: str, reply_content: Optional[str] = None):
        """Send notification to all ticket participants"""
        if not self.is_configured():
            return
        
        ticket_number = ticket.get("ticket_number", "")
        subject_base = ticket.get("subject", "Your Ticket")
        requester_email = ticket.get("requester_email", "")
        requester_name = ticket.get("requester_name", "Customer")
        
        # Build recipient list
        recipients = []
        
        # Add requester
        if requester_email:
            recipients.append({"email": requester_email, "name": requester_name, "type": "requester"})
        
        # Add participants
        participants = await self.db.ticket_participants.find(
            {"ticket_id": ticket.get("id"), "is_active": True, "receives_notifications": True},
            {"_id": 0}
        ).to_list(50)
        
        for p in participants:
            if p.get("email") and p.get("email").lower() != requester_email.lower():
                recipients.append({"email": p.get("email"), "name": p.get("name"), "type": "participant"})
        
        if not recipients:
            return
        
        # Build email content based on event type
        portal_url = f"{SYSTEM_BASE_URL}/support"
        
        if event_type == "ticket_created":
            subject = f"[{ticket_number}] Ticket Created: {subject_base}"
            body_html = f"""
                <p>Hello,</p>
                <p>A new support ticket has been created.</p>
                <div class="ticket-info">
                    <p><strong>Ticket Number:</strong> {ticket_number}</p>
                    <p><strong>Subject:</strong> {subject_base}</p>
                    <p><strong>Priority:</strong> {ticket.get('priority', 'medium').capitalize()}</p>
                    <p><strong>Status:</strong> Open</p>
                </div>
                <p><strong>Description:</strong></p>
                <p style="background: white; padding: 15px; border-radius: 6px;">{ticket.get('description', '')}</p>
                <p>You can check the status of your ticket at any time:</p>
                <a href="{portal_url}" class="btn">View Ticket Status</a>
            """
        
        elif event_type == "reply_added":
            subject = f"Re: [{ticket_number}] {subject_base}"
            body_html = f"""
                <p>Hello,</p>
                <p>A new reply has been added to your support ticket.</p>
                <div class="ticket-info">
                    <p><strong>Ticket Number:</strong> {ticket_number}</p>
                    <p><strong>Subject:</strong> {subject_base}</p>
                </div>
                <p><strong>Reply:</strong></p>
                <p style="background: white; padding: 15px; border-radius: 6px;">{reply_content or 'No content'}</p>
                <a href="{portal_url}" class="btn">View Full Conversation</a>
            """
        
        elif event_type == "status_changed":
            subject = f"[{ticket_number}] Status Updated: {subject_base}"
            body_html = f"""
                <p>Hello,</p>
                <p>The status of your support ticket has been updated.</p>
                <div class="ticket-info">
                    <p><strong>Ticket Number:</strong> {ticket_number}</p>
                    <p><strong>Subject:</strong> {subject_base}</p>
                    <p><strong>New Status:</strong> {ticket.get('status', 'open').replace('_', ' ').title()}</p>
                </div>
                <a href="{portal_url}" class="btn">View Ticket</a>
            """
        
        elif event_type == "ticket_closed":
            subject = f"[{ticket_number}] Ticket Closed: {subject_base}"
            body_html = f"""
                <p>Hello,</p>
                <p>Your support ticket has been closed.</p>
                <div class="ticket-info">
                    <p><strong>Ticket Number:</strong> {ticket_number}</p>
                    <p><strong>Subject:</strong> {subject_base}</p>
                    <p><strong>Status:</strong> Closed</p>
                </div>
                <p>If you need further assistance, please create a new ticket.</p>
                <a href="{portal_url}" class="btn">Create New Ticket</a>
            """
        
        else:
            return
        
        # Send to all recipients
        for recipient in recipients:
            await self.send_email(recipient["email"], subject, body_html)
    
    # ==================== IMAP - RECEIVING EMAILS ====================
    
    def _create_imap_connection(self):
        """Create IMAP connection with SSL"""
        try:
            mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
            mail.login(EMAIL_USER, EMAIL_PASSWORD)
            return mail
        except Exception as e:
            logger.error(f"IMAP connection failed: {e}")
            return None
    
    def _decode_email_header(self, header_value: str) -> str:
        """Decode email header to string"""
        if not header_value:
            return ""
        decoded_parts = decode_header(header_value)
        result = []
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(encoding or 'utf-8', errors='replace'))
            else:
                result.append(part)
        return ' '.join(result)
    
    def _extract_email_body(self, msg) -> tuple:
        """Extract plain text and HTML body from email"""
        plain_body = ""
        html_body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                
                if "attachment" in content_disposition:
                    continue
                
                try:
                    body = part.get_payload(decode=True)
                    if body:
                        charset = part.get_content_charset() or 'utf-8'
                        body = body.decode(charset, errors='replace')
                        
                        if content_type == "text/plain":
                            plain_body = body
                        elif content_type == "text/html":
                            html_body = body
                except Exception as e:
                    logger.error(f"Error extracting email body: {e}")
        else:
            try:
                body = msg.get_payload(decode=True)
                if body:
                    charset = msg.get_content_charset() or 'utf-8'
                    body = body.decode(charset, errors='replace')
                    if msg.get_content_type() == "text/html":
                        html_body = body
                    else:
                        plain_body = body
            except Exception as e:
                logger.error(f"Error extracting email body: {e}")
        
        return plain_body, html_body
    
    def _extract_ticket_number_from_subject(self, subject: str) -> Optional[str]:
        """Extract ticket number from email subject (e.g., [TKT-ABC123] or [TKT-20250128-ABC123])"""
        # Support both new short format (TKT-XXXXXX) and old long format (TKT-YYYYMMDD-XXXXXX)
        match = re.search(r'\[?(TKT-(?:\d{8}-)?[A-Z0-9]{6})\]?', subject, re.IGNORECASE)
        return match.group(1).upper() if match else None
    
    def _clean_reply_content(self, body: str, ticket_number: Optional[str] = None) -> str:
        """Clean reply content - remove quoted text and signatures"""
        lines = body.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Stop at common reply markers
            if any(marker in line.lower() for marker in [
                'on ', 'wrote:', 'from:', '-----original message', 
                '________________________________', '> ', 'sent from'
            ]):
                break
            cleaned_lines.append(line)
        
        cleaned = '\n'.join(cleaned_lines).strip()
        
        # Remove ticket number references if present
        if ticket_number:
            cleaned = re.sub(rf'\[?{re.escape(ticket_number)}\]?\s*', '', cleaned, flags=re.IGNORECASE)
        
        return cleaned
    
    async def fetch_new_emails(self, folder: str = "INBOX", mark_read: bool = True) -> List[dict]:
        """Fetch unread emails from IMAP inbox"""
        if not self.is_configured():
            return []
        
        emails = []
        mail = self._create_imap_connection()
        if not mail:
            return []
        
        try:
            mail.select(folder)
            _, message_numbers = mail.search(None, 'UNSEEN')
            
            for num in message_numbers[0].split():
                try:
                    _, msg_data = mail.fetch(num, '(RFC822)')
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract email details
                    from_header = self._decode_email_header(msg.get('From', ''))
                    to_header = self._decode_email_header(msg.get('To', ''))
                    subject = self._decode_email_header(msg.get('Subject', ''))
                    message_id = msg.get('Message-ID', '')
                    in_reply_to = msg.get('In-Reply-To', '')
                    references = msg.get('References', '')
                    date_header = msg.get('Date', '')
                    
                    # Parse From address
                    from_match = re.search(r'<?([^<>@]+@[^<>]+)>?', from_header)
                    from_email = from_match.group(1) if from_match else from_header
                    from_name = re.sub(r'<[^>]+>', '', from_header).strip() or from_email.split('@')[0]
                    
                    # Extract body
                    plain_body, html_body = self._extract_email_body(msg)
                    body = plain_body or html_body
                    
                    # Try to extract ticket number
                    ticket_number = self._extract_ticket_number_from_subject(subject)
                    
                    emails.append({
                        "message_id": message_id,
                        "from_email": from_email,
                        "from_name": from_name.replace('"', ''),
                        "to": to_header,
                        "subject": subject,
                        "body": body,
                        "body_html": html_body,
                        "in_reply_to": in_reply_to,
                        "references": references,
                        "date": date_header,
                        "ticket_number": ticket_number,
                        "imap_num": num
                    })
                    
                    if mark_read:
                        mail.store(num, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    logger.error(f"Error processing email {num}: {e}")
            
            mail.logout()
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
        
        return emails
    
    async def process_incoming_email(self, email_data: dict) -> Optional[str]:
        """Process an incoming email - either add to existing ticket or create new one"""
        ticket_number = email_data.get("ticket_number")
        from_email = email_data.get("from_email", "").lower()
        from_name = email_data.get("from_name", "")
        subject = email_data.get("subject", "")
        body = email_data.get("body", "")
        
        if ticket_number:
            # This is a reply to an existing ticket
            ticket = await self.db.tickets.find_one(
                {"ticket_number": ticket_number, "is_deleted": {"$ne": True}},
                {"_id": 0}
            )
            
            if ticket:
                # Verify sender is requester or participant
                is_authorized = False
                if ticket.get("requester_email", "").lower() == from_email:
                    is_authorized = True
                else:
                    participant = await self.db.ticket_participants.find_one(
                        {"ticket_id": ticket.get("id"), "email": {"$regex": f"^{re.escape(from_email)}$", "$options": "i"}, "is_active": True},
                        {"_id": 0}
                    )
                    if participant:
                        is_authorized = True
                
                if is_authorized:
                    # Clean the reply content
                    cleaned_body = self._clean_reply_content(body, ticket_number)
                    
                    if cleaned_body:
                        # Add reply to ticket thread
                        entry_id = str(uuid.uuid4())
                        entry = {
                            "id": entry_id,
                            "ticket_id": ticket.get("id"),
                            "entry_type": "customer_message",
                            "author_id": "email",
                            "author_name": from_name,
                            "author_type": "customer",
                            "author_email": from_email,
                            "content": cleaned_body,
                            "content_html": None,
                            "is_internal": False,
                            "is_hidden": False,
                            "created_at": get_ist_isoformat(),
                            "updated_at": get_ist_isoformat(),
                            "source": "email",
                            "email_message_id": email_data.get("message_id")
                        }
                        
                        await self.db.ticket_thread.insert_one(entry)
                        
                        # Update ticket
                        update_data = {
                            "updated_at": get_ist_isoformat(),
                            "last_customer_reply_at": get_ist_isoformat(),
                            "reply_count": ticket.get("reply_count", 0) + 1
                        }
                        
                        # If waiting on customer, reopen
                        if ticket.get("status") == "waiting_on_customer":
                            update_data["status"] = "open"
                        
                        await self.db.tickets.update_one({"id": ticket.get("id")}, {"$set": update_data})
                        
                        logger.info(f"Added email reply to ticket {ticket_number}")
                        return ticket_number
                else:
                    logger.warning(f"Unauthorized email reply attempt from {from_email} to ticket {ticket_number}")
        else:
            # This is a new ticket
            # Check if this sender has recent tickets with similar subject (to prevent duplicates)
            existing = await self.db.tickets.find_one(
                {
                    "requester_email": {"$regex": f"^{re.escape(from_email)}$", "$options": "i"},
                    "source": "email",
                    "is_deleted": {"$ne": True}
                },
                {"_id": 0},
                sort=[("created_at", -1)]
            )
            
            # Create new ticket
            ticket_id = str(uuid.uuid4())
            new_ticket_number = f"TKT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:6].upper()}"
            
            # Clean subject (remove Re:, Fwd:, etc.)
            clean_subject = re.sub(r'^(re:|fw:|fwd:)\s*', '', subject, flags=re.IGNORECASE).strip()
            if not clean_subject:
                clean_subject = "Email Support Request"
            
            ticket = {
                "id": ticket_id,
                "ticket_number": new_ticket_number,
                "company_id": "EMAIL",
                "source": "email",
                "help_topic_id": None,
                "department_id": None,
                "subject": clean_subject,
                "description": body,
                "status": "open",
                "priority": "medium",
                "priority_order": 2,
                "requester_id": "email",
                "requester_name": from_name,
                "requester_email": from_email,
                "requester_phone": None,
                "participant_ids": [],
                "participant_count": 0,
                "assigned_to": None,
                "assigned_to_name": None,
                "assigned_at": None,
                "watchers": [],
                "sla_status": None,
                "tags": ["email"],
                "category": None,
                "form_data": None,
                "custom_fields": {},
                "device_id": None,
                "service_id": None,
                "attachments": [],
                "reply_count": 0,
                "internal_note_count": 0,
                "created_at": get_ist_isoformat(),
                "updated_at": get_ist_isoformat(),
                "first_response_at": None,
                "resolved_at": None,
                "closed_at": None,
                "last_customer_reply_at": None,
                "last_staff_reply_at": None,
                "created_by": "email",
                "created_by_type": "customer",
                "is_deleted": False,
                "email_message_id": email_data.get("message_id")
            }
            
            await self.db.tickets.insert_one(ticket)
            
            # Create initial thread entry
            entry = {
                "id": str(uuid.uuid4()),
                "ticket_id": ticket_id,
                "entry_type": "system_event",
                "author_id": "email",
                "author_name": from_name,
                "author_type": "customer",
                "author_email": from_email,
                "content": None,
                "event_type": "ticket_created",
                "event_data": {"source": "email"},
                "is_internal": False,
                "is_hidden": False,
                "created_at": get_ist_isoformat(),
                "updated_at": get_ist_isoformat(),
                "source": "email"
            }
            await self.db.ticket_thread.insert_one(entry)
            
            logger.info(f"Created new ticket from email: {new_ticket_number}")
            
            # Send confirmation email
            await self.send_ticket_notification(ticket, "ticket_created")
            
            return new_ticket_number
        
        return None
    
    async def sync_emails(self):
        """Main sync function - fetch and process all new emails"""
        if not self.is_configured():
            logger.info("Email not configured, skipping sync")
            return {"processed": 0, "created": 0, "replied": 0}
        
        emails = await self.fetch_new_emails()
        
        stats = {"processed": 0, "created": 0, "replied": 0}
        
        for email_data in emails:
            try:
                result = await self.process_incoming_email(email_data)
                stats["processed"] += 1
                if result:
                    if email_data.get("ticket_number"):
                        stats["replied"] += 1
                    else:
                        stats["created"] += 1
            except Exception as e:
                logger.error(f"Error processing email: {e}")
        
        logger.info(f"Email sync complete: {stats}")
        return stats


# Global instance
_email_service: Optional[EmailService] = None


def init_email_service(db: AsyncIOMotorDatabase):
    """Initialize the email service"""
    global _email_service
    _email_service = EmailService(db)
    return _email_service


def get_email_service() -> Optional[EmailService]:
    """Get the email service instance"""
    return _email_service
