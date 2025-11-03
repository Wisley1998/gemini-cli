#!/bin/bash

# MCP Performance Tests Setup and Run Script
# 设置和运行MCP性能测试的脚本

set -e

echo "╔═══════════════════════════════════════════════════════════════════╗"
echo "║                                                                   ║"
echo "║           MCP Performance Tests Setup                             ║"
echo "║           MCP 性能测试设置                                        ║"
echo "║                                                                   ║"
echo "╚═══════════════════════════════════════════════════════════════════╝"
echo ""

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js 18+"
    exit 1
fi

echo "✓ Node.js 版本: $(node --version)"

# 检查npm
if ! command -v npm &> /dev/null; then
    echo "❌ npm 未安装"
    exit 1
fi

echo "✓ npm 版本: $(npm --version)"
echo ""

# 检查.env文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，从模板创建..."
    cp .env.example .env
    echo "✓ 已创建 .env 文件，请编辑并填入你的API tokens"
    echo ""
    echo "需要配置:"
    echo "  - GITHUB_PERSONAL_ACCESS_TOKEN"
    echo "  - HF_TOKEN"
    echo ""
    read -p "按回车继续..."
fi

# 加载环境变量
if [ -f ".env" ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 安装依赖
if [ ! -d "node_modules" ]; then
    echo "📦 安装依赖..."
    npm install
    echo "✓ 依赖安装完成"
    echo ""
fi

# 选择测试
echo "请选择要运行的测试:"
echo "  1. 测试所有 MCP 服务器"
echo "  2. 只测试 GitHub MCP"
echo "  3. 只测试 Playwright MCP"
echo "  4. 只测试 Huggingface MCP"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo "运行所有测试..."
        npm test
        ;;
    2)
        echo ""
        echo "运行 GitHub MCP 测试..."
        npm run test:github
        ;;
    3)
        echo ""
        echo "运行 Playwright MCP 测试..."
        npm run test:playwright
        ;;
    4)
        echo ""
        echo "运行 Huggingface MCP 测试..."
        npm run test:huggingface
        ;;
    *)
        echo "❌ 无效选项"
        exit 1
        ;;
esac
