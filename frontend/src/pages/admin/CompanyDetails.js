import { useState, useEffect, useMemo } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Building2, ArrowLeft, Edit2, Save, X, MapPin, Users, Laptop, Package, 
  FileText, Shield, Wrench, Mail, Phone, Calendar, CheckCircle2, XCircle,
  AlertCircle, Clock, ChevronRight, KeyRound, Plus, Eye, EyeOff, Trash2, Search, Globe
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const TABS = [
  { id: 'overview', label: 'Overview', icon: Building2 },
  { id: 'portal_users', label: 'Portal Logins', icon: KeyRound },
  { id: 'sites', label: 'Sites', icon: MapPin },
  { id: 'users', label: 'Users/Contacts', icon: Users },
  { id: 'email_domains', label: 'Email Domains', icon: Globe },
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
  
  // Device search and modal state
  const [deviceSearchQuery, setDeviceSearchQuery] = useState('');
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [showDeviceModal, setShowDeviceModal] = useState(false);
  const [editingDevice, setEditingDevice] = useState(false);
  const [deviceForm, setDeviceForm] = useState({});
  const [savingDevice, setSavingDevice] = useState(false);

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

  // Portal Users functions
  const fetchPortalUsers = async () => {
    try {
      setLoadingPortalUsers(true);
      const response = await axios.get(`${API}/admin/companies/${companyId}/portal-users`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPortalUsers(response.data);
    } catch (error) {
      console.error('Failed to load portal users:', error);
    } finally {
      setLoadingPortalUsers(false);
    }
  };

  const handleAddPortalUser = async (e) => {
    e.preventDefault();
    if (!newPortalUser.name || !newPortalUser.email || !newPortalUser.password) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      setSaving(true);
      await axios.post(`${API}/admin/companies/${companyId}/portal-users`, newPortalUser, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Portal user created successfully');
      setShowAddPortalUser(false);
      setNewPortalUser({ name: '', email: '', phone: '', password: '', role: 'company_viewer' });
      fetchPortalUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create portal user');
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePortalUser = async (userId, userName) => {
    if (!window.confirm(`Are you sure you want to delete portal user "${userName}"?`)) return;
    
    try {
      await axios.delete(`${API}/admin/companies/${companyId}/portal-users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Portal user deleted');
      fetchPortalUsers();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete portal user');
    }
  };

  const handleResetPassword = async (userId, userName) => {
    const newPassword = window.prompt(`Enter new password for "${userName}":`);
    if (!newPassword) return;
    
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    try {
      await axios.put(`${API}/admin/companies/${companyId}/portal-users/${userId}/reset-password`, 
        { password: newPassword },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Password reset successfully');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reset password');
    }
  };

  // Load portal users when tab changes
  useEffect(() => {
    if (activeTab === 'portal_users' && portalUsers.length === 0) {
      fetchPortalUsers();
    }
  }, [activeTab]);

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

          {/* Portal Users Tab */}
          {activeTab === 'portal_users' && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <h3 className="font-medium text-slate-900">Company Portal Logins</h3>
                  <p className="text-sm text-slate-500 mt-1">
                    Manage users who can login to the company portal. 
                    Company Code: <span className="font-mono font-medium text-blue-600">{company.code || 'Not Set'}</span>
                  </p>
                </div>
                <Button 
                  onClick={() => setShowAddPortalUser(true)}
                  className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Portal User
                </Button>
              </div>
              
              {loadingPortalUsers ? (
                <div className="flex items-center justify-center py-8">
                  <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                </div>
              ) : portalUsers.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full table-modern">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Email</th>
                        <th>Phone</th>
                        <th>Role</th>
                        <th>Last Login</th>
                        <th>Status</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {portalUsers.map((user) => (
                        <tr key={user.id}>
                          <td>
                            <div className="flex items-center gap-3">
                              <div className="w-9 h-9 bg-emerald-50 rounded-full flex items-center justify-center">
                                <span className="text-sm font-medium text-emerald-600">
                                  {user.name?.charAt(0)?.toUpperCase() || 'U'}
                                </span>
                              </div>
                              <span className="font-medium">{user.name}</span>
                            </div>
                          </td>
                          <td className="text-sm">{user.email}</td>
                          <td className="text-sm">{user.phone || '-'}</td>
                          <td>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              user.role === 'company_admin' 
                                ? 'bg-purple-50 text-purple-700' 
                                : 'bg-slate-100 text-slate-600'
                            }`}>
                              {user.role === 'company_admin' ? 'Admin' : 'Viewer'}
                            </span>
                          </td>
                          <td className="text-sm text-slate-500">
                            {user.last_login ? formatDate(user.last_login) : 'Never'}
                          </td>
                          <td>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              user.is_active ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                            }`}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </span>
                          </td>
                          <td>
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => handleResetPassword(user.id, user.name)}
                                className="text-blue-600 hover:text-blue-800 text-sm"
                                title="Reset Password"
                              >
                                <KeyRound className="h-4 w-4" />
                              </button>
                              <button
                                onClick={() => handleDeletePortalUser(user.id, user.name)}
                                className="text-red-600 hover:text-red-800 text-sm"
                                title="Delete User"
                              >
                                <Trash2 className="h-4 w-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 bg-slate-50 rounded-lg">
                  <KeyRound className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                  <p className="text-slate-500 mb-4">No portal users found for this company</p>
                  <p className="text-sm text-slate-400 mb-4">
                    Users can self-register using company code: <span className="font-mono font-medium">{company.code || 'Not Set'}</span>
                  </p>
                  <Button 
                    onClick={() => setShowAddPortalUser(true)}
                    variant="outline"
                  >
                    <Plus className="h-4 w-4 mr-2" />
                    Add First Portal User
                  </Button>
                </div>
              )}
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
              {/* Device Search Bar */}
              <div className="mb-4">
                <div className="relative max-w-md">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <Input
                    placeholder="Search devices (e.g., CCTV, security camera, laptop, notebook...)"
                    value={deviceSearchQuery}
                    onChange={(e) => setDeviceSearchQuery(e.target.value)}
                    className="pl-10"
                  />
                </div>
              </div>
              
              {(() => {
                // Device category synonyms for smart local filtering
                const SYNONYMS = {
                  'cctv': ['cctv', 'video surveillance', 'ip camera', 'security camera', 'surveillance', 'camera system'],
                  'nvr': ['nvr', 'network video recorder', 'video recorder', 'dvr'],
                  'laptop': ['laptop', 'notebook', 'portable computer', 'ultrabook', 'macbook'],
                  'desktop': ['desktop', 'pc', 'personal computer', 'workstation', 'computer'],
                  'printer': ['printer', 'laser printer', 'inkjet', 'multifunction', 'mfp', 'copier'],
                  'router': ['router', 'wifi router', 'wireless router', 'gateway', 'access point'],
                  'switch': ['switch', 'network switch', 'ethernet switch', 'hub'],
                  'ups': ['ups', 'uninterruptible power', 'battery backup', 'power backup'],
                  'server': ['server', 'rack server', 'file server', 'nas'],
                };
                
                // Get all matching device types for a search term
                const getMatchingTypes = (searchTerm) => {
                  const term = searchTerm.toLowerCase();
                  const matchingTypes = [];
                  for (const [type, synonyms] of Object.entries(SYNONYMS)) {
                    if (synonyms.some(syn => syn.includes(term) || term.includes(syn))) {
                      matchingTypes.push(type);
                    }
                  }
                  return matchingTypes;
                };
                
                // Filter devices based on search query with synonym support
                const filteredDevices = devices.filter(device => {
                  if (!deviceSearchQuery.trim()) return true;
                  const query = deviceSearchQuery.toLowerCase();
                  
                  // Direct field matches
                  if (
                    device.serial_number?.toLowerCase().includes(query) ||
                    device.brand?.toLowerCase().includes(query) ||
                    device.model?.toLowerCase().includes(query) ||
                    device.asset_tag?.toLowerCase().includes(query) ||
                    device.device_type?.toLowerCase().includes(query)
                  ) {
                    return true;
                  }
                  
                  // Synonym-based matching
                  const matchingTypes = getMatchingTypes(query);
                  if (matchingTypes.length > 0) {
                    const deviceTypeLower = device.device_type?.toLowerCase() || '';
                    return matchingTypes.some(type => 
                      deviceTypeLower.includes(type) || 
                      SYNONYMS[type]?.some(syn => deviceTypeLower.includes(syn))
                    );
                  }
                  
                  return false;
                });
                
                return filteredDevices.length > 0 ? (
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
                      {filteredDevices.map((device) => (
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
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => {
                                setSelectedDevice(device);
                                setDeviceForm({
                                  device_type: device.device_type || '',
                                  brand: device.brand || '',
                                  model: device.model || '',
                                  serial_number: device.serial_number || '',
                                  asset_tag: device.asset_tag || '',
                                  purchase_date: device.purchase_date || '',
                                  warranty_end_date: device.warranty_end_date || '',
                                  location: device.location || '',
                                  condition: device.condition || 'good',
                                  status: device.status || 'active',
                                  notes: device.notes || ''
                                });
                                setEditingDevice(false);
                                setShowDeviceModal(true);
                              }}
                              className="text-[#0F62FE] hover:text-[#0F62FE]"
                            >
                              <Eye className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <EmptyState icon={Laptop} message={deviceSearchQuery ? "No devices match your search" : "No devices found for this company"} />
              );
              })()}
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

      {/* Add Portal User Modal */}
      <Dialog open={showAddPortalUser} onOpenChange={setShowAddPortalUser}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Add Portal User</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleAddPortalUser} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Full Name *</label>
              <input
                type="text"
                value={newPortalUser.name}
                onChange={(e) => setNewPortalUser({ ...newPortalUser, name: e.target.value })}
                className="form-input"
                placeholder="Enter full name"
                required
              />
            </div>
            <div>
              <label className="form-label">Email *</label>
              <input
                type="email"
                value={newPortalUser.email}
                onChange={(e) => setNewPortalUser({ ...newPortalUser, email: e.target.value })}
                className="form-input"
                placeholder="Enter email address"
                required
              />
            </div>
            <div>
              <label className="form-label">Phone</label>
              <input
                type="tel"
                value={newPortalUser.phone}
                onChange={(e) => setNewPortalUser({ ...newPortalUser, phone: e.target.value })}
                className="form-input"
                placeholder="Enter phone number"
              />
            </div>
            <div>
              <label className="form-label">Password *</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={newPortalUser.password}
                  onChange={(e) => setNewPortalUser({ ...newPortalUser, password: e.target.value })}
                  className="form-input pr-10"
                  placeholder="Enter password (min 6 characters)"
                  required
                  minLength={6}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>
            <div>
              <label className="form-label">Role</label>
              <select
                value={newPortalUser.role}
                onChange={(e) => setNewPortalUser({ ...newPortalUser, role: e.target.value })}
                className="form-input"
              >
                <option value="company_viewer">Viewer (Read Only)</option>
                <option value="company_admin">Admin (Full Access)</option>
              </select>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setShowAddPortalUser(false)}>
                Cancel
              </Button>
              <Button 
                type="submit"
                disabled={saving}
                className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
              >
                {saving ? 'Creating...' : 'Create User'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
      
      {/* Device Details Modal */}
      <Dialog open={showDeviceModal} onOpenChange={setShowDeviceModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center justify-between">
              <span>{selectedDevice?.brand} {selectedDevice?.model}</span>
              {!editingDevice && (
                <Button 
                  variant="outline" 
                  size="sm"
                  onClick={() => setEditingDevice(true)}
                >
                  <Edit2 className="h-4 w-4 mr-1" />
                  Edit
                </Button>
              )}
            </DialogTitle>
          </DialogHeader>
          
          {selectedDevice && (
            <div className="space-y-4">
              {editingDevice ? (
                // Edit Form
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700">Device Type</label>
                    <Input
                      value={deviceForm.device_type}
                      onChange={(e) => setDeviceForm({...deviceForm, device_type: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Brand</label>
                    <Input
                      value={deviceForm.brand}
                      onChange={(e) => setDeviceForm({...deviceForm, brand: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Model</label>
                    <Input
                      value={deviceForm.model}
                      onChange={(e) => setDeviceForm({...deviceForm, model: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Serial Number</label>
                    <Input
                      value={deviceForm.serial_number}
                      onChange={(e) => setDeviceForm({...deviceForm, serial_number: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Asset Tag</label>
                    <Input
                      value={deviceForm.asset_tag}
                      onChange={(e) => setDeviceForm({...deviceForm, asset_tag: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Purchase Date</label>
                    <Input
                      type="date"
                      value={deviceForm.purchase_date}
                      onChange={(e) => setDeviceForm({...deviceForm, purchase_date: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Warranty End Date</label>
                    <Input
                      type="date"
                      value={deviceForm.warranty_end_date}
                      onChange={(e) => setDeviceForm({...deviceForm, warranty_end_date: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Location</label>
                    <Input
                      value={deviceForm.location}
                      onChange={(e) => setDeviceForm({...deviceForm, location: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Condition</label>
                    <select
                      value={deviceForm.condition}
                      onChange={(e) => setDeviceForm({...deviceForm, condition: e.target.value})}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                    >
                      <option value="new">New</option>
                      <option value="good">Good</option>
                      <option value="fair">Fair</option>
                      <option value="poor">Poor</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700">Status</label>
                    <select
                      value={deviceForm.status}
                      onChange={(e) => setDeviceForm({...deviceForm, status: e.target.value})}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                    >
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                      <option value="maintenance">Maintenance</option>
                      <option value="retired">Retired</option>
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="text-sm font-medium text-gray-700">Notes</label>
                    <textarea
                      value={deviceForm.notes}
                      onChange={(e) => setDeviceForm({...deviceForm, notes: e.target.value})}
                      rows={3}
                      className="w-full px-3 py-2 border rounded-md text-sm"
                    />
                  </div>
                </div>
              ) : (
                // View Mode
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Device Type</p>
                    <p className="font-medium">{selectedDevice.device_type}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Brand</p>
                    <p className="font-medium">{selectedDevice.brand}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Model</p>
                    <p className="font-medium">{selectedDevice.model}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Serial Number</p>
                    <p className="font-medium font-mono">{selectedDevice.serial_number}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Asset Tag</p>
                    <p className="font-medium">{selectedDevice.asset_tag || '-'}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Purchase Date</p>
                    <p className="font-medium">{selectedDevice.purchase_date || '-'}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Warranty End</p>
                    <p className="font-medium">{selectedDevice.warranty_end_date || '-'}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Location</p>
                    <p className="font-medium">{selectedDevice.location || '-'}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Condition</p>
                    <p className="font-medium capitalize">{selectedDevice.condition}</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg">
                    <p className="text-xs text-gray-500">Status</p>
                    <p className="font-medium capitalize">{selectedDevice.status}</p>
                  </div>
                  {selectedDevice.notes && (
                    <div className="col-span-2 bg-gray-50 p-3 rounded-lg">
                      <p className="text-xs text-gray-500">Notes</p>
                      <p className="text-sm">{selectedDevice.notes}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
          
          <DialogFooter>
            {editingDevice ? (
              <>
                <Button 
                  variant="outline" 
                  onClick={() => setEditingDevice(false)}
                >
                  Cancel
                </Button>
                <Button 
                  onClick={async () => {
                    setSavingDevice(true);
                    try {
                      await axios.put(
                        `${API}/admin/devices/${selectedDevice.id}`,
                        deviceForm,
                        { headers: { Authorization: `Bearer ${token}` } }
                      );
                      toast.success('Device updated successfully');
                      setEditingDevice(false);
                      setShowDeviceModal(false);
                      // Refresh company data
                      fetchCompanyOverview();
                    } catch (error) {
                      toast.error('Failed to update device');
                    } finally {
                      setSavingDevice(false);
                    }
                  }}
                  disabled={savingDevice}
                  className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
                >
                  {savingDevice ? 'Saving...' : 'Save Changes'}
                </Button>
              </>
            ) : (
              <Button variant="outline" onClick={() => setShowDeviceModal(false)}>
                Close
              </Button>
            )}
          </DialogFooter>
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
