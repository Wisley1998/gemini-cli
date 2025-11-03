#!/bin/zsh

# Hugging Face MCP 清理脚本
# 使用方法: ./clean-hf-mcp.sh [command]

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "${YELLOW}🔍 检查 Hugging Face MCP 服务器状态...${NC}"

# 查找所有 hf-mcp-server 进程
HF_PROCESSES=$(ps aux | grep -E "hf-mcp-server|@llmindset" | grep -v grep | wc -l | tr -d ' ')

if [ "$HF_PROCESSES" -eq 0 ]; then
    echo "${GREEN}✅ 没有发现残留的 hf-mcp-server 进程${NC}"
    
    # 检查端口
    if lsof -i :3000 >/dev/null 2>&1; then
        echo "${YELLOW}⚠️  端口 3000 被其他进程占用:${NC}"
        lsof -i :3000
    else
        echo "${GREEN}✅ 端口 3000 空闲${NC}"
    fi
else
    echo "${RED}❌ 发现 $HF_PROCESSES 个 hf-mcp-server 进程${NC}"
    echo ""
    ps aux | grep -E "hf-mcp-server|@llmindset" | grep -v grep
    echo ""
    
    # 如果有参数 -f 或 --force,自动清理
    if [ "$1" = "-f" ] || [ "$1" = "--force" ]; then
        echo "${YELLOW}🧹 正在清理进程...${NC}"
        pkill -f hf-mcp-server
        sleep 1
        echo "${GREEN}✅ 清理完成${NC}"
    else
        echo "${YELLOW}提示: 运行 '$0 --force' 来自动清理这些进程${NC}"
        echo ""
        echo "或手动执行:"
        echo "  pkill -f hf-mcp-server"
    fi
fi

echo ""
echo "现在可以安全地运行 gemini 命令了:"
echo "  gemini -p \"你的查询\" --yolo"
