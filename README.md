# OrzMC 2.0

[![官网](https://img.shields.io/badge/官网-orzmc.github.io/OrzPythonMC-15803d)](https://orzmc.github.io/OrzPythonMC/)
[![PyPI](https://img.shields.io/pypi/v/orzmc-app?label=orzmc-app)](https://pypi.org/project/orzmc-app/)
[![License](https://img.shields.io/github/license/OrzMC/OrzPythonMC)](LICENSE)

跨平台 Minecraft **客户端启动 / 服务端部署**工具,一条命令即可安装与启动。多版本并存、Java 运行时自动托管(不依赖系统 Java),发布为 PyPI 包与各平台独立二进制。

## 核心特性

- **多版本并存**:客户端 / 服务端一版本一目录,互不干扰
- **Java 自动托管**:按版本下载 JRE 到应用目录,无需系统 Java
- **即装即用**:文件缺失自动补齐,无需独立 install 步骤
- **服务端一键部署**:自动接受 EULA、写配置;`--nogui` 无窗口启动,`stop` / Ctrl-C 优雅关闭
- **交互式版本选择器**:键盘导航 TUI,输入即过滤,响应式适配终端尺寸
- **跨平台**:macOS / Linux / Windows × x86_64 / arm64,发布即用

## 安装

**方式一:PyPI(推荐,需 Python 3.10+)**

```bash
pip install orzmc-app
orzmc --help
```

**方式二:独立二进制(无需 Python / Java)**

从 [Releases](https://github.com/OrzMC/OrzPythonMC/releases) 下载对应平台的二进制(`orzmc-macos-*` / `orzmc-linux-*` / `orzmc-windows-*`),解压后直接运行。官网页面会自动识别你的平台,给出对应下载链接。

## 快速开始

```bash
# 启动最新版(26.2)原版客户端;-v 缺省时自动用 Mojang 最新 release
orzmc client -v 26.2 -u Steve

# 以 Fabric / Forge 启动客户端(自动装 loader / 官方安装器收割)
orzmc client -v 26.2 -t fabric
orzmc client -v 26.2 -t forge

# 部署并启动 Paper / Fabric 服务端(自动接受 EULA)
orzmc server -v 26.2 -t paper --yes --nogui
orzmc server -v 26.2 -t fabric --yes

# 管理已安装版本
orzmc list
orzmc remove -v 26.2 --yes
```

## 命令行

```
orzmc [--verbose]                 # 无子命令 → 打印帮助
orzmc client   [-v VER] [-u USER] [-t vanilla|fabric|forge] [-m MIN] [-x MAX]
               [--extract-music] [--jvm-opts ...]
orzmc server   [-v VER] [-t vanilla|paper|fabric|forge] [-m MIN] [-x MAX]
               [--force-upgrade] [--symlink] [--force-download] [--yes]
               [--jvm-opts ...] [--server-args ...] [--nogui]
orzmc remove   -v VER [--server -t TYPE] [--yes]
orzmc list
orzmc backup   [-v VER] [-t TYPE]
orzmc version
```

要点:

- **版本缺省**:有 TTY 时弹出键盘导航选择器(`↑↓` 选择、`←→` / PgUp / PgDn 翻页、输入即过滤、`t` 切正式 / 测试版、`x` 清空、Enter 选中、Esc 用最新);脚本 / 管道等非 TTY 场景自动用最新 release 与默认值,不阻塞。
- **运行即安装**:`client` / `server` 检测到文件缺失会自动下载补齐。
- **服务端关闭**:终端输入 `stop` 保存退出,或按 **Ctrl-C**(等待保存退出,超 60s 才强制结束,不留孤儿进程)。
- **类型**:客户端 `vanilla|fabric|forge`;服务端 `vanilla|paper|fabric|forge`。
- **Java**:版本要求读自版本 JSON,自动下载 Temurin JRE 到 `java/<大版本>/`,无需完整 JDK。

## 目录结构(统一,多版本并存)

```
<root>/                                  # 默认 ~/minecraft,可用 --root-dir 指定
  versions/<mc_version>/                 # 一个版本一目录,客户端/服务端并存
    client/   assets/  libraries/  natives/  <version>.jar  ...
    server/<type>/   <core>.jar  eula.txt  server.properties  world/  ...
  java/<java_major>/                     # 应用托管的 JRE/JDK,不依赖系统 java
  cache/  backup/worlds/  backup/music/<ver>/
```

## 开发

项目为 **uv workspace**(库 `orzmc` + 应用 `orzmc-app`),架构约定见 [AGENTS.md](AGENTS.md)。

```bash
uv sync --all-packages        # 安装依赖(锁定 3.12 工具链)
uv run --all-packages pytest  # 全部测试(库 + 应用)
uv run ruff check .           # lint
uv run --all-packages mypy    # 类型检查
uv build --all-packages       # 构建两个包
```

## 自动化验收与 CI

跨平台由三个 GitHub Actions 工作流保证(**6 平台** = macOS / Linux / Windows × x86_64 / arm64):

- **`ci.yml`**(push / PR):质量门禁 + 6 平台 pytest + 合并后 6 平台二进制构建
- **`acceptance.yml`**(每日 + 手动):真实下载 Minecraft / Java 并启动,以最新版为主基准,`backcompat` 冒烟旧版本
- **`release.yml`**(打 `v*` 标签):6 平台二进制挂 Release + `orzmc` / `orzmc-app` 双包发布 PyPI

本地跑真实验收:

```bash
uv run --package orzmc-app python scripts/acceptance.py \
    --case server:vanilla:latest --case client:vanilla:latest \
    --root /tmp/orzmc-accept
```

## 兼容性说明(v1 → v2)

- 旧顶层 `orzmc -s -v 26.2` 改为 `orzmc server -v 26.2`;客户端 / 服务端统一 `-v/-t/-m/-x`。
- 旧 `-E "a:..."` 改为 `--jvm-opts "..."` 与 `--server-args "..."`。
- 目录结构改为统一布局;`orzmc list` 可查看已装版本与类型,便于迁移。
- 移除 nginx / rsync / daemon 等系统级能力;直连官方源。
