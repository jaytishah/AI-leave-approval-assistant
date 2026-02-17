import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Calendar, FileText, AlertCircle, XCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { leaveApi, adminApi } from '@/services/api';
import { Button, Select } from '@/components/ui';

interface CompanyPolicy {
  weekly_off_type: string;
  description: string;
}

interface Holiday {
  id: number;
  name: string;
  date: string;
  is_active: boolean;
}

const leaveRequestSchema = z.object({
  leave_type: z.string().min(1, 'Please select a leave type'),
  start_date: z.string().min(1, 'Start date is required'),
  end_date: z.string().min(1, 'End date is required'),
  reason_text: z.string().optional(),
  medical_certificate: z.any().optional(),
}).refine((data) => {
  if (data.start_date && data.end_date) {
    return new Date(data.start_date) <= new Date(data.end_date);
  }
  return true;
}, {
  message: 'End date must be after start date',
  path: ['end_date'],
}).refine((data) => {
  // Medical certificate is mandatory for sick leave > 2 days (as per company policy)
  if (data.leave_type === 'SICK' && data.start_date && data.end_date) {
    const start = new Date(data.start_date);
    const end = new Date(data.end_date);
    const days = Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;
    if (days > 2 && !data.medical_certificate) {
      return false;
    }
  }
  return true;
}, {
  message: 'Medical certificate is mandatory for sick leave exceeding 2 consecutive days',
  path: ['medical_certificate'],
});

type LeaveRequestFormData = z.infer<typeof leaveRequestSchema>;

interface LeaveRequestFormProps {
  onSuccess: () => void;
  onCancel: () => void;
}

export function LeaveRequestForm({ onSuccess, onCancel }: LeaveRequestFormProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [medicalCertificate, setMedicalCertificate] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string>('');
  const [workingDaysData, setWorkingDaysData] = useState<{
    total_days: number;
    breakdown: {
      total_calendar_days: number;
      working_days: number;
      weekends: number;
      holidays: number;
    };
  } | null>(null);
  const [loadingDays, setLoadingDays] = useState(false);
  const [companyPolicy, setCompanyPolicy] = useState<CompanyPolicy | null>(null);
  const [holidays, setHolidays] = useState<Holiday[]>([]);
  const [startDateError, setStartDateError] = useState<string>('');
  const [endDateError, setEndDateError] = useState<string>('');
  
  const {
    register,
    handleSubmit,
    watch,
    setValue,
    formState: { errors },
  } = useForm<LeaveRequestFormData>({
    resolver: zodResolver(leaveRequestSchema),
    defaultValues: {
      leave_type: '',
      start_date: '',
      end_date: '',
      reason_text: '',
    },
  });
  
  const startDate = watch('start_date');
  const endDate = watch('end_date');
  const leaveType = watch('leave_type');
  
  // Fetch company policy and holidays on mount
  useEffect(() => {
    const fetchPolicyAndHolidays = async () => {
      try {
        const [policyResponse, holidaysResponse] = await Promise.all([
          adminApi.getCompanyPolicy(),
          adminApi.getHolidays()
        ]);
        setCompanyPolicy(policyResponse);
        setHolidays(holidaysResponse.filter((h: Holiday) => h.is_active));
      } catch (error) {
        console.error('Failed to fetch policy and holidays:', error);
        // Default to SAT_SUN if fetch fails
        setCompanyPolicy({ weekly_off_type: 'SAT_SUN', description: 'Default: Saturday and Sunday off' });
        setHolidays([]);
      }
    };
    
    fetchPolicyAndHolidays();
  }, []);
  
  // Check if a date is a non-working day (weekend or holiday)
  const isNonWorkingDay = (dateString: string): { isNonWorking: boolean; reason: string } => {
    if (!companyPolicy) return { isNonWorking: false, reason: '' };
    
    const date = new Date(dateString);
    const dayOfWeek = date.getDay(); // 0 = Sunday, 6 = Saturday
    
    // Check if it's a holiday
    const dateOnlyString = dateString.split('T')[0];
    const isHoliday = holidays.some(h => {
      const holidayDate = h.date.split('T')[0];
      return holidayDate === dateOnlyString;
    });
    
    if (isHoliday) {
      const holiday = holidays.find(h => h.date.split('T')[0] === dateOnlyString);
      return { isNonWorking: true, reason: `Holiday: ${holiday?.name}` };
    }
    
    // Check weekend based on policy
    const policy = companyPolicy.weekly_off_type;
    
    if (policy === 'SUNDAY') {
      if (dayOfWeek === 0) {
        return { isNonWorking: true, reason: 'Sunday (Weekly off)' };
      }
    } else if (policy === 'SAT_SUN') {
      if (dayOfWeek === 0 || dayOfWeek === 6) {
        return { isNonWorking: true, reason: dayOfWeek === 0 ? 'Sunday (Weekly off)' : 'Saturday (Weekly off)' };
      }
    } else if (policy === 'ALT_SAT') {
      // 2nd and 4th Saturday + all Sundays
      if (dayOfWeek === 0) {
        return { isNonWorking: true, reason: 'Sunday (Weekly off)' };
      }
      if (dayOfWeek === 6) {
        // Calculate which Saturday of the month
        const dateNum = date.getDate();
        const weekNumber = Math.ceil(dateNum / 7);
        if (weekNumber === 2 || weekNumber === 4) {
          return { isNonWorking: true, reason: `${weekNumber === 2 ? '2nd' : '4th'} Saturday (Weekly off)` };
        }
      }
    }
    
    return { isNonWorking: false, reason: '' };
  };
  
  // Validate date selection
  const validateDateSelection = (dateString: string, fieldName: 'start' | 'end') => {
    if (!dateString) {
      if (fieldName === 'start') setStartDateError('');
      else setEndDateError('');
      return true;
    }
    
    const check = isNonWorkingDay(dateString);
    if (check.isNonWorking) {
      const errorMsg = `Cannot select ${check.reason}. Please choose a working day.`;
      if (fieldName === 'start') {
        setStartDateError(errorMsg);
      } else {
        setEndDateError(errorMsg);
      }
      return false;
    }
    
    if (fieldName === 'start') setStartDateError('');
    else setEndDateError('');
    return true;
  };
  
  // Handle date changes with validation
  const handleStartDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setValue('start_date', value);
    validateDateSelection(value, 'start');
  };
  
  const handleEndDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setValue('end_date', value);
    validateDateSelection(value, 'end');
  };
  
  // Fetch working days when dates change
  useEffect(() => {
    const fetchWorkingDays = async () => {
      if (!startDate || !endDate) {
        setWorkingDaysData(null);
        return;
      }
      
      const start = new Date(startDate);
      const end = new Date(endDate);
      if (start > end) {
        setWorkingDaysData(null);
        return;
      }
      
      setLoadingDays(true);
      try {
        const response = await adminApi.calculateWorkingDays({
          start_date: startDate,
          end_date: endDate,
        });
        setWorkingDaysData(response);
      } catch (error) {
        console.error('Failed to calculate working days:', error);
        // Fallback to simple calculation if API fails
        setWorkingDaysData(null);
      } finally {
        setLoadingDays(false);
      }
    };
    
    fetchWorkingDays();
  }, [startDate, endDate]);
  
  const calculateDays = () => {
    if (!startDate || !endDate) return 0;
    const start = new Date(startDate);
    const end = new Date(endDate);
    if (start > end) return 0;
    
    let count = 0;
    const current = new Date(start);
    while (current <= end) {
      const day = current.getDay();
      if (day !== 0 && day !== 6) count++;
      current.setDate(current.getDate() + 1);
    }
    return count;
  };
  
  const days = workingDaysData?.total_days || calculateDays();
  
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    setFileError('');
    
    if (!file) {
      setMedicalCertificate(null);
      setValue('medical_certificate', undefined);
      return;
    }
    
    // Validate file size (5MB max)
    const maxSize = 5 * 1024 * 1024; // 5MB in bytes
    if (file.size > maxSize) {
      setFileError('File size must not exceed 5MB');
      e.target.value = '';
      return;
    }
    
    // Validate file type (only PDF, JPG, PNG)
    const allowedTypes = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg'];
    if (!allowedTypes.includes(file.type)) {
      setFileError('Only PDF, JPG, and PNG files are allowed');
      e.target.value = '';
      return;
    }
    
    setMedicalCertificate(file);
    setValue('medical_certificate', file);
  };
  
  const onSubmit = async (data: LeaveRequestFormData) => {
    // Final validation before submission
    const startCheck = isNonWorkingDay(data.start_date);
    const endCheck = isNonWorkingDay(data.end_date);
    
    if (startCheck.isNonWorking) {
      toast.error(`Start date is invalid: ${startCheck.reason}`);
      setStartDateError(`Cannot select ${startCheck.reason}`);
      return;
    }
    
    if (endCheck.isNonWorking) {
      toast.error(`End date is invalid: ${endCheck.reason}`);
      setEndDateError(`Cannot select ${endCheck.reason}`);
      return;
    }
    
    setIsLoading(true);
    try {
      let medicalCertData = {};
      
      // Handle medical certificate for sick leave
      if (data.leave_type === 'SICK' && medicalCertificate) {
        // Convert file to base64 for storage
        const reader = new FileReader();
        const base64Promise = new Promise<string>((resolve, reject) => {
          reader.onload = () => resolve(reader.result as string);
          reader.onerror = reject;
          reader.readAsDataURL(medicalCertificate);
        });
        
        const base64Data = await base64Promise;
        medicalCertData = {
          medical_certificate_url: base64Data,
          medical_certificate_filename: medicalCertificate.name,
          medical_certificate_size: medicalCertificate.size,
        };
      }
      
      await leaveApi.createLeaveRequest({
        leave_type: data.leave_type,
        start_date: new Date(data.start_date).toISOString(),
        end_date: new Date(data.end_date).toISOString(),
        reason_text: data.reason_text,
        ...medicalCertData,
      });
      toast.success('Leave request submitted successfully!');
      onSuccess();
    } catch (error: unknown) {
      const err = error as { response?: { data?: { detail?: string } } };
      toast.error(err.response?.data?.detail || 'Failed to submit leave request');
    } finally {
      setIsLoading(false);
    }
  };
  
  const leaveTypeOptions = [
    { value: '', label: 'Select leave type' },
    { value: 'ANNUAL', label: '🏖️ Annual Leave' },
    { value: 'SICK', label: '🏥 Sick Leave' },
    { value: 'CASUAL', label: '☕ Casual Leave' },
    { value: 'UNPAID', label: '📋 Unpaid Leave' },
  ];
  
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <Select
          label="Leave Type"
          options={leaveTypeOptions}
          error={errors.leave_type?.message}
          {...register('leave_type')}
        />
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.1 }}
        className="grid grid-cols-2 gap-4"
      >
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            <Calendar className="w-4 h-4 inline mr-1" />
            Start Date
          </label>
          <input
            type="date"
            value={startDate}
            onChange={handleStartDateChange}
            min={new Date().toISOString().split('T')[0]}
            className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              startDateError ? 'border-red-500 bg-red-50' : 'border-gray-200'
            }`}
          />
          {startDateError && (
            <p className="mt-1.5 text-sm text-red-600 flex items-center gap-1">
              <XCircle className="w-4 h-4" />
              {startDateError}
            </p>
          )}
          {errors.start_date && !startDateError && (
            <p className="mt-1 text-sm text-red-600">{errors.start_date.message}</p>
          )}
        </div>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            <Calendar className="w-4 h-4 inline mr-1" />
            End Date
          </label>
          <input
            type="date"
            value={endDate}
            onChange={handleEndDateChange}
            min={startDate || new Date().toISOString().split('T')[0]}
            className={`w-full px-4 py-2.5 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
              endDateError ? 'border-red-500 bg-red-50' : 'border-gray-200'
            }`}
          />
          {endDateError && (
            <p className="mt-1.5 text-sm text-red-600 flex items-center gap-1">
              <XCircle className="w-4 h-4" />
              {endDateError}
            </p>
          )}
          {errors.end_date && !endDateError && (
            <p className="mt-1 text-sm text-red-600">{errors.end_date.message}</p>
          )}
        </div>
      </motion.div>
      
      {/* Company Policy Info */}
      {companyPolicy && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15 }}
          className="bg-blue-50 rounded-lg p-3 flex items-start gap-2"
        >
          <AlertCircle className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="text-xs text-blue-800">
            <p className="font-medium mb-0.5">Company Policy:</p>
            <p>{companyPolicy.description}</p>
            <p className="mt-1 text-blue-600">
              {companyPolicy.weekly_off_type === 'SUNDAY' && '• Sundays are weekly offs (6-day work week)'}
              {companyPolicy.weekly_off_type === 'SAT_SUN' && '• Saturdays and Sundays are weekly offs (5-day work week)'}
              {companyPolicy.weekly_off_type === 'ALT_SAT' && '• 2nd & 4th Saturdays + all Sundays are weekly offs'}
            </p>
            <p className="mt-0.5 text-blue-600">• Holidays cannot be selected for leave requests</p>
          </div>
        </motion.div>
      )}
      
      {days > 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-primary-50 rounded-lg p-4"
        >
          <div className="flex items-center gap-3 mb-3">
            <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
              <span className="text-xl font-bold text-primary-600">{days}</span>
            </div>
            <div>
              <p className="font-medium text-primary-900">
                {days} Working {days === 1 ? 'Day' : 'Days'}
              </p>
              <p className="text-sm text-primary-600">
                {loadingDays ? 'Calculating...' : '(based on company policy)'}
              </p>
            </div>
          </div>
          
          {workingDaysData?.breakdown && (
            <div className="grid grid-cols-4 gap-2 pt-3 border-t border-primary-100">
              <div className="text-center">
                <p className="text-xs text-primary-600">Total Days</p>
                <p className="text-sm font-semibold text-primary-900">
                  {workingDaysData.breakdown.total_calendar_days}
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-primary-600">Working</p>
                <p className="text-sm font-semibold text-green-600">
                  {workingDaysData.breakdown.working_days}
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-primary-600">Weekends</p>
                <p className="text-sm font-semibold text-orange-600">
                  {workingDaysData.breakdown.weekends}
                </p>
              </div>
              <div className="text-center">
                <p className="text-xs text-primary-600">Holidays</p>
                <p className="text-sm font-semibold text-red-600">
                  {workingDaysData.breakdown.holidays}
                </p>
              </div>
            </div>
          )}
        </motion.div>
      )}
      
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.2 }}
      >
        <label className="block text-sm font-medium text-gray-700 mb-1.5">
          <FileText className="w-4 h-4 inline mr-1" />
          Reason (Optional)
        </label>
        <textarea
          {...register('reason_text')}
          rows={3}
          placeholder="Provide details about your leave request..."
          className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
        />
      </motion.div>
      
      {/* Medical Certificate Upload for Sick Leave */}
      {leaveType === 'SICK' && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.25 }}
          className="space-y-2"
        >
          <label className="block text-sm font-medium text-gray-700 mb-1.5">
            🏥 Medical Certificate {days > 2 && <span className="text-red-500">*</span>}
            {days <= 2 && <span className="text-gray-500 text-xs ml-1">(Optional)</span>}
          </label>
          <div className="relative">
            <input
              type="file"
              accept=".pdf,.jpg,.jpeg,.png"
              onChange={handleFileChange}
              className="w-full px-4 py-2.5 border-2 border-dashed border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-primary-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100 cursor-pointer"
            />
          </div>
          {medicalCertificate && (
            <div className="flex items-center gap-2 text-sm text-green-600 bg-green-50 px-3 py-2 rounded-lg">
              <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
              </svg>
              <span>{medicalCertificate.name} ({(medicalCertificate.size / 1024).toFixed(2)} KB)</span>
            </div>
          )}
          {fileError && (
            <p className="text-sm text-red-600 flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              {fileError}
            </p>
          )}
          {errors.medical_certificate && (
            <p className="text-sm text-red-600 flex items-center gap-1">
              <AlertCircle className="w-4 h-4" />
              {errors.medical_certificate.message}
            </p>
          )}
          <p className="text-xs text-gray-500 flex items-center gap-1">
            <AlertCircle className="w-3 h-3" />
            {days > 2 
              ? 'Required for sick leave exceeding 2 days • PDF, JPG, PNG • Max 5MB'
              : 'Optional for sick leave up to 2 days • PDF, JPG, PNG • Max 5MB'
            }
          </p>
        </motion.div>
      )}
      
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="bg-amber-50 rounded-lg p-4 flex items-start gap-3"
      >
        <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
        <div className="text-sm text-amber-800">
          <p className="font-medium">Note:</p>
          <p>Your request will be automatically processed by our AI system and may require manager approval based on company policy.</p>
        </div>
      </motion.div>
      
      <div className="flex gap-3 pt-2">
        <Button type="button" variant="secondary" onClick={onCancel} className="flex-1">
          Cancel
        </Button>
        <Button type="submit" isLoading={isLoading} className="flex-1">
          Submit Request
        </Button>
      </div>
    </form>
  );
}
