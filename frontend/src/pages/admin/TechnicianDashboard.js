import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Ticket, Clock, Calendar, CheckCircle, MapPin, AlertTriangle, ChevronRight, Wrench, User } from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const getToken = () => localStorage.getItem('admin_token');

const StatsCard = ({ label, value, icon: Icon, color }) => (
  <div className="bg-white border border-slate-200 rounded-lg p-4" data-testid={`stat-${label.toLowerCase().replace(/\s/g, '-')}`}>
    <div className="flex items-center justify-between">
      <div>
        <p className="text-sm text-slate-500">{label}</p>
        <p className="text-2xl font-semibold mt-1">{value}</p>
      </div>
      <div className={`p-2.5 rounded-lg ${color}`}><Icon className="w-5 h-5" /></div>
    </div>
  </div>
);

const priorityColors = {
  low: 'bg-slate-100 text-slate-600',
  medium: 'bg-blue-100 text-blue-600',
  high: 'bg-orange-100 text-orange-600',
  critical: 'bg-red-100 text-red-600',
};

export default function TechnicianDashboard() {
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboard = useCallback(async () => {
    try {
      const res = await fetch(`${API}/api/ticketing/technician/dashboard`, {
        headers: { Authorization: `Bearer ${getToken()}` }
      });
      if (res.ok) setData(await res.json());
      else toast.error('Failed to load dashboard');
    } catch { toast.error('Network error'); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchDashboard(); }, [fetchDashboard]);

  if (loading) return <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>;
  if (!data) return <div className="flex items-center justify-center h-64 text-slate-400">No data</div>;

  const { assigned_tickets, assigned_tasks, upcoming_schedules, stats, engineer } = data;

  return (
    <div className="space-y-6" data-testid="technician-dashboard">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Technician Dashboard</h1>
        <p className="text-sm text-slate-500 mt-1">
          {engineer ? `Welcome, ${engineer.name}` : 'Your assigned tickets and tasks'}
        </p>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <StatsCard label="Assigned Tickets" value={stats.total_assigned} icon={Ticket} color="bg-blue-50 text-blue-600" />
        <StatsCard label="Visits Today" value={stats.visits_today} icon={Calendar} color="bg-purple-50 text-purple-600" />
        <StatsCard label="Pending Diagnosis" value={stats.pending_diagnosis} icon={AlertTriangle} color="bg-orange-50 text-orange-600" />
        <StatsCard label="Completed This Week" value={stats.completed_this_week} icon={CheckCircle} color="bg-green-50 text-green-600" />
      </div>

      {/* Upcoming Schedules */}
      {upcoming_schedules.length > 0 && (
        <div className="bg-white border rounded-lg p-4" data-testid="upcoming-schedules">
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1"><Calendar className="w-4 h-4" /> Upcoming Visits</h2>
          <div className="space-y-2">
            {upcoming_schedules.map(s => (
              <div key={s.id} className="flex items-center gap-3 border rounded-lg p-3 hover:bg-slate-50">
                <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                  <MapPin className="w-5 h-5 text-purple-500" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium">#{s.ticket_number} - {s.company_name || s.subject}</p>
                  <p className="text-xs text-slate-400">{new Date(s.scheduled_at).toLocaleString()}</p>
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'scheduled' ? 'bg-blue-100 text-blue-600' : 'bg-green-100 text-green-600'}`}>
                  {s.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Assigned Tickets */}
      <div className="bg-white border rounded-lg overflow-hidden" data-testid="assigned-tickets">
        <div className="p-4 border-b">
          <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-1"><Ticket className="w-4 h-4" /> My Tickets ({assigned_tickets.length})</h2>
        </div>
        {assigned_tickets.length === 0 ? (
          <div className="text-center py-12 text-slate-400">No assigned tickets</div>
        ) : (
          <table className="w-full">
            <thead className="bg-slate-50 border-b">
              <tr>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Ticket</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Subject</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Company</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Stage</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Priority</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Scheduled</th>
                <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Actions</th>
              </tr>
            </thead>
            <tbody>
              {assigned_tickets.map(t => (
                <tr key={t.id} className="border-b hover:bg-slate-50" data-testid={`my-ticket-${t.ticket_number}`}>
                  <td className="px-4 py-3"><span className="font-mono text-sm font-semibold text-blue-600">#{t.ticket_number}</span></td>
                  <td className="px-4 py-3"><p className="text-sm text-slate-900 truncate max-w-[200px]">{t.subject}</p></td>
                  <td className="px-4 py-3"><span className="text-xs text-slate-500">{t.company_name || '-'}</span></td>
                  <td className="px-4 py-3">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-blue-50 text-blue-700">{t.current_stage_name}</span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${priorityColors[t.priority_name] || priorityColors.medium}`}>{t.priority_name}</span>
                  </td>
                  <td className="px-4 py-3">
                    {t.scheduled_at ? <span className="text-xs text-purple-600">{new Date(t.scheduled_at).toLocaleDateString()}</span> : <span className="text-xs text-slate-300">-</span>}
                  </td>
                  <td className="px-4 py-3">
                    <Button variant="outline" size="sm" onClick={() => navigate(`/admin/service-requests/${t.id}`)} data-testid={`view-ticket-${t.ticket_number}`}>
                      View <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pending Tasks */}
      {assigned_tasks.length > 0 && (
        <div className="bg-white border rounded-lg p-4" data-testid="pending-tasks">
          <h2 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-1"><Wrench className="w-4 h-4" /> My Tasks ({assigned_tasks.length})</h2>
          <div className="space-y-2">
            {assigned_tasks.map(task => (
              <div key={task.id} className="flex items-center gap-3 border rounded-lg p-3 hover:bg-slate-50">
                <div className={`w-2 h-2 rounded-full ${task.status === 'in_progress' ? 'bg-yellow-500' : 'bg-slate-300'}`} />
                <div className="flex-1">
                  <p className="text-sm font-medium">{task.name}</p>
                  <p className="text-xs text-slate-400">Ticket #{task.ticket_number}</p>
                </div>
                {task.due_at && (
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Clock className="w-3 h-3" /> Due: {new Date(task.due_at).toLocaleDateString()}
                  </span>
                )}
                <span className={`text-xs px-2 py-0.5 rounded-full ${task.status === 'in_progress' ? 'bg-yellow-100 text-yellow-600' : 'bg-slate-100 text-slate-600'}`}>
                  {task.status}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
