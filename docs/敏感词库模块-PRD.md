# 敏感词库模块 PRD

## 1. 背景

当前“户籍政策问答助手”使用知识库检索节点来做敏感词拦截，例如用户输入“我要投诉”“什么玩意儿”时，通过测试知识库命中后返回固定回复“您的问题小赵不能理解”。

这种方式可以验证流程，但不适合作为长期能力：

- 知识库检索依赖 embedding 或关键词分数，命中阈值不稳定。
- 敏感词属于规则匹配，不应消耗向量检索和大模型资源。
- 用户需要长期维护词库，包括手动录入、批量导入、URL 同步、启用停用、分类管理和命中测试。
- 后续不同应用可能需要绑定不同敏感词策略。

因此需要设计一个独立的“敏感词库”模块，为工作流提供稳定、可维护、可审计的前置检测能力。

## 2. 目标

### 2.1 产品目标

- 提供一个用户友好的敏感词维护入口。
- 支持手动维护、批量导入和远程 URL 同步。
- 支持在应用工作流中作为前置检测能力使用。
- 命中敏感词时可以直接返回配置文案，未命中时继续原有问答流程。
- 支持命中记录，便于排查误拦截和优化词库。

### 2.2 技术目标

- 敏感词检测不依赖大模型、不依赖向量检索。
- 检测逻辑低延迟、可缓存、可扩展。
- 第一版尽量不改工作流画布核心，优先通过“自定义工具”或“工具节点”接入。
- 后续可升级为原生工作流节点。

## 3. 非目标

第一版不做以下能力：

- 不做复杂内容安全审核模型。
- 不做语义级违规判断。
- 不替代知识库问答权限控制。
- 不做多租户外部 SaaS 同步平台。
- 不做细粒度合规报告和人工审核流。

## 4. 用户角色

### 管理员

- 创建和管理敏感词库。
- 配置远程同步源。
- 配置默认命中动作和默认回复。
- 将敏感词库绑定到应用或工作流。

### 应用配置人员

- 在工作流中选择敏感词检测工具或节点。
- 配置命中后的分支逻辑。
- 测试某个输入是否会命中。

### 普通聊天用户

- 无感使用。
- 输入命中敏感词时收到固定提示。

## 5. 核心场景

### 5.1 手动维护敏感词

管理员进入“敏感词库”页面，创建词库并录入词条：

- 我要投诉
- 什么玩意儿
- 投诉

保存后，工作流可立即使用最新词库。

### 5.2 批量导入

管理员粘贴多行文本或上传文件：

```text
我要投诉
什么玩意儿
投诉
```

系统解析、去重并写入词库。

### 5.3 URL 同步

管理员配置一个远程词库地址：

```text
https://example.com/sensitive_words.txt
```

系统支持手动同步和定时同步。同步后将词条保存到本地数据库，聊天运行时只读取本地缓存，不实时请求远程 URL。

### 5.4 工作流前置检测

应用工作流配置：

```text
开始
-> 敏感词检测工具
-> 判断器
   -> hit = true：指定回复
   -> hit = false：进入原有政策问答流程
```

命中时返回：

```text
您的问题小赵不能理解
```

未命中时继续：

```text
问题优化 -> 知识库检索 -> 重排 -> AI 回答
```

## 6. 功能需求

### 6.1 敏感词库管理

列表字段：

- 词库名称
- 描述
- 词条数量
- 默认动作
- 默认回复
- 状态
- 更新时间

操作：

- 新建词库
- 编辑词库
- 删除词库
- 启用/停用词库
- 查看词条
- 命中测试

### 6.2 敏感词条管理

词条字段：

- 词条内容
- 分类
- 匹配方式
- 处理动作
- 回复文案
- 来源
- 状态
- 更新时间

匹配方式：

- `contains`：包含匹配，默认。
- `exact`：完全匹配。
- `regex`：正则匹配，第一版可选。

处理动作：

- `block`：拦截并返回固定文案。
- `mark`：只标记命中，后续流程自行判断。
- `replace`：替换敏感词，第一版可选。

操作：

- 新增词条
- 编辑词条
- 删除词条
- 批量启用/停用
- 批量导入
- 批量删除
- 导出词条

### 6.3 批量导入

支持格式：

- 纯文本，一行一个词。
- CSV，字段包括 `word,category,match_type,action,reply`。
- JSON 数组，字段包括 `word,category,match_type,action,reply`。

导入规则：

- 自动去除首尾空白。
- 空行忽略。
- 重复词条跳过或更新，策略可配置。
- 导入完成后展示新增数、更新数、跳过数、失败数。

### 6.4 URL 同步

同步源字段：

- 名称
- URL
- 格式：`txt`、`csv`、`json`
- 同步周期
- 是否启用
- 最近同步时间
- 最近同步状态

同步规则：

- 支持立即同步。
- 支持定时同步。
- 同步失败需要记录错误信息。
- 远程 URL 只用于更新本地词库，不参与聊天实时检测。
- 需要 URL 白名单或可信域校验，避免 SSRF 风险。

### 6.5 命中测试

管理员输入测试文本：

```text
我要投诉
```

系统返回：

```json
{
  "hit": true,
  "words": ["我要投诉"],
  "action": "block",
  "reply": "您的问题小赵不能理解"
}
```

### 6.6 工作流工具接入

第一版建议实现为电信智能体自定义工具：

输入：

- `text`：用户问题。
- `lexicon_id`：敏感词库 ID。

输出：

```json
{
  "hit": true,
  "words": ["我要投诉"],
  "categories": ["complaint"],
  "action": "block",
  "reply": "您的问题小赵不能理解"
}
```

工作流判断：

```text
敏感词检测工具.result.hit = true
```

命中则进入指定回复节点，未命中则进入正常问答节点。

### 6.7 应用级绑定

后续可支持在应用配置页绑定敏感词库：

- 是否启用敏感词检测。
- 选择一个或多个敏感词库。
- 配置默认命中回复。
- 配置是否记录命中日志。

如果做应用级绑定，则运行时可以在聊天 API 入口做前置检测，用户不需要每个工作流都手动拖节点。

## 7. 数据结构建议

### 7.1 sensitive_lexicon

```text
id
workspace_id
name
desc
is_active
default_action
default_reply
created_by
create_time
update_time
```

### 7.2 sensitive_word

```text
id
lexicon_id
word
normalized_word
category
match_type
action
reply
is_active
source
source_key
create_time
update_time
```

### 7.3 sensitive_sync_source

```text
id
lexicon_id
name
url
format
sync_interval
is_active
last_sync_time
last_sync_status
create_time
update_time
```

### 7.4 sensitive_sync_log

```text
id
source_id
status
total_count
added_count
updated_count
skipped_count
failed_count
error_message
create_time
```

### 7.5 sensitive_hit_log

```text
id
workspace_id
application_id
chat_id
chat_record_id
lexicon_id
matched_words
input_text
action
reply
create_time
```

## 8. 检测逻辑

### 8.1 文本归一化

检测前对用户输入和词条做统一归一化：

- 去除首尾空白。
- 全角转半角。
- 英文转小写。
- 去除反引号等 Markdown 包裹符。
- 可选：去除空格和常见标点。

示例：

```text
我 要 投 诉 -> 我要投诉
`我要投诉` -> 我要投诉
```

### 8.2 第一版匹配算法

词条数量较少时，使用普通字符串匹配：

```text
for word in active_words:
    if word in normalized_text:
        hit
```

### 8.3 后续优化

如果词条量达到数万级，可升级为：

- AC 自动机。
- Redis 缓存词库。
- 按 workspace 或 lexicon 分组缓存。

## 9. 缓存策略

运行时不应每次查询数据库。

建议缓存 key：

```text
sensitive_lexicon:{workspace_id}:{lexicon_id}
```

缓存内容：

```json
{
  "version": "20260806103000",
  "words": []
}
```

刷新时机：

- 词条新增、编辑、删除。
- 词库启用/停用。
- URL 同步完成。

## 10. 接口建议

### 10.1 词库管理

```text
GET    /api/sensitive/lexicons
POST   /api/sensitive/lexicons
GET    /api/sensitive/lexicons/{id}
PUT    /api/sensitive/lexicons/{id}
DELETE /api/sensitive/lexicons/{id}
```

### 10.2 词条管理

```text
GET    /api/sensitive/lexicons/{id}/words
POST   /api/sensitive/lexicons/{id}/words
PUT    /api/sensitive/words/{word_id}
DELETE /api/sensitive/words/{word_id}
POST   /api/sensitive/lexicons/{id}/words/import
```

### 10.3 同步源

```text
GET    /api/sensitive/lexicons/{id}/sync_sources
POST   /api/sensitive/lexicons/{id}/sync_sources
PUT    /api/sensitive/sync_sources/{source_id}
DELETE /api/sensitive/sync_sources/{source_id}
POST   /api/sensitive/sync_sources/{source_id}/sync
GET    /api/sensitive/sync_sources/{source_id}/logs
```

### 10.4 命中测试

```text
POST /api/sensitive/lexicons/{id}/test
```

请求：

```json
{
  "text": "我要投诉"
}
```

响应：

```json
{
  "hit": true,
  "words": ["我要投诉"],
  "action": "block",
  "reply": "您的问题小赵不能理解"
}
```

## 11. 权限

- 词库应归属 workspace。
- workspace 管理员可创建、编辑、删除词库。
- 普通应用配置人员可选择已有词库，但不一定能编辑词库。
- 共享词库可设置为只读。
- 命中日志应避免向无权限用户泄露原始敏感输入。

## 12. 安全要求

- URL 同步需要限制协议，只允许 `http` 和 `https`。
- URL 同步需要可信域或白名单，避免 SSRF。
- 正则匹配需要限制复杂度，避免 ReDoS。
- 命中日志中的用户输入需要按系统日志策略保留和清理。
- 导入文件需要限制大小和格式。

## 13. 页面建议

### 13.1 敏感词库列表页

位置建议：

```text
系统管理 / 安全策略 / 敏感词库
```

或：

```text
资源管理 / 敏感词库
```

### 13.2 词库详情页

包含 tab：

- 词条
- 同步源
- 命中测试
- 命中日志
- 设置

### 13.3 工作流配置

第一版通过工具节点实现：

- 工具名称：敏感词检测
- 输入：`{{开始.question}}`
- 词库：选择某个词库

后续原生节点：

- 节点名称：敏感词检测
- 输入文本
- 词库选择
- 命中动作
- 默认回复

## 14. 迭代计划

### V1：最小可用

- 敏感词库和词条表。
- 后端检测函数。
- 批量粘贴导入。
- 命中测试接口。
- 自定义工具接入工作流。
- 命中返回结构化结果。

### V2：维护增强

- URL 同步。
- 同步日志。
- 文件导入导出。
- 分类管理。
- 命中日志。
- Redis 缓存。

### V3：产品化节点

- 工作流原生敏感词检测节点。
- 应用级绑定敏感词库。
- 多词库组合策略。
- 高性能 AC 自动机。
- 更细的动作策略：拦截、替换、标记、转人工。

## 15. 验收标准

### V1 验收

- 用户可以创建敏感词库。
- 用户可以新增、删除、批量导入词条。
- 用户可以输入文本测试命中结果。
- 工作流可以调用敏感词检测工具。
- 输入“我要投诉”时返回：

```text
您的问题小赵不能理解
```

- 输入“子女投靠落户条件”时不被拦截，继续进入政策问答流程。
- 检测过程不调用大模型，不调用向量检索。

### V2 验收

- 用户可以配置 URL 同步源。
- 用户可以手动触发同步。
- 同步结果有日志。
- 同步后的词条可以立即参与命中测试。
- URL 不可用时不影响聊天运行。

## 16. 当前项目落地建议

当前电信智能体已经支持工具节点和 Python 自定义工具。第一版建议不要直接改工作流画布节点系统，而是：

```text
1. 新增敏感词数据表和管理接口
2. 新增检测服务函数
3. 新建一个“敏感词检测”自定义工具
4. 在户籍政策问答助手工作流最前面调用该工具
5. 判断 result.hit 决定是否进入固定回复
```

这样风险最低，也便于后续再升级成原生节点。
