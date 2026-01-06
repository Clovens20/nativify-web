import Sidebar from './Sidebar';
import { Bell, Search } from 'lucide-react';
import { Input } from '../ui/input';

export const DashboardLayout = ({ children, title, subtitle }) => {
  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      
      {/* Main content area */}
      <main className="ml-64 min-h-screen">
        {/* Top bar */}
        <header className="h-16 glass border-b border-white/10 flex items-center justify-between px-8 sticky top-0 z-10">
          <div>
            {title && <h1 className="font-heading font-bold text-xl text-white">{title}</h1>}
            {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
              <Input 
                placeholder="Search..." 
                className="pl-10 w-64 bg-white/5 border-white/10 focus:border-primary"
                data-testid="search-input"
              />
            </div>
            <button 
              className="w-10 h-10 rounded-sm bg-white/5 border border-white/10 flex items-center justify-center hover:border-primary/50 transition-colors"
              data-testid="notifications-btn"
            >
              <Bell className="w-5 h-5 text-muted-foreground" />
            </button>
          </div>
        </header>
        
        {/* Page content */}
        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
};

export default DashboardLayout;
