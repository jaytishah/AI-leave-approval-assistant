// User Types
export interface User {
  id: number;
  email: string;
  first_name: string;
  last_name: string;
  full_name?: string;
  role: 'EMPLOYEE' | 'HR' | 'ADMIN';
  department_id: number | null;
  manager_id: number | null;
  location: string | null;
  grade: string | null;
  level: string | null;
  tenure_months: number;
  is_active: boolean;
  avatar_url: string | null;
  created_at: string;
  department_name?: string;
}

// Leave Types
export type LeaveType = 'ANNUAL' | 'SICK' | 'CASUAL' | 'MATERNITY' | 'PATERNITY' | 'UNPAID';
export type LeaveStatus = 'PENDING' | 'APPROVED' | 'REJECTED' | 'CANCELLED' | 'PENDING_REVIEW';
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH';

export interface LeaveRequest {
  id: number;
  request_number: string;
  employee_id: number;
  leave_type: LeaveType;
  start_date: string;
  end_date: string;
  total_days: number;
  days_requested: number;
  reason_text: string | null;
  medical_certificate_url: string | null;
  medical_certificate_filename: string | null;
  medical_certificate_size: number | null;
  medical_certificate_validation: MedicalCertificateValidation | null;
  status: LeaveStatus;
  risk_level: RiskLevel;
  ai_validity_score: number | null;
  ai_risk_flags: string[] | null;
  ai_recommended_action: string | null;
  ai_rationale: string | null;
  ai_reason_category: string | null;
  decision_engine: string | null;
  decision_explanation: string | null;
  reviewed_by: number | null;
  reviewed_at: string | null;
  reviewer_comments: string | null;
  created_at: string;
  updated_at: string | null;
}

// Medical Certificate Validation Result
export interface MedicalCertificateValidation {
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

export interface LeaveRequestWithEmployee extends LeaveRequest {
  employee_name: string;
  employee_email: string;
  employee_department: string | null;
  employee_avatar: string | null;
}

export interface LeaveRequestDetail extends LeaveRequestWithEmployee {
  employee_total_balance: number | null;
  employee_used_ytd: number | null;
  team_coverage: number | null;
  team_context: string | null;
  historical_pattern: string | null;
}

export interface LeaveBalance {
  id: number;
  employee_id: number;
  leave_type: LeaveType;
  year: number;
  total_days: number;
  used_days: number;
  pending_days: number;
  remaining_days: number;
  accrual_rate_per_month: number;
  balance_reset_date: string | null;
}

// Policy Types
export interface LeavePolicy {
  id: number;
  name: string;
  department_id: number | null;
  location: string | null;
  grade: string | null;
  annual_leave_days: number;
  sick_leave_days: number;
  casual_leave_days: number;
  maternity_leave_days: number;
  paternity_leave_days: number;
  allow_negative_balance: boolean;
  reason_mandatory: boolean;
  require_manager_approval: boolean;
  long_leave_threshold_days: number;
  min_advance_days_for_long_leave: number;
  max_consecutive_leave_days: number;
  max_unplanned_leaves_30_days: number;
  max_leaves_90_days: number;
  max_pattern_score: number;
  history_window_days: number;
  blackout_periods: { start_date: string; end_date: string }[];
  holidays: string[];
  is_active: boolean;
  created_at: string;
}

// Holiday Types
export interface Holiday {
  id: number;
  name: string;
  date: string;
  type: string;
  location: string | null;
  is_active: boolean;
  created_at: string;
}

// Audit Log Types
export interface AuditLog {
  id: number;
  leave_request_id: number;
  action: string;
  actor_id: number | null;
  actor_type: string | null;
  previous_status: string | null;
  new_status: string | null;
  details: string | null;
  metadata: Record<string, unknown> | null;
  created_at: string;
}

// Dashboard Types
export interface DashboardStats {
  total_pending: number;
  high_risk_flagged: number;
  team_coverage: number;
  pending_change_percent: number;
}

export interface EmployeeDashboard {
  leave_balances: LeaveBalance[];
  recent_requests: LeaveRequest[];
  upcoming_holidays: Holiday[];
  ai_suggestion: string | null;
}

export interface HRDashboard {
  stats: DashboardStats;
  pending_requests: LeaveRequestWithEmployee[];
}

export interface AdminDashboard {
  total_employees: number;
  total_departments: number;
  total_requests_this_month: number;
  approval_rate: number;
  ai_accuracy: number;
  recent_audit_logs: AuditLog[];
}

// AI Config Types
export interface AIConfig {
  id: number;
  name: string;
  provider: string;
  model_name: string;
  temperature: number;
  min_confidence_to_approve: number;
  min_confidence_to_auto_reject: number;
  timeout_ms: number;
  fallback_mode: string;
  is_active: boolean;
  created_at: string;
}

// Auth Types
export interface LoginRequest {
  email: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

// Department Types
export interface Department {
  id: number;
  name: string;
  code: string;
  description: string | null;
  created_at: string;
}
