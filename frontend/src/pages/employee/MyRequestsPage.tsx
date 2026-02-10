import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  Plus,
  Search,
  Filter,
  Calendar,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  ChevronRight,
  FileText,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { leaveApi } from '@/services/api';
import { LeaveRequest } from '@/types';
import { Card, Badge, Button, Modal } from '@/components/ui';
import { LeaveRequestForm } from '@/components/forms/LeaveRequestForm';

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

export default function MyRequestsPage() {
  const [requests, setRequests] = useState<LeaveRequest[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showNewRequestModal, setShowNewRequestModal] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [selectedRequest, setSelectedRequest] = useState<LeaveRequest | null>(null);
  
  useEffect(() => {
    fetchRequests();
  }, []);
  
  const fetchRequests = async () => {
    try {
      const response = await leaveApi.getMyLeaveRequests();
      setRequests(response.data);
    } catch (error) {
      console.error('Failed to fetch requests:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const filteredRequests = requests.filter((req) => {
    const matchesSearch =
      req.leave_type.toLowerCase().includes(searchTerm.toLowerCase()) ||
      req.reason_text?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesFilter = filterStatus === 'all' || req.status.toLowerCase() === filterStatus;
    return matchesSearch && matchesFilter;
  });
  
  const getStatusBadge = (status: string) => {
    const variants: Record<string, { variant: 'success' | 'warning' | 'danger' | 'default'; icon: React.ElementType }> = {
      APPROVED: { variant: 'success', icon: CheckCircle },
      PENDING: { variant: 'warning', icon: Clock },
      PENDING_REVIEW: { variant: 'warning', icon: Clock },
      PENDING_HR: { variant: 'warning', icon: Clock },
      PENDING_MANAGER: { variant: 'warning', icon: Clock },
      REJECTED: { variant: 'danger', icon: XCircle },
      CANCELLED: { variant: 'default', icon: AlertCircle },
    };
    
    const config = variants[status] || { variant: 'default', icon: AlertCircle };
    const Icon = config.icon;
    
    const displayStatus = status === 'PENDING_REVIEW' ? 'PENDING HR REVIEW' : status.replace(/_/g, ' ');
    
    return (
      <Badge variant={config.variant} className="flex items-center gap-1">
        <Icon className="w-3 h-3" />
        {displayStatus}
      </Badge>
    );
  };
  
  const getLeaveTypeEmoji = (type: string) => {
    const emojis: Record<string, string> = {
      ANNUAL: '🏖️',
      SICK: '🏥',
      CASUAL: '☕',
      UNPAID: '📋',
    };
    return emojis[type] || '📅';
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
          <h1 className="text-2xl font-bold text-gray-900">My Leave Requests</h1>
          <p className="text-gray-600 mt-1">View and manage your leave requests</p>
        </div>
        <Button onClick={() => setShowNewRequestModal(true)}>
          <Plus className="w-4 h-4 mr-2" />
          New Request
        </Button>
      </motion.div>
      
      {/* Filters */}
      <motion.div variants={itemVariants}>
        <Card>
          <div className="p-4 flex items-center gap-4">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search requests..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div className="relative">
              <Filter className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="pl-10 pr-8 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 appearance-none bg-white"
              >
                <option value="all">All Status</option>
                <option value="approved">Approved</option>
                <option value="pending">Pending</option>
                <option value="pending_review">Pending Review</option>
                <option value="rejected">Rejected</option>
                <option value="cancelled">Cancelled</option>
              </select>
            </div>
          </div>
        </Card>
      </motion.div>
      
      {/* Requests List */}
      <motion.div variants={itemVariants}>
        {filteredRequests.length === 0 ? (
          <Card>
            <div className="p-12 text-center">
              <FileText className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">No requests found</h3>
              <p className="text-gray-500 mb-4">
                {searchTerm || filterStatus !== 'all'
                  ? 'Try adjusting your filters'
                  : "You haven't made any leave requests yet"}
              </p>
              <Button onClick={() => setShowNewRequestModal(true)}>
                <Plus className="w-4 h-4 mr-2" />
                Create Your First Request
              </Button>
            </div>
          </Card>
        ) : (
          <div className="space-y-4">
            {filteredRequests.map((request, index) => (
              <motion.div
                key={request.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => setSelectedRequest(request)}
                >
                  <div className="p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-12 h-12 bg-primary-50 rounded-xl flex items-center justify-center text-2xl">
                        {getLeaveTypeEmoji(request.leave_type)}
                      </div>
                      <div>
                        <div className="flex items-center gap-3">
                          <h3 className="font-semibold text-gray-900">
                            {request.leave_type} Leave
                          </h3>
                          {getStatusBadge(request.status)}
                        </div>
                        <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                          <span className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {new Date(request.start_date).toLocaleDateString()} -{' '}
                            {new Date(request.end_date).toLocaleDateString()}
                          </span>
                          <span className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {request.total_days || request.days_requested} day{(request.total_days || request.days_requested) !== 1 ? 's' : ''}
                          </span>
                        </div>
                      </div>
                    </div>
                    <ChevronRight className="w-5 h-5 text-gray-400" />
                  </div>
                </Card>
              </motion.div>
            ))}
          </div>
        )}
      </motion.div>
      
      {/* New Request Modal */}
      <Modal
        isOpen={showNewRequestModal}
        onClose={() => setShowNewRequestModal(false)}
        title="New Leave Request"
      >
        <LeaveRequestForm
          onSuccess={() => {
            setShowNewRequestModal(false);
            fetchRequests();
          }}
          onCancel={() => setShowNewRequestModal(false)}
        />
      </Modal>
      
      {/* Request Detail Modal */}
      <Modal
        isOpen={!!selectedRequest}
        onClose={() => setSelectedRequest(null)}
        title={`Leave Request #${selectedRequest?.id}`}
      >
        {selectedRequest && (
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-gray-600">Status</span>
              {getStatusBadge(selectedRequest.status)}
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Leave Type</p>
                <p className="font-medium text-gray-900">{selectedRequest.leave_type}</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Duration</p>
                <p className="font-medium text-gray-900">{selectedRequest.days_requested} days</p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Start Date</p>
                <p className="font-medium text-gray-900">
                  {new Date(selectedRequest.start_date).toLocaleDateString()}
                </p>
              </div>
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">End Date</p>
                <p className="font-medium text-gray-900">
                  {new Date(selectedRequest.end_date).toLocaleDateString()}
                </p>
              </div>
            </div>
            
            {selectedRequest.reason_text && (
              <div className="p-3 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Reason</p>
                <p className="text-gray-900 mt-1">{selectedRequest.reason_text}</p>
              </div>
            )}
            
            {/* AI Assessment */}
            {selectedRequest.ai_validity_score !== undefined && selectedRequest.ai_validity_score !== null && (
              <div className="p-4 bg-purple-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-purple-600 font-medium">AI Assessment</span>
                </div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600">Validity Score</span>
                  <span className="font-bold text-purple-600">
                    {selectedRequest.ai_validity_score}%
                  </span>
                </div>
                {selectedRequest.ai_rationale && (
                  <p className="text-sm text-gray-600 mt-2">{selectedRequest.ai_rationale}</p>
                )}
              </div>
            )}
            
            {/* Rejection Reason */}
            {selectedRequest.status === 'REJECTED' && (
              <div className="p-4 bg-red-50 rounded-lg border border-red-100">
                <div className="flex items-center gap-2 mb-2">
                  <XCircle className="w-4 h-4 text-red-600" />
                  <span className="text-red-600 font-medium">Rejection Reason</span>
                </div>
                <p className="text-gray-700">
                  {selectedRequest.reviewer_comments || selectedRequest.decision_explanation || 'No specific reason provided'}
                </p>
              </div>
            )}
            
            {/* Decision Explanation */}
            {selectedRequest.decision_explanation && selectedRequest.status !== 'REJECTED' && (
              <div className="p-4 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <FileText className="w-4 h-4 text-gray-600" />
                  <span className="text-gray-600 font-medium">Decision Details</span>
                </div>
                <p className="text-sm text-gray-600">{selectedRequest.decision_explanation}</p>
              </div>
            )}
            
            {(selectedRequest.status === 'PENDING' || selectedRequest.status === 'PENDING_REVIEW') && (
              <div className="pt-2">
                <Button
                  variant="secondary"
                  className="w-full"
                  onClick={async () => {
                    try {
                      await leaveApi.cancelRequest(selectedRequest.id);
                      toast.success('Leave request cancelled');
                      setSelectedRequest(null);
                      fetchRequests();
                    } catch (error) {
                      toast.error('Failed to cancel request');
                    }
                  }}
                >
                  Cancel Request
                </Button>
              </div>
            )}
          </div>
        )}
      </Modal>
    </motion.div>
  );
}
