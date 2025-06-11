#!/usr/bin/env python3
import asyncio
import asyncpg
import random
import os
import csv
from faker import Faker
import uuid
from datetime import datetime, timedelta
import sys

# 設定 Faker 使用中文（台灣）
fake = Faker(['zh_TW'])

# 系所列表
departments = [
    "資訊工程學系", "電機工程學系", "機械工程學系", "土木工程學系", "化學工程學系",
    "財務金融學系", "企業管理學系", "會計學系", "國際企業學系", "經濟學系",
    "中國文學系", "外國語文學系", "歷史學系", "哲學系", "社會學系",
    "法律學系", "政治學系", "心理學系", "醫學系", "公共衛生學系",
    "數學系", "物理學系", "化學系", "生物學系", "地球科學系",
    "教育學系", "體育學系", "音樂學系", "美術學系", "戲劇學系"
]

# 年級列表
grades = ["大一", "大二", "大三", "大四", "碩一", "碩二", "博一", "博二", "博三"]

# 身份別列表
identity_types = ["本國生", "僑生", "外國學生", "陸生", "交換生"]

# 數據庫配置
DB_CONFIG = {
    "user": "local",
    "password": "local1234",
    "database": "postgres",
    "host": "localhost",
    "port": 5432
}

async def create_fake_students(conn, num_students=3000, export_csv=True):
    """創建假學生資料並插入數據庫，可選擇匯出為 CSV"""
    students = []
    all_students = []  # 用於CSV匯出
    print(f"開始生成 {num_students} 位學生的資料...")
    
    for i in range(num_students):
        # 創建基本學生資料
        student_id = f"{random.randint(100, 120)}{random.randint(1, 9)}{random.randint(10000, 99999)}"
        
        first_name = fake.last_name()
        last_name = fake.first_name()
        full_name = f"{first_name}{last_name}"
        
        department = random.choice(departments)
        grade = random.choice(grades)
        identity_type = random.choice(identity_types)
        id_number = fake.ssn() if identity_type == "本國生" else None
        address = fake.address()
        phone = fake.phone_number()
        email = f"{student_id}@university.edu.tw"

        student = {
            "id": student_id,
            "department": department,
            "name": full_name,
            "grade": grade,
            "id_number": id_number,
            "address": address,
            "identity_type": identity_type,
            "phone": phone,
            "email": email
        }
        students.append(student)
        all_students.append(student)
        
        # 每500筆做一次批量插入，以提高效率
        if len(students) >= 500:
            await insert_students(conn, students)
            print(f"已插入 {i+1} 位學生")
            students = []
    
    # 插入剩餘的學生數據
    if students:
        await insert_students(conn, students)
        print(f"已插入所有 {num_students} 位學生")
    
    # 匯出為 CSV
    if export_csv and all_students:
        export_students_to_csv(all_students)
    
    return num_students

async def insert_students(conn, students):
    """批量插入學生數據"""
    # 準備批量插入的參數
    values = []
    for student in students:
        values.append((
            student["id"],
            student["department"],
            student["name"],
            student["grade"],
            student["id_number"],
            student["address"],
            student["identity_type"],
            student["phone"],
            student["email"]
        ))
    
    # 執行批量插入
    await conn.executemany("""
        INSERT INTO student (id, department, name, grade, id_number, address, identity_type, phone, email)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        ON CONFLICT (id) DO NOTHING
    """, values)

def export_students_to_csv(students):
    """將學生資料匯出為 CSV 文件"""
    # 確保 exports 目錄存在
    os.makedirs("exports", exist_ok=True)
    
    # 生成時間戳為檔名一部分
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"exports/students_{timestamp}.csv"
    
    # 寫入 CSV
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ["id", "department", "name", "grade", "id_number", 
                     "address", "identity_type", "phone", "email"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for student in students:
            writer.writerow(student)
    
    print(f"學生資料已匯出至 {filename}")

async def export_existing_students_to_csv(conn):
    """從數據庫匯出現有學生資料為 CSV"""
    students = await conn.fetch("SELECT * FROM student")
    
    if not students:
        print("數據庫中沒有學生資料")
        return
    
    # 將數據庫結果轉換為字典列表
    student_dicts = []
    for student in students:
        student_dict = dict(student)
        # 移除 created_at 時間戳，因為CSV不需要
        if 'created_at' in student_dict:
            student_dict.pop('created_at')
        student_dicts.append(student_dict)
    
    # 匯出為 CSV
    export_students_to_csv(student_dicts)
    return len(student_dicts)

async def check_student_table_exists(conn):
    """檢查 student 表是否存在"""
    query = """
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'student'
    );
    """
    exists = await conn.fetchval(query)
    return exists

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
        table_exists = await check_student_table_exists(conn)
        if not table_exists:
            print("錯誤: student 表不存在。請先運行數據庫遷移腳本創建表結構。")
            return
        
        try:
            # 檢查數據庫中是否已有足夠的學生數據
            count = await conn.fetchval("SELECT COUNT(*) FROM student")
            print(f"數據庫中已有 {count} 位學生")
            
            if count >= 3000:
                print("數據庫中已有足夠的學生數據，是否要匯出現有資料為 CSV？(y/n)")
                user_input = input().strip().lower()
                if user_input == 'y':
                    num_exported = await export_existing_students_to_csv(conn)
                    print(f"已匯出 {num_exported} 位學生的資料")
            else:
                # 生成並插入假學生數據
                num_to_create = 3000 - count
                num_created = await create_fake_students(conn, num_to_create)
                print(f"成功生成並插入 {num_created} 位假學生資料")
        
        finally:
            # 關閉數據庫連接
            await conn.close()
    
    except Exception as e:
        print(f"連接數據庫時發生錯誤: {str(e)}")
        print("請確保數據庫服務正在運行，並且連接信息正確。")

if __name__ == "__main__":
    # 執行主函數
    asyncio.run(main()) 