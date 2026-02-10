AI-Assisted Leave Management System – Project Plan 

1. Project Overview 

This project is an AI-assisted leave management system built using React, FastAPI, and MySQL. It supports three roles: Employee, HR, and Admin. The system automates leave evaluation using rule-based validation combined with AI advisory logic, while maintaining full auditability and human control. 

2. Technology Stack 

- Frontend: React 
- Backend: Python (FastAPI) 
- Database: MySQL 
- AI: LLM integration via backend 
- Email: SMTP or transactional email service 

3. System Architecture 

React-based dashboards communicate with FastAPI through REST APIs. FastAPI handles authentication, leave processing, AI evaluation, email notifications, and database operations. MySQL stores all user, leave, policy, and audit data. 

4. User Roles and Dashboards 

Employee Dashboard: 
- Apply for leave 
- Track leave status 
- View approval/rejection reasons 
 
HR Dashboard: 
- View pending leave requests 
- See AI recommendations and risk indicators 
- Approve, reject, or send for manual review 
 
Admin Dashboard: 
- Manage leave policies 
- Configure AI thresholds 
- View audit logs and analytics 

5. Database Design Overview 

Core tables include: 
- Users 
- Leave Requests 
- Leave Policies 
- AI Configuration 
- Leave Audit Logs 
 
Audit logs ensure traceability of every decision. 

6. Backend Workflow 

1. Employee submits leave request 
2. Backend validates request using deterministic rules 
3. AI evaluates leave reason and historical patterns 
4. Final decision is made using rules + AI + guardrails 
5. Decision is stored with audit metadata 
6. Email notification is sent to employee 

7. Rules Engine 

The rules engine checks leave balance, date validity, policy constraints, frequent leave patterns, blackout periods, and mandatory fields. Blocking rule violations lead to immediate rejection. 

8. AI Evaluation Logic 

AI evaluates the plausibility of the leave reason using anonymized data. It returns a structured response including a validity score, risk flags, recommended action, and rationale. AI is advisory only. 

9. Decision Logic 

Final decisions are based on configurable thresholds. High-confidence low-risk requests may be auto-approved, high-risk low-confidence requests may be auto-rejected, and complex cases are routed for manual HR review. 

10. Email Notification System 

Automated emails are sent when a leave is approved, rejected, or marked for manual review. Emails include leave dates and decision explanation. 

11. Security and Compliance 

Role-based access control, minimal AI data exposure, audit trails, and fail-safe AI fallback mechanisms are implemented to ensure compliance and responsible AI usage. 

12. Outcome 

The system provides a scalable, enterprise-grade leave management workflow with intelligent automation, transparency, and human oversight.