# 抽獎系統資料結構變更說明

## 變更概述

原本的抽獎系統使用了獨立的 `student` 和 `final_teaching_comments` 表格來存儲學生資訊和教學評鑑資料。為了簡化資料結構並移除個人敏感資訊，我們已將這些資訊整合到 `lottery_participants` 表格的 `meta` 欄位中。

## 主要變更

### 1. 移除的表格
- `student` - 學生基本資料表
- `final_teaching_comments` - 期末教學評鑑表

### 2. 保留的表格
- `lottery_events` - 抽獎活動表
- `lottery_participants` - 參與者表（新增 `meta` 欄位）
- `lottery_prizes` - 獎品表
- `lottery_winners` - 中獎者表

### 3. 新的資料結構

#### lottery_participants 表格
```sql
CREATE TABLE lottery_participants (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR NOT NULL REFERENCES lottery_events(id) ON DELETE CASCADE,
    meta jsonb DEFAULT '{}'::jsonb NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### meta 欄位結構
```json
{
  "student_info": {
    "id": "學號",
    "name": "姓名",
    "department": "系所",
    "grade": "年級"
  },
  "teaching_comments": {  // 僅教學評鑑抽獎需要
    "required_surveys": 3,
    "completed_surveys": 3,
    "surveys_completed": true,
    "valid_surveys": true
  }
}
```

### 4. 移除的個人資訊欄位
為了保護隱私，以下欄位已被移除：
- `id_number` - 身份證字號
- `address` - 戶籍地址
- `identity_type` - 身份別
- `phone` - 手機號碼
- `email` - 電子郵件

## 遷移步驟

### 1. 執行資料庫遷移
```bash
# 移除舊表格並更新結構
psql -h localhost -p 5432 -U local -d postgres -f db_migrations/remove_old_tables.sql
```

### 2. 創建新的抽獎活動和參與者
```bash
# 使用新的腳本創建測試資料
python scripts/create_lottery_events.py
```

## API 變更

### 學生資料導入
原本需要先創建學生記錄再添加參與者，現在直接將學生資訊作為參與者的 metadata 存儲：

```python
# 舊方式
student = await LotteryDAO.get_or_create_student(conn, student_data)
participant = await LotteryDAO.add_participant(conn, event_id, student['id'])

# 新方式
participant = await LotteryDAO.add_participant(conn, event_id, student_data)
```

### 查詢參與者
查詢結果會自動將 meta 欄位中的資訊展開為平面結構，保持 API 回應格式的一致性。

## 優勢

1. **簡化資料結構** - 減少表格數量和關聯複雜度
2. **保護隱私** - 移除敏感個人資訊
3. **靈活性** - JSONB 欄位可以輕鬆擴展新的 metadata
4. **效能** - 減少 JOIN 查詢，提升查詢效能
5. **維護性** - 更簡潔的資料模型，易於維護

## 注意事項

1. 現有的資料會在執行遷移腳本時被清除
2. 新的結構不再支援學生資料的獨立管理
3. 所有學生資訊都與特定的抽獎活動綁定
4. 如需要學生資料的持久化存儲，請考慮其他解決方案 