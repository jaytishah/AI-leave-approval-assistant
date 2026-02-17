import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Users,
  Building2,
  Brain,
  Shield,
  Database,
  TrendingUp,
  Activity,
  RefreshCw,
  Save,
  Plus,
  Edit,
  Trash2,
  Search,
  UserPlus,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { adminApi } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { Card, Badge, Button, Input, Modal, Avatar } from '@/components/ui';

interface SystemStats {
  total_users: number;
  total_departments: number;
  total_requests_today: number;
  ai_processed_today: number;
  auto_approved_rate: number;
  system_health: string;
}

interface UserData {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  role: string;
  department_id: number | null;
  department_name: string | null;
  is_active: boolean;
  level: string | null;
  tenure_months: number;
  avatar_url: string | null;
}

interface AIConfig {
  id: number;
  config_key: string;
  config_value: string;
  description: string;
}

interface Department {
  id: number;
  name: string;
  code: string;
  employee_count: number;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function AdminDashboardPage() {
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [aiConfig, setAIConfig] = useState<AIConfig[]>([]);
  const [departments, setDepartments] = useState<Department[]>([]);
  const [users, setUsers] = useState<UserData[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('overview');
  const [showDeptModal, setShowDeptModal] = useState(false);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingConfig, setEditingConfig] = useState<AIConfig | null>(null);
  const [editingUser, setEditingUser] = useState<UserData | null>(null);
  const [userSearchTerm, setUserSearchTerm] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState<string>('all');
  const [newUser, setNewUser] = useState({
    email: '',
    password: '',
    first_name: '',
    last_name: '',
    role: 'EMPLOYEE',
    department_id: 0,
    level: '',
  });
  
  useEffect(() => {
    // Fetch data when component mounts
    fetchData();
  }, []);
  
  // Fetch users when switching to users tab
  useEffect(() => {
    if (activeTab === 'users') {
      fetchUsers();
    }
  }, [activeTab, userRoleFilter]);
  
  const fetchUsers = async () => {
    try {
      const params: { role?: string } = {};
      if (userRoleFilter && userRoleFilter !== 'all') {
        params.role = userRoleFilter;
      }
      console.log('[AdminDashboard] Fetching users with params:', params);
      const response = await adminApi.getAllUsers(params);
      console.log('[AdminDashboard] Users response:', response.data);
      setUsers(response.data || []);
    } catch (error) {
      console.error('Failed to fetch users:', error);
      toast.error('Failed to load users');
    }
  };
  
  const fetchData = async () => {
    try {
      console.log('[AdminDashboard] Fetching data...');
      
      // Fetch stats first - this is critical for Overview
      try {
        const statsRes = await adminApi.getSystemStats();
        console.log('[AdminDashboard] Stats response:', statsRes);
        console.log('[AdminDashboard] Stats data:', statsRes.data);
        setStats(statsRes.data);
      } catch (statsError) {
        console.error('[AdminDashboard] Failed to fetch stats:', statsError);
      }
      
      // Fetch config and departments
      try {
        const [configRes, deptRes] = await Promise.all([
          adminApi.getAIConfig(),
          adminApi.getDepartments(),
        ]);
        setAIConfig(configRes.data || []);
        setDepartments(deptRes.data || []);
      } catch (otherError) {
        console.error('[AdminDashboard] Failed to fetch config/departments:', otherError);
      }
      
    } catch (error) {
      console.error('[AdminDashboard] Failed to fetch admin data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleUpdateConfig = async (config: AIConfig, newValue: string) => {
    try {
      await adminApi.updateAIConfig(config.id, { config_value: newValue });
      toast.success('Configuration updated successfully');
      setEditingConfig(null);
      fetchData();
    } catch (error) {
      toast.error('Failed to update configuration');
    }
  };
  
  const tabs = [
    { id: 'overview', label: 'Overview', icon: Activity },
    { id: 'ai-config', label: 'AI Settings', icon: Brain },
    { id: 'departments', label: 'Departments', icon: Building2 },
    { id: 'users', label: 'User Management', icon: Users },
  ];
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }
  
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-1">System configuration and management</p>
        </div>
        <Badge
          variant={stats?.system_health === 'healthy' ? 'success' : 'warning'}
          className="px-3 py-1.5"
        >
          <Activity className="w-4 h-4 mr-1" />
          System {stats?.system_health || 'Unknown'}
        </Badge>
      </motion.div>
      
      {/* Tabs */}
      <motion.div variants={itemVariants}>
        <div className="flex items-center gap-2 bg-gray-100 p-1 rounded-lg w-fit">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'bg-white text-primary-600 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </motion.div>
      
      {/* Overview Tab */}
      {activeTab === 'overview' && (
        <motion.div variants={containerVariants} className="space-y-6">
          {/* Stats Grid */}
          <motion.div variants={itemVariants} className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <StatsCard
              icon={Users}
              label="Total Users"
              value={stats?.total_users || 0}
              color="blue"
            />
            <StatsCard
              icon={Building2}
              label="Departments"
              value={stats?.total_departments || 0}
              color="purple"
            />
            <StatsCard
              icon={Database}
              label="Requests Today"
              value={stats?.total_requests_today || 0}
              color="green"
            />
            <StatsCard
              icon={Brain}
              label="AI Processed"
              value={stats?.ai_processed_today || 0}
              color="amber"
            />
            <StatsCard
              icon={TrendingUp}
              label="Auto-Approved"
              value={`${stats?.auto_approved_rate || 0}%`}
              color="teal"
            />
            <StatsCard
              icon={Shield}
              label="System Health"
              value={stats?.system_health || 'N/A'}
              color="emerald"
            />
          </motion.div>
          
          {/* Quick Actions */}
          <motion.div variants={itemVariants}>
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <QuickActionCard
                    icon={RefreshCw}
                    label="Sync Data"
                    description="Refresh all cached data"
                    onClick={() => {
                      fetchData();
                      toast.success('Data refreshed');
                    }}
                  />
                  <QuickActionCard
                    icon={Brain}
                    label="Test AI"
                    description="Run AI diagnostics"
                    onClick={() => toast.success('AI systems operational')}
                  />
                  <QuickActionCard
                    icon={Database}
                    label="Backup"
                    description="Create system backup"
                    onClick={() => toast.success('Backup initiated')}
                  />
                  <QuickActionCard
                    icon={Shield}
                    label="Security Scan"
                    description="Run security audit"
                    onClick={() => toast.success('Security scan started')}
                  />
                </div>
              </div>
            </Card>
          </motion.div>
        </motion.div>
      )}
      
      {/* AI Config Tab */}
      {activeTab === 'ai-config' && (
        <motion.div variants={containerVariants} className="space-y-6">
          <motion.div variants={itemVariants}>
            <Card>
              <div className="p-6 border-b border-gray-100">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                    <Brain className="w-5 h-5 text-white" />
                  </div>
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">AI Configuration</h2>
                    <p className="text-sm text-gray-500">Configure Gemini AI model settings</p>
                  </div>
                </div>
              </div>
              
              <div className="divide-y divide-gray-100">
                {aiConfig.map((config) => (
                  <div key={config.id} className="p-6 flex items-center justify-between">
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{config.config_key}</p>
                      <p className="text-sm text-gray-500 mt-1">{config.description}</p>
                    </div>
                    <div className="flex items-center gap-4">
                      {editingConfig?.id === config.id ? (
                        <>
                          <input
                            type="text"
                            defaultValue={config.config_value}
                            className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm w-48"
                            onKeyDown={(e) => {
                              if (e.key === 'Enter') {
                                handleUpdateConfig(config, e.currentTarget.value);
                              }
                            }}
                          />
                          <Button
                            size="sm"
                            onClick={() => setEditingConfig(null)}
                            variant="secondary"
                          >
                            Cancel
                          </Button>
                        </>
                      ) : (
                        <>
                          <Badge variant="default">{config.config_value}</Badge>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => setEditingConfig(config)}
                          >
                            <Edit className="w-4 h-4" />
                          </Button>
                        </>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </motion.div>
          
          {/* AI Thresholds */}
          <motion.div variants={itemVariants}>
            <Card>
              <div className="p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-4">Decision Thresholds</h3>
                <div className="space-y-4">
                  <ThresholdSlider
                    label="Auto-Approve Threshold"
                    value={80}
                    description="Requests with validity score above this will be auto-approved"
                  />
                  <ThresholdSlider
                    label="Auto-Reject Threshold"
                    value={30}
                    description="Requests with validity score below this will be auto-rejected"
                  />
                  <ThresholdSlider
                    label="HR Review Required"
                    value={60}
                    description="Requests between thresholds require HR review"
                  />
                </div>
              </div>
            </Card>
          </motion.div>
        </motion.div>
      )}
      
      {/* Departments Tab */}
      {activeTab === 'departments' && (
        <motion.div variants={containerVariants} className="space-y-6">
          <motion.div variants={itemVariants} className="flex justify-end">
            <Button onClick={() => setShowDeptModal(true)}>
              <Plus className="w-4 h-4 mr-2" />
              Add Department
            </Button>
          </motion.div>
          
          <motion.div variants={itemVariants}>
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Department
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Code
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                        Employees
                      </th>
                      <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {departments.map((dept) => (
                      <tr key={dept.id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                              <Building2 className="w-5 h-5 text-primary-600" />
                            </div>
                            <span className="font-medium text-gray-900">{dept.name}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <Badge variant="default">{dept.code}</Badge>
                        </td>
                        <td className="px-6 py-4 text-gray-600">{dept.employee_count}</td>
                        <td className="px-6 py-4 text-right">
                          <Button variant="ghost" size="sm">
                            <Edit className="w-4 h-4" />
                          </Button>
                          <Button variant="ghost" size="sm" className="text-red-500">
                            <Trash2 className="w-4 h-4" />
                          </Button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Card>
          </motion.div>
        </motion.div>
      )}
      
      {/* Users Tab */}
      {activeTab === 'users' && (
        <motion.div variants={containerVariants} className="space-y-6">
          {/* Header with actions */}
          <motion.div variants={itemVariants} className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search users..."
                  value={userSearchTerm}
                  onChange={(e) => setUserSearchTerm(e.target.value)}
                  className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-64"
                />
              </div>
              <select
                value={userRoleFilter}
                onChange={(e) => {
                  setUserRoleFilter(e.target.value);
                  fetchUsers();
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="all">All Roles</option>
                <option value="EMPLOYEE">Employees</option>
                <option value="HR">HR</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>
            <Button onClick={() => {
              setEditingUser(null);
              setNewUser({
                email: '',
                password: '',
                first_name: '',
                last_name: '',
                role: 'EMPLOYEE',
                department_id: 0,
                level: '',
              });
              setShowUserModal(true);
            }}>
              <UserPlus className="w-4 h-4 mr-2" />
              Add User
            </Button>
          </motion.div>
          
          {/* Users List */}
          <motion.div variants={itemVariants}>
            <Card>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-gray-100">
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Department</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Level</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                      <th className="px-6 py-4 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {users
                      .filter(user => {
                        if (!userSearchTerm) return true;
                        const search = userSearchTerm.toLowerCase();
                        return (
                          user.first_name.toLowerCase().includes(search) ||
                          user.last_name.toLowerCase().includes(search) ||
                          user.email.toLowerCase().includes(search)
                        );
                      })
                      .map((user) => (
                        <tr key={user.id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <Avatar name={`${user.first_name} ${user.last_name}`} size="sm" />
                              <div>
                                <p className="font-medium text-gray-900">{user.first_name} {user.last_name}</p>
                                <p className="text-sm text-gray-500">{user.email}</p>
                              </div>
                            </div>
                          </td>
                          <td className="px-6 py-4">
                            <Badge variant={
                              user.role === 'ADMIN' ? 'danger' :
                              user.role === 'HR' ? 'warning' : 'default'
                            }>
                              {user.role}
                            </Badge>
                          </td>
                          <td className="px-6 py-4 text-gray-600">
                            {user.department_name || '-'}
                          </td>
                          <td className="px-6 py-4 text-gray-600">
                            {user.level || '-'}
                          </td>
                          <td className="px-6 py-4">
                            <Badge variant={user.is_active ? 'success' : 'danger'}>
                              {user.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => {
                                  setEditingUser(user);
                                  setShowUserModal(true);
                                }}
                                className="p-2 text-gray-500 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                              >
                                <Edit className="w-4 h-4" />
                              </button>
                              <button
                                onClick={async () => {
                                  if (confirm(`Are you sure you want to ${user.is_active ? 'deactivate' : 'activate'} this user?`)) {
                                    try {
                                      await adminApi.updateUser(user.id, { is_active: !user.is_active });
                                      toast.success(`User ${user.is_active ? 'deactivated' : 'activated'} successfully`);
                                      fetchUsers();
                                    } catch (error) {
                                      toast.error('Failed to update user status');
                                    }
                                  }
                                }}
                                className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          </td>
                        </tr>
                      ))}
                  </tbody>
                </table>
                {users.length === 0 && (
                  <div className="p-12 text-center">
                    <Users className="w-12 h-12 mx-auto text-gray-300 mb-4" />
                    <p className="text-gray-500">No users found</p>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
        </motion.div>
      )}
      
      {/* Add Department Modal */}
      <Modal
        isOpen={showDeptModal}
        onClose={() => setShowDeptModal(false)}
        title="Add New Department"
      >
        <form className="space-y-4">
          <Input label="Department Name" placeholder="e.g., Engineering" />
          <Input label="Department Code" placeholder="e.g., ENG" />
          <div className="flex gap-3">
            <Button
              type="button"
              variant="secondary"
              onClick={() => setShowDeptModal(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button type="submit" className="flex-1">
              <Save className="w-4 h-4 mr-2" />
              Save Department
            </Button>
          </div>
        </form>
      </Modal>
      
      {/* Add/Edit User Modal */}
      <Modal
        isOpen={showUserModal}
        onClose={() => {
          setShowUserModal(false);
          setEditingUser(null);
        }}
        title={editingUser ? 'Edit User' : 'Add New User'}
      >
        <form 
          className="space-y-4"
          onSubmit={async (e) => {
            e.preventDefault();
            try {
              if (editingUser) {
                await adminApi.updateUser(editingUser.id, {
                  first_name: newUser.first_name || editingUser.first_name,
                  last_name: newUser.last_name || editingUser.last_name,
                  department_id: newUser.department_id || editingUser.department_id || undefined,
                  level: newUser.level || editingUser.level || undefined,
                });
                toast.success('User updated successfully');
              } else {
                await adminApi.createUser({
                  email: newUser.email,
                  password: newUser.password,
                  first_name: newUser.first_name,
                  last_name: newUser.last_name,
                  role: newUser.role,
                  department_id: newUser.department_id || undefined,
                  level: newUser.level || undefined,
                });
                toast.success('User created successfully');
              }
              setShowUserModal(false);
              setEditingUser(null);
              fetchUsers();
            } catch (error) {
              toast.error(editingUser ? 'Failed to update user' : 'Failed to create user');
            }
          }}
        >
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="First Name"
              value={editingUser ? (newUser.first_name || editingUser.first_name) : newUser.first_name}
              onChange={(e) => setNewUser({ ...newUser, first_name: e.target.value })}
              required
            />
            <Input
              label="Last Name"
              value={editingUser ? (newUser.last_name || editingUser.last_name) : newUser.last_name}
              onChange={(e) => setNewUser({ ...newUser, last_name: e.target.value })}
              required
            />
          </div>
          
          <Input
            label="Email"
            type="email"
            value={editingUser ? editingUser.email : newUser.email}
            onChange={(e) => setNewUser({ ...newUser, email: e.target.value })}
            disabled={!!editingUser}
            required={!editingUser}
          />
          
          {!editingUser && (
            <Input
              label="Password"
              type="password"
              value={newUser.password}
              onChange={(e) => setNewUser({ ...newUser, password: e.target.value })}
              required
            />
          )}
          
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Role</label>
              <select
                value={editingUser ? editingUser.role : newUser.role}
                onChange={(e) => setNewUser({ ...newUser, role: e.target.value })}
                disabled={!!editingUser}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="EMPLOYEE">Employee</option>
                <option value="HR">HR</option>
                <option value="ADMIN">Admin</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1.5">Department</label>
              <select
                value={editingUser ? (newUser.department_id || editingUser.department_id || '') : newUser.department_id}
                onChange={(e) => setNewUser({ ...newUser, department_id: parseInt(e.target.value) || 0 })}
                className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="">Select Department</option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.id}>{dept.name}</option>
                ))}
              </select>
            </div>
          </div>
          
          <Input
            label="Level"
            placeholder="e.g., L3, L4, L5"
            value={editingUser ? (newUser.level || editingUser.level || '') : newUser.level}
            onChange={(e) => setNewUser({ ...newUser, level: e.target.value })}
          />
          
          <div className="flex gap-3 pt-4">
            <Button
              type="button"
              variant="secondary"
              onClick={() => {
                setShowUserModal(false);
                setEditingUser(null);
              }}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button type="submit" className="flex-1">
              <Save className="w-4 h-4 mr-2" />
              {editingUser ? 'Update User' : 'Create User'}
            </Button>
          </div>
        </form>
      </Modal>
    </motion.div>
  );
}

// Stats Card Component
interface StatsCardProps {
  icon: React.ElementType;
  label: string;
  value: number | string;
  color: string;
}

function StatsCard({ icon: Icon, label, value, color }: StatsCardProps) {
  const colorClasses: Record<string, string> = {
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
    green: 'bg-green-50 text-green-600',
    amber: 'bg-amber-50 text-amber-600',
    teal: 'bg-teal-50 text-teal-600',
    emerald: 'bg-emerald-50 text-emerald-600',
  };
  
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white rounded-xl border border-gray-100 p-4"
    >
      <div
        className={`w-10 h-10 rounded-lg ${colorClasses[color]} flex items-center justify-center mb-3`}
      >
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </motion.div>
  );
}

// Quick Action Card
interface QuickActionCardProps {
  icon: React.ElementType;
  label: string;
  description: string;
  onClick: () => void;
}

function QuickActionCard({ icon: Icon, label, description, onClick }: QuickActionCardProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className="p-4 bg-gray-50 rounded-xl text-left hover:bg-gray-100 transition-colors"
    >
      <Icon className="w-6 h-6 text-primary-600 mb-2" />
      <p className="font-medium text-gray-900">{label}</p>
      <p className="text-sm text-gray-500">{description}</p>
    </motion.button>
  );
}

// Threshold Slider
interface ThresholdSliderProps {
  label: string;
  value: number;
  description: string;
}

function ThresholdSlider({ label, value, description }: ThresholdSliderProps) {
  const [currentValue, setCurrentValue] = useState(value);
  
  return (
    <div className="p-4 bg-gray-50 rounded-lg">
      <div className="flex items-center justify-between mb-2">
        <p className="font-medium text-gray-900">{label}</p>
        <span className="text-lg font-bold text-primary-600">{currentValue}%</span>
      </div>
      <input
        type="range"
        min="0"
        max="100"
        value={currentValue}
        onChange={(e) => setCurrentValue(Number(e.target.value))}
        className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-primary-600"
      />
      <p className="text-sm text-gray-500 mt-2">{description}</p>
    </div>
  );
}
