"""
Security utilities for the application
- Rate limiting
- Password validation
- Input sanitization
"""
import re
from typing import Tuple
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

# Rate limiter instance - uses IP address for identification
limiter = Limiter(key_func=get_remote_address)

# Rate limit configurations
RATE_LIMITS = {
    "login": "5/minute",          # Max 5 login attempts per minute per IP
    "register": "3/minute",       # Max 3 registrations per minute per IP
    "password_reset": "3/minute", # Max 3 password reset requests per minute
    "api_general": "100/minute",  # General API rate limit
    "api_heavy": "20/minute",     # Heavy operations (exports, bulk)
}


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password meets security requirements:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        return False, "Password must contain at least one special character (!@#$%^&*...)"
    
    return True, "Password meets requirements"


def sanitize_input(value: str, max_length: int = 500) -> str:
    """
    Sanitize user input to prevent injection attacks
    - Strips leading/trailing whitespace
    - Truncates to max length
    - Removes potentially dangerous characters for NoSQL
    """
    if not value:
        return value
    
    # Strip whitespace
    value = value.strip()
    
    # Truncate to max length
    if len(value) > max_length:
        value = value[:max_length]
    
    # Remove MongoDB operator characters at the start (prevents NoSQL injection)
    if value.startswith('$'):
        value = value[1:]
    
    return value


def is_valid_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def get_client_ip(request: Request) -> str:
    """Get client IP address, handling proxies"""
    # Check for forwarded IP (behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    return request.client.host if request.client else "unknown"
