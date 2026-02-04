import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { Label } from '../../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { 
  Plus, Search, Filter, Clock, User, MapPin, Phone, Mail, 
  Wrench, AlertCircle, CheckCircle2, XCircle, ArrowRight,
  ChevronRight, RefreshCw, Calendar, Hash, FileText
} from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// State colors mapping
const STATE_COLORS = {
  CREATED: 'bg-slate-100 text-slate-800 border-slate-200',
  ASSIGNED: 'bg-blue-100 text-blue-800 border-blue-200',
  DECLINED: 'bg-red-100 text-red-800 border-red-200',
  ACCEPTED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  VISIT_IN_PROGRESS: 'bg-amber-100 text-amber-800 border-amber-200',
  VISIT_COMPLETED: 'bg-teal-100 text-teal-800 border-teal-200',
  PENDING_PART: 'bg-orange-100 text-orange-800 border-orange-200',
  PENDING_APPROVAL: 'bg-purple-100 text-purple-800 border-purple-200',
  REPAIR_IN_PROGRESS: 'bg-indigo-100 text-indigo-800 border-indigo-200',
  QC_PENDING: 'bg-cyan-100 text-cyan-800 border-cyan-200',
  READY_FOR_RETURN: 'bg-green-100 text-green-800 border-green-200',
  RESOLVED: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  CANCELLED: 'bg-slate-100 text-slate-500 border-slate-200'
};

const PRIORITY_COLORS = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  urgent: 'bg-red-100 text-red-700'
};

export default function ServiceRequests() {
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [stats, setStats] = useState({ total: 0, open: 0, closed: 0, by_state: {} });
  const [states, setStates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterState, setFilterState] = useState('all');
  const [filterPriority, setFilterPriority] = useState('all');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  
  // Modals
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedRequest, setSelectedRequest] = useState(null);
  const [showTransitionModal, setShowTransitionModal] = useState(false);
  const [transitionTarget, setTransitionTarget] = useState(null);
  
  // Form state
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    category: 'repair',
    priority: 'medium',
    customer_name: '',
    customer_email: '',
    customer_mobile: '',
    customer_company_name: '',
    location_address: '',
    location_city: '',
    location_pincode: '',
    device_serial: '',
    device_name: ''
  });
  
  // Transition form
  const [transitionData, setTransitionData] = useState({
    reason: '',
    staff_id: '',
    decline_reason: '',
    diagnostics: '',
    resolution_notes: '',
    cancellation_reason: '',
    approval_amount: ''
  });

  const fetchStats = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/service-requests/stats`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  }, []);

  const fetchStates = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/service-requests/states`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (response.ok) {
        const data = await response.json();
        setStates(data.states || []);
      }
    } catch (error) {
      console.error('Failed to fetch states:', error);
    }
  }, []);

  const fetchRequests = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({ page, limit: 20 });
      
      if (searchQuery) params.append('search', searchQuery);
      if (filterState !== 'all') params.append('state', filterState);
      if (filterPriority !== 'all') params.append('priority', filterPriority);
      
      const response = await fetch(`${API_URL}/api/admin/service-requests?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setRequests(data.service_requests || []);
        setTotalPages(data.pages || 1);
      }
    } catch (error) {
      console.error('Failed to fetch requests:', error);
      toast.error('Failed to load service requests');
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery, filterState, filterPriority]);

  const fetchRequestDetail = async (requestId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/service-requests/${requestId}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      
      if (response.ok) {
        const data = await response.json();
        setSelectedRequest(data);
        setShowDetailModal(true);
      }
    } catch (error) {
      console.error('Failed to fetch request detail:', error);
      toast.error('Failed to load request details');
    }
  };

  useEffect(() => {
    fetchStats();
    fetchStates();
  }, [fetchStats, fetchStates]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const handleCreateRequest = async (e) => {
    e.preventDefault();
    
    if (!formData.title.trim()) {
      toast.error('Title is required');
      return;
    }
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/admin/service-requests`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });
      
      if (response.ok) {
        const data = await response.json();
        toast.success(`Service request created: ${data.service_request?.ticket_number}`);
        setShowCreateModal(false);
        setFormData({
          title: '', description: '', category: 'repair', priority: 'medium',
          customer_name: '', customer_email: '', customer_mobile: '',
          customer_company_name: '', location_address: '', location_city: '',
          location_pincode: '', device_serial: '', device_name: ''
        });
        fetchRequests();
        fetchStats();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Failed to create request');
      }
    } catch (error) {
      console.error('Failed to create request:', error);
      toast.error('Failed to create service request');
    }
  };

  const handleTransition = async () => {
    if (!selectedRequest || !transitionTarget) return;
    
    try {
      const token = localStorage.getItem('token');
      const body = {
        target_state: transitionTarget.state,
        reason: transitionData.reason
      };
      
      // Add state-specific data
      if (transitionTarget.state === 'ASSIGNED' && transitionData.staff_id) {
        body.assigned_staff_id = transitionData.staff_id;
      }
      if (transitionTarget.state === 'DECLINED') {
        body.decline_reason = transitionData.decline_reason;
      }
      if (transitionTarget.state === 'VISIT_COMPLETED') {
        body.diagnostics = transitionData.diagnostics;
      }
      if (transitionTarget.state === 'RESOLVED') {
        body.resolution_notes = transitionData.resolution_notes;
      }
      if (transitionTarget.state === 'CANCELLED') {
        body.cancellation_reason = transitionData.cancellation_reason;
      }
      if (transitionTarget.state === 'PENDING_APPROVAL' && transitionData.approval_amount) {
        body.approval_amount = parseFloat(transitionData.approval_amount);
      }
      
      const response = await fetch(
        `${API_URL}/api/admin/service-requests/${selectedRequest.id}/transition`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(body)
        }
      );
      
      if (response.ok) {
        const data = await response.json();
        toast.success(`Transitioned to ${transitionTarget.label}`);
        setShowTransitionModal(false);
        setTransitionTarget(null);
        setTransitionData({
          reason: '', staff_id: '', decline_reason: '', diagnostics: '',
          resolution_notes: '', cancellation_reason: '', approval_amount: ''
        });
        setSelectedRequest(data.service_request);
        fetchRequests();
        fetchStats();
      } else {
        const error = await response.json();
        toast.error(error.detail || 'Transition failed');
      }
    } catch (error) {
      console.error('Transition failed:', error);
      toast.error('Failed to transition state');
    }
  };

  const openTransitionModal = (transition) => {
    setTransitionTarget(transition);
    setShowTransitionModal(true);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <div className="space-y-6" data-testid="service-requests-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Service Requests</h1>
          <p className="text-slate-500">FSM-driven service request management</p>
        </div>
        <Button onClick={() => setShowCreateModal(true)} data-testid="create-request-btn">
          <Plus className="h-4 w-4 mr-2" />
          New Request
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Total</p>
                <p className="text-2xl font-bold">{stats.total}</p>
              </div>
              <FileText className="h-8 w-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Open</p>
                <p className="text-2xl font-bold text-blue-600">{stats.open}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Resolved</p>
                <p className="text-2xl font-bold text-green-600">{stats.by_state?.RESOLVED || 0}</p>
              </div>
              <CheckCircle2 className="h-8 w-8 text-green-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-500">Cancelled</p>
                <p className="text-2xl font-bold text-slate-600">{stats.by_state?.CANCELLED || 0}</p>
              </div>
              <XCircle className="h-8 w-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="pt-4">
          <div className="flex flex-wrap gap-4 items-center">
            <div className="flex-1 min-w-[200px]">
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
            
            <Select value={filterState} onValueChange={setFilterState}>
              <SelectTrigger className="w-[180px]" data-testid="filter-state">
                <SelectValue placeholder="Filter by state" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All States</SelectItem>
                {states.map(s => (
                  <SelectItem key={s.value} value={s.value}>{s.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={filterPriority} onValueChange={setFilterPriority}>
              <SelectTrigger className="w-[150px]" data-testid="filter-priority">
                <SelectValue placeholder="Priority" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Priorities</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="urgent">Urgent</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" onClick={fetchRequests} data-testid="refresh-btn">
              <RefreshCw className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Requests List */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-8 text-center text-slate-500">Loading...</div>
          ) : requests.length === 0 ? (
            <div className="p-8 text-center text-slate-500">
              <Wrench className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <p>No service requests found</p>
              <Button onClick={() => setShowCreateModal(true)} className="mt-4" variant="outline">
                Create First Request
              </Button>
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {requests.map((req) => (
                <div 
                  key={req.id} 
                  className="p-4 hover:bg-slate-50 cursor-pointer transition-colors"
                  onClick={() => fetchRequestDetail(req.id)}
                  data-testid={`request-row-${req.ticket_number}`}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="min-w-[80px]">
                        <span className="font-mono font-bold text-slate-900">{req.ticket_number}</span>
                      </div>
                      <div>
                        <h3 className="font-medium text-slate-900">{req.title}</h3>
                        <div className="flex items-center gap-2 text-sm text-slate-500 mt-1">
                          {req.customer_snapshot?.name && (
                            <span className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {req.customer_snapshot.name}
                            </span>
                          )}
                          <span>•</span>
                          <span>{formatDate(req.created_at)}</span>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Badge className={PRIORITY_COLORS[req.priority] || 'bg-slate-100'}>
                        {req.priority}
                      </Badge>
                      <Badge className={`${STATE_COLORS[req.state] || 'bg-slate-100'} border`}>
                        {req.state_metadata?.label || req.state}
                      </Badge>
                      <ChevronRight className="h-5 w-5 text-slate-400" />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between p-4 border-t border-slate-100">
              <Button 
                variant="outline" 
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                Previous
              </Button>
              <span className="text-sm text-slate-500">Page {page} of {totalPages}</span>
              <Button 
                variant="outline" 
                disabled={page === totalPages}
                onClick={() => setPage(p => p + 1)}
              >
                Next
              </Button>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Request Modal */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Create Service Request</DialogTitle>
            <DialogDescription>Enter details for the new service request</DialogDescription>
          </DialogHeader>
          
          <form onSubmit={handleCreateRequest} className="space-y-4">
            <Tabs defaultValue="basic">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="customer">Customer</TabsTrigger>
                <TabsTrigger value="device">Device</TabsTrigger>
              </TabsList>
              
              <TabsContent value="basic" className="space-y-4 mt-4">
                <div>
                  <Label htmlFor="title">Title *</Label>
                  <Input
                    id="title"
                    value={formData.title}
                    onChange={(e) => setFormData({...formData, title: e.target.value})}
                    placeholder="Brief description of the issue"
                    data-testid="input-title"
                  />
                </div>
                
                <div>
                  <Label htmlFor="description">Description</Label>
                  <Textarea
                    id="description"
                    value={formData.description}
                    onChange={(e) => setFormData({...formData, description: e.target.value})}
                    placeholder="Detailed description..."
                    rows={3}
                    data-testid="input-description"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="category">Category</Label>
                    <Select 
                      value={formData.category} 
                      onValueChange={(v) => setFormData({...formData, category: v})}
                    >
                      <SelectTrigger data-testid="select-category">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="repair">Repair</SelectItem>
                        <SelectItem value="maintenance">Maintenance</SelectItem>
                        <SelectItem value="installation">Installation</SelectItem>
                        <SelectItem value="inspection">Inspection</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  
                  <div>
                    <Label htmlFor="priority">Priority</Label>
                    <Select 
                      value={formData.priority} 
                      onValueChange={(v) => setFormData({...formData, priority: v})}
                    >
                      <SelectTrigger data-testid="select-priority">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="low">Low</SelectItem>
                        <SelectItem value="medium">Medium</SelectItem>
                        <SelectItem value="high">High</SelectItem>
                        <SelectItem value="urgent">Urgent</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="customer" className="space-y-4 mt-4">
                <div>
                  <Label htmlFor="customer_name">Customer Name</Label>
                  <Input
                    id="customer_name"
                    value={formData.customer_name}
                    onChange={(e) => setFormData({...formData, customer_name: e.target.value})}
                    placeholder="John Doe"
                    data-testid="input-customer-name"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="customer_email">Email</Label>
                    <Input
                      id="customer_email"
                      type="email"
                      value={formData.customer_email}
                      onChange={(e) => setFormData({...formData, customer_email: e.target.value})}
                      placeholder="john@example.com"
                    />
                  </div>
                  <div>
                    <Label htmlFor="customer_mobile">Mobile</Label>
                    <Input
                      id="customer_mobile"
                      value={formData.customer_mobile}
                      onChange={(e) => setFormData({...formData, customer_mobile: e.target.value})}
                      placeholder="9876543210"
                    />
                  </div>
                </div>
                
                <div>
                  <Label htmlFor="customer_company">Company Name</Label>
                  <Input
                    id="customer_company"
                    value={formData.customer_company_name}
                    onChange={(e) => setFormData({...formData, customer_company_name: e.target.value})}
                    placeholder="Acme Corp"
                  />
                </div>
                
                <div>
                  <Label htmlFor="location_address">Service Location</Label>
                  <Input
                    id="location_address"
                    value={formData.location_address}
                    onChange={(e) => setFormData({...formData, location_address: e.target.value})}
                    placeholder="123 Main Street"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="location_city">City</Label>
                    <Input
                      id="location_city"
                      value={formData.location_city}
                      onChange={(e) => setFormData({...formData, location_city: e.target.value})}
                      placeholder="Mumbai"
                    />
                  </div>
                  <div>
                    <Label htmlFor="location_pincode">Pincode</Label>
                    <Input
                      id="location_pincode"
                      value={formData.location_pincode}
                      onChange={(e) => setFormData({...formData, location_pincode: e.target.value})}
                      placeholder="400001"
                    />
                  </div>
                </div>
              </TabsContent>
              
              <TabsContent value="device" className="space-y-4 mt-4">
                <div>
                  <Label htmlFor="device_name">Device/Asset Name</Label>
                  <Input
                    id="device_name"
                    value={formData.device_name}
                    onChange={(e) => setFormData({...formData, device_name: e.target.value})}
                    placeholder="HP LaserJet Pro"
                  />
                </div>
                
                <div>
                  <Label htmlFor="device_serial">Serial Number</Label>
                  <Input
                    id="device_serial"
                    value={formData.device_serial}
                    onChange={(e) => setFormData({...formData, device_serial: e.target.value})}
                    placeholder="ABC123XYZ"
                  />
                </div>
              </TabsContent>
            </Tabs>
            
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setShowCreateModal(false)}>
                Cancel
              </Button>
              <Button type="submit" data-testid="submit-create-btn">
                Create Request
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {selectedRequest && (
            <>
              <DialogHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <DialogTitle className="flex items-center gap-2">
                      <Hash className="h-5 w-5" />
                      {selectedRequest.ticket_number}
                    </DialogTitle>
                    <DialogDescription>{selectedRequest.title}</DialogDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge className={PRIORITY_COLORS[selectedRequest.priority] || 'bg-slate-100'}>
                      {selectedRequest.priority}
                    </Badge>
                    <Badge className={`${STATE_COLORS[selectedRequest.state] || 'bg-slate-100'} border text-sm px-3 py-1`}>
                      {selectedRequest.state_metadata?.label || selectedRequest.state}
                    </Badge>
                  </div>
                </div>
              </DialogHeader>
              
              <Tabs defaultValue="details">
                <TabsList>
                  <TabsTrigger value="details">Details</TabsTrigger>
                  <TabsTrigger value="history">History ({selectedRequest.state_history?.length || 0})</TabsTrigger>
                  <TabsTrigger value="actions">Actions</TabsTrigger>
                </TabsList>
                
                <TabsContent value="details" className="space-y-4 mt-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-3">
                      <div>
                        <Label className="text-xs text-slate-500">Category</Label>
                        <p className="font-medium capitalize">{selectedRequest.category || '-'}</p>
                      </div>
                      <div>
                        <Label className="text-xs text-slate-500">Description</Label>
                        <p className="text-sm">{selectedRequest.description || 'No description'}</p>
                      </div>
                      <div>
                        <Label className="text-xs text-slate-500">Created</Label>
                        <p>{formatDate(selectedRequest.created_at)}</p>
                      </div>
                    </div>
                    
                    <div className="space-y-3">
                      {selectedRequest.customer_snapshot && (
                        <div className="p-3 bg-slate-50 rounded-lg">
                          <Label className="text-xs text-slate-500 mb-2 block">Customer</Label>
                          <div className="space-y-1">
                            <p className="font-medium flex items-center gap-2">
                              <User className="h-4 w-4" />
                              {selectedRequest.customer_snapshot.name}
                            </p>
                            {selectedRequest.customer_snapshot.email && (
                              <p className="text-sm flex items-center gap-2 text-slate-600">
                                <Mail className="h-3 w-3" />
                                {selectedRequest.customer_snapshot.email}
                              </p>
                            )}
                            {selectedRequest.customer_snapshot.mobile && (
                              <p className="text-sm flex items-center gap-2 text-slate-600">
                                <Phone className="h-3 w-3" />
                                {selectedRequest.customer_snapshot.mobile}
                              </p>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {selectedRequest.assigned_staff_name && (
                        <div>
                          <Label className="text-xs text-slate-500">Assigned To</Label>
                          <p className="font-medium">{selectedRequest.assigned_staff_name}</p>
                        </div>
                      )}
                      
                      {selectedRequest.device_name && (
                        <div>
                          <Label className="text-xs text-slate-500">Device</Label>
                          <p>{selectedRequest.device_name}</p>
                          {selectedRequest.device_serial && (
                            <p className="text-sm text-slate-500">S/N: {selectedRequest.device_serial}</p>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  {selectedRequest.resolution_notes && (
                    <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                      <Label className="text-xs text-green-700 mb-1 block">Resolution Notes</Label>
                      <p className="text-green-900">{selectedRequest.resolution_notes}</p>
                    </div>
                  )}
                  
                  {selectedRequest.cancellation_reason && (
                    <div className="p-3 bg-red-50 rounded-lg border border-red-200">
                      <Label className="text-xs text-red-700 mb-1 block">Cancellation Reason</Label>
                      <p className="text-red-900">{selectedRequest.cancellation_reason}</p>
                    </div>
                  )}
                </TabsContent>
                
                <TabsContent value="history" className="mt-4">
                  <div className="space-y-3">
                    {(selectedRequest.state_history || []).slice().reverse().map((h, idx) => (
                      <div key={h.id || idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                        <div className="mt-1">
                          <ArrowRight className="h-4 w-4 text-slate-400" />
                        </div>
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            <Badge className={`${STATE_COLORS[h.to_state] || 'bg-slate-100'} border text-xs`}>
                              {h.to_state}
                            </Badge>
                            {h.from_state && (
                              <>
                                <span className="text-xs text-slate-400">from</span>
                                <Badge variant="outline" className="text-xs">{h.from_state}</Badge>
                              </>
                            )}
                          </div>
                          <p className="text-sm text-slate-600 mt-1">
                            {h.actor_name} ({h.actor_role})
                          </p>
                          {h.reason && (
                            <p className="text-sm text-slate-500 mt-1 italic">{h.reason}</p>
                          )}
                          <p className="text-xs text-slate-400 mt-1">
                            {formatDate(h.timestamp)}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </TabsContent>
                
                <TabsContent value="actions" className="mt-4">
                  {selectedRequest.available_transitions?.length > 0 ? (
                    <div className="space-y-3">
                      <p className="text-sm text-slate-600 mb-3">
                        Available transitions from <strong>{selectedRequest.state}</strong>:
                      </p>
                      <div className="grid grid-cols-2 gap-3">
                        {selectedRequest.available_transitions.map((t) => (
                          <Button
                            key={t.state}
                            variant="outline"
                            className="justify-start"
                            onClick={() => openTransitionModal(t)}
                            data-testid={`transition-${t.state}`}
                          >
                            <ArrowRight className="h-4 w-4 mr-2" />
                            {t.label}
                          </Button>
                        ))}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center text-slate-500 py-8">
                      <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                      <p>This request is in a terminal state.</p>
                      <p className="text-sm">No further transitions available.</p>
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Transition Modal */}
      <Dialog open={showTransitionModal} onOpenChange={setShowTransitionModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Transition to {transitionTarget?.label}</DialogTitle>
            <DialogDescription>{transitionTarget?.description}</DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div>
              <Label htmlFor="reason">Reason / Notes</Label>
              <Textarea
                id="reason"
                value={transitionData.reason}
                onChange={(e) => setTransitionData({...transitionData, reason: e.target.value})}
                placeholder="Optional reason for this transition..."
                rows={2}
              />
            </div>
            
            {/* State-specific fields */}
            {transitionTarget?.state === 'ASSIGNED' && (
              <div>
                <Label htmlFor="staff_id">Staff ID</Label>
                <Input
                  id="staff_id"
                  value={transitionData.staff_id}
                  onChange={(e) => setTransitionData({...transitionData, staff_id: e.target.value})}
                  placeholder="Enter technician/staff ID"
                />
              </div>
            )}
            
            {transitionTarget?.state === 'DECLINED' && (
              <div>
                <Label htmlFor="decline_reason">Decline Reason *</Label>
                <Textarea
                  id="decline_reason"
                  value={transitionData.decline_reason}
                  onChange={(e) => setTransitionData({...transitionData, decline_reason: e.target.value})}
                  placeholder="Why is this being declined?"
                  rows={2}
                />
              </div>
            )}
            
            {transitionTarget?.state === 'VISIT_COMPLETED' && (
              <div>
                <Label htmlFor="diagnostics">Diagnostics *</Label>
                <Textarea
                  id="diagnostics"
                  value={transitionData.diagnostics}
                  onChange={(e) => setTransitionData({...transitionData, diagnostics: e.target.value})}
                  placeholder="What was found during the visit?"
                  rows={3}
                />
              </div>
            )}
            
            {transitionTarget?.state === 'RESOLVED' && (
              <div>
                <Label htmlFor="resolution_notes">Resolution Notes *</Label>
                <Textarea
                  id="resolution_notes"
                  value={transitionData.resolution_notes}
                  onChange={(e) => setTransitionData({...transitionData, resolution_notes: e.target.value})}
                  placeholder="How was the issue resolved?"
                  rows={3}
                />
              </div>
            )}
            
            {transitionTarget?.state === 'CANCELLED' && (
              <div>
                <Label htmlFor="cancellation_reason">Cancellation Reason *</Label>
                <Textarea
                  id="cancellation_reason"
                  value={transitionData.cancellation_reason}
                  onChange={(e) => setTransitionData({...transitionData, cancellation_reason: e.target.value})}
                  placeholder="Why is this being cancelled?"
                  rows={2}
                />
              </div>
            )}
            
            {transitionTarget?.state === 'PENDING_APPROVAL' && (
              <div>
                <Label htmlFor="approval_amount">Approval Amount *</Label>
                <Input
                  id="approval_amount"
                  type="number"
                  value={transitionData.approval_amount}
                  onChange={(e) => setTransitionData({...transitionData, approval_amount: e.target.value})}
                  placeholder="0.00"
                />
              </div>
            )}
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTransitionModal(false)}>
              Cancel
            </Button>
            <Button onClick={handleTransition} data-testid="confirm-transition-btn">
              Confirm Transition
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
