#!/usr/bin/env python3
"""
測試參與者文件上傳功能
"""

import requests
import os

BASE_URL = "http://localhost:8000"

def test_upload_participants(file_path, event_id="event_001"):
    """測試上傳參與者文件"""
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    print(f"📤 正在上傳文件：{file_path}")
    print(f"🎯 目標活動：{event_id}")
    
    try:
        with open(file_path, 'rb') as file:
            files = {'file': file}
            response = requests.post(
                f"{BASE_URL}/lottery/events/{event_id}/participants/upload",
                files=files
            )
        
        print(f"📊 狀態碼：{response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 上傳成功！")
            print(f"   成功上傳：{result.get('result', {}).get('success_count', 0)} 人")
            if 'error_count' in result.get('result', {}):
                print(f"   錯誤數量：{result['result']['error_count']}")
            if 'errors' in result.get('result', {}):
                print(f"   錯誤詳情：{result['result']['errors']}")
        else:
            print("❌ 上傳失敗")
            try:
                error_info = response.json()
                print(f"   錯誤信息：{error_info}")
            except:
                print(f"   HTTP 錯誤：{response.text}")
                
        return response.status_code == 200
        
    except requests.exceptions.ConnectionError:
        print("❌ 無法連接到服務器")
        print("💡 請確保 API 服務器正在運行：uvicorn lottery_api.main:app --reload")
        return False
    except Exception as e:
        print(f"❌ 上傳過程中發生錯誤：{e}")
        return False

def test_get_participants(event_id="event_001"):
    """測試取得參與者列表"""
    
    print(f"\n📋 正在取得活動 {event_id} 的參與者列表...")
    
    try:
        response = requests.get(f"{BASE_URL}/lottery/events/{event_id}/participants")
        
        if response.status_code == 200:
            result = response.json()
            participants = result.get('result', {})
            
            print("✅ 取得成功！")
            print(f"   總參與者數：{participants.get('total_count', 0)}")
            print(f"   符合條件者：{participants.get('eligible_count', 0)}")
            
            # 顯示前幾個參與者
            participant_list = participants.get('participants', [])
            if participant_list:
                print(f"\n📝 前 3 位參與者：")
                for i, p in enumerate(participant_list[:3], 1):
                    print(f"   {i}. {p.get('name', 'N/A')} ({p.get('department', 'N/A')}) - {p.get('student_id', 'N/A')}")
        else:
            print("❌ 取得失敗")
            print(f"   狀態碼：{response.status_code}")
            
    except Exception as e:
        print(f"❌ 取得參與者列表時發生錯誤：{e}")

def create_test_event():
    """創建測試用的抽獎活動"""
    
    print("🎯 創建測試抽獎活動...")
    
    event_data = {
        "name": "測試抽獎活動",
        "description": "用於測試上傳功能的抽獎活動",
        "event_date": "2024-12-31T23:59:59"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/lottery/events", json=event_data)
        
        if response.status_code == 200:
            result = response.json()
            event_id = result.get('result', {}).get('id')
            print(f"✅ 活動創建成功！活動 ID：{event_id}")
            return event_id
        else:
            print("❌ 活動創建失敗")
            print(f"   狀態碼：{response.status_code}")
            print(f"   回應：{response.text}")
            return "event_001"  # 使用預設 ID
            
    except Exception as e:
        print(f"❌ 創建活動時發生錯誤：{e}")
        return "event_001"  # 使用預設 ID

def main():
    """主測試流程"""
    
    print("🧪 抽獎系統文件上傳功能測試")
    print("="*50)
    
    # 檢查測試文件是否存在
    test_files = [
        "test_data/sample_upload.xlsx",
        "test_data/basic_participants.xlsx", 
        "test_data/essential_participants.xlsx",
        "test_data/participants.csv"
    ]
    
    available_files = [f for f in test_files if os.path.exists(f)]
    
    if not available_files:
        print("❌ 沒有找到測試文件")
        print("💡 請先執行：python generate_test_participants.py")
        return
    
    print(f"📁 找到 {len(available_files)} 個測試文件")
    
    # 創建測試活動
    event_id = create_test_event()
    
    # 逐一測試上傳
    success_count = 0
    for file_path in available_files:
        print(f"\n{'='*60}")
        if test_upload_participants(file_path, event_id):
            success_count += 1
        
        # 測試取得參與者列表
        test_get_participants(event_id)
    
    # 總結
    print(f"\n{'='*60}")
    print(f"🎯 測試總結：")
    print(f"   測試文件總數：{len(available_files)}")
    print(f"   上傳成功數量：{success_count}")
    print(f"   成功率：{success_count/len(available_files)*100:.1f}%")
    
    if success_count == len(available_files):
        print("🎉 所有測試都通過了！")
    else:
        print("⚠️  部分測試失敗，請檢查 API 服務器狀態")
    
    print(f"\n💡 測試完成後可以使用以下 curl 命令測試：")
    print(f"curl -X POST 'http://localhost:8000/lottery/events/{event_id}/participants/upload' \\")
    print(f"     -F 'file=@test_data/sample_upload.xlsx'")

if __name__ == "__main__":
    main() 