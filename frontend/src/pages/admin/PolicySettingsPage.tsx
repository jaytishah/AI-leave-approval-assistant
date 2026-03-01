import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Settings, Calendar, Save, RefreshCw, Info } from 'lucide-react';
import toast from 'react-hot-toast';
import { adminApi } from '@/services/api';
import { Card, Button } from '@/components/ui';

interface CompanyPolicy {
  id: number;
  weekly_off_type: string;
  description: string;
  effective_from: string | null;
  updated_at: string | null;
}

const WEEKLY_OFF_OPTIONS = [
  {
    value: 'SUNDAY',
    label: 'Only Sunday Off',
    description: 'Employees have only Sunday as weekly off',
  },
  {
    value: 'SAT_SUN',
    label: 'Saturday + Sunday Off',
    description: 'Standard 5-day work week with both Saturday and Sunday off',
  },
  {
    value: 'ALT_SAT',
    label: 'Alternate Saturday Off',
    description: '2nd and 4th Saturday off (along with all Sundays)',
  },
];

export default function PolicySettingsPage() {
  const [policy, setPolicy] = useState<CompanyPolicy | null>(null);
  const [selectedOption, setSelectedOption] = useState<string>('SAT_SUN');
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchPolicy();
  }, []);

  const fetchPolicy = async () => {
    try {
      setLoading(true);
      const response = await adminApi.getCompanyPolicy();
      setPolicy(response);
      setSelectedOption(response.weekly_off_type);
    } catch (error: any) {
      console.error('Failed to fetch policy:', error);
      toast.error('Failed to load company policy');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      const selectedConfig = WEEKLY_OFF_OPTIONS.find(opt => opt.value === selectedOption);
      
      await adminApi.updateCompanyPolicy({
        weekly_off_type: selectedOption,
        description: selectedConfig?.description
      });
      
      toast.success('Company policy updated successfully! Calendars will reflect the new weekend settings.');
      await fetchPolicy();
    } catch (error: any) {
      console.error('Failed to update policy:', error);
      toast.error(error.response?.data?.detail || 'Failed to update policy');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mb-8"
      >
        <div className="flex items-center gap-3 mb-2">
          <Settings className="w-8 h-8 text-indigo-600" />
          <h1 className="text-3xl font-bold text-gray-900">Policy Settings</h1>
        </div>
        <p className="text-gray-600">
          Configure company-wide leave policies and working day calculations
        </p>
      </motion.div>

      {loading ? (
        <Card className="p-8 text-center">
          <RefreshCw className="w-8 h-8 text-indigo-600 animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading policy settings...</p>
        </Card>
      ) : (
        <>
          {/* Weekly Off Configuration */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="p-6 mb-6">
              <div className="flex items-center gap-3 mb-6">
                <Calendar className="w-6 h-6 text-indigo-600" />
                <h2 className="text-xl font-semibold text-gray-900">
                  Weekly Off Days Configuration
                </h2>
              </div>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <div className="flex items-start gap-3">
                  <Info className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                  <div className="text-sm text-blue-900">
                    <p className="font-medium mb-1">How Weekly Off Works:</p>
                    <p>
                      When employees apply for leave, the system will automatically
                      exclude configured weekly off days from the leave count. For
                      example, if an employee applies for leave from Friday to Monday
                      with "Saturday + Sunday Off" policy, only Friday and Monday will
                      be counted as 2 leave days.
                    </p>
                  </div>
                </div>
              </div>

              <div className="space-y-4">
                {WEEKLY_OFF_OPTIONS.map((option) => (
                  <label
                    key={option.value}
                    className={`
                      flex items-start p-4 border-2 rounded-lg cursor-pointer
                      transition-all duration-200 hover:border-indigo-300
                      ${
                        selectedOption === option.value
                          ? 'border-indigo-600 bg-indigo-50'
                          : 'border-gray-200 bg-white'
                      }
                    `}
                  >
                    <input
                      type="radio"
                      name="weekly_off"
                      value={option.value}
                      checked={selectedOption === option.value}
                      onChange={(e) => setSelectedOption(e.target.value)}
                      className="mt-1 w-4 h-4 text-indigo-600 focus:ring-indigo-500"
                    />
                    <div className="ml-3 flex-1">
                      <div className="flex items-center justify-between">
                        <h3 className="font-semibold text-gray-900">
                          {option.label}
                        </h3>
                        {selectedOption === option.value && (
                          <span className="px-2 py-1 text-xs font-medium text-indigo-700 bg-indigo-100 rounded-full">
                            Current
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 mt-1">
                        {option.description}
                      </p>
                    </div>
                  </label>
                ))}
              </div>

              <div className="mt-6 flex items-center justify-between pt-6 border-t">
                <div className="text-sm text-gray-600">
                  {policy?.updated_at && (
                    <p>
                      Last updated:{' '}
                      {new Date(policy.updated_at).toLocaleString('en-US', {
                        dateStyle: 'medium',
                        timeStyle: 'short',
                      })}
                    </p>
                  )}
                </div>
                <div className="flex gap-3">
                  <Button
                    variant="secondary"
                    onClick={fetchPolicy}
                    disabled={loading || saving}
                  >
                    <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
                    Refresh
                  </Button>
                  <Button
                    onClick={handleSave}
                    disabled={saving || selectedOption === policy?.weekly_off_type}
                  >
                    {saving ? (
                      <>
                        <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                        Saving...
                      </>
                    ) : (
                      <>
                        <Save className="w-4 h-4 mr-2" />
                        Save Changes
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Example Scenarios */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="p-6">
              <h3 className="font-semibold text-gray-900 mb-4">
                Example: How Leave Days Are Calculated
              </h3>
              
              <div className="space-y-4">
                <div className="bg-gray-50 rounded-lg p-4">
                  <p className="font-medium text-gray-900 mb-2">
                    Scenario: Leave from Friday to Monday
                  </p>
                  <ul className="space-y-2 text-sm text-gray-700">
                    <li>
                      <span className="font-medium">Only Sunday Off:</span>{' '}
                      Friday (1) + Saturday (1) + Monday (1) = <strong>3 leave days</strong>
                    </li>
                    <li>
                      <span className="font-medium">Saturday + Sunday Off:</span>{' '}
                      Friday (1) + Monday (1) = <strong>2 leave days</strong>
                    </li>
                    <li>
                      <span className="font-medium">Alternate Saturday Off:</span>{' '}
                      Depends on which Saturday. If 2nd/4th Saturday, then <strong>2 days</strong>, otherwise <strong>3 days</strong>
                    </li>
                  </ul>
                </div>
              </div>
            </Card>
          </motion.div>
        </>
      )}
    </div>
  );
}
