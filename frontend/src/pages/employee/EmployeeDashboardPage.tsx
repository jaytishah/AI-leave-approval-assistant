import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Calendar,
  Plus,
  TrendingUp,
  Sparkles,
  Clock,
  AlertCircle,
  ChevronRight,
  MoreVertical,
} from 'lucide-react';
import { useAuthStore } from '@/store/authStore';
import { adminApi } from '@/services/api';
import { Card, Button, StatusBadge, Badge, Modal } from '@/components/ui';
import { formatDate, formatDateRange, getLeaveTypeIcon, getLeaveTypeLabel, cn } from '@/lib/utils';
import { LeaveBalance, LeaveRequest, Holiday, EmployeeDashboard } from '@/types';
import { LeaveRequestForm } from '@/components/forms/LeaveRequestForm';

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

export default function EmployeeDashboardPage() {
  const { user } = useAuthStore();
  const [dashboard, setDashboard] = useState<EmployeeDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  
  const fetchDashboard = async () => {
    try {
      const response = await adminApi.getEmployeeDashboard();
      setDashboard(response.data);
    } catch (error) {
      console.error('Failed to fetch dashboard:', error);
    } finally {
      setLoading(false);
    }
  };
  
  useEffect(() => {
    fetchDashboard();
  }, []);
  
  const handleLeaveSubmitted = () => {
    setShowLeaveModal(false);
    fetchDashboard();
  };
  
  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
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
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.first_name}
          </h1>
          <p className="text-gray-500 mt-1">
            Here's an overview of your leave status
          </p>
        </div>
        
        <Button onClick={() => setShowLeaveModal(true)} className="gap-2">
          <Plus className="w-4 h-4" />
          Apply for Leave
        </Button>
      </motion.div>
      
      {/* AI Suggestion Banner */}
      {dashboard?.ai_suggestion && (
        <motion.div
          variants={itemVariants}
          className="bg-gradient-to-r from-primary-50 to-blue-50 rounded-xl p-4 border border-primary-100"
        >
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center flex-shrink-0">
              <Sparkles className="w-5 h-5 text-primary-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-primary-900">AI Suggestion:</p>
              <p className="text-sm text-primary-700 mt-0.5">{dashboard.ai_suggestion}</p>
            </div>
          </div>
        </motion.div>
      )}
      
      {/* Leave Balance Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {dashboard?.leave_balances.map((balance, index) => (
          <LeaveBalanceCard key={balance.id} balance={balance} delay={index * 0.1} />
        ))}
      </motion.div>
      
      {/* Recent Requests & Holidays */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Requests */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
          <Card className="h-full">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Recent Requests</h2>
              <a href="/my-requests" className="text-sm text-primary-600 hover:text-primary-700 flex items-center gap-1">
                View all <ChevronRight className="w-4 h-4" />
              </a>
            </div>
            
            {dashboard?.recent_requests.length === 0 ? (
              <div className="text-center py-8 text-gray-500">
                <Calendar className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                <p>No recent leave requests</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <th className="pb-3">Leave Type</th>
                      <th className="pb-3">Dates</th>
                      <th className="pb-3">Duration</th>
                      <th className="pb-3">Status</th>
                      <th className="pb-3"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {dashboard?.recent_requests.map((request) => (
                      <LeaveRequestRow key={request.id} request={request} />
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Card>
        </motion.div>
        
        {/* Upcoming Holidays & Need a Break */}
        <motion.div variants={itemVariants} className="space-y-6">
          {/* Upcoming Holidays */}
          <Card>
            <div className="flex items-center gap-2 mb-4">
              <Calendar className="w-5 h-5 text-primary-600" />
              <h2 className="text-lg font-semibold text-gray-900">Upcoming Holidays</h2>
            </div>
            
            <div className="space-y-3">
              {dashboard?.upcoming_holidays.slice(0, 3).map((holiday) => (
                <HolidayItem key={holiday.id} holiday={holiday} />
              ))}
            </div>
          </Card>
          
          {/* Need a Break Card */}
          <Card className="bg-gradient-to-br from-primary-600 to-primary-700 text-white">
            <h3 className="font-semibold text-lg mb-2">Need a Break?</h3>
            <p className="text-sm text-primary-100 mb-4">
              Our AI suggests you've worked 45 days without a break. Stress levels might be higher than usual.
            </p>
            <Button
              variant="secondary"
              className="w-full bg-white text-primary-600 hover:bg-primary-50"
              onClick={() => setShowLeaveModal(true)}
            >
              Request Recommended Leave
            </Button>
          </Card>
        </motion.div>
      </div>
      
      {/* Leave Request Modal */}
      <Modal
        isOpen={showLeaveModal}
        onClose={() => setShowLeaveModal(false)}
        title="Apply for Leave"
        size="lg"
      >
        <LeaveRequestForm onSuccess={handleLeaveSubmitted} onCancel={() => setShowLeaveModal(false)} />
      </Modal>
    </motion.div>
  );
}

// Leave Balance Card Component
function LeaveBalanceCard({ balance, delay }: { balance: LeaveBalance; delay: number }) {
  const getBalanceColor = (type: string) => {
    switch (type) {
      case 'ANNUAL':
        return 'bg-blue-500';
      case 'SICK':
        return 'bg-red-500';
      case 'CASUAL':
        return 'bg-amber-500';
      default:
        return 'bg-gray-500';
    }
  };
  
  const getBalanceIcon = (type: string) => {
    switch (type) {
      case 'ANNUAL':
        return <Calendar className="w-5 h-5 text-blue-600" />;
      case 'SICK':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      case 'CASUAL':
        return <Clock className="w-5 h-5 text-amber-600" />;
      default:
        return <Calendar className="w-5 h-5 text-gray-600" />;
    }
  };
  
  const percentage = (balance.remaining_days / balance.total_days) * 100;
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay }}
      className="bg-white rounded-xl shadow-card p-5"
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className={cn(
            'w-10 h-10 rounded-lg flex items-center justify-center',
            balance.leave_type === 'ANNUAL' ? 'bg-blue-100' :
            balance.leave_type === 'SICK' ? 'bg-red-100' : 'bg-amber-100'
          )}>
            {getBalanceIcon(balance.leave_type)}
          </div>
          <span className="font-medium text-gray-900">{getLeaveTypeLabel(balance.leave_type)}</span>
        </div>
        
        {balance.accrual_rate_per_month > 0 && (
          <Badge variant="success" size="sm">
            <TrendingUp className="w-3 h-3 mr-1" />
            +{balance.accrual_rate_per_month} per month
          </Badge>
        )}
      </div>
      
      <div className="mb-3">
        <span className="text-3xl font-bold text-gray-900">{balance.remaining_days}</span>
        <span className="text-gray-500 ml-1">Days</span>
      </div>
      
      <div className="mb-2">
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${percentage}%` }}
            transition={{ duration: 0.5, delay: delay + 0.2 }}
            className={cn('h-full rounded-full', getBalanceColor(balance.leave_type))}
          />
        </div>
      </div>
      
      <p className="text-xs text-gray-500">
        {balance.used_days > 0 
          ? `Used ${balance.used_days} days this period`
          : `Remaining of ${balance.total_days} days yearly quota`
        }
      </p>
      
      {balance.balance_reset_date && (
        <p className="text-xs text-gray-400 mt-1">
          Balance reset in {Math.ceil((new Date(balance.balance_reset_date).getTime() - Date.now()) / (1000 * 60 * 60 * 24))} days
        </p>
      )}
    </motion.div>
  );
}

// Leave Request Row Component
function LeaveRequestRow({ request }: { request: LeaveRequest }) {
  return (
    <tr className="hover:bg-gray-50 transition-colors">
      <td className="py-4">
        <div className="flex items-center gap-3">
          <span className="text-xl">{getLeaveTypeIcon(request.leave_type)}</span>
          <span className="font-medium text-gray-900">{getLeaveTypeLabel(request.leave_type)}</span>
        </div>
      </td>
      <td className="py-4 text-gray-600">
        {formatDateRange(request.start_date, request.end_date)}
      </td>
      <td className="py-4 text-gray-600">
        {request.total_days} {request.total_days === 1 ? 'Day' : 'Days'}
      </td>
      <td className="py-4">
        <StatusBadge status={request.status} />
      </td>
      <td className="py-4">
        <button className="p-1 text-gray-400 hover:text-gray-600 rounded">
          <MoreVertical className="w-4 h-4" />
        </button>
      </td>
    </tr>
  );
}

// Holiday Item Component
function HolidayItem({ holiday }: { holiday: Holiday }) {
  return (
    <div className="flex items-center justify-between py-2">
      <div>
        <p className="font-medium text-gray-900">{holiday.name}</p>
        <p className="text-sm text-gray-500">{formatDate(holiday.date, 'EEEE, MMM d')}</p>
      </div>
      <Badge variant={holiday.type === 'PUBLIC' ? 'primary' : 'default'} size="sm">
        {holiday.type === 'PUBLIC' ? 'Public Holiday' : 'Regional'}
      </Badge>
    </div>
  );
}
