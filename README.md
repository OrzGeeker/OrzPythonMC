# OrzMC 2.0

[![站点](https://img.shields.io/badge/站点-OrzMC%20官网-15803d)](https://orzmc.github.io/OrzPythonMC/)

> 🏠 **项目主页**:<https://orzmc.github.io/OrzPythonMC/> — 一键安装指引、各平台独立二进制下载(自动识别平台)、功能与特性介绍。改动 `docs/` 推送即自动更新。

跨平台 Minecraft 客户端启动 / 服务端部署工具。Python 编写,提供**命令行直用**(交互式 rich 提示),支持**多版本客户端/服务端并存**,Java 运行时**自动下载并收敛到应用目录**(不依赖系统 Java),发布为 **PyPI 包** 与 **各平台独立二进制**。

## 安装

### 方式一:PyPI(需要本机 Python 3.10+)

```bash
pip install orzmc-app
orzmc --help
```

### 方式二:独立二进制(GitHub Release)

从 [Releases](https://github.com/OrzGeeker/OrzPythonMC/releases) 下载对应平台的二进制(`orzmc-macos-*` / `orzmc-linux-*` / `orzmc-windows-*`),解压后直接运行,无需 Python / Java。

## 使用方式

```bash
orzmc --help     # 帮助(无子命令时同样打印帮助)
orzmc client -v 26.2 -u player     # 命令行直用(-v 缺省时用 Mojang 最新 release)
```

交互式运行(有 TTY)时,缺省版本弹键盘导航选择器(默认光标在最新,`↑↓` 选择版本、`←→` 前后翻页(翻页键/首尾键同样可用),输入在当前列表中即时过滤,`t` 切换正式版/测试版、`x` 清空过滤,Enter 选中、Esc 用最新);选择器按终端尺寸响应式布局——选中行反显高亮、列表上下沿有「还有 N 个」滚动指示、搜索命中片段高亮、底部帮助拆成多行短句说明每个按键的作用(按列宽/行高自动增减,窄窗隐藏)。Java/EULA/移除等操作会逐行确认;脚本/管道等非 TTY 场景自动用 Mojang 最新 release 与默认值,不阻塞。

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

- **版本缺省**:交互(TTY)时弹全屏键盘导航选择器——默认光标落在最新正式版(直接 Enter 即选中),`↑/↓` 选择版本、`←/→`(及 `PgUp/PgDn`)前后翻页、`Home/End` 跳首尾,滚动整个通道的版本列表(默认视口最近 10 个);`←/→` 翻页仅在搜索框为空时生效,有查询时左右键用于移动光标改错字。输入即按子串过滤**当前列表**(正式版或测试版,命中片段高亮;想搜测试版/远古版本需先 `t` 切过去),`t` 切换正式版/测试版列表,`x` 清空过滤,Esc 退出用最新。选择器**响应式适配终端尺寸**:选中行反显高亮(无指针)、超视口时显示「↑/↓ 还有 N 个」滚动指示、底部帮助拆成多行短句说明每个按键的作用,按列宽放得下几条就显示几条、按行高保列表至少 3 行,窄窗自动隐藏帮助并缩窄视口(窗口运行中调整大小也会实时跟随)。脚本/管道等非 TTY 场景自动使用 Mojang 最新 release。
- **运行即安装**:`client` / `server` 检测到文件缺失会自动下载安装,无需独立 `install` 子命令。
- **服务端关闭**:运行中直接在终端输入 `stop` 保存退出;或按 **Ctrl-C**(CLI 会等待服务端保存退出,超过 60s 未退出才强制结束,不会遗留孤儿进程)。`--nogui` 以无窗口模式启动,控制台输入同样有效。
- **`remove`** 默认移除客户端;`--server -t TYPE` 移除指定类型的服务端;`--yes` 跳过确认。
- **类型**:客户端支持 `vanilla|fabric|forge`;服务端支持 `vanilla|paper|fabric|forge`(客户端 `-t paper` 会被拒绝,spigot 已并入 Paper)。
- **Java**:版本要求来自版本 JSON 的 `javaVersion.majorVersion`(缺省 8);自动下载 Temurin JRE 装到 `java/<大版本>/`(所有类型运行时均无需完整 JDK)。

## 常用示例

```bash
orzmc client -v 26.2 -u Steve          # 启动最新版(26.2)原版客户端(自动补齐文件)
orzmc client -v 26.2 -t fabric         # 以 Fabric 客户端启动(自动装 loader)
orzmc client -v 26.2 -t forge          # 以 Forge 客户端启动(官方安装器收割)
orzmc server -v 26.2 -t paper --yes    # 部署并启动 Paper 服务端(自动接受 EULA)
orzmc server -v 26.2 -t fabric --yes   # 部署并启动 Fabric 服务端
orzmc list                              # 查看已安装版本(客户端/服务端类型)
orzmc remove -v 26.2 --yes              # 移除最新版客户端
```

## 目录结构(统一,多版本并存)

```
<root>/                                  # 默认 ~/minecraft,可用 --root-dir 指定
  versions/<mc_version>/                 # 一个版本一目录,客户端/服务端并存
    client/   assets/  libraries/  natives/  <version>.jar  ...
    server/<type>/   <core>.jar  eula.txt  server.properties  world/  ...   # vanilla|paper|fabric|forge
  java/<java_major>/                     # 应用托管的 JRE/JDK(独立沙盒,不依赖系统 java)
  cache/version_manifest.json            # 版本清单缓存
  cache/versions/<mc_version>.json       # 版本元数据缓存(客户端/服务端共用)
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
uv run orzmc --help           # 本地运行(CLI)
uv build --all-packages       # 构建两个包
uv run --package orzmc-app python scripts/build.py   # 构建单文件二进制 → dist/orzmc
```

## 自动化验收与 CI

跨平台保证由三个 GitHub Actions 工作流承担(**6 平台** = macOS/Linux/Windows × x86_64/arm64):

- **`ci.yml`(每次 push/PR)**:`quality` 单 runner 跑格式 / lint / mypy / 测试 / 构建(平台无关,只跑一次);`test` 在 **6 平台全跑 pytest**(纯 Python 假件,秒级,专抓 OS 差异);`binary` 在**合并到 main 后** 6 平台构建 PyInstaller 二进制(PR 不跑,保持快速)。
- **`acceptance.yml`(每日 04:23 UTC + 手动触发)**:**真实验收** —— 真实下载 Minecraft / Java 并启动。版本策略**以最新版本为主基准**:`primary` 在 6 平台跑最新版 × 全部类型(vanilla/paper/fabric/forge 服务端 + vanilla/fabric/forge 客户端);`backcompat` 手动 `full` 套件时在 x86_64 三平台跑**旧版本后向兼容冒烟**(默认 `1.20.4`,`backcompat_versions` 输入可加 1.21.x 等)。
- **`release.yml`(打 `v*` 标签)**:6 平台各构建一个独立二进制挂到 GitHub Release;复用 `ci.yml` 作质量门禁。

验收 harness 即仓库内 `scripts/acceptance.py`(跨平台,不依赖 pgrep/pkill),本地可直接跑:

```bash
uv run --package orzmc-app python scripts/acceptance.py \
    --case server:vanilla:latest --case client:vanilla:latest \
    --backcompat "1.20.4" --root /tmp/orzmc-accept
```

版本来源遵循约束:最新版本号由 Mojang `version_manifest_v2.json` 的 `latest.release` 解析,不额外拉取其它源;各类型按各自官方源获取。

## 兼容性说明(v1 → v2)

- 旧顶层 `orzmc -s -v 26.2` 改为 `orzmc server -v 26.2`;客户端/服务端统一 `-v/-t/-m/-x`。
- 旧 `-E "a:..."` 改为 `--jvm-opts "..."` 与 `--server-args "..."`。
- 目录结构改为统一布局;`orzmc list` 可查看已装版本与类型,便于迁移。
- 移除 nginx/rsync/daemon/skin system/BMCLAPI 镜像等系统级能力;直连官方源。
