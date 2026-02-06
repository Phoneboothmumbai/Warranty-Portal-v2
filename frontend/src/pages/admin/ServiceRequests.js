import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { Label } from '../../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import { 
  Plus, Search, Clock, User,
  Wrench, AlertCircle, CheckCircle2, XCircle, Play,
  RefreshCw, Calendar, FileText, MoreVertical, UserPlus,
  Timer, Package, ChevronRight, Building2
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status configuration
const STATUS_CONFIG = {
  new: { label: 'New', color: 'bg-slate-100 text-slate-800 border-slate-300', icon: FileText },
  assigned: { label: 'Assigned', color: 'bg-blue-100 text-blue-800 border-blue-300', icon: UserPlus },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-800 border-amber-300', icon: Play },
  pending_parts: { label: 'Pending Parts', color: 'bg-orange-100 text-orange-800 border-orange-300', icon: Package },
  completed: { label: 'Completed', color: 'bg-green-100 text-green-800 border-green-300', icon: CheckCircle2 },
  closed: { label: 'Closed', color: 'bg-emerald-100 text-emerald-800 border-emerald-300', icon: CheckCircle2 },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-500 border-red-300', icon: XCircle }
};

const PRIORITY_CONFIG = {
  low: { label: 'Low', color: 'bg-slate-100 text-slate-700' },
  medium: { label: 'Medium', color: 'bg-yellow-100 text-yellow-700' },
  high: { label: 'High', color: 'bg-orange-100 text-orange-700' },
  critical: { label: 'Critical', color: 'bg-red-100 text-red-700' }
};

// Status Badge Component
const StatusBadge = ({ status }) => {
  const config = STATUS_CONFIG[status] || STATUS_CONFIG.new;
  const Icon = config.icon;
  return (
    <Badge variant="outline" className={`${config.color} gap-1`}>
      <Icon className="h-3 w-3" />
      {config.label}
    </Badge>
  );
};

// Priority Badge Component
const PriorityBadge = ({ priority }) => {
  const config = PRIORITY_CONFIG[priority] || PRIORITY_CONFIG.medium;
  return (
    <Badge variant="outline" className={config.color}>
      {config.label}
    </Badge>
  );
};

export default function ServiceRequests() {
  const token = localStorage.getItem('admin_token');
  
  // Data state
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({ total: 0, open: 0, closed: 0, urgent: 0, by_status: {}, by_priority: {} });
  const [loading, setLoading] = useState(true);
  const [companies, setCompanies] = useState([]);
  const [staff, setStaff] = useState([]);
  const [problems, setProblems] = useState([]);
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Modal state
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [creating, setCreating] = useState(false);
  
  // Form state
  const [formData, setFormData] = useState({
    company_id: '',
    title: '',
    description: '',
    priority: 'medium',
    problem_id: '',
    contact_name: '',
    contact_phone: '',
    contact_email: '',
    is_urgent: false
  });

  // Fetch tickets
  const fetchTickets = useCallback(async () => {
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const params = new URLSearchParams({ page, limit: 20 });
      if (searchQuery) params.append('search', searchQuery);
      if (filterStatus !== 'all') params.append('status', filterStatus);
      if (filterPriority !== 'all') params.append('priority', filterPriority);
      
      const res = await axios.get(`${API_URL}/api/admin/service-tickets?${params}`, { headers });
      setTickets(res.data.tickets || []);
      setTotalPages(res.data.pages || 1);
    } catch (error) {
      console.error('Failed to fetch tickets:', error);
      toast.error('Failed to load tickets');
    }
  }, [page, searchQuery, filterStatus, filterPriority, token]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const res = await axios.get(`${API_URL}/api/admin/service-tickets/stats`, { headers });
      setStats(res.data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, [token]);

  // Fetch supporting data
  const fetchSupportingData = useCallback(async () => {
    const headers = { Authorization: `Bearer ${token}` };
    try {
      const [companiesRes, staffRes, problemsRes] = await Promise.all([
        axios.get(`${API_URL}/api/admin/companies?limit=500`, { headers }),
        axios.get(`${API_URL}/api/admin/staff/users?limit=100`, { headers }),
        axios.get(`${API_URL}/api/admin/problems`, { headers })
      ]);
      setCompanies(companiesRes.data.companies || []);
      setStaff(staffRes.data.users || []);
      setProblems(problemsRes.data.problems || []);
    } catch (error) {
      console.error('Failed to fetch supporting data:', error);
    }
  }, [token]);

  const headers = { Authorization: `Bearer ${token}` };

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchTickets(), fetchStats(), fetchSupportingData()]);
      setLoading(false);
    };
    loadData();
  }, [fetchTickets, fetchStats, fetchSupportingData]);

  // Create ticket
  const handleCreateTicket = async () => {
    if (!formData.company_id) {
      toast.error('Please select a company');
      return;
    }
    if (!formData.title.trim()) {
      toast.error('Please enter a title');
      return;
    }

    setCreating(true);
    try {
      const res = await axios.post(`${API_URL}/api/admin/service-tickets`, formData, { headers });
      toast.success(`Ticket ${res.data.ticket_number} created successfully`);
      setShowCreateModal(false);
      resetForm();
      fetchTickets();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create ticket');
    } finally {
      setCreating(false);
    }
  };

  // Assign ticket
  const handleAssignTicket = async (ticketId, technicianId) => {
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/assign`, 
        { technician_id: technicianId }, 
        { headers }
      );
      toast.success('Ticket assigned successfully');
      setShowAssignModal(false);
      fetchTickets();
      fetchStats();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign ticket');
    }
  };

  // Status actions
  const handleStatusAction = async (ticketId, action, data = {}) => {
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/${action}`, data, { headers });
      toast.success(`Ticket ${action} successful`);
      fetchTickets();
      fetchStats();
      if (selectedTicket?.id === ticketId) {
        fetchTicketDetail(ticketId);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || `Failed to ${action} ticket`);
    }
  };

  // Fetch ticket detail
  const fetchTicketDetail = async (ticketId) => {
    try {
      const res = await axios.get(`${API_URL}/api/admin/service-tickets/${ticketId}`, { headers });
      setSelectedTicket(res.data);
    } catch (error) {
      toast.error('Failed to load ticket details');
    }
  };

  // View ticket detail
  const handleViewTicket = async (ticket) => {
    await fetchTicketDetail(ticket.id);
    setShowDetailModal(true);
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      company_id: '',
      title: '',
      description: '',
      priority: 'medium',
      problem_id: '',
      contact_name: '',
      contact_phone: '',
      contact_email: '',
      is_urgent: false
    });
  };

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div data-testid="service-tickets-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Service Tickets</h1>
          <p className="text-slate-500 text-sm">Manage service requests and field operations</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} data-testid="new-ticket-btn">
          <Plus className="h-4 w-4 mr-2" />
          New Ticket
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-white">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
                <p className="text-xs text-slate-500">Total Tickets</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-amber-100 rounded-lg">
                <Clock className="h-5 w-5 text-amber-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.open}</p>
                <p className="text-xs text-slate-500">Open</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.closed}</p>
                <p className="text-xs text-slate-500">Closed</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-white">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-red-100 rounded-lg">
                <AlertCircle className="h-5 w-5 text-red-600" />
              </div>
              <div>
                <p className="text-2xl font-bold text-slate-900">{stats.urgent}</p>
                <p className="text-xs text-slate-500">Urgent</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card className="bg-white">
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Search by ticket, title, customer..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                  data-testid="search-input"
                />
              </div>
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-[160px]" data-testid="status-filter">
                <SelectValue placeholder="All Statuses" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Statuses</SelectItem>
                {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>{config.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger className="w-[160px]" data-testid="priority-filter">
                <SelectValue placeholder="All Priorities" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                {Object.entries(PRIORITY_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>{config.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={() => { fetchTickets(); fetchStats(); }}>
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Tickets List */}
      <Card className="bg-white">
        <CardContent className="p-0">
          {tickets.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-500">
              <Wrench className="h-12 w-12 mb-4 text-slate-300" />
              <p className="text-lg">No service tickets found</p>
              <Button variant="outline" className="mt-4" onClick={() => setShowCreateModal(true)}>
                Create First Ticket
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {tickets.map((ticket) => (
                <div
                  key={ticket.id}
                  className="p-4 hover:bg-slate-50 transition-colors cursor-pointer"
                  onClick={() => handleViewTicket(ticket)}
                  data-testid={`ticket-row-${ticket.ticket_number}`}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-mono text-sm font-semibold text-blue-600">
                          #{ticket.ticket_number}
                        </span>
                        <StatusBadge status={ticket.status} />
                        <PriorityBadge priority={ticket.priority} />
                        {ticket.is_urgent && (
                          <Badge variant="destructive" className="text-xs">URGENT</Badge>
                        )}
                      </div>
                      <h3 className="font-medium text-slate-900 truncate">{ticket.title}</h3>
                      <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                        <span className="flex items-center gap-1">
                          <Building2 className="h-3.5 w-3.5" />
                          {ticket.company_name}
                        </span>
                        {ticket.assigned_to_name && (
                          <span className="flex items-center gap-1">
                            <User className="h-3.5 w-3.5" />
                            {ticket.assigned_to_name}
                          </span>
                        )}
                        <span className="flex items-center gap-1">
                          <Calendar className="h-3.5 w-3.5" />
                          {formatDate(ticket.created_at)}
                        </span>
                        {ticket.total_time_minutes > 0 && (
                          <span className="flex items-center gap-1">
                            <Timer className="h-3.5 w-3.5" />
                            {ticket.total_time_minutes}m
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={(e) => { e.stopPropagation(); handleViewTicket(ticket); }}>
                            View Details
                          </DropdownMenuItem>
                          {ticket.status === 'new' && (
                            <DropdownMenuItem onClick={(e) => { 
                              e.stopPropagation(); 
                              setSelectedTicket(ticket);
                              setShowAssignModal(true);
                            }}>
                              Assign Technician
                            </DropdownMenuItem>
                          )}
                          {ticket.status === 'assigned' && (
                            <DropdownMenuItem onClick={(e) => { 
                              e.stopPropagation(); 
                              handleStatusAction(ticket.id, 'start');
                            }}>
                              Start Work
                            </DropdownMenuItem>
                          )}
                          {ticket.status === 'in_progress' && (
                            <>
                              <DropdownMenuItem onClick={(e) => { 
                                e.stopPropagation(); 
                                handleStatusAction(ticket.id, 'pending-parts');
                              }}>
                                Mark Pending Parts
                              </DropdownMenuItem>
                              <DropdownMenuItem onClick={(e) => { 
                                e.stopPropagation(); 
                                handleStatusAction(ticket.id, 'complete', {
                                  resolution_summary: 'Issue resolved',
                                  resolution_type: 'fixed'
                                });
                              }}>
                                Complete
                              </DropdownMenuItem>
                            </>
                          )}
                          {ticket.status === 'completed' && (
                            <DropdownMenuItem onClick={(e) => { 
                              e.stopPropagation(); 
                              handleStatusAction(ticket.id, 'close');
                            }}>
                              Close Ticket
                            </DropdownMenuItem>
                          )}
                          <DropdownMenuSeparator />
                          {!['closed', 'cancelled'].includes(ticket.status) && (
                            <DropdownMenuItem 
                              className="text-red-600"
                              onClick={(e) => { 
                                e.stopPropagation(); 
                                handleStatusAction(ticket.id, 'cancel', {
                                  cancellation_reason: 'Cancelled by admin'
                                });
                              }}
                            >
                              Cancel Ticket
                            </DropdownMenuItem>
                          )}
                        </DropdownMenuContent>
                      </DropdownMenu>
                      <ChevronRight className="h-5 w-5 text-slate-400" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex justify-center gap-2">
          <Button
            variant="outline"
            size="sm"
            disabled={page === 1}
            onClick={() => setPage(p => Math.max(1, p - 1))}
          >
            Previous
          </Button>
          <span className="flex items-center px-4 text-sm text-slate-600">
            Page {page} of {totalPages}
          </span>
          <Button
            variant="outline"
            size="sm"
            disabled={page === totalPages}
            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
          >
            Next
          </Button>
        </div>
      )}

      {/* Create Ticket Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Service Ticket</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Company *</Label>
              <Select value={formData.company_id} onValueChange={(val) => setFormData({...formData, company_id: val})}>
                <SelectTrigger data-testid="company-select">
                  <SelectValue placeholder="Select company" />
                </SelectTrigger>
                <SelectContent>
                  {companies.map((c) => (
                    <SelectItem key={c.id} value={c.id}>{c.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Title *</Label>
              <Input
                value={formData.title}
                onChange={(e) => setFormData({...formData, title: e.target.value})}
                placeholder="Brief description of the issue"
                data-testid="title-input"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea
                value={formData.description}
                onChange={(e) => setFormData({...formData, description: e.target.value})}
                placeholder="Detailed description..."
                rows={3}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Priority</Label>
                <Select value={formData.priority} onValueChange={(val) => setFormData({...formData, priority: val})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="medium">Medium</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Problem Type</Label>
                <Select value={formData.problem_id} onValueChange={(val) => setFormData({...formData, problem_id: val})}>
                  <SelectTrigger>
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {problems.map((p) => (
                      <SelectItem key={p.id} value={p.id}>{p.name}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Contact Name</Label>
                <Input
                  value={formData.contact_name}
                  onChange={(e) => setFormData({...formData, contact_name: e.target.value})}
                  placeholder="Contact person"
                />
              </div>
              <div>
                <Label>Contact Phone</Label>
                <Input
                  value={formData.contact_phone}
                  onChange={(e) => setFormData({...formData, contact_phone: e.target.value})}
                  placeholder="Phone number"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="is_urgent"
                checked={formData.is_urgent}
                onChange={(e) => setFormData({...formData, is_urgent: e.target.checked})}
                className="rounded"
              />
              <Label htmlFor="is_urgent" className="text-sm font-normal">Mark as Urgent</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button onClick={handleCreateTicket} disabled={creating} data-testid="create-btn">
              {creating ? 'Creating...' : 'Create Ticket'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Modal */}
      <Dialog open={showAssignModal} onOpenChange={setShowAssignModal}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Assign Technician</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Assign ticket <span className="font-mono font-semibold">#{selectedTicket?.ticket_number}</span> to a technician
            </p>
            <div className="space-y-2">
              {staff.filter(s => s.state === 'active').map((tech) => (
                <div
                  key={tech.id}
                  className="flex items-center justify-between p-3 border rounded-lg hover:bg-slate-50 cursor-pointer"
                  onClick={() => handleAssignTicket(selectedTicket?.id, tech.id)}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <User className="h-4 w-4 text-blue-600" />
                    </div>
                    <div>
                      <p className="font-medium text-slate-900">{tech.name}</p>
                      <p className="text-xs text-slate-500">{tech.email}</p>
                    </div>
                  </div>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </div>
              ))}
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span className="font-mono text-blue-600">#{selectedTicket?.ticket_number}</span>
              <StatusBadge status={selectedTicket?.status} />
              <PriorityBadge priority={selectedTicket?.priority} />
            </DialogTitle>
          </DialogHeader>
          {selectedTicket && (
            <div className="space-y-6">
              {/* Basic Info */}
              <div>
                <h3 className="text-lg font-semibold text-slate-900">{selectedTicket.title}</h3>
                {selectedTicket.description && (
                  <p className="text-slate-600 mt-1">{selectedTicket.description}</p>
                )}
              </div>

              {/* Details Grid */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500">Company</p>
                  <p className="font-medium">{selectedTicket.company_name}</p>
                </div>
                <div>
                  <p className="text-slate-500">Assigned To</p>
                  <p className="font-medium">{selectedTicket.assigned_to_name || 'Unassigned'}</p>
                </div>
                <div>
                  <p className="text-slate-500">Created</p>
                  <p className="font-medium">{formatDate(selectedTicket.created_at)}</p>
                </div>
                <div>
                  <p className="text-slate-500">Total Time</p>
                  <p className="font-medium">{selectedTicket.total_time_minutes || 0} minutes</p>
                </div>
                {selectedTicket.contact && (
                  <>
                    <div>
                      <p className="text-slate-500">Contact</p>
                      <p className="font-medium">{selectedTicket.contact.name}</p>
                    </div>
                    <div>
                      <p className="text-slate-500">Phone</p>
                      <p className="font-medium">{selectedTicket.contact.phone || '-'}</p>
                    </div>
                  </>
                )}
              </div>

              {/* Status History */}
              {selectedTicket.status_history?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2">Status History</h4>
                  <div className="space-y-2">
                    {selectedTicket.status_history.map((h, idx) => (
                      <div key={idx} className="flex items-center gap-2 text-sm">
                        <div className="w-2 h-2 rounded-full bg-blue-500" />
                        <span className="text-slate-600">{formatDate(h.changed_at)}</span>
                        <span className="text-slate-900">
                          {h.from_status ? `${h.from_status} → ` : ''}{h.to_status}
                        </span>
                        <span className="text-slate-500">by {h.changed_by_name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Visits */}
              {selectedTicket.visits?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-slate-900 mb-2">Visits ({selectedTicket.visits.length})</h4>
                  <div className="space-y-2">
                    {selectedTicket.visits.map((visit) => (
                      <div key={visit.id} className="p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="font-medium">Visit #{visit.visit_number}</span>
                          <Badge variant="outline">{visit.status}</Badge>
                        </div>
                        <p className="text-sm text-slate-600 mt-1">
                          {visit.technician_name} • {visit.duration_minutes || 0} min
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 pt-4 border-t">
                {selectedTicket.status === 'new' && (
                  <Button onClick={() => { setShowDetailModal(false); setShowAssignModal(true); }}>
                    <UserPlus className="h-4 w-4 mr-2" />
                    Assign
                  </Button>
                )}
                {selectedTicket.status === 'assigned' && (
                  <Button onClick={() => handleStatusAction(selectedTicket.id, 'start')}>
                    <Play className="h-4 w-4 mr-2" />
                    Start Work
                  </Button>
                )}
                {selectedTicket.status === 'in_progress' && (
                  <Button onClick={() => handleStatusAction(selectedTicket.id, 'complete', {
                    resolution_summary: 'Issue resolved',
                    resolution_type: 'fixed'
                  })}>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Complete
                  </Button>
                )}
                {selectedTicket.status === 'completed' && (
                  <Button onClick={() => handleStatusAction(selectedTicket.id, 'close')}>
                    <CheckCircle2 className="h-4 w-4 mr-2" />
                    Close Ticket
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
