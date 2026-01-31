import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { Shield, LogIn } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PlatformLogin() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [isSetup, setIsSetup] = useState(false);
  const [name, setName] = useState('');
  const navigate = useNavigate();

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/api/platform/login`, { email, password });
      
      localStorage.setItem('platformToken', response.data.access_token);
      localStorage.setItem('platformAdmin', JSON.stringify(response.data.admin));
      
      toast.success(`Welcome back, ${response.data.admin.name}!`);
      navigate('/platform/dashboard');
    } catch (error) {
      if (error.response?.status === 401) {
        toast.error('Invalid credentials');
      } else {
        // Check if we need to setup
        toast.error(error.response?.data?.detail || 'Login failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleSetup = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const response = await axios.post(`${API}/api/platform/setup`, {
        email,
        name,
        password
      });
      
      localStorage.setItem('platformToken', response.data.access_token);
      localStorage.setItem('platformAdmin', JSON.stringify(response.data.admin));
      
      toast.success('Platform admin created successfully!');
      navigate('/platform/dashboard');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Setup failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md bg-white border border-slate-200 shadow-sm" data-testid="platform-login-card">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-blue-500 to-blue-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-blue-500/20">
            <Shield className="w-8 h-8 text-slate-900" />
          </div>
          <CardTitle className="text-2xl text-slate-900">Platform Admin</CardTitle>
          <CardDescription className="text-slate-500">
            {isSetup ? 'Create your super admin account' : 'Sign in to manage all tenants'}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={isSetup ? handleSetup : handleLogin} className="space-y-4">
            {isSetup && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                  placeholder="Platform Admin"
                  required
                  data-testid="name-input"
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="admin@platform.com"
                required
                data-testid="email-input"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 bg-white border border-slate-300 rounded-lg text-slate-900 placeholder-slate-400 focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                required
                data-testid="password-input"
              />
            </div>
            
            <Button
              type="submit"
              className="w-full bg-blue-600 hover:bg-blue-700 text-slate-900 py-2.5 rounded-lg font-medium transition-all"
              disabled={loading}
              data-testid="login-button"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  {isSetup ? 'Creating...' : 'Signing in...'}
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  <LogIn className="w-4 h-4" />
                  {isSetup ? 'Create Admin Account' : 'Sign In'}
                </span>
              )}
            </Button>
          </form>
          
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => setIsSetup(!isSetup)}
              className="text-sm text-slate-500 hover:text-blue-600 transition-colors"
            >
              {isSetup ? 'Already have an account? Sign in' : 'First time? Setup admin account'}
            </button>
          </div>
          
          <div className="mt-4 pt-4 border-t border-slate-200 text-center">
            <p className="text-xs text-slate-500">
              This is the platform super admin panel.
              <br />
              For tenant admin access, use <a href="/admin/login" className="text-blue-600 hover:text-blue-700">/admin/login</a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
