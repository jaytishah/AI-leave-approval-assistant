import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import {
  ChevronLeft,
  ChevronRight,
  Calendar as CalendarIcon,
  Users,
  Briefcase,
} from 'lucide-react';
import { adminApi } from '@/services/api';
import { Card, Badge } from '@/components/ui';

interface CalendarEvent {
  id: number;
  title: string;
  date: string;
  type: 'leave' | 'holiday' | 'team';
  employee_name?: string;
  leave_type?: string;
}

interface CompanyPolicy {
  id: number;
  weekly_off_type: string;
  description: string;
  effective_from: string | null;
  updated_at: string | null;
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

const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

export default function CalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [policy, setPolicy] = useState<CompanyPolicy | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedDate, setSelectedDate] = useState<Date | null>(null);
  
  useEffect(() => {
    fetchPolicy();
    fetchEvents();
  }, [currentDate]);
  
  const fetchPolicy = async () => {
    try {
      const response = await adminApi.getCompanyPolicy();
      setPolicy(response);
    } catch (error) {
      console.error('Failed to fetch policy:', error);
      // Default to SAT_SUN if fetch fails
      setPolicy({
        id: 1,
        weekly_off_type: 'SAT_SUN',
        description: 'Saturday and Sunday weekly off',
        effective_from: null,
        updated_at: null,
      });
    }
  };
  
  const fetchEvents = async () => {
    try {
      // Fetch leaves and holidays for the current month
      const response = await adminApi.getCalendarEvents(
        currentDate.getFullYear(),
        currentDate.getMonth() + 1
      );
      setEvents(response.data);
    } catch (error) {
      console.error('Failed to fetch events:', error);
      // Use empty events if fetch fails
      setEvents([]);
    } finally {
      setIsLoading(false);
    }
  };
  
  const isWeekend = (day: number): boolean => {
    if (!policy) return false;
    
    const date = new Date(currentDate.getFullYear(), currentDate.getMonth(), day);
    const dayOfWeek = date.getDay(); // 0 = Sunday, 6 = Saturday
    
    switch (policy.weekly_off_type) {
      case 'SUNDAY':
        return dayOfWeek === 0; // Only Sunday
        
      case 'SAT_SUN':
        return dayOfWeek === 0 || dayOfWeek === 6; // Saturday and Sunday
        
      case 'ALT_SAT':
        // All Sundays + 2nd and 4th Saturday
        if (dayOfWeek === 0) return true; // Sunday
        if (dayOfWeek === 6) {
          // Check if it's 2nd or 4th Saturday
          const weekNumber = Math.ceil(day / 7);
          return weekNumber === 2 || weekNumber === 4;
        }
        return false;
        
      default:
        return false;
    }
  };
  
  const getWeekendLabel = (): string => {
    if (!policy) return 'Weekend';
    
    switch (policy.weekly_off_type) {
      case 'SUNDAY':
        return 'Sunday (Weekend)';
      case 'SAT_SUN':
        return 'Sat + Sun (Weekend)';
      case 'ALT_SAT':
        return 'Alt Sat + Sun (Weekend)';
      default:
        return 'Weekend';
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
  
  const getEventsForDate = (day: number) => {
    const dateStr = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    return events.filter((event) => event.date === dateStr);
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
  
  const selectedDateEvents = selectedDate
    ? getEventsForDate(selectedDate.getDate())
    : [];
  
  const getEventColor = (type: string) => {
    const colors: Record<string, string> = {
      leave: 'bg-blue-500',
      holiday: 'bg-red-500',
      team: 'bg-green-500',
    };
    return colors[type] || 'bg-gray-500';
  };
  
  const getEventIcon = (type: string) => {
    switch (type) {
      case 'leave':
        return Briefcase;
      case 'holiday':
        return CalendarIcon;
      case 'team':
        return Users;
      default:
        return CalendarIcon;
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
          <h1 className="text-2xl font-bold text-gray-900">Leave Calendar</h1>
          <p className="text-gray-600 mt-1">View leaves and holidays at a glance</p>
        </div>
        <button
          onClick={goToToday}
          className="px-4 py-2 text-sm font-medium text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
        >
          Today
        </button>
      </motion.div>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Calendar */}
        <motion.div variants={itemVariants} className="lg:col-span-2">
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
                  const dayEvents = getEventsForDate(day);
                  const isWeekendDay = isWeekend(day);
                  
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
                        isWeekendDay
                          ? 'bg-gray-200 border border-gray-300'
                          : isToday(day)
                          ? 'bg-primary-50 border-2 border-primary-500'
                          : isSelected(day)
                          ? 'bg-gray-100'
                          : 'hover:bg-gray-50'
                      }`}
                    >
                      <div className="flex flex-col h-full">
                        <span
                          className={`text-sm font-medium ${
                            isWeekendDay
                              ? 'text-gray-500'
                              : isToday(day)
                              ? 'text-primary-600'
                              : 'text-gray-900'
                          }`}
                        >
                          {day}
                        </span>
                        <div className="flex-1 overflow-hidden space-y-0.5 mt-1">
                          {dayEvents.slice(0, 2).map((event) => (
                            <div
                              key={event.id}
                              className={`text-xs px-1 py-0.5 rounded text-white truncate ${getEventColor(
                                event.type
                              )}`}
                            >
                              {event.title}
                            </div>
                          ))}
                          {dayEvents.length > 2 && (
                            <div className="text-xs text-gray-500 px-1">
                              +{dayEvents.length - 2} more
                            </div>
                          )}
                        </div>
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>
          </Card>
        </motion.div>
        
        {/* Events Sidebar */}
        <motion.div variants={itemVariants} className="space-y-6">
          {/* Selected Date Events */}
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
                selectedDateEvents.length > 0 ? (
                  <div className="space-y-3">
                    {selectedDateEvents.map((event) => {
                      const Icon = getEventIcon(event.type);
                      return (
                        <div
                          key={event.id}
                          className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg"
                        >
                          <div
                            className={`w-8 h-8 rounded-lg flex items-center justify-center ${getEventColor(
                              event.type
                            )} bg-opacity-20`}
                          >
                            <Icon className={`w-4 h-4 ${getEventColor(event.type).replace('bg-', 'text-')}`} />
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-900">{event.title}</p>
                            {event.employee_name && (
                              <p className="text-sm text-gray-500">{event.employee_name}</p>
                            )}
                            {event.leave_type && (
                              <Badge variant="default" className="mt-1">
                                {event.leave_type}
                              </Badge>
                            )}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                ) : (
                  <p className="text-gray-500 text-sm">No events on this date</p>
                )
              ) : (
                <p className="text-gray-500 text-sm">Click on a date to see events</p>
              )}
            </div>
          </Card>
          
          {/* Legend */}
          <Card>
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Legend</h3>
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-blue-500"></div>
                  <span className="text-sm text-gray-600">Team Leave</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span className="text-sm text-gray-600">Public Holiday</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span className="text-sm text-gray-600">Team Event</span>
                </div>
                <div className="flex items-center gap-3">
                  <div className="w-4 h-4 rounded bg-gray-300 border border-gray-400"></div>
                  <span className="text-sm text-gray-600">{getWeekendLabel()}</span>
                </div>
              </div>
            </div>
          </Card>
          
          {/* Upcoming */}
          <Card>
            <div className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">Upcoming Events</h3>
              <div className="space-y-3">
                {events
                  .filter((e) => new Date(e.date) >= new Date())
                  .slice(0, 5)
                  .map((event) => (
                    <div key={event.id} className="flex items-center gap-3">
                      <div
                        className={`w-2 h-2 rounded-full ${getEventColor(event.type)}`}
                      ></div>
                      <div className="flex-1">
                        <p className="text-sm font-medium text-gray-900">{event.title}</p>
                        <p className="text-xs text-gray-500">
                          {new Date(event.date).toLocaleDateString('en-US', {
                            month: 'short',
                            day: 'numeric',
                          })}
                        </p>
                      </div>
                    </div>
                  ))}
              </div>
            </div>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  );
}
