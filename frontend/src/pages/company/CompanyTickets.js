import React, { useState, useEffect, useCallback } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import { 
  Ticket, Plus, Search, Filter, RefreshCw, Clock, 
  CheckCircle2, AlertTriangle, ArrowRight, Laptop,
  Calendar, User, MapPin, ChevronRight
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../components/ui/dialog';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { toast } from 'sonner';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  new: { label: 'New', color: 'bg-blue-100 text-blue-700 border-blue-300', icon: Ticket },
  pending_acceptance: { label: 'Pending', color: 'bg-purple-100 text-purple-700 border-purple-300', icon: Clock },
  assigned: { label: 'Assigned', color: 'bg-indigo-100 text-indigo-700 border-indigo-300', icon: User },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700 border-amber-300', icon: Clock },
  pending_parts: { label: 'Pending Parts', color: 'bg-orange-100 text-orange-700 border-orange-300', icon: AlertTriangle },
  completed: { label: 'Completed', color: 'bg-emerald-100 text-emerald-700 border-emerald-300', icon: CheckCircle2 },
  closed: { label: 'Closed', color: 'bg-slate-100 text-slate-700 border-slate-300', icon: CheckCircle2 },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700 border-red-300', icon: AlertTriangle },
};

const PRIORITY_CONFIG = {
  low: { label: 'Low', color: 'bg-slate-100 text-slate-600' },
  medium: { label: 'Medium', color: 'bg-blue-100 text-blue-600' },
  high: { label: 'High', color: 'bg-orange-100 text-orange-600' },
  critical: { label: 'Critical', color: 'bg-red-100 text-red-600' },
};

const CompanyTickets = () => {
  const { token } = useCompanyAuth();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [devices, setDevices] = useState([]);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [createLoading, setCreateLoading] = useState(false);
  
  // Filters
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  
  // Create ticket form
  const [newTicket, setNewTicket] = useState({
    device_id: searchParams.get('device') || '',
    title: '',
    description: '',
    priority: 'medium',
    contact_name: '',
    contact_phone: '',
    contact_email: '',
  });

  const headers = { Authorization: `Bearer ${token}` };

  const fetchTickets = useCallback(async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      if (statusFilter && statusFilter !== 'all') params.append('status', statusFilter);
      if (search) params.append('search', search);
      
      const response = await axios.get(`${API}/api/company/service-tickets?${params}`, { headers });
      setTickets(response.data.tickets || response.data || []);
    } catch (err) {
      console.error('Failed to fetch tickets:', err);
      toast.error('Failed to load service tickets');
    } finally {
      setLoading(false);
    }
  }, [token, statusFilter, search]);

  const fetchDevices = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/api/company/devices?limit=100`, { headers });
      setDevices(response.data.devices || response.data || []);
    } catch (err) {
      console.error('Failed to fetch devices:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchTickets();
    fetchDevices();
  }, [fetchTickets, fetchDevices]);

  // Open create modal if device param is present
  useEffect(() => {
    if (searchParams.get('device')) {
      setShowCreateModal(true);
    }
  }, [searchParams]);

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    
    if (!newTicket.title.trim()) {
      toast.error('Please enter a title');
      return;
    }
    if (!newTicket.description.trim()) {
      toast.error('Please describe the issue');
      return;
    }

    setCreateLoading(true);
    try {
      const response = await axios.post(`${API}/api/company/service-tickets`, newTicket, { headers });
      toast.success('Service request created successfully');
      setShowCreateModal(false);
      setNewTicket({
        device_id: '',
        title: '',
        description: '',
        priority: 'medium',
        contact_name: '',
        contact_phone: '',
        contact_email: '',
      });
      fetchTickets();
      
      // Navigate to the new ticket
      if (response.data?.id) {
        navigate(`/company/tickets/${response.data.id}`);
      }
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to create service request');
    } finally {
      setCreateLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric' 
    });
  };

  // Stats
  const openCount = tickets.filter(t => ['new', 'pending_acceptance', 'assigned', 'in_progress'].includes(t.status)).length;
  const pendingPartsCount = tickets.filter(t => t.status === 'pending_parts').length;
  const completedCount = tickets.filter(t => ['completed', 'closed'].includes(t.status)).length;

  return (
    <div data-testid="company-tickets-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Service Tickets</h1>
          <p className="text-slate-500 text-sm mt-1">Track and manage your service requests</p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={fetchTickets} variant="outline" disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Button 
            onClick={() => setShowCreateModal(true)} 
            className="bg-emerald-600 hover:bg-emerald-700"
            data-testid="create-ticket-btn"
          >
            <Plus className="h-4 w-4 mr-2" />
            New Service Request
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="bg-blue-50 border-blue-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-blue-600">Open Tickets</p>
                <p className="text-3xl font-bold text-blue-700">{openCount}</p>
              </div>
              <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                <Ticket className="h-6 w-6 text-blue-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-orange-50 border-orange-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-orange-600">Pending Parts</p>
                <p className="text-3xl font-bold text-orange-700">{pendingPartsCount}</p>
              </div>
              <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                <AlertTriangle className="h-6 w-6 text-orange-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card className="bg-emerald-50 border-emerald-100">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-emerald-600">Completed</p>
                <p className="text-3xl font-bold text-emerald-700">{completedCount}</p>
              </div>
              <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                <CheckCircle2 className="h-6 w-6 text-emerald-600" />
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="text-3xl font-bold text-slate-900">{tickets.length}</p>
              </div>
              <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center">
                <Ticket className="h-6 w-6 text-slate-600" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="Search tickets..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={statusFilter} onValueChange={setStatusFilter}>
              <SelectTrigger className="w-full md:w-48">
                <Filter className="h-4 w-4 mr-2" />
                <SelectValue placeholder="Filter by status" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Status</SelectItem>
                <SelectItem value="new">New</SelectItem>
                <SelectItem value="in_progress">In Progress</SelectItem>
                <SelectItem value="pending_parts">Pending Parts</SelectItem>
                <SelectItem value="completed">Completed</SelectItem>
                <SelectItem value="closed">Closed</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Tickets List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
            </div>
          ) : tickets.length === 0 ? (
            <div className="text-center py-12">
              <Ticket className="h-12 w-12 text-slate-300 mx-auto mb-4" />
              <p className="text-slate-500">No service tickets found</p>
              <p className="text-slate-400 text-sm mt-1">
                Create a new service request to get started.
              </p>
              <Button 
                onClick={() => setShowCreateModal(true)} 
                className="mt-4 bg-emerald-600 hover:bg-emerald-700"
              >
                <Plus className="h-4 w-4 mr-2" />
                New Service Request
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {tickets.map((ticket) => {
                const statusConfig = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.new;
                const priorityConfig = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
                
                return (
                  <Link 
                    key={ticket.id} 
                    to={`/company/tickets/${ticket.id}`}
                    className="flex items-center justify-between p-4 hover:bg-slate-50 transition-colors"
                    data-testid={`ticket-row-${ticket.id}`}
                  >
                    <div className="flex items-center gap-4 flex-1 min-w-0">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${statusConfig.color}`}>
                        <Ticket className="h-5 w-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <span className="font-mono text-sm text-emerald-600">#{ticket.ticket_number}</span>
                          <Badge className={`${statusConfig.color} border text-xs`}>
                            {statusConfig.label}
                          </Badge>
                          <Badge className={`${priorityConfig.color} text-xs`}>
                            {priorityConfig.label}
                          </Badge>
                        </div>
                        <p className="font-medium text-slate-900 truncate">{ticket.title}</p>
                        <div className="flex items-center gap-4 text-xs text-slate-500 mt-1">
                          {ticket.device_serial && (
                            <span className="flex items-center gap-1">
                              <Laptop className="h-3 w-3" />
                              {ticket.device_serial}
                            </span>
                          )}
                          <span className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            {formatDate(ticket.created_at)}
                          </span>
                          {ticket.assigned_to_name && (
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {ticket.assigned_to_name}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <ChevronRight className="h-5 w-5 text-slate-400" />
                  </Link>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Ticket Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Ticket className="h-5 w-5" />
              New Service Request
            </DialogTitle>
          </DialogHeader>
          
          <form onSubmit={handleCreateTicket} className="space-y-4 mt-4">
            {/* Device Selection */}
            <div className="space-y-2">
              <Label>Device (Optional)</Label>
              <Select 
                value={newTicket.device_id} 
                onValueChange={(value) => setNewTicket({...newTicket, device_id: value})}
              >
                <SelectTrigger>
                  <Laptop className="h-4 w-4 mr-2" />
                  <SelectValue placeholder="Select a device" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">No specific device</SelectItem>
                  {devices.map((device) => (
                    <SelectItem key={device.id} value={device.id}>
                      {device.serial_number} - {device.brand} {device.model}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Title */}
            <div className="space-y-2">
              <Label>Issue Title *</Label>
              <Input
                placeholder="Brief description of the issue"
                value={newTicket.title}
                onChange={(e) => setNewTicket({...newTicket, title: e.target.value})}
                required
              />
            </div>

            {/* Description */}
            <div className="space-y-2">
              <Label>Description *</Label>
              <Textarea
                placeholder="Please provide details about the issue..."
                value={newTicket.description}
                onChange={(e) => setNewTicket({...newTicket, description: e.target.value})}
                rows={4}
                required
              />
            </div>

            {/* Priority */}
            <div className="space-y-2">
              <Label>Priority</Label>
              <Select 
                value={newTicket.priority} 
                onValueChange={(value) => setNewTicket({...newTicket, priority: value})}
              >
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

            {/* Contact Info */}
            <div className="border-t pt-4 mt-4">
              <p className="text-sm font-medium text-slate-700 mb-3">Contact Information</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label>Contact Name</Label>
                  <Input
                    placeholder="Your name"
                    value={newTicket.contact_name}
                    onChange={(e) => setNewTicket({...newTicket, contact_name: e.target.value})}
                  />
                </div>
                <div className="space-y-2">
                  <Label>Phone Number</Label>
                  <Input
                    placeholder="+91 98765 43210"
                    value={newTicket.contact_phone}
                    onChange={(e) => setNewTicket({...newTicket, contact_phone: e.target.value})}
                  />
                </div>
              </div>
            </div>
          </form>
          
          <DialogFooter className="mt-6">
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button 
              onClick={handleCreateTicket} 
              disabled={createLoading}
              className="bg-emerald-600 hover:bg-emerald-700"
            >
              {createLoading ? 'Creating...' : 'Create Request'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CompanyTickets;
