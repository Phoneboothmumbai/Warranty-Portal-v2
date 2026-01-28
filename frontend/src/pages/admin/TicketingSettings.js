import { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { 
  Plus, Search, Edit2, Trash2, Building2, Clock, 
  CheckCircle2, AlertTriangle, MoreVertical, RefreshCw,
  Timer, Calendar, Users, Shield, Tag, FileText, MessageSquare,
  ChevronRight, ChevronDown, GripVertical, Eye, EyeOff, Zap,
  HelpCircle, FormInput, Layers
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from '../../components/ui/dialog';
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from '../../components/ui/dropdown-menu';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Icon mapping for help topics
const iconOptions = [
  { value: 'monitor', label: 'Monitor', icon: '🖥️' },
  { value: 'code', label: 'Code', icon: '💻' },
  { value: 'wifi', label: 'WiFi', icon: '📶' },
  { value: 'apple', label: 'Apple', icon: '🍎' },
  { value: 'package', label: 'Package', icon: '📦' },
  { value: 'key', label: 'Key', icon: '🔑' },
  { value: 'shield', label: 'Shield', icon: '🛡️' },
  { value: 'printer', label: 'Printer', icon: '🖨️' },
  { value: 'phone', label: 'Phone', icon: '📱' },
  { value: 'cloud', label: 'Cloud', icon: '☁️' },
];

const getTopicIcon = (iconName) => {
  const icon = iconOptions.find(i => i.value === iconName);
  return icon?.icon || '📋';
};

export default function TicketingSettings() {
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState('help-topics');
  const [loading, setLoading] = useState(true);
  
  // Data
  const [departments, setDepartments] = useState([]);
  const [slaPolicies, setSLAPolicies] = useState([]);
  const [helpTopics, setHelpTopics] = useState([]);
  const [customForms, setCustomForms] = useState([]);
  const [cannedResponses, setCannedResponses] = useState([]);
  const [admins, setAdmins] = useState([]);
  const [emailStatus, setEmailStatus] = useState(null);
  
  // Modals
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showSLAModal, setShowSLAModal] = useState(false);
  const [showHelpTopicModal, setShowHelpTopicModal] = useState(false);
  const [showFormModal, setShowFormModal] = useState(false);
  const [showCannedModal, setShowCannedModal] = useState(false);
  const [editingItem, setEditingItem] = useState(null);
  
  // Email
  const [emailTesting, setEmailTesting] = useState(false);
  const [emailSyncing, setEmailSyncing] = useState(false);
  const [testEmailAddress, setTestEmailAddress] = useState('');
  
  // Department form
  const [deptForm, setDeptForm] = useState({
    name: '', description: '', email: '', default_priority: 'medium',
    default_sla_id: '', auto_assign_to: '', is_public: true, sort_order: 0
  });
  
  // SLA form
  const [slaForm, setSLAForm] = useState({
    name: '', description: '', response_time_hours: 4, resolution_time_hours: 24,
    response_time_business_hours: true, resolution_time_business_hours: true,
    business_hours_start: '09:00', business_hours_end: '18:00',
    business_days: [1, 2, 3, 4, 5], is_default: false
  });
  
  // Help Topic form
  const [topicForm, setTopicForm] = useState({
    name: '', description: '', icon: '', auto_department_id: '',
    auto_priority: '', auto_sla_id: '', auto_assign_to: '',
    custom_form_id: '', is_public: true, sort_order: 0
  });
  
  // Custom Form state
  const [formBuilderData, setFormBuilderData] = useState({
    name: '', description: '', fields: []
  });
  const [editingField, setEditingField] = useState(null);
  
  // Canned Response form
  const [cannedForm, setCannedForm] = useState({
    title: '', content: '', department_id: '', category: '',
    tags: [], is_personal: false
  });
  
  const headers = { Authorization: `Bearer ${token}` };

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [deptRes, slaRes, topicsRes, formsRes, cannedRes, adminsRes] = await Promise.all([
        axios.get(`${API}/ticketing/admin/departments`, { headers }),
        axios.get(`${API}/ticketing/admin/sla-policies`, { headers }),
        axios.get(`${API}/ticketing/admin/help-topics?include_inactive=true`, { headers }),
        axios.get(`${API}/ticketing/admin/custom-forms`, { headers }),
        axios.get(`${API}/ticketing/admin/canned-responses`, { headers }),
        axios.get(`${API}/admin/users`, { headers }),
        axios.get(`${API}/ticketing/admin/email/status`, { headers }).catch(() => ({ data: null }))
      ]);
      setDepartments(deptRes.data || []);
      setSLAPolicies(slaRes.data || []);
      setHelpTopics(topicsRes.data || []);
      setCustomForms(formsRes.data || []);
      setCannedResponses(cannedRes.data || []);
      setAdmins(adminsRes.data?.users || adminsRes.data || []);
      setEmailStatus(emailRes.data);
    } catch (error) {
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => { fetchData(); }, [fetchData]);

  // ==================== EMAIL HANDLERS ====================
  const handleTestEmailConnection = async () => {
    setEmailTesting(true);
    try {
      const response = await axios.post(`${API}/ticketing/admin/email/test`, {}, { headers });
      if (response.data.smtp && response.data.imap) {
        toast.success('Email connection successful! SMTP and IMAP are working.');
      } else {
        const errors = response.data.errors || [];
        toast.error(`Connection issues: ${errors.join(', ') || 'Unknown error'}`);
      }
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to test connection');
    } finally {
      setEmailTesting(false);
    }
  };

  const handleSyncEmails = async () => {
    setEmailSyncing(true);
    try {
      const response = await axios.post(`${API}/ticketing/admin/email/sync`, {}, { headers });
      const stats = response.data.stats || {};
      toast.success(`Email sync complete: ${stats.processed || 0} processed, ${stats.created || 0} new tickets, ${stats.replied || 0} replies`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to sync emails');
    } finally {
      setEmailSyncing(false);
    }
  };

  const handleSendTestEmail = async () => {
    if (!testEmailAddress) {
      toast.error('Enter an email address');
      return;
    }
    try {
      await axios.post(`${API}/ticketing/admin/email/send-test?to_email=${encodeURIComponent(testEmailAddress)}`, {}, { headers });
      toast.success(`Test email sent to ${testEmailAddress}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send test email');
    }
  };

  // ==================== DEPARTMENT HANDLERS ====================
  const handleSaveDepartment = async () => {
    try {
      if (editingItem) {
        await axios.put(`${API}/ticketing/admin/departments/${editingItem.id}`, deptForm, { headers });
        toast.success('Department updated');
      } else {
        await axios.post(`${API}/ticketing/admin/departments`, deptForm, { headers });
        toast.success('Department created');
      }
      setShowDeptModal(false);
      setEditingItem(null);
      resetDeptForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save department');
    }
  };

  const resetDeptForm = () => setDeptForm({
    name: '', description: '', email: '', default_priority: 'medium',
    default_sla_id: '', auto_assign_to: '', is_public: true, sort_order: 0
  });

  const editDepartment = (dept) => {
    setEditingItem(dept);
    setDeptForm(dept);
    setShowDeptModal(true);
  };

  // ==================== SLA HANDLERS ====================
  const handleSaveSLA = async () => {
    try {
      if (editingItem) {
        await axios.put(`${API}/ticketing/admin/sla-policies/${editingItem.id}`, slaForm, { headers });
        toast.success('SLA policy updated');
      } else {
        await axios.post(`${API}/ticketing/admin/sla-policies`, slaForm, { headers });
        toast.success('SLA policy created');
      }
      setShowSLAModal(false);
      setEditingItem(null);
      resetSLAForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save SLA policy');
    }
  };

  const resetSLAForm = () => setSLAForm({
    name: '', description: '', response_time_hours: 4, resolution_time_hours: 24,
    response_time_business_hours: true, resolution_time_business_hours: true,
    business_hours_start: '09:00', business_hours_end: '18:00',
    business_days: [1, 2, 3, 4, 5], is_default: false
  });

  const editSLA = (sla) => {
    setEditingItem(sla);
    setSLAForm(sla);
    setShowSLAModal(true);
  };

  // ==================== HELP TOPIC HANDLERS ====================
  const handleSaveHelpTopic = async () => {
    try {
      if (editingItem) {
        await axios.put(`${API}/ticketing/admin/help-topics/${editingItem.id}`, topicForm, { headers });
        toast.success('Help topic updated');
      } else {
        await axios.post(`${API}/ticketing/admin/help-topics`, topicForm, { headers });
        toast.success('Help topic created');
      }
      setShowHelpTopicModal(false);
      setEditingItem(null);
      resetTopicForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save help topic');
    }
  };

  const resetTopicForm = () => setTopicForm({
    name: '', description: '', icon: '', auto_department_id: '',
    auto_priority: '', auto_sla_id: '', auto_assign_to: '',
    custom_form_id: '', is_public: true, sort_order: 0
  });

  const editHelpTopic = (topic) => {
    setEditingItem(topic);
    setTopicForm({
      name: topic.name || '',
      description: topic.description || '',
      icon: topic.icon || '',
      auto_department_id: topic.auto_department_id || '',
      auto_priority: topic.auto_priority || '',
      auto_sla_id: topic.auto_sla_id || '',
      auto_assign_to: topic.auto_assign_to || '',
      custom_form_id: topic.custom_form_id || '',
      is_public: topic.is_public !== false,
      sort_order: topic.sort_order || 0
    });
    setShowHelpTopicModal(true);
  };

  const deleteHelpTopic = async (id) => {
    if (!window.confirm('Delete this help topic?')) return;
    try {
      await axios.delete(`${API}/ticketing/admin/help-topics/${id}`, { headers });
      toast.success('Help topic deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
  };

  // ==================== CUSTOM FORM HANDLERS ====================
  const handleSaveCustomForm = async () => {
    try {
      if (editingItem) {
        await axios.put(`${API}/ticketing/admin/custom-forms/${editingItem.id}`, formBuilderData, { headers });
        toast.success('Form updated');
      } else {
        await axios.post(`${API}/ticketing/admin/custom-forms`, formBuilderData, { headers });
        toast.success('Form created');
      }
      setShowFormModal(false);
      setEditingItem(null);
      resetFormBuilder();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save form');
    }
  };

  const resetFormBuilder = () => setFormBuilderData({ name: '', description: '', fields: [] });

  const editCustomForm = (form) => {
    setEditingItem(form);
    setFormBuilderData({
      name: form.name || '',
      description: form.description || '',
      fields: form.fields || []
    });
    setShowFormModal(true);
  };

  const deleteCustomForm = async (id) => {
    if (!window.confirm('Delete this form?')) return;
    try {
      await axios.delete(`${API}/ticketing/admin/custom-forms/${id}`, { headers });
      toast.success('Form deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Cannot delete - form is in use');
    }
  };

  const addFormField = () => {
    const newField = {
      id: `field_${Date.now()}`,
      name: `field_${formBuilderData.fields.length + 1}`,
      label: `Field ${formBuilderData.fields.length + 1}`,
      field_type: 'text',
      required: false,
      options: [],
      placeholder: '',
      help_text: '',
      width: 'full',
      sort_order: formBuilderData.fields.length
    };
    setFormBuilderData(prev => ({ ...prev, fields: [...prev.fields, newField] }));
    setEditingField(newField.id);
  };

  const updateFormField = (fieldId, updates) => {
    setFormBuilderData(prev => ({
      ...prev,
      fields: prev.fields.map(f => f.id === fieldId ? { ...f, ...updates } : f)
    }));
  };

  const removeFormField = (fieldId) => {
    setFormBuilderData(prev => ({
      ...prev,
      fields: prev.fields.filter(f => f.id !== fieldId)
    }));
  };

  // ==================== CANNED RESPONSE HANDLERS ====================
  const handleSaveCanned = async () => {
    try {
      if (editingItem) {
        await axios.put(`${API}/ticketing/admin/canned-responses/${editingItem.id}`, cannedForm, { headers });
        toast.success('Canned response updated');
      } else {
        await axios.post(`${API}/ticketing/admin/canned-responses`, cannedForm, { headers });
        toast.success('Canned response created');
      }
      setShowCannedModal(false);
      setEditingItem(null);
      resetCannedForm();
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save canned response');
    }
  };

  const resetCannedForm = () => setCannedForm({
    title: '', content: '', department_id: '', category: '', tags: [], is_personal: false
  });

  const editCanned = (canned) => {
    setEditingItem(canned);
    setCannedForm({
      title: canned.title || '',
      content: canned.content || '',
      department_id: canned.department_id || '',
      category: canned.category || '',
      tags: canned.tags || [],
      is_personal: canned.is_personal || false
    });
    setShowCannedModal(true);
  };

  const deleteCanned = async (id) => {
    if (!window.confirm('Delete this canned response?')) return;
    try {
      await axios.delete(`${API}/ticketing/admin/canned-responses/${id}`, { headers });
      toast.success('Canned response deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
  };

  // ==================== RENDER ====================
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="h-8 w-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Ticketing Configuration</h1>
          <p className="text-slate-500 text-sm mt-1">Manage help topics, forms, departments, SLAs, canned responses, and email</p>
        </div>
        <Button variant="outline" onClick={fetchData} data-testid="refresh-btn">
          <RefreshCw className="h-4 w-4 mr-2" /> Refresh
        </Button>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-1 -mb-px overflow-x-auto">
          {[
            { id: 'help-topics', label: 'Help Topics', icon: HelpCircle, count: helpTopics.length },
            { id: 'custom-forms', label: 'Custom Forms', icon: FormInput, count: customForms.length },
            { id: 'canned-responses', label: 'Canned Responses', icon: MessageSquare, count: cannedResponses.length },
            { id: 'departments', label: 'Departments', icon: Building2, count: departments.length },
            { id: 'sla-policies', label: 'SLA Policies', icon: Timer, count: slaPolicies.length },
            { id: 'email', label: 'Email', icon: Tag, count: null },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-colors whitespace-nowrap ${
                activeTab === tab.id
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300'
              }`}
              data-testid={`tab-${tab.id}`}
            >
              <tab.icon className="h-4 w-4" />
              {tab.label}
              <span className={`text-xs px-2 py-0.5 rounded-full ${
                activeTab === tab.id ? 'bg-blue-100 text-blue-600' : 'bg-slate-100 text-slate-500'
              }`}>
                {tab.count !== null && tab.count}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Email Tab */}
      {activeTab === 'email' && (
        <div className="space-y-6">
          <p className="text-sm text-slate-500">
            Configure email integration to send notifications to ticket participants and receive tickets via email.
          </p>
          
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Connection Status */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="font-medium text-slate-900 mb-4 flex items-center gap-2">
                <Shield className="h-5 w-5 text-blue-600" />
                Connection Status
              </h3>
              
              {emailStatus ? (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-600">Status</span>
                    {emailStatus.is_configured ? (
                      <span className="flex items-center gap-1 text-emerald-600">
                        <CheckCircle2 className="h-4 w-4" /> Configured
                      </span>
                    ) : (
                      <span className="flex items-center gap-1 text-amber-600">
                        <AlertTriangle className="h-4 w-4" /> Not Configured
                      </span>
                    )}
                  </div>
                  
                  {emailStatus.is_configured && (
                    <>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">Email Account</span>
                        <span className="font-mono text-slate-700">{emailStatus.email_user}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">SMTP Server</span>
                        <span className="font-mono text-slate-700">{emailStatus.smtp_host}:{emailStatus.smtp_port}</span>
                      </div>
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-500">IMAP Server</span>
                        <span className="font-mono text-slate-700">{emailStatus.imap_host}:{emailStatus.imap_port}</span>
                      </div>
                    </>
                  )}
                  
                  <Button 
                    onClick={handleTestEmailConnection} 
                    disabled={emailTesting || !emailStatus.is_configured}
                    className="w-full mt-4"
                    variant="outline"
                    data-testid="test-email-btn"
                  >
                    {emailTesting ? (
                      <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Testing...</>
                    ) : (
                      <><Zap className="h-4 w-4 mr-2" /> Test Connection</>
                    )}
                  </Button>
                </div>
              ) : (
                <div className="text-center py-4 text-slate-400">
                  <p>Loading email status...</p>
                </div>
              )}
            </div>
            
            {/* Email Actions */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h3 className="font-medium text-slate-900 mb-4 flex items-center gap-2">
                <Layers className="h-5 w-5 text-purple-600" />
                Email Actions
              </h3>
              
              <div className="space-y-4">
                {/* Sync Emails */}
                <div className="p-4 bg-slate-50 rounded-lg">
                  <h4 className="font-medium text-sm text-slate-900 mb-2">Sync Incoming Emails</h4>
                  <p className="text-xs text-slate-500 mb-3">
                    Fetch unread emails from the inbox and create/update tickets automatically.
                  </p>
                  <Button 
                    onClick={handleSyncEmails} 
                    disabled={emailSyncing || !emailStatus?.is_configured}
                    size="sm"
                    data-testid="sync-emails-btn"
                  >
                    {emailSyncing ? (
                      <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Syncing...</>
                    ) : (
                      <><RefreshCw className="h-4 w-4 mr-2" /> Sync Now</>
                    )}
                  </Button>
                </div>
                
                {/* Send Test Email */}
                <div className="p-4 bg-slate-50 rounded-lg">
                  <h4 className="font-medium text-sm text-slate-900 mb-2">Send Test Email</h4>
                  <p className="text-xs text-slate-500 mb-3">
                    Send a test email to verify SMTP is working correctly.
                  </p>
                  <div className="flex gap-2">
                    <input
                      type="email"
                      value={testEmailAddress}
                      onChange={(e) => setTestEmailAddress(e.target.value)}
                      placeholder="recipient@example.com"
                      className="flex-1 px-3 py-2 border border-slate-200 rounded-lg text-sm"
                      data-testid="test-email-input"
                    />
                    <Button 
                      onClick={handleSendTestEmail} 
                      disabled={!emailStatus?.is_configured || !testEmailAddress}
                      size="sm"
                      data-testid="send-test-email-btn"
                    >
                      Send
                    </Button>
                  </div>
                </div>
              </div>
            </div>
          </div>
          
          {/* Configuration Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
            <h3 className="font-medium text-blue-900 mb-3">Configuration Instructions</h3>
            <div className="text-sm text-blue-800 space-y-2">
              <p>To enable email integration with Google Workspace:</p>
              <ol className="list-decimal list-inside space-y-1 ml-2">
                <li>Enable 2-Step Verification on your Google account</li>
                <li>Generate an App Password at <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noreferrer" className="underline">Google App Passwords</a></li>
                <li>Set the following environment variables in your server:</li>
              </ol>
              <pre className="bg-blue-100 p-3 rounded-lg mt-2 text-xs overflow-x-auto">
{`EMAIL_USER=your-email@yourdomain.com
EMAIL_PASSWORD=your-app-password
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
IMAP_HOST=imap.gmail.com
IMAP_PORT=993
EMAIL_FROM_NAME=Support Team
SYSTEM_BASE_URL=https://your-support-portal.com`}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Help Topics Tab */}
      {activeTab === 'help-topics' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-500">
              Help Topics define issue types and drive smart routing, SLA, and form selection.
            </p>
            <Button onClick={() => { resetTopicForm(); setEditingItem(null); setShowHelpTopicModal(true); }} data-testid="add-help-topic-btn">
              <Plus className="h-4 w-4 mr-2" /> Add Help Topic
            </Button>
          </div>
          
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Topic</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Auto-Routing</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Custom Form</th>
                  <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Public</th>
                  <th className="text-right text-xs font-medium text-slate-500 uppercase px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {helpTopics.map(topic => (
                  <tr key={topic.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">{getTopicIcon(topic.icon)}</span>
                        <div>
                          <p className="font-medium text-slate-900">{topic.name}</p>
                          <p className="text-xs text-slate-500">{topic.description}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="text-xs space-y-1">
                        {topic.auto_department_id && (
                          <p className="text-slate-600">
                            <span className="text-slate-400">Dept:</span> {departments.find(d => d.id === topic.auto_department_id)?.name || '-'}
                          </p>
                        )}
                        {topic.auto_priority && (
                          <p className="text-slate-600">
                            <span className="text-slate-400">Priority:</span> {topic.auto_priority}
                          </p>
                        )}
                        {topic.auto_sla_id && (
                          <p className="text-slate-600">
                            <span className="text-slate-400">SLA:</span> {slaPolicies.find(s => s.id === topic.auto_sla_id)?.name || '-'}
                          </p>
                        )}
                        {!topic.auto_department_id && !topic.auto_priority && !topic.auto_sla_id && (
                          <span className="text-slate-400">-</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {topic.custom_form_id ? (
                        <span className="inline-flex items-center gap-1 text-xs bg-purple-100 text-purple-700 px-2 py-1 rounded-full">
                          <FormInput className="h-3 w-3" />
                          {customForms.find(f => f.id === topic.custom_form_id)?.name || 'Form'}
                        </span>
                      ) : (
                        <span className="text-slate-400 text-xs">None</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      {topic.is_public ? (
                        <Eye className="h-4 w-4 text-emerald-500 mx-auto" />
                      ) : (
                        <EyeOff className="h-4 w-4 text-slate-300 mx-auto" />
                      )}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => editHelpTopic(topic)}>
                            <Edit2 className="h-4 w-4 mr-2" /> Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => deleteHelpTopic(topic.id)} className="text-red-600">
                            <Trash2 className="h-4 w-4 mr-2" /> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
                {helpTopics.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                      No help topics yet. Create one to get started.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Custom Forms Tab */}
      {activeTab === 'custom-forms' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-500">
              Custom forms collect specific information based on the selected Help Topic.
            </p>
            <Button onClick={() => { resetFormBuilder(); setEditingItem(null); setShowFormModal(true); }} data-testid="add-form-btn">
              <Plus className="h-4 w-4 mr-2" /> Add Custom Form
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {customForms.map(form => (
              <div key={form.id} className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md transition-shadow">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center">
                      <FormInput className="h-5 w-5 text-purple-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">{form.name}</h3>
                      <p className="text-xs text-slate-500">{form.fields?.length || 0} fields</p>
                    </div>
                  </div>
                  <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                      <Button variant="ghost" size="sm">
                        <MoreVertical className="h-4 w-4" />
                      </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                      <DropdownMenuItem onClick={() => editCustomForm(form)}>
                        <Edit2 className="h-4 w-4 mr-2" /> Edit
                      </DropdownMenuItem>
                      <DropdownMenuItem onClick={() => deleteCustomForm(form.id)} className="text-red-600">
                        <Trash2 className="h-4 w-4 mr-2" /> Delete
                      </DropdownMenuItem>
                    </DropdownMenuContent>
                  </DropdownMenu>
                </div>
                {form.description && (
                  <p className="text-sm text-slate-500 mt-3">{form.description}</p>
                )}
                <div className="mt-3 flex flex-wrap gap-1">
                  {form.fields?.slice(0, 4).map(field => (
                    <span key={field.id} className="text-xs bg-slate-100 text-slate-600 px-2 py-1 rounded">
                      {field.label}
                    </span>
                  ))}
                  {form.fields?.length > 4 && (
                    <span className="text-xs bg-slate-100 text-slate-400 px-2 py-1 rounded">
                      +{form.fields.length - 4} more
                    </span>
                  )}
                </div>
                <div className="mt-3 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-400">
                  <span>v{form.version || 1}</span>
                  <span>{helpTopics.filter(t => t.custom_form_id === form.id).length} topics using</span>
                </div>
              </div>
            ))}
            {customForms.length === 0 && (
              <div className="col-span-full text-center py-8 text-slate-400">
                No custom forms yet. Create one to collect specific ticket information.
              </div>
            )}
          </div>
        </div>
      )}

      {/* Canned Responses Tab */}
      {activeTab === 'canned-responses' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-500">
              Predefined replies to speed up responses. Variables: {`{{customer_name}}, {{ticket_number}}, {{department_name}}`}
            </p>
            <Button onClick={() => { resetCannedForm(); setEditingItem(null); setShowCannedModal(true); }} data-testid="add-canned-btn">
              <Plus className="h-4 w-4 mr-2" /> Add Canned Response
            </Button>
          </div>
          
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Title</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Category</th>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Department</th>
                  <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Usage</th>
                  <th className="text-right text-xs font-medium text-slate-500 uppercase px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {cannedResponses.map(canned => (
                  <tr key={canned.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div>
                        <p className="font-medium text-slate-900">{canned.title}</p>
                        <p className="text-xs text-slate-500 truncate max-w-xs">
                          {canned.content?.substring(0, 60)}...
                        </p>
                      </div>
                    </td>
                    <td className="px-4 py-3">
                      {canned.category ? (
                        <span className="inline-flex items-center text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full">
                          {canned.category}
                        </span>
                      ) : (
                        <span className="text-slate-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3">
                      {canned.department_id ? (
                        <span className="text-sm text-slate-600">
                          {departments.find(d => d.id === canned.department_id)?.name || '-'}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400">All departments</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-sm font-medium text-slate-600">{canned.usage_count || 0}</span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <DropdownMenu>
                        <DropdownMenuTrigger asChild>
                          <Button variant="ghost" size="sm">
                            <MoreVertical className="h-4 w-4" />
                          </Button>
                        </DropdownMenuTrigger>
                        <DropdownMenuContent align="end">
                          <DropdownMenuItem onClick={() => editCanned(canned)}>
                            <Edit2 className="h-4 w-4 mr-2" /> Edit
                          </DropdownMenuItem>
                          <DropdownMenuItem onClick={() => deleteCanned(canned.id)} className="text-red-600">
                            <Trash2 className="h-4 w-4 mr-2" /> Delete
                          </DropdownMenuItem>
                        </DropdownMenuContent>
                      </DropdownMenu>
                    </td>
                  </tr>
                ))}
                {cannedResponses.length === 0 && (
                  <tr>
                    <td colSpan={5} className="px-4 py-8 text-center text-slate-400">
                      No canned responses yet. Create templates to speed up replies.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Departments Tab */}
      {activeTab === 'departments' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-500">Organize tickets by department for better routing.</p>
            <Button onClick={() => { resetDeptForm(); setEditingItem(null); setShowDeptModal(true); }} data-testid="add-dept-btn">
              <Plus className="h-4 w-4 mr-2" /> Add Department
            </Button>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {departments.map(dept => (
              <div key={dept.id} className="bg-white rounded-xl border border-slate-200 p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-blue-600" />
                    </div>
                    <div>
                      <h3 className="font-medium text-slate-900">{dept.name}</h3>
                      <p className="text-xs text-slate-500">{dept.description}</p>
                    </div>
                  </div>
                  <Button variant="ghost" size="sm" onClick={() => editDepartment(dept)}>
                    <Edit2 className="h-4 w-4" />
                  </Button>
                </div>
                <div className="mt-4 space-y-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-slate-500">Default SLA</span>
                    <span className="text-slate-700">{slaPolicies.find(s => s.id === dept.default_sla_id)?.name || 'None'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Default Priority</span>
                    <span className="text-slate-700 capitalize">{dept.default_priority || 'Medium'}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-500">Public</span>
                    <span>{dept.is_public ? <Eye className="h-4 w-4 text-emerald-500" /> : <EyeOff className="h-4 w-4 text-slate-300" />}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SLA Policies Tab */}
      {activeTab === 'sla-policies' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <p className="text-sm text-slate-500">Define response and resolution time commitments.</p>
            <Button onClick={() => { resetSLAForm(); setEditingItem(null); setShowSLAModal(true); }} data-testid="add-sla-btn">
              <Plus className="h-4 w-4 mr-2" /> Add SLA Policy
            </Button>
          </div>
          
          <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
            <table className="w-full">
              <thead className="bg-slate-50 border-b border-slate-200">
                <tr>
                  <th className="text-left text-xs font-medium text-slate-500 uppercase px-4 py-3">Policy Name</th>
                  <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Response Time</th>
                  <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Resolution Time</th>
                  <th className="text-center text-xs font-medium text-slate-500 uppercase px-4 py-3">Business Hours</th>
                  <th className="text-right text-xs font-medium text-slate-500 uppercase px-4 py-3">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {slaPolicies.map(sla => (
                  <tr key={sla.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3">
                      <div className="flex items-center gap-2">
                        <p className="font-medium text-slate-900">{sla.name}</p>
                        {sla.is_default && (
                          <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full">Default</span>
                        )}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-sm text-slate-600">{sla.response_time_hours}h</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-sm text-slate-600">{sla.resolution_time_hours}h</span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      <span className="text-xs text-slate-500">
                        {sla.business_hours_start} - {sla.business_hours_end}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <Button variant="ghost" size="sm" onClick={() => editSLA(sla)}>
                        <Edit2 className="h-4 w-4" />
                      </Button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ==================== MODALS ==================== */}

      {/* Help Topic Modal */}
      <Dialog open={showHelpTopicModal} onOpenChange={setShowHelpTopicModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Help Topic' : 'Create Help Topic'}</DialogTitle>
            <DialogDescription>
              Help Topics define issue types and control smart routing.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
            <div className="grid grid-cols-2 gap-4">
              <div className="col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-1">Name *</label>
                <input
                  type="text"
                  value={topicForm.name}
                  onChange={(e) => setTopicForm(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  placeholder="e.g., Hardware Issue"
                  data-testid="topic-name-input"
                />
              </div>
              <div className="col-span-2">
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <input
                  type="text"
                  value={topicForm.description}
                  onChange={(e) => setTopicForm(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  placeholder="Brief description"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Icon</label>
                <select
                  value={topicForm.icon}
                  onChange={(e) => setTopicForm(prev => ({ ...prev, icon: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="">Select icon</option>
                  {iconOptions.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.icon} {opt.label}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Custom Form</label>
                <select
                  value={topicForm.custom_form_id}
                  onChange={(e) => setTopicForm(prev => ({ ...prev, custom_form_id: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="">No custom form</option>
                  {customForms.map(f => (
                    <option key={f.id} value={f.id}>{f.name}</option>
                  ))}
                </select>
              </div>
            </div>

            <div className="border-t border-slate-200 pt-4">
              <h4 className="text-sm font-medium text-slate-900 mb-3 flex items-center gap-2">
                <Zap className="h-4 w-4 text-amber-500" /> Auto-Routing Settings
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Auto-assign Department</label>
                  <select
                    value={topicForm.auto_department_id}
                    onChange={(e) => setTopicForm(prev => ({ ...prev, auto_department_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  >
                    <option value="">None</option>
                    {departments.map(d => (
                      <option key={d.id} value={d.id}>{d.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Auto-assign Priority</label>
                  <select
                    value={topicForm.auto_priority}
                    onChange={(e) => setTopicForm(prev => ({ ...prev, auto_priority: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  >
                    <option value="">None</option>
                    <option value="low">Low</option>
                    <option value="medium">Medium</option>
                    <option value="high">High</option>
                    <option value="critical">Critical</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Auto-assign SLA</label>
                  <select
                    value={topicForm.auto_sla_id}
                    onChange={(e) => setTopicForm(prev => ({ ...prev, auto_sla_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  >
                    <option value="">None (use default)</option>
                    {slaPolicies.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">Auto-assign To</label>
                  <select
                    value={topicForm.auto_assign_to}
                    onChange={(e) => setTopicForm(prev => ({ ...prev, auto_assign_to: e.target.value }))}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  >
                    <option value="">None</option>
                    {admins.map(a => (
                      <option key={a.id} value={a.id}>{a.name}</option>
                    ))}
                  </select>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-2">
              <input
                type="checkbox"
                id="topic-public"
                checked={topicForm.is_public}
                onChange={(e) => setTopicForm(prev => ({ ...prev, is_public: e.target.checked }))}
                className="rounded border-slate-300"
              />
              <label htmlFor="topic-public" className="text-sm text-slate-700">
                Visible in customer portal
              </label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setShowHelpTopicModal(false)}>Cancel</Button>
            <Button onClick={handleSaveHelpTopic} data-testid="save-topic-btn">
              {editingItem ? 'Update' : 'Create'} Help Topic
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Custom Form Builder Modal */}
      <Dialog open={showFormModal} onOpenChange={setShowFormModal}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Custom Form' : 'Create Custom Form'}</DialogTitle>
          </DialogHeader>
          <div className="flex-1 overflow-y-auto space-y-4 pr-2">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Form Name *</label>
                <input
                  type="text"
                  value={formBuilderData.name}
                  onChange={(e) => setFormBuilderData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  placeholder="e.g., Hardware Issue Form"
                  data-testid="form-name-input"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
                <input
                  type="text"
                  value={formBuilderData.description}
                  onChange={(e) => setFormBuilderData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  placeholder="Brief description"
                />
              </div>
            </div>

            <div className="border-t border-slate-200 pt-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="text-sm font-medium text-slate-900">Form Fields</h4>
                <Button size="sm" onClick={addFormField} data-testid="add-field-btn">
                  <Plus className="h-4 w-4 mr-1" /> Add Field
                </Button>
              </div>
              
              <div className="space-y-3">
                {formBuilderData.fields.map((field, idx) => (
                  <div
                    key={field.id}
                    className={`border rounded-lg p-4 ${editingField === field.id ? 'border-blue-500 bg-blue-50' : 'border-slate-200 bg-white'}`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex items-center gap-2">
                        <GripVertical className="h-4 w-4 text-slate-400" />
                        <span className="text-sm font-medium text-slate-700">{field.label}</span>
                        <span className="text-xs text-slate-400">({field.field_type})</span>
                        {field.required && <span className="text-xs text-red-500">*</span>}
                      </div>
                      <div className="flex items-center gap-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setEditingField(editingField === field.id ? null : field.id)}
                        >
                          <Edit2 className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeFormField(field.id)}
                        >
                          <Trash2 className="h-4 w-4 text-red-500" />
                        </Button>
                      </div>
                    </div>
                    
                    {editingField === field.id && (
                      <div className="grid grid-cols-3 gap-3 pt-3 border-t border-slate-100">
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1">Field Name</label>
                          <input
                            type="text"
                            value={field.name}
                            onChange={(e) => updateFormField(field.id, { name: e.target.value })}
                            className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1">Label</label>
                          <input
                            type="text"
                            value={field.label}
                            onChange={(e) => updateFormField(field.id, { label: e.target.value })}
                            className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1">Type</label>
                          <select
                            value={field.field_type}
                            onChange={(e) => updateFormField(field.id, { field_type: e.target.value })}
                            className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm"
                          >
                            <option value="text">Text</option>
                            <option value="textarea">Textarea</option>
                            <option value="number">Number</option>
                            <option value="email">Email</option>
                            <option value="phone">Phone</option>
                            <option value="select">Dropdown</option>
                            <option value="multiselect">Multi-select</option>
                            <option value="checkbox">Checkbox</option>
                            <option value="date">Date</option>
                            <option value="file">File Upload</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1">Placeholder</label>
                          <input
                            type="text"
                            value={field.placeholder || ''}
                            onChange={(e) => updateFormField(field.id, { placeholder: e.target.value })}
                            className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1">Help Text</label>
                          <input
                            type="text"
                            value={field.help_text || ''}
                            onChange={(e) => updateFormField(field.id, { help_text: e.target.value })}
                            className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm"
                          />
                        </div>
                        <div className="flex items-center gap-4 pt-5">
                          <label className="flex items-center gap-2 text-sm">
                            <input
                              type="checkbox"
                              checked={field.required}
                              onChange={(e) => updateFormField(field.id, { required: e.target.checked })}
                              className="rounded border-slate-300"
                            />
                            Required
                          </label>
                        </div>
                        {(field.field_type === 'select' || field.field_type === 'multiselect') && (
                          <div className="col-span-3">
                            <label className="block text-xs font-medium text-slate-600 mb-1">
                              Options (one per line: value|label)
                            </label>
                            <textarea
                              value={(field.options || []).map(o => `${o.value}|${o.label}`).join('\n')}
                              onChange={(e) => {
                                const options = e.target.value.split('\n').filter(l => l.trim()).map(line => {
                                  const [value, label] = line.split('|');
                                  return { value: value?.trim() || '', label: label?.trim() || value?.trim() || '' };
                                });
                                updateFormField(field.id, { options });
                              }}
                              className="w-full px-2 py-1.5 border border-slate-200 rounded text-sm"
                              rows={3}
                              placeholder="laptop|Laptop&#10;desktop|Desktop"
                            />
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
                {formBuilderData.fields.length === 0 && (
                  <div className="text-center py-8 text-slate-400 border border-dashed border-slate-200 rounded-lg">
                    No fields yet. Click &quot;Add Field&quot; to start building your form.
                  </div>
                )}
              </div>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setShowFormModal(false)}>Cancel</Button>
            <Button onClick={handleSaveCustomForm} data-testid="save-form-btn">
              {editingItem ? 'Update' : 'Create'} Form
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Canned Response Modal */}
      <Dialog open={showCannedModal} onOpenChange={setShowCannedModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Canned Response' : 'Create Canned Response'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Title *</label>
              <input
                type="text"
                value={cannedForm.title}
                onChange={(e) => setCannedForm(prev => ({ ...prev, title: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                placeholder="e.g., Acknowledgement - Hardware"
                data-testid="canned-title-input"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Category</label>
                <input
                  type="text"
                  value={cannedForm.category}
                  onChange={(e) => setCannedForm(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                  placeholder="e.g., Acknowledgement"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Department</label>
                <select
                  value={cannedForm.department_id}
                  onChange={(e) => setCannedForm(prev => ({ ...prev, department_id: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="">All departments</option>
                  {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Content *</label>
              <textarea
                value={cannedForm.content}
                onChange={(e) => setCannedForm(prev => ({ ...prev, content: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                rows={8}
                placeholder="Dear {{customer_name}},&#10;&#10;Thank you for your ticket ({{ticket_number}})..."
                data-testid="canned-content-input"
              />
              <p className="text-xs text-slate-500 mt-1">
                Variables: {`{{customer_name}}, {{ticket_number}}, {{subject}}, {{department_name}}, {{assigned_to}}, {{sla_due}}`}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="canned-personal"
                checked={cannedForm.is_personal}
                onChange={(e) => setCannedForm(prev => ({ ...prev, is_personal: e.target.checked }))}
                className="rounded border-slate-300"
              />
              <label htmlFor="canned-personal" className="text-sm text-slate-700">
                Personal (only visible to me)
              </label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setShowCannedModal(false)}>Cancel</Button>
            <Button onClick={handleSaveCanned} data-testid="save-canned-btn">
              {editingItem ? 'Update' : 'Create'} Response
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Department Modal */}
      <Dialog open={showDeptModal} onOpenChange={setShowDeptModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit Department' : 'Create Department'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name *</label>
              <input
                type="text"
                value={deptForm.name}
                onChange={(e) => setDeptForm(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Description</label>
              <input
                type="text"
                value={deptForm.description}
                onChange={(e) => setDeptForm(prev => ({ ...prev, description: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Default SLA</label>
                <select
                  value={deptForm.default_sla_id}
                  onChange={(e) => setDeptForm(prev => ({ ...prev, default_sla_id: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="">None</option>
                  {slaPolicies.map(s => (
                    <option key={s.id} value={s.id}>{s.name}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Default Priority</label>
                <select
                  value={deptForm.default_priority}
                  onChange={(e) => setDeptForm(prev => ({ ...prev, default_priority: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                >
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                  <option value="critical">Critical</option>
                </select>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="dept-public"
                checked={deptForm.is_public}
                onChange={(e) => setDeptForm(prev => ({ ...prev, is_public: e.target.checked }))}
                className="rounded border-slate-300"
              />
              <label htmlFor="dept-public" className="text-sm text-slate-700">Visible in customer portal</label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setShowDeptModal(false)}>Cancel</Button>
            <Button onClick={handleSaveDepartment}>
              {editingItem ? 'Update' : 'Create'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* SLA Modal */}
      <Dialog open={showSLAModal} onOpenChange={setShowSLAModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingItem ? 'Edit SLA Policy' : 'Create SLA Policy'}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Name *</label>
              <input
                type="text"
                value={slaForm.name}
                onChange={(e) => setSLAForm(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Response Time (hours)</label>
                <input
                  type="number"
                  value={slaForm.response_time_hours}
                  onChange={(e) => setSLAForm(prev => ({ ...prev, response_time_hours: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Resolution Time (hours)</label>
                <input
                  type="number"
                  value={slaForm.resolution_time_hours}
                  onChange={(e) => setSLAForm(prev => ({ ...prev, resolution_time_hours: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Business Hours Start</label>
                <input
                  type="time"
                  value={slaForm.business_hours_start}
                  onChange={(e) => setSLAForm(prev => ({ ...prev, business_hours_start: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Business Hours End</label>
                <input
                  type="time"
                  value={slaForm.business_hours_end}
                  onChange={(e) => setSLAForm(prev => ({ ...prev, business_hours_end: e.target.value }))}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                />
              </div>
            </div>
            <div className="flex items-center gap-2">
              <input
                type="checkbox"
                id="sla-default"
                checked={slaForm.is_default}
                onChange={(e) => setSLAForm(prev => ({ ...prev, is_default: e.target.checked }))}
                className="rounded border-slate-300"
              />
              <label htmlFor="sla-default" className="text-sm text-slate-700">Set as default policy</label>
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-4 border-t">
            <Button variant="outline" onClick={() => setShowSLAModal(false)}>Cancel</Button>
            <Button onClick={handleSaveSLA}>
              {editingItem ? 'Update' : 'Create'}
            </Button>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
