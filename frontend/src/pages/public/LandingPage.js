import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { 
  ArrowRight, Check, 
  Ticket, FileText, BarChart3, 
  QrCode, Layers, Shield,
  Zap, Clock, Users, Server,
  ChevronRight, ArrowUpRight
} from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';
import { Button } from '../../components/ui/button';
import PublicHeader from '../../components/public/PublicHeader';
import PublicFooter from '../../components/public/PublicFooter';

/* ─── Animated counter hook ─── */
function useCountUp(end, duration = 2000, startOnView = true) {
  const [count, setCount] = useState(0);
  const ref = useRef(null);
  const started = useRef(false);

  useEffect(() => {
    if (!startOnView) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting && !started.current) {
          started.current = true;
          const startTime = performance.now();
          const numEnd = parseInt(String(end).replace(/[^0-9]/g, ''), 10);
          const step = (now) => {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const eased = 1 - Math.pow(1 - progress, 3);
            setCount(Math.floor(eased * numEnd));
            if (progress < 1) requestAnimationFrame(step);
          };
          requestAnimationFrame(step);
        }
      },
      { threshold: 0.3 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [end, duration, startOnView]);

  return { count, ref };
}

/* ─── Fade-in on scroll component ─── */
function FadeIn({ children, className = '', delay = 0 }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold: 0.1 }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  return (
    <div
      ref={ref}
      className={className}
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(24px)',
        transition: `opacity 0.7s ease ${delay}ms, transform 0.7s ease ${delay}ms`,
      }}
    >
      {children}
    </div>
  );
}

/* ─── Image constants ─── */
const IMAGES = {
  serverRoom: 'https://images.pexels.com/photos/5480781/pexels-photo-5480781.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940',
  team: 'https://images.unsplash.com/photo-1758518727477-3885839edee7?crop=entropy&cs=srgb&fm=jpg&q=85',
  analytics: 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?crop=entropy&cs=srgb&fm=jpg&q=85',
  techBlue: 'https://images.unsplash.com/photo-1771773490670-7376a45c0e96?crop=entropy&cs=srgb&fm=jpg&q=85',
  workspace: 'https://images.unsplash.com/photo-1627929994715-997356049549?crop=entropy&cs=srgb&fm=jpg&q=85',
  engineer: 'https://images.unsplash.com/photo-1768633647910-7e6fb53e5b0f?crop=entropy&cs=srgb&fm=jpg&q=85',
};

const LandingPage = () => {
  const { settings } = useSettings();

  const stat1 = useCountUp(5000, 2200);
  const stat2 = useCountUp(30, 1800);

  const features = [
    {
      icon: Layers,
      title: 'Multi-Client Management',
      description: 'Manage all your clients\' IT assets from a single dashboard. Perfect for MSPs handling multiple organizations.',
      color: 'bg-[#0F62FE]',
    },
    {
      icon: Shield,
      title: 'Warranty Tracking',
      description: 'Never miss a warranty claim. Get alerts before expiry and maximize coverage for all clients.',
      color: 'bg-emerald-500',
    },
    {
      icon: Ticket,
      title: 'Service Desk',
      description: 'Enterprise ticketing with SLA management, auto-routing, email-to-ticket, and client portals.',
      color: 'bg-violet-500',
    },
    {
      icon: FileText,
      title: 'AMC & Contracts',
      description: 'Track service contracts, usage limits, renewals, and billing across all your clients.',
      color: 'bg-amber-500',
    },
    {
      icon: QrCode,
      title: 'QR Asset Labels',
      description: 'Generate QR codes for instant asset lookup. Engineers scan to view history or raise tickets.',
      color: 'bg-rose-500',
    },
    {
      icon: BarChart3,
      title: 'Client Reports',
      description: 'Generate professional reports for clients. Asset health, SLA compliance, and service summaries.',
      color: 'bg-cyan-500',
    },
  ];

  const pricingPlans = [
    {
      name: 'Free Trial',
      price: '₹0',
      period: '14 days',
      description: 'Try all features risk-free',
      features: ['Up to 2 clients', '50 devices', '5 technicians', 'Basic ticketing', 'Email support'],
      cta: 'Start Free Trial',
      highlighted: false,
    },
    {
      name: 'Starter',
      price: '₹2,999',
      period: '/month',
      description: 'For small IT teams',
      features: ['Up to 5 clients', '100 devices', '10 technicians', 'SLA management', 'Email integration', 'API access'],
      cta: 'Get Started',
      highlighted: false,
    },
    {
      name: 'Professional',
      price: '₹7,999',
      period: '/month',
      description: 'For growing MSPs',
      features: ['Up to 25 clients', '500 devices', '50 technicians', 'Custom forms', 'Priority support', 'White-label reports', 'Advanced analytics'],
      cta: 'Get Started',
      highlighted: true,
    },
    {
      name: 'Enterprise',
      price: 'Custom',
      period: '',
      description: 'For large MSPs',
      features: ['Unlimited clients', 'Unlimited devices', 'Dedicated support', 'Custom integrations', 'SLA guarantee', 'On-site training'],
      cta: 'Contact Sales',
      highlighted: false,
    },
  ];

  return (
    <div className="min-h-screen bg-white" data-testid="landing-page">
      <PublicHeader />

      {/* ════════════════════ HERO ════════════════════ */}
      <section className="relative pt-28 pb-0 md:pt-36 lg:pt-40 overflow-hidden" data-testid="hero-section">
        {/* subtle grid background */}
        <div className="absolute inset-0 opacity-[0.03]" style={{
          backgroundImage: 'linear-gradient(#0F62FE 1px, transparent 1px), linear-gradient(90deg, #0F62FE 1px, transparent 1px)',
          backgroundSize: '64px 64px',
        }} />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="grid lg:grid-cols-12 gap-12 lg:gap-8 items-center">
            {/* LEFT — Copy */}
            <div className="lg:col-span-6 xl:col-span-7">
              <FadeIn>
                <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-[#0F62FE]/5 border border-[#0F62FE]/10 rounded-md mb-8">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#0F62FE] opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#0F62FE]" />
                  </span>
                  <span className="text-sm font-medium text-[#0F62FE] font-mono tracking-wide">Trusted by 30+ IT Teams</span>
                </div>
              </FadeIn>

              <FadeIn delay={80}>
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 tracking-tight leading-[1.08] mb-6 font-display" data-testid="hero-heading">
                  After-Sales Service.
                  <br />
                  <span className="bg-gradient-to-r from-[#0F62FE] to-cyan-500 bg-clip-text text-transparent">
                    Before the Competition.
                  </span>
                </h1>
              </FadeIn>

              <FadeIn delay={160}>
                <p className="text-base lg:text-lg text-slate-600 mb-10 max-w-lg leading-relaxed">
                  The complete IT service management platform for MSPs. Track assets, warranties, service tickets, and AMC contracts — all from one powerful dashboard.
                </p>
              </FadeIn>

              <FadeIn delay={240}>
                <div className="flex flex-col sm:flex-row gap-3 mb-12">
                  <Link to="/signup">
                    <Button
                      className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-7 py-3.5 h-auto text-sm rounded-lg font-semibold transition-transform hover:-translate-y-0.5 shadow-lg shadow-blue-500/20"
                      data-testid="hero-cta-primary"
                    >
                      Start Free Trial
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                  <Link to="/features">
                    <Button
                      variant="outline"
                      className="px-7 py-3.5 h-auto text-sm rounded-lg font-semibold border border-slate-200 hover:border-slate-300 hover:bg-slate-50 transition-transform hover:-translate-y-0.5"
                      data-testid="hero-cta-secondary"
                    >
                      See How It Works
                      <ChevronRight className="ml-1 h-4 w-4" />
                    </Button>
                  </Link>
                </div>
              </FadeIn>

              {/* Trust strip */}
              <FadeIn delay={320}>
                <div className="flex items-center gap-6 text-sm text-slate-500">
                  <div className="flex items-center gap-1.5">
                    <Check className="h-4 w-4 text-emerald-500" />
                    <span>No credit card required</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Check className="h-4 w-4 text-emerald-500" />
                    <span>14-day free trial</span>
                  </div>
                  <div className="hidden sm:flex items-center gap-1.5">
                    <Check className="h-4 w-4 text-emerald-500" />
                    <span>SOC 2 compliant</span>
                  </div>
                </div>
              </FadeIn>
            </div>

            {/* RIGHT — Hero Visual */}
            <div className="lg:col-span-6 xl:col-span-5 relative">
              <FadeIn delay={200}>
                <div className="relative">
                  {/* Main dashboard card */}
                  <div className="bg-[#0B1221] rounded-2xl p-1.5 shadow-2xl shadow-slate-900/20">
                    <div className="rounded-xl overflow-hidden">
                      <img
                        src={IMAGES.analytics}
                        alt="Analytics dashboard"
                        className="w-full h-auto object-cover"
                        loading="eager"
                      />
                    </div>
                  </div>

                  {/* Floating stat card — top-left */}
                  <div className="absolute -top-4 -left-6 bg-white rounded-xl shadow-xl shadow-slate-200/60 border border-slate-100 p-4 hidden lg:block" style={{ minWidth: 160 }}>
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-8 h-8 rounded-lg bg-emerald-50 flex items-center justify-center">
                        <Zap className="h-4 w-4 text-emerald-600" />
                      </div>
                      <span className="text-xs font-medium text-slate-500">Uptime</span>
                    </div>
                    <span className="text-2xl font-bold text-slate-900 font-display">99.9%</span>
                  </div>

                  {/* Floating stat card — bottom-right */}
                  <div className="absolute -bottom-4 -right-4 bg-white rounded-xl shadow-xl shadow-slate-200/60 border border-slate-100 p-4 hidden lg:block" style={{ minWidth: 170 }}>
                    <div className="flex items-center gap-3 mb-2">
                      <div className="w-8 h-8 rounded-lg bg-blue-50 flex items-center justify-center">
                        <Clock className="h-4 w-4 text-[#0F62FE]" />
                      </div>
                      <span className="text-xs font-medium text-slate-500">Avg Response</span>
                    </div>
                    <span className="text-2xl font-bold text-slate-900 font-display">&lt; 2 hr</span>
                  </div>
                </div>
              </FadeIn>
            </div>
          </div>
        </div>

        {/* ─── Stats Bar ─── */}
        <div className="mt-20 lg:mt-28 bg-[#0B1221]" data-testid="stats-bar">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-2 md:grid-cols-4 divide-x divide-slate-700/50">
              <div className="py-10 md:py-14 px-6 text-center" ref={stat1.ref}>
                <div className="text-3xl md:text-4xl font-bold text-white font-display">{stat1.count.toLocaleString()}+</div>
                <div className="text-sm text-slate-400 mt-1">Assets Managed</div>
              </div>
              <div className="py-10 md:py-14 px-6 text-center" ref={stat2.ref}>
                <div className="text-3xl md:text-4xl font-bold text-white font-display">{stat2.count}+</div>
                <div className="text-sm text-slate-400 mt-1">MSPs & IT Teams</div>
              </div>
              <div className="py-10 md:py-14 px-6 text-center">
                <div className="text-3xl md:text-4xl font-bold text-white font-display">99.9%</div>
                <div className="text-sm text-slate-400 mt-1">Uptime</div>
              </div>
              <div className="py-10 md:py-14 px-6 text-center">
                <div className="text-3xl md:text-4xl font-bold text-cyan-400 font-display">&lt; 2hr</div>
                <div className="text-sm text-slate-400 mt-1">Avg Response</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ════════════════════ TRUSTED BY ════════════════════ */}
      <section className="py-16 bg-slate-50/70 border-b border-slate-100" data-testid="trusted-by-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-xs font-mono uppercase tracking-[0.2em] text-slate-400 mb-10">
            Trusted by forward-thinking IT teams
          </p>
          <div className="flex flex-wrap justify-center items-center gap-x-14 gap-y-6">
            {['TechServe Solutions', 'CloudIT Partners', 'SecureNet MSP', 'ProSupport IT', 'InfraCare Systems', 'NetOps Global'].map((name, i) => (
              <div key={i} className="flex items-center gap-2.5 opacity-40 hover:opacity-80 transition-opacity duration-300 cursor-default">
                <div className="w-9 h-9 rounded-lg bg-slate-200 flex items-center justify-center">
                  <Server className="h-4 w-4 text-slate-500" />
                </div>
                <span className="text-sm font-semibold text-slate-600">{name}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════ FEATURES — BENTO GRID ════════════════════ */}
      <section className="py-24 md:py-32" id="features" data-testid="features-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <FadeIn>
            <div className="max-w-2xl mb-16">
              <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#0F62FE] mb-4 block">
                Platform
              </span>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight mb-5 font-display">
                Everything your IT team needs. Nothing it doesn't.
              </h2>
              <p className="text-base text-slate-600 leading-relaxed">
                From asset tracking to SLA compliance — one platform that replaces the spreadsheets, emails, and guesswork.
              </p>
            </div>
          </FadeIn>

          {/* Bento Grid */}
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {/* Card 1 — Large with image */}
            <FadeIn className="lg:col-span-2 lg:row-span-2" delay={0}>
              <div
                className="group relative h-full rounded-2xl overflow-hidden border border-slate-100 hover:border-slate-200 hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-300 cursor-pointer"
                data-testid="feature-card-0"
              >
                <div className="absolute inset-0">
                  <img src={IMAGES.serverRoom} alt="Data center" className="w-full h-full object-cover" loading="lazy" />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/70 to-slate-900/20" />
                </div>
                <div className="relative h-full flex flex-col justify-end p-8 md:p-10 min-h-[360px] lg:min-h-[440px]">
                  <div className="w-12 h-12 bg-[#0F62FE] rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
                    <Layers className="h-6 w-6 text-white" />
                  </div>
                  <h3 className="text-2xl font-semibold text-white mb-3 font-display">Multi-Client Management</h3>
                  <p className="text-slate-300 leading-relaxed max-w-md">
                    Manage all your clients' IT assets from a single dashboard. Perfect for MSPs handling multiple organizations with hundreds of devices.
                  </p>
                </div>
              </div>
            </FadeIn>

            {/* Card 2 — icon card */}
            <FadeIn delay={100}>
              <div
                className="group p-7 bg-white rounded-2xl border border-slate-100 hover:border-slate-200 hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-300 cursor-pointer h-full"
                data-testid="feature-card-1"
              >
                <div className="w-12 h-12 bg-emerald-500 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
                  <Shield className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2 font-display">Warranty Tracking</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Get alerts before expiry and maximize warranty coverage for every client.
                </p>
              </div>
            </FadeIn>

            {/* Card 3 — icon card */}
            <FadeIn delay={200}>
              <div
                className="group p-7 bg-white rounded-2xl border border-slate-100 hover:border-slate-200 hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-300 cursor-pointer h-full"
                data-testid="feature-card-2"
              >
                <div className="w-12 h-12 bg-violet-500 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
                  <Ticket className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2 font-display">Service Desk</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Enterprise ticketing with SLA management, auto-routing, and email-to-ticket conversion.
                </p>
              </div>
            </FadeIn>

            {/* Card 4 — image card */}
            <FadeIn delay={150}>
              <div
                className="group relative rounded-2xl overflow-hidden border border-slate-100 hover:border-slate-200 hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-300 cursor-pointer h-full min-h-[220px]"
                data-testid="feature-card-3"
              >
                <div className="absolute inset-0">
                  <img src={IMAGES.engineer} alt="IT technicians" className="w-full h-full object-cover" loading="lazy" />
                  <div className="absolute inset-0 bg-gradient-to-t from-slate-900 via-slate-900/60 to-transparent" />
                </div>
                <div className="relative h-full flex flex-col justify-end p-7">
                  <div className="w-10 h-10 bg-amber-500 rounded-lg flex items-center justify-center mb-3 group-hover:scale-110 transition-transform duration-300">
                    <FileText className="h-5 w-5 text-white" />
                  </div>
                  <h3 className="text-lg font-semibold text-white mb-1 font-display">AMC & Contracts</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">Track service contracts, renewals, and billing.</p>
                </div>
              </div>
            </FadeIn>

            {/* Card 5 — icon card */}
            <FadeIn delay={250}>
              <div
                className="group p-7 bg-white rounded-2xl border border-slate-100 hover:border-slate-200 hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-300 cursor-pointer h-full"
                data-testid="feature-card-4"
              >
                <div className="w-12 h-12 bg-rose-500 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
                  <QrCode className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2 font-display">QR Asset Labels</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Generate QR codes for instant asset lookup. Scan to view history or raise tickets.
                </p>
              </div>
            </FadeIn>

            {/* Card 6 — icon card */}
            <FadeIn delay={300}>
              <div
                className="group p-7 bg-white rounded-2xl border border-slate-100 hover:border-slate-200 hover:shadow-xl hover:shadow-slate-100/60 transition-shadow duration-300 cursor-pointer h-full"
                data-testid="feature-card-5"
              >
                <div className="w-12 h-12 bg-cyan-500 rounded-xl flex items-center justify-center mb-5 group-hover:scale-110 transition-transform duration-300">
                  <BarChart3 className="h-6 w-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2 font-display">Client Reports</h3>
                <p className="text-sm text-slate-600 leading-relaxed">
                  Professional reports: asset health, SLA compliance, and service summaries.
                </p>
              </div>
            </FadeIn>
          </div>

          <FadeIn delay={350}>
            <div className="mt-12">
              <Link to="/features">
                <Button variant="outline" className="px-7 py-3.5 h-auto text-sm rounded-lg font-semibold border border-slate-200 hover:border-[#0F62FE] hover:text-[#0F62FE] transition-colors">
                  Explore All Features
                  <ArrowUpRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </FadeIn>
        </div>
      </section>

      {/* ════════════════════ FULL-WIDTH IMAGE BREAK ════════════════════ */}
      <section className="relative h-[340px] md:h-[400px] overflow-hidden" data-testid="image-break-section">
        <img
          src={IMAGES.team}
          alt="Professional IT team"
          className="absolute inset-0 w-full h-full object-cover"
          loading="lazy"
        />
        <div className="absolute inset-0 bg-[#0B1221]/75" />
        <div className="relative h-full flex items-center">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full">
            <FadeIn>
              <div className="max-w-2xl">
                <blockquote className="text-xl md:text-2xl font-medium text-white leading-relaxed mb-6 font-display">
                  "aftersales.support replaced 4 different tools for us. Our response time dropped from 6 hours to under 90 minutes."
                </blockquote>
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-[#0F62FE] flex items-center justify-center text-white font-bold text-sm">RK</div>
                  <div>
                    <div className="text-sm font-semibold text-white">Rahul Kapoor</div>
                    <div className="text-xs text-slate-400">Head of IT, TechServe Solutions</div>
                  </div>
                </div>
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      {/* ════════════════════ HOW IT WORKS ════════════════════ */}
      <section className="py-24 md:py-32 bg-slate-50/50" data-testid="how-it-works-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <FadeIn>
            <div className="max-w-2xl mb-16">
              <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#0F62FE] mb-4 block">
                Getting started
              </span>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight mb-5 font-display">
                Up and running in minutes
              </h2>
              <p className="text-base text-slate-600 leading-relaxed">
                No complex migrations. No week-long onboarding. Just sign up and start managing.
              </p>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              { step: '01', title: 'Create Your Workspace', description: 'Sign up, name your organization, and invite your team. Takes under 2 minutes.', icon: Users },
              { step: '02', title: 'Import Your Assets', description: 'Bulk upload devices via Excel or add them one by one. We handle the rest.', icon: Server },
              { step: '03', title: 'Start Delivering', description: 'Monitor warranties, manage tickets, track SLAs, and generate client reports.', icon: Zap },
            ].map((item, index) => (
              <FadeIn key={index} delay={index * 120}>
                <div className="relative group">
                  <div className="text-6xl font-bold text-slate-100 font-display mb-4 group-hover:text-[#0F62FE]/10 transition-colors duration-300">{item.step}</div>
                  <div className="w-11 h-11 rounded-lg bg-[#0F62FE]/5 border border-[#0F62FE]/10 flex items-center justify-center mb-4">
                    <item.icon className="h-5 w-5 text-[#0F62FE]" />
                  </div>
                  <h3 className="text-xl font-semibold text-slate-900 mb-2 font-display">{item.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed">{item.description}</p>
                  {index < 2 && (
                    <div className="hidden md:block absolute top-6 right-0 translate-x-1/2 w-12 h-[2px] bg-slate-200" />
                  )}
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════ PRICING ════════════════════ */}
      <section className="py-24 md:py-32" id="pricing" data-testid="pricing-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <FadeIn>
            <div className="text-center max-w-2xl mx-auto mb-16">
              <span className="text-xs font-mono uppercase tracking-[0.2em] text-[#0F62FE] mb-4 block">
                Pricing
              </span>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 tracking-tight mb-5 font-display">
                Transparent pricing. No surprises.
              </h2>
              <p className="text-base text-slate-600 leading-relaxed">
                Start free. Upgrade when you're ready. Cancel anytime.
              </p>
            </div>
          </FadeIn>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-5">
            {pricingPlans.map((plan, index) => (
              <FadeIn key={index} delay={index * 80}>
                <div
                  className={`relative p-7 rounded-2xl border-2 h-full flex flex-col transition-shadow duration-300 ${
                    plan.highlighted
                      ? 'bg-[#0B1221] text-white border-[#0B1221] shadow-2xl shadow-slate-900/20 lg:scale-105 z-10'
                      : 'bg-white text-slate-900 border-slate-100 hover:border-slate-200 hover:shadow-lg'
                  }`}
                  data-testid={`pricing-card-${plan.name.toLowerCase().replace(' ', '-')}`}
                >
                  {plan.highlighted && (
                    <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 px-4 py-1 bg-cyan-400 text-[#0B1221] text-[11px] font-bold rounded-md uppercase tracking-wide">
                      Most Popular
                    </div>
                  )}

                  <h3 className={`text-lg font-semibold mb-1 font-display ${plan.highlighted ? 'text-white' : 'text-slate-900'}`}>
                    {plan.name}
                  </h3>
                  <p className={`text-sm mb-6 ${plan.highlighted ? 'text-slate-400' : 'text-slate-500'}`}>
                    {plan.description}
                  </p>

                  <div className="mb-7">
                    <span className="text-3xl font-bold font-display">{plan.price}</span>
                    <span className={`text-sm ${plan.highlighted ? 'text-slate-400' : 'text-slate-500'}`}>{plan.period}</span>
                  </div>

                  <ul className="space-y-3 mb-8 flex-1">
                    {plan.features.map((feature, fIndex) => (
                      <li key={fIndex} className="flex items-start gap-2.5 text-sm">
                        <Check className={`h-4 w-4 mt-0.5 flex-shrink-0 ${plan.highlighted ? 'text-cyan-400' : 'text-emerald-500'}`} />
                        <span className={plan.highlighted ? 'text-slate-300' : 'text-slate-600'}>{feature}</span>
                      </li>
                    ))}
                  </ul>

                  <Link to={plan.name === 'Enterprise' ? '/page/contact-us' : '/signup'} className="mt-auto">
                    <Button
                      className={`w-full py-3 h-auto rounded-lg font-semibold text-sm transition-transform hover:-translate-y-0.5 ${
                        plan.highlighted
                          ? 'bg-white text-[#0B1221] hover:bg-slate-100'
                          : 'bg-[#0F62FE] text-white hover:bg-[#0043CE]'
                      }`}
                    >
                      {plan.cta}
                    </Button>
                  </Link>
                </div>
              </FadeIn>
            ))}
          </div>
        </div>
      </section>

      {/* ════════════════════ FINAL CTA ════════════════════ */}
      <section className="py-24 md:py-32 bg-[#0B1221]" data-testid="cta-section">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <FadeIn>
              <div>
                <h2 className="text-3xl md:text-4xl font-bold text-white tracking-tight mb-6 font-display">
                  Ready to transform your after-sales operations?
                </h2>
                <p className="text-base text-slate-400 mb-8 max-w-md leading-relaxed">
                  Join hundreds of MSPs and IT teams already delivering faster, better service with aftersales.support.
                </p>
                <div className="flex flex-col sm:flex-row gap-3">
                  <Link to="/signup">
                    <Button className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-8 py-3.5 h-auto text-sm rounded-lg font-semibold transition-transform hover:-translate-y-0.5 shadow-lg shadow-blue-500/20">
                      Start Free Trial
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </Link>
                  <Link to="/page/contact-us">
                    <Button variant="outline" className="px-8 py-3.5 h-auto text-sm rounded-lg font-semibold border border-slate-600 text-white hover:bg-slate-800 transition-colors">
                      Talk to Sales
                    </Button>
                  </Link>
                </div>
              </div>
            </FadeIn>

            <FadeIn delay={150}>
              <div className="relative rounded-2xl overflow-hidden h-[260px] lg:h-[300px]">
                <img
                  src={IMAGES.workspace}
                  alt="Modern workspace"
                  className="w-full h-full object-cover"
                  loading="lazy"
                />
                <div className="absolute inset-0 bg-gradient-to-r from-[#0B1221]/40 to-transparent" />
              </div>
            </FadeIn>
          </div>
        </div>
      </section>

      <PublicFooter />
    </div>
  );
};

export default LandingPage;
