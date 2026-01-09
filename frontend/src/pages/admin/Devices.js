import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Plus, Search, Edit2, Trash2, Laptop, MoreVertical, Building2, User, Calendar, Eye, History, FileText, Shield, CheckCircle, XCircle, Clock, AlertTriangle, ExternalLink, MapPin, Package, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { BulkImport } from '../../components/ui/bulk-import';
import { toast } from 'sonner';
import { SmartSelect } from '../../components/ui/smart-select';
import { DateDurationInput } from '../../components/ui/date-duration-input';
import { QuickCreateCompany, QuickCreateUser, QuickCreateMaster } from '../../components/forms';
import { useNavigate, useSearchParams } from 'react-router-dom';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Bulk import configuration
const bulkImportColumns = [
  { key: 'serial_number', label: 'Serial Number', required: true, example: 'ABC123456' },
  { key: 'company_code', label: 'Company Code', required: true, example: 'ACME001' },
  { key: 'company_name', label: 'Company Name (alt)', required: false, example: 'Acme Corp' },
  { key: 'device_type', label: 'Device Type', required: false, example: 'Laptop' },
  { key: 'brand', label: 'Brand', required: true, example: 'Dell' },
  { key: 'model', label: 'Model', required: true, example: 'Latitude 5520' },
  { key: 'asset_tag', label: 'Asset Tag', required: false, example: 'ACME-001' },
  { key: 'purchase_date', label: 'Purchase Date', required: false, example: '2024-01-15' },
  { key: 'warranty_end_date', label: 'Warranty End', required: false, example: '2027-01-15' },
  { key: 'vendor', label: 'Vendor', required: false, example: 'Dell India' },
  { key: 'location', label: 'Location', required: false, example: 'Floor 2, Desk 15' },
  { key: 'condition', label: 'Condition', required: false, example: 'good' },
  { key: 'status', label: 'Status', required: false, example: 'active' },
];

const deviceSampleData = [
  { serial_number: 'DEL-001-2024', company_code: 'ACME001', device_type: 'Laptop', brand: 'Dell', model: 'Latitude 5520', asset_tag: 'ACME-LAP-001', purchase_date: '2024-01-15', warranty_end_date: '2027-01-15', vendor: 'Dell India', location: 'Floor 2, Desk 15', condition: 'good', status: 'active' },
  { serial_number: 'HP-002-2024', company_code: 'ACME001', device_type: 'Printer', brand: 'HP', model: 'LaserJet Pro M404', asset_tag: 'ACME-PRN-001', purchase_date: '2024-02-20', warranty_end_date: '2026-02-20', vendor: 'HP Store', location: 'Reception', condition: 'new', status: 'active' },
];

// Empty consumable item template
const emptyConsumable = {
  id: '',
  name: '',
  consumable_type: 'Toner Cartridge',
  model_number: '',
  brand: '',
  color: '',
  notes: ''
};

const Devices = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [devices, setDevices] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterAMC, setFilterAMC] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedDevice, setSelectedDevice] = useState(null);
  const [editingDevice, setEditingDevice] = useState(null);
  
  // Master data
  const [deviceTypes, setDeviceTypes] = useState([]);
  const [brands, setBrands] = useState([]);
  const [conditions, setConditions] = useState([]);
  const [assetStatuses, setAssetStatuses] = useState([]);
  
  const [formData, setFormData] = useState({
    company_id: '',
    assigned_user_id: '',
    device_type: '',
    brand: '',
    model: '',
    serial_number: '',
    asset_tag: '',
    purchase_date: '',
    purchase_cost: '',
    vendor: '',
    warranty_end_date: '',
    location: '',
    condition: 'good',
    status: 'active',
    notes: '',
    // Multiple consumables for printers
    consumables: []
  });

  useEffect(() => {
    fetchData();
    fetchMasterData();
  }, [filterCompany, filterStatus, filterAMC]);

  // Handle URL query parameter to open device details directly
  useEffect(() => {
    const deviceId = searchParams.get('id');
    if (deviceId && devices.length > 0) {
      const device = devices.find(d => d.id === deviceId);
      if (device) {
        setSelectedDevice(device);
        setDetailModalOpen(true);
        // Clear the URL parameter after opening
        setSearchParams({});
      }
    }
  }, [devices, searchParams]);

  const fetchMasterData = async () => {
    try {
      const [deviceTypesRes, brandsRes, conditionsRes, statusesRes] = await Promise.all([
        axios.get(`${API}/masters/public`, { params: { master_type: 'device_type' } }),
        axios.get(`${API}/masters/public`, { params: { master_type: 'brand' } }),
        axios.get(`${API}/masters/public`, { params: { master_type: 'condition' } }),
        axios.get(`${API}/masters/public`, { params: { master_type: 'asset_status' } }),
      ]);
      setDeviceTypes(deviceTypesRes.data);
      setBrands(brandsRes.data);
      setConditions(conditionsRes.data);
      setAssetStatuses(statusesRes.data);
    } catch (error) {
      console.error('Failed to fetch master data');
    }
  };

  const fetchData = async () => {
    try {
      const params = {};
      if (filterCompany) params.company_id = filterCompany;
      if (filterStatus) params.status = filterStatus;
      if (filterAMC) params.amc_status = filterAMC;
      
      const [devicesRes, companiesRes] = await Promise.all([
        axios.get(`${API}/admin/devices`, {
          params,
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/companies`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setDevices(devicesRes.data);
      setCompanies(companiesRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const fetchCompanyUsers = async (companyId) => {
    if (!companyId) {
      setUsers([]);
      return;
    }
    try {
      const response = await axios.get(`${API}/admin/users`, {
        params: { company_id: companyId },
        headers: { Authorization: `Bearer ${token}` }
      });
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users');
    }
  };

  const handleCompanyChange = (companyId) => {
    setFormData({ ...formData, company_id: companyId, assigned_user_id: '' });
    fetchCompanyUsers(companyId);
  };

  // Consumable management functions
  const addConsumable = () => {
    const newConsumable = { 
      ...emptyConsumable, 
      id: `temp-${Date.now()}` 
    };
    setFormData({ 
      ...formData, 
      consumables: [...formData.consumables, newConsumable] 
    });
  };

  const updateConsumable = (index, field, value) => {
    const updated = [...formData.consumables];
    updated[index] = { ...updated[index], [field]: value };
    setFormData({ ...formData, consumables: updated });
  };

  const removeConsumable = (index) => {
    const updated = formData.consumables.filter((_, i) => i !== index);
    setFormData({ ...formData, consumables: updated });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.serial_number || !formData.brand || !formData.model || !formData.device_type) {
      toast.error('Please fill in required fields');
      return;
    }

    const submitData = { ...formData };
    // Clean up optional fields
    ['assigned_user_id', 'asset_tag', 'warranty_end_date', 'vendor', 'location', 'notes'].forEach(field => {
      if (!submitData[field]) delete submitData[field];
    });
    if (submitData.purchase_cost) {
      submitData.purchase_cost = parseFloat(submitData.purchase_cost);
    } else {
      delete submitData.purchase_cost;
    }
    // Clean up empty consumables
    if (submitData.consumables) {
      submitData.consumables = submitData.consumables.filter(c => c.name || c.model_number);
    }

    try {
      if (editingDevice) {
        await axios.put(`${API}/admin/devices/${editingDevice.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Device updated');
      } else {
        await axios.post(`${API}/admin/devices`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Device created');
      }
      fetchData();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (device) => {
    if (!window.confirm(`Delete "${device.brand} ${device.model}"? This will also delete related parts and service history.`)) return;
    
    try {
      await axios.delete(`${API}/admin/devices/${device.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Device deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete device');
    }
  };

  const handleBulkImport = async (records) => {
    const response = await axios.post(`${API}/admin/bulk-import/devices`, 
      { records },
      { headers: { Authorization: `Bearer ${token}` } }
    );
    fetchData();
    return response.data;
  };

  const openCreateModal = () => {
    setEditingDevice(null);
    setFormData({
      company_id: filterCompany || '',
      assigned_user_id: '',
      device_type: deviceTypes[0]?.name || 'Laptop',
      brand: '',
      model: '',
      serial_number: '',
      asset_tag: '',
      purchase_date: '',
      purchase_cost: '',
      vendor: '',
      warranty_end_date: '',
      location: '',
      condition: 'good',
      status: 'active',
      notes: '',
      consumables: []
    });
    if (filterCompany) {
      fetchCompanyUsers(filterCompany);
    } else {
      setUsers([]);
    }
    setModalOpen(true);
  };

  const openEditModal = async (device) => {
    setEditingDevice(device);
    setFormData({
      company_id: device.company_id,
      assigned_user_id: device.assigned_user_id || '',
      device_type: device.device_type,
      brand: device.brand,
      model: device.model,
      serial_number: device.serial_number,
      asset_tag: device.asset_tag || '',
      purchase_date: device.purchase_date,
      purchase_cost: device.purchase_cost || '',
      vendor: device.vendor || '',
      warranty_end_date: device.warranty_end_date || '',
      location: device.location || '',
      condition: device.condition || 'good',
      status: device.status,
      notes: device.notes || '',
      consumables: device.consumables || []
    });
    await fetchCompanyUsers(device.company_id);
    setModalOpen(true);
  };

  const openDetailModal = async (device) => {
    try {
      // Fetch full device details including AMC info from API
      const response = await axios.get(`${API}/admin/devices/${device.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedDevice(response.data);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error('Failed to fetch device details');
      // Fallback to list data
      setSelectedDevice(device);
      setDetailModalOpen(true);
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingDevice(null);
    setUsers([]);
  };

  const getCompanyName = (companyId) => {
    const company = companies.find(c => c.id === companyId);
    return company?.name || 'Unknown';
  };

  const getUserName = (userId) => {
    if (!userId) return null;
    const allUsers = devices.map(d => d.assigned_user).filter(Boolean);
    // This is a simplified lookup - in production you'd want to cache this
    return userId;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const isWarrantyActive = (dateStr) => {
    if (!dateStr) return false;
    return new Date(dateStr) >= new Date();
  };

  const getWarrantyDaysLeft = (dateStr) => {
    if (!dateStr) return null;
    const end = new Date(dateStr);
    const now = new Date();
    const diff = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    return diff;
  };

  const filteredDevices = devices.filter(d => 
    d.serial_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.brand.toLowerCase().includes(searchQuery.toLowerCase()) ||
    d.model.toLowerCase().includes(searchQuery.toLowerCase()) ||
    (d.asset_tag && d.asset_tag.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  const statusColors = {
    active: 'bg-emerald-50 text-emerald-600',
    in_repair: 'bg-amber-50 text-amber-600',
    retired: 'bg-slate-100 text-slate-500',
    lost: 'bg-red-50 text-red-600',
    scrapped: 'bg-slate-200 text-slate-600'
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="devices-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Devices</h1>
          <p className="text-slate-500 mt-1">Manage devices and assets</p>
        </div>
        <Button 
          onClick={openCreateModal}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
          data-testid="add-device-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Device
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by serial, brand, model..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input pl-11"
            data-testid="search-devices"
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
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="form-select w-full sm:w-40"
        >
          <option value="">All Statuses</option>
          {assetStatuses.map(s => (
            <option key={s.id} value={s.code?.toLowerCase() || s.name.toLowerCase()}>{s.name}</option>
          ))}
        </select>
        <select
          value={filterAMC}
          onChange={(e) => setFilterAMC(e.target.value)}
          className="form-select w-full sm:w-36"
        >
          <option value="">All AMC</option>
          <option value="active">AMC Active</option>
          <option value="expired">AMC Expired</option>
          <option value="none">No AMC</option>
        </select>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Total Devices</p>
          <p className="text-2xl font-semibold text-slate-900 mt-1">{devices.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Active</p>
          <p className="text-2xl font-semibold text-emerald-600 mt-1">
            {devices.filter(d => d.status === 'active').length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Under Warranty</p>
          <p className="text-2xl font-semibold text-blue-600 mt-1">
            {devices.filter(d => isWarrantyActive(d.warranty_end_date)).length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">With AMC</p>
          <p className="text-2xl font-semibold text-purple-600 mt-1">
            {devices.filter(d => d.amc_status === 'active').length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">In Repair</p>
          <p className="text-2xl font-semibold text-amber-600 mt-1">
            {devices.filter(d => d.status === 'in_repair').length}
          </p>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {filteredDevices.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full table-modern">
              <thead>
                <tr>
                  <th>Device</th>
                  <th>Serial / Asset</th>
                  <th>Company</th>
                  <th>Warranty</th>
                  <th>AMC</th>
                  <th>Condition</th>
                  <th>Status</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {filteredDevices.map((device) => {
                  const daysLeft = getWarrantyDaysLeft(device.warranty_end_date);
                  return (
                    <tr key={device.id} data-testid={`device-row-${device.id}`}>
                      <td>
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 bg-slate-100 rounded-lg flex items-center justify-center">
                            <Laptop className="h-4 w-4 text-slate-600" />
                          </div>
                          <div>
                            <p className="font-medium text-slate-900">{device.brand} {device.model}</p>
                            <div className="flex items-center gap-2">
                              <span className="text-xs text-slate-500">{device.device_type}</span>
                              {device.source === 'deployment' && (
                                <span className="text-xs px-1.5 py-0.5 bg-purple-50 text-purple-600 rounded">
                                  Deployment
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      </td>
                      <td>
                        <p className="font-mono text-sm">{device.serial_number}</p>
                        {device.asset_tag && (
                          <p className="text-xs text-slate-500 font-mono">Tag: {device.asset_tag}</p>
                        )}
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <Building2 className="h-3.5 w-3.5 text-slate-400" />
                          <span className="text-sm">{getCompanyName(device.company_id)}</span>
                        </div>
                        {device.site_name && (
                          <p className="text-xs text-slate-500 flex items-center gap-1 mt-0.5">
                            <MapPin className="h-3 w-3" />
                            {device.site_name}
                          </p>
                        )}
                      </td>
                      <td>
                        {device.warranty_end_date ? (
                          <div>
                            <span className={`text-xs px-2 py-1 rounded-full ${
                              daysLeft > 30
                                ? 'bg-emerald-50 text-emerald-600'
                                : daysLeft > 0
                                ? 'bg-amber-50 text-amber-600'
                                : 'bg-slate-100 text-slate-500'
                            }`}>
                              {daysLeft > 0 ? `${daysLeft} days` : 'Expired'}
                            </span>
                            <p className="text-xs text-slate-500 mt-1">{formatDate(device.warranty_end_date)}</p>
                          </div>
                        ) : (
                          <span className="text-xs text-slate-400">Not set</span>
                        )}
                      </td>
                      <td>
                        {/* AMC Status Column - P0 Fix */}
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          device.amc_status === 'active'
                            ? 'bg-blue-50 text-blue-600'
                            : device.amc_status === 'expired'
                            ? 'bg-orange-50 text-orange-600'
                            : 'bg-slate-100 text-slate-400'
                        }`}>
                          {device.amc_status === 'active' ? 'Active' : device.amc_status === 'expired' ? 'Expired' : 'None'}
                        </span>
                        {device.amc_contract_name && (
                          <p className="text-xs text-slate-500 mt-1 truncate max-w-[100px]" title={device.amc_contract_name}>
                            {device.amc_contract_name}
                          </p>
                        )}
                      </td>
                      <td>
                        <span className="text-sm capitalize text-slate-600">{device.condition || '-'}</span>
                      </td>
                      <td>
                        <span className={`text-xs px-2 py-1 rounded-full capitalize ${statusColors[device.status] || 'bg-slate-100 text-slate-500'}`}>
                          {device.status?.replace('_', ' ')}
                        </span>
                      </td>
                      <td>
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="icon">
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem onClick={() => openDetailModal(device)}>
                              <Eye className="h-4 w-4 mr-2" />
                              View Details
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openEditModal(device)}>
                              <Edit2 className="h-4 w-4 mr-2" />
                              Edit
                            </DropdownMenuItem>
                            <DropdownMenuItem 
                              onClick={() => handleDelete(device)}
                              className="text-red-600"
                            >
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
          </div>
        ) : (
          <div className="text-center py-16">
            <Laptop className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No devices found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add your first device
            </Button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingDevice ? 'Edit Device' : 'Add Device'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Company *</label>
                <SmartSelect
                  value={formData.company_id}
                  onValueChange={(value) => handleCompanyChange(value)}
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
                  data-testid="device-company-select"
                />
              </div>
              <div>
                <label className="form-label">Assigned User</label>
                <SmartSelect
                  value={formData.assigned_user_id}
                  onValueChange={(value) => setFormData({ ...formData, assigned_user_id: value })}
                  placeholder={!formData.company_id ? "Select company first" : "Select User (optional)"}
                  searchPlaceholder="Search users..."
                  emptyText="No users found"
                  disabled={!formData.company_id}
                  fetchOptions={formData.company_id ? async (q) => {
                    const res = await axios.get(`${API}/admin/users`, {
                      params: { q, company_id: formData.company_id, limit: 20 },
                      headers: { Authorization: `Bearer ${token}` }
                    });
                    return res.data;
                  } : undefined}
                  options={!formData.company_id ? [] : undefined}
                  displayKey="name"
                  valueKey="id"
                  allowCreate={!!formData.company_id}
                  createLabel="Add New User"
                  renderCreateForm={formData.company_id ? ({ initialValue, onSuccess, onCancel }) => (
                    <QuickCreateUser
                      initialValue={initialValue}
                      companyId={formData.company_id}
                      onSuccess={onSuccess}
                      onCancel={onCancel}
                      token={token}
                    />
                  ) : undefined}
                />
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">Device Type *</label>
                <SmartSelect
                  value={formData.device_type}
                  onValueChange={(value) => setFormData({ ...formData, device_type: value })}
                  placeholder="Select Type"
                  searchPlaceholder="Search types..."
                  emptyText="No types found"
                  fetchOptions={async (q) => {
                    const res = await axios.get(`${API}/masters/public`, {
                      params: { master_type: 'device_type', q, limit: 20 }
                    });
                    return res.data;
                  }}
                  displayKey="name"
                  valueKey="name"
                  allowCreate
                  createLabel="Add New Type"
                  renderCreateForm={({ initialValue, onSuccess, onCancel }) => (
                    <QuickCreateMaster
                      initialValue={initialValue}
                      masterType="device_type"
                      masterLabel="Device Type"
                      onSuccess={(item) => onSuccess({ ...item, id: item.name })}
                      onCancel={onCancel}
                      token={token}
                    />
                  )}
                />
              </div>
              <div>
                <label className="form-label">Brand *</label>
                <SmartSelect
                  value={formData.brand}
                  onValueChange={(value) => setFormData({ ...formData, brand: value })}
                  placeholder="Select Brand"
                  searchPlaceholder="Search brands..."
                  emptyText="No brands found"
                  fetchOptions={async (q) => {
                    const res = await axios.get(`${API}/masters/public`, {
                      params: { master_type: 'brand', q, limit: 20 }
                    });
                    return res.data;
                  }}
                  displayKey="name"
                  valueKey="name"
                  allowCreate
                  createLabel="Add New Brand"
                  renderCreateForm={({ initialValue, onSuccess, onCancel }) => (
                    <QuickCreateMaster
                      initialValue={initialValue}
                      masterType="brand"
                      masterLabel="Brand"
                      onSuccess={(item) => onSuccess({ ...item, id: item.name })}
                      onCancel={onCancel}
                      token={token}
                    />
                  )}
                  data-testid="device-brand-select"
                />
              </div>
              <div>
                <label className="form-label">Model *</label>
                <input
                  type="text"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  className="form-input"
                  placeholder="Latitude 5520..."
                  data-testid="device-model-input"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Serial Number *</label>
                <input
                  type="text"
                  value={formData.serial_number}
                  onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
                  className="form-input font-mono"
                  data-testid="device-serial-input"
                />
              </div>
              <div>
                <label className="form-label">Asset Tag</label>
                <input
                  type="text"
                  value={formData.asset_tag}
                  onChange={(e) => setFormData({ ...formData, asset_tag: e.target.value })}
                  className="form-input font-mono"
                  placeholder="Optional"
                />
              </div>
            </div>
            
            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">Purchase Date *</label>
                <input
                  type="date"
                  value={formData.purchase_date}
                  onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
                  className="form-input"
                  data-testid="device-purchase-date-input"
                />
              </div>
              <div>
                <label className="form-label">Purchase Cost</label>
                <input
                  type="number"
                  value={formData.purchase_cost}
                  onChange={(e) => setFormData({ ...formData, purchase_cost: e.target.value })}
                  className="form-input"
                  placeholder="0.00"
                  step="0.01"
                />
              </div>
              <div>
                <label className="form-label">Vendor</label>
                <input
                  type="text"
                  value={formData.vendor}
                  onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                  className="form-input"
                  placeholder="Supplier name"
                />
              </div>
            </div>
            
            {/* Warranty Date with Dual Mode Input */}
            <div className="p-4 bg-slate-50 rounded-lg">
              <DateDurationInput
                label="Warranty Coverage"
                startDate={formData.purchase_date}
                endDate={formData.warranty_end_date}
                onEndDateChange={(date) => setFormData({ ...formData, warranty_end_date: date })}
                defaultMode="duration"
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Location</label>
                <input
                  type="text"
                  value={formData.location}
                  onChange={(e) => setFormData({ ...formData, location: e.target.value })}
                  className="form-input"
                  placeholder="Office, Room, etc."
                />
              </div>
              <div>
                <label className="form-label">Condition</label>
                <SmartSelect
                  value={formData.condition}
                  onValueChange={(value) => setFormData({ ...formData, condition: value })}
                  placeholder="Select Condition"
                  searchPlaceholder="Search..."
                  options={conditions.length > 0 
                    ? conditions.map(c => ({ id: c.code?.toLowerCase() || c.name.toLowerCase(), name: c.name, label: c.name }))
                    : [
                        { id: 'new', name: 'New', label: 'New' },
                        { id: 'good', name: 'Good', label: 'Good' },
                        { id: 'fair', name: 'Fair', label: 'Fair' },
                        { id: 'poor', name: 'Poor', label: 'Poor' }
                      ]
                  }
                  displayKey="label"
                  valueKey="id"
                />
              </div>
            </div>
            
            <div>
              <label className="form-label">Status</label>
              <SmartSelect
                value={formData.status}
                onValueChange={(value) => setFormData({ ...formData, status: value })}
                placeholder="Select Status"
                searchPlaceholder="Search..."
                options={assetStatuses.length > 0 
                  ? assetStatuses.map(s => ({ id: s.code?.toLowerCase() || s.name.toLowerCase(), name: s.name, label: s.name }))
                  : [
                      { id: 'active', name: 'Active', label: 'Active' },
                      { id: 'in_repair', name: 'In Repair', label: 'In Repair' },
                      { id: 'retired', name: 'Retired', label: 'Retired' },
                      { id: 'lost', name: 'Lost', label: 'Lost' },
                      { id: 'scrapped', name: 'Scrapped', label: 'Scrapped' }
                    ]
                }
                displayKey="label"
                valueKey="id"
              />
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
            
            {/* Consumable Details - Show only for Printers */}
            {formData.device_type?.toLowerCase().includes('printer') && (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-lg space-y-4">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-semibold text-amber-800 uppercase tracking-wider flex items-center gap-2">
                    <Package className="h-4 w-4" />
                    Consumables ({formData.consumables.length})
                  </h4>
                  <Button 
                    type="button" 
                    size="sm" 
                    onClick={addConsumable}
                    className="bg-amber-600 hover:bg-amber-700 text-white"
                    data-testid="add-consumable-btn"
                  >
                    <Plus className="h-4 w-4 mr-1" />
                    Add Consumable
                  </Button>
                </div>
                <p className="text-xs text-amber-700">
                  Define all ink/toner cartridges this printer uses. Customers can select which ones to order.
                </p>
                
                {formData.consumables.length === 0 ? (
                  <div className="text-center py-6 text-amber-600 border border-dashed border-amber-300 rounded-lg">
                    <Package className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No consumables defined yet</p>
                    <p className="text-xs">Click "Add Consumable" to add ink/toner cartridges</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {formData.consumables.map((consumable, index) => (
                      <div key={consumable.id || index} className="bg-white p-3 rounded-lg border border-amber-200 space-y-3">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-amber-700">Consumable #{index + 1}</span>
                          <button
                            type="button"
                            onClick={() => removeConsumable(index)}
                            className="text-red-500 hover:text-red-700 p-1"
                            data-testid={`remove-consumable-${index}`}
                          >
                            <X className="h-4 w-4" />
                          </button>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                          <div>
                            <label className="text-xs text-slate-600">Name *</label>
                            <input
                              type="text"
                              value={consumable.name}
                              onChange={(e) => updateConsumable(index, 'name', e.target.value)}
                              className="form-input text-sm"
                              placeholder="e.g., Black Toner"
                              data-testid={`consumable-name-${index}`}
                            />
                          </div>
                          <div>
                            <label className="text-xs text-slate-600">Type</label>
                            <select
                              value={consumable.consumable_type}
                              onChange={(e) => updateConsumable(index, 'consumable_type', e.target.value)}
                              className="form-select text-sm"
                            >
                              <option value="Toner Cartridge">Toner Cartridge</option>
                              <option value="Ink Cartridge">Ink Cartridge</option>
                              <option value="Drum Unit">Drum Unit</option>
                              <option value="Ink Tank">Ink Tank</option>
                              <option value="Ribbon">Ribbon</option>
                              <option value="Other">Other</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-xs text-slate-600">Model/Part No. *</label>
                            <input
                              type="text"
                              value={consumable.model_number}
                              onChange={(e) => updateConsumable(index, 'model_number', e.target.value)}
                              className="form-input text-sm"
                              placeholder="e.g., HP 26A"
                              data-testid={`consumable-model-${index}`}
                            />
                          </div>
                          <div>
                            <label className="text-xs text-slate-600">Color</label>
                            <select
                              value={consumable.color || ''}
                              onChange={(e) => updateConsumable(index, 'color', e.target.value)}
                              className="form-select text-sm"
                            >
                              <option value="">None</option>
                              <option value="Black">Black</option>
                              <option value="Cyan">Cyan</option>
                              <option value="Magenta">Magenta</option>
                              <option value="Yellow">Yellow</option>
                              <option value="Photo Black">Photo Black</option>
                              <option value="Tri-Color">Tri-Color</option>
                            </select>
                          </div>
                          <div>
                            <label className="text-xs text-slate-600">Brand</label>
                            <input
                              type="text"
                              value={consumable.brand || ''}
                              onChange={(e) => updateConsumable(index, 'brand', e.target.value)}
                              className="form-input text-sm"
                              placeholder="e.g., HP, Canon"
                            />
                          </div>
                          <div>
                            <label className="text-xs text-slate-600">Notes</label>
                            <input
                              type="text"
                              value={consumable.notes || ''}
                              onChange={(e) => updateConsumable(index, 'notes', e.target.value)}
                              className="form-input text-sm"
                              placeholder="Yield info..."
                            />
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
            
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="device-submit-btn">
                {editingDevice ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Modal - FULL AMC DETAILS */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Device Details</DialogTitle>
          </DialogHeader>
          {selectedDevice && (
            <div className="space-y-6 mt-4">
              {/* Device Header with AMC Badge */}
              <div className="flex items-start gap-4">
                <div className="w-16 h-16 bg-slate-100 rounded-xl flex items-center justify-center">
                  <Laptop className="h-8 w-8 text-slate-600" />
                </div>
                <div className="flex-1">
                  <h3 className="text-xl font-semibold text-slate-900">
                    {selectedDevice.brand} {selectedDevice.model}
                  </h3>
                  <p className="text-slate-500">{selectedDevice.device_type}</p>
                  <div className="flex items-center gap-2 mt-2 flex-wrap">
                    <span className={`text-xs px-2 py-1 rounded-full capitalize ${statusColors[selectedDevice.status]}`}>
                      {selectedDevice.status?.replace('_', ' ')}
                    </span>
                    <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-600 capitalize">
                      {selectedDevice.condition}
                    </span>
                    {/* AMC Badge */}
                    {selectedDevice.amc_status === 'active' && (
                      <span className="text-xs px-2 py-1 rounded-full bg-emerald-100 text-emerald-700 flex items-center gap-1">
                        <Shield className="h-3 w-3" />
                        AMC Active
                      </span>
                    )}
                    {selectedDevice.amc_status === 'expired' && (
                      <span className="text-xs px-2 py-1 rounded-full bg-red-100 text-red-700 flex items-center gap-1">
                        <Shield className="h-3 w-3" />
                        AMC Expired
                      </span>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Device Basic Info */}
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="space-y-3">
                  <div>
                    <p className="text-slate-500">Serial Number</p>
                    <p className="font-mono font-medium">{selectedDevice.serial_number}</p>
                  </div>
                  {selectedDevice.asset_tag && (
                    <div>
                      <p className="text-slate-500">Asset Tag</p>
                      <p className="font-mono font-medium">{selectedDevice.asset_tag}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-slate-500">Company</p>
                    <p className="font-medium">{selectedDevice.company_name || getCompanyName(selectedDevice.company_id)}</p>
                  </div>
                  {selectedDevice.site_name && (
                    <div>
                      <p className="text-slate-500">Site</p>
                      <p className="font-medium flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {selectedDevice.site_name}
                      </p>
                    </div>
                  )}
                  {selectedDevice.location && (
                    <div>
                      <p className="text-slate-500">Location</p>
                      <p className="font-medium">{selectedDevice.location}</p>
                    </div>
                  )}
                  {selectedDevice.source === 'deployment' && selectedDevice.deployment_name && (
                    <div>
                      <p className="text-slate-500">Source</p>
                      <a 
                        href={`/admin/deployments?id=${selectedDevice.deployment_id}`}
                        className="font-medium text-purple-600 hover:underline flex items-center gap-1"
                      >
                        <Package className="h-3 w-3" />
                        {selectedDevice.deployment_name}
                      </a>
                    </div>
                  )}
                </div>
                <div className="space-y-3">
                  <div>
                    <p className="text-slate-500">Purchase Date</p>
                    <p className="font-medium">{formatDate(selectedDevice.purchase_date)}</p>
                  </div>
                  {selectedDevice.purchase_cost && (
                    <div>
                      <p className="text-slate-500">Purchase Cost</p>
                      <p className="font-medium">₹{selectedDevice.purchase_cost.toLocaleString()}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-slate-500">
                      {selectedDevice.active_amc ? 'Manufacturer Warranty (Overridden by AMC)' : 'Warranty End'}
                    </p>
                    <p className={`font-medium ${selectedDevice.active_amc ? 'text-slate-400' : ''}`}>
                      {selectedDevice.warranty_end_date ? (
                        <>
                          {formatDate(selectedDevice.warranty_end_date)}
                          {!selectedDevice.active_amc && isWarrantyActive(selectedDevice.warranty_end_date) && (
                            <span className="ml-2 text-xs text-emerald-600">
                              ({getWarrantyDaysLeft(selectedDevice.warranty_end_date)} days left)
                            </span>
                          )}
                        </>
                      ) : 'Not set'}
                    </p>
                  </div>
                  {selectedDevice.vendor && (
                    <div>
                      <p className="text-slate-500">Vendor</p>
                      <p className="font-medium">{selectedDevice.vendor}</p>
                    </div>
                  )}
                </div>
              </div>
              
              {/* AMC Coverage Details Section - Only show if device has AMC */}
              {selectedDevice.active_amc && (
                <div className="border-t pt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider flex items-center gap-2">
                      <Shield className="h-4 w-4 text-emerald-600" />
                      AMC Coverage Details
                    </h4>
                    <button
                      onClick={() => {
                        setDetailModalOpen(false);
                        navigate(`/admin/amc-contracts?id=${selectedDevice.active_amc.amc_contract_id}`);
                      }}
                      className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                    >
                      View Contract <ExternalLink className="h-3 w-3" />
                    </button>
                  </div>
                  
                  <div className="bg-emerald-50 border border-emerald-100 rounded-xl p-4 space-y-4">
                    {/* AMC Identity */}
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <p className="text-slate-500">Contract Name</p>
                        <p className="font-medium text-slate-900">{selectedDevice.active_amc.amc_name}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Contract Type</p>
                        <p className="font-medium text-slate-900 capitalize">
                          {selectedDevice.active_amc.amc_type?.replace(/_/g, ' ') || 'Standard'}
                        </p>
                      </div>
                    </div>
                    
                    {/* Coverage Period */}
                    <div className="grid grid-cols-3 gap-4 text-sm">
                      <div>
                        <p className="text-slate-500">Start Date</p>
                        <p className="font-medium">{formatDate(selectedDevice.active_amc.coverage_start)}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">End Date</p>
                        <p className="font-medium">{formatDate(selectedDevice.active_amc.coverage_end)}</p>
                      </div>
                      <div>
                        <p className="text-slate-500">Status</p>
                        <div className="flex items-center gap-2">
                          {selectedDevice.active_amc.coverage_active ? (
                            <>
                              <CheckCircle className="h-4 w-4 text-emerald-600" />
                              <span className="font-medium text-emerald-700">Active</span>
                              <span className="text-xs text-emerald-600">
                                ({getWarrantyDaysLeft(selectedDevice.active_amc.coverage_end)} days left)
                              </span>
                            </>
                          ) : (
                            <>
                              <XCircle className="h-4 w-4 text-red-500" />
                              <span className="font-medium text-red-600">Expired</span>
                            </>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    {/* Coverage Scope */}
                    {selectedDevice.active_amc.coverage_includes && (
                      <div className="border-t border-emerald-200 pt-4">
                        <p className="text-sm font-medium text-slate-700 mb-2">Coverage Scope</p>
                        <div className="grid grid-cols-2 gap-4">
                          <div>
                            <p className="text-xs text-slate-500 mb-2">✅ Covered Items</p>
                            <div className="flex flex-wrap gap-1">
                              {(selectedDevice.active_amc.coverage_includes.hardware !== false) && (
                                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">Hardware Parts</span>
                              )}
                              {(selectedDevice.active_amc.coverage_includes.software !== false) && (
                                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">Software</span>
                              )}
                              {selectedDevice.active_amc.coverage_includes.onsite_support && (
                                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">Onsite Support</span>
                              )}
                              {selectedDevice.active_amc.coverage_includes.remote_support && (
                                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">Remote Support</span>
                              )}
                              {selectedDevice.active_amc.coverage_includes.preventive_maintenance && (
                                <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">Preventive Maintenance</span>
                              )}
                            </div>
                          </div>
                          <div>
                            <p className="text-xs text-slate-500 mb-2">❌ Not Covered</p>
                            <div className="flex flex-wrap gap-1">
                              {selectedDevice.active_amc.coverage_includes.hardware === false && (
                                <span className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded">Hardware Parts</span>
                              )}
                              {selectedDevice.active_amc.coverage_includes.exclusions?.map((item, idx) => (
                                <span key={idx} className="text-xs bg-red-50 text-red-600 px-2 py-0.5 rounded">{item}</span>
                              ))}
                              {!selectedDevice.active_amc.coverage_includes.exclusions?.length && 
                               selectedDevice.active_amc.coverage_includes.hardware !== false && (
                                <span className="text-xs text-slate-400">None specified</span>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                    
                    {/* Service Entitlements */}
                    {selectedDevice.active_amc.entitlements && (
                      <div className="border-t border-emerald-200 pt-4">
                        <p className="text-sm font-medium text-slate-700 mb-2">Service Entitlements</p>
                        <div className="grid grid-cols-3 gap-4 text-sm">
                          {selectedDevice.active_amc.entitlements.visits_per_year && (
                            <div>
                              <p className="text-xs text-slate-500">Visits/Year</p>
                              <p className="font-medium">
                                {selectedDevice.active_amc.entitlements.visits_per_year === -1 
                                  ? 'Unlimited' 
                                  : selectedDevice.active_amc.entitlements.visits_per_year}
                              </p>
                            </div>
                          )}
                          {selectedDevice.active_amc.entitlements.response_sla && (
                            <div>
                              <p className="text-xs text-slate-500">Response SLA</p>
                              <p className="font-medium">{selectedDevice.active_amc.entitlements.response_sla}</p>
                            </div>
                          )}
                          {selectedDevice.active_amc.entitlements.resolution_sla && (
                            <div>
                              <p className="text-xs text-slate-500">Resolution SLA</p>
                              <p className="font-medium">{selectedDevice.active_amc.entitlements.resolution_sla}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
              
              {/* Show expired AMC history if exists but not active */}
              {selectedDevice.amc_assignments && selectedDevice.amc_assignments.length > 0 && !selectedDevice.active_amc && (
                <div className="border-t pt-6">
                  <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4 flex items-center gap-2">
                    <Clock className="h-4 w-4 text-slate-400" />
                    AMC History (Expired)
                  </h4>
                  <div className="bg-slate-50 border border-slate-100 rounded-xl p-4">
                    {selectedDevice.amc_assignments.map((amc, idx) => (
                      <div key={idx} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                        <div>
                          <p className="font-medium text-slate-700">{amc.amc_name}</p>
                          <p className="text-xs text-slate-500">
                            {formatDate(amc.coverage_start)} — {formatDate(amc.coverage_end)}
                          </p>
                        </div>
                        <span className="text-xs px-2 py-1 rounded-full bg-red-50 text-red-600">Expired</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {/* Parts Section */}
              {selectedDevice.parts && selectedDevice.parts.length > 0 && (
                <div className="border-t pt-6">
                  <h4 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-4">
                    Replaced Parts ({selectedDevice.parts.length})
                  </h4>
                  <div className="space-y-2">
                    {selectedDevice.parts.map((part, idx) => (
                      <div key={idx} className="flex items-center justify-between py-2 px-3 bg-slate-50 rounded-lg text-sm">
                        <div>
                          <p className="font-medium">{part.part_name}</p>
                          <p className="text-xs text-slate-500">Replaced: {formatDate(part.replaced_date)}</p>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded-full ${
                          isWarrantyActive(part.warranty_expiry_date) 
                            ? 'bg-emerald-50 text-emerald-600' 
                            : 'bg-slate-100 text-slate-500'
                        }`}>
                          {isWarrantyActive(part.warranty_expiry_date) ? 'Under Warranty' : 'Warranty Expired'}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              
              {selectedDevice.notes && (
                <div className="border-t pt-6">
                  <p className="text-slate-500 text-sm">Notes</p>
                  <p className="text-sm mt-1">{selectedDevice.notes}</p>
                </div>
              )}
              
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={() => setDetailModalOpen(false)}>
                  Close
                </Button>
                <Button 
                  onClick={() => {
                    setDetailModalOpen(false);
                    openEditModal(selectedDevice);
                  }}
                  className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
                >
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit Device
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Devices;
