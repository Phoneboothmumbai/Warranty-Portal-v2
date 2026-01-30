import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Building2, Users, Monitor, Server, Wifi, Key, ArrowRight, ArrowLeft,
  CheckCircle2, Clock, AlertTriangle, Download, Upload, Plus, Trash2,
  FileSpreadsheet, Save, Send, MessageSquare, Shield
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';
import * as XLSX from 'xlsx';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Step definitions
const STEPS = [
  { id: 1, title: 'Company & Contract', icon: Building2, description: 'Basic company details' },
  { id: 2, title: 'Office Environment', icon: Users, description: 'Office setup info' },
  { id: 3, title: 'Device Categories', icon: Monitor, description: 'What devices you have' },
  { id: 4, title: 'Device Inventory', icon: FileSpreadsheet, description: 'Detailed device list' },
  { id: 5, title: 'Network & Servers', icon: Server, description: 'Infrastructure details' },
  { id: 6, title: 'Software & Access', icon: Key, description: 'Software and credentials' },
  { id: 7, title: 'Vendor Handover', icon: Wifi, description: 'Previous IT vendor info' },
  { id: 8, title: 'Scope Confirmation', icon: Shield, description: 'Terms and guardrails' },
];

const DEVICE_TYPES = [
  'Desktop', 'Laptop', 'Apple Mac', 'Apple iPhone', 'Apple iPad',
  'Server', 'Router', 'Switch', 'Firewall', 'Printer', 'Scanner',
  'CCTV', 'Access Point', 'UPS', 'Other'
];

const WORKING_DAYS = [
  { value: 'monday', label: 'Monday' },
  { value: 'tuesday', label: 'Tuesday' },
  { value: 'wednesday', label: 'Wednesday' },
  { value: 'thursday', label: 'Thursday' },
  { value: 'friday', label: 'Friday' },
  { value: 'saturday', label: 'Saturday' },
  { value: 'sunday', label: 'Sunday' },
];

const CompanyAMCOnboarding = () => {
  const { token } = useCompanyAuth();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [currentStep, setCurrentStep] = useState(1);
  const [onboarding, setOnboarding] = useState(null);
  const [showSubmitConfirm, setShowSubmitConfirm] = useState(false);
  
  // Form state for all steps
  const [formData, setFormData] = useState({
    step1: {
      company_name_legal: '',
      brand_trade_name: '',
      registered_address: '',
      office_addresses: [],
      gst_number: '',
      billing_address: '',
      po_amc_reference: '',
      amc_start_date: '',
      amc_end_date: '',
      contracted_user_count: '',
      contracted_device_count: '',
      amc_type: 'per_device',
      primary_spoc: { name: '', email: '', mobile: '' },
      escalation_contact: { name: '', email: '', mobile: '' },
      billing_contact: { name: '', email: '', mobile: '' },
    },
    step2: {
      office_type: '',
      working_days: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
      working_hours_start: '09:00',
      working_hours_end: '18:00',
      total_employees: '',
      it_usage_nature: 'business_apps',
    },
    step3: {
      has_desktops: false,
      has_laptops: false,
      has_apple_devices: false,
      has_servers: false,
      has_network_devices: false,
      has_printers: false,
      has_cctv: false,
      has_wifi_aps: false,
      has_ups: false,
      other_devices: '',
    },
    step4: {
      devices: [],
    },
    step5: {
      internet_providers: [],
      bandwidth: '',
      has_static_ip: false,
      static_ip_addresses: '',
      router_firewall_brand: '',
      router_firewall_model: '',
      switch_count: '',
      vlans: '',
      wifi_controller: '',
      has_servers: false,
      servers: [],
      backup_responsibility_acknowledged: false,
    },
    step6: {
      email_platform: '',
      admin_access_available: false,
      domain_names: [],
      licenses: [],
      has_vpn: false,
      vpn_type: '',
      has_password_manager: false,
      password_manager_name: '',
      additional_software: '',
    },
    step7: {
      previous_vendor_name: '',
      previous_vendor_contact: '',
      has_network_diagram: null,
      has_ip_details: null,
      has_server_credentials: null,
      has_firewall_access: null,
      has_isp_details: null,
      has_asset_list: null,
      has_open_issues_list: null,
      missing_info_acknowledged: false,
      handover_notes: '',
    },
    step8: {
      devices_limited_to_listed: false,
      new_devices_chargeable: false,
      installations_chargeable: false,
      unsupported_devices_excluded: false,
      onsite_waiting_billable: false,
      reopened_tickets_new: false,
      information_accuracy_confirmed: false,
      additional_terms: '',
    },
  });

  const fetchOnboarding = useCallback(async () => {
    try {
      const response = await axios.get(`${API}/portal/onboarding`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setOnboarding(response.data);
      
      // Populate form data from saved onboarding
      const ob = response.data;
      setFormData(prev => ({
        step1: ob.step1_company_contract || prev.step1,
        step2: ob.step2_office_environment || prev.step2,
        step3: ob.step3_device_categories || prev.step3,
        step4: ob.step4_device_inventory || prev.step4,
        step5: ob.step5_network_infra || prev.step5,
        step6: ob.step6_software_access || prev.step6,
        step7: ob.step7_vendor_handover || prev.step7,
        step8: ob.step8_scope_confirmation || prev.step8,
      }));
      setCurrentStep(ob.current_step || 1);
    } catch (error) {
      toast.error('Failed to load onboarding data');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchOnboarding();
  }, [fetchOnboarding]);

  const saveDraft = async (showToast = true) => {
    setSaving(true);
    try {
      await axios.put(`${API}/portal/onboarding`, {
        current_step: currentStep,
        step1_company_contract: formData.step1,
        step2_office_environment: formData.step2,
        step3_device_categories: formData.step3,
        step4_device_inventory: formData.step4,
        step5_network_infra: formData.step5,
        step6_software_access: formData.step6,
        step7_vendor_handover: formData.step7,
        step8_scope_confirmation: formData.step8,
      }, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (showToast) toast.success('Draft saved');
    } catch (error) {
      toast.error('Failed to save draft');
    } finally {
      setSaving(false);
    }
  };

  const handleNext = async () => {
    await saveDraft(false);
    if (currentStep < 8) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    if (!formData.step8.information_accuracy_confirmed) {
      toast.error('Please confirm information accuracy before submitting');
      return;
    }
    
    try {
      await saveDraft(false);
      await axios.post(`${API}/portal/onboarding/submit`, {}, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success('Onboarding submitted successfully!');
      setShowSubmitConfirm(false);
      fetchOnboarding();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit');
    }
  };

  const updateStep = (step, field, value) => {
    setFormData(prev => ({
      ...prev,
      [`step${step}`]: {
        ...prev[`step${step}`],
        [field]: value
      }
    }));
  };

  const updateNestedField = (step, parent, field, value) => {
    setFormData(prev => ({
      ...prev,
      [`step${step}`]: {
        ...prev[`step${step}`],
        [parent]: {
          ...prev[`step${step}`][parent],
          [field]: value
        }
      }
    }));
  };

  // Device inventory handlers
  const addDevice = () => {
    const newDevice = {
      id: `dev_${Date.now()}`,
      device_type: '',
      brand: '',
      model: '',
      serial_number: '',
      configuration: '',
      os_version: '',
      purchase_date: '',
      warranty_status: '',
      condition: 'working',
      assigned_user: '',
      department: '',
      physical_location: '',
    };
    updateStep(4, 'devices', [...formData.step4.devices, newDevice]);
  };

  const updateDevice = (deviceId, field, value) => {
    const updatedDevices = formData.step4.devices.map(d => 
      d.id === deviceId ? { ...d, [field]: value } : d
    );
    updateStep(4, 'devices', updatedDevices);
  };

  const removeDevice = (deviceId) => {
    updateStep(4, 'devices', formData.step4.devices.filter(d => d.id !== deviceId));
  };

  const handleExcelUpload = async (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const data = await file.arrayBuffer();
      const workbook = XLSX.read(data);
      
      // Parse ALL sheets (except Instructions) and combine devices
      const allDevices = [];
      for (const sheetName of workbook.SheetNames) {
        // Skip the Instructions sheet
        if (sheetName.toLowerCase() === 'instructions') continue;
        
        const worksheet = workbook.Sheets[sheetName];
        const jsonData = XLSX.utils.sheet_to_json(worksheet);
        
        // Filter out empty rows and sample data rows
        const validDevices = jsonData.filter(row => {
          const serial = row['Serial Number*'] || row['serial_number'];
          // Skip if no serial or if it's the sample serial
          return serial && !['ABC123XYZ', 'DEF456UVW', 'GHI789RST', 'JKL012MNO', 
                           'C02XL12345', 'FCZ2312A1BC', 'HIK20241234', 
                           '24:5A:4C:AB:12:34', 'AS1234567890'].includes(serial);
        });
        
        allDevices.push(...validDevices);
      }
      
      if (allDevices.length === 0) {
        toast.warning('No devices found. Make sure to replace sample data with real device information.');
        e.target.value = '';
        return;
      }
      
      // Process and normalize devices
      const response = await axios.post(`${API}/portal/onboarding/upload-devices`, 
        { devices: allDevices },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      updateStep(4, 'devices', [...formData.step4.devices, ...response.data.devices]);
      toast.success(`${response.data.count} devices imported from ${workbook.SheetNames.filter(s => s.toLowerCase() !== 'instructions').length} sheet(s)`);
    } catch (error) {
      toast.error('Failed to import devices');
    }
    
    e.target.value = '';
  };

  const downloadTemplate = () => {
    // Build query params based on selected device categories in Step 3
    const categoryMapping = {
      has_desktops: 'desktops',
      has_laptops: 'laptops',
      has_apple_devices: 'apple_devices',
      has_servers: 'servers',
      has_network_devices: 'network_devices',
      has_printers: 'printers',
      has_cctv: 'cctv',
      has_wifi_aps: 'wifi_aps',
      has_ups: 'ups',
    };
    
    const selectedCategories = Object.entries(categoryMapping)
      .filter(([key]) => formData.step3[key])
      .map(([, value]) => value);
    
    let url = `${API}/portal/onboarding/device-template`;
    if (selectedCategories.length > 0) {
      url += `?categories=${selectedCategories.join(',')}`;
    }
    
    window.open(url, '_blank');
  };

  // Server handlers
  const addServer = () => {
    const newServer = {
      id: `srv_${Date.now()}`,
      type: 'physical',
      os: '',
      roles: '',
      backup_status: '',
      last_backup: '',
    };
    updateStep(5, 'servers', [...formData.step5.servers, newServer]);
  };

  const updateServer = (serverId, field, value) => {
    const updatedServers = formData.step5.servers.map(s => 
      s.id === serverId ? { ...s, [field]: value } : s
    );
    updateStep(5, 'servers', updatedServers);
  };

  const removeServer = (serverId) => {
    updateStep(5, 'servers', formData.step5.servers.filter(s => s.id !== serverId));
  };

  // Check if form is editable
  const isEditable = !onboarding || ['draft', 'changes_requested'].includes(onboarding.status);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  // Show status banner for submitted/approved
  const renderStatusBanner = () => {
    if (!onboarding) return null;
    
    const statusConfig = {
      submitted: { bg: 'bg-blue-50', border: 'border-blue-200', text: 'text-blue-800', icon: Clock, message: 'Your onboarding has been submitted and is pending review.' },
      changes_requested: { bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-800', icon: AlertTriangle, message: 'Changes have been requested. Please review the feedback below.' },
      approved: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800', icon: CheckCircle2, message: 'Your onboarding has been approved!' },
      converted: { bg: 'bg-emerald-50', border: 'border-emerald-200', text: 'text-emerald-800', icon: CheckCircle2, message: 'Onboarding complete! Your AMC is now active.' },
    };
    
    const config = statusConfig[onboarding.status];
    if (!config) return null;
    
    const Icon = config.icon;
    
    return (
      <div className={`${config.bg} ${config.border} border rounded-xl p-4 mb-6`}>
        <div className="flex items-start gap-3">
          <Icon className={`h-5 w-5 ${config.text} mt-0.5`} />
          <div>
            <p className={`font-medium ${config.text}`}>{config.message}</p>
            {onboarding.status === 'changes_requested' && onboarding.admin_feedback && (
              <div className="mt-2 p-3 bg-white rounded-lg border border-amber-200">
                <p className="text-sm font-medium text-slate-700 mb-1">Admin Feedback:</p>
                <p className="text-sm text-slate-600">{onboarding.admin_feedback}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6" data-testid="amc-onboarding-page">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">AMC Onboarding</h1>
          <p className="text-slate-500 mt-1">Complete this form to set up your AMC</p>
        </div>
        {isEditable && (
          <Button 
            variant="outline" 
            onClick={() => saveDraft(true)}
            disabled={saving}
          >
            <Save className="h-4 w-4 mr-2" />
            {saving ? 'Saving...' : 'Save Draft'}
          </Button>
        )}
      </div>

      {renderStatusBanner()}

      {/* Progress Steps */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 overflow-x-auto">
        <div className="flex items-center min-w-max">
          {STEPS.map((step, index) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep > step.id;
            
            return (
              <div key={step.id} className="flex items-center">
                <button
                  onClick={() => isEditable && setCurrentStep(step.id)}
                  disabled={!isEditable}
                  className={`flex flex-col items-center px-4 py-2 rounded-lg transition-all ${
                    isActive ? 'bg-emerald-50' : isCompleted ? 'bg-green-50' : ''
                  } ${isEditable ? 'cursor-pointer hover:bg-slate-50' : 'cursor-default'}`}
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center mb-1 ${
                    isActive ? 'bg-emerald-600 text-white' :
                    isCompleted ? 'bg-green-500 text-white' :
                    'bg-slate-200 text-slate-500'
                  }`}>
                    {isCompleted ? <CheckCircle2 className="h-5 w-5" /> : <Icon className="h-5 w-5" />}
                  </div>
                  <span className={`text-xs font-medium ${isActive ? 'text-emerald-700' : 'text-slate-600'}`}>
                    {step.title}
                  </span>
                </button>
                {index < STEPS.length - 1 && (
                  <div className={`w-8 h-0.5 ${isCompleted ? 'bg-green-500' : 'bg-slate-200'}`} />
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Step Content */}
      <div className="bg-white rounded-xl border border-slate-200 p-6">
        {/* Step 1: Company & Contract */}
        {currentStep === 1 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-900">Company & Contract Details</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Company Name (Legal) *</label>
                <input
                  type="text"
                  value={formData.step1.company_name_legal}
                  onChange={(e) => updateStep(1, 'company_name_legal', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">Brand / Trade Name</label>
                <input
                  type="text"
                  value={formData.step1.brand_trade_name}
                  onChange={(e) => updateStep(1, 'brand_trade_name', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
            </div>

            <div>
              <label className="form-label">Registered Address</label>
              <textarea
                value={formData.step1.registered_address}
                onChange={(e) => updateStep(1, 'registered_address', e.target.value)}
                className="form-input"
                rows={2}
                disabled={!isEditable}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">GST Number</label>
                <input
                  type="text"
                  value={formData.step1.gst_number}
                  onChange={(e) => updateStep(1, 'gst_number', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">PO / AMC Reference Number</label>
                <input
                  type="text"
                  value={formData.step1.po_amc_reference}
                  onChange={(e) => updateStep(1, 'po_amc_reference', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
            </div>

            <div>
              <label className="form-label">Billing Address</label>
              <textarea
                value={formData.step1.billing_address}
                onChange={(e) => updateStep(1, 'billing_address', e.target.value)}
                className="form-input"
                rows={2}
                disabled={!isEditable}
              />
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">AMC Start Date</label>
                <input
                  type="date"
                  value={formData.step1.amc_start_date}
                  onChange={(e) => updateStep(1, 'amc_start_date', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">AMC End Date</label>
                <input
                  type="date"
                  value={formData.step1.amc_end_date}
                  onChange={(e) => updateStep(1, 'amc_end_date', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">AMC Type</label>
                <select
                  value={formData.step1.amc_type}
                  onChange={(e) => updateStep(1, 'amc_type', e.target.value)}
                  className="form-select"
                  disabled={!isEditable}
                >
                  <option value="per_user">Per User</option>
                  <option value="per_device">Per Device</option>
                  <option value="hybrid">Hybrid</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Contracted User Count</label>
                <input
                  type="number"
                  value={formData.step1.contracted_user_count}
                  onChange={(e) => updateStep(1, 'contracted_user_count', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">Contracted Device Count</label>
                <input
                  type="number"
                  value={formData.step1.contracted_device_count}
                  onChange={(e) => updateStep(1, 'contracted_device_count', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
            </div>

            {/* Contacts */}
            <div className="border-t pt-4 mt-4">
              <h3 className="font-medium text-slate-900 mb-4">Contact Information</h3>
              
              <div className="space-y-4">
                <div>
                  <label className="form-label">Primary SPOC (Admin) *</label>
                  <div className="grid grid-cols-3 gap-3">
                    <input
                      type="text"
                      placeholder="Name"
                      value={formData.step1.primary_spoc?.name || ''}
                      onChange={(e) => updateNestedField(1, 'primary_spoc', 'name', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                    <input
                      type="email"
                      placeholder="Email"
                      value={formData.step1.primary_spoc?.email || ''}
                      onChange={(e) => updateNestedField(1, 'primary_spoc', 'email', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                    <input
                      type="tel"
                      placeholder="Mobile"
                      value={formData.step1.primary_spoc?.mobile || ''}
                      onChange={(e) => updateNestedField(1, 'primary_spoc', 'mobile', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                  </div>
                </div>

                <div>
                  <label className="form-label">Escalation Contact</label>
                  <div className="grid grid-cols-3 gap-3">
                    <input
                      type="text"
                      placeholder="Name"
                      value={formData.step1.escalation_contact?.name || ''}
                      onChange={(e) => updateNestedField(1, 'escalation_contact', 'name', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                    <input
                      type="email"
                      placeholder="Email"
                      value={formData.step1.escalation_contact?.email || ''}
                      onChange={(e) => updateNestedField(1, 'escalation_contact', 'email', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                    <input
                      type="tel"
                      placeholder="Mobile"
                      value={formData.step1.escalation_contact?.mobile || ''}
                      onChange={(e) => updateNestedField(1, 'escalation_contact', 'mobile', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                  </div>
                </div>

                <div>
                  <label className="form-label">Billing Contact</label>
                  <div className="grid grid-cols-3 gap-3">
                    <input
                      type="text"
                      placeholder="Name"
                      value={formData.step1.billing_contact?.name || ''}
                      onChange={(e) => updateNestedField(1, 'billing_contact', 'name', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                    <input
                      type="email"
                      placeholder="Email"
                      value={formData.step1.billing_contact?.email || ''}
                      onChange={(e) => updateNestedField(1, 'billing_contact', 'email', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                    <input
                      type="tel"
                      placeholder="Mobile"
                      value={formData.step1.billing_contact?.mobile || ''}
                      onChange={(e) => updateNestedField(1, 'billing_contact', 'mobile', e.target.value)}
                      className="form-input"
                      disabled={!isEditable}
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Office Environment */}
        {currentStep === 2 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-900">Office & Environment Snapshot</h2>
            
            <div>
              <label className="form-label">Office Type</label>
              <div className="grid grid-cols-4 gap-3">
                {['corporate', 'coworking', 'factory', 'retail'].map(type => (
                  <label key={type} className={`flex items-center justify-center p-3 border rounded-lg cursor-pointer transition-all ${
                    formData.step2.office_type === type ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-slate-300'
                  }`}>
                    <input
                      type="radio"
                      name="office_type"
                      value={type}
                      checked={formData.step2.office_type === type}
                      onChange={(e) => updateStep(2, 'office_type', e.target.value)}
                      className="sr-only"
                      disabled={!isEditable}
                    />
                    <span className="capitalize">{type === 'coworking' ? 'Co-working' : type}</span>
                  </label>
                ))}
              </div>
            </div>

            <div>
              <label className="form-label">Working Days</label>
              <div className="flex flex-wrap gap-2">
                {WORKING_DAYS.map(day => (
                  <label key={day.value} className={`px-3 py-2 border rounded-lg cursor-pointer transition-all ${
                    formData.step2.working_days?.includes(day.value) ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-slate-300'
                  }`}>
                    <input
                      type="checkbox"
                      checked={formData.step2.working_days?.includes(day.value)}
                      onChange={(e) => {
                        const days = formData.step2.working_days || [];
                        if (e.target.checked) {
                          updateStep(2, 'working_days', [...days, day.value]);
                        } else {
                          updateStep(2, 'working_days', days.filter(d => d !== day.value));
                        }
                      }}
                      className="sr-only"
                      disabled={!isEditable}
                    />
                    {day.label}
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">Working Hours Start</label>
                <input
                  type="time"
                  value={formData.step2.working_hours_start}
                  onChange={(e) => updateStep(2, 'working_hours_start', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">Working Hours End</label>
                <input
                  type="time"
                  value={formData.step2.working_hours_end}
                  onChange={(e) => updateStep(2, 'working_hours_end', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">Total Employees</label>
                <input
                  type="number"
                  value={formData.step2.total_employees}
                  onChange={(e) => updateStep(2, 'total_employees', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
            </div>

            <div>
              <label className="form-label">IT Usage Nature</label>
              <div className="grid grid-cols-3 gap-3">
                {[
                  { value: 'basic', label: 'Basic', desc: 'Email, Browsing' },
                  { value: 'business_apps', label: 'Business Apps', desc: 'Office, CRM, etc.' },
                  { value: 'heavy', label: 'Heavy', desc: 'Design, Dev, ERP' },
                ].map(option => (
                  <label key={option.value} className={`flex flex-col p-3 border rounded-lg cursor-pointer transition-all ${
                    formData.step2.it_usage_nature === option.value ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-slate-300'
                  }`}>
                    <input
                      type="radio"
                      name="it_usage"
                      value={option.value}
                      checked={formData.step2.it_usage_nature === option.value}
                      onChange={(e) => updateStep(2, 'it_usage_nature', e.target.value)}
                      className="sr-only"
                      disabled={!isEditable}
                    />
                    <span className="font-medium">{option.label}</span>
                    <span className="text-xs text-slate-500">{option.desc}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Device Categories */}
        {currentStep === 3 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-900">Device Categories</h2>
            <p className="text-slate-500">Select all device types present in your organization</p>
            
            <div className="grid grid-cols-3 gap-4">
              {[
                { key: 'has_desktops', label: 'Desktop PCs', icon: '🖥️' },
                { key: 'has_laptops', label: 'Laptops', icon: '💻' },
                { key: 'has_apple_devices', label: 'Apple Devices', icon: '🍎' },
                { key: 'has_servers', label: 'Servers', icon: '🖧' },
                { key: 'has_network_devices', label: 'Network Devices', icon: '🔌' },
                { key: 'has_printers', label: 'Printers/Scanners', icon: '🖨️' },
                { key: 'has_cctv', label: 'CCTV/Access Control', icon: '📹' },
                { key: 'has_wifi_aps', label: 'Wi-Fi Access Points', icon: '📶' },
                { key: 'has_ups', label: 'UPS/Power Backup', icon: '🔋' },
              ].map(item => (
                <label key={item.key} className={`flex items-center gap-3 p-4 border rounded-lg cursor-pointer transition-all ${
                  formData.step3[item.key] ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-slate-300'
                }`}>
                  <input
                    type="checkbox"
                    checked={formData.step3[item.key]}
                    onChange={(e) => updateStep(3, item.key, e.target.checked)}
                    className="w-5 h-5 text-emerald-600 rounded"
                    disabled={!isEditable}
                  />
                  <span className="text-2xl">{item.icon}</span>
                  <span className="font-medium">{item.label}</span>
                </label>
              ))}
            </div>

            <div>
              <label className="form-label">Other Devices (specify)</label>
              <input
                type="text"
                value={formData.step3.other_devices}
                onChange={(e) => updateStep(3, 'other_devices', e.target.value)}
                className="form-input"
                placeholder="e.g., Biometric machines, Projectors, etc."
                disabled={!isEditable}
              />
            </div>
          </div>
        )}

        {/* Step 4: Device Inventory */}
        {currentStep === 4 && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-900">Device Inventory</h2>
                <p className="text-slate-500">Add all devices covered under AMC</p>
              </div>
              {isEditable && (
                <div className="flex gap-2">
                  <Button variant="outline" onClick={downloadTemplate}>
                    <Download className="h-4 w-4 mr-2" />
                    Download Template
                  </Button>
                  <label className="cursor-pointer">
                    <input
                      type="file"
                      accept=".xlsx,.xls"
                      onChange={handleExcelUpload}
                      className="hidden"
                    />
                    <Button variant="outline" as="span">
                      <Upload className="h-4 w-4 mr-2" />
                      Import Excel
                    </Button>
                  </label>
                  <Button onClick={addDevice}>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Device
                  </Button>
                </div>
              )}
            </div>

            {formData.step4.devices.length === 0 ? (
              <div className="text-center py-12 bg-slate-50 rounded-lg">
                <Monitor className="h-12 w-12 mx-auto text-slate-300 mb-4" />
                <p className="text-slate-500 mb-4">No devices added yet</p>
                <div className="flex justify-center gap-3">
                  <Button variant="outline" onClick={downloadTemplate}>
                    <Download className="h-4 w-4 mr-2" />
                    Download Excel Template
                  </Button>
                  {isEditable && (
                    <Button onClick={addDevice}>
                      <Plus className="h-4 w-4 mr-2" />
                      Add Manually
                    </Button>
                  )}
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <p className="text-sm text-slate-500">{formData.step4.devices.length} devices added</p>
                
                {formData.step4.devices.map((device, index) => (
                  <div key={device.id} className="border border-slate-200 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-medium text-slate-700">Device #{index + 1}</span>
                      {isEditable && (
                        <Button variant="ghost" size="sm" onClick={() => removeDevice(device.id)} className="text-red-600">
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                    
                    <div className="grid grid-cols-4 gap-3">
                      <div>
                        <label className="text-xs text-slate-500">Device Type *</label>
                        <select
                          value={device.device_type}
                          onChange={(e) => updateDevice(device.id, 'device_type', e.target.value)}
                          className="form-select text-sm"
                          disabled={!isEditable}
                        >
                          <option value="">Select...</option>
                          {DEVICE_TYPES.map(type => (
                            <option key={type} value={type}>{type}</option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Brand</label>
                        <input
                          type="text"
                          value={device.brand}
                          onChange={(e) => updateDevice(device.id, 'brand', e.target.value)}
                          className="form-input text-sm"
                          disabled={!isEditable}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Model</label>
                        <input
                          type="text"
                          value={device.model}
                          onChange={(e) => updateDevice(device.id, 'model', e.target.value)}
                          className="form-input text-sm"
                          disabled={!isEditable}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Serial Number *</label>
                        <input
                          type="text"
                          value={device.serial_number}
                          onChange={(e) => updateDevice(device.id, 'serial_number', e.target.value)}
                          className="form-input text-sm"
                          disabled={!isEditable}
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="text-xs text-slate-500">Configuration</label>
                        <input
                          type="text"
                          value={device.configuration}
                          onChange={(e) => updateDevice(device.id, 'configuration', e.target.value)}
                          className="form-input text-sm"
                          placeholder="RAM, Storage, CPU"
                          disabled={!isEditable}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Warranty Status</label>
                        <select
                          value={device.warranty_status}
                          onChange={(e) => updateDevice(device.id, 'warranty_status', e.target.value)}
                          className="form-select text-sm"
                          disabled={!isEditable}
                        >
                          <option value="">Select...</option>
                          <option value="under_oem">Under OEM</option>
                          <option value="extended">Extended</option>
                          <option value="expired">Expired</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Condition</label>
                        <select
                          value={device.condition}
                          onChange={(e) => updateDevice(device.id, 'condition', e.target.value)}
                          className="form-select text-sm"
                          disabled={!isEditable}
                        >
                          <option value="working">Working</option>
                          <option value="intermittent">Intermittent</option>
                          <option value="faulty">Faulty</option>
                        </select>
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Assigned User</label>
                        <input
                          type="text"
                          value={device.assigned_user}
                          onChange={(e) => updateDevice(device.id, 'assigned_user', e.target.value)}
                          className="form-input text-sm"
                          disabled={!isEditable}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Department</label>
                        <input
                          type="text"
                          value={device.department}
                          onChange={(e) => updateDevice(device.id, 'department', e.target.value)}
                          className="form-input text-sm"
                          disabled={!isEditable}
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-500">Location</label>
                        <input
                          type="text"
                          value={device.physical_location}
                          onChange={(e) => updateDevice(device.id, 'physical_location', e.target.value)}
                          className="form-input text-sm"
                          disabled={!isEditable}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 5: Network & Servers */}
        {currentStep === 5 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-900">Network & Server Infrastructure</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Internet Provider(s)</label>
                <input
                  type="text"
                  value={formData.step5.internet_providers?.join(', ') || ''}
                  onChange={(e) => updateStep(5, 'internet_providers', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                  className="form-input"
                  placeholder="e.g., Airtel, Jio"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">Bandwidth</label>
                <input
                  type="text"
                  value={formData.step5.bandwidth}
                  onChange={(e) => updateStep(5, 'bandwidth', e.target.value)}
                  className="form-input"
                  placeholder="e.g., 100 Mbps"
                  disabled={!isEditable}
                />
              </div>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="static_ip"
                checked={formData.step5.has_static_ip}
                onChange={(e) => updateStep(5, 'has_static_ip', e.target.checked)}
                className="w-5 h-5 text-emerald-600 rounded"
                disabled={!isEditable}
              />
              <label htmlFor="static_ip" className="font-medium">Has Static IP</label>
            </div>

            {/* Conditional Static IP Address field */}
            {formData.step5.has_static_ip && (
              <div className="ml-8 bg-slate-50 p-4 rounded-lg border border-slate-200">
                <label className="form-label">Static IP Address(es)</label>
                <input
                  type="text"
                  value={formData.step5.static_ip_addresses || ''}
                  onChange={(e) => updateStep(5, 'static_ip_addresses', e.target.value)}
                  className="form-input"
                  placeholder="e.g., 203.0.113.10, 203.0.113.11"
                  disabled={!isEditable}
                />
                <p className="text-xs text-slate-500 mt-1">Enter multiple IPs separated by commas</p>
              </div>
            )}

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Router/Firewall Brand</label>
                <input
                  type="text"
                  value={formData.step5.router_firewall_brand}
                  onChange={(e) => updateStep(5, 'router_firewall_brand', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">Router/Firewall Model</label>
                <input
                  type="text"
                  value={formData.step5.router_firewall_model}
                  onChange={(e) => updateStep(5, 'router_firewall_model', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="form-label">Switch Count</label>
                <input
                  type="number"
                  value={formData.step5.switch_count}
                  onChange={(e) => updateStep(5, 'switch_count', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">VLANs (if any)</label>
                <input
                  type="text"
                  value={formData.step5.vlans}
                  onChange={(e) => updateStep(5, 'vlans', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">Wi-Fi Controller</label>
                <input
                  type="text"
                  value={formData.step5.wifi_controller}
                  onChange={(e) => updateStep(5, 'wifi_controller', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
            </div>

            {/* Servers Section */}
            <div className="border-t pt-4 mt-4">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    id="has_servers"
                    checked={formData.step5.has_servers}
                    onChange={(e) => updateStep(5, 'has_servers', e.target.checked)}
                    className="w-5 h-5 text-emerald-600 rounded"
                    disabled={!isEditable}
                  />
                  <label htmlFor="has_servers" className="font-medium">Has Servers</label>
                </div>
                {formData.step5.has_servers && isEditable && (
                  <Button variant="outline" size="sm" onClick={addServer}>
                    <Plus className="h-4 w-4 mr-1" />
                    Add Server
                  </Button>
                )}
              </div>

              {formData.step5.has_servers && formData.step5.servers?.map((server, index) => (
                <div key={server.id} className="border border-slate-200 rounded-lg p-4 mb-3">
                  <div className="flex items-center justify-between mb-3">
                    <span className="font-medium text-slate-700">Server #{index + 1}</span>
                    {isEditable && (
                      <Button variant="ghost" size="sm" onClick={() => removeServer(server.id)} className="text-red-600">
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    )}
                  </div>
                  <div className="grid grid-cols-5 gap-3">
                    <div>
                      <label className="text-xs text-slate-500">Type</label>
                      <select
                        value={server.type}
                        onChange={(e) => updateServer(server.id, 'type', e.target.value)}
                        className="form-select text-sm"
                        disabled={!isEditable}
                      >
                        <option value="physical">Physical</option>
                        <option value="virtual">Virtual</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-slate-500">OS</label>
                      <input
                        type="text"
                        value={server.os}
                        onChange={(e) => updateServer(server.id, 'os', e.target.value)}
                        className="form-input text-sm"
                        disabled={!isEditable}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-500">Roles</label>
                      <input
                        type="text"
                        value={server.roles}
                        onChange={(e) => updateServer(server.id, 'roles', e.target.value)}
                        className="form-input text-sm"
                        placeholder="AD, File, ERP"
                        disabled={!isEditable}
                      />
                    </div>
                    <div>
                      <label className="text-xs text-slate-500">Backup Status</label>
                      <select
                        value={server.backup_status}
                        onChange={(e) => updateServer(server.id, 'backup_status', e.target.value)}
                        className="form-select text-sm"
                        disabled={!isEditable}
                      >
                        <option value="">Select...</option>
                        <option value="configured">Configured</option>
                        <option value="not_configured">Not Configured</option>
                        <option value="unknown">Unknown</option>
                      </select>
                    </div>
                    <div>
                      <label className="text-xs text-slate-500">Last Backup</label>
                      <input
                        type="date"
                        value={server.last_backup}
                        onChange={(e) => updateServer(server.id, 'last_backup', e.target.value)}
                        className="form-input text-sm"
                        disabled={!isEditable}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Backup Acknowledgment */}
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4 mt-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.step5.backup_responsibility_acknowledged}
                  onChange={(e) => updateStep(5, 'backup_responsibility_acknowledged', e.target.checked)}
                  className="w-5 h-5 text-amber-600 rounded mt-0.5"
                  disabled={!isEditable}
                />
                <span className="text-amber-800">
                  <strong>Important:</strong> We understand that data backup responsibility remains with the client. 
                  The IT service provider is not liable for data loss due to missing or failed backups.
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Step 6: Software & Access */}
        {currentStep === 6 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-900">Software & Access Information</h2>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Email Platform</label>
                <select
                  value={formData.step6.email_platform}
                  onChange={(e) => updateStep(6, 'email_platform', e.target.value)}
                  className="form-select"
                  disabled={!isEditable}
                >
                  <option value="">Select...</option>
                  <option value="google">Google Workspace</option>
                  <option value="microsoft">Microsoft 365</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div>
                <label className="form-label">Domain Name(s)</label>
                <input
                  type="text"
                  value={formData.step6.domain_names?.join(', ') || ''}
                  onChange={(e) => updateStep(6, 'domain_names', e.target.value.split(',').map(s => s.trim()).filter(Boolean))}
                  className="form-input"
                  placeholder="e.g., company.com, company.in"
                  disabled={!isEditable}
                />
              </div>
            </div>

            <div className="flex flex-wrap gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.step6.admin_access_available}
                  onChange={(e) => updateStep(6, 'admin_access_available', e.target.checked)}
                  className="w-5 h-5 text-emerald-600 rounded"
                  disabled={!isEditable}
                />
                <span>Admin Access Available</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.step6.has_vpn}
                  onChange={(e) => updateStep(6, 'has_vpn', e.target.checked)}
                  className="w-5 h-5 text-emerald-600 rounded"
                  disabled={!isEditable}
                />
                <span>Uses VPN</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.step6.has_password_manager}
                  onChange={(e) => updateStep(6, 'has_password_manager', e.target.checked)}
                  className="w-5 h-5 text-emerald-600 rounded"
                  disabled={!isEditable}
                />
                <span>Uses Password Manager</span>
              </label>
            </div>

            {/* Conditional VPN and Password Manager details */}
            {(formData.step6.has_vpn || formData.step6.has_password_manager) && (
              <div className="grid grid-cols-2 gap-4 bg-slate-50 p-4 rounded-lg border border-slate-200">
                {formData.step6.has_vpn && (
                  <div>
                    <label className="form-label">VPN Type / Provider</label>
                    <input
                      type="text"
                      value={formData.step6.vpn_type || ''}
                      onChange={(e) => updateStep(6, 'vpn_type', e.target.value)}
                      className="form-input"
                      placeholder="e.g., Cisco AnyConnect, FortiClient, NordVPN"
                      disabled={!isEditable}
                    />
                  </div>
                )}
                {formData.step6.has_password_manager && (
                  <div>
                    <label className="form-label">Password Manager</label>
                    <input
                      type="text"
                      value={formData.step6.password_manager_name || ''}
                      onChange={(e) => updateStep(6, 'password_manager_name', e.target.value)}
                      className="form-input"
                      placeholder="e.g., LastPass, 1Password, Bitwarden"
                      disabled={!isEditable}
                    />
                  </div>
                )}
              </div>
            )}

            <div>
              <label className="form-label">Additional Software / Notes</label>
              <textarea
                value={formData.step6.additional_software}
                onChange={(e) => updateStep(6, 'additional_software', e.target.value)}
                className="form-input"
                rows={3}
                placeholder="List any specific software, ERP systems, antivirus, etc."
                disabled={!isEditable}
              />
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-blue-800 text-sm">
                <strong>Note:</strong> Credentials can be shared securely later via encrypted channel. 
                Do not include passwords in this form.
              </p>
            </div>
          </div>
        )}

        {/* Step 7: Vendor Handover */}
        {currentStep === 7 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-900">Existing IT Vendor Handover</h2>
            <p className="text-slate-500">This information helps us provide better service continuity</p>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="form-label">Previous IT Vendor Name</label>
                <input
                  type="text"
                  value={formData.step7.previous_vendor_name}
                  onChange={(e) => updateStep(7, 'previous_vendor_name', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
              <div>
                <label className="form-label">Vendor Contact Person</label>
                <input
                  type="text"
                  value={formData.step7.previous_vendor_contact}
                  onChange={(e) => updateStep(7, 'previous_vendor_contact', e.target.value)}
                  className="form-input"
                  disabled={!isEditable}
                />
              </div>
            </div>

            <div>
              <label className="form-label mb-3">Handover Checklist</label>
              <p className="text-sm text-slate-500 mb-3">Confirm what documentation has been received from the previous vendor:</p>
              
              <div className="grid grid-cols-2 gap-3">
                {[
                  { key: 'has_network_diagram', label: 'Network Diagram' },
                  { key: 'has_ip_details', label: 'IP Addressing Details' },
                  { key: 'has_server_credentials', label: 'Server Credentials' },
                  { key: 'has_firewall_access', label: 'Firewall Access' },
                  { key: 'has_isp_details', label: 'ISP Account Details' },
                  { key: 'has_asset_list', label: 'Asset List' },
                  { key: 'has_open_issues_list', label: 'Open Issues List' },
                ].map(item => (
                  <div key={item.key} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                    <span className="flex-1">{item.label}</span>
                    <div className="flex gap-2">
                      <label className={`px-3 py-1 rounded cursor-pointer ${formData.step7[item.key] === true ? 'bg-green-500 text-white' : 'bg-slate-200'}`}>
                        <input
                          type="radio"
                          name={item.key}
                          checked={formData.step7[item.key] === true}
                          onChange={() => updateStep(7, item.key, true)}
                          className="sr-only"
                          disabled={!isEditable}
                        />
                        Yes
                      </label>
                      <label className={`px-3 py-1 rounded cursor-pointer ${formData.step7[item.key] === false ? 'bg-red-500 text-white' : 'bg-slate-200'}`}>
                        <input
                          type="radio"
                          name={item.key}
                          checked={formData.step7[item.key] === false}
                          onChange={() => updateStep(7, item.key, false)}
                          className="sr-only"
                          disabled={!isEditable}
                        />
                        No
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div>
              <label className="form-label">Handover Notes</label>
              <textarea
                value={formData.step7.handover_notes}
                onChange={(e) => updateStep(7, 'handover_notes', e.target.value)}
                className="form-input"
                rows={3}
                placeholder="Any additional notes about the handover process..."
                disabled={!isEditable}
              />
            </div>

            <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.step7.missing_info_acknowledged}
                  onChange={(e) => updateStep(7, 'missing_info_acknowledged', e.target.checked)}
                  className="w-5 h-5 text-amber-600 rounded mt-0.5"
                  disabled={!isEditable}
                />
                <span className="text-amber-800">
                  <strong>Acknowledgment:</strong> Client confirms that missing information (marked as "No" above) 
                  may impact resolution timelines and service quality.
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Step 8: Scope Confirmation */}
        {currentStep === 8 && (
          <div className="space-y-6">
            <h2 className="text-lg font-semibold text-slate-900">AMC Scope Confirmation & Guardrails</h2>
            <p className="text-slate-500">Please review and confirm the following terms:</p>
            
            <div className="space-y-3">
              {[
                { key: 'devices_limited_to_listed', label: 'Devices covered under AMC are limited to the assets listed in this onboarding form.' },
                { key: 'new_devices_chargeable', label: 'Addition of new devices will require commercial revision.' },
                { key: 'installations_chargeable', label: 'New installations and projects are chargeable separately.' },
                { key: 'unsupported_devices_excluded', label: 'Unsupported, obsolete, or extremely old devices are excluded from AMC scope.' },
                { key: 'onsite_waiting_billable', label: 'Onsite waiting time beyond 10 minutes is billable.' },
                { key: 'reopened_tickets_new', label: 'Reopened tickets (issues recurring after resolution) are treated as new tickets.' },
              ].map(item => (
                <label key={item.key} className={`flex items-start gap-3 p-4 border rounded-lg cursor-pointer transition-all ${
                  formData.step8[item.key] ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-slate-300'
                }`}>
                  <input
                    type="checkbox"
                    checked={formData.step8[item.key]}
                    onChange={(e) => updateStep(8, item.key, e.target.checked)}
                    className="w-5 h-5 text-emerald-600 rounded mt-0.5"
                    disabled={!isEditable}
                  />
                  <span>{item.label}</span>
                </label>
              ))}
            </div>

            <div>
              <label className="form-label">Additional Terms / Notes</label>
              <textarea
                value={formData.step8.additional_terms}
                onChange={(e) => updateStep(8, 'additional_terms', e.target.value)}
                className="form-input"
                rows={3}
                placeholder="Any additional terms or special conditions..."
                disabled={!isEditable}
              />
            </div>

            {/* Final Confirmation */}
            <div className="bg-emerald-50 border-2 border-emerald-500 rounded-lg p-4">
              <label className="flex items-start gap-3 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.step8.information_accuracy_confirmed}
                  onChange={(e) => updateStep(8, 'information_accuracy_confirmed', e.target.checked)}
                  className="w-6 h-6 text-emerald-600 rounded mt-0.5"
                  disabled={!isEditable}
                />
                <span className="text-emerald-800 font-medium">
                  I confirm that all information provided in this onboarding form is accurate and complete to the best of my knowledge.
                </span>
              </label>
            </div>
          </div>
        )}

        {/* Navigation */}
        <div className="flex justify-between items-center pt-6 mt-6 border-t">
          <Button
            variant="outline"
            onClick={handlePrevious}
            disabled={currentStep === 1}
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            Previous
          </Button>

          <div className="flex gap-3">
            {isEditable && (
              <Button variant="outline" onClick={() => saveDraft(true)} disabled={saving}>
                <Save className="h-4 w-4 mr-2" />
                Save Draft
              </Button>
            )}
            
            {currentStep < 8 ? (
              <Button onClick={handleNext} className="bg-emerald-600 hover:bg-emerald-700">
                Next
                <ArrowRight className="h-4 w-4 ml-2" />
              </Button>
            ) : isEditable ? (
              <Button 
                onClick={() => setShowSubmitConfirm(true)} 
                className="bg-emerald-600 hover:bg-emerald-700"
                disabled={!formData.step8.information_accuracy_confirmed}
              >
                <Send className="h-4 w-4 mr-2" />
                Submit Onboarding
              </Button>
            ) : null}
          </div>
        </div>
      </div>

      {/* Submit Confirmation Dialog */}
      <Dialog open={showSubmitConfirm} onOpenChange={setShowSubmitConfirm}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Submit Onboarding?</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 mt-4">
            <p className="text-slate-600">
              Once submitted, you will not be able to edit this form. Our team will review the information and contact you if any changes are needed.
            </p>
            <div className="flex justify-end gap-3">
              <Button variant="outline" onClick={() => setShowSubmitConfirm(false)}>
                Cancel
              </Button>
              <Button onClick={handleSubmit} className="bg-emerald-600 hover:bg-emerald-700">
                <Send className="h-4 w-4 mr-2" />
                Submit
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CompanyAMCOnboarding;
