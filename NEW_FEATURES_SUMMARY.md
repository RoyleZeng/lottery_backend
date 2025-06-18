# 新功能實現總結

本次更新為抽獎系統新增了兩個重要功能：

## 1. Event 軟刪除功能

### 功能說明

- 實現了軟刪除機制，刪除活動時不會真正從資料庫中移除，而是設置 `is_deleted` 標記
- 在取得活動列表時會自動排除被軟刪除的活動
- 提供恢復功能，可以將被軟刪除的活動恢復

### 技術實現

#### 資料庫變更

- 為 `lottery_events` 表新增 `is_deleted` 欄位（BOOLEAN，預設 FALSE）
- 新增索引 `idx_lottery_events_is_deleted` 提升查詢效能

#### API 端點

1. **軟刪除活動**

   ```
   DELETE /lottery/events/{event_id}
   ```

   - 將活動的 `is_deleted` 設為 TRUE
   - 返回刪除確認訊息

2. **恢復活動**

   ```
   PUT /lottery/events/{event_id}/restore
   ```

   - 將活動的 `is_deleted` 設為 FALSE
   - 返回恢復確認訊息

3. **獲取被軟刪除的活動**
   ```
   GET /lottery/deleted-events
   ```
   - 支援分頁參數 `limit` 和 `offset`
   - 返回所有被軟刪除的活動列表

#### 代碼修改

- **DAO 層**：更新所有查詢以排除軟刪除的活動
- **Business 層**：新增軟刪除和恢復的業務邏輯
- **Schema**：新增 `SoftDeleteEventResponse` 模型
- **Endpoints**：新增相關 API 端點

### 使用範例

```bash
# 軟刪除活動
curl -X DELETE "http://localhost:8000/lottery/events/{event_id}"

# 恢復活動
curl -X PUT "http://localhost:8000/lottery/events/{event_id}/restore"

# 查看被軟刪除的活動
curl -X GET "http://localhost:8000/lottery/deleted-events"
```

## 2. Email 測試 API 功能

### 功能說明

- 新增測試中獎通知郵件的 API
- 功能與正式發送 API 相同，但最後是發送給前端指定的測試收件人清單
- 使用實際中獎者資料作為模板變數，但發送給測試郵箱

### 技術實現

#### API 端點

```
POST /email/test-winners/{event_id}
```

#### 請求參數

```json
{
  "email_config": {
    "smtp_server": "dragon.nchu.edu.tw",
    "smtp_port": 465,
    "username": "your-email@dragon.nchu.edu.tw",
    "password": "your-password",
    "use_tls": true
  },
  "sender_name": "測試抽獎系統",
  "subject": "🎉 中獎通知測試 - {{winner_name}} 獲得 {{prize_name}}",
  "email_template": "自定義文字模板...",
  "html_template": "自定義 HTML 模板...",
  "test_recipients": ["test1@example.com", "test2@example.com"]
}
```

#### 功能特點

1. **使用真實中獎者資料**：從資料庫獲取實際中獎者資料作為模板變數
2. **發送給測試收件人**：不會發送給真實中獎者，而是發送給指定的測試郵箱
3. **完整模板支援**：支援所有模板變數和自定義模板
4. **測試標記**：郵件內容會自動加上測試標記，避免混淆

#### 代碼修改

- **Schema**：新增 `TestWinnersEmailRequest` 模型
- **Business 層**：新增 `test_winners_notification` 方法
- **Endpoints**：新增測試 API 端點

### 使用範例

```bash
curl -X POST "http://localhost:8000/email/test-winners/{event_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "email_config": {
      "smtp_server": "dragon.nchu.edu.tw",
      "smtp_port": 465,
      "username": "test@dragon.nchu.edu.tw",
      "password": "test-password",
      "use_tls": true
    },
    "sender_name": "測試抽獎系統",
    "subject": "🎉 中獎通知測試",
    "test_recipients": ["test@example.com"]
  }'
```

## 測試結果

### 軟刪除功能測試

✅ 軟刪除活動成功  
✅ 活動從正常列表中消失  
✅ 被軟刪除的活動可正確查詢  
✅ 活動恢復功能正常  
✅ 恢復後活動重新出現在正常列表中

### Email 測試 API 功能測試

✅ 測試 API 端點正常運作  
✅ 使用真實中獎者資料生成模板  
✅ 發送給指定測試收件人  
✅ 郵件內容包含測試標記  
✅ 模板變數正確替換

## 部署說明

### 資料庫遷移

需要執行以下 SQL 來新增軟刪除欄位：

```sql
-- 新增 is_deleted 欄位
ALTER TABLE lottery_events ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- 新增索引
CREATE INDEX IF NOT EXISTS idx_lottery_events_is_deleted ON lottery_events(is_deleted);
```

### API 文檔更新

新的 API 端點已自動加入到 Swagger 文檔中，可透過 `/api/spec/doc` 查看完整 API 說明。

## 安全考量

### 軟刪除

- 軟刪除的活動仍存在於資料庫中，包含所有相關資料
- 只有具備適當權限的使用者才能查看和恢復被軟刪除的活動
- 建議定期清理長期被軟刪除的活動資料

### Email 測試

- 測試 API 使用與正式 API 相同的認證機制
- 測試郵件會明確標示為測試內容，避免混淆
- 建議使用專用的測試郵箱進行測試

## 後續建議

1. **軟刪除功能**

   - 考慮新增批量軟刪除功能
   - 新增軟刪除時間記錄
   - 實現自動清理機制

2. **Email 測試功能**
   - 新增更多測試模式（如只發送給單一測試收件人）
   - 新增測試報告功能
   - 考慮新增預覽功能（不實際發送郵件）

這兩個新功能大幅提升了系統的可用性和測試便利性，為管理者提供了更好的管理工具。
