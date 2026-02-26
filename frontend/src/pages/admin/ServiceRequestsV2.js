import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Filter, Ticket, Clock, AlertTriangle, CheckCircle, ChevronDown, X, RefreshCw, MapPin, User, Monitor, Building2 } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const priorityColors = {
  low: 'bg-slate-100 text-slate-700',
  medium: 'bg-blue-100 text-blue-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
};

const StatsCard = ({ label, value, icon: Icon, color }) => (
  <div className="bg-white border border-slate-200 rounded-lg p-4" data-testid={`stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-semibold mt-1">{value}</p>
      </div>
      <div className={`p-2.5 rounded-lg ${color}`}>
        <Icon className="w-5 h-5" />
      </div>
    </div>
  </div>
);

// ── Searchable Dropdown ──
const SearchSelect = ({ options, value, onChange, placeholder, renderOption, searchKeys, emptyText, testId }) => {
  const [open, setOpen] = useState(false);
  const [q, setQ] = useState('');
  const ref = useRef(null);

  useEffect(() => {
    const handler = (e) => { if (ref.current && !ref.current.contains(e.target)) setOpen(false); };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  const filtered = useMemo(() => {
    if (!q.trim()) return options;
    const lower = q.toLowerCase();
    return options.filter(o => (searchKeys || ['name']).some(k => (o[k] || '').toLowerCase().includes(lower)));
  }, [options, q, searchKeys]);

  const selected = options.find(o => o.id === value);

  return (
    <div className="relative" ref={ref}>
      <button
        type="button"
        className={`w-full border rounded-lg px-3 py-2 text-sm text-left flex items-center justify-between ${!value ? 'text-slate-400' : 'text-slate-800'}`}
        onClick={() => setOpen(!open)}
        data-testid={testId}
      >
        <span className="truncate">{selected ? (renderOption ? renderOption(selected, true) : selected.name) : placeholder}</span>
        <ChevronDown className={`w-4 h-4 shrink-0 transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>
      {open && (
        <div className="absolute z-50 top-full left-0 right-0 mt-1 bg-white border rounded-lg shadow-lg max-h-60 overflow-hidden">
          <div className="p-2 border-b">
            <Input
              autoFocus
              placeholder={`Search...`}
              value={q}
              onChange={e => setQ(e.target.value)}
              className="text-sm h-8"
              data-testid={`${testId}-search`}
            />
          </div>
          <div className="overflow-auto max-h-48">
            {filtered.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-3">{emptyText || 'No results'}</p>
            ) : (
              filtered.map(o => (
                <button
                  key={o.id}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-blue-50 transition-colors ${value === o.id ? 'bg-blue-50 text-blue-700 font-medium' : ''}`}
                  onClick={() => { onChange(o.id, o); setOpen(false); setQ(''); }}
                  data-testid={`${testId}-opt-${o.id}`}
                >
                  {renderOption ? renderOption(o) : o.name}
                </button>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// ── Create Ticket Modal ──
const CreateTicketModal = ({ open, onClose, onCreated }) => {
  const token = localStorage.getItem('admin_token');
  const hdrs = { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' };

  // Core state
  const [helpTopics, setHelpTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [topicDetails, setTopicDetails] = useState(null);
  const [formValues, setFormValues] = useState({});
  const [subject, setSubject] = useState('');
  const [description, setDescription] = useState('');
  const [priorities, setPriorities] = useState([]);
  const [selectedPriority, setSelectedPriority] = useState('');

  // Company flow
  const [companies, setCompanies] = useState([]);
  const [selectedCompany, setSelectedCompany] = useState('');
  const [sites, setSites] = useState([]);
  const [selectedSite, setSelectedSite] = useState('');
  const [useCustomLocation, setUseCustomLocation] = useState(false);
  const [customLocation, setCustomLocation] = useState('');
  const [employees, setEmployees] = useState([]);
  const [selectedEmployee, setSelectedEmployee] = useState('');
  const [useCustomEmployee, setUseCustomEmployee] = useState(false);
  const [contactName, setContactName] = useState('');
  const [contactPhone, setContactPhone] = useState('');
  const [contactEmail, setContactEmail] = useState('');

  // Device
  const [devices, setDevices] = useState([]);
  const [deviceSearch, setDeviceSearch] = useState('');
  const [selectedDevice, setSelectedDevice] = useState('');
  const [useCustomDevice, setUseCustomDevice] = useState(false);
  const [deviceDescription, setDeviceDescription] = useState('');

  const [submitting, setSubmitting] = useState(false);

  // Init data
  useEffect(() => {
    if (!open) return;
    Promise.all([
      fetch(`${API}/api/ticketing/help-topics`, { headers: hdrs }).then(r => r.json()),
      fetch(`${API}/api/admin/companies`, { headers: hdrs }).then(r => r.json()),
      fetch(`${API}/api/ticketing/priorities`, { headers: hdrs }).then(r => r.json()),
    ]).then(([topics, comps, prios]) => {
      setHelpTopics(Array.isArray(topics) ? topics : []);
      setCompanies(Array.isArray(comps) ? comps : []);
      setPriorities(Array.isArray(prios) ? prios : []);
    });
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open]);

  // Fetch topic details
  useEffect(() => {
    if (!selectedTopic) { setTopicDetails(null); return; }
    fetch(`${API}/api/ticketing/help-topics/${selectedTopic}`, { headers: hdrs })
      .then(r => r.json()).then(setTopicDetails);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedTopic]);

  // Fetch sites when company changes
  useEffect(() => {
    setSites([]); setSelectedSite(''); setEmployees([]); setSelectedEmployee('');
    setDevices([]); setSelectedDevice(''); setUseCustomLocation(false); setUseCustomEmployee(false);
    if (!selectedCompany) return;
    fetch(`${API}/api/admin/sites?company_id=${selectedCompany}`, { headers: hdrs })
      .then(r => r.json()).then(d => setSites(Array.isArray(d) ? d : d.sites || []));
    fetch(`${API}/api/admin/company-employees?company_id=${selectedCompany}`, { headers: hdrs })
      .then(r => r.json()).then(d => setEmployees(Array.isArray(d) ? d : d.employees || []));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCompany]);

  // Fetch devices when site changes
  useEffect(() => {
    setDevices([]); setSelectedDevice(''); setUseCustomDevice(false);
    if (!selectedCompany) return;
    let url = `${API}/api/admin/devices?company_id=${selectedCompany}&limit=100`;
    if (selectedSite) url += `&site_id=${selectedSite}`;
    if (deviceSearch.trim()) url += `&q=${encodeURIComponent(deviceSearch)}`;
    fetch(url, { headers: hdrs })
      .then(r => r.json())
      .then(d => setDevices(Array.isArray(d) ? d : d.devices || []));
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCompany, selectedSite, deviceSearch]);

  // When employee is selected, autofill contact
  const onEmployeeSelect = (id, emp) => {
    setSelectedEmployee(id);
    if (emp) {
      setContactName(emp.name || '');
      setContactPhone(emp.phone || '');
      setContactEmail(emp.email || '');
    }
  };

  const handleSubmit = async () => {
    if (!selectedTopic || !subject.trim()) { toast.error('Please select a help topic and enter a subject'); return; }
    setSubmitting(true);
    try {
      const body = {
        help_topic_id: selectedTopic,
        subject, description,
        form_values: formValues,
        company_id: selectedCompany || undefined,
        site_id: (!useCustomLocation && selectedSite) || undefined,
        custom_location: useCustomLocation ? customLocation : undefined,
        employee_id: (!useCustomEmployee && selectedEmployee) || undefined,
        employee_name: useCustomEmployee ? contactName : undefined,
        contact_name: contactName || undefined,
        contact_email: contactEmail || undefined,
        contact_phone: contactPhone || undefined,
        device_id: (!useCustomDevice && selectedDevice) || undefined,
        device_description: useCustomDevice ? deviceDescription : undefined,
        priority_id: selectedPriority || undefined,
      };
      const res = await fetch(`${API}/api/ticketing/tickets`, { method: 'POST', headers: hdrs, body: JSON.stringify(body) });
      if (!res.ok) throw new Error((await res.json()).detail || 'Failed');
      const ticket = await res.json();
      toast.success(`Ticket ${ticket.ticket_number} created`);
      onCreated?.();
      onClose();
    } catch (e) { toast.error(e.message); }
    finally { setSubmitting(false); }
  };

  if (!open) return null;

  const formFields = topicDetails?.form?.fields || [];

  return (
    <div className="fixed inset-0 z-50 bg-black/40 flex items-start justify-center pt-6 overflow-y-auto" data-testid="create-ticket-modal">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 mb-10">
        <div className="flex items-center justify-between p-5 border-b">
          <h2 className="text-lg font-semibold">Create New Ticket</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded"><X className="w-5 h-5" /></button>
        </div>
        <div className="p-5 space-y-4 max-h-[75vh] overflow-y-auto">

          {/* Help Topic & Priority */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Help Topic *</label>
              <select data-testid="help-topic-select" className="w-full border rounded-lg px-3 py-2 text-sm" value={selectedTopic || ''} onChange={e => { setSelectedTopic(e.target.value); setFormValues({}); }}>
                <option value="">Select a help topic...</option>
                {helpTopics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
              </select>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Priority</label>
              <select className="w-full border rounded-lg px-3 py-2 text-sm" value={selectedPriority} onChange={e => setSelectedPriority(e.target.value)} data-testid="priority-select">
                <option value="">Default</option>
                {priorities.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </div>
          </div>

          {/* Company */}
          <div className="border rounded-lg p-4 space-y-3 bg-slate-50/50">
            <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-1"><Building2 className="w-4 h-4" /> Company & Location</h3>
            <div>
              <label className="text-xs font-medium text-slate-600 block mb-1">Company</label>
              <SearchSelect
                options={companies}
                value={selectedCompany}
                onChange={(id) => setSelectedCompany(id)}
                placeholder="Search & select company..."
                searchKeys={['name', 'email', 'phone']}
                renderOption={(c, isLabel) => isLabel ? c.name : (
                  <div><p className="font-medium">{c.name}</p>{c.city && <p className="text-[10px] text-slate-400">{c.city}</p>}</div>
                )}
                testId="company-select"
              />
            </div>

            {/* Site / Location */}
            {selectedCompany && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-slate-600 flex items-center gap-1"><MapPin className="w-3 h-3" /> Site / Location</label>
                  <button className="text-[10px] text-blue-600 hover:underline" onClick={() => { setUseCustomLocation(!useCustomLocation); setSelectedSite(''); }} data-testid="toggle-custom-location">
                    {useCustomLocation ? 'Select from list' : '+ Another location'}
                  </button>
                </div>
                {useCustomLocation ? (
                  <Input placeholder="Type full address..." value={customLocation} onChange={e => setCustomLocation(e.target.value)} className="text-sm" data-testid="custom-location" />
                ) : (
                  <SearchSelect
                    options={sites}
                    value={selectedSite}
                    onChange={(id) => setSelectedSite(id)}
                    placeholder="Select site..."
                    searchKeys={['name', 'address', 'city']}
                    renderOption={(s, isLabel) => isLabel ? `${s.name}${s.city ? `, ${s.city}` : ''}` : (
                      <div><p className="font-medium">{s.name}</p><p className="text-[10px] text-slate-400">{s.address}{s.city ? `, ${s.city}` : ''}</p></div>
                    )}
                    emptyText="No sites found"
                    testId="site-select"
                  />
                )}
              </div>
            )}

            {/* Employee / Complainant */}
            {selectedCompany && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-medium text-slate-600 flex items-center gap-1"><User className="w-3 h-3" /> Complainant / Employee</label>
                  <button className="text-[10px] text-blue-600 hover:underline" onClick={() => { setUseCustomEmployee(!useCustomEmployee); setSelectedEmployee(''); }} data-testid="toggle-custom-employee">
                    {useCustomEmployee ? 'Select from list' : '+ Another person'}
                  </button>
                </div>
                {useCustomEmployee ? (
                  <div className="grid grid-cols-3 gap-2">
                    <Input placeholder="Name" value={contactName} onChange={e => setContactName(e.target.value)} className="text-sm" data-testid="custom-emp-name" />
                    <Input placeholder="Phone" value={contactPhone} onChange={e => setContactPhone(e.target.value)} className="text-sm" data-testid="custom-emp-phone" />
                    <Input placeholder="Email" value={contactEmail} onChange={e => setContactEmail(e.target.value)} className="text-sm" data-testid="custom-emp-email" />
                  </div>
                ) : (
                  <SearchSelect
                    options={employees}
                    value={selectedEmployee}
                    onChange={onEmployeeSelect}
                    placeholder="Search employee..."
                    searchKeys={['name', 'email', 'phone', 'department']}
                    renderOption={(e, isLabel) => isLabel ? `${e.name}${e.department ? ` (${e.department})` : ''}` : (
                      <div className="flex items-center justify-between">
                        <div><p className="font-medium">{e.name}</p>{e.department && <p className="text-[10px] text-slate-400">{e.department}</p>}</div>
                        {e.phone && <span className="text-[10px] text-slate-400">{e.phone}</span>}
                      </div>
                    )}
                    emptyText="No employees found"
                    testId="employee-select"
                  />
                )}
              </div>
            )}
          </div>

          {/* Device / Asset */}
          {selectedCompany && (
            <div className="border rounded-lg p-4 space-y-3 bg-slate-50/50">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-700 flex items-center gap-1"><Monitor className="w-4 h-4" /> Device / Asset <span className="text-[10px] text-slate-400 font-normal">(optional)</span></h3>
                <button className="text-[10px] text-blue-600 hover:underline" onClick={() => { setUseCustomDevice(!useCustomDevice); setSelectedDevice(''); }} data-testid="toggle-custom-device">
                  {useCustomDevice ? 'Select from list' : '+ Type manually'}
                </button>
              </div>
              {useCustomDevice ? (
                <textarea
                  className="w-full border rounded-lg px-3 py-2 text-sm min-h-[60px]"
                  placeholder="Describe the device (name, model, serial number, etc.)..."
                  value={deviceDescription}
                  onChange={e => setDeviceDescription(e.target.value)}
                  data-testid="custom-device-desc"
                />
              ) : (
                <SearchSelect
                  options={devices}
                  value={selectedDevice}
                  onChange={(id) => setSelectedDevice(id)}
                  placeholder="Search by name, model, serial number..."
                  searchKeys={['display_name', 'brand', 'model', 'serial_number', 'asset_tag', 'device_type', 'name']}
                  renderOption={(d, isLabel) => {
                    const label = d.display_name || `${d.brand || ''} ${d.model || ''}`.trim() || d.device_type || d.name;
                    if (isLabel) return `${label}${d.serial_number ? ` (S/N: ${d.serial_number})` : ''}`;
                    return (
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{label}</p>
                          <p className="text-[10px] text-slate-400">
                            {d.device_type}{d.serial_number ? ` | S/N: ${d.serial_number}` : ''}{d.asset_tag ? ` | Tag: ${d.asset_tag}` : ''}
                          </p>
                        </div>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${d.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-500'}`}>{d.status || 'active'}</span>
                      </div>
                    );
                  }}
                  emptyText="No devices found"
                  testId="device-select"
                />
              )}
            </div>
          )}

          {/* Subject & Description */}
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Subject *</label>
            <Input data-testid="ticket-subject" value={subject} onChange={e => setSubject(e.target.value)} placeholder="Brief description of the issue" />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-700 block mb-1.5">Description</label>
            <textarea data-testid="ticket-description" className="w-full border rounded-lg px-3 py-2 text-sm min-h-[80px]" value={description} onChange={e => setDescription(e.target.value)} placeholder="Detailed description..." />
          </div>

          {/* Contact override (if employee was selected) */}
          {selectedEmployee && !useCustomEmployee && (
            <div className="grid grid-cols-3 gap-3">
              <div><label className="text-xs font-medium text-slate-600 block mb-1">Contact Name</label><Input className="text-sm" value={contactName} onChange={e => setContactName(e.target.value)} /></div>
              <div><label className="text-xs font-medium text-slate-600 block mb-1">Phone</label><Input className="text-sm" value={contactPhone} onChange={e => setContactPhone(e.target.value)} /></div>
              <div><label className="text-xs font-medium text-slate-600 block mb-1">Email</label><Input className="text-sm" value={contactEmail} onChange={e => setContactEmail(e.target.value)} /></div>
            </div>
          )}

          {/* No company selected - manual contact */}
          {!selectedCompany && (
            <div className="grid grid-cols-3 gap-3">
              <div><label className="text-sm font-medium text-slate-700 block mb-1.5">Contact Name</label><Input data-testid="contact-name" value={contactName} onChange={e => setContactName(e.target.value)} placeholder="Name" /></div>
              <div><label className="text-sm font-medium text-slate-700 block mb-1.5">Contact Email</label><Input data-testid="contact-email" value={contactEmail} onChange={e => setContactEmail(e.target.value)} placeholder="Email" /></div>
              <div><label className="text-sm font-medium text-slate-700 block mb-1.5">Contact Phone</label><Input data-testid="contact-phone" value={contactPhone} onChange={e => setContactPhone(e.target.value)} placeholder="Phone" /></div>
            </div>
          )}

          {/* Custom Form Fields */}
          {formFields.length > 0 && (
            <div className="border-t pt-4 mt-2">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">Custom Fields - {topicDetails?.form?.name}</h3>
              <div className="grid grid-cols-2 gap-3">
                {formFields.map(f => (
                  <div key={f.id} className={f.width === 'full' ? 'col-span-2' : ''}>
                    <label className="text-sm font-medium text-slate-600 block mb-1">{f.label} {f.required && '*'}</label>
                    {f.field_type === 'select' ? (
                      <select className="w-full border rounded-lg px-3 py-2 text-sm" value={formValues[f.slug] || ''} onChange={e => setFormValues(p => ({ ...p, [f.slug]: e.target.value }))}>
                        <option value="">Select...</option>
                        {(f.options || []).map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                    ) : f.field_type === 'textarea' ? (
                      <textarea className="w-full border rounded-lg px-3 py-2 text-sm" value={formValues[f.slug] || ''} onChange={e => setFormValues(p => ({ ...p, [f.slug]: e.target.value }))} />
                    ) : (
                      <Input type={f.field_type === 'number' ? 'number' : f.field_type === 'date' ? 'date' : 'text'} value={formValues[f.slug] || ''} onChange={e => setFormValues(p => ({ ...p, [f.slug]: e.target.value }))} placeholder={f.placeholder || ''} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
        <div className="flex justify-end gap-3 p-5 border-t">
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={handleSubmit} disabled={submitting} data-testid="submit-ticket-btn">
            {submitting ? 'Creating...' : 'Create Ticket'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default function ServiceRequestsV2() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState({ is_open: null, help_topic_id: null, priority: null });
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [helpTopics, setHelpTopics] = useState([]);
  const [showCreate, setShowCreate] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    const token = localStorage.getItem('admin_token');
    const params = new URLSearchParams({ page, limit: 20 });
    if (search) params.set('search', search);
    if (filter.is_open !== null) params.set('is_open', filter.is_open);
    if (filter.help_topic_id) params.set('help_topic_id', filter.help_topic_id);
    if (filter.priority) params.set('priority', filter.priority);

    try {
      const [ticketsRes, statsRes] = await Promise.all([
        fetch(`${API}/api/ticketing/tickets?${params}`, { headers: { Authorization: `Bearer ${token}` } }),
        fetch(`${API}/api/ticketing/stats`, { headers: { Authorization: `Bearer ${token}` } }),
      ]);
      const ticketsData = await ticketsRes.json();
      setTickets(ticketsData.tickets || []);
      setTotalPages(ticketsData.pages || 1);
      setStats(await statsRes.json());
    } catch { toast.error('Failed to load tickets'); }
    finally { setLoading(false); }
  }, [page, search, filter]);

  useEffect(() => { fetchTickets(); }, [fetchTickets]);

  useEffect(() => {
    const token = localStorage.getItem('admin_token');
    fetch(`${API}/api/ticketing/help-topics`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json()).then(data => setHelpTopics(Array.isArray(data) ? data : []));
  }, []);

  return (
    <div className="space-y-6" data-testid="tickets-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Tickets</h1>
          <p className="text-sm text-slate-500 mt-1">Manage service requests and support tickets</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={fetchTickets} data-testid="refresh-btn">
            <RefreshCw className="w-4 h-4 mr-1" /> Refresh
          </Button>
          <Button size="sm" onClick={() => setShowCreate(true)} data-testid="create-ticket-btn">
            <Plus className="w-4 h-4 mr-1" /> New Ticket
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatsCard label="Open" value={stats.open || 0} icon={Ticket} color="bg-blue-50 text-blue-600" />
        <StatsCard label="Closed" value={stats.closed || 0} icon={CheckCircle} color="bg-green-50 text-green-600" />
        <StatsCard label="Total" value={stats.total || 0} icon={Clock} color="bg-slate-50 text-slate-600" />
        <StatsCard label="Pending Tasks" value={stats.pending_tasks || 0} icon={AlertTriangle} color="bg-orange-50 text-orange-600" />
      </div>

      <div className="flex gap-3 items-center">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <Input
            data-testid="search-tickets"
            className="pl-9"
            placeholder="Search by ticket number or subject..."
            value={search}
            onChange={e => { setSearch(e.target.value); setPage(1); }}
          />
        </div>
        <Button variant="outline" size="sm" onClick={() => setShowFilters(!showFilters)} data-testid="filter-btn">
          <Filter className="w-4 h-4 mr-1" /> Filters {showFilters && <ChevronDown className="w-3 h-3 ml-1" />}
        </Button>
      </div>

      {showFilters && (
        <div className="flex gap-3 items-center bg-slate-50 p-3 rounded-lg" data-testid="filter-bar">
          <select className="border rounded-lg px-3 py-1.5 text-sm" value={filter.is_open ?? ''} onChange={e => { setFilter(f => ({ ...f, is_open: e.target.value === '' ? null : e.target.value === 'true' })); setPage(1); }}>
            <option value="">All Status</option>
            <option value="true">Open</option>
            <option value="false">Closed</option>
          </select>
          <select className="border rounded-lg px-3 py-1.5 text-sm" value={filter.help_topic_id || ''} onChange={e => { setFilter(f => ({ ...f, help_topic_id: e.target.value || null })); setPage(1); }}>
            <option value="">All Topics</option>
            {helpTopics.map(t => <option key={t.id} value={t.id}>{t.name}</option>)}
          </select>
          <select className="border rounded-lg px-3 py-1.5 text-sm" value={filter.priority || ''} onChange={e => { setFilter(f => ({ ...f, priority: e.target.value || null })); setPage(1); }}>
            <option value="">All Priorities</option>
            <option value="low">Low</option>
            <option value="medium">Medium</option>
            <option value="high">High</option>
            <option value="critical">Critical</option>
          </select>
          <Button variant="ghost" size="sm" onClick={() => { setFilter({ is_open: null, help_topic_id: null, priority: null }); setPage(1); }}>Clear</Button>
        </div>
      )}

      <div className="bg-white border border-slate-200 rounded-lg overflow-hidden" data-testid="tickets-table">
        <table className="w-full">
          <thead className="bg-slate-50 border-b">
            <tr>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Ticket</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Subject</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Help Topic</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Stage</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Priority</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Assigned</th>
              <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Created</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={7} className="text-center py-12 text-slate-400">Loading...</td></tr>
            ) : tickets.length === 0 ? (
              <tr><td colSpan={7} className="text-center py-12 text-slate-400">No tickets found</td></tr>
            ) : tickets.map(t => (
              <tr
                key={t.id}
                className="border-b hover:bg-slate-50 cursor-pointer transition-colors"
                onClick={() => navigate(`/admin/service-requests/${t.id}`)}
                data-testid={`ticket-row-${t.ticket_number}`}
              >
                <td className="px-4 py-3">
                  <span className="font-mono text-sm font-semibold text-blue-600">#{t.ticket_number}</span>
                </td>
                <td className="px-4 py-3">
                  <p className="text-sm font-medium text-slate-900 truncate max-w-[250px]">{t.subject}</p>
                  {t.company_name && <p className="text-xs text-slate-400">{t.company_name}</p>}
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">{t.help_topic_name}</span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${t.is_open ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'}`}>
                    {t.current_stage_name || 'New'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[t.priority_name] || priorityColors.medium}`}>
                    {t.priority_name || 'medium'}
                  </span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-slate-500">{t.assigned_to_name || t.assigned_team_name || '-'}</span>
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-slate-400">{t.created_at ? new Date(t.created_at).toLocaleDateString() : '-'}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex justify-center gap-2" data-testid="pagination">
          <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>Previous</Button>
          <span className="text-sm text-slate-500 self-center">Page {page} of {totalPages}</span>
          <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage(p => p + 1)}>Next</Button>
        </div>
      )}

      <CreateTicketModal open={showCreate} onClose={() => setShowCreate(false)} onCreated={fetchTickets} />
    </div>
  );
}
