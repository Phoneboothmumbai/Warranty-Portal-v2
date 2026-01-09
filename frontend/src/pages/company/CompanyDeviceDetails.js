import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Laptop, ArrowLeft, Shield, Calendar, MapPin, Building2, Tag,
  Clock, AlertTriangle, CheckCircle2, XCircle, Ticket, FileText,
  ChevronRight, Wrench, Package, ShoppingCart
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyDeviceDetails = () => {
  const { deviceId } = useParams();
  const { token } = useCompanyAuth();
  const navigate = useNavigate();
  const [device, setDevice] = useState(null);
  const [parts, setParts] = useState([]);
  const [serviceHistory, setServiceHistory] = useState([]);
  const [amcInfo, setAmcInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  
  // Consumable order state
  const [orderModalOpen, setOrderModalOpen] = useState(false);
  const [orderLoading, setOrderLoading] = useState(false);
  const [selectedConsumables, setSelectedConsumables] = useState({});
  const [orderNotes, setOrderNotes] = useState('');

  useEffect(() => {
    fetchDevice();
  }, [deviceId]);

  const fetchDevice = async () => {
    try {
      const response = await axios.get(`${API}/company/devices/${deviceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // API returns { device: {...}, parts: [...], service_history: [...], amc_info: {...} }
      setDevice(response.data.device);
      setParts(response.data.parts || []);
      setServiceHistory(response.data.service_history || []);
      setAmcInfo(response.data.amc_info);
    } catch (error) {
      toast.error('Failed to load device details');
      navigate('/company/devices');
    } finally {
      setLoading(false);
    }
  };

  const toggleConsumable = (consumableId) => {
    setSelectedConsumables(prev => {
      const newState = { ...prev };
      if (newState[consumableId]) {
        delete newState[consumableId];
      } else {
        newState[consumableId] = 1; // Default quantity 1
      }
      return newState;
    });
  };

  const updateConsumableQty = (consumableId, qty) => {
    setSelectedConsumables(prev => ({
      ...prev,
      [consumableId]: Math.max(1, parseInt(qty) || 1)
    }));
  };

  const handleOrderConsumable = async () => {
    const selectedIds = Object.keys(selectedConsumables);
    if (selectedIds.length === 0) {
      toast.error('Please select at least one consumable to order');
      return;
    }
    
    // Build order items from selected consumables
    const consumables = device.consumables || [];
    const orderItems = selectedIds.map(id => {
      const consumable = consumables.find(c => c.id === id);
      return {
        consumable_id: id,
        name: consumable?.name || 'Consumable',
        consumable_type: consumable?.consumable_type || 'Consumable',
        model_number: consumable?.model_number || '',
        brand: consumable?.brand,
        color: consumable?.color,
        quantity: selectedConsumables[id]
      };
    });
    
    setOrderLoading(true);
    try {
      const response = await axios.post(
        `${API}/company/devices/${deviceId}/order-consumable`,
        {
          items: orderItems,
          notes: orderNotes
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      const itemCount = response.data.items_count || orderItems.length;
      const totalQty = response.data.total_quantity || orderItems.reduce((s, i) => s + i.quantity, 0);
      toast.success(`Order ${response.data.order_number} submitted! (${itemCount} items, ${totalQty} units)`);
      setOrderModalOpen(false);
      setSelectedConsumables({});
      setOrderNotes('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit order');
    } finally {
      setOrderLoading(false);
    }
  };

  const isPrinter = device?.category?.toLowerCase().includes('printer') || 
                    device?.device_type?.toLowerCase().includes('printer');

  const getWarrantyStatus = () => {
    if (!device?.warranty_end_date) return { status: 'unknown', label: 'Unknown', color: 'slate' };
    
    const endDate = new Date(device.warranty_end_date);
    const today = new Date();
    const daysLeft = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
    
    if (daysLeft < 0) return { status: 'expired', label: 'Expired', color: 'red', days: Math.abs(daysLeft) };
    if (daysLeft <= 30) return { status: 'critical', label: `${daysLeft} days left`, color: 'red', days: daysLeft };
    if (daysLeft <= 60) return { status: 'warning', label: `${daysLeft} days left`, color: 'amber', days: daysLeft };
    if (daysLeft <= 90) return { status: 'attention', label: `${daysLeft} days left`, color: 'orange', days: daysLeft };
    return { status: 'active', label: 'Active', color: 'emerald', days: daysLeft };
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!device) return null;

  const warranty = getWarrantyStatus();
  const colorClasses = {
    red: 'bg-red-50 text-red-700 border-red-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    slate: 'bg-slate-50 text-slate-600 border-slate-200',
  };

  return (
    <div className="space-y-6" data-testid="device-details-page">
      {/* Back Button */}
      <Link 
        to="/company/devices" 
        className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Devices
      </Link>

      {/* Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 bg-slate-100 rounded-xl flex items-center justify-center">
              <Laptop className="h-8 w-8 text-slate-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{device.serial_number}</h1>
              <p className="text-slate-500 mt-1">
                {device.device_type || device.category} • {device.brand} {device.model}
              </p>
              {device.site_name && (
                <div className="flex items-center gap-1.5 text-sm text-slate-500 mt-2">
                  <MapPin className="h-4 w-4" />
                  {device.site_name}
                </div>
              )}
            </div>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border ${colorClasses[warranty.color]}`}>
              <Shield className="h-5 w-5" />
              Warranty: {warranty.label}
            </div>
            <div className="flex flex-wrap gap-2">
              {isPrinter && (
                <Button 
                  onClick={() => setOrderModalOpen(true)}
                  variant="outline"
                  className="border-amber-500 text-amber-700 hover:bg-amber-50"
                  data-testid="order-consumables-btn"
                >
                  <ShoppingCart className="h-4 w-4 mr-2" />
                  Order Consumables
                </Button>
              )}
              <Link to={`/company/tickets?device=${device.id}`}>
                <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="raise-ticket-btn">
                  <Ticket className="h-4 w-4 mr-2" />
                  Raise Service Request
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Device Information */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Laptop className="h-5 w-5 text-slate-400" />
            Device Information
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Serial Number</dt>
              <dd className="font-medium text-slate-900">{device.serial_number}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Type</dt>
              <dd className="font-medium text-slate-900">{device.device_type || device.category || 'N/A'}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Brand</dt>
              <dd className="font-medium text-slate-900">{device.brand || 'N/A'}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Model</dt>
              <dd className="font-medium text-slate-900">{device.model || 'N/A'}</dd>
            </div>
            {device.asset_tag && (
              <div className="flex justify-between py-2 border-b border-slate-100">
                <dt className="text-slate-500">Asset Tag</dt>
                <dd className="font-medium text-slate-900">{device.asset_tag}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Warranty Information */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-slate-400" />
            Warranty Information
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Status</dt>
              <dd className={`font-medium ${warranty.color === 'emerald' ? 'text-emerald-600' : warranty.color === 'red' ? 'text-red-600' : 'text-amber-600'}`}>
                {warranty.status === 'expired' ? 'Expired' : 'Active'}
              </dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Start Date</dt>
              <dd className="font-medium text-slate-900">{formatDate(device.warranty_start_date)}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">End Date</dt>
              <dd className="font-medium text-slate-900">{formatDate(device.warranty_end_date)}</dd>
            </div>
            {warranty.days !== undefined && (
              <div className="flex justify-between py-2">
                <dt className="text-slate-500">
                  {warranty.status === 'expired' ? 'Expired' : 'Remaining'}
                </dt>
                <dd className={`font-medium ${warranty.color === 'emerald' ? 'text-emerald-600' : warranty.color === 'red' ? 'text-red-600' : 'text-amber-600'}`}>
                  {warranty.status === 'expired' ? `${warranty.days} days ago` : `${warranty.days} days`}
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      {/* Service History */}
      {serviceHistory && serviceHistory.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Wrench className="h-5 w-5 text-slate-400" />
              Service History
            </h2>
          </div>
          <div className="divide-y divide-slate-100">
            {serviceHistory.map((record, index) => (
              <div key={index} className="p-4 hover:bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900">{record.service_type}</p>
                    <p className="text-sm text-slate-500 mt-1">{record.problem_reported || record.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-slate-900">{formatDate(record.service_date)}</p>
                    <p className="text-xs text-slate-500">{record.technician_name || record.technician}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Parts / Components */}
      {parts && parts.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Tag className="h-5 w-5 text-slate-400" />
              Parts / Components
            </h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-100">
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Part Name</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Serial #</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Replaced</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Warranty Expiry</th>
                  <th className="text-left px-4 py-3 font-medium text-slate-600">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {parts.map((part, index) => {
                  const partExpiry = part.warranty_expiry_date ? new Date(part.warranty_expiry_date) : null;
                  const isPartActive = partExpiry && partExpiry > new Date();
                  return (
                    <tr key={index}>
                      <td className="px-4 py-3 font-medium text-slate-900">{part.part_name}</td>
                      <td className="px-4 py-3 font-mono text-slate-600">{part.serial_number || '-'}</td>
                      <td className="px-4 py-3 text-slate-600">{formatDate(part.replaced_date)}</td>
                      <td className="px-4 py-3 text-slate-600">{formatDate(part.warranty_expiry_date)}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          isPartActive ? 'bg-emerald-50 text-emerald-700' : 'bg-red-50 text-red-700'
                        }`}>
                          {isPartActive ? 'Covered' : 'Expired'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* AMC Information */}
      {amcInfo && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <FileText className="h-5 w-5 text-slate-400" />
            AMC Contract
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Contract Name</dt>
              <dd className="font-medium text-slate-900">{amcInfo.contract_name || 'N/A'}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Type</dt>
              <dd className="font-medium text-slate-900">{amcInfo.amc_type || 'N/A'}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Coverage Start</dt>
              <dd className="font-medium text-slate-900">{formatDate(amcInfo.coverage_start)}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Coverage End</dt>
              <dd className="font-medium text-slate-900">{formatDate(amcInfo.coverage_end)}</dd>
            </div>
            {amcInfo.coverage_includes && amcInfo.coverage_includes.length > 0 && (
              <div className="py-2">
                <dt className="text-slate-500 mb-2">Coverage Includes</dt>
                <dd className="flex flex-wrap gap-2">
                  {amcInfo.coverage_includes.map((item, idx) => (
                    <span key={idx} className="px-2 py-1 bg-emerald-50 text-emerald-700 text-xs rounded-full">
                      {item}
                    </span>
                  ))}
                </dd>
              </div>
            )}
          </dl>
        </div>
      )}

      {/* Order Consumables Modal */}
      <Dialog open={orderModalOpen} onOpenChange={setOrderModalOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5 text-amber-600" />
              Order Consumables
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4 mt-4">
            {/* Printer Info */}
            <div className="bg-slate-50 rounded-lg p-4">
              <p className="text-sm text-slate-500">Ordering for:</p>
              <p className="font-medium text-slate-900">{device.brand} {device.model}</p>
              <p className="text-xs text-slate-500 font-mono">{device.serial_number}</p>
            </div>

            {/* Consumable Details */}
            {(device.consumable_type || device.consumable_model) && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
                <p className="text-sm font-medium text-amber-800 mb-2">Configured Consumable:</p>
                <div className="text-sm text-amber-700 space-y-1">
                  {device.consumable_type && <p>Type: {device.consumable_type}</p>}
                  {device.consumable_model && <p>Model/Part: {device.consumable_model}</p>}
                  {device.consumable_brand && <p>Brand: {device.consumable_brand}</p>}
                </div>
              </div>
            )}

            {/* Order Form */}
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Quantity</label>
              <input
                type="number"
                min="1"
                max="100"
                value={orderForm.quantity}
                onChange={(e) => setOrderForm({ ...orderForm, quantity: parseInt(e.target.value) || 1 })}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                data-testid="consumable-quantity-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Notes (Optional)</label>
              <textarea
                value={orderForm.notes}
                onChange={(e) => setOrderForm({ ...orderForm, notes: e.target.value })}
                placeholder="Any special requirements or instructions..."
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                rows={3}
                data-testid="consumable-notes-input"
              />
            </div>

            <p className="text-xs text-slate-500">
              This request will be sent to the support team for processing. You will be contacted regarding pricing and delivery.
            </p>

            <div className="flex justify-end gap-3 pt-2">
              <Button 
                variant="outline" 
                onClick={() => setOrderModalOpen(false)}
                disabled={orderLoading}
              >
                Cancel
              </Button>
              <Button 
                onClick={handleOrderConsumable}
                disabled={orderLoading}
                className="bg-amber-600 hover:bg-amber-700 text-white"
                data-testid="submit-consumable-order-btn"
              >
                {orderLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Submitting...
                  </>
                ) : (
                  <>
                    <Package className="h-4 w-4 mr-2" />
                    Submit Order
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Related Tickets - removed since tickets aren't returned from this API */}
    </div>
  );
};

export default CompanyDeviceDetails;
