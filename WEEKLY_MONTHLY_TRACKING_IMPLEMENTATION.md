# Weekly and Monthly Leave Tracking Implementation

## Overview
Implemented calendar-based weekly and monthly leave tracking to complement the existing 30-day and 90-day rolling window tracking. This allows HR to set limits like "maximum 2 leave requests per week" or "maximum 5 requests per calendar month" to prevent leave abuse.

## What Was Implemented

### 1. Database Model Updates (`backend/app/models/models.py`)
Added 4 new columns to the `LeavePolicy` model:
- `max_leaves_per_week` (default: 2) - Maximum leave requests allowed per calendar week
- `max_leaves_per_month` (default: 5) - Maximum leave requests allowed per calendar month
- `max_days_per_week` (default: 3) - Maximum leave days allowed per calendar week
- `max_days_per_month` (default: 7) - Maximum leave days allowed per calendar month

### 2. Statistics Computation (`backend/app/services/leave_utils.py`)
Updated `compute_leave_stats()` function to calculate:
- `leaves_this_week` - Count of leave requests submitted this calendar week (Monday-Sunday)
- `leaves_this_month` - Count of leave requests submitted this calendar month
- `days_this_week` - Total leave days requested this week
- `days_this_month` - Total leave days requested this month

**Week Calculation**: Uses Monday as week start (ISO calendar standard)
**Month Calculation**: Uses calendar month (1st to last day)

### 3. Rule Violations (`backend/app/services/leave_utils.py`)
Updated `check_rule_violations()` function to enforce:
- Check #7: Weekly leave request limit
- Check #8: Weekly leave days limit
- Check #9: Monthly leave request limit
- Check #10: Monthly leave days limit

### 4. Database Migration (`backend/migrations/add_weekly_monthly_limits.py`)
Created migration script with:
- `upgrade()` - Adds 4 new columns to leave_policy table
- `downgrade()` - Removes columns if needed
- Idempotent checks (won't fail if columns already exist)

### 5. API Schemas (`backend/app/schemas/schemas.py`)
Updated Pydantic schemas:
- `LeavePolicyBase` - Added 4 fields with default values
- `LeavePolicyUpdate` - Added 4 optional fields
- `LeavePolicyResponse` - Inherits from Base, automatically includes new fields

## How to Apply Changes

### Step 1: Run Database Migration
```bash
cd backend
python migrations/add_weekly_monthly_limits.py
```

Expected output:
```
Running upgrade...
✓ Added max_leaves_per_week column to leave_policy table
✓ Added max_leaves_per_month column to leave_policy table
✓ Added max_days_per_week column to leave_policy table
✓ Added max_days_per_month column to leave_policy table

✓ Migration completed successfully!
```

### Step 2: Restart Backend Server
```bash
# Stop current server (Ctrl+C)
# Start server
uvicorn app.main:app --reload
```

### Step 3: Verify in Database (Optional)
```sql
DESCRIBE leave_policy;
-- Should show the 4 new columns

SELECT id, name, max_leaves_per_week, max_leaves_per_month, 
       max_days_per_week, max_days_per_month 
FROM leave_policy;
-- Should show default values (2, 5, 3, 7)
```

## How It Works

### Example Scenario 1: Too Many Requests This Week
- Policy: `max_leaves_per_week = 2`
- Employee already submitted 2 leave requests this week (Monday-Sunday)
- Employee tries to submit 3rd request **this week**
- **Result**: Violation - "Maximum leave requests per week (2) already reached"

### Example Scenario 2: Too Many Days This Month
- Policy: `max_days_per_month = 7`
- Employee already took 5 days leave this month
- Employee requests 3 more days **this month**
- **Result**: Violation - "Exceeds maximum leave days per month (7)"

### Calendar Boundaries
- **Week**: Monday 00:00:00 to Sunday 23:59:59 (ISO 8601)
- **Month**: 1st day 00:00:00 to last day 23:59:59

### Tracking Logic
Counts are based on `leave.created_at` (when request was submitted), not `start_date` (when leave begins). This prevents employees from submitting multiple future leaves in a short time.

## Comparison with Existing Tracking

| Feature | Existing (Rolling Windows) | New (Calendar-Based) |
|---------|---------------------------|----------------------|
| **30-day unplanned** | Last 30 days from today | ❌ |
| **90-day total** | Last 90 days from today | ❌ |
| **Weekly limits** | ❌ | This calendar week (Mon-Sun) |
| **Monthly limits** | ❌ | This calendar month |
| **Reset timing** | Rolling, never resets | Resets Monday/1st of month |

Both systems work together to provide comprehensive leave abuse detection.

## Configuration via Admin UI

After migration, HR admins can configure these limits in the Policy Settings page:
1. Navigate to Admin Dashboard > Policy Settings
2. Update fields:
   - Max Leave Requests per Week
   - Max Leave Requests per Month
   - Max Leave Days per Week
   - Max Leave Days per Month
3. Save changes

**Note**: Frontend UI may need updates to expose these fields. Currently, API supports them but UI form may not display them yet.

## Rollback Instructions

If you need to revert changes:
```bash
cd backend
python migrations/add_weekly_monthly_limits.py downgrade
```

This will remove the 4 columns from the database.

## Testing Recommendations

1. **Test weekly limit**:
   - Submit 2 leave requests today
   - Try submitting 3rd request same week
   - Expected: Violation message

2. **Test monthly limit**:
   - Submit 5 leave requests this month
   - Try submitting 6th request same month
   - Expected: Violation message

3. **Test week boundary**:
   - Submit 2 requests on Sunday
   - On Monday (new week), should be able to submit again

4. **Test month boundary**:
   - Submit 5 requests on Jan 31
   - On Feb 1 (new month), should be able to submit again

## Files Modified

1. `/backend/app/models/models.py` - Lines 101-114
2. `/backend/app/services/leave_utils.py` - Lines 138-194, 253-280
3. `/backend/app/schemas/schemas.py` - Lines 298-322, 329-349
4. `/backend/migrations/add_weekly_monthly_limits.py` - New file

## Next Steps

1. ✅ Run migration script
2. ⏳ Update admin frontend to expose new fields
3. ⏳ Add tooltips explaining week/month calculation
4. ⏳ Update employee dashboard to show weekly/monthly usage stats
5. ⏳ Add to AI Analytics Dashboard if needed
