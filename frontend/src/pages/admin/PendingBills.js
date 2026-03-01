import { useState, useEffect, useCallback } from 'react';
import {
  FileText, Clock, CheckCircle, Search, Hash, Building2,
  Loader2, ChevronRight, X, Receipt, IndianRupee, User, Package
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { useAuth } from '../../context/AuthContext';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function PendingBills() {
  const { token } = useAuth();
  const [bills, setBills] = useState([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [expandedId, setExpandedId] = useState(null);
  const [billModal, setBillModal] = useState(null);
  const [billNumber, setBillNumber] = useState('');
  const [completing, setCompleting] = useState(false);

  const hdrs = useCallback(() => ({
    Authorization: `Bearer ${token}`,
    'Content-Type': 'application/json',
  }), [token]);

  const fetchBills = useCallback(async () => {
    try {
      const params = statusFilter ? `?status=${statusFilter}` : '';
      const res = await fetch(`${API}/api/admin/pending-bills${params}`, { headers: hdrs() });
      if (res.ok) {
        const d = await res.json();
        setBills(d.bills || []);
      }
    } catch { toast.error('Failed to load bills'); }
    finally { setLoading(false); }
  }, [token, statusFilter, hdrs]);

  useEffect(() => { fetchBills(); }, [fetchBills]);

  const completeBill = async () => {
    if (!billModal || !billNumber.trim()) { toast.error('Bill/Invoice number is required'); return; }
    setCompleting(true);
    try {
      const res = await fetch(`${API}/api/admin/pending-bills/${billModal.id}/complete`, {
        method: 'PUT', headers: hdrs(),
        body: JSON.stringify({ bill_number: billNumber }),
      });
      if (res.ok) {
        toast.success(`Bill marked as done. Invoice: ${billNumber}`);
        setBillModal(null); setBillNumber('');
        fetchBills();
      } else {
        const d = await res.json();
        toast.error(d.detail || 'Failed');
      }
    } catch { toast.error('Network error'); }
    finally { setCompleting(false); }
  };

  const pendingCount = bills.filter(b => b.status === 'pending').length;
  const billedCount = bills.filter(b => b.status === 'billed').length;
  const totalPendingAmt = bills.filter(b => b.status === 'pending').reduce((s, b) => s + (b.grand_total || 0), 0);

  if (loading) return <div className="flex justify-center py-16"><Loader2 className="w-6 h-6 animate-spin text-slate-400" /></div>;

  return (
    <div className="space-y-6" data-testid="pending-bills-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Pending Bills</h1>
          <p className="text-slate-500 mt-1">Parts consumed during field visits awaiting invoicing</p>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4" data-testid="stat-pending">
          <p className="text-xs text-amber-600 font-medium">Pending</p>
          <p className="text-2xl font-bold text-amber-800 mt-1">{pendingCount}</p>
        </div>
        <div className="bg-green-50 border border-green-200 rounded-xl p-4" data-testid="stat-billed">
          <p className="text-xs text-green-600 font-medium">Billed</p>
          <p className="text-2xl font-bold text-green-800 mt-1">{billedCount}</p>
        </div>
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4" data-testid="stat-amount">
          <p className="text-xs text-blue-600 font-medium">Pending Amount</p>
          <p className="text-2xl font-bold text-blue-800 mt-1 font-mono">{totalPendingAmt.toFixed(2)}</p>
        </div>
      </div>

      {/* Filter */}
      <div className="flex gap-2">
        {[
          { key: '', label: 'All' },
          { key: 'pending', label: 'Pending', color: 'bg-amber-50 text-amber-700 border-amber-200' },
          { key: 'billed', label: 'Billed', color: 'bg-green-50 text-green-700 border-green-200' },
        ].map(f => (
          <button key={f.key}
            onClick={() => setStatusFilter(statusFilter === f.key ? '' : f.key)}
            className={`px-3 py-1.5 rounded-full text-xs font-medium border transition-colors ${
              statusFilter === f.key
                ? (f.color || 'bg-slate-900 text-white border-slate-900')
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
            data-testid={`bill-filter-${f.key || 'all'}`}
          >{f.label}</button>
        ))}
      </div>

      {/* Bills list */}
      {bills.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border">
          <Receipt className="h-12 w-12 mx-auto text-slate-300 mb-4" />
          <p className="text-slate-500">{statusFilter ? `No ${statusFilter} bills` : 'No pending bills yet'}</p>
          <p className="text-xs text-slate-400 mt-1">Bills are auto-created when engineers use parts during visits</p>
        </div>
      ) : (
        <div className="space-y-3">
          {bills.map(bill => {
            const isExpanded = expandedId === bill.id;
            const isPending = bill.status === 'pending';

            return (
              <div key={bill.id} className={`bg-white rounded-xl border overflow-hidden ${isPending ? 'border-l-4 border-l-amber-400' : ''}`} data-testid={`bill-${bill.id}`}>
                {/* Row */}
                <div className="px-5 py-4 flex items-center gap-4 cursor-pointer hover:bg-slate-50" onClick={() => setExpandedId(isExpanded ? null : bill.id)}>
                  {isPending ? <Clock className="w-5 h-5 text-amber-500 shrink-0" /> : <CheckCircle className="w-5 h-5 text-green-500 shrink-0" />}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-mono text-sm font-bold text-blue-600">#{bill.ticket_number}</span>
                      <span className={`text-[10px] px-2 py-0.5 rounded-full font-medium ${isPending ? 'bg-amber-50 text-amber-700 border border-amber-200' : 'bg-green-50 text-green-700 border border-green-200'}`}>
                        {isPending ? 'Pending' : 'Billed'}
                      </span>
                      {bill.bill_number && <span className="text-[10px] bg-blue-50 text-blue-600 px-2 py-0.5 rounded-full">INV: {bill.bill_number}</span>}
                      <span className="text-xs text-slate-400">{bill.items?.length || 0} item{(bill.items?.length || 0) !== 1 ? 's' : ''} &middot; {bill.visit_count || 1} visit{(bill.visit_count || 1) !== 1 ? 's' : ''}</span>
                    </div>
                    <p className="text-sm text-slate-600 mt-0.5 flex items-center gap-1"><Building2 className="w-3 h-3" />{bill.company_name}</p>
                    {bill.subject && <p className="text-xs text-slate-400 truncate">{bill.subject}</p>}
                  </div>
                  <div className="text-right shrink-0">
                    <p className="font-mono text-sm font-bold text-slate-900">{bill.grand_total?.toFixed(2)}</p>
                    <p className="text-[10px] text-slate-400">{bill.created_at ? new Date(bill.created_at).toLocaleDateString() : ''}</p>
                  </div>
                  <ChevronRight className={`w-4 h-4 text-slate-400 transition-transform ${isExpanded ? 'rotate-90' : ''}`} />
                </div>

                {/* Expanded */}
                {isExpanded && (
                  <div className="border-t px-5 py-4 bg-slate-50/50 space-y-4">
                    {/* Items */}
                    <div className="bg-white rounded-lg border overflow-hidden">
                      <table className="w-full text-xs">
                        <thead className="bg-slate-50">
                          <tr>
                            <th className="text-left px-3 py-2 font-medium text-slate-500">Part</th>
                            <th className="text-left px-2 py-2 font-medium text-slate-500">Added By</th>
                            <th className="text-center px-2 py-2 font-medium text-slate-500">Qty</th>
                            <th className="text-right px-2 py-2 font-medium text-slate-500">Price</th>
                            <th className="text-right px-2 py-2 font-medium text-slate-500">GST</th>
                            <th className="text-right px-3 py-2 font-medium text-slate-500">Total</th>
                          </tr>
                        </thead>
                        <tbody>
                          {(bill.items || []).map((item, i) => (
                            <tr key={i} className="border-t">
                              <td className="px-3 py-2 font-medium text-slate-700">{item.product_name}</td>
                              <td className="px-2 py-2 text-slate-400">{item.added_by}</td>
                              <td className="text-center px-2 py-2">{item.quantity}</td>
                              <td className="text-right px-2 py-2 font-mono">{item.unit_price?.toFixed(2)}</td>
                              <td className="text-right px-2 py-2 font-mono">{item.gst_amount?.toFixed(2)}</td>
                              <td className="text-right px-3 py-2 font-mono font-medium">{item.line_total?.toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                        <tfoot className="border-t bg-slate-50">
                          <tr>
                            <td colSpan="4"></td>
                            <td className="text-right px-2 py-2 font-medium text-slate-500">Subtotal</td>
                            <td className="text-right px-3 py-2 font-mono">{bill.subtotal?.toFixed(2)}</td>
                          </tr>
                          <tr>
                            <td colSpan="4"></td>
                            <td className="text-right px-2 py-1 font-medium text-slate-500">GST</td>
                            <td className="text-right px-3 py-1 font-mono">{bill.total_gst?.toFixed(2)}</td>
                          </tr>
                          <tr>
                            <td colSpan="4"></td>
                            <td className="text-right px-2 py-2 font-semibold text-slate-700">Grand Total</td>
                            <td className="text-right px-3 py-2 font-mono text-sm font-bold">{bill.grand_total?.toFixed(2)}</td>
                          </tr>
                        </tfoot>
                      </table>
                    </div>

                    {/* Meta */}
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div className="bg-white rounded-lg border p-3">
                        <p className="text-slate-400 mb-0.5">Contact</p>
                        <p className="font-medium text-slate-700">{bill.contact_name || '-'}</p>
                        {bill.contact_email && <p className="text-slate-400">{bill.contact_email}</p>}
                      </div>
                      <div className="bg-white rounded-lg border p-3">
                        <p className="text-slate-400 mb-0.5">Created</p>
                        <p className="font-medium text-slate-700">{bill.created_at ? new Date(bill.created_at).toLocaleString() : '-'}</p>
                      </div>
                      <div className="bg-white rounded-lg border p-3">
                        <p className="text-slate-400 mb-0.5">Visits</p>
                        <p className="font-medium text-slate-700">{bill.visit_count || 1} visit{(bill.visit_count || 1) !== 1 ? 's' : ''}</p>
                      </div>
                    </div>

                    {bill.billed_at && (
                      <div className="bg-green-50 border border-green-200 rounded-lg p-3 text-xs">
                        <p className="text-green-700 font-medium">Billed by {bill.billed_by} on {new Date(bill.billed_at).toLocaleString()}</p>
                        <p className="text-green-600 font-mono font-bold mt-0.5">Invoice: {bill.bill_number}</p>
                      </div>
                    )}

                    {/* Action */}
                    {isPending && (
                      <div className="flex justify-end">
                        <Button className="bg-green-600 hover:bg-green-700 text-white gap-1.5" onClick={(e) => { e.stopPropagation(); setBillModal(bill); setBillNumber(''); }} data-testid={`mark-billed-${bill.id}`}>
                          <CheckCircle className="w-3.5 h-3.5" /> Mark as Done
                        </Button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Bill Number Dialog */}
      <Dialog open={!!billModal} onOpenChange={() => setBillModal(null)}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Complete Bill — #{billModal?.ticket_number}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="bg-slate-50 rounded-lg p-3 text-xs">
              <p className="text-slate-500">{billModal?.company_name}</p>
              <p className="font-mono font-bold text-lg text-slate-900 mt-1">{billModal?.grand_total?.toFixed(2)}</p>
              <p className="text-slate-400">{billModal?.items?.length} items</p>
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700 block mb-1.5">Bill / Invoice Number *</label>
              <input className="w-full border rounded-lg px-3 py-2.5 text-sm font-mono" placeholder="e.g., INV-2026-0001"
                value={billNumber} onChange={e => setBillNumber(e.target.value)} autoFocus data-testid="bill-number-input" />
            </div>
            <div className="flex gap-2 justify-end pt-2">
              <Button variant="outline" onClick={() => setBillModal(null)}>Cancel</Button>
              <Button onClick={completeBill} disabled={completing || !billNumber.trim()} className="bg-green-600 hover:bg-green-700 text-white" data-testid="confirm-bill-btn">
                {completing ? <Loader2 className="w-4 h-4 animate-spin mr-1" /> : <CheckCircle className="w-3.5 h-3.5 mr-1" />}
                Confirm
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
