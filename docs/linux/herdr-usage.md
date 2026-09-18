# Herdr 使用笔记

## 简介

Herdr 是一个用于统一管理本地/远程终端、长期运行任务和 Coding Agent 会话的终端工作台。

当前使用版本：

- 本地 Herdr：`0.9.0`
- 远程 Herdr：`0.9.1`
- 当前组合使用效果较好

Herdr 采用 Client / Server 模型：Server 负责持有 pane、进程和会话状态，Client 负责终端 UI。退出或 detach Client 后，只要 Server 仍在运行，Pane 中的 Codex、Claude Code、Shell 等任务可以继续运行。

## 常见命令

### 启动 / 连接默认 Session

```bash
herdr
```

启动或连接默认 Herdr Session。

### 查看版本

```bash
herdr --version
```

### 查看 Session

```bash
herdr session list
```

输出 JSON：

```bash
herdr session list --json
```

> 注意：这里是 `herdr session list`，不是 `herdr --session list`。

### 连接指定 Session

```bash
herdr session attach codex
```

也可以在启动时直接指定 Session：

```bash
herdr --session codex
```

两种形式：

```text
herdr session attach codex   # session 子命令
herdr --session codex        # 启动参数
```

### 停止 Session

```bash
herdr session stop codex
```

停止默认 Session：

```bash
herdr session stop default
```

### 删除 Session

```bash
herdr session delete codex
```

### 连接远程 Herdr

如果 `~/.ssh/config` 中已经配置：

```sshconfig
Host dev
    HostName 192.168.1.10
    User root
    Port 22
```

可以直接：

```bash
herdr --remote dev
```

也可以使用完整 SSH 地址：

```bash
herdr --remote ssh://root@192.168.1.10:22
```

连接远程指定 Session：

```bash
herdr --remote dev --session codex
```

结构：

```text
本地 Herdr Client
        │
        │ SSH
        ▼
远程 Herdr Server
        │
        ├── Workspace
        ├── Tab
        ├── Pane
        └── Codex / Claude / Shell
```

远程机器负责运行 Pane 和任务，本地 Herdr 负责显示 UI、快捷键和交互。

### 管理远程机器

添加远程机器：

```bash
herdr machine add dev --label "Dev Server"
```

如果远程机器需要指定 Session：

```bash
herdr machine add dev \
  --label "Dev Server" \
  --remote-session codex
```

### Detach

默认快捷键：

```text
Ctrl+B → q
```

只会断开当前 Client，Server 和 Pane 中的任务继续运行。

重新连接：

```bash
herdr
```

### 停止 Herdr Server

```bash
herdr server stop
```

这与 detach 不同：停止 Server 会结束该 Session 下的 Pane 进程。

### 查看默认配置

```bash
herdr --default-config
```

生成配置文件：

```bash
mkdir -p ~/.config/herdr
herdr --default-config > ~/.config/herdr/config.toml
```

macOS / Linux 常用配置位置：

```text
~/.config/herdr/config.toml
```

修改配置后可以重新加载：

```bash
herdr server reload-config
```

## 推荐配置

### SSH

建议先在 `~/.ssh/config` 中定义远程机器：

```sshconfig
Host dev
    HostName 192.168.1.10
    User root
    Port 22
    IdentityFile ~/.ssh/id_ed25519
    ServerAliveInterval 30
    ServerAliveCountMax 3
```

先确认普通 SSH 正常：

```bash
ssh dev
```

再使用：

```bash
herdr --remote dev
```

如果 SSH 私钥有 passphrase，可先：

```bash
ssh-add
```

### Herdr Remote

`~/.config/herdr/config.toml`：

```toml
[remote]
manage_ssh_config = true
```

如果希望完全使用原始 SSH 配置：

```toml
[remote]
manage_ssh_config = false
```

## 常用命令速查

```bash
# 启动 / Attach 默认 Session
herdr

# 查看版本
herdr --version

# 查看所有 Session
herdr session list

# Attach 指定 Session
herdr session attach codex

# 启动时指定 Session
herdr --session codex

# 停止 Session
herdr session stop codex

# 删除 Session
herdr session delete codex

# 远程连接
herdr --remote dev

# 远程连接指定 Session
herdr --remote dev --session codex

# 添加远程机器
herdr machine add dev --label "Dev Server"

# 查看默认配置
herdr --default-config

# Reload 配置
herdr server reload-config

# 停止当前 Herdr Server
herdr server stop

# 更新 Herdr
herdr update
```

## 核心理解

Herdr 可以简单理解为：

```text
tmux
+
终端 UI
+
长期 Session
+
Coding Agent 管理
+
远程 SSH 管理
```

对于 Coding Agent 场景：

```text
Herdr
  └── Workspace
      └── Tab
          ├── Pane → Codex
          ├── Pane → Claude Code
          ├── Pane → Shell
          └── Pane → kubectl / logs
```

Herdr 负责管理终端和会话，Codex、Claude Code 等 Coding Agent 负责真正执行代码分析、修改和开发任务。
