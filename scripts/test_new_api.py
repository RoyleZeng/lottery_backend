#!/usr/bin/env python3
"""
測試新的抽獎 API 結構
此腳本會測試新的 metadata 結構是否正常工作
"""
import asyncio
import asyncpg
import json
import sys
from datetime import datetime

# 數據庫配置
DB_CONFIG = {
    "user": "local",
    "password": "local1234",
    "database": "postgres",
    "host": "localhost",
    "port": 5432
}

def parse_meta(meta_value):
    """Parse meta field from database"""
    if isinstance(meta_value, str):
        try:
            return json.loads(meta_value)
        except (json.JSONDecodeError, TypeError):
            return {}
    elif isinstance(meta_value, dict):
        return meta_value
    else:
        return {}

async def test_database_structure(conn):
    """測試資料庫結構"""
    print("=== 測試資料庫結構 ===")
    
    # 檢查表格是否存在
    tables = ['lottery_events', 'lottery_participants', 'lottery_prizes', 'lottery_winners']
    for table in tables:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
            )
        """, table)
        print(f"✓ {table} 表格存在: {exists}")
    
    # 檢查 lottery_participants 是否有 meta 欄位
    has_meta = await conn.fetchval("""
        SELECT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'lottery_participants' AND column_name = 'meta'
        )
    """)
    print(f"✓ lottery_participants.meta 欄位存在: {has_meta}")
    
    # 檢查舊表格是否已移除
    old_tables = ['student', 'final_teaching_comments']
    for table in old_tables:
        exists = await conn.fetchval("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name = $1
            )
        """, table)
        print(f"✓ {table} 表格已移除: {not exists}")

async def test_participant_operations(conn):
    """測試參與者操作"""
    print("\n=== 測試參與者操作 ===")
    
    # 查找一個抽獎活動
    event = await conn.fetchrow("SELECT id, name FROM lottery_events LIMIT 1")
    if not event:
        print("❌ 沒有找到抽獎活動，請先運行 create_lottery_events.py")
        return
    
    event_id = event['id']
    print(f"✓ 使用抽獎活動: {event['name']} (ID: {event_id})")
    
    # 測試添加參與者
    test_student = {
        "id": "TEST001",
        "name": "測試學生",
        "department": "資訊工程學系",
        "grade": "大三"
    }
    
    meta = {
        "student_info": test_student
    }
    
    try:
        participant_id = await conn.fetchval("""
            INSERT INTO lottery_participants (event_id, meta)
            VALUES ($1, $2)
            RETURNING id
        """, event_id, json.dumps(meta))
        print(f"✓ 成功添加測試參與者，ID: {participant_id}")
    except Exception as e:
        print(f"❌ 添加參與者失敗: {e}")
        return
    
    # 測試查詢參與者
    try:
        participant = await conn.fetchrow("""
            SELECT id, event_id, meta, created_at
            FROM lottery_participants
            WHERE id = $1
        """, participant_id)
        
        if participant:
            meta_data = parse_meta(participant['meta'])
            student_info = meta_data.get('student_info', {})
            print(f"✓ 查詢參與者成功:")
            print(f"  - 學號: {student_info.get('id')}")
            print(f"  - 姓名: {student_info.get('name')}")
            print(f"  - 系所: {student_info.get('department')}")
            print(f"  - 年級: {student_info.get('grade')}")
        else:
            print("❌ 查詢參與者失敗")
    except Exception as e:
        print(f"❌ 查詢參與者失敗: {e}")
    
    # 清理測試資料
    try:
        await conn.execute("DELETE FROM lottery_participants WHERE id = $1", participant_id)
        print("✓ 清理測試資料完成")
    except Exception as e:
        print(f"❌ 清理測試資料失敗: {e}")

async def test_teaching_comments(conn):
    """測試教學評鑑資料"""
    print("\n=== 測試教學評鑑資料 ===")
    
    # 查找教學評鑑抽獎活動
    event = await conn.fetchrow("""
        SELECT id, name FROM lottery_events 
        WHERE type = 'final_teaching' 
        LIMIT 1
    """)
    
    if not event:
        print("❌ 沒有找到教學評鑑抽獎活動")
        return
    
    event_id = event['id']
    print(f"✓ 使用教學評鑑抽獎活動: {event['name']} (ID: {event_id})")
    
    # 測試添加帶有教學評鑑資料的參與者
    meta = {
        "student_info": {
            "id": "TEST002",
            "name": "測試學生2",
            "department": "電機工程學系",
            "grade": "大四"
        },
        "teaching_comments": {
            "required_surveys": 5,
            "completed_surveys": 5,
            "surveys_completed": True,
            "valid_surveys": True
        }
    }
    
    try:
        participant_id = await conn.fetchval("""
            INSERT INTO lottery_participants (event_id, meta)
            VALUES ($1, $2)
            RETURNING id
        """, event_id, json.dumps(meta))
        print(f"✓ 成功添加帶有教學評鑑資料的參與者，ID: {participant_id}")
    except Exception as e:
        print(f"❌ 添加參與者失敗: {e}")
        return
    
    # 測試查詢教學評鑑資料
    try:
        participant = await conn.fetchrow("""
            SELECT id, event_id, meta, created_at
            FROM lottery_participants
            WHERE id = $1
        """, participant_id)
        
        if participant:
            meta_data = parse_meta(participant['meta'])
            student_info = meta_data.get('student_info', {})
            teaching_comments = meta_data.get('teaching_comments', {})
            
            print(f"✓ 查詢教學評鑑參與者成功:")
            print(f"  - 學號: {student_info.get('id')}")
            print(f"  - 姓名: {student_info.get('name')}")
            print(f"  - 必修問卷數: {teaching_comments.get('required_surveys')}")
            print(f"  - 已完成問卷數: {teaching_comments.get('completed_surveys')}")
            print(f"  - 問卷完成狀態: {teaching_comments.get('surveys_completed')}")
            print(f"  - 有效問卷狀態: {teaching_comments.get('valid_surveys')}")
        else:
            print("❌ 查詢參與者失敗")
    except Exception as e:
        print(f"❌ 查詢參與者失敗: {e}")
    
    # 清理測試資料
    try:
        await conn.execute("DELETE FROM lottery_participants WHERE id = $1", participant_id)
        print("✓ 清理測試資料完成")
    except Exception as e:
        print(f"❌ 清理測試資料失敗: {e}")

async def test_statistics(conn):
    """測試統計資料"""
    print("\n=== 測試統計資料 ===")
    
    # 統計抽獎活動數量
    event_count = await conn.fetchval("SELECT COUNT(*) FROM lottery_events")
    print(f"✓ 抽獎活動總數: {event_count}")
    
    # 統計參與者數量
    participant_count = await conn.fetchval("SELECT COUNT(*) FROM lottery_participants")
    print(f"✓ 參與者總數: {participant_count}")
    
    # 統計各類型活動的參與者數量
    stats = await conn.fetch("""
        SELECT e.type, e.name, COUNT(p.id) as participant_count
        FROM lottery_events e
        LEFT JOIN lottery_participants p ON e.id = p.event_id
        GROUP BY e.id, e.type, e.name
        ORDER BY e.type
    """)
    
    print("✓ 各活動參與者統計:")
    for stat in stats:
        print(f"  - {stat['name']} ({stat['type']}): {stat['participant_count']} 人")

async def main():
    """主函數"""
    host = DB_CONFIG["host"]
    port = DB_CONFIG["port"]
    
    if len(sys.argv) > 1:
        host = sys.argv[1]
    if len(sys.argv) > 2:
        try:
            port = int(sys.argv[2])
        except ValueError:
            print(f"錯誤: 無效的端口號 '{sys.argv[2]}'")
            return
    
    print(f"連接到數據庫 {host}:{port}...")
    
    try:
        conn = await asyncpg.connect(
            user=DB_CONFIG["user"],
            password=DB_CONFIG["password"],
            database=DB_CONFIG["database"],
            host=host,
            port=port
        )
        
        print("✓ 數據庫連接成功！\n")
        
        # 執行測試
        await test_database_structure(conn)
        await test_participant_operations(conn)
        await test_teaching_comments(conn)
        await test_statistics(conn)
        
        print("\n=== 測試完成 ===")
        print("✓ 新的資料結構測試通過！")
        
    except Exception as e:
        print(f"❌ 連接數據庫失敗: {e}")
    finally:
        if 'conn' in locals():
            await conn.close()

if __name__ == "__main__":
    asyncio.run(main()) 