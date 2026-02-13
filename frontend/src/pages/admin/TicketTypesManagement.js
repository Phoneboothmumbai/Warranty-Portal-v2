import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from '../../components/ui/dialog';
import { Label } from '../../components/ui/label';
import { Textarea } from '../../components/ui/textarea';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Switch } from '../../components/ui/switch';
import { toast } from 'sonner';
import axios from 'axios';
import {
  Ticket, Plus, Search, Settings, Wrench, TrendingUp, ShoppingCart, 
  HelpCircle, MessageSquare, RotateCcw, Phone, Handshake, AlertTriangle,
  PackagePlus, GraduationCap, RefreshCw, Receipt, Settings2, MapPin,
  PlayCircle, UserPlus, ChevronRight, Edit, Trash2, Eye, Workflow,
  FileText, CheckCircle, XCircle, Clock, ArrowRight, Loader2, Filter,
  Download, Upload
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

const CATEGORY_CONFIG = {
  support: { name: 'Support', icon: Wrench, color: 'bg-red-500' },
  sales: { name: 'Sales', icon: TrendingUp, color: 'bg-emerald-500' },
  operations: { name: 'Operations', icon: Settings, color: 'bg-amber-500' },
  finance: { name: 'Finance', icon: Receipt, color: 'bg-purple-500' },
  hr: { name: 'HR', icon: UserPlus, color: 'bg-pink-500' },
  general: { name: 'General', icon: HelpCircle, color: 'bg-blue-500' }
};

const ICON_MAP = {
  'wrench': Wrench,
  'trending-up': TrendingUp,
  'file-text': FileText,
  'shopping-cart': ShoppingCart,
  'help-circle': HelpCircle,
  'message-square': MessageSquare,
  'rotate-ccw': RotateCcw,
  'phone-callback': Phone,
  'handshake': Handshake,
  'alert-triangle': AlertTriangle,
  'package-plus': PackagePlus,
  'graduation-cap': GraduationCap,
  'refresh-cw': RefreshCw,
  'receipt': Receipt,
  'settings': Settings2,
  'map-pin': MapPin,
  'play-circle': PlayCircle,
  'user-plus': UserPlus,
  'ticket': Ticket
};

export default function TicketTypesManagement() {
  const [ticketTypes, setTicketTypes] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedType, setSelectedType] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [seeding, setSeeding] = useState(false);
  
  const token = localStorage.getItem('token');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchTicketTypes();
  }, []);

  const fetchTicketTypes = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`${API}/api/admin/ticket-types?include_inactive=true`, { headers });
      setTicketTypes(response.data);
    } catch (error) {
      console.error('Failed to fetch ticket types:', error);
      toast.error('Failed to load ticket types');
    } finally {
      setLoading(false);
    }
  };

  const handleSeedDefaults = async () => {
    setSeeding(true);
    try {
      const response = await axios.post(`${API}/api/admin/ticket-types/seed`, {}, { headers });
      toast.success(response.data.message);
      fetchTicketTypes();
    } catch (error) {
      toast.error('Failed to seed ticket types');
    } finally {
      setSeeding(false);
    }
  };

  const handleToggleActive = async (typeId, currentStatus) => {
    try {
      await axios.put(`${API}/api/admin/ticket-types/${typeId}`, 
        { is_active: !currentStatus }, 
        { headers }
      );
      toast.success(`Ticket type ${!currentStatus ? 'activated' : 'deactivated'}`);
      fetchTicketTypes();
    } catch (error) {
      toast.error('Failed to update ticket type');
    }
  };

  const handleDeleteType = async (typeId) => {
    if (!window.confirm('Are you sure you want to delete this ticket type?')) return;
    
    try {
      await axios.delete(`${API}/api/admin/ticket-types/${typeId}`, { headers });
      toast.success('Ticket type deleted');
      fetchTicketTypes();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete ticket type');
    }
  };

  const filteredTypes = ticketTypes.filter(type => {
    const matchesSearch = type.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
                         type.slug.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesCategory = selectedCategory === 'all' || type.category === selectedCategory;
    return matchesSearch && matchesCategory;
  });

  const groupedTypes = filteredTypes.reduce((acc, type) => {
    const category = type.category || 'general';
    if (!acc[category]) acc[category] = [];
    acc[category].push(type);
    return acc;
  }, {});

  const getIcon = (iconName) => {
    const IconComponent = ICON_MAP[iconName] || Ticket;
    return IconComponent;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="ticket-types-management">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Ticket Types & Workflows</h1>
          <p className="text-slate-600">Manage different types of tickets and their workflows</p>
        </div>
        <div className="flex items-center gap-2">
          {ticketTypes.length === 0 && (
            <Button 
              onClick={handleSeedDefaults}
              disabled={seeding}
              className="bg-emerald-600 hover:bg-emerald-700"
              data-testid="seed-defaults-btn"
            >
              {seeding ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
              Load Default Types
            </Button>
          )}
          <Button 
            onClick={() => setShowCreateModal(true)}
            className="bg-blue-600 hover:bg-blue-700"
            data-testid="create-type-btn"
          >
            <Plus className="w-4 h-4 mr-2" />
            New Ticket Type
          </Button>
        </div>
      </div>

      {/* Stats Row */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-4">
            <div className="text-3xl font-bold text-blue-700">{ticketTypes.length}</div>
            <div className="text-sm text-blue-600">Total Types</div>
          </CardContent>
        </Card>
        {Object.entries(CATEGORY_CONFIG).map(([key, config]) => {
          const count = ticketTypes.filter(t => t.category === key).length;
          const IconComp = config.icon;
          return (
            <Card key={key} className="bg-white border-slate-200 hover:shadow-md transition-shadow cursor-pointer"
                  onClick={() => setSelectedCategory(selectedCategory === key ? 'all' : key)}>
              <CardContent className="p-4">
                <div className="flex items-center gap-2">
                  <div className={`w-8 h-8 rounded-lg ${config.color} flex items-center justify-center`}>
                    <IconComp className="w-4 h-4 text-white" />
                  </div>
                  <div>
                    <div className="text-xl font-bold text-slate-900">{count}</div>
                    <div className="text-xs text-slate-600">{config.name}</div>
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input
                placeholder="Search ticket types..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-9"
                data-testid="search-input"
              />
            </div>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger className="w-full sm:w-48" data-testid="category-filter">
                <Filter className="w-4 h-4 mr-2" />
                <SelectValue placeholder="All Categories" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                {Object.entries(CATEGORY_CONFIG).map(([key, config]) => (
                  <SelectItem key={key} value={key}>{config.name}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Ticket Types Grid */}
      {Object.entries(groupedTypes).length === 0 ? (
        <Card>
          <CardContent className="p-12 text-center">
            <Ticket className="w-12 h-12 mx-auto text-slate-300 mb-4" />
            <h3 className="text-lg font-medium text-slate-900 mb-2">No Ticket Types Found</h3>
            <p className="text-slate-600 mb-4">
              {ticketTypes.length === 0 
                ? "Get started by loading default ticket types or create your own."
                : "No ticket types match your search criteria."}
            </p>
            {ticketTypes.length === 0 && (
              <Button onClick={handleSeedDefaults} disabled={seeding}>
                {seeding ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
                Load Default Types
              </Button>
            )}
          </CardContent>
        </Card>
      ) : (
        Object.entries(groupedTypes).map(([category, types]) => {
          const categoryConfig = CATEGORY_CONFIG[category] || CATEGORY_CONFIG.general;
          const CategoryIcon = categoryConfig.icon;
          
          return (
            <div key={category} className="space-y-3">
              <div className="flex items-center gap-2">
                <div className={`w-6 h-6 rounded ${categoryConfig.color} flex items-center justify-center`}>
                  <CategoryIcon className="w-3.5 h-3.5 text-white" />
                </div>
                <h2 className="text-lg font-semibold text-slate-900">{categoryConfig.name}</h2>
                <Badge variant="outline" className="ml-2">{types.length}</Badge>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {types.map((type) => {
                  const TypeIcon = getIcon(type.icon);
                  return (
                    <Card 
                      key={type.id} 
                      className={`hover:shadow-md transition-all cursor-pointer ${!type.is_active ? 'opacity-60' : ''}`}
                      onClick={() => { setSelectedType(type); setShowDetailModal(true); }}
                      data-testid={`ticket-type-${type.slug}`}
                    >
                      <CardContent className="p-4">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div 
                              className="w-10 h-10 rounded-lg flex items-center justify-center"
                              style={{ backgroundColor: `${type.color}20`, color: type.color }}
                            >
                              <TypeIcon className="w-5 h-5" />
                            </div>
                            <div>
                              <h3 className="font-semibold text-slate-900">{type.name}</h3>
                              <p className="text-xs text-slate-500 font-mono">{type.slug}</p>
                            </div>
                          </div>
                          <div className="flex items-center gap-1">
                            {type.is_system && (
                              <Badge variant="outline" className="text-xs bg-slate-100">System</Badge>
                            )}
                            {!type.is_active && (
                              <Badge variant="outline" className="text-xs bg-red-50 text-red-600">Inactive</Badge>
                            )}
                          </div>
                        </div>
                        
                        {type.description && (
                          <p className="text-sm text-slate-600 mb-3 line-clamp-2">{type.description}</p>
                        )}
                        
                        <div className="flex items-center justify-between text-xs">
                          <div className="flex items-center gap-3 text-slate-500">
                            <span className="flex items-center gap-1">
                              <Workflow className="w-3.5 h-3.5" />
                              {type.workflow_statuses?.length || 0} statuses
                            </span>
                            <span className="flex items-center gap-1">
                              <FileText className="w-3.5 h-3.5" />
                              {type.custom_fields?.length || 0} fields
                            </span>
                          </div>
                          <div className="flex items-center gap-1 text-slate-500">
                            <Ticket className="w-3.5 h-3.5" />
                            {type.ticket_count || 0}
                          </div>
                        </div>
                        
                        {/* Workflow Preview */}
                        {type.workflow_statuses && type.workflow_statuses.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-slate-100">
                            <div className="flex items-center gap-1 overflow-x-auto pb-1">
                              {type.workflow_statuses.slice(0, 5).map((status, idx) => (
                                <div key={status.id} className="flex items-center">
                                  <span 
                                    className="px-2 py-0.5 rounded text-xs font-medium whitespace-nowrap"
                                    style={{ backgroundColor: `${status.color}20`, color: status.color }}
                                  >
                                    {status.name}
                                  </span>
                                  {idx < Math.min(type.workflow_statuses.length - 1, 4) && (
                                    <ArrowRight className="w-3 h-3 text-slate-300 mx-0.5 flex-shrink-0" />
                                  )}
                                </div>
                              ))}
                              {type.workflow_statuses.length > 5 && (
                                <span className="text-xs text-slate-400 ml-1">+{type.workflow_statuses.length - 5}</span>
                              )}
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          );
        })
      )}

      {/* Detail Modal */}
      <Dialog open={showDetailModal} onOpenChange={setShowDetailModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {selectedType && (
            <>
              <DialogHeader>
                <div className="flex items-center gap-3">
                  <div 
                    className="w-12 h-12 rounded-lg flex items-center justify-center"
                    style={{ backgroundColor: `${selectedType.color}20`, color: selectedType.color }}
                  >
                    {(() => { const Icon = getIcon(selectedType.icon); return <Icon className="w-6 h-6" />; })()}
                  </div>
                  <div>
                    <DialogTitle className="text-xl">{selectedType.name}</DialogTitle>
                    <p className="text-sm text-slate-500 font-mono">{selectedType.slug}</p>
                  </div>
                </div>
              </DialogHeader>
              
              <Tabs defaultValue="workflow" className="mt-4">
                <TabsList className="grid grid-cols-3 w-full">
                  <TabsTrigger value="workflow">Workflow</TabsTrigger>
                  <TabsTrigger value="fields">Custom Fields</TabsTrigger>
                  <TabsTrigger value="settings">Settings</TabsTrigger>
                </TabsList>
                
                <TabsContent value="workflow" className="mt-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-900">Workflow Statuses</h3>
                    <Badge>{selectedType.workflow_statuses?.length || 0} statuses</Badge>
                  </div>
                  
                  <div className="space-y-2">
                    {selectedType.workflow_statuses?.map((status, idx) => (
                      <div 
                        key={status.id}
                        className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg"
                      >
                        <div className="w-6 h-6 rounded-full bg-slate-200 flex items-center justify-center text-xs font-medium">
                          {idx + 1}
                        </div>
                        <div 
                          className="px-3 py-1 rounded-full text-sm font-medium"
                          style={{ backgroundColor: `${status.color}20`, color: status.color }}
                        >
                          {status.name}
                        </div>
                        <div className="flex-1 flex items-center gap-2">
                          {status.is_initial && (
                            <Badge variant="outline" className="text-xs bg-green-50 text-green-600">Initial</Badge>
                          )}
                          {status.is_terminal && (
                            <Badge variant="outline" className="text-xs bg-slate-100">Terminal</Badge>
                          )}
                          {status.is_success && (
                            <Badge variant="outline" className="text-xs bg-emerald-50 text-emerald-600">Success</Badge>
                          )}
                          {status.is_failure && (
                            <Badge variant="outline" className="text-xs bg-red-50 text-red-600">Failure</Badge>
                          )}
                        </div>
                        {status.can_transition_to?.length > 0 && (
                          <div className="text-xs text-slate-500">
                            → {status.can_transition_to.join(', ')}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </TabsContent>
                
                <TabsContent value="fields" className="mt-4 space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-slate-900">Custom Fields</h3>
                    <Badge>{selectedType.custom_fields?.length || 0} fields</Badge>
                  </div>
                  
                  {selectedType.custom_fields?.length === 0 ? (
                    <div className="text-center py-8 text-slate-500">
                      <FileText className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                      <p>No custom fields defined</p>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      {selectedType.custom_fields?.map((field) => (
                        <div 
                          key={field.id}
                          className="flex items-center justify-between p-3 bg-slate-50 rounded-lg"
                        >
                          <div className="flex items-center gap-3">
                            <div className="font-medium text-slate-900">{field.name}</div>
                            <Badge variant="outline" className="text-xs">{field.field_type}</Badge>
                            {field.required && (
                              <Badge variant="outline" className="text-xs bg-red-50 text-red-600">Required</Badge>
                            )}
                          </div>
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            {field.show_in_list && <span>📋 List</span>}
                            {field.show_in_create && <span>➕ Create</span>}
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </TabsContent>
                
                <TabsContent value="settings" className="mt-4 space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                      <Label className="text-slate-500 text-xs">Category</Label>
                      <div className="font-medium">{CATEGORY_CONFIG[selectedType.category]?.name || selectedType.category}</div>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-slate-500 text-xs">Default Priority</Label>
                      <div className="font-medium capitalize">{selectedType.default_priority}</div>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-slate-500 text-xs">Requires Device</Label>
                      <div className="font-medium">{selectedType.requires_device ? 'Yes' : 'No'}</div>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-slate-500 text-xs">Requires Company</Label>
                      <div className="font-medium">{selectedType.requires_company ? 'Yes' : 'No'}</div>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-slate-500 text-xs">Customer Portal</Label>
                      <div className="font-medium">{selectedType.enable_customer_portal ? 'Enabled' : 'Disabled'}</div>
                    </div>
                    <div className="space-y-1">
                      <Label className="text-slate-500 text-xs">Job Lifecycle</Label>
                      <div className="font-medium">{selectedType.requires_job_lifecycle ? 'Required' : 'Not Required'}</div>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Switch 
                        checked={selectedType.is_active}
                        onCheckedChange={() => handleToggleActive(selectedType.id, selectedType.is_active)}
                        disabled={selectedType.is_system}
                      />
                      <Label>Active</Label>
                    </div>
                    {!selectedType.is_system && (
                      <Button 
                        variant="destructive" 
                        size="sm"
                        onClick={() => { handleDeleteType(selectedType.id); setShowDetailModal(false); }}
                      >
                        <Trash2 className="w-4 h-4 mr-1" />
                        Delete
                      </Button>
                    )}
                  </div>
                </TabsContent>
              </Tabs>
            </>
          )}
        </DialogContent>
      </Dialog>

      {/* Create Modal - Simplified for now */}
      <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Ticket Type</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Name</Label>
              <Input placeholder="e.g., Equipment Rental" data-testid="new-type-name" />
            </div>
            <div className="space-y-2">
              <Label>Category</Label>
              <Select defaultValue="general">
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CATEGORY_CONFIG).map(([key, config]) => (
                    <SelectItem key={key} value={key}>{config.name}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-2">
              <Label>Description</Label>
              <Textarea placeholder="Brief description of this ticket type..." />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateModal(false)}>Cancel</Button>
            <Button className="bg-blue-600 hover:bg-blue-700">Create Type</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
