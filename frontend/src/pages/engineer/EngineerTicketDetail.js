import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, MapPin, Phone, Building2, Clock, 
  CheckCircle2, AlertCircle, Play, User, Package,
  Calendar, FileText, Wrench, Timer, Send, Bell,
  Check, X, Truck, Shield, Clipboard, GitBranch, Home
} from 'lucide-react';
import { useEngineerAuth } from '../../context/EngineerAuthContext';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Textarea } from '../../components/ui/textarea';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
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

const EngineerTicketDetail = () => {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const { token, isAuthenticated, engineer } = useEngineerAuth();
  
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Modal states
  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [declineReason, setDeclineReason] = useState('');

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/engineer');
    }
  }, [isAuthenticated, navigate]);

  // Fetch ticket details
  const fetchTicketDetails = useCallback(async () => {
    if (!token) return;
    
    try {
      const response = await axios.get(`${API}/api/engineer/tickets/${ticketId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTicket(response.data);
    } catch (err) {
      console.error('Failed to fetch ticket:', err);
      toast.error('Failed to load ticket details');
      navigate('/engineer/dashboard');
    } finally {
      setLoading(false);
    }
  }, [ticketId, token, navigate]);

  useEffect(() => {
    fetchTicketDetails();
  }, [fetchTicketDetails]);

  const handleAcceptTicket = async () => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/engineer/tickets/${ticketId}/accept`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Ticket accepted! Ready to start work.');
      fetchTicketDetails();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to accept ticket');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeclineTicket = async () => {
    if (!declineReason.trim()) {
      toast.error('Please provide a reason for declining');
      return;
    }
    
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/engineer/tickets/${ticketId}/decline`,
        { reason: declineReason },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Ticket declined. Admin will reassign.');
      navigate('/engineer/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to decline ticket');
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending_acceptance': return 'bg-purple-50 text-purple-600 border-purple-200';
      case 'assigned': return 'bg-blue-50 text-blue-600 border-blue-200';
      case 'in_progress': return 'bg-amber-50 text-amber-600 border-amber-200';
      case 'pending_parts': return 'bg-orange-50 text-orange-600 border-orange-200';
      case 'completed': return 'bg-emerald-50 text-emerald-600 border-emerald-200';
      default: return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending_acceptance': return <Bell className="h-4 w-4" />;
      case 'assigned': return <Check className="h-4 w-4" />;
      case 'in_progress': return <Play className="h-4 w-4" />;
      case 'pending_parts': return <Package className="h-4 w-4" />;
      case 'completed': return <CheckCircle2 className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-500 text-white';
      case 'high': return 'bg-orange-500 text-white';
      case 'medium': return 'bg-yellow-500 text-white';
      case 'low': return 'bg-slate-400 text-white';
      default: return 'bg-slate-400 text-white';
    }
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

  if (!ticket) return null;

  const isPendingAcceptance = ticket.status === 'pending_acceptance';
  const isAssigned = ticket.status === 'assigned';
  const isInProgress = ticket.status === 'in_progress';
  const isPendingParts = ticket.status === 'pending_parts';
  const isCompleted = ticket.status === 'completed';

  return (
    <div data-testid="engineer-ticket-detail" className="min-h-screen bg-slate-50 pb-32">
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
                <span className="font-mono text-blue-300">#{ticket.ticket_number}</span>
              </p>
              <p className="text-xs text-slate-400">{ticket.company_name}</p>
            </div>
          </div>
        </div>

        {/* Pending Acceptance Banner */}
        {isPendingAcceptance && (
          <div className="px-4 pb-4">
            <div className="bg-purple-500/20 border border-purple-500/30 rounded-xl p-4">
              <div className="flex items-center gap-3 mb-3">
                <Bell className="h-5 w-5 text-purple-400" />
                <p className="text-purple-200 font-medium">New Assignment - Action Required</p>
              </div>
              <div className="flex gap-2">
                <Button 
                  className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                  onClick={handleAcceptTicket}
                  disabled={actionLoading}
                  data-testid="accept-ticket-btn"
                >
                  <Check className="h-4 w-4 mr-2" />
                  Accept Job
                </Button>
                <Button 
                  variant="outline" 
                  className="flex-1 border-red-400 text-red-400 hover:bg-red-500/20"
                  onClick={() => setShowDeclineModal(true)}
                  disabled={actionLoading}
                  data-testid="decline-ticket-btn"
                >
                  <X className="h-4 w-4 mr-2" />
                  Decline
                </Button>
              </div>
            </div>
          </div>
        )}
      </header>

      <main className="p-4 space-y-4">
        {/* Status Card */}
        <Card className={`border-l-4 ${
          isPendingAcceptance ? 'border-l-purple-500' :
          isAssigned ? 'border-l-blue-500' : 
          isInProgress ? 'border-l-amber-500' : 
          isPendingParts ? 'border-l-orange-500' :
          'border-l-emerald-500'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Badge className={`${getStatusColor(ticket.status)} border`}>
                  {getStatusIcon(ticket.status)}
                  <span className="ml-1 capitalize">{ticket.status?.replace('_', ' ')}</span>
                </Badge>
                <Badge className={getPriorityColor(ticket.priority)}>
                  {ticket.priority}
                </Badge>
                {ticket.is_urgent && (
                  <Badge variant="destructive">Urgent</Badge>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Title & Description */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <FileText className="h-4 w-4" />
              Issue Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <p className="font-medium text-slate-900">{ticket.title}</p>
              {ticket.description && (
                <p className="text-sm text-slate-600 mt-2">{ticket.description}</p>
              )}
            </div>
            {ticket.problem_name && (
              <div className="flex justify-between items-center text-sm">
                <span className="text-slate-500">Problem Type</span>
                <span>{ticket.problem_name}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Customer Info */}
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
                  <a 
                    href={`tel:${ticket.contact.phone}`}
                    className="flex items-center gap-2 text-blue-600"
                  >
                    <Phone className="h-4 w-4" />
                    {ticket.contact.phone}
                  </a>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Location */}
        {ticket.location && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Location
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700">
                {ticket.location.site_name && <span className="font-medium">{ticket.location.site_name}<br /></span>}
                {ticket.location.address}
                {ticket.location.city && `, ${ticket.location.city}`}
              </p>
            </CardContent>
          </Card>
        )}

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
              {ticket.asset_tag && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Asset Tag</span>
                  <span>{ticket.asset_tag}</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Quotation Info (if pending parts) */}
        {isPendingParts && ticket.quotation && (
          <Card className="border-orange-200">
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2 text-orange-700">
                <Package className="h-4 w-4" />
                Quotation Status
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Quotation #</span>
                <span className="font-mono">{ticket.quotation.quotation_number}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Status</span>
                <Badge variant="outline" className="capitalize">
                  {ticket.quotation.status}
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Amount</span>
                <span className="font-medium">₹{ticket.quotation.total_amount?.toFixed(2)}</span>
              </div>
              {ticket.quotation.status === 'approved' && (
                <p className="text-emerald-600 text-xs mt-2">
                  Quotation approved - You can proceed with the work
                </p>
              )}
            </CardContent>
          </Card>
        )}

        {/* Visits */}
        {ticket.visits?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                My Visits ({ticket.visits.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {ticket.visits.map((visit) => (
                  <div 
                    key={visit.id}
                    className="border border-slate-200 rounded-lg p-3 cursor-pointer hover:bg-slate-50"
                    onClick={() => navigate(`/engineer/visit/${visit.id}`)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="font-medium text-sm">Visit #{visit.visit_number}</span>
                      <Badge variant="outline" className="capitalize text-xs">
                        {visit.status?.replace('_', ' ')}
                      </Badge>
                    </div>
                    {visit.scheduled_date && (
                      <p className="text-xs text-slate-500">
                        {visit.scheduled_date} {visit.scheduled_time_from && `at ${visit.scheduled_time_from}`}
                      </p>
                    )}
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Timeline */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Timer className="h-4 w-4" />
              Timeline
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-slate-500">Created</span>
              <span>{formatDateTime(ticket.created_at)}</span>
            </div>
            {ticket.assigned_at && (
              <div className="flex justify-between">
                <span className="text-slate-500">Assigned</span>
                <span>{formatDateTime(ticket.assigned_at)}</span>
              </div>
            )}
            {ticket.assignment_accepted_at && (
              <div className="flex justify-between">
                <span className="text-slate-500">Accepted</span>
                <span>{formatDateTime(ticket.assignment_accepted_at)}</span>
              </div>
            )}
            {ticket.resolved_at && (
              <div className="flex justify-between">
                <span className="text-slate-500">Resolved</span>
                <span>{formatDateTime(ticket.resolved_at)}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </main>

      {/* Bottom Action Button */}
      {isAssigned && ticket.visits?.length > 0 && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4">
          <Button 
            className="w-full bg-blue-500 hover:bg-blue-600 h-12"
            onClick={() => navigate(`/engineer/visit/${ticket.visits[0].id}`)}
          >
            <Play className="h-5 w-5 mr-2" />
            Go to Visit
          </Button>
        </div>
      )}

      {/* Decline Modal */}
      <Dialog open={showDeclineModal} onOpenChange={setShowDeclineModal}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Decline Assignment</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="bg-slate-50 rounded-lg p-3">
              <p className="font-mono text-sm text-blue-600">#{ticket.ticket_number}</p>
              <p className="font-medium text-sm mt-1">{ticket.title}</p>
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">
                Reason for declining *
              </label>
              <Textarea
                placeholder="Please provide a reason..."
                value={declineReason}
                onChange={(e) => setDeclineReason(e.target.value)}
                rows={3}
              />
            </div>
          </div>
          <DialogFooter>
            <Button 
              variant="outline" 
              onClick={() => {
                setShowDeclineModal(false);
                setDeclineReason('');
              }}
            >
              Cancel
            </Button>
            <Button 
              onClick={handleDeclineTicket}
              disabled={actionLoading || !declineReason.trim()}
              className="bg-red-500 hover:bg-red-600"
            >
              {actionLoading ? 'Declining...' : 'Decline'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EngineerTicketDetail;
