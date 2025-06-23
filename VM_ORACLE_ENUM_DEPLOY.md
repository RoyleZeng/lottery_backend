# 🚀 虛擬機 Oracle 環境變數和 Enum 功能部署

## 部署概述

本次更新包含：

- ✅ ValidSurveys 和 StudentType enum 功能
- ✅ Oracle 環境變數自動設置
- ✅ 新的啟動腳本 start_server.sh
- ✅ 完整的 Oracle 環境設置文檔

## 1. 停止現有服務

```bash
# 檢查並停止服務
sudo systemctl stop lottery-backend 2>/dev/null || echo "systemd service not found"
pkill -f "python -m lottery_api.main" 2>/dev/null || echo "no manual processes found"

# 檢查進程是否完全停止
ps aux | grep lottery_api || echo "no processes found"
```

## 2. 備份現有代碼

```bash
# 進入項目目錄
cd ~/backend_api/lottery_backend

# 備份現有代碼
cp -r . ../lottery_backend_backup_$(date +%Y%m%d_%H%M%S)

# 備份數據庫（可選）
pg_dump -h localhost -U local -d postgres > ~/backup_oracle_enum_$(date +%Y%m%d_%H%M%S).sql 2>/dev/null || echo "database backup skipped"
```

## 3. 更新代碼

### 方法 1: 使用 Git (如果網絡正常)

```bash
# 拉取最新代碼
git fetch origin
git pull origin main

# 檢查更新
git log --oneline -5
```

### 方法 2: 使用文件傳輸 (推薦)

```bash
# 解壓新代碼（假設已上傳 lottery_backend_oracle_enum_update.tar.gz）
tar -xzf ~/lottery_backend_oracle_enum_update.tar.gz --overwrite

# 檢查關鍵文件是否存在
ls -la start_server.sh ORACLE_ENVIRONMENT_SETUP.md ENUM_IMPLEMENTATION_SUMMARY.md
```

## 4. 設置文件權限

```bash
# 設置啟動腳本權限
chmod +x start_server.sh

# 檢查權限
ls -la start_server.sh
```

## 5. 檢查 Oracle 環境

```bash
# 檢查 Oracle Instant Client
ls -la ~/instantclient_23_4/

# 檢查 libaio 符號連結
ls -la ~/lib/libaio.so.1 || echo "libaio symlink not found"

# 如果需要創建 libaio 符號連結
mkdir -p ~/lib
ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 ~/lib/libaio.so.1 2>/dev/null || echo "libaio symlink already exists or not needed"
```

## 6. 更新 Python 依賴

```bash
# 激活虛擬環境
source .venv/bin/activate

# 檢查當前依賴
pip list | grep -E "(oracledb|cx-Oracle|pydantic|fastapi)"

# 更新依賴（如果需要）
pip install -r requirements.txt
```

## 7. 測試新功能

```bash
# 使用新的啟動腳本測試
./start_server.sh foreground &
SERVER_PID=$!

# 等待啟動
sleep 5

# 測試基本 API
curl -X GET "http://localhost:8000/lottery/events" | head -20

# 測試 enum 功能（創建測試活動）
curl -X POST "http://localhost:8000/lottery/events" \
  -H "Content-Type: application/json" \
  -d '{
    "academic_year_term": "113-1",
    "name": "Enum測試活動",
    "description": "測試ValidSurveys和StudentType enum",
    "event_date": "2024-12-20T10:00:00",
    "type": "final_teaching"
  }'

# 停止測試服務器
kill $SERVER_PID
```

## 8. 啟動生產服務（包含 Oracle 環境變數）

### 方法 1: 使用新的啟動腳本（推薦）

```bash
# 後台啟動服務
./start_server.sh

# 檢查狀態
./start_server.sh --status
```

### 方法 2: 手動啟動（包含 Oracle 環境變數）

```bash
# 設置 Oracle 環境變數並啟動
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4
source .venv/bin/activate
nohup python -m lottery_api.main > lottery_backend.log 2>&1 &
echo $! > lottery_backend.pid
```

### 方法 3: 使用 Screen

```bash
# 在 screen 中啟動（包含 Oracle 環境變數）
screen -dmS lottery-backend bash -c "
export LD_LIBRARY_PATH=~/instantclient_23_4:\$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4
source .venv/bin/activate
python -m lottery_api.main
"

# 查看 screen 會話
screen -ls
```

## 9. 驗證部署

```bash
# 檢查服務狀態
ps aux | grep lottery_api

# 檢查端口
netstat -tlnp | grep :8000

# 測試 API
curl -X GET "http://localhost:8000/lottery/events" | jq '.success' 2>/dev/null || echo "API responding"

# 檢查 Oracle 環境變數（如果服務在前台運行）
echo "ORACLE_HOME: $ORACLE_HOME"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"

# 檢查日誌
tail -f lottery_backend.log | head -20
```

## 10. 測試 Enum 功能

```bash
# 創建 final_teaching 活動
EVENT_RESPONSE=$(curl -s -X POST "http://localhost:8000/lottery/events" \
  -H "Content-Type: application/json" \
  -d '{
    "academic_year_term": "113-1",
    "name": "Enum功能測試",
    "description": "測試ValidSurveys和StudentType enum",
    "event_date": "2024-12-20T10:00:00",
    "type": "final_teaching"
  }')

echo "Event creation response: $EVENT_RESPONSE"

# 提取 event_id（如果有 jq）
EVENT_ID=$(echo $EVENT_RESPONSE | jq -r '.result.id' 2>/dev/null)

if [ "$EVENT_ID" != "null" ] && [ "$EVENT_ID" != "" ]; then
    echo "Created event ID: $EVENT_ID"

    # 測試學生導入（使用 enum 值）
    curl -X POST "http://localhost:8000/lottery/events/$EVENT_ID/participants" \
      -H "Content-Type: application/json" \
      -d '{
        "students": [
          {
            "id": "TEST001",
            "name": "測試外籍生",
            "department": "資工系",
            "grade": "大四",
            "valid_surveys": "Y",
            "student_type": "Y",
            "id_number": "A123456789",
            "address": "台北市信義區",
            "phone": "0912345678",
            "email": "test@example.com"
          }
        ]
      }'
else
    echo "Could not extract event ID, manual testing required"
fi
```

## 🔧 故障排除

### Oracle 連接問題

```bash
# 檢查 Oracle 環境變數
env | grep ORACLE
env | grep LD_LIBRARY

# 檢查 Oracle 客戶端文件
ls -la ~/instantclient_23_4/libclntsh.so*

# 檢查進程環境變數
ps aux | grep lottery_api
PID=$(pgrep -f lottery_api)
if [ "$PID" ]; then
    cat /proc/$PID/environ | tr '\0' '\n' | grep ORACLE
fi
```

### 服務啟動問題

```bash
# 檢查啟動日誌
tail -f lottery_backend.log

# 檢查虛擬環境
source .venv/bin/activate
python -c "import lottery_api; print('Import successful')"

# 檢查端口占用
lsof -i :8000
```

### Enum 功能問題

```bash
# 檢查 schema 更新
python -c "
from lottery_api.schema.lottery import ValidSurveys, StudentType
print('ValidSurveys.YES =', ValidSurveys.YES)
print('StudentType.FOREIGN =', StudentType.FOREIGN)
"
```

## ✅ 部署完成檢查清單

- [ ] 服務正常啟動
- [ ] Oracle 環境變數正確設置
- [ ] 基本 API 正常工作
- [ ] Enum 功能正常（ValidSurveys, StudentType）
- [ ] Final teaching 導入功能正常
- [ ] 沒有錯誤日誌
- [ ] 啟動腳本工作正常

## 📋 新功能說明

### ValidSurveys Enum

- `Y` = 有效問卷
- `N` = 無效問卷
- 只有 `valid_surveys="Y"` 的學生會被導入

### StudentType Enum

- `Y` = 外籍生
- `N` = 本國生
- 對應 Oracle 資料庫中的 STUD_EXTRA 欄位

### Oracle 環境變數

- 自動設置 `ORACLE_HOME` 和 `LD_LIBRARY_PATH`
- 支持 Oracle 連接降級模式
- 新的啟動腳本簡化部署流程

---

**版本**: v3.0 (Oracle 環境變數 + ValidSurveys/StudentType Enum)  
**部署方式**: 文件傳輸 + 新啟動腳本
