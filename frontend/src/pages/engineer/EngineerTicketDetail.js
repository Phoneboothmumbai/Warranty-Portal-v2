import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Building2, MapPin, User, Monitor, Clock, Phone, Mail,
  FileText, Calendar, Wrench, AlertTriangle, CheckCircle, ChevronRight,
  Shield, Hash, Info, Play, Square, Package, Send, Loader2,
  Stethoscope, Lightbulb, CircleCheck, CircleAlert, Timer, X
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { useEngineerAuth } from '../../context/EngineerAuthContext';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const priorityColors = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-orange-100 text-orange-600',
  critical: 'bg-red-100 text-red-600',
};

const Section = ({ icon: Icon, title, children, color = 'text-slate-600', actions }) => (
  <div className="bg-white border rounded-lg overflow-hidden" data-testid={`section-${title.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center justify-between px-4 py-3 border-b bg-slate-50">
      <div className="flex items-center gap-2">
        <Icon className={`w-4 h-4 ${color}`} />
        <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
      </div>
      {actions}
    </div>
    <div className="p-4">{children}</div>
  </div>
);

const InfoRow = ({ label, value }) => {
  if (!value) return null;
  return (
    <div className="flex items-start gap-2 py-1.5">
      <span className="text-xs text-slate-400 w-28 shrink-0">{label}</span>
      <span className="text-sm text-slate-800">{value}</span>
    </div>
  );
};

// Timer display component
const LiveTimer = ({ startTime }) => {
  const [elapsed, setElapsed] = useState('');

  useEffect(() => {
    if (!startTime) return;
    const update = () => {
      const start = new Date(startTime);
      const diff = Math.floor((Date.now() - start.getTime()) / 1000);
      const hrs = Math.floor(diff / 3600);
      const mins = Math.floor((diff % 3600) / 60);
      const secs = diff % 60;
      setElapsed(`${hrs > 0 ? hrs + 'h ' : ''}${mins}m ${secs}s`);
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, [startTime]);

  return <span className="font-mono text-sm font-bold text-blue-700">{elapsed}</span>;
};

export default function EngineerTicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const { token } = useEngineerAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [visit, setVisit] = useState(null);
  const [actionLoading, setActionLoading] = useState(false);

  // Service form state
  const [showServiceForm, setShowServiceForm] = useState(false);
  const [serviceForm, setServiceForm] = useState({
    problem_found: '', diagnosis: '', solution_applied: '', resolution_type: '', notes: ''
  });

  // Parts request state
  const [showPartsForm, setShowPartsForm] = useState(false);
  const [partsItems, setPartsItems] = useState([]);
  const [newPart, setNewPart] = useState({ product_name: '', quantity: 1, unit_price: 0, gst_slab: 18 });
  const [partsNotes, setPartsNotes] = useState('');

  // Checkout state
  const [showCheckout, setShowCheckout] = useState(false);
  const [customerName, setCustomerName] = useState('');

  // Visit history
  const [visitHistory, setVisitHistory] = useState([]);

  const hdrs = useCallback(() => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }), [token]);

  const fetchDetail = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/engineer/ticket/${ticketId}`, { headers: hdrs() });
      if (!res.ok) { toast.error('Failed to load ticket'); navigate('/engineer/dashboard'); return; }
      setData(await res.json());
    } catch { toast.error('Network error'); }
    finally { setLoading(false); }
  }, [ticketId, hdrs, navigate]);

  const fetchVisit = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/engineer/visit/${ticketId}`, { headers: hdrs() });
      if (res.ok) {
        const d = await res.json();
        setVisit(d.visit);
        if (d.visit) {
          setServiceForm({
            problem_found: d.visit.problem_found || '',
            diagnosis: d.visit.diagnosis || '',
            solution_applied: d.visit.solution_applied || '',
            resolution_type: d.visit.resolution_type || '',
            notes: d.visit.notes || '',
          });
        }
      }
    } catch {}
  }, [ticketId, hdrs]);

  const fetchVisitHistory = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/engineer/visit/history/${ticketId}`, { headers: hdrs() });
      if (res.ok) {
        const d = await res.json();
        setVisitHistory(d.visits || []);
      }
    } catch {}
  }, [ticketId, hdrs]);

  useEffect(() => { fetchDetail(); fetchVisit(); fetchVisitHistory(); }, [fetchDetail, fetchVisit, fetchVisitHistory]);

  // ── Actions ──
  const handleStartVisit = async () => {
    setActionLoading(true);
    try {
      const res = await fetch(`${API}/api/engineer/visit/start`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ ticket_id: ticketId }),
      });
      const d = await res.json();
      if (res.ok) {
        setVisit(d.visit);
        toast.success('Visit started! Timer is running.');
        fetchDetail();
      } else {
        toast.error(d.detail || 'Failed to start visit');
      }
    } catch { toast.error('Network error'); }
    finally { setActionLoading(false); }
  };

  const handleUpdateVisit = async () => {
    if (!visit) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${API}/api/engineer/visit/${visit.id}/update`, {
        method: 'PUT', headers: hdrs(),
        body: JSON.stringify(serviceForm),
      });
      const d = await res.json();
      if (res.ok) {
        setVisit(d.visit);
        toast.success('Report saved');
        setShowServiceForm(false);
      } else {
        toast.error(d.detail || 'Failed to update');
      }
    } catch { toast.error('Network error'); }
    finally { setActionLoading(false); }
  };

  const handleRequestParts = async () => {
    if (!visit || partsItems.length === 0) return;
    setActionLoading(true);
    try {
      const res = await fetch(`${API}/api/engineer/visit/${visit.id}/request-parts`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({ parts: partsItems, notes: partsNotes }),
      });
      const d = await res.json();
      if (res.ok) {
        toast.success(`Parts requested! Quotation ${d.quotation_number} created.`);
        setShowPartsForm(false);
        setPartsItems([]);
        setPartsNotes('');
        fetchVisit();
        fetchDetail();
      } else {
        toast.error(d.detail || 'Failed to request parts');
      }
    } catch { toast.error('Network error'); }
    finally { setActionLoading(false); }
  };

  const handleCheckout = async () => {
    if (!visit) return;
    const resolution = serviceForm.resolution_type || 'fixed';
    setActionLoading(true);
    try {
      const res = await fetch(`${API}/api/engineer/visit/${visit.id}/checkout`, {
        method: 'POST', headers: hdrs(),
        body: JSON.stringify({
          resolution_type: resolution,
          problem_found: serviceForm.problem_found,
          diagnosis: serviceForm.diagnosis,
          solution_applied: serviceForm.solution_applied,
          notes: serviceForm.notes,
          customer_name: customerName,
        }),
      });
      const d = await res.json();
      if (res.ok) {
        toast.success(`Visit completed. Ticket moved to '${d.next_stage}'`);
        setShowCheckout(false);
        fetchDetail();
        fetchVisit();
        fetchVisitHistory();
      } else {
        toast.error(d.detail || 'Checkout failed');
      }
    } catch { toast.error('Network error'); }
    finally { setActionLoading(false); }
  };

  const addPartItem = () => {
    if (!newPart.product_name) { toast.error('Enter part name'); return; }
    setPartsItems([...partsItems, { ...newPart }]);
    setNewPart({ product_name: '', quantity: 1, unit_price: 0, gst_slab: 18 });
  };

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!data) return null;

  const { ticket, company, site, employee, device, repair_history, schedules } = data;
  const isVisitActive = visit && visit.status === 'in_progress';
  const isVisitCompleted = visit && visit.status === 'completed';
  const canStartVisit = ticket.assignment_status === 'accepted' && !isVisitActive;

  return (
    <div className="space-y-4 max-w-5xl" data-testid="engineer-ticket-detail">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/engineer/dashboard')} data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="font-mono text-lg font-bold text-blue-600" data-testid="ticket-number">#{ticket.ticket_number}</span>
            <span className={`text-xs px-2 py-0.5 rounded ${priorityColors[ticket.priority_name] || 'bg-slate-100'}`}>{ticket.priority_name}</span>
            <span className="text-xs bg-blue-50 text-blue-700 px-2 py-0.5 rounded">{ticket.current_stage_name || 'Open'}</span>
            {ticket.assignment_status && (
              <span className={`text-xs px-2 py-0.5 rounded ${
                ticket.assignment_status === 'accepted' ? 'bg-green-50 text-green-700' :
                ticket.assignment_status === 'pending' ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'
              }`}>{ticket.assignment_status}</span>
            )}
          </div>
          <h1 className="text-xl font-bold text-slate-900 mt-1" data-testid="ticket-subject">{ticket.subject}</h1>
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════ */}
      {/* VISIT CONTROL BAR */}
      {/* ═══════════════════════════════════════════════════ */}
      {(canStartVisit || isVisitActive) && (
        <div className={`rounded-xl border-2 p-4 ${isVisitActive ? 'border-amber-400 bg-amber-50' : 'border-green-300 bg-green-50'}`} data-testid="visit-control">
          {/* Start Visit */}
          {canStartVisit && !isVisitActive && (
            <div className="flex items-center justify-between">
              <div>
                <p className="font-semibold text-green-800">Ready to Start Visit</p>
                <p className="text-xs text-green-600 mt-0.5">Check in when you arrive at the customer site</p>
              </div>
              <Button className="bg-green-600 hover:bg-green-700 text-white gap-2" onClick={handleStartVisit} disabled={actionLoading} data-testid="start-visit-btn">
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
                Start Visit
              </Button>
            </div>
          )}

          {/* Active Visit Controls */}
          {isVisitActive && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 bg-amber-500 rounded-full animate-pulse" />
                  <div>
                    <p className="font-semibold text-amber-800">Visit In Progress</p>
                    <p className="text-xs text-amber-600 mt-0.5">
                      Started: {new Date(visit.check_in_time).toLocaleString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Timer className="w-4 h-4 text-blue-600" />
                  <LiveTimer startTime={visit.check_in_time} />
                </div>
              </div>

              <div className="flex gap-2 flex-wrap">
                <Button size="sm" variant="outline" className="gap-1.5" onClick={() => setShowServiceForm(true)} data-testid="update-report-btn">
                  <Stethoscope className="w-3.5 h-3.5" />
                  {visit.problem_found ? 'Edit Report' : 'Add Report'}
                </Button>
                <Button size="sm" variant="outline" className="gap-1.5 text-purple-700 border-purple-200 hover:bg-purple-50" onClick={() => setShowPartsForm(true)} data-testid="request-parts-btn">
                  <Package className="w-3.5 h-3.5" />
                  Request Parts
                </Button>
                <Button size="sm" className="gap-1.5 bg-red-600 hover:bg-red-700 text-white ml-auto" onClick={() => setShowCheckout(true)} data-testid="checkout-btn">
                  <Square className="w-3.5 h-3.5" />
                  Check Out
                </Button>
              </div>

              {/* Quick status of what's been filled */}
              {(visit.problem_found || visit.diagnosis || visit.resolution_type) && (
                <div className="flex gap-2 flex-wrap text-[10px]">
                  {visit.problem_found && <span className="bg-white px-2 py-0.5 rounded border text-slate-600">Problem noted</span>}
                  {visit.diagnosis && <span className="bg-white px-2 py-0.5 rounded border text-slate-600">Diagnosis done</span>}
                  {visit.resolution_type && (
                    <span className={`px-2 py-0.5 rounded border ${
                      visit.resolution_type === 'fixed' ? 'bg-green-100 text-green-700' :
                      visit.resolution_type === 'parts_needed' ? 'bg-orange-100 text-orange-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {visit.resolution_type === 'fixed' ? 'Fixed' : visit.resolution_type === 'parts_needed' ? 'Parts Needed' : 'Escalation'}
                    </span>
                  )}
                  {visit.parts_request_id && <span className="bg-purple-100 text-purple-700 px-2 py-0.5 rounded border">Parts requested</span>}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Visit completed banner */}
      {isVisitCompleted && (
        <div className="rounded-xl border-2 border-green-300 bg-green-50 p-4" data-testid="visit-completed">
          <div className="flex items-center gap-3">
            <CheckCircle className="w-5 h-5 text-green-600" />
            <div>
              <p className="font-semibold text-green-800">Visit Completed</p>
              <p className="text-xs text-green-600">
                Duration: {visit.duration_minutes ? `${visit.duration_minutes} min` : 'N/A'} | Resolution: {visit.resolution_type || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-3 gap-4">
        {/* Left Column - Main Info */}
        <div className="col-span-2 space-y-4">
          {/* Job Details */}
          <Section icon={FileText} title="Job Details" color="text-blue-600">
            {ticket.description && (
              <div className="mb-3">
                <p className="text-xs text-slate-400 mb-1">Description / Fault</p>
                <p className="text-sm text-slate-700 whitespace-pre-wrap bg-slate-50 rounded-lg p-3">{ticket.description}</p>
              </div>
            )}
            <div className="grid grid-cols-2 gap-x-6">
              <InfoRow label="Help Topic" value={ticket.help_topic_name} />
              <InfoRow label="Category" value={ticket.category} />
              <InfoRow label="Created" value={ticket.created_at ? new Date(ticket.created_at).toLocaleString() : null} />
              <InfoRow label="Updated" value={ticket.updated_at ? new Date(ticket.updated_at).toLocaleString() : null} />
              {ticket.scheduled_at && <InfoRow label="Scheduled" value={new Date(ticket.scheduled_at).toLocaleString()} />}
            </div>
          </Section>

          {/* Device Info */}
          {device && (
            <Section icon={Monitor} title="Device Information" color="text-purple-600">
              <div className="grid grid-cols-2 gap-x-6">
                <InfoRow label="Name" value={device.name} />
                <InfoRow label="Model" value={device.model} />
                <InfoRow label="Serial No." value={device.serial_number} />
                <InfoRow label="Manufacturer" value={device.manufacturer} />
                <InfoRow label="Type" value={device.device_type} />
                <InfoRow label="IP Address" value={device.ip_address} />
                <InfoRow label="Location" value={device.location} />
                <InfoRow label="Purchase Date" value={device.purchase_date} />
                <InfoRow label="Warranty Until" value={device.warranty_end_date} />
                {device.warranty_status && (
                  <div className="flex items-start gap-2 py-1.5">
                    <span className="text-xs text-slate-400 w-28 shrink-0">Warranty</span>
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${
                      device.warranty_status === 'active' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'
                    }`}>{device.warranty_status}</span>
                  </div>
                )}
              </div>
            </Section>
          )}

          {/* Repair History */}
          {repair_history && repair_history.length > 0 && (
            <Section icon={Wrench} title={`Repair History (${repair_history.length})`} color="text-orange-600">
              <div className="space-y-2">
                {repair_history.map(h => (
                  <div key={h.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-slate-50">
                    <div className={`w-2 h-2 rounded-full ${h.is_open ? 'bg-blue-500' : 'bg-green-500'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold text-slate-600">#{h.ticket_number}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${h.is_open ? 'bg-blue-50 text-blue-600' : 'bg-green-50 text-green-600'}`}>
                          {h.is_open ? 'Open' : 'Resolved'}
                        </span>
                      </div>
                      <p className="text-xs text-slate-700 mt-0.5 truncate">{h.subject}</p>
                      <p className="text-[10px] text-slate-400">{h.assigned_to_name} &middot; {h.created_at ? new Date(h.created_at).toLocaleDateString() : ''}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Visit History */}
          {visitHistory.length > 0 && (
            <Section icon={Clock} title={`Visit History (${visitHistory.length})`} color="text-indigo-600">
              <div className="space-y-2">
                {visitHistory.map(v => (
                  <div key={v.id} className="p-3 rounded-lg border text-xs">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-slate-700">{v.engineer_name}</span>
                      <span className={`px-1.5 py-0.5 rounded ${
                        v.status === 'in_progress' ? 'bg-amber-50 text-amber-700' :
                        v.status === 'completed' ? 'bg-green-50 text-green-700' : 'bg-slate-100 text-slate-500'
                      }`}>{v.status}</span>
                    </div>
                    <p className="text-slate-500">
                      In: {v.check_in_time ? new Date(v.check_in_time).toLocaleString() : '-'}
                      {v.check_out_time && ` | Out: ${new Date(v.check_out_time).toLocaleString()}`}
                      {v.duration_minutes && ` | ${v.duration_minutes} min`}
                    </p>
                    {v.problem_found && <p className="text-slate-600 mt-1"><strong>Problem:</strong> {v.problem_found}</p>}
                    {v.solution_applied && <p className="text-slate-600"><strong>Solution:</strong> {v.solution_applied}</p>}
                    {v.resolution_type && (
                      <span className={`inline-block mt-1 px-1.5 py-0.5 rounded ${
                        v.resolution_type === 'fixed' ? 'bg-green-100 text-green-700' :
                        v.resolution_type === 'parts_needed' ? 'bg-orange-100 text-orange-700' : 'bg-red-100 text-red-700'
                      }`}>{v.resolution_type}</span>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* Timeline */}
          {ticket.timeline && ticket.timeline.length > 0 && (
            <Section icon={Clock} title="Timeline" color="text-slate-500">
              <div className="space-y-3">
                {[...ticket.timeline].reverse().map((entry, i) => (
                  <div key={entry.id || i} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className={`w-2.5 h-2.5 rounded-full mt-1 ${
                        entry.type?.includes('visit') ? 'bg-amber-500' :
                        entry.type?.includes('parts') ? 'bg-purple-500' :
                        entry.type?.includes('accepted') ? 'bg-green-500' :
                        entry.type?.includes('declined') ? 'bg-red-500' :
                        entry.type?.includes('assign') ? 'bg-blue-500' : 'bg-slate-300'
                      }`} />
                      {i < ticket.timeline.length - 1 && <div className="w-px flex-1 bg-slate-200 mt-1" />}
                    </div>
                    <div className="pb-3">
                      <p className="text-sm text-slate-700">{entry.description}</p>
                      <p className="text-[10px] text-slate-400 mt-0.5">
                        {entry.user_name} &middot; {entry.created_at ? new Date(entry.created_at).toLocaleString() : ''}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>

        {/* Right Column - Customer & Schedule */}
        <div className="space-y-4">
          {/* Company */}
          <Section icon={Building2} title="Company" color="text-indigo-600">
            {company ? (
              <div>
                <p className="font-semibold text-sm text-slate-800">{company.name}</p>
                {company.phone && <p className="text-xs text-slate-500 flex items-center gap-1 mt-1"><Phone className="w-3 h-3" />{company.phone}</p>}
                {company.email && <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5"><Mail className="w-3 h-3" />{company.email}</p>}
                {company.address && <p className="text-xs text-slate-400 mt-1"><MapPin className="w-3 h-3 inline mr-1" />{[company.address, company.city, company.state].filter(Boolean).join(', ')}</p>}
              </div>
            ) : (
              <p className="text-sm text-slate-800">{ticket.company_name || 'N/A'}</p>
            )}
          </Section>

          {/* Site */}
          {(site || ticket.site_address) && (
            <Section icon={MapPin} title="Site / Location" color="text-green-600">
              {site ? (
                <div>
                  <p className="font-semibold text-sm text-slate-800">{site.name}</p>
                  <p className="text-xs text-slate-500 mt-1">{[site.address, site.city, site.state, site.pincode].filter(Boolean).join(', ')}</p>
                  {site.contact_name && <p className="text-xs text-slate-500 mt-1"><User className="w-3 h-3 inline mr-1" />{site.contact_name}</p>}
                  {site.contact_phone && <p className="text-xs text-slate-500"><Phone className="w-3 h-3 inline mr-1" />{site.contact_phone}</p>}
                </div>
              ) : <p className="text-sm text-slate-700">{ticket.site_address}</p>}
            </Section>
          )}

          {/* Contact */}
          <Section icon={User} title="Contact Person" color="text-teal-600">
            {employee ? (
              <div>
                <p className="font-semibold text-sm text-slate-800">{employee.name}</p>
                {employee.designation && <p className="text-xs text-slate-400">{employee.designation}</p>}
                {employee.phone && <p className="text-xs text-slate-500 flex items-center gap-1 mt-1"><Phone className="w-3 h-3" />{employee.phone}</p>}
                {employee.email && <p className="text-xs text-slate-500 flex items-center gap-1"><Mail className="w-3 h-3" />{employee.email}</p>}
              </div>
            ) : (
              <div>
                {ticket.contact_name && <p className="font-semibold text-sm text-slate-800">{ticket.contact_name}</p>}
                {ticket.contact_phone && <p className="text-xs text-slate-500 flex items-center gap-1 mt-1"><Phone className="w-3 h-3" />{ticket.contact_phone}</p>}
                {ticket.contact_email && <p className="text-xs text-slate-500 flex items-center gap-1"><Mail className="w-3 h-3" />{ticket.contact_email}</p>}
              </div>
            )}
          </Section>

          {/* Scheduled Visits */}
          {schedules && schedules.length > 0 && (
            <Section icon={Calendar} title="Scheduled Visits" color="text-blue-600">
              <div className="space-y-2">
                {schedules.map(s => (
                  <div key={s.id} className="p-2.5 rounded-lg border text-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-medium text-slate-700">{new Date(s.scheduled_at).toLocaleString()}</span>
                      <span className={`px-1.5 py-0.5 rounded ${
                        s.status === 'accepted' ? 'bg-green-50 text-green-600' :
                        s.status === 'completed' ? 'bg-blue-50 text-blue-600' : 'bg-slate-100 text-slate-500'
                      }`}>{s.status}</span>
                    </div>
                    {s.notes && <p className="text-slate-400 mt-1">{s.notes}</p>}
                  </div>
                ))}
              </div>
            </Section>
          )}
        </div>
      </div>

      {/* ═══════════════════════════════════════════════════ */}
      {/* SERVICE REPORT DIALOG */}
      {/* ═══════════════════════════════════════════════════ */}
      {showServiceForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="service-report-dialog">
          <div className="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-xl">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold text-slate-800">Service Report</h3>
              <button onClick={() => setShowServiceForm(false)} className="p-1 hover:bg-slate-100 rounded"><X className="w-4 h-4" /></button>
            </div>
            <div className="p-4 space-y-4">
              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Problem Found *</label>
                <textarea className="w-full border rounded-lg px-3 py-2 text-sm resize-none" rows={3} placeholder="Describe the problem..."
                  value={serviceForm.problem_found} onChange={e => setServiceForm({...serviceForm, problem_found: e.target.value})} data-testid="problem-found" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Diagnosis</label>
                <textarea className="w-full border rounded-lg px-3 py-2 text-sm resize-none" rows={2} placeholder="Root cause analysis..."
                  value={serviceForm.diagnosis} onChange={e => setServiceForm({...serviceForm, diagnosis: e.target.value})} data-testid="diagnosis" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Solution Applied</label>
                <textarea className="w-full border rounded-lg px-3 py-2 text-sm resize-none" rows={2} placeholder="What was done to fix..."
                  value={serviceForm.solution_applied} onChange={e => setServiceForm({...serviceForm, solution_applied: e.target.value})} data-testid="solution-applied" />
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Resolution</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { val: 'fixed', label: 'Fixed', icon: CircleCheck, color: 'green' },
                    { val: 'parts_needed', label: 'Parts Needed', icon: Package, color: 'orange' },
                    { val: 'escalation', label: 'Escalate', icon: CircleAlert, color: 'red' },
                  ].map(opt => (
                    <button key={opt.val} type="button" data-testid={`resolution-${opt.val}`}
                      className={`p-2 rounded-lg border text-xs font-medium flex flex-col items-center gap-1 transition-all ${
                        serviceForm.resolution_type === opt.val
                          ? `bg-${opt.color}-50 border-${opt.color}-400 text-${opt.color}-700 ring-1 ring-${opt.color}-300`
                          : 'hover:bg-slate-50'
                      }`}
                      onClick={() => setServiceForm({...serviceForm, resolution_type: opt.val})}>
                      <opt.icon className="w-4 h-4" />
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Notes</label>
                <textarea className="w-full border rounded-lg px-3 py-2 text-sm resize-none" rows={2} placeholder="Additional notes..."
                  value={serviceForm.notes} onChange={e => setServiceForm({...serviceForm, notes: e.target.value})} data-testid="visit-notes" />
              </div>
              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setShowServiceForm(false)}>Cancel</Button>
                <Button onClick={handleUpdateVisit} disabled={actionLoading || !serviceForm.problem_found} data-testid="save-report-btn">
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : null}
                  Save Report
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════ */}
      {/* PARTS REQUEST DIALOG */}
      {/* ═══════════════════════════════════════════════════ */}
      {showPartsForm && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="parts-request-dialog">
          <div className="bg-white rounded-xl w-full max-w-lg max-h-[90vh] overflow-y-auto shadow-xl">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold text-slate-800">Request Parts</h3>
              <button onClick={() => setShowPartsForm(false)} className="p-1 hover:bg-slate-100 rounded"><X className="w-4 h-4" /></button>
            </div>
            <div className="p-4 space-y-4">
              <p className="text-xs text-slate-500">Add parts needed. A quotation will be auto-created for back office review.</p>

              {/* Add part form */}
              <div className="grid grid-cols-12 gap-2 items-end">
                <div className="col-span-5">
                  <label className="text-[10px] text-slate-500 block mb-0.5">Part Name *</label>
                  <input className="w-full border rounded px-2 py-1.5 text-sm" placeholder="e.g., RAM 8GB DDR4"
                    value={newPart.product_name} onChange={e => setNewPart({...newPart, product_name: e.target.value})} data-testid="part-name-input" />
                </div>
                <div className="col-span-2">
                  <label className="text-[10px] text-slate-500 block mb-0.5">Qty</label>
                  <input type="number" min="1" className="w-full border rounded px-2 py-1.5 text-sm"
                    value={newPart.quantity} onChange={e => setNewPart({...newPart, quantity: parseInt(e.target.value) || 1})} />
                </div>
                <div className="col-span-3">
                  <label className="text-[10px] text-slate-500 block mb-0.5">Unit Price</label>
                  <input type="number" min="0" step="0.01" className="w-full border rounded px-2 py-1.5 text-sm"
                    value={newPart.unit_price} onChange={e => setNewPart({...newPart, unit_price: parseFloat(e.target.value) || 0})} />
                </div>
                <div className="col-span-2">
                  <Button size="sm" variant="outline" onClick={addPartItem} data-testid="add-part-btn">Add</Button>
                </div>
              </div>

              {/* Parts list */}
              {partsItems.length > 0 && (
                <div className="border rounded-lg overflow-hidden">
                  <table className="w-full text-xs">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="text-left px-3 py-2 font-medium text-slate-500">Part</th>
                        <th className="text-center px-2 py-2 font-medium text-slate-500">Qty</th>
                        <th className="text-right px-2 py-2 font-medium text-slate-500">Price</th>
                        <th className="text-right px-3 py-2 font-medium text-slate-500">Total</th>
                        <th className="w-8"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {partsItems.map((p, i) => {
                        const lineTotal = p.unit_price * p.quantity;
                        const gst = lineTotal * p.gst_slab / 100;
                        return (
                          <tr key={i} className="border-t">
                            <td className="px-3 py-2 font-medium text-slate-700">{p.product_name}</td>
                            <td className="text-center px-2 py-2">{p.quantity}</td>
                            <td className="text-right px-2 py-2">{p.unit_price.toFixed(2)}</td>
                            <td className="text-right px-3 py-2 font-medium">{(lineTotal + gst).toFixed(2)}</td>
                            <td className="px-1">
                              <button onClick={() => setPartsItems(partsItems.filter((_, j) => j !== i))} className="text-red-400 hover:text-red-600">
                                <X className="w-3 h-3" />
                              </button>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}

              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Notes</label>
                <textarea className="w-full border rounded-lg px-3 py-2 text-sm resize-none" rows={2} placeholder="Any notes for back office..."
                  value={partsNotes} onChange={e => setPartsNotes(e.target.value)} />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setShowPartsForm(false)}>Cancel</Button>
                <Button onClick={handleRequestParts} disabled={actionLoading || partsItems.length === 0} className="bg-purple-600 hover:bg-purple-700" data-testid="submit-parts-btn">
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Send className="w-3.5 h-3.5 mr-1" />}
                  Submit Parts Request
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ═══════════════════════════════════════════════════ */}
      {/* CHECKOUT DIALOG */}
      {/* ═══════════════════════════════════════════════════ */}
      {showCheckout && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4" data-testid="checkout-dialog">
          <div className="bg-white rounded-xl w-full max-w-md shadow-xl">
            <div className="flex items-center justify-between p-4 border-b">
              <h3 className="font-semibold text-slate-800">Check Out & Complete Visit</h3>
              <button onClick={() => setShowCheckout(false)} className="p-1 hover:bg-slate-100 rounded"><X className="w-4 h-4" /></button>
            </div>
            <div className="p-4 space-y-4">
              {visit && (
                <div className="bg-slate-50 rounded-lg p-3 text-xs space-y-1">
                  <p><strong>Duration:</strong> <LiveTimer startTime={visit.check_in_time} /></p>
                  {visit.problem_found && <p><strong>Problem:</strong> {visit.problem_found}</p>}
                  {visit.solution_applied && <p><strong>Solution:</strong> {visit.solution_applied}</p>}
                </div>
              )}

              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1.5">Resolution Type *</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { val: 'fixed', label: 'Fixed', color: 'bg-green-600' },
                    { val: 'parts_needed', label: 'Parts Needed', color: 'bg-orange-500' },
                    { val: 'escalation', label: 'Escalate', color: 'bg-red-500' },
                  ].map(opt => (
                    <button key={opt.val} type="button"
                      className={`p-2 rounded-lg border text-xs font-medium transition-all ${
                        serviceForm.resolution_type === opt.val ? `${opt.color} text-white` : 'hover:bg-slate-50'
                      }`}
                      onClick={() => setServiceForm({...serviceForm, resolution_type: opt.val})} data-testid={`checkout-resolution-${opt.val}`}>
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="text-xs font-medium text-slate-600 block mb-1">Customer Name (optional)</label>
                <input className="w-full border rounded-lg px-3 py-2 text-sm" placeholder="Name of person who received service"
                  value={customerName} onChange={e => setCustomerName(e.target.value)} data-testid="customer-name" />
              </div>

              <div className="flex gap-2 justify-end pt-2">
                <Button variant="outline" onClick={() => setShowCheckout(false)}>Cancel</Button>
                <Button onClick={handleCheckout} disabled={actionLoading || !serviceForm.resolution_type} className="bg-red-600 hover:bg-red-700" data-testid="confirm-checkout-btn">
                  {actionLoading ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <Square className="w-3.5 h-3.5 mr-1" />}
                  Check Out
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
