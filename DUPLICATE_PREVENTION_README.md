# 重複參與者去重功能

## 問題描述

在原本的 API 實現中，當多次上傳參與者時，如果同一個學號的學生已經在該活動中存在，系統會創建重複的參與者記錄。這會導致：

1. 資料庫中出現重複記錄
2. 參與者列表顯示同一個學生多次
3. 抽獎時可能抽到同一個人多次

## 解決方案

實現了「存在則更新，不存在則插入」的 upsert 邏輯，確保每個學號在同一個活動中只會有一筆記錄。

## 新增功能

### 1. 重複檢查機制

- 在批量添加參與者前，先查詢該活動中已存在的參與者
- 使用 `JSON_EXTRACT_PATH_TEXT` 從 meta 欄位中提取學號進行比對
- 建立學號到參與者記錄的映射表

### 2. 智能處理邏輯

- **新學號**：直接插入新的參與者記錄
- **已存在學號**：更新現有參與者的 meta 資料
- **Oracle 查詢失敗**：仍然跳過該學生

### 3. 詳細回應資訊

API 回應現在包含更詳細的處理資訊：

```json
{
  "imported": [...],
  "skipped": [...],
  "total_imported": 3,
  "total_skipped": 0,
  "inserted_count": 1,  // 新增的參與者數量
  "updated_count": 2    // 更新的參與者數量
}
```

## 實作細節

### 新增的 DAO 方法

#### `get_existing_participants_by_student_ids`

- 查詢指定活動中已存在的參與者
- 使用學號列表批量查詢，提升效能
- 返回學號到參與者記錄的映射表

#### `update_participant`

- 更新現有參與者的 meta 資料
- 保持參與者 ID 不變，只更新內容

#### `add_participants_batch` (修改)

- 加入重複檢查邏輯
- 分離插入和更新操作
- 提供詳細的處理統計

### 資料庫查詢優化

使用 PostgreSQL 的 JSON 操作符進行高效查詢：

```sql
SELECT id, event_id, meta, created_at
FROM lottery_participants
WHERE event_id = $1
AND meta->'student_info'->>'id' IN ($2, $3, ...)
```

JSON 操作符說明：

- `->` : 獲取 JSON 物件/陣列
- `->>` : 獲取 JSON 值為文字
- `meta->'student_info'` : 獲取 student_info 物件
- `->>'id'` : 提取 id 欄位為文字

## 使用範例

### 第一次上傳

```bash
curl -X POST "http://localhost:8000/lottery/events/{event_id}/participants" \
  -H "Content-Type: application/json" \
  -d '{
    "students": [
      {
        "id": "A12345678",
        "name": "張三",
        "department": "資訊工程系",
        "valid_surveys": "Y"
      },
      {
        "id": "B87654321",
        "name": "李四",
        "department": "電子工程系",
        "valid_surveys": "Y"
      }
    ]
  }'
```

**回應**：

```json
{
  "result": {
    "total_imported": 2,
    "total_skipped": 0,
    "inserted_count": 2,
    "updated_count": 0
  }
}
```

### 第二次上傳（包含重複）

```bash
curl -X POST "http://localhost:8000/lottery/events/{event_id}/participants" \
  -H "Content-Type: application/json" \
  -d '{
    "students": [
      {
        "id": "A12345678",
        "name": "張三 (更新)",
        "department": "資訊工程系",
        "required_surveys": 6,
        "valid_surveys": "Y"
      },
      {
        "id": "C11111111",
        "name": "王五",
        "department": "機械工程系",
        "valid_surveys": "Y"
      }
    ]
  }'
```

**回應**：

```json
{
  "result": {
    "total_imported": 2,
    "total_skipped": 0,
    "inserted_count": 1, // C11111111 (新)
    "updated_count": 1 // A12345678 (更新)
  }
}
```

## 測試

使用提供的測試腳本驗證功能：

```bash
python test_duplicate_participants.py
```

測試腳本會：

1. 創建測試活動
2. 第一次上傳 2 個參與者
3. 第二次上傳 3 個參與者（其中 2 個重複，1 個新的）
4. 驗證最終只有 3 個不重複的參與者
5. 確認重複的參與者資料被正確更新

## 效益

1. **資料一致性**：避免重複記錄，保持資料庫整潔
2. **用戶體驗**：參與者列表不會出現重複項目
3. **抽獎公平性**：每個學號只會被抽中一次
4. **資料更新**：支援更新學生的最新資訊（如問卷完成情況）
5. **向後相容**：現有的 API 使用方式完全不變

## 注意事項

1. 重複判斷基於學號（`student_info.id`）
2. 更新操作會完全替換 meta 資料
3. 參與者的 ID 和創建時間保持不變
4. 適用於所有活動類型（general 和 final_teaching）
5. Oracle 查詢失敗時的處理邏輯保持不變
