import { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  FileText,
  Calendar,
  Settings,
  LogOut,
  Bell,
  Search,
  ChevronDown,
  Menu,
  X,
  Sparkles,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { Avatar } from '@/components/ui';
import { cn } from '@/lib/utils';

interface NavItem {
  icon: React.ElementType;
  label: string;
  path: string;
  roles?: string[];
}

const navItems: NavItem[] = [
  // Employee sees Dashboard and My Requests
  { icon: LayoutDashboard, label: 'Dashboard', path: '/dashboard', roles: ['EMPLOYEE'] },
  { icon: FileText, label: 'My Requests', path: '/my-requests', roles: ['EMPLOYEE'] },
  { icon: Calendar, label: 'Calendar', path: '/calendar', roles: ['EMPLOYEE'] },
  // HR sees HR Dashboard
  { icon: LayoutDashboard, label: 'HR Dashboard', path: '/hr', roles: ['HR'] },
  // Admin sees Admin Dashboard and HR Dashboard
  { icon: LayoutDashboard, label: 'Admin Dashboard', path: '/admin', roles: ['ADMIN'] },
  { icon: FileText, label: 'HR Dashboard', path: '/hr', roles: ['ADMIN'] },
  // Settings for all
  { icon: Settings, label: 'Settings', path: '/settings' },
];

export function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  
  const filteredNavItems = navItems.filter((item) => {
    if (!item.roles) return true;
    return item.roles.includes(user?.role || '');
  });
  
  const handleLogout = () => {
    logout();
    navigate('/login');
  };
  
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile Header */}
      <div className="lg:hidden fixed top-0 left-0 right-0 h-16 bg-white border-b border-gray-200 z-40 px-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary-600 rounded-lg flex items-center justify-center">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <span className="font-semibold text-gray-900">LeaveAI</span>
          </div>
        </div>
        
        <Avatar
          src={user?.avatar_url}
          name={`${user?.first_name} ${user?.last_name}`}
          size="sm"
        />
      </div>
      
      {/* Mobile Sidebar Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileMenuOpen(false)}
            className="lg:hidden fixed inset-0 bg-black/50 z-40"
          />
        )}
      </AnimatePresence>
      
      {/* Sidebar */}
      <motion.aside
        initial={false}
        animate={{
          width: sidebarOpen ? 260 : 80,
          x: mobileMenuOpen ? 0 : (typeof window !== 'undefined' && window.innerWidth < 1024 ? -260 : 0),
        }}
        className={cn(
          'fixed left-0 top-0 h-full bg-white border-r border-gray-200 z-50',
          'flex flex-col',
          'lg:translate-x-0'
        )}
      >
        {/* Logo */}
        <div className="h-16 flex items-center justify-between px-4 border-b border-gray-100">
          <Link to="/dashboard" className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary-600 rounded-xl flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-white" />
            </div>
            <AnimatePresence>
              {sidebarOpen && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                >
                  <span className="font-bold text-lg text-gray-900">LeaveAI</span>
                  <span className="block text-xs text-gray-500">Enterprise Portal</span>
                </motion.div>
              )}
            </AnimatePresence>
          </Link>
          
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="hidden lg:flex p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Menu className="w-5 h-5" />
          </button>
        </div>
        
        {/* Navigation */}
        <nav className="flex-1 py-4 px-3 overflow-y-auto">
          <ul className="space-y-1">
            {filteredNavItems.map((item) => {
              const isActive = location.pathname === item.path;
              const Icon = item.icon;
              
              return (
                <li key={item.path}>
                  <Link
                    to={item.path}
                    onClick={() => setMobileMenuOpen(false)}
                    className={cn(
                      'flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200',
                      isActive
                        ? 'bg-primary-50 text-primary-600'
                        : 'text-gray-600 hover:bg-gray-100'
                    )}
                  >
                    <Icon className={cn('w-5 h-5', isActive && 'text-primary-600')} />
                    <AnimatePresence>
                      {sidebarOpen && (
                        <motion.span
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          exit={{ opacity: 0, x: -10 }}
                          className={cn(
                            'text-sm font-medium',
                            isActive ? 'text-primary-600' : 'text-gray-700'
                          )}
                        >
                          {item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </Link>
                </li>
              );
            })}
          </ul>
        </nav>
        
        {/* User Section */}
        <div className="p-3 border-t border-gray-100">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="w-full flex items-center gap-3 p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <Avatar
              src={user?.avatar_url}
              name={`${user?.first_name} ${user?.last_name}`}
              size="md"
            />
            <AnimatePresence>
              {sidebarOpen && (
                <motion.div
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -10 }}
                  className="flex-1 text-left"
                >
                  <p className="text-sm font-medium text-gray-900 truncate">
                    {user?.first_name} {user?.last_name}
                  </p>
                  <p className="text-xs text-gray-500">{user?.role}</p>
                </motion.div>
              )}
            </AnimatePresence>
            {sidebarOpen && <ChevronDown className="w-4 h-4 text-gray-400" />}
          </button>
          
          <AnimatePresence>
            {userMenuOpen && sidebarOpen && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                className="mt-2 py-2 bg-white rounded-lg border border-gray-200 shadow-lg"
              >
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center gap-2 px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  Sign Out
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </motion.aside>
      
      {/* Main Content */}
      <main
        className={cn(
          'transition-all duration-300 min-h-screen',
          'pt-16 lg:pt-0',
          sidebarOpen ? 'lg:ml-[260px]' : 'lg:ml-20'
        )}
      >
        {/* Top Bar */}
        <header className="hidden lg:flex h-16 bg-white border-b border-gray-200 items-center justify-between px-6">
          <div className="flex items-center gap-4">
            <nav className="flex items-center text-sm text-gray-500">
              <span>Home</span>
              <span className="mx-2">/</span>
              <span className="text-gray-900">
                {filteredNavItems.find((item) => item.path === location.pathname)?.label || 'Dashboard'}
              </span>
            </nav>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="relative">
              <Search className="w-4 h-4 absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400" />
              <input
                type="text"
                placeholder="Search records..."
                className="pl-10 pr-4 py-2 w-64 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
            
            <button className="p-2 text-gray-600 hover:bg-gray-100 rounded-lg relative">
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            </button>
            
            <div className="flex items-center gap-3 pl-4 border-l border-gray-200">
              <Avatar
                src={user?.avatar_url}
                name={`${user?.first_name} ${user?.last_name}`}
                size="md"
              />
              <div>
                <p className="text-sm font-medium text-gray-900">
                  {user?.first_name} {user?.last_name}
                </p>
              </div>
              <ChevronDown className="w-4 h-4 text-gray-400" />
            </div>
          </div>
        </header>
        
        {/* Page Content */}
        <div className="p-4 lg:p-6">
          {children}
        </div>
      </main>
    </div>
  );
}
