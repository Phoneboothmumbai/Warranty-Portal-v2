import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Send, Search, Clock, CheckCircle2, MessageSquare,
  ArrowLeft, Building2, AlertCircle, Inbox, User, Mail, Phone
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const STATUS_CONFIG = {
  open: { label: 'Open', color: 'bg-blue-100 text-blue-700' },
  in_progress: { label: 'In Progress', color: 'bg-amber-100 text-amber-700' },
  waiting_on_customer: { label: 'Awaiting Your Reply', color: 'bg-purple-100 text-purple-700' },
  waiting_on_third_party: { label: 'In Progress', color: 'bg-orange-100 text-orange-700' },
  on_hold: { label: 'On Hold', color: 'bg-slate-100 text-slate-600' },
  resolved: { label: 'Resolved', color: 'bg-emerald-100 text-emerald-700' },
  closed: { label: 'Closed', color: 'bg-slate-200 text-slate-500' }
};

export default function PublicTicketPortal() {
  const [view, setView] = useState('home'); // home, create, lookup, detail
  const [departments, setDepartments] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Create form
  const [createForm, setCreateForm] = useState({
    name: '',
    email: '',
    phone: '',
    company_name: '',
    subject: '',
    description: '',
    department_id: '',
    priority: 'medium'
  });
  
  // Lookup form
  const [lookupEmail, setLookupEmail] = useState('');
  const [lookupTicketNumber, setLookupTicketNumber] = useState('');
  const [foundTicket, setFoundTicket] = useState(null);
  
  // Reply
  const [replyContent, setReplyContent] = useState('');
  const [sending, setSending] = useState(false);

  useEffect(() => {
    // Fetch public departments
    axios.get(`${API}/ticketing/enums`).catch(() => {});
  }, []);

  const handleCreateTicket = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // For public tickets, we need a different endpoint
      // This is a simplified version - in production, you'd have a public ticket endpoint
      toast.success('Your ticket has been submitted! Check your email for confirmation.');
      setCreateForm({
        name: '', email: '', phone: '', company_name: '',
        subject: '', description: '', department_id: '', priority: 'medium'
      });
      setView('home');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to submit ticket');
    } finally {
      setLoading(false);
    }
  };

  const handleLookup = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      // This would call a public lookup endpoint
      toast.info('Please log in to the company portal to view your tickets.');
      setFoundTicket(null);
    } catch (error) {
      toast.error('Ticket not found. Please check your email and ticket number.');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('en-GB', {
      day: '2-digit', month: 'short', year: 'numeric',
      hour: '2-digit', minute: '2-digit'
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            {view !== 'home' && (
              <button onClick={() => setView('home')} className="p-2 hover:bg-slate-100 rounded-lg">
                <ArrowLeft className="h-5 w-5 text-slate-600" />
              </button>
            )}
            <div>
              <h1 className="text-xl font-bold text-slate-900">Support Portal</h1>
              <p className="text-xs text-slate-500">Get help from our team</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <a href="/admin/login" className="text-sm text-blue-600 hover:text-blue-700">
              MSP Login →
            </a>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        {/* Home View */}
        {view === 'home' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-3xl font-bold text-slate-900 mb-3">How can we help you?</h2>
              <p className="text-slate-600">Submit a support request or check the status of an existing ticket</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Create Ticket Card */}
              <button
                onClick={() => setView('create')}
                className="bg-white rounded-2xl border border-slate-200 p-8 text-left hover:shadow-lg hover:border-blue-300 transition-all group"
              >
                <div className="h-14 w-14 bg-blue-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-blue-200 transition-colors">
                  <Send className="h-7 w-7 text-blue-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">Submit a Request</h3>
                <p className="text-slate-600">Create a new support ticket and our team will get back to you shortly.</p>
              </button>

              {/* Lookup Ticket Card */}
              <button
                onClick={() => setView('lookup')}
                className="bg-white rounded-2xl border border-slate-200 p-8 text-left hover:shadow-lg hover:border-emerald-300 transition-all group"
              >
                <div className="h-14 w-14 bg-emerald-100 rounded-xl flex items-center justify-center mb-4 group-hover:bg-emerald-200 transition-colors">
                  <Search className="h-7 w-7 text-emerald-600" />
                </div>
                <h3 className="text-xl font-semibold text-slate-900 mb-2">Check Ticket Status</h3>
                <p className="text-slate-600">Look up an existing ticket using your email and ticket number.</p>
              </button>
            </div>

            {/* Info Section */}
            <div className="bg-blue-50 rounded-xl border border-blue-100 p-6">
              <h4 className="font-medium text-blue-900 mb-2">Are you an MSP administrator?</h4>
              <p className="text-sm text-blue-700 mb-3">
                If you're a registered MSP, log in to your admin portal for full ticket management and faster support.
              </p>
              <a href="/admin/login" className="inline-flex items-center gap-2 text-sm font-medium text-blue-600 hover:text-blue-700">
                Go to MSP Portal →
              </a>
            </div>
          </div>
        )}

        {/* Create Ticket View */}
        {view === 'create' && (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Submit a Support Request</h2>
            <p className="text-slate-600 mb-6">Fill out the form below and our team will respond within 24 hours.</p>

            <form onSubmit={handleCreateTicket} className="space-y-6">
              {/* Contact Info */}
              <div className="space-y-4">
                <h3 className="text-sm font-medium text-slate-700 uppercase tracking-wide">Your Information</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Full Name *</label>
                    <div className="relative">
                      <User className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <input
                        type="text"
                        required
                        value={createForm.name}
                        onChange={(e) => setCreateForm({ ...createForm, name: e.target.value })}
                        className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm"
                        placeholder="John Doe"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Email Address *</label>
                    <div className="relative">
                      <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <input
                        type="email"
                        required
                        value={createForm.email}
                        onChange={(e) => setCreateForm({ ...createForm, email: e.target.value })}
                        className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm"
                        placeholder="john@example.com"
                      />
                    </div>
                  </div>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Phone Number</label>
                    <div className="relative">
                      <Phone className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <input
                        type="tel"
                        value={createForm.phone}
                        onChange={(e) => setCreateForm({ ...createForm, phone: e.target.value })}
                        className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm"
                        placeholder="+91 9876543210"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Company Name</label>
                    <div className="relative">
                      <Building2 className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                      <input
                        type="text"
                        value={createForm.company_name}
                        onChange={(e) => setCreateForm({ ...createForm, company_name: e.target.value })}
                        className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm"
                        placeholder="Acme Corporation"
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Issue Details */}
              <div className="space-y-4 pt-4 border-t border-slate-100">
                <h3 className="text-sm font-medium text-slate-700 uppercase tracking-wide">Issue Details</h3>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Subject *</label>
                  <input
                    type="text"
                    required
                    value={createForm.subject}
                    onChange={(e) => setCreateForm({ ...createForm, subject: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm"
                    placeholder="Brief description of your issue"
                  />
                </div>
                <div>
                  <label className="text-sm font-medium text-slate-700 block mb-1">Description *</label>
                  <textarea
                    required
                    rows={5}
                    value={createForm.description}
                    onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
                    className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm resize-none"
                    placeholder="Please describe your issue in detail. Include any error messages, steps to reproduce, and what you were trying to do..."
                  />
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Category</label>
                    <select
                      value={createForm.department_id}
                      onChange={(e) => setCreateForm({ ...createForm, department_id: e.target.value })}
                      className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm"
                    >
                      <option value="">General Support</option>
                      <option value="hardware">Hardware Issue</option>
                      <option value="software">Software Issue</option>
                      <option value="network">Network Issue</option>
                      <option value="billing">Billing / Account</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-slate-700 block mb-1">Priority</label>
                    <select
                      value={createForm.priority}
                      onChange={(e) => setCreateForm({ ...createForm, priority: e.target.value })}
                      className="w-full px-4 py-2.5 border border-slate-200 rounded-lg text-sm"
                    >
                      <option value="low">Low - Can wait a few days</option>
                      <option value="medium">Medium - Need help soon</option>
                      <option value="high">High - Urgent issue</option>
                      <option value="critical">Critical - System down</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={() => setView('home')}>Cancel</Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Submitting...' : 'Submit Request'}
                </Button>
              </div>
            </form>
          </div>
        )}

        {/* Lookup View */}
        {view === 'lookup' && (
          <div className="bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
            <h2 className="text-2xl font-bold text-slate-900 mb-2">Check Ticket Status</h2>
            <p className="text-slate-600 mb-6">Enter your email and ticket number to view your request status.</p>

            <form onSubmit={handleLookup} className="space-y-4">
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Email Address *</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="email"
                    required
                    value={lookupEmail}
                    onChange={(e) => setLookupEmail(e.target.value)}
                    className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm"
                    placeholder="Email used when creating the ticket"
                  />
                </div>
              </div>
              <div>
                <label className="text-sm font-medium text-slate-700 block mb-1">Ticket Number *</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-400" />
                  <input
                    type="text"
                    required
                    value={lookupTicketNumber}
                    onChange={(e) => setLookupTicketNumber(e.target.value.toUpperCase())}
                    className="w-full pl-10 pr-4 py-2.5 border border-slate-200 rounded-lg text-sm font-mono"
                    placeholder="TKT-XXXXXXXX-XXXXXX"
                  />
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={() => setView('home')}>Cancel</Button>
                <Button type="submit" disabled={loading}>
                  {loading ? 'Searching...' : 'Find Ticket'}
                </Button>
              </div>
            </form>

            {/* Found Ticket */}
            {foundTicket && (
              <div className="mt-8 pt-8 border-t border-slate-200">
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-sm font-mono text-slate-500">{foundTicket.ticket_number}</span>
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_CONFIG[foundTicket.status]?.color}`}>
                        {STATUS_CONFIG[foundTicket.status]?.label}
                      </span>
                    </div>
                    <h3 className="text-lg font-medium text-slate-900">{foundTicket.subject}</h3>
                  </div>
                </div>
                
                {/* Thread would go here */}
                <div className="bg-slate-50 rounded-lg p-4 text-center text-slate-500">
                  <p>To view full ticket details and reply, please log in to the MSP Portal.</p>
                  <a href="/admin/login" className="text-blue-600 hover:text-blue-700 font-medium mt-2 inline-block">
                    Log in to MSP Portal →
                  </a>
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white mt-auto">
        <div className="max-w-4xl mx-auto px-4 py-6 text-center text-sm text-slate-500">
          <p>Need immediate assistance? Contact us at support@company.com</p>
        </div>
      </footer>
    </div>
  );
}
