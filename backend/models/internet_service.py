"""
Internet Service / ISP Connection models
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from utils.helpers import get_ist_isoformat


class InternetService(BaseModel):
    """Internet/ISP connection details for a company or site"""
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    site_id: Optional[str] = None  # Optional: Link to specific site
    
    # Provider Details
    provider_name: str  # ISP name (Airtel, Jio, ACT, etc.)
    connection_type: str = "broadband"  # broadband, leased_line, fiber, 4g, 5g
    account_number: Optional[str] = None
    customer_id: Optional[str] = None
    
    # Plan Details
    plan_name: Optional[str] = None
    speed_download: Optional[str] = None  # e.g., "100 Mbps"
    speed_upload: Optional[str] = None  # e.g., "100 Mbps"
    data_limit: Optional[str] = None  # e.g., "Unlimited", "500 GB"
    monthly_cost: Optional[float] = None
    
    # Contract Details
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    billing_cycle: str = "monthly"  # monthly, quarterly, yearly
    
    # IP Details
    ip_type: str = "dynamic"  # dynamic, static
    static_ip: Optional[str] = None  # If static IP
    gateway: Optional[str] = None
    dns_primary: Optional[str] = None
    dns_secondary: Optional[str] = None
    
    # Router/Modem Credentials
    router_ip: Optional[str] = None  # Usually 192.168.1.1
    router_username: Optional[str] = None
    router_password: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    
    # PPPoE Credentials (if applicable)
    pppoe_username: Optional[str] = None
    pppoe_password: Optional[str] = None
    
    # Support Contact
    support_phone: Optional[str] = None
    support_email: Optional[str] = None
    account_manager: Optional[str] = None
    account_manager_phone: Optional[str] = None
    
    # Status
    status: str = "active"  # active, suspended, terminated
    notes: Optional[str] = None
    
    is_deleted: bool = False
    created_at: str = Field(default_factory=get_ist_isoformat)


class InternetServiceCreate(BaseModel):
    company_id: str
    site_id: Optional[str] = None
    provider_name: str
    connection_type: str = "broadband"
    account_number: Optional[str] = None
    customer_id: Optional[str] = None
    plan_name: Optional[str] = None
    speed_download: Optional[str] = None
    speed_upload: Optional[str] = None
    data_limit: Optional[str] = None
    monthly_cost: Optional[float] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    billing_cycle: str = "monthly"
    ip_type: str = "dynamic"
    static_ip: Optional[str] = None
    gateway: Optional[str] = None
    dns_primary: Optional[str] = None
    dns_secondary: Optional[str] = None
    router_ip: Optional[str] = None
    router_username: Optional[str] = None
    router_password: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    pppoe_username: Optional[str] = None
    pppoe_password: Optional[str] = None
    support_phone: Optional[str] = None
    support_email: Optional[str] = None
    account_manager: Optional[str] = None
    account_manager_phone: Optional[str] = None
    status: str = "active"
    notes: Optional[str] = None


class InternetServiceUpdate(BaseModel):
    company_id: Optional[str] = None
    site_id: Optional[str] = None
    provider_name: Optional[str] = None
    connection_type: Optional[str] = None
    account_number: Optional[str] = None
    customer_id: Optional[str] = None
    plan_name: Optional[str] = None
    speed_download: Optional[str] = None
    speed_upload: Optional[str] = None
    data_limit: Optional[str] = None
    monthly_cost: Optional[float] = None
    contract_start_date: Optional[str] = None
    contract_end_date: Optional[str] = None
    billing_cycle: Optional[str] = None
    ip_type: Optional[str] = None
    static_ip: Optional[str] = None
    gateway: Optional[str] = None
    dns_primary: Optional[str] = None
    dns_secondary: Optional[str] = None
    router_ip: Optional[str] = None
    router_username: Optional[str] = None
    router_password: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_password: Optional[str] = None
    pppoe_username: Optional[str] = None
    pppoe_password: Optional[str] = None
    support_phone: Optional[str] = None
    support_email: Optional[str] = None
    account_manager: Optional[str] = None
    account_manager_phone: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
