import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Wrench, LogOut, Clock, CheckCircle2, AlertCircle, 
  MapPin, Phone, Building2, Laptop, ChevronRight,
  Play, Calendar, RefreshCw, Package, Timer, User
} from 'lucide-react';
import { useEngineerAuth } from '../../context/EngineerAuthContext';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent } from '../../components/ui/card';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const TechnicianDashboard = () => {
  const navigate = useNavigate();
  const { engineer, token, logout, isAuthenticated } = useEngineerAuth();
  const [visits, setVisits] = useState([]);
  const [stats, setStats] = useState({ scheduled: 0, in_progress: 0, completed: 0 });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('pending');
  const [refreshing, setRefreshing] = useState(false);

  // Redirect if not authenticated
  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/engineer');
    }
  }, [isAuthenticated, navigate]);

  const fetchVisits = useCallback(async () => {
    if (!token || !engineer?.id) return;
    
    try {
      setRefreshing(true);
      // Fetch visits assigned to this technician using engineer endpoint
      const response = await axios.get(`${API}/api/engineer/my-visits`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      const visitsList = response.data || [];
      setVisits(visitsList);
      
      // Calculate stats
      const scheduled = visitsList.filter(v => v.status === 'scheduled').length;
      const in_progress = visitsList.filter(v => ['in_progress', 'in_transit', 'on_site'].includes(v.status)).length;
      const completed = visitsList.filter(v => v.status === 'completed').length;
      setStats({ scheduled, in_progress, completed });
      
    } catch (err) {
      console.error('Failed to fetch visits:', err);
      toast.error('Failed to load visits');
        console.error('Fallback also failed:', fallbackErr);
        toast.error('Failed to load visits');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [token, engineer?.id]);

  useEffect(() => {
    fetchVisits();
  }, [fetchVisits]);

  const handleLogout = () => {
    logout();
    navigate('/engineer');
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'scheduled': return 'bg-blue-50 text-blue-600 border-blue-200';
      case 'in_progress': return 'bg-amber-50 text-amber-600 border-amber-200';
      case 'completed': return 'bg-emerald-50 text-emerald-600 border-emerald-200';
      case 'cancelled': return 'bg-red-50 text-red-600 border-red-200';
      default: return 'bg-slate-50 text-slate-600 border-slate-200';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'scheduled': return <Clock className="h-4 w-4" />;
      case 'in_progress': return <Play className="h-4 w-4" />;
      case 'completed': return <CheckCircle2 className="h-4 w-4" />;
      default: return <AlertCircle className="h-4 w-4" />;
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    return date.toLocaleDateString('en-GB', { day: '2-digit', month: 'short' });
  };

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    // Handle both ISO datetime and HH:MM format
    if (timeStr.includes('T')) {
      const date = new Date(timeStr);
      return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit' });
    }
    return timeStr;
  };

  const filteredVisits = visits.filter(v => {
    if (activeTab === 'pending') return v.status === 'scheduled' || v.status === 'in_progress';
    return v.status === 'completed';
  });

  const pendingCount = stats.scheduled + stats.in_progress;
  const completedCount = stats.completed;

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div data-testid="technician-dashboard" className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 text-white sticky top-0 z-50">
        <div className="px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-500 rounded-xl flex items-center justify-center">
                <Wrench className="h-5 w-5 text-white" />
              </div>
              <div>
                <p className="font-semibold">{engineer?.name || 'Technician'}</p>
                <p className="text-xs text-slate-400">Service Engineer</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={fetchVisits}
                disabled={refreshing}
                className="text-slate-300 hover:text-white hover:bg-slate-700"
              >
                <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              </Button>
              <Button 
                variant="ghost" 
                size="sm" 
                onClick={handleLogout}
                className="text-slate-300 hover:text-white hover:bg-slate-700"
                data-testid="logout-btn"
              >
                <LogOut className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Row */}
        <div className="px-4 pb-4">
          <div className="grid grid-cols-3 gap-3">
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-blue-400">{stats.scheduled}</p>
              <p className="text-xs text-slate-400">Scheduled</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-amber-400">{stats.in_progress}</p>
              <p className="text-xs text-slate-400">In Progress</p>
            </div>
            <div className="bg-slate-800/50 rounded-lg p-3 text-center">
              <p className="text-2xl font-bold text-emerald-400">{stats.completed}</p>
              <p className="text-xs text-slate-400">Completed</p>
            </div>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-t border-slate-700">
          <button
            onClick={() => setActiveTab('pending')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === 'pending' 
                ? 'text-blue-400 border-b-2 border-blue-400' 
                : 'text-slate-400 hover:text-white'
            }`}
            data-testid="pending-tab"
          >
            Pending ({pendingCount})
          </button>
          <button
            onClick={() => setActiveTab('completed')}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${
              activeTab === 'completed' 
                ? 'text-blue-400 border-b-2 border-blue-400' 
                : 'text-slate-400 hover:text-white'
            }`}
            data-testid="completed-tab"
          >
            Completed ({completedCount})
          </button>
        </div>
      </header>

      {/* Content */}
      <main className="p-4 pb-20">
        {filteredVisits.length === 0 ? (
          <div className="text-center py-12">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4">
              {activeTab === 'pending' ? (
                <Clock className="h-8 w-8 text-slate-400" />
              ) : (
                <CheckCircle2 className="h-8 w-8 text-slate-400" />
              )}
            </div>
            <p className="text-slate-500 mb-2">
              {activeTab === 'pending' ? 'No pending visits' : 'No completed visits'}
            </p>
            <p className="text-slate-400 text-sm">
              {activeTab === 'pending' 
                ? 'New visits will appear here when assigned' 
                : 'Completed visits will be shown here'}
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {filteredVisits.map((visit) => (
              <Card 
                key={visit.id} 
                className="overflow-hidden cursor-pointer hover:shadow-md transition-shadow"
                onClick={() => navigate(`/engineer/visit/${visit.id}`)}
                data-testid={`visit-card-${visit.id}`}
              >
                <CardContent className="p-0">
                  <div className="p-4">
                    {/* Header */}
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <Badge className={`${getStatusColor(visit.status)} border`}>
                          {getStatusIcon(visit.status)}
                          <span className="ml-1 capitalize">{visit.status?.replace('_', ' ')}</span>
                        </Badge>
                        {visit.is_urgent && (
                          <Badge variant="destructive" className="text-xs">Urgent</Badge>
                        )}
                      </div>
                      <ChevronRight className="h-5 w-5 text-slate-400" />
                    </div>

                    {/* Ticket Info */}
                    <div className="mb-3">
                      <p className="font-medium text-slate-900 text-sm flex items-center gap-2">
                        <span className="font-mono text-blue-600">#{visit.ticket_number}</span>
                        <span className="text-slate-400">•</span>
                        <span>Visit #{visit.visit_number}</span>
                      </p>
                      {visit.purpose && (
                        <p className="text-slate-600 text-sm line-clamp-1 mt-1">{visit.purpose}</p>
                      )}
                    </div>

                    {/* Schedule Info */}
                    {visit.scheduled_date && (
                      <div className="flex items-center gap-2 text-sm text-slate-600 mb-2">
                        <Calendar className="h-4 w-4 text-slate-400" />
                        <span>{formatDate(visit.scheduled_date)}</span>
                        {visit.scheduled_time_from && (
                          <>
                            <span className="text-slate-400">•</span>
                            <span>{visit.scheduled_time_from} - {visit.scheduled_time_to || 'TBD'}</span>
                          </>
                        )}
                      </div>
                    )}

                    {/* Duration (for completed) */}
                    {visit.duration_minutes > 0 && (
                      <div className="flex items-center gap-2 text-sm text-slate-600 mb-2">
                        <Timer className="h-4 w-4 text-slate-400" />
                        <span>{visit.duration_minutes} minutes</span>
                      </div>
                    )}

                    {/* Visit Location */}
                    {visit.visit_location && (
                      <div className="flex items-center gap-2 text-sm text-slate-500">
                        <MapPin className="h-4 w-4 text-slate-400" />
                        <span className="line-clamp-1">{visit.visit_location}</span>
                      </div>
                    )}

                    {/* Time Info for in-progress */}
                    {visit.status === 'in_progress' && visit.start_time && (
                      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-2 text-xs text-amber-600">
                        <Play className="h-3 w-3" />
                        <span>Started at {formatTime(visit.start_time)}</span>
                      </div>
                    )}

                    {/* Time Info for completed */}
                    {visit.status === 'completed' && visit.start_time && (
                      <div className="mt-3 pt-3 border-t border-slate-100 flex items-center gap-4 text-xs text-slate-500">
                        <span className="flex items-center gap-1">
                          <Play className="h-3 w-3" />
                          {formatTime(visit.start_time)}
                        </span>
                        {visit.end_time && (
                          <span className="flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3" />
                            {formatTime(visit.end_time)}
                          </span>
                        )}
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Floating Action - Today's Summary */}
      {activeTab === 'pending' && pendingCount > 0 && (
        <div className="fixed bottom-4 left-4 right-4">
          <div className="bg-slate-900 text-white rounded-xl p-4 shadow-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">Today's Workload</p>
                <p className="text-lg font-semibold">{pendingCount} visits pending</p>
              </div>
              <Button 
                onClick={fetchVisits}
                variant="secondary"
                size="sm"
                className="bg-blue-500 hover:bg-blue-600 text-white"
              >
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TechnicianDashboard;
