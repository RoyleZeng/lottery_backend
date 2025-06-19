# Oracle 環境設置指南

## 概述

為了讓抽獎系統正確連接到 Oracle 資料庫，需要設置適當的環境變數。本文檔詳細說明了如何在不同環境中配置 Oracle 環境變數。

## 環境變數說明

### 必要的環境變數

```bash
# Oracle 客戶端路徑
export ORACLE_HOME=~/instantclient_23_4

# 庫文件路徑
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH

# 如果需要 libaio 支援
export LD_LIBRARY_PATH=~/lib:$LD_LIBRARY_PATH
```

### 環境變數說明

- **ORACLE_HOME**: Oracle 客戶端安裝目錄
- **LD_LIBRARY_PATH**: 動態庫搜索路徑，包含 Oracle 客戶端庫
- **libaio**: 異步 I/O 庫，某些系統需要額外的符號連結

## 設置方法

### 方法 1: 使用啟動腳本（推薦）

使用項目提供的 `start_server.sh` 腳本，會自動設置環境變數：

```bash
# 後台啟動（自動設置環境變數）
./start_server.sh

# 前台啟動（用於調試）
./start_server.sh foreground

# 檢查服務狀態
./start_server.sh --status
```

### 方法 2: 手動設置環境變數

#### 臨時設置（當前會話有效）

```bash
# 設置環境變數
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4

# 啟動服務
source .venv/bin/activate
python -m lottery_api.main
```

#### 永久設置（添加到 shell 配置文件）

在 `~/.bashrc` 或 `~/.profile` 中添加：

```bash
# Oracle 環境變數
export ORACLE_HOME=~/instantclient_23_4
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH

# 如果需要 libaio 支援
if [ -f ~/lib/libaio.so.1 ]; then
    export LD_LIBRARY_PATH=~/lib:$LD_LIBRARY_PATH
fi
```

然後重新載入配置：

```bash
source ~/.bashrc
```

### 方法 3: 使用 systemd 服務

如果使用 systemd 管理服務，在服務配置文件中添加環境變數：

```ini
[Unit]
Description=Lottery Backend API
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/lottery_backend
Environment=ORACLE_HOME=/home/your-username/instantclient_23_4
Environment=LD_LIBRARY_PATH=/home/your-username/instantclient_23_4:/home/your-username/lib
ExecStart=/path/to/lottery_backend/.venv/bin/python -m lottery_api.main
Restart=always

[Install]
WantedBy=multi-user.target
```

## 驗證設置

### 檢查環境變數

```bash
echo "ORACLE_HOME: $ORACLE_HOME"
echo "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
```

### 檢查 Oracle 客戶端文件

```bash
# 檢查 Oracle 客戶端目錄
ls -la ~/instantclient_23_4/

# 檢查關鍵庫文件
ls -la ~/instantclient_23_4/libclntsh.so*
ls -la ~/instantclient_23_4/libocci.so*
```

### 檢查 libaio 符號連結

```bash
# 檢查 libaio 符號連結
ls -la ~/lib/libaio.so.1

# 如果不存在，創建符號連結
mkdir -p ~/lib
ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 ~/lib/libaio.so.1
```

### 測試 Oracle 連接

```bash
# 啟動服務並測試
./start_server.sh foreground

# 在另一個終端測試 API
curl -X GET "http://localhost:8000/lottery/events"
```

## 常見問題

### DPI-1047 錯誤

**錯誤信息**: `DPI-1047: Cannot locate a 64-bit Oracle Client library`

**解決方案**:

1. 確認 Oracle Instant Client 已正確安裝
2. 檢查 `LD_LIBRARY_PATH` 設置
3. 確認庫文件權限

```bash
# 檢查庫文件
ldd ~/instantclient_23_4/libclntsh.so.23.1
```

### libaio 相關錯誤

**錯誤信息**: `libaio.so.1: cannot open shared object file`

**解決方案**:

```bash
# 安裝 libaio
sudo apt-get install libaio1

# 或創建符號連結
mkdir -p ~/lib
ln -s /usr/lib/x86_64-linux-gnu/libaio.so.1t64 ~/lib/libaio.so.1
```

### 權限問題

**錯誤信息**: `Permission denied`

**解決方案**:

```bash
# 檢查文件權限
chmod +x ~/instantclient_23_4/*
chmod +r ~/instantclient_23_4/*
```

## 不同部署方式的環境變數設置

### 1. 開發環境

```bash
# 臨時設置，用於開發和測試
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4
source .venv/bin/activate
python -m lottery_api.main
```

### 2. 生產環境 - 後台運行

```bash
# 使用 nohup 後台運行
export LD_LIBRARY_PATH=~/instantclient_23_4:$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4
source .venv/bin/activate
nohup python -m lottery_api.main > lottery_backend.log 2>&1 &
```

### 3. 生產環境 - Screen

```bash
# 使用 screen 管理
screen -dmS lottery-backend bash -c "
export LD_LIBRARY_PATH=~/instantclient_23_4:\$LD_LIBRARY_PATH
export ORACLE_HOME=~/instantclient_23_4
source .venv/bin/activate
python -m lottery_api.main
"
```

### 4. 生產環境 - Docker

```dockerfile
# Dockerfile 中設置環境變數
ENV ORACLE_HOME=/opt/oracle/instantclient_23_4
ENV LD_LIBRARY_PATH=/opt/oracle/instantclient_23_4:$LD_LIBRARY_PATH
```

## 最佳實踐

1. **使用啟動腳本**: 推薦使用 `start_server.sh` 自動處理環境變數
2. **版本控制**: 確保 Oracle 客戶端版本與服務器兼容
3. **權限管理**: 確保庫文件有適當的讀取和執行權限
4. **日誌監控**: 監控啟動日誌以及時發現環境問題
5. **備用方案**: 系統已實現 Oracle 降級模式，連接失敗時自動使用 mock 資料

## 故障排除

### 檢查環境變數

```bash
# 檢查當前環境變數
env | grep ORACLE
env | grep LD_LIBRARY

# 檢查進程環境變數
ps aux | grep lottery_api
cat /proc/PID/environ | tr '\0' '\n' | grep ORACLE
```

### 檢查庫依賴

```bash
# 檢查 Python 模組依賴
ldd .venv/lib/python3.9/site-packages/cx_Oracle.cpython-39-x86_64-linux-gnu.so
```

### 檢查服務日誌

```bash
# 檢查啟動日誌
tail -f lottery_backend.log

# 檢查 systemd 日誌
sudo journalctl -u lottery-backend -f
```

---

**注意**: 如果 Oracle 連接失敗，系統會自動降級到 mock 模式，不會影響基本功能的使用。
