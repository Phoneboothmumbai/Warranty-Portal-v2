import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useSettings } from '../context/SettingsContext';
import { useBranding } from '../contexts/BrandingContext';
import CompanySwitcher from '../components/CompanySwitcher';
import UniversalSearch from '../components/UniversalSearch';
import NotificationBell from '../components/NotificationBell';
import { Button } from '../components/ui/button';
import {
  LayoutDashboard, Building2, Users, Laptop, Wrench,
  FileCheck, Settings, LogOut, Shield, Menu, X, ChevronRight,
  Database, History, FileText, MapPin, Package, Key, ShoppingBag,
  ClipboardList, UserCircle, Mail, Layers, AlertTriangle, Briefcase,
  HardDrive, FileBarChart, Globe, Lock, Sparkles, Monitor, BookOpen,
  UserCog, Keyboard, MessageSquare, User, Calendar, IndianRupee,
  BarChart3, Headphones, Cable, Activity, FolderKanban
} from 'lucide-react';

const API = process.env.REACT_APP_BACKEND_URL;

// ── Module definitions with their sub-pages ──
const MODULES = [
  {
    id: 'dashboard',
    label: 'Dashboard',
    icon: LayoutDashboard,
    path: '/admin/dashboard',
    noSidebar: true,
    items: [],
  },
  {
    id: 'service',
    label: 'Service Desk',
    icon: Headphones,
    path: '/admin/service-requests',
    items: [
      { path: '/admin/service-requests', label: 'Tickets', icon: Wrench },
      { path: '/admin/technician-dashboard', label: 'Workforce', icon: User },
      { path: '/admin/calendar', label: 'Calendar', icon: Calendar },
      { path: '/admin/ticketing-config', label: 'Ticketing Setup', icon: ClipboardList },
      { path: '/admin/renewal-alerts', label: 'Renewal Alerts', icon: AlertTriangle },
    ],
  },
  {
    id: 'projects',
    label: 'Projects',
    icon: FolderKanban,
    path: '/admin/projects',
    items: [
      { path: '/admin/projects', label: 'All Projects', icon: FolderKanban },
      { path: '/admin/project-templates', label: 'Task Templates', icon: ClipboardList },
    ],
  },
  {
    id: 'assets',
    label: 'Assets',
    icon: Laptop,
    path: '/admin/devices',
    items: [
      { path: '/admin/devices', label: 'Devices', icon: Laptop },
      { path: '/admin/accessories', label: 'Accessories', icon: Keyboard },
      { path: '/admin/asset-groups', label: 'Asset Groups', icon: Layers },
      { path: '/admin/parts', label: 'Parts', icon: Wrench },
      { path: '/admin/deployments', label: 'Deployments', icon: Package },
      { path: '/admin/device-catalog', label: 'Device Catalog', icon: Sparkles },
    ],
  },
  {
    id: 'contracts',
    label: 'Contracts',
    icon: FileText,
    path: '/admin/amc-contracts',
    items: [
      { path: '/admin/amc-contracts', label: 'AMC Contracts', icon: FileText },
      { path: '/admin/amc-requests', label: 'AMC Requests', icon: FileCheck },
      { path: '/admin/licenses', label: 'Licenses', icon: Key },
      { path: '/admin/subscriptions', label: 'Subscriptions', icon: Mail },
      { path: '/admin/internet-services', label: 'Internet Services', icon: Globe },
      { path: '/admin/service-history', label: 'Service History', icon: History },
    ],
  },
  {
    id: 'analytics',
    label: 'Analytics',
    icon: BarChart3,
    path: '/admin/analytics',
    noSidebar: true,
    items: [],
  },
  {
    id: 'settings',
    label: 'Settings',
    icon: Settings,
    path: '/admin/organization',
    items: [
      { path: '/admin/organization', label: 'Organization', icon: Building2 },
      { path: '/admin/settings', label: 'Portal Settings', icon: Settings },
      { path: '/admin/master-data', label: 'Master Data', icon: Database },
      { path: '/admin/item-master', label: 'Item Master', icon: Package },
      { path: '/admin/knowledge-base', label: 'Knowledge Base', icon: BookOpen },
      { path: '/admin/custom-domains', label: 'Custom Domains', icon: Globe },
      { path: '/admin/credentials', label: 'Credentials', icon: Lock },
      { path: '/admin/supply-products', label: 'Products', icon: ShoppingBag },
      { path: '/admin/supply-orders', label: 'Orders', icon: ClipboardList },
      { path: '/admin/parts-requests', label: 'Parts Requests', icon: Wrench },
      { path: '/admin/pending-bills', label: 'Pending Bills', icon: IndianRupee },
      { path: '/admin/usage', label: 'Usage & Limits', icon: Layers },
      { path: '/admin/integrations/watchtower', label: 'WatchTower', icon: Monitor, flag: 'watchtower' },
      { path: '/admin/integrations/moltbot', label: 'MoltBot (Chat)', icon: MessageSquare, flag: 'moltbot' },
      { path: '/admin/integrations/tgms', label: 'Remote Mgmt', icon: Cable, flag: 'tgms' },
    ],
  },
];

// All nav items flattened for route matching
const allNavItems = MODULES.flatMap(m => [
  { path: m.path, label: m.label },
  ...m.items
]);

// Find which module a path belongs to
function getActiveModule(pathname) {
  for (const mod of MODULES) {
    if (mod.items.some(i => pathname.startsWith(i.path))) return mod.id;
    if (pathname.startsWith(mod.path)) return mod.id;
  }
  return 'dashboard';
}

const AdminLayout = () => {
  const { admin, loading, isAuthenticated, logout, authError } = useAuth();
  const { settings } = useSettings();
  const { branding, organization } = useBranding();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [featureFlags, setFeatureFlags] = useState({});

  const activeModuleId = getActiveModule(location.pathname);
  const activeModule = MODULES.find(m => m.id === activeModuleId) || MODULES[0];
  const hasSidebar = !activeModule.noSidebar && activeModule.items.length > 0;

  // Fetch feature flags
  useEffect(() => {
    const fetchFlags = async () => {
      try {
        const token = localStorage.getItem('admin_token');
        if (!token) return;
        const res = await fetch(`${API}/api/admin/feature-flags`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok) {
          const data = await res.json();
          setFeatureFlags(data.feature_flags || {});
        }
      } catch (e) { /* ignore */ }
    };
    if (isAuthenticated) fetchFlags();
  }, [isAuthenticated]);

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      const cur = location.pathname;
      if (cur !== '/admin/login' && cur !== '/admin/setup') {
        sessionStorage.setItem('redirectAfterLogin', cur);
      }
      navigate('/admin/login');
    }
  }, [loading, isAuthenticated, navigate, location.pathname]);

  // Close mobile menu on navigation
  useEffect(() => { setMobileMenuOpen(false); }, [location.pathname]);

  if (loading) return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-slate-50">
      <div className="w-8 h-8 border-4 border-[#0F62FE] border-t-transparent rounded-full animate-spin" />
      <p className="mt-4 text-sm text-slate-500">Loading...</p>
    </div>
  );
  if (!isAuthenticated) return null;

  const showAuthWarning = authError && isAuthenticated;

  const filteredItems = (activeModule.items || []).filter(item => {
    if (item.flag) {
      if (item.flag === 'tgms' && featureFlags.tgms === false) return false;
      if (item.flag === 'watchtower' && !featureFlags.watchtower) return false;
      if (item.flag === 'moltbot' && !featureFlags.moltbot) return false;
    }
    if (item.path === '/admin/knowledge-base' && featureFlags.knowledge_base === false) return false;
    if (item.path === '/admin/custom-domains' && featureFlags.custom_domains === false) return false;
    return true;
  });

  const currentPage = allNavItems.find(item => location.pathname.startsWith(item.path))?.label || 'Dashboard';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* ── TOP BAR ── */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-50">
        <div className="flex items-center h-14 px-4 lg:px-6">
          {/* Logo */}
          <div className="flex items-center gap-2.5 mr-6 shrink-0">
            {(branding.logo_base64 || branding.logo_url || settings.logo_base64 || settings.logo_url) ? (
              <img
                src={branding.logo_base64 || branding.logo_url || settings.logo_base64 || settings.logo_url}
                alt="Logo" className="h-7 w-auto"
              />
            ) : (
              <div className="h-7 w-7 rounded-md flex items-center justify-center"
                style={{ backgroundColor: branding.accent_color || '#0F62FE' }}>
                <Shield className="h-4 w-4 text-white" />
              </div>
            )}
            <span className="font-semibold text-slate-900 text-sm hidden sm:block">
              {settings.company_name || 'aftersales.support'}
            </span>
          </div>

          {/* Module tabs — desktop */}
          <nav className="hidden lg:flex items-center gap-0.5 flex-1" data-testid="module-tabs">
            {MODULES.map(mod => {
              const isActive = activeModuleId === mod.id;
              return (
                <NavLink
                  key={mod.id}
                  to={mod.path}
                  className={`flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded-md transition-all ${
                    isActive
                      ? 'bg-[#0F62FE] text-white shadow-sm'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                  data-testid={`module-${mod.id}`}
                >
                  <mod.icon className="w-4 h-4" />
                  {mod.label}
                </NavLink>
              );
            })}
          </nav>

          {/* Right side */}
          <div className="flex items-center gap-2 ml-auto">
            <div className="hidden md:block"><CompanySwitcher /></div>
            <UniversalSearch />
            <NotificationBell />
            <div className="hidden lg:flex items-center gap-2 ml-2 pl-3 border-l border-slate-200">
              <div className="w-7 h-7 rounded-full bg-[#E8F0FE] flex items-center justify-center">
                <span className="text-xs font-semibold text-[#0F62FE]">{admin?.name?.charAt(0).toUpperCase() || 'A'}</span>
              </div>
              <span className="text-xs text-slate-600 max-w-[100px] truncate">{admin?.name}</span>
              <button onClick={() => { logout(); navigate('/admin/login'); }} className="text-slate-400 hover:text-red-500 transition-colors" data-testid="logout-btn" title="Sign Out">
                <LogOut className="h-4 w-4" />
              </button>
            </div>
            {/* Mobile hamburger */}
            <Button variant="ghost" size="icon" className="lg:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)} data-testid="mobile-menu-btn">
              {mobileMenuOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
            </Button>
          </div>
        </div>

        {/* Mobile Module Tabs (horizontal scroll) */}
        <div className="lg:hidden overflow-x-auto flex items-center gap-1 px-4 pb-2 scrollbar-thin">
          {MODULES.map(mod => {
            const isActive = activeModuleId === mod.id;
            return (
              <NavLink
                key={mod.id}
                to={mod.path}
                className={`flex items-center gap-1 px-2.5 py-1.5 text-xs font-medium rounded-md whitespace-nowrap transition-all ${
                  isActive ? 'bg-[#0F62FE] text-white' : 'text-slate-500 hover:bg-slate-100'
                }`}
              >
                <mod.icon className="w-3.5 h-3.5" />
                {mod.label}
              </NavLink>
            );
          })}
        </div>
      </header>

      {/* ── MOBILE OVERLAY ── */}
      {mobileMenuOpen && (
        <>
          <div className="lg:hidden fixed inset-0 bg-black/50 z-40" onClick={() => setMobileMenuOpen(false)} />
          <div className="lg:hidden fixed top-0 right-0 w-72 h-full bg-white z-50 shadow-xl overflow-y-auto">
            <div className="p-4 border-b flex items-center justify-between">
              <span className="font-semibold text-sm">Menu</span>
              <button onClick={() => setMobileMenuOpen(false)}><X className="h-5 w-5 text-slate-400" /></button>
            </div>
            <div className="p-3">
              <CompanySwitcher />
            </div>
            <nav className="p-3 space-y-4">
              {MODULES.map(mod => (
                <div key={mod.id}>
                  <NavLink to={mod.path} className={({ isActive }) => `flex items-center gap-2 px-3 py-2 text-sm font-semibold rounded-md ${isActive ? 'text-[#0F62FE] bg-blue-50' : 'text-slate-700'}`}>
                    <mod.icon className="w-4 h-4" />{mod.label}
                  </NavLink>
                  {activeModuleId === mod.id && mod.items.length > 0 && (
                    <div className="ml-4 mt-1 space-y-0.5 border-l border-slate-100 pl-3">
                      {mod.items.filter(i => !i.flag || featureFlags[i.flag]).map(item => (
                        <NavLink key={item.path} to={item.path} onClick={() => setMobileMenuOpen(false)}
                          className={({ isActive }) => `flex items-center gap-2 px-2 py-1.5 text-xs rounded ${isActive ? 'text-[#0F62FE] bg-blue-50 font-medium' : 'text-slate-500 hover:text-slate-700'}`}>
                          <item.icon className="w-3.5 h-3.5" />{item.label}
                        </NavLink>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </nav>
            <div className="p-4 border-t mt-4">
              <div className="flex items-center gap-3 mb-3">
                <div className="w-8 h-8 rounded-full bg-[#E8F0FE] flex items-center justify-center">
                  <span className="text-sm font-medium text-[#0F62FE]">{admin?.name?.charAt(0).toUpperCase() || 'A'}</span>
                </div>
                <div><p className="text-sm font-medium">{admin?.name}</p><p className="text-xs text-slate-500">{admin?.email}</p></div>
              </div>
              <Button variant="ghost" className="w-full justify-start text-slate-600 hover:text-red-600" onClick={() => { logout(); navigate('/admin/login'); }}>
                <LogOut className="h-4 w-4 mr-2" />Sign Out
              </Button>
            </div>
          </div>
        </>
      )}

      {/* ── BODY ── */}
      <div className="flex flex-1">
        {/* Context Sidebar — only for modules with sub-pages */}
        {hasSidebar && (
          <aside className="hidden lg:block w-52 bg-white border-r border-slate-100 shrink-0 sticky top-14 h-[calc(100vh-3.5rem)] overflow-y-auto">
            <div className="py-4 px-3">
              <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-widest px-3 mb-2">{activeModule.label}</p>
              <nav className="space-y-0.5">
                {filteredItems.map(item => (
                  <NavLink
                    key={item.path}
                    to={item.path}
                    className={({ isActive }) => `flex items-center gap-2 px-3 py-2 text-sm rounded-md transition-all ${
                      isActive
                        ? 'bg-blue-50 text-[#0F62FE] font-medium'
                        : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                    }`}
                    data-testid={`nav-${item.label.toLowerCase().replace(/\s+/g, '-')}`}
                  >
                    <item.icon className="w-4 h-4 shrink-0" />
                    <span className="truncate">{item.label}</span>
                  </NavLink>
                ))}
              </nav>
            </div>
          </aside>
        )}

        {/* Main Content */}
        <main className="flex-1 min-w-0">
          {showAuthWarning && (
            <div className="bg-amber-50 border-b border-amber-200 px-4 py-2 text-sm text-amber-800 flex items-center justify-center gap-2">
              <span>{authError}</span>
              <button onClick={() => window.location.reload()} className="underline hover:no-underline">Retry</button>
            </div>
          )}
          <div className="p-5 lg:p-7">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;
