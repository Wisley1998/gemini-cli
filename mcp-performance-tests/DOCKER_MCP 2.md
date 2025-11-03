# Docker MCP Server 测试文档

## 🐋 关于 Docker MCP Server

Docker MCP Server 是一个用于管理 Docker 容器、镜像、网络和卷的 MCP 服务器。它允许通过自然语言与 Docker 进行交互。

### 📦 安装

```bash
# 使用 uvx 安装（推荐）
uvx mcp-server-docker

# 或全局安装
pip install mcp-server-docker
```

### 🔧 配置

在 `.gemini/settings.json` 中添加：

```json
{
  "mcpServers": {
    "docker": {
      "command": "uvx",
      "args": ["mcp-server-docker"],
      "env": {}
    }
  }
}
```

### 🔨 提供的工具 (26个)

#### 容器管理 (8个)

- `list_containers` - 列出所有容器
- `create_container` - 创建新容器
- `run_container` - 运行容器
- `recreate_container` - 重建容器
- `start_container` - 启动容器
- `fetch_container_logs` - 获取容器日志
- `stop_container` - 停止容器
- `remove_container` - 删除容器

#### 镜像管理 (5个)

- `list_images` - 列出所有镜像
- `pull_image` - 从仓库拉取镜像
- `push_image` - 推送镜像到仓库
- `build_image` - 构建镜像
- `remove_image` - 删除镜像

#### 网络管理 (3个)

- `list_networks` - 列出所有网络
- `create_network` - 创建网络
- `remove_network` - 删除网络

#### 卷管理 (3个)

- `list_volumes` - 列出所有卷
- `create_volume` - 创建卷
- `remove_volume` - 删除卷

### 📊 测试用例

本测试包含以下测试用例（完整生命周期测试）：

1. **列出所有容器** - 测试容器查询性能
2. **列出所有镜像** - 测试镜像查询性能
3. **列出网络** - 测试网络配置查询
4. **列出卷** - 测试存储卷查询
5. **拉取轻量镜像** (alpine:latest) - 测试镜像拉取速度
6. **创建测试容器** - 测试容器创建性能
7. **启动测试容器** - 测试容器启动速度
8. **获取容器日志** - 测试日志读取性能
9. **停止测试容器** - 测试容器停止操作
10. **删除测试容器** - 测试容器清理操作
11. **删除测试镜像** - 测试镜像清理操作

### ⚡ 性能指标

测试会测量以下时间：

- **启动时间**: uvx + Docker SDK 初始化
- **工具发现**: 列出所有 26 个可用工具
- **镜像拉取**: 网络下载时间（alpine 约 3MB）
- **容器生命周期**: 创建 → 启动 → 日志 → 停止 → 删除
- **查询操作**: 列出容器、镜像、网络、卷的速度

### 🎯 使用场景

#### 场景 1: 快速开发环境

```bash
$ gemini

You: 启动一个 Redis 容器，端口 6379
# Docker MCP 自动创建并启动容器
```

#### 场景 2: 微服务部署

```bash
You: 部署 WordPress + MySQL，暴露在 8080 端口
# Docker MCP 创建网络、卷、启动两个容器
```

#### 场景 3: 容器调试

```bash
You: 我的 app-container 挂了，查看日志
# Docker MCP 获取日志并分析错误
```

#### 场景 4: 资源清理

```bash
You: 清理所有未使用的镜像和容器
# Docker MCP 列出并删除无用资源
```

### ⚠️ 注意事项

1. **Docker 必须运行**: 测试前确保 Docker daemon 正在运行

   ```bash
   docker ps  # 检查 Docker 是否运行
   ```

2. **权限要求**: 确保当前用户有 Docker 操作权限

   ```bash
   # macOS/Linux: 添加到 docker 组
   sudo usermod -aG docker $USER
   ```

3. **网络要求**: 拉取镜像需要网络连接

4. **安全警告**:
   - 不要在生产环境使用敏感数据
   - 审查 AI 创建的容器配置
   - 不支持 `--privileged` 等危险选项

### 🚀 运行测试

```bash
# 使用快速测试脚本
./quick-test.sh docker

# 或使用 npm
npm run test:docker

# 或直接运行
node test-docker.js
```

### 📈 预期性能

基于初步测试的预期性能（仅供参考）：

- **启动时间**: 3-5 秒（uvx + Docker SDK）
- **工具列表**: < 10ms
- **查询操作**: 10-50ms（取决于现有容器数量）
- **镜像拉取**: 5-30 秒（取决于镜像大小和网络）
- **容器创建**: 100-500ms
- **容器启动**: 100-500ms

### 🔗 相关链接

- GitHub: https://github.com/ckreiling/mcp-server-docker
- 官方文档: [Docker MCP Server README](https://github.com/ckreiling/mcp-server-docker#readme)
- Docker SDK: https://docker-py.readthedocs.io/

### 🐛 故障排查

#### 问题 1: "Cannot connect to Docker daemon"

```bash
# 解决方法: 启动 Docker Desktop (macOS) 或 Docker 服务 (Linux)
# macOS: 打开 Docker Desktop 应用
# Linux: sudo systemctl start docker
```

#### 问题 2: "Permission denied"

```bash
# 解决方法: 添加用户到 docker 组
sudo usermod -aG docker $USER
# 然后注销重新登录
```

#### 问题 3: "Image not found"

```bash
# 解决方法: 检查网络连接和镜像名称
docker pull alpine:latest  # 手动测试
```

#### 问题 4: uvx 未安装

```bash
# 解决方法: 安装 uv
pip install uv
# 或使用 Homebrew (macOS)
brew install uv
```
