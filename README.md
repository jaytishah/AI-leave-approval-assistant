# AI-Assisted Leave Management System

A comprehensive enterprise-grade leave management system powered by AI (Gemini 2.5 Flash) for intelligent leave request processing, with React frontend and FastAPI backend.

## Features

### 🤖 AI-Powered Processing
- **Advanced AI Evaluation** using Gemini 2.5 Flash for intelligent leave analysis
- **Validity Scoring & Risk Assessment** with confidence-based decision thresholds
- **Smart Recommendations** for approval/rejection with detailed rationale
- **Pattern Detection** for suspicious requests and abuse prevention
- **Security Layer** with prompt injection detection (blocks manipulation attempts)
- **Input Validation** with random text and gibberish detection
- **Word Limit Enforcement** (5-300 words) preventing both lazy and verbose submissions

### 📋 Leave Request Management
- **Medical Certificate Upload** (mandatory for sick leave ≥2 days, max 5MB)
- **Certificate Validation** with OCR text extraction and field detection
- **Emergency Leave Flagging** to bypass advance notice requirements
- **Weekly/Monthly Tracking** (max 2 requests/week, 5/month by default)
- **Working Days Calculation** based on company weekly off policy
- **Real-time Balance Updates** with pending/used/remaining days

### 👥 Role-Based Access
- **Employee**: Submit leave requests, view balances, track request status, upload documents
- **HR Manager**: Review pending requests with complete employee data, approve/reject with AI assistance
- **Admin**: System configuration, policy management, AI settings, company policy configuration

### 📊 Dashboard Features
- **Real-time Leave Balance Tracking** across all leave types
- **AI-suggested Optimal Leave Dates** based on team availability
- **Calendar View** with team leaves and company holidays
- **Audit Trail** for all actions with detailed logging
- **AI Usage Analytics** tracking API calls, costs, and performance

### 🔒 Security & Validation
- **JWT-based Authentication** with secure token handling
- **Role-based Authorization** for all API endpoints
- **Password Hashing** with bcrypt
- **Prompt Injection Protection** (10+ detection patterns)
- **Input Sanitization** preventing SQL injection and XSS attacks
- **File Upload Security** (type validation, size limits, secure storage)

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **SQLAlchemy** - ORM for database operations
- **PyMySQL** - MySQL database driver
- **python-jose** - JWT token handling
- **google-generativeai** - Gemini AI integration
- **aiosmtplib** - Async email service

### Frontend
- **React 18** - UI library
- **Vite** - Build tool
- **TypeScript** - Type safety
- **Tailwind CSS** - Utility-first CSS
- **Framer Motion** - Animations
- **Zustand** - State management
- **React Router v6** - Routing
- **React Hook Form + Zod** - Form handling

## Project Structure

```
├── backend/
│   ├── app/
│   │   ├── api/                    # API routes
│   │   │   ├── auth.py            # Authentication endpoints
│   │   │   ├── leaves.py          # Leave management endpoints
│   │   │   ├── users.py           # User management endpoints
│   │   │   └── admin.py           # Admin & policy endpoints
│   │   ├── core/                   # Config, security, database
│   │   │   ├── config.py          # Environment configuration
│   │   │   ├── security.py        # JWT & password hashing
│   │   │   └── database.py        # Database connection
│   │   ├── models/                 # SQLAlchemy models
│   │   │   └── models.py          # All database models (17 models)
│   │   ├── schemas/                # Pydantic schemas
│   │   │   └── schemas.py         # Request/Response schemas
│   │   └── services/               # Business logic
│   │       ├── ai_service.py      # Gemini AI integration
│   │       ├── leave_processing.py # Leave workflow engine
│   │       ├── leave_utils.py     # Policy checks & calculations
│   │       ├── certificate_validator.py # Medical cert validation
│   │       └── email_service.py   # Notification service
│   ├── migrations/                 # Database migrations (9 scripts)
│   ├── uploads/                    # File storage
│   │   └── medical_certificates/  # Medical cert uploads
│   ├── main.py                     # FastAPI app entry
│   ├── seed_db.py                  # Database seeding
│   ├── import_holidays.py          # Holiday import utility
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/             # Reusable UI components
│   │   │   ├── forms/             # Form components
│   │   │   ├── layout/            # Layout components
│   │   │   └── ui/                # UI primitives
│   │   ├── pages/                  # Page components
│   │   │   ├── employee/          # Employee portal
│   │   │   ├── hr/                # HR portal
│   │   │   └── admin/             # Admin portal
│   │   ├── services/               # API services
│   │   │   └── api.ts             # API client
│   │   ├── store/                  # Zustand stores
│   │   │   └── authStore.ts       # Authentication state
│   │   ├── types/                  # TypeScript types
│   │   │   └── index.ts           # Type definitions
│   │   └── App.tsx                 # Main app component
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## Key Features Breakdown

### 1. **Medical Certificate Management**
- **Mandatory Upload**: Sick leave requests ≥2 working days require medical certificate
- **File Validation**: PDF, JPG, JPEG, PNG formats accepted (max 5MB)
- **OCR Extraction**: Automatic text extraction from certificates
- **Field Detection**: AI-powered extraction of doctor name, hospital, diagnosis, dates
- **Validation Results**: Confidence scoring and detected field verification
- **Secure Storage**: Files stored with unique identifiers in secure directory

### 2. **Company Policy Configuration**
- **Weekly Off Types**: 
  - Sunday only (6-day work week)
  - Saturday & Sunday (5-day work week)
  - Alternate Saturday (2nd & 4th Saturday off)
- **Working Days Calculation**: Accurate calculation excluding weekends and holidays
- **Holiday Management**: Import and manage company holidays
- **Policy Versioning**: Track policy changes with effective dates

### 3. **Advanced Leave Validation**
- **13 Strict Rejection Rules**:
  1. Missing/empty description
  2. Leave type mismatch (e.g., travel for sick leave)
  3. Vague/generic descriptions ("personal", "urgent")
  4. Unprofessional language ("lazy", "not in mood")
  5. Non-health reasons for sick leave
  6. Ambiguous medical claims without details
  7. Duration-reason inconsistency (minor issue, 5+ days)
  8. Work availability mention (should use WFH)
  9. Suspicious patterns (repeated "urgent")
  10. Missing medical proof reference (3+ days sick leave)
  11. Copy-paste generic templates
  12. Vague mental health claims without medical context
  13. Explicit policy violations (vacation for sick leave)

- **Word Count Limits**: 5-300 words (prevents both lazy and manipulation)
- **Prompt Injection Detection**: Blocks AI manipulation attempts
- **Random Text Filtering**: Rejects gibberish, keyboard mashing, meaningless input

### 4. **Weekly/Monthly Tracking**
- **Request Limits**: 
  - Max 2 leave requests per calendar week (Monday-Sunday)
  - Max 5 leave requests per calendar month
- **Day Limits**:
  - Max 3 leave days per week
  - Max 7 leave days per month
- **Configurable**: Admin can adjust limits via policy settings
- **Real-time Enforcement**: Checks applied during request submission

### 5. **HR Review Dashboard Enhancements**
- **Complete Employee Profile**: Name, email, department, role, avatar
- **All Leave Balances**: Annual, Sick, Casual, Maternity, Paternity
- **Balance Breakdown**: Total, used, pending, remaining days
- **Historical Context**: Past leave patterns and usage trends
- **Team Impact**: Coverage analysis and team availability
- **AI Recommendations**: Validity score, risk flags, suggested action

### 6. **AI Security & Accuracy**
- **Gemini 2.5 Flash**: Latest AI model for natural language understanding
- **Confidence Thresholds**: 
  - 85+ = Auto-approve (high confidence)
  - 70-84 = Good confidence approval
  - 60-69 = Reject suspicious requests
  - <60 = Escalate for manual review
- **Fallback System**: Rule-based validation if AI unavailable
- **Retry Logic**: Exponential backoff for API quota errors
- **Usage Tracking**: Log all AI calls with cost and performance metrics



### Prerequisites
- Python 3.10+
- Node.js 18+
- MySQL 8.0+
- Google Cloud account (for Gemini API)

### Backend Setup

1. Navigate to backend directory:
```bash
cd backend
```

2. Create virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database and API credentials
```

5. Run database migrations and seed:
```bash
python seed_db.py
```

6. Start the server:
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Configure environment:
```bash
cp .env.example .env
# Edit .env with your API URL
```

4. Start development server:
```bash
npm run dev
```

5. Open http://localhost:5173 in your browser

### Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@company.com | admin123 |
| HR | hr@company.com | hr123 |
| Employee | john@company.com | employee123 |

## Environment Variables

### Backend (.env)
```
DATABASE_URL=mysql+pymysql://user:pass@localhost/leave_management
SECRET_KEY=your-secret-key
GEMINI_API_KEY=your-gemini-api-key
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email
SMTP_PASSWORD=your-app-password
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000/api
```

## API Documentation

Once the backend is running, access:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key API Endpoints

#### Authentication (`/api/auth`)
- `POST /login` - User login with email/password
- `POST /register` - Create new user account
- `GET /me` - Get current user profile

#### Leave Management (`/api/leaves`)
- `POST /leaves` - Create leave request (with medical certificate upload)
- `GET /leaves` - List employee's leave requests
- `GET /leaves/{id}` - Get leave request details
- `GET /pending` - Get pending requests for HR
- `PUT /leaves/{id}` - Update leave request
- `POST /leaves/{id}/approve` - Approve leave request
- `POST /leaves/{id}/reject` - Reject leave request
- `DELETE /leaves/{id}` - Cancel leave request

#### User Management (`/api/users`)
- `GET /users` - List all users
- `GET /users/{id}` - Get user profile
- `GET /balances` - Get leave balances
- `PUT /users/{id}` - Update user profile

#### Admin & Policy (`/api/admin`)
- `GET /admin/policies` - List leave policies
- `PUT /admin/policies/{id}` - Update leave policy
- `GET /admin/policy` - Get company policy (weekly off config)
- `PUT /admin/policy` - Update company policy
- `GET /admin/holidays` - List holidays
- `POST /admin/holidays` - Add holiday
- `GET /admin/ai-usage` - AI usage analytics
- `GET /admin/dashboard/*` - Dashboard statistics

## Leave Processing Logic

The AI-powered leave processing follows this comprehensive workflow:

1. **Load Request** - Fetch leave request, employee details, and historical data
2. **Validate Input** 
   - Check word count (5-300 words)
   - Detect prompt injection attempts
   - Filter random text/gibberish
   - Verify medical certificate (if sick leave ≥2 days)
3. **Compute Statistics** 
   - Calculate leave balance across all types
   - Analyze historical leave patterns
   - Count leaves this week/month
   - Calculate working days (excluding weekends/holidays)
4. **Check Policy Rules** 
   - Verify against 13 strict rejection rules
   - Check weekly/monthly limits
   - Validate advance notice requirements
   - Check blackout periods
   - Verify consecutive leave limits
5. **AI Evaluation** 
   - Send to Gemini 2.5 Flash for intelligent assessment
   - Analyze reason quality and authenticity
   - Detect manipulation attempts
   - Generate confidence score and recommendations
6. **Apply Decision Thresholds**
   - Auto-approve high confidence (85+)
   - Reject suspicious requests (60-69)
   - Escalate borderline cases for manual review
7. **Persist & Notify** 
   - Save to database with audit trail
   - Update leave balances
   - Send email notifications
   - Log AI usage and costs

## Database Schema

### Core Models (17 Total)
- **User**: Employee information, role, department, manager
- **Department**: Organizational structure
- **LeavePolicy**: Leave allocation rules and limits
- **CompanyPolicy**: Weekly off configuration, effective dates
- **LeaveRequest**: Leave applications with AI analysis results
- **MedicalCertificate**: Medical certificate files and extracted data
- **LeaveBalance**: Current balance per employee per leave type
- **Holiday**: Company holidays and observances
- **LeaveAuditLog**: All actions on leave requests
- **AIConfiguration**: AI model settings and parameters
- **AIUsageLog**: AI API call tracking and cost analysis
- **ApprovalTask**: Workflow tasks for HR/Manager approval

### Key Migrations
1. `add_medical_certificate_table.py` - Medical certificate storage
2. `add_weekly_monthly_limits.py` - Weekly/monthly tracking fields
3. `add_company_policy.py` - Company policy configuration
4. `add_emergency_flag.py` - Emergency leave bypass
5. `add_detection_flags.py` - Certificate validation flags
6. `add_ai_usage_logs.py` - AI usage tracking
7. `update_casual_leave_to_15.py` - Company policy update

## Recent Enhancements

### 📋 Medical Certificate Management (v1.5)
- Mandatory medical certificate upload for sick leave ≥2 working days
- File validation with 5MB size limit (PDF, JPG, JPEG, PNG)
- OCR text extraction and field detection (doctor, hospital, diagnosis, dates)
- Confidence-based validation with detailed results
- Secure file storage with unique identifiers

### 🔒 Robust Validation System (v1.4)
- **Word Count Limits**: 5-300 words enforced
- **Prompt Injection Protection**: 10+ detection patterns blocking manipulation
- **Random Text Filtering**: Gibberish and keyboard mashing detection
- **13 Strict Rejection Rules**: Comprehensive policy enforcement
- **Fallback System**: Rule-based validation when AI unavailable

### 📊 Weekly/Monthly Tracking (v1.3)
- Calendar-based weekly tracking (max 2 requests/week)
- Monthly request limits (max 5 requests/month)
- Daily limits (max 3 days/week, 7 days/month)
- Configurable limits via admin policy settings
- Real-time enforcement during request submission

### ⚙️ Company Policy Settings (v1.2)
- **Weekly Off Configuration**: Sunday, SAT_SUN, ALT_SAT (alternate Saturday)
- **Working Days Calculation**: Accurate calculation excluding configured weekends
- **Holiday Management**: Import and manage company holidays
- **Policy Versioning**: Track changes with effective dates
- **Admin UI**: User-friendly policy configuration interface

### 👨‍💼 HR Review Enhancement (v1.1)
- Complete employee profiles in review dashboard
- All leave balances visible (Annual, Sick, Casual, etc.)
- Balance breakdown: total, used, pending, remaining
- Historical usage patterns and trends
- Team coverage analysis

### 🤖 AI Service Improvements (v1.0)
- Upgraded to **Gemini 2.5 Flash** model
- Confidence-based decision thresholds (85+ auto-approve)
- Enhanced prompt engineering with security rules
- Exponential backoff retry logic for quota errors
- AI usage tracking and cost analytics
- Comprehensive audit logging

## Implementation Documentation

Detailed implementation guides available in the repository:
- `MEDICAL_CERTIFICATE_FEATURE.md` - Medical certificate upload system
- `ROBUST_VALIDATION_IMPLEMENTATION.md` - Security and validation layers
- `WEEKLY_MONTHLY_TRACKING_IMPLEMENTATION.md` - Calendar-based tracking
- `WORD_LIMIT_VALIDATION.md` - Word count enforcement
- `POLICY_SETTINGS_IMPLEMENTATION.md` - Company policy configuration
- `HR_REVIEW_ENHANCEMENT.md` - HR dashboard improvements
- `FEATURE_1_IMPLEMENTATION.md` - Initial AI integration

## Contributing

This is an enterprise leave management system with strict quality standards:

1. **Code Quality**: Follow existing patterns and conventions
2. **Testing**: Test all new features thoroughly
3. **Documentation**: Update relevant .md files for new features
4. **Security**: Never commit API keys or sensitive data
5. **Migrations**: Create migration scripts for database changes



MIT License - see LICENSE file for details.
