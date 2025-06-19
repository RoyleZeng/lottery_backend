#!/usr/bin/env python3
"""
測試 final_teaching 類型的匯入功能
"""
import sys
import os
import asyncio
import json
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from lottery_api.data_access_object.db import Database
from lottery_api.business_model.lottery_business import LotteryBusiness
from lottery_api.schema.lottery import LotteryEventCreate, LotteryEventType

async def test_final_teaching_import():
    """測試 final_teaching 類型的學生匯入功能"""
    print("🧪 測試 final_teaching 類型的學生匯入功能")
    
    conn = await Database.get_connection()
    try:
        # 1. 創建 final_teaching 類型的活動
        print("\n1. 創建 final_teaching 類型的活動...")
        event_data = LotteryEventCreate(
            academic_year_term="113-1",
            name="期末教學評量抽獎測試",
            description="測試 final_teaching 類型的完整資料匯入",
            event_date="2024-01-15T10:00:00",
            type=LotteryEventType.FINAL_TEACHING
        )
        
        event = await LotteryBusiness.create_lottery_event(conn, event_data)
        event_id = event['id']
        print(f"✅ 活動已創建，ID: {event_id}")
        
        # 2. 準備測試學生資料（包含完整資訊）
        print("\n2. 準備測試學生資料...")
        students_data = [
            {
                "id": "S1234567",
                "department": "資訊工程學系",
                "name": "王小明",
                "grade": "大四",
                "id_number": "A123456789",
                "address": "台中市南區興大路145號",
                "student_type": "本國生",
                "phone": "0912345678",
                "email": "s1234567@smail.nchu.edu.tw",
                "required_surveys": 5,
                "completed_surveys": 5,
                "surveys_completed": True,
                "valid_surveys": "Y"
            },
            {
                "id": "S2345678",
                "department": "電機工程學系",
                "name": "李小華",
                "grade": "大三",
                "id_number": "B234567890",
                "address": "台中市西區民權路99號",
                "student_type": "本國生",
                "phone": "0923456789",
                "email": "s2345678@smail.nchu.edu.tw",
                "required_surveys": 4,
                "completed_surveys": 3,
                "surveys_completed": False,
                "valid_surveys": "N"  # 這個學生應該被跳過
            },
            {
                "id": "S3456789",
                "department": "機械工程學系",
                "name": "張小美",
                "grade": "大二",
                "id_number": "C345678901",
                "address": "台中市北區學士路100號",
                "student_type": "外籍生",
                "phone": "0934567890",
                "email": "s3456789@smail.nchu.edu.tw",
                "required_surveys": 6,
                "completed_surveys": 6,
                "surveys_completed": True,
                "valid_surveys": "Y"
            }
        ]
        
        print(f"   準備了 {len(students_data)} 筆學生資料")
        
        # 3. 匯入學生資料
        print("\n3. 匯入學生資料...")
        result = await LotteryBusiness.import_students_and_add_participants(
            conn, event_id, students_data
        )
        
        print(f"✅ 匯入結果:")
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
        
        # 4. 查看參與者資料
        print("\n4. 查看參與者資料...")
        participants_result = await LotteryBusiness.get_participants(conn, event_id)
        participants = participants_result['participants']
        
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
        
        # 5. 清理測試資料
        print("5. 清理測試資料...")
        await LotteryBusiness.soft_delete_event(conn, event_id)
        print("✅ 測試完成，已清理測試資料")
    
    except Exception as e:
        print(f"❌ 測試過程中發生錯誤: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_final_teaching_import()) 