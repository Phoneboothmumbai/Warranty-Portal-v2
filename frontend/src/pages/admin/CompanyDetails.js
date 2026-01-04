import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Building2, ArrowLeft, Edit2, Save, X, MapPin, Users, Laptop, Package, 
  FileText, Shield, Wrench, Mail, Phone, Calendar, CheckCircle2, XCircle,
  AlertCircle, Clock, ChevronRight, KeyRound, Plus, Eye, EyeOff, Trash2
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TABS = [
  { id: 'overview', label: 'Overview', icon: Building2 },
  { id: 'portal_users', label: 'Portal Logins', icon: KeyRound },
  { id: 'sites', label: 'Sites', icon: MapPin },
  { id: 'users', label: 'Users/Contacts', icon: Users },
  { id: 'devices', label: 'Devices', icon: Laptop },
  { id: 'deployments', label: 'Deployments', icon: Package },
  { id: 'licenses', label: 'Licenses', icon: FileText },
  { id: 'amc', label: 'AMC Contracts', icon: Shield },
  { id: 'services', label: 'Service History', icon: Wrench },
];

const CompanyDetails = () => {
  const { companyId } = useParams();
  const navigate = useNavigate();
  const { token } = useAuth();
  
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isEditing, setIsEditing] = useState(false);
  const [editForm, setEditForm] = useState({});
  const [saving, setSaving] = useState(false);
  
  // Portal Users state
  const [portalUsers, setPortalUsers] = useState([]);
  const [loadingPortalUsers, setLoadingPortalUsers] = useState(false);
  const [showAddPortalUser, setShowAddPortalUser] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [newPortalUser, setNewPortalUser] = useState({
    name: '',
    email: '',
    phone: '',
    password: '',
    role: 'company_viewer'
  });

  useEffect(() => {
    fetchCompanyOverview();
  }, [companyId]);

  const fetchCompanyOverview = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/admin/companies/${companyId}/overview`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
      setEditForm(response.data.company);
    } catch (error) {
      toast.error('Failed to load company details');
      navigate('/admin/companies');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveCompany = async () => {
    try {
      setSaving(true);
      await axios.put(`${API}/admin/companies/${companyId}`, editForm, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Company updated successfully');
      setIsEditing(false);
      fetchCompanyOverview();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update company');
    } finally {
      setSaving(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!data) return null;

  const { company, summary, devices, sites, users, deployments, licenses, amc_contracts, services } = data;

  return (
    <div className="space-y-6" data-testid="company-details-page">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <Button 
            variant="ghost" 
            size="icon" 
            onClick={() => navigate('/admin/companies')}
            className="shrink-0"
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 bg-blue-50 rounded-xl flex items-center justify-center">
              <Building2 className="h-8 w-8 text-blue-600" />
            </div>
            <div>
              <h1 className="text-2xl font-semibold text-slate-900">{company.name}</h1>
              <p className="text-slate-500 flex items-center gap-2 mt-1">
                <span className="text-sm">{company.code || company.id?.slice(0, 8)}</span>
                <span className={`px-2 py-0.5 rounded-full text-xs ${company.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                  {company.status || 'Active'}
                </span>
              </p>
            </div>
          </div>
        </div>
        <Button 
          onClick={() => setIsEditing(true)}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
        >
          <Edit2 className="h-4 w-4 mr-2" />
          Edit Company
        </Button>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
            <MapPin className="h-4 w-4" />
            Sites
          </div>
          <p className="text-2xl font-semibold text-slate-900">{summary.total_sites}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
            <Users className="h-4 w-4" />
            Users
          </div>
          <p className="text-2xl font-semibold text-slate-900">{summary.total_users}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
            <Laptop className="h-4 w-4" />
            Devices
          </div>
          <p className="text-2xl font-semibold text-slate-900">{summary.total_devices}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-2 text-emerald-600 text-sm mb-1">
            <CheckCircle2 className="h-4 w-4" />
            Active Warranties
          </div>
          <p className="text-2xl font-semibold text-emerald-600">{summary.active_warranties}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-2 text-blue-600 text-sm mb-1">
            <Shield className="h-4 w-4" />
            AMC Covered
          </div>
          <p className="text-2xl font-semibold text-blue-600">{summary.active_amc_devices}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-2 text-slate-500 text-sm mb-1">
            <Wrench className="h-4 w-4" />
            Service Records
          </div>
          <p className="text-2xl font-semibold text-slate-900">{summary.total_service_records}</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <div className="border-b border-slate-100 overflow-x-auto">
          <div className="flex">
            {TABS.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center gap-2 px-5 py-4 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                    activeTab === tab.id
                      ? 'border-[#0F62FE] text-[#0F62FE]'
                      : 'border-transparent text-slate-500 hover:text-slate-700'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>

        <div className="p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-4">
                  <h3 className="font-medium text-slate-900">Contact Information</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <Users className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="text-xs text-slate-500">Contact Person</p>
                        <p className="text-sm font-medium">{company.contact_person || '-'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Mail className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="text-xs text-slate-500">Email</p>
                        <p className="text-sm font-medium">{company.email || '-'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Phone className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="text-xs text-slate-500">Phone</p>
                        <p className="text-sm font-medium">{company.phone || '-'}</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="space-y-4">
                  <h3 className="font-medium text-slate-900">Additional Details</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <MapPin className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="text-xs text-slate-500">Address</p>
                        <p className="text-sm font-medium">{company.address || '-'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <FileText className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="text-xs text-slate-500">GST Number</p>
                        <p className="text-sm font-medium">{company.gst_number || '-'}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <Calendar className="h-4 w-4 text-slate-400" />
                      <div>
                        <p className="text-xs text-slate-500">Created</p>
                        <p className="text-sm font-medium">{formatDate(company.created_at)}</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Sites Tab */}
          {activeTab === 'sites' && (
            <div>
              {sites.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full table-modern">
                    <thead>
                      <tr>
                        <th>Site Name</th>
                        <th>Address</th>
                        <th>Contact</th>
                        <th>Status</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {sites.map((site) => (
                        <tr key={site.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 bg-slate-100 rounded-lg flex items-center justify-center">
                                <MapPin className="h-4 w-4 text-slate-600" />
                              </div>
                              <span className="font-medium">{site.name}</span>
                            </div>
                          </td>
                          <td className="text-sm text-slate-600">{site.address || '-'}</td>
                          <td className="text-sm">{site.contact_person || '-'}</td>
                          <td>
                            <span className={`px-2 py-1 rounded-full text-xs ${site.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                              {site.status || 'Active'}
                            </span>
                          </td>
                          <td>
                            <Link to={`/admin/sites?id=${site.id}`} className="text-[#0F62FE] hover:underline text-sm">
                              View
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState icon={MapPin} message="No sites found for this company" />
              )}
            </div>
          )}

          {/* Users Tab */}
          {activeTab === 'users' && (
            <div>
              {users.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full table-modern">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Department</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {users.map((user) => (
                        <tr key={user.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 bg-blue-50 rounded-full flex items-center justify-center">
                                <span className="text-sm font-medium text-blue-600">
                                  {user.name?.charAt(0)?.toUpperCase() || 'U'}
                                </span>
                              </div>
                              <span className="font-medium">{user.name}</span>
                            </div>
                          </td>
                          <td className="text-sm">{user.email || '-'}</td>
                          <td className="text-sm">{user.phone || '-'}</td>
                          <td className="text-sm text-slate-600">{user.department || '-'}</td>
                          <td>
                            <span className={`px-2 py-1 rounded-full text-xs ${user.status === 'active' ? 'bg-emerald-50 text-emerald-700' : 'bg-slate-100 text-slate-600'}`}>
                              {user.status || 'Active'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState icon={Users} message="No users/contacts found for this company" />
              )}
            </div>
          )}

          {/* Devices Tab */}
          {activeTab === 'devices' && (
            <div>
              {devices.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full table-modern">
                    <thead>
                      <tr>
                        <th>Device</th>
                        <th>Serial Number</th>
                        <th>Asset Tag</th>
                        <th>Warranty</th>
                        <th>AMC</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {devices.map((device) => (
                        <tr key={device.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 bg-slate-100 rounded-lg flex items-center justify-center">
                                <Laptop className="h-4 w-4 text-slate-600" />
                              </div>
                              <div>
                                <p className="font-medium">{device.brand} {device.model}</p>
                                <p className="text-xs text-slate-500">{device.device_type}</p>
                              </div>
                            </div>
                          </td>
                          <td className="text-sm font-mono">{device.serial_number}</td>
                          <td className="text-sm">{device.asset_tag || '-'}</td>
                          <td>
                            {device.warranty_active ? (
                              <span className="flex items-center gap-1 text-emerald-600 text-sm">
                                <CheckCircle2 className="h-4 w-4" />
                                Active
                              </span>
                            ) : (
                              <span className="flex items-center gap-1 text-slate-400 text-sm">
                                <XCircle className="h-4 w-4" />
                                Expired
                              </span>
                            )}
                          </td>
                          <td>
                            {device.amc_status === 'active' ? (
                              <span className="px-2 py-1 bg-blue-50 text-blue-700 rounded-full text-xs">
                                AMC Active
                              </span>
                            ) : (
                              <span className="text-slate-400 text-sm">-</span>
                            )}
                          </td>
                          <td>
                            <Link to={`/admin/devices?id=${device.id}`} className="text-[#0F62FE] hover:underline text-sm">
                              View
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState icon={Laptop} message="No devices found for this company" />
              )}
            </div>
          )}

          {/* Deployments Tab */}
          {activeTab === 'deployments' && (
            <div>
              {deployments.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full table-modern">
                    <thead>
                      <tr>
                        <th>Deployment</th>
                        <th>Site</th>
                        <th>Date</th>
                        <th>Items</th>
                        <th>Installed By</th>
                        <th></th>
                      </tr>
                    </thead>
                    <tbody>
                      {deployments.map((dep) => (
                        <tr key={dep.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 bg-emerald-50 rounded-lg flex items-center justify-center">
                                <Package className="h-4 w-4 text-emerald-600" />
                              </div>
                              <span className="font-medium">{dep.name}</span>
                            </div>
                          </td>
                          <td className="text-sm">{dep.site_name}</td>
                          <td className="text-sm">{formatDate(dep.deployment_date)}</td>
                          <td className="text-sm font-medium">{dep.items_count} items</td>
                          <td className="text-sm text-slate-600">{dep.installed_by || '-'}</td>
                          <td>
                            <Link to={`/admin/deployments?id=${dep.id}`} className="text-[#0F62FE] hover:underline text-sm">
                              View
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState icon={Package} message="No deployments found for this company" />
              )}
            </div>
          )}

          {/* Licenses Tab */}
          {activeTab === 'licenses' && (
            <div>
              {licenses.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full table-modern">
                    <thead>
                      <tr>
                        <th>Software</th>
                        <th>License Type</th>
                        <th>Seats</th>
                        <th>Expiry</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {licenses.map((lic) => (
                        <tr key={lic.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 bg-purple-50 rounded-lg flex items-center justify-center">
                                <FileText className="h-4 w-4 text-purple-600" />
                              </div>
                              <span className="font-medium">{lic.software_name}</span>
                            </div>
                          </td>
                          <td className="text-sm">{lic.license_type || '-'}</td>
                          <td className="text-sm">{lic.seats || '-'}</td>
                          <td className="text-sm">{formatDate(lic.end_date)}</td>
                          <td>
                            {!lic.is_expired ? (
                              <span className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs">Active</span>
                            ) : (
                              <span className="px-2 py-1 bg-red-50 text-red-700 rounded-full text-xs">Expired</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState icon={FileText} message="No licenses found for this company" />
              )}
            </div>
          )}

          {/* AMC Tab */}
          {activeTab === 'amc' && (
            <div>
              {amc_contracts.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full table-modern">
                    <thead>
                      <tr>
                        <th>Contract Name</th>
                        <th>Type</th>
                        <th>Period</th>
                        <th>Devices Covered</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {amc_contracts.map((amc) => (
                        <tr key={amc.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 bg-blue-50 rounded-lg flex items-center justify-center">
                                <Shield className="h-4 w-4 text-blue-600" />
                              </div>
                              <span className="font-medium">{amc.name}</span>
                            </div>
                          </td>
                          <td className="text-sm capitalize">{amc.amc_type?.replace('_', ' ') || '-'}</td>
                          <td className="text-sm">{formatDate(amc.start_date)} - {formatDate(amc.end_date)}</td>
                          <td className="text-sm font-medium">{amc.devices_covered} devices</td>
                          <td>
                            {amc.is_active ? (
                              <span className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs">Active</span>
                            ) : (
                              <span className="px-2 py-1 bg-red-50 text-red-700 rounded-full text-xs">Expired</span>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState icon={Shield} message="No AMC contracts found for this company" />
              )}
            </div>
          )}

          {/* Services Tab */}
          {activeTab === 'services' && (
            <div>
              {services.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full table-modern">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Device</th>
                        <th>Service Type</th>
                        <th>Issue</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {services.map((svc) => (
                        <tr key={svc.id}>
                          <td className="text-sm">{formatDate(svc.service_date)}</td>
                          <td className="text-sm">{svc.device_info || '-'}</td>
                          <td className="text-sm capitalize">{svc.service_type?.replace('_', ' ') || '-'}</td>
                          <td className="text-sm text-slate-600 max-w-[200px] truncate">{svc.problem_reported || '-'}</td>
                          <td>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              svc.status === 'completed' ? 'bg-emerald-50 text-emerald-700' :
                              svc.status === 'in_progress' ? 'bg-amber-50 text-amber-700' :
                              'bg-slate-100 text-slate-600'
                            }`}>
                              {svc.status?.replace('_', ' ') || 'Pending'}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState icon={Wrench} message="No service records found for this company" />
              )}
            </div>
          )}
        </div>
      </div>

      {/* Edit Company Modal */}
      <Dialog open={isEditing} onOpenChange={setIsEditing}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Edit Company</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div>
              <label className="form-label">Company Name *</label>
              <input
                type="text"
                value={editForm.name || ''}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                className="form-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Contact Person</label>
                <input
                  type="text"
                  value={editForm.contact_person || ''}
                  onChange={(e) => setEditForm({ ...editForm, contact_person: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Email</label>
                <input
                  type="email"
                  value={editForm.email || ''}
                  onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                  className="form-input"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Phone</label>
                <input
                  type="text"
                  value={editForm.phone || ''}
                  onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">GST Number</label>
                <input
                  type="text"
                  value={editForm.gst_number || ''}
                  onChange={(e) => setEditForm({ ...editForm, gst_number: e.target.value })}
                  className="form-input"
                />
              </div>
            </div>
            <div>
              <label className="form-label">Address</label>
              <textarea
                value={editForm.address || ''}
                onChange={(e) => setEditForm({ ...editForm, address: e.target.value })}
                className="form-input"
                rows={2}
              />
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setIsEditing(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleSaveCompany}
                disabled={saving}
                className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
              >
                {saving ? 'Saving...' : 'Save Changes'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

// Empty State Component
const EmptyState = ({ icon: Icon, message }) => (
  <div className="text-center py-12">
    <Icon className="h-12 w-12 mx-auto text-slate-300 mb-3" />
    <p className="text-slate-500">{message}</p>
  </div>
);

export default CompanyDetails;
