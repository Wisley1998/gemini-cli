# MCP 性能测试 - 快速开始 ⚡

## 你遇到的问题解决了！ ✅

**问题**: `npm install` 失败，`ECONNREFUSED`  
**原因**: 设置了 `https_proxy=http://127.0.0.1:7890` 但 Clash VPN 没开  
**解决**: 已通过 `unset https_proxy && npm install` 成功安装依赖

---

## 📦 已完成的设置

✅ 创建了独立的 `mcp-performance-tests/` 文件夹  
✅ 安装了所有依赖（`@modelcontextprotocol/sdk`）  
✅ 配置了环境变量（`.env` 文件，包含你的 tokens）  
✅ 创建了三个 MCP server 的性能测试

---

## 🚀 现在就可以运行测试！

### 方式 1: 快速测试脚本（推荐）

```bash
cd mcp-performance-tests

# 自动处理代理问题，运行所有测试
./quick-test.sh all

# 或单独测试某个
./quick-test.sh github
./quick-test.sh playwright
./quick-test.sh huggingface
```

### 方式 2: 使用 npm 命令

```bash
cd mcp-performance-tests

# 测试所有
npm test

# 单独测试
npm run test:github
npm run test:playwright
npm run test:huggingface
```

---

## 📊 测试内容

### 1. GitHub MCP Server

- ⏱️ Docker 启动时间
- 🔧 工具: `search_repositories`, `get_repository`
- 📝 测试仓库搜索和信息获取

### 2. Playwright MCP Server

- ⏱️ npx + 浏览器启动时间
- 🔧 工具: `playwright_navigate`, `playwright_screenshot`, `playwright_evaluate`
- 📝 测试网页操作和截图

### 3. Huggingface MCP Server

- ⏱️ npx + 模型加载时间
- 🔧 工具: `generate_text`, `sentiment_analysis`, `text_classification`
- 📝 测试 AI 模型推理

---

## 📈 你会看到什么输出

每个测试会显示详细的时间统计：

```
============================================================
GitHub MCP Server Performance Test
============================================================

[时间] 🚀 启动MCP服务器...
[时间] ⏱️  启动并连接耗时: 2333ms

[时间] 🤝 执行协议握手...
[时间] ⏱️  握手耗时: 222ms

[时间] 📦 获取可用工具列表...
[时间] ⏱️  工具列表获取耗时: 111ms

[时间] ⚡ 执行工具: search_repositories
[时间] ⏱️  工具执行耗时: 2334ms

[时间] 🔄 第二次执行（测试缓存）...
[时间] ⏱️  第二次执行耗时: 1666ms

📊 总体统计:
   启动耗时:      2333ms
   握手耗时:      222ms
   工具列表:      111ms
   首次执行:      2334ms
   二次执行:      1666ms
   性能提升:      28.6%
   总耗时:        8500ms
```

---

## 🔧 如果遇到问题

### Docker 问题（GitHub MCP）

```bash
# 确保 Docker 运行
docker ps

# 启动 Docker Desktop
open -a Docker
```

### 代理问题

```bash
# 检查代理设置
echo $https_proxy

# 临时取消代理
unset https_proxy
unset http_proxy
```

### 环境变量问题

```bash
# 手动导出(如果自动加载失败)
export GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
export HF_TOKEN=your_huggingface_token_here
```

---

## 📚 文档

- **README.md** - 项目概述
- **USAGE.md** - 详细使用指南（你现在应该看的）
- **QUICKSTART.md** - 本文档，快速开始

---

## 🎯 下一步

1. **运行第一个测试**:

   ```bash
   ./quick-test.sh github
   ```

2. **查看详细说明**:

   ```bash
   cat USAGE.md
   ```

3. **自定义测试**:
   - 编辑 `test-*.js` 文件中的 `testConfig`
   - 添加更多测试用例

---

## ✨ 特点

- ✅ 完全独立，不依赖 gemini-cli
- ✅ 测量完整时间（启动、握手、执行、关闭）
- ✅ 自动重试测试缓存效果
- ✅ 详细的时间统计和日志
- ✅ 智能处理代理问题
- ✅ 支持单独或批量测试

---

**准备好了吗？运行你的第一个测试吧！** 🚀

```bash
cd mcp-performance-tests
./quick-test.sh all
```
