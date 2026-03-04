import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import {
  FolderKanban, Plus, Search, Building2, Clock, CheckCircle2,
  AlertTriangle, ChevronRight, Filter, Pause
} from 'lucide-react';
import { Input } from '../../components/ui/input';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  planning: { label: 'Planning', color: 'bg-blue-50 text-blue-700 border-blue-200', icon: Clock },
  active: { label: 'Active', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', icon: FolderKanban },
  'on-hold': { label: 'On Hold', color: 'bg-amber-50 text-amber-700 border-amber-200', icon: Pause },
  completed: { label: 'Completed', color: 'bg-slate-100 text-slate-600 border-slate-200', icon: CheckCircle2 },
};

const PRIORITY_COLORS = {
  critical: 'text-red-600', high: 'text-orange-600', medium: 'text-blue-600', low: 'text-green-600',
};

export default function Projects() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [projects, setProjects] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreate, setShowCreate] = useState(false);
  const [form, setForm] = useState({ name: '', company_id: '', description: '', priority: 'medium', start_date: '', end_date: '' });
  const [creating, setCreating] = useState(false);

  const hdrs = useCallback(() => ({
    Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'
  }), [token]);

  const fetchProjects = useCallback(async () => {
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.set('status', statusFilter);
      const res = await fetch(`${API}/api/projects?${params}`, { headers: hdrs() });
      if (res.ok) setProjects(await res.json());
    } catch { /* */ }
    finally { setLoading(false); }
  }, [hdrs, statusFilter]);

  useEffect(() => { fetchProjects(); }, [fetchProjects]);

  useEffect(() => {
    (async () => {
      try {
        const [cRes, tRes] = await Promise.all([
          fetch(`${API}/api/admin/companies`, { headers: hdrs() }),
          fetch(`${API}/api/projects/templates`, { headers: hdrs() }),
        ]);
        if (cRes.ok) setCompanies(await cRes.json());
        if (tRes.ok) {
          const t = await tRes.json();
          setTemplates(t);
          if (t.length === 0) {
            // Seed defaults
            await fetch(`${API}/api/projects/templates/seed-defaults`, { method: 'POST', headers: hdrs() });
            const r2 = await fetch(`${API}/api/projects/templates`, { headers: hdrs() });
            if (r2.ok) setTemplates(await r2.json());
          }
        }
      } catch { /* */ }
    })();
  }, [hdrs]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!form.name || !form.company_id) return toast.error('Name and company are required');
    setCreating(true);
    try {
      const res = await fetch(`${API}/api/projects`, {
        method: 'POST', headers: hdrs(), body: JSON.stringify(form)
      });
      if (res.ok) {
        const p = await res.json();
        toast.success('Project created');
        setShowCreate(false);
        setForm({ name: '', company_id: '', description: '', priority: 'medium', start_date: '', end_date: '' });
        navigate(`/admin/projects/${p.id}`);
      }
    } catch { toast.error('Failed to create project'); }
    finally { setCreating(false); }
  };

  const filtered = projects.filter(p =>
    (p.name || '').toLowerCase().includes(search.toLowerCase()) ||
    (p.company_name || '').toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="space-y-5" data-testid="projects-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Projects</h1>
          <p className="text-sm text-slate-500">{projects.length} project{projects.length !== 1 ? 's' : ''}</p>
        </div>
        <Button onClick={() => setShowCreate(true)} className="bg-[#0F62FE] hover:bg-[#0353E9] text-white" data-testid="create-project-btn">
          <Plus className="w-4 h-4 mr-1.5" />New Project
        </Button>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 flex-wrap">
        <div className="relative flex-1 max-w-xs">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input className="pl-9" placeholder="Search projects..." value={search} onChange={e => setSearch(e.target.value)} data-testid="project-search" />
        </div>
        <div className="flex border rounded-lg overflow-hidden">
          {['', 'active', 'planning', 'on-hold', 'completed'].map(s => (
            <button key={s} onClick={() => setStatusFilter(s)}
              className={`px-3 py-2 text-xs font-medium capitalize transition-colors ${statusFilter === s ? 'bg-[#0F62FE] text-white' : 'text-slate-600 hover:bg-slate-50'}`}
              data-testid={`project-filter-${s || 'all'}`}>
              {s || 'All'}
            </button>
          ))}
        </div>
      </div>

      {/* Project Cards */}
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-3 border-[#0F62FE] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : filtered.length > 0 ? (
        <div className="space-y-2">
          {filtered.map(p => {
            const cfg = STATUS_CONFIG[p.status] || STATUS_CONFIG.planning;
            const Icon = cfg.icon;
            return (
              <div key={p.id} onClick={() => navigate(`/admin/projects/${p.id}`)}
                className="bg-white rounded-lg border p-4 hover:border-slate-300 hover:shadow-sm transition-all cursor-pointer group"
                data-testid={`project-card-${p.id}`}>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <div className="w-10 h-10 rounded-lg bg-[#0F62FE]/10 flex items-center justify-center shrink-0">
                      <FolderKanban className="w-5 h-5 text-[#0F62FE]" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-slate-800 truncate">{p.name}</h3>
                        <span className={`px-2 py-0.5 rounded-full text-[10px] border font-medium inline-flex items-center gap-1 ${cfg.color}`}>
                          <Icon className="w-3 h-3" />{cfg.label}
                        </span>
                        <span className={`text-[10px] font-medium capitalize ${PRIORITY_COLORS[p.priority] || ''}`}>{p.priority}</span>
                      </div>
                      <div className="flex items-center gap-3 mt-0.5 text-xs text-slate-500">
                        <span className="flex items-center gap-1"><Building2 className="w-3 h-3" />{p.company_name}</span>
                        <span>{p.task_count} task{p.task_count !== 1 ? 's' : ''}</span>
                        <span>{p.completed_subtasks}/{p.subtask_count} subtasks done</span>
                        {p.start_date && <span>{p.start_date.slice(0, 10)}</span>}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-3 shrink-0">
                    {/* Progress bar */}
                    <div className="w-24 hidden sm:block">
                      <div className="flex items-center justify-between text-[10px] text-slate-500 mb-0.5">
                        <span>Progress</span><span>{p.progress}%</span>
                      </div>
                      <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div className="h-full rounded-full transition-all" style={{ width: `${p.progress}%`, backgroundColor: p.progress === 100 ? '#22C55E' : '#0F62FE' }} />
                      </div>
                    </div>
                    <ChevronRight className="w-4 h-4 text-slate-300 group-hover:text-slate-500 transition-colors" />
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        <div className="bg-white rounded-lg border p-12 text-center">
          <FolderKanban className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500 mb-3">{search ? 'No projects match your search' : 'No projects yet'}</p>
          <Button onClick={() => setShowCreate(true)} variant="outline" size="sm">Create your first project</Button>
        </div>
      )}

      {/* Create Modal */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={() => setShowCreate(false)}>
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md" onClick={e => e.stopPropagation()} data-testid="create-project-modal">
            <div className="p-5 border-b">
              <h2 className="text-lg font-bold text-slate-900">New Project</h2>
            </div>
            <form onSubmit={handleCreate} className="p-5 space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Project Name *</label>
                <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} placeholder="e.g., Office Network Setup - Acme Corp" required data-testid="project-name-input" />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Company *</label>
                <select value={form.company_id} onChange={e => setForm({ ...form, company_id: e.target.value })} required
                  className="w-full border rounded-md px-3 py-2 text-sm" data-testid="project-company-select">
                  <option value="">Select company</option>
                  {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Description</label>
                <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
                  className="w-full border rounded-md px-3 py-2 text-sm h-20 resize-none" placeholder="Brief description..." />
              </div>
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Priority</label>
                  <select value={form.priority} onChange={e => setForm({ ...form, priority: e.target.value })}
                    className="w-full border rounded-md px-3 py-2 text-sm" data-testid="project-priority-select">
                    {['low', 'medium', 'high', 'critical'].map(p => <option key={p} value={p}>{p}</option>)}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Start</label>
                  <Input type="date" value={form.start_date} onChange={e => setForm({ ...form, start_date: e.target.value })} />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">End</label>
                  <Input type="date" value={form.end_date} onChange={e => setForm({ ...form, end_date: e.target.value })} />
                </div>
              </div>
              <div className="flex justify-end gap-2 pt-2">
                <Button type="button" variant="outline" onClick={() => setShowCreate(false)}>Cancel</Button>
                <Button type="submit" disabled={creating} className="bg-[#0F62FE] hover:bg-[#0353E9] text-white" data-testid="project-create-submit">
                  {creating ? 'Creating...' : 'Create Project'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
