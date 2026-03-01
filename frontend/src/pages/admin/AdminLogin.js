import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { Shield, Mail, Lock, ArrowRight, Building2 } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useSettings } from '../../context/SettingsContext';
import { useTenant, getTenantRequestConfig, buildTenantUrl } from '../../context/TenantContext';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';
import TenantError, { TenantLoading } from '../../components/TenantError';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AdminLogin = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [checkingSetup, setCheckingSetup] = useState(true);
  const { login, isAuthenticated } = useAuth();
  const { settings } = useSettings();
  const { tenant, loading: tenantLoading, error: tenantError, resolution } = useTenant();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate(buildTenantUrl('/admin/dashboard'));
    }
    checkAdminSetup();
  }, [isAuthenticated, navigate]);

  const checkAdminSetup = async () => {
    try {
      const config = getTenantRequestConfig();
      await axios.get(`${API}/auth/me`, config);
    } catch (error) {
      // This is expected - just checking
    }
    setCheckingSetup(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please enter email and password');
      return;
    }

    setLoading(true);
    try {
      // Pass tenant context to login
      await login(email, password, tenant?.slug);
      toast.success('Login successful');
      
      // Check for stored redirect path
      const redirectPath = sessionStorage.getItem('redirectAfterLogin');
      if (redirectPath) {
        sessionStorage.removeItem('redirectAfterLogin');
        navigate(buildTenantUrl(redirectPath));
      } else {
        navigate(buildTenantUrl('/admin/dashboard'));
      }
    } catch (error) {
      const message = error.response?.data?.detail || 'Login failed';
      if (message.includes('Invalid credentials')) {
        toast.error('Invalid email or password');
      } else if (message.includes('suspended')) {
        toast.error('This workspace has been suspended. Contact support.');
      } else if (!error.response) {
        toast.error('Network error. Please check your connection.');
      } else {
        toast.error(message);
      }
    } finally {
      setLoading(false);
    }
  };

  // Show tenant error if present
  if (tenantError) {
    return <TenantError error={tenantError} tenantName={tenant?.name} slug={tenant?.slug} />;
  }

  // Show loading while resolving tenant
  if (tenantLoading) {
    return <TenantLoading />;
  }

  if (checkingSetup) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  // Get branding - prefer tenant branding, fallback to global settings
  const branding = tenant?.branding || settings;
  const accentColor = branding?.accent_color || '#0F62FE';
  const companyName = 'aftersales.support';
  const logo = branding?.logo_base64 || branding?.logo_url || settings.logo_base64 || settings.logo_url;

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-6 py-12">
      <div className="w-full max-w-md">
        {/* Logo & Branding */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-4">
            {logo ? (
              <img 
                src={logo} 
                alt={companyName} 
                className="h-10 w-auto"
              />
            ) : (
              <Shield className="h-10 w-10" style={{ color: accentColor }} />
            )}
          </div>
          <h1 className="text-2xl font-semibold text-slate-900 mb-2">
            {tenant ? companyName : 'Admin Portal'}
          </h1>
          <p className="text-slate-500 text-sm">
            {tenant ? (
              <>Sign in to <span className="font-medium text-slate-700">{tenant.name}</span></>
            ) : (
              'Sign in to manage warranties and assets'
            )}
          </p>
          
          {/* Tenant indicator */}
          {tenant && (
            <div className="mt-3 inline-flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-full text-xs text-slate-600">
              <Building2 className="w-3.5 h-3.5" />
              <span>Workspace: <span className="font-mono font-medium">{tenant.slug}</span></span>
            </div>
          )}
        </div>

        {/* Login Card */}
        <div className="bg-white rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-slate-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="form-label">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="admin@example.com"
                  className="form-input pl-11"
                  data-testid="admin-email-input"
                />
              </div>
            </div>

            <div>
              <label className="form-label">Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="form-input pl-11"
                  data-testid="admin-password-input"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full py-3"
              style={{ backgroundColor: accentColor }}
              data-testid="admin-login-btn"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Signing in...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  Sign In
                  <ArrowRight className="h-4 w-4" />
                </span>
              )}
            </Button>
          </form>

          {/* Setup Link - only show if no tenant context */}
          {!tenant && (
            <div className="mt-6 pt-6 border-t border-slate-100 text-center">
              <p className="text-sm text-slate-500">
                First time?{' '}
                <Link 
                  to="/admin/setup" 
                  className="hover:underline font-medium"
                  style={{ color: accentColor }}
                  data-testid="setup-link"
                >
                  Create admin account
                </Link>
              </p>
            </div>
          )}
          
          {/* Dev mode info */}
          {resolution === 'query_param' && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-xs text-amber-800">
              <strong>Dev Mode:</strong> Using <code className="bg-amber-100 px-1 rounded">?_tenant={tenant?.slug}</code> query param
            </div>
          )}
        </div>

        {/* Back to Portal */}
        <div className="mt-8 text-center space-y-2">
          <Link 
            to="/" 
            className="text-sm text-slate-500 hover:text-slate-700 transition-colors block"
          >
            ← Back to Home
          </Link>
          {tenant && (
            <p className="text-xs text-slate-400">
              Not a member of {tenant.name}? Contact your administrator.
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminLogin;
