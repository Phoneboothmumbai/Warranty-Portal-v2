import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Clock, User, Building2, MessageSquare, CheckCircle, AlertTriangle,
  ChevronRight, Send, Lock, Tag, Edit2, Users
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const priorityColors = {
  low: 'bg-slate-100 text-slate-700 border-slate-200',
  medium: 'bg-blue-100 text-blue-700 border-blue-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
};

const stageTypeColors = {
  initial: '#3B82F6',
  in_progress: '#F59E0B',
  waiting: '#8B5CF6',
  terminal_success: '#10B981',
  terminal_failure: '#EF4444',
};

const WorkflowProgress = ({ workflow, currentStageId }) => {
  if (!workflow?.stages?.length) return null;
  const stages = [...workflow.stages].sort((a, b) => a.order - b.order);
  const currentIdx = stages.findIndex(s => s.id === currentStageId);

  return (
    <div className="bg-white border rounded-lg p-4" data-testid="workflow-progress">
      <h3 className="text-sm font-semibold text-slate-700 mb-3">Workflow: {workflow.name}</h3>
      <div className="flex items-center gap-1 overflow-x-auto pb-2">
        {stages.map((stage, i) => {
          const isCurrent = stage.id === currentStageId;
          const isPast = i < currentIdx;
          const color = stageTypeColors[stage.stage_type] || '#6B7280';
          return (
            <div key={stage.id} className="flex items-center shrink-0">
              <div
                className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${
                  isCurrent ? 'ring-2 ring-offset-1 shadow-sm' : isPast ? 'opacity-60' : 'opacity-40'
                }`}
                style={{
                  borderColor: color,
                  backgroundColor: isCurrent ? color : 'transparent',
                  color: isCurrent ? '#fff' : color,
                  ringColor: isCurrent ? color : undefined,
                }}
                data-testid={`stage-${stage.slug}`}
              >
                {isPast && <CheckCircle className="w-3 h-3" />}
                {stage.name}
              </div>
              {i < stages.length - 1 && <ChevronRight className="w-4 h-4 text-slate-300 mx-0.5 shrink-0" />}
            </div>
          );
        })}
      </div>
    </div>
  );
};

const TimelineEntry = ({ entry }) => {
  const icons = {
    ticket_created: <Clock className="w-4 h-4 text-blue-500" />,
    stage_change: <ChevronRight className="w-4 h-4 text-purple-500" />,
    comment: <MessageSquare className="w-4 h-4 text-slate-500" />,
    assignment: <User className="w-4 h-4 text-green-500" />,
    task_completed: <CheckCircle className="w-4 h-4 text-green-500" />,
  };

  return (
    <div className={`flex gap-3 py-3 ${entry.is_internal ? 'bg-amber-50/50 -mx-3 px-3 rounded' : ''}`} data-testid={`timeline-${entry.id}`}>
      <div className="mt-0.5">{icons[entry.type] || <Clock className="w-4 h-4 text-slate-400" />}</div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-slate-700">{entry.description}</p>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs text-slate-400">{entry.user_name || 'System'}</span>
          <span className="text-xs text-slate-300">|</span>
          <span className="text-xs text-slate-400">{entry.created_at ? new Date(entry.created_at).toLocaleString() : ''}</span>
          {entry.is_internal && <span className="text-xs bg-amber-200 text-amber-800 px-1.5 py-0.5 rounded flex items-center gap-1"><Lock className="w-3 h-3" /> Internal</span>}
        </div>
      </div>
    </div>
  );
};

const TaskCard = ({ task, onComplete }) => (
  <div className="border rounded-lg p-3 bg-white" data-testid={`task-${task.id}`}>
    <div className="flex items-center justify-between">
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${task.status === 'completed' ? 'bg-green-500' : task.status === 'in_progress' ? 'bg-yellow-500' : 'bg-slate-300'}`} />
        <span className="text-sm font-medium">{task.name}</span>
      </div>
      <span className={`text-xs px-2 py-0.5 rounded-full ${task.status === 'completed' ? 'bg-green-100 text-green-700' : task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-700' : 'bg-slate-100 text-slate-600'}`}>
        {task.status}
      </span>
    </div>
    {task.assigned_team_name && <p className="text-xs text-slate-400 mt-1 ml-4">Team: {task.assigned_team_name}</p>}
    {task.status === 'pending' && (
      <Button size="sm" variant="outline" className="mt-2 ml-4" onClick={() => onComplete(task.id)} data-testid={`complete-task-${task.id}`}>
        Mark Complete
      </Button>
    )}
  </div>
);

export default function ServiceTicketDetailV2() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [comment, setComment] = useState('');
  const [isInternal, setIsInternal] = useState(false);
  const [sending, setSending] = useState(false);
  const [teams, setTeams] = useState([]);
  const [showAssign, setShowAssign] = useState(false);
  const [assignTeamId, setAssignTeamId] = useState('');

  const fetchTicket = useCallback(async () => {
    const token = localStorage.getItem('admin_token');
    try {
      const res = await fetch(`${API}/api/ticketing/tickets/${ticketId}`, { headers: { Authorization: `Bearer ${token}` } });
      if (!res.ok) throw new Error('Not found');
      setTicket(await res.json());
    } catch { toast.error('Failed to load ticket'); }
    finally { setLoading(false); }
  }, [ticketId]);

  useEffect(() => {
    fetchTicket();
    const token = localStorage.getItem('admin_token');
    fetch(`${API}/api/ticketing/teams`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(data => setTeams(Array.isArray(data) ? data : []));
  }, [fetchTicket]);

  const handleComment = async () => {
    if (!comment.trim()) return;
    setSending(true);
    const token = localStorage.getItem('admin_token');
    try {
      await fetch(`${API}/api/ticketing/tickets/${ticketId}/comment`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ content: comment, is_internal: isInternal }),
      });
      setComment('');
      fetchTicket();
      toast.success('Comment added');
    } catch { toast.error('Failed to add comment'); }
    finally { setSending(false); }
  };

  const handleTransition = async (transitionId) => {
    const token = localStorage.getItem('admin_token');
    try {
      const res = await fetch(`${API}/api/ticketing/tickets/${ticketId}/transition`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ transition_id: transitionId }),
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      setTicket(await res.json());
      toast.success('Ticket updated');
    } catch (e) { toast.error(e.message); }
  };

  const handleAssign = async () => {
    if (!assignTeamId) return;
    const token = localStorage.getItem('admin_token');
    try {
      await fetch(`${API}/api/ticketing/tickets/${ticketId}/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ assigned_team_id: assignTeamId }),
      });
      fetchTicket();
      setShowAssign(false);
      toast.success('Team assigned');
    } catch { toast.error('Failed to assign'); }
  };

  const handleCompleteTask = async (taskId) => {
    const token = localStorage.getItem('admin_token');
    try {
      await fetch(`${API}/api/ticketing/tasks/${taskId}/complete`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${token}` },
        body: JSON.stringify({ notes: 'Completed' }),
      });
      fetchTicket();
      toast.success('Task completed');
    } catch { toast.error('Failed'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!ticket) return <div className="flex items-center justify-center h-64 text-slate-400">Ticket not found</div>;

  const currentStage = ticket.workflow?.stages?.find(s => s.id === ticket.current_stage_id);
  const transitions = currentStage?.transitions || [];
  const timeline = [...(ticket.timeline || [])].reverse();

  return (
    <div className="space-y-6" data-testid="ticket-detail">
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/admin/service-requests')} data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold text-slate-900">#{ticket.ticket_number}</h1>
            <span className={`text-xs px-2 py-0.5 rounded-full ${ticket.is_open ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'}`}>
              {ticket.is_open ? 'Open' : 'Closed'}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[ticket.priority_name] || priorityColors.medium}`}>
              {ticket.priority_name}
            </span>
          </div>
          <p className="text-sm text-slate-500">{ticket.subject}</p>
        </div>
        <div className="flex gap-2">
          {transitions.map(t => (
            <Button
              key={t.id}
              size="sm"
              variant={t.color === 'success' ? 'default' : t.color === 'danger' ? 'destructive' : 'outline'}
              onClick={() => handleTransition(t.id)}
              data-testid={`transition-${t.id}`}
            >
              {t.label}
            </Button>
          ))}
        </div>
      </div>

      <WorkflowProgress workflow={ticket.workflow} currentStageId={ticket.current_stage_id} />

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-5">
          {ticket.description && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Description</h3>
              <p className="text-sm text-slate-600 whitespace-pre-wrap">{ticket.description}</p>
            </div>
          )}

          {Object.keys(ticket.form_values || {}).length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Custom Fields</h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(ticket.form_values).map(([key, val]) => (
                  <div key={key}>
                    <span className="text-xs text-slate-400">{key.replace(/_/g, ' ')}</span>
                    <p className="text-sm text-slate-700">{String(val)}</p>
                  </div>
                ))}
              </div>
            </div>
          )}

          {(ticket.tasks || []).length > 0 && (
            <div data-testid="tasks-section">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Tasks ({ticket.tasks.length})</h3>
              <div className="space-y-2">
                {ticket.tasks.map(task => <TaskCard key={task.id} task={task} onComplete={handleCompleteTask} />)}
              </div>
            </div>
          )}

          <div className="bg-white border rounded-lg p-4" data-testid="timeline-section">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Activity ({timeline.length})</h3>
            <div className="divide-y">
              {timeline.map(entry => <TimelineEntry key={entry.id} entry={entry} />)}
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4" data-testid="comment-section">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-sm font-semibold text-slate-700">Add Comment</h3>
              <label className="flex items-center gap-1.5 text-xs text-slate-500 ml-auto cursor-pointer">
                <input type="checkbox" checked={isInternal} onChange={e => setIsInternal(e.target.checked)} className="rounded" />
                <Lock className="w-3 h-3" /> Internal note
              </label>
            </div>
            <textarea
              data-testid="comment-input"
              className="w-full border rounded-lg px-3 py-2 text-sm min-h-[80px] mb-2"
              value={comment}
              onChange={e => setComment(e.target.value)}
              placeholder="Write a comment..."
            />
            <Button size="sm" onClick={handleComment} disabled={sending || !comment.trim()} data-testid="send-comment-btn">
              <Send className="w-3.5 h-3.5 mr-1" /> {sending ? 'Sending...' : 'Send'}
            </Button>
          </div>
        </div>

        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Details</h3>
            <div className="space-y-3">
              <div>
                <span className="text-xs text-slate-400 block">Help Topic</span>
                <span className="text-sm text-slate-700">{ticket.help_topic_name}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Current Stage</span>
                <span className="text-sm text-slate-700">{ticket.current_stage_name || 'New'}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Created</span>
                <span className="text-sm text-slate-700">{ticket.created_at ? new Date(ticket.created_at).toLocaleString() : '-'}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Created By</span>
                <span className="text-sm text-slate-700">{ticket.created_by_name || '-'}</span>
              </div>
              <div>
                <span className="text-xs text-slate-400 block">Source</span>
                <span className="text-sm text-slate-700 capitalize">{ticket.source}</span>
              </div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-700">Assignment</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowAssign(!showAssign)} data-testid="assign-btn">
                <Edit2 className="w-3 h-3" />
              </Button>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-700">{ticket.assigned_team_name || 'Unassigned'}</span>
              </div>
              <div className="flex items-center gap-2">
                <User className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-700">{ticket.assigned_to_name || 'Unassigned'}</span>
              </div>
            </div>
            {showAssign && (
              <div className="mt-3 pt-3 border-t space-y-2" data-testid="assign-form">
                <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={assignTeamId} onChange={e => setAssignTeamId(e.target.value)}>
                  <option value="">Select team...</option>
                  {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
                <Button size="sm" onClick={handleAssign} className="w-full">Assign</Button>
              </div>
            )}
          </div>

          {ticket.company_name && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Company</h3>
              <div className="flex items-center gap-2">
                <Building2 className="w-4 h-4 text-slate-400" />
                <span className="text-sm text-slate-700">{ticket.company_name}</span>
              </div>
            </div>
          )}

          {ticket.contact && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Contact</h3>
              <div className="space-y-1 text-sm text-slate-600">
                {ticket.contact.name && <p>{ticket.contact.name}</p>}
                {ticket.contact.email && <p>{ticket.contact.email}</p>}
                {ticket.contact.phone && <p>{ticket.contact.phone}</p>}
              </div>
            </div>
          )}

          {ticket.tags?.length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Tags</h3>
              <div className="flex flex-wrap gap-1">
                {ticket.tags.map(tag => (
                  <span key={tag} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full flex items-center gap-1">
                    <Tag className="w-3 h-3" /> {tag}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
