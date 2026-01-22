import { useState, useEffect, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Label } from '../../components/ui/label';
import { Badge } from '../../components/ui/badge';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '../../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../../components/ui/select';
import { toast } from 'sonner';
import { 
  Search, Plus, Sparkles, Database, RefreshCw, CheckCircle, 
  Printer, Laptop, Monitor, HardDrive, Router, Server, 
  Battery, Video, Loader2, Package, Trash2, Eye
} from 'lucide-react';

const API_URL = process.env.REACT_APP_BACKEND_URL;

const DEVICE_TYPES = [
  { value: 'Printer', label: 'Printer', icon: Printer },
  { value: 'Laptop', label: 'Laptop', icon: Laptop },
  { value: 'Desktop', label: 'Desktop', icon: Monitor },
  { value: 'NVR', label: 'NVR', icon: Video },
  { value: 'CCTV', label: 'CCTV Camera', icon: Video },
  { value: 'Router', label: 'Router/Switch', icon: Router },
  { value: 'UPS', label: 'UPS', icon: Battery },
  { value: 'Server', label: 'Server', icon: Server },
];

const DeviceModelCatalog = () => {
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [filterType, setFilterType] = useState('');
  const [filterBrand, setFilterBrand] = useState('');
  
  // AI Lookup Modal
  const [showLookupModal, setShowLookupModal] = useState(false);
  const [lookupData, setLookupData] = useState({ device_type: '', brand: '', model: '' });
  const [lookupLoading, setLookupLoading] = useState(false);
  const [lookupResult, setLookupResult] = useState(null);
  
  // View Model Modal
  const [showViewModal, setShowViewModal] = useState(false);
  const [viewingModel, setViewingModel] = useState(null);

  const fetchModels = useCallback(async () => {
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (searchQuery) params.append('q', searchQuery);
      if (filterType) params.append('device_type', filterType);
      if (filterBrand) params.append('brand', filterBrand);
      
      const response = await fetch(`${API_URL}/api/device-models?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        const data = await response.json();
        setModels(data);
      }
    } catch (error) {
      console.error('Error fetching models:', error);
      toast.error('Failed to load device models');
    } finally {
      setLoading(false);
    }
  }, [searchQuery, filterType, filterBrand]);

  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const handleAILookup = async () => {
    if (!lookupData.device_type || !lookupData.brand || !lookupData.model) {
      toast.error('Please fill in all fields');
      return;
    }
    
    setLookupLoading(true);
    setLookupResult(null);
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/device-models/lookup`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(lookupData),
      });
      
      const data = await response.json();
      setLookupResult(data);
      
      if (data.found) {
        toast.success('Device specifications found!');
        fetchModels(); // Refresh the list
      } else {
        toast.error(data.message || 'Device not found');
      }
    } catch (error) {
      console.error('AI Lookup error:', error);
      toast.error('AI lookup failed');
    } finally {
      setLookupLoading(false);
    }
  };

  const handleVerify = async (modelId) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/device-models/${modelId}/verify`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        toast.success('Model verified');
        fetchModels();
      }
    } catch (error) {
      toast.error('Failed to verify model');
    }
  };

  const handleDelete = async (modelId) => {
    if (!window.confirm('Are you sure you want to delete this device model?')) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${API_URL}/api/device-models/${modelId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        toast.success('Model deleted');
        fetchModels();
      }
    } catch (error) {
      toast.error('Failed to delete model');
    }
  };

  const getDeviceIcon = (type) => {
    const deviceType = DEVICE_TYPES.find(d => d.value === type);
    if (deviceType) {
      const Icon = deviceType.icon;
      return <Icon className="h-5 w-5" />;
    }
    return <HardDrive className="h-5 w-5" />;
  };

  const uniqueBrands = [...new Set(models.map(m => m.brand))].sort();

  return (
    <div className="space-y-6" data-testid="device-model-catalog-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Device Model Catalog</h1>
          <p className="text-sm text-gray-500 mt-1">
            AI-powered device specifications and compatible parts database
          </p>
        </div>
        <Button 
          onClick={() => {
            setShowLookupModal(true);
            setLookupResult(null);
            setLookupData({ device_type: '', brand: '', model: '' });
          }}
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-700 hover:to-indigo-700"
          data-testid="ai-lookup-btn"
        >
          <Sparkles className="h-4 w-4 mr-2" />
          AI Lookup
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-blue-600 font-medium">Total Models</p>
                <p className="text-2xl font-bold text-blue-700">{models.length}</p>
              </div>
              <Database className="h-8 w-8 text-blue-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-green-600 font-medium">Verified</p>
                <p className="text-2xl font-bold text-green-700">
                  {models.filter(m => m.is_verified).length}
                </p>
              </div>
              <CheckCircle className="h-8 w-8 text-green-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-violet-50 to-violet-100 border-violet-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-violet-600 font-medium">AI Generated</p>
                <p className="text-2xl font-bold text-violet-700">
                  {models.filter(m => m.source === 'ai_generated').length}
                </p>
              </div>
              <Sparkles className="h-8 w-8 text-violet-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-gradient-to-br from-amber-50 to-amber-100 border-amber-200">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs text-amber-600 font-medium">Brands</p>
                <p className="text-2xl font-bold text-amber-700">{uniqueBrands.length}</p>
              </div>
              <Package className="h-8 w-8 text-amber-500 opacity-50" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Filters */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="flex-1">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search models, brands..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                  data-testid="search-input"
                />
              </div>
            </div>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-full sm:w-40" data-testid="filter-type">
                <SelectValue placeholder="Device Type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {DEVICE_TYPES.map(type => (
                  <SelectItem key={type.value} value={type.value}>{type.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterBrand} onValueChange={setFilterBrand}>
              <SelectTrigger className="w-full sm:w-40" data-testid="filter-brand">
                <SelectValue placeholder="Brand" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Brands</SelectItem>
                {uniqueBrands.map(brand => (
                  <SelectItem key={brand} value={brand}>{brand}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>

      {/* Models List */}
      {loading ? (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      ) : models.length === 0 ? (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Database className="h-12 w-12 text-gray-300 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No device models yet</h3>
              <p className="text-gray-500 mb-4">
                Use AI Lookup to automatically fetch device specifications
              </p>
              <Button onClick={() => setShowLookupModal(true)}>
                <Sparkles className="h-4 w-4 mr-2" />
                Start AI Lookup
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4">
          {models.map((model) => (
            <Card key={model.id} className="hover:shadow-md transition-shadow" data-testid={`model-card-${model.id}`}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="flex items-start space-x-4">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      {getDeviceIcon(model.device_type)}
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">
                          {model.brand} {model.model}
                        </h3>
                        {model.is_verified && (
                          <Badge className="bg-green-100 text-green-700 text-xs">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Verified
                          </Badge>
                        )}
                        {model.source === 'ai_generated' && !model.is_verified && (
                          <Badge className="bg-violet-100 text-violet-700 text-xs">
                            <Sparkles className="h-3 w-3 mr-1" />
                            AI
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {model.device_type} {model.category && `• ${model.category}`}
                      </p>
                      <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                        <span>{model.compatible_consumables?.length || 0} consumables</span>
                        <span>{model.compatible_upgrades?.length || 0} upgrades</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => {
                        setViewingModel(model);
                        setShowViewModal(true);
                      }}
                    >
                      <Eye className="h-4 w-4 mr-1" />
                      View
                    </Button>
                    {!model.is_verified && (
                      <Button 
                        variant="outline" 
                        size="sm"
                        onClick={() => handleVerify(model.id)}
                        className="text-green-600 hover:text-green-700"
                      >
                        <CheckCircle className="h-4 w-4" />
                      </Button>
                    )}
                    <Button 
                      variant="ghost" 
                      size="sm"
                      onClick={() => handleDelete(model.id)}
                      className="text-red-500 hover:text-red-600"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* AI Lookup Modal */}
      <Dialog open={showLookupModal} onOpenChange={setShowLookupModal}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Sparkles className="h-5 w-5 text-violet-600" />
              AI Device Lookup
            </DialogTitle>
            <DialogDescription>
              Enter device details to automatically fetch specifications and compatible parts
            </DialogDescription>
          </DialogHeader>
          
          <div className="space-y-4 py-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <Label>Device Type *</Label>
                <Select 
                  value={lookupData.device_type} 
                  onValueChange={(v) => setLookupData({...lookupData, device_type: v})}
                >
                  <SelectTrigger data-testid="lookup-device-type">
                    <SelectValue placeholder="Select type" />
                  </SelectTrigger>
                  <SelectContent>
                    {DEVICE_TYPES.map(type => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label>Brand *</Label>
                <Input
                  placeholder="e.g., HP, Dell, Hikvision"
                  value={lookupData.brand}
                  onChange={(e) => setLookupData({...lookupData, brand: e.target.value})}
                  data-testid="lookup-brand"
                />
              </div>
              <div>
                <Label>Model *</Label>
                <Input
                  placeholder="e.g., LaserJet Pro M428fdw"
                  value={lookupData.model}
                  onChange={(e) => setLookupData({...lookupData, model: e.target.value})}
                  data-testid="lookup-model"
                />
              </div>
            </div>

            {/* Results */}
            {lookupResult && (
              <div className="mt-4 border rounded-lg p-4 bg-gray-50">
                {lookupResult.found ? (
                  <div className="space-y-4">
                    <div className="flex items-center gap-2 text-green-600">
                      <CheckCircle className="h-5 w-5" />
                      <span className="font-medium">Device Found!</span>
                      <Badge variant="outline" className="ml-2">
                        {lookupResult.source === 'cache' ? 'From Cache' : 'AI Generated'}
                      </Badge>
                    </div>
                    
                    {lookupResult.device_model && (
                      <>
                        <div>
                          <h4 className="font-medium text-gray-900 mb-2">Specifications</h4>
                          <div className="grid grid-cols-2 gap-2 text-sm">
                            {Object.entries(lookupResult.device_model.specifications || {})
                              .filter(([_, v]) => v !== null && v !== '' && v !== undefined)
                              .slice(0, 10)
                              .map(([key, value]) => (
                                <div key={key} className="flex">
                                  <span className="text-gray-500 capitalize">
                                    {key.replace(/_/g, ' ')}:
                                  </span>
                                  <span className="ml-2 font-medium">
                                    {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : 
                                     Array.isArray(value) ? value.join(', ') : String(value)}
                                  </span>
                                </div>
                              ))}
                          </div>
                        </div>

                        {lookupResult.device_model.compatible_consumables?.length > 0 && (
                          <div>
                            <h4 className="font-medium text-gray-900 mb-2">
                              Compatible Consumables ({lookupResult.device_model.compatible_consumables.length})
                            </h4>
                            <div className="space-y-2">
                              {lookupResult.device_model.compatible_consumables.map((c, i) => (
                                <div key={i} className="flex items-center justify-between text-sm bg-white p-2 rounded border">
                                  <div>
                                    <span className="font-medium">{c.name}</span>
                                    {c.color && <Badge variant="outline" className="ml-2 text-xs">{c.color}</Badge>}
                                  </div>
                                  <div className="text-gray-500">
                                    <span className="font-mono">{c.part_number}</span>
                                    {c.yield_pages && <span className="ml-2">({c.yield_pages})</span>}
                                  </div>
                                </div>
                              ))}
                            </div>
                          </div>
                        )}
                      </>
                    )}
                  </div>
                ) : (
                  <div className="text-amber-600 flex items-center gap-2">
                    <RefreshCw className="h-5 w-5" />
                    <span>{lookupResult.message}</span>
                  </div>
                )}
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowLookupModal(false)}>
              Close
            </Button>
            <Button 
              onClick={handleAILookup} 
              disabled={lookupLoading}
              className="bg-gradient-to-r from-violet-600 to-indigo-600"
            >
              {lookupLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Looking up...
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4 mr-2" />
                  Fetch Specifications
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* View Model Modal */}
      <Dialog open={showViewModal} onOpenChange={setShowViewModal}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              {viewingModel?.brand} {viewingModel?.model}
            </DialogTitle>
            <DialogDescription>
              {viewingModel?.device_type} {viewingModel?.category && `• ${viewingModel.category}`}
            </DialogDescription>
          </DialogHeader>
          
          {viewingModel && (
            <div className="space-y-6 py-4">
              {/* Specifications */}
              <div>
                <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <HardDrive className="h-4 w-4" />
                  Specifications
                </h4>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {Object.entries(viewingModel.specifications || {})
                    .filter(([_, v]) => v !== null && v !== '' && v !== undefined && !(Array.isArray(v) && v.length === 0))
                    .map(([key, value]) => (
                      <div key={key} className="bg-gray-50 p-3 rounded-lg">
                        <p className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</p>
                        <p className="font-medium text-gray-900">
                          {typeof value === 'boolean' ? (value ? 'Yes' : 'No') : 
                           Array.isArray(value) ? value.join(', ') : String(value)}
                        </p>
                      </div>
                    ))}
                </div>
              </div>

              {/* Consumables */}
              {viewingModel.compatible_consumables?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Package className="h-4 w-4" />
                    Compatible Consumables ({viewingModel.compatible_consumables.length})
                  </h4>
                  <div className="border rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="text-left p-3 font-medium">Name</th>
                          <th className="text-left p-3 font-medium">Part Number</th>
                          <th className="text-left p-3 font-medium">Type</th>
                          <th className="text-left p-3 font-medium">Yield/Capacity</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y">
                        {viewingModel.compatible_consumables.map((c, i) => (
                          <tr key={i} className="hover:bg-gray-50">
                            <td className="p-3">
                              {c.name}
                              {c.color && <Badge variant="outline" className="ml-2 text-xs">{c.color}</Badge>}
                            </td>
                            <td className="p-3 font-mono text-gray-600">{c.part_number}</td>
                            <td className="p-3">{c.consumable_type}</td>
                            <td className="p-3">{c.yield_pages || c.capacity || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {/* Upgrades */}
              {viewingModel.compatible_upgrades?.length > 0 && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-3 flex items-center gap-2">
                    <Plus className="h-4 w-4" />
                    Compatible Upgrades ({viewingModel.compatible_upgrades.length})
                  </h4>
                  <div className="space-y-2">
                    {viewingModel.compatible_upgrades.map((u, i) => (
                      <div key={i} className="flex items-center justify-between bg-gray-50 p-3 rounded-lg">
                        <div>
                          <span className="font-medium">{u.name}</span>
                          <Badge variant="outline" className="ml-2 text-xs">{u.consumable_type}</Badge>
                        </div>
                        <div className="text-gray-500 text-sm">
                          {u.part_number && <span className="font-mono">{u.part_number}</span>}
                          {u.capacity && <span className="ml-2">({u.capacity})</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Metadata */}
              <div className="text-xs text-gray-500 pt-4 border-t">
                <div className="flex items-center gap-4">
                  <span>Source: {viewingModel.source}</span>
                  {viewingModel.ai_confidence && (
                    <span>Confidence: {Math.round(viewingModel.ai_confidence * 100)}%</span>
                  )}
                  <span>Created: {new Date(viewingModel.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setShowViewModal(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default DeviceModelCatalog;
