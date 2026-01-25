import { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, Building2, Calendar, Package, Clock, CheckCircle2, 
  XCircle, AlertTriangle, DollarSign, FileText, User, Laptop,
  Monitor, Printer, Server, Tablet, Edit2, RefreshCw
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusConfig = {
  pending_review: { label: 'Pending Review', color: 'bg-amber-100 text-amber-700 border-amber-200', icon: Clock },
  under_review: { label: 'Under Review', color: 'bg-blue-100 text-blue-700 border-blue-200', icon: RefreshCw },
  approved: { label: 'Approved', color: 'bg-emerald-100 text-emerald-700 border-emerald-200', icon: CheckCircle2 },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700 border-red-200', icon: XCircle },
  changes_requested: { label: 'Changes Requested', color: 'bg-orange-100 text-orange-700 border-orange-200', icon: AlertTriangle },
  cancelled: { label: 'Cancelled', color: 'bg-slate-100 text-slate-600 border-slate-200', icon: XCircle }
};

const amcTypeLabels = {
  comprehensive: 'Comprehensive',
  non_comprehensive: 'Non-Comprehensive',
  on_call: 'On-Call Basis'
};

const deviceIcons = {
  LAPTOP: Laptop,
  DESKTOP: Monitor,
  TABLET: Tablet,
  PRINTER: Printer,
  SERVER: Server,
};

const AdminAMCRequestDetail = () => {
  const { requestId } = useParams();
  const { token } = useAuth();
  const navigate = useNavigate();
  const [request, setRequest] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Edit mode
  const [isEditing, setIsEditing] = useState(false);
  const [editData, setEditData] = useState({
    price_per_device: '',
    total_price: '',
    admin_notes: '',
    rejection_reason: '',
    changes_requested_note: ''
  });

  const fetchRequest = useCallback(async () => {
    try {
      setLoading(true);
      const res = await axios.get(`${API}/admin/amc-requests/${requestId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setRequest(res.data);
      setEditData({
        price_per_device: res.data.price_per_device || '',
        total_price: res.data.total_price || '',
        admin_notes: res.data.admin_notes || '',
        rejection_reason: res.data.rejection_reason || '',
        changes_requested_note: res.data.changes_requested_note || ''
      });
    } catch (error) {
      toast.error('Failed to load request details');
      navigate('/admin/amc-requests');
    } finally {
      setLoading(false);
    }
  }, [requestId, token, navigate]);

  useEffect(() => {
    fetchRequest();
  }, [fetchRequest]);

  const handleUpdateStatus = async (newStatus, additionalData = {}) => {
    try {
      setActionLoading(true);
      await axios.put(`${API}/admin/amc-requests/${requestId}`, {
        status: newStatus,
        ...editData,
        ...additionalData
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success(`Request ${newStatus.replace('_', ' ')}`);
      fetchRequest();
      setIsEditing(false);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to update request');
    } finally {
      setActionLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!editData.total_price) {
      toast.error('Please set the total price before approving');
      return;
    }
    
    try {
      setActionLoading(true);
      // First update pricing
      await axios.put(`${API}/admin/amc-requests/${requestId}`, editData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // Then approve
      const res = await axios.post(`${API}/admin/amc-requests/${requestId}/approve`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('AMC Request approved and contract created!');
      navigate('/admin/amc-requests');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to approve request');
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!editData.rejection_reason) {
      toast.error('Please provide a rejection reason');
      return;
    }
    await handleUpdateStatus('rejected', { rejection_reason: editData.rejection_reason });
  };

  const handleRequestChanges = async () => {
    if (!editData.changes_requested_note) {
      toast.error('Please specify what changes are needed');
      return;
    }
    await handleUpdateStatus('changes_requested', { changes_requested_note: editData.changes_requested_note });
  };

  const calculatePricing = () => {
    if (editData.price_per_device && request?.device_count) {
      const years = request.duration_months / 12;
      return parseFloat(editData.price_per_device) * request.device_count * years;
    }
    return 0;
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    if (!amount) return '-';
    return `₹${parseFloat(amount).toLocaleString('en-IN')}`;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!request) return null;

  const status = statusConfig[request.status] || statusConfig.pending_review;
  const StatusIcon = status.icon;
  const canEdit = ['pending_review', 'under_review'].includes(request.status);

  return (
    <div className="space-y-6" data-testid="admin-amc-request-detail">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/admin/amc-requests')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">AMC Request Details</h1>
            <p className="text-slate-500">Review and process this AMC request</p>
          </div>
        </div>
        <span className={`px-3 py-1.5 rounded-full text-sm font-medium border flex items-center gap-1 ${status.color}`}>
          <StatusIcon className="h-4 w-4" />
          {status.label}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Details */}
        <div className="lg:col-span-2 space-y-6">
          {/* Company & Request Info */}
          <div className="bg-white rounded-xl border border-slate-100 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Building2 className="h-5 w-5 text-blue-600" />
              Request Information
            </h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-slate-500">Company</p>
                <p className="font-medium text-slate-900">{request.company?.name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Requested By</p>
                <p className="font-medium text-slate-900">{request.requested_by_name}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">AMC Type</p>
                <p className="font-medium text-slate-900">{amcTypeLabels[request.amc_type]}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Duration</p>
                <p className="font-medium text-slate-900">{request.duration_months} months</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Preferred Start Date</p>
                <p className="font-medium text-slate-900">{formatDate(request.preferred_start_date)}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Submitted On</p>
                <p className="font-medium text-slate-900">{formatDate(request.created_at)}</p>
              </div>
            </div>

            {request.special_requirements && (
              <div className="mt-4 pt-4 border-t border-slate-100">
                <p className="text-sm text-slate-500 mb-1">Special Requirements</p>
                <p className="text-slate-700 bg-slate-50 p-3 rounded-lg">{request.special_requirements}</p>
              </div>
            )}

            {request.budget_range && (
              <div className="mt-3">
                <p className="text-sm text-slate-500 mb-1">Budget Range</p>
                <p className="text-slate-700">{request.budget_range}</p>
              </div>
            )}
          </div>

          {/* Selected Devices */}
          <div className="bg-white rounded-xl border border-slate-100 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <Package className="h-5 w-5 text-purple-600" />
              Selected Devices
              <span className="px-2 py-0.5 bg-purple-100 text-purple-700 text-xs rounded-full">
                {request.device_count} devices
              </span>
            </h2>

            {request.selection_type === 'all' && (
              <div className="p-4 bg-blue-50 rounded-lg text-center">
                <Package className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <p className="font-medium text-slate-900">All Company Devices</p>
                <p className="text-sm text-slate-500">{request.device_count} devices total</p>
              </div>
            )}

            {request.selection_type === 'by_category' && (
              <div className="flex flex-wrap gap-2">
                {request.selected_categories?.map((cat) => (
                  <span key={cat} className="px-3 py-1.5 bg-slate-100 rounded-full text-sm text-slate-700">
                    {cat}
                  </span>
                ))}
              </div>
            )}

            {request.selection_type === 'specific' && request.selected_devices && (
              <div className="max-h-64 overflow-y-auto border rounded-lg divide-y">
                {request.selected_devices.map((device) => {
                  const DeviceIcon = deviceIcons[device.device_type] || Laptop;
                  return (
                    <div key={device.id} className="flex items-center gap-3 p-3">
                      <DeviceIcon className="h-5 w-5 text-slate-400" />
                      <div className="flex-1">
                        <p className="font-medium text-slate-900">{device.brand} {device.model}</p>
                        <p className="text-sm text-slate-500">{device.serial_number}</p>
                      </div>
                      <span className="text-xs px-2 py-1 bg-slate-100 rounded-full">
                        {device.device_type}
                      </span>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar - Pricing & Actions */}
        <div className="space-y-6">
          {/* Pricing Card */}
          <div className="bg-white rounded-xl border border-slate-100 p-6">
            <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
              <DollarSign className="h-5 w-5 text-emerald-600" />
              Pricing
            </h2>

            {canEdit ? (
              <div className="space-y-4">
                <div>
                  <label className="text-sm font-medium text-slate-700">Price per Device/Year</label>
                  <Input
                    type="number"
                    placeholder="e.g., 2500"
                    value={editData.price_per_device}
                    onChange={(e) => {
                      const price = e.target.value;
                      const total = price && request.device_count 
                        ? parseFloat(price) * request.device_count * (request.duration_months / 12)
                        : '';
                      setEditData({ ...editData, price_per_device: price, total_price: total });
                    }}
                    className="mt-1"
                  />
                </div>
                
                <div className="p-3 bg-slate-50 rounded-lg space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Devices</span>
                    <span className="text-slate-700">{request.device_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Duration</span>
                    <span className="text-slate-700">{request.duration_months / 12} year(s)</span>
                  </div>
                  <div className="flex justify-between pt-2 border-t border-slate-200 font-semibold">
                    <span className="text-slate-900">Total</span>
                    <span className="text-emerald-600">
                      {editData.total_price ? formatCurrency(editData.total_price) : '-'}
                    </span>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-slate-700">Admin Notes</label>
                  <Textarea
                    placeholder="Internal notes..."
                    value={editData.admin_notes}
                    onChange={(e) => setEditData({ ...editData, admin_notes: e.target.value })}
                    rows={2}
                    className="mt-1"
                  />
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-slate-500">Price/Device</span>
                  <span className="font-medium">{formatCurrency(request.price_per_device)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Total Price</span>
                  <span className="font-semibold text-emerald-600">{formatCurrency(request.total_price)}</span>
                </div>
                {request.admin_notes && (
                  <div className="pt-3 border-t">
                    <p className="text-sm text-slate-500">Admin Notes</p>
                    <p className="text-sm text-slate-700">{request.admin_notes}</p>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Actions Card */}
          {canEdit && (
            <div className="bg-white rounded-xl border border-slate-100 p-6 space-y-4">
              <h2 className="text-lg font-semibold text-slate-900">Actions</h2>

              {/* Mark Under Review */}
              {request.status === 'pending_review' && (
                <Button 
                  className="w-full" 
                  variant="outline"
                  onClick={() => handleUpdateStatus('under_review')}
                  disabled={actionLoading}
                >
                  <RefreshCw className="h-4 w-4 mr-2" />
                  Mark Under Review
                </Button>
              )}

              {/* Approve */}
              <Button 
                className="w-full bg-emerald-600 hover:bg-emerald-700" 
                onClick={handleApprove}
                disabled={actionLoading || !editData.total_price}
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Approve & Create Contract
              </Button>

              {/* Request Changes */}
              <div className="space-y-2">
                <Textarea
                  placeholder="What changes are needed?"
                  value={editData.changes_requested_note}
                  onChange={(e) => setEditData({ ...editData, changes_requested_note: e.target.value })}
                  rows={2}
                />
                <Button 
                  className="w-full" 
                  variant="outline"
                  onClick={handleRequestChanges}
                  disabled={actionLoading}
                >
                  <AlertTriangle className="h-4 w-4 mr-2" />
                  Request Changes
                </Button>
              </div>

              {/* Reject */}
              <div className="space-y-2">
                <Textarea
                  placeholder="Reason for rejection..."
                  value={editData.rejection_reason}
                  onChange={(e) => setEditData({ ...editData, rejection_reason: e.target.value })}
                  rows={2}
                />
                <Button 
                  className="w-full" 
                  variant="destructive"
                  onClick={handleReject}
                  disabled={actionLoading}
                >
                  <XCircle className="h-4 w-4 mr-2" />
                  Reject Request
                </Button>
              </div>
            </div>
          )}

          {/* Payment Status (for approved) */}
          {request.status === 'approved' && (
            <div className="bg-white rounded-xl border border-slate-100 p-6">
              <h2 className="text-lg font-semibold text-slate-900 mb-4">Payment Status</h2>
              <div className={`p-3 rounded-lg text-center ${
                request.payment_status === 'paid' 
                  ? 'bg-emerald-50 text-emerald-700' 
                  : 'bg-amber-50 text-amber-700'
              }`}>
                {request.payment_status === 'paid' ? 'Payment Received' : 'Payment Pending'}
              </div>
              {request.payment_status !== 'paid' && (
                <Button 
                  className="w-full mt-3"
                  variant="outline"
                  onClick={() => handleUpdateStatus('approved', { 
                    payment_status: 'paid', 
                    payment_date: new Date().toISOString() 
                  })}
                >
                  Mark as Paid
                </Button>
              )}
            </div>
          )}

          {/* Rejection/Changes Info */}
          {request.status === 'rejected' && request.rejection_reason && (
            <div className="bg-red-50 rounded-xl border border-red-200 p-4">
              <p className="text-sm font-medium text-red-700 mb-1">Rejection Reason</p>
              <p className="text-sm text-red-600">{request.rejection_reason}</p>
            </div>
          )}

          {request.status === 'changes_requested' && request.changes_requested_note && (
            <div className="bg-orange-50 rounded-xl border border-orange-200 p-4">
              <p className="text-sm font-medium text-orange-700 mb-1">Changes Requested</p>
              <p className="text-sm text-orange-600">{request.changes_requested_note}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminAMCRequestDetail;
