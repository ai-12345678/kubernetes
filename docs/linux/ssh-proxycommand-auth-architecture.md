# SSH ProxyCommand + Auth 访问架构

## 架构图

```text
OpenSSH
  │
  │ ProxyCommand
  ▼
auth-cli（进行认证、鉴权、准入）
  │
  │ 传递目标信息：
  │ user / hostname / port
  ▼
auth-server（自动化操作）
  │
  │ connect(hostname:port)
  ▼
target:sshd
```

## 配置示例

```sshconfig
Host dev
    HostName 192.168.xx.xx
    User root

    PreferredAuthentications publickey,password
    PubkeyAuthentication yes
    PasswordAuthentication yes

    ProxyCommand auth-cli proxy %h %p %r
    ControlMaster auto
    ControlPath ~/.ssh/master-%r@%h:%p
    ControlPersist 8h
```

其中：

```text
%h = hostname
%p = port
%r = username
```

## 一句话说明

OpenSSH 通过 `ProxyCommand` 将目标的 `host / port / user` 传给 `auth-cli`；`auth-cli` 完成认证、鉴权和准入后，把目标信息提交给 `auth-server`；`auth-server` 执行自动化连接操作，建立到目标机器的通道，并透明转发后续 SSH 流量。
