"""
osTicket integration service
"""
import logging
from typing import Optional
import httpx

from config import OSTICKET_URL, OSTICKET_API_KEY

logger = logging.getLogger(__name__)


async def create_osticket(
    email: str,
    name: str,
    subject: str,
    message: str,
    phone: str = "",
    priority_id: Optional[int] = None
) -> dict:
    """
    Create a ticket in osTicket system.
    Returns dict with 'ticket_id' on success, or 'error' on failure.
    Note: osTicket API keys are IP-restricted. This will only work from the configured server IP.
    """
    if not OSTICKET_URL or not OSTICKET_API_KEY:
        logger.warning("osTicket not configured - skipping ticket sync")
        return {"error": "osTicket not configured", "ticket_id": None}
    
    try:
        api_url = f"{OSTICKET_URL.rstrip('/')}/api/tickets.json"
        
        logger.info(f"Creating osTicket: URL={api_url}, Email={email}, Subject={subject[:50]}...")
        
        payload = {
            "alert": True,
            "autorespond": True,
            "source": "API",
            "name": name,
            "email": email,
            "subject": subject,
            "message": f"data:text/html,{message}",
        }
        
        if phone:
            payload["phone"] = phone
        
        if priority_id:
            payload["priority"] = priority_id
        
        headers = {
            "X-API-Key": OSTICKET_API_KEY,
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.post(api_url, json=payload, headers=headers)
            
            logger.info(f"osTicket response: status={response.status_code}, body={response.text[:200]}")
            
            if response.status_code == 201:
                osticket_id = response.text.strip()
                logger.info(f"osTicket created successfully: {osticket_id}")
                return {"ticket_id": osticket_id, "error": None}
            elif response.status_code == 401:
                error_msg = f"API key rejected (IP restriction): {response.text}"
                logger.warning(f"osTicket: {error_msg}")
                return {"ticket_id": None, "error": error_msg}
            else:
                error_msg = f"API error {response.status_code}: {response.text}"
                logger.error(f"osTicket: {error_msg}")
                return {"ticket_id": None, "error": error_msg}
                
    except Exception as e:
        error_msg = f"Connection failed: {str(e)}"
        logger.error(f"osTicket integration failed: {error_msg}")
        return {"ticket_id": None, "error": error_msg}
