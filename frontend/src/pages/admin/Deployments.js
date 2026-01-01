import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, Package, MoreVertical, Building2, MapPin,
  Eye, Calendar, ChevronDown, ChevronUp, X, Check, Server, Laptop, Camera, 
  Wifi, Speaker, Monitor, HardDrive, FileText
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useSearchParams } from 'react-router-dom';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ITEM_TYPES = [
  { value: 'device', label: 'Device' },
  { value: 'infrastructure', label: 'Infrastructure' },
  { value: 'software', label: 'Software' },
  { value: 'subscription', label: 'Subscription' },
];

const CATEGORIES = [
  { value: 'CCTV Camera', label: 'CCTV Camera', icon: Camera },
  { value: 'NVR', label: 'NVR', icon: Server },
  { value: 'Access Point', label: 'Access Point', icon: Wifi },
  { value: 'Switch', label: 'Switch', icon: HardDrive },
  { value: 'Speaker', label: 'Speaker', icon: Speaker },
  { value: 'Computer', label: 'Computer', icon: Monitor },
  { value: 'Laptop', label: 'Laptop', icon: Laptop },
  { value: 'Server', label: 'Server', icon: Server },
  { value: 'Software License', label: 'Software License', icon: FileText },
  { value: 'Subscription', label: 'Subscription', icon: FileText },
  { value: 'Access Control', label: 'Access Control', icon: HardDrive },
  { value: 'PA System', label: 'PA System', icon: Speaker },
  { value: 'Other', label: 'Other', icon: Package },
];

const WARRANTY_TYPES = [
  { value: 'manufacturer', label: 'Manufacturer' },
  { value: 'installer', label: 'Installer' },
  { value: 'amc_linked', label: 'AMC Linked' },
];

const Deployments = () => {
  const { token } = useAuth();
  const [searchParams] = useSearchParams();
  const initialSiteId = searchParams.get('site_id') || '';
  
  const [deployments, setDeployments] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [sites, setSites] = useState([]);
  const [amcContracts, setAmcContracts] = useState([]);
  const [brands, setBrands] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [filterSite, setFilterSite] = useState(initialSiteId);
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [editingDeployment, setEditingDeployment] = useState(null);
  const [selectedDeployment, setSelectedDeployment] = useState(null);
  
  const [formData, setFormData] = useState({
    company_id: '',
    site_id: '',
    name: '',
    deployment_date: new Date().toISOString().split('T')[0],
    installed_by: '',
    notes: '',
    items: []
  });

  // Empty item template
  const emptyItem = {
    item_type: 'device',
    category: 'CCTV Camera',
    brand: '',
    model: '',
    quantity: 1,
    is_serialized: false,
    serial_numbers: [''],
    zone_location: '',
    installation_date: '',
    warranty_start_date: '',
    warranty_end_date: '',
    warranty_type: 'manufacturer',
    amc_contract_id: '',
    notes: ''
  };

  useEffect(() => {
    fetchData();
    fetchMasterData();
  }, [filterCompany, filterSite]);

  const fetchMasterData = async () => {
    try {
      const response = await axios.get(`${API}/masters/public`, { params: { master_type: 'brand' } });
      setBrands(response.data);
    } catch (error) {
      console.error('Failed to fetch brands');
    }
  };

  const fetchData = async () => {
    try {
      const params = {};
      if (filterCompany) params.company_id = filterCompany;
      if (filterSite) params.site_id = filterSite;
      
      const [deploymentsRes, companiesRes, sitesRes, amcRes] = await Promise.all([
        axios.get(`${API}/admin/deployments`, {
          params,
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/companies`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/sites`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/amc-contracts`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: [] }))
      ]);
      
      setDeployments(deploymentsRes.data);
      setCompanies(companiesRes.data);
      setSites(sitesRes.data);
      setAmcContracts(amcRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.site_id || !formData.name) {
      toast.error('Please fill in required fields');
      return;
    }

    // Process items - clean up empty serial numbers
    const processedItems = formData.items.map(item => ({
      ...item,
      serial_numbers: item.is_serialized 
        ? item.serial_numbers.filter(sn => sn.trim() !== '')
        : [],
      quantity: item.is_serialized 
        ? item.serial_numbers.filter(sn => sn.trim() !== '').length || 1
        : item.quantity
    }));

    const submitData = {
      ...formData,
      items: processedItems
    };

    try {
      if (editingDeployment) {
        await axios.put(`${API}/admin/deployments/${editingDeployment.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Deployment updated');
      } else {
        await axios.post(`${API}/admin/deployments`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Deployment created');
      }
      fetchData();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (deployment) => {
    if (!window.confirm(`Delete deployment "${deployment.name}"?`)) return;
    
    try {
      await axios.delete(`${API}/admin/deployments/${deployment.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Deployment archived');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete deployment');
    }
  };

  const openCreateModal = () => {
    setEditingDeployment(null);
    const companySites = filterCompany ? sites.filter(s => s.company_id === filterCompany) : sites;
    setFormData({
      company_id: filterCompany || '',
      site_id: filterSite || '',
      name: '',
      deployment_date: new Date().toISOString().split('T')[0],
      installed_by: '',
      notes: '',
      items: [{ ...emptyItem }]
    });
    setModalOpen(true);
  };

  const openEditModal = (deployment) => {
    setEditingDeployment(deployment);
    setFormData({
      company_id: deployment.company_id,
      site_id: deployment.site_id,
      name: deployment.name,
      deployment_date: deployment.deployment_date,
      installed_by: deployment.installed_by || '',
      notes: deployment.notes || '',
      items: deployment.items?.length > 0 ? deployment.items : [{ ...emptyItem }]
    });
    setModalOpen(true);
  };

  const openDetailModal = async (deployment) => {
    try {
      const response = await axios.get(`${API}/admin/deployments/${deployment.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedDeployment(response.data);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error('Failed to load deployment details');
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingDeployment(null);
  };

  // Item management functions
  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { ...emptyItem }]
    });
  };

  const removeItem = (index) => {
    if (formData.items.length <= 1) return;
    setFormData({
      ...formData,
      items: formData.items.filter((_, i) => i !== index)
    });
  };

  const updateItem = (index, field, value) => {
    const updatedItems = [...formData.items];
    updatedItems[index] = { ...updatedItems[index], [field]: value };
    
    // Auto-adjust serial numbers array based on quantity
    if (field === 'quantity' && updatedItems[index].is_serialized) {
      const qty = parseInt(value) || 1;
      const currentSerials = updatedItems[index].serial_numbers;
      if (qty > currentSerials.length) {
        updatedItems[index].serial_numbers = [
          ...currentSerials,
          ...Array(qty - currentSerials.length).fill('')
        ];
      } else {
        updatedItems[index].serial_numbers = currentSerials.slice(0, qty);
      }
    }
    
    // Toggle serialized state
    if (field === 'is_serialized') {
      if (value) {
        updatedItems[index].serial_numbers = Array(updatedItems[index].quantity).fill('');
      } else {
        updatedItems[index].serial_numbers = [];
      }
    }
    
    setFormData({ ...formData, items: updatedItems });
  };

  const updateSerialNumber = (itemIndex, snIndex, value) => {
    const updatedItems = [...formData.items];
    const serials = [...updatedItems[itemIndex].serial_numbers];
    serials[snIndex] = value;
    updatedItems[itemIndex].serial_numbers = serials;
    setFormData({ ...formData, items: updatedItems });
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const filteredDeployments = deployments.filter(d => 
    d.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.company_name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.site_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const companySites = formData.company_id 
    ? sites.filter(s => s.company_id === formData.company_id) 
    : sites;

  const companyAmcs = formData.company_id
    ? amcContracts.filter(a => a.company_id === formData.company_id && a.status === 'active')
    : [];

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="deployments-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Deployments</h1>
          <p className="text-slate-500 mt-1">Track installations and deployed items at each site</p>
        </div>
        <Button 
          onClick={openCreateModal}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
          data-testid="add-deployment-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          New Deployment
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Total Deployments</p>
          <p className="text-2xl font-semibold text-slate-900 mt-1">{deployments.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Total Items</p>
          <p className="text-2xl font-semibold text-blue-600 mt-1">
            {deployments.reduce((sum, d) => sum + (d.items_count || 0), 0)}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Sites Covered</p>
          <p className="text-2xl font-semibold text-emerald-600 mt-1">
            {new Set(deployments.map(d => d.site_id)).size}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Companies</p>
          <p className="text-2xl font-semibold text-amber-600 mt-1">
            {new Set(deployments.map(d => d.company_id)).size}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search deployments..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input pl-11"
          />
        </div>
        <select
          value={filterCompany}
          onChange={(e) => {
            setFilterCompany(e.target.value);
            setFilterSite('');
          }}
          className="form-select w-full sm:w-48"
        >
          <option value="">All Companies</option>
          {companies.map(c => (
            <option key={c.id} value={c.id}>{c.name}</option>
          ))}
        </select>
        <select
          value={filterSite}
          onChange={(e) => setFilterSite(e.target.value)}
          className="form-select w-full sm:w-48"
        >
          <option value="">All Sites</option>
          {(filterCompany ? sites.filter(s => s.company_id === filterCompany) : sites).map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      </div>

      {/* Deployments List */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {filteredDeployments.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full table-modern">
              <thead>
                <tr>
                  <th>Deployment</th>
                  <th>Site</th>
                  <th>Company</th>
                  <th>Date</th>
                  <th>Items</th>
                  <th>Installed By</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {filteredDeployments.map((deployment) => (
                  <tr key={deployment.id} data-testid={`deployment-row-${deployment.id}`}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-emerald-50 rounded-lg flex items-center justify-center">
                          <Package className="h-4 w-4 text-emerald-600" />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{deployment.name}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <MapPin className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-sm">{deployment.site_name}</span>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-sm">{deployment.company_name}</span>
                      </div>
                    </td>
                    <td>
                      <span className="text-sm">{formatDate(deployment.deployment_date)}</span>
                    </td>
                    <td>
                      <span className="text-sm font-medium">{deployment.items_count || 0} items</span>
                    </td>
                    <td>
                      <span className="text-sm text-slate-600">{deployment.installed_by || '-'}</span>
                    </td>
                    <td>
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="icon">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openDetailModal(deployment)}>
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openEditModal(deployment)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(deployment)}
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
            <Package className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No deployments found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Create first deployment
            </Button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-4xl max-h-[95vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingDeployment ? 'Edit Deployment' : 'New Deployment'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-6 mt-4">
            {/* Header Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Company *</label>
                <select
                  value={formData.company_id}
                  onChange={(e) => setFormData({ ...formData, company_id: e.target.value, site_id: '' })}
                  className="form-select"
                  disabled={!!editingDeployment}
                >
                  <option value="">Select Company</option>
                  {companies.map(c => (
                    <option key={c.id} value={c.id}>{c.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="form-label">Site *</label>
                <select
                  value={formData.site_id}
                  onChange={(e) => setFormData({ ...formData, site_id: e.target.value })}
                  className="form-select"
                  disabled={!formData.company_id || !!editingDeployment}
                >
                  <option value="">Select Site</option>
                  {companySites.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">Deployment Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="form-input"
                  placeholder="Phase 1 Infra Deployment"
                />
              </div>
              <div>
                <label className="form-label">Deployment Date</label>
                <input
                  type="date"
                  value={formData.deployment_date}
                  onChange={(e) => setFormData({ ...formData, deployment_date: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Installed By</label>
                <input
                  type="text"
                  value={formData.installed_by}
                  onChange={(e) => setFormData({ ...formData, installed_by: e.target.value })}
                  className="form-input"
                  placeholder="Internal / Vendor name"
                />
              </div>
            </div>

            {/* Items Section */}
            <div className="border-t pt-4">
              <div className="flex items-center justify-between mb-4">
                <h4 className="text-sm font-medium text-slate-900">Deployment Items</h4>
                <Button type="button" variant="outline" size="sm" onClick={addItem}>
                  <Plus className="h-3 w-3 mr-1" />
                  Add Item
                </Button>
              </div>

              <div className="space-y-4">
                {formData.items.map((item, index) => (
                  <div key={index} className="border rounded-lg p-4 bg-slate-50">
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-sm font-medium text-slate-700">Item #{index + 1}</span>
                      {formData.items.length > 1 && (
                        <button
                          type="button"
                          onClick={() => removeItem(index)}
                          className="text-red-500 hover:text-red-700"
                        >
                          <X className="h-4 w-4" />
                        </button>
                      )}
                    </div>

                    <div className="grid grid-cols-4 gap-3">
                      <div>
                        <label className="text-xs text-slate-500">Type</label>
                        <select
                          value={item.item_type}
                          onChange={(e) => updateItem(index, 'item_type', e.target.value)}
                          className="form-select text-sm"
                        >
                          {ITEM_TYPES.map(t => (
                            <option key={t.value} value={t.value}>{t.label}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Category</label>
                        <select
                          value={item.category}
                          onChange={(e) => updateItem(index, 'category', e.target.value)}
                          className="form-select text-sm"
                        >
                          {CATEGORIES.map(c => (
                            <option key={c.value} value={c.value}>{c.label}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Brand</label>
                        <input
                          type="text"
                          value={item.brand}
                          onChange={(e) => updateItem(index, 'brand', e.target.value)}
                          className="form-input text-sm"
                          placeholder="Brand"
                          list={`brands-${index}`}
                        />
                        <datalist id={`brands-${index}`}>
                          {brands.map(b => (
                            <option key={b.id} value={b.name} />
                          ))}
                        </datalist>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Model</label>
                        <input
                          type="text"
                          value={item.model}
                          onChange={(e) => updateItem(index, 'model', e.target.value)}
                          className="form-input text-sm"
                          placeholder="Model"
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-3 mt-3">
                      <div>
                        <label className="text-xs text-slate-500">Quantity</label>
                        <input
                          type="number"
                          value={item.quantity}
                          onChange={(e) => updateItem(index, 'quantity', parseInt(e.target.value) || 1)}
                          className="form-input text-sm"
                          min="1"
                        />
                      </div>
                      <div className="flex items-end">
                        <label className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={item.is_serialized}
                            onChange={(e) => updateItem(index, 'is_serialized', e.target.checked)}
                            className="rounded border-slate-300"
                          />
                          Has Serial Numbers
                        </label>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Zone/Location</label>
                        <input
                          type="text"
                          value={item.zone_location}
                          onChange={(e) => updateItem(index, 'zone_location', e.target.value)}
                          className="form-input text-sm"
                          placeholder="Floor 3 – Reception"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Warranty Type</label>
                        <select
                          value={item.warranty_type}
                          onChange={(e) => updateItem(index, 'warranty_type', e.target.value)}
                          className="form-select text-sm"
                        >
                          {WARRANTY_TYPES.map(t => (
                            <option key={t.value} value={t.value}>{t.label}</option>
                          ))}
                        </select>
                      </div>
                    </div>

                    {/* Serial Numbers */}
                    {item.is_serialized && (
                      <div className="mt-3 p-3 bg-white rounded border">
                        <label className="text-xs text-slate-500 mb-2 block">
                          Serial Numbers ({item.serial_numbers.length})
                        </label>
                        <div className="grid grid-cols-3 gap-2">
                          {item.serial_numbers.map((sn, snIndex) => (
                            <input
                              key={snIndex}
                              type="text"
                              value={sn}
                              onChange={(e) => updateSerialNumber(index, snIndex, e.target.value)}
                              className="form-input text-sm font-mono"
                              placeholder={`S/N ${snIndex + 1}`}
                            />
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Warranty Dates */}
                    <div className="grid grid-cols-3 gap-3 mt-3">
                      <div>
                        <label className="text-xs text-slate-500">Install Date</label>
                        <input
                          type="date"
                          value={item.installation_date}
                          onChange={(e) => updateItem(index, 'installation_date', e.target.value)}
                          className="form-input text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Warranty Start</label>
                        <input
                          type="date"
                          value={item.warranty_start_date}
                          onChange={(e) => updateItem(index, 'warranty_start_date', e.target.value)}
                          className="form-input text-sm"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Warranty End</label>
                        <input
                          type="date"
                          value={item.warranty_end_date}
                          onChange={(e) => updateItem(index, 'warranty_end_date', e.target.value)}
                          className="form-input text-sm"
                        />
                      </div>
                    </div>

                    {/* AMC Link */}
                    {companyAmcs.length > 0 && (
                      <div className="mt-3">
                        <label className="text-xs text-slate-500">Link to AMC</label>
                        <select
                          value={item.amc_contract_id}
                          onChange={(e) => updateItem(index, 'amc_contract_id', e.target.value)}
                          className="form-select text-sm"
                        >
                          <option value="">No AMC Link</option>
                          {companyAmcs.map(amc => (
                            <option key={amc.id} value={amc.id}>{amc.name}</option>
                          ))}
                        </select>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="form-label">Notes</label>
              <textarea
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                className="form-input"
                rows={2}
                placeholder="Deployment notes..."
              />
            </div>

            {/* Form Actions */}
            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                {editingDeployment ? 'Update' : 'Create'} Deployment
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Deployment Details</DialogTitle>
          </DialogHeader>
          {selectedDeployment && (
            <div className="space-y-6 mt-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-emerald-50 rounded-xl flex items-center justify-center">
                    <Package className="h-7 w-7 text-emerald-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-slate-900">{selectedDeployment.name}</h3>
                    <p className="text-slate-500">{selectedDeployment.site_name} • {selectedDeployment.company_name}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-500">Deployed</p>
                  <p className="font-medium">{formatDate(selectedDeployment.deployment_date)}</p>
                </div>
              </div>

              {/* Info */}
              <div className="grid grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-xs text-slate-500">Installed By</p>
                  <p className="text-sm font-medium">{selectedDeployment.installed_by || '-'}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Total Items</p>
                  <p className="text-sm font-medium">{selectedDeployment.items?.length || 0}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Created</p>
                  <p className="text-sm font-medium">{formatDate(selectedDeployment.created_at)}</p>
                </div>
              </div>

              {/* Items */}
              <div>
                <h4 className="text-sm font-medium text-slate-900 mb-3">Deployed Items</h4>
                <div className="space-y-3">
                  {selectedDeployment.items?.map((item, idx) => {
                    const CategoryIcon = CATEGORIES.find(c => c.value === item.category)?.icon || Package;
                    return (
                      <div key={idx} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                              <CategoryIcon className="h-4 w-4 text-slate-600" />
                            </div>
                            <div>
                              <p className="font-medium text-slate-900">
                                {item.brand} {item.model}
                              </p>
                              <p className="text-sm text-slate-500">{item.category}</p>
                            </div>
                          </div>
                          <div className="text-right">
                            <p className="text-sm font-medium">Qty: {item.quantity}</p>
                            {item.zone_location && (
                              <p className="text-xs text-slate-500">{item.zone_location}</p>
                            )}
                          </div>
                        </div>

                        {/* Serial Numbers */}
                        {item.serial_numbers?.length > 0 && (
                          <div className="mt-3 pt-3 border-t">
                            <p className="text-xs text-slate-500 mb-1">Serial Numbers:</p>
                            <div className="flex flex-wrap gap-1">
                              {item.serial_numbers.map((sn, snIdx) => (
                                <span key={snIdx} className="text-xs font-mono bg-slate-100 px-2 py-1 rounded">
                                  {sn}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Warranty & AMC */}
                        <div className="mt-3 pt-3 border-t flex items-center justify-between text-sm">
                          <div>
                            {item.warranty_end_date && (
                              <span className="text-slate-600">
                                Warranty: {formatDate(item.warranty_start_date)} - {formatDate(item.warranty_end_date)}
                              </span>
                            )}
                          </div>
                          {item.is_amc_covered && (
                            <span className="px-2 py-1 bg-emerald-50 text-emerald-700 rounded-full text-xs">
                              ✓ AMC: {item.covering_amc}
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={() => setDetailModalOpen(false)}>
                  Close
                </Button>
                <Button 
                  onClick={() => {
                    setDetailModalOpen(false);
                    openEditModal(selectedDeployment);
                  }}
                  className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
                >
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Deployments;
