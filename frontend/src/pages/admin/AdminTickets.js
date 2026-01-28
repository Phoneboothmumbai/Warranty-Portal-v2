import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Filter, Clock, AlertTriangle, CheckCircle2, 
  User, Building2, ChevronDown, MoreVertical, MessageSquare,
  RefreshCw, Inbox, AlertCircle, Timer, Users, X, UserPlus, Check
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Searchable Select Component
const SearchableSelect = ({ options, value, onChange, placeholder, displayKey = 'name', valueKey = 'id', disabled = false, icon: Icon, loading = false }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const containerRef = useRef(null);
  
  const filteredOptions = options.filter(opt => 
    (opt[displayKey] || '').toLowerCase().includes(search.toLowerCase()) ||
    (opt.email || '').toLowerCase().includes(search.toLowerCase())
  );
  
  const selectedOption = options.find(opt => opt[valueKey] === value);
  
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (containerRef.current && !containerRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);
  
  return (
    <div ref={containerRef} className="relative">
      <button
        type="button"
        disabled={disabled}
        onClick={() => setIsOpen(!isOpen)}
        className={`w-full px-3 py-2 border border-slate-200 rounded-lg text-sm text-left flex items-center justify-between ${disabled ? 'bg-slate-50 cursor-not-allowed' : 'bg-white hover:border-slate-300'}`}
      >
        <span className="flex items-center gap-2 truncate">
          {Icon && <Icon className="h-4 w-4 text-slate-400 flex-shrink-0" />}
          {selectedOption ? (
            <span className="text-slate-900">
              {selectedOption[displayKey]}
              {selectedOption.email && <span className="text-slate-400 ml-1">({selectedOption.email})</span>}
            </span>
          ) : (
            <span className="text-slate-400">{placeholder}</span>
          )}
        </span>
        <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute z-50 mt-1 w-full bg-white border border-slate-200 rounded-lg shadow-lg max-h-64 overflow-hidden">
          <div className="p-2 border-b border-slate-100">
            <div className="relative">
              <Search className="absolute left-2 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="Search..."
                className="w-full pl-8 pr-3 py-1.5 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>
          </div>
          <div className="overflow-y-auto max-h-48">
            {filteredOptions.length === 0 ? (
              <div className="px-3 py-4 text-sm text-slate-500 text-center">
                {options.length === 0 ? 'No options available' : 'No matches found'}
              </div>
            ) : (
              filteredOptions.map(opt => (
                <button
                  key={opt[valueKey]}
                  type="button"
                  onClick={() => {
                    onChange(opt[valueKey]);
                    setIsOpen(false);
                    setSearch('');
                  }}
                  className={`w-full px-3 py-2 text-sm text-left hover:bg-slate-50 flex items-center justify-between ${value === opt[valueKey] ? 'bg-blue-50' : ''}`}
                >
                  <span>
                    <span className="font-medium text-slate-900">{opt[displayKey]}</span>
                    {opt.email && <span className="text-slate-500 ml-2 text-xs">{opt.email}</span>}
                  </span>
                  {value === opt[valueKey] && <Check className="h-4 w-4 text-blue-600" />}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

const STATUS_CONFIG = {
  open: { label: 'Open', color: 'bg-blue-100 text-blue-700', icon: Inbox },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700', icon: RefreshCw },
  waiting_on_customer: { label: 'Waiting on Customer', color: 'bg-purple-100 text-purple-700', icon: Clock },
  waiting_on_third_party: { label: 'Waiting on 3rd Party', color: 'bg-orange-100 text-orange-700', icon: Users },
  on_hold: { label: 'On Hold', color: 'bg-slate-100 text-slate-600', icon: Clock },
  resolved: { label: 'Resolved', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2 },
  closed: { label: 'Closed', color: 'bg-slate-200 text-slate-500', icon: CheckCircle2 }
};

const PRIORITY_CONFIG = {
  low: { label: 'Low', color: 'bg-slate-100 text-slate-600' },
  medium: { label: 'Medium', color: 'bg-blue-100 text-blue-700' },
  high: { label: 'High', color: 'bg-orange-100 text-orange-700' },
  critical: { label: 'Critical', color: 'bg-red-100 text-red-700' }
};

export default function AdminTickets() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState(null);
  const [departments, setDepartments] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [companyUsers, setCompanyUsers] = useState([]);
  const [enums, setEnums] = useState(null);
  
  // Filters
  const [filters, setFilters] = useState({
    status: '',
    priority: '',
    department_id: '',
    assigned_to: '',
    company_id: '',
    unassigned: false,
    search: ''
  });
  
  // Create ticket modal
  const [showCreate, setShowCreate] = useState(false);
  const [selectedCompanyId, setSelectedCompanyId] = useState('');
  const [createData, setCreateData] = useState({
    subject: '',
    description: '',
    department_id: '',
    priority: 'medium',
    category: '',
    tags: '',
    requester_id: ''
  });
  const [creating, setCreating] = useState(false);
  const [loadingCompanyUsers, setLoadingCompanyUsers] = useState(false);
  
  // CC Participants for new ticket
  const [ccParticipants, setCcParticipants] = useState([]);
  const [newCcEmail, setNewCcEmail] = useState('');
  const [newCcName, setNewCcName] = useState('');

  const fetchData = useCallback(async () => {
    try {
      // Fetch data with individual error handling so one failure doesn't break everything
      const results = await Promise.allSettled([
        axios.get(`${API}/ticketing/admin/tickets`, {
          params: { ...filters, search: filters.search || undefined },
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/ticketing/admin/dashboard`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/ticketing/admin/departments`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/users`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/companies`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/ticketing/enums`)
      ]);
      
      // Extract data from settled promises
      const [ticketsRes, dashboardRes, deptsRes, adminsRes, companiesRes, enumsRes] = results;
      
      if (ticketsRes.status === 'fulfilled') {
        setTickets(ticketsRes.value.data.tickets || []);
      }
      if (dashboardRes.status === 'fulfilled') {
        setDashboard(dashboardRes.value.data);
      }
      if (deptsRes.status === 'fulfilled') {
        setDepartments(deptsRes.value.data || []);
      }
      if (adminsRes.status === 'fulfilled') {
        setAdmins(adminsRes.value.data || []);
      }
      if (companiesRes.status === 'fulfilled') {
        setCompanies(companiesRes.value.data || []);
        console.log('Companies loaded:', companiesRes.value.data?.length || 0);
      } else {
        console.error('Failed to load companies:', companiesRes.reason);
      }
      if (enumsRes.status === 'fulfilled') {
        setEnums(enumsRes.value.data);
      }
      
      // Show error if tickets failed to load
      if (ticketsRes.status === 'rejected') {
        toast.error('Failed to load tickets');
      }
    } catch (error) {
      console.error('Fetch error:', error);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token, filters]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const fetchCompanyUsers = async (companyId) => {
    if (!companyId) {
      setCompanyUsers([]);
      return;
    }
    setLoadingCompanyUsers(true);
    try {
      const res = await axios.get(`${API}/admin/company-users?company_id=${companyId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setCompanyUsers(res.data || []);
      console.log('Company users loaded:', res.data?.length || 0);
    } catch (error) {
      console.error('Failed to load company users:', error);
      toast.error('Failed to load company users');
      setCompanyUsers([]);
    } finally {
      setLoadingCompanyUsers(false);
    }
  };

  const addCcParticipant = () => {
    if (!newCcEmail.trim()) {
      toast.error('Please enter an email address');
      return;
    }
    // Basic email validation
    if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(newCcEmail.trim())) {
      toast.error('Please enter a valid email address');
      return;
    }
    // Check for duplicates
    if (ccParticipants.some(p => p.email.toLowerCase() === newCcEmail.trim().toLowerCase())) {
      toast.error('This email is already added');
      return;
    }
    setCcParticipants([...ccParticipants, {
      email: newCcEmail.trim(),
      name: newCcName.trim() || newCcEmail.trim().split('@')[0]
    }]);
    setNewCcEmail('');
    setNewCcName('');
  };

  const removeCcParticipant = (email) => {
    setCcParticipants(ccParticipants.filter(p => p.email !== email));
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!createData.requester_id) {
      toast.error('Please select a requester');
      return;
    }
    setCreating(true);
    try {
      const payload = {
        subject: createData.subject,
        description: createData.description,
        department_id: createData.department_id || undefined,
        priority: createData.priority,
        category: createData.category || undefined,
        tags: createData.tags ? createData.tags.split(',').map(t => t.trim()) : [],
        participants: ccParticipants.length > 0 ? ccParticipants : undefined
      };
      const res = await axios.post(
        `${API}/ticketing/admin/tickets?requester_id=${createData.requester_id}`,
        payload,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Ticket ${res.data.ticket_number} created${ccParticipants.length > 0 ? ` with ${ccParticipants.length} CC` : ''}`);
      setShowCreate(false);
      setSelectedCompanyId('');
      setCompanyUsers([]);
      setCreateData({ subject: '', description: '', department_id: '', priority: 'medium', category: '', tags: '', requester_id: '' });
      setCcParticipants([]);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setCreating(false);
    }
  };

  const handleQuickAssign = async (ticketId, assigneeId) => {
    try {
      await axios.post(
        `${API}/ticketing/admin/tickets/${ticketId}/assign?assignee_id=${assigneeId}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Ticket assigned');
      fetchData();
    } catch (error) {
      toast.error('Failed to assign ticket');
    }
  };

  const handleQuickStatus = async (ticketId, newStatus) => {
    try {
      await axios.put(
        `${API}/ticketing/admin/tickets/${ticketId}`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Status updated');
      fetchData();
    } catch (error) {
      toast.error('Failed to update status');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);
    
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  };

  const isSLABreached = (ticket) => {
    const sla = ticket.sla_status;
    if (!sla) return false;
    return sla.response_breached || sla.resolution_breached;
  };

  const getSLATimeRemaining = (ticket) => {
    const sla = ticket.sla_status;
    if (!sla || sla.is_paused) return null;
    
    const dueAt = ticket.first_response_at ? sla.resolution_due_at : sla.response_due_at;
    if (!dueAt) return null;
    
    const due = new Date(dueAt);
    const now = new Date();
    const diffMs = due - now;
    
    if (diffMs < 0) return { breached: true, text: 'Breached' };
    
    const hours = Math.floor(diffMs / 3600000);
    const mins = Math.floor((diffMs % 3600000) / 60000);
    
    if (hours > 24) return { breached: false, text: `${Math.floor(hours / 24)}d ${hours % 24}h` };
    return { breached: false, text: `${hours}h ${mins}m`, urgent: hours < 2 };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div data-testid="admin-tickets-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Support Tickets</h1>
          <p className="text-slate-500 text-sm">Manage and respond to support requests</p>
        </div>
        <Button onClick={() => setShowCreate(true)} data-testid="create-ticket-btn">
          <Plus className="h-4 w-4 mr-2" />
          Create Ticket
        </Button>
      </div>

      {/* Dashboard Stats */}
      {dashboard && (
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Inbox className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{dashboard.total_open}</p>
                <p className="text-xs text-slate-500">Open Tickets</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <User className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{dashboard.unassigned}</p>
                <p className="text-xs text-slate-500">Unassigned</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertTriangle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{dashboard.sla_breached}</p>
                <p className="text-xs text-slate-500">SLA Breached</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-orange-100 rounded-lg">
                <AlertCircle className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{dashboard.by_priority?.high || 0}</p>
                <p className="text-xs text-slate-500">High Priority</p>
              </div>
            </div>
          </div>
          <div className="bg-white rounded-xl border border-slate-200 p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <Timer className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{dashboard.by_priority?.critical || 0}</p>
                <p className="text-xs text-slate-500">Critical</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4">
        <div className="flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search tickets..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm"
            />
          </div>
          
          <select
            value={filters.status}
            onChange={(e) => setFilters({ ...filters, status: e.target.value })}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
          >
            <option value="">All Statuses</option>
            {enums?.statuses?.map(s => (
              <option key={s.value} value={s.value}>{s.label}</option>
            ))}
          </select>
          
          <select
            value={filters.priority}
            onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
          >
            <option value="">All Priorities</option>
            {enums?.priorities?.map(p => (
              <option key={p.value} value={p.value}>{p.label}</option>
            ))}
          </select>
          
          <select
            value={filters.department_id}
            onChange={(e) => setFilters({ ...filters, department_id: e.target.value })}
            className="px-3 py-2 border border-slate-200 rounded-lg text-sm"
          >
            <option value="">All Departments</option>
            {departments.map(d => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
          
          <label className="flex items-center gap-2 text-sm text-slate-600">
            <input
              type="checkbox"
              checked={filters.unassigned}
              onChange={(e) => setFilters({ ...filters, unassigned: e.target.checked })}
              className="rounded"
            />
            Unassigned only
          </label>
          
          <Button variant="outline" size="sm" onClick={fetchData}>
            <RefreshCw className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Ticket List */}
      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Ticket</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Requester</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Status</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Priority</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Assigned</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">SLA</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-slate-500 uppercase">Updated</th>
              <th className="text-right px-4 py-3 text-xs font-medium text-slate-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {tickets.length === 0 ? (
              <tr>
                <td colSpan={8} className="px-4 py-12 text-center text-slate-500">
                  <Inbox className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No tickets found</p>
                </td>
              </tr>
            ) : (
              tickets.map(ticket => {
                const statusConfig = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;
                const priorityConfig = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
                const slaTime = getSLATimeRemaining(ticket);
                const breached = isSLABreached(ticket);
                
                return (
                  <tr 
                    key={ticket.id} 
                    className="hover:bg-slate-50 cursor-pointer"
                    onClick={() => navigate(`/admin/tickets/${ticket.id}`)}
                  >
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-slate-900 text-sm">{ticket.ticket_number}</p>
                        <p className="text-sm text-slate-600 truncate max-w-[250px]">{ticket.subject}</p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <div className="h-8 w-8 bg-slate-100 rounded-full flex items-center justify-center">
                          <User className="h-4 w-4 text-slate-500" />
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-900">{ticket.requester_name}</p>
                          <p className="text-xs text-slate-500">{ticket.requester_email}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusConfig.color}`}>
                        {statusConfig.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityConfig.color}`}>
                        {priorityConfig.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      {ticket.assigned_to_name ? (
                        <span className="text-sm text-slate-700">{ticket.assigned_to_name}</span>
                      ) : (
                        <span className="text-sm text-amber-600 font-medium">Unassigned</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {breached ? (
                        <span className="px-2 py-1 bg-red-100 text-red-700 rounded text-xs font-medium flex items-center gap-1 w-fit">
                          <AlertTriangle className="h-3 w-3" />
                          Breached
                        </span>
                      ) : slaTime ? (
                        <span className={`px-2 py-1 rounded text-xs font-medium ${slaTime.urgent ? 'bg-amber-100 text-amber-700' : 'bg-slate-100 text-slate-600'}`}>
                          {slaTime.text}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-500">
                      {formatDate(ticket.updated_at)}
                    </td>
                    <td className="px-4 py-3 text-right" onClick={(e) => e.stopPropagation()}>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => navigate(`/admin/tickets/${ticket.id}`)}>
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleQuickStatus(ticket.id, 'in_progress')}>
                            Mark In Progress
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => handleQuickStatus(ticket.id, 'resolved')}>
                            Mark Resolved
                          </DropdownMenuItem>
                          {admins.slice(0, 5).map(admin => (
                            <DropdownMenuItem key={admin.id} onClick={() => handleQuickAssign(ticket.id, admin.id)}>
                              Assign to {admin.name}
                            </DropdownMenuItem>
                          ))}
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Create Ticket Modal */}
      <Dialog open={showCreate} onOpenChange={(open) => {
        setShowCreate(open);
        if (!open) {
          setSelectedCompanyId('');
          setCompanyUsers([]);
          setCreateData({ subject: '', description: '', department_id: '', priority: 'medium', category: '', tags: '', requester_id: '' });
          setCcParticipants([]);
          setNewCcEmail('');
          setNewCcName('');
        }
      }}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create New Ticket</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTicket} className="space-y-4">
            {/* Company Selection */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Company *</label>
                <SearchableSelect
                  options={companies}
                  value={selectedCompanyId}
                  onChange={(val) => {
                    setSelectedCompanyId(val);
                    setCreateData({ ...createData, requester_id: '' });
                    fetchCompanyUsers(val);
                  }}
                  placeholder="Search & select company..."
                  displayKey="name"
                  valueKey="id"
                  icon={Building2}
                />
                {!selectedCompanyId && <input type="hidden" name="company_required" required />}
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Requester *</label>
                <SearchableSelect
                  options={companyUsers}
                  value={createData.requester_id}
                  onChange={(val) => setCreateData({ ...createData, requester_id: val })}
                  placeholder={selectedCompanyId ? "Search & select requester..." : "Select company first"}
                  displayKey="name"
                  valueKey="id"
                  disabled={!selectedCompanyId}
                  icon={User}
                />
                {!createData.requester_id && <input type="hidden" name="requester_required" required />}
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Subject *</label>
              <input
                type="text"
                required
                value={createData.subject}
                onChange={(e) => setCreateData({ ...createData, subject: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="Brief description of the issue"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Description *</label>
              <textarea
                required
                rows={4}
                value={createData.description}
                onChange={(e) => setCreateData({ ...createData, description: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm resize-none"
                placeholder="Detailed description of the issue..."
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
                  <option value="">Select Department</option>
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
                  {enums?.priorities?.map(p => (
                    <option key={p.value} value={p.value}>{p.label}</option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Tags (comma-separated)</label>
              <input
                type="text"
                value={createData.tags}
                onChange={(e) => setCreateData({ ...createData, tags: e.target.value })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="laptop, hardware, urgent"
              />
            </div>

            {/* CC / Participants Section */}
            <div className="border border-slate-200 rounded-lg p-4 bg-slate-50">
              <label className="text-sm font-medium text-slate-700 flex items-center gap-2 mb-3">
                <Users className="h-4 w-4" />
                CC / Additional Recipients
                <span className="text-xs text-slate-500 font-normal">(will receive email updates)</span>
              </label>
              
              {/* Added participants */}
              {ccParticipants.length > 0 && (
                <div className="flex flex-wrap gap-2 mb-3">
                  {ccParticipants.map((p, idx) => (
                    <div key={idx} className="flex items-center gap-2 bg-white border border-slate-200 rounded-full px-3 py-1 text-sm">
                      <User className="h-3 w-3 text-slate-400" />
                      <span className="text-slate-700">{p.name}</span>
                      <span className="text-slate-400 text-xs">({p.email})</span>
                      <button
                        type="button"
                        onClick={() => removeCcParticipant(p.email)}
                        className="text-slate-400 hover:text-red-500 ml-1"
                      >
                        <X className="h-3 w-3" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              
              {/* Add new participant */}
              <div className="flex gap-2">
                <input
                  type="text"
                  value={newCcName}
                  onChange={(e) => setNewCcName(e.target.value)}
                  className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
                  placeholder="Name (optional)"
                />
                <input
                  type="email"
                  value={newCcEmail}
                  onChange={(e) => setNewCcEmail(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addCcParticipant())}
                  className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
                  placeholder="Email address"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={addCcParticipant}
                  className="flex items-center gap-1"
                >
                  <UserPlus className="h-4 w-4" />
                  Add
                </Button>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
              <Button type="submit" disabled={creating}>
                {creating ? 'Creating...' : 'Create Ticket'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
