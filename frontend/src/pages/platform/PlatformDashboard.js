import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Building2, HardDrive, Users, Ticket, TrendingUp, AlertCircle, Clock } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_COLORS = {
  trial: 'bg-blue-500/20 text-blue-400',
  active: 'bg-emerald-500/20 text-emerald-400',
  past_due: 'bg-amber-500/20 text-amber-400',
  suspended: 'bg-red-500/20 text-red-400',
  cancelled: 'bg-slate-500/20 text-slate-400',
  churned: 'bg-slate-600/20 text-slate-500'
};

const PLAN_COLORS = {
  trial: 'bg-slate-500/20 text-slate-400',
  starter: 'bg-blue-500/20 text-blue-400',
  professional: 'bg-purple-500/20 text-purple-400',
  enterprise: 'bg-amber-500/20 text-amber-400'
};

export default function PlatformDashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const token = localStorage.getItem('platformToken');

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  const StatCard = ({ label, value, icon: Icon, color = 'purple' }) => (
    <Card className="bg-slate-800/50 border-slate-700">
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm text-slate-400 mb-1">{label}</p>
            <p className="text-3xl font-bold text-white">{value?.toLocaleString() || 0}</p>
          </div>
          <div className={`p-3 rounded-xl bg-${color}-500/20`}>
            <Icon className={`w-6 h-6 text-${color}-400`} />
          </div>
        </div>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6" data-testid="platform-dashboard">
      <div>
        <h1 className="text-2xl font-bold text-white">Platform Dashboard</h1>
        <p className="text-slate-400">Overview of all tenants and platform health</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard 
          label="Total Organizations" 
          value={stats?.totals?.organizations} 
          icon={Building2}
          color="purple"
        />
        <StatCard 
          label="Total Companies" 
          value={stats?.totals?.companies} 
          icon={Building2}
          color="blue"
        />
        <StatCard 
          label="Total Devices" 
          value={stats?.totals?.devices} 
          icon={HardDrive}
          color="emerald"
        />
        <StatCard 
          label="Total Users" 
          value={stats?.totals?.users} 
          icon={Users}
          color="amber"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Organizations by Status */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <AlertCircle className="w-5 h-5 text-purple-400" />
              Organizations by Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats?.organizations_by_status || {}).map(([status, count]) => (
                <div key={status} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${STATUS_COLORS[status] || 'bg-slate-500/20 text-slate-400'}`}>
                      {status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <span className="text-white font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Organizations by Plan */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <CardTitle className="text-white flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-purple-400" />
              Organizations by Plan
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats?.organizations_by_plan || {}).map(([plan, count]) => (
                <div key={plan} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${PLAN_COLORS[plan] || 'bg-slate-500/20 text-slate-400'}`}>
                      {plan.toUpperCase()}
                    </span>
                  </div>
                  <span className="text-white font-semibold">{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Organizations */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardHeader>
          <CardTitle className="text-white flex items-center gap-2">
            <Clock className="w-5 h-5 text-purple-400" />
            Recent Organizations
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Organization</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Slug</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Plan</th>
                  <th className="text-left py-3 px-4 text-sm font-medium text-slate-400">Created</th>
                </tr>
              </thead>
              <tbody>
                {stats?.recent_organizations?.map(org => (
                  <tr key={org.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                    <td className="py-3 px-4 text-white font-medium">{org.name}</td>
                    <td className="py-3 px-4 text-slate-400 font-mono text-sm">{org.slug}</td>
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
                    <td className="py-3 px-4 text-slate-400 text-sm">
                      {new Date(org.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
