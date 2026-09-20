# Postman CLI 在旧 Linux 环境中的动态加载器兼容方案

## 问题背景

在较老的 Linux 环境中直接运行 `postman-cli`，可能出现以下错误：

```text
./postman-cli: /usr/lib64/libstdc++.so.6: version `CXXABI_1.3.11' not found
./postman-cli: /usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.14' not found
./postman-cli: /usr/lib64/libstdc++.so.6: version `GLIBCXX_3.4.19' not found
```

这说明 `postman-cli` 加载了系统自带的旧版 `libstdc++.so.6`，无法满足程序需要的符号版本。

当前机器已经准备了新版 GCC Runtime：

```text
/home/gcc-10/lib
```

目标是让 `postman-cli` 使用该目录中的动态加载器和运行库，而不是系统默认版本。

## 现象对比

普通 Node.js ELF 程序可以显式通过新版动态加载器启动：

```bash
exec /home/gcc-10/lib/ld-linux-x86-64.so.2 \
  --library-path /home/gcc-10/lib \
  /home/node-v22.12.0-linux-x64/bin/node \
  "$@"
```

但用同样方式启动 `postman-cli`：

```bash
exec /home/gcc-10/lib/ld-linux-x86-64.so.2 \
  --library-path /home/gcc-10/lib \
  /home/postman-cli
```

可能报错：

```text
Pkg: Error reading from file.
```

## 根因

`postman-cli` 是通过 `pkg` 打包的 Node.js 单文件程序。它不仅包含 ELF 和 Node Runtime，还在文件尾部附加了 JavaScript、Snapshot 和资源文件：

```text
postman-cli
├── ELF Header
├── Node Runtime
├── Native Code
└── pkg payload
    ├── JavaScript
    ├── Snapshot
    └── Resources
```

程序启动后，`pkg` Runtime 需要基于当前的主程序定位当前可执行文件，并从文件尾部读取 payload。

如果把 `ld-linux-x86-64.so.2` 作为 `exec` 的目标程序：

```text
Shell
  └── exec ld-linux
        └── 加载 postman-cli
              └── pkg Runtime
                    └── 基于当前主程序定位到 ld-linux
                          └── 尝试从 ld-linux 读取 payload（失败）
```

此时主程序入口是动态加载器。`pkg` Runtime 可能将 `ld-linux` 识别为当前可执行文件，并错误地从 `ld-linux` 文件尾部读取 payload，最终导致读取失败。

## 核心结论

不要使用下面的方式启动 `postman-cli`：

```bash
exec /home/gcc-10/lib/ld-linux-x86-64.so.2 \
  --library-path /home/gcc-10/lib \
  /home/postman-cli
```

推荐修改副本 ELF Header 中的 `PT_INTERP`，让 Kernel 在直接执行 `postman-cli` 时自动选择新的动态加载器：

```text
Shell
  └── exec /home/postman-cli.compat
        └── Kernel 读取 PT_INTERP
              └── /home/pm-ld.so
                    └── postman-cli.compat
                          └── pkg 读取自身 payload
```

这样，Shell 直接执行的仍然是 `postman-cli.compat`，能够最大程度保持 `pkg` 单文件程序原有的启动语义。

## 修改步骤

### 1. 设置路径

```bash
POSTMAN_DIR=/home
RUNTIME_DIR=/home/gcc-10/lib
```

### 2. 检查文件和动态加载器

```bash
test -x "$POSTMAN_DIR/postman-cli"
test -x "$RUNTIME_DIR/ld-linux-x86-64.so.2"

readelf -lW "$POSTMAN_DIR/postman-cli" |
  grep 'Requesting program interpreter'
```

预期原始 Interpreter 为：

```text
[Requesting program interpreter: /lib64/ld-linux-x86-64.so.2]
```

### 3. 创建动态加载器短链接

原 Interpreter 字符串长度有限，因此使用较短的固定路径：

```bash
ln -sfn \
  "$RUNTIME_DIR/ld-linux-x86-64.so.2" \
  /home/pm-ld.so
```

### 4. 复制兼容版本

保留原文件，不要直接修改：

```bash
cp -a \
  "$POSTMAN_DIR/postman-cli" \
  "$POSTMAN_DIR/postman-cli.compat"
```

### 5. 原位修改 `PT_INTERP`

将：

```text
/lib64/ld-linux-x86-64.so.2
```

替换为：

```text
/home/pm-ld.so
```

并使用 `\0` 补齐剩余空间：

```bash
perl -0777 -i -pe '
s{\Q/lib64/ld-linux-x86-64.so.2\E}{
  "/home/pm-ld.so" .
  "\0" x (
    length("/lib64/ld-linux-x86-64.so.2") -
    length("/home/pm-ld.so")
  )
}e
' "$POSTMAN_DIR/postman-cli.compat"
```

这里必须进行等长度原位替换，不能插入或删除字节。否则可能改变 `pkg` payload 的文件偏移，使内嵌资源无法读取。

## 验证

### 1. 验证 Interpreter

```bash
readelf -lW "$POSTMAN_DIR/postman-cli.compat" |
  grep 'Requesting program interpreter'
```

预期结果：

```text
[Requesting program interpreter: /home/pm-ld.so]
```

### 2. 验证动态库来源

```bash
LD_LIBRARY_PATH="$RUNTIME_DIR" \
  ldd "$POSTMAN_DIR/postman-cli.compat" |
  grep -E 'libstdc\+\+|libgcc_s'
```

确认 `libstdc++.so.6` 和 `libgcc_s.so.1` 来自：

```text
/home/gcc-10/lib
```

### 3. 验证 Postman CLI

```bash
LD_LIBRARY_PATH="$RUNTIME_DIR" \
  "$POSTMAN_DIR/postman-cli.compat" --version
```

此时不要再显式调用 `ld-linux-x86-64.so.2`。

## 最终包装脚本

可以创建 `/home/postman-cli.sh`：

```sh
#!/bin/sh

RUNTIME_DIR=/home/gcc-10/lib
POSTMAN_BIN=/home/postman-cli.compat

export LD_LIBRARY_PATH="$RUNTIME_DIR${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"

exec "$POSTMAN_BIN" "$@"
```

增加执行权限：

```bash
chmod +x /home/postman-cli.sh
```

使用示例：

```bash
/home/postman-cli.sh --version

/home/postman-cli.sh collection run postman/collections/speech-split \
  -e postman/environments/dev.environment.yaml \
  --verbose
```

## 注意事项

- 保留原始 `/home/postman-cli`，只修改复制后的兼容版本。
- 新 Interpreter 路径不能长于原路径，否则无法安全地原位替换。
- 不要使用会改变文件布局的方式修改这个 `pkg` 单文件程序。
- `PT_INTERP` 决定使用哪个动态加载器，`LD_LIBRARY_PATH` 决定优先从哪里加载共享库，两者作用不同。
- 升级 `postman-cli` 后，应从新的原始文件重新生成 `postman-cli.compat`。
- 如果仍出现 `GLIBC_*` 缺失，说明问题已超出 `libstdc++` 范畴，还需要检查新版 Runtime 与系统 glibc、内核之间的兼容性。

## 总结

本方案的关键是：

> 对于 `pkg` 打包的 Node.js 单文件程序，让 Kernel 通过 ELF `PT_INTERP` 选择新的动态加载器，不要把动态加载器本身作为程序入口执行。

最终运行方式为：

```bash
LD_LIBRARY_PATH=/home/gcc-10/lib \
  exec /home/postman-cli.compat "$@"
```

从 Kernel 的视角看，两种启动方式的关键区别是：

- 执行 `exec /home/postman-cli.compat` 时，Kernel 视角中的可执行文件是 `/home/postman-cli.compat`。随后 Kernel 根据该 ELF 的 `PT_INTERP` 再加载指定的动态加载器。
- 执行 `exec /home/gcc-10/lib/ld-linux-x86-64.so.2 xxxx` 时，Kernel 视角中的可执行文件是 `/home/gcc-10/lib/ld-linux-x86-64.so.2`，而 `xxxx` 只是传递给动态加载器的参数。

注意：`pkg` 拿到的是 `/proc/self/exe` 指向的路径，然后打开这个路径对应的文件，在文件中按照偏移读取 prelude 和 payload。

| 项目 | 写法 A：`exec ./postman-cli` | 写法 B：`exec ld.so --library-path ... ./postman-cli` |
|---|---|---|
| `/proc/self/exe` | `postman-cli` | `ld.so` |
