import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { Plus, Search, Edit2, Trash2, MoreVertical, Building2, Keyboard, Mouse, Headphones, Monitor, Cable, Package, User } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, DropdownMenuSeparator } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';
import { SmartSelect } from '../../components/ui/smart-select';
import { QuickCreateCompany } from '../../components/forms';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const accessoryIcons = {
  KEYBOARD: Keyboard,
  MOUSE: Mouse,
  HEADSET: Headphones,
  MONITOR_STAND: Monitor,
  CABLE: Cable,
};

const statusColors = {
  available: 'bg-emerald-100 text-emerald-700',
  assigned: 'bg-blue-100 text-blue-700',
  in_repair: 'bg-amber-100 text-amber-700',
  disposed: 'bg-red-100 text-red-700'
};

const Accessories = () => {
  const { token } = useAuth();
  const [accessories, setAccessories] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [employees, setEmployees] = useState([]);
  const [accessoryTypes, setAccessoryTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [modalOpen, setModalOpen] = useState(false);
  const [editingAccessory, setEditingAccessory] = useState(null);
  
  const [formData, setFormData] = useState({
    company_id: '',
    name: '',
    accessory_type: '',
    brand: '',
    model: '',
    serial_number: '',
    assigned_employee_id: '',
    purchase_date: '',
    purchase_price: '',
    vendor: '',
    warranty_end_date: '',
    status: 'available',
    condition: 'good',
    quantity: 1,
    notes: ''
  });

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [accRes, compRes, typeRes] = await Promise.all([
        axios.get(`${API}/admin/accessories`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/companies`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/admin/masters`, { params: { master_type: 'accessory_type' }, headers: { Authorization: `Bearer ${token}` } })
      ]);
      setAccessories(accRes.data);
      setCompanies(compRes.data);
      setAccessoryTypes(typeRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Fetch employees when company changes
  useEffect(() => {
    const fetchEmployees = async () => {
      if (formData.company_id) {
        try {
          const res = await axios.get(`${API}/admin/company-employees`, {
            params: { company_id: formData.company_id },
            headers: { Authorization: `Bearer ${token}` }
          });
          setEmployees(res.data);
        } catch (e) {
          setEmployees([]);
        }
      } else {
        setEmployees([]);
      }
    };
    fetchEmployees();
  }, [formData.company_id, token]);

  const filtered = accessories.filter(acc => {
    const matchesSearch = !searchQuery || 
      acc.name?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      acc.brand?.toLowerCase().includes(searchQuery.toLowerCase()) ||
      acc.serial_number?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCompany = !filterCompany || acc.company_id === filterCompany;
    const matchesType = !filterType || acc.accessory_type === filterType;
    const matchesStatus = !filterStatus || acc.status === filterStatus;
    return matchesSearch && matchesCompany && matchesType && matchesStatus;
  });

  const stats = {
    total: accessories.length,
    available: accessories.filter(a => a.status === 'available').length,
    assigned: accessories.filter(a => a.status === 'assigned').length,
    inRepair: accessories.filter(a => a.status === 'in_repair').length
  };

  const openCreateModal = () => {
    setEditingAccessory(null);
    setFormData({
      company_id: filterCompany || '',
      name: '',
      accessory_type: accessoryTypes[0]?.code || '',
      brand: '',
      model: '',
      serial_number: '',
      assigned_employee_id: '',
      purchase_date: '',
      purchase_price: '',
      vendor: '',
      warranty_end_date: '',
      status: 'available',
      condition: 'good',
      quantity: 1,
      notes: ''
    });
    setModalOpen(true);
  };

  const openEditModal = (acc) => {
    setEditingAccessory(acc);
    setFormData({
      company_id: acc.company_id || '',
      name: acc.name || '',
      accessory_type: acc.accessory_type || '',
      brand: acc.brand || '',
      model: acc.model || '',
      serial_number: acc.serial_number || '',
      assigned_employee_id: acc.assigned_employee_id || '',
      purchase_date: acc.purchase_date?.split('T')[0] || '',
      purchase_price: acc.purchase_price || '',
      vendor: acc.vendor || '',
      warranty_end_date: acc.warranty_end_date?.split('T')[0] || '',
      status: acc.status || 'available',
      condition: acc.condition || 'good',
      quantity: acc.quantity || 1,
      notes: acc.notes || ''
    });
    setModalOpen(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.company_id || !formData.name || !formData.accessory_type) {
      toast.error('Please fill required fields');
      return;
    }

    try {
      const submitData = { ...formData };
      if (submitData.purchase_price) submitData.purchase_price = parseFloat(submitData.purchase_price);
      if (!submitData.assigned_employee_id) delete submitData.assigned_employee_id;

      if (editingAccessory) {
        await axios.put(`${API}/admin/accessories/${editingAccessory.id}`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Accessory updated');
      } else {
        await axios.post(`${API}/admin/accessories`, submitData, {
          headers: { Authorization: `Bearer ${token}` }
        });
        toast.success('Accessory created');
      }
      setModalOpen(false);
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save');
    }
  };

  const handleDelete = async (acc) => {
    if (!window.confirm(`Delete "${acc.name}"?`)) return;
    try {
      await axios.delete(`${API}/admin/accessories/${acc.id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Accessory deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  const getIcon = (type) => {
    const Icon = accessoryIcons[type] || Package;
    return Icon;
  };

  return (
    <div className="space-y-6" data-testid="accessories-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Accessories & Peripherals</h1>
          <p className="text-slate-500">Manage keyboards, mice, cables, and other accessories</p>
        </div>
        <Button onClick={openCreateModal} className="bg-[#0F62FE] hover:bg-[#0043CE] text-white" data-testid="add-accessory-btn">
          <Plus className="h-4 w-4 mr-2" />
          Add Accessory
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
              <Package className="h-5 w-5 text-slate-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.total}</p>
              <p className="text-xs text-slate-500">Total</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <Package className="h-5 w-5 text-emerald-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.available}</p>
              <p className="text-xs text-slate-500">Available</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.assigned}</p>
              <p className="text-xs text-slate-500">Assigned</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-xl border border-slate-100 p-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
              <Package className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <p className="text-2xl font-bold text-slate-900">{stats.inRepair}</p>
              <p className="text-xs text-slate-500">In Repair</p>
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
              placeholder="Search accessories..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-input pl-10"
            />
          </div>
          <select value={filterCompany} onChange={(e) => setFilterCompany(e.target.value)} className="form-select w-48">
            <option value="">All Companies</option>
            {companies.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
          <select value={filterType} onChange={(e) => setFilterType(e.target.value)} className="form-select w-40">
            <option value="">All Types</option>
            {accessoryTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
          </select>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)} className="form-select w-36">
            <option value="">All Status</option>
            <option value="available">Available</option>
            <option value="assigned">Assigned</option>
            <option value="in_repair">In Repair</option>
            <option value="disposed">Disposed</option>
          </select>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
          </div>
        ) : filtered.length > 0 ? (
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600 uppercase">Accessory</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600 uppercase">Company</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600 uppercase">Type</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600 uppercase">Assigned To</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600 uppercase">Status</th>
                <th className="text-left px-4 py-3 text-xs font-semibold text-slate-600 uppercase">Qty</th>
                <th className="w-12"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filtered.map((acc) => {
                const Icon = getIcon(acc.accessory_type);
                return (
                  <tr key={acc.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <div className="w-9 h-9 rounded-lg bg-slate-100 flex items-center justify-center">
                          <Icon className="h-4 w-4 text-slate-600" />
                        </div>
                        <div>
                          <p className="font-medium text-slate-900">{acc.name}</p>
                          <p className="text-xs text-slate-500">{acc.brand} {acc.model}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">{acc.company_name}</td>
                    <td className="px-4 py-3">
                      <span className="text-xs px-2 py-1 rounded-full bg-slate-100 text-slate-600">
                        {accessoryTypes.find(t => t.code === acc.accessory_type)?.name || acc.accessory_type}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {acc.assigned_employee_name || '-'}
                    </td>
                    <td className="px-4 py-3">
                      <span className={`text-xs px-2 py-1 rounded-full ${statusColors[acc.status]}`}>
                        {acc.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">{acc.quantity}</td>
                    <td className="px-4 py-3">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <button className="p-1.5 hover:bg-slate-100 rounded-lg">
                            <MoreVertical className="h-4 w-4 text-slate-400" />
                          </button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => openEditModal(acc)}>
                            <Edit2 className="h-4 w-4 mr-2" />
                            Edit
                          </DropdownMenuItem>
                          <DropdownMenuSeparator />
                          <DropdownMenuItem className="text-red-600" onClick={() => handleDelete(acc)}>
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
          <div className="text-center py-12">
            <Package className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <p className="text-slate-500">No accessories found</p>
          </div>
        )}
      </div>

      {/* Create/Edit Modal */}
      <Dialog open={modalOpen} onOpenChange={setModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingAccessory ? 'Edit Accessory' : 'Add Accessory'}</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4 mt-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="form-label">Company *</label>
                <SmartSelect
                  value={formData.company_id}
                  onChange={(val) => setFormData({ ...formData, company_id: val, assigned_employee_id: '' })}
                  options={companies.map(c => ({ value: c.id, label: c.name }))}
                  placeholder="Select company"
                  quickCreate={<QuickCreateCompany onCreated={(c) => { setCompanies([...companies, c]); setFormData({ ...formData, company_id: c.id }); }} />}
                />
              </div>
              <div>
                <label className="form-label">Name *</label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="form-input"
                  placeholder="e.g., Logitech MK270 Keyboard"
                />
              </div>
              <div>
                <label className="form-label">Type *</label>
                <select
                  value={formData.accessory_type}
                  onChange={(e) => setFormData({ ...formData, accessory_type: e.target.value })}
                  className="form-select"
                >
                  <option value="">Select type</option>
                  {accessoryTypes.map(t => <option key={t.code} value={t.code}>{t.name}</option>)}
                </select>
              </div>
              <div>
                <label className="form-label">Brand</label>
                <input
                  type="text"
                  value={formData.brand}
                  onChange={(e) => setFormData({ ...formData, brand: e.target.value })}
                  className="form-input"
                  placeholder="e.g., Logitech"
                />
              </div>
              <div>
                <label className="form-label">Model</label>
                <input
                  type="text"
                  value={formData.model}
                  onChange={(e) => setFormData({ ...formData, model: e.target.value })}
                  className="form-input"
                  placeholder="e.g., MK270"
                />
              </div>
              <div>
                <label className="form-label">Serial Number</label>
                <input
                  type="text"
                  value={formData.serial_number}
                  onChange={(e) => setFormData({ ...formData, serial_number: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Quantity</label>
                <input
                  type="number"
                  value={formData.quantity}
                  onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
                  className="form-input"
                  min="1"
                />
              </div>
              <div>
                <label className="form-label">Assigned To</label>
                <select
                  value={formData.assigned_employee_id}
                  onChange={(e) => setFormData({ ...formData, assigned_employee_id: e.target.value, status: e.target.value ? 'assigned' : 'available' })}
                  className="form-select"
                  disabled={!formData.company_id}
                >
                  <option value="">Not assigned</option>
                  {employees.map(e => <option key={e.id} value={e.id}>{e.name}</option>)}
                </select>
              </div>
              <div>
                <label className="form-label">Status</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({ ...formData, status: e.target.value })}
                  className="form-select"
                >
                  <option value="available">Available</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_repair">In Repair</option>
                  <option value="disposed">Disposed</option>
                </select>
              </div>
              <div>
                <label className="form-label">Condition</label>
                <select
                  value={formData.condition}
                  onChange={(e) => setFormData({ ...formData, condition: e.target.value })}
                  className="form-select"
                >
                  <option value="new">New</option>
                  <option value="good">Good</option>
                  <option value="fair">Fair</option>
                  <option value="poor">Poor</option>
                </select>
              </div>
              <div>
                <label className="form-label">Purchase Date</label>
                <input
                  type="date"
                  value={formData.purchase_date}
                  onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Purchase Price</label>
                <input
                  type="number"
                  value={formData.purchase_price}
                  onChange={(e) => setFormData({ ...formData, purchase_price: e.target.value })}
                  className="form-input"
                  placeholder="₹"
                />
              </div>
              <div>
                <label className="form-label">Vendor</label>
                <input
                  type="text"
                  value={formData.vendor}
                  onChange={(e) => setFormData({ ...formData, vendor: e.target.value })}
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Warranty End Date</label>
                <input
                  type="date"
                  value={formData.warranty_end_date}
                  onChange={(e) => setFormData({ ...formData, warranty_end_date: e.target.value })}
                  className="form-input"
                />
              </div>
              <div className="col-span-2">
                <label className="form-label">Notes</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  className="form-input"
                  rows={2}
                />
              </div>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button type="button" variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
              <Button type="submit" className="bg-[#0F62FE] hover:bg-[#0043CE] text-white">
                {editingAccessory ? 'Update' : 'Create'}
              </Button>
            </div>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Accessories;
