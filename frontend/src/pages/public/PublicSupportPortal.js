import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import { 
  Send, Search, ArrowLeft, Shield, Clock, CheckCircle2, 
  AlertCircle, MessageSquare, User, Mail, Phone, 
  FileText, ChevronRight, RefreshCw, Ticket, ExternalLink
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Status badge colors
const statusConfig = {
  open: { label: 'Open', color: 'bg-blue-100 text-blue-700' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700' },
  waiting_on_customer: { label: 'Awaiting Your Reply', color: 'bg-purple-100 text-purple-700' },
  waiting_on_third_party: { label: 'Pending', color: 'bg-slate-100 text-slate-600' },
  on_hold: { label: 'On Hold', color: 'bg-slate-100 text-slate-600' },
  resolved: { label: 'Resolved', color: 'bg-emerald-100 text-emerald-700' },
  closed: { label: 'Closed', color: 'bg-slate-100 text-slate-500' },
};

export default function PublicSupportPortal() {
  const [activeTab, setActiveTab] = useState('create');  // create, check
  const [loading, setLoading] = useState(false);
  const [departments, setDepartments] = useState([]);
  const [helpTopics, setHelpTopics] = useState([]);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [customForm, setCustomForm] = useState(null);
  
  // Create ticket form
  const [form, setForm] = useState({
    name: '',
    email: '',
    phone: '',
    subject: '',
    description: '',
    help_topic_id: '',
    department_id: '',
    priority: 'medium',
    form_data: {}
  });
  
  // Check ticket form
  const [checkForm, setCheckForm] = useState({ ticket_number: '', email: '' });
  const [ticketDetails, setTicketDetails] = useState(null);
  const [replyContent, setReplyContent] = useState('');
  
  // Success state
  const [submittedTicket, setSubmittedTicket] = useState(null);

  useEffect(() => {
    fetchPublicData();
  }, []);

  const fetchPublicData = async () => {
    try {
      const [topicsRes, deptsRes] = await Promise.all([
        axios.get(`${API}/ticketing/public/help-topics`),
        axios.get(`${API}/ticketing/public/departments`)
      ]);
      setHelpTopics(topicsRes.data || []);
      setDepartments(deptsRes.data || []);
    } catch (error) {
      console.log('No public help topics available');
    }
  };

  const handleTopicSelect = async (topicId) => {
    const topic = helpTopics.find(t => t.id === topicId);
    setSelectedTopic(topic);
    setForm(prev => ({ ...prev, help_topic_id: topicId, form_data: {} }));
    
    // Fetch custom form if linked
    if (topic?.custom_form_id) {
      try {
        const response = await axios.get(`${API}/ticketing/public/custom-forms/${topic.custom_form_id}`);
        setCustomForm(response.data);
      } catch (error) {
        setCustomForm(null);
      }
    } else {
      setCustomForm(null);
    }
  };

  const updateFormData = (fieldName, value) => {
    setForm(prev => ({
      ...prev,
      form_data: { ...prev.form_data, [fieldName]: value }
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!form.name || !form.email || !form.subject || !form.description) {
      toast.error('Please fill in all required fields');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.post(`${API}/ticketing/public/tickets`, form);
      setSubmittedTicket(response.data);
      toast.success('Ticket submitted successfully!');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit ticket');
    } finally {
      setLoading(false);
    }
  };

  const handleCheckTicket = async (e) => {
    e.preventDefault();
    if (!checkForm.ticket_number || !checkForm.email) {
      toast.error('Please enter ticket number and email');
      return;
    }
    
    setLoading(true);
    try {
      const response = await axios.get(
        `${API}/ticketing/public/tickets/${checkForm.ticket_number}`,
        { params: { email: checkForm.email } }
      );
      setTicketDetails(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Ticket not found');
      setTicketDetails(null);
    } finally {
      setLoading(false);
    }
  };

  const handleReply = async () => {
    if (!replyContent.trim()) {
      toast.error('Please enter a reply');
      return;
    }
    
    setLoading(true);
    try {
      await axios.post(
        `${API}/ticketing/public/tickets/${ticketDetails.ticket_number}/reply`,
        null,
        { params: { content: replyContent, email: checkForm.email } }
      );
      toast.success('Reply sent successfully');
      setReplyContent('');
      // Refresh ticket details
      handleCheckTicket({ preventDefault: () => {} });
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send reply');
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setForm({
      name: '', email: '', phone: '', subject: '', description: '',
      department_id: '', category: '', priority: 'medium'
    });
    setSubmittedTicket(null);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-white to-blue-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2 text-slate-600 hover:text-slate-900">
            <ArrowLeft className="h-5 w-5" />
            <span className="text-sm font-medium">Back to Home</span>
          </Link>
          <div className="flex items-center gap-2">
            <Shield className="h-6 w-6 text-blue-600" />
            <span className="font-semibold text-slate-900">Support Portal</span>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Tab Navigation */}
        <div className="flex gap-2 mb-8 bg-slate-100 p-1 rounded-xl w-fit mx-auto" data-testid="support-tabs">
          <button
            onClick={() => { setActiveTab('create'); setTicketDetails(null); }}
            className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'create' 
                ? 'bg-white text-slate-900 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
            data-testid="create-ticket-tab"
          >
            <Send className="h-4 w-4 inline mr-2" />
            Submit a Request
          </button>
          <button
            onClick={() => { setActiveTab('check'); setSubmittedTicket(null); }}
            className={`px-6 py-2.5 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'check' 
                ? 'bg-white text-slate-900 shadow-sm' 
                : 'text-slate-600 hover:text-slate-900'
            }`}
            data-testid="check-ticket-tab"
          >
            <Search className="h-4 w-4 inline mr-2" />
            Check Ticket Status
          </button>
        </div>

        {/* Create Ticket Tab */}
        {activeTab === 'create' && !submittedTicket && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden" data-testid="create-ticket-form">
            <div className="bg-gradient-to-r from-blue-600 to-blue-700 p-6 text-white">
              <h1 className="text-xl font-semibold">Submit a Support Request</h1>
              <p className="text-blue-100 text-sm mt-1">
                Fill out the form below and our team will get back to you as soon as possible.
              </p>
            </div>
            
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Contact Info */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Your Name <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input
                      type="text"
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="John Doe"
                      required
                      data-testid="input-name"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Email Address <span className="text-red-500">*</span>
                  </label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input
                      type="email"
                      value={form.email}
                      onChange={(e) => setForm({ ...form, email: e.target.value })}
                      className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="you@example.com"
                      required
                      data-testid="input-email"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Phone Number
                  </label>
                  <div className="relative">
                    <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                    <input
                      type="tel"
                      value={form.phone}
                      onChange={(e) => setForm({ ...form, phone: e.target.value })}
                      className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      placeholder="+1 (555) 123-4567"
                      data-testid="input-phone"
                    />
                  </div>
                </div>
                {departments.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Department
                    </label>
                    <select
                      value={form.department_id}
                      onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                      className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      data-testid="select-department"
                    >
                      <option value="">Select a department</option>
                      {departments.map(d => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                )}
              </div>

              {/* Help Topic Selection */}
              {helpTopics.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Help Topic <span className="text-red-500">*</span>
                  </label>
                  <select
                    value={form.help_topic_id}
                    onChange={(e) => handleTopicSelect(e.target.value)}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    data-testid="select-help-topic"
                    required
                  >
                    <option value="">Select a help topic</option>
                    {helpTopics.map(topic => (
                      <option key={topic.id} value={topic.id}>{topic.topic}</option>
                    ))}
                  </select>
                  {selectedTopic && (
                    <p className="text-sm text-slate-500 mt-1">{selectedTopic.description}</p>
                  )}
                </div>
              )}

              {/* Custom Form Fields */}
              {customForm && customForm.fields && (
                <div className="space-y-4 p-4 bg-slate-50 rounded-lg border border-slate-200">
                  <h3 className="text-sm font-medium text-slate-700">Additional Information</h3>
                  {customForm.fields.map((field, index) => (
                    <div key={index}>
                      <label className="block text-sm font-medium text-slate-700 mb-1">
                        {field.label} {field.required && <span className="text-red-500">*</span>}
                      </label>
                      {field.type === 'text' && (
                        <input
                          type="text"
                          value={form.form_data[field.name] || ''}
                          onChange={(e) => updateFormData(field.name, e.target.value)}
                          className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          placeholder={field.placeholder}
                          required={field.required}
                        />
                      )}
                      {field.type === 'textarea' && (
                        <textarea
                          value={form.form_data[field.name] || ''}
                          onChange={(e) => updateFormData(field.name, e.target.value)}
                          rows={3}
                          className="w-full px-4 py-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                          placeholder={field.placeholder}
                          required={field.required}
                        />
                      )}
                      {field.type === 'select' && (
                        <select
                          value={form.form_data[field.name] || ''}
                          onChange={(e) => updateFormData(field.name, e.target.value)}
                          className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                          required={field.required}
                        >
                          <option value="">Select an option</option>
                          {field.options?.map((option, optIndex) => (
                            <option key={optIndex} value={option}>{option}</option>
                          ))}
                        </select>
                      )}
                      {field.type === 'checkbox' && (
                        <label className="flex items-center gap-2">
                          <input
                            type="checkbox"
                            checked={form.form_data[field.name] || false}
                            onChange={(e) => updateFormData(field.name, e.target.checked)}
                            className="rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                            required={field.required}
                          />
                          <span className="text-sm text-slate-600">{field.placeholder}</span>
                        </label>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {/* Priority */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {departments.length > 0 && (
                  <div>
                    <label className="block text-sm font-medium text-slate-700 mb-1">
                      Department
                    </label>
                    <select
                      value={form.department_id}
                      onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                      className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                      data-testid="select-department"
                    >
                      <option value="">Select a department</option>
                      {departments.map(d => (
                        <option key={d.id} value={d.id}>{d.name}</option>
                      ))}
                    </select>
                  </div>
                )}
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">
                    Priority
                  </label>
                  <select
                    value={form.priority}
                    onChange={(e) => setForm({ ...form, priority: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    data-testid="select-priority"
                  >
                    <option value="low">Low - General inquiry</option>
                    <option value="medium">Medium - Standard request</option>
                    <option value="high">High - Urgent issue</option>
                    <option value="critical">Critical - System down</option>
                  </select>
                </div>
              </div>

              {/* Subject */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Subject <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={form.subject}
                  onChange={(e) => setForm({ ...form, subject: e.target.value })}
                  className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Brief summary of your issue"
                  required
                  data-testid="input-subject"
                />
              </div>

              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Description <span className="text-red-500">*</span>
                </label>
                <textarea
                  value={form.description}
                  onChange={(e) => setForm({ ...form, description: e.target.value })}
                  rows={5}
                  className="w-full px-4 py-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                  placeholder="Please describe your issue in detail. Include any relevant information such as error messages, steps to reproduce, or device information."
                  required
                  data-testid="input-description"
                />
              </div>

              <div className="flex justify-end pt-2">
                <Button type="submit" disabled={loading} className="px-8" data-testid="submit-ticket-btn">
                  {loading ? (
                    <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Submitting...</>
                  ) : (
                    <><Send className="h-4 w-4 mr-2" /> Submit Request</>
                  )}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Success State */}
        {submittedTicket && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-8 text-center" data-testid="ticket-submitted-success">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 className="h-8 w-8 text-emerald-600" />
            </div>
            <h2 className="text-xl font-semibold text-slate-900 mb-2">Request Submitted!</h2>
            <p className="text-slate-500 mb-6">Your support request has been received.</p>
            
            <div className="bg-slate-50 rounded-xl p-6 mb-6 max-w-sm mx-auto">
              <p className="text-sm text-slate-500 mb-1">Your Ticket Number</p>
              <p className="text-2xl font-bold text-blue-600 font-mono" data-testid="ticket-number">
                {submittedTicket.ticket_number}
              </p>
              <p className="text-xs text-slate-400 mt-2">
                Save this number to check your ticket status later
              </p>
            </div>

            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={resetForm} data-testid="submit-another-btn">
                Submit Another Request
              </Button>
              <Button onClick={() => {
                setCheckForm({ ticket_number: submittedTicket.ticket_number, email: form.email });
                setActiveTab('check');
                setSubmittedTicket(null);
              }} data-testid="view-ticket-btn">
                View Ticket
              </Button>
            </div>
          </div>
        )}

        {/* Check Ticket Tab */}
        {activeTab === 'check' && !ticketDetails && (
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden" data-testid="check-ticket-form">
            <div className="bg-gradient-to-r from-slate-700 to-slate-800 p-6 text-white">
              <h1 className="text-xl font-semibold">Check Ticket Status</h1>
              <p className="text-slate-300 text-sm mt-1">
                Enter your ticket number and email to view your request status.
              </p>
            </div>
            
            <form onSubmit={handleCheckTicket} className="p-6 space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Ticket Number <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Ticket className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    value={checkForm.ticket_number}
                    onChange={(e) => setCheckForm({ ...checkForm, ticket_number: e.target.value.toUpperCase() })}
                    className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="TKT-20250128-ABCDEF"
                    required
                    data-testid="input-ticket-number"
                  />
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Email Address <span className="text-red-500">*</span>
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    value={checkForm.email}
                    onChange={(e) => setCheckForm({ ...checkForm, email: e.target.value })}
                    className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Email used when creating the ticket"
                    required
                    data-testid="input-check-email"
                  />
                </div>
              </div>

              <Button type="submit" disabled={loading} className="w-full" data-testid="check-status-btn">
                {loading ? (
                  <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Checking...</>
                ) : (
                  <><Search className="h-4 w-4 mr-2" /> Check Status</>
                )}
              </Button>
            </form>
          </div>
        )}

        {/* Ticket Details */}
        {ticketDetails && (
          <div className="space-y-6" data-testid="ticket-details">
            {/* Back button */}
            <button 
              onClick={() => setTicketDetails(null)}
              className="flex items-center gap-2 text-slate-600 hover:text-slate-900 text-sm"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to Search
            </button>

            {/* Ticket Header */}
            <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="p-6 border-b border-slate-100">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <p className="text-sm text-slate-500 font-mono mb-1">{ticketDetails.ticket_number}</p>
                    <h1 className="text-xl font-semibold text-slate-900">{ticketDetails.subject}</h1>
                    {ticketDetails.department_name && (
                      <p className="text-sm text-slate-500 mt-1">Department: {ticketDetails.department_name}</p>
                    )}
                  </div>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${
                    statusConfig[ticketDetails.status]?.color || 'bg-slate-100 text-slate-600'
                  }`}>
                    {statusConfig[ticketDetails.status]?.label || ticketDetails.status}
                  </span>
                </div>
                
                <div className="flex gap-6 mt-4 text-sm text-slate-500">
                  <span className="flex items-center gap-1">
                    <Clock className="h-4 w-4" />
                    Created: {new Date(ticketDetails.created_at).toLocaleDateString()}
                  </span>
                  <span className={`flex items-center gap-1 capitalize ${
                    ticketDetails.priority === 'critical' ? 'text-red-600' :
                    ticketDetails.priority === 'high' ? 'text-orange-600' :
                    ticketDetails.priority === 'medium' ? 'text-blue-600' : 'text-slate-500'
                  }`}>
                    <AlertCircle className="h-4 w-4" />
                    {ticketDetails.priority} Priority
                  </span>
                </div>
              </div>

              {/* Original Description */}
              <div className="p-6 bg-slate-50 border-b border-slate-100">
                <h3 className="text-sm font-medium text-slate-700 mb-2">Original Request</h3>
                <p className="text-sm text-slate-600 whitespace-pre-wrap">{ticketDetails.description}</p>
              </div>

              {/* Conversation Thread */}
              <div className="p-6">
                <h3 className="text-sm font-medium text-slate-700 mb-4 flex items-center gap-2">
                  <MessageSquare className="h-4 w-4" />
                  Conversation ({ticketDetails.thread?.length || 0} entries)
                </h3>
                
                <div className="space-y-4">
                  {ticketDetails.thread?.filter(e => e.entry_type !== 'system_event' || e.event_type === 'ticket_created').map((entry, idx) => (
                    <div 
                      key={entry.id || idx}
                      className={`p-4 rounded-xl ${
                        entry.author_type === 'customer' 
                          ? 'bg-blue-50 border border-blue-100 ml-0 mr-8' 
                          : entry.entry_type === 'system_event'
                          ? 'bg-slate-50 border border-slate-100 mx-8 text-center'
                          : 'bg-emerald-50 border border-emerald-100 ml-8 mr-0'
                      }`}
                    >
                      {entry.entry_type === 'system_event' ? (
                        <p className="text-xs text-slate-500">
                          {entry.event_type === 'ticket_created' && 'Ticket created'}
                          {entry.event_type === 'status_changed' && `Status changed to ${entry.event_data?.new}`}
                          <span className="text-slate-400 ml-2">
                            {new Date(entry.created_at).toLocaleString()}
                          </span>
                        </p>
                      ) : (
                        <>
                          <div className="flex items-center justify-between mb-2">
                            <span className={`text-sm font-medium ${
                              entry.author_type === 'customer' ? 'text-blue-700' : 'text-emerald-700'
                            }`}>
                              {entry.author_type === 'customer' ? 'You' : 'Support Team'}
                            </span>
                            <span className="text-xs text-slate-400">
                              {new Date(entry.created_at).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm text-slate-700 whitespace-pre-wrap">{entry.content}</p>
                        </>
                      )}
                    </div>
                  ))}
                  
                  {(!ticketDetails.thread || ticketDetails.thread.length === 0) && (
                    <p className="text-center text-sm text-slate-400 py-4">No responses yet</p>
                  )}
                </div>

                {/* Reply Form */}
                {ticketDetails.status !== 'closed' && (
                  <div className="mt-6 pt-6 border-t border-slate-100">
                    <h4 className="text-sm font-medium text-slate-700 mb-2">Add a Reply</h4>
                    <textarea
                      value={replyContent}
                      onChange={(e) => setReplyContent(e.target.value)}
                      rows={3}
                      className="w-full px-4 py-3 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
                      placeholder="Type your reply here..."
                      data-testid="input-reply"
                    />
                    <div className="flex justify-end mt-3">
                      <Button onClick={handleReply} disabled={loading || !replyContent.trim()} data-testid="send-reply-btn">
                        {loading ? (
                          <><RefreshCw className="h-4 w-4 mr-2 animate-spin" /> Sending...</>
                        ) : (
                          <><Send className="h-4 w-4 mr-2" /> Send Reply</>
                        )}
                      </Button>
                    </div>
                  </div>
                )}

                {ticketDetails.status === 'closed' && (
                  <div className="mt-6 pt-6 border-t border-slate-100 text-center text-sm text-slate-500">
                    This ticket is closed. If you need further assistance, please submit a new request.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Help Info */}
        <div className="mt-8 text-center text-sm text-slate-500">
          <p>Need immediate assistance? Contact us at <a href="mailto:support@example.com" className="text-blue-600 hover:underline">support@example.com</a></p>
        </div>
      </main>
    </div>
  );
}
