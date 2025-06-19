#!/bin/bash

# 抽獎系統服務器啟動腳本
# 包含 Oracle 環境變數設置

set -e

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

# 檢查並設置 Oracle 環境變數
setup_oracle_env() {
    log_info "設置 Oracle 環境變數..."
    
    # Oracle Instant Client 路徑
    ORACLE_CLIENT_PATH="$HOME/instantclient_23_4"
    
    if [ -d "$ORACLE_CLIENT_PATH" ]; then
        export LD_LIBRARY_PATH="$ORACLE_CLIENT_PATH:$LD_LIBRARY_PATH"
        export ORACLE_HOME="$ORACLE_CLIENT_PATH"
        log_success "Oracle 環境變數已設置"
        log_info "ORACLE_HOME: $ORACLE_HOME"
        log_info "LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
    else
        log_warning "Oracle Instant Client 目錄不存在: $ORACLE_CLIENT_PATH"
        log_warning "系統將使用 Oracle 降級模式運行"
    fi
    
    # 檢查 libaio 符號連結
    if [ -f "$HOME/lib/libaio.so.1" ]; then
        export LD_LIBRARY_PATH="$HOME/lib:$LD_LIBRARY_PATH"
        log_info "已包含 libaio 庫路徑"
    fi
}

# 檢查虛擬環境
check_venv() {
    if [ ! -d ".venv" ]; then
        log_error "虛擬環境不存在，請先創建虛擬環境"
        log_info "運行: python3 -m venv .venv"
        exit 1
    fi
    
    if [ ! -f ".venv/bin/activate" ]; then
        log_error "虛擬環境激活腳本不存在"
        exit 1
    fi
    
    log_success "虛擬環境檢查通過"
}

# 停止現有服務
stop_existing_service() {
    log_info "停止現有服務..."
    
    # 停止可能的進程
    if pgrep -f "lottery_api.main" > /dev/null; then
        log_info "發現運行中的服務，正在停止..."
        pkill -f "python -m lottery_api.main" || true
        sleep 2
        log_success "現有服務已停止"
    fi
    
    # 清理 PID 文件
    if [ -f "lottery_backend.pid" ]; then
        rm -f lottery_backend.pid
        log_info "已清理 PID 文件"
    fi
}

# 啟動服務
start_service() {
    local mode=${1:-background}
    
    log_info "啟動抽獎系統服務..."
    
    # 設置 Oracle 環境變數
    setup_oracle_env
    
    # 激活虛擬環境
    source .venv/bin/activate
    log_success "虛擬環境已激活"
    
    case $mode in
        "foreground"|"fg")
            log_info "在前台啟動服務..."
            python -m lottery_api.main
            ;;
        "background"|"bg")
            log_info "在後台啟動服務..."
            nohup python -m lottery_api.main > lottery_backend.log 2>&1 &
            echo $! > lottery_backend.pid
            log_success "服務已在後台啟動，PID: $(cat lottery_backend.pid)"
            log_info "日誌文件: lottery_backend.log"
            ;;
        "screen")
            if ! command -v screen >/dev/null 2>&1; then
                log_error "screen 未安裝，請安裝 screen 或使用其他模式"
                exit 1
            fi
            log_info "在 screen 中啟動服務..."
            screen -dmS lottery-backend bash -c "
                export LD_LIBRARY_PATH='$LD_LIBRARY_PATH'
                export ORACLE_HOME='$ORACLE_HOME'
                source .venv/bin/activate
                python -m lottery_api.main
            "
            log_success "服務已在 screen 中啟動"
            log_info "使用 'screen -r lottery-backend' 查看服務狀態"
            ;;
        *)
            log_error "未知的啟動模式: $mode"
            log_info "支持的模式: foreground, background, screen"
            exit 1
            ;;
    esac
}

# 檢查服務狀態
check_service_status() {
    log_info "檢查服務狀態..."
    
    # 等待服務啟動
    sleep 3
    
    # 檢查進程
    if pgrep -f "lottery_api.main" > /dev/null; then
        log_success "✅ 服務進程正在運行"
        
        # 檢查 API 響應
        if curl -s -f "http://localhost:8000/lottery/events" > /dev/null 2>&1; then
            log_success "✅ API 服務正常響應"
        else
            log_warning "⚠️  API 服務無響應，可能仍在啟動中"
        fi
    else
        log_error "❌ 服務進程未運行"
        return 1
    fi
}

# 顯示使用說明
show_usage() {
    echo "抽獎系統服務器啟動腳本"
    echo
    echo "用法: $0 [模式] [選項]"
    echo
    echo "模式:"
    echo "  foreground, fg    在前台啟動服務 (默認用於開發)"
    echo "  background, bg    在後台啟動服務 (默認用於生產)"
    echo "  screen           在 screen 中啟動服務"
    echo
    echo "選項:"
    echo "  --stop           停止現有服務"
    echo "  --status         檢查服務狀態"
    echo "  --restart        重啟服務"
    echo "  --help, -h       顯示此幫助信息"
    echo
    echo "示例:"
    echo "  $0                    # 後台啟動"
    echo "  $0 foreground         # 前台啟動"
    echo "  $0 screen            # 在 screen 中啟動"
    echo "  $0 --stop            # 停止服務"
    echo "  $0 --restart         # 重啟服務"
    echo
    echo "Oracle 環境變數會自動設置:"
    echo "  export LD_LIBRARY_PATH=~/instantclient_23_4:\$LD_LIBRARY_PATH"
    echo "  export ORACLE_HOME=~/instantclient_23_4"
}

# 主函數
main() {
    case "${1:-background}" in
        "--help"|"-h")
            show_usage
            exit 0
            ;;
        "--stop")
            stop_existing_service
            exit 0
            ;;
        "--status")
            check_service_status
            exit 0
            ;;
        "--restart")
            stop_existing_service
            sleep 2
            check_venv
            start_service background
            check_service_status
            exit 0
            ;;
        "foreground"|"fg"|"background"|"bg"|"screen")
            check_venv
            stop_existing_service
            start_service "$1"
            if [ "$1" != "foreground" ] && [ "$1" != "fg" ]; then
                check_service_status
            fi
            ;;
        *)
            log_error "未知的參數: $1"
            show_usage
            exit 1
            ;;
    esac
}

# 錯誤處理
trap 'log_error "啟動過程中發生錯誤"; exit 1' ERR

# 運行主函數
main "$@" 