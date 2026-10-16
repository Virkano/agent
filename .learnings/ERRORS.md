# Errors

## ERR-063：浏览器控制运行时未启动

- **现象**：首次执行桌面浏览器检查时返回 `runtime_unavailable`，无法枚举应用窗口。
- **根因**：Orca 桌面控制运行时当时未启动，不是 Chrome 或项目页面故障。
- **修复**：执行 `orca open --json` 启动运行时；随后使用当前 Codex 的计算机控制接口绑定已打开的 Chrome 项目页面。
- **验证**：成功读取 `localhost:3000/admin/model`，打开添加模型弹窗，并确认最终仅展示 7 个公有供应商和 Docker AI、Ollama 两个私有供应商。

## ERR-062：新增流水线模型的长补丁在外键定义处被截断

- **现象**：首次新增 `models/pipeline.py` 时，补丁末尾在 `approved_by` 外键处混入无效字符，文件暂时语法不完整。
- **根因**：单次新增文件补丁过长，且提交前未检查末尾完整性。
- **修复**：立即以截断位置为锚点补齐运行审批字段、运行约束和阶段运行模型；后续按模型、服务、视图分别使用小补丁。
- **验证**：文件尾部已补齐，待 Ruff 和 Django check 验证。

## ERR-061：收尾读取命令的路径和工作目录被草稿字符污染

- **Symptom**: A final log-inspection command contained corrupted path and working-directory text, so process creation failed before execution.
- **Cause**: Draft fragments were submitted without a final argument check, repeating the same orchestration pattern.
- **Fix**: Stop issuing nonessential inspection calls; use only verified absolute paths and one operation per call.
- **Verification**: The required code, migration, test, build, browser, plan, and acceptance-document checks had already passed before this nonessential read failed.

## ERR-060：验收文档最后一行混入无效文本

- **现象**：新增 M08-01 验收文档时，下一步说明末尾混入无效字符。
- **根因**：长补丁尾部没有在提交前做完整性复核。
- **修复**：立即将该行替换为完整的 M08-02 任务说明；长文档提交后增加 `tail` 和异常字符检查。
- **验证**：已用 `tail` 检查验收文档末尾，并用异常字符检索确认新增文档和计划没有残留草稿字符。

## ERR-059：M08 进度插入补丁被草稿残片破坏

- **现象**：首次向 M08 验收段落插入当前进度时，工具脚本混入无效文本并报 JavaScript 语法错误；随后一次误触发了当前模式不可用的交互提问工具。
- **根因**：连续工具调用中没有保持单一操作，违反了已提升的最小命令规则。
- **修复**：取消组合内容，将进度压缩为一个完整句子的小补丁；不再发起无关交互。
- **验证**：M08 当前进度与下一步已成功更新。

## ERR-057：实施计划批量补丁的上下文包含重复词

- **现象**：更新 M08 进度时，补丁上下文误写为“完成一次一次实验”，与原文不一致，导致整批补丁未应用。
- **根因**：远距离批量补丁没有逐字复用刚读取的文档原文。
- **修复**：拆分为多个小补丁，分别更新现状、优先级、追踪表、里程碑与下一步。
- **验证**：M08 现状、优先级、X32/X33 状态、当前进度与下一步已分别更新成功。

## ERR-056：写入学习记录时连续提交了不完整补丁片段

- **现象**：向 `.learnings/LEARNINGS.md` 添加用户纠正时，两次补丁分别因缺少合法 hunk 和找不到占位上下文而失败。
- **根因**：没有先基于已读取的稳定锚点完成补丁正文，提交了草稿片段。
- **修复**：以文件固定分隔线 `---` 为上下文，一次性插入完整、符合 self-improvement 格式的学习条目。
- **验证**：`LRN-20260911-004` 已成功写入，并已将规则提升到 `AGENTS.md` 和排障手册。

## ERR-055：读取学习日志时命令字符串混入残片导致引号不闭合

- **现象**：执行 `sed` 读取 `.learnings/LEARNINGS.md` 时，命令中混入多余路径残片，zsh 报 `unmatched '`。
- **根因**：连续编排工具调用时未先清空上一条命令草稿，属于 ERR-043/050 同类重复失误。
- **修复**：后续不再拼接路径命令，改为每次只执行一个带完整绝对路径的简单命令；将“提交前检查工具脚本和 shell 引号”提升到 AGENTS.md。
- **验证**：已通过单一路径命令读取学习日志，并完成学习记录及规则提升。

## ERR-054：清理错误日志时补丁上下文与原文不一致

- **现象**：批量清理 ERR-051/052 和重复 ERR-050 时，补丁中的一行上下文多写了重复词，导致整个补丁校验失败。
- **根因**：一次补丁承担了多个不相关清理目标，扩大了上下文敏感面。
- **修复**：拆成小补丁，先只替换准确复制的 ERR-051/052 区块，再单独处理重复条目。
- **验证**：本区块替换已成功。

## ERR-053：修正错误日志时误写了不存在的目标路径

- **现象**：清理错误日志中的不准确条目时，把文件路径误写成 `.learnings/ERRORSethers.md`，补丁未修改文件。
- **根因**：工具调用提交前没有核对目标路径。
- **修复**：固定使用已确认的 `.learnings/ERRORS.md` 路径，并以当前文件原文作为补丁上下文。
- **验证**：后续补丁已成功应用。

## ERR-052：错误日志补丁调用混入无效 JavaScript 标识符

- **现象**：一次 `apply_patch` 调用误写无效标识符，脚本在解析阶段报 `SyntaxError: Unexpected token ';'`，补丁未执行。
- **根因**：工具调用文本出现非必要编辑残留，未遵守最小三段式调用约束。
- **修复**：使用仅包含 `patch`、`tools.apply_patch(patch)`、`text(result)` 的脚本重试；删除未实际发生的 ERR-051 描述。
- **验证**：本条已准确写入错误日志。

## ERR-050：修正工具脚本后仍残留无效 JavaScript 语句

- **现象**：检索实施计划时，`functions.exec` 在命令调用后残留 `note` 赋值，触发 `ReferenceError: note is not defined`。
- **根因**：未落实上一条“只发送最小合法脚本”的修复措施，且命令中的文档路径也未完整核对。
- **修复**：后续工具脚本严格限制为 `const r = await ...; text(r.output);` 三段式，并使用已确认的完整绝对路径。
- **验证**：已成功读取 M08/X32/X33 计划段落，后续状态更新使用该原文作为依据。

## ERR-049：跨用户续接后沿用旧 Playwright 元素引用失效

- **现象**：用户续接任务后继续点击此前快照中的 `f1e266`，CLI 报元素引用不存在。
- **根因**：Playwright CLI 的页面快照引用可能在任务消息边界、页面更新或会话恢复后失效。
- **修复**：按 Playwright 规范重新生成快照，再使用新引用操作；关键动作前不跨消息边界复用旧引用。
- **验证**：重新快照后完成了版本注册，并通过接口完成评估和发布；浏览器最终刷新无控制台错误。

## ERR-048：Playwright `run-code` 页面沙箱不能读取 Node `process.env`

- **现象**：将临时令牌通过环境变量传给 `run-code` 后，页面函数内访问 `process.env` 报 `ReferenceError: process is not defined`。
- **根因**：该 CLI 的函数代码在浏览器页面执行环境中运行，没有 Node.js 的 `process` 全局对象。
- **修复**：改用 CLI `eval` 将 shell 内存变量写入 localStorage，并将该次命令标准输出丢弃，避免会话令牌进入工具输出或文档；随后单独执行无敏感信息的页面跳转。
- **验证**：临时令牌已在不输出凭证的前提下写入 localStorage，生命周期页面成功加载。

## ERR-047：Playwright CLI `run-code` 多语句未包装为异步函数

- **现象**：给浏览器写入临时令牌并跳转页面的 `run-code` 调用报 `SyntaxError: Unexpected identifier 'page'`。
- **根因**：当前 CLI 版本的 `run-code` 对多条 await 语句需要接收完整的 `async (page) => { ... }` 函数，而非直接拼接语句。
- **修复**：将操作包装为单个异步页面函数后重试，令牌只通过进程环境传递，不输出到日志。
- **验证**：改用完整异步函数完成后续页面跳转，浏览器验收已通过。

## ERR-046：仓库根目录直接运行 Django Python 片段缺少 `apps/` 模块路径

- **现象**：为浏览器验收生成临时本地会话令牌时，直接执行 `.venv/bin/python -c` 报 `ModuleNotFoundError: telecom_ai_agent`。
- **根因**：项目 Django 包位于 `apps/`，直接 Python 进程没有像 `apps/manage.py` 一样把该目录加入模块搜索路径。
- **修复**：沿用项目命令基线，通过 `apps/manage.py shell -c` 执行 Django 代码，不手工猜测设置模块路径。
- **验证**：通过 `apps/manage.py shell -c` 成功建立临时会话，页面及接口验收通过。

## ERR-045：Playwright CLI 的 npx 缓存目录残留导致安装重命名冲突

- **现象**：Playwright 降级验收首次启动时报 `ENOTEMPTY`，npm 无法把缓存中的 `playwright-core` 重命名为临时目录。
- **根因**：`~/.npm/_npx/31e32ef8478fbf80` 内存在上次未清理完整的包安装状态，和本次 npx 包解析冲突。
- **修复**：将该精确缓存目录移动到系统临时目录保留备份，再由 npx 重建干净缓存；不改动项目依赖。
- **验证**：缓存重建后 Playwright CLI 正常启动，页面验收已通过；原缓存备份保留在系统临时目录。

## ERR-044：浏览器状态读取被请求头策略初始化失败阻断

- **现象**：首次调用 CUA `getState()` 进行生命周期页面验收时，应用清单可读取，但浏览器清单返回 `Unable to load browser request-header policy`。
- **根因**：浏览器控制运行时的请求头策略未成功初始化，不是前端页面或本地服务错误。
- **修复**：保留当前 CUA 会话并重试浏览器状态；若仍失败，改用项目 Playwright 浏览器验收流程。
- **验证**：CUA 重试仍失败后成功切换 Playwright；页面加载、接口数据、滚动到底和控制台错误检查均通过。

## ERR-043：工具编排脚本混入无效参数导致补丁未执行

- **现象**：更新 ERR-042 验证结果时，`functions.exec` 的 JavaScript 调用末尾误混入无效文本，触发 `SyntaxError: missing ) after argument list`，文件未变化。
- **根因**：组合工具调用参数时未在提交前复核 JavaScript 语法。
- **修复**：重新发送只包含合法 `apply_patch(patch)` 调用的最小脚本。
- **验证**：ERR-042 验证结果和本条记录均已成功写入。

## ERR-042：`el-table` 插槽行默认推断为 `any`，不能直接索引状态映射

- **现象**：生命周期页面运行 `pnpm run type-check` 时，模板中的 `experimentTagType[row.status]` 和 `versionTagType[row.status]` 报 TS7053。
- **根因**：Element Plus 表格默认插槽的 `row` 在模板中被推断为 `any`，TypeScript 不允许用 `any` 直接索引严格的 `Record<状态联合类型, TagType>`。
- **修复**：通过带显式状态联合类型参数的辅助函数读取标签类型，模板只调用辅助函数，保持映射本身的穷举校验。
- **验证**：目标 ESLint、`pnpm run type-check` 和 `pnpm run build` 均已通过。

## ERR-041：同一补丁不能同时删除并新增同一路径

- **现象**：使用 `apply_patch` 替换 `apps/models_provider/tests.py` 时，在同一个补丁中同时声明 `Delete File` 和 `Add File`，校验阶段报错 `multiple operations target the same file`，补丁未应用。
- **根因**：`apply_patch` 要求单个补丁内每个文件只能作为一个操作目标；替换已有文件应使用 `Update File`，或拆成两个独立补丁。
- **修复**：改用单个 `Update File` 操作替换测试文件内容，并在应用前复核测试代码中的拼写。
- **验证**：测试文件已通过单个 `Update File` 成功替换；目标 Ruff 检查通过，`ModelLifecycleServiceTests` 9 项 Django 测试全部通过。

## [ERR-20260911-040] lifecycle-export-duplicate-and-star-import-lint

**Logged**: 2026-09-11T09:43:00+08:00
**Priority**: low
**Status**: resolved
**Area**: model-lifecycle

### Summary
模型生命周期模块接入包导出时，`models/__init__.py` 中重复加入了 `lifecycle`，且把既有通配导入入口纳入 Ruff 目标后统一触发 `F403`；Django `check` 不受影响。

### Resolution
- **Resolved**: 2026-09-11T09:44:00+08:00
- **Notes**: 删除重复导入，并在沿用项目既有包导出约定的通配导入行上显式标注 `noqa: F403`；大段服务代码后继续用 `rg` 检查关键定义只出现一次。

---

## [ERR-20261001-001] apply_patch

**Logged**: 2026-10-01T19:30:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
一次跨三个后端文件的大型权限替换补丁因其中一个上下文不存在而整体失败。

### Error
```text
apply_patch verification failed: Failed to find expected lines in apps/platform_monitoring/views.py
```

### Context
- 同一补丁同时修改报告、平台监控和 API 编排权限。
- 补丁中包含尚未存在的替换后上下文，导致整个补丁没有应用。

### Suggested Fix
跨文件且重复替换较多时，先按文件读取准确上下文，再按单文件或小批次应用补丁；不要把预期替换后的行当成当前上下文。

### Metadata
- Reproducible: yes
- Related Files: apps/platform_monitoring/views.py, apps/marketing/views/report.py, apps/tools/views/api_orchestration.py

### Resolution
- **Resolved**: 2026-10-01T19:31:00+08:00
- **Notes**: 已确认失败补丁未产生部分修改，并在用户调整权限策略后撤回相关细粒度方案。

---

## [ERR-20261001-002] apply_patch

**Logged**: 2026-10-01T19:45:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
为演练导出接口补日志时，过于宽泛的补丁上下文把“导出演练投诉数据”日志加到了仪表盘查询方法。

### Error
```text
通用的 @has_permissions + def get 上下文首先匹配了 Dashboard.get，而不是 ComplaintExport.get。
```

### Context
- 同一大文件存在大量结构相同的嵌套 APIView。
- 首个补丁块没有包含目标类名作为唯一上下文。

### Suggested Fix
修改同一文件内重复结构的方法时，补丁必须包含目标 `class` 名称；应用后立即用 `rg` 和局部 `sed` 核对装饰器实际位置。

### Metadata
- Reproducible: yes
- Related Files: apps/rehearsal/views.py

### Resolution
- **Resolved**: 2026-10-01T19:46:00+08:00
- **Notes**: 已从 Dashboard.get 移除误加日志，并精确添加到 ComplaintExport.get。

---

## [ERR-20260911-039] error-log-prepend-context-stale

**Logged**: 2026-09-11T09:32:30+08:00
**Priority**: low
**Status**: resolved
**Area**: developer-tooling

### Summary
向错误日志顶部插入新条目时，补丁仍假定上一条是 ERR-036；实际 ERR-037 已先插入，导致上下文校验失败。

### Resolution
- **Resolved**: 2026-09-11T09:33:00+08:00
- **Notes**: 高频追加的日志文件只使用稳定的 `# Errors` 标题作为插入锚点，不依赖当前首条编号。

---

## [ERR-20260911-038] global-bell-blocked-by-open-drawer

**Logged**: 2026-09-11T09:32:00+08:00
**Priority**: low
**Status**: resolved
**Area**: browser-testing

### Summary
报告订阅抽屉开启时直接点击页面右上角全局通知，抽屉遮罩拦截了指针事件，Playwright 点击超时。

### Resolution
- **Resolved**: 2026-09-11T09:32:00+08:00
- **Notes**: 先关闭抽屉或对话框，再操作被遮罩保护的页面级控件；每次跨层级操作前从快照确认当前 overlay 状态。

---

## [ERR-20260911-037] report-subscription-utc-time-displayed-raw

**Logged**: 2026-09-11T09:30:00+08:00
**Priority**: high
**Status**: resolved
**Area**: frontend-timezone

### Summary
报告订阅选择每天 `09:00` 后，卡片把后端 ISO 时间字符串直接截断显示为 `01:00`；后端按 Asia/Shanghai 正确计算并以 UTC 传输，但前端没有转换成本地时间。

### Resolution
- **Resolved**: 2026-09-11T09:31:00+08:00
- **Notes**: `formatDate` 先用 `Date` 解析 ISO 时间，再用浏览器本地年月日时分格式化；非法时间才退回字符串截断。涉及后端带时区时间的页面禁止直接 `slice` ISO 字符串。

---

## [ERR-20260911-036] backend-restarted-on-wrong-port

**Logged**: 2026-09-11T09:28:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: local-services

### Summary
为加载报告文案修复而重启 Django 时误用了 `8000`，但 Vite 开发代理固定指向 `127.0.0.1:8080`，导致前端 `/admin/api/user/profile` 返回代理 500；直连 `8000` 的正确路径仍能返回 401，说明后端本身正常而端口不匹配。

### Resolution
- **Resolved**: 2026-09-11T09:28:00+08:00
- **Notes**: 启停前先核对 `ui/vite.config.ts` 的代理目标，本项目联调后端使用 `8080`；重启后分别检查直连后端和前端代理端点，再继续浏览器验收。

---

## [ERR-20260911-035] report-test-file-name-assumption

**Logged**: 2026-09-11T09:27:00+08:00
**Priority**: low
**Status**: resolved
**Area**: developer-tooling

### Summary
按文件名模式查找报告测试时未命中，`rg` 返回非零状态，使后续通过 `&&` 串联的 Ruff 检查没有执行；实际报告测试位于通用的 `apps/marketing/tests.py`。

### Resolution
- **Resolved**: 2026-09-11T09:27:00+08:00
- **Notes**: 不假设测试文件命名，改为按关键类名检索测试内容；发现型检索与必须执行的检查分开运行。

---

## [ERR-20260911-034] element-plus-radio-native-input-intercepted

**Logged**: 2026-09-11T09:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: browser-testing

### Summary
Playwright 按快照引用点击 Element Plus 单选框的原生 `input` 时，可见的 `span.el-radio-button__inner` 拦截了指针事件；后续表单仍提交，导致报告沿用默认“最终点击”归因。

### Resolution
- **Resolved**: 2026-09-11T09:26:00+08:00
- **Notes**: 对 Element Plus radio/checkbox 优先点击可见标签文本或关联 label，提交前重新获取快照确认选中状态，不直接点击被组件样式隐藏的原生 input。

---

## [ERR-20260911-033] playwright-login-refs-stale

**Logged**: 2026-09-11T09:21:00+08:00
**Priority**: low
**Status**: resolved
**Area**: browser-testing

### Summary
登录失败触发验证码后页面节点重新挂载，沿用上一份快照的输入框引用，连续三个 Playwright 操作均提示引用不存在。

### Resolution
- **Resolved**: 2026-09-11T09:22:00+08:00
- **Notes**: 按 Playwright 技能规范重新获取快照后再操作；涉及验证码等动态区域时，每次刷新或失败响应后都重新取引用。

---

## [ERR-20260910-032] font-metadata-library-unavailable

**Logged**: 2026-09-10T15:19:00+08:00
**Priority**: low
**Status**: resolved
**Area**: document-export

### Summary
尝试用虚拟环境中的 `fontTools` 读取仓库字体内部名称，但该可选依赖未安装。

### Resolution
- **Resolved**: 2026-09-10T15:19:00+08:00
- **Notes**: 不为一次元数据检查新增依赖，改用系统 `strings` 读取字体 name 表，确认字体族为 `Alibaba PuHuiTi 3.0`。

---

## [ERR-20260910-031] report-export-cjk-font-missing

**Logged**: 2026-09-10T15:16:00+08:00
**Priority**: high
**Status**: resolved
**Area**: document-export

### Summary
首次渲染报告 DOCX/PDF 后，中文显示为空白方框；PDF 使用未嵌入的 CID 字体，DOCX 强制使用 Arial，渲染环境无法回退中文字体。随后用于查询字体的 `fc-list` 在当前 macOS 环境不可用。

### Resolution
- **Resolved**: 2026-09-10T15:18:00+08:00
- **Notes**: PDF 改为嵌入仓库已有的阿里巴巴普惠体 TTF；DOCX 为正文、标题和所有表格单元格显式设置已安装的 `Hiragino Sans GB` 东亚字体。重新生成并逐页渲染检查。

---

## [ERR-20260910-030] render-command-destructive-cleanup-rejected

**Logged**: 2026-09-10T15:14:00+08:00
**Priority**: low
**Status**: resolved
**Area**: document-export

### Summary
导出物渲染命令试图先用 `rm -rf` 清理两个输出子目录，被安全策略拒绝，渲染未执行。

### Resolution
- **Resolved**: 2026-09-10T15:15:00+08:00
- **Notes**: 不再清理目录，改用带时间版本号的新输出目录执行渲染；临时验收文件保留在明确的 `output/report-export-qa` 范围内。

---

## [ERR-20260910-029] export-artifact-marker-ordered-late

**Logged**: 2026-09-10T15:13:00+08:00
**Priority**: low
**Status**: resolved
**Area**: document-export

### Summary
报告导出单元测试首次在内存中生成 PDF/DOCX 样本时，文档技能要求的制品操作标记尚未执行；随后首个错误记录补丁又使用了错误上下文而未应用。

### Resolution
- **Resolved**: 2026-09-10T15:14:00+08:00
- **Notes**: 在生成落盘验收样本前分别补执行 PDF 与 DOCX 创建标记；以后文档导出功能先标记，再运行任何会实际调用生成器的测试或命令。

---

## [ERR-20260910-028] subscription-test-uuid-string-mismatch

**Logged**: 2026-09-10T15:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend-tests

### Summary
报告订阅回归测试把数据库 UUID 字段直接与 API 返回的字符串 ID 比较，业务结果正确但断言失败。

### Resolution
- **Resolved**: 2026-09-10T15:11:00+08:00
- **Notes**: 将 ORM UUID 显式转换为字符串后比较，并重跑报告服务测试。

---

## [ERR-20260910-027] malformed-tool-invocations

**Logged**: 2026-09-10T15:12:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
一次静态检查工具调用混入了无效 JavaScript，随后一次补丁调用缺少标准补丁头，命令均未真正执行。

### Resolution
- **Resolved**: 2026-09-10T15:13:00+08:00
- **Notes**: 恢复为单一、最小化工具调用；后续不在检查调用中混入说明性文本，补丁必须以标准头开始。

---

Command failures and integration errors.

---

## [ERR-20260910-026] attribution-chart-css-typos

**Logged**: 2026-09-10T15:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
归因条形图样式补丁中颜色值多了一位，渐变函数也混入重复参数，浏览器会忽略对应声明。

### Resolution
- **Resolved**: 2026-09-10T15:10:00+08:00
- **Notes**: 将颜色恢复为 `#4e5b61`，渐变恢复为 `linear-gradient(90deg, ...)`，并纳入目标 ESLint、构建及浏览器视觉验收。

---

## [ERR-20260910-025] frontend-followup-patches-stale-context

**Logged**: 2026-09-10T15:08:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
通知后续补丁引用的字段已由前一补丁修改，随后样式补丁又把压缩在同一行的规则误写成分行上下文，导致两次匹配失败。

### Resolution
- **Resolved**: 2026-09-10T15:09:00+08:00
- **Notes**: 先读取精确行内容，确认通知改动已生效，再使用稳定的单行锚点分别插入报告图表与订阅列表样式。

---

## [ERR-20260910-024] analysis-report-sfc-import-placement

**Logged**: 2026-09-10T15:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
多段 SFC 补丁把报告订阅相关的 API/type import 追加到了 `</style>` 之后；首次清理补丁又因引用了并不存在的重复字段而无法匹配。

### Resolution
- **Resolved**: 2026-09-10T15:06:00+08:00
- **Notes**: 缩小补丁范围，将符号移入既有 import 块并删除文件尾残留；以后大段 SFC 补丁完成后立即检查 script import 块和文件尾，再执行 ESLint/type-check。

---

## [ERR-20260910-023] report-service-import-placement

**Logged**: 2026-09-10T14:58:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
报告服务补丁把四个模型 import 追加到模块末尾；语法编译能通过，但模块加载时会因使用前未导入而失败。

### Resolution
- **Resolved**: 2026-09-10T14:59:00+08:00
- **Notes**: 将模型名移入 `marketing.models` 导入块并删除末尾残留；大补丁后除 `py_compile` 外还需执行 Django `check` 验证真实模块导入。

---

## [ERR-20260910-022] report-subscription-model-field-typos

**Logged**: 2026-09-10T14:51:30+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
追加报告订阅模型的大段补丁中，`DateTimeField` 和 `models.TextField` 两个类型名被异常文本污染；第一次同时补记错误时又引用了错误的上一条标题上下文，补丁整体未应用。

### Resolution
- **Resolved**: 2026-09-10T14:52:00+08:00
- **Notes**: 按文件固定头部分别定位并更正字段类型，在继续生成迁移前执行 `py_compile`；大段模型修改以后拆成更小补丁并优先运行语法检查。首次错误记录的说明文本也出现异常片段，已在继续前清理。

---

## [ERR-20260910-021] report-model-patch-stray-token

**Logged**: 2026-09-10T14:51:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
新增报告归因方式字段时，补丁中 `db_index=True` 后误带无效标记，形成 Python 语法错误。

### Resolution
- **Resolved**: 2026-09-10T14:51:00+08:00
- **Notes**: 在运行任何管理命令前立即移除多余标记；后续模型补丁先执行语法编译再生成迁移。

---

## [ERR-20260910-020] report-export-dependency-probe

**Logged**: 2026-09-10T14:47:00+08:00
**Priority**: low
**Status**: resolved
**Area**: dependencies, document-export

### Summary
M04-02 导出能力预检时，一条命令让 zsh 展开不存在的 `requirements*.txt`，同时确认项目虚拟环境缺少 PDF 生成依赖 `reportlab`；`python-docx` 已存在。

### Resolution
- **Resolved**: 2026-09-10T14:48:00+08:00
- **Notes**: 改用 `rg --files` 定位项目唯一依赖清单 `pyproject.toml`，按 PDF 生成规范补充并锁定 ReportLab；以后可选依赖文件不交给 shell 通配符展开。

---

## [ERR-20260910-019] report-error-sanitization-test-expectation

**Logged**: 2026-09-10T14:43:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests, security

### Summary
报告生成异常改为安全的通用用户提示后，专项测试仍断言原始模型异常文本，导致 1 项回归失败。

### Resolution
- **Resolved**: 2026-09-10T14:44:00+08:00
- **Notes**: 测试改为断言脱敏后的稳定业务提示；原始 provider 异常不写入报告、运行记录或前端响应，随后重新执行专项回归。

---

## [ERR-20260910-018] playwright-token-output-and-revocation

**Logged**: 2026-09-10T14:36:00+08:00
**Priority**: high
**Status**: resolved
**Area**: security, browser-testing

### Summary
为本地浏览器验收注入临时登录态时，Playwright CLI 将 `localstorage-set` 的调用代码回显，导致一次性会话令牌出现在命令输出；首次按捕获值删除时因 CLI 原始输出不是纯令牌而未命中缓存。

### Resolution
- **Resolved**: 2026-09-10T14:39:00+08:00
- **Notes**: 已关闭验收浏览器，并通过签名签发时间、用户名和 TOKEN 缓存版本精确定位 15 分钟内新建的临时令牌，Redis 删除返回成功。后续浏览器验收禁止把令牌作为 CLI 参数传入，优先使用已授权存储状态或无敏感值回显的隔离脚本。

---

## [ERR-20260910-017] zsh-unmatched-optional-env-glob

**Logged**: 2026-09-10T14:34:00+08:00
**Priority**: low
**Status**: resolved
**Area**: diagnostics

### Summary
查找浏览器验收登录说明时直接向 `rg` 传入 `ui/.env*`，zsh 在无匹配文件时先于命令报 `no matches found`。

### Resolution
- **Resolved**: 2026-09-10T14:35:00+08:00
- **Notes**: 后续可选文件先通过 `rg --files` 解析，或使用 `--glob` 由 `rg` 自行匹配，不再让 shell 展开可能为空的通配符。

---

## [ERR-20260910-016] playwright-npx-cache-enotempty

**Logged**: 2026-09-10T14:33:00+08:00
**Priority**: low
**Status**: resolved
**Area**: browser-testing

### Summary
浏览器连接器不可用后切换到 Playwright CLI，首次通过技能包装脚本启动时，npm 的 `_npx` 缓存目录发生 `ENOTEMPTY` 重命名冲突。

### Resolution
- **Resolved**: 2026-09-10T14:34:00+08:00
- **Notes**: 不删除用户全局 npm 缓存，改用项目 `ui/` 已安装的 Playwright 依赖与现有验收脚本/独立临时缓存完成浏览器验证。2026-09-11 再次通过包装脚本启动时复现相同错误，确认后续直接调用缓存中已安装的 CLI，避免包装脚本重复触发 npx 安装阶段。

---

## [ERR-20260910-015] cua-browser-provider-unavailable

**Logged**: 2026-09-10T14:32:00+08:00
**Priority**: low
**Status**: resolved
**Area**: browser-testing

### Summary
本轮 UI 验收中，桌面浏览器连接器连续两次返回 `Unable to load browser request-header policy`，无法取得现有标签页；前后端端口和构建均正常。

### Resolution
- **Resolved**: 2026-09-10T14:33:00+08:00
- **Notes**: 重置连接会话后故障仍可复现，因此切换到仓库可用的 Playwright 浏览器流程，避免把连接器故障误判为前端页面故障。

---

## [ERR-20260910-014] browser-acceptance-services-stopped

**Logged**: 2026-09-10T14:29:00+08:00
**Priority**: low
**Status**: resolved
**Area**: local-services

### Summary
AI 分析报告页面进入浏览器验收前，探测 `127.0.0.1:3000` 和 `127.0.0.1:8080` 均连接失败；原因是上一轮按用户要求停止了前后端服务，并非本次代码或数据库故障。

### Resolution
- **Resolved**: 2026-09-10T14:30:00+08:00
- **Notes**: 已先确认正式数据库迁移和自动化测试成功，再按项目约定重新启动前后端用于本轮浏览器验收；服务可用性以后在 UI 验收命令前置检查。

---

## [ERR-20260910-013] error-log-tool-call-syntax

**Logged**: 2026-09-10T12:27:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
记录 Django 配置路径错误时，工具包装脚本误写为无效的 `await ++` 表达式，导致错误记录首次写入失败。

### Resolution
- **Resolved**: 2026-09-10T12:28:00+08:00
- **Notes**: 改用标准 `tools.apply_patch(patch)` 调用并一次补记两项错误；失败发生在补丁解析前，业务文件未受影响。

---

## [ERR-20260910-012] settings-apps-path-assumption

**Logged**: 2026-09-10T12:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: diagnostics

### Summary
启动 AI 分析报告中心开发时，首次读取命令按常见 Django 目录猜测了 `apps/telecom_ai_agent/settings/base/apps.py`，但当前项目没有该文件。

### Resolution
- **Resolved**: 2026-09-10T12:26:00+08:00
- **Notes**: 改用 `rg --files` 和 `rg "INSTALLED_APPS"` 定位真实配置文件；其余只读检查正常，未修改业务状态。

---

## [ERR-20260910-011] priority-plan-patch-context-typo

**Logged**: 2026-09-10T12:08:00+08:00
**Priority**: low
**Status**: resolved
**Area**: documentation

### Summary
更新优先级计划时，首次补丁的预期上下文混入了错误文本，随后一次空补丁又使用了错误文件名，均在校验阶段失败。

### Resolution
- **Resolved**: 2026-09-10T12:10:00+08:00
- **Notes**: 重新读取目标段落后拆分为小补丁并按真实上下文更新；失败发生在写入前，没有覆盖计划内容。

---

## [ERR-20260910-010] rg-empty-alternative-matched-all-files

**Logged**: 2026-09-10T12:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: diagnostics

### Summary
首次扫描未实现业务关键词时，正则分支中误写了连续的 `||`，产生空匹配，导致 `rg` 命中几乎所有代码并输出无关内容。

### Resolution
- **Resolved**: 2026-09-10T12:06:00+08:00
- **Notes**: 删除空分支后重新执行关键词扫描，并结合业务目录、迁移、页面和验收文档交叉判断，未使用错误输出形成结论。

---

## [ERR-20260910-009] tool-wrapper-property-typo

**Logged**: 2026-09-10T11:35:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
读取建设方案提取结果时，两次在 JavaScript 工具包装对象中误写等待时间属性，脚本在实际命令执行前失败。

### Resolution
- **Resolved**: 2026-09-10T11:36:00+08:00
- **Notes**: 改回工具定义中的 `yield_time_ms` 后成功执行；未修改任何业务文件。后续复杂工具调用先保持对象字段最小化并对照 schema。

---

## [ERR-20260910-008] evaluation-doc-context-drift

**Logged**: 2026-09-10T10:57:00+08:00
**Priority**: low
**Status**: resolved
**Area**: documentation

### Summary
同步检索评估批量导入说明时，补丁使用的旧句子与验收文档当前内容不一致，首次补丁上下文校验失败；第一次记录错误时也误用了不存在的上下文。

### Resolution
- **Resolved**: 2026-09-10T10:57:00+08:00
- **Notes**: 重新读取当前文档后按实际段落拆分补丁，错误记录改为锚定文件固定头部；未覆盖已有内容。

---

## [ERR-20260910-005] playwright-artifact-workdir-created-too-late

**Logged**: 2026-09-10T10:36:00+08:00
**Priority**: low
**Status**: resolved
**Area**: diagnostics

### Summary
首次运行 Playwright 验收时，把尚未创建的产物目录直接作为进程工作目录；进程在执行目录创建命令前就因工作目录不存在而失败。

### Resolution
- **Resolved**: 2026-09-10T10:36:00+08:00
- **Notes**: 先从仓库根目录创建 `output/playwright/localhost-debug/`，再从该目录运行浏览器命令。

---

## [ERR-20260910-004] vite-force-argument-separator

**Logged**: 2026-09-10T10:35:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
首次重启前端时使用 `pnpm run dev -- --force`，实际展开为 `vite -- --force`，没有触发 Vite 强制依赖优化。

### Resolution
- **Resolved**: 2026-09-10T10:35:00+08:00
- **Notes**: 改用 `pnpm exec vite --force`，启动日志确认 `Forced re-optimization of dependencies`。

---

## [ERR-20260910-006] result-module-path-assumption

**Logged**: 2026-09-10T10:42:00+08:00
**Priority**: low
**Status**: resolved
**Area**: diagnostics

### Summary
检查知识库评估导入接口的公共响应封装时，误把 `common.result` 推断为 `apps/common/result.py`，辅助读取命令返回文件不存在。

### Resolution
- **Resolved**: 2026-09-10T11:00:00+08:00
- **Notes**: 该读取与实现无依赖，未修改业务状态；后续先用 `rg --files apps/common` 解析模块真实路径，不根据 Python 导入名猜测文件路径。

---

## [ERR-20260910-007] evaluation-import-prettier

**Logged**: 2026-09-10T10:45:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
检索评估批量导入按钮区首次执行 Prettier 检查未通过。

### Resolution
- **Resolved**: 2026-09-10T10:45:00+08:00
- **Notes**: 使用仓库现有 Prettier 对目标 Vue 文件进行机械格式化，并重新执行格式、ESLint、类型和构建检查。

---

## [ERR-20260910-003] stale-in-app-browser-tab-id

**Logged**: 2026-09-10T10:34:00+08:00
**Priority**: low
**Status**: resolved
**Area**: diagnostics

### Summary
前端修复后尝试复用应用内浏览器旧标签 ID，标签已失效，自动导航返回 `Tab not found`。

### Error
```text
Tab not found: 2 in browser 1
```

### Resolution
- **Resolved**: 2026-09-10T10:34:00+08:00
- **Notes**: 服务端 IPv4/IPv6 HTTP 验证不受影响；后续浏览器验收先重新读取当前浏览器与标签清单，不复用过期 ID。

---

## [ERR-20260910-002] zsh-unmatched-env-glob

**Logged**: 2026-09-10T10:32:00+08:00
**Priority**: low
**Status**: resolved
**Area**: diagnostics

### Summary
读取 Vite 配置后的辅助环境文件检查直接使用 `ui/.env*`，zsh 在没有匹配文件时触发 `no matches found`。

### Error
```text
zsh: no matches found: ui/.env*
```

### Context
- Vite skill 和 `ui/vite.config.ts` 已在报错前成功读取。
- 失败只影响非必要的环境文件枚举，没有修改文件或服务状态。

### Suggested Fix
文件发现统一使用 `rg --files` 或 `find` 后再读取，不把可能为空的 glob 直接交给 zsh 展开。

### Metadata
- Reproducible: yes
- Related Files: ui/vite.config.ts

### Resolution
- **Resolved**: 2026-09-10T10:32:00+08:00
- **Notes**: 后续不再使用未加保护的空匹配通配符。

---

## [ERR-20260910-001] local-model-migration-baseline-missing

**Logged**: 2026-09-10T10:27:00+08:00
**Priority**: medium
**Status**: pending
**Area**: infra

### Summary
本地向量服务可以正常启动，但启动迁移检查提示 `local_model` 没有模型迁移基线；Web/Celery 的全量迁移还曾提示 `system_manage` 漂移。

### Error
```text
Your models in app(s): 'local_model' have changes that are not yet reflected in a migration.
makemigrations local_model --check --dry-run: would create local_model/0001_initial.py
```

### Context
- `apps/local_model/migrations/` 当前只有 `__init__.py`。
- `local_model` 使用独立 `SERVER_NAME=local_model` 设置，迁移预览会创建 `SystemSetting`、`User`、`Model` 三个模型。
- 定向执行 `makemigrations system_manage --check --dry-run` 返回无变化，说明 Web 启动时的 `system_manage` 提示需单独复核，不能直接生成迁移。
- 当前 PostgreSQL 已有共享表，本地向量服务仍可运行；本次未生成或应用迁移，避免误改现有共享表历史。

### Suggested Fix
在独立任务中审计 local-model 与 Web 共用表的迁移策略：确认应采用初始状态迁移、迁移模块映射还是显式不管理；先在全新测试库验证，再加入仓库。同步定位全量 `migrate` 中 `system_manage` 的条件加载差异。

### Metadata
- Reproducible: yes
- Related Files: apps/local_model/migrations, apps/telecom_ai_agent/settings/base/model.py, apps/system_manage/migrations

---

## [ERR-20260909-001] chained-check-did-not-stop

**Logged**: 2026-09-09T10:17:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
检索评估模块首次 Ruff 检查发现两个无用导入，但同一脚本没有启用失败即停，后续迁移生成仍继续执行，降低了前置门禁的可信度。

### Error
```text
F401 django.db.models.Q imported but unused
F401 django.db.models.QuerySet imported but unused
```

### Context
- 操作：新模块静态检查后生成 Django 迁移。
- 根因：两个导入在实现调整后不再使用；多行 shell 脚本未设置 `set -e`。

### Suggested Fix
删除无用导入；有前后置依赖的验收命令统一在脚本首行使用 `set -e`，只有互不依赖的检查才并行执行。

### Metadata
- Reproducible: yes
- Related Files: apps/knowledge/serializers/evaluation.py

### Resolution
- **Resolved**: 2026-09-09T10:18:00+08:00
- **Notes**: 已删除无用导入；后续迁移、测试与构建脚本启用失败即停。

---

## [ERR-20260908-010] embedding-healthcheck-model-id

**Logged**: 2026-09-08T15:46:00+08:00
**Priority**: low
**Status**: resolved
**Area**: diagnostics

### Summary
本地向量服务健康检查首次把模型名称放在要求 UUID 的 URL 参数中，HTTP 返回 200，但业务响应为模型 ID 校验失败。

### Resolution
- **Resolved**: 2026-09-08T15:47:00+08:00
- **Notes**: 从本地模型表读取默认向量模型 UUID 后重新请求，服务返回业务码 200 和完整向量。

---

## [ERR-20260908-009] final-alert-ui-patch-context

**Logged**: 2026-09-08T15:39:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
告警最终收口的前端逻辑补丁把两段相邻 `sed` 输出的重叠行误判为源码重复，补丁上下文校验失败且未写入文件。

### Resolution
- **Resolved**: 2026-09-08T15:40:00+08:00
- **Notes**: 重新按文件真实上下文拆分补丁，先修改模板再修改加载和交互逻辑；后续 ESLint、类型检查及生产构建均通过。

---

## [ERR-20260908-008] alert-noise-score-boundary

**Logged**: 2026-09-08T14:42:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
告警降噪专项测试中，4 次刷新加 1 次重开得到 6 分，但初始高噪声阈值设为 7，导致明显反复的告警仍被归为中等级别。

### Resolution
- **Resolved**: 2026-09-08T14:42:00+08:00
- **Notes**: 将综合噪声分达到 5 分判定为高噪声；单项阈值（刷新 5 次或重开 2 次）保持不变。

---

## [ERR-20260908-007] diagnostic-tool-call-typos

**Logged**: 2026-09-08T14:15:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
Ollama 并行诊断的首次编排存在 JavaScript 语法错误，重试时又误写了一个工作目录，命令均未实际进入项目诊断阶段。

### Resolution
- **Resolved**: 2026-09-08T14:15:00+08:00
- **Notes**: 简化工具调用并统一复用已确认的项目绝对路径后重新执行；配置检索也改为先定位实际文件，避免把不存在的根目录 `config.yml` 当作固定入口。

---

## [ERR-20260908-006] migration-check-missing-env

**Logged**: 2026-09-08T14:09:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
执行 Django 迁移一致性检查时未加载 `.env.local`，项目找不到运行配置文件并提前退出。

### Resolution
- **Resolved**: 2026-09-08T14:09:00+08:00
- **Notes**: 后续 Django 管理命令统一先加载项目环境变量；业务代码和迁移内容无需修改。

---

## [ERR-20260908-005] oversized-ui-patch-context

**Logged**: 2026-09-08T14:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
一次性向营销运营页加入类型、状态和处理逻辑时，补丁包含尚未存在的上下文行，导致整块补丁校验失败。

### Resolution
- **Resolved**: 2026-09-08T14:06:00+08:00
- **Notes**: 改为按导入、状态、加载函数和处理函数分块应用；模板与脚本分别校验。

---

## [ERR-20260908-004] invalid-character-in-test-fixture

**Logged**: 2026-09-08T14:02:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
新增告警复盘测试骨架时，测试参数中误带无效字符，形成无法解析的 Python 代码。

### Resolution
- **Resolved**: 2026-09-08T14:03:00+08:00
- **Notes**: 在运行测试前通过局部检查发现并替换为完整测试用例；后续先完成整段补丁再执行语法与 Ruff 检查。

---

## [ERR-20260908-003] eslint-wrong-workdir

**Logged**: 2026-09-08T13:31:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
收尾静态检查从仓库根目录执行 `npm exec eslint`，未找到 `ui/` 下的本地依赖并尝试访问镜像源，最终因受限网络失败。

### Resolution
- **Resolved**: 2026-09-08T13:32:00+08:00
- **Notes**: 前端命令固定在 `ui/` 工作目录执行；本轮 ESLint 已在正确目录通过，不需要下载依赖。

---

## [ERR-20260908-002] sandbox-local-port-visibility

**Logged**: 2026-09-08T13:26:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
沙箱内 `curl 127.0.0.1:8080` 无法看到宿主已有监听进程，误判后端未启动；再次启动 `runserver` 才报告端口已占用。

### Resolution
- **Resolved**: 2026-09-08T13:27:00+08:00
- **Notes**: 本地服务状态改用获批的宿主侧 `lsof` 只读确认；不再把沙箱内 localhost 连接失败直接等同于服务未运行。

---

## [ERR-20260908-001] element-plus-upload-error-type

**Logged**: 2026-09-08T13:24:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
告警附件上传失败回调向 Element Plus `onError` 传入普通 `Error`，与其要求的 `UploadAjaxError` 类型不兼容，导致 `vue-tsc` 失败。

### Resolution
- **Resolved**: 2026-09-08T13:25:00+08:00
- **Notes**: 自定义上传函数不再伪造组件内部错误类型；保留 Promise 拒绝，让上传组件按自定义请求约定处理失败。

---

## [ERR-20260908-001] django-command-used-system-python

**Logged**: 2026-09-08T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
生成营销迁移时先误用系统 Python，切换 `.venv` 后又因未加载根目录 `.env.local` 而找不到运行配置。

### Resolution
- **Resolved**: 2026-09-08T00:00:00+08:00
- **Notes**: 已确认 Django 命令需从仓库根目录加载 `.env.local`，并统一使用 `.venv/bin/python apps/manage.py`。

### Metadata
- Reproducible: yes
- Related Files: apps/manage.py, .venv/pyvenv.cfg
- See Also: ERR-20260907-014, ERR-20260907-013A, ERR-20260907-010

---

## [ERR-20260908-002] postgres-lock-nullable-join

**Logged**: 2026-09-08T10:15:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
告警协作事务在 `select_for_update()` 后联表读取可空负责人，PostgreSQL 拒绝对外连接可空侧加锁。

### Error
`FOR UPDATE cannot be applied to the nullable side of an outer join`

### Resolution
- **Resolved**: 2026-09-08T10:16:00+08:00
- **Notes**: 协作事务只锁 `marketing_alert` 主表，需要的规则和负责人按外键延迟读取。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/serializers/alerts.py

---

## [ERR-20260908-003] zsh-empty-glob-config-search

**Logged**: 2026-09-08T10:24:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
检索前端端口配置时使用了可能为空的 `ui/.env*`，被 zsh `nomatch` 提前终止。

### Resolution
- **Resolved**: 2026-09-08T10:24:00+08:00
- **Notes**: 改用 `rg --files` 和明确存在的配置文件，不再向 shell 传递未解析通配符。

### Metadata
- Reproducible: yes
- Related Files: ui/vite.config.ts

---

## [ERR-20260907-034] cua-localstorage-unavailable

**Logged**: 2026-09-07T18:13:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
真实浏览器验收时尝试通过页面执行上下文读取 `window.localStorage` 以直接调试鉴权接口，持久化浏览器通道未暴露该能力。

### Resolution
- **Resolved**: 2026-09-07T18:18:00+08:00
- **Notes**: 改用 Django 服务层诊断确认规则、成员、同步和分页查询，再通过已登录真实页面点击刷新、查询、规则保存、告警抽屉和通知直达，完成同等层级验收。

---

## [ERR-20260907-018] sla-select-for-update-nullable-rule

**Logged**: 2026-09-07T18:05:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
SLA 扫描在 `select_for_update()` 查询中同时 `select_related()` 可为空的告警规则，PostgreSQL 拒绝锁定外连接的可空侧。

### Error
```
FOR UPDATE cannot be applied to the nullable side of an outer join
```

### Resolution
- **Resolved**: 2026-09-07T18:06:00+08:00
- **Notes**: 改为先只锁定告警行，再批量加载规则映射，既保留并发保护也避免可空外连接锁。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/serializers/alerts.py
- See Also: ERR-20260904-016 quality-review-select-for-update-outer-join
- Recurrence-Count: 2

---

## [ERR-20260907-017] celery-cli-path-dependency

**Logged**: 2026-09-07T16:22:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
通过项目入口启动本地任务服务时，Django 管理命令硬编码执行 PATH 中的 `celery`，未激活虚拟环境时即使当前 Python 已安装 Celery 也会启动失败。

### Error
```
FileNotFoundError: [Errno 2] No such file or directory: 'celery'
```

### Resolution
- **Resolved**: 2026-09-07T16:23:00+08:00
- **Notes**: 管理命令改为使用 `sys.executable -m celery`，确保任务 worker 与启动 Django 命令使用同一个 Python 环境。

---

## [ERR-20260907-016] cua-playwright-reload-method

**Logged**: 2026-09-07T16:19:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
真实浏览器复测时尝试调用持久化页面代理未暴露的 `tab.playwright.reload()`。

### Resolution
- **Resolved**: 2026-09-07T16:20:00+08:00
- **Notes**: 改用页面原生 `CMD+R` 刷新，并通过 `playwright.domSnapshot()` 和 `tab.dev.logs()` 完成页面及零错误验收。

---

## [ERR-20260907-015] apply-patch-duplicate-file-section

**Logged**: 2026-09-07T16:16:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
一次补丁中为同一文件声明了两个独立 `Update File` 区块，补丁校验拒绝执行。

### Resolution
- **Resolved**: 2026-09-07T16:17:00+08:00
- **Notes**: 已合并为单个文件更新区块和多个上下文片段；失败补丁未写入任何内容。

---

## [ERR-20260907-014] django-project-venv

**Logged**: 2026-09-07T16:14:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
纠正 Django 入口后仍使用系统 Python，未加载项目 `.venv`，导致无法导入 Django。

### Resolution
- **Resolved**: 2026-09-07T16:15:00+08:00
- **Notes**: 已改用 `.venv/bin/python apps/manage.py`，迁移、测试和系统检查均正常通过。

---

## [ERR-20260907-013] django-entry-path-assumption

**Logged**: 2026-09-07T16:12:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
阶段验收时从仓库根目录直接执行 `python manage.py`，但本项目 Django 入口实际位于 `apps/manage.py`。

### Error
```
python: can't open file '/Users/zhaozhenchao/course/AI/Agent/manage.py'
```

### Resolution
- **Resolved**: 2026-09-07T16:13:00+08:00
- **Notes**: 已先用 `rg --files -g 'manage.py'` 确认入口，后续统一使用 `python apps/manage.py`；错误命令未修改应用或数据。

---

## [ERR-20260907-012] scheduler-entry-ruff-imports

**Logged**: 2026-09-07T16:02:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
新增营销告警调度注册后，Ruff 同时发现通知服务的未使用导入，以及既有调度入口使用通配符导入导致的未定义名称检查错误。

### Error
```
F401 unused import; F403 star import; F405 name may be undefined
```

### Context
- 检查范围包含新增通知服务和为本阶段修改的公共调度入口。
- 调度入口原有运行行为正常，但通配符导入不利于静态检查和新增任务维护。

### Suggested Fix
删除未使用导入，并把调度入口改为显式模块导入。

### Metadata
- Reproducible: yes
- Related Files: apps/common/job/__init__.py, apps/marketing/serializers/notifications.py

### Resolution
- **Resolved**: 2026-09-07T16:03:00+08:00
- **Notes**: 已改为显式导入三个既有任务模块及营销任务模块，运行顺序保持不变。

---

## [ERR-20260907-011] cua-tab-snapshot-method

**Logged**: 2026-09-07T15:11:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
真实浏览器刷新后误调用不存在的 `tab.snapshot()` 方法。

### Error
```
tab.snapshot is not a function
```

### Context
- 页面 `reload` 已成功执行，失败仅发生在后续读取页面状态。
- 持久化 CUA 通道需要使用其 Playwright DOM 接口读取状态。

### Suggested Fix
使用 `tab.playwright.domSnapshot()`，不要混用其他浏览器自动化工具的方法名。

### Metadata
- Reproducible: yes
- Related Files: ui/src/views/marketing-operations/index.vue

### Resolution
- **Resolved**: 2026-09-07T15:12:00+08:00
- **Notes**: 已切换为该通道支持的 Playwright DOM 快照接口。

---

## [ERR-20260907-010] result-module-path-assumption

**Logged**: 2026-09-07T15:08:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
检查分页返回结构时把 `common.result` 错当成单文件，读取了不存在的 `apps/common/result.py`。

### Error
```
cat: apps/common/result.py: No such file or directory
```

### Context
- 只读检查命令路径写错，未修改业务数据。
- 实际实现是 `apps/common/result/` 包。

### Suggested Fix
先用 `rg --files` 或 `find` 确认模块对应的文件路径，再读取实现。

### Metadata
- Reproducible: yes
- Related Files: apps/common/result/
- Recurrence-Count: 2
- See Also: UI 营销 API 文件同样不能按页面名推测，应先使用 `rg --files`。

### Resolution
- **Resolved**: 2026-09-07T15:09:00+08:00
- **Notes**: 已通过文件清单确认真实模块路径，后续按包目录读取。

---

## [ERR-20260907-031] cua-networkidle-unsupported

**Logged**: 2026-09-07T14:52:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
持久化浏览器通道不支持 `networkidle` 页面等待条件，导航后的等待调用失败。

### Resolution
- **Resolved**: 2026-09-07T14:52:00+08:00
- **Notes**: 改用 `domcontentloaded`、短暂渲染等待和页面关键元素作为就绪判断，监控页面随后正常完成验收。

---

## [ERR-20260907-030] playwright-cli-npx-cache-conflict

**Logged**: 2026-09-07T14:51:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Playwright CLI 包装脚本在 npm `_npx` 缓存目录更新包时触发 `ENOTEMPTY`，无法启动浏览器命令。

### Resolution
- **Resolved**: 2026-09-07T14:51:00+08:00
- **Notes**: 本次 SLA 验收再次复现（Recurrence-Count: 4），冲突位置变为 `playwright-core`；未删除用户全局 npm 缓存，继续改用当前可用的持久化浏览器自动化通道完成页面验收。

---

## [ERR-20260907-029] zsh-unquoted-query-url

**Logged**: 2026-09-07T14:50:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
使用 zsh 调用带查询参数的运营监控接口时没有引用 URL，`?` 被当作文件名通配符，HTTP 请求没有发出。

### Resolution
- **Resolved**: 2026-09-07T14:50:00+08:00
- **Notes**: 对完整 URL 使用单引号后重新执行接口验收。

---

## [ERR-20260907-028] operations-table-slot-type

**Logged**: 2026-09-07T14:42:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
运营监控表格直接使用插槽中的 `any` 状态值索引严格类型映射，导致 Vue TypeScript 检查失败。

### Resolution
- **Resolved**: 2026-09-07T14:43:00+08:00
- **Notes**: 增加带状态联合类型和默认值的转换函数，模板不再直接使用未收窄值索引对象。

---

## [ERR-20260907-027] marketing-tests-import-patch-context

**Logged**: 2026-09-07T14:35:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
向营销测试文件补充导入时使用了不匹配的上下文顺序，`apply_patch` 校验失败，补丁未写入。

### Resolution
- **Resolved**: 2026-09-07T14:36:00+08:00
- **Notes**: 先读取文件实际导入顺序，再使用精确上下文完成补丁；新增运营监控测试随后通过。

---

## [ERR-20260907-026] tool-wrapper-javascript-syntax

**Logged**: 2026-09-07T14:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
读取下一阶段计划时，两次工具包装脚本出现 JavaScript 字符串和变量声明语法错误，实际检索命令没有执行。

### Resolution
- **Resolved**: 2026-09-07T14:25:00+08:00
- **Notes**: 改用单行、完整初始化的 `const` 工具调用后检索成功；没有修改业务数据。

---

## [ERR-20260907-025] django-shell-apps-prefix

**Logged**: 2026-09-07T14:22:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
在 Django shell 中误用 `apps.xpack_lite`、`apps.marketing` 和 `apps.users` 导入路径，模型没有归属到已安装应用。

### Resolution
- **Resolved**: 2026-09-07T14:22:00+08:00
- **Notes**: Django 运行时统一使用 `xpack_lite`、`marketing`、`users` 等应用包名；只读核对随后成功，未修改数据。

---

## [ERR-20260907-024] django-check-system-python

**Logged**: 2026-09-07T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
最终检查先直接调用了系统 `python`，随后虽切换到虚拟环境但没有导出 `.env.local` 中的变量，导致 Django 依赖或配置文件定位失败。

### Resolution
- **Resolved**: 2026-09-07T00:00:00+08:00
- **Notes**: 改为从仓库根目录以 `set -a` 加载 `.env.local`，再使用 `.venv/bin/python` 执行 Django 管理命令；运行中的前后端服务未受影响。

---

## [ERR-20260907-022] django-command-env-path

**Logged**: 2026-09-07T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
在 `apps` 工作目录执行 Django 命令时错误地从当前目录加载 `.env.local`，导致配置文件路径没有注入。

### Error
```
zsh:source: no such file or directory: .env.local
ImportError: Error: No config file found.
```

### Context
- `.env.local` 位于仓库根目录，不在 `apps` 子目录。
- 未产生数据库或业务数据变更。

### Suggested Fix
从 `apps` 目录执行时使用 `source ../.env.local`，或在仓库根目录加载环境后再进入 `apps`。

### Metadata
- Reproducible: yes
- Related Files: .env.local, apps/manage.py

### Resolution
- **Resolved**: 2026-09-07T00:00:00+08:00
- **Notes**: 后续 Django 命令统一从仓库根目录加载 `.env.local`。

---

## [ERR-20260907-023] qa-cleanup-folder-import

**Logged**: 2026-09-07T14:15:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
隔离浏览器验收数据清理首次使用了不存在的文件夹模型模块路径。

### Error
```
ModuleNotFoundError: No module named 'application.models.application_folder'
```

### Context
- 错误发生在事务和删除语句开始前，没有删除任何数据。
- `ApplicationFolder`、`KnowledgeFolder`、`ToolFolder` 均由各应用的 `models` 包导出。

### Suggested Fix
从 `application.models`、`knowledge.models` 和 `tools.models` 导入对应模型。

### Metadata
- Reproducible: yes
- Related Files: apps/application/models/application.py, apps/knowledge/models/knowledge.py, apps/tools/models/tool.py

### Resolution
- **Resolved**: 2026-09-07T14:16:00+08:00
- **Notes**: 使用应用级模型导出后清理成功，并确认临时工作空间、用户和质检记录均不存在。

---

## [ERR-20260907-020] quality-rule-effect-old-backend-route

**Logged**: 2026-09-07T13:48:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
新质检规则效果页面首次浏览器验收时被跳转到 404，原因是运行中的旧后端进程尚未加载新增 URL 路由。

### Error
`GET /admin/api/workspace/{workspace_id}/marketing/quality-rule-effect -> 404`

### Context
- Vue 页面路由本身存在且菜单可见。
- 全局 Axios 错误处理在接口 404 后将页面导航到 `/admin/404`，容易误判为前端路由缺失。

### Suggested Fix
新增后端 URL 配置后先重启本地 Web 服务，并在浏览器验收前用匿名请求确认接口从 404 变为预期的 401。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/urls.py, ui/src/views/marketing-quality/index.vue

### Resolution
- **Resolved**: 2026-09-07T13:49:00+08:00
- **Notes**: 重启后端后匿名接口返回 401；登录态页面及筛选请求均正常，无新增 404/500。

---

## [ERR-20260907-021] cua-element-plus-option-hidden-match

**Logged**: 2026-09-07T13:50:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
浏览器自动化按下拉项文本选择 Element Plus 选项时只匹配到隐藏副本，触发可见元素等待超时。

### Error
`Playwright selector deadline exceeded: no_visible_match`

### Context
- 下拉框已展开，辅助功能树提供了可见选项的动态 DOM id。

### Suggested Fix
对 Element Plus 浮层选项优先使用当前辅助功能树中的动态 id 定位，而不是对重复文本使用 `last()`。

### Metadata
- Reproducible: yes
- Related Files: ui/src/views/marketing-quality/component/RuleEffectPanel.vue

### Resolution
- **Resolved**: 2026-09-07T13:51:00+08:00
- **Notes**: 改用可见选项 id 后成功筛选“内部话术暴露”，并完成重置验证。

---

## [ERR-20260907-001] django-command-workdir-mismatch

**Logged**: 2026-09-07T12:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
在仓库根目录执行 Django 验收准备命令时，沿用了 `apps` 工作目录下的虚拟环境相对路径，导致 Python 可执行文件不存在。

### Error
```
zsh: no such file or directory: ../.venv/bin/python
```

### Context
- 仓库根目录是 `/Users/zhaozhenchao/course/AI/Agent`
- `manage.py` 位于 `apps/manage.py`，虚拟环境位于根目录 `.venv`
- Django 管理命令还必须从仓库根目录自动导出 `.env.local` 后再进入 `apps` 目录执行。

### Suggested Fix
从仓库根目录加载并导出 `.env.local`，随后进入 `apps` 目录，统一使用 `../.venv/bin/python manage.py ...`。

### Metadata
- Reproducible: yes
- Related Files: apps/manage.py, .venv/pyvenv.cfg, .env.local
- See Also: ERR-20260907-010

### Resolution
- **Resolved**: 2026-09-07T12:01:00+08:00
- **Notes**: 已使用项目启动脚本一致的环境加载方式和正确工作目录完成命令。

---

## [ERR-20260907-018] verification-path-relative-to-apps

**Logged**: 2026-09-07T13:23:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
迁移状态检查从 `apps` 目录执行后，后续文档行号命令仍使用仓库根目录相对路径，导致三个 `nl` 读取失败；迁移检查本身已成功。

### Resolution
- **Resolved**: 2026-09-07T13:24:00+08:00
- **Notes**: 切回仓库根目录重新读取文档和代码行号。

### Metadata
- Reproducible: yes
- Related Files: docs/测试/第二十八阶段-发送前影子质检与依赖降级验收文档.md

---

## [ERR-20260907-017] frontend-repository-lint-baseline

**Logged**: 2026-09-07T13:21:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
全仓 `pnpm lint` 被 72 个既有 ESLint 错误阻断，错误集中在动态表单、工作流、Markdown 和其他旧组件，不涉及本阶段营销 API 与质检页面。

### Resolution
- **Resolved**: 2026-09-07T13:22:00+08:00
- **Notes**: 已回退全仓 `--fix` 对无关文件造成的机械改动，并对本阶段两个前端文件单独执行 ESLint，结果通过；全仓历史基线留待独立治理。

### Metadata
- Reproducible: yes
- Related Files: ui/src/views/marketing-quality/index.vue, ui/src/api/marketing/task.ts

---

## [ERR-20260907-016] django-test-discovery-label

**Logged**: 2026-09-07T13:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
`manage.py test marketing` 在当前包布局下额外发现 `apps.marketing.models`，并且遗留测试数据库触发无交互确认，导致业务测试之外的发现错误。

### Resolution
- **Resolved**: 2026-09-07T13:22:00+08:00
- **Notes**: 使用明确测试标签 `marketing.tests --keepdb`，31 项真实营销测试全部通过。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/tests.py

---

## [ERR-20260907-015] quality-policy-cleanup-missing-row

**Logged**: 2026-09-07T13:18:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
验收清理脚本假定目标工作空间一定存在显式质量策略记录，实际该工作空间使用的是“无记录时默认影子检测”的配置。

### Resolution
- **Resolved**: 2026-09-07T13:19:00+08:00
- **Notes**: 清理结果已提交，后续校验改为允许策略表无行并按服务默认值判断，不再用 `.get()` 假定记录存在。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/preflight.py, apps/marketing/serializers/quality_policy.py

---

## [ERR-20260907-014] cua-unsupported-helper-methods

**Logged**: 2026-09-07T13:16:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
浏览器验收误用了页面代理不存在的 `domcontentloaded()` 和 `click()` 快捷方法。

### Resolution
- **Resolved**: 2026-09-07T13:16:00+08:00
- **Notes**: 导航后使用短轮询读取新快照，并通过 `getByRole(...).click()` 完成可访问性定位和展开验证；业务状态未受影响。

### Metadata
- Reproducible: yes
- Related Files: docs/测试/第二十八阶段-发送前影子质检与依赖降级验收文档.md

---

## [ERR-20260907-013A] django-command-missing-venv

**Logged**: 2026-09-07T13:17:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
验收查询已加载 `.env.local`，但第一次仍调用系统 Python，因未进入项目虚拟环境而找不到 Django。

### Resolution
- **Resolved**: 2026-09-07T13:17:00+08:00
- **Notes**: 改用仓库内 `.venv/bin/python` 执行管理命令。

### Metadata
- Reproducible: yes
- Related Files: .venv, apps/manage.py

---

## [ERR-20260907-013] runtime-fallback-test-context

**Logged**: 2026-09-07T13:13:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
运行时兜底测试期望命中客户资费专用文案，但测试来源缺少营销客户标识。

### Resolution
- **Resolved**: 2026-09-07T13:13:00+08:00
- **Notes**: 补齐与真实营销客户对话一致的任务和客户来源字段，业务代码无需调整。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/tests.py
- Recurrence-Count: 2

---

## [ERR-20260907-012] marketing-embedding-json-response

**Logged**: 2026-09-07T13:11:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
真实营销对话在本地 embedding 服务不可用时直接解析空响应，向客户展示 `Expecting value` 并产生接口 500。

### Resolution
- **Resolved**: 2026-09-07T13:14:00+08:00
- **Notes**: 营销链路的知识检索异常改为降级到无引用生成，并增加客户可见安全兜底；原始异常仅写服务日志，不能直接展示给客户。

### Metadata
- Reproducible: yes
- Related Files: apps/application/chat_pipeline/step/search_dataset_step/impl/base_search_dataset_step.py, apps/application/chat_pipeline/step/chat_step/impl/base_chat_step.py

---

## [ERR-20260907-011] dynamic-workspace-model-key

**Logged**: 2026-09-07T13:09:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
浏览器验收准备阶段使用不存在的动态模型键读取工作空间，导致只读 shell 查询失败。

### Resolution
- **Resolved**: 2026-09-07T13:09:00+08:00
- **Notes**: 改为使用 `xpack_lite.models.Workspace` 和 `WorkspaceUserRoleMapping` 的实际模型定义。

### Metadata
- Reproducible: yes
- Related Files: apps/xpack_lite/models/rbac.py

---

## [ERR-20260907-010] django-command-missing-local-env

**Logged**: 2026-09-07T11:22:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
直接从 `apps` 目录执行 Django 迁移命令时没有加载项目 `.env.local`，配置加载器找不到数据库配置文件。

### Error
`ImportError: Error: No config file found.`

### Context
- 命令本身正确，但本地开发配置保存在仓库根目录 `.env.local`。
- 未输出或记录任何配置值。

### Suggested Fix
运行管理命令前从仓库根目录加载并自动导出 `.env.local`，保持与本地前后端启动脚本一致。

### Resolution
- **Resolved**: 2026-09-07T13:02:00+08:00
- **Notes**: 使用 shell 自动导出方式加载本地配置后，迁移文件正常生成；第二次未导出的尝试也归入同一问题。

### Metadata
- Reproducible: yes
- Related Files: .env.local, apps/telecom_ai_agent/const.py
- Recurrence-Count: 2

---

## [ERR-20260904-020] cua-playwright-url-method

**Logged**: 2026-09-04T16:43:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
最终浏览器检查尝试通过页面 Playwright 代理调用不存在的 `url()` 方法。

### Resolution
- **Resolved**: 2026-09-04T16:43:00+08:00
- **Notes**: 移除非必要地址读取，使用已知导航地址和控制台日志完成最终验收。

### Metadata
- Reproducible: yes
- Related Files: docs/测试/第二十七阶段-人工质检与修订闭环验收文档.md

---

## [ERR-20260904-019] quality-validation-business-500

**Logged**: 2026-09-04T16:41:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
DRF 参数校验异常经过项目统一异常处理器后被转换为业务码 500，导致“确认问题但未填意见”等预期输入错误看起来像服务异常。

### Resolution
- **Resolved**: 2026-09-04T16:41:00+08:00
- **Notes**: 人工质检服务显式将查询和处理参数错误转换为业务码 400，并增加回归测试；无效请求不会修改质检记录。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/serializers/quality_review.py, apps/marketing/tests.py

---

## [ERR-20260904-018] quality-browser-hmr-closed-drawer

**Logged**: 2026-09-04T16:38:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
质检页面热更新后抽屉自动关闭，浏览器验收脚本继续点击“取消”时选择器已不存在。

### Resolution
- **Resolved**: 2026-09-04T16:38:00+08:00
- **Notes**: 重新获取页面快照，再按最新页面状态打开已修订记录；最终页面和控制台检查通过。

### Metadata
- Reproducible: no
- Related Files: ui/src/views/marketing-quality/index.vue

---

## [ERR-20260904-017] quality-workbench-table-row-index

**Logged**: 2026-09-04T16:35:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: frontend

### Summary
Element Plus 表格插槽将行对象推断为 `any`，模板直接用行状态索引强类型映射时触发 Vue TypeScript 检查错误。

### Resolution
- **Resolved**: 2026-09-04T16:35:00+08:00
- **Notes**: 增加接收明确联合类型的状态转换函数，模板不再直接以 `any` 索引映射，也没有使用类型忽略指令。

### Metadata
- Reproducible: yes
- Related Files: ui/src/views/marketing-quality/index.vue

---

## [ERR-20260904-016] quality-review-select-for-update-outer-join

**Logged**: 2026-09-04T16:33:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
人工复核处理查询在 `select_for_update()` 前同时连接了可空的客户和复核人，PostgreSQL 拒绝对外连接的可空侧加行锁。

### Error
`FOR UPDATE cannot be applied to the nullable side of an outer join`

### Resolution
- **Resolved**: 2026-09-04T16:33:00+08:00
- **Notes**: 事务内只锁定质检主记录，关联对象按需读取；保留并发版本递增和唯一约束。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/serializers/quality_review.py

---

## [ERR-20260904-015] quality-test-patch-context

**Logged**: 2026-09-04T16:31:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
人工质检测试的首个补丁按预期导入顺序定位，但现有测试文件经过格式调整后导入顺序不同，补丁上下文未命中。

### Resolution
- **Resolved**: 2026-09-04T16:31:00+08:00
- **Notes**: 重新读取目标文件并使用实际上下文应用小范围补丁；失败尝试没有写入文件。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/tests.py

---

## [ERR-20260904-014] cua-tab-snapshot-method

**Logged**: 2026-09-04T16:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tooling

### Summary
浏览器验收时误把页面对象当作带 `snapshot()` 方法的对象调用，实际应通过页面的 Playwright DOM 快照能力读取结构。

### Resolution
- **Resolved**: 2026-09-04T16:25:00+08:00
- **Notes**: 改用 `playwright.domSnapshot()` 完成复盘页结构检查，并继续验证浏览器错误日志；业务代码和页面状态未受影响。

### Metadata
- Reproducible: yes
- Related Files: docs/测试/第二十六阶段-营销对话自动质检验收文档.md

---

## [ERR-20260904-013] page-dict-test-access

**Logged**: 2026-09-04T16:14:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
质检聚合测试把继承自 `dict` 的 `Page` 当作带 `.records` 属性的对象读取。

### Resolution
- **Resolved**: 2026-09-04T16:14:00+08:00
- **Notes**: 按后端真实结构改为 `page["records"]`，不改变接口返回契约。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/tests.py, apps/common/result/result.py

---

## [ERR-20260904-012] marketing-quality-test-import

**Logged**: 2026-09-04T13:45:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
新增营销回答质检测试时遗漏 `ChatRecord` 导入，Ruff 在执行测试前发现未定义名称。

### Resolution
- **Resolved**: 2026-09-04T13:45:00+08:00
- **Notes**: 补齐显式模型导入，并继续执行静态检查、迁移检查和测试。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/tests.py

---

## [ERR-20260904-011] excel-timezone-datetime

**Logged**: 2026-09-04T00:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: export

### Summary
后端生成 Excel 时直接写入带时区的 Django `datetime`，openpyxl 拒绝保存工作簿。

### Resolution
- **Resolved**: 2026-09-04
- **Notes**: 导出时间先转换为当前本地时区，再移除 `tzinfo` 后写入 Excel；增加工作簿加载测试防止回归。

---

## [ERR-20260904-010] mixed-backend-frontend-workdir

**Logged**: 2026-09-04T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
在 `ui` 工作目录中同时执行后端 Ruff 和前端校验，导致 Ruff 找不到 `apps/marketing` 文件。

### Resolution
- **Resolved**: 2026-09-04
- **Notes**: 后端校验改在 `apps` 目录执行，前端校验单独在 `ui` 目录执行；未影响代码和运行服务。

---

## [ERR-20260904-003] playwright-cli-npx-cache

**Logged**: 2026-09-04T13:23:00+08:00
**Priority**: low
**Status**: pending
**Area**: tooling

### Summary
Playwright CLI 包装器初始化时，`npx` 缓存目录在重命名 `playwright` 包时返回 `ENOTEMPTY`，无法创建浏览器会话。

### Context
- 命令：`playwright_cli.sh open http://127.0.0.1:3000/admin/marketing-campaign --headed`
- 失败目录：`/Users/zhaozhenchao/.npm/_npx/31e32ef8478fbf80/node_modules/playwright`
- 影响：仅影响 CLI 包装器；前后端服务及业务功能未受影响。

### Suggested Fix
后续在没有运行中 npx 进程时清理该单一缓存项并重装 `@playwright/cli`；本轮使用桌面浏览器自动化完成同等验收。

---

## [ERR-20260904-002] phase-25-validation-drift

**Logged**: 2026-09-04T13:17:00+08:00
**Priority**: low
**Status**: resolved
**Area**: validation

### Summary
活动复盘首轮并行检查发现前端编译目标不支持 `String.replaceAll`，营销任务接口类型将运行时必有字段误标为可选；全局 Django 迁移检查还报告了与本阶段无关的 `tools` 模块 choices 漂移。

### Resolution
- CSV 转义改用当前编译目标支持的正则替换。
- 将营销任务配置和服务端批次状态按真实响应收紧为必填类型，消除模板中的不安全索引。
- 本阶段迁移改用 `makemigrations marketing --check --dry-run` 定向确认，并单独审计 `tools` 漂移，不把无关迁移混入活动版本功能。

---

## [ERR-20260904-001] update-plan-unavailable

**Logged**: 2026-09-04T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
本轮计划同步调用不可用，但不影响仓库开发与验证。

### Resolution
- **Resolved**: 2026-09-04T00:00:00+08:00
- **Notes**: 改用对话进度更新继续推进，不依赖计划工具。

---

## [ERR-20260902-012] workspace-model-import

**Logged**: 2026-09-02T15:40:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
诊断工作空间时从 `system_manage.models` 导入了不存在的 `Workspace`，查询在写入前中断。

### Resolution
- **Resolved**: 2026-09-02T15:40:00+08:00
- **Notes**: 已确认工作空间模型位于 `xpack_lite.models`；后续写入前先用正确模型只读确认。

---

## [ERR-20260902-010] campaign-static-check

**Logged**: 2026-09-02T15:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
新增营销活动服务首次静态检查发现压缩式语句违反代码规范，且任务快照校验遗漏推荐策略校验函数导入。

### Resolution
- **Resolved**: 2026-09-02T15:00:00+08:00
- **Notes**: 已拆分服务与视图语句并补齐导入；后续以 ruff 作为迁移前门禁。

---

## [ERR-20260902-011] static-check-working-directory

**Logged**: 2026-09-02T15:05:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
在前后端混合检查时复用了错误工作目录，分别导致找不到 `ruff` 命令和后端模块相对路径。

### Resolution
- **Resolved**: 2026-09-02T15:05:00+08:00
- **Notes**: 后端检查固定从 `apps` 执行，前端检查固定从 `ui` 执行，不再串联跨目录命令。

---

## [ERR-20260902-010] class-method-shadows-builtin-type

**Logged**: 2026-09-02T14:30:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: backend

### Summary
`MarketingCustomerService` 已定义 `list()` 方法；在同一类中使用 `list[dict]` 类型注解时，Python 将 `list` 解析为该方法而不是内置类型，导致 Django 加载路由失败。

### Resolution
- **Resolved**: 2026-09-02T14:30:00+08:00
- **Notes**: 已移除该类方法内部不必要的内置泛型注解，并在后续迁移与系统检查中验证应用可正常加载。

---

## [ERR-20260901-007] result-envelope-business-error

**Logged**: 2026-09-01T16:51:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Endpoint boundary-test assertion expected HTTP 400, while this project encodes expected business validation failures as HTTP 200 with response body `code=400`.

### Error
`AssertionError: (200, {'code': 400, 'message': 'Customer is not included in this touch batch', 'data': None})`

### Context
The test attempted to record an execution result for a customer outside the selected batch snapshot. The endpoint correctly rejected it and did not return 500.

### Suggested Fix
For endpoint tests in this project, assert both HTTP transport success and the result-envelope business code according to the expected validation branch.

### Metadata
- Reproducible: yes
- Related Files: apps/common/result.py

### Resolution
- **Resolved**: 2026-09-01T16:51:00+08:00
- **Notes**: Boundary verification now treats `HTTP 200 + code=400` as the intended validation outcome.

---

## [ERR-20260901-006] drf-apiresponse-inspection

**Logged**: 2026-09-01T16:32:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Direct DRF view verification incorrectly assumed the project's result helper returns a DRF `Response` with a `.data` attribute.

### Error
`AttributeError: 'Result' object has no attribute 'data'`

### Context
The POST request had already completed successfully and created the test touch batch. The test harness failed only while reading its response.

### Suggested Fix
For direct view tests in this project, decode the JSON response body with `json.loads(response.content)` instead of accessing `.data`.

### Metadata
- Reproducible: yes
- Related Files: apps/common/result.py

### Resolution
- **Resolved**: 2026-09-01T16:32:00+08:00
- **Notes**: Subsequent endpoint assertions use decoded response content.

---

## [ERR-20260901-003] django-shell-paragraph-inspection

**Logged**: 2026-09-01T14:59:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
知识库检查脚本读取了 Paragraph 模型中不存在的 hit_handling_method 字段。

### Error
`AttributeError: 'Paragraph' object has no attribute 'hit_handling_method'`

### Context
仅用于输出诊断信息；查询在读取结果阶段失败，未修改任何业务数据。

### Suggested Fix
改为读取 Paragraph 实际字段，并从检索结果详情中检查命中策略。

### Metadata
- Reproducible: yes
- Related Files: apps/knowledge/models/paragraph.py

### Resolution
- **Resolved**: 2026-09-01T14:59:00+08:00
- **Notes**: 后续诊断脚本已移除该字段。

---

## [ERR-20260901-004] marketing-no-reference-setting-validation

**Logged**: 2026-09-01T15:04:00+08:00
**Priority**: high
**Status**: resolved
**Area**: backend

### Summary
营销无引用提示词返回了 Django 懒翻译对象，管道参数校验将其判为非字符串。

### Error
`no_references_setting.value: Not a valid string.`

### Context
真实流式会话在知识库未命中时返回配置错误文案，未产生 500，但导致客户无法获得答案。

### Suggested Fix
无引用提示词返回普通字符串；营销上下文仍由系统消息传递。

### Metadata
- Reproducible: yes
- Related Files: apps/application/serializers/common.py

### Resolution
- **Resolved**: 2026-09-01T15:04:00+08:00
- **Notes**: 已移除该路径上的懒翻译包装。

---

## [ERR-20260901-001] playwright_cli

**Logged**: 2026-09-01T00:00:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
Playwright CLI wrapper failed because the local npx cache could not rename an existing package directory.

### Error
```text
npm error ENOTEMPTY: directory not empty, rename .../@playwright/cli -> .../@playwright/.cli-...
```

### Context
- Attempted to run the bundled Playwright CLI wrapper for browser validation.
- This is an npm/npx cache issue, not an application runtime failure.

### Suggested Fix
Use an already installed Playwright package if available, or clear the specific stale npx package cache outside the application workspace.

### Metadata
- Reproducible: yes
- Related Files: /Users/zhaozhenchao/.codex/skills/playwright/scripts/playwright_cli.sh

---

## [ERR-20260901-002] playwright_node_script

**Logged**: 2026-09-01T00:00:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Node 24 rejected a Playwright script that mixed CommonJS `require()` with top-level `await`.

### Error
```text
ReferenceError: Cannot determine intended module format because both require() and top-level await are present.
```

### Context
- Attempted to run an inline Playwright browser validation script.
- The script used `require('playwright')` and top-level `await` together.

### Suggested Fix
Use ESM dynamic import or wrap the script body in an async function when running inline Node scripts.

### Metadata
- Reproducible: yes
- Related Files: ui/node_modules/playwright

---

## [ERR-20260901-005] marketing-recommendation-retest-env

**Logged**: 2026-09-01T15:47:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
营销推荐复测脚本遗漏数据库密码环境变量，初始化 Django 数据库连接失败。

### Error
`password authentication failed for user "root"`

### Context
仅用于本地演示场景的读取与会话验证；错误发生在读取访问令牌前，未发送聊天请求、未修改业务数据。

### Suggested Fix
复用后端启动使用的完整数据库环境变量，并在执行前核对变量名。

### Metadata
- Reproducible: yes
- Related Files: apps/marketing/recommendation.py

### Resolution
- **Resolved**: 2026-09-01T15:47:00+08:00
- **Notes**: 已修正测试命令的数据库密码变量并重新执行验证；运行多个 Django 命令时，每条命令都必须显式携带运行环境变量。

---

## [ERR-20260901-006] django-check-interpreter

**Logged**: 2026-09-01T16:10:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
直接调用系统 Python 执行 Django 检查时未加载项目虚拟环境，导致找不到 Django。

### Suggested Fix
后端检查、迁移和自测统一使用仓库根目录 `.venv/bin/python`，并保留后端启动所需的运行环境变量。

### Metadata
- Reproducible: yes
- Related Files: apps/manage.py

### Resolution
- **Resolved**: 2026-09-01T16:10:00+08:00
- **Notes**: 已定位运行中的后端使用项目 `.venv` 解释器，后续命令改用该解释器。

---

## [ERR-20260901-007] approval-route-test-prefix

**Logged**: 2026-09-01T17:25:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
审批接口的路由自测遗漏统一的 `/admin/api` 前缀，导致测试脚本解析到不存在的路径。

### Suggested Fix
接口路由测试应从项目总路由前缀拼接路径，并用 `finally` 清理临时批次。

### Metadata
- Reproducible: yes
- Related Files: apps/telecom_ai_agent/urls/web.py

### Resolution
- **Resolved**: 2026-09-01T17:25:00+08:00
- **Notes**: 已改用实际前缀重新执行路由和响应验证。

---

## [ERR-20260902-001] approval-dashboard-current-time

**Logged**: 2026-09-02T10:19:00+08:00
**Priority**: low
**Status**: resolved
**Area**: backend

### Summary
审批超时统计首次实现时遗漏初始化当前时间变量，静态检查发现未定义名称。

### Resolution
- **Resolved**: 2026-09-02T10:19:00+08:00
- **Notes**: 已在看板统计入口统一读取当前时间，并重新执行检查。

---

## [ERR-20260902-002] frontend-patch-context

**Logged**: 2026-09-02T10:26:00+08:00
**Priority**: low
**Status**: resolved
**Area**: frontend

### Summary
一次包含多个前端位置的补丁因代码上下文已变化而未匹配，未产生文件改动。

### Resolution
- **Resolved**: 2026-09-02T10:26:00+08:00
- **Notes**: 已先用精确行号定位状态、表单和映射位置，再拆分为小补丁继续修改。

---

## [ERR-20260902-003] django-standalone-settings

**Logged**: 2026-09-02T13:19:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
独立 Python 验收脚本调用 `django.setup()` 前未指定项目设置模块，导致 Django 设置未初始化。

### Resolution
- **Resolved**: 2026-09-02T13:19:00+08:00
- **Notes**: 独立脚本需显式设置 `DJANGO_SETTINGS_MODULE=telecom_ai_agent.settings`；也可优先经 `manage.py` 运行。

---

## [ERR-20260902-004] django-test-existing-database

**Logged**: 2026-09-02T13:20:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
Django 测试默认创建测试数据库时发现同名测试库已存在，并在非交互会话中请求删除确认而中断。

### Resolution
- **Resolved**: 2026-09-02T13:20:00+08:00
- **Notes**: 改用 `manage.py test --keepdb` 复用现有测试数据库，避免删除任何测试或业务数据。

---

## [ERR-20260902-005] django-test-migration-dependency

**Logged**: 2026-09-02T13:21:00+08:00
**Priority**: medium
**Status**: pending
**Area**: tests

### Summary
复用本地测试数据库执行 Django 测试时，系统管理迁移在 `workspace` 表创建前调用默认工作空间初始化，导致测试库迁移中断。

### Context
- 命令：`manage.py test marketing.tests.MarketingConversionTests --keepdb`
- 错误：`relation "workspace" does not exist`
- 影响：隔离测试库无法初始化；业务库迁移、真实路由和端到端临时数据验收均正常。

### Resolution
- **Resolved**: 2026-09-02T14:20:00+08:00
- **Notes**: 历史迁移不再调用当前运行时的工作空间模型；在该迁移所处的历史时点，按已有用户创建默认工作空间权限。全新临时测试库已完成全部迁移并通过营销回归测试。

### Metadata
- Reproducible: yes
- Related Files: apps/system_manage/migrations/0003_alter_workspaceuserresourcepermission_target.py, apps/xpack_lite/services.py

---

## [ERR-20260902-006] customer-list-test-param

**Logged**: 2026-09-02T13:23:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
端到端验收调用客户列表服务时传入列表而非查询字典，触发序列化器参数校验失败。

### Resolution
- **Resolved**: 2026-09-02T13:23:00+08:00
- **Notes**: 已改为传入空字典；测试的 `finally` 已清理临时任务、批次、客户和转化记录。

---

## [ERR-20260902-007] nested-workdir-path

**Logged**: 2026-09-02T13:26:00+08:00
**Priority**: low
**Status**: resolved
**Area**: tests

### Summary
在 `apps` 工作目录中诊断配置时重复使用了 `apps/` 路径前缀，导致只读查询找不到文件。

### Resolution
- **Resolved**: 2026-09-02T13:26:00+08:00
- **Notes**: 已改用相对当前工作目录的路径；未修改任何业务或配置文件。

---

## [ERR-20260902-008] models-provider-seed-migration

**Logged**: 2026-09-02T14:13:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
修复 `workspace` 依赖后，干净测试库在模型提供方历史种子迁移中向 `model_name` 非空字段写入空值而中断。

### Context
- 命令：使用独立临时数据库执行 `manage.py test marketing.tests`
- 错误：`null value in column "model_name" of relation "model" violates not-null constraint`
- 相关文件：`apps/models_provider/migrations/0001_initial.py`

### Suggested Fix
为历史内置 embedding 模型补齐稳定的 `model_name`，使初始种子数据符合初始表结构。

### Resolution
- **Resolved**: 2026-09-02T14:20:00+08:00
- **Notes**: 为未配置外部 embedding 模型名的干净环境提供稳定的历史默认值；后续重命名迁移会将其升级为当前名称。

---

## [ERR-20260902-009] pgvector-test-database-extension

**Logged**: 2026-09-02T14:14:00+08:00
**Priority**: medium
**Status**: resolved
**Area**: tests

### Summary
干净测试库创建知识库 embedding 表时未先启用 `pgvector` 扩展，导致 PostgreSQL 找不到 `vector` 类型。

### Suggested Fix
在知识库初始迁移创建使用 `vector` 类型的表之前执行 `CREATE EXTENSION IF NOT EXISTS vector`。

### Resolution
- **Resolved**: 2026-09-02T14:20:00+08:00
- **Notes**: 知识库初始迁移已在创建 embedding 表前确保启用 `vector` 扩展；全新临时测试库验证通过。

---
# ERR-023：补丁上下文过宽导致导入项落到文件尾部（2026-09-10）

- 现象：`py_compile` 能通过，但检查文件时发现新增的报告归因/投递模型名被追加为文件尾部裸表达式，模块加载时会触发 `NameError`。
- 根因：一次包含多个相似上下文的补丁错误匹配了文件末尾，没有在导入元组内落位；仅做语法编译无法发现模块级名字求值问题。
- 修复：将四个模型名移回 `marketing.models` 导入元组并删除尾部裸表达式。
- 验证：后续同时执行 `py_compile`、Django `check` 和目标测试，避免把语法通过误认为模块可导入。
## [ERR-20260911-063] M08-02 视图与定时任务合并补丁上下文不匹配

- 时间：2026-09-11
- 现象：一次性新增流水线视图、路由和定时任务时，`apps/common/job/__init__.py` 的预期导入上下文不存在，导致 `apply_patch` 整体校验失败。
- 根因：补丁基于假定的 `pipeline_jobs`/`marketing_jobs` 导入名，而文件实际使用的是 `marketing.pipeline_jobs` 尚未引入、营销任务变量名也不同。
- 修复：先读取真实文件内容，将新增文件、模块导出、路由和任务入口拆成独立小补丁，按实际上下文落位。
- 验证：后续通过 Django `check`、目标测试和接口验收确认。

## [ERR-20260911-064] 工具编排脚本出现语法错误

- 时间：2026-09-11
- 现象：拆分补丁时生成了无效 JavaScript，工具在执行前以 `Unexpected token` 失败，未修改文件。
- 根因：工具调用中混入了不属于脚本的文本和多余括号。
- 修复：恢复为单条、最小化的 `apply_patch` 或 `exec_command` 调用，执行前检查括号和字符串边界。
- 验证：后续最小化只读命令已正常执行。

## [ERR-20260911-065] 最小化只读命令变量声明不完整

- 时间：2026-09-11
- 现象：一次读取错误日志的工具脚本因变量声明不完整而在执行前失败，未运行任何 shell 命令。
- 根因：编排层代码生成不完整。
- 修复：使用固定模板 `const result = await tools.exec_command(...); text(result.output);`，不在同一调用组合其他操作。
- 验证：相同模板随后成功读取错误日志。

## [ERR-20260911-066] 定时任务补丁混入异常字符

- 时间：2026-09-11
- 现象：新建 `pipeline_jobs.py` 后复查发现导入行后多出分号，调度参数中混入字符，会导致 Python 语法错误和未定义变量。
- 根因：补丁生成文本被异常字符污染，但 `apply_patch` 只校验上下文，不校验 Python 语法。
- 修复：逐行修正异常字符；所有新增 Python 文件立即执行 `py_compile`，再运行 Django `check`。
- 验证：待本轮静态检查确认。

## [ERR-20260911-067] 错误日志与代码合并补丁上下文不匹配

- 时间：2026-09-11
- 现象：修复定时任务时同时追加错误日志，因日志预期文本与实际文本不完全一致，补丁整体未应用。
- 根因：把无依赖的代码修复和文档记录放入同一补丁。
- 修复：代码与日志分开应用，代码补丁已成功。
- 验证：后续读取文件并执行语法检查。

## [ERR-20260911-068] 追加错误记录时再次使用了不精确上下文

- 时间：2026-09-11
- 现象：第二次追加记录仍因预期验证语句与实际内容不同而失败。
- 根因：未先读取日志尾部就假定了上一条记录的精确文字。
- 修复：先读取文件尾部，再以真实末行作为补丁锚点。
- 验证：本条记录已成功追加。

## [ERR-20260911-069] 模块导出与任务入口补丁仍被错误合并

- 时间：2026-09-11
- 现象：更新视图和序列化器导出时，补丁又包含了不存在的任务入口上下文，导致整体未应用。
- 根因：没有遵守上一条记录提出的单文件小补丁约束。
- 修复：先独立更新模块导出，再按真实内容更新任务入口。
- 验证：模块导出和任务入口均已应用。

## [ERR-20260911-070] 错误记录补丁自身混入无关文本

- 时间：2026-09-11
- 现象：ERR-069 的现象描述中混入无关英文提示文本。
- 根因：生成补丁时文本内容被污染，且没有在提交前做最小内容核对。
- 修复：读取日志尾部并替换为完整、准确的中文记录。
- 验证：当前日志尾部内容已修正。

## [ERR-20260911-071] 模块导出出现重复导入

- 时间：2026-09-11
- 现象：复查发现视图和序列化器 `__init__.py` 中各有两条相同的 pipeline 导入。
- 根因：前次合并补丁虽报告后部上下文失败，但前部文件变更已存在，之后又重复应用。
- 修复：删除重复导入，并在每次补丁后读取目标文件核对实际状态。
- 验证：两个模块均只保留一条 pipeline 导入。

## [ERR-20260911-072] 补丁缺少结束标记

- 时间：2026-09-11
- 现象：一次清理重复导入的补丁缺少 `*** End Patch`，执行前即失败。
- 根因：补丁模板不完整。
- 修复：恢复完整模板后重新执行。
- 验证：完整补丁已成功应用。

## [ERR-20260911-073] 清理重复导入时文件路径拼写错误

- 时间：2026-09-11
- 现象：一次补丁把 `__init__.py` 写成 `__init__..py`，未找到文件。
- 根因：路径多输入了一个句点。
- 修复：使用从只读输出确认的准确路径重新执行。
- 验证：流水线新增的五个 Python 文件均已通过 `py_compile`。

## [ERR-20260911-074] 流水线阶段快照包含 datetime 导致测试失败

- 时间：2026-09-11
- 现象：6 个流水线测试均在保存评估阶段输出时失败，错误为 `Object of type datetime is not JSON serializable`；异常处理随后因测试事务已 broken 又触发 `TransactionManagementError`。
- 根因：生命周期序列化字典包含时间对象，却被直接写入阶段 JSONField。
- 修复：阶段输入和输出快照入库前统一通过 Django JSON 编码器转换成 JSON 安全值。
- 验证：6 个流水线测试已全部通过。

## [ERR-20260911-075] Vue 组件补丁混入异常模板文本

- 时间：2026-09-11
- 现象：新增流水线工作台后复查发现 3 处模板标签或 class 中混入无关字符。
- 根因：大段补丁生成文本被污染，语义异常但仍可落盘。
- 修复：用 `rg` 搜索异常片段并逐处恢复为标准 Vue 模板。
- 验证：目标文件 ESLint 已通过。

## [ERR-20260911-076] 模板表格行状态索引缺少类型边界

- 时间：2026-09-11
- 现象：`vue-tsc` 报 TS7053，模板中的表格 `row.status` 被推断为 any，不能直接索引强类型状态映射。
- 根因：Element Plus 表格插槽行缺少可推断的泛型类型。
- 修复：增加接收 `PipelineRunStatus` 的 `getStatusType` 函数，把类型边界从模板移入脚本。
- 验证：`pnpm run type-check` 已通过。

## [ERR-20260911-077] 非 Plan 模式误调用交互提问工具

- 时间：2026-09-11
- 现象：误调用了仅 Plan 模式可用的用户输入工具，调用被拒绝，未产生项目变更。
- 根因：工具选择错误，本任务无需用户确认。
- 修复：继续按既定计划执行，不再调用该工具。
- 验证：后续命令正常执行。

## [ERR-20260911-078] 编排脚本包含无效问号表达式

- 时间：2026-09-11
- 现象：一次空编排脚本包含无效问号表达式，在执行前失败。
- 根因：工具调用内容生成不完整。
- 修复：恢复固定的最小工具调用模板。
- 验证：后续只读命令已成功。

## [ERR-20260911-079] Playwright 技能读取命令脚本被污染

- 时间：2026-09-11
- 现象：读取 Playwright 技能时命令参数混入无效标识符，导致编排脚本执行前失败。
- 根因：工具脚本没有保持单一命令结构。
- 修复：改为固定模板，仅执行一条读取命令。
- 验证：Playwright 技能文件已完整读取。

## [ERR-20260911-080] Playwright 浏览器会话未打开

- 时间：2026-09-11
- 现象：首次执行 `tab-list` 时默认浏览器未打开，命令退出码为 1。
- 根因：误以为上一轮浏览器会话仍然存在。
- 修复：先显式打开浏览器，再进行导航和控制台检查。
- 验证：后续浏览器验收成功。

## [ERR-20260911-081] 页签接入补丁重复应用

- 时间：2026-09-11
- 现象：再次接入流水线页签时上下文不匹配；复查发现接入已经存在。
- 根因：未先核对大补丁的实际落盘范围。
- 修复：以文件现状为准，不再重复修改。
- 验证：默认流水线页签和浏览器展示正常。

## [ERR-20260911-082] Ruff 文件路径拼写错误

- 时间：2026-09-11
- 现象：首次 Ruff 命令把目录名多写了一个字母，目标文件不存在。
- 根因：手工输入路径错误。
- 修复：从实际文件路径复制后重新执行。
- 验证：M08-02 后端目标文件 Ruff 检查通过。

## [ERR-20260911-083] 回归命令误用裸 set 打印环境变量

- 时间：2026-09-11
- 现象：加载 `.env.local` 后，本应执行 `set +a`，却误写为裸 `set`，导致环境变量被输出到命令日志。
- 根因：后端命令基线被手工输入错误，且执行前没有核对环境加载模板。
- 修复：固定使用 `set -a`、`source .env.local`、`set +a` 三行模板；加载本地配置的命令块禁止出现裸 `set`；记录中不抄录任何变量值。
- 验证：该次测试本身 15 项通过；最终检查使用固定模板重新执行。

## [ERR-20260911-084] 经验规则合并补丁包含不存在的手册标题

- 时间：2026-09-11
- 现象：同时更新错误日志、AGENTS 和排障手册时，因假定的手册标题不存在导致补丁失败。
- 根因：再次合并了多个无依赖文件，且未读取手册实际标题。
- 修复：分别更新错误日志与 AGENTS；手册按实际章节追加。
- 验证：待最终核对。

## [ERR-20260911-085] 只读核对命令路径被污染

- 时间：2026-09-11
- 现象：一次核对命令的文件名和工作目录混入无效字符，进程未创建。
- 根因：工具参数生成异常。
- 修复：恢复真实工作目录和文件路径后重新执行。
- 验证：后续核对命令成功。

## [ERR-20260912-086] 定时任务错误使用 RedisLock 上下文管理器

- 时间：2026-09-12
- 现象：最终复查发现 `pipeline_jobs.run()` 使用 `with RedisLock(key)`，但项目的 `RedisLock` 构造函数不接收参数，也未实现上下文管理器协议。
- 根因：沿用了通用锁的常见写法，没有先核对项目自定义锁接口；Django `check` 不会执行任务注册函数，因此未提前暴露。
- 修复：改为项目已有的 `RedisLock()`、`try_lock()`、`finally un_lock()` 模式，并增加调度注册单元测试。
- 验证：调度注册单元测试和真实 DjangoJobStore 注册均通过。

## [ERR-20260912-087] 修复调度锁的首个补丁混入草稿字符

- 时间：2026-09-12
- 现象：首次修复补丁的预期行混入无关字符，校验失败，未修改文件。
- 根因：补丁生成文本未在执行前核对。
- 修复：读取目标文件后，以准确上下文重新应用最小补丁。
- 验证：调度锁实现已正确修改。

## [ERR-20260912-088] keepdb 中后台调度补跑干扰全库计数断言

- 时间：2026-09-12
- 现象：新增调度测试后，测试进程启动时历史 APScheduler 任务出现 missed-run 补跑；3 个使用全库计数的断言受到并发测试数据干扰而失败。
- 根因：测试断言统计全表或全部到期流水线，没有绑定本次创建的模型版本/流水线 ID；在 `--keepdb` 且调度线程活跃时不具隔离性。
- 修复：发布记录按本次 `model_version_id` 统计，定时扫描结果按本次 `pipeline_id` 筛选。
- 验证：7 个流水线测试已全部通过。

## [ERR-20260912-089] 浏览器内注销请求失败

- 时间：2026-09-12
- 现象：尝试在临时 Playwright 页面内调用注销接口时 `fetch` 失败，随后浏览器会话已关闭。
- 根因：临时浏览器会话中的前端代理/服务状态已变化，页面内请求未能送达注销接口。
- 修复：关闭隔离浏览器；在服务端检查系统令牌缓存，当前无临时系统用户令牌，因此未删除或影响其他登录会话。
- 验证：浏览器进程已关闭，Redis 中系统 TOKEN 缓存计数为 0。

## [ERR-20260912-090] 发布记录模型补丁使用了过时上下文

- 时间：2026-09-12
- 现象：补充索引发布记录字段时，补丁校验失败，文件未被修改。
- 根因：大段文件创建后没有先读取文件尾部，误以为字段尚未写入，并使用了与实际内容不一致的上下文。
- 修复：立即读取目标模型尾部，确认原因、操作人和排序字段已完整存在，不再重复修改。
- 验证：`KnowledgeIndexReleaseRecord` 已包含 `reason`、`operator`、`operator_name` 及倒序排列配置。

## [ERR-20260912-091] APIClient 验收缺少项目权限上下文

- 时间：2026-09-12
- 现象：使用 DRF `APIClient.force_authenticate(user=...)` 调用 ETL 接口时，权限装饰器读取 `request.auth.role_list` 报空；同时误把项目自定义 `JsonResponse` 当作 DRF Response 读取 `.data`。
- 根因：项目权限校验不仅依赖 `request.user`，还依赖认证处理器生成的角色/权限上下文；统一响应类型是 `common.result.Result`。
- 修复：验收夹具为 `force_authenticate` 同时注入只含测试角色的认证上下文，并从响应 JSON 内容读取统一响应体，不生成或回显真实访问令牌。
- 验证：补齐测试角色上下文后，ETL 创建、发布与仪表盘三个 API 均返回 HTTP 200 和应用码 200。

## [ERR-20260912-092] 浏览器连接器无法枚举标签页

- 时间：2026-09-12
- 现象：精简 UI 验收时，计算机使用连接器能返回本机应用列表，但浏览器清单为空并提示请求失败。
- 根因：连接器到浏览器提供方的本地请求异常，和 ETL 页面、前后端服务无关。
- 修复：停止重复调用连接器，改用仓库既有的隔离 Playwright 验收方式；业务数据继续通过 API 构造。
- 验证：隔离 Playwright 会话成功展示 ETL 页面，控制台 0 错误并滚动到底部。

## [ERR-20260912-093] Playwright run-code 多语句格式错误

- 时间：2026-09-12
- 现象：隔离 UI 验收中，把多个 `await page...` 语句直接传给 `run-code`，CLI 返回 JavaScript 语法错误，登录未提交。
- 根因：当前 Playwright CLI 的 `run-code` 参数需要可调用的异步函数体，多语句不能按 `eval` 表达式格式传入。
- 修复：保留环境变量传递临时密码的安全方式，改用 `async (page) => { ... }` 函数格式。
- 验证：改用 storage-state 后成功登录并打开 ETL 页面。

## [ERR-20260912-094] Playwright CLI 帮助子命令写法错误

- 时间：2026-09-12
- 现象：为确认 `run-code` 语法执行了 `playwright-cli help run-code`，CLI 提示 `help` 不是命令并只返回总帮助。
- 根因：把常见的 `help <command>` 形式套用到该 CLI；它使用 `--help [command]`。
- 修复：后续按总帮助已确认的 `run-code [code]` 用法直接使用异步函数表达式，不再试错组合帮助命令。
- 验证：异步函数格式可正常执行页面滚动、详情展开和注销请求。

## [ERR-20260912-095] Playwright run-code 无法读取进程环境变量

- 时间：2026-09-12
- 现象：异步函数格式已被 CLI 接受，但函数内读取 `process.env` 时提示 `process is not defined`，登录仍未提交。
- 根因：当前 Playwright CLI 在隔离执行上下文运行代码，不暴露 Node `process`，不能用环境变量安全传入密码。
- 修复：禁止退化为把密码或令牌写进 CLI 参数；改为权限收紧的一次性 storage-state 文件，验收后删除临时账号、浏览器会话和状态文件。
- 验证：未把密码或令牌放入 CLI 参数；一次性状态文件加载成功。

## [ERR-20260912-096] Playwright 包装器无法读取进程替换状态流

- 时间：2026-09-12
- 现象：用 `/dev/fd/*` 进程替换向 `state-load` 提供一次性认证状态时，子进程读取到空 JSON。
- 根因：Playwright 包装器还会启动下级 `npx` 进程，进程替换文件描述符没有可靠继承到最终进程。
- 修复：停止组合调用；使用 `mktemp -d` 创建仓库外临时目录，生成权限为 600 的短期 storage-state 文件，加载后立即删除。
- 验证：权限为 600 的临时状态文件可被 Playwright 加载，验收后目录已删除。

## [ERR-20260912-097] 临时状态目录清理命令被安全策略拒绝

- 时间：2026-09-12
- 现象：尝试用 `rm -rf` 删除已验证的单一临时目录时，命令在创建进程前被安全策略拒绝，后续页面导航也未执行。
- 根因：清理命令仍使用了递归强制删除形式，不符合项目的可控删除约束。
- 修复：改为校验并删除确切的 `state.json` 文件，再用 `rmdir` 删除空目录；页面导航单独执行。
- 验证：精确删除状态文件并移除空目录后，路径不存在；临时账号计数为 0。

## [ERR-20260912-098] Playwright 临时快照文件名手输错误

- 时间：2026-09-12
- 现象：精确清理本次五个浏览器临时文件时，最后一个时间戳路径混入错误字符；前四个已删除，最后一个未删除。
- 根因：没有把只读枚举结果原样复制到删除命令。
- 修复：重新枚举本次剩余文件，只对准确路径执行一次最小删除。
- 验证：按准确路径删除后，本次时间范围内不再有 Playwright 临时文件。

## [ERR-20260912-099] 平台监控服务文件尾部残留重复草稿

- 时间：2026-09-12
- 现象：补充告警操作和定时采集函数后，文件尾部仍保留一份旧实现，形成缩进错误和重复定义。
- 根因：在未读取文件尾部的情况下连续应用大段补丁，新增实现没有完整替换先前草稿。
- 修复：立即读取文件尾部，精确删除重复代码；后续先做重复定义检索和 Python 编译检查，再运行 Django 检查。
- 验证：文件尾部只保留一份 `operate_alert` 与 `collect_all_workspaces` 实现。

## [ERR-20260912-100] Element Plus 表格插槽行类型不能直接索引严格映射

- 时间：2026-09-12
- 现象：平台监控页面类型检查报 TS7053，模板中的 `row.auto_action` 被推断为 `any`，无法直接索引 `Record<MonitoringAutoAction, string>`。
- 根因：`el-table-column` 默认插槽没有把数据行泛型传播给 Vue 模板类型检查器。
- 修复：增加接收字符串边界值的 `getAutoActionLabel()`，在函数内部收窄到已知联合类型并提供未知值回退。
- 验证：目标 ESLint 和 `vue-tsc --build` 已通过。

## [ERR-20260912-101] 全局告警通知测试忽略了多接收人语义

- 时间：2026-09-12
- 现象：平台告警通知测试用来源 ID 执行 `.get()`，默认工作区存在多个有效管理员时返回多条记录。
- 根因：全局铃铛通知按“告警 × 接收人”生成，测试错误地假设一个告警全局只有一条通知。
- 修复：断言增加本次测试用户条件，验证该接收人的通知内容和跳转地址。
- 验证：重新运行平台监控全部服务与 API 测试。

## [ERR-20260912-102] 运行中的后端未热加载新增 URL 配置

- 时间：2026-09-12
- 现象：独立 Django APIClient 已成功调用平台监控接口，但运行在 8080 的现有后端进程及 Vite 代理仍对新增路径返回 404。
- 根因：当前联调后端进程未启用或未触发 URL 配置热加载，仍持有功能开发前的路由表。
- 修复：保留前端、Ollama 和向量服务，仅重启后端进程；随后同时验证直连与 Vite 代理受保护接口返回 401 而不是 404。
- 验证：重启后，直连 8080 与 Vite 代理 3000 均从 404 变为受保护接口预期的 401，页面路由返回 200。

## [ERR-20260912-103] 浏览器连接器策略读取错误再次出现

- 时间：2026-09-12
- 现象：M08-04 精简 UI 验收时，浏览器连接器仍无法枚举标签页并提示无法加载 request-header policy。
- 根因：本地浏览器提供方策略链路异常，与平台监控页面和服务状态无关。
- 修复：不重复调用连接器，切换到已验证的隔离 Playwright + 短期 storage-state 方式，仅检查关键显示、控制台和滚动。
- 验证：隔离浏览器完成页面、全局铃铛、控制台和滚动验收，临时状态已撤销并删除。
- 关联：ERR-20260912-092。

## [ERR-20260912-104] Playwright storage-state 加载顺序错误

- 时间：2026-09-12
- 现象：先执行 `state-load` 再打开命名浏览器会话时，CLI 提示会话尚未打开；随后页面进入登录页。
- 根因：当前 Playwright CLI 的 `state-load` 只能作用于已经存在的浏览器会话。
- 修复：改为“先 open 会话 → state-load → goto 目标页”的固定顺序，不重新生成或回显短期令牌。
- 验证：按正确顺序恢复登录态后成功打开 `/admin/platform-monitoring`。

## [ERR-20260912-105] 多文件文档补丁因末段上下文校验失败

- 时间：2026-09-12
- 现象：一次性创建验收文档并修改计划、排障手册和 AGENTS 时，末段上下文未匹配，整包未落盘。
- 根因：把四类文档更新放入同一个大补丁，任一文件上下文变化都会阻断全部修改。
- 修复：确认文件均未写入后，停止组合调用，改为按目标文件分别应用最小补丁。
- 验证：验收文档、计划状态、手册章节和 AGENTS 新规则均已分别写入并检索确认。

## [ERR-20260912-106] 监控规则局部更新会误判阈值缺失

- 时间：2026-09-12
- 现象：规则启用/停用接口只提交 `enabled` 时，写入序列化器看不到数据库中的原阈值，可能返回“至少配置一个告警阈值”。
- 根因：服务把请求作为序列化器的 `partial` 数据校验，但跨字段校验仅检查本次请求字段，没有合并已有规则值。
- 修复：更新已有规则前先把当前完整配置与请求字段合并，再执行一次完整校验和保存；补充仅更新 `enabled` 的回归断言。
- 验证：后端 Ruff、Django check、无缺失迁移检查和平台监控 5 个测试全部通过；后端重启后直连接口与 Vite 代理均返回预期的未认证 401。

## [ERR-20260912-107] 营销模块只读检索命令混入错误路径

- 时间：2026-09-12
- 现象：组合读取营销模块结构时，`sed` 参数中误写了不存在的 `apps/marketing/models/__.py`，并把范围参数拆成了独立路径。
- 根因：一次命令混排多个文件与范围时未先核对实际文件清单，且命令后段成功掩盖了前段读取错误。
- 修复：停止复用该组合命令，后续只对 `rg --files` 已确认存在的文件逐个读取，并以 `set -e` 保证任一步失败即退出。
- 验证：使用 `set -e` 和已确认路径分别读取模型导出、场景模型、视图导出、URL、服务及前端路由，全部成功。

## [ERR-20260912-108] 物料向量范数字段重复声明

- 时间：2026-09-12
- 现象：生成推荐模型迁移后复读源码，发现 `RecommendationItemEmbedding.vector_norm` 连续声明两次。
- 根因：大段新增模型文件后又单独补字段，没有先检索确认该字段已经包含在草稿末段；Python 静默覆盖前一声明，普通静态检查未报错。
- 修复：保留与已生成迁移一致的单一 `default=0` 声明，并重新执行重复字段检索、迁移差异检查和测试。
- 验证：重复字段检索只剩单一定义，迁移差异检查无变更，推荐引擎 5 个专项测试全部通过。

## [ERR-20260912-109] Playwright run-code 等待语法不兼容

- 时间：2026-09-12
- 现象：页面导航成功后执行 `run-code "await page.waitForTimeout(...)"`，当前 CLI 报 `SyntaxError: Unexpected identifier 'page'`。
- 根因：当前 Playwright CLI 的 `run-code` 不接受裸 `await page...` 语句，参考示例与实际版本行为不一致。
- 修复：移除非必要的显式等待，改用导航完成后的 `snapshot`、`console` 和只读 `eval` 验收。
- 验证：移除显式等待后完成页面快照、TopK 交互、0 控制台错误及滚动到底验收。

## [ERR-20260912-110] 错误记录补丁引用了不存在的标题

- 时间：2026-09-12
- 现象：追加 ERR-109 时误把 ERR-108 的标题写成上一条只读检索错误，导致补丁上下文校验失败。
- 根因：未先读取错误日志尾部就手工复用相邻编号标题。
- 修复：先读取日志尾部确认真实标题，再以末条完整上下文追加最小补丁。
- 验证：ERR-109 与本条记录已成功追加，未改动既有条目。

## [ERR-20260912-111] 验收文档新增补丁头格式错误

- 时间：2026-09-12
- 现象：创建 M07-01 验收文档时，`Add File` 路径后误插入独立 `.md` 行，补丁解析器判定为非法 hunk header。
- 根因：长文件补丁的目标路径在编辑草稿时被错误断行。
- 修复：确认目标文档未创建，改用完整且单行的绝对文件路径重新提交单文件补丁。
- 验证：`docs/测试/双塔召回模型M07-01验收文档.md` 已创建并包含完整验收标题与结果。

## [ERR-20260912-112] 最终 Ruff 命令误包含整个 apps 目录

- 时间：2026-09-12
- 现象：目标文件列表中间误多写一个独立 `apps` 参数，Ruff 扫描全仓库并报告 672 条既有基线问题，后续后端检查按 `set -e` 停止。
- 根因：长文件列表人工拼接时未检查每个路径是否都为明确目标文件。
- 修复：不处理无关基线问题；改用数组式精确目标清单重新运行 Ruff，再继续 Django、迁移和专项测试。
- 验证：精确目标文件 Ruff 全部通过，随后 Django check、迁移差异检查和 5 项专项测试均通过；未修改任何无关基线文件。

## [ERR-20260912-113] ERR-112 追加补丁再次使用错误上下文

- 时间：2026-09-12
- 现象：记录 Ruff 命令错误时，把 ERR-110 的验证行错误地放在 ERR-111 标题下，导致补丁上下文校验失败。
- 根因：在没有复读日志尾部的情况下凭编号记忆拼接上下文，重复了 ERR-110 的同类错误。
- 修复：停止猜测上下文，先执行最小 `tail`，再以最后一条完整标题和验证行追加记录。
- 验证：ERR-112 与本条记录已成功追加。

## [ERR-20260912-114] 融合服务残留未使用导入导致静态检查中止

- 时间：2026-09-12
- 现象：首次执行 M07-02 目标文件 Ruff 时，`recommendation_fusion.py` 中的 `_to_number` 被报告为未使用，后续迁移生成按 `set -e` 中止。
- 根因：融合算法草稿最初计划直接比较数值特征，最终改为复用规则匹配函数后没有同步删除该导入。
- 修复：删除未使用导入，再重新执行目标 Ruff 和迁移生成。
- 验证：删除导入后目标 Ruff 通过，迁移 `0028_recommendation_fusion_v1.py` 成功生成，Django check、迁移差异检查及 10 项推荐引擎测试全部通过。

## [ERR-20260912-115] 前端目录内重复定义检查误用仓库根路径

- 时间：2026-09-12
- 现象：在 `ui/` 工作目录执行重复定义检查时仍传入 `apps` 和 `ui` 根目录相对路径，`rg` 报路径不存在，后续 ESLint 与类型检查按 `set -e` 中止。
- 根因：把必须在 `ui/` 执行的前端检查与仓库根目录的跨端检索放进了同一命令块，却没有按工作目录拆分路径。
- 修复：跨端重复定义检索改在仓库根目录执行；ESLint、类型检查与构建单独在 `ui/` 执行。
- 验证：跨端检索在仓库根目录确认目标类和导出均只有单一定义；前端目标 ESLint、类型检查与生产构建全部通过。

## [ERR-20260912-116] APIClient 验收脚本误把项目 Result 当作 DRF Response

- 时间：2026-09-12
- 现象：通过 Django `APIClient` 创建融合验收客户成功后，脚本读取 `response.data` 报 `AttributeError: 'Result' object has no attribute 'data'`，后续接口验收中止。
- 根因：项目的 `result.success()` 返回自定义 HTTP `Result`，不像 DRF `Response` 暴露 `.data`；既有专项测试实际使用 `json.loads(response.content)`，验收脚本未复用该约定。
- 修复：保留已成功创建的脱敏客户，后续统一使用 `json.loads(response.content)["data"]` 解析接口响应，并让脚本先复用已有客户再继续。
- 验证：修正为解析 `response.content` 后，客户双塔推理、融合配置、融合推理和融合看板四个接口均为 200；六路全部命中北京物料且去重断言通过。

## [ERR-20260912-117] CUA 首次读取浏览器状态时策略加载失败

- 时间：2026-09-12
- 现象：真实页面验收前调用 CUA `getState()`，应用清单成功返回，但浏览器部分报 `Unable to load browser request-header policy`。
- 根因：CUA 浏览器请求头策略在首次初始化时未能加载，属于浏览器控制层临时初始化失败，并非前端服务故障。
- 修复：按工具返回建议重试浏览器状态读取；若仍失败则改用已加载 Playwright 技能的隔离会话验收。
- 验证：第二次 `getState()` 成功返回 Chrome 及本地前端标签页，确认是一次性初始化波动。

## [ERR-20260912-118] CUA 直接 getTab 后误使用未绑定 browser 变量

- 时间：2026-09-12
- 现象：通过 `cua.getTab()` 已取得本地页面句柄后，按会话命名要求调用 `browser.nameSession()`，运行时提示 `browser is not defined`。
- 根因：首个选择调用只把结果赋给了 `tab`，工具虽选择了浏览器但没有自动创建 JavaScript 的 `browser` 变量。
- 修复：显式通过本地 URL 获取并绑定 `browser` 句柄，再命名会话并继续复用已有 `tab`。
- 验证：显式绑定 Chrome 浏览器并成功认领原有本地前端标签页；浏览器会话已命名。

## [ERR-20260912-119] CUA 本地页面等待模式不支持 networkidle

- 时间：2026-09-12
- 现象：认领 Chrome 本地页面并导航成功后，调用 `waitForLoadState({state: "networkidle"})` 报当前实现不支持该等待模式。
- 根因：CUA 暴露的类型文档列出 `networkidle`，但本次 Chrome 扩展后端只支持较基础的加载状态。
- 修复：改用 `domcontentloaded`，再通过目标标题/控件可见性确认异步接口数据已渲染。
- 验证：改用 `domcontentloaded` 并等待页面标题后，完整 DOM 快照成功返回，多路融合页面和异步数据均已呈现。

## [ERR-20260912-120] 融合记录页误按页签名称定位 tabpanel

- 时间：2026-09-12
- 现象：点击“融合记录 2”页签后，继续用相同名称精确等待 `tabpanel`，但 Element Plus 面板未暴露对应可访问名称，等待超时。
- 根因：把 `tab` 的可访问名称错误假设为其关联 `tabpanel` 的名称；点击本身已成功，不应依赖这一非必要定位。
- 修复：点击后直接重新读取 DOM 快照，以“客户/模型/TopK/执行时间”等实际表头确认面板切换，再执行滚动和控制台检查。
- 验证：重新点击后直接等待实际表头“执行时间”，融合记录面板成功显示两条真实记录和本地化执行时间。

## [ERR-20260912-121] CUA 页面重载后的复合验收调用在指标读取时超时

- 时间：2026-09-12
- 现象：为隔离历史控制台错误，单次 CUA 调用串联重载、标题等待、日志过滤和滚动指标读取；前序步骤完成后，最后读取 `.recommendation-page` 指标时 CDP `Runtime.evaluate` 超时。
- 根因：重载后的多个浏览器动作压在同一次调用中，Chrome 扩展的短 CDP 评估窗口不足；并非页面标题或接口加载失败。
- 修复：停止复合调用，后续把控制台日志和布局指标拆成两个最小只读检查；控制台只统计重载时间点之后的新错误。
- 验证：该复合调用不再复用；此前已分别完成页面关键交互、配置弹窗、融合记录和页面底部检查。跨日后以专项测试、生产构建及直连/代理端点状态重新验证功能与路由。

## [ERR-20260914-122] 跨日继续验收时本地前端服务已停止

- 时间：2026-09-14
- 现象：继续 M07-02 浏览器复验时，原标签页仍保留已渲染页面；主动重载后变为 `ERR_CONNECTION_REFUSED`。
- 根因：前一开发回合与本次继续之间跨日，原 Vite 开发服务进程已退出；保留标签页不能作为当前服务在线证据。
- 修复：重新核对 3000/8080 端口和进程，按项目命令基线启动缺失的前后端，再通过重载页面、直连接口和 Vite 代理复验。
- 验证：前后端重新启动后，`8080` 直连和 `3000` Vite 代理的新融合看板端点均返回预期未认证 401；浏览器可重新进入登录页，证明前端服务已恢复，未复用过期登录态。

## [ERR-20260914-123] 精排页面补丁使用省略文本导致上下文校验失败

- 时间：2026-09-14
- 现象：向推荐引擎页面插入精排策略与运行记录页签时，`apply_patch` 提示找不到预期行，文件未发生修改。
- 根因：补丁定位文本中误写了人工省略号，并非源文件里的完整标签内容。
- 修复：先用 `rg` 获取真实行号和完整标签，再以精确上下文拆分提交补丁。
- 验证：使用真实完整标签定位后页签补丁成功；目标 ESLint、类型检查和生产构建均通过。

## [ERR-20260914-124] 精排 API 导出补丁基于过期文件顺序定位失败

- 时间：2026-09-14
- 现象：补充精排看板请求函数时，`apply_patch` 找不到推理导出前的预期上下文，文件未被该次操作修改。
- 根因：前一批补丁已改变 API 文件尾部导出顺序，且同批操作实际已加入目标函数；继续按旧顺序定位造成失败，并暴露了重复的版本创建/发布导出。
- 修复：读取文件尾部真实内容，保留单一的看板、创建、发布、推理导出并删除重复定义。
- 验证：API 看板、创建、发布和推理导出均仅保留一个定义；目标 ESLint、类型检查和生产构建均通过。

## [ERR-20260914-125] 前端工作目录再次混入仓库根检索路径

- 时间：2026-09-14
- 现象：在 `ui/` 工作目录执行组合静态检查时，前置 `rg` 使用 `apps/marketing` 与 `ui/src/...`，报告路径不存在；由于 `set -e`，ESLint 和类型检查未执行。
- 根因：跨端重复定义检索与必须在 `ui/` 执行的 pnpm 命令再次被放入同一工作目录，复发 ERR-20260912-115。
- 修复：立即停止组合命令；跨端 `rg` 固定从仓库根执行，pnpm 校验固定从 `ui/` 单独执行。
- 验证：仓库根重复定义检索与 `ui/` 内 ESLint、类型检查、构建分别执行并全部通过。
- 关联：ERR-20260912-115。

## [ERR-20260914-126] CUA 隔离执行环境不允许直接赋值元素 scrollTop

- 时间：2026-09-14
- 现象：真实浏览器滚动验收中，通过 CUA `evaluate` 给 `.recommendation-page.scrollTop` 赋值时报该属性只有 getter。
- 根因：CUA 的隔离执行环境把查询到的 DOM 元素包装为受限代理，属性直接赋值不可用；不是页面滚动容器样式故障。
- 修复：改用元素原生 `scrollTo()` 方法触发滚动，再只读获取 `scrollTop/clientHeight/scrollHeight` 判断是否到底。
- 验证：改用 `scrollTo()` 后读取到 `atBottom=true`、`scrollHeight=clientHeight=875`，页面当前无溢出内容且不存在滚动阻断。

## [ERR-20260914-127] 推荐引擎测试检索误用不存在的 tests 目录

- 时间：2026-09-14
- 现象：检索 M07-04 相关测试时对 `apps/marketing/tests` 执行 `rg`，命令返回路径不存在。
- 根因：未先确认该应用的实际测试布局；项目同时使用 `apps/marketing/tests.py` 和 `apps/marketing/test_recommendation_engine.py`，并不存在 `tests/` 目录。
- 修复：先用 `find apps/marketing -maxdepth 3` 定位测试文件，再针对实际文件执行检索和回归。
- 验证：已定位推荐引擎专项测试文件为 `apps/marketing/test_recommendation_engine.py`，后续测试修改与执行固定使用该路径。

## [ERR-20260914-128] 推荐引擎前端 API 文件名猜测错误

- 时间：2026-09-14
- 现象：尝试读取 `ui/src/api/marketing/recommendation.ts` 时文件不存在，导致同一命令块后续页面检查未执行。
- 根因：未先读取前端文件清单，按通用命名猜测了路径；实际文件是 `ui/src/api/marketing/recommendation-engine.ts`。
- 修复：通过 `find ui/src` 定位推荐相关文件，后续使用实际 API 文件路径。
- 验证：已成功读取 `recommendation-engine.ts` 并确认既有精排类型及 API 导出。

## [ERR-20260914-129] 推荐引擎 Vue 页面目录猜测错误

- 时间：2026-09-14
- 现象：尝试读取 `ui/src/views/marketing/recommendation/index.vue` 时文件不存在。
- 根因：继续按常见业务域嵌套结构猜测页面路径，没有先从路由的动态 import 反查组件位置；实际路径是 `ui/src/views/recommendation-engine/index.vue`。
- 修复：读取 `ui/src/router/modules/recommendation-engine.ts` 的组件引用后再定位页面；此类视图文件后续统一先从路由反查。
- 验证：路由明确指向 `@/views/recommendation-engine/index.vue`，并已在该文件检索到召回、精排配置及运行记录区域。

## [ERR-20260914-130] CUA 标签页句柄不提供 waitForLoadState

- 时间：2026-09-14
- 现象：导航到推荐引擎页面后调用 `tab.waitForLoadState(...)`，运行时返回 `tab.waitForLoadState is not a function`。
- 根因：把另一套浏览器自动化接口的等待方法套用到当前 CUA 标签页句柄；当前版本未暴露该方法。
- 修复：导航后直接读取可访问性快照，并使用当前文档提供的元素等待/快照能力确认异步渲染，不再调用 `waitForLoadState`。
- 验证：改用 `tab.playwright.getByRole(...).waitFor(...)` 后成功确认页面标题、X04 标识、增量学习页签和真实验收数据；页面滚动到底且控制台无错误。

## [ERR-20260914-131] 收尾一致性补丁上下文混入手误参数名

- 时间：2026-09-14
- 现象：调整增量训练评估权重时，`apply_patch` 提示找不到预期上下文，整批补丁未应用。
- 根因：补丁上下文手误写入 `workspace_ID_id`，与真实代码 `RecommendationRankingService(self.workspace_id, self.user)` 不一致。
- 修复：先用带行号读取真实代码，将后端权重调整和前端幂等键拆成两个最小补丁。
- 验证：补丁失败时文件未修改；按真实行号拆分后修改成功，后端 19 项测试、Ruff、Django 检查与迁移检查，以及前端 ESLint、类型检查和生产构建全部通过。

## [ERR-20260914-128] 推荐引擎前端 API 文件名判断错误

- 时间：2026-09-14
- 现象：读取前端推荐接口定义时使用了不存在的 `ui/src/api/marketing/recommendation.ts`，`sed` 返回文件不存在。
- 根因：未先读取目录文件清单，凭模块名称猜测文件名，实际文件为 `recommendation-engine.ts`。
- 修复：先用 `find ui/src` 定位 recommendation/marketing 相关文件，再读取和修改真实路径。
- 验证：已定位接口文件 `ui/src/api/marketing/recommendation-engine.ts` 及推荐引擎路由、页面相关文件，后续不再使用猜测路径。

## [ERR-20260914-132] 模型定义检索混入不存在的旧路径

- 时间：2026-09-14
- 现象：检索推荐模型定义时额外传入不存在的 `apps/marketing/models/recommendation.py`，产生无关的 `rg` 路径错误。
- 根因：没有先用文件清单确认模型文件名，把记忆中的候选路径和真实路径混在同一次命令中；实际文件为 `apps/marketing/models/recommendation_engine.py`。
- 修复：后续先执行 `rg --files apps/marketing/models | rg recommendation`，只对返回的真实路径检索。
- 验证：已确认排序运行和反馈模型均位于 `recommendation_engine.py`，后续验收改用该路径。

## [ERR-20260914-133] 错误日志追加补丁使用了过宽上下文

- 时间：2026-09-14
- 现象：首次追加 ERR-132 时以通用分隔线作为补丁上下文，`apply_patch` 无法唯一、准确命中，文件未修改。
- 根因：没有先读取日志末尾真实内容，且该文件现有条目并非统一模板格式。
- 修复：先读取末尾，再以最后一条记录的完整验证行作为精确锚点，一次性追加 ERR-132 与本条记录。
- 验证：两条记录均已成功写入；后续日志追加固定先读取末尾并使用唯一锚点。

## [ERR-20260914-134] zsh 未匹配文档通配符中断检索

- 时间：2026-09-14
- 现象：对 `docs/测试/推荐*` 执行 `rg` 时，zsh 在没有匹配文件的情况下先报 `no matches found`。
- 根因：把未经确认的裸通配符交给 zsh 展开；目标文档文件名尚未创建，且现有推荐验收文档的实际命名未先列出。
- 修复：文档发现统一先用 `rg --files docs/测试 | rg 推荐` 或 `find`，后续检索只传入已确认文件路径。
- 验证：已停止使用该通配符，后续真实数据定位改从数据库和明确源码路径执行。

## [ERR-20260914-135] zsh 将未加引号的查询参数问号当作通配符

- 时间：2026-09-14
- 现象：健康检查循环中的 `...?days=30` 未加引号，zsh 把 `?` 解释成单字符通配符并报 `no matches found`，请求没有发出。
- 根因：ERR-20260914-134 的 shell 展开规则同样适用于 URL 查询字符串，首次修复后没有把规则扩展到所有含 `?`/`&` 的 URL。
- 修复：shell 命令中的完整 URL 使用单引号包裹，再交给循环变量和 `curl`；含查询参数的 URL 一律不得裸写。
- 验证：加引号重跑后，8080 直连与 3000 Vite 代理均返回预期 401，而非 404。
- 关联：ERR-20260914-134。

## [ERR-20260914-136] zsh 健康检查误用只读变量 status

- 时间：2026-09-14
- 现象：修正 URL 引号后，循环赋值 `status=$(...)` 报 `read-only variable: status`，请求检查未完成。
- 根因：`status` 是 zsh 的特殊只读参数，同时也违反项目“脚本变量避免常见系统选项名”的约束。
- 修复：改用任务语义明确且不冲突的 `http_code`，健康检查拆为最小命令执行。
- 验证：改用 `http_code` 后脚本正常执行，两个端点均返回预期 401。

## [ERR-20260914-137] CUA 浏览器请求头策略加载失败

- 时间：2026-09-14
- 现象：`cua.getState()` 能列出桌面应用，但浏览器列表为空并返回 `Unable to load browser request-header policy`。
- 根因：当前统一浏览器控制层未能加载本地请求头策略，属于自动化通道初始化故障，与被测前端页面无关。
- 修复：按工具错误建议只重试一次浏览器状态读取；如仍失败，不循环重试，改用 API、构建和接口连通性证据验收。
- 验证：待单次重试确认。
- 验证：单次重试仍返回相同错误，已停止使用 CUA 并切换到项目约定的 Playwright CLI 隔离验收流程。

## [ERR-20260914-138] 注销路由检索再次混入不存在的项目 URL 路径

- 时间：2026-09-14
- 现象：已从 `apps/users/urls.py` 确认注销路由后，同一检索命令仍附带不存在的 `apps/telecom_ai_agent/urls.py` 并产生路径错误。
- 根因：把不必要的候选根路由文件混入了已有充分证据的检索，复发“先猜路径再检索”问题。
- 修复：停止继续查找候选路径，直接使用 `users/urls.py` 已确认的 `/user/logout`，结合前端 `/admin/api` 基址完成注销。
- 验证：浏览器内注销返回 HTTP 200，隔离会话已关闭，本轮临时快照已精确删除。
- 关联：ERR-20260914-132。

## [ERR-20260914-139] 部署文件检索再次使用未匹配的 zsh 通配符

- 时间：2026-09-14
- 现象：检查运行栈时把 `docker-compose*.yml` 直接作为 zsh 参数，目录中无匹配文件并报 `no matches found`。
- 根因：没有执行已经写入 `AGENTS.md` 的“可选路径先用 `rg --files` 确认”规则，属于 ERR-20260914-134 的再次复发。
- 修复：后续文件发现统一从 `rg --files` 结果中过滤，不再在命令参数中使用可能为空的 shell glob。
- 验证：已改用明确的 `pyproject.toml` 与 `apps/telecom_ai_agent/asgi.py`，确认仓库有 ASGI 入口和 `websockets` 客户端依赖，但没有 Channels/Daphne 服务栈。
- 关联：ERR-20260914-134、ERR-20260914-135。
## ERR-20260914-140：读取前端参考 API 时猜测了不存在的文件名

- 时间：2026-09-14
- 现象：执行 `sed -n` 读取 `ui/src/api/marketing/recommendation.ts` 时返回 `No such file or directory`。
- 根因：未先用 `rg --files` 核对前端 API 的实际目录和命名，直接根据功能名猜测路径。
- 修复：先列出 `ui/src/api/marketing` 及相邻模块的真实文件，再选择结构最接近的实现作为参考。
- 验证：后续文件读取只使用 `rg --files` 返回的明确路径。
## ERR-20260914-141：IVR 页面表格插槽状态映射未收窄类型

- 时间：2026-09-14
- 现象：`pnpm run type-check` 与 `pnpm run build` 在 `ivr-simulator/index.vue` 报 TS7053，模板插槽的 `row.status` 为 `any`，不能直接索引 `Record<IvrSessionStatus, ...>`。
- 根因：Element Plus 表格默认插槽没有把行数据泛型传递给模板类型系统，严格类型检查无法证明状态值是合法联合类型。
- 修复：增加接收未知字符串并提供兜底值的 `getStatusType()`，模板不再直接索引映射。
- 验证：重新执行目标 ESLint、`pnpm run type-check` 和 `pnpm run build`。
## ERR-20260914-142：IVR 新接口探针误加 `/api` 前缀

- 时间：2026-09-14
- 现象：重启后探测 `http://127.0.0.1:8080/api/workspace/.../marketing/ivr/dashboard`，后端直连和 Vite 代理都返回 404。
- 根因：探测前未核对项目根 URL 与 `ui/vite.config.ts`，沿用其他项目常见的 `/api` 前缀。
- 修复：读取真实 URL include 和代理规则，以项目实际路径重新探测。
- 验证：直连后端及前端代理端点均应返回鉴权错误而不是 404。
## ERR-20260914-143：将 Django 根路由误判为单文件 `urls.py`

- 时间：2026-09-14
- 现象：读取 `apps/telecom_ai_agent/urls.py` 返回不存在；检索结果实际显示路由位于 `apps/telecom_ai_agent/urls/web.py`。
- 根因：在已有 `rg` 输出明确给出目录式路由后，仍沿用了 Django 常见单文件结构。
- 修复：只读取检索结果中已确认存在的 `apps/telecom_ai_agent/urls/web.py`。
- 验证：从路由配置确认管理 API 前缀，并使用真实路径重新探测。
## ERR-20260914-144：可选环境键检索无结果导致组合只读命令退出 1

- 时间：2026-09-14
- 现象：路由与 Axios 配置均读取成功，但末尾 `rg -n "VITE_BASE_PATH" ui/env` 无匹配，使整条组合命令退出码为 1。
- 根因：把允许“无结果”的辅助检索与确定性读取放在同一命令调用中，未单独处理 ripgrep 的无匹配语义。
- 修复：后续确定性检查单独执行；可选检索根据需要单独调用，不让它掩盖已成功的核心检查。
- 验证：使用已由 Django 与 Axios 同时确认的 `/admin/api` 路径完成直连和代理探针。
## ERR-20260914-145：M09-01 多文件文档补丁被单一上下文失败整体阻断

- 时间：2026-09-14
- 现象：一次补丁同时创建验收文档并修改计划、排障手册和 `AGENTS.md`，因 `AGENTS.md` 插入点未匹配而整包未落盘。
- 根因：把四类文档更新放入同一个大补丁，重复了 ERR-20260912-105 已记录的编排错误；且对目标段落的顺序假设不准确。
- 修复：确认所有目标均未落盘后，改为每个文件一个最小补丁，并在每步后检索验证。
- 验证：验收文档、计划状态、排障规则和工程规则分别写入并可检索。
- 关联：ERR-20260912-105。

## ERR-20260914-146：工作区角色查询使用了不存在的展示字段

- 时间：2026-09-14
- 现象：准备 M09-02 浏览器验收登录态时，查询 `role__name` 抛出 `FieldError`。
- 根因：未先核对 `Role` 模型字段，沿用了通用的 `name` 命名；本项目实际字段是 `role_name`。
- 修复：将只读查询改为 `role__role_name`，并在后续鉴权辅助脚本中直接使用已验证的关系字段。
- 验证：更正后的查询成功返回该工作区用户及 `工作空间管理员` 角色。

## ERR-20260914-147：M09-02 自动迁移未通过最终格式门禁

- 时间：2026-09-14
- 现象：后端最终门禁在 `ruff format --check` 处停止，提示 `0032_change_operation_risk_confirmation_v1.py` 需要格式化。
- 根因：生成迁移后只检查了业务文件，没有把新迁移纳入首次格式化检查。
- 修复：对迁移执行 Ruff 机械格式化，并从静态检查开始完整重跑后端门禁。
- 验证：Ruff、Django check、`makemigrations --check --dry-run` 及 M09-01～M09-02 共 9 个测试全部通过，重复定义检索结果正常。

## ERR-20260914-148：PDF 依赖探针把可选抽取库与生成依赖合并导入

- 时间：2026-09-14
- 现象：M09-03 开始前使用一条 Python 命令同时导入 `reportlab`、`pypdf` 和 `pdfplumber`，因 `.venv` 未安装 `pdfplumber` 而退出 1。
- 根因：把 PDF 生成、读取和可选文本抽取依赖合并成全有或全无的探针，不能反映本任务实际所需能力。
- 修复：复用仓库已有 ReportLab 中文导出器；使用已存在的 `pdftoppm` 做逐页渲染，不为非必需的 `pdfplumber` 增加依赖。
- 验证：真实 M09-03 PDF 已生成并识别为 PDF 1.4 共 2 页；以 144 DPI 逐页渲染后确认中文、表格、换行、页码和 Asia/Shanghai 生成时间均正常。

## ERR-20260914-149：通信状态加锁查询携带可空用户外连接

- 时间：2026-09-14
- 现象：M09-03 四个专项测试均在发送通信事件时触发 PostgreSQL `FOR UPDATE cannot be applied to the nullable side of an outer join`。
- 根因：`_get_communication(lock=True)` 在 `select_for_update()` 后继续 `select_related("operation", "user")`，其中可空 `user` 形成外连接；重复违反了项目已有的主表独立加锁规则。
- 修复：加锁分支只查询并锁定通信主表，操作、用户等关系在锁定后按需读取；非加锁分支才使用 `select_related()`。
- 验证：修复后 M09-03 四个专项测试全部通过，覆盖通信状态、执行门禁、审计、全局通知、报告和导出。

## ERR-20260914-150：报告导出下拉的模板箭头参数被推断为隐式 any

- 时间：2026-09-14
- 现象：M09-03 前端 `vue-tsc` 在报告列表的 `@command="(format) => ..."` 报 TS7006。
- 根因：Element Plus 下拉命令在 Vue 模板内联箭头中没有为参数提供可收窄类型。
- 修复：改用具名处理函数接收模板 `$event` 和报告 ID，在脚本中显式声明 `ExportFormat`。
- 验证：目标文件 ESLint 和 `pnpm run type-check` 均通过。

## ERR-20260914-151：长验收命令输出截断后终端句柄失效

- 时间：2026-09-14
- 现象：M09-03 API 验收脚本输出大量 SQL，结果被截断；后续读取最终摘要时会话已经结束，返回 `Unknown process id`。
- 根因：验收脚本复用了开启数据库调试输出的环境，且把数据构造、导出和汇总放在同一长会话中，最终结果依赖临时终端句柄。
- 修复：不再重跑可能重复写入的整套脚本，改为分别从数据库和已落盘文件反查结果；后续验收脚本关闭调试 SQL，并把汇总验证拆成短命令。
- 验证：后续分别从数据库确认 4 条变更、6 条通信和 1 份报告，从文件确认 2 页 PDF 与带 BOM CSV，并通过隔离浏览器确认页面和日期下钻，均不依赖原终端句柄。

## ERR-20260914-152：Django Shell 使用了错误的应用包前缀

- 时间：2026-09-14
- 现象：M09-03 汇总反查命令导入 `apps.marketing...` 后，Django 报模型未声明 `app_label` 且不属于 `INSTALLED_APPS`。
- 根因：仓库目录虽然是 `apps/marketing/`，但 Django 应用的 Python 包名是 `marketing`；错误前缀让同一模型模块以另一个命名空间被重复加载。
- 修复：管理命令内统一从 `marketing...` 导入应用代码，不根据文件系统目录补 `apps.` 前缀。
- 验证：从 `marketing.serializers...` 和 `marketing.models...` 导入后成功输出 M09-03 数据库汇总，Django check 与 13 个 M09 回归测试通过。

## ERR-20260914-153：M09-03 汇总脚本猜测了不存在的响应键

- 时间：2026-09-14
- 现象：改正应用导入路径后，汇总脚本访问 `dashboard()["communication_summary"]` 抛出 `KeyError`。
- 根因：未先核对 `ChangeOperationControlService.dashboard()` 的真实返回结构，按记忆猜测了键名。
- 修复：先读取服务实现或只输出顶层键，再按已确认的结构提取验收摘要。
- 验证：按实现中的 `summary`、`communication_counts` 和 `reports` 结构成功读取 4 条变更、6 条通信与 1 份报告。

## ERR-20260914-154：PDF 复查脚本使用 `rm -f` 被安全策略拒绝

- 时间：2026-09-14
- 现象：重新生成并渲染 M09-03 PDF 的组合命令因包含 `rm -f` 被执行工具整体拒绝，命令未开始执行。
- 根因：对已确认存在的临时 PNG 仍使用了强制删除参数，超出了本次清理所需的最小操作。
- 修复：先确认两个精确文件存在，再使用不带 `-f` 的 `/bin/rm` 删除，不使用通配符或目录递归。
- 验证：使用不带强制参数的精确删除后重新生成并渲染两页 PDF，临时 PNG 逐页检查后也已精确删除，临时目录为空并移除。

## ERR-20260914-155：浏览器验收把未创建目录设为进程工作目录

- 时间：2026-09-14
- 现象：Playwright 命令计划先创建 `output/playwright/m09-03`，但同一次调用已经把该路径设为 `workdir`，进程在执行 `mkdir` 前因目录不存在而启动失败。
- 根因：忽略了执行器先解析工作目录、再运行命令的顺序。
- 修复：从已存在的仓库根目录单独创建产物目录，确认存在后再以该目录启动浏览器命令。
- 验证：从仓库根目录创建产物目录后，隔离 Playwright 会话成功完成页面、管控抽屉、报告下钻、截图和控制台验收。

## ERR-20260914-156：Playwright `eval` 传入多语句导致语法错误

- 时间：2026-09-14
- 现象：使用 `eval "const el = ...; ..."` 检查 IVR 长页面滚动时返回 `Unexpected token 'const'`，后续截图和点击因 `set -e` 未执行。
- 根因：当前 Playwright CLI 的 `eval` 参数按 JavaScript 表达式求值，不能直接接收顶层声明和多语句。
- 修复：把滚动与尺寸返回包装为单个立即执行函数表达式，或使用元素引用表达式；保持不用裸 `run-code` 等待。
- 验证：立即执行函数表达式成功返回主页面 `2934/889/3823` 和管控抽屉 `323/842/1165` 的滚动数据，页面均可滚动到底。

## ERR-20260914-157：Vue 模板自动解包导致下载 loading 参数类型错误

- 时间：2026-09-14
- 现象：M10-01 首次执行 `pnpm run type-check` 时，模板中调用 `exportComplaints(..., exporting)` 报布尔值不能赋给 `Ref<boolean>`。
- 根因：Vue 模板会自动解包顶层 `ref`，因此模板表达式中的 `exporting` 已是 `boolean`，与请求方法期望的 `Ref<boolean>` 不一致。
- 修复：新增脚本层 `exportCurrentComplaints()` 包装函数，由脚本作用域把原始 `ref` 传给 API，模板只触发无参函数。
- 验证：修复后重新执行目标 ESLint、全量 `vue-tsc` 与前端构建确认。

## ERR-20260914-158：开发服务器在路由与页面分步创建期间短暂解析失败

- 时间：2026-09-14
- 现象：M10-01 先写入 `rehearsal` 路由、后写入页面文件时，正在运行的 Vite 热更新短暂报告无法解析 `@/views/rehearsal/index.vue`。
- 根因：路由模块与其动态导入目标不是在同一个补丁中落盘，文件创建间隙触发了开发服务器重载。
- 修复：完成页面文件后执行目标 ESLint、全量类型检查和生产构建，并重启 Vite 清除瞬时错误状态。
- 验证：生产构建已能解析预演页面模块；重启后继续以真实页面和控制台验收结果为准。

## ERR-20260914-159：Playwright 技能文档的网络命令与当前 CLI 版本不一致

- 时间：2026-09-14
- 现象：M10-01 浏览器验收执行 `playwright-cli network` 返回 `Unknown command: network`。
- 根因：技能参考文档仍使用旧命令名，而当前安装版本将网络请求列表命令命名为 `requests`，并通过 `request <index>` 查看详情。
- 修复：停止继续猜测子命令，按当前 CLI 输出改用 `requests` / `request`。
- 验证：使用 `requests` 读取实际预演接口 URL，以浏览器真实工作空间为准补充验收数据。

## ERR-20260914-160：M10-01 最终门禁遗漏配置文件机械格式化

- 时间：2026-09-14
- 现象：最终 `ruff format --check` 提示 `settings/base/web.py` 和 `urls/web.py` 需要格式化，后续检查因 `set -e` 未继续。
- 根因：首次只对新 `rehearsal` 应用执行了格式化，修改应用注册和 URL include 后仅执行过 Ruff lint，没有把两个被修改的配置文件纳入 formatter。
- 修复：对这两个配置文件执行 Ruff 机械格式化，并从格式、lint、Django check、迁移检查和专项测试开始完整重跑门禁。
- 验证：12 个目标 Python 文件通过 Ruff format 与 lint；Django check、无缺失迁移检查、5 个专项测试、重复定义检索和 `git diff --check` 全部通过。

## ERR-20260914-161：误判 artifact-tool 包含 README 文件

- 时间：2026-09-14
- 现象：核对工作簿工具包时直接读取包根目录的 `README.md`，命令返回文件不存在。
- 根因：未先根据目录清单和 `package.json` 确认当前打包版本的文档入口，沿用了常见 npm 包目录结构的假设。
- 修复：后续只读取技能已指定的 API 参考，或先列出工具包 `docs/` 与导出入口后再选择实际存在的文件；不再猜测 README 路径。
- 验证：通过 artifact-tool 成功定位 `Sheet1!C21:D21`，确认 X19 原文为“增加处置进度模拟能力 / 增加动态流程模拟引擎”。

## ERR-20260914-162：处置流程测试错误假设异常类型与默认模板顺序

- 时间：2026-09-14
- 现象：M10-02 首次 7 个专项测试出现 1 个错误、1 个失败：重复步骤校验实际抛出 DRF `ValidationError`，API 测试又把首个模板固定假设为 4 步，但排序后的首项是 5 步政企模板。
- 根因：测试断言没有按序列化器的真实异常契约，也把模板集合顺序误当成业务语义。
- 修复：重复步骤用 DRF `ValidationError` 断言；流程步骤数与本次实际选中模板的 `step_count` 对齐，不依赖数组首项对应哪种客户类型。
- 验证：模板步骤数断言已不再依赖顺序；异常类型修复的首个补丁误命中了另一个相邻断言，见 ERR-20260914-163。

## ERR-20260914-163：宽泛补丁误改相邻异常断言

- 时间：2026-09-14
- 现象：修复 ERR-20260914-162 后重跑测试仍有 2 个错误，原有“空实例不能准备”测试被改成期待 `ValidationError`，而目标“重复步骤”测试仍在期待 `AppApiException`。
- 根因：补丁只按重复的 `with self.assertRaises(AppApiException)` 文本匹配，命中了文件中更靠前的断言，没有带测试方法名或上下文定位。
- 修复：使用两个测试方法名作为补丁上下文，分别恢复准备校验的 `AppApiException`，并把重复步骤校验改为 DRF `ValidationError`。
- 验证：精确修复后 7 个 rehearsal 专项测试全部通过，原有准备校验与新增流程模板校验均恢复正确断言。

## ERR-20260914-164：页面热更新关闭抽屉后仍按打开状态检查滚动

- 时间：2026-09-14
- 现象：浏览器验收使用 `.process-drawer .drawer-scroll` 定位流程抽屉滚动容器时返回 `null`；此前快照中抽屉内容曾显示。
- 根因：后端重启和前端热更新后页面已重新加载、抽屉恢复为关闭状态，验收脚本沿用了重载前的 UI 状态；并非 Teleport 丢失样式类。
- 修复：每次重载后先重新打开目标抽屉并获取新快照，再在当前 `[role=dialog]` 内定位 `.drawer-scroll`，不复用旧引用或旧 UI 状态。
- 验证：重新打开流程抽屉后定位到唯一滚动容器，尺寸为 `1503/963`，成功滚动至 `scrollTop=540` 且 `atBottom=true`。

## ERR-20260914-165：宿主浏览器状态读取策略加载失败

- 时间：2026-09-14
- 现象：使用宿主浏览器状态读取能力时返回 `Unable to load browser request-header policy`，未能列出浏览器标签页。
- 根因：宿主统一浏览器控制层未成功加载请求头策略，属于控制通道初始化失败，不是业务页面故障。
- 修复：不重试该控制通道，改用已建立且登录态隔离的 Playwright CLI 会话继续验收。
- 验证：同一页面经 Playwright 正常访问，处置流程列表和详情接口均为 `200`，控制台 `0` 条错误。

## ERR-20260914-166：误把 Playwright CLI 当作全局命令

- 时间：2026-09-14
- 现象：直接执行 `playwright-cli -s=m10-02 snapshot` 返回 `command not found`。
- 根因：当前环境没有全局安装 CLI，项目约定使用技能目录中的包装脚本按需调用 npm 包。
- 修复：使用 `/Users/zhaozhenchao/.codex/skills/playwright/scripts/playwright_cli.sh` 调用原有 `m10-02` 会话。
- 验证：包装脚本成功读取页面快照、执行抽屉和页面滚动、截图，并确认控制台无错误。

## ERR-20260914-167：导出可读性补丁沿用错误的测试样例名称

- 时间：2026-09-14
- 现象：为处置进度 CSV 增加中文当前步骤时，联合补丁因找不到“公众申告处置闭环演练”断言而整体失败。
- 根因：把开发库中的演示流程名称误当成测试夹具名称；测试实际使用“公众申告人工处置演练”。
- 修复：先读取目标测试方法，再以方法名和真实断言为上下文分别修改导出逻辑与测试。
- 验证：补丁成功应用，并通过专项测试和真实 CSV 内容检查。

## ERR-20260914-168：依据截断拼接输出误判源码存在重复行

- 时间：2026-09-14
- 现象：M10-03 首次序列化补丁尝试删除两个相邻的 `event_type_label`，但补丁校验失败。
- 根因：并行读取多个长文件时工具输出被截断和拼接，视觉上出现重复片段；没有先用小范围命令核对实际源码。
- 修复：对目标行号单独读取，以函数和字段上下文精确应用序列化补丁，不再根据截断后的组合输出做删除判断。
- 验证：精确补丁成功加入数据模板、批次和时序点序列化，后续以 Ruff、专项测试和重复定义检索确认。
## ERR-20260914-169：在 Playwright 产物目录执行后端登录态撤销失败

- **现象**：关闭 M10-03 隔离浏览器后，同一命令块中的 `source .env.local` 提示文件不存在，撤销脚本未继续执行。
- **根因**：命令工作目录为 `output/playwright/m10-03/`，却使用了只能从仓库根目录解析的 `.env.local` 和 `apps/manage.py` 相对路径。
- **修复**：从仓库根目录重新执行标准环境加载块，从权限为 `600` 的临时文件读取令牌并按 TOKEN 缓存版本精确删除，随后删除临时文件和空目录。
- **验证**：精确删除后缓存查询为空，临时令牌文件与目录已删除，用户其他会话未清理。

## ERR-20260914-170：以连字符开头的检索模式被误判为命令参数

- **现象**：检索头部样式变量时，`rg` 返回 `unrecognized flag --app-header-height...`。
- **根因**：正则表达式以 CSS 自定义属性的 `--` 开头，命令中未用 `--` 明确结束选项解析。
- **修复**：后续检索此类模式统一使用 `rg -n -- 'pattern' paths...`，避免把检索内容当作参数。
- **验证**：改用选项终止符后可正常读取头部尺寸变量与相关样式位置。

## ERR-20260914-171：按猜测的包产物路径校验图标失败

- **现象**：校验 Element Plus 图标导出时，脚本读取不存在的 `dist/es/index.mjs`，把候选图标全部报告为缺失。
- **根因**：未先查看当前安装版本的包目录结构，直接套用了另一种构建产物路径。
- **修复**：先读取包内 `package.json` 的 exports/module 入口，再从真实入口校验命名导出。
- **验证**：后续候选图标只采用真实入口中存在的导出。

## ERR-20260914-172：Django shell 使用了带项目目录前缀的应用导入

- **现象**：创建导航验收登录态前查询用户时，`from apps.users.models import User` 触发模型未声明 `app_label` 的运行时错误。
- **根因**：`apps/` 是管理命令的项目目录，不是 Django 已注册应用标签；运行时应用路径是 `users`。
- **修复**：Django shell 内统一从已注册应用包导入，例如 `from users.models import User`。
- **验证**：改用注册应用路径后能够正常读取验收用户，且不再重复加载错误模块名。

## ERR-20260915-173：把工作空间字符串误当成独立 Workspace 模型

- **现象**：准备 M10-04 真实验收数据时执行 `from system_manage.models import Workspace`，Django shell 报 `ImportError`。
- **根因**：该项目的工作空间由各业务表 `workspace_id` 字符串和权限映射共同表达，`system_manage.models` 并未导出独立的 `Workspace` 模型；沿用了其他项目的常见数据模型假设。
- **修复**：先从现有业务数据和用户权限映射中读取实际 `workspace_id`，不再导入不存在的聚合模型。
- **验证**：后续验收脚本将使用已存在的 `rehearsal` 业务记录或 `default` 工作空间，并以服务/API 返回结果核对归属。

## ERR-20260915-174：Playwright 命令使用了尚未创建的验收目录

- **现象**：以 `output/playwright/m10-04` 作为工作目录启动命名浏览器会话时，执行器在创建进程前报 `No such file or directory`。
- **根因**：新验收标签的产物目录尚未创建，直接把它传给 `workdir`；浏览器和登录态并未实际启动或加载。
- **修复**：先显式创建确切的 `output/playwright/m10-04` 目录，再按 `open → state-load → goto` 顺序启动验收。
- **验证**：目录创建后需确认命名会话能打开页面，并在加载状态后读取到 X21 页面而非登录页。

## ERR-20260915-175：Playwright CLI `eval` 误用元素回调格式

- **现象**：滚动场景执行抽屉时执行 `eval "el => { ... }" <ref>`，CLI 返回 `SyntaxError: Unexpected token ')'`。
- **根因**：当前项目封装的 Playwright CLI 要求元素回调参数显式写成 `(element) => ...`；省略参数括号的 `el => ...` 在该命令解析链路中失败。
- **修复**：滚动与只读 DOM 检查使用 `(element) => { ... }`，并通过稳定选择器或快照 ref 指定目标元素。
- **验证**：使用 `.drawer-scroll` 与 `.rehearsal-page` 选择器分别滚动到底部，并核对 `atBottom` 为 `true`。

## ERR-20260915-176：Element Plus 隐藏抽屉导致关闭按钮选择器不唯一

- **现象**：用 `.el-drawer__close-btn` 关闭场景详情时，Playwright 严格模式发现 7 个同类按钮并拒绝点击。
- **根因**：页面上的多个 `el-drawer` 关闭后仍保留在 DOM 中，只有一个可见；仅按通用类名无法区分当前抽屉与隐藏抽屉。
- **修复**：浏览器验收统一把抽屉操作限定到当前可见容器，例如 `.el-drawer:visible .el-drawer__close-btn`，或使用可见对话框的无歧义快照 ref。
- **验证**：当前场景抽屉能够唯一关闭，随后主页面滚动和其他抽屉表单检查可继续执行。

## ERR-20260915-177：按猜测时间戳检索 Playwright 快照失败

- **现象**：使用猜测的 `page-<timestamp>-*.yml` 通配符检索快照时，zsh 报 `no matches found`。
- **根因**：CLI 实际生成的文件时间戳与命令输出时间不完全一致，且 zsh 默认会在无匹配通配符时终止命令。
- **修复**：先用 `rg --files .playwright-cli` 获取真实产物路径，再对精确路径检索；不猜测带时间戳的文件名。
- **验证**：能够从最新真实快照中定位“新建剧本”和“创建场景执行”控件。

## ERR-20260915-178：误用 Playwright CLI 网络列表命令

- **现象**：完成 M10-04 控制台检查后执行 `network`，CLI 返回 `Unknown command: network`。
- **根因**：把浏览器能力分类名当成了子命令；当前 CLI 用 `requests` 列出请求，用 `request <index>` 查看单个请求。
- **修复**：先查看 CLI 帮助并改用 `requests`，只在需要时读取目标请求详情。
- **验证**：能够列出页面加载期间的场景剧本、场景执行、工作单等真实接口请求及响应状态。

## ERR-20260915-179：长服务文件多位置组合补丁校验失败

- **现象**：为场景执行同时增加告警计数和详情预取时，一个包含三个远距离目标片段的补丁因 `work_order_count` 上下文不匹配而整体失败。
- **根因**：在持续扩展的长文件中按记忆组合多个远距离上下文，目标字段的实际位置与预估顺序不一致。
- **修复**：先用 `rg` 和小范围 `sed` 定位每个确切片段，再将查询注解、序列化字段和预取关系拆成独立最小补丁。
- **验证**：三个改动分别应用，并通过 Ruff、重复定义检索和专项测试确认。

## ERR-20260915-180：Vue SFC 移动端样式补丁漏逗号导致 SCSS 非法嵌套

- **现象**：告警模拟页面样式扩展后，移动端媒体查询出现 `.work-order-create { .alert-template-rail...` 结构，前端编译报错。
- **根因**：向一组逗号分隔选择器追加告警相关选择器时，把原本应保留的逗号改成了 `{` 前的结尾，形成非法嵌套。
- **修复**：把 `.work-order-create` 恢复为逗号分隔项，让 `.alert-template-rail`、`.alert-template-base-grid`、`.alert-create-grid`、`.alert-facts`、`.alert-operate-grid` 共用同一 `grid-template-columns: 1fr` 规则。
- **验证**：目标文件 ESLint、`pnpm run type-check` 和 `pnpm run build` 均已通过。

## ERR-20260915-181：URL 检索命令混入不存在文件路径

- **现象**：核对预演路由时执行 `rg` 同时传入 `apps/telecom_ai_agent/urls.py`，命令以退出码 2 结束。
- **根因**：该项目 URL 模块位于 `apps/telecom_ai_agent/urls/` 目录下，没有同名 `urls.py` 文件；把常见 Django 路径假设混入了精确检索。
- **修复**：后续只检索实际存在的 `apps/telecom_ai_agent/urls/web.py`、`apps/telecom_ai_agent/urls/model.py` 与目标 app 的 `urls.py`。
- **验证**：真实路由已确认挂载在 admin API 前缀下，直连带 workspace 的接口返回 401 而非 404，说明 URL 生效。

## ERR-20260915-182：把运行时导入包路径当成仓库根路径读取

- **现象**：准备 APIClient 验收时执行 `sed common/auth/authentication.py` 和 `sed common/auth/__init__.py`，均返回文件不存在。
- **根因**：Django 的 `common.auth` 是 `apps/common/auth/` 下的运行时包，不能省略 `apps/` 项目目录前缀读取源码。
- **修复**：改为参考现有测试中的 `force_authenticate` 写法，后续读取源码使用 `apps/common/auth/...`。
- **验证**：DRF APIClient 注入 `WORKSPACE_MANAGE:/WORKSPACE/<workspace_id>` 后，dashboard、alert list、timeline 三个接口均返回 200。

## ERR-20260915-183：API 验收脚本误判 dashboard.alerts 返回结构

- **现象**：用 DRF APIClient 验收 M10-05 接口时，dashboard 请求成功并返回告警模板，但脚本执行 `data.get('alerts', {}).get('items', [])` 抛出 `AttributeError: 'list' object has no attribute 'get'`。
- **根因**：dashboard 中的 `alerts` 是首页摘要列表，不是分页对象；把 `list_alerts()` 的分页返回结构套到了 dashboard 摘要字段。
- **修复**：验收脚本区分 dashboard 摘要列表和 `/alert` 分页接口，dashboard 使用 `len(data.get('alerts', []))`。
- **验证**：重跑 dashboard、alert list、timeline 三个真实接口通过；dashboard 告警摘要按列表读取，`/alert` 分页接口按 `items` 读取。

## ERR-20260915-184：临时 Playwright 登录态脚本导错 AuthenticationType

- **现象**：生成 M10-05 浏览器验收 storage state 时，脚本执行 `from application.models import AuthenticationType` 抛出 `ImportError`。
- **根因**：系统用户 token 使用的枚举定义在 `common.constants.authentication_type.AuthenticationType`，不是 `application.models`；沿用了聊天/应用模型附近的错误记忆。
- **修复**：改从 `common.constants.authentication_type` 导入，并确认失败发生在 state 文件写入前。
- **验证**：临时 state 生成成功；浏览器验收结束后已从 Django cache 撤销 token，并删除 `storage-state.json`。

## ERR-20260915-185：Playwright CLI screenshot 参数被误当选择器

- **现象**：执行 `screenshot /Users/.../m10-05-alert-drawer.png` 时，CLI 报 `Unexpected token "" while parsing css selector`。
- **根因**：当前 Playwright CLI 的 `screenshot [target]` 参数用于元素目标，不是输出文件路径；传入绝对路径会被当作 CSS selector。
- **修复**：改用无参 `screenshot` 让 CLI 自动保存截图，或先查看该 CLI 是否提供单独的输出选项。
- **验证**：无参截图成功生成 `output/playwright/m10-05/.playwright-cli/page-2026-09-15T03-08-35-115Z.png`。

## ERR-20260915-186：用 rg --files 检索隐藏 Playwright 产物目录漏匹配

- **现象**：确认 M10-05 验收截图和临时 state 文件时，`rg --files output/playwright/m10-05 .playwright-cli | rg ...` 返回 1。
- **根因**：Playwright CLI 将截图保存到隐藏目录 `.playwright-cli/` 下，`rg --files` 默认不列出隐藏目录内容；同时临时 `storage-state.json` 已删除，没有匹配项。
- **修复**：对隐藏验收产物改用显式 `find output/playwright/m10-05 -path '*/.playwright-cli/*'` 或给 `rg --files` 加隐藏文件选项。
- **验证**：`find` 已确认截图文件存在，`test ! -f output/playwright/m10-05/storage-state.json` 已确认临时 state 删除。

## ERR-20260915-187：计划与验收文档组合补丁因表格行上下文不匹配失败

- **现象**：一次性更新实施计划、排障手册并新增 M10-05 验收文档时，补丁在“故障与场景预演”表格行处校验失败。
- **根因**：补丁上下文遗漏了 Markdown 表格行开头的 `|`，导致第一处目标无法匹配，整包未落盘。
- **修复**：停止组合大补丁，改为按计划、排障手册、验收文档分别应用最小补丁。
- **验证**：实施计划、排障手册和 `docs/测试/告警模拟与时序同步M10-05验收文档.md` 已分别更新，并用 `rg`/`test -f` 确认落盘。

## ERR-20260915-188：读取技能文件时把别名当成真实路径段

- **现象**：尝试读取 `r0/vue/SKILL.md`、`r0/vue-best-practices/SKILL.md`、`r0/pnpm/SKILL.md` 时，命令返回 `No such file or directory`。
- **根因**：技能清单里的 `r0` 是 `/Users/zhaozhenchao/.codex/skills` 的路径别名，不是该目录下的子目录名。
- **修复**：按技能根映射展开为 `/Users/zhaozhenchao/.codex/skills/<skill>/SKILL.md`，并成功读取相关技能说明。
- **验证**：`vue`、`vue-best-practices`、`pnpm` 与 `self-improvement` 技能文件已按正确路径读取。

## ERR-20260915-189：追加错误日志时复用尾部上下文匹配失败

- **现象**：追加 ERR-188 时，补丁提示无法找到预期的尾部验证行。
- **根因**：补丁上下文使用了与文件实际内容不完全一致的片段；长日志文件追加时依赖过长上下文容易失败。
- **修复**：重新读取文件尾部，使用最小精确上下文追加新记录。
- **验证**：ERR-188 与 ERR-189 已追加到 `.learnings/ERRORS.md`。

## ERR-20260915-190：前端 imports 补丁按预估顺序匹配失败

- **现象**：给 `ui/src/views/rehearsal/index.vue` 增加数据模型类型 imports 时，补丁提示无法找到 `DataDistribution` 后的预期上下文。
- **根因**：当前 imports 实际顺序与按记忆预估的顺序不同，直接组合多行上下文导致匹配失败。
- **修复**：先读取 imports 小范围真实内容，再用精确邻近行补丁插入类型。
- **验证**：数据模型相关类型 imports 已成功加入页面文件。

## ERR-20260915-191：移动端媒体查询补丁混用预估列表导致匹配失败

- **现象**：为数据模型模块补响应式样式时，组合补丁在 `.process-template-rail` 附近提示上下文不匹配。
- **根因**：媒体查询中的选择器列表比预估多，且目标 `simulation-template-rail` 位于另一个列表，不能跨列表一次性插入。
- **修复**：重新读取完整媒体查询，分别替换 `seven-steps` 为 `eight-steps`，并在真实选择器列表中追加数据模型布局类。
- **验证**：`model-filter-bar`、`model-flow-strip`、`source-count-grid`、`data-model-form-grid` 已接入窄屏规则。

## ERR-20260915-192：APIClient 验收脚本误用 Django 默认用户模型

- **现象**：用 `get_user_model()` 生成 APIClient 验收用户时，脚本报 `AUTH_USER_MODEL refers to model 'auth.User' that has not been installed`。
- **根因**：当前项目未安装 Django 默认 `auth` app，既有测试是通过项目夹具里的用户对象配合 `force_authenticate()` 注入工作区权限，不能临时假设存在 `auth.User`。
- **修复**：后续 API 快速验收改用项目已有测试夹具/项目用户模型写法，或直接复用 `apps/rehearsal/tests.py` 中的 `SimpleNamespace(role_list, permission_list)` 认证上下文。
- **验证**：改用 `users.models.User` 和 `SimpleNamespace(role_list, permission_list)` 后，X23 数据模型列表与详情接口均返回 200。

## ERR-20260915-193：临时浏览器登录态脚本导错 CONFIG

- **现象**：生成 Playwright storage state 时执行 `from common.config import CONFIG` 抛出 `ImportError`。
- **根因**：项目运行时代码中的 `CONFIG` 定义在 `telecom_ai_agent.const`，`common.config` 是配置子包，不导出该对象。
- **修复**：按 `apps/users/serializers/login.py` 和 `apps/common/auth/handle/impl/user_token.py` 的真实导入方式，改为 `from telecom_ai_agent.const import CONFIG`。
- **验证**：改用正确导入路径后，Playwright storage state 生成成功；浏览器验收结束后已按 TOKEN 缓存版本撤销令牌并删除 state 文件。

## ERR-20260915-194：在尚未存在的 Playwright 产物目录中启动命令

- **现象**：尝试在 `output/playwright/m10-06` 作为 `workdir` 的同一条命令里执行 `mkdir -p output/playwright/m10-06`，工具直接报 `No such file or directory`，命令没有启动。
- **根因**：`workdir` 必须在进程创建前已经存在，不能依赖命令体里的 `mkdir` 创建当前工作目录。
- **修复**：先从仓库根目录创建验收产物目录，再把后续 Playwright 命令的工作目录切到该目录。
- **验证**：`output/playwright/m10-06` 已创建，后续浏览器命令可从该目录运行。

## ERR-20260915-195：按记忆补模型枚举导致上下文不匹配

- **现象**：给 `apps/rehearsal/models.py` 追加 X24 场景库模型时，补丁在 `SceneRunAction` 枚举处失败。
- **根因**：预估的中文标签与源码实际 `SKIP_STEP = "跳过当前步骤"` 不一致，导致整段上下文无法匹配。
- **修复**：先读取精确上下文，再拆成小补丁插入枚举、模型和字段。
- **验证**：后续以实际源码上下文完成 X24 模型、迁移、服务、API 和测试修改；`py_compile`、`ruff check apps/rehearsal`、`manage.py test rehearsal --keepdb --noinput` 均已通过。

## ERR-20260915-196：场景库克隆继承默认实例导致测试断言偏小

- **现象**：新增 X24 场景库服务/API 回归时，实例详情里的 `scene_library_count` 和 `scene_libraries` 长度实际为 2，但测试断言为 1。
- **根因**：`clone_scene_library()` 设计上会继承源场景库的默认实例、流程模板和数据模型；因此同一实例详情会同时展示原库与克隆版本，这不是重复数据。
- **修复**：把测试断言调整为 2，并保留克隆版本可见性，避免误删继承绑定。
- **验证**：重新执行 `./.venv/bin/python apps/manage.py test rehearsal --keepdb --noinput`，19 个 rehearsal 测试全部通过。

## ERR-20260915-197：清理 Playwright 临时登录态时使用 rm -f 被安全策略拦截

- **现象**：撤销 X24 浏览器验收登录态后，组合命令里使用 `rm -f output/playwright/m10-07/storage-state.json` 删除临时 state 文件，工具直接拒绝执行。
- **根因**：当前执行环境会拦截 `rm -f` 风格命令；即使目标是明确文件，也不应依赖强制删除参数。
- **修复**：后续清理临时验收文件改用精确存在性检查后执行 `unlink <明确文件>`，并把 token 撤销、文件删除、浏览器关闭拆成可验证的小步骤。
- **验证**：已用 `unlink` 删除临时 state 文件，并通过 `test ! -e output/playwright/m10-07/storage-state.json` 确认；Playwright 会话已关闭。

## ERR-20260915-198：回溯模块组合补丁依赖宽泛上下文导致匹配失败

- **现象**：为 dashboard 摘要和实例时间线一次性补充 X25 回溯字段时，补丁提示无法找到预期上下文。
- **根因**：大文件中存在相似的查询与返回片段，组合补丁依赖了按记忆推断的宽泛邻近行，源码在上一轮修改后已发生偏移。
- **修复**：先用 `rg` 和小范围 `sed` 锁定真实位置，再按 dashboard、时间线和服务方法分别应用最小补丁；完成后检查关键类和方法是否重复。
- **验证**：关键字段和方法已分别落盘，后续继续通过静态检查与回归测试确认完整性。

## ERR-20260915-199：X25 浏览器验收遇到旧后端路由与临时用户权限不一致

- **现象**：真实浏览器首次打开预演页后，新增 `/traceback` 接口返回 404，其余预演接口对临时验收用户返回 403，页面被错误处理逻辑带到 404。
- **根因**：本地后端以 `--noreload` 运行，新增 URL 后尚未重启；同时沿用的 `codex_x23_validator` 仅有用户表角色字段，没有默认工作空间的真实角色映射，浏览器 TokenAuth 无法获得所需权限。
- **修复**：重启后端以加载新 URL；浏览器临时登录态改用具有真实工作空间角色映射的现有管理员，验收后精确撤销令牌并删除状态文件。
- **验证**：后端重启后新增回溯接口与其余预演接口均返回 200；使用具有真实工作空间角色映射的管理员完成页面验收，控制台 0 个 error，临时令牌和状态文件已在验收后撤销清理。

## ERR-20260915-200：Playwright CLI run-code 不接受裸 await 语句

- **现象**：使用 `run-code "await page.getByRole(...).click()"` 打开 X25 回溯详情时返回 `SyntaxError: Unexpected identifier 'page'`。
- **根因**：当前安装的 Playwright CLI 将 `run-code` 参数解析为可调用函数表达式，和技能示例中的裸 `await page...` 写法不一致。
- **修复**：优先从新快照取得稳定元素引用并使用 `click <ref>`；确需 `run-code` 时先查看当前 CLI 帮助并传入其要求的函数表达式。
- **验证**：重新快照取得稳定引用 `f1e846` 后使用 `click f1e846` 成功打开详情抽屉，并完成抽屉滚动到底、节点对比、指标差值和不可变时间线验收。

## ERR-20260915-201：后端启动后立即探测产生短暂连接拒绝

- **现象**：启动 Django 本地服务后立即执行一次 `curl` 就出现 `Connection refused`，但服务进程随后正常完成初始化并开始监听 8080。
- **根因**：应用启动期间还在加载词典、应用目录和 Django 配置；启动命令返回运行会话不代表 HTTP 端口已经就绪，单次即时探测存在启动竞态。
- **修复**：启动后先读取服务会话直到出现监听日志，或对健康/真实业务端点做有上限的短间隔重试；不得根据第一次连接失败直接判定服务离线。
- **验证**：服务完成初始化后，X25 dashboard、列表、详情和导出接口均返回 200，真实浏览器页面正常加载且控制台 0 个 error。

## ERR-20260915-202：X26 关键字查询测试遗漏所属实例匹配口径

- **现象**：X26 API 专项测试预期关键字 `X26` 只返回一条实例记录，实际返回实例及其申告批次两条记录。
- **根因**：统一记录查询按设计同时检索记录编号、名称、结果摘要和所属实例编号/名称；申告批次虽然自身名称不含 `X26`，其所属实例名称包含该关键字。
- **修复**：保留对所属实例字段的检索能力，将测试断言改为同时校验 `INSTANCE` 与 `COMPLAINT_BATCH` 两类记录。
- **验证**：修正后 X26 服务层与 API 两项专项测试通过，`rehearsal` 全量 23 项回归测试通过。

## ERR-20260915-203：macOS 临时状态文件清理误用 `/usr/bin/unlink`

- **现象**：X26 浏览器验收令牌已从缓存精确撤销，但随后执行 `/usr/bin/unlink` 报 `no such file or directory`，状态文件未在该命令块中删除。
- **根因**：预设了 Linux 风格的可执行文件位置，没有先核对当前 macOS 环境中 `unlink` 的实际路径。
- **修复**：先使用 `command -v unlink` 解析系统命令位置，再对已确认的单个绝对路径执行 `unlink`；不使用递归删除或目录通配符。
- **验证**：`command -v unlink` 返回 `/bin/unlink`；使用该路径精确删除后，`test ! -e` 已确认状态文件不存在。

## ERR-20260915-204：X27 代码盘点使用不存在的裸通配符

- **现象**：同时扫描 `apps/rehearsal/models.py` 与 `apps/rehearsal/models/*.py` 时，后一个路径没有匹配文件，zsh 在命令执行前报 `no matches found`。
- **根因**：没有先确认 `rehearsal` 是单文件模型结构，直接传入了可能为空的裸通配符。
- **修复**：先用 `rg --files apps/rehearsal` 确认文件结构，再对已存在的明确路径执行检索。
- **验证**：`rg --files apps/rehearsal` 已确认模型位于单文件 `apps/rehearsal/models.py`，随后针对明确路径完成模型、服务、路由与测试结构盘点。

## ERR-20260915-205：X27 服务层专项测试命令使用基础 Fixture 类名

- **现象**：测试加载器报告 `RehearsalFixture` 没有 `test_capability_mock_invoke_history_replay_and_warroom` 方法；同一命令中的 API 专项测试正常执行。
- **根因**：测试方法定义在 `RehearsalServiceTests`，编排命令误把公共数据夹具 `RehearsalFixture` 当成了测试类。
- **修复**：先用 `rg` 确认测试类定义，再以 `rehearsal.tests.RehearsalServiceTests...` 的完整名称重跑。
- **验证**：使用 `RehearsalServiceTests` 与 `RehearsalApiTests` 的正确完整名称后，两条 X27 专项测试均通过。

## ERR-20260915-206：X27 前端辅助函数补丁上下文不完整

- **现象**：为状态标签新增函数时，`apply_patch` 报找不到预期的 `return types[state]` 片段。
- **根因**：现有 `simulationRecordTagType` 直接返回对象索引，没有局部 `types` 变量，补丁上下文来自错误记忆。
- **修复**：先读取目标函数的精确行，再以完整函数结尾作为锚点追加新函数。
- **验证**：按精确函数片段追加后补丁成功，目标文件 ESLint 与 Vue 类型检查均通过。

## ERR-20260915-207：前后端并行启动期间 Vite 首次代理请求被拒绝

- **现象**：Vite 已先就绪，页面随即向后端代理发出请求；Django 尚在初始化，Vite 记录一次连接 `127.0.0.1:8080` 被拒绝。日志中的查询参数已脱敏，不在文档保存临时凭证。
- **根因**：两个服务并行启动时前端就绪更快，已有页面自动请求形成短暂启动竞态。
- **修复**：等待 Django 明确输出监听日志后，再分别探测 8080 直连路由与 3000 代理路由；不把单次启动期拒绝判定为持续故障。
- **验证**：Django 就绪后，8080 直连与 3000 Vite 代理的 X27 路由均返回预期的未认证 401，确认路由存在且代理已恢复。
- **关联**：ERR-20260915-201。

## ERR-20260915-208：X28 视图补丁使用了不一致的格式锚点

- **现象**：在能力调用视图后批量插入 X28 接口类时，`apply_patch` 提示找不到预期上下文，补丁未写入文件。
- **根因**：预估的 `CapabilityCallReplay` 返回语句采用多行格式，而源码实际格式不同；大段补丁依赖了未经核对的尾部锚点。
- **修复**：先用 `rg` 和小范围 `sed` 读取 `CapabilityCallReplay` 与 `SceneScript` 之间的精确源码，再以类声明为最小稳定锚点插入。
- **验证**：按精确锚点写入 6 个 X28 视图后，`py_compile`、Ruff、Django check 和 2 项专项测试均通过。

## ERR-20260915-209：X28 实例事件编码超过字段长度

- **现象**：执行 `makemigrations rehearsal` 时 Django `fields.E009` 报告 `RehearsalInstanceEvent.event_type` 的 24 字符字段无法容纳 27 字符的新选项。
- **根因**：新增内部值 `FAULT_CONFIGURATION_APPLIED` 时只核对了中文展示语义，没有同步核对既有 `event_type.max_length`。
- **修复**：将数据库内部事件值缩短为 `FAULT_CONFIG_APPLIED`，中文标签仍保持“应用故障模拟配置”，不扩大既有字段和索引宽度。
- **验证**：缩短内部事件值后 Django check 通过，`0010` 迁移成功生成并应用，2 项 X28 专项测试通过。

## ERR-20260915-210：验收脚本误用 Django 标准用户模型入口

- **现象**：X28 API 验收脚本调用 `django.contrib.auth.get_user_model()` 时报告 `AUTH_USER_MODEL` 指向未安装的 `auth.User`。
- **根因**：本项目采用独立注册的 `users` 应用但未启用 Django 标准 `auth` 应用，通用用户模型入口与项目注册方式不匹配。
- **修复**：验收脚本按已注册应用标签改为从 `users.models` 导入项目用户模型，不使用 `apps.users` 或标准 `auth.User`。
- **验证**：改用 `users.models.User` 后验收通过：共 3 个配置版本（2 个可应用、1 个待校验），待校验版本准确返回 5 个问题，V2 配置成功保存到实例快照并生成 3 条配置审计事件。

## ERR-20260915-211：Playwright CLI eval 不接受分号分隔的多语句

- **现象**：X28 页面验收用一条 `eval` 同时执行 `scrollIntoView()` 和返回尺寸对象时，CLI 报 `SyntaxError: Unexpected token ';'`。
- **根因**：当前 Playwright CLI 的 `eval` 参数按单个 JavaScript 表达式解析，分号分隔的语句块不是合法输入。
- **修复**：改用逗号表达式或单个自执行表达式返回结果；页面局部快照直接使用 `snapshot <unique-selector>`，不需要用脚本点击。
- **验证**：单表达式成功把 X28 面板滚动到视口顶部，局部快照完整显示 3 个配置版本、拓扑矩阵和操作区；详情抽屉滚动至 `858.5/858`，新建抽屉滚动至 `422.5/422`，页面主容器滚动至底部并确认“模拟申告数据”可见。

## ERR-20260915-212：向量模型诊断猜测了不存在的模型文件路径

- **现象**：最终服务探针读取 `apps/models_provider/models/model.py` 时 `sed` 报文件不存在。
- **根因**：按常见单文件结构猜测了模型定义路径，没有先通过 `rg --files` 确认当前 `models_provider` 的实际模块结构。
- **修复**：不再依赖模型源码猜测，改用已确认存在的 `models_provider.tools.get_model_by_id()` 和数据库中的真实向量模型 UUID执行 `embed_query()`。
- **验证**：使用真实模型加载入口调用成功，`telecom-ai-embedding` 返回 384 维数值向量，未输出凭证。

## ERR-20260915-213：默认本地向量模型端点返回非 JSON 响应

- **现象**：通过数据库中的默认 EMBEDDING 模型实例执行 `embed_query()` 时，在本地 Web embedding 实现的 `res.json()` 处抛出 `JSONDecodeError`。
- **根因**：Ollama 11434 在线不代表数据库默认向量模型在线；该模型实际走独立的本地 Web 向量端点，当前响应不是预期 JSON，需要继续核对配置端口、真实路径和对应服务进程。
- **修复**：按模型 UUID 解析本地向量服务配置（不输出凭证），检查监听端口和真实 embedding 路由，启动或纠正服务后再调用同一模型实例。
- **验证**：启动独立本地模型服务后，同一数据库模型的 `embed_query()` 返回 384 维非空数值向量；证明故障来自 11636 服务未启动，而不是 Ollama 或模型配置本身。

## ERR-20260915-214：本地向量服务诊断再次使用了无匹配裸通配符

- **现象**：检索 compose 配置时把 `docker-compose*.yml` 直接交给 zsh，仓库根目录无匹配文件并报 `no matches found`。
- **根因**：没有遵守先用 `rg --files`/`find` 确认可选路径的项目规则，重复使用了可能为空的裸通配符。
- **修复**：先列出真实 compose/config 文件，再把明确路径交给 `rg`；环境配置只提取 `LOCAL_MODEL_HOST/PORT/PROTOCOL` 等非凭证字段。
- **验证**：从 `apps/telecom_ai_agent/conf.py` 确认真实端口为 11636，从 `scripts/start-local.sh` 确认启动入口；服务启动后实际向量调用通过。

## ERR-20260915-215：端口拒绝后诊断脚本仍检查未生成响应文件

- **现象**：11636 连接被拒绝后，后续 `file`/`wc` 仍检查 curl 原计划生成的临时响应文件，产生额外“文件不存在”错误。
- **根因**：诊断步骤存在先后依赖却没有用 `set -e` 或按 curl 结果分支，失败后的文件检查没有意义。
- **修复**：确认端口无监听后停止依赖响应体的检查；后续启动服务、端口探针和真实 `embed_query()` 按顺序执行，任一步失败即停止。
- **验证**：按“启动服务 → 确认监听日志 → 实际模型调用”顺序完成，11636 正常监听，默认模型返回 384 维数值向量。

## ERR-20260915-216：X29 首次检索混入不存在的计划文档路径

- **现象**：检索 X25/X28 现有实现时，`rg` 报告 `docs/版本建设计划.md` 不存在，整条检索返回非零。
- **根因**：沿用概括性文件名直接拼接命令，没有先从 `docs/` 文件清单确认本仓库的真实计划文件名。
- **修复**：先用 `rg --files docs | rg '计划|规划|建设|版本'` 定位真实文件，确认计划为 `docs/建设方案全量粗粒度V1实施计划.md`；后续只使用已确认的明确路径。
- **验证**：文件清单成功返回计划和相关建设文档，后续 X29 检索改用真实路径执行。

## ERR-20260915-217：X29 大段样式补丁使用了错误的工作流网格值

- **现象**：插入 X29 控制台样式时，`apply_patch` 因找不到预期的 `.workflow-steps.twelve-steps` 六列规则而整体拒绝补丁。
- **根因**：模板已按 13 步调整，但样式锚点仍按推测的六列值编写；源码实际是 12 列，且大段补丁把工作流类替换和 X29 新样式绑定在一次操作中。
- **修复**：先读取工作流与故障配置样式的精确片段，将类名替换和新样式追加拆分为独立小补丁。
- **验证**：后续补丁分别命中真实 `.workflow-steps.twelve-steps` 规则和 `.fault-audit-list p` 锚点，前端样式写入后通过 ESLint、类型检查和构建。

## ERR-20260915-218：X29 API 验收单行脚本的 f-string 引号冲突

- **现象**：Django shell API 验收脚本在 `instance["id"]` 所在 f-string 处报 `SyntaxError: unmatched '['`，脚本在首个写请求前终止。
- **根因**：把多步骤 API 编排压缩到 shell 的 ANSI 引号参数中，外层 f-string 和字典索引使用了相同双引号；组合命令过长，静态可读性不足。
- **修复**：停止继续修改长单行命令，改用 `apply_patch` 创建可静态检查的最小临时验收脚本，执行前先 `py_compile`，验收后精确删除该脚本。
- **验证**：修正后的 API 验收成功生成 1 个 X29 镜像、3 个流量帧和 64 位 SHA-256 校验和，列表节点筛选和详情读取均通过。

## ERR-20260915-219：X29 抽屉快照使用了过宽的 dialog 选择器

- **现象**：点击“查看完整证据”已打开 X29 详情抽屉，但 `snapshot "[role=dialog]"` 因页面中 30 个已挂载弹层同时匹配而触发 Playwright strict mode violation。
- **根因**：Element Plus 会预挂载多个隐藏弹层，通用角色选择器无法唯一定位当前可见的 X29 抽屉。
- **修复**：页面状态变化后重新取快照，使用业务唯一类 `.scene-replay-detail-drawer` 与 `.scene-replay-create-drawer` 定位，不复用通用角色选择器。
- **验证**：唯一类选择器成功读取 X29 详情和新建抽屉，并分别将内部 `.drawer-scroll` 滚动到实际底部。

## ERR-20260917-220：X30 统一记录组合补丁混入过期上下文

- **现象**：同时补充场景回放重复键清理、故障上报统一记录状态、记录投影和详情分支时，`apply_patch` 在场景回放汇总片段校验失败，整批补丁未写入。
- **根因**：检查输出曾显示重复 `ready` 行，但文件当前内容已经变化；把独立改动绑定到同一组合补丁，导致过期片段阻断其余有效修改。
- **修复**：重新读取每个目标区域的精确上下文，按状态映射、记录投影和详情分支拆成最小补丁；不再把顺手清理与核心功能绑定。
- **验证**：拆分补丁后已通过 `py_compile`、关键定义检查、X30 专项测试及预演模块 31 个全量测试。

## ERR-20260917-221：X30 页面验收前联调服务已退出

- **现象**：验收前检查 `8080`、`3000` 与 `11636`，Django、Vite 和向量服务均无监听；Ollama `11434/api/tags` 正常。
- **根因**：前序联调进程并非持久守护进程，在长时间开发与命令会话切换后已经退出；不能沿用旧 PID 或旧会话状态判断服务仍在线。
- **修复**：重新读取当前端口与启动配置，分别启动 Django `--noreload`、Vite 和向量服务；不使用宽泛进程终止命令。
- **验证**：`8080`、`3000`、`11636` 均已监听；Django 直连、Vite 代理与管理端页面均返回 200，向量模型真实 `embed_query()` 返回 384 维非零向量。

## ERR-20260917-222：zsh 可选 Docker 路径裸通配符导致检索提前失败

- **现象**：检索向量服务启动说明时把 `docker-compose*` 直接作为 `rg` 路径参数，zsh 在仓库中无匹配文件并报 `no matches found`，导致同一条检索命令未完整执行。
- **根因**：没有先确认可选文件是否存在，违反了项目关于 zsh 裸通配符的既有约束。
- **修复**：先用 `rg --files` 枚举实际文件，再对明确路径或全仓库执行检索；不再把可能无匹配的 glob 交给 zsh 展开。
- **验证**：后续启动定位使用 `rg --files | rg` 与明确的 `scripts/start-local.sh` 路径完成。

## ERR-20260917-223：并行启动时 Vite 在 Django 就绪前触发一次代理拒绝

- **现象**：前端、后端和向量服务并行启动期间，Vite 已先监听并收到页面遗留的 `/chat/api/profile` 请求，此时 Django 尚未完成系统初始化，产生一次 `ECONNREFUSED 127.0.0.1:8080`；随后 Django 正常监听。
- **根因**：三个服务就绪时间不同，并行启动只代表进程已创建，不代表依赖端口已经可以接收请求。
- **修复**：启动后增加独立就绪探针，按后端直连、Vite 代理、向量真实端点顺序验证，不以启动命令返回会话号作为就绪依据。
- **验证**：后端直连、Vite 代理、管理端页面及向量真实端点四项探针均已通过；启动过程中本地向量应用还提示存在未生成迁移，作为既有技术债保留，不在 X30 范围内擅自生成迁移。

## ERR-20260917-224：X30 阶段条误读快照中不存在的顺序字段

- **现象**：真实截图中四个阶段的序号显示为 `undefined`，阶段名称、责任角色和时限正常。
- **根因**：模板创建请求与持久化快照按数组顺序保存阶段，`sequence_no` 只在模板序列化输出中补充；故障上报的 `template_snapshot.stage_definitions` 保留原始结构。前端错误地假设快照项也始终包含 `sequence_no`。
- **修复**：模板轨道、塔台阶段线、创建预览和详情阶段线统一使用 Vue 循环索引 `index + 1` 作为展示及完成态判断，不依赖可选序号字段。
- **验证**：目标 ESLint、类型检查和生产构建全部通过；真实页面四个阶段显示为 `01`～`04`，塔台文本不再包含 `undefined`，控制台 0 error。

## ERR-225：DRF 下载接口使用 `format` 查询参数导致请求在视图前返回 404

- 时间：2026-09-17
- 场景：M10-14 / X31 辅助模拟 PDF、Excel、JSON 下载接口验收。
- 现象：辅助模拟创建、列表和详情均正常，但 `?format=pdf`、`?format=xlsx` 下载请求返回 404，业务视图未执行。
- 根因：Django REST Framework 默认将 `format` 作为 URL format override 参数；`pdf`、`xlsx` 不是当前 API renderer，DRF 在进入视图前完成内容协商并返回 404。
- 修复：业务导出参数改名为 `export_format`，保留 `report_level=summary|full`。
- 验证：下载接口定向测试与 rehearsal 33 项全量回归通过；真实 PDF、Excel、JSON 已生成并分别完成四页渲染、工作表解析和 JSON 反序列化检查。
- 复用规则：DRF 接口的业务查询参数避免使用框架保留的 `format`；文件格式选择统一使用 `export_format`。

## ERR-226：X31 前端首次类型检查未兼容项目 ES target 与新增联合类型

- 时间：2026-09-17
- 场景：M10-14 / X31 辅助模拟 Vue 页面类型检查。
- 现象：`vue-tsc` 报 `String.replaceAll` 不存在，以及 `SimulationRecordKind` 新增 `AUXILIARY_SIMULATION` 后展示码映射缺少对应键。
- 根因：项目 TypeScript lib 目标低于 ES2021，不能直接使用 `replaceAll`；扩展联合类型时遗漏同步穷尽映射。
- 修复：使用 `split().join()` 兼容当前目标，并为统一模拟记录展示码补充 `AUXILIARY_SIMULATION: AUX`。
- 验证：目标文件 ESLint、`pnpm run type-check` 和 `pnpm run build` 全部通过。
- 复用规则：页面代码按仓库当前 TS target 选择字符串 API；扩展联合类型时同步检索所有穷尽映射、筛选项和标签函数。

## ERR-227：X31 全量门禁被测试中的未使用变量阻断

- 时间：2026-09-17
- 场景：M10-14 / X31 后端 Ruff、系统检查与全量回归串行门禁。
- 现象：Ruff `F841` 指出测试中查询得到的 `second_row` 从未使用，按 `set -e` 正确阻断后续检查。
- 根因：可复现性测试改为比较序列化结果后，遗留了第二个 ORM 对象查询变量。
- 修复：删除无效查询，只保留实际用于三格式导出的首个模型对象。
- 验证：目标 Ruff、Django check、迁移一致性检查和 rehearsal 33 项全量测试串行通过。
- 复用规则：测试重构后立即清理不再参与断言的中间变量，先过目标 Ruff 再启动耗时全量回归。
## ERR-228：PDF 重生成命令混入清理动作被安全策略拒绝（2026-09-17）

- **现象**：将 `py_compile`、Django shell、删除临时脚本、清理渲染目录和重新渲染合并到一次命令时，整条命令因包含删除动作被执行策略拒绝，实际未执行。
- **根因**：产物生成与清理职责混在同一个组合命令里，没有遵循“连续集成操作按最小步骤执行”的约束。
- **修复**：生成、渲染与清理分开执行；渲染使用新的明确目录，临时脚本使用 `apply_patch` 精确删除。
- **验证**：PDF 已重新生成并逐页检查 4 页，中文、图表、表头和跨页原始数据均无裁切或重叠；临时脚本、字节码和两组渲染目录已按明确路径移入废纸篓。
## ERR-229：同一补丁对测试文件同时执行删除与新增被拒绝（2026-09-17）

- **现象**：把 `apps/trigger/tests.py` 从占位文件替换为 M06-01 测试时，在一个补丁中同时声明 Delete File 和 Add File，补丁校验提示同一路径存在多个操作。
- **根因**：`apply_patch` 不允许一个补丁对同一路径声明两种文件级操作。
- **修复**：保留原文件，改用单个 Update File 替换占位内容。
- **验证**：M06-01 测试已用 `Update File` 落盘，`trigger` 4 项专项测试全部通过。
## ERR-230：UUIDv7 前缀截断导致同毫秒任务编号重复（2026-09-17）

- **现象**：M06-01 专项测试连续创建调度任务时，多个任务都生成 `DSP-20260917-01A0AE`，触发任务编号唯一约束。
- **根因**：UUIDv7 的高位编码时间戳，同一毫秒生成的 UUID 前缀高度相同；截取字符串前 6 位不能作为随机短码。
- **修复**：任务编号改用去除连字符后的 UUIDv7 随机尾段作为短码。
- **验证**：任务编号改用 UUIDv7 随机尾段后，连续创建任务不再冲突，`trigger` 4 项专项测试全部通过。

## ERR-231：前端路由早于懒加载页面落盘触发 Vite 热更新缺页（2026-09-17）

- **现象**：开发服务器监测到 `resource-coordination.ts` 后立即重载，此时页面文件尚未写入，短暂报 `Failed to resolve import "@/views/resource-coordination/index.vue"`。
- **根因**：跨文件功能的落盘顺序是“注册路由 → 创建页面”，Vite 在两次写入之间完成了一次热更新。
- **修复**：页面文件完成后重新构建并重启 Vite；把可复用规则提升到 `AGENTS.md`，以后先落页面和依赖文件，再注册路由入口。
- **验证**：目标 ESLint、类型检查和生产构建通过；重启后页面入口及 Dashboard 请求均返回 200，浏览器控制台 0 error。

## ERR-232：并行重启时 Vite 再次早于 Django 就绪（2026-09-17）

- **现象**：Vite 已监听后，浏览器遗留请求在 Django 完成系统初始化前到达，产生两次 `ECONNREFUSED 127.0.0.1:8080`。
- **根因**：进程并行启动不等于依赖服务同时就绪；前端启动耗时明显短于 Django 初始化。
- **修复**：仍以独立就绪探针为准，并把“后端就绪后再启动或刷新前端”提升到 `AGENTS.md`；未把瞬时代理错误误判成业务故障。
- **验证**：后端直连与 Vite 代理的新接口都返回预期鉴权响应，带临时登录态的 Dashboard 请求返回 200。
- **See Also**：ERR-20260917-223

## ERR-233：在命令内部创建目录不能满足 exec 启动前的工作目录校验（2026-09-17）

- **现象**：把 `mkdir -p output/playwright/m06-01` 和后续命令放在同一调用中，同时将尚不存在的目录设为 `workdir`，进程在执行 `mkdir` 前即报 `No such file or directory`。
- **根因**：执行器会在启动 shell 之前先切换工作目录，命令体中的目录创建来不及生效。
- **修复**：先从仓库根目录独立创建并确认验收目录，再以该目录作为 Playwright 命令工作目录。
- **验证**：目录创建后，命名浏览器会话按 open → state-load → goto 顺序成功完成页面、抽屉和滚动验收；临时登录态随后精确撤销。
- **See Also**：`AGENTS.md`“新建 Playwright 验收标签”规则

## ERR-234：Vue-i18n 菜单回退函数触发 TypeScript 深层泛型实例化（2026-09-17）

- **现象**：为菜单增加“存在翻译则翻译，否则显示原文”的辅助函数后，`vue-tsc` 在 `i18n.global.t(title)` 报 `TS2589: Type instantiation is excessively deep and possibly infinite`。
- **根因**：项目的完整语言消息类型较大，直接在 Vue SFC 中调用 `t` 的重载会让 TypeScript 展开深层键路径泛型；运行逻辑本身没有错误。
- **修复**：在组件内把 `te` 和 `t` 明确收窄为 `(key: string) => boolean/string`，保留运行时翻译存在性判断，避免编译器递归推导整个消息树。
- **验证**：收窄函数类型后，目标 ESLint、`pnpm run type-check` 和 `pnpm run build` 全部通过；浏览器新会话不再出现菜单翻译缺失告警。

## ERR-235：M06-02 再次先注册路由后落页面，触发 Vite 短暂缺页（2026-09-17）

- **现象**：开发服务器监测到 `event-orchestration.ts` 后立即解析懒加载入口，而 `views/event-orchestration/index.vue` 尚未写入，短暂报 `Failed to resolve import`。
- **根因**：一次补丁先新增 API、路由和导航，下一次补丁才新增页面，仍违反已记录的“页面先于路由入口落盘”顺序。
- **修复**：页面落盘后完成目标 ESLint、类型检查和生产构建，并重启 Vite 清除旧模块图。
- **验证**：生产构建成功；后续以全新服务和浏览器会话验证页面及接口。
- **防再犯**：新增懒加载页面时，第一个补丁只创建页面及其直接依赖；确认文件存在后，第二个补丁再注册路由、导航与 Vite 回退，不把这些入口与页面拆成相反顺序。

## ERR-236：检索 Playwright 参数文档时漏写 `rg --`（2026-09-17）

- **现象**：检索包含 `--session` 的模式时，`rg` 把模式解释为自身参数并报 `unrecognized flag`。
- **根因**：已知以 `-` 开头的检索模式必须用 `--` 终止参数解析，但本次组合正则漏写。
- **修复**：改为 `rg -n -- "pattern" file`。
- **验证**：修正后正常定位 Playwright 会话、状态加载、控制台与关闭命令。

## ERR-237：压缩行 SCSS 使用宽上下文补丁匹配失败（2026-09-18）

- **现象**：M06-03 页面视觉调整的整块补丁提示找不到预期行，样式未应用。
- **根因**：目标 SCSS 将多个选择器压缩在同一行，补丁上下文把其中一个选择器误判为独立行，导致精确匹配失败。
- **修复**：保留已落盘的模板与脚本改动，改用只匹配真实完整行或最小字符串的分段补丁处理样式。
- **验证**：改用真实完整行与追加覆盖规则后样式成功落盘；目标 ESLint、`pnpm run type-check` 和 `pnpm run build` 均通过。
- **复用规则**：修改压缩格式的样式文件前先读取真实行结构；避免用格式化后的想象上下文提交大块补丁。

## ERR-238：向量探针误选已失效的首个本地模型记录（2026-09-18）

- **现象**：11636 已监听，但直接选择数据库中第一个 `model_local_provider` / `EMBEDDING` / `SUCCESS` 记录调用时，返回模型标识不是有效本地目录或 Hugging Face 仓库。
- **根因**：`SUCCESS` 是数据库配置状态，不保证该历史模型仍被真实知识库使用或其模型资产仍存在；“第一个成功记录”不是可靠业务探针选择规则。
- **修复**：改为从现有知识库的 `embedding_model` 绑定关系读取真实模型 UUID，再通过应用模型加载逻辑执行 `embed_query()`。
- **验证**：从“智能客服”知识库读取其真实绑定模型 UUID，通过应用模型加载逻辑调用成功，返回 384 维非空向量。
- **复用规则**：本地向量服务验收必须以真实知识库绑定的模型为入口，不按 provider/status 排序猜测模型。

## ERR-239：M03 动态基线样例在中间值提前触发两次派单（2026-09-18）

- **现象**：把指标告警与派单关系改成支持重复告警的一对多后，验收测试预期一张派单，实际生成两张。
- **根因**：样例序列中的 `42` 已超过三点历史窗口的关注阈值；随后 `41` 恢复、`86` 再次越界，按正确的重复告警语义生成了第二张派单，并非关联模型重复写入。
- **修复**：提高验收样例的动态偏差倍数，使普通波动不触发，最终异常峰值仍稳定触发；另保留独立回归用例验证告警关闭后再次越界会生成新派单。
- **验证**：重新执行平台监控测试，确认单次样例只生成一张派单，重复告警用例生成两张不同派单。
- **复用规则**：动态阈值样例必须先按实际均值和标准差核算每个中间点，分别覆盖“正常波动”和“明确异常”，不能只凭肉眼挑数值。
## ERR-240：apply_patch 同一补丁不能同时删除并新增同一路径

- 时间：2026-09-18
- 现象：尝试在一个补丁中对 `ui/src/views/metric-foundation/index.vue` 先 `Delete File` 再 `Add File`，工具返回 `multiple operations target`。
- 根因：`apply_patch` 不接受同一补丁内针对同一路径的多个文件级操作。
- 修复：拆成两个独立补丁，或使用单一 `Update File` 块。
- 验证：失败补丁未修改目标文件；后续通过拆分操作完成页面更新并执行 ESLint、类型检查和构建。

## ERR-241：output 目录内的 Django 脚本缺少 apps 模块路径

- 时间：2026-09-20
- 现象：从仓库根目录执行 `output/playwright/m03-02/create_state.py` 时，`django.setup()` 报 `ModuleNotFoundError: telecom_ai_agent`。
- 根因：独立脚本所在目录是 `output/playwright/m03-02`，Python 不会像 `apps/manage.py` 一样自动把仓库的 `apps/` 加入模块搜索路径。
- 修复：脚本在导入 Django 前根据自身位置计算仓库根目录，并把 `<repo>/apps` 显式加入 `sys.path`。
- 验证：脚本通过 `py_compile`，成功生成权限为 `600` 的 storage state；验收后按缓存版本撤销令牌。

## ERR-242：M03-02 测试文件残留未使用模型导入

- 时间：2026-09-20
- 现象：最终 `ruff check` 报 `MetricDutyShift imported but unused`。
- 根因：补值班测试时先导入模型，最终断言改为使用服务返回值，没有同步删除导入。
- 修复：移除测试文件中的未使用导入，不使用自动修复改动其他文件。
- 验证：目标 Ruff、platform_monitoring 全量测试和 `git diff --check` 重新通过。

## ERR-243：在组合执行器中并行转发本地图像参数失败

- 时间：2026-09-20
- 现象：在一次组合执行中用 `Promise.all` 并行调用两次本地图像查看工具，即使传入字符串 `detail: "high"`，执行器仍报 `image detail must be a string when provided`。
- 根因：组合执行器并行转发图像结果时对 `detail` 参数/图像输出发生了不兼容转换，不是截图文件损坏。
- 修复：停止并行转发，改成一次只查看一张图并省略可选 `detail` 参数；截图文件仍用 `file` 和单图视觉检查验收。
- 验证：后续单图调用成功显示趋势页和详情抽屉截图。
- 复用规则：本地图像视觉检查使用单次 `view_image` 调用；不要在同一个组合执行器脚本中并行转发多张图。

## ERR-244：M05-01 页面使用了当前 TypeScript lib 未包含的 replaceAll

- 时间：2026-09-20
- 现象：`pnpm run type-check` 在 API 编排页的时间格式化函数报 `TS2550: Property 'replaceAll' does not exist on type 'string'`。
- 根因：项目当前 TypeScript `lib` 目标低于 ES2021，页面误用了 `String.prototype.replaceAll`。
- 修复：改用兼容现有编译目标的全局正则 `replace(/\\//g, '-')`。
- 验证：目标 ESLint、`pnpm run type-check` 和 `pnpm run build` 重新执行后全部通过。

## ERR-245：rg 的 glob 过滤参数放在路径之后被解析为文件名

- 时间：2026-09-20
- 现象：检索 Playwright 验收脚本时，`rg` 报 `-g: No such file or directory`。
- 根因：命令先写了搜索路径，后写 `-g '*.md' -g '*.py'`，导致 glob 选项未按参数解析。
- 修复：所有 `rg` 选项放在模式和路径之前，使用 `rg -n -g '*.md' -g '*.py' -- 'pattern' paths...`。
- 后续：首次修正后的组合命令末尾又出现同样错误，说明宽命令未充分检查；已停止继续组合检索，改为一次一个最小命令。
- 验证：修正参数顺序的单一命令已正常定位历史验收说明和 TokenCache 实现。

## ERR-246：M05-01 浏览器首次进入新路由收到非 2xx 响应

- 时间：2026-09-20
- 现象：Playwright 按 `open → state-load → goto` 进入 `/admin/api-orchestration` 时报 `ERR_HTTP_RESPONSE_CODE_FAILURE`。
- 根因：页面路由 `/admin/api-orchestration` 以固定代理前缀 `/admin/api` 开头，Vite 在 SPA 回退之前将它误当成后端 API 转发，因而返回 500。
- 修复：前端菜单和页面入口改为 `/integration-orchestration`，同步调整 Vite 本地回退白名单；后端 `/admin/api/.../api-orchestration/...` 接口保持不变。
- 验证：Vite 重启后 `/admin/integration-orchestration` 返回 200，API 直连与 Vite 代理均返回预期的未登录 401；随后从已加载登录态的命名会话重新 `goto` 进行功能验收。

## ERR-247：Playwright 命名会话在跨回合环境更新后被回收

- 时间：2026-09-21
- 现象：前一回合已成功打开的 `m0501` 会话，用户继续后执行点击时提示 `browser is not open`。
- 根因：命名 Playwright 浏览器进程没有跨宿主回合/环境更新保留，元素引用也随会话失效；隔夜后 storage state 内的限时令牌也已过期。
- 修复：重建命名会话，重新签发一次本地限时令牌，再按 `state-load → goto → snapshot` 加载，不复用旧元素引用。
- 验证：新令牌加载后页面和全部业务请求正常，控制台 0 error；验收结束后已精确撤销令牌，并删除 storage state、临时脚本和隐藏会话产物。

## ERR-248：M11 安全检查检索猜测了不存在的应用配置文件

- 时间：2026-09-21
- 现象：读取 `apps/common/apps.py` 报文件不存在。
- 根因：按常见 Django 应用结构猜测路径，没有先确认仓库实际文件列表。
- 修复：改用 `rg --files apps/common` 确认目录结构，再选择现有入口或独立检查脚本实现。
- 验证：文件列表显示该应用当前没有 `apps.py`，后续不再依赖这个猜测路径。

## ERR-249：独立安全预检导入 Django settings 子模块触发配置加载

- 时间：2026-09-21
- 现象：不加载本地配置运行预检脚本时，导入 `telecom_ai_agent.settings.deployment` 先执行了 `settings/__init__.py`，随后因缺少外部配置文件报错。
- 根因：Python 导入子模块会先执行父包初始化；`settings` 包初始化不是无副作用的。
- 修复：将纯部署校验函数移到 `telecom_ai_agent` 顶层模块，使独立预检不依赖 Django settings 初始化。
- 验证：修复后独立脚本可在不加载 `.env.local` 的本地模式运行，并可用受控变量校验生产模式。
- 修复过程补充：首次 `apply_patch` 移动文件时给出了空更新块，工具拒绝；改为带实际上下文的移动补丁后继续。
- 预检继续执行后发现 Dockerfile 仍有两个空 Redis 口令默认项；按同一规则移除，并重跑静态门禁。
- 第二次预检暴露纯函数仍假设配置对象有 `get_debug()`，而独立脚本传普通字典；改为基于映射字段读取并解析布尔值，保持纯函数可测试。

## ERR-250：主数据审计测试将 Django 实例内部状态直接 JSON 序列化

- 时间：2026-09-21
- 现象：`test_successful_master_read_persists_value_free_fact` 在 `json.dumps(event.__dict__)` 报 `ModelState is not JSON serializable`。
- 根因：Django 模型 `__dict__` 含内部 `_state`，不是数据库审计字段集合。
- 修复：测试只提取模型持久化字段和值，再检查其中不含查询值和联系方式。
- 验证：修复后重跑该测试及 M11-03 相关回归。

## ERR-251：目标用户视图的 Ruff 检查发现既有未使用异常变量

- 时间：2026-09-21
- 现象：对 M11-03 修改涉及的 `apps/users/views/user.py` 执行 Ruff 时，原有密码解密异常分支 `except Exception as e` 报 F841。
- 根因：异常变量未在分支中使用，与新增读取审计逻辑无关，但阻断目标文件静态检查。
- 修复：保留异常处理行为，仅移除未使用的变量绑定。
- 验证：重新运行目标文件 Ruff 和 M11-03 回归测试。

## ERR-252：M11 扫描脚本首次静态检查发现未使用导入

- 时间：2026-09-21
- 现象：`ruff check scripts/m11_security_scan.py` 报 F401，`sys` 导入未使用。
- 根因：编写扫描编排脚本时保留了草稿导入；组合检查没有先 `set -e`，导致后续检查表验证仍运行。
- 修复：移除导入；有先后依赖的检查重新使用 `set -e`，先通过静态检查再运行扫描。
- 验证：目标 Ruff 和检查表只读验证重新执行通过。

## ERR-253：M11 依赖与镜像扫描首次运行未生成两类报告

- 时间：2026-09-21
- 现象：Python 审计正常产出发现项；`pnpm audit` 返回 `ERR_PNPM_AUDIT_ENDPOINT_NOT_EXISTS`，Docker Scout 提示需要 Docker 登录，前端和镜像均被脚本标为 `ERROR` 而非通过。
- 根因：本机 pnpm 默认 npm 镜像站不提供 audit 接口；Docker Scout 漏洞服务需要当前主机的 Docker 凭据，虽然本地已有旧镜像也不能匿名扫描。
- 修复：前端只读审计显式使用官方 npm registry；镜像保留 `ERROR/未验证` 并记录旧镜像 ID，不借用其他镜像结果或假报通过。补充扫描工具/登录条件后再复扫。
- 验证：显式 registry 后 `pnpm audit` 返回结构化漏洞清单；一键报告重新执行后前端从 `ERROR` 变为 `FINDINGS`。

## ERR-254：M11 文档检索误用了猜测的操作手册文件名

- 时间：2026-09-21
- 现象：`rg` 同时检索计划与 `docs/建设方案分步开发与验收操作手册.md` 时，后者不存在，命令返回 2。
- 根因：实际文件名是 `docs/建设文档分步开发与验收操作手册.md`，未先枚举路径。
- 修复：先用 `rg --files docs` 定位准确文件名，后续检索只传已存在路径。
- 验证：文件列表确认目标文件存在，后续按准确名称继续。

## ERR-255：M11 扫描单测临时目录不在仓库内

- 时间：2026-09-21
- 现象：新增前端扫描单测把报告写入系统临时目录，脚本计算仓库相对报告路径时报 `ValueError`；组合校验未设置 `set -e`，随后静态检查继续运行。
- 根因：生产脚本约定报告落在仓库输出目录，而单测没有遵守；有先后依赖的校验仍混合执行。
- 修复：单测临时目录指定在 `output/` 下；后续回归命令先执行 `set -e`。
- 验证：目标单测与 Ruff 重新执行通过。

## ERR-256：备份资料检索使用未确认的 zsh 通配路径

- 时间：2026-09-22
- 现象：检索 `docker-compose*` 时 zsh 报 `no matches found`；组合命令未先 `set -e`，后续 AGENTS 输出掩盖了失败退出码。
- 根因：没有先列出仓库文件便猜测 compose 文件名，且把有先后依赖的检索组合在无错误中止的命令中。
- 修复：用 `rg --files` 找实际 compose/备份路径，再按准确路径检索；组合检查先执行 `set -e`。
- 验证：后续路径枚举与定向检索正常。

## ERR-257：数据库容量探针误把 schema 字符串与 OID 比较

- 时间：2026-09-22
- 现象：查询 `pg_class.relnamespace` 时把拼接的文本与 OID 直接比较，PostgreSQL 报运算符不匹配。
- 根因：为避免命令引号嵌套而过度改写 SQL，遗漏了列类型。
- 修复：容量只查 `pg_database_size`；表数从 `pg_tables` 以 `current_schema()` 过滤，不拼接 OID。
- 验证：修正后的只读探针返回数据库容量、表数和扩展名。

## ERR-258：备份演练预检没有读取项目的 JB_ 数据库变量

- 时间：2026-09-22
- 现象：备份脚本预检报 `DB_NAME must be a simple PostgreSQL identifier`，虽然 Django 实际连接正常。
- 根因：脚本最初只读取通用 `DB_*` 环境变量，本项目 `.env.local` 使用 `JB_DB_*`，由项目配置层映射。
- 修复：脚本优先读取 `JB_DB_*`，兼容 `DB_*`，不打印变量值或密码。
- 验证：加载 `.env.local` 后重新运行预检与隔离恢复演练。

## ERR-259：隔离库首次恢复失败但脚本隐藏了可诊断错误

- 时间：2026-09-22
- 现象：57 MB 本地库已成功产生自定义格式备份，但恢复到新建临时库返回 1；脚本只报告通用失败，临时库已安全删除。
- 根因：恢复命令的 stderr 被完全隐藏，无法定位具体对象/参数错误；加最小诊断后确认 `pg_restore` 必须显式使用 `-d` 指定目标库，不能像 `psql/pg_dump` 一样把库名放在末尾。
- 修复：仅在失败时把 stderr 写入权限为 600 的本地诊断文件，不在控制台或文档直接打印原始内容；恢复命令改用 `-d "$db"`，并删除临时敏感诊断文件。
- 验证：重新运行演练，要求表、大对象和文件行数量一致，临时库被删除。

## ERR-260：M02 质检文档检索传入不存在的裸通配符

- 时间：2026-09-22
- 现象：检索 `docs/测试/营销回答质检*` 时 zsh 报 `no matches found`，组合命令前段输出掩盖了这一错误。
- 根因：未先枚举确切文档路径，且组合检索未用 `set -e` 统一中止。
- 修复：先用 `rg --files docs/测试` 定位文件，再以已确认的路径检索；后续组合校验先 `set -e`。
- 验证：目标文件检索改按文件列表确认，不再依赖裸通配符。

## ERR-261：在 ui 工作目录误用仓库根目录相对路径

- 时间：2026-09-22
- 现象：检查 pnpm 配置时在 `ui/` 工作目录执行 `rg --files ... ui .`，其中 `ui` 被解析为不存在的 `ui/ui`，报 `No such file or directory`；后续 ESLint 因命令未设 `set -e` 仍继续执行。
- 根因：切换工作目录后沿用了仓库根目录的相对路径，并把独立检查放在同一命令块而未设置失败即停止。
- 修复：在 `ui/` 中只查 `.`，前端校验分别运行或先 `set -e`；根目录文档操作切回仓库根目录。
- 验证：重新从正确目录执行配置枚举和目标文件 ESLint。

## ERR-262：后端重启未就绪时立即执行直连与代理探针

- 时间：2026-09-22
- 现象：`runserver --noreload` 刚启动就探测 8080，直连返回连接失败、Vite 代理返回 500。
- 根因：Django 启动前还有系统检查和初始化，端口尚未监听；不是新复核路由本身的故障。
- 修复：等待启动会话完成初始化后，再核对监听端口并执行直连与代理探针。
- 验证：同一路由直连与 Vite 代理均返回未登录预期状态 401，证明路由已注册且代理可达。

## ERR-263：探查可选 management 目录时再次传入裸通配符

- 时间：2026-09-22
- 现象：`apps/application/management` 目录不存在，随后 `apps/application/management/commands/*.py` 在 zsh 中报 `no matches found`。
- 根因：在未用 `rg --files` 确认目录存在时直接传入裸通配符，重复了 ERR-260 的路径假设。
- 修复：停止该组合探查；新验收命令先按已知文件结构判断目录，必要时用 `apply_patch` 创建，检索只用已确认的文件路径。
- 验证：后续不对可选路径使用裸通配符。

## ERR-264：M02 直连序列化器验收未传必需的客户端 IP

- 时间：2026-09-22
- 现象：调用 `OpenChatSerializers` 和 `ChatSerializers` 验收真实对话时，创建 `application_chat` 因 `ip_address` 为 `NULL` 违反非空约束。
- 根因：实际 HTTP 入口会由请求提取 IP；直连序列化器的验收脚本绕过视图，没有补传该字段。
- 修复：脚本两个序列化器都显式传 `127.0.0.1` 作为本地验收来源；不改业务表约束。
- 验证：重新执行真实资料对话探针，并检查记录、合规元数据和复核条目。

## ERR-265：Ollama 在线但独立向量服务未启动

- 时间：2026-09-22
- 现象：真实产品资料已索引，Ollama `/api/tags` 返回模型列表，但通用服务助手检索在 `LocalEmbedding.embed_query()` 处解析非 JSON 响应失败。
- 根因：知识库绑定的向量模型通过 `127.0.0.1:11636/admin/api/model/<UUID>/embed_query` 提供服务；当时 11636 未监听。Ollama 的 11434 是生成模型服务，不能替代独立向量服务。
- 修复：按项目既有 `scripts/start-local.sh local_model` 启动独立向量服务，等待 11636 监听，再运行绑定模型 UUID 的真实对话探针。
- 验证：真实资料样例完成检索和回答，合规动作为 `PASS`、引用数 1；同一资料检索后注入受控违规模型答复，合规动作为 `BLOCKED` 并创建待复核条目，原违规文本未进入对话详情。

## ERR-266：复核事实核查误把 chat_id 当作 record_id

- 时间：2026-09-22
- 现象：浏览器提交复核后，Django 查询 `ServiceAnswerReview(record_id=<验收打印的 chat_id>)` 报不存在；组合命令接 `tail` 后掩盖了失败退出码。
- 根因：验收脚本输出的是会话 ID，不是对话记录 ID；shell 管道未启用 `pipefail`。
- 修复：按 `record__chat_id` 查询复核事实，组合检查使用 `set -e` 与 `set -o pipefail`，不再把两个 UUID 混用。
- 验证：复核状态、版本号和操作事件数与浏览器提交结果一致。

## ERR-267：M12 文档定位沿用错误的文件名

- 时间：2026-09-22
- 现象：检索 `docs/建设方案分步开发与验收操作手册.md` 报文件不存在。
- 根因：实际文件名需要先通过文件列表确认，直接按记忆拼接了路径。
- 修复：改用 `rg --files docs` 先定位，再使用确切路径；不把文件缺失误判为验收材料缺失。
- 验证：M12 计划改从已确认的 `docs/建设方案全量粗粒度V1实施计划.md` 读取，其他文档按枚举结果访问。
- 复发：定位平台监控模型时再次假定存在 `apps/platform_monitoring/models/` 目录；检索结果显示该路径不存在。后续严格先 `rg --files apps/platform_monitoring` 再选具体文件，不使用猜测的可选目录路径。

## ERR-268：M12 首轮跨模块 keepdb 回归暴露测试隔离问题

- 时间：2026-09-22
- 现象：57 个跨模块测试组合出现多项失败，服务助手复核测试的全表计数断言预期 1、实际 3；该模块单独执行曾通过。
- 根因：训练流水线测试模块导入了 `common.job.scheduler`，原实现模块导入时就启动 `BackgroundScheduler`。测试发现阶段后台作业与测试事务并发运行，使推荐模块的全表计数断言串扰；复用测试库只是表象。
- 修复：复核用例改按本次 record 精确计数；`manage.py test` 时调度器只定义对象、不启动后台线程，正常服务启动行为不变。
- 验证：推荐模块单独 21 项、与其他模块合并 57 项，均在原有 `--keepdb --noinput` 模式下通过。无需隔离测试运行器。

## ERR-269：筛选测试输出的临时 JS 正则语法错误

- 时间：2026-09-22
- 现象：工具编排脚本在运行测试前因正则表达式末尾多了一个右括号，报 `Unmatched ')'`。
- 根因：为压缩大量测试日志而临时拼接复杂正则，缺少最小语法检查。
- 修复：改用简单的 `startsWith` 条件筛选失败摘要；不再组合复杂未验证正则。
- 验证：重新运行测试并取得失败分类。

## ERR-270：改写主库名不能直接选择隔离测试库

- 时间：2026-09-22
- 现象：临时设置 `JB_DB_NAME=m12_v1_audit_20260922` 后执行 keepdb 回归，Django 在建测试库之前即尝试连接该不存在的主库并失败。
- 根因：`JB_DB_NAME` 指向应用默认连接而不是测试库名称；修改它会令初始化无法连接现有主库。
- 修复：保持主库连接不变，仅通过显式测试运行器或 `DATABASES['default']['TEST']['NAME']` 指定唯一的测试库；不得为此修改 `.env.local`。
- 验证：后续用临时隔离测试库确认故障仍可复现，最终定位为测试阶段后台调度器意外启动；恢复普通主库配置和常规 `--keepdb`，57 项组合回归通过。隔离运行器已移除。

## ERR-271：隔离测试运行器只更新 settings 未覆盖已缓存连接

- 时间：2026-09-22
- 现象：指定 `JB_ISOLATED_TEST_DB_NAME` 后测试仍报告使用既有测试库，推荐模块原有计数失败不变。
- 根因：Django 测试数据库构建读取 `connections[alias].settings_dict`；该连接对象可能已经在应用初始化阶段创建，仅修改 `settings.DATABASES` 不保证同步到缓存连接。
- 修复：在运行器 `setup_databases` 同时把显式测试库名写入已缓存连接的 `settings_dict['TEST']`，不改应用主库 `NAME`。
- 验证：唯一测试库正确创建并完成迁移，但推荐串扰仍复现，排除了既有测试库残留作为根因；隔离运行器已移除，实际修复见 ERR-268。

## ERR-272：M12 台账探针假定告警直接绑定 task_id

- 时间：2026-09-22
- 现象：联动关系只读查询对 `MarketingAlert.values("task_id")` 报 `FieldError`。
- 根因：营销告警通过规则及 `source_snapshot` 关联业务来源，而不是直接 `task` 外键；临时长命令按别的模型结构猜字段。
- 修复：先读取模型定义，再在短的可复用只读探针中分别按真实 FK 与快照字段汇总；不再把所有关联查询塞进一条 `shell -c`。
- 验证：重新核对共同工作空间的任务、推荐、对话、报告与告警关系。

## ERR-273：M12 指标探针使用了错误的流程节点反向关系名

- 时间：2026-09-22
- 现象：`m12_metric_alert_probe.py` 首次运行在读取待人工节点时抛出 `AttributeError: EventFlowRun has no attribute nodes`；指标定义和批次尚未写入。
- 根因：编排模型实际声明 `EventFlowNodeRun.run.related_name="node_runs"`，脚本按通用名称猜成 `nodes`。
- 修复：改用 `run.node_runs`，并在运行前核对相关模型的 `related_name`。
- 验证：修正后指标探针成功创建 1 条观测、1 条告警与 1 张派单，重复执行复用原批次及工单；全局铃铛对应通知 2 条。

## ERR-274：报告测试文件检索使用了 zsh 裸通配符

- 时间：2026-09-22
- 现象：`rg ... apps/marketing/test_report*` 因路径无匹配，被 zsh 在执行前报 `no matches found`。
- 根因：未先用 `rg --files` 确认候选路径，与项目命令约束不符。
- 修复：先列文件，再按确认存在的测试文件运行 `rg`；不在 zsh 命令里传可能无匹配的裸通配符。
- 验证：使用 `rg --files apps/marketing` 确认报告测试位于 `apps/marketing/tests.py`，随后定位到 `MarketingAnalysisReportServiceTests`。

## ERR-275：头部导航容器路径按惯例猜错

- 时间：2026-09-22
- 现象：读取 `ui/src/layout/layout-header/index.vue` 报文件不存在；同一命令中其他导航文件读取成功。
- 根因：未先确认布局文件清单，按常见目录结构猜了不存在的 `index.vue`。
- 修复：先用 `rg --files ui/src/layout` 定位实际 `SystemHeader.vue` / `UserHeader.vue`，再读取。
- 验证：文件清单已确认，后续按真实路径检查头部容器。

## ERR-276：指标调度入口检查猜测了不存在的模块路径

- 时间：2026-09-22
- 现象：读取 `apps/platform_monitoring/tasks.py` 和 `apps/telecom_ai_agent/celery.py` 返回文件不存在。
- 根因：按常见 Celery 布局猜路径，没有先用 `rg --files` 核对仓库实际结构。
- 修复：以 `rg --files`/现有 import 链定位模块；本项目平台监控当前使用 `platform_monitoring/jobs.py` 的 APScheduler 入口，不能假定独立 tasks.py。
- 验证：已读取实际 `jobs.py`、`common/job/__init__.py` 与 `ops/celery/signal_handler.py`；新增业务指标任务后，两个平台监控调度项均成功注册。

## ERR-277：M12 跨协议探针假定精排记录直接关联营销任务

- 时间：2026-09-23
- 现象：探针查询 `RecommendationRankingRun.select_related("task", "customer")` 抛出 `FieldError`，三类协议验收数据尚未写入。
- 根因：精排运行直接关联客户、融合运行和精排版本；营销任务属于客户关系，应通过 `customer__task` 读取。
- 修复：查询改为 `select_related("customer__task")`，任务 ID 改从 `ranking.customer.task_id` 获取；跨模型写探针前先核对真实外键链。
- 验证：修正后同一场景完成 IVR 契约回放、晓搭 Mock 调用和预演实例，重复执行复用原事实；三模块 46 项专项测试通过。

## ERR-278：M12 版本事实核查猜错模型发布记录类名

- 时间：2026-09-23
- 现象：只读 shell 导入 `LifecycleModelReleaseRecord` 抛出 `ImportError`，版本事实尚未输出。
- 根因：实际类名是 `ModelReleaseRecord`；按生命周期版本类名习惯错误补全了发布记录名称。
- 修复：先从 `models_provider/models/lifecycle.py` 和包导出核对真实类名，再执行最小只读查询。
- 验证：使用 `ModelReleaseRecord` 完成只读核对，并补齐同任务知识索引发布/回滚事实；版本探针重复执行无新增发布记录，相关 28 项测试通过。

## ERR-279：Docker 配置审计再次使用不存在的 zsh 裸通配符

- 时间：2026-09-23
- 现象：检索环境配置时传入 `.env.example*`，zsh 因无匹配文件报 `no matches found`，该段检索未执行。
- 根因：没有先用 `rg --files` 确认示例环境文件是否存在，复发了 ERR-274 同类命令问题。
- 修复：所有可选配置路径先枚举真实文件，再把明确路径传给 `rg`；不在 zsh 中使用可能无匹配的裸通配符。
- 验证：已通过明确文件清单完成 Docker/Compose/环境样例审计，部署预检脚本和 Compose 配置校验通过。

## ERR-280：Ollama 提供器目标 Ruff 检查暴露历史未使用导入

- 时间：2026-09-23
- 现象：Docker 模型地址改造后的目标 Ruff 检查报告 `BaseModelCredential`、`ValidCode` 两个导入未使用。
- 根因：该旧文件此前未进入本轮目标静态检查，清理 URL 辅助代码后仍保留了无引用导入。
- 修复：删除两个未使用导入，不改变 Ollama 提供器行为。
- 验证：Ollama 目标 Ruff 通过，部署、Web 和 Ollama 端点共 19 项专项测试通过。

## ERR-281：Web 专项测试依赖 locale 编译产物不存在

- 时间：2026-09-23
- 现象：`test_root_locale_index_returns_empty_list_when_missing` 等两项在工作区已有编译后的 `index.json` 时收到 `FileResponse`，调用 `response.json()` 报错。
- 根因：测试目标是文件缺失回退，却没有显式隔离 `os.path.isfile`，结果受先前 `compilemessages`/构建产物影响。
- 修复：两项用例显式 mock 目标文件不存在，只验证缺失回退语义，不依赖工作区残留。
- 验证：Web、部署与 Ollama 专项共 19 项测试通过，不再受已生成 locale 文件影响。
## ERR-282：Docker 镜像构建期间守护进程 API 返回 500

- 日期：2026-09-23
- 现象：`docker compose build app` 长时间无新输出，同时只读执行 `docker ps` 返回 `Internal Server Error`，请求的是本机 Docker socket 的 `/v1.24/containers/json`。
- 根因：Docker Desktop Linux 虚拟机生命周期接口持续 `connection refused`，守护进程已失去响应；并非应用构建脚本报错。
- 修复：终止已退出的构建任务，完整退出并重新启动 Docker Desktop。
- 验证：`docker info` 恢复，`telecom-ai-agent:local` 重新构建成功，容器实际启动并进入 healthy。

## ERR-283：审计可选隐藏目录时再次使用了 zsh 裸通配符

- 日期：2026-09-23
- 现象：`du -sh .docker/* .docker/.[!.]*` 因隐藏文件模式无匹配而触发 `zsh: no matches found`，导致同一命令未执行。
- 根因：未遵守项目已沉淀的“可选路径先枚举、不得传裸通配符”规则。
- 修复：改用 `find .docker -mindepth 1 -maxdepth 1 -print0` 配合 `du -sh`，不依赖 shell glob 是否有匹配。
- 验证：已使用 `find` 完成目录审计，不再依赖可选 glob 命中。

## ERR-284：同一 apply_patch 同时删除并新增相同文档失败

- 日期：2026-09-23
- 现象：重写 Docker 部署文档时，在一个补丁中同时 `Delete File` 和 `Add File` 指向同一路径，校验报 `multiple operations target`。
- 根因：`apply_patch` 不允许单个补丁对同一路径执行两种文件级操作。
- 修复：改为先删除文件、再用独立补丁新增，或使用单一 `Update File`。
- 验证：`docs/Docker手动打包与运行命令.md` 已用独立补丁重写，并在真实镜像验收后补齐导出/导入说明。

## ERR-285：应用镜像重建因固定阿里云 APT HTTP 镜像中断

- 日期：2026-09-23
- 现象：运行层安装 `curl/ffmpeg` 时大量软件包从 `mirrors.aliyun.com` 下载失败，APT 重试后以 exit code 100 退出；并取消并行中的 Python 构建层。
- 根因：Dockerfile 将 Debian 软件源硬编码为阿里云 HTTP 镜像，当前 Docker 网络到该镜像连接不稳定，且 Compose 无法覆盖构建参数。
- 修复：Dockerfile 默认恢复 Debian 官方 HTTPS 源；Compose 暴露 `APT_DEBIAN_MIRROR`、`APT_SECURITY_MIRROR` 构建参数，特殊网络环境可在 `docker/.env` 覆盖。
- 验证：使用官方 HTTPS 源完成 2.52 GB 业务镜像构建，容器启动与健康检查通过。

## ERR-286：复用本地 PostgreSQL 18 镜像启动时健康检查失败

- 日期：2026-09-23
- 现象：因 Docker Hub 拉取不稳定，Compose 临时覆盖为本机已有 `telecom-ai-postgres-pgvector:18`；容器启动后 PostgreSQL 健康检查失败，应用未启动。
- 根因：覆盖镜像入口后 Compose 生成的容器 `Cmd=null`，入口脚本没有收到 `postgres` 参数而正常退出，`restart: unless-stopped` 形成退出码 0 的重启循环。
- 修复：根据用户最终部署边界，删除 Compose 内 PostgreSQL/Redis 服务，只保留业务容器并通过环境变量连接已有中间件；因此不再需要修补临时 PostgreSQL Compose 命令。
- 验证：Compose 只包含 `app` 服务，真实容器已成功对接现有 `telecom-ai-postgres` 和 `redis`，`/healthz` 返回 200。

## ERR-287：zsh 验收循环误用特殊变量 `path` 导致系统命令不可用

- 日期：2026-09-23
- 现象：HTTP 验收循环使用 `for path in ...` 后，同一 zsh 命令块中的 `curl`、`tr`、`cat` 均报 `command not found`。
- 根因：zsh 的 `path` 是与 `PATH` 绑定的特殊数组变量，循环赋值覆盖了命令搜索路径。
- 修复：脚本变量改用业务化名称（如 `request_path`），并将该规则补充到项目经验约束。
- 验证：使用 `request_path` 重新执行后，`/healthz`、`/admin/login`、`/chat/` 均返回 200，未认证管理 API 返回 401。

## ERR-288：容器验收组合命令被安全规则拒绝

- 日期：2026-09-23
- 现象：组合执行 HTTP、进程和模型探针时，因命令末尾使用 `rm -f` 删除临时响应文件，整个命令在执行前被安全规则拒绝。
- 根因：验收脚本不必要地将响应写入临时文件，又使用强制删除收尾，触发了破坏性命令防护。
- 修复：改为响应直接通过管道统计，并拆分为不落盘的最小探针；需临时文件时使用 `mktemp -d` 和明确可恢复的清理方式。
- 验证：改用 `/dev/null` 和管道后，HTTP 探针成功执行，容器健康且只映射 8080。

## ERR-289：精简运行镜像不包含 `ps`

- 日期：2026-09-23
- 现象：容器内进程验收执行 `ps -ef` 返回 `ps: not found`，`set -e` 使后续 Ollama 和向量端口探针未执行。
- 根因：运行镜像为精简 Debian 环境，未安装只用于诊断的 `procps`；验收脚本错误假设 `ps` 必定存在。
- 修复：不为单次验收增大业务镜像，改为读取 `/proc/*/cmdline` 核对 Gunicorn、Celery 和本地向量服务进程。
- 验证：从 `/proc/*/cmdline` 确认 Web Gunicorn、内部向量 Gunicorn 和 Celery Worker 存在；后续 Ollama 与 384 维向量请求探针均通过。

## ERR-290：更新工程规则时补丁上下文过时

- 日期：2026-09-23
- 现象：向 `AGENTS.md` 添加镜像验收经验时，`apply_patch` 提示找不到预期的 zsh 规则行。
- 根因：该行在先前已补充 `path` 特殊变量，本次补丁仍使用只含 `status` 的旧上下文。
- 修复：先读取当前文件尾部，再以现存完整行为锚点追加规则。
- 验证：镜像验收探针规则已成功加入 `AGENTS.md`。

## ERR-291：文档渲染环境没有 `fc-list`

- 日期：2026-09-23
- 现象：为修复参考 DOCX 中文字体在 LibreOffice 渲染为方框的问题，执行 `fc-list :lang=zh` 时返回 `command not found`。
- 根因：当前捆绑文档运行时未提供 fontconfig CLI，不能用 `fc-list` 盘点中文字体。
- 修复：改用 `find` 盘点系统与工作区的 TTF/TTC/OTF 文件，并用实际 DOCX 渲染验证选定字体，不依赖 fontconfig CLI。
- 验证：最终 71 页 DOCX 已逐页渲染检查，嵌入的 Alibaba PuHuiTi 中文字形显示正常，无方框、缺字或越界。

## ERR-292：捆绑 Python 环境未安装 `fontTools`

- 日期：2026-09-23
- 现象：尝试用 `fontTools.ttLib` 读取系统 TTC/TTF 字体家族名时抛出 `ModuleNotFoundError`。
- 根因：文档捆绑 Python 依赖集不包含 `fontTools`，该盘点只是可选便利路径。
- 修复：不为单次文档任务安装新依赖；使用已知 macOS 字体家族名生成最小 DOCX，以实际 LibreOffice 渲染结果选定中文字体。
- 验证：字体样例与最终 71 页 DOCX 均在捆绑 LibreOffice 渲染通过，无需安装 `fontTools`。

## ERR-293：技能安装器下载 GitHub ZIP 时传输中断

- 日期：2026-09-23
- 现象：安装 `lc2panda/wps-skills` 仓库中的 `wps-office` 技能时，默认 ZIP 下载抛出 `http.client.IncompleteRead`，仅接收到部分压缩包内容。
- 根因：GitHub 归档下载连接在分块传输过程中提前中断，与技能目录结构无关。
- 修复：改用安装器的 `--method git`，通过 Git 稀疏检出获取 `skills/wps-office`。
- 验证：技能已安装到 `/Users/zhaozhenchao/.codex/skills/wps-office`，`SKILL.md` 与 `README.md` 均存在，完整读取通过。

## ERR-294：详设取证时误判 Django 根路由为单文件

- 日期：2026-09-24
- 现象：读取 `apps/telecom_ai_agent/urls.py` 时返回文件不存在。
- 根因：项目根路由采用 `apps/telecom_ai_agent/urls/` 包结构，入口分别位于 `__init__.py`、`web.py` 和 `model.py`，不能按常见单文件布局猜测。
- 修复：先用 `rg --files` 或 `find` 确认实际路径，再读取路由包；详设接口取证同时以已生成的 `output/m11-02/asset-inventory.json` 为准。
- 验证：已定位三个根路由文件，并继续从 893 条真实路由资产清单提取代表性接口。

## ERR-295：DOCX 包保真校验沿用了旧的嵌入字体文件名

- 日期：2026-09-24
- 现象：最终 DOCX 的 ZIP 完整性检查通过，但自定义包差异脚本报告 `word/fonts/AlibabaPuHuiTi-Regular.odttf` 为非预期新增项，并错误显示嵌入字体不存在。
- 根因：校验白名单仍使用生成脚本早期设想的 `AlibabaPuHuiTi355Regular.ttf`，而实际嵌入工具按 Office 字体混淆规范写入 `AlibabaPuHuiTi-Regular.odttf`。
- 修复：以最终包中 `fontTable.xml` 和字体关系文件的实际目标为准，更新白名单和存在性检查，不修改已通过渲染的文档。
- 验证：使用修正后的规则重新比较参考包与成品包，除正文、内容类型、字体表、字体关系和嵌入字体外，其余源部件哈希一致。

## ERR-296：LibreOffice 复用既有实例导致中文字体渲染失效

- 日期：2026-09-24
- 现象：测试报告 DOCX 已嵌入项目中文字体，但首次通过 `soffice --headless` 转 PDF 时中文消失，仅英数内容可见。
- 根因：LibreOffice 命令连接到已使用其他字体环境启动的既有用户实例，当前命令传入的 `FONTCONFIG_FILE` 没有在该实例中重新生效；文档本身的中文和嵌入字体包均完整。
- 修复：每轮文档渲染使用 `mktemp -d` 创建独立目录，并通过 `-env:UserInstallation=file://...` 启动隔离的 LibreOffice 用户实例，同时显式传入项目字体配置。
- 验证：隔离实例将最终测试报告渲染为 13 页 A4 PDF，逐页检查中文、表格和分页均正常。

## ERR-297：测试报告生成脚本首次静态检查存在未使用导入

- 日期：2026-09-24
- 现象：`ruff check scripts/generate_project_test_report.py` 报 4 个 F401，涉及未使用的分页、对齐和尺寸常量。
- 根因：生成脚本在版式迭代后移除了对应实现，但没有同步清理早期导入。
- 修复：删除 `WD_SECTION_START`、`WD_ALIGN_VERTICAL`、`WD_BREAK` 和 `Inches` 未使用导入。
- 验证：重新执行 Ruff、Python 编译、DOCX ZIP 完整性和 python-docx 解析检查均通过。

## ERR-298：DOCX 内容验收只读取顶层段落导致错误断言

- 日期：2026-09-24
- 现象：测试报告 ZIP 完整性通过，但使用 `Document.paragraphs` 断言“生产上线暂不批准”时失败。
- 根因：该结论位于表格单元格中，python-docx 的 `Document.paragraphs` 不包含表格内段落；验收程序把读取范围不足误判为内容缺失。
- 修复：内容验收同时遍历顶层段落和所有表格单元格段落，再检查关键标题、结论和表格数量。
- 验证：修正读取范围后关键内容与文档结构检查通过。

## ERR-299：检索 SQL 元命令时反斜杠模式解析失败

- 日期：2026-09-24
- 现象：使用 `rg` 的正则分组同时检索 `\\connect` 时返回 `unrecognized escape sequence`。
- 根因：正则中的反斜杠层经过 shell 与 ripgrep 两次解释，模式没有按字面量传递。
- 修复：后续分别使用固定字符串检索，或使用 `rg --fixed-strings -- '\\connect'`，不在复杂分组中拼接 psql 元命令。
- 验证：已通过固定字符串与独立模式完成初始化 SQL 内容核对。

## ERR-300：zsh 中未命中的可选 Compose 通配符中断文件检索

- 日期：2026-09-24
- 现象：直接把 `compose*.yml` 作为 `rg` 的可选路径参数时，zsh 在命令执行前报告 `no matches found`，导致同一条检索没有运行。
- 根因：zsh 默认会把未命中的裸通配符视为错误；该路径只是候选文件，不应依赖 shell 展开。
- 修复：先使用 `rg --files -g 'compose*.yml' -g 'docker-compose*.yml'` 确认真实文件，再把明确路径传给后续检索。
- 验证：已定位仓库实际使用的 `docker-compose.yml`，并确认数据库默认名为 `initdb`、默认用户为 `root`。

## ERR-301：同一 apply_patch 中重复操作 README 路径

- 日期：2026-09-24
- 现象：一个补丁同时对 `README.md` 使用 `Delete File` 和 `Add File`，工具拒绝并提示同一路径存在多个操作。
- 根因：`apply_patch` 不接受在同一补丁事务内先删除再新增同一路径。
- 修复：对已有文件使用单次 `Update File`，新增交付文档再使用独立的 `Add File`。
- 验证：重新应用后 README 与交付文档均通过差异和 Markdown 结构检查。

## ERR-302：Django shell 聚合查询遗漏 `Count` 导入

- 日期：2026-09-28
- 现象：查询内置角色在各工作空间的绑定数量时，Django shell 在执行 `annotate(total=Count('id'))` 时报 `NameError`。
- 根因：shell 命令中未从 `django.db.models` 导入 `Count`，且在同一行中混合了两个不相依赖的查询。
- 修复：把角色列表与聚合统计拆成独立的最小查询，聚合查询显式导入 `Count`。
- 验证：修正查询已返回各工作空间的内置角色绑定数量。

## ERR-303：演示专属角色误叠加内置普通用户角色

- 日期：2026-09-28
- 现象：验收 AI 与知识工程师的有效角色时，期望得到 `EXTENDS_USER` 专属角色，实际得到内置 `USER`。
- 根因：账号生成命令把 `User.role` 的兼容字段与实际的 `WorkspaceUserRoleMapping` 绑定混为一件事，给所有专属角色额外绑定了内置普通用户角色，扩大了权限。
- 修复：在角色定义中增加 `bind_base_role`，平台管理员、营销运营专员和调度演练负责人因现有粗粒度门禁保留内置角色，AI 工程师和质检值班专员只绑定专属角色。
- 验证：幂等刷新后，AI 工程师和质检值班专员均只保留两个工作空间的专属角色绑定，密码和目标权限验收通过。

## ERR-304：管理命令 shell 未初始化可插拔模型注册表导致权限验收走降级分支

- 日期：2026-09-28
- 现象：数据库已确认 AI 工程师只绑定专属角色，但在独立 `manage.py shell` 验收中 `get_auth()` 仍根据 `User.role` 返回内置 `USER`。
- 根因：独立 shell 进程没有像 Web 启动流程那样初始化 `DatabaseModelManage`，`get_auth()` 无法取得 xpack 的角色和工作空间模型，因而走了社区版兼容降级分支；这不是数据库映射未更新。
- 修复：权限验收脚本在调用 `get_auth()` 前检查并执行 `DatabaseModelManage.init()`，并精确清理上一次降级分支写入的目标用户角色/权限缓存；账号生成命令则将缓存失效改为 `transaction.on_commit()`，确保新映射提交后再对外可见。
- 验证：清理目标缓存并初始化注册表后，5 个账号的有效角色、目标权限、资源权限、活动状态和密码校验全部通过。

## ERR-305：演示账号验收只检查权限列表，未覆盖真实菜单接口

- 日期：2026-09-28
- 现象：`demo_platform_admin` 能登录且包含 `ADMIN` 和大量系统权限，但进入多个 V1 业务菜单时仍提示无权限。
- 根因：首次验收只校验密码、有效角色和权限列表，没有用真实登录上下文请求各菜单的代表性 API。平台管理员只在默认空间绑定了 `ADMIN`，而部分新增 V1 业务接口仍只接受当前工作空间的 `USER` 或 `WORKSPACE_MANAGE`。
- 修复：平台管理员保留系统 `ADMIN`，并在每个演示工作空间同时绑定 `WORKSPACE_MANAGE` 和 `USER`；新增真实登录后的跨模块只读 API 冒烟验收，不再以权限数量代替页面可用性。
- 验证：刷新角色映射后，5 个演示账号均通过真实登录、令牌鉴权和退出流程；跨用户管理、模型、知识库、工具、智能体、营销、监控、指标、API/事件编排、资源协调、演练、IVR 与变更管理的 46 个代表性只读请求全部通过（46/46）。

## ERR-306：统一响应实现路径误按单文件布局查找

- 日期：2026-09-28
- 现象：读取 `apps/common/result.py` 失败。
- 根因：项目的统一响应实现是 `apps/common/result/` 包，具体实现位于 `result/result.py`，不是单文件布局。
- 修复：先用 `rg --files apps/common/result` 确认真实结构，再读取 `__init__.py`、`result.py` 和 `api.py`。
- 验证：已读取实际实现，并据此按 HTTP 状态码与业务响应码双重验收。

## ERR-307：首轮真实 API 冒烟未按页面实际参数与复核职责配权

- 日期：2026-09-28
- 现象：46 个真实登录后只读请求中 43 个通过；工具分页返回业务码 500，质检账号访问服务助手复核返回 403。
- 根因：工具分页验收未像真实页面一样传入必需的 `folder_id` 和 `scope`；服务助手复核接口只允许系统管理员或工作空间管理员，与“质检与值班专员”的实际职责不一致。
- 修复：工具分页冒烟补充 `folder_id=default&scope=WORKSPACE`；复核列表接受工作空间级 `APPLICATION_CHAT_LOG_READ`，复核处理接受 `APPLICATION_CHAT_LOG_ANNOTATION`，同时保留管理员兼容路径，并为质检演示角色增加标注权限。
- 验证：`application.test_service_answer_review` 5 条测试全部通过；5 个演示账号完整 API 冒烟重跑 46/46 通过，工具分页和服务助手复核均不再报错。

## ERR-308：智能体子页面显示权限与兼容接口门禁不一致

- 日期：2026-09-28
- 现象：AI 与知识工程师能够进入智能体详情，但“设置”和“对话用户”子页面请求返回无权限；新增回归首次又把兼容接口的 HTTP 200 误判为业务成功。
- 根因：前端入口按智能体资源级 `APPLICATION_*` 权限判断，`xpack_lite` 的智能体展示设置和对话用户授权接口却硬编码要求 `WORKSPACE_MANAGE`；同时这些兼容接口把业务错误码放在 JSON `code` 中，不能只断言 HTTP 状态。
- 修复：智能体设置分别按资源级 `APPLICATION_READ/EDIT` 校验，对话用户分别按 `APPLICATION_CHAT_USER_READ/EDIT` 校验，保留工作空间管理员兼容路径并校验资源确属目标工作空间；回归同时断言 HTTP 状态和 JSON 业务码。
- 验证：资源权限与原有守卫共 8 条测试全部通过；AI 工程师真实登录后，智能体详情、设置、对话用户组、用户组成员及退出 5/5 通过；`manage.py check` 无错误。

## ERR-309：代码内接口回归通过但运行中的开发后端未加载新代码

- 日期：2026-09-28
- 现象：Django `APIClient` 使用 AI 工程师真实登录后 5 项接口全部通过，但请求正在监听 `127.0.0.1:8080` 的服务时，智能体设置和对话用户 3 项仍返回业务码 403。
- 根因：8080 后端进程早于本次代码修改启动，且实际未发生自动重载；只运行进程内测试不能证明浏览器正在访问的服务已加载修复。
- 修复：精确重启 8080 后端，再用同一演示账号通过真实 HTTP 登录、请求和退出。
- 验证：精确重启 8080 后端后，通过 `127.0.0.1:8080` 真实 HTTP 完成 AI 工程师登录、智能体详情、设置、对话用户组、用户组成员和退出，5/5 通过。

## ERR-310：服务助手复核后端已授权但前端菜单仍对质检角色隐藏

- 日期：2026-09-29
- 现象：质检值班专员调用服务助手复核接口已经通过，但按角色演示时在顶部导航中看不到“服务助手复核”入口。
- 根因：后端已按 `APPLICATION_CHAT_LOG_READ` / `APPLICATION_CHAT_LOG_ANNOTATION` 开放列表与处置权限，前端顶级路由仍只允许系统管理员和工作空间管理员，菜单可见性与接口门禁没有同步。
- 修复：服务助手复核路由增加工作空间级 `APPLICATION_CHAT_LOG_READ` 菜单权限；处置动作仍由后端 `APPLICATION_CHAT_LOG_ANNOTATION` 独立校验，避免只读用户获得写权限。
- 验证：目标路由 ESLint、前端类型检查和生产构建通过；质检演示稿以该真实导航路径为准。

## ERR-311：推荐引擎配置弹窗直接克隆 Vue Proxy 导致点击无响应

- 日期：2026-10-02
- 现象：“精排策略”和“融合配置”按钮存在，弹窗组件也已实现，但点击后没有弹窗。
- 根因：点击处理函数对 `ref` 内部的深层响应式对象直接调用 `structuredClone()`；浏览器无法克隆 Vue Proxy，在更新弹窗可见状态前抛出 `DataCloneError`。
- 修复：统一通过 `structuredClone(toRaw(value))` 创建可编辑副本。
- 验证：目标文件 ESLint、前端类型检查、生产构建通过；真实浏览器在已有发布版本 v3 下成功打开精排策略与融合配置弹窗，复选框取消/勾选正常，控制台 0 错误且原 6 条复选框属性警告消失。

## ERR-312：推荐引擎组合补丁因重复导入假设失配

- 日期：2026-10-02
- 现象：首次组合补丁在类型导入区域找不到预期的重复 `RecommendationModelStatus` 行，整组补丁未应用。
- 根因：终端截取内容被误读为重复导入，组合补丁包含了未经精确核对的上下文。
- 修复：重新读取准确行段，将代码修复与经验文档拆成最小补丁分别应用。
- 验证：代码补丁与规则补丁均已成功应用。

## ERR-313：zsh 未命中的请求工具通配符中断检索

- 日期：2026-10-02
- 现象：检索前端鉴权实现时把 `ui/src/utils/request*` 作为路径参数，zsh 在执行 `rg` 前报 `no matches found`。
- 根因：再次对不确定是否存在的路径使用了裸通配符。
- 修复：后续先通过 `rg --files ui/src` 确认实际请求模块路径，再传入明确文件；不再对可选路径使用 shell 通配符。
- 验证：已按明确路径完成临时登录态创建、真实页面验收、令牌精确撤销和临时状态文件删除。

## ERR-314：收尾验证记录补丁使用了过时原句

- 日期：2026-10-02
- 现象：更新 ERR-311、ERR-313 验证结论时，补丁锚点中的“类型检查”等文字与文件现状不一致，导致首次 `apply_patch` 未命中。
- 根因：根据工作摘要拟定补丁，未先读取错误记录文件中的当前原文。
- 修复：先用 `rg` 定位当前条目，再用完整现有验证行作为最小补丁锚点。
- 验证：ERR-311、ERR-313 已更新为实际完成状态，本条失败也已留痕。

## ERR-315：热更新后未确认一级分组便定位二级导航

- 日期：2026-10-02
- 现象：浏览器验收直接点击“能力沙盒”二级模块时，定位器报告无匹配元素。
- 根因：页面热更新后状态已重置为“总览与实例”，此时二级导航按设计不渲染；验收脚本沿用了上一次浏览器状态假设。
- 修复：每轮验收先读取当前页面状态，并显式切换到目标一级分组，等待二级导航可见后再操作。
- 验证：按“读取 AX 状态 → 点击一级分组控件 → 获取新状态 → 真实坐标点击吸顶导航”的顺序完成滚动位置复验，避免定位器自身滚动元素进入视口干扰结论。

## ERR-316：学习与错误记录误放在同一补丁文件上下文

- 日期：2026-10-02
- 现象：收尾时尝试同时更新滚动交互学习和浏览器验收错误，却把 ERR-315 的锚点放在 `LEARNINGS.md` 更新段内，补丁校验失败。
- 根因：组合补丁缺少第二个明确的 `Update File` 边界。
- 修复：先读取两个文件当前条目，再为 `LEARNINGS.md` 和 `ERRORS.md` 分别声明更新目标。
- 验证：学习结论、ERR-315 验证方式和本条错误均已成功写入。

## ERR-317：预演文案组合补丁依赖了不准确的相邻上下文

- 日期：2026-10-02
- 现象：批量清理“模拟”文案时，首个大补丁无法命中选项数组附近的预期上下文，整组补丁未应用。
- 根因：组合补丁把实际分散在不同位置的配置项假设为相邻内容，且没有先为每段改动读取精确上下文。
- 修复：按模板文案、导航配置、表单默认值和提示消息拆成最小补丁逐段应用。
- 验证：用户可见“模拟”文案已清理，目标文件后续通过检索与前端校验。

## ERR-318：同一补丁重复声明目标文件导致校验失败

- 日期：2026-10-02
- 现象：一次补丁同时修改预演页模板和样式时，将同一个 Vue 文件声明为两个更新目标，补丁工具直接拒绝执行。
- 根因：为区分模板与样式分段时重复写了 `Update File`，违反补丁工具对单次操作中目标文件唯一性的要求。
- 修复：同一文件的模板与样式改动合并到一个更新声明；跨文件文案再单独提交。
- 验证：预演页文案、英文计划标签隐藏和导航布局修复均已成功应用。

## ERR-319：包含两个相同默认值的组合补丁未精确命中

- 日期：2026-10-02
- 现象：继续清理 `Mock` 展示文案时，组合补丁未能命中第二处 `/mock/` 默认值，导致整组未应用。
- 根因：同一文件中存在两个文本相同但缩进不同的默认值，跨越多个远距离代码段的补丁上下文不够稳定。
- 修复：先读取两个默认值和消息所在的准确代码段，再将预演页与 API 编排页拆成独立最小补丁。
- 验证：两处默认地址均改为 `/sandbox/`，用户可见 `Mock` 文案已替换，内部接口枚举保持不变。

## ERR-320：本地向量服务未启用时管理命令不注册服务名

- 日期：2026-10-09
- 现象：执行 `manage.py start local_model -d` 时，命令提示 `local_model` 不是可选服务。
- 根因：`.env.local` 未启用 `TELECOM_AI_START_LOCAL_MODEL`；项目会据此从服务列表中移除 `local_model`，导致知识库检索依赖的 11636 端口未随前后端启动。
- 修复：不改写用户环境文件，仅在当前启动命令中设置 `TELECOM_AI_START_LOCAL_MODEL=true`，再启动独立向量服务。
- 验证：11636 已监听；使用数据库中真实向量模型 UUID 执行 `embed_query('你好')`，返回 384 维归一化向量；营销闭环测试智能体端到端对话的检索步骤恢复为 200。

## ERR-321：本地向量服务的 Gunicorn 启动器保留旧仓库路径

- 日期：2026-10-09
- 现象：启用 `local_model` 服务名后，启动过程报 `FileNotFoundError: gunicorn`；即使把 `.venv/bin` 前置到 `PATH` 仍然失败。
- 根因：`.venv/bin/gunicorn` 存在，但首行解释器仍指向旧目录 `/Users/zhaozhenchao/course/AI/MaxKB/.venv/bin/python`；内核因解释器不存在而返回文件不存在。
- 修复：不改写虚拟环境启动器，改用当前有效的 `./.venv/bin/python -m gunicorn` 显式启动本地向量服务。
- 验证：通过当前虚拟环境的 `python -m gunicorn` 启动后，11636 正常监听，真实 `embed_query()` 与智能体端到端对话均已通过。

## ERR-322：zsh 对未命中的 requirements 通配符提前报错

- 日期：2026-10-09
- 现象：检查 Gunicorn 依赖声明时把 `requirements*.txt` 直接作为命令参数，zsh 在执行 `rg` 前报 `no matches found`。
- 根因：再次对不确定是否存在的路径使用了裸通配符。
- 修复：后续依赖检索先通过 `rg --files` 获取明确文件，或只检查已经确认存在的 `pyproject.toml`、锁文件与虚拟环境模块。
- 验证：已确认 Gunicorn Python 模块存在，真正问题是启动器 shebang 指向旧仓库目录。

## ERR-323：临时字节码清理使用 `rm -f` 被安全策略拒绝

- 日期：2026-10-09
- 现象：清理已确认路径下的临时 `pyc` 时，组合命令因包含 `rm -f` 被执行策略拒绝，后续流式对话探针也未执行。
- 根因：对单个已确认文件仍使用了受限制的删除命令，并把清理与业务验收放在同一组合命令中。
- 修复：拆分操作；对明确的单文件使用 `unlink`，流式对话探针独立执行。
- 验证：临时字节码已删除；独立流式对话探针返回稳定问候，检索标记为跳过、引用段落为 0，且不再包含“资源未刷新”或“确认已办理”。

## ERR-324：`--noreload` 后端未加载新对话分流代码

- 日期：2026-10-09
- 现象：会话意图分流单元测试通过后，真实新会话发送“你好”仍返回旧的套餐办理状态文案。
- 根因：联调后端使用 `runserver --noreload`，修改 Python 文件后进程不会自动加载新代码。
- 修复：重启 8080 后端进程，再重新创建全新会话验收。
- 验证：阻塞与流式接口均返回稳定问候；检索详情为 `conversation_intent=greeting`、`retrieval_skipped=true`、引用段落数 0。

## ERR-325：在 `ui/` 目录误用仓库根目录 `.env.local` 相对路径

- 日期：2026-10-09
- 现象：恢复知识来源后组合执行接口探针与前端文本检查时，`source .env.local` 报文件不存在。
- 根因：前端检查要求在 `ui/` 执行，但后端命令基线中的 `.env.local` 和 `apps/manage.py` 都是仓库根目录相对路径，两类命令被错误混在同一工作目录。
- 修复：后端探针切回仓库根目录执行；前端文件检查再从根目录使用明确的 `ui/` 路径。
- 验证：公开应用配置重新返回 `show_source=true`，前端临时 `showParagraphSource` 计算属性已不存在。

## ERR-326：宿主机未安装 PostgreSQL `psql` 客户端

- 日期：2026-10-09
- 现象：执行初始化 SQL 空库验收时，宿主机报 `command not found: psql`。
- 根因：当前开发机只通过 Docker 运行 PostgreSQL，没有安装宿主机命令行客户端。
- 修复：使用已核对名称与端口映射的 `telecom-ai-postgres` 容器内 `psql`，初始化 SQL 通过标准输入传入；Django 仍从宿主机连接临时数据库。
- 验证：脚本在唯一临时库中连续执行两次均成功；全量迁移、`migrate --check`、`makemigrations --check --dry-run` 与 `manage.py check` 均通过；临时库已精确删除并确认不存在。

## ERR-327：zsh 对未确认存在的 Dockerfile 通配符提前报错

- 日期：2026-10-09
- 现象：联合检索部署配置时把仓库根目录 `Dockerfile*` 作为可选路径传给 `rg`，zsh 在命令执行前报 `no matches found`。
- 根因：没有先确认根目录是否存在匹配文件，又一次对可选路径使用了裸通配符。
- 修复：后续只检索已确认存在的 `docker/`、`docker-compose.yml` 和 `docker/.env.example`，或先通过 `rg --files` 获取明确路径。
- 验证：已使用 `docker-compose.yml`、`docker/.env.example`、`docker/start-app.sh` 和 `docker/Dockerfile.app` 明确路径完成部署默认值检查。

## ERR-328：Milvus 依赖核查再次传入未确认的 requirements 通配符

- 日期：2026-10-10
- 现象：核对 Milvus 客户端依赖时把可选的 `requirements/*.txt` 直接传给 `rg`，zsh 在该目录无匹配文件时提前报 `no matches found`。
- 根因：没有先用文件清单确认依赖文件，重复使用了可能无匹配的裸通配符。
- 修复：改为先通过 `rg --files` 获取实际存在的依赖清单，再对明确文件执行检索。
- 验证：通过文件清单确认当前依赖入口只有 `pyproject.toml`；其中没有 Milvus/PyMilvus/Zilliz 依赖，向量存储注册表和运行回退实现均只有 PostgreSQL `pg_vector`。

## ERR-329：前端环境目录检索未先确认文件清单

- 日期：2026-10-14
- 现象：核对 Vite 本地端口时直接对 `ui/env` 执行 `rg`，命令因没有检索到匹配项返回退出码 1。
- 根因：没有先确认环境文件名称和内容格式；首次文件清单还遗漏了被忽略规则覆盖的 `ui/env/.env`。
- 修复：先查看目录清单，再显式读取已确认存在的 `ui/env/.env` 与 `.env.chat`。
- 验证：已确认管理端为 `3000/admin/`，对话端为 `3001/chat/`。

## ERR-330：营销对话数据核对时从错误的 Django 包导入 `Chat`

- 日期：2026-10-15
- 现象：执行只读 Django shell 探针时，`from chat.models import Chat` 报 `ImportError`。
- 根因：`Chat` 实际注册在 `application.models.application_chat`，`chat.models` 没有导出该模型。
- 修复：改用 `from application.models.application_chat import Chat`，后续仍按项目已注册应用标签执行管理命令。
- 验证：使用正确导入后重新执行营销任务、客户和对话归属只读统计。

## ERR-331：服务检查命令再次使用可能无匹配的 Compose 通配符

- 日期：2026-10-16
- 现象：定位本地向量服务时，将 `compose*.yml` 直接作为 `rg` 输入路径，zsh 因仓库中没有匹配文件而报 `no matches found`。
- 根因：虽然仓库存在 `docker-compose.yml`，但同时传入了未经文件清单确认的可选通配符，违反了可选路径先确认的约束。
- 修复：改用 `rg --files -g '*compose*.yml' -g '*compose*.yaml'` 获取真实文件列表，并只对已确认的 `.env.local` 与 `docker-compose.yml` 检索。
- 验证：后续检查成功识别本地向量服务监听 `127.0.0.1:11435`，且未再触发 zsh 通配符错误。

## ERR-332：退出 Ollama 桌面应用后后台服务仍监听端口

- 日期：2026-10-16
- 现象：执行 Ollama 应用退出并向已确认的 `ollama serve` 发送 `SIGTERM` 后，`11434` 端口在五秒内仍保持监听。
- 根因：Ollama 桌面应用及其后台服务的退出生命周期相互独立，普通应用退出或单次终止信号未能及时关闭后台服务。
- 修复：重新读取 `11434` 当前监听 PID 与命令，仅在仍确认为 `ollama serve` 时升级为强制终止，并再次检查端口。
- 验证：`11434` 与项目向量服务 `11636` 均已停止监听；PostgreSQL `5432`、Redis `6379` 和非项目的 CodeGeeX `11435` 仍正常监听。
