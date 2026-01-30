import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Shield, ArrowRight, Check, HelpCircle, X } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { useSettings } from '../../context/SettingsContext';

const PricingPage = () => {
  const { settings } = useSettings();
  const [billingPeriod, setBillingPeriod] = useState('monthly');

  const plans = [
    {
      name: 'Free Trial',
      monthlyPrice: 0,
      yearlyPrice: 0,
      period: '14 days',
      description: 'Perfect for evaluation',
      features: {
        companies: '2 clients',
        devices: '50',
        users: '5 technicians',
        tickets: '100/month',
        sla: false,
        email: false,
        api: false,
        customForms: false,
        priority: false,
        sso: false
      },
      cta: 'Start Free Trial',
      highlighted: false
    },
    {
      name: 'Starter',
      monthlyPrice: 2999,
      yearlyPrice: 29990,
      period: '/month',
      description: 'For small IT teams',
      features: {
        companies: '5 clients',
        devices: '100',
        users: '10 technicians',
        tickets: '500/month',
        sla: true,
        email: true,
        api: true,
        customForms: false,
        priority: false,
        sso: false
      },
      cta: 'Get Started',
      highlighted: false
    },
    {
      name: 'Professional',
      monthlyPrice: 7999,
      yearlyPrice: 79990,
      period: '/month',
      description: 'For growing MSPs',
      features: {
        companies: '25 clients',
        devices: '500',
        users: '50 technicians',
        tickets: 'Unlimited',
        sla: true,
        email: true,
        api: true,
        customForms: true,
        priority: true,
        sso: false
      },
      cta: 'Get Started',
      highlighted: true
    },
    {
      name: 'Enterprise',
      monthlyPrice: null,
      yearlyPrice: null,
      period: '',
      description: 'For large MSPs',
      features: {
        companies: 'Unlimited',
        devices: 'Unlimited',
        users: 'Unlimited',
        tickets: 'Unlimited',
        sla: true,
        email: true,
        api: true,
        customForms: true,
        priority: true,
        sso: true
      },
      cta: 'Contact Sales',
      highlighted: false
    }
  ];

  const featureLabels = {
    companies: 'Client Organizations',
    devices: 'Total Devices',
    users: 'Technicians',
    tickets: 'Monthly Tickets',
    sla: 'SLA Management',
    email: 'Email-to-Ticket',
    api: 'API Access',
    customForms: 'Custom Forms',
    priority: 'Priority Support',
    sso: 'SSO Integration'
  };

  const faqs = [
    {
      question: 'Can I switch plans as my MSP grows?',
      answer: 'Absolutely! You can upgrade anytime as you onboard more clients. When upgrading, you\'ll be prorated for the remaining period. Downgrading applies from your next billing cycle.'
    },
    {
      question: 'What happens after my trial ends?',
      answer: 'After your 14-day trial, you\'ll need to select a paid plan to continue. Your data (all clients, assets, tickets) will be preserved for 30 days, giving you time to decide.'
    },
    {
      question: 'Is there a setup fee or onboarding cost?',
      answer: 'No setup fees or hidden charges. Enterprise plans include free onboarding and training for your team.'
    },
    {
      question: 'Do you offer discounts for annual billing?',
      answer: 'Yes! Annual billing saves you approximately 17% (pay for 10 months, get 12). Great for MSPs with predictable client bases.'
    },
    {
      question: 'What payment methods do you accept?',
      answer: 'We accept all major credit/debit cards, UPI, net banking, and wallets through our secure payment partner Razorpay.'
    },
    {
      question: 'Can I get a refund?',
      answer: 'Yes, we offer a 7-day money-back guarantee for all paid plans. If you\'re not satisfied, contact us within 7 days of purchase for a full refund.'
    }
  ];

  const formatPrice = (price) => {
    if (price === null) return 'Custom';
    return `₹${price.toLocaleString('en-IN')}`;
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/50">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center gap-3 group">
              <div className="w-10 h-10 rounded-xl bg-[#0F62FE] flex items-center justify-center">
                <Shield className="h-5 w-5 text-white" />
              </div>
              <span className="text-lg font-semibold text-slate-900 font-display">
                {settings.company_name || 'AssetVault'}
              </span>
            </Link>

            <div className="hidden md:flex items-center gap-8">
              <Link to="/features" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Features</Link>
              <Link to="/pricing" className="text-sm font-medium text-[#0F62FE]">Pricing</Link>
              <Link to="/page/contact-us" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Contact</Link>
            </div>

            <div className="hidden md:flex items-center gap-4">
              <Link to="/signup">
                <Button className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-5 py-2 rounded-lg font-medium">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </div>
        </nav>
      </header>

      {/* Hero */}
      <section className="pt-32 pb-16 md:pt-40 md:pb-20 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-6 font-display">
            Simple, transparent pricing
          </h1>
          <p className="text-lg text-slate-600 max-w-2xl mx-auto leading-relaxed mb-10">
            Start free, upgrade when you're ready. No hidden fees.
          </p>

          {/* Billing Toggle */}
          <div className="inline-flex items-center gap-4 p-1.5 bg-slate-100 rounded-xl">
            <button
              onClick={() => setBillingPeriod('monthly')}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
                billingPeriod === 'monthly'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Monthly
            </button>
            <button
              onClick={() => setBillingPeriod('yearly')}
              className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all flex items-center gap-2 ${
                billingPeriod === 'yearly'
                  ? 'bg-white text-slate-900 shadow-sm'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Yearly
              <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Save 17%</span>
            </button>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="pb-20 md:pb-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {plans.map((plan, index) => (
              <div 
                key={index}
                className={`relative p-8 rounded-2xl border transition-all duration-300 ${
                  plan.highlighted 
                    ? 'bg-slate-900 text-white border-slate-900 shadow-xl' 
                    : 'bg-white text-slate-900 border-slate-200 hover:border-slate-300 hover:shadow-lg'
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 py-1 bg-[#0F62FE] text-white text-xs font-medium rounded-full">
                    Most Popular
                  </div>
                )}
                
                <h3 className={`text-xl font-semibold mb-2 ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>
                  {plan.name}
                </h3>
                <p className={`text-sm mb-6 ${plan.highlighted ? 'text-slate-400' : 'text-slate-500'}`}>
                  {plan.description}
                </p>
                
                <div className="mb-8">
                  <span className="text-4xl font-bold">
                    {formatPrice(billingPeriod === 'yearly' ? plan.yearlyPrice : plan.monthlyPrice)}
                  </span>
                  {plan.monthlyPrice !== null && (
                    <span className={`text-sm ${plan.highlighted ? 'text-slate-400' : 'text-slate-500'}`}>
                      {billingPeriod === 'yearly' ? '/year' : plan.period}
                    </span>
                  )}
                </div>

                <div className="space-y-3 mb-8">
                  <div className="flex items-center justify-between text-sm">
                    <span className={plan.highlighted ? 'text-slate-400' : 'text-slate-600'}>Companies</span>
                    <span className={`font-medium ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>{plan.features.companies}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className={plan.highlighted ? 'text-slate-400' : 'text-slate-600'}>Devices</span>
                    <span className={`font-medium ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>{plan.features.devices}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className={plan.highlighted ? 'text-slate-400' : 'text-slate-600'}>Users</span>
                    <span className={`font-medium ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>{plan.features.users}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className={plan.highlighted ? 'text-slate-400' : 'text-slate-600'}>Tickets</span>
                    <span className={`font-medium ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>{plan.features.tickets}</span>
                  </div>
                </div>

                <Link to={plan.name === 'Enterprise' ? '/page/contact-us' : '/signup'}>
                  <Button 
                    className={`w-full py-3 h-auto rounded-lg font-medium transition-all ${
                      plan.highlighted 
                        ? 'bg-white text-slate-900 hover:bg-slate-100' 
                        : 'bg-slate-900 text-white hover:bg-slate-800'
                    }`}
                  >
                    {plan.cta}
                  </Button>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Feature Comparison */}
      <section className="py-16 md:py-20 bg-white border-t border-slate-100">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-900 text-center mb-4">
            Feature comparison
          </h2>
          <p className="text-slate-600 text-center mb-12">
            See what's included in each plan
          </p>

          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50">
                  <th className="text-left p-4 font-medium text-slate-700">Feature</th>
                  {plans.map((plan, i) => (
                    <th key={i} className={`p-4 text-center font-medium ${plan.highlighted ? 'text-slate-900' : 'text-slate-700'}`}>
                      {plan.name}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {Object.entries(featureLabels).map(([key, label], index) => (
                  <tr key={key} className="border-b border-slate-100 last:border-b-0">
                    <td className="p-4 text-sm text-slate-600">{label}</td>
                    {plans.map((plan, i) => (
                      <td key={i} className="p-4 text-center">
                        {typeof plan.features[key] === 'boolean' ? (
                          plan.features[key] ? (
                            <Check className="h-5 w-5 text-emerald-500 mx-auto" />
                          ) : (
                            <X className="h-5 w-5 text-slate-300 mx-auto" />
                          )
                        ) : (
                          <span className="text-sm text-slate-900">{plan.features[key]}</span>
                        )}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-16 md:py-20 bg-white border-t border-slate-100">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-2xl md:text-3xl font-bold text-slate-900 text-center mb-12">
            Frequently asked questions
          </h2>

          <div className="space-y-4">
            {faqs.map((faq, index) => (
              <div key={index} className="p-6 bg-white rounded-lg border border-slate-200">
                <h3 className="font-medium text-slate-900 mb-2">
                  {faq.question}
                </h3>
                <p className="text-slate-600 text-sm leading-relaxed">
                  {faq.answer}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-16 md:py-20 bg-slate-900">
        <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-2xl md:text-3xl font-bold text-white mb-4">
            Ready to get started?
          </h2>
          <p className="text-slate-400 mb-8">
            Start your free 14-day trial. No credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <Link to="/signup">
              <Button className="bg-white text-slate-900 hover:bg-slate-100 px-6 py-3 h-auto text-sm rounded-lg font-medium">
                Start Free Trial
              </Button>
            </Link>
            <Link to="/page/contact-us">
              <Button variant="outline" className="px-6 py-3 h-auto text-sm rounded-lg font-medium border border-slate-600 text-white hover:bg-slate-800">
                Contact Sales
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-[#0F62FE] flex items-center justify-center">
                <Shield className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold font-display">{settings.company_name || 'AssetVault'}</span>
            </div>
            <div className="flex gap-8 text-sm text-slate-400">
              <Link to="/" className="hover:text-white transition-colors">Home</Link>
              <Link to="/features" className="hover:text-white transition-colors">Features</Link>
              <Link to="/page/contact-us" className="hover:text-white transition-colors">Contact</Link>
              <Link to="/page/privacy-policy" className="hover:text-white transition-colors">Privacy</Link>
            </div>
            <p className="text-sm text-slate-500">
              © {new Date().getFullYear()} {settings.company_name || 'AssetVault'}
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default PricingPage;
