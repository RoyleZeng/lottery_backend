#!/usr/bin/env python3
"""
測試更新 event API 的腳本
"""

import requests
import json
from datetime import datetime, timedelta

# API 基礎 URL
BASE_URL = "http://127.0.0.1:8000/lottery"

def test_update_event_api():
    """測試更新 event API"""
    print("=== 測試更新 Event API ===\n")
    
    # 1. 先創建一個測試 event
    print("1. 創建測試 event...")
    create_data = {
        "academic_year_term": "113-1",
        "name": "測試抽獎活動",
        "description": "這是一個測試活動",
        "event_date": (datetime.now() + timedelta(days=7)).isoformat(),
        "type": "general"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/events", json=create_data)
        if response.status_code == 201:
            event_data = response.json()['result']
            event_id = event_data['id']
            print(f"✓ 創建成功，Event ID: {event_id}")
            print(f"  原始名稱: {event_data['name']}")
            print(f"  原始描述: {event_data['description']}")
        else:
            print(f"✗ 創建失敗: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"✗ 創建 event 時發生錯誤: {e}")
        return
    
    # 2. 測試部分更新（只更新名稱和描述）
    print("\n2. 測試部分更新 (只更新名稱和描述)...")
    update_data = {
        "name": "更新後的抽獎活動名稱",
        "description": "這是更新後的活動描述"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/events/{event_id}", json=update_data)
        if response.status_code == 200:
            updated_event = response.json()['result']
            print("✓ 部分更新成功")
            print(f"  更新後名稱: {updated_event['name']}")
            print(f"  更新後描述: {updated_event['description']}")
            print(f"  學年期 (應保持不變): {updated_event['academic_year_term']}")
        else:
            print(f"✗ 部分更新失敗: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 部分更新時發生錯誤: {e}")
    
    # 3. 測試完整更新
    print("\n3. 測試完整更新...")
    full_update_data = {
        "academic_year_term": "113-2",
        "name": "完全更新的抽獎活動",
        "description": "完全更新的活動描述",
        "event_date": (datetime.now() + timedelta(days=14)).isoformat(),
        "type": "final_teaching"
    }
    
    try:
        response = requests.put(f"{BASE_URL}/events/{event_id}", json=full_update_data)
        if response.status_code == 200:
            updated_event = response.json()['result']
            print("✓ 完整更新成功")
            print(f"  學年期: {updated_event['academic_year_term']}")
            print(f"  名稱: {updated_event['name']}")
            print(f"  描述: {updated_event['description']}")
            print(f"  類型: {updated_event['type']}")
        else:
            print(f"✗ 完整更新失敗: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 完整更新時發生錯誤: {e}")
    
    # 4. 測試空更新（不提供任何欄位）
    print("\n4. 測試空更新...")
    try:
        response = requests.put(f"{BASE_URL}/events/{event_id}", json={})
        if response.status_code == 404:
            print("✓ 空更新正確返回 404 (沒有變更)")
        else:
            print(f"✗ 空更新應該返回 404，但返回: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 空更新測試時發生錯誤: {e}")
    
    # 5. 測試更新不存在的 event
    print("\n5. 測試更新不存在的 event...")
    fake_id = "00000000-0000-0000-0000-000000000000"
    try:
        response = requests.put(f"{BASE_URL}/events/{fake_id}", json={"name": "測試"})
        if response.status_code == 404:
            print("✓ 更新不存在的 event 正確返回 404")
        else:
            print(f"✗ 應該返回 404，但返回: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"✗ 測試不存在 event 時發生錯誤: {e}")
    
    # 6. 查看最終狀態
    print(f"\n6. 查看最終的 event 狀態...")
    try:
        response = requests.get(f"{BASE_URL}/events/{event_id}")
        if response.status_code == 200:
            final_event = response.json()['result']
            print("✓ 最終狀態:")
            print(f"  ID: {final_event['id']}")
            print(f"  學年期: {final_event['academic_year_term']}")
            print(f"  名稱: {final_event['name']}")
            print(f"  描述: {final_event['description']}")
            print(f"  類型: {final_event['type']}")
            print(f"  狀態: {final_event['status']}")
        else:
            print(f"✗ 獲取最終狀態失敗: {response.status_code}")
    except Exception as e:
        print(f"✗ 獲取最終狀態時發生錯誤: {e}")

if __name__ == "__main__":
    test_update_event_api() 