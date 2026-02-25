import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, Ticket, Clock, AlertTriangle, CheckCircle, ChevronDown, X, RefreshCw } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const priorityColors = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

const StatsCard = ({ label, value, icon: Icon, color }) => (
  <div className="bg-white border border-slate-200 rounded-lg p-4" data-testid={`stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-semibold mt-1">{value}</p>
      </div>
      <div className={`p-2.5 rounded-lg ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  </div>
);

const CreateTicketModal = ({ open, onClose, onCreated }) => {
  const [helpTopics, setHelpTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topicDetails, setTopicDetails] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [contactName, setContactName] = useState('');
  const [contactEmail, setContactEmail] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [priorities, setPriorities] = useState([]);
  const [selectedPriority, setSelectedPriority] = useState('');

  useEffect(() => {
    if (!open) return;
    const token = localStorage.getItem('admin_token');
    Promise.all([
      fetch(`${API}/api/ticketing/help-topics`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
      fetch(`${API}/api/admin/companies`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
      fetch(`${API}/api/ticketing/priorities`, { headers: { Authorization: `Bearer ${token}` } }).then(r => r.json()),
    ]).then(([topics, comps, prios]) => {
      setHelpTopics(Array.isArray(topics) ? topics : []);
      setCompanies(Array.isArray(comps) ? comps : []);
      setPriorities(Array.isArray(prios) ? prios : []);
    });
  }, [open]);

  useEffect(() => {
    if (!selectedTopic) { setTopicDetails(null); return; }
    const token = localStorage.getItem('admin_token');
    fetch(`${API}/api/ticketing/help-topics/${selectedTopic}`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(setTopicDetails);
  }, [selectedTopic]);

  const handleSubmit = async () => {
    if (!selectedTopic || !subject.trim()) {
      toast.error('Please select a help topic and enter a subject');
      return;
    }
    setSubmitting(true);
    try {
      const token = localStorage.getItem('admin_token');
      const res = await fetch(`${API}/api/ticketing/tickets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({
          help_topic_id: selectedTopic,
          subject,
          description,
          form_values: formValues,
          company_id: selectedCompany || undefined,
          contact_name: contactName || undefined,
          contact_email: contactEmail || undefined,
          contact_phone: contactPhone || undefined,
          priority_id: selectedPriority || undefined,
        }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      const ticket = await res.json();
      toast.success(`Ticket ${ticket.ticket_number} created`);
      onCreated?.();
      onClose();
    } catch (e) { toast.error(e.message); }
    finally { setSubmitting(false); }
  };

  if (!open) return null;

  const formFields = topicDetails?.form?.fields || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-start justify-center pt-10 overflow-y-auto" data-testid="create-ticket-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 mb-10">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold">Create New Ticket</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5 space-y-4 max-h-[70vh] overflow-y-auto">
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Help Topic *</label>
            <select
              data-testid="help-topic-select"
              className="w-full border rounded-lg px-3 py-2 text-sm"
              value={selectedTopic || ''}
              onChange={e => { setSelectedTopic(e.target.value); setFormValues({}); }}
            >
              <option value="">Select a help topic...</option>
              {helpTopics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Company</label>
              <select className="w-full border rounded-lg px-3 py-2 text-sm" value={selectedCompany} onChange={e => setSelectedCompany(e.target.value)} data-testid="company-select">
                <option value="">Select company...</option>
                {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Priority</label>
              <select className="w-full border rounded-lg px-3 py-2 text-sm" value={selectedPriority} onChange={e => setSelectedPriority(e.target.value)} data-testid="priority-select">
                <option value="">Default</option>
                {priorities.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Subject *</label>
            <Input data-testid="ticket-subject" value={subject} onChange={e => setSubject(e.target.value)} placeholder="Brief description of the issue" />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Description</label>
            <textarea data-testid="ticket-description" className="w-full border rounded-lg px-3 py-2 text-sm min-h-[80px]" value={description} onChange={e => setDescription(e.target.value)} placeholder="Detailed description..." />
          </div>

          <div className="grid grid-cols-3 gap-3">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Contact Name</label>
              <Input data-testid="contact-name" value={contactName} onChange={e => setContactName(e.target.value)} placeholder="Name" />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Contact Email</label>
              <Input data-testid="contact-email" value={contactEmail} onChange={e => setContactEmail(e.target.value)} placeholder="Email" />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Contact Phone</label>
              <Input data-testid="contact-phone" value={contactPhone} onChange={e => setContactPhone(e.target.value)} placeholder="Phone" />
            </div>
          </div>

          {formFields.length > 0 && (
            <div className="border-t pt-4 mt-2">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Custom Fields - {topicDetails?.form?.name}</h3>
              <div className="grid grid-cols-2 gap-3">
                {formFields.map(f => (
                  <div key={f.id} className={f.width === 'full' ? 'col-span-2' : ''}>
                    <label className="text-sm font-medium text-slate-600 block mb-1">{f.label} {f.required && '*'}</label>
                    {f.field_type === 'select' ? (
                      <select className="w-full border rounded-lg px-3 py-2 text-sm" value={formValues[f.slug] || ''} onChange={e => setFormValues(p => ({ ...p, [f.slug]: e.target.value }))}>
                        <option value="">Select...</option>
                        {(f.options || []).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    ) : f.field_type === 'textarea' ? (
                      <textarea className="w-full border rounded-lg px-3 py-2 text-sm" value={formValues[f.slug] || ''} onChange={e => setFormValues(p => ({ ...p, [f.slug]: e.target.value }))} />
                    ) : (
                      <Input type={f.field_type === 'number' ? 'number' : f.field_type === 'date' ? 'date' : 'text'} value={formValues[f.slug] || ''} onChange={e => setFormValues(p => ({ ...p, [f.slug]: e.target.value }))} placeholder={f.placeholder || ''} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={submitting} data-testid="submit-ticket-btn">
            {submitting ? 'Creating...' : 'Create Ticket'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default function ServiceRequestsV2() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState({ is_open: null, help_topic_id: null, priority: null });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [helpTopics, setHelpTopics] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem('admin_token');
    const params = new URLSearchParams({ page, limit: 20 });
    if (search) params.set('search', search);
    if (filter.is_open !== null) params.set('is_open', filter.is_open);
    if (filter.help_topic_id) params.set('help_topic_id', filter.help_topic_id);
    if (filter.priority) params.set('priority', filter.priority);

    try {
      const [ticketsRes, statsRes] = await Promise.all([
        fetch(`${API}/api/ticketing/tickets?${params}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/api/ticketing/stats`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      const ticketsData = await ticketsRes.json();
      setTickets(ticketsData.tickets || []);
      setTotalPages(ticketsData.pages || 1);
      setStats(await statsRes.json());
    } catch { toast.error('Failed to load tickets'); }
    finally { setLoading(false); }
  }, [page, search, filter]);

  useEffect(() => { fetchTickets(); }, [fetchTickets]);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    fetch(`${API}/api/ticketing/help-topics`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(data => setHelpTopics(Array.isArray(data) ? data : []));
  }, []);

  return (
    <div className="space-y-6" data-testid="tickets-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tickets</h1>
          <p className="text-sm text-slate-500 mt-1">Manage service requests and support tickets</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchTickets} data-testid="refresh-btn">
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
          <Button size="sm" onClick={() => setShowCreate(true)} data-testid="create-ticket-btn">
            <Plus className="w-4 h-4 mr-1" /> New Ticket
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatsCard label="Open" value={stats.open || 0} icon={Ticket} color="bg-blue-50 text-blue-600" />
        <StatsCard label="Closed" value={stats.closed || 0} icon={CheckCircle} color="bg-green-50 text-green-600" />
        <StatsCard label="Total" value={stats.total || 0} icon={Clock} color="bg-slate-50 text-slate-600" />
        <StatsCard label="Pending Tasks" value={stats.pending_tasks || 0} icon={AlertTriangle} color="bg-orange-50 text-orange-600" />
      </div>

      <div className="flex gap-3 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            data-testid="search-tickets"
            className="pl-9"
            placeholder="Search by ticket number or subject..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <Button variant="outline" size="sm" onClick={() => setShowFilters(!showFilters)} data-testid="filter-btn">
          <Filter className="w-4 h-4 mr-1" /> Filters {showFilters && <ChevronDown className="w-3 h-3 ml-1" />}
        </Button>
      </div>

      {showFilters && (
        <div className="flex gap-3 items-center bg-slate-50 p-3 rounded-lg" data-testid="filter-bar">
          <select className="border rounded-lg px-3 py-1.5 text-sm" value={filter.is_open ?? ''} onChange={e => { setFilter(f => ({ ...f, is_open: e.target.value === '' ? null : e.target.value === 'true' })); setPage(1); }}>
            <option value="">All Status</option>
            <option value="true">Open</option>
            <option value="false">Closed</option>
          </select>
          <select className="border rounded-lg px-3 py-1.5 text-sm" value={filter.help_topic_id || ''} onChange={e => { setFilter(f => ({ ...f, help_topic_id: e.target.value || null })); setPage(1); }}>
            <option value="">All Topics</option>
            {helpTopics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <select className="border rounded-lg px-3 py-1.5 text-sm" value={filter.priority || ''} onChange={e => { setFilter(f => ({ ...f, priority: e.target.value || null })); setPage(1); }}>
            <option value="">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <Button variant="ghost" size="sm" onClick={() => { setFilter({ is_open: null, help_topic_id: null, priority: null }); setPage(1); }}>Clear</Button>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden" data-testid="tickets-table">
        <table className="w-full">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Ticket</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Subject</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Help Topic</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Stage</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Priority</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Assigned</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-12 text-slate-400">Loading...</td></tr>
            ) : tickets.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-12 text-slate-400">No tickets found</td></tr>
            ) : tickets.map(t => (
              <tr
                key={t.id}
                className="border-b hover:bg-slate-50 cursor-pointer transition-colors"
                onClick={() => navigate(`/admin/service-requests/${t.id}`)}
                data-testid={`ticket-row-${t.ticket_number}`}
              >
                <td className="px-4 py-3">
                  <span className="font-mono text-sm font-semibold text-blue-600">#{t.ticket_number}</span>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-slate-900 truncate max-w-[250px]">{t.subject}</p>
                  {t.company_name && <p className="text-xs text-slate-400">{t.company_name}</p>}
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{t.help_topic_name}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${t.is_open ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'}`}>
                    {t.current_stage_name || 'New'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[t.priority_name] || priorityColors.medium}`}>
                    {t.priority_name || 'medium'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-slate-500">{t.assigned_to_name || t.assigned_team_name || '-'}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-slate-400">{t.created_at ? new Date(t.created_at).toLocaleDateString() : '-'}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2" data-testid="pagination">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
          <span className="text-sm text-slate-500 self-center">Page {page} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
        </div>
      )}

      <CreateTicketModal open={showCreate} onClose={() => setShowCreate(false)} onCreated={fetchTickets} />
    </div>
  );
}
