import { Link } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';

const PublicFooter = ({ variant = 'full' }) => {
  const { settings } = useSettings();
  const companyName = settings?.company_name || 'AssetVault';

  // Simple footer for signup/login pages
  if (variant === 'simple') {
    return (
      <footer className="py-8 border-t border-slate-200 bg-white" data-testid="public-footer-simple">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <p className="text-center text-sm text-slate-500">
            © {new Date().getFullYear()} {companyName}. All rights reserved.
          </p>
        </div>
      </footer>
    );
  }

  // Full footer
  return (
    <footer className="bg-slate-900 text-white py-20 border-t border-slate-800" data-testid="public-footer">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid md:grid-cols-2 lg:grid-cols-5 gap-12 mb-16">
          {/* Brand */}
          <div className="lg:col-span-2">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-[#0F62FE] flex items-center justify-center">
                {(settings?.logo_base64 || settings?.logo_url) ? (
                  <img src={settings.logo_base64 || settings.logo_url} alt="Logo" className="h-5 w-5" />
                ) : (
                  <Shield className="h-5 w-5 text-white" />
                )}
              </div>
              <span className="text-xl font-semibold font-display">{companyName}</span>
            </div>
            <p className="text-slate-400 leading-relaxed mb-6 max-w-sm">
              Enterprise-grade warranty and asset tracking platform. Built for modern IT teams and MSPs.
            </p>
            <div className="flex gap-4">
              <a href="#" className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-slate-700 transition-colors">
                <span className="sr-only">Twitter</span>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84"/>
                </svg>
              </a>
              <a href="#" className="w-10 h-10 rounded-lg bg-slate-800 flex items-center justify-center hover:bg-slate-700 transition-colors">
                <span className="sr-only">LinkedIn</span>
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z"/>
                </svg>
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
              <li><Link to="/admin/login" className="hover:text-white transition-colors">MSP Login</Link></li>
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
          © {new Date().getFullYear()} {companyName}. All rights reserved.
        </div>
      </div>
    </footer>
  );
};

export default PublicFooter;
