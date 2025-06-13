from typing import List, Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class EmailConfig(BaseModel):
    """Email server configuration"""
    smtp_server: str = Field(..., description="SMTP 伺服器地址")
    smtp_port: int = Field(default=587, description="SMTP 連接埠 (25, 587, 465)")
    username: str = Field(..., description="郵件帳號")
    password: str = Field(..., description="郵件密碼")
    use_tls: bool = Field(default=True, description="是否使用 TLS/SSL 加密")
    
    class Config:
        schema_extra = {
            "example": {
                "smtp_server": "dragon.nchu.edu.tw",
                "smtp_port": 465,
                "username": "your-username@dragon.nchu.edu.tw",
                "password": "your-password",
                "use_tls": True
            }
        }


class EmailRecipient(BaseModel):
    """Email recipient information"""
    email: EmailStr
    name: Optional[str] = None


class EmailContent(BaseModel):
    """Email content"""
    subject: str
    body: str
    html_body: Optional[str] = None


class SendEmailRequest(BaseModel):
    """Request model for sending email"""
    email_config: EmailConfig
    sender_name: Optional[str] = None
    recipients: List[EmailRecipient]
    content: EmailContent


class SendEmailResponse(BaseModel):
    """Response model for email sending"""
    success: bool
    message: str
    sent_count: int
    failed_recipients: Optional[List[str]] = None

    model_config = ConfigDict(from_attributes=True)


class SendWinnersEmailRequest(BaseModel):
    """Request model for sending winner notification emails"""
    email_config: EmailConfig
    sender_name: Optional[str] = "抽獎系統"
    subject: Optional[str] = "恭喜您中獎了！"
    email_template: Optional[str] = None
    html_template: Optional[str] = None


class BulkEmailRequest(BaseModel):
    """Request model for bulk email sending"""
    email_config: EmailConfig
    sender_name: Optional[str] = None
    subject: str
    body: str
    html_body: Optional[str] = None
    recipient_emails: List[EmailStr] 