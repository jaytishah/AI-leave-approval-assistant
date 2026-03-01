# Leave Policy Optimization Report

## 🔍 ANALYSIS: Hardcoded vs AI Prompt Redundancy

### ✅ **ALREADY HARDCODED IN BUSINESS LOGIC** (Redundant in AI Prompt)

#### 1. **Numeric Leave Limits**
- **Hardcoded in:** Database/LeaveBalance table
- **Location:** `check_rule_violations()` in leave_utils.py line 205
- **Logic:** Balance checking: `balance_remaining < requested_days`
- **Can Remove:** Exact numbers (15 casual, 10 sick, 30 carryforward)

#### 2. **Medical Certificate Requirement**
- **Hardcoded in:** `check_rule_violations()` line 244-247
- **Code:**
  ```python
  if leave_request.leave_type == LeaveType.SICK and requested_days > 2:
      if not leave_request.medical_certificate_url:
          violations.append("Medical certificate is mandatory...")
  ```
- **Can Remove:** "Medical certificate MANDATORY if > 2 consecutive days"

#### 3. **Advance Notice Rules**
- **Hardcoded in:** `check_rule_violations()` line 250-256
- **Code:**
  ```python
  if days_before_start_casual < 1 and not is_emergency:
      violations.append("Casual Leave requires at least 1 working day advance notice")
  ```
- **Can Remove:** Specific advance notice requirements

#### 4. **Date Validation**
- **Hardcoded in:** `leave_processing.py` line 56
- **Code:** `if leave_req.start_date > leave_req.end_date: REJECT`
- **Can Remove:** Date range validation logic

#### 5. **Blackout Periods**
- **Hardcoded in:** `check_rule_violations()` line 217-219
- **Can Remove:** Blackout period logic (not in current prompt anyway)

#### 6. **Consecutive Leave Limits**
- **Hardcoded in:** `check_rule_violations()` line 229-231
- **Can Remove:** Not in current prompt

#### 7. **Weekend/Holiday Calculation**
- **Hardcoded in:** `calculate_working_days()` in leave_utils.py
- **Can Remove:** Calendar year rules, holiday logic

#### 8. **Balance Exhaustion → LWP**
- **Hardcoded in:** Balance checking logic
- **Can Remove:** LWP rules (automatically enforced)

#### 9. **Leave Categories (CASUAL, SICK, LWP)**
- **Hardcoded in:** Database enum LeaveType
- **Can Remove:** Detailed carryforward/encashment rules

---

### 🎯 **AI'S ACTUAL JOB** (Must Keep in Prompt)

1. **Reason-to-LeaveType Matching**
   - Is "vacation" appropriate for SICK leave? → NO
   - Is "fever" appropriate for SICK leave? → YES
   
2. **Reason Quality Assessment**
   - Is the reason clear and specific?
   - Is language professional?
   - Is there enough detail?

3. **Security Detection**
   - Prompt injection attempts
   - Manipulation patterns
   - Gibberish/random text

4. **Reasonability Judgment**
   - Is 5 days reasonable for "headache"? → Questionable
   - Is 3 days reasonable for "fever"? → YES

5. **Ambiguity Handling**
   - When to route to MANUAL_REVIEW
   - When something is vague but not clearly invalid

---

## 🚀 **OPTIMIZED POLICY** (Token Reduction: ~50%)

### What to KEEP:
- Leave type validation matrix (vacation vs medical reasons)
- Evaluation guidelines (approve/reject/review criteria)
- Security rules (prompt injection detection)
- Duration reasonability examples
- Output format requirements

### What to REMOVE:
- Specific numeric limits (15 days, 10 days, 2 days threshold)
- Detailed advance notice rules
- Carryforward/encashment details
- Calendar year information
- Balance checking logic
- LWP detailed rules
- General policy rules (system requirements)

### Estimated Token Savings:
- **Current:** ~1,800 tokens
- **Optimized:** ~900 tokens
- **Reduction:** 50% (900 tokens saved)

---

## ⚙️ **RECOMMENDED IMPLEMENTATION**

Create a **focused AI prompt** that only contains:
1. Core responsibility: "Match reason to leave type + assess quality"
2. Leave type validation matrix (CASUAL vs SICK appropriate reasons)
3. Security patterns to detect
4. When to recommend MANUAL_REVIEW
5. JSON output format

Remove all enforcement details that code already handles.
