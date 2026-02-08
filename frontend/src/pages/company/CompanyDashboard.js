import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Laptop, Shield, Clock, AlertTriangle, Ticket, 
  ChevronRight, ArrowUpRight, CheckCircle2, Monitor
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { toast } from 'sonner';
import WatchTowerAgentDownload from '../../components/WatchTowerAgentDownload';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyDashboard = () => {
  const { token, user } = useCompanyAuth();
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboard();
  }, []);

  const fetchDashboard = async () => {
    try {
      const response = await axios.get(`${API}/company/dashboard`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setStats(response.data);
    } catch (error) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="company-dashboard">
      {/* Welcome Header */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-600 rounded-2xl p-6 text-white">
        <h1 className="text-2xl font-bold">Welcome back, {user?.name?.split(' ')[0]}!</h1>
        <p className="text-emerald-100 mt-1">{user?.company_name}</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Laptop}
          label="Total Devices"
          value={stats?.total_devices || 0}
          color="blue"
          link="/company/devices"
        />
        <StatCard
          icon={AlertTriangle}
          label="Warranties Expiring (30 days)"
          value={stats?.warranties_expiring_30_days || 0}
          color="amber"
          link="/company/warranty?filter=expiring"
        />
        <StatCard
          icon={Shield}
          label="Active AMC Contracts"
          value={stats?.active_amc_contracts || 0}
          color="emerald"
          link="/company/amc"
        />
        <StatCard
          icon={Ticket}
          label="Open Tickets"
          value={stats?.open_service_tickets || 0}
          color="purple"
          link="/company/tickets?status=open"
        />
      </div>

      {/* Secondary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Expiring in 60 days</p>
              <p className="text-2xl font-bold text-amber-600 mt-1">{stats?.warranties_expiring_60_days || 0}</p>
            </div>
            <Clock className="h-10 w-10 text-amber-100" />
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Expiring in 90 days</p>
              <p className="text-2xl font-bold text-orange-600 mt-1">{stats?.warranties_expiring_90_days || 0}</p>
            </div>
            <Clock className="h-10 w-10 text-orange-100" />
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-slate-500">Active Warranties</p>
              <p className="text-2xl font-bold text-emerald-600 mt-1">
                {(stats?.total_devices || 0) - (stats?.warranties_expiring_30_days || 0) - (stats?.warranties_expiring_60_days || 0) - (stats?.warranties_expiring_90_days || 0)}
              </p>
            </div>
            <CheckCircle2 className="h-10 w-10 text-emerald-100" />
          </div>
        </div>
      </div>

      {/* Recent Tickets */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
          <h2 className="font-semibold text-slate-900">Recent Service Tickets</h2>
          <Link 
            to="/company/tickets" 
            className="text-sm text-emerald-600 hover:text-emerald-700 flex items-center gap-1"
          >
            View all <ChevronRight className="h-4 w-4" />
          </Link>
        </div>
        
        {stats?.recent_tickets?.length > 0 ? (
          <div className="divide-y divide-slate-100">
            {stats.recent_tickets.map((ticket) => (
              <Link
                key={ticket.id}
                to={`/company/tickets/${ticket.id}`}
                className="flex items-center justify-between px-6 py-4 hover:bg-slate-50 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className={`w-2 h-2 rounded-full ${
                    ticket.status === 'open' ? 'bg-amber-500' :
                    ticket.status === 'in_progress' ? 'bg-blue-500' :
                    ticket.status === 'resolved' ? 'bg-emerald-500' :
                    'bg-slate-400'
                  }`} />
                  <div>
                    <p className="font-medium text-slate-900">{ticket.subject}</p>
                    <p className="text-sm text-slate-500">{ticket.ticket_number}</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    ticket.status === 'open' ? 'bg-amber-50 text-amber-700' :
                    ticket.status === 'in_progress' ? 'bg-blue-50 text-blue-700' :
                    ticket.status === 'resolved' ? 'bg-emerald-50 text-emerald-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                    {ticket.status?.replace('_', ' ')}
                  </span>
                  <ArrowUpRight className="h-4 w-4 text-slate-400" />
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="px-6 py-12 text-center">
            <Ticket className="h-12 w-12 text-slate-200 mx-auto mb-3" />
            <p className="text-slate-500">No recent tickets</p>
            <Link 
              to="/company/tickets" 
              className="text-sm text-emerald-600 hover:text-emerald-700 mt-2 inline-block"
            >
              Create a service request
            </Link>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Link
          to="/company/tickets"
          className="bg-white rounded-xl border border-slate-100 p-5 hover:border-emerald-200 hover:shadow-md transition-all group"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900">Raise Service Request</h3>
              <p className="text-sm text-slate-500 mt-1">Report an issue with a device</p>
            </div>
            <ArrowUpRight className="h-5 w-5 text-slate-400 group-hover:text-emerald-600" />
          </div>
        </Link>
        <Link
          to="/company/warranty"
          className="bg-white rounded-xl border border-slate-100 p-5 hover:border-emerald-200 hover:shadow-md transition-all group"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900">Check Warranty Status</h3>
              <p className="text-sm text-slate-500 mt-1">View device warranty details</p>
            </div>
            <ArrowUpRight className="h-5 w-5 text-slate-400 group-hover:text-emerald-600" />
          </div>
        </Link>
        <Link
          to="/company/amc"
          className="bg-white rounded-xl border border-slate-100 p-5 hover:border-emerald-200 hover:shadow-md transition-all group"
        >
          <div className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold text-slate-900">View AMC Contracts</h3>
              <p className="text-sm text-slate-500 mt-1">Check coverage and entitlements</p>
            </div>
            <ArrowUpRight className="h-5 w-5 text-slate-400 group-hover:text-emerald-600" />
          </div>
        </Link>
      </div>
    </div>
  );
};

const StatCard = ({ icon: Icon, label, value, color, link }) => {
  const colorClasses = {
    blue: 'bg-blue-50 text-blue-600',
    amber: 'bg-amber-50 text-amber-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    purple: 'bg-purple-50 text-purple-600',
  };

  return (
    <Link
      to={link}
      className="bg-white rounded-xl border border-slate-100 p-5 hover:border-emerald-200 hover:shadow-md transition-all"
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">{label}</p>
          <p className="text-3xl font-bold text-slate-900 mt-1">{value}</p>
        </div>
        <div className={`w-12 h-12 rounded-xl flex items-center justify-center ${colorClasses[color]}`}>
          <Icon className="h-6 w-6" />
        </div>
      </div>
    </Link>
  );
};

export default CompanyDashboard;
