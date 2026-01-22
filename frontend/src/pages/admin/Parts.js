import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Plus, Search, Edit2, Trash2, Wrench, MoreVertical, Laptop, CheckCircle2, XCircle, HardDrive, Calendar, Building2, DollarSign } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { SmartSelect } from '../../components/ui/smart-select';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const defaultPartTypes = ['HDD', 'SSD', 'RAM', 'Power Supply', 'Battery', 'Keyboard', 'Screen', 'Motherboard', 'Camera Lens', 'Fan', 'Charger', 'Network Card', 'Other'];

const Parts = () => {
  const { token } = useAuth();
  const [parts, setParts] = useState([]);
  const [devices, setDevices] = useState([]);
  const [partTypes, setPartTypes] = useState(defaultPartTypes);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterDevice, setFilterDevice] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingPart, setEditingPart] = useState(null);
  const [formData, setFormData] = useState({
    device_id: '',
    part_type: 'HDD',
    part_name: '',
    brand: '',
    model_number: '',
    serial_number: '',
    capacity: '',
    purchase_date: '',
    replaced_date: '',
    warranty_months: 12,
    vendor: '',
    purchase_cost: '',
    notes: ''
  });

  useEffect(() => {
    fetchData();
  }, [filterDevice]);

  const fetchData = async () => {
    try {
      const [partsRes, devicesRes] = await Promise.all([
        axios.get(`${API}/admin/parts`, {
          params: filterDevice ? { device_id: filterDevice } : {},
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/devices`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setParts(partsRes.data);
      setDevices(devicesRes.data);
      
      // Extract unique part names from existing parts and merge with defaults
      const existingPartNames = [...new Set(partsRes.data.map(p => p.part_name))];
      const allPartTypes = [...new Set([...defaultPartTypes, ...existingPartNames])];
      setPartTypes(allPartTypes);
    } catch (error) {
      toast.error('Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  // Prepare device options for SmartSelect
  const deviceOptions = devices.map(d => ({
    id: d.id,
    label: `${d.brand} ${d.model} (${d.serial_number})`,
    subtitle: d.company_name || ''
  }));

  // Prepare part type options for SmartSelect
  const partTypeOptions = partTypes.map(p => ({
    id: p,
    label: p
  }));

  // Handle adding new part type
  const handleAddPartType = (newPartName) => {
    if (newPartName && !partTypes.includes(newPartName)) {
      setPartTypes(prev => [...prev, newPartName]);
      setFormData(prev => ({ ...prev, part_type: newPartName, part_name: newPartName }));
      toast.success(`Added new part type: ${newPartName}`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.device_id || !formData.part_name || !formData.replaced_date || !formData.warranty_months) {
      toast.error('Please fill in required fields');
      return;
    }

    try {
      const payload = {
        ...formData,
        purchase_cost: formData.purchase_cost ? parseFloat(formData.purchase_cost) : null
      };
      
      if (editingPart) {
        await axios.put(`${API}/admin/parts/${editingPart.id}`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Part updated');
      } else {
        await axios.post(`${API}/admin/parts`, payload, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Part created');
      }
      fetchData();
      closeModal();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Operation failed');
    }
  };

  const handleDelete = async (part) => {
    if (!window.confirm(`Delete "${part.part_name}" part record?`)) return;
    
    try {
      await axios.delete(`${API}/admin/parts/${part.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Part deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete part');
    }
  };

  const openCreateModal = () => {
    setEditingPart(null);
    setFormData({
      device_id: filterDevice || '',
      part_type: 'HDD',
      part_name: '',
      brand: '',
      model_number: '',
      serial_number: '',
      capacity: '',
      purchase_date: new Date().toISOString().split('T')[0],
      replaced_date: new Date().toISOString().split('T')[0],
      warranty_months: 12,
      vendor: '',
      purchase_cost: '',
      notes: ''
    });
    setModalOpen(true);
  };

  const openEditModal = (part) => {
    setEditingPart(part);
    setFormData({
      device_id: part.device_id,
      part_type: part.part_type || part.part_name,
      part_name: part.part_name,
      brand: part.brand || '',
      model_number: part.model_number || '',
      serial_number: part.serial_number || '',
      capacity: part.capacity || '',
      purchase_date: part.purchase_date || '',
      replaced_date: part.replaced_date,
      warranty_months: part.warranty_months,
      vendor: part.vendor || '',
      purchase_cost: part.purchase_cost || '',
      notes: part.notes || ''
    });
    setModalOpen(true);
  };
      device_id: part.device_id,
      part_name: part.part_name,
      serial_number: part.serial_number || '',
      replaced_date: part.replaced_date,
      warranty_months: part.warranty_months,
      notes: part.notes || ''
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingPart(null);
  };

  const getDeviceInfo = (deviceId) => {
    const device = devices.find(d => d.id === deviceId);
    return device ? `${device.brand} ${device.model} (${device.serial_number})` : 'Unknown';
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' });
  };

  const isWarrantyActive = (dateStr) => {
    if (!dateStr) return false;
    return new Date(dateStr) >= new Date();
  };

  const filteredParts = parts.filter(p => 
    p.part_name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="parts-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Parts</h1>
          <p className="text-slate-500 mt-1">Track replaced parts and warranties</p>
        </div>
        <Button 
          onClick={openCreateModal}
          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white"
          data-testid="add-part-btn"
        >
          <Plus className="h-4 w-4 mr-2" />
          Add Part
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1 max-w-md">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search parts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="form-input pl-11"
            data-testid="search-parts"
          />
        </div>
        <select
          value={filterDevice}
          onChange={(e) => setFilterDevice(e.target.value)}
          className="form-select w-full sm:w-80"
        >
          <option value="">All Devices</option>
          {devices.map(d => (
            <option key={d.id} value={d.id}>{d.brand} {d.model} ({d.serial_number})</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {filteredParts.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full table-modern">
              <thead>
                <tr>
                  <th>Part</th>
                  <th>Device</th>
                  <th>Details</th>
                  <th>Installed</th>
                  <th>Warranty</th>
                  <th>Status</th>
                  <th className="w-16"></th>
                </tr>
              </thead>
              <tbody>
                {filteredParts.map((part) => (
                  <tr key={part.id} data-testid={`part-row-${part.id}`}>
                    <td>
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <HardDrive className="h-5 w-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{part.part_name}</p>
                          <p className="text-xs text-slate-500">{part.part_type || 'Part'}</p>
                        </div>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        <Laptop className="h-3.5 w-3.5 text-slate-400" />
                        <span className="text-sm">{getDeviceInfo(part.device_id)}</span>
                      </div>
                    </td>
                    <td>
                      <div className="text-sm">
                        {part.brand && <p className="text-slate-900">{part.brand} {part.model_number || ''}</p>}
                        {part.capacity && <p className="text-slate-500">{part.capacity}</p>}
                        {part.serial_number && <p className="text-xs text-slate-400">SN: {part.serial_number}</p>}
                        {!part.brand && !part.capacity && !part.serial_number && <span className="text-slate-400">-</span>}
                      </div>
                    </td>
                    <td className="text-sm">{formatDate(part.replaced_date)}</td>
                    <td>
                      <div>
                        <p className="text-sm font-medium">{part.warranty_months} months</p>
                        <p className="text-xs text-slate-500">Until {formatDate(part.warranty_expiry_date)}</p>
                      </div>
                    </td>
                    <td>
                      <div className="flex items-center gap-2">
                        {isWarrantyActive(part.warranty_expiry_date) ? (
                          <>
                            <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                            <span className="badge-active">Covered</span>
                          </>
                        ) : (
                          <>
                            <XCircle className="h-4 w-4 text-slate-400" />
                            <span className="badge-expired">Expired</span>
                          </>
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
                          <DropdownMenuItem onClick={() => openEditModal(part)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem 
                            onClick={() => handleDelete(part)}
                            className="text-red-600"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Delete
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
            <Wrench className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500 mb-4">No parts found</p>
            <Button onClick={openCreateModal} variant="outline">
              <Plus className="h-4 w-4 mr-2" />
              Add your first part
            </Button>
          </div>
        )}
      </div>

      {/* Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <HardDrive className="h-5 w-5 text-blue-600" />
              {editingPart ? 'Edit Part' : 'Add Part'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-5 mt-4">
            {/* Device Selection */}
            <div>
              <label className="form-label">Device *</label>
              <SmartSelect
                value={formData.device_id}
                onValueChange={(val) => setFormData({ ...formData, device_id: val })}
                options={deviceOptions}
                placeholder="Search and select device..."
                searchPlaceholder="Search by brand, model, serial..."
                emptyText="No devices found"
                disabled={editingPart}
                data-testid="part-device-select"
              />
            </div>

            {/* Part Type & Name */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Part Type *</label>
                <SmartSelect
                  value={formData.part_type}
                  onValueChange={(val) => setFormData({ ...formData, part_type: val, part_name: formData.part_name || val })}
                  options={partTypeOptions}
                  placeholder="Select part type..."
                  searchPlaceholder="Search part types..."
                  emptyText="No matching parts"
                  allowCreate={true}
                  createLabel="Add New Part Type"
                  onCreateNew={handleAddPartType}
                  data-testid="part-type-select"
                />
              </div>
              <div>
                <label className="form-label">Part Name/Description *</label>
                <input
                  type="text"
                  value={formData.part_name}
                  onChange={(e) => setFormData({ ...formData, part_name: e.target.value })}
                  className="form-input"
                  placeholder="e.g., Seagate Skyhawk 4TB"
                  data-testid="part-name-input"
                />
              </div>
            </div>

            {/* Brand & Model */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Brand</label>
                <input
                  type="text"
                  value={formData.brand}
                  onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                  className="form-input"
                  placeholder="e.g., Seagate, WD, Samsung"
                  data-testid="part-brand-input"
                />
              </div>
              <div>
                <label className="form-label">Model Number</label>
                <input
                  type="text"
                  value={formData.model_number}
                  onChange={(e) => setFormData({ ...formData, model_number: e.target.value })}
                  className="form-input"
                  placeholder="e.g., ST4000VX013"
                  data-testid="part-model-input"
                />
              </div>
            </div>

            {/* Serial & Capacity */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Serial Number</label>
                <input
                  type="text"
                  value={formData.serial_number}
                  onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
                  className="form-input"
                  placeholder="Enter serial number"
                  data-testid="part-serial-number-input"
                />
              </div>
              <div>
                <label className="form-label">Capacity/Size</label>
                <input
                  type="text"
                  value={formData.capacity}
                  onChange={(e) => setFormData({ ...formData, capacity: e.target.value })}
                  className="form-input"
                  placeholder="e.g., 4TB, 16GB, 512GB"
                  data-testid="part-capacity-input"
                />
              </div>
            </div>

            {/* Dates */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Purchase Date</label>
                <input
                  type="date"
                  value={formData.purchase_date}
                  onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
                  className="form-input"
                  data-testid="part-purchase-date-input"
                />
              </div>
              <div>
                <label className="form-label">Installation Date *</label>
                <input
                  type="date"
                  value={formData.replaced_date}
                  onChange={(e) => setFormData({ ...formData, replaced_date: e.target.value })}
                  className="form-input"
                  data-testid="part-replaced-date-input"
                />
              </div>
            </div>

            {/* Warranty */}
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="text-sm font-semibold text-blue-800 mb-3 flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Warranty Information
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-medium text-blue-700">Warranty Period (Months) *</label>
                  <input
                    type="number"
                    min="1"
                    value={formData.warranty_months}
                    onChange={(e) => setFormData({ ...formData, warranty_months: parseInt(e.target.value) || 1 })}
                    className="form-input mt-1 bg-white"
                    data-testid="part-warranty-months-input"
                  />
                </div>
                <div>
                  <label className="text-xs font-medium text-blue-700">Warranty Expiry</label>
                  <p className="form-input mt-1 bg-white text-slate-600">
                    {formData.replaced_date && formData.warranty_months
                      ? new Date(new Date(formData.replaced_date).setMonth(new Date(formData.replaced_date).getMonth() + formData.warranty_months)).toLocaleDateString()
                      : 'Set dates above'}
                  </p>
                </div>
              </div>
            </div>

            {/* Vendor & Cost */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Vendor/Supplier</label>
                <input
                  type="text"
                  value={formData.vendor}
                  onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                  className="form-input"
                  placeholder="Where purchased from"
                  data-testid="part-vendor-input"
                />
              </div>
              <div>
                <label className="form-label">Purchase Cost (₹)</label>
                <input
                  type="number"
                  value={formData.purchase_cost}
                  onChange={(e) => setFormData({ ...formData, purchase_cost: e.target.value })}
                  className="form-input"
                  placeholder="0"
                  min="0"
                  data-testid="part-cost-input"
                />
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
                placeholder="Additional details about this part..."
                data-testid="part-notes-input"
              />
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t">
              <Button type="button" variant="outline" onClick={closeModal}>
                Cancel
              </Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                {editingPart ? 'Update Part' : 'Add Part'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Parts;
