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


async def fetch_osticket_details(ticket_id: str) -> dict:
    """
    Fetch ticket details from osTicket.
    Returns ticket info including status and thread/replies.
    
    Note: Standard osTicket API has limited read capabilities.
    The /api/tickets/{id} endpoint may not be available depending on osTicket version
    and installed plugins. Consider using osTicket's "Ticket Export" plugin or
    direct database access for full sync capabilities.
    """
    if not OSTICKET_URL or not OSTICKET_API_KEY:
        return {"error": "osTicket not configured", "data": None}
    
    try:
        # Try the standard ticket endpoint first
        # Note: This endpoint may require osTicket REST API plugin
        api_url = f"{OSTICKET_URL.rstrip('/')}/api/tickets/{ticket_id}.json"
        
        headers = {
            "X-API-Key": OSTICKET_API_KEY,
            "Content-Type": "application/json"
        }
        
        logger.info(f"Fetching osTicket details: {api_url}")
        
        async with httpx.AsyncClient(timeout=30.0) as http_client:
            response = await http_client.get(api_url, headers=headers)
            
            logger.info(f"osTicket fetch response: status={response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {"data": data, "error": None}
                except Exception:
                    # osTicket sometimes returns non-JSON
                    return {"data": {"raw": response.text}, "error": None}
            elif response.status_code == 401:
                return {"data": None, "error": "API access denied. Check API key and IP restrictions."}
            elif response.status_code == 404:
                return {"data": None, "error": "Ticket not found in osTicket"}
            elif response.status_code == 400:
                # 400 often means the endpoint doesn't exist or requires a plugin
                return {"data": None, "error": "osTicket API does not support ticket retrieval. Install REST API plugin or check osTicket settings."}
            else:
                return {"data": None, "error": f"osTicket API error ({response.status_code})"}
                
    except Exception as e:
        logger.error(f"osTicket fetch failed: {str(e)}")
        return {"data": None, "error": f"Connection error: {str(e)}"}

