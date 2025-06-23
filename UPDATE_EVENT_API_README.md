# 更新 Event API 文檔

## 新增功能

新增了 `PUT /lottery/events/{event_id}` API 端點，用於更新現有的抽獎活動資訊。

## API 端點

### PUT /lottery/events/{event_id}

更新指定的抽獎活動。

#### 請求參數

- **路徑參數**：

  - `event_id` (string): 抽獎活動的 UUID

- **請求主體** (JSON):
  ```json
  {
    "academic_year_term": "113-2", // 可選：學年期
    "name": "更新後的活動名稱", // 可選：活動名稱
    "description": "更新後的活動描述", // 可選：活動描述
    "event_date": "2024-07-15T10:00:00", // 可選：活動日期 (ISO 8601 格式)
    "type": "general" // 可選：活動類型 ("general" 或 "final_teaching")
  }
  ```

#### 回應

- **成功 (200)**:

  ```json
  {
    "result": {
      "id": "event-uuid",
      "academic_year_term": "113-2",
      "name": "更新後的活動名稱",
      "description": "更新後的活動描述",
      "event_date": "2024-07-15T10:00:00",
      "type": "general",
      "status": "pending",
      "is_deleted": false,
      "created_at": "2024-06-20T10:00:00"
    }
  }
  ```

- **錯誤回應**:
  - `404 Not Found`: 活動不存在
  - `400 Bad Request`: 無法更新已抽獎的活動

#### 功能特點

1. **部分更新**：只需提供要更新的欄位，其他欄位保持不變
2. **完整更新**：可以同時更新所有欄位
3. **保護機制**：無法更新已經抽獎（status = "drawn"）的活動
4. **驗證**：自動驗證輸入資料的格式和類型

## 使用範例

### 1. 只更新活動名稱

```bash
curl -X PUT "http://localhost:8000/lottery/events/{event_id}" \
  -H "Content-Type: application/json" \
  -d '{"name": "新的活動名稱"}'
```

### 2. 更新多個欄位

```bash
curl -X PUT "http://localhost:8000/lottery/events/{event_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "期末教學評量抽獎",
    "description": "113學年度第2學期期末教學評量抽獎活動",
    "type": "final_teaching"
  }'
```

### 3. 完整更新

```bash
curl -X PUT "http://localhost:8000/lottery/events/{event_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "academic_year_term": "113-2",
    "name": "期末教學評量抽獎",
    "description": "113學年度第2學期期末教學評量抽獎活動",
    "event_date": "2024-07-15T14:00:00",
    "type": "final_teaching"
  }'
```

## 測試

使用提供的測試腳本來測試 API：

```bash
python test_update_event_api.py
```

該腳本會自動：

1. 創建測試活動
2. 測試部分更新
3. 測試完整更新
4. 測試空更新
5. 測試更新不存在的活動
6. 顯示最終狀態

## 限制

1. 無法更新已經抽獎的活動（status = "drawn"）
2. 所有欄位都是可選的，但至少需要提供一個欄位
3. 無法更新已軟刪除的活動（is_deleted = true）
4. 日期格式必須符合 ISO 8601 標準
5. 活動類型只能是 "general" 或 "final_teaching"

## 實作細節

### 資料庫層 (DAO)

- 新增 `update_lottery_event` 方法
- 使用動態 SQL 建構只更新提供的欄位
- 確保只更新未軟刪除的活動

### 業務邏輯層 (Business)

- 新增 `update_lottery_event` 方法
- 檢查活動是否存在
- 防止更新已抽獎的活動
- 處理列舉類型轉換

### API 層 (Endpoints)

- 新增 PUT 端點
- 使用 `LotteryEventUpdate` schema 驗證輸入
- 適當的錯誤處理和狀態碼回應
