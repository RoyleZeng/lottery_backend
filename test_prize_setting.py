#!/usr/bin/env python3
"""
測試獎項設定功能 - 驗證 set_prizes 不會累加舊獎項
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def create_test_event():
    """創建測試活動"""
    event_data = {
        "name": "獎項設定測試活動",
        "description": "測試 set_prizes 功能",
        "event_date": "2024-12-31T23:59:59"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/lottery/events", json=event_data)
        if response.status_code == 200:
            result = response.json()
            event_id = result.get('result', {}).get('id')
            print(f"✅ 測試活動創建成功：{event_id}")
            return event_id
        else:
            print(f"❌ 活動創建失敗：{response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 創建活動時發生錯誤：{e}")
        return None

def set_prizes(event_id, prizes):
    """設定獎項"""
    prize_data = {"prizes": prizes}
    
    try:
        response = requests.post(
            f"{BASE_URL}/lottery/events/{event_id}/prizes",
            json=prize_data
        )
        
        if response.status_code == 200:
            result = response.json()
            prizes_result = result.get('result', [])
            print(f"✅ 獎項設定成功，共 {len(prizes_result)} 個獎項")
            for i, prize in enumerate(prizes_result, 1):
                print(f"   {i}. {prize.get('name')} x{prize.get('quantity')}")
            return True
        else:
            print(f"❌ 獎項設定失敗：{response.status_code}")
            try:
                error_info = response.json()
                print(f"   錯誤信息：{error_info}")
            except:
                print(f"   HTTP 錯誤：{response.text}")
            return False
    except Exception as e:
        print(f"❌ 設定獎項時發生錯誤：{e}")
        return False

def get_prizes(event_id):
    """取得獎項列表"""
    try:
        response = requests.get(f"{BASE_URL}/lottery/events/{event_id}/prizes")
        
        if response.status_code == 200:
            result = response.json()
            prizes_data = result.get('result', {})
            prizes = prizes_data.get('prizes', [])
            
            print(f"📋 當前獎項列表（共 {len(prizes)} 個）：")
            if prizes:
                for i, prize in enumerate(prizes, 1):
                    print(f"   {i}. {prize.get('name')} x{prize.get('quantity')} (ID: {prize.get('id')})")
            else:
                print("   (無獎項)")
            return len(prizes)
        else:
            print(f"❌ 取得獎項失敗：{response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ 取得獎項時發生錯誤：{e}")
        return 0

def test_prize_replacement():
    """測試獎項替換功能"""
    print("🧪 開始測試獎項設定功能")
    print("="*60)
    
    # 創建測試活動
    event_id = create_test_event()
    if not event_id:
        return False
    
    print("\n" + "="*60)
    print("📍 第一次設定獎項")
    print("-"*30)
    
    # 第一次設定獎項
    first_prizes = [
        {"name": "頭獎", "quantity": 1},
        {"name": "二獎", "quantity": 2}
    ]
    
    success = set_prizes(event_id, first_prizes)
    if not success:
        return False
    
    # 檢查獎項數量
    count1 = get_prizes(event_id)
    expected_count1 = 2
    
    if count1 != expected_count1:
        print(f"❌ 第一次設定失敗：期望 {expected_count1} 個獎項，實際 {count1} 個")
        return False
    
    print(f"✅ 第一次設定正確：{count1} 個獎項")
    
    print("\n" + "="*60)
    print("📍 第二次設定獎項（應該替換，不是累加）")
    print("-"*30)
    
    # 第二次設定獎項（不同的獎項）
    second_prizes = [
        {"name": "特等獎", "quantity": 1},
        {"name": "優等獎", "quantity": 3},
        {"name": "佳作", "quantity": 5}
    ]
    
    success = set_prizes(event_id, second_prizes)
    if not success:
        return False
    
    # 檢查獎項數量
    count2 = get_prizes(event_id)
    expected_count2 = 3
    
    if count2 != expected_count2:
        print(f"❌ 第二次設定失敗：期望 {expected_count2} 個獎項，實際 {count2} 個")
        print("❌ 這表示舊獎項沒有被正確刪除，而是累加了！")
        return False
    
    print(f"✅ 第二次設定正確：{count2} 個獎項")
    
    print("\n" + "="*60)
    print("📍 第三次設定獎項（更少的獎項）")
    print("-"*30)
    
    # 第三次設定獎項（更少的獎項，測試是否正確清除多餘的）
    third_prizes = [
        {"name": "冠軍", "quantity": 1}
    ]
    
    success = set_prizes(event_id, third_prizes)
    if not success:
        return False
    
    # 檢查獎項數量
    count3 = get_prizes(event_id)
    expected_count3 = 1
    
    if count3 != expected_count3:
        print(f"❌ 第三次設定失敗：期望 {expected_count3} 個獎項，實際 {count3} 個")
        return False
    
    print(f"✅ 第三次設定正確：{count3} 個獎項")
    
    print("\n" + "="*60)
    print("📍 第四次設定獎項（空獎項列表）")
    print("-"*30)
    
    # 第四次設定空獎項（測試清空功能）
    empty_prizes = []
    
    success = set_prizes(event_id, empty_prizes)
    if not success:
        return False
    
    # 檢查獎項數量
    count4 = get_prizes(event_id)
    expected_count4 = 0
    
    if count4 != expected_count4:
        print(f"❌ 第四次設定失敗：期望 {expected_count4} 個獎項，實際 {count4} 個")
        return False
    
    print(f"✅ 第四次設定正確：{count4} 個獎項（已清空）")
    
    return True

def main():
    """主測試流程"""
    print("🎯 獎項設定功能測試")
    print("目標：驗證 set_prizes 會正確替換獎項，而不是累加")
    print("="*60)
    
    try:
        # 測試服務器連接
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print("✅ API 服務器連接正常")
    except:
        print("❌ 無法連接到 API 服務器")
        print("💡 請確保服務器正在運行：uvicorn lottery_api.main:app --reload")
        return
    
    # 執行測試
    if test_prize_replacement():
        print("\n🎉 所有測試通過！獎項設定功能正常運作")
        print("✅ 修復成功：set_prizes 現在會正確替換獎項，不會累加")
    else:
        print("\n❌ 測試失敗！請檢查 set_prizes 的實現")
        print("🔧 可能需要檢查 LotteryBusiness.set_prizes 方法")

if __name__ == "__main__":
    main() 