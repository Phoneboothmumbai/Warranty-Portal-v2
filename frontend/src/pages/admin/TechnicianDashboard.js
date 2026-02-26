import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Ticket, Clock, Calendar, CheckCircle, MapPin, AlertTriangle,
  ChevronRight, Wrench, User, Check, X, MessageSquare, RefreshCw
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const getToken = () => localStorage.getItem('admin_token');
const hdrs = () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` });

const StatsCard = ({ label, value, icon: Icon, color }) => (
  <div className="bg-white border border-slate-200 rounded-lg p-4" data-testid={`stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-semibold mt-1">{value}</p>
      </div>
      <div className={`p-2.5 rounded-lg ${color}`}><Icon className="w-5 h-5" /></div>
    </div>
  </div>
);

const priorityColors = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-orange-100 text-orange-600',
  critical: 'bg-red-100 text-red-600',
};

// ── Pending Assignment Card ──
const PendingCard = ({ ticket, declineReasons, onAccept, onDecline, onReschedule }) => {
  const [action, setAction] = useState(null); // 'decline' | 'reschedule'
  const [reasonId, setReasonId] = useState('');
  const [reasonDetail, setReasonDetail] = useState('');
  const [proposedTime, setProposedTime] = useState('');
  const [proposedDate, setProposedDate] = useState('');
  const [notes, setNotes] = useState('');

  return (
    <div className="border-2 border-amber-300 bg-amber-50/50 rounded-lg p-4" data-testid={`pending-${ticket.ticket_number}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-sm font-bold text-amber-700">#{ticket.ticket_number}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${priorityColors[ticket.priority_name] || priorityColors.medium}`}>{ticket.priority_name}</span>
            <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded">Pending Acceptance</span>
          </div>
          <p className="text-sm font-medium text-slate-800">{ticket.subject}</p>
          <p className="text-xs text-slate-500">{ticket.company_name} &middot; {ticket.help_topic_name || ticket.current_stage_name}</p>
          {ticket.scheduled_at && (
            <p className="text-xs text-purple-600 mt-1 flex items-center gap-1">
              <Calendar className="w-3 h-3" /> Scheduled: {new Date(ticket.scheduled_at).toLocaleString()}
            </p>
          )}
        </div>
      </div>

      {/* Action buttons */}
      {!action && (
        <div className="flex gap-2 mt-3">
          <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white" onClick={() => onAccept(ticket.id)} data-testid={`accept-${ticket.ticket_number}`}>
            <Check className="w-3.5 h-3.5 mr-1" /> Accept
          </Button>
          <Button size="sm" variant="outline" onClick={() => setAction('reschedule')} data-testid={`reschedule-btn-${ticket.ticket_number}`}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Accept & Reschedule
          </Button>
          <Button size="sm" variant="outline" className="text-red-600 border-red-200 hover:bg-red-50" onClick={() => setAction('decline')} data-testid={`decline-btn-${ticket.ticket_number}`}>
            <X className="w-3.5 h-3.5 mr-1" /> Decline
          </Button>
        </div>
      )}

      {/* Decline form */}
      {action === 'decline' && (
        <div className="mt-3 bg-white rounded-lg border p-3 space-y-2" data-testid={`decline-form-${ticket.ticket_number}`}>
          <p className="text-xs font-medium text-red-700">Reason for declining:</p>
          <select className="w-full border rounded px-3 py-2 text-sm" value={reasonId} onChange={e => setReasonId(e.target.value)} data-testid="decline-reason">
            <option value="">Select reason...</option>
            {declineReasons.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
          </select>
          <Input placeholder="Additional details (optional)" value={reasonDetail} onChange={e => setReasonDetail(e.target.value)} className="text-sm" data-testid="decline-detail" />
          <div className="flex gap-2">
            <Button size="sm" className="bg-red-600 hover:bg-red-700 text-white" disabled={!reasonId} onClick={() => onDecline(ticket.id, reasonId, reasonDetail)} data-testid={`confirm-decline-${ticket.ticket_number}`}>
              Confirm Decline
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setAction(null)}>Cancel</Button>
          </div>
        </div>
      )}

      {/* Reschedule form */}
      {action === 'reschedule' && (
        <div className="mt-3 bg-white rounded-lg border p-3 space-y-2" data-testid={`reschedule-form-${ticket.ticket_number}`}>
          <p className="text-xs font-medium text-blue-700">Propose a new time:</p>
          <div className="flex gap-2">
            <Input type="date" className="text-sm" value={proposedDate} onChange={e => setProposedDate(e.target.value)} min={new Date().toISOString().split('T')[0]} data-testid="reschedule-date" />
            <Input type="time" className="text-sm" value={proposedTime} onChange={e => setProposedTime(e.target.value)} data-testid="reschedule-time" />
          </div>
          <Input placeholder="Notes (optional)" value={notes} onChange={e => setNotes(e.target.value)} className="text-sm" />
          <div className="flex gap-2">
            <Button size="sm" disabled={!proposedDate || !proposedTime} onClick={() => {
              const dt = `${proposedDate}T${proposedTime}:00`;
              const [h, m] = proposedTime.split(':').map(Number);
              const endMins = h * 60 + m + 60;
              const endDt = `${proposedDate}T${String(Math.floor(endMins / 60)).padStart(2, '0')}:${String(endMins % 60).padStart(2, '0')}:00`;
              onReschedule(ticket.id, dt, endDt, notes);
            }} data-testid={`confirm-reschedule-${ticket.ticket_number}`}>
              Accept & Reschedule
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setAction(null)}>Cancel</Button>
          </div>
        </div>
      )}
    </div>
  );
};

// ── MAIN COMPONENT ──
export default function TechnicianDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [pendingData, setPendingData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ticketing/technician/dashboard`, { headers: hdrs() });
      if (res.ok) setData(await res.json());
      else toast.error('Failed to load dashboard');
    } catch { toast.error('Network error'); }
    finally { setLoading(false); }
  }, []);

  const fetchPending = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ticketing/assignment/pending`, { headers: hdrs() });
      if (res.ok) setPendingData(await res.json());
    } catch {}
  }, []);

  useEffect(() => { fetchDashboard(); fetchPending(); }, [fetchDashboard, fetchPending]);

  const handleAccept = async (ticketId) => {
    try {
      const res = await fetch(`${API}/api/ticketing/assignment/accept`, {
        method: 'POST', headers: hdrs(), body: JSON.stringify({ ticket_id: ticketId }),
      });
      if (res.ok) { toast.success('Job accepted!'); fetchDashboard(); fetchPending(); }
      else { const e = await res.json(); toast.error(e.detail || 'Failed'); }
    } catch { toast.error('Failed'); }
  };

  const handleDecline = async (ticketId, reasonId, detail) => {
    try {
      const res = await fetch(`${API}/api/ticketing/assignment/decline`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ ticket_id: ticketId, reason_id: reasonId, reason_detail: detail }),
      });
      if (res.ok) { toast.success('Job declined. Back office has been notified.'); fetchDashboard(); fetchPending(); }
      else { const e = await res.json(); toast.error(e.detail || 'Failed'); }
    } catch { toast.error('Failed'); }
  };

  const handleReschedule = async (ticketId, proposedTime, endTime, notes) => {
    try {
      const res = await fetch(`${API}/api/ticketing/assignment/reschedule`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ ticket_id: ticketId, proposed_time: proposedTime, proposed_end_time: endTime, notes }),
      });
      if (res.ok) { toast.success('Accepted & rescheduled!'); fetchDashboard(); fetchPending(); }
      else { const e = await res.json(); toast.error(e.detail || 'Failed'); }
    } catch { toast.error('Failed'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!data) return <div className="flex items-center justify-center h-64 text-slate-400">No data</div>;

  const { assigned_tickets, assigned_tasks, upcoming_schedules, stats, engineer } = data;
  const pendingTickets = pendingData?.tickets || [];
  const declineReasons = pendingData?.decline_reasons || [];

  return (
    <div className="space-y-6" data-testid="technician-dashboard">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Technician Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          {engineer ? `Welcome, ${engineer.name}` : 'Your assigned tickets and tasks'}
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatsCard label="Assigned Tickets" value={stats.total_assigned} icon={Ticket} color="bg-blue-50 text-blue-600" />
        <StatsCard label="Visits Today" value={stats.visits_today} icon={Calendar} color="bg-purple-50 text-purple-600" />
        <StatsCard label="Pending Diagnosis" value={stats.pending_diagnosis} icon={AlertTriangle} color="bg-orange-50 text-orange-600" />
        <StatsCard label="Completed This Week" value={stats.completed_this_week} icon={CheckCircle} color="bg-green-50 text-green-600" />
      </div>

      {/* Pending Assignments */}
      {pendingTickets.length > 0 && (
        <div data-testid="pending-assignments">
          <h2 className="text-sm font-semibold text-amber-700 mb-3 flex items-center gap-1.5">
            <AlertTriangle className="w-4 h-4" />
            Pending Acceptance ({pendingTickets.length})
            <span className="text-[10px] bg-amber-100 text-amber-600 px-2 py-0.5 rounded-full ml-1">Action Required</span>
          </h2>
          <div className="space-y-3">
            {pendingTickets.map(t => (
              <PendingCard
                key={t.id}
                ticket={t}
                declineReasons={declineReasons}
                onAccept={handleAccept}
                onDecline={handleDecline}
                onReschedule={handleReschedule}
              />
            ))}
          </div>
        </div>
      )}

      {/* Upcoming Schedules */}
      {upcoming_schedules.length > 0 && (
        <div className="bg-white border rounded-lg p-4" data-testid="upcoming-schedules">
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1"><Calendar className="w-4 h-4" /> Upcoming Visits</h2>
          <div className="space-y-2">
            {upcoming_schedules.map(s => (
              <div key={s.id} className="flex items-center gap-3 border rounded-lg p-3 hover:bg-slate-50">
                <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-purple-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">#{s.ticket_number} - {s.company_name || s.subject}</p>
                  <p className="text-xs text-slate-400">{new Date(s.scheduled_at).toLocaleString()}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'accepted' ? 'bg-green-100 text-green-600' : 'bg-blue-100 text-blue-600'}`}>
                  {s.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assigned Tickets */}
      <div className="bg-white border rounded-lg overflow-hidden" data-testid="assigned-tickets">
        <div className="p-4 border-b">
          <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-1"><Ticket className="w-4 h-4" /> My Tickets ({assigned_tickets.length})</h2>
        </div>
        {assigned_tickets.length === 0 ? (
          <div className="text-center py-12 text-slate-400">No assigned tickets</div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Ticket</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Subject</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Company</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Stage</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Priority</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {assigned_tickets.map(t => (
                <tr key={t.id} className="border-b hover:bg-slate-50" data-testid={`my-ticket-${t.ticket_number}`}>
                  <td className="px-4 py-3"><span className="font-mono text-sm font-semibold text-blue-600">#{t.ticket_number}</span></td>
                  <td className="px-4 py-3"><p className="text-sm text-slate-900 truncate max-w-[200px]">{t.subject}</p></td>
                  <td className="px-4 py-3"><span className="text-xs text-slate-500">{t.company_name || '-'}</span></td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">{t.current_stage_name}</span>
                  </td>
                  <td className="px-4 py-3">
                    {t.assignment_status === 'pending' ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">Pending</span>
                    ) : t.assignment_status === 'accepted' ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">Accepted</span>
                    ) : t.assignment_status === 'declined' ? (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">Declined</span>
                    ) : (
                      <span className="text-xs text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[t.priority_name] || priorityColors.medium}`}>{t.priority_name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <Button variant="outline" size="sm" onClick={() => navigate(`/admin/service-requests/${t.id}`)} data-testid={`view-ticket-${t.ticket_number}`}>
                      View <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pending Tasks */}
      {assigned_tasks.length > 0 && (
        <div className="bg-white border rounded-lg p-4" data-testid="pending-tasks">
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1"><Wrench className="w-4 h-4" /> My Tasks ({assigned_tasks.length})</h2>
          <div className="space-y-2">
            {assigned_tasks.map(task => (
              <div key={task.id} className="flex items-center gap-3 border rounded-lg p-3 hover:bg-slate-50">
                <div className={`w-2 h-2 rounded-full ${task.status === 'in_progress' ? 'bg-yellow-500' : 'bg-slate-300'}`} />
                <div className="flex-1">
                  <p className="text-sm font-medium">{task.name}</p>
                  <p className="text-xs text-slate-400">Ticket #{task.ticket_number}</p>
                </div>
                {task.due_at && (
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Due: {new Date(task.due_at).toLocaleDateString()}
                  </span>
                )}
                <span className={`text-xs px-2 py-0.5 rounded-full ${task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-600' : 'bg-slate-100 text-slate-600'}`}>
                  {task.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
