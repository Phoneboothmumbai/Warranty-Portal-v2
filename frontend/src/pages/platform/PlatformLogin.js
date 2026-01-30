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
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-[url('data:image/svg+xml,%3Csvg width=%2260%22 height=%2260%22 viewBox=%220 0 60 60%22 xmlns=%22http://www.w3.org/2000/svg%22%3E%3Cg fill=%22none%22 fill-rule=%22evenodd%22%3E%3Cg fill=%22%239C92AC%22 fill-opacity=%220.05%22%3E%3Cpath d=%22M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z%22/%3E%3C/g%3E%3C/g%3E%3C/svg%3E')] opacity-20"></div>
      
      <Card className="w-full max-w-md relative z-10 bg-slate-800/90 border-slate-700 backdrop-blur-sm" data-testid="platform-login-card">
        <CardHeader className="text-center pb-2">
          <div className="mx-auto w-16 h-16 bg-gradient-to-br from-violet-500 to-purple-600 rounded-2xl flex items-center justify-center mb-4 shadow-lg shadow-purple-500/30">
            <Shield className="w-8 h-8 text-white" />
          </div>
          <CardTitle className="text-2xl text-white">Platform Admin</CardTitle>
          <CardDescription className="text-slate-400">
            {isSetup ? 'Create your super admin account' : 'Sign in to manage all tenants'}
          </CardDescription>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={isSetup ? handleSetup : handleLogin} className="space-y-4">
            {isSetup && (
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-1">Full Name</label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                  placeholder="Platform Admin"
                  required
                  data-testid="name-input"
                />
              </div>
            )}
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Email</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                placeholder="admin@platform.com"
                required
                data-testid="email-input"
              />
            </div>
            
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-1">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-2.5 bg-slate-700/50 border border-slate-600 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent transition-all"
                placeholder="••••••••"
                required
                data-testid="password-input"
              />
            </div>
            
            <Button
              type="submit"
              className="w-full bg-gradient-to-r from-violet-500 to-purple-600 hover:from-violet-600 hover:to-purple-700 text-white py-2.5 rounded-lg font-medium transition-all shadow-lg shadow-purple-500/25"
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
              className="text-sm text-slate-400 hover:text-purple-400 transition-colors"
            >
              {isSetup ? 'Already have an account? Sign in' : 'First time? Setup admin account'}
            </button>
          </div>
          
          <div className="mt-4 pt-4 border-t border-slate-700 text-center">
            <p className="text-xs text-slate-500">
              This is the platform super admin panel.
              <br />
              For tenant admin access, use <a href="/admin/login" className="text-purple-400 hover:text-purple-300">/admin/login</a>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
