import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Calendar, ChevronLeft, ChevronRight, Clock, MapPin,
  AlertTriangle, User, Ticket
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { useEngineerAuth } from '../../context/EngineerAuthContext';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const DAYS_SHORT = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function getDaysInMonth(y, m) { return new Date(y, m + 1, 0).getDate(); }
function getFirstDay(y, m) { return new Date(y, m, 1).getDay(); }
function fmtDate(y, m, d) { return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`; }

const EventCard = ({ event }) => (
  <div
    className="flex items-start gap-2 p-2.5 rounded-lg border text-sm"
    style={{ borderLeftWidth: 3, borderLeftColor: event.color }}
    data-testid={`event-${event.id}`}
  >
    <div className="flex-1 min-w-0">
      <p className="font-medium text-slate-800 text-xs truncate">{event.title}</p>
      {event.start_time && (
        <p className="text-[11px] text-slate-500 flex items-center gap-1">
          <Clock className="w-3 h-3" />
          {event.start_time}{event.end_time ? ` - ${event.end_time}` : ''}
        </p>
      )}
      {event.company_name && (
        <p className="text-[11px] text-slate-400 truncate">{event.company_name}</p>
      )}
      {event.stage && (
        <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded mt-0.5 inline-block">{event.stage}</span>
      )}
    </div>
    {event.all_day && (
      <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-50 text-red-600 shrink-0">All Day</span>
    )}
  </div>
);

export default function EngineerCalendar() {
  const { token } = useEngineerAuth();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(new Date().toISOString().split('T')[0]);
  const [events, setEvents] = useState([]);
  const [workingHours, setWorkingHours] = useState({});
  const [loading, setLoading] = useState(true);

  const today = useMemo(() => new Date().toISOString().split('T')[0], []);
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  const dateRange = useMemo(() => ({
    from: `${year}-${String(month + 1).padStart(2, '0')}-01`,
    to: `${year}-${String(month + 1).padStart(2, '0')}-${getDaysInMonth(year, month)}`,
  }), [year, month]);

  const fetchSchedule = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(
        `${API}/api/calendar/my-schedule?date_from=${dateRange.from}&date_to=${dateRange.to}`,
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' } }
      );
      if (!res.ok) throw new Error('Failed');
      const data = await res.json();
      setEvents(data.events || []);
      setWorkingHours(data.working_hours || {});
    } catch { toast.error('Failed to load schedule'); }
    finally { setLoading(false); }
  }, [dateRange, token]);

  useEffect(() => { fetchSchedule(); }, [fetchSchedule]);

  const navigate = (dir) => {
    const d = new Date(currentDate);
    d.setMonth(d.getMonth() + dir);
    setCurrentDate(d);
  };

  const dayEvents = selectedDate ? events.filter(e => e.date === selectedDate) : [];
  const dayName = selectedDate ? new Date(selectedDate + 'T00:00:00').toLocaleDateString('en', { weekday: 'long' }).toLowerCase() : '';
  const dayWH = workingHours[dayName];

  // Build month grid
  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDay(year, month);
  const prevDays = getDaysInMonth(year, month - 1);
  const cells = [];
  for (let i = firstDay - 1; i >= 0; i--) cells.push({ day: prevDays - i, current: false, date: null });
  for (let d = 1; d <= daysInMonth; d++) cells.push({ day: d, current: true, date: fmtDate(year, month, d) });
  const remaining = 42 - cells.length;
  for (let d = 1; d <= remaining; d++) cells.push({ day: d, current: false, date: null });

  // Count events per date
  const eventCountMap = {};
  events.forEach(e => { eventCountMap[e.date] = (eventCountMap[e.date] || 0) + 1; });

  // Check if date is holiday
  const holidayDates = new Set(events.filter(e => e.type === 'holiday' || e.type === 'personal_holiday').map(e => e.date));

  return (
    <div className="space-y-6" data-testid="engineer-calendar">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">My Calendar</h1>
        <p className="text-sm text-slate-500 mt-1">Your schedule, visits & holidays</p>
      </div>

      <div className="flex gap-6">
        {/* Calendar Grid */}
        <div className="flex-1 bg-white border rounded-lg overflow-hidden">
          {/* Month nav */}
          <div className="flex items-center justify-between p-4 border-b">
            <Button size="sm" variant="ghost" onClick={() => navigate(-1)}><ChevronLeft className="w-4 h-4" /></Button>
            <h2 className="text-lg font-semibold text-slate-800">{MONTHS[month]} {year}</h2>
            <Button size="sm" variant="ghost" onClick={() => navigate(1)}><ChevronRight className="w-4 h-4" /></Button>
          </div>

          {/* Day headers */}
          <div className="grid grid-cols-7 border-b">
            {DAYS_SHORT.map(d => (
              <div key={d} className="text-center text-xs font-semibold text-slate-500 py-2">{d}</div>
            ))}
          </div>

          {/* Cells */}
          {loading ? (
            <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>
          ) : (
            <div className="grid grid-cols-7">
              {cells.map((cell, idx) => {
                const isToday = cell.date === today;
                const isSelected = cell.date === selectedDate;
                const count = cell.date ? eventCountMap[cell.date] || 0 : 0;
                const isHoliday = cell.date && holidayDates.has(cell.date);
                return (
                  <div
                    key={idx}
                    className={`border-b border-r p-2 min-h-[64px] cursor-pointer transition-all ${
                      !cell.current ? 'bg-slate-50/50' : isSelected ? 'bg-blue-50 ring-1 ring-blue-300' : 'hover:bg-slate-50'
                    } ${isHoliday ? 'bg-red-50/50' : ''}`}
                    onClick={() => cell.date && setSelectedDate(cell.date)}
                  >
                    <div className={`text-xs font-medium w-6 h-6 flex items-center justify-center rounded-full ${
                      isToday ? 'bg-blue-600 text-white' : cell.current ? 'text-slate-700' : 'text-slate-300'
                    }`}>
                      {cell.day}
                    </div>
                    {count > 0 && (
                      <div className="flex gap-0.5 mt-1">
                        {Array.from({ length: Math.min(count, 4) }, (_, i) => (
                          <span key={i} className="w-1.5 h-1.5 rounded-full bg-blue-500"></span>
                        ))}
                        {count > 4 && <span className="text-[9px] text-slate-400">+{count - 4}</span>}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}

          {/* Working hours legend */}
          {Object.keys(workingHours).length > 0 && (
            <div className="p-3 border-t bg-slate-50">
              <p className="text-xs font-medium text-slate-500 mb-1.5">My Working Hours</p>
              <div className="flex gap-2 flex-wrap">
                {['monday','tuesday','wednesday','thursday','friday','saturday','sunday'].map(d => {
                  const wh = workingHours[d];
                  return (
                    <span key={d} className={`text-[10px] px-2 py-0.5 rounded ${wh?.is_working ? 'bg-green-100 text-green-700' : 'bg-slate-200 text-slate-400'}`}>
                      {d.slice(0, 3).charAt(0).toUpperCase() + d.slice(1, 3)} {wh?.is_working ? `${wh.start}-${wh.end}` : 'Off'}
                    </span>
                  );
                })}
              </div>
            </div>
          )}
        </div>

        {/* Day Detail Sidebar */}
        <div className="w-80 bg-white border rounded-lg overflow-hidden shrink-0" data-testid="day-detail">
          <div className="p-4 border-b bg-slate-50">
            <h3 className="text-sm font-semibold text-slate-800">
              {selectedDate ? new Date(selectedDate + 'T00:00:00').toLocaleDateString('en', { weekday: 'long', month: 'long', day: 'numeric' }) : 'Select a date'}
            </h3>
            {dayWH && (
              <p className="text-xs text-slate-400 mt-0.5">
                {dayWH.is_working ? `Working: ${dayWH.start} - ${dayWH.end}` : 'Day Off'}
              </p>
            )}
          </div>
          <div className="p-4">
            {dayEvents.length === 0 ? (
              <div className="text-center py-10">
                <Calendar className="w-8 h-8 text-slate-200 mx-auto mb-2" />
                <p className="text-xs text-slate-400">No events scheduled</p>
              </div>
            ) : (
              <div className="space-y-2">
                {dayEvents.sort((a, b) => {
                  if (a.all_day && !b.all_day) return -1;
                  if (!a.all_day && b.all_day) return 1;
                  return (a.start_time || '').localeCompare(b.start_time || '');
                }).map(event => (
                  <EventCard key={event.id} event={event} />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
