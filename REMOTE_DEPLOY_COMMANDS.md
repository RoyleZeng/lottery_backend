# 🚀 虛擬機部署命令清單

由於 GitHub 連接問題，請在虛擬機上按順序執行以下命令：

## 1. 停止現有服務

```bash
# 檢查並停止服務
sudo systemctl stop lottery-backend 2>/dev/null || echo "systemd service not found"
pkill -f "python -m lottery_api.main" 2>/dev/null || echo "no manual processes found"
```

## 2. 備份現有代碼和數據庫

```bash
# 備份現有代碼
cd ~/backend_api
cp -r lottery_backend lottery_backend_backup_$(date +%Y%m%d_%H%M%S)

# 備份數據庫（如果需要）
pg_dump -h localhost -U local -d postgres > ~/backup_$(date +%Y%m%d_%H%M%S).sql 2>/dev/null || echo "database backup skipped"
```

## 3. 解壓新代碼

```bash
# 進入項目目錄
cd ~/backend_api/lottery_backend

# 解壓新代碼（覆蓋現有文件）
tar -xzf ~/lottery_backend_update.tar.gz --overwrite

# 檢查文件是否正確更新
ls -la deploy.sh DEPLOYMENT_GUIDE.md NEW_FEATURES_SUMMARY.md
```

## 4. 執行數據庫遷移

```bash
# 連接數據庫執行遷移
psql -h localhost -U local -d postgres -c "
-- 新增 is_deleted 欄位
ALTER TABLE lottery_events ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- 新增索引提升查詢效能
CREATE INDEX IF NOT EXISTS idx_lottery_events_is_deleted ON lottery_events(is_deleted);

-- 驗證變更
SELECT 'Migration completed' as status;
"
```

## 5. 更新 Python 依賴

```bash
# 激活虛擬環境
source .venv/bin/activate

# 更新依賴（如果有新的）
pip install -r requirements.txt
```

## 6. 測試新功能

```bash
# 設置 Oracle 環境變數
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4

# 啟動測試服務器
python -m lottery_api.main &
SERVER_PID=$!

# 等待啟動
sleep 5

# 測試基本 API
curl -X GET "http://localhost:8000/lottery/events" | head -20

# 測試新的軟刪除 API
curl -X GET "http://localhost:8000/lottery/deleted-events"

# 測試 Oracle 連接（如果有學生資料）
curl -X GET "http://localhost:8000/lottery/events" | grep -i "oracle" || echo "Oracle connection test completed"

# 停止測試服務器
kill $SERVER_PID
```

## 7. 啟動生產服務（包含 Oracle 環境變數）

```bash
# 方法一：使用啟動腳本（推薦）
chmod +x start_server.sh
./start_server.sh

# 方法二：使用 systemd（如果配置了）
sudo systemctl start lottery-backend
sudo systemctl enable lottery-backend

# 方法三：使用 screen 後台運行（包含 Oracle 環境變數）
screen -dmS lottery-backend bash -c "
export LD_LIBRARY_PATH=~/instantclient_23_4:\$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4
source .venv/bin/activate
python -m lottery_api.main
"

# 方法四：直接後台運行（包含 Oracle 環境變數）
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4
source .venv/bin/activate
nohup python -m lottery_api.main > lottery_backend.log 2>&1 &
echo $! > lottery_backend.pid
```

## 8. 驗證部署

```bash
# 檢查服務狀態
sudo systemctl status lottery-backend 2>/dev/null || echo "checking manual process..."
ps aux | grep lottery_api

# 測試 API
curl -X GET "http://localhost:8000/lottery/events" | jq '.success'
curl -X GET "http://localhost:8000/lottery/deleted-events" | jq '.success'

# 檢查數據庫變更
psql -h localhost -U local -d postgres -c "
SELECT
    COUNT(*) as total_events,
    COUNT(*) FILTER (WHERE is_deleted = false) as active_events,
    COUNT(*) FILTER (WHERE is_deleted = true) as deleted_events
FROM lottery_events;
"
```

## 9. 運行完整測試（可選）

```bash
# 運行新功能測試
python test_new_features.py

# 運行郵件修復測試（需要配置郵件）
# python test_email_fix.py
```

## 🔧 故障排除

如果遇到問題：

### 服務無法啟動

```bash
# 檢查日誌
sudo journalctl -u lottery-backend -n 50
# 或
tail -f lottery_backend.log
```

### 數據庫連接問題

```bash
# 測試數據庫連接
psql -h localhost -U local -d postgres -c "SELECT 1;"
```

### API 無法訪問

```bash
# 檢查端口
netstat -tlnp | grep :8000

# 檢查進程
ps aux | grep lottery_api
```

## ✅ 部署完成檢查

- [ ] 服務正常啟動
- [ ] 基本 API 正常工作
- [ ] 軟刪除 API 正常工作
- [ ] 數據庫遷移成功
- [ ] 沒有錯誤日誌

## 🆕 新功能說明

部署完成後，系統將包含以下新功能：

1. **軟刪除功能**

   - `DELETE /lottery/events/{event_id}` - 軟刪除活動
   - `PUT /lottery/events/{event_id}/restore` - 恢復活動
   - `GET /lottery/deleted-events` - 查看被軟刪除的活動

2. **Email 測試 API**

   - `POST /email/test-winners/{event_id}` - 測試中獎通知郵件

3. **郵件修復**
   - 修復 Gmail RFC 5322 標頭問題
   - 支援中文寄件人名稱

---

**版本**: v2.0 (軟刪除 + Email 測試 API)  
**部署方式**: 文件傳輸（因 GitHub 連接問題）
