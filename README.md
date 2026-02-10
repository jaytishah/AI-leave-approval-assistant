# AI-Assisted Leave Management System

A comprehensive leave management system powered by AI (Gemini 2.5 Flash) for intelligent leave request processing, with React frontend and FastAPI backend.

## Features

### 🤖 AI-Powered Processing
- Automatic leave request evaluation using Gemini 2.5 Flash
- Validity scoring and risk assessment
- Smart recommendations for approval/rejection
- Pattern detection for suspicious requests

### 👥 Role-Based Access
- **Employee**: Submit leave requests, view balances, track request status
- **HR Manager**: Review pending requests, approve/reject with AI assistance
- **Admin**: System configuration, policy management, AI settings

### 📊 Dashboard Features
- Real-time leave balance tracking
- AI-suggested optimal leave dates
- Calendar view with team leaves
- Audit trail for all actions

### 🔒 Security
- JWT-based authentication
- Role-based authorization
- Password hashing with bcrypt
- Secure API endpoints

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
│   │   ├── api/           # API routes
│   │   ├── core/          # Config, security, database
│   │   ├── models/        # SQLAlchemy models
│   │   ├── schemas/       # Pydantic schemas
│   │   └── services/      # Business logic
│   ├── main.py            # FastAPI app entry
│   ├── seed_db.py         # Database seeding
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   │   ├── components/    # Reusable UI components
│   │   ├── pages/         # Page components
│   │   ├── services/      # API services
│   │   ├── store/         # Zustand stores
│   │   ├── types/         # TypeScript types
│   │   └── App.tsx        # Main app component
│   ├── package.json
│   └── vite.config.ts
│
└── README.md
```

## Getting Started

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
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Leave Processing Logic

The AI-powered leave processing follows this workflow:

1. **Load Request** - Fetch leave request and employee details
2. **Validate Input** - Check for valid dates and leave type
3. **Compute Stats** - Calculate leave balance, history, patterns
4. **Check Policy Rules** - Verify against company leave policies
5. **AI Evaluation** - Send to Gemini for intelligent assessment
6. **Final Decision** - Combine rule-based and AI results
7. **Persist & Notify** - Save to database and send notifications

## License

MIT License - see LICENSE file for details.
