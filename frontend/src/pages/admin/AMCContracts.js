import { useState, useEffect, useMemo } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, Shield, MoreVertical, Building2, 
  CheckCircle2, XCircle, Clock, AlertTriangle, ChevronRight, ChevronLeft,
  Eye, Calendar, Settings2, FileText, X, Upload, Download, File, Paperclip
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Transfer list for asset selection - moved outside component
const TransferList = ({ available, selected, onSelect, onDeselect }) => (
  <div className="grid grid-cols-2 gap-4">
    <div className="border rounded-lg p-3">
      <p className="text-xs font-medium text-slate-500 mb-2">Available Assets ({available.length})</p>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {available.map(asset => (
          <div 
            key={asset.id}
            onClick={() => onSelect(asset.id)}
            className="flex items-center justify-between p-2 bg-slate-50 rounded cursor-pointer hover:bg-slate-100"
          >
            <span className="text-sm truncate">{asset.brand} {asset.model}</span>
            <ChevronRight className="h-4 w-4 text-slate-400" />
          </div>
        ))}
        {available.length === 0 && <p className="text-xs text-slate-400">No assets available</p>}
      </div>
    </div>
    <div className="border rounded-lg p-3 border-emerald-200 bg-emerald-50/50">
      <p className="text-xs font-medium text-emerald-600 mb-2">Covered Assets ({selected.length})</p>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {selected.map(asset => (
          <div 
            key={asset.id}
            onClick={() => onDeselect(asset.id)}
            className="flex items-center justify-between p-2 bg-white rounded cursor-pointer hover:bg-red-50"
          >
            <ChevronLeft className="h-4 w-4 text-slate-400" />
            <span className="text-sm truncate">{asset.brand} {asset.model}</span>
          </div>
        ))}
        {selected.length === 0 && <p className="text-xs text-slate-400">No assets selected</p>}
      </div>
    </div>
  </div>
);

// AMC Types with descriptions
const AMC_TYPES = [
  { value: 'comprehensive', label: 'Comprehensive', desc: 'Full coverage including parts & labor' },
  { value: 'non_comprehensive', label: 'Non-Comprehensive', desc: 'Labor only, parts chargeable' },
  { value: 'support_only', label: 'Support Only', desc: 'Remote/phone support only' },
];

// Coverage options
const COVERAGE_OPTIONS = [
  { key: 'onsite_support', label: 'Onsite Support', desc: 'Engineer visits to customer location' },
  { key: 'remote_support', label: 'Remote Support', desc: 'Phone/remote assistance' },
  { key: 'preventive_maintenance', label: 'Preventive Maintenance', desc: 'Scheduled maintenance visits' },
];

// Exclusion options
const EXCLUSION_OPTIONS = [
  { key: 'hardware_parts', label: 'Hardware Parts', desc: 'Physical components' },
  { key: 'consumables', label: 'Consumables', desc: 'Ink, toner, batteries, etc.' },
  { key: 'accessories', label: 'Accessories', desc: 'Cables, bags, peripherals' },
  { key: 'third_party_software', label: 'Third-party Software', desc: 'Non-OEM software issues' },
  { key: 'physical_liquid_damage', label: 'Physical/Liquid Damage', desc: 'Accidental damage' },
];

// PM Frequency options
const PM_FREQUENCIES = [
  { value: 'quarterly', label: 'Quarterly', desc: '4 visits/year' },
  { value: 'half_yearly', label: 'Half-Yearly', desc: '2 visits/year' },
  { value: 'yearly', label: 'Yearly', desc: '1 visit/year' },
];

const AMCContracts = () => {
  const { token } = useAuth();
  const [contracts, setContracts] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [devices, setDevices] = useState([]);
  const [deviceTypes, setDeviceTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  
  // Modal state
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [editingContract, setEditingContract] = useState(null);
  const [selectedContract, setSelectedContract] = useState(null);
  const [activeTab, setActiveTab] = useState('basic');
  
  // Form data
  const [formData, setFormData] = useState({
    company_id: '',
    name: '',
    amc_type: 'comprehensive',
    start_date: '',
    end_date: '',
    coverage_includes: {
      onsite_support: true,
      remote_support: true,
      preventive_maintenance: true,
    },
    exclusions: {
      hardware_parts: true,
      consumables: true,
      accessories: true,
      third_party_software: true,
      physical_liquid_damage: true,
    },
    entitlements: {
      onsite_visits_per_year: null,
      remote_support_type: 'unlimited',
      remote_support_count: null,
      preventive_maintenance_frequency: 'quarterly',
    },
    asset_mapping: {
      mapping_type: 'all_company',
      selected_asset_ids: [],
      selected_device_types: [],
    },
    internal_notes: '',
  });

  useEffect(() => {
    fetchData();
  }, [filterStatus, filterCompany]);

  const fetchData = async () => {
    try {
      const params = {};
      if (filterStatus) params.status = filterStatus;
      if (filterCompany) params.company_id = filterCompany;
      
      const [contractsRes, companiesRes, devicesRes, deviceTypesRes] = await Promise.all([
        axios.get(`${API}/admin/amc-contracts`, {
          params,
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/companies`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/devices`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/masters/public`, { params: { master_type: 'device_type' } }),
      ]);
      
      setContracts(contractsRes.data);
      setCompanies(companiesRes.data);
      setDevices(devicesRes.data);
      setDeviceTypes(deviceTypesRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const companyDevices = useMemo(() => {
    if (!formData.company_id) return [];
    return devices.filter(d => d.company_id === formData.company_id);
  }, [formData.company_id, devices]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.name || !formData.start_date || !formData.end_date) {
      toast.error('Please fill in required fields');
      return;
    }

    if (new Date(formData.end_date) <= new Date(formData.start_date)) {
      toast.error('End date must be after start date');
      return;
    }

    try {
      if (editingContract) {
        await axios.put(`${API}/admin/amc-contracts/${editingContract.id}`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('AMC Contract updated');
      } else {
        await axios.post(`${API}/admin/amc-contracts`, formData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('AMC Contract created');
      }
      fetchData();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (contract) => {
    if (!window.confirm(`Delete AMC Contract "${contract.name}"?`)) return;
    
    try {
      await axios.delete(`${API}/admin/amc-contracts/${contract.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('AMC Contract archived');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete contract');
    }
  };

  const openCreateModal = () => {
    setEditingContract(null);
    const today = new Date().toISOString().split('T')[0];
    const nextYear = new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().split('T')[0];
    setFormData({
      company_id: filterCompany || '',
      name: '',
      amc_type: 'comprehensive',
      start_date: today,
      end_date: nextYear,
      coverage_includes: {
        onsite_support: true,
        remote_support: true,
        preventive_maintenance: true,
      },
      exclusions: {
        hardware_parts: true,
        consumables: true,
        accessories: true,
        third_party_software: true,
        physical_liquid_damage: true,
      },
      entitlements: {
        onsite_visits_per_year: null,
        remote_support_type: 'unlimited',
        remote_support_count: null,
        preventive_maintenance_frequency: 'quarterly',
      },
      asset_mapping: {
        mapping_type: 'all_company',
        selected_asset_ids: [],
        selected_device_types: [],
      },
      internal_notes: '',
    });
    setActiveTab('basic');
    setModalOpen(true);
  };

  const openEditModal = (contract) => {
    setEditingContract(contract);
    setFormData({
      company_id: contract.company_id,
      name: contract.name,
      amc_type: contract.amc_type || 'comprehensive',
      start_date: contract.start_date,
      end_date: contract.end_date,
      coverage_includes: contract.coverage_includes || {},
      exclusions: contract.exclusions || {},
      entitlements: contract.entitlements || {},
      asset_mapping: contract.asset_mapping || { mapping_type: 'all_company', selected_asset_ids: [], selected_device_types: [] },
      internal_notes: contract.internal_notes || '',
    });
    setActiveTab('basic');
    setModalOpen(true);
  };

  const openDetailModal = async (contract) => {
    try {
      const response = await axios.get(`${API}/admin/amc-contracts/${contract.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedContract(response.data);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error('Failed to load contract details');
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingContract(null);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const getStatusBadge = (status, daysLeft) => {
    if (status === 'active') {
      if (daysLeft <= 7) {
        return <span className="badge-warning">Expiring Soon</span>;
      }
      return <span className="badge-active">Active</span>;
    } else if (status === 'expired') {
      return <span className="badge-expired">Expired</span>;
    } else if (status === 'upcoming') {
      return <span className="bg-blue-50 text-blue-600 text-xs px-2 py-1 rounded-full">Upcoming</span>;
    }
    return <span className="badge-expired">{status}</span>;
  };

  const filteredContracts = contracts.filter(c => 
    c.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    c.company_name?.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="amc-contracts-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">AMC Contracts</h1>
          <p className="text-slate-500 mt-1">Manage Annual Maintenance Contracts with coverage rules</p>
        </div>
        <Button 
          onClick={openCreateModal}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
          data-testid="add-contract-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          New AMC Contract
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Total Contracts</p>
          <p className="text-2xl font-semibold text-slate-900 mt-1">{contracts.length}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Active</p>
          <p className="text-2xl font-semibold text-emerald-600 mt-1">
            {contracts.filter(c => c.status === 'active').length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Expiring Soon</p>
          <p className="text-2xl font-semibold text-amber-600 mt-1">
            {contracts.filter(c => c.status === 'active' && c.days_until_expiry <= 30).length}
          </p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Expired</p>
          <p className="text-2xl font-semibold text-slate-400 mt-1">
            {contracts.filter(c => c.status === 'expired').length}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search contracts..."
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
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="form-select w-full sm:w-36"
        >
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="expired">Expired</option>
          <option value="upcoming">Upcoming</option>
        </select>
      </div>

      {/* Contracts List */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {filteredContracts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full table-modern">
              <thead>
                <tr>
                  <th>Contract</th>
                  <th>Company</th>
                  <th>Type</th>
                  <th>Period</th>
                  <th>Status</th>
                  <th>Coverage</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {filteredContracts.map((contract) => (
                  <tr key={contract.id} data-testid={`contract-row-${contract.id}`}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
                          <Shield className="h-4 w-4 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{contract.name}</p>
                          <p className="text-xs text-slate-500">
                            {contract.usage_count || 0} service records
                          </p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Building2 className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-sm">{contract.company_name}</span>
                      </div>
                    </td>
                    <td>
                      <span className="text-sm capitalize">{contract.amc_type?.replace('_', '-')}</span>
                    </td>
                    <td>
                      <div className="text-sm">
                        <p>{formatDate(contract.start_date)}</p>
                        <p className="text-slate-500">to {formatDate(contract.end_date)}</p>
                      </div>
                    </td>
                    <td>
                      <div className="flex flex-col gap-1">
                        {getStatusBadge(contract.status, contract.days_until_expiry)}
                        {contract.status === 'active' && contract.days_until_expiry > 0 && (
                          <span className="text-xs text-slate-500">{contract.days_until_expiry} days left</span>
                        )}
                      </div>
                    </td>
                    <td>
                      <div className="flex flex-wrap gap-1">
                        {contract.coverage_includes?.onsite_support && (
                          <span className="text-xs bg-emerald-50 text-emerald-600 px-1.5 py-0.5 rounded">Onsite</span>
                        )}
                        {contract.coverage_includes?.remote_support && (
                          <span className="text-xs bg-blue-50 text-blue-600 px-1.5 py-0.5 rounded">Remote</span>
                        )}
                        {contract.coverage_includes?.preventive_maintenance && (
                          <span className="text-xs bg-purple-50 text-purple-600 px-1.5 py-0.5 rounded">PM</span>
                        )}
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
                          <DropdownMenuItem onClick={() => openDetailModal(contract)}>
                            <Eye className="h-4 w-4 mr-2" />
                            View Details
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => openEditModal(contract)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(contract)}
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
            <Shield className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No AMC contracts found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Create your first AMC Contract
            </Button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingContract ? 'Edit AMC Contract' : 'New AMC Contract'}</DialogTitle>
          </DialogHeader>
          
          {/* Tabs */}
          <div className="flex border-b border-slate-200 mt-4">
            {['basic', 'coverage', 'assets', 'entitlements'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
                  activeTab === tab
                    ? 'border-[#0F62FE] text-[#0F62FE]'
                    : 'border-transparent text-slate-500 hover:text-slate-700'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="space-y-6 mt-4">
            {/* Basic Tab */}
            {activeTab === 'basic' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Company *</label>
                    <select
                      value={formData.company_id}
                      onChange={(e) => setFormData({ ...formData, company_id: e.target.value })}
                      className="form-select"
                      disabled={!!editingContract}
                    >
                      <option value="">Select Company</option>
                      {companies.map(c => (
                        <option key={c.id} value={c.id}>{c.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="form-label">AMC Type *</label>
                    <select
                      value={formData.amc_type}
                      onChange={(e) => setFormData({ ...formData, amc_type: e.target.value })}
                      className="form-select"
                    >
                      {AMC_TYPES.map(type => (
                        <option key={type.value} value={type.value}>{type.label}</option>
                      ))}
                    </select>
                    <p className="text-xs text-slate-500 mt-1">
                      {AMC_TYPES.find(t => t.value === formData.amc_type)?.desc}
                    </p>
                  </div>
                </div>
                
                <div>
                  <label className="form-label">Contract Name *</label>
                  <input
                    type="text"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    className="form-input"
                    placeholder="e.g., CoreCare AMC 2025-26"
                  />
                </div>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Start Date *</label>
                    <input
                      type="date"
                      value={formData.start_date}
                      onChange={(e) => setFormData({ ...formData, start_date: e.target.value })}
                      className="form-input"
                    />
                  </div>
                  <div>
                    <label className="form-label">End Date *</label>
                    <input
                      type="date"
                      value={formData.end_date}
                      onChange={(e) => setFormData({ ...formData, end_date: e.target.value })}
                      className="form-input"
                    />
                  </div>
                </div>
                
                <div>
                  <label className="form-label">Internal Notes</label>
                  <textarea
                    value={formData.internal_notes}
                    onChange={(e) => setFormData({ ...formData, internal_notes: e.target.value })}
                    className="form-input"
                    rows={2}
                    placeholder="Internal notes (not visible to customer)"
                  />
                </div>
              </div>
            )}

            {/* Coverage Tab */}
            {activeTab === 'coverage' && (
              <div className="space-y-6">
                {/* What's Included */}
                <div>
                  <h4 className="text-sm font-medium text-slate-900 mb-3">Coverage Includes</h4>
                  <div className="space-y-2">
                    {COVERAGE_OPTIONS.map(option => (
                      <label key={option.key} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100">
                        <input
                          type="checkbox"
                          checked={formData.coverage_includes[option.key] || false}
                          onChange={(e) => setFormData({
                            ...formData,
                            coverage_includes: {
                              ...formData.coverage_includes,
                              [option.key]: e.target.checked
                            }
                          })}
                          className="mt-0.5 rounded border-slate-300"
                        />
                        <div>
                          <p className="text-sm font-medium text-slate-900">{option.label}</p>
                          <p className="text-xs text-slate-500">{option.desc}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Exclusions */}
                <div>
                  <h4 className="text-sm font-medium text-slate-900 mb-3">Explicit Exclusions</h4>
                  <p className="text-xs text-slate-500 mb-3">Check items that are NOT covered under this AMC</p>
                  <div className="grid grid-cols-2 gap-2">
                    {EXCLUSION_OPTIONS.map(option => (
                      <label key={option.key} className="flex items-start gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-red-50">
                        <input
                          type="checkbox"
                          checked={formData.exclusions[option.key] || false}
                          onChange={(e) => setFormData({
                            ...formData,
                            exclusions: {
                              ...formData.exclusions,
                              [option.key]: e.target.checked
                            }
                          })}
                          className="mt-0.5 rounded border-slate-300"
                        />
                        <div>
                          <p className="text-sm font-medium text-slate-900">{option.label}</p>
                          <p className="text-xs text-slate-500">{option.desc}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Assets Tab */}
            {activeTab === 'assets' && (
              <div className="space-y-4">
                <div>
                  <label className="form-label">Asset Mapping Type</label>
                  <div className="space-y-2">
                    {[
                      { value: 'all_company', label: 'All Company Assets', desc: 'Cover all current and future assets' },
                      { value: 'selected_assets', label: 'Selected Assets Only', desc: 'Choose specific devices' },
                      { value: 'device_types', label: 'By Device Types', desc: 'Cover specific types (e.g., Laptops only)' },
                    ].map(option => (
                      <label key={option.value} className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer ${
                        formData.asset_mapping.mapping_type === option.value 
                          ? 'border-[#0F62FE] bg-blue-50' 
                          : 'border-slate-200 hover:bg-slate-50'
                      }`}>
                        <input
                          type="radio"
                          name="mapping_type"
                          value={option.value}
                          checked={formData.asset_mapping.mapping_type === option.value}
                          onChange={(e) => setFormData({
                            ...formData,
                            asset_mapping: {
                              ...formData.asset_mapping,
                              mapping_type: e.target.value
                            }
                          })}
                          className="mt-0.5"
                        />
                        <div>
                          <p className="text-sm font-medium text-slate-900">{option.label}</p>
                          <p className="text-xs text-slate-500">{option.desc}</p>
                        </div>
                      </label>
                    ))}
                  </div>
                </div>

                {/* Asset Selection */}
                {formData.asset_mapping.mapping_type === 'selected_assets' && formData.company_id && (
                  <div>
                    <label className="form-label">Select Assets</label>
                    <TransferList
                      available={companyDevices.filter(d => !formData.asset_mapping.selected_asset_ids.includes(d.id))}
                      selected={companyDevices.filter(d => formData.asset_mapping.selected_asset_ids.includes(d.id))}
                      onSelect={(id) => setFormData({
                        ...formData,
                        asset_mapping: {
                          ...formData.asset_mapping,
                          selected_asset_ids: [...formData.asset_mapping.selected_asset_ids, id]
                        }
                      })}
                      onDeselect={(id) => setFormData({
                        ...formData,
                        asset_mapping: {
                          ...formData.asset_mapping,
                          selected_asset_ids: formData.asset_mapping.selected_asset_ids.filter(i => i !== id)
                        }
                      })}
                    />
                  </div>
                )}

                {/* Device Type Selection */}
                {formData.asset_mapping.mapping_type === 'device_types' && (
                  <div>
                    <label className="form-label">Select Device Types</label>
                    <div className="grid grid-cols-3 gap-2">
                      {deviceTypes.map(type => (
                        <label key={type.id} className={`flex items-center gap-2 p-2 border rounded cursor-pointer ${
                          formData.asset_mapping.selected_device_types.includes(type.name)
                            ? 'border-[#0F62FE] bg-blue-50'
                            : 'border-slate-200 hover:bg-slate-50'
                        }`}>
                          <input
                            type="checkbox"
                            checked={formData.asset_mapping.selected_device_types.includes(type.name)}
                            onChange={(e) => {
                              const types = e.target.checked
                                ? [...formData.asset_mapping.selected_device_types, type.name]
                                : formData.asset_mapping.selected_device_types.filter(t => t !== type.name);
                              setFormData({
                                ...formData,
                                asset_mapping: {
                                  ...formData.asset_mapping,
                                  selected_device_types: types
                                }
                              });
                            }}
                            className="rounded border-slate-300"
                          />
                          <span className="text-sm">{type.name}</span>
                        </label>
                      ))}
                    </div>
                  </div>
                )}

                {!formData.company_id && formData.asset_mapping.mapping_type === 'selected_assets' && (
                  <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-lg">
                    Please select a company first to see available assets
                  </p>
                )}
              </div>
            )}

            {/* Entitlements Tab */}
            {activeTab === 'entitlements' && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="form-label">Onsite Visits (per year)</label>
                    <input
                      type="number"
                      value={formData.entitlements.onsite_visits_per_year || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        entitlements: {
                          ...formData.entitlements,
                          onsite_visits_per_year: e.target.value ? parseInt(e.target.value) : null
                        }
                      })}
                      className="form-input"
                      placeholder="Leave empty for unlimited"
                      min="0"
                    />
                    <p className="text-xs text-slate-500 mt-1">Empty = Unlimited visits</p>
                  </div>
                  <div>
                    <label className="form-label">Remote Support</label>
                    <select
                      value={formData.entitlements.remote_support_type}
                      onChange={(e) => setFormData({
                        ...formData,
                        entitlements: {
                          ...formData.entitlements,
                          remote_support_type: e.target.value
                        }
                      })}
                      className="form-select"
                    >
                      <option value="unlimited">Unlimited</option>
                      <option value="count_based">Count-based</option>
                    </select>
                  </div>
                </div>
                
                {formData.entitlements.remote_support_type === 'count_based' && (
                  <div>
                    <label className="form-label">Remote Support Count</label>
                    <input
                      type="number"
                      value={formData.entitlements.remote_support_count || ''}
                      onChange={(e) => setFormData({
                        ...formData,
                        entitlements: {
                          ...formData.entitlements,
                          remote_support_count: e.target.value ? parseInt(e.target.value) : null
                        }
                      })}
                      className="form-input"
                      placeholder="Number of remote support sessions"
                      min="0"
                    />
                  </div>
                )}
                
                <div>
                  <label className="form-label">Preventive Maintenance Frequency</label>
                  <div className="grid grid-cols-3 gap-2">
                    {PM_FREQUENCIES.map(freq => (
                      <label key={freq.value} className={`flex flex-col p-3 border rounded-lg cursor-pointer ${
                        formData.entitlements.preventive_maintenance_frequency === freq.value
                          ? 'border-[#0F62FE] bg-blue-50'
                          : 'border-slate-200 hover:bg-slate-50'
                      }`}>
                        <input
                          type="radio"
                          name="pm_freq"
                          value={freq.value}
                          checked={formData.entitlements.preventive_maintenance_frequency === freq.value}
                          onChange={(e) => setFormData({
                            ...formData,
                            entitlements: {
                              ...formData.entitlements,
                              preventive_maintenance_frequency: e.target.value
                            }
                          })}
                          className="sr-only"
                        />
                        <span className="text-sm font-medium">{freq.label}</span>
                        <span className="text-xs text-slate-500">{freq.desc}</span>
                      </label>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Form Actions */}
            <div className="flex justify-between items-center pt-4 border-t">
              <div className="flex gap-2">
                {activeTab !== 'basic' && (
                  <Button type="button" variant="outline" onClick={() => {
                    const tabs = ['basic', 'coverage', 'assets', 'entitlements'];
                    const idx = tabs.indexOf(activeTab);
                    if (idx > 0) setActiveTab(tabs[idx - 1]);
                  }}>
                    Previous
                  </Button>
                )}
              </div>
              <div className="flex gap-2">
                <Button type="button" variant="outline" onClick={closeModal}>
                  Cancel
                </Button>
                {activeTab !== 'entitlements' ? (
                  <Button type="button" onClick={() => {
                    const tabs = ['basic', 'coverage', 'assets', 'entitlements'];
                    const idx = tabs.indexOf(activeTab);
                    if (idx < tabs.length - 1) setActiveTab(tabs[idx + 1]);
                  }} className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                    Next
                  </Button>
                ) : (
                  <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                    {editingContract ? 'Update Contract' : 'Create Contract'}
                  </Button>
                )}
              </div>
            </div>
          </form>
        </DialogContent>
      </Dialog>

      {/* Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>AMC Contract Details</DialogTitle>
          </DialogHeader>
          {selectedContract && (
            <div className="space-y-6 mt-4">
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-4">
                  <div className="w-14 h-14 bg-blue-50 rounded-xl flex items-center justify-center">
                    <Shield className="h-7 w-7 text-blue-600" />
                  </div>
                  <div>
                    <h3 className="text-xl font-semibold text-slate-900">{selectedContract.name}</h3>
                    <p className="text-slate-500">{selectedContract.company_name}</p>
                  </div>
                </div>
                {getStatusBadge(selectedContract.status, selectedContract.days_until_expiry)}
              </div>

              {/* Key Info */}
              <div className="grid grid-cols-3 gap-4 p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="text-xs text-slate-500">Type</p>
                  <p className="font-medium capitalize">{selectedContract.amc_type?.replace('_', '-')}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Period</p>
                  <p className="font-medium">{formatDate(selectedContract.start_date)} - {formatDate(selectedContract.end_date)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-500">Days Left</p>
                  <p className="font-medium">{selectedContract.days_until_expiry > 0 ? selectedContract.days_until_expiry : 'Expired'}</p>
                </div>
              </div>

              {/* Coverage */}
              <div>
                <h4 className="text-sm font-medium text-slate-900 mb-2">Coverage Includes</h4>
                <div className="flex flex-wrap gap-2">
                  {selectedContract.coverage_includes?.onsite_support && (
                    <span className="px-3 py-1 bg-emerald-50 text-emerald-700 rounded-full text-sm">✓ Onsite Support</span>
                  )}
                  {selectedContract.coverage_includes?.remote_support && (
                    <span className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm">✓ Remote Support</span>
                  )}
                  {selectedContract.coverage_includes?.preventive_maintenance && (
                    <span className="px-3 py-1 bg-purple-50 text-purple-700 rounded-full text-sm">✓ Preventive Maintenance</span>
                  )}
                </div>
              </div>

              {/* Exclusions */}
              <div>
                <h4 className="text-sm font-medium text-slate-900 mb-2">Exclusions</h4>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(selectedContract.exclusions || {}).filter(([_, v]) => v).map(([k]) => (
                    <span key={k} className="px-3 py-1 bg-red-50 text-red-700 rounded-full text-sm">
                      ✗ {k.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                    </span>
                  ))}
                </div>
              </div>

              {/* Covered Assets */}
              <div>
                <h4 className="text-sm font-medium text-slate-900 mb-2">
                  Covered Assets ({selectedContract.covered_assets_count || 0})
                </h4>
                {selectedContract.asset_mapping?.mapping_type === 'all_company' && (
                  <p className="text-sm text-slate-500">All company assets are covered</p>
                )}
                {selectedContract.asset_mapping?.mapping_type === 'device_types' && (
                  <p className="text-sm text-slate-500">
                    Device types: {selectedContract.asset_mapping.selected_device_types?.join(', ') || 'None selected'}
                  </p>
                )}
                {selectedContract.covered_assets?.length > 0 && (
                  <div className="mt-2 max-h-32 overflow-y-auto space-y-1">
                    {selectedContract.covered_assets.slice(0, 10).map(asset => (
                      <div key={asset.id} className="text-sm p-2 bg-slate-50 rounded flex justify-between">
                        <span>{asset.brand} {asset.model}</span>
                        <span className="text-slate-500 font-mono text-xs">{asset.serial_number}</span>
                      </div>
                    ))}
                    {selectedContract.covered_assets.length > 10 && (
                      <p className="text-xs text-slate-500">+{selectedContract.covered_assets.length - 10} more</p>
                    )}
                  </div>
                )}
              </div>

              {/* Usage Stats */}
              {selectedContract.usage_stats && (
                <div>
                  <h4 className="text-sm font-medium text-slate-900 mb-2">Usage This Period</h4>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-2xl font-semibold text-slate-900">{selectedContract.usage_stats.onsite_visits_used}</p>
                      <p className="text-xs text-slate-500">Onsite Visits</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-2xl font-semibold text-slate-900">{selectedContract.usage_stats.remote_support_used}</p>
                      <p className="text-xs text-slate-500">Remote Support</p>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg">
                      <p className="text-2xl font-semibold text-slate-900">{selectedContract.usage_stats.preventive_maintenance_used}</p>
                      <p className="text-xs text-slate-500">PM Visits</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={() => setDetailModalOpen(false)}>
                  Close
                </Button>
                <Button 
                  onClick={() => {
                    setDetailModalOpen(false);
                    openEditModal(selectedContract);
                  }}
                  className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
                >
                  <Edit2 className="h-4 w-4 mr-2" />
                  Edit Contract
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default AMCContracts;
