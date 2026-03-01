"""
Medical Certificate Validator Service
=====================================
Extracts text from medical certificates (PDF/Images) and validates content.

Uses:
- EasyOCR for image text extraction (English only, gpu=False)
- PyPDF2 for PDF text extraction (optional)
- AI (Gemini) for content validation (optional)

ARCHITECTURE:
Step 1: File Upload Handling - Save files securely
Step 2: EasyOCR Extraction - Extract raw text and store in DB
"""

import base64
import io
import re
import ssl
import os
import uuid
from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

# Fix SSL certificate issues on macOS
ssl._create_default_https_context = ssl._create_unverified_context

# PDF extraction
try:
    import PyPDF2
    HAS_PYPDF2 = True
except ImportError:
    HAS_PYPDF2 = False
    print("Warning: PyPDF2 not installed. PDF text extraction disabled.")

# Image OCR
try:
    from PIL import Image
    import easyocr
    HAS_OCR = True
    # Initialize EasyOCR reader (singleton pattern for performance)
    _ocr_reader = None
except ImportError:
    HAS_OCR = False
    _ocr_reader = None
    print("Warning: EasyOCR/PIL not installed. Image OCR disabled.")


class ValidationResult(str, Enum):
    VALID = "VALID"
    INVALID = "INVALID"
    NEEDS_REVIEW = "NEEDS_REVIEW"
    EXTRACTION_FAILED = "EXTRACTION_FAILED"


@dataclass
class CertificateValidationResult:
    """Result of medical certificate validation"""
    is_valid: bool
    result: ValidationResult
    extracted_text: Optional[str] = None
    confidence_score: float = 0.0
    detected_fields: dict = None
    validation_notes: List[str] = None
    
    def __post_init__(self):
        if self.detected_fields is None:
            self.detected_fields = {}
        if self.validation_notes is None:
            self.validation_notes = []


class MedicalCertificateValidator:
    """
    Validates medical certificates by extracting and analyzing text content.
    
    Validation checks:
    1. Extract text from PDF or image
    2. Check for required keywords (medical, doctor, patient, date, etc.)
    3. Detect key fields (doctor name, hospital, date, diagnosis)
    4. Calculate confidence score
    5. Optionally use AI for deeper validation
    """
    
    # Keywords that should appear in a valid medical certificate
    REQUIRED_KEYWORDS = [
        # Medical terms
        r'\b(medical|certificate|doctor|dr\.|physician|clinic|hospital|healthcare)\b',
        # Patient related
        r'\b(patient|name|diagnosis|treatment|prescription|illness|disease|condition)\b',
        # Date related
        r'\b(date|from|to|period|days?|leave|rest)\b',
    ]
    
    # Keywords that indicate it's likely a medical certificate
    MEDICAL_INDICATORS = [
        'medical certificate', 'fitness certificate', 'sick leave',
        'medical leave', 'doctor', 'dr.', 'physician', 'clinic',
        'hospital', 'healthcare', 'diagnosis', 'treatment',
        'prescription', 'patient', 'illness', 'disease',
        'rest advised', 'leave recommended', 'unfit for duty',
        'fit to resume', 'medical practitioner', 'mbbs', 'md',
        'registration no', 'license no'
    ]
    
    # Patterns to extract specific fields
    FIELD_PATTERNS = {
        'date': r'(?:date|dated?)[\s:]*(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})',
        'patient_name': r'(?:patient|name|mr\.|mrs\.|ms\.)[\s:]*([A-Za-z\s]+)',
        'doctor_name': r'(?:dr\.?|doctor)[\s:]*([A-Za-z\s\.]+)',
        'hospital': r'(?:hospital|clinic|medical center)[\s:]*([A-Za-z\s]+)',
        'diagnosis': r'(?:diagnosis|condition|suffering from)[\s:]*([A-Za-z\s,]+)',
        'leave_days': r'(\d+)\s*(?:days?|day\'?s?)\s*(?:leave|rest|off)',
        'registration_no': r'(?:reg(?:istration)?\.?\s*no\.?|license\s*no\.?)[\s:]*([A-Za-z0-9/-]+)',
    }
    
    def __init__(self, use_ai_validation: bool = False, ai_service = None):
        """
        Initialize the validator.
        
        Args:
            use_ai_validation: Whether to use AI for deeper content validation
            ai_service: AI service instance for validation (optional)
        """
        self.use_ai_validation = use_ai_validation
        self.ai_service = ai_service
    
    def validate_certificate(
        self, 
        file_data: str, 
        filename: str
    ) -> CertificateValidationResult:
        """
        Main validation method - extracts text and validates content.
        
        Args:
            file_data: Base64 encoded file data (data:mime;base64,...)
            filename: Original filename
            
        Returns:
            CertificateValidationResult with validation details
        """
        notes = []
        
        # Step 1: Extract text from file
        extracted_text, extraction_error = self._extract_text(file_data, filename)
        
        if extraction_error:
            notes.append(f"Extraction error: {extraction_error}")
            return CertificateValidationResult(
                is_valid=False,
                result=ValidationResult.EXTRACTION_FAILED,
                extracted_text=None,
                confidence_score=0.0,
                validation_notes=notes
            )
        
        if not extracted_text or len(extracted_text.strip()) < 20:
            notes.append("Insufficient text extracted from document")
            return CertificateValidationResult(
                is_valid=False,
                result=ValidationResult.NEEDS_REVIEW,
                extracted_text=extracted_text,
                confidence_score=0.1,
                validation_notes=notes
            )
        
        # Step 2: Analyze extracted text
        confidence_score, detected_fields, analysis_notes = self._analyze_text(extracted_text)
        notes.extend(analysis_notes)
        
        # Step 3: Determine validation result
        # Note: confidence_score here is 0.0-1.0, so 0.7 = 70%
        if confidence_score >= 0.7:  # >= 70% is HIGH
            result = ValidationResult.VALID
            is_valid = True
            notes.append("Certificate appears valid with high confidence")
        elif confidence_score >= 0.4:  # 40-69% is MEDIUM
            result = ValidationResult.NEEDS_REVIEW
            is_valid = True  # Allow but flag for review
            notes.append("Certificate needs HR review - moderate confidence")
        else:  # < 40% is LOW
            result = ValidationResult.INVALID
            is_valid = False
            notes.append("Certificate appears invalid - low confidence score")
        
        return CertificateValidationResult(
            is_valid=is_valid,
            result=result,
            extracted_text=extracted_text[:500] if extracted_text else None,  # Truncate for storage
            confidence_score=confidence_score,
            detected_fields=detected_fields,
            validation_notes=notes
        )
    
    def _extract_text(self, file_data: str, filename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract text from base64 encoded file.
        
        Returns:
            Tuple of (extracted_text, error_message)
        """
        try:
            # Parse base64 data
            if ',' in file_data:
                header, base64_content = file_data.split(',', 1)
            else:
                base64_content = file_data
                header = ''
            
            # Decode base64
            file_bytes = base64.b64decode(base64_content)
            
            # Determine file type
            filename_lower = filename.lower()
            
            if filename_lower.endswith('.pdf') or 'pdf' in header:
                return self._extract_from_pdf(file_bytes)
            elif filename_lower.endswith(('.jpg', '.jpeg', '.png')) or 'image' in header:
                return self._extract_from_image(file_bytes)
            else:
                return None, f"Unsupported file type: {filename}"
                
        except Exception as e:
            return None, f"Error processing file: {str(e)}"
    
    def _extract_from_pdf(self, file_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
        """Extract text from PDF file."""
        if not HAS_PYPDF2:
            return None, "PyPDF2 not installed - cannot extract PDF text"
        
        try:
            pdf_file = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text_parts = []
            for page in pdf_reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text)
            
            extracted_text = '\n'.join(text_parts)
            
            if not extracted_text.strip():
                # PDF might be image-based, try OCR
                return None, "PDF contains no extractable text (may be image-based)"
            
            return extracted_text, None
            
        except Exception as e:
            return None, f"PDF extraction error: {str(e)}"
    
    def _extract_from_image(self, file_bytes: bytes) -> Tuple[Optional[str], Optional[str]]:
        """Extract text from image using EasyOCR."""
        global _ocr_reader
        
        if not HAS_OCR:
            return None, "EasyOCR/PIL not installed - cannot perform OCR"
        
        try:
            # Initialize EasyOCR reader if not already done (singleton)
            if _ocr_reader is None:
                _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            
            # Convert bytes to image
            image = Image.open(io.BytesIO(file_bytes))
            
            # Perform OCR using EasyOCR
            results = _ocr_reader.readtext(image, detail=0)  # detail=0 returns only text
            
            # Combine all detected text lines
            extracted_text = '\n'.join(results)
            
            if not extracted_text.strip():
                return None, "No text detected in image"
            
            return extracted_text, None
            
        except Exception as e:
            return None, f"OCR error: {str(e)}"
    
    def _analyze_text(self, text: str) -> Tuple[float, dict, List[str]]:
        """
        Analyze extracted text for medical certificate indicators.
        
        Returns:
            Tuple of (confidence_score, detected_fields, notes)
        """
        text_lower = text.lower()
        notes = []
        score_components = []
        
        # Check 1: Required keyword categories (30% of score)
        keyword_matches = 0
        for pattern in self.REQUIRED_KEYWORDS:
            if re.search(pattern, text_lower):
                keyword_matches += 1
        
        keyword_score = (keyword_matches / len(self.REQUIRED_KEYWORDS)) * 0.3
        score_components.append(keyword_score)
        notes.append(f"Keyword categories matched: {keyword_matches}/{len(self.REQUIRED_KEYWORDS)}")
        
        # Check 2: Medical indicators (40% of score)
        indicator_count = sum(1 for ind in self.MEDICAL_INDICATORS if ind in text_lower)
        indicator_score = min(indicator_count / 5, 1.0) * 0.4  # Cap at 5 matches
        score_components.append(indicator_score)
        notes.append(f"Medical indicators found: {indicator_count}")
        
        # Check 3: Extract and validate specific fields (30% of score)
        detected_fields = {}
        fields_found = 0
        
        for field_name, pattern in self.FIELD_PATTERNS.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                detected_fields[field_name] = match.group(1).strip()
                fields_found += 1
        
        field_score = (fields_found / len(self.FIELD_PATTERNS)) * 0.3
        score_components.append(field_score)
        notes.append(f"Fields detected: {list(detected_fields.keys())}")
        
        # Calculate final confidence score
        confidence_score = sum(score_components)
        
        # Bonus: If key fields like doctor and date are found, boost confidence
        if 'doctor_name' in detected_fields and 'date' in detected_fields:
            confidence_score = min(confidence_score + 0.15, 1.0)
            notes.append("Bonus: Doctor name and date detected")
        
        return round(confidence_score, 2), detected_fields, notes


# ========================================================
# STEP 1: FILE UPLOAD HANDLING
# ========================================================

def save_medical_certificate_file(
    file_content: bytes,
    filename: str,
    leave_id: int
) -> Dict[str, Any]:
    """
    Save uploaded medical certificate file securely.
    
    Args:
        file_content: Raw file bytes
        filename: Original filename
        leave_id: Leave request ID
        
    Returns:
        Dict with file_path, file_name, file_size, file_type
        
    Validates:
        - File type (jpg, png, jpeg, pdf)
        - Creates secure filename
        - Saves to uploads/medical_certificates/
    """
    # Validate file type
    filename_lower = filename.lower()
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.pdf']
    
    file_ext = None
    for ext in allowed_extensions:
        if filename_lower.endswith(ext):
            file_ext = ext
            break
    
    if not file_ext:
        raise ValueError(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
    
    # Determine file type/mime
    file_type_map = {
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.png': 'image/png',
        '.pdf': 'application/pdf'
    }
    file_type = file_type_map.get(file_ext, 'application/octet-stream')
    
    # Generate secure filename: leave_{leave_id}_{uuid}{ext}
    secure_filename = f"leave_{leave_id}_{uuid.uuid4()}{file_ext}"
    
    # Create directory if it doesn't exist
    upload_dir = Path("uploads/medical_certificates")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Full file path
    file_path = upload_dir / secure_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(file_content)
    
    # Get file size
    file_size = len(file_content)
    
    return {
        "file_path": str(file_path),
        "file_name": filename,
        "file_size": file_size,
        "file_type": file_type
    }


# ========================================================
# STEP 2: EASY OCR EXTRACTION
# ========================================================

def perform_ocr(file_path: str) -> Dict[str, Any]:
    """
    Extract text from medical certificate image using EasyOCR.
    
    Args:
        file_path: Path to the saved file
        
    Returns:
        Dict with:
            - extracted_text: Full raw text (LONGTEXT)
            - success: Boolean
            - error: Error message if any
            
    Uses:
        - EasyOCR with English language only
        - gpu=False (CPU only)
        - Combines all detected text into clean multiline string
        
    IMPORTANT: Raw text is NEVER deleted - stored permanently for audit
    """
    global _ocr_reader
    
    if not HAS_OCR:
        return {
            "extracted_text": None,
            "success": False,
            "error": "EasyOCR/PIL not installed - cannot perform OCR"
        }
    
    try:
        file_path_obj = Path(file_path)
        
        # Check if file exists
        if not file_path_obj.exists():
            return {
                "extracted_text": None,
                "success": False,
                "error": f"File not found: {file_path}"
            }
        
        # Check file type
        file_ext = file_path_obj.suffix.lower()
        
        # Handle PDF files (try text extraction first, then OCR if needed)
        if file_ext == '.pdf':
            if HAS_PYPDF2:
                try:
                    with open(file_path, 'rb') as f:
                        pdf_reader = PyPDF2.PdfReader(f)
                        text_parts = []
                        
                        for page in pdf_reader.pages:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                text_parts.append(page_text)
                        
                        if text_parts:
                            extracted_text = '\n'.join(text_parts)
                            return {
                                "extracted_text": extracted_text,
                                "success": True,
                                "error": None
                            }
                except Exception as e:
                    # PDF text extraction failed, will try OCR below
                    pass
            
            # PDF is image-based or extraction failed
            return {
                "extracted_text": None,
                "success": False,
                "error": "PDF text extraction not supported or PDF is image-based. Please upload as JPG/PNG."
            }
        
        # Handle image files with EasyOCR
        if file_ext not in ['.jpg', '.jpeg', '.png']:
            return {
                "extracted_text": None,
                "success": False,
                "error": f"Unsupported file type: {file_ext}"
            }
        
        # Initialize EasyOCR reader (singleton pattern)
        if _ocr_reader is None:
            _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
        
        # Perform OCR - EasyOCR with English only, gpu=False
        # EasyOCR readtext() accepts: file path (string), numpy array, or bytes
        # Pass file path directly as string
        results = _ocr_reader.readtext(str(file_path), detail=0)
        
        # Combine all detected text lines into clean multiline string
        extracted_text = '\n'.join(results)
        
        # Check if any text was extracted
        if not extracted_text or not extracted_text.strip():
            return {
                "extracted_text": "",
                "success": True,
                "error": "No text detected in image (blank or unclear image)"
            }
        
        return {
            "extracted_text": extracted_text,
            "success": True,
            "error": None
        }
        
    except Exception as e:
        return {
            "extracted_text": None,
            "success": False,
            "error": f"OCR extraction failed: {str(e)}"
        }


# ========================================================
# STEP 3: STRUCTURED FIELD EXTRACTION
# ========================================================

def extract_structured_fields(extracted_text: str) -> Dict[str, Any]:
    """
    Extract structured fields from raw OCR text using ROBUST detection-based approach.
    
    ROBUST VERSION:
    - Implements detection-based logic with boolean flags
    - Separates text extraction from detection confirmation
    - Never auto-rejects on missing fields
    - Emphasizes presence detection over perfect extraction
    
    Args:
        extracted_text: Raw text from OCR (Step 2)
        
    Returns:
        Dict containing:
            MANDATORY FIELDS (Detection-Based):
            - doctor_name_text: str or None
            - doctor_name_detected: bool
            - clinic_name_text: str or None
            - clinic_name_detected: bool
            - certificate_date: str or None (raw string format)
            - date_detected: bool
            - medical_keywords_detected: bool
            - signature_or_stamp_detected: bool
            
            OPTIONAL FIELDS:
            - rest_days: int or None
            - diagnosis: str or None
            - registration_number: str or None
            - contact_number: str or None
            
    IMPORTANT: Missing field does NOT auto-reject.
    Presence detection is more important than perfect extraction.
    """
    
    if not extracted_text or not extracted_text.strip():
        return {
            # Doctor information
            "doctor_name_text": None,
            "doctor_name_detected": False,
            # Clinic information
            "clinic_name_text": None,
            "clinic_name_detected": False,
            # Date information
            "certificate_date": None,
            "date_detected": False,
            # Medical keywords
            "medical_keywords_detected": False,
            # Signature/Stamp
            "signature_or_stamp_detected": False,
            # Optional fields
            "rest_days": None,
            "diagnosis": None,
            "registration_number": None,
            "contact_number": None
        }
    
    text_lower = extracted_text.lower()
    fields = {}
    
    # ========================================
    # MANDATORY FIELD 1: DOCTOR INFORMATION (Detection-Based)
    # ========================================
    doctor_name_text = None
    doctor_name_detected = False
    
    # Detect doctor-related keywords first
    doctor_indicators = ['dr.', 'dr', 'doctor', 'physician', 'mbbs', 'md', 'bams', 'bhms', 'ayush']
    doctor_detected_keyword = any(indicator in text_lower for indicator in doctor_indicators)
    
    if doctor_detected_keyword:
        doctor_name_detected = True  # Pattern detected
        
        # Try to extract actual name
        doctor_patterns = [
            r'(?:dr\.?|doctor|physician)\s*[:\-]?\s*([A-Z][a-z]+(?:\s+[A-Z]\.?)?(?:\s+[A-Z][a-z]+)+)',
            r'([A-Z][a-z]+\s+[A-Z][a-z]+)\s*,?\s*(?:MBBS|MD|BAMS|BHMS)',
            r'DR[\.:\s]+\(?(?:MRS|MR)?\)?\s*([A-Z\s\.]+)',
            r'(?:Dr\.?\s+)([A-Z][a-zA-Z\s\.]+?)(?:\n|,|MBBS|MD)',
        ]
        
        for pattern in doctor_patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE | re.MULTILINE)
            if match:
                doctor_name_text = match.group(1).strip()
                # Clean up the name
                doctor_name_text = re.sub(r'\s+', ' ', doctor_name_text)
                if len(doctor_name_text) > 3:  # Valid name should be > 3 chars
                    break
    
    fields['doctor_name_text'] = doctor_name_text
    fields['doctor_name_detected'] = doctor_name_detected
    
    # ========================================
    # MANDATORY FIELD 2: CLINIC INFORMATION (Detection-Based)
    # ========================================
    clinic_name_text = None
    clinic_name_detected = False
    
    # Detect clinic-related keywords first
    clinic_indicators = ['clinic', 'hospital', 'medical center', 'healthcare', 'health center', 'medical']
    clinic_detected_keyword = any(indicator in text_lower for indicator in clinic_indicators)
    
    if clinic_detected_keyword:
        clinic_name_detected = True  # Pattern detected
        
        # Try to extract actual clinic name
        clinic_patterns = [
            r'(?:clinic|hospital|medical center|health(?:care)? center)[:\s]*([A-Za-z\s]+?)(?:\n|$|,)',
            r'([A-Z][A-Za-z\s&\-]+(?:CLINIC|HOSPITAL|MEDICAL CENTER))',
            r'([A-Z][A-Za-z\s]+)\s+(?:CLINIC|HOSPITAL)',
            r'([A-Z][A-Z\s]+)\s*\n',  # All caps line (often clinic name)
        ]
        
        for pattern in clinic_patterns:
            match = re.search(pattern, extracted_text, re.IGNORECASE | re.MULTILINE)
            if match:
                clinic_name_text = match.group(1).strip()
                # Clean up
                clinic_name_text = re.sub(r'\s+', ' ', clinic_name_text)
                # Filter out common false positives
                if len(clinic_name_text) > 3 and clinic_name_text.lower() not in ['medical certificate', 'the clinic', 'the hospital']:
                    break
    
    fields['clinic_name_text'] = clinic_name_text
    fields['clinic_name_detected'] = clinic_name_detected
    
    # ========================================
    # MANDATORY FIELD 3: CERTIFICATE DATE (Detection-Based)
    # ========================================
    certificate_date = None
    date_detected = False
    
    # Multiple date format patterns
    date_patterns = [
        # With labels
        r'(?:date|dated?)[:\s]*(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2,4})',
        # Standalone dates
        r'\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{4})\b',
        # Date with month names
        r'\b(\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\s+\d{4})\b',
        # DD-MM-YY format
        r'\b(\d{1,2}[-/\.]\d{1,2}[-/\.]\d{2})\b',
    ]
    
    for pattern in date_patterns:
        match = re.search(pattern, text_lower, re.IGNORECASE)
        if match:
            date_str = match.group(1)
            certificate_date = date_str
            date_detected = True
            break
    
    fields['certificate_date'] = certificate_date
    fields['date_detected'] = date_detected
    
    # ========================================
    # MANDATORY FIELD 4: MEDICAL KEYWORDS DETECTED
    # ========================================
    medical_keywords = [
        # Core medical terms
        'medical', 'certificate', 'doctor', 'patient', 'diagnosis', 
        'treatment', 'prescription', 'illness', 'disease', 'clinic',
        'hospital', 'physician', 'consultation', 'examination',
        # Medical advice terms
        'advised', 'rest', 'sick', 'unwell', 'fever', 'infection',
        'viral', 'bacterial', 'pain', 'symptom',
        # Medical qualifications
        'mbbs', 'md', 'bams', 'bhms',
        # Medical procedures
        'under treatment', 'medically fit', 'unfit for duty',
        'advised rest', 'recommended rest'
    ]
    
    keywords_found = sum(1 for kw in medical_keywords if kw in text_lower)
    medical_keywords_detected = keywords_found >= 3  # At least 3 medical keywords
    
    fields['medical_keywords_detected'] = medical_keywords_detected
    
    # ========================================
    # MANDATORY FIELD 5: SIGNATURE/STAMP DETECTED
    # ========================================
    signature_indicators = [
        # Signature related
        'signature', 'signed', 'sign',
        # Stamp/Seal related
        'stamp', 'seal',
        # Registration/License (implies official stamp)
        'registration', 'license', 'reg no', 'reg.no', 'reg. no',
        # Medical qualifications (implies doctor signature)
        'mbbs', 'md', 'bams', 'bhms', 'ms', 'dnb',
        # Title indicators (implies signed by doctor)
        'dr.', 'dr', 'doctor'
    ]
    
    signature_found = any(indicator in text_lower for indicator in signature_indicators)
    fields['signature_or_stamp_detected'] = signature_found
    
    # ========================================
    # OPTIONAL FIELD 1: REST DAYS
    # ========================================
    rest_days = None
    rest_patterns = [
        r'(?:advised|recommended|prescribed)\s+(?:rest|leave)\s+(?:for|of)\s+(\d+)\s+days?',
        r'(\d+)\s+days?\s+(?:rest|leave|off)',
        r'rest\s+(?:for|of)\s+(\d+)\s+days?',
        r'leave\s+(?:for|of)\s+(\d+)\s+days?',
        r'(\d+)\s+day[s]?\s+medical\s+leave',
    ]
    
    for pattern in rest_patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                rest_days = int(match.group(1))
                if 1 <= rest_days <= 365:  # Sanity check
                    break
                else:
                    rest_days = None  # Invalid range
            except:
                pass
    
    fields['rest_days'] = rest_days
    
    # ========================================
    # OPTIONAL FIELD 2: DIAGNOSIS
    # ========================================
    diagnosis = None
    diagnosis_patterns = [
        r'(?:diagnosis|suffering from|diagnosed with)[:\s]+([A-Za-z\s,]+?)(?:\n|\.)',
        r'(?:condition|illness|disease)[:\s]+([A-Za-z\s]+?)(?:\n|\.)',
        r'(?:patient is suffering from|complaining of)[:\s]+([A-Za-z\s,]+?)(?:\n|\.)',
    ]
    
    for pattern in diagnosis_patterns:
        match = re.search(pattern, extracted_text, re.IGNORECASE)
        if match:
            diagnosis = match.group(1).strip()
            # Clean up
            diagnosis = re.sub(r'\s+', ' ', diagnosis)
            if len(diagnosis) > 3 and len(diagnosis) < 200:
                break
    
    fields['diagnosis'] = diagnosis
    
    # ========================================
    # OPTIONAL FIELD 3: REGISTRATION NUMBER
    # ========================================
    registration_number = None
    reg_patterns = [
        r'(?:reg(?:istration)?\.?\s*no\.?|license\s*no\.?)[:\s]*([A-Z0-9\-/\.]+)',
        r'(?:Reg No)[:\s\.]*([A-Z0-9\-/\.]+)',
        r'(?:Registration|License)[:\s]+([A-Z0-9\-/\.]+)',
        r'(?:MCI|SMC|Medical Council)[:\s]+([A-Z0-9\-/\.]+)',
    ]
    
    for pattern in reg_patterns:
        match = re.search(pattern, extracted_text, re.IGNORECASE)
        if match:
            registration_number = match.group(1).strip()
            # Clean up
            registration_number = re.sub(r'\s+', '', registration_number)
            if len(registration_number) > 3 and len(registration_number) < 50:
                break
    
    fields['registration_number'] = registration_number
    
    # ========================================
    # OPTIONAL FIELD 4: CONTACT NUMBER
    # ========================================
    contact_number = None
    phone_patterns = [
        r'(?:phone|tel|mobile|contact|call)[:\s]*(\+?\d[\d\s\-\(\)]{7,15})',
        r'\b(\d{10})\b',  # 10 digit number
        r'\b(\d{3}[-\s]?\d{3}[-\s]?\d{4})\b',  # Formatted phone
        r'\b(\+91[\s\-]?\d{10})\b',  # Indian format
    ]
    
    for pattern in phone_patterns:
        match = re.search(pattern, extracted_text)
        if match:
            contact_number = match.group(1).strip()
            # Clean up
            contact_number = re.sub(r'[^\d\+]', '', contact_number)
            if len(contact_number) >= 7 and len(contact_number) <= 15:
                break
    
    fields['contact_number'] = contact_number
    
    return fields


def calculate_confidence(structured_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate confidence score based on detection flags from Step 3.
    
    RULE-BASED CONFIDENCE SCORING (Total = 100 points):
    - +20 if doctor_name_detected is True
    - +20 if clinic_name_detected is True
    - +20 if medical_keywords_detected is True
    - +15 if date_detected is True
    - +15 if rest_days is NOT NULL
    - +10 if signature_or_stamp_detected is True
    
    CONFIDENCE LEVEL CLASSIFICATION:
    - > 70: HIGH
    - 40-70: MEDIUM
    - < 40: LOW
    
    HR REVIEW FLAG LOGIC:
    - If confidence_level == "LOW": requires_hr_review = True
    - Else: requires_hr_review = False
    
    IMPORTANT:
    - Low confidence does NOT auto-reject
    - It only signals HR to review carefully
    - System must NOT update final_status here
    
    Args:
        structured_fields: Dictionary returned from extract_structured_fields()
                          containing detection flags and extracted data
    
    Returns:
        Dict containing:
            - confidence_score: int (0-100)
            - confidence_level: str ("HIGH", "MEDIUM", "LOW")
            - requires_hr_review: bool
            - scoring_breakdown: dict (for transparency)
    """
    
    if not structured_fields:
        return {
            "confidence_score": 0,
            "confidence_level": "LOW",
            "requires_hr_review": True,
            "scoring_breakdown": {
                "doctor_name_detected": 0,
                "clinic_name_detected": 0,
                "medical_keywords_detected": 0,
                "date_detected": 0,
                "rest_days_provided": 0,
                "signature_or_stamp_detected": 0
            }
        }
    
    # Initialize score and breakdown
    score = 0
    breakdown = {}
    
    # Rule 1: Doctor name detected (+20 points)
    if structured_fields.get('doctor_name_detected', False):
        score += 20
        breakdown['doctor_name_detected'] = 20
    else:
        breakdown['doctor_name_detected'] = 0
    
    # Rule 2: Clinic name detected (+20 points)
    if structured_fields.get('clinic_name_detected', False):
        score += 20
        breakdown['clinic_name_detected'] = 20
    else:
        breakdown['clinic_name_detected'] = 0
    
    # Rule 3: Medical keywords detected (+20 points)
    if structured_fields.get('medical_keywords_detected', False):
        score += 20
        breakdown['medical_keywords_detected'] = 20
    else:
        breakdown['medical_keywords_detected'] = 0
    
    # Rule 4: Date detected (+15 points)
    if structured_fields.get('date_detected', False):
        score += 15
        breakdown['date_detected'] = 15
    else:
        breakdown['date_detected'] = 0
    
    # Rule 5: Rest days provided (+15 points)
    rest_days = structured_fields.get('rest_days')
    if rest_days is not None and rest_days > 0:
        score += 15
        breakdown['rest_days_provided'] = 15
    else:
        breakdown['rest_days_provided'] = 0
    
    # Rule 6: Signature or stamp detected (+10 points)
    if structured_fields.get('signature_or_stamp_detected', False):
        score += 10
        breakdown['signature_or_stamp_detected'] = 10
    else:
        breakdown['signature_or_stamp_detected'] = 0
    
    # Ensure score is within bounds (0-100)
    score = max(0, min(100, score))
    
    # Determine confidence level
    if score >= 70:  # Changed from > 70 to >= 70 (now 70 is HIGH)
        confidence_level = "HIGH"
    elif 40 <= score < 70:  # Changed from <= 70 to < 70
        confidence_level = "MEDIUM"
    else:  # score < 40
        confidence_level = "LOW"
    
    # Determine HR review requirement
    # Only LOW confidence requires HR review
    requires_hr_review = (confidence_level == "LOW")
    
    return {
        "confidence_score": score,
        "confidence_level": confidence_level,
        "requires_hr_review": requires_hr_review,
        "scoring_breakdown": breakdown
    }


# Convenience function for quick validation
def validate_medical_certificate(
    file_data: str, 
    filename: str,
    use_ai: bool = False
) -> CertificateValidationResult:
    """
    Quick validation of a medical certificate.
    
    Args:
        file_data: Base64 encoded file data
        filename: Original filename
        use_ai: Whether to use AI validation
        
    Returns:
        CertificateValidationResult
    """
    validator = MedicalCertificateValidator(use_ai_validation=use_ai)
    return validator.validate_certificate(file_data, filename)


# Test the module
if __name__ == "__main__":
    print("Medical Certificate Validator")
    print("=" * 50)
    print(f"PDF extraction available: {HAS_PYPDF2}")
    print(f"Image OCR available: {HAS_OCR}")
    print()
    
    # Test with sample text
    validator = MedicalCertificateValidator()
    
    sample_text = """
    MEDICAL CERTIFICATE
    
    Date: 02-02-2026
    
    This is to certify that Mr. John Smith has been examined 
    and found to be suffering from viral fever.
    
    The patient is advised rest for 3 days.
    
    Dr. Sarah Johnson, MBBS
    Registration No: MCI/12345
    City Hospital
    """
    
    # Simulate analysis
    score, fields, notes = validator._analyze_text(sample_text)
    
    print("Sample Analysis Results:")
    print(f"Confidence Score: {score}")
    print(f"Detected Fields: {fields}")
    print(f"Notes: {notes}")
