---
title: OrzMC 重构任务清单
version: 1.0
---

## 阶段 0：稳定性修复
- 修复 Forge 构建流程调用错误
- Downloader 增加超时与 Content-Length 缺失容错
- 高风险系统操作增加显式确认参数

## 阶段 1：抽象基础设施
- 新增 infra 层：runner/http/fs
- 迁移外部命令调用到 runner
- 迁移网络请求到 http

## 阶段 2：拆分配置与路径
- 引入 RuntimeOptions 与 PathLayout
- 移除 Config getter 中的副作用
- 逐步替换调用点

## 阶段 3：用例化 Client/Server
- 将 Client/Server 拆为 UseCase + Plan + Steps
- 保持行为一致，避免引入新流程
- 增加最小单元测试

## 阶段 4：清理全局副作用
- CleanUp 改为显式启用
- Downloader 全局状态移至实例
