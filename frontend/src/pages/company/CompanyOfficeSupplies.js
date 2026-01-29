import { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Package, ShoppingCart, Plus, Minus, MapPin, Building2, 
  Clock, CheckCircle2, Truck, FileText, ChevronRight, Search, X
} from 'lucide-react';
import { useCompanyAuth } from '../../context/CompanyAuthContext';
import { Button } from '../../components/ui/button';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '../../components/ui/dialog';
import { toast } from 'sonner';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const CompanyOfficeSupplies = () => {
  const { token } = useCompanyAuth();
  const [catalog, setCatalog] = useState([]);
  const [sites, setSites] = useState([]);
  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('catalog');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Cart state
  const [cart, setCart] = useState({});
  
  // Order modal state
  const [orderModalOpen, setOrderModalOpen] = useState(false);
  const [orderLoading, setOrderLoading] = useState(false);
  const [deliveryType, setDeliveryType] = useState('existing');
  const [selectedSite, setSelectedSite] = useState('');
  const [newLocation, setNewLocation] = useState({
    address: '',
    city: '',
    pincode: '',
    contact_person: '',
    contact_phone: ''
  });
  const [orderNotes, setOrderNotes] = useState('');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [catalogRes, sitesRes, ordersRes] = await Promise.all([
        axios.get(`${API}/company/supply-catalog`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/company/sites`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        axios.get(`${API}/company/supply-orders`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);
      setCatalog(catalogRes.data);
      setSites(sitesRes.data);
      setOrders(ordersRes.data);
    } catch (error) {
      toast.error('Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const updateCart = (productId, quantity) => {
    setCart(prev => {
      const newCart = { ...prev };
      if (quantity <= 0) {
        delete newCart[productId];
      } else {
        newCart[productId] = quantity;
      }
      return newCart;
    });
  };

  const getCartCount = () => {
    return Object.values(cart).reduce((sum, qty) => sum + qty, 0);
  };

  const getCartItems = () => {
    const items = [];
    catalog.forEach(category => {
      category.products.forEach(product => {
        if (cart[product.id]) {
          items.push({
            ...product,
            category_name: category.name,
            quantity: cart[product.id]
          });
        }
      });
    });
    return items;
  };

  const handlePlaceOrder = async () => {
    const cartItems = getCartItems();
    if (cartItems.length === 0) {
      toast.error('Your cart is empty');
      return;
    }

    // Validate delivery location
    if (deliveryType === 'existing' && !selectedSite) {
      toast.error('Please select a delivery location');
      return;
    }
    if (deliveryType === 'new') {
      if (!newLocation.address || !newLocation.contact_person || !newLocation.contact_phone) {
        toast.error('Please fill in all required delivery fields');
        return;
      }
    }

    setOrderLoading(true);
    try {
      const orderData = {
        items: cartItems.map(item => ({
          product_id: item.id,
          quantity: item.quantity
        })),
        delivery_location: deliveryType === 'existing' 
          ? { type: 'existing', site_id: selectedSite }
          : { type: 'new', ...newLocation },
        notes: orderNotes
      };

      const response = await axios.post(`${API}/company/supply-orders`, orderData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success(`Order ${response.data.order_number} placed successfully!`);
      setOrderModalOpen(false);
      setCart({});
      setOrderNotes('');
      setDeliveryType('existing');
      setSelectedSite('');
      setNewLocation({ address: '', city: '', pincode: '', contact_person: '', contact_phone: '' });
      fetchData();
      setActiveTab('orders');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to place order');
    } finally {
      setOrderLoading(false);
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      requested: 'bg-blue-100 text-blue-700',
      approved: 'bg-emerald-100 text-emerald-700',
      processing: 'bg-amber-100 text-amber-700',
      delivered: 'bg-green-100 text-green-700',
      cancelled: 'bg-red-100 text-red-700'
    };
    return colors[status] || 'bg-slate-100 text-slate-700';
  };

  const getStatusIcon = (status) => {
    const icons = {
      requested: Clock,
      approved: CheckCircle2,
      processing: Package,
      delivered: Truck,
      cancelled: FileText
    };
    const Icon = icons[status] || Clock;
    return <Icon className="h-4 w-4" />;
  };

  // Filter catalog by search query
  const getFilteredCatalog = () => {
    if (!searchQuery.trim()) return catalog;
    
    const query = searchQuery.toLowerCase();
    return catalog.map(category => ({
      ...category,
      products: category.products.filter(product => 
        product.name.toLowerCase().includes(query) ||
        (product.description && product.description.toLowerCase().includes(query))
      )
    })).filter(category => category.products.length > 0);
  };

  const filteredCatalog = getFilteredCatalog();
  const totalProducts = catalog.reduce((sum, cat) => sum + cat.products.length, 0);
  const filteredProductCount = filteredCatalog.reduce((sum, cat) => sum + cat.products.length, 0);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Office Supplies</h1>
          <p className="text-slate-500 mt-1">Order stationery, consumables, and supplies</p>
        </div>
        
        {getCartCount() > 0 && (
          <Button 
            onClick={() => setOrderModalOpen(true)}
            className="bg-emerald-600 hover:bg-emerald-700"
            data-testid="view-cart-btn"
          >
            <ShoppingCart className="h-4 w-4 mr-2" />
            View Cart ({getCartCount()} items)
          </Button>
        )}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('catalog')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
            activeTab === 'catalog' 
              ? 'bg-white text-slate-900 shadow-sm' 
              : 'text-slate-600 hover:text-slate-900'
          }`}
          data-testid="catalog-tab"
        >
          <Package className="h-4 w-4 inline mr-2" />
          Catalog
        </button>
        <button
          onClick={() => setActiveTab('orders')}
          className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
            activeTab === 'orders' 
              ? 'bg-white text-slate-900 shadow-sm' 
              : 'text-slate-600 hover:text-slate-900'
          }`}
          data-testid="orders-tab"
        >
          <FileText className="h-4 w-4 inline mr-2" />
          My Orders ({orders.length})
        </button>
      </div>

      {activeTab === 'catalog' ? (
        /* Catalog View */
        <div className="space-y-6">
          {/* Search Bar */}
          <div className="relative">
            <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-slate-400" />
            <input
              type="text"
              placeholder="Search products..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-12 pr-12 py-3 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              data-testid="catalog-search"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-4 top-1/2 -translate-y-1/2 p-1 hover:bg-slate-100 rounded-full"
              >
                <X className="h-4 w-4 text-slate-400" />
              </button>
            )}
          </div>
          
          {/* Search Results Info */}
          {searchQuery && (
            <p className="text-sm text-slate-500">
              Showing {filteredProductCount} of {totalProducts} products
              {filteredProductCount === 0 && (
                <span className="ml-2 text-amber-600">— Try a different search term</span>
              )}
            </p>
          )}

          {filteredCatalog.map(category => (
            <div key={category.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden">
              <div className="bg-slate-50 px-6 py-4 border-b border-slate-200">
                <h2 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
                  <span className="text-xl">{category.icon}</span>
                  {category.name}
                  {searchQuery && (
                    <span className="text-sm font-normal text-slate-400">
                      ({category.products.length} matches)
                    </span>
                  )}
                </h2>
                {category.description && (
                  <p className="text-sm text-slate-500 mt-1">{category.description}</p>
                )}
              </div>
              <div className="divide-y divide-slate-100">
                {category.products.map(product => (
                  <div 
                    key={product.id} 
                    className="px-6 py-4 flex items-center justify-between hover:bg-slate-50 transition-colors"
                  >
                    <div className="flex-1">
                      <h3 className="font-medium text-slate-900">{product.name}</h3>
                      {product.description && (
                        <p className="text-sm text-slate-500">{product.description}</p>
                      )}
                      <div className="flex items-center gap-3 mt-1">
                        <p className="text-xs text-slate-400">Unit: {product.unit}</p>
                        {product.price && (
                          <p className="text-sm font-semibold text-emerald-600">₹{product.price.toLocaleString('en-IN')}</p>
                        )}
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      {cart[product.id] ? (
                        <div className="flex items-center gap-2 bg-emerald-50 rounded-lg p-1">
                          <button
                            onClick={() => updateCart(product.id, cart[product.id] - 1)}
                            className="w-8 h-8 flex items-center justify-center text-emerald-700 hover:bg-emerald-100 rounded"
                            data-testid={`minus-${product.id}`}
                          >
                            <Minus className="h-4 w-4" />
                          </button>
                          <span className="w-8 text-center font-medium text-emerald-700" data-testid={`qty-${product.id}`}>
                            {cart[product.id]}
                          </span>
                          <button
                            onClick={() => updateCart(product.id, cart[product.id] + 1)}
                            className="w-8 h-8 flex items-center justify-center text-emerald-700 hover:bg-emerald-100 rounded"
                            data-testid={`plus-${product.id}`}
                          >
                            <Plus className="h-4 w-4" />
                          </button>
                        </div>
                      ) : (
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => updateCart(product.id, 1)}
                          className="border-emerald-500 text-emerald-700 hover:bg-emerald-50"
                          data-testid={`add-${product.id}`}
                        >
                          <Plus className="h-4 w-4 mr-1" />
                          Add
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
          
          {/* Empty state when search has no results */}
          {searchQuery && filteredCatalog.length === 0 && (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
              <Search className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No products found</h3>
              <p className="text-slate-500 mb-4">Try searching with different keywords</p>
              <Button onClick={() => setSearchQuery('')} variant="outline">
                Clear Search
              </Button>
            </div>
          )}
        </div>
      ) : (
        /* Orders View */
        <div className="space-y-4">
          {orders.length === 0 ? (
            <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
              <FileText className="h-12 w-12 mx-auto text-slate-300 mb-4" />
              <h3 className="text-lg font-medium text-slate-900 mb-2">No Orders Yet</h3>
              <p className="text-slate-500 mb-4">Browse the catalog and place your first order</p>
              <Button onClick={() => setActiveTab('catalog')} variant="outline">
                Browse Catalog
              </Button>
            </div>
          ) : (
            orders.map(order => (
              <div key={order.id} className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
                  <div>
                    <div className="flex items-center gap-3">
                      <span className="font-mono font-medium text-slate-900">{order.order_number}</span>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium flex items-center gap-1 ${getStatusColor(order.status)}`}>
                        {getStatusIcon(order.status)}
                        {order.status.charAt(0).toUpperCase() + order.status.slice(1)}
                      </span>
                    </div>
                    <p className="text-sm text-slate-500 mt-1">
                      {new Date(order.created_at).toLocaleDateString('en-IN', {
                        day: 'numeric',
                        month: 'short',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </p>
                  </div>
                  <ChevronRight className="h-5 w-5 text-slate-400" />
                </div>
                <div className="px-6 py-4">
                  <div className="space-y-2">
                    {order.items.map((item, idx) => (
                      <div key={idx} className="flex items-center justify-between text-sm">
                        <span className="text-slate-600">{item.product_name}</span>
                        <span className="font-medium text-slate-900">{item.quantity} {item.unit}</span>
                      </div>
                    ))}
                  </div>
                  {order.delivery_location && (
                    <div className="mt-4 pt-4 border-t border-slate-100">
                      <p className="text-xs text-slate-500 flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        Delivery: {order.delivery_location.site_name || order.delivery_location.address || 'Location specified'}
                        {order.delivery_location.city && `, ${order.delivery_location.city}`}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
        </div>
      )}

      {/* Place Order Modal */}
      <Dialog open={orderModalOpen} onOpenChange={setOrderModalOpen}>
        <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <ShoppingCart className="h-5 w-5 text-emerald-600" />
              Place Order
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-6 mt-4">
            {/* Cart Items */}
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-3">Items ({getCartCount()})</h3>
              <div className="bg-slate-50 rounded-lg p-4 space-y-3 max-h-48 overflow-y-auto">
                {getCartItems().map(item => (
                  <div key={item.id} className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-slate-900 text-sm">{item.name}</p>
                      <p className="text-xs text-slate-500">{item.category_name}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => updateCart(item.id, item.quantity - 1)}
                        className="w-6 h-6 flex items-center justify-center text-slate-500 hover:text-slate-700 hover:bg-slate-200 rounded"
                      >
                        <Minus className="h-3 w-3" />
                      </button>
                      <span className="w-6 text-center font-medium text-sm">{item.quantity}</span>
                      <button
                        onClick={() => updateCart(item.id, item.quantity + 1)}
                        className="w-6 h-6 flex items-center justify-center text-slate-500 hover:text-slate-700 hover:bg-slate-200 rounded"
                      >
                        <Plus className="h-3 w-3" />
                      </button>
                      <span className="text-xs text-slate-400 w-16">{item.unit}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Delivery Location */}
            <div>
              <h3 className="text-sm font-medium text-slate-700 mb-3 flex items-center gap-2">
                <MapPin className="h-4 w-4" />
                Delivery Location
              </h3>
              
              <div className="space-y-3">
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setDeliveryType('existing')}
                    className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                      deliveryType === 'existing'
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                        : 'border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    <Building2 className="h-4 w-4 inline mr-2" />
                    Registered Site
                  </button>
                  <button
                    type="button"
                    onClick={() => setDeliveryType('new')}
                    className={`flex-1 px-4 py-2 rounded-lg text-sm font-medium border transition-all ${
                      deliveryType === 'new'
                        ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                        : 'border-slate-200 text-slate-600 hover:border-slate-300'
                    }`}
                  >
                    <MapPin className="h-4 w-4 inline mr-2" />
                    New Location
                  </button>
                </div>

                {deliveryType === 'existing' ? (
                  <select
                    value={selectedSite}
                    onChange={(e) => setSelectedSite(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                    data-testid="site-select"
                  >
                    <option value="">Select delivery site...</option>
                    {sites.map(site => (
                      <option key={site.id} value={site.id}>
                        {site.name} - {site.city || site.address}
                      </option>
                    ))}
                  </select>
                ) : (
                  <div className="space-y-3 bg-slate-50 p-4 rounded-lg">
                    <input
                      type="text"
                      placeholder="Address *"
                      value={newLocation.address}
                      onChange={(e) => setNewLocation({ ...newLocation, address: e.target.value })}
                      className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      data-testid="new-address"
                    />
                    <div className="grid grid-cols-2 gap-3">
                      <input
                        type="text"
                        placeholder="City"
                        value={newLocation.city}
                        onChange={(e) => setNewLocation({ ...newLocation, city: e.target.value })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                      <input
                        type="text"
                        placeholder="Pincode"
                        value={newLocation.pincode}
                        onChange={(e) => setNewLocation({ ...newLocation, pincode: e.target.value })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <input
                        type="text"
                        placeholder="Contact Person *"
                        value={newLocation.contact_person}
                        onChange={(e) => setNewLocation({ ...newLocation, contact_person: e.target.value })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        data-testid="contact-person"
                      />
                      <input
                        type="text"
                        placeholder="Contact Phone *"
                        value={newLocation.contact_phone}
                        onChange={(e) => setNewLocation({ ...newLocation, contact_phone: e.target.value })}
                        className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                        data-testid="contact-phone"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Notes */}
            <div>
              <label className="text-sm font-medium text-slate-700 mb-2 block">
                Notes / Special Instructions (Optional)
              </label>
              <textarea
                value={orderNotes}
                onChange={(e) => setOrderNotes(e.target.value)}
                placeholder="e.g., Urgent, Deliver before 4 PM, Use specific brand..."
                className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
                rows={2}
                data-testid="order-notes"
              />
            </div>

            {/* Submit */}
            <div className="flex justify-end gap-3 pt-2">
              <Button 
                variant="outline" 
                onClick={() => setOrderModalOpen(false)}
                disabled={orderLoading}
              >
                Cancel
              </Button>
              <Button 
                onClick={handlePlaceOrder}
                disabled={orderLoading || getCartCount() === 0}
                className="bg-emerald-600 hover:bg-emerald-700"
                data-testid="submit-order-btn"
              >
                {orderLoading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2" />
                    Placing Order...
                  </>
                ) : (
                  <>
                    <ShoppingCart className="h-4 w-4 mr-2" />
                    Place Order
                  </>
                )}
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default CompanyOfficeSupplies;
