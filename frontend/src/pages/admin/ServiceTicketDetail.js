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
  Phone, Mail, MapPin, AlertCircle, Send, Wrench, Zap,
  Truck, Shield, Factory, Home, Clipboard, GitBranch
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Status configuration - Extended for Job Lifecycle
const STATUS_CONFIG = {
  new: { label: 'New', color: 'bg-slate-100 text-slate-800 border-slate-300', icon: FileText },
  pending_acceptance: { label: 'Pending Acceptance', color: 'bg-purple-100 text-purple-800 border-purple-300', icon: Clock },
  assigned: { label: 'Assigned', color: 'bg-blue-100 text-blue-800 border-blue-300', icon: UserPlus },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-800 border-amber-300', icon: Play },
  pending_parts: { label: 'Pending Parts', color: 'bg-orange-100 text-orange-800 border-orange-300', icon: Package },
  device_pickup: { label: 'Device Pickup', color: 'bg-indigo-100 text-indigo-800 border-indigo-300', icon: Truck },
  device_under_repair: { label: 'Under Repair', color: 'bg-violet-100 text-violet-800 border-violet-300', icon: Wrench },
  ready_for_delivery: { label: 'Ready for Delivery', color: 'bg-cyan-100 text-cyan-800 border-cyan-300', icon: Package },
  out_for_delivery: { label: 'Out for Delivery', color: 'bg-teal-100 text-teal-800 border-teal-300', icon: Truck },
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
  
  // Ticketing config data
  const [helpTopics, setHelpTopics] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [slaPolicies, setSlaPolicies] = useState([]);
  const [cannedResponses, setCannedResponses] = useState([]);
  
  // Modal states
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [showVisitModal, setShowVisitModal] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [showCommentModal, setShowCommentModal] = useState(false);
  const [showPartsRequestModal, setShowPartsRequestModal] = useState(false);
  const [showCannedResponseModal, setShowCannedResponseModal] = useState(false);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Job Lifecycle Modals
  const [showDiagnosisModal, setShowDiagnosisModal] = useState(false);
  const [showPathSelectionModal, setShowPathSelectionModal] = useState(false);
  const [showPickupModal, setShowPickupModal] = useState(false);
  const [showWarrantyModal, setShowWarrantyModal] = useState(false);
  const [showAMCRepairModal, setShowAMCRepairModal] = useState(false);
  const [showOEMRepairModal, setShowOEMRepairModal] = useState(false);
  const [showDeliveryModal, setShowDeliveryModal] = useState(false);
  
  // Job Lifecycle Form Data
  const [diagnosisData, setDiagnosisData] = useState({
    problem_identified: '',
    root_cause: '',
    observations: '',
    time_spent_minutes: 0
  });
  const [pathSelectionData, setPathSelectionData] = useState({
    path: '',
    notes: '',
    resolution_summary: ''
  });
  const [pickupData, setPickupData] = useState({
    pickup_type: 'engineer',
    pickup_person_name: '',
    pickup_date: '',
    pickup_time: '',
    pickup_location: '',
    device_condition: '',
    accessories_taken: [],
    customer_acknowledgement: false,
    customer_name: ''
  });
  const [warrantyData, setWarrantyData] = useState({
    warranty_type: '',
    amc_contract_id: '',
    notes: ''
  });
  const [amcRepairData, setAmcRepairData] = useState({
    assigned_engineer_id: '',
    assigned_engineer_name: '',
    issue_identified: '',
    repair_actions: [],
    parts_replaced: [],
    internal_notes: ''
  });
  const [oemRepairData, setOemRepairData] = useState({
    oem_name: '',
    oem_service_center: '',
    oem_ticket_number: '',
    sent_to_oem_date: '',
    repair_performed: '',
    received_back_date: ''
  });
  const [deliveryData, setDeliveryData] = useState({
    delivery_type: 'engineer',
    delivery_person_name: '',
    delivery_date: '',
    delivery_time: '',
    delivery_location: '',
    delivered_to_name: '',
    customer_confirmation: false
  });
  
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
      
      // Fetch ticketing config data (Help Topics, Departments, SLA, Canned Responses)
      try {
        const [topicsRes, deptsRes, slaRes, cannedRes] = await Promise.all([
          axios.get(`${API_URL}/api/admin/ticketing-config/help-topics`, { headers: authHeaders }).catch(() => ({ data: { topics: [] } })),
          axios.get(`${API_URL}/api/admin/ticketing-config/departments`, { headers: authHeaders }).catch(() => ({ data: { departments: [] } })),
          axios.get(`${API_URL}/api/admin/ticketing-config/sla-policies`, { headers: authHeaders }).catch(() => ({ data: { policies: [] } })),
          axios.get(`${API_URL}/api/admin/ticketing-config/canned-responses`, { headers: authHeaders }).catch(() => ({ data: { responses: [] } }))
        ]);
        setHelpTopics(topicsRes.data?.topics || []);
        setDepartments(deptsRes.data?.departments || []);
        setSlaPolicies(slaRes.data?.policies || []);
        setCannedResponses(cannedRes.data?.responses || []);
      } catch (e) {
        console.log('Ticketing config fetch failed (optional):', e.message);
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

  // ==================== JOB LIFECYCLE HANDLERS ====================

  // Submit Diagnosis
  const handleSubmitDiagnosis = async () => {
    if (!diagnosisData.problem_identified) {
      toast.error('Please identify the problem');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/diagnosis`, diagnosisData, { headers });
      toast.success('Diagnosis submitted');
      setShowDiagnosisModal(false);
      setShowPathSelectionModal(true); // Immediately show path selection
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit diagnosis');
    } finally {
      setActionLoading(false);
    }
  };

  // Select Resolution Path
  const handleSelectPath = async () => {
    if (!pathSelectionData.path) {
      toast.error('Please select a resolution path');
      return;
    }
    if (pathSelectionData.path === 'resolved_on_visit' && !pathSelectionData.resolution_summary) {
      toast.error('Please provide resolution summary');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/select-path`, pathSelectionData, { headers });
      toast.success('Path selected');
      setShowPathSelectionModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to select path');
    } finally {
      setActionLoading(false);
    }
  };

  // Record Device Pickup
  const handleRecordPickup = async () => {
    if (!pickupData.pickup_person_name || !pickupData.pickup_date || !pickupData.device_condition) {
      toast.error('Please fill all required fields');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/device-pickup`, pickupData, { headers });
      toast.success('Device pickup recorded');
      setShowPickupModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record pickup');
    } finally {
      setActionLoading(false);
    }
  };

  // Record Warranty Decision
  const handleWarrantyDecision = async () => {
    if (!warrantyData.warranty_type) {
      toast.error('Please select warranty type');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/warranty-decision`, warrantyData, { headers });
      toast.success('Warranty decision recorded');
      setShowWarrantyModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record warranty decision');
    } finally {
      setActionLoading(false);
    }
  };

  // Record AMC Repair
  const handleAMCRepair = async () => {
    if (!amcRepairData.issue_identified) {
      toast.error('Please identify the issue');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/amc-repair`, amcRepairData, { headers });
      toast.success('AMC repair details saved');
      setShowAMCRepairModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record AMC repair');
    } finally {
      setActionLoading(false);
    }
  };

  // Complete AMC Repair
  const handleCompleteAMCRepair = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/amc-repair/complete`, {}, { headers });
      toast.success('AMC repair completed - Device ready for delivery');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete AMC repair');
    } finally {
      setActionLoading(false);
    }
  };

  // Record OEM Repair
  const handleOEMRepair = async () => {
    if (!oemRepairData.oem_name) {
      toast.error('Please provide OEM name');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/oem-repair`, oemRepairData, { headers });
      toast.success('OEM repair details saved');
      setShowOEMRepairModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record OEM repair');
    } finally {
      setActionLoading(false);
    }
  };

  // Complete OEM Repair
  const handleCompleteOEMRepair = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/oem-repair/complete`, {}, { headers });
      toast.success('OEM repair completed - Device ready for delivery');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to complete OEM repair');
    } finally {
      setActionLoading(false);
    }
  };

  // Record Device Delivery
  const handleRecordDelivery = async () => {
    if (!deliveryData.delivery_person_name || !deliveryData.delivery_date || !deliveryData.delivered_to_name) {
      toast.error('Please fill all required fields');
      return;
    }
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/device-delivery`, deliveryData, { headers });
      toast.success('Device delivered - Ticket completed');
      setShowDeliveryModal(false);
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to record delivery');
    } finally {
      setActionLoading(false);
    }
  };

  // Resume from Parts
  const handleResumeFromParts = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API_URL}/api/admin/job-lifecycle/${ticketId}/resume-from-parts`, { notes: 'Parts received' }, { headers });
      toast.success('Ticket resumed');
      fetchTicket();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to resume ticket');
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

  // STRICT WORKFLOW RULES - enforcing 1→2→3→4→5→6→7 flow
  // 1. NEW: Can assign
  // 2. PENDING_ACCEPTANCE: Can reassign (before engineer responds)  
  // 3. ASSIGNED: Engineer accepted, work should start - no reassign
  // 4. IN_PROGRESS: Work ongoing - no reassign
  // 5. PENDING_PARTS: Waiting for quotation - no reassign
  // 6. COMPLETED: Work done - can only close
  // 7. CLOSED/CANCELLED: Terminal states
  
  const canAssign = ['new', 'pending_acceptance'].includes(ticket.status);
  const canStart = ticket.status === 'assigned';  // Only assigned can start work
  const canComplete = ticket.status === 'in_progress' || (ticket.status === 'pending_parts' && ticket.quotation_status === 'approved');
  const canClose = ticket.status === 'completed';
  const canCancel = !['closed', 'cancelled', 'in_progress', 'pending_parts', 'completed'].includes(ticket.status);

  return (
    <div data-testid="ticket-detail-page" className="space-y-6">
      {/* Quotation Alert Banner - Show when pending parts */}
      {ticket.status === 'pending_parts' && (
        <div className={`p-4 rounded-lg border ${
          ticket.quotation_status === 'approved' 
            ? 'bg-emerald-50 border-emerald-200' 
            : ticket.quotation_status === 'rejected'
            ? 'bg-red-50 border-red-200'
            : ticket.quotation_status === 'sent'
            ? 'bg-blue-50 border-blue-200'
            : 'bg-orange-50 border-orange-200'
        }`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Package className={`h-5 w-5 ${
                ticket.quotation_status === 'approved' ? 'text-emerald-600' :
                ticket.quotation_status === 'rejected' ? 'text-red-600' :
                ticket.quotation_status === 'sent' ? 'text-blue-600' :
                'text-orange-600'
              }`} />
              <div>
                <p className="font-medium text-slate-900">
                  {ticket.quotation_status === 'approved' 
                    ? '✅ Quotation Approved - Ready to resume work'
                    : ticket.quotation_status === 'rejected'
                    ? '❌ Quotation Rejected - Needs revision'
                    : ticket.quotation_status === 'sent'
                    ? '📧 Quotation Sent - Awaiting customer response'
                    : '📝 Quotation Draft - Needs review and sending'}
                </p>
                <p className="text-sm text-slate-600">
                  Parts are required to complete this service ticket.
                </p>
              </div>
            </div>
            <Button 
              onClick={() => navigate('/admin/quotations')} 
              size="sm"
              className={
                ticket.quotation_status === 'approved' ? 'bg-emerald-600 hover:bg-emerald-700' :
                ticket.quotation_status === 'draft' ? 'bg-orange-600 hover:bg-orange-700' :
                ''
              }
            >
              <FileText className="h-4 w-4 mr-2" />
              {ticket.quotation_status === 'draft' ? 'Review & Send' : 'View Quotation'}
            </Button>
          </div>
        </div>
      )}

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
            {/* Show link to quotations when pending parts */}
            {ticket.status === 'pending_parts' && ticket.quotation_id && (
              <Button 
                onClick={() => navigate('/admin/quotations')} 
                variant="outline" 
                className="text-orange-600 border-orange-300 hover:bg-orange-50"
              >
                <FileText className="h-4 w-4 mr-2" />
                View Quotation
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
            {cannedResponses.length > 0 && (
              <Button onClick={() => setShowCannedResponseModal(true)} variant="outline" className="text-purple-600 border-purple-300 hover:bg-purple-50">
                <Zap className="h-4 w-4 mr-2" />
                Canned Response
              </Button>
            )}
            {canCancel && (
              <Button onClick={handleCancel} variant="outline" className="text-red-600 hover:bg-red-50">
                <XCircle className="h-4 w-4 mr-2" />
                Cancel
              </Button>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Workflow Progress Indicator */}
      <Card className="bg-white">
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-700">Ticket Workflow Progress</span>
            {ticket.status === 'pending_parts' && ticket.quotation_status && (
              <Badge variant="outline" className="bg-orange-50 text-orange-700 border-orange-200">
                Quotation: {ticket.quotation_status}
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-1">
            {[
              { key: 'new', label: '1. Created', color: 'slate' },
              { key: 'pending_acceptance', label: '2. Assigned', color: 'purple' },
              { key: 'assigned', label: '3. Accepted', color: 'blue' },
              { key: 'in_progress', label: '4. In Progress', color: 'amber' },
              { key: 'pending_parts', label: '5. Parts', color: 'orange', optional: true },
              { key: 'completed', label: '6. Completed', color: 'green' },
              { key: 'closed', label: '7. Closed', color: 'emerald' },
            ].map((step, idx, arr) => {
              const statusOrder = ['new', 'pending_acceptance', 'assigned', 'in_progress', 'pending_parts', 'completed', 'closed'];
              const currentIdx = statusOrder.indexOf(ticket.status);
              const stepIdx = statusOrder.indexOf(step.key);
              const isActive = step.key === ticket.status;
              const isPast = stepIdx < currentIdx || (ticket.status === 'in_progress' && step.key === 'pending_parts');
              const isCancelled = ticket.status === 'cancelled';
              
              return (
                <React.Fragment key={step.key}>
                  <div 
                    className={`flex-1 h-2 rounded-full transition-all ${
                      isCancelled ? 'bg-red-200' :
                      isActive ? `bg-${step.color}-500` :
                      isPast ? `bg-${step.color}-300` :
                      'bg-slate-200'
                    }`}
                    title={step.label}
                  />
                  {idx < arr.length - 1 && <div className="w-1" />}
                </React.Fragment>
              );
            })}
          </div>
          <div className="flex justify-between mt-1 text-xs text-slate-500">
            <span>Created</span>
            <span>Assigned</span>
            <span>Accepted</span>
            <span>Work</span>
            <span>Parts</span>
            <span>Done</span>
            <span>Closed</span>
          </div>
          {ticket.status === 'cancelled' && (
            <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
              This ticket was cancelled. Reason: {ticket.cancellation_reason || 'Not specified'}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Job Lifecycle Actions */}
      {ticket.status !== 'closed' && ticket.status !== 'cancelled' && (
        <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
          <CardHeader className="pb-2">
            <CardTitle className="text-base flex items-center gap-2">
              <GitBranch className="h-5 w-5 text-indigo-600" />
              Job Lifecycle Actions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Status: In Progress - Need Diagnosis & Path Selection */}
              {ticket.status === 'in_progress' && !ticket.diagnosis && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-amber-200">
                  <div>
                    <p className="font-medium text-amber-800">Step 1: Submit Diagnosis</p>
                    <p className="text-sm text-amber-600">Document the problem identified during visit</p>
                  </div>
                  <Button onClick={() => setShowDiagnosisModal(true)} className="bg-amber-600 hover:bg-amber-700">
                    <Clipboard className="h-4 w-4 mr-2" />
                    Submit Diagnosis
                  </Button>
                </div>
              )}

              {ticket.status === 'in_progress' && ticket.diagnosis && !ticket.resolution_path && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-purple-200">
                  <div>
                    <p className="font-medium text-purple-800">Step 2: Select Resolution Path (REQUIRED)</p>
                    <p className="text-sm text-purple-600">Choose how this ticket will be resolved</p>
                  </div>
                  <Button onClick={() => setShowPathSelectionModal(true)} className="bg-purple-600 hover:bg-purple-700">
                    <GitBranch className="h-4 w-4 mr-2" />
                    Select Path
                  </Button>
                </div>
              )}

              {/* Status: Pending Parts - Can Resume */}
              {ticket.status === 'pending_parts' && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-orange-200">
                  <div>
                    <p className="font-medium text-orange-800">Waiting for Parts</p>
                    <p className="text-sm text-orange-600">SLA is paused. Resume when parts arrive.</p>
                  </div>
                  <Button onClick={handleResumeFromParts} disabled={actionLoading} className="bg-orange-600 hover:bg-orange-700">
                    <Play className="h-4 w-4 mr-2" />
                    Parts Received - Resume
                  </Button>
                </div>
              )}

              {/* Status: Device Pickup - Need to record pickup */}
              {ticket.status === 'device_pickup' && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-indigo-200">
                  <div>
                    <p className="font-medium text-indigo-800">Record Device Pickup</p>
                    <p className="text-sm text-indigo-600">Enter pickup details to move device to back office</p>
                  </div>
                  <Button onClick={() => setShowPickupModal(true)} className="bg-indigo-600 hover:bg-indigo-700">
                    <Truck className="h-4 w-4 mr-2" />
                    Record Pickup
                  </Button>
                </div>
              )}

              {/* Status: Device Under Repair - Need Warranty Decision */}
              {ticket.status === 'device_under_repair' && !ticket.warranty_decision && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-violet-200">
                  <div>
                    <p className="font-medium text-violet-800">Warranty Decision Required</p>
                    <p className="text-sm text-violet-600">Classify as AMC, OEM Warranty, or Out of Warranty</p>
                  </div>
                  <Button onClick={() => setShowWarrantyModal(true)} className="bg-violet-600 hover:bg-violet-700">
                    <Shield className="h-4 w-4 mr-2" />
                    Record Warranty Decision
                  </Button>
                </div>
              )}

              {/* Under Repair with AMC */}
              {ticket.status === 'device_under_repair' && ticket.warranty_type === 'under_amc' && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-blue-200">
                  <div>
                    <p className="font-medium text-blue-800">AMC Internal Repair</p>
                    <p className="text-sm text-blue-600">
                      {ticket.amc_repair ? 'Repair in progress' : 'Record repair details'}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => setShowAMCRepairModal(true)} variant="outline" className="border-blue-300">
                      <Wrench className="h-4 w-4 mr-2" />
                      {ticket.amc_repair ? 'Update Repair' : 'Start Repair'}
                    </Button>
                    {ticket.amc_repair && (
                      <Button onClick={handleCompleteAMCRepair} disabled={actionLoading} className="bg-green-600 hover:bg-green-700">
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        Complete Repair
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {/* Under Repair with OEM */}
              {ticket.status === 'device_under_repair' && ticket.warranty_type === 'under_oem' && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-cyan-200">
                  <div>
                    <p className="font-medium text-cyan-800">OEM Warranty Repair</p>
                    <p className="text-sm text-cyan-600">
                      {ticket.oem_repair ? `OEM: ${ticket.oem_repair.oem_name}` : 'Record OEM repair details'}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={() => setShowOEMRepairModal(true)} variant="outline" className="border-cyan-300">
                      <Factory className="h-4 w-4 mr-2" />
                      {ticket.oem_repair ? 'Update OEM Details' : 'Record OEM Details'}
                    </Button>
                    {ticket.oem_repair?.received_back_date && (
                      <Button onClick={handleCompleteOEMRepair} disabled={actionLoading} className="bg-green-600 hover:bg-green-700">
                        <CheckCircle2 className="h-4 w-4 mr-2" />
                        Complete Repair
                      </Button>
                    )}
                  </div>
                </div>
              )}

              {/* Ready for Delivery */}
              {(ticket.status === 'ready_for_delivery' || ticket.status === 'out_for_delivery') && (
                <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-teal-200">
                  <div>
                    <p className="font-medium text-teal-800">Device Ready for Delivery</p>
                    <p className="text-sm text-teal-600">Record delivery details to complete ticket</p>
                  </div>
                  <Button onClick={() => setShowDeliveryModal(true)} className="bg-teal-600 hover:bg-teal-700">
                    <Home className="h-4 w-4 mr-2" />
                    Record Delivery
                  </Button>
                </div>
              )}

              {/* Show current path if selected */}
              {ticket.resolution_path && (
                <div className="p-3 bg-slate-100 rounded-lg">
                  <div className="flex items-center gap-2 text-sm">
                    <span className="text-slate-600">Resolution Path:</span>
                    <Badge variant="outline" className="font-medium">
                      {ticket.resolution_path === 'resolved_on_visit' && '✅ Resolved On-Site'}
                      {ticket.resolution_path === 'pending_for_part' && '🟡 Pending for Parts'}
                      {ticket.resolution_path === 'device_to_backoffice' && '🔴 Device to Back Office'}
                    </Badge>
                    {ticket.warranty_type && (
                      <Badge variant="outline" className="ml-2">
                        {ticket.warranty_type === 'under_amc' && '📋 Under AMC'}
                        {ticket.warranty_type === 'under_oem' && '🏭 Under OEM Warranty'}
                        {ticket.warranty_type === 'out_of_warranty' && '⚠️ Out of Warranty'}
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

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

            {/* Ticket Configuration - osTicket Features */}
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center gap-2">
                  <Wrench className="h-4 w-4" />
                  Ticket Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-500">Help Topic</Label>
                    <Select
                      value={ticket.help_topic_id || 'none'}
                      onValueChange={async (value) => {
                        try {
                          await axios.patch(`${API_URL}/api/admin/service-tickets/${ticketId}`, 
                            { help_topic_id: value === 'none' ? null : value }, 
                            { headers }
                          );
                          toast.success('Help topic updated');
                          fetchTicket();
                        } catch (e) {
                          toast.error('Failed to update help topic');
                        }
                      }}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select help topic" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No Help Topic</SelectItem>
                        {helpTopics.map(topic => (
                          <SelectItem key={topic.id} value={topic.id}>{topic.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-slate-500">Department</Label>
                    <Select
                      value={ticket.department_id || 'none'}
                      onValueChange={async (value) => {
                        try {
                          await axios.patch(`${API_URL}/api/admin/service-tickets/${ticketId}`, 
                            { department_id: value === 'none' ? null : value }, 
                            { headers }
                          );
                          toast.success('Department updated');
                          fetchTicket();
                        } catch (e) {
                          toast.error('Failed to update department');
                        }
                      }}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select department" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No Department</SelectItem>
                        {departments.map(dept => (
                          <SelectItem key={dept.id} value={dept.id}>{dept.name}</SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <Label className="text-slate-500">SLA Policy</Label>
                    <Select
                      value={ticket.sla_policy_id || 'none'}
                      onValueChange={async (value) => {
                        try {
                          await axios.patch(`${API_URL}/api/admin/service-tickets/${ticketId}`, 
                            { sla_policy_id: value === 'none' ? null : value }, 
                            { headers }
                          );
                          toast.success('SLA policy updated');
                          fetchTicket();
                        } catch (e) {
                          toast.error('Failed to update SLA policy');
                        }
                      }}
                    >
                      <SelectTrigger className="w-full">
                        <SelectValue placeholder="Select SLA policy" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="none">No SLA Policy</SelectItem>
                        {slaPolicies.map(sla => (
                          <SelectItem key={sla.id} value={sla.id}>
                            {sla.name} ({sla.response_time}h / {sla.resolution_time}h)
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label className="text-slate-500">Priority</Label>
                    <Select
                      value={ticket.priority || 'medium'}
                      onValueChange={async (value) => {
                        try {
                          await axios.patch(`${API_URL}/api/admin/service-tickets/${ticketId}`, 
                            { priority: value }, 
                            { headers }
                          );
                          toast.success('Priority updated');
                          fetchTicket();
                        } catch (e) {
                          toast.error('Failed to update priority');
                        }
                      }}
                    >
                      <SelectTrigger className="w-full">
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
                </div>
                {ticket.sla_policy_id && ticket.sla_due_at && (
                  <div className="p-3 bg-amber-50 border border-amber-200 rounded-lg">
                    <Label className="text-amber-700 text-xs">SLA Due Date</Label>
                    <p className="text-amber-900 font-medium">{formatDate(ticket.sla_due_at)}</p>
                  </div>
                )}
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

          {/* Conversation Thread Section */}
          <div className="mt-6">
            <Card>
              <CardHeader className="border-b">
                <CardTitle className="text-lg flex items-center gap-2">
                  <History className="h-5 w-5" />
                  Conversation & Activity Thread
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {/* Reply Input Section */}
                <div className="p-4 bg-slate-50 border-b">
                  <Tabs defaultValue="reply" className="w-full">
                    <TabsList className="mb-3">
                      <TabsTrigger value="reply" className="flex items-center gap-2">
                        <Send className="h-4 w-4" />
                        Reply to Customer
                      </TabsTrigger>
                      <TabsTrigger value="internal" className="flex items-center gap-2">
                        <AlertCircle className="h-4 w-4" />
                        Internal Note
                      </TabsTrigger>
                    </TabsList>
                    <TabsContent value="reply" className="space-y-3">
                      <Textarea 
                        placeholder="Type your reply to the customer..."
                        value={commentText}
                        onChange={(e) => {
                          setCommentText(e.target.value);
                          setIsInternalComment(false);
                        }}
                        rows={3}
                        className="resize-none"
                      />
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {cannedResponses.length > 0 && (
                            <Select
                              onValueChange={(value) => {
                                const response = cannedResponses.find(r => r.id === value);
                                if (response) {
                                  setCommentText(response.content);
                                  setIsInternalComment(false);
                                }
                              }}
                            >
                              <SelectTrigger className="w-48">
                                <SelectValue placeholder="Insert canned response..." />
                              </SelectTrigger>
                              <SelectContent>
                                {cannedResponses.map(r => (
                                  <SelectItem key={r.id} value={r.id}>{r.title}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          )}
                        </div>
                        <Button 
                          onClick={handleAddComment} 
                          disabled={actionLoading || !commentText.trim()}
                          className="bg-blue-600 hover:bg-blue-700"
                        >
                          <Send className="h-4 w-4 mr-2" />
                          Send Reply
                        </Button>
                      </div>
                    </TabsContent>
                    <TabsContent value="internal" className="space-y-3">
                      <Textarea 
                        placeholder="Add an internal note (not visible to customer)..."
                        value={commentText}
                        onChange={(e) => {
                          setCommentText(e.target.value);
                          setIsInternalComment(true);
                        }}
                        rows={3}
                        className="resize-none bg-amber-50 border-amber-200"
                      />
                      <div className="flex items-center justify-end">
                        <Button 
                          onClick={handleAddComment} 
                          disabled={actionLoading || !commentText.trim()}
                          variant="outline"
                          className="border-amber-300 text-amber-700 hover:bg-amber-50"
                        >
                          <AlertCircle className="h-4 w-4 mr-2" />
                          Add Internal Note
                        </Button>
                      </div>
                    </TabsContent>
                  </Tabs>
                </div>

                {/* Thread Timeline */}
                <div className="divide-y">
                  {/* Combine comments and status_history into a single timeline */}
                  {(() => {
                    const allEvents = [];
                    
                    // Add comments
                    (ticket.comments || []).forEach(comment => {
                      allEvents.push({
                        type: 'comment',
                        id: comment.id,
                        created_at: comment.created_at,
                        author_name: comment.author_name,
                        text: comment.text,
                        is_internal: comment.is_internal
                      });
                    });
                    
                    // Add status changes
                    (ticket.status_history || []).forEach((change, idx) => {
                      allEvents.push({
                        type: 'status_change',
                        id: `status-${idx}`,
                        created_at: change.changed_at || change.timestamp,
                        from_status: change.from_status,
                        to_status: change.to_status || change.status,
                        changed_by: change.changed_by_name || change.changed_by,
                        notes: change.notes
                      });
                    });
                    
                    // Sort by date descending (newest first)
                    allEvents.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
                    
                    if (allEvents.length === 0) {
                      return (
                        <div className="p-8 text-center text-slate-500">
                          <MessageSquare className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                          <p>No conversation history yet</p>
                          <p className="text-sm">Start the conversation by adding a comment above</p>
                        </div>
                      );
                    }
                    
                    return allEvents.map((event) => (
                      <div key={event.id} className={`p-4 ${event.type === 'comment' && event.is_internal ? 'bg-amber-50' : ''}`}>
                        {event.type === 'comment' ? (
                          <div>
                            <div className="flex items-start gap-3">
                              <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-medium ${event.is_internal ? 'bg-amber-500' : 'bg-blue-500'}`}>
                                {event.author_name?.charAt(0)?.toUpperCase() || 'U'}
                              </div>
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="font-medium text-slate-900">{event.author_name}</span>
                                  {event.is_internal && (
                                    <Badge variant="outline" className="text-xs bg-amber-100 text-amber-700 border-amber-300">
                                      Internal Note
                                    </Badge>
                                  )}
                                  <span className="text-xs text-slate-500">{formatDate(event.created_at)}</span>
                                </div>
                                <p className="text-slate-700 whitespace-pre-wrap">{event.text}</p>
                              </div>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-3 text-sm">
                            <div className="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center">
                              <RefreshCw className="h-4 w-4 text-slate-500" />
                            </div>
                            <div className="flex-1">
                              <span className="text-slate-600">
                                <span className="font-medium">{event.changed_by || 'System'}</span>
                                {' changed status '}
                                {event.from_status && (
                                  <>
                                    from <Badge variant="outline" className="mx-1">{event.from_status}</Badge>
                                  </>
                                )}
                                to <Badge variant="outline" className="mx-1">{event.to_status}</Badge>
                              </span>
                              {event.notes && (
                                <p className="text-slate-500 mt-1 text-xs">{event.notes}</p>
                              )}
                              <span className="text-xs text-slate-400 block mt-1">{formatDate(event.created_at)}</span>
                            </div>
                          </div>
                        )}
                      </div>
                    ));
                  })()}
                </div>
              </CardContent>
            </Card>
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

      {/* Canned Response Modal */}
      <Dialog open={showCannedResponseModal} onOpenChange={setShowCannedResponseModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Zap className="h-5 w-5 text-purple-600" />
              Insert Canned Response
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {cannedResponses.length === 0 ? (
              <p className="text-slate-500 text-center py-4">No canned responses available. Create them in Ticketing Config.</p>
            ) : (
              cannedResponses.map(response => (
                <div 
                  key={response.id} 
                  className="p-4 border border-slate-200 rounded-lg hover:border-purple-300 hover:bg-purple-50 cursor-pointer transition-colors"
                  onClick={async () => {
                    try {
                      await axios.post(`${API_URL}/api/admin/service-tickets/${ticketId}/comments`, 
                        { text: response.content, is_internal: false }, 
                        { headers }
                      );
                      toast.success('Canned response added as comment');
                      setShowCannedResponseModal(false);
                      fetchTicket();
                    } catch (e) {
                      toast.error('Failed to add canned response');
                    }
                  }}
                >
                  <div className="flex items-center justify-between mb-2">
                    <h4 className="font-medium text-slate-900">{response.title}</h4>
                    <Badge variant="outline" className="text-xs">
                      {response.category || 'General'}
                    </Badge>
                  </div>
                  <p className="text-sm text-slate-600 line-clamp-3">{response.content}</p>
                </div>
              ))
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCannedResponseModal(false)}>Cancel</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
