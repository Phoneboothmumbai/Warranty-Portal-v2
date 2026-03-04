import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTenant } from '../../context/TenantContext';
import { Shield, LogIn, Eye, EyeOff } from 'lucide-react';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';

export default function PortalLogin() {
  const { tenant, login, tenantCode, isAuthenticated } = useTenant();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  if (isAuthenticated) {
    navigate(`/portal/${tenantCode}`, { replace: true });
    return null;
  }

  const primaryColor = tenant?.portal_theme?.primary_color || tenant?.accent_color || '#0F62FE';

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      await login(email, password);
      navigate(`/portal/${tenantCode}`);
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 via-white to-slate-100 p-4">
      <div className="w-full max-w-sm">
        {/* Branding Header */}
        <div className="text-center mb-8">
          {tenant?.logo_url ? (
            <img src={tenant.logo_url} alt="" className="h-12 mx-auto mb-4" />
          ) : (
            <div className="h-14 w-14 rounded-xl mx-auto mb-4 flex items-center justify-center shadow-lg" style={{ backgroundColor: primaryColor }}>
              <Shield className="h-7 w-7 text-white" />
            </div>
          )}
          <h1 className="text-xl font-bold text-slate-900">{tenant?.company_name || 'Customer Portal'}</h1>
          <p className="text-sm text-slate-500 mt-1">Sign in to access your service portal</p>
        </div>

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="bg-white rounded-xl border shadow-sm p-6 space-y-4" data-testid="portal-login-form">
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1">Email</label>
            <Input type="email" value={email} onChange={e => setEmail(e.target.value)}
              placeholder="your@email.com" required data-testid="portal-login-email" />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1">Password</label>
            <div className="relative">
              <Input type={showPw ? 'text' : 'password'} value={password} onChange={e => setPassword(e.target.value)}
                placeholder="Enter password" required data-testid="portal-login-password" />
              <button type="button" onClick={() => setShowPw(!showPw)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>
          {error && <p className="text-xs text-red-500 bg-red-50 p-2 rounded" data-testid="portal-login-error">{error}</p>}
          <Button type="submit" disabled={loading} className="w-full text-white"
            style={{ backgroundColor: primaryColor }} data-testid="portal-login-btn">
            {loading ? 'Signing in...' : <><LogIn className="w-4 h-4 mr-2" />Sign In</>}
          </Button>
        </form>

        <p className="text-center text-xs text-slate-400 mt-6">
          Powered by <span className="font-medium">{tenant?.provider_name || 'aftersales.support'}</span>
        </p>
      </div>
    </div>
  );
}
