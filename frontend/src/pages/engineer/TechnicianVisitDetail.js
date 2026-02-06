import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, MapPin, Phone, Building2, Laptop, Clock, 
  CheckCircle2, Camera, AlertCircle, Play, User, Square,
  Calendar, FileText, Wrench, Package, Timer, Send
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
  const { token, isAuthenticated } = useEngineerAuth();
  
  const [visit, setVisit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  
  // Modal states
  const [showStopTimerModal, setShowStopTimerModal] = useState(false);
  const [showAddActionModal, setShowAddActionModal] = useState(false);
  const [showRequestPartsModal, setShowRequestPartsModal] = useState(false);
  
  // Form data
  const [stopTimerData, setStopTimerData] = useState({
    diagnostics: '',
    actions_taken: [],
    work_summary: '',
    outcome: 'resolved',
    customer_name: '',
    notes: ''
  });
  const [newAction, setNewAction] = useState('');
  const [actionToAdd, setActionToAdd] = useState('');
  
  // Items for parts request
  const [items, setItems] = useState([]);
  const [partsRequestData, setPartsRequestData] = useState({
    item_id: '',
    quantity_requested: 1,
    urgency: 'normal',
    request_notes: ''
  });

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/engineer');
    }
  }, [isAuthenticated, navigate]);

  // Fetch visit details
  const fetchVisitDetails = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${API}/api/admin/visits/${visitId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setVisit(response.data);
      
      // Pre-fill stop timer data if visit has data
      if (response.data.diagnostics || response.data.work_summary) {
        setStopTimerData({
          diagnostics: response.data.diagnostics || '',
          actions_taken: response.data.actions_taken || [],
          work_summary: response.data.work_summary || '',
          outcome: response.data.outcome || 'resolved',
          customer_name: response.data.customer_name || '',
          notes: response.data.internal_notes || ''
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

  // Fetch items for parts request
  const fetchItems = useCallback(async () => {
    if (!token) return;
    try {
      const res = await axios.get(`${API}/api/admin/items?limit=500`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setItems(res.data.items || []);
    } catch (err) {
      console.error('Failed to fetch items:', err);
    }
  }, [token]);

  useEffect(() => {
    fetchVisitDetails();
    fetchItems();
  }, [fetchVisitDetails, fetchItems]);

  // Timer effect for in-progress visits
  useEffect(() => {
    if (visit?.status === 'in_progress' && visit?.start_time) {
      const startTime = new Date(visit.start_time).getTime();
      
      const updateElapsed = () => {
        const now = Date.now();
        const elapsed = Math.floor((now - startTime) / 1000);
        setElapsedTime(elapsed);
      };
      
      updateElapsed();
      const interval = setInterval(updateElapsed, 1000);
      
      return () => clearInterval(interval);
    }
  }, [visit?.status, visit?.start_time]);

  // Format elapsed time
  const formatElapsedTime = (seconds) => {
    const hrs = Math.floor(seconds / 3600);
    const mins = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    
    if (hrs > 0) {
      return `${hrs}h ${mins}m ${secs}s`;
    }
    return `${mins}m ${secs}s`;
  };

  // Start timer
  const handleStartTimer = async () => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/admin/visits/${visitId}/start-timer`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Timer started! Work in progress.');
      fetchVisitDetails();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to start timer');
    } finally {
      setActionLoading(false);
    }
  };

  // Stop timer
  const handleStopTimer = async () => {
    if (!stopTimerData.work_summary) {
      toast.error('Please provide a work summary');
      return;
    }
    
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/admin/visits/${visitId}/stop-timer`,
        stopTimerData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Visit completed successfully!');
      setShowStopTimerModal(false);
      navigate('/engineer/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to stop timer');
    } finally {
      setActionLoading(false);
    }
  };

  // Add action
  const handleAddAction = async () => {
    if (!actionToAdd.trim()) {
      toast.error('Please enter an action');
      return;
    }
    
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/admin/visits/${visitId}/add-action`,
        { action: actionToAdd },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Action recorded');
      setShowAddActionModal(false);
      setActionToAdd('');
      fetchVisitDetails();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to add action');
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
      await axios.post(
        `${API}/api/admin/ticket-parts/requests`,
        { 
          ...partsRequestData, 
          ticket_id: visit.ticket_id,
          visit_id: visitId 
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Parts requested successfully');
      setShowRequestPartsModal(false);
      setPartsRequestData({ item_id: '', quantity_requested: 1, urgency: 'normal', request_notes: '' });
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to request parts');
    } finally {
      setActionLoading(false);
    }
  };

  // Add action to stop timer form
  const addActionToList = () => {
    if (newAction.trim()) {
      setStopTimerData({
        ...stopTimerData,
        actions_taken: [...stopTimerData.actions_taken, newAction.trim()]
      });
      setNewAction('');
    }
  };

  const removeActionFromList = (index) => {
    setStopTimerData({
      ...stopTimerData,
      actions_taken: stopTimerData.actions_taken.filter((_, i) => i !== index)
    });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!visit) return null;

  const isScheduled = visit.status === 'scheduled';
  const isInProgress = visit.status === 'in_progress';
  const isCompleted = visit.status === 'completed';

  return (
    <div data-testid="visit-detail-page" className="min-h-screen bg-slate-50 pb-32">
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
                <span className="font-mono text-blue-300">#{visit.ticket_number}</span>
                <span className="text-slate-400">•</span>
                <span>Visit #{visit.visit_number}</span>
              </p>
              <p className="text-xs text-slate-400 capitalize">{visit.status?.replace('_', ' ')}</p>
            </div>
          </div>
        </div>

        {/* Live Timer for In Progress */}
        {isInProgress && (
          <div className="px-4 pb-4">
            <div className="bg-amber-500/20 border border-amber-500/30 rounded-xl p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-amber-500 rounded-full animate-pulse" />
                  <div>
                    <p className="text-xs text-amber-200">TIME ELAPSED</p>
                    <p className="text-2xl font-mono font-bold text-amber-400">
                      {formatElapsedTime(elapsedTime)}
                    </p>
                  </div>
                </div>
                <Button 
                  onClick={() => setShowStopTimerModal(true)}
                  className="bg-red-500 hover:bg-red-600"
                  data-testid="stop-timer-btn"
                >
                  <Square className="h-4 w-4 mr-2" />
                  Stop
                </Button>
              </div>
            </div>
          </div>
        )}
      </header>

      <main className="p-4 space-y-4">
        {/* Status Card */}
        <Card className={`border-l-4 ${
          isScheduled ? 'border-l-blue-500' : 
          isInProgress ? 'border-l-amber-500' : 'border-l-emerald-500'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isScheduled && <Clock className="h-6 w-6 text-blue-500" />}
                {isInProgress && <Play className="h-6 w-6 text-amber-500" />}
                {isCompleted && <CheckCircle2 className="h-6 w-6 text-emerald-500" />}
                <div>
                  <p className="font-medium text-slate-900">
                    {isScheduled && 'Ready to Start'}
                    {isInProgress && 'Work in Progress'}
                    {isCompleted && 'Visit Completed'}
                  </p>
                  <p className="text-sm text-slate-500">
                    {isScheduled && 'Start the timer when you begin work'}
                    {isInProgress && 'Remember to stop the timer when done'}
                    {isCompleted && `Completed in ${visit.duration_minutes} minutes`}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Ticket Info */}
        {visit.ticket && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Ticket Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 text-sm">Ticket</span>
                <span className="font-mono font-medium">#{visit.ticket.ticket_number}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 text-sm">Title</span>
                <span className="font-medium text-right max-w-[60%]">{visit.ticket.title}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-500 text-sm">Company</span>
                <span>{visit.ticket.company_name}</span>
              </div>
              {visit.ticket.device_name && (
                <div className="flex justify-between items-center">
                  <span className="text-slate-500 text-sm">Device</span>
                  <span>{visit.ticket.device_name}</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Contact Info */}
        {visit.ticket?.contact && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <User className="h-4 w-4" />
                Contact Information
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="font-medium">{visit.ticket.contact.name}</p>
              {visit.ticket.contact.phone && (
                <a 
                  href={`tel:${visit.ticket.contact.phone}`}
                  className="flex items-center gap-2 text-sm text-blue-600"
                >
                  <Phone className="h-4 w-4" />
                  {visit.ticket.contact.phone}
                </a>
              )}
            </CardContent>
          </Card>
        )}

        {/* Location */}
        {(visit.visit_location || visit.ticket?.location) && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Location
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700">
                {visit.visit_location || 
                  (visit.ticket?.location && 
                    `${visit.ticket.location.site_name || ''} ${visit.ticket.location.address || ''} ${visit.ticket.location.city || ''}`.trim()
                  )
                }
              </p>
            </CardContent>
          </Card>
        )}

        {/* Schedule */}
        {visit.scheduled_date && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Schedule
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Date</span>
                <span>{visit.scheduled_date}</span>
              </div>
              {visit.scheduled_time_from && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Time</span>
                  <span>{visit.scheduled_time_from} - {visit.scheduled_time_to || 'TBD'}</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Purpose */}
        {visit.purpose && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Wrench className="h-4 w-4" />
                Purpose
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700">{visit.purpose}</p>
            </CardContent>
          </Card>
        )}

        {/* Actions Taken (for in-progress/completed) */}
        {(isInProgress || isCompleted) && visit.actions_taken?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Actions Taken
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {visit.actions_taken.map((action, i) => (
                  <li key={i} className="flex items-start gap-2 text-sm">
                    <span className="w-1.5 h-1.5 bg-blue-500 rounded-full mt-2" />
                    {action}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Work Summary (for completed) */}
        {isCompleted && visit.work_summary && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Work Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              {visit.diagnostics && (
                <div>
                  <p className="text-slate-500 mb-1">Diagnostics</p>
                  <p className="text-slate-900">{visit.diagnostics}</p>
                </div>
              )}
              <div>
                <p className="text-slate-500 mb-1">Summary</p>
                <p className="text-slate-900">{visit.work_summary}</p>
              </div>
              {visit.outcome && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Outcome</span>
                  <Badge variant="outline" className="capitalize">{visit.outcome}</Badge>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Timeline (for completed) */}
        {isCompleted && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Timer className="h-4 w-4" />
                Time Log
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Started</span>
                <span>{formatDateTime(visit.start_time)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Ended</span>
                <span>{formatDateTime(visit.end_time)}</span>
              </div>
              <div className="flex justify-between font-medium">
                <span className="text-slate-500">Duration</span>
                <span>{visit.duration_minutes} minutes</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Parts Issued */}
        {visit.parts_issued?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Package className="h-4 w-4" />
                Parts Used
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {visit.parts_issued.map((part) => (
                  <div key={part.id} className="flex justify-between items-center text-sm">
                    <span>{part.item_name}</span>
                    <Badge variant="outline">x{part.quantity_issued}</Badge>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>

      {/* Action Buttons */}
      {!isCompleted && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 space-y-2">
          {isScheduled && (
            <Button 
              className="w-full bg-blue-500 hover:bg-blue-600 h-12"
              onClick={handleStartTimer}
              disabled={actionLoading}
              data-testid="start-timer-btn"
            >
              <Play className="h-5 w-5 mr-2" />
              {actionLoading ? 'Starting...' : 'Start Timer'}
            </Button>
          )}
          
          {isInProgress && (
            <>
              <div className="grid grid-cols-2 gap-2">
                <Button 
                  variant="outline" 
                  className="h-12"
                  onClick={() => setShowAddActionModal(true)}
                >
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Add Action
                </Button>
                <Button 
                  variant="outline" 
                  className="h-12"
                  onClick={() => setShowRequestPartsModal(true)}
                >
                  <Package className="h-4 w-4 mr-2" />
                  Request Parts
                </Button>
              </div>
              <Button 
                className="w-full bg-emerald-500 hover:bg-emerald-600 h-12"
                onClick={() => setShowStopTimerModal(true)}
                data-testid="complete-btn"
              >
                <CheckCircle2 className="h-5 w-5 mr-2" />
                Complete Visit
              </Button>
            </>
          )}
        </div>
      )}

      {/* Stop Timer / Complete Modal */}
      <Dialog open={showStopTimerModal} onOpenChange={setShowStopTimerModal}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Complete Visit</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="bg-slate-100 rounded-lg p-3 text-center">
              <p className="text-sm text-slate-500">Total Time</p>
              <p className="text-xl font-mono font-bold">{formatElapsedTime(elapsedTime)}</p>
            </div>
            
            <div className="space-y-2">
              <Label>Diagnostics</Label>
              <Textarea
                placeholder="What did you find/diagnose?"
                value={stopTimerData.diagnostics}
                onChange={(e) => setStopTimerData({...stopTimerData, diagnostics: e.target.value})}
                rows={2}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Work Summary *</Label>
              <Textarea
                placeholder="Summarize the work done..."
                value={stopTimerData.work_summary}
                onChange={(e) => setStopTimerData({...stopTimerData, work_summary: e.target.value})}
                rows={3}
              />
            </div>
            
            <div className="space-y-2">
              <Label>Actions Taken</Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Add an action"
                  value={newAction}
                  onChange={(e) => setNewAction(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addActionToList()}
                />
                <Button type="button" variant="outline" onClick={addActionToList}>Add</Button>
              </div>
              {stopTimerData.actions_taken.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {stopTimerData.actions_taken.map((action, i) => (
                    <Badge 
                      key={i} 
                      variant="secondary" 
                      className="cursor-pointer" 
                      onClick={() => removeActionFromList(i)}
                    >
                      {action} ✕
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            
            <div className="space-y-2">
              <Label>Outcome</Label>
              <Select 
                value={stopTimerData.outcome} 
                onValueChange={(v) => setStopTimerData({...stopTimerData, outcome: v})}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="parts_needed">Parts Needed</SelectItem>
                  <SelectItem value="followup_needed">Follow-up Needed</SelectItem>
                  <SelectItem value="escalated">Escalated</SelectItem>
                  <SelectItem value="unable_to_resolve">Unable to Resolve</SelectItem>
                </SelectContent>
              </Select>
            </div>
            
            <div className="space-y-2">
              <Label>Customer Name (Optional)</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Person who received service"
                  value={stopTimerData.customer_name}
                  onChange={(e) => setStopTimerData({...stopTimerData, customer_name: e.target.value})}
                  className="pl-10"
                />
              </div>
            </div>
            
            <div className="space-y-2">
              <Label>Internal Notes</Label>
              <Textarea
                placeholder="Any additional notes..."
                value={stopTimerData.notes}
                onChange={(e) => setStopTimerData({...stopTimerData, notes: e.target.value})}
                rows={2}
              />
            </div>
          </div>
          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setShowStopTimerModal(false)}>Cancel</Button>
            <Button 
              onClick={handleStopTimer} 
              disabled={actionLoading}
              className="bg-emerald-500 hover:bg-emerald-600"
            >
              {actionLoading ? 'Completing...' : 'Complete Visit'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Add Action Modal */}
      <Dialog open={showAddActionModal} onOpenChange={setShowAddActionModal}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Record Action</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Action Taken</Label>
              <Textarea
                placeholder="Describe the action taken..."
                value={actionToAdd}
                onChange={(e) => setActionToAdd(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowAddActionModal(false)}>Cancel</Button>
            <Button onClick={handleAddAction} disabled={actionLoading}>
              {actionLoading ? 'Adding...' : 'Add Action'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Request Parts Modal */}
      <Dialog open={showRequestPartsModal} onOpenChange={setShowRequestPartsModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Request Parts</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Item *</Label>
              <Select 
                value={partsRequestData.item_id} 
                onValueChange={(v) => setPartsRequestData({...partsRequestData, item_id: v})}
              >
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
              <div className="space-y-2">
                <Label>Quantity</Label>
                <Input
                  type="number"
                  min="1"
                  value={partsRequestData.quantity_requested}
                  onChange={(e) => setPartsRequestData({...partsRequestData, quantity_requested: parseInt(e.target.value) || 1})}
                />
              </div>
              <div className="space-y-2">
                <Label>Urgency</Label>
                <Select 
                  value={partsRequestData.urgency} 
                  onValueChange={(v) => setPartsRequestData({...partsRequestData, urgency: v})}
                >
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
            <div className="space-y-2">
              <Label>Notes</Label>
              <Textarea
                placeholder="Why do you need this part?"
                value={partsRequestData.request_notes}
                onChange={(e) => setPartsRequestData({...partsRequestData, request_notes: e.target.value})}
                rows={2}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRequestPartsModal(false)}>Cancel</Button>
            <Button onClick={handleRequestParts} disabled={actionLoading}>
              {actionLoading ? 'Requesting...' : 'Request Parts'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default TechnicianVisitDetail;
