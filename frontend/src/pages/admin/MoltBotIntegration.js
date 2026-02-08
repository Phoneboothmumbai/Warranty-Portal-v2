import React, { useState, useEffect, useCallback } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { 
  MessageSquare, Settings, Zap, Phone, Globe, Shield, 
  ToggleLeft, ToggleRight, Copy, RefreshCw, ExternalLink,
  CheckCircle2, XCircle, AlertCircle, Bot, Send, BookOpen, FileText, Lock
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Switch } from '../../components/ui/switch';
import { Badge } from '../../components/ui/badge';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';

const API_URL = process.env.REACT_APP_BACKEND_URL;

export default function MoltBotIntegration() {
  const token = localStorage.getItem('admin_token');
  const headers = { Authorization: `Bearer ${token}` };
  
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [config, setConfig] = useState({
    enabled: false,
    api_key: '',
    webhook_secret: '',
    auto_create_tickets: true,
    default_priority: 'medium',
    default_help_topic_id: '',
    greeting_message: '',
    notification_channels: ['webhook'],
    // Bot Configuration
    bot_instructions: '',
    knowledge_base: '',
    restrict_to_support_only: true,
    restrict_to_employees: false,
    allowed_topics: ['warranty', 'service', 'repair', 'support', 'device', 'amc'],
    off_topic_response: ''
  });
  const [orgInfo, setOrgInfo] = useState(null);
  const [helpTopics, setHelpTopics] = useState([]);
  const [events, setEvents] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [activeTab, setActiveTab] = useState('settings');
  const [testMessage, setTestMessage] = useState('');
  const [testPhone, setTestPhone] = useState('');

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [configRes, topicsRes, orgRes] = await Promise.all([
        axios.get(`${API_URL}/api/admin/moltbot/config`, { headers }).catch(() => ({ data: {} })),
        axios.get(`${API_URL}/api/admin/ticketing-config/help-topics`, { headers }).catch(() => ({ data: { topics: [] } })),
        axios.get(`${API_URL}/api/auth/me`, { headers }).catch(() => ({ data: {} }))
      ]);
      
      if (configRes.data.configured) {
        setConfig(prev => ({ ...prev, ...configRes.data }));
      }
      setHelpTopics(topicsRes.data.topics || []);
      setOrgInfo(orgRes.data);
      
      // Fetch events and conversations if enabled
      if (configRes.data.enabled) {
        const [eventsRes, convsRes] = await Promise.all([
          axios.get(`${API_URL}/api/admin/moltbot/events?limit=20`, { headers }).catch(() => ({ data: { events: [] } })),
          axios.get(`${API_URL}/api/admin/moltbot/conversations?limit=20`, { headers }).catch(() => ({ data: { conversations: [] } }))
        ]);
        setEvents(eventsRes.data.events || []);
        setConversations(convsRes.data.conversations || []);
      }
    } catch (error) {
      console.error('Failed to fetch MoltBot config:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const saveConfig = async () => {
    setSaving(true);
    try {
      await axios.post(`${API_URL}/api/admin/moltbot/config`, {
        ...config,
        api_key: config.api_key || '****' // Don't send empty if not changed
      }, { headers });
      toast.success('MoltBot configuration saved');
      fetchData();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save configuration');
    } finally {
      setSaving(false);
    }
  };

  const copyWebhookUrl = () => {
    const webhookUrl = `https://aftersales.support/api/admin/moltbot/webhook/${orgInfo?.organization_id || 'YOUR_ORG_ID'}`;
    navigator.clipboard.writeText(webhookUrl);
    toast.success('Webhook URL copied to clipboard');
  };

  const sendTestMessage = async () => {
    if (!testPhone || !testMessage) {
      toast.error('Please enter phone number and message');
      return;
    }
    try {
      await axios.post(`${API_URL}/api/admin/moltbot/send-message`, {
        recipient_phone: testPhone,
        message: testMessage,
        channel: 'whatsapp'
      }, { headers });
      toast.success('Test message sent');
      setTestMessage('');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send message');
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="h-8 w-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 flex items-center gap-3">
            <Bot className="h-7 w-7 text-green-500" />
            MoltBot Integration
          </h1>
          <p className="text-slate-500 mt-1">
            Connect WhatsApp & Telegram for automated customer support
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-600">Integration Status:</span>
            {config.enabled ? (
              <Badge className="bg-green-500">
                <CheckCircle2 className="h-3 w-3 mr-1" />
                Active
              </Badge>
            ) : (
              <Badge variant="outline" className="text-slate-500">
                <XCircle className="h-3 w-3 mr-1" />
                Disabled
              </Badge>
            )}
          </div>
        </div>
      </div>

      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="settings" className="flex items-center gap-2">
            <Settings className="h-4 w-4" />
            Settings
          </TabsTrigger>
          <TabsTrigger value="bot-config" className="flex items-center gap-2">
            <Bot className="h-4 w-4" />
            Bot Config
          </TabsTrigger>
          <TabsTrigger value="webhook" className="flex items-center gap-2">
            <Zap className="h-4 w-4" />
            Webhook
          </TabsTrigger>
          <TabsTrigger value="messages" className="flex items-center gap-2">
            <MessageSquare className="h-4 w-4" />
            Messages
          </TabsTrigger>
          <TabsTrigger value="test" className="flex items-center gap-2">
            <Send className="h-4 w-4" />
            Test
          </TabsTrigger>
        </TabsList>

        {/* Settings Tab */}
        <TabsContent value="settings" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <ToggleRight className="h-5 w-5" />
                Enable MoltBot
              </CardTitle>
              <CardDescription>
                Turn on to start receiving messages from WhatsApp/Telegram
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div>
                  <p className="font-medium">MoltBot Integration</p>
                  <p className="text-sm text-slate-500">
                    {config.enabled ? 'Customers can reach you via WhatsApp & Telegram' : 'Enable to start receiving messages'}
                  </p>
                </div>
                <Switch
                  checked={config.enabled}
                  onCheckedChange={(v) => setConfig({ ...config, enabled: v })}
                />
              </div>
            </CardContent>
          </Card>

          {config.enabled && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    API Configuration
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <Label>MoltBot API Key</Label>
                    <Input
                      type="password"
                      value={config.api_key}
                      onChange={(e) => setConfig({ ...config, api_key: e.target.value })}
                      placeholder="Enter your MoltBot API key"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Get this from your MoltBot dashboard: <code>moltbot config get api.key</code>
                    </p>
                  </div>
                  <div>
                    <Label>Webhook Secret (Optional)</Label>
                    <Input
                      value={config.webhook_secret}
                      onChange={(e) => setConfig({ ...config, webhook_secret: e.target.value })}
                      placeholder="Optional security key"
                    />
                    <p className="text-xs text-slate-500 mt-1">
                      Add extra security by verifying webhook requests
                    </p>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <MessageSquare className="h-5 w-5" />
                    Ticket Settings
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Smart Ticket Creation</Label>
                      <p className="text-sm text-slate-500">Ask customer before creating ticket</p>
                    </div>
                    <Switch
                      checked={config.auto_create_tickets}
                      onCheckedChange={(v) => setConfig({ ...config, auto_create_tickets: v })}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label>Default Priority</Label>
                      <Select
                        value={config.default_priority}
                        onValueChange={(v) => setConfig({ ...config, default_priority: v })}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="low">Low</SelectItem>
                          <SelectItem value="medium">Medium</SelectItem>
                          <SelectItem value="high">High</SelectItem>
                          <SelectItem value="critical">Critical</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div>
                      <Label>Default Help Topic</Label>
                      <Select
                        value={config.default_help_topic_id || 'none'}
                        onValueChange={(v) => setConfig({ ...config, default_help_topic_id: v === 'none' ? '' : v })}
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select topic" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="none">No default</SelectItem>
                          {helpTopics.map((topic) => (
                            <SelectItem key={topic.id} value={topic.id}>{topic.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                  <div>
                    <Label>Custom Greeting Message (Optional)</Label>
                    <Textarea
                      value={config.greeting_message || ''}
                      onChange={(e) => setConfig({ ...config, greeting_message: e.target.value })}
                      placeholder="Leave empty to use default greeting"
                      rows={3}
                    />
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          <div className="flex justify-end">
            <Button onClick={saveConfig} disabled={saving}>
              {saving ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : null}
              Save Configuration
            </Button>
          </div>
        </TabsContent>

        {/* Bot Configuration Tab */}
        <TabsContent value="bot-config" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Lock className="h-5 w-5" />
                Access Control
              </CardTitle>
              <CardDescription>
                Control who can interact with the bot and what topics it handles
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div>
                  <Label className="font-medium">Restrict to Support Queries Only</Label>
                  <p className="text-sm text-slate-500">
                    Bot will only respond to warranty, service, repair, and device-related questions
                  </p>
                </div>
                <Switch
                  checked={config.restrict_to_support_only}
                  onCheckedChange={(v) => setConfig({ ...config, restrict_to_support_only: v })}
                />
              </div>
              
              <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
                <div>
                  <Label className="font-medium">Restrict to Registered Employees</Label>
                  <p className="text-sm text-slate-500">
                    Only allow users whose phone numbers are registered as company employees
                  </p>
                </div>
                <Switch
                  checked={config.restrict_to_employees}
                  onCheckedChange={(v) => setConfig({ ...config, restrict_to_employees: v })}
                />
              </div>

              <div>
                <Label>Allowed Topics (comma-separated)</Label>
                <Input
                  value={config.allowed_topics?.join(', ') || ''}
                  onChange={(e) => setConfig({ 
                    ...config, 
                    allowed_topics: e.target.value.split(',').map(t => t.trim().toLowerCase()).filter(Boolean)
                  })}
                  placeholder="warranty, service, repair, support, device, amc"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Topics the bot is allowed to discuss when restriction is enabled
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Bot Instructions & Guidelines
              </CardTitle>
              <CardDescription>
                Define how the bot should behave and respond to customers
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Custom Instructions</Label>
                <Textarea
                  value={config.bot_instructions || ''}
                  onChange={(e) => setConfig({ ...config, bot_instructions: e.target.value })}
                  placeholder={`Example instructions:
- Always greet the customer politely
- Ask for device serial number before troubleshooting
- If issue cannot be resolved, offer to create a support ticket
- Never discuss pricing without manager approval
- Escalate urgent issues immediately`}
                  rows={8}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-slate-500 mt-1">
                  These instructions guide how the bot interacts with customers
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BookOpen className="h-5 w-5" />
                Knowledge Base
              </CardTitle>
              <CardDescription>
                Add product information, FAQs, and troubleshooting guides for the bot to reference
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Knowledge Base Content</Label>
                <Textarea
                  value={config.knowledge_base || ''}
                  onChange={(e) => setConfig({ ...config, knowledge_base: e.target.value })}
                  placeholder={`Example knowledge base:

## Products We Support
- Dell Laptops (Latitude, Inspiron, XPS series)
- HP Printers (LaserJet, OfficeJet series)
- Lenovo Desktops (ThinkCentre series)

## Common Issues & Solutions

### Laptop won't start
1. Check if charger is connected and LED is on
2. Try holding power button for 15 seconds
3. Remove battery (if removable) and try again
4. If still not working, create a support ticket

### Printer not printing
1. Check paper tray and ink/toner levels
2. Run printer self-test
3. Reinstall printer drivers
4. If issue persists, schedule a service visit

## Warranty Information
- Standard warranty: 1 year from purchase
- Extended warranty available: Up to 3 years
- AMC contracts available for out-of-warranty devices

## Contact Information
- Support Hours: Mon-Sat 9 AM - 6 PM
- Emergency Support: Available for AMC customers`}
                  rows={15}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-slate-500 mt-1">
                  The bot will use this information to answer customer queries. Use Markdown formatting.
                </p>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                Out-of-Scope Response
              </CardTitle>
              <CardDescription>
                How the bot should respond to off-topic queries
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div>
                <Label>Response for Off-Topic Queries</Label>
                <Textarea
                  value={config.off_topic_response || ''}
                  onChange={(e) => setConfig({ ...config, off_topic_response: e.target.value })}
                  placeholder="I'm sorry, I can only help with warranty, service, and device-related questions. For other queries, please contact our main office."
                  rows={3}
                />
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-end">
            <Button onClick={saveConfig} disabled={saving}>
              {saving ? <RefreshCw className="h-4 w-4 mr-2 animate-spin" /> : null}
              Save Bot Configuration
            </Button>
          </div>
        </TabsContent>

        {/* Webhook Tab */}
        <TabsContent value="webhook" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Globe className="h-5 w-5" />
                Webhook Configuration
              </CardTitle>
              <CardDescription>
                Configure MoltBot to send messages to your portal
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <Label>Your Webhook URL</Label>
                <div className="flex gap-2 mt-1">
                  <Input
                    readOnly
                    value={`https://aftersales.support/api/admin/moltbot/webhook/${orgInfo?.organization_id || 'YOUR_ORG_ID'}`}
                    className="font-mono text-sm"
                  />
                  <Button variant="outline" onClick={copyWebhookUrl}>
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
                <p className="text-xs text-slate-500 mt-1">
                  Configure this URL in your MoltBot settings
                </p>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900 mb-2">Setup Instructions</h4>
                <ol className="text-sm text-blue-800 space-y-2 list-decimal list-inside">
                  <li>SSH into your MoltBot server: <code className="bg-blue-100 px-1 rounded">ssh root@65.20.79.16</code></li>
                  <li>Set webhook URL: <code className="bg-blue-100 px-1 rounded">moltbot config set webhook.url "YOUR_WEBHOOK_URL"</code></li>
                  <li>Set webhook secret (optional): <code className="bg-blue-100 px-1 rounded">moltbot config set webhook.secret "YOUR_SECRET"</code></li>
                  <li>Restart MoltBot: <code className="bg-blue-100 px-1 rounded">sudo systemctl restart moltbot</code></li>
                </ol>
              </div>

              <div className="flex items-center gap-2">
                <a 
                  href="https://molt-bot.live/docs/webhooks" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline text-sm flex items-center gap-1"
                >
                  View MoltBot Documentation
                  <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Recent Webhook Events</CardTitle>
            </CardHeader>
            <CardContent>
              {events.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <Zap className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No webhook events yet</p>
                  <p className="text-sm">Events will appear here once MoltBot sends messages</p>
                </div>
              ) : (
                <div className="space-y-2 max-h-96 overflow-y-auto">
                  {events.map((event) => (
                    <div key={event.id} className="flex items-center gap-3 p-3 border rounded-lg">
                      {event.processed ? (
                        <CheckCircle2 className="h-5 w-5 text-green-500 flex-shrink-0" />
                      ) : event.error ? (
                        <XCircle className="h-5 w-5 text-red-500 flex-shrink-0" />
                      ) : (
                        <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0" />
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium truncate">{event.event_type}</p>
                        <p className="text-xs text-slate-500">
                          {new Date(event.received_at).toLocaleString()}
                        </p>
                      </div>
                      {event.ticket_number && (
                        <Badge variant="outline">{event.ticket_number}</Badge>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Messages Tab */}
        <TabsContent value="messages" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Active Conversations</CardTitle>
              <CardDescription>Recent customer conversations via MoltBot</CardDescription>
            </CardHeader>
            <CardContent>
              {conversations.length === 0 ? (
                <div className="text-center py-8 text-slate-500">
                  <MessageSquare className="h-12 w-12 mx-auto mb-3 text-slate-300" />
                  <p>No conversations yet</p>
                  <p className="text-sm">Conversations will appear here when customers message you</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {conversations.map((conv) => (
                    <div key={conv.id} className="p-4 border rounded-lg hover:bg-slate-50">
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <Phone className="h-4 w-4 text-green-500" />
                          <span className="font-medium">{conv.sender_name || conv.sender_phone || 'Unknown'}</span>
                        </div>
                        <Badge variant="outline" className="capitalize">{conv.state}</Badge>
                      </div>
                      <div className="text-sm text-slate-500">
                        <span>{conv.sender_phone}</span>
                        {conv.ticket_number && (
                          <span className="ml-2">• Ticket: {conv.ticket_number}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Test Tab */}
        <TabsContent value="test" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Send className="h-5 w-5" />
                Send Test Message
              </CardTitle>
              <CardDescription>
                Test your MoltBot integration by sending a message
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {!config.enabled ? (
                <div className="p-4 bg-yellow-50 text-yellow-800 rounded-lg">
                  <AlertCircle className="h-5 w-5 inline mr-2" />
                  Enable MoltBot integration first to send test messages
                </div>
              ) : (
                <>
                  <div>
                    <Label>Phone Number (with country code)</Label>
                    <Input
                      value={testPhone}
                      onChange={(e) => setTestPhone(e.target.value)}
                      placeholder="+91XXXXXXXXXX"
                    />
                  </div>
                  <div>
                    <Label>Message</Label>
                    <Textarea
                      value={testMessage}
                      onChange={(e) => setTestMessage(e.target.value)}
                      placeholder="Enter test message..."
                      rows={3}
                    />
                  </div>
                  <Button onClick={sendTestMessage}>
                    <Send className="h-4 w-4 mr-2" />
                    Send Test Message
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
