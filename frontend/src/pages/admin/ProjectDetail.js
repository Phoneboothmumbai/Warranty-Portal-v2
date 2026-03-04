import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  ArrowLeft, Plus, ChevronDown, ChevronRight, CheckCircle2, Circle,
  Clock, AlertTriangle, User, Calendar, MessageSquare, FolderKanban,
  Trash2, Play, BarChart3, ListTodo, GanttChart
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_ICON = {
  pending: <Circle className="w-4 h-4 text-slate-300" />,
  'in-progress': <Play className="w-4 h-4 text-blue-500" />,
  completed: <CheckCircle2 className="w-4 h-4 text-emerald-500" />,
  skipped: <Circle className="w-4 h-4 text-slate-200 line-through" />,
};

const STATUS_BADGE = {
  pending: 'bg-slate-50 text-slate-600 border-slate-200',
  'in-progress': 'bg-blue-50 text-blue-700 border-blue-200',
  completed: 'bg-emerald-50 text-emerald-700 border-emerald-200',
  skipped: 'bg-slate-50 text-slate-400 border-slate-100',
};

export default function ProjectDetail() {
  const { projectId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [project, setProject] = useState(null);
  const [templates, setTemplates] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedTasks, setExpandedTasks] = useState({});
  const [showAddTask, setShowAddTask] = useState(false);
  const [taskForm, setTaskForm] = useState({ template_id: '', name: '', assigned_to: '', start_date: '', due_date: '' });
  const [adding, setAdding] = useState(false);
  const [view, setView] = useState('tasks'); // tasks | gantt

  const hdrs = useCallback(() => ({
    Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'
  }), [token]);

  const fetchProject = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/projects/${projectId}`, { headers: hdrs() });
      if (res.ok) {
        const data = await res.json();
        setProject(data);
        // Auto-expand all tasks
        const exp = {};
        (data.tasks || []).forEach(t => { exp[t.id] = true; });
        setExpandedTasks(prev => Object.keys(prev).length === 0 ? exp : prev);
      }
    } catch { /* */ }
    finally { setLoading(false); }
  }, [projectId, hdrs]);

  useEffect(() => { fetchProject(); }, [fetchProject]);

  useEffect(() => {
    (async () => {
      try {
        const [tRes, sRes] = await Promise.all([
          fetch(`${API}/api/projects/templates`, { headers: hdrs() }),
          fetch(`${API}/api/projects/staff-list`, { headers: hdrs() }),
        ]);
        if (tRes.ok) setTemplates(await tRes.json());
        if (sRes.ok) {
          const d = await sRes.json();
          setStaff([...(d.staff || []), ...(d.members || [])]);
        }
      } catch { /* */ }
    })();
  }, [hdrs]);

  const toggleTask = (id) => setExpandedTasks(prev => ({ ...prev, [id]: !prev[id] }));

  const addTask = async (e) => {
    e.preventDefault();
    if (!taskForm.template_id) return toast.error('Select a template');
    setAdding(true);
    try {
      const res = await fetch(`${API}/api/projects/${projectId}/tasks`, {
        method: 'POST', headers: hdrs(), body: JSON.stringify(taskForm)
      });
      if (res.ok) {
        toast.success('Task added with subtasks');
        setShowAddTask(false);
        setTaskForm({ template_id: '', name: '', assigned_to: '', start_date: '', due_date: '' });
        fetchProject();
      }
    } catch { toast.error('Failed to add task'); }
    finally { setAdding(false); }
  };

  const updateSubtask = async (taskId, subtaskId, updates) => {
    try {
      await fetch(`${API}/api/projects/${projectId}/tasks/${taskId}/subtasks/${subtaskId}`, {
        method: 'PUT', headers: hdrs(), body: JSON.stringify(updates)
      });
      fetchProject();
    } catch { toast.error('Update failed'); }
  };

  const deleteTask = async (taskId) => {
    if (!window.confirm('Delete this task and all its subtasks?')) return;
    try {
      await fetch(`${API}/api/projects/${projectId}/tasks/${taskId}`, {
        method: 'DELETE', headers: hdrs()
      });
      toast.success('Task deleted');
      fetchProject();
    } catch { toast.error('Delete failed'); }
  };

  const completeSubtask = async (taskId, subtask) => {
    const remarks = window.prompt('Add completion remarks (optional):');
    if (remarks === null) return;
    await updateSubtask(taskId, subtask.id, { status: 'completed', remarks: remarks || subtask.remarks || '' });
    toast.success(`"${subtask.name}" marked complete`);
  };

  const startSubtask = async (taskId, subtask) => {
    await updateSubtask(taskId, subtask.id, { status: 'in-progress' });
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-6 h-6 border-3 border-[#0F62FE] border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (!project) return (
    <div className="text-center p-12">
      <p className="text-slate-500">Project not found</p>
      <Button variant="outline" className="mt-3" onClick={() => navigate('/admin/projects')}>Back to Projects</Button>
    </div>
  );

  const tasks = project.tasks || [];

  return (
    <div className="space-y-5" data-testid="project-detail">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <button onClick={() => navigate('/admin/projects')} className="mt-1 p-1 rounded hover:bg-slate-100" data-testid="back-to-projects">
            <ArrowLeft className="w-5 h-5 text-slate-500" />
          </button>
          <div>
            <h1 className="text-xl font-bold text-slate-900">{project.name}</h1>
            <div className="flex items-center gap-3 mt-1 text-xs text-slate-500">
              <span className="flex items-center gap-1"><FolderKanban className="w-3 h-3" />{project.company_name}</span>
              <span className={`px-2 py-0.5 rounded-full border text-[10px] font-medium capitalize ${
                project.status === 'active' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                project.status === 'completed' ? 'bg-slate-100 text-slate-600 border-slate-200' :
                'bg-blue-50 text-blue-700 border-blue-200'
              }`}>{project.status}</span>
              <span className="capitalize font-medium">{project.priority} priority</span>
              {project.start_date && <span><Calendar className="w-3 h-3 inline mr-0.5" />{project.start_date.slice(0, 10)}</span>}
              {project.end_date && <span>- {project.end_date.slice(0, 10)}</span>}
            </div>
          </div>
        </div>
        <Button onClick={() => setShowAddTask(true)} className="bg-[#0F62FE] hover:bg-[#0353E9] text-white" data-testid="add-task-btn">
          <Plus className="w-4 h-4 mr-1.5" />Add Task
        </Button>
      </div>

      {/* Progress Overview */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-white rounded-lg border p-3">
          <p className="text-xs text-slate-500">Tasks</p>
          <p className="text-2xl font-bold text-slate-800">{tasks.length}</p>
        </div>
        <div className="bg-white rounded-lg border p-3">
          <p className="text-xs text-slate-500">Subtasks</p>
          <p className="text-2xl font-bold text-slate-800">{project.completed_subtasks}/{project.subtask_count}</p>
        </div>
        <div className="bg-white rounded-lg border p-3">
          <p className="text-xs text-slate-500">Progress</p>
          <p className="text-2xl font-bold" style={{ color: project.progress === 100 ? '#22C55E' : '#0F62FE' }}>{project.progress}%</p>
        </div>
        <div className="bg-white rounded-lg border p-3">
          <p className="text-xs text-slate-500">Status</p>
          <p className="text-lg font-bold text-slate-800 capitalize">{project.status}</p>
        </div>
      </div>

      {/* Overall progress bar */}
      <div className="bg-white rounded-lg border p-3">
        <div className="h-2.5 bg-slate-100 rounded-full overflow-hidden">
          <div className="h-full rounded-full transition-all duration-500" style={{ width: `${project.progress}%`, backgroundColor: project.progress === 100 ? '#22C55E' : '#0F62FE' }} />
        </div>
        <p className="text-xs text-slate-500 mt-1">{project.completed_subtasks} of {project.subtask_count} subtasks completed</p>
      </div>

      {/* View Toggle */}
      <div className="flex items-center gap-1 border rounded-lg p-0.5 w-fit">
        <button onClick={() => setView('tasks')} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${view === 'tasks' ? 'bg-[#0F62FE] text-white' : 'text-slate-600 hover:bg-slate-50'}`} data-testid="view-tasks">
          <ListTodo className="w-3.5 h-3.5" />Tasks
        </button>
        <button onClick={() => setView('gantt')} className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${view === 'gantt' ? 'bg-[#0F62FE] text-white' : 'text-slate-600 hover:bg-slate-50'}`} data-testid="view-gantt">
          <BarChart3 className="w-3.5 h-3.5" />Gantt
        </button>
      </div>

      {/* Task List View */}
      {view === 'tasks' && (
        <div className="space-y-3" data-testid="task-list">
          {tasks.length === 0 ? (
            <div className="bg-white rounded-lg border p-12 text-center">
              <FolderKanban className="w-10 h-10 text-slate-300 mx-auto mb-3" />
              <p className="text-sm text-slate-500 mb-3">No tasks yet. Add a task from a template to get started.</p>
              <Button onClick={() => setShowAddTask(true)} variant="outline" size="sm">Add Task</Button>
            </div>
          ) : tasks.map(task => (
            <div key={task.id} className="bg-white rounded-lg border overflow-hidden" data-testid={`task-${task.id}`}>
              {/* Task Header */}
              <div className="flex items-center gap-3 p-4 cursor-pointer hover:bg-slate-50 transition-colors" onClick={() => toggleTask(task.id)}>
                {expandedTasks[task.id] ? <ChevronDown className="w-4 h-4 text-slate-400 shrink-0" /> : <ChevronRight className="w-4 h-4 text-slate-400 shrink-0" />}
                {STATUS_ICON[task.status] || STATUS_ICON.pending}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-800">{task.name}</h3>
                    <span className={`px-1.5 py-0.5 rounded text-[10px] border font-medium ${STATUS_BADGE[task.status] || STATUS_BADGE.pending}`}>{task.status}</span>
                    <span className="text-[10px] text-slate-400 bg-slate-50 px-1.5 py-0.5 rounded">{task.template_name}</span>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-slate-500 mt-0.5">
                    {task.assigned_to_name && <span className="flex items-center gap-1"><User className="w-3 h-3" />{task.assigned_to_name}</span>}
                    <span>{task.completed_subtasks}/{task.subtask_count} done</span>
                    {task.due_date && <span className="flex items-center gap-1"><Calendar className="w-3 h-3" />{task.due_date.slice(0, 10)}</span>}
                  </div>
                </div>
                <div className="flex items-center gap-3 shrink-0">
                  <div className="w-20 hidden sm:block">
                    <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                      <div className="h-full rounded-full transition-all" style={{ width: `${task.progress}%`, backgroundColor: task.progress === 100 ? '#22C55E' : '#0F62FE' }} />
                    </div>
                    <p className="text-[10px] text-slate-400 mt-0.5 text-right">{task.progress}%</p>
                  </div>
                  <button onClick={e => { e.stopPropagation(); deleteTask(task.id); }} className="p-1 text-slate-300 hover:text-red-500 transition-colors" data-testid={`delete-task-${task.id}`}>
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Subtasks */}
              {expandedTasks[task.id] && (
                <div className="border-t bg-slate-50/50">
                  {(task.subtasks || []).map((st, idx) => {
                    const isActive = st.status === 'in-progress';
                    const isDone = st.status === 'completed';
                    const isPending = st.status === 'pending';
                    // Check if previous subtask is done (for sequential flow)
                    const prevDone = idx === 0 || (task.subtasks[idx - 1]?.status === 'completed');

                    return (
                      <div key={st.id} className={`flex items-start gap-3 px-4 py-3 border-b border-slate-100 last:border-b-0 ${isDone ? 'opacity-70' : ''}`}
                        data-testid={`subtask-${st.id}`}>
                        {/* Status + Order */}
                        <div className="flex items-center gap-2 shrink-0 pt-0.5">
                          <span className="text-[10px] text-slate-400 font-mono w-5 text-right">{st.order}.</span>
                          {isDone ? (
                            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                          ) : isActive ? (
                            <div className="w-5 h-5 rounded-full border-2 border-blue-500 flex items-center justify-center">
                              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                            </div>
                          ) : (
                            <Circle className="w-5 h-5 text-slate-200" />
                          )}
                        </div>

                        {/* Content */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2">
                            <span className={`text-sm font-medium ${isDone ? 'text-slate-500 line-through' : 'text-slate-800'}`}>{st.name}</span>
                            {st.is_mandatory && <span className="text-[9px] text-red-500 bg-red-50 px-1 rounded">Required</span>}
                            {st.estimated_hours > 0 && <span className="text-[10px] text-slate-400"><Clock className="w-3 h-3 inline mr-0.5" />{st.estimated_hours}h est.</span>}
                          </div>
                          {st.description && <p className="text-xs text-slate-500 mt-0.5">{st.description}</p>}

                          {/* Metadata */}
                          <div className="flex items-center gap-3 mt-1 text-[10px] text-slate-400 flex-wrap">
                            {st.assigned_to_name && <span className="flex items-center gap-0.5"><User className="w-3 h-3" />{st.assigned_to_name}</span>}
                            {st.started_at && <span>Started: {st.started_at.slice(0, 16).replace('T', ' ')}</span>}
                            {st.completed_at && <span>Done: {st.completed_at.slice(0, 16).replace('T', ' ')}</span>}
                            {st.completed_by_name && <span>By: {st.completed_by_name}</span>}
                            {st.actual_hours > 0 && <span>{st.actual_hours}h actual</span>}
                          </div>

                          {/* Remarks */}
                          {st.remarks && (
                            <div className="mt-1 flex items-start gap-1 text-xs bg-slate-100 rounded px-2 py-1">
                              <MessageSquare className="w-3 h-3 text-slate-400 mt-0.5 shrink-0" />
                              <span className="text-slate-600">{st.remarks}</span>
                            </div>
                          )}
                        </div>

                        {/* Actions */}
                        <div className="flex items-center gap-1 shrink-0">
                          {isPending && prevDone && (
                            <button onClick={() => startSubtask(task.id, st)}
                              className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100 transition-colors"
                              data-testid={`start-subtask-${st.id}`}>
                              Start
                            </button>
                          )}
                          {(isActive || (isPending && prevDone)) && (
                            <button onClick={() => completeSubtask(task.id, st)}
                              className="px-2 py-1 text-xs bg-emerald-50 text-emerald-700 rounded hover:bg-emerald-100 transition-colors"
                              data-testid={`complete-subtask-${st.id}`}>
                              Done
                            </button>
                          )}
                          {!isDone && (
                            <select value={st.assigned_to || ''} onChange={e => updateSubtask(task.id, st.id, { assigned_to: e.target.value })}
                              className="text-[10px] border rounded px-1 py-0.5 text-slate-500 max-w-[100px]"
                              data-testid={`assign-subtask-${st.id}`}>
                              <option value="">Assign</option>
                              {staff.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                            </select>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Gantt View */}
      {view === 'gantt' && <GanttView tasks={tasks} project={project} />}

      {/* Add Task Modal */}
      {showAddTask && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowAddTask(false)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md" onClick={e => e.stopPropagation()} data-testid="add-task-modal">
            <div className="p-5 border-b">
              <h2 className="text-lg font-bold text-slate-900">Add Task from Template</h2>
              <p className="text-xs text-slate-500 mt-1">Select a template — all subtasks will be auto-generated</p>
            </div>
            <form onSubmit={addTask} className="p-5 space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Template *</label>
                <select value={taskForm.template_id} onChange={e => {
                  const t = templates.find(t => t.id === e.target.value);
                  setTaskForm({ ...taskForm, template_id: e.target.value, name: t ? t.name : '' });
                }} required className="w-full border rounded-md px-3 py-2 text-sm" data-testid="task-template-select">
                  <option value="">Select template</option>
                  {templates.map(t => (
                    <option key={t.id} value={t.id}>{t.name} ({(t.subtasks || []).length} subtasks)</option>
                  ))}
                </select>
                {taskForm.template_id && (() => {
                  const tmpl = templates.find(t => t.id === taskForm.template_id);
                  if (!tmpl) return null;
                  return (
                    <div className="mt-2 bg-slate-50 rounded p-2 max-h-32 overflow-y-auto">
                      <p className="text-xs font-medium text-slate-600 mb-1">Subtasks that will be created:</p>
                      {(tmpl.subtasks || []).map((s, i) => (
                        <p key={i} className="text-xs text-slate-500">{s.order}. {s.name} {s.estimated_hours > 0 && `(${s.estimated_hours}h)`}</p>
                      ))}
                    </div>
                  );
                })()}
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Task Name</label>
                <Input value={taskForm.name} onChange={e => setTaskForm({ ...taskForm, name: e.target.value })}
                  placeholder="e.g., CCTV - Building A (defaults to template name)" data-testid="task-name-input" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Assign To</label>
                <select value={taskForm.assigned_to} onChange={e => setTaskForm({ ...taskForm, assigned_to: e.target.value })}
                  className="w-full border rounded-md px-3 py-2 text-sm">
                  <option value="">Unassigned</option>
                  {staff.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                </select>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Start</label>
                  <Input type="date" value={taskForm.start_date} onChange={e => setTaskForm({ ...taskForm, start_date: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Due</label>
                  <Input type="date" value={taskForm.due_date} onChange={e => setTaskForm({ ...taskForm, due_date: e.target.value })} />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowAddTask(false)}>Cancel</Button>
                <Button type="submit" disabled={adding} className="bg-[#0F62FE] hover:bg-[#0353E9] text-white" data-testid="task-add-submit">
                  {adding ? 'Adding...' : 'Add Task'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}


// ══════════════════════════════════════════════════════════
// GANTT CHART COMPONENT
// ══════════════════════════════════════════════════════════

function GanttView({ tasks, project }) {
  if (tasks.length === 0) return (
    <div className="bg-white rounded-lg border p-12 text-center">
      <p className="text-sm text-slate-500">Add tasks to see the Gantt chart</p>
    </div>
  );

  // Compute date range
  const allDates = [];
  const pStart = project.start_date ? new Date(project.start_date) : null;
  const pEnd = project.end_date ? new Date(project.end_date) : null;
  if (pStart) allDates.push(pStart);
  if (pEnd) allDates.push(pEnd);

  tasks.forEach(t => {
    if (t.start_date) allDates.push(new Date(t.start_date));
    if (t.due_date) allDates.push(new Date(t.due_date));
    if (t.created_at) allDates.push(new Date(t.created_at));
  });

  if (allDates.length === 0) allDates.push(new Date());
  const minDate = new Date(Math.min(...allDates.map(d => d.getTime())));
  const maxDate = new Date(Math.max(...allDates.map(d => d.getTime())));

  // Ensure at least 30 days range
  const range = (maxDate - minDate) / (1000 * 60 * 60 * 24);
  if (range < 30) maxDate.setDate(maxDate.getDate() + (30 - range));

  // Add padding
  minDate.setDate(minDate.getDate() - 3);
  maxDate.setDate(maxDate.getDate() + 7);

  const totalDays = Math.max(1, Math.ceil((maxDate - minDate) / (1000 * 60 * 60 * 24)));
  const dayWidth = Math.max(20, 800 / totalDays);

  const getOffset = (dateStr) => {
    if (!dateStr) return 0;
    const d = new Date(dateStr);
    return Math.max(0, (d - minDate) / (1000 * 60 * 60 * 24)) * dayWidth;
  };

  const getWidth = (startStr, endStr) => {
    if (!startStr || !endStr) return dayWidth * 7; // default 1 week
    const s = new Date(startStr);
    const e = new Date(endStr);
    return Math.max(dayWidth, ((e - s) / (1000 * 60 * 60 * 24)) * dayWidth);
  };

  // Generate month labels
  const months = [];
  const cur = new Date(minDate);
  cur.setDate(1);
  while (cur <= maxDate) {
    months.push({ label: cur.toLocaleDateString('en', { month: 'short', year: '2-digit' }), offset: getOffset(cur.toISOString()) });
    cur.setMonth(cur.getMonth() + 1);
  }

  const chartWidth = totalDays * dayWidth;

  return (
    <div className="bg-white rounded-lg border overflow-hidden" data-testid="gantt-chart">
      <div className="overflow-x-auto">
        <div style={{ minWidth: 300 + chartWidth }}>
          {/* Month headers */}
          <div className="flex border-b">
            <div className="w-[300px] shrink-0 bg-slate-50 p-2 border-r">
              <span className="text-xs font-medium text-slate-600">Task / Subtask</span>
            </div>
            <div className="flex-1 relative bg-slate-50" style={{ width: chartWidth }}>
              <div className="flex">
                {months.map((m, i) => (
                  <div key={i} className="text-[10px] text-slate-500 font-medium px-2 py-2 border-r border-slate-200" style={{ position: 'absolute', left: m.offset }}>
                    {m.label}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Today marker */}
          <div className="relative">
            {tasks.map(task => (
              <div key={task.id}>
                {/* Main task bar */}
                <div className="flex border-b border-slate-100 hover:bg-blue-50/30">
                  <div className="w-[300px] shrink-0 p-2 border-r flex items-center gap-2">
                    <FolderKanban className="w-3.5 h-3.5 text-[#0F62FE] shrink-0" />
                    <span className="text-xs font-semibold text-slate-800 truncate">{task.name}</span>
                    <span className="text-[10px] text-slate-400 shrink-0">{task.progress}%</span>
                  </div>
                  <div className="flex-1 relative py-1.5" style={{ width: chartWidth }}>
                    <div className="absolute h-5 rounded-md flex items-center px-1.5"
                      style={{
                        left: getOffset(task.start_date || task.created_at),
                        width: getWidth(task.start_date || task.created_at, task.due_date || project.end_date),
                        backgroundColor: task.status === 'completed' ? '#22C55E' : '#0F62FE',
                        opacity: 0.85,
                      }}>
                      <span className="text-[9px] text-white font-medium truncate">{task.name}</span>
                    </div>
                  </div>
                </div>

                {/* Subtask bars */}
                {(task.subtasks || []).map(st => (
                  <div key={st.id} className="flex border-b border-slate-50 hover:bg-slate-50/50">
                    <div className="w-[300px] shrink-0 p-1.5 pl-8 border-r flex items-center gap-2">
                      {st.status === 'completed' ? <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" /> : <Circle className="w-3 h-3 text-slate-200 shrink-0" />}
                      <span className={`text-[11px] truncate ${st.status === 'completed' ? 'text-slate-400 line-through' : 'text-slate-600'}`}>{st.order}. {st.name}</span>
                    </div>
                    <div className="flex-1 relative py-1" style={{ width: chartWidth }}>
                      <div className="absolute h-3.5 rounded"
                        style={{
                          left: getOffset(st.started_at || task.start_date || task.created_at),
                          width: Math.max(dayWidth * 2, (st.estimated_hours || 4) * dayWidth * 0.5),
                          backgroundColor: st.status === 'completed' ? '#86EFAC' : st.status === 'in-progress' ? '#93C5FD' : '#E2E8F0',
                        }} />
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
