import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FolderKanban, 
  Package, 
  Key, 
  FileText, 
  Settings,
  LogOut,
  Zap
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { cn } from '../../lib/utils';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { path: '/projects', label: 'Projects', icon: FolderKanban },
  { path: '/builds', label: 'Builds', icon: Package },
  { path: '/api-keys', label: 'API Keys', icon: Key },
  { path: '/docs', label: 'Documentation', icon: FileText },
  { path: '/settings', label: 'Settings', icon: Settings },
];

export const Sidebar = () => {
  const location = useLocation();
  const { user, logout } = useAuth();

  return (
    <aside className="w-64 h-screen fixed left-0 top-0 glass border-r border-white/10 flex flex-col" data-testid="sidebar">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <Link to="/dashboard" className="flex items-center gap-3" data-testid="sidebar-logo">
          <div className="w-10 h-10 rounded-md bg-primary/20 border border-primary flex items-center justify-center">
            <Zap className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h1 className="font-heading font-bold text-lg text-white">NativiWeb</h1>
            <p className="text-xs text-muted-foreground">Studio</p>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.path || 
            (item.path !== '/dashboard' && location.pathname.startsWith(item.path));
          const Icon = item.icon;
          
          return (
            <Link
              key={item.path}
              to={item.path}
              data-testid={`nav-${item.path.slice(1)}`}
              className={cn(
                "flex items-center gap-3 px-4 py-3 rounded-sm transition-all duration-200",
                isActive 
                  ? "bg-primary/10 text-primary border border-primary/30" 
                  : "text-muted-foreground hover:text-white hover:bg-white/5"
              )}
            >
              <Icon className="w-5 h-5" />
              <span className="font-medium">{item.label}</span>
            </Link>
          );
        })}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-white/10">
        <div className="flex items-center gap-3 px-4 py-3 mb-2">
          <div className="w-8 h-8 rounded-full bg-secondary/20 border border-secondary/30 flex items-center justify-center">
            <span className="text-sm font-bold text-secondary">
              {user?.name?.charAt(0).toUpperCase() || 'U'}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium text-white truncate">{user?.name || 'User'}</p>
            <p className="text-xs text-muted-foreground truncate">{user?.email}</p>
          </div>
        </div>
        <button
          onClick={logout}
          data-testid="logout-btn"
          className="flex items-center gap-3 px-4 py-3 w-full rounded-sm text-muted-foreground hover:text-destructive hover:bg-destructive/10 transition-all"
        >
          <LogOut className="w-5 h-5" />
          <span className="font-medium">Logout</span>
        </button>
      </div>
    </aside>
  );
};

export default Sidebar;
