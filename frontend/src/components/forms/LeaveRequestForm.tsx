import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { motion } from 'framer-motion';
import { Calendar, FileText, AlertCircle } from 'lucide-react';
import toast from 'react-hot-toast';
import { leaveApi } from '@/services/api';
import { Button, Select } from '@/components/ui';

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
  
  const days = calculateDays();
  
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
            {...register('start_date')}
            min={new Date().toISOString().split('T')[0]}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          {errors.start_date && (
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
            {...register('end_date')}
            min={startDate || new Date().toISOString().split('T')[0]}
            className="w-full px-4 py-2.5 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
          {errors.end_date && (
            <p className="mt-1 text-sm text-red-600">{errors.end_date.message}</p>
          )}
        </div>
      </motion.div>
      
      {days > 0 && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="bg-primary-50 rounded-lg p-4 flex items-center gap-3"
        >
          <div className="w-12 h-12 bg-primary-100 rounded-lg flex items-center justify-center">
            <span className="text-xl font-bold text-primary-600">{days}</span>
          </div>
          <div>
            <p className="font-medium text-primary-900">
              {days} Business {days === 1 ? 'Day' : 'Days'}
            </p>
            <p className="text-sm text-primary-600">
              (excluding weekends and holidays)
            </p>
          </div>
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
