import axios from 'axios';
import { useAuthStore } from '@/store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const state = useAuthStore.getState();
    const token = state.token;
    const hasHydrated = state._hasHydrated;
    console.log('[API] Request to:', config.url);
    console.log('[API] State:', { token: token ? token.substring(0, 20) + '...' : null, isAuthenticated: state.isAuthenticated, hasHydrated });
    
    // Try to get token from localStorage directly as fallback
    if (!token) {
      try {
        const stored = localStorage.getItem('auth-storage');
        if (stored) {
          const parsed = JSON.parse(stored);
          if (parsed.state?.token) {
            console.log('[API] Found token in localStorage directly');
            config.headers.Authorization = `Bearer ${parsed.state.token}`;
            return config;
          }
        }
      } catch (e) {
        console.error('[API] Error reading localStorage:', e);
      }
    }
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.log('[API] Error:', error.response?.status, 'for', error.config?.url);
    // Don't auto-logout - let the components handle auth errors
    // The ProtectedRoute component will handle redirects
    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authApi = {
  login: async (email: string, password: string) => {
    const formData = new URLSearchParams();
    formData.append('username', email);
    formData.append('password', password);
    
    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    return response.data;
  },
  
  loginJson: async (email: string, password: string) => {
    const response = await api.post('/auth/login/json', { email, password });
    return response.data;
  },
  
  register: async (userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role?: string;
  }) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  
  getMe: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
};

// Leave API
export const leaveApi = {
  getMyLeaveRequests: () => {
    return api.get('/leaves/');
  },
  
  getLeaveRequest: (id: number) => {
    return api.get(`/leaves/${id}`);
  },
  
  approveLeaveRequest: (id: number, comments?: string) => {
    return api.put(`/leaves/${id}/approve`, null, {
      params: comments ? { comments } : {},
    });
  },
  
  rejectLeaveRequest: (id: number, reason: string) => {
    return api.put(`/leaves/${id}/reject`, null, {
      params: { reason },
    });
  },
  
  createLeaveRequest: async (data: {
    leave_type: string;
    start_date: string;
    end_date: string;
    reason_text?: string;
    medical_certificate_url?: string;
    medical_certificate_filename?: string;
    medical_certificate_size?: number;
  }) => {
    const response = await api.post('/leaves/', data);
    return response.data;
  },
  
  getPendingRequests: async (riskLevel?: string, departmentId?: number) => {
    const params: Record<string, string | number> = {};
    if (riskLevel) params.risk_level = riskLevel;
    if (departmentId) params.department_id = departmentId;
    const response = await api.get('/leaves/pending', { params });
    return response.data;
  },
  
  getAllRequests: async (status?: string, employeeId?: number) => {
    const params: Record<string, string | number> = {};
    if (status) params.status = status;
    if (employeeId) params.employee_id = employeeId;
    const response = await api.get('/leaves/all', { params });
    return response.data;
  },
  
  cancelRequest: async (id: number) => {
    const response = await api.put(`/leaves/${id}/cancel`);
    return response.data;
  },
  
  getAuditTrail: async (id: number) => {
    const response = await api.get(`/leaves/${id}/audit`);
    return response.data;
  },
  
  getMyBalance: async () => {
    const response = await api.get('/leaves/balance/me');
    return response.data;
  },
};

// User API
export const userApi = {
  getAllUsers: async (role?: string, departmentId?: number) => {
    const params: Record<string, string | number> = {};
    if (role) params.role = role;
    if (departmentId) params.department_id = departmentId;
    const response = await api.get('/users/', { params });
    return response.data;
  },
  
  getEmployees: async (departmentId?: number) => {
    const params = departmentId ? { department_id: departmentId } : {};
    const response = await api.get('/users/employees', { params });
    return response.data;
  },
  
  getUser: async (id: number) => {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },
  
  createUser: async (userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: string;
    department_id?: number;
  }) => {
    const response = await api.post('/users/', userData);
    return response.data;
  },
  
  updateUser: async (id: number, userData: Partial<{
    first_name: string;
    last_name: string;
    department_id: number;
    is_active: boolean;
  }>) => {
    const response = await api.put(`/users/${id}`, userData);
    return response.data;
  },
  
  getUserBalance: async (id: number) => {
    const response = await api.get(`/users/${id}/balance`);
    return response.data;
  },
  
  getDepartments: async () => {
    const response = await api.get('/users/departments/');
    return response.data;
  },
  
  createDepartment: async (data: { name: string; code: string; description?: string }) => {
    const response = await api.post('/users/departments/', data);
    return response.data;
  },
};

// Admin API
export const adminApi = {
  getEmployeeDashboard: () => {
    return api.get('/admin/dashboard/employee');
  },
  
  getHRDashboard: () => {
    return api.get('/admin/dashboard/hr');
  },
  
  getAdminDashboard: () => {
    return api.get('/admin/dashboard/admin');
  },
  
  getPendingRequests: () => {
    return api.get('/leaves/pending');
  },
  
  getSystemStats: () => {
    return api.get('/admin/system-stats');
  },
  
  getAIConfig: () => {
    return api.get('/admin/ai-config');
  },
  
  getDepartments: () => {
    return api.get('/users/departments/');
  },
  
  getCalendarEvents: (year: number, month: number) => {
    return api.get('/admin/calendar-events', { params: { year, month } });
  },
  
  getPolicies: async (departmentId?: number) => {
    const params = departmentId ? { department_id: departmentId } : {};
    const response = await api.get('/admin/policies', { params });
    return response.data;
  },
  
  getPolicy: async (id: number) => {
    const response = await api.get(`/admin/policies/${id}`);
    return response.data;
  },
  
  createPolicy: async (data: Partial<{
    name: string;
    department_id: number;
    annual_leave_days: number;
    sick_leave_days: number;
    casual_leave_days: number;
    allow_negative_balance: boolean;
    reason_mandatory: boolean;
    require_manager_approval: boolean;
    long_leave_threshold_days: number;
    min_advance_days_for_long_leave: number;
    max_consecutive_leave_days: number;
    max_unplanned_leaves_30_days: number;
    max_leaves_90_days: number;
    max_pattern_score: number;
    blackout_periods: { start_date: string; end_date: string }[];
    holidays: string[];
  }>) => {
    const response = await api.post('/admin/policies', data);
    return response.data;
  },
  
  updatePolicy: async (id: number, data: Record<string, unknown>) => {
    const response = await api.put(`/admin/policies/${id}`, data);
    return response.data;
  },
  
  getAIConfigs: async () => {
    const response = await api.get('/admin/ai-config');
    return response.data;
  },
  
  updateAIConfig: (id: number, data: { config_value: string }) => {
    return api.put(`/admin/ai-config/${id}`, data);
  },
  
  getHolidays: async (year?: number) => {
    const params = year ? { year } : {};
    const response = await api.get('/admin/holidays', { params });
    return response.data;
  },
  
  createHoliday: async (data: { name: string; date: string; type: string; location?: string }) => {
    const response = await api.post('/admin/holidays', data);
    return response.data;
  },
  
  deleteHoliday: async (id: number) => {
    const response = await api.delete(`/admin/holidays/${id}`);
    return response.data;
  },
  
  getAuditLogs: async (leaveRequestId?: number, actorId?: number) => {
    const params: Record<string, number> = {};
    if (leaveRequestId) params.leave_request_id = leaveRequestId;
    if (actorId) params.actor_id = actorId;
    const response = await api.get('/admin/audit-logs', { params });
    return response.data;
  },
  
  // User Management
  getAllUsers: async (params?: { role?: string; department_id?: number; is_active?: boolean }) => {
    const response = await api.get('/users/', { params });
    return response;
  },
  
  getUser: async (userId: number) => {
    const response = await api.get(`/users/${userId}`);
    return response;
  },
  
  createUser: async (userData: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    role: string;
    department_id?: number;
    manager_id?: number;
    location?: string;
    grade?: string;
    level?: string;
  }) => {
    const response = await api.post('/users/', userData);
    return response;
  },
  
  updateUser: async (userId: number, userData: {
    first_name?: string;
    last_name?: string;
    department_id?: number;
    manager_id?: number;
    location?: string;
    grade?: string;
    level?: string;
    is_active?: boolean;
  }) => {
    const response = await api.put(`/users/${userId}`, userData);
    return response;
  },
  
  deleteUser: async (userId: number) => {
    const response = await api.delete(`/users/${userId}`);
    return response;
  },
  
  // Leave Balance Management
  getUserBalances: async (userId: number) => {
    const response = await api.get(`/users/${userId}/balances`);
    return response;
  },
  
  updateUserBalance: async (userId: number, balanceData: {
    leave_type: string;
    total_days?: number;
    used_days?: number;
  }) => {
    const response = await api.post(`/users/${userId}/balances`, balanceData);
    return response;
  },
};
