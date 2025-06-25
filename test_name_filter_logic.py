#!/usr/bin/env python3
"""
測試抽獎時過濾沒有名字的參與者功能
"""

import requests
import json
import sys

# API 基礎 URL  
BASE_URL = "http://localhost:8000"

def test_name_filter_in_lottery():
    """測試抽獎時會過濾掉沒有名字的參與者"""
    print("=" * 60)
    print("測試抽獎名字過濾功能")
    print("=" * 60)
    
    # 1. 創建測試活動
    print("\n1. 創建測試活動...")
    event_data = {
        "academic_year_term": "113-1",
        "name": "名字過濾測試活動",
        "description": "測試沒有名字的參與者不會被抽中",
        "event_date": "2024-01-15",
        "type": "general"
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events", json=event_data)
    if response.status_code not in [200, 201]:
        print(f"❌ 創建活動失敗: {response.status_code} - {response.text}")
        return None
    
    event = response.json()['result']
    event_id = event['id']
    print(f"✅ 活動創建成功，ID: {event_id}")
    
    # 2. 添加測試參與者（包含有名字和沒有名字的）
    print("\n2. 添加測試參與者...")
    
    # 手動添加參與者（模擬有名字和沒有名字的情況）
    participants_data = {
        "students": [
            {
                "id": "test001",
                "department": "資訊工程系",
                "name": "張三",  # 有名字
                "grade": "大三"
            },
            {
                "id": "test002",
                "department": "電機工程系", 
                "name": "",  # 沒有名字（空字串）
                "grade": "大二"
            },
            {
                "id": "test003",
                "department": "機械工程系",
                "name": "李四",  # 有名字
                "grade": "大四"
            },
            {
                "id": "test004",
                "department": "化工系",
                # 完全沒有 name 欄位
                "grade": "大一"
            },
            {
                "id": "test005",
                "department": "數學系",
                "name": "   ",  # 只有空白字元
                "grade": "大三"
            }
        ]
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events/{event_id}/participants", json=participants_data)
    if response.status_code not in [200, 201]:
        print(f"❌ 添加參與者失敗: {response.status_code} - {response.text}")
        return event_id
    
    import_result = response.json()['result']
    total_processed = import_result.get('total_processed', import_result.get('imported_count', len(participants_data['students'])))
    print(f"✅ 參與者添加成功，總共處理: {total_processed} 位")
    
    # 3. 查看所有參與者
    print("\n3. 查看所有參與者...")
    response = requests.get(f"{BASE_URL}/lottery/events/{event_id}/participants")
    if response.status_code == 200:
        result = response.json()['result']
        print(f"參與者總數: {result['total']}")
        for i, participant in enumerate(result['participants'], 1):
            name = participant.get('name', 'NO_NAME')
            print(f"  {i}. 學號: {participant['student_id']}, 姓名: '{name}', 系所: {participant.get('department', 'N/A')}")
    else:
        print(f"❌ 查看參與者失敗: {response.status_code}")
        return event_id
    
    # 4. 設置獎項
    print("\n4. 設置獎項...")
    prizes_data = {
        "prizes": [
            {"name": "測試獎項", "quantity": 3}  # 設置3個獎，看能抽到哪些人
        ]
    }
    
    response = requests.post(f"{BASE_URL}/lottery/events/{event_id}/prizes", json=prizes_data)
    if response.status_code not in [200, 201]:
        print(f"❌ 設置獎項失敗: {response.status_code} - {response.text}")
        return event_id
    
    print("✅ 獎項設置成功")
    
    # 5. 執行抽獎
    print("\n5. 執行抽獎...")
    draw_data = {"event_id": event_id}
    response = requests.post(f"{BASE_URL}/lottery/events/{event_id}/draw", json=draw_data)
    
    if response.status_code == 200:
        winners = response.json()['result']
        print("🎉 抽獎執行成功！")
        
        for prize_group in winners:
            print(f"\n獎項: {prize_group['prize_name']} (數量: {prize_group['quantity']})")
            if prize_group['winners']:
                for winner in prize_group['winners']:
                    name = winner.get('name', 'NO_NAME')
                    print(f"  🏆 中獎者: 學號 {winner['student_id']}, 姓名: '{name}'")
            else:
                print("  沒有中獎者")
        
        # 檢查是否有沒有名字的人中獎
        all_winners = []
        for prize_group in winners:
            all_winners.extend(prize_group['winners'])
        
        invalid_name_winners = [w for w in all_winners if not w.get('name') or w.get('name').strip() == '']
        if invalid_name_winners:
            print(f"\n❌ 測試失敗！發現 {len(invalid_name_winners)} 位沒有名字的中獎者：")
            for winner in invalid_name_winners:
                print(f"  - 學號: {winner['student_id']}, 姓名: '{winner.get('name', 'NO_NAME')}'")
        else:
            print(f"\n✅ 測試成功！所有中獎者都有有效的名字，沒有名字的參與者被正確過濾了！")
            
    else:
        print(f"❌ 抽獎失敗: {response.status_code} - {response.text}")
    
    return event_id

def cleanup_test_event(event_id):
    """清理測試活動"""
    if not event_id:
        return
        
    print(f"\n6. 清理測試活動 {event_id}...")
    response = requests.delete(f"{BASE_URL}/lottery/events/{event_id}")
    if response.status_code == 200:
        print("✅ 測試活動已清理")
    else:
        print(f"⚠️  清理活動失敗: {response.status_code} - {response.text}")

if __name__ == "__main__":
    try:
        event_id = test_name_filter_in_lottery()
        
        # 詢問是否要清理測試數據
        if event_id:
            user_input = input("\n是否要清理測試活動？(y/N): ").strip().lower()
            if user_input in ['y', 'yes']:
                cleanup_test_event(event_id)
            else:
                print(f"測試活動保留，ID: {event_id}")
                
    except KeyboardInterrupt:
        print("\n測試被中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試過程中發生錯誤: {e}")
        sys.exit(1) 