import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Send, Clock, User, Building2, AlertTriangle, 
  CheckCircle2, MessageSquare, Lock, RefreshCw, Edit2,
  ChevronDown, Paperclip, Tag, Calendar, Timer, Users,
  UserPlus, X, Mail, Phone, FileText, Zap
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_CONFIG = {
  open: { label: 'Open', color: 'bg-blue-100 text-blue-700 border-blue-200' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700 border-amber-200' },
  waiting_on_customer: { label: 'Waiting on Customer', color: 'bg-purple-100 text-purple-700 border-purple-200' },
  waiting_on_third_party: { label: 'Waiting on 3rd Party', color: 'bg-orange-100 text-orange-700 border-orange-200' },
  on_hold: { label: 'On Hold', color: 'bg-slate-100 text-slate-600 border-slate-200' },
  resolved: { label: 'Resolved', color: 'bg-emerald-100 text-emerald-700 border-emerald-200' },
  closed: { label: 'Closed', color: 'bg-slate-200 text-slate-500 border-slate-300' }
};

const PRIORITY_CONFIG = {
  low: { label: 'Low', color: 'bg-slate-100 text-slate-600' },
  medium: { label: 'Medium', color: 'bg-blue-100 text-blue-700' },
  high: { label: 'High', color: 'bg-orange-100 text-orange-700' },
  critical: { label: 'Critical', color: 'bg-red-100 text-red-700' }
};

const ENTRY_TYPE_CONFIG = {
  customer_message: { label: 'Customer', bgColor: 'bg-blue-50', borderColor: 'border-blue-200', icon: User },
  technician_reply: { label: 'Staff Reply', bgColor: 'bg-white', borderColor: 'border-slate-200', icon: MessageSquare },
  internal_note: { label: 'Internal Note', bgColor: 'bg-amber-50', borderColor: 'border-amber-200', icon: Lock },
  system_event: { label: 'System', bgColor: 'bg-slate-50', borderColor: 'border-slate-200', icon: RefreshCw }
};

export default function AdminTicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const { token, user } = useAuth();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [departments, setDepartments] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [enums, setEnums] = useState(null);
  
  // Reply form
  const [replyContent, setReplyContent] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [sending, setSending] = useState(false);
  const threadEndRef = useRef(null);
  
  // Edit modal
  const [showEdit, setShowEdit] = useState(false);
  const [editData, setEditData] = useState({});

  const fetchTicket = useCallback(async () => {
    try {
      const [ticketRes, deptsRes, adminsRes, enumsRes] = await Promise.all([
        axios.get(`${API}/ticketing/admin/tickets/${ticketId}`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/ticketing/admin/departments`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/ticketing/enums`)
      ]);
      
      setTicket(ticketRes.data);
      setDepartments(deptsRes.data || []);
      setAdmins(adminsRes.data || []);
      setEnums(enumsRes.data);
      setEditData({
        status: ticketRes.data.status,
        priority: ticketRes.data.priority,
        department_id: ticketRes.data.department_id || '',
        assigned_to: ticketRes.data.assigned_to || ''
      });
    } catch (error) {
      toast.error('Failed to load ticket');
      navigate('/admin/tickets');
    } finally {
      setLoading(false);
    }
  }, [ticketId, token, navigate]);

  useEffect(() => {
    fetchTicket();
  }, [fetchTicket]);

  useEffect(() => {
    // Scroll to bottom of thread on load
    if (threadEndRef.current) {
      threadEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [ticket?.thread]);

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyContent.trim()) return;
    
    setSending(true);
    try {
      await axios.post(
        `${API}/ticketing/admin/tickets/${ticketId}/reply`,
        { content: replyContent, is_internal: isInternal },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(isInternal ? 'Internal note added' : 'Reply sent');
      setReplyContent('');
      fetchTicket();
    } catch (error) {
      toast.error('Failed to send reply');
    } finally {
      setSending(false);
    }
  };

  const handleUpdateTicket = async () => {
    try {
      await axios.put(
        `${API}/ticketing/admin/tickets/${ticketId}`,
        editData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Ticket updated');
      setShowEdit(false);
      fetchTicket();
    } catch (error) {
      toast.error('Failed to update ticket');
    }
  };

  const handleQuickAssign = async (assigneeId) => {
    try {
      await axios.post(
        `${API}/ticketing/admin/tickets/${ticketId}/assign?assignee_id=${assigneeId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Ticket assigned');
      fetchTicket();
    } catch (error) {
      toast.error('Failed to assign');
    }
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const formatEventData = (eventType, eventData) => {
    switch (eventType) {
      case 'ticket_created':
        return 'Ticket created';
      case 'status_changed':
        return `Status changed from "${STATUS_CONFIG[eventData?.old]?.label || eventData?.old}" to "${STATUS_CONFIG[eventData?.new]?.label || eventData?.new}"`;
      case 'priority_changed':
        return `Priority changed from "${eventData?.old}" to "${eventData?.new}"`;
      case 'assigned':
        return `Assigned to ${eventData?.assignee_name || 'staff member'}`;
      case 'reassigned':
        return `Reassigned to ${eventData?.assignee_name || 'staff member'}`;
      case 'department_changed':
        return `Department changed`;
      default:
        return eventType?.replace(/_/g, ' ');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!ticket) return null;

  const statusConfig = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;
  const priorityConfig = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
  const sla = ticket.sla_status;
  const isSLABreached = sla?.response_breached || sla?.resolution_breached;

  return (
    <div data-testid="admin-ticket-detail-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-4">
          <button onClick={() => navigate('/admin/tickets')} className="p-2 hover:bg-slate-100 rounded-lg">
            <ArrowLeft className="h-5 w-5 text-slate-600" />
          </button>
          <div>
            <div className="flex items-center gap-3 mb-1">
              <h1 className="text-xl font-bold text-slate-900">{ticket.ticket_number}</h1>
              <span className={`px-2 py-1 rounded-full text-xs font-medium border ${statusConfig.color}`}>
                {statusConfig.label}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityConfig.color}`}>
                {priorityConfig.label}
              </span>
              {isSLABreached && (
                <span className="px-2 py-1 bg-red-100 text-red-700 rounded-full text-xs font-medium flex items-center gap-1">
                  <AlertTriangle className="h-3 w-3" />
                  SLA Breached
                </span>
              )}
            </div>
            <h2 className="text-lg text-slate-700">{ticket.subject}</h2>
          </div>
        </div>
        <Button variant="outline" onClick={() => setShowEdit(true)}>
          <Edit2 className="h-4 w-4 mr-2" />
          Edit Ticket
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Thread */}
        <div className="lg:col-span-2 space-y-4">
          {/* Original Description */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-2 mb-3">
              <div className="h-8 w-8 bg-blue-100 rounded-full flex items-center justify-center">
                <User className="h-4 w-4 text-blue-600" />
              </div>
              <div>
                <p className="font-medium text-slate-900 text-sm">{ticket.requester_name}</p>
                <p className="text-xs text-slate-500">{formatDateTime(ticket.created_at)}</p>
              </div>
            </div>
            <div className="prose prose-sm max-w-none text-slate-700 whitespace-pre-wrap">
              {ticket.description}
            </div>
            {ticket.tags?.length > 0 && (
              <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-100">
                <Tag className="h-4 w-4 text-slate-400" />
                {ticket.tags.map((tag, i) => (
                  <span key={i} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">{tag}</span>
                ))}
              </div>
            )}
          </div>

          {/* Thread */}
          <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
            {ticket.thread?.map((entry, index) => {
              const config = ENTRY_TYPE_CONFIG[entry.entry_type] || ENTRY_TYPE_CONFIG.system_event;
              const EntryIcon = config.icon;
              
              if (entry.entry_type === 'system_event') {
                return (
                  <div key={entry.id || index} className="flex items-center gap-2 py-2">
                    <div className="flex-1 border-t border-slate-200"></div>
                    <span className="text-xs text-slate-500 flex items-center gap-1">
                      <RefreshCw className="h-3 w-3" />
                      {formatEventData(entry.event_type, entry.event_data)}
                      <span className="text-slate-400">• {formatDateTime(entry.created_at)}</span>
                    </span>
                    <div className="flex-1 border-t border-slate-200"></div>
                  </div>
                );
              }
              
              return (
                <div key={entry.id || index} className={`rounded-xl border p-4 ${config.bgColor} ${config.borderColor}`}>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <div className={`h-7 w-7 rounded-full flex items-center justify-center ${entry.entry_type === 'customer_message' ? 'bg-blue-100' : entry.entry_type === 'internal_note' ? 'bg-amber-100' : 'bg-slate-100'}`}>
                        <EntryIcon className={`h-3.5 w-3.5 ${entry.entry_type === 'customer_message' ? 'text-blue-600' : entry.entry_type === 'internal_note' ? 'text-amber-600' : 'text-slate-600'}`} />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900 text-sm">{entry.author_name || 'Unknown'}</p>
                        <p className="text-xs text-slate-500">{config.label}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      {entry.is_internal && (
                        <span className="px-2 py-0.5 bg-amber-200 text-amber-800 rounded text-xs flex items-center gap-1">
                          <Lock className="h-3 w-3" />
                          Internal
                        </span>
                      )}
                      <span className="text-xs text-slate-500">{formatDateTime(entry.created_at)}</span>
                    </div>
                  </div>
                  <div className="text-sm text-slate-700 whitespace-pre-wrap">{entry.content}</div>
                </div>
              );
            })}
            <div ref={threadEndRef} />
          </div>

          {/* Reply Form */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <form onSubmit={handleSendReply}>
              <div className="mb-3">
                <div className="flex items-center gap-4 mb-2">
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      checked={!isInternal}
                      onChange={() => setIsInternal(false)}
                      className="text-blue-600"
                    />
                    <span className="text-sm text-slate-700">Reply to Customer</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input
                      type="radio"
                      checked={isInternal}
                      onChange={() => setIsInternal(true)}
                      className="text-amber-600"
                    />
                    <span className="text-sm text-slate-700 flex items-center gap-1">
                      <Lock className="h-3 w-3" />
                      Internal Note
                    </span>
                  </label>
                </div>
                <textarea
                  value={replyContent}
                  onChange={(e) => setReplyContent(e.target.value)}
                  placeholder={isInternal ? "Add an internal note (not visible to customer)..." : "Type your reply..."}
                  rows={4}
                  className={`w-full px-3 py-2 border rounded-lg text-sm resize-none ${isInternal ? 'border-amber-200 bg-amber-50' : 'border-slate-200'}`}
                />
              </div>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Button type="button" variant="ghost" size="sm" disabled>
                    <Paperclip className="h-4 w-4" />
                  </Button>
                </div>
                <Button type="submit" disabled={sending || !replyContent.trim()}>
                  <Send className="h-4 w-4 mr-2" />
                  {sending ? 'Sending...' : isInternal ? 'Add Note' : 'Send Reply'}
                </Button>
              </div>
            </form>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          {/* Ticket Info */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="font-medium text-slate-900 mb-4">Ticket Details</h3>
            <div className="space-y-3 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Status</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${statusConfig.color}`}>{statusConfig.label}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Priority</span>
                <span className={`px-2 py-0.5 rounded text-xs font-medium ${priorityConfig.color}`}>{priorityConfig.label}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Department</span>
                <span className="text-slate-900">{ticket.department?.name || 'Unassigned'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Assigned To</span>
                <span className="text-slate-900">{ticket.assigned_to_name || <span className="text-amber-600">Unassigned</span>}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Source</span>
                <span className="text-slate-900 capitalize">{ticket.source}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span className="text-slate-900">{formatDateTime(ticket.created_at)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Updated</span>
                <span className="text-slate-900">{formatDateTime(ticket.updated_at)}</span>
              </div>
            </div>
          </div>

          {/* SLA Info */}
          {sla && (
            <div className={`rounded-xl border p-4 ${isSLABreached ? 'bg-red-50 border-red-200' : 'bg-white border-slate-200'}`}>
              <h3 className="font-medium text-slate-900 mb-4 flex items-center gap-2">
                <Timer className="h-4 w-4" />
                SLA Status
              </h3>
              <div className="space-y-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Policy</span>
                  <span className="text-slate-900">{sla.sla_policy_name || 'Default'}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Response</span>
                  {sla.response_met === true ? (
                    <span className="text-emerald-600 flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> Met</span>
                  ) : sla.response_breached ? (
                    <span className="text-red-600 flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Breached</span>
                  ) : (
                    <span className="text-slate-600">{formatDateTime(sla.response_due_at)}</span>
                  )}
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-slate-500">Resolution</span>
                  {sla.resolution_met === true ? (
                    <span className="text-emerald-600 flex items-center gap-1"><CheckCircle2 className="h-3 w-3" /> Met</span>
                  ) : sla.resolution_breached ? (
                    <span className="text-red-600 flex items-center gap-1"><AlertTriangle className="h-3 w-3" /> Breached</span>
                  ) : (
                    <span className="text-slate-600">{formatDateTime(sla.resolution_due_at)}</span>
                  )}
                </div>
                {sla.is_paused && (
                  <div className="pt-2 border-t border-slate-200">
                    <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs">SLA Paused</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Requester Info */}
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <h3 className="font-medium text-slate-900 mb-4 flex items-center gap-2">
              <User className="h-4 w-4" />
              Requester
            </h3>
            <div className="space-y-2 text-sm">
              <p className="font-medium text-slate-900">{ticket.requester_name}</p>
              <p className="text-slate-500">{ticket.requester_email}</p>
              {ticket.requester_phone && (
                <p className="text-slate-500">{ticket.requester_phone}</p>
              )}
            </div>
          </div>

          {/* Quick Assign */}
          {!ticket.assigned_to && (
            <div className="bg-amber-50 rounded-xl border border-amber-200 p-4">
              <h3 className="font-medium text-amber-900 mb-3">Quick Assign</h3>
              <div className="space-y-2">
                {admins.slice(0, 5).map(admin => (
                  <button
                    key={admin.id}
                    onClick={() => handleQuickAssign(admin.id)}
                    className="w-full px-3 py-2 bg-white border border-amber-200 rounded-lg text-sm text-left hover:bg-amber-100 transition-colors"
                  >
                    {admin.name}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Edit Modal */}
      <Dialog open={showEdit} onOpenChange={setShowEdit}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit Ticket</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Status</label>
              <select
                value={editData.status}
                onChange={(e) => setEditData({ ...editData, status: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              >
                {enums?.statuses?.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Priority</label>
              <select
                value={editData.priority}
                onChange={(e) => setEditData({ ...editData, priority: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              >
                {enums?.priorities?.map(p => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Department</label>
              <select
                value={editData.department_id}
                onChange={(e) => setEditData({ ...editData, department_id: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              >
                <option value="">No Department</option>
                {departments.map(d => (
                  <option key={d.id} value={d.id}>{d.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Assigned To</label>
              <select
                value={editData.assigned_to}
                onChange={(e) => setEditData({ ...editData, assigned_to: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              >
                <option value="">Unassigned</option>
                {admins.map(a => (
                  <option key={a.id} value={a.id}>{a.name}</option>
                ))}
              </select>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button variant="outline" onClick={() => setShowEdit(false)}>Cancel</Button>
              <Button onClick={handleUpdateTicket}>Save Changes</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
