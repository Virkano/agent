# OpenAPI、参数编排与版本差异 M05-02 验收文档

> 验收日期：2026-09-21  
> 对应计划：P1-08 / M05-02  
> 需求范围：X10 的 OpenAPI 导入、参数来源/依赖和契约版本差异

## 1. 交付结果

- 支持导入 OpenAPI 3.x JSON 文档，解析指定操作或首个可用操作，自动生成请求方法、接口路径、输入/输出 Schema 和请求参数绑定。
- 支持本地 `#/components/schemas/*` 引用解析；循环引用、缺失引用、不受支持的根类型和无可用操作会被明确拒绝。
- 契约版本新增 OpenAPI 原文快照和参数绑定快照，继续保持历史版本不可覆盖、回滚生成新版本。
- 参数来源支持 `REQUEST`、`CONTEXT`、`CONSTANT`、`PREVIOUS_OUTPUT`；保存时校验目标字段、重复目标、未知依赖、自依赖和依赖环。
- 模拟调用按依赖顺序解析参数后再执行输入 Schema 校验；审计只保存解析后的业务参数和来源类型，不保存 `source_context`。
- 支持任意两个契约版本对比，输出配置变更字段、输入/输出字段增删、必填变化和类型变化，并单独标识路径、方法、新增输入必填、输出删除及类型变化等破坏性变更。
- 页面新增 OpenAPI 导入区、参数来源编辑区、版本差异入口和破坏性变更抽屉。

## 2. 主要接口

| 接口 | 用途 |
| --- | --- |
| `POST /admin/api/workspace/{workspace_id}/api-orchestration/openapi/import` | 解析 OpenAPI 3.x 并返回可编辑契约 |
| `PUT /admin/api/workspace/{workspace_id}/api-orchestration/asset/{asset_id}` | 保存包含 OpenAPI 快照和参数绑定的新版本 |
| `GET .../version/{base_version_id}/compare?target_version_id=...` | 比较两个不可变契约版本 |
| `POST .../mock-invoke` | 按参数来源与依赖解析后执行 Mock 调用 |

## 3. 自动化验证

后端执行：

```bash
./.venv/bin/python -m ruff check apps/tools/api_orchestration.py apps/tools/models/api_orchestration.py apps/tools/views/api_orchestration.py apps/tools/test_api_orchestration.py
./.venv/bin/python apps/manage.py check
./.venv/bin/python apps/manage.py makemigrations --check
./.venv/bin/python apps/manage.py test tools.test_api_orchestration --keepdb --noinput
```

结果：Ruff、Django check、迁移一致性和 6 项专项测试全部通过。覆盖 OpenAPI `$ref` 解析、请求/响应 Schema、参数多来源及依赖、敏感上下文不落审计、依赖环拒绝、破坏性版本差异和原 M05-01 回归。`tools.0010_api_orchestration_contract` 已应用到本地开发库。

前端在 `ui/` 执行：

```bash
pnpm exec eslint src/api/api-orchestration.ts src/views/api-orchestration/index.vue --fix
pnpm run type-check
pnpm run build
```

结果全部通过。构建仅保留仓库既有的第三方注释、`eval` 和大分块警告，无新增错误。

## 4. 真实浏览器验收

- 从 V3 打开“创建新版本”，载入 OpenAPI 3.0.3 样例并解析，路径、输入/输出 Schema 和 2 个请求参数来源均正确回填。
- 保存得到 V4 草稿，OpenAPI 和参数来源标记可见。
- V3 → V4 差异识别 3 项破坏性变化：路径变化、新增必填 `channel`、删除输出字段 `recommendations`。
- 发布 V4 后原 V3 自动归档；V4 Mock 调用成功，审计显示解析后参数与 `parameterSources`，不含鉴权或来源上下文。
- 新增接口的导入、保存、差异、发布、调用及刷新请求均为 200；浏览器控制台 0 error。2 条 warning 为项目既有 Vue 生命周期提示。
- 详情抽屉实测 `scrollHeight 1087 > clientHeight 774`，滚动到底后 `scrollTop 313`。
- 临时登录态权限为 `600`，验收后已按缓存版本精确撤销；状态文件、脚本和隐藏会话产物均已删除。验收业务数据按约定保留。

验收截图：

- [V3 → V4 破坏性版本差异](../../output/playwright/m05-02/m05-02-version-diff.png)
- [OpenAPI V4 已发布](../../output/playwright/m05-02/m05-02-published-version.png)
- [参数解析后的脱敏调用审计](../../output/playwright/m05-02/m05-02-invocation-audit.png)

## 5. 已知边界与下一步

- 当前 OpenAPI 导入以单操作和常用 JSON Schema 基本类型为粗粒度范围，复杂组合类型、远程引用和全量 OpenAPI 编辑器不在本阶段。
- 当前鉴权仍接收内部已验证上下文，未直接处理真实 API Key、JWT、OAuth2 或签名凭证。
- 下一步 M05-03 补齐启用/停用、测试/灰度/生产发布门禁、最小生产鉴权验证、超时/有限重试/熔断及真实晓搭网关适配入口。

## 6. 结论

M05-02 验收通过，已形成“OpenAPI 导入 → 契约回填 → 参数来源与依赖校验 → 不可变版本保存 → 破坏性差异识别 → 发布 → 参数解析调用与脱敏审计”闭环。
