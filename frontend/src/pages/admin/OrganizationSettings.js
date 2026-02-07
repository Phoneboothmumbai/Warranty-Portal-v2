import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Switch } from '../../components/ui/switch';
import { toast } from 'sonner';
import { 
  Building2, Users, HardDrive, Ticket, Settings, CreditCard, Shield, Palette,
  Upload, Globe, Mail, Image, Eye, Loader2, CheckCircle, AlertCircle, UserCog, ChevronRight,
  Wrench, FileText, MailCheck
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const PLAN_BADGES = {
  trial: { label: 'Trial', variant: 'outline' },
  starter: { label: 'Starter', variant: 'secondary' },
  professional: { label: 'Professional', variant: 'default' },
  enterprise: { label: 'Enterprise', variant: 'destructive' }
};

export default function OrganizationSettings() {
  const navigate = useNavigate();
  const [organization, setOrganization] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [branding, setBranding] = useState({
    company_name: '',
    logo_url: '',
    logo_base64: '',
    accent_color: '#0F62FE',
    favicon_url: '',
    custom_domain: '',
    support_email: '',
    footer_text: '',
    hide_powered_by: false,
    custom_css: ''
  });
  const [emailSettings, setEmailSettings] = useState({
    email_from_name: '',
    email_from_address: '',
    smtp_host: '',
    smtp_port: 587,
    smtp_username: '',
    smtp_password: '',
    imap_host: '',
    imap_port: 993,
    imap_username: '',
    imap_password: ''
  });
  const logoInputRef = useRef(null);
  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchOrganization();
    fetchPlans();
  }, []);

  const fetchOrganization = async () => {
    try {
      const response = await axios.get(`${API}/api/org/current`, { headers });
      setOrganization(response.data);
      
      // Populate branding form
      if (response.data.branding) {
        setBranding(prev => ({ ...prev, ...response.data.branding }));
      }
      if (response.data.settings) {
        setEmailSettings(prev => ({ ...prev, ...response.data.settings }));
      }
    } catch (error) {
      if (error.response?.data?.is_legacy_admin) {
        toast.info('Please migrate to the organization model for full features');
      } else {
        toast.error('Failed to load organization');
      }
    } finally {
      setLoading(false);
    }
  };

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/api/org/plans`);
      setPlans(response.data);
    } catch (error) {
      console.error('Failed to fetch plans');
    }
  };

  const handleLogoUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      toast.error('Please upload an image file');
      return;
    }

    if (file.size > 2 * 1024 * 1024) {
      toast.error('Logo must be less than 2MB');
      return;
    }

    const reader = new FileReader();
    reader.onloadend = () => {
      setBranding(prev => ({ ...prev, logo_base64: reader.result }));
    };
    reader.readAsDataURL(file);
  };

  const saveBranding = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/api/org/current/branding`, branding, { headers });
      toast.success('Branding settings saved');
      fetchOrganization();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save branding');
    } finally {
      setSaving(false);
    }
  };

  const saveEmailSettings = async () => {
    setSaving(true);
    try {
      await axios.put(`${API}/api/org/current/settings`, emailSettings, { headers });
      toast.success('Email settings saved');
      fetchOrganization();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  if (!organization) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-6 text-center">
            <Building2 className="w-12 h-12 mx-auto text-slate-400 mb-4" />
            <h3 className="text-lg font-medium">Organization Not Found</h3>
            <p className="text-slate-500 mt-2">
              Your account hasn't been migrated to the new multi-tenant model yet.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const plan = organization.subscription?.plan || 'trial';
  const limits = organization.plan_limits || {};
  const usage = organization.usage || {};
  const isPremium = ['professional', 'enterprise'].includes(plan);

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Building2 },
    { id: 'team', label: 'Staff & Technicians', icon: UserCog },
    { id: 'branding', label: 'White Label', icon: Palette },
    { id: 'email', label: 'Email Config', icon: Mail },
    { id: 'billing', label: 'Billing', icon: CreditCard },
  ];

  return (
    <div className="p-6 max-w-6xl mx-auto" data-testid="organization-settings">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{organization.name}</h1>
          <p className="text-slate-500">{organization.slug}.yourportal.com</p>
        </div>
        <Badge variant={PLAN_BADGES[plan]?.variant || 'outline'} className="text-sm px-3 py-1">
          {PLAN_BADGES[plan]?.label || plan}
        </Badge>
      </div>

      {/* Tabs */}
      <div className="flex border-b mb-6">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            <tab.icon className="w-4 h-4" />
            {tab.label}
          </button>
        ))}
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Building2 className="w-5 h-5 text-blue-500" />
                  <span className="text-sm text-slate-600">Clients</span>
                </div>
                <div className="text-2xl font-bold">{usage.companies || 0} / {limits.max_companies === -1 ? '∞' : limits.max_companies}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <HardDrive className="w-5 h-5 text-emerald-500" />
                  <span className="text-sm text-slate-600">Devices</span>
                </div>
                <div className="text-2xl font-bold">{usage.devices || 0} / {limits.max_devices === -1 ? '∞' : limits.max_devices}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Users className="w-5 h-5 text-purple-500" />
                  <span className="text-sm text-slate-600">Users</span>
                </div>
                <div className="text-2xl font-bold">{usage.users || 0} / {limits.max_users === -1 ? '∞' : limits.max_users}</div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center gap-3 mb-2">
                  <Ticket className="w-5 h-5 text-amber-500" />
                  <span className="text-sm text-slate-600">Tickets/mo</span>
                </div>
                <div className="text-2xl font-bold">{usage.tickets_this_month || 0} / {limits.max_tickets_per_month === -1 ? '∞' : limits.max_tickets_per_month}</div>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader>
              <CardTitle>Organization Details</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-slate-500">Organization ID</Label>
                  <p className="font-mono text-sm">{organization.id}</p>
                </div>
                <div>
                  <Label className="text-slate-500">Created</Label>
                  <p>{new Date(organization.created_at).toLocaleDateString()}</p>
                </div>
                <div>
                  <Label className="text-slate-500">Status</Label>
                  <Badge variant={organization.status === 'active' ? 'default' : 'secondary'}>
                    {organization.status}
                  </Badge>
                </div>
                <div>
                  <Label className="text-slate-500">Plan</Label>
                  <p className="capitalize">{plan}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Staff & Technicians Tab */}
      {activeTab === 'team' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <UserCog className="w-5 h-5" />
                Staff & Technicians
              </CardTitle>
              <CardDescription>
                Manage your organization's staff members, technicians, roles and permissions
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div 
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate('/admin/staff')}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                      <Users className="w-5 h-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">Staff Management</h3>
                      <p className="text-sm text-slate-500">Add and manage staff members, technicians, and engineers</p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400" />
                </div>
                
                <div 
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate('/admin/staff?tab=roles')}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                      <Shield className="w-5 h-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">Roles & Permissions</h3>
                      <p className="text-sm text-slate-500">Configure roles and access permissions for your team</p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400" />
                </div>
                
                <div 
                  className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => navigate('/admin/staff?tab=departments')}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                      <Building2 className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">Departments</h3>
                      <p className="text-sm text-slate-500">Organize staff into departments and teams</p>
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-slate-400" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* White Label Tab */}
      {activeTab === 'branding' && (
        <div className="space-y-6">
          {!isPremium && (
            <Card className="border-amber-200 bg-amber-50">
              <CardContent className="p-4 flex items-center gap-3">
                <AlertCircle className="w-5 h-5 text-amber-600" />
                <div>
                  <p className="font-medium text-amber-800">White-label features require Professional or Enterprise plan</p>
                  <p className="text-sm text-amber-600">Upgrade to customize branding for your clients</p>
                </div>
                <Button size="sm" className="ml-auto">Upgrade</Button>
              </CardContent>
            </Card>
          )}

          {/* Logo & Identity */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Image className="w-5 h-5" />
                Logo & Identity
              </CardTitle>
              <CardDescription>Customize how your portal appears to clients</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="flex items-start gap-6">
                <div className="flex-shrink-0">
                  <div className="w-24 h-24 rounded-xl border-2 border-dashed border-slate-300 flex items-center justify-center bg-slate-50 overflow-hidden">
                    {branding.logo_base64 || branding.logo_url ? (
                      <img 
                        src={branding.logo_base64 || branding.logo_url} 
                        alt="Logo" 
                        className="w-full h-full object-contain"
                      />
                    ) : (
                      <Building2 className="w-8 h-8 text-slate-400" />
                    )}
                  </div>
                  <input
                    ref={logoInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleLogoUpload}
                    className="hidden"
                  />
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="mt-2 w-24"
                    onClick={() => logoInputRef.current?.click()}
                    disabled={!isPremium}
                  >
                    <Upload className="w-4 h-4 mr-1" />
                    Upload
                  </Button>
                </div>
                <div className="flex-1 space-y-4">
                  <div>
                    <Label htmlFor="company_name">Display Name</Label>
                    <Input
                      id="company_name"
                      value={branding.company_name}
                      onChange={e => setBranding({...branding, company_name: e.target.value})}
                      placeholder="Your Company Name"
                      disabled={!isPremium}
                    />
                    <p className="text-xs text-slate-500 mt-1">Shown in the header and emails</p>
                  </div>
                  <div>
                    <Label htmlFor="accent_color">Brand Color</Label>
                    <div className="flex items-center gap-2">
                      <input
                        type="color"
                        id="accent_color"
                        value={branding.accent_color || '#0F62FE'}
                        onChange={e => setBranding({...branding, accent_color: e.target.value})}
                        className="w-10 h-10 rounded cursor-pointer border"
                        disabled={!isPremium}
                      />
                      <Input
                        value={branding.accent_color || '#0F62FE'}
                        onChange={e => setBranding({...branding, accent_color: e.target.value})}
                        className="w-32 font-mono"
                        disabled={!isPremium}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Custom Domain */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="w-5 h-5" />
                Custom Domain
              </CardTitle>
              <CardDescription>Use your own domain for the client portal</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="custom_domain">Domain Name</Label>
                <Input
                  id="custom_domain"
                  value={branding.custom_domain}
                  onChange={e => setBranding({...branding, custom_domain: e.target.value})}
                  placeholder="support.yourdomain.com"
                  disabled={!isPremium}
                />
                <p className="text-xs text-slate-500 mt-1">
                  Add a CNAME record pointing to <code className="bg-slate-100 px-1 rounded">portal.assetvault.io</code>
                </p>
              </div>
              <div>
                <Label htmlFor="support_email">Support Email</Label>
                <Input
                  id="support_email"
                  type="email"
                  value={branding.support_email}
                  onChange={e => setBranding({...branding, support_email: e.target.value})}
                  placeholder="support@yourdomain.com"
                  disabled={!isPremium}
                />
              </div>
            </CardContent>
          </Card>

          {/* Advanced Branding */}
          <Card>
            <CardHeader>
              <CardTitle>Advanced Branding</CardTitle>
              <CardDescription>Additional customization options</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label htmlFor="footer_text">Custom Footer Text</Label>
                <Input
                  id="footer_text"
                  value={branding.footer_text}
                  onChange={e => setBranding({...branding, footer_text: e.target.value})}
                  placeholder="© 2025 Your Company. All rights reserved."
                  disabled={!isPremium}
                />
              </div>
              <div className="flex items-center justify-between">
                <div>
                  <Label>Hide "Powered by AssetVault"</Label>
                  <p className="text-xs text-slate-500">Remove branding from client portal footer</p>
                </div>
                <Switch
                  checked={branding.hide_powered_by}
                  onCheckedChange={v => setBranding({...branding, hide_powered_by: v})}
                  disabled={!isPremium}
                />
              </div>
              <div>
                <Label htmlFor="custom_css">Custom CSS</Label>
                <Textarea
                  id="custom_css"
                  value={branding.custom_css}
                  onChange={e => setBranding({...branding, custom_css: e.target.value})}
                  placeholder=".custom-header { background: #your-color; }"
                  rows={4}
                  className="font-mono text-sm"
                  disabled={!isPremium}
                />
                <p className="text-xs text-slate-500 mt-1">Advanced: Add custom CSS to override portal styles</p>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={saveBranding} disabled={saving || !isPremium}>
              {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              Save Branding Settings
            </Button>
          </div>
        </div>
      )}

      {/* Email Config Tab */}
      {activeTab === 'email' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Mail className="w-5 h-5" />
                Email Sender Settings
              </CardTitle>
              <CardDescription>Configure how emails are sent to your clients</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="email_from_name">From Name</Label>
                  <Input
                    id="email_from_name"
                    value={emailSettings.email_from_name}
                    onChange={e => setEmailSettings({...emailSettings, email_from_name: e.target.value})}
                    placeholder="Your Company Support"
                  />
                </div>
                <div>
                  <Label htmlFor="email_from_address">From Email</Label>
                  <Input
                    id="email_from_address"
                    type="email"
                    value={emailSettings.email_from_address}
                    onChange={e => setEmailSettings({...emailSettings, email_from_address: e.target.value})}
                    placeholder="support@yourdomain.com"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>SMTP Configuration</CardTitle>
              <CardDescription>Outgoing email server settings</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="smtp_host">SMTP Host</Label>
                  <Input
                    id="smtp_host"
                    value={emailSettings.smtp_host}
                    onChange={e => setEmailSettings({...emailSettings, smtp_host: e.target.value})}
                    placeholder="smtp.gmail.com"
                  />
                </div>
                <div>
                  <Label htmlFor="smtp_port">SMTP Port</Label>
                  <Input
                    id="smtp_port"
                    type="number"
                    value={emailSettings.smtp_port}
                    onChange={e => setEmailSettings({...emailSettings, smtp_port: parseInt(e.target.value)})}
                    placeholder="587"
                  />
                </div>
                <div>
                  <Label htmlFor="smtp_username">Username</Label>
                  <Input
                    id="smtp_username"
                    value={emailSettings.smtp_username}
                    onChange={e => setEmailSettings({...emailSettings, smtp_username: e.target.value})}
                    placeholder="your-email@gmail.com"
                  />
                </div>
                <div>
                  <Label htmlFor="smtp_password">Password / App Password</Label>
                  <Input
                    id="smtp_password"
                    type="password"
                    value={emailSettings.smtp_password}
                    onChange={e => setEmailSettings({...emailSettings, smtp_password: e.target.value})}
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>IMAP Configuration</CardTitle>
              <CardDescription>Incoming email server for email-to-ticket</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="imap_host">IMAP Host</Label>
                  <Input
                    id="imap_host"
                    value={emailSettings.imap_host}
                    onChange={e => setEmailSettings({...emailSettings, imap_host: e.target.value})}
                    placeholder="imap.gmail.com"
                  />
                </div>
                <div>
                  <Label htmlFor="imap_port">IMAP Port</Label>
                  <Input
                    id="imap_port"
                    type="number"
                    value={emailSettings.imap_port}
                    onChange={e => setEmailSettings({...emailSettings, imap_port: parseInt(e.target.value)})}
                    placeholder="993"
                  />
                </div>
                <div>
                  <Label htmlFor="imap_username">Username</Label>
                  <Input
                    id="imap_username"
                    value={emailSettings.imap_username}
                    onChange={e => setEmailSettings({...emailSettings, imap_username: e.target.value})}
                    placeholder="your-email@gmail.com"
                  />
                </div>
                <div>
                  <Label htmlFor="imap_password">Password / App Password</Label>
                  <Input
                    id="imap_password"
                    type="password"
                    value={emailSettings.imap_password}
                    onChange={e => setEmailSettings({...emailSettings, imap_password: e.target.value})}
                    placeholder="••••••••"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={saveEmailSettings} disabled={saving}>
              {saving ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <CheckCircle className="w-4 h-4 mr-2" />}
              Save Email Settings
            </Button>
          </div>
        </div>
      )}

      {/* Billing Tab */}
      {activeTab === 'billing' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Current Plan</CardTitle>
              <CardDescription>Your subscription details</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div>
                  <h3 className="text-lg font-semibold capitalize">{plan} Plan</h3>
                  <p className="text-slate-500">
                    {plan === 'trial' && organization.subscription?.trial_ends_at && (
                      <>Trial ends: {new Date(organization.subscription.trial_ends_at).toLocaleDateString()}</>
                    )}
                    {plan !== 'trial' && 'Active subscription'}
                  </p>
                </div>
                <Button variant="outline">Manage Subscription</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Available Plans</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-3 gap-4">
                {plans.filter(p => p.id !== 'trial').map(p => (
                  <div 
                    key={p.id}
                    className={`p-4 rounded-lg border-2 ${
                      p.id === plan ? 'border-blue-500 bg-blue-50' : 'border-slate-200'
                    }`}
                  >
                    <h4 className="font-semibold">{p.name}</h4>
                    <p className="text-2xl font-bold mt-2">
                      {p.price === 0 ? 'Free' : `₹${p.price?.toLocaleString()}`}
                      <span className="text-sm font-normal text-slate-500">/mo</span>
                    </p>
                    <ul className="mt-4 space-y-2 text-sm text-slate-600">
                      <li>• {p.limits?.max_companies === -1 ? 'Unlimited' : p.limits?.max_companies} clients</li>
                      <li>• {p.limits?.max_devices === -1 ? 'Unlimited' : p.limits?.max_devices} devices</li>
                      <li>• {p.limits?.max_users === -1 ? 'Unlimited' : p.limits?.max_users} users</li>
                    </ul>
                    {p.id !== plan && (
                      <Button className="w-full mt-4" size="sm">
                        {plans.findIndex(x => x.id === p.id) > plans.findIndex(x => x.id === plan) ? 'Upgrade' : 'Downgrade'}
                      </Button>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
