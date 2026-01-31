import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { toast } from 'sonner';
import { 
  Settings, Globe, Mail, CreditCard, Shield, Bell, Save, 
  Loader2, CheckCircle, Building2, DollarSign
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PlatformSettings() {
  const [settings, setSettings] = useState({
    platform_name: 'Asset Vault',
    platform_url: '',
    support_email: '',
    billing_email: '',
    default_trial_days: 14,
    allow_self_signup: true,
    require_email_verification: true,
    maintenance_mode: false,
    maintenance_message: '',
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    razorpay_key_id: '',
    razorpay_key_secret: '',
    google_analytics_id: '',
    sentry_dsn: ''
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('general');
  
  const token = localStorage.getItem('platformToken');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await axios.get(`${API}/api/platform/settings`, { headers });
      setSettings(prev => ({ ...prev, ...response.data }));
    } catch (error) {
      console.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/api/platform/settings`, settings, { headers });
      toast.success('Settings saved successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const tabs = [
    { id: 'general', label: 'General', icon: Settings },
    { id: 'signup', label: 'Signup & Trial', icon: Building2 },
    { id: 'email', label: 'Email (SMTP)', icon: Mail },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'integrations', label: 'Integrations', icon: Globe }
  ];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="platform-settings">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Platform Settings</h1>
          <p className="text-slate-600">Configure global platform settings</p>
        </div>
        <Button onClick={handleSave} disabled={saving} className="bg-blue-600 hover:bg-purple-700">
          {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Save className="w-4 h-4 mr-2" />}
          Save Changes
        </Button>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-slate-200 pb-4">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-100 text-blue-600'
                : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100/50'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* General Settings */}
      {activeTab === 'general' && (
        <div className="grid gap-6">
          <Card className="bg-slate-50/50 border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Platform Identity</CardTitle>
              <CardDescription className="text-slate-600">Basic platform information</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-700">Platform Name</Label>
                  <Input
                    value={settings.platform_name}
                    onChange={(e) => setSettings({ ...settings, platform_name: e.target.value })}
                    className="bg-slate-100 border-slate-300 text-slate-900"
                    placeholder="Asset Vault"
                  />
                </div>
                <div>
                  <Label className="text-slate-700">Platform URL</Label>
                  <Input
                    value={settings.platform_url}
                    onChange={(e) => setSettings({ ...settings, platform_url: e.target.value })}
                    className="bg-slate-100 border-slate-300 text-slate-900"
                    placeholder="https://app.assetvault.io"
                  />
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-700">Support Email</Label>
                  <Input
                    type="email"
                    value={settings.support_email}
                    onChange={(e) => setSettings({ ...settings, support_email: e.target.value })}
                    className="bg-slate-100 border-slate-300 text-slate-900"
                    placeholder="support@platform.com"
                  />
                </div>
                <div>
                  <Label className="text-slate-700">Billing Email</Label>
                  <Input
                    type="email"
                    value={settings.billing_email}
                    onChange={(e) => setSettings({ ...settings, billing_email: e.target.value })}
                    className="bg-slate-100 border-slate-300 text-slate-900"
                    placeholder="billing@platform.com"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-50/50 border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Maintenance Mode</CardTitle>
              <CardDescription className="text-slate-600">Enable to show maintenance page to all users</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Enable Maintenance Mode</p>
                  <p className="text-sm text-slate-600">All users will see a maintenance message</p>
                </div>
                <Switch
                  checked={settings.maintenance_mode}
                  onCheckedChange={(v) => setSettings({ ...settings, maintenance_mode: v })}
                />
              </div>
              
              {settings.maintenance_mode && (
                <div>
                  <Label className="text-slate-700">Maintenance Message</Label>
                  <Input
                    value={settings.maintenance_message}
                    onChange={(e) => setSettings({ ...settings, maintenance_message: e.target.value })}
                    className="bg-slate-100 border-slate-300 text-slate-900"
                    placeholder="We're currently performing scheduled maintenance..."
                  />
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {/* Signup & Trial Settings */}
      {activeTab === 'signup' && (
        <div className="grid gap-6">
          <Card className="bg-slate-50/50 border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Signup Settings</CardTitle>
              <CardDescription className="text-slate-600">Control how new organizations can sign up</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Allow Self-Signup</p>
                  <p className="text-sm text-slate-600">Allow organizations to sign up without an invite</p>
                </div>
                <Switch
                  checked={settings.allow_self_signup}
                  onCheckedChange={(v) => setSettings({ ...settings, allow_self_signup: v })}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-slate-900">Require Email Verification</p>
                  <p className="text-sm text-slate-600">New users must verify their email address</p>
                </div>
                <Switch
                  checked={settings.require_email_verification}
                  onCheckedChange={(v) => setSettings({ ...settings, require_email_verification: v })}
                />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-50/50 border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Trial Settings</CardTitle>
              <CardDescription className="text-slate-600">Configure trial period for new organizations</CardDescription>
            </CardHeader>
            <CardContent>
              <div>
                <Label className="text-slate-700">Default Trial Period (Days)</Label>
                <Input
                  type="number"
                  value={settings.default_trial_days}
                  onChange={(e) => setSettings({ ...settings, default_trial_days: parseInt(e.target.value) })}
                  className="bg-slate-100 border-slate-300 text-slate-900 w-32"
                  min={1}
                  max={90}
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Email Settings */}
      {activeTab === 'email' && (
        <Card className="bg-slate-50/50 border-slate-200">
          <CardHeader>
            <CardTitle className="text-slate-900">SMTP Configuration</CardTitle>
            <CardDescription className="text-slate-600">Configure email server for platform notifications</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-700">SMTP Host</Label>
                <Input
                  value={settings.smtp_host}
                  onChange={(e) => setSettings({ ...settings, smtp_host: e.target.value })}
                  className="bg-slate-100 border-slate-300 text-slate-900"
                  placeholder="smtp.gmail.com"
                />
              </div>
              <div>
                <Label className="text-slate-700">SMTP Port</Label>
                <Input
                  type="number"
                  value={settings.smtp_port}
                  onChange={(e) => setSettings({ ...settings, smtp_port: parseInt(e.target.value) })}
                  className="bg-slate-100 border-slate-300 text-slate-900"
                  placeholder="587"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-700">SMTP Username</Label>
                <Input
                  value={settings.smtp_username}
                  onChange={(e) => setSettings({ ...settings, smtp_username: e.target.value })}
                  className="bg-slate-100 border-slate-300 text-slate-900"
                  placeholder="your-email@gmail.com"
                />
              </div>
              <div>
                <Label className="text-slate-700">SMTP Password</Label>
                <Input
                  type="password"
                  value={settings.smtp_password}
                  onChange={(e) => setSettings({ ...settings, smtp_password: e.target.value })}
                  className="bg-slate-100 border-slate-300 text-slate-900"
                  placeholder="••••••••"
                />
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Billing Settings */}
      {activeTab === 'billing' && (
        <Card className="bg-slate-50/50 border-slate-200">
          <CardHeader>
            <CardTitle className="text-slate-900">Razorpay Configuration</CardTitle>
            <CardDescription className="text-slate-600">Configure payment gateway for subscriptions</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label className="text-slate-700">Razorpay Key ID</Label>
                <Input
                  value={settings.razorpay_key_id}
                  onChange={(e) => setSettings({ ...settings, razorpay_key_id: e.target.value })}
                  className="bg-slate-100 border-slate-300 text-slate-900"
                  placeholder="rzp_test_..."
                />
              </div>
              <div>
                <Label className="text-slate-700">Razorpay Key Secret</Label>
                <Input
                  type="password"
                  value={settings.razorpay_key_secret}
                  onChange={(e) => setSettings({ ...settings, razorpay_key_secret: e.target.value })}
                  className="bg-slate-100 border-slate-300 text-slate-900"
                  placeholder="••••••••"
                />
              </div>
            </div>
            
            <div className="p-4 bg-slate-100/30 rounded-lg">
              <p className="text-sm text-slate-600">
                Get your Razorpay API keys from{' '}
                <a href="https://dashboard.razorpay.com/app/keys" target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:text-purple-300">
                  dashboard.razorpay.com
                </a>
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Integrations Settings */}
      {activeTab === 'integrations' && (
        <div className="grid gap-6">
          <Card className="bg-slate-50/50 border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Analytics</CardTitle>
              <CardDescription className="text-slate-600">Configure analytics and tracking</CardDescription>
            </CardHeader>
            <CardContent>
              <div>
                <Label className="text-slate-700">Google Analytics ID</Label>
                <Input
                  value={settings.google_analytics_id}
                  onChange={(e) => setSettings({ ...settings, google_analytics_id: e.target.value })}
                  className="bg-slate-100 border-slate-300 text-slate-900"
                  placeholder="G-XXXXXXXXXX"
                />
              </div>
            </CardContent>
          </Card>

          <Card className="bg-slate-50/50 border-slate-200">
            <CardHeader>
              <CardTitle className="text-slate-900">Error Tracking</CardTitle>
              <CardDescription className="text-slate-600">Configure error tracking service</CardDescription>
            </CardHeader>
            <CardContent>
              <div>
                <Label className="text-slate-700">Sentry DSN</Label>
                <Input
                  value={settings.sentry_dsn}
                  onChange={(e) => setSettings({ ...settings, sentry_dsn: e.target.value })}
                  className="bg-slate-100 border-slate-300 text-slate-900"
                  placeholder="https://...@sentry.io/..."
                />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
