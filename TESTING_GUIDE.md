# Quick Testing Guide - Company Policy Settings

## 🎯 Quick Start Testing

### Prerequisites
✅ Backend running on port 8000
✅ Frontend running on port 5173
✅ Database migration completed
✅ Admin user credentials available

---

## 🧪 Test Scenarios

### Scenario 1: Configure Company Policy (Admin)

**Steps:**
1. Open browser: `http://localhost:5173`
2. Login as Admin user
3. Navigate to `/admin/policy-settings`
4. You should see 3 radio button options:
   - Only Sunday
   - Saturday & Sunday (default selected)
   - Alternate Saturday (2nd & 4th Saturday)
5. Select a different option
6. Click "Save Policy"
7. Wait for success toast notification
8. Verify the description updates

**Expected Result:**
- ✅ Policy saves successfully
- ✅ Toast notification appears
- ✅ Description shows correct information
- ✅ Last updated timestamp changes

---

### Scenario 2: Test Working Days Calculation

**Test Case A: 5-Day Work Week (Sat+Sun off)**

**Steps:**
1. Ensure policy is set to "Saturday & Sunday"
2. Go to Dashboard (any user)
3. Click "Request Leave"
4. Select dates:
   - Start: Monday (any Monday)
   - End: Friday (same week)
5. Observe the working days display

**Expected Result:**
- Total Days: 5
- Working Days: 5
- Weekends: 0
- Holidays: 0 (if no holidays)

---

**Test Case B: Include Weekend**

**Steps:**
1. Policy: "Saturday & Sunday"
2. Select dates:
   - Start: Friday
   - End: Monday (next week)
5. Observe the display

**Expected Result:**
- Total Days: 4
- Working Days: 2 (Friday + Monday)
- Weekends: 2 (Saturday + Sunday)
- Holidays: 0

---

**Test Case C: Only Sunday Off**

**Steps:**
1. Admin: Change policy to "Only Sunday"
2. Employee: Request leave
3. Select dates:
   - Start: Friday
   - End: Monday
4. Observe

**Expected Result:**
- Total Days: 4
- Working Days: 3 (Friday + Saturday + Monday)
- Weekends: 1 (only Sunday)
- Holidays: 0

---

**Test Case D: Alternate Saturday**

**Steps:**
1. Admin: Change policy to "Alternate Saturday"
2. Employee: Request leave
3. Select a date range that includes:
   - A 2nd Saturday (should be off)
   - A 1st/3rd Saturday (should be working)
4. Example: Jan 6-13, 2024
   - Jan 6 (Sat) = 1st Saturday = WORKING
   - Jan 7 (Sun) = OFF
   - Jan 13 (Sat) = 2nd Saturday = OFF
   - Jan 14 (Sun) = OFF

**Expected Result:**
- Correctly excludes 2nd & 4th Saturdays
- Includes 1st, 3rd, 5th Saturdays as working days
- All Sundays excluded

---

### Scenario 3: Cross-Month Calculation

**Steps:**
1. Policy: "Saturday & Sunday"
2. Select dates:
   - Start: Jan 29, 2024 (Monday)
   - End: Feb 2, 2024 (Friday)
3. Observe

**Expected Result:**
- Should correctly count working days across month boundary
- Total Days: 5
- Working Days: 5
- Weekends: 0

---

### Scenario 4: With Holidays

**Prerequisite:** Add a holiday in the date range

**Steps:**
1. Admin: Go to holidays section
2. Add a holiday on a working day (e.g., Jan 15, 2024 - Monday)
3. Employee: Request leave from Jan 15-19, 2024
4. Observe

**Expected Result:**
- Total Days: 5
- Working Days: 4
- Weekends: 0
- Holidays: 1

---

## 🔍 API Testing (Optional)

### Test GET /admin/policy
```bash
curl -X GET http://localhost:8000/admin/policy \
  -H "Authorization: Bearer YOUR_TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "weekly_off_type": "SAT_SUN",
  "description": "Saturday and Sunday weekly off",
  "effective_from": "2024-01-01",
  "created_at": "2024-12-...",
  "updated_at": "2024-12-..."
}
```

---

### Test PUT /admin/policy
```bash
curl -X PUT http://localhost:8000/admin/policy \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "weekly_off_type": "ALT_SAT",
    "description": "Alternate Saturday and Sunday off"
  }'
```

**Expected Response:**
```json
{
  "message": "Company policy updated successfully",
  "policy": { ... }
}
```

---

### Test POST /admin/calculate-working-days
```bash
curl -X POST http://localhost:8000/admin/calculate-working-days \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-01",
    "end_date": "2024-01-10"
  }'
```

**Expected Response:**
```json
{
  "total_days": 7,
  "breakdown": {
    "total_calendar_days": 10,
    "working_days": 7,
    "weekends": 3,
    "holidays": 0
  }
}
```

---

## ✅ Validation Checklist

### Policy Settings Page
- [ ] Page loads without errors
- [ ] Current policy is pre-selected
- [ ] Radio buttons are clickable
- [ ] Description updates when selection changes
- [ ] Examples section shows correct information
- [ ] Save button works and shows loading state
- [ ] Success toast appears after save
- [ ] Refresh button works
- [ ] Last updated timestamp is correct
- [ ] Page is admin-only (non-admin cannot access)

### Leave Request Form
- [ ] Form loads correctly
- [ ] Date pickers work
- [ ] Working days calculate automatically when dates selected
- [ ] Loading indicator shows during calculation
- [ ] Breakdown displays correctly (4 metrics in grid)
- [ ] Numbers update when dates change
- [ ] Works with all 3 policy types
- [ ] Handles invalid date ranges gracefully
- [ ] Medical certificate upload still works (for sick leave)

### Backend
- [ ] Migration ran successfully
- [ ] company_policy table exists in database
- [ ] Default policy record is inserted
- [ ] GET /admin/policy returns correct data
- [ ] PUT /admin/policy updates database
- [ ] POST /admin/calculate-working-days returns correct calculations
- [ ] Leave creation uses new working days calculation
- [ ] No server errors in backend logs

### Frontend
- [ ] No console errors in browser
- [ ] No TypeScript compilation errors
- [ ] Routing works (/admin/policy-settings)
- [ ] API calls succeed (check Network tab)
- [ ] Toast notifications appear
- [ ] Animations are smooth
- [ ] Responsive design works on mobile

---

## 🐛 Common Issues & Solutions

### Issue: Policy Settings page not accessible
**Solution:** Make sure you're logged in as ADMIN role

### Issue: Working days not calculating
**Solution:** 
1. Check browser console for errors
2. Check Network tab - is API call being made?
3. Verify backend is running on port 8000
4. Check backend logs for errors

### Issue: "API key limit over" error
**Solution:** API key is working now. If issue persists, check backend logs.

### Issue: Policy not saving
**Solution:**
1. Check if user has ADMIN role
2. Check backend database connection
3. Verify company_policy table exists
4. Check backend logs for SQL errors

### Issue: Dates showing 0 working days
**Solution:**
1. Ensure end date is after start date
2. Check if all days in range are weekends/holidays
3. Verify policy is correctly saved in database

---

## 📊 Database Verification

### Check Current Policy
```sql
SELECT * FROM company_policy ORDER BY id DESC LIMIT 1;
```

### Update Policy Manually (if needed)
```sql
UPDATE company_policy 
SET weekly_off_type = 'SAT_SUN',
    description = 'Saturday and Sunday weekly off'
WHERE id = 1;
```

### View All Policies
```sql
SELECT 
    id,
    weekly_off_type,
    description,
    effective_from,
    DATE_FORMAT(created_at, '%Y-%m-%d %H:%i') as created,
    DATE_FORMAT(updated_at, '%Y-%m-%d %H:%i') as updated
FROM company_policy;
```

---

## 🎯 Success Criteria

✅ Admin can change policy from UI
✅ Policy changes are saved to database
✅ Working days calculation reflects current policy
✅ Breakdown shows correct numbers
✅ All 3 policy types work correctly
✅ Edge cases handled (cross-month, cross-year)
✅ UI is responsive and smooth
✅ No errors in console or backend logs

---

## 📝 Test Results Template

```
Date: ___________
Tester: ___________

Scenario 1 (Configure Policy): ☐ Pass ☐ Fail
Scenario 2A (5-day week): ☐ Pass ☐ Fail
Scenario 2B (Include weekend): ☐ Pass ☐ Fail
Scenario 2C (Only Sunday): ☐ Pass ☐ Fail
Scenario 2D (Alternate Saturday): ☐ Pass ☐ Fail
Scenario 3 (Cross-month): ☐ Pass ☐ Fail
Scenario 4 (With holidays): ☐ Pass ☐ Fail

Additional Comments:
_________________________________________
_________________________________________
```

---

**Ready to test!** 🚀

Start with Scenario 1 to configure the policy, then test different date ranges in Scenario 2.
