import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from '@/store/authStore';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import LoginPage from '@/pages/LoginPage';
import EmployeeDashboardPage from '@/pages/employee/EmployeeDashboardPage';
import MyRequestsPage from '@/pages/employee/MyRequestsPage';
import CalendarPage from '@/pages/shared/CalendarPage';
import HRDashboardPage from '@/pages/hr/HRDashboardPage';
import LeaveRequestDetailPage from '@/pages/hr/LeaveRequestDetailPage';
import AdminDashboardPage from '@/pages/admin/AdminDashboardPage';
import PolicySettingsPage from '@/pages/admin/PolicySettingsPage';
import SettingsPage from '@/pages/SettingsPage';

// Protected Route Component
interface ProtectedRouteProps {
  children: React.ReactNode;
  allowedRoles?: string[];
}

function ProtectedRoute({ children, allowedRoles }: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    // Redirect to appropriate dashboard based on role
    switch (user.role) {
      case 'ADMIN':
        return <Navigate to="/admin" replace />;
      case 'HR':
        return <Navigate to="/hr" replace />;
      default:
        return <Navigate to="/dashboard" replace />;
    }
  }
  
  return <>{children}</>;
}

// Root redirect based on role
function RootRedirect() {
  const { isAuthenticated, user } = useAuthStore();
  
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }
  
  switch (user?.role) {
    case 'ADMIN':
      return <Navigate to="/admin" replace />;
    case 'HR':
      return <Navigate to="/hr" replace />;
    default:
      return <Navigate to="/dashboard" replace />;
  }
}

// Loading component while hydrating
function AuthLoader({ children }: { children: React.ReactNode }) {
  const hasHydrated = useAuthStore((state) => state._hasHydrated);
  
  if (!hasHydrated) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }
  
  return <>{children}</>;
}

function App() {
  return (
    <BrowserRouter>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            background: '#fff',
            color: '#374151',
            boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
            borderRadius: '0.75rem',
            padding: '1rem',
          },
          success: {
            iconTheme: {
              primary: '#10B981',
              secondary: '#fff',
            },
          },
          error: {
            iconTheme: {
              primary: '#EF4444',
              secondary: '#fff',
            },
          },
        }}
      />
      
      <AuthLoader>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<LoginPage />} />
          
          {/* Root Redirect */}
          <Route path="/" element={<RootRedirect />} />
          
          {/* Employee Routes */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
              <DashboardLayout>
                <EmployeeDashboardPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/my-requests"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <MyRequestsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/calendar"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <CalendarPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        
        {/* HR Routes */}
        <Route
          path="/hr"
          element={
            <ProtectedRoute allowedRoles={['HR', 'ADMIN']}>
              <DashboardLayout>
                <HRDashboardPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/calendar"
          element={
            <ProtectedRoute allowedRoles={['HR', 'ADMIN']}>
              <DashboardLayout>
                <CalendarPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/hr/requests/:id"
          element={
            <ProtectedRoute allowedRoles={['HR', 'ADMIN']}>
              <DashboardLayout>
                <LeaveRequestDetailPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        
        {/* Admin Routes */}
        <Route
          path="/admin"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <DashboardLayout>
                <AdminDashboardPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/calendar"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <DashboardLayout>
                <CalendarPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin/policy-settings"
          element={
            <ProtectedRoute allowedRoles={['ADMIN']}>
              <DashboardLayout>
                <PolicySettingsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        
        {/* Shared Routes */}
        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <DashboardLayout>
                <SettingsPage />
              </DashboardLayout>
            </ProtectedRoute>
          }
        />
        
        {/* Catch all - redirect to root */}
        <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthLoader>
    </BrowserRouter>
  );
}

export default App;
