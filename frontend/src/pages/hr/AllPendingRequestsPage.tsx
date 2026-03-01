import { useEffect, useState } from 'react';
import { adminApi } from '@/services/api';
import { Card } from '@/components/ui';
import { LeaveRequestWithEmployee } from '@/types';

export default function AllPendingRequestsPage() {
  const [requests, setRequests] = useState<LeaveRequestWithEmployee[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    adminApi.getPendingRequests().then(res => {
      setRequests(res.data || []);
      setIsLoading(false);
    });
  }, []);

  return (
    <div className="max-w-4xl mx-auto py-8">
      <h2 className="text-2xl font-bold mb-6">All Pending Leave Requests</h2>
      {isLoading ? (
        <p>Loading...</p>
      ) : requests.length === 0 ? (
        <p className="text-gray-500">No pending requests found.</p>
      ) : (
        <div className="space-y-4">
          {requests.map((req) => (
            <Card key={req.id} className="p-4">
              <div className="flex items-center gap-4">
                <div className="font-medium text-lg">{req.employee_name}</div>
                <div className="text-sm text-gray-500">{req.employee_department || 'N/A'}</div>
                <div className="ml-auto text-xs text-gray-400">{req.leave_type}</div>
              </div>
              <div className="mt-2 text-sm">
                <span>Duration: {req.start_date} - {req.end_date}</span>
                <span className="ml-4">AI Assessment: {req.risk_level} ({req.ai_validity_score ?? 0}%)</span>
              </div>
              <div className="mt-2">
                <button className="text-blue-600 hover:underline">Review</button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
