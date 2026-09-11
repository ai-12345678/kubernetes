# Kubernetes Context 简介

**Context 是 kubectl 连接集群时使用的一套环境配置，身份只是其中一部分。**

```text
context = 集群（cluster）+ 身份（user）+ 默认命名空间（namespace）
```

| 字段 | 含义 | 示例 |
| --- | --- | --- |
| cluster | 连接哪个集群 | prod |
| user | 使用哪份认证配置 | readonly |
| namespace | 默认在哪个命名空间操作 | speech-prod |

例如，`prod-speech-readonly` 表示：使用 readonly 对应的认证配置，连接 prod 集群，默认操作 speech-prod 命名空间。

同一集群可以配置多个 context，分别使用不同身份或默认命名空间。Context 通常保存在 `~/.kube/config` 中。

## 常用命令

```bash
# 查看所有 context
kubectl config get-contexts

# 查看当前 context
kubectl config current-context

# 切换 context
kubectl config use-context prod-speech-readonly

# 仅本次命令指定 context
kubectl --context=prod-speech-readonly get pods

# 覆盖默认命名空间
kubectl get pods -n monitoring
```

## 注意

Context 是客户端配置，不决定权限。命名为 readonly 不会自动变成只读，实际权限由集群侧的授权机制（通常是 RBAC）决定。默认 namespace 也不代表只能访问该命名空间。
