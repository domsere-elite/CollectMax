import os
import logging
from typing import Optional, Dict, Any
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)


class CommsManager:
    def __init__(self, db_cursor=None):
        """
        Initialize communications manager with SendGrid integration.
        
        Args:
            db_cursor: Optional database cursor for email logging
        """
        self.sendgrid_api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("SENDGRID_FROM_EMAIL", "noreply@collectmax.com")
        self.from_name = os.getenv("SENDGRID_FROM_NAME", "CollectMax")
        self.cursor = db_cursor
        
        if self.sendgrid_api_key and self.sendgrid_api_key != "your_sendgrid_api_key_here":
            self.sg = SendGridAPIClient(self.sendgrid_api_key)
        else:
            self.sg = None
            logger.warning("SendGrid API key not configured. Email sending disabled.")

    def send_email(
        self, 
        to_email: str, 
        subject: str, 
        html_content: str,
        debt_id: Optional[int] = None,
        template_id: Optional[str] = None,
        dynamic_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Send an email via SendGrid.
        
        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML email body
            debt_id: Optional debt ID for logging
            template_id: Optional SendGrid template ID
            dynamic_data: Optional dynamic template data
            
        Returns:
            dict with 'success', 'message_id', and 'status_code'
        """
        if not self.sg:
            logger.error("SendGrid not configured. Cannot send email.")
            return {
                "success": False,
                "error": "SendGrid not configured",
                "message_id": None
            }
        
        try:
            # Use dynamic template if provided
            if template_id and dynamic_data:
                # When using dynamic templates, SendGrid ignores subject and html_content
                # The template defines these, so we only pass the dynamic data
                message = Mail(
                    from_email=Email(self.from_email, self.from_name),
                    to_emails=To(to_email)
                )
                message.template_id = template_id
                message.dynamic_template_data = dynamic_data
                
                logger.info(f"Sending email with template {template_id} to {to_email}")
                logger.debug(f"Dynamic data keys: {list(dynamic_data.keys())}")
            else:
                # Standard email without template
                message = Mail(
                    from_email=Email(self.from_email, self.from_name),
                    to_emails=To(to_email),
                    subject=subject,
                    html_content=Content("text/html", html_content)
                )
                
                logger.info(f"Sending standard email to {to_email}")
            
            response = self.sg.send(message)
            
            # Extract SendGrid message ID from headers
            message_id = response.headers.get('X-Message-Id')
            
            # Log email to database if cursor provided
            if self.cursor and debt_id:
                self._log_email(
                    debt_id=debt_id,
                    recipient_email=to_email,
                    subject=subject,
                    template_id=template_id,
                    sendgrid_message_id=message_id,
                    status='sent'
                )
            
            logger.info(f"Email sent successfully to {to_email}. Message ID: {message_id}")
            
            return {
                "success": True,
                "message_id": message_id,
                "status_code": response.status_code
            }
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            
            # Log failed attempt if cursor provided
            if self.cursor and debt_id:
                self._log_email(
                    debt_id=debt_id,
                    recipient_email=to_email,
                    subject=subject,
                    template_id=template_id,
                    sendgrid_message_id=None,
                    status='failed',
                    error_message=str(e)
                )
            
            return {
                "success": False,
                "error": str(e),
                "message_id": None
            }

    def send_validation_notice(self, debtor_email: str, pdf_url: str, debt_id: Optional[int] = None):
        """
        Sends the FDCPA validation notice via SendGrid.
        
        Args:
            debtor_email: Debtor's email address
            pdf_url: URL to the validation notice PDF
            debt_id: Optional debt ID for logging
        """
        subject = "Debt Validation Notice - Action Required"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>Debt Validation Notice</h2>
                <p>This is an attempt to collect a debt. Any information obtained will be used for that purpose.</p>
                <p>You have the right to dispute this debt. Please review your validation notice:</p>
                <p style="margin: 20px 0;">
                    <a href="{pdf_url}" 
                       style="background-color: #007bff; color: white; padding: 12px 24px; 
                              text-decoration: none; border-radius: 4px; display: inline-block;">
                        View Validation Notice
                    </a>
                </p>
                <p style="font-size: 12px; color: #666; margin-top: 30px;">
                    This is a communication from a debt collector.
                </p>
            </body>
        </html>
        """
        
        return self.send_email(
            to_email=debtor_email,
            subject=subject,
            html_content=html_content,
            debt_id=debt_id
        )

    def send_payment_confirmation(
        self, 
        debtor_email: str, 
        amount: float, 
        reference_number: str,
        debt_id: Optional[int] = None
    ):
        """
        Sends a payment confirmation email.
        
        Args:
            debtor_email: Debtor's email address
            amount: Payment amount
            reference_number: Transaction reference number
            debt_id: Optional debt ID for logging
        """
        subject = "Payment Confirmation"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <h2>Payment Received</h2>
                <p>Thank you for your payment. We have successfully processed your payment.</p>
                <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <p><strong>Amount Paid:</strong> ${amount:.2f}</p>
                    <p><strong>Reference Number:</strong> {reference_number}</p>
                    <p><strong>Date:</strong> {self._get_current_date()}</p>
                </div>
                <p>Please keep this confirmation for your records.</p>
            </body>
        </html>
        """
        
        return self.send_email(
            to_email=debtor_email,
            subject=subject,
            html_content=html_content,
            debt_id=debt_id
        )

    def _log_email(
        self,
        debt_id: int,
        recipient_email: str,
        subject: str,
        template_id: Optional[str],
        sendgrid_message_id: Optional[str],
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Log email send attempt to database.
        
        Args:
            debt_id: Debt ID
            recipient_email: Recipient email address
            subject: Email subject
            template_id: SendGrid template ID if used
            sendgrid_message_id: SendGrid message ID
            status: 'sent' or 'failed'
            error_message: Error message if failed
        """
        try:
            # Get debtor_id from debt_id
            self.cursor.execute("""
                SELECT debtor_id FROM debts WHERE id = %s
            """, (debt_id,))
            result = self.cursor.fetchone()
            debtor_id = result['debtor_id'] if result else None
            
            self.cursor.execute("""
                INSERT INTO email_logs (
                    debt_id, debtor_id, email_to, email_from, subject, 
                    template_id, sendgrid_message_id, status, error_message
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                debt_id, debtor_id, recipient_email, self.from_email, 
                subject, template_id, sendgrid_message_id, status, error_message
            ))
        except Exception as e:
            logger.error(f"Failed to log email to database: {str(e)}")

    def _get_current_date(self) -> str:
        """Get current date formatted for emails."""
        from datetime import datetime
        return datetime.now().strftime("%B %d, %Y")

    def send_sms(self, phone: str, message: str):
        """
        Stub for Solutions By Text (SBT) integration.
        TODO: Implement SMS provider integration
        """
        logger.info(f"[SolutionsByText] SMS to {phone}: '{message}'")
        return True

    def dial_debtor(self, phone: str):
        """
        Stub for TCN Dialing integration.
        TODO: Implement dialer integration
        """
        logger.info(f"[TCN] Dialing request initiated for {phone}")
        return {"call_id": "mock_call_123"}
