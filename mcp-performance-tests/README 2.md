# MCP Server Performance Tests

独立的MCP服务器性能测试套件，用于测量每个MCP工具执行任务的完整时间。

## 测试的MCP Servers

1. **GitHub MCP Server** - GitHub仓库操作
2. **Playwright MCP Server** - 浏览器自动化
3. **Huggingface MCP Server** - AI模型推理
4. **Pydantic MCP Run Python** - 沙箱环境Python代码执行
5. **Fetcher MCP Server** - 基于Playwright的网页抓取
6. **Docker MCP Server** - Docker容器和镜像管理

## 测量的时间指标

每个测试会测量以下完整流程的时间：

- 🚀 **MCP Server启动时间**
- 🤝 **协议握手时间** (初始化)
- 📦 **工具列表获取时间**
- ⚡ **工具执行时间**（包括冷启动、库加载等）
- 🔄 **第二次执行时间**（测试缓存效果）
- 🛑 **服务器关闭时间**

## 安装依赖

```bash
cd mcp-performance-tests
npm install
```

**⚠️ 如果遇到 `ECONNREFUSED` 错误**：你可能设置了代理但代理服务未运行（如 Clash VPN）

```bash
# 临时取消代理后安装
unset https_proxy && unset http_proxy && npm install
```

## 运行测试

### 🚀 快速测试（推荐，自动处理代理）

```bash
./quick-test.sh all          # 测试所有
./quick-test.sh github       # 单独测试 GitHub
./quick-test.sh playwright   # 单独测试 Playwright
./quick-test.sh huggingface  # 单独测试 Huggingface
./quick-test.sh pydantic     # 单独测试 Pydantic Run Python
./quick-test.sh fetcher      # 单独测试 Fetcher
./quick-test.sh docker       # 单独测试 Docker
```

### 使用 npm 脚本

```bash
npm test                     # 测试所有
npm run test:github          # GitHub MCP
npm run test:playwright      # Playwright MCP
npm run test:huggingface     # Huggingface MCP
npm run test:pydantic        # Pydantic MCP Run Python
npm run test:fetcher         # Fetcher MCP
npm run test:docker          # Docker MCP
```

## 环境变量

需要在 `.env` 文件中配置以下环境变量：

```bash
GITHUB_PERSONAL_ACCESS_TOKEN=your_token_here
HF_TOKEN=your_huggingface_token_here
```

或者直接在运行时导出：

```bash
export GITHUB_PERSONAL_ACCESS_TOKEN=your_token
export HF_TOKEN=your_token
npm test
```

## 输出格式

测试会输出详细的时间统计：

```
================================
GitHub MCP Server Performance Test
================================

[时间戳] 🚀 启动MCP服务器...
[时间戳] ⏱️  启动耗时: 1234ms

[时间戳] 🤝 初始化协议握手...
[时间戳] ⏱️  握手耗时: 567ms

[时间戳] 📦 获取可用工具列表...
[时间戳] ⏱️  工具列表耗时: 123ms
[时间戳] 📋 可用工具: 15个

[时间戳] ⚡ 执行工具: search_repositories
[时间戳] ⏱️  执行耗时: 2345ms

[时间戳] 🔄 第二次执行相同工具...
[时间戳] ⏱️  第二次执行耗时: 1234ms

[时间戳] 🛑 关闭MCP服务器...
[时间戳] ⏱️  关闭耗时: 56ms

📊 总耗时: 5679ms
```

## 测试场景

### GitHub MCP Server

- 搜索仓库
- 获取用户信息

### Playwright MCP Server

- 打开网页
- 截图
- 提取页面内容

### Huggingface MCP Server

- 文本生成
- 模型推理
- 情感分析

### Pydantic MCP Run Python

- 执行Python代码
- 沙箱环境隔离
- 自动依赖管理

### Fetcher MCP Server

- 网页内容抓取
- JavaScript执行
- 智能内容提取

## 注意事项

- 测试是独立的，不依赖gemini-cli
- 每个测试都会完整启动和关闭MCP服务器
- 时间包括所有开销（进程启动、协议握手、库加载等）
- Docker容器启动会比较慢（GitHub MCP Server）
- 首次运行可能需要下载Docker镜像或npm包
