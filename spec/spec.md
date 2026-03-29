---
title: OrzMC 重构规格
version: 1.0
scope: 保持功能不变的结构性重构
principles:
  - 功能一致
  - 简洁清晰
  - 避免过度设计
  - 逐步可交付
---

## 目标与边界

### 目标
- 保持客户端/服务端核心能力与现有 CLI 行为一致
- 提升可维护性、可测试性、稳定性与扩展性
- 结构清晰，便于后续快速迭代

### 边界
- 不新增业务功能与新命令
- 不改变现有 CLI 选项含义与默认行为
- 不引入复杂框架或重依赖
- 不重构为大型工程形态

## 使用场景与逻辑复核

### 场景一：启动客户端
- 用户通过 `orzmc` 启动
- 版本选择、用户名、客户端类型（pure/forge）与额外 jar 参数
- 下载并组装 Java 参数运行客户端

### 场景二：部署服务端
- 用户通过 `orzmc -s` 部署
- 支持 vanilla/spigot/paper/forge
- 生成服务端核心、修改 EULA、设置 offline 模式、可选备份与 forceUpgrade

### 场景三：运维扩展
- nginx 配置、systemd daemon、皮肤系统
- 这些操作可能修改系统级目录和服务

## 当前主要问题
- 模块职责混杂：Config/Client/Server/Downloader 集中业务与 IO
- 反向依赖：core 依赖 app
- 副作用分散：路径 getter 创建目录、import 注册 signal
- 外部命令散落：os.system/os.popen 造成不可测试与不可观测

## 架构重构目标结构

### 分层与依赖
- app：CLI 编排与用例入口
- domain：纯逻辑、参数构造、步骤计划
- infra：文件系统、网络、进程执行

依赖方向：app -> domain / infra，infra 不依赖 app

### 关键对象
- RuntimeOptions：CLI 解析结果，不含 IO
- PathLayout：路径拼装，不创建目录
- UseCase + Plan + Step：用例产生步骤计划，infra 执行

## 非功能性要求
- 结构化日志输出，可用 verbose/debug 控制
- 网络调用具备 timeout 与异常降级
- 所有系统级操作具备显式确认参数

## 兼容性约束
- CLI 参数兼容
- 文件结构与默认目录兼容
- 默认行为与当前版本一致
