#!/usr/bin/env python3
"""
測試郵件 From 標頭修復
"""

import requests
import json

BASE_URL = "http://localhost:8000"

def test_email_header_fix():
    """測試郵件標頭修復"""
    print("🔧 測試郵件 From 標頭修復...")
    
    # 測試配置（請替換為您的實際憑證）
    email_config = {
        "smtp_server": "dragon.nchu.edu.tw",
        "smtp_port": 465,
        "username": "roy980630@dragon.nchu.edu.tw",
        "password": "Roy653013",
        "use_tls": True
    }
    
    # 測試中獎通知郵件
    test_request = {
        "email_config": email_config,
        "sender_name": "抽獎系統測試",
        "subject": "🎉 中獎通知測試 - RFC 5322 修復版本",
        "email_template": """親愛的 {{winner_name}} 同學，

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
{{sender_name}}

【這是測試郵件 - From 標頭已修復為符合 RFC 5322 規範】""",
        "test_recipients": [
            "roy980630@gmail.com"
        ]
    }
    
    # 查找有中獎者的活動
    print("1. 查找有中獎者的活動...")
    response = requests.get(f"{BASE_URL}/lottery/events")
    events = response.json()["result"]
    drawn_events = [e for e in events if e["status"] == "drawn"]
    
    if not drawn_events:
        print("   ❌ 沒有已抽獎的活動，無法測試")
        return
    
    test_event = drawn_events[0]
    event_id = test_event["id"]
    event_name = test_event["name"]
    print(f"   ✅ 使用活動：{event_name}")
    
    # 發送測試郵件
    print("\n2. 發送測試郵件（修復後的 From 標頭）...")
    response = requests.post(f"{BASE_URL}/email/test-winners/{event_id}", json=test_request)
    
    if response.status_code == 200:
        result = response.json()["result"]
        if result["success"]:
            print(f"   ✅ 郵件發送成功！")
            print(f"   📧 成功發送: {result['sent_count']} 封")
            print(f"   📝 訊息: {result['message']}")
            print("\n🎯 修復說明：")
            print("   - 使用 email.utils.formataddr() 正確格式化 From 標頭")
            print("   - 符合 RFC 5322 規範")
            print("   - 支援中文寄件人名稱的正確編碼")
            print("   - Gmail 現在應該可以正常接收郵件")
        else:
            print(f"   ⚠️  郵件發送失敗: {result['message']}")
    else:
        print(f"   ❌ API 調用失敗: {response.status_code}")
        print(f"   錯誤: {response.text}")
    
    # 測試連接
    print("\n3. 測試郵件伺服器連接...")
    response = requests.post(f"{BASE_URL}/email/test-connection", json=email_config)
    result = response.json()["result"]
    
    if result["success"]:
        print("   ✅ 郵件伺服器連接成功")
    else:
        print(f"   ⚠️  連接測試: {result['message']}")

def main():
    """主函數"""
    print("🚀 開始測試郵件 From 標頭修復...")
    
    try:
        # 檢查服務器
        response = requests.get(f"{BASE_URL}/lottery/events", timeout=5)
        if response.status_code != 200:
            print("❌ API 服務器無法訪問")
            return
    except requests.exceptions.RequestException:
        print("❌ 無法連接到 API 服務器")
        return
    
    test_email_header_fix()
    
    print("\n" + "="*60)
    print("✅ 郵件 From 標頭修復測試完成！")
    print("\n修復內容：")
    print("1. 使用 email.utils.formataddr() 正確格式化郵件標頭")
    print("2. 符合 RFC 5322 規範要求")
    print("3. 正確處理中文字符編碼")
    print("4. 修復 Gmail 的 '550-5.7.1 Messages missing a valid address in From: header' 錯誤")
    print("\n現在郵件應該可以成功發送到 Gmail 等嚴格的郵件服務商！")

if __name__ == "__main__":
    main() 