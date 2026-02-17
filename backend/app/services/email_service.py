import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, List
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending email notifications"""
    
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USER
        self.password = settings.SMTP_PASSWORD
        self.from_email = settings.EMAIL_FROM
        self.from_name = settings.EMAIL_FROM_NAME
        
        # Log configuration on init (hide password)
        logger.info(f"[EMAIL] Initialized with host={self.host}, port={self.port}, user={self.username}, from={self.from_email}")
    
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email using Gmail SMTP"""
        
        # Check if email is configured
        if not self.username or not self.password:
            logger.error("[EMAIL] SMTP_USER or SMTP_PASSWORD not configured in .env")
            print(f"[EMAIL ERROR] SMTP credentials not configured. Set SMTP_USER and SMTP_PASSWORD in .env")
            return False
        
        try:
            message = MIMEMultipart("alternative")
            # IMPORTANT: Use the actual SMTP_USER email as the From address for Gmail
            message["From"] = f"{self.from_name} <{self.username}>"
            message["To"] = to_email
            message["Subject"] = subject
            
            # Add plain text fallback
            if text_content:
                message.attach(MIMEText(text_content, "plain"))
            else:
                # Generate plain text from subject
                message.attach(MIMEText(f"{subject}\n\nPlease view this email in HTML format.", "plain"))
            
            # Add HTML content
            message.attach(MIMEText(html_content, "html"))
            
            print(f"[EMAIL] Attempting to send email to {to_email} via {self.host}:{self.port}")
            
            # Send email using Gmail's TLS on port 587
            # Using start_tls=True for port 587 (STARTTLS)
            await aiosmtplib.send(
                message,
                hostname=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                start_tls=True,
                validate_certs=False  # Disable strict cert validation for local dev
            )
            
            logger.info(f"[EMAIL] ✅ Email sent successfully to {to_email}")
            print(f"[EMAIL] ✅ Email sent successfully to {to_email}")
            return True
            
        except aiosmtplib.SMTPAuthenticationError as e:
            logger.error(f"[EMAIL] ❌ Authentication failed: {str(e)}")
            print(f"[EMAIL ERROR] ❌ Authentication failed - check SMTP_USER and SMTP_PASSWORD in .env")
            print(f"[EMAIL ERROR] For Gmail, you need an App Password, not your regular password!")
            print(f"[EMAIL ERROR] Get one at: https://myaccount.google.com/apppasswords")
            return False
        except aiosmtplib.SMTPConnectError as e:
            logger.error(f"[EMAIL] ❌ Connection failed: {str(e)}")
            print(f"[EMAIL ERROR] ❌ Cannot connect to {self.host}:{self.port}")
            return False
        except Exception as e:
            logger.error(f"[EMAIL] ❌ Failed to send email to {to_email}: {str(e)}")
            print(f"[EMAIL ERROR] ❌ Failed to send email: {str(e)}")
            return False
    
    def _get_base_template(self, content: str) -> str:
        """Get base HTML email template with professional styling"""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.7;
                    color: #1f2937;
                    background-color: #f3f4f6;
                    margin: 0;
                    padding: 20px;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #60a5fa 100%);
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 28px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .header p {{
                    margin: 8px 0 0;
                    opacity: 0.95;
                    font-size: 15px;
                    font-weight: 400;
                }}
                .content {{
                    padding: 40px 30px;
                    background: #ffffff;
                }}
                .content h2 {{
                    margin-top: 0;
                    font-size: 22px;
                    color: #111827;
                    font-weight: 600;
                }}
                .content p {{
                    margin: 12px 0;
                    color: #4b5563;
                    font-size: 15px;
                }}
                .status-badge {{
                    display: inline-block;
                    padding: 10px 20px;
                    border-radius: 24px;
                    font-weight: 600;
                    font-size: 14px;
                    margin: 15px 0;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .status-approved {{
                    background: #d1fae5;
                    color: #065f46;
                    border: 2px solid #059669;
                }}
                .status-rejected {{
                    background: #fee2e2;
                    color: #991b1b;
                    border: 2px solid #dc2626;
                }}
                .status-pending {{
                    background: #fef3c7;
                    color: #92400e;
                    border: 2px solid #f59e0b;
                }}
                .details {{
                    background: #f9fafb;
                    padding: 24px;
                    border-radius: 10px;
                    margin: 25px 0;
                    border: 1px solid #e5e7eb;
                }}
                .details-row {{
                    display: flex;
                    justify-content: space-between;
                    padding: 12px 0;
                    border-bottom: 1px solid #e5e7eb;
                }}
                .details-row:last-child {{
                    border-bottom: none;
                }}
                .details-label {{
                    color: #6b7280;
                    font-size: 14px;
                    font-weight: 500;
                }}
                .details-value {{
                    font-weight: 600;
                    color: #111827;
                    font-size: 14px;
                }}
                .reason-box {{
                    background: #eff6ff;
                    border-left: 4px solid #3b82f6;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .reason-box h3 {{
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    color: #1e40af;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}
                .reason-box p {{
                    margin: 0;
                    color: #1e3a8a;
                    font-size: 15px;
                    line-height: 1.6;
                    font-style: italic;
                }}
                .rejection-reason {{
                    background: #fef2f2;
                    border-left: 4px solid #dc2626;
                    padding: 20px;
                    border-radius: 6px;
                    margin: 20px 0;
                }}
                .rejection-reason h3 {{
                    margin: 0 0 10px 0;
                    font-size: 14px;
                    color: #991b1b;
                    font-weight: 600;
                    text-transform: uppercase;
                }}
                .rejection-reason p {{
                    margin: 0;
                    color: #7f1d1d;
                    font-size: 15px;
                }}
                .footer {{
                    background: #f9fafb;
                    text-align: center;
                    padding: 30px;
                    color: #6b7280;
                    font-size: 13px;
                    border-top: 1px solid #e5e7eb;
                }}
                .footer p {{
                    margin: 5px 0;
                }}
                .footer a {{
                    color: #3b82f6;
                    text-decoration: none;
                }}
                .divider {{
                    height: 1px;
                    background: #e5e7eb;
                    margin: 25px 0;
                }}
                .button {{
                    display: inline-block;
                    background: #2563eb;
                    color: white !important;
                    padding: 14px 28px;
                    border-radius: 8px;
                    text-decoration: none;
                    font-weight: 600;
                    margin-top: 20px;
                    box-shadow: 0 2px 4px rgba(37, 99, 235, 0.3);
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🏢 LeaveAI Enterprise</h1>
                    <p>AI-Powered Leave Management System</p>
                </div>
                <div class="content">
                    {content}
                </div>
                <div class="footer">
                    <p><strong>LeaveAI Enterprise Portal</strong></p>
                    <p>This is an automated notification. Please do not reply to this email.</p>
                    <p style="margin-top: 15px;">© 2026 LeaveAI. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    async def send_leave_approved(
        self,
        to_email: str,
        employee_name: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        total_days: float,
        reason_text: Optional[str] = None,
        explanation: Optional[str] = None
    ) -> bool:
        """Send leave approved notification"""
        
        # Build reason section if employee provided one
        reason_section = ""
        if reason_text:
            reason_section = f"""
            <div class="reason-box">
                <h3>📝 Your Leave Reason</h3>
                <p>"{reason_text}"</p>
            </div>
            """
        
        # Build HR comment section if provided
        hr_comment = ""
        if explanation:
            hr_comment = f"""
            <div class="divider"></div>
            <p style="color: #059669; font-weight: 500;"><strong>💬 HR Comment:</strong> {explanation}</p>
            """
        
        content = f"""
            <h2>Leave Request Approved ✅</h2>
            <p>Dear {employee_name},</p>
            <p>We are pleased to inform you that your leave request has been <span class="status-badge status-approved">Approved</span></p>
            
            <div class="details">
                <div class="details-row">
                    <span class="details-label">Leave Type</span>
                    <span class="details-value">{leave_type}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Start Date</span>
                    <span class="details-value">{start_date}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">End Date</span>
                    <span class="details-value">{end_date}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Total Days</span>
                    <span class="details-value">{total_days} days</span>
                </div>
            </div>
            
            {reason_section}
            {hr_comment}
            
            <div class="divider"></div>
            <p style="color: #059669; font-weight: 500;">✨ Your leave has been recorded. Enjoy your time off!</p>
            <p style="color: #6b7280; font-size: 14px;">If you have any questions, please contact your HR representative.</p>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="✅ Leave Request Approved - LeaveAI Enterprise",
            html_content=self._get_base_template(content)
        )
    
    async def send_leave_rejected(
        self,
        to_email: str,
        employee_name: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        total_days: float,
        reason: str,
        employee_reason: Optional[str] = None
    ) -> bool:
        """Send leave rejected notification"""
        
        # Build employee's original reason section if available
        employee_reason_section = ""
        if employee_reason:
            employee_reason_section = f"""
            <div class="reason-box">
                <h3>📝 Your Leave Reason</h3>
                <p>"{employee_reason}"</p>
            </div>
            """
        
        content = f"""
            <h2>Leave Request Status Update</h2>
            <p>Dear {employee_name},</p>
            <p>We regret to inform you that your leave request has been <span class="status-badge status-rejected">Rejected</span></p>
            
            <div class="details">
                <div class="details-row">
                    <span class="details-label">Leave Type</span>
                    <span class="details-value">{leave_type}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Start Date</span>
                    <span class="details-value">{start_date}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">End Date</span>
                    <span class="details-value">{end_date}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Total Days</span>
                    <span class="details-value">{total_days} days</span>
                </div>
            </div>
            
            {employee_reason_section}
            
            <div class="rejection-reason">
                <h3>❌ Rejection Reason</h3>
                <p>{reason}</p>
            </div>
            
            <div class="divider"></div>
            <p style="color: #6b7280; font-size: 14px;">If you have questions about this decision or would like to discuss alternative dates, please contact your HR representative.</p>
            <p style="color: #6b7280; font-size: 14px;">You may submit a new leave request with different dates or circumstances.</p>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="❌ Leave Request Status Update - LeaveAI Enterprise",
            html_content=self._get_base_template(content)
        )
    
    async def send_leave_pending_review(
        self,
        to_email: str,
        employee_name: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        total_days: float,
        reason_text: Optional[str] = None
    ) -> bool:
        """Send leave pending review notification"""
        
        # Build reason section if employee provided one
        reason_section = ""
        if reason_text:
            reason_section = f"""
            <div class="reason-box">
                <h3>📝 Your Leave Reason</h3>
                <p>"{reason_text}"</p>
            </div>
            """
        
        content = f"""
            <h2>Leave Request Received</h2>
            <p>Dear {employee_name},</p>
            <p>Your leave request has been successfully submitted and is currently <span class="status-badge status-pending">Under Review</span></p>
            
            <div class="details">
                <div class="details-row">
                    <span class="details-label">Leave Type</span>
                    <span class="details-value">{leave_type}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Start Date</span>
                    <span class="details-value">{start_date}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">End Date</span>
                    <span class="details-value">{end_date}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Total Days</span>
                    <span class="details-value">{total_days} days</span>
                </div>
            </div>
            
            {reason_section}
            
            <div class="divider"></div>
            <p style="color: #92400e; font-weight: 500;">⏳ Your request is being reviewed by our HR team.</p>
            <p style="color: #6b7280; font-size: 14px;">You will receive a notification via email once a decision has been made. This typically takes 1-2 business days.</p>
            <p style="color: #6b7280; font-size: 14px;">You can track the status of your request by logging into the LeaveAI portal.</p>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject="📋 Leave Request Under Review - LeaveAI Enterprise",
            html_content=self._get_base_template(content)
        )
    
    async def send_hr_review_notification(
        self,
        to_email: str,
        hr_name: str,
        employee_name: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        total_days: float,
        request_number: str,
        ai_recommendation: Optional[str] = None,
        risk_level: Optional[str] = None
    ) -> bool:
        """Send notification to HR for manual review"""
        risk_badge = ""
        if risk_level == "HIGH":
            risk_badge = '<span style="background: #fee2e2; color: #dc2626; padding: 4px 8px; border-radius: 4px; font-size: 12px;">HIGH RISK</span>'
        elif risk_level == "MEDIUM":
            risk_badge = '<span style="background: #fef3c7; color: #d97706; padding: 4px 8px; border-radius: 4px; font-size: 12px;">MEDIUM RISK</span>'
        
        content = f"""
            <h2>Leave Request Requires Review 📋</h2>
            <p>Hi {hr_name},</p>
            <p>A leave request requires your review. {risk_badge}</p>
            
            <div class="details">
                <div class="details-row">
                    <span class="details-label">Request Number</span>
                    <span class="details-value">{request_number}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Employee</span>
                    <span class="details-value">{employee_name}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Leave Type</span>
                    <span class="details-value">{leave_type}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Dates</span>
                    <span class="details-value">{start_date} - {end_date}</span>
                </div>
                <div class="details-row">
                    <span class="details-label">Total Days</span>
                    <span class="details-value">{total_days} days</span>
                </div>
                {f'''<div class="details-row">
                    <span class="details-label">AI Recommendation</span>
                    <span class="details-value">{ai_recommendation}</span>
                </div>''' if ai_recommendation else ''}
            </div>
            
            <p style="text-align: center;">
                <a href="#" class="button">Review Request</a>
            </p>
        """
        
        return await self.send_email(
            to_email=to_email,
            subject=f"📋 Leave Request Needs Review - {request_number}",
            html_content=self._get_base_template(content)
        )


# Singleton instance
email_service = EmailService()
