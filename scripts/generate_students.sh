#!/bin/bash

# 定義顏色代碼
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== 學生資料生成工具 =====${NC}"
echo "此腳本將生成3000位假學生資料並寫入數據庫"
echo

# 獲取Docker容器狀態
DOCKER_RUNNING=false
if command -v docker &> /dev/null; then
    echo "檢查 Docker 容器狀態..."
    if docker ps | grep -q postgres; then
        DOCKER_RUNNING=true
        CONTAINER_ID=$(docker ps | grep postgres | awk '{print $1}' | head -n 1)
        CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' $CONTAINER_ID)
        echo -e "${GREEN}發現運行中的 PostgreSQL Docker 容器: $CONTAINER_ID${NC}"
        echo "容器 IP: $CONTAINER_IP"
    else
        echo -e "${YELLOW}未發現運行中的 PostgreSQL Docker 容器。${NC}"
    fi
else
    echo -e "${YELLOW}Docker命令未找到，將嘗試連接本地數據庫。${NC}"
fi

# 檢查資料庫是否可以連接
echo "正在檢查數據庫連接..."
DB_HOST="localhost"
DB_PORT=5432

if [ "$DOCKER_RUNNING" = true ]; then
    echo -e "${BLUE}嘗試連接到 Docker 容器中的數據庫...${NC}"
    DB_HOST="$CONTAINER_IP"
    if ! docker exec $CONTAINER_ID psql -U local -d postgres -c "SELECT 1" &> /dev/null; then
        echo -e "${YELLOW}警告: 無法通過 Docker 容器連接到數據庫。將嘗試直接連接。${NC}"
    else
        echo -e "${GREEN}Docker 容器中的數據庫連接正常!${NC}"
    fi
elif command -v psql &> /dev/null; then
    echo -e "${BLUE}嘗試連接到本地數據庫...${NC}"
    if ! psql -h localhost -U local -d postgres -c "SELECT 1" &> /dev/null; then
        echo -e "${YELLOW}警告: 無法連接到本地數據庫。請確保 PostgreSQL 服務正在運行。${NC}"
    else
        echo -e "${GREEN}本地數據庫連接正常!${NC}"
    fi
else
    echo -e "${YELLOW}警告: 未找到 psql 命令。請確保 PostgreSQL 已安裝且加入PATH。${NC}"
fi

echo
echo -e "${BLUE}將使用以下數據庫連接參數:${NC}"
echo "主機: $DB_HOST"
echo "端口: $DB_PORT"
echo
echo "正在運行 Python 腳本..."
echo "注意: 這可能需要幾分鐘時間"
echo

# 激活虛擬環境（如果有）
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# 運行 Python 腳本，傳遞數據庫連接參數
python scripts/generate_fake_students.py $DB_HOST $DB_PORT

echo
echo -e "${GREEN}腳本執行完畢!${NC}"
echo "如果生成了CSV文件, 可以在 exports/ 目錄下找到" 