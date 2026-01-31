import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import { Switch } from '../../components/ui/switch';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Separator } from '../../components/ui/separator';
import { 
  Dialog, DialogContent, DialogDescription, DialogFooter, 
  DialogHeader, DialogTitle 
} from '../../components/ui/dialog';
import { 
  Select, SelectContent, SelectItem, SelectTrigger, SelectValue 
} from '../../components/ui/select';
import { toast } from 'sonner';
import { 
  CreditCard, Plus, Edit2, Trash2, GripVertical, Users, 
  Check, X, Eye, EyeOff, Star, RefreshCw, AlertTriangle,
  Sparkles, Shield, Zap, Building2, Package
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL;

// Format price for display
const formatPrice = (paise, currency = 'INR') => {
  if (paise === 0) return 'Free';
  if (paise < 0) return 'Custom';
  const amount = paise / 100;
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency: currency,
    minimumFractionDigits: 0
  }).format(amount);
};

export default function PlatformPlans() {
  const [plans, setPlans] = useState([]);
  const [metadata, setMetadata] = useState({ features: {}, limits: {} });
  const [loading, setLoading] = useState(true);
  const [showEditor, setShowEditor] = useState(false);
  const [editingPlan, setEditingPlan] = useState(null);
  const [saving, setSaving] = useState(false);
  const [activeTab, setActiveTab] = useState('basic');

  const token = localStorage.getItem('platformToken');
  const headers = { Authorization: `Bearer ${token}` };

  useEffect(() => {
    fetchPlans();
    fetchMetadata();
  }, []);

  const fetchPlans = async () => {
    try {
      const response = await axios.get(`${API}/api/platform/plans`, { headers });
      setPlans(response.data || []);
    } catch (error) {
      console.error('Failed to fetch plans:', error);
      toast.error('Failed to load plans');
    } finally {
      setLoading(false);
    }
  };

  const fetchMetadata = async () => {
    try {
      const response = await axios.get(`${API}/api/platform/plans/metadata`, { headers });
      setMetadata(response.data || { features: {}, limits: {} });
    } catch (error) {
      console.error('Failed to fetch metadata');
    }
  };

  const handleCreatePlan = () => {
    setEditingPlan({
      name: '',
      slug: '',
      tagline: '',
      description: '',
      price_monthly: 0,
      price_yearly: 0,
      currency: 'INR',
      display_order: plans.length,
      is_popular: false,
      is_public: true,
      color: '#6366f1',
      status: 'draft',
      features: {},
      limits: {
        max_companies: 5,
        max_devices: 100,
        max_users: 10,
        max_tickets_per_month: 500,
        max_storage_gb: 5,
        max_email_templates: 10,
        max_custom_fields: 20,
        max_departments: 3,
        max_sla_policies: 3,
        max_canned_responses: 25,
        max_knowledge_articles: 50
      },
      support_level: 'email',
      response_time_hours: 24,
      is_trial: false,
      trial_days: 0
    });
    setShowEditor(true);
    setActiveTab('basic');
  };

  const handleEditPlan = (plan) => {
    setEditingPlan({ ...plan });
    setShowEditor(true);
    setActiveTab('basic');
  };

  const handleSavePlan = async () => {
    if (!editingPlan.name || !editingPlan.slug) {
      toast.error('Name and slug are required');
      return;
    }

    setSaving(true);
    try {
      if (editingPlan.id) {
        await axios.put(`${API}/api/platform/plans/${editingPlan.id}`, editingPlan, { headers });
        toast.success('Plan updated successfully');
      } else {
        await axios.post(`${API}/api/platform/plans`, editingPlan, { headers });
        toast.success('Plan created successfully');
      }
      setShowEditor(false);
      setEditingPlan(null);
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to save plan');
    } finally {
      setSaving(false);
    }
  };

  const handleDeletePlan = async (plan) => {
    if (plan.used_by_count > 0) {
      toast.error(`Cannot delete. ${plan.used_by_count} customers are using this plan.`);
      return;
    }

    if (!confirm(`Delete "${plan.name}"? This cannot be undone.`)) return;

    try {
      await axios.delete(`${API}/api/platform/plans/${plan.id}`, { headers });
      toast.success('Plan deleted');
      fetchPlans();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to delete plan');
    }
  };

  const handleSeedPlans = async () => {
    try {
      const response = await axios.post(`${API}/api/platform/plans/seed`, {}, { headers });
      toast.success(response.data.message);
      fetchPlans();
    } catch (error) {
      toast.error('Failed to seed plans');
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      active: 'bg-green-100 text-green-800',
      draft: 'bg-amber-100 text-amber-800',
      archived: 'bg-slate-100 text-slate-800'
    };
    return <Badge className={styles[status] || styles.draft}>{status}</Badge>;
  };

  const updateFeature = (key, value) => {
    setEditingPlan(prev => ({
      ...prev,
      features: { ...prev.features, [key]: value }
    }));
  };

  const updateLimit = (key, value) => {
    setEditingPlan(prev => ({
      ...prev,
      limits: { ...prev.limits, [key]: parseInt(value) || 0 }
    }));
  };

  // Group features by category
  const groupedFeatures = Object.entries(metadata.features).reduce((acc, [key, meta]) => {
    const category = meta.category || 'Other';
    if (!acc[category]) acc[category] = [];
    acc[category].push({ key, ...meta });
    return acc;
  }, {});

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <RefreshCw className="w-6 h-6 animate-spin text-slate-400" />
      </div>
    );
  }

  return (
    <div className="space-y-6" data-testid="platform-plans-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Subscription Plans</h1>
          <p className="text-slate-400 mt-1">Manage pricing plans and features</p>
        </div>
        <div className="flex gap-2">
          {plans.length === 0 && (
            <Button variant="outline" onClick={handleSeedPlans}>
              <Package className="w-4 h-4 mr-2" />
              Seed Default Plans
            </Button>
          )}
          <Button onClick={handleCreatePlan}>
            <Plus className="w-4 h-4 mr-2" />
            Create Plan
          </Button>
        </div>
      </div>

      {/* Plans Grid */}
      {plans.length === 0 ? (
        <Card className="bg-slate-800 border-slate-700">
          <CardContent className="text-center py-12">
            <CreditCard className="w-12 h-12 text-slate-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-white">No plans configured</h3>
            <p className="text-slate-400 mt-1 mb-4">
              Create your first subscription plan or seed defaults
            </p>
            <div className="flex gap-2 justify-center">
              <Button variant="outline" onClick={handleSeedPlans}>
                Seed Defaults
              </Button>
              <Button onClick={handleCreatePlan}>
                Create Plan
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {plans.map((plan) => (
            <Card 
              key={plan.id} 
              className={`bg-slate-800 border-slate-700 relative overflow-hidden ${
                plan.is_popular ? 'ring-2 ring-purple-500' : ''
              }`}
            >
              {plan.is_popular && (
                <div className="absolute top-0 right-0 bg-purple-500 text-white text-xs px-2 py-1 rounded-bl">
                  <Star className="w-3 h-3 inline mr-1" />
                  Popular
                </div>
              )}
              
              <CardHeader className="pb-2">
                <div className="flex items-start justify-between">
                  <div>
                    <CardTitle className="text-white flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded-full" 
                        style={{ backgroundColor: plan.color }}
                      />
                      {plan.name}
                    </CardTitle>
                    <CardDescription className="text-slate-400">
                      {plan.tagline}
                    </CardDescription>
                  </div>
                  {getStatusBadge(plan.status)}
                </div>
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Price */}
                <div>
                  <p className="text-2xl font-bold text-white">
                    {formatPrice(plan.price_monthly)}
                    {plan.price_monthly > 0 && (
                      <span className="text-sm font-normal text-slate-400">/mo</span>
                    )}
                  </p>
                  {plan.price_yearly > 0 && (
                    <p className="text-sm text-slate-400">
                      or {formatPrice(plan.price_yearly)}/year
                    </p>
                  )}
                </div>

                {/* Customer count warning */}
                {plan.used_by_count > 0 && (
                  <div className="flex items-center gap-2 text-amber-400 text-sm bg-amber-500/10 px-2 py-1 rounded">
                    <Users className="w-4 h-4" />
                    {plan.used_by_count} customer{plan.used_by_count > 1 ? 's' : ''}
                  </div>
                )}

                {/* Quick stats */}
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="text-slate-400">
                    <Building2 className="w-3 h-3 inline mr-1" />
                    {plan.limits?.max_companies === -1 ? '∞' : plan.limits?.max_companies || 0} companies
                  </div>
                  <div className="text-slate-400">
                    <Users className="w-3 h-3 inline mr-1" />
                    {plan.limits?.max_users === -1 ? '∞' : plan.limits?.max_users || 0} users
                  </div>
                </div>

                {/* Visibility */}
                <div className="flex items-center gap-2 text-sm">
                  {plan.is_public ? (
                    <span className="text-green-400 flex items-center gap-1">
                      <Eye className="w-3 h-3" /> Public
                    </span>
                  ) : (
                    <span className="text-slate-500 flex items-center gap-1">
                      <EyeOff className="w-3 h-3" /> Hidden
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="flex gap-2 pt-2">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => handleEditPlan(plan)}
                  >
                    <Edit2 className="w-3 h-3 mr-1" />
                    Edit
                  </Button>
                  <Button 
                    variant="ghost" 
                    size="sm"
                    className="text-red-400 hover:text-red-300 hover:bg-red-500/10"
                    onClick={() => handleDeletePlan(plan)}
                    disabled={plan.used_by_count > 0}
                  >
                    <Trash2 className="w-3 h-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Plan Editor Modal */}
      <Dialog open={showEditor} onOpenChange={setShowEditor}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-slate-900 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">
              {editingPlan?.id ? 'Edit Plan' : 'Create Plan'}
            </DialogTitle>
            <DialogDescription>
              {editingPlan?.used_by_count > 0 && (
                <span className="text-amber-400 flex items-center gap-1">
                  <AlertTriangle className="w-4 h-4" />
                  {editingPlan.used_by_count} customers using this plan. Changes will increment version.
                </span>
              )}
            </DialogDescription>
          </DialogHeader>

          {editingPlan && (
            <Tabs value={activeTab} onValueChange={setActiveTab}>
              <TabsList className="grid w-full grid-cols-4 bg-slate-800">
                <TabsTrigger value="basic">Basic Info</TabsTrigger>
                <TabsTrigger value="features">Features</TabsTrigger>
                <TabsTrigger value="limits">Limits</TabsTrigger>
                <TabsTrigger value="display">Display</TabsTrigger>
              </TabsList>

              {/* Basic Info Tab */}
              <TabsContent value="basic" className="space-y-4 mt-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Plan Name *</Label>
                    <Input
                      value={editingPlan.name}
                      onChange={(e) => setEditingPlan(prev => ({ ...prev, name: e.target.value }))}
                      placeholder="Professional"
                      className="bg-slate-800 border-slate-600 text-white"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Slug *</Label>
                    <Input
                      value={editingPlan.slug}
                      onChange={(e) => setEditingPlan(prev => ({ 
                        ...prev, 
                        slug: e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, '-')
                      }))}
                      placeholder="professional"
                      className="bg-slate-800 border-slate-600 text-white"
                      disabled={editingPlan.id && editingPlan.used_by_count > 0}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-slate-300">Tagline</Label>
                  <Input
                    value={editingPlan.tagline}
                    onChange={(e) => setEditingPlan(prev => ({ ...prev, tagline: e.target.value }))}
                    placeholder="For growing businesses"
                    className="bg-slate-800 border-slate-600 text-white"
                  />
                </div>

                <div className="space-y-2">
                  <Label className="text-slate-300">Description</Label>
                  <Input
                    value={editingPlan.description}
                    onChange={(e) => setEditingPlan(prev => ({ ...prev, description: e.target.value }))}
                    placeholder="Full description of the plan"
                    className="bg-slate-800 border-slate-600 text-white"
                  />
                </div>

                <Separator className="bg-slate-700" />

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Monthly Price (in paise)</Label>
                    <Input
                      type="number"
                      value={editingPlan.price_monthly}
                      onChange={(e) => setEditingPlan(prev => ({ ...prev, price_monthly: parseInt(e.target.value) || 0 }))}
                      placeholder="299900 = ₹2,999"
                      className="bg-slate-800 border-slate-600 text-white"
                    />
                    <p className="text-xs text-slate-500">
                      Display: {formatPrice(editingPlan.price_monthly)}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Yearly Price (in paise)</Label>
                    <Input
                      type="number"
                      value={editingPlan.price_yearly}
                      onChange={(e) => setEditingPlan(prev => ({ ...prev, price_yearly: parseInt(e.target.value) || 0 }))}
                      placeholder="2999000 = ₹29,990"
                      className="bg-slate-800 border-slate-600 text-white"
                    />
                    <p className="text-xs text-slate-500">
                      Display: {formatPrice(editingPlan.price_yearly)}
                    </p>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Support Level</Label>
                    <Select 
                      value={editingPlan.support_level} 
                      onValueChange={(v) => setEditingPlan(prev => ({ ...prev, support_level: v }))}
                    >
                      <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="community">Community</SelectItem>
                        <SelectItem value="email">Email Support</SelectItem>
                        <SelectItem value="priority">Priority Support</SelectItem>
                        <SelectItem value="dedicated">Dedicated Support</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Response Time (hours)</Label>
                    <Input
                      type="number"
                      value={editingPlan.response_time_hours || ''}
                      onChange={(e) => setEditingPlan(prev => ({ ...prev, response_time_hours: parseInt(e.target.value) || null }))}
                      placeholder="24"
                      className="bg-slate-800 border-slate-600 text-white"
                    />
                  </div>
                </div>

                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <Switch
                      checked={editingPlan.is_trial}
                      onCheckedChange={(v) => setEditingPlan(prev => ({ ...prev, is_trial: v }))}
                    />
                    <Label className="text-slate-300">Trial Plan</Label>
                  </div>
                  {editingPlan.is_trial && (
                    <div className="flex items-center gap-2">
                      <Input
                        type="number"
                        value={editingPlan.trial_days}
                        onChange={(e) => setEditingPlan(prev => ({ ...prev, trial_days: parseInt(e.target.value) || 0 }))}
                        className="w-20 bg-slate-800 border-slate-600 text-white"
                      />
                      <Label className="text-slate-300">days</Label>
                    </div>
                  )}
                </div>
              </TabsContent>

              {/* Features Tab */}
              <TabsContent value="features" className="space-y-4 mt-4">
                {Object.entries(groupedFeatures).map(([category, features]) => (
                  <div key={category}>
                    <h3 className="text-sm font-medium text-slate-400 mb-2">{category}</h3>
                    <div className="grid gap-2 sm:grid-cols-2">
                      {features.map(({ key, name, description }) => (
                        <div 
                          key={key}
                          className="flex items-center justify-between p-2 rounded bg-slate-800"
                        >
                          <div>
                            <p className="text-sm text-white">{name}</p>
                            <p className="text-xs text-slate-500">{description}</p>
                          </div>
                          <Switch
                            checked={editingPlan.features?.[key] || false}
                            onCheckedChange={(v) => updateFeature(key, v)}
                          />
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </TabsContent>

              {/* Limits Tab */}
              <TabsContent value="limits" className="space-y-4 mt-4">
                <p className="text-sm text-slate-400">Set -1 for unlimited</p>
                <div className="grid gap-4 sm:grid-cols-2">
                  {Object.entries(metadata.limits).map(([key, meta]) => (
                    <div key={key} className="space-y-1">
                      <Label className="text-slate-300">{meta.name}</Label>
                      <Input
                        type="number"
                        value={editingPlan.limits?.[key] ?? 0}
                        onChange={(e) => updateLimit(key, e.target.value)}
                        className="bg-slate-800 border-slate-600 text-white"
                      />
                      <p className="text-xs text-slate-500">{meta.description}</p>
                    </div>
                  ))}
                </div>
              </TabsContent>

              {/* Display Tab */}
              <TabsContent value="display" className="space-y-4 mt-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label className="text-slate-300">Status</Label>
                    <Select 
                      value={editingPlan.status} 
                      onValueChange={(v) => setEditingPlan(prev => ({ ...prev, status: v }))}
                    >
                      <SelectTrigger className="bg-slate-800 border-slate-600 text-white">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="draft">Draft</SelectItem>
                        <SelectItem value="active">Active</SelectItem>
                        <SelectItem value="archived">Archived</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="space-y-2">
                    <Label className="text-slate-300">Display Order</Label>
                    <Input
                      type="number"
                      value={editingPlan.display_order}
                      onChange={(e) => setEditingPlan(prev => ({ ...prev, display_order: parseInt(e.target.value) || 0 }))}
                      className="bg-slate-800 border-slate-600 text-white"
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label className="text-slate-300">Accent Color</Label>
                  <div className="flex gap-2">
                    <Input
                      type="color"
                      value={editingPlan.color}
                      onChange={(e) => setEditingPlan(prev => ({ ...prev, color: e.target.value }))}
                      className="w-16 h-10 p-1 cursor-pointer bg-slate-800 border-slate-600"
                    />
                    <Input
                      value={editingPlan.color}
                      onChange={(e) => setEditingPlan(prev => ({ ...prev, color: e.target.value }))}
                      className="flex-1 bg-slate-800 border-slate-600 text-white"
                    />
                  </div>
                </div>

                <div className="flex flex-col gap-4">
                  <div className="flex items-center justify-between p-3 rounded bg-slate-800">
                    <div>
                      <p className="text-white">Show on Pricing Page</p>
                      <p className="text-xs text-slate-500">Make this plan visible to the public</p>
                    </div>
                    <Switch
                      checked={editingPlan.is_public}
                      onCheckedChange={(v) => setEditingPlan(prev => ({ ...prev, is_public: v }))}
                    />
                  </div>
                  <div className="flex items-center justify-between p-3 rounded bg-slate-800">
                    <div>
                      <p className="text-white">Mark as Popular</p>
                      <p className="text-xs text-slate-500">Highlight this plan with a badge</p>
                    </div>
                    <Switch
                      checked={editingPlan.is_popular}
                      onCheckedChange={(v) => setEditingPlan(prev => ({ ...prev, is_popular: v }))}
                    />
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          )}

          <DialogFooter className="mt-4">
            <Button variant="outline" onClick={() => setShowEditor(false)}>
              Cancel
            </Button>
            <Button onClick={handleSavePlan} disabled={saving}>
              {saving ? 'Saving...' : editingPlan?.id ? 'Update Plan' : 'Create Plan'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
