import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, Wrench, MoreVertical, 
  Calendar, FileText, Paperclip, Download, X, Clock,
  ChevronDown, Filter, Laptop
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const ServiceHistory = () => {
  const { token } = useAuth();
  const [services, setServices] = useState([]);
  const [devices, setDevices] = useState([]);
  const [amcContracts, setAmcContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDevice, setFilterDevice] = useState('');
  const [filterType, setFilterType] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [selectedService, setSelectedService] = useState(null);
  const [editingService, setEditingService] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [deviceAmcCoverage, setDeviceAmcCoverage] = useState(null);
  
  // Master data
  const [serviceTypes, setServiceTypes] = useState([]);
  
  const [formData, setFormData] = useState({
    device_id: '',
    service_date: new Date().toISOString().split('T')[0],
    service_type: '',
    problem_reported: '',
    action_taken: '',
    warranty_impact: 'not_applicable',
    technician_name: '',
    ticket_id: '',
    notes: '',
    // AMC fields
    amc_contract_id: '',
    billing_type: 'covered',
    chargeable_reason: ''
  });

  useEffect(() => {
    fetchData();
    fetchMasterData();
  }, [filterDevice, filterType]);

  const fetchMasterData = async () => {
    try {
      const response = await axios.get(`${API}/masters/public`, { 
        params: { master_type: 'service_type' } 
      });
      setServiceTypes(response.data);
    } catch (error) {
      console.error('Failed to fetch service types');
    }
  };

  const fetchData = async () => {
    try {
      const params = {};
      if (filterDevice) params.device_id = filterDevice;
      
      const [servicesRes, devicesRes, amcRes] = await Promise.all([
        axios.get(`${API}/admin/services`, {
          params,
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/devices`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/amc-contracts`, {
          headers: { Authorization: `Bearer ${token}` }
        }).catch(() => ({ data: [] }))
      ]);
      
      let filteredServices = servicesRes.data;
      if (filterType) {
        filteredServices = filteredServices.filter(s => s.service_type === filterType);
      }
      
      setServices(filteredServices);
      setDevices(devicesRes.data);
      setAmcContracts(amcRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  // Check AMC coverage when device changes
  const checkAmcCoverage = async (deviceId) => {
    if (!deviceId) {
      setDeviceAmcCoverage(null);
      return;
    }
    try {
      const response = await axios.get(`${API}/admin/amc-contracts/check-coverage/${deviceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDeviceAmcCoverage(response.data);
      
      // Auto-set AMC contract if device is covered
      if (response.data.is_covered && response.data.active_contracts.length > 0) {
        setFormData(prev => ({
          ...prev,
          amc_contract_id: response.data.active_contracts[0].contract_id,
          billing_type: 'covered'
        }));
      } else {
        setFormData(prev => ({
          ...prev,
          amc_contract_id: '',
          billing_type: 'chargeable',
          chargeable_reason: 'No active AMC'
        }));
      }
    } catch (error) {
      setDeviceAmcCoverage(null);
    }
  };
      
      setServices(filteredServices);
      setDevices(devicesRes.data);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.device_id || !formData.service_type || !formData.action_taken) {
      toast.error('Please fill in required fields');
      return;
    }

    const submitData = { ...formData };
    ['problem_reported', 'technician_name', 'ticket_id', 'notes'].forEach(field => {
      if (!submitData[field]) delete submitData[field];
    });

    try {
      if (editingService) {
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
      fetchData();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleFileUpload = async (serviceId, file) => {
    if (!file) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await axios.post(`${API}/admin/services/${serviceId}/attachments`, formData, {
        headers: { 
          Authorization: `Bearer ${token}`,
          'Content-Type': 'multipart/form-data'
        }
      });
      toast.success('Attachment uploaded');
      fetchData();
      // Refresh selected service if detail modal is open
      if (selectedService && selectedService.id === serviceId) {
        const response = await axios.get(`${API}/admin/services/${serviceId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSelectedService(response.data);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteAttachment = async (serviceId, attachmentId) => {
    if (!window.confirm('Delete this attachment?')) return;
    
    try {
      await axios.delete(`${API}/admin/services/${serviceId}/attachments/${attachmentId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Attachment deleted');
      fetchData();
      // Refresh selected service
      if (selectedService && selectedService.id === serviceId) {
        const response = await axios.get(`${API}/admin/services/${serviceId}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        setSelectedService(response.data);
      }
    } catch (error) {
      toast.error('Failed to delete attachment');
    }
  };

  const openCreateModal = (deviceId = '') => {
    setEditingService(null);
    setDeviceAmcCoverage(null);
    setFormData({
      device_id: deviceId || filterDevice || '',
      service_date: new Date().toISOString().split('T')[0],
      service_type: serviceTypes[0]?.name || 'Repair',
      problem_reported: '',
      action_taken: '',
      warranty_impact: 'not_applicable',
      technician_name: '',
      ticket_id: '',
      notes: '',
      amc_contract_id: '',
      billing_type: 'covered',
      chargeable_reason: ''
    });
    if (deviceId || filterDevice) {
      checkAmcCoverage(deviceId || filterDevice);
    }
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
      warranty_impact: service.warranty_impact || 'not_applicable',
      technician_name: service.technician_name || '',
      ticket_id: service.ticket_id || '',
      notes: service.notes || '',
      amc_contract_id: service.amc_contract_id || '',
      billing_type: service.billing_type || 'covered',
      chargeable_reason: service.chargeable_reason || ''
    });
    checkAmcCoverage(service.device_id);
    setModalOpen(true);
  };

  const openDetailModal = (service) => {
    setSelectedService(service);
    setDetailModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingService(null);
  };

  const getDevice = (deviceId) => {
    return devices.find(d => d.id === deviceId);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  const filteredServices = services.filter(s => {
    const device = getDevice(s.device_id);
    const searchLower = searchQuery.toLowerCase();
    return (
      s.action_taken?.toLowerCase().includes(searchLower) ||
      s.problem_reported?.toLowerCase().includes(searchLower) ||
      s.ticket_id?.toLowerCase().includes(searchLower) ||
      device?.serial_number?.toLowerCase().includes(searchLower) ||
      device?.brand?.toLowerCase().includes(searchLower)
    );
  });

  const serviceTypeColors = {
    'Repair': 'bg-amber-50 text-amber-600',
    'Part Replacement': 'bg-blue-50 text-blue-600',
    'Inspection': 'bg-purple-50 text-purple-600',
    'AMC Visit': 'bg-emerald-50 text-emerald-600',
    'Preventive Maintenance': 'bg-cyan-50 text-cyan-600',
    'Software Update': 'bg-indigo-50 text-indigo-600',
    'Warranty Claim': 'bg-rose-50 text-rose-600',
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="service-history-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Service History</h1>
          <p className="text-slate-500 mt-1">Track repairs, maintenance, and service records</p>
        </div>
        <Button 
          onClick={() => openCreateModal()}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
          data-testid="add-service-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Service Record
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by action, problem, ticket..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input pl-11"
          />
        </div>
        <select
          value={filterDevice}
          onChange={(e) => setFilterDevice(e.target.value)}
          className="form-select w-full sm:w-56"
        >
          <option value="">All Devices</option>
          {devices.map(d => (
            <option key={d.id} value={d.id}>{d.brand} {d.model} - {d.serial_number}</option>
          ))}
        </select>
        <select
          value={filterType}
          onChange={(e) => setFilterType(e.target.value)}
          className="form-select w-full sm:w-44"
        >
          <option value="">All Types</option>
          {serviceTypes.map(t => (
            <option key={t.id} value={t.name}>{t.name}</option>
          ))}
        </select>
      </div>

      {/* Timeline View */}
      <div className="bg-white rounded-xl border border-slate-100 divide-y divide-slate-100">
        {filteredServices.length > 0 ? (
          filteredServices.map((service) => {
            const device = getDevice(service.device_id);
            return (
              <div 
                key={service.id} 
                className="p-4 hover:bg-slate-50 transition-colors cursor-pointer"
                onClick={() => openDetailModal(service)}
                data-testid={`service-row-${service.id}`}
              >
                <div className="flex items-start gap-4">
                  {/* Timeline Icon */}
                  <div className="flex flex-col items-center">
                    <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      serviceTypeColors[service.service_type] || 'bg-slate-100 text-slate-600'
                    }`}>
                      <Wrench className="h-4 w-4" />
                    </div>
                    <div className="w-0.5 h-full bg-slate-200 mt-2 hidden sm:block"></div>
                  </div>
                  
                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-4">
                      <div>
                        <div className="flex items-center gap-2 flex-wrap">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            serviceTypeColors[service.service_type] || 'bg-slate-100 text-slate-600'
                          }`}>
                            {service.service_type}
                          </span>
                          {service.ticket_id && (
                            <span className="text-xs font-mono text-slate-500">#{service.ticket_id}</span>
                          )}
                        </div>
                        <h3 className="font-medium text-slate-900 mt-2">{service.action_taken}</h3>
                        {service.problem_reported && (
                          <p className="text-sm text-slate-500 mt-1">Problem: {service.problem_reported}</p>
                        )}
                      </div>
                      <div className="text-right shrink-0">
                        <p className="text-sm font-medium text-slate-900">{formatDate(service.service_date)}</p>
                        {service.technician_name && (
                          <p className="text-xs text-slate-500 mt-1">by {service.technician_name}</p>
                        )}
                      </div>
                    </div>
                    
                    {/* Device Info */}
                    {device && (
                      <div className="flex items-center gap-2 mt-3 text-sm text-slate-500">
                        <Laptop className="h-3.5 w-3.5" />
                        <span>{device.brand} {device.model}</span>
                        <span className="font-mono text-xs">({device.serial_number})</span>
                      </div>
                    )}
                    
                    {/* Attachments indicator */}
                    {service.attachments?.length > 0 && (
                      <div className="flex items-center gap-1 mt-2 text-xs text-slate-500">
                        <Paperclip className="h-3 w-3" />
                        <span>{service.attachments.length} attachment(s)</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Actions */}
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild onClick={(e) => e.stopPropagation()}>
                      <Button variant="ghost" size="icon">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openDetailModal(service); }}>
                        <FileText className="h-4 w-4 mr-2" />
                        View Details
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={(e) => { e.stopPropagation(); openEditModal(service); }}>
                        <Edit2 className="h-4 w-4 mr-2" />
                        Edit
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
              </div>
            );
          })
        ) : (
          <div className="text-center py-16">
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
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingService ? 'Edit Service Record' : 'Add Service Record'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div>
              <label className="form-label">Device *</label>
              <select
                value={formData.device_id}
                onChange={(e) => setFormData({ ...formData, device_id: e.target.value })}
                className="form-select"
                disabled={!!editingService}
              >
                <option value="">Select Device</option>
                {devices.map(d => (
                  <option key={d.id} value={d.id}>{d.brand} {d.model} - {d.serial_number}</option>
                ))}
              </select>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Service Date *</label>
                <input
                  type="date"
                  value={formData.service_date}
                  onChange={(e) => setFormData({ ...formData, service_date: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Service Type *</label>
                <select
                  value={formData.service_type}
                  onChange={(e) => setFormData({ ...formData, service_type: e.target.value })}
                  className="form-select"
                >
                  <option value="">Select Type</option>
                  {serviceTypes.map(t => (
                    <option key={t.id} value={t.name}>{t.name}</option>
                  ))}
                </select>
              </div>
            </div>
            
            <div>
              <label className="form-label">Problem Reported</label>
              <textarea
                value={formData.problem_reported}
                onChange={(e) => setFormData({ ...formData, problem_reported: e.target.value })}
                className="form-input"
                rows={2}
                placeholder="Describe the issue reported..."
              />
            </div>
            
            <div>
              <label className="form-label">Action Taken *</label>
              <textarea
                value={formData.action_taken}
                onChange={(e) => setFormData({ ...formData, action_taken: e.target.value })}
                className="form-input"
                rows={2}
                placeholder="Describe what was done..."
              />
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Technician Name</label>
                <input
                  type="text"
                  value={formData.technician_name}
                  onChange={(e) => setFormData({ ...formData, technician_name: e.target.value })}
                  className="form-input"
                  placeholder="Who performed the service?"
                />
              </div>
              <div>
                <label className="form-label">Ticket ID</label>
                <input
                  type="text"
                  value={formData.ticket_id}
                  onChange={(e) => setFormData({ ...formData, ticket_id: e.target.value })}
                  className="form-input"
                  placeholder="Reference ticket number"
                />
              </div>
            </div>
            
            <div>
              <label className="form-label">Warranty Impact</label>
              <select
                value={formData.warranty_impact}
                onChange={(e) => setFormData({ ...formData, warranty_impact: e.target.value })}
                className="form-select"
              >
                <option value="not_applicable">Not Applicable</option>
                <option value="started">New Warranty Started</option>
                <option value="extended">Warranty Extended</option>
              </select>
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
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
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
              {/* Header */}
              <div className="flex items-start gap-4">
                <div className={`w-12 h-12 rounded-full flex items-center justify-center ${
                  serviceTypeColors[selectedService.service_type] || 'bg-slate-100 text-slate-600'
                }`}>
                  <Wrench className="h-5 w-5" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${
                      serviceTypeColors[selectedService.service_type] || 'bg-slate-100 text-slate-600'
                    }`}>
                      {selectedService.service_type}
                    </span>
                    {selectedService.ticket_id && (
                      <span className="text-xs font-mono bg-slate-100 px-2 py-1 rounded">
                        #{selectedService.ticket_id}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-slate-500 mt-1">
                    {formatDate(selectedService.service_date)}
                    {selectedService.technician_name && ` • by ${selectedService.technician_name}`}
                  </p>
                </div>
              </div>
              
              {/* Device Info */}
              {(() => {
                const device = getDevice(selectedService.device_id);
                return device ? (
                  <div className="bg-slate-50 rounded-lg p-4">
                    <div className="flex items-center gap-3">
                      <Laptop className="h-5 w-5 text-slate-600" />
                      <div>
                        <p className="font-medium text-slate-900">{device.brand} {device.model}</p>
                        <p className="text-sm text-slate-500 font-mono">{device.serial_number}</p>
                      </div>
                    </div>
                  </div>
                ) : null;
              })()}
              
              {/* Details */}
              <div className="space-y-4">
                {selectedService.problem_reported && (
                  <div>
                    <p className="text-sm font-medium text-slate-500">Problem Reported</p>
                    <p className="mt-1">{selectedService.problem_reported}</p>
                  </div>
                )}
                
                <div>
                  <p className="text-sm font-medium text-slate-500">Action Taken</p>
                  <p className="mt-1">{selectedService.action_taken}</p>
                </div>
                
                {selectedService.warranty_impact !== 'not_applicable' && (
                  <div>
                    <p className="text-sm font-medium text-slate-500">Warranty Impact</p>
                    <span className="inline-block mt-1 text-xs px-2 py-1 rounded-full bg-blue-50 text-blue-600 capitalize">
                      {selectedService.warranty_impact?.replace('_', ' ')}
                    </span>
                  </div>
                )}
                
                {selectedService.notes && (
                  <div>
                    <p className="text-sm font-medium text-slate-500">Notes</p>
                    <p className="mt-1 text-sm text-slate-600">{selectedService.notes}</p>
                  </div>
                )}
              </div>
              
              {/* Attachments */}
              <div>
                <div className="flex items-center justify-between mb-3">
                  <p className="text-sm font-medium text-slate-500">Attachments</p>
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      className="hidden"
                      accept=".pdf,.jpg,.jpeg,.png"
                      onChange={(e) => handleFileUpload(selectedService.id, e.target.files?.[0])}
                      disabled={uploading}
                    />
                    <Button variant="outline" size="sm" disabled={uploading} asChild>
                      <span>
                        <Paperclip className="h-3 w-3 mr-1" />
                        {uploading ? 'Uploading...' : 'Add'}
                      </span>
                    </Button>
                  </label>
                </div>
                
                {selectedService.attachments?.length > 0 ? (
                  <div className="space-y-2">
                    {selectedService.attachments.map((att) => (
                      <div 
                        key={att.id} 
                        className="flex items-center justify-between bg-slate-50 rounded-lg px-3 py-2"
                      >
                        <div className="flex items-center gap-2 min-w-0">
                          <FileText className="h-4 w-4 text-slate-500 shrink-0" />
                          <span className="text-sm truncate">{att.original_name}</span>
                          <span className="text-xs text-slate-400">
                            ({(att.file_size / 1024).toFixed(1)} KB)
                          </span>
                        </div>
                        <div className="flex items-center gap-1">
                          <a
                            href={`${process.env.REACT_APP_BACKEND_URL}/uploads/${att.filename}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="p-1 hover:bg-slate-200 rounded"
                          >
                            <Download className="h-4 w-4 text-slate-500" />
                          </a>
                          <button
                            onClick={() => handleDeleteAttachment(selectedService.id, att.id)}
                            className="p-1 hover:bg-red-100 rounded"
                          >
                            <X className="h-4 w-4 text-red-500" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-slate-400">No attachments</p>
                )}
              </div>
              
              {/* Footer */}
              <div className="flex items-center justify-between pt-4 border-t text-xs text-slate-400">
                <p>Created by {selectedService.created_by_name} on {formatDateTime(selectedService.created_at)}</p>
              </div>
              
              <div className="flex justify-end gap-3">
                <Button variant="outline" onClick={() => setDetailModalOpen(false)}>
                  Close
                </Button>
                <Button 
                  onClick={() => {
                    setDetailModalOpen(false);
                    openEditModal(selectedService);
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

export default ServiceHistory;
