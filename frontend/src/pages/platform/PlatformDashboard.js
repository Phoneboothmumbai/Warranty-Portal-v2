import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { 
  Building2, HardDrive, Users, Ticket, TrendingUp, AlertCircle, Clock,
  DollarSign, Calendar, ArrowUpRight, UserPlus, RefreshCw, ChevronRight,
  CreditCard, Target, Activity
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_COLORS = {
  trial: 'bg-blue-500/20 text-blue-400',
  active: 'bg-emerald-500/20 text-emerald-400',
  past_due: 'bg-amber-500/20 text-amber-400',
  suspended: 'bg-red-500/20 text-red-400',
  cancelled: 'bg-slate-500/20 text-slate-600',
  churned: 'bg-slate-600/20 text-slate-500'
};

const PLAN_COLORS = {
  trial: 'bg-slate-500/20 text-slate-600',
  starter: 'bg-blue-500/20 text-blue-400',
  professional: 'bg-blue-100 text-blue-600',
  enterprise: 'bg-amber-500/20 text-amber-400'
};

export default function PlatformDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('platformToken');
  const navigate = useNavigate();

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/api/platform/dashboard/stats`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="platform-dashboard">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Platform Dashboard</h1>
          <p className="text-slate-600">Overview of all tenants and platform health</p>
        </div>
        <Button 
          onClick={fetchStats} 
          variant="outline" 
          className="border-slate-300 text-slate-700 hover:bg-slate-100"
          data-testid="refresh-stats-btn"
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Revenue Metrics - Top Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-emerald-500/20 to-emerald-600/10 border-emerald-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-emerald-400 text-sm font-medium">Monthly Revenue</span>
              <div className="p-2 rounded-lg bg-emerald-500/20">
                <DollarSign className="w-5 h-5 text-emerald-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-slate-900">₹{stats?.revenue?.mrr?.toLocaleString() || 0}</p>
            <div className="flex items-center gap-1 mt-2 text-emerald-400 text-sm">
              <TrendingUp className="w-4 h-4" />
              <span>MRR from active subscriptions</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-blue-600 text-sm font-medium">Annual Revenue</span>
              <div className="p-2 rounded-lg bg-blue-100">
                <Calendar className="w-5 h-5 text-blue-600" />
              </div>
            </div>
            <p className="text-3xl font-bold text-slate-900">₹{stats?.revenue?.arr?.toLocaleString() || 0}</p>
            <div className="flex items-center gap-1 mt-2 text-blue-600 text-sm">
              <span>Projected ARR</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-blue-500/20 to-blue-600/10 border-blue-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-blue-400 text-sm font-medium">New This Month</span>
              <div className="p-2 rounded-lg bg-blue-500/20">
                <UserPlus className="w-5 h-5 text-blue-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-slate-900">{stats?.growth?.new_this_month || 0}</p>
            <div className="flex items-center gap-1 mt-2 text-blue-400 text-sm">
              <ArrowUpRight className="w-4 h-4" />
              <span>New signups</span>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-500/20 to-amber-600/10 border-amber-500/30">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-amber-400 text-sm font-medium">Conversion Rate</span>
              <div className="p-2 rounded-lg bg-amber-500/20">
                <Target className="w-5 h-5 text-amber-400" />
              </div>
            </div>
            <p className="text-3xl font-bold text-slate-900">{stats?.growth?.trial_conversion_rate || 0}%</p>
            <div className="flex items-center gap-1 mt-2 text-amber-400 text-sm">
              <span>Trial to paid</span>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Platform Stats - Second Row */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Card className="bg-slate-50/50 border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <Building2 className="w-5 h-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.totals?.organizations || 0}</p>
                <p className="text-sm text-slate-600">Organizations</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-50/50 border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-500/20">
                <Building2 className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.totals?.companies || 0}</p>
                <p className="text-sm text-slate-600">Companies</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-50/50 border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-500/20">
                <HardDrive className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.totals?.devices || 0}</p>
                <p className="text-sm text-slate-600">Devices</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-50/50 border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-amber-500/20">
                <Users className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.totals?.users || 0}</p>
                <p className="text-sm text-slate-600">Users</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-slate-50/50 border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-pink-500/20">
                <Ticket className="w-5 h-5 text-pink-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats?.totals?.tickets || 0}</p>
                <p className="text-sm text-slate-600">Tickets</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Organizations by Status */}
        <Card className="bg-slate-50/50 border-slate-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-slate-900 flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-blue-600" />
              Organizations by Status
            </CardTitle>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/platform/organizations')}
              className="text-blue-600 hover:text-purple-300"
            >
              View All <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats?.organizations_by_status || {}).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between p-3 bg-slate-100/30 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-2 h-2 rounded-full ${
                      status === 'active' ? 'bg-emerald-500' :
                      status === 'trial' ? 'bg-blue-500' :
                      status === 'suspended' ? 'bg-red-500' :
                      status === 'past_due' ? 'bg-amber-500' :
                      'bg-slate-500'
                    }`} />
                    <span className="text-slate-900 capitalize">{status.replace('_', ' ')}</span>
                  </div>
                  <span className="text-xl font-bold text-slate-900">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Organizations by Plan */}
        <Card className="bg-slate-50/50 border-slate-200">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-slate-900 flex items-center gap-2">
              <CreditCard className="w-5 h-5 text-blue-600" />
              Organizations by Plan
            </CardTitle>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/platform/billing')}
              className="text-blue-600 hover:text-purple-300"
            >
              Revenue Details <ChevronRight className="w-4 h-4 ml-1" />
            </Button>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats?.organizations_by_plan || {}).map(([plan, count]) => {
                const planPrice = {trial: 0, starter: 2999, professional: 7999, enterprise: 19999}[plan] || 0;
                return (
                  <div key={plan} className="flex items-center justify-between p-3 bg-slate-100/30 rounded-lg">
                    <div className="flex items-center gap-3">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${PLAN_COLORS[plan] || 'bg-slate-500/20 text-slate-600'}`}>
                        {plan.toUpperCase()}
                      </span>
                      {planPrice > 0 && (
                        <span className="text-slate-600 text-sm">₹{planPrice}/mo</span>
                      )}
                    </div>
                    <span className="text-xl font-bold text-slate-900">{count}</span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Organizations */}
      <Card className="bg-slate-50/50 border-slate-200">
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-slate-900 flex items-center gap-2">
            <Clock className="w-5 h-5 text-blue-600" />
            Recent Organizations
          </CardTitle>
          <Button 
            variant="ghost" 
            size="sm" 
            onClick={() => navigate('/platform/organizations')}
            className="text-blue-600 hover:text-purple-300"
          >
            View All <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-200">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Organization</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Slug</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Plan</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-600">Created</th>
                </tr>
              </thead>
              <tbody>
                {stats?.recent_organizations?.length > 0 ? (
                  stats.recent_organizations.map(org => (
                    <tr key={org.id} className="border-b border-slate-200/50 hover:bg-slate-100/30">
                      <td className="py-3 px-4 text-slate-900 font-medium">{org.name}</td>
                      <td className="py-3 px-4 text-slate-600 font-mono text-sm">{org.slug}</td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[org.status]}`}>
                          {org.status}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${PLAN_COLORS[org.subscription?.plan]}`}>
                          {org.subscription?.plan || 'trial'}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-slate-600 text-sm">
                        {new Date(org.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td colSpan={5} className="py-8 text-center text-slate-600">
                      No organizations yet. Create your first tenant!
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card className="bg-slate-50/50 border-slate-200">
        <CardHeader>
          <CardTitle className="text-slate-900 flex items-center gap-2">
            <Activity className="w-5 h-5 text-blue-600" />
            Quick Actions
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <Button 
              onClick={() => navigate('/platform/organizations')}
              variant="outline" 
              className="border-slate-300 text-slate-700 hover:bg-blue-100 hover:text-purple-300 hover:border-blue-500/50 justify-start h-auto py-4"
              data-testid="quick-action-orgs"
            >
              <Building2 className="w-5 h-5 mr-3" />
              <div className="text-left">
                <p className="font-medium">Manage Organizations</p>
                <p className="text-xs text-slate-600">View & manage tenants</p>
              </div>
            </Button>
            
            <Button 
              onClick={() => navigate('/platform/billing')}
              variant="outline" 
              className="border-slate-300 text-slate-700 hover:bg-emerald-500/20 hover:text-emerald-300 hover:border-emerald-500/50 justify-start h-auto py-4"
              data-testid="quick-action-billing"
            >
              <DollarSign className="w-5 h-5 mr-3" />
              <div className="text-left">
                <p className="font-medium">Revenue Analytics</p>
                <p className="text-xs text-slate-600">View billing & revenue</p>
              </div>
            </Button>
            
            <Button 
              onClick={() => navigate('/platform/admins')}
              variant="outline" 
              className="border-slate-300 text-slate-700 hover:bg-blue-500/20 hover:text-blue-300 hover:border-blue-500/50 justify-start h-auto py-4"
              data-testid="quick-action-admins"
            >
              <Users className="w-5 h-5 mr-3" />
              <div className="text-left">
                <p className="font-medium">Platform Admins</p>
                <p className="text-xs text-slate-600">Manage super admins</p>
              </div>
            </Button>
            
            <Button 
              onClick={() => navigate('/platform/settings')}
              variant="outline" 
              className="border-slate-300 text-slate-700 hover:bg-amber-500/20 hover:text-amber-300 hover:border-amber-500/50 justify-start h-auto py-4"
              data-testid="quick-action-settings"
            >
              <AlertCircle className="w-5 h-5 mr-3" />
              <div className="text-left">
                <p className="font-medium">Platform Settings</p>
                <p className="text-xs text-slate-600">Configure platform</p>
              </div>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
