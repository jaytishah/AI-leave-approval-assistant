import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
} from 'lucide-react';
import { leaveApi } from '@/services/api';
import { Card } from '@/components/ui';

interface ApprovedLeave {
  id: number;
  leave_type: string;
  start_date: string;
  end_date: string;
  total_days: number;
  reason_text?: string;
}

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

const LEAVE_TYPE_COLORS: Record<string, string> = {
  ANNUAL: 'bg-blue-500 text-white',
  SICK: 'bg-red-500 text-white',
  CASUAL: 'bg-amber-500 text-white',
};

export function EmployeeLeaveCalendar() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [approvedLeaves, setApprovedLeaves] = useState<ApprovedLeave[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  
  useEffect(() => {
    fetchApprovedLeaves();
  }, []);
  
  const fetchApprovedLeaves = async () => {
    try {
      const data = await leaveApi.getMyApprovedLeaves();
      setApprovedLeaves(data);
    } catch (error) {
      console.error('Failed to fetch approved leaves:', error);
    } finally {
      setIsLoading(false);
    }
  };
  
  const getDaysInMonth = (date: Date) => {
    const year = date.getFullYear();
    const month = date.getMonth();
    const firstDay = new Date(year, month, 1);
    const lastDay = new Date(year, month + 1, 0);
    const daysInMonth = lastDay.getDate();
    const startingDay = firstDay.getDay();
    
    return { daysInMonth, startingDay };
  };
  
  const { daysInMonth, startingDay } = getDaysInMonth(currentDate);
  
  const goToPrevMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() - 1, 1));
  };
  
  const goToNextMonth = () => {
    setCurrentDate(new Date(currentDate.getFullYear(), currentDate.getMonth() + 1, 1));
  };
  
  const goToToday = () => {
    setCurrentDate(new Date());
    setSelectedDate(new Date());
  };
  
  const getLeaveForDate = (day: number): ApprovedLeave | null => {
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const checkDate = new Date(dateStr);
    checkDate.setHours(0, 0, 0, 0);
    
    for (const leave of approvedLeaves) {
      const startDate = new Date(leave.start_date);
      const endDate = new Date(leave.end_date);
      startDate.setHours(0, 0, 0, 0);
      endDate.setHours(0, 0, 0, 0);
      
      if (checkDate >= startDate && checkDate <= endDate) {
        return leave;
      }
    }
    
    return null;
  };
  
  const isToday = (day: number) => {
    const today = new Date();
    return (
      day === today.getDate() &&
      currentDate.getMonth() === today.getMonth() &&
      currentDate.getFullYear() === today.getFullYear()
    );
  };
  
  const isSelected = (day: number) => {
    if (!selectedDate) return false;
    return (
      day === selectedDate.getDate() &&
      currentDate.getMonth() === selectedDate.getMonth() &&
      currentDate.getFullYear() === selectedDate.getFullYear()
    );
  };
  
  const selectedDateLeave = selectedDate ? getLeaveForDate(selectedDate.getDate()) : null;
  
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-primary-500"></div>
      </div>
    );
  }
  
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">My Leave Calendar</h2>
          <p className="text-gray-600 mt-1">View your approved leaves</p>
        </div>
        <button
          onClick={goToToday}
          className="px-4 py-2 text-sm font-medium text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
        >
          Today
        </button>
      </div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <div className="lg:col-span-2">
          <Card>
            <div className="p-6">
              {/* Month Navigation */}
              <div className="flex items-center justify-between mb-6">
                <button
                  onClick={goToPrevMonth}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <ChevronLeft className="w-5 h-5 text-gray-600" />
                </button>
                <h2 className="text-xl font-semibold text-gray-900">
                  {MONTHS[currentDate.getMonth()]} {currentDate.getFullYear()}
                </h2>
                <button
                  onClick={goToNextMonth}
                  className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
                >
                  <ChevronRight className="w-5 h-5 text-gray-600" />
                </button>
              </div>
              
              {/* Day Headers */}
              <div className="grid grid-cols-7 gap-1 mb-2">
                {DAYS.map((day) => (
                  <div
                    key={day}
                    className="text-center text-sm font-medium text-gray-500 py-2"
                  >
                    {day}
                  </div>
                ))}
              </div>
              
              {/* Calendar Grid */}
              <div className="grid grid-cols-7 gap-1">
                {/* Empty cells for days before the first day of month */}
                {Array.from({ length: startingDay }).map((_, index) => (
                  <div key={`empty-${index}`} className="h-24 p-1"></div>
                ))}
                
                {/* Days of the month */}
                {Array.from({ length: daysInMonth }).map((_, index) => {
                  const day = index + 1;
                  const leave = getLeaveForDate(day);
                  
                  return (
                    <motion.div
                      key={day}
                      whileHover={{ scale: 1.02 }}
                      onClick={() =>
                        setSelectedDate(
                          new Date(currentDate.getFullYear(), currentDate.getMonth(), day)
                        )
                      }
                      className={`h-24 p-1 rounded-lg cursor-pointer transition-colors ${
                        isToday(day)
                          ? 'bg-primary-50 border-2 border-primary-500'
                          : isSelected(day)
                          ? 'bg-gray-100'
                          : 'hover:bg-gray-50'
                      } ${leave ? 'border-2 border-' + (leave.leave_type === 'ANNUAL' ? 'blue-300' : leave.leave_type === 'SICK' ? 'red-300' : 'amber-300') : ''}`}
                    >
                      <div className="flex flex-col h-full">
                        <span
                          className={`text-sm font-medium ${
                            isToday(day) ? 'text-primary-600' : 'text-gray-900'
                          }`}
                        >
                          {day}
                        </span>
                        {leave && (
                          <div className={`text-xs px-1 py-0.5 rounded mt-1 ${LEAVE_TYPE_COLORS[leave.leave_type] || 'bg-gray-500 text-white'}`}>
                            {leave.leave_type}
                          </div>
                        )}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </Card>
        </div>
        
        {/* Leave Details Sidebar */}
        <div className="space-y-6">
          {/* Selected Date Details */}
          <Card>
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                {selectedDate
                  ? selectedDate.toLocaleDateString('en-US', {
                      weekday: 'long',
                      month: 'long',
                      day: 'numeric',
                    })
                  : 'Select a date'}
              </h3>
              
              {selectedDate ? (
                selectedDateLeave ? (
                  <div className="space-y-3">
                    <div className="p-3 bg-gray-50 rounded-lg">
                      <div className={`inline-flex items-center px-2 py-1 rounded text-sm font-medium mb-2 ${LEAVE_TYPE_COLORS[selectedDateLeave.leave_type] || 'bg-gray-500 text-white'}`}>
                        {selectedDateLeave.leave_type} Leave
                      </div>
                      <p className="text-sm text-gray-600 mt-2">
                        <strong>Duration:</strong> {new Date(selectedDateLeave.start_date).toLocaleDateString()} - {new Date(selectedDateLeave.end_date).toLocaleDateString()}
                      </p>
                      <p className="text-sm text-gray-600 mt-1">
                        <strong>Days:</strong> {selectedDateLeave.total_days} working day{selectedDateLeave.total_days !== 1 ? 's' : ''}
                      </p>
                      {selectedDateLeave.reason_text && (
                        <p className="text-sm text-gray-600 mt-1">
                          <strong>Reason:</strong> {selectedDateLeave.reason_text}
                        </p>
                      )}
                      <div className="mt-2 inline-flex items-center px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                        ✓ Approved
                      </div>
                    </div>
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No leave on this date</p>
                )
              ) : (
                <p className="text-gray-500 text-sm">Click on a date to see details</p>
              )}
            </div>
          </Card>
          
          {/* Legend */}
          <Card>
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Legend</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-8 h-6 rounded bg-blue-500"></div>
                  <span className="text-sm text-gray-600">Annual Leave</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-6 rounded bg-red-500"></div>
                  <span className="text-sm text-gray-600">Sick Leave</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-8 h-6 rounded bg-amber-500"></div>
                  <span className="text-sm text-gray-600">Casual Leave</span>
                </div>
              </div>
            </div>
          </Card>
          
          {/* Leave Summary */}
          <Card>
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Leave Summary</h3>
              <div className="space-y-2">
                <p className="text-sm text-gray-600">
                  <strong>Total Approved Leaves:</strong> {approvedLeaves.length}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Total Days:</strong> {approvedLeaves.reduce((sum, leave) => sum + leave.total_days, 0)}
                </p>
              </div>
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
