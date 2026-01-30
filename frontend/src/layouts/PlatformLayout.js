import { useState, useEffect } from 'react';
import { Outlet, NavLink, useNavigate, useLocation } from 'react-router-dom';
import { 
  Shield, LayoutDashboard, Building2, Settings, LogOut, 
  Menu, X, Users, CreditCard, FileText, ChevronDown, ScrollText
} from 'lucide-react';
import { toast } from 'sonner';

const navItems = [
  { path: '/platform/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/platform/organizations', label: 'Organizations', icon: Building2 },
  { path: '/platform/billing', label: 'Revenue & Billing', icon: CreditCard },
  { path: '/platform/admins', label: 'Platform Admins', icon: Users },
  { path: '/platform/audit-logs', label: 'Audit Logs', icon: ScrollText },
  { path: '/platform/settings', label: 'Settings', icon: Settings },
];

export default function PlatformLayout() {
  const [admin, setAdmin] = useState(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const token = localStorage.getItem('platformToken');
    const adminData = localStorage.getItem('platformAdmin');
    
    if (!token || !adminData) {
      navigate('/platform/login');
      return;
    }
    
    try {
      setAdmin(JSON.parse(adminData));
    } catch {
      navigate('/platform/login');
    }
  }, [navigate]);

  const handleLogout = () => {
    localStorage.removeItem('platformToken');
    localStorage.removeItem('platformAdmin');
    toast.success('Logged out successfully');
    navigate('/platform/login');
  };

  if (!admin) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-purple-500"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-900" data-testid="platform-layout">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/60 z-40 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        fixed top-0 left-0 z-50 h-full w-64 bg-slate-800 border-r border-slate-700
        transform transition-transform duration-300 ease-in-out
        ${sidebarOpen ? 'translate-x-0' : '-translate-x-full'}
        lg:translate-x-0
      `}>
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-slate-700">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-violet-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-white">Platform</span>
              <span className="text-xs text-slate-400 block">Super Admin</span>
            </div>
          </div>
          <button 
            className="lg:hidden text-slate-400 hover:text-white"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation */}
        <nav className="p-4 space-y-1">
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              onClick={() => setSidebarOpen(false)}
              className={({ isActive }) => `
                flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
                ${isActive 
                  ? 'bg-purple-500/20 text-purple-400' 
                  : 'text-slate-400 hover:bg-slate-700/50 hover:text-white'
                }
              `}
            >
              <item.icon className="w-5 h-5" />
              {item.label}
            </NavLink>
          ))}
        </nav>

        {/* Admin Info */}
        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-slate-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-10 h-10 bg-purple-500/20 rounded-full flex items-center justify-center">
              <span className="text-purple-400 font-semibold">
                {admin.name?.charAt(0)?.toUpperCase() || 'A'}
              </span>
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-white truncate">{admin.name}</p>
              <p className="text-xs text-slate-400 truncate">{admin.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-slate-700/50 hover:bg-red-500/20 text-slate-400 hover:text-red-400 rounded-lg text-sm transition-colors"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="lg:pl-64">
        {/* Top Bar */}
        <header className="h-16 bg-slate-800/80 backdrop-blur-sm border-b border-slate-700 flex items-center justify-between px-4 lg:px-6 sticky top-0 z-30">
          <button 
            className="lg:hidden text-slate-400 hover:text-white"
            onClick={() => setSidebarOpen(true)}
          >
            <Menu className="w-6 h-6" />
          </button>
          
          <div className="flex-1 lg:flex-none" />
          
          <div className="flex items-center gap-4">
            <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-400 rounded-full font-medium">
              {admin.role?.replace('_', ' ').toUpperCase()}
            </span>
          </div>
        </header>

        {/* Page Content */}
        <main className="p-4 lg:p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
