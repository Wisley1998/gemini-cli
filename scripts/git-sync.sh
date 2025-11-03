#!/bin/bash

# Git 同步脚本 - 支持拉取和推送操作,带二次确认
# 用法: ./scripts/git-sync.sh [pull|push]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_info() {
    echo -e "${BLUE}ℹ ${NC}$1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# 确认函数
confirm() {
    local prompt="$1"
    local response
    
    while true; do
        echo -e "${YELLOW}?${NC} $prompt (y/n): "
        read -r response
        case "$response" in
            [yY]|[yY][eE][sS])
                return 0
                ;;
            [nN]|[nN][oO])
                return 1
                ;;
            *)
                print_warning "请输入 y 或 n"
                ;;
        esac
    done
}

# 检查是否在 git 仓库中
check_git_repo() {
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        print_error "当前目录不是 Git 仓库!"
        exit 1
    fi
}

# 获取当前分支
get_current_branch() {
    git rev-parse --abbrev-ref HEAD
}

# 检查是否有未提交的更改
check_uncommitted_changes() {
    if ! git diff-index --quiet HEAD --; then
        return 1
    fi
    return 0
}

# 显示状态信息
show_status() {
    local branch=$(get_current_branch)
    local remote=$(git remote get-url origin 2>/dev/null || echo "未配置")
    
    echo ""
    print_info "=== Git 仓库状态 ==="
    echo "  当前分支: ${GREEN}$branch${NC}"
    echo "  远程仓库: ${BLUE}$remote${NC}"
    echo ""
    
    # 显示未提交的更改
    if ! check_uncommitted_changes; then
        print_warning "发现未提交的更改:"
        git status --short
        echo ""
    fi
}

# 拉取操作
do_pull() {
    local branch=$(get_current_branch)
    
    print_info "准备从远程仓库拉取最新代码..."
    show_status
    
    # 检查未提交的更改
    if ! check_uncommitted_changes; then
        print_warning "你有未提交的更改,拉取可能会导致冲突!"
        if ! confirm "是否继续拉取? (建议先提交或暂存更改)"; then
            print_info "操作已取消"
            exit 0
        fi
    fi
    
    # 显示将要执行的操作
    echo ""
    print_info "将执行以下操作:"
    echo "  1. git fetch origin"
    echo "  2. git pull origin $branch"
    echo ""
    
    if ! confirm "确认要拉取分支 '$branch' 的最新代码吗?"; then
        print_info "操作已取消"
        exit 0
    fi
    
    # 执行拉取
    print_info "正在获取远程更新..."
    git fetch origin
    
    print_info "正在拉取代码..."
    if git pull origin "$branch"; then
        print_success "代码拉取成功!"
        echo ""
        print_info "最新提交:"
        git log -1 --oneline --decorate
    else
        print_error "拉取失败,可能存在冲突需要解决"
        exit 1
    fi
}

# 推送操作
do_push() {
    local branch=$(get_current_branch)
    
    print_info "准备推送代码到远程仓库..."
    show_status
    
    # 检查未提交的更改
    if ! check_uncommitted_changes; then
        print_error "你有未提交的更改,请先提交后再推送!"
        echo ""
        if confirm "是否现在提交这些更改?"; then
            # 显示更改的文件
            echo ""
            print_info "更改的文件:"
            git status --short
            echo ""
            
            # 询问提交信息
            echo -e "${YELLOW}?${NC} 请输入提交信息: "
            read -r commit_message
            
            if [ -z "$commit_message" ]; then
                print_error "提交信息不能为空!"
                exit 1
            fi
            
            # 确认提交
            if confirm "确认提交这些更改吗?"; then
                git add .
                if git commit --no-verify -m "$commit_message"; then
                    print_success "代码已提交"
                else
                    print_error "提交失败"
                    exit 1
                fi
            else
                print_info "操作已取消"
                exit 0
            fi
        else
            print_info "操作已取消"
            exit 0
        fi
    fi
    
    # 显示将要推送的提交
    echo ""
    print_info "准备推送的提交:"
    git log origin/"$branch".."$branch" --oneline --decorate 2>/dev/null || git log -5 --oneline --decorate
    echo ""
    
    # 显示将要执行的操作
    print_info "将执行以下操作:"
    echo "  git push origin $branch"
    echo ""
    
    if ! confirm "确认要推送分支 '$branch' 到远程仓库吗?"; then
        print_info "操作已取消"
        exit 0
    fi
    
    # 执行推送
    print_info "正在推送代码..."
    if git push origin "$branch"; then
        print_success "代码推送成功!"
    else
        print_error "推送失败!"
        print_info "如果远程分支有新提交,请先执行 pull 操作"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "Git 同步脚本"
    echo ""
    echo "用法:"
    echo "  $0 pull    - 从远程仓库拉取最新代码"
    echo "  $0 push    - 推送本地代码到远程仓库"
    echo "  $0 status  - 显示仓库状态"
    echo "  $0 help    - 显示此帮助信息"
    echo ""
    echo "特性:"
    echo "  • 所有操作都需要人工二次确认"
    echo "  • 推送前自动检查未提交的更改"
    echo "  • 拉取前警告可能的冲突"
    echo "  • 彩色输出,清晰易读"
    echo ""
}

# 主函数
main() {
    check_git_repo
    
    local action="${1:-}"
    
    case "$action" in
        pull)
            do_pull
            ;;
        push)
            do_push
            ;;
        status)
            show_status
            ;;
        help|--help|-h)
            show_help
            ;;
        "")
            print_error "请指定操作: pull 或 push"
            echo ""
            show_help
            exit 1
            ;;
        *)
            print_error "未知操作: $action"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"
