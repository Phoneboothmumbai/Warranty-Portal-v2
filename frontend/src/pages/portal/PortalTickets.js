import { useState, useEffect } from 'react';
import { useTenant } from '../../context/TenantContext';
import { Wrench, Clock, Search } from 'lucide-react';
import { Input } from '../../components/ui/input';

const API = process.env.REACT_APP_BACKEND_URL;

const statusColor = (isOpen) => isOpen
  ? 'bg-amber-50 text-amber-700 border-amber-200'
  : 'bg-emerald-50 text-emerald-700 border-emerald-200';

export default function PortalTickets() {
  const { tenant, hdrs, tenantCode } = useTenant();
  const [tickets, setTickets] = useState([]);
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);
  const primary = tenant?.portal_theme?.primary_color || '#0F62FE';

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch(`${API}/api/portal/tenant/${tenantCode}/analytics?days=365`);
        if (res.ok) {
          const d = await res.json();
          setTickets(d.recent_tickets || []);
        }
      } catch { /* */ }
      finally { setLoading(false); }
    })();
  }, [tenantCode]);

  const filtered = tickets.filter(t =>
    (t.subject || '').toLowerCase().includes(search.toLowerCase()) ||
    (t.ticket_number || '').includes(search)
  );

  return (
    <div className="space-y-4" data-testid="portal-tickets">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold text-slate-900">Support Tickets</h1>
        <div className="relative w-64">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <Input className="pl-9" placeholder="Search tickets..." value={search} onChange={e => setSearch(e.target.value)} data-testid="portal-ticket-search" />
        </div>
      </div>
      {loading ? (
        <div className="flex items-center justify-center h-40">
          <div className="w-6 h-6 border-3 border-t-transparent rounded-full animate-spin" style={{ borderColor: primary }} />
        </div>
      ) : filtered.length > 0 ? (
        <div className="bg-white rounded-lg border overflow-hidden">
          <table className="w-full text-sm">
            <thead><tr className="border-b bg-slate-50">
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Ticket #</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Subject</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Status</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Priority</th>
              <th className="text-left py-3 px-4 text-xs font-medium text-slate-500">Created</th>
            </tr></thead>
            <tbody>
              {filtered.map(t => (
                <tr key={t.id} className="border-b border-slate-50 hover:bg-slate-50">
                  <td className="py-3 px-4 font-mono text-xs text-slate-500">#{t.ticket_number}</td>
                  <td className="py-3 px-4 font-medium text-slate-700">{t.subject}</td>
                  <td className="py-3 px-4"><span className={`px-2 py-0.5 rounded-full text-xs border ${statusColor(t.is_open)}`}>{t.status}</span></td>
                  <td className="py-3 px-4 text-xs capitalize text-slate-600">{t.priority}</td>
                  <td className="py-3 px-4 text-xs text-slate-400">{t.created}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg border p-12 text-center">
          <Wrench className="w-10 h-10 text-slate-300 mx-auto mb-3" />
          <p className="text-sm text-slate-500">No support tickets found</p>
        </div>
      )}
    </div>
  );
}
