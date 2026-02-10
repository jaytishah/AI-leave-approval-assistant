import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  Brain,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Clock,
  Building2,
  FileText,
  Shield,
  History,
  MessageSquare,
  Mail,
  Download,
  Eye,
  FileCheck,
  Stethoscope,
} from 'lucide-react';
import toast from 'react-hot-toast';
import { leaveApi } from '@/services/api';
import { Card, Badge, Button, Avatar, Modal } from '@/components/ui';

// Medical Certificate Validation interface
interface MedicalCertificateValidation {
  is_valid: boolean | null;
  result: 'VALID' | 'INVALID' | 'NEEDS_REVIEW' | 'EXTRACTION_FAILED';
  confidence_score: number;
  detected_fields: {
    date?: string;
    patient_name?: string;
    doctor_name?: string;
    hospital?: string;
    diagnosis?: string;
    leave_days?: string;
    registration_no?: string;
  };
  validation_notes: string[];
  extracted_text_preview: string | null;
  error?: string;
}

interface LeaveRequestDetail {
  id: number;
  request_number: string;
  employee_id: number;
  employee_name: string;
  employee_email: string;
  employee_department?: string;
  employee_avatar?: string;
  employee_total_balance?: number;
  employee_used_ytd?: number;
  leave_type: string;
  start_date: string;
  end_date: string;
  total_days: number;
  reason_text?: string;
  medical_certificate_url?: string;
  medical_certificate_filename?: string;
  medical_certificate_size?: number;
  medical_certificate_validation?: MedicalCertificateValidation;
  status: string;
  risk_level: string;
  ai_validity_score?: number;
  ai_risk_flags?: string[];
  ai_recommended_action?: string;
  ai_rationale?: string;
  ai_reason_category?: string;
  decision_engine?: string;
  decision_explanation?: string;
  reviewed_by?: number;
  reviewed_at?: string;
  reviewer_comments?: string;
  created_at: string;
  updated_at?: string;
}

interface AuditEntry {
  id: number;
  action: string;
  actor_id?: number;
  actor_type: string;
  previous_status?: string;
  new_status?: string;
  details?: string;
  created_at: string;
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

export default function LeaveRequestDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [request, setRequest] = useState<LeaveRequestDetail | null>(null);
  const [auditTrail, setAuditTrail] = useState<AuditEntry[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const [approveComment, setApproveComment] = useState('');
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [showCertificateModal, setShowCertificateModal] = useState(false);
  const [showExtractedTextModal, setShowExtractedTextModal] = useState(false);
  
  useEffect(() => {
    if (id) {
      fetchRequestDetail();
      fetchAuditTrail();
    }
  }, [id]);
  
  const fetchRequestDetail = async () => {
    try {
      const response = await leaveApi.getLeaveRequest(Number(id));
      console.log('[HR Detail] Request data:', response.data);
      setRequest(response.data);
    } catch (error) {
      console.error('Failed to fetch request detail:', error);
      toast.error('Failed to load request details');
    } finally {
      setIsLoading(false);
    }
  };
  
  const fetchAuditTrail = async () => {
    try {
      const response = await leaveApi.getAuditTrail(Number(id));
      setAuditTrail(response.data || []);
    } catch (error) {
      console.error('Failed to fetch audit trail:', error);
    }
  };
  
  const handleApprove = async () => {
    setIsProcessing(true);
    try {
      await leaveApi.approveLeaveRequest(Number(id), approveComment || undefined);
      toast.success('Leave request approved! Email notification sent to employee.');
      navigate('/hr');
    } catch (error) {
      toast.error('Failed to approve request');
    } finally {
      setIsProcessing(false);
      setShowApproveModal(false);
    }
  };
  
  const handleReject = async () => {
    if (!rejectReason.trim()) {
      toast.error('Please provide a reason for rejection');
      return;
    }
    setIsProcessing(true);
    try {
      await leaveApi.rejectLeaveRequest(Number(id), rejectReason);
      toast.success('Leave request rejected! Email notification sent to employee.');
      navigate('/hr');
    } catch (error) {
      toast.error('Failed to reject request');
    } finally {
      setIsProcessing(false);
      setShowRejectModal(false);
    }
  };
  
  const getRiskColor = (risk?: string) => {
    const colors: Record<string, string> = {
      low: 'text-green-600 bg-green-50',
      medium: 'text-amber-600 bg-amber-50',
      high: 'text-red-600 bg-red-50',
    };
    return colors[risk?.toLowerCase() || 'low'] || 'text-gray-600 bg-gray-50';
  };
  
  const getStatusBadge = (status: string) => {
    const variants: Record<string, 'success' | 'warning' | 'danger' | 'default'> = {
      APPROVED: 'success',
      PENDING: 'warning',
      PENDING_REVIEW: 'warning',
      REJECTED: 'danger',
      CANCELLED: 'default',
    };
    return <Badge variant={variants[status] || 'default'}>{status.replace(/_/g, ' ')}</Badge>;
  };
  
  const isPending = request?.status === 'PENDING' || request?.status === 'PENDING_REVIEW';
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }
  
  if (!request) {
    return (
      <div className="text-center py-12">
        <p className="text-gray-500">Request not found</p>
        <Button className="mt-4" onClick={() => navigate('/hr')}>
          Back to Dashboard
        </Button>
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
        <div className="flex items-center gap-4">
          <Button variant="ghost" onClick={() => navigate('/hr')}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold text-gray-900">
                Leave Request #{request.request_number || request.id}
              </h1>
              {getStatusBadge(request.status)}
            </div>
            <p className="text-gray-600">Submitted on {new Date(request.created_at).toLocaleDateString()}</p>
          </div>
        </div>
        
        {isPending && (
          <div className="flex items-center gap-3">
            <Button
              variant="secondary"
              onClick={() => setShowRejectModal(true)}
              disabled={isProcessing}
            >
              <XCircle className="w-4 h-4 mr-2" />
              Reject
            </Button>
            <Button onClick={() => setShowApproveModal(true)} disabled={isProcessing}>
              <CheckCircle className="w-4 h-4 mr-2" />
              Approve
            </Button>
          </div>
        )}
      </motion.div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content - Left Side */}
        <div className="lg:col-span-2 space-y-6">
          {/* Employee Info Card */}
          <motion.div variants={itemVariants}>
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Employee Information</h2>
                <div className="flex items-start gap-4">
                  <Avatar name={request.employee_name} src={request.employee_avatar} size="lg" />
                  <div className="flex-1">
                    <h3 className="font-semibold text-gray-900 text-lg">{request.employee_name}</h3>
                    <p className="text-gray-500">{request.employee_email}</p>
                    {request.employee_department && (
                      <div className="flex items-center gap-2 mt-2 text-sm text-gray-600">
                        <Building2 className="w-4 h-4" />
                        {request.employee_department}
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </Card>
          </motion.div>
          
          {/* Request Details */}
          <motion.div variants={itemVariants}>
            <Card>
              <div className="p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Request Details</h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500 mb-1">Leave Type</p>
                    <Badge variant={request.leave_type === 'SICK' ? 'warning' : 'primary'}>
                      {request.leave_type}
                    </Badge>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500 mb-1">Duration</p>
                    <p className="font-semibold text-gray-900">{request.total_days} days</p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500 mb-1">Start Date</p>
                    <p className="font-semibold text-gray-900">
                      {new Date(request.start_date).toLocaleDateString()}
                    </p>
                  </div>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500 mb-1">End Date</p>
                    <p className="font-semibold text-gray-900">
                      {new Date(request.end_date).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                
                {request.reason_text && (
                  <div className="mt-4 p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-2 mb-2">
                      <FileText className="w-4 h-4 text-gray-400" />
                      <p className="text-sm font-medium text-gray-700">Reason Provided</p>
                    </div>
                    <p className="text-gray-600">{request.reason_text}</p>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
          
          {/* Medical Certificate Section - Only for SICK leave */}
          {request.leave_type === 'SICK' && request.medical_certificate_url && (
            <motion.div variants={itemVariants}>
              <Card>
                <div className="p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                      <Stethoscope className="w-5 h-5 text-blue-500" />
                      <h2 className="text-lg font-semibold text-gray-900">Medical Certificate</h2>
                    </div>
                    {request.medical_certificate_validation && (
                      <Badge 
                        variant={
                          request.medical_certificate_validation.result === 'VALID' ? 'success' :
                          request.medical_certificate_validation.result === 'NEEDS_REVIEW' ? 'warning' :
                          request.medical_certificate_validation.result === 'INVALID' ? 'danger' : 'default'
                        }
                      >
                        {request.medical_certificate_validation.result === 'VALID' && <CheckCircle className="w-3 h-3 mr-1" />}
                        {request.medical_certificate_validation.result === 'NEEDS_REVIEW' && <AlertTriangle className="w-3 h-3 mr-1" />}
                        {request.medical_certificate_validation.result === 'INVALID' && <XCircle className="w-3 h-3 mr-1" />}
                        {request.medical_certificate_validation.result.replace('_', ' ')}
                      </Badge>
                    )}
                  </div>
                  
                  {/* File Info */}
                  <div className="bg-blue-50 rounded-lg p-4 mb-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                          <FileCheck className="w-5 h-5 text-blue-600" />
                        </div>
                        <div>
                          <p className="font-medium text-gray-900">{request.medical_certificate_filename || 'medical_certificate'}</p>
                          <p className="text-sm text-gray-500">
                            {request.medical_certificate_size 
                              ? `${(request.medical_certificate_size / 1024).toFixed(2)} KB`
                              : 'Size unknown'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Button 
                          variant="secondary" 
                          size="sm"
                          onClick={() => setShowCertificateModal(true)}
                        >
                          <Eye className="w-4 h-4 mr-1" />
                          View
                        </Button>
                        <Button 
                          variant="secondary" 
                          size="sm"
                          onClick={() => {
                            const link = document.createElement('a');
                            link.href = request.medical_certificate_url || '';
                            link.download = request.medical_certificate_filename || 'medical_certificate';
                            link.click();
                          }}
                        >
                          <Download className="w-4 h-4 mr-1" />
                          Download
                        </Button>
                      </div>
                    </div>
                  </div>
                  
                  {/* Validation Results */}
                  {request.medical_certificate_validation && (
                    <div className="space-y-4">
                      {/* Confidence Score */}
                      <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                        <span className="text-sm font-medium text-gray-700">Validation Confidence</span>
                        <div className="flex items-center gap-2">
                          <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div 
                              className={`h-full rounded-full ${
                                request.medical_certificate_validation.confidence_score >= 0.7 ? 'bg-green-500' :
                                request.medical_certificate_validation.confidence_score >= 0.4 ? 'bg-amber-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${request.medical_certificate_validation.confidence_score * 100}%` }}
                            />
                          </div>
                          <span className="font-semibold text-gray-900">
                            {Math.round(request.medical_certificate_validation.confidence_score * 100)}%
                          </span>
                        </div>
                      </div>
                      
                      {/* Detected Fields */}
                      {request.medical_certificate_validation.detected_fields && 
                       Object.keys(request.medical_certificate_validation.detected_fields).length > 0 && (
                        <div className="p-4 bg-green-50 rounded-lg">
                          <div className="flex items-center gap-2 mb-3">
                            <CheckCircle className="w-4 h-4 text-green-600" />
                            <h4 className="font-medium text-green-800">Extracted Information</h4>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            {request.medical_certificate_validation.detected_fields.doctor_name && (
                              <div>
                                <p className="text-xs text-gray-500 uppercase">Doctor Name</p>
                                <p className="text-sm font-medium text-gray-900 capitalize">
                                  {request.medical_certificate_validation.detected_fields.doctor_name}
                                </p>
                              </div>
                            )}
                            {request.medical_certificate_validation.detected_fields.date && (
                              <div>
                                <p className="text-xs text-gray-500 uppercase">Date</p>
                                <p className="text-sm font-medium text-gray-900">
                                  {request.medical_certificate_validation.detected_fields.date}
                                </p>
                              </div>
                            )}
                            {request.medical_certificate_validation.detected_fields.diagnosis && (
                              <div>
                                <p className="text-xs text-gray-500 uppercase">Diagnosis</p>
                                <p className="text-sm font-medium text-gray-900 capitalize">
                                  {request.medical_certificate_validation.detected_fields.diagnosis}
                                </p>
                              </div>
                            )}
                            {request.medical_certificate_validation.detected_fields.hospital && (
                              <div>
                                <p className="text-xs text-gray-500 uppercase">Hospital/Clinic</p>
                                <p className="text-sm font-medium text-gray-900 capitalize">
                                  {request.medical_certificate_validation.detected_fields.hospital}
                                </p>
                              </div>
                            )}
                            {request.medical_certificate_validation.detected_fields.patient_name && (
                              <div>
                                <p className="text-xs text-gray-500 uppercase">Patient Name</p>
                                <p className="text-sm font-medium text-gray-900 capitalize">
                                  {request.medical_certificate_validation.detected_fields.patient_name}
                                </p>
                              </div>
                            )}
                            {request.medical_certificate_validation.detected_fields.registration_no && (
                              <div>
                                <p className="text-xs text-gray-500 uppercase">Registration No</p>
                                <p className="text-sm font-medium text-gray-900 uppercase">
                                  {request.medical_certificate_validation.detected_fields.registration_no}
                                </p>
                              </div>
                            )}
                            {request.medical_certificate_validation.detected_fields.leave_days && (
                              <div>
                                <p className="text-xs text-gray-500 uppercase">Recommended Leave</p>
                                <p className="text-sm font-medium text-gray-900">
                                  {request.medical_certificate_validation.detected_fields.leave_days}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                      
                      {/* Extracted Text Preview */}
                      {request.medical_certificate_validation.extracted_text_preview && (
                        <div className="p-4 bg-gray-50 rounded-lg">
                          <div className="flex items-center justify-between mb-2">
                            <div className="flex items-center gap-2">
                              <FileText className="w-4 h-4 text-gray-500" />
                              <h4 className="font-medium text-gray-700">Extracted Text Preview</h4>
                            </div>
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => setShowExtractedTextModal(true)}
                            >
                              View Full Text
                            </Button>
                          </div>
                          <p className="text-sm text-gray-600 bg-white p-3 rounded border border-gray-200 font-mono whitespace-pre-wrap">
                            {request.medical_certificate_validation.extracted_text_preview.substring(0, 200)}
                            {request.medical_certificate_validation.extracted_text_preview.length > 200 && '...'}
                          </p>
                        </div>
                      )}
                      
                      {/* Validation Notes */}
                      {request.medical_certificate_validation.validation_notes && 
                       request.medical_certificate_validation.validation_notes.length > 0 && (
                        <div className="p-4 bg-amber-50 rounded-lg">
                          <div className="flex items-center gap-2 mb-2">
                            <AlertTriangle className="w-4 h-4 text-amber-600" />
                            <h4 className="font-medium text-amber-800">Validation Notes</h4>
                          </div>
                          <ul className="space-y-1">
                            {request.medical_certificate_validation.validation_notes.map((note, index) => (
                              <li key={index} className="text-sm text-amber-700 flex items-start gap-2">
                                <span className="text-amber-400">•</span>
                                {note}
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                      
                      {/* Error Message */}
                      {request.medical_certificate_validation.error && (
                        <div className="p-4 bg-red-50 rounded-lg">
                          <div className="flex items-center gap-2 mb-2">
                            <XCircle className="w-4 h-4 text-red-600" />
                            <h4 className="font-medium text-red-800">Extraction Error</h4>
                          </div>
                          <p className="text-sm text-red-700">{request.medical_certificate_validation.error}</p>
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* If no validation results */}
                  {!request.medical_certificate_validation && (
                    <div className="p-4 bg-gray-50 rounded-lg text-center">
                      <AlertTriangle className="w-8 h-8 text-amber-500 mx-auto mb-2" />
                      <p className="text-sm text-gray-600">Certificate validation pending or not available</p>
                      <p className="text-xs text-gray-500 mt-1">Please review the certificate manually</p>
                    </div>
                  )}
                </div>
              </Card>
            </motion.div>
          )}
          
          {/* Leave Balance */}
          {(request.employee_total_balance !== undefined || request.employee_used_ytd !== undefined) && (
            <motion.div variants={itemVariants}>
              <Card>
                <div className="p-6">
                  <h2 className="text-lg font-semibold text-gray-900 mb-4">Leave Balance</h2>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-green-50 rounded-lg">
                      <p className="text-2xl font-bold text-green-600">
                        {(request.employee_total_balance || 0) - (request.employee_used_ytd || 0)}
                      </p>
                      <p className="text-sm text-gray-600">Days Remaining</p>
                    </div>
                    <div className="text-center p-4 bg-blue-50 rounded-lg">
                      <p className="text-2xl font-bold text-blue-600">{request.employee_used_ytd || 0}</p>
                      <p className="text-sm text-gray-600">Days Used</p>
                    </div>
                    <div className="text-center p-4 bg-purple-50 rounded-lg">
                      <p className="text-2xl font-bold text-purple-600">{request.employee_total_balance || 0}</p>
                      <p className="text-sm text-gray-600">Total Entitlement</p>
                    </div>
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
          
          {/* Decision Info (if already decided) */}
          {(request.status === 'APPROVED' || request.status === 'REJECTED') && (
            <motion.div variants={itemVariants}>
              <Card>
                <div className={`p-6 ${request.status === 'APPROVED' ? 'bg-green-50' : 'bg-red-50'} rounded-lg`}>
                  <div className="flex items-center gap-2 mb-3">
                    {request.status === 'APPROVED' ? (
                      <CheckCircle className="w-5 h-5 text-green-600" />
                    ) : (
                      <XCircle className="w-5 h-5 text-red-600" />
                    )}
                    <h2 className={`text-lg font-semibold ${request.status === 'APPROVED' ? 'text-green-800' : 'text-red-800'}`}>
                      {request.status === 'APPROVED' ? 'Request Approved' : 'Request Rejected'}
                    </h2>
                  </div>
                  {request.reviewer_comments && (
                    <div className="mb-3">
                      <p className="text-sm font-medium text-gray-700 mb-1">HR Comments:</p>
                      <p className="text-gray-600">{request.reviewer_comments}</p>
                    </div>
                  )}
                  {request.decision_explanation && (
                    <div>
                      <p className="text-sm font-medium text-gray-700 mb-1">Decision Details:</p>
                      <p className="text-gray-600 text-sm">{request.decision_explanation}</p>
                    </div>
                  )}
                  {request.reviewed_at && (
                    <p className="text-xs text-gray-500 mt-3">
                      Reviewed on {new Date(request.reviewed_at).toLocaleString()}
                    </p>
                  )}
                </div>
              </Card>
            </motion.div>
          )}
          
          {/* Audit Trail */}
          <motion.div variants={itemVariants}>
            <Card>
              <div className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <History className="w-5 h-5 text-gray-400" />
                  <h2 className="text-lg font-semibold text-gray-900">Audit Trail</h2>
                </div>
                <div className="space-y-4">
                  {auditTrail.length > 0 ? (
                    auditTrail.map((entry, index) => (
                      <div
                        key={entry.id}
                        className="flex items-start gap-4 relative"
                      >
                        {index !== auditTrail.length - 1 && (
                          <div className="absolute left-4 top-8 bottom-0 w-px bg-gray-200" />
                        )}
                        <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center flex-shrink-0">
                          <Clock className="w-4 h-4 text-primary-600" />
                        </div>
                        <div className="flex-1 pb-4">
                          <p className="font-medium text-gray-900">{entry.action}</p>
                          <p className="text-sm text-gray-500">by {entry.actor_type}</p>
                          {entry.details && (
                            <p className="text-sm text-gray-600 mt-1">{entry.details}</p>
                          )}
                          <p className="text-xs text-gray-400 mt-1">
                            {new Date(entry.created_at).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    ))
                  ) : (
                    <p className="text-gray-500 text-sm">No audit entries yet</p>
                  )}
                </div>
              </div>
            </Card>
          </motion.div>
        </div>
        
        {/* AI Advisory Panel - Right Side */}
        <div className="space-y-6">
          {/* AI Score Card */}
          <motion.div variants={itemVariants}>
            <Card className="overflow-hidden">
              <div className="bg-gradient-to-r from-purple-600 to-blue-600 p-6 text-white">
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 bg-white/20 rounded-lg flex items-center justify-center">
                    <Brain className="w-6 h-6" />
                  </div>
                  <div>
                    <h3 className="font-semibold">AI Advisory Panel</h3>
                    <p className="text-sm text-white/80">Powered by Gemini AI</p>
                  </div>
                </div>
                
                <div className="text-center py-4">
                  <div className="text-5xl font-bold mb-2">
                    {request.ai_validity_score ?? 'N/A'}
                    {request.ai_validity_score !== null && request.ai_validity_score !== undefined && '%'}
                  </div>
                  <p className="text-white/80">Validity Score</p>
                </div>
              </div>
              
              <div className="p-6 space-y-4">
                {/* Risk Level */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Risk Level</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getRiskColor(request.risk_level)}`}>
                    {request.risk_level?.toUpperCase() || 'N/A'}
                  </span>
                </div>
                
                {/* Recommendation */}
                <div className="flex items-center justify-between">
                  <span className="text-gray-600">Recommendation</span>
                  <div className="flex items-center gap-2">
                    {request.ai_recommended_action?.toLowerCase() === 'approve' ? (
                      <CheckCircle className="w-4 h-4 text-green-500" />
                    ) : request.ai_recommended_action?.toLowerCase() === 'reject' ? (
                      <XCircle className="w-4 h-4 text-red-500" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                    )}
                    <span className="font-medium capitalize">
                      {request.ai_recommended_action?.replace('_', ' ') || 'Pending'}
                    </span>
                  </div>
                </div>
                
                {/* Category */}
                {request.ai_reason_category && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Category</span>
                    <span className="font-medium">{request.ai_reason_category}</span>
                  </div>
                )}
                
                {/* Decision Engine */}
                {request.decision_engine && (
                  <div className="flex items-center justify-between">
                    <span className="text-gray-600">Decision By</span>
                    <span className="font-medium text-sm">{request.decision_engine}</span>
                  </div>
                )}
              </div>
            </Card>
          </motion.div>
          
          {/* Risk Flags */}
          {request.ai_risk_flags && request.ai_risk_flags.length > 0 && (
            <motion.div variants={itemVariants}>
              <Card>
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Shield className="w-5 h-5 text-amber-500" />
                    <h3 className="font-semibold text-gray-900">Risk Flags</h3>
                  </div>
                  <div className="space-y-2">
                    {request.ai_risk_flags.map((flag, index) => (
                      <div
                        key={index}
                        className="flex items-start gap-2 p-3 bg-amber-50 rounded-lg"
                      >
                        <AlertTriangle className="w-4 h-4 text-amber-500 flex-shrink-0 mt-0.5" />
                        <p className="text-sm text-amber-800">{flag}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </Card>
            </motion.div>
          )}
          
          {/* AI Rationale */}
          {request.ai_rationale && (
            <motion.div variants={itemVariants}>
              <Card>
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <MessageSquare className="w-5 h-5 text-blue-500" />
                    <h3 className="font-semibold text-gray-900">AI Analysis</h3>
                  </div>
                  <p className="text-gray-600 text-sm leading-relaxed">
                    {request.ai_rationale}
                  </p>
                </div>
              </Card>
            </motion.div>
          )}
          
          {/* Email Notification Info */}
          <motion.div variants={itemVariants}>
            <Card>
              <div className="p-6">
                <div className="flex items-center gap-2 mb-3">
                  <Mail className="w-5 h-5 text-blue-500" />
                  <h3 className="font-semibold text-gray-900">Notifications</h3>
                </div>
                <p className="text-sm text-gray-600">
                  Upon approval or rejection, an email notification will be automatically sent to{' '}
                  <strong>{request.employee_email}</strong> with the decision details.
                </p>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
      
      {/* Approve Modal */}
      <Modal
        isOpen={showApproveModal}
        onClose={() => setShowApproveModal(false)}
        title="Approve Leave Request"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Are you sure you want to approve this leave request? An email notification will be sent to the employee.
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Comments (optional)
            </label>
            <textarea
              value={approveComment}
              onChange={(e) => setApproveComment(e.target.value)}
              rows={3}
              placeholder="Add any comments for the employee..."
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>
          <div className="flex gap-3">
            <Button
              variant="secondary"
              onClick={() => setShowApproveModal(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              onClick={handleApprove}
              isLoading={isProcessing}
              className="flex-1"
            >
              <CheckCircle className="w-4 h-4 mr-2" />
              Confirm Approval
            </Button>
          </div>
        </div>
      </Modal>
      
      {/* Reject Modal */}
      <Modal
        isOpen={showRejectModal}
        onClose={() => setShowRejectModal(false)}
        title="Reject Leave Request"
      >
        <div className="space-y-4">
          <p className="text-gray-600">
            Please provide a reason for rejecting this leave request. This will be shared with the employee via email.
          </p>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1.5">
              Rejection Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
              rows={4}
              placeholder="Enter the reason for rejection..."
              className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>
          <div className="flex gap-3">
            <Button
              variant="secondary"
              onClick={() => setShowRejectModal(false)}
              className="flex-1"
            >
              Cancel
            </Button>
            <Button
              variant="danger"
              onClick={handleReject}
              isLoading={isProcessing}
              className="flex-1"
            >
              <XCircle className="w-4 h-4 mr-2" />
              Confirm Rejection
            </Button>
          </div>
        </div>
      </Modal>
      
      {/* Medical Certificate View Modal */}
      <Modal
        isOpen={showCertificateModal}
        onClose={() => setShowCertificateModal(false)}
        title="Medical Certificate"
      >
        <div className="space-y-4">
          {request?.medical_certificate_url && (
            <>
              {request.medical_certificate_filename?.toLowerCase().endsWith('.pdf') ? (
                <div className="text-center p-8 bg-gray-50 rounded-lg">
                  <FileCheck className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-600 mb-4">PDF files cannot be previewed directly.</p>
                  <Button
                    onClick={() => {
                      const link = document.createElement('a');
                      link.href = request.medical_certificate_url || '';
                      link.download = request.medical_certificate_filename || 'medical_certificate.pdf';
                      link.click();
                    }}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Download PDF
                  </Button>
                </div>
              ) : (
                <div className="max-h-[60vh] overflow-auto">
                  <img
                    src={request.medical_certificate_url}
                    alt="Medical Certificate"
                    className="w-full rounded-lg"
                  />
                </div>
              )}
              <div className="flex items-center justify-between text-sm text-gray-500">
                <span>{request.medical_certificate_filename}</span>
                <span>
                  {request.medical_certificate_size 
                    ? `${(request.medical_certificate_size / 1024).toFixed(2)} KB`
                    : 'Size unknown'}
                </span>
              </div>
            </>
          )}
        </div>
      </Modal>
      
      {/* Extracted Text Modal */}
      <Modal
        isOpen={showExtractedTextModal}
        onClose={() => setShowExtractedTextModal(false)}
        title="Extracted Text from Medical Certificate"
      >
        <div className="space-y-4">
          <div className="bg-gray-50 p-4 rounded-lg max-h-[50vh] overflow-auto">
            <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono">
              {request?.medical_certificate_validation?.extracted_text_preview || 'No text extracted'}
            </pre>
          </div>
          <p className="text-xs text-gray-500">
            This text was automatically extracted using OCR (Optical Character Recognition) for PDF and image files.
          </p>
        </div>
      </Modal>
    </motion.div>
  );
}
