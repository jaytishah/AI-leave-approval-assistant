from datetime import datetime, timedelta
from typing import List, Optional
from app.models import LeaveRequest, LeavePolicy
import json


def days_between(date1: datetime, date2: datetime) -> int:
    """Calculate days between two dates"""
    return (date2 - date1).days


def business_days_between(start_date: datetime, end_date: datetime, holidays: List[str] = None) -> float:
    """Calculate business days between two dates excluding weekends and holidays"""
    if holidays is None:
        holidays = []
    
    holiday_dates = set()
    for h in holidays:
        try:
            if isinstance(h, str):
                holiday_dates.add(datetime.strptime(h, "%Y-%m-%d").date())
            elif isinstance(h, datetime):
                holiday_dates.add(h.date())
        except:
            pass
    
    business_days = 0
    current_date = start_date.date() if isinstance(start_date, datetime) else start_date
    end = end_date.date() if isinstance(end_date, datetime) else end_date
    
    while current_date <= end:
        # Skip weekends (5 = Saturday, 6 = Sunday)
        if current_date.weekday() < 5 and current_date not in holiday_dates:
            business_days += 1
        current_date += timedelta(days=1)
    
    return business_days


def is_in_blackout_period(start_date: datetime, end_date: datetime, blackout_periods: List[dict]) -> bool:
    """Check if leave dates fall within any blackout period"""
    if not blackout_periods:
        return False
    
    for period in blackout_periods:
        try:
            blackout_start = datetime.strptime(period.get("start_date", ""), "%Y-%m-%d")
            blackout_end = datetime.strptime(period.get("end_date", ""), "%Y-%m-%d")
            
            # Check if there's any overlap
            if start_date <= blackout_end and end_date >= blackout_start:
                return True
        except:
            continue
    
    return False


def count_leaves_in_period(leave_history: List[LeaveRequest], days: int, leave_type: str = None) -> int:
    """Count leaves in the specified period"""
    cutoff_date = datetime.now() - timedelta(days=days)
    count = 0
    
    for leave in leave_history:
        if leave.created_at >= cutoff_date:
            if leave_type is None or leave.leave_type.value == leave_type:
                count += 1
    
    return count


def count_leaves_on_weekday(leave_history: List[LeaveRequest], days: int, weekday: str) -> int:
    """Count leaves that start on a specific weekday"""
    weekday_map = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5, "SUN": 6}
    target_weekday = weekday_map.get(weekday.upper(), 0)
    
    cutoff_date = datetime.now() - timedelta(days=days)
    count = 0
    
    for leave in leave_history:
        if leave.created_at >= cutoff_date:
            if leave.start_date.weekday() == target_weekday:
                count += 1
    
    return count


def max_consecutive_leave_days(leave_history: List[LeaveRequest]) -> int:
    """Calculate maximum consecutive leave days"""
    if not leave_history:
        return 0
    
    # Sort by start date
    sorted_leaves = sorted(leave_history, key=lambda x: x.start_date)
    
    max_streak = 0
    current_streak = 0
    last_end_date = None
    
    for leave in sorted_leaves:
        if leave.status.value not in ["APPROVED", "PENDING", "PENDING_REVIEW"]:
            continue
            
        if last_end_date is None:
            current_streak = int(leave.total_days)
        elif (leave.start_date.date() - last_end_date.date()).days <= 1:
            # Consecutive or overlapping
            current_streak += int(leave.total_days)
        else:
            current_streak = int(leave.total_days)
        
        max_streak = max(max_streak, current_streak)
        last_end_date = leave.end_date
    
    return max_streak


def calculate_pattern_score(monday_count: int, friday_count: int) -> float:
    """Calculate pattern score for Monday/Friday leaves"""
    total = monday_count + friday_count
    if total == 0:
        return 0.0
    
    # Higher score indicates suspicious pattern
    # Normalize to 0-1 range
    max_expected = 10  # Expected max for 90 days
    score = min(total / max_expected, 1.0)
    
    # Add weight if there's a significant imbalance
    if total > 3:
        imbalance = abs(monday_count - friday_count) / total
        score = score * (1 + imbalance * 0.5)
    
    return min(score, 1.0)


def compute_leave_stats(leave_history: List[LeaveRequest], policy: LeavePolicy) -> dict:
    """Compute comprehensive leave statistics"""
    stats = {
        "unplanned_leaves_last_30_days": 0,
        "total_leaves_last_90_days": 0,
        "consecutive_leave_streak_days": 0,
        "monday_leaves_last_90_days": 0,
        "friday_leaves_last_90_days": 0,
        "monday_friday_pattern_score": 0.0,
        "risk_level": "LOW"
    }
    
    if not leave_history:
        return stats
    
    # Count unplanned leaves in last 30 days (assuming SICK and leaves < 1 day notice are unplanned)
    cutoff_30 = datetime.now() - timedelta(days=30)
    cutoff_90 = datetime.now() - timedelta(days=90)
    
    for leave in leave_history:
        if leave.status.value in ["APPROVED", "PENDING", "PENDING_REVIEW"]:
            # 90-day stats
            if leave.created_at >= cutoff_90:
                stats["total_leaves_last_90_days"] += 1
                
                if leave.start_date.weekday() == 0:  # Monday
                    stats["monday_leaves_last_90_days"] += 1
                elif leave.start_date.weekday() == 4:  # Friday
                    stats["friday_leaves_last_90_days"] += 1
            
            # 30-day stats - unplanned check
            if leave.created_at >= cutoff_30:
                days_notice = (leave.start_date - leave.created_at).days
                if days_notice < 1 or leave.leave_type.value == "SICK":
                    stats["unplanned_leaves_last_30_days"] += 1
    
    # Calculate consecutive streak
    stats["consecutive_leave_streak_days"] = max_consecutive_leave_days(leave_history)
    
    # Calculate pattern score
    stats["monday_friday_pattern_score"] = calculate_pattern_score(
        stats["monday_leaves_last_90_days"],
        stats["friday_leaves_last_90_days"]
    )
    
    # Determine risk level
    if stats["unplanned_leaves_last_30_days"] >= policy.max_unplanned_leaves_30_days:
        stats["risk_level"] = "HIGH"
    elif stats["total_leaves_last_90_days"] >= policy.max_leaves_90_days:
        stats["risk_level"] = "MEDIUM"
    elif stats["monday_friday_pattern_score"] >= policy.max_pattern_score:
        stats["risk_level"] = "MEDIUM"
    
    return stats


def check_rule_violations(
    leave_request: LeaveRequest,
    policy: LeavePolicy,
    balance_remaining: float,
    requested_days: float,
    stats: dict
) -> List[str]:
    """Check for policy rule violations"""
    violations = []
    
    # 1. Leave balance check
    if balance_remaining < requested_days and not policy.allow_negative_balance:
        violations.append("Insufficient leave balance")
    
    # 2. Notice period for long leaves
    days_before_start = (leave_request.start_date - datetime.now()).days
    if requested_days >= policy.long_leave_threshold_days:
        if days_before_start < policy.min_advance_days_for_long_leave:
            violations.append(f"Long leave requires {policy.min_advance_days_for_long_leave} days advance notice")
    
    # 3. Blackout period check
    if is_in_blackout_period(leave_request.start_date, leave_request.end_date, policy.blackout_periods or []):
        violations.append("Leave requested in blackout period")
    
    # 4. Too many unplanned leaves
    if stats.get("unplanned_leaves_last_30_days", 0) >= policy.max_unplanned_leaves_30_days:
        violations.append("Too many unplanned leaves in last 30 days")
    
    # 5. Monday/Friday pattern
    if stats.get("monday_friday_pattern_score", 0) >= policy.max_pattern_score:
        violations.append("Suspicious Monday/Friday leave pattern detected")
    
    # 6. Consecutive leave limit
    current_streak = stats.get("consecutive_leave_streak_days", 0)
    if current_streak + requested_days > policy.max_consecutive_leave_days:
        violations.append(f"Exceeds maximum consecutive leave days ({policy.max_consecutive_leave_days})")
    
    # 7. Reason mandatory check
    if policy.reason_mandatory and not leave_request.reason_text:
        violations.append("Leave reason is required")
    
    # 8. Date validation
    if leave_request.start_date > leave_request.end_date:
        violations.append("Invalid date range: start date after end date")
    
    return violations


def is_blocking_violation(violations: List[str], policy: LeavePolicy) -> bool:
    """Determine if violations should block the request"""
    blocking_keywords = [
        "Insufficient leave balance",
        "Invalid date range",
        "blackout period",
        "Leave reason is required"
    ]
    
    for violation in violations:
        for keyword in blocking_keywords:
            if keyword.lower() in violation.lower():
                return True
    
    return False


def build_explanation(violations: List[str], ai_score: float = None, ai_flags: List[str] = None) -> str:
    """Build explanation string from violations and AI results"""
    parts = []
    
    if violations:
        parts.append("Rule violations: " + "; ".join(violations))
    else:
        parts.append("Rules check: PASSED")
    
    if ai_score is not None:
        parts.append(f"AI validity score: {ai_score}")
    
    if ai_flags:
        parts.append(f"AI flags: {', '.join(ai_flags)}")
    
    return " | ".join(parts)


def compute_priority(stats: dict, requested_days: float) -> str:
    """Compute priority for manual review queue"""
    risk_level = stats.get("risk_level", "LOW")
    
    if risk_level == "HIGH" or requested_days >= 10:
        return "HIGH"
    elif risk_level == "MEDIUM" or requested_days >= 5:
        return "MEDIUM"
    else:
        return "NORMAL"


def generate_request_number() -> str:
    """Generate unique leave request number"""
    import random
    import string
    timestamp = datetime.now().strftime("%Y%m%d")
    random_suffix = ''.join(random.choices(string.digits, k=4))
    return f"LR-{timestamp}-{random_suffix}"
