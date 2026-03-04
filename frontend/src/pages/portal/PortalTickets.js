import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import { Wrench, Search, ChevronLeft, ChevronRight, Filter, AlertTriangle } from 'lucide-react';
import { Input } from '../../components/ui/input';

const API = process.env.REACT_APP_BACKEND_URL;

const priorityBadge = (p) => {
  const map = {
    critical: 'bg-red-50 text-red-700 border-red-200',
    high: 'bg-orange-50 text-orange-700 border-orange-200',
    medium: 'bg-blue-50 text-blue-700 border-blue-200',
    low: 'bg-green-50 text-green-700 border-green-200',
  };
  return map[p] || 'bg-slate-50 text-slate-600 border-slate-200';
};

export default function PortalTickets() {
  const { tenant, tenantCode } = useTenant();
  const [tickets, setTickets] = useState([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [page, setPage] = useState(1);
  const [loading, setLoading] = useState(true);
  const primary = tenant?.portal_theme?.primary_color || tenant?.accent_color || '#0F62FE';
  const limit = 25;

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams({ page, limit });
        if (statusFilter !== 'all') params.set('status', statusFilter);
        if (search) params.set('search', search);
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/tickets?${params}`);
        if (res.ok) {
          const d = await res.json();
          setTickets(d.tickets || []);
          setTotal(d.total || 0);
        }
      } catch { /* */ }
      finally { setLoading(false); }
    })();
  }, [tenantCode, page, statusFilter, search]);

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="space-y-4" data-testid="portal-tickets">
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-bold text-slate-900">Support Tickets</h1>
          <p className="text-sm text-slate-500">{total} ticket{total !== 1 ? 's' : ''} total</p>
        </div>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
            <Input className="pl-9 w-56" placeholder="Search tickets..."
              value={search} onChange={e => { setSearch(e.target.value); setPage(1); }}
              data-testid="portal-ticket-search" />
          </div>
          <div className="flex items-center border rounded-lg overflow-hidden">
            {['all', 'open', 'closed'].map(s => (
              <button key={s} onClick={() => { setStatusFilter(s); setPage(1); }}
                className={`px-3 py-2 text-xs font-medium capitalize transition-colors ${
                  statusFilter === s ? 'text-white' : 'text-slate-600 hover:bg-slate-50'
                }`}
                style={statusFilter === s ? { backgroundColor: primary } : {}}
                data-testid={`portal-ticket-filter-${s}`}>
                {s}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-3 border-t-transparent rounded-full animate-spin" style={{ borderColor: primary }} />
        </div>
      ) : tickets.length > 0 ? (
        <>
          <div className="bg-white rounded-lg border overflow-hidden">
            <table className="w-full text-sm">
              <thead><tr className="border-b bg-slate-50">
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Ticket #</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Subject</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 hidden md:table-cell">Topic</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Status</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Priority</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500 hidden lg:table-cell">Assigned</th>
                <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Created</th>
              </tr></thead>
              <tbody>
                {tickets.map(t => (
                  <tr key={t.id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                    <td className="py-3 px-4 font-mono text-xs text-slate-500">#{t.ticket_number}</td>
                    <td className="py-3 px-4">
                      <span className="font-medium text-slate-700">{t.subject}</span>
                      {t.sla_breached && (
                        <span className="ml-2 inline-flex items-center gap-0.5 text-[10px] text-red-600">
                          <AlertTriangle className="w-3 h-3" />SLA
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500 hidden md:table-cell">{t.help_topic || '-'}</td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs border font-medium ${
                        t.is_open ? 'bg-amber-50 text-amber-700 border-amber-200' : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      }`}>{t.status}</span>
                    </td>
                    <td className="py-3 px-4">
                      <span className={`px-2 py-0.5 rounded-full text-xs border capitalize ${priorityBadge(t.priority)}`}>{t.priority}</span>
                    </td>
                    <td className="py-3 px-4 text-xs text-slate-500 hidden lg:table-cell">{t.assigned_to}</td>
                    <td className="py-3 px-4 text-xs text-slate-400">{(t.created_at || '').slice(0, 10)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between">
              <p className="text-xs text-slate-500">Page {page} of {totalPages}</p>
              <div className="flex items-center gap-1">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page === 1}
                  className="p-1.5 rounded border text-slate-500 hover:bg-slate-50 disabled:opacity-30" data-testid="portal-tickets-prev">
                  <ChevronLeft className="w-4 h-4" />
                </button>
                <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page === totalPages}
                  className="p-1.5 rounded border text-slate-500 hover:bg-slate-50 disabled:opacity-30" data-testid="portal-tickets-next">
                  <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          )}
        </>
      ) : (
        <div className="bg-white rounded-lg border p-12 text-center">
          <Wrench className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500">{search ? 'No tickets match your search' : 'No support tickets found'}</p>
        </div>
      )}
    </div>
  );
}
