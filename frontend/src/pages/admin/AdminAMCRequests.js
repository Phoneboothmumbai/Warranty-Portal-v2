import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  FileText, Clock, CheckCircle2, XCircle, AlertTriangle,
  Calendar, Package, ChevronRight, Filter, Search, RefreshCw,
  Building2, DollarSign, Eye
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const statusConfig = {
  pending_review: { label: 'Pending Review', color: 'bg-amber-100 text-amber-700', icon: Clock },
  under_review: { label: 'Under Review', color: 'bg-blue-100 text-blue-700', icon: RefreshCw },
  approved: { label: 'Approved', color: 'bg-emerald-100 text-emerald-700', icon: CheckCircle2 },
  rejected: { label: 'Rejected', color: 'bg-red-100 text-red-700', icon: XCircle },
  changes_requested: { label: 'Changes Requested', color: 'bg-orange-100 text-orange-700', icon: AlertTriangle },
  cancelled: { label: 'Cancelled', color: 'bg-slate-100 text-slate-600', icon: XCircle }
};

const amcTypeLabels = {
  comprehensive: 'Comprehensive',
  non_comprehensive: 'Non-Comprehensive',
  on_call: 'On-Call Basis'
};

const AdminAMCRequests = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  const fetchRequests = useCallback(async () => {
    try {
      setLoading(true);
      const params = {};
      if (statusFilter) params.status = statusFilter;
      
      const res = await axios.get(`${API}/admin/amc-requests`, {
        params,
        headers: { Authorization: `Bearer ${token}` }
      });
      setRequests(res.data);
    } catch (error) {
      toast.error('Failed to load AMC requests');
    } finally {
      setLoading(false);
    }
  }, [token, statusFilter]);

  useEffect(() => {
    fetchRequests();
  }, [fetchRequests]);

  const filteredRequests = requests.filter(req => {
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        req.company_name?.toLowerCase().includes(query) ||
        req.amc_type?.toLowerCase().includes(query) ||
        req.requested_by_name?.toLowerCase().includes(query)
      );
    }
    return true;
  });

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric', month: 'short', year: 'numeric'
    });
  };

  const formatCurrency = (amount) => {
    if (!amount) return '-';
    return `₹${amount.toLocaleString('en-IN')}`;
  };

  const pendingCount = requests.filter(r => r.status === 'pending_review').length;
  const underReviewCount = requests.filter(r => r.status === 'under_review').length;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="admin-amc-requests">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">AMC Requests</h1>
          <p className="text-slate-500">Review and manage AMC requests from companies</p>
        </div>
        {pendingCount > 0 && (
          <div className="flex items-center gap-2 px-3 py-2 bg-amber-50 border border-amber-200 rounded-lg">
            <Clock className="h-4 w-4 text-amber-600" />
            <span className="text-sm font-medium text-amber-700">
              {pendingCount} pending review
            </span>
          </div>
        )}
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div 
          className={`bg-white rounded-xl border p-4 cursor-pointer transition-colors ${
            statusFilter === '' ? 'border-blue-500 bg-blue-50' : 'border-slate-100 hover:border-slate-200'
          }`}
          onClick={() => setStatusFilter('')}
        >
          <p className="text-sm text-slate-500">All Requests</p>
          <p className="text-2xl font-semibold text-slate-900">{requests.length}</p>
        </div>
        <div 
          className={`bg-white rounded-xl border p-4 cursor-pointer transition-colors ${
            statusFilter === 'pending_review' ? 'border-amber-500 bg-amber-50' : 'border-slate-100 hover:border-slate-200'
          }`}
          onClick={() => setStatusFilter('pending_review')}
        >
          <p className="text-sm text-slate-500">Pending</p>
          <p className="text-2xl font-semibold text-amber-600">{pendingCount}</p>
        </div>
        <div 
          className={`bg-white rounded-xl border p-4 cursor-pointer transition-colors ${
            statusFilter === 'under_review' ? 'border-blue-500 bg-blue-50' : 'border-slate-100 hover:border-slate-200'
          }`}
          onClick={() => setStatusFilter('under_review')}
        >
          <p className="text-sm text-slate-500">Under Review</p>
          <p className="text-2xl font-semibold text-blue-600">{underReviewCount}</p>
        </div>
        <div 
          className={`bg-white rounded-xl border p-4 cursor-pointer transition-colors ${
            statusFilter === 'approved' ? 'border-emerald-500 bg-emerald-50' : 'border-slate-100 hover:border-slate-200'
          }`}
          onClick={() => setStatusFilter('approved')}
        >
          <p className="text-sm text-slate-500">Approved</p>
          <p className="text-2xl font-semibold text-emerald-600">
            {requests.filter(r => r.status === 'approved').length}
          </p>
        </div>
        <div 
          className={`bg-white rounded-xl border p-4 cursor-pointer transition-colors ${
            statusFilter === 'rejected' ? 'border-red-500 bg-red-50' : 'border-slate-100 hover:border-slate-200'
          }`}
          onClick={() => setStatusFilter('rejected')}
        >
          <p className="text-sm text-slate-500">Rejected</p>
          <p className="text-2xl font-semibold text-red-600">
            {requests.filter(r => r.status === 'rejected').length}
          </p>
        </div>
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
        <Input
          placeholder="Search by company, type..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Requests Table */}
      {filteredRequests.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-100 p-12 text-center">
          <FileText className="h-12 w-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-900 mb-2">No AMC Requests</h3>
          <p className="text-slate-500">
            {statusFilter ? `No requests with status "${statusConfig[statusFilter]?.label}"` : 'No AMC requests yet'}
          </p>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-100 overflow-hidden">
          <table className="w-full">
            <thead className="bg-slate-50 border-b border-slate-100">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Company</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">AMC Type</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Devices</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Duration</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Quoted</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Status</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-slate-500 uppercase">Submitted</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-slate-500 uppercase">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredRequests.map((request) => {
                const status = statusConfig[request.status] || statusConfig.pending_review;
                const StatusIcon = status.icon;
                
                return (
                  <tr 
                    key={request.id}
                    className="hover:bg-slate-50 cursor-pointer"
                    onClick={() => navigate(`/admin/amc-requests/${request.id}`)}
                  >
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <Building2 className="h-4 w-4 text-slate-400" />
                        <div>
                          <p className="font-medium text-slate-900">{request.company_name}</p>
                          <p className="text-xs text-slate-500">by {request.requested_by_name}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-700">
                        {amcTypeLabels[request.amc_type] || request.amc_type}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-700">{request.device_count}</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-700">{request.duration_months} months</span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm font-medium text-slate-700">
                        {formatCurrency(request.total_price)}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${status.color}`}>
                        <StatusIcon className="h-3 w-3" />
                        {status.label}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <span className="text-sm text-slate-500">{formatDate(request.created_at)}</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <Button variant="ghost" size="sm">
                        <Eye className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default AdminAMCRequests;
