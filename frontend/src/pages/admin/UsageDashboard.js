import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import { 
  Building2, HardDrive, Users, Ticket, FileText, Wrench,
  TrendingUp, AlertTriangle, CheckCircle, ArrowRight, Zap
} from 'lucide-react';
import { Link } from 'react-router-dom';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const PLAN_LIMITS = {
  trial: { companies: 2, devices: 50, users: 5, tickets_per_month: 100 },
  starter: { companies: 5, devices: 100, users: 10, tickets_per_month: 500 },
  professional: { companies: 25, devices: 500, users: 50, tickets_per_month: 2000 },
  enterprise: { companies: -1, devices: -1, users: -1, tickets_per_month: -1 }
};

const PLAN_NAMES = {
  trial: 'Free Trial',
  starter: 'Starter',
  professional: 'Professional',
  enterprise: 'Enterprise'
};

export default function UsageDashboard() {
  const [loading, setLoading] = useState(true);
  const [usage, setUsage] = useState(null);
  const [organization, setOrganization] = useState(null);
  const token = localStorage.getItem('token');

  useEffect(() => {
    fetchUsage();
  }, []);

  const fetchUsage = async () => {
    try {
      const [usageRes, orgRes] = await Promise.all([
        axios.get(`${API}/api/org/usage`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/api/org/current`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setUsage(usageRes.data);
      setOrganization(orgRes.data);
    } catch (error) {
      toast.error('Failed to load usage data');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!usage || !organization) {
    return (
      <div className="p-6">
        <Card>
          <CardContent className="p-8 text-center">
            <AlertTriangle className="w-12 h-12 mx-auto text-amber-500 mb-4" />
            <h3 className="text-lg font-semibold mb-2">Usage Data Unavailable</h3>
            <p className="text-slate-500">Unable to load usage statistics. Please try again later.</p>
          </CardContent>
        </Card>
      </div>
    );
  }

  const plan = organization.subscription?.plan || 'trial';
  const limits = usage.limits || PLAN_LIMITS[plan] || {};
  const currentUsage = usage.usage || {};

  const UsageCard = ({ label, icon: Icon, current, max, color = 'blue' }) => {
    const isUnlimited = max === -1;
    const percentage = isUnlimited ? 0 : Math.min((current / max) * 100, 100);
    const isWarning = percentage > 70 && percentage <= 90;
    const isCritical = percentage > 90;

    const getStatusColor = () => {
      if (isUnlimited) return 'emerald';
      if (isCritical) return 'red';
      if (isWarning) return 'amber';
      return color;
    };

    const statusColor = getStatusColor();

    return (
      <Card className="relative overflow-hidden">
        <CardContent className="p-6">
          <div className="flex items-start justify-between mb-4">
            <div className={`p-3 rounded-xl bg-${statusColor}-100`}>
              <Icon className={`w-6 h-6 text-${statusColor}-600`} />
            </div>
            {!isUnlimited && isCritical && (
              <Badge variant="destructive" className="text-xs">
                Near Limit
              </Badge>
            )}
            {isUnlimited && (
              <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-700 border-emerald-200">
                Unlimited
              </Badge>
            )}
          </div>

          <div className="mb-3">
            <p className="text-sm text-slate-500 mb-1">{label}</p>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-bold text-slate-900">{current.toLocaleString()}</span>
              {!isUnlimited && (
                <span className="text-slate-400">/ {max.toLocaleString()}</span>
              )}
            </div>
          </div>

          {!isUnlimited && (
            <div className="space-y-2">
              <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  className={`h-full rounded-full transition-all duration-500 ${
                    isCritical ? 'bg-red-500' : 
                    isWarning ? 'bg-amber-500' : 
                    `bg-${color}-500`
                  }`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <p className="text-xs text-slate-400 text-right">
                {Math.round(percentage)}% used
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  const trialDaysRemaining = organization.subscription?.trial_ends_at 
    ? Math.max(0, Math.ceil((new Date(organization.subscription.trial_ends_at) - new Date()) / (1000 * 60 * 60 * 24)))
    : 0;

  return (
    <div className="p-6 max-w-6xl mx-auto space-y-6" data-testid="usage-dashboard">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Usage Dashboard</h1>
          <p className="text-slate-500">Monitor your organization's resource usage</p>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm text-slate-500">Current Plan</p>
            <p className="font-semibold text-slate-900">{PLAN_NAMES[plan] || plan}</p>
          </div>
          {plan !== 'enterprise' && (
            <Link to="/admin/organization">
              <Button>
                <Zap className="w-4 h-4 mr-2" />
                Upgrade
              </Button>
            </Link>
          )}
        </div>
      </div>

      {/* Trial Warning */}
      {plan === 'trial' && trialDaysRemaining <= 7 && (
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="p-4 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 text-amber-600" />
              <div>
                <p className="font-medium text-amber-800">
                  {trialDaysRemaining === 0 
                    ? 'Your trial has expired!' 
                    : `Your trial expires in ${trialDaysRemaining} day${trialDaysRemaining === 1 ? '' : 's'}`}
                </p>
                <p className="text-sm text-amber-700">Upgrade now to keep your data and continue using all features.</p>
              </div>
            </div>
            <Link to="/admin/organization">
              <Button className="bg-amber-600 hover:bg-amber-700">
                Upgrade Now
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </Link>
          </CardContent>
        </Card>
      )}

      {/* Usage Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        <UsageCard 
          label="Companies" 
          icon={Building2} 
          current={currentUsage.companies || 0} 
          max={limits.companies || 5}
          color="blue"
        />
        <UsageCard 
          label="Devices" 
          icon={HardDrive} 
          current={currentUsage.devices || 0} 
          max={limits.devices || 100}
          color="purple"
        />
        <UsageCard 
          label="Users" 
          icon={Users} 
          current={currentUsage.users || 0} 
          max={limits.users || 10}
          color="emerald"
        />
        <UsageCard 
          label="Tickets This Month" 
          icon={Ticket} 
          current={currentUsage.tickets_this_month || 0} 
          max={limits.tickets_per_month || 500}
          color="amber"
        />
      </div>

      {/* Plan Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-600" />
            Plan Comparison
          </CardTitle>
          <CardDescription>See what you could get with an upgraded plan</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Feature</th>
                  {Object.keys(PLAN_LIMITS).map(p => (
                    <th key={p} className={`text-center py-3 px-4 text-sm font-medium ${p === plan ? 'bg-blue-50 text-blue-700' : 'text-slate-600'}`}>
                      {PLAN_NAMES[p]}
                      {p === plan && <span className="block text-xs font-normal">(Current)</span>}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr className="border-b">
                  <td className="py-3 px-4 text-sm text-slate-700">Companies</td>
                  {Object.entries(PLAN_LIMITS).map(([p, l]) => (
                    <td key={p} className={`text-center py-3 px-4 text-sm ${p === plan ? 'bg-blue-50 font-medium' : ''}`}>
                      {l.companies === -1 ? '∞' : l.companies}
                    </td>
                  ))}
                </tr>
                <tr className="border-b">
                  <td className="py-3 px-4 text-sm text-slate-700">Devices</td>
                  {Object.entries(PLAN_LIMITS).map(([p, l]) => (
                    <td key={p} className={`text-center py-3 px-4 text-sm ${p === plan ? 'bg-blue-50 font-medium' : ''}`}>
                      {l.devices === -1 ? '∞' : l.devices}
                    </td>
                  ))}
                </tr>
                <tr className="border-b">
                  <td className="py-3 px-4 text-sm text-slate-700">Users</td>
                  {Object.entries(PLAN_LIMITS).map(([p, l]) => (
                    <td key={p} className={`text-center py-3 px-4 text-sm ${p === plan ? 'bg-blue-50 font-medium' : ''}`}>
                      {l.users === -1 ? '∞' : l.users}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="py-3 px-4 text-sm text-slate-700">Tickets/Month</td>
                  {Object.entries(PLAN_LIMITS).map(([p, l]) => (
                    <td key={p} className={`text-center py-3 px-4 text-sm ${p === plan ? 'bg-blue-50 font-medium' : ''}`}>
                      {l.tickets_per_month === -1 ? '∞' : l.tickets_per_month.toLocaleString()}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link to="/admin/companies" className="block">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Building2 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-slate-900">Manage Companies</p>
                <p className="text-sm text-slate-500">{currentUsage.companies || 0} companies</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link to="/admin/devices" className="block">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="p-3 bg-purple-100 rounded-lg">
                <HardDrive className="w-5 h-5 text-purple-600" />
              </div>
              <div>
                <p className="font-medium text-slate-900">Manage Devices</p>
                <p className="text-sm text-slate-500">{currentUsage.devices || 0} devices</p>
              </div>
            </CardContent>
          </Card>
        </Link>

        <Link to="/admin/tickets" className="block">
          <Card className="hover:shadow-md transition-shadow cursor-pointer">
            <CardContent className="p-4 flex items-center gap-4">
              <div className="p-3 bg-amber-100 rounded-lg">
                <Ticket className="w-5 h-5 text-amber-600" />
              </div>
              <div>
                <p className="font-medium text-slate-900">View Tickets</p>
                <p className="text-sm text-slate-500">{currentUsage.tickets_this_month || 0} this month</p>
              </div>
            </CardContent>
          </Card>
        </Link>
      </div>
    </div>
  );
}
