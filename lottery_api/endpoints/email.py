from fastapi import APIRouter, Depends, status, HTTPException
from typing import Dict, Any

from lottery_api.data_access_object.db import get_db_connection
from lottery_api.business_model.email_business import EmailBusiness
from lottery_api.lib.response import ExceptionResponse, SingleResponse, to_json_response
from lottery_api.schema.email import (
    SendEmailRequest, SendEmailResponse, BulkEmailRequest,
    SendWinnersEmailRequest, EmailConfig
)

router = APIRouter(prefix="/email", tags=["email"])


@router.post("/send", response_model=SingleResponse[SendEmailResponse], status_code=status.HTTP_200_OK)
async def send_email(
    request: SendEmailRequest
):
    """發送郵件給指定收件人"""
    result = await EmailBusiness.send_email(
        email_config=request.email_config,
        sender_name=request.sender_name,
        recipients=request.recipients,
        content=request.content
    )
    return to_json_response(SingleResponse(result=result))


@router.post("/send-bulk", response_model=SingleResponse[SendEmailResponse], status_code=status.HTTP_200_OK)
async def send_bulk_email(
    request: BulkEmailRequest
):
    """批量發送郵件給多個收件人"""
    result = await EmailBusiness.send_bulk_email(
        email_config=request.email_config,
        sender_name=request.sender_name,
        subject=request.subject,
        body=request.body,
        html_body=request.html_body,
        recipient_emails=request.recipient_emails
    )
    return to_json_response(SingleResponse(result=result))


@router.post("/send-winners/{event_id}", response_model=SingleResponse[SendEmailResponse],
             responses={
                 404: {'model': ExceptionResponse},
                 400: {'model': ExceptionResponse}
             })
async def send_winners_notification(
    event_id: str,
    request: SendWinnersEmailRequest,
    conn=Depends(get_db_connection)
):
    """發送中獎通知郵件給抽獎活動的中獎者"""
    result = await EmailBusiness.send_winners_notification(
        conn=conn,
        event_id=event_id,
        email_config=request.email_config,
        sender_name=request.sender_name,
        subject=request.subject,
        email_template=request.email_template,
        html_template=request.html_template
    )
    return to_json_response(SingleResponse(result=result))


@router.post("/test-connection", response_model=SingleResponse[Dict[str, Any]], status_code=status.HTTP_200_OK)
async def test_email_connection(
    email_config: EmailConfig
):
    """測試郵件伺服器連接"""
    result = EmailBusiness.test_email_connection(email_config)
    return to_json_response(SingleResponse(result=result))


@router.get("/template-variables", response_model=SingleResponse[Dict[str, Any]])
async def get_template_variables():
    """取得郵件模板可用的變數列表"""
    variables = {
        "available_variables": {
            "winner_name": {
                "description": "中獎者姓名",
                "example": "王小明",
                "usage": "{{winner_name}}"
            },
            "event_name": {
                "description": "抽獎活動名稱",
                "example": "期末學生活動抽獎",
                "usage": "{{event_name}}"
            },
            "event_date": {
                "description": "活動日期",
                "example": "2024-01-15",
                "usage": "{{event_date}}"
            },
            "prize_name": {
                "description": "獎項名稱",
                "example": "頭獎 - iPad Pro",
                "usage": "{{prize_name}}"
            },
            "sender_name": {
                "description": "寄件者名稱",
                "example": "抽獎系統",
                "usage": "{{sender_name}}"
            },
            "student_id": {
                "description": "學號",
                "example": "s1234567",
                "usage": "{{student_id}}"
            },
            "department": {
                "description": "系所",
                "example": "資訊工程學系",
                "usage": "{{department}}"
            },
            "grade": {
                "description": "年級",
                "example": "大三",
                "usage": "{{grade}}"
            },
            "phone": {
                "description": "電話號碼",
                "example": "0912345678",
                "usage": "{{phone}}"
            },
            "email": {
                "description": "電子郵件",
                "example": "student@example.com",
                "usage": "{{email}}"
            }
        },
        "usage_notes": [
            "使用雙大括號 {{variable_name}} 來標記變數",
            "變數名稱區分大小寫",
            "如果中獎者資料中沒有某個欄位，會顯示 '未提供'",
            "可以在主旨、文字內容和 HTML 內容中使用變數",
            "HTML 模板中請確保正確的 HTML 語法"
        ],
        "example_templates": {
            "simple_text": """親愛的 {{winner_name}}，

恭喜您在「{{event_name}}」中獲得「{{prize_name}}」！

請聯絡我們領取獎品。

{{sender_name}}""",
            "detailed_text": """親愛的 {{winner_name}} 同學，

恭喜您在「{{event_name}}」抽獎活動中獲得「{{prize_name}}」！

中獎者資訊：
- 姓名：{{winner_name}}
- 學號：{{student_id}}
- 系所：{{department}}
- 年級：{{grade}}
- 聯絡電話：{{phone}}

活動資訊：
- 活動名稱：{{event_name}}
- 活動日期：{{event_date}}

請依照相關規定領取您的獎品。

祝您學業進步！

{{sender_name}}""",
            "simple_html": """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>中獎通知</title>
</head>
<body>
    <h2>🎉 恭喜中獎！</h2>
    <p>親愛的 <strong>{{winner_name}}</strong>，</p>
    <p>恭喜您在「{{event_name}}」中獲得「<span style="color: red;">{{prize_name}}</span>」！</p>
    <p>請聯絡我們領取獎品。</p>
    <p>{{sender_name}}</p>
</body>
</html>"""
        }
    }
    return to_json_response(SingleResponse(result=variables))


@router.get("/smtp-settings-example", response_model=SingleResponse[Dict[str, Any]])
async def get_smtp_settings_example():
    """取得常見郵件服務商的 SMTP 設定範例"""
    examples = {
        "nchu_secure": {
            "smtp_server": "dragon.nchu.edu.tw",
            "smtp_port": 465,
            "use_tls": True,
            "note": "中興大學安全連線 (SMTPs)，建議使用此設定",
            "example_username": "username@dragon.nchu.edu.tw"
        },
        "nchu_plain": {
            "smtp_server": "dragon.nchu.edu.tw",
            "smtp_port": 25,
            "use_tls": False,
            "note": "中興大學一般連線 (不建議使用，安全性較低)",
            "example_username": "username@dragon.nchu.edu.tw"
        },
        "gmail": {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "use_tls": True,
            "note": "需要使用應用程式密碼，不能使用一般密碼"
        },
        "outlook": {
            "smtp_server": "smtp-mail.outlook.com",
            "smtp_port": 587,
            "use_tls": True,
            "note": "支援 Outlook.com, Hotmail.com 等微軟郵件服務"
        },
        "yahoo": {
            "smtp_server": "smtp.mail.yahoo.com",
            "smtp_port": 587,
            "use_tls": True,
            "note": "需要開啟應用程式密碼功能"
        },
        "custom": {
            "smtp_server": "your-smtp-server.com",
            "smtp_port": 587,
            "use_tls": True,
            "note": "請聯絡您的郵件服務提供商取得正確設定"
        }
    }
    return to_json_response(SingleResponse(result=examples)) 