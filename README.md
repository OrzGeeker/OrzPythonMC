# OrzMC 2.0

跨平台 Minecraft 客户端启动 / 服务端部署工具。Python 编写,提供 **Textual TUI** 与 **命令行直用** 两种模式,支持**多版本客户端/服务端并存**,Java 运行时**自动下载并收敛到应用目录**(不依赖系统 Java),发布为 **PyPI 包** 与 **各平台独立二进制**。

## 安装

### 方式一:PyPI(需要本机 Python 3.10+)

```bash
pip install orzmc-app
orzmc --help
```

### 方式二:独立二进制(GitHub Release)

从 [Releases](https://github.com/OrzGeeker/OrzPythonMC/releases) 下载对应平台的二进制(`orzmc-macos-*` / `orzmc-linux-*` / `orzmc-windows-*`),解压后直接运行,无需 Python / Java。

## 两种使用模式

```bash
orzmc            # 无子命令 → 打开 Textual TUI
orzmc tui        # 强制打开 TUI
orzmc client -v 1.20.4 -u player  # 命令行直用
```

TUI 提供四个页签:**客户端**(版本/用户名/类型/OptiFine/Fabric/内存)、**服务端**(类型/内存/EULA/ForceUpgrade/软链接)、**运维**(已装版本列表/移除/备份世界/刷新版本缓存/Java 状态)、**设置**(游戏根目录)。

## 命令行

```
orzmc [--verbose]                 # 无子命令 → TUI
orzmc client   [-v VER] [-u USER] [-t vanilla|forge] [-m MIN] [-x MAX]
               [--optifine] [--fabric] [--extract-music] [--jvm-opts ...]
orzmc server   [-v VER] [-t vanilla|paper|spigot|forge] [-m MIN] [-x MAX]
               [--force-upgrade] [--symlink] [--force-download] [--yes]
               [--jvm-opts ...] [--server-args ...]
orzmc remove   -v VER [--server -t TYPE] [--yes]
orzmc list
orzmc backup   [-v VER] [-t TYPE]
orzmc tui
orzmc version
```

- **版本缺省**:交互(TTY)时弹菜单选择;脚本/管道等非 TTY 场景自动使用 Mojang 最新 release。
- **运行即安装**:`client` / `server` 检测到文件缺失会自动下载安装,无需独立 `install` 子命令。
- **`remove`** 默认移除客户端;`--server -t TYPE` 移除指定类型的服务端;`--yes` 跳过确认。
- **Java**:版本要求来自版本 JSON 的 `javaVersion.majorVersion`(缺省 8);自动下载 Temurin JRE 装到 `java/<大版本>/`,仅 Spigot 构建需要 JDK。

## 目录结构(统一,多版本并存)

```
<root>/                                  # 默认 ~/minecraft,可在 TUI 设置页或 --root-dir 指定
  versions/<mc_version>/                 # 一个版本一目录,客户端/服务端并存
    client/   assets/  libraries/  natives/  <version>.jar  <version>.json  ...
    server/<type>/   <core>.jar  eula.txt  server.properties  world/  ...   # vanilla|paper|spigot|forge
  java/<java_major>/                     # 应用托管的 JRE/JDK(独立沙盒,不依赖系统 java)
  cache/version_manifest.json            # 版本清单缓存
  backup/worlds/<ver>-<type>-<ts>.zip    # 世界备份
  backup/music/<ver>/                    # --extract-music 提取的客户端音乐
```

## 开发

项目为 **uv workspace**(库 `orzmc` + 应用 `orzmc-app`)。架构约定见 [AGENTS.md](AGENTS.md)。

```bash
uv sync --all-packages        # 安装依赖(锁定 3.12 工具链)
uv run --all-packages pytest  # 全部测试(库 + 应用)
uv run ruff check .           # lint
uv run --all-packages mypy    # 类型检查
uv run orzmc tui              # 本地运行
uv build --all-packages       # 构建两个包
uv run --package orzmc-app python scripts/build.py   # 构建单文件二进制 → dist/orzmc
```

## 兼容性说明(v1 → v2)

- 旧顶层 `orzmc -s -v 1.20.4` 改为 `orzmc server -v 1.20.4`;客户端/服务端统一 `-v/-t/-m/-x`。
- 旧 `-E "a:..."` 改为 `--jvm-opts "..."` 与 `--server-args "..."`。
- 目录结构改为统一布局;`orzmc list` 可查看已装版本与类型,便于迁移。
- 移除 nginx/rsync/daemon/skin system/BMCLAPI 镜像等系统级能力;直连官方源。
