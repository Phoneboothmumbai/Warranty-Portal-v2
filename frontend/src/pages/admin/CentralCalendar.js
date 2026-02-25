import { useState, useEffect, useCallback, useMemo } from 'react';
import {
  Calendar, ChevronLeft, ChevronRight, Plus, X, Clock, AlertTriangle,
  Zap, Filter, User, MapPin, Ticket, Trash2, Save
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;
const headers = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('admin_token')}`,
});

const DAYS = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday'];
const MONTHS = ['January','February','March','April','May','June','July','August','September','October','November','December'];
const VIEWS = ['month', 'week', 'day'];

const COLORS = [
  '#3b82f6','#8b5cf6','#06b6d4','#10b981','#f59e0b','#ec4899',
  '#6366f1','#14b8a6','#f97316','#84cc16','#a855f7','#0ea5e9'
];

// ── Helpers ──

function getDaysInMonth(year, month) {
  return new Date(year, month + 1, 0).getDate();
}
function getFirstDayOfMonth(year, month) {
  return new Date(year, month, 1).getDay();
}
function formatDate(y, m, d) {
  return `${y}-${String(m + 1).padStart(2, '0')}-${String(d).padStart(2, '0')}`;
}
function getWeekDates(date) {
  const d = new Date(date);
  const day = d.getDay();
  const diff = d.getDate() - day;
  return Array.from({ length: 7 }, (_, i) => {
    const wd = new Date(d);
    wd.setDate(diff + i);
    return wd;
  });
}

// ── Event Dot ──

const EventDot = ({ event }) => (
  <div
    className="text-[10px] px-1 py-0.5 rounded truncate leading-tight cursor-pointer"
    style={{ backgroundColor: event.color + '22', color: event.color, borderLeft: `2px solid ${event.color}` }}
    title={`${event.start_time || 'All day'} ${event.title}`}
  >
    {event.start_time && <span className="font-semibold mr-0.5">{event.start_time}</span>}
    {event.title}
  </div>
);

// ── Month View ──

const MonthView = ({ year, month, events, onDateClick, today }) => {
  const daysInMonth = getDaysInMonth(year, month);
  const firstDay = getFirstDayOfMonth(year, month);
  const prevDays = getDaysInMonth(year, month - 1);
  const cells = [];

  // Previous month filler
  for (let i = firstDay - 1; i >= 0; i--) {
    const d = prevDays - i;
    cells.push({ day: d, current: false, date: null });
  }
  // Current month
  for (let d = 1; d <= daysInMonth; d++) {
    const dateStr = formatDate(year, month, d);
    cells.push({ day: d, current: true, date: dateStr });
  }
  // Next month filler
  const remaining = 42 - cells.length;
  for (let d = 1; d <= remaining; d++) {
    cells.push({ day: d, current: false, date: null });
  }

  const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  return (
    <div data-testid="month-view">
      <div className="grid grid-cols-7 border-b">
        {dayNames.map(d => (
          <div key={d} className="text-center text-xs font-semibold text-slate-500 py-2">{d}</div>
        ))}
      </div>
      <div className="grid grid-cols-7 auto-rows-fr" style={{ minHeight: '480px' }}>
        {cells.map((cell, idx) => {
          const dayEvents = cell.date ? events.filter(e => e.date === cell.date) : [];
          const isToday = cell.date === today;
          return (
            <div
              key={idx}
              className={`border-b border-r p-1 min-h-[80px] cursor-pointer transition-colors hover:bg-slate-50 ${!cell.current ? 'bg-slate-50/50' : ''}`}
              onClick={() => cell.date && onDateClick(cell.date)}
            >
              <div className={`text-xs font-medium mb-0.5 w-6 h-6 flex items-center justify-center rounded-full ${isToday ? 'bg-blue-600 text-white' : cell.current ? 'text-slate-700' : 'text-slate-300'}`}>
                {cell.day}
              </div>
              <div className="space-y-0.5">
                {dayEvents.slice(0, 3).map(e => <EventDot key={e.id} event={e} />)}
                {dayEvents.length > 3 && (
                  <div className="text-[10px] text-slate-400 pl-1">+{dayEvents.length - 3} more</div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── Week View ──

const WeekView = ({ date, events, onDateClick, today }) => {
  const weekDates = getWeekDates(date);
  const hours = Array.from({ length: 12 }, (_, i) => i + 7); // 7am to 6pm

  return (
    <div data-testid="week-view" className="overflow-auto" style={{ maxHeight: '560px' }}>
      <div className="grid grid-cols-8 sticky top-0 bg-white z-10 border-b">
        <div className="text-xs text-slate-400 p-2"></div>
        {weekDates.map(d => {
          const dateStr = d.toISOString().split('T')[0];
          const isToday = dateStr === today;
          return (
            <div key={dateStr} className={`text-center p-2 cursor-pointer ${isToday ? 'bg-blue-50' : ''}`} onClick={() => onDateClick(dateStr)}>
              <div className="text-[10px] text-slate-400">{['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][d.getDay()]}</div>
              <div className={`text-sm font-semibold ${isToday ? 'text-blue-600' : 'text-slate-700'}`}>{d.getDate()}</div>
            </div>
          );
        })}
      </div>
      <div className="grid grid-cols-8">
        {hours.map(h => (
          <div key={h} className="contents">
            <div className="text-[10px] text-slate-400 text-right pr-2 py-3 border-b">
              {h > 12 ? h - 12 : h}{h >= 12 ? 'PM' : 'AM'}
            </div>
            {weekDates.map(d => {
              const dateStr = d.toISOString().split('T')[0];
              const hourEvents = events.filter(e => {
                if (e.date !== dateStr || !e.start_time) return false;
                const eh = parseInt(e.start_time.split(':')[0], 10);
                return eh === h;
              });
              return (
                <div key={`${dateStr}-${h}`} className="border-b border-r p-0.5 min-h-[48px]">
                  {hourEvents.map(e => <EventDot key={e.id} event={e} />)}
                </div>
              );
            })}
          </div>
        ))}
      </div>
    </div>
  );
};

// ── Day View ──

const DayView = ({ date, events, engineers }) => {
  const dayEvents = events.filter(e => e.date === date);
  const allDayEvents = dayEvents.filter(e => e.all_day);
  const timedEvents = dayEvents.filter(e => !e.all_day).sort((a, b) => (a.start_time || '').localeCompare(b.start_time || ''));
  const hours = Array.from({ length: 12 }, (_, i) => i + 7);

  return (
    <div data-testid="day-view">
      {allDayEvents.length > 0 && (
        <div className="border-b p-3 bg-slate-50 space-y-1">
          <p className="text-xs font-semibold text-slate-500 mb-1">All Day</p>
          {allDayEvents.map(e => (
            <div key={e.id} className="text-sm px-2 py-1 rounded" style={{ backgroundColor: e.color + '22', color: e.color, borderLeft: `3px solid ${e.color}` }}>
              {e.title}
            </div>
          ))}
        </div>
      )}
      <div className="overflow-auto" style={{ maxHeight: '480px' }}>
        {hours.map(h => {
          const hourStr = `${String(h).padStart(2, '0')}`;
          const hourEvents = timedEvents.filter(e => e.start_time && e.start_time.startsWith(hourStr));
          return (
            <div key={h} className="flex border-b min-h-[56px]">
              <div className="w-16 text-xs text-slate-400 text-right pr-3 py-2 shrink-0">
                {h > 12 ? h - 12 : h}:00 {h >= 12 ? 'PM' : 'AM'}
              </div>
              <div className="flex-1 p-1 space-y-1">
                {hourEvents.map(e => (
                  <div key={e.id} className="flex items-center gap-2 text-sm px-2 py-1.5 rounded" style={{ backgroundColor: e.color + '15', borderLeft: `3px solid ${e.color}` }}>
                    <span className="font-semibold text-xs" style={{ color: e.color }}>{e.start_time}{e.end_time ? ` - ${e.end_time}` : ''}</span>
                    <span className="text-slate-700 truncate">{e.title}</span>
                    {e.engineer_name && <span className="text-xs text-slate-400 ml-auto shrink-0 flex items-center gap-0.5"><User className="w-3 h-3" />{e.engineer_name}</span>}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

// ── Sidebar Panel ──

const SidePanel = ({ selectedDate, events, activePanel, setActivePanel, holidays, emergencyHours, standardHours, onAddHoliday, onDeleteHoliday, onAddEmergency, onDeleteEmergency, onUpdateStdHours }) => {
  const [holidayForm, setHolidayForm] = useState({ name: '', date: selectedDate || '', type: 'public' });
  const [emergencyForm, setEmergencyForm] = useState({ date: selectedDate || '', reason: '', start: '09:00', end: '18:00' });
  const [stdHours, setStdHours] = useState(standardHours);

  useEffect(() => { setStdHours(standardHours); }, [standardHours]);
  useEffect(() => {
    setHolidayForm(f => ({ ...f, date: selectedDate || f.date }));
    setEmergencyForm(f => ({ ...f, date: selectedDate || f.date }));
  }, [selectedDate]);

  const dayEvents = selectedDate ? events.filter(e => e.date === selectedDate) : [];

  return (
    <div className="w-80 border-l bg-white overflow-auto shrink-0" data-testid="calendar-sidebar">
      {/* Tab buttons */}
      <div className="flex border-b">
        {[
          { id: 'events', label: 'Events', icon: Calendar },
          { id: 'holidays', label: 'Holidays', icon: AlertTriangle },
          { id: 'hours', label: 'Hours', icon: Clock },
          { id: 'emergency', label: 'Emergency', icon: Zap },
        ].map(t => (
          <button key={t.id} className={`flex-1 py-2.5 text-xs font-medium transition-colors ${activePanel === t.id ? 'text-blue-600 border-b-2 border-blue-600 bg-blue-50/50' : 'text-slate-400 hover:text-slate-600'}`} onClick={() => setActivePanel(t.id)} data-testid={`panel-${t.id}`}>
            <t.icon className="w-3.5 h-3.5 mx-auto mb-0.5" />{t.label}
          </button>
        ))}
      </div>

      <div className="p-4">
        {/* EVENTS PANEL */}
        {activePanel === 'events' && (
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-2">{selectedDate || 'Select a date'}</h3>
            {dayEvents.length === 0 ? (
              <p className="text-xs text-slate-400 text-center py-8">No events</p>
            ) : (
              <div className="space-y-2">
                {dayEvents.map(e => (
                  <div key={e.id} className="p-2.5 rounded-lg border text-sm" style={{ borderLeftWidth: 3, borderLeftColor: e.color }}>
                    <p className="font-medium text-slate-800 text-xs">{e.title}</p>
                    {e.start_time && <p className="text-[11px] text-slate-500">{e.start_time}{e.end_time ? ` - ${e.end_time}` : ''}</p>}
                    {e.engineer_name && <p className="text-[11px] text-slate-400 flex items-center gap-0.5"><User className="w-3 h-3" />{e.engineer_name}</p>}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* HOLIDAYS PANEL */}
        {activePanel === 'holidays' && (
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Organization Holidays</h3>
            <div className="space-y-2 mb-4 border-b pb-4">
              <Input placeholder="Holiday name" value={holidayForm.name} onChange={e => setHolidayForm(f => ({ ...f, name: e.target.value }))} className="text-sm" data-testid="holiday-name" />
              <Input type="date" value={holidayForm.date} onChange={e => setHolidayForm(f => ({ ...f, date: e.target.value }))} className="text-sm" data-testid="holiday-date" />
              <select className="w-full border rounded-md px-3 py-2 text-sm" value={holidayForm.type} onChange={e => setHolidayForm(f => ({ ...f, type: e.target.value }))}>
                <option value="public">Public Holiday</option>
                <option value="company">Company Holiday</option>
                <option value="optional">Optional Holiday</option>
              </select>
              <Button size="sm" className="w-full" onClick={() => { onAddHoliday(holidayForm); setHolidayForm({ name: '', date: '', type: 'public' }); }} disabled={!holidayForm.name || !holidayForm.date} data-testid="add-holiday-btn">
                <Plus className="w-3.5 h-3.5 mr-1" /> Add Holiday
              </Button>
            </div>
            <div className="space-y-1.5 max-h-64 overflow-auto">
              {holidays.map(h => (
                <div key={h.id} className="flex items-center justify-between p-2 bg-red-50 rounded text-xs">
                  <div>
                    <p className="font-medium text-red-700">{h.name}</p>
                    <p className="text-red-400">{h.date} &middot; {h.type}</p>
                  </div>
                  <button onClick={() => onDeleteHoliday(h.id)} className="text-red-300 hover:text-red-600"><Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              ))}
              {holidays.length === 0 && <p className="text-xs text-slate-400 text-center py-4">No holidays added</p>}
            </div>
          </div>
        )}

        {/* STANDARD HOURS PANEL */}
        {activePanel === 'hours' && (
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Standard Working Hours</h3>
            <div className="space-y-2">
              {DAYS.map(day => {
                const dh = stdHours[day] || { is_working: false, start: '09:00', end: '18:00' };
                return (
                  <div key={day} className="flex items-center gap-2">
                    <label className="flex items-center gap-1.5 w-20">
                      <input type="checkbox" checked={dh.is_working} onChange={e => setStdHours(h => ({ ...h, [day]: { ...h[day], is_working: e.target.checked } }))} className="rounded" />
                      <span className="text-xs capitalize font-medium">{day.slice(0, 3)}</span>
                    </label>
                    {dh.is_working ? (
                      <>
                        <input type="time" className="border rounded px-1.5 py-1 text-xs w-[85px]" value={dh.start} onChange={e => setStdHours(h => ({ ...h, [day]: { ...h[day], start: e.target.value } }))} />
                        <span className="text-xs text-slate-300">-</span>
                        <input type="time" className="border rounded px-1.5 py-1 text-xs w-[85px]" value={dh.end} onChange={e => setStdHours(h => ({ ...h, [day]: { ...h[day], end: e.target.value } }))} />
                      </>
                    ) : <span className="text-[10px] text-slate-400 italic">Off</span>}
                  </div>
                );
              })}
            </div>
            <Button size="sm" className="w-full mt-4" onClick={() => onUpdateStdHours(stdHours)} data-testid="save-std-hours">
              <Save className="w-3.5 h-3.5 mr-1" /> Save Standard Hours
            </Button>
          </div>
        )}

        {/* EMERGENCY HOURS PANEL */}
        {activePanel === 'emergency' && (
          <div>
            <h3 className="text-sm font-semibold text-slate-700 mb-3">Emergency Working Hours</h3>
            <div className="space-y-2 mb-4 border-b pb-4">
              <Input type="date" value={emergencyForm.date} onChange={e => setEmergencyForm(f => ({ ...f, date: e.target.value }))} className="text-sm" data-testid="emergency-date" />
              <Input placeholder="Reason" value={emergencyForm.reason} onChange={e => setEmergencyForm(f => ({ ...f, reason: e.target.value }))} className="text-sm" data-testid="emergency-reason" />
              <div className="flex gap-2">
                <Input type="time" value={emergencyForm.start} onChange={e => setEmergencyForm(f => ({ ...f, start: e.target.value }))} className="text-sm" />
                <Input type="time" value={emergencyForm.end} onChange={e => setEmergencyForm(f => ({ ...f, end: e.target.value }))} className="text-sm" />
              </div>
              <Button size="sm" className="w-full" onClick={() => { onAddEmergency(emergencyForm); setEmergencyForm({ date: '', reason: '', start: '09:00', end: '18:00' }); }} disabled={!emergencyForm.date || !emergencyForm.reason} data-testid="add-emergency-btn">
                <Plus className="w-3.5 h-3.5 mr-1" /> Add Emergency Hours
              </Button>
            </div>
            <div className="space-y-1.5 max-h-64 overflow-auto">
              {emergencyHours.map(e => (
                <div key={e.id} className="flex items-center justify-between p-2 bg-amber-50 rounded text-xs">
                  <div>
                    <p className="font-medium text-amber-700">{e.reason}</p>
                    <p className="text-amber-400">{e.date} &middot; {e.start} - {e.end}</p>
                  </div>
                  <button onClick={() => onDeleteEmergency(e.id)} className="text-amber-300 hover:text-amber-600"><Trash2 className="w-3.5 h-3.5" /></button>
                </div>
              ))}
              {emergencyHours.length === 0 && <p className="text-xs text-slate-400 text-center py-4">No emergency hours</p>}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ── MAIN CALENDAR COMPONENT ──

export default function CentralCalendar() {
  const [view, setView] = useState('month');
  const [currentDate, setCurrentDate] = useState(new Date());
  const [selectedDate, setSelectedDate] = useState(null);
  const [events, setEvents] = useState([]);
  const [engineers, setEngineers] = useState([]);
  const [filterEngineer, setFilterEngineer] = useState('');
  const [holidays, setHolidays] = useState([]);
  const [emergencyHours, setEmergencyHours] = useState([]);
  const [standardHours, setStandardHours] = useState({});
  const [activePanel, setActivePanel] = useState('events');
  const [loading, setLoading] = useState(true);

  const today = useMemo(() => new Date().toISOString().split('T')[0], []);
  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Calculate date range based on view
  const dateRange = useMemo(() => {
    if (view === 'month') {
      const from = `${year}-${String(month + 1).padStart(2, '0')}-01`;
      const to = `${year}-${String(month + 1).padStart(2, '0')}-${getDaysInMonth(year, month)}`;
      return { from, to };
    }
    if (view === 'week') {
      const weekDates = getWeekDates(currentDate);
      return { from: weekDates[0].toISOString().split('T')[0], to: weekDates[6].toISOString().split('T')[0] };
    }
    const d = currentDate.toISOString().split('T')[0];
    return { from: d, to: d };
  }, [view, year, month, currentDate]);

  // Assign colors to engineers
  const engineerColors = useMemo(() => {
    const map = {};
    engineers.forEach((e, i) => { map[e.id] = COLORS[i % COLORS.length]; });
    return map;
  }, [engineers]);

  // Fetch events
  const fetchEvents = useCallback(async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ date_from: dateRange.from, date_to: dateRange.to });
      if (filterEngineer) params.append('engineer_id', filterEngineer);
      const res = await fetch(`${API}/api/calendar/events?${params}`, { headers: headers() });
      const data = await res.json();
      // Apply engineer colors to schedule/ticket events
      const colored = (data.events || []).map(e => {
        if (e.engineer_id && engineerColors[e.engineer_id]) {
          return { ...e, color: engineerColors[e.engineer_id] };
        }
        return e;
      });
      setEvents(colored);
      setEngineers(data.engineers || []);
    } catch { toast.error('Failed to load calendar'); }
    finally { setLoading(false); }
  }, [dateRange, filterEngineer, engineerColors]);

  // Fetch holidays + standard hours + emergency hours
  const fetchConfig = useCallback(async () => {
    try {
      const [hRes, sRes, eRes] = await Promise.all([
        fetch(`${API}/api/calendar/holidays?year=${year}`, { headers: headers() }),
        fetch(`${API}/api/calendar/standard-hours`, { headers: headers() }),
        fetch(`${API}/api/calendar/emergency-hours?date_from=${dateRange.from}&date_to=${dateRange.to}`, { headers: headers() }),
      ]);
      setHolidays(await hRes.json());
      setStandardHours(await sRes.json());
      setEmergencyHours(await eRes.json());
    } catch {}
  }, [year, dateRange]);

  useEffect(() => { fetchEvents(); }, [fetchEvents]);
  useEffect(() => { fetchConfig(); }, [fetchConfig]);

  // Navigation
  const navigate = (dir) => {
    const d = new Date(currentDate);
    if (view === 'month') d.setMonth(d.getMonth() + dir);
    else if (view === 'week') d.setDate(d.getDate() + 7 * dir);
    else d.setDate(d.getDate() + dir);
    setCurrentDate(d);
  };
  const goToday = () => setCurrentDate(new Date());
  const onDateClick = (date) => { setSelectedDate(date); setActivePanel('events'); };

  // CRUD handlers
  const addHoliday = async (form) => {
    try {
      const res = await fetch(`${API}/api/calendar/holidays`, { method: 'POST', headers: headers(), body: JSON.stringify(form) });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
      toast.success('Holiday added'); fetchConfig(); fetchEvents();
    } catch (e) { toast.error(e.message || 'Failed'); }
  };
  const deleteHoliday = async (id) => {
    await fetch(`${API}/api/calendar/holidays/${id}`, { method: 'DELETE', headers: headers() });
    toast.success('Deleted'); fetchConfig(); fetchEvents();
  };
  const addEmergency = async (form) => {
    try {
      const res = await fetch(`${API}/api/calendar/emergency-hours`, { method: 'POST', headers: headers(), body: JSON.stringify(form) });
      if (!res.ok) { const e = await res.json(); throw new Error(e.detail); }
      toast.success('Emergency hours added'); fetchConfig(); fetchEvents();
    } catch (e) { toast.error(e.message || 'Failed'); }
  };
  const deleteEmergency = async (id) => {
    await fetch(`${API}/api/calendar/emergency-hours/${id}`, { method: 'DELETE', headers: headers() });
    toast.success('Deleted'); fetchConfig(); fetchEvents();
  };
  const updateStdHours = async (data) => {
    try {
      await fetch(`${API}/api/calendar/standard-hours`, { method: 'PUT', headers: headers(), body: JSON.stringify(data) });
      toast.success('Standard hours saved'); fetchConfig();
    } catch { toast.error('Failed'); }
  };

  // Title text
  const title = view === 'month'
    ? `${MONTHS[month]} ${year}`
    : view === 'week'
      ? (() => {
          const wd = getWeekDates(currentDate);
          return `${wd[0].toLocaleDateString('en', { month: 'short', day: 'numeric' })} - ${wd[6].toLocaleDateString('en', { month: 'short', day: 'numeric', year: 'numeric' })}`;
        })()
      : currentDate.toLocaleDateString('en', { weekday: 'long', month: 'long', day: 'numeric', year: 'numeric' });

  return (
    <div className="h-[calc(100vh-100px)] flex flex-col" data-testid="central-calendar">
      {/* Header */}
      <div className="flex items-center justify-between pb-4 shrink-0">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Calendar</h1>
          <p className="text-sm text-slate-500">Organization schedule, holidays & working hours</p>
        </div>
        <div className="flex items-center gap-3">
          {/* Engineer filter */}
          <div className="flex items-center gap-1.5">
            <Filter className="w-4 h-4 text-slate-400" />
            <select
              className="border rounded-lg px-2.5 py-1.5 text-sm"
              value={filterEngineer}
              onChange={e => setFilterEngineer(e.target.value)}
              data-testid="engineer-filter"
            >
              <option value="">All Technicians</option>
              {engineers.map(e => (
                <option key={e.id} value={e.id}>{e.name}</option>
              ))}
            </select>
          </div>
          {/* Engineer legend */}
          <div className="flex gap-1">
            {engineers.slice(0, 6).map(e => (
              <span key={e.id} className="flex items-center gap-1 text-[10px] text-slate-600 bg-slate-50 px-1.5 py-0.5 rounded-full">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ backgroundColor: engineerColors[e.id] || '#999' }}></span>
                {e.name?.split(' ')[0]}
              </span>
            ))}
          </div>
        </div>
      </div>

      {/* Toolbar */}
      <div className="flex items-center justify-between pb-3 shrink-0">
        <div className="flex items-center gap-2">
          <Button size="sm" variant="outline" onClick={() => navigate(-1)} data-testid="nav-prev"><ChevronLeft className="w-4 h-4" /></Button>
          <Button size="sm" variant="outline" onClick={goToday}>Today</Button>
          <Button size="sm" variant="outline" onClick={() => navigate(1)} data-testid="nav-next"><ChevronRight className="w-4 h-4" /></Button>
          <h2 className="text-lg font-semibold text-slate-800 ml-2">{title}</h2>
        </div>
        <div className="flex bg-slate-100 rounded-lg p-0.5">
          {VIEWS.map(v => (
            <button key={v} className={`px-3 py-1 text-sm rounded-md capitalize ${view === v ? 'bg-white shadow-sm font-medium text-slate-800' : 'text-slate-500'}`} onClick={() => setView(v)} data-testid={`view-${v}`}>{v}</button>
          ))}
        </div>
      </div>

      {/* Calendar + Sidebar */}
      <div className="flex flex-1 border rounded-lg bg-white overflow-hidden">
        <div className="flex-1 overflow-auto">
          {loading && <div className="flex items-center justify-center h-64 text-slate-400">Loading...</div>}
          {!loading && view === 'month' && <MonthView year={year} month={month} events={events} onDateClick={onDateClick} today={today} />}
          {!loading && view === 'week' && <WeekView date={currentDate} events={events} onDateClick={onDateClick} today={today} />}
          {!loading && view === 'day' && <DayView date={currentDate.toISOString().split('T')[0]} events={events} engineers={engineers} />}
        </div>
        <SidePanel
          selectedDate={selectedDate}
          events={events}
          activePanel={activePanel}
          setActivePanel={setActivePanel}
          holidays={holidays}
          emergencyHours={emergencyHours}
          standardHours={standardHours}
          onAddHoliday={addHoliday}
          onDeleteHoliday={deleteHoliday}
          onAddEmergency={addEmergency}
          onDeleteEmergency={deleteEmergency}
          onUpdateStdHours={updateStdHours}
        />
      </div>
    </div>
  );
}
