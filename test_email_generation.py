#!/usr/bin/env python3
"""
測試 Email 自動生成功能
驗證中獎通知系統能否正確根據學號生成 email 地址
"""

import asyncio
import asyncpg
import json
from lottery_api.utils.email_generator import EmailGenerator
from lottery_api.business_model.lottery_business import LotteryBusiness
from lottery_api.business_model.email_business import EmailBusiness
from lottery_api.schema.email import EmailConfig

# 數據庫配置
DB_CONFIG = {
    "user": "local",
    "password": "local1234", 
    "database": "postgres",
    "host": "localhost",
    "port": 5432
}

# 測試用的 Email 配置（請替換為實際配置）
EMAIL_CONFIG = EmailConfig(
    smtp_server="smtp.gmail.com",
    smtp_port=587,
    username="your-email@gmail.com",
    password="your-app-password",
    use_tls=True
)

async def test_email_generation_for_winners():
    """測試為中獎者自動生成 email 地址"""
    print("=== 測試 Email 自動生成功能 ===\n")
    
    try:
        # 連接數據庫
        conn = await asyncpg.connect(**DB_CONFIG)
        print("✅ 數據庫連接成功")
        
        # 獲取抽獎活動列表
        events = await LotteryBusiness.get_lottery_events(conn)
        if not events:
            print("❌ 沒有找到抽獎活動")
            return
            
        print(f"📋 找到 {len(events)} 個抽獎活動")
        
        # 選擇第一個活動進行測試
        test_event = events[0]
        event_id = test_event["id"]
        event_name = test_event["name"]
        
        print(f"🎯 測試活動: {event_name} (ID: {event_id})")
        
        # 獲取中獎者
        winners = await LotteryBusiness.get_winners(conn, event_id)
        if not winners:
            print("❌ 此活動沒有中獎者")
            return
            
        print(f"🏆 找到 {len(winners)} 個獎項的中獎者")
        
        # 測試 email 生成
        total_winners = 0
        generated_emails = 0
        
        print("\n=== Email 生成測試結果 ===")
        
        for prize_group in winners:
            prize_name = prize_group["prize_name"]
            prize_winners = prize_group["winners"]
            
            print(f"\n🏅 {prize_name} ({len(prize_winners)} 位中獎者):")
            
            for winner in prize_winners:
                total_winners += 1
                student_id = winner.get("student_id", "N/A")
                name = winner.get("name", "未知")
                
                # 生成 email
                generated_email = EmailGenerator.generate_email_from_student_id(student_id)
                student_type = EmailGenerator.get_student_type_from_id(student_id)
                
                if generated_email:
                    generated_emails += 1
                    status = "✅"
                else:
                    status = "❌"
                
                print(f"  {status} {name} (學號: {student_id})")
                print(f"      類型: {student_type or '無法識別'}")
                print(f"      Email: {generated_email or '無法生成'}")
        
        print(f"\n📊 統計結果:")
        print(f"   總中獎者: {total_winners} 位")
        print(f"   成功生成 Email: {generated_emails} 位")
        print(f"   生成成功率: {(generated_emails/total_winners*100):.1f}%")
        
        # 測試實際的 email 通知功能（不實際發送）
        print(f"\n=== 測試 Email 通知功能 ===")
        
        try:
            # 這裡我們只測試 email 地址的生成，不實際發送郵件
            print("🔍 模擬 email 通知流程...")
            
            # 模擬收集收件人
            recipients = []
            for prize_group in winners:
                for winner in prize_group["winners"]:
                    email = winner.get("email")
                    if not email and winner.get("student_id"):
                        email = EmailGenerator.generate_email_from_student_id(winner["student_id"])
                    
                    if email:
                        recipients.append({
                            "name": winner.get("name", ""),
                            "email": email,
                            "student_id": winner.get("student_id", ""),
                            "prize": prize_group["prize_name"]
                        })
            
            print(f"📧 準備發送給 {len(recipients)} 位收件人:")
            for i, recipient in enumerate(recipients[:5]):  # 只顯示前5位
                print(f"   {i+1}. {recipient['name']} <{recipient['email']}>")
            
            if len(recipients) > 5:
                print(f"   ... 還有 {len(recipients) - 5} 位收件人")
                
            print("✅ Email 通知功能測試完成（未實際發送）")
            
        except Exception as e:
            print(f"❌ Email 通知功能測試失敗: {str(e)}")
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
    finally:
        if 'conn' in locals():
            await conn.close()
            print("\n🔌 數據庫連接已關閉")

async def test_email_generation_rules():
    """測試各種學號格式的 email 生成規則"""
    print("\n=== 測試學號 Email 生成規則 ===")
    
    test_cases = [
        # (學號, 預期前綴, 學生類型)
        ("4101027415", "s", "大學部"),
        ("7101027416", "g", "研究所"),
        ("8101027417", "d", "博士班"),
        ("5101027418", "w", "在職專班"),
        ("3101027419", "n", "進修部"),
        ("s4101027415", "s", "大學部"),  # 已有前綴
        ("G7101027416", "g", "研究所"),  # 大寫前綴
        ("410102741", None, None),      # 學號太短
        ("9101027415", None, None),     # 不支援的開頭
        ("abc123", None, None),         # 無效格式
    ]
    
    print(f"{'學號':<15} {'生成Email':<35} {'學生類型':<20} {'狀態'}")
    print("-" * 80)
    
    for student_id, expected_prefix, expected_type in test_cases:
        email = EmailGenerator.generate_email_from_student_id(student_id)
        student_type = EmailGenerator.get_student_type_from_id(student_id)
        
        if email and expected_prefix:
            status = "✅" if email.startswith(expected_prefix) else "❌"
        elif not email and not expected_prefix:
            status = "✅"
        else:
            status = "❌"
            
        print(f"{student_id:<15} {email or 'None':<35} {student_type or 'None':<20} {status}")

async def main():
    """主測試函數"""
    print("🚀 開始測試 Email 自動生成功能\n")
    
    # 測試基本的 email 生成規則
    await test_email_generation_rules()
    
    # 測試實際中獎者的 email 生成
    await test_email_generation_for_winners()
    
    print("\n🎉 所有測試完成！")
    print("\n💡 使用說明:")
    print("1. 系統會自動根據學號第一位數字生成對應的 email 地址")
    print("2. 生成規則:")
    print("   - 4開頭: s{學號}@mail.nchu.edu.tw (大學部)")
    print("   - 7開頭: g{學號}@mail.nchu.edu.tw (研究所)")
    print("   - 8開頭: d{學號}@mail.nchu.edu.tw (博士班)")
    print("   - 5開頭: w{學號}@mail.nchu.edu.tw (在職專班)")
    print("   - 3開頭: n{學號}@mail.nchu.edu.tw (進修部)")
    print("3. 如果學號格式不符合規則，將無法生成 email 地址")
    print("4. 發送中獎通知時，系統會自動為每位中獎者生成對應的 email 地址")

if __name__ == "__main__":
    asyncio.run(main()) 