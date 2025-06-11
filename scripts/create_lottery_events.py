#!/usr/bin/env python3
import asyncio
import asyncpg
import random
import sys
import uuid
import json
from datetime import datetime, timedelta

# 數據庫配置
DB_CONFIG = {
    "user": "local",
    "password": "local1234",
    "database": "postgres",
    "host": "localhost",
    "port": 5432
}

async def check_tables_exist(conn):
    """檢查所需表格是否存在"""
    tables = ['lottery_events', 'lottery_participants', 'lottery_prizes']
    all_exist = True
    
    for table in tables:
        query = """
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = $1
        );
        """
        exists = await conn.fetchval(query, table)
        if not exists:
            print(f"錯誤: {table} 表不存在")
            all_exist = False
    
    return all_exist

async def generate_fake_student_data():
    """生成假的學生資料"""
    departments = [
        "資訊工程學系", "電機工程學系", "機械工程學系", "化學工程學系", "土木工程學系",
        "企業管理學系", "會計學系", "財務金融學系", "國際貿易學系", "經濟學系",
        "中國文學系", "外國語文學系", "歷史學系", "哲學系", "藝術學系",
        "數學系", "物理學系", "化學系", "生物學系", "心理學系"
    ]
    
    grades = ["大一", "大二", "大三", "大四", "碩一", "碩二", "博一", "博二", "博三"]
    
    # 生成中文姓名
    surnames = ["王", "李", "張", "劉", "陳", "楊", "趙", "黃", "周", "吳", "徐", "孫", "胡", "朱", "高", "林", "何", "郭", "馬", "羅"]
    given_names = ["志明", "春嬌", "小明", "小華", "小美", "小芳", "建國", "淑芬", "雅婷", "怡君", "俊傑", "美玲", "家豪", "佳穎", "宗翰", "雅雯", "承翰", "詩涵", "冠宇", "欣怡"]
    
    students = []
    for i in range(3000):
        student_id = f"S{i+1:06d}"  # S000001, S000002, ...
        name = random.choice(surnames) + random.choice(given_names)
        department = random.choice(departments)
        grade = random.choice(grades)
        
        students.append({
            "id": student_id,
            "name": name,
            "department": department,
            "grade": grade
        })
    
    return students

async def create_lottery_events(conn):
    """創建兩個抽獎活動"""
    # 創建一般抽獎活動
    regular_event_id = str(uuid.uuid4())
    regular_event_name = "期末學生活動抽獎"
    regular_event_desc = "參與校園活動的學生抽獎活動"
    regular_event_date = datetime.now() + timedelta(days=10)
    academic_year_term = "112-2"  # 112學年第2學期
    
    # 創建教學評量抽獎活動
    teaching_event_id = str(uuid.uuid4())
    teaching_event_name = "期末教學評量抽獎"
    teaching_event_desc = "填寫期末教學評量問卷的學生抽獎活動"
    teaching_event_date = datetime.now() + timedelta(days=15)
    
    # 插入抽獎活動
    await conn.execute("""
    INSERT INTO lottery_events (id, academic_year_term, name, description, event_date, type, status)
    VALUES ($1, $2, $3, $4, $5, 'general', 'pending')
    ON CONFLICT (id) DO NOTHING
    """, regular_event_id, academic_year_term, regular_event_name, regular_event_desc, regular_event_date)
    
    await conn.execute("""
    INSERT INTO lottery_events (id, academic_year_term, name, description, event_date, type, status)
    VALUES ($1, $2, $3, $4, $5, 'final_teaching', 'pending')
    ON CONFLICT (id) DO NOTHING
    """, teaching_event_id, academic_year_term, teaching_event_name, teaching_event_desc, teaching_event_date)
    
    print(f"已創建一般抽獎活動: ID={regular_event_id}, 名稱={regular_event_name}")
    print(f"已創建教學評量抽獎活動: ID={teaching_event_id}, 名稱={teaching_event_name}")
    
    return regular_event_id, teaching_event_id

async def add_participants(conn, regular_event_id, teaching_event_id, regular_count=1000, teaching_count=1500):
    """添加參與者到抽獎活動，使用 meta 欄位存儲學生資訊"""
    # 生成假學生資料
    all_students = await generate_fake_student_data()
    random.shuffle(all_students)
    
    # 確保數量不超過可用學生數
    total_students = len(all_students)
    if regular_count + teaching_count > total_students:
        teaching_count = min(teaching_count, total_students // 2)
        regular_count = min(regular_count, total_students - teaching_count)
        print(f"警告: 請求的參與者數量超過可用學生數，已調整為: 一般抽獎={regular_count}, 教學評量抽獎={teaching_count}")
    
    # 分配學生到兩個抽獎活動
    regular_students = all_students[:regular_count]
    teaching_students = all_students[regular_count:regular_count+teaching_count]
    
    # 為一般抽獎添加參與者
    regular_added = 0
    for student in regular_students:
        try:
            meta = {
                "student_info": {
                    "id": student["id"],
                    "name": student["name"],
                    "department": student["department"],
                    "grade": student["grade"]
                }
            }
            
            await conn.execute("""
            INSERT INTO lottery_participants (event_id, meta)
            VALUES ($1, $2)
            """, regular_event_id, json.dumps(meta))
            regular_added += 1
        except Exception as e:
            print(f"添加參與者時出錯: {e}")
    
    # 為教學評量抽獎添加參與者和評量記錄
    teaching_added = 0
    for student in teaching_students:
        try:
            # 隨機生成評量資料
            required_surveys = random.randint(3, 8)
            completed_surveys = random.randint(0, required_surveys)
            surveys_completed = completed_surveys >= required_surveys
            valid_surveys = surveys_completed and random.random() > 0.05  # 95% 有效問卷
            
            meta = {
                "student_info": {
                    "id": student["id"],
                    "name": student["name"],
                    "department": student["department"],
                    "grade": student["grade"]
                },
                "teaching_comments": {
                    "required_surveys": required_surveys,
                    "completed_surveys": completed_surveys,
                    "surveys_completed": surveys_completed,
                    "valid_surveys": valid_surveys
                }
            }
            
            await conn.execute("""
            INSERT INTO lottery_participants (event_id, meta)
            VALUES ($1, $2)
            """, teaching_event_id, json.dumps(meta))
            
            teaching_added += 1
        except Exception as e:
            print(f"添加教學評量參與者時出錯: {e}")
    
    print(f"已為一般抽獎活動添加 {regular_added} 位參與者")
    print(f"已為教學評量抽獎活動添加 {teaching_added} 位參與者，並生成問卷記錄")
    
    return regular_added, teaching_added

async def create_prizes(conn, regular_event_id, teaching_event_id):
    """為抽獎活動創建獎品"""
    # 一般抽獎獎品
    regular_prizes = [
        ("頭獎 - iPad", 1),
        ("二獎 - AirPods", 3),
        ("三獎 - 禮券 1000元", 10),
        ("四獎 - 禮券 500元", 20),
        ("五獎 - 校園週邊商品", 30)
    ]
    
    # 教學評量抽獎獎品
    teaching_prizes = [
        ("特獎 - MacBook Air", 1),
        ("一獎 - iPhone", 2),
        ("二獎 - iPad", 5),
        ("三獎 - AirPods", 10),
        ("四獎 - 禮券 2000元", 20),
        ("五獎 - 禮券 1000元", 30),
        ("六獎 - 禮券 500元", 50)
    ]
    
    # 為一般抽獎添加獎品
    for name, quantity in regular_prizes:
        await conn.execute("""
        INSERT INTO lottery_prizes (event_id, name, quantity)
        VALUES ($1, $2, $3)
        """, regular_event_id, name, quantity)
    
    # 為教學評量抽獎添加獎品
    for name, quantity in teaching_prizes:
        await conn.execute("""
        INSERT INTO lottery_prizes (event_id, name, quantity)
        VALUES ($1, $2, $3)
        """, teaching_event_id, name, quantity)
    
    print(f"已為一般抽獎活動添加 {len(regular_prizes)} 個獎項")
    print(f"已為教學評量抽獎活動添加 {len(teaching_prizes)} 個獎項")

async def main():
    """主函數"""
    # 解析命令行參數
    host = DB_CONFIG["host"]
    port = DB_CONFIG["port"]
    
    # 如果有提供參數，使用命令行中的 host 和 port
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"錯誤: 無效的端口號 '{sys.argv[2]}'，使用默認端口 {port}")
    
    print(f"嘗試連接到數據庫 {host}:{port}...")
    
    try:
        # 連接數據庫
        conn = await asyncpg.connect(
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            host=host,
            port=port
        )
        
        print("成功連接到數據庫！")
        
        # 檢查表是否存在
        tables_exist = await check_tables_exist(conn)
        if not tables_exist:
            print("錯誤: 必要的表結構不存在。請先運行數據庫遷移腳本。")
            return
        
        try:
            # 創建抽獎活動
            regular_event_id, teaching_event_id = await create_lottery_events(conn)
            
            # 添加參與者
            regular_added, teaching_added = await add_participants(conn, regular_event_id, teaching_event_id)
            
            # 創建獎品
            await create_prizes(conn, regular_event_id, teaching_event_id)
            
            print("\n數據生成摘要:")
            print("="*50)
            print(f"一般抽獎活動 ID: {regular_event_id}")
            print(f"教學評量抽獎活動 ID: {teaching_event_id}")
            print(f"一般抽獎參與者: {regular_added}人")
            print(f"教學評量參與者: {teaching_added}人 (含問卷記錄)")
            print("="*50)
            
        finally:
            # 關閉數據庫連接
            await conn.close()
    
    except Exception as e:
        print(f"連接數據庫時發生錯誤: {str(e)}")
        print("請確保數據庫服務正在運行，並且連接信息正確。")

if __name__ == "__main__":
    # 執行主函數
    asyncio.run(main()) 