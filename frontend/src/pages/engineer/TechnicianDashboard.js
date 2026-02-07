import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Wrench, LogOut, Clock, CheckCircle2, AlertCircle, 
  MapPin, ChevronRight, Play, Calendar, RefreshCw, 
  Package, Timer, User, Ticket, Check, X, Bell,
  FileText, Building2
} from 'lucide-react';
import { useEngineerAuth } from '../../context/EngineerAuthContext';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Textarea } from '../../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const TechnicianDashboard = () => {
  const navigate = useNavigate();
  const { engineer, token, logout, isAuthenticated } = useEngineerAuth();
  const [visits, setVisits] = useState([]);
  const [tickets, setTickets] = useState({
    pending_acceptance: [],
    accepted: [],
    in_progress: [],
    total: 0
  });
  const [stats, setStats] = useState({ 
    pending_acceptance: 0,
    scheduled: 0, 
    in_progress: 0, 
    completed: 0 
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('tickets');
  const [refreshing, setRefreshing] = useState(false);
  
  // Decline modal state
  const [showDeclineModal, setShowDeclineModal] = useState(false);
  const [declineTicket, setDeclineTicket] = useState(null);
  const [declineReason, setDeclineReason] = useState('');
  const [actionLoading, setActionLoading] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/engineer');
    }
  }, [isAuthenticated, navigate]);

  const fetchData = useCallback(async () => {
    if (!token || !engineer?.id) return;
    
    try {
      setRefreshing(true);
      
      // Fetch tickets and visits in parallel
      const [ticketsRes, visitsRes] = await Promise.all([
        axios.get(`${API}/api/engineer/my-tickets`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/api/engineer/my-visits`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      
      const ticketsData = ticketsRes.data || {};
      const visitsList = visitsRes.data || [];
      
      setTickets(ticketsData);
      setVisits(visitsList);
      
      // Calculate stats
      const scheduled = visitsList.filter(v => v.status === 'scheduled').length;
      const in_progress = visitsList.filter(v => ['in_progress', 'in_transit', 'on_site'].includes(v.status)).length;
      const completed = visitsList.filter(v => v.status === 'completed').length;
      
      setStats({ 
        pending_acceptance: ticketsData.pending_acceptance?.length || 0,
        scheduled, 
        in_progress, 
        completed 
      });
      
    } catch (err) {
      console.error('Failed to fetch data:', err);
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token, engineer?.id]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleLogout = () => {
    logout();
    navigate('/engineer');
  };

  const handleAcceptTicket = async (ticketId) => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/engineer/tickets/${ticketId}/accept`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Ticket accepted! Ready to start work.');
      fetchData();
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
        `${API}/api/engineer/tickets/${declineTicket.id}/decline`,
        { reason: declineReason },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Ticket declined. Admin will reassign.');
      setShowDeclineModal(false);
      setDeclineTicket(null);
      setDeclineReason('');
      fetchData();
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
      case 'scheduled': return 'bg-blue-50 text-blue-600 border-blue-200';
      case 'in_progress': return 'bg-amber-50 text-amber-600 border-amber-200';
      case 'pending_parts': return 'bg-orange-50 text-orange-600 border-orange-200';
      case 'completed': return 'bg-emerald-50 text-emerald-600 border-emerald-200';
      case 'cancelled': return 'bg-red-50 text-red-600 border-red-200';
      default: return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'pending_acceptance': return <Bell className="h-4 w-4" />;
      case 'assigned': return <Check className="h-4 w-4" />;
      case 'scheduled': return <Clock className="h-4 w-4" />;
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

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    if (timeStr.includes('T')) {
      const date = new Date(timeStr);
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    return timeStr;
  };

  const filteredVisits = visits.filter(v => {
    if (activeTab === 'pending') return v.status === 'scheduled' || v.status === 'in_progress';
    return v.status === 'completed';
  });

  const pendingCount = stats.scheduled + stats.in_progress;
  const completedCount = stats.completed;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div data-testid="technician-dashboard" className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 text-white sticky top-0 z-50">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center">
                <Wrench className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="font-semibold">{engineer?.name || 'Technician'}</p>
                <p className="text-xs text-slate-400">Service Engineer</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={fetchData}
                disabled={refreshing}
                className="text-slate-300 hover:text-white hover:bg-slate-700"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleLogout}
                className="text-slate-300 hover:text-white hover:bg-slate-700"
                data-testid="logout-btn"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Row */}
        <div className="px-4 pb-4">
          <div className="grid grid-cols-4 gap-2">
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-purple-400">{stats.pending_acceptance}</p>
              <p className="text-xs text-slate-400">New Jobs</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-blue-400">{stats.scheduled}</p>
              <p className="text-xs text-slate-400">Scheduled</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-amber-400">{stats.in_progress}</p>
              <p className="text-xs text-slate-400">In Progress</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-xl font-bold text-emerald-400">{stats.completed}</p>
              <p className="text-xs text-slate-400">Completed</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-t border-slate-700">
          <button
            onClick={() => setActiveTab('tickets')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === 'tickets' 
                ? 'text-blue-400 border-b-2 border-blue-400' 
                : 'text-slate-400 hover:text-white'
            }`}
            data-testid="tickets-tab"
          >
            Tickets {stats.pending_acceptance > 0 && (
              <span className="ml-1 bg-purple-500 text-white text-xs px-1.5 py-0.5 rounded-full">
                {stats.pending_acceptance}
              </span>
            )}
          </button>
          <button
            onClick={() => setActiveTab('pending')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === 'pending' 
                ? 'text-blue-400 border-b-2 border-blue-400' 
                : 'text-slate-400 hover:text-white'
            }`}
            data-testid="pending-tab"
          >
            Visits ({pendingCount})
          </button>
          <button
            onClick={() => setActiveTab('completed')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === 'completed' 
                ? 'text-blue-400 border-b-2 border-blue-400' 
                : 'text-slate-400 hover:text-white'
            }`}
            data-testid="completed-tab"
          >
            Done ({completedCount})
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="p-4 pb-20">
        {/* Tickets Tab - Shows pending acceptance + assigned tickets */}
        {activeTab === 'tickets' && (
          <>
            {/* Pending Acceptance Section */}
            {tickets.pending_acceptance?.length > 0 && (
              <div className="mb-6">
                <h2 className="text-sm font-semibold text-purple-700 mb-3 flex items-center gap-2">
                  <Bell className="h-4 w-4" />
                  New Job Assignments - Action Required
                </h2>
                <div className="space-y-3">
                  {tickets.pending_acceptance.map((ticket) => (
                    <Card 
                      key={ticket.id} 
                      className="overflow-hidden border-l-4 border-l-purple-500"
                      data-testid={`pending-ticket-${ticket.id}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div>
                            <div className="flex items-center gap-2 mb-1">
                              <span className="font-mono text-sm text-blue-600 font-semibold">
                                #{ticket.ticket_number}
                              </span>
                              <Badge className={getPriorityColor(ticket.priority)}>
                                {ticket.priority}
                              </Badge>
                              {ticket.is_urgent && (
                                <Badge variant="destructive" className="text-xs">Urgent</Badge>
                              )}
                            </div>
                            <p className="font-medium text-slate-900">{ticket.title}</p>
                          </div>
                        </div>
                        
                        <div className="space-y-1 text-sm text-slate-600 mb-4">
                          <div className="flex items-center gap-2">
                            <Building2 className="h-4 w-4 text-slate-400" />
                            <span>{ticket.company_name}</span>
                          </div>
                          {ticket.location?.address && (
                            <div className="flex items-center gap-2">
                              <MapPin className="h-4 w-4 text-slate-400" />
                              <span className="line-clamp-1">{ticket.location.address}</span>
                            </div>
                          )}
                          {ticket.device_name && (
                            <div className="flex items-center gap-2">
                              <FileText className="h-4 w-4 text-slate-400" />
                              <span>{ticket.device_name}</span>
                            </div>
                          )}
                        </div>

                        <div className="flex gap-2">
                          <Button 
                            className="flex-1 bg-emerald-500 hover:bg-emerald-600"
                            onClick={() => handleAcceptTicket(ticket.id)}
                            disabled={actionLoading}
                            data-testid={`accept-btn-${ticket.id}`}
                          >
                            <Check className="h-4 w-4 mr-2" />
                            Accept
                          </Button>
                          <Button 
                            variant="outline" 
                            className="flex-1 border-red-300 text-red-600 hover:bg-red-50"
                            onClick={() => {
                              setDeclineTicket(ticket);
                              setShowDeclineModal(true);
                            }}
                            disabled={actionLoading}
                            data-testid={`decline-btn-${ticket.id}`}
                          >
                            <X className="h-4 w-4 mr-2" />
                            Decline
                          </Button>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Accepted/Assigned Tickets */}
            {(tickets.accepted?.length > 0 || tickets.in_progress?.length > 0) && (
              <div>
                <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
                  <Ticket className="h-4 w-4" />
                  My Active Tickets
                </h2>
                <div className="space-y-3">
                  {[...tickets.accepted, ...tickets.in_progress].map((ticket) => (
                    <Card 
                      key={ticket.id} 
                      className="overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
                      onClick={() => navigate(`/engineer/ticket/${ticket.id}`)}
                      data-testid={`ticket-card-${ticket.id}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <Badge className={`${getStatusColor(ticket.status)} border`}>
                              {getStatusIcon(ticket.status)}
                              <span className="ml-1 capitalize">{ticket.status?.replace('_', ' ')}</span>
                            </Badge>
                            <Badge className={getPriorityColor(ticket.priority)}>
                              {ticket.priority}
                            </Badge>
                          </div>
                          <ChevronRight className="h-5 w-5 text-slate-400" />
                        </div>
                        
                        <p className="font-mono text-sm text-blue-600 font-semibold">
                          #{ticket.ticket_number}
                        </p>
                        <p className="font-medium text-slate-900 mt-1">{ticket.title}</p>
                        <p className="text-sm text-slate-600 mt-1">{ticket.company_name}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Empty State */}
            {tickets.pending_acceptance?.length === 0 && 
             tickets.accepted?.length === 0 && 
             tickets.in_progress?.length === 0 && (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Ticket className="h-8 w-8 text-slate-400" />
                </div>
                <p className="text-slate-500 mb-2">No active tickets</p>
                <p className="text-slate-400 text-sm">
                  New assignments will appear here
                </p>
              </div>
            )}
          </>
        )}

        {/* Visits Tab - Shows scheduled and in-progress visits */}
        {activeTab === 'pending' && (
          <>
            {filteredVisits.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Clock className="h-8 w-8 text-slate-400" />
                </div>
                <p className="text-slate-500 mb-2">No pending visits</p>
                <p className="text-slate-400 text-sm">
                  Scheduled visits will appear here
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredVisits.map((visit) => (
                  <Card 
                    key={visit.id} 
                    className="overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => navigate(`/engineer/visit/${visit.id}`)}
                    data-testid={`visit-card-${visit.id}`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-2">
                          <Badge className={`${getStatusColor(visit.status)} border`}>
                            {getStatusIcon(visit.status)}
                            <span className="ml-1 capitalize">{visit.status?.replace('_', ' ')}</span>
                          </Badge>
                          {visit.is_urgent && (
                            <Badge variant="destructive" className="text-xs">Urgent</Badge>
                          )}
                        </div>
                        <ChevronRight className="h-5 w-5 text-slate-400" />
                      </div>

                      <div className="mb-3">
                        <p className="font-medium text-slate-900 text-sm flex items-center gap-2">
                          <span className="font-mono text-blue-600">#{visit.ticket_number}</span>
                          <span className="text-slate-400">•</span>
                          <span>Visit #{visit.visit_number}</span>
                        </p>
                        {visit.purpose && (
                          <p className="text-slate-600 text-sm line-clamp-1 mt-1">{visit.purpose}</p>
                        )}
                      </div>

                      {visit.scheduled_date && (
                        <div className="flex items-center gap-2 text-sm text-slate-600 mb-2">
                          <Calendar className="h-4 w-4 text-slate-400" />
                          <span>{formatDate(visit.scheduled_date)}</span>
                          {visit.scheduled_time_from && (
                            <>
                              <span className="text-slate-400">•</span>
                              <span>{visit.scheduled_time_from} - {visit.scheduled_time_to || 'TBD'}</span>
                            </>
                          )}
                        </div>
                      )}

                      {visit.visit_location && (
                        <div className="flex items-center gap-2 text-sm text-slate-500">
                          <MapPin className="h-4 w-4 text-slate-400" />
                          <span className="line-clamp-1">{visit.visit_location}</span>
                        </div>
                      )}

                      {visit.status === 'in_progress' && visit.start_time && (
                        <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-amber-600">
                          <Play className="h-3 w-3" />
                          <span>Started at {formatTime(visit.start_time)}</span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}

        {/* Completed Tab */}
        {activeTab === 'completed' && (
          <>
            {filteredVisits.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <CheckCircle2 className="h-8 w-8 text-slate-400" />
                </div>
                <p className="text-slate-500 mb-2">No completed visits</p>
                <p className="text-slate-400 text-sm">
                  Completed visits will be shown here
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredVisits.map((visit) => (
                  <Card 
                    key={visit.id} 
                    className="overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
                    onClick={() => navigate(`/engineer/visit/${visit.id}`)}
                    data-testid={`visit-card-${visit.id}`}
                  >
                    <CardContent className="p-4">
                      <div className="flex items-start justify-between mb-3">
                        <Badge className={`${getStatusColor(visit.status)} border`}>
                          {getStatusIcon(visit.status)}
                          <span className="ml-1 capitalize">{visit.status?.replace('_', ' ')}</span>
                        </Badge>
                        <ChevronRight className="h-5 w-5 text-slate-400" />
                      </div>

                      <div className="mb-3">
                        <p className="font-medium text-slate-900 text-sm flex items-center gap-2">
                          <span className="font-mono text-blue-600">#{visit.ticket_number}</span>
                          <span className="text-slate-400">•</span>
                          <span>Visit #{visit.visit_number}</span>
                        </p>
                      </div>

                      {visit.duration_minutes > 0 && (
                        <div className="flex items-center gap-2 text-sm text-slate-600 mb-2">
                          <Timer className="h-4 w-4 text-slate-400" />
                          <span>{visit.duration_minutes} minutes</span>
                        </div>
                      )}

                      {visit.start_time && visit.end_time && (
                        <div className="flex items-center gap-4 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <Play className="h-3 w-3" />
                            {formatTime(visit.start_time)}
                          </span>
                          <span className="flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            {formatTime(visit.end_time)}
                          </span>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </>
        )}
      </main>

      {/* Floating Action - Today's Summary */}
      {activeTab === 'pending' && pendingCount > 0 && (
        <div className="fixed bottom-4 left-4 right-4">
          <div className="bg-slate-900 text-white rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Today's Workload</p>
                <p className="text-lg font-semibold">{pendingCount} visits pending</p>
              </div>
              <Button 
                onClick={fetchData}
                variant="secondary"
                size="sm"
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Decline Modal */}
      <Dialog open={showDeclineModal} onOpenChange={setShowDeclineModal}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Decline Assignment</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            {declineTicket && (
              <div className="bg-slate-50 rounded-lg p-3">
                <p className="font-mono text-sm text-blue-600">#{declineTicket.ticket_number}</p>
                <p className="font-medium text-sm mt-1">{declineTicket.title}</p>
              </div>
            )}
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
                setDeclineTicket(null);
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

export default TechnicianDashboard;
