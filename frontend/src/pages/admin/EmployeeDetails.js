import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, User, Building2, Mail, Phone, MapPin, Briefcase, 
  Laptop, Key, Shield, Ticket, Wrench, Calendar, AlertTriangle,
  CheckCircle, Clock, ExternalLink, ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusColors = {
  active: 'bg-emerald-100 text-emerald-700',
  in_repair: 'bg-amber-100 text-amber-700',
  retired: 'bg-slate-100 text-slate-600',
  expiring: 'bg-amber-100 text-amber-700',
  expired: 'bg-red-100 text-red-700',
  open: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-amber-100 text-amber-700',
  resolved: 'bg-emerald-100 text-emerald-700',
  closed: 'bg-slate-100 text-slate-600'
};

const EmployeeDetails = () => {
  const { employeeId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('devices');

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/admin/company-employees/${employeeId}/full-profile`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(res.data);
    } catch (error) {
      toast.error('Failed to load employee details');
      navigate('/admin/employees');
    } finally {
      setLoading(false);
    }
  }, [employeeId, token, navigate]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', { 
      day: 'numeric', month: 'short', year: 'numeric' 
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!data) return null;

  const { employee, summary, devices, licenses, subscriptions, service_history, tickets } = data;

  const tabs = [
    { id: 'devices', label: 'Devices', icon: Laptop, count: summary.total_devices },
    { id: 'licenses', label: 'Licenses', icon: Key, count: summary.total_licenses },
    { id: 'subscriptions', label: 'Subscriptions', icon: Mail, count: subscriptions?.length || 0 },
    { id: 'service', label: 'Service History', icon: Wrench, count: summary.total_service_records },
    { id: 'tickets', label: 'Tickets', icon: Ticket, count: tickets?.length || 0 },
  ];

  return (
    <div className="space-y-6" data-testid="employee-details-page">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate('/admin/employees')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Employee Profile</h1>
          <p className="text-slate-500">View all devices, licenses, and related information</p>
        </div>
      </div>

      {/* Employee Info Card */}
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <div className="flex items-start gap-6">
          <div className="w-20 h-20 rounded-full bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center text-white text-3xl font-bold">
            {employee.name?.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">{employee.name}</h2>
                {employee.designation && (
                  <p className="text-slate-600">{employee.designation}</p>
                )}
              </div>
              {employee.employee_id && (
                <span className="px-3 py-1 bg-slate-100 rounded-lg text-sm font-mono">
                  ID: {employee.employee_id}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <div className="flex items-center gap-2 text-slate-600">
                <Building2 className="h-4 w-4 text-slate-400" />
                <span className="text-sm">{employee.company_name}</span>
              </div>
              {employee.department && (
                <div className="flex items-center gap-2 text-slate-600">
                  <Briefcase className="h-4 w-4 text-slate-400" />
                  <span className="text-sm">{employee.department}</span>
                </div>
              )}
              {employee.email && (
                <div className="flex items-center gap-2 text-slate-600">
                  <Mail className="h-4 w-4 text-slate-400" />
                  <span className="text-sm">{employee.email}</span>
                </div>
              )}
              {employee.phone && (
                <div className="flex items-center gap-2 text-slate-600">
                  <Phone className="h-4 w-4 text-slate-400" />
                  <span className="text-sm">{employee.phone}</span>
                </div>
              )}
              {employee.location && (
                <div className="flex items-center gap-2 text-slate-600">
                  <MapPin className="h-4 w-4 text-slate-400" />
                  <span className="text-sm">{employee.location}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Laptop className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{summary.total_devices}</p>
              <p className="text-xs text-slate-500">Devices</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Shield className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{summary.devices_under_warranty}</p>
              <p className="text-xs text-slate-500">Under Warranty</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Key className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{summary.total_licenses}</p>
              <p className="text-xs text-slate-500">Licenses</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Wrench className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{summary.total_service_records}</p>
              <p className="text-xs text-slate-500">Services</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
              <Ticket className="h-5 w-5 text-red-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{summary.open_tickets}</p>
              <p className="text-xs text-slate-500">Open Tickets</p>
            </div>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-slate-100">
        <div className="border-b border-slate-100 p-1 flex gap-1 overflow-x-auto">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'bg-[#0F62FE] text-white'
                    : 'text-slate-600 hover:bg-slate-50'
                }`}
              >
                <Icon className="h-4 w-4" />
                {tab.label}
                {tab.count > 0 && (
                  <span className={`px-2 py-0.5 rounded-full text-xs ${
                    activeTab === tab.id ? 'bg-white/20' : 'bg-slate-100'
                  }`}>
                    {tab.count}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="p-6">
          {/* Devices Tab */}
          {activeTab === 'devices' && (
            <div className="space-y-4">
              {devices.length > 0 ? (
                devices.map((device) => (
                  <div 
                    key={device.id} 
                    className="bg-slate-50 rounded-lg p-4 hover:bg-slate-100 transition-colors cursor-pointer"
                    onClick={() => navigate(`/admin/devices?q=${device.serial_number}`)}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-lg bg-white border border-slate-200 flex items-center justify-center">
                          <Laptop className="h-6 w-6 text-slate-400" />
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <h4 className="font-semibold text-slate-900">
                              {device.brand} {device.model || device.device_type}
                            </h4>
                            <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[device.status] || 'bg-slate-100'}`}>
                              {device.status}
                            </span>
                          </div>
                          <p className="text-sm text-slate-500 font-mono">{device.serial_number}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                            <span>Type: {device.device_type}</span>
                            {device.warranty_end_date && (
                              <span className={`flex items-center gap-1 ${
                                device.warranty_status === 'active' ? 'text-emerald-600' :
                                device.warranty_status === 'expiring' ? 'text-amber-600' : 'text-red-600'
                              }`}>
                                <Shield className="h-3 w-3" />
                                Warranty: {formatDate(device.warranty_end_date)}
                                {device.warranty_days_remaining !== undefined && (
                                  <span>({device.warranty_days_remaining} days)</span>
                                )}
                              </span>
                            )}
                          </div>
                          {device.configuration && (
                            <p className="text-xs text-slate-400 mt-1 line-clamp-1">
                              Config: {device.configuration}
                            </p>
                          )}
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-slate-400" />
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Laptop className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                  <p>No devices assigned to this employee</p>
                </div>
              )}
            </div>
          )}

          {/* Licenses Tab */}
          {activeTab === 'licenses' && (
            <div className="space-y-4">
              {licenses.length > 0 ? (
                licenses.map((license) => (
                  <div key={license.id} className="bg-slate-50 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                          <Key className="h-6 w-6 text-purple-600" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-slate-900">{license.software_name}</h4>
                          <p className="text-sm text-slate-500">{license.license_type} License</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                            {license.license_key && (
                              <span className="font-mono bg-slate-200 px-2 py-0.5 rounded">
                                {license.license_key.substring(0, 20)}...
                              </span>
                            )}
                            {license.expiry_date && (
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                Expires: {formatDate(license.expiry_date)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${statusColors[license.status] || 'bg-slate-100'}`}>
                        {license.status}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Key className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                  <p>No licenses assigned to this employee</p>
                </div>
              )}
            </div>
          )}

          {/* Subscriptions Tab */}
          {activeTab === 'subscriptions' && (
            <div className="space-y-4">
              <p className="text-sm text-slate-500 mb-4">
                Email/Cloud subscriptions available for {employee.company_name}
              </p>
              {subscriptions.length > 0 ? (
                subscriptions.map((sub) => (
                  <div key={sub.id} className="bg-slate-50 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center">
                          <Mail className="h-6 w-6 text-blue-600" />
                        </div>
                        <div>
                          <h4 className="font-semibold text-slate-900">{sub.provider_name || sub.provider}</h4>
                          <p className="text-sm text-blue-600">{sub.domain}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                            <span>Plan: {sub.plan_name || sub.plan_type}</span>
                            <span>Users: {sub.num_users}</span>
                            {sub.renewal_date && (
                              <span className="flex items-center gap-1">
                                <Calendar className="h-3 w-3" />
                                Renews: {formatDate(sub.renewal_date)}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${statusColors[sub.status] || 'bg-slate-100'}`}>
                        {sub.status?.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Mail className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                  <p>No subscriptions found for this company</p>
                </div>
              )}
            </div>
          )}

          {/* Service History Tab */}
          {activeTab === 'service' && (
            <div className="space-y-4">
              {service_history.length > 0 ? (
                service_history.map((record) => (
                  <div key={record.id} className="bg-slate-50 rounded-lg p-4">
                    <div className="flex items-start gap-4">
                      <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                        <Wrench className="h-5 w-5 text-amber-600" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-start justify-between">
                          <div>
                            <h4 className="font-semibold text-slate-900">{record.service_type}</h4>
                            <p className="text-sm text-slate-500">{record.description}</p>
                          </div>
                          <span className="text-xs text-slate-500">{formatDate(record.service_date)}</span>
                        </div>
                        <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                          {record.technician_name && <span>Tech: {record.technician_name}</span>}
                          {record.cost && <span>Cost: ₹{record.cost}</span>}
                          <span className={`px-2 py-0.5 rounded-full ${statusColors[record.status] || 'bg-slate-100'}`}>
                            {record.status}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Wrench className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                  <p>No service history for this employee's devices</p>
                </div>
              )}
            </div>
          )}

          {/* Tickets Tab */}
          {activeTab === 'tickets' && (
            <div className="space-y-4">
              {tickets.length > 0 ? (
                tickets.map((ticket) => (
                  <div key={ticket.id} className="bg-slate-50 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-4">
                        <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                          ticket.status === 'open' ? 'bg-blue-100' :
                          ticket.status === 'in_progress' ? 'bg-amber-100' : 'bg-emerald-100'
                        }`}>
                          <Ticket className={`h-5 w-5 ${
                            ticket.status === 'open' ? 'text-blue-600' :
                            ticket.status === 'in_progress' ? 'text-amber-600' : 'text-emerald-600'
                          }`} />
                        </div>
                        <div>
                          <h4 className="font-semibold text-slate-900">{ticket.subject}</h4>
                          <p className="text-sm text-slate-500 line-clamp-2">{ticket.description}</p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                            <span className="font-mono">{ticket.ticket_number}</span>
                            <span>Priority: {ticket.priority}</span>
                            <span>{formatDate(ticket.created_at)}</span>
                          </div>
                        </div>
                      </div>
                      <span className={`text-xs px-2 py-1 rounded-full ${statusColors[ticket.status] || 'bg-slate-100'}`}>
                        {ticket.status?.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <Ticket className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                  <p>No tickets found for this employee</p>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default EmployeeDetails;
