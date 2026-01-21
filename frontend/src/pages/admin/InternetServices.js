import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, MoreVertical, Building2, Globe, Wifi, 
  Calendar, Phone, Mail, User, Network, CheckCircle, XCircle, Eye,
  Signal, Router, Key, DollarSign
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import { SmartSelect } from '../../components/ui/smart-select';
import { QuickCreateCompany } from '../../components/forms';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const connectionTypes = [
  { value: 'broadband', label: 'Broadband' },
  { value: 'fiber', label: 'Fiber' },
  { value: 'leased_line', label: 'Leased Line' },
  { value: '4g', label: '4G/LTE' },
  { value: '5g', label: '5G' },
  { value: 'dsl', label: 'DSL' },
  { value: 'cable', label: 'Cable' },
];

const ipTypes = [
  { value: 'dynamic', label: 'Dynamic IP' },
  { value: 'static', label: 'Static IP' },
];

const billingCycles = [
  { value: 'monthly', label: 'Monthly' },
  { value: 'quarterly', label: 'Quarterly' },
  { value: 'half_yearly', label: 'Half Yearly' },
  { value: 'yearly', label: 'Yearly' },
];

const InternetServices = () => {
  const { token } = useAuth();
  const [services, setServices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [sites, setSites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [editingService, setEditingService] = useState(null);

  const initialFormState = {
    company_id: '',
    site_id: '',
    provider_name: '',
    connection_type: 'broadband',
    account_number: '',
    customer_id: '',
    plan_name: '',
    speed_download: '',
    speed_upload: '',
    data_limit: '',
    monthly_cost: '',
    contract_start_date: '',
    contract_end_date: '',
    billing_cycle: 'monthly',
    ip_type: 'dynamic',
    static_ip: '',
    gateway: '',
    dns_primary: '',
    dns_secondary: '',
    router_ip: '',
    router_username: '',
    router_password: '',
    wifi_ssid: '',
    wifi_password: '',
    pppoe_username: '',
    pppoe_password: '',
    support_phone: '',
    support_email: '',
    account_manager: '',
    account_manager_phone: '',
    status: 'active',
    notes: ''
  };

  const [formData, setFormData] = useState(initialFormState);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [servicesRes, companiesRes, sitesRes] = await Promise.all([
        axios.get(`${API}/admin/internet-services`, {
          params: { company_id: filterCompany || undefined, status: filterStatus || undefined },
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/companies`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/sites`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      setServices(servicesRes.data);
      setCompanies(companiesRes.data);
      setSites(sitesRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token, filterCompany, filterStatus]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const filteredServices = services.filter(service => {
    const matchesSearch = !searchQuery || 
      service.provider_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      service.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      service.account_number?.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesSearch;
  });

  const openCreateModal = () => {
    setEditingService(null);
    setFormData({ ...initialFormState, company_id: filterCompany || '' });
    setModalOpen(true);
  };

  const openEditModal = (service) => {
    setEditingService(service);
    setFormData({
      company_id: service.company_id || '',
      site_id: service.site_id || '',
      provider_name: service.provider_name || '',
      connection_type: service.connection_type || 'broadband',
      account_number: service.account_number || '',
      customer_id: service.customer_id || '',
      plan_name: service.plan_name || '',
      speed_download: service.speed_download || '',
      speed_upload: service.speed_upload || '',
      data_limit: service.data_limit || '',
      monthly_cost: service.monthly_cost || '',
      contract_start_date: service.contract_start_date || '',
      contract_end_date: service.contract_end_date || '',
      billing_cycle: service.billing_cycle || 'monthly',
      ip_type: service.ip_type || 'dynamic',
      static_ip: service.static_ip || '',
      gateway: service.gateway || '',
      dns_primary: service.dns_primary || '',
      dns_secondary: service.dns_secondary || '',
      router_ip: service.router_ip || '',
      router_username: service.router_username || '',
      router_password: service.router_password || '',
      wifi_ssid: service.wifi_ssid || '',
      wifi_password: service.wifi_password || '',
      pppoe_username: service.pppoe_username || '',
      pppoe_password: service.pppoe_password || '',
      support_phone: service.support_phone || '',
      support_email: service.support_email || '',
      account_manager: service.account_manager || '',
      account_manager_phone: service.account_manager_phone || '',
      status: service.status || 'active',
      notes: service.notes || ''
    });
    setModalOpen(true);
  };

  const openDetailModal = async (service) => {
    try {
      const res = await axios.get(`${API}/admin/internet-services/${service.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedService(res.data);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error('Failed to load service details');
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.provider_name) {
      toast.error('Please fill required fields');
      return;
    }

    try {
      const payload = {
        ...formData,
        monthly_cost: formData.monthly_cost ? parseFloat(formData.monthly_cost) : null
      };

      if (editingService) {
        await axios.put(`${API}/admin/internet-services/${editingService.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Internet service updated');
      } else {
        await axios.post(`${API}/admin/internet-services`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Internet service created');
      }
      setModalOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save');
    }
  };

  const handleDelete = async (service) => {
    if (!window.confirm(`Delete internet service for "${service.provider_name}"?`)) return;
    try {
      await axios.delete(`${API}/admin/internet-services/${service.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Internet service deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const stats = {
    total: services.length,
    active: services.filter(s => s.status === 'active').length,
    withStaticIP: services.filter(s => s.ip_type === 'static').length
  };

  const companySites = sites.filter(s => s.company_id === formData.company_id);

  return (
    <div className="space-y-6" data-testid="internet-services-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900 flex items-center gap-2">
            <Globe className="h-6 w-6 text-emerald-600" />
            Internet Services
          </h1>
          <p className="text-slate-500">Manage ISP connections, plans, and credentials</p>
        </div>
        <Button onClick={openCreateModal} className="bg-emerald-600 hover:bg-emerald-700 text-white" data-testid="add-service-btn">
          <Plus className="h-4 w-4 mr-2" />
          Add Internet Service
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Globe className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              <p className="text-xs text-slate-500">Total Connections</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-green-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.active}</p>
              <p className="text-xs text-slate-500">Active</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Network className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.withStaticIP}</p>
              <p className="text-xs text-slate-500">With Static IP</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl border border-slate-100 p-4">
        <div className="flex flex-wrap gap-4">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search by provider, company, account..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input pl-10"
            />
          </div>
          <select value={filterCompany} onChange={(e) => setFilterCompany(e.target.value)} className="form-select w-48">
            <option value="">All Companies</option>
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="form-select w-36">
            <option value="">All Status</option>
            <option value="active">Active</option>
            <option value="suspended">Suspended</option>
            <option value="terminated">Terminated</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        <table className="w-full">
          <thead className="bg-slate-50 border-b border-slate-100">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Provider</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Company / Site</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Plan</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">IP Type</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Contract End</th>
              <th className="px-6 py-3 text-left text-xs font-semibold text-slate-600 uppercase">Status</th>
              <th className="px-6 py-3 text-right text-xs font-semibold text-slate-600 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {loading ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center">
                  <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
                </td>
              </tr>
            ) : filteredServices.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-6 py-12 text-center text-slate-500">
                  <Globe className="h-12 w-12 mx-auto text-slate-300 mb-3" />
                  <p>No internet services found</p>
                </td>
              </tr>
            ) : (
              filteredServices.map(service => (
                <tr key={service.id} className="hover:bg-slate-50">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
                        <Globe className="h-5 w-5 text-emerald-600" />
                      </div>
                      <div>
                        <p className="font-medium text-slate-900">{service.provider_name}</p>
                        <p className="text-sm text-slate-500">{service.connection_type}</p>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <p className="font-medium text-slate-900">{service.company_name}</p>
                    {service.site_name && <p className="text-sm text-slate-500">{service.site_name}</p>}
                  </td>
                  <td className="px-6 py-4">
                    {service.plan_name && <p className="text-slate-900">{service.plan_name}</p>}
                    {service.speed_download && (
                      <p className="text-sm text-slate-500 flex items-center gap-1">
                        <Signal className="h-3 w-3" />
                        {service.speed_download}
                      </p>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                      service.ip_type === 'static' ? 'bg-blue-100 text-blue-700' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {service.ip_type === 'static' ? 'Static' : 'Dynamic'}
                    </span>
                    {service.static_ip && (
                      <p className="text-xs text-slate-500 mt-1">{service.static_ip}</p>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    {service.contract_end_date ? (
                      <span className="text-slate-600">{new Date(service.contract_end_date).toLocaleDateString()}</span>
                    ) : (
                      <span className="text-slate-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      service.status === 'active' ? 'bg-green-100 text-green-700' :
                      service.status === 'suspended' ? 'bg-amber-100 text-amber-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {service.status === 'active' ? <CheckCircle className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                      {service.status}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-right">
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="sm">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => openDetailModal(service)}>
                          <Eye className="h-4 w-4 mr-2" />
                          View Details
                        </DropdownMenuItem>
                        <DropdownMenuItem onClick={() => openEditModal(service)}>
                          <Edit2 className="h-4 w-4 mr-2" />
                          Edit
                        </DropdownMenuItem>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem className="text-red-600" onClick={() => handleDelete(service)}>
                          <Trash2 className="h-4 w-4 mr-2" />
                          Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingService ? 'Edit Internet Service' : 'Add Internet Service'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-6 mt-4">
            {/* Basic Info */}
            <div className="space-y-4">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <Building2 className="h-4 w-4" />
                Basic Information
              </h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Company *</label>
                  <SmartSelect
                    value={formData.company_id}
                    onValueChange={(val) => setFormData({ ...formData, company_id: val, site_id: '' })}
                    options={companies.map(c => ({ id: c.id, label: c.name }))}
                    placeholder="Select company"
                    quickCreate={<QuickCreateCompany onCreated={(c) => { setCompanies([...companies, c]); setFormData({ ...formData, company_id: c.id }); }} />}
                  />
                </div>
                <div>
                  <label className="form-label">Site (Optional)</label>
                  <select value={formData.site_id} onChange={(e) => setFormData({ ...formData, site_id: e.target.value })} className="form-select">
                    <option value="">Select site...</option>
                    {companySites.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                  </select>
                </div>
                <div>
                  <label className="form-label">Status</label>
                  <select value={formData.status} onChange={(e) => setFormData({ ...formData, status: e.target.value })} className="form-select">
                    <option value="active">Active</option>
                    <option value="suspended">Suspended</option>
                    <option value="terminated">Terminated</option>
                  </select>
                </div>
              </div>
            </div>

            {/* Provider Details */}
            <div className="space-y-4">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <Globe className="h-4 w-4" />
                Provider Details
              </h4>
              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="form-label">Provider Name *</label>
                  <input type="text" value={formData.provider_name} onChange={(e) => setFormData({ ...formData, provider_name: e.target.value })} className="form-input" placeholder="e.g., Airtel, Jio, ACT" required />
                </div>
                <div>
                  <label className="form-label">Connection Type</label>
                  <select value={formData.connection_type} onChange={(e) => setFormData({ ...formData, connection_type: e.target.value })} className="form-select">
                    {connectionTypes.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="form-label">Account Number</label>
                  <input type="text" value={formData.account_number} onChange={(e) => setFormData({ ...formData, account_number: e.target.value })} className="form-input" placeholder="ISP Account #" />
                </div>
                <div>
                  <label className="form-label">Customer ID</label>
                  <input type="text" value={formData.customer_id} onChange={(e) => setFormData({ ...formData, customer_id: e.target.value })} className="form-input" placeholder="Customer ID" />
                </div>
              </div>
            </div>

            {/* Plan Details */}
            <div className="space-y-4">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <Signal className="h-4 w-4" />
                Plan Details
              </h4>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <label className="form-label">Plan Name</label>
                  <input type="text" value={formData.plan_name} onChange={(e) => setFormData({ ...formData, plan_name: e.target.value })} className="form-input" placeholder="e.g., Business 100" />
                </div>
                <div>
                  <label className="form-label">Download Speed</label>
                  <input type="text" value={formData.speed_download} onChange={(e) => setFormData({ ...formData, speed_download: e.target.value })} className="form-input" placeholder="e.g., 100 Mbps" />
                </div>
                <div>
                  <label className="form-label">Upload Speed</label>
                  <input type="text" value={formData.speed_upload} onChange={(e) => setFormData({ ...formData, speed_upload: e.target.value })} className="form-input" placeholder="e.g., 100 Mbps" />
                </div>
                <div>
                  <label className="form-label">Data Limit</label>
                  <input type="text" value={formData.data_limit} onChange={(e) => setFormData({ ...formData, data_limit: e.target.value })} className="form-input" placeholder="e.g., Unlimited" />
                </div>
                <div>
                  <label className="form-label">Monthly Cost (₹)</label>
                  <input type="number" value={formData.monthly_cost} onChange={(e) => setFormData({ ...formData, monthly_cost: e.target.value })} className="form-input" placeholder="0" />
                </div>
                <div>
                  <label className="form-label">Billing Cycle</label>
                  <select value={formData.billing_cycle} onChange={(e) => setFormData({ ...formData, billing_cycle: e.target.value })} className="form-select">
                    {billingCycles.map(b => <option key={b.value} value={b.value}>{b.label}</option>)}
                  </select>
                </div>
                <div>
                  <label className="form-label">Contract Start</label>
                  <input type="date" value={formData.contract_start_date} onChange={(e) => setFormData({ ...formData, contract_start_date: e.target.value })} className="form-input" />
                </div>
                <div>
                  <label className="form-label">Contract End</label>
                  <input type="date" value={formData.contract_end_date} onChange={(e) => setFormData({ ...formData, contract_end_date: e.target.value })} className="form-input" />
                </div>
              </div>
            </div>

            {/* IP Configuration */}
            <div className="space-y-4">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <Network className="h-4 w-4" />
                IP Configuration
              </h4>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <label className="form-label">IP Type</label>
                  <select value={formData.ip_type} onChange={(e) => setFormData({ ...formData, ip_type: e.target.value })} className="form-select">
                    {ipTypes.map(t => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>
                </div>
                {formData.ip_type === 'static' && (
                  <>
                    <div>
                      <label className="form-label">Static IP</label>
                      <input type="text" value={formData.static_ip} onChange={(e) => setFormData({ ...formData, static_ip: e.target.value })} className="form-input" placeholder="e.g., 203.0.113.1" />
                    </div>
                    <div>
                      <label className="form-label">Gateway</label>
                      <input type="text" value={formData.gateway} onChange={(e) => setFormData({ ...formData, gateway: e.target.value })} className="form-input" placeholder="e.g., 203.0.113.254" />
                    </div>
                  </>
                )}
                <div>
                  <label className="form-label">Primary DNS</label>
                  <input type="text" value={formData.dns_primary} onChange={(e) => setFormData({ ...formData, dns_primary: e.target.value })} className="form-input" placeholder="e.g., 8.8.8.8" />
                </div>
                <div>
                  <label className="form-label">Secondary DNS</label>
                  <input type="text" value={formData.dns_secondary} onChange={(e) => setFormData({ ...formData, dns_secondary: e.target.value })} className="form-input" placeholder="e.g., 8.8.4.4" />
                </div>
              </div>
            </div>

            {/* Router/Modem Credentials */}
            <div className="space-y-4">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <Router className="h-4 w-4" />
                Router/Modem Credentials
              </h4>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <label className="form-label">Router IP</label>
                  <input type="text" value={formData.router_ip} onChange={(e) => setFormData({ ...formData, router_ip: e.target.value })} className="form-input" placeholder="e.g., 192.168.1.1" />
                </div>
                <div>
                  <label className="form-label">Router Username</label>
                  <input type="text" value={formData.router_username} onChange={(e) => setFormData({ ...formData, router_username: e.target.value })} className="form-input" placeholder="admin" />
                </div>
                <div>
                  <label className="form-label">Router Password</label>
                  <input type="text" value={formData.router_password} onChange={(e) => setFormData({ ...formData, router_password: e.target.value })} className="form-input" placeholder="Password" />
                </div>
              </div>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <label className="form-label">WiFi SSID</label>
                  <input type="text" value={formData.wifi_ssid} onChange={(e) => setFormData({ ...formData, wifi_ssid: e.target.value })} className="form-input" placeholder="Network Name" />
                </div>
                <div>
                  <label className="form-label">WiFi Password</label>
                  <input type="text" value={formData.wifi_password} onChange={(e) => setFormData({ ...formData, wifi_password: e.target.value })} className="form-input" placeholder="WiFi Password" />
                </div>
                <div>
                  <label className="form-label">PPPoE Username</label>
                  <input type="text" value={formData.pppoe_username} onChange={(e) => setFormData({ ...formData, pppoe_username: e.target.value })} className="form-input" placeholder="PPPoE User" />
                </div>
                <div>
                  <label className="form-label">PPPoE Password</label>
                  <input type="text" value={formData.pppoe_password} onChange={(e) => setFormData({ ...formData, pppoe_password: e.target.value })} className="form-input" placeholder="PPPoE Pass" />
                </div>
              </div>
            </div>

            {/* Support Contact */}
            <div className="space-y-4">
              <h4 className="font-semibold text-slate-900 flex items-center gap-2">
                <Phone className="h-4 w-4" />
                Support Contact
              </h4>
              <div className="grid grid-cols-4 gap-4">
                <div>
                  <label className="form-label">Support Phone</label>
                  <input type="text" value={formData.support_phone} onChange={(e) => setFormData({ ...formData, support_phone: e.target.value })} className="form-input" placeholder="Support number" />
                </div>
                <div>
                  <label className="form-label">Support Email</label>
                  <input type="email" value={formData.support_email} onChange={(e) => setFormData({ ...formData, support_email: e.target.value })} className="form-input" placeholder="support@isp.com" />
                </div>
                <div>
                  <label className="form-label">Account Manager</label>
                  <input type="text" value={formData.account_manager} onChange={(e) => setFormData({ ...formData, account_manager: e.target.value })} className="form-input" placeholder="Name" />
                </div>
                <div>
                  <label className="form-label">Manager Phone</label>
                  <input type="text" value={formData.account_manager_phone} onChange={(e) => setFormData({ ...formData, account_manager_phone: e.target.value })} className="form-input" placeholder="Phone" />
                </div>
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="form-label">Notes</label>
              <textarea value={formData.notes} onChange={(e) => setFormData({ ...formData, notes: e.target.value })} className="form-input" rows={2} placeholder="Additional notes..." />
            </div>

            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700 text-white">
                {editingService ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Internet Service Details</DialogTitle>
          </DialogHeader>
          {selectedService && (
            <div className="space-y-6 mt-4">
              <div className="flex items-start gap-4 p-4 bg-slate-50 rounded-lg">
                <div className="w-14 h-14 rounded-xl bg-emerald-100 flex items-center justify-center">
                  <Globe className="h-7 w-7 text-emerald-600" />
                </div>
                <div>
                  <h3 className="text-lg font-bold">{selectedService.provider_name}</h3>
                  <p className="text-slate-500">{selectedService.company_name}</p>
                  {selectedService.site_name && <p className="text-sm text-slate-400">{selectedService.site_name}</p>}
                </div>
              </div>

              {/* Plan Info */}
              {selectedService.plan_name && (
                <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 rounded-lg">
                  <div>
                    <p className="text-xs text-blue-600 uppercase font-semibold">Plan</p>
                    <p className="font-medium">{selectedService.plan_name}</p>
                  </div>
                  {selectedService.speed_download && (
                    <div>
                      <p className="text-xs text-blue-600 uppercase font-semibold">Speed</p>
                      <p className="font-medium">{selectedService.speed_download} / {selectedService.speed_upload || 'N/A'}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Credentials */}
              {(selectedService.router_ip || selectedService.wifi_ssid) && (
                <div>
                  <h4 className="font-semibold mb-2 flex items-center gap-2"><Key className="h-4 w-4" /> Credentials</h4>
                  <div className="space-y-2">
                    {selectedService.router_ip && (
                      <div className="flex justify-between p-2 bg-slate-50 rounded">
                        <span className="text-slate-600">Router IP</span>
                        <code className="bg-slate-200 px-2 rounded">{selectedService.router_ip}</code>
                      </div>
                    )}
                    {selectedService.wifi_ssid && (
                      <div className="flex justify-between p-2 bg-slate-50 rounded">
                        <span className="text-slate-600">WiFi SSID</span>
                        <code className="bg-slate-200 px-2 rounded">{selectedService.wifi_ssid}</code>
                      </div>
                    )}
                    {selectedService.static_ip && (
                      <div className="flex justify-between p-2 bg-slate-50 rounded">
                        <span className="text-slate-600">Static IP</span>
                        <code className="bg-slate-200 px-2 rounded">{selectedService.static_ip}</code>
                      </div>
                    )}
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-2 pt-4">
                <Button variant="outline" onClick={() => { setDetailModalOpen(false); openEditModal(selectedService); }}>
                  <Edit2 className="h-4 w-4 mr-2" /> Edit
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default InternetServices;
