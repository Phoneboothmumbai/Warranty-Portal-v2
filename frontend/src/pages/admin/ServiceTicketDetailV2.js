import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Clock, User, Building2, MessageSquare, CheckCircle, AlertTriangle,
  ChevronRight, Send, Lock, Tag, Edit2, Users, Calendar, Wrench, FileText,
  X, Clipboard, Package, MapPin, RefreshCw
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const getToken = () => localStorage.getItem('admin_token');
const authHeaders = () => ({ Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' });

const priorityColors = {
  low: 'bg-slate-100 text-slate-700 border-slate-200',
  medium: 'bg-blue-100 text-blue-700 border-blue-200',
  high: 'bg-orange-100 text-orange-700 border-orange-200',
  critical: 'bg-red-100 text-red-700 border-red-200',
};

const stageTypeColors = {
  initial: '#3B82F6', in_progress: '#F59E0B', waiting: '#8B5CF6',
  terminal_success: '#10B981', terminal_failure: '#EF4444',
};

// ========== WORKFLOW PROGRESS ==========
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
              <div className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium border transition-all ${isCurrent ? 'ring-2 ring-offset-1 shadow-sm' : isPast ? 'opacity-60' : 'opacity-40'}`}
                style={{ borderColor: color, backgroundColor: isCurrent ? color : 'transparent', color: isCurrent ? '#fff' : color }}
                data-testid={`stage-${stage.slug}`}>
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

// ========== ASSIGN ENGINEER MODAL ==========
const AssignEngineerModal = ({ open, onClose, onConfirm, ticket }) => {
  const [engineers, setEngineers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (!open) return;
    fetch(`${API}/api/ticketing/engineers`, { headers: authHeaders() })
      .then(r => r.json())
      .then(data => { setEngineers(Array.isArray(data) ? data : []); setLoading(false); });
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" data-testid="assign-engineer-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold">Assign Technician</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <div className="p-5 max-h-[60vh] overflow-y-auto">
          {loading ? <p className="text-center text-slate-400 py-8">Loading engineers...</p> : engineers.length === 0 ? (
            <p className="text-center text-slate-400 py-8">No engineers found. Add engineers in the Settings page.</p>
          ) : (
            <div className="space-y-2">
              {engineers.map(eng => {
                const isLastVisited = eng.last_ticket?.company_name === ticket?.company_name;
                return (
                  <div key={eng.id}
                    className={`border rounded-lg p-3 cursor-pointer transition-all ${selected === eng.id ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-200' : 'hover:border-slate-300'}`}
                    onClick={() => setSelected(eng.id)}
                    data-testid={`engineer-${eng.id}`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-full bg-slate-200 flex items-center justify-center text-sm font-semibold text-slate-600">
                          {eng.name?.charAt(0) || 'E'}
                        </div>
                        <div>
                          <p className="text-sm font-medium text-slate-800">{eng.name}</p>
                          <p className="text-xs text-slate-400">{eng.email}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${eng.open_tickets > 3 ? 'bg-red-100 text-red-600' : eng.open_tickets > 0 ? 'bg-yellow-100 text-yellow-600' : 'bg-green-100 text-green-600'}`}>
                          {eng.open_tickets} active
                        </span>
                      </div>
                    </div>
                    {isLastVisited && (
                      <div className="mt-2 ml-12 text-xs bg-amber-50 text-amber-700 px-2 py-1 rounded inline-flex items-center gap-1">
                        <MapPin className="w-3 h-3" /> Last visited this company
                      </div>
                    )}
                    {eng.last_ticket && (
                      <p className="mt-1 ml-12 text-xs text-slate-400">
                        Last: #{eng.last_ticket.ticket_number} - {eng.last_ticket.company_name || eng.last_ticket.subject}
                      </p>
                    )}
                    {eng.specialization && <p className="mt-1 ml-12 text-xs text-slate-400">Specialization: {eng.specialization}</p>}
                  </div>
                );
              })}
            </div>
          )}
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button disabled={!selected} onClick={() => {
            const eng = engineers.find(e => e.id === selected);
            onConfirm(selected, eng?.name || '');
          }} data-testid="confirm-assign-btn">Assign</Button>
        </div>
      </div>
    </div>
  );
};

// ========== SCHEDULE VISIT MODAL ==========
const ScheduleVisitModal = ({ open, onClose, onConfirm, ticket }) => {
  const [date, setDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState('');
  const [notes, setNotes] = useState('');
  const [slotsData, setSlotsData] = useState(null);
  const [loading, setLoading] = useState(false);

  const engineerId = ticket?.assigned_to_id;

  useEffect(() => {
    if (!open || !engineerId || !date) { setSlotsData(null); return; }
    setLoading(true);
    setSelectedSlot('');
    fetch(`${API}/api/ticketing/engineers/${engineerId}/available-slots?date=${date}`, { headers: authHeaders() })
      .then(r => r.json())
      .then(data => { setSlotsData(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [open, engineerId, date]);

  if (!open) return null;

  const slots = slotsData?.slots || [];
  const isWorkingDay = slotsData?.is_working_day;
  const isHoliday = slotsData?.is_holiday;

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" data-testid="schedule-visit-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-xl mx-4">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2"><Calendar className="w-5 h-5" /> Schedule Visit</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <div className="p-5 space-y-4">
          {ticket?.assigned_to_name && (
            <div className="bg-slate-50 rounded-lg p-3 flex items-center gap-2">
              <User className="w-4 h-4 text-slate-500" />
              <span className="text-sm">Technician: <strong>{ticket.assigned_to_name}</strong></span>
            </div>
          )}

          <div>
            <label className="text-sm font-medium block mb-1">Select Date *</label>
            <input type="date" className="w-full border rounded-lg px-3 py-2 text-sm" value={date} onChange={e => setDate(e.target.value)} min={new Date().toISOString().split('T')[0]} data-testid="visit-date" />
          </div>

          {date && loading && <p className="text-center text-slate-400 py-4 text-sm">Loading available slots...</p>}

          {date && !loading && slotsData && !isWorkingDay && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3" data-testid="not-working-day">
              <p className="text-sm text-red-700 flex items-center gap-1">
                <AlertTriangle className="w-4 h-4" />
                {isHoliday ? 'This is a holiday for this technician' : slotsData.message || 'Not a working day'}
              </p>
            </div>
          )}

          {date && !loading && slots.length > 0 && (
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium">Select Time Slot *</label>
                <span className="text-xs text-slate-400">{slotsData.work_start} - {slotsData.work_end}</span>
              </div>
              <div className="grid grid-cols-6 gap-1.5" data-testid="time-slots-grid">
                {slots.map(slot => (
                  <button
                    key={slot.time}
                    disabled={!slot.available}
                    onClick={() => setSelectedSlot(slot.time)}
                    className={`px-2 py-2 text-xs rounded-lg border transition-all font-medium ${
                      selectedSlot === slot.time
                        ? 'bg-blue-600 text-white border-blue-600 ring-2 ring-blue-200'
                        : slot.available
                          ? 'bg-white text-slate-700 border-slate-200 hover:border-blue-300 hover:bg-blue-50 cursor-pointer'
                          : 'bg-red-50 text-red-300 border-red-100 cursor-not-allowed line-through'
                    }`}
                    data-testid={`slot-${slot.time}`}
                    title={slot.blocked_by ? `Blocked: ${slot.blocked_by}` : 'Available'}
                  >
                    {slot.time}
                  </button>
                ))}
              </div>
              {slotsData.bookings?.length > 0 && (
                <div className="mt-3 bg-amber-50 border border-amber-200 rounded-lg p-3" data-testid="existing-bookings">
                  <p className="text-xs font-medium text-amber-800 mb-1 flex items-center gap-1">
                    <AlertTriangle className="w-3.5 h-3.5" /> Existing appointments (1hr gap enforced):
                  </p>
                  {slotsData.bookings.map((b, i) => (
                    <div key={i} className="text-xs text-amber-700 ml-4 mb-0.5">
                      {b.time} — #{b.ticket_number} {b.company_name || b.subject}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          <div>
            <label className="text-sm font-medium block mb-1">Notes</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm" value={notes} onChange={e => setNotes(e.target.value)} placeholder="Any notes for the visit..." />
          </div>
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button disabled={!date || !selectedSlot} onClick={() => {
            const scheduled_at = `${date}T${selectedSlot}:00`;
            // End time = start + 1 hour
            const [sh, sm] = selectedSlot.split(':').map(Number);
            const endMins = sh * 60 + sm + 60;
            const eh = Math.floor(endMins / 60);
            const em = endMins % 60;
            const scheduled_end = `${date}T${String(eh).padStart(2,'0')}:${String(em).padStart(2,'0')}:00`;
            onConfirm(scheduled_at, scheduled_end, notes);
          }} data-testid="confirm-schedule-btn">Schedule</Button>
        </div>
      </div>
    </div>
  );
};

// ========== DIAGNOSIS MODAL ==========
const DiagnosisModal = ({ open, onClose, onConfirm }) => {
  const [findings, setFindings] = useState('');
  const [recommendation, setRecommendation] = useState('');

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" data-testid="diagnosis-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2"><Clipboard className="w-5 h-5" /> Submit Diagnosis</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1">Findings *</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm min-h-[100px]" value={findings} onChange={e => setFindings(e.target.value)}
              placeholder="Describe what was found during diagnosis..." data-testid="diagnosis-findings" />
          </div>
          <div>
            <label className="text-sm font-medium block mb-1">Recommendation</label>
            <select className="w-full border rounded-lg px-3 py-2 text-sm" value={recommendation} onChange={e => setRecommendation(e.target.value)} data-testid="diagnosis-recommendation">
              <option value="">Select recommendation...</option>
              <option value="fix_on_site">Can be fixed on-site</option>
              <option value="parts_required">Parts/replacement required</option>
              <option value="escalate">Needs escalation</option>
              <option value="warranty_claim">Warranty claim</option>
              <option value="user_training">User training needed</option>
            </select>
          </div>
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button disabled={!findings.trim()} onClick={() => onConfirm(findings, recommendation)} data-testid="confirm-diagnosis-btn">Submit Diagnosis</Button>
        </div>
      </div>
    </div>
  );
};

// ========== PARTS LIST MODAL ==========
const PartsListModal = ({ open, onClose, onConfirm }) => {
  const [parts, setParts] = useState([{ name: '', quantity: 1, notes: '' }]);
  const [description, setDescription] = useState('');

  const addPart = () => setParts(p => [...p, { name: '', quantity: 1, notes: '' }]);
  const updatePart = (i, field, val) => setParts(p => p.map((part, idx) => idx === i ? { ...part, [field]: val } : part));
  const removePart = (i) => setParts(p => p.filter((_, idx) => idx !== i));

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" data-testid="parts-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2"><Package className="w-5 h-5" /> Parts Required</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <div className="p-5 space-y-3 max-h-[60vh] overflow-y-auto">
          <div>
            <label className="text-sm font-medium block mb-1">Description</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm" value={description} onChange={e => setDescription(e.target.value)} placeholder="Why are parts needed?" />
          </div>
          {parts.map((part, i) => (
            <div key={i} className="flex gap-2 items-start">
              <Input className="flex-1" placeholder="Part name *" value={part.name} onChange={e => updatePart(i, 'name', e.target.value)} data-testid={`part-name-${i}`} />
              <Input className="w-20" type="number" min="1" value={part.quantity} onChange={e => updatePart(i, 'quantity', parseInt(e.target.value) || 1)} />
              <Input className="flex-1" placeholder="Notes" value={part.notes} onChange={e => updatePart(i, 'notes', e.target.value)} />
              {parts.length > 1 && <button onClick={() => removePart(i)} className="p-2 hover:bg-red-50 rounded"><X className="w-4 h-4 text-red-400" /></button>}
            </div>
          ))}
          <Button variant="outline" size="sm" onClick={addPart}>+ Add Part</Button>
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button disabled={!parts.some(p => p.name.trim())} onClick={() => onConfirm(parts.filter(p => p.name.trim()), description)} data-testid="confirm-parts-btn">Submit</Button>
        </div>
      </div>
    </div>
  );
};

// ========== RESOLUTION MODAL ==========
const ResolutionModal = ({ open, onClose, onConfirm }) => {
  const [notes, setNotes] = useState('');
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" data-testid="resolution-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2"><CheckCircle className="w-5 h-5" /> Resolution Details</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1">What was done to fix the issue? *</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm min-h-[100px]" value={notes} onChange={e => setNotes(e.target.value)}
              placeholder="Describe the resolution..." data-testid="resolution-notes" />
          </div>
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button disabled={!notes.trim()} onClick={() => onConfirm(notes)} data-testid="confirm-resolution-btn">Confirm Resolution</Button>
        </div>
      </div>
    </div>
  );
};

// ========== QUOTATION MODAL ==========
const QuotationModal = ({ open, onClose, onConfirm }) => {
  const [notes, setNotes] = useState('');
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-center justify-center" data-testid="quotation-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg mx-4">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold flex items-center gap-2"><FileText className="w-5 h-5" /> Send Quotation</h2>
          <button onClick={onClose}><X className="w-5 h-5 text-slate-400" /></button>
        </div>
        <div className="p-5 space-y-4">
          <div>
            <label className="text-sm font-medium block mb-1">Quotation Notes</label>
            <textarea className="w-full border rounded-lg px-3 py-2 text-sm min-h-[80px]" value={notes} onChange={e => setNotes(e.target.value)}
              placeholder="Additional notes for the quotation..." data-testid="quotation-notes" />
          </div>
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={() => onConfirm(notes)} data-testid="confirm-quotation-btn">Send Quotation</Button>
        </div>
      </div>
    </div>
  );
};

// ========== TIMELINE ENTRY ==========
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

// ========== TASK CARD ==========
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
    {task.assigned_to_name && <p className="text-xs text-slate-400 mt-1 ml-4">Assigned: {task.assigned_to_name}</p>}
    {task.assigned_team_name && <p className="text-xs text-slate-400 mt-0.5 ml-4">Team: {task.assigned_team_name}</p>}
    {task.status !== 'completed' && (
      <Button size="sm" variant="outline" className="mt-2 ml-4" onClick={() => onComplete(task.id)} data-testid={`complete-task-${task.id}`}>
        Mark Complete
      </Button>
    )}
  </div>
);

// ========== MAIN COMPONENT ==========
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
  const [assignUserId, setAssignUserId] = useState('');

  // Transition modal states
  const [activeModal, setActiveModal] = useState(null); // 'assign_engineer' | 'schedule_visit' | 'diagnosis' | 'parts_list' | 'resolution' | 'quotation'
  const [pendingTransitionId, setPendingTransitionId] = useState(null);
  const [transitioning, setTransitioning] = useState(false);

  const fetchTicket = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ticketing/tickets/${ticketId}`, { headers: authHeaders() });
      if (!res.ok) throw new Error('Not found');
      setTicket(await res.json());
    } catch { toast.error('Failed to load ticket'); }
    finally { setLoading(false); }
  }, [ticketId]);

  useEffect(() => {
    fetchTicket();
    fetch(`${API}/api/ticketing/teams`, { headers: authHeaders() })
      .then(r => r.json()).then(data => setTeams(Array.isArray(data) ? data : []));
  }, [fetchTicket]);

  const handleComment = async () => {
    if (!comment.trim()) return;
    setSending(true);
    try {
      await fetch(`${API}/api/ticketing/tickets/${ticketId}/comment`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ content: comment, is_internal: isInternal }),
      });
      setComment(''); fetchTicket(); toast.success('Comment added');
    } catch { toast.error('Failed'); }
    finally { setSending(false); }
  };

  // Handle transition button click - check if it needs input
  const handleTransitionClick = (transition) => {
    const requires = transition.requires_input;
    if (requires && requires !== 'none') {
      setPendingTransitionId(transition.id);
      setActiveModal(requires);
    } else {
      executeTransition(transition.id, {});
    }
  };

  // Execute the actual transition API call
  const executeTransition = async (transitionId, extraData) => {
    setTransitioning(true);
    try {
      const res = await fetch(`${API}/api/ticketing/tickets/${ticketId}/transition`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ transition_id: transitionId, ...extraData }),
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Failed');
      }
      setTicket(await res.json());
      setActiveModal(null);
      setPendingTransitionId(null);
      toast.success('Ticket updated');
    } catch (e) { toast.error(e.message); }
    finally { setTransitioning(false); }
  };

  const handleAssignEngineer = (engineerId, engineerName) => {
    executeTransition(pendingTransitionId, { assigned_to_id: engineerId, assigned_to_name: engineerName });
  };

  const handleScheduleVisit = (scheduledAt, scheduledEnd, notes) => {
    executeTransition(pendingTransitionId, { scheduled_at: scheduledAt, scheduled_end_at: scheduledEnd, schedule_notes: notes });
  };

  const handleDiagnosis = (findings, recommendation) => {
    executeTransition(pendingTransitionId, { diagnosis_findings: findings, diagnosis_recommendation: recommendation });
  };

  const handlePartsRequired = (parts, description) => {
    executeTransition(pendingTransitionId, { parts_list: parts, notes: description });
  };

  const handleResolution = (notes) => {
    executeTransition(pendingTransitionId, { resolution_notes: notes });
  };

  const handleQuotation = (notes) => {
    executeTransition(pendingTransitionId, { notes: notes || 'Quotation sent' });
  };

  const handleAssignTeam = async () => {
    if (!assignTeamId && !assignUserId) return;
    try {
      await fetch(`${API}/api/ticketing/tickets/${ticketId}/assign`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ assigned_team_id: assignTeamId || undefined, assigned_to_id: assignUserId || undefined }),
      });
      fetchTicket(); setShowAssign(false); toast.success('Updated');
    } catch { toast.error('Failed'); }
  };

  const handleCompleteTask = async (taskId) => {
    try {
      await fetch(`${API}/api/ticketing/tasks/${taskId}/complete`, {
        method: 'POST', headers: authHeaders(),
        body: JSON.stringify({ notes: 'Completed' }),
      });
      fetchTicket(); toast.success('Task completed');
    } catch { toast.error('Failed'); }
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!ticket) return <div className="flex items-center justify-center h-64 text-slate-400">Ticket not found</div>;

  const currentStage = ticket.workflow?.stages?.find(s => s.id === ticket.current_stage_id);
  const transitions = currentStage?.transitions || [];
  const timeline = [...(ticket.timeline || [])].reverse();

  return (
    <div className="space-y-6" data-testid="ticket-detail">
      {/* Header */}
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
        <div className="flex gap-2 flex-wrap justify-end">
          {transitions.map(t => (
            <Button key={t.id} size="sm"
              variant={t.color === 'success' ? 'default' : t.color === 'danger' ? 'destructive' : 'outline'}
              onClick={() => handleTransitionClick(t)}
              disabled={transitioning}
              data-testid={`transition-${t.id}`}>
              {t.requires_input === 'assign_engineer' && <User className="w-3.5 h-3.5 mr-1" />}
              {t.requires_input === 'schedule_visit' && <Calendar className="w-3.5 h-3.5 mr-1" />}
              {t.requires_input === 'diagnosis' && <Clipboard className="w-3.5 h-3.5 mr-1" />}
              {t.requires_input === 'parts_list' && <Package className="w-3.5 h-3.5 mr-1" />}
              {t.requires_input === 'resolution' && <Wrench className="w-3.5 h-3.5 mr-1" />}
              {t.label}
            </Button>
          ))}
        </div>
      </div>

      <WorkflowProgress workflow={ticket.workflow} currentStageId={ticket.current_stage_id} />

      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 space-y-5">
          {/* Description */}
          {ticket.description && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Description</h3>
              <p className="text-sm text-slate-600 whitespace-pre-wrap">{ticket.description}</p>
            </div>
          )}

          {/* Diagnosis */}
          {ticket.diagnosis && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4" data-testid="diagnosis-section">
              <h3 className="text-sm font-semibold text-amber-800 mb-2 flex items-center gap-1"><Clipboard className="w-4 h-4" /> Diagnosis</h3>
              <p className="text-sm text-amber-700">{ticket.diagnosis.findings}</p>
              {ticket.diagnosis.recommendation && <p className="text-xs text-amber-600 mt-1">Recommendation: {ticket.diagnosis.recommendation}</p>}
              <p className="text-xs text-amber-500 mt-1">By {ticket.diagnosis.diagnosed_by} at {new Date(ticket.diagnosis.diagnosed_at).toLocaleString()}</p>
            </div>
          )}

          {/* Parts Required */}
          {ticket.parts_required?.length > 0 && (
            <div className="bg-white border rounded-lg p-4" data-testid="parts-section">
              <h3 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-1"><Package className="w-4 h-4" /> Parts Required</h3>
              <table className="w-full text-sm">
                <thead><tr className="text-xs text-slate-400"><th className="text-left py-1">Part</th><th className="text-left py-1">Qty</th><th className="text-left py-1">Notes</th></tr></thead>
                <tbody>
                  {ticket.parts_required.map((p, i) => (
                    <tr key={i} className="border-t"><td className="py-1.5">{p.name}</td><td className="py-1.5">{p.quantity}</td><td className="py-1.5 text-slate-500">{p.notes}</td></tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Schedule Info */}
          {ticket.scheduled_at && (
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4" data-testid="schedule-section">
              <h3 className="text-sm font-semibold text-purple-800 mb-1 flex items-center gap-1"><Calendar className="w-4 h-4" /> Scheduled Visit</h3>
              <p className="text-sm text-purple-700">{new Date(ticket.scheduled_at).toLocaleString()}</p>
              {ticket.schedule_notes && <p className="text-xs text-purple-600 mt-1">{ticket.schedule_notes}</p>}
            </div>
          )}

          {/* Custom Fields */}
          {Object.keys(ticket.form_values || {}).length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Custom Fields</h3>
              <div className="grid grid-cols-2 gap-2">
                {Object.entries(ticket.form_values).map(([key, val]) => (
                  <div key={key}><span className="text-xs text-slate-400">{key.replace(/_/g, ' ')}</span><p className="text-sm text-slate-700">{String(val)}</p></div>
                ))}
              </div>
            </div>
          )}

          {/* Tasks */}
          {(ticket.tasks || []).length > 0 && (
            <div data-testid="tasks-section">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Tasks ({ticket.tasks.length})</h3>
              <div className="space-y-2">{ticket.tasks.map(task => <TaskCard key={task.id} task={task} onComplete={handleCompleteTask} />)}</div>
            </div>
          )}

          {/* Timeline */}
          <div className="bg-white border rounded-lg p-4" data-testid="timeline-section">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Activity ({timeline.length})</h3>
            <div className="divide-y">{timeline.map(entry => <TimelineEntry key={entry.id} entry={entry} />)}</div>
          </div>

          {/* Comment Box */}
          <div className="bg-white border rounded-lg p-4" data-testid="comment-section">
            <div className="flex items-center gap-2 mb-3">
              <h3 className="text-sm font-semibold text-slate-700">Add Comment</h3>
              <label className="flex items-center gap-1.5 text-xs text-slate-500 ml-auto cursor-pointer">
                <input type="checkbox" checked={isInternal} onChange={e => setIsInternal(e.target.checked)} className="rounded" />
                <Lock className="w-3 h-3" /> Internal note
              </label>
            </div>
            <textarea data-testid="comment-input" className="w-full border rounded-lg px-3 py-2 text-sm min-h-[80px] mb-2" value={comment}
              onChange={e => setComment(e.target.value)} placeholder="Write a comment..." />
            <Button size="sm" onClick={handleComment} disabled={sending || !comment.trim()} data-testid="send-comment-btn">
              <Send className="w-3.5 h-3.5 mr-1" /> {sending ? 'Sending...' : 'Send'}
            </Button>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-4">
          <div className="bg-white border rounded-lg p-4">
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Details</h3>
            <div className="space-y-3">
              <div><span className="text-xs text-slate-400 block">Help Topic</span><span className="text-sm text-slate-700">{ticket.help_topic_name}</span></div>
              <div><span className="text-xs text-slate-400 block">Current Stage</span><span className="text-sm text-slate-700">{ticket.current_stage_name || 'New'}</span></div>
              <div><span className="text-xs text-slate-400 block">Created</span><span className="text-sm text-slate-700">{ticket.created_at ? new Date(ticket.created_at).toLocaleString() : '-'}</span></div>
              <div><span className="text-xs text-slate-400 block">Created By</span><span className="text-sm text-slate-700">{ticket.created_by_name || '-'}</span></div>
              <div><span className="text-xs text-slate-400 block">Source</span><span className="text-sm text-slate-700 capitalize">{ticket.source}</span></div>
            </div>
          </div>

          <div className="bg-white border rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-slate-700">Assignment</h3>
              <Button variant="ghost" size="sm" onClick={() => setShowAssign(!showAssign)} data-testid="edit-assign-btn"><Edit2 className="w-3 h-3" /></Button>
            </div>
            <div className="space-y-2">
              <div className="flex items-center gap-2"><Users className="w-4 h-4 text-slate-400" /><span className="text-sm text-slate-700">{ticket.assigned_team_name || 'Unassigned'}</span></div>
              <div className="flex items-center gap-2"><User className="w-4 h-4 text-slate-400" /><span className="text-sm text-slate-700">{ticket.assigned_to_name || 'Unassigned'}</span></div>
            </div>
            {showAssign && (
              <div className="mt-3 pt-3 border-t space-y-2" data-testid="assign-form">
                <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={assignTeamId} onChange={e => setAssignTeamId(e.target.value)}>
                  <option value="">Select team...</option>
                  {teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                </select>
                <Button size="sm" onClick={handleAssignTeam} className="w-full">Update</Button>
              </div>
            )}
          </div>

          {ticket.company_name && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Company</h3>
              <div className="flex items-center gap-2"><Building2 className="w-4 h-4 text-slate-400" /><span className="text-sm text-slate-700">{ticket.company_name}</span></div>
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

          {ticket.resolution_notes && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4" data-testid="resolution-section">
              <h3 className="text-sm font-semibold text-green-800 mb-1">Resolution</h3>
              <p className="text-sm text-green-700">{ticket.resolution_notes}</p>
            </div>
          )}

          {ticket.tags?.length > 0 && (
            <div className="bg-white border rounded-lg p-4">
              <h3 className="text-sm font-semibold text-slate-700 mb-2">Tags</h3>
              <div className="flex flex-wrap gap-1">{ticket.tags.map(tag => (
                <span key={tag} className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full flex items-center gap-1"><Tag className="w-3 h-3" /> {tag}</span>
              ))}</div>
            </div>
          )}
        </div>
      </div>

      {/* Transition Modals */}
      <AssignEngineerModal open={activeModal === 'assign_engineer'} onClose={() => { setActiveModal(null); setPendingTransitionId(null); }} onConfirm={handleAssignEngineer} ticket={ticket} />
      <ScheduleVisitModal open={activeModal === 'schedule_visit'} onClose={() => { setActiveModal(null); setPendingTransitionId(null); }} onConfirm={handleScheduleVisit} ticket={ticket} />
      <DiagnosisModal open={activeModal === 'diagnosis'} onClose={() => { setActiveModal(null); setPendingTransitionId(null); }} onConfirm={handleDiagnosis} />
      <PartsListModal open={activeModal === 'parts_list'} onClose={() => { setActiveModal(null); setPendingTransitionId(null); }} onConfirm={handlePartsRequired} />
      <ResolutionModal open={activeModal === 'resolution'} onClose={() => { setActiveModal(null); setPendingTransitionId(null); }} onConfirm={handleResolution} />
      <QuotationModal open={activeModal === 'quotation'} onClose={() => { setActiveModal(null); setPendingTransitionId(null); }} onConfirm={handleQuotation} />
    </div>
  );
}
