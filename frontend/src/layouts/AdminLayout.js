import { useEffect, useState } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Building2, Users, Laptop, Wrench, 
  FileCheck, Settings, LogOut, Shield, Menu, X, ChevronRight, ChevronDown, Database, History, FileText, MapPin, Package, Key, ShoppingBag, ClipboardList, UserCircle, Mail, Keyboard, Layers, AlertTriangle, Briefcase, HardDrive, FileBarChart, Globe, Lock, Sparkles, Inbox, Monitor, BookOpen, UserCog
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useSettings } from '../context/SettingsContext';
import { useBranding } from '../contexts/BrandingContext';
import { Button } from '../components/ui/button';
import UniversalSearch from '../components/UniversalSearch';
import CompanySwitcher from '../components/CompanySwitcher';

// Grouped navigation structure
const navGroups = [
  {
    id: 'main',
    items: [
      { path: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
      { path: '/admin/usage', label: 'Usage & Limits', icon: Layers },
      { path: '/admin/service-requests', label: 'Service Tickets', icon: Wrench },
      { path: '/admin/renewal-alerts', label: 'Renewal Alerts', icon: AlertTriangle },
      { path: '/admin/credentials', label: 'Credentials', icon: Lock },
    ]
  },
  {
    id: 'organization',
    label: 'Organization',
    icon: Building2,
    items: [
      { path: '/admin/companies', label: 'Companies', icon: Building2 },
      { path: '/admin/company-domains', label: 'Email Domains', icon: Globe },
      { path: '/admin/sites', label: 'Sites', icon: MapPin },
      { path: '/admin/users', label: 'Users', icon: Users },
      { path: '/admin/employees', label: 'Employees', icon: UserCircle },
      { path: '/admin/team', label: 'Team Members', icon: UserCog },
      { path: '/admin/staff', label: 'Staff Management', icon: Shield },
    ]
  },
  {
    id: 'assets',
    label: 'Assets',
    icon: Laptop,
    items: [
      { path: '/admin/devices', label: 'Devices', icon: Laptop },
      { path: '/admin/accessories', label: 'Accessories', icon: Keyboard },
      { path: '/admin/asset-groups', label: 'Asset Groups', icon: Layers },
      { path: '/admin/parts', label: 'Parts', icon: Wrench },
      { path: '/admin/deployments', label: 'Deployments', icon: Package },
      { path: '/admin/device-catalog', label: 'Device Catalog', icon: Sparkles },
    ]
  },
  {
    id: 'contracts',
    label: 'Contracts & Licenses',
    icon: FileText,
    items: [
      { path: '/admin/licenses', label: 'Licenses', icon: Key },
      { path: '/admin/amc-contracts', label: 'AMC Contracts', icon: FileText },
      { path: '/admin/amc-requests', label: 'AMC Requests', icon: FileText },
      { path: '/admin/subscriptions', label: 'Subscriptions', icon: Mail },
      { path: '/admin/internet-services', label: 'Internet Services', icon: Globe },
      { path: '/admin/service-history', label: 'Service History', icon: History },
    ]
  },
  {
    id: 'supplies',
    label: 'Office Supplies',
    icon: ShoppingBag,
    items: [
      { path: '/admin/supply-products', label: 'Products', icon: ShoppingBag },
      { path: '/admin/supply-orders', label: 'Orders', icon: ClipboardList },
    ]
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    items: [
      { path: '/admin/organization', label: 'Organization', icon: Building2 },
      { path: '/admin/custom-domains', label: 'Custom Domains', icon: Globe },
      { path: '/admin/email-whitelabel', label: 'Email Settings', icon: Mail },
      { path: '/admin/knowledge-base', label: 'Knowledge Base', icon: BookOpen },
      { path: '/admin/static-pages', label: 'Static Pages', icon: FileText },
      { path: '/admin/master-data', label: 'Master Data', icon: Database },
      { path: '/admin/ticketing-settings', label: 'Ticketing Config', icon: Inbox },
      { path: '/admin/integrations/tactical-rmm', label: 'Tactical RMM', icon: Monitor },
      { path: '/admin/integrations/tgms', label: 'Remote Management', icon: Laptop },
      { path: '/admin/settings', label: 'Settings', icon: Settings },
    ]
  },
];

// Flatten for finding current page
const allNavItems = navGroups.flatMap(g => g.items);

const AdminLayout = () => {
  const { admin, loading, isAuthenticated, logout, authError } = useAuth();
  const { settings } = useSettings();
  const { branding, organization } = useBranding();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [featureFlags, setFeatureFlags] = useState({});
  const [expandedGroups, setExpandedGroups] = useState(() => {
    // Auto-expand group containing current path
    const currentGroup = navGroups.find(g => g.items.some(i => location.pathname.startsWith(i.path)));
    return currentGroup ? { [currentGroup.id]: true } : { main: true };
  });

  // Fetch feature flags
  useEffect(() => {
    const fetchFeatureFlags = async () => {
      try {
        const token = localStorage.getItem('admin_token');
        if (!token) return;
        
        const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/admin/feature-flags`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (response.ok) {
          const data = await response.json();
          setFeatureFlags(data.feature_flags || {});
        }
      } catch (error) {
        console.error('Failed to fetch feature flags:', error);
      }
    };
    
    if (isAuthenticated) {
      fetchFeatureFlags();
    }
  }, [isAuthenticated]);

  // Filter nav items based on feature flags
  const getFilteredNavGroups = () => {
    return navGroups.map(group => ({
      ...group,
      items: group.items.filter(item => {
        // Hide Tactical RMM if feature flag is disabled
        if (item.path === '/admin/integrations/tactical-rmm' && !featureFlags.tactical_rmm) {
          return false;
        }
        // Hide TGMS if feature flag is disabled
        if (item.path === '/admin/integrations/tgms' && featureFlags.tgms === false) {
          return false;
        }
        // Hide Staff Management if feature flag is disabled
        if (item.path === '/admin/staff' && featureFlags.staff_module === false) {
          return false;
        }
        // Hide Knowledge Base if feature flag is disabled
        if (item.path === '/admin/knowledge-base' && featureFlags.knowledge_base === false) {
          return false;
        }
        // Hide Custom Domains if feature flag is disabled
        if (item.path === '/admin/custom-domains' && featureFlags.custom_domains === false) {
          return false;
        }
        return true;
      })
    }));
  };

  const filteredNavGroups = getFilteredNavGroups();

  // Auto-expand group when navigating - must be before any early returns
  useEffect(() => {
    const currentGroup = navGroups.find(g => g.items.some(i => location.pathname.startsWith(i.path)));
    if (currentGroup && !expandedGroups[currentGroup.id]) {
      setExpandedGroups(prev => ({ ...prev, [currentGroup.id]: true }));
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      // Store the intended destination to redirect after login
      const currentPath = location.pathname;
      if (currentPath !== '/admin/login' && currentPath !== '/admin/setup') {
        sessionStorage.setItem('redirectAfterLogin', currentPath);
      }
      navigate('/admin/login');
    }
  }, [loading, isAuthenticated, navigate, location.pathname]);

  if (loading) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
        <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin"></div>
        <p className="mt-4 text-sm text-slate-500">Loading...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return null;
  }

  // Show warning banner if there's an auth error but user is still authenticated
  const showAuthWarning = authError && isAuthenticated;

  const handleLogout = () => {
    logout();
    navigate('/admin/login');
  };

  const toggleGroup = (groupId) => {
    setExpandedGroups(prev => ({
      ...prev,
      [groupId]: !prev[groupId]
    }));
  };

  const currentPage = allNavItems.find(item => location.pathname.startsWith(item.path))?.label || 'Dashboard';

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Mobile Header */}
      <div className="lg:hidden bg-white border-b border-slate-100 px-4 py-3 flex items-center justify-between sticky top-0 z-40">
        <div className="flex items-center gap-3">
          {(settings.logo_base64 || settings.logo_url) ? (
            <img 
              src={settings.logo_base64 || settings.logo_url} 
              alt="Logo" 
              className="h-8 w-auto"
            />
          ) : (
            <Shield className="h-7 w-7 text-[#0F62FE]" />
          )}
          <span className="font-semibold text-slate-900">{currentPage}</span>
        </div>
        <div className="flex items-center gap-2">
          <UniversalSearch />
          <Button 
            variant="ghost" 
            size="icon"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            data-testid="mobile-menu-btn"
          >
            {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
        </div>
      </div>

      {/* Mobile Sidebar Overlay */}
      {sidebarOpen && (
        <div 
          className="lg:hidden fixed inset-0 bg-black/50 z-40"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 h-full w-64 bg-white border-r border-slate-100 z-50
        transform transition-transform duration-300 ease-in-out
        lg:translate-x-0 ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
        <div className="flex flex-col h-full">
          {/* Logo - Uses organization branding if available */}
          <div className="p-6 border-b border-slate-100">
            <div className="flex items-center gap-3">
              {(branding.logo_base64 || branding.logo_url || settings.logo_base64 || settings.logo_url) ? (
                <img 
                  src={branding.logo_base64 || branding.logo_url || settings.logo_base64 || settings.logo_url} 
                  alt="Logo" 
                  className="h-8 w-auto"
                />
              ) : (
                <div 
                  className="h-8 w-8 rounded-lg flex items-center justify-center"
                  style={{ backgroundColor: branding.accent_color || '#0F62FE' }}
                >
                  <Shield className="h-5 w-5 text-white" />
                </div>
              )}
              <div>
                <span className="font-semibold text-slate-900 text-sm">
                  {branding.company_name || settings.company_name || 'Warranty Portal'}
                </span>
                <p className="text-xs text-slate-500">
                  {organization?.subscription?.plan ? (
                    <span className="capitalize">{organization.subscription.plan} Plan</span>
                  ) : 'Admin Portal'}
                </p>
              </div>
            </div>
          </div>

          {/* Company Switcher - For MSP users to switch between companies */}
          <div className="px-3 py-2 border-b border-slate-100">
            <CompanySwitcher />
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
            {filteredNavGroups.map((group) => (
              <div key={group.id}>
                {/* Main items without group header */}
                {group.id === 'main' ? (
                  group.items.map((item) => (
                    <NavLink
                      key={item.path}
                      to={item.path}
                      onClick={() => setSidebarOpen(false)}
                      className={({ isActive }) => `
                        sidebar-link ${isActive ? 'active' : ''}
                      `}
                      data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
                    >
                      <item.icon className="h-4 w-4" />
                      {item.label}
                    </NavLink>
                  ))
                ) : (
                  <>
                    {/* Collapsible group header */}
                    <button
                      onClick={() => toggleGroup(group.id)}
                      className="w-full flex items-center justify-between px-3 py-2 mt-2 text-xs font-semibold text-slate-500 hover:text-slate-700 hover:bg-slate-50 rounded-lg transition-colors"
                    >
                      <div className="flex items-center gap-2">
                        <group.icon className="h-3.5 w-3.5" />
                        <span className="uppercase tracking-wider">{group.label}</span>
                      </div>
                      {expandedGroups[group.id] ? (
                        <ChevronDown className="h-3.5 w-3.5" />
                      ) : (
                        <ChevronRight className="h-3.5 w-3.5" />
                      )}
                    </button>
                    
                    {/* Group items */}
                    {expandedGroups[group.id] && (
                      <div className="ml-2 pl-2 border-l border-slate-100 space-y-0.5">
                        {group.items.map((item) => (
                          <NavLink
                            key={item.path}
                            to={item.path}
                            onClick={() => setSidebarOpen(false)}
                            className={({ isActive }) => `
                              sidebar-link text-sm py-1.5 ${isActive ? 'active' : ''}
                            `}
                            data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
                          >
                            <item.icon className="h-3.5 w-3.5" />
                            {item.label}
                          </NavLink>
                        ))}
                      </div>
                    )}
                  </>
                )}
              </div>
            ))}
          </nav>

          {/* User & Logout */}
          <div className="p-4 border-t border-slate-100">
            <div className="flex items-center gap-3 px-4 py-3 mb-2">
              <div className="w-8 h-8 rounded-full bg-[#E8F0FE] flex items-center justify-center">
                <span className="text-sm font-medium text-[#0F62FE]">
                  {admin?.name?.charAt(0).toUpperCase() || 'A'}
                </span>
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-slate-900 truncate">{admin?.name}</p>
                <p className="text-xs text-slate-500 truncate">{admin?.email}</p>
              </div>
            </div>
            <Button 
              variant="ghost" 
              className="w-full justify-start text-slate-600 hover:text-red-600 hover:bg-red-50"
              onClick={handleLogout}
              data-testid="logout-btn"
            >
              <LogOut className="h-4 w-4 mr-3" />
              Sign Out
            </Button>
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="lg:ml-64 min-h-screen">
        {/* Auth Warning Banner */}
        {showAuthWarning && (
          <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-sm text-amber-800 flex items-center justify-center gap-2">
            <span>⚠️ {authError}</span>
            <button 
              onClick={() => window.location.reload()} 
              className="underline hover:no-underline"
            >
              Retry
            </button>
          </div>
        )}
        
        {/* Desktop Header */}
        <header className="hidden lg:flex items-center justify-between bg-white border-b border-slate-100 px-8 py-4 sticky top-0 z-30">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <a href="/" className="hover:text-slate-700">Portal</a>
              <ChevronRight className="h-3 w-3" />
              <span className="text-slate-900 font-medium">{currentPage}</span>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <UniversalSearch />
            <a 
              href="/" 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-sm text-slate-500 hover:text-[#0F62FE] transition-colors"
            >
              View Public Portal →
            </a>
          </div>
        </header>

        {/* Page Content */}
        <div className="p-6 lg:p-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
};

export default AdminLayout;
