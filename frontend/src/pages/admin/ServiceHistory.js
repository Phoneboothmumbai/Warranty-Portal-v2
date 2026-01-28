import { useState, useEffect, useCallback, useRef } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, Wrench, MoreVertical, 
  Calendar, FileText, Paperclip, Download, X, Clock,
  ChevronDown, Filter, Laptop, Building2, AlertTriangle,
  CheckCircle2, ExternalLink, Shield, Upload, Check
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';

// Searchable Device Selector Component
const SearchableDeviceSelect = ({ devices, value, onChange, disabled }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');
  const wrapperRef = useRef(null);
  
  const selectedDevice = devices.find(d => d.id === value);
  
  const filteredDevices = devices.filter(d => {
    const searchLower = search.toLowerCase();
    return (
      d.brand?.toLowerCase().includes(searchLower) ||
      d.model?.toLowerCase().includes(searchLower) ||
      d.serial_number?.toLowerCase().includes(searchLower) ||
      d.asset_tag?.toLowerCase().includes(searchLower)
    );
  });

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  return (
    <div ref={wrapperRef} className="relative">
      <button
        type="button"
        onClick={() => !disabled && setIsOpen(!isOpen)}
        disabled={disabled}
        className={`w-full px-3 py-2 border border-slate-200 rounded-lg text-sm text-left flex items-center justify-between ${
          disabled ? 'bg-slate-100 cursor-not-allowed' : 'bg-white cursor-pointer hover:border-slate-300'
        }`}
      >
        <span className={selectedDevice ? 'text-slate-900' : 'text-slate-400'}>
          {selectedDevice 
            ? `${selectedDevice.brand} ${selectedDevice.model} - ${selectedDevice.serial_number}`
            : 'Select Device'
          }
        </span>
        <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>
      
      {isOpen && (
        <div className="absolute z-50 w-full mt-1 bg-white border border-slate-200 rounded-lg shadow-lg max-h-64 overflow-hidden">
          <div className="p-2 border-b border-slate-100">
            <div className="relative">
              <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search by brand, model, serial..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="w-full pl-8 pr-3 py-2 text-sm border border-slate-200 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>
          </div>
          <div className="max-h-48 overflow-y-auto">
            {filteredDevices.length > 0 ? (
              filteredDevices.map(device => (
                <button
                  key={device.id}
                  type="button"
                  onClick={() => {
                    onChange(device.id);
                    setIsOpen(false);
                    setSearch('');
                  }}
                  className={`w-full px-3 py-2 text-left text-sm hover:bg-slate-50 flex items-center justify-between ${
                    device.id === value ? 'bg-blue-50' : ''
                  }`}
                >
                  <div>
                    <p className="font-medium text-slate-900">{device.brand} {device.model}</p>
                    <p className="text-xs text-slate-500">{device.serial_number} {device.asset_tag ? `• ${device.asset_tag}` : ''}</p>
                  </div>
                  {device.id === value && <Check className="h-4 w-4 text-blue-600" />}
                </button>
              ))
            ) : (
              <p className="px-3 py-4 text-sm text-slate-500 text-center">No devices found</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Stage Timeline Component
const STAGE_STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'bg-slate-100 text-slate-500', icon: Clock, dotColor: 'bg-slate-300' },
  in_progress: { label: 'In Progress', color: 'bg-blue-100 text-blue-700', icon: Clock, dotColor: 'bg-blue-500' },
  completed: { label: 'Completed', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2, dotColor: 'bg-emerald-500' },
  skipped: { label: 'Skipped', color: 'bg-slate-100 text-slate-400', icon: X, dotColor: 'bg-slate-300' }
};

const StageTimeline = ({ service, onStageUpdate, disabled }) => {
  const [expandedStage, setExpandedStage] = useState(null);
  const [stageNotes, setStageNotes] = useState('');
  const [updating, setUpdating] = useState(false);
  
  const stages = service.stages || [];
  const sortedStages = [...stages].sort((a, b) => (a.order || 0) - (b.order || 0));
  
  const handleStatusChange = async (stageKey, newStatus) => {
    if (disabled || updating) return;
    setUpdating(true);
    try {
      await onStageUpdate(service.id, stageKey, { 
        status: newStatus,
        notes: stageNotes || undefined
      });
      setStageNotes('');
      setExpandedStage(null);
    } finally {
      setUpdating(false);
    }
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <div className="bg-slate-50 rounded-lg p-4">
      <div className="flex items-center justify-between mb-4">
        <h4 className="font-medium text-slate-900 flex items-center gap-2">
          <Clock className="h-4 w-4" />
          Service Timeline
        </h4>
        <span className="text-xs text-slate-500">
          {sortedStages.filter(s => s.status === 'completed').length} / {sortedStages.length} completed
        </span>
      </div>
      
      <div className="relative">
        {/* Timeline line */}
        <div className="absolute left-4 top-2 bottom-2 w-0.5 bg-slate-200"></div>
        
        <div className="space-y-1">
          {sortedStages.map((stage, index) => {
            const config = STAGE_STATUS_CONFIG[stage.status] || STAGE_STATUS_CONFIG.pending;
            const StatusIcon = config.icon;
            const isExpanded = expandedStage === stage.stage_key;
            const isLast = index === sortedStages.length - 1;
            
            return (
              <div key={stage.id || stage.stage_key} className="relative">
                {/* Timeline dot */}
                <div className={`absolute left-2.5 w-3 h-3 rounded-full ${config.dotColor} ring-2 ring-white z-10`}></div>
                
                <div className={`ml-8 ${!isLast ? 'pb-3' : ''}`}>
                  <button
                    type="button"
                    onClick={() => setExpandedStage(isExpanded ? null : stage.stage_key)}
                    className={`w-full text-left p-2 rounded-lg transition-colors ${
                      isExpanded ? 'bg-white shadow-sm' : 'hover:bg-white/50'
                    }`}
                    disabled={disabled}
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-900">{stage.stage_label}</span>
                        <span className={`px-1.5 py-0.5 rounded text-xs font-medium ${config.color}`}>
                          {config.label}
                        </span>
                        {stage.is_custom && (
                          <span className="px-1.5 py-0.5 rounded text-xs bg-amber-100 text-amber-700">Custom</span>
                        )}
                      </div>
                      <div className="flex items-center gap-2">
                        {stage.completed_at && (
                          <span className="text-xs text-slate-500">{formatDateTime(stage.completed_at)}</span>
                        )}
                        <ChevronDown className={`h-4 w-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-180' : ''}`} />
                      </div>
                    </div>
                  </button>
                  
                  {/* Expanded Stage Details */}
                  {isExpanded && (
                    <div className="mt-2 p-3 bg-white rounded-lg border border-slate-200 space-y-3">
                      {/* Stage info */}
                      <div className="grid grid-cols-2 gap-2 text-xs">
                        {stage.started_at && (
                          <div>
                            <span className="text-slate-500">Started:</span>
                            <span className="ml-1 text-slate-700">{formatDateTime(stage.started_at)}</span>
                          </div>
                        )}
                        {stage.completed_at && (
                          <div>
                            <span className="text-slate-500">Completed:</span>
                            <span className="ml-1 text-slate-700">{formatDateTime(stage.completed_at)}</span>
                          </div>
                        )}
                        {stage.updated_by_name && (
                          <div>
                            <span className="text-slate-500">Updated by:</span>
                            <span className="ml-1 text-slate-700">{stage.updated_by_name}</span>
                          </div>
                        )}
                      </div>
                      
                      {/* Notes */}
                      {stage.notes && (
                        <div className="text-xs">
                          <span className="text-slate-500">Notes:</span>
                          <p className="mt-1 text-slate-700 bg-slate-50 p-2 rounded">{stage.notes}</p>
                        </div>
                      )}
                      
                      {/* Actions */}
                      {!disabled && stage.status !== 'completed' && (
                        <div className="pt-2 border-t border-slate-100 space-y-2">
                          <textarea
                            placeholder="Add notes for this stage..."
                            value={stageNotes}
                            onChange={(e) => setStageNotes(e.target.value)}
                            className="w-full px-2 py-1.5 text-xs border border-slate-200 rounded resize-none"
                            rows={2}
                          />
                          <div className="flex gap-2">
                            {stage.status === 'pending' && (
                              <button
                                onClick={() => handleStatusChange(stage.stage_key, 'in_progress')}
                                disabled={updating}
                                className="px-2 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                              >
                                Start
                              </button>
                            )}
                            {(stage.status === 'pending' || stage.status === 'in_progress') && (
                              <>
                                <button
                                  onClick={() => handleStatusChange(stage.stage_key, 'completed')}
                                  disabled={updating}
                                  className="px-2 py-1 text-xs bg-emerald-500 text-white rounded hover:bg-emerald-600 disabled:opacity-50"
                                >
                                  Complete
                                </button>
                                <button
                                  onClick={() => handleStatusChange(stage.stage_key, 'skipped')}
                                  disabled={updating}
                                  className="px-2 py-1 text-xs bg-slate-200 text-slate-600 rounded hover:bg-slate-300 disabled:opacity-50"
                                >
                                  Skip
                                </button>
                              </>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Service Category Labels & Colors
const SERVICE_CATEGORY_CONFIG = {
  internal_service: { label: 'Internal Service', color: 'bg-blue-100 text-blue-700', icon: Wrench },
  oem_warranty_service: { label: 'OEM Warranty', color: 'bg-purple-100 text-purple-700', icon: Shield },
  paid_third_party_service: { label: 'Third-Party', color: 'bg-amber-100 text-amber-700', icon: Building2 },
  inspection_diagnosis: { label: 'Inspection', color: 'bg-slate-100 text-slate-700', icon: Search }
};

const STATUS_CONFIG = {
  open: { label: 'Open', color: 'bg-blue-100 text-blue-700' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700' },
  on_hold: { label: 'On Hold', color: 'bg-orange-100 text-orange-700' },
  completed: { label: 'Completed', color: 'bg-emerald-100 text-emerald-700' },
  closed: { label: 'Closed', color: 'bg-slate-100 text-slate-700' }
};

const OEM_STATUS_CONFIG = {
  reported_to_oem: { label: 'Reported to OEM', color: 'bg-blue-100 text-blue-700' },
  oem_accepted: { label: 'OEM Accepted', color: 'bg-cyan-100 text-cyan-700' },
  engineer_assigned: { label: 'Engineer Assigned', color: 'bg-indigo-100 text-indigo-700' },
  parts_dispatched: { label: 'Parts Dispatched', color: 'bg-violet-100 text-violet-700' },
  visit_scheduled: { label: 'Visit Scheduled', color: 'bg-purple-100 text-purple-700' },
  resolved_by_oem: { label: 'Resolved by OEM', color: 'bg-emerald-100 text-emerald-700' },
  closed_by_oem: { label: 'Closed by OEM', color: 'bg-slate-100 text-slate-700' }
};

const ServiceHistory = () => {
  const { token } = useAuth();
  const [services, setServices] = useState([]);
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDevice, setFilterDevice] = useState('');
  const [filterCategory, setFilterCategory] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [editingService, setEditingService] = useState(null);
  const [uploading, setUploading] = useState(false);
  
  // Service options from backend
  const [serviceOptions, setServiceOptions] = useState(null);
  const [serviceTypes, setServiceTypes] = useState([]);
  
  // Form data
  const [formData, setFormData] = useState({
    device_id: '',
    service_date: new Date().toISOString().split('T')[0],
    service_type: '',
    problem_reported: '',
    action_taken: '',
    status: 'open',
    technician_name: '',
    notes: '',
    // NEW: Service Classification
    service_category: 'internal_service',
    service_responsibility: 'our_team',
    service_role: 'provider',
    // NEW: Billing
    billing_impact: 'not_billable',
    // NEW: OEM Details
    oem_details: null
  });

  // OEM Form Data (nested)
  const [oemFormData, setOemFormData] = useState({
    oem_name: '',
    oem_service_tag: '',
    oem_warranty_type: '',
    oem_case_number: '',
    case_raised_date: new Date().toISOString().split('T')[0],
    case_raised_via: 'oem_portal',
    oem_priority: 'Standard',
    oem_case_status: 'reported_to_oem',
    oem_engineer_name: '',
    oem_engineer_phone: '',
    oem_visit_date: '',
    oem_remarks: ''
  });

  // Service Outcome (for closure)
  const [outcomeData, setOutcomeData] = useState({
    resolution_summary: '',
    part_replaced: '',
    cost_incurred: 0,
    closed_by: ''
  });

  const fetchServiceOptions = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/admin/services/options`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setServiceOptions(response.data);
    } catch (error) {
      console.error('Failed to fetch service options');
    }
  }, [token]);

  const fetchMasterData = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/masters/public`, { 
        params: { master_type: 'service_type' } 
      });
      setServiceTypes(response.data);
    } catch (error) {
      console.error('Failed to fetch service types');
    }
  }, []);

  const fetchData = useCallback(async () => {
    try {
      const params = {};
      if (filterDevice) params.device_id = filterDevice;
      if (filterCategory) params.service_category = filterCategory;
      if (filterStatus) params.status = filterStatus;
      
      const [servicesRes, devicesRes] = await Promise.all([
        axios.get(`${API}/admin/services`, {
          params,
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/devices`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setServices(servicesRes.data);
      setDevices(devicesRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token, filterDevice, filterCategory, filterStatus]);

  useEffect(() => {
    fetchData();
    fetchMasterData();
    fetchServiceOptions();
  }, [fetchData, fetchMasterData, fetchServiceOptions]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.device_id || !formData.action_taken) {
      toast.error('Please fill required fields');
      return;
    }
    
    // Prepare submission data
    let submitData = { ...formData };
    
    // If OEM category, include OEM details
    if (formData.service_category === 'oem_warranty_service') {
      if (!oemFormData.oem_name || !oemFormData.oem_case_number || !oemFormData.oem_warranty_type) {
        toast.error('OEM Name, Case Number, and Warranty Type are required for OEM services');
        return;
      }
      submitData.oem_details = oemFormData;
    }
    
    try {
      if (editingService) {
        // Include outcome if closing
        if (submitData.status === 'closed' || 
            (submitData.service_category === 'oem_warranty_service' && 
             oemFormData.oem_case_status === 'closed_by_oem')) {
          if (!outcomeData.resolution_summary) {
            toast.error('Resolution summary is required for closure');
            return;
          }
          submitData.service_outcome = {
            ...outcomeData,
            closure_date: new Date().toISOString().split('T')[0]
          };
        }
        
        await axios.put(`${API}/admin/services/${editingService.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Service record updated');
      } else {
        await axios.post(`${API}/admin/services`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Service record created');
      }
      closeModal();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Delete this service record?')) return;
    try {
      await axios.delete(`${API}/admin/services/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Service record deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const handleFileUpload = async (serviceId, file) => {
    setUploading(true);
    const formDataUpload = new FormData();
    formDataUpload.append('file', file);
    
    try {
      await axios.post(`${API}/admin/services/${serviceId}/attachments`, formDataUpload, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.success('Attachment uploaded');
      fetchData();
      if (selectedService?.id === serviceId) {
        const res = await axios.get(`${API}/admin/services/${serviceId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSelectedService(res.data);
      }
    } catch (error) {
      toast.error('Failed to upload');
    } finally {
      setUploading(false);
    }
  };

  const openCreateModal = (deviceId = '') => {
    setEditingService(null);
    setFormData({
      device_id: deviceId || filterDevice || '',
      service_date: new Date().toISOString().split('T')[0],
      service_type: serviceTypes[0]?.name || 'Repair',
      problem_reported: '',
      action_taken: '',
      status: 'open',
      technician_name: '',
      notes: '',
      service_category: 'internal_service',
      service_responsibility: 'our_team',
      service_role: 'provider',
      billing_impact: 'not_billable',
      oem_details: null
    });
    setOemFormData({
      oem_name: '',
      oem_service_tag: '',
      oem_warranty_type: '',
      oem_case_number: '',
      case_raised_date: new Date().toISOString().split('T')[0],
      case_raised_via: 'oem_portal',
      oem_priority: 'Standard',
      oem_case_status: 'reported_to_oem',
      oem_engineer_name: '',
      oem_engineer_phone: '',
      oem_visit_date: '',
      oem_remarks: ''
    });
    setOutcomeData({ resolution_summary: '', part_replaced: '', cost_incurred: 0, closed_by: '' });
    setModalOpen(true);
  };

  const openEditModal = (service) => {
    setEditingService(service);
    setFormData({
      device_id: service.device_id,
      service_date: service.service_date,
      service_type: service.service_type,
      problem_reported: service.problem_reported || '',
      action_taken: service.action_taken,
      status: service.status || 'open',
      technician_name: service.technician_name || '',
      notes: service.notes || '',
      service_category: service.service_category || 'internal_service',
      service_responsibility: service.service_responsibility || 'our_team',
      service_role: service.service_role || 'provider',
      billing_impact: service.billing_impact || 'not_billable',
      oem_details: service.oem_details
    });
    if (service.oem_details) {
      setOemFormData(service.oem_details);
    }
    if (service.service_outcome) {
      setOutcomeData(service.service_outcome);
    }
    setModalOpen(true);
  };

  const openDetailModal = async (service) => {
    try {
      const res = await axios.get(`${API}/admin/services/${service.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setSelectedService(res.data);
      setDetailModalOpen(true);
    } catch (error) {
      toast.error('Failed to load service details');
    }
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingService(null);
  };

  const getDevice = (deviceId) => devices.find(d => d.id === deviceId);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const filteredServices = services.filter(s => {
    const device = getDevice(s.device_id);
    const searchLower = searchQuery.toLowerCase();
    return (
      s.action_taken?.toLowerCase().includes(searchLower) ||
      s.problem_reported?.toLowerCase().includes(searchLower) ||
      s.oem_details?.oem_case_number?.toLowerCase().includes(searchLower) ||
      device?.serial_number?.toLowerCase().includes(searchLower) ||
      device?.brand?.toLowerCase().includes(searchLower)
    );
  });

  // Stats
  const stats = {
    total: services.length,
    internal: services.filter(s => s.service_category === 'internal_service').length,
    oem: services.filter(s => s.service_category === 'oem_warranty_service').length,
    open: services.filter(s => !s.is_closed).length
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="service-history-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Service Records</h1>
          <p className="text-slate-500 mt-1">Track repairs, maintenance, and OEM warranty services</p>
        </div>
        <Button onClick={() => openCreateModal()} data-testid="add-service-btn">
          <Plus className="h-4 w-4 mr-2" />
          Add Service Record
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Total Records</p>
          <p className="text-2xl font-semibold text-slate-900">{stats.total}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Internal Services</p>
          <p className="text-2xl font-semibold text-blue-600">{stats.internal}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">OEM Warranty</p>
          <p className="text-2xl font-semibold text-purple-600">{stats.oem}</p>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <p className="text-sm text-slate-500">Open Cases</p>
          <p className="text-2xl font-semibold text-amber-600">{stats.open}</p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-3">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by action, problem, OEM case..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg text-sm"
          />
        </div>
        <select
          value={filterCategory}
          onChange={(e) => setFilterCategory(e.target.value)}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
        >
          <option value="">All Categories</option>
          <option value="internal_service">Internal Service</option>
          <option value="oem_warranty_service">OEM Warranty</option>
          <option value="paid_third_party_service">Third-Party</option>
          <option value="inspection_diagnosis">Inspection</option>
        </select>
        <select
          value={filterStatus}
          onChange={(e) => setFilterStatus(e.target.value)}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white"
        >
          <option value="">All Status</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="completed">Completed</option>
          <option value="closed">Closed</option>
        </select>
        <select
          value={filterDevice}
          onChange={(e) => setFilterDevice(e.target.value)}
          className="px-3 py-2 border border-slate-200 rounded-lg text-sm bg-white max-w-xs"
        >
          <option value="">All Devices</option>
          {devices.slice(0, 50).map(d => (
            <option key={d.id} value={d.id}>{d.brand} {d.model} - {d.serial_number}</option>
          ))}
        </select>
      </div>

      {/* Service Records List */}
      <div className="space-y-3">
        {filteredServices.length > 0 ? (
          filteredServices.map(service => {
            const device = getDevice(service.device_id);
            const categoryConfig = SERVICE_CATEGORY_CONFIG[service.service_category] || SERVICE_CATEGORY_CONFIG.internal_service;
            const statusConfig = service.service_category === 'oem_warranty_service' && service.oem_details?.oem_case_status
              ? OEM_STATUS_CONFIG[service.oem_details.oem_case_status] || STATUS_CONFIG[service.status]
              : STATUS_CONFIG[service.status] || STATUS_CONFIG.open;
            const CategoryIcon = categoryConfig.icon;
            
            return (
              <div 
                key={service.id}
                className={`bg-white rounded-xl border p-4 hover:shadow-sm transition-all cursor-pointer ${
                  service.is_closed ? 'border-slate-100 opacity-75' : 'border-slate-200'
                }`}
                onClick={() => openDetailModal(service)}
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4">
                    <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${categoryConfig.color}`}>
                      <CategoryIcon className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${categoryConfig.color}`}>
                          {categoryConfig.label}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${statusConfig.color}`}>
                          {statusConfig.label}
                        </span>
                        {service.is_closed && (
                          <span className="px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-500">
                            <CheckCircle2 className="h-3 w-3 inline mr-1" />
                            Closed
                          </span>
                        )}
                      </div>
                      <p className="font-medium text-slate-900">{service.service_type}</p>
                      <p className="text-sm text-slate-500 line-clamp-1">{service.action_taken}</p>
                      {device && (
                        <p className="text-xs text-slate-400 mt-1 flex items-center gap-1">
                          <Laptop className="h-3 w-3" />
                          {device.brand} {device.model} • {device.serial_number}
                        </p>
                      )}
                      {service.oem_details && (
                        <p className="text-xs text-purple-600 mt-1 flex items-center gap-1">
                          <Shield className="h-3 w-3" />
                          {service.oem_details.oem_name} • Case: {service.oem_details.oem_case_number}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="text-right">
                      <p className="text-sm font-medium text-slate-600">{formatDate(service.service_date)}</p>
                      {service.technician_name && (
                        <p className="text-xs text-slate-400">Tech: {service.technician_name}</p>
                      )}
                      {service.attachments?.length > 0 && (
                        <p className="text-xs text-slate-400 flex items-center justify-end gap-1 mt-1">
                          <Paperclip className="h-3 w-3" />
                          {service.attachments.length} files
                        </p>
                      )}
                    </div>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                        <Button variant="ghost" size="icon" className="h-8 w-8">
                          <MoreVertical className="h-4 w-4" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openEditModal(service); }}>
                          <Edit2 className="h-4 w-4 mr-2" /> Edit
                        </DropdownMenuItem>
                        <DropdownMenuItem 
                          onClick={(e) => { e.stopPropagation(); handleDelete(service.id); }}
                          className="text-red-600"
                        >
                          <Trash2 className="h-4 w-4 mr-2" /> Delete
                        </DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-16 bg-white rounded-xl border border-slate-100">
            <Wrench className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No service records found</p>
            <Button onClick={() => openCreateModal()} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add first service record
            </Button>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingService ? 'Edit Service Record' : 'Add Service Record'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-6 mt-4">
            {/* Service Classification */}
            <div className="bg-slate-50 rounded-lg p-4 space-y-4">
              <h3 className="font-medium text-slate-900">Service Classification</h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Service Category *</label>
                  <select
                    value={formData.service_category}
                    onChange={(e) => {
                      const category = e.target.value;
                      setFormData({ 
                        ...formData, 
                        service_category: category,
                        // Auto-set for OEM
                        service_responsibility: category === 'oem_warranty_service' ? 'oem' : formData.service_responsibility,
                        service_role: category === 'oem_warranty_service' ? 'coordinator_facilitator' : formData.service_role,
                        billing_impact: category === 'oem_warranty_service' ? 'warranty_covered' : formData.billing_impact
                      });
                    }}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    disabled={editingService?.is_closed}
                  >
                    {serviceOptions?.service_categories?.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    )) || (
                      <>
                        <option value="internal_service">Internal Service (Provided by Us)</option>
                        <option value="oem_warranty_service">OEM Warranty Service (Facilitated)</option>
                        <option value="paid_third_party_service">Paid Third-Party Service</option>
                        <option value="inspection_diagnosis">Inspection / Diagnosis Only</option>
                      </>
                    )}
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Status</label>
                  <select
                    value={formData.status}
                    onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    disabled={editingService?.is_closed}
                  >
                    {serviceOptions?.service_statuses?.map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    )) || (
                      <>
                        <option value="open">Open</option>
                        <option value="in_progress">In Progress</option>
                        <option value="on_hold">On Hold</option>
                        <option value="completed">Completed</option>
                        <option value="closed">Closed</option>
                      </>
                    )}
                  </select>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Service Responsibility</label>
                  <select
                    value={formData.service_responsibility}
                    onChange={(e) => setFormData({ ...formData, service_responsibility: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    disabled={formData.service_category === 'oem_warranty_service' || editingService?.is_closed}
                  >
                    <option value="our_team">Our Team</option>
                    <option value="oem">OEM</option>
                    <option value="partner_vendor">Partner / Vendor</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Service Role</label>
                  <select
                    value={formData.service_role}
                    onChange={(e) => setFormData({ ...formData, service_role: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    disabled={formData.service_category === 'oem_warranty_service' || editingService?.is_closed}
                  >
                    <option value="provider">Provider</option>
                    <option value="coordinator_facilitator">Coordinator / Facilitator</option>
                    <option value="observer">Observer</option>
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Billing Impact</label>
                <select
                  value={formData.billing_impact}
                  onChange={(e) => setFormData({ ...formData, billing_impact: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  disabled={formData.service_category === 'oem_warranty_service' || editingService?.is_closed}
                >
                  <option value="not_billable">Not Billable</option>
                  <option value="warranty_covered">Warranty Covered</option>
                  <option value="chargeable">Chargeable</option>
                </select>
              </div>
              {formData.service_category === 'oem_warranty_service' && (
                <div className="bg-purple-50 rounded-lg p-3 text-sm text-purple-700 flex items-start gap-2">
                  <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                  <span>OEM Warranty Service: Responsibility, Role, and Billing are auto-locked. This record will NOT count toward AMC quota.</span>
                </div>
              )}
            </div>

            {/* Basic Service Info */}
            <div className="space-y-4">
              <h3 className="font-medium text-slate-900">Service Details</h3>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Device *</label>
                <SearchableDeviceSelect
                  devices={devices}
                  value={formData.device_id}
                  onChange={(deviceId) => setFormData({ ...formData, device_id: deviceId })}
                  disabled={!!editingService}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Service Date *</label>
                  <input
                    type="date"
                    value={formData.service_date}
                    onChange={(e) => setFormData({ ...formData, service_date: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    required
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Service Type *</label>
                  <select
                    value={formData.service_type}
                    onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    required
                  >
                    <option value="">Select Type</option>
                    {serviceTypes.map(t => (
                      <option key={t.id} value={t.name}>{t.name}</option>
                    ))}
                  </select>
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Problem Reported</label>
                <textarea
                  value={formData.problem_reported}
                  onChange={(e) => setFormData({ ...formData, problem_reported: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  rows={2}
                  placeholder="Describe the issue reported..."
                />
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Action Taken *</label>
                <textarea
                  value={formData.action_taken}
                  onChange={(e) => setFormData({ ...formData, action_taken: e.target.value })}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  rows={2}
                  placeholder="Describe what was done..."
                  required
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Technician Name</label>
                  <input
                    type="text"
                    value={formData.technician_name}
                    onChange={(e) => setFormData({ ...formData, technician_name: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    placeholder="Who performed the service?"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Notes</label>
                  <input
                    type="text"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    placeholder="Additional notes..."
                  />
                </div>
              </div>
            </div>

            {/* OEM Service Details - Conditional */}
            {formData.service_category === 'oem_warranty_service' && (
              <div className="bg-purple-50 rounded-lg p-4 space-y-4">
                <h3 className="font-medium text-purple-900 flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  OEM Service Details (Required)
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">OEM Name *</label>
                    <select
                      value={oemFormData.oem_name}
                      onChange={(e) => setOemFormData({ ...oemFormData, oem_name: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      required
                    >
                      <option value="">Select OEM</option>
                      {(serviceOptions?.oem_names || ['Dell', 'HP', 'Lenovo', 'Asus', 'Acer', 'Apple', 'Microsoft', 'Samsung', 'Other']).map(name => (
                        <option key={name} value={name}>{name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">OEM Warranty Type *</label>
                    <select
                      value={oemFormData.oem_warranty_type}
                      onChange={(e) => setOemFormData({ ...oemFormData, oem_warranty_type: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      required
                    >
                      <option value="">Select Type</option>
                      {(serviceOptions?.oem_warranty_types || ['ADP', 'NBD', 'Standard', 'ProSupport', 'Premium', 'Extended', 'Other']).map(type => (
                        <option key={type} value={type}>{type}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">OEM Case/SR Number *</label>
                    <input
                      type="text"
                      value={oemFormData.oem_case_number}
                      onChange={(e) => setOemFormData({ ...oemFormData, oem_case_number: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      placeholder="e.g., SR123456789"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">OEM Service Tag</label>
                    <input
                      type="text"
                      value={oemFormData.oem_service_tag}
                      onChange={(e) => setOemFormData({ ...oemFormData, oem_service_tag: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      placeholder="Device service tag"
                    />
                  </div>
                </div>
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Case Raised Date *</label>
                    <input
                      type="date"
                      value={oemFormData.case_raised_date}
                      onChange={(e) => setOemFormData({ ...oemFormData, case_raised_date: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      required
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Raised Via *</label>
                    <select
                      value={oemFormData.case_raised_via}
                      onChange={(e) => setOemFormData({ ...oemFormData, case_raised_via: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      required
                    >
                      {(serviceOptions?.oem_case_raised_via || [
                        {value: 'phone', label: 'Phone'},
                        {value: 'oem_portal', label: 'OEM Portal'},
                        {value: 'email', label: 'Email'},
                        {value: 'chat', label: 'Chat'}
                      ]).map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">OEM Priority</label>
                    <select
                      value={oemFormData.oem_priority}
                      onChange={(e) => setOemFormData({ ...oemFormData, oem_priority: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    >
                      {(serviceOptions?.oem_priority || [
                        {value: 'NBD', label: 'Next Business Day'},
                        {value: 'Standard', label: 'Standard'},
                        {value: 'Deferred', label: 'Deferred'},
                        {value: 'Critical', label: 'Critical/Urgent'}
                      ]).map(opt => (
                        <option key={opt.value} value={opt.value}>{opt.label}</option>
                      ))}
                    </select>
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">OEM Case Status</label>
                  <select
                    value={oemFormData.oem_case_status}
                    onChange={(e) => setOemFormData({ ...oemFormData, oem_case_status: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  >
                    {(serviceOptions?.oem_case_statuses || [
                      {value: 'reported_to_oem', label: 'Reported to OEM'},
                      {value: 'oem_accepted', label: 'OEM Accepted'},
                      {value: 'engineer_assigned', label: 'Engineer Assigned'},
                      {value: 'parts_dispatched', label: 'Parts Dispatched'},
                      {value: 'visit_scheduled', label: 'Visit Scheduled'},
                      {value: 'resolved_by_oem', label: 'Resolved by OEM'},
                      {value: 'closed_by_oem', label: 'Closed by OEM'}
                    ]).map(opt => (
                      <option key={opt.value} value={opt.value}>{opt.label}</option>
                    ))}
                  </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">OEM Engineer Name</label>
                    <input
                      type="text"
                      value={oemFormData.oem_engineer_name}
                      onChange={(e) => setOemFormData({ ...oemFormData, oem_engineer_name: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      placeholder="Engineer assigned by OEM"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">OEM Visit Date</label>
                    <input
                      type="date"
                      value={oemFormData.oem_visit_date}
                      onChange={(e) => setOemFormData({ ...oemFormData, oem_visit_date: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">OEM Remarks</label>
                  <textarea
                    value={oemFormData.oem_remarks}
                    onChange={(e) => setOemFormData({ ...oemFormData, oem_remarks: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    rows={2}
                    placeholder="Additional remarks about OEM service..."
                  />
                </div>
              </div>
            )}

            {/* Service Outcome - For Closure */}
            {(formData.status === 'closed' || (formData.service_category === 'oem_warranty_service' && oemFormData.oem_case_status === 'closed_by_oem')) && (
              <div className="bg-emerald-50 rounded-lg p-4 space-y-4">
                <h3 className="font-medium text-emerald-900 flex items-center gap-2">
                  <CheckCircle2 className="h-5 w-5" />
                  Service Outcome (Required for Closure)
                </h3>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Resolution Summary *</label>
                  <textarea
                    value={outcomeData.resolution_summary}
                    onChange={(e) => setOutcomeData({ ...outcomeData, resolution_summary: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    rows={2}
                    placeholder="Describe how the issue was resolved..."
                    required
                  />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Part Replaced</label>
                    <input
                      type="text"
                      value={outcomeData.part_replaced}
                      onChange={(e) => setOutcomeData({ ...outcomeData, part_replaced: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      placeholder="e.g., Motherboard, Display"
                    />
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Cost Incurred (₹)</label>
                    <input
                      type="number"
                      value={outcomeData.cost_incurred}
                      onChange={(e) => setOutcomeData({ ...outcomeData, cost_incurred: parseFloat(e.target.value) || 0 })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      placeholder="0"
                    />
                  </div>
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Closed By *</label>
                  <select
                    value={outcomeData.closed_by}
                    onChange={(e) => setOutcomeData({ ...outcomeData, closed_by: e.target.value })}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                    required
                  >
                    <option value="">Select</option>
                    <option value="OEM">OEM</option>
                    <option value="Our Team">Our Team</option>
                    <option value="Customer">Customer</option>
                    <option value="Auto-Resolved">Auto-Resolved</option>
                  </select>
                </div>
              </div>
            )}

            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" disabled={editingService?.is_closed}>
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
            <DialogTitle>Service Record Details</DialogTitle>
          </DialogHeader>
          {selectedService && (
            <div className="space-y-6 mt-4">
              {/* Classification Badge */}
              <div className="flex items-center gap-2 flex-wrap">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${SERVICE_CATEGORY_CONFIG[selectedService.service_category]?.color || 'bg-slate-100'}`}>
                  {SERVICE_CATEGORY_CONFIG[selectedService.service_category]?.label || 'Internal Service'}
                </span>
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${STATUS_CONFIG[selectedService.status]?.color || 'bg-slate-100'}`}>
                  {STATUS_CONFIG[selectedService.status]?.label || selectedService.status}
                </span>
                {selectedService.is_closed && (
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-emerald-100 text-emerald-700">
                    <CheckCircle2 className="h-3 w-3 inline mr-1" />
                    Closed
                  </span>
                )}
              </div>

              {/* Device Info */}
              {(() => {
                const device = getDevice(selectedService.device_id);
                return device && (
                  <div className="bg-slate-50 rounded-lg p-4">
                    <h4 className="text-sm font-medium text-slate-500 mb-2">Device</h4>
                    <p className="font-medium text-slate-900">{device.brand} {device.model}</p>
                    <p className="text-sm text-slate-500">{device.serial_number}</p>
                  </div>
                );
              })()}

              {/* Service Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-medium text-slate-500">Service Date</h4>
                  <p className="text-slate-900">{formatDate(selectedService.service_date)}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-500">Service Type</h4>
                  <p className="text-slate-900">{selectedService.service_type}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-500">Responsibility</h4>
                  <p className="text-slate-900 capitalize">{selectedService.service_responsibility?.replace('_', ' ')}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-500">Role</h4>
                  <p className="text-slate-900 capitalize">{selectedService.service_role?.replace('_', ' ')}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-500">Billing Impact</h4>
                  <p className="text-slate-900 capitalize">{selectedService.billing_impact?.replace('_', ' ')}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-slate-500">Counts Toward AMC</h4>
                  <p className="text-slate-900">{selectedService.counts_toward_amc ? 'Yes' : 'No'}</p>
                </div>
              </div>

              {/* Problem & Action */}
              {selectedService.problem_reported && (
                <div>
                  <h4 className="text-sm font-medium text-slate-500 mb-1">Problem Reported</h4>
                  <p className="text-slate-900 bg-slate-50 p-3 rounded-lg">{selectedService.problem_reported}</p>
                </div>
              )}
              <div>
                <h4 className="text-sm font-medium text-slate-500 mb-1">Action Taken</h4>
                <p className="text-slate-900 bg-slate-50 p-3 rounded-lg">{selectedService.action_taken}</p>
              </div>

              {/* Stage Timeline */}
              {selectedService.stages && selectedService.stages.length > 0 && (
                <StageTimeline 
                  service={selectedService} 
                  onStageUpdate={handleStageUpdate}
                  disabled={selectedService.is_closed}
                />
              )}

              {/* OEM Details */}
              {selectedService.oem_details && (
                <div className="bg-purple-50 rounded-lg p-4 space-y-3">
                  <h4 className="font-medium text-purple-900 flex items-center gap-2">
                    <Shield className="h-4 w-4" />
                    OEM Service Details
                  </h4>
                  <div className="grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <span className="text-slate-500">OEM:</span>
                      <span className="ml-2 text-slate-900 font-medium">{selectedService.oem_details.oem_name}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Warranty Type:</span>
                      <span className="ml-2 text-slate-900 font-medium">{selectedService.oem_details.oem_warranty_type}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Case Number:</span>
                      <span className="ml-2 text-slate-900 font-medium">{selectedService.oem_details.oem_case_number}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Case Status:</span>
                      <span className={`ml-2 px-2 py-0.5 rounded-full text-xs font-medium ${OEM_STATUS_CONFIG[selectedService.oem_details.oem_case_status]?.color || 'bg-slate-100'}`}>
                        {OEM_STATUS_CONFIG[selectedService.oem_details.oem_case_status]?.label || selectedService.oem_details.oem_case_status}
                      </span>
                    </div>
                    <div>
                      <span className="text-slate-500">Raised Date:</span>
                      <span className="ml-2 text-slate-900">{formatDate(selectedService.oem_details.case_raised_date)}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Raised Via:</span>
                      <span className="ml-2 text-slate-900 capitalize">{selectedService.oem_details.case_raised_via?.replace('_', ' ')}</span>
                    </div>
                    {selectedService.oem_details.oem_engineer_name && (
                      <div>
                        <span className="text-slate-500">OEM Engineer:</span>
                        <span className="ml-2 text-slate-900">{selectedService.oem_details.oem_engineer_name}</span>
                      </div>
                    )}
                    {selectedService.oem_details.oem_visit_date && (
                      <div>
                        <span className="text-slate-500">Visit Date:</span>
                        <span className="ml-2 text-slate-900">{formatDate(selectedService.oem_details.oem_visit_date)}</span>
                      </div>
                    )}
                  </div>
                  {selectedService.oem_details.oem_remarks && (
                    <div>
                      <span className="text-slate-500 text-sm">Remarks:</span>
                      <p className="text-slate-900 text-sm mt-1">{selectedService.oem_details.oem_remarks}</p>
                    </div>
                  )}
                </div>
              )}

              {/* Service Outcome */}
              {selectedService.service_outcome && (
                <div className="bg-emerald-50 rounded-lg p-4 space-y-3">
                  <h4 className="font-medium text-emerald-900 flex items-center gap-2">
                    <CheckCircle2 className="h-4 w-4" />
                    Service Outcome
                  </h4>
                  <div>
                    <span className="text-slate-500 text-sm">Resolution:</span>
                    <p className="text-slate-900 text-sm mt-1">{selectedService.service_outcome.resolution_summary}</p>
                  </div>
                  <div className="grid grid-cols-3 gap-3 text-sm">
                    {selectedService.service_outcome.part_replaced && (
                      <div>
                        <span className="text-slate-500">Part Replaced:</span>
                        <span className="ml-2 text-slate-900">{selectedService.service_outcome.part_replaced}</span>
                      </div>
                    )}
                    <div>
                      <span className="text-slate-500">Cost:</span>
                      <span className="ml-2 text-slate-900">₹{selectedService.service_outcome.cost_incurred?.toLocaleString('en-IN')}</span>
                    </div>
                    <div>
                      <span className="text-slate-500">Closed By:</span>
                      <span className="ml-2 text-slate-900">{selectedService.service_outcome.closed_by}</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Attachments */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-slate-900 flex items-center gap-2">
                    <Paperclip className="h-4 w-4" />
                    Attachments ({selectedService.attachments?.length || 0})
                  </h4>
                  {!selectedService.is_closed && (
                    <label className="cursor-pointer">
                      <input
                        type="file"
                        className="hidden"
                        onChange={(e) => e.target.files?.[0] && handleFileUpload(selectedService.id, e.target.files[0])}
                        disabled={uploading}
                      />
                      <Button variant="outline" size="sm" asChild disabled={uploading}>
                        <span>
                          <Upload className="h-4 w-4 mr-1" />
                          {uploading ? 'Uploading...' : 'Upload'}
                        </span>
                      </Button>
                    </label>
                  )}
                </div>
                {selectedService.attachments?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedService.attachments.map((att, i) => (
                      <div key={i} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                        <div className="flex items-center gap-2">
                          <FileText className="h-4 w-4 text-slate-400" />
                          <span className="text-sm text-slate-700">{att.filename}</span>
                        </div>
                        <a 
                          href={att.url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-blue-600 hover:text-blue-700"
                        >
                          <Download className="h-4 w-4" />
                        </a>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-500 text-center py-4 bg-slate-50 rounded-lg">
                    No attachments
                  </p>
                )}
                {selectedService.service_category === 'oem_warranty_service' && !selectedService.is_closed && selectedService.attachments?.length === 0 && (
                  <div className="mt-2 p-3 bg-amber-50 rounded-lg text-sm text-amber-700 flex items-start gap-2">
                    <AlertTriangle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <span>OEM service records require at least one attachment (proof) before closure for audit and dispute protection.</span>
                  </div>
                )}
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <Button variant="outline" onClick={() => setDetailModalOpen(false)}>
                  Close
                </Button>
                {!selectedService.is_closed && (
                  <Button onClick={() => { setDetailModalOpen(false); openEditModal(selectedService); }}>
                    <Edit2 className="h-4 w-4 mr-2" />
                    Edit
                  </Button>
                )}
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default ServiceHistory;
