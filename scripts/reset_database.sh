#!/bin/bash

# 定義顏色代碼
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== 重置數據庫結構 =====${NC}"
echo "此腳本將刪除並重新創建所有表結構"
echo

# 檢查遷移文件是否存在
MIGRATION_FILE="db_migrations/lottery_tables.sql"
if [ ! -f "$MIGRATION_FILE" ]; then
    echo -e "${RED}錯誤: 遷移文件不存在: $MIGRATION_FILE${NC}"
    exit 1
fi

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

# 設置數據庫連接參數
DB_HOST="localhost"
DB_PORT=5432
DB_USER="local"
DB_NAME="postgres"
DB_PASS="local1234"

# 創建刪除表的SQL腳本
RESET_SQL=$(cat << EOF
DROP TABLE IF EXISTS lottery_winners CASCADE;
DROP TABLE IF EXISTS lottery_prizes CASCADE;
DROP TABLE IF EXISTS final_teaching_comments CASCADE;
DROP TABLE IF EXISTS lottery_participants CASCADE;
DROP TABLE IF EXISTS student CASCADE;
DROP TABLE IF EXISTS lottery_events CASCADE;
EOF
)

if [ "$DOCKER_RUNNING" = true ]; then
    echo -e "${BLUE}將使用 Docker 容器中的數據庫...${NC}"
    
    # 執行重置SQL
    echo "刪除現有表..."
    echo "$RESET_SQL" | docker exec -i $CONTAINER_ID psql -U $DB_USER -d $DB_NAME
    
    # 將遷移文件複製到容器
    echo "將遷移文件複製到容器..."
    TEMP_FILE="/tmp/lottery_tables.sql"
    docker cp $MIGRATION_FILE $CONTAINER_ID:$TEMP_FILE
    
    # 執行遷移
    echo "在容器中執行遷移文件..."
    if docker exec $CONTAINER_ID psql -U $DB_USER -d $DB_NAME -f $TEMP_FILE; then
        echo -e "${GREEN}遷移成功完成!${NC}"
    else
        echo -e "${RED}遷移失敗。請檢查錯誤消息。${NC}"
        exit 1
    fi
    
    # 清理臨時文件
    docker exec $CONTAINER_ID rm $TEMP_FILE
else
    echo -e "${BLUE}嘗試連接到本地數據庫...${NC}"
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}錯誤: 未找到 psql 命令. 請確保 PostgreSQL 已安裝且加入PATH.${NC}"
        exit 1
    fi
    
    # 執行重置SQL
    echo "刪除現有表..."
    echo "$RESET_SQL" | PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME
    
    # 執行遷移
    echo "執行遷移文件..."
    if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $MIGRATION_FILE; then
        echo -e "${GREEN}遷移成功完成!${NC}"
    else
        echo -e "${RED}遷移失敗。請檢查錯誤消息。${NC}"
        exit 1
    fi
fi

echo
echo -e "${GREEN}數據庫結構已重置並重建!${NC}"
echo "現在可以運行 ./scripts/generate_fake_students.py 來生成假學生數據"
echo "然後運行 ./scripts/create_lottery_events.py 來創建抽獎活動" 