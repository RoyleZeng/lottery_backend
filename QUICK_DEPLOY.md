# 🚀 快速部署指南

## 在目標虛擬機上快速部署新功能

### 方法一：使用自動化部署腳本（推薦）

```bash
# 1. 進入項目目錄
cd /path/to/lottery_backend

# 2. 拉取最新代碼
git pull origin main

# 3. 運行自動化部署腳本
./deploy.sh
```

部署腳本會自動執行：

- ✅ 停止現有服務
- ✅ 備份數據庫
- ✅ 更新代碼和依賴
- ✅ 執行數據庫遷移
- ✅ 測試部署
- ✅ 啟動服務
- ✅ 驗證功能

### 方法二：手動部署

```bash
# 1. 停止服務
sudo systemctl stop lottery-backend
# 或
pkill -f "python -m lottery_api.main"

# 2. 更新代碼
cd /path/to/lottery_backend
git pull origin main

# 3. 激活虛擬環境
source .venv/bin/activate

# 4. 執行數據庫遷移
psql -h localhost -U your_username -d your_database -f db_migrations/add_soft_delete_column.sql

# 5. 啟動服務
sudo systemctl start lottery-backend
# 或
python -m lottery_api.main
```

## 🆕 新功能驗證

部署完成後，測試新功能：

```bash
# 測試軟刪除功能
curl -X GET "http://localhost:8000/lottery/deleted-events"

# 測試郵件 API
curl -X GET "http://localhost:8000/email/template-variables"

# 運行完整測試
python test_new_features.py
```

## 📋 新增的 API 端點

1. **軟刪除功能**

   - `DELETE /lottery/events/{event_id}` - 軟刪除活動
   - `PUT /lottery/events/{event_id}/restore` - 恢復活動
   - `GET /lottery/deleted-events` - 獲取被軟刪除的活動

2. **Email 測試 API**
   - `POST /email/test-winners/{event_id}` - 測試中獎通知郵件

## 🔧 問題排除

如果遇到問題：

1. **檢查服務狀態**

   ```bash
   sudo systemctl status lottery-backend
   ```

2. **查看日誌**

   ```bash
   sudo journalctl -u lottery-backend -f
   ```

3. **檢查數據庫**

   ```sql
   SELECT id, name, is_deleted FROM lottery_events LIMIT 5;
   ```

4. **重啟服務**
   ```bash
   sudo systemctl restart lottery-backend
   ```

## 📞 支援

詳細信息請參考：

- 📖 [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - 完整部署指南
- 📋 [NEW_FEATURES_SUMMARY.md](./NEW_FEATURES_SUMMARY.md) - 新功能說明

---

**版本**: v2.0 (軟刪除 + Email 測試 API)  
**最後更新**: 2025-06-18
