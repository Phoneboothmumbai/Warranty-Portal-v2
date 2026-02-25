import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Clock, MessageSquare, CheckCircle, ChevronRight } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CompanyTicketDetailV2() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [sending, setSending] = useState(false);

  const fetchTicket = async () => {
    const token = localStorage.getItem('company_token');
    try {
      const res = await fetch(`${API}/api/ticketing/tickets/${ticketId}`, { headers: { Authorization: `Bearer ${token}` } });
      if (res.ok) setTicket(await res.json());
      else toast.error('Ticket not found');
    } catch { toast.error('Failed to load'); }
    finally { setLoading(false); }
  };

  useEffect(() => { fetchTicket(); }, [ticketId]);

  const handleComment = async () => {
    if (!comment.trim()) return;
    setSending(true);
    const token = localStorage.getItem('company_token');
    try {
      await fetch(`${API}/api/ticketing/tickets/${ticketId}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ content: comment }),
      });
      setComment('');
      fetchTicket();
    } catch { toast.error('Failed'); }
    finally { setSending(false); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!ticket) return <div className="flex items-center justify-center h-64 text-slate-400">Ticket not found</div>;

  const timeline = [...(ticket.timeline || [])].filter(e => !e.is_internal).reverse();

  return (
    <div className="space-y-6" data-testid="company-ticket-detail">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/company/tickets')}>
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <div>
          <h1 className="text-xl font-bold">#{ticket.ticket_number}</h1>
          <p className="text-sm text-slate-500">{ticket.subject}</p>
        </div>
        <span className={`ml-auto text-xs px-2 py-0.5 rounded-full ${ticket.is_open ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'}`}>
          {ticket.current_stage_name || 'New'}
        </span>
      </div>

      {ticket.workflow?.stages?.length > 0 && (
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-1 overflow-x-auto">
            {[...ticket.workflow.stages].sort((a, b) => a.order - b.order).map((stage, i) => {
              const isCurrent = stage.id === ticket.current_stage_id;
              const currentIdx = ticket.workflow.stages.findIndex(s => s.id === ticket.current_stage_id);
              const isPast = i < currentIdx;
              return (
                <div key={stage.id} className="flex items-center shrink-0">
                  <div className={`px-3 py-1 rounded-full text-xs font-medium border ${isCurrent ? 'bg-blue-500 text-white border-blue-500' : isPast ? 'bg-green-50 text-green-600 border-green-200' : 'bg-slate-50 text-slate-400 border-slate-200'}`}>
                    {isPast && <CheckCircle className="w-3 h-3 inline mr-1" />}
                    {stage.name}
                  </div>
                  {i < ticket.workflow.stages.length - 1 && <ChevronRight className="w-4 h-4 text-slate-300 mx-0.5" />}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-4">
          {ticket.description && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold mb-2">Description</h3>
              <p className="text-sm text-slate-600 whitespace-pre-wrap">{ticket.description}</p>
            </div>
          )}

          <div className="bg-white border rounded-lg p-4" data-testid="activity">
            <h3 className="text-sm font-semibold mb-3">Activity</h3>
            <div className="space-y-3">
              {timeline.map(entry => (
                <div key={entry.id} className="flex gap-3 py-2 border-b last:border-0">
                  <MessageSquare className="w-4 h-4 text-slate-400 mt-0.5 shrink-0" />
                  <div>
                    <p className="text-sm text-slate-700">{entry.description}</p>
                    <p className="text-xs text-slate-400 mt-0.5">{entry.user_name} - {entry.created_at ? new Date(entry.created_at).toLocaleString() : ''}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-sm font-semibold mb-2">Add Message</h3>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm min-h-[80px] mb-2" value={comment} onChange={e => setComment(e.target.value)} placeholder="Type your message..." data-testid="comment-input" />
            <Button size="sm" onClick={handleComment} disabled={sending || !comment.trim()} data-testid="send-btn">
              {sending ? 'Sending...' : 'Send'}
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-sm font-semibold mb-3">Details</h3>
            <div className="space-y-2 text-sm">
              <div><span className="text-slate-400 text-xs block">Help Topic</span>{ticket.help_topic_name}</div>
              <div><span className="text-slate-400 text-xs block">Priority</span><span className="capitalize">{ticket.priority_name}</span></div>
              <div><span className="text-slate-400 text-xs block">Created</span>{ticket.created_at ? new Date(ticket.created_at).toLocaleString() : '-'}</div>
              {ticket.assigned_team_name && <div><span className="text-slate-400 text-xs block">Team</span>{ticket.assigned_team_name}</div>}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
