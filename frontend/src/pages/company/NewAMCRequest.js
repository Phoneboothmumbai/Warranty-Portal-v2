import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { 
  ArrowLeft, Package, Calendar, FileText, CheckCircle2,
  Laptop, Monitor, Printer, Server, Tablet, Shield
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Checkbox } from '../../components/ui/checkbox';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const deviceIcons = {
  LAPTOP: Laptop,
  DESKTOP: Monitor,
  TABLET: Tablet,
  PRINTER: Printer,
  SERVER: Server,
};

const amcTypes = [
  { value: 'comprehensive', label: 'Comprehensive', description: 'Full coverage including parts & labor' },
  { value: 'non_comprehensive', label: 'Non-Comprehensive', description: 'Labor only, parts charged separately' },
  { value: 'on_call', label: 'On-Call Basis', description: 'Pay per service visit' }
];

const durationOptions = [
  { value: 12, label: '1 Year', discount: 0 },
  { value: 24, label: '2 Years', discount: 10 },
  { value: 36, label: '3 Years', discount: 15 }
];

const NewAMCRequest = () => {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [step, setStep] = useState(1);
  
  // Data
  const [packages, setPackages] = useState([]);
  const [devices, setDevices] = useState([]);
  const [deviceTypes, setDeviceTypes] = useState([]);
  
  // Form state
  const [formData, setFormData] = useState({
    package_id: '',
    amc_type: 'comprehensive',
    duration_months: 12,
    selection_type: 'specific',
    selected_device_ids: [],
    selected_categories: [],
    preferred_start_date: new Date().toISOString().split('T')[0],
    special_requirements: '',
    budget_range: ''
  });

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [packagesRes, devicesRes] = await Promise.all([
        axios.get(`${API}/company/amc-packages`, { headers: { Authorization: `Bearer ${token}` } }),
        axios.get(`${API}/company/devices`, { headers: { Authorization: `Bearer ${token}` } })
      ]);
      
      setPackages(packagesRes.data);
      setDevices(devicesRes.data);
      
      // Extract unique device types
      const types = [...new Set(devicesRes.data.map(d => d.device_type).filter(Boolean))];
      setDeviceTypes(types);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleDeviceToggle = (deviceId) => {
    setFormData(prev => ({
      ...prev,
      selected_device_ids: prev.selected_device_ids.includes(deviceId)
        ? prev.selected_device_ids.filter(id => id !== deviceId)
        : [...prev.selected_device_ids, deviceId]
    }));
  };

  const handleCategoryToggle = (category) => {
    setFormData(prev => ({
      ...prev,
      selected_categories: prev.selected_categories.includes(category)
        ? prev.selected_categories.filter(c => c !== category)
        : [...prev.selected_categories, category]
    }));
  };

  const selectAllDevices = () => {
    setFormData(prev => ({
      ...prev,
      selected_device_ids: devices.map(d => d.id)
    }));
  };

  const deselectAllDevices = () => {
    setFormData(prev => ({
      ...prev,
      selected_device_ids: []
    }));
  };

  const getSelectedDeviceCount = () => {
    if (formData.selection_type === 'specific') {
      return formData.selected_device_ids.length;
    } else if (formData.selection_type === 'all') {
      return devices.length;
    } else if (formData.selection_type === 'by_category') {
      return devices.filter(d => formData.selected_categories.includes(d.device_type)).length;
    }
    return 0;
  };

  const calculateEstimatedPrice = () => {
    const selectedPackage = packages.find(p => p.id === formData.package_id);
    if (!selectedPackage) return null;
    
    const deviceCount = getSelectedDeviceCount();
    const pricePerDevice = selectedPackage.price_per_device || 0;
    const years = formData.duration_months / 12;
    const durationOption = durationOptions.find(d => d.value === formData.duration_months);
    const discount = durationOption?.discount || 0;
    
    const basePrice = pricePerDevice * deviceCount * years;
    const discountAmount = (basePrice * discount) / 100;
    
    return {
      basePrice,
      discount,
      discountAmount,
      finalPrice: basePrice - discountAmount,
      pricePerDevice,
      deviceCount
    };
  };

  const handleSubmit = async () => {
    if (formData.selection_type === 'specific' && formData.selected_device_ids.length === 0) {
      toast.error('Please select at least one device');
      return;
    }
    if (formData.selection_type === 'by_category' && formData.selected_categories.length === 0) {
      toast.error('Please select at least one device category');
      return;
    }

    try {
      setSubmitting(true);
      await axios.post(`${API}/company/amc-requests`, formData, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('AMC Request submitted successfully!');
      navigate('/company/amc-requests');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit request');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  const pricing = calculateEstimatedPrice();

  return (
    <div className="space-y-6 max-w-4xl mx-auto" data-testid="new-amc-request">
      {/* Header */}
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Request AMC</h1>
          <p className="text-slate-500">Submit a new Annual Maintenance Contract request</p>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-2">
        {[1, 2, 3].map((s) => (
          <div key={s} className="flex items-center">
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
              step >= s ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-500'
            }`}>
              {s}
            </div>
            {s < 3 && <div className={`w-16 h-1 mx-2 ${step > s ? 'bg-blue-600' : 'bg-slate-200'}`} />}
          </div>
        ))}
      </div>
      <div className="flex justify-center gap-8 text-sm text-slate-500">
        <span className={step >= 1 ? 'text-blue-600 font-medium' : ''}>AMC Type</span>
        <span className={step >= 2 ? 'text-blue-600 font-medium' : ''}>Select Devices</span>
        <span className={step >= 3 ? 'text-blue-600 font-medium' : ''}>Review & Submit</span>
      </div>

      {/* Step 1: AMC Type & Package */}
      {step === 1 && (
        <div className="bg-white rounded-xl border border-slate-100 p-6 space-y-6">
          <h2 className="text-lg font-semibold text-slate-900">Select AMC Type & Duration</h2>
          
          {/* AMC Type */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700">AMC Type</label>
            <div className="grid gap-3">
              {amcTypes.map((type) => (
                <label
                  key={type.value}
                  className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                    formData.amc_type === type.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="amc_type"
                    value={type.value}
                    checked={formData.amc_type === type.value}
                    onChange={(e) => setFormData({ ...formData, amc_type: e.target.value })}
                    className="mt-1"
                  />
                  <div>
                    <p className="font-medium text-slate-900">{type.label}</p>
                    <p className="text-sm text-slate-500">{type.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Duration */}
          <div className="space-y-3">
            <label className="text-sm font-medium text-slate-700">Contract Duration</label>
            <div className="grid grid-cols-3 gap-3">
              {durationOptions.map((option) => (
                <label
                  key={option.value}
                  className={`p-4 rounded-lg border-2 cursor-pointer text-center transition-colors ${
                    formData.duration_months === option.value
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-slate-200 hover:border-slate-300'
                  }`}
                >
                  <input
                    type="radio"
                    name="duration"
                    value={option.value}
                    checked={formData.duration_months === option.value}
                    onChange={() => setFormData({ ...formData, duration_months: option.value })}
                    className="sr-only"
                  />
                  <p className="font-medium text-slate-900">{option.label}</p>
                  {option.discount > 0 && (
                    <p className="text-sm text-emerald-600">Save {option.discount}%</p>
                  )}
                </label>
              ))}
            </div>
          </div>

          {/* Package Selection (if available) */}
          {packages.length > 0 && (
            <div className="space-y-3">
              <label className="text-sm font-medium text-slate-700">Select Package (Optional)</label>
              <div className="grid gap-3">
                {packages.map((pkg) => (
                  <label
                    key={pkg.id}
                    className={`flex items-start gap-3 p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                      formData.package_id === pkg.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <input
                      type="radio"
                      name="package"
                      value={pkg.id}
                      checked={formData.package_id === pkg.id}
                      onChange={() => setFormData({ ...formData, package_id: pkg.id })}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <p className="font-medium text-slate-900">{pkg.name}</p>
                        <p className="font-semibold text-blue-600">
                          ₹{pkg.price_per_device?.toLocaleString('en-IN')}/device/year
                        </p>
                      </div>
                      {pkg.description && (
                        <p className="text-sm text-slate-500 mt-1">{pkg.description}</p>
                      )}
                    </div>
                  </label>
                ))}
              </div>
            </div>
          )}

          {/* Start Date */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-700">Preferred Start Date</label>
            <Input
              type="date"
              value={formData.preferred_start_date}
              onChange={(e) => setFormData({ ...formData, preferred_start_date: e.target.value })}
              min={new Date().toISOString().split('T')[0]}
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={() => setStep(2)}>
              Next: Select Devices
            </Button>
          </div>
        </div>
      )}

      {/* Step 2: Device Selection */}
      {step === 2 && (
        <div className="bg-white rounded-xl border border-slate-100 p-6 space-y-6">
          <h2 className="text-lg font-semibold text-slate-900">Select Devices</h2>
          
          {/* Selection Type */}
          <div className="flex gap-3">
            {[
              { value: 'specific', label: 'Select Specific Devices' },
              { value: 'all', label: 'All Devices' },
              { value: 'by_category', label: 'By Category' }
            ].map((option) => (
              <Button
                key={option.value}
                variant={formData.selection_type === option.value ? 'default' : 'outline'}
                onClick={() => setFormData({ ...formData, selection_type: option.value })}
              >
                {option.label}
              </Button>
            ))}
          </div>

          {/* Specific Device Selection */}
          {formData.selection_type === 'specific' && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <p className="text-sm text-slate-500">
                  {formData.selected_device_ids.length} of {devices.length} devices selected
                </p>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" onClick={selectAllDevices}>Select All</Button>
                  <Button variant="outline" size="sm" onClick={deselectAllDevices}>Deselect All</Button>
                </div>
              </div>
              <div className="max-h-96 overflow-y-auto border rounded-lg divide-y">
                {devices.map((device) => {
                  const DeviceIcon = deviceIcons[device.device_type] || Laptop;
                  const isSelected = formData.selected_device_ids.includes(device.id);
                  
                  return (
                    <label
                      key={device.id}
                      className={`flex items-center gap-3 p-3 cursor-pointer hover:bg-slate-50 ${
                        isSelected ? 'bg-blue-50' : ''
                      }`}
                    >
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => handleDeviceToggle(device.id)}
                      />
                      <DeviceIcon className="h-5 w-5 text-slate-400" />
                      <div className="flex-1">
                        <p className="font-medium text-slate-900">{device.brand} {device.model}</p>
                        <p className="text-sm text-slate-500">{device.serial_number}</p>
                      </div>
                      <span className="text-xs px-2 py-1 bg-slate-100 rounded-full text-slate-600">
                        {device.device_type}
                      </span>
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          {/* All Devices */}
          {formData.selection_type === 'all' && (
            <div className="p-6 bg-blue-50 rounded-lg text-center">
              <Package className="h-10 w-10 text-blue-600 mx-auto mb-2" />
              <p className="font-medium text-slate-900">All {devices.length} devices will be covered</p>
              <p className="text-sm text-slate-500">Your entire device inventory will be included in this AMC</p>
            </div>
          )}

          {/* By Category */}
          {formData.selection_type === 'by_category' && (
            <div className="space-y-3">
              <p className="text-sm text-slate-500">Select device categories to include:</p>
              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                {deviceTypes.map((type) => {
                  const count = devices.filter(d => d.device_type === type).length;
                  const isSelected = formData.selected_categories.includes(type);
                  const DeviceIcon = deviceIcons[type] || Package;
                  
                  return (
                    <label
                      key={type}
                      className={`flex items-center gap-3 p-4 rounded-lg border-2 cursor-pointer transition-colors ${
                        isSelected ? 'border-blue-500 bg-blue-50' : 'border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <Checkbox
                        checked={isSelected}
                        onCheckedChange={() => handleCategoryToggle(type)}
                      />
                      <DeviceIcon className="h-5 w-5 text-slate-500" />
                      <div>
                        <p className="font-medium text-slate-900">{type}</p>
                        <p className="text-sm text-slate-500">{count} devices</p>
                      </div>
                    </label>
                  );
                })}
              </div>
            </div>
          )}

          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
            <Button onClick={() => setStep(3)} disabled={getSelectedDeviceCount() === 0}>
              Next: Review
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: Review & Submit */}
      {step === 3 && (
        <div className="space-y-6">
          {/* Summary Card */}
          <div className="bg-white rounded-xl border border-slate-100 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-slate-900">Review Your Request</h2>
            
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <p className="text-slate-500">AMC Type</p>
                <p className="font-medium text-slate-900">
                  {amcTypes.find(t => t.value === formData.amc_type)?.label}
                </p>
              </div>
              <div>
                <p className="text-slate-500">Duration</p>
                <p className="font-medium text-slate-900">
                  {durationOptions.find(d => d.value === formData.duration_months)?.label}
                </p>
              </div>
              <div>
                <p className="text-slate-500">Devices Covered</p>
                <p className="font-medium text-slate-900">{getSelectedDeviceCount()} devices</p>
              </div>
              <div>
                <p className="text-slate-500">Start Date</p>
                <p className="font-medium text-slate-900">
                  {new Date(formData.preferred_start_date).toLocaleDateString('en-IN', {
                    day: 'numeric', month: 'long', year: 'numeric'
                  })}
                </p>
              </div>
            </div>

            {/* Pricing Estimate */}
            {pricing && (
              <div className="bg-slate-50 rounded-lg p-4 mt-4">
                <h3 className="font-medium text-slate-900 mb-3">Estimated Pricing</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-slate-500">
                      {pricing.deviceCount} devices × ₹{pricing.pricePerDevice.toLocaleString('en-IN')}/device
                    </span>
                    <span className="text-slate-900">₹{pricing.basePrice.toLocaleString('en-IN')}</span>
                  </div>
                  {pricing.discount > 0 && (
                    <div className="flex justify-between text-emerald-600">
                      <span>Multi-year discount ({pricing.discount}%)</span>
                      <span>-₹{pricing.discountAmount.toLocaleString('en-IN')}</span>
                    </div>
                  )}
                  <div className="flex justify-between pt-2 border-t border-slate-200 font-semibold">
                    <span className="text-slate-900">Estimated Total</span>
                    <span className="text-blue-600">₹{pricing.finalPrice.toLocaleString('en-IN')}</span>
                  </div>
                </div>
                <p className="text-xs text-slate-400 mt-2">
                  * Final pricing will be confirmed by our team
                </p>
              </div>
            )}
          </div>

          {/* Additional Details */}
          <div className="bg-white rounded-xl border border-slate-100 p-6 space-y-4">
            <h3 className="font-medium text-slate-900">Additional Information (Optional)</h3>
            
            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Special Requirements</label>
              <Textarea
                placeholder="Any specific requirements or notes for this AMC..."
                value={formData.special_requirements}
                onChange={(e) => setFormData({ ...formData, special_requirements: e.target.value })}
                rows={3}
              />
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium text-slate-700">Budget Range</label>
              <Input
                placeholder="e.g., ₹50,000 - ₹75,000"
                value={formData.budget_range}
                onChange={(e) => setFormData({ ...formData, budget_range: e.target.value })}
              />
            </div>
          </div>

          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(2)}>Back</Button>
            <Button onClick={handleSubmit} disabled={submitting}>
              {submitting ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                  Submitting...
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4 mr-2" />
                  Submit Request
                </>
              )}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NewAMCRequest;
