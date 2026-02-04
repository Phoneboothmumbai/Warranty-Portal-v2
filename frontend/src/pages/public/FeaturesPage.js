import { Link } from 'react-router-dom';
import { 
  ArrowRight, HardDrive, Ticket, FileText, 
  BarChart3, QrCode, Bell, Wrench, Users, Building2,
  Lock, Globe, Mail, Clock, CheckCircle,
  Database, Cloud, Layers
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import PublicHeader from '../../components/public/PublicHeader';
import PublicFooter from '../../components/public/PublicFooter';

const FeaturesPage = () => {
  const mainFeatures = [
    {
      icon: Layers,
      title: 'Multi-Client Management',
      description: 'Manage all your clients from one dashboard. Each client gets their own isolated environment with separate assets, tickets, and contracts. Perfect for MSPs handling dozens of organizations.',
      highlights: ['Isolated client data', 'Bulk client onboarding', 'Per-client reporting', 'White-label options'],
      color: 'bg-blue-500',
      image: 'https://static.prod-images.emergentagent.com/jobs/77de96b7-114e-4ef9-99d0-a0515c928a97/images/feab4534cce1f2362b32a777d41ce1afede48e8892fed8c6d89bd57d67614a1c.png'
    },
    {
      icon: HardDrive,
      title: 'Warranty Intelligence',
      description: 'Never miss a warranty claim across any client. Our system tracks expiry dates, sends automated alerts, and helps you maximize warranty ROI for your entire client base.',
      highlights: ['Cross-client alerts', 'Coverage verification', 'AMC override logic', 'Client-ready reports'],
      color: 'bg-emerald-500',
      image: 'https://static.prod-images.emergentagent.com/jobs/77de96b7-114e-4ef9-99d0-a0515c928a97/images/af88f29c05f7ccd022a71f991cc3f2793c4c264af2d668422d01cd75c1dbbb70.png'
    },
    {
      icon: Ticket,
      title: 'Service Desk & Ticketing',
      description: 'Professional service desk for MSPs. Handle tickets across all clients with SLA management, auto-routing based on client contracts, email-to-ticket, and client portals.',
      highlights: ['Per-client SLAs', 'Auto-assignment', 'Email integration', 'Client self-service'],
      color: 'bg-purple-500',
      image: 'https://static.prod-images.emergentagent.com/jobs/77de96b7-114e-4ef9-99d0-a0515c928a97/images/50861e39048d86cff8fe8b92af2c02c17139d3e9e3ab60a77fbfb14da4abb22c.png'
    },
    {
      icon: FileText,
      title: 'AMC & Contract Management',
      description: 'Track service contracts across all clients. Monitor usage limits, renewal dates, and automatically link contracts to devices for comprehensive coverage tracking.',
      highlights: ['Multi-client contracts', 'Usage tracking', 'Renewal automation', 'Billing integration'],
      color: 'bg-amber-500',
      image: 'https://static.prod-images.emergentagent.com/jobs/77de96b7-114e-4ef9-99d0-a0515c928a97/images/bf7e05c2cbb18cd6b864ecb97a35e1f303c26a4642e9afec35c8eba67eb87b2d.png'
    }
  ];

  const additionalFeatures = [
    { icon: QrCode, title: 'QR Asset Labels', description: 'Generate QR codes for instant asset lookup. Engineers scan to view history or raise tickets.' },
    { icon: Bell, title: 'Smart Notifications', description: 'Alerts for warranty expiry, SLA breaches, and contract renewals across all clients.' },
    { icon: Users, title: 'Team Management', description: 'Assign technicians to clients, track workload, and manage schedules.' },
    { icon: Building2, title: 'Client Portals', description: 'Branded self-service portals for your clients to view assets and submit tickets.' },
    { icon: Wrench, title: 'Field Engineer App', description: 'Mobile-friendly interface for technicians to log visits, update tickets, and capture signatures.' },
    { icon: BarChart3, title: 'MSP Analytics', description: 'Business insights: profitability per client, SLA compliance, technician utilization.' },
    { icon: Mail, title: 'Email-to-Ticket', description: 'Clients email support, tickets auto-create and route to the right team.' },
    { icon: Lock, title: 'Role-Based Access', description: 'Granular permissions: MSP admins, technicians, client admins, and end-users.' },
    { icon: Database, title: 'Bulk Operations', description: 'Onboard new clients fast with Excel/CSV imports for devices and users.' },
    { icon: Globe, title: 'REST API', description: 'Integrate with RMM tools, PSA software, and your existing stack.' },
    { icon: Clock, title: 'Audit Trail', description: 'Complete logging of all changes for compliance and client transparency.' },
    { icon: Cloud, title: 'Secure Cloud', description: 'SOC 2 compliant infrastructure with 99.9% uptime guarantee.' }
  ];

  return (
    <div className="min-h-screen bg-white" data-testid="features-page">
      <PublicHeader />

      {/* Hero */}
      <section className="pt-32 pb-20 md:pt-40 md:pb-24 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-blue-50 to-transparent rounded-full blur-3xl opacity-60" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative text-center">
          <span className="text-sm font-mono uppercase tracking-widest text-[#0F62FE] mb-4 block">
            Features
          </span>
          <h1 className="text-4xl md:text-6xl font-bold text-slate-900 tracking-tight mb-6 font-display">
            Everything MSPs Need<br />to Scale Service Delivery
          </h1>
          <p className="text-lg md:text-xl text-slate-600 max-w-3xl mx-auto leading-relaxed">
            Purpose-built for IT service providers. Manage multiple clients, track assets across organizations, handle tickets professionally, and grow your MSP business.
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
                <div className={`rounded-3xl overflow-hidden shadow-2xl border border-slate-200 ${index % 2 === 1 ? 'lg:order-1' : ''}`}>
                  <img 
                    src={feature.image} 
                    alt={feature.title}
                    className="w-full h-full object-cover aspect-video"
                  />
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

      <PublicFooter />
    </div>
  );
};

export default FeaturesPage;
