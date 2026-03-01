import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { Shield, User, Mail, Lock, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const AdminSetup = () => {
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!name || !email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    if (password.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }

    if (password !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }

    setLoading(true);
    try {
      await axios.post(`${API}/auth/setup`, { name, email, password });
      setSuccess(true);
      toast.success('Admin account created successfully');
      setTimeout(() => navigate('/admin/login'), 2000);
    } catch (error) {
      const message = error.response?.data?.detail || 'Setup failed';
      toast.error(message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-6">
        <div className="text-center animate-fade-in">
          <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-6">
            <CheckCircle2 className="h-8 w-8 text-emerald-500" />
          </div>
          <h2 className="text-2xl font-semibold text-slate-900 mb-3">Account Created!</h2>
          <p className="text-slate-500 mb-6">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-6 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-10">
          <div className="flex items-center justify-center gap-3 mb-4">
            <Shield className="h-10 w-10 text-[#0F62FE]" />
          </div>
          <h1 className="text-2xl font-semibold text-slate-900 mb-2">Create Admin Account</h1>
          <p className="text-slate-500 text-sm">Set up your first administrator account</p>
        </div>

        {/* Setup Card */}
        <div className="bg-white rounded-2xl shadow-[0_2px_8px_rgba(0,0,0,0.04)] border border-slate-100 p-8">
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="form-label">Full Name</label>
              <div className="relative">
                <User className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="John Doe"
                  className="form-input pl-11"
                  data-testid="setup-name-input"
                />
              </div>
            </div>

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
                  data-testid="setup-email-input"
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
                  placeholder="Minimum 6 characters"
                  className="form-input pl-11"
                  data-testid="setup-password-input"
                />
              </div>
            </div>

            <div>
              <label className="form-label">Confirm Password</label>
              <div className="relative">
                <Lock className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter password"
                  className="form-input pl-11"
                  data-testid="setup-confirm-password-input"
                />
              </div>
            </div>

            <Button
              type="submit"
              disabled={loading}
              className="w-full bg-[#0F62FE] hover:bg-[#0043CE] text-white py-3"
              data-testid="setup-submit-btn"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  Creating Account...
                </span>
              ) : (
                <span className="flex items-center justify-center gap-2">
                  Create Account
                  <ArrowRight className="h-4 w-4" />
                </span>
              )}
            </Button>
          </form>

          {/* Login Link */}
          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <p className="text-sm text-slate-500">
              Already have an account?{' '}
              <a 
                href="/admin/login" 
                className="text-[#0F62FE] hover:underline font-medium"
              >
                Sign in
              </a>
            </p>
          </div>
        </div>

        {/* Back to Portal */}
        <div className="mt-8 text-center">
          <a 
            href="/" 
            className="text-sm text-slate-500 hover:text-slate-700 transition-colors"
          >
            ← Back to aftersales.support
          </a>
        </div>
      </div>
    </div>
  );
};

export default AdminSetup;
