# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20261016-001] correction

**Logged**: 2026-10-16T10:30:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend, frontend, tests

### Summary
模型供应商可见性调整必须同时覆盖后端目录、左侧供应商分组、全部模型列表和“添加模型”供应商弹窗，并在重启 `--noreload` 后端后用真实浏览器验收。

### Details
首次调整只依赖后端供应商目录和侧栏分组，运行中的 `python main.py dev web` 使用 `--noreload`，因此浏览器仍从旧进程取得完整供应商列表；“添加模型”弹窗又直接调用按模型类型查询的供应商接口，缺少前端白名单兜底。仅凭单元测试和构建通过不能证明当前运行页面已经生效。

### Suggested Action
供应商可见性使用前后端同一明确白名单；前端 API 层统一过滤所有供应商目录响应，业务列表继续过滤遗留模型；修改后重启后端，并分别打开侧栏和添加模型弹窗检查实际名称。

### Metadata
- Source: user_feedback
- Related Files: apps/models_provider/constants/model_provider_constants.py, apps/models_provider/views/provide.py, ui/src/api/model/provider.ts, ui/src/utils/model-provider-visibility.ts, ui/src/views/model/index.vue
- Tags: model-provider, visibility, dialog, noreload, browser-acceptance

### Resolution
- **Resolved**: 2026-10-16T10:30:00+08:00
- **Notes**: 增加前端统一白名单过滤，覆盖供应商侧栏、全部模型列表和添加模型弹窗；后端重启后完成真实浏览器验收。

---

## [LRN-20261002-001] correction

**Logged**: 2026-10-02T14:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
同页分组或页签切换必须默认保持当前阅读位置，不能为了展示新内容主动滚动到导航顶部。

### Details
故障场景预演改成两级导航后，切换函数调用 `scrollIntoView({ behavior: 'smooth' })`，导致用户每次点击分组或模块时页面都明显上滚，打断连续浏览。页签切换本身已经提供充分的状态反馈，不应附带页面定位副作用。

### Suggested Action
分组、页签和视图切换只更新当前选中状态；仅当用户明确点击“定位到模块”、校验失败需要暴露目标字段，或新内容完全位于视口外且业务流程明确要求时才滚动。

### Metadata
- Source: user_feedback
- Related Files: ui/src/views/rehearsal/index.vue
- Tags: navigation, scroll-position, tabs, ux

### Resolution
- **Resolved**: 2026-10-02T14:00:00+08:00
- **Notes**: 已移除一级分组和二级模块切换中的 `scrollIntoView()`；切换前记录容器位置并在 DOM 更新后恢复到新内容的可滚动范围，同时让两级导航吸顶。真实坐标点击验证模块切换从 772px 保持到新页面最大 662px，一级分组切换保持在 291px，均未跳回顶部。

---

## [LRN-20261001-001] correction

**Logged**: 2026-10-01T19:30:00+08:00
**Priority**: high
**Status**: promoted
**Area**: backend, frontend, docs

### Summary
本项目新增 V1 业务页面采用“一页一权”，页面 READ 权限同时授予页面内全部操作能力。

### Details
在用户要求继续完善权限时，曾按常见 RBAC 方式开始拆分编辑、执行、删除和导出权限。用户随后明确产品规则：新增页面只要拥有查询/查看权限，就应拥有整个页面的全部权限。细粒度拆分会增加角色配置成本并偏离当前粗粒度 V1 目标。

### Suggested Action
新增 V1 页面只定义工作空间级 `<MODULE>_READ`，并让菜单、路由及页面下全部接口复用该权限；原有智能体、知识库、模型、工具和系统管理继续保留细粒度与资源级授权。只有用户明确提出只读/操作分离时才升级权限模型。

### Metadata
- Source: user_feedback
- Related Files: AGENTS.md, docs/新增功能权限接入与验收规范.md, apps/common/constants/permission_constants.py
- Tags: rbac, workspace, coarse-grained-permission, v1
- Promoted: AGENTS.md

---

## [LRN-20260922-001] best_practice

**Logged**: 2026-09-22T12:00:00+08:00
**Priority**: high
**Status**: promoted
**Area**: tests

### Summary
测试发现阶段不能因导入业务模块而启动后台调度线程。

### Details
推荐引擎单独测试 21 项通过，和模型流水线模块组合时出现跨测试计数串扰。隔离新测试库仍复现，排除了数据库残留。模型流水线测试的导入链触发了 APScheduler 模块顶层 `start()`；在测试事务中运行后台作业会制造隐蔽的并发状态。

### Suggested Action
在 `manage.py test` 进程只实例化调度器，不启动线程；跨模块组合运行并核对稳定性，不通过清空测试库掩盖导入副作用。

### Metadata
- Source: error
- Related Files: apps/common/job/scheduler.py, apps/models_provider/test_pipeline.py, apps/marketing/test_recommendation_engine.py
- Tags: test-isolation, scheduler, background-thread, django
- See Also: ERR-268, ERR-271
- Promoted: AGENTS.md

### Resolution
- **Resolved**: 2026-09-22
- **Notes**: 调度器测试进程不启动；默认 keepdb 模式下第一批 57 项、第二批 56 项跨模块回归通过。

---

## [LRN-20260911-004] correction

**Logged**: 2026-09-11T15:00:00+08:00
**Priority**: high
**Status**: promoted
**Area**: browser-testing

### Summary
功能验收数据应优先通过接口快速构造，真实浏览器聚焦页面报错、关键展示和滚动；验收数据默认可以保留。

### Details
完整依靠浏览器逐字段创建实验、注册版本、评估和发布会产生大量快照与元素引用成本。用户明确指出本地粗粒度 V1 的主要浏览器目标是观察报错，因此后续改为 API 构造状态，浏览器只刷新核对摘要、控制台和滚动。用户同时明确验收数据无需清理，可作为可见样例保留。

### Suggested Action
端到端验收采用“接口准备数据 → 浏览器最小烟测 → 必要时才逐步 UI 交互”；只有专门验证表单交互时才全程走浏览器。

### Metadata
- Source: user_feedback
- Related Files: AGENTS.md, docs/开发与运维排障手册.md
- Tags: browser-qa, api-seeding, token-efficiency, acceptance-data
- Pattern-Key: browser.acceptance.api_seed
- Recurrence-Count: 1

---

## [LRN-20260910-003] correction

**Logged**: 2026-09-10T11:45:00+08:00
**Priority**: critical
**Status**: resolved
**Area**: planning

### Summary
建设方案型项目应先按原始材料建立全量可追踪的粗粒度 V1，再安排单模块深度优化；不能只根据当前最成熟的功能持续追加增强。

### Details
知识库检索评估已经具备完整闭环，但继续建设基线对比和回归门禁会进一步加深局部能力，不能解决建设方案中报告、调度、推荐、模型底座、IVR、晓搭、指标和预演等尚未覆盖的内容。

### Suggested Action
后续每一步必须关联 `X01～X38` 需求编号和对应里程碑；完成当前任务包后优先进入下一未覆盖能力，非阻塞优化统一放入 M12 后的 V2 清单。

### Metadata
- Source: user_feedback
- Related Files: docs/建设方案全量粗粒度V1实施计划.md
- Tags: breadth-first, requirement-traceability, construction-plan, v1

---

## [LRN-20260910-002] correction

**Logged**: 2026-09-10T10:55:00+08:00
**Priority**: high
**Status**: resolved
**Area**: frontend

### Summary
嵌套在 `overflow: hidden` 布局中的长页面必须显式建立自己的滚动容器。

### Details
知识库详情右侧布局会裁剪溢出内容；检索评估页原先只有 `min-height: 100%`，内容超过视口后没有元素承接滚轮事件。将页面设为 `height: 100%`、`min-height: 0`、`overflow-y: auto` 并统一 `box-sizing` 后，浏览器已能滚动到评估问题集底部。

### Suggested Action
新增知识库详情子页面时，交付前用真实浏览器检查首屏和页面底部；如果父级负责裁剪，子页面必须显式声明纵向滚动。

### Metadata
- Source: user_feedback
- Related Files: ui/src/views/knowledge-evaluation/index.vue, ui/src/components/layout-container/index.vue
- Tags: overflow, nested-layout, browser-smoke-test

---

## [LRN-20260910-001] correction

**Logged**: 2026-09-10T10:30:00+08:00
**Priority**: high
**Status**: resolved
**Area**: diagnostics

### Summary
本地前端启动验收不能只检查端口和 curl 200，还必须用真实浏览器确认管理端首屏可见，并给出带 `/admin/` 的完整入口。

### Details
Vite 的 `http://127.0.0.1:3000/` 根路径返回 404，而 `http://127.0.0.1:3000/admin/`、入口脚本和 Vite 客户端均返回 200。用户反馈打不开后，通过真实 Chrome 验证 `/admin/login` 已正常显示账号登录页，并直接保留正确标签页。

### Suggested Action
以后本地前端启动完成后同时执行三层验收：监听端口、管理端 HTTP 资源、真实浏览器首屏。向用户交付时优先提供 `http://localhost:3000/admin/`，不要只提供端口或根地址。

### Metadata
- Source: user_feedback
- Related Files: scripts/start-local.sh, docs/开发与运维排障手册.md
- Tags: vite, localhost, browser-smoke-test, startup

---

## [LRN-20260909-001] best_practice

**Logged**: 2026-09-09T10:47:00+08:00
**Priority**: high
**Status**: resolved
**Area**: diagnostics

### Summary
本地服务的根路径 HTTP 状态不能代替业务端点健康检查；本地向量服务根路径返回 404，但使用知识库绑定的模型 UUID 执行 `embed_query()` 可正常返回 384 维向量。

### Details
端口监听、HTTP 根路径、模型配置和业务推理是四个不同层次。Ollama 应检查 `/api/tags` 及目标模型，本地向量模型应通过应用模型加载逻辑执行真实向量调用。需要鉴权的后端 API 未登录返回 401，也能证明服务、路由和鉴权链路已经生效。

### Suggested Action
本地智能体或检索报错时按“进程/容器 → 端口 → 正确业务端点 → 应用内真实调用”的顺序验证，不再用根路径 404 或未认证 401 推断服务离线。详细步骤见 `docs/开发与运维排障手册.md`。

### Metadata
- Source: development
- Related Files: apps/knowledge/serializers/evaluation.py, docs/开发与运维排障手册.md
- Tags: embedding, ollama, diagnostics, health-check

---

## [LRN-20260909-002] best_practice

**Logged**: 2026-09-09T10:47:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
大型服务补丁后应显式检查关键方法是否重复定义，避免后定义的方法无声覆盖前面的实现。

### Details
检索评估服务组装期间曾在编辑检查中发现 `detail` 和 `export_rows` 的重复草稿，虽然在测试前已移除且未造成运行失败，但 Python 对重复方法不会给出语法错误，单靠测试不一定覆盖所有被覆盖分支。

### Suggested Action
修改大型类后先用 `rg -n "def <method>"` 审核关键入口，再运行 Ruff、迁移检查和专项测试。此规则已同步到 `AGENTS.md`。

### Metadata
- Source: development
- Related Files: apps/knowledge/serializers/evaluation.py, AGENTS.md
- Tags: duplicate-definition, review, backend

---

## [LRN-20260901-001] correction

**Logged**: 2026-09-01T00:00:00+08:00
**Priority**: high
**Status**: pending
**Area**: tests

### Summary
营销智能体测试不能只验证接口 200 和页面可用，还必须验证回答是否符合营销场景语义。

### Details
用户在“套餐升级问题”测试中发现智能体回答了 MySQL/数据库升级内容。根因是测试智能体提示词和无召回兜底提示词过松，短问题未被固定为“中国电信通信套餐升级”语义。

### Suggested Action
后续智能体场景验收必须包含负向语义检查：短问题、歧义问题、无知识库召回时不得跑到非业务领域；交付前要用真实聊天链路检查答案内容。

### Metadata
- Source: user_feedback
- Related Files: apps/application/models/application.py, apps/application/serializers/common.py
- Tags: marketing-agent, qa, prompt-guardrail

---

## [LRN-20260901-002] correction

**Logged**: 2026-09-01T14:55:00+08:00
**Priority**: critical
**Status**: resolved
**Area**: backend

### Summary
客户对话不能用硬编码坐席话术替代智能体、知识库和多轮主链路。

### Details
为压制跑偏回复而加入的费用类直接回答绕过了模型调用，并把内部“建议坐席话术/转人工条件”输出到客户窗口；完整营销上下文还被拼入检索词，影响知识库命中。

### Suggested Action
删除直接回答分支；客户问题只用于知识库检索，营销上下文只作为模型内部提示；将默认提示词明确为客户可见文案，不输出运营内部标签。

### Metadata
- Source: user_feedback
- Related Files: apps/application/chat_pipeline/step/chat_step/impl/base_chat_step.py, apps/application/chat_pipeline/step/search_dataset_step/impl/base_search_dataset_step.py, apps/application/serializers/common.py
- Tags: marketing-agent, rag, multi-turn, audience-separation

### Resolution
- **Resolved**: 2026-09-01T15:09:00+08:00
- **Notes**: 已恢复模型和知识库主链路；营销上下文改为 SystemMessage；已发布版本同步更新；知识库段落和分块已重建索引；费用类回复增加客户合规校验。

---
