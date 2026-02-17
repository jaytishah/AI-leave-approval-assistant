import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Clock,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Users,
  TrendingUp,
  Search,
  Filter,
  ChevronRight,
  Brain,
  Calendar,
  FileCheck,
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { adminApi } from '@/services/api';
import { Card, Badge, Button, Avatar } from '@/components/ui';

// Medical Certificate Validation interface
interface MedicalCertificateValidation {
  is_valid: boolean | null;
  result: 'VALID' | 'INVALID' | 'NEEDS_REVIEW' | 'EXTRACTION_FAILED';
  confidence_score: number;
}

interface PendingRequest {
  id: number;
  request_number: string;
  employee_name: string;
  employee_email: string;
  employee_avatar?: string;
  employee_department?: string;
  leave_type: string;
  start_date: string;
  end_date: string;
  total_days: number;
  days_requested?: number;
  reason_text?: string;
  medical_certificate_url?: string;
  medical_certificate_filename?: string;
  medical_certificate_validation?: MedicalCertificateValidation;
  ai_recommended_action?: string;
  ai_validity_score?: number;
  risk_level: string;
  status: string;
  created_at: string;
}

interface DashboardStats {
  total_pending: number;
  high_risk_flagged: number;
  team_coverage: number;
  pending_change_percent: number;
}

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.08,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function HRDashboardPage() {
  const [requests, setRequests] = useState<PendingRequest[]>([]);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRisk, setFilterRisk] = useState<string>('all');
  
  useEffect(() => {
    fetchDashboard();
  }, []);
  
  const fetchDashboard = async () => {
    try {
      const requestsRes = await adminApi.getPendingRequests();
      console.log('[HR Dashboard] Pending requests:', requestsRes.data);
      setRequests(requestsRes.data || []);
      
      // Calculate stats from requests
      const pending = requestsRes.data || [];
      const highRisk = pending.filter((r: PendingRequest) => r.risk_level === 'HIGH').length;
      setStats({
        total_pending: pending.length,
        high_risk_flagged: highRisk,
        team_coverage: 94,
        pending_change_percent: 0
      });
    } catch (error) {
      console.error('Failed to fetch HR dashboard:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const filteredRequests = requests.filter((req) => {
    const matchesSearch =
      req.employee_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.employee_department?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.employee_email?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterRisk === 'all' || req.risk_level?.toLowerCase() === filterRisk;
    return matchesSearch && matchesFilter;
  });
  
  const getRiskBadge = (risk: string, score: number) => {
    const variants: Record<string, 'success' | 'warning' | 'danger'> = {
      low: 'success',
      medium: 'warning',
      high: 'danger',
    };
    return (
      <div className="flex items-center gap-2">
        <Badge variant={variants[risk.toLowerCase()] || 'default'}>
          {risk.toUpperCase()}
        </Badge>
        <span className="text-sm text-gray-500">{score}%</span>
      </div>
    );
  };
  
  const getRecommendationIcon = (recommendation: string) => {
    switch (recommendation.toLowerCase()) {
      case 'approve':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'reject':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <AlertTriangle className="w-4 h-4 text-amber-500" />;
    }
  };
  
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
          <h1 className="text-2xl font-bold text-gray-900">HR Dashboard</h1>
          <p className="text-gray-600 mt-1">Manage and review leave requests</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="primary" className="px-3 py-1.5">
            <Brain className="w-4 h-4 mr-1" />
            AI Powered
          </Badge>
        </div>
      </motion.div>
      
      {/* Stats Cards */}
      <motion.div variants={itemVariants} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatsCard
          icon={Clock}
          label="Pending"
          value={stats?.total_pending || 0}
          color="amber"
        />
        <StatsCard
          icon={AlertTriangle}
          label="High Risk"
          value={stats?.high_risk_flagged || 0}
          color="red"
        />
        <StatsCard
          icon={Users}
          label="Team Coverage"
          value={`${stats?.team_coverage || 0}%`}
          color="green"
        />
        <StatsCard
          icon={TrendingUp}
          label="Change"
          value={`${stats?.pending_change_percent || 0}%`}
          color="blue"
        />
      </motion.div>
      
      {/* Pending Requests Section */}
      <motion.div variants={itemVariants}>
        <Card>
          <div className="p-6 border-b border-gray-100">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">
                Pending Leave Requests
              </h2>
              <div className="flex items-center gap-3">
                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search employees..."
                    value={searchTerm}
                    onChange={(e) => setSearchTerm(e.target.value)}
                    className="pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 w-64"
                  />
                </div>
                {/* Filter */}
                <div className="relative">
                  <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                  <select
                    value={filterRisk}
                    onChange={(e) => setFilterRisk(e.target.value)}
                    className="pl-10 pr-8 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none bg-white"
                  >
                    <option value="all">All Risk Levels</option>
                    <option value="low">Low Risk</option>
                    <option value="medium">Medium Risk</option>
                    <option value="high">High Risk</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Employee
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Leave Type
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Duration
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    AI Assessment
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Recommendation
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-100">
                {filteredRequests.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                      <Clock className="w-12 h-12 mx-auto mb-3 text-gray-300" />
                      <p className="font-medium">No pending requests</p>
                      <p className="text-sm">All caught up! 🎉</p>
                    </td>
                  </tr>
                ) : (
                  filteredRequests.map((request, index) => (
                    <motion.tr
                      key={request.id}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: index * 0.05 }}
                      className="hover:bg-gray-50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <Avatar
                            name={request.employee_name}
                            src={request.employee_avatar}
                            size="sm"
                          />
                          <div>
                            <p className="font-medium text-gray-900">
                              {request.employee_name}
                            </p>
                            <p className="text-sm text-gray-500">{request.employee_department || 'N/A'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Badge variant={request.leave_type === 'SICK' ? 'warning' : 'default'}>
                            {request.leave_type}
                          </Badge>
                          {/* Medical Certificate Indicator for SICK leave */}
                          {request.leave_type === 'SICK' && request.medical_certificate_url && (
                            <div className="relative group">
                              <div className={`w-6 h-6 rounded-full flex items-center justify-center ${
                                request.medical_certificate_validation?.result === 'VALID' 
                                  ? 'bg-green-100' 
                                  : request.medical_certificate_validation?.result === 'NEEDS_REVIEW'
                                  ? 'bg-amber-100'
                                  : request.medical_certificate_validation?.result === 'INVALID'
                                  ? 'bg-red-100'
                                  : 'bg-blue-100'
                              }`}>
                                <FileCheck className={`w-3.5 h-3.5 ${
                                  request.medical_certificate_validation?.result === 'VALID' 
                                    ? 'text-green-600' 
                                    : request.medical_certificate_validation?.result === 'NEEDS_REVIEW'
                                    ? 'text-amber-600'
                                    : request.medical_certificate_validation?.result === 'INVALID'
                                    ? 'text-red-600'
                                    : 'text-blue-600'
                                }`} />
                              </div>
                              {/* Tooltip */}
                              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                                <div className="bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                                  Medical Certificate: {request.medical_certificate_validation?.result || 'Attached'}
                                  {request.medical_certificate_validation?.confidence_score && (
                                    <span> ({Math.round(request.medical_certificate_validation.confidence_score * 100)}%)</span>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                          {/* Warning if SICK leave without certificate */}
                          {request.leave_type === 'SICK' && !request.medical_certificate_url && (
                            <div className="relative group">
                              <AlertTriangle className="w-4 h-4 text-red-500" />
                              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                                <div className="bg-gray-900 text-white text-xs rounded px-2 py-1 whitespace-nowrap">
                                  No medical certificate attached!
                                </div>
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <Calendar className="w-4 h-4 text-gray-400" />
                          <div>
                            <p className="text-sm font-medium text-gray-900">
                              {request.total_days || request.days_requested} day{(request.total_days || request.days_requested) !== 1 ? 's' : ''}
                            </p>
                            <p className="text-xs text-gray-500">
                              {new Date(request.start_date).toLocaleDateString()} -{' '}
                              {new Date(request.end_date).toLocaleDateString()}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        {getRiskBadge(request.risk_level || 'LOW', request.ai_validity_score || 0)}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          {getRecommendationIcon(request.ai_recommended_action || 'manual_review')}
                          <span className="text-sm font-medium capitalize">
                            {request.ai_recommended_action?.replace('_', ' ') || 'Pending'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link to={`/hr/requests/${request.id}`}>
                          <Button variant="ghost" size="sm">
                            Review
                            <ChevronRight className="w-4 h-4 ml-1" />
                          </Button>
                        </Link>
                      </td>
                    </motion.tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </Card>
      </motion.div>
      
      {/* Quick Actions & Insights */}
      <motion.div variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* AI Insights */}
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-blue-500 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">AI Insights</h3>
                <p className="text-sm text-gray-500">Smart recommendations</p>
              </div>
            </div>
            
            <div className="space-y-3">
              <InsightItem
                type="info"
                message="3 requests from Engineering dept pending - consider batch review"
              />
              <InsightItem
                type="warning"
                message="High leave requests expected next week (holiday season)"
              />
              <InsightItem
                type="success"
                message="95% of auto-approved requests had no issues last month"
              />
            </div>
          </div>
        </Card>
        
        {/* Team Overview */}
        <Card>
          <div className="p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 bg-gradient-to-r from-green-500 to-teal-500 rounded-lg flex items-center justify-center">
                <Users className="w-5 h-5 text-white" />
              </div>
              <div>
                <h3 className="font-semibold text-gray-900">Currently On Leave</h3>
                <p className="text-sm text-gray-500">Team members away today</p>
              </div>
            </div>
            
            <div className="space-y-3">
              {[
                { name: 'Sarah Johnson', dept: 'Marketing', return: 'Tomorrow' },
                { name: 'Mike Chen', dept: 'Engineering', return: 'Dec 15' },
                { name: 'Emily Davis', dept: 'Design', return: 'Dec 18' },
              ].map((person, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center gap-3">
                    <Avatar name={person.name} size="sm" />
                    <div>
                      <p className="font-medium text-sm text-gray-900">{person.name}</p>
                      <p className="text-xs text-gray-500">{person.dept}</p>
                    </div>
                  </div>
                  <span className="text-xs text-gray-500">Returns {person.return}</span>
                </div>
              ))}
            </div>
          </div>
        </Card>
      </motion.div>
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
    amber: 'bg-amber-50 text-amber-600',
    green: 'bg-green-50 text-green-600',
    red: 'bg-red-50 text-red-600',
    orange: 'bg-orange-50 text-orange-600',
    blue: 'bg-blue-50 text-blue-600',
    purple: 'bg-purple-50 text-purple-600',
  };
  
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      className="bg-white rounded-xl border border-gray-100 p-4"
    >
      <div className={`w-10 h-10 rounded-lg ${colorClasses[color]} flex items-center justify-center mb-3`}>
        <Icon className="w-5 h-5" />
      </div>
      <p className="text-2xl font-bold text-gray-900">{value}</p>
      <p className="text-sm text-gray-500">{label}</p>
    </motion.div>
  );
}

// Insight Item Component
interface InsightItemProps {
  type: 'info' | 'warning' | 'success';
  message: string;
}

function InsightItem({ type, message }: InsightItemProps) {
  const styles: Record<string, { bg: string; icon: React.ElementType; iconColor: string }> = {
    info: { bg: 'bg-blue-50', icon: Brain, iconColor: 'text-blue-500' },
    warning: { bg: 'bg-amber-50', icon: AlertTriangle, iconColor: 'text-amber-500' },
    success: { bg: 'bg-green-50', icon: CheckCircle, iconColor: 'text-green-500' },
  };
  
  const style = styles[type];
  const Icon = style.icon;
  
  return (
    <div className={`p-3 rounded-lg ${style.bg} flex items-start gap-3`}>
      <Icon className={`w-4 h-4 ${style.iconColor} flex-shrink-0 mt-0.5`} />
      <p className="text-sm text-gray-700">{message}</p>
    </div>
  );
}
