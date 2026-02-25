import { useState, useEffect, useCallback } from 'react';
import {
  Ticket, FileText, GitBranch, Users, Shield, Clock, MessageSquare, Bell,
  Plus, Edit2, Trash2, ChevronRight, Save, X, AlertTriangle, CheckCircle
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
  { id: 'teams', label: 'Teams', icon: Users },
  { id: 'roles', label: 'Roles', icon: Shield },
  { id: 'sla', label: 'SLA Policies', icon: Clock },
  { id: 'canned', label: 'Canned Responses', icon: MessageSquare },
  { id: 'priorities', label: 'Priorities', icon: AlertTriangle },
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
      setTopics(Array.isArray(t) ? t : []);
      setForms(Array.isArray(f) ? f : []);
      setWorkflows(Array.isArray(w) ? w : []);
      setTeams(Array.isArray(tm) ? tm : []);
      setSlas(Array.isArray(s) ? s : []);
    } catch { toast.error('Failed to load'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetch_(); }, [fetch_]);

  const handleSave = async (data) => {
    try {
      if (editing?.id) {
        await fetch(`${API}/api/ticketing/help-topics/${editing.id}`, { method: 'PUT', headers: headers(), body: JSON.stringify(data) });
      } else {
        await fetch(`${API}/api/ticketing/help-topics`, { method: 'POST', headers: headers(), body: JSON.stringify(data) });
      }
      toast.success('Saved'); setEditing(null); fetch_();
    } catch { toast.error('Failed'); }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this help topic?')) return;
    await fetch(`${API}/api/ticketing/help-topics/${id}`, { method: 'DELETE', headers: headers() });
    toast.success('Deleted'); fetch_();
  };

  if (editing !== null) {
    return <HelpTopicEditor topic={editing} forms={forms} workflows={workflows} teams={teams} slas={slas} onSave={handleSave} onCancel={() => setEditing(null)} />;
  }

  return (
    <div data-testid="help-topics-tab">
      <div className="flex justify-between items-center mb-4">
        <p className="text-sm text-slate-500">{topics.length} help topics configured</p>
        <Button size="sm" onClick={() => setEditing({})} data-testid="add-help-topic"><Plus className="w-4 h-4 mr-1" /> Add Help Topic</Button>
      </div>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {topics.map(t => (
            <ConfigCard key={t.id} item={t} onEdit={setEditing} onDelete={handleDelete}>
              <div className="flex gap-2 mt-2 flex-wrap">
                {t.category && <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">{t.category}</span>}
                {t.form_id && <span className="text-xs bg-blue-50 text-blue-600 px-2 py-0.5 rounded">Has Form</span>}
                {t.workflow_id && <span className="text-xs bg-purple-50 text-purple-600 px-2 py-0.5 rounded">Has Workflow</span>}
                {!t.is_active && <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded">Inactive</span>}
                <span className="text-xs text-slate-400">{t.ticket_count || 0} tickets</span>
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
    category: topic.category || 'support', form_id: topic.form_id || '',
    workflow_id: topic.workflow_id || '', default_team_id: topic.default_team_id || '',
    sla_policy_id: topic.sla_policy_id || '', default_priority: topic.default_priority || 'medium',
    is_active: topic.is_active !== false, is_public: topic.is_public !== false,
    require_company: topic.require_company !== false, require_contact: topic.require_contact !== false,
    require_device: topic.require_device || false,
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
        <div><label className="text-sm font-medium block mb-1">Category</label>
          <select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.category} onChange={e => set('category', e.target.value)}>
            <option value="support">Support</option><option value="sales">Sales</option><option value="operations">Operations</option><option value="general">General</option>
          </select></div>
        <div><label className="text-sm font-medium block mb-1">Default Priority</label>
          <select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.default_priority} onChange={e => set('default_priority', e.target.value)}>
            <option value="low">Low</option><option value="medium">Medium</option><option value="high">High</option><option value="critical">Critical</option>
          </select></div>
        <div><label className="text-sm font-medium block mb-1">Form</label>
          <select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.form_id} onChange={e => set('form_id', e.target.value)}>
            <option value="">No custom form</option>{forms.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select></div>
        <div><label className="text-sm font-medium block mb-1">Workflow</label>
          <select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.workflow_id} onChange={e => set('workflow_id', e.target.value)}>
            <option value="">No workflow</option>{workflows.map(w => <option key={w.id} value={w.id}>{w.name}</option>)}
          </select></div>
        <div><label className="text-sm font-medium block mb-1">Default Team</label>
          <select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.default_team_id} onChange={e => set('default_team_id', e.target.value)}>
            <option value="">None</option>{teams.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select></div>
        <div><label className="text-sm font-medium block mb-1">SLA Policy</label>
          <select className="w-full border rounded-lg px-3 py-2 text-sm" value={data.sla_policy_id} onChange={e => set('sla_policy_id', e.target.value)}>
            <option value="">None</option>{slas.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
          </select></div>
        <div className="col-span-2 flex gap-4 flex-wrap">
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={data.is_active} onChange={e => set('is_active', e.target.checked)} /> Active</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={data.is_public} onChange={e => set('is_public', e.target.checked)} /> Public (customer portal)</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={data.require_company} onChange={e => set('require_company', e.target.checked)} /> Require Company</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={data.require_contact} onChange={e => set('require_contact', e.target.checked)} /> Require Contact</label>
          <label className="flex items-center gap-2 text-sm"><input type="checkbox" checked={data.require_device} onChange={e => set('require_device', e.target.checked)} /> Require Device</label>
        </div>
      </div>
      <div className="flex justify-end gap-2 mt-5 pt-4 border-t">
        <Button variant="outline" onClick={onCancel}>Cancel</Button>
        <Button onClick={() => onSave(data)} data-testid="save-topic"><Save className="w-4 h-4 mr-1" /> Save</Button>
      </div>
    </div>
  );
};

// ========== FORMS TAB ==========
const FormsTab = () => {
  const [forms, setForms] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/ticketing/forms`, { headers: headers() })
      .then(r => r.json()).then(data => { setForms(Array.isArray(data) ? data : []); setLoading(false); });
  }, []);

  return (
    <div data-testid="forms-tab">
      <p className="text-sm text-slate-500 mb-4">{forms.length} forms configured</p>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {forms.map(f => (
            <ConfigCard key={f.id} item={f}>
              <p className="text-xs text-slate-400 mt-1">{f.fields?.length || 0} fields</p>
              <div className="flex gap-1 mt-2 flex-wrap">
                {(f.fields || []).slice(0, 4).map(field => (
                  <span key={field.id} className="text-xs bg-slate-50 text-slate-500 px-1.5 py-0.5 rounded">{field.label}</span>
                ))}
                {(f.fields || []).length > 4 && <span className="text-xs text-slate-400">+{f.fields.length - 4} more</span>}
              </div>
            </ConfigCard>
          ))}
        </div>
      )}
    </div>
  );
};

// ========== WORKFLOWS TAB ==========
const WorkflowsTab = () => {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    fetch(`${API}/api/ticketing/workflows`, { headers: headers() })
      .then(r => r.json()).then(data => { setWorkflows(Array.isArray(data) ? data : []); setLoading(false); });
  }, []);

  const stageColors = { initial: 'bg-blue-100 text-blue-700', in_progress: 'bg-yellow-100 text-yellow-700', waiting: 'bg-purple-100 text-purple-700', terminal_success: 'bg-green-100 text-green-700', terminal_failure: 'bg-red-100 text-red-700' };

  return (
    <div data-testid="workflows-tab">
      <p className="text-sm text-slate-500 mb-4">{workflows.length} workflows configured</p>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="space-y-3">
          {workflows.map(w => (
            <div key={w.id} className="border rounded-lg bg-white overflow-hidden" data-testid={`workflow-${w.id}`}>
              <div className="p-4 flex items-center justify-between cursor-pointer hover:bg-slate-50" onClick={() => setExpanded(expanded === w.id ? null : w.id)}>
                <div>
                  <h4 className="text-sm font-semibold text-slate-800">{w.name}</h4>
                  <p className="text-xs text-slate-500">{w.stages?.length || 0} stages</p>
                </div>
                <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform ${expanded === w.id ? 'rotate-90' : ''}`} />
              </div>
              {expanded === w.id && (
                <div className="border-t p-4">
                  <div className="flex flex-wrap gap-2">
                    {[...(w.stages || [])].sort((a, b) => a.order - b.order).map((stage, i) => (
                      <div key={stage.id} className="flex items-center gap-1">
                        <span className={`text-xs px-2 py-1 rounded-full ${stageColors[stage.stage_type] || 'bg-slate-100 text-slate-600'}`}>
                          {stage.name}
                        </span>
                        {i < (w.stages || []).length - 1 && <ChevronRight className="w-3 h-3 text-slate-300" />}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

// ========== TEAMS TAB ==========
const TeamsTab = () => {
  const [teams, setTeams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/ticketing/teams`, { headers: headers() })
      .then(r => r.json()).then(data => { setTeams(Array.isArray(data) ? data : []); setLoading(false); });
  }, []);

  return (
    <div data-testid="teams-tab">
      <p className="text-sm text-slate-500 mb-4">{teams.length} teams configured</p>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {teams.map(t => (
            <ConfigCard key={t.id} item={t}>
              <div className="flex gap-2 mt-2">
                <span className="text-xs text-slate-400">{t.members?.length || 0} members</span>
                <span className="text-xs text-slate-400 capitalize">{t.assignment_method}</span>
              </div>
            </ConfigCard>
          ))}
        </div>
      )}
    </div>
  );
};

// ========== ROLES TAB ==========
const RolesTab = () => {
  const [roles, setRoles] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/ticketing/roles`, { headers: headers() })
      .then(r => r.json()).then(data => { setRoles(Array.isArray(data) ? data : []); setLoading(false); });
  }, []);

  return (
    <div data-testid="roles-tab">
      <p className="text-sm text-slate-500 mb-4">{roles.length} roles configured</p>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {roles.map(r => (
            <ConfigCard key={r.id} item={r}>
              <div className="flex gap-1 mt-2 flex-wrap">
                {(r.permissions || []).slice(0, 3).map(p => (
                  <span key={p} className="text-xs bg-slate-50 text-slate-500 px-1.5 py-0.5 rounded">{p}</span>
                ))}
                {(r.permissions || []).length > 3 && <span className="text-xs text-slate-400">+{r.permissions.length - 3} more</span>}
              </div>
            </ConfigCard>
          ))}
        </div>
      )}
    </div>
  );
};

// ========== SLA TAB ==========
const SLATab = () => {
  const [policies, setPolicies] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/ticketing/sla-policies`, { headers: headers() })
      .then(r => r.json()).then(data => { setPolicies(Array.isArray(data) ? data : []); setLoading(false); });
  }, []);

  return (
    <div data-testid="sla-tab">
      <p className="text-sm text-slate-500 mb-4">{policies.length} SLA policies configured</p>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {policies.map(p => (
            <ConfigCard key={p.id} item={p}>
              <div className="flex gap-3 mt-2 text-xs text-slate-500">
                <span>Response: {p.response_time_hours}h</span>
                <span>Resolution: {p.resolution_time_hours}h</span>
                {p.escalation_enabled && <span className="text-orange-500">Escalation: {p.escalation_after_hours}h</span>}
              </div>
            </ConfigCard>
          ))}
        </div>
      )}
    </div>
  );
};

// ========== CANNED RESPONSES TAB ==========
const CannedTab = () => {
  const [responses, setResponses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/ticketing/canned-responses`, { headers: headers() })
      .then(r => r.json()).then(data => { setResponses(Array.isArray(data) ? data : []); setLoading(false); });
  }, []);

  return (
    <div data-testid="canned-tab">
      <p className="text-sm text-slate-500 mb-4">{responses.length} canned responses</p>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {responses.map(r => (
            <ConfigCard key={r.id} item={r}>
              {r.category && <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded mt-1 inline-block">{r.category}</span>}
              <p className="text-xs text-slate-400 mt-1 line-clamp-2">{r.body}</p>
            </ConfigCard>
          ))}
        </div>
      )}
    </div>
  );
};

// ========== PRIORITIES TAB ==========
const PrioritiesTab = () => {
  const [priorities, setPriorities] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API}/api/ticketing/priorities`, { headers: headers() })
      .then(r => r.json()).then(data => { setPriorities(Array.isArray(data) ? data : []); setLoading(false); });
  }, []);

  return (
    <div data-testid="priorities-tab">
      <p className="text-sm text-slate-500 mb-4">{priorities.length} priorities configured</p>
      {loading ? <p className="text-center py-8 text-slate-400">Loading...</p> : (
        <div className="grid grid-cols-2 gap-3">
          {priorities.map(p => (
            <ConfigCard key={p.id} item={p}>
              <div className="flex items-center gap-2 mt-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: p.color }} />
                <span className="text-xs text-slate-400">SLA x{p.sla_multiplier}</span>
                {p.is_default && <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">Default</span>}
              </div>
            </ConfigCard>
          ))}
        </div>
      )}
    </div>
  );
};

// ========== MAIN COMPONENT ==========
export default function TicketingConfigV2() {
  const [activeTab, setActiveTab] = useState('help-topics');

  const tabComponents = {
    'help-topics': HelpTopicsTab,
    'forms': FormsTab,
    'workflows': WorkflowsTab,
    'teams': TeamsTab,
    'roles': RolesTab,
    'sla': SLATab,
    'canned': CannedTab,
    'priorities': PrioritiesTab,
  };

  const ActiveComponent = tabComponents[activeTab];

  return (
    <div className="space-y-6" data-testid="ticketing-config-page">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Ticketing Setup</h1>
        <p className="text-sm text-slate-500 mt-1">Configure help topics, forms, workflows, teams, and more</p>
      </div>

      <div className="flex gap-1 bg-slate-100 p-1 rounded-lg overflow-x-auto" data-testid="config-tabs">
        {tabs.map(tab => {
          const Icon = tab.icon;
          return (
            <button
              key={tab.id}
              className={`flex items-center gap-1.5 px-3 py-2 text-sm rounded-md whitespace-nowrap transition-colors ${
                activeTab === tab.id ? 'bg-white text-slate-900 shadow-sm font-medium' : 'text-slate-500 hover:text-slate-700'
              }`}
              onClick={() => setActiveTab(tab.id)}
              data-testid={`tab-${tab.id}`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </div>

      <ActiveComponent />
    </div>
  );
}
