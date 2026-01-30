import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import { Building2, Users, HardDrive, Ticket, Settings, CreditCard, Shield, Palette } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const PLAN_BADGES = {
  trial: { label: 'Trial', variant: 'outline' },
  starter: { label: 'Starter', variant: 'secondary' },
  professional: { label: 'Professional', variant: 'default' },
  enterprise: { label: 'Enterprise', variant: 'destructive' }
};

export default function OrganizationSettings() {
  const [organization, setOrganization] = useState(null);
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchOrganization();
    fetchPlans();
  }, []);

  const fetchOrganization = async () => {
    try {
      const response = await axios.get(`${API}/api/org/current`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOrganization(response.data);
    } catch (error) {
      // If no org context, might be legacy admin
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

  const handleUpgrade = async (planId) => {
    try {
      await axios.post(`${API}/api/org/subscription/upgrade`, 
        { plan: planId },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Plan upgraded successfully!');
      fetchOrganization();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to upgrade plan');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
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
              Please contact support for assistance.
            </p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const plan = organization.subscription?.plan || 'trial';
  const limits = organization.plan_limits || {};
  const usage = organization.usage || {};

  const tabs = [
    { id: 'overview', label: 'Overview', icon: Building2 },
    { id: 'billing', label: 'Billing', icon: CreditCard },
    { id: 'branding', label: 'Branding', icon: Palette },
    { id: 'settings', label: 'Settings', icon: Settings },
  ];

  const UsageCard = ({ label, icon: Icon, current, max }) => {
    const isUnlimited = max === -1;
    const percentage = isUnlimited ? 0 : (current / max) * 100;
    const isWarning = percentage > 80;
    const isCritical = percentage > 95;

    return (
      <div className="bg-white rounded-lg border p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className={`p-2 rounded-lg ${isCritical ? 'bg-red-100' : isWarning ? 'bg-amber-100' : 'bg-blue-100'}`}>
            <Icon className={`w-5 h-5 ${isCritical ? 'text-red-600' : isWarning ? 'text-amber-600' : 'text-blue-600'}`} />
          </div>
          <span className="font-medium text-slate-700">{label}</span>
        </div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-slate-900">{current}</span>
          <span className="text-slate-500">/ {isUnlimited ? '∞' : max}</span>
        </div>
        {!isUnlimited && (
          <div className="mt-2 bg-slate-200 rounded-full h-2 overflow-hidden">
            <div 
              className={`h-full transition-all ${
                isCritical ? 'bg-red-500' : isWarning ? 'bg-amber-500' : 'bg-blue-500'
              }`}
              style={{ width: `${Math.min(percentage, 100)}%` }}
            />
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="p-6 max-w-6xl mx-auto" data-testid="organization-settings">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{organization.name}</h1>
          <p className="text-slate-500">{organization.slug}.yourportal.com</p>
        </div>
        <Badge 
          variant={PLAN_BADGES[plan]?.variant || 'outline'}
          className="text-sm px-3 py-1"
        >
          {PLAN_BADGES[plan]?.label || plan}
        </Badge>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 border-b-2 transition-colors ${
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

      {/* Tab Content */}
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Usage Stats */}
          <div>
            <h3 className="text-lg font-semibold mb-4">Usage</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              <UsageCard 
                label="Companies" 
                icon={Building2} 
                current={usage.companies || 0} 
                max={limits.companies || 5} 
              />
              <UsageCard 
                label="Devices" 
                icon={HardDrive} 
                current={usage.devices || 0} 
                max={limits.devices || 100} 
              />
              <UsageCard 
                label="Users" 
                icon={Users} 
                current={usage.users || 0} 
                max={limits.users || 10} 
              />
              <UsageCard 
                label="Tickets/Month" 
                icon={Ticket} 
                current={organization.subscription?.tickets_this_month || 0} 
                max={limits.tickets_per_month || 500} 
              />
            </div>
          </div>

          {/* Quick Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Organization Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-500">Status</span>
                  <Badge variant={organization.status === 'active' ? 'default' : 'secondary'}>
                    {organization.status}
                  </Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Owner</span>
                  <span>{organization.owner_email}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Created</span>
                  <span>{new Date(organization.created_at).toLocaleDateString()}</span>
                </div>
                {organization.industry && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Industry</span>
                    <span>{organization.industry}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base">Subscription</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-500">Current Plan</span>
                  <span className="font-medium">{PLAN_BADGES[plan]?.label}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Billing Cycle</span>
                  <span className="capitalize">{organization.subscription?.billing_cycle || 'monthly'}</span>
                </div>
                {organization.subscription?.current_period_end && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Renews On</span>
                    <span>{new Date(organization.subscription.current_period_end).toLocaleDateString()}</span>
                  </div>
                )}
                {plan === 'trial' && organization.subscription?.trial_ends_at && (
                  <div className="mt-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                    <p className="text-sm text-amber-700">
                      <strong>Trial ends:</strong> {new Date(organization.subscription.trial_ends_at).toLocaleDateString()}
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {activeTab === 'billing' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Subscription Plans</CardTitle>
              <CardDescription>Choose the plan that best fits your needs</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {plans.map(p => {
                  const isCurrent = p.id === plan;
                  const isEnterprise = p.id === 'enterprise';
                  
                  return (
                    <div 
                      key={p.id}
                      className={`p-4 rounded-lg border-2 transition-all ${
                        isCurrent ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <h4 className="font-semibold text-lg">{p.name}</h4>
                      <div className="mt-2 mb-4">
                        {p.price_monthly ? (
                          <>
                            <span className="text-2xl font-bold">₹{p.price_monthly.toLocaleString()}</span>
                            <span className="text-slate-500">/month</span>
                          </>
                        ) : (
                          <span className="text-lg font-medium text-slate-600">
                            {p.id === 'trial' ? 'Free' : 'Contact Sales'}
                          </span>
                        )}
                      </div>
                      
                      <ul className="space-y-2 text-sm text-slate-600 mb-4">
                        <li>• {p.limits?.companies === -1 ? 'Unlimited' : p.limits?.companies} Companies</li>
                        <li>• {p.limits?.devices === -1 ? 'Unlimited' : p.limits?.devices} Devices</li>
                        <li>• {p.limits?.users === -1 ? 'Unlimited' : p.limits?.users} Users</li>
                      </ul>

                      {isCurrent ? (
                        <Badge className="w-full justify-center py-2">Current Plan</Badge>
                      ) : isEnterprise ? (
                        <Button variant="outline" className="w-full" disabled>
                          Contact Sales
                        </Button>
                      ) : (
                        <Button 
                          className="w-full"
                          onClick={() => handleUpgrade(p.id)}
                          disabled={p.id === 'trial'}
                        >
                          {p.id === 'trial' ? 'Free Trial' : 'Upgrade'}
                        </Button>
                      )}
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {activeTab === 'branding' && (
        <Card>
          <CardHeader>
            <CardTitle>Branding Settings</CardTitle>
            <CardDescription>Customize your portal's appearance</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">Accent Color</label>
                <div className="flex items-center gap-3">
                  <input 
                    type="color" 
                    value={organization.branding?.accent_color || '#0F62FE'}
                    className="w-10 h-10 rounded cursor-pointer"
                    onChange={(e) => {
                      // TODO: Implement update
                    }}
                  />
                  <span className="text-slate-500">{organization.branding?.accent_color || '#0F62FE'}</span>
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Company Name (Display)</label>
                <input 
                  type="text"
                  className="form-input"
                  defaultValue={organization.branding?.company_name || organization.name}
                  placeholder="Your Company Name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Logo</label>
                <div className="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center">
                  {organization.branding?.logo_url ? (
                    <img src={organization.branding.logo_url} alt="Logo" className="max-h-20 mx-auto" />
                  ) : (
                    <p className="text-slate-500">Click to upload logo</p>
                  )}
                </div>
              </div>

              <Button className="mt-4">Save Branding</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {activeTab === 'settings' && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>General Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Timezone</label>
                  <select className="form-input" defaultValue={organization.settings?.timezone || 'Asia/Kolkata'}>
                    <option value="Asia/Kolkata">Asia/Kolkata (IST)</option>
                    <option value="America/New_York">America/New_York (EST)</option>
                    <option value="Europe/London">Europe/London (GMT)</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Date Format</label>
                  <select className="form-input" defaultValue={organization.settings?.date_format || 'DD/MM/YYYY'}>
                    <option value="DD/MM/YYYY">DD/MM/YYYY</option>
                    <option value="MM/DD/YYYY">MM/DD/YYYY</option>
                    <option value="YYYY-MM-DD">YYYY-MM-DD</option>
                  </select>
                </div>
              </div>
              <Button>Save Settings</Button>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Shield className="w-5 h-5" />
                Feature Toggles
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {[
                  { key: 'enable_public_portal', label: 'Public Portal', desc: 'Allow warranty lookups without login' },
                  { key: 'enable_qr_codes', label: 'QR Code Generation', desc: 'Generate QR codes for devices' },
                  { key: 'enable_ai_features', label: 'AI Features', desc: 'AI-powered triage and suggestions' },
                  { key: 'enable_email_ticketing', label: 'Email Ticketing', desc: 'Create tickets from emails' }
                ].map(feature => (
                  <div key={feature.key} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                    <div>
                      <p className="font-medium">{feature.label}</p>
                      <p className="text-sm text-slate-500">{feature.desc}</p>
                    </div>
                    <label className="relative inline-flex items-center cursor-pointer">
                      <input 
                        type="checkbox" 
                        className="sr-only peer"
                        defaultChecked={organization.settings?.[feature.key]}
                      />
                      <div className="w-11 h-6 bg-slate-300 peer-focus:ring-2 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                    </label>
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
