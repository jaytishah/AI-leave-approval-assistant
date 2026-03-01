from fastapi import APIRouter, Depends, HTTPException, status, Query, File, UploadFile, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import List, Optional
from datetime import datetime, timedelta
import uuid
import os

from app.core import get_db
from app.models import (
    LeaveRequest, LeaveStatus, LeaveType, LeaveBalance,
    LeaveAuditLog, User, LeavePolicy, RiskLevel, MedicalCertificate, AIUsageLog
)
from app.schemas import (
    LeaveRequestCreate, LeaveRequestResponse, LeaveRequestUpdate,
    LeaveRequestWithEmployee, LeaveRequestDetail, LeaveBalanceResponse,
    AuditLogResponse, LeaveRequestForHRReview, EmployeeLeaveBalance,
    EmployeeLeaveHistory, EmployeeLeaveStats
)
from app.api.auth import get_current_user, require_role
from app.models import UserRole
from app.services import process_leave_request, generate_request_number, business_days_between, calculate_working_days
from app.models import CompanyPolicy
from app.services.email_service import email_service
from app.services.certificate_validator import (
    save_medical_certificate_file, 
    perform_ocr,
    extract_structured_fields,
    calculate_confidence,
    validate_medical_certificate, 
    ValidationResult
)
from app.services.ai_service import get_ai_recommendation

router = APIRouter(prefix="/leaves", tags=["Leave Management"])


def check_leave_overlap(employee_id: int, start_date, end_date, db: Session, exclude_leave_id: int = None) -> dict:
    """
    Check if a leave request overlaps with existing approved leaves.
    Returns dict with 'has_overlap' (bool) and 'overlapping_leaves' (list).
    
    Handles:
    - Full overlap: New leave completely covers existing leave
    - Partial overlap: New leave partially overlaps existing leave
    - Single day inside multi-day: One day falls within existing leave
    - Multi-day overlapping single-day: New multi-day overlaps existing single-day
    """
    # Query all approved leaves for this employee
    query = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == employee_id,
        LeaveRequest.status == LeaveStatus.APPROVED
    )
    
    # Exclude current leave if updating
    if exclude_leave_id:
        query = query.filter(LeaveRequest.id != exclude_leave_id)
    
    approved_leaves = query.all()
    
    overlapping_leaves = []
    
    for leave in approved_leaves:
        # Check if there's any overlap between date ranges
        # Overlap exists if: start1 <= end2 AND end1 >= start2
        # Normalise DB datetimes to date so comparison always works
        leave_start = leave.start_date.date() if hasattr(leave.start_date, 'date') else leave.start_date
        leave_end = leave.end_date.date() if hasattr(leave.end_date, 'date') else leave.end_date
        if start_date <= leave_end and end_date >= leave_start:
            overlapping_leaves.append({
                "id": leave.id,
                "leave_type": leave.leave_type.value,
                "start_date": leave.start_date.strftime("%Y-%m-%d"),
                "end_date": leave.end_date.strftime("%Y-%m-%d"),
                "total_days": leave.total_days
            })
    
    return {
        "has_overlap": len(overlapping_leaves) > 0,
        "overlapping_leaves": overlapping_leaves
    }


@router.post("/", response_model=LeaveRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_leave_request(
    leave_type: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    reason_text: Optional[str] = Form(None),
    is_emergency: Optional[bool] = Form(False),
    medical_certificate: Optional[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new leave request with file upload support"""
    
    # Parse dates
    try:
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid date format"
        )
    
    # Validate leave type
    try:
        leave_type_enum = LeaveType(leave_type.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid leave type: {leave_type}"
        )
    
    # Sick leave validation: Can only be taken for today or previous days
    if leave_type_enum == LeaveType.SICK:
        today = datetime.now().date()
        leave_start_date = start_dt.date()
        if leave_start_date > today:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Sick leave can only be taken for today or previous days, not for future dates"
            )
    
    # Generate request number
    request_number = generate_request_number()
    
    # Check for overlapping approved leaves
    overlap_check = check_leave_overlap(
        employee_id=current_user.id,
        start_date=start_dt.date(),
        end_date=end_dt.date(),
        db=db
    )
    
    if overlap_check["has_overlap"]:
        overlapping = overlap_check["overlapping_leaves"][0]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Leave request overlaps with already approved {overlapping['leave_type']} leave from {overlapping['start_date']} to {overlapping['end_date']}"
        )
    
    # Get holidays from Holiday table (active holidays only)
    from app.models.models import Holiday
    holiday_records = db.query(Holiday).filter(
        Holiday.is_active == True
    ).all()
    holidays = [h.date.strftime("%Y-%m-%d") for h in holiday_records]
    
    # Get company policy for weekly off configuration
    company_policy = db.query(CompanyPolicy).order_by(CompanyPolicy.updated_at.desc()).first()
    weekly_off_type = company_policy.weekly_off_type.value if company_policy else "SAT_SUN"
    
    # Calculate total days using proper working days calculation
    total_days = calculate_working_days(
        start_dt.date(),
        end_dt.date(),
        weekly_off_type,
        holidays
    )
    
    # Medical certificate handling
    certificate_url = None
    certificate_filename = None
    certificate_size = None
    certificate_validation = None
    
    # Validate medical certificate for sick leave >= 2 working days
    if leave_type_enum == LeaveType.SICK and total_days >= 2:
        if not medical_certificate:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Medical certificate is mandatory for sick leave of {total_days} working days or more"
            )
        
        # Process medical certificate with Step 1 & 2
        if medical_certificate:
            # Read file contents
            contents = await medical_certificate.read()
            file_size = len(contents)
            
            # Check file size (5MB max)
            if file_size > 5 * 1024 * 1024:  # 5MB
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Medical certificate file size must not exceed 5MB"
                )
            
            # Validate file type
            allowed_types = ['application/pdf', 'image/jpeg', 'image/png', 'image/jpg']
            if medical_certificate.content_type not in allowed_types:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only PDF, JPG, and PNG files are allowed"
                )
            
            certificate_filename = medical_certificate.filename
            certificate_size = file_size
            
            # Store for later use after leave_request is created
            certificate_data = {
                "contents": contents,
                "filename": certificate_filename
            }
    
    # Create leave request
    leave_request = LeaveRequest(
        request_number=request_number,
        employee_id=current_user.id,
        leave_type=leave_type_enum,
        start_date=start_dt.date(),
        end_date=end_dt.date(),
        total_days=total_days,
        reason_text=reason_text,
        is_emergency=is_emergency,
        medical_certificate_url=certificate_url,
        medical_certificate_filename=certificate_filename,
        medical_certificate_size=certificate_size,
        medical_certificate_validation=certificate_validation,
        status=LeaveStatus.PENDING
    )
    
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    
    # ========================================================
    # STEP 1 & STEP 2: Process Medical Certificate
    # ========================================================
    if leave_type_enum == LeaveType.SICK and total_days >= 2 and 'certificate_data' in locals():
        try:
            # STEP 1: Save medical certificate file
            file_info = save_medical_certificate_file(
                file_content=certificate_data['contents'],
                filename=certificate_data['filename'],
                leave_id=leave_request.id
            )
            
            print(f"✓ Step 1 Complete: File saved to {file_info['file_path']}")
            
            # STEP 2: Extract text using EasyOCR
            ocr_result = perform_ocr(file_info['file_path'])
            
            if ocr_result['success']:
                print(f"✓ Step 2 Complete: OCR extracted {len(ocr_result['extracted_text'])} characters")
            else:
                print(f"⚠ Step 2: OCR extraction had issues: {ocr_result['error']}")
            
            # STEP 3: Extract structured fields from OCR text (ROBUST VERSION)
            structured_fields = {}
            if ocr_result['success'] and ocr_result.get('extracted_text'):
                structured_fields = extract_structured_fields(ocr_result['extracted_text'])
                
                # Count detected fields (using detection flags, not text extraction)
                detection_count = sum([
                    structured_fields.get('doctor_name_detected', False),
                    structured_fields.get('clinic_name_detected', False),
                    structured_fields.get('date_detected', False),
                    structured_fields.get('medical_keywords_detected', False),
                    structured_fields.get('signature_or_stamp_detected', False)
                ])
                print(f"✓ Step 3 Complete (ROBUST): {detection_count}/5 mandatory fields DETECTED")
                
                # Also count successfully extracted text (optional)
                extraction_count = sum([
                    bool(structured_fields.get('doctor_name_text')),
                    bool(structured_fields.get('clinic_name_text')),
                    bool(structured_fields.get('certificate_date')),
                    structured_fields.get('medical_keywords_detected', False),
                    structured_fields.get('signature_or_stamp_detected', False)
                ])
                print(f"  └─ Text extracted for {extraction_count}/5 fields")
            else:
                # No OCR text, use default None values
                structured_fields = {
                    'doctor_name_text': None,
                    'doctor_name_detected': False,
                    'clinic_name_text': None,
                    'clinic_name_detected': False,
                    'certificate_date': None,
                    'date_detected': False,
                    'medical_keywords_detected': False,
                    'signature_or_stamp_detected': False,
                    'rest_days': None,
                    'diagnosis': None,
                    'registration_number': None,
                    'contact_number': None
                }
            
            # STEP 4: Calculate confidence score (RULE-BASED ENGINE)
            confidence_result = calculate_confidence(structured_fields)
            print(f"✓ Step 4 Complete: Confidence Score = {confidence_result['confidence_score']}/100 ({confidence_result['confidence_level']})")
            print(f"  └─ Requires HR Review: {confidence_result['requires_hr_review']}")
            print(f"  └─ Scoring Breakdown: {confidence_result['scoring_breakdown']}")
            
            # STEP 5: Get AI Recommendation (GEMINI API - ADVISORY ONLY)
            ai_result = None
            ai_recommendation_value = None
            ai_reason_value = None
            
            try:
                # Calculate leave days from request
                leave_days = (leave_request.end_date - leave_request.start_date).days + 1
                
                # Call AI service (async)
                import asyncio
                ai_result = await get_ai_recommendation(
                    extracted_text=ocr_result.get('extracted_text', ''),
                    structured_fields=structured_fields,
                    confidence_score=confidence_result['confidence_score'],
                    confidence_level=confidence_result['confidence_level'],
                    leave_days_applied=leave_days
                )
                
                ai_recommendation_value = ai_result.get('ai_recommendation')
                ai_reason_value = ai_result.get('ai_reason')
                
                print(f"✓ Step 5 Complete: AI Recommendation = {ai_recommendation_value}")
                print(f"  └─ AI Reason: {ai_reason_value[:100]}..." if ai_reason_value and len(ai_reason_value) > 100 else f"  └─ AI Reason: {ai_reason_value}")
                if ai_result.get('error'):
                    print(f"  └─ AI Warning: {ai_result['error']}")
                
                # ── Analytics: log medical-cert token usage (isolated) ───────
                try:
                    if ai_result.get("_prompt_tokens") is not None:
                        from app.core import settings as _settings
                        usage_log = AIUsageLog(
                            employee_id=current_user.id,
                            leave_request_id=leave_request.id,
                            call_type="MEDICAL_CERT",
                            leave_type=leave_type_enum.value,
                            model_name=ai_result.get("_model_name", _settings.GEMINI_MODEL),
                            prompt_tokens=ai_result.get("_prompt_tokens", 0),
                            output_tokens=ai_result.get("_output_tokens", 0),
                            total_tokens=ai_result.get("_total_tokens", 0),
                            ai_recommended_action=ai_recommendation_value
                        )
                        db.add(usage_log)
                        db.commit()
                        print(f"[AI Analytics] Logged medical-cert usage: {ai_result.get('_total_tokens', 0)} tokens")
                except Exception as _log_err:
                    print(f"[AI Analytics] Medical-cert log failed (non-fatal): {_log_err}")
                # ────────────────────────────────────────────────────────────
                    
            except Exception as ai_error:
                print(f"⚠ Step 5: AI recommendation failed - {ai_error}")
                # Fallback to safe default
                ai_recommendation_value = "REVIEW"
                ai_reason_value = "AI service unavailable. Manual HR review required for medical certificate verification."
            
            # Save to medical_certificates table with extracted fields
            medical_cert = MedicalCertificate(
                leave_id=leave_request.id,
                file_path=file_info['file_path'],
                file_name=file_info['file_name'],
                file_size=file_info['file_size'],
                file_type=file_info['file_type'],
                extracted_text=ocr_result.get('extracted_text'),  # Raw OCR text - NEVER DELETE
                # Step 3: Structured fields (ROBUST VERSION with detection flags)
                doctor_name_text=structured_fields.get('doctor_name_text'),
                doctor_name_detected=structured_fields.get('doctor_name_detected', False),
                clinic_name_text=structured_fields.get('clinic_name_text'),
                clinic_name_detected=structured_fields.get('clinic_name_detected', False),
                certificate_date=structured_fields.get('certificate_date'),
                date_detected=structured_fields.get('date_detected', False),
                medical_keywords_detected=structured_fields.get('medical_keywords_detected', False),
                signature_or_stamp_detected=structured_fields.get('signature_or_stamp_detected', False),
                rest_days=structured_fields.get('rest_days'),
                diagnosis=structured_fields.get('diagnosis'),
                registration_number=structured_fields.get('registration_number'),
                contact_number=structured_fields.get('contact_number'),
                # Step 4: Confidence Engine results (RULE-BASED)
                confidence_score=confidence_result['confidence_score'],
                confidence_level=confidence_result['confidence_level'],
                requires_hr_review=confidence_result['requires_hr_review'],
                # Step 5: AI Recommendation Layer (GEMINI API - ADVISORY ONLY)
                ai_recommendation=ai_recommendation_value,
                ai_reason=ai_reason_value,
                # Step 6: HR Final Decision (NULL until HR acts)
                final_status=None,  # NULL until HR acts
                hr_reason=None
            )
            
            db.add(medical_cert)
            db.commit()
            db.refresh(medical_cert)
            
            print(f"✓ Medical certificate record created with ID: {medical_cert.id}")
            
            # Update leave request with certificate info (for backward compatibility)
            leave_request.medical_certificate_url = file_info['file_path']
            leave_request.medical_certificate_filename = file_info['file_name']
            leave_request.medical_certificate_size = file_info['file_size']
            leave_request.medical_certificate_validation = {
                "ocr_success": ocr_result['success'],
                "ocr_error": ocr_result.get('error'),
                "text_length": len(ocr_result.get('extracted_text', '')),
                "status": "PENDING_HR_REVIEW"
            }
            db.commit()
            db.refresh(leave_request)
            
        except Exception as e:
            print(f"✗ Error processing medical certificate: {e}")
            # Don't fail the entire request - flag for HR manual review
            leave_request.medical_certificate_validation = {
                "error": str(e),
                "status": "PROCESSING_FAILED_NEEDS_HR_REVIEW"
            }
            db.commit()
            db.refresh(leave_request)
    
    # Create audit log
    audit_log = LeaveAuditLog(
        leave_request_id=leave_request.id,
        action="Request Submitted",
        actor_id=current_user.id,
        actor_type="USER",
        new_status=LeaveStatus.PENDING.value,
        details=f"Leave request submitted for {total_days} working days"
    )
    db.add(audit_log)
    db.commit()
    
    # Process the leave request asynchronously
    try:
        await process_leave_request(db, leave_request.id)
        db.refresh(leave_request)
    except Exception as e:
        print(f"Error processing leave request: {e}")
    
    return LeaveRequestResponse.model_validate(leave_request)


@router.get("/", response_model=List[LeaveRequestResponse])
async def get_my_leave_requests(
    status: Optional[LeaveStatus] = None,
    leave_type: Optional[LeaveType] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's leave requests"""
    query = db.query(LeaveRequest).filter(LeaveRequest.employee_id == current_user.id)
    
    if status:
        query = query.filter(LeaveRequest.status == status)
    if leave_type:
        query = query.filter(LeaveRequest.leave_type == leave_type)
    
    leave_requests = query.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(limit).all()
    
    return [LeaveRequestResponse.model_validate(lr) for lr in leave_requests]


@router.get("/pending", response_model=List[LeaveRequestForHRReview])
async def get_pending_requests(
    risk_level: Optional[RiskLevel] = None,
    department_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all pending leave requests with complete employee data (HR/Admin only)"""
    query = db.query(LeaveRequest).filter(
        LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW])
    )
    
    if risk_level:
        query = query.filter(LeaveRequest.risk_level == risk_level)
    
    if department_id:
        query = query.join(User).filter(User.department_id == department_id)
    
    leave_requests = query.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(limit).all()
    
    current_year = datetime.now().year
    result = []
    
    for lr in leave_requests:
        employee = db.query(User).filter(User.id == lr.employee_id).first()
        if not employee:
            continue
        
        # Get employee's leave balances (all types)
        balances = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.year == current_year
        ).all()
        
        employee_balances = [
            EmployeeLeaveBalance(
                leave_type=b.leave_type.value,
                total_days=b.total_days,
                used_days=b.used_days,
                pending_days=b.pending_days,
                remaining_days=b.remaining_days
            ) for b in balances
        ]
        
        # Get employee's recent leave history (last 10 completed requests)
        history = db.query(LeaveRequest).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_([LeaveStatus.APPROVED, LeaveStatus.REJECTED])
        ).order_by(LeaveRequest.created_at.desc()).limit(10).all()
        
        employee_history = [
            EmployeeLeaveHistory(
                id=h.id,
                request_number=h.request_number,
                leave_type=h.leave_type.value,
                start_date=h.start_date,
                end_date=h.end_date,
                total_days=h.total_days,
                status=h.status.value,
                created_at=h.created_at
            ) for h in history
        ]
        
        # Calculate statistics
        # Total leaves this year
        total_this_year = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).scalar() or 0
        
        # Total days taken this year
        total_days_this_year = db.query(func.sum(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).scalar() or 0.0
        
        # Leaves in last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)
        leaves_30_days = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date >= thirty_days_ago
        ).scalar() or 0
        
        # Leaves in last 90 days
        ninety_days_ago = datetime.now() - timedelta(days=90)
        leaves_90_days = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date >= ninety_days_ago
        ).scalar() or 0
        
        # Most used leave type
        most_used = db.query(
            LeaveRequest.leave_type,
            func.count(LeaveRequest.id).label('count')
        ).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).group_by(LeaveRequest.leave_type).order_by(func.count(LeaveRequest.id).desc()).first()
        
        most_used_type = most_used[0].value if most_used else None
        
        # Average leave duration
        avg_duration = db.query(func.avg(LeaveRequest.total_days)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).scalar()
        
        # Pending requests count
        pending_count = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == employee.id,
            LeaveRequest.status.in_([LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW])
        ).scalar() or 0
        
        employee_stats = EmployeeLeaveStats(
            total_leaves_this_year=total_this_year,
            total_days_taken_this_year=float(total_days_this_year),
            leaves_last_30_days=leaves_30_days,
            leaves_last_90_days=leaves_90_days,
            most_used_leave_type=most_used_type,
            average_leave_duration=float(avg_duration) if avg_duration else None,
            pending_requests_count=pending_count
        )
        
        result.append(LeaveRequestForHRReview(
            **LeaveRequestResponse.model_validate(lr).model_dump(),
            employee_name=f"{employee.first_name} {employee.last_name}",
            employee_email=employee.email,
            employee_department=employee.department.name if employee.department else None,
            employee_avatar=employee.avatar_url,
            employee_leave_balances=employee_balances,
            employee_leave_history=employee_history,
            employee_leave_stats=employee_stats
        ))
    
    return result


@router.get("/all", response_model=List[LeaveRequestWithEmployee])
async def get_all_requests(
    status: Optional[LeaveStatus] = None,
    employee_id: Optional[int] = None,
    limit: int = Query(default=50, le=100),
    offset: int = 0,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get all leave requests (HR/Admin only)"""
    query = db.query(LeaveRequest)
    
    if status:
        query = query.filter(LeaveRequest.status == status)
    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    
    leave_requests = query.order_by(LeaveRequest.created_at.desc()).offset(offset).limit(limit).all()
    
    result = []
    for lr in leave_requests:
        employee = db.query(User).filter(User.id == lr.employee_id).first()
        result.append(LeaveRequestWithEmployee(
            **LeaveRequestResponse.model_validate(lr).model_dump(),
            employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
            employee_email=employee.email if employee else "",
            employee_department=employee.department.name if employee and employee.department else None,
            employee_avatar=employee.avatar_url if employee else None
        ))
    
    return result


@router.get("/balance/me", response_model=List[LeaveBalanceResponse])
async def get_my_leave_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's leave balance"""
    current_year = datetime.now().year
    
    balances = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == current_user.id,
        LeaveBalance.year == current_year
    ).all()
    
    return [LeaveBalanceResponse.model_validate(b) for b in balances]


@router.get("/approved/me", response_model=List[dict])
async def get_my_approved_leaves(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's approved leaves for calendar and date blocking"""
    approved_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.employee_id == current_user.id,
        LeaveRequest.status == LeaveStatus.APPROVED
    ).order_by(LeaveRequest.start_date).all()
    
    return [{
        "id": leave.id,
        "leave_type": leave.leave_type.value,
        "start_date": leave.start_date.strftime("%Y-%m-%d"),
        "end_date": leave.end_date.strftime("%Y-%m-%d"),
        "total_days": leave.total_days,
        "reason_text": leave.reason_text
    } for leave in approved_leaves]


@router.get("/{leave_id}", response_model=LeaveRequestDetail)
async def get_leave_request(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get leave request details with employee context"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE and leave_request.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this request")
    
    employee = db.query(User).filter(User.id == leave_request.employee_id).first()
    
    # Get balance info for this specific leave type
    current_year = datetime.now().year
    balance = db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == leave_request.employee_id,
        LeaveBalance.leave_type == leave_request.leave_type,
        LeaveBalance.year == current_year
    ).first()
    
    # Build historical pattern summary for HR
    historical_pattern = None
    if current_user.role in [UserRole.HR, UserRole.ADMIN]:
        # Get stats for pattern analysis
        total_leaves = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == leave_request.employee_id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            func.extract('year', LeaveRequest.start_date) == current_year
        ).scalar() or 0
        
        recent_leaves = db.query(func.count(LeaveRequest.id)).filter(
            LeaveRequest.employee_id == leave_request.employee_id,
            LeaveRequest.status == LeaveStatus.APPROVED,
            LeaveRequest.start_date >= datetime.now() - timedelta(days=60)
        ).scalar() or 0
        
        historical_pattern = f"{total_leaves} approved leaves this year, {recent_leaves} in last 60 days"
    
    # Fetch medical certificate data from medical_certificates table (Steps 3-5)
    if leave_request.leave_type == LeaveType.SICK and leave_request.medical_certificate_url:
        medical_cert = db.query(MedicalCertificate).filter(
            MedicalCertificate.leave_id == leave_request.id
        ).first()
        
        if medical_cert:
            # Populate medical_certificate_validation with comprehensive Step 3-5 data
            leave_request.medical_certificate_validation = {
                # Step 3: Structured Field Extraction
                "doctor_name_text": medical_cert.doctor_name_text,
                "clinic_name_text": medical_cert.clinic_name_text,
                "certificate_date": medical_cert.certificate_date,
                "rest_days": medical_cert.rest_days,
                "diagnosis": medical_cert.diagnosis,
                "registration_number": medical_cert.registration_number,
                "contact_number": medical_cert.contact_number,
                "extracted_text": medical_cert.extracted_text,
                # Step 4: Confidence Engine
                "confidence_score": medical_cert.confidence_score,
                "confidence_level": medical_cert.confidence_level,
                "requires_hr_review": medical_cert.requires_hr_review,
                # Step 5: AI Recommendation
                "ai_recommendation": medical_cert.ai_recommendation,
                "ai_reason": medical_cert.ai_reason
            }
    
    return LeaveRequestDetail(
        **LeaveRequestResponse.model_validate(leave_request).model_dump(),
        employee_name=f"{employee.first_name} {employee.last_name}" if employee else "Unknown",
        employee_email=employee.email if employee else "",
        employee_department=employee.department.name if employee and employee.department else None,
        employee_avatar=employee.avatar_url if employee else None,
        employee_total_balance=balance.total_days if balance else None,
        employee_used_ytd=balance.used_days if balance else None,
        team_coverage=None,
        team_context=None,
        historical_pattern=historical_pattern
    )


@router.put("/{leave_id}/approve")
async def approve_leave_request(
    leave_id: int,
    comments: Optional[str] = None,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Approve a leave request (HR/Admin only)"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.status not in [LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW]:
        raise HTTPException(status_code=400, detail="Leave request cannot be approved")
    
    previous_status = leave_request.status.value
    leave_request.status = LeaveStatus.APPROVED
    leave_request.reviewed_by = current_user.id
    leave_request.reviewed_at = datetime.now()
    leave_request.reviewer_comments = comments
    
    # STEP 6 FIX: Update medical certificate final_status if certificate exists
    if leave_request.leave_type == LeaveType.SICK and leave_request.medical_certificate_url:
        medical_cert = db.query(MedicalCertificate).filter(
            MedicalCertificate.leave_id == leave_request.id
        ).first()
        
        if medical_cert:
            # Update medical certificate final status
            medical_cert.final_status = "APPROVED"
            medical_cert.hr_reason = comments or "Medical certificate approved by HR"
            
            # Log AI vs HR decision for audit (if AI recommendation exists)
            if medical_cert.ai_recommendation:
                if medical_cert.ai_recommendation == "APPROVE":
                    print(f"✓ HR decision aligns with AI recommendation (APPROVE)")
                else:
                    print(f"⚠ HR overrode AI recommendation ({medical_cert.ai_recommendation} → APPROVED)")
                    if comments:
                        print(f"  HR reasoning: {comments}")
    
    # Update leave balance
    employee = db.query(User).filter(User.id == leave_request.employee_id).first()
    if employee:
        balance = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee.id,
            LeaveBalance.leave_type == leave_request.leave_type,
            LeaveBalance.year == datetime.now().year
        ).first()
        
        if balance:
            balance.used_days += leave_request.total_days
            balance.pending_days = max(0, balance.pending_days - leave_request.total_days)
            balance.remaining_days = balance.total_days - balance.used_days
    
    # Create audit log
    audit_log = LeaveAuditLog(
        leave_request_id=leave_id,
        action="Approved",
        actor_id=current_user.id,
        actor_type="USER",
        previous_status=previous_status,
        new_status=LeaveStatus.APPROVED.value,
        details=comments or "Leave request approved by HR"
    )
    db.add(audit_log)
    db.commit()
    
    # Send email notification to employee
    if employee and employee.email:
        try:
            await email_service.send_leave_approved(
                to_email=employee.email,
                employee_name=f"{employee.first_name} {employee.last_name}",
                leave_type=leave_request.leave_type.value,
                start_date=leave_request.start_date.strftime("%Y-%m-%d"),
                end_date=leave_request.end_date.strftime("%Y-%m-%d"),
                total_days=leave_request.total_days,
                reason_text=leave_request.reason_text,
                explanation=comments
            )
        except Exception as e:
            # Log but don't fail the approval
            print(f"Failed to send approval email: {e}")
    
    return {"message": "Leave request approved", "status": "APPROVED"}


@router.put("/{leave_id}/reject")
async def reject_leave_request(
    leave_id: int,
    reason: str,
    current_user: User = Depends(require_role(UserRole.HR, UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Reject a leave request (HR/Admin only)"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.status not in [LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW]:
        raise HTTPException(status_code=400, detail="Leave request cannot be rejected")
    
    previous_status = leave_request.status.value
    leave_request.status = LeaveStatus.REJECTED
    leave_request.reviewed_by = current_user.id
    leave_request.reviewed_at = datetime.now()
    leave_request.reviewer_comments = reason
    
    # STEP 6 FIX: Update medical certificate final_status if certificate exists
    if leave_request.leave_type == LeaveType.SICK and leave_request.medical_certificate_url:
        medical_cert = db.query(MedicalCertificate).filter(
            MedicalCertificate.leave_id == leave_request.id
        ).first()
        
        if medical_cert:
            # Update medical certificate final status
            medical_cert.final_status = "REJECTED"
            medical_cert.hr_reason = reason
            
            # Log AI vs HR decision for audit (if AI recommendation exists)
            if medical_cert.ai_recommendation:
                if medical_cert.ai_recommendation == "REJECT":
                    print(f"✓ HR decision aligns with AI recommendation (REJECT)")
                else:
                    print(f"⚠ HR overrode AI recommendation ({medical_cert.ai_recommendation} → REJECTED)")
                    print(f"  HR reasoning: {reason}")
    
    # Get employee for email
    employee = db.query(User).filter(User.id == leave_request.employee_id).first()
    
    # Create audit log
    audit_log = LeaveAuditLog(
        leave_request_id=leave_id,
        action="Rejected",
        actor_id=current_user.id,
        actor_type="USER",
        previous_status=previous_status,
        new_status=LeaveStatus.REJECTED.value,
        details=reason
    )
    db.add(audit_log)
    db.commit()
    
    # Send email notification to employee
    if employee and employee.email:
        try:
            await email_service.send_leave_rejected(
                to_email=employee.email,
                employee_name=f"{employee.first_name} {employee.last_name}",
                leave_type=leave_request.leave_type.value,
                start_date=leave_request.start_date.strftime("%Y-%m-%d"),
                end_date=leave_request.end_date.strftime("%Y-%m-%d"),
                total_days=leave_request.total_days,
                reason=reason,
                employee_reason=leave_request.reason_text
            )
        except Exception as e:
            # Log but don't fail the rejection
            print(f"Failed to send rejection email: {e}")
    
    return {"message": "Leave request rejected", "status": "REJECTED"}


@router.put("/{leave_id}/cancel")
async def cancel_leave_request(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel a leave request (only by the employee who created it)"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    if leave_request.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to cancel this request")
    
    if leave_request.status not in [LeaveStatus.PENDING, LeaveStatus.PENDING_REVIEW]:
        raise HTTPException(status_code=400, detail="Leave request cannot be cancelled")
    
    previous_status = leave_request.status.value
    leave_request.status = LeaveStatus.CANCELLED
    
    # Create audit log
    audit_log = LeaveAuditLog(
        leave_request_id=leave_id,
        action="Cancelled",
        actor_id=current_user.id,
        actor_type="USER",
        previous_status=previous_status,
        new_status=LeaveStatus.CANCELLED.value,
        details="Leave request cancelled by employee"
    )
    db.add(audit_log)
    db.commit()
    
    return {"message": "Leave request cancelled", "status": "CANCELLED"}


@router.get("/{leave_id}/audit", response_model=List[AuditLogResponse])
async def get_leave_audit_trail(
    leave_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get audit trail for a leave request"""
    leave_request = db.query(LeaveRequest).filter(LeaveRequest.id == leave_id).first()
    
    if not leave_request:
        raise HTTPException(status_code=404, detail="Leave request not found")
    
    # Check permissions
    if current_user.role == UserRole.EMPLOYEE and leave_request.employee_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this audit trail")
    
    audit_logs = db.query(LeaveAuditLog).filter(
        LeaveAuditLog.leave_request_id == leave_id
    ).order_by(LeaveAuditLog.created_at.asc()).all()
    
    return [AuditLogResponse.model_validate(log) for log in audit_logs]
