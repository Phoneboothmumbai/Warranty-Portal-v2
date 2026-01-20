import { useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Building2, Users, Laptop, Wrench, 
  FileCheck, Settings, LogOut, Shield, Menu, X, ChevronRight, Database, History, FileText, MapPin, Package, Key, ShoppingBag, ClipboardList, UserCircle, Mail, Keyboard, Layers, AlertTriangle
} from 'lucide-react';
import { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useSettings } from '../context/SettingsContext';
import { Button } from '../components/ui/button';
import UniversalSearch from '../components/UniversalSearch';

const navItems = [
  { path: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/admin/renewal-alerts', label: 'Renewal Alerts', icon: AlertTriangle },
  { path: '/admin/companies', label: 'Companies', icon: Building2 },
  { path: '/admin/sites', label: 'Sites', icon: MapPin },
  { path: '/admin/users', label: 'Users', icon: Users },
  { path: '/admin/employees', label: 'Employees', icon: UserCircle },
  { path: '/admin/subscriptions', label: 'Subscriptions', icon: Mail },
  { type: 'divider', label: 'Assets' },
  { path: '/admin/devices', label: 'Devices', icon: Laptop },
  { path: '/admin/accessories', label: 'Accessories', icon: Keyboard },
  { path: '/admin/asset-groups', label: 'Asset Groups', icon: Layers },
  { path: '/admin/deployments', label: 'Deployments', icon: Package },
  { path: '/admin/parts', label: 'Parts', icon: Wrench },
  { path: '/admin/licenses', label: 'Licenses', icon: Key },
  { path: '/admin/service-history', label: 'Service History', icon: History },
  { path: '/admin/amc-contracts', label: 'AMC Contracts', icon: FileText },
  { type: 'divider', label: 'Office Supplies' },
  { path: '/admin/supply-products', label: 'Products', icon: ShoppingBag },
  { path: '/admin/supply-orders', label: 'Orders', icon: ClipboardList },
  { type: 'divider', label: 'Settings' },
  { path: '/admin/master-data', label: 'Master Data', icon: Database },
  { path: '/admin/settings', label: 'Settings', icon: Settings },
];

const AdminLayout = () => {
  const { admin, loading, isAuthenticated, logout, authError } = useAuth();
  const { settings } = useSettings();
  const navigate = useNavigate();
  const location = useLocation();
  const [sidebarOpen, setSidebarOpen] = useState(false);

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

  const currentPage = navItems.find(item => location.pathname.startsWith(item.path))?.label || 'Dashboard';

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
          {/* Logo */}
          <div className="p-6 border-b border-slate-100">
            <div className="flex items-center gap-3">
              {(settings.logo_base64 || settings.logo_url) ? (
                <img 
                  src={settings.logo_base64 || settings.logo_url} 
                  alt="Logo" 
                  className="h-8 w-auto"
                />
              ) : (
                <Shield className="h-8 w-8 text-[#0F62FE]" />
              )}
              <div>
                <span className="font-semibold text-slate-900 text-sm">{settings.company_name}</span>
                <p className="text-xs text-slate-500">Admin Portal</p>
              </div>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
            {navItems.map((item, index) => (
              item.type === 'divider' ? (
                <div key={`divider-${index}`} className="pt-4 pb-2">
                  <p className="px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                    {item.label}
                  </p>
                </div>
              ) : (
                <NavLink
                  key={item.path}
                  to={item.path}
                  onClick={() => setSidebarOpen(false)}
                  className={({ isActive }) => `
                    sidebar-link ${isActive ? 'active' : ''}
                  `}
                  data-testid={`nav-${item.label.toLowerCase()}`}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </NavLink>
              )
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
