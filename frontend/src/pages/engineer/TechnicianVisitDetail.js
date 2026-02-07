import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, MapPin, Phone, Building2, Clock, 
  CheckCircle2, Camera, AlertCircle, Play, User, Square,
  Calendar, FileText, Wrench, Package, Timer, Send, 
  Plus, X, History, Upload, ChevronDown, ChevronUp
} from 'lucide-react';
import { useEngineerAuth } from '../../context/EngineerAuthContext';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const TechnicianVisitDetail = () => {
  const { visitId } = useParams();
  const navigate = useNavigate();
  const { token, isAuthenticated, engineer } = useEngineerAuth();
  
  const [visit, setVisit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const timerRef = useRef(null);
  
  // Expandable sections
  const [showPreviousVisits, setShowPreviousVisits] = useState(false);
  
  // Modal states
  const [showDiagnosisModal, setShowDiagnosisModal] = useState(false);
  const [showResolveModal, setShowResolveModal] = useState(false);
  const [showPendingPartsModal, setShowPendingPartsModal] = useState(false);
  const [showPhotoModal, setShowPhotoModal] = useState(false);
  
  // Form data for diagnosis
  const [diagnosisData, setDiagnosisData] = useState({
    problem_identified: '',
    root_cause: '',
    observations: ''
  });
  
  // Form data for resolution
  const [resolutionData, setResolutionData] = useState({
    resolution_summary: '',
    actions_taken: [],
    recommendations: ''
  });
  const [newAction, setNewAction] = useState('');
  
  // Form data for pending parts
  const [partsData, setPartsData] = useState({
    diagnosis: {
      problem_identified: '',
      root_cause: '',
      observations: ''
    },
    parts_required: [],
    remarks: ''
  });
  const [newPart, setNewPart] = useState({
    item_id: '',
    item_name: '',
    item_description: '',
    quantity: 1,
    urgency: 'normal',
    notes: ''
  });
  
  // Inventory items for selection
  const [inventoryItems, setInventoryItems] = useState([]);
  const [searchingItems, setSearchingItems] = useState(false);
  const [itemSearch, setItemSearch] = useState('');

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/engineer');
    }
  }, [isAuthenticated, navigate]);

  // Fetch visit details using new engineer portal API
  const fetchVisitDetails = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${API}/api/engineer/visits/${visitId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      // Handle both old and new API response structures
      let visitData;
      if (response.data.visit) {
        // Old API structure: { visit: {...}, ticket: {...}, device: {...}, company: {...} }
        visitData = {
          ...response.data.visit,
          ticket: response.data.ticket || {},
          previous_visits: response.data.service_history || [],
          parts_issued: []
        };
      } else {
        // New API structure: flat object with nested data
        visitData = response.data;
      }
      
      setVisit(visitData);
      
      // Pre-fill diagnosis form if data exists
      if (visitData.problem_found || visitData.diagnosis) {
        setDiagnosisData({
          problem_identified: visitData.problem_found || '',
          root_cause: visitData.diagnosis || '',
          observations: visitData.findings || ''
        });
      }
    } catch (err) {
      console.error('Failed to fetch visit:', err);
      toast.error('Failed to load visit details');
      navigate('/engineer/dashboard');
    } finally {
      setLoading(false);
    }
  }, [visitId, token, navigate]);

  useEffect(() => {
    fetchVisitDetails();
  }, [fetchVisitDetails]);

  // Timer for in-progress visits
  useEffect(() => {
    if (visit?.status === 'in_progress' && visit?.start_time) {
      const startTime = new Date(visit.start_time).getTime();
      
      const updateTimer = () => {
        const now = Date.now();
        const elapsed = Math.floor((now - startTime) / 1000);
        setElapsedTime(elapsed);
      };
      
      updateTimer();
      timerRef.current = setInterval(updateTimer, 1000);
      
      return () => {
        if (timerRef.current) {
          clearInterval(timerRef.current);
        }
      };
    }
  }, [visit?.status, visit?.start_time]);

  // Search inventory items
  const searchInventory = async (query) => {
    if (!query || query.length < 2) {
      setInventoryItems([]);
      return;
    }
    
    setSearchingItems(true);
    try {
      const response = await axios.get(`${API}/api/engineer/inventory/items?search=${query}&limit=10`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setInventoryItems(response.data.items || []);
    } catch (err) {
      console.error('Failed to search items:', err);
    } finally {
      setSearchingItems(false);
    }
  };

  // Start Visit
  const handleStartVisit = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API}/api/engineer/visits/${visitId}/start`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Visit started!');
      fetchVisitDetails();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start visit');
    } finally {
      setActionLoading(false);
    }
  };

  // End Visit (just stops timer, doesn't resolve)
  const handleEndVisit = async () => {
    setActionLoading(true);
    try {
      await axios.post(`${API}/api/engineer/visits/${visitId}/end`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Visit timer stopped');
      fetchVisitDetails();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to end visit');
    } finally {
      setActionLoading(false);
    }
  };

  // Save Diagnosis
  const handleSaveDiagnosis = async () => {
    if (!diagnosisData.problem_identified.trim()) {
      toast.error('Please enter the problem identified');
      return;
    }
    
    setActionLoading(true);
    try {
      await axios.post(`${API}/api/engineer/visits/${visitId}/diagnosis`, diagnosisData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Diagnosis saved');
      setShowDiagnosisModal(false);
      fetchVisitDetails();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save diagnosis');
    } finally {
      setActionLoading(false);
    }
  };

  // Resolve Visit
  const handleResolveVisit = async () => {
    if (!resolutionData.resolution_summary.trim()) {
      toast.error('Please enter resolution summary');
      return;
    }
    
    setActionLoading(true);
    try {
      await axios.post(`${API}/api/engineer/visits/${visitId}/resolve`, resolutionData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Visit resolved successfully!');
      setShowResolveModal(false);
      navigate('/engineer/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to resolve visit');
    } finally {
      setActionLoading(false);
    }
  };

  // Mark Pending Parts
  const handleMarkPendingParts = async () => {
    if (!partsData.diagnosis.problem_identified.trim()) {
      toast.error('Please enter the problem identified');
      return;
    }
    if (partsData.parts_required.length === 0) {
      toast.error('Please add at least one part');
      return;
    }
    if (!partsData.remarks.trim()) {
      toast.error('Please enter remarks (mandatory)');
      return;
    }
    
    setActionLoading(true);
    try {
      const response = await axios.post(`${API}/api/engineer/visits/${visitId}/pending-parts`, partsData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Marked as pending parts. Quotation ${response.data.quotation_number} created.`);
      setShowPendingPartsModal(false);
      navigate('/engineer/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to mark pending parts');
    } finally {
      setActionLoading(false);
    }
  };

  // Add action to resolution list
  const handleAddAction = () => {
    if (!newAction.trim()) return;
    setResolutionData(prev => ({
      ...prev,
      actions_taken: [...prev.actions_taken, newAction.trim()]
    }));
    setNewAction('');
  };

  // Remove action from resolution list
  const handleRemoveAction = (index) => {
    setResolutionData(prev => ({
      ...prev,
      actions_taken: prev.actions_taken.filter((_, i) => i !== index)
    }));
  };

  // Add part to parts list
  const handleAddPart = () => {
    if (!newPart.item_name.trim()) {
      toast.error('Please enter part name');
      return;
    }
    setPartsData(prev => ({
      ...prev,
      parts_required: [...prev.parts_required, { ...newPart }]
    }));
    setNewPart({
      item_id: '',
      item_name: '',
      item_description: '',
      quantity: 1,
      urgency: 'normal',
      notes: ''
    });
    setItemSearch('');
    setInventoryItems([]);
  };

  // Remove part from list
  const handleRemovePart = (index) => {
    setPartsData(prev => ({
      ...prev,
      parts_required: prev.parts_required.filter((_, i) => i !== index)
    }));
  };

  // Select item from inventory
  const handleSelectInventoryItem = (item) => {
    setNewPart(prev => ({
      ...prev,
      item_id: item.id,
      item_name: item.name,
      item_description: item.description || ''
    }));
    setItemSearch(item.name);
    setInventoryItems([]);
  };

  const formatTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hrs.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit'
    });
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-50 text-blue-600 border-blue-200';
      case 'in_progress': return 'bg-amber-50 text-amber-600 border-amber-200';
      case 'paused': return 'bg-orange-50 text-orange-600 border-orange-200';
      case 'completed': return 'bg-emerald-50 text-emerald-600 border-emerald-200';
      default: return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!visit) return null;

  const ticket = visit.ticket || {};
  const isScheduled = visit.status === 'scheduled';
  const isInProgress = visit.status === 'in_progress' || visit.status === 'on_site';
  const isCompleted = visit.status === 'completed';
  const isPaused = visit.status === 'paused';
  const hasDiagnosis = visit.problem_found || visit.diagnosis;

  return (
    <div data-testid="technician-visit-detail" className="min-h-screen bg-slate-50 pb-32">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 text-white sticky top-0 z-50">
        <div className="px-4 py-4">
          <div className="flex items-center gap-3">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/engineer/dashboard')}
              className="text-white hover:bg-slate-700 p-2"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div className="flex-1">
              <p className="font-semibold flex items-center gap-2">
                Visit #{visit.visit_number}
                <span className="text-slate-400">•</span>
                <span className="font-mono text-blue-300 text-sm">#{visit.ticket_number}</span>
              </p>
              <p className="text-xs text-slate-400">{ticket.company_name}</p>
            </div>
            <Badge className={`${getStatusColor(visit.status)} border`}>
              {visit.status?.replace('_', ' ')}
            </Badge>
          </div>
        </div>

        {/* Timer Display for In Progress */}
        {isInProgress && (
          <div className="px-4 pb-4">
            <div className="bg-amber-500/20 border border-amber-500/30 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-amber-500 rounded-full flex items-center justify-center animate-pulse">
                    <Timer className="h-5 w-5 text-white" />
                  </div>
                  <div>
                    <p className="text-amber-200 text-sm">Visit In Progress</p>
                    <p className="text-2xl font-mono font-bold text-white">{formatTime(elapsedTime)}</p>
                  </div>
                </div>
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={handleEndVisit}
                  disabled={actionLoading}
                  className="border-amber-400 text-amber-400 hover:bg-amber-500/20"
                >
                  <Square className="h-4 w-4 mr-1" />
                  Stop
                </Button>
              </div>
            </div>
          </div>
        )}
      </header>

      <main className="p-4 space-y-4">
        {/* Ticket Summary */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Issue Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="font-medium text-slate-900">{ticket.title}</p>
            {ticket.description && (
              <p className="text-sm text-slate-600">{ticket.description}</p>
            )}
            {ticket.priority && (
              <Badge className={`
                ${ticket.priority === 'critical' ? 'bg-red-500 text-white' :
                  ticket.priority === 'high' ? 'bg-orange-500 text-white' :
                  ticket.priority === 'medium' ? 'bg-yellow-500 text-white' :
                  'bg-slate-400 text-white'}
              `}>
                {ticket.priority}
              </Badge>
            )}
          </CardContent>
        </Card>

        {/* Customer & Location */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Customer
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="font-medium">{ticket.company_name}</p>
            {ticket.contact && (
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2">
                  <User className="h-4 w-4 text-slate-400" />
                  <span>{ticket.contact.name}</span>
                </div>
                {ticket.contact.phone && (
                  <a href={`tel:${ticket.contact.phone}`} className="flex items-center gap-2 text-blue-600">
                    <Phone className="h-4 w-4" />
                    {ticket.contact.phone}
                  </a>
                )}
              </div>
            )}
            {ticket.location && (
              <div className="pt-2 border-t">
                <div className="flex items-start gap-2 text-sm text-slate-600">
                  <MapPin className="h-4 w-4 text-slate-400 mt-0.5" />
                  <span>{ticket.location.address}{ticket.location.city && `, ${ticket.location.city}`}</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Device Info */}
        {ticket.device_name && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Wrench className="h-4 w-4" />
                Device
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Device</span>
                <span>{ticket.device_name}</span>
              </div>
              {ticket.device_serial && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Serial</span>
                  <span className="font-mono">{ticket.device_serial}</span>
                </div>
              )}
              {ticket.warranty_status && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Warranty</span>
                  <Badge variant="outline">{ticket.warranty_status}</Badge>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Diagnosis & Findings */}
        <Card className={hasDiagnosis ? 'border-emerald-200' : 'border-amber-200'}>
          <CardHeader className="pb-2">
            <div className="flex items-center justify-between">
              <CardTitle className="text-sm flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Diagnosis & Findings
              </CardTitle>
              {isInProgress && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setShowDiagnosisModal(true)}
                >
                  {hasDiagnosis ? 'Edit' : 'Add'}
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {hasDiagnosis ? (
              <div className="space-y-3 text-sm">
                <div>
                  <p className="text-slate-500 text-xs">Problem Identified</p>
                  <p className="font-medium">{visit.problem_found}</p>
                </div>
                {visit.diagnosis && (
                  <div>
                    <p className="text-slate-500 text-xs">Root Cause</p>
                    <p>{visit.diagnosis}</p>
                  </div>
                )}
                {visit.findings && (
                  <div>
                    <p className="text-slate-500 text-xs">Observations</p>
                    <p>{visit.findings}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-slate-500 text-sm italic">
                {isInProgress ? 'Click "Add" to record diagnosis' : 'No diagnosis recorded'}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Previous Visits */}
        {visit.previous_visits?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <button 
                className="flex items-center justify-between w-full"
                onClick={() => setShowPreviousVisits(!showPreviousVisits)}
              >
                <CardTitle className="text-sm flex items-center gap-2">
                  <History className="h-4 w-4" />
                  Previous Visits ({visit.previous_visits.length})
                </CardTitle>
                {showPreviousVisits ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </button>
            </CardHeader>
            {showPreviousVisits && (
              <CardContent>
                <div className="space-y-3">
                  {visit.previous_visits.map((pv, idx) => (
                    <div key={idx} className="border border-slate-200 rounded-lg p-3 text-sm">
                      <div className="flex justify-between items-center mb-2">
                        <span className="font-medium">Visit #{pv.visit_number}</span>
                        <Badge variant="outline" className="text-xs capitalize">{pv.status}</Badge>
                      </div>
                      <p className="text-xs text-slate-500 mb-1">{pv.scheduled_date} • {pv.technician_name}</p>
                      {pv.problem_found && (
                        <p className="text-slate-700"><strong>Problem:</strong> {pv.problem_found}</p>
                      )}
                      {pv.resolution && (
                        <p className="text-slate-700"><strong>Resolution:</strong> {pv.resolution}</p>
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            )}
          </Card>
        )}

        {/* Parts Issued (for this visit) */}
        {visit.parts_issued?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Package className="h-4 w-4" />
                Parts Issued ({visit.parts_issued.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {visit.parts_issued.map((part, idx) => (
                  <div key={idx} className="flex justify-between items-center text-sm border-b border-slate-100 pb-2 last:border-0">
                    <div>
                      <p className="font-medium">{part.item_name}</p>
                      <p className="text-xs text-slate-500">Qty: {part.quantity_issued}</p>
                    </div>
                    {part.serial_numbers?.length > 0 && (
                      <span className="text-xs text-slate-400 font-mono">{part.serial_numbers.join(', ')}</span>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Photos */}
        {visit.photos?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Camera className="h-4 w-4" />
                Photos ({visit.photos.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-2">
                {visit.photos.map((photo, idx) => (
                  <img key={idx} src={photo} alt={`Visit photo ${idx + 1}`} className="rounded-lg w-full h-20 object-cover" />
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Resolution Summary (if completed) */}
        {isCompleted && visit.resolution && (
          <Card className="border-emerald-200 bg-emerald-50/50">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2 text-emerald-700">
                <CheckCircle2 className="h-4 w-4" />
                Resolution
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700">{visit.resolution}</p>
              {visit.actions_taken?.length > 0 && (
                <div className="mt-3 pt-3 border-t border-emerald-200">
                  <p className="text-xs text-slate-500 mb-1">Actions Taken:</p>
                  <ul className="list-disc list-inside text-sm">
                    {visit.actions_taken.map((action, idx) => (
                      <li key={idx}>{action}</li>
                    ))}
                  </ul>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </main>

      {/* Bottom Action Buttons */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 space-y-2">
        {isScheduled && (
          <Button 
            className="w-full bg-blue-500 hover:bg-blue-600 h-12"
            onClick={handleStartVisit}
            disabled={actionLoading}
            data-testid="start-visit-btn"
          >
            <Play className="h-5 w-5 mr-2" />
            Start Visit
          </Button>
        )}
        
        {isInProgress && (
          <div className="grid grid-cols-2 gap-2">
            <Button 
              className="bg-emerald-500 hover:bg-emerald-600"
              onClick={() => setShowResolveModal(true)}
              disabled={actionLoading || !hasDiagnosis}
              data-testid="resolve-btn"
            >
              <CheckCircle2 className="h-4 w-4 mr-2" />
              Resolve
            </Button>
            <Button 
              variant="outline"
              className="border-orange-300 text-orange-600 hover:bg-orange-50"
              onClick={() => {
                setPartsData(prev => ({
                  ...prev,
                  diagnosis: { ...diagnosisData }
                }));
                setShowPendingPartsModal(true);
              }}
              disabled={actionLoading}
              data-testid="pending-parts-btn"
            >
              <Package className="h-4 w-4 mr-2" />
              Need Parts
            </Button>
          </div>
        )}
        
        {isPaused && (
          <div className="text-center py-2">
            <Badge className="bg-orange-100 text-orange-700 border border-orange-300">
              Pending Parts - Awaiting Quotation Approval
            </Badge>
          </div>
        )}
        
        {isCompleted && (
          <Button 
            variant="outline"
            className="w-full"
            onClick={() => navigate('/engineer/dashboard')}
          >
            Back to Dashboard
          </Button>
        )}
      </div>

      {/* Diagnosis Modal */}
      <Dialog open={showDiagnosisModal} onOpenChange={setShowDiagnosisModal}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Diagnosis & Findings</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Problem Identified *</Label>
              <Textarea
                placeholder="Describe the problem found..."
                value={diagnosisData.problem_identified}
                onChange={(e) => setDiagnosisData(prev => ({ ...prev, problem_identified: e.target.value }))}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label>Root Cause</Label>
              <Textarea
                placeholder="What caused the problem..."
                value={diagnosisData.root_cause}
                onChange={(e) => setDiagnosisData(prev => ({ ...prev, root_cause: e.target.value }))}
                rows={2}
              />
            </div>
            <div className="space-y-2">
              <Label>Observations</Label>
              <Textarea
                placeholder="Additional observations..."
                value={diagnosisData.observations}
                onChange={(e) => setDiagnosisData(prev => ({ ...prev, observations: e.target.value }))}
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDiagnosisModal(false)}>Cancel</Button>
            <Button onClick={handleSaveDiagnosis} disabled={actionLoading}>
              {actionLoading ? 'Saving...' : 'Save Diagnosis'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Resolve Modal */}
      <Dialog open={showResolveModal} onOpenChange={setShowResolveModal}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Resolve Visit</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Resolution Summary *</Label>
              <Textarea
                placeholder="Describe how the issue was resolved..."
                value={resolutionData.resolution_summary}
                onChange={(e) => setResolutionData(prev => ({ ...prev, resolution_summary: e.target.value }))}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label>Actions Taken</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Add an action..."
                  value={newAction}
                  onChange={(e) => setNewAction(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddAction()}
                />
                <Button type="button" onClick={handleAddAction} size="icon">
                  <Plus className="h-4 w-4" />
                </Button>
              </div>
              {resolutionData.actions_taken.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {resolutionData.actions_taken.map((action, idx) => (
                    <Badge key={idx} variant="secondary" className="flex items-center gap-1">
                      {action}
                      <X className="h-3 w-3 cursor-pointer" onClick={() => handleRemoveAction(idx)} />
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <div className="space-y-2">
              <Label>Recommendations</Label>
              <Textarea
                placeholder="Any recommendations for the customer..."
                value={resolutionData.recommendations}
                onChange={(e) => setResolutionData(prev => ({ ...prev, recommendations: e.target.value }))}
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowResolveModal(false)}>Cancel</Button>
            <Button onClick={handleResolveVisit} disabled={actionLoading} className="bg-emerald-500 hover:bg-emerald-600">
              {actionLoading ? 'Resolving...' : 'Resolve & Complete'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Pending Parts Modal */}
      <Dialog open={showPendingPartsModal} onOpenChange={setShowPendingPartsModal}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Request Parts</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {/* Diagnosis Section */}
            <div className="border rounded-lg p-3 bg-slate-50">
              <p className="text-sm font-medium mb-2">Diagnosis (Required)</p>
              <div className="space-y-2">
                <Input
                  placeholder="Problem identified *"
                  value={partsData.diagnosis.problem_identified}
                  onChange={(e) => setPartsData(prev => ({ 
                    ...prev, 
                    diagnosis: { ...prev.diagnosis, problem_identified: e.target.value }
                  }))}
                />
                <Input
                  placeholder="Root cause"
                  value={partsData.diagnosis.root_cause}
                  onChange={(e) => setPartsData(prev => ({ 
                    ...prev, 
                    diagnosis: { ...prev.diagnosis, root_cause: e.target.value }
                  }))}
                />
              </div>
            </div>

            {/* Parts Selection */}
            <div className="space-y-2">
              <Label>Add Parts</Label>
              <div className="relative">
                <Input
                  placeholder="Search inventory or type part name..."
                  value={itemSearch}
                  onChange={(e) => {
                    setItemSearch(e.target.value);
                    setNewPart(prev => ({ ...prev, item_name: e.target.value, item_id: '' }));
                    searchInventory(e.target.value);
                  }}
                />
                {inventoryItems.length > 0 && (
                  <div className="absolute z-10 w-full mt-1 bg-white border rounded-lg shadow-lg max-h-40 overflow-y-auto">
                    {inventoryItems.map((item) => (
                      <button
                        key={item.id}
                        className="w-full px-3 py-2 text-left hover:bg-slate-50 text-sm"
                        onClick={() => handleSelectInventoryItem(item)}
                      >
                        <span className="font-medium">{item.name}</span>
                        {item.sku && <span className="text-slate-400 ml-2">({item.sku})</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <div className="grid grid-cols-2 gap-2">
                <Input
                  type="number"
                  min="1"
                  placeholder="Qty"
                  value={newPart.quantity}
                  onChange={(e) => setNewPart(prev => ({ ...prev, quantity: parseInt(e.target.value) || 1 }))}
                />
                <Select value={newPart.urgency} onValueChange={(v) => setNewPart(prev => ({ ...prev, urgency: v }))}>
                  <SelectTrigger>
                    <SelectValue placeholder="Urgency" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="normal">Normal</SelectItem>
                    <SelectItem value="urgent">Urgent</SelectItem>
                    <SelectItem value="critical">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Button type="button" variant="outline" onClick={handleAddPart} className="w-full">
                <Plus className="h-4 w-4 mr-2" />
                Add Part
              </Button>
            </div>

            {/* Parts List */}
            {partsData.parts_required.length > 0 && (
              <div className="space-y-2">
                <Label>Parts to Request ({partsData.parts_required.length})</Label>
                <div className="space-y-2">
                  {partsData.parts_required.map((part, idx) => (
                    <div key={idx} className="flex items-center justify-between bg-slate-50 rounded-lg p-2 text-sm">
                      <div>
                        <span className="font-medium">{part.item_name}</span>
                        <span className="text-slate-500 ml-2">x{part.quantity}</span>
                        <Badge variant="outline" className="ml-2 text-xs capitalize">{part.urgency}</Badge>
                      </div>
                      <Button variant="ghost" size="sm" onClick={() => handleRemovePart(idx)}>
                        <X className="h-4 w-4" />
                      </Button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Remarks */}
            <div className="space-y-2">
              <Label>Remarks (Mandatory) *</Label>
              <Textarea
                placeholder="Explain why these parts are needed..."
                value={partsData.remarks}
                onChange={(e) => setPartsData(prev => ({ ...prev, remarks: e.target.value }))}
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPendingPartsModal(false)}>Cancel</Button>
            <Button 
              onClick={handleMarkPendingParts} 
              disabled={actionLoading}
              className="bg-orange-500 hover:bg-orange-600"
            >
              {actionLoading ? 'Submitting...' : 'Submit & Create Quotation'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TechnicianVisitDetail;
