import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Shield, ArrowRight } from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';
import { Button } from '../../components/ui/button';

const LandingPage = () => {
  const [query, setQuery] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { settings } = useSettings();

  const handleSearch = (e) => {
    e.preventDefault();
    if (!query.trim()) {
      setError('Please enter a Serial Number or Asset Tag');
      return;
    }
    if (query.trim().length < 2) {
      setError('Search query too short');
      return;
    }
    setError('');
    navigate(`/warranty/${encodeURIComponent(query.trim())}`);
  };

  return (
    <div className="min-h-screen flex flex-col bg-white">
      {/* Header */}
      <header className="w-full px-6 py-4 flex justify-between items-center border-b border-slate-100">
        <div className="flex items-center gap-3">
          {(settings.logo_base64 || settings.logo_url) ? (
            <img 
              src={settings.logo_base64 || settings.logo_url} 
              alt="Logo" 
              className="h-8 w-auto"
            />
          ) : (
            <Shield className="h-7 w-7 text-[#0F62FE]" />
          )}
          <span className="text-lg font-semibold text-slate-900">{settings.company_name}</span>
        </div>
        <div className="flex items-center gap-4">
          <a 
            href="/company/login" 
            className="text-sm font-medium text-[#0F62FE] hover:text-[#0043CE] transition-colors"
            data-testid="company-login-link"
          >
            Company Login
          </a>
          <a 
            href="/admin/login" 
            className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
            data-testid="admin-login-link"
          >
            Admin Portal
          </a>
        </div>
      </header>

      {/* Hero Section - The Monolith */}
      <main className="flex-1 flex items-center justify-center px-6 py-16">
        <div className="w-full max-w-2xl mx-auto text-center animate-fade-in">
          {/* Caption */}
          <div className="mb-6">
            <span className="text-xs uppercase tracking-widest text-slate-400 font-medium">
              Warranty Verification Portal
            </span>
          </div>

          {/* Main Heading */}
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-semibold text-slate-900 tracking-tight mb-6">
            Check Your<br />
            <span className="text-[#0F62FE]">Warranty Status</span>
          </h1>

          {/* Subheading */}
          <p className="text-base sm:text-lg text-slate-500 mb-12 max-w-md mx-auto leading-relaxed">
            Enter your device Serial Number or Asset Tag to view warranty coverage details instantly.
          </p>

          {/* Search Form */}
          <form onSubmit={handleSearch} className="w-full">
            <div className="relative">
              <div className="absolute left-5 top-1/2 -translate-y-1/2 text-slate-400">
                <Search className="h-5 w-5" />
              </div>
              <input
                type="text"
                value={query}
                onChange={(e) => { setQuery(e.target.value); setError(''); }}
                placeholder="Enter Serial Number or Asset Tag"
                className="input-hero pl-14 pr-44 font-mono text-base sm:text-lg"
                data-testid="warranty-search-input"
              />
              <div className="absolute right-2 top-1/2 -translate-y-1/2">
                <Button 
                  type="submit"
                  className="bg-[#0F62FE] hover:bg-[#0043CE] text-white px-6 py-2.5 rounded-lg font-medium transition-all shadow-sm hover:shadow-md active:scale-[0.98]"
                  data-testid="warranty-search-btn"
                >
                  Check Warranty
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </div>
            </div>
            {error && (
              <p className="text-red-500 text-sm mt-3" data-testid="search-error">{error}</p>
            )}
          </form>

          {/* Trust Indicators */}
          <div className="mt-16 flex flex-wrap justify-center gap-8 text-sm text-slate-400">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
              <span>Real-time Data</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
              <span>Secure Lookup</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 rounded-full bg-emerald-400"></div>
              <span>PDF Reports</span>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="px-6 py-6 border-t border-slate-100">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4 text-sm text-slate-400">
          <span>© {new Date().getFullYear()} {settings.company_name}. All rights reserved.</span>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;
