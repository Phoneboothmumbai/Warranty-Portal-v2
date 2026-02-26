import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  ArrowLeft, Building2, MapPin, User, Monitor, Clock, Phone, Mail,
  FileText, Calendar, Wrench, AlertTriangle, CheckCircle, ChevronRight,
  Shield, Hash, Info
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

const Section = ({ icon: Icon, title, children, color = 'text-slate-600' }) => (
  <div className="bg-white border rounded-lg overflow-hidden" data-testid={`section-${title.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center gap-2 px-4 py-3 border-b bg-slate-50">
      <Icon className={`w-4 h-4 ${color}`} />
      <h3 className="text-sm font-semibold text-slate-700">{title}</h3>
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

export default function EngineerTicketDetail() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const { token } = useEngineerAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const hdrs = useCallback(() => ({
    'Content-Type': 'application/json',
    Authorization: `Bearer ${token}`,
  }), [token]);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const res = await fetch(`${API}/api/engineer/ticket/${ticketId}`, { headers: hdrs() });
        if (!res.ok) { toast.error('Failed to load ticket'); navigate('/engineer/dashboard'); return; }
        setData(await res.json());
      } catch { toast.error('Network error'); }
      finally { setLoading(false); }
    };
    fetchDetail();
  }, [ticketId, hdrs, navigate]);

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!data) return null;

  const { ticket, company, site, employee, device, repair_history, schedules } = data;

  return (
    <div className="space-y-4 max-w-5xl" data-testid="engineer-ticket-detail">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Button variant="ghost" size="sm" onClick={() => navigate('/engineer/dashboard')} data-testid="back-btn">
          <ArrowLeft className="w-4 h-4 mr-1" /> Back
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
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
              {ticket.device_description && <InfoRow label="Device (manual)" value={ticket.device_description} />}
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
                <InfoRow label="MAC Address" value={device.mac_address} />
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
                {device.notes && <InfoRow label="Notes" value={device.notes} />}
              </div>
            </Section>
          )}

          {/* Repair History */}
          {repair_history.length > 0 && (
            <Section icon={Wrench} title={`Repair History (${repair_history.length})`} color="text-orange-600">
              <div className="space-y-2">
                {repair_history.map(h => (
                  <div key={h.id} className="flex items-center gap-3 p-3 rounded-lg border hover:bg-slate-50">
                    <div className={`w-2 h-2 rounded-full ${h.is_open ? 'bg-blue-500' : 'bg-green-500'}`} />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-xs font-semibold text-slate-600">#{h.ticket_number}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${priorityColors[h.priority_name] || 'bg-slate-100'}`}>{h.priority_name}</span>
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

          {/* Timeline */}
          {ticket.timeline && ticket.timeline.length > 0 && (
            <Section icon={Clock} title="Timeline" color="text-slate-500">
              <div className="space-y-3">
                {[...ticket.timeline].reverse().map((entry, i) => (
                  <div key={entry.id || i} className="flex gap-3">
                    <div className="flex flex-col items-center">
                      <div className={`w-2.5 h-2.5 rounded-full mt-1 ${
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

          {/* Site/Location */}
          {(site || ticket.site_address) && (
            <Section icon={MapPin} title="Site / Location" color="text-green-600">
              {site ? (
                <div>
                  <p className="font-semibold text-sm text-slate-800">{site.name}</p>
                  <p className="text-xs text-slate-500 mt-1">{[site.address, site.city, site.state, site.pincode].filter(Boolean).join(', ')}</p>
                  {site.contact_name && <p className="text-xs text-slate-500 mt-1"><User className="w-3 h-3 inline mr-1" />{site.contact_name}</p>}
                  {site.contact_phone && <p className="text-xs text-slate-500"><Phone className="w-3 h-3 inline mr-1" />{site.contact_phone}</p>}
                </div>
              ) : (
                <p className="text-sm text-slate-700">{ticket.site_address}</p>
              )}
            </Section>
          )}

          {/* Contact / Employee */}
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
                {!ticket.contact_name && !employee && <p className="text-xs text-slate-400">No contact info</p>}
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
    </div>
  );
}
