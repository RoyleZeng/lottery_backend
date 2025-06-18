#!/bin/bash

# 抽獎系統自動化部署腳本
# 版本: v2.0 (軟刪除 + Email 測試 API)

set -e  # 遇到錯誤立即退出

echo "🚀 開始部署抽獎系統..."

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日誌函數
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 檢查是否為 root 用戶
check_user() {
    if [[ $EUID -eq 0 ]]; then
        log_warning "建議不要使用 root 用戶運行此腳本"
        read -p "是否繼續？(y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# 檢查必要工具
check_dependencies() {
    log_info "檢查必要工具..."
    
    local missing_tools=()
    
    command -v git >/dev/null 2>&1 || missing_tools+=("git")
    command -v python3 >/dev/null 2>&1 || missing_tools+=("python3")
    command -v psql >/dev/null 2>&1 || missing_tools+=("postgresql-client")
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "缺少必要工具: ${missing_tools[*]}"
        log_info "請先安裝這些工具，然後重新運行腳本"
        exit 1
    fi
    
    log_success "所有必要工具已安裝"
}

# 停止現有服務
stop_service() {
    log_info "停止現有服務..."
    
    # 嘗試停止 systemd 服務
    if systemctl is-active --quiet lottery-backend 2>/dev/null; then
        log_info "停止 systemd 服務..."
        sudo systemctl stop lottery-backend
        log_success "systemd 服務已停止"
    fi
    
    # 停止可能的手動進程
    if pgrep -f "lottery_api.main" > /dev/null; then
        log_info "停止手動進程..."
        pkill -f "python -m lottery_api.main" || true
        sleep 2
        log_success "手動進程已停止"
    fi
}

# 備份數據庫
backup_database() {
    log_info "備份數據庫..."
    
    # 獲取數據庫配置
    if [ -f "config.local.env" ]; then
        source config.local.env
    fi
    
    # 設置默認值
    DB_HOST=${DB_HOST:-localhost}
    DB_USER=${DB_USER:-local}
    DB_NAME=${DB_NAME:-postgres}
    
    local backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    
    log_info "備份數據庫到 $backup_file..."
    if pg_dump -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" > "$backup_file" 2>/dev/null; then
        log_success "數據庫備份完成: $backup_file"
    else
        log_warning "數據庫備份失敗，但繼續部署..."
    fi
}

# 更新代碼
update_code() {
    log_info "更新代碼..."
    
    # 檢查是否在 git 倉庫中
    if [ ! -d ".git" ]; then
        log_error "當前目錄不是 git 倉庫"
        exit 1
    fi
    
    # 顯示當前版本
    log_info "當前版本: $(git log --oneline -1)"
    
    # 拉取最新代碼
    git fetch origin
    git pull origin main
    
    # 顯示新版本
    log_success "更新完成，新版本: $(git log --oneline -1)"
}

# 更新依賴
update_dependencies() {
    log_info "檢查並更新依賴..."
    
    # 檢查虛擬環境
    if [ ! -d ".venv" ]; then
        log_warning "虛擬環境不存在，創建新的虛擬環境..."
        python3 -m venv .venv
    fi
    
    # 激活虛擬環境
    source .venv/bin/activate
    
    # 更新 pip
    pip install --upgrade pip
    
    # 安裝依賴
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        log_success "依賴更新完成"
    else
        log_warning "requirements.txt 不存在，跳過依賴安裝"
    fi
}

# 執行數據庫遷移
migrate_database() {
    log_info "執行數據庫遷移..."
    
    # 獲取數據庫配置
    if [ -f "config.local.env" ]; then
        source config.local.env
    fi
    
    # 設置默認值
    DB_HOST=${DB_HOST:-localhost}
    DB_USER=${DB_USER:-local}
    DB_NAME=${DB_NAME:-postgres}
    
    # 執行遷移
    if [ -f "db_migrations/add_soft_delete_column.sql" ]; then
        log_info "執行軟刪除欄位遷移..."
        if psql -h "$DB_HOST" -U "$DB_USER" -d "$DB_NAME" -f "db_migrations/add_soft_delete_column.sql" 2>/dev/null; then
            log_success "數據庫遷移完成"
        else
            log_error "數據庫遷移失敗"
            exit 1
        fi
    else
        log_warning "遷移文件不存在，跳過數據庫遷移"
    fi
}

# 測試部署
test_deployment() {
    log_info "測試部署..."
    
    # 激活虛擬環境
    source .venv/bin/activate
    
    # 啟動測試服務器
    log_info "啟動測試服務器..."
    python -m lottery_api.main &
    SERVER_PID=$!
    
    # 等待服務器啟動
    sleep 5
    
    # 測試 API
    log_info "測試 API 連接..."
    if curl -s -f "http://localhost:8000/lottery/events" > /dev/null; then
        log_success "API 測試通過"
    else
        log_error "API 測試失敗"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    
    # 測試新功能
    log_info "測試軟刪除 API..."
    if curl -s -f "http://localhost:8000/lottery/deleted-events" > /dev/null; then
        log_success "軟刪除 API 測試通過"
    else
        log_error "軟刪除 API 測試失敗"
        kill $SERVER_PID 2>/dev/null || true
        exit 1
    fi
    
    # 停止測試服務器
    kill $SERVER_PID 2>/dev/null || true
    sleep 2
    
    log_success "所有測試通過"
}

# 啟動生產服務
start_service() {
    log_info "啟動生產服務..."
    
    # 嘗試啟動 systemd 服務
    if systemctl list-unit-files | grep -q lottery-backend; then
        log_info "啟動 systemd 服務..."
        sudo systemctl start lottery-backend
        sudo systemctl enable lottery-backend
        log_success "systemd 服務已啟動"
    else
        log_info "systemd 服務不存在，使用 screen 啟動..."
        
        # 檢查 screen 是否安裝
        if ! command -v screen >/dev/null 2>&1; then
            log_warning "screen 未安裝，直接在後台啟動服務"
            source .venv/bin/activate
            nohup python -m lottery_api.main > lottery_backend.log 2>&1 &
            echo $! > lottery_backend.pid
            log_success "服務已在後台啟動，PID: $(cat lottery_backend.pid)"
        else
            # 使用 screen 啟動
            screen -dmS lottery-backend bash -c "source .venv/bin/activate && python -m lottery_api.main"
            log_success "服務已在 screen 中啟動"
            log_info "使用 'screen -r lottery-backend' 查看服務狀態"
        fi
    fi
}

# 驗證部署
verify_deployment() {
    log_info "驗證部署..."
    
    # 等待服務啟動
    sleep 5
    
    # 檢查服務狀態
    if curl -s -f "http://localhost:8000/lottery/events" > /dev/null; then
        log_success "✅ 服務正常運行"
    else
        log_error "❌ 服務無法訪問"
        return 1
    fi
    
    # 檢查新功能
    if curl -s -f "http://localhost:8000/lottery/deleted-events" > /dev/null; then
        log_success "✅ 軟刪除功能正常"
    else
        log_error "❌ 軟刪除功能異常"
        return 1
    fi
    
    log_success "🎉 部署驗證完成！"
}

# 顯示部署結果
show_summary() {
    echo
    echo "=" * 60
    log_success "🎉 抽獎系統部署完成！"
    echo "=" * 60
    echo
    echo "📋 部署摘要:"
    echo "  • 版本: v2.0 (軟刪除 + Email 測試 API)"
    echo "  • 提交: $(git log --oneline -1)"
    echo "  • 服務狀態: 運行中"
    echo "  • API 地址: http://localhost:8000"
    echo "  • API 文檔: http://localhost:8000/api/spec/doc"
    echo
    echo "🆕 新功能:"
    echo "  • Event 軟刪除功能"
    echo "  • Email 測試 API"
    echo "  • 郵件標頭修復 (RFC 5322)"
    echo
    echo "🔧 管理命令:"
    echo "  • 查看服務狀態: sudo systemctl status lottery-backend"
    echo "  • 查看日誌: sudo journalctl -u lottery-backend -f"
    echo "  • 重啟服務: sudo systemctl restart lottery-backend"
    echo
    echo "📖 更多信息請參考 DEPLOYMENT_GUIDE.md"
    echo
}

# 主函數
main() {
    echo "🚀 抽獎系統自動化部署腳本 v2.0"
    echo "包含: 軟刪除功能 + Email 測試 API + 郵件修復"
    echo

    # 確認部署
    read -p "確定要開始部署嗎？(y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "部署已取消"
        exit 0
    fi

    # 執行部署步驟
    check_user
    check_dependencies
    stop_service
    backup_database
    update_code
    update_dependencies
    migrate_database
    test_deployment
    start_service
    verify_deployment
    show_summary
}

# 錯誤處理
trap 'log_error "部署過程中發生錯誤，請檢查上面的錯誤信息"; exit 1' ERR

# 運行主函數
main "$@" 