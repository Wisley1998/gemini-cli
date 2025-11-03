#!/bin/bash
# DeepResearch Bench 任务执行脚本
# 用于批量运行 DeepResearch Bench 研究任务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认配置
PROMPTS_DIR="./deepresearch-bench-prompts"
RESULTS_DIR="./deepresearch-bench-results"
LIMIT=""
GEMINI_CMD="gemini"
MODEL=""
VERBOSE=false
DRY_RUN=false

# 打印帮助信息
print_help() {
    cat << EOF
DeepResearch Bench 任务执行脚本

用法: $0 [选项]

选项:
    -h, --help              显示此帮助信息
    -l, --limit N           只运行前 N 个任务
    -p, --prompts-dir DIR   prompt 文件目录 (默认: $PROMPTS_DIR)
    -r, --results-dir DIR   结果输出目录 (默认: $RESULTS_DIR)
    -m, --model MODEL       指定使用的模型
    -v, --verbose           显示详细输出
    -d, --dry-run           演习模式，只显示将要执行的命令
    --gemini-cmd CMD        gemini 命令路径 (默认: $GEMINI_CMD)

示例:
    # 运行所有任务
    $0

    # 只运行前 5 个任务
    $0 --limit 5

    # 使用特定模型运行
    $0 --model gemini-2.5-pro --limit 3

    # 演习模式
    $0 --dry-run --limit 10
EOF
}

# 解析命令行参数
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            print_help
            exit 0
            ;;
        -l|--limit)
            LIMIT="$2"
            shift 2
            ;;
        -p|--prompts-dir)
            PROMPTS_DIR="$2"
            shift 2
            ;;
        -r|--results-dir)
            RESULTS_DIR="$2"
            shift 2
            ;;
        -m|--model)
            MODEL="$2"
            shift 2
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --gemini-cmd)
            GEMINI_CMD="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}错误: 未知选项 $1${NC}"
            print_help
            exit 1
            ;;
    esac
done

# 打印横幅
print_banner() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                   DeepResearch Bench 任务执行器                            ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}🔍 检查依赖...${NC}"
    
    if ! command -v $GEMINI_CMD &> /dev/null; then
        echo -e "${RED}❌ 错误: 找不到 gemini 命令${NC}"
        echo -e "${YELLOW}请确保 gemini-cli 已正确安装并在 PATH 中${NC}"
        exit 1
    fi
    
    if [ ! -d "$PROMPTS_DIR" ]; then
        echo -e "${RED}❌ 错误: prompt 目录不存在: $PROMPTS_DIR${NC}"
        echo -e "${YELLOW}请先运行: python extract-deepresearch-bench-prompts.py${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ 依赖检查通过${NC}"
    echo ""
}

# 创建结果目录
setup_results_dir() {
    if [ ! -d "$RESULTS_DIR" ]; then
        mkdir -p "$RESULTS_DIR"
        echo -e "${GREEN}✅ 创建结果目录: $RESULTS_DIR${NC}"
    fi
}

# 获取 prompt 文件列表
get_prompt_files() {
    local files=($(ls -1 "$PROMPTS_DIR"/prompt_*.txt 2>/dev/null | sort))
    
    if [ ${#files[@]} -eq 0 ]; then
        echo -e "${RED}❌ 错误: 在 $PROMPTS_DIR 中没有找到 prompt 文件${NC}"
        exit 1
    fi
    
    # 如果设置了限制，只返回前 N 个文件
    if [ -n "$LIMIT" ]; then
        files=("${files[@]:0:$LIMIT}")
    fi
    
    echo "${files[@]}"
}

# 执行单个任务
run_task() {
    local prompt_file="$1"
    local task_number="$2"
    local total_tasks="$3"
    
    # 提取任务 ID
    local filename=$(basename "$prompt_file")
    local task_id=$(echo "$filename" | sed -E 's/prompt_[0-9]+_(.*)\.txt/\1/')
    
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🚀 任务 [$task_number/$total_tasks]: $task_id${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # 构建输出文件路径
    local output_file="$RESULTS_DIR/result_${task_number}_${task_id}.md"
    local log_file="$RESULTS_DIR/log_${task_number}_${task_id}.txt"
    
    # 构建 gemini 命令
    local cmd="$GEMINI_CMD"
    
    # 添加模型参数
    if [ -n "$MODEL" ]; then
        cmd="$cmd --model $MODEL"
    fi
    
    # 添加 prompt
    cmd="$cmd --prompt \"\$(cat '$prompt_file')\""
    
    # 演习模式
    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}[DRY RUN] 将执行:${NC}"
        echo "$cmd > '$output_file'"
        echo ""
        return 0
    fi
    
    # 显示详细信息
    if [ "$VERBOSE" = true ]; then
        echo -e "${YELLOW}📝 Prompt 文件: $prompt_file${NC}"
        echo -e "${YELLOW}📄 输出文件: $output_file${NC}"
        echo -e "${YELLOW}📋 日志文件: $log_file${NC}"
        echo ""
    fi
    
    # 记录开始时间
    local start_time=$(date +%s)
    
    # 执行任务
    echo -e "${YELLOW}⏳ 正在执行研究任务...${NC}"
    
    if eval "$cmd" > "$output_file" 2> "$log_file"; then
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo -e "${GREEN}✅ 任务完成 (耗时: ${duration}秒)${NC}"
        echo -e "${GREEN}📄 结果已保存到: $output_file${NC}"
        
        # 显示结果摘要
        local word_count=$(wc -w < "$output_file" | tr -d ' ')
        local line_count=$(wc -l < "$output_file" | tr -d ' ')
        echo -e "${BLUE}📊 报告统计: $line_count 行, $word_count 字${NC}"
        
        return 0
    else
        local end_time=$(date +%s)
        local duration=$((end_time - start_time))
        
        echo -e "${RED}❌ 任务失败 (耗时: ${duration}秒)${NC}"
        echo -e "${RED}📋 查看日志: $log_file${NC}"
        
        # 显示错误信息
        if [ "$VERBOSE" = true ] && [ -f "$log_file" ]; then
            echo -e "${YELLOW}错误详情:${NC}"
            tail -n 20 "$log_file"
        fi
        
        return 1
    fi
}



# 主函数
main() {
    print_banner
    
    # 检查依赖
    check_dependencies
    
    # 设置结果目录
    setup_results_dir
    
    # 获取 prompt 文件列表
    echo -e "${YELLOW}📂 扫描 prompt 文件...${NC}"
    prompt_files=($(get_prompt_files))
    total_tasks=${#prompt_files[@]}
    
    echo -e "${GREEN}✅ 找到 $total_tasks 个任务${NC}"
    echo ""
    
    # 显示配置
    echo -e "${BLUE}⚙️  配置:${NC}"
    echo -e "  • Prompt 目录: $PROMPTS_DIR"
    echo -e "  • 结果目录: $RESULTS_DIR"
    echo -e "  • 任务数量: $total_tasks"
    [ -n "$MODEL" ] && echo -e "  • 模型: $MODEL"
    [ "$VERBOSE" = true ] && echo -e "  • 详细输出: 是"
    [ "$DRY_RUN" = true ] && echo -e "  • 演习模式: 是"
    echo ""
    
    # 确认执行
    if [ "$DRY_RUN" = false ]; then
        echo -e "${YELLOW}按 Enter 开始执行，Ctrl+C 取消...${NC}"
        read
    fi
    
    # 执行任务
    local success_count=0
    local failed_count=0
    local start_time=$(date +%s)
    
    for i in "${!prompt_files[@]}"; do
        local task_number=$((i + 1))
        local prompt_file="${prompt_files[$i]}"
        
        if run_task "$prompt_file" "$task_number" "$total_tasks"; then
            ((success_count++))
        else
            ((failed_count++))
        fi
        
        echo ""
        
        # 添加延迟以避免过快请求
        if [ "$DRY_RUN" = false ] && [ $task_number -lt $total_tasks ]; then
            sleep 2
        fi
    done
    
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))
    
    # 打印总结
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                              执行完成                                       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}📊 总结:${NC}"
    echo -e "  • 总任务数: $total_tasks"
    echo -e "  • 成功: ${GREEN}$success_count${NC}"
    echo -e "  • 失败: ${RED}$failed_count${NC}"
    echo -e "  • 总耗时: ${total_duration} 秒"
    echo ""
    
    echo -e "${GREEN}🎉 所有任务已完成！${NC}"
    echo -e "${YELLOW}📁 结果保存在: $RESULTS_DIR${NC}"
    echo ""
}

# 运行主函数
main
