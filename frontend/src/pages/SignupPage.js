import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { toast } from 'sonner';
import { 
  Building2, CheckCircle2, ArrowRight, Sparkles, Shield, 
  Zap, Users, HardDrive, Ticket, ChevronRight
} from 'lucide-react';
import { Button } from '../components/ui/button';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const PLANS = [
  {
    id: 'trial',
    name: 'Free Trial',
    price: 0,
    period: '14 days',
    description: 'Try all features free for 14 days',
    features: [
      '2 Companies',
      '50 Devices',
      '5 Users',
      'Basic Ticketing',
      'Device Management',
      'Warranty Tracking'
    ],
    highlighted: false,
    cta: 'Start Free Trial'
  },
  {
    id: 'starter',
    name: 'Starter',
    price: 2999,
    period: '/month',
    description: 'For small IT teams',
    features: [
      '5 Companies',
      '100 Devices',
      '10 Users',
      'Everything in Trial',
      'AMC Management',
      'Basic Reports'
    ],
    highlighted: false,
    cta: 'Get Started'
  },
  {
    id: 'professional',
    name: 'Professional',
    price: 7999,
    period: '/month',
    description: 'For growing businesses',
    features: [
      '25 Companies',
      '500 Devices',
      '50 Users',
      'Everything in Starter',
      'SLA Management',
      'Email Integration',
      'Custom Forms',
      'Advanced Reports',
      'API Access'
    ],
    highlighted: true,
    cta: 'Get Professional'
  },
  {
    id: 'enterprise',
    name: 'Enterprise',
    price: null,
    period: 'Custom',
    description: 'For large organizations',
    features: [
      'Unlimited Companies',
      'Unlimited Devices',
      'Unlimited Users',
      'Everything in Pro',
      'Custom Branding',
      'Dedicated Support',
      'SLA Guarantee',
      'Custom Integrations'
    ],
    highlighted: false,
    cta: 'Contact Sales'
  }
];

export default function SignupPage() {
  const [step, setStep] = useState(1); // 1: Plan selection, 2: Account details, 3: Payment (if not trial)
  const [selectedPlan, setSelectedPlan] = useState('trial');
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

      // Store auth data
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
        // Redirect to payment
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
      // Create Razorpay subscription order
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
        name: 'Warranty Portal',
        description: `${PLANS.find(p => p.id === selectedPlan)?.name} Plan`,
        handler: async (razorpayResponse) => {
          // Verify payment on backend
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
          color: '#7C3AED'
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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900/20 to-slate-900">
      {/* Header */}
      <header className="border-b border-slate-800">
        <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2">
            <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-purple-600 rounded-xl flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-white">Warranty Portal</span>
          </Link>
          <div className="flex items-center gap-4">
            <span className="text-slate-400 text-sm">Already have an account?</span>
            <Link to="/admin/login">
              <Button variant="outline" className="border-slate-600 text-slate-300 hover:bg-slate-800">
                Sign In
              </Button>
            </Link>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-12">
        {/* Progress Steps */}
        <div className="flex items-center justify-center gap-4 mb-12">
          {['Select Plan', 'Create Account', 'Payment'].map((label, idx) => (
            <div key={label} className="flex items-center">
              <div className={`
                w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${step > idx + 1 ? 'bg-emerald-500 text-white' : 
                  step === idx + 1 ? 'bg-purple-600 text-white' : 
                  'bg-slate-700 text-slate-400'}
              `}>
                {step > idx + 1 ? <CheckCircle2 className="w-5 h-5" /> : idx + 1}
              </div>
              <span className={`ml-2 text-sm ${step >= idx + 1 ? 'text-white' : 'text-slate-500'}`}>
                {label}
              </span>
              {idx < 2 && (
                <ChevronRight className="w-5 h-5 text-slate-600 mx-4" />
              )}
            </div>
          ))}
        </div>

        {/* Step 1: Plan Selection */}
        {step === 1 && (
          <div data-testid="plan-selection">
            <div className="text-center mb-12">
              <h1 className="text-4xl font-bold text-white mb-4">Choose Your Plan</h1>
              <p className="text-slate-400 text-lg">Start with a free trial, upgrade anytime</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
              {PLANS.map(plan => (
                <div
                  key={plan.id}
                  onClick={() => setSelectedPlan(plan.id)}
                  className={`
                    relative p-6 rounded-2xl cursor-pointer transition-all duration-300
                    ${selectedPlan === plan.id 
                      ? 'bg-purple-600/20 border-2 border-purple-500 scale-105' 
                      : 'bg-slate-800/50 border border-slate-700 hover:border-slate-600'}
                    ${plan.highlighted ? 'ring-2 ring-purple-500/50' : ''}
                  `}
                >
                  {plan.highlighted && (
                    <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                      <span className="px-3 py-1 bg-gradient-to-r from-violet-500 to-purple-600 text-white text-xs font-semibold rounded-full">
                        MOST POPULAR
                      </span>
                    </div>
                  )}
                  
                  <h3 className="text-xl font-bold text-white mb-2">{plan.name}</h3>
                  <p className="text-slate-400 text-sm mb-4">{plan.description}</p>
                  
                  <div className="mb-6">
                    {plan.price !== null ? (
                      <>
                        <span className="text-3xl font-bold text-white">₹{plan.price.toLocaleString()}</span>
                        <span className="text-slate-400">{plan.period}</span>
                      </>
                    ) : (
                      <span className="text-2xl font-bold text-white">Custom Pricing</span>
                    )}
                  </div>

                  <ul className="space-y-2 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-center gap-2 text-sm text-slate-300">
                        <CheckCircle2 className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>

                  <div className={`
                    w-full py-2 rounded-lg text-center text-sm font-medium transition-colors
                    ${selectedPlan === plan.id 
                      ? 'bg-purple-600 text-white' 
                      : 'bg-slate-700 text-slate-300'}
                  `}>
                    {selectedPlan === plan.id ? 'Selected' : 'Select'}
                  </div>
                </div>
              ))}
            </div>

            <div className="text-center">
              <Button
                onClick={() => setStep(2)}
                className="px-8 py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white rounded-xl"
                size="lg"
              >
                Continue with {PLANS.find(p => p.id === selectedPlan)?.name}
                <ArrowRight className="w-5 h-5 ml-2" />
              </Button>
            </div>
          </div>
        )}

        {/* Step 2: Account Details */}
        {step === 2 && (
          <div className="max-w-xl mx-auto" data-testid="account-form">
            <div className="text-center mb-8">
              <h1 className="text-3xl font-bold text-white mb-2">Create Your Account</h1>
              <p className="text-slate-400">Set up your organization on Warranty Portal</p>
            </div>

            <form onSubmit={handleSignup} className="bg-slate-800/50 rounded-2xl p-8 border border-slate-700">
              <div className="space-y-5">
                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Organization Name *
                  </label>
                  <input
                    type="text"
                    value={formData.organization_name}
                    onChange={(e) => setFormData({ ...formData, organization_name: e.target.value })}
                    className={`w-full px-4 py-3 bg-slate-700/50 border ${errors.organization_name ? 'border-red-500' : 'border-slate-600'} rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent`}
                    placeholder="Acme Corporation"
                  />
                  {errors.organization_name && (
                    <p className="text-red-400 text-sm mt-1">{errors.organization_name}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      Your Name *
                    </label>
                    <input
                      type="text"
                      value={formData.owner_name}
                      onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
                      className={`w-full px-4 py-3 bg-slate-700/50 border ${errors.owner_name ? 'border-red-500' : 'border-slate-600'} rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent`}
                      placeholder="John Doe"
                    />
                    {errors.owner_name && (
                      <p className="text-red-400 text-sm mt-1">{errors.owner_name}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      Phone
                    </label>
                    <input
                      type="tel"
                      value={formData.phone}
                      onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                      placeholder="+91 98765 43210"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-slate-300 mb-1.5">
                    Work Email *
                  </label>
                  <input
                    type="email"
                    value={formData.owner_email}
                    onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
                    className={`w-full px-4 py-3 bg-slate-700/50 border ${errors.owner_email ? 'border-red-500' : 'border-slate-600'} rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent`}
                    placeholder="john@acme.com"
                  />
                  {errors.owner_email && (
                    <p className="text-red-400 text-sm mt-1">{errors.owner_email}</p>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      Password *
                    </label>
                    <input
                      type="password"
                      value={formData.owner_password}
                      onChange={(e) => setFormData({ ...formData, owner_password: e.target.value })}
                      className={`w-full px-4 py-3 bg-slate-700/50 border ${errors.owner_password ? 'border-red-500' : 'border-slate-600'} rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent`}
                      placeholder="••••••••"
                    />
                    {errors.owner_password && (
                      <p className="text-red-400 text-sm mt-1">{errors.owner_password}</p>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      Confirm Password *
                    </label>
                    <input
                      type="password"
                      value={formData.confirm_password}
                      onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
                      className={`w-full px-4 py-3 bg-slate-700/50 border ${errors.confirm_password ? 'border-red-500' : 'border-slate-600'} rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent`}
                      placeholder="••••••••"
                    />
                    {errors.confirm_password && (
                      <p className="text-red-400 text-sm mt-1">{errors.confirm_password}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      Industry
                    </label>
                    <select
                      value={formData.industry}
                      onChange={(e) => setFormData({ ...formData, industry: e.target.value })}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                    <label className="block text-sm font-medium text-slate-300 mb-1.5">
                      Company Size
                    </label>
                    <select
                      value={formData.company_size}
                      onChange={(e) => setFormData({ ...formData, company_size: e.target.value })}
                      className="w-full px-4 py-3 bg-slate-700/50 border border-slate-600 rounded-lg text-white focus:ring-2 focus:ring-purple-500 focus:border-transparent"
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
                  className="flex-1 border-slate-600 text-slate-300"
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  disabled={loading}
                  className="flex-1 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700"
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
                <a href="#" className="text-purple-400 hover:text-purple-300">Terms of Service</a>
                {' '}and{' '}
                <a href="#" className="text-purple-400 hover:text-purple-300">Privacy Policy</a>
              </p>
            </form>
          </div>
        )}

        {/* Step 3: Payment */}
        {step === 3 && (
          <div className="max-w-md mx-auto text-center" data-testid="payment-step">
            <div className="bg-slate-800/50 rounded-2xl p-8 border border-slate-700">
              <div className="w-16 h-16 bg-purple-600/20 rounded-full flex items-center justify-center mx-auto mb-6">
                <Sparkles className="w-8 h-8 text-purple-400" />
              </div>
              
              <h2 className="text-2xl font-bold text-white mb-2">Complete Your Purchase</h2>
              <p className="text-slate-400 mb-6">
                You're subscribing to the {PLANS.find(p => p.id === selectedPlan)?.name} plan
              </p>

              <div className="bg-slate-700/50 rounded-lg p-4 mb-6">
                <div className="flex justify-between items-center">
                  <span className="text-slate-300">{PLANS.find(p => p.id === selectedPlan)?.name} (Monthly)</span>
                  <span className="text-white font-bold">
                    ₹{PLANS.find(p => p.id === selectedPlan)?.price?.toLocaleString()}
                  </span>
                </div>
              </div>

              <Button
                onClick={handlePayment}
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700"
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
    </div>
  );
}
