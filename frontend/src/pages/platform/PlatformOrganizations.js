import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { toast } from 'sonner';
import { 
  Building2, Plus, Search, MoreVertical, Eye, Pause, Play, Trash2,
  Users, HardDrive, X
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_BADGES = {
  trial: { label: 'Trial', class: 'bg-blue-500/20 text-blue-400 border-blue-500/30' },
  active: { label: 'Active', class: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30' },
  past_due: { label: 'Past Due', class: 'bg-amber-500/20 text-amber-400 border-amber-500/30' },
  suspended: { label: 'Suspended', class: 'bg-red-500/20 text-red-400 border-red-500/30' },
  cancelled: { label: 'Cancelled', class: 'bg-slate-500/20 text-slate-400 border-slate-500/30' },
  churned: { label: 'Churned', class: 'bg-slate-600/20 text-slate-500 border-slate-600/30' }
};

const PLAN_BADGES = {
  trial: { label: 'Trial', class: 'bg-slate-500/20 text-slate-300' },
  starter: { label: 'Starter', class: 'bg-blue-500/20 text-blue-300' },
  professional: { label: 'Pro', class: 'bg-purple-500/20 text-purple-300' },
  enterprise: { label: 'Enterprise', class: 'bg-amber-500/20 text-amber-300' }
};

export default function PlatformOrganizations() {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedOrg, setSelectedOrg] = useState(null);
  const [actionMenuOpen, setActionMenuOpen] = useState(null);
  const [pagination, setPagination] = useState({ page: 1, pages: 1, total: 0 });
  
  const token = localStorage.getItem('platformToken');
  const navigate = useNavigate();

  useEffect(() => {
    fetchOrganizations();
  }, [searchQuery, statusFilter, pagination.page]);

  const fetchOrganizations = async () => {
    try {
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (statusFilter) params.append('status', statusFilter);
      params.append('page', pagination.page);
      params.append('limit', 20);
      
      const response = await axios.get(`${API}/api/platform/organizations?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setOrganizations(response.data.organizations);
      setPagination({
        page: response.data.page,
        pages: response.data.pages,
        total: response.data.total
      });
    } catch (error) {
      toast.error('Failed to fetch organizations');
    } finally {
      setLoading(false);
    }
  };

  const handleSuspend = async (orgId) => {
    try {
      await axios.post(`${API}/api/platform/organizations/${orgId}/suspend`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Organization suspended');
      fetchOrganizations();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to suspend');
    }
    setActionMenuOpen(null);
  };

  const handleReactivate = async (orgId) => {
    try {
      await axios.post(`${API}/api/platform/organizations/${orgId}/reactivate`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Organization reactivated');
      fetchOrganizations();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to reactivate');
    }
    setActionMenuOpen(null);
  };

  const handleDelete = async (orgId) => {
    if (!window.confirm('Are you sure you want to delete this organization? This cannot be undone.')) return;
    
    try {
      await axios.delete(`${API}/api/platform/organizations/${orgId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Organization deleted');
      fetchOrganizations();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
    setActionMenuOpen(null);
  };

  return (
    <div className="space-y-6" data-testid="platform-organizations">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Organizations</h1>
          <p className="text-slate-400">Manage all tenants on the platform</p>
        </div>
        <Button 
          onClick={() => setShowCreateModal(true)}
          className="bg-purple-600 hover:bg-purple-700"
        >
          <Plus className="w-4 h-4 mr-2" />
          Create Organization
        </Button>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search organizations..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-400 focus:ring-2 focus:ring-purple-500 focus:border-transparent"
          />
        </div>
        
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:ring-2 focus:ring-purple-500"
        >
          <option value="">All Status</option>
          <option value="trial">Trial</option>
          <option value="active">Active</option>
          <option value="past_due">Past Due</option>
          <option value="suspended">Suspended</option>
        </select>
      </div>

      {/* Organizations Table */}
      <Card className="bg-slate-800/50 border-slate-700">
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left py-4 px-6 text-sm font-medium text-slate-400">Organization</th>
                  <th className="text-left py-4 px-6 text-sm font-medium text-slate-400">Status</th>
                  <th className="text-left py-4 px-6 text-sm font-medium text-slate-400">Plan</th>
                  <th className="text-left py-4 px-6 text-sm font-medium text-slate-400">Usage</th>
                  <th className="text-left py-4 px-6 text-sm font-medium text-slate-400">Created</th>
                  <th className="text-right py-4 px-6 text-sm font-medium text-slate-400">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500 mx-auto"></div>
                    </td>
                  </tr>
                ) : organizations.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-slate-400">
                      No organizations found
                    </td>
                  </tr>
                ) : (
                  organizations.map(org => (
                    <tr key={org.id} className="border-b border-slate-700/50 hover:bg-slate-700/30">
                      <td className="py-4 px-6">
                        <div>
                          <p className="text-white font-medium">{org.name}</p>
                          <p className="text-sm text-slate-400">{org.owner_email}</p>
                        </div>
                      </td>
                      <td className="py-4 px-6">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${STATUS_BADGES[org.status]?.class}`}>
                          {STATUS_BADGES[org.status]?.label || org.status}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${PLAN_BADGES[org.subscription?.plan]?.class}`}>
                          {PLAN_BADGES[org.subscription?.plan]?.label || org.subscription?.plan}
                        </span>
                      </td>
                      <td className="py-4 px-6">
                        <div className="flex items-center gap-4 text-sm text-slate-400">
                          <span className="flex items-center gap-1">
                            <Building2 className="w-3.5 h-3.5" />
                            {org.stats?.companies || 0}
                          </span>
                          <span className="flex items-center gap-1">
                            <HardDrive className="w-3.5 h-3.5" />
                            {org.stats?.devices || 0}
                          </span>
                          <span className="flex items-center gap-1">
                            <Users className="w-3.5 h-3.5" />
                            {org.stats?.users || 0}
                          </span>
                        </div>
                      </td>
                      <td className="py-4 px-6 text-sm text-slate-400">
                        {new Date(org.created_at).toLocaleDateString()}
                      </td>
                      <td className="py-4 px-6 text-right relative">
                        <button
                          onClick={() => setActionMenuOpen(actionMenuOpen === org.id ? null : org.id)}
                          className="p-2 hover:bg-slate-700 rounded-lg text-slate-400 hover:text-white transition-colors"
                        >
                          <MoreVertical className="w-4 h-4" />
                        </button>
                        
                        {actionMenuOpen === org.id && (
                          <div className="absolute right-6 top-full mt-1 w-48 bg-slate-800 border border-slate-700 rounded-lg shadow-xl z-10">
                            <button
                              onClick={() => setSelectedOrg(org)}
                              className="w-full px-4 py-2.5 text-left text-sm text-slate-300 hover:bg-slate-700 flex items-center gap-2"
                            >
                              <Eye className="w-4 h-4" />
                              View Details
                            </button>
                            {org.status === 'suspended' ? (
                              <button
                                onClick={() => handleReactivate(org.id)}
                                className="w-full px-4 py-2.5 text-left text-sm text-emerald-400 hover:bg-slate-700 flex items-center gap-2"
                              >
                                <Play className="w-4 h-4" />
                                Reactivate
                              </button>
                            ) : (
                              <button
                                onClick={() => handleSuspend(org.id)}
                                className="w-full px-4 py-2.5 text-left text-sm text-amber-400 hover:bg-slate-700 flex items-center gap-2"
                              >
                                <Pause className="w-4 h-4" />
                                Suspend
                              </button>
                            )}
                            <button
                              onClick={() => handleDelete(org.id)}
                              className="w-full px-4 py-2.5 text-left text-sm text-red-400 hover:bg-slate-700 flex items-center gap-2"
                            >
                              <Trash2 className="w-4 h-4" />
                              Delete
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
          
          {/* Pagination */}
          {pagination.pages > 1 && (
            <div className="flex items-center justify-between px-6 py-4 border-t border-slate-700">
              <p className="text-sm text-slate-400">
                Showing {organizations.length} of {pagination.total} organizations
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.page === 1}
                  onClick={() => setPagination(p => ({ ...p, page: p.page - 1 }))}
                  className="border-slate-600 text-slate-300"
                >
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={pagination.page === pagination.pages}
                  onClick={() => setPagination(p => ({ ...p, page: p.page + 1 }))}
                  className="border-slate-600 text-slate-300"
                >
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Create Organization Modal */}
      {showCreateModal && (
        <CreateOrganizationModal 
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            fetchOrganizations();
          }}
          token={token}
        />
      )}

      {/* View Organization Detail Modal */}
      {selectedOrg && (
        <OrganizationDetailModal
          org={selectedOrg}
          onClose={() => setSelectedOrg(null)}
          token={token}
        />
      )}
    </div>
  );
}

function CreateOrganizationModal({ onClose, onSuccess, token }) {
  const [formData, setFormData] = useState({
    name: '',
    owner_email: '',
    owner_name: '',
    owner_password: '',
    plan: 'trial'
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      await axios.post(`${API}/api/platform/organizations`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Organization created successfully');
      onSuccess();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to create organization');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-md">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white">Create Organization</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Organization Name</label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
              placeholder="Acme Corp"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Owner Name</label>
            <input
              type="text"
              value={formData.owner_name}
              onChange={(e) => setFormData({ ...formData, owner_name: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
              placeholder="John Doe"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Owner Email</label>
            <input
              type="email"
              value={formData.owner_email}
              onChange={(e) => setFormData({ ...formData, owner_email: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
              placeholder="john@acme.com"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Owner Password</label>
            <input
              type="password"
              value={formData.owner_password}
              onChange={(e) => setFormData({ ...formData, owner_password: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
              placeholder="••••••••"
              required
            />
          </div>
          
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-1">Plan</label>
            <select
              value={formData.plan}
              onChange={(e) => setFormData({ ...formData, plan: e.target.value })}
              className="w-full px-4 py-2 bg-slate-700 border border-slate-600 rounded-lg text-white"
            >
              <option value="trial">Trial (14 days)</option>
              <option value="starter">Starter</option>
              <option value="professional">Professional</option>
              <option value="enterprise">Enterprise</option>
            </select>
          </div>
          
          <div className="flex gap-3 pt-4">
            <Button type="button" variant="outline" onClick={onClose} className="flex-1 border-slate-600">
              Cancel
            </Button>
            <Button type="submit" disabled={loading} className="flex-1 bg-purple-600 hover:bg-purple-700">
              {loading ? 'Creating...' : 'Create'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}

function OrganizationDetailModal({ org, onClose, token }) {
  const [details, setDetails] = useState(null);
  const [loading, setLoading] = useState(true);
  const [changingPlan, setChangingPlan] = useState(false);
  const [newPlan, setNewPlan] = useState('');

  useEffect(() => {
    fetchDetails();
  }, [org.id]);

  const fetchDetails = async () => {
    try {
      const response = await axios.get(`${API}/api/platform/organizations/${org.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDetails(response.data);
      setNewPlan(response.data.organization?.subscription?.plan || 'trial');
    } catch (error) {
      toast.error('Failed to fetch details');
    } finally {
      setLoading(false);
    }
  };

  const handleChangePlan = async () => {
    try {
      setChangingPlan(true);
      await axios.put(`${API}/api/platform/organizations/${org.id}`, 
        { plan: newPlan },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Plan updated successfully');
      fetchDetails();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update plan');
    } finally {
      setChangingPlan(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-slate-800 rounded-xl border border-slate-700 w-full max-w-2xl max-h-[80vh] overflow-hidden">
        <div className="flex items-center justify-between p-6 border-b border-slate-700">
          <h2 className="text-xl font-semibold text-white">{org.name}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <X className="w-5 h-5" />
          </button>
        </div>
        
        <div className="p-6 overflow-y-auto max-h-[60vh]">
          {loading ? (
            <div className="flex justify-center py-8">
              <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-purple-500"></div>
            </div>
          ) : details ? (
            <div className="space-y-6">
              {/* Basic Info */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Organization Details</h3>
                <div className="bg-slate-700/50 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-slate-400">Slug</span>
                    <span className="text-white font-mono">{details.organization.slug}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Owner</span>
                    <span className="text-white">{details.organization.owner_email}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Status</span>
                    <span className={`px-2 py-0.5 rounded text-xs ${STATUS_BADGES[details.organization.status]?.class}`}>
                      {details.organization.status}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Created</span>
                    <span className="text-white">{new Date(details.organization.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              </div>

              {/* Subscription Management */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Subscription</h3>
                <div className="bg-slate-700/50 rounded-lg p-4 space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-400">Current Plan</span>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-medium ${PLAN_BADGES[details.organization.subscription?.plan]?.class}`}>
                      {details.organization.subscription?.plan?.toUpperCase() || 'TRIAL'}
                    </span>
                  </div>
                  
                  <div className="border-t border-slate-600 pt-4">
                    <label className="text-sm text-slate-300 mb-2 block">Change Plan</label>
                    <div className="flex gap-2">
                      <select
                        value={newPlan}
                        onChange={(e) => setNewPlan(e.target.value)}
                        className="flex-1 px-3 py-2 bg-slate-600 border border-slate-500 rounded-lg text-white text-sm"
                        data-testid="plan-select"
                      >
                        <option value="trial">Trial (Free)</option>
                        <option value="starter">Starter (₹2,999/mo)</option>
                        <option value="professional">Professional (₹7,999/mo)</option>
                        <option value="enterprise">Enterprise (₹19,999/mo)</option>
                      </select>
                      <Button
                        onClick={handleChangePlan}
                        disabled={changingPlan || newPlan === details.organization.subscription?.plan}
                        className="bg-purple-600 hover:bg-purple-700"
                        data-testid="change-plan-btn"
                      >
                        {changingPlan ? 'Updating...' : 'Update'}
                      </Button>
                    </div>
                  </div>
                </div>
              </div>

              {/* Usage Stats */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Usage</h3>
                <div className="grid grid-cols-3 gap-4">
                  <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-white">{details.stats.companies}</p>
                    <p className="text-sm text-slate-400">Companies</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-white">{details.stats.devices}</p>
                    <p className="text-sm text-slate-400">Devices</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-white">{details.stats.users}</p>
                    <p className="text-sm text-slate-400">Users</p>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4 mt-4">
                  <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-white">{details.stats.tickets || 0}</p>
                    <p className="text-sm text-slate-400">Tickets</p>
                  </div>
                  <div className="bg-slate-700/50 rounded-lg p-4 text-center">
                    <p className="text-2xl font-bold text-white">{details.stats.amc_contracts || 0}</p>
                    <p className="text-sm text-slate-400">AMC Contracts</p>
                  </div>
                </div>
              </div>

              {/* Members */}
              <div>
                <h3 className="text-sm font-medium text-slate-400 mb-2">Team Members ({details.members.length})</h3>
                <div className="bg-slate-700/50 rounded-lg divide-y divide-slate-600 max-h-48 overflow-y-auto">
                  {details.members.map(member => (
                    <div key={member.id} className="p-3 flex items-center justify-between">
                      <div>
                        <p className="text-white font-medium">{member.name}</p>
                        <p className="text-sm text-slate-400">{member.email}</p>
                      </div>
                      <span className="text-xs px-2 py-1 bg-slate-600 rounded text-slate-300">
                        {member.role}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <p className="text-center text-slate-400">Failed to load details</p>
          )}
        </div>
      </div>
    </div>
  );
}
