import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Shield, CheckCircle2, XCircle, AlertCircle, Clock,
  Laptop, Printer, Monitor, Router, Camera, HardDrive, Cpu, Server,
  Building2, User, Calendar, MapPin, Wrench, AlertTriangle,
  ChevronRight, QrCode, Phone, Mail
} from 'lucide-react';
import { useSettings } from '../../context/SettingsContext';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../../components/ui/dialog';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const deviceIcons = {
  'Laptop': Laptop,
  'CCTV': Camera,
  'Printer': Printer,
  'Monitor': Monitor,
  'Router': Router,
  'Server': Server,
  'Desktop': Cpu,
  'UPS': HardDrive,
};

const PublicDevicePage = () => {
  const { identifier } = useParams();
  const { settings } = useSettings();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showRequestDialog, setShowRequestDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [ticketNumber, setTicketNumber] = useState('');
  
  const [requestForm, setRequestForm] = useState({
    name: '',
    email: '',
    phone: '',
    issue_category: 'hardware',
    description: ''
  });

  useEffect(() => {
    fetchDeviceInfo();
  }, [identifier]);

  const fetchDeviceInfo = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/device/${identifier}/info`);
      setData(response.data);
      setError(null);
    } catch (err) {
      setError(err.response?.data?.detail || 'Device not found');
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitRequest = async (e) => {
    e.preventDefault();
    
    if (!requestForm.name || !requestForm.email || !requestForm.description) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    try {
      setSubmitting(true);
      const response = await axios.post(`${API}/device/${identifier}/quick-request`, requestForm);
      setTicketNumber(response.data.ticket_number);
      setSubmitted(true);
      toast.success('Service request submitted successfully!');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to submit request');
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return '-';
    try {
      return new Date(dateStr).toLocaleDateString('en-GB', {
        day: '2-digit',
        month: 'short',
        year: 'numeric'
      });
    } catch {
      return dateStr;
    }
  };

  const DeviceIcon = data?.device?.device_type ? 
    (deviceIcons[data.device.device_type] || Laptop) : Laptop;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-100">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-slate-500">Loading device information...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="w-full px-4 py-4 bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <Link to="/" className="flex items-center gap-3">
            {(settings.logo_base64 || settings.logo_url) ? (
              <img 
                src={settings.logo_base64 || settings.logo_url} 
                alt="Logo" 
                className="h-8 w-auto"
              />
            ) : (
              <Shield className="h-7 w-7 text-[#0F62FE]" />
            )}
            <span className="text-lg font-semibold text-slate-900">{settings.company_name}</span>
          </Link>
          <div className="flex items-center gap-2">
            <QrCode className="h-4 w-4 text-slate-400" />
            <span className="text-sm text-slate-500">Device Info</span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {error ? (
            /* Error State */
            <Card className="text-center py-12" data-testid="device-error">
              <CardContent>
                <div className="w-16 h-16 bg-amber-50 rounded-full flex items-center justify-center mx-auto mb-6">
                  <AlertCircle className="h-8 w-8 text-amber-500" />
                </div>
                <h2 className="text-2xl font-semibold text-slate-900 mb-3">Device Not Found</h2>
                <p className="text-slate-500 mb-8 max-w-md mx-auto">
                  We couldn&apos;t find a device with the identifier &quot;{identifier}&quot;. 
                  Please check the QR code or serial number.
                </p>
                <Link to="/">
                  <Button className="bg-[#0F62FE] hover:bg-[#0043CE]">
                    Go to Home
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ) : data ? (
            <div className="space-y-6 animate-in fade-in duration-500">
              {/* Device Header Card */}
              <Card className="overflow-hidden" data-testid="device-info-card">
                <div className="bg-gradient-to-r from-slate-900 to-slate-800 px-6 py-6 text-white">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-14 h-14 bg-white/10 rounded-xl flex items-center justify-center backdrop-blur-sm">
                        <DeviceIcon className="h-7 w-7 text-white" />
                      </div>
                      <div>
                        <h1 className="text-xl font-bold">{data.device.brand} {data.device.model}</h1>
                        <p className="text-slate-300 text-sm mt-0.5">{data.device.device_type}</p>
                      </div>
                    </div>
                    <Badge 
                      variant={data.device.warranty_active ? "default" : "secondary"}
                      className={data.device.warranty_active ? "bg-emerald-500/90 hover:bg-emerald-500" : ""}
                    >
                      {data.device.warranty_active ? '✓ Protected' : 'Not Covered'}
                    </Badge>
                  </div>
                </div>
                
                <CardContent className="p-6">
                  <div className="grid sm:grid-cols-2 gap-6">
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 text-sm">
                        <span className="text-slate-500 w-28">Serial Number</span>
                        <span className="font-mono font-medium text-slate-900" data-testid="serial-number">
                          {data.device.serial_number}
                        </span>
                      </div>
                      {data.device.asset_tag && (
                        <div className="flex items-center gap-3 text-sm">
                          <span className="text-slate-500 w-28">Asset Tag</span>
                          <span className="font-mono font-medium text-slate-900">{data.device.asset_tag}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-3 text-sm">
                        <span className="text-slate-500 w-28">Purchase Date</span>
                        <span className="text-slate-900">{formatDate(data.device.purchase_date)}</span>
                      </div>
                      {data.device.location && (
                        <div className="flex items-center gap-3 text-sm">
                          <span className="text-slate-500 w-28">Location</span>
                          <span className="text-slate-900">{data.device.location}</span>
                        </div>
                      )}
                    </div>
                    <div className="space-y-4">
                      <div className="flex items-center gap-3 text-sm">
                        <Building2 className="h-4 w-4 text-slate-400" />
                        <span className="text-slate-900">{data.company.name}</span>
                      </div>
                      {data.assigned_user && (
                        <div className="flex items-center gap-3 text-sm">
                          <User className="h-4 w-4 text-slate-400" />
                          <span className="text-slate-900">{data.assigned_user}</span>
                        </div>
                      )}
                      {data.site && (
                        <div className="flex items-center gap-3 text-sm">
                          <MapPin className="h-4 w-4 text-slate-400" />
                          <span className="text-slate-900">{data.site.name}</span>
                        </div>
                      )}
                      <div className="flex items-center gap-3 text-sm">
                        <Calendar className="h-4 w-4 text-slate-400" />
                        <span className="text-slate-900">
                          Warranty until {formatDate(data.device.warranty_end_date)}
                        </span>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Coverage Status */}
              <div className="grid sm:grid-cols-2 gap-4">
                {/* Warranty Status */}
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {data.device.warranty_active ? (
                          <div className="w-10 h-10 bg-emerald-50 rounded-full flex items-center justify-center">
                            <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                          </div>
                        ) : (
                          <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
                            <XCircle className="h-5 w-5 text-slate-400" />
                          </div>
                        )}
                        <div>
                          <p className="font-medium text-slate-900">Device Warranty</p>
                          <p className="text-sm text-slate-500">
                            {data.device.warranty_active ? 'Active coverage' : 'Expired'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                {/* AMC Status */}
                <Card>
                  <CardContent className="p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        {data.amc ? (
                          <div className="w-10 h-10 bg-blue-50 rounded-full flex items-center justify-center">
                            <Shield className="h-5 w-5 text-blue-500" />
                          </div>
                        ) : (
                          <div className="w-10 h-10 bg-slate-100 rounded-full flex items-center justify-center">
                            <Shield className="h-5 w-5 text-slate-400" />
                          </div>
                        )}
                        <div>
                          <p className="font-medium text-slate-900">
                            {data.amc ? data.amc.name : 'No AMC'}
                          </p>
                          <p className="text-sm text-slate-500">
                            {data.amc ? `Until ${formatDate(data.amc.coverage_end)}` : 'No active contract'}
                          </p>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Parts Warranty */}
              {data.parts && data.parts.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Cpu className="h-4 w-4" />
                      Replaced Parts
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-2">
                      {data.parts.map((part, index) => (
                        <div 
                          key={index}
                          className="flex items-center justify-between py-2 px-3 bg-slate-50 rounded-lg"
                        >
                          <span className="text-sm font-medium text-slate-700">{part.part_name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-xs text-slate-500">
                              Expires {formatDate(part.warranty_expiry_date)}
                            </span>
                            {part.warranty_active ? (
                              <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                            ) : (
                              <XCircle className="h-4 w-4 text-slate-400" />
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Service History */}
              {data.service_history && data.service_history.length > 0 && (
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="text-base flex items-center gap-2">
                      <Wrench className="h-4 w-4" />
                      Recent Service History
                      {data.service_count > 5 && (
                        <Badge variant="secondary" className="ml-2">
                          {data.service_count} total
                        </Badge>
                      )}
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <div className="space-y-3">
                      {data.service_history.map((service, index) => (
                        <div 
                          key={index}
                          className="flex items-start gap-3 py-3 border-b border-slate-100 last:border-0"
                        >
                          <div className="w-8 h-8 bg-blue-50 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5">
                            <Clock className="h-4 w-4 text-blue-500" />
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between gap-2">
                              <p className="text-sm font-medium text-slate-900">{service.service_type}</p>
                              <span className="text-xs text-slate-500">{formatDate(service.service_date)}</span>
                            </div>
                            <p className="text-sm text-slate-600 mt-0.5 line-clamp-2">{service.action_taken}</p>
                            {service.technician_name && (
                              <p className="text-xs text-slate-400 mt-1">By {service.technician_name}</p>
                            )}
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              )}

              {/* Quick Service Request Button */}
              <Card className="border-2 border-dashed border-[#0F62FE]/30 bg-[#0F62FE]/5">
                <CardContent className="p-6">
                  <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-[#0F62FE]/10 rounded-full flex items-center justify-center">
                        <AlertTriangle className="h-6 w-6 text-[#0F62FE]" />
                      </div>
                      <div>
                        <h3 className="font-semibold text-slate-900">Need Help?</h3>
                        <p className="text-sm text-slate-600">Report an issue - no login required</p>
                      </div>
                    </div>
                    
                    <Dialog open={showRequestDialog} onOpenChange={setShowRequestDialog}>
                      <DialogTrigger asChild>
                        <Button 
                          className="bg-[#0F62FE] hover:bg-[#0043CE] w-full sm:w-auto"
                          data-testid="report-issue-btn"
                        >
                          <AlertTriangle className="h-4 w-4 mr-2" />
                          Report Issue
                        </Button>
                      </DialogTrigger>
                      <DialogContent className="sm:max-w-md">
                        {submitted ? (
                          <div className="text-center py-6">
                            <div className="w-16 h-16 bg-emerald-50 rounded-full flex items-center justify-center mx-auto mb-4">
                              <CheckCircle2 className="h-8 w-8 text-emerald-500" />
                            </div>
                            <DialogTitle className="text-xl mb-2">Request Submitted!</DialogTitle>
                            <DialogDescription className="mb-4">
                              Your ticket number is:
                            </DialogDescription>
                            <div className="bg-slate-100 rounded-lg py-3 px-4 font-mono text-lg font-bold text-slate-900 mb-4">
                              {ticketNumber}
                            </div>
                            <p className="text-sm text-slate-500 mb-6">
                              Our team will contact you shortly at the email/phone provided.
                            </p>
                            <Button onClick={() => {
                              setShowRequestDialog(false);
                              setSubmitted(false);
                              setRequestForm({ name: '', email: '', phone: '', issue_category: 'hardware', description: '' });
                            }}>
                              Close
                            </Button>
                          </div>
                        ) : (
                          <>
                            <DialogHeader>
                              <DialogTitle>Report an Issue</DialogTitle>
                              <DialogDescription>
                                Submit a quick service request for this device. No login needed.
                              </DialogDescription>
                            </DialogHeader>
                            <form onSubmit={handleSubmitRequest} className="space-y-4 mt-4">
                              <div className="space-y-2">
                                <Label htmlFor="name">Your Name *</Label>
                                <Input
                                  id="name"
                                  placeholder="Enter your name"
                                  value={requestForm.name}
                                  onChange={(e) => setRequestForm({...requestForm, name: e.target.value})}
                                  required
                                  data-testid="request-name-input"
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label htmlFor="email">Email Address *</Label>
                                <Input
                                  id="email"
                                  type="email"
                                  placeholder="your@email.com"
                                  value={requestForm.email}
                                  onChange={(e) => setRequestForm({...requestForm, email: e.target.value})}
                                  required
                                  data-testid="request-email-input"
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label htmlFor="phone">Phone Number</Label>
                                <Input
                                  id="phone"
                                  type="tel"
                                  placeholder="+91 98765 43210"
                                  value={requestForm.phone}
                                  onChange={(e) => setRequestForm({...requestForm, phone: e.target.value})}
                                  data-testid="request-phone-input"
                                />
                              </div>
                              
                              <div className="space-y-2">
                                <Label htmlFor="category">Issue Category</Label>
                                <Select 
                                  value={requestForm.issue_category}
                                  onValueChange={(value) => setRequestForm({...requestForm, issue_category: value})}
                                >
                                  <SelectTrigger data-testid="request-category-select">
                                    <SelectValue placeholder="Select category" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="hardware">Hardware Issue</SelectItem>
                                    <SelectItem value="software">Software Issue</SelectItem>
                                    <SelectItem value="network">Network Issue</SelectItem>
                                    <SelectItem value="performance">Performance Issue</SelectItem>
                                    <SelectItem value="other">Other</SelectItem>
                                  </SelectContent>
                                </Select>
                              </div>
                              
                              <div className="space-y-2">
                                <Label htmlFor="description">Describe the Issue *</Label>
                                <Textarea
                                  id="description"
                                  placeholder="Please describe the issue you're experiencing..."
                                  rows={4}
                                  value={requestForm.description}
                                  onChange={(e) => setRequestForm({...requestForm, description: e.target.value})}
                                  required
                                  data-testid="request-description-input"
                                />
                              </div>
                              
                              <div className="flex justify-end gap-3 pt-2">
                                <Button 
                                  type="button" 
                                  variant="outline" 
                                  onClick={() => setShowRequestDialog(false)}
                                >
                                  Cancel
                                </Button>
                                <Button 
                                  type="submit" 
                                  className="bg-[#0F62FE] hover:bg-[#0043CE]"
                                  disabled={submitting}
                                  data-testid="submit-request-btn"
                                >
                                  {submitting ? 'Submitting...' : 'Submit Request'}
                                </Button>
                              </div>
                            </form>
                          </>
                        )}
                      </DialogContent>
                    </Dialog>
                  </div>
                </CardContent>
              </Card>

              {/* Footer Note */}
              <p className="text-center text-sm text-slate-400 pt-4">
                Scanned via QR Code • {settings.company_name}
              </p>
            </div>
          ) : null}
        </div>
      </main>
    </div>
  );
};

export default PublicDevicePage;
