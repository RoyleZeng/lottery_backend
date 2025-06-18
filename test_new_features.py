#!/usr/bin/env python3
"""
測試新功能腳本
1. Event 軟刪除功能
2. Email 測試 API 功能
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    print(f"\n{'='*60}")
    print(f" {title}")
    print(f"{'='*60}")

def test_soft_delete_features():
    """測試軟刪除功能"""
    print_section("測試 Event 軟刪除功能")
    
    # 1. 獲取現有活動列表
    print("1. 獲取現有活動列表")
    response = requests.get(f"{BASE_URL}/lottery/events")
    events = response.json()["result"]
    print(f"   目前有 {len(events)} 個活動")
    
    if not events:
        print("   沒有活動可供測試，請先創建一些活動")
        return
    
    # 選擇第一個活動進行測試
    test_event = events[0]
    event_id = test_event["id"]
    event_name = test_event["name"]
    
    print(f"   測試活動：{event_name} (ID: {event_id[:8]}...)")
    
    # 2. 軟刪除活動
    print("\n2. 軟刪除活動")
    response = requests.delete(f"{BASE_URL}/lottery/events/{event_id}")
    if response.status_code == 200:
        result = response.json()["result"]
        print(f"   ✅ {result['message']}")
    else:
        print(f"   ❌ 軟刪除失敗: {response.text}")
        return
    
    # 3. 驗證活動從正常列表中消失
    print("\n3. 驗證活動從正常列表中消失")
    response = requests.get(f"{BASE_URL}/lottery/events")
    current_events = response.json()["result"]
    print(f"   正常活動數量從 {len(events)} 減少到 {len(current_events)}")
    
    # 4. 查看被軟刪除的活動
    print("\n4. 查看被軟刪除的活動")
    response = requests.get(f"{BASE_URL}/lottery/deleted-events")
    deleted_events = response.json()["result"]
    print(f"   被軟刪除的活動數量: {len(deleted_events)}")
    for event in deleted_events:
        print(f"   - {event['name']} (已刪除: {event['is_deleted']})")
    
    # 5. 恢復活動
    print("\n5. 恢復活動")
    response = requests.put(f"{BASE_URL}/lottery/events/{event_id}/restore")
    if response.status_code == 200:
        result = response.json()["result"]
        print(f"   ✅ {result['message']}")
    else:
        print(f"   ❌ 恢復失敗: {response.text}")
        return
    
    # 6. 驗證活動恢復到正常列表
    print("\n6. 驗證活動恢復到正常列表")
    response = requests.get(f"{BASE_URL}/lottery/events")
    restored_events = response.json()["result"]
    print(f"   正常活動數量恢復到 {len(restored_events)}")
    
    print("\n✅ 軟刪除功能測試完成！")

def test_email_test_api():
    """測試 Email 測試 API 功能"""
    print_section("測試 Email 測試 API 功能")
    
    # 1. 查找有中獎者的活動
    print("1. 查找有中獎者的活動")
    response = requests.get(f"{BASE_URL}/lottery/events")
    events = response.json()["result"]
    drawn_events = [e for e in events if e["status"] == "drawn"]
    
    if not drawn_events:
        print("   沒有已抽獎的活動，無法測試 email 功能")
        return
    
    test_event = drawn_events[0]
    event_id = test_event["id"]
    event_name = test_event["name"]
    print(f"   測試活動：{event_name} (ID: {event_id[:8]}...)")
    
    # 2. 測試郵件伺服器連接
    print("\n2. 測試郵件伺服器連接")
    email_config = {
        "smtp_server": "dragon.nchu.edu.tw",
        "smtp_port": 465,
        "username": "test@dragon.nchu.edu.tw",
        "password": "test-password",
        "use_tls": True
    }
    
    response = requests.post(f"{BASE_URL}/email/test-connection", json=email_config)
    result = response.json()["result"]
    if result["success"]:
        print("   ✅ 郵件伺服器連接成功")
    else:
        print(f"   ⚠️  郵件伺服器連接失敗（預期結果）: {result['message']}")
    
    # 3. 測試中獎通知郵件
    print("\n3. 測試中獎通知郵件（發送給測試收件人）")
    test_request = {
        "email_config": email_config,
        "sender_name": "測試抽獎系統",
        "subject": "🎉 中獎通知測試 - {{winner_name}} 獲得 {{prize_name}}",
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

【這是測試郵件，實際中獎者為其他人】""",
        "test_recipients": [
            "test1@example.com",
            "test2@example.com",
            "admin@example.com"
        ]
    }
    
    response = requests.post(f"{BASE_URL}/email/test-winners/{event_id}", json=test_request)
    result = response.json()["result"]
    
    print(f"   發送結果: {result['message']}")
    print(f"   成功發送: {result['sent_count']} 封")
    if result.get('failed_recipients'):
        print(f"   失敗收件人: {len(result['failed_recipients'])} 個")
        for email in result['failed_recipients']:
            print(f"     - {email}")
    
    # 4. 獲取模板變數說明
    print("\n4. 獲取模板變數說明")
    response = requests.get(f"{BASE_URL}/email/template-variables")
    variables = response.json()["result"]
    print(f"   可用變數數量: {len(variables['available_variables'])}")
    print("   主要變數:")
    for var_name, var_info in list(variables['available_variables'].items())[:5]:
        print(f"     - {var_info['usage']}: {var_info['description']}")
    
    # 5. 獲取 SMTP 設定範例
    print("\n5. 獲取 SMTP 設定範例")
    response = requests.get(f"{BASE_URL}/email/smtp-settings-example")
    examples = response.json()["result"]
    print(f"   可用設定範例: {len(examples)} 個")
    for name, config in list(examples.items())[:3]:
        print(f"     - {name}: {config['smtp_server']}:{config['smtp_port']}")
    
    print("\n✅ Email 測試 API 功能測試完成！")

def main():
    """主測試函數"""
    print("🚀 開始測試新功能...")
    
    try:
        # 測試服務器是否運行
        response = requests.get(f"{BASE_URL}/lottery/events", timeout=5)
        if response.status_code != 200:
            print("❌ API 服務器無法訪問，請確保服務器正在運行")
            return
    except requests.exceptions.RequestException:
        print("❌ 無法連接到 API 服務器，請確保服務器正在運行在 http://localhost:8000")
        return
    
    # 執行測試
    test_soft_delete_features()
    test_email_test_api()
    
    print_section("測試總結")
    print("✅ 所有新功能測試完成！")
    print("\n新功能說明：")
    print("1. Event 軟刪除功能：")
    print("   - DELETE /lottery/events/{event_id} - 軟刪除活動")
    print("   - PUT /lottery/events/{event_id}/restore - 恢復活動")
    print("   - GET /lottery/deleted-events - 獲取被軟刪除的活動")
    print("\n2. Email 測試 API：")
    print("   - POST /email/test-winners/{event_id} - 測試中獎通知（發送給指定測試收件人）")
    print("   - POST /email/test-connection - 測試郵件伺服器連接")
    print("   - GET /email/template-variables - 獲取模板變數說明")
    print("   - GET /email/smtp-settings-example - 獲取 SMTP 設定範例")

if __name__ == "__main__":
    main() 