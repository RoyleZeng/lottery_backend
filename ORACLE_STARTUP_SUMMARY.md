# Oracle 環境變數啟動總結

## 🚀 快速啟動

### 推薦方式（使用啟動腳本）

```bash
# 後台啟動（生產環境）
./start_server.sh

# 前台啟動（調試模式）
./start_server.sh foreground

# 檢查狀態
./start_server.sh --status
```

### 手動啟動（你建議的方式）

```bash
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH && \
export ORACLE_HOME=~/instantclient_23_4 && \
nohup python -m lottery_api.main > lottery_backend.log 2>&1 &
```

## 📁 相關文件

- `start_server.sh` - 自動啟動腳本（推薦）
- `deploy.sh` - 完整部署腳本（已更新包含 Oracle 環境變數）
- `ORACLE_ENVIRONMENT_SETUP.md` - 詳細環境設置指南
- `REMOTE_DEPLOY_COMMANDS.md` - 遠程部署命令（已更新）

## ✅ 功能特點

- 🔧 **自動環境檢查**: 檢查 Oracle Instant Client 是否存在
- 🔄 **降級支援**: Oracle 連接失敗時自動使用 mock 模式
- 📊 **多種啟動模式**: 前台、後台、screen
- 🛠️ **服務管理**: 停止、重啟、狀態檢查
- 📋 **詳細日誌**: 啟動過程和錯誤信息記錄

## 🔍 驗證連接

```bash
# 檢查環境變數
echo "ORACLE_HOME: $ORACLE_HOME"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

# 測試 API
curl -X GET "http://localhost:8000/lottery/events"
```

---

**問題解決**: 如果遇到 Oracle 連接問題，請參考 `ORACLE_ENVIRONMENT_SETUP.md` 詳細指南。
