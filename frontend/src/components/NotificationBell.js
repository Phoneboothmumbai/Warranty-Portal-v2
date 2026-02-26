import { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, X, AlertTriangle, Check, RefreshCw, User, Clock, ChevronRight } from 'lucide-react';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const hdrs = () => ({ 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('admin_token')}` });

export default function NotificationBell() {
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [notifs, setNotifs] = useState([]);
  const [unread, setUnread] = useState(0);
  const [reassignPanel, setReassignPanel] = useState(null); // { ticketId, notifId }
  const [suggestions, setSuggestions] = useState([]);
  const [loadingSuggest, setLoadingSuggest] = useState(false);
  const ref = useRef(null);

  const fetchNotifs = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/notifications?limit=20`, { headers: hdrs() });
      if (res.ok) {
        const data = await res.json();
        setNotifs(data.notifications || []);
        setUnread(data.unread_count || 0);
      }
    } catch {}
  }, []);

  useEffect(() => { fetchNotifs(); const iv = setInterval(fetchNotifs, 30000); return () => clearInterval(iv); }, [fetchNotifs]);

  // Close on outside click
  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const markRead = async (id) => {
    await fetch(`${API}/api/notifications/${id}/read`, { method: 'PUT', headers: hdrs() });
    fetchNotifs();
  };

  const markAllRead = async () => {
    await fetch(`${API}/api/notifications/read-all`, { method: 'PUT', headers: hdrs() });
    fetchNotifs();
  };

  const openReassign = async (ticketId, notifId) => {
    setReassignPanel({ ticketId, notifId });
    setLoadingSuggest(true);
    try {
      const res = await fetch(`${API}/api/ticketing/assignment/suggest-reassign/${ticketId}`, { headers: hdrs() });
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
      }
    } catch {}
    setLoadingSuggest(false);
  };

  const handleReassign = async (engineerId) => {
    try {
      const res = await fetch(`${API}/api/ticketing/assignment/reassign`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ ticket_id: reassignPanel.ticketId, engineer_id: engineerId }),
      });
      if (res.ok) {
        toast.success('Ticket reassigned!');
        if (reassignPanel.notifId) markRead(reassignPanel.notifId);
        setReassignPanel(null);
        fetchNotifs();
      } else { const e = await res.json(); toast.error(e.detail || 'Failed'); }
    } catch { toast.error('Failed'); }
  };

  const typeColors = {
    assignment_declined: { bg: 'bg-red-50', border: 'border-red-200', icon: AlertTriangle, iconColor: 'text-red-500' },
    assignment_accepted: { bg: 'bg-green-50', border: 'border-green-200', icon: Check, iconColor: 'text-green-500' },
    escalation: { bg: 'bg-amber-50', border: 'border-amber-200', icon: Clock, iconColor: 'text-amber-500' },
  };

  return (
    <div className="relative" ref={ref}>
      <button
        className="relative p-2 rounded-lg hover:bg-slate-100 transition-colors"
        onClick={() => setOpen(!open)}
        data-testid="notification-bell"
      >
        <Bell className="w-5 h-5 text-slate-600" />
        {unread > 0 && (
          <span className="absolute -top-0.5 -right-0.5 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center" data-testid="unread-badge">
            {unread > 9 ? '9+' : unread}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute right-0 top-12 w-96 bg-white rounded-xl shadow-2xl border z-50 overflow-hidden" data-testid="notification-panel">
          <div className="flex items-center justify-between p-3 border-b bg-slate-50">
            <h3 className="text-sm font-semibold text-slate-800">Notifications</h3>
            <div className="flex gap-2">
              {unread > 0 && (
                <button className="text-xs text-blue-600 hover:underline" onClick={markAllRead} data-testid="mark-all-read">
                  Mark all read
                </button>
              )}
              <button onClick={() => setOpen(false)}><X className="w-4 h-4 text-slate-400" /></button>
            </div>
          </div>

          {/* Reassign Panel */}
          {reassignPanel && (
            <div className="p-3 border-b bg-blue-50" data-testid="reassign-panel">
              <div className="flex items-center justify-between mb-2">
                <p className="text-xs font-semibold text-blue-800">Smart Reassignment Suggestions</p>
                <button onClick={() => setReassignPanel(null)}><X className="w-3.5 h-3.5 text-blue-400" /></button>
              </div>
              {loadingSuggest ? <p className="text-xs text-blue-400 py-2">Loading...</p> : (
                <div className="space-y-1.5 max-h-48 overflow-auto">
                  {suggestions.map(s => (
                    <div key={s.engineer_id} className="flex items-center justify-between bg-white rounded p-2 border">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-blue-100 flex items-center justify-center text-[10px] font-bold text-blue-700">
                          {s.name?.charAt(0)}
                        </div>
                        <div>
                          <p className="text-xs font-medium">{s.name}</p>
                          <p className="text-[10px] text-slate-400">
                            {s.open_tickets} tickets &middot; {s.specialization || 'General'}
                            {s.recent_declines > 0 && <span className="text-red-400"> &middot; {s.recent_declines} declines</span>}
                          </p>
                        </div>
                      </div>
                      <Button size="sm" className="text-xs h-7 px-2" onClick={() => handleReassign(s.engineer_id)} data-testid={`reassign-to-${s.engineer_id}`}>
                        Assign
                      </Button>
                    </div>
                  ))}
                  {suggestions.length === 0 && <p className="text-xs text-blue-400 text-center py-2">No technicians available</p>}
                </div>
              )}
            </div>
          )}

          <div className="max-h-[400px] overflow-auto" data-testid="notification-list">
            {notifs.length === 0 ? (
              <div className="text-center py-10 text-slate-400">
                <Bell className="w-6 h-6 mx-auto mb-2 opacity-30" />
                <p className="text-xs">No notifications</p>
              </div>
            ) : (
              notifs.map(n => {
                const style = typeColors[n.type] || { bg: 'bg-slate-50', border: 'border-slate-200', icon: Bell, iconColor: 'text-slate-400' };
                const Icon = style.icon;
                return (
                  <div
                    key={n.id}
                    className={`p-3 border-b transition-colors ${n.is_read ? 'bg-white' : style.bg} hover:bg-slate-50`}
                    data-testid={`notif-${n.id}`}
                  >
                    <div className="flex gap-2">
                      <Icon className={`w-4 h-4 mt-0.5 shrink-0 ${style.iconColor}`} />
                      <div className="flex-1 min-w-0">
                        <p className={`text-xs font-semibold ${n.is_read ? 'text-slate-600' : 'text-slate-800'}`}>{n.title}</p>
                        <p className="text-[11px] text-slate-500 mt-0.5">{n.message}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className="text-[10px] text-slate-400">
                            {new Date(n.created_at).toLocaleString()}
                          </span>
                          {!n.is_read && (
                            <button className="text-[10px] text-blue-600 hover:underline" onClick={() => markRead(n.id)}>Mark read</button>
                          )}
                          {n.type === 'assignment_declined' && n.ticket_id && (
                            <button
                              className="text-[10px] text-orange-600 hover:underline font-medium flex items-center gap-0.5"
                              onClick={() => openReassign(n.ticket_id, n.id)}
                              data-testid={`reassign-btn-${n.id}`}
                            >
                              <RefreshCw className="w-3 h-3" /> Reassign
                            </button>
                          )}
                          {n.ticket_id && (
                            <button
                              className="text-[10px] text-blue-600 hover:underline flex items-center gap-0.5"
                              onClick={() => { navigate(`/admin/service-requests/${n.ticket_id}`); setOpen(false); }}
                            >
                              View <ChevronRight className="w-3 h-3" />
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>
      )}
    </div>
  );
}
