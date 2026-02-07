import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { 
  Laptop, ArrowLeft, Shield, Calendar, MapPin, Building2, Tag,
  Clock, AlertTriangle, CheckCircle2, XCircle, Ticket, FileText,
  ChevronRight, Wrench, Package, ShoppingCart, TrendingUp, DollarSign,
  Activity, Cpu, HardDrive, Wifi, RefreshCw, User, Phone, Mail,
  BarChart3, PieChart, Timer, Settings, Monitor, Server, Zap,
  ArrowUpRight, ArrowDownRight, Minus, History, CircleDot
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Progress } from '../../components/ui/progress';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { toast } from 'sonner';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

const STATUS_CONFIG = {
  new: { label: 'New', color: 'bg-blue-100 text-blue-700' },
  pending_acceptance: { label: 'Pending', color: 'bg-purple-100 text-purple-700' },
  assigned: { label: 'Assigned', color: 'bg-indigo-100 text-indigo-700' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700' },
  pending_parts: { label: 'Pending Parts', color: 'bg-orange-100 text-orange-700' },
  completed: { label: 'Completed', color: 'bg-emerald-100 text-emerald-700' },
  closed: { label: 'Closed', color: 'bg-slate-100 text-slate-700' },
  cancelled: { label: 'Cancelled', color: 'bg-red-100 text-red-700' },
  resolved: { label: 'Resolved', color: 'bg-emerald-100 text-emerald-700' },
};

const DeviceDashboard = () => {
  const { deviceId } = useParams();
  const navigate = useNavigate();
  const { token } = useCompanyAuth();
  
  const [device, setDevice] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');

  const headers = { Authorization: `Bearer ${token}` };

  const [watchTowerData, setWatchTowerData] = useState(null);
  const [watchTowerLoading, setWatchTowerLoading] = useState(false);

  const fetchDeviceAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/api/company/devices/${deviceId}/analytics`, { headers });
      setDevice(response.data.device);
      setAnalytics(response.data);
    } catch (err) {
      console.error('Failed to fetch device analytics:', err);
      toast.error('Failed to load device dashboard');
      navigate('/company/devices');
    } finally {
      setLoading(false);
    }
  }, [deviceId, token, navigate]);

  const fetchWatchTowerStatus = useCallback(async () => {
    try {
      setWatchTowerLoading(true);
      const response = await axios.get(`${API}/api/watchtower/device/${deviceId}/status`, { headers });
      setWatchTowerData(response.data);
    } catch (err) {
      console.error('Failed to fetch WatchTower status:', err);
      setWatchTowerData({ integrated: false, message: 'Unable to connect to WatchTower' });
    } finally {
      setWatchTowerLoading(false);
    }
  }, [deviceId, token]);

  useEffect(() => {
    fetchDeviceAnalytics();
    fetchWatchTowerStatus();
  }, [fetchDeviceAnalytics, fetchWatchTowerStatus]);

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR' }).format(amount || 0);
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric'
    });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleDateString('en-GB', { 
      day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit'
    });
  };

  const getWarrantyStatus = () => {
    if (!device?.warranty_end) return { status: 'unknown', color: 'slate', days: 'N/A' };
    const endDate = new Date(device.warranty_end);
    const now = new Date();
    const daysLeft = Math.ceil((endDate - now) / (1000 * 60 * 60 * 24));
    
    if (daysLeft < 0) return { status: 'expired', color: 'red', days: Math.abs(daysLeft) };
    if (daysLeft <= 30) return { status: 'expiring', color: 'orange', days: daysLeft };
    if (daysLeft <= 90) return { status: 'warning', color: 'amber', days: daysLeft };
    return { status: 'active', color: 'emerald', days: daysLeft };
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!device || !analytics) return null;

  const warrantyInfo = getWarrantyStatus();
  const ticketAnalytics = analytics.ticket_analytics || {};
  const financialSummary = analytics.financial_summary || {};
  const amcAnalytics = analytics.amc_analytics;
  const rmmData = analytics.rmm_data || {};
  const lifecycleEvents = analytics.lifecycle_events || [];

  return (
    <div data-testid="device-dashboard" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate('/company/devices')}>
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-slate-900">
                {device.brand} {device.model}
              </h1>
              {amcAnalytics && (
                <Badge className="bg-emerald-100 text-emerald-700 border border-emerald-300">
                  AMC Active
                </Badge>
              )}
            </div>
            <p className="text-slate-500 font-mono text-sm mt-1">{device.serial_number}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={fetchDeviceAnalytics} variant="outline" disabled={loading}>
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <Link to={`/company/tickets?device=${device.id}`}>
            <Button className="bg-emerald-600 hover:bg-emerald-700">
              <Ticket className="h-4 w-4 mr-2" />
              Raise Service Request
            </Button>
          </Link>
        </div>
      </div>

      {/* Quick Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {/* Total Tickets */}
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Ticket className="h-8 w-8 text-blue-600" />
              <span className="text-3xl font-bold text-blue-700">{ticketAnalytics.total_tickets || 0}</span>
            </div>
            <p className="text-xs text-blue-600 mt-2 font-medium">Total Tickets</p>
          </CardContent>
        </Card>

        {/* Open Tickets */}
        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Clock className="h-8 w-8 text-amber-600" />
              <span className="text-3xl font-bold text-amber-700">{ticketAnalytics.open_tickets || 0}</span>
            </div>
            <p className="text-xs text-amber-600 mt-2 font-medium">Open Tickets</p>
          </CardContent>
        </Card>

        {/* Avg TAT */}
        <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Timer className="h-8 w-8 text-purple-600" />
              <span className="text-2xl font-bold text-purple-700">{ticketAnalytics.avg_tat_display || 'N/A'}</span>
            </div>
            <p className="text-xs text-purple-600 mt-2 font-medium">Avg TAT</p>
          </CardContent>
        </Card>

        {/* Total Spend */}
        <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <DollarSign className="h-8 w-8 text-emerald-600" />
              <span className="text-xl font-bold text-emerald-700">{formatCurrency(financialSummary.total_spend)}</span>
            </div>
            <p className="text-xs text-emerald-600 mt-2 font-medium">Total Spend</p>
          </CardContent>
        </Card>

        {/* Warranty */}
        <Card className={`bg-gradient-to-br from-${warrantyInfo.color}-50 to-${warrantyInfo.color}-100 border-${warrantyInfo.color}-200`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Shield className={`h-8 w-8 text-${warrantyInfo.color}-600`} />
              <span className={`text-2xl font-bold text-${warrantyInfo.color}-700`}>
                {warrantyInfo.days || 0}
              </span>
            </div>
            <p className={`text-xs text-${warrantyInfo.color}-600 mt-2 font-medium`}>
              {warrantyInfo.status === 'expired' ? 'Days Expired' : 'Days Left'}
            </p>
          </CardContent>
        </Card>

        {/* Parts Replaced */}
        <Card className="bg-gradient-to-br from-slate-50 to-slate-100 border-slate-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <Package className="h-8 w-8 text-slate-600" />
              <span className="text-3xl font-bold text-slate-700">{analytics.parts_replaced?.length || 0}</span>
            </div>
            <p className="text-xs text-slate-600 mt-2 font-medium">Parts Replaced</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Dashboard Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
        <TabsList className="bg-slate-100 p-1">
          <TabsTrigger value="overview" className="data-[state=active]:bg-white">
            <BarChart3 className="h-4 w-4 mr-2" />
            Overview
          </TabsTrigger>
          <TabsTrigger value="tickets" className="data-[state=active]:bg-white">
            <Ticket className="h-4 w-4 mr-2" />
            Tickets ({ticketAnalytics.total_tickets || 0})
          </TabsTrigger>
          <TabsTrigger value="lifecycle" className="data-[state=active]:bg-white">
            <History className="h-4 w-4 mr-2" />
            Lifecycle
          </TabsTrigger>
          {amcAnalytics && (
            <TabsTrigger value="amc" className="data-[state=active]:bg-white">
              <FileText className="h-4 w-4 mr-2" />
              AMC
            </TabsTrigger>
          )}
          <TabsTrigger value="rmm" className="data-[state=active]:bg-white">
            <Monitor className="h-4 w-4 mr-2" />
            WatchTower
          </TabsTrigger>
          <TabsTrigger value="details" className="data-[state=active]:bg-white">
            <Settings className="h-4 w-4 mr-2" />
            Details
          </TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Device Info Card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Laptop className="h-4 w-4" />
                  Device Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <InfoRow label="Serial Number" value={device.serial_number} mono />
                <InfoRow label="Asset Tag" value={device.asset_tag} />
                <InfoRow label="Type" value={device.device_type || device.category} />
                <InfoRow label="Brand" value={device.brand} />
                <InfoRow label="Model" value={device.model} />
                <InfoRow label="Status" value={
                  <Badge className={device.status === 'active' ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-700'}>
                    {device.status || 'Active'}
                  </Badge>
                } />
              </CardContent>
            </Card>

            {/* Warranty Status Card */}
            <Card className={warrantyInfo.status === 'expired' ? 'border-red-200 bg-red-50' : ''}>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  Warranty Status
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <div className="text-center py-4">
                  <div className={`w-20 h-20 mx-auto rounded-full flex items-center justify-center ${
                    warrantyInfo.status === 'active' ? 'bg-emerald-100' :
                    warrantyInfo.status === 'warning' ? 'bg-amber-100' :
                    warrantyInfo.status === 'expiring' ? 'bg-orange-100' :
                    'bg-red-100'
                  }`}>
                    <Shield className={`h-10 w-10 ${
                      warrantyInfo.status === 'active' ? 'text-emerald-600' :
                      warrantyInfo.status === 'warning' ? 'text-amber-600' :
                      warrantyInfo.status === 'expiring' ? 'text-orange-600' :
                      'text-red-600'
                    }`} />
                  </div>
                  <p className={`text-2xl font-bold mt-3 ${
                    warrantyInfo.status === 'active' ? 'text-emerald-700' :
                    warrantyInfo.status === 'warning' ? 'text-amber-700' :
                    warrantyInfo.status === 'expiring' ? 'text-orange-700' :
                    'text-red-700'
                  }`}>
                    {warrantyInfo.status === 'expired' ? 'Expired' : `${warrantyInfo.days} Days`}
                  </p>
                  <p className="text-slate-500 text-xs mt-1">
                    {warrantyInfo.status === 'expired' ? 'Warranty has expired' : 'Until warranty expires'}
                  </p>
                </div>
                <InfoRow label="Warranty Start" value={formatDate(device.warranty_start)} />
                <InfoRow label="Warranty End" value={formatDate(device.warranty_end)} />
                <InfoRow label="Warranty Type" value={device.warranty_type || 'Standard'} />
              </CardContent>
            </Card>

            {/* Financial Summary Card */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <DollarSign className="h-4 w-4" />
                  Financial Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="text-center py-4 border-b border-slate-100">
                  <p className="text-3xl font-bold text-emerald-600">{formatCurrency(financialSummary.total_spend + financialSummary.parts_cost)}</p>
                  <p className="text-slate-500 text-xs mt-1">Total Spend on Device</p>
                </div>
                <InfoRow label="Service Costs" value={formatCurrency(financialSummary.total_spend)} />
                <InfoRow label="Parts Cost" value={formatCurrency(financialSummary.parts_cost)} />
                <InfoRow label="Pending Quotations" value={financialSummary.pending_quotations || 0} />
                {device.purchase_price && (
                  <InfoRow label="Purchase Price" value={formatCurrency(device.purchase_price)} />
                )}
              </CardContent>
            </Card>
          </div>

          {/* Recent Activity */}
          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Activity className="h-4 w-4" />
                  Recent Activity
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={() => setActiveTab('lifecycle')}>
                  View All <ChevronRight className="h-4 w-4 ml-1" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {lifecycleEvents.slice(0, 5).map((event, idx) => (
                  <div key={idx} className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      event.type === 'service_ticket' ? 'bg-blue-100' :
                      event.type === 'part_replaced' ? 'bg-purple-100' :
                      event.type === 'amc_enrolled' ? 'bg-emerald-100' :
                      'bg-slate-100'
                    }`}>
                      {event.type === 'service_ticket' ? <Ticket className="h-4 w-4 text-blue-600" /> :
                       event.type === 'part_replaced' ? <Package className="h-4 w-4 text-purple-600" /> :
                       event.type === 'amc_enrolled' ? <FileText className="h-4 w-4 text-emerald-600" /> :
                       <CircleDot className="h-4 w-4 text-slate-600" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 text-sm">{event.title}</p>
                      <p className="text-xs text-slate-500 truncate">{event.description}</p>
                    </div>
                    <span className="text-xs text-slate-400">{formatDate(event.date)}</span>
                  </div>
                ))}
                {lifecycleEvents.length === 0 && (
                  <p className="text-center text-slate-500 py-8">No recent activity</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Tickets Tab */}
        <TabsContent value="tickets" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
            <Card className="bg-blue-50 border-blue-100">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold text-blue-700">{ticketAnalytics.total_tickets || 0}</p>
                <p className="text-xs text-blue-600 font-medium">Total Tickets</p>
              </CardContent>
            </Card>
            <Card className="bg-amber-50 border-amber-100">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold text-amber-700">{ticketAnalytics.open_tickets || 0}</p>
                <p className="text-xs text-amber-600 font-medium">Open</p>
              </CardContent>
            </Card>
            <Card className="bg-emerald-50 border-emerald-100">
              <CardContent className="p-4 text-center">
                <p className="text-3xl font-bold text-emerald-700">{ticketAnalytics.resolved_tickets || 0}</p>
                <p className="text-xs text-emerald-600 font-medium">Resolved</p>
              </CardContent>
            </Card>
            <Card className="bg-purple-50 border-purple-100">
              <CardContent className="p-4 text-center">
                <p className="text-xl font-bold text-purple-700">{ticketAnalytics.avg_tat_display || 'N/A'}</p>
                <p className="text-xs text-purple-600 font-medium">Avg Resolution Time</p>
              </CardContent>
            </Card>
          </div>

          <Card>
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base">Service Tickets</CardTitle>
                <Link to={`/company/tickets?device=${device.id}`}>
                  <Button size="sm" className="bg-emerald-600 hover:bg-emerald-700">
                    <Ticket className="h-4 w-4 mr-2" />
                    New Ticket
                  </Button>
                </Link>
              </div>
            </CardHeader>
            <CardContent>
              {ticketAnalytics.tickets?.length > 0 ? (
                <div className="space-y-2">
                  {ticketAnalytics.tickets.map((ticket) => {
                    const statusConfig = STATUS_CONFIG[ticket.status] || STATUS_CONFIG.new;
                    return (
                      <Link 
                        key={ticket.id} 
                        to={`/company/tickets/${ticket.id}`}
                        className="flex items-center justify-between p-3 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-2 h-2 rounded-full ${
                            ['new', 'pending_acceptance', 'assigned', 'in_progress'].includes(ticket.status) ? 'bg-amber-500' :
                            ['completed', 'closed', 'resolved'].includes(ticket.status) ? 'bg-emerald-500' :
                            'bg-slate-400'
                          }`} />
                          <div>
                            <p className="font-medium text-slate-900 text-sm">
                              <span className="font-mono text-emerald-600">#{ticket.ticket_number}</span>
                              {' - '}
                              {ticket.title || ticket.subject}
                            </p>
                            <p className="text-xs text-slate-500">{formatDate(ticket.created_at)}</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className={statusConfig.color}>{statusConfig.label}</Badge>
                          <ChevronRight className="h-4 w-4 text-slate-400" />
                        </div>
                      </Link>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-8">
                  <Ticket className="h-12 w-12 text-slate-300 mx-auto mb-3" />
                  <p className="text-slate-500">No tickets found for this device</p>
                  <Link to={`/company/tickets?device=${device.id}`}>
                    <Button size="sm" className="mt-3 bg-emerald-600 hover:bg-emerald-700">
                      Create First Ticket
                    </Button>
                  </Link>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Lifecycle Tab */}
        <TabsContent value="lifecycle" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <History className="h-4 w-4" />
                Device Lifecycle
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="relative">
                {/* Timeline line */}
                <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200" />
                
                <div className="space-y-4">
                  {lifecycleEvents.map((event, idx) => (
                    <div key={idx} className="relative pl-10">
                      {/* Timeline dot */}
                      <div className={`absolute left-2 w-5 h-5 rounded-full border-2 border-white ${
                        event.type === 'device_registered' ? 'bg-blue-500' :
                        event.type === 'warranty_start' ? 'bg-emerald-500' :
                        event.type === 'warranty_end' ? 'bg-red-500' :
                        event.type === 'amc_enrolled' ? 'bg-purple-500' :
                        event.type === 'service_ticket' ? 'bg-amber-500' :
                        event.type === 'part_replaced' ? 'bg-indigo-500' :
                        'bg-slate-400'
                      }`} />
                      
                      <div className={`p-4 rounded-lg border ${
                        event.is_future ? 'bg-slate-50 border-dashed border-slate-300' : 'bg-white border-slate-200'
                      }`}>
                        <div className="flex items-center justify-between mb-1">
                          <span className="font-medium text-slate-900">{event.title}</span>
                          {event.status && (
                            <Badge className={STATUS_CONFIG[event.status]?.color || 'bg-slate-100 text-slate-700'}>
                              {STATUS_CONFIG[event.status]?.label || event.status}
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-600">{event.description}</p>
                        <div className="flex items-center justify-between mt-2">
                          <span className="text-xs text-slate-400">{formatDateTime(event.date)}</span>
                          {event.cost && (
                            <span className="text-sm font-medium text-emerald-600">{formatCurrency(event.cost)}</span>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                  
                  {lifecycleEvents.length === 0 && (
                    <p className="text-center text-slate-500 py-8">No lifecycle events recorded</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* AMC Tab */}
        {amcAnalytics && (
          <TabsContent value="amc" className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* AMC Status Card */}
              <Card className="bg-gradient-to-br from-emerald-50 to-emerald-100 border-emerald-200">
                <CardContent className="p-6 text-center">
                  <div className="w-16 h-16 mx-auto bg-emerald-200 rounded-full flex items-center justify-center mb-4">
                    <CheckCircle2 className="h-8 w-8 text-emerald-600" />
                  </div>
                  <p className="text-xl font-bold text-emerald-700">AMC Active</p>
                  <p className="text-sm text-emerald-600 mt-1">{amcAnalytics.contract_name}</p>
                </CardContent>
              </Card>

              {/* Coverage Progress */}
              <Card>
                <CardContent className="p-6">
                  <div className="text-center mb-4">
                    <p className="text-4xl font-bold text-slate-900">{amcAnalytics.days_remaining}</p>
                    <p className="text-sm text-slate-500">Days Remaining</p>
                  </div>
                  <Progress value={amcAnalytics.coverage_percentage} className="h-2" />
                  <div className="flex justify-between text-xs text-slate-500 mt-2">
                    <span>{formatDate(amcAnalytics.coverage_start)}</span>
                    <span>{formatDate(amcAnalytics.coverage_end)}</span>
                  </div>
                </CardContent>
              </Card>

              {/* PM Compliance */}
              <Card>
                <CardContent className="p-6 text-center">
                  <div className="relative w-24 h-24 mx-auto mb-4">
                    <svg className="w-24 h-24 transform -rotate-90">
                      <circle cx="48" cy="48" r="40" stroke="#e2e8f0" strokeWidth="8" fill="none" />
                      <circle 
                        cx="48" cy="48" r="40" 
                        stroke="#10b981" strokeWidth="8" fill="none"
                        strokeDasharray={`${(amcAnalytics.pm_compliance / 100) * 251.2} 251.2`}
                        strokeLinecap="round"
                      />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                      <span className="text-xl font-bold text-slate-900">{amcAnalytics.pm_compliance}%</span>
                    </div>
                  </div>
                  <p className="text-sm text-slate-500">PM Compliance</p>
                  <p className="text-xs text-slate-400 mt-1">
                    {amcAnalytics.pm_visits_completed} of {amcAnalytics.pm_visits_expected} visits
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* AMC Details */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Contract Details</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3 text-sm">
                  <InfoRow label="Contract Name" value={amcAnalytics.contract_name} />
                  <InfoRow label="AMC Type" value={amcAnalytics.amc_type} />
                  <InfoRow label="PM Schedule" value={amcAnalytics.pm_schedule?.replace('_', ' ')} />
                  <InfoRow label="Next PM Due" value={formatDate(amcAnalytics.next_pm_due)} />
                  <InfoRow label="Contract Value" value={formatCurrency(amcAnalytics.contract_value)} />
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Coverage Includes</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    {Array.isArray(amcAnalytics.coverage_includes) && amcAnalytics.coverage_includes.length > 0 ? (
                      amcAnalytics.coverage_includes.map((item, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                          <span>{item}</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-slate-500 text-sm">Coverage details not specified</p>
                    )}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Entitlements */}
            {amcAnalytics.entitlements && Object.keys(amcAnalytics.entitlements).length > 0 && (
              <Card>
                <CardHeader className="pb-3">
                  <CardTitle className="text-base">Entitlements</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {Object.entries(amcAnalytics.entitlements).map(([key, value]) => (
                      <div key={key} className="text-center p-3 bg-slate-50 rounded-lg">
                        <p className="text-2xl font-bold text-slate-900">{value}</p>
                        <p className="text-xs text-slate-500 capitalize">{key.replace(/_/g, ' ')}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        )}

        {/* WatchTower Tab */}
        <TabsContent value="rmm" className="space-y-4">
          {rmmData.integrated ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* WatchTower metrics would go here when integrated */}
            </div>
          ) : (
            <Card className="border-dashed border-2 border-indigo-200 bg-gradient-to-br from-indigo-50 to-slate-50">
              <CardContent className="py-12 text-center">
                <div className="w-20 h-20 mx-auto bg-indigo-100 rounded-full flex items-center justify-center mb-6">
                  <Monitor className="h-10 w-10 text-indigo-600" />
                </div>
                <h3 className="text-xl font-semibold text-indigo-900 mb-2">WatchTower - Real-Time Monitoring</h3>
                <p className="text-slate-600 max-w-md mx-auto mb-6">
                  WatchTower provides real-time device monitoring, including CPU usage, memory, disk space, installed software, pending updates, and security alerts.
                </p>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 max-w-2xl mx-auto">
                  <div className="p-4 bg-white rounded-lg shadow-sm border border-indigo-100">
                    <Cpu className="h-6 w-6 text-indigo-500 mx-auto mb-2" />
                    <p className="text-xs text-slate-600 font-medium">CPU Usage</p>
                  </div>
                  <div className="p-4 bg-white rounded-lg shadow-sm border border-indigo-100">
                    <Server className="h-6 w-6 text-indigo-500 mx-auto mb-2" />
                    <p className="text-xs text-slate-600 font-medium">Memory</p>
                  </div>
                  <div className="p-4 bg-white rounded-lg shadow-sm border border-indigo-100">
                    <HardDrive className="h-6 w-6 text-indigo-500 mx-auto mb-2" />
                    <p className="text-xs text-slate-600 font-medium">Disk Space</p>
                  </div>
                  <div className="p-4 bg-white rounded-lg shadow-sm border border-indigo-100">
                    <Wifi className="h-6 w-6 text-indigo-500 mx-auto mb-2" />
                    <p className="text-xs text-slate-600 font-medium">Network</p>
                  </div>
                </div>
                <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg max-w-md mx-auto">
                  <p className="text-sm text-amber-800">
                    <strong>Setup Required:</strong> Install the WatchTower agent on this device to enable real-time monitoring.
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Details Tab */}
        <TabsContent value="details" className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Configuration */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Configuration
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <InfoRow label="Processor" value={device.processor || device.cpu} />
                <InfoRow label="RAM" value={device.ram || device.memory} />
                <InfoRow label="Storage" value={device.storage || device.hard_drive} />
                <InfoRow label="Operating System" value={device.os || device.operating_system} />
                <InfoRow label="OS Version" value={device.os_version} />
              </CardContent>
            </Card>

            {/* Assignment */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Assignment
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <InfoRow label="Assigned To" value={device.assigned_employee_name || device.assigned_to} />
                <InfoRow label="Department" value={device.department} />
                <InfoRow label="Location" value={device.location || device.site_name} />
                {device.assigned_employee_email && (
                  <InfoRow label="Email" value={device.assigned_employee_email} />
                )}
              </CardContent>
            </Card>

            {/* Purchase Info */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <ShoppingCart className="h-4 w-4" />
                  Purchase Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <InfoRow label="Purchase Date" value={formatDate(device.purchase_date)} />
                <InfoRow label="Purchase Price" value={device.purchase_price ? formatCurrency(device.purchase_price) : '-'} />
                <InfoRow label="Vendor" value={device.vendor || device.supplier} />
                <InfoRow label="Invoice Number" value={device.invoice_number} />
              </CardContent>
            </Card>

            {/* Network Info */}
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Wifi className="h-4 w-4" />
                  Network Information
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <InfoRow label="IP Address" value={device.ip_address} />
                <InfoRow label="MAC Address" value={device.mac_address} />
                <InfoRow label="Hostname" value={device.hostname || device.computer_name} />
              </CardContent>
            </Card>
          </div>

          {/* Custom Fields */}
          {device.custom_fields && Object.keys(device.custom_fields).length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">Additional Information</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  {Object.entries(device.custom_fields).map(([key, value]) => (
                    <div key={key} className="p-3 bg-slate-50 rounded-lg">
                      <p className="text-xs text-slate-500 capitalize">{key.replace(/_/g, ' ')}</p>
                      <p className="font-medium text-slate-900">{value || '-'}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Parts Replaced */}
          {analytics.parts_replaced?.length > 0 && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base flex items-center gap-2">
                  <Package className="h-4 w-4" />
                  Parts Replaced
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {analytics.parts_replaced.map((part, idx) => (
                    <div key={idx} className="flex items-center justify-between p-3 bg-slate-50 rounded-lg">
                      <div>
                        <p className="font-medium text-slate-900">{part.name || part.part_name}</p>
                        <p className="text-xs text-slate-500">{part.description}</p>
                      </div>
                      <div className="text-right">
                        {(part.cost || part.price) && (
                          <p className="font-medium text-emerald-600">{formatCurrency(part.cost || part.price)}</p>
                        )}
                        <p className="text-xs text-slate-400">{formatDate(part.created_at || part.replaced_at)}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Helper component for info rows
const InfoRow = ({ label, value, mono }) => (
  <div className="flex justify-between py-1 border-b border-slate-50 last:border-0">
    <span className="text-slate-500">{label}</span>
    <span className={`font-medium text-slate-900 ${mono ? 'font-mono' : ''}`}>
      {value || '-'}
    </span>
  </div>
);

export default DeviceDashboard;
