#!/bin/bash

# Quick Test Runner - 智能处理代理问题
# 自动检测并处理代理配置

echo "🔍 检查网络环境..."
echo ""

# 检查是否设置了代理
if [ ! -z "$https_proxy" ] || [ ! -z "$http_proxy" ]; then
    echo "⚠️  检测到代理配置:"
    [ ! -z "$https_proxy" ] && echo "   https_proxy = $https_proxy"
    [ ! -z "$http_proxy" ] && echo "   http_proxy = $http_proxy"
    echo ""
    
    # 测试代理是否可用
    proxy_host=$(echo $https_proxy | sed 's|http://||' | sed 's|https://||' | cut -d: -f1)
    proxy_port=$(echo $https_proxy | sed 's|http://||' | sed 's|https://||' | cut -d: -f2 | cut -d/ -f1)
    
    if nc -z -w2 "$proxy_host" "$proxy_port" 2>/dev/null; then
        echo "✅ 代理服务可用，将使用代理"
    else
        echo "❌ 代理服务不可用 (${proxy_host}:${proxy_port})"
        echo "   正在临时禁用代理..."
        unset https_proxy
        unset http_proxy
        unset HTTPS_PROXY
        unset HTTP_PROXY
        echo "✅ 已禁用代理"
    fi
    echo ""
fi

# 加载环境变量
if [ -f ".env" ]; then
    echo "📝 加载 .env 配置..."
    export $(cat .env | grep -v '^#' | xargs)
    echo "✅ 环境变量已加载"
    echo ""
fi

# 检查依赖
if [ ! -d "node_modules" ]; then
    echo "❌ 未安装依赖，请先运行: npm install"
    exit 1
fi

# 运行测试
if [ -z "$1" ]; then
    echo "📋 可用的测试选项:"
    echo "   ./quick-test.sh all          - 运行所有测试"
    echo "   ./quick-test.sh github       - 测试 GitHub MCP"
    echo "   ./quick-test.sh playwright   - 测试 Playwright MCP"
    echo "   ./quick-test.sh huggingface  - 测试 Huggingface MCP"
    echo "   ./quick-test.sh pydantic     - 测试 Pydantic MCP Run Python"
    echo "   ./quick-test.sh fetcher      - 测试 Fetcher MCP"
    echo "   ./quick-test.sh docker       - 测试 Docker MCP"
    echo ""
    echo "📊 内部时间测量 (DEBUG 模式):"
    echo "   ./quick-test.sh playwright-debug  - Playwright 内部时间分析"
    echo "   ./quick-test.sh fetcher-debug     - Fetcher 内部时间分析"
    echo "   ./quick-test.sh github-debug      - GitHub 内部时间分析"
    echo ""
    read -p "请选择: " choice
else
    choice=$1
fi

case $choice in
    all)
        echo "🚀 运行所有测试..."
        node test-all.js
        ;;
    github)
        echo "🚀 运行 GitHub MCP 测试..."
        node test-github.js
        ;;
    playwright)
        echo "🚀 运行 Playwright MCP 测试..."
        node test-playwright.js
        ;;
    huggingface)
        echo "🚀 运行 Huggingface MCP 测试..."
        node test-huggingface.js
        ;;
    pydantic)
        echo "🚀 运行 Pydantic MCP Run Python 测试..."
        node test-pydantic.js
        ;;
    fetcher)
        echo "🚀 运行 Fetcher MCP 测试..."
        node test-fetcher.js
        ;;
    docker)
        echo "🚀 运行 Docker MCP 测试..."
        node test-docker.js
        ;;
    playwright-debug)
        echo "🔍 运行 Playwright MCP DEBUG 模式..."
        node test-with-debug-logs.js
        echo ""
        echo "📊 正在分析日志..."
        node analyze-playwright-logs.js
        ;;
    fetcher-debug)
        echo "🔍 运行 Fetcher MCP DEBUG 模式..."
        node test-fetcher-with-debug-logs.js
        echo ""
        echo "📊 正在分析日志..."
        node analyze-fetcher-logs.js
        ;;
    github-debug)
        echo "🔍 运行 GitHub MCP DEBUG 模式..."
        node test-github-with-debug-logs.js
        ;;
    *)
        echo "❌ 无效选项: $choice"
        exit 1
        ;;
esac
