import { cn } from '@/lib/utils';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'primary';
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({ children, variant = 'default', size = 'md', className }: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-700',
    success: 'bg-green-100 text-green-700',
    warning: 'bg-amber-100 text-amber-700',
    danger: 'bg-red-100 text-red-700',
    primary: 'bg-blue-100 text-blue-700',
  };
  
  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-xs',
  };
  
  return (
    <span
      className={cn(
        'inline-flex items-center font-medium rounded-full',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {children}
    </span>
  );
}

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className }: StatusBadgeProps) {
  const getVariant = () => {
    switch (status) {
      case 'APPROVED':
        return 'success';
      case 'REJECTED':
        return 'danger';
      case 'PENDING':
      case 'PENDING_REVIEW':
        return 'warning';
      default:
        return 'default';
    }
  };
  
  const getLabel = () => {
    switch (status) {
      case 'PENDING_REVIEW':
        return 'Pending Review';
      default:
        return status.charAt(0) + status.slice(1).toLowerCase();
    }
  };
  
  return (
    <Badge variant={getVariant()} className={className}>
      <span className="w-1.5 h-1.5 rounded-full bg-current mr-1.5" />
      {getLabel()}
    </Badge>
  );
}

interface RiskBadgeProps {
  risk: string;
  score?: number;
  className?: string;
}

export function RiskBadge({ risk, score, className }: RiskBadgeProps) {
  const getVariant = () => {
    switch (risk) {
      case 'HIGH':
        return 'danger';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
        return 'success';
      default:
        return 'default';
    }
  };
  
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <Badge variant={getVariant()}>
        {risk} RISK
      </Badge>
      {score !== undefined && (
        <span className="text-sm font-semibold text-gray-700">{score}%</span>
      )}
    </div>
  );
}
