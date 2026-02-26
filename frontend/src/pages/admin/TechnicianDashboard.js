import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Users, Ticket, AlertTriangle, Clock, CheckCircle, XCircle,
  RefreshCw, ChevronRight, MapPin, TrendingUp, Calendar, User,
  ArrowUpRight, Zap
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const hdrs = () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('admin_token')}` });

const priorityColors = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-orange-100 text-orange-600',
  critical: 'bg-red-100 text-red-600',
};

const SummaryCard = ({ label, value, icon: Icon, color, sub }) => (
  <div className="bg-white border rounded-lg p-4" data-testid={`summary-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p>
        <p className="text-2xl font-bold mt-1">{value}</p>
        {sub && <p className="text-[11px] text-slate-400 mt-0.5">{sub}</p>}
      </div>
      <div className={`p-2.5 rounded-lg ${color}`}><Icon className="w-5 h-5" /></div>
    </div>
  </div>
);

export default function WorkforceOverview() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [reassigning, setReassigning] = useState(null); // ticket being reassigned
  const [suggestions, setSuggestions] = useState([]);

  const fetch_ = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ticketing/workforce/overview`, { headers: hdrs() });
      if (res.ok) setData(await res.json());
      else toast.error('Failed to load');
    } catch { toast.error('Network error'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetch_(); const iv = setInterval(fetch_, 60000); return () => clearInterval(iv); }, [fetch_]);

  const openReassign = async (ticketId) => {
    setReassigning(ticketId);
    try {
      const res = await fetch(`${API}/api/ticketing/assignment/suggest-reassign/${ticketId}`, { headers: hdrs() });
      if (res.ok) setSuggestions((await res.json()).suggestions || []);
    } catch {}
  };

  const handleReassign = async (ticketId, engineerId) => {
    try {
      const res = await fetch(`${API}/api/ticketing/assignment/reassign`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ ticket_id: ticketId, engineer_id: engineerId }),
      });
      if (res.ok) { toast.success('Reassigned!'); setReassigning(null); fetch_(); }
      else { const e = await res.json(); toast.error(e.detail || 'Failed'); }
    } catch { toast.error('Failed'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!data) return <div className="flex items-center justify-center h-64 text-slate-400">No data</div>;

  const { workforce, needs_reassignment, escalations, summary } = data;

  return (
    <div className="space-y-6" data-testid="workforce-overview">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Workforce Overview</h1>
          <p className="text-sm text-slate-500 mt-1">Technician workloads, SLA performance & escalations</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetch_} data-testid="refresh-btn">
          <RefreshCw className="w-4 h-4 mr-1" /> Refresh
        </Button>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-4 gap-4">
        <SummaryCard label="Technicians" value={summary.total_technicians} icon={Users} color="bg-blue-50 text-blue-600" />
        <SummaryCard label="Pending Acceptance" value={summary.total_pending} icon={Clock} color="bg-amber-50 text-amber-600" sub="Awaiting technician response" />
        <SummaryCard label="Overdue" value={summary.total_overdue} icon={AlertTriangle} color="bg-red-50 text-red-600" sub={`>${data.escalation_threshold_hours}h no response`} />
        <SummaryCard label="Needs Reassignment" value={summary.total_declined} icon={RefreshCw} color="bg-purple-50 text-purple-600" sub="Declined by technician" />
      </div>

      {/* Escalation Alerts */}
      {escalations.length > 0 && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4" data-testid="escalation-alerts">
          <h2 className="text-sm font-semibold text-red-800 mb-3 flex items-center gap-1.5">
            <Zap className="w-4 h-4" /> Escalation Alerts — No response for {data.escalation_threshold_hours}+ hours
          </h2>
          <div className="space-y-2">
            {escalations.map(t => (
              <div key={t.id} className="flex items-center justify-between bg-white rounded-lg border border-red-100 p-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-8 rounded bg-red-100 flex items-center justify-center">
                    <AlertTriangle className="w-4 h-4 text-red-500" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">#{t.ticket_number} — {t.subject}</p>
                    <p className="text-xs text-slate-500">
                      Assigned to <strong>{t.assigned_to_name}</strong> at {new Date(t.assigned_at).toLocaleString()}
                    </p>
                  </div>
                </div>
                <Button size="sm" variant="outline" className="text-red-600 border-red-200" onClick={() => openReassign(t.id)} data-testid={`escalate-${t.ticket_number}`}>
                  <RefreshCw className="w-3.5 h-3.5 mr-1" /> Reassign
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Declined — Needs Reassignment */}
      {needs_reassignment.length > 0 && (
        <div className="bg-white border rounded-lg overflow-hidden" data-testid="needs-reassignment">
          <div className="p-4 border-b bg-purple-50">
            <h2 className="text-sm font-semibold text-purple-800 flex items-center gap-1.5">
              <XCircle className="w-4 h-4" /> Declined — Needs Reassignment ({needs_reassignment.length})
            </h2>
          </div>
          <div className="divide-y">
            {needs_reassignment.map(t => (
              <div key={t.id} className="flex items-center justify-between p-4 hover:bg-slate-50">
                <div className="flex items-center gap-3 flex-1">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-mono text-sm font-bold text-slate-700">#{t.ticket_number}</span>
                      <span className={`text-[10px] px-1.5 py-0.5 rounded ${priorityColors[t.priority_name] || 'bg-slate-100'}`}>{t.priority_name}</span>
                    </div>
                    <p className="text-xs text-slate-600 mt-0.5">{t.subject}</p>
                    <p className="text-[11px] text-slate-400 mt-0.5">
                      Declined by {t.assigned_to_name} — <em>{t.decline_reason_label}</em>
                      {t.decline_detail && <span> ({t.decline_detail})</span>}
                    </p>
                  </div>
                </div>
                <div className="flex gap-2">
                  {reassigning === t.id ? (
                    <div className="flex gap-1.5 items-center">
                      {suggestions.map(s => (
                        <button key={s.engineer_id} onClick={() => handleReassign(t.id, s.engineer_id)}
                          className="flex items-center gap-1 text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-lg hover:bg-blue-100 border border-blue-200"
                          data-testid={`assign-${s.engineer_id}`}
                        >
                          <span className="w-5 h-5 rounded-full bg-blue-200 flex items-center justify-center text-[10px] font-bold">{s.name?.charAt(0)}</span>
                          {s.name?.split(' ')[0]}
                          <span className="text-[10px] text-blue-400">({s.open_tickets})</span>
                        </button>
                      ))}
                      <button onClick={() => setReassigning(null)} className="text-xs text-slate-400 hover:text-slate-600 px-1">Cancel</button>
                    </div>
                  ) : (
                    <>
                      <Button size="sm" variant="outline" onClick={() => openReassign(t.id)} data-testid={`reassign-${t.ticket_number}`}>
                        <RefreshCw className="w-3.5 h-3.5 mr-1" /> Reassign
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => navigate(`/admin/service-requests/${t.id}`)} data-testid={`view-${t.ticket_number}`}>
                        View <ChevronRight className="w-3 h-3 ml-0.5" />
                      </Button>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Technician Table */}
      <div className="bg-white border rounded-lg overflow-hidden" data-testid="workforce-table">
        <div className="p-4 border-b">
          <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-1.5">
            <Users className="w-4 h-4" /> All Technicians
          </h2>
        </div>
        <table className="w-full">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Technician</th>
              <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Open</th>
              <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Pending</th>
              <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Declined</th>
              <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Visits Today</th>
              <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Accept Rate</th>
              <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Status</th>
            </tr>
          </thead>
          <tbody>
            {workforce.map(eng => (
              <tr key={eng.id} className="border-b hover:bg-slate-50" data-testid={`eng-row-${eng.id}`}>
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2.5">
                    <div className="w-8 h-8 rounded-full bg-blue-100 flex items-center justify-center text-xs font-bold text-blue-700">
                      {eng.name?.charAt(0)}
                    </div>
                    <div>
                      <p className="text-sm font-medium text-slate-800">{eng.name}</p>
                      <p className="text-[11px] text-slate-400">{eng.specialization || eng.email}</p>
                    </div>
                  </div>
                </td>
                <td className="text-center px-4 py-3">
                  <span className={`text-sm font-semibold ${eng.open_tickets > 5 ? 'text-red-600' : eng.open_tickets > 2 ? 'text-amber-600' : 'text-slate-700'}`}>
                    {eng.open_tickets}
                  </span>
                </td>
                <td className="text-center px-4 py-3">
                  {eng.pending_acceptance > 0 ? (
                    <span className="inline-flex items-center gap-1 text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full font-medium">
                      <Clock className="w-3 h-3" /> {eng.pending_acceptance}
                    </span>
                  ) : <span className="text-xs text-slate-300">0</span>}
                </td>
                <td className="text-center px-4 py-3">
                  {eng.declined > 0 ? (
                    <span className="text-xs text-red-600 font-medium">{eng.declined}</span>
                  ) : <span className="text-xs text-slate-300">0</span>}
                </td>
                <td className="text-center px-4 py-3">
                  {eng.visits_today > 0 ? (
                    <span className="inline-flex items-center gap-1 text-xs bg-purple-100 text-purple-700 px-2 py-0.5 rounded-full">
                      <MapPin className="w-3 h-3" /> {eng.visits_today}
                    </span>
                  ) : <span className="text-xs text-slate-300">0</span>}
                </td>
                <td className="text-center px-4 py-3">
                  {eng.acceptance_rate !== null ? (
                    <span className={`text-xs font-medium ${eng.acceptance_rate >= 80 ? 'text-green-600' : eng.acceptance_rate >= 50 ? 'text-amber-600' : 'text-red-600'}`}>
                      {eng.acceptance_rate}%
                    </span>
                  ) : <span className="text-xs text-slate-300">N/A</span>}
                </td>
                <td className="text-center px-4 py-3">
                  {eng.overdue_pending > 0 ? (
                    <span className="inline-flex items-center gap-1 text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded-full">
                      <AlertTriangle className="w-3 h-3" /> Overdue
                    </span>
                  ) : eng.pending_acceptance > 0 ? (
                    <span className="text-xs bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded-full">Awaiting</span>
                  ) : (
                    <span className="text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded-full">Active</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
