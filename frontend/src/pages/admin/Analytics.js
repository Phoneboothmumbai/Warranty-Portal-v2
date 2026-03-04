import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart,
  PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar
} from 'recharts';
import {
  BarChart3, TrendingUp, Users, DollarSign, Monitor, Clock, GitBranch,
  Package, FileText, Brain, ChevronDown, Calendar, ArrowUp, ArrowDown,
  AlertTriangle, Shield, Target, Activity, Zap, Heart
} from 'lucide-react';
import { Button } from '../../components/ui/button';

const API = process.env.REACT_APP_BACKEND_URL;

const COLORS = ['#0F62FE', '#6929C4', '#1192E8', '#005D5D', '#9F1853', '#FA4D56', '#570408', '#198038', '#002D9C', '#EE538B', '#B28600', '#009D9A'];
const PRIORITY_COLORS = { critical: '#DC2626', high: '#F97316', medium: '#3B82F6', low: '#22C55E' };

// ── Shared Components ──
const KpiCard = ({ label, value, change, type, prefix }) => {
  const isPositive = change > 0;
  const colors = { success: 'text-emerald-600', warning: 'text-amber-600', info: 'text-blue-600', neutral: 'text-slate-600' };
  return (
    <div className="bg-white rounded-lg border p-4 flex flex-col gap-1" data-testid={`kpi-${label.toLowerCase().replace(/\s/g, '-')}`}>
      <span className="text-xs text-slate-500 uppercase tracking-wide">{label}</span>
      <div className="flex items-end gap-2">
        <span className={`text-2xl font-bold ${colors[type] || 'text-slate-800'}`}>
          {prefix && <span className="text-sm font-normal mr-0.5">{prefix} </span>}
          {typeof value === 'number' ? value.toLocaleString('en-IN') : value}
        </span>
        {change !== undefined && change !== null && (
          <span className={`text-xs flex items-center gap-0.5 mb-1 ${isPositive ? 'text-emerald-600' : 'text-red-500'}`}>
            {isPositive ? <ArrowUp className="w-3 h-3" /> : <ArrowDown className="w-3 h-3" />}
            {Math.abs(change)}%
          </span>
        )}
      </div>
    </div>
  );
};

const ChartCard = ({ title, children, className = '' }) => (
  <div className={`bg-white rounded-lg border p-4 ${className}`}>
    <h3 className="text-sm font-semibold text-slate-700 mb-3">{title}</h3>
    {children}
  </div>
);

const TabBtn = ({ active, onClick, icon: Icon, label }) => (
  <button
    onClick={onClick}
    className={`flex items-center gap-1.5 px-3 py-2 text-xs font-medium rounded-lg transition-all whitespace-nowrap ${
      active ? 'bg-[#0F62FE] text-white shadow-sm' : 'text-slate-600 hover:bg-slate-100'
    }`}
    data-testid={`tab-${label.toLowerCase().replace(/\s/g, '-')}`}
  >
    <Icon className="w-3.5 h-3.5" />
    {label}
  </button>
);

const MiniTable = ({ columns, data }) => (
  <div className="overflow-auto max-h-72">
    <table className="w-full text-xs">
      <thead><tr className="border-b">{columns.map(c => <th key={c.key} className="text-left py-2 px-2 text-slate-500 font-medium">{c.label}</th>)}</tr></thead>
      <tbody>{data.map((row, i) => (
        <tr key={i} className="border-b border-slate-50 hover:bg-slate-50">
          {columns.map(c => <td key={c.key} className="py-2 px-2 text-slate-700">{c.render ? c.render(row[c.key], row) : row[c.key]}</td>)}
        </tr>
      ))}</tbody>
    </table>
  </div>
);

const EmptyState = ({ msg }) => <div className="flex items-center justify-center h-40 text-sm text-slate-400">{msg}</div>;

// ── Tab Panels ──

const TicketIntelligence = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, volume_by_day, stage_distribution, priority_distribution, topic_distribution, source_distribution } = data;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3">
        <KpiCard label="Total Tickets" value={s.total_tickets} type="info" />
        <KpiCard label="Open" value={s.open_tickets} type="warning" />
        <KpiCard label="Unassigned" value={s.unassigned} type="warning" />
        <KpiCard label="Avg Resolution" value={`${s.avg_resolution_hours}h`} type="info" />
        <KpiCard label="P95 Resolution" value={`${s.p95_resolution_hours}h`} type="neutral" />
        <KpiCard label="Reopen Rate" value={`${s.reopen_rate}%`} type={s.reopen_rate > 10 ? 'warning' : 'success'} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Ticket Volume Trend">
          {volume_by_day.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={volume_by_day}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 10 }} tickFormatter={v => v.slice(5)} />
                <YAxis tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="count" stroke="#0F62FE" fill="#0F62FE" fillOpacity={0.1} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No data for period" />}
        </ChartCard>
        <ChartCard title="Stage Distribution (Open Tickets)">
          {stage_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={stage_distribution} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 10 }} /><YAxis dataKey="name" type="category" width={100} tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} /><Bar dataKey="count" fill="#0F62FE" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No open tickets" />}
        </ChartCard>
        <ChartCard title="By Priority">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart><Pie data={priority_distribution} cx="50%" cy="50%" outerRadius={70} dataKey="count" label={({ name, count }) => `${name} (${count})`} labelLine={false}>
              {priority_distribution.map((e, i) => <Cell key={i} fill={PRIORITY_COLORS[e.name] || COLORS[i % COLORS.length]} />)}
            </Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Top Help Topics">
          {topic_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={topic_distribution.slice(0, 8)} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 10 }} /><YAxis dataKey="name" type="category" width={120} tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} /><Bar dataKey="count" fill="#6929C4" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No data" />}
        </ChartCard>
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Ticket Source">
          <ResponsiveContainer width="100%" height={180}>
            <PieChart><Pie data={source_distribution} cx="50%" cy="50%" outerRadius={60} dataKey="count" label={({ name, count }) => `${name} (${count})`}>
              {source_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Key Insights">
          <div className="space-y-2 text-xs text-slate-600">
            <div className="flex items-start gap-2 p-2 bg-blue-50 rounded"><Activity className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" /><span>{s.period_tickets} tickets created in this period. {s.unassigned} awaiting assignment.</span></div>
            {s.avg_resolution_hours > 0 && <div className="flex items-start gap-2 p-2 bg-emerald-50 rounded"><Clock className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" /><span>Average resolution time is {s.avg_resolution_hours}h (P95: {s.p95_resolution_hours}h)</span></div>}
            {s.reopen_rate > 5 && <div className="flex items-start gap-2 p-2 bg-amber-50 rounded"><AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" /><span>Reopen rate of {s.reopen_rate}% is above target. Review resolution quality.</span></div>}
          </div>
        </ChartCard>
      </div>
    </div>
  );
};

const WorkforcePerformance = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, scorecards, workload_distribution } = data;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <KpiCard label="Engineers" value={s.total_engineers} type="info" />
        <KpiCard label="Assigned Tickets" value={s.total_assigned_tickets} type="neutral" />
        <KpiCard label="Avg Per Engineer" value={s.avg_tickets_per_engineer} type="neutral" />
        <KpiCard label="Total Visits" value={s.total_visits} type="info" />
        <KpiCard label="First-Time Fix" value={`${s.avg_first_time_fix}%`} type="success" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Workload Distribution">
          {workload_distribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={workload_distribution}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 9 }} angle={-20} textAnchor="end" height={50} />
                <YAxis tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ fontSize: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="open" stackId="a" fill="#F97316" name="Open" radius={[0, 0, 0, 0]} />
                <Bar dataKey="closed" stackId="a" fill="#22C55E" name="Closed" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No data" />}
        </ChartCard>
        <ChartCard title="Engineer Scorecard">
          <MiniTable
            columns={[
              { key: 'name', label: 'Engineer' },
              { key: 'total_assigned', label: 'Assigned' },
              { key: 'closed', label: 'Closed' },
              { key: 'avg_resolution_hours', label: 'Avg Res (h)' },
              { key: 'first_time_fix_rate', label: 'FTF %', render: v => <span className={v >= 80 ? 'text-emerald-600 font-semibold' : v >= 50 ? 'text-amber-600' : 'text-red-500'}>{v}%</span> },
              { key: 'parts_cost', label: 'Parts Cost', render: v => `₹${v.toLocaleString('en-IN')}` },
            ]}
            data={scorecards}
          />
        </ChartCard>
      </div>
    </div>
  );
};

const FinancialAnalytics = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, quotation_pipeline, revenue_by_month, aging_buckets } = data;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard label="Total Quoted" value={s.total_quoted} prefix="INR" type="info" />
        <KpiCard label="Approved Revenue" value={s.total_approved} prefix="INR" type="success" />
        <KpiCard label="Conversion Rate" value={`${s.conversion_rate}%`} type={s.conversion_rate > 50 ? 'success' : 'warning'} />
        <KpiCard label="Parts Cost" value={s.total_parts_cost} prefix="INR" type="neutral" />
        <KpiCard label="Pending Bills" value={s.pending_bills_total} prefix="INR" type="warning" />
        <KpiCard label="Active AMC" value={s.active_amc_contracts} type="info" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Revenue by Month">
          {revenue_by_month.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={revenue_by_month}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} formatter={v => [`₹${v.toLocaleString('en-IN')}`, 'Revenue']} />
                <Bar dataKey="amount" fill="#198038" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No revenue data yet" />}
        </ChartCard>
        <ChartCard title="Quotation Pipeline">
          {quotation_pipeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart><Pie data={quotation_pipeline} cx="50%" cy="50%" outerRadius={70} dataKey="count" label={({ status, count }) => `${status} (${count})`}>
                {quotation_pipeline.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Pie><Tooltip formatter={(v, n, p) => [`${v} (₹${p.payload.amount.toLocaleString('en-IN')})`, p.payload.status]} /></PieChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No quotations" />}
        </ChartCard>
        <ChartCard title="Pending Bills Aging" className="lg:col-span-2">
          <ResponsiveContainer width="100%" height={180}>
            <BarChart data={aging_buckets}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="bucket" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} />
              <Tooltip contentStyle={{ fontSize: 12 }} formatter={v => [`₹${v.toLocaleString('en-IN')}`, 'Amount']} />
              <Bar dataKey="amount" fill="#DC2626" radius={[4, 4, 0, 0]}>
                {aging_buckets.map((_, i) => <Cell key={i} fill={['#22C55E', '#F59E0B', '#F97316', '#DC2626'][i] || '#DC2626'} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
    </div>
  );
};

const ClientHealth = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, companies } = data;
  const healthColor = score => score >= 80 ? 'text-emerald-600 bg-emerald-50' : score >= 50 ? 'text-amber-600 bg-amber-50' : 'text-red-600 bg-red-50';
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Companies" value={s.total_companies} type="info" />
        <KpiCard label="Avg Health Score" value={s.avg_health_score} type={s.avg_health_score >= 80 ? 'success' : 'warning'} />
        <KpiCard label="At Risk" value={s.at_risk_companies} type={s.at_risk_companies > 0 ? 'warning' : 'success'} />
        <KpiCard label="Devices Managed" value={s.total_devices_managed} type="neutral" />
      </div>
      <ChartCard title="Company Health Rankings">
        <MiniTable
          columns={[
            { key: 'name', label: 'Company', render: v => <span className="font-medium">{v}</span> },
            { key: 'health_score', label: 'Health', render: v => <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${healthColor(v)}`}>{v}</span> },
            { key: 'device_count', label: 'Devices' },
            { key: 'total_tickets', label: 'Tickets' },
            { key: 'open_tickets', label: 'Open' },
            { key: 'sla_breaches', label: 'SLA Breaches' },
            { key: 'revenue', label: 'Revenue', render: v => `₹${v.toLocaleString('en-IN')}` },
            { key: 'amc_status', label: 'AMC', render: v => <span className={`text-xs px-1.5 py-0.5 rounded ${v === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>{v || 'none'}</span> },
          ]}
          data={companies.slice().reverse()}
        />
      </ChartCard>
    </div>
  );
};

const AssetIntelligence = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, warranty_timeline, brand_distribution, type_distribution, age_distribution, failure_by_brand } = data;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-7 gap-3">
        <KpiCard label="Total Devices" value={s.total_devices} type="info" />
        <KpiCard label="Active Warranty" value={s.active_warranty} type="success" />
        <KpiCard label="Expired" value={s.expired_warranty} type="warning" />
        <KpiCard label="Expiring 30d" value={s.expiring_30d} type={s.expiring_30d > 0 ? 'warning' : 'neutral'} />
        <KpiCard label="Expiring 60d" value={s.expiring_60d} type="neutral" />
        <KpiCard label="Expiring 90d" value={s.expiring_90d} type="neutral" />
        <KpiCard label="With Tickets" value={s.devices_with_tickets} type="info" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Warranty Timeline">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={warranty_timeline}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="label" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {warranty_timeline.map((_, i) => <Cell key={i} fill={['#DC2626', '#F97316', '#F59E0B', '#3B82F6', '#22C55E'][i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Brand Distribution">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart><Pie data={brand_distribution} cx="50%" cy="50%" outerRadius={70} dataKey="count" label={({ name, count }) => `${name} (${count})`}>
              {brand_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Device Age Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={age_distribution}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="bucket" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" fill="#6929C4" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Failure Rate by Brand">
          <MiniTable
            columns={[
              { key: 'brand', label: 'Brand', render: v => <span className="font-medium">{v}</span> },
              { key: 'devices', label: 'Devices' },
              { key: 'tickets', label: 'Tickets' },
              { key: 'rate', label: 'Failure %', render: v => <span className={v > 20 ? 'text-red-600 font-semibold' : 'text-slate-600'}>{v}%</span> },
            ]}
            data={failure_by_brand}
          />
        </ChartCard>
      </div>
    </div>
  );
};

const SLACompliance = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, breach_by_priority, breach_by_team, breach_trend } = data;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard label="Total Tickets" value={s.total_tickets} type="info" />
        <KpiCard label="Compliant" value={s.sla_compliant} type="success" />
        <KpiCard label="Breached" value={s.sla_breached} type={s.sla_breached > 0 ? 'warning' : 'success'} />
        <KpiCard label="Compliance %" value={`${s.compliance_rate}%`} type={s.compliance_rate >= 90 ? 'success' : 'warning'} />
        <KpiCard label="Overdue" value={s.overdue} type={s.overdue > 0 ? 'warning' : 'success'} />
        <KpiCard label="Escalated" value={s.escalated} type={s.escalated > 0 ? 'warning' : 'neutral'} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="SLA Breach by Priority">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={breach_by_priority}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="priority" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ fontSize: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
              <Bar dataKey="total" fill="#3B82F6" name="Total" radius={[4, 4, 0, 0]} />
              <Bar dataKey="breached" fill="#DC2626" name="Breached" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Breach by Team">
          <MiniTable
            columns={[
              { key: 'team', label: 'Team' },
              { key: 'total', label: 'Total' },
              { key: 'breached', label: 'Breached' },
              { key: 'rate', label: 'Breach %', render: v => <span className={v > 10 ? 'text-red-600 font-semibold' : 'text-emerald-600'}>{v}%</span> },
            ]}
            data={breach_by_team}
          />
        </ChartCard>
        {breach_trend.length > 0 && (
          <ChartCard title="SLA Breach Trend (Weekly)" className="lg:col-span-2">
            <ResponsiveContainer width="100%" height={200}>
              <LineChart data={breach_trend}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="week" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="rate" stroke="#DC2626" strokeWidth={2} name="Breach %" dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </ChartCard>
        )}
      </div>
    </div>
  );
};

const WorkflowAnalytics = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, workflows, warranty_type_distribution } = data;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
        <KpiCard label="Active Workflows" value={s.total_workflows} type="info" />
        <KpiCard label="Active Tickets" value={s.total_active_tickets} type="warning" />
        <KpiCard label="Warranty Types" value={warranty_type_distribution.length} type="neutral" />
      </div>
      <ChartCard title="Warranty Type Distribution">
        <ResponsiveContainer width="100%" height={180}>
          <PieChart><Pie data={warranty_type_distribution} cx="50%" cy="50%" outerRadius={60} dataKey="count" label={({ type, count }) => `${type} (${count})`}>
            {warranty_type_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
          </Pie><Tooltip /></PieChart>
        </ResponsiveContainer>
      </ChartCard>
      {workflows.map(wf => (
        <ChartCard key={wf.id} title={`${wf.name} — ${wf.total_tickets} tickets (${wf.open_tickets} open)`}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            <div>
              <p className="text-xs text-slate-500 mb-2">Stage Backlog</p>
              <ResponsiveContainer width="100%" height={180}>
                <BarChart data={wf.stage_backlog}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                  <XAxis dataKey="stage" tick={{ fontSize: 8 }} angle={-30} textAnchor="end" height={60} />
                  <YAxis tick={{ fontSize: 10 }} allowDecimals={false} /><Tooltip contentStyle={{ fontSize: 12 }} />
                  <Bar dataKey="count" fill="#1192E8" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
            {wf.stage_cycle_times.length > 0 && (
              <div>
                <p className="text-xs text-slate-500 mb-2">Avg Cycle Time per Stage (hours)</p>
                <MiniTable
                  columns={[
                    { key: 'stage', label: 'Stage' },
                    { key: 'avg_hours', label: 'Avg Hours' },
                    { key: 'count', label: 'Samples' },
                  ]}
                  data={wf.stage_cycle_times}
                />
              </div>
            )}
          </div>
        </ChartCard>
      ))}
    </div>
  );
};

const InventoryAnalytics = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, stock_alerts, top_consumed, transaction_trend, part_request_status } = data;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        <KpiCard label="Products" value={s.total_products} type="info" />
        <KpiCard label="Stock Items" value={s.total_stock_items} type="neutral" />
        <KpiCard label="Low Stock Alerts" value={s.low_stock_alerts} type={s.low_stock_alerts > 0 ? 'warning' : 'success'} />
        <KpiCard label="Transactions" value={s.total_transactions} type="neutral" />
        <KpiCard label="Pending Parts" value={s.pending_part_requests} type={s.pending_part_requests > 0 ? 'warning' : 'neutral'} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Transaction Trend (In/Out)">
          {transaction_trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={transaction_trend}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ fontSize: 12 }} /><Legend wrapperStyle={{ fontSize: 11 }} />
                <Bar dataKey="in" fill="#22C55E" name="Stock In" radius={[4, 4, 0, 0]} />
                <Bar dataKey="out" fill="#F97316" name="Stock Out" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No transactions yet" />}
        </ChartCard>
        <ChartCard title="Top Consumed Items">
          {top_consumed.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={top_consumed.slice(0, 8)} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 10 }} /><YAxis dataKey="item" type="category" width={120} tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} /><Bar dataKey="quantity" fill="#9F1853" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No consumption data" />}
        </ChartCard>
        {stock_alerts.length > 0 && (
          <ChartCard title="Low Stock Alerts" className="lg:col-span-2">
            <MiniTable
              columns={[
                { key: 'product', label: 'Product' },
                { key: 'stock', label: 'Current Stock', render: v => <span className="text-red-600 font-semibold">{v}</span> },
                { key: 'reorder_level', label: 'Reorder Level' },
                { key: 'deficit', label: 'Deficit', render: v => <span className="text-red-600">-{v}</span> },
              ]}
              data={stock_alerts}
            />
          </ChartCard>
        )}
      </div>
    </div>
  );
};

const ContractAnalytics = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, type_distribution, expiry_pipeline, by_company } = data;
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <KpiCard label="Total Contracts" value={s.total_contracts} type="info" />
        <KpiCard label="Active" value={s.active_contracts} type="success" />
        <KpiCard label="Expired" value={s.expired_contracts} type="warning" />
        <KpiCard label="Coverage Rate" value={`${s.coverage_rate}%`} type={s.coverage_rate >= 50 ? 'success' : 'warning'} />
        <KpiCard label="Expiring 30d" value={s.expiring_30d} type={s.expiring_30d > 0 ? 'warning' : 'neutral'} />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Contract Type Distribution">
          <ResponsiveContainer width="100%" height={200}>
            <PieChart><Pie data={type_distribution} cx="50%" cy="50%" outerRadius={65} dataKey="count" label={({ type, count }) => `${type} (${count})`}>
              {type_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
            </Pie><Tooltip /></PieChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Expiry Pipeline">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={expiry_pipeline}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="label" tick={{ fontSize: 9 }} /><YAxis tick={{ fontSize: 10 }} allowDecimals={false} /><Tooltip contentStyle={{ fontSize: 12 }} />
              <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                {expiry_pipeline.map((_, i) => <Cell key={i} fill={['#DC2626', '#F97316', '#F59E0B', '#22C55E'][i]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Contracts by Company" className="lg:col-span-2">
          <MiniTable
            columns={[
              { key: 'company', label: 'Company', render: v => <span className="font-medium">{v}</span> },
              { key: 'count', label: 'Contracts' },
            ]}
            data={by_company}
          />
        </ChartCard>
      </div>
    </div>
  );
};

const OperationalIntelligence = ({ data }) => {
  if (!data) return <EmptyState msg="Loading..." />;
  const { summary: s, weekly_trend, anomalies, recommendations, top_issues } = data;
  const trendColors = { increasing: 'text-red-600', decreasing: 'text-emerald-600', stable: 'text-blue-600' };
  return (
    <div className="space-y-4">
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <KpiCard label="Trend" value={s.trend_direction} type={s.trend_direction === 'decreasing' ? 'success' : s.trend_direction === 'increasing' ? 'warning' : 'info'} />
        <KpiCard label="Next Week Forecast" value={s.predicted_next_week} type="info" />
        <KpiCard label="Anomalies" value={s.anomalies_detected} type={s.anomalies_detected > 0 ? 'warning' : 'success'} />
        <KpiCard label="Recommendations" value={s.recommendations_count} type="info" />
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Weekly Ticket Trend (12 weeks)">
          {weekly_trend.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <AreaChart data={weekly_trend}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="week" tick={{ fontSize: 9 }} /><YAxis tick={{ fontSize: 10 }} /><Tooltip contentStyle={{ fontSize: 12 }} />
                <Area type="monotone" dataKey="count" stroke="#0F62FE" fill="#0F62FE" fillOpacity={0.1} strokeWidth={2} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="Not enough data" />}
        </ChartCard>
        <ChartCard title="Top Issue Categories">
          {top_issues.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={top_issues.slice(0, 8)} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis type="number" tick={{ fontSize: 10 }} /><YAxis dataKey="topic" type="category" width={120} tick={{ fontSize: 9 }} />
                <Tooltip contentStyle={{ fontSize: 12 }} /><Bar dataKey="count" fill="#005D5D" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState msg="No data" />}
        </ChartCard>
      </div>
      {anomalies.length > 0 && (
        <ChartCard title="Anomaly Alerts">
          <div className="space-y-2">
            {anomalies.map((a, i) => (
              <div key={i} className="flex items-start gap-2 p-2 bg-amber-50 border border-amber-100 rounded text-xs">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <span><strong>{a.company}</strong> has {a.current_week_tickets} tickets this week ({a.spike_factor}x normal avg of {a.avg_weekly_tickets})</span>
              </div>
            ))}
          </div>
        </ChartCard>
      )}
      {recommendations.length > 0 && (
        <ChartCard title="Action Recommendations">
          <div className="space-y-2">
            {recommendations.map((r, i) => (
              <div key={i} className={`flex items-start gap-2 p-2 rounded text-xs border ${r.priority === 'high' ? 'bg-red-50 border-red-100' : 'bg-blue-50 border-blue-100'}`}>
                <Zap className={`w-4 h-4 shrink-0 mt-0.5 ${r.priority === 'high' ? 'text-red-600' : 'text-blue-600'}`} />
                <div><p className="font-medium">{r.message}</p><p className="text-slate-500 mt-0.5">{r.action}</p></div>
              </div>
            ))}
          </div>
        </ChartCard>
      )}
    </div>
  );
};


// ══════════════════════════════════════════════════════════
// MAIN ANALYTICS PAGE
// ══════════════════════════════════════════════════════════

const TABS = [
  { id: 'overview', label: 'Overview', icon: BarChart3 },
  { id: 'tickets', label: 'Tickets', icon: BarChart3 },
  { id: 'workforce', label: 'Workforce', icon: Users },
  { id: 'financial', label: 'Financial', icon: DollarSign },
  { id: 'clients', label: 'Clients', icon: Heart },
  { id: 'assets', label: 'Assets', icon: Monitor },
  { id: 'sla', label: 'SLA', icon: Shield },
  { id: 'workflows', label: 'Workflows', icon: GitBranch },
  { id: 'inventory', label: 'Inventory', icon: Package },
  { id: 'contracts', label: 'Contracts', icon: FileText },
  { id: 'intelligence', label: 'AI Insights', icon: Brain },
];

const PERIODS = [
  { label: '7 Days', value: 7 },
  { label: '30 Days', value: 30 },
  { label: '90 Days', value: 90 },
  { label: '365 Days', value: 365 },
];

export default function Analytics() {
  const [activeTab, setActiveTab] = useState('overview');
  const [days, setDays] = useState(30);
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(false);

  const hdrs = useCallback(() => {
    const token = localStorage.getItem('admin_token');
    return { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };
  }, []);

  const fetchData = useCallback(async (endpoint, key) => {
    try {
      const res = await fetch(`${API}/api/analytics/${endpoint}`, { headers: hdrs() });
      if (res.ok) {
        const d = await res.json();
        setData(prev => ({ ...prev, [key]: d }));
      }
    } catch (e) {
      console.error(`Analytics fetch error (${key}):`, e);
    }
  }, [hdrs]);

  useEffect(() => {
    setLoading(true);
    const promises = [];

    if (activeTab === 'overview') {
      promises.push(fetchData(`executive-summary?days=${days}`, 'executive'));
      promises.push(fetchData(`tickets?days=${days}`, 'tickets'));
      promises.push(fetchData(`workforce?days=${days}`, 'workforce'));
      promises.push(fetchData(`financial?days=${days}`, 'financial'));
    } else if (activeTab === 'tickets') {
      promises.push(fetchData(`tickets?days=${days}`, 'tickets'));
    } else if (activeTab === 'workforce') {
      promises.push(fetchData(`workforce?days=${days}`, 'workforce'));
    } else if (activeTab === 'financial') {
      promises.push(fetchData(`financial?days=${days}`, 'financial'));
    } else if (activeTab === 'clients') {
      promises.push(fetchData(`clients?days=${days}`, 'clients'));
    } else if (activeTab === 'assets') {
      promises.push(fetchData('assets', 'assets'));
    } else if (activeTab === 'sla') {
      promises.push(fetchData(`sla?days=${days}`, 'sla'));
    } else if (activeTab === 'workflows') {
      promises.push(fetchData('workflows', 'workflows'));
    } else if (activeTab === 'inventory') {
      promises.push(fetchData('inventory', 'inventory'));
    } else if (activeTab === 'contracts') {
      promises.push(fetchData('contracts', 'contracts'));
    } else if (activeTab === 'intelligence') {
      promises.push(fetchData(`operational?days=${days}`, 'operational'));
    }

    Promise.all(promises).finally(() => setLoading(false));
  }, [activeTab, days, fetchData]);

  // Overview Tab
  const OverviewPanel = () => {
    const exec = data.executive;
    const tickets = data.tickets;
    const workforce = data.workforce;
    const financial = data.financial;
    if (!exec) return <EmptyState msg="Loading overview..." />;
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-3">
          {exec.kpis.map(kpi => <KpiCard key={kpi.label} {...kpi} />)}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          {tickets && (
            <ChartCard title="Ticket Volume Trend">
              {tickets.volume_by_day.length > 0 ? (
                <ResponsiveContainer width="100%" height={180}>
                  <AreaChart data={tickets.volume_by_day}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="date" tick={{ fontSize: 9 }} tickFormatter={v => v.slice(5)} /><YAxis tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 12 }} /><Area type="monotone" dataKey="count" stroke="#0F62FE" fill="#0F62FE" fillOpacity={0.1} strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              ) : <EmptyState msg="No data" />}
            </ChartCard>
          )}
          {tickets && (
            <ChartCard title="Stage Distribution">
              {tickets.stage_distribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={180}>
                  <PieChart><Pie data={tickets.stage_distribution} cx="50%" cy="50%" outerRadius={60} dataKey="count" label={({ name, count }) => `${name}(${count})`} labelLine={false}>
                    {tickets.stage_distribution.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie><Tooltip /></PieChart>
                </ResponsiveContainer>
              ) : <EmptyState msg="No open tickets" />}
            </ChartCard>
          )}
          {workforce && (
            <ChartCard title="Workload Distribution">
              {workforce.workload_distribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={workforce.workload_distribution}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="name" tick={{ fontSize: 8 }} angle={-20} textAnchor="end" height={40} /><YAxis tick={{ fontSize: 10 }} />
                    <Tooltip contentStyle={{ fontSize: 12 }} />
                    <Bar dataKey="open" stackId="a" fill="#F97316" name="Open" />
                    <Bar dataKey="closed" stackId="a" fill="#22C55E" name="Closed" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <EmptyState msg="No data" />}
            </ChartCard>
          )}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {financial && (
            <ChartCard title="Revenue by Month">
              {financial.revenue_by_month.length > 0 ? (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={financial.revenue_by_month}><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis dataKey="month" tick={{ fontSize: 10 }} /><YAxis tick={{ fontSize: 10 }} />
                    <Tooltip formatter={v => [`₹${v.toLocaleString('en-IN')}`, 'Revenue']} contentStyle={{ fontSize: 12 }} />
                    <Bar dataKey="amount" fill="#198038" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <EmptyState msg="No revenue data yet" />}
            </ChartCard>
          )}
          {tickets && (
            <ChartCard title="Top Help Topics">
              {tickets.topic_distribution.length > 0 ? (
                <ResponsiveContainer width="100%" height={180}>
                  <BarChart data={tickets.topic_distribution.slice(0, 6)} layout="vertical"><CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                    <XAxis type="number" tick={{ fontSize: 10 }} /><YAxis dataKey="name" type="category" width={110} tick={{ fontSize: 9 }} />
                    <Tooltip contentStyle={{ fontSize: 12 }} /><Bar dataKey="count" fill="#6929C4" radius={[0, 4, 4, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              ) : <EmptyState msg="No data" />}
            </ChartCard>
          )}
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-4" data-testid="analytics-dashboard">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Analytics</h1>
          <p className="text-sm text-slate-500">Comprehensive business intelligence and insights</p>
        </div>
        <div className="flex items-center gap-2">
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => setDays(p.value)}
              className={`px-3 py-1.5 text-xs font-medium rounded-lg transition-all ${
                days === p.value ? 'bg-[#0F62FE] text-white' : 'text-slate-600 hover:bg-slate-100 border'
              }`}
              data-testid={`period-${p.value}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="flex items-center gap-1 overflow-x-auto pb-1 scrollbar-thin" data-testid="analytics-tabs">
        {TABS.map(tab => (
          <TabBtn key={tab.id} active={activeTab === tab.id} onClick={() => setActiveTab(tab.id)} icon={tab.icon} label={tab.label} />
        ))}
      </div>

      {/* Loading indicator */}
      {loading && <div className="h-1 bg-blue-100 rounded overflow-hidden"><div className="h-full bg-[#0F62FE] rounded animate-pulse w-1/2" /></div>}

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'overview' && <OverviewPanel />}
        {activeTab === 'tickets' && <TicketIntelligence data={data.tickets} />}
        {activeTab === 'workforce' && <WorkforcePerformance data={data.workforce} />}
        {activeTab === 'financial' && <FinancialAnalytics data={data.financial} />}
        {activeTab === 'clients' && <ClientHealth data={data.clients} />}
        {activeTab === 'assets' && <AssetIntelligence data={data.assets} />}
        {activeTab === 'sla' && <SLACompliance data={data.sla} />}
        {activeTab === 'workflows' && <WorkflowAnalytics data={data.workflows} />}
        {activeTab === 'inventory' && <InventoryAnalytics data={data.inventory} />}
        {activeTab === 'contracts' && <ContractAnalytics data={data.contracts} />}
        {activeTab === 'intelligence' && <OperationalIntelligence data={data.operational} />}
      </div>
    </div>
  );
}
