#!/usr/bin/env python3
"""
測試更新的上傳參與者和抽獎邏輯

測試項目：
1. General 參與者：Oracle 查不到不跳過，仍然匯入
2. Final_teaching 參與者：需要 surveys_completed=Y 和 valid_surveys=Y 
3. 回傳格式：包含總上傳人數和匯入待抽名單人數
4. 抽獎邏輯：只有符合條件的參與者才能被抽中
"""

import requests
import asyncio
import json
import sys
import os

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000"

def test_general_logic():
    """測試 General 類型活動的新邏輯"""
    print("=" * 80)
    print("測試 General 類型活動的新邏輯")
    print("=" * 80)
    
    # 1. 創建 general 活動
    print("\n1. 創建 general 活動...")
    event_data = {
        "academic_year_term": "113-1",
        "name": "General 邏輯測試活動",
        "description": "測試 Oracle 查不到不跳過的邏輯",
        "event_date": "2024-01-15T10:00:00",
        "type": "general"
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events", json=event_data)
    if response.status_code != 200:
        print(f"❌ 創建活動失敗: {response.status_code} - {response.text}")
        return None
    
    event_id = response.json()['result']['id']
    print(f"✅ 活動創建成功，ID: {event_id}")
    
    # 2. 上傳參與者（包含一些 Oracle 查不到的學號）
    print("\n2. 上傳參與者（包含可能查不到的學號）...")
    students_data = {
        "students": [
            {
                "id": "S1234567",  # 可能存在的學號
                "department": "資訊工程學系",
                "name": "王小明",
                "grade": "大四",
                "required_surveys": 5,
                "completed_surveys": 5,
                "surveys_completed": "Y",
                "valid_surveys": "Y"
            },
            {
                "id": "S9999999",  # 肯定不存在的學號
                "department": "測試系",
                "name": "測試學生",
                "grade": "大一",
                "required_surveys": 3,
                "completed_surveys": 3,
                "surveys_completed": "Y",
                "valid_surveys": "Y"
            },
            {
                "id": "S0000000",  # 另一個不存在的學號
                "department": "虛擬系",
                "name": "虛擬學生",
                "grade": "大二",
                "required_surveys": 4,
                "completed_surveys": 4,
                "surveys_completed": "Y",
                "valid_surveys": "Y"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events/{event_id}/participants", json=students_data)
    if response.status_code not in [200, 201]:
        print(f"❌ 上傳參與者失敗: {response.status_code} - {response.text}")
        return event_id
    
    result = response.json()['result']
    print("✅ 上傳參與者成功:")
    print(f"   - 總上傳人數: {result.get('total_uploaded', 'N/A')}")
    print(f"   - 成功匯入: {result['total_imported']} 人")
    print(f"   - 待抽名單: {result.get('total_eligible', 'N/A')} 人")
    print(f"   - 跳過: {result['total_skipped']} 人")
    print(f"   - 新增: {result.get('inserted_count', 0)} 人")
    print(f"   - 更新: {result.get('updated_count', 0)} 人")
    
    if result['skipped']:
        print("   跳過的學生:")
        for student in result['skipped']:
            print(f"     - {student['student_id']}: {student['reason']}")
    
    print(f"\n📊 測試結果: 預期全部學生都應該被匯入（即使 Oracle 查不到）")
    print(f"   實際匯入: {result['total_imported']}/{result.get('total_uploaded', len(students_data['students']))}")
    
    return event_id


def test_final_teaching_logic():
    """測試 Final_teaching 類型活動的新邏輯"""
    print("\n" + "=" * 80)
    print("測試 Final_teaching 類型活動的新邏輯")
    print("=" * 80)
    
    # 1. 創建 final_teaching 活動
    print("\n1. 創建 final_teaching 活動...")
    event_data = {
        "academic_year_term": "113-1",
        "name": "Final Teaching 邏輯測試活動",
        "description": "測試雙重條件檢查邏輯",
        "event_date": "2024-01-15T10:00:00",
        "type": "final_teaching"
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events", json=event_data)
    if response.status_code != 200:
        print(f"❌ 創建活動失敗: {response.status_code} - {response.text}")
        return None
    
    event_id = response.json()['result']['id']
    print(f"✅ 活動創建成功，ID: {event_id}")
    
    # 2. 上傳不同條件的參與者
    print("\n2. 上傳不同條件的參與者...")
    students_data = {
        "students": [
            {
                "id": "FT001",
                "department": "資訊工程學系",
                "name": "完全符合學生",
                "grade": "大四",
                "id_number": "A123456789",
                "address": "台中市南區興大路145號",
                "student_type": "N",
                "phone": "0912345678",
                "email": "ft001@smail.nchu.edu.tw",
                "required_surveys": 5,
                "completed_surveys": 5,
                "surveys_completed": "Y",  # ✅ 完成問卷
                "valid_surveys": "Y"       # ✅ 有效問卷
            },
            {
                "id": "FT002",
                "department": "電機工程學系",
                "name": "未完成問卷學生",
                "grade": "大三",
                "id_number": "B234567890",
                "address": "台中市西區民權路99號",
                "student_type": "N",
                "phone": "0923456789",
                "email": "ft002@smail.nchu.edu.tw",
                "required_surveys": 4,
                "completed_surveys": 3,
                "surveys_completed": "N",  # ❌ 未完成問卷
                "valid_surveys": "Y"       # ✅ 有效問卷
            },
            {
                "id": "FT003",
                "department": "機械工程學系",
                "name": "無效問卷學生",
                "grade": "大二",
                "id_number": "C345678901",
                "address": "台中市北區學士路100號",
                "student_type": "Y",
                "phone": "0934567890",
                "email": "ft003@smail.nchu.edu.tw",
                "required_surveys": 6,
                "completed_surveys": 6,
                "surveys_completed": "Y",  # ✅ 完成問卷
                "valid_surveys": "N"       # ❌ 無效問卷
            },
            {
                "id": "FT004",
                "department": "化學工程學系",
                "name": "雙重不符合學生",
                "grade": "大一",
                "id_number": "D456789012",
                "address": "台中市東區建國路200號",
                "student_type": "N",
                "phone": "0945678901",
                "email": "ft004@smail.nchu.edu.tw",
                "required_surveys": 3,
                "completed_surveys": 2,
                "surveys_completed": "N",  # ❌ 未完成問卷
                "valid_surveys": "N"       # ❌ 無效問卷
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events/{event_id}/participants", json=students_data)
    if response.status_code not in [200, 201]:
        print(f"❌ 上傳參與者失敗: {response.status_code} - {response.text}")
        return event_id
    
    result = response.json()['result']
    print("✅ 上傳參與者成功:")
    print(f"   - 總上傳人數: {result.get('total_uploaded', 'N/A')}")
    print(f"   - 成功匯入: {result['total_imported']} 人")
    print(f"   - 待抽名單: {result.get('total_eligible', 'N/A')} 人")
    print(f"   - 跳過: {result['total_skipped']} 人")
    print(f"   - 新增: {result.get('inserted_count', 0)} 人")
    print(f"   - 更新: {result.get('updated_count', 0)} 人")
    
    if result['skipped']:
        print("   跳過的學生:")
        for student in result['skipped']:
            print(f"     - {student['student_id']}: {student['reason']}")
    
    print(f"\n📊 測試結果: 只有 surveys_completed=Y 且 valid_surveys=Y 的學生應該被匯入")
    print(f"   預期匯入: 1 人（FT001）")
    print(f"   實際匯入: {result['total_imported']} 人")
    print(f"   預期跳過: 3 人（FT002, FT003, FT004）")
    print(f"   實際跳過: {result['total_skipped']} 人")
    
    return event_id


def test_drawing_logic(event_id):
    """測試抽獎邏輯"""
    if not event_id:
        print("\n❌ 無法測試抽獎邏輯：沒有有效的活動 ID")
        return
    
    print(f"\n" + "=" * 80)
    print(f"測試抽獎邏輯 - 活動 ID: {event_id}")
    print("=" * 80)
    
    # 1. 設置獎項
    print("\n1. 設置獎項...")
    prizes_data = {
        "prizes": [
            {"name": "一獎", "quantity": 1},
            {"name": "二獎", "quantity": 2}
        ]
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events/{event_id}/prizes", json=prizes_data)
    if response.status_code not in [200, 201]:
        print(f"❌ 設置獎項失敗: {response.status_code} - {response.text}")
        return
    
    print("✅ 獎項設置成功")
    
    # 2. 查看待抽名單
    print("\n2. 查看待抽名單...")
    response = requests.get(f"{BASE_URL}/lottery/events/{event_id}/participants")
    if response.status_code == 200:
        result = response.json()['result']
        print(f"✅ 待抽名單中有 {result['total']} 位參與者")
        for participant in result['participants']:
            print(f"   - {participant['student_id']}: {participant['name']}")
            print(f"     surveys_completed: {participant.get('surveys_completed', 'N/A')}")
            print(f"     valid_surveys: {participant.get('valid_surveys', 'N/A')}")
    else:
        print(f"❌ 查看待抽名單失敗: {response.status_code}")
        return
    
    # 3. 執行抽獎
    print("\n3. 執行抽獎...")
    draw_data = {"event_id": event_id}
    response = requests.post(f"{BASE_URL}/lottery/events/{event_id}/draw", json=draw_data)
    
    if response.status_code in [200, 201]:
        result = response.json()['result']
        print("✅ 抽獎成功:")
        if isinstance(result, list):
            prizes = result
        else:
            prizes = result.get('prizes', [])
        
        for prize in prizes:
            print(f"   {prize['prize_name']} ({prize['quantity']} 名):")
            for winner in prize['winners']:
                print(f"     - {winner['student_id']}: {winner['name']}")
    else:
        print(f"❌ 抽獎失敗: {response.status_code} - {response.text}")


def test_cleanup(event_ids):
    """清理測試資料"""
    print("\n" + "=" * 80)
    print("清理測試資料")
    print("=" * 80)
    
    for event_id in event_ids:
        if event_id:
            print(f"\n清理活動 {event_id}...")
            response = requests.delete(f"{BASE_URL}/lottery/events/{event_id}")
            if response.status_code == 200:
                print(f"✅ 活動 {event_id} 已清理")
            else:
                print(f"❌ 清理活動 {event_id} 失敗: {response.status_code}")


def main():
    """主測試函數"""
    print("🚀 開始測試更新的上傳參與者和抽獎邏輯")
    print("🔍 測試項目:")
    print("   1. General 參與者：Oracle 查不到不跳過")
    print("   2. Final_teaching 參與者：雙重條件檢查")
    print("   3. 回傳格式：新增統計欄位")
    print("   4. 抽獎邏輯：只抽符合條件的參與者")
    
    event_ids = []
    
    try:
        # 測試 General 邏輯
        general_event_id = test_general_logic()
        event_ids.append(general_event_id)
        
        # 測試 Final_teaching 邏輯
        final_teaching_event_id = test_final_teaching_logic()
        event_ids.append(final_teaching_event_id)
        
        # 測試抽獎邏輯（使用 final_teaching 活動）
        test_drawing_logic(final_teaching_event_id)
        
        print("\n🎉 所有測試完成！")
        
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
    
    finally:
        # 清理測試資料
        test_cleanup(event_ids)


if __name__ == "__main__":
    main() 