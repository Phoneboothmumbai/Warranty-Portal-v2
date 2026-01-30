"""
Billing Routes - Razorpay Subscription Integration
===================================================
Handles subscription payments, upgrades, and billing management.
"""
import os
import hmac
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import Optional

from services.tenant import get_org_from_token, get_current_organization
from models.organization import SUBSCRIPTION_PLANS
from utils.helpers import get_ist_isoformat

logger = logging.getLogger(__name__)
router = APIRouter()

# Razorpay configuration
RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

# Plan ID mapping (create these in Razorpay Dashboard)
RAZORPAY_PLAN_IDS = {
    "starter_monthly": os.environ.get("RAZORPAY_PLAN_STARTER_MONTHLY", ""),
    "starter_yearly": os.environ.get("RAZORPAY_PLAN_STARTER_YEARLY", ""),
    "professional_monthly": os.environ.get("RAZORPAY_PLAN_PRO_MONTHLY", ""),
    "professional_yearly": os.environ.get("RAZORPAY_PLAN_PRO_YEARLY", ""),
}

_db = None
_razorpay_client = None

def init_db(database):
    global _db, _razorpay_client
    _db = database
    
    # Initialize Razorpay client if keys are available
    if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
        try:
            import razorpay
            _razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))
            logger.info("Razorpay client initialized")
        except ImportError:
            logger.warning("Razorpay package not installed. Run: pip install razorpay")
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay: {e}")


class CreateSubscriptionRequest(BaseModel):
    plan: str  # starter, professional
    billing_cycle: str = "monthly"  # monthly, yearly


class VerifyPaymentRequest(BaseModel):
    razorpay_payment_id: str
    razorpay_subscription_id: str
    razorpay_signature: str


class CreateOrderRequest(BaseModel):
    plan: str
    billing_cycle: str = "monthly"


# ==================== SUBSCRIPTION ENDPOINTS ====================

@router.post("/create-subscription")
async def create_subscription(
    request: CreateSubscriptionRequest,
    auth_info: dict = Depends(get_org_from_token)
):
    """Create a Razorpay subscription for the organization"""
    
    if not _razorpay_client:
        raise HTTPException(
            status_code=503,
            detail="Payment service not configured. Please contact support."
        )
    
    org = auth_info.get("organization", {})
    
    # Validate plan
    if request.plan not in ["starter", "professional"]:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    # Get Razorpay plan ID
    plan_key = f"{request.plan}_{request.billing_cycle}"
    razorpay_plan_id = RAZORPAY_PLAN_IDS.get(plan_key)
    
    if not razorpay_plan_id:
        # If plan IDs not configured, create a one-time order instead
        return await create_order_fallback(request, org)
    
    try:
        # Create subscription in Razorpay
        subscription = _razorpay_client.subscription.create({
            "plan_id": razorpay_plan_id,
            "total_count": 12 if request.billing_cycle == "monthly" else 1,
            "customer_notify": 1,
            "notes": {
                "organization_id": org["id"],
                "organization_name": org["name"],
                "plan": request.plan
            }
        })
        
        # Store subscription info
        await _db.billing_subscriptions.insert_one({
            "organization_id": org["id"],
            "razorpay_subscription_id": subscription["id"],
            "plan": request.plan,
            "billing_cycle": request.billing_cycle,
            "status": "created",
            "created_at": get_ist_isoformat()
        })
        
        return {
            "subscription_id": subscription["id"],
            "razorpay_key": RAZORPAY_KEY_ID,
            "plan": request.plan,
            "amount": SUBSCRIPTION_PLANS[request.plan][f"price_{request.billing_cycle}"]
        }
        
    except Exception as e:
        logger.error(f"Razorpay subscription creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create subscription")


async def create_order_fallback(request: CreateSubscriptionRequest, org: dict):
    """Fallback: Create a one-time order if subscription plans not configured"""
    
    plan_config = SUBSCRIPTION_PLANS.get(request.plan)
    if not plan_config:
        raise HTTPException(status_code=400, detail="Invalid plan")
    
    price_key = f"price_{request.billing_cycle}"
    amount = plan_config.get(price_key, plan_config.get("price_monthly", 0))
    
    if not amount:
        raise HTTPException(status_code=400, detail="Price not available for this plan")
    
    try:
        # Create order in Razorpay
        order = _razorpay_client.order.create({
            "amount": amount * 100,  # Convert to paise
            "currency": "INR",
            "receipt": f"org_{org['id']}_{request.plan}",
            "notes": {
                "organization_id": org["id"],
                "plan": request.plan,
                "billing_cycle": request.billing_cycle
            }
        })
        
        # Store order info
        await _db.billing_orders.insert_one({
            "organization_id": org["id"],
            "razorpay_order_id": order["id"],
            "plan": request.plan,
            "billing_cycle": request.billing_cycle,
            "amount": amount,
            "status": "created",
            "created_at": get_ist_isoformat()
        })
        
        return {
            "order_id": order["id"],
            "razorpay_key": RAZORPAY_KEY_ID,
            "plan": request.plan,
            "amount": amount,
            "currency": "INR"
        }
        
    except Exception as e:
        logger.error(f"Razorpay order creation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to create payment order")


@router.post("/verify-payment")
async def verify_payment(
    request: VerifyPaymentRequest,
    auth_info: dict = Depends(get_org_from_token)
):
    """Verify Razorpay payment signature and activate subscription"""
    
    org = auth_info.get("organization", {})
    
    # Verify signature
    try:
        message = f"{request.razorpay_subscription_id}|{request.razorpay_payment_id}"
        generated_signature = hmac.new(
            RAZORPAY_KEY_SECRET.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if generated_signature != request.razorpay_signature:
            raise HTTPException(status_code=400, detail="Invalid payment signature")
            
    except Exception as e:
        logger.error(f"Signature verification failed: {e}")
        raise HTTPException(status_code=400, detail="Payment verification failed")
    
    # Get subscription details
    subscription_doc = await _db.billing_subscriptions.find_one({
        "organization_id": org["id"],
        "razorpay_subscription_id": request.razorpay_subscription_id
    })
    
    if not subscription_doc:
        # Check for order-based payment
        order_doc = await _db.billing_orders.find_one({
            "organization_id": org["id"]
        }, sort=[("created_at", -1)])
        
        if order_doc:
            plan = order_doc.get("plan", "starter")
            billing_cycle = order_doc.get("billing_cycle", "monthly")
        else:
            plan = "starter"
            billing_cycle = "monthly"
    else:
        plan = subscription_doc.get("plan", "starter")
        billing_cycle = subscription_doc.get("billing_cycle", "monthly")
    
    # Calculate period end
    if billing_cycle == "yearly":
        period_end = datetime.now(timezone.utc) + timedelta(days=365)
    else:
        period_end = datetime.now(timezone.utc) + timedelta(days=30)
    
    # Update organization subscription
    await _db.organizations.update_one(
        {"id": org["id"]},
        {"$set": {
            "status": "active",
            "subscription.plan": plan,
            "subscription.status": "active",
            "subscription.billing_cycle": billing_cycle,
            "subscription.current_period_start": get_ist_isoformat(),
            "subscription.current_period_end": period_end.isoformat(),
            "subscription.razorpay_subscription_id": request.razorpay_subscription_id,
            "subscription.last_payment_id": request.razorpay_payment_id,
            "subscription.plan_changed_at": get_ist_isoformat(),
            "updated_at": get_ist_isoformat()
        }}
    )
    
    # Update subscription record
    if subscription_doc:
        await _db.billing_subscriptions.update_one(
            {"razorpay_subscription_id": request.razorpay_subscription_id},
            {"$set": {
                "status": "active",
                "razorpay_payment_id": request.razorpay_payment_id,
                "activated_at": get_ist_isoformat()
            }}
        )
    
    # Record payment
    await _db.billing_payments.insert_one({
        "organization_id": org["id"],
        "razorpay_payment_id": request.razorpay_payment_id,
        "razorpay_subscription_id": request.razorpay_subscription_id,
        "plan": plan,
        "amount": SUBSCRIPTION_PLANS[plan].get(f"price_{billing_cycle}", 0),
        "currency": "INR",
        "status": "captured",
        "created_at": get_ist_isoformat()
    })
    
    return {
        "message": "Payment verified successfully",
        "plan": plan,
        "status": "active",
        "period_end": period_end.isoformat()
    }


@router.post("/webhook")
async def handle_webhook(request: Request):
    """Handle Razorpay webhook events"""
    
    payload = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    
    # Verify webhook signature
    if RAZORPAY_WEBHOOK_SECRET:
        try:
            generated_signature = hmac.new(
                RAZORPAY_WEBHOOK_SECRET.encode(),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            if generated_signature != signature:
                raise HTTPException(status_code=400, detail="Invalid webhook signature")
        except Exception as e:
            logger.error(f"Webhook verification failed: {e}")
            raise HTTPException(status_code=400, detail="Webhook verification failed")
    
    # Parse payload
    import json
    data = json.loads(payload)
    event = data.get("event")
    
    logger.info(f"Received Razorpay webhook: {event}")
    
    # Handle different events
    if event == "subscription.activated":
        await handle_subscription_activated(data)
    elif event == "subscription.charged":
        await handle_subscription_charged(data)
    elif event == "subscription.cancelled":
        await handle_subscription_cancelled(data)
    elif event == "subscription.halted":
        await handle_subscription_halted(data)
    elif event == "payment.captured":
        await handle_payment_captured(data)
    elif event == "payment.failed":
        await handle_payment_failed(data)
    
    return {"status": "processed"}


async def handle_subscription_activated(data):
    """Handle subscription activation"""
    subscription = data.get("payload", {}).get("subscription", {}).get("entity", {})
    org_id = subscription.get("notes", {}).get("organization_id")
    
    if org_id:
        await _db.organizations.update_one(
            {"id": org_id},
            {"$set": {
                "status": "active",
                "subscription.status": "active",
                "updated_at": get_ist_isoformat()
            }}
        )


async def handle_subscription_charged(data):
    """Handle successful subscription payment"""
    payment = data.get("payload", {}).get("payment", {}).get("entity", {})
    subscription = data.get("payload", {}).get("subscription", {}).get("entity", {})
    org_id = subscription.get("notes", {}).get("organization_id")
    
    if org_id:
        # Record payment
        await _db.billing_payments.insert_one({
            "organization_id": org_id,
            "razorpay_payment_id": payment.get("id"),
            "razorpay_subscription_id": subscription.get("id"),
            "amount": payment.get("amount", 0) / 100,
            "currency": payment.get("currency", "INR"),
            "status": "captured",
            "created_at": get_ist_isoformat()
        })
        
        # Update subscription period
        await _db.organizations.update_one(
            {"id": org_id},
            {"$set": {
                "subscription.current_period_start": get_ist_isoformat(),
                "subscription.current_period_end": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "subscription.last_payment_id": payment.get("id"),
                "updated_at": get_ist_isoformat()
            }}
        )


async def handle_subscription_cancelled(data):
    """Handle subscription cancellation"""
    subscription = data.get("payload", {}).get("subscription", {}).get("entity", {})
    org_id = subscription.get("notes", {}).get("organization_id")
    
    if org_id:
        await _db.organizations.update_one(
            {"id": org_id},
            {"$set": {
                "status": "cancelled",
                "subscription.status": "cancelled",
                "subscription.cancelled_at": get_ist_isoformat(),
                "updated_at": get_ist_isoformat()
            }}
        )


async def handle_subscription_halted(data):
    """Handle subscription halt (payment failure)"""
    subscription = data.get("payload", {}).get("subscription", {}).get("entity", {})
    org_id = subscription.get("notes", {}).get("organization_id")
    
    if org_id:
        await _db.organizations.update_one(
            {"id": org_id},
            {"$set": {
                "status": "past_due",
                "subscription.status": "past_due",
                "updated_at": get_ist_isoformat()
            }}
        )


async def handle_payment_captured(data):
    """Handle successful one-time payment"""
    payment = data.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payment.get("order_id")
    
    if order_id:
        order_doc = await _db.billing_orders.find_one({"razorpay_order_id": order_id})
        if order_doc:
            await _db.billing_orders.update_one(
                {"razorpay_order_id": order_id},
                {"$set": {
                    "status": "paid",
                    "razorpay_payment_id": payment.get("id"),
                    "paid_at": get_ist_isoformat()
                }}
            )


async def handle_payment_failed(data):
    """Handle payment failure"""
    payment = data.get("payload", {}).get("payment", {}).get("entity", {})
    logger.warning(f"Payment failed: {payment.get('id')}")


# ==================== BILLING INFO ENDPOINTS ====================

@router.get("/subscription")
async def get_subscription_info(auth_info: dict = Depends(get_org_from_token)):
    """Get current subscription information"""
    org = auth_info.get("organization", {})
    subscription = org.get("subscription", {})
    plan = subscription.get("plan", "trial")
    
    plan_config = SUBSCRIPTION_PLANS.get(plan, {})
    
    # Get payment history
    payments = await _db.billing_payments.find(
        {"organization_id": org["id"]},
        {"_id": 0}
    ).sort("created_at", -1).limit(10).to_list(10)
    
    return {
        "subscription": subscription,
        "plan_config": plan_config,
        "payments": payments
    }


@router.post("/cancel-subscription")
async def cancel_subscription(
    reason: Optional[str] = None,
    auth_info: dict = Depends(get_org_from_token)
):
    """Cancel subscription (will remain active until period end)"""
    org = auth_info.get("organization", {})
    subscription_id = org.get("subscription", {}).get("razorpay_subscription_id")
    
    if subscription_id and _razorpay_client:
        try:
            _razorpay_client.subscription.cancel(subscription_id)
        except Exception as e:
            logger.error(f"Failed to cancel Razorpay subscription: {e}")
    
    # Update organization
    await _db.organizations.update_one(
        {"id": org["id"]},
        {"$set": {
            "subscription.status": "cancelled",
            "subscription.cancelled_at": get_ist_isoformat(),
            "subscription.cancel_reason": reason,
            "updated_at": get_ist_isoformat()
        }}
    )
    
    return {
        "message": "Subscription cancelled. Access will continue until the end of the billing period.",
        "period_end": org.get("subscription", {}).get("current_period_end")
    }


@router.get("/invoices")
async def get_invoices(
    page: int = 1,
    limit: int = 20,
    auth_info: dict = Depends(get_org_from_token)
):
    """Get billing invoices"""
    org = auth_info.get("organization", {})
    
    skip = (page - 1) * limit
    
    payments = await _db.billing_payments.find(
        {"organization_id": org["id"]},
        {"_id": 0}
    ).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    
    total = await _db.billing_payments.count_documents({"organization_id": org["id"]})
    
    return {
        "invoices": payments,
        "total": total,
        "page": page,
        "pages": (total + limit - 1) // limit
    }
