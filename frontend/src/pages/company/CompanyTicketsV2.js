import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, Ticket, Clock, CheckCircle } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

export default function CompanyTicketsV2() {
  const navigate = useNavigate();
  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');

  const fetchTickets = useCallback(async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('company_token');
      const params = new URLSearchParams();
      if (search) params.set('search', search);
      const res = await fetch(`${API}/api/ticketing/tickets?${params}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setTickets(data.tickets || []);
      }
    } catch { toast.error('Failed to load tickets'); }
    finally { setLoading(false); }
  }, [search]);

  useEffect(() => { fetchTickets(); }, [fetchTickets]);

  const priorityColors = {
    low: 'bg-slate-100 text-slate-600',
    medium: 'bg-blue-100 text-blue-600',
    high: 'bg-orange-100 text-orange-600',
    critical: 'bg-red-100 text-red-600',
  };

  const openCount = tickets.filter(t => t.is_open).length;
  const closedCount = tickets.filter(t => !t.is_open).length;

  return (
    <div className="space-y-6" data-testid="company-tickets-page">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Support Tickets</h1>
          <p className="text-sm text-slate-500 mt-1">Track your service requests</p>
        </div>
      </div>

      <div className="grid grid-cols-3 gap-4">
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Ticket className="w-5 h-5 text-blue-500" />
            <div><p className="text-xs text-slate-500">Open</p><p className="text-xl font-semibold">{openCount}</p></div>
          </div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2">
            <CheckCircle className="w-5 h-5 text-green-500" />
            <div><p className="text-xs text-slate-500">Closed</p><p className="text-xl font-semibold">{closedCount}</p></div>
          </div>
        </div>
        <div className="bg-white border rounded-lg p-4">
          <div className="flex items-center gap-2">
            <Clock className="w-5 h-5 text-slate-500" />
            <div><p className="text-xs text-slate-500">Total</p><p className="text-xl font-semibold">{tickets.length}</p></div>
          </div>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <Input className="pl-9" placeholder="Search tickets..." value={search} onChange={e => setSearch(e.target.value)} data-testid="search-tickets" />
      </div>

      <div className="bg-white border rounded-lg overflow-hidden" data-testid="tickets-list">
        {loading ? (
          <div className="text-center py-12 text-slate-400">Loading...</div>
        ) : tickets.length === 0 ? (
          <div className="text-center py-12 text-slate-400">No tickets found</div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Ticket</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Subject</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Status</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Priority</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Created</th>
              </tr>
            </thead>
            <tbody>
              {tickets.map(t => (
                <tr key={t.id} className="border-b hover:bg-slate-50 cursor-pointer" onClick={() => navigate(`/company/tickets/${t.id}`)} data-testid={`ticket-${t.ticket_number}`}>
                  <td className="px-4 py-3"><span className="font-mono text-sm font-semibold text-blue-600">#{t.ticket_number}</span></td>
                  <td className="px-4 py-3"><span className="text-sm">{t.subject}</span></td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${t.is_open ? 'bg-blue-50 text-blue-700' : 'bg-green-50 text-green-700'}`}>
                      {t.current_stage_name || 'New'}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[t.priority_name] || priorityColors.medium}`}>{t.priority_name}</span>
                  </td>
                  <td className="px-4 py-3"><span className="text-xs text-slate-400">{t.created_at ? new Date(t.created_at).toLocaleDateString() : '-'}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
