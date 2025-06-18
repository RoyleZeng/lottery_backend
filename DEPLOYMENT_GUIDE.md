# 抽獎系統部署指南

本指南將幫助您在目標虛擬機上部署最新版本的抽獎系統，包含新的軟刪除功能和 Email 測試 API。

## 🚀 新功能概覽

本次更新包含以下新功能：

1. **Event 軟刪除功能** - 支援軟刪除和恢復活動
2. **Email 測試 API** - 測試中獎通知郵件功能
3. **郵件標頭修復** - 修復 Gmail RFC 5322 規範問題

## 📋 部署前準備

### 1. 系統要求

- Python 3.9+
- PostgreSQL 12+
- Git
- 網路連接

### 2. 檢查當前版本

```bash
cd /path/to/lottery_backend
git log --oneline -5
```

## 🔄 部署步驟

### 步驟 1: 停止當前服務

```bash
# 如果使用 systemd
sudo systemctl stop lottery-backend

# 或者手動停止進程
pkill -f "python -m lottery_api.main"
```

### 步驟 2: 備份數據庫（建議）

```bash
# 備份 PostgreSQL 數據庫
pg_dump -h localhost -U your_username -d your_database > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 步驟 3: 拉取最新代碼

```bash
cd /path/to/lottery_backend
git fetch origin
git pull origin main
```

### 步驟 4: 更新依賴（如有需要）

```bash
# 激活虛擬環境
source .venv/bin/activate

# 更新依賴
pip install -r requirements.txt
```

### 步驟 5: 執行資料庫遷移

```bash
# 連接到 PostgreSQL 並執行遷移
psql -h localhost -U your_username -d your_database -f db_migrations/add_soft_delete_column.sql
```

或者手動執行 SQL：

```sql
-- 新增 is_deleted 欄位
ALTER TABLE lottery_events ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- 新增索引提升查詢效能
CREATE INDEX IF NOT EXISTS idx_lottery_events_is_deleted ON lottery_events(is_deleted);

-- 驗證變更
SELECT id, name, type, status, is_deleted FROM lottery_events LIMIT 5;
```

### 步驟 6: 測試部署

```bash
# 激活虛擬環境
source .venv/bin/activate

# 啟動服務器（測試模式）
python -m lottery_api.main
```

在另一個終端中測試：

```bash
# 測試基本 API
curl -X GET "http://localhost:8000/lottery/events" | jq '.'

# 測試新的軟刪除 API
curl -X GET "http://localhost:8000/lottery/deleted-events" | jq '.'
```

### 步驟 7: 啟動生產服務

```bash
# 停止測試服務器（Ctrl+C）

# 如果使用 systemd
sudo systemctl start lottery-backend
sudo systemctl enable lottery-backend

# 或者使用 screen/tmux 在後台運行
screen -S lottery-backend
python -m lottery_api.main
# 按 Ctrl+A, D 離開 screen
```

## 🧪 功能測試

### 測試軟刪除功能

```bash
# 運行完整功能測試
python test_new_features.py
```

### 測試郵件功能

```bash
# 測試郵件修復（需要更新郵件憑證）
python test_email_fix.py
```

### 手動測試新 API

1. **軟刪除活動**

```bash
curl -X DELETE "http://localhost:8000/lottery/events/{event_id}"
```

2. **查看被軟刪除的活動**

```bash
curl -X GET "http://localhost:8000/lottery/deleted-events"
```

3. **恢復活動**

```bash
curl -X PUT "http://localhost:8000/lottery/events/{event_id}/restore"
```

4. **測試中獎通知郵件**

```bash
curl -X POST "http://localhost:8000/email/test-winners/{event_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "email_config": {
      "smtp_server": "dragon.nchu.edu.tw",
      "smtp_port": 465,
      "username": "your-email@dragon.nchu.edu.tw",
      "password": "your-password",
      "use_tls": true
    },
    "sender_name": "抽獎系統",
    "subject": "測試郵件",
    "test_recipients": ["test@example.com"]
  }'
```

## 📊 監控和驗證

### 檢查服務狀態

```bash
# 如果使用 systemd
sudo systemctl status lottery-backend

# 檢查日志
sudo journalctl -u lottery-backend -f

# 或者檢查進程
ps aux | grep lottery_api
```

### 檢查 API 健康狀態

```bash
# 檢查 API 文檔
curl -I "http://localhost:8000/api/spec/doc"

# 檢查活動列表
curl -X GET "http://localhost:8000/lottery/events" | jq '.result | length'
```

### 驗證數據庫變更

```sql
-- 檢查新欄位
\d lottery_events

-- 檢查索引
\di lottery_events*

-- 檢查數據
SELECT
    COUNT(*) as total_events,
    COUNT(*) FILTER (WHERE is_deleted = false) as active_events,
    COUNT(*) FILTER (WHERE is_deleted = true) as deleted_events
FROM lottery_events;
```

## 🔧 故障排除

### 常見問題

1. **資料庫連接問題**

```bash
# 檢查 PostgreSQL 服務
sudo systemctl status postgresql

# 檢查連接
psql -h localhost -U your_username -d your_database -c "SELECT 1;"
```

2. **郵件發送問題**

```bash
# 測試郵件伺服器連接
curl -X POST "http://localhost:8000/email/test-connection" \
  -H "Content-Type: application/json" \
  -d '{"smtp_server":"dragon.nchu.edu.tw","smtp_port":465,"username":"test","password":"test","use_tls":true}'
```

3. **API 無法訪問**

```bash
# 檢查端口佔用
netstat -tlnp | grep :8000

# 檢查防火牆
sudo ufw status
```

### 回滾步驟（如果需要）

```bash
# 回滾到上一個版本
git log --oneline -10
git reset --hard <previous_commit_hash>

# 重啟服務
sudo systemctl restart lottery-backend
```

## 📝 配置更新

### 郵件配置

如果需要更新郵件配置，請確保：

1. SMTP 服務器設定正確
2. 用戶名和密碼有效
3. 端口和加密設定匹配

### 環境變數

檢查並更新必要的環境變數：

```bash
# 檢查當前配置
cat config.local.env

# 如果需要，更新資料庫連接等配置
```

## ✅ 部署完成檢查清單

- [ ] 代碼成功更新到最新版本
- [ ] 資料庫遷移成功執行
- [ ] 服務正常啟動
- [ ] 基本 API 功能正常
- [ ] 軟刪除功能測試通過
- [ ] 郵件功能測試通過（如果配置了郵件）
- [ ] 日志沒有錯誤訊息
- [ ] 系統監控正常

## 📞 支援

如果在部署過程中遇到問題，請檢查：

1. 日志文件中的錯誤訊息
2. 資料庫連接狀態
3. 網路連接和防火牆設定
4. Python 虛擬環境是否正確激活

---

**部署日期**: $(date)  
**版本**: v2.0 (軟刪除 + Email 測試 API)  
**提交**: a38e58d
