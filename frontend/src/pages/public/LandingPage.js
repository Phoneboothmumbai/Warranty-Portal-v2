import { useState } from 'react';
import { Link } from 'react-router-dom';
import { 
  Shield, ArrowRight, Check, 
  HardDrive, Ticket, FileText, BarChart3, 
  QrCode, Building2,
  Menu, X, Play, ArrowUpRight
} from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';
import { Button } from '../../components/ui/button';

const LandingPage = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { settings } = useSettings();

  const features = [
    {
      icon: HardDrive,
      title: 'Asset Management',
      description: 'Track all IT assets with complete lifecycle visibility. From procurement to retirement.',
      color: 'bg-blue-500'
    },
    {
      icon: Shield,
      title: 'Warranty Tracking',
      description: 'Never miss a warranty claim. Get alerts before expiry and maximize coverage.',
      color: 'bg-emerald-500'
    },
    {
      icon: Ticket,
      title: 'Service Tickets',
      description: 'Enterprise ticketing with SLA management, auto-routing, and email integration.',
      color: 'bg-purple-500'
    },
    {
      icon: FileText,
      title: 'AMC Contracts',
      description: 'Manage service contracts with usage tracking, renewal alerts, and compliance.',
      color: 'bg-amber-500'
    },
    {
      icon: QrCode,
      title: 'QR Code Labels',
      description: 'Generate QR codes for instant asset lookup. Scan to raise tickets or view details.',
      color: 'bg-rose-500'
    },
    {
      icon: BarChart3,
      title: 'Analytics & Reports',
      description: 'Real-time dashboards, expiry forecasts, and exportable PDF reports.',
      color: 'bg-cyan-500'
    }
  ];

  const pricingPlans = [
    {
      name: 'Free Trial',
      price: '₹0',
      period: '14 days',
      description: 'Try all features risk-free',
      features: ['Up to 2 companies', '50 devices', '5 users', 'Basic ticketing', 'Email support'],
      cta: 'Start Free Trial',
      highlighted: false
    },
    {
      name: 'Starter',
      price: '₹2,999',
      period: '/month',
      description: 'For growing businesses',
      features: ['Up to 5 companies', '100 devices', '10 users', 'SLA management', 'Email integration', 'API access'],
      cta: 'Get Started',
      highlighted: false
    },
    {
      name: 'Professional',
      price: '₹7,999',
      period: '/month',
      description: 'For established enterprises',
      features: ['Up to 25 companies', '500 devices', '50 users', 'Custom forms', 'Priority support', 'SSO integration', 'Advanced analytics'],
      cta: 'Get Started',
      highlighted: true
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large organizations',
      features: ['Unlimited everything', 'Dedicated support', 'On-premise option', 'Custom integrations', 'SLA guarantee', 'Training included'],
      cta: 'Contact Sales',
      highlighted: false
    }
  ];

  const stats = [
    { value: '10,000+', label: 'Assets Tracked' },
    { value: '500+', label: 'Companies' },
    { value: '99.9%', label: 'Uptime' },
    { value: '24/7', label: 'Support' }
  ];

  return (
    <div className="min-h-screen bg-white" data-testid="landing-page">
      {/* Navigation */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/50">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <Link to="/" className="flex items-center gap-3 group" data-testid="nav-logo">
              <div className="w-10 h-10 rounded-xl bg-[#0F62FE] flex items-center justify-center group-hover:scale-105 transition-transform">
                {(settings.logo_base64 || settings.logo_url) ? (
                  <img src={settings.logo_base64 || settings.logo_url} alt="Logo" className="h-6 w-6" />
                ) : (
                  <Shield className="h-5 w-5 text-white" />
                )}
              </div>
              <span className="text-lg font-semibold text-slate-900 font-display">
                {settings.company_name || 'AssetVault'}
              </span>
            </Link>

            {/* Desktop Navigation */}
            <div className="hidden md:flex items-center gap-8">
              <Link to="/features" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors" data-testid="nav-features">
                Features
              </Link>
              <Link to="/pricing" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors" data-testid="nav-pricing">
                Pricing
              </Link>
              <Link to="/page/contact-us" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                Contact
              </Link>
              <Link to="/support" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">
                Support Portal
              </Link>
            </div>

            {/* Desktop CTA */}
            <div className="hidden md:flex items-center gap-4">
              <Link to="/company/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors" data-testid="nav-login">
                Sign In
              </Link>
              <Link to="/signup">
                <Button className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-5 py-2 rounded-lg font-medium transition-all hover:-translate-y-0.5 hover:shadow-lg" data-testid="nav-get-started">
                  Get Started
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>

            {/* Mobile Menu Button */}
            <button 
              className="md:hidden p-2 text-slate-600 hover:text-slate-900"
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              data-testid="mobile-menu-btn"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>

          {/* Mobile Menu */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t border-slate-100" data-testid="mobile-menu">
              <div className="flex flex-col gap-4">
                <Link to="/features" className="text-sm font-medium text-slate-600 hover:text-slate-900 py-2">Features</Link>
                <Link to="/pricing" className="text-sm font-medium text-slate-600 hover:text-slate-900 py-2">Pricing</Link>
                <Link to="/page/contact-us" className="text-sm font-medium text-slate-600 hover:text-slate-900 py-2">Contact</Link>
                <Link to="/support" className="text-sm font-medium text-slate-600 hover:text-slate-900 py-2">Support Portal</Link>
                <div className="flex flex-col gap-3 pt-4 border-t border-slate-100">
                  <Link to="/company/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 py-2">Sign In</Link>
                  <Link to="/signup">
                    <Button className="w-full bg-[#0F62FE] hover:bg-[#0043CE] text-white">Get Started</Button>
                  </Link>
                </div>
              </div>
            </div>
          )}
        </nav>
      </header>

      {/* Hero Section */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-32 relative overflow-hidden" data-testid="hero-section">
        {/* Background Elements */}
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-gradient-to-br from-blue-50 to-transparent rounded-full blur-3xl opacity-60 -translate-y-1/2 translate-x-1/2" />
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-gradient-to-tr from-slate-100 to-transparent rounded-full blur-3xl opacity-40 translate-y-1/2 -translate-x-1/2" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="max-w-4xl mx-auto text-center">
            {/* Badge */}
            <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-full mb-8">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
              </span>
              <span className="text-sm font-medium text-blue-700">Enterprise Asset Management Platform</span>
            </div>

            {/* Heading */}
            <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-slate-900 tracking-tight leading-[1.1] mb-6 font-display" data-testid="hero-heading">
              Track Every Asset.
              <br />
              <span className="text-[#0F62FE]">Never Miss a Warranty.</span>
            </h1>

            {/* Subheading */}
            <p className="text-lg md:text-xl text-slate-600 mb-10 max-w-2xl mx-auto leading-relaxed">
              The complete platform for IT asset tracking, warranty management, service tickets, and AMC contracts. Built for enterprises that demand reliability.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-16">
              <Link to="/signup">
                <Button className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-8 py-4 h-auto text-base rounded-xl font-semibold transition-all hover:-translate-y-1 hover:shadow-xl shadow-lg shadow-blue-500/25" data-testid="hero-cta-primary">
                  Start Free Trial
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Link to="/features">
                <Button variant="outline" className="px-8 py-4 h-auto text-base rounded-xl font-semibold border-2 border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-all" data-testid="hero-cta-secondary">
                  <Play className="mr-2 h-5 w-5 text-[#0F62FE]" />
                  See How It Works
                </Button>
              </Link>
            </div>

            {/* Stats */}
            <div className="flex flex-wrap justify-center gap-12">
              {stats.map((stat, index) => (
                <div key={index} className="text-center">
                  <div className="text-3xl md:text-4xl font-bold text-slate-900 font-display">{stat.value}</div>
                  <div className="text-sm text-slate-500">{stat.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Dashboard Preview */}
          <div className="mt-20 relative">
            <div className="bg-slate-900 rounded-2xl p-2 shadow-2xl shadow-slate-300/50 max-w-5xl mx-auto">
              <div className="bg-slate-800 rounded-xl p-6">
                <div className="flex items-center gap-2 mb-4">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="ml-4 text-sm text-slate-400 font-mono">dashboard.assetvault.io</span>
                </div>
                <div className="grid grid-cols-4 gap-4">
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-white font-display">847</div>
                    <div className="text-xs text-slate-400">Total Assets</div>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-emerald-400 font-display">92%</div>
                    <div className="text-xs text-slate-400">Under Warranty</div>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-amber-400 font-display">23</div>
                    <div className="text-xs text-slate-400">Expiring Soon</div>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-400 font-display">12</div>
                    <div className="text-xs text-slate-400">Active Tickets</div>
                  </div>
                </div>
              </div>
            </div>
            {/* Decorative Elements */}
            <div className="absolute -top-4 -left-4 w-20 h-20 bg-blue-100 rounded-2xl rotate-12 -z-10"></div>
            <div className="absolute -bottom-4 -right-4 w-24 h-24 bg-emerald-100 rounded-2xl -rotate-12 -z-10"></div>
          </div>
        </div>
      </section>

      {/* Trusted By Section */}
      <section className="py-16 border-y border-slate-100 bg-slate-50/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm font-medium text-slate-500 mb-8 uppercase tracking-widest">
            Trusted by leading enterprises
          </p>
          <div className="flex flex-wrap justify-center items-center gap-12 opacity-60">
            {[1, 2, 3, 4, 5].map((i) => (
              <div key={i} className="flex items-center gap-2 text-slate-400">
                <Building2 className="h-8 w-8" />
                <span className="text-lg font-semibold">Company {i}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-24 md:py-32" id="features" data-testid="features-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Section Header */}
          <div className="text-center max-w-3xl mx-auto mb-20">
            <span className="text-sm font-mono uppercase tracking-widest text-[#0F62FE] mb-4 block">
              Features
            </span>
            <h2 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-6 font-display">
              Everything you need to manage IT assets
            </h2>
            <p className="text-lg text-slate-600 leading-relaxed">
              From warranty tracking to service management, get complete visibility and control over your entire asset portfolio.
            </p>
          </div>

          {/* Features Grid - Bento Style */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {features.map((feature, index) => (
              <div 
                key={index}
                className="group p-8 bg-white rounded-2xl border border-slate-100 hover:border-slate-200 hover:shadow-xl hover:shadow-slate-100/50 transition-all duration-300 cursor-pointer"
                data-testid={`feature-card-${index}`}
              >
                <div className={`w-14 h-14 ${feature.color} rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                  <feature.icon className="h-7 w-7 text-white" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-3 font-display">{feature.title}</h3>
                <p className="text-slate-600 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>

          {/* View All Features CTA */}
          <div className="text-center mt-16">
            <Link to="/features">
              <Button variant="outline" className="px-8 py-4 h-auto text-base rounded-xl font-semibold border-2 border-slate-200 hover:border-[#0F62FE] hover:text-[#0F62FE] transition-all">
                View All Features
                <ArrowUpRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* How It Works Section */}
      <section className="py-24 md:py-32 bg-slate-900 text-white" data-testid="how-it-works-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <span className="text-sm font-mono uppercase tracking-widest text-blue-400 mb-4 block">
              How It Works
            </span>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tight mb-6 font-display">
              Get started in minutes
            </h2>
            <p className="text-lg text-slate-400 leading-relaxed">
              Simple onboarding process to get your team up and running quickly.
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Sign Up', description: 'Create your organization account and invite team members.' },
              { step: '02', title: 'Import Assets', description: 'Bulk upload devices via Excel or add them manually.' },
              { step: '03', title: 'Start Tracking', description: 'Monitor warranties, manage tickets, and generate reports.' }
            ].map((item, index) => (
              <div key={index} className="relative">
                <div className="text-7xl font-bold text-slate-800 font-display mb-4">{item.step}</div>
                <h3 className="text-2xl font-semibold mb-3 font-display">{item.title}</h3>
                <p className="text-slate-400 leading-relaxed">{item.description}</p>
                {index < 2 && (
                  <div className="hidden md:block absolute top-8 right-0 w-16 h-0.5 bg-gradient-to-r from-slate-700 to-transparent"></div>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section className="py-24 md:py-32" id="pricing" data-testid="pricing-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto mb-20">
            <span className="text-sm font-mono uppercase tracking-widest text-[#0F62FE] mb-4 block">
              Pricing
            </span>
            <h2 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-6 font-display">
              Simple, transparent pricing
            </h2>
            <p className="text-lg text-slate-600 leading-relaxed">
              Start free, upgrade when you need. No hidden fees.
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {pricingPlans.map((plan, index) => (
              <div 
                key={index}
                className={`relative p-8 rounded-2xl border-2 transition-all duration-300 ${
                  plan.highlighted 
                    ? 'bg-[#0F62FE] text-white border-[#0F62FE] shadow-2xl shadow-blue-500/30 scale-105 z-10' 
                    : 'bg-white text-slate-900 border-slate-100 hover:border-slate-200 hover:shadow-xl'
                }`}
                data-testid={`pricing-card-${plan.name.toLowerCase().replace(' ', '-')}`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 bg-amber-400 text-slate-900 text-xs font-bold rounded-full uppercase tracking-wide">
                    Most Popular
                  </div>
                )}
                
                <h3 className={`text-xl font-semibold mb-2 font-display ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>
                  {plan.name}
                </h3>
                <p className={`text-sm mb-6 ${plan.highlighted ? 'text-blue-100' : 'text-slate-500'}`}>
                  {plan.description}
                </p>
                
                <div className="mb-8">
                  <span className="text-4xl font-bold font-display">{plan.price}</span>
                  <span className={`text-sm ${plan.highlighted ? 'text-blue-100' : 'text-slate-500'}`}>{plan.period}</span>
                </div>

                <ul className="space-y-4 mb-8">
                  {plan.features.map((feature, fIndex) => (
                    <li key={fIndex} className="flex items-center gap-3 text-sm">
                      <Check className={`h-5 w-5 flex-shrink-0 ${plan.highlighted ? 'text-blue-200' : 'text-emerald-500'}`} />
                      <span className={plan.highlighted ? 'text-blue-50' : 'text-slate-600'}>{feature}</span>
                    </li>
                  ))}
                </ul>

                <Link to={plan.name === 'Enterprise' ? '/page/contact-us' : '/signup'}>
                  <Button 
                    className={`w-full py-3 h-auto rounded-xl font-semibold transition-all hover:-translate-y-0.5 ${
                      plan.highlighted 
                        ? 'bg-white text-[#0F62FE] hover:bg-blue-50' 
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

      {/* CTA Section */}
      <section className="py-24 md:py-32 bg-gradient-to-br from-slate-900 to-slate-800" data-testid="cta-section">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold text-white tracking-tight mb-6 font-display">
            Ready to transform your asset management?
          </h2>
          <p className="text-lg text-slate-400 mb-10 max-w-2xl mx-auto">
            Join hundreds of enterprises already using our platform. Start your free trial today—no credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup">
              <Button className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-10 py-4 h-auto text-lg rounded-xl font-semibold transition-all hover:-translate-y-1 hover:shadow-xl shadow-lg shadow-blue-500/25">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/page/contact-us">
              <Button variant="outline" className="px-10 py-4 h-auto text-lg rounded-xl font-semibold border-2 border-slate-600 text-white hover:bg-slate-800 transition-all">
                Talk to Sales
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-20 border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-12 mb-16">
            {/* Brand */}
            <div className="lg:col-span-2">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-xl bg-[#0F62FE] flex items-center justify-center">
                  <Shield className="h-5 w-5 text-white" />
                </div>
                <span className="text-xl font-semibold font-display">{settings.company_name || 'AssetVault'}</span>
              </div>
              <p className="text-slate-400 leading-relaxed mb-6 max-w-sm">
                Enterprise-grade warranty and asset tracking platform. Built for modern IT teams.
              </p>
              <div className="flex gap-4">
                <a href="#" className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-slate-700 transition-colors">
                  <span className="sr-only">Twitter</span>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"/></svg>
                </a>
                <a href="#" className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-slate-700 transition-colors">
                  <span className="sr-only">LinkedIn</span>
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/></svg>
                </a>
              </div>
            </div>

            {/* Product */}
            <div>
              <h4 className="font-semibold mb-4 font-display">Product</h4>
              <ul className="space-y-3 text-slate-400">
                <li><Link to="/features" className="hover:text-white transition-colors">Features</Link></li>
                <li><Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link></li>
                <li><Link to="/signup" className="hover:text-white transition-colors">Get Started</Link></li>
                <li><Link to="/support" className="hover:text-white transition-colors">Support Portal</Link></li>
              </ul>
            </div>

            {/* Company */}
            <div>
              <h4 className="font-semibold mb-4 font-display">Company</h4>
              <ul className="space-y-3 text-slate-400">
                <li><Link to="/page/about" className="hover:text-white transition-colors">About</Link></li>
                <li><Link to="/page/contact-us" className="hover:text-white transition-colors">Contact</Link></li>
                <li><Link to="/admin/login" className="hover:text-white transition-colors">Admin Portal</Link></li>
                <li><Link to="/company/login" className="hover:text-white transition-colors">Company Login</Link></li>
              </ul>
            </div>

            {/* Legal */}
            <div>
              <h4 className="font-semibold mb-4 font-display">Legal</h4>
              <ul className="space-y-3 text-slate-400">
                <li><Link to="/page/privacy-policy" className="hover:text-white transition-colors">Privacy Policy</Link></li>
                <li><Link to="/page/terms-of-service" className="hover:text-white transition-colors">Terms of Service</Link></li>
                <li><Link to="/page/refund-policy" className="hover:text-white transition-colors">Refund Policy</Link></li>
                <li><Link to="/page/disclaimer" className="hover:text-white transition-colors">Disclaimer</Link></li>
              </ul>
            </div>
          </div>

          <div className="pt-8 border-t border-slate-800 text-center text-slate-500 text-sm">
            © {new Date().getFullYear()} {settings.company_name || 'AssetVault'}. All rights reserved.
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
