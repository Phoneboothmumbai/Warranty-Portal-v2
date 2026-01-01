import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, MapPin, MoreVertical, Building2, 
  Eye, Phone, Mail, Package, ChevronRight
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Link } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const SITE_TYPES = [
  { value: 'office', label: 'Office' },
  { value: 'warehouse', label: 'Warehouse' },
  { value: 'site_project', label: 'Site / Project' },
  { value: 'branch', label: 'Branch' },
];

const Sites = () => {
  const { token } = useAuth();
  const [sites, setSites] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [editingSite, setEditingSite] = useState(null);
  const [selectedSite, setSelectedSite] = useState(null);
  
  const [formData, setFormData] = useState({
    company_id: '',
    name: '',
    site_type: 'office',
    address: '',
    city: '',
    primary_contact_name: '',
    contact_number: '',
    contact_email: '',
    notes: ''
  });

  useEffect(() => {
    fetchData();
  }, [filterCompany]);

  const fetchData = async () => {
    try {
      const params = {};
      if (filterCompany) params.company_id = filterCompany;
      
      const [sitesRes, companiesRes] = await Promise.all([
        axios.get(`${API}/admin/sites`, {
          params,
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/companies`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setSites(sitesRes.data);
      setCompanies(companiesRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.name) {
      toast.error('Please fill in required fields');
      return;
    }

    const submitData = { ...formData };
    ['address', 'city', 'primary_contact_name', 'contact_number', 'contact_email', 'notes'].forEach(f => {
      if (!submitData[f]) delete submitData[f];
    });

    try {
      if (editingSite) {
        await axios.put(`${API}/admin/sites/${editingSite.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Site updated');
      } else {
        await axios.post(`${API}/admin/sites`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Site created');
      }
      fetchData();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (site) => {
    if (!window.confirm(`Delete site "${site.name}"?`)) return;
    
    try {
      await axios.delete(`${API}/admin/sites/${site.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Site archived');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete site');
    }
  };

  const openCreateModal = () => {
    setEditingSite(null);
    setFormData({
      company_id: filterCompany || '',
      name: '',
      site_type: 'office',
      address: '',
      city: '',
      primary_contact_name: '',
      contact_number: '',
      contact_email: '',
      notes: ''
    });
    setModalOpen(true);
  };

  const openEditModal = (site) => {
    setEditingSite(site);
    setFormData({
      company_id: site.company_id,
      name: site.name,
      site_type: site.site_type || 'office',
      address: site.address || '',
      city: site.city || '',
      primary_contact_name: site.primary_contact_name || '',
      contact_number: site.contact_number || '',
      contact_email: site.contact_email || '',
      notes: site.notes || ''
    });
    setModalOpen(true);
  };

  const openDetailModal = async (site) => {
    try {
      const response = await axios.get(`${API}/admin/sites/${site.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedSite(response.data);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error('Failed to load site details');
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingSite(null);
  };

  const filteredSites = sites.filter(s => 
    s.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    s.city?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getSiteTypeLabel = (type) => {
    const found = SITE_TYPES.find(t => t.value === type);
    return found ? found.label : type;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="sites-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Sites & Locations</h1>
          <p className="text-slate-500 mt-1">Manage company sites, branches, and project locations</p>
        </div>
        <Button 
          onClick={openCreateModal}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
          data-testid="add-site-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Site
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Total Sites</p>
          <p className="text-2xl font-semibold text-slate-900 mt-1">{sites.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Offices</p>
          <p className="text-2xl font-semibold text-blue-600 mt-1">
            {sites.filter(s => s.site_type === 'office').length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Projects</p>
          <p className="text-2xl font-semibold text-emerald-600 mt-1">
            {sites.filter(s => s.site_type === 'site_project').length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Total Deployments</p>
          <p className="text-2xl font-semibold text-amber-600 mt-1">
            {sites.reduce((sum, s) => sum + (s.deployments_count || 0), 0)}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search sites..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input pl-11"
          />
        </div>
        <select
          value={filterCompany}
          onChange={(e) => setFilterCompany(e.target.value)}
          className="form-select w-full sm:w-48"
        >
          <option value="">All Companies</option>
          {companies.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
      </div>

      {/* Sites List */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {filteredSites.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full table-modern">
              <thead>
                <tr>
                  <th>Site</th>
                  <th>Company</th>
                  <th>Type</th>
                  <th>Location</th>
                  <th>Contact</th>
                  <th>Deployments</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {filteredSites.map((site) => (
                  <tr key={site.id} data-testid={`site-row-${site.id}`}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                          <MapPin className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{site.name}</p>
                          {site.address && (
                            <p className="text-xs text-slate-500 truncate max-w-[200px]">{site.address}</p>
                          )}
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-sm">{site.company_name}</span>
                      </div>
                    </td>
                    <td>
                      <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-600">
                        {getSiteTypeLabel(site.site_type)}
                      </span>
                    </td>
                    <td>
                      <span className="text-sm text-slate-600">{site.city || '-'}</span>
                    </td>
                    <td>
                      <div className="text-sm">
                        <p className="text-slate-900">{site.primary_contact_name || '-'}</p>
                        {site.contact_number && (
                          <p className="text-xs text-slate-500">{site.contact_number}</p>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Package className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-sm">{site.deployments_count || 0}</span>
                        <span className="text-xs text-slate-400">({site.items_count || 0} items)</span>
                      </div>
                    </td>
                    <td>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openDetailModal(site)}>
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openEditModal(site)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(site)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Archive
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-16">
            <MapPin className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No sites found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add your first site
            </Button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingSite ? 'Edit Site' : 'Add Site'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Company *</label>
              <select
                value={formData.company_id}
                onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                className="form-select"
                disabled={!!editingSite}
              >
                <option value="">Select Company</option>
                {companies.map(c => (
                  <option key={c.id} value={c.id}>{c.name}</option>
                ))}
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2 sm:col-span-1">
                <label className="form-label">Site Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="form-input"
                  placeholder="e.g., Wadhwa 1620 – Mulund"
                />
              </div>
              <div className="col-span-2 sm:col-span-1">
                <label className="form-label">Site Type</label>
                <select
                  value={formData.site_type}
                  onChange={(e) => setFormData({ ...formData, site_type: e.target.value })}
                  className="form-select"
                >
                  {SITE_TYPES.map(type => (
                    <option key={type.value} value={type.value}>{type.label}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div>
              <label className="form-label">Address</label>
              <textarea
                value={formData.address}
                onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                className="form-input"
                rows={2}
                placeholder="Full address"
              />
            </div>
            
            <div>
              <label className="form-label">City</label>
              <input
                type="text"
                value={formData.city}
                onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                className="form-input"
                placeholder="City name"
              />
            </div>
            
            <div className="border-t pt-4 mt-4">
              <p className="text-sm font-medium text-slate-700 mb-3">Primary Contact</p>
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2 sm:col-span-1">
                  <label className="form-label">Contact Name</label>
                  <input
                    type="text"
                    value={formData.primary_contact_name}
                    onChange={(e) => setFormData({ ...formData, primary_contact_name: e.target.value })}
                    className="form-input"
                    placeholder="Site manager name"
                  />
                </div>
                <div className="col-span-2 sm:col-span-1">
                  <label className="form-label">Phone</label>
                  <input
                    type="tel"
                    value={formData.contact_number}
                    onChange={(e) => setFormData({ ...formData, contact_number: e.target.value })}
                    className="form-input"
                    placeholder="+91..."
                  />
                </div>
              </div>
              <div className="mt-4">
                <label className="form-label">Email</label>
                <input
                  type="email"
                  value={formData.contact_email}
                  onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                  className="form-input"
                  placeholder="site@company.com"
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
                placeholder="Internal notes..."
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                {editingSite ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Site Details</DialogTitle>
          </DialogHeader>
          {selectedSite && (
            <div className="space-y-6 mt-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center">
                    <MapPin className="h-7 w-7 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-slate-900">{selectedSite.name}</h3>
                    <p className="text-slate-500">{selectedSite.company_name}</p>
                  </div>
                </div>
                <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-600">
                  {getSiteTypeLabel(selectedSite.site_type)}
                </span>
              </div>

              {/* Info Grid */}
              <div className="grid grid-cols-2 gap-4 p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-xs text-slate-500">Address</p>
                  <p className="text-sm font-medium">{selectedSite.address || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">City</p>
                  <p className="text-sm font-medium">{selectedSite.city || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Contact</p>
                  <p className="text-sm font-medium">{selectedSite.primary_contact_name || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Phone</p>
                  <p className="text-sm font-medium">{selectedSite.contact_number || '-'}</p>
                </div>
              </div>

              {/* Deployments */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-medium text-slate-900">
                    Deployments ({selectedSite.deployments?.length || 0})
                  </h4>
                  <Link 
                    to={`/admin/deployments?site_id=${selectedSite.id}`}
                    className="text-xs text-[#0F62FE] hover:underline"
                  >
                    View All →
                  </Link>
                </div>
                {selectedSite.deployments?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedSite.deployments.slice(0, 5).map(dep => (
                      <div key={dep.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div>
                          <p className="text-sm font-medium text-slate-900">{dep.name}</p>
                          <p className="text-xs text-slate-500">{dep.items?.length || 0} items</p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No deployments yet</p>
                )}
              </div>

              {/* Active AMCs */}
              {selectedSite.active_amcs?.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-slate-900 mb-3">
                    Active AMC Coverage
                  </h4>
                  <div className="space-y-2">
                    {selectedSite.active_amcs.map(amc => (
                      <div key={amc.id} className="flex items-center gap-2 p-2 bg-emerald-50 rounded-lg text-sm text-emerald-700">
                        <span>✓</span>
                        <span>{amc.name}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={() => setDetailModalOpen(false)}>
                  Close
                </Button>
                <Link to={`/admin/deployments?site_id=${selectedSite.id}`}>
                  <Button className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                    <Package className="h-4 w-4 mr-2" />
                    Add Deployment
                  </Button>
                </Link>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Sites;
