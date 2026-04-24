"""Email service for sending emails."""
from flask import current_app
from flask_mail import Message
import os


class EmailService:
    """Service for sending emails."""

    @staticmethod
    def send_password_reset_email(email, username, reset_token):
        """
        Send password reset email to user.

        Args:
            email: Recipient email address
            username: Admin username
            reset_token: Password reset token

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            # Import mail here to avoid circular import
            from app import mail

            frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')
            sender = os.getenv('MAIL_DEFAULT_SENDER') or os.getenv('MAIL_USERNAME')

            if not sender:
                current_app.logger.error(
                    "No email sender configured. Set MAIL_DEFAULT_SENDER or MAIL_USERNAME in .env"
                )
                return False

            reset_link = f"{frontend_url}/reset-password?token={reset_token}"
            subject = "FitCore - Password Reset Request"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #EDEDED;
                        background-color: #0B0B0B;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #1A1A1A;
                        border-radius: 10px;
                    }}
                    .header {{
                        text-align: center;
                        padding: 20px 0;
                        border-bottom: 2px solid #B6FF00;
                    }}
                    .logo {{
                        font-size: 32px;
                        font-weight: bold;
                        color: #B6FF00;
                    }}
                    .content {{
                        padding: 30px 20px;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 14px 36px;
                        background-color: #B6FF00;
                        color: #0B0B0B;
                        text-decoration: none;
                        border-radius: 8px;
                        font-weight: bold;
                        font-size: 16px;
                        margin: 20px 0;
                    }}
                    .footer {{
                        text-align: center;
                        padding: 20px;
                        color: #EDEDED;
                        opacity: 0.6;
                        font-size: 12px;
                        border-top: 1px solid #333;
                    }}
                    .warning {{
                        background-color: #2A2A2A;
                        padding: 15px;
                        border-left: 4px solid #B6FF00;
                        margin: 20px 0;
                        border-radius: 4px;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <div class="logo">FitCore</div>
                        <p style="color:#EDEDED;opacity:0.7;margin:4px 0 0;">Gym Management System</p>
                    </div>
                    <div class="content">
                        <h2 style="color: #B6FF00;">Password Reset Request</h2>
                        <p>Hi <strong>{username}</strong>,</p>
                        <p>We received a request to reset your FitCore admin password. Click the button below to set a new password:</p>
                        <div style="text-align: center;">
                            <a href="{reset_link}" class="button">Reset My Password</a>
                        </div>
                        <div class="warning">
                            <strong>Security Notice:</strong>
                            <ul style="margin:8px 0 0; padding-left:20px;">
                                <li>This link expires in <strong>24 hours</strong></li>
                                <li>If you did not request this, ignore this email</li>
                                <li>Never share this link with anyone</li>
                            </ul>
                        </div>
                        <p style="font-size:13px;color:#aaa;">Or copy and paste this link into your browser:</p>
                        <p style="word-break: break-all; color: #B6FF00; font-size:13px;">{reset_link}</p>
                    </div>
                    <div class="footer">
                        <p>© 2026 FitCore Gym Management System &mdash; Karachi, Pakistan</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""FitCore - Password Reset Request

Hi {username},

We received a request to reset your FitCore admin password.

Reset link (expires in 24 hours):
{reset_link}

If you did not request this, please ignore this email.

© 2026 FitCore Gym Management System
"""

            msg = Message(
                subject=subject,
                sender=sender,
                recipients=[email],
                body=text_body,
                html=html_body
            )

            mail.send(msg)
            current_app.logger.info(f"Password reset email sent to {email}")
            return True

        except Exception as e:
            current_app.logger.error(f"Failed to send password reset email: {str(e)}")
            return False
