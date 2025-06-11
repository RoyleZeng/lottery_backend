#!/bin/bash

# Email API 測試範例 - 中興大學設定
# 使用 curl 命令測試各種 email 功能

BASE_URL="http://localhost:8000"

echo "=== Email API 測試範例 - 中興大學設定 ==="
echo

# 1. 取得 SMTP 設定範例
echo "1. 取得 SMTP 設定範例"
curl -X GET "$BASE_URL/email/smtp-settings-example" \
  -H "Content-Type: application/json" | jq '.'

echo -e "\n" && read -p "按 Enter 繼續..."

# 2. 取得模板變數列表
echo "2. 取得模板變數列表"
curl -X GET "$BASE_URL/email/template-variables" \
  -H "Content-Type: application/json" | jq '.'

echo -e "\n" && read -p "按 Enter 繼續..."

# 3. 測試郵件伺服器連接 (中興大學安全連線)
echo "3. 測試郵件伺服器連接 (中興大學安全連線)"
echo "注意：請修改以下的帳號密碼為您的實際設定"
echo
cat << 'EOF'
curl -X POST "$BASE_URL/email/test-connection" \
  -H "Content-Type: application/json" \
  -d '{
    "smtp_server": "dragon.nchu.edu.tw",
    "smtp_port": 465,
    "username": "your-username@dragon.nchu.edu.tw",
    "password": "your-password",
    "use_tls": true
  }'
EOF
echo
echo "---"
echo

# 4. 發送郵件 (中興大學設定)
echo "4. 發送郵件 (中興大學設定)"
echo "注意：請修改以下的帳號密碼和收件人為您的實際設定"
echo
cat << 'EOF'
curl -X POST "$BASE_URL/email/send" \
  -H "Content-Type: application/json" \
  -d '{
    "email_config": {
      "smtp_server": "dragon.nchu.edu.tw",
      "smtp_port": 465,
      "username": "your-username@dragon.nchu.edu.tw",
      "password": "your-password",
      "use_tls": true
    },
    "sender_name": "抽獎系統測試",
    "recipients": [
      {
        "email": "recipient@example.com",
        "name": "測試收件人"
      }
    ],
    "content": {
      "subject": "測試郵件",
      "body": "這是一封測試郵件，用來驗證郵件發送功能是否正常運作。",
      "html_body": "<h1>測試郵件</h1><p>這是一封測試郵件，用來驗證郵件發送功能是否正常運作。</p>"
    }
  }'
EOF
echo
echo "---"
echo

# 5. 批量發送郵件
echo "5. 批量發送郵件"
echo "注意：請修改以下的帳號密碼和收件人為您的實際設定"
echo
cat << 'EOF'
curl -X POST "$BASE_URL/email/send-bulk" \
  -H "Content-Type: application/json" \
  -d '{
    "email_config": {
      "smtp_server": "dragon.nchu.edu.tw",
      "smtp_port": 465,
      "username": "your-username@dragon.nchu.edu.tw",
      "password": "your-password",
      "use_tls": true
    },
    "sender_name": "抽獎系統批量測試",
    "subject": "批量測試郵件",
    "body": "這是一封批量測試郵件。",
    "html_body": "<h1>批量測試郵件</h1><p>這是一封批量測試郵件。</p>",
    "recipient_emails": [
      "recipient1@example.com",
      "recipient2@example.com"
    ]
  }'
EOF
echo
echo "---"
echo

# 6. 發送中獎通知郵件（使用預設模板）
echo "6. 發送中獎通知郵件（預設模板）"
curl -X POST "$BASE_URL/email/send-winners/event_001" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "event_001",
    "email_config": {
      "smtp_server": "dragon.nchu.edu.tw",
      "smtp_port": 465,
      "username": "your-username@dragon.nchu.edu.tw",
      "password": "your-password",
      "use_tls": true
    },
    "sender_name": "中興大學抽獎系統",
    "subject": "恭喜您中獎了！"
  }' | jq '.'

echo -e "\n" && read -p "按 Enter 繼續..."

# 7. 發送中獎通知郵件（使用自定義模板）
echo "7. 發送中獎通知郵件（自定義模板）"
curl -X POST "$BASE_URL/email/send-winners/event_001" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "event_001",
    "email_config": {
      "smtp_server": "dragon.nchu.edu.tw",
      "smtp_port": 465,
      "username": "your-username@dragon.nchu.edu.tw",
      "password": "your-password",
      "use_tls": true
    },
    "sender_name": "中興大學抽獎系統",
    "subject": "🎉 恭喜 {{winner_name}} 在「{{event_name}}」中獲得「{{prize_name}}」！",
    "email_template": "親愛的 {{winner_name}} 同學，\n\n🎉 恭喜您中獎了！🎉\n\n您在「{{event_name}}」抽獎活動中獲得了「{{prize_name}}」！\n\n📋 中獎者資訊：\n• 姓名：{{winner_name}}\n• 學號：{{student_id}}\n• 系所：{{department}}\n• 年級：{{grade}}\n\n📅 活動資訊：\n• 活動名稱：{{event_name}}\n• 活動日期：{{event_date}}\n\n請盡快聯絡我們領取您的獎品！\n\n祝您學業進步！\n{{sender_name}}",
    "html_template": "<!DOCTYPE html><html><head><meta charset=\"UTF-8\"><title>中獎通知</title><style>body{font-family:Arial,sans-serif;line-height:1.6;color:#333;background-color:#f5f5f5;margin:0;padding:20px}.container{max-width:600px;margin:0 auto;background-color:white;border-radius:10px;box-shadow:0 4px 6px rgba(0,0,0,0.1);overflow:hidden}.header{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);color:white;padding:30px 20px;text-align:center}.content{padding:30px}.prize-info{background-color:#e8f5e8;padding:15px;border-radius:5px;margin:15px 0}.winner-info{background-color:#f0f8ff;padding:15px;border-radius:5px;margin:15px 0}.footer{text-align:center;color:#666;font-size:14px;margin-top:30px}.highlight{color:#d63384;font-weight:bold}</style></head><body><div class=\"container\"><div class=\"header\"><h1>🎉 恭喜中獎！🎉</h1><p>{{event_name}}</p></div><div class=\"content\"><p>親愛的 <strong>{{winner_name}}</strong>，</p><p>恭喜您在「<span class=\"highlight\">{{event_name}}</span>」抽獎活動中獲得獎項！</p><div class=\"prize-info\"><h3>🏆 獲得獎項</h3><p><strong>{{prize_name}}</strong></p></div><div class=\"winner-info\"><h3>👤 中獎者資訊</h3><ul><li><strong>姓名：</strong>{{winner_name}}</li><li><strong>學號：</strong>{{student_id}}</li><li><strong>系所：</strong>{{department}}</li><li><strong>年級：</strong>{{grade}}</li></ul></div><p>請依照相關規定領取您的獎品。</p><p>祝您<br>身體健康，學業進步！</p></div><div class=\"footer\"><p><strong>{{sender_name}}</strong></p></div></div></body></html>"
  }' | jq '.'

echo -e "\n=== 完成 ==="
echo "注意：請將範例中的郵件設定替換為您的實際設定"
echo "- SMTP 伺服器、帳號、密碼"
echo "- 收件人郵件地址"
echo "- 活動 ID (event_001)"

echo "使用說明："
echo "1. 確保 API 伺服器正在運行：python -m lottery_api.main"
echo "2. 修改上述範例中的帳號密碼為您的實際設定"
echo "3. 建議使用中興大學安全連線設定："
echo "   - SMTP 伺服器: dragon.nchu.edu.tw"
echo "   - 連接埠: 465 (SMTPs 安全連線)"
echo "   - 帳號格式: username@dragon.nchu.edu.tw"
echo "4. 執行前請先測試連接以確保設定正確"
echo
echo "更多詳細說明請參考 EMAIL_API_README.md" 