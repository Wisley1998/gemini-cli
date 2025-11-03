# 新增 MCP Server 测试

## 🎉 新增内容

我们添加了两个新的 MCP Server 性能测试：

### 1. Pydantic MCP Run Python ⭐

**项目地址**: https://github.com/pydantic/mcp-run-python

**功能**: 在沙箱WebAssembly环境中安全执行Python代码

**特点**:

- ✅ 沙箱隔离执行
- ✅ 自动依赖管理
- ✅ 支持异步代码
- ✅ 完整的输出捕获（stdout, stderr, 返回值）

**配置**:

```json
{
  "mcpServers": {
    "pydantic-run-python": {
      "command": "uvx",
      "args": ["mcp-run-python@latest", "stdio"],
      "env": {}
    }
  }
}
```

**测试用例**:

1. 执行简单Python代码
2. 执行带依赖的Python代码（datetime）
3. 执行数学计算（math库）

**依赖要求**:

- Python（已安装）
- Deno（需要安装）
- uvx（Python包管理工具）

---

### 2. Fetcher MCP Server 🌐

**项目地址**: https://github.com/jae-jae/fetcher-mcp

**功能**: 使用Playwright headless浏览器抓取网页内容

**特点**:

- ✅ JavaScript支持（执行动态内容）
- ✅ 智能内容提取（Readability算法）
- ✅ 并行处理（批量抓取）
- ✅ 资源优化（阻止不必要的资源）
- ✅ 支持HTML和Markdown输出

**配置**:

```json
{
  "mcpServers": {
    "fetcher": {
      "command": "npx",
      "args": ["-y", "fetcher-mcp"],
      "env": {}
    }
  }
}
```

**测试用例**:

1. 抓取简单网页（example.com）并提取主要内容
2. 抓取并返回原始HTML
3. 批量抓取多个网页

**依赖要求**:

- Node.js（已安装）
- Playwright Chromium浏览器（首次使用会自动提示安装）

---

## 📋 完整的测试列表

现在我们有 **5个** MCP Server 测试：

| #   | MCP Server              | 命令                          | 测试内容           |
| --- | ----------------------- | ----------------------------- | ------------------ |
| 1   | GitHub                  | `./quick-test.sh github`      | 仓库搜索、用户信息 |
| 2   | Playwright              | `./quick-test.sh playwright`  | 网页导航           |
| 3   | Huggingface             | `./quick-test.sh huggingface` | AI模型推理         |
| 4   | **Pydantic Run Python** | `./quick-test.sh pydantic`    | Python代码执行 ⭐  |
| 5   | **Fetcher**             | `./quick-test.sh fetcher`     | 网页抓取 ⭐        |

---

## 🚀 快速开始

### 测试新增的 MCP Servers

```bash
cd mcp-performance-tests

# 测试 Pydantic Run Python
./quick-test.sh pydantic

# 测试 Fetcher
./quick-test.sh fetcher

# 测试所有（包括新增的）
./quick-test.sh all
```

### 或使用 npm 命令

```bash
npm run test:pydantic
npm run test:fetcher
npm test  # 测试所有
```

---

## 📊 预期性能指标

### Pydantic MCP Run Python

```
启动+握手:     ~2000ms  (uvx + Deno 初始化)
工具列表:      ~10ms
首次执行:      ~1000ms  (Python代码执行 + 依赖加载)
二次执行:      ~500ms   (缓存生效)
总耗时:        ~4秒
```

**关键特点**:

- 首次启动需要初始化Deno环境
- Python代码在WebAssembly沙箱中执行
- 支持自动安装Python包

---

### Fetcher MCP Server

```
启动+握手:     ~3000ms  (npx + Playwright 浏览器启动)
工具列表:      ~5ms
首次执行:      ~2500ms  (浏览器导航 + 内容提取)
二次执行:      ~1500ms  (浏览器已启动)
总耗时:        ~7秒
```

**关键特点**:

- 首次运行需要下载Chromium浏览器
- 支持JavaScript渲染的动态网页
- 智能提取主要内容（去除广告、导航等）

---

## ⚠️ 注意事项

### Pydantic Run Python

1. **需要安装 Deno**

   ```bash
   # macOS
   brew install deno

   # 或使用官方安装脚本
   curl -fsSL https://deno.land/install.sh | sh
   ```

2. **需要安装 uvx**

   ```bash
   pip install uv
   # 或
   pipx install uv
   ```

3. **首次运行较慢**
   - 需要下载和初始化Deno环境
   - 需要安装Python依赖包

---

### Fetcher MCP

1. **需要安装 Playwright 浏览器**
   首次使用会提示安装，或手动运行：

   ```bash
   npx playwright install chromium
   ```

2. **网络要求**
   - 需要访问目标网站
   - 某些网站可能有反爬虫机制

3. **资源消耗**
   - 浏览器会占用较多内存和CPU
   - 建议在良好的网络环境下测试

---

## 🔍 故障排除

### Pydantic Run Python 问题

**问题**: `uvx: command not found`

**解决**:

```bash
pip install uv
# 或
pipx install uv
```

**问题**: `deno: command not found`

**解决**:

```bash
brew install deno
# 或访问 https://deno.com/ 查看安装说明
```

---

### Fetcher MCP 问题

**问题**: `Chromium not found`

**解决**:

```bash
npx playwright install chromium
```

**问题**: `fetch_url tool not found`

**可能原因**: 工具名称可能不同，运行测试查看实际可用工具列表

**解决**: 检查测试输出中的工具列表，更新测试用例

---

## 📝 测试文件

新增的测试文件：

- `test-pydantic.js` - Pydantic MCP Run Python 测试
- `test-fetcher.js` - Fetcher MCP Server 测试

配置文件已更新：

- `package.json` - 添加了 `test:pydantic` 和 `test:fetcher` 脚本
- `quick-test.sh` - 添加了 `pydantic` 和 `fetcher` 选项
- `test-all.js` - 包含所有5个测试
- `.gemini/settings.json` - 添加了新的 MCP server 配置

---

## 🎯 测试目标

这些新测试帮助你测量：

### Pydantic Run Python

- ⏱️ WebAssembly 沙箱初始化时间
- ⏱️ Python 代码执行时间（冷启动 vs 热启动）
- ⏱️ 依赖包安装和加载时间
- ⏱️ 不同复杂度代码的执行性能

### Fetcher MCP

- ⏱️ Playwright 浏览器启动时间
- ⏱️ 网页加载和渲染时间
- ⏱️ 内容提取和转换时间（HTML → Markdown）
- ⏱️ 并行抓取的性能优势
- ⏱️ 缓存对性能的影响

---

## ✨ 总结

现在你有了一个完整的 MCP Server 性能测试套件，涵盖：

1. **版本控制** - GitHub MCP
2. **浏览器自动化** - Playwright MCP
3. **AI模型** - Huggingface MCP
4. **Python执行** - Pydantic Run Python ⭐ 新增
5. **网页抓取** - Fetcher MCP ⭐ 新增

所有测试完全独立，可以单独运行，自动处理代理问题！

**开始测试新功能**:

```bash
cd mcp-performance-tests
./quick-test.sh pydantic
./quick-test.sh fetcher
```

🚀 **祝测试愉快！**
