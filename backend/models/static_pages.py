"""
Static Pages Model - Editable content pages
===========================================
For legal pages, contact info, and other static content.
"""
import uuid
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from utils.helpers import get_ist_isoformat


class StaticPage(BaseModel):
    """Static page content model"""
    model_config = ConfigDict(extra="ignore")
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Page identification
    slug: str  # unique identifier: contact-us, privacy-policy, terms-of-service, refund-policy, disclaimer
    title: str
    
    # Content (supports HTML/Markdown)
    content: str = ""
    
    # SEO
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    
    # Status
    is_published: bool = True
    
    # Audit
    created_at: str = Field(default_factory=get_ist_isoformat)
    updated_at: str = Field(default_factory=get_ist_isoformat)
    updated_by: Optional[str] = None


class StaticPageUpdate(BaseModel):
    """Update static page content"""
    title: Optional[str] = None
    content: Optional[str] = None
    meta_title: Optional[str] = None
    meta_description: Optional[str] = None
    is_published: Optional[bool] = None


# Default page templates
DEFAULT_PAGES = {
    "contact-us": {
        "title": "Contact Us",
        "content": """
<div class="space-y-6">
    <div>
        <h2 class="text-xl font-semibold mb-2">Get in Touch</h2>
        <p>We'd love to hear from you. Reach out to us through any of the following channels:</p>
    </div>
    
    <div class="grid md:grid-cols-2 gap-6">
        <div class="bg-slate-50 p-4 rounded-lg">
            <h3 class="font-medium mb-2">Email</h3>
            <p class="text-slate-600">support@yourcompany.com</p>
        </div>
        
        <div class="bg-slate-50 p-4 rounded-lg">
            <h3 class="font-medium mb-2">Phone</h3>
            <p class="text-slate-600">+91 98765 43210</p>
        </div>
        
        <div class="bg-slate-50 p-4 rounded-lg">
            <h3 class="font-medium mb-2">Address</h3>
            <p class="text-slate-600">123 Business Park, Tech City<br/>Mumbai, Maharashtra 400001</p>
        </div>
        
        <div class="bg-slate-50 p-4 rounded-lg">
            <h3 class="font-medium mb-2">Business Hours</h3>
            <p class="text-slate-600">Monday - Friday: 9:00 AM - 6:00 PM<br/>Saturday: 10:00 AM - 2:00 PM</p>
        </div>
    </div>
</div>
"""
    },
    "privacy-policy": {
        "title": "Privacy Policy",
        "content": """
<div class="prose max-w-none">
    <p class="text-slate-600 mb-6">Last updated: January 2026</p>
    
    <h2>1. Information We Collect</h2>
    <p>We collect information you provide directly to us, such as when you create an account, use our services, or contact us for support.</p>
    
    <h2>2. How We Use Your Information</h2>
    <p>We use the information we collect to provide, maintain, and improve our services, process transactions, and communicate with you.</p>
    
    <h2>3. Information Sharing</h2>
    <p>We do not sell, trade, or otherwise transfer your personal information to third parties without your consent, except as described in this policy.</p>
    
    <h2>4. Data Security</h2>
    <p>We implement appropriate security measures to protect your personal information against unauthorized access, alteration, disclosure, or destruction.</p>
    
    <h2>5. Your Rights</h2>
    <p>You have the right to access, correct, or delete your personal information. Contact us to exercise these rights.</p>
    
    <h2>6. Contact Us</h2>
    <p>If you have questions about this Privacy Policy, please contact us at privacy@yourcompany.com</p>
</div>
"""
    },
    "terms-of-service": {
        "title": "Terms of Service",
        "content": """
<div class="prose max-w-none">
    <p class="text-slate-600 mb-6">Last updated: January 2026</p>
    
    <h2>1. Acceptance of Terms</h2>
    <p>By accessing or using our services, you agree to be bound by these Terms of Service and our Privacy Policy.</p>
    
    <h2>2. Use of Services</h2>
    <p>You agree to use our services only for lawful purposes and in accordance with these Terms. You are responsible for maintaining the confidentiality of your account.</p>
    
    <h2>3. Subscription and Payments</h2>
    <p>Certain features require a paid subscription. Payments are processed securely through our payment partners. Subscriptions auto-renew unless cancelled.</p>
    
    <h2>4. Intellectual Property</h2>
    <p>All content, features, and functionality of our services are owned by us and protected by intellectual property laws.</p>
    
    <h2>5. Limitation of Liability</h2>
    <p>We shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of our services.</p>
    
    <h2>6. Termination</h2>
    <p>We may terminate or suspend your account at any time for violations of these Terms or for any other reason at our discretion.</p>
    
    <h2>7. Changes to Terms</h2>
    <p>We reserve the right to modify these Terms at any time. Continued use of our services constitutes acceptance of modified Terms.</p>
</div>
"""
    },
    "refund-policy": {
        "title": "Refund Policy",
        "content": """
<div class="prose max-w-none">
    <p class="text-slate-600 mb-6">Last updated: January 2026</p>
    
    <h2>1. Subscription Refunds</h2>
    <p>We offer a 14-day money-back guarantee for new subscriptions. If you're not satisfied with our service, contact us within 14 days of your initial purchase for a full refund.</p>
    
    <h2>2. Refund Process</h2>
    <p>To request a refund:</p>
    <ul>
        <li>Email us at billing@yourcompany.com with your account details</li>
        <li>Include your reason for the refund request</li>
        <li>Refunds are processed within 5-7 business days</li>
    </ul>
    
    <h2>3. Non-Refundable Items</h2>
    <p>The following are not eligible for refunds:</p>
    <ul>
        <li>Subscriptions after the 14-day guarantee period</li>
        <li>Partial month usage</li>
        <li>Add-on services or one-time purchases</li>
    </ul>
    
    <h2>4. Cancellation</h2>
    <p>You may cancel your subscription at any time. Your service will continue until the end of your current billing period.</p>
    
    <h2>5. Contact</h2>
    <p>For billing inquiries, contact us at billing@yourcompany.com</p>
</div>
"""
    },
    "disclaimer": {
        "title": "Disclaimer",
        "content": """
<div class="prose max-w-none">
    <p class="text-slate-600 mb-6">Last updated: January 2026</p>
    
    <h2>1. General Information</h2>
    <p>The information provided on this website is for general informational purposes only. While we strive to keep the information up to date and accurate, we make no representations or warranties of any kind.</p>
    
    <h2>2. Professional Advice</h2>
    <p>The content on this website does not constitute professional advice. For specific advice regarding your business or legal matters, please consult with appropriate professionals.</p>
    
    <h2>3. External Links</h2>
    <p>Our website may contain links to external websites. We are not responsible for the content or privacy practices of these external sites.</p>
    
    <h2>4. Service Availability</h2>
    <p>We strive to maintain continuous service availability but do not guarantee uninterrupted access. Scheduled maintenance and unforeseen circumstances may affect service availability.</p>
    
    <h2>5. Accuracy of Information</h2>
    <p>While we make every effort to ensure the accuracy of information on our platform, we cannot guarantee that all information is complete, accurate, or current.</p>
    
    <h2>6. Limitation</h2>
    <p>Your use of any information or materials on this website is entirely at your own risk, for which we shall not be liable.</p>
</div>
"""
    }
}
