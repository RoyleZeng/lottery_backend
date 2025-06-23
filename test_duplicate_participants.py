#!/usr/bin/env python3
"""
測試重複參與者去重功能的腳本
"""

import requests
import json
from datetime import datetime, timedelta

# API 基礎 URL
BASE_URL = "http://127.0.0.1:8000/lottery"

def test_duplicate_participants():
    """測試重複參與者去重功能"""
    print("=== 測試重複參與者去重功能 ===\n")
    
    # 1. 創建測試 event
    print("1. 創建測試 event...")
    create_data = {
        "academic_year_term": "113-1",
        "name": "去重測試抽獎活動",
        "description": "測試重複參與者去重功能",
        "event_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "type": "final_teaching"  # 使用 final_teaching 類型避免 Oracle 查詢
    }
    
    try:
        response = requests.post(f"{BASE_URL}/events", json=create_data)
        if response.status_code == 201:
            event_data = response.json()['result']
            event_id = event_data['id']
            print(f"✓ 創建成功，Event ID: {event_id}")
        else:
            print(f"✗ 創建失敗: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ 創建 event 時發生錯誤: {e}")
        return
    
    # 2. 第一次上傳參與者
    print("\n2. 第一次上傳參與者...")
    first_batch = {
        "students": [
            {
                "id": "A12345678",
                "name": "測試學生1",
                "department": "資訊工程系",
                "grade": "大三",
                "valid_surveys": "Y",
                "required_surveys": 5,
                "completed_surveys": 5,
                "surveys_completed": True,
                "id_number": "A123456789",
                "phone": "0912345678",
                "email": "student1@example.com"
            },
            {
                "id": "B87654321",
                "name": "測試學生2",
                "department": "電子工程系",
                "grade": "大四",
                "valid_surveys": "Y",
                "required_surveys": 4,
                "completed_surveys": 4,
                "surveys_completed": True,
                "id_number": "B987654321",
                "phone": "0987654321",
                "email": "student2@example.com"
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/events/{event_id}/participants", json=first_batch)
        if response.status_code == 201:
            result = response.json()['result']
            print("✓ 第一次上傳成功")
            print(f"  新增: {result['total_imported']} 人")
            print(f"  跳過: {result['total_skipped']} 人")
            print(f"  插入數量: {result.get('inserted_count', 0)} 人")
            print(f"  更新數量: {result.get('updated_count', 0)} 人")
        else:
            print(f"✗ 第一次上傳失敗: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ 第一次上傳時發生錯誤: {e}")
        return
    
    # 3. 查看當前參與者數量
    print("\n3. 查看第一次上傳後的參與者數量...")
    try:
        response = requests.get(f"{BASE_URL}/events/{event_id}/participants")
        if response.status_code == 200:
            result = response.json()['result']
            print(f"✓ 目前參與者總數: {result['total']} 人")
            for participant in result['participants']:
                print(f"  - {participant['student_id']}: {participant['name']}")
        else:
            print(f"✗ 獲取參與者失敗: {response.status_code}")
    except Exception as e:
        print(f"✗ 獲取參與者時發生錯誤: {e}")
    
    # 4. 第二次上傳（包含重複和新的參與者）
    print("\n4. 第二次上傳（包含重複學號）...")
    second_batch = {
        "students": [
            {
                "id": "A12345678",  # 重複的學號
                "name": "測試學生1 (更新後)",
                "department": "資訊工程系",
                "grade": "大三",
                "valid_surveys": "Y",
                "required_surveys": 6,  # 更新的資料
                "completed_surveys": 6,  # 更新的資料
                "surveys_completed": True,
                "id_number": "A123456789",
                "phone": "0912345679",  # 更新的電話
                "email": "student1_updated@example.com"  # 更新的email
            },
            {
                "id": "C11111111",  # 新的學號
                "name": "測試學生3",
                "department": "機械工程系",
                "grade": "大二",
                "valid_surveys": "Y",
                "required_surveys": 3,
                "completed_surveys": 3,
                "surveys_completed": True,
                "id_number": "C111111111",
                "phone": "0911111111",
                "email": "student3@example.com"
            },
            {
                "id": "B87654321",  # 重複的學號
                "name": "測試學生2 (更新後)",
                "department": "電子工程系",
                "grade": "大四",
                "valid_surveys": "Y",
                "required_surveys": 5,  # 更新的資料
                "completed_surveys": 5,  # 更新的資料
                "surveys_completed": True,
                "id_number": "B987654321",
                "phone": "0987654322",  # 更新的電話
                "email": "student2_updated@example.com"  # 更新的email
            }
        ]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/events/{event_id}/participants", json=second_batch)
        if response.status_code == 201:
            result = response.json()['result']
            print("✓ 第二次上傳成功")
            print(f"  總處理: {result['total_imported']} 人")
            print(f"  跳過: {result['total_skipped']} 人")
            print(f"  插入數量: {result.get('inserted_count', 0)} 人 (新參與者)")
            print(f"  更新數量: {result.get('updated_count', 0)} 人 (已存在參與者)")
            
            if result.get('skipped'):
                print("  跳過的學生:")
                for skipped in result['skipped']:
                    print(f"    - {skipped['student_id']}: {skipped['reason']}")
        else:
            print(f"✗ 第二次上傳失敗: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ 第二次上傳時發生錯誤: {e}")
        return
    
    # 5. 查看最終參與者數量和內容
    print("\n5. 查看第二次上傳後的參與者數量和內容...")
    try:
        response = requests.get(f"{BASE_URL}/events/{event_id}/participants")
        if response.status_code == 200:
            result = response.json()['result']
            print(f"✓ 最終參與者總數: {result['total']} 人")
            print("  參與者詳細資訊:")
            for participant in result['participants']:
                print(f"    - 學號: {participant['student_id']}")
                print(f"      姓名: {participant['name']}")
                print(f"      系所: {participant['department']}")
                print(f"      必修問卷: {participant.get('required_surveys', 'N/A')}")
                print(f"      完成問卷: {participant.get('completed_surveys', 'N/A')}")
                print("")
        else:
            print(f"✗ 獲取最終參與者失敗: {response.status_code}")
    except Exception as e:
        print(f"✗ 獲取最終參與者時發生錯誤: {e}")
    
    # 6. 驗證結果
    print("6. 驗證結果...")
    expected_total = 3  # 應該是 3 個不同的學號
    try:
        response = requests.get(f"{BASE_URL}/events/{event_id}/participants")
        if response.status_code == 200:
            actual_total = response.json()['result']['total']
            if actual_total == expected_total:
                print(f"✓ 去重功能正常！預期 {expected_total} 人，實際 {actual_total} 人")
                print("✓ 重複學號已被正確處理（更新而非重複插入）")
            else:
                print(f"✗ 去重功能異常！預期 {expected_total} 人，實際 {actual_total} 人")
        else:
            print("✗ 無法驗證結果")
    except Exception as e:
        print(f"✗ 驗證時發生錯誤: {e}")

if __name__ == "__main__":
    test_duplicate_participants() 