import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Laptop, ArrowLeft, Shield, Calendar, MapPin, Building2, Tag,
  Clock, AlertTriangle, CheckCircle2, XCircle, Wrench, Package,
  User, FileText, QrCode, Edit2, Printer, Monitor, Tablet, Server
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const deviceIcons = {
  LAPTOP: Laptop,
  DESKTOP: Monitor,
  TABLET: Tablet,
  PRINTER: Printer,
  SERVER: Server,
};

const statusColors = {
  active: 'bg-emerald-100 text-emerald-700 border-emerald-200',
  in_repair: 'bg-amber-100 text-amber-700 border-amber-200',
  retired: 'bg-slate-100 text-slate-600 border-slate-200',
  disposed: 'bg-red-100 text-red-700 border-red-200'
};

const warrantyStatusColors = {
  active: 'text-emerald-600',
  expiring: 'text-amber-600',
  expired: 'text-red-600'
};

const AdminDeviceDetails = () => {
  const { deviceId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [device, setDevice] = useState(null);
  const [serviceHistory, setServiceHistory] = useState([]);
  const [parts, setParts] = useState([]);
  const [assignedEmployee, setAssignedEmployee] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDevice = useCallback(async () => {
    try {
      setLoading(true);
      // Fetch device details
      const deviceRes = await axios.get(`${API}/admin/devices/${deviceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setDevice(deviceRes.data);

      // Fetch service history for this device
      try {
        const serviceRes = await axios.get(`${API}/admin/service-records`, {
          params: { device_id: deviceId, limit: 20 },
          headers: { Authorization: `Bearer ${token}` }
        });
        setServiceHistory(serviceRes.data || []);
      } catch (e) {
        setServiceHistory([]);
      }

      // Fetch parts for this device
      try {
        const partsRes = await axios.get(`${API}/admin/parts`, {
          params: { device_id: deviceId, limit: 50 },
          headers: { Authorization: `Bearer ${token}` }
        });
        setParts(partsRes.data || []);
      } catch (e) {
        setParts([]);
      }

      // Fetch assigned employee if exists
      if (deviceRes.data.assigned_employee_id) {
        try {
          const empRes = await axios.get(`${API}/admin/company-employees/${deviceRes.data.assigned_employee_id}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          setAssignedEmployee(empRes.data);
        } catch (e) {
          setAssignedEmployee(null);
        }
      }

    } catch (error) {
      toast.error('Failed to load device details');
      navigate('/admin/devices');
    } finally {
      setLoading(false);
    }
  }, [deviceId, token, navigate]);

  useEffect(() => {
    fetchDevice();
  }, [fetchDevice]);

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', { 
      day: 'numeric', month: 'short', year: 'numeric' 
    });
  };

  const calculateWarrantyStatus = (endDate) => {
    if (!endDate) return { status: 'unknown', days: null };
    const end = new Date(endDate);
    const now = new Date();
    const days = Math.ceil((end - now) / (1000 * 60 * 60 * 24));
    
    if (days < 0) return { status: 'expired', days: Math.abs(days) };
    if (days <= 30) return { status: 'expiring', days };
    return { status: 'active', days };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!device) return null;

  const DeviceIcon = deviceIcons[device.device_type] || Laptop;
  const warranty = calculateWarrantyStatus(device.warranty_end_date);

  return (
    <div className="space-y-6" data-testid="admin-device-details">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">Device Details</h1>
            <p className="text-slate-500">View and manage device information</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button 
            variant="outline" 
            onClick={() => navigate('/admin/devices', { state: { editDeviceId: device.id } })}
          >
            <Edit2 className="h-4 w-4 mr-2" />
            Edit Device
          </Button>
          {device.qr_code_url && (
            <Button variant="outline" onClick={() => window.open(device.qr_code_url, '_blank')}>
              <QrCode className="h-4 w-4 mr-2" />
              View QR Code
            </Button>
          )}
        </div>
      </div>

      {/* Device Overview Card */}
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <div className="flex items-start gap-6">
          <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center">
            <DeviceIcon className="h-10 w-10 text-white" />
          </div>
          <div className="flex-1">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-2xl font-bold text-slate-900">
                  {device.brand} {device.model || device.device_type}
                </h2>
                <p className="text-slate-500 font-mono text-lg">{device.serial_number}</p>
              </div>
              <span className={`px-3 py-1 rounded-full text-sm font-medium border ${statusColors[device.status] || 'bg-slate-100'}`}>
                {device.status?.replace('_', ' ')}
              </span>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
              <div className="flex items-center gap-2 text-slate-600">
                <Tag className="h-4 w-4 text-slate-400" />
                <span className="text-sm">{device.device_type}</span>
              </div>
              <div className="flex items-center gap-2 text-slate-600">
                <Building2 className="h-4 w-4 text-slate-400" />
                <span className="text-sm">{device.company_name || 'No Company'}</span>
              </div>
              {device.site_name && (
                <div className="flex items-center gap-2 text-slate-600">
                  <MapPin className="h-4 w-4 text-slate-400" />
                  <span className="text-sm">{device.site_name}</span>
                </div>
              )}
              {device.asset_tag && (
                <div className="flex items-center gap-2 text-slate-600">
                  <FileText className="h-4 w-4 text-slate-400" />
                  <span className="text-sm">Asset: {device.asset_tag}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {/* Warranty Info */}
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-blue-600" />
            Warranty Information
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-500">Start Date</span>
              <span className="font-medium">{formatDate(device.warranty_start_date)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">End Date</span>
              <span className="font-medium">{formatDate(device.warranty_end_date)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500">Status</span>
              <span className={`font-medium flex items-center gap-1 ${warrantyStatusColors[warranty.status]}`}>
                {warranty.status === 'active' && <CheckCircle2 className="h-4 w-4" />}
                {warranty.status === 'expiring' && <AlertTriangle className="h-4 w-4" />}
                {warranty.status === 'expired' && <XCircle className="h-4 w-4" />}
                {warranty.days !== null ? (
                  warranty.status === 'expired' 
                    ? `Expired ${warranty.days} days ago`
                    : `${warranty.days} days remaining`
                ) : 'Unknown'}
              </span>
            </div>
            {device.warranty_type && (
              <div className="flex justify-between">
                <span className="text-slate-500">Type</span>
                <span className="font-medium">{device.warranty_type}</span>
              </div>
            )}
          </div>
        </div>

        {/* Assigned Employee */}
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <User className="h-5 w-5 text-purple-600" />
            Assigned Employee
          </h3>
          {assignedEmployee ? (
            <div 
              className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg cursor-pointer hover:bg-slate-100 transition-colors"
              onClick={() => navigate(`/admin/employees/${assignedEmployee.id}`)}
            >
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center text-white font-medium">
                {assignedEmployee.name?.charAt(0)?.toUpperCase()}
              </div>
              <div>
                <p className="font-medium text-slate-900">{assignedEmployee.name}</p>
                {assignedEmployee.department && (
                  <p className="text-xs text-slate-500">{assignedEmployee.department}</p>
                )}
                {assignedEmployee.email && (
                  <p className="text-xs text-slate-400">{assignedEmployee.email}</p>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-6 text-slate-400">
              <User className="h-8 w-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No employee assigned</p>
            </div>
          )}
        </div>

        {/* Configuration */}
        {device.configuration && (
          <div className="bg-white rounded-xl border border-slate-100 p-5">
            <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Package className="h-5 w-5 text-amber-600" />
              Configuration
            </h3>
            <div className="bg-slate-50 rounded-lg p-3">
              <pre className="text-sm text-slate-600 whitespace-pre-wrap font-mono">
                {device.configuration}
              </pre>
            </div>
          </div>
        )}

        {/* Purchase Info */}
        <div className="bg-white rounded-xl border border-slate-100 p-5">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Calendar className="h-5 w-5 text-emerald-600" />
            Purchase Information
          </h3>
          <div className="space-y-3">
            <div className="flex justify-between">
              <span className="text-slate-500">Purchase Date</span>
              <span className="font-medium">{formatDate(device.purchase_date)}</span>
            </div>
            {device.purchase_price && (
              <div className="flex justify-between">
                <span className="text-slate-500">Purchase Price</span>
                <span className="font-medium">₹{device.purchase_price.toLocaleString('en-IN')}</span>
              </div>
            )}
            {device.vendor && (
              <div className="flex justify-between">
                <span className="text-slate-500">Vendor</span>
                <span className="font-medium">{device.vendor}</span>
              </div>
            )}
            {device.invoice_number && (
              <div className="flex justify-between">
                <span className="text-slate-500">Invoice #</span>
                <span className="font-medium font-mono">{device.invoice_number}</span>
              </div>
            )}
          </div>
        </div>

        {/* Additional Details */}
        {(device.notes || device.condition) && (
          <div className="bg-white rounded-xl border border-slate-100 p-5">
            <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <FileText className="h-5 w-5 text-slate-600" />
              Additional Details
            </h3>
            <div className="space-y-3">
              {device.condition && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Condition</span>
                  <span className="font-medium">{device.condition}</span>
                </div>
              )}
              {device.notes && (
                <div>
                  <span className="text-slate-500 block mb-1">Notes</span>
                  <p className="text-sm text-slate-600 bg-slate-50 p-2 rounded">{device.notes}</p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Service History */}
      <div className="bg-white rounded-xl border border-slate-100 p-6">
        <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
          <Wrench className="h-5 w-5 text-amber-600" />
          Service History
          {serviceHistory.length > 0 && (
            <span className="px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full text-xs">
              {serviceHistory.length}
            </span>
          )}
        </h3>
        {serviceHistory.length > 0 ? (
          <div className="space-y-3">
            {serviceHistory.map((record) => (
              <div key={record.id} className="flex items-start gap-4 p-3 bg-slate-50 rounded-lg">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center flex-shrink-0">
                  <Wrench className="h-5 w-5 text-amber-600" />
                </div>
                <div className="flex-1">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="font-medium text-slate-900">{record.service_type}</p>
                      <p className="text-sm text-slate-500">{record.description}</p>
                    </div>
                    <span className="text-xs text-slate-400">{formatDate(record.service_date)}</span>
                  </div>
                  <div className="flex gap-4 mt-2 text-xs text-slate-500">
                    {record.technician_name && <span>Tech: {record.technician_name}</span>}
                    {record.cost && <span>Cost: ₹{record.cost}</span>}
                    <span className={`px-2 py-0.5 rounded-full ${
                      record.status === 'completed' ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                    }`}>
                      {record.status}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">
            <Wrench className="h-10 w-10 mx-auto mb-2 opacity-50" />
            <p>No service history found</p>
          </div>
        )}
      </div>

      {/* Parts */}
      {parts.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-100 p-6">
          <h3 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Package className="h-5 w-5 text-blue-600" />
            Installed Parts
            <span className="px-2 py-0.5 bg-blue-100 text-blue-700 rounded-full text-xs">
              {parts.length}
            </span>
          </h3>
          <div className="space-y-4">
            {parts.map((part) => {
              const partWarranty = calculateWarrantyStatus(part.warranty_expiry_date);
              return (
                <div key={part.id} className="p-4 bg-slate-50 rounded-lg border border-slate-100">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                        <Package className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <p className="font-semibold text-slate-900">{part.part_name}</p>
                        {part.part_type && (
                          <span className="text-xs px-2 py-0.5 bg-slate-200 text-slate-600 rounded-full">
                            {part.part_type}
                          </span>
                        )}
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${
                      partWarranty.status === 'active' ? 'bg-emerald-100 text-emerald-700' :
                      partWarranty.status === 'expiring' ? 'bg-amber-100 text-amber-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {partWarranty.status === 'active' && <CheckCircle2 className="h-3 w-3" />}
                      {partWarranty.status === 'expiring' && <AlertTriangle className="h-3 w-3" />}
                      {partWarranty.status === 'expired' && <XCircle className="h-3 w-3" />}
                      {partWarranty.status === 'expired' ? 'Warranty Expired' : 
                       partWarranty.status === 'expiring' ? `${partWarranty.days}d left` : 
                       'Under Warranty'}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                    {part.brand && (
                      <div>
                        <span className="text-slate-400 text-xs block">Brand</span>
                        <span className="text-slate-700 font-medium">{part.brand}</span>
                      </div>
                    )}
                    {part.model_number && (
                      <div>
                        <span className="text-slate-400 text-xs block">Model</span>
                        <span className="text-slate-700 font-medium font-mono">{part.model_number}</span>
                      </div>
                    )}
                    {part.serial_number && (
                      <div>
                        <span className="text-slate-400 text-xs block">Serial No.</span>
                        <span className="text-slate-700 font-medium font-mono">{part.serial_number}</span>
                      </div>
                    )}
                    {part.capacity && (
                      <div>
                        <span className="text-slate-400 text-xs block">Capacity</span>
                        <span className="text-slate-700 font-medium">{part.capacity}</span>
                      </div>
                    )}
                    {part.purchase_date && (
                      <div>
                        <span className="text-slate-400 text-xs block">Purchase Date</span>
                        <span className="text-slate-700">{formatDate(part.purchase_date)}</span>
                      </div>
                    )}
                    {part.replaced_date && (
                      <div>
                        <span className="text-slate-400 text-xs block">Installed On</span>
                        <span className="text-slate-700">{formatDate(part.replaced_date)}</span>
                      </div>
                    )}
                    {part.warranty_expiry_date && (
                      <div>
                        <span className="text-slate-400 text-xs block">Warranty Until</span>
                        <span className={`font-medium ${warrantyStatusColors[partWarranty.status]}`}>
                          {formatDate(part.warranty_expiry_date)}
                        </span>
                      </div>
                    )}
                    {part.warranty_months && (
                      <div>
                        <span className="text-slate-400 text-xs block">Warranty Period</span>
                        <span className="text-slate-700">{part.warranty_months} months</span>
                      </div>
                    )}
                    {part.vendor && (
                      <div>
                        <span className="text-slate-400 text-xs block">Vendor</span>
                        <span className="text-slate-700">{part.vendor}</span>
                      </div>
                    )}
                    {part.purchase_cost && (
                      <div>
                        <span className="text-slate-400 text-xs block">Cost</span>
                        <span className="text-slate-700 font-medium">₹{part.purchase_cost.toLocaleString('en-IN')}</span>
                      </div>
                    )}
                  </div>
                  
                  {part.notes && (
                    <div className="mt-3 pt-3 border-t border-slate-200">
                      <span className="text-slate-400 text-xs block mb-1">Notes</span>
                      <p className="text-sm text-slate-600">{part.notes}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminDeviceDetails;
