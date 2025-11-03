# Scripts 目录

这个目录包含了项目使用的各种实用脚本。

## Git 同步脚本

### `git-sync.sh` - 交互式 Git 同步工具

一个安全的、带二次确认的 Git 同步脚本。

**快速使用:**

```bash
# 拉取最新代码
./scripts/git-sync.sh pull
# 或
npm run git:pull

# 推送代码
./scripts/git-sync.sh push
# 或
npm run git:push

# 查看状态
./scripts/git-sync.sh status
# 或
npm run git:status
```

**详细文档:** 查看 [docs/git-sync-usage.md](../docs/git-sync-usage.md)

**主要特性:**

- ✅ 所有操作都需要人工二次确认
- ✅ 自动检测未提交的更改
- ✅ 彩色输出,清晰易读
- ✅ 安全的错误处理

## 其他脚本

- `build.js` - 构建脚本
- `start.js` - 启动脚本
- `clean.js` - 清理脚本
- `pre-commit.js` - Git pre-commit 钩子
- ...更多脚本请查看各自的文件
