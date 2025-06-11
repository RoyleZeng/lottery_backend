import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any, Optional
import logging
import socket

from lottery_api.schema.email import EmailConfig, EmailRecipient, EmailContent, SendEmailResponse
from lottery_api.business_model.lottery_business import LotteryBusiness
from lottery_api.lib.base_exception import ParameterViolationException

logger = logging.getLogger(__name__)


class EmailBusiness:
    """Business logic for email operations"""

    @staticmethod
    def _create_smtp_connection(email_config: EmailConfig):
        """Create SMTP connection with the provided configuration"""
        try:
            # Set socket timeout to 30 seconds
            socket.setdefaulttimeout(30)

            # Create SMTP connection based on port and TLS settings
            if email_config.smtp_port == 465:
                # Use SMTP_SSL for port 465 (implicit SSL)
                context = ssl.create_default_context()
                server = smtplib.SMTP_SSL(email_config.smtp_server, email_config.smtp_port, context=context, timeout=30)
                logger.info(f"Created SMTP_SSL connection to {email_config.smtp_server}:{email_config.smtp_port}")
            elif email_config.use_tls and email_config.smtp_port == 587:
                # Use STARTTLS for port 587
                context = ssl.create_default_context()
                server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port, timeout=30)
                server.starttls(context=context)
                logger.info(
                    f"Created SMTP connection with STARTTLS to {email_config.smtp_server}:{email_config.smtp_port}")
            else:
                # Plain SMTP connection (not recommended)
                server = smtplib.SMTP(email_config.smtp_server, email_config.smtp_port, timeout=30)
                logger.info(f"Created plain SMTP connection to {email_config.smtp_server}:{email_config.smtp_port}")

            # Enable debug output for troubleshooting
            server.set_debuglevel(1)

            # Login to the server
            server.login(email_config.username, email_config.password)
            logger.info(f"Successfully logged in as {email_config.username}")

            return server
        except socket.timeout:
            logger.error(f"Connection timeout to {email_config.smtp_server}:{email_config.smtp_port}")
            raise ParameterViolationException(
                f"連接郵件伺服器超時: {email_config.smtp_server}:{email_config.smtp_port}")
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP authentication failed: {str(e)}")
            raise ParameterViolationException(f"郵件伺服器認證失敗: {str(e)}")
        except smtplib.SMTPConnectError as e:
            logger.error(f"SMTP connection failed: {str(e)}")
            raise ParameterViolationException(f"無法連接到郵件伺服器: {str(e)}")
        except Exception as e:
            logger.error(f"Failed to create SMTP connection: {str(e)}")
            raise ParameterViolationException(f"郵件伺服器連接失敗: {str(e)}")

    @staticmethod
    def _create_email_message(
            sender_email: str,
            sender_name: str,
            recipient: EmailRecipient,
            content: EmailContent
    ) -> MIMEMultipart:
        """Create email message"""
        message = MIMEMultipart("alternative")
        message["Subject"] = content.subject
        message["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
        message["To"] = f"{recipient.name} <{recipient.email}>" if recipient.name else recipient.email

        # Add plain text part
        text_part = MIMEText(content.body, "plain", "utf-8")
        message.attach(text_part)

        # Add HTML part if provided
        if content.html_body:
            html_part = MIMEText(content.html_body, "html", "utf-8")
            message.attach(html_part)

        return message

    @staticmethod
    async def send_email(
            email_config: EmailConfig,
            sender_name: str,
            recipients: List[EmailRecipient],
            content: EmailContent
    ) -> Optional[SendEmailResponse]:
        """Send email to multiple recipients"""
        failed_recipients = []
        sent_count = 0

        try:
            # Create SMTP connection
            server = EmailBusiness._create_smtp_connection(email_config)

            for recipient in recipients:
                try:
                    # Create email message
                    message = EmailBusiness._create_email_message(
                        email_config.username,
                        sender_name or "系統通知",
                        recipient,
                        content
                    )

                    # Send email
                    server.send_message(message)
                    sent_count += 1
                    logger.info(f"Email sent successfully to {recipient.email}")

                except Exception as e:
                    logger.error(f"Failed to send email to {recipient.email}: {str(e)}")
                    failed_recipients.append(recipient.email)


        except Exception as e:
            logger.error(f"SMTP connection error: {str(e)}")
            return SendEmailResponse(
                success=False,
                message=f"郵件伺服器連接失敗: {str(e)}",
                sent_count=0,
                failed_recipients=[r.email for r in recipients]
            )

        success = sent_count > 0
        message = f"成功發送 {sent_count} 封郵件"
        if failed_recipients:
            message += f"，{len(failed_recipients)} 封發送失敗"

        return SendEmailResponse(
            success=success,
            message=message,
            sent_count=sent_count,
            failed_recipients=failed_recipients if failed_recipients else None
        )

    @staticmethod
    async def send_bulk_email(
            email_config: EmailConfig,
            sender_name: str,
            subject: str,
            body: str,
            html_body: str,
            recipient_emails: List[str]
    ) -> SendEmailResponse:
        """Send bulk email to multiple email addresses"""
        recipients = [EmailRecipient(email=email) for email in recipient_emails]
        content = EmailContent(subject=subject, body=body, html_body=html_body)

        return await EmailBusiness.send_email(email_config, sender_name, recipients, content)

    @staticmethod
    async def send_winners_notification(
            conn,
            event_id: str,
            email_config: EmailConfig,
            sender_name: str = "抽獎系統",
            subject: str = "恭喜您中獎了！",
            email_template: str = None,
            html_template: str = None
    ) -> Optional[SendEmailResponse]:
        """Send notification emails to lottery winners with template variable substitution"""
        # Get winners for the event
        winners = await LotteryBusiness.get_winners(conn, event_id)

        if not winners:
            raise ParameterViolationException("此抽獎活動沒有中獎者")

        # Get event details
        event = await LotteryBusiness.get_lottery_event(conn, event_id)

        # Prepare recipients list (assuming winners have email in their data)
        recipients = []
        for prize_group in winners:
            for winner in prize_group["winners"]:
                # Note: This assumes email is stored in winner data
                # You may need to modify this based on your actual data structure
                if "email" in winner and winner["email"]:
                    recipients.append(EmailRecipient(
                        email=winner["email"],
                        name=winner.get("name", "")
                    ))

        if not recipients:
            raise ParameterViolationException("中獎者資料中沒有找到有效的電子郵件地址")

        # Default text template if not provided
        if not email_template:
            email_template = """親愛的 {{winner_name}}，

恭喜您在「{{event_name}}」抽獎活動中獲得「{{prize_name}}」！

活動詳情：
- 活動名稱：{{event_name}}
- 活動日期：{{event_date}}
- 獲得獎項：{{prize_name}}
- 中獎者姓名：{{winner_name}}
- 學號：{{student_id}}
- 系所：{{department}}
- 年級：{{grade}}

請依照相關規定領取您的獎品。

祝您
身體健康，學業進步！

{{sender_name}}"""

        # Default HTML template if not provided
        if not html_template:
            html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>中獎通知</title>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background-color: #f8f9fa; padding: 20px; text-align: center; border-radius: 8px; }
        .content { padding: 20px 0; }
        .prize-info { background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .winner-info { background-color: #f0f8ff; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .footer { text-align: center; color: #666; font-size: 14px; margin-top: 30px; }
        .highlight { color: #d63384; font-weight: bold; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎉 恭喜中獎！🎉</h1>
        </div>
        
        <div class="content">
            <p>親愛的 <strong>{{winner_name}}</strong>，</p>
            
            <p>恭喜您在「<span class="highlight">{{event_name}}</span>」抽獎活動中獲得獎項！</p>
            
            <div class="prize-info">
                <h3>🏆 獲得獎項</h3>
                <p><strong>{{prize_name}}</strong></p>
            </div>
            
            <div class="winner-info">
                <h3>👤 中獎者資訊</h3>
                <ul>
                    <li><strong>姓名：</strong>{{winner_name}}</li>
                    <li><strong>學號：</strong>{{student_id}}</li>
                    <li><strong>系所：</strong>{{department}}</li>
                    <li><strong>年級：</strong>{{grade}}</li>
                </ul>
            </div>
            
            <div class="prize-info">
                <h3>📅 活動資訊</h3>
                <ul>
                    <li><strong>活動名稱：</strong>{{event_name}}</li>
                    <li><strong>活動日期：</strong>{{event_date}}</li>
                </ul>
            </div>
            
            <p>請依照相關規定領取您的獎品。</p>
            
            <p>祝您<br>
            身體健康，學業進步！</p>
        </div>
        
        <div class="footer">
            <p>{{sender_name}}</p>
        </div>
    </div>
</body>
</html>"""

        # Send personalized emails to each winner
        failed_recipients = []
        sent_count = 0

        try:
            server = EmailBusiness._create_smtp_connection(email_config)

            try:
                for prize_group in winners:
                    prize_name = prize_group["prize_name"]
                    for winner in prize_group["winners"]:
                        if "email" in winner and winner["email"]:
                            try:
                                # Prepare template variables
                                template_vars = {
                                    'winner_name': winner.get("name", "同學"),
                                    'event_name': event["name"],
                                    'event_date': event["event_date"].strftime("%Y-%m-%d") if event.get("event_date") else "未指定",
                                    'prize_name': prize_name,
                                    'sender_name': sender_name,
                                    'student_id': winner.get("student_id", "未提供"),
                                    'department': winner.get("department", "未提供"),
                                    'grade': winner.get("grade", "未提供"),
                                    'phone': winner.get("phone", "未提供"),
                                    'email': winner.get("email", ""),
                                }

                                # Replace template variables using double curly braces {{variable}}
                                personalized_body = EmailBusiness._replace_template_variables(email_template, template_vars)
                                personalized_html = EmailBusiness._replace_template_variables(html_template, template_vars) if html_template else None

                                content = EmailContent(
                                    subject=EmailBusiness._replace_template_variables(subject, template_vars),
                                    body=personalized_body,
                                    html_body=personalized_html
                                )

                                recipient = EmailRecipient(
                                    email=winner["email"],
                                    name=winner.get("name", "")
                                )

                                message = EmailBusiness._create_email_message(
                                    email_config.username,
                                    sender_name,
                                    recipient,
                                    content
                                )

                                server.send_message(message)
                                sent_count += 1
                                logger.info(f"Winner notification sent to {winner['email']}")

                            except Exception as e:
                                logger.error(f"Failed to send winner notification to {winner['email']}: {str(e)}")
                                failed_recipients.append(winner["email"])

            finally:
                server.quit()

        except Exception as e:
            logger.error(f"SMTP connection error: {str(e)}")
            return SendEmailResponse(
                success=False,
                message=f"郵件伺服器連接失敗: {str(e)}",
                sent_count=0,
                failed_recipients=[r.email for r in recipients]
            )

        success = sent_count > 0
        message = f"成功發送 {sent_count} 封中獎通知郵件"
        if failed_recipients:
            message += f"，{len(failed_recipients)} 封發送失敗"

        return SendEmailResponse(
            success=success,
            message=message,
            sent_count=sent_count,
            failed_recipients=failed_recipients if failed_recipients else None
        )

    @staticmethod
    def _replace_template_variables(template: str, variables: dict) -> str:
        """Replace template variables in the format {{variable_name}} with actual values"""
        if not template:
            return template
            
        result = template
        for key, value in variables.items():
            # Replace {{key}} with value
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        
        return result

    @staticmethod
    def test_email_connection(email_config: EmailConfig) -> Dict[str, Any]:
        """Test email server connection"""
        try:
            server = EmailBusiness._create_smtp_connection(email_config)
            server.quit()
            return {
                "success": True,
                "message": "郵件伺服器連接測試成功"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"郵件伺服器連接測試失敗: {str(e)}"
            }
