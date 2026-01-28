import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Clock, CheckCircle2, MessageSquare, 
  RefreshCw, Inbox, ChevronRight, AlertCircle
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_CONFIG = {
  open: { label: 'Open', color: 'bg-blue-100 text-blue-700' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700' },
  waiting_on_customer: { label: 'Awaiting Your Reply', color: 'bg-purple-100 text-purple-700' },
  waiting_on_third_party: { label: 'In Progress', color: 'bg-orange-100 text-orange-700' },
  on_hold: { label: 'On Hold', color: 'bg-slate-100 text-slate-600' },
  resolved: { label: 'Resolved', color: 'bg-emerald-100 text-emerald-700' },
  closed: { label: 'Closed', color: 'bg-slate-200 text-slate-500' }
};

const PRIORITY_CONFIG = {
  low: { label: 'Low', color: 'text-slate-500' },
  medium: { label: 'Medium', color: 'text-blue-600' },
  high: { label: 'High', color: 'text-orange-600' },
  critical: { label: 'Urgent', color: 'text-red-600' }
};

export default function CompanySupportTickets() {
  const { token, user } = useCompanyAuth();
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [departments, setDepartments] = useState([]);
  const [filter, setFilter] = useState('all');
  
  // Create ticket modal
  const [showCreate, setShowCreate] = useState(false);
  const [createData, setCreateData] = useState({
    subject: '',
    description: '',
    department_id: '',
    priority: 'medium'
  });
  const [creating, setCreating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const status = filter === 'all' ? undefined : filter === 'active' ? 'open' : filter;
      const [ticketsRes, deptsRes] = await Promise.all([
        axios.get(`${API}/ticketing/portal/tickets`, {
          params: { status },
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/ticketing/portal/departments`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setTickets(ticketsRes.data || []);
      setDepartments(deptsRes.data || []);
    } catch (error) {
      toast.error('Failed to load tickets');
    } finally {
      setLoading(false);
    }
  }, [token, filter]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    setCreating(true);
    try {
      const payload = {
        subject: createData.subject,
        description: createData.description,
        department_id: createData.department_id || undefined,
        priority: createData.priority
      };
      const res = await axios.post(
        `${API}/ticketing/portal/tickets`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Ticket ${res.data.ticket_number} created successfully`);
      setShowCreate(false);
      setCreateData({ subject: '', description: '', department_id: '', priority: 'medium' });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setCreating(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffHours < 1) return 'Just now';
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  };

  const activeTickets = tickets.filter(t => !['resolved', 'closed'].includes(t.status));
  const resolvedTickets = tickets.filter(t => ['resolved', 'closed'].includes(t.status));

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div data-testid="company-support-tickets-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Support Tickets</h1>
          <p className="text-slate-500 text-sm">Submit and track your support requests</p>
        </div>
        <Button onClick={() => setShowCreate(true)} data-testid="create-ticket-btn">
          <Plus className="h-4 w-4 mr-2" />
          New Ticket
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Inbox className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{activeTickets.length}</p>
              <p className="text-xs text-slate-500">Active Tickets</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-purple-100 rounded-lg">
              <AlertCircle className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">
                {tickets.filter(t => t.status === 'waiting_on_customer').length}
              </p>
              <p className="text-xs text-slate-500">Awaiting Reply</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-amber-100 rounded-lg">
              <Clock className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">
                {tickets.filter(t => t.status === 'in_progress').length}
              </p>
              <p className="text-xs text-slate-500">In Progress</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-emerald-100 rounded-lg">
              <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{resolvedTickets.length}</p>
              <p className="text-xs text-slate-500">Resolved</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2">
        {[
          { key: 'all', label: 'All Tickets' },
          { key: 'active', label: 'Active' },
          { key: 'resolved', label: 'Resolved' }
        ].map(tab => (
          <button
            key={tab.key}
            onClick={() => setFilter(tab.key)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === tab.key
                ? 'bg-slate-900 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Ticket List */}
      <div className="space-y-3">
        {tickets.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Inbox className="h-12 w-12 mx-auto mb-4 text-slate-300" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No tickets yet</h3>
            <p className="text-slate-500 mb-4">Create a new ticket to get support from our team</p>
            <Button onClick={() => setShowCreate(true)}>
              <Plus className="h-4 w-4 mr-2" />
              Create First Ticket
            </Button>
          </div>
        ) : (
          tickets.map(ticket => {
            const statusConfig = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;
            const priorityConfig = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
            const needsReply = ticket.status === 'waiting_on_customer';
            
            return (
              <div
                key={ticket.id}
                onClick={() => navigate(`/company/support-tickets/${ticket.id}`)}
                className={`bg-white rounded-xl border p-4 cursor-pointer hover:shadow-md transition-shadow ${
                  needsReply ? 'border-purple-300 bg-purple-50/30' : 'border-slate-200'
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs text-slate-500 font-mono">{ticket.ticket_number}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                      {needsReply && (
                        <span className="px-2 py-0.5 bg-purple-200 text-purple-800 rounded-full text-xs font-medium animate-pulse">
                          Action Required
                        </span>
                      )}
                    </div>
                    <h3 className="font-medium text-slate-900 mb-1">{ticket.subject}</h3>
                    <p className="text-sm text-slate-500 line-clamp-1">{ticket.description}</p>
                  </div>
                  <div className="flex flex-col items-end gap-2 ml-4">
                    <span className={`text-xs font-medium ${priorityConfig.color}`}>
                      {priorityConfig.label}
                    </span>
                    <span className="text-xs text-slate-400">{formatDate(ticket.updated_at)}</span>
                    <ChevronRight className="h-5 w-5 text-slate-300" />
                  </div>
                </div>
                {ticket.reply_count > 0 && (
                  <div className="flex items-center gap-1 mt-3 pt-3 border-t border-slate-100 text-xs text-slate-500">
                    <MessageSquare className="h-3 w-3" />
                    {ticket.reply_count} {ticket.reply_count === 1 ? 'reply' : 'replies'}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Create Ticket Modal */}
      <Dialog open={showCreate} onOpenChange={setShowCreate}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Support Ticket</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTicket} className="space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Subject *</label>
              <input
                type="text"
                required
                value={createData.subject}
                onChange={(e) => setCreateData({ ...createData, subject: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="Brief description of your issue"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Description *</label>
              <textarea
                required
                rows={5}
                value={createData.description}
                onChange={(e) => setCreateData({ ...createData, description: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm resize-none"
                placeholder="Please describe your issue in detail. Include any error messages, steps to reproduce, and what you were trying to do..."
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Department</label>
                <select
                  value={createData.department_id}
                  onChange={(e) => setCreateData({ ...createData, department_id: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="">General Support</option>
                  {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Priority</label>
                <select
                  value={createData.priority}
                  onChange={(e) => setCreateData({ ...createData, priority: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="low">Low - Can wait</option>
                  <option value="medium">Medium - Normal</option>
                  <option value="high">High - Important</option>
                  <option value="critical">Critical - Blocking work</option>
                </select>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button type="submit" disabled={creating}>
                {creating ? 'Creating...' : 'Submit Ticket'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
