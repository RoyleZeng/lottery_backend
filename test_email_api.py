#!/usr/bin/env python3
"""
Email API 測試腳本
使用前請先修改郵件設定
"""

import requests
import json

BASE_URL = "http://localhost:8000"

# 中興大學郵件設定範例 (請修改為您的實際設定)
EMAIL_CONFIG = {
    "smtp_server": "dragon.nchu.edu.tw",
    "smtp_port": 465,  # 使用安全連線 SMTPs
    "username": "your-username@dragon.nchu.edu.tw",  # 請修改
    "password": "your-password",                     # 請修改
    "use_tls": True
}

def test_smtp_settings():
    """取得 SMTP 設定範例"""
    response = requests.get(f"{BASE_URL}/email/smtp-settings-example")
    print("SMTP 設定範例:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_connection():
    """測試郵件伺服器連接"""
    response = requests.post(f"{BASE_URL}/email/test-connection", json=EMAIL_CONFIG)
    print("連接測試結果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def send_test_email():
    """發送測試郵件"""
    email_request = {
        "email_config": EMAIL_CONFIG,
        "sender_name": "抽獎系統測試",
        "recipients": [
            {
                "email": "recipient@example.com",  # 請修改
                "name": "測試收件人"
            }
        ],
        "content": {
            "subject": "測試郵件",
            "body": "這是一封測試郵件。"
        }
    }
    
    response = requests.post(f"{BASE_URL}/email/send", json=email_request)
    print("發送郵件結果:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def test_template_variables():
    """取得模板變數列表"""
    response = requests.get(f"{BASE_URL}/email/template-variables")
    print("模板變數列表:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

def send_winners_notification_with_custom_template():
    """發送中獎通知郵件（使用自定義模板）"""
    
    # 自定義文字模板
    custom_text_template = """親愛的 {{winner_name}} 同學，

🎉 恭喜您中獎了！🎉

您在「{{event_name}}」抽獎活動中獲得了「{{prize_name}}」！

📋 中獎者資訊：
• 姓名：{{winner_name}}
• 學號：{{student_id}}
• 系所：{{department}}
• 年級：{{grade}}

📅 活動資訊：
• 活動名稱：{{event_name}}
• 活動日期：{{event_date}}

請盡快聯絡我們領取您的獎品！

祝您學業進步！
{{sender_name}}"""

    # 自定義 HTML 模板
    custom_html_template = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>🎉 中獎通知 - {{event_name}}</title>
    <style>
        body { 
            font-family: 'Microsoft JhengHei', Arial, sans-serif; 
            line-height: 1.8; 
            color: #333; 
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .email-container { 
            max-width: 600px; 
            margin: 0 auto; 
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px 20px; 
            text-align: center; 
        }
        .header h1 {
            margin: 0;
            font-size: 28px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .content { 
            padding: 30px; 
        }
        .congratulations {
            background: linear-gradient(135deg, #ffeaa7 0%, #fab1a0 100%);
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            margin: 20px 0;
            border-left: 5px solid #e17055;
        }
        .prize-section { 
            background-color: #e8f5e8; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 5px solid #00b894;
        }
        .winner-info { 
            background-color: #f0f8ff; 
            padding: 20px; 
            border-radius: 8px; 
            margin: 20px 0;
            border-left: 5px solid #74b9ff;
        }
                 .event-info {
             background-color: #fff5f5;
             padding: 20px;
             border-radius: 8px;
             margin: 20px 0;
             border-left: 5px solid #fd79a8;
         }
         .info-list {
             list-style: none;
             padding: 0;
         }
         .info-list li {
             padding: 8px 0;
             border-bottom: 1px solid #eee;
         }
         .info-list li:last-child {
             border-bottom: none;
         }
         .label {
             font-weight: bold;
             color: #2d3436;
             display: inline-block;
             width: 80px;
         }
         .value {
             color: #636e72;
         }
         .footer { 
             text-align: center; 
             color: #666; 
             font-size: 14px; 
             margin-top: 30px;
             padding-top: 20px;
             border-top: 2px solid #ddd;
         }
         .highlight { 
             color: #e17055; 
             font-weight: bold; 
             font-size: 1.1em;
         }
         .emoji {
             font-size: 1.2em;
         }
     </style>
 </head>
 <body>
     <div class="email-container">
         <div class="header">
             <h1><span class="emoji">🎉</span> 中獎通知 <span class="emoji">🎉</span></h1>
             <p>{{event_name}}</p>
         </div>
         
         <div class="content">
             <div class="congratulations">
                 <h2 style="margin: 0; color: #2d3436;">恭喜 {{winner_name}} 同學中獎！</h2>
             </div>
             
             <p style="font-size: 16px; text-align: center; margin: 25px 0;">
                 恭喜您在「<span class="highlight">{{event_name}}</span>」抽獎活動中脫穎而出！
             </p>
             
             <div class="prize-section">
                 <h3 style="margin-top: 0; color: #00b894;"><span class="emoji">🏆</span> 獲得獎項</h3>
                 <p style="font-size: 18px; font-weight: bold; color: #2d3436; text-align: center; margin: 15px 0;">
                     {{prize_name}}
                 </p>
             </div>
             
             <div class="winner-info">
                 <h3 style="margin-top: 0; color: #74b9ff;"><span class="emoji">👤</span> 中獎者資訊</h3>
                 <ul class="info-list">
                     <li><span class="label">姓名：</span><span class="value">{{winner_name}}</span></li>
                     <li><span class="label">學號：</span><span class="value">{{student_id}}</span></li>
                     <li><span class="label">系所：</span><span class="value">{{department}}</span></li>
                     <li><span class="label">年級：</span><span class="value">{{grade}}</span></li>
                     <li><span class="label">電話：</span><span class="value">{{phone}}</span></li>
                 </ul>
             </div>
             
             <div class="event-info">
                 <h3 style="margin-top: 0; color: #fd79a8;"><span class="emoji">📅</span> 活動資訊</h3>
                 <ul class="info-list">
                     <li><span class="label">活動名稱：</span><span class="value">{{event_name}}</span></li>
                     <li><span class="label">活動日期：</span><span class="value">{{event_date}}</span></li>
                 </ul>
             </div>
             
             <div style="background-color: #fff3cd; padding: 15px; border-radius: 5px; border-left: 5px solid #ffc107; margin: 20px 0;">
                 <p style="margin: 0; color: #856404;">
                     <strong><span class="emoji">📢</span> 重要提醒：</strong>請依照相關規定領取您的獎品，如有疑問請聯絡主辦單位。
                 </p>
             </div>
             
             <p style="text-align: center; margin: 30px 0;">
                 祝您<br>
                 <strong>身體健康，學業進步！</strong>
             </p>
         </div>
         
         <div class="footer">
             <p><strong>{{sender_name}}</strong></p>
             <p style="font-size: 12px; color: #999;">此為系統自動發送的郵件，請勿直接回覆</p>
         </div>
     </div>
 </body>
 </html>"""

    winners_request = {
        "event_id": "event_001",  # 請修改為實際的活動 ID
        "email_config": EMAIL_CONFIG,
        "sender_name": "中興大學抽獎系統",
        "subject": "🎉 恭喜您在「{{event_name}}」中獲得「{{prize_name}}」！",
        "email_template": custom_text_template,
        "html_template": custom_html_template
    }
    
    response = requests.post(f"{BASE_URL}/email/send-winners/event_001", json=winners_request)
    print("發送中獎通知郵件結果（自定義模板）:")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    print("Email API 測試 - 中興大學設定")
    print("=" * 40)
    
    # 只執行不需要實際郵件設定的測試
    test_smtp_settings()
    
    print("\n注意：以下功能需要修改腳本中的郵件設定後才能使用：")
    print("- test_connection()")
    print("- send_test_email()")
    print("\n建議使用中興大學安全連線設定：")
    print("- SMTP 伺服器: dragon.nchu.edu.tw")
    print("- 連接埠: 465 (SMTPs 安全連線)")
    print("- 帳號: your-username@dragon.nchu.edu.tw")
    print("\n詳細說明請參考 EMAIL_API_README.md") 