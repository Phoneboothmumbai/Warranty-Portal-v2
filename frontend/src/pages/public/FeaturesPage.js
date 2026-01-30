import { Link } from 'react-router-dom';
import { 
  Shield, ArrowRight, HardDrive, Ticket, FileText, 
  BarChart3, QrCode, Bell, Wrench, Users, Building2,
  Lock, Zap, Globe, Mail, Clock, CheckCircle,
  Smartphone, Database, Cloud, Settings
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { useSettings } from '../../context/SettingsContext';

const FeaturesPage = () => {
  const { settings } = useSettings();

  const mainFeatures = [
    {
      icon: HardDrive,
      title: 'Asset Lifecycle Management',
      description: 'Track every IT asset from procurement to retirement. Maintain complete visibility with detailed records including purchase info, warranty status, assignments, and service history.',
      highlights: ['Complete asset inventory', 'Assignment tracking', 'Lifecycle stages', 'Bulk import/export'],
      color: 'bg-blue-500'
    },
    {
      icon: Shield,
      title: 'Warranty Tracking & Alerts',
      description: 'Never miss a warranty claim again. Our intelligent system tracks expiry dates and sends automated alerts before coverage ends, maximizing your warranty ROI.',
      highlights: ['Expiry notifications', 'Coverage verification', 'AMC override logic', 'PDF reports'],
      color: 'bg-emerald-500'
    },
    {
      icon: Ticket,
      title: 'Enterprise Ticketing System',
      description: 'Full-featured ticketing inspired by osTicket. Complete with SLA management, auto-routing, canned responses, custom forms, and email integration.',
      highlights: ['SLA tracking', 'Auto-assignment', 'Email integration', 'Custom forms'],
      color: 'bg-purple-500'
    },
    {
      icon: FileText,
      title: 'AMC Contract Management',
      description: 'Manage Annual Maintenance Contracts with ease. Track coverage, usage limits, renewals, and link contracts to devices for comprehensive service coverage.',
      highlights: ['Usage tracking', 'Renewal alerts', 'Device assignments', 'Contract documents'],
      color: 'bg-amber-500'
    }
  ];

  const additionalFeatures = [
    { icon: QrCode, title: 'QR Code Generation', description: 'Generate printable QR codes for instant asset lookup and service requests.' },
    { icon: Bell, title: 'Smart Notifications', description: 'In-app alerts for warranty expiry, SLA breaches, and ticket updates.' },
    { icon: Users, title: 'Multi-tenant Architecture', description: 'Isolate data between organizations with complete tenant separation.' },
    { icon: Building2, title: 'Company Portal', description: 'Self-service portal for your clients to view assets and raise tickets.' },
    { icon: Wrench, title: 'Engineer Portal', description: 'Mobile-friendly interface for field technicians and service visits.' },
    { icon: BarChart3, title: 'Analytics Dashboard', description: 'Real-time insights into asset health, warranty status, and service metrics.' },
    { icon: Mail, title: 'Email Integration', description: 'Create and reply to tickets via email. SMTP and IMAP support.' },
    { icon: Lock, title: 'Role-Based Access', description: 'Granular permissions for admins, company users, and engineers.' },
    { icon: Database, title: 'Bulk Operations', description: 'Import devices, companies, and employees via Excel/CSV.' },
    { icon: Globe, title: 'API Access', description: 'RESTful API for integrations with your existing systems.' },
    { icon: Clock, title: 'Audit Logging', description: 'Complete audit trail of all changes for compliance and accountability.' },
    { icon: Cloud, title: 'Cloud Hosted', description: 'Secure, reliable cloud infrastructure with 99.9% uptime SLA.' }
  ];

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
              <Link to="/features" className="text-sm font-medium text-[#0F62FE]">Features</Link>
              <Link to="/pricing" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Pricing</Link>
              <Link to="/page/contact-us" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Contact</Link>
            </div>

            <div className="hidden md:flex items-center gap-4">
              <Link to="/company/login" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Sign In</Link>
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
      <section className="pt-32 pb-20 md:pt-40 md:pb-24 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-blue-50 to-transparent rounded-full blur-3xl opacity-60" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative text-center">
          <span className="text-sm font-mono uppercase tracking-widest text-[#0F62FE] mb-4 block">
            Features
          </span>
          <h1 className="text-4xl md:text-6xl font-bold text-slate-900 tracking-tight mb-6 font-display">
            Powerful features for<br />modern IT teams
          </h1>
          <p className="text-lg md:text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Everything you need to track assets, manage warranties, handle service requests, and maintain compliance—all in one platform.
          </p>
        </div>
      </section>

      {/* Main Features */}
      <section className="py-20 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="space-y-24">
            {mainFeatures.map((feature, index) => (
              <div 
                key={index} 
                className={`grid lg:grid-cols-2 gap-12 items-center ${index % 2 === 1 ? 'lg:flex-row-reverse' : ''}`}
              >
                <div className={index % 2 === 1 ? 'lg:order-2' : ''}>
                  <div className={`w-16 h-16 ${feature.color} rounded-2xl flex items-center justify-center mb-6`}>
                    <feature.icon className="h-8 w-8 text-white" />
                  </div>
                  <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4 font-display">
                    {feature.title}
                  </h2>
                  <p className="text-lg text-slate-600 mb-8 leading-relaxed">
                    {feature.description}
                  </p>
                  <ul className="space-y-3">
                    {feature.highlights.map((highlight, hIndex) => (
                      <li key={hIndex} className="flex items-center gap-3">
                        <CheckCircle className="h-5 w-5 text-emerald-500 flex-shrink-0" />
                        <span className="text-slate-700">{highlight}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className={`bg-slate-100 rounded-3xl aspect-video flex items-center justify-center ${index % 2 === 1 ? 'lg:order-1' : ''}`}>
                  <div className="text-center p-8">
                    <feature.icon className="h-20 w-20 text-slate-300 mx-auto mb-4" />
                    <p className="text-slate-400 text-sm">Feature Preview</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Additional Features Grid */}
      <section className="py-20 md:py-24 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-4 font-display">
              And much more...
            </h2>
            <p className="text-lg text-slate-600">
              Additional capabilities to streamline your IT operations
            </p>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {additionalFeatures.map((feature, index) => (
              <div 
                key={index}
                className="p-6 bg-white rounded-2xl border border-slate-100 hover:border-slate-200 hover:shadow-lg transition-all duration-300"
              >
                <div className="w-12 h-12 bg-slate-100 rounded-xl flex items-center justify-center mb-4">
                  <feature.icon className="h-6 w-6 text-slate-600" />
                </div>
                <h3 className="text-lg font-semibold text-slate-900 mb-2 font-display">{feature.title}</h3>
                <p className="text-sm text-slate-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 md:py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6 font-display">
            Ready to get started?
          </h2>
          <p className="text-lg text-slate-600 mb-10">
            Start your free trial today. No credit card required.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/signup">
              <Button className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-8 py-4 h-auto text-base rounded-xl font-semibold">
                Start Free Trial
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/pricing">
              <Button variant="outline" className="px-8 py-4 h-auto text-base rounded-xl font-semibold border-2">
                View Pricing
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
              <Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link>
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

export default FeaturesPage;
