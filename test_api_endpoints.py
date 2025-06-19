#!/usr/bin/env python3
"""
測試 API 端點功能
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_api_endpoints():
    """測試 API 端點功能"""
    print("🧪 測試 API 端點功能")
    
    # 1. 測試創建 final_teaching 活動
    print("\n1. 創建 final_teaching 活動...")
    event_data = {
        "academic_year_term": "113-1",
        "name": "API測試-期末教學評量抽獎",
        "description": "測試 final_teaching API 功能",
        "event_date": "2024-01-15T10:00:00",
        "type": "final_teaching"
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events", json=event_data)
    if response.status_code in [200, 201]:
        event = response.json()['result']
        event_id = event['id']
        print(f"✅ 活動創建成功，ID: {event_id}")
    else:
        print(f"❌ 活動創建失敗: {response.status_code} - {response.text}")
        return
    
    # 2. 測試匯入 final_teaching 學生
    print("\n2. 匯入 final_teaching 學生...")
    students_data = {
        "students": [
            {
                "id": "API001",
                "department": "資訊工程學系",
                "name": "API測試學生1",
                "grade": "大四",
                "id_number": "A123456789",
                "address": "台中市南區興大路145號",
                "student_type": "本國生",
                "phone": "0912345678",
                "email": "api001@smail.nchu.edu.tw",
                "required_surveys": 5,
                "completed_surveys": 5,
                "surveys_completed": True,
                "valid_surveys": "Y"
            },
            {
                "id": "API002",
                "department": "電機工程學系",
                "name": "API測試學生2",
                "grade": "大三",
                "id_number": "B234567890",
                "address": "台中市西區民權路99號",
                "student_type": "外籍生",
                "phone": "0923456789",
                "email": "api002@smail.nchu.edu.tw",
                "required_surveys": 4,
                "completed_surveys": 3,
                "surveys_completed": False,
                "valid_surveys": "N"  # 這個應該被跳過
            },
            {
                "id": "API003",
                "department": "機械工程學系",
                "name": "API測試學生3",
                "grade": "大二",
                "id_number": "C345678901",
                "address": "台中市北區學士路100號",
                "student_type": "本國生",
                "phone": "0934567890",
                "email": "api003@smail.nchu.edu.tw",
                "required_surveys": 6,
                "completed_surveys": 6,
                "surveys_completed": True,
                "valid_surveys": "Y"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events/{event_id}/participants", json=students_data)
    if response.status_code in [200, 201]:
        result = response.json()['result']
        print(f"✅ 學生匯入成功:")
        print(f"   - 成功匯入: {result['total_imported']} 人")
        print(f"   - 跳過: {result['total_skipped']} 人")
        
        if result['imported']:
            print("   成功匯入的學生:")
            for student in result['imported']:
                print(f"     - {student['student_name']} ({student['student_id']})")
        
        if result['skipped']:
            print("   跳過的學生:")
            for student in result['skipped']:
                print(f"     - {student['student_id']}: {student['reason']}")
    else:
        print(f"❌ 學生匯入失敗: {response.status_code} - {response.text}")
        return
    
    # 3. 測試查看參與者
    print("\n3. 查看參與者...")
    response = requests.get(f"{BASE_URL}/lottery/events/{event_id}/participants")
    if response.status_code == 200:
        result = response.json()['result']
        participants = result['participants']
        print(f"✅ 找到 {len(participants)} 位參與者:")
        
        for participant in participants:
            print(f"   - {participant['name']} ({participant['student_id']})")
            print(f"     系所: {participant['department']}")
            print(f"     年級: {participant['grade']}")
            print(f"     身份證: {participant.get('id_number', 'N/A')}")
            print(f"     地址: {participant.get('address', 'N/A')}")
            print(f"     身份別: {participant.get('student_type', 'N/A')}")
            print(f"     手機: {participant.get('phone', 'N/A')}")
            print(f"     Email: {participant.get('email', 'N/A')}")
            print(f"     問卷狀態: {participant.get('valid_surveys', 'N/A')}")
            print()
    else:
        print(f"❌ 查看參與者失敗: {response.status_code} - {response.text}")
    
    # 4. 測試創建 general 活動（對比測試）
    print("\n4. 創建 general 活動進行對比測試...")
    general_event_data = {
        "academic_year_term": "113-1",
        "name": "API測試-一般抽獎",
        "description": "測試 general API 功能",
        "event_date": "2024-01-15T10:00:00",
        "type": "general"
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events", json=general_event_data)
    if response.status_code in [200, 201]:
        general_event = response.json()['result']
        general_event_id = general_event['id']
        print(f"✅ General 活動創建成功，ID: {general_event_id}")
        
        # 測試匯入 general 學生（簡化格式）
        general_students_data = {
            "students": [
                {
                    "id": "GEN001",
                    "department": "資訊工程學系",
                    "name": "一般測試學生",
                    "grade": "大四"
                }
            ]
        }
        
        response = requests.post(f"{BASE_URL}/lottery/events/{general_event_id}/participants", json=general_students_data)
        if response.status_code in [200, 201]:
            result = response.json()['result']
            print(f"✅ General 學生匯入結果:")
            print(f"   - 成功匯入: {result['total_imported']} 人")
            print(f"   - 跳過: {result['total_skipped']} 人")
        else:
            print(f"❌ General 學生匯入失敗: {response.status_code} - {response.text}")
    else:
        print(f"❌ General 活動創建失敗: {response.status_code} - {response.text}")
    
    # 5. 清理測試資料
    print("\n5. 清理測試資料...")
    for test_event_id in [event_id, general_event_id if 'general_event_id' in locals() else None]:
        if test_event_id:
            response = requests.delete(f"{BASE_URL}/lottery/events/{test_event_id}")
            if response.status_code == 200:
                print(f"✅ 已清理活動: {test_event_id}")
            else:
                print(f"⚠️  清理活動失敗: {test_event_id}")
    
    print("\n🎉 API 測試完成！")

if __name__ == "__main__":
    print("等待服務器啟動...")
    time.sleep(2)
    
    try:
        # 檢查服務器是否運行
        response = requests.get(f"{BASE_URL}/api/spec/doc", timeout=5)
        if response.status_code == 200:
            print("✅ 服務器運行正常")
            test_api_endpoints()
        else:
            print("❌ 服務器未正常運行")
    except requests.exceptions.RequestException as e:
        print(f"❌ 無法連接到服務器: {e}")
        print("請確保服務器在 http://localhost:8000 運行") 