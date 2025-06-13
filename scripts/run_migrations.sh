#!/bin/bash

# 定義顏色代碼
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}===== 數據庫遷移工具 =====${NC}"
echo "此腳本將在數據庫中創建必要的表結構"
echo

# 檢查遷移文件是否存在
MIGRATION_FILES=("db_migrations/users_table.sql" "db_migrations/lottery_tables.sql" "db_migrations/remove_old_tables.sql")
for file in "${MIGRATION_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}錯誤: 遷移文件不存在: $file${NC}"
        exit 1
    fi
done

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

if [ "$DOCKER_RUNNING" = true ]; then
    echo -e "${BLUE}將使用 Docker 容器中的數據庫...${NC}"
    
    # 執行每個遷移文件
    for file in "${MIGRATION_FILES[@]}"; do
        echo "處理遷移文件: $file"
        
        # 將遷移文件複製到容器
        TEMP_FILE="/tmp/$(basename $file)"
        docker cp $file $CONTAINER_ID:$TEMP_FILE
        
        # 執行遷移
        echo "在容器中執行遷移文件..."
        if docker exec $CONTAINER_ID psql -U $DB_USER -d $DB_NAME -f $TEMP_FILE; then
            echo -e "${GREEN}$file 遷移成功完成!${NC}"
        else
            echo -e "${RED}$file 遷移失敗。請檢查錯誤消息。${NC}"
            exit 1
        fi
        
        # 清理臨時文件
        docker exec $CONTAINER_ID rm $TEMP_FILE
    done
else
    echo -e "${BLUE}嘗試連接到本地數據庫...${NC}"
    if ! command -v psql &> /dev/null; then
        echo -e "${RED}錯誤: 未找到 psql 命令. 請確保 PostgreSQL 已安裝且加入PATH.${NC}"
        exit 1
    fi
    
    # 執行每個遷移文件
    for file in "${MIGRATION_FILES[@]}"; do
        echo "處理遷移文件: $file"
        
        if PGPASSWORD=$DB_PASS psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f $file; then
            echo -e "${GREEN}$file 遷移成功完成!${NC}"
        else
            echo -e "${RED}$file 遷移失敗。請檢查錯誤消息。${NC}"
            exit 1
        fi
    done
fi

echo
echo -e "${GREEN}數據庫結構已就緒!${NC}"
echo "現在可以運行 python scripts/create_lottery_events.py 來創建抽獎活動和參與者數據"
echo "詳細的結構變更說明請參考: scripts/README_new_structure.md" 