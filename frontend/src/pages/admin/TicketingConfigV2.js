import { useState, useEffect, useCallback } from 'react';
import {
  Ticket, FileText, GitBranch, Users, Shield, Clock, MessageSquare, Bell,
  Plus, Edit2, Trash2, ChevronRight, Save, X, AlertTriangle, CheckCircle,
  GripVertical, ArrowUp, ArrowDown, Settings, Copy, Mail, RefreshCw,
  UserCog, DollarSign, Calendar, Phone
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const getToken = () => localStorage.getItem('admin_token');
const headers = () => ({ Authorization: `Bearer ${getToken()}`, 'Content-Type': 'application/json' });

const tabs = [
  { id: 'help-topics', label: 'Help Topics', icon: Ticket },
  { id: 'forms', label: 'Forms', icon: FileText },
  { id: 'workflows', label: 'Workflows', icon: GitBranch },
  { id: 'technicians', label: 'Technicians', icon: UserCog },
  { id: 'teams', label: 'Teams', icon: Users },
  { id: 'roles', label: 'Roles', icon: Shield },
  { id: 'sla', label: 'SLA Policies', icon: Clock },
  { id: 'canned', label: 'Canned Responses', icon: MessageSquare },
  { id: 'priorities', label: 'Priorities', icon: AlertTriangle },
  { id: 'email', label: 'Email Inbox', icon: Mail },
];

const ConfigCard = ({ item, onEdit, onDelete, children }) => (
  <div className="border rounded-lg p-4 bg-white hover:border-blue-200 transition-colors" data-testid={`config-card-${item.id}`}>
    <div className="flex items-start justify-between">
      <div className="flex-1 min-w-0">
        <h4 className="text-sm font-semibold text-slate-800">{item.name}</h4>
        {item.description && <p className="text-xs text-slate-500 mt-0.5 line-clamp-2">{item.description}</p>}
        {children}
      </div>
      <div className="flex gap-1 ml-2 shrink-0">
        {onEdit && <button onClick={() => onEdit(item)} className="p-1 hover:bg-slate-100 rounded" data-testid={`edit-${item.id}`}><Edit2 className="w-3.5 h-3.5 text-slate-400" /></button>}
        {onDelete && !item.is_system && <button onClick={() => onDelete(item.id)} className="p-1 hover:bg-red-50 rounded" data-testid={`delete-${item.id}`}><Trash2 className="w-3.5 h-3.5 text-red-400" /></button>}
      </div>
    </div>
  </div>
);

// ========== HELP TOPICS TAB ==========
const HelpTopicsTab = () => {
  const [topics, setTopics] = useState([]);
  const [forms, setForms] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [teams, setTeams] = useState([]);
  const [slas, setSlas] = useState([]);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    try {
      const [t, f, w, tm, s] = await Promise.all([
        fetch(`${API}/api/ticketing/help-topics?include_inactive=true`, { headers: headers() }).then(r => r.json()),
        fetch(`${API}/api/ticketing/forms`, { headers: headers() }).then(r => r.json()),
        fetch(`${API}/api/ticketing/workflows`, { headers: headers() }).then(r => r.json()),
        fetch(`${API}/api/ticketing/teams`, { headers: headers() }).then(r => r.json()),
        fetch(`${API}/api/ticketing/sla-policies`, { headers: headers() }).then(r => r.json()),
      ]);
      setTopics(Array.isArray(t) ? t : []); setForms(Array.isArray(f) ? f : []);
      setWorkflows(Array.isArray(w) ? w : []); setTeams(Array.isArray(tm) ? tm : []);
      setSlas(Array.isArray(s) ? s : []);
    } catch { toast.error('Failed to load'); } finally { setLoading(false); }
  }, []);
  useEffect(() => { fetch_(); }, [fetch_]);

  const handleSave = async (data) => {
    try {
      const method = editing?.id ? 'PUT' : 'POST';
      const url = editing?.id ? `${API}/api/ticketing/help-topics/${editing.id}` : `${API}/api/ticketing/help-topics`;
      await fetch(url, { method, headers: headers(), body: JSON.stringify(data) });
      toast.success('Saved'); setEditing(null); fetch_();
    } catch { toast.error('Failed'); }
  };
  const handleDelete = async (id) => { if (!window.confirm('Delete?')) return; await fetch(`${API}/api/ticketing/help-topics/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Deleted'); fetch_(); };

  if (editing !== null) {
    return <HelpTopicEditor topic={editing} forms={forms} workflows={workflows} teams={teams} slas={slas} onSave={handleSave} onCancel={() => setEditing(null)} />;
  }
  return (
    <div data-testid="help-topics-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-slate-500">{topics.length} help topics</p>
        <Button size="sm" onClick={() => setEditing({})} data-testid="add-help-topic"><Plus className="w-4 h-4 mr-1" /> Add Help Topic</Button>
      </div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {topics.map(t => (
            <ConfigCard key={t.id} item={t} onEdit={setEditing} onDelete={handleDelete}>
              <div className="flex gap-2 mt-2 flex-wrap">
                {t.category && <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">{t.category}</span>}
                {t.form_id && <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded">Form</span>}
                {t.workflow_id && <span className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded">Workflow</span>}
                {!t.is_active && <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded">Inactive</span>}
              </div>
            </ConfigCard>
          ))}
        </div>
      )}
    </div>
  );
};

const HelpTopicEditor = ({ topic, forms, workflows, teams, slas, onSave, onCancel }) => {
  const [data, setData] = useState({
    name: topic.name || '', slug: topic.slug || '', description: topic.description || '',
    category: topic.category || 'support', form_id: topic.form_id || '', workflow_id: topic.workflow_id || '',
    default_team_id: topic.default_team_id || '', sla_policy_id: topic.sla_policy_id || '',
    default_priority: topic.default_priority || 'medium', is_active: topic.is_active !== false,
    is_public: topic.is_public !== false, require_company: topic.require_company !== false,
    require_contact: topic.require_contact !== false, require_device: topic.require_device || false,
  });
  const set = (k, v) => setData(d => ({ ...d, [k]: v }));
  return (
    <div className="bg-white border rounded-lg p-5" data-testid="help-topic-editor">
      <div className="flex justify-between mb-4">
        <h3 className="text-lg font-semibold">{topic.id ? 'Edit' : 'New'} Help Topic</h3>
        <button onClick={onCancel}><X className="w-5 h-5 text-slate-400" /></button>
      </div>
      <div className="grid grid-cols-2 gap-4">
        <div><label className="text-sm font-medium block mb-1">Name *</label><Input value={data.name} onChange={e => { set('name', e.target.value); if (!topic.id) set('slug', e.target.value.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '')); }} data-testid="topic-name" /></div>
        <div><label className="text-sm font-medium block mb-1">Slug</label><Input value={data.slug} onChange={e => set('slug', e.target.value)} /></div>
        <div className="col-span-2"><label className="text-sm font-medium block mb-1">Description</label><textarea className="w-full border rounded-lg px-3 py-2 text-sm" value={data.description} onChange={e => set('description', e.target.value)} /></div>
        <div><label className="text-sm font-medium block mb-1">Category</label><select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.category} onChange={e => set('category', e.target.value)}><option value="support">Support</option><option value="sales">Sales</option><option value="operations">Operations</option><option value="general">General</option></select></div>
        <div><label className="text-sm font-medium block mb-1">Priority</label><select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.default_priority} onChange={e => set('default_priority', e.target.value)}><option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option></select></div>
        <div><label className="text-sm font-medium block mb-1">Form</label><select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.form_id} onChange={e => set('form_id', e.target.value)}><option value="">None</option>{forms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}</select></div>
        <div><label className="text-sm font-medium block mb-1">Workflow</label><select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.workflow_id} onChange={e => set('workflow_id', e.target.value)}><option value="">None</option>{workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}</select></div>
        <div><label className="text-sm font-medium block mb-1">Default Team</label><select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.default_team_id} onChange={e => set('default_team_id', e.target.value)}><option value="">None</option>{teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}</select></div>
        <div><label className="text-sm font-medium block mb-1">SLA Policy</label><select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.sla_policy_id} onChange={e => set('sla_policy_id', e.target.value)}><option value="">None</option>{slas.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}</select></div>
        <div className="col-span-2 flex gap-4 flex-wrap">
          {[['is_active','Active'],['is_public','Public'],['require_company','Require Company'],['require_contact','Require Contact'],['require_device','Require Device']].map(([k,l]) => (
            <label key={k} className="flex items-center gap-2 text-sm"><input type="checkbox" checked={data[k]} onChange={e => set(k, e.target.checked)} /> {l}</label>
          ))}
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-5 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => onSave(data)} data-testid="save-topic"><Save className="w-4 h-4 mr-1" /> Save</Button>
      </div>
    </div>
  );
};

// ========== FORM BUILDER TAB ==========
const FIELD_TYPES = [
  { value: 'text', label: 'Text' }, { value: 'textarea', label: 'Textarea' }, { value: 'number', label: 'Number' },
  { value: 'select', label: 'Dropdown' }, { value: 'date', label: 'Date' }, { value: 'email', label: 'Email' },
  { value: 'phone', label: 'Phone' }, { value: 'checkbox', label: 'Checkbox' }, { value: 'url', label: 'URL' },
];

const FormsTab = () => {
  const [forms, setForms] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`${API}/api/ticketing/forms`, { headers: headers() });
    setForms(await res.json()); setLoading(false);
  }, []);
  useEffect(() => { fetch_(); }, [fetch_]);

  const handleSave = async (formData) => {
    try {
      const method = editing?.id ? 'PUT' : 'POST';
      const url = editing?.id ? `${API}/api/ticketing/forms/${editing.id}` : `${API}/api/ticketing/forms`;
      const res = await fetch(url, { method, headers: headers(), body: JSON.stringify(formData) });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      toast.success('Form saved'); setEditing(null); fetch_();
    } catch (e) { toast.error(e.message); }
  };

  const handleDelete = async (id) => { if (!window.confirm('Delete this form?')) return; await fetch(`${API}/api/ticketing/forms/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Deleted'); fetch_(); };

  if (editing !== null) return <FormBuilder form={editing} onSave={handleSave} onCancel={() => setEditing(null)} />;

  return (
    <div data-testid="forms-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-slate-500">{forms.length} forms</p>
        <Button size="sm" onClick={() => setEditing({})} data-testid="add-form"><Plus className="w-4 h-4 mr-1" /> New Form</Button>
      </div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {forms.map(f => (
            <ConfigCard key={f.id} item={f} onEdit={setEditing} onDelete={handleDelete}>
              <p className="text-xs text-slate-400 mt-1">{f.fields?.length || 0} fields</p>
              <div className="flex gap-1 mt-2 flex-wrap">
                {(f.fields || []).slice(0, 5).map(field => (
                  <span key={field.id} className="text-xs bg-slate-50 text-slate-500 px-1.5 py-0.5 rounded">{field.label}</span>
                ))}
              </div>
            </ConfigCard>
          ))}
        </div>
      )}
    </div>
  );
};

const FormBuilder = ({ form, onSave, onCancel }) => {
  const [name, setName] = useState(form.name || '');
  const [description, setDescription] = useState(form.description || '');
  const [fields, setFields] = useState(form.fields || []);

  const addField = () => {
    setFields(f => [...f, { id: `field_${Date.now()}`, slug: '', label: '', field_type: 'text', required: false, placeholder: '', options: [], width: 'half', order: f.length }]);
  };

  const updateField = (idx, key, val) => setFields(f => f.map((field, i) => i === idx ? { ...field, [key]: val } : field));
  const removeField = (idx) => setFields(f => f.filter((_, i) => i !== idx));
  const moveField = (idx, dir) => {
    const newFields = [...fields];
    const swap = idx + dir;
    if (swap < 0 || swap >= newFields.length) return;
    [newFields[idx], newFields[swap]] = [newFields[swap], newFields[idx]];
    newFields.forEach((f, i) => f.order = i);
    setFields(newFields);
  };

  return (
    <div className="bg-white border rounded-lg" data-testid="form-builder">
      <div className="flex justify-between items-center p-5 border-b">
        <h3 className="text-lg font-semibold">{form.id ? 'Edit' : 'New'} Form</h3>
        <button onClick={onCancel}><X className="w-5 h-5 text-slate-400" /></button>
      </div>
      <div className="p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="text-sm font-medium block mb-1">Form Name *</label><Input value={name} onChange={e => setName(e.target.value)} data-testid="form-name" /></div>
          <div><label className="text-sm font-medium block mb-1">Description</label><Input value={description} onChange={e => setDescription(e.target.value)} /></div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-3">
            <h4 className="text-sm font-semibold text-slate-700">Fields ({fields.length})</h4>
            <Button size="sm" variant="outline" onClick={addField} data-testid="add-field-btn"><Plus className="w-3.5 h-3.5 mr-1" /> Add Field</Button>
          </div>

          <div className="space-y-3">
            {fields.map((field, idx) => (
              <div key={field.id} className="border rounded-lg p-3 bg-slate-50" data-testid={`field-${idx}`}>
                <div className="flex items-center gap-2 mb-2">
                  <GripVertical className="w-4 h-4 text-slate-300 cursor-grab" />
                  <span className="text-xs font-mono text-slate-400">#{idx + 1}</span>
                  <div className="flex-1" />
                  <button onClick={() => moveField(idx, -1)} disabled={idx === 0} className="p-1 hover:bg-slate-200 rounded disabled:opacity-30"><ArrowUp className="w-3.5 h-3.5" /></button>
                  <button onClick={() => moveField(idx, 1)} disabled={idx === fields.length - 1} className="p-1 hover:bg-slate-200 rounded disabled:opacity-30"><ArrowDown className="w-3.5 h-3.5" /></button>
                  <button onClick={() => removeField(idx)} className="p-1 hover:bg-red-100 rounded"><Trash2 className="w-3.5 h-3.5 text-red-400" /></button>
                </div>
                <div className="grid grid-cols-4 gap-2">
                  <div><label className="text-xs text-slate-500 block mb-0.5">Label *</label>
                    <Input className="text-sm" value={field.label} onChange={e => { updateField(idx, 'label', e.target.value); if (!form.id) updateField(idx, 'slug', e.target.value.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')); }} /></div>
                  <div><label className="text-xs text-slate-500 block mb-0.5">Slug</label>
                    <Input className="text-sm" value={field.slug} onChange={e => updateField(idx, 'slug', e.target.value)} /></div>
                  <div><label className="text-xs text-slate-500 block mb-0.5">Type</label>
                    <select className="w-full border rounded-md px-2 py-1.5 text-sm" value={field.field_type} onChange={e => updateField(idx, 'field_type', e.target.value)}>
                      {FIELD_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                    </select></div>
                  <div className="flex items-end gap-3">
                    <label className="flex items-center gap-1.5 text-xs"><input type="checkbox" checked={field.required} onChange={e => updateField(idx, 'required', e.target.checked)} /> Required</label>
                    <select className="border rounded-md px-2 py-1 text-xs" value={field.width || 'half'} onChange={e => updateField(idx, 'width', e.target.value)}>
                      <option value="half">Half</option><option value="full">Full</option>
                    </select>
                  </div>
                </div>
                {field.field_type === 'select' && (
                  <div className="mt-2">
                    <label className="text-xs text-slate-500 block mb-0.5">Options (comma-separated)</label>
                    <Input className="text-sm" value={(field.options || []).map(o => o.label || o.value).join(', ')}
                      onChange={e => updateField(idx, 'options', e.target.value.split(',').map(v => ({ label: v.trim(), value: v.trim().toLowerCase().replace(/\s+/g, '_') })).filter(o => o.label))}
                      placeholder="Option 1, Option 2, Option 3" />
                  </div>
                )}
                <div className="mt-2"><label className="text-xs text-slate-500 block mb-0.5">Placeholder</label>
                  <Input className="text-sm" value={field.placeholder || ''} onChange={e => updateField(idx, 'placeholder', e.target.value)} /></div>
              </div>
            ))}
          </div>
          {fields.length === 0 && <p className="text-center py-8 text-sm text-slate-400 border rounded-lg border-dashed">No fields yet. Click "Add Field" to start building your form.</p>}
        </div>
      </div>
      <div className="flex justify-end gap-2 p-5 border-t">
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => { if (!name.trim()) { toast.error('Form name required'); return; } onSave({ name, description, slug: name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''), fields: fields.map((f, i) => ({ ...f, order: i })) }); }} data-testid="save-form"><Save className="w-4 h-4 mr-1" /> Save Form</Button>
      </div>
    </div>
  );
};

// ========== WORKFLOW DESIGNER TAB ==========
const STAGE_TYPES = [
  { value: 'initial', label: 'Initial', color: '#3B82F6' },
  { value: 'in_progress', label: 'In Progress', color: '#F59E0B' },
  { value: 'waiting', label: 'Waiting', color: '#8B5CF6' },
  { value: 'terminal_success', label: 'Resolved/Success', color: '#10B981' },
  { value: 'terminal_failure', label: 'Cancelled/Failed', color: '#EF4444' },
];

const INPUT_TYPES = [
  { value: '', label: 'None' }, { value: 'assign_engineer', label: 'Assign Engineer' },
  { value: 'schedule_visit', label: 'Schedule Visit' }, { value: 'diagnosis', label: 'Diagnosis Form' },
  { value: 'resolution', label: 'Resolution Notes' }, { value: 'parts_list', label: 'Parts List' },
  { value: 'quotation', label: 'Quotation' },
];

const WorkflowsTab = () => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(null);

  const fetch_ = useCallback(async () => {
    setLoading(true);
    const res = await fetch(`${API}/api/ticketing/workflows`, { headers: headers() });
    setWorkflows(await res.json()); setLoading(false);
  }, []);
  useEffect(() => { fetch_(); }, [fetch_]);

  const handleSave = async (data) => {
    try {
      const method = editing?.id ? 'PUT' : 'POST';
      const url = editing?.id ? `${API}/api/ticketing/workflows/${editing.id}` : `${API}/api/ticketing/workflows`;
      const res = await fetch(url, { method, headers: headers(), body: JSON.stringify(data) });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      toast.success('Workflow saved'); setEditing(null); fetch_();
    } catch (e) { toast.error(e.message); }
  };

  const handleDelete = async (id) => { if (!window.confirm('Delete this workflow?')) return; await fetch(`${API}/api/ticketing/workflows/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Deleted'); fetch_(); };

  if (editing !== null) return <WorkflowDesigner workflow={editing} onSave={handleSave} onCancel={() => setEditing(null)} />;

  const stageColors = { initial: 'bg-blue-100 text-blue-700', in_progress: 'bg-yellow-100 text-yellow-700', waiting: 'bg-purple-100 text-purple-700', terminal_success: 'bg-green-100 text-green-700', terminal_failure: 'bg-red-100 text-red-700' };

  return (
    <div data-testid="workflows-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-slate-500">{workflows.length} workflows</p>
        <Button size="sm" onClick={() => setEditing({})} data-testid="add-workflow"><Plus className="w-4 h-4 mr-1" /> New Workflow</Button>
      </div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="space-y-3">
          {workflows.map(w => (
            <div key={w.id} className="border rounded-lg bg-white p-4" data-testid={`workflow-${w.id}`}>
              <div className="flex items-center justify-between mb-3">
                <div><h4 className="text-sm font-semibold">{w.name}</h4><p className="text-xs text-slate-500">{w.stages?.length || 0} stages</p></div>
                <div className="flex gap-1">
                  <button onClick={() => setEditing(w)} className="p-1 hover:bg-slate-100 rounded"><Edit2 className="w-4 h-4 text-slate-400" /></button>
                  {!w.is_system && <button onClick={() => handleDelete(w.id)} className="p-1 hover:bg-red-50 rounded"><Trash2 className="w-4 h-4 text-red-400" /></button>}
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {[...(w.stages || [])].sort((a, b) => a.order - b.order).map((stage, i) => (
                  <div key={stage.id} className="flex items-center gap-1">
                    <span className={`text-xs px-2 py-1 rounded-full ${stageColors[stage.stage_type] || 'bg-slate-100 text-slate-600'}`}>{stage.name}</span>
                    {i < (w.stages || []).length - 1 && <ChevronRight className="w-3 h-3 text-slate-300" />}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const WorkflowDesigner = ({ workflow, onSave, onCancel }) => {
  const [name, setName] = useState(workflow.name || '');
  const [description, setDescription] = useState(workflow.description || '');
  const [teams, setTeams] = useState([]);
  const [stages, setStages] = useState(() => {
    const s = workflow.stages ? [...workflow.stages].sort((a, b) => a.order - b.order) : [];
    return s;
  });
  const [expandedStage, setExpandedStage] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/ticketing/teams`, { headers: headers() }).then(r => r.json()).then(d => setTeams(Array.isArray(d) ? d : []));
  }, []);

  const addStage = () => {
    const id = `stage_${Date.now()}`;
    setStages(s => [...s, { id, name: '', slug: '', stage_type: 'in_progress', order: s.length, transitions: [], entry_actions: [], assigned_team_id: '' }]);
    setExpandedStage(id);
  };

  const updateStage = (id, key, val) => setStages(s => s.map(st => st.id === id ? { ...st, [key]: val } : st));
  const removeStage = (id) => {
    setStages(s => s.filter(st => st.id !== id).map((st, i) => ({
      ...st, order: i, transitions: st.transitions.filter(t => t.to_stage_id !== id)
    })));
  };
  const moveStage = (idx, dir) => {
    const s = [...stages]; const swap = idx + dir;
    if (swap < 0 || swap >= s.length) return;
    [s[idx], s[swap]] = [s[swap], s[idx]];
    s.forEach((st, i) => st.order = i);
    setStages(s);
  };

  const addTransition = (stageId) => {
    setStages(s => s.map(st => st.id === stageId ? {
      ...st, transitions: [...st.transitions, { id: `trans_${Date.now()}`, to_stage_id: '', label: '', color: 'primary', requires_input: '', order: st.transitions.length }]
    } : st));
  };
  const updateTransition = (stageId, transId, key, val) => {
    setStages(s => s.map(st => st.id === stageId ? {
      ...st, transitions: st.transitions.map(t => t.id === transId ? { ...t, [key]: val } : t)
    } : st));
  };
  const removeTransition = (stageId, transId) => {
    setStages(s => s.map(st => st.id === stageId ? {
      ...st, transitions: st.transitions.filter(t => t.id !== transId)
    } : st));
  };

  return (
    <div className="bg-white border rounded-lg" data-testid="workflow-designer">
      <div className="flex justify-between items-center p-5 border-b">
        <h3 className="text-lg font-semibold">{workflow.id ? 'Edit' : 'New'} Workflow</h3>
        <button onClick={onCancel}><X className="w-5 h-5 text-slate-400" /></button>
      </div>
      <div className="p-5 space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div><label className="text-sm font-medium block mb-1">Workflow Name *</label><Input value={name} onChange={e => setName(e.target.value)} data-testid="workflow-name" /></div>
          <div><label className="text-sm font-medium block mb-1">Description</label><Input value={description} onChange={e => setDescription(e.target.value)} /></div>
        </div>

        <div>
          <div className="flex justify-between items-center mb-3">
            <h4 className="text-sm font-semibold text-slate-700">Stages ({stages.length})</h4>
            <Button size="sm" variant="outline" onClick={addStage} data-testid="add-stage-btn"><Plus className="w-3.5 h-3.5 mr-1" /> Add Stage</Button>
          </div>

          <div className="space-y-2">
            {stages.map((stage, idx) => {
              const stageType = STAGE_TYPES.find(t => t.value === stage.stage_type);
              const isExpanded = expandedStage === stage.id;
              return (
                <div key={stage.id} className="border rounded-lg overflow-hidden" data-testid={`designer-stage-${idx}`}>
                  <div className="flex items-center gap-2 p-3 bg-slate-50 cursor-pointer" onClick={() => setExpandedStage(isExpanded ? null : stage.id)}>
                    <GripVertical className="w-4 h-4 text-slate-300" />
                    <div className="w-3 h-3 rounded-full" style={{ backgroundColor: stageType?.color || '#6B7280' }} />
                    <span className="text-sm font-medium flex-1">{stage.name || '(unnamed)'}</span>
                    <span className="text-xs text-slate-400">{stageType?.label}</span>
                    <span className="text-xs text-slate-300">{stage.transitions.length} transitions</span>
                    <button onClick={e => { e.stopPropagation(); moveStage(idx, -1); }} disabled={idx === 0} className="p-1 hover:bg-slate-200 rounded disabled:opacity-30"><ArrowUp className="w-3.5 h-3.5" /></button>
                    <button onClick={e => { e.stopPropagation(); moveStage(idx, 1); }} disabled={idx === stages.length - 1} className="p-1 hover:bg-slate-200 rounded disabled:opacity-30"><ArrowDown className="w-3.5 h-3.5" /></button>
                    <button onClick={e => { e.stopPropagation(); removeStage(stage.id); }} className="p-1 hover:bg-red-100 rounded"><Trash2 className="w-3.5 h-3.5 text-red-400" /></button>
                    <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                  </div>
                  {isExpanded && (
                    <div className="p-4 border-t space-y-3">
                      <div className="grid grid-cols-4 gap-3">
                        <div><label className="text-xs text-slate-500 block mb-0.5">Name *</label><Input className="text-sm" value={stage.name} onChange={e => { updateStage(stage.id, 'name', e.target.value); updateStage(stage.id, 'slug', e.target.value.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_]/g, '')); }} /></div>
                        <div><label className="text-xs text-slate-500 block mb-0.5">Type *</label><select className="w-full border rounded-md px-2 py-1.5 text-sm" value={stage.stage_type} onChange={e => updateStage(stage.id, 'stage_type', e.target.value)}>
                          {STAGE_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                        </select></div>
                        <div><label className="text-xs text-slate-500 block mb-0.5">Assigned Team</label><select className="w-full border rounded-md px-2 py-1.5 text-sm" value={stage.assigned_team_id || ''} onChange={e => updateStage(stage.id, 'assigned_team_id', e.target.value)}>
                          <option value="">None</option>{teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
                        </select></div>
                        <div><label className="text-xs text-slate-500 block mb-0.5">Slug</label><Input className="text-sm" value={stage.slug || ''} onChange={e => updateStage(stage.id, 'slug', e.target.value)} /></div>
                      </div>

                      <div>
                        <div className="flex justify-between items-center mb-2">
                          <h5 className="text-xs font-semibold text-slate-600">Transitions ({stage.transitions.length})</h5>
                          <Button size="sm" variant="ghost" onClick={() => addTransition(stage.id)} className="h-7 text-xs"><Plus className="w-3 h-3 mr-1" /> Add</Button>
                        </div>
                        {stage.transitions.map(trans => (
                          <div key={trans.id} className="flex items-center gap-2 mb-2 bg-white p-2 rounded border">
                            <Input className="text-xs flex-1" placeholder="Button label" value={trans.label} onChange={e => updateTransition(stage.id, trans.id, 'label', e.target.value)} />
                            <select className="border rounded px-2 py-1 text-xs w-40" value={trans.to_stage_id} onChange={e => updateTransition(stage.id, trans.id, 'to_stage_id', e.target.value)}>
                              <option value="">Target stage...</option>
                              {stages.filter(s => s.id !== stage.id).map(s => <option key={s.id} value={s.id}>{s.name || '(unnamed)'}</option>)}
                            </select>
                            <select className="border rounded px-2 py-1 text-xs w-28" value={trans.requires_input || ''} onChange={e => updateTransition(stage.id, trans.id, 'requires_input', e.target.value)}>
                              {INPUT_TYPES.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                            </select>
                            <select className="border rounded px-1.5 py-1 text-xs w-20" value={trans.color || 'primary'} onChange={e => updateTransition(stage.id, trans.id, 'color', e.target.value)}>
                              <option value="primary">Blue</option><option value="success">Green</option><option value="warning">Amber</option><option value="danger">Red</option>
                            </select>
                            <button onClick={() => removeTransition(stage.id, trans.id)} className="p-1 hover:bg-red-50 rounded"><X className="w-3.5 h-3.5 text-red-400" /></button>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
          {stages.length === 0 && <p className="text-center py-8 text-sm text-slate-400 border rounded-lg border-dashed">No stages. Click "Add Stage" to design your workflow.</p>}
        </div>
      </div>
      <div className="flex justify-end gap-2 p-5 border-t">
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => {
          if (!name.trim()) { toast.error('Workflow name required'); return; }
          if (stages.length === 0) { toast.error('Add at least one stage'); return; }
          onSave({ name, description, slug: name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, ''), stages: stages.map((s, i) => ({ ...s, order: i })) });
        }} data-testid="save-workflow"><Save className="w-4 h-4 mr-1" /> Save Workflow</Button>
      </div>
    </div>
  );
};

// ========== TEAMS TAB ==========
const TeamsTab = () => {
  const [teams, setTeams] = useState([]); const [loading, setLoading] = useState(true); const [editing, setEditing] = useState(null);
  const fetch_ = useCallback(async () => { setLoading(true); const r = await fetch(`${API}/api/ticketing/teams`, { headers: headers() }); setTeams(await r.json()); setLoading(false); }, []);
  useEffect(() => { fetch_(); }, [fetch_]);
  const handleSave = async (data) => {
    const method = editing?.id ? 'PUT' : 'POST';
    const url = editing?.id ? `${API}/api/ticketing/teams/${editing.id}` : `${API}/api/ticketing/teams`;
    await fetch(url, { method, headers: headers(), body: JSON.stringify(data) }); toast.success('Saved'); setEditing(null); fetch_();
  };
  const handleDelete = async (id) => { if (!window.confirm('Delete?')) return; await fetch(`${API}/api/ticketing/teams/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Deleted'); fetch_(); };

  if (editing !== null) {
    const d = editing;
    return <GenericEditor title="Team" fields={[
      { key: 'name', label: 'Name *', type: 'text', value: d.name || '' },
      { key: 'slug', label: 'Slug', type: 'text', value: d.slug || '' },
      { key: 'description', label: 'Description', type: 'textarea', value: d.description || '' },
      { key: 'assignment_method', label: 'Assignment', type: 'select', value: d.assignment_method || 'manual', options: [{ value: 'manual', label: 'Manual' }, { value: 'round_robin', label: 'Round Robin' }, { value: 'load_balanced', label: 'Load Balanced' }] },
    ]} onSave={handleSave} onCancel={() => setEditing(null)} />;
  }
  return (
    <div data-testid="teams-tab">
      <div className="flex justify-between items-center mb-4"><p className="text-sm text-slate-500">{teams.length} teams</p><Button size="sm" onClick={() => setEditing({})}><Plus className="w-4 h-4 mr-1" /> Add Team</Button></div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : <div className="grid grid-cols-2 gap-3">{teams.map(t => <ConfigCard key={t.id} item={t} onEdit={setEditing} onDelete={handleDelete}><div className="flex gap-2 mt-2"><span className="text-xs text-slate-400">{t.members?.length || 0} members</span><span className="text-xs text-slate-400 capitalize">{t.assignment_method}</span></div></ConfigCard>)}</div>}
    </div>
  );
};

// ========== ROLES TAB ==========
const RoleEditor = ({ role, onSave, onCancel }) => {
  const [name, setName] = useState(role.name || '');
  const [description, setDescription] = useState(role.description || '');
  const [perms, setPerms] = useState(role.permissions || []);
  return (
    <div className="bg-white border rounded-lg p-5" data-testid="role-editor">
      <div className="flex justify-between mb-4"><h3 className="text-lg font-semibold">{role.id ? 'Edit' : 'New'} Role</h3><button onClick={onCancel}><X className="w-5 h-5 text-slate-400" /></button></div>
      <div className="grid grid-cols-2 gap-4">
        <div><label className="text-sm font-medium block mb-1">Name *</label><Input value={name} onChange={e => setName(e.target.value)} /></div>
        <div className="col-span-2"><label className="text-sm font-medium block mb-1">Description</label><textarea className="w-full border rounded-lg px-3 py-2 text-sm" value={description} onChange={e => setDescription(e.target.value)} /></div>
      </div>
      <div className="mt-4"><label className="text-sm font-medium block mb-2">Permissions</label>
        <div className="grid grid-cols-3 gap-2">{PERMISSIONS.map(p => (
          <label key={p} className="flex items-center gap-2 text-xs"><input type="checkbox" checked={perms.includes(p)} onChange={e => setPerms(prev => e.target.checked ? [...prev, p] : prev.filter(x => x !== p))} />{p}</label>
        ))}</div>
      </div>
      <div className="flex justify-end gap-2 mt-5 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => onSave({ name, description, permissions: perms })}><Save className="w-4 h-4 mr-1" /> Save</Button>
      </div>
    </div>
  );
};

const PERMISSIONS = ['tickets.view', 'tickets.create', 'tickets.edit', 'tickets.delete', 'tickets.assign', 'tickets.close', 'tickets.transfer', 'tasks.view', 'tasks.edit', 'tasks.complete', 'config.manage', 'reports.view'];
const RolesTab = () => {
  const [roles, setRoles] = useState([]); const [loading, setLoading] = useState(true); const [editing, setEditing] = useState(null);
  const fetch_ = useCallback(async () => { setLoading(true); const r = await fetch(`${API}/api/ticketing/roles`, { headers: headers() }); setRoles(await r.json()); setLoading(false); }, []);
  useEffect(() => { fetch_(); }, [fetch_]);
  const handleSave = async (data) => {
    const method = editing?.id ? 'PUT' : 'POST';
    const url = editing?.id ? `${API}/api/ticketing/roles/${editing.id}` : `${API}/api/ticketing/roles`;
    await fetch(url, { method, headers: headers(), body: JSON.stringify(data) }); toast.success('Saved'); setEditing(null); fetch_();
  };
  const handleDelete = async (id) => { if (!window.confirm('Delete?')) return; await fetch(`${API}/api/ticketing/roles/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Deleted'); fetch_(); };

  if (editing !== null) {
    return <RoleEditor role={editing} onSave={handleSave} onCancel={() => setEditing(null)} />;
  }
  return (
    <div data-testid="roles-tab">
      <div className="flex justify-between items-center mb-4"><p className="text-sm text-slate-500">{roles.length} roles</p><Button size="sm" onClick={() => setEditing({})}><Plus className="w-4 h-4 mr-1" /> Add Role</Button></div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : <div className="grid grid-cols-2 gap-3">{roles.map(r => <ConfigCard key={r.id} item={r} onEdit={setEditing} onDelete={handleDelete}><div className="flex gap-1 mt-2 flex-wrap">{(r.permissions || []).slice(0, 3).map(p => <span key={p} className="text-xs bg-slate-50 text-slate-500 px-1.5 py-0.5 rounded">{p}</span>)}{(r.permissions || []).length > 3 && <span className="text-xs text-slate-400">+{r.permissions.length - 3}</span>}</div></ConfigCard>)}</div>}
    </div>
  );
};

// ========== SLA TAB ==========
const SLATab = () => {
  const [policies, setPolicies] = useState([]); const [loading, setLoading] = useState(true); const [editing, setEditing] = useState(null);
  const fetch_ = useCallback(async () => { setLoading(true); const r = await fetch(`${API}/api/ticketing/sla-policies`, { headers: headers() }); setPolicies(await r.json()); setLoading(false); }, []);
  useEffect(() => { fetch_(); }, [fetch_]);
  const handleSave = async (data) => {
    data.response_time_hours = parseFloat(data.response_time_hours) || 4;
    data.resolution_time_hours = parseFloat(data.resolution_time_hours) || 24;
    data.escalation_after_hours = parseFloat(data.escalation_after_hours) || 0;
    data.escalation_enabled = data.escalation_after_hours > 0;
    const method = editing?.id ? 'PUT' : 'POST';
    const url = editing?.id ? `${API}/api/ticketing/sla-policies/${editing.id}` : `${API}/api/ticketing/sla-policies`;
    await fetch(url, { method, headers: headers(), body: JSON.stringify(data) }); toast.success('Saved'); setEditing(null); fetch_();
  };
  const handleDelete = async (id) => { if (!window.confirm('Delete?')) return; await fetch(`${API}/api/ticketing/sla-policies/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Deleted'); fetch_(); };

  if (editing !== null) {
    return <GenericEditor title="SLA Policy" fields={[
      { key: 'name', label: 'Name *', type: 'text', value: editing.name || '' },
      { key: 'description', label: 'Description', type: 'textarea', value: editing.description || '' },
      { key: 'response_time_hours', label: 'Response Time (hours)', type: 'number', value: editing.response_time_hours || 4 },
      { key: 'resolution_time_hours', label: 'Resolution Time (hours)', type: 'number', value: editing.resolution_time_hours || 24 },
      { key: 'escalation_after_hours', label: 'Escalate After (hours, 0=disabled)', type: 'number', value: editing.escalation_after_hours || 0 },
    ]} onSave={handleSave} onCancel={() => setEditing(null)} />;
  }
  return (
    <div data-testid="sla-tab">
      <div className="flex justify-between items-center mb-4"><p className="text-sm text-slate-500">{policies.length} SLA policies</p><Button size="sm" onClick={() => setEditing({})}><Plus className="w-4 h-4 mr-1" /> Add SLA</Button></div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : <div className="grid grid-cols-2 gap-3">{policies.map(p => <ConfigCard key={p.id} item={p} onEdit={setEditing} onDelete={handleDelete}><div className="flex gap-3 mt-2 text-xs text-slate-500"><span>Response: {p.response_time_hours}h</span><span>Resolution: {p.resolution_time_hours}h</span>{p.escalation_enabled && <span className="text-orange-500">Esc: {p.escalation_after_hours}h</span>}</div></ConfigCard>)}</div>}
    </div>
  );
};

// ========== CANNED TAB ==========
const CannedTab = () => {
  const [responses, setResponses] = useState([]); const [loading, setLoading] = useState(true); const [editing, setEditing] = useState(null);
  const fetch_ = useCallback(async () => { setLoading(true); const r = await fetch(`${API}/api/ticketing/canned-responses`, { headers: headers() }); setResponses(await r.json()); setLoading(false); }, []);
  useEffect(() => { fetch_(); }, [fetch_]);
  const handleSave = async (data) => {
    const method = editing?.id ? 'PUT' : 'POST';
    const url = editing?.id ? `${API}/api/ticketing/canned-responses/${editing.id}` : `${API}/api/ticketing/canned-responses`;
    await fetch(url, { method, headers: headers(), body: JSON.stringify(data) }); toast.success('Saved'); setEditing(null); fetch_();
  };
  const handleDelete = async (id) => { if (!window.confirm('Delete?')) return; await fetch(`${API}/api/ticketing/canned-responses/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Deleted'); fetch_(); };

  if (editing !== null) {
    return <GenericEditor title="Canned Response" fields={[
      { key: 'name', label: 'Title *', type: 'text', value: editing.name || '' },
      { key: 'category', label: 'Category', type: 'select', value: editing.category || 'general', options: [{ value: 'general', label: 'General' }, { value: 'greeting', label: 'Greeting' }, { value: 'troubleshooting', label: 'Troubleshooting' }, { value: 'closure', label: 'Closure' }, { value: 'escalation', label: 'Escalation' }] },
      { key: 'body', label: 'Response Body *', type: 'textarea', value: editing.body || '' },
    ]} onSave={handleSave} onCancel={() => setEditing(null)} />;
  }
  return (
    <div data-testid="canned-tab">
      <div className="flex justify-between items-center mb-4"><p className="text-sm text-slate-500">{responses.length} canned responses</p><Button size="sm" onClick={() => setEditing({})}><Plus className="w-4 h-4 mr-1" /> Add Response</Button></div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : <div className="grid grid-cols-2 gap-3">{responses.map(r => <ConfigCard key={r.id} item={r} onEdit={setEditing} onDelete={handleDelete}>{r.category && <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded mt-1 inline-block">{r.category}</span>}<p className="text-xs text-slate-400 mt-1 line-clamp-2">{r.body}</p></ConfigCard>)}</div>}
    </div>
  );
};

// ========== PRIORITIES TAB ==========
const PrioritiesTab = () => {
  const [priorities, setPriorities] = useState([]); const [loading, setLoading] = useState(true); const [editing, setEditing] = useState(null);
  const fetch_ = useCallback(async () => { setLoading(true); const r = await fetch(`${API}/api/ticketing/priorities`, { headers: headers() }); setPriorities(await r.json()); setLoading(false); }, []);
  useEffect(() => { fetch_(); }, [fetch_]);
  const handleSave = async (data) => {
    data.sla_multiplier = parseFloat(data.sla_multiplier) || 1;
    const method = editing?.id ? 'PUT' : 'POST';
    const url = editing?.id ? `${API}/api/ticketing/priorities/${editing.id}` : `${API}/api/ticketing/priorities`;
    await fetch(url, { method, headers: headers(), body: JSON.stringify(data) }); toast.success('Saved'); setEditing(null); fetch_();
  };
  const handleDelete = async (id) => { if (!window.confirm('Delete?')) return; await fetch(`${API}/api/ticketing/priorities/${id}`, { method: 'DELETE', headers: headers() }); toast.success('Deleted'); fetch_(); };

  if (editing !== null) {
    return <GenericEditor title="Priority" fields={[
      { key: 'name', label: 'Name *', type: 'text', value: editing.name || '' },
      { key: 'color', label: 'Color', type: 'text', value: editing.color || '#3B82F6' },
      { key: 'sla_multiplier', label: 'SLA Multiplier', type: 'number', value: editing.sla_multiplier || 1 },
    ]} onSave={handleSave} onCancel={() => setEditing(null)} />;
  }
  return (
    <div data-testid="priorities-tab">
      <div className="flex justify-between items-center mb-4"><p className="text-sm text-slate-500">{priorities.length} priorities</p><Button size="sm" onClick={() => setEditing({})}><Plus className="w-4 h-4 mr-1" /> Add Priority</Button></div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : <div className="grid grid-cols-2 gap-3">{priorities.map(p => <ConfigCard key={p.id} item={p} onEdit={setEditing} onDelete={handleDelete}><div className="flex items-center gap-2 mt-2"><div className="w-3 h-3 rounded-full" style={{ backgroundColor: p.color }} /><span className="text-xs text-slate-400">SLA x{p.sla_multiplier}</span>{p.is_default && <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">Default</span>}</div></ConfigCard>)}</div>}
    </div>
  );
};

// ========== EMAIL INBOX TAB ==========
const EmailInboxTab = () => {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [logs, setLogs] = useState([]);
  const [helpTopics, setHelpTopics] = useState([]);

  const [form, setForm] = useState({
    email_address: '', display_name: '',
    imap_host: '', imap_port: 993, imap_username: '', imap_password: '', imap_use_ssl: true, imap_folder: 'INBOX',
    smtp_host: '', smtp_port: 587, smtp_username: '', smtp_password: '', smtp_use_tls: true,
    poll_interval_minutes: 5, is_active: true, auto_create_tickets: true, default_help_topic_id: '',
  });
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  useEffect(() => {
    Promise.all([
      fetch(`${API}/api/ticketing/email-inbox`, { headers: headers() }).then(r => r.json()),
      fetch(`${API}/api/ticketing/email-inbox/logs`, { headers: headers() }).then(r => r.json()).catch(() => []),
      fetch(`${API}/api/ticketing/help-topics`, { headers: headers() }).then(r => r.json()),
    ]).then(([cfg, syncLogs, topics]) => {
      if (cfg.configured) {
        setConfig(cfg);
        setForm(f => ({ ...f, ...cfg, imap_password: '', smtp_password: '' }));
      }
      setLogs(Array.isArray(syncLogs) ? syncLogs : []);
      setHelpTopics(Array.isArray(topics) ? topics : []);
      setLoading(false);
    });
  }, []);

  const handleSave = async () => {
    if (!form.email_address || !form.imap_host || !form.smtp_host) {
      toast.error('Email address, IMAP host, and SMTP host are required');
      return;
    }
    setSaving(true);
    try {
      const res = await fetch(`${API}/api/ticketing/email-inbox/configure`, {
        method: 'POST', headers: headers(), body: JSON.stringify(form)
      });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      toast.success('Email inbox configured');
      const cfg = await fetch(`${API}/api/ticketing/email-inbox`, { headers: headers() }).then(r => r.json());
      setConfig(cfg);
    } catch (e) { toast.error(e.message); }
    finally { setSaving(false); }
  };

  const handleTest = async () => {
    setTesting(true); setTestResults(null);
    try {
      const res = await fetch(`${API}/api/ticketing/email-inbox/test`, {
        method: 'POST', headers: headers(), body: JSON.stringify(form)
      });
      setTestResults(await res.json());
    } catch { toast.error('Test failed'); }
    finally { setTesting(false); }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      const res = await fetch(`${API}/api/ticketing/email-inbox/sync`, {
        method: 'POST', headers: headers()
      });
      const result = await res.json();
      toast.success(`Synced: ${result.fetched} fetched, ${result.new_tickets} new tickets, ${result.updated_tickets} updated`);
      const syncLogs = await fetch(`${API}/api/ticketing/email-inbox/logs`, { headers: headers() }).then(r => r.json());
      setLogs(Array.isArray(syncLogs) ? syncLogs : []);
    } catch (e) { toast.error('Sync failed'); }
    finally { setSyncing(false); }
  };

  if (loading) return <p className="text-center py-8 text-slate-400">Loading...</p>;

  const presets = [
    { label: 'Gmail', imap_host: 'imap.gmail.com', imap_port: 993, smtp_host: 'smtp.gmail.com', smtp_port: 587 },
    { label: 'Outlook/365', imap_host: 'outlook.office365.com', imap_port: 993, smtp_host: 'smtp.office365.com', smtp_port: 587 },
    { label: 'Yahoo', imap_host: 'imap.mail.yahoo.com', imap_port: 993, smtp_host: 'smtp.mail.yahoo.com', smtp_port: 587 },
    { label: 'Zoho', imap_host: 'imap.zoho.com', imap_port: 993, smtp_host: 'smtp.zoho.com', smtp_port: 587 },
  ];

  return (
    <div data-testid="email-inbox-tab" className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-500">Connect your email inbox to automatically create and thread tickets from incoming emails</p>
          {config?.last_sync_at && (
            <p className="text-xs text-slate-400 mt-1">
              Last sync: {new Date(config.last_sync_at).toLocaleString()} ({config.last_sync_status})
              {config.total_emails_fetched > 0 && ` | ${config.total_emails_fetched} emails fetched, ${config.total_tickets_created} tickets created`}
            </p>
          )}
        </div>
        {config?.configured && (
          <Button size="sm" variant="outline" onClick={handleSync} disabled={syncing} data-testid="sync-now-btn">
            <RefreshCw className={`w-4 h-4 mr-1 ${syncing ? 'animate-spin' : ''}`} /> {syncing ? 'Syncing...' : 'Sync Now'}
          </Button>
        )}
      </div>

      <div className="bg-white border rounded-lg p-5 space-y-5">
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-2">Quick Setup</h3>
          <div className="flex gap-2">
            {presets.map(p => (
              <Button key={p.label} size="sm" variant="outline" onClick={() => setForm(f => ({ ...f, imap_host: p.imap_host, imap_port: p.imap_port, smtp_host: p.smtp_host, smtp_port: p.smtp_port }))} data-testid={`preset-${p.label.toLowerCase()}`}>
                {p.label}
              </Button>
            ))}
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div><label className="text-sm font-medium block mb-1">Email Address *</label><Input value={form.email_address} onChange={e => set('email_address', e.target.value)} placeholder="support@yourcompany.com" data-testid="email-address" /></div>
          <div><label className="text-sm font-medium block mb-1">Display Name</label><Input value={form.display_name} onChange={e => set('display_name', e.target.value)} placeholder="Support Team" /></div>
        </div>

        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">IMAP Settings (Incoming)</h3>
          <div className="grid grid-cols-4 gap-3">
            <div><label className="text-xs text-slate-500 block mb-0.5">IMAP Host *</label><Input className="text-sm" value={form.imap_host} onChange={e => set('imap_host', e.target.value)} placeholder="imap.gmail.com" data-testid="imap-host" /></div>
            <div><label className="text-xs text-slate-500 block mb-0.5">Port</label><Input className="text-sm" type="number" value={form.imap_port} onChange={e => set('imap_port', parseInt(e.target.value))} /></div>
            <div><label className="text-xs text-slate-500 block mb-0.5">Username</label><Input className="text-sm" value={form.imap_username} onChange={e => set('imap_username', e.target.value)} placeholder="Same as email" /></div>
            <div><label className="text-xs text-slate-500 block mb-0.5">Password / App Password *</label><Input className="text-sm" type="password" value={form.imap_password} onChange={e => set('imap_password', e.target.value)} placeholder={config?.imap_password_set ? '(saved)' : 'Enter password'} data-testid="imap-password" /></div>
          </div>
          <div className="flex gap-4 mt-2">
            <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={form.imap_use_ssl} onChange={e => set('imap_use_ssl', e.target.checked)} /> Use SSL</label>
            <div className="flex items-center gap-2"><label className="text-xs text-slate-500">Folder:</label><Input className="text-xs w-24 h-7" value={form.imap_folder} onChange={e => set('imap_folder', e.target.value)} /></div>
          </div>
        </div>

        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">SMTP Settings (Outgoing)</h3>
          <div className="grid grid-cols-4 gap-3">
            <div><label className="text-xs text-slate-500 block mb-0.5">SMTP Host *</label><Input className="text-sm" value={form.smtp_host} onChange={e => set('smtp_host', e.target.value)} placeholder="smtp.gmail.com" data-testid="smtp-host" /></div>
            <div><label className="text-xs text-slate-500 block mb-0.5">Port</label><Input className="text-sm" type="number" value={form.smtp_port} onChange={e => set('smtp_port', parseInt(e.target.value))} /></div>
            <div><label className="text-xs text-slate-500 block mb-0.5">Username</label><Input className="text-sm" value={form.smtp_username} onChange={e => set('smtp_username', e.target.value)} placeholder="Same as email" /></div>
            <div><label className="text-xs text-slate-500 block mb-0.5">Password / App Password *</label><Input className="text-sm" type="password" value={form.smtp_password} onChange={e => set('smtp_password', e.target.value)} placeholder={config?.smtp_password_set ? '(saved)' : 'Enter password'} data-testid="smtp-password" /></div>
          </div>
          <label className="flex items-center gap-2 text-xs mt-2"><input type="checkbox" checked={form.smtp_use_tls} onChange={e => set('smtp_use_tls', e.target.checked)} /> Use TLS (STARTTLS)</label>
        </div>

        <div className="border-t pt-4">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Ticket Settings</h3>
          <div className="grid grid-cols-3 gap-3">
            <div><label className="text-xs text-slate-500 block mb-0.5">Default Help Topic</label>
              <select className="w-full border rounded-lg px-3 py-1.5 text-sm" value={form.default_help_topic_id} onChange={e => set('default_help_topic_id', e.target.value)}>
                <option value="">Auto (first active topic)</option>
                {helpTopics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select></div>
            <div><label className="text-xs text-slate-500 block mb-0.5">Poll Interval (minutes)</label>
              <Input className="text-sm" type="number" min="1" max="60" value={form.poll_interval_minutes} onChange={e => set('poll_interval_minutes', parseInt(e.target.value))} /></div>
            <div className="flex flex-col justify-end gap-2">
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={form.auto_create_tickets} onChange={e => set('auto_create_tickets', e.target.checked)} /> Auto-create tickets from emails</label>
              <label className="flex items-center gap-2 text-xs"><input type="checkbox" checked={form.is_active} onChange={e => set('is_active', e.target.checked)} /> Active (enable polling)</label>
            </div>
          </div>
        </div>

        {testResults && (
          <div className="border-t pt-4" data-testid="test-results">
            <h3 className="text-sm font-semibold text-slate-700 mb-2">Connection Test Results</h3>
            <div className="grid grid-cols-2 gap-3">
              <div className={`border rounded-lg p-3 ${testResults.imap?.status === 'success' ? 'bg-green-50 border-green-200' : testResults.imap?.status === 'error' ? 'bg-red-50 border-red-200' : 'bg-slate-50'}`}>
                <p className="text-sm font-medium flex items-center gap-1">
                  {testResults.imap?.status === 'success' ? <CheckCircle className="w-4 h-4 text-green-500" /> : testResults.imap?.status === 'error' ? <AlertTriangle className="w-4 h-4 text-red-500" /> : null}
                  IMAP: {testResults.imap?.status}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">{testResults.imap?.message}</p>
              </div>
              <div className={`border rounded-lg p-3 ${testResults.smtp?.status === 'success' ? 'bg-green-50 border-green-200' : testResults.smtp?.status === 'error' ? 'bg-red-50 border-red-200' : 'bg-slate-50'}`}>
                <p className="text-sm font-medium flex items-center gap-1">
                  {testResults.smtp?.status === 'success' ? <CheckCircle className="w-4 h-4 text-green-500" /> : testResults.smtp?.status === 'error' ? <AlertTriangle className="w-4 h-4 text-red-500" /> : null}
                  SMTP: {testResults.smtp?.status}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">{testResults.smtp?.message}</p>
              </div>
            </div>
          </div>
        )}

        <div className="flex justify-end gap-2 border-t pt-4">
          <Button variant="outline" onClick={handleTest} disabled={testing} data-testid="test-connection-btn">
            {testing ? 'Testing...' : 'Test Connection'}
          </Button>
          <Button onClick={handleSave} disabled={saving} data-testid="save-email-config-btn">
            <Save className="w-4 h-4 mr-1" /> {saving ? 'Saving...' : 'Save Configuration'}
          </Button>
        </div>
      </div>

      {logs.length > 0 && (
        <div className="bg-white border rounded-lg p-4" data-testid="sync-logs">
          <h3 className="text-sm font-semibold text-slate-700 mb-3">Sync History</h3>
          <div className="space-y-2">
            {logs.map(log => (
              <div key={log.id} className="flex items-center gap-3 text-sm border-b pb-2 last:border-0">
                <span className={`w-2 h-2 rounded-full ${log.status === 'success' ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-xs text-slate-400">{new Date(log.synced_at).toLocaleString()}</span>
                {log.status === 'success' ? (
                  <span className="text-xs text-slate-500">{log.fetched} fetched, {log.new_tickets} new, {log.updated_tickets} updated</span>
                ) : (
                  <span className="text-xs text-red-500">{log.error}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

// ========== GENERIC EDITOR HELPER ==========
const GenericEditor = ({ title, fields, onSave, onCancel, extraContent }) => {
  const [values, setValues] = useState(() => {
    const v = {};
    fields.forEach(f => v[f.key] = f.value);
    return v;
  });
  const set = (k, v) => setValues(d => ({ ...d, [k]: v }));
  return (
    <div className="bg-white border rounded-lg p-5">
      <div className="flex justify-between mb-4"><h3 className="text-lg font-semibold">{title}</h3><button onClick={onCancel}><X className="w-5 h-5 text-slate-400" /></button></div>
      <div className="grid grid-cols-2 gap-4">
        {fields.map(f => (
          <div key={f.key} className={f.type === 'textarea' ? 'col-span-2' : ''}>
            <label className="text-sm font-medium block mb-1">{f.label}</label>
            {f.type === 'textarea' ? <textarea className="w-full border rounded-lg px-3 py-2 text-sm min-h-[80px]" value={values[f.key]} onChange={e => set(f.key, e.target.value)} />
              : f.type === 'select' ? <select className="w-full border rounded-lg px-3 py-2 text-sm" value={values[f.key]} onChange={e => set(f.key, e.target.value)}>{f.options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}</select>
              : <Input type={f.type === 'number' ? 'number' : 'text'} value={values[f.key]} onChange={e => set(f.key, e.target.value)} />}
          </div>
        ))}
      </div>
      {extraContent}
      <div className="flex justify-end gap-2 mt-5 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => onSave(values)}><Save className="w-4 h-4 mr-1" /> Save</Button>
      </div>
    </div>
  );
};

const GenericEditorInner = GenericEditor;

// ========== MAIN COMPONENT ==========
export default function TicketingConfigV2() {
  const [activeTab, setActiveTab] = useState('help-topics');
  const tabComponents = { 'help-topics': HelpTopicsTab, 'forms': FormsTab, 'workflows': WorkflowsTab, 'technicians': TechniciansTab, 'teams': TeamsTab, 'roles': RolesTab, 'sla': SLATab, 'canned': CannedTab, 'priorities': PrioritiesTab, 'email': EmailInboxTab };
  const ActiveComponent = tabComponents[activeTab];
  return (
    <div className="space-y-6" data-testid="ticketing-config-page">
      <div><h1 className="text-2xl font-bold text-slate-900">Ticketing Setup</h1><p className="text-sm text-slate-500 mt-1">Configure help topics, forms, workflows, teams, and more</p></div>
      <div className="flex gap-1 bg-slate-100 p-1 rounded-lg overflow-x-auto" data-testid="config-tabs">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return <button key={tab.id} className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-md whitespace-nowrap transition-colors ${activeTab === tab.id ? 'bg-white text-slate-900 shadow-sm font-medium' : 'text-slate-500 hover:text-slate-700'}`} onClick={() => setActiveTab(tab.id)} data-testid={`tab-${tab.id}`}><Icon className="w-4 h-4" />{tab.label}</button>;
        })}
      </div>
      {ActiveComponent ? <ActiveComponent /> : null}
    </div>
  );
}
