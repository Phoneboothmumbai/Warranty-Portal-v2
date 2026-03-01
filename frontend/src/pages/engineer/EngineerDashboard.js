import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Ticket, Clock, Calendar, CheckCircle, MapPin, AlertTriangle,
  ChevronRight, Check, X, RefreshCw, Zap, Loader2
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { useEngineerAuth } from '../../context/EngineerAuthContext';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const priorityColors = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-orange-100 text-orange-600',
  critical: 'bg-red-100 text-red-600',
};

const StatsCard = ({ label, value, icon: Icon, color }) => (
  <div className="bg-white border rounded-lg p-4" data-testid={`stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center justify-between">
      <div><p className="text-xs text-slate-500 uppercase tracking-wide">{label}</p><p className="text-2xl font-bold mt-1">{value}</p></div>
      <div className={`p-2.5 rounded-lg ${color}`}><Icon className="w-5 h-5" /></div>
    </div>
  </div>
);

// ── Pending Assignment Card ──
const PendingCard = ({ ticket, declineReasons, onAccept, onDecline, onReschedule, token }) => {
  const [action, setAction] = useState(null);
  const [reasonId, setReasonId] = useState('');
  const [reasonDetail, setReasonDetail] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState('');
  const [notes, setNotes] = useState('');
  const [slotData, setSlotData] = useState(null);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const todayStr = new Date().toISOString().slice(0, 10);

  const fetchSlots = async (date) => {
    if (!date) return;
    setLoadingSlots(true);
    setSlotData(null);
    setSelectedSlot('');
    try {
      const res = await fetch(`${API}/api/engineer/available-slots?date=${date}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        setSlotData(await res.json());
      } else {
        const err = await res.json();
        toast.error(err.detail || 'Failed to load slots');
        setSlotData({ slots: [], message: err.detail });
      }
    } catch {
      toast.error('Failed to load available slots');
    } finally {
      setLoadingSlots(false);
    }
  };

  const handleDateChange = (e) => {
    const date = e.target.value;
    setSelectedDate(date);
    if (date) fetchSlots(date);
  };

  const handleSubmitReschedule = async () => {
    if (!selectedDate) { toast.error('Please select a date'); return; }
    if (!selectedSlot) { toast.error('Please select a time slot'); return; }
    setSubmitting(true);
    const proposedTime = `${selectedDate}T${selectedSlot}:00`;
    const [sh, sm] = selectedSlot.split(':').map(Number);
    const endH = sh + 1;
    const endTime = `${selectedDate}T${String(endH).padStart(2, '0')}:${String(sm).padStart(2, '0')}:00`;
    await onReschedule(ticket.id, proposedTime, endTime, notes);
    setSubmitting(false);
  };

  const availableSlots = slotData?.slots?.filter(s => s.available) || [];
  const blockedSlots = slotData?.slots?.filter(s => !s.available) || [];

  return (
    <div className="border-2 border-amber-300 bg-amber-50/50 rounded-xl p-4" data-testid={`pending-${ticket.ticket_number}`}>
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-sm font-bold text-amber-700">#{ticket.ticket_number}</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${priorityColors[ticket.priority_name] || priorityColors.medium}`}>{ticket.priority_name}</span>
            <span className="text-[10px] bg-amber-100 text-amber-700 px-1.5 py-0.5 rounded font-medium">Pending Acceptance</span>
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

      {!action && (
        <div className="flex gap-2 mt-3">
          <Button size="sm" className="bg-green-600 hover:bg-green-700 text-white" onClick={() => onAccept(ticket.id)} data-testid={`accept-${ticket.ticket_number}`}>
            <Check className="w-3.5 h-3.5 mr-1" /> Accept Job
          </Button>
          <Button size="sm" variant="outline" onClick={() => setAction('reschedule')} data-testid={`reschedule-btn-${ticket.ticket_number}`}>
            <RefreshCw className="w-3.5 h-3.5 mr-1" /> Accept & Reschedule
          </Button>
          <Button size="sm" variant="outline" className="text-red-600 border-red-200 hover:bg-red-50" onClick={() => setAction('decline')} data-testid={`decline-btn-${ticket.ticket_number}`}>
            <X className="w-3.5 h-3.5 mr-1" /> Decline
          </Button>
        </div>
      )}

      {action === 'decline' && (
        <div className="mt-3 bg-white rounded-lg border p-3 space-y-2" data-testid={`decline-form-${ticket.ticket_number}`}>
          <p className="text-xs font-medium text-red-700">Reason for declining:</p>
          <select className="w-full border rounded px-3 py-2 text-sm" value={reasonId} onChange={e => setReasonId(e.target.value)} data-testid="decline-reason">
            <option value="">Select reason...</option>
            {declineReasons.map(r => <option key={r.id} value={r.id}>{r.label}</option>)}
          </select>
          <Input placeholder="Additional details (optional)" value={reasonDetail} onChange={e => setReasonDetail(e.target.value)} className="text-sm" />
          <div className="flex gap-2">
            <Button size="sm" className="bg-red-600 hover:bg-red-700 text-white" disabled={!reasonId} onClick={() => onDecline(ticket.id, reasonId, reasonDetail)} data-testid={`confirm-decline-${ticket.ticket_number}`}>
              Confirm Decline
            </Button>
            <Button size="sm" variant="ghost" onClick={() => setAction(null)}>Cancel</Button>
          </div>
        </div>
      )}

      {action === 'reschedule' && (
        <div className="mt-3 bg-white rounded-lg border p-3 space-y-3" data-testid={`reschedule-form-${ticket.ticket_number}`}>
          <p className="text-xs font-medium text-blue-700">Select a date and available time slot:</p>

          {/* Date Picker */}
          <div>
            <label className="text-xs text-slate-500 block mb-1">Date</label>
            <input
              type="date"
              className="w-full border rounded-md px-3 py-2 text-sm bg-white"
              min={todayStr}
              value={selectedDate}
              onChange={handleDateChange}
              data-testid="reschedule-date"
            />
          </div>

          {/* Slot Loading */}
          {loadingSlots && (
            <div className="flex items-center justify-center py-4 text-slate-400" data-testid="slots-loading">
              <Loader2 className="w-4 h-4 animate-spin mr-2" /> Loading available slots...
            </div>
          )}

          {/* Non-working day / Holiday message */}
          {slotData && !slotData.is_working_day && (
            <div className="bg-orange-50 border border-orange-200 rounded-lg px-3 py-2 text-xs text-orange-700" data-testid="non-working-msg">
              {slotData.message || 'This is not a working day. Please select another date.'}
            </div>
          )}

          {/* Available Slots Grid */}
          {slotData && slotData.is_working_day && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="text-xs text-slate-500">
                  Available Slots ({slotData.work_start} - {slotData.work_end})
                </label>
                <span className="text-[10px] text-slate-400">
                  {availableSlots.length} available / {slotData.slots?.length || 0} total
                </span>
              </div>
              {availableSlots.length === 0 ? (
                <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 text-xs text-red-600" data-testid="no-slots-msg">
                  No available slots on this date. Please try another day.
                </div>
              ) : (
                <div className="grid grid-cols-4 sm:grid-cols-6 gap-1.5" data-testid="slot-grid">
                  {slotData.slots.map(slot => (
                    <button
                      key={slot.time}
                      type="button"
                      disabled={!slot.available}
                      onClick={() => setSelectedSlot(slot.time)}
                      className={`px-2 py-1.5 text-xs rounded-md border transition-all font-medium
                        ${!slot.available
                          ? 'bg-slate-100 text-slate-300 border-slate-100 cursor-not-allowed line-through'
                          : selectedSlot === slot.time
                            ? 'bg-blue-600 text-white border-blue-600 ring-2 ring-blue-300'
                            : 'bg-white text-slate-700 border-slate-200 hover:border-blue-400 hover:bg-blue-50 cursor-pointer'
                        }`}
                      title={slot.blocked_by ? `Blocked: ${slot.blocked_by}` : `Select ${slot.time}`}
                      data-testid={`slot-${slot.time.replace(':', '')}`}
                    >
                      {slot.time}
                    </button>
                  ))}
                </div>
              )}
              {selectedSlot && (
                <p className="text-xs text-blue-600 mt-1.5 font-medium" data-testid="selected-slot-label">
                  Selected: {selectedDate} at {selectedSlot}
                </p>
              )}
            </div>
          )}

          {/* Notes */}
          {selectedSlot && (
            <div>
              <label className="text-xs text-slate-500 block mb-1">Notes (optional)</label>
              <input
                type="text"
                placeholder="Add any notes..."
                className="w-full border rounded-md px-3 py-2 text-sm"
                value={notes}
                onChange={e => setNotes(e.target.value)}
                data-testid="reschedule-notes"
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-2">
            <Button
              size="sm"
              className="bg-blue-600 hover:bg-blue-700 text-white"
              disabled={!selectedSlot || submitting}
              onClick={handleSubmitReschedule}
              data-testid={`confirm-reschedule-${ticket.ticket_number}`}
            >
              {submitting ? <Loader2 className="w-3.5 h-3.5 mr-1 animate-spin" /> : <Check className="w-3.5 h-3.5 mr-1" />}
              Accept & Reschedule
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { setAction(null); setSelectedDate(''); setSelectedSlot(''); setSlotData(null); }}>Cancel</Button>
          </div>
        </div>
      )}
    </div>
  );
};

// ── MAIN ──
export default function EngineerDashboard() {
  const navigate = useNavigate();
  const { token, engineer } = useEngineerAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const hdrs = useCallback(() => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }), [token]);

  const fetchDash = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/engineer/dashboard`, { headers: hdrs() });
      if (res.ok) setData(await res.json());
      else toast.error('Failed to load dashboard');
    } catch { toast.error('Network error'); }
    finally { setLoading(false); }
  }, [hdrs]);

  useEffect(() => { fetchDash(); }, [fetchDash]);

  const handleAccept = async (ticketId) => {
    try {
      const res = await fetch(`${API}/api/engineer/assignment/accept`, {
        method: 'POST', headers: hdrs(), body: JSON.stringify({ ticket_id: ticketId }),
      });
      if (res.ok) { toast.success('Job accepted!'); fetchDash(); }
      else { const e = await res.json(); toast.error(e.detail || 'Failed'); }
    } catch { toast.error('Failed'); }
  };

  const handleDecline = async (ticketId, reasonId, detail) => {
    try {
      const res = await fetch(`${API}/api/engineer/assignment/decline`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ ticket_id: ticketId, reason_id: reasonId, reason_detail: detail }),
      });
      if (res.ok) { toast.success('Job declined. Back office has been notified.'); fetchDash(); }
      else { const e = await res.json(); toast.error(e.detail || 'Failed'); }
    } catch { toast.error('Failed'); }
  };

  const handleReschedule = async (ticketId, proposedTime, endTime, notes) => {
    try {
      console.log('Reschedule request:', { ticketId, proposedTime, endTime, notes });
      const res = await fetch(`${API}/api/engineer/assignment/reschedule`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ ticket_id: ticketId, proposed_time: proposedTime, proposed_end_time: endTime, notes: notes || '' }),
      });
      const body = await res.json();
      console.log('Reschedule response:', res.status, body);
      if (res.ok) { toast.success('Accepted & rescheduled!'); fetchDash(); }
      else { toast.error(`Error ${res.status}: ${body.detail || JSON.stringify(body)}`); }
    } catch (err) { 
      console.error('Reschedule error:', err);
      toast.error('Network error: ' + err.message); 
    }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!data) return <div className="flex items-center justify-center h-64 text-slate-400">No data</div>;

  const { pending_tickets, active_tickets, upcoming_schedules, decline_reasons, stats } = data;

  return (
    <div className="space-y-6" data-testid="engineer-dashboard">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">Welcome, {engineer?.name || data.engineer?.name}</p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatsCard label="Total Assigned" value={stats.total_assigned} icon={Ticket} color="bg-blue-50 text-blue-600" />
        <StatsCard label="Pending Accept" value={stats.pending_count} icon={AlertTriangle} color="bg-amber-50 text-amber-600" />
        <StatsCard label="Visits Today" value={stats.visits_today} icon={MapPin} color="bg-purple-50 text-purple-600" />
        <StatsCard label="Active Tickets" value={stats.active_count} icon={CheckCircle} color="bg-green-50 text-green-600" />
      </div>

      {/* Pending Acceptance — THE KEY SECTION */}
      {pending_tickets.length > 0 && (
        <div data-testid="pending-assignments">
          <h2 className="text-sm font-semibold text-amber-700 mb-3 flex items-center gap-1.5">
            <Zap className="w-4 h-4" />
            Jobs Awaiting Your Response ({pending_tickets.length})
            <span className="text-[10px] bg-amber-100 text-amber-600 px-2 py-0.5 rounded-full ml-1 animate-pulse">Action Required</span>
          </h2>
          <div className="space-y-3">
            {pending_tickets.map(t => (
              <PendingCard key={t.id} ticket={t} declineReasons={decline_reasons}
                onAccept={handleAccept} onDecline={handleDecline} onReschedule={handleReschedule} token={token} />
            ))}
          </div>
        </div>
      )}

      {/* Upcoming Visits */}
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

      {/* Active Tickets */}
      {active_tickets.length > 0 && (
        <div className="bg-white border rounded-lg overflow-hidden" data-testid="active-tickets">
          <div className="p-4 border-b">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-1"><Ticket className="w-4 h-4" /> Active Tickets ({active_tickets.length})</h2>
          </div>
          <div className="divide-y">
            {active_tickets.map(t => (
              <div key={t.id} className="flex items-center justify-between p-4 hover:bg-slate-50 cursor-pointer" onClick={() => navigate(`/engineer/ticket/${t.id}`)} data-testid={`active-${t.ticket_number}`}>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className="font-mono text-sm font-semibold text-blue-600">#{t.ticket_number}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded ${priorityColors[t.priority_name] || 'bg-slate-100'}`}>{t.priority_name}</span>
                    <span className="text-[10px] bg-blue-50 text-blue-700 px-1.5 py-0.5 rounded">{t.current_stage_name}</span>
                  </div>
                  <p className="text-sm text-slate-700 mt-0.5">{t.subject}</p>
                  <p className="text-xs text-slate-400">{t.company_name}</p>
                </div>
                <ChevronRight className="w-4 h-4 text-slate-300" />
              </div>
            ))}
          </div>
        </div>
      )}

      {pending_tickets.length === 0 && active_tickets.length === 0 && (
        <div className="text-center py-16 bg-white border rounded-lg">
          <CheckCircle className="w-12 h-12 text-green-200 mx-auto mb-3" />
          <p className="text-slate-500">No pending assignments or active tickets</p>
          <p className="text-xs text-slate-400 mt-1">You're all caught up!</p>
        </div>
      )}
    </div>
  );
}
