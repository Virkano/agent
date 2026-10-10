# Feature Requests

Capabilities requested by the user.

---

## [FEAT-20260910-001] construction-scheme-breadth-first-v1

**Logged**: 2026-09-10T11:45:00+08:00
**Priority**: critical
**Status**: in_progress
**Area**: product, backend, frontend, integration, operations

### Requested Capability
以原始建设方案和功能对比表为唯一基线，先将全部建设内容做出一版可运行、可演示、可验收的粗粒度 V1，再统一进入专项优化，避免继续在单个模块上纵向做深而遗漏整体范围。

### Progress
- 已重新提取 Word 建设方案的功能、体系架构、安全、数据、接口、部署和性能要求。
- 已提取 Excel Sheet1 的 38 项能力及 Sheet2 的模块目录。
- 已建立 `docs/建设方案全量粗粒度V1实施计划.md`，按 X01～X38 映射到 M00～M12。
- 已按代码、迁移、前端入口、测试和验收文档重新核对完成度，并改为“未做 > 部分完成 > 基本完成 > 已完成冻结”的优先级。
- 已完成 P0-01 / M04-01 AI 分析报告中心最小闭环：营销数据计算、财务参数、模板版本、规则/LLM 解读、报告库、失败留痕与重试。
- 已完成工作空间角色校验、正式迁移、71 项营销回归、前端静态门禁和真实浏览器生成/滚动验收。
- 下一开发任务为 P0-02 / M04-02 归因、图表、订阅与 HTML/PDF/Word 分发。

### Metadata
- Frequency: recurring
- Related Features: service assistant, recommendation, report, scheduling, IVR, Xiaoda, rehearsal, MLflow

---

## [FEAT-20260909-001] knowledge-retrieval-evaluation-center

**Logged**: 2026-09-09T10:00:00+08:00
**Priority**: high
**Status**: complete
**Area**: backend, frontend, diagnostics

### Requested Capability
在知识库详情中提供完整的检索评估中心，用固定问题集对比向量、关键词、混合和重排链路，并将开发中遇到的数据库与本地服务问题沉淀为可复用文档。

### Progress
- 已完成评估样本 CRUD、跨知识库目标校验和历史快照保留。
- 已完成 CSV 模板、批量原子导入、重复问题跳过和评估样本导出，可维护 20～50 条真实脱敏评估集。
- 已完成多模式批量执行、Recall@K、命中率、MRR、无答案率、错误和耗时指标。
- 已完成依赖健康检查、执行历史、逐条召回详情和 CSV 导出。
- 已完成知识库详情入口、响应式评估看板和权限隔离。
- 已完成数据库迁移、专项/回归测试、前端生产构建和真实检索事务回滚验收。
- 已新增项目级 `AGENTS.md` 和 `docs/开发与运维排障手册.md`，固化 PostgreSQL、Django、本地向量模型和 Ollama 的诊断顺序。

### Metadata
- Frequency: recurring
- Related Features: knowledge hit test, local embedding, Ollama, marketing RAG

---

## [FEAT-20260907-002] marketing-operations-dashboard

**Logged**: 2026-09-07T14:31:00+08:00
**Priority**: high
**Status**: complete
**Area**: backend, frontend

### Requested Capability
在现有营销闭环基础上建立工作空间级运营监控，统一查看任务、客户对话、响应速度、回答质量、发送前处理、逾期批次和转化结果。

### User Context
营销功能已经可以执行和质检，需要让管理员快速知道系统是否正常、哪些任务有问题以及应该进入哪里处理。

### Complexity Estimate
medium

### Progress
- 已完成近 7/30/90 天与单任务筛选。
- 已完成客户对话、成功率、响应时间、Token、质检、拦截、旁路、逾期批次和转化指标。
- 已完成每日运行趋势、工作空间健康结论、待关注事项和任务健康明细。
- 已完成异常事项到对话质检或营销任务的处理入口。
- 已完成工作空间隔离、参数校验、自动化回归和真实浏览器验收。
- 持久化告警认领、关闭与通知渠道安排在下一阶段。

### Metadata
- Frequency: recurring
- Related Features: marketing task effect, answer quality review, preflight interception

---

## [FEAT-20260904-001] marketing-answer-quality-review

**Logged**: 2026-09-04T13:45:00+08:00
**Priority**: high
**Status**: complete
**Area**: backend, frontend

### Requested Capability
为营销智能体建立回答质检与纠错闭环，识别答非所问、重复回答、内部话术暴露、未确认资费和引用缺失。

### User Context
现有套餐营销对话曾出现数据库升级答案、重复模板和面向坐席的内部措辞，需要在交付前自动发现并可复盘。

### Complexity Estimate
complex

### Suggested Implementation
先以独立质检记录和确定性规则旁路运行，再增加人工复核队列；高风险拦截须在误报率验证后通过工作空间开关灰度启用。

### Progress
- 已完成回答质检记录、确定性规则、新回答自动质检和历史回答按需回填。
- 已在营销任务复盘中展示质检汇总、通过率、问题分布及逐条原因。
- 已完成独立人工复核队列、条件筛选、确认正常/问题、修订答案和不可覆盖的操作历史。
- 已将待处理、已复核、已修订数量同步到任务复盘。
- 已完成工作空间级关闭/影子检测策略、发送前原始/最终答案快照、处理动作和检测耗时记录。
- 已完成营销知识检索依赖失败降级和客户安全兜底，底层异常不再直接形成接口 500 或显示给客户。
- 已完成按质检规则统计命中量、人工样本、问题确认率、误报率和灰度准入阻塞原因，并提供任务/规则/日期筛选。
- 已完成工作空间级高风险灰度拦截：只允许已通过准入门槛的规则启用，并支持按规则白名单配置。
- 已完成发送前缓冲、客户安全替换、模型原始回答与最终回答双留痕、灰度拦截与异常旁路实时统计。
- 已完成 300ms 超时/异常旁路、一键回退影子模式，以及人工复核导致规则失准后的自动降级。
- 当前真实工作空间仍为影子检测且没有准入候选，因此不会自动拦截现有客户回答。

### Metadata
- Frequency: recurring
- Related Features: marketing task effect, campaign recommendation, knowledge citation

---
