import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import { 
  DollarSign, TrendingUp, TrendingDown, Calendar, CreditCard,
  Building2, RefreshCw, Loader2, Download, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const PLAN_PRICES = {
  trial: 0,
  starter: 2999,
  professional: 7999,
  enterprise: 19999
};

export default function PlatformBilling() {
  const [stats, setStats] = useState(null);
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedPeriod, setSelectedPeriod] = useState('month');
  
  const token = localStorage.getItem('platformToken');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, orgsRes] = await Promise.all([
        axios.get(`${API}/api/platform/dashboard/stats`, { headers }),
        axios.get(`${API}/api/platform/organizations?limit=100`, { headers })
      ]);
      
      setStats(statsRes.data);
      setOrganizations(orgsRes.data.organizations || []);
    } catch (error) {
      toast.error('Failed to load billing data');
    } finally {
      setLoading(false);
    }
  };

  // Calculate MRR
  const calculateMRR = () => {
    return organizations.reduce((total, org) => {
      const plan = org.subscription?.plan || 'trial';
      if (org.status === 'active' || org.status === 'trial') {
        return total + (PLAN_PRICES[plan] || 0);
      }
      return total;
    }, 0);
  };

  // Calculate by plan
  const getRevenueByPlan = () => {
    const revenue = {};
    organizations.forEach(org => {
      const plan = org.subscription?.plan || 'trial';
      if (org.status === 'active') {
        revenue[plan] = (revenue[plan] || 0) + (PLAN_PRICES[plan] || 0);
      }
    });
    return revenue;
  };

  const mrr = calculateMRR();
  const arr = mrr * 12;
  const revenueByPlan = getRevenueByPlan();
  const paidOrgs = organizations.filter(o => o.subscription?.plan && o.subscription.plan !== 'trial' && o.status === 'active').length;
  const trialOrgs = organizations.filter(o => o.status === 'trial').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="platform-billing">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Revenue & Billing</h1>
          <p className="text-slate-400">Platform revenue analytics and subscription overview</p>
        </div>
        <Button onClick={fetchData} variant="outline" className="border-slate-600 text-slate-300">
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border-emerald-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-emerald-400 text-sm font-medium">Monthly Revenue (MRR)</span>
              <div className="p-2 rounded-lg bg-emerald-500/20">
                <DollarSign className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-white">₹{mrr.toLocaleString()}</p>
            <div className="flex items-center gap-1 mt-2 text-emerald-400 text-sm">
              <TrendingUp className="w-4 h-4" />
              <span>Active subscriptions</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-purple-500/20 to-purple-600/10 border-purple-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-purple-400 text-sm font-medium">Annual Revenue (ARR)</span>
              <div className="p-2 rounded-lg bg-purple-500/20">
                <Calendar className="w-5 h-5 text-purple-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-white">₹{arr.toLocaleString()}</p>
            <div className="flex items-center gap-1 mt-2 text-purple-400 text-sm">
              <span>Projected annual revenue</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-blue-400 text-sm font-medium">Paying Customers</span>
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Building2 className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-white">{paidOrgs}</p>
            <div className="flex items-center gap-1 mt-2 text-blue-400 text-sm">
              <span>Active paid subscriptions</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 border-amber-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-amber-400 text-sm font-medium">Trial Organizations</span>
              <div className="p-2 rounded-lg bg-amber-500/20">
                <CreditCard className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-white">{trialOrgs}</p>
            <div className="flex items-center gap-1 mt-2 text-amber-400 text-sm">
              <span>Potential conversions</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Revenue Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-400" />
              Revenue by Plan
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(PLAN_PRICES).filter(([plan]) => plan !== 'trial').map(([plan, price]) => {
                const count = organizations.filter(o => o.subscription?.plan === plan && o.status === 'active').length;
                const revenue = count * price;
                const percentage = mrr > 0 ? (revenue / mrr * 100) : 0;
                
                return (
                  <div key={plan} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-white capitalize font-medium">{plan}</span>
                        <span className="text-slate-400 text-sm">({count} orgs)</span>
                      </div>
                      <span className="text-white font-semibold">₹{revenue.toLocaleString()}</span>
                    </div>
                    <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-gradient-to-r from-purple-500 to-purple-600 rounded-full transition-all duration-500"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <Building2 className="w-5 h-5 text-purple-400" />
              Organization Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Object.entries(stats?.organizations_by_status || {}).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between p-3 bg-slate-700/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      status === 'active' ? 'bg-emerald-500' :
                      status === 'trial' ? 'bg-blue-500' :
                      status === 'suspended' ? 'bg-red-500' :
                      status === 'past_due' ? 'bg-amber-500' :
                      'bg-slate-500'
                    }`} />
                    <span className="text-white capitalize">{status.replace('_', ' ')}</span>
                  </div>
                  <span className="text-xl font-bold text-white">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Subscriptions */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <CreditCard className="w-5 h-5 text-purple-400" />
            All Subscriptions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Organization</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Plan</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Monthly Value</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Created</th>
                </tr>
              </thead>
              <tbody>
                {organizations.slice(0, 20).map(org => {
                  const plan = org.subscription?.plan || 'trial';
                  const price = PLAN_PRICES[plan] || 0;
                  
                  return (
                    <tr key={org.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-3 px-4">
                        <p className="text-white font-medium">{org.name}</p>
                        <p className="text-xs text-slate-400">{org.owner_email}</p>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          plan === 'enterprise' ? 'bg-amber-500/20 text-amber-400' :
                          plan === 'professional' ? 'bg-purple-500/20 text-purple-400' :
                          plan === 'starter' ? 'bg-blue-500/20 text-blue-400' :
                          'bg-slate-500/20 text-slate-400'
                        }`}>
                          {plan.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded text-xs font-medium ${
                          org.status === 'active' ? 'bg-emerald-500/20 text-emerald-400' :
                          org.status === 'trial' ? 'bg-blue-500/20 text-blue-400' :
                          org.status === 'suspended' ? 'bg-red-500/20 text-red-400' :
                          'bg-slate-500/20 text-slate-400'
                        }`}>
                          {org.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-white font-medium">
                        ₹{price.toLocaleString()}
                      </td>
                      <td className="py-3 px-4 text-slate-400 text-sm">
                        {new Date(org.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
