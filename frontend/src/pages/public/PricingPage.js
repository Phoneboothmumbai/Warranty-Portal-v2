import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { Check, X, ArrowRight, Sparkles, RefreshCw } from 'lucide-react';
import { Button } from '../../components/ui/button';
import PublicHeader from '../../components/public/PublicHeader';
import PublicFooter from '../../components/public/PublicFooter';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const formatPrice = (paise, currency = 'INR') => {
  if (!paise || paise === 0) return 'Free';
  if (paise < 0) return 'Custom';
  const amount = paise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0
  }).format(amount);
};

const FEATURE_LABELS = {
  ticketing: 'Support Ticketing',
  device_management: 'Device Management',
  warranty_tracking: 'Warranty Tracking',
  amc_management: 'AMC Management',
  sla_management: 'SLA Management',
  email_integration: 'Email Integration',
  api_access: 'API Access',
  custom_forms: 'Custom Forms',
  knowledge_base: 'Knowledge Base',
  reports_basic: 'Basic Reports',
  reports_advanced: 'Advanced Reports',
  white_labeling: 'White Labeling',
  custom_domain: 'Custom Domain',
  sso_integration: 'SSO Integration',
  priority_support: 'Priority Support',
  dedicated_support: 'Dedicated Support',
  ai_features: 'AI Features',
  bulk_import: 'Bulk Import',
  export_data: 'Export Data',
  audit_logs: 'Audit Logs',
  multi_department: 'Multi-Department',
  custom_workflows: 'Custom Workflows'
};

const KEY_FEATURES = [
  'ticketing',
  'device_management',
  'warranty_tracking',
  'amc_management',
  'sla_management',
  'email_integration',
  'api_access',
  'knowledge_base',
  'ai_features',
  'white_labeling'
];

const PricingPage = () => {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [billingPeriod, setBillingPeriod] = useState('monthly');

  useEffect(() => {
    fetchPlans();
  }, []);

  const fetchPlans = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/api/public/plans`);
      setPlans(response.data || []);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
    } finally {
      setLoading(false);
    }
  };

  const getPrice = (plan) => {
    if (plan.is_trial) return 'Free';
    const price = billingPeriod === 'yearly' ? plan.price_yearly : plan.price_monthly;
    return formatPrice(price, plan.currency);
  };

  const getPeriod = (plan) => {
    if (plan.is_trial) return `${plan.trial_days} days`;
    if (plan.price_monthly === 0 && !plan.is_trial) return 'Contact us';
    return billingPeriod === 'yearly' ? '/year' : '/month';
  };

  const getLimitDisplay = (value) => {
    if (value === -1) return 'Unlimited';
    return value;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-white">
        <PublicHeader />
        <div className="flex items-center justify-center h-96 pt-16">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-slate-900"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white" data-testid="pricing-page">
      <PublicHeader />

      {/* Hero */}
      <section className="pt-32 pb-16 sm:pt-40 sm:pb-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <span className="text-sm font-mono uppercase tracking-widest text-[#0F62FE] mb-4 block">
            Pricing
          </span>
          <h1 className="text-4xl sm:text-5xl font-bold text-slate-900 tracking-tight">
            Simple, transparent pricing
          </h1>
          <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
            Choose the plan that fits your needs. All plans include core features.
            Upgrade or downgrade anytime.
          </p>

          {/* Billing toggle */}
          <div className="mt-8 inline-flex items-center gap-3 bg-slate-100 p-1 rounded-full">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                billingPeriod === 'monthly'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              data-testid="billing-monthly"
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('yearly')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                billingPeriod === 'yearly'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
              data-testid="billing-yearly"
            >
              Yearly
              <span className="ml-1 text-xs text-green-600 font-semibold">Save 17%</span>
            </button>
          </div>
        </div>
      </section>

      {/* Plans */}
      <section className="pb-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid gap-8 lg:grid-cols-4 md:grid-cols-2">
            {plans.map((plan) => (
              <div
                key={plan.id}
                className={`relative rounded-2xl border ${
                  plan.is_popular
                    ? 'border-[#0F62FE] shadow-xl'
                    : 'border-slate-200'
                } bg-white p-6 flex flex-col`}
                data-testid={`plan-card-${plan.slug}`}
              >
                {plan.is_popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-[#0F62FE] text-white text-xs font-semibold px-3 py-1 rounded-full flex items-center gap-1">
                      <Sparkles className="w-3 h-3" />
                      Most Popular
                    </span>
                  </div>
                )}

                {/* Plan header */}
                <div className="mb-6">
                  <h3 className="text-lg font-semibold text-slate-900">{plan.name}</h3>
                  <p className="text-sm text-slate-500 mt-1">{plan.tagline}</p>
                </div>

                {/* Price */}
                <div className="mb-6">
                  <div className="flex items-baseline gap-1">
                    <span className="text-4xl font-bold text-slate-900">
                      {getPrice(plan)}
                    </span>
                    <span className="text-slate-500 text-sm">
                      {getPeriod(plan)}
                    </span>
                  </div>
                </div>

                {/* CTA */}
                <Link to="/signup" className="mb-6">
                  <Button 
                    className={`w-full ${
                      plan.is_popular 
                        ? 'bg-[#0F62FE] hover:bg-[#0043CE]' 
                        : 'bg-white text-slate-900 border border-slate-200 hover:bg-slate-50'
                    }`}
                    variant={plan.is_popular ? 'default' : 'outline'}
                  >
                    {plan.is_trial ? 'Start Free Trial' : plan.price_monthly === 0 ? 'Contact Sales' : 'Get Started'}
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </Link>

                {/* Limits */}
                <div className="space-y-2 mb-6 pb-6 border-b border-slate-100">
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Companies</span>
                    <span className="font-medium text-slate-900">
                      {getLimitDisplay(plan.limits?.max_companies)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Devices</span>
                    <span className="font-medium text-slate-900">
                      {getLimitDisplay(plan.limits?.max_devices)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Team Members</span>
                    <span className="font-medium text-slate-900">
                      {getLimitDisplay(plan.limits?.max_users)}
                    </span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="text-slate-600">Tickets/month</span>
                    <span className="font-medium text-slate-900">
                      {getLimitDisplay(plan.limits?.max_tickets_per_month)}
                    </span>
                  </div>
                </div>

                {/* Features */}
                <div className="flex-1">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
                    Features
                  </p>
                  <ul className="space-y-2">
                    {KEY_FEATURES.map((featureKey) => {
                      const enabled = plan.features?.[featureKey];
                      return (
                        <li key={featureKey} className="flex items-center gap-2 text-sm">
                          {enabled ? (
                            <Check className="w-4 h-4 text-green-600 flex-shrink-0" />
                          ) : (
                            <X className="w-4 h-4 text-slate-300 flex-shrink-0" />
                          )}
                          <span className={enabled ? 'text-slate-700' : 'text-slate-400'}>
                            {FEATURE_LABELS[featureKey] || featureKey}
                          </span>
                        </li>
                      );
                    })}
                  </ul>
                </div>

                {/* Support level */}
                {plan.support_level && plan.support_level !== 'community' && (
                  <div className="mt-4 pt-4 border-t border-slate-100">
                    <p className="text-xs text-slate-500">
                      {plan.support_level === 'email' && '📧 Email support'}
                      {plan.support_level === 'priority' && '⚡ Priority support'}
                      {plan.support_level === 'dedicated' && '🎯 Dedicated support'}
                      {plan.response_time_hours && ` (${plan.response_time_hours}h response)`}
                    </p>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ or CTA */}
      <section className="py-16 bg-slate-50 border-t border-slate-100">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl font-bold text-slate-900">Need help choosing?</h2>
          <p className="mt-2 text-slate-600">
            Our team is here to help you find the right plan for your business.
          </p>
          <div className="mt-6 flex gap-4 justify-center">
            <Link to="/signup">
              <Button className="bg-[#0F62FE] hover:bg-[#0043CE]">Start Free Trial</Button>
            </Link>
            <a href="mailto:sales@aftersales.support">
              <Button variant="outline">Contact Sales</Button>
            </a>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
};

export default PricingPage;
