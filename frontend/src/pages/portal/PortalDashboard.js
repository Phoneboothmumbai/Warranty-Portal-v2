import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import {
  BarChart, Bar, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Wrench, Laptop, Shield, Clock, AlertTriangle, FileText, TrendingUp, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const API = process.env.REACT_APP_BACKEND_URL;
const COLORS = ['#0F62FE', '#6929C4', '#1192E8', '#005D5D', '#9F1853', '#FA4D56', '#198038', '#002D9C'];
const PRIORITY_COLORS = { critical: '#DC2626', high: '#F97316', medium: '#3B82F6', low: '#22C55E' };

const Kpi = ({ label, value, icon: Icon, color = '#0F62FE', sub }) => (
  <div className="bg-white rounded-lg border p-4" data-testid={`portal-kpi-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-start justify-between">
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold text-slate-800 mt-1">{value}</p>
        {sub && <p className="text-xs text-slate-400 mt-0.5">{sub}</p>}
      </div>
      <div className="w-9 h-9 rounded-lg flex items-center justify-center" style={{ backgroundColor: color + '15' }}>
        <Icon className="w-5 h-5" style={{ color }} />
      </div>
    </div>
  </div>
);

const Card = ({ title, children, className = '' }) => (
  <div className={`bg-white rounded-lg border p-4 ${className}`}>
    <h3 className="text-sm font-semibold text-slate-700 mb-3">{title}</h3>
    {children}
  </div>
);

export default function PortalDashboard() {
  const { tenant, hdrs, tenantCode } = useTenant();
  const [data, setData] = useState(null);
  const [days, setDays] = useState(30);
  const navigate = useNavigate();
  const primary = tenant?.portal_theme?.primary_color || tenant?.accent_color || '#0F62FE';

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/analytics?days=${days}`);
        if (res.ok) setData(await res.json());
      } catch { /* ignore */ }
    })();
  }, [tenantCode, days]);

  if (!data) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-3 border-t-transparent rounded-full animate-spin" style={{ borderColor: primary }} />
    </div>
  );

  const { summary: s, volume_by_day, stage_distribution, priority_distribution, topic_distribution, warranty_timeline, brand_distribution, recent_tickets } = data;

  return (
    <div className="space-y-5" data-testid="portal-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Welcome back</h1>
          <p className="text-sm text-slate-500">Here's your service overview for {data.company_name}</p>
        </div>
        <div className="flex items-center gap-2">
          {[7, 30, 90].map(d => (
            <button key={d} onClick={() => setDays(d)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${days === d ? 'text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100 border'}`}
              style={days === d ? { backgroundColor: primary } : {}}
              data-testid={`portal-period-${d}`}>
              {d}d
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <Kpi label="Open Tickets" value={s.open_tickets} icon={Wrench} color="#F97316" sub={`${s.total_tickets} total`} />
        <Kpi label="Resolved" value={s.closed_tickets} icon={Shield} color="#22C55E" />
        <Kpi label="Avg Resolution" value={`${s.avg_resolution_hours}h`} icon={Clock} color="#3B82F6" />
        <Kpi label="Devices" value={s.total_devices} icon={Laptop} color="#6929C4" sub={`${s.active_warranty} under warranty`} />
        <Kpi label="Contracts" value={s.active_contracts} icon={FileText} color="#005D5D" />
        <Kpi label="SLA Compliance" value={`${s.sla_compliance}%`} icon={TrendingUp} color={s.sla_compliance >= 90 ? '#22C55E' : '#F97316'} />
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <Card title="Ticket Volume Trend">
          {volume_by_day.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <AreaChart data={volume_by_day}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={v => v.slice(5)} /><YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="count" stroke={primary} fill={primary} fillOpacity={0.1} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <div className="h-48 flex items-center justify-center text-sm text-slate-400">No tickets in this period</div>}
        </Card>

        <Card title="Warranty Status">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={warranty_timeline}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="label" tick={{ fontSize: 9 }} /><YAxis tick={{ fontSize: 10 }} allowDecimals={false} />
              <Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {warranty_timeline.map((_, i) => <Cell key={i} fill={['#DC2626', '#F97316', '#F59E0B', '#3B82F6', '#22C55E'][i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <Card title="By Status">
          {stage_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart><Pie data={stage_distribution} cx="50%" cy="50%" outerRadius={60} dataKey="count" label={({ name, count }) => `${name} (${count})`} labelLine={false}>
                {stage_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie><Tooltip /></PieChart>
            </ResponsiveContainer>
          ) : <div className="h-44 flex items-center justify-center text-sm text-slate-400">No open tickets</div>}
        </Card>

        <Card title="By Priority">
          {priority_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart><Pie data={priority_distribution} cx="50%" cy="50%" outerRadius={60} dataKey="count" label={({ name, count }) => `${name} (${count})`} labelLine={false}>
                {priority_distribution.map((e, i) => <Cell key={i} fill={PRIORITY_COLORS[e.name] || COLORS[i % COLORS.length]} />)}
              </Pie><Tooltip /></PieChart>
            </ResponsiveContainer>
          ) : <div className="h-44 flex items-center justify-center text-sm text-slate-400">No data</div>}
        </Card>

        <Card title="Device Brands">
          {brand_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={180}>
              <PieChart><Pie data={brand_distribution} cx="50%" cy="50%" outerRadius={60} dataKey="count" label={({ name, count }) => `${name}(${count})`} labelLine={false}>
                {brand_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie><Tooltip /></PieChart>
            </ResponsiveContainer>
          ) : <div className="h-44 flex items-center justify-center text-sm text-slate-400">No devices</div>}
        </Card>
      </div>

      {/* Alerts */}
      {(s.expired_warranty > 0 || s.expiring_30d > 0) && (
        <div className="flex items-start gap-2 p-3 bg-amber-50 border border-amber-100 rounded-lg text-sm">
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="text-amber-800">
            {s.expired_warranty > 0 && <span className="font-medium">{s.expired_warranty} device(s) have expired warranty. </span>}
            {s.expiring_30d > 0 && <span className="font-medium">{s.expiring_30d} device(s) warranty expiring within 30 days. </span>}
            <span>Contact your service provider for renewal.</span>
          </div>
        </div>
      )}

      {/* Recent Tickets */}
      <Card title="Recent Tickets">
        {recent_tickets.length > 0 ? (
          <div className="space-y-2">
            {recent_tickets.map(t => (
              <div key={t.id} className="flex items-center justify-between p-2 hover:bg-slate-50 rounded cursor-pointer border border-slate-50"
                onClick={() => navigate(`/portal/${tenantCode}/tickets`)}>
                <div className="flex items-center gap-3">
                  <span className="text-xs font-mono text-slate-400">#{t.ticket_number}</span>
                  <span className="text-sm text-slate-700">{t.subject}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                    t.is_open ? 'bg-amber-50 text-amber-700' : 'bg-emerald-50 text-emerald-700'
                  }`}>{t.status}</span>
                  <span className="text-xs text-slate-400">{t.created}</span>
                  <ArrowRight className="w-3.5 h-3.5 text-slate-300" />
                </div>
              </div>
            ))}
          </div>
        ) : <div className="h-20 flex items-center justify-center text-sm text-slate-400">No tickets yet</div>}
      </Card>

      {/* Top Issues */}
      {topic_distribution.length > 0 && (
        <Card title="Common Issue Types">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={topic_distribution.slice(0, 6)} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis type="number" tick={{ fontSize: 10 }} /><YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 9 }} />
              <Tooltip contentStyle={{ fontSize: 12 }} /><Bar dataKey="count" fill={primary} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}
    </div>
  );
}
