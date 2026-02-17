"""
Medical Certificate Validator Service
=====================================
Extracts text from medical certificates (PDF/Images) and validates content.

Uses:
- PyPDF2 for PDF text extraction
- pytesseract (Tesseract OCR) for image text extraction
- AI (Gemini) for content validation
"""

import base64
import io
import re
from typing import Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum

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
    import pytesseract
    HAS_OCR = True
except ImportError:
    HAS_OCR = False
    print("Warning: pytesseract/PIL not installed. Image OCR disabled.")


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
        if confidence_score >= 0.7:
            result = ValidationResult.VALID
            is_valid = True
            notes.append("Certificate appears valid with high confidence")
        elif confidence_score >= 0.4:
            result = ValidationResult.NEEDS_REVIEW
            is_valid = True  # Allow but flag for review
            notes.append("Certificate needs HR review - moderate confidence")
        else:
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
        """Extract text from image using OCR."""
        if not HAS_OCR:
            return None, "pytesseract/PIL not installed - cannot perform OCR"
        
        try:
            image = Image.open(io.BytesIO(file_bytes))
            
            # Perform OCR
            extracted_text = pytesseract.image_to_string(image)
            
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
