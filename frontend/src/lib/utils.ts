import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { format, parseISO, formatDistanceToNow } from 'date-fns';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date, formatStr: string = 'MMM dd, yyyy') {
  const dateObj = typeof date === 'string' ? parseISO(date) : date;
  return format(dateObj, formatStr);
}

export function formatDateRange(startDate: string, endDate: string) {
  const start = parseISO(startDate);
  const end = parseISO(endDate);
  return `${format(start, 'MMM dd')} - ${format(end, 'MMM dd, yyyy')}`;
}

export function formatTimeAgo(date: string) {
  return formatDistanceToNow(parseISO(date), { addSuffix: true });
}

export function getStatusColor(status: string) {
  switch (status) {
    case 'APPROVED':
      return 'badge-success';
    case 'REJECTED':
      return 'badge-danger';
    case 'PENDING':
    case 'PENDING_REVIEW':
      return 'badge-warning';
    case 'CANCELLED':
      return 'bg-gray-100 text-gray-600';
    default:
      return 'badge-primary';
  }
}

export function getRiskColor(risk: string) {
  switch (risk) {
    case 'HIGH':
      return 'bg-red-100 text-red-700';
    case 'MEDIUM':
      return 'bg-yellow-100 text-yellow-700';
    case 'LOW':
      return 'bg-green-100 text-green-700';
    default:
      return 'bg-gray-100 text-gray-600';
  }
}

export function getLeaveTypeIcon(type: string) {
  switch (type) {
    case 'ANNUAL':
      return '🏖️';
    case 'SICK':
      return '🏥';
    case 'CASUAL':
      return '☕';
    case 'MATERNITY':
      return '👶';
    case 'PATERNITY':
      return '👨‍👧';
    case 'UNPAID':
      return '📋';
    default:
      return '📅';
  }
}

export function getLeaveTypeLabel(type: string) {
  switch (type) {
    case 'ANNUAL':
      return 'Annual Leave';
    case 'SICK':
      return 'Sick Leave';
    case 'CASUAL':
      return 'Casual Leave';
    case 'MATERNITY':
      return 'Maternity Leave';
    case 'PATERNITY':
      return 'Paternity Leave';
    case 'UNPAID':
      return 'Unpaid Leave';
    default:
      return type;
  }
}

export function getLeaveTypeColor(type: string) {
  switch (type) {
    case 'ANNUAL':
      return 'bg-blue-100 text-blue-700';
    case 'SICK':
      return 'bg-red-100 text-red-700';
    case 'CASUAL':
      return 'bg-amber-100 text-amber-700';
    case 'MATERNITY':
    case 'PATERNITY':
      return 'bg-purple-100 text-purple-700';
    case 'UNPAID':
      return 'bg-gray-100 text-gray-700';
    default:
      return 'bg-gray-100 text-gray-600';
  }
}

export function truncateText(text: string, maxLength: number) {
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength) + '...';
}

export function getInitials(firstName: string, lastName: string) {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase();
}
