import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Menu, X, ArrowRight } from 'lucide-react';
import { Button } from '../ui/button';
import { useSettings } from '../../context/SettingsContext';

const PublicHeader = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { settings } = useSettings();
  const location = useLocation();

  const navLinks = [
    { to: '/features', label: 'Features' },
    { to: '/pricing', label: 'Pricing' },
    { to: '/page/contact-us', label: 'Contact' },
    { to: '/support', label: 'Support Portal' }
  ];

  const isActive = (path) => location.pathname === path;

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-xl border-b border-slate-200/50" data-testid="public-header">
      <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3 group" data-testid="header-logo">
            <div className="w-10 h-10 rounded-xl bg-[#0F62FE] flex items-center justify-center group-hover:scale-105 transition-transform">
              {(settings?.logo_base64 || settings?.logo_url) ? (
                <img src={settings.logo_base64 || settings.logo_url} alt="Logo" className="h-6 w-6" />
              ) : (
                <Shield className="h-5 w-5 text-white" />
              )}
            </div>
            <span className="text-lg font-semibold text-slate-900 font-display">
              {settings?.company_name || 'MSP Portal'}
            </span>
          </Link>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-8">
            {navLinks.map(link => (
              <Link 
                key={link.to}
                to={link.to} 
                className={`text-sm font-medium transition-colors ${
                  isActive(link.to) 
                    ? 'text-[#0F62FE]' 
                    : 'text-slate-600 hover:text-slate-900'
                }`}
                data-testid={`nav-${link.label.toLowerCase().replace(' ', '-')}`}
              >
                {link.label}
              </Link>
            ))}
          </div>

          {/* Desktop CTA */}
          <div className="hidden md:flex items-center gap-4">
            <Link 
              to="/admin/login" 
              className="text-sm font-medium text-slate-600 hover:text-slate-900 transition-colors"
              data-testid="nav-signin"
            >
              MSP Login
            </Link>
            <Link to="/signup">
              <Button 
                className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-5 py-2 rounded-lg font-medium transition-all hover:-translate-y-0.5 hover:shadow-lg" 
                data-testid="nav-get-started"
              >
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
              {navLinks.map(link => (
                <Link 
                  key={link.to}
                  to={link.to} 
                  className={`text-sm font-medium py-2 ${
                    isActive(link.to) 
                      ? 'text-[#0F62FE]' 
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                  onClick={() => setMobileMenuOpen(false)}
                >
                  {link.label}
                </Link>
              ))}
              <div className="flex flex-col gap-3 pt-4 border-t border-slate-100">
                <Link to="/admin/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="outline" className="w-full">MSP Login</Button>
                </Link>
                <Link to="/signup" onClick={() => setMobileMenuOpen(false)}>
                  <Button className="w-full bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                    Get Started
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        )}
      </nav>
    </header>
  );
};

export default PublicHeader;
