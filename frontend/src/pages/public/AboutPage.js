import { Link } from 'react-router-dom';
import { Shield, ArrowRight, Target, Eye, Users, Award } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { useSettings } from '../../context/SettingsContext';

const AboutPage = () => {
  const { settings } = useSettings();

  const values = [
    {
      icon: Target,
      title: 'Mission-Driven',
      description: 'We believe every business deserves enterprise-grade IT asset management without the enterprise price tag.'
    },
    {
      icon: Eye,
      title: 'Transparency',
      description: 'Simple pricing, honest communication, and no hidden fees. What you see is what you get.'
    },
    {
      icon: Users,
      title: 'Customer First',
      description: 'We build features our customers actually need, not what looks good in a demo.'
    },
    {
      icon: Award,
      title: 'Quality',
      description: 'Reliable, secure, and performant. We take uptime and data security seriously.'
    }
  ];

  const stats = [
    { value: '2024', label: 'Founded' },
    { value: '10,000+', label: 'Assets Tracked' },
    { value: '500+', label: 'Organizations' },
    { value: '99.9%', label: 'Uptime' }
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
              <Link to="/features" className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors">Features</Link>
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
      <section className="pt-32 pb-16 md:pt-40 md:pb-20 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-gradient-to-br from-blue-50 to-transparent rounded-full blur-3xl opacity-60" />
        
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
          <div className="max-w-3xl">
            <span className="text-sm font-mono uppercase tracking-widest text-[#0F62FE] mb-4 block">
              About Us
            </span>
            <h1 className="text-4xl md:text-6xl font-bold text-slate-900 tracking-tight mb-6 font-display">
              Making IT asset management simple
            </h1>
            <p className="text-lg md:text-xl text-slate-600 leading-relaxed">
              We started with a simple question: Why is managing IT assets so complicated? Our mission is to bring clarity, control, and peace of mind to IT teams everywhere.
            </p>
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="py-16 bg-slate-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-4xl md:text-5xl font-bold text-slate-900 mb-2 font-display">{stat.value}</div>
                <div className="text-slate-500">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Story */}
      <section className="py-20 md:py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid lg:grid-cols-2 gap-16 items-center">
            <div>
              <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6 font-display">
                Our Story
              </h2>
              <div className="space-y-4 text-lg text-slate-600 leading-relaxed">
                <p>
                  Born from the frustration of managing spreadsheets, tracking warranty emails, and losing track of service contracts, we set out to build a better way.
                </p>
                <p>
                  Our team has decades of combined experience in IT operations, enterprise software, and customer success. We've felt the pain firsthand and built the solution we wished we had.
                </p>
                <p>
                  Today, we're proud to serve hundreds of organizations—from small businesses to large enterprises—helping them track every asset, never miss a warranty, and deliver exceptional IT service.
                </p>
              </div>
            </div>
            <div className="bg-slate-100 rounded-3xl aspect-square flex items-center justify-center">
              <div className="text-center p-8">
                <Shield className="h-24 w-24 text-slate-300 mx-auto mb-4" />
                <p className="text-slate-400 text-sm">Team Photo</p>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section className="py-20 md:py-24 bg-slate-900 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4 font-display">
              Our Values
            </h2>
            <p className="text-lg text-slate-400 max-w-2xl mx-auto">
              The principles that guide everything we do
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {values.map((value, index) => (
              <div key={index} className="text-center">
                <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-6">
                  <value.icon className="h-8 w-8 text-[#0F62FE]" />
                </div>
                <h3 className="text-xl font-semibold mb-3 font-display">{value.title}</h3>
                <p className="text-slate-400 leading-relaxed">{value.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20 md:py-24">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-4xl font-bold text-slate-900 mb-6 font-display">
            Want to learn more?
          </h2>
          <p className="text-lg text-slate-600 mb-10">
            Get in touch with our team to see how we can help your organization.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link to="/page/contact-us">
              <Button className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-8 py-4 h-auto text-base rounded-xl font-semibold">
                Contact Us
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Link to="/signup">
              <Button variant="outline" className="px-8 py-4 h-auto text-base rounded-xl font-semibold border-2">
                Start Free Trial
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
              <Link to="/pricing" className="hover:text-white transition-colors">Pricing</Link>
              <Link to="/page/contact-us" className="hover:text-white transition-colors">Contact</Link>
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

export default AboutPage;
