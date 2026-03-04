import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../../context/AuthContext';
import {
  Plus, Trash2, GripVertical, ChevronDown, ChevronRight, Edit3, Save, X,
  FileText, Clock, AlertTriangle, CheckCircle2
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function ProjectTemplates() {
  const { token } = useAuth();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState({});
  const [editing, setEditing] = useState(null);
  const [showCreate, setShowCreate] = useState(false);

  const hdrs = useCallback(() => ({
    Authorization: `Bearer ${token}`, 'Content-Type': 'application/json'
  }), [token]);

  const fetchTemplates = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/projects/templates`, { headers: hdrs() });
      if (res.ok) {
        const data = await res.json();
        setTemplates(data);
        if (data.length === 0) {
          const seedRes = await fetch(`${API}/api/projects/templates/seed-defaults`, { method: 'POST', headers: hdrs() });
          if (seedRes.ok) {
            const r2 = await fetch(`${API}/api/projects/templates`, { headers: hdrs() });
            if (r2.ok) setTemplates(await r2.json());
            toast.success('Default templates loaded');
          }
        }
      }
    } catch { /* */ }
    finally { setLoading(false); }
  }, [hdrs]);

  useEffect(() => { fetchTemplates(); }, [fetchTemplates]);

  const deleteTemplate = async (id) => {
    if (!window.confirm('Delete this template?')) return;
    await fetch(`${API}/api/projects/templates/${id}`, { method: 'DELETE', headers: hdrs() });
    toast.success('Template deleted');
    fetchTemplates();
  };

  return (
    <div className="space-y-5" data-testid="project-templates-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Task Templates</h1>
          <p className="text-sm text-slate-500">Define reusable task templates with auto-generated subtasks</p>
        </div>
        <Button onClick={() => setShowCreate(true)} className="bg-[#0F62FE] hover:bg-[#0353E9] text-white" data-testid="create-template-btn">
          <Plus className="w-4 h-4 mr-1.5" />New Template
        </Button>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-3 border-[#0F62FE] border-t-transparent rounded-full animate-spin" />
        </div>
      ) : templates.length === 0 ? (
        <div className="bg-white rounded-lg border p-12 text-center">
          <FileText className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No templates yet</p>
        </div>
      ) : (
        <div className="space-y-3">
          {templates.map(tmpl => (
            <div key={tmpl.id} className="bg-white rounded-lg border overflow-hidden" data-testid={`template-${tmpl.id}`}>
              <div className="flex items-center gap-3 p-4 cursor-pointer hover:bg-slate-50" onClick={() => setExpanded(p => ({ ...p, [tmpl.id]: !p[tmpl.id] }))}>
                {expanded[tmpl.id] ? <ChevronDown className="w-4 h-4 text-slate-400" /> : <ChevronRight className="w-4 h-4 text-slate-400" />}
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h3 className="font-semibold text-slate-800">{tmpl.name}</h3>
                    {tmpl.category && <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-500">{tmpl.category}</span>}
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">{tmpl.description}</p>
                </div>
                <span className="text-xs text-slate-400">{(tmpl.subtasks || []).length} subtasks</span>
                <button onClick={e => { e.stopPropagation(); deleteTemplate(tmpl.id); }} className="p-1 text-slate-300 hover:text-red-500">
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>

              {expanded[tmpl.id] && (
                <div className="border-t bg-slate-50/50 p-4">
                  {editing === tmpl.id ? (
                    <TemplateEditor template={tmpl} hdrs={hdrs} onSave={() => { setEditing(null); fetchTemplates(); }} onCancel={() => setEditing(null)} />
                  ) : (
                    <>
                      <div className="flex items-center justify-between mb-3">
                        <p className="text-xs font-medium text-slate-600">Subtask Sequence</p>
                        <Button variant="outline" size="sm" onClick={() => setEditing(tmpl.id)} data-testid={`edit-template-${tmpl.id}`}>
                          <Edit3 className="w-3 h-3 mr-1" />Edit
                        </Button>
                      </div>
                      <div className="space-y-1.5">
                        {(tmpl.subtasks || []).sort((a, b) => a.order - b.order).map(s => (
                          <div key={s.order} className="flex items-center gap-3 bg-white rounded p-2 border border-slate-100">
                            <span className="text-xs font-mono text-slate-400 w-6 text-right">{s.order}.</span>
                            <div className="flex-1">
                              <span className="text-sm text-slate-700 font-medium">{s.name}</span>
                              {s.description && <p className="text-xs text-slate-400">{s.description}</p>}
                            </div>
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                              {s.estimated_hours > 0 && <span className="flex items-center gap-0.5"><Clock className="w-3 h-3" />{s.estimated_hours}h</span>}
                              {s.is_mandatory ? <span className="text-red-500 text-[10px]">Required</span> : <span className="text-[10px]">Optional</span>}
                            </div>
                          </div>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Create Template Modal */}
      {showCreate && <CreateTemplateModal hdrs={hdrs} onClose={() => setShowCreate(false)} onCreated={() => { setShowCreate(false); fetchTemplates(); }} />}
    </div>
  );
}


function TemplateEditor({ template, hdrs, onSave, onCancel }) {
  const [name, setName] = useState(template.name);
  const [description, setDescription] = useState(template.description || '');
  const [category, setCategory] = useState(template.category || '');
  const [subtasks, setSubtasks] = useState(
    (template.subtasks || []).sort((a, b) => a.order - b.order).map(s => ({ ...s }))
  );
  const [saving, setSaving] = useState(false);

  const addSubtask = () => {
    setSubtasks([...subtasks, { name: '', description: '', order: subtasks.length + 1, estimated_hours: 0, is_mandatory: true }]);
  };

  const removeSubtask = (idx) => {
    const updated = subtasks.filter((_, i) => i !== idx).map((s, i) => ({ ...s, order: i + 1 }));
    setSubtasks(updated);
  };

  const updateSt = (idx, field, val) => {
    const updated = [...subtasks];
    updated[idx] = { ...updated[idx], [field]: val };
    setSubtasks(updated);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await fetch(`${API}/api/projects/templates/${template.id}`, {
        method: 'PUT', headers: hdrs(),
        body: JSON.stringify({ name, description, category, subtasks })
      });
      toast.success('Template updated');
      onSave();
    } catch { toast.error('Failed'); }
    finally { setSaving(false); }
  };

  return (
    <div className="space-y-3">
      <div className="grid grid-cols-3 gap-2">
        <Input value={name} onChange={e => setName(e.target.value)} placeholder="Template name" />
        <Input value={category} onChange={e => setCategory(e.target.value)} placeholder="Category" />
        <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="Description" />
      </div>
      <div className="space-y-1.5">
        {subtasks.map((s, i) => (
          <div key={i} className="flex items-center gap-2 bg-white rounded p-2 border">
            <span className="text-xs font-mono text-slate-400 w-5 text-right">{i + 1}.</span>
            <Input className="flex-1 h-8 text-sm" value={s.name} onChange={e => updateSt(i, 'name', e.target.value)} placeholder="Subtask name" />
            <Input className="w-48 h-8 text-sm" value={s.description} onChange={e => updateSt(i, 'description', e.target.value)} placeholder="Description" />
            <Input className="w-16 h-8 text-sm" type="number" value={s.estimated_hours} onChange={e => updateSt(i, 'estimated_hours', parseFloat(e.target.value) || 0)} placeholder="Hrs" />
            <label className="flex items-center gap-1 text-xs">
              <input type="checkbox" checked={s.is_mandatory} onChange={e => updateSt(i, 'is_mandatory', e.target.checked)} />Req
            </label>
            <button onClick={() => removeSubtask(i)} className="p-1 text-slate-300 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
          </div>
        ))}
      </div>
      <div className="flex items-center justify-between">
        <Button variant="outline" size="sm" onClick={addSubtask}><Plus className="w-3 h-3 mr-1" />Add Subtask</Button>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={onCancel}><X className="w-3 h-3 mr-1" />Cancel</Button>
          <Button size="sm" onClick={handleSave} disabled={saving} className="bg-[#0F62FE] text-white"><Save className="w-3 h-3 mr-1" />{saving ? 'Saving...' : 'Save'}</Button>
        </div>
      </div>
    </div>
  );
}


function CreateTemplateModal({ hdrs, onClose, onCreated }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [subtasks, setSubtasks] = useState([
    { name: '', description: '', order: 1, estimated_hours: 0, is_mandatory: true }
  ]);
  const [creating, setCreating] = useState(false);

  const addSubtask = () => {
    setSubtasks([...subtasks, { name: '', description: '', order: subtasks.length + 1, estimated_hours: 0, is_mandatory: true }]);
  };

  const removeSubtask = (idx) => {
    setSubtasks(subtasks.filter((_, i) => i !== idx).map((s, i) => ({ ...s, order: i + 1 })));
  };

  const updateSt = (idx, field, val) => {
    const updated = [...subtasks];
    updated[idx] = { ...updated[idx], [field]: val };
    setSubtasks(updated);
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!name) return toast.error('Name required');
    const validSt = subtasks.filter(s => s.name.trim());
    if (validSt.length === 0) return toast.error('Add at least one subtask');
    setCreating(true);
    try {
      const res = await fetch(`${API}/api/projects/templates`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ name, description, category, subtasks: validSt })
      });
      if (res.ok) { toast.success('Template created'); onCreated(); }
    } catch { toast.error('Failed'); }
    finally { setCreating(false); }
  };

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[80vh] overflow-y-auto" onClick={e => e.stopPropagation()} data-testid="create-template-modal">
        <div className="p-5 border-b sticky top-0 bg-white z-10">
          <h2 className="text-lg font-bold text-slate-900">New Task Template</h2>
          <p className="text-xs text-slate-500">Define a reusable task with sequential subtasks</p>
        </div>
        <form onSubmit={handleCreate} className="p-5 space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Name *</label>
              <Input value={name} onChange={e => setName(e.target.value)} placeholder="e.g., CCTV Installation" required data-testid="template-name-input" />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1">Category</label>
              <Input value={category} onChange={e => setCategory(e.target.value)} placeholder="e.g., Security" />
            </div>
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1">Description</label>
            <Input value={description} onChange={e => setDescription(e.target.value)} placeholder="Brief description" />
          </div>

          <div>
            <label className="text-sm font-medium text-slate-700 block mb-2">Subtasks (in order)</label>
            <div className="space-y-1.5">
              {subtasks.map((s, i) => (
                <div key={i} className="flex items-center gap-2 bg-slate-50 rounded p-2">
                  <span className="text-xs font-mono text-slate-400 w-5">{i + 1}.</span>
                  <Input className="flex-1 h-8 text-sm" value={s.name} onChange={e => updateSt(i, 'name', e.target.value)} placeholder="Subtask name" />
                  <Input className="w-14 h-8 text-sm" type="number" value={s.estimated_hours || ''} onChange={e => updateSt(i, 'estimated_hours', parseFloat(e.target.value) || 0)} placeholder="Hrs" />
                  {subtasks.length > 1 && (
                    <button type="button" onClick={() => removeSubtask(i)} className="p-0.5 text-slate-300 hover:text-red-500"><Trash2 className="w-3.5 h-3.5" /></button>
                  )}
                </div>
              ))}
            </div>
            <Button type="button" variant="outline" size="sm" className="mt-2" onClick={addSubtask}>
              <Plus className="w-3 h-3 mr-1" />Add Subtask
            </Button>
          </div>

          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={onClose}>Cancel</Button>
            <Button type="submit" disabled={creating} className="bg-[#0F62FE] text-white" data-testid="template-create-submit">
              {creating ? 'Creating...' : 'Create Template'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
