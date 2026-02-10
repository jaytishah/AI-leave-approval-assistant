import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  User,
  Bell,
  Shield,
  Eye,
  EyeOff,
  Save,
  Camera,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/store/authStore';
import { Card, Button, Input, Avatar } from '@/components/ui';

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

export default function SettingsPage() {
  const { user } = useAuthStore();
  const [activeTab, setActiveTab] = useState('profile');
  const [showPassword, setShowPassword] = useState(false);
  const [notifications, setNotifications] = useState({
    email_leave_status: true,
    email_approval_needed: true,
    push_notifications: false,
    weekly_summary: true,
  });
  
  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'notifications', label: 'Notifications', icon: Bell },
    { id: 'security', label: 'Security', icon: Shield },
  ];
  
  const handleSaveProfile = () => {
    toast.success('Profile updated successfully');
  };
  
  const handleSaveNotifications = () => {
    toast.success('Notification preferences saved');
  };
  
  const handleChangePassword = () => {
    toast.success('Password changed successfully');
  };
  
  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Header */}
      <motion.div variants={itemVariants}>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="text-gray-600 mt-1">Manage your account preferences</p>
      </motion.div>
      
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar */}
        <motion.div variants={itemVariants} className="lg:col-span-1">
          <Card>
            <div className="p-4 space-y-1">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors text-left ${
                    activeTab === tab.id
                      ? 'bg-primary-50 text-primary-600'
                      : 'text-gray-600 hover:bg-gray-50'
                  }`}
                >
                  <tab.icon className="w-5 h-5" />
                  {tab.label}
                </button>
              ))}
            </div>
          </Card>
        </motion.div>
        
        {/* Content */}
        <motion.div variants={itemVariants} className="lg:col-span-3">
          {/* Profile Tab */}
          {activeTab === 'profile' && (
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Profile Information</h2>
                
                {/* Avatar */}
                <div className="flex items-center gap-6 mb-8">
                  <div className="relative">
                    <Avatar name={`${user?.first_name || ''} ${user?.last_name || ''}`.trim() || 'User'} size="lg" className="w-20 h-20" />
                    <button className="absolute bottom-0 right-0 w-8 h-8 bg-primary-500 rounded-full flex items-center justify-center text-white shadow-lg hover:bg-primary-600 transition-colors">
                      <Camera className="w-4 h-4" />
                    </button>
                  </div>
                  <div>
                    <h3 className="font-semibold text-gray-900">{`${user?.first_name || ''} ${user?.last_name || ''}`.trim()}</h3>
                    <p className="text-gray-500">{user?.email}</p>
                    <p className="text-sm text-gray-400 mt-1">Role: {user?.role}</p>
                  </div>
                </div>
                
                {/* Form */}
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <Input
                      label="First Name"
                      defaultValue={user?.first_name}
                    />
                    <Input
                      label="Last Name"
                      defaultValue={user?.last_name}
                    />
                  </div>
                  
                  <Input
                    label="Email Address"
                    type="email"
                    defaultValue={user?.email}
                  />
                  
                  <Input
                    label="Phone Number"
                    type="tel"
                    placeholder="+1 (555) 000-0000"
                  />
                  
                  <div className="pt-4">
                    <Button onClick={handleSaveProfile}>
                      <Save className="w-4 h-4 mr-2" />
                      Save Changes
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          )}
          
          {/* Notifications Tab */}
          {activeTab === 'notifications' && (
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">
                  Notification Preferences
                </h2>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-4">Email Notifications</h3>
                    <div className="space-y-4">
                      <NotificationToggle
                        label="Leave Request Status"
                        description="Get notified when your leave request is approved or rejected"
                        checked={notifications.email_leave_status}
                        onChange={(checked) =>
                          setNotifications({ ...notifications, email_leave_status: checked })
                        }
                      />
                      <NotificationToggle
                        label="Approval Required"
                        description="Get notified when a request needs your approval"
                        checked={notifications.email_approval_needed}
                        onChange={(checked) =>
                          setNotifications({ ...notifications, email_approval_needed: checked })
                        }
                      />
                      <NotificationToggle
                        label="Weekly Summary"
                        description="Receive a weekly summary of team leaves"
                        checked={notifications.weekly_summary}
                        onChange={(checked) =>
                          setNotifications({ ...notifications, weekly_summary: checked })
                        }
                      />
                    </div>
                  </div>
                  
                  <div className="border-t pt-6">
                    <h3 className="font-medium text-gray-900 mb-4">Push Notifications</h3>
                    <NotificationToggle
                      label="Browser Notifications"
                      description="Receive push notifications in your browser"
                      checked={notifications.push_notifications}
                      onChange={(checked) =>
                        setNotifications({ ...notifications, push_notifications: checked })
                      }
                    />
                  </div>
                  
                  <div className="pt-4">
                    <Button onClick={handleSaveNotifications}>
                      <Save className="w-4 h-4 mr-2" />
                      Save Preferences
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          )}
          
          {/* Security Tab */}
          {activeTab === 'security' && (
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-6">Security Settings</h2>
                
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium text-gray-900 mb-4">Change Password</h3>
                    <div className="space-y-4 max-w-md">
                      <div className="relative">
                        <Input
                          label="Current Password"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Enter current password"
                        />
                      </div>
                      <div className="relative">
                        <Input
                          label="New Password"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Enter new password"
                        />
                      </div>
                      <div className="relative">
                        <Input
                          label="Confirm New Password"
                          type={showPassword ? 'text' : 'password'}
                          placeholder="Confirm new password"
                        />
                      </div>
                      
                      <button
                        type="button"
                        onClick={() => setShowPassword(!showPassword)}
                        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
                      >
                        {showPassword ? (
                          <EyeOff className="w-4 h-4" />
                        ) : (
                          <Eye className="w-4 h-4" />
                        )}
                        {showPassword ? 'Hide' : 'Show'} passwords
                      </button>
                      
                      <Button onClick={handleChangePassword}>
                        <Shield className="w-4 h-4 mr-2" />
                        Update Password
                      </Button>
                    </div>
                  </div>
                  
                  <div className="border-t pt-6">
                    <h3 className="font-medium text-gray-900 mb-4">Two-Factor Authentication</h3>
                    <div className="p-4 bg-gray-50 rounded-lg">
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">2FA is disabled</p>
                          <p className="text-sm text-gray-500 mt-1">
                            Add an extra layer of security to your account
                          </p>
                        </div>
                        <Button variant="secondary" size="sm">
                          Enable 2FA
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  <div className="border-t pt-6">
                    <h3 className="font-medium text-gray-900 mb-4">Active Sessions</h3>
                    <div className="space-y-3">
                      <div className="p-4 bg-gray-50 rounded-lg flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">Current Session</p>
                          <p className="text-sm text-gray-500">Windows • Chrome • Last active now</p>
                        </div>
                        <span className="text-green-500 text-sm font-medium">Active</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </Card>
          )}
        </motion.div>
      </div>
    </motion.div>
  );
}

// Notification Toggle Component
interface NotificationToggleProps {
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
}

function NotificationToggle({ label, description, checked, onChange }: NotificationToggleProps) {
  return (
    <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
      <div>
        <p className="font-medium text-gray-900">{label}</p>
        <p className="text-sm text-gray-500">{description}</p>
      </div>
      <button
        onClick={() => onChange(!checked)}
        className={`relative w-12 h-6 rounded-full transition-colors ${
          checked ? 'bg-primary-500' : 'bg-gray-300'
        }`}
      >
        <span
          className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-transform ${
            checked ? 'translate-x-7' : 'translate-x-1'
          }`}
        />
      </button>
    </div>
  );
}
