import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Textarea } from '../../components/ui/textarea';
import { Badge } from '../../components/ui/badge';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { 
  Plus, Settings, Trash2, Edit, GripVertical, Save,
  AlertCircle, CheckCircle2, Clock, Tag, Users, Bell,
  FileText, Workflow, Shield, ChevronRight, ChevronDown,
  HelpCircle, Palette, Hash, ToggleLeft, List, Mail,
  MessageSquare, Zap, Filter, ArrowRight, Copy
} from 'lucide-react';
import { toast } from 'sonner';
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL;

// Master type configuration
const MASTER_TYPES = {
  ticket_status: { label: 'Ticket Statuses', icon: Clock, description: 'Define ticket lifecycle stages' },
  priority: { label: 'Priorities', icon: AlertCircle, description: 'Set priority levels for tickets' },
  problem_type: { label: 'Problem Types', icon: Tag, description: 'Categorize issues by type' },
  visit_type: { label: 'Visit Types', icon: Users, description: 'Types of service visits' },
  service_category: { label: 'Service Categories', icon: FileText, description: 'Warranty, AMC, Chargeable, etc.' },
  resolution_type: { label: 'Resolution Types', icon: CheckCircle2, description: 'How issues are resolved' }
};

// Color palette for badges
const COLOR_OPTIONS = [
  { value: '#6B7280', label: 'Gray' },
  { value: '#3B82F6', label: 'Blue' },
  { value: '#10B981', label: 'Green' },
  { value: '#F59E0B', label: 'Yellow' },
  { value: '#F97316', label: 'Orange' },
  { value: '#EF4444', label: 'Red' },
  { value: '#8B5CF6', label: 'Purple' },
  { value: '#EC4899', label: 'Pink' },
  { value: '#06B6D4', label: 'Cyan' }
];

// Form field types
const FIELD_TYPES = [
  { value: 'text', label: 'Text Input', icon: '📝' },
  { value: 'textarea', label: 'Text Area', icon: '📄' },
  { value: 'number', label: 'Number', icon: '🔢' },
  { value: 'email', label: 'Email', icon: '📧' },
  { value: 'phone', label: 'Phone', icon: '📞' },
  { value: 'select', label: 'Dropdown', icon: '📋' },
  { value: 'multi_select', label: 'Multi-Select', icon: '☑️' },
  { value: 'radio', label: 'Radio Buttons', icon: '🔘' },
  { value: 'checkbox', label: 'Checkbox', icon: '✅' },
  { value: 'date', label: 'Date', icon: '📅' },
  { value: 'datetime', label: 'Date & Time', icon: '⏰' },
  { value: 'file', label: 'File Upload', icon: '📎' },
  { value: 'section_header', label: 'Section Header', icon: '📌' }
];

// Workflow triggers
const WORKFLOW_TRIGGERS = [
  { value: 'ticket_created', label: 'Ticket Created' },
  { value: 'ticket_updated', label: 'Ticket Updated' },
  { value: 'ticket_assigned', label: 'Ticket Assigned' },
  { value: 'ticket_status_changed', label: 'Status Changed' },
  { value: 'ticket_priority_changed', label: 'Priority Changed' },
  { value: 'sla_breach_warning', label: 'SLA Warning' },
  { value: 'sla_breached', label: 'SLA Breached' },
  { value: 'parts_requested', label: 'Parts Requested' },
  { value: 'visit_scheduled', label: 'Visit Scheduled' },
  { value: 'visit_completed', label: 'Visit Completed' }
];

// Condition operators
const CONDITION_OPERATORS = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Not Equals' },
  { value: 'contains', label: 'Contains' },
  { value: 'not_contains', label: 'Not Contains' },
  { value: 'starts_with', label: 'Starts With' },
  { value: 'greater_than', label: 'Greater Than' },
  { value: 'less_than', label: 'Less Than' },
  { value: 'is_empty', label: 'Is Empty' },
  { value: 'is_not_empty', label: 'Is Not Empty' },
  { value: 'in_list', label: 'In List' }
];

// Action types
const ACTION_TYPES = [
  { value: 'assign_to_user', label: 'Assign to User' },
  { value: 'assign_to_team', label: 'Assign to Team' },
  { value: 'set_priority', label: 'Set Priority' },
  { value: 'set_category', label: 'Set Category' },
  { value: 'set_status', label: 'Set Status' },
  { value: 'add_tag', label: 'Add Tag' },
  { value: 'send_email', label: 'Send Email' },
  { value: 'send_sms', label: 'Send SMS' },
  { value: 'require_approval', label: 'Require Approval' },
  { value: 'escalate', label: 'Escalate' },
  { value: 'add_comment', label: 'Add Comment' }
];

// Notification events
const NOTIFICATION_EVENTS = [
  { value: 'ticket_created', label: 'Ticket Created' },
  { value: 'ticket_assigned', label: 'Ticket Assigned' },
  { value: 'ticket_status_changed', label: 'Status Changed' },
  { value: 'ticket_comment_added', label: 'Comment Added' },
  { value: 'ticket_completed', label: 'Ticket Completed' },
  { value: 'ticket_closed', label: 'Ticket Closed' },
  { value: 'visit_scheduled', label: 'Visit Scheduled' },
  { value: 'visit_completed', label: 'Visit Completed' },
  { value: 'parts_requested', label: 'Parts Requested' },
  { value: 'parts_approved', label: 'Parts Approved' },
  { value: 'sla_warning', label: 'SLA Warning' },
  { value: 'sla_breached', label: 'SLA Breached' }
];

export default function TicketingConfig() {
  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };
  
  const [activeTab, setActiveTab] = useState('topics');
  const [loading, setLoading] = useState(false);
  
  // Data states
  const [masters, setMasters] = useState({});
  const [helpTopics, setHelpTopics] = useState([]);
  const [workflowRules, setWorkflowRules] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [staff, setStaff] = useState([]);
  const [cannedResponses, setCannedResponses] = useState([]);
  const [cannedCategories, setCannedCategories] = useState([]);
  const [slaPolicies, setSlaPolicies] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [customForms, setCustomForms] = useState([]);
  
  // Modal states
  const [showMasterModal, setShowMasterModal] = useState(false);
  const [showTopicModal, setShowTopicModal] = useState(false);
  const [showRuleModal, setShowRuleModal] = useState(false);
  const [showNotificationModal, setShowNotificationModal] = useState(false);
  const [showCannedModal, setShowCannedModal] = useState(false);
  const [showSLAModal, setShowSLAModal] = useState(false);
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showFormModal, setShowFormModal] = useState(false);
  
  // Selected items
  const [selectedMasterType, setSelectedMasterType] = useState('ticket_status');
  const [editingMaster, setEditingMaster] = useState(null);
  const [editingTopic, setEditingTopic] = useState(null);
  const [editingRule, setEditingRule] = useState(null);
  const [editingNotification, setEditingNotification] = useState(null);
  const [editingCanned, setEditingCanned] = useState(null);
  const [editingSLA, setEditingSLA] = useState(null);
  const [editingDept, setEditingDept] = useState(null);
  const [editingForm, setEditingForm] = useState(null);
  
  // Form data
  const [masterForm, setMasterForm] = useState({ name: '', code: '', color: '#6B7280', description: '', is_active: true });
  const [topicForm, setTopicForm] = useState({ name: '', description: '', is_active: true, is_public: true, custom_fields: [] });
  const [ruleForm, setRuleForm] = useState({ name: '', trigger: 'ticket_created', conditions: [], condition_logic: 'all', actions: [], is_active: true });
  const [notificationForm, setNotificationForm] = useState({ event: 'ticket_created', channels: ['email'], recipients: ['assigned_technician'], is_active: true });
  const [cannedForm, setCannedForm] = useState({ title: '', category: '', content: '', is_personal: false, is_active: true });
  const [slaForm, setSlaForm] = useState({ 
    name: '', description: '', response_time_hours: 4, resolution_time_hours: 24, 
    response_time_business_hours: true, resolution_time_business_hours: true,
    escalation_enabled: true, escalation_after_hours: 2, is_active: true, is_default: false
  });
  const [deptForm, setDeptForm] = useState({ name: '', description: '', email: '', is_active: true, is_public: true });
  const [formForm, setFormForm] = useState({ name: '', description: '', form_type: 'ticket', fields: [], is_active: true });

  // Fetch all data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [mastersRes, topicsRes, rulesRes, notifRes, staffRes, cannedRes, slaRes, deptRes, formsRes] = await Promise.all([
        axios.get(`${API_URL}/api/admin/ticketing-config/masters`, { headers }),
        axios.get(`${API_URL}/api/admin/ticketing-config/help-topics`, { headers }),
        axios.get(`${API_URL}/api/admin/ticketing-config/workflow-rules`, { headers }),
        axios.get(`${API_URL}/api/admin/ticketing-config/notifications`, { headers }),
        axios.get(`${API_URL}/api/admin/staff/users?limit=100`, { headers }).catch(() => ({ data: { users: [] } })),
        axios.get(`${API_URL}/api/admin/ticketing-config/canned-responses`, { headers }).catch(() => ({ data: { responses: [], categories: [] } })),
        axios.get(`${API_URL}/api/admin/ticketing-config/sla-policies`, { headers }).catch(() => ({ data: { policies: [] } })),
        axios.get(`${API_URL}/api/admin/ticketing-config/departments`, { headers }).catch(() => ({ data: { departments: [] } })),
        axios.get(`${API_URL}/api/admin/ticketing-config/custom-forms`, { headers }).catch(() => ({ data: { forms: [] } }))
      ]);
      
      // Group masters by type
      const grouped = {};
      (mastersRes.data.masters || []).forEach(m => {
        if (!grouped[m.master_type]) grouped[m.master_type] = [];
        grouped[m.master_type].push(m);
      });
      setMasters(grouped);
      
      setHelpTopics(topicsRes.data.topics || []);
      setWorkflowRules(rulesRes.data.rules || []);
      setNotifications(notifRes.data.settings || []);
      setStaff(staffRes.data.users || staffRes.data || []);
      setCannedResponses(cannedRes.data.responses || []);
      setCannedCategories(cannedRes.data.categories || []);
      setSlaPolicies(slaRes.data.policies || []);
      setDepartments(deptRes.data.departments || []);
      setCustomForms(formsRes.data.forms || []);
    } catch (error) {
      console.error('Failed to fetch config:', error);
      toast.error('Failed to load configuration');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Seed defaults
  const seedDefaults = async () => {
    await seedAllDefaults();
  };

  // Master CRUD
  const saveMaster = async () => {
    try {
      if (editingMaster) {
        await axios.put(`${API_URL}/api/admin/ticketing-config/masters/${editingMaster.id}`, masterForm, { headers });
        toast.success('Master updated');
      } else {
        await axios.post(`${API_URL}/api/admin/ticketing-config/masters`, { ...masterForm, master_type: selectedMasterType }, { headers });
        toast.success('Master created');
      }
      setShowMasterModal(false);
      setEditingMaster(null);
      setMasterForm({ name: '', code: '', color: '#6B7280', description: '', is_active: true });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save master');
    }
  };

  const deleteMaster = async (id) => {
    if (!window.confirm('Delete this item?')) return;
    try {
      await axios.delete(`${API_URL}/api/admin/ticketing-config/masters/${id}`, { headers });
      toast.success('Master deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
  };

  // Help Topic CRUD
  const saveTopic = async () => {
    try {
      if (editingTopic) {
        await axios.put(`${API_URL}/api/admin/ticketing-config/help-topics/${editingTopic.id}`, topicForm, { headers });
        toast.success('Help topic updated');
      } else {
        await axios.post(`${API_URL}/api/admin/ticketing-config/help-topics`, topicForm, { headers });
        toast.success('Help topic created');
      }
      setShowTopicModal(false);
      setEditingTopic(null);
      setTopicForm({ name: '', description: '', is_active: true, is_public: true, custom_fields: [] });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save topic');
    }
  };

  const deleteTopic = async (id) => {
    if (!window.confirm('Delete this topic?')) return;
    try {
      await axios.delete(`${API_URL}/api/admin/ticketing-config/help-topics/${id}`, { headers });
      toast.success('Topic deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete topic');
    }
  };

  // Workflow Rule CRUD
  const saveRule = async () => {
    try {
      if (editingRule) {
        await axios.put(`${API_URL}/api/admin/ticketing-config/workflow-rules/${editingRule.id}`, ruleForm, { headers });
        toast.success('Rule updated');
      } else {
        await axios.post(`${API_URL}/api/admin/ticketing-config/workflow-rules`, ruleForm, { headers });
        toast.success('Rule created');
      }
      setShowRuleModal(false);
      setEditingRule(null);
      setRuleForm({ name: '', trigger: 'ticket_created', conditions: [], condition_logic: 'all', actions: [], is_active: true });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save rule');
    }
  };

  const deleteRule = async (id) => {
    if (!window.confirm('Delete this rule?')) return;
    try {
      await axios.delete(`${API_URL}/api/admin/ticketing-config/workflow-rules/${id}`, { headers });
      toast.success('Rule deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete rule');
    }
  };

  // Notification CRUD
  const saveNotification = async () => {
    try {
      if (editingNotification) {
        await axios.put(`${API_URL}/api/admin/ticketing-config/notifications/${editingNotification.id}`, notificationForm, { headers });
      } else {
        await axios.post(`${API_URL}/api/admin/ticketing-config/notifications`, notificationForm, { headers });
      }
      toast.success('Notification settings saved');
      setShowNotificationModal(false);
      setEditingNotification(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to save notification settings');
    }
  };

  // Canned Response CRUD
  const saveCanned = async () => {
    try {
      if (editingCanned) {
        await axios.put(`${API_URL}/api/admin/ticketing-config/canned-responses/${editingCanned.id}`, cannedForm, { headers });
        toast.success('Canned response updated');
      } else {
        await axios.post(`${API_URL}/api/admin/ticketing-config/canned-responses`, cannedForm, { headers });
        toast.success('Canned response created');
      }
      setShowCannedModal(false);
      setEditingCanned(null);
      setCannedForm({ title: '', category: '', content: '', is_personal: false, is_active: true });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save canned response');
    }
  };

  const deleteCanned = async (id) => {
    if (!window.confirm('Delete this canned response?')) return;
    try {
      await axios.delete(`${API_URL}/api/admin/ticketing-config/canned-responses/${id}`, { headers });
      toast.success('Canned response deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
  };

  // SLA Policy CRUD
  const saveSLA = async () => {
    try {
      if (editingSLA) {
        await axios.put(`${API_URL}/api/admin/ticketing-config/sla-policies/${editingSLA.id}`, slaForm, { headers });
        toast.success('SLA policy updated');
      } else {
        await axios.post(`${API_URL}/api/admin/ticketing-config/sla-policies`, slaForm, { headers });
        toast.success('SLA policy created');
      }
      setShowSLAModal(false);
      setEditingSLA(null);
      setSlaForm({ 
        name: '', description: '', response_time_hours: 4, resolution_time_hours: 24, 
        response_time_business_hours: true, resolution_time_business_hours: true,
        escalation_enabled: true, escalation_after_hours: 2, is_active: true, is_default: false
      });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save SLA policy');
    }
  };

  const deleteSLA = async (id) => {
    if (!window.confirm('Delete this SLA policy?')) return;
    try {
      await axios.delete(`${API_URL}/api/admin/ticketing-config/sla-policies/${id}`, { headers });
      toast.success('SLA policy deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  // Department CRUD
  const saveDept = async () => {
    try {
      if (editingDept) {
        await axios.put(`${API_URL}/api/admin/ticketing-config/departments/${editingDept.id}`, deptForm, { headers });
        toast.success('Department updated');
      } else {
        await axios.post(`${API_URL}/api/admin/ticketing-config/departments`, deptForm, { headers });
        toast.success('Department created');
      }
      setShowDeptModal(false);
      setEditingDept(null);
      setDeptForm({ name: '', description: '', email: '', is_active: true, is_public: true });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save department');
    }
  };

  const deleteDept = async (id) => {
    if (!window.confirm('Delete this department?')) return;
    try {
      await axios.delete(`${API_URL}/api/admin/ticketing-config/departments/${id}`, { headers });
      toast.success('Department deleted');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete');
    }
  };

  // Custom Form CRUD
  const saveForm = async () => {
    try {
      if (editingForm) {
        await axios.put(`${API_URL}/api/admin/ticketing-config/custom-forms/${editingForm.id}`, formForm, { headers });
        toast.success('Form updated');
      } else {
        await axios.post(`${API_URL}/api/admin/ticketing-config/custom-forms`, formForm, { headers });
        toast.success('Form created');
      }
      setShowFormModal(false);
      setEditingForm(null);
      setFormForm({ name: '', description: '', form_type: 'ticket', fields: [], is_active: true });
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save form');
    }
  };

  const deleteForm = async (id) => {
    if (!window.confirm('Delete this custom form?')) return;
    try {
      await axios.delete(`${API_URL}/api/admin/ticketing-config/custom-forms/${id}`, { headers });
      toast.success('Form deleted');
      fetchData();
    } catch (error) {
      toast.error('Failed to delete');
    }
  };

  // Seed defaults for new features
  const seedAllDefaults = async () => {
    try {
      await Promise.all([
        axios.post(`${API_URL}/api/admin/ticketing-config/masters/seed-defaults`, {}, { headers }),
        axios.post(`${API_URL}/api/admin/ticketing-config/notifications/seed-defaults`, {}, { headers }),
        axios.post(`${API_URL}/api/admin/ticketing-config/sla-policies/seed-defaults`, {}, { headers }),
        axios.post(`${API_URL}/api/admin/ticketing-config/departments/seed-defaults`, {}, { headers })
      ]);
      toast.success('Default configuration seeded');
      fetchData();
    } catch (error) {
      toast.error('Failed to seed defaults');
    }
  };

  // Form field management for Help Topics
  const addFormField = () => {
    const newField = {
      id: `field_${Date.now()}`,
      field_type: 'text',
      label: 'New Field',
      placeholder: '',
      help_text: '',
      validation: { required: false },
      options: [],
      width: 'full',
      sort_order: topicForm.custom_fields.length
    };
    setTopicForm({ ...topicForm, custom_fields: [...topicForm.custom_fields, newField] });
  };

  const updateFormField = (index, updates) => {
    const fields = [...topicForm.custom_fields];
    fields[index] = { ...fields[index], ...updates };
    setTopicForm({ ...topicForm, custom_fields: fields });
  };

  const removeFormField = (index) => {
    const fields = topicForm.custom_fields.filter((_, i) => i !== index);
    setTopicForm({ ...topicForm, custom_fields: fields });
  };

  // Condition management for Rules
  const addCondition = () => {
    setRuleForm({
      ...ruleForm,
      conditions: [...ruleForm.conditions, { field: 'ticket.priority', operator: 'equals', value: '', logic: 'and' }]
    });
  };

  const updateCondition = (index, updates) => {
    const conditions = [...ruleForm.conditions];
    conditions[index] = { ...conditions[index], ...updates };
    setRuleForm({ ...ruleForm, conditions });
  };

  const removeCondition = (index) => {
    setRuleForm({ ...ruleForm, conditions: ruleForm.conditions.filter((_, i) => i !== index) });
  };

  // Action management for Rules
  const addAction = () => {
    setRuleForm({
      ...ruleForm,
      actions: [...ruleForm.actions, { action_type: 'assign_to_user', value: '' }]
    });
  };

  const updateAction = (index, updates) => {
    const actions = [...ruleForm.actions];
    actions[index] = { ...actions[index], ...updates };
    setRuleForm({ ...ruleForm, actions });
  };

  const removeAction = (index) => {
    setRuleForm({ ...ruleForm, actions: ruleForm.actions.filter((_, i) => i !== index) });
  };

  return (
    <div data-testid="ticketing-config-page" className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Ticketing Configuration</h1>
          <p className="text-slate-500">Manage service masters, help topics, workflow rules, and notifications</p>
        </div>
        <Button onClick={seedDefaults} variant="outline">
          <Settings className="h-4 w-4 mr-2" />
          Seed Defaults
        </Button>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="flex flex-wrap gap-1 w-full h-auto p-1 bg-slate-100 rounded-lg">
          <TabsTrigger value="topics" className="flex items-center gap-2 text-xs px-3 py-2">
            <HelpCircle className="h-4 w-4" />
            Help Topics
          </TabsTrigger>
          <TabsTrigger value="forms" className="flex items-center gap-2 text-xs px-3 py-2">
            <FileText className="h-4 w-4" />
            Custom Forms
          </TabsTrigger>
          <TabsTrigger value="canned" className="flex items-center gap-2 text-xs px-3 py-2">
            <MessageSquare className="h-4 w-4" />
            Canned Responses
          </TabsTrigger>
          <TabsTrigger value="departments" className="flex items-center gap-2 text-xs px-3 py-2">
            <Users className="h-4 w-4" />
            Departments
          </TabsTrigger>
          <TabsTrigger value="sla" className="flex items-center gap-2 text-xs px-3 py-2">
            <Clock className="h-4 w-4" />
            SLA Policies
          </TabsTrigger>
          <TabsTrigger value="masters" className="flex items-center gap-2 text-xs px-3 py-2">
            <List className="h-4 w-4" />
            Masters
          </TabsTrigger>
          <TabsTrigger value="notifications" className="flex items-center gap-2 text-xs px-3 py-2">
            <Bell className="h-4 w-4" />
            Notifications
          </TabsTrigger>
        </TabsList>

        {/* Service Masters Tab */}
        <TabsContent value="masters" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Master Type Selector */}
            <Card className="lg:col-span-1">
              <CardHeader>
                <CardTitle className="text-sm">Master Types</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <div className="space-y-1">
                  {Object.entries(MASTER_TYPES).map(([key, config]) => {
                    const Icon = config.icon;
                    const count = masters[key]?.length || 0;
                    return (
                      <button
                        key={key}
                        onClick={() => setSelectedMasterType(key)}
                        className={`w-full flex items-center gap-3 px-4 py-3 text-left transition-colors ${
                          selectedMasterType === key ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-500' : 'hover:bg-slate-50'
                        }`}
                      >
                        <Icon className="h-4 w-4" />
                        <div className="flex-1">
                          <p className="text-sm font-medium">{config.label}</p>
                          <p className="text-xs text-slate-500">{count} items</p>
                        </div>
                        <ChevronRight className="h-4 w-4 text-slate-400" />
                      </button>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            {/* Master Items */}
            <Card className="lg:col-span-3">
              <CardHeader className="flex flex-row items-center justify-between">
                <div>
                  <CardTitle>{MASTER_TYPES[selectedMasterType]?.label}</CardTitle>
                  <CardDescription>{MASTER_TYPES[selectedMasterType]?.description}</CardDescription>
                </div>
                <Button onClick={() => { setEditingMaster(null); setMasterForm({ name: '', code: '', color: '#6B7280', description: '', is_active: true }); setShowMasterModal(true); }}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add
                </Button>
              </CardHeader>
              <CardContent>
                {(masters[selectedMasterType] || []).length === 0 ? (
                  <div className="text-center py-8 text-slate-500">
                    <List className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                    <p>No items yet. Click "Add" to create one or "Seed Defaults" to create standard items.</p>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {(masters[selectedMasterType] || []).map((item) => (
                      <div key={item.id} className="flex items-center gap-3 p-3 border rounded-lg hover:bg-slate-50 group">
                        <GripVertical className="h-4 w-4 text-slate-300 cursor-grab" />
                        <div 
                          className="w-4 h-4 rounded-full border" 
                          style={{ backgroundColor: item.color || '#6B7280' }}
                        />
                        <div className="flex-1">
                          <p className="font-medium text-slate-900">{item.name}</p>
                          <p className="text-xs text-slate-500">{item.code}</p>
                        </div>
                        {item.is_default && <Badge variant="outline" className="text-xs">Default</Badge>}
                        {item.is_system && <Badge variant="secondary" className="text-xs">System</Badge>}
                        {!item.is_active && <Badge variant="outline" className="text-xs text-red-500">Inactive</Badge>}
                        <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                          <Button 
                            size="icon" 
                            variant="ghost" 
                            className="h-8 w-8"
                            onClick={() => { setEditingMaster(item); setMasterForm(item); setShowMasterModal(true); }}
                            disabled={item.is_system}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button 
                            size="icon" 
                            variant="ghost" 
                            className="h-8 w-8 text-red-500"
                            onClick={() => deleteMaster(item.id)}
                            disabled={item.is_system}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Help Topics Tab */}
        <TabsContent value="topics" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Help Topics</CardTitle>
                <CardDescription>Create help topics with custom forms for structured ticket input</CardDescription>
              </div>
              <Button onClick={() => { setEditingTopic(null); setTopicForm({ name: '', description: '', is_active: true, is_public: true, custom_fields: [] }); setShowTopicModal(true); }}>
                <Plus className="h-4 w-4 mr-2" />
                Add Topic
              </Button>
            </CardHeader>
            <CardContent>
              {helpTopics.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <HelpCircle className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No help topics yet. Create topics to guide users when creating tickets.</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {helpTopics.map((topic) => (
                    <Card key={topic.id} className="hover:shadow-md transition-shadow cursor-pointer" onClick={() => { setEditingTopic(topic); setTopicForm(topic); setShowTopicModal(true); }}>
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="w-8 h-8 rounded-lg bg-blue-100 flex items-center justify-center">
                              <HelpCircle className="h-4 w-4 text-blue-600" />
                            </div>
                            <div>
                              <p className="font-medium text-slate-900">{topic.name}</p>
                              <p className="text-xs text-slate-500">{topic.custom_fields?.length || 0} custom fields</p>
                            </div>
                          </div>
                          <div className="flex gap-1">
                            {!topic.is_active && <Badge variant="outline" className="text-xs text-red-500">Inactive</Badge>}
                            {topic.is_public && <Badge variant="outline" className="text-xs text-green-600">Public</Badge>}
                          </div>
                        </div>
                        {topic.description && (
                          <p className="text-sm text-slate-600 line-clamp-2">{topic.description}</p>
                        )}
                        {(topic.sla_response_hours || topic.sla_resolution_hours) && (
                          <div className="flex gap-2 mt-2">
                            {topic.sla_response_hours && <Badge variant="secondary" className="text-xs">Response: {topic.sla_response_hours}h</Badge>}
                            {topic.sla_resolution_hours && <Badge variant="secondary" className="text-xs">Resolution: {topic.sla_resolution_hours}h</Badge>}
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Workflow Rules Tab */}
        <TabsContent value="rules" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Workflow Rules</CardTitle>
                <CardDescription>Automate ticket assignment, escalation, and notifications based on conditions</CardDescription>
              </div>
              <Button onClick={() => { setEditingRule(null); setRuleForm({ name: '', trigger: 'ticket_created', conditions: [], condition_logic: 'all', actions: [], is_active: true }); setShowRuleModal(true); }}>
                <Plus className="h-4 w-4 mr-2" />
                Add Rule
              </Button>
            </CardHeader>
            <CardContent>
              {workflowRules.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Workflow className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No workflow rules yet. Create rules to automate ticket processing.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {workflowRules.map((rule, index) => (
                    <div key={rule.id} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-slate-50 group">
                      <GripVertical className="h-5 w-5 text-slate-300 cursor-grab" />
                      <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center text-sm font-medium text-purple-600">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <p className="font-medium text-slate-900">{rule.name}</p>
                          <Badge variant="outline" className="text-xs capitalize">{rule.trigger.replace(/_/g, ' ')}</Badge>
                          {!rule.is_active && <Badge variant="outline" className="text-xs text-red-500">Inactive</Badge>}
                        </div>
                        <div className="flex items-center gap-2 text-sm text-slate-500">
                          <span>{rule.conditions?.length || 0} conditions</span>
                          <ArrowRight className="h-3 w-3" />
                          <span>{rule.actions?.length || 0} actions</span>
                          {rule.execution_count > 0 && <span className="text-slate-400">• Executed {rule.execution_count}x</span>}
                        </div>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => { setEditingRule(rule); setRuleForm(rule); setShowRuleModal(true); }}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500" onClick={() => deleteRule(rule.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Notification Settings</CardTitle>
                <CardDescription>Configure when and how notifications are sent</CardDescription>
              </div>
              <Button onClick={() => { setEditingNotification(null); setNotificationForm({ event: 'ticket_created', channels: ['email'], recipients: ['assigned_technician'], is_active: true }); setShowNotificationModal(true); }}>
                <Plus className="h-4 w-4 mr-2" />
                Add Notification
              </Button>
            </CardHeader>
            <CardContent>
              {notifications.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Bell className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No notification settings yet. Click "Seed Defaults" to create standard notifications.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {notifications.map((notif) => (
                    <div key={notif.id} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-slate-50 group">
                      <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${notif.is_active ? 'bg-green-100' : 'bg-slate-100'}`}>
                        <Bell className={`h-5 w-5 ${notif.is_active ? 'text-green-600' : 'text-slate-400'}`} />
                      </div>
                      <div className="flex-1">
                        <p className="font-medium text-slate-900 capitalize">{notif.event?.replace(/_/g, ' ')}</p>
                        <div className="flex items-center gap-2 text-sm text-slate-500">
                          {notif.channels?.map(c => (
                            <Badge key={c} variant="outline" className="text-xs capitalize">{c}</Badge>
                          ))}
                          <span>→</span>
                          {notif.recipients?.slice(0, 2).map(r => (
                            <Badge key={r} variant="secondary" className="text-xs capitalize">{r.replace(/_/g, ' ')}</Badge>
                          ))}
                          {notif.recipients?.length > 2 && <span className="text-xs">+{notif.recipients.length - 2} more</span>}
                        </div>
                      </div>
                      <Switch checked={notif.is_active} disabled />
                      <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => { setEditingNotification(notif); setNotificationForm(notif); setShowNotificationModal(true); }}>
                          <Edit className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Canned Responses Tab */}
        <TabsContent value="canned" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Canned Responses</CardTitle>
                <CardDescription>Pre-defined replies for common inquiries. Use variables like {'{{customer_name}}'}, {'{{ticket_number}}'}</CardDescription>
              </div>
              <Button onClick={() => { setEditingCanned(null); setCannedForm({ title: '', category: '', content: '', is_personal: false, is_active: true }); setShowCannedModal(true); }}>
                <Plus className="h-4 w-4 mr-2" />
                Add Response
              </Button>
            </CardHeader>
            <CardContent>
              {cannedResponses.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No canned responses yet. Create one to get started.</p>
                </div>
              ) : (
                <div className="space-y-2">
                  {cannedResponses.map((item) => (
                    <div key={item.id} className="flex items-start gap-3 p-4 border rounded-lg hover:bg-slate-50 group">
                      <MessageSquare className="h-5 w-5 text-blue-500 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="font-medium text-slate-900">{item.title}</p>
                          {item.category && <Badge variant="outline" className="text-xs">{item.category}</Badge>}
                          {item.is_personal && <Badge variant="secondary" className="text-xs">Personal</Badge>}
                        </div>
                        <p className="text-sm text-slate-500 mt-1 truncate">{item.content}</p>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => { setEditingCanned(item); setCannedForm(item); setShowCannedModal(true); }}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500" onClick={() => deleteCanned(item.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Departments Tab */}
        <TabsContent value="departments" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Departments</CardTitle>
                <CardDescription>Organize tickets by department for better routing</CardDescription>
              </div>
              <Button onClick={() => { setEditingDept(null); setDeptForm({ name: '', description: '', email: '', is_active: true, is_public: true }); setShowDeptModal(true); }}>
                <Plus className="h-4 w-4 mr-2" />
                Add Department
              </Button>
            </CardHeader>
            <CardContent>
              {departments.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Users className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No departments yet. Create one to get started.</p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {departments.map((dept) => (
                    <div key={dept.id} className="p-4 border rounded-lg hover:bg-slate-50 group">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="font-medium">{dept.name}</h3>
                            {!dept.is_active && <Badge variant="outline" className="text-xs text-red-500">Inactive</Badge>}
                            {dept.is_public && <Badge variant="secondary" className="text-xs">Public</Badge>}
                          </div>
                          <p className="text-sm text-slate-500 mt-1">{dept.description || 'No description'}</p>
                          {dept.email && <p className="text-xs text-slate-400 mt-1">{dept.email}</p>}
                        </div>
                        <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => { setEditingDept(dept); setDeptForm(dept); setShowDeptModal(true); }}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500" onClick={() => deleteDept(dept.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      <div className="flex gap-4 mt-3 text-xs text-slate-500">
                        <span>{dept.member_count || 0} members</span>
                        <span>{dept.open_tickets || 0} open tickets</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* SLA Policies Tab */}
        <TabsContent value="sla" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>SLA Policies</CardTitle>
                <CardDescription>Define response and resolution time targets for tickets</CardDescription>
              </div>
              <Button onClick={() => { setEditingSLA(null); setSlaForm({ name: '', description: '', response_time_hours: 4, resolution_time_hours: 24, response_time_business_hours: true, resolution_time_business_hours: true, escalation_enabled: true, escalation_after_hours: 2, is_active: true, is_default: false }); setShowSLAModal(true); }}>
                <Plus className="h-4 w-4 mr-2" />
                Add SLA Policy
              </Button>
            </CardHeader>
            <CardContent>
              {slaPolicies.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Clock className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No SLA policies yet. Click "Seed Defaults" to create standard policies.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {slaPolicies.map((sla) => (
                    <div key={sla.id} className="flex items-center gap-4 p-4 border rounded-lg hover:bg-slate-50 group">
                      <Clock className="h-8 w-8 text-blue-500" />
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h3 className="font-medium">{sla.name}</h3>
                          {sla.is_default && <Badge className="bg-green-500">Default</Badge>}
                          {!sla.is_active && <Badge variant="outline" className="text-red-500">Inactive</Badge>}
                        </div>
                        <p className="text-sm text-slate-500">{sla.description}</p>
                        <div className="flex gap-4 mt-2 text-xs">
                          <span className="flex items-center gap-1">
                            <AlertCircle className="h-3 w-3 text-yellow-500" />
                            Response: {sla.response_time_hours}h
                          </span>
                          <span className="flex items-center gap-1">
                            <CheckCircle2 className="h-3 w-3 text-green-500" />
                            Resolution: {sla.resolution_time_hours}h
                          </span>
                          {sla.escalation_enabled && (
                            <span className="flex items-center gap-1">
                              <Zap className="h-3 w-3 text-orange-500" />
                              Escalate at {sla.escalation_after_hours}h
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                        <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => { setEditingSLA(sla); setSlaForm(sla); setShowSLAModal(true); }}>
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500" onClick={() => deleteSLA(sla.id)}>
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Custom Forms Tab */}
        <TabsContent value="forms" className="space-y-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle>Custom Forms</CardTitle>
                <CardDescription>Create custom forms to collect additional information for tickets</CardDescription>
              </div>
              <Button onClick={() => { setEditingForm(null); setFormForm({ name: '', description: '', form_type: 'ticket', fields: [], is_active: true }); setShowFormModal(true); }}>
                <Plus className="h-4 w-4 mr-2" />
                Add Form
              </Button>
            </CardHeader>
            <CardContent>
              {customForms.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <FileText className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No custom forms yet. Click "Add Form" to create one.</p>
                </div>
              ) : (
                <div className="grid gap-4 md:grid-cols-2">
                  {customForms.map((form) => (
                    <div key={form.id} className="p-4 border rounded-lg hover:bg-slate-50 group">
                      <div className="flex items-start justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <FileText className="h-5 w-5 text-blue-500" />
                            <h3 className="font-medium">{form.name}</h3>
                            <Badge variant="outline" className="text-xs capitalize">{form.form_type}</Badge>
                          </div>
                          <p className="text-sm text-slate-500 mt-1">{form.description || 'No description'}</p>
                          <p className="text-xs text-slate-400 mt-2">{form.fields?.length || 0} fields</p>
                        </div>
                        <div className="opacity-0 group-hover:opacity-100 flex gap-1">
                          <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => { setEditingForm(form); setFormForm(form); setShowFormModal(true); }}>
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500" onClick={() => deleteForm(form.id)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Master Modal */}
      <Dialog open={showMasterModal} onOpenChange={setShowMasterModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingMaster ? 'Edit' : 'Add'} {MASTER_TYPES[selectedMasterType]?.label.slice(0, -1)}</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Name *</Label>
              <Input value={masterForm.name} onChange={(e) => setMasterForm({ ...masterForm, name: e.target.value })} placeholder="Enter name" />
            </div>
            <div>
              <Label>Code</Label>
              <Input value={masterForm.code} onChange={(e) => setMasterForm({ ...masterForm, code: e.target.value.toUpperCase() })} placeholder="AUTO_GENERATED" />
            </div>
            <div>
              <Label>Color</Label>
              <div className="flex gap-2 mt-1">
                {COLOR_OPTIONS.map((c) => (
                  <button
                    key={c.value}
                    onClick={() => setMasterForm({ ...masterForm, color: c.value })}
                    className={`w-8 h-8 rounded-full border-2 ${masterForm.color === c.value ? 'border-slate-900' : 'border-transparent'}`}
                    style={{ backgroundColor: c.value }}
                    title={c.label}
                  />
                ))}
              </div>
            </div>
            <div>
              <Label>Description</Label>
              <Textarea value={masterForm.description || ''} onChange={(e) => setMasterForm({ ...masterForm, description: e.target.value })} placeholder="Optional description" />
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={masterForm.is_active} onCheckedChange={(v) => setMasterForm({ ...masterForm, is_active: v })} />
              <Label>Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowMasterModal(false)}>Cancel</Button>
            <Button onClick={saveMaster}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Help Topic Modal */}
      <Dialog open={showTopicModal} onOpenChange={setShowTopicModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingTopic ? 'Edit' : 'Create'} Help Topic</DialogTitle>
          </DialogHeader>
          <div className="space-y-6">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Topic Name *</Label>
                <Input value={topicForm.name} onChange={(e) => setTopicForm({ ...topicForm, name: e.target.value })} placeholder="e.g., Network Issue" />
              </div>
              <div className="flex items-end gap-4">
                <div className="flex items-center gap-2">
                  <Switch checked={topicForm.is_active} onCheckedChange={(v) => setTopicForm({ ...topicForm, is_active: v })} />
                  <Label>Active</Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch checked={topicForm.is_public} onCheckedChange={(v) => setTopicForm({ ...topicForm, is_public: v })} />
                  <Label>Public</Label>
                </div>
              </div>
            </div>
            <div>
              <Label>Description</Label>
              <Textarea value={topicForm.description || ''} onChange={(e) => setTopicForm({ ...topicForm, description: e.target.value })} placeholder="Help text shown to users" />
            </div>

            {/* SLA Settings */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Response SLA (hours)</Label>
                <Input type="number" value={topicForm.sla_response_hours || ''} onChange={(e) => setTopicForm({ ...topicForm, sla_response_hours: parseInt(e.target.value) || null })} placeholder="e.g., 4" />
              </div>
              <div>
                <Label>Resolution SLA (hours)</Label>
                <Input type="number" value={topicForm.sla_resolution_hours || ''} onChange={(e) => setTopicForm({ ...topicForm, sla_resolution_hours: parseInt(e.target.value) || null })} placeholder="e.g., 24" />
              </div>
            </div>

            {/* Custom Form Fields */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label className="text-base">Custom Form Fields</Label>
                <Button size="sm" variant="outline" onClick={addFormField}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Field
                </Button>
              </div>
              {topicForm.custom_fields?.length === 0 ? (
                <div className="text-center py-6 border-2 border-dashed rounded-lg text-slate-500">
                  <FileText className="h-8 w-8 mx-auto mb-2 text-slate-300" />
                  <p className="text-sm">No custom fields. Add fields to create a structured form.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {topicForm.custom_fields.map((field, index) => (
                    <div key={field.id} className="p-4 border rounded-lg bg-slate-50">
                      <div className="flex items-start gap-3">
                        <GripVertical className="h-5 w-5 text-slate-300 cursor-grab mt-2" />
                        <div className="flex-1 grid grid-cols-3 gap-3">
                          <div>
                            <Label className="text-xs">Field Type</Label>
                            <Select value={field.field_type} onValueChange={(v) => updateFormField(index, { field_type: v })}>
                              <SelectTrigger className="h-9">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                {FIELD_TYPES.map((t) => (
                                  <SelectItem key={t.value} value={t.value}>{t.icon} {t.label}</SelectItem>
                                ))}
                              </SelectContent>
                            </Select>
                          </div>
                          <div>
                            <Label className="text-xs">Label</Label>
                            <Input className="h-9" value={field.label} onChange={(e) => updateFormField(index, { label: e.target.value })} />
                          </div>
                          <div>
                            <Label className="text-xs">Width</Label>
                            <Select value={field.width} onValueChange={(v) => updateFormField(index, { width: v })}>
                              <SelectTrigger className="h-9">
                                <SelectValue />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="full">Full Width</SelectItem>
                                <SelectItem value="half">Half Width</SelectItem>
                                <SelectItem value="third">One Third</SelectItem>
                              </SelectContent>
                            </Select>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="flex items-center gap-1">
                            <Switch 
                              checked={field.validation?.required} 
                              onCheckedChange={(v) => updateFormField(index, { validation: { ...field.validation, required: v } })} 
                            />
                            <span className="text-xs text-slate-500">Required</span>
                          </div>
                          <Button size="icon" variant="ghost" className="h-8 w-8 text-red-500" onClick={() => removeFormField(index)}>
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                      {['select', 'multi_select', 'radio', 'checkbox'].includes(field.field_type) && (
                        <div className="mt-3 ml-8">
                          <Label className="text-xs">Options (one per line)</Label>
                          <Textarea
                            className="h-20 text-sm"
                            value={(field.options || []).map(o => o.label).join('\n')}
                            onChange={(e) => {
                              const options = e.target.value.split('\n').filter(l => l.trim()).map(l => ({ label: l.trim(), value: l.trim().toLowerCase().replace(/\s+/g, '_') }));
                              updateFormField(index, { options });
                            }}
                            placeholder="Option 1\nOption 2\nOption 3"
                          />
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowTopicModal(false)}>Cancel</Button>
            {editingTopic && <Button variant="outline" className="text-red-500" onClick={() => { deleteTopic(editingTopic.id); setShowTopicModal(false); }}>Delete</Button>}
            <Button onClick={saveTopic}>Save Topic</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Workflow Rule Modal */}
      <Dialog open={showRuleModal} onOpenChange={setShowRuleModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{editingRule ? 'Edit' : 'Create'} Workflow Rule</DialogTitle>
          </DialogHeader>
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Rule Name *</Label>
                <Input value={ruleForm.name} onChange={(e) => setRuleForm({ ...ruleForm, name: e.target.value })} placeholder="e.g., Auto-assign critical tickets" />
              </div>
              <div>
                <Label>Trigger Event *</Label>
                <Select value={ruleForm.trigger} onValueChange={(v) => setRuleForm({ ...ruleForm, trigger: v })}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {WORKFLOW_TRIGGERS.map((t) => (
                      <SelectItem key={t.value} value={t.value}>{t.label}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Conditions */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <Label className="text-base">Conditions</Label>
                  <Select value={ruleForm.condition_logic} onValueChange={(v) => setRuleForm({ ...ruleForm, condition_logic: v })}>
                    <SelectTrigger className="w-32 h-8">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">Match ALL</SelectItem>
                      <SelectItem value="any">Match ANY</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <Button size="sm" variant="outline" onClick={addCondition}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Condition
                </Button>
              </div>
              {ruleForm.conditions.length === 0 ? (
                <div className="text-center py-4 border-2 border-dashed rounded-lg text-slate-500 text-sm">
                  No conditions. Rule will trigger for all events.
                </div>
              ) : (
                <div className="space-y-2">
                  {ruleForm.conditions.map((cond, index) => (
                    <div key={index} className="flex items-center gap-2 p-3 bg-slate-50 rounded-lg">
                      {index > 0 && (
                        <Badge variant="outline" className="text-xs">{ruleForm.condition_logic === 'all' ? 'AND' : 'OR'}</Badge>
                      )}
                      <Select value={cond.field} onValueChange={(v) => updateCondition(index, { field: v })}>
                        <SelectTrigger className="w-40 h-9">
                          <SelectValue placeholder="Field" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="ticket.priority">Priority</SelectItem>
                          <SelectItem value="ticket.status">Status</SelectItem>
                          <SelectItem value="ticket.company_id">Company</SelectItem>
                          <SelectItem value="ticket.problem_type">Problem Type</SelectItem>
                          <SelectItem value="ticket.category">Category</SelectItem>
                          <SelectItem value="ticket.is_urgent">Is Urgent</SelectItem>
                        </SelectContent>
                      </Select>
                      <Select value={cond.operator} onValueChange={(v) => updateCondition(index, { operator: v })}>
                        <SelectTrigger className="w-32 h-9">
                          <SelectValue placeholder="Operator" />
                        </SelectTrigger>
                        <SelectContent>
                          {CONDITION_OPERATORS.map((op) => (
                            <SelectItem key={op.value} value={op.value}>{op.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {!['is_empty', 'is_not_empty'].includes(cond.operator) && (
                        <Input 
                          className="flex-1 h-9" 
                          value={cond.value} 
                          onChange={(e) => updateCondition(index, { value: e.target.value })} 
                          placeholder="Value" 
                        />
                      )}
                      <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => removeCondition(index)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Actions */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <Label className="text-base">Actions</Label>
                <Button size="sm" variant="outline" onClick={addAction}>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Action
                </Button>
              </div>
              {ruleForm.actions.length === 0 ? (
                <div className="text-center py-4 border-2 border-dashed rounded-lg text-slate-500 text-sm">
                  No actions. Add at least one action.
                </div>
              ) : (
                <div className="space-y-2">
                  {ruleForm.actions.map((action, index) => (
                    <div key={index} className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg">
                      <Zap className="h-4 w-4 text-blue-500" />
                      <Select value={action.action_type} onValueChange={(v) => updateAction(index, { action_type: v })}>
                        <SelectTrigger className="w-44 h-9">
                          <SelectValue placeholder="Action" />
                        </SelectTrigger>
                        <SelectContent>
                          {ACTION_TYPES.map((a) => (
                            <SelectItem key={a.value} value={a.value}>{a.label}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                      {action.action_type === 'assign_to_user' && (
                        <Select value={action.value} onValueChange={(v) => updateAction(index, { value: v })}>
                          <SelectTrigger className="flex-1 h-9">
                            <SelectValue placeholder="Select user" />
                          </SelectTrigger>
                          <SelectContent>
                            {staff.map((s) => (
                              <SelectItem key={s.id} value={s.id}>{s.name}</SelectItem>
                            ))}
                          </SelectContent>
                        </Select>
                      )}
                      {['set_priority', 'set_status', 'set_category', 'add_tag', 'add_comment'].includes(action.action_type) && (
                        <Input 
                          className="flex-1 h-9" 
                          value={action.value || ''} 
                          onChange={(e) => updateAction(index, { value: e.target.value })} 
                          placeholder="Value" 
                        />
                      )}
                      <Button size="icon" variant="ghost" className="h-8 w-8" onClick={() => removeAction(index)}>
                        <Trash2 className="h-4 w-4 text-red-500" />
                      </Button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch checked={ruleForm.is_active} onCheckedChange={(v) => setRuleForm({ ...ruleForm, is_active: v })} />
                <Label>Active</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={ruleForm.stop_processing} onCheckedChange={(v) => setRuleForm({ ...ruleForm, stop_processing: v })} />
                <Label>Stop processing other rules</Label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRuleModal(false)}>Cancel</Button>
            <Button onClick={saveRule}>Save Rule</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Notification Modal */}
      <Dialog open={showNotificationModal} onOpenChange={setShowNotificationModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingNotification ? 'Edit' : 'Add'} Notification Setting</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Event *</Label>
              <Select value={notificationForm.event} onValueChange={(v) => setNotificationForm({ ...notificationForm, event: v })}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {NOTIFICATION_EVENTS.map((e) => (
                    <SelectItem key={e.value} value={e.value}>{e.label}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Channels</Label>
              <div className="flex gap-2 mt-1">
                {['email', 'sms', 'in_app'].map((ch) => (
                  <Badge
                    key={ch}
                    variant={notificationForm.channels?.includes(ch) ? 'default' : 'outline'}
                    className="cursor-pointer capitalize"
                    onClick={() => {
                      const channels = notificationForm.channels || [];
                      setNotificationForm({
                        ...notificationForm,
                        channels: channels.includes(ch) ? channels.filter(c => c !== ch) : [...channels, ch]
                      });
                    }}
                  >
                    {ch === 'email' && <Mail className="h-3 w-3 mr-1" />}
                    {ch === 'sms' && <MessageSquare className="h-3 w-3 mr-1" />}
                    {ch === 'in_app' && <Bell className="h-3 w-3 mr-1" />}
                    {ch.replace('_', ' ')}
                  </Badge>
                ))}
              </div>
            </div>
            <div>
              <Label>Recipients</Label>
              <div className="flex flex-wrap gap-2 mt-1">
                {['ticket_creator', 'assigned_technician', 'company_contact', 'team_members', 'managers'].map((r) => (
                  <Badge
                    key={r}
                    variant={notificationForm.recipients?.includes(r) ? 'default' : 'outline'}
                    className="cursor-pointer capitalize text-xs"
                    onClick={() => {
                      const recipients = notificationForm.recipients || [];
                      setNotificationForm({
                        ...notificationForm,
                        recipients: recipients.includes(r) ? recipients.filter(x => x !== r) : [...recipients, r]
                      });
                    }}
                  >
                    {r.replace(/_/g, ' ')}
                  </Badge>
                ))}
              </div>
            </div>
            {notificationForm.channels?.includes('email') && (
              <div>
                <Label>Email Subject</Label>
                <Input 
                  value={notificationForm.email_subject || ''} 
                  onChange={(e) => setNotificationForm({ ...notificationForm, email_subject: e.target.value })}
                  placeholder="e.g., Ticket #{ticket_number} - {title}"
                />
                <p className="text-xs text-slate-500 mt-1">Use {'{ticket_number}'}, {'{title}'}, {'{status}'} as placeholders</p>
              </div>
            )}
            <div className="flex items-center gap-2">
              <Switch checked={notificationForm.is_active} onCheckedChange={(v) => setNotificationForm({ ...notificationForm, is_active: v })} />
              <Label>Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNotificationModal(false)}>Cancel</Button>
            <Button onClick={saveNotification}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Canned Response Modal */}
      <Dialog open={showCannedModal} onOpenChange={setShowCannedModal}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>{editingCanned ? 'Edit' : 'Create'} Canned Response</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Title *</Label>
                <Input 
                  value={cannedForm.title} 
                  onChange={(e) => setCannedForm({ ...cannedForm, title: e.target.value })} 
                  placeholder="e.g., Acknowledgement - Hardware"
                />
              </div>
              <div>
                <Label>Category</Label>
                <Input 
                  value={cannedForm.category || ''} 
                  onChange={(e) => setCannedForm({ ...cannedForm, category: e.target.value })} 
                  placeholder="e.g., Acknowledgement"
                  list="canned-categories"
                />
                <datalist id="canned-categories">
                  {cannedCategories.map((cat) => (
                    <option key={cat} value={cat} />
                  ))}
                </datalist>
              </div>
            </div>
            <div>
              <Label>Department</Label>
              <Select 
                value={cannedForm.department_id || 'all'} 
                onValueChange={(v) => setCannedForm({ ...cannedForm, department_id: v === 'all' ? null : v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="All departments" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All departments</SelectItem>
                  {departments.map((dept) => (
                    <SelectItem key={dept.id} value={dept.id}>{dept.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Content *</Label>
              <Textarea 
                value={cannedForm.content} 
                onChange={(e) => setCannedForm({ ...cannedForm, content: e.target.value })} 
                placeholder="Dear {{customer_name}},&#10;&#10;Thank you for your ticket ({{ticket_number}})..."
                rows={6}
              />
              <p className="text-xs text-slate-500 mt-1">
                Variables: {'{{customer_name}}'}, {'{{ticket_number}}'}, {'{{subject}}'}, {'{{department_name}}'}, {'{{assigned_to}}'}, {'{{sla_due}}'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={cannedForm.is_personal} onCheckedChange={(v) => setCannedForm({ ...cannedForm, is_personal: v })} />
              <Label>Personal (only visible to me)</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCannedModal(false)}>Cancel</Button>
            <Button onClick={saveCanned}>
              {editingCanned ? 'Update' : 'Create'} Response
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* SLA Policy Modal */}
      <Dialog open={showSLAModal} onOpenChange={setShowSLAModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingSLA ? 'Edit' : 'Create'} SLA Policy</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Name *</Label>
              <Input 
                value={slaForm.name} 
                onChange={(e) => setSlaForm({ ...slaForm, name: e.target.value })} 
                placeholder="e.g., Standard - 4 Hour Response"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea 
                value={slaForm.description || ''} 
                onChange={(e) => setSlaForm({ ...slaForm, description: e.target.value })} 
                placeholder="Description of this SLA policy"
                rows={2}
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Response Time (hours)</Label>
                <Input 
                  type="number" 
                  value={slaForm.response_time_hours} 
                  onChange={(e) => setSlaForm({ ...slaForm, response_time_hours: parseInt(e.target.value) || 0 })} 
                />
                <div className="flex items-center gap-2 mt-1">
                  <Switch 
                    checked={slaForm.response_time_business_hours} 
                    onCheckedChange={(v) => setSlaForm({ ...slaForm, response_time_business_hours: v })} 
                  />
                  <Label className="text-xs">Business hours only</Label>
                </div>
              </div>
              <div>
                <Label>Resolution Time (hours)</Label>
                <Input 
                  type="number" 
                  value={slaForm.resolution_time_hours} 
                  onChange={(e) => setSlaForm({ ...slaForm, resolution_time_hours: parseInt(e.target.value) || 0 })} 
                />
                <div className="flex items-center gap-2 mt-1">
                  <Switch 
                    checked={slaForm.resolution_time_business_hours} 
                    onCheckedChange={(v) => setSlaForm({ ...slaForm, resolution_time_business_hours: v })} 
                  />
                  <Label className="text-xs">Business hours only</Label>
                </div>
              </div>
            </div>
            <div className="border-t pt-4">
              <div className="flex items-center gap-2 mb-3">
                <Switch 
                  checked={slaForm.escalation_enabled} 
                  onCheckedChange={(v) => setSlaForm({ ...slaForm, escalation_enabled: v })} 
                />
                <Label>Enable Escalation</Label>
              </div>
              {slaForm.escalation_enabled && (
                <div>
                  <Label>Escalate (hours before breach)</Label>
                  <Input 
                    type="number" 
                    value={slaForm.escalation_after_hours} 
                    onChange={(e) => setSlaForm({ ...slaForm, escalation_after_hours: parseInt(e.target.value) || 0 })} 
                  />
                </div>
              )}
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch checked={slaForm.is_active} onCheckedChange={(v) => setSlaForm({ ...slaForm, is_active: v })} />
                <Label>Active</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={slaForm.is_default} onCheckedChange={(v) => setSlaForm({ ...slaForm, is_default: v })} />
                <Label>Default Policy</Label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowSLAModal(false)}>Cancel</Button>
            <Button onClick={saveSLA}>
              {editingSLA ? 'Update' : 'Create'} Policy
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Department Modal */}
      <Dialog open={showDeptModal} onOpenChange={setShowDeptModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{editingDept ? 'Edit' : 'Create'} Department</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Name *</Label>
              <Input 
                value={deptForm.name} 
                onChange={(e) => setDeptForm({ ...deptForm, name: e.target.value })} 
                placeholder="e.g., Technical Support"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Textarea 
                value={deptForm.description || ''} 
                onChange={(e) => setDeptForm({ ...deptForm, description: e.target.value })} 
                placeholder="Brief description of this department"
                rows={2}
              />
            </div>
            <div>
              <Label>Email</Label>
              <Input 
                type="email"
                value={deptForm.email || ''} 
                onChange={(e) => setDeptForm({ ...deptForm, email: e.target.value })} 
                placeholder="support@company.com"
              />
            </div>
            <div>
              <Label>Manager</Label>
              <Select 
                value={deptForm.manager_id || 'none'} 
                onValueChange={(v) => setDeptForm({ ...deptForm, manager_id: v === 'none' ? null : v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select manager" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No manager assigned</SelectItem>
                  {staff.map((s) => (
                    <SelectItem key={s.id} value={s.id}>{s.name || s.email}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>SLA Policy</Label>
              <Select 
                value={deptForm.sla_policy_id || 'none'} 
                onValueChange={(v) => setDeptForm({ ...deptForm, sla_policy_id: v === 'none' ? null : v })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Use default SLA" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">Use default SLA</SelectItem>
                  {slaPolicies.map((sla) => (
                    <SelectItem key={sla.id} value={sla.id}>{sla.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <Switch checked={deptForm.is_active} onCheckedChange={(v) => setDeptForm({ ...deptForm, is_active: v })} />
                <Label>Active</Label>
              </div>
              <div className="flex items-center gap-2">
                <Switch checked={deptForm.is_public} onCheckedChange={(v) => setDeptForm({ ...deptForm, is_public: v })} />
                <Label>Public (visible in portal)</Label>
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeptModal(false)}>Cancel</Button>
            <Button onClick={saveDept}>
              {editingDept ? 'Update' : 'Create'} Department
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Custom Form Modal */}
      <Dialog open={showFormModal} onOpenChange={setShowFormModal}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle>{editingForm ? 'Edit' : 'Create'} Custom Form</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <Label>Form Name *</Label>
              <Input 
                value={formForm.name} 
                onChange={(e) => setFormForm({ ...formForm, name: e.target.value })} 
                placeholder="e.g., Hardware Issue Form"
              />
            </div>
            <div>
              <Label>Description</Label>
              <Input 
                value={formForm.description || ''} 
                onChange={(e) => setFormForm({ ...formForm, description: e.target.value })} 
                placeholder="Brief description"
              />
            </div>
            <div>
              <Label>Form Type</Label>
              <Select 
                value={formForm.form_type} 
                onValueChange={(v) => setFormForm({ ...formForm, form_type: v })}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="ticket">Ticket Form</SelectItem>
                  <SelectItem value="visit">Visit Form</SelectItem>
                  <SelectItem value="device">Device Form</SelectItem>
                  <SelectItem value="contact">Contact Form</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Form Fields</Label>
              <div className="border rounded-lg p-4 min-h-[100px] mt-1">
                {formForm.fields?.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-4">
                    No fields yet. Click 'Add Field' to start building your form.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {formForm.fields?.map((field, index) => (
                      <div key={field.id || index} className="flex items-center gap-2 p-2 bg-slate-50 rounded">
                        <span className="text-sm flex-1">{field.label || 'Untitled Field'}</span>
                        <Badge variant="outline" className="text-xs">{field.field_type}</Badge>
                        <Button 
                          size="icon" 
                          variant="ghost" 
                          className="h-6 w-6 text-red-500"
                          onClick={() => {
                            const newFields = formForm.fields.filter((_, i) => i !== index);
                            setFormForm({ ...formForm, fields: newFields });
                          }}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="mt-3 w-full"
                  onClick={() => {
                    const newField = {
                      id: `field_${Date.now()}`,
                      field_type: 'text',
                      label: 'New Field',
                      placeholder: '',
                      validation: { required: false },
                      sort_order: formForm.fields?.length || 0
                    };
                    setFormForm({ ...formForm, fields: [...(formForm.fields || []), newField] });
                  }}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Field
                </Button>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={formForm.is_active} onCheckedChange={(v) => setFormForm({ ...formForm, is_active: v })} />
              <Label>Active</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowFormModal(false)}>Cancel</Button>
            <Button onClick={saveForm}>
              {editingForm ? 'Update' : 'Create'} Form
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
