# AGENTS.md — OrzMC 项目事实来源

> 本文件是本仓库的**单一事实来源**。Claude Code / Codex / Cursor / Copilot 等任何 AI 智能体在动手前必须先读本文件。
> 项目有版本漂移风险时,优先依据本文件,而不是旧代码或记忆。若发现本文件与代码不符,请先更新本文件并同步代码。

## 项目定位

OrzMC 是一个跨平台 Minecraft **客户端启动 / 服务端部署** CLI + TUI 工具。**应用 + 库**双层结构:

- **`orzmc`(库)**:可复用能力,独立发布到 PyPI,高测试覆盖。零框架依赖(仅 requests / beautifulsoup4 / pyyaml / rich)。
- **`orzmc-app`(应用)**:Textual TUI + typer CLI,提供 `orzmc` 命令。只调用库的**公共 API**,不触碰库内部实现。

用户最终体验:无参 `orzmc` 打开 TUI;`orzmc client/server` 等直接命令行使用;版本缺失自动安装;Java 运行时沙盒托管在应用目录下,不依赖系统 java。

## 技术选型

| 项 | 选择 | 说明 |
|---|---|---|
| 包管理 | **uv**(workspace) | 根 pyproject 声明成员;`uv.lock` 提交入库,保证可复现 |
| 构建 | hatchling | 库版本动态读取自 `orzmc/version.py`(唯一版本源) |
| Python | `>=3.10` | 工具链固定 **3.12**(`uv python pin 3.12`) |
| TUI | Textual | 无参入口 |
| CLI | typer | 子命令结构 |
| 测试 | pytest + ruff + mypy | 库测试不打真实网络 / 系统 java |

## 架构与依赖方向

```
orzmc_app(应用:cli/ + ui/)  →  orzmc 公共 API
orzmc/services → orzmc/core → orzmc/domain + orzmc/infra
```

- **依赖只允许单向向下**:`domain` 与 `infra` 最底层;`core` 适配外部 API(Mojang/Forge/Paper/Adoptium);`services` 编排用例。
- **协议解耦**:`orzmc/infra/log.py` 定义 `Reporter`,`orzmc/infra/progress.py` 定义 `ProgressSink`。库内置 rich 默认实现;应用层注入 Textual 实现。**禁止**库内直接 `print` / `os.system`。
- **路径纯函数**:`PathLayout`(domain)只拼路径、**不建目录**;建目录统一在 service 内 `fs.ensure_dir`。
- **Java 沙盒**:运行时安装在 `<root>/java/<major>/`,用 `bin/java` 启动;版本要求读自版本 JSON `javaVersion.majorVersion`(缺失默认 8)。JRE 优先,仅 Spigot 构建需 JDK。

## 目录结构

```
python/                         # uv workspace 根
  pyproject.toml  uv.lock  AGENTS.md  README.md
  .github/workflows/{ci,release}.yml  scripts/build.py
  orzmc/                        # 库包(name="orzmc",py.typed)
    pyproject.toml
    orzmc/  version.py  __init__.py
            domain/  infra/  core/  services/
    tests/
  orzmc_app/                    # 应用包(name="orzmc-app")
    pyproject.toml
    orzmc_app/  cli/  ui/  __init__.py
    tests/
```

游戏根目录(默认 `~/minecraft`,可配置),统一多版本并存布局,由库内 `PathLayout` 负责:

```
<root>/
  versions/<mc_version>/          # 一版本一目录,客户端/服务端并存
    client/  assets/  libraries/  natives/  profiles/
             <version>.jar  <version>.json  launcher_profiles.json
    server/<server_type>/         # vanilla|paper|spigot|forge
      <core>.jar  eula.txt  server.properties  commands.yml  world/  plugins/
  java/<java_major>/              # 托管 JRE/JDK,不依赖系统 java
  cache/version_manifest.json  cache/download_tmp/
  backup/worlds/  backup/music/<v>/
```

## 常用命令

```bash
uv python pin 3.12                  # 固定工具链
uv sync --all-packages              # 安装全部成员 + 开发依赖(首次 / 依赖变更后)
uv run ruff check .                 # lint
uv run ruff format --check .        # 格式检查
uv run --all-packages pytest        # 全部测试
uv run mypy                         # 类型检查
uv run orzmc --help                 # 应用子命令树
uv run orzmc version                # 打印版本(读取库 version.py)
uv run orzmc tui                    # 打开 TUI
uv build --all-packages            # 构建 sdist+wheel(库与应用)
uv publish                         # 发布到 PyPI
uv run --package orzmc-app python scripts/build.py   # PyInstaller 单文件二进制 → dist/
uv lock                            # 锁定依赖
```

## 代码规范

- **ruff**:`select = E,F,W,I,UP,B,SIM,C4,RUF`,`line-length = 120`;isort first-party = `orzmc, orzmc_app`。
- **mypy**:`check_untyped_defs`,`no_implicit_optional`。
- **pytest**:库测试用 **fake `Reporter`/`ProgressSink`/内存文件系统**,直接打公共 API 与 domain;不碰网络、不碰系统 java。测试文件放 `orzmc/tests/`、`orzmc_app/tests/`。
- **导入规范**:库内按层引用(`from orzmc.domain...`);应用只 `from orzmc import ...` 公共 API。
- **异常**:网络 / 文件错误在 service 层统一捕获并转 `RuntimeError`(中文消息),不裸抛 requests 异常。
- **类型注解**:公共 API 全量注解;`from __future__ import annotations` 开头。

## 改动流程

新增 / 修改能力时必须遵循:

1. **先在库实现 + 测试**:在 `orzmc/` 对应层改代码,`orzmc/tests/` 补用例;`uv run --all-packages pytest` 全绿后再进应用层。
2. **再暴露公共 API**:把新能力加入 `orzmc/__init__.py`(公共 API 即契约,改动要谨慎)。
3. **应用层调用**:`orzmc_app/cli/`、`orzmc_app/ui/` 只调用公共 API,不 import 库内部模块。
4. **跑全部门禁**:`ruff` → `mypy` → `pytest` → `uv build` 全过。
5. **更新本文件**:涉及架构 / 命令 / 目录结构 / 规范的变更,同步更新 AGENTS.md(并考虑 README)。
6. 关键决策记录在本文件,避免各智能体行为漂移。

## 发布

- 双通道:**GitHub Release**(各平台 PyInstaller 二进制,见 `release.yml`)+ **PyPI**(`orzmc` 与 `orzmc-app` 双包,`uv publish`)。
- 版本号唯一源:`orzmc/version.py` 的 `__version__`。发版前提升它,并同步 `orzmc_app/pyproject.toml` 的 `version`。
- CI 只做质量门禁与发布,**不**负责版本号管理。
