import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, MapPin, Phone, Building2, Laptop, Clock, 
  CheckCircle2, Camera, AlertCircle, Play, User,
  Calendar, FileText, Wrench, Package
} from 'lucide-react';
import { useEngineerAuth } from '../../context/EngineerAuthContext';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = process.env.REACT_APP_BACKEND_URL;

const EngineerVisitDetail = () => {
  const { visitId } = useParams();
  const navigate = useNavigate();
  const { token } = useEngineerAuth();
  
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [showServiceForm, setShowServiceForm] = useState(false);
  const [showCheckoutDialog, setShowCheckoutDialog] = useState(false);
  
  const [serviceReport, setServiceReport] = useState({
    problem_found: '',
    action_taken: '',
    parts_used: [],
    notes: ''
  });
  
  const [customerName, setCustomerName] = useState('');
  const [newPart, setNewPart] = useState({ name: '', quantity: 1 });

  useEffect(() => {
    fetchVisitDetails();
  }, [visitId]);

  const fetchVisitDetails = async () => {
    try {
      const response = await axios.get(`${API}/api/engineer/visits/${visitId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setData(response.data);
      
      // Pre-fill service report if exists
      if (response.data.visit.problem_found) {
        setServiceReport({
          problem_found: response.data.visit.problem_found || '',
          action_taken: response.data.visit.action_taken || '',
          parts_used: response.data.visit.parts_used || [],
          notes: response.data.visit.check_out_notes || ''
        });
      }
    } catch (err) {
      toast.error('Failed to load visit details');
      navigate('/engineer/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckIn = async () => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/engineer/visits/${visitId}/check-in`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Checked in successfully!');
      fetchVisitDetails();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Check-in failed');
    } finally {
      setActionLoading(false);
    }
  };

  const handleSaveReport = async () => {
    if (!serviceReport.problem_found || !serviceReport.action_taken) {
      toast.error('Please fill in problem found and action taken');
      return;
    }
    
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/engineer/visits/${visitId}/service-report`,
        serviceReport,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Report saved!');
      setShowServiceForm(false);
      fetchVisitDetails();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Failed to save report');
    } finally {
      setActionLoading(false);
    }
  };

  const handlePhotoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await axios.post(
        `${API}/api/engineer/visits/${visitId}/upload-photo`,
        formData,
        { headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'multipart/form-data' } }
      );
      toast.success('Photo uploaded!');
      fetchVisitDetails();
    } catch (err) {
      toast.error('Failed to upload photo');
    }
  };

  const handleCheckOut = async () => {
    setActionLoading(true);
    try {
      await axios.post(
        `${API}/api/engineer/visits/${visitId}/check-out`,
        { customer_name: customerName },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      toast.success('Visit completed successfully!');
      navigate('/engineer/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Check-out failed');
    } finally {
      setActionLoading(false);
    }
  };

  const addPart = () => {
    if (newPart.name) {
      setServiceReport({
        ...serviceReport,
        parts_used: [...serviceReport.parts_used, { ...newPart }]
      });
      setNewPart({ name: '', quantity: 1 });
    }
  };

  const removePart = (index) => {
    setServiceReport({
      ...serviceReport,
      parts_used: serviceReport.parts_used.filter((_, i) => i !== index)
    });
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="w-8 h-8 border-4 border-orange-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const { visit, device, company, ticket, service_history } = data;
  const isAssigned = visit.status === 'assigned';
  const isInProgress = visit.status === 'in_progress';
  const isCompleted = visit.status === 'completed';

  return (
    <div className="min-h-screen bg-slate-50 pb-24">
      {/* Header */}
      <header className="bg-gradient-to-r from-slate-900 to-slate-800 text-white sticky top-0 z-50">
        <div className="px-4 py-4">
          <div className="flex items-center gap-3">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => navigate('/engineer/dashboard')}
              className="text-white hover:bg-slate-700 p-2"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>
            <div>
              <p className="font-semibold">{ticket?.ticket_number}</p>
              <p className="text-xs text-slate-400 capitalize">{visit.status.replace('_', ' ')}</p>
            </div>
          </div>
        </div>
      </header>

      <main className="p-4 space-y-4">
        {/* Status Card */}
        <Card className={`border-l-4 ${
          isAssigned ? 'border-l-blue-500' : 
          isInProgress ? 'border-l-amber-500' : 'border-l-emerald-500'
        }`}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {isAssigned && <Clock className="h-6 w-6 text-blue-500" />}
                {isInProgress && <Play className="h-6 w-6 text-amber-500" />}
                {isCompleted && <CheckCircle2 className="h-6 w-6 text-emerald-500" />}
                <div>
                  <p className="font-medium text-slate-900">
                    {isAssigned && 'Ready to Start'}
                    {isInProgress && 'In Progress'}
                    {isCompleted && 'Completed'}
                  </p>
                  <p className="text-sm text-slate-500">
                    {isAssigned && 'Check in when you arrive at site'}
                    {isInProgress && 'Complete your service report'}
                    {isCompleted && `Completed at ${formatDateTime(visit.check_out_time)}`}
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Device Info */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Laptop className="h-4 w-4" />
              Device Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-slate-500 text-sm">Device</span>
              <span className="font-medium">{device?.brand} {device?.model}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-slate-500 text-sm">Serial Number</span>
              <span className="font-mono text-sm">{device?.serial_number}</span>
            </div>
            {device?.asset_tag && (
              <div className="flex justify-between items-center">
                <span className="text-slate-500 text-sm">Asset Tag</span>
                <span className="font-mono text-sm">{device.asset_tag}</span>
              </div>
            )}
            {device?.location && (
              <div className="flex justify-between items-center">
                <span className="text-slate-500 text-sm">Location</span>
                <span className="text-sm">{device.location}</span>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Company Info */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <Building2 className="h-4 w-4" />
              Company Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="font-medium">{company?.name}</p>
            {company?.address && (
              <div className="flex items-start gap-2 text-sm text-slate-600">
                <MapPin className="h-4 w-4 mt-0.5 flex-shrink-0" />
                <span>{company.address}</span>
              </div>
            )}
            {company?.contact_phone && (
              <a 
                href={`tel:${company.contact_phone}`}
                className="flex items-center gap-2 text-sm text-blue-600"
              >
                <Phone className="h-4 w-4" />
                {company.contact_phone}
              </a>
            )}
          </CardContent>
        </Card>

        {/* Issue Details */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Issue Details
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <p className="font-medium">{ticket?.subject}</p>
            <p className="text-sm text-slate-600">{ticket?.description}</p>
            <div className="flex gap-2">
              <Badge variant="outline">{ticket?.issue_category}</Badge>
              <Badge variant={ticket?.priority === 'high' ? 'destructive' : 'secondary'}>
                {ticket?.priority}
              </Badge>
            </div>
          </CardContent>
        </Card>

        {/* Visit Times */}
        {visit.check_in_time && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Calendar className="h-4 w-4" />
                Visit Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-500">Check-in</span>
                <span>{formatDateTime(visit.check_in_time)}</span>
              </div>
              {visit.check_out_time && (
                <div className="flex justify-between">
                  <span className="text-slate-500">Check-out</span>
                  <span>{formatDateTime(visit.check_out_time)}</span>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Service Report (if completed) */}
        {(isInProgress || isCompleted) && visit.problem_found && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <FileText className="h-4 w-4" />
                Service Report
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3 text-sm">
              <div>
                <p className="text-slate-500 mb-1">Problem Found</p>
                <p className="text-slate-900">{visit.problem_found}</p>
              </div>
              <div>
                <p className="text-slate-500 mb-1">Action Taken</p>
                <p className="text-slate-900">{visit.action_taken}</p>
              </div>
              {visit.parts_used?.length > 0 && (
                <div>
                  <p className="text-slate-500 mb-1">Parts Used</p>
                  <div className="space-y-1">
                    {visit.parts_used.map((part, i) => (
                      <Badge key={i} variant="outline" className="mr-1">
                        {part.name} x{part.quantity}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Photos */}
        {visit.photos?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Camera className="h-4 w-4" />
                Photos ({visit.photos.length})
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-3 gap-2">
                {visit.photos.map((photo, i) => (
                  <img
                    key={i}
                    src={`${API}/uploads/${photo}`}
                    alt={`Visit photo ${i + 1}`}
                    className="w-full h-20 object-cover rounded-lg"
                  />
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Service History */}
        {service_history?.length > 0 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm flex items-center gap-2">
                <Wrench className="h-4 w-4" />
                Previous Service History
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {service_history.map((record, i) => (
                  <div key={i} className="text-sm border-l-2 border-slate-200 pl-3">
                    <div className="flex justify-between">
                      <span className="font-medium">{record.service_type}</span>
                      <span className="text-slate-500">{record.service_date}</span>
                    </div>
                    <p className="text-slate-600 text-xs mt-1">{record.action_taken}</p>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}
      </main>

      {/* Action Buttons */}
      {!isCompleted && (
        <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-4 space-y-2">
          {isAssigned && (
            <Button 
              className="w-full bg-blue-500 hover:bg-blue-600 h-12"
              onClick={handleCheckIn}
              disabled={actionLoading}
            >
              <Play className="h-5 w-5 mr-2" />
              {actionLoading ? 'Checking in...' : 'Check In'}
            </Button>
          )}
          
          {isInProgress && (
            <>
              <div className="grid grid-cols-2 gap-2">
                <Button 
                  variant="outline" 
                  className="h-12"
                  onClick={() => setShowServiceForm(true)}
                >
                  <FileText className="h-4 w-4 mr-2" />
                  {visit.problem_found ? 'Edit Report' : 'Add Report'}
                </Button>
                <label className="cursor-pointer">
                  <Button variant="outline" className="w-full h-12" asChild>
                    <span>
                      <Camera className="h-4 w-4 mr-2" />
                      Add Photo
                    </span>
                  </Button>
                  <input 
                    type="file" 
                    accept="image/*" 
                    capture="environment"
                    className="hidden" 
                    onChange={handlePhotoUpload}
                  />
                </label>
              </div>
              <Button 
                className="w-full bg-emerald-500 hover:bg-emerald-600 h-12"
                onClick={() => setShowCheckoutDialog(true)}
                disabled={!visit.problem_found || !visit.action_taken}
              >
                <CheckCircle2 className="h-5 w-5 mr-2" />
                Complete & Check Out
              </Button>
            </>
          )}
        </div>
      )}

      {/* Service Report Dialog */}
      <Dialog open={showServiceForm} onOpenChange={setShowServiceForm}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Service Report</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Problem Found *</Label>
              <Textarea
                placeholder="Describe the problem you found..."
                value={serviceReport.problem_found}
                onChange={(e) => setServiceReport({...serviceReport, problem_found: e.target.value})}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label>Action Taken *</Label>
              <Textarea
                placeholder="Describe what you did to fix it..."
                value={serviceReport.action_taken}
                onChange={(e) => setServiceReport({...serviceReport, action_taken: e.target.value})}
                rows={3}
              />
            </div>
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Package className="h-4 w-4" />
                Parts Used
              </Label>
              <div className="flex gap-2">
                <Input
                  placeholder="Part name"
                  value={newPart.name}
                  onChange={(e) => setNewPart({...newPart, name: e.target.value})}
                  className="flex-1"
                />
                <Input
                  type="number"
                  placeholder="Qty"
                  value={newPart.quantity}
                  onChange={(e) => setNewPart({...newPart, quantity: parseInt(e.target.value) || 1})}
                  className="w-20"
                />
                <Button type="button" variant="outline" onClick={addPart}>Add</Button>
              </div>
              {serviceReport.parts_used.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-2">
                  {serviceReport.parts_used.map((part, i) => (
                    <Badge key={i} variant="secondary" className="cursor-pointer" onClick={() => removePart(i)}>
                      {part.name} x{part.quantity} ✕
                    </Badge>
                  ))}
                </div>
              )}
            </div>
            <div className="space-y-2">
              <Label>Additional Notes</Label>
              <Textarea
                placeholder="Any additional notes..."
                value={serviceReport.notes}
                onChange={(e) => setServiceReport({...serviceReport, notes: e.target.value})}
                rows={2}
              />
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowServiceForm(false)}>Cancel</Button>
              <Button onClick={handleSaveReport} disabled={actionLoading}>
                {actionLoading ? 'Saving...' : 'Save Report'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>

      {/* Checkout Dialog */}
      <Dialog open={showCheckoutDialog} onOpenChange={setShowCheckoutDialog}>
        <DialogContent className="max-w-sm">
          <DialogHeader>
            <DialogTitle>Complete Visit</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <div className="space-y-2">
              <Label>Customer Name (Optional)</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                <Input
                  placeholder="Name of person who received service"
                  value={customerName}
                  onChange={(e) => setCustomerName(e.target.value)}
                  className="pl-10"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 pt-4">
              <Button variant="outline" onClick={() => setShowCheckoutDialog(false)}>Cancel</Button>
              <Button 
                onClick={handleCheckOut} 
                disabled={actionLoading}
                className="bg-emerald-500 hover:bg-emerald-600"
              >
                {actionLoading ? 'Completing...' : 'Complete Visit'}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default EngineerVisitDetail;
