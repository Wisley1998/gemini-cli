#!/bin/bash
# 简易SWE-bench工具配置脚本

echo "🚀 开始配置简易SWE-bench所需的MCP工具..."

# 1. Git操作 (必需)
echo "📦 添加 Git MCP 服务器..."
gemini mcp add git npx -y @modelcontextprotocol/server-git --scope project

# 2. 文件系统增强 (推荐)
echo "📦 添加 Filesystem MCP 服务器..."
gemini mcp add filesystem npx -y @modelcontextprotocol/server-filesystem --scope project

# 3. 结构化思考 (可选)
echo "📦 添加 Sequential Thinking MCP 服务器..."
gemini mcp add sequential npx -y @modelcontextprotocol/server-sequential-thinking --scope project

echo "✅ 配置完成！"
echo ""
echo "📋 已添加的工具："
echo "  1. git - Git仓库操作"
echo "  2. filesystem - 增强的文件系统操作"
echo "  3. sequential - 结构化任务规划"
echo ""
echo "🔍 查看所有MCP服务器："
gemini mcp list
