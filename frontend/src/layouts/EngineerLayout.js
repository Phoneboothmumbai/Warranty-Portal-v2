import { useEffect } from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import { LayoutDashboard, Calendar, LogOut, Wrench, User } from 'lucide-react';
import { useEngineerAuth } from '../context/EngineerAuthContext';
import { Button } from '../components/ui/button';

const navItems = [
  { path: '/engineer/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/engineer/calendar', label: 'My Calendar', icon: Calendar },
];

export default function EngineerLayout() {
  const { engineer, logout, isAuthenticated } = useEngineerAuth();
  const navigate = useNavigate();

  useEffect(() => {
    if (!isAuthenticated) navigate('/engineer');
  }, [isAuthenticated, navigate]);

  if (!isAuthenticated) return null;

  return (
    <div className="flex h-screen bg-slate-50" data-testid="engineer-layout">
      {/* Sidebar */}
      <aside className="w-56 bg-slate-900 text-white flex flex-col shrink-0">
        <div className="p-4 border-b border-slate-700">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-orange-500 flex items-center justify-center">
              <Wrench className="w-4 h-4 text-white" />
            </div>
            <div>
              <p className="text-sm font-semibold">Tech Portal</p>
              <p className="text-[10px] text-slate-400">{engineer?.name || 'Technician'}</p>
            </div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1">
          {navItems.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm transition-colors ${
                  isActive ? 'bg-slate-700 text-white font-medium' : 'text-slate-400 hover:text-white hover:bg-slate-800'
                }`
              }
              data-testid={`nav-${item.label.toLowerCase().replace(/\s/g, '-')}`}
            >
              <item.icon className="w-4 h-4" />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-slate-700">
          <div className="flex items-center gap-2 px-3 py-2 mb-2">
            <div className="w-7 h-7 rounded-full bg-slate-700 flex items-center justify-center">
              <User className="w-3.5 h-3.5 text-slate-300" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">{engineer?.name}</p>
              <p className="text-[10px] text-slate-500 truncate">{engineer?.email}</p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="w-full text-slate-400 hover:text-white hover:bg-slate-800 justify-start"
            onClick={() => { logout(); navigate('/engineer'); }}
            data-testid="engineer-logout"
          >
            <LogOut className="w-4 h-4 mr-2" /> Logout
          </Button>
        </div>
      </aside>
      {/* Main Content */}
      <main className="flex-1 overflow-auto p-6">
        <Outlet />
      </main>
    </div>
  );
}
