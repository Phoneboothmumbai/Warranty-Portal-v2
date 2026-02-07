import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Ticket, ArrowLeft, RefreshCw, Clock, User, Calendar, 
  Laptop, MapPin, Phone, Mail, FileText, CheckCircle2,
  AlertTriangle, Package, MessageSquare, Wrench, Building2
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { toast } from 'sonner';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  new: { label: 'New', color: 'bg-blue-100 text-blue-700 border-blue-300', icon: Ticket },
  pending_acceptance: { label: 'Pending Acceptance', color: 'bg-purple-100 text-purple-700 border-purple-300', icon: Clock },
  assigned: { label: 'Assigned', color: 'bg-indigo-100 text-indigo-700 border-indigo-300', icon: User },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700 border-amber-300', icon: Wrench },
  pending_parts: { label: 'Pending Parts', color: 'bg-orange-100 text-orange-700 border-orange-300', icon: Package },
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

const CompanyTicketDetail = () => {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const { token } = useCompanyAuth();
  
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);

  const headers = { Authorization: `Bearer ${token}` };

  const fetchTicket = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/api/company/service-tickets/${ticketId}`, { headers });
      setTicket(response.data);
    } catch (err) {
      console.error('Failed to fetch ticket:', err);
      toast.error('Failed to load ticket details');
      navigate('/company/tickets');
    } finally {
      setLoading(false);
    }
  }, [ticketId, token, navigate]);

  useEffect(() => {
    fetchTicket();
  }, [fetchTicket]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  const formatDateShort = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!ticket) return null;

  const statusConfig = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.new;
  const priorityConfig = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
  const StatusIcon = statusConfig.icon;

  return (
    <div data-testid="company-ticket-detail" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/company/tickets')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900 font-mono">#{ticket.ticket_number}</h1>
              <Badge className={`${statusConfig.color} border`}>
                <StatusIcon className="h-3 w-3 mr-1" />
                {statusConfig.label}
              </Badge>
              <Badge className={priorityConfig.color}>
                {priorityConfig.label}
              </Badge>
            </div>
            <p className="text-slate-500 text-sm mt-1">{ticket.title}</p>
          </div>
        </div>
        <Button variant="outline" onClick={fetchTicket}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* Status Banner */}
      {ticket.status === 'pending_parts' && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <Package className="h-5 w-5 text-orange-600" />
            <div>
              <p className="font-medium text-orange-900">Waiting for Parts</p>
              <p className="text-sm text-orange-700">
                This ticket is pending parts approval. Please check your quotations for any pending approvals.
              </p>
            </div>
            <Link to="/company/quotations" className="ml-auto">
              <Button size="sm" className="bg-orange-600 hover:bg-orange-700">
                View Quotations
              </Button>
            </Link>
          </div>
        </div>
      )}

      {ticket.status === 'completed' && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
            <div>
              <p className="font-medium text-emerald-900">Service Completed</p>
              <p className="text-sm text-emerald-700">
                The service work has been completed. Please review the resolution details below.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Workflow Progress */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-slate-700">Ticket Progress</span>
          </div>
          <div className="flex items-center gap-1">
            {[
              { key: 'new', label: 'Created' },
              { key: 'pending_acceptance', label: 'Assigned' },
              { key: 'assigned', label: 'Accepted' },
              { key: 'in_progress', label: 'Work Started' },
              { key: 'pending_parts', label: 'Parts', optional: true },
              { key: 'completed', label: 'Completed' },
              { key: 'closed', label: 'Closed' },
            ].map((step, idx, arr) => {
              const statusOrder = ['new', 'pending_acceptance', 'assigned', 'in_progress', 'pending_parts', 'completed', 'closed'];
              const currentIdx = statusOrder.indexOf(ticket.status);
              const stepIdx = statusOrder.indexOf(step.key);
              const isActive = step.key === ticket.status;
              const isPast = stepIdx < currentIdx;
              
              return (
                <React.Fragment key={step.key}>
                  <div 
                    className={`flex-1 h-2 rounded-full transition-all ${
                      isActive ? 'bg-emerald-500' :
                      isPast ? 'bg-emerald-300' :
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
        </CardContent>
      </Card>

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Main Info */}
        <div className="lg:col-span-2 space-y-6">
          <Tabs defaultValue="details">
            <TabsList>
              <TabsTrigger value="details">Details</TabsTrigger>
              <TabsTrigger value="visits">Visits ({ticket.visits?.length || 0})</TabsTrigger>
              <TabsTrigger value="history">History</TabsTrigger>
            </TabsList>

            <TabsContent value="details" className="mt-4 space-y-4">
              {/* Issue Description */}
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base flex items-center gap-2">
                    <FileText className="h-4 w-4" />
                    Issue Description
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-slate-700 whitespace-pre-wrap">
                    {ticket.description || 'No description provided.'}
                  </p>
                </CardContent>
              </Card>

              {/* Resolution (if completed) */}
              {(ticket.status === 'completed' || ticket.status === 'closed') && ticket.resolution_notes && (
                <Card className="border-emerald-200 bg-emerald-50">
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2 text-emerald-800">
                      <CheckCircle2 className="h-4 w-4" />
                      Resolution
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-emerald-800 whitespace-pre-wrap">
                      {ticket.resolution_notes}
                    </p>
                  </CardContent>
                </Card>
              )}

              {/* Diagnosis Notes */}
              {ticket.diagnosis_notes && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Wrench className="h-4 w-4" />
                      Engineer Diagnosis
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <p className="text-slate-700 whitespace-pre-wrap">
                      {ticket.diagnosis_notes}
                    </p>
                  </CardContent>
                </Card>
              )}
            </TabsContent>

            <TabsContent value="visits" className="mt-4">
              <Card>
                <CardContent className="p-0">
                  {ticket.visits?.length > 0 ? (
                    <div className="divide-y divide-slate-100">
                      {ticket.visits.map((visit, idx) => (
                        <div key={visit.id || idx} className="p-4">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <Badge variant="outline" className="text-xs">
                                Visit #{idx + 1}
                              </Badge>
                              <Badge className={
                                visit.status === 'completed' ? 'bg-emerald-100 text-emerald-700' :
                                visit.status === 'in_progress' ? 'bg-amber-100 text-amber-700' :
                                'bg-slate-100 text-slate-700'
                              }>
                                {visit.status}
                              </Badge>
                            </div>
                            <span className="text-xs text-slate-500">
                              {formatDate(visit.scheduled_date || visit.start_time)}
                            </span>
                          </div>
                          {visit.engineer_name && (
                            <p className="text-sm text-slate-600 flex items-center gap-1">
                              <User className="h-3 w-3" />
                              {visit.engineer_name}
                            </p>
                          )}
                          {visit.notes && (
                            <p className="text-sm text-slate-700 mt-2 bg-slate-50 p-2 rounded">
                              {visit.notes}
                            </p>
                          )}
                          {visit.duration_minutes && (
                            <p className="text-xs text-slate-500 mt-2">
                              Duration: {visit.duration_minutes} minutes
                            </p>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Clock className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                      <p className="text-slate-500 text-sm">No visits scheduled yet</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="history" className="mt-4">
              <Card>
                <CardContent className="p-0">
                  {ticket.status_history?.length > 0 ? (
                    <div className="divide-y divide-slate-100">
                      {[...ticket.status_history].reverse().map((change, idx) => (
                        <div key={idx} className="p-4 flex items-start gap-3">
                          <div className="w-2 h-2 rounded-full bg-emerald-500 mt-2" />
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <Badge variant="outline" className="text-xs">
                                {change.from_status || 'created'} → {change.to_status}
                              </Badge>
                              <span className="text-xs text-slate-500">
                                {formatDate(change.changed_at)}
                              </span>
                            </div>
                            {change.notes && (
                              <p className="text-sm text-slate-600">{change.notes}</p>
                            )}
                            {change.changed_by_name && (
                              <p className="text-xs text-slate-500 mt-1">
                                by {change.changed_by_name}
                              </p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-center py-8">
                      <Clock className="h-8 w-8 text-slate-300 mx-auto mb-2" />
                      <p className="text-slate-500 text-sm">No history available</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </div>

        {/* Right Column - Sidebar Info */}
        <div className="space-y-4">
          {/* Device Info */}
          {ticket.device_serial && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Laptop className="h-4 w-4" />
                  Device
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Serial</span>
                  <span className="font-mono font-medium">{ticket.device_serial}</span>
                </div>
                {ticket.device_brand && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Brand</span>
                    <span>{ticket.device_brand}</span>
                  </div>
                )}
                {ticket.device_model && (
                  <div className="flex justify-between">
                    <span className="text-slate-500">Model</span>
                    <span>{ticket.device_model}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Assignment Info */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <User className="h-4 w-4" />
                Assignment
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Assigned To</span>
                <span>{ticket.assigned_to_name || 'Not assigned'}</span>
              </div>
              {ticket.assigned_at && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Assigned On</span>
                  <span>{formatDateShort(ticket.assigned_at)}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Location */}
          {(ticket.site_name || ticket.site_address) && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  Location
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm">
                <p className="font-medium">{ticket.site_name}</p>
                {ticket.site_address && (
                  <p className="text-slate-500 text-xs mt-1">{ticket.site_address}</p>
                )}
              </CardContent>
            </Card>
          )}

          {/* Contact Info */}
          {(ticket.contact_name || ticket.contact_phone || ticket.contact_email) && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Phone className="h-4 w-4" />
                  Contact
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm">
                {ticket.contact_name && (
                  <div className="flex items-center gap-2">
                    <User className="h-3 w-3 text-slate-400" />
                    <span>{ticket.contact_name}</span>
                  </div>
                )}
                {ticket.contact_phone && (
                  <div className="flex items-center gap-2">
                    <Phone className="h-3 w-3 text-slate-400" />
                    <span>{ticket.contact_phone}</span>
                  </div>
                )}
                {ticket.contact_email && (
                  <div className="flex items-center gap-2">
                    <Mail className="h-3 w-3 text-slate-400" />
                    <span>{ticket.contact_email}</span>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Timeline */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span>{formatDateShort(ticket.created_at)}</span>
              </div>
              {ticket.completed_at && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Completed</span>
                  <span>{formatDateShort(ticket.completed_at)}</span>
                </div>
              )}
              {ticket.closed_at && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Closed</span>
                  <span>{formatDateShort(ticket.closed_at)}</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default CompanyTicketDetail;
