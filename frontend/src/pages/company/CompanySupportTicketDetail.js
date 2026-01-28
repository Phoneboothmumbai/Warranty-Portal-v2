import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { useParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, Send, Clock, User, MessageSquare, 
  CheckCircle2, RefreshCw, Tag, AlertCircle
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_CONFIG = {
  open: { label: 'Open', color: 'bg-blue-100 text-blue-700 border-blue-200', description: 'Your ticket is being reviewed' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700 border-amber-200', description: 'A technician is working on your issue' },
  waiting_on_customer: { label: 'Awaiting Your Reply', color: 'bg-purple-100 text-purple-700 border-purple-200', description: 'We need more information from you' },
  waiting_on_third_party: { label: 'In Progress', color: 'bg-orange-100 text-orange-700 border-orange-200', description: 'Waiting for a vendor response' },
  on_hold: { label: 'On Hold', color: 'bg-slate-100 text-slate-600 border-slate-200', description: 'Temporarily paused' },
  resolved: { label: 'Resolved', color: 'bg-emerald-100 text-emerald-700 border-emerald-200', description: 'Your issue has been resolved' },
  closed: { label: 'Closed', color: 'bg-slate-200 text-slate-500 border-slate-300', description: 'This ticket is closed' }
};

const PRIORITY_CONFIG = {
  low: { label: 'Low', color: 'bg-slate-100 text-slate-600' },
  medium: { label: 'Medium', color: 'bg-blue-100 text-blue-700' },
  high: { label: 'High', color: 'bg-orange-100 text-orange-700' },
  critical: { label: 'Critical', color: 'bg-red-100 text-red-700' }
};

export default function CompanySupportTicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const { token, user } = useCompanyAuth();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Reply form
  const [replyContent, setReplyContent] = useState('');
  const [sending, setSending] = useState(false);
  const threadEndRef = useRef(null);

  const fetchTicket = useCallback(async () => {
    try {
      const res = await axios.get(`${API}/ticketing/portal/tickets/${ticketId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setTicket(res.data);
    } catch (error) {
      toast.error('Failed to load ticket');
      navigate('/company/support-tickets');
    } finally {
      setLoading(false);
    }
  }, [ticketId, token, navigate]);

  useEffect(() => {
    fetchTicket();
  }, [fetchTicket]);

  useEffect(() => {
    if (threadEndRef.current) {
      threadEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [ticket?.thread]);

  const handleSendReply = async (e) => {
    e.preventDefault();
    if (!replyContent.trim()) return;
    
    setSending(true);
    try {
      await axios.post(
        `${API}/ticketing/portal/tickets/${ticketId}/reply`,
        { content: replyContent },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Reply sent');
      setReplyContent('');
      fetchTicket();
    } catch (error) {
      toast.error('Failed to send reply');
    } finally {
      setSending(false);
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
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-slate-400" />
      </div>
    );
  }

  if (!ticket) return null;

  const statusConfig = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.open;
  const priorityConfig = PRIORITY_CONFIG[ticket.priority] || PRIORITY_CONFIG.medium;
  const isClosed = ['resolved', 'closed'].includes(ticket.status);
  const needsReply = ticket.status === 'waiting_on_customer';

  return (
    <div data-testid="company-ticket-detail-page" className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-start gap-4">
        <button onClick={() => navigate('/company/support-tickets')} className="p-2 hover:bg-slate-100 rounded-lg">
          <ArrowLeft className="h-5 w-5 text-slate-600" />
        </button>
        <div className="flex-1">
          <div className="flex items-center gap-3 mb-1">
            <span className="text-sm text-slate-500 font-mono">{ticket.ticket_number}</span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium border ${statusConfig.color}`}>
              {statusConfig.label}
            </span>
            <span className={`px-2 py-1 rounded-full text-xs font-medium ${priorityConfig.color}`}>
              {priorityConfig.label}
            </span>
          </div>
          <h1 className="text-xl font-bold text-slate-900">{ticket.subject}</h1>
        </div>
      </div>

      {/* Status Banner */}
      {needsReply && (
        <div className="bg-purple-50 border border-purple-200 rounded-xl p-4 flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-purple-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-purple-900">Your reply is needed</p>
            <p className="text-sm text-purple-700">Our team has requested more information. Please reply below to continue.</p>
          </div>
        </div>
      )}

      {isClosed && (
        <div className="bg-slate-50 border border-slate-200 rounded-xl p-4 flex items-start gap-3">
          <CheckCircle2 className="h-5 w-5 text-emerald-600 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-medium text-slate-900">This ticket has been resolved</p>
            <p className="text-sm text-slate-600">If you need further assistance, please create a new ticket.</p>
          </div>
        </div>
      )}

      {/* Original Description */}
      <div className="bg-white rounded-xl border border-slate-200 p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="h-10 w-10 bg-blue-100 rounded-full flex items-center justify-center">
            <User className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <p className="font-medium text-slate-900">{ticket.requester_name || 'You'}</p>
            <p className="text-xs text-slate-500">{formatDateTime(ticket.created_at)}</p>
          </div>
        </div>
        <div className="prose prose-sm max-w-none text-slate-700 whitespace-pre-wrap">
          {ticket.description}
        </div>
        {ticket.tags?.length > 0 && (
          <div className="flex items-center gap-2 mt-4 pt-4 border-t border-slate-100">
            <Tag className="h-4 w-4 text-slate-400" />
            {ticket.tags.map((tag, i) => (
              <span key={i} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-xs">{tag}</span>
            ))}
          </div>
        )}
      </div>

      {/* Thread */}
      <div className="space-y-4">
        {ticket.thread?.filter(e => e.entry_type !== 'system_event').map((entry, index) => {
          const isCustomer = entry.entry_type === 'customer_message';
          
          return (
            <div
              key={entry.id || index}
              className={`rounded-xl border p-4 ${
                isCustomer 
                  ? 'bg-blue-50 border-blue-200 ml-8' 
                  : 'bg-white border-slate-200 mr-8'
              }`}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <div className={`h-8 w-8 rounded-full flex items-center justify-center ${
                    isCustomer ? 'bg-blue-100' : 'bg-slate-100'
                  }`}>
                    {isCustomer ? (
                      <User className="h-4 w-4 text-blue-600" />
                    ) : (
                      <MessageSquare className="h-4 w-4 text-slate-600" />
                    )}
                  </div>
                  <div>
                    <p className="font-medium text-slate-900 text-sm">
                      {isCustomer ? 'You' : 'Support Team'}
                    </p>
                  </div>
                </div>
                <span className="text-xs text-slate-500">{formatDateTime(entry.created_at)}</span>
              </div>
              <div className="text-sm text-slate-700 whitespace-pre-wrap">{entry.content}</div>
            </div>
          );
        })}
        <div ref={threadEndRef} />
      </div>

      {/* Reply Form */}
      {!isClosed && (
        <div className="bg-white rounded-xl border border-slate-200 p-4">
          <form onSubmit={handleSendReply}>
            <label className="text-sm font-medium text-slate-700 block mb-2">Your Reply</label>
            <textarea
              value={replyContent}
              onChange={(e) => setReplyContent(e.target.value)}
              placeholder="Type your message here..."
              rows={4}
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm resize-none mb-3"
            />
            <div className="flex justify-end">
              <Button type="submit" disabled={sending || !replyContent.trim()}>
                <Send className="h-4 w-4 mr-2" />
                {sending ? 'Sending...' : 'Send Reply'}
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Ticket Info Footer */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-slate-500 mb-1">Created</p>
            <p className="font-medium text-slate-900">{formatDateTime(ticket.created_at)}</p>
          </div>
          <div>
            <p className="text-slate-500 mb-1">Last Updated</p>
            <p className="font-medium text-slate-900">{formatDateTime(ticket.updated_at)}</p>
          </div>
          <div>
            <p className="text-slate-500 mb-1">Status</p>
            <p className="font-medium text-slate-900">{statusConfig.label}</p>
          </div>
          <div>
            <p className="text-slate-500 mb-1">Priority</p>
            <p className="font-medium text-slate-900 capitalize">{ticket.priority}</p>
          </div>
        </div>
      </div>
    </div>
  );
}
