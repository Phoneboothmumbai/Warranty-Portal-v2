import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Search, Package, Clock, CheckCircle2, Truck, XCircle, 
  Building2, MapPin, User, FileText, ChevronDown, Filter
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusOptions = [
  { value: 'requested', label: 'Requested', color: 'bg-blue-100 text-blue-700', icon: Clock },
  { value: 'approved', label: 'Approved', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2 },
  { value: 'processing', label: 'Processing', color: 'bg-amber-100 text-amber-700', icon: Package },
  { value: 'delivered', label: 'Delivered', color: 'bg-green-100 text-green-700', icon: Truck },
  { value: 'cancelled', label: 'Cancelled', color: 'bg-red-100 text-red-700', icon: XCircle },
];

const SupplyOrders = () => {
  const { token } = useAuth();
  const [orders, setOrders] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterCompany, setFilterCompany] = useState('');
  
  // Detail modal
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [detailModalOpen, setDetailModalOpen] = useState(false);
  const [updating, setUpdating] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      const [ordersRes, companiesRes] = await Promise.all([
        axios.get(`${API}/admin/supply-orders`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/admin/companies`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setOrders(ordersRes.data);
      setCompanies(companiesRes.data);
    } catch (error) {
      toast.error('Failed to load orders');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const getStatusConfig = (status) => {
    return statusOptions.find(s => s.value === status) || statusOptions[0];
  };

  const updateOrderStatus = async (orderId, newStatus) => {
    setUpdating(true);
    try {
      await axios.put(`${API}/admin/supply-orders/${orderId}`, 
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success(`Order status updated to ${newStatus}`);
      fetchData();
      if (selectedOrder?.id === orderId) {
        setSelectedOrder(prev => ({ ...prev, status: newStatus }));
      }
    } catch (error) {
      toast.error('Failed to update order');
    } finally {
      setUpdating(false);
    }
  };

  const updateOrderNotes = async (orderId, notes) => {
    try {
      await axios.put(`${API}/admin/supply-orders/${orderId}`, 
        { admin_notes: notes },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Notes saved');
      fetchData();
    } catch (error) {
      toast.error('Failed to save notes');
    }
  };

  const openDetailModal = (order) => {
    setSelectedOrder(order);
    setDetailModalOpen(true);
  };

  const filteredOrders = orders.filter(order => {
    const matchesSearch = 
      order.order_number.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.company_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      order.requested_by_name.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = !filterStatus || order.status === filterStatus;
    const matchesCompany = !filterCompany || order.company_id === filterCompany;
    return matchesSearch && matchesStatus && matchesCompany;
  });

  const formatDate = (dateStr) => {
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Office Supplies - Orders</h1>
          <p className="text-slate-500 mt-1">
            {orders.length} orders • {orders.filter(o => o.status === 'requested').length} pending
          </p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {statusOptions.map(status => {
          const count = orders.filter(o => o.status === status.value).length;
          const StatusIcon = status.icon;
          return (
            <div 
              key={status.value}
              onClick={() => setFilterStatus(filterStatus === status.value ? '' : status.value)}
              className={`bg-white rounded-xl border p-4 cursor-pointer transition-all ${
                filterStatus === status.value 
                  ? 'border-emerald-500 ring-2 ring-emerald-100' 
                  : 'border-slate-200 hover:border-slate-300'
              }`}
            >
              <div className="flex items-center gap-2">
                <StatusIcon className="h-4 w-4 text-slate-400" />
                <span className="text-sm text-slate-500">{status.label}</span>
              </div>
              <p className="text-2xl font-bold text-slate-900 mt-1">{count}</p>
            </div>
          );
        })}
      </div>

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by order #, company, or user..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
          />
        </div>
        <select
          value={filterCompany}
          onChange={(e) => setFilterCompany(e.target.value)}
          className="px-4 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
        >
          <option value="">All Companies</option>
          {companies.map(company => (
            <option key={company.id} value={company.id}>{company.name}</option>
          ))}
        </select>
        {filterStatus && (
          <Button variant="outline" size="sm" onClick={() => setFilterStatus('')}>
            <XCircle className="h-4 w-4 mr-1" />
            Clear Filter
          </Button>
        )}
      </div>

      {/* Orders List */}
      <div className="space-y-4">
        {filteredOrders.length === 0 ? (
          <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
            <Package className="h-12 w-12 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No Orders Found</h3>
            <p className="text-slate-500">
              {orders.length === 0 ? 'No orders have been placed yet.' : 'Try adjusting your filters.'}
            </p>
          </div>
        ) : (
          filteredOrders.map(order => {
            const statusConfig = getStatusConfig(order.status);
            const StatusIcon = statusConfig.icon;
            return (
              <div 
                key={order.id} 
                className="bg-white rounded-xl border border-slate-200 overflow-hidden hover:border-slate-300 transition-colors"
              >
                <div className="p-4 sm:p-6">
                  <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
                    {/* Order Info */}
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-mono font-bold text-slate-900">{order.order_number}</span>
                        <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium ${statusConfig.color}`}>
                          <StatusIcon className="h-3 w-3" />
                          {statusConfig.label}
                        </span>
                      </div>
                      
                      <div className="flex flex-wrap gap-4 text-sm text-slate-600">
                        <div className="flex items-center gap-1">
                          <Building2 className="h-4 w-4 text-slate-400" />
                          {order.company_name}
                        </div>
                        <div className="flex items-center gap-1">
                          <User className="h-4 w-4 text-slate-400" />
                          {order.requested_by_name}
                        </div>
                        <div className="flex items-center gap-1">
                          <Clock className="h-4 w-4 text-slate-400" />
                          {formatDate(order.created_at)}
                        </div>
                      </div>

                      {/* Items Preview */}
                      <div className="mt-3 flex flex-wrap gap-2">
                        {order.items.slice(0, 3).map((item, idx) => (
                          <span key={idx} className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600">
                            {item.product_name} × {item.quantity}
                          </span>
                        ))}
                        {order.items.length > 3 && (
                          <span className="px-2 py-1 bg-slate-100 rounded text-xs text-slate-600">
                            +{order.items.length - 3} more
                          </span>
                        )}
                      </div>

                      {/* Delivery Location */}
                      {order.delivery_location && (
                        <div className="mt-2 text-xs text-slate-500 flex items-center gap-1">
                          <MapPin className="h-3 w-3" />
                          {order.delivery_location.site_name || order.delivery_location.address}
                          {order.delivery_location.city && `, ${order.delivery_location.city}`}
                        </div>
                      )}
                    </div>

                    {/* Actions */}
                    <div className="flex items-center gap-2">
                      <select
                        value={order.status}
                        onChange={(e) => updateOrderStatus(order.id, e.target.value)}
                        className="px-3 py-1.5 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        disabled={updating}
                      >
                        {statusOptions.map(status => (
                          <option key={status.value} value={status.value}>{status.label}</option>
                        ))}
                      </select>
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => openDetailModal(order)}
                      >
                        <FileText className="h-4 w-4 mr-1" />
                        Details
                      </Button>
                    </div>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>

      {/* Order Detail Modal */}
      <Dialog open={detailModalOpen} onOpenChange={setDetailModalOpen}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Package className="h-5 w-5 text-emerald-600" />
              Order Details
            </DialogTitle>
          </DialogHeader>
          
          {selectedOrder && (
            <div className="space-y-6 mt-4">
              {/* Order Header */}
              <div className="flex items-center justify-between pb-4 border-b border-slate-200">
                <div>
                  <p className="font-mono font-bold text-lg text-slate-900">{selectedOrder.order_number}</p>
                  <p className="text-sm text-slate-500">{formatDate(selectedOrder.created_at)}</p>
                </div>
                <select
                  value={selectedOrder.status}
                  onChange={(e) => updateOrderStatus(selectedOrder.id, e.target.value)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium border-2 ${getStatusConfig(selectedOrder.status).color}`}
                >
                  {statusOptions.map(status => (
                    <option key={status.value} value={status.value}>{status.label}</option>
                  ))}
                </select>
              </div>

              {/* Company & Requester */}
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-50 rounded-lg p-4">
                  <p className="text-xs font-medium text-slate-500 uppercase mb-2">Company</p>
                  <p className="font-medium text-slate-900">{selectedOrder.company_name}</p>
                </div>
                <div className="bg-slate-50 rounded-lg p-4">
                  <p className="text-xs font-medium text-slate-500 uppercase mb-2">Requested By</p>
                  <p className="font-medium text-slate-900">{selectedOrder.requested_by_name}</p>
                  <p className="text-sm text-slate-500">{selectedOrder.requested_by_email}</p>
                  {selectedOrder.requested_by_phone && (
                    <p className="text-sm text-slate-500">{selectedOrder.requested_by_phone}</p>
                  )}
                </div>
              </div>

              {/* Delivery Location */}
              <div className="bg-emerald-50 rounded-lg p-4">
                <p className="text-xs font-medium text-emerald-700 uppercase mb-2 flex items-center gap-1">
                  <MapPin className="h-3 w-3" />
                  Delivery Location
                </p>
                {selectedOrder.delivery_location?.site_name && (
                  <p className="font-medium text-emerald-900">{selectedOrder.delivery_location.site_name}</p>
                )}
                <p className="text-sm text-emerald-700">
                  {selectedOrder.delivery_location?.address}
                  {selectedOrder.delivery_location?.city && `, ${selectedOrder.delivery_location.city}`}
                  {selectedOrder.delivery_location?.pincode && ` - ${selectedOrder.delivery_location.pincode}`}
                </p>
                {selectedOrder.delivery_location?.contact_person && (
                  <p className="text-sm text-emerald-700 mt-2">
                    Contact: {selectedOrder.delivery_location.contact_person}
                    {selectedOrder.delivery_location?.contact_phone && ` • ${selectedOrder.delivery_location.contact_phone}`}
                  </p>
                )}
              </div>

              {/* Items */}
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase mb-3">Items Ordered ({selectedOrder.items.length})</p>
                <div className="border border-slate-200 rounded-lg overflow-hidden">
                  <table className="w-full">
                    <thead className="bg-slate-50">
                      <tr>
                        <th className="px-4 py-2 text-left text-xs font-medium text-slate-600">Product</th>
                        <th className="px-4 py-2 text-left text-xs font-medium text-slate-600">Category</th>
                        <th className="px-4 py-2 text-right text-xs font-medium text-slate-600">Qty</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100">
                      {selectedOrder.items.map((item, idx) => (
                        <tr key={idx}>
                          <td className="px-4 py-3 text-sm font-medium text-slate-900">{item.product_name}</td>
                          <td className="px-4 py-3 text-sm text-slate-500">{item.category_name}</td>
                          <td className="px-4 py-3 text-sm text-right font-medium">{item.quantity} {item.unit}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Notes */}
              {selectedOrder.notes && (
                <div className="bg-amber-50 rounded-lg p-4">
                  <p className="text-xs font-medium text-amber-700 uppercase mb-2">Customer Notes</p>
                  <p className="text-sm text-amber-900">{selectedOrder.notes}</p>
                </div>
              )}

              {/* Admin Notes */}
              <div>
                <p className="text-xs font-medium text-slate-500 uppercase mb-2">Admin Notes</p>
                <textarea
                  defaultValue={selectedOrder.admin_notes || ''}
                  onBlur={(e) => {
                    if (e.target.value !== (selectedOrder.admin_notes || '')) {
                      updateOrderNotes(selectedOrder.id, e.target.value);
                    }
                  }}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                  rows={2}
                  placeholder="Internal notes (vendor, tracking, etc.)"
                />
              </div>

              {/* osTicket Link */}
              {selectedOrder.osticket_id && (
                <div className="text-sm text-slate-500">
                  osTicket ID: <span className="font-mono">{selectedOrder.osticket_id}</span>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SupplyOrders;
