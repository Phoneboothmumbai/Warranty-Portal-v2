import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { Label } from '../../components/ui/label';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { 
  ArrowLeft, Clock, User, Building2, Laptop, Calendar, 
  CheckCircle2, XCircle, Play, Pause, UserPlus, Package,
  FileText, MessageSquare, History, Timer, Plus, RefreshCw,
  Phone, Mail, MapPin, AlertCircle, Send, Wrench
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status configuration
const STATUS_CONFIG = {
  new: { label: 'New', color: 'bg-slate-100 text-slate-800 border-slate-300', icon: FileText },
  pending_acceptance: { label: 'Pending Acceptance', color: 'bg-purple-100 text-purple-800 border-purple-300', icon: Clock },
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

const PriorityBadge = ({ priority }) => {
  const config = PRIORITY_CONFIG[priority] || PRIORITY_CONFIG.medium;
  return (
    <Badge variant="outline" className={config.color}>
      {config.label}
    </Badge>
  );
};

export default function ServiceTicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };
  
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [staff, setStaff] = useState([]);
  const [items, setItems] = useState([]);
  const [locations, setLocations] = useState([]);
  
  // Modal states
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showVisitModal, setShowVisitModal] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [showPartsRequestModal, setShowPartsRequestModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Form data
  const [selectedTechnician, setSelectedTechnician] = useState('');
  const [assignNotes, setAssignNotes] = useState('');
  const [commentText, setCommentText] = useState('');
  const [isInternalComment, setIsInternalComment] = useState(true);
  const [resolutionData, setResolutionData] = useState({
    resolution_summary: '',
    resolution_type: 'fixed'
  });
  const [visitData, setVisitData] = useState({
    technician_id: '',
    scheduled_date: '',
    scheduled_time_from: '',
    scheduled_time_to: '',
    purpose: ''
  });
  const [partsRequestData, setPartsRequestData] = useState({
    item_id: '',
    quantity_requested: 1,
    urgency: 'normal',
    request_notes: ''
  });

  // Fetch ticket details
  const fetchTicket = useCallback(async () => {
    try {
      const res = await axios.get(`${API_URL}/api/admin/service-tickets/${ticketId}`, { headers });
      setTicket(res.data);
    } catch (error) {
      toast.error('Failed to load ticket');
      navigate('/admin/service-requests');
    } finally {
      setLoading(false);
    }
  }, [ticketId, navigate]);

  // Fetch supporting data
  const fetchSupportingData = useCallback(async () => {
    const authHeaders = { Authorization: `Bearer ${localStorage.getItem('admin_token')}` };
    try {
      // Fetch staff users
      const staffRes = await axios.get(`${API_URL}/api/admin/staff/users?limit=100`, { headers: authHeaders });
      console.log('Staff API response:', staffRes.data);
      
      // Also try engineers endpoint
      let engineers = [];
      try {
        const engRes = await axios.get(`${API_URL}/api/admin/engineers`, { headers: authHeaders });
        engineers = Array.isArray(engRes.data) ? engRes.data : [];
        console.log('Engineers API response:', engineers);
      } catch (e) {
        console.log('Engineers fetch failed (optional):', e.message);
      }
      
      // Get staff users from response - API returns { users: [...] }
      const staffUsers = staffRes.data?.users || [];
      console.log('Staff users parsed:', staffUsers.length, staffUsers);
      
      // Get ALL active staff users (they appear in Staff Management, so they can be technicians)
      const allTechnicians = staffUsers.filter(s => s.state === 'active');
      console.log('Active staff users:', allTechnicians.length);
      
      // Add engineers that aren't already in staff users
      const existingEmails = new Set(allTechnicians.map(t => t.email?.toLowerCase()));
      engineers.forEach(eng => {
        if (eng.is_active && !existingEmails.has(eng.email?.toLowerCase())) {
          allTechnicians.push({ ...eng, state: 'active' });
        }
      });
      
      console.log('Final technicians list:', allTechnicians.length, allTechnicians.map(t => ({ name: t.name, state: t.state })));
      setStaff(allTechnicians);
      
      // Fetch other supporting data
      try {
        const [itemsRes, locationsRes] = await Promise.all([
          axios.get(`${API_URL}/api/admin/items?limit=500`, { headers: authHeaders }),
          axios.get(`${API_URL}/api/admin/inventory/locations`, { headers: authHeaders })
        ]);
        setItems(Array.isArray(itemsRes.data) ? itemsRes.data : (itemsRes.data?.items || []));
        setLocations(Array.isArray(locationsRes.data) ? locationsRes.data : (locationsRes.data?.locations || []));
      } catch (e) {
        console.log('Items/Locations fetch failed (optional):', e.message);
      }
    } catch (error) {
      console.error('Failed to fetch staff users:', error);
    }
  }, []);

  useEffect(() => {
    fetchTicket();
    fetchSupportingData();
  }, [fetchTicket, fetchSupportingData]);

  // Status actions
  const handleAssign = async () => {
    if (!selectedTechnician) {
      toast.error('Please select a technician');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/assign`, 
        { technician_id: selectedTechnician, notes: assignNotes }, 
        { headers }
      );
      toast.success('Ticket assigned successfully');
      setShowAssignModal(false);
      setSelectedTechnician('');
      setAssignNotes('');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to assign ticket');
    } finally {
      setActionLoading(false);
    }
  };

  const handleStartWork = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/start`, {}, { headers });
      toast.success('Work started');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to start work');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePendingParts = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/pending-parts`, {}, { headers });
      toast.success('Marked as pending parts');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update status');
    } finally {
      setActionLoading(false);
    }
  };

  const handleComplete = async () => {
    if (!resolutionData.resolution_summary) {
      toast.error('Please provide a resolution summary');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/complete`, resolutionData, { headers });
      toast.success('Ticket completed');
      setShowCompleteModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete ticket');
    } finally {
      setActionLoading(false);
    }
  };

  const handleClose = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/close`, {}, { headers });
      toast.success('Ticket closed');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to close ticket');
    } finally {
      setActionLoading(false);
    }
  };

  const handleCancel = async () => {
    if (!window.confirm('Are you sure you want to cancel this ticket?')) return;
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/cancel`, 
        { cancellation_reason: 'Cancelled by admin' }, 
        { headers }
      );
      toast.success('Ticket cancelled');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to cancel ticket');
    } finally {
      setActionLoading(false);
    }
  };

  // Add comment
  const handleAddComment = async () => {
    if (!commentText.trim()) {
      toast.error('Please enter a comment');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/comments`, 
        { text: commentText, is_internal: isInternalComment }, 
        { headers }
      );
      toast.success('Comment added');
      setShowCommentModal(false);
      setCommentText('');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to add comment');
    } finally {
      setActionLoading(false);
    }
  };

  // Create visit
  const handleCreateVisit = async () => {
    if (!visitData.technician_id) {
      toast.error('Please select a technician');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/visits`, 
        { ...visitData, ticket_id: ticketId }, 
        { headers }
      );
      toast.success('Visit scheduled');
      setShowVisitModal(false);
      setVisitData({ technician_id: '', scheduled_date: '', scheduled_time_from: '', scheduled_time_to: '', purpose: '' });
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create visit');
    } finally {
      setActionLoading(false);
    }
  };

  // Request parts
  const handleRequestParts = async () => {
    if (!partsRequestData.item_id) {
      toast.error('Please select an item');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/ticket-parts/requests`, 
        { ...partsRequestData, ticket_id: ticketId }, 
        { headers }
      );
      toast.success('Parts requested');
      setShowPartsRequestModal(false);
      setPartsRequestData({ item_id: '', quantity_requested: 1, urgency: 'normal', request_notes: '' });
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to request parts');
    } finally {
      setActionLoading(false);
    }
  };

  // Format date
  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!ticket) return null;

  const canAssign = ['new', 'assigned'].includes(ticket.status);
  const canStart = ticket.status === 'assigned' || ticket.status === 'pending_parts';
  const canComplete = ['in_progress', 'pending_parts'].includes(ticket.status);
  const canClose = ticket.status === 'completed';
  const canCancel = !['closed', 'cancelled'].includes(ticket.status);

  return (
    <div data-testid="ticket-detail-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/service-requests')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 font-mono">#{ticket.ticket_number}</h1>
              <StatusBadge status={ticket.status} />
              <PriorityBadge priority={ticket.priority} />
              {ticket.is_urgent && <Badge variant="destructive">URGENT</Badge>}
            </div>
            <p className="text-slate-500 text-sm mt-1">{ticket.title}</p>
          </div>
        </div>
        <Button variant="outline" onClick={fetchTicket} data-testid="refresh-btn">
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Action Buttons */}
      <Card className="bg-white">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-2">
            {canAssign && (
              <Button onClick={() => setShowAssignModal(true)} data-testid="assign-btn">
                <UserPlus className="h-4 w-4 mr-2" />
                {ticket.assigned_to_id ? 'Reassign' : 'Assign'}
              </Button>
            )}
            {canStart && (
              <Button onClick={handleStartWork} disabled={actionLoading} variant="outline">
                <Play className="h-4 w-4 mr-2" />
                Start Work
              </Button>
            )}
            {ticket.status === 'in_progress' && (
              <Button onClick={handlePendingParts} disabled={actionLoading} variant="outline">
                <Package className="h-4 w-4 mr-2" />
                Pending Parts
              </Button>
            )}
            {canComplete && (
              <Button onClick={() => setShowCompleteModal(true)} className="bg-green-600 hover:bg-green-700">
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Complete
              </Button>
            )}
            {canClose && (
              <Button onClick={handleClose} disabled={actionLoading} className="bg-emerald-600 hover:bg-emerald-700">
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Close Ticket
              </Button>
            )}
            <Button onClick={() => setShowVisitModal(true)} variant="outline" data-testid="schedule-visit-btn">
              <Calendar className="h-4 w-4 mr-2" />
              Schedule Visit
            </Button>
            <Button onClick={() => setShowPartsRequestModal(true)} variant="outline">
              <Package className="h-4 w-4 mr-2" />
              Request Parts
            </Button>
            <Button onClick={() => setShowCommentModal(true)} variant="outline">
              <MessageSquare className="h-4 w-4 mr-2" />
              Add Comment
            </Button>
            {canCancel && (
              <Button onClick={handleCancel} variant="outline" className="text-red-600 hover:bg-red-50">
                <XCircle className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Main Content - Tabs */}
      <Tabs defaultValue="details" className="space-y-4">
        <TabsList>
          <TabsTrigger value="details">Details</TabsTrigger>
          <TabsTrigger value="visits">Visits ({ticket.visits?.length || 0})</TabsTrigger>
          <TabsTrigger value="parts">Parts ({(ticket.part_requests?.length || 0) + (ticket.parts_issued?.length || 0)})</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Ticket Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <FileText className="h-4 w-4" />
                  Ticket Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-slate-500">Title</Label>
                  <p className="font-medium">{ticket.title}</p>
                </div>
                {ticket.description && (
                  <div>
                    <Label className="text-slate-500">Description</Label>
                    <p className="text-slate-700">{ticket.description}</p>
                  </div>
                )}
                {ticket.problem_name && (
                  <div>
                    <Label className="text-slate-500">Problem Type</Label>
                    <p>{ticket.problem_name}</p>
                  </div>
                )}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-500">Created</Label>
                    <p className="text-sm">{formatDate(ticket.created_at)}</p>
                  </div>
                  <div>
                    <Label className="text-slate-500">Source</Label>
                    <p className="capitalize">{ticket.source}</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-500">Total Time</Label>
                    <p className="flex items-center gap-1">
                      <Timer className="h-4 w-4" />
                      {ticket.total_time_minutes || 0} minutes
                    </p>
                  </div>
                  <div>
                    <Label className="text-slate-500">Total Cost</Label>
                    <p className="font-mono">₹{ticket.total_cost?.toLocaleString() || 0}</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Customer Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  Customer Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <Label className="text-slate-500">Company</Label>
                  <p className="font-medium">{ticket.company_name}</p>
                </div>
                {ticket.contact && (
                  <>
                    <div>
                      <Label className="text-slate-500">Contact Person</Label>
                      <p className="flex items-center gap-2">
                        <User className="h-4 w-4 text-slate-400" />
                        {ticket.contact.name}
                      </p>
                    </div>
                    {ticket.contact.phone && (
                      <div>
                        <Label className="text-slate-500">Phone</Label>
                        <p className="flex items-center gap-2">
                          <Phone className="h-4 w-4 text-slate-400" />
                          <a href={`tel:${ticket.contact.phone}`} className="text-blue-600">{ticket.contact.phone}</a>
                        </p>
                      </div>
                    )}
                    {ticket.contact.email && (
                      <div>
                        <Label className="text-slate-500">Email</Label>
                        <p className="flex items-center gap-2">
                          <Mail className="h-4 w-4 text-slate-400" />
                          <a href={`mailto:${ticket.contact.email}`} className="text-blue-600">{ticket.contact.email}</a>
                        </p>
                      </div>
                    )}
                  </>
                )}
                {ticket.location && (
                  <div>
                    <Label className="text-slate-500">Location</Label>
                    <p className="flex items-start gap-2">
                      <MapPin className="h-4 w-4 text-slate-400 mt-0.5" />
                      <span>
                        {ticket.location.site_name && <span className="font-medium">{ticket.location.site_name}<br/></span>}
                        {ticket.location.address}
                        {ticket.location.city && `, ${ticket.location.city}`}
                      </span>
                    </p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Device Info */}
            {ticket.device_id && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <Laptop className="h-4 w-4" />
                    Device Information
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Device</span>
                    <span className="font-medium">{ticket.device_name || '-'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Serial Number</span>
                    <span className="font-mono text-sm">{ticket.device_serial || '-'}</span>
                  </div>
                  {ticket.asset_tag && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Asset Tag</span>
                      <span className="font-mono text-sm">{ticket.asset_tag}</span>
                    </div>
                  )}
                  {ticket.device_type && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Type</span>
                      <span>{ticket.device_type}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Assignment Info */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Assignment
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-500">Assigned To</span>
                  <span className="font-medium">{ticket.assigned_to_name || 'Unassigned'}</span>
                </div>
                {ticket.assigned_at && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Assigned At</span>
                    <span className="text-sm">{formatDate(ticket.assigned_at)}</span>
                  </div>
                )}
                {ticket.assigned_by_name && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Assigned By</span>
                    <span>{ticket.assigned_by_name}</span>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Resolution Info */}
            {ticket.resolution_summary && (
              <Card>
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Resolution
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div>
                    <Label className="text-slate-500">Summary</Label>
                    <p>{ticket.resolution_summary}</p>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Type</span>
                    <span className="capitalize">{ticket.resolution_type}</span>
                  </div>
                  {ticket.resolved_at && (
                    <div className="flex justify-between">
                      <span className="text-slate-500">Resolved At</span>
                      <span className="text-sm">{formatDate(ticket.resolved_at)}</span>
                    </div>
                  )}
                </CardContent>
              </Card>
            )}

            {/* Comments */}
            {ticket.comments?.length > 0 && (
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="text-base flex items-center gap-2">
                    <MessageSquare className="h-4 w-4" />
                    Comments ({ticket.comments.length})
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {ticket.comments.map((comment) => (
                      <div key={comment.id} className="p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-sm">{comment.author_name}</span>
                          <span className="text-xs text-slate-500">{formatDate(comment.created_at)}</span>
                        </div>
                        <p className="text-sm text-slate-700">{comment.text}</p>
                        {comment.is_internal && (
                          <Badge variant="outline" className="mt-2 text-xs">Internal</Badge>
                        )}
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        </TabsContent>

        {/* Visits Tab */}
        <TabsContent value="visits">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Service Visits</CardTitle>
              <Button size="sm" onClick={() => setShowVisitModal(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Schedule Visit
              </Button>
            </CardHeader>
            <CardContent>
              {ticket.visits?.length > 0 ? (
                <div className="space-y-3">
                  {ticket.visits.map((visit) => (
                    <div key={visit.id} className="p-4 border rounded-lg hover:bg-slate-50">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className="font-medium">Visit #{visit.visit_number}</span>
                          <Badge variant="outline" className={
                            visit.status === 'completed' ? 'bg-green-100 text-green-700' :
                            visit.status === 'in_progress' ? 'bg-amber-100 text-amber-700' :
                            'bg-slate-100 text-slate-700'
                          }>
                            {visit.status}
                          </Badge>
                        </div>
                        <span className="text-sm text-slate-500">
                          {visit.duration_minutes > 0 && `${visit.duration_minutes} min`}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-sm">
                        <div className="flex items-center gap-2 text-slate-600">
                          <User className="h-3.5 w-3.5" />
                          {visit.technician_name}
                        </div>
                        {visit.scheduled_date && (
                          <div className="flex items-center gap-2 text-slate-600">
                            <Calendar className="h-3.5 w-3.5" />
                            {visit.scheduled_date}
                            {visit.scheduled_time_from && ` ${visit.scheduled_time_from}`}
                          </div>
                        )}
                      </div>
                      {visit.purpose && (
                        <p className="text-sm text-slate-500 mt-2">{visit.purpose}</p>
                      )}
                      {visit.work_summary && (
                        <div className="mt-2 p-2 bg-slate-100 rounded text-sm">
                          <span className="font-medium">Summary: </span>{visit.work_summary}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Calendar className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No visits scheduled yet</p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Parts Tab */}
        <TabsContent value="parts" className="space-y-4">
          {/* Parts Requests */}
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">Parts Requests</CardTitle>
              <Button size="sm" onClick={() => setShowPartsRequestModal(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Request Parts
              </Button>
            </CardHeader>
            <CardContent>
              {ticket.part_requests?.length > 0 ? (
                <div className="space-y-3">
                  {ticket.part_requests.map((req) => (
                    <div key={req.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{req.item_name}</span>
                        <Badge variant="outline" className={
                          req.status === 'approved' ? 'bg-green-100 text-green-700' :
                          req.status === 'rejected' ? 'bg-red-100 text-red-700' :
                          req.status === 'issued' ? 'bg-blue-100 text-blue-700' :
                          'bg-amber-100 text-amber-700'
                        }>
                          {req.status}
                        </Badge>
                      </div>
                      <div className="flex gap-4 text-sm text-slate-600">
                        <span>Qty: {req.quantity_requested}</span>
                        {req.quantity_approved && <span>Approved: {req.quantity_approved}</span>}
                        <span className="capitalize">Urgency: {req.urgency}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-4 text-slate-500">No parts requested</p>
              )}
            </CardContent>
          </Card>

          {/* Parts Issued */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Parts Issued</CardTitle>
            </CardHeader>
            <CardContent>
              {ticket.parts_issued?.length > 0 ? (
                <div className="space-y-3">
                  {ticket.parts_issued.map((issue) => (
                    <div key={issue.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between mb-2">
                        <span className="font-medium">{issue.item_name}</span>
                        <span className="font-mono text-sm">₹{issue.total_price?.toLocaleString()}</span>
                      </div>
                      <div className="flex gap-4 text-sm text-slate-600">
                        <span>Qty: {issue.quantity_issued}</span>
                        {issue.quantity_returned > 0 && <span>Returned: {issue.quantity_returned}</span>}
                        <span>From: {issue.issued_from_location_name}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center py-4 text-slate-500">No parts issued</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <History className="h-4 w-4" />
                Status History
              </CardTitle>
            </CardHeader>
            <CardContent>
              {ticket.status_history?.length > 0 ? (
                <div className="relative">
                  <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200" />
                  <div className="space-y-4">
                    {ticket.status_history.map((h, idx) => (
                      <div key={idx} className="relative flex gap-4 pl-10">
                        <div className="absolute left-2.5 w-3 h-3 rounded-full bg-blue-500 border-2 border-white" />
                        <div className="flex-1 pb-4">
                          <div className="flex items-center gap-2">
                            {h.from_status && (
                              <>
                                <Badge variant="outline" className="text-xs">{h.from_status}</Badge>
                                <span className="text-slate-400">→</span>
                              </>
                            )}
                            <Badge variant="outline" className="text-xs bg-blue-50">{h.to_status}</Badge>
                          </div>
                          <p className="text-sm text-slate-600 mt-1">
                            by {h.changed_by_name} • {formatDate(h.changed_at)}
                          </p>
                          {h.notes && <p className="text-sm text-slate-500 mt-1">{h.notes}</p>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ) : (
                <p className="text-center py-4 text-slate-500">No history available</p>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Assign Modal */}
      <Dialog open={showAssignModal} onOpenChange={setShowAssignModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Assign Technician</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Select Technician</Label>
              <Select value={selectedTechnician} onValueChange={setSelectedTechnician}>
                <SelectTrigger data-testid="technician-select">
                  <SelectValue placeholder="Select technician" />
                </SelectTrigger>
                <SelectContent>
                  {staff.filter(s => s.state === 'active').map((tech) => (
                    <SelectItem key={tech.id} value={tech.id}>{tech.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Notes (optional)</Label>
              <Textarea
                value={assignNotes}
                onChange={(e) => setAssignNotes(e.target.value)}
                placeholder="Assignment notes..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAssignModal(false)}>Cancel</Button>
            <Button onClick={handleAssign} disabled={actionLoading}>
              {actionLoading ? 'Assigning...' : 'Assign'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Complete Modal */}
      <Dialog open={showCompleteModal} onOpenChange={setShowCompleteModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Complete Ticket</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Resolution Summary *</Label>
              <Textarea
                value={resolutionData.resolution_summary}
                onChange={(e) => setResolutionData({...resolutionData, resolution_summary: e.target.value})}
                placeholder="Describe how the issue was resolved..."
                rows={3}
              />
            </div>
            <div>
              <Label>Resolution Type</Label>
              <Select 
                value={resolutionData.resolution_type} 
                onValueChange={(v) => setResolutionData({...resolutionData, resolution_type: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="fixed">Fixed</SelectItem>
                  <SelectItem value="replaced">Replaced</SelectItem>
                  <SelectItem value="workaround">Workaround</SelectItem>
                  <SelectItem value="not_reproducible">Not Reproducible</SelectItem>
                  <SelectItem value="duplicate">Duplicate</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCompleteModal(false)}>Cancel</Button>
            <Button onClick={handleComplete} disabled={actionLoading} className="bg-green-600 hover:bg-green-700">
              {actionLoading ? 'Completing...' : 'Complete Ticket'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Comment Modal */}
      <Dialog open={showCommentModal} onOpenChange={setShowCommentModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Comment</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Comment</Label>
              <Textarea
                value={commentText}
                onChange={(e) => setCommentText(e.target.value)}
                placeholder="Enter your comment..."
                rows={3}
              />
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="internal"
                checked={isInternalComment}
                onChange={(e) => setIsInternalComment(e.target.checked)}
              />
              <Label htmlFor="internal" className="font-normal">Internal note (not visible to customer)</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCommentModal(false)}>Cancel</Button>
            <Button onClick={handleAddComment} disabled={actionLoading}>
              {actionLoading ? 'Adding...' : 'Add Comment'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Schedule Visit Modal */}
      <Dialog open={showVisitModal} onOpenChange={setShowVisitModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Schedule Visit</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Technician *</Label>
              <Select value={visitData.technician_id} onValueChange={(v) => setVisitData({...visitData, technician_id: v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select technician" />
                </SelectTrigger>
                <SelectContent>
                  {staff.filter(s => s.state === 'active').map((tech) => (
                    <SelectItem key={tech.id} value={tech.id}>{tech.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Date</Label>
              <Input
                type="date"
                value={visitData.scheduled_date}
                onChange={(e) => setVisitData({...visitData, scheduled_date: e.target.value})}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>From Time</Label>
                <Input
                  type="time"
                  value={visitData.scheduled_time_from}
                  onChange={(e) => setVisitData({...visitData, scheduled_time_from: e.target.value})}
                />
              </div>
              <div>
                <Label>To Time</Label>
                <Input
                  type="time"
                  value={visitData.scheduled_time_to}
                  onChange={(e) => setVisitData({...visitData, scheduled_time_to: e.target.value})}
                />
              </div>
            </div>
            <div>
              <Label>Purpose</Label>
              <Input
                value={visitData.purpose}
                onChange={(e) => setVisitData({...visitData, purpose: e.target.value})}
                placeholder="Purpose of the visit..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVisitModal(false)}>Cancel</Button>
            <Button onClick={handleCreateVisit} disabled={actionLoading}>
              {actionLoading ? 'Scheduling...' : 'Schedule Visit'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Parts Request Modal */}
      <Dialog open={showPartsRequestModal} onOpenChange={setShowPartsRequestModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request Parts</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Item *</Label>
              <Select value={partsRequestData.item_id} onValueChange={(v) => setPartsRequestData({...partsRequestData, item_id: v})}>
                <SelectTrigger>
                  <SelectValue placeholder="Select item" />
                </SelectTrigger>
                <SelectContent>
                  {items.map((item) => (
                    <SelectItem key={item.id} value={item.id}>
                      {item.name} {item.sku && `(${item.sku})`}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Quantity</Label>
                <Input
                  type="number"
                  min="1"
                  value={partsRequestData.quantity_requested}
                  onChange={(e) => setPartsRequestData({...partsRequestData, quantity_requested: parseInt(e.target.value) || 1})}
                />
              </div>
              <div>
                <Label>Urgency</Label>
                <Select value={partsRequestData.urgency} onValueChange={(v) => setPartsRequestData({...partsRequestData, urgency: v})}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="low">Low</SelectItem>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="high">High</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
            <div>
              <Label>Notes</Label>
              <Textarea
                value={partsRequestData.request_notes}
                onChange={(e) => setPartsRequestData({...partsRequestData, request_notes: e.target.value})}
                placeholder="Additional notes..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPartsRequestModal(false)}>Cancel</Button>
            <Button onClick={handleRequestParts} disabled={actionLoading}>
              {actionLoading ? 'Requesting...' : 'Request Parts'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
