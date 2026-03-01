import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { 
  CheckCircle2, ArrowRight, Sparkles,
  ChevronRight, RefreshCw, Loader2
} from 'lucide-react';
import { Button } from '../components/ui/button';
import PublicHeader from '../components/public/PublicHeader';
import PublicFooter from '../components/public/PublicFooter';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Fallback plans if API fails
const FALLBACK_PLANS = [
  {
    id: 'trial',
    name: 'Free Trial',
    slug: 'trial',
    price_monthly: 0,
    description: 'Try all features free for 14 days',
    is_trial: true,
    trial_days: 14,
    limits: { companies: 2, devices: 50, users: 5 },
    features: { ticketing: true, device_management: true, warranty_tracking: true },
    highlighted: false
  },
  {
    id: 'starter',
    name: 'Starter',
    slug: 'starter',
    price_monthly: 299900,
    description: 'For small IT teams',
    limits: { companies: 5, devices: 100, users: 10 },
    features: { ticketing: true, device_management: true, warranty_tracking: true, amc_management: true, reports_basic: true },
    highlighted: false
  },
  {
    id: 'professional',
    name: 'Professional',
    slug: 'professional',
    price_monthly: 799900,
    description: 'For growing businesses',
    is_popular: true,
    limits: { companies: 25, devices: 500, users: 50 },
    features: { ticketing: true, device_management: true, warranty_tracking: true, amc_management: true, sla_management: true, email_integration: true, custom_forms: true, reports_advanced: true, api_access: true },
    highlighted: true
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    slug: 'enterprise',
    price_monthly: -1,
    description: 'For large organizations',
    limits: { companies: -1, devices: -1, users: -1 },
    features: { ticketing: true, device_management: true, warranty_tracking: true, amc_management: true, sla_management: true, email_integration: true, custom_forms: true, reports_advanced: true, api_access: true, white_labeling: true, dedicated_support: true },
    highlighted: false
  }
];

const formatPrice = (paise) => {
  if (!paise || paise === 0) return { amount: 'Free', period: '' };
  if (paise < 0) return { amount: 'Custom', period: '' };
  const amount = paise / 100;
  return {
    amount: new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 0
    }).format(amount),
    period: '/month'
  };
};

const formatLimit = (value) => {
  if (value === -1 || value === null || value === undefined) return 'Unlimited';
  return value.toLocaleString();
};

export default function SignupPage() {
  const [step, setStep] = useState(1);
  const [selectedPlan, setSelectedPlan] = useState('trial');
  const [plans, setPlans] = useState([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [formData, setFormData] = useState({
    organization_name: '',
    owner_name: '',
    owner_email: '',
    owner_password: '',
    confirm_password: '',
    phone: '',
    industry: '',
    company_size: ''
  });
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    setLoadingPlans(true);
    try {
      const response = await axios.get(`${API}/api/public/plans`);
      const fetchedPlans = response.data || [];
      
      // Transform plans for display
      const transformedPlans = fetchedPlans.map(plan => ({
        ...plan,
        highlighted: plan.is_popular || false
      }));
      
      setPlans(transformedPlans.length > 0 ? transformedPlans : FALLBACK_PLANS);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      setPlans(FALLBACK_PLANS);
    } finally {
      setLoadingPlans(false);
    }
  };

  const getSelectedPlanData = () => {
    return plans.find(p => p.slug === selectedPlan || p.id === selectedPlan) || plans[0];
  };

  const getPlanFeatures = (plan) => {
    const features = [];
    const limits = plan.limits || {};
    
    // Add limits as features
    if (limits.companies) features.push(`${formatLimit(limits.companies)} Companies`);
    if (limits.devices) features.push(`${formatLimit(limits.devices)} Devices`);
    if (limits.users) features.push(`${formatLimit(limits.users)} Users`);
    
    // Add enabled features
    const featureMap = plan.features || {};
    const featureLabels = {
      ticketing: 'Support Ticketing',
      device_management: 'Device Management',
      warranty_tracking: 'Warranty Tracking',
      amc_management: 'AMC Management',
      sla_management: 'SLA Management',
      email_integration: 'Email Integration',
      api_access: 'API Access',
      reports_basic: 'Basic Reports',
      reports_advanced: 'Advanced Reports',
      white_labeling: 'White Labeling',
      dedicated_support: 'Dedicated Support',
      ai_features: 'AI Features'
    };
    
    Object.entries(featureMap).forEach(([key, enabled]) => {
      if (enabled && featureLabels[key]) {
        features.push(featureLabels[key]);
      }
    });
    
    return features.slice(0, 8); // Limit to 8 features for display
  };

  const validateForm = () => {
    const newErrors = {};
    
    if (!formData.organization_name.trim()) {
      newErrors.organization_name = 'Organization name is required';
    }
    if (!formData.owner_name.trim()) {
      newErrors.owner_name = 'Your name is required';
    }
    if (!formData.owner_email.trim()) {
      newErrors.owner_email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(formData.owner_email)) {
      newErrors.owner_email = 'Invalid email format';
    }
    if (!formData.owner_password) {
      newErrors.owner_password = 'Password is required';
    } else if (formData.owner_password.length < 8) {
      newErrors.owner_password = 'Password must be at least 8 characters';
    }
    if (formData.owner_password !== formData.confirm_password) {
      newErrors.confirm_password = 'Passwords do not match';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSignup = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) return;
    
    setLoading(true);
    
    try {
      const response = await axios.post(`${API}/api/org/signup`, {
        name: formData.organization_name,
        slug: formData.organization_name.toLowerCase().replace(/[^a-z0-9]+/g, '-'),
        owner_email: formData.owner_email,
        owner_name: formData.owner_name,
        owner_password: formData.owner_password,
        phone: formData.phone,
        industry: formData.industry,
        company_size: formData.company_size
      });

      localStorage.setItem('token', response.data.access_token);
      localStorage.setItem('orgAdmin', JSON.stringify(response.data.user));
      localStorage.setItem('organization', JSON.stringify(response.data.organization));

      if (selectedPlan === 'trial') {
        toast.success('Welcome! Your 14-day trial has started.');
        navigate('/admin/dashboard');
      } else if (selectedPlan === 'enterprise') {
        toast.success('Account created! Our team will contact you shortly.');
        navigate('/admin/dashboard');
      } else {
        setStep(3);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handlePayment = async () => {
    setLoading(true);
    
    try {
      const token = localStorage.getItem('token');
      const response = await axios.post(`${API}/api/billing/create-subscription`, {
        plan: selectedPlan,
        billing_cycle: 'monthly'
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });

      const options = {
        key: response.data.razorpay_key,
        subscription_id: response.data.subscription_id,
        name: 'aftersales.support',
        description: `${getSelectedPlanData()?.name || 'Selected'} Plan`,
        handler: async (razorpayResponse) => {
          await axios.post(`${API}/api/billing/verify-payment`, {
            razorpay_payment_id: razorpayResponse.razorpay_payment_id,
            razorpay_subscription_id: razorpayResponse.razorpay_subscription_id,
            razorpay_signature: razorpayResponse.razorpay_signature
          }, {
            headers: { Authorization: `Bearer ${token}` }
          });
          
          toast.success('Payment successful! Welcome aboard.');
          navigate('/admin/dashboard');
        },
        prefill: {
          name: formData.owner_name,
          email: formData.owner_email,
          contact: formData.phone
        },
        theme: {
          color: '#0F62FE'
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (error) {
      toast.error('Payment initialization failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50" data-testid="signup-page">
      <PublicHeader />

      <main className="max-w-7xl mx-auto px-4 pt-28 pb-12">
        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 mb-12">
          {['Select Plan', 'Create Account', 'Payment'].map((label, idx) => (
            <div key={label} className="flex items-center">
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${step > idx + 1 ? 'bg-emerald-500 text-white' : 
                  step === idx + 1 ? 'bg-[#0F62FE] text-white' : 
                  'bg-slate-200 text-slate-500'}
              `}>
                {step > idx + 1 ? <CheckCircle2 className="w-5 h-5" /> : idx + 1}
              </div>
              <span className={`ml-2 text-sm ${step >= idx + 1 ? 'text-slate-900' : 'text-slate-500'}`}>
                {label}
              </span>
              {idx < 2 && (
                <ChevronRight className="w-5 h-5 text-slate-400 mx-4" />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Plan Selection */}
        {step === 1 && (
          <div data-testid="plan-selection">
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-slate-900 mb-4">Choose Your Plan</h1>
              <p className="text-slate-600 text-lg">Start with a free trial, upgrade anytime</p>
              <Button
                variant="ghost"
                size="sm"
                onClick={fetchPlans}
                disabled={loadingPlans}
                className="mt-4 text-slate-500 hover:text-slate-700"
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${loadingPlans ? 'animate-spin' : ''}`} />
                Refresh Plans
              </Button>
            </div>

            {loadingPlans ? (
              <div className="flex items-center justify-center py-20">
                <Loader2 className="w-8 h-8 animate-spin text-[#0F62FE]" />
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  {plans.map(plan => {
                    const price = formatPrice(plan.price_monthly);
                    const features = getPlanFeatures(plan);
                    const planId = plan.slug || plan.id;
                    
                    return (
                      <div
                        key={planId}
                        onClick={() => setSelectedPlan(planId)}
                        className={`
                          relative p-6 rounded-2xl cursor-pointer transition-all duration-300
                          ${selectedPlan === planId 
                            ? 'bg-white border-2 border-[#0F62FE] shadow-xl scale-105' 
                            : 'bg-white border border-slate-200 hover:border-slate-300 hover:shadow-lg'}
                          ${plan.is_popular ? 'ring-2 ring-[#0F62FE]/30' : ''}
                        `}
                        data-testid={`plan-card-${planId}`}
                      >
                        {plan.is_popular && (
                          <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                            <span className="px-3 py-1 bg-[#0F62FE] text-white text-xs font-semibold rounded-full">
                              MOST POPULAR
                            </span>
                          </div>
                        )}
                        
                        <h3 className="text-xl font-bold text-slate-900 mb-2">{plan.name}</h3>
                        <p className="text-slate-500 text-sm mb-4">{plan.description || plan.tagline}</p>
                        
                        <div className="mb-6">
                          <span className="text-3xl font-bold text-slate-900">{price.amount}</span>
                          {price.period && <span className="text-slate-500">{price.period}</span>}
                        </div>

                        <ul className="space-y-2 mb-6">
                          {features.map((feature, idx) => (
                            <li key={idx} className="flex items-center gap-2 text-sm text-slate-600">
                              <CheckCircle2 className="w-4 h-4 text-emerald-500 flex-shrink-0" />
                              {feature}
                            </li>
                          ))}
                        </ul>

                        <div className={`
                          w-full py-2 rounded-lg text-center text-sm font-medium transition-colors
                          ${selectedPlan === planId 
                            ? 'bg-[#0F62FE] text-white' 
                            : 'bg-slate-100 text-slate-600'}
                        `}>
                          {selectedPlan === planId ? 'Selected' : 'Select'}
                        </div>
                      </div>
                    );
                  })}
                </div>

                <div className="text-center">
                  <Button
                    onClick={() => setStep(2)}
                    className="px-8 py-3 bg-[#0F62FE] hover:bg-[#0043CE] text-white rounded-xl"
                    size="lg"
                    data-testid="continue-to-account-btn"
                  >
                    Continue with {getSelectedPlanData()?.name || 'Selected Plan'}
                    <ArrowRight className="w-5 h-5 ml-2" />
                  </Button>
                </div>
              </>
            )}
          </div>
        )}

        {/* Step 2: Account Details */}
        {step === 2 && (
          <div className="max-w-xl mx-auto" data-testid="account-form">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-slate-900 mb-2">Create Your Account</h1>
              <p className="text-slate-600">Set up your organization on aftersales.support</p>
            </div>

            <form onSubmit={handleSignup} className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Organization Name *
                  </label>
                  <input
                    type="text"
                    value={formData.organization_name}
                    onChange={(e) => setFormData({ ...formData, organization_name: e.target.value })}
                    className={`w-full px-4 py-3 bg-white border ${errors.organization_name ? 'border-red-500' : 'border-slate-300'} rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-[#0F62FE] focus:border-transparent`}
                    placeholder="Acme Corporation"
                    data-testid="input-org-name"
                  />
                  {errors.organization_name && (
                    <p className="text-red-500 text-sm mt-1">{errors.organization_name}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Your Name *
                    </label>
                    <input
                      type="text"
                      value={formData.owner_name}
                      onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                      className={`w-full px-4 py-3 bg-white border ${errors.owner_name ? 'border-red-500' : 'border-slate-300'} rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-[#0F62FE] focus:border-transparent`}
                      placeholder="John Doe"
                      data-testid="input-owner-name"
                    />
                    {errors.owner_name && (
                      <p className="text-red-500 text-sm mt-1">{errors.owner_name}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-[#0F62FE] focus:border-transparent"
                      placeholder="+91 98765 43210"
                      data-testid="input-phone"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1.5">
                    Work Email *
                  </label>
                  <input
                    type="email"
                    value={formData.owner_email}
                    onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
                    className={`w-full px-4 py-3 bg-white border ${errors.owner_email ? 'border-red-500' : 'border-slate-300'} rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-[#0F62FE] focus:border-transparent`}
                    placeholder="john@acme.com"
                    data-testid="input-email"
                  />
                  {errors.owner_email && (
                    <p className="text-red-500 text-sm mt-1">{errors.owner_email}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Password *
                    </label>
                    <input
                      type="password"
                      value={formData.owner_password}
                      onChange={(e) => setFormData({ ...formData, owner_password: e.target.value })}
                      className={`w-full px-4 py-3 bg-white border ${errors.owner_password ? 'border-red-500' : 'border-slate-300'} rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-[#0F62FE] focus:border-transparent`}
                      placeholder="••••••••"
                      data-testid="input-password"
                    />
                    {errors.owner_password && (
                      <p className="text-red-500 text-sm mt-1">{errors.owner_password}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Confirm Password *
                    </label>
                    <input
                      type="password"
                      value={formData.confirm_password}
                      onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                      className={`w-full px-4 py-3 bg-white border ${errors.confirm_password ? 'border-red-500' : 'border-slate-300'} rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-[#0F62FE] focus:border-transparent`}
                      placeholder="••••••••"
                      data-testid="input-confirm-password"
                    />
                    {errors.confirm_password && (
                      <p className="text-red-500 text-sm mt-1">{errors.confirm_password}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Industry
                    </label>
                    <select
                      value={formData.industry}
                      onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                      className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 focus:ring-2 focus:ring-[#0F62FE] focus:border-transparent"
                      data-testid="select-industry"
                    >
                      <option value="">Select industry</option>
                      <option value="IT Services">IT Services</option>
                      <option value="Manufacturing">Manufacturing</option>
                      <option value="Healthcare">Healthcare</option>
                      <option value="Education">Education</option>
                      <option value="Finance">Finance</option>
                      <option value="Retail">Retail</option>
                      <option value="Other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1.5">
                      Company Size
                    </label>
                    <select
                      value={formData.company_size}
                      onChange={(e) => setFormData({ ...formData, company_size: e.target.value })}
                      className="w-full px-4 py-3 bg-white border border-slate-300 rounded-lg text-slate-900 focus:ring-2 focus:ring-[#0F62FE] focus:border-transparent"
                      data-testid="select-company-size"
                    >
                      <option value="">Select size</option>
                      <option value="1-10">1-10 employees</option>
                      <option value="11-50">11-50 employees</option>
                      <option value="51-200">51-200 employees</option>
                      <option value="201-500">201-500 employees</option>
                      <option value="500+">500+ employees</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="mt-8 flex gap-4">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep(1)}
                  className="flex-1 border-slate-300 text-slate-700 hover:bg-slate-50"
                  data-testid="back-btn"
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-[#0F62FE] hover:bg-[#0043CE]"
                  data-testid="submit-btn"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </svg>
                      Creating account...
                    </span>
                  ) : selectedPlan === 'trial' ? (
                    'Start Free Trial'
                  ) : (
                    'Continue to Payment'
                  )}
                </Button>
              </div>

              <p className="text-center text-sm text-slate-500 mt-6">
                By signing up, you agree to our{' '}
                <Link to="/page/terms-of-service" className="text-[#0F62FE] hover:underline">Terms of Service</Link>
                {' '}and{' '}
                <Link to="/page/privacy-policy" className="text-[#0F62FE] hover:underline">Privacy Policy</Link>
              </p>
            </form>
          </div>
        )}

        {/* Step 3: Payment */}
        {step === 3 && (
          <div className="max-w-md mx-auto text-center" data-testid="payment-step">
            <div className="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
              <div className="w-16 h-16 bg-[#0F62FE]/10 rounded-full flex items-center justify-center mx-auto mb-6">
                <Sparkles className="w-8 h-8 text-[#0F62FE]" />
              </div>
              
              <h2 className="text-2xl font-bold text-slate-900 mb-2">Complete Your Purchase</h2>
              <p className="text-slate-600 mb-6">
                You're subscribing to the {PLANS.find(p => p.id === selectedPlan)?.name} plan
              </p>

              <div className="bg-slate-50 rounded-lg p-4 mb-6">
                <div className="flex justify-between items-center">
                  <span className="text-slate-600">{PLANS.find(p => p.id === selectedPlan)?.name} (Monthly)</span>
                  <span className="text-slate-900 font-bold">
                    ₹{PLANS.find(p => p.id === selectedPlan)?.price?.toLocaleString()}
                  </span>
                </div>
              </div>

              <Button
                onClick={handlePayment}
                disabled={loading}
                className="w-full py-3 bg-[#0F62FE] hover:bg-[#0043CE]"
                data-testid="pay-btn"
              >
                {loading ? 'Processing...' : 'Pay with Razorpay'}
              </Button>

              <p className="text-xs text-slate-500 mt-4">
                Secure payment powered by Razorpay. Cancel anytime.
              </p>
            </div>
          </div>
        )}
      </main>

      <PublicFooter variant="simple" />
    </div>
  );
}
