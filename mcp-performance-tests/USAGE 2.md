# MCP 性能测试使用指南

## 📋 目录结构

```
mcp-performance-tests/
├── package.json              # 项目配置和依赖
├── README.md                 # 项目说明
├── USAGE.md                  # 本使用指南
├── .env                      # 环境变量配置（包含API tokens）
├── .env.example              # 环境变量模板
├── .gitignore               # Git忽略文件
├── run.sh                    # 快速启动脚本
│
├── utils.js                  # 工具函数（时间测量、日志等）
├── mcp-client.js            # MCP客户端封装
│
├── test-github.js           # GitHub MCP测试
├── test-playwright.js       # Playwright MCP测试
├── test-huggingface.js      # Huggingface MCP测试
└── test-all.js              # 运行所有测试
```

## 🚀 快速开始

### 1. 进入测试目录

```bash
cd mcp-performance-tests
```

### 2. 配置环境变量

编辑 `.env` 文件(已经使用你的tokens创建好了):

```bash
GITHUB_PERSONAL_ACCESS_TOKEN=your_github_token_here
HF_TOKEN=your_huggingface_token_here
```

### 3. 安装依赖

```bash
npm install
```

### 4. 运行测试

#### 方式1: 使用npm脚本

```bash
# 测试所有MCP服务器
npm test

# 单独测试某个服务器
npm run test:github        # GitHub MCP
npm run test:playwright    # Playwright MCP
npm run test:huggingface   # Huggingface MCP
```

#### 方式2: 使用快速测试脚本（推荐，自动处理代理）

```bash
# 自动检测并处理代理问题
./quick-test.sh all          # 运行所有测试
./quick-test.sh github       # 只测试 GitHub
./quick-test.sh playwright   # 只测试 Playwright
./quick-test.sh huggingface  # 只测试 Huggingface
```

#### 方式3: 使用交互式启动脚本

```bash
./run.sh
```

然后选择要运行的测试。

#### 方式4: 直接运行测试文件

```bash
node test-github.js
node test-playwright.js
node test-huggingface.js
node test-all.js
```

## 📊 测试输出示例

每个测试会输出详细的性能数据：

```
============================================================
GitHub MCP Server Performance Test
============================================================
测试 GitHub MCP Server 的完整执行时间
包括: Docker启动、协议握手、工具执行等所有阶段

[2025-10-14 11:30:00.123] 🚀 启动MCP服务器: docker run -i --rm ...
[2025-10-14 11:30:02.456] ⏱️  启动并连接耗时: 2333ms

[2025-10-14 11:30:02.456] 🤝 执行协议握手 (initialize)...
[2025-10-14 11:30:02.678] ✓ 协议版本: 2024-11-05
[2025-10-14 11:30:02.678] ✓ 服务器名称: github-mcp-server
[2025-10-14 11:30:02.678] ✓ 服务器版本: 1.0.0
[2025-10-14 11:30:02.678] ⏱️  握手耗时: 222ms

[2025-10-14 11:30:02.678] 📦 获取可用工具列表...
[2025-10-14 11:30:02.789] ✓ 发现 15 个可用工具

   可用工具:
   1. search_repositories
      Search for GitHub repositories by query
   2. get_repository
      Get detailed information about a specific repository
   ...

[2025-10-14 11:30:02.789] ⏱️  工具列表获取耗时: 111ms

────────────────────────────────────────────────────────────
[2025-10-14 11:30:02.789] 🧪 测试用例 1/2: 搜索仓库
────────────────────────────────────────────────────────────
[2025-10-14 11:30:02.789] ⚡ 执行工具: search_repositories
   参数: {
     "query": "model context protocol",
     "maxResults": 5
   }
[2025-10-14 11:30:05.123] ✓ 工具执行完成
   返回内容数: 5
   [0] text: Found 5 repositories...
[2025-10-14 11:30:05.123] ⏱️  工具 "search_repositories" 执行耗时: 2334ms

   🔄 第 2 次执行...
[2025-10-14 11:30:05.123] ⚡ 执行工具: search_repositories
[2025-10-14 11:30:06.789] ✓ 工具执行完成
[2025-10-14 11:30:06.789] ⏱️  工具 "search_repositories" 执行耗时: 1666ms

...

[2025-10-14 11:30:10.000] 🛑 关闭MCP连接...
[2025-10-14 11:30:10.050] ✓ MCP连接已关闭
[2025-10-14 11:30:10.050] ⏱️  关闭耗时: 50ms

============================================================
Performance Summary / 性能统计摘要
============================================================

📊 总体统计:
   启动耗时:      2333ms
   握手耗时:      222ms
   工具列表:      111ms
   首次执行:      2334ms
   二次执行:      1666ms
   性能提升:      28.6%
   关闭耗时:      50ms
   ────────────────────────────────────────
   总耗时:        8500ms

🔧 工具信息:
   可用工具数:    15个

============================================================

📋 测试用例详细耗时:
   1. 搜索仓库: 2334ms ✓
   2. 搜索仓库 (第2次): 1666ms ✓
   3. 获取仓库信息: 1234ms ✓

✅ GitHub MCP Server 测试完成!
```

## 🔍 测试内容说明

### GitHub MCP Server 测试

- **测试工具**: `search_repositories`, `get_repository`
- **测试内容**: 搜索仓库、获取仓库详情
- **特点**: Docker容器启动，冷启动较慢

### Playwright MCP Server 测试

- **测试工具**: `playwright_navigate`, `playwright_screenshot`, `playwright_evaluate`
- **测试内容**: 打开网页、截图、提取页面内容
- **特点**: 需要下载浏览器，首次运行较慢

### Huggingface MCP Server 测试

- **测试工具**: `generate_text`, `sentiment_analysis`, `text_classification`
- **测试内容**: 文本生成、情感分析、文本分类
- **特点**: 模型加载和推理，可能需要网络下载模型

## 📈 性能指标解释

每个测试测量以下时间：

1. **启动耗时**: 进程启动 + 传输层建立
2. **握手耗时**: MCP协议初始化
3. **工具列表**: 获取可用工具列表
4. **首次执行**: 第一次调用工具（包含冷启动、库加载）
5. **二次执行**: 第二次调用相同工具（测试缓存效果）
6. **关闭耗时**: 断开连接和清理
7. **总耗时**: 完整流程的总时间

## 🛠️ 自定义测试

你可以修改测试文件中的 `testConfig` 来自定义测试场景：

```javascript
const testConfig = {
  testCases: [
    {
      name: '测试名称',
      tool: '工具名称',
      args: {
        // 工具参数
      },
      repeat: 2, // 重复次数（可选）
    },
  ],
};
```

## 🐛 故障排除

### 问题1: npm install 失败 - ECONNREFUSED 错误

**原因**: 设置了代理但代理服务未运行（比如设置了 7890 端口但 Clash VPN 未开启）

**解决方案**:

```bash
# 方案A: 临时取消代理（推荐）
unset https_proxy
unset http_proxy
npm install

# 方案B: 启动你的代理服务（Clash等）
# 然后再运行 npm install

# 方案C: 检查代理设置
echo $https_proxy  # 查看当前代理
export https_proxy=""  # 清除代理
export http_proxy=""   # 清除代理
```

### 问题1.1: npm install 网络慢

**原因**: npm源在国外，下载慢

**解决方案**:

```bash
# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com
npm install

# 或使用cnpm
npm install -g cnpm --registry=https://registry.npmmirror.com
cnpm install
```

### 问题2: Docker相关错误（GitHub MCP）

**原因**: Docker未启动或无权限

**解决方案**:

```bash
# 检查Docker状态
docker ps

# 启动Docker Desktop
open -a Docker

# 拉取镜像
docker pull ghcr.io/github/github-mcp-server
```

### 问题3: 环境变量未生效

**原因**: .env文件未加载

**解决方案**:

```bash
# 手动导出环境变量
export GITHUB_PERSONAL_ACCESS_TOKEN=your_token
export HF_TOKEN=your_token

# 然后运行测试
npm test
```

### 问题4: MCP服务器超时

**原因**: 网络慢或服务器资源不足

**解决方案**:

- 检查网络连接
- 等待首次下载完成（Docker镜像、npm包、模型等）
- 增加超时时间（修改测试文件中的等待逻辑）

## 📝 注意事项

1. **首次运行较慢**: 需要下载Docker镜像、npm包、浏览器、模型等
2. **网络要求**: 某些操作需要访问GitHub、Huggingface等服务
3. **API限制**: GitHub API有速率限制，频繁测试可能受限
4. **资源消耗**: Docker和浏览器会消耗较多内存和CPU
5. **独立测试**: 这些测试完全独立于gemini-cli，可单独运行

## 🔐 安全提示

- `.env` 文件包含敏感信息，不要提交到Git
- `.gitignore` 已配置忽略 `.env` 文件
- 定期更新你的API tokens
- 不要在公共场合分享tokens

## 📚 更多信息

- MCP SDK文档: https://github.com/modelcontextprotocol/sdk
- GitHub MCP Server: https://github.com/github/github-mcp-server
- Playwright MCP: https://playwright.dev/
- Huggingface: https://huggingface.co/

## 🤝 贡献

如果你想添加更多测试或改进现有测试：

1. 在相应的测试文件中添加新的测试用例
2. 修改 `testConfig.testCases` 数组
3. 运行测试验证
4. 提交改进

---

**祝测试顺利！如有问题请查看故障排除部分或提issue。** 🚀
