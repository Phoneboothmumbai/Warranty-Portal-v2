import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Plus, Search, Edit2, Trash2, Mail, MoreVertical, Building2, Calendar, Users, AlertTriangle, CheckCircle, Clock, Globe, DollarSign, Ticket } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';
import { SmartSelect } from '../../components/ui/smart-select';
import { QuickCreateCompany } from '../../components/forms';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusColors = {
  active: 'bg-emerald-100 text-emerald-700',
  expiring_soon: 'bg-amber-100 text-amber-700',
  expired: 'bg-red-100 text-red-700',
  cancelled: 'bg-slate-100 text-slate-600'
};

const statusIcons = {
  active: CheckCircle,
  expiring_soon: AlertTriangle,
  expired: Clock,
  cancelled: Clock
};

const Subscriptions = () => {
  const { token } = useAuth();
  const [subscriptions, setSubscriptions] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [filterProvider, setFilterProvider] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [ticketModalOpen, setTicketModalOpen] = useState(false);
  const [selectedSubscription, setSelectedSubscription] = useState(null);
  const [editingSubscription, setEditingSubscription] = useState(null);
  
  // Master data from API
  const [providers, setProviders] = useState([]);
  const [plans, setPlans] = useState([]);
  const [billingCycles, setBillingCycles] = useState([]);
  
  const [formData, setFormData] = useState({
    company_id: '',
    provider: '',
    domain: '',
    plan_type: '',
    plan_name: '',
    num_users: 1,
    price_per_user: '',
    billing_cycle: 'YEARLY',
    total_price: '',
    currency: 'INR',
    start_date: '',
    renewal_date: '',
    admin_email: '',
    secondary_admin: '',
    notes: ''
  });

  const [ticketData, setTicketData] = useState({
    subject: '',
    description: '',
    issue_type: 'other',
    priority: 'medium'
  });

  // Fetch master data on mount
  useEffect(() => {
    const fetchMasterData = async () => {
      try {
        const [provRes, planRes, cycleRes] = await Promise.all([
          axios.get(`${API}/admin/masters`, { params: { master_type: 'subscription_provider' }, headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${API}/admin/masters`, { params: { master_type: 'subscription_plan' }, headers: { Authorization: `Bearer ${token}` } }),
          axios.get(`${API}/admin/masters`, { params: { master_type: 'billing_cycle' }, headers: { Authorization: `Bearer ${token}` } })
        ]);
        setProviders(provRes.data);
        setPlans(planRes.data);
        setBillingCycles(cycleRes.data);
        
        // Set defaults if available
        if (provRes.data.length > 0) {
          setFormData(prev => ({ ...prev, provider: provRes.data[0].code }));
        }
        if (planRes.data.length > 0) {
          setFormData(prev => ({ ...prev, plan_type: planRes.data[0].code, plan_name: planRes.data[0].name }));
        }
      } catch (error) {
        console.error('Failed to load master data', error);
      }
    };
    fetchMasterData();
  }, [token]);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const params = { limit: 200 };
      if (filterCompany) params.company_id = filterCompany;
      if (filterProvider) params.provider = filterProvider;
      if (filterStatus) params.status = filterStatus;
      if (searchQuery) params.q = searchQuery;
      
      const [subRes, compRes] = await Promise.all([
        axios.get(`${API}/admin/subscriptions`, { params, headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/companies`, { params: { limit: 500 }, headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setSubscriptions(subRes.data);
      setCompanies(compRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token, filterCompany, filterProvider, filterStatus, searchQuery]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const openCreateModal = () => {
    setEditingSubscription(null);
    setFormData({
      company_id: filterCompany || '',
      provider: providers.length > 0 ? providers[0].code : '',
      domain: '',
      plan_type: plans.length > 0 ? plans[0].code : '',
      plan_name: plans.length > 0 ? plans[0].name : '',
      num_users: 1,
      price_per_user: '',
      billing_cycle: billingCycles.find(c => c.code === 'YEARLY')?.code || (billingCycles.length > 0 ? billingCycles[0].code : 'YEARLY'),
      total_price: '',
      currency: 'INR',
      start_date: new Date().toISOString().split('T')[0],
      renewal_date: '',
      admin_email: '',
      secondary_admin: '',
      notes: ''
    });
    setModalOpen(true);
  };

  const openEditModal = (subscription) => {
    setEditingSubscription(subscription);
    setFormData({
      company_id: subscription.company_id,
      provider: subscription.provider,
      domain: subscription.domain,
      plan_type: subscription.plan_type,
      plan_name: subscription.plan_name || '',
      num_users: subscription.num_users || 1,
      price_per_user: subscription.price_per_user || '',
      billing_cycle: subscription.billing_cycle || 'yearly',
      total_price: subscription.total_price || '',
      currency: subscription.currency || 'INR',
      start_date: subscription.start_date || '',
      renewal_date: subscription.renewal_date || '',
      admin_email: subscription.admin_email || '',
      secondary_admin: subscription.secondary_admin || '',
      notes: subscription.notes || ''
    });
    setModalOpen(true);
  };

  const openDetailModal = async (subscription) => {
    try {
      const res = await axios.get(`${API}/admin/subscriptions/${subscription.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedSubscription(res.data);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error('Failed to load details');
    }
  };

  const openTicketModal = (subscription) => {
    setSelectedSubscription(subscription);
    setTicketData({
      subject: '',
      description: '',
      issue_type: 'other',
      priority: 'medium'
    });
    setTicketModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingSubscription(null);
  };

  const handleProviderChange = (providerCode) => {
    const provider = providers.find(p => p.code === providerCode);
    setFormData({
      ...formData,
      provider: providerCode
    });
  };

  const handlePlanChange = (planCode) => {
    const plan = plans.find(p => p.code === planCode);
    setFormData({
      ...formData,
      plan_type: planCode,
      plan_name: plan?.name || planCode
    });
  };

  const getProviderName = (code) => {
    const p = providers.find(pr => pr.code === code);
    return p?.name || code;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.domain || !formData.start_date) {
      toast.error('Please fill in required fields');
      return;
    }

    const submitData = { ...formData };
    // Clean up optional fields
    ['notes', 'secondary_admin', 'renewal_date', 'admin_email'].forEach(field => {
      if (!submitData[field]) delete submitData[field];
    });
    if (submitData.price_per_user) {
      submitData.price_per_user = parseFloat(submitData.price_per_user);
    } else {
      delete submitData.price_per_user;
    }
    if (submitData.total_price) {
      submitData.total_price = parseFloat(submitData.total_price);
    } else {
      delete submitData.total_price;
    }
    submitData.num_users = parseInt(submitData.num_users) || 1;

    try {
      if (editingSubscription) {
        await axios.put(`${API}/admin/subscriptions/${editingSubscription.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Subscription updated');
      } else {
        await axios.post(`${API}/admin/subscriptions`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Subscription created');
      }
      fetchData();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (subscription) => {
    if (!window.confirm(`Delete subscription for "${subscription.domain}"?`)) return;
    
    try {
      await axios.delete(`${API}/admin/subscriptions/${subscription.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Subscription deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    if (!ticketData.subject || !ticketData.description) {
      toast.error('Subject and description are required');
      return;
    }

    try {
      const formDataObj = new FormData();
      formDataObj.append('subject', ticketData.subject);
      formDataObj.append('description', ticketData.description);
      formDataObj.append('issue_type', ticketData.issue_type);
      formDataObj.append('priority', ticketData.priority);

      await axios.post(`${API}/admin/subscriptions/${selectedSubscription.id}/tickets`, formDataObj, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Ticket created successfully');
      setTicketModalOpen(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create ticket');
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', { day: 'numeric', month: 'short', year: 'numeric' });
  };

  const formatCurrency = (amount, currency = 'INR') => {
    if (!amount) return '-';
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency }).format(amount);
  };

  const getProviderIcon = (provider) => {
    const p = PROVIDERS.find(pr => pr.id === provider);
    return p?.icon || '⚪';
  };

  // Stats
  const stats = {
    total: subscriptions.length,
    active: subscriptions.filter(s => s.status === 'active').length,
    expiring: subscriptions.filter(s => s.status === 'expiring_soon').length,
    totalUsers: subscriptions.reduce((sum, s) => sum + (s.num_users || 0), 0)
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Email & Cloud Subscriptions</h1>
          <p className="text-slate-500 mt-1">Manage Google Workspace, Titan, Microsoft 365 and other email services</p>
        </div>
        <Button 
          onClick={openCreateModal} 
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
          data-testid="add-subscription-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Subscription
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-4 mb-6">
        <div className="relative flex-1 min-w-[200px] max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by domain, admin email..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input pl-10"
            data-testid="subscription-search"
          />
        </div>
        <select
          value={filterCompany}
          onChange={(e) => setFilterCompany(e.target.value)}
          className="form-select w-48"
        >
          <option value="">All Companies</option>
          {companies.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <select
          value={filterProvider}
          onChange={(e) => setFilterProvider(e.target.value)}
          className="form-select w-48"
        >
          <option value="">All Providers</option>
          {PROVIDERS.map(p => (
            <option key={p.id} value={p.id}>{p.icon} {p.name}</option>
          ))}
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="form-select w-40"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="expiring_soon">Expiring Soon</option>
          <option value="expired">Expired</option>
        </select>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <Mail className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              <p className="text-sm text-slate-500">Subscriptions</p>
            </div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <CheckCircle className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.active}</p>
              <p className="text-sm text-slate-500">Active</p>
            </div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <AlertTriangle className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.expiring}</p>
              <p className="text-sm text-slate-500">Expiring Soon</p>
            </div>
          </div>
        </div>
        <div className="bg-white border border-slate-200 rounded-xl p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
              <Users className="h-5 w-5 text-purple-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.totalUsers}</p>
              <p className="text-sm text-slate-500">Total Users</p>
            </div>
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white border border-slate-200 rounded-xl overflow-hidden">
        {loading ? (
          <div className="text-center py-12">Loading...</div>
        ) : subscriptions.length > 0 ? (
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-200">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Provider / Domain</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Company</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Plan</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Users</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Renewal</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-500 uppercase">Status</th>
                <th className="w-10"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {subscriptions.map((sub) => {
                const StatusIcon = statusIcons[sub.status] || Clock;
                return (
                  <tr key={sub.id} className="hover:bg-slate-50" data-testid={`subscription-row-${sub.id}`}>
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{getProviderIcon(sub.provider)}</span>
                        <div>
                          <p className="font-medium text-slate-900">{sub.provider_name}</p>
                          <p className="text-sm text-blue-600 flex items-center gap-1">
                            <Globe className="h-3 w-3" />
                            {sub.domain}
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-600">{sub.company_name}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-900">{sub.plan_name || sub.plan_type}</span>
                      {sub.total_price && (
                        <p className="text-xs text-slate-500">{formatCurrency(sub.total_price)}/{sub.billing_cycle}</p>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-slate-900">{sub.num_users}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-600">{formatDate(sub.renewal_date)}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded-full capitalize flex items-center gap-1 w-fit ${statusColors[sub.status]}`}>
                        <StatusIcon className="h-3 w-3" />
                        {sub.status?.replace('_', ' ')}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button className="p-1.5 hover:bg-slate-100 rounded-lg">
                            <MoreVertical className="h-4 w-4 text-slate-400" />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openDetailModal(sub)}>
                            <Mail className="h-4 w-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openEditModal(sub)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openTicketModal(sub)}>
                            <Ticket className="h-4 w-4 mr-2" />
                            Create Ticket
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600" onClick={() => handleDelete(sub)}>
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        ) : (
          <div className="text-center py-16">
            <Mail className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No subscriptions found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add your first subscription
            </Button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingSubscription ? 'Edit Subscription' : 'Add Subscription'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Company *</label>
                <SmartSelect
                  value={formData.company_id}
                  onValueChange={(value) => setFormData({ ...formData, company_id: value })}
                  placeholder="Select Company"
                  searchPlaceholder="Search companies..."
                  emptyText="No companies found"
                  fetchOptions={async (q) => {
                    const res = await axios.get(`${API}/admin/companies`, {
                      params: { q, limit: 20 },
                      headers: { Authorization: `Bearer ${token}` }
                    });
                    return res.data;
                  }}
                  displayKey="name"
                  valueKey="id"
                  allowCreate
                  createLabel="Add New Company"
                  renderCreateForm={({ initialValue, onSuccess, onCancel }) => (
                    <QuickCreateCompany
                      initialValue={initialValue}
                      onSuccess={onSuccess}
                      onCancel={onCancel}
                      token={token}
                    />
                  )}
                />
              </div>
              <div>
                <label className="form-label">Domain *</label>
                <input
                  type="text"
                  value={formData.domain}
                  onChange={(e) => setFormData({ ...formData, domain: e.target.value })}
                  className="form-input"
                  placeholder="example.com"
                  data-testid="subscription-domain"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Provider *</label>
                <select
                  value={formData.provider}
                  onChange={(e) => handleProviderChange(e.target.value)}
                  className="form-select"
                >
                  {PROVIDERS.map(p => (
                    <option key={p.id} value={p.id}>{p.icon} {p.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="form-label">Plan *</label>
                <select
                  value={formData.plan_type}
                  onChange={(e) => handlePlanChange(e.target.value)}
                  className="form-select"
                >
                  {(PLANS[formData.provider] || PLANS.other).map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">No. of Users *</label>
                <input
                  type="number"
                  value={formData.num_users}
                  onChange={(e) => setFormData({ ...formData, num_users: e.target.value })}
                  className="form-input"
                  min="1"
                  data-testid="subscription-users"
                />
              </div>
              <div>
                <label className="form-label">Price per User</label>
                <input
                  type="number"
                  value={formData.price_per_user}
                  onChange={(e) => setFormData({ ...formData, price_per_user: e.target.value })}
                  className="form-input"
                  placeholder="0.00"
                  step="0.01"
                />
              </div>
              <div>
                <label className="form-label">Billing Cycle</label>
                <select
                  value={formData.billing_cycle}
                  onChange={(e) => setFormData({ ...formData, billing_cycle: e.target.value })}
                  className="form-select"
                >
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Start Date *</label>
                <input
                  type="date"
                  value={formData.start_date}
                  onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                  className="form-input"
                  data-testid="subscription-start-date"
                />
              </div>
              <div>
                <label className="form-label">Renewal Date</label>
                <input
                  type="date"
                  value={formData.renewal_date}
                  onChange={(e) => setFormData({ ...formData, renewal_date: e.target.value })}
                  className="form-input"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Admin Email</label>
                <input
                  type="email"
                  value={formData.admin_email}
                  onChange={(e) => setFormData({ ...formData, admin_email: e.target.value })}
                  className="form-input"
                  placeholder="admin@example.com"
                />
              </div>
              <div>
                <label className="form-label">Secondary Admin</label>
                <input
                  type="email"
                  value={formData.secondary_admin}
                  onChange={(e) => setFormData({ ...formData, secondary_admin: e.target.value })}
                  className="form-input"
                  placeholder="backup@example.com"
                />
              </div>
            </div>
            
            <div>
              <label className="form-label">Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="form-input"
                rows={2}
                placeholder="Additional notes..."
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="subscription-submit">
                {editingSubscription ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Subscription Details</DialogTitle>
          </DialogHeader>
          {selectedSubscription && (
            <div className="space-y-6 mt-4">
              <div className="flex items-center gap-4">
                <span className="text-4xl">{getProviderIcon(selectedSubscription.provider)}</span>
                <div>
                  <h3 className="text-xl font-semibold">{selectedSubscription.provider_name}</h3>
                  <p className="text-blue-600 flex items-center gap-1">
                    <Globe className="h-4 w-4" />
                    {selectedSubscription.domain}
                  </p>
                </div>
                <span className={`ml-auto text-sm px-3 py-1 rounded-full ${statusColors[selectedSubscription.status]}`}>
                  {selectedSubscription.status?.replace('_', ' ')}
                </span>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-slate-500">Company</p>
                  <p className="font-medium">{selectedSubscription.company_name}</p>
                </div>
                <div>
                  <p className="text-slate-500">Plan</p>
                  <p className="font-medium">{selectedSubscription.plan_name}</p>
                </div>
                <div>
                  <p className="text-slate-500">Users</p>
                  <p className="font-medium">{selectedSubscription.num_users}</p>
                </div>
                <div>
                  <p className="text-slate-500">Total Cost</p>
                  <p className="font-medium">{formatCurrency(selectedSubscription.total_price)} / {selectedSubscription.billing_cycle}</p>
                </div>
                <div>
                  <p className="text-slate-500">Start Date</p>
                  <p className="font-medium">{formatDate(selectedSubscription.start_date)}</p>
                </div>
                <div>
                  <p className="text-slate-500">Renewal Date</p>
                  <p className="font-medium">{formatDate(selectedSubscription.renewal_date)}</p>
                </div>
                {selectedSubscription.admin_email && (
                  <div>
                    <p className="text-slate-500">Admin Email</p>
                    <p className="font-medium">{selectedSubscription.admin_email}</p>
                  </div>
                )}
              </div>
              
              {selectedSubscription.recent_tickets?.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Recent Tickets</h4>
                  <div className="space-y-2">
                    {selectedSubscription.recent_tickets.map(ticket => (
                      <div key={ticket.id} className="p-3 bg-slate-50 rounded-lg text-sm">
                        <div className="flex justify-between">
                          <span className="font-medium">{ticket.subject}</span>
                          <span className={`text-xs px-2 py-0.5 rounded-full ${statusColors[ticket.status] || 'bg-slate-100'}`}>
                            {ticket.status}
                          </span>
                        </div>
                        <p className="text-slate-500 text-xs mt-1">{ticket.ticket_number} • {formatDate(ticket.created_at)}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={() => openTicketModal(selectedSubscription)}>
                  <Ticket className="h-4 w-4 mr-2" />
                  Create Ticket
                </Button>
                <Button onClick={() => { setDetailModalOpen(false); openEditModal(selectedSubscription); }}>
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Ticket Modal */}
      <Dialog open={ticketModalOpen} onOpenChange={setTicketModalOpen}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>Create Support Ticket</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreateTicket} className="space-y-4 mt-4">
            {selectedSubscription && (
              <div className="p-3 bg-slate-50 rounded-lg text-sm">
                <p><strong>Subscription:</strong> {selectedSubscription.provider_name}</p>
                <p><strong>Domain:</strong> {selectedSubscription.domain}</p>
              </div>
            )}
            
            <div>
              <label className="form-label">Issue Type</label>
              <select
                value={ticketData.issue_type}
                onChange={(e) => setTicketData({ ...ticketData, issue_type: e.target.value })}
                className="form-select"
              >
                <option value="login_issue">Login Issue</option>
                <option value="email_not_working">Email Not Working</option>
                <option value="storage_full">Storage Full</option>
                <option value="billing">Billing Issue</option>
                <option value="dns_issue">DNS Issue</option>
                <option value="add_user">Add User</option>
                <option value="remove_user">Remove User</option>
                <option value="other">Other</option>
              </select>
            </div>
            
            <div>
              <label className="form-label">Subject *</label>
              <input
                type="text"
                value={ticketData.subject}
                onChange={(e) => setTicketData({ ...ticketData, subject: e.target.value })}
                className="form-input"
                placeholder="Brief description of the issue"
              />
            </div>
            
            <div>
              <label className="form-label">Description *</label>
              <textarea
                value={ticketData.description}
                onChange={(e) => setTicketData({ ...ticketData, description: e.target.value })}
                className="form-input"
                rows={4}
                placeholder="Detailed description of the issue..."
              />
            </div>
            
            <div>
              <label className="form-label">Priority</label>
              <select
                value={ticketData.priority}
                onChange={(e) => setTicketData({ ...ticketData, priority: e.target.value })}
                className="form-select"
              >
                <option value="low">Low</option>
                <option value="medium">Medium</option>
                <option value="high">High</option>
                <option value="urgent">Urgent</option>
              </select>
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setTicketModalOpen(false)}>
                Cancel
              </Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                Create Ticket
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Subscriptions;
