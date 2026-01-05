import { useState, useEffect } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  Laptop, ArrowLeft, Shield, Calendar, MapPin, Building2, Tag,
  Clock, AlertTriangle, CheckCircle2, XCircle, Ticket, FileText,
  ChevronRight, Wrench
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyDeviceDetails = () => {
  const { deviceId } = useParams();
  const { token } = useCompanyAuth();
  const navigate = useNavigate();
  const [device, setDevice] = useState(null);
  const [parts, setParts] = useState([]);
  const [serviceHistory, setServiceHistory] = useState([]);
  const [amcInfo, setAmcInfo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDevice();
  }, [deviceId]);

  const fetchDevice = async () => {
    try {
      const response = await axios.get(`${API}/company/devices/${deviceId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      // API returns { device: {...}, parts: [...], service_history: [...], amc_info: {...} }
      setDevice(response.data.device);
      setParts(response.data.parts || []);
      setServiceHistory(response.data.service_history || []);
      setAmcInfo(response.data.amc_info);
    } catch (error) {
      toast.error('Failed to load device details');
      navigate('/company/devices');
    } finally {
      setLoading(false);
    }
  };

  const getWarrantyStatus = () => {
    if (!device?.warranty_end_date) return { status: 'unknown', label: 'Unknown', color: 'slate' };
    
    const endDate = new Date(device.warranty_end_date);
    const today = new Date();
    const daysLeft = Math.ceil((endDate - today) / (1000 * 60 * 60 * 24));
    
    if (daysLeft < 0) return { status: 'expired', label: 'Expired', color: 'red', days: Math.abs(daysLeft) };
    if (daysLeft <= 30) return { status: 'critical', label: `${daysLeft} days left`, color: 'red', days: daysLeft };
    if (daysLeft <= 60) return { status: 'warning', label: `${daysLeft} days left`, color: 'amber', days: daysLeft };
    if (daysLeft <= 90) return { status: 'attention', label: `${daysLeft} days left`, color: 'orange', days: daysLeft };
    return { status: 'active', label: 'Active', color: 'emerald', days: daysLeft };
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return 'N/A';
    return new Date(dateStr).toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric'
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (!device) return null;

  const warranty = getWarrantyStatus();
  const colorClasses = {
    red: 'bg-red-50 text-red-700 border-red-200',
    amber: 'bg-amber-50 text-amber-700 border-amber-200',
    orange: 'bg-orange-50 text-orange-700 border-orange-200',
    emerald: 'bg-emerald-50 text-emerald-700 border-emerald-200',
    slate: 'bg-slate-50 text-slate-600 border-slate-200',
  };

  return (
    <div className="space-y-6" data-testid="device-details-page">
      {/* Back Button */}
      <Link 
        to="/company/devices" 
        className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-900"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Devices
      </Link>

      {/* Header Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-4">
          <div className="flex items-start gap-4">
            <div className="w-16 h-16 bg-slate-100 rounded-xl flex items-center justify-center">
              <Laptop className="h-8 w-8 text-slate-600" />
            </div>
            <div>
              <h1 className="text-2xl font-bold text-slate-900">{device.serial_number}</h1>
              <p className="text-slate-500 mt-1">
                {device.category} • {device.brand} {device.model}
              </p>
              {device.site_name && (
                <div className="flex items-center gap-1.5 text-sm text-slate-500 mt-2">
                  <MapPin className="h-4 w-4" />
                  {device.site_name}
                </div>
              )}
            </div>
          </div>
          
          <div className="flex flex-col items-end gap-3">
            <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium border ${colorClasses[warranty.color]}`}>
              <Shield className="h-5 w-5" />
              Warranty: {warranty.label}
            </div>
            <Link to={`/company/tickets?device=${device.id}`}>
              <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="raise-ticket-btn">
                <Ticket className="h-4 w-4 mr-2" />
                Raise Service Request
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Info Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Device Information */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Laptop className="h-5 w-5 text-slate-400" />
            Device Information
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Serial Number</dt>
              <dd className="font-medium text-slate-900">{device.serial_number}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Category</dt>
              <dd className="font-medium text-slate-900">{device.category || 'N/A'}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Brand</dt>
              <dd className="font-medium text-slate-900">{device.brand || 'N/A'}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Model</dt>
              <dd className="font-medium text-slate-900">{device.model || 'N/A'}</dd>
            </div>
            {device.asset_tag && (
              <div className="flex justify-between py-2 border-b border-slate-100">
                <dt className="text-slate-500">Asset Tag</dt>
                <dd className="font-medium text-slate-900">{device.asset_tag}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Warranty Information */}
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-900 mb-4 flex items-center gap-2">
            <Shield className="h-5 w-5 text-slate-400" />
            Warranty Information
          </h2>
          <dl className="space-y-3">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Status</dt>
              <dd className={`font-medium ${warranty.color === 'emerald' ? 'text-emerald-600' : warranty.color === 'red' ? 'text-red-600' : 'text-amber-600'}`}>
                {warranty.status === 'expired' ? 'Expired' : 'Active'}
              </dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">Start Date</dt>
              <dd className="font-medium text-slate-900">{formatDate(device.warranty_start_date)}</dd>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <dt className="text-slate-500">End Date</dt>
              <dd className="font-medium text-slate-900">{formatDate(device.warranty_end_date)}</dd>
            </div>
            {warranty.days !== undefined && (
              <div className="flex justify-between py-2">
                <dt className="text-slate-500">
                  {warranty.status === 'expired' ? 'Expired' : 'Remaining'}
                </dt>
                <dd className={`font-medium ${warranty.color === 'emerald' ? 'text-emerald-600' : warranty.color === 'red' ? 'text-red-600' : 'text-amber-600'}`}>
                  {warranty.status === 'expired' ? `${warranty.days} days ago` : `${warranty.days} days`}
                </dd>
              </div>
            )}
          </dl>
        </div>
      </div>

      {/* Service History */}
      {serviceHistory && serviceHistory.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Wrench className="h-5 w-5 text-slate-400" />
              Service History
            </h2>
          </div>
          <div className="divide-y divide-slate-100">
            {serviceHistory.map((record, index) => (
              <div key={index} className="p-4 hover:bg-slate-50">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium text-slate-900">{record.service_type}</p>
                    <p className="text-sm text-slate-500 mt-1">{record.problem_reported || record.description}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm font-medium text-slate-900">{formatDate(record.service_date)}</p>
                    <p className="text-xs text-slate-500">{record.technician_name || record.technician}</p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Related Tickets */}
      {device.tickets && device.tickets.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100">
            <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
              <Ticket className="h-5 w-5 text-slate-400" />
              Related Tickets
            </h2>
            <Link 
              to={`/company/tickets?device=${device.id}`}
              className="text-sm text-emerald-600 hover:text-emerald-700"
            >
              View all
            </Link>
          </div>
          <div className="divide-y divide-slate-100">
            {device.tickets.slice(0, 5).map((ticket) => (
              <Link
                key={ticket.id}
                to={`/company/tickets/${ticket.id}`}
                className="flex items-center justify-between p-4 hover:bg-slate-50"
              >
                <div>
                  <p className="font-medium text-slate-900">{ticket.subject}</p>
                  <p className="text-sm text-slate-500">{ticket.ticket_number}</p>
                </div>
                <div className="flex items-center gap-3">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                    ticket.status === 'open' ? 'bg-amber-50 text-amber-700' :
                    ticket.status === 'in_progress' ? 'bg-blue-50 text-blue-700' :
                    ticket.status === 'resolved' ? 'bg-emerald-50 text-emerald-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                    {ticket.status?.replace('_', ' ')}
                  </span>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </div>
              </Link>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default CompanyDeviceDetails;
