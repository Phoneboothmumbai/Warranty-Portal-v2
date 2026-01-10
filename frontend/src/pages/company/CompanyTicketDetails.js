import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, Ticket, Clock, CheckCircle2, AlertCircle, Loader2,
  MessageSquare, Send, User, Calendar, Laptop
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyTicketDetails = () => {
  const { ticketId } = useParams();
  const { token, user } = useCompanyAuth();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    fetchTicket();
  }, [ticketId]);

  const fetchTicket = async () => {
    try {
      const response = await axios.get(`${API}/company/tickets/${ticketId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTicket(response.data);
    } catch (error) {
      toast.error('Failed to load ticket details');
      navigate('/company/tickets');
    } finally {
      setLoading(false);
    }
  };

  const handleAddComment = async (e) => {
    e.preventDefault();
    if (!comment.trim()) return;

    setSubmitting(true);
    try {
      await axios.post(`${API}/company/tickets/${ticketId}/comments`, 
        { comment: comment, attachments: [] },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Comment added');
      setComment('');
      fetchTicket();
    } catch (error) {
      toast.error('Failed to add comment');
    } finally {
      setSubmitting(false);
    }
  };

  const handleSyncFromOsTicket = async () => {
    if (!ticket?.osticket_id) {
      toast.info('This ticket is not linked to osTicket');
      return;
    }

    setSyncing(true);
    try {
      const response = await axios.post(`${API}/company/tickets/${ticketId}/sync`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data.changes && response.data.changes.length > 0) {
        toast.success(`Synced: ${response.data.changes.join(', ')}`);
      } else {
        toast.info('Already up to date');
      }
      
      // Update local ticket data
      if (response.data.ticket) {
        setTicket(response.data.ticket);
      } else {
        fetchTicket();
      }
    } catch (error) {
      const errorMsg = error.response?.data?.detail || 'Failed to sync ticket';
      // Show a more user-friendly message for common errors
      if (errorMsg.includes('does not support') || errorMsg.includes('plugin')) {
        toast.error('Sync not available. osTicket REST API plugin required.');
      } else if (errorMsg.includes('IP') || errorMsg.includes('denied')) {
        toast.error('Sync unavailable from this location.');
      } else {
        toast.error(errorMsg);
      }
    } finally {
      setSyncing(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'open': return <AlertCircle className="h-5 w-5" />;
      case 'in_progress': return <Loader2 className="h-5 w-5" />;
      case 'resolved': return <CheckCircle2 className="h-5 w-5" />;
      case 'closed': return <CheckCircle2 className="h-5 w-5" />;
      default: return <Clock className="h-5 w-5" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'open': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'in_progress': return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'resolved': return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'closed': return 'bg-slate-100 text-slate-600 border-slate-200';
      default: return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high': return 'bg-red-50 text-red-700 border-red-200';
      case 'medium': return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'low': return 'bg-slate-100 text-slate-600 border-slate-200';
      default: return 'bg-slate-100 text-slate-600 border-slate-200';
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!ticket) return null;

  return (
    <div className="space-y-6" data-testid="ticket-details-page">
      {/* Back Button */}
      <Link 
        to="/company/tickets" 
        className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Tickets
      </Link>

      {/* Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <span className="text-sm font-mono text-slate-500">{ticket.ticket_number}</span>
              <span className={`px-2 py-0.5 rounded text-xs font-medium border ${getPriorityColor(ticket.priority)}`}>
                {ticket.priority} priority
              </span>
              {ticket.osticket_id && (
                <span className="px-2 py-0.5 rounded text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200">
                  Ticket #{ticket.osticket_id}
                </span>
              )}
            </div>
            <h1 className="text-2xl font-bold text-slate-900">{ticket.subject}</h1>
            <p className="text-slate-500 mt-2 flex items-center gap-2">
              <Calendar className="h-4 w-4" />
              Created {formatDate(ticket.created_at)}
              {ticket.last_synced_at && (
                <span className="text-xs text-slate-400 ml-2">
                  • Last synced: {formatDate(ticket.last_synced_at)}
                </span>
              )}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            {ticket.osticket_id && (
              <Button
                variant="outline"
                size="sm"
                onClick={handleSyncFromOsTicket}
                disabled={syncing}
                className="border-purple-200 text-purple-700 hover:bg-purple-50"
                data-testid="sync-osticket-btn"
              >
                <RefreshCw className={`h-4 w-4 mr-2 ${syncing ? 'animate-spin' : ''}`} />
                {syncing ? 'Syncing...' : 'Refresh Ticket'}
              </Button>
            )}
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border ${getStatusColor(ticket.status)}`}>
              {getStatusIcon(ticket.status)}
              {ticket.status?.replace('_', ' ')}
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4">Description</h2>
            <p className="text-slate-600 whitespace-pre-wrap">{ticket.description}</p>
          </div>

          {/* Comments */}
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <div className="px-6 py-4 border-b border-slate-100">
              <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-slate-400" />
                Comments ({ticket.comments?.length || 0})
              </h2>
            </div>
            
            <div className="divide-y divide-slate-100">
              {ticket.comments && ticket.comments.length > 0 ? (
                ticket.comments.map((c, index) => (
                  <div key={index} className="p-4">
                    <div className="flex items-start gap-3">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                        c.user_type === 'admin' ? 'bg-blue-100 text-blue-700' 
                        : c.user_type === 'osticket_staff' ? 'bg-purple-100 text-purple-700'
                        : 'bg-emerald-100 text-emerald-700'
                      }`}>
                        <User className="h-4 w-4" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className="font-medium text-slate-900">{c.user_name}</span>
                          {c.user_type === 'admin' && (
                            <span className="px-1.5 py-0.5 bg-blue-50 text-blue-700 text-xs rounded">Admin</span>
                          )}
                          {c.user_type === 'osticket_staff' && (
                            <span className="px-1.5 py-0.5 bg-purple-50 text-purple-700 text-xs rounded">osTicket</span>
                          )}
                          <span className="text-xs text-slate-400">{formatDate(c.created_at)}</span>
                          {c.source === 'osticket_sync' && (
                            <span className="text-xs text-purple-500">(synced)</span>
                          )}
                        </div>
                        <p className="text-slate-600 mt-1 whitespace-pre-wrap">{c.content || c.comment}</p>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="p-8 text-center">
                  <MessageSquare className="h-10 w-10 text-slate-200 mx-auto mb-2" />
                  <p className="text-slate-500">No comments yet</p>
                </div>
              )}
            </div>

            {/* Add Comment Form */}
            {ticket.status !== 'closed' && (
              <form onSubmit={handleAddComment} className="p-4 border-t border-slate-100 bg-slate-50">
                <div className="flex gap-3">
                  <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center flex-shrink-0">
                    <User className="h-4 w-4" />
                  </div>
                  <div className="flex-1">
                    <textarea
                      value={comment}
                      onChange={(e) => setComment(e.target.value)}
                      placeholder="Add a comment..."
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500 resize-none h-20"
                      data-testid="comment-input"
                    />
                    <div className="flex justify-end mt-2">
                      <Button
                        type="submit"
                        disabled={submitting || !comment.trim()}
                        className="bg-emerald-600 hover:bg-emerald-700"
                        data-testid="submit-comment-btn"
                      >
                        {submitting ? (
                          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                        ) : (
                          <>
                            <Send className="h-4 w-4 mr-2" />
                            Send
                          </>
                        )}
                      </Button>
                    </div>
                  </div>
                </div>
              </form>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Device Info */}
          {ticket.device && (
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="text-sm font-semibold text-slate-900 mb-4 flex items-center gap-2">
                <Laptop className="h-4 w-4 text-slate-400" />
                Related Device
              </h3>
              <Link 
                to={`/company/devices/${ticket.device.id}`}
                className="block p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
              >
                <p className="font-medium text-slate-900">{ticket.device.serial_number}</p>
                <p className="text-sm text-slate-500 mt-0.5">
                  {ticket.device.brand} {ticket.device.model}
                </p>
              </Link>
            </div>
          )}

          {/* Ticket Details */}
          <div className="bg-white rounded-xl border border-slate-200 p-6">
            <h3 className="text-sm font-semibold text-slate-900 mb-4">Ticket Details</h3>
            <dl className="space-y-3 text-sm">
              <div className="flex justify-between">
                <dt className="text-slate-500">Ticket ID</dt>
                <dd className="font-mono text-slate-900">{ticket.ticket_number}</dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Status</dt>
                <dd className={`px-2 py-0.5 rounded text-xs font-medium ${getStatusColor(ticket.status)}`}>
                  {ticket.status?.replace('_', ' ')}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Priority</dt>
                <dd className={`px-2 py-0.5 rounded text-xs font-medium ${getPriorityColor(ticket.priority)}`}>
                  {ticket.priority}
                </dd>
              </div>
              <div className="flex justify-between">
                <dt className="text-slate-500">Created</dt>
                <dd className="text-slate-900">{formatDate(ticket.created_at)}</dd>
              </div>
              {ticket.updated_at && (
                <div className="flex justify-between">
                  <dt className="text-slate-500">Last Updated</dt>
                  <dd className="text-slate-900">{formatDate(ticket.updated_at)}</dd>
                </div>
              )}
              {ticket.resolved_at && (
                <div className="flex justify-between">
                  <dt className="text-slate-500">Resolved</dt>
                  <dd className="text-slate-900">{formatDate(ticket.resolved_at)}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CompanyTicketDetails;
