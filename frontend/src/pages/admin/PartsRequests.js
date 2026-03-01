import { useState, useEffect, useCallback } from 'react';
import {
  Package, Search, Filter, ExternalLink, FileText, Clock,
  CheckCircle, Truck, AlertCircle, Loader2, ChevronRight, User
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  pending: { label: 'Pending', color: 'bg-amber-50 text-amber-700 border-amber-200', icon: Clock },
  quoted: { label: 'Quoted', color: 'bg-blue-50 text-blue-700 border-blue-200', icon: FileText },
  approved: { label: 'Approved', color: 'bg-green-50 text-green-700 border-green-200', icon: CheckCircle },
  procured: { label: 'Procured', color: 'bg-purple-50 text-purple-700 border-purple-200', icon: Package },
  delivered: { label: 'Delivered', color: 'bg-teal-50 text-teal-700 border-teal-200', icon: Truck },
};

const STATUSES = ['pending', 'quoted', 'approved', 'procured', 'delivered'];

export default function PartsRequests() {
  const { token } = useAuth();
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [updating, setUpdating] = useState(null);

  const hdrs = useCallback(() => ({
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }), [token]);

  const fetchRequests = useCallback(async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const res = await fetch(`${API}/api/admin/parts-requests${params}`, { headers: hdrs() });
      if (res.ok) {
        const data = await res.json();
        setRequests(data.parts_requests || []);
      }
    } catch { toast.error('Failed to load parts requests'); }
    finally { setLoading(false); }
  }, [token, statusFilter, hdrs]);

  useEffect(() => { fetchRequests(); }, [fetchRequests]);

  const updateStatus = async (requestId, newStatus) => {
    setUpdating(requestId);
    try {
      const res = await fetch(`${API}/api/admin/parts-requests/${requestId}/status?status=${newStatus}`, {
        method: 'PUT', headers: hdrs(),
      });
      if (res.ok) {
        toast.success(`Status updated to "${newStatus}"`);
        fetchRequests();
      } else {
        const d = await res.json();
        toast.error(d.detail || 'Failed to update');
      }
    } catch { toast.error('Network error'); }
    finally { setUpdating(null); }
  };

  const getNextStatus = (current) => {
    const idx = STATUSES.indexOf(current);
    return idx < STATUSES.length - 1 ? STATUSES[idx + 1] : null;
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <Loader2 className="w-6 h-6 animate-spin text-slate-400" />
    </div>
  );

  return (
    <div className="space-y-6" data-testid="parts-requests-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Parts Requests</h1>
          <p className="text-slate-500 mt-1">Manage parts requested by engineers during field visits</p>
        </div>
        <Badge variant="secondary" className="text-sm">{requests.length} request{requests.length !== 1 ? 's' : ''}</Badge>
      </div>

      {/* Status filter pills */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setStatusFilter('')}
          className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${!statusFilter ? 'bg-slate-900 text-white border-slate-900' : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}
          data-testid="filter-all"
        >All</button>
        {STATUSES.map(s => {
          const cfg = STATUS_CONFIG[s];
          return (
            <button key={s}
              onClick={() => setStatusFilter(statusFilter === s ? '' : s)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${statusFilter === s ? `${cfg.color} border-current` : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'}`}
              data-testid={`filter-${s}`}
            >{cfg.label}</button>
          );
        })}
      </div>

      {/* Requests list */}
      {requests.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border">
          <Package className="h-12 w-12 mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">{statusFilter ? `No ${statusFilter} requests` : 'No parts requests yet'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {requests.map(pr => {
            const cfg = STATUS_CONFIG[pr.status] || STATUS_CONFIG.pending;
            const StatusIcon = cfg.icon;
            const isExpanded = expandedId === pr.id;
            const nextStatus = getNextStatus(pr.status);

            return (
              <div key={pr.id} className="bg-white rounded-xl border overflow-hidden" data-testid={`pr-${pr.id}`}>
                {/* Header row */}
                <div
                  className="px-5 py-4 flex items-center gap-4 cursor-pointer hover:bg-slate-50 transition-colors"
                  onClick={() => setExpandedId(isExpanded ? null : pr.id)}
                >
                  <StatusIcon className="w-5 h-5 text-slate-400 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-sm font-bold text-blue-600">#{pr.ticket_number}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full border font-medium ${cfg.color}`}>{cfg.label}</span>
                      <span className="text-xs text-slate-400">{pr.items?.length || 0} item{(pr.items?.length || 0) !== 1 ? 's' : ''}</span>
                    </div>
                    <p className="text-sm text-slate-600 mt-0.5">{pr.company_name}</p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-mono text-sm font-semibold text-slate-900">{pr.grand_total?.toFixed(2)}</p>
                    <p className="text-[10px] text-slate-400 flex items-center gap-1 justify-end">
                      <User className="w-3 h-3" />{pr.engineer_name}
                    </p>
                  </div>
                  <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                </div>

                {/* Expanded details */}
                {isExpanded && (
                  <div className="border-t px-5 py-4 bg-slate-50/50 space-y-4">
                    {/* Items table */}
                    <div className="bg-white rounded-lg border overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-slate-50">
                          <tr>
                            <th className="text-left px-3 py-2 font-medium text-slate-500">Part</th>
                            <th className="text-center px-2 py-2 font-medium text-slate-500">Qty</th>
                            <th className="text-right px-2 py-2 font-medium text-slate-500">Unit Price</th>
                            <th className="text-right px-2 py-2 font-medium text-slate-500">GST</th>
                            <th className="text-right px-3 py-2 font-medium text-slate-500">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(pr.items || []).map((item, i) => (
                            <tr key={i} className="border-t">
                              <td className="px-3 py-2 font-medium text-slate-700">{item.product_name}</td>
                              <td className="text-center px-2 py-2">{item.quantity}</td>
                              <td className="text-right px-2 py-2 font-mono">{item.unit_price?.toFixed(2)}</td>
                              <td className="text-right px-2 py-2 font-mono">{item.gst_amount?.toFixed(2)}</td>
                              <td className="text-right px-3 py-2 font-mono font-medium">{item.line_total?.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot className="border-t bg-slate-50">
                          <tr>
                            <td colSpan="3"></td>
                            <td className="text-right px-2 py-2 text-xs font-medium text-slate-500">Subtotal</td>
                            <td className="text-right px-3 py-2 font-mono text-xs">{pr.subtotal?.toFixed(2)}</td>
                          </tr>
                          <tr>
                            <td colSpan="3"></td>
                            <td className="text-right px-2 py-1 text-xs font-medium text-slate-500">GST</td>
                            <td className="text-right px-3 py-1 font-mono text-xs">{pr.total_gst?.toFixed(2)}</td>
                          </tr>
                          <tr>
                            <td colSpan="3"></td>
                            <td className="text-right px-2 py-2 text-xs font-semibold text-slate-700">Grand Total</td>
                            <td className="text-right px-3 py-2 font-mono text-sm font-bold text-slate-900">{pr.grand_total?.toFixed(2)}</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>

                    {/* Meta info */}
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div className="bg-white rounded-lg border p-3">
                        <p className="text-slate-400 mb-0.5">Engineer</p>
                        <p className="font-medium text-slate-700">{pr.engineer_name}</p>
                      </div>
                      <div className="bg-white rounded-lg border p-3">
                        <p className="text-slate-400 mb-0.5">Requested</p>
                        <p className="font-medium text-slate-700">{pr.created_at ? new Date(pr.created_at).toLocaleString() : '-'}</p>
                      </div>
                      <div className="bg-white rounded-lg border p-3">
                        <p className="text-slate-400 mb-0.5">Quotation</p>
                        <p className="font-medium text-blue-600">{pr.quotation_id ? 'Linked' : 'N/A'}</p>
                      </div>
                    </div>

                    {pr.notes && (
                      <div className="bg-white rounded-lg border p-3 text-xs">
                        <p className="text-slate-400 mb-0.5">Notes</p>
                        <p className="text-slate-700">{pr.notes}</p>
                      </div>
                    )}

                    {/* Action buttons */}
                    <div className="flex gap-2 justify-end">
                      {pr.quotation_id && (
                        <Button size="sm" variant="outline" className="gap-1.5" onClick={() => window.open(`/admin/quotations`, '_blank')} data-testid={`view-quotation-${pr.id}`}>
                          <ExternalLink className="w-3.5 h-3.5" /> View Quotation
                        </Button>
                      )}
                      {nextStatus && (
                        <Button
                          size="sm"
                          className="bg-[#0F62FE] hover:bg-[#0043CE] text-white gap-1.5"
                          disabled={updating === pr.id}
                          onClick={(e) => { e.stopPropagation(); updateStatus(pr.id, nextStatus); }}
                          data-testid={`advance-${pr.id}`}
                        >
                          {updating === pr.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <CheckCircle className="w-3.5 h-3.5" />}
                          Mark as {STATUS_CONFIG[nextStatus]?.label}
                        </Button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
