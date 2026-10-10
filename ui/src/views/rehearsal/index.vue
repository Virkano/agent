<template>
  <div ref="rehearsalPage" v-loading="loading" class="rehearsal-page">
    <section class="command-hero">
      <div>
        <h1>故障与场景预演</h1>
        <p class="hero-copy">
          从客户申告和指标变化出发，配置故障矩阵、随机因子、场景回放与分阶段上报，再完成处置、恢复、能力调用和结果报告。
        </p>
      </div>
      <div class="hero-actions">
        <el-button plain @click="rehearsalApi.downloadImportTemplate()">下载导入模板</el-button>
        <el-button type="primary" @click="openCreateDialog">新建预演实例</el-button>
      </div>
    </section>

    <nav class="workspace-nav" aria-label="预演功能分组">
      <button
        v-for="item in workspaceViews"
        :key="item.value"
        type="button"
        :class="{ active: activeWorkspace === item.value }"
        :aria-pressed="activeWorkspace === item.value"
        @click="switchWorkspace(item.value)"
      >
        <span class="workspace-index">{{ item.index }}</span>
        <span class="workspace-copy">
          <strong>{{ item.title }}</strong>
          <small>{{ item.description }}</small>
        </span>
        <em>{{ item.scope }}</em>
      </button>
    </nav>

    <div v-if="activeWorkspace !== 'overview'" class="module-nav" role="tablist" aria-label="当前分组功能">
      <button
        v-for="item in activeModuleViews"
        :key="item.value"
        type="button"
        role="tab"
        :aria-selected="activeModule === item.value"
        :class="{ active: activeModule === item.value }"
        @click="switchModule(item.value)"
      >
        <strong>{{ item.title }}</strong>
        <small>{{ item.description }}</small>
      </button>
    </div>

    <section v-show="activeWorkspace === 'overview'" class="metric-grid">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <small>{{ metric.hint }}</small>
      </article>
    </section>

    <section v-show="activeWorkspace === 'overview'" class="workflow-strip">
      <div class="section-heading compact">
        <div>
          <p class="eyebrow">CONTROL CHAIN</p>
          <h2>统一预演控制链</h2>
        </div>
      </div>
      <div class="workflow-steps fourteen-steps">
        <div v-for="(step, index) in workflowSteps" :key="step.title" class="workflow-step">
          <span class="step-index">{{ String(index + 1).padStart(2, '0') }}</span>
          <div>
            <strong>{{ step.title }}</strong>
            <small>{{ step.desc }}</small>
          </div>
        </div>
      </div>
    </section>

    <section v-show="activeWorkspace === 'overview'" class="content-grid">
      <article class="panel template-panel">
        <div class="section-heading">
          <div>
            <p class="eyebrow">DATA BLUEPRINT</p>
            <h2>申告模板</h2>
          </div>
          <span>{{ dashboard.templates.length }} 套</span>
        </div>
        <div class="template-list">
          <button
            v-for="item in dashboard.templates"
            :key="item.id"
            class="template-card"
            type="button"
            @click="chooseTemplate(item)"
          >
            <div class="template-symbol" :class="item.customer_type.toLowerCase()">
              {{ item.customer_type === 'PUBLIC' ? 'P' : 'E' }}
            </div>
            <div class="template-main">
              <div class="template-title">
                <strong>{{ item.name }}</strong>
                <el-tag size="small" effect="plain">V{{ item.version }}</el-tag>
              </div>
              <p>{{ item.code }}</p>
              <div class="tag-row">
                <span v-for="category in item.categories" :key="category">{{ category }}</span>
              </div>
            </div>
          </button>
        </div>
      </article>

      <article class="panel instance-panel">
        <div class="section-heading">
          <div>
            <p class="eyebrow">ACTIVE RUNS</p>
            <h2>预演实例</h2>
          </div>
          <el-button link type="primary" @click="refreshAll">刷新</el-button>
        </div>
        <el-table :data="dashboard.instances" max-height="332" empty-text="还没有预演实例">
          <el-table-column label="实例" min-width="210">
            <template #default="{ row }">
              <button class="instance-link" type="button" @click="openInstance(row)">
                <strong>{{ row.name }}</strong>
                <small>{{ row.code }}</small>
              </button>
            </template>
          </el-table-column>
          <el-table-column label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" effect="plain">
                {{ row.status_label }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="complaint_count" label="有效申告" width="92" />
          <el-table-column prop="batch_count" label="批次" width="70" />
          <el-table-column label="操作" width="90" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openInstance(row)">进入预演</el-button>
            </template>
          </el-table-column>
        </el-table>
      </article>
    </section>

    <section v-show="activeWorkspace === 'data' && activeModule === 'process'" class="panel process-panel">
      <div class="section-heading process-heading">
        <div>
          <p class="eyebrow">DYNAMIC DISPOSAL ENGINE · X19</p>
          <h2>处置进度</h2>
        </div>
        <div class="process-summary">
          <span><b>{{ dashboard.summary.process_running_count }}</b> 执行中</span>
          <span class="blocked"><b>{{ dashboard.summary.process_blocked_count }}</b> 已阻塞</span>
          <el-button plain @click="exportCurrentProcessRuns">导出进度</el-button>
        </div>
      </div>

      <div class="process-template-rail">
        <button
          v-for="template in dashboard.process_templates"
          :key="template.id"
          type="button"
          class="process-template-card"
          :class="{ active: processFilters.template_id === template.id }"
          @click="selectProcessTemplate(template)"
        >
          <div>
            <span>{{ template.customer_scope_label }} · V{{ template.version }}</span>
            <strong>{{ template.name }}</strong>
          </div>
          <small>{{ template.step_count }} 步 · {{ template.auto_advance ? '支持自动推进' : '人工推进' }}</small>
        </button>
      </div>

      <div class="filter-bar process-filter-bar">
        <el-select v-model="processFilters.instance_id" clearable placeholder="全部预演实例">
          <el-option
            v-for="item in dashboard.instances"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select v-model="processFilters.template_id" clearable placeholder="全部流程模板">
          <el-option
            v-for="item in dashboard.process_templates"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select v-model="processFilters.status" clearable placeholder="全部状态">
          <el-option label="待执行" value="PENDING" />
          <el-option label="执行中" value="RUNNING" />
          <el-option label="已阻塞" value="BLOCKED" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="已取消" value="CANCELLED" />
          <el-option label="失败" value="FAILED" />
        </el-select>
        <el-input
          v-model="processFilters.keyword"
          clearable
          placeholder="流程或实例名称"
          @keyup.enter="loadProcessRuns(1)"
        />
        <el-button type="primary" @click="loadProcessRuns(1)">查询</el-button>
        <el-button @click="resetProcessFilters">重置</el-button>
      </div>

      <el-table v-loading="processLoading" :data="processPage.items" empty-text="还没有处置流程">
        <el-table-column label="流程" min-width="230">
          <template #default="{ row }">
            <button class="instance-link" type="button" @click="openProcessRun(row)">
              <strong>{{ row.name }}</strong>
              <small>{{ row.code }} · {{ row.template_name }}</small>
            </button>
          </template>
        </el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="状态" width="96">
          <template #default="{ row }">
            <el-tag :type="processTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="当前步骤" min-width="145">
          <template #default="{ row }">{{ currentStepName(row) }}</template>
        </el-table-column>
        <el-table-column label="执行进度" min-width="180">
          <template #default="{ row }">
            <div class="progress-cell">
              <el-progress :percentage="row.progress_percent" :stroke-width="7" />
              <span>{{ row.completed_steps }}/{{ row.total_steps }} 步</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="推进" width="80">
          <template #default="{ row }">{{ row.auto_advance ? '自动' : '人工' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="92" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openProcessRun(row)">查看进度</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ processPage.total }} 条处置流程</span>
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="processPage.page"
          :page-size="processPage.page_size"
          :total="processPage.total"
          @current-change="loadProcessRuns"
        />
      </div>
    </section>

    <section v-show="activeWorkspace === 'data' && activeModule === 'data-simulation'" class="panel data-simulation-panel">
      <div class="section-heading simulation-heading">
        <div>
          <p class="eyebrow">SIMULATED SIGNAL LAB · X20</p>
          <h2>数据构造与趋势看板</h2>
        </div>
        <div class="simulation-summary">
          <span><b>{{ dashboard.summary.metric_batch_count }}</b> 指标批次</span>
          <span><b>{{ dashboard.summary.sentiment_batch_count }}</b> 舆情批次</span>
          <span><b>{{ dashboard.summary.data_point_count }}</b> 时序点</span>
          <el-button plain :loading="dataExporting" @click="exportCurrentDataSimulations">导出数据</el-button>
          <el-button type="primary" @click="openDataCreate()">新建趋势数据</el-button>
        </div>
      </div>

      <div class="simulation-template-rail">
        <button
          v-for="template in dashboard.data_templates"
          :key="template.id"
          type="button"
          class="simulation-template-card"
          :class="template.kind.toLowerCase()"
          @click="openDataCreate(template)"
        >
          <span class="simulation-template-code">{{ template.code }} · V{{ template.version }}</span>
          <strong>{{ template.name }}</strong>
          <p>{{ template.description }}</p>
          <div>
            <span>{{ template.field_count }} 个字段</span>
            <span>{{ template.kind_label }}</span>
          </div>
        </button>
      </div>

      <div class="filter-bar data-filter-bar">
        <el-select v-model="dataFilters.instance_id" clearable placeholder="全部预演实例">
          <el-option
            v-for="item in dashboard.instances"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select v-model="dataFilters.kind" clearable placeholder="数据类型">
          <el-option label="指标趋势" value="METRIC" />
          <el-option label="舆情趋势" value="SENTIMENT" />
        </el-select>
        <el-select v-model="dataFilters.tag" clearable placeholder="业务标签">
          <el-option
            v-for="item in dashboard.data_tag_counts"
            :key="item.name"
            :label="`${item.name} · ${item.count}`"
            :value="item.name"
          />
        </el-select>
        <el-input
          v-model="dataFilters.keyword"
          clearable
          placeholder="批次、模板或实例"
          @keyup.enter="loadDataSimulations(1)"
        />
        <el-button type="primary" @click="loadDataSimulations(1)">查询</el-button>
        <el-button @click="resetDataFilters">重置</el-button>
      </div>

      <el-table v-loading="dataLoading" :data="dataPage.items" empty-text="还没有数据批次">
        <el-table-column label="数据批次" min-width="235">
          <template #default="{ row }">
            <button class="instance-link" type="button" @click="openDataSimulation(row)">
              <strong>{{ row.name }}</strong>
              <small>{{ row.code }} · V{{ row.version }}</small>
            </button>
          </template>
        </el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="类型" width="98">
          <template #default="{ row }">
            <el-tag :type="dataKindTagType(row.kind)" effect="plain">{{ row.kind_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间范围" min-width="225">
          <template #default="{ row }">{{ formatTimeRange(row.time_start, row.time_end) }}</template>
        </el-table-column>
        <el-table-column prop="point_count" label="点数" width="70" />
        <el-table-column label="标签" min-width="150">
          <template #default="{ row }">
            <div class="tag-row"><span v-for="tag in row.tags" :key="tag">{{ tag }}</span></div>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="92" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDataSimulation(row)">查看趋势</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ dataPage.total }} 个数据批次</span>
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="dataPage.page"
          :page-size="dataPage.page_size"
          :total="dataPage.total"
          @current-change="loadDataSimulations"
        />
      </div>
    </section>

    <section v-show="activeWorkspace === 'data' && activeModule === 'data-model'" class="panel data-model-panel">
      <div class="section-heading model-heading">
        <div>
          <p class="eyebrow">REHEARSAL DATA MODEL · X23</p>
          <h2>预演数据模型</h2>
        </div>
        <div class="model-summary">
          <span><b>{{ dashboard.summary.data_model_count }}</b> 模型</span>
          <span><b>{{ dashboard.summary.data_model_version_count }}</b> 版本</span>
          <span class="warning"><b>{{ dashboard.summary.data_model_warn_count }}</b> 质量提醒</span>
          <el-button type="primary" @click="openDataModelCreate()">构建数据模型</el-button>
        </div>
      </div>

      <div class="model-flow-strip">
        <article>
          <span>01</span>
          <strong>构建策略</strong>
          <small>全量实例、场景关联或故障链路</small>
        </article>
        <article>
          <span>02</span>
          <strong>转换器</strong>
          <small>统一转换成可回放的 canonical schema</small>
        </article>
        <article>
          <span>03</span>
          <strong>加载记录</strong>
          <small>每次刷新生成版本、校验和加载审计</small>
        </article>
        <article>
          <span>04</span>
          <strong>场景关联</strong>
          <small>把剧本、时序、告警和工单串到同一血缘</small>
        </article>
      </div>

      <div class="filter-bar model-filter-bar">
        <el-select v-model="dataModelFilters.instance_id" clearable placeholder="全部预演实例">
          <el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="dataModelFilters.build_strategy" clearable placeholder="构建策略">
          <el-option label="全量实例构建" value="FULL_INSTANCE" />
          <el-option label="场景关联构建" value="SCENE_LINKED" />
          <el-option label="故障链路构建" value="FAULT_CHAIN" />
        </el-select>
        <el-select v-model="dataModelFilters.quality_status" clearable placeholder="质量状态">
          <el-option label="校验通过" value="PASS" />
          <el-option label="存在提醒" value="WARN" />
          <el-option label="校验失败" value="FAIL" />
        </el-select>
        <el-input
          v-model="dataModelFilters.keyword"
          clearable
          placeholder="模型、实例或转换器"
          @keyup.enter="loadDataModels(1)"
        />
        <el-button type="primary" @click="loadDataModels(1)">查询</el-button>
        <el-button @click="resetDataModelFilters">重置</el-button>
      </div>

      <el-table v-loading="dataModelLoading" :data="dataModelPage.items" empty-text="还没有预演数据模型">
        <el-table-column label="数据模型" min-width="240">
          <template #default="{ row }">
            <button class="instance-link" type="button" @click="openDataModel(row)">
              <strong>{{ row.name }}</strong>
              <small>{{ row.code }} · {{ row.transformer_code }}</small>
            </button>
          </template>
        </el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="策略" width="128">
          <template #default="{ row }">{{ row.build_strategy_label }}</template>
        </el-table-column>
        <el-table-column label="质量" width="104">
          <template #default="{ row }">
            <el-tag :type="dataModelQualityTagType(row.quality_status)" effect="dark">
              {{ row.quality_status_label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="版本" width="90">
          <template #default="{ row }">V{{ row.current_version }}</template>
        </el-table-column>
        <el-table-column label="来源规模" min-width="190">
          <template #default="{ row }">{{ dataModelSourceSummary(row) }}</template>
        </el-table-column>
        <el-table-column label="关联场景" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">{{ row.scene_run_name || '未绑定' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openDataModel(row)">详情</el-button>
            <el-button link type="primary" @click="reloadDataModel(row)">重新加载</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ dataModelPage.total }} 个数据模型</span>
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="dataModelPage.page"
          :page-size="dataModelPage.page_size"
          :total="dataModelPage.total"
          @current-change="loadDataModels"
        />
      </div>
    </section>

    <section v-show="activeWorkspace === 'data' && activeModule === 'traceback'" class="panel traceback-panel">
      <div class="section-heading traceback-heading">
        <div>
          <p class="eyebrow">DATA TRACEBACK · X25</p>
          <h2>数据动态回溯</h2>
        </div>
        <div class="traceback-summary">
          <span><b>{{ dashboard.summary.traceback_count }}</b> 快照</span>
          <span><b>{{ dashboard.summary.traceback_ready_count }}</b> 可回放</span>
          <el-button plain :loading="tracebackExporting" @click="exportCurrentTracebacks">导出回溯</el-button>
          <el-button type="primary" @click="openTracebackCreate()">生成回溯</el-button>
        </div>
      </div>

      <div class="traceback-flow-strip">
        <article><span>01</span><strong>聚合事实</strong><small>申告、指标、舆情、处置、场景、告警和工单</small></article>
        <article><span>02</span><strong>锁定窗口</strong><small>全量实例、故障窗口或自定义时间范围</small></article>
        <article><span>03</span><strong>对比节点</strong><small>识别首末信号、状态分布和跨节点转移</small></article>
        <article><span>04</span><strong>固化回放</strong><small>保存校验和快照，支持详情追溯与 CSV 导出</small></article>
      </div>

      <div class="filter-bar traceback-filter-bar">
        <el-select v-model="tracebackFilters.instance_id" clearable placeholder="全部预演实例">
          <el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="tracebackFilters.scope" clearable placeholder="回溯范围">
          <el-option label="全量实例" value="FULL_INSTANCE" />
          <el-option label="故障窗口" value="INCIDENT_WINDOW" />
          <el-option label="自定义窗口" value="CUSTOM" />
        </el-select>
        <el-select v-model="tracebackFilters.status" clearable placeholder="快照状态">
          <el-option label="已生成" value="READY" />
          <el-option label="无回溯数据" value="EMPTY" />
          <el-option label="已归档" value="ARCHIVED" />
        </el-select>
        <el-select v-model="tracebackFilters.kind" clearable placeholder="事件类型">
          <el-option v-for="item in tracebackKindOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-input
          v-model="tracebackFilters.keyword"
          clearable
          placeholder="回溯名称、编号或实例"
          @keyup.enter="loadTracebacks(1)"
        />
        <el-button type="primary" @click="loadTracebacks(1)">查询</el-button>
        <el-button @click="resetTracebackFilters">重置</el-button>
      </div>

      <el-table v-loading="tracebackLoading" :data="tracebackPage.items" empty-text="还没有数据回溯快照">
        <el-table-column label="回溯快照" min-width="250">
          <template #default="{ row }">
            <button class="instance-link" type="button" @click="openTraceback(row)">
              <strong>{{ row.name }}</strong>
              <small>{{ row.code }} · {{ formatTime(row.generated_at) }}</small>
            </button>
          </template>
        </el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="范围 / 状态" width="150">
          <template #default="{ row }">
            <div class="traceback-state-cell">
              <span>{{ row.scope_label }}</span>
              <el-tag :type="tracebackStatusTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="事件构成" min-width="230">
          <template #default="{ row }">
            <div class="traceback-kind-chips">
              <span v-for="item in tracebackKindEntries(row)" :key="item.kind">{{ item.label }} {{ item.count }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="关键窗口" min-width="225">
          <template #default="{ row }">{{ formatTimeRange(row.summary.first_event_at || null, row.summary.last_event_at || null) }}</template>
        </el-table-column>
        <el-table-column label="节点 / 转移" width="112">
          <template #default="{ row }">{{ row.summary.node_count || 0 }} / {{ row.summary.transition_count || 0 }}</template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }"><el-button link type="primary" @click="openTraceback(row)">查看回放</el-button></template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ tracebackPage.total }} 个回溯快照</span>
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="tracebackPage.page"
          :page-size="tracebackPage.page_size"
          :total="tracebackPage.total"
          @current-change="loadTracebacks"
        />
      </div>
    </section>

    <section v-show="activeWorkspace === 'data' && activeModule === 'record'" class="panel record-panel">
      <div class="section-heading record-heading">
        <div>
          <p class="eyebrow">SIMULATION ARCHIVE · X26</p>
          <h2>预演记录查询</h2>
        </div>
        <div class="record-heading-actions">
          <span><b>{{ simulationRecordPage.summary.total }}</b> 条统一记录</span>
          <el-button plain :loading="simulationRecordExporting" @click="exportCurrentSimulationRecords">导出记录</el-button>
        </div>
      </div>

      <div class="record-scoreboard">
        <article><small>ALL RECORDS</small><strong>{{ simulationRecordPage.summary.total }}</strong><span>跨 8 类预演事实</span></article>
        <article class="success"><small>SUCCEEDED</small><strong>{{ simulationRecordPage.summary.succeeded }}</strong><span>已形成明确结果</span></article>
        <article class="running"><small>IN FLIGHT</small><strong>{{ simulationRecordPage.summary.running }}</strong><span>仍在运行链路中</span></article>
        <article class="attention"><small>ATTENTION</small><strong>{{ simulationRecordPage.summary.attention }}</strong><span>阻塞、部分成功或待确认</span></article>
        <article class="failed"><small>FAILED</small><strong>{{ simulationRecordPage.summary.failed }}</strong><span>保留失败证据</span></article>
        <article><small>AVG DURATION</small><strong>{{ formatDuration(simulationRecordPage.summary.average_duration_seconds) }}</strong><span>当前筛选口径</span></article>
      </div>

      <div class="filter-bar record-filter-bar">
        <el-select v-model="simulationRecordFilters.instance_id" clearable placeholder="全部预演实例">
          <el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="simulationRecordFilters.kind" clearable placeholder="全部记录类型">
          <el-option v-for="item in simulationRecordKindOptions" :key="item.value" :label="item.label" :value="item.value" />
        </el-select>
        <el-select v-model="simulationRecordFilters.state" clearable placeholder="全部统一结果">
          <el-option label="待执行" value="PENDING" />
          <el-option label="执行中" value="RUNNING" />
          <el-option label="已完成" value="SUCCEEDED" />
          <el-option label="需关注" value="ATTENTION" />
          <el-option label="已失败" value="FAILED" />
        </el-select>
        <el-date-picker v-model="simulationRecordFilters.date_from" type="date" value-format="YYYY-MM-DD" placeholder="开始日期" />
        <el-date-picker v-model="simulationRecordFilters.date_to" type="date" value-format="YYYY-MM-DD" placeholder="结束日期" />
        <el-input
          v-model="simulationRecordFilters.keyword"
          clearable
          placeholder="记录、实例或结果摘要"
          @keyup.enter="loadSimulationRecords(1)"
        />
        <el-button type="primary" @click="loadSimulationRecords(1)">查询</el-button>
        <el-button @click="resetSimulationRecordFilters">重置</el-button>
      </div>

      <el-table v-loading="simulationRecordLoading" :data="simulationRecordPage.items" empty-text="还没有预演记录">
        <el-table-column label="记录" min-width="270">
          <template #default="{ row }">
            <button class="record-link" type="button" @click="openSimulationRecord(row)">
              <span :class="`record-kind ${row.kind.toLowerCase()}`">{{ simulationRecordKindCode(row.kind) }}</span>
              <span><strong>{{ row.name }}</strong><small>{{ row.code }} · {{ formatTime(row.update_time) }}</small></span>
            </button>
          </template>
        </el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="类型 / 次数" width="130">
          <template #default="{ row }"><span>{{ row.kind_label }}</span><br /><small>第 {{ row.occurrence_no }} 次</small></template>
        </el-table-column>
        <el-table-column label="统一结果" width="112">
          <template #default="{ row }"><el-tag :type="simulationRecordTagType(row.state)" effect="plain">{{ row.state_label }}</el-tag></template>
        </el-table-column>
        <el-table-column label="历史进度" min-width="160">
          <template #default="{ row }"><el-progress :percentage="row.progress_percent" :stroke-width="7" :show-text="false" /><small>{{ row.progress_percent }}% · {{ row.status_label }}</small></template>
        </el-table-column>
        <el-table-column prop="result_summary" label="结果摘要" min-width="260" show-overflow-tooltip />
        <el-table-column label="耗时" width="105">
          <template #default="{ row }">{{ formatDuration(row.duration_seconds) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="86" fixed="right">
          <template #default="{ row }"><el-button link type="primary" @click="openSimulationRecord(row)">下钻</el-button></template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ simulationRecordPage.total }} 条预演记录</span>
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="simulationRecordPage.page"
          :page-size="simulationRecordPage.page_size"
          :total="simulationRecordPage.total"
          @current-change="loadSimulationRecords"
        />
      </div>
    </section>

    <section v-show="activeWorkspace === 'fault' && activeModule === 'capability'" class="panel capability-panel">
      <div class="section-heading capability-heading">
        <div>
          <p class="eyebrow">CAPABILITY SANDBOX · X27</p>
          <h2>能力调用演练</h2>
        </div>
        <div class="capability-heading-actions">
          <span><b>{{ capabilityCallPage.summary.total }}</b> 次调用留痕</span>
          <el-button plain @click="openCapabilityMockDrawer">新建隔离能力</el-button>
        </div>
      </div>

      <div class="capability-scoreboard">
        <article><small>能力目录</small><strong>{{ dashboard.summary.capability_mock_count }}</strong><span>API 与原子能力</span></article>
        <article><small>ALL CALLS</small><strong>{{ capabilityCallPage.summary.total }}</strong><span>沙盒与重放总量</span></article>
        <article class="success"><small>SUCCEEDED</small><strong>{{ capabilityCallPage.summary.succeeded }}</strong><span>响应符合预期</span></article>
        <article class="danger"><small>ATTENTION</small><strong>{{ capabilityCallPage.summary.failed + capabilityCallPage.summary.timeout }}</strong><span>失败与超时证据</span></article>
        <article><small>AVG LATENCY</small><strong>{{ capabilityCallPage.summary.average_latency_ms }}ms</strong><span>当前筛选口径</span></article>
      </div>

      <div class="capability-workbench">
        <div class="capability-catalog">
          <div class="capability-subheading"><span>能力目录</span><small>{{ dashboard.capability_mocks.length }} 个可用版本</small></div>
          <button
            v-for="item in dashboard.capability_mocks"
            :key="item.id"
            type="button"
            class="capability-card"
            :class="{ active: capabilityInvokeForm.capability_id === item.id }"
            @click="selectCapabilityMock(item)"
          >
            <span :class="`capability-kind ${item.kind.toLowerCase()}`">{{ item.kind === 'API' ? 'API' : 'ATM' }}</span>
            <span class="capability-card-main">
              <strong>{{ item.name }}</strong>
              <small>{{ item.method }} · {{ item.endpoint }}</small>
              <em>V{{ item.version }} · 默认 {{ item.default_latency_ms }}ms</em>
            </span>
          </button>
        </div>

        <div class="sandbox-console">
          <div class="capability-subheading"><span>隔离调用台</span><small>不访问真实生产接口</small></div>
          <div class="sandbox-grid">
            <label><span>预演实例</span><el-select v-model="capabilityInvokeForm.instance_id" placeholder="选择实例"><el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
            <label><span>预期结果</span><el-select v-model="capabilityInvokeForm.expected_status"><el-option label="调用成功" value="SUCCEEDED" /><el-option label="调用失败" value="FAILED" /><el-option label="调用超时" value="TIMEOUT" /></el-select></label>
            <label><span>战情室分组</span><el-input v-model="capabilityInvokeForm.warroom_group" maxlength="64" /></label>
            <label><span>调用耗时（ms）</span><el-input-number v-model="capabilityInvokeForm.latency_ms" :min="0" :max="120000" :step="50" controls-position="right" /></label>
            <label class="wide"><span>请求参数 JSON</span><el-input v-model="capabilityInvokeForm.request_payload_text" type="textarea" :rows="6" /></label>
          </div>
          <div class="sandbox-footer">
            <span>{{ selectedCapabilityMock?.code || '先选择一项演练能力' }}</span>
            <el-button type="primary" :loading="capabilityInvoking" @click="invokeSelectedCapability">执行沙盒调用</el-button>
          </div>
        </div>
      </div>

      <div v-if="capabilityCallPage.warrooms.length" class="warroom-rail">
        <button
          v-for="room in capabilityCallPage.warrooms"
          :key="room.warroom_group"
          type="button"
          :class="{ active: capabilityCallFilters.warroom_group === room.warroom_group }"
          @click="filterWarroom(room.warroom_group)"
        >
          <small>WARROOM</small><strong>{{ room.warroom_group }}</strong><span>{{ room.total }} 次调用 · {{ room.attention }} 条关注</span>
        </button>
      </div>

      <div class="filter-bar capability-filter-bar">
        <el-select v-model="capabilityCallFilters.instance_id" clearable placeholder="全部预演实例"><el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        <el-select v-model="capabilityCallFilters.kind" clearable placeholder="全部能力类型"><el-option label="API 接口" value="API" /><el-option label="原子能力" value="ATOMIC" /></el-select>
        <el-select v-model="capabilityCallFilters.status" clearable placeholder="全部调用结果"><el-option label="调用成功" value="SUCCEEDED" /><el-option label="调用失败" value="FAILED" /><el-option label="调用超时" value="TIMEOUT" /></el-select>
        <el-input v-model="capabilityCallFilters.keyword" clearable placeholder="能力、实例、请求或战情室" @keyup.enter="loadCapabilityCalls(1)" />
        <el-button type="primary" @click="loadCapabilityCalls(1)">查询</el-button>
        <el-button @click="resetCapabilityCallFilters">重置</el-button>
      </div>

      <el-table v-loading="capabilityCallLoading" :data="capabilityCallPage.items" empty-text="还没有能力调用记录">
        <el-table-column label="调用" min-width="260">
          <template #default="{ row }"><button type="button" class="capability-call-link" @click="openCapabilityCall(row)"><span :class="`capability-kind ${row.capability_kind.toLowerCase()}`">{{ row.capability_kind === 'API' ? 'API' : 'ATM' }}</span><span><strong>{{ row.capability_name }}</strong><small>{{ row.request_id }}</small></span></button></template>
        </el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="次数 / 来源" width="120"><template #default="{ row }">第 {{ row.call_no }} 次<br /><small>{{ row.source === 'REPLAY' ? '详情重放' : '沙盒调用' }}</small></template></el-table-column>
        <el-table-column label="调用结果" width="112"><template #default="{ row }"><el-tag :type="capabilityStatusTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag></template></el-table-column>
        <el-table-column prop="warroom_group" label="战情室" min-width="150" show-overflow-tooltip />
        <el-table-column label="响应" width="130"><template #default="{ row }"><strong>HTTP {{ row.http_status }}</strong><br /><small>{{ row.latency_ms }}ms</small></template></el-table-column>
        <el-table-column label="调用时间" width="164"><template #default="{ row }">{{ formatTime(row.started_at) }}</template></el-table-column>
        <el-table-column label="操作" width="86" fixed="right"><template #default="{ row }"><el-button link type="primary" @click="openCapabilityCall(row)">详情</el-button></template></el-table-column>
      </el-table>
      <div class="pagination-row"><span>共 {{ capabilityCallPage.total }} 次调用</span><el-pagination background layout="prev, pager, next" :current-page="capabilityCallPage.page" :page-size="capabilityCallPage.page_size" :total="capabilityCallPage.total" @current-change="loadCapabilityCalls" /></div>
    </section>

    <section v-show="activeWorkspace === 'fault' && activeModule === 'fault-configuration'" class="panel fault-configuration-panel">
      <div class="section-heading fault-configuration-heading">
        <div>
          <p class="eyebrow">FAULT MATRIX · X28</p>
          <h2>故障配置</h2>
        </div>
        <div class="fault-configuration-heading-actions">
          <span><b>{{ faultConfigurationPage.summary.ready }}</b> 个版本可应用</span>
          <el-button type="primary" @click="openFaultConfigurationForm">新建故障配置</el-button>
        </div>
      </div>

      <div class="fault-scoreboard">
        <article><small>CONFIG VERSIONS</small><strong>{{ faultConfigurationPage.summary.total }}</strong><span>当前筛选版本</span></article>
        <article class="ready"><small>READY</small><strong>{{ faultConfigurationPage.summary.ready }}</strong><span>五项校验通过</span></article>
        <article class="draft"><small>DRAFT</small><strong>{{ faultConfigurationPage.summary.draft }}</strong><span>待补齐或复核</span></article>
        <article><small>BOUND INSTANCE</small><strong>{{ faultConfigurationPage.summary.bound_instances }}</strong><span>已固化配置快照</span></article>
      </div>

      <div class="fault-workbench">
        <aside class="fault-config-rail">
          <div class="capability-subheading"><span>配置版本</span><small>SCENE LINKED</small></div>
          <button
            v-for="item in faultConfigurationPage.items"
            :key="item.id"
            type="button"
            :class="{ active: faultConfigurationPreview?.id === item.id }"
            @click="selectFaultConfiguration(item)"
          >
            <span class="fault-version">V{{ item.version }}</span>
            <span><strong>{{ item.name }}</strong><small>{{ item.scenario_name }} · {{ item.topology_node_count }} 节点</small></span>
            <i :class="item.status.toLowerCase()">{{ item.status_label }}</i>
          </button>
        </aside>

        <div v-if="faultConfigurationPreview" class="fault-blueprint">
          <div class="fault-blueprint-head">
            <div><p class="eyebrow">{{ faultConfigurationPreview.code }} · V{{ faultConfigurationPreview.version }}</p><h3>{{ faultConfigurationPreview.name }}</h3><span>{{ faultConfigurationPreview.description || '版本化故障配置快照' }}</span></div>
            <el-tag :type="faultConfigurationStatusTagType(faultConfigurationPreview.status)" effect="dark">{{ faultConfigurationPreview.status_label }}</el-tag>
          </div>

          <div class="topology-board">
            <div class="topology-board-head"><span>TOPOLOGY SNAPSHOT</span><small>{{ faultConfigurationPreview.topology_snapshot.version || '未标记拓扑版本' }} · {{ faultConfigurationPreview.topology_link_count }} 条链路</small></div>
            <div class="topology-nodes">
              <article
                v-for="(node, index) in faultConfigurationPreview.topology_snapshot.nodes || []"
                :key="node.id"
                :class="faultNodeStateClass(node.state)"
              >
                <span>{{ String(index + 1).padStart(2, '0') }}</span><i></i><strong>{{ node.name }}</strong><small>{{ node.id }} · {{ node.type }}</small><em>{{ faultNodeStateLabel(node.state) }}</em>
              </article>
            </div>
            <div class="topology-links"><span v-for="link in faultConfigurationPreview.topology_snapshot.links || []" :key="`${link.source}-${link.target}`">{{ link.source }} → {{ link.target }} / {{ link.state || 'UNKNOWN' }}</span></div>
          </div>

          <div class="fault-policy-grid">
            <article><small>ALERT RULES</small><strong>{{ faultConfigurationPreview.alert_rule_count }} 条</strong><p>{{ faultConfigurationPreview.alert_rules.map((item) => item.name).join(' / ') }}</p></article>
            <article><small>TIMEOUT</small><strong>{{ faultConfigurationPreview.timeout_policy.overall_seconds || 0 }}s</strong><p>步骤 {{ faultConfigurationPreview.timeout_policy.step_seconds || 0 }}s · {{ faultConfigurationPreview.timeout_policy.on_timeout || '未配置' }}</p></article>
            <article><small>ACTIVE WINDOW</small><strong>{{ faultConfigurationPreview.active_window.start || '—' }}—{{ faultConfigurationPreview.active_window.end || '—' }}</strong><p>{{ faultConfigurationPreview.active_window.timezone || '未设置时区' }} · {{ faultConfigurationPreview.active_window.weekdays?.length || 0 }} 天</p></article>
            <article><small>EMERGENCY PLAN</small><strong>{{ faultConfigurationPreview.plan_step_count }} 步</strong><p>{{ faultConfigurationPreview.emergency_plan.name || '未绑定应急预案' }}</p></article>
          </div>

          <div class="fault-apply-bar">
            <div><span>应用到预演实例</span><small>绑定时保存不可变配置快照</small></div>
            <el-select v-model="faultConfigurationApplyForm.instance_id" placeholder="选择同场景活动实例"><el-option v-for="item in faultConfigurationInstances" :key="item.id" :label="item.name" :value="item.id" /></el-select>
            <el-button type="primary" :disabled="faultConfigurationPreview.status !== 'READY'" :loading="faultConfigurationOperating" @click="applySelectedFaultConfiguration">应用配置</el-button>
          </div>
        </div>
        <el-empty v-else description="暂无故障配置" />
      </div>

      <div class="filter-bar fault-configuration-filter-bar">
        <el-select v-model="faultConfigurationFilters.scenario_id" clearable placeholder="全部预演场景"><el-option v-for="item in dashboard.scenarios" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        <el-select v-model="faultConfigurationFilters.status" clearable placeholder="全部配置状态"><el-option label="待校验" value="DRAFT" /><el-option label="可应用" value="READY" /><el-option label="已归档" value="ARCHIVED" /></el-select>
        <el-select v-model="faultConfigurationFilters.bound" clearable placeholder="全部绑定状态"><el-option label="已绑定实例" value="true" /><el-option label="未绑定实例" value="false" /></el-select>
        <el-input v-model="faultConfigurationFilters.keyword" clearable placeholder="配置、场景或版本编号" @keyup.enter="loadFaultConfigurations(1)" />
        <el-button type="primary" @click="loadFaultConfigurations(1)">查询</el-button>
        <el-button @click="resetFaultConfigurationFilters">重置</el-button>
      </div>

      <el-table v-loading="faultConfigurationLoading" :data="faultConfigurationPage.items" empty-text="还没有故障配置">
        <el-table-column label="配置版本" min-width="250"><template #default="{ row }"><button type="button" class="fault-config-link" @click="openFaultConfiguration(row)"><span>V{{ row.version }}</span><i><strong>{{ row.name }}</strong><small>{{ row.code }}</small></i></button></template></el-table-column>
        <el-table-column prop="scenario_name" label="关联场景" min-width="170" show-overflow-tooltip />
        <el-table-column label="配置矩阵" min-width="230"><template #default="{ row }">{{ row.alert_rule_count }} 告警 · {{ row.topology_node_count }} 节点 · {{ row.plan_step_count }} 预案步骤</template></el-table-column>
        <el-table-column label="实例绑定" width="110"><template #default="{ row }">{{ row.bound_instance_count }} 个</template></el-table-column>
        <el-table-column label="状态" width="105"><template #default="{ row }"><el-tag :type="faultConfigurationStatusTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="190" fixed="right"><template #default="{ row }"><el-button link type="primary" @click="openFaultConfiguration(row)">详情</el-button><el-button link type="primary" :disabled="row.status === 'ARCHIVED'" @click="cloneFaultConfiguration(row)">克隆</el-button><el-button v-if="row.status === 'DRAFT'" link type="warning" @click="validateFaultConfiguration(row)">校验</el-button></template></el-table-column>
      </el-table>
      <div class="pagination-row"><span>共 {{ faultConfigurationPage.total }} 个配置版本</span><el-pagination background layout="prev, pager, next" :current-page="faultConfigurationPage.page" :page-size="faultConfigurationPage.page_size" :total="faultConfigurationPage.total" @current-change="loadFaultConfigurations" /></div>
    </section>

    <section v-show="activeWorkspace === 'fault' && activeModule === 'scene-replay'" class="panel scene-replay-panel">
      <div class="section-heading scene-replay-heading">
        <div>
          <p class="eyebrow">NETWORK REPLAY OSCILLOSCOPE · X29</p>
          <h2>场景动态回溯</h2>
        </div>
        <div class="scene-replay-heading-actions">
          <span><b>{{ sceneReplayPage.summary.ready }}</b> 个镜像可回放</span>
          <el-button type="primary" @click="openSceneReplayCreate">生成场景回溯</el-button>
        </div>
      </div>

      <div class="scene-replay-scoreboard">
        <article><small>REPLAY SNAPSHOTS</small><strong>{{ sceneReplayPage.summary.total }}</strong><span>不可变回放镜像</span></article>
        <article><small>TRAFFIC FRAMES</small><strong>{{ sceneReplayPage.summary.traffic_frames }}</strong><span>流量 / 告警 / 控制信号</span></article>
        <article class="attention"><small>NODE DELTAS</small><strong>{{ sceneReplayPage.summary.changed_nodes }}</strong><span>状态发生变化的节点</span></article>
        <article><small>AVG LATENCY</small><strong>{{ sceneReplayPage.summary.average_latency_ms }}ms</strong><span>能力流量平均时延</span></article>
      </div>

      <div class="scene-replay-workbench">
        <aside class="scene-replay-rail">
          <div class="capability-subheading"><span>回放镜像</span><small>IMMUTABLE</small></div>
          <button
            v-for="item in sceneReplayPage.items"
            :key="item.id"
            type="button"
            :class="{ active: selectedSceneReplay?.id === item.id }"
            @click="selectSceneReplay(item)"
          >
            <span>{{ item.code.slice(-6) }}</span>
            <i><strong>{{ item.name }}</strong><small>{{ item.traffic_frame_count }} 帧 · {{ item.changed_node_count }} 节点变化</small></i>
            <em>{{ item.status_label }}</em>
          </button>
        </aside>

        <div v-if="selectedSceneReplay" v-loading="sceneReplayDetailLoading" class="scene-replay-scope">
          <div class="replay-console-head">
            <div><p class="eyebrow">{{ selectedSceneReplay.code }} · {{ selectedSceneReplay.summary.topology_version || 'TOPOLOGY' }}</p><h3>{{ selectedSceneReplay.name }}</h3><span>{{ selectedSceneReplay.instance_name }} · 配置 V{{ selectedSceneReplay.fault_configuration_version || '—' }}</span></div>
            <el-button plain @click="openSceneReplay(selectedSceneReplay)">查看完整证据</el-button>
          </div>

          <div class="traffic-oscilloscope">
            <div class="traffic-toolbar">
              <button type="button" @click="moveReplayCursor(-1)">‹</button>
              <button type="button" class="play" @click="toggleSceneReplayPlayback">{{ sceneReplayPlaying ? 'Ⅱ' : '▶' }}</button>
              <button type="button" @click="moveReplayCursor(1)">›</button>
              <span>FRAME {{ String(currentSceneReplayFrame?.sequence_no || 0).padStart(3, '0') }} / {{ selectedSceneReplay.traffic_frames?.length || 0 }}</span>
              <strong>{{ currentSceneReplayFrame?.source_node || '—' }} → {{ currentSceneReplayFrame?.target_node || '—' }}</strong>
            </div>
            <el-slider v-model="sceneReplayCursor" :min="0" :max="Math.max((selectedSceneReplay.traffic_frames?.length || 1) - 1, 0)" :show-tooltip="false" />
            <div v-if="currentSceneReplayFrame" class="traffic-frame-card" :class="currentSceneReplayFrame.channel.toLowerCase()">
              <span>{{ currentSceneReplayFrame.channel_label }}</span><strong>{{ currentSceneReplayFrame.title }}</strong><small>{{ formatTime(currentSceneReplayFrame.occurred_at) }} · {{ currentSceneReplayFrame.protocol }} · {{ currentSceneReplayFrame.latency_ms }}ms</small><em>{{ currentSceneReplayFrame.status_label }}</em>
            </div>
            <el-empty v-else :image-size="54" description="当前镜像没有流量帧" />
          </div>

          <div class="topology-mirror-grid">
            <section>
              <header><span>BEFORE</span><small>配置拓扑快照</small></header>
              <button v-for="node in selectedSceneReplay.topology_before?.nodes || []" :key="node.id" type="button" :class="[faultNodeStateClass(node.state), { active: activeReplayNodeId === node.id }]" @click="activeReplayNodeId = node.id"><i></i><strong>{{ node.name }}</strong><small>{{ node.id }}</small><em>{{ faultNodeStateLabel(node.state) }}</em></button>
            </section>
            <section class="after">
              <header><span>AFTER</span><small>流量事实推演结果</small></header>
              <button v-for="node in selectedSceneReplay.topology_after?.nodes || []" :key="node.id" type="button" :class="[faultNodeStateClass(node.state), { active: activeReplayNodeId === node.id }]" @click="activeReplayNodeId = node.id"><i></i><strong>{{ node.name }}</strong><small>{{ node.id }}</small><em>{{ faultNodeStateLabel(node.state) }}</em></button>
            </section>
          </div>

          <div v-if="activeSceneReplayNode" class="node-trace-strip">
            <div><span>NODE TRACE</span><strong>{{ activeSceneReplayNode.node_name }}</strong><small>{{ activeSceneReplayNode.node_id }} · {{ activeSceneReplayNode.node_type }}</small></div>
            <b>{{ activeSceneReplayNode.before_state }} → {{ activeSceneReplayNode.after_state }}</b>
            <span>{{ activeSceneReplayNode.traffic_count }} 帧经过 · {{ activeSceneReplayNode.attention_count }} 帧需关注</span>
          </div>
        </div>
        <el-empty v-else description="先生成一个场景回溯镜像" />
      </div>

      <div class="filter-bar scene-replay-filter-bar">
        <el-select v-model="sceneReplayFilters.instance_id" clearable placeholder="全部预演实例"><el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        <el-select v-model="sceneReplayFilters.status" clearable placeholder="全部回放状态"><el-option label="可回放" value="READY" /><el-option label="无流量数据" value="EMPTY" /></el-select>
        <el-input v-model="sceneReplayFilters.node_id" clearable placeholder="节点编号" @keyup.enter="loadSceneReplays(1)" />
        <el-input v-model="sceneReplayFilters.keyword" clearable placeholder="镜像、实例或场景执行" @keyup.enter="loadSceneReplays(1)" />
        <el-button type="primary" @click="loadSceneReplays(1)">查询</el-button>
        <el-button @click="resetSceneReplayFilters">重置</el-button>
      </div>

      <el-table v-loading="sceneReplayLoading" :data="sceneReplayPage.items" empty-text="还没有场景动态回溯">
        <el-table-column label="回放镜像" min-width="270"><template #default="{ row }"><button type="button" class="scene-replay-link" @click="openSceneReplay(row)"><span>SR</span><i><strong>{{ row.name }}</strong><small>{{ row.code }}</small></i></button></template></el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="事实帧" width="100"><template #default="{ row }">{{ row.traffic_frame_count }} 帧</template></el-table-column>
        <el-table-column label="镜像差异" width="150"><template #default="{ row }">{{ row.changed_node_count }} 节点 · {{ row.changed_link_count }} 链路</template></el-table-column>
        <el-table-column label="状态" width="105"><template #default="{ row }"><el-tag :type="sceneReplayTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag></template></el-table-column>
        <el-table-column label="生成时间" width="164"><template #default="{ row }">{{ formatTime(row.generated_at) }}</template></el-table-column>
        <el-table-column label="操作" width="86" fixed="right"><template #default="{ row }"><el-button link type="primary" @click="openSceneReplay(row)">详情</el-button></template></el-table-column>
      </el-table>
      <div class="pagination-row"><span>共 {{ sceneReplayPage.total }} 个回放镜像</span><el-pagination background layout="prev, pager, next" :current-page="sceneReplayPage.page" :page-size="sceneReplayPage.page_size" :total="sceneReplayPage.total" @current-change="loadSceneReplays" /></div>
    </section>

    <section v-show="activeWorkspace === 'fault' && activeModule === 'fault-report'" class="panel fault-report-panel">
      <div class="section-heading fault-report-heading">
        <div>
          <p class="eyebrow">INCIDENT REPORTING TOWER · X30</p>
          <h2>故障上报</h2>
        </div>
        <div class="fault-report-heading-actions">
          <span><b>{{ faultReportPage.summary.active }}</b> 起处理中 · <b>{{ faultReportPage.summary.overdue }}</b> 起超时</span>
          <el-button type="primary" @click="openFaultReportCreate">发起故障上报</el-button>
        </div>
      </div>

      <div class="fault-report-scoreboard">
        <article><small>REPORT LEDGER</small><strong>{{ faultReportPage.summary.total }}</strong><span>版本化故障事实</span></article>
        <article class="active"><small>ACTIVE INCIDENTS</small><strong>{{ faultReportPage.summary.active }}</strong><span>已上报 / 处理中</span></article>
        <article :class="{ danger: faultReportPage.summary.overdue > 0 }"><small>SLA OVERDUE</small><strong>{{ faultReportPage.summary.overdue }}</strong><span>阶段时限已超时</span></article>
        <article><small>EVIDENCE REFS</small><strong>{{ faultReportPage.summary.attachments }}</strong><span>证据引用与元数据</span></article>
      </div>

      <div class="fault-report-workbench">
        <aside class="fault-report-template-rail">
          <div class="capability-subheading"><span>上报模板</span><small>VERSIONED</small></div>
          <article v-for="template in dashboard.fault_report_templates" :key="template.id">
            <header><span>V{{ template.version }}</span><strong>{{ template.name }}</strong><em>{{ template.default_level_label }}</em></header>
            <div><span v-for="(stage, index) in template.stage_definitions" :key="stage.code">{{ index + 1 }}. {{ stage.name }} · {{ stage.duration_minutes }}m</span></div>
          </article>
          <el-empty v-if="!dashboard.fault_report_templates.length" :image-size="54" description="暂无上报模板" />
        </aside>

        <div v-if="selectedFaultReport" v-loading="faultReportDetailLoading" class="fault-report-command-center">
          <header>
            <div><p class="eyebrow">{{ selectedFaultReport.code }} · {{ selectedFaultReport.instance_name }}</p><h3>{{ selectedFaultReport.title }}</h3><span>{{ selectedFaultReport.impact_scope || '未补充影响范围' }}</span></div>
            <div class="fault-report-level" :class="selectedFaultReport.level.toLowerCase()"><small>SEVERITY</small><strong>{{ selectedFaultReport.level_label }}</strong><em>{{ selectedFaultReport.status_label }}</em></div>
          </header>

          <div class="fault-report-stage-line">
            <article
              v-for="(stage, index) in selectedFaultReport.template_snapshot.stage_definitions || []"
              :key="stage.code"
              :class="{ done: index + 1 < selectedFaultReport.stage_index, current: stage.code === selectedFaultReport.current_stage_code }"
            >
              <span>{{ String(index + 1).padStart(2, '0') }}</span><strong>{{ stage.name }}</strong><small>{{ stage.owner_role }} · {{ stage.duration_minutes }} 分钟</small>
            </article>
          </div>

          <div class="fault-report-runtime">
            <div><span>CURRENT STAGE</span><strong>{{ selectedFaultReport.current_stage_name }}</strong><small>{{ selectedFaultReport.stage_owner_role || '待指定责任席位' }}</small></div>
            <div :class="{ overdue: faultReportCountdown.overdue }"><span>STAGE SLA</span><strong>{{ faultReportCountdown.text }}</strong><small>{{ formatTime(selectedFaultReport.stage_deadline_at) }} 截止</small></div>
            <div><span>PROGRESS</span><strong>{{ selectedFaultReport.progress_percent }}%</strong><small>{{ selectedFaultReport.stage_index }}/{{ selectedFaultReport.stage_count }} 阶段</small></div>
            <div><span>EVIDENCE</span><strong>{{ selectedFaultReport.attachment_count }}</strong><small>{{ selectedFaultReport.event_count }} 条审计事件</small></div>
          </div>

          <div class="fault-report-quick-actions">
            <el-button v-if="selectedFaultReport.allowed_actions.includes('SUBMITTED')" type="warning" @click="operateSelectedFaultReport('SUBMITTED')">正式上报</el-button>
            <el-button v-if="selectedFaultReport.allowed_actions.includes('ACCEPTED')" type="primary" @click="operateSelectedFaultReport('ACCEPTED')">受理故障</el-button>
            <el-button v-if="selectedFaultReport.allowed_actions.includes('STAGE_ADVANCED')" type="primary" plain @click="openFaultReportAction('STAGE_ADVANCED')">推进阶段</el-button>
            <el-button v-if="selectedFaultReport.allowed_actions.includes('ESCALATED')" type="danger" plain @click="openFaultReportAction('ESCALATED')">升级故障</el-button>
            <el-button v-if="selectedFaultReport.allowed_actions.includes('ATTACHMENT_ADDED')" @click="openFaultReportAction('ATTACHMENT_ADDED')">补充证据</el-button>
            <el-button v-if="selectedFaultReport.allowed_actions.includes('RECOVERED')" type="success" @click="openFaultReportAction('RECOVERED')">确认恢复</el-button>
            <el-button v-if="selectedFaultReport.allowed_actions.includes('CLOSED')" type="success" plain @click="openFaultReportAction('CLOSED')">关闭归档</el-button>
            <el-button plain @click="openFaultReport(selectedFaultReport)">完整事实链</el-button>
          </div>
        </div>
        <el-empty v-else description="还没有故障上报记录" />
      </div>

      <div class="filter-bar fault-report-filter-bar">
        <el-select v-model="faultReportFilters.instance_id" clearable placeholder="全部预演实例"><el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        <el-select v-model="faultReportFilters.status" clearable placeholder="全部上报状态"><el-option label="草稿" value="DRAFT" /><el-option label="已上报" value="REPORTED" /><el-option label="处理中" value="PROCESSING" /><el-option label="已恢复" value="RECOVERED" /><el-option label="已关闭" value="CLOSED" /></el-select>
        <el-select v-model="faultReportFilters.level" clearable placeholder="全部故障等级"><el-option label="一级故障" value="LEVEL_1" /><el-option label="二级故障" value="LEVEL_2" /><el-option label="三级故障" value="LEVEL_3" /><el-option label="四级故障" value="LEVEL_4" /></el-select>
        <el-select v-model="faultReportFilters.overdue" clearable placeholder="全部时限状态"><el-option label="仅看超时" value="true" /></el-select>
        <el-input v-model="faultReportFilters.keyword" clearable placeholder="编号、标题或影响范围" @keyup.enter="loadFaultReports(1)" />
        <el-button type="primary" @click="loadFaultReports(1)">查询</el-button>
        <el-button @click="resetFaultReportFilters">重置</el-button>
      </div>

      <el-table v-loading="faultReportLoading" :data="faultReportPage.items" empty-text="还没有故障上报记录" @row-click="selectFaultReport">
        <el-table-column label="故障事件" min-width="280"><template #default="{ row }"><button type="button" class="fault-report-link" @click.stop="openFaultReport(row)"><span :class="row.level.toLowerCase()">{{ faultReportLevelCode(row.level) }}</span><i><strong>{{ row.title }}</strong><small>{{ row.code }} · {{ row.instance_name }}</small></i></button></template></el-table-column>
        <el-table-column label="当前阶段" min-width="170"><template #default="{ row }"><strong>{{ row.current_stage_name }}</strong><small class="table-subtext">{{ row.stage_owner_role || '—' }} · {{ row.progress_percent }}%</small></template></el-table-column>
        <el-table-column label="阶段时限" width="150"><template #default="{ row }"><span :class="['countdown-cell', { overdue: reportCountdown(row).overdue }]">{{ reportCountdown(row).text }}</span></template></el-table-column>
        <el-table-column label="证据" width="80"><template #default="{ row }">{{ row.attachment_count }} 份</template></el-table-column>
        <el-table-column label="状态" width="100"><template #default="{ row }"><el-tag :type="faultReportStatusTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="86" fixed="right"><template #default="{ row }"><el-button link type="primary" @click.stop="openFaultReport(row)">详情</el-button></template></el-table-column>
      </el-table>
      <div class="pagination-row"><span>共 {{ faultReportPage.total }} 起故障上报</span><el-pagination background layout="prev, pager, next" :current-page="faultReportPage.page" :page-size="faultReportPage.page_size" :total="faultReportPage.total" @current-change="loadFaultReports" /></div>
    </section>

    <section v-show="activeWorkspace === 'fault' && activeModule === 'auxiliary'" class="panel auxiliary-simulation-panel">
      <div class="section-heading auxiliary-heading">
        <div>
          <p class="eyebrow">STOCHASTIC LAB · X31</p>
          <h2>辅助演练与结果报告</h2>
        </div>
        <div class="auxiliary-heading-actions">
          <span><b>{{ auxiliarySimulationPage.summary.triggered_factor_count }}</b> 项因子命中 · <b>{{ auxiliarySimulationPage.summary.anomaly_count }}</b> 个异常窗口</span>
          <el-button type="primary" @click="openAuxiliarySimulationCreate">组合随机因子</el-button>
        </div>
      </div>

      <div class="factor-catalog-grid">
        <article v-for="factor in dashboard.random_factor_catalog" :key="factor.code" :class="factor.category.toLowerCase()">
          <small>{{ factorCategoryLabel(factor.category) }} · {{ factor.distribution === 'NORMAL' ? '正态' : '均匀' }}</small>
          <strong>{{ factor.name }}</strong>
          <p>{{ factor.min_value }} — {{ factor.max_value }} {{ factor.unit }}</p>
          <span>{{ Math.round(factor.trigger_probability * 100) }}% 默认触发概率</span>
        </article>
      </div>

      <div v-if="selectedAuxiliarySimulation" v-loading="auxiliarySimulationDetailLoading" class="auxiliary-command-center">
        <div class="auxiliary-command-copy">
          <p class="eyebrow">{{ selectedAuxiliarySimulation.code }} · SEED {{ selectedAuxiliarySimulation.seed }}</p>
          <h3>{{ selectedAuxiliarySimulation.name }}</h3>
          <span>{{ selectedAuxiliarySimulation.summary.conclusion }}</span>
          <div><el-tag :type="selectedAuxiliarySimulation.status === 'ATTENTION' ? 'warning' : 'success'" effect="dark">{{ selectedAuxiliarySimulation.status_label }}</el-tag><small>SHA-256 {{ selectedAuxiliarySimulation.checksum.slice(0, 16) }}…</small></div>
        </div>
        <div class="auxiliary-mini-chart">
          <header><span>IMPACT CURVE</span><small>响应超时率 / 分钟</small></header>
          <svg viewBox="0 0 620 150" preserveAspectRatio="none" aria-label="辅助演练响应超时率趋势">
            <defs><linearGradient id="auxArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#e17152" stop-opacity=".42" /><stop offset="1" stop-color="#e17152" stop-opacity=".02" /></linearGradient></defs>
            <path :d="auxiliaryChartArea" fill="url(#auxArea)" />
            <polyline :points="auxiliaryChartPolyline" fill="none" stroke="#e17152" stroke-width="3" vector-effect="non-scaling-stroke" />
          </svg>
          <footer><span>0 MIN</span><strong>{{ selectedAuxiliarySimulation.anomaly_count }} ANOMALIES</strong><span>{{ selectedAuxiliarySimulation.duration_minutes }} MIN</span></footer>
        </div>
        <div class="auxiliary-stats-strip">
          <article v-for="item in selectedAuxiliarySimulation.statistics.slice(0, 4)" :key="item.code"><small>{{ item.name }}</small><strong>{{ item.peak }}</strong><span :class="{ rising: item.delta_percent > 0 }">{{ item.delta_percent > 0 ? '+' : '' }}{{ item.delta_percent }}%</span></article>
        </div>
      </div>
      <el-empty v-else description="还没有辅助演练批次" />

      <div class="filter-bar auxiliary-filter-bar">
        <el-select v-model="auxiliarySimulationFilters.instance_id" clearable placeholder="全部预演实例"><el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" /></el-select>
        <el-select v-model="auxiliarySimulationFilters.status" clearable placeholder="全部结果"><el-option label="演练完成" value="COMPLETED" /><el-option label="存在异常点" value="ATTENTION" /></el-select>
        <el-input v-model="auxiliarySimulationFilters.seed" clearable placeholder="随机种子" @keyup.enter="loadAuxiliarySimulations(1)" />
        <el-input v-model="auxiliarySimulationFilters.keyword" clearable placeholder="批次、实例或编号" @keyup.enter="loadAuxiliarySimulations(1)" />
        <el-button type="primary" @click="loadAuxiliarySimulations(1)">查询</el-button>
        <el-button @click="resetAuxiliarySimulationFilters">重置</el-button>
      </div>

      <el-table v-loading="auxiliarySimulationLoading" :data="auxiliarySimulationPage.items" empty-text="还没有辅助演练批次" @row-click="selectAuxiliarySimulation">
        <el-table-column label="演练批次" min-width="260"><template #default="{ row }"><button type="button" class="auxiliary-link" @click.stop="openAuxiliarySimulation(row)"><span>AUX</span><i><strong>{{ row.name }}</strong><small>{{ row.code }} · SEED {{ row.seed }}</small></i></button></template></el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="因子命中" width="112"><template #default="{ row }">{{ row.triggered_factor_count }}/{{ row.factor_count }} 项</template></el-table-column>
        <el-table-column label="异常窗口" width="104"><template #default="{ row }"><span :class="{ 'text-danger': row.anomaly_count }">{{ row.anomaly_count }} 个</span></template></el-table-column>
        <el-table-column label="状态" width="106"><template #default="{ row }"><el-tag :type="row.status === 'ATTENTION' ? 'warning' : 'success'" effect="plain">{{ row.status_label }}</el-tag></template></el-table-column>
        <el-table-column label="操作" width="190" fixed="right"><template #default="{ row }"><el-button link type="primary" @click.stop="openAuxiliarySimulation(row)">分析</el-button><el-button link type="success" @click.stop="quickExportAuxiliary(row, 'pdf')">PDF</el-button><el-button link @click.stop="quickExportAuxiliary(row, 'xlsx')">Excel</el-button></template></el-table-column>
      </el-table>
      <div class="pagination-row"><span>共 {{ auxiliarySimulationPage.total }} 个随机因子批次</span><el-pagination background layout="prev, pager, next" :current-page="auxiliarySimulationPage.page" :page-size="auxiliarySimulationPage.page_size" :total="auxiliarySimulationPage.total" @current-change="loadAuxiliarySimulations" /></div>
    </section>

    <section v-show="activeWorkspace === 'scene' && activeModule === 'scene-library'" class="panel scene-library-panel">
      <div class="section-heading library-heading">
        <div>
          <p class="eyebrow">SCENE LIBRARY · X24</p>
          <h2>预演场景库</h2>
        </div>
        <div class="library-summary">
          <span><b>{{ dashboard.summary.scene_library_count }}</b> 版本</span>
          <span><b>{{ dashboard.summary.scene_library_ready_count }}</b> 可复用</span>
          <el-button type="primary" @click="openSceneLibraryCreate()">新建场景库</el-button>
        </div>
      </div>

      <div class="library-flow-strip">
        <article>
          <span>01</span>
          <strong>绑定剧本</strong>
          <small>固化步骤快照和默认执行配置</small>
        </article>
        <article>
          <span>02</span>
          <strong>关联实例</strong>
          <small>绑定实例、流程模板与数据模型</small>
        </article>
        <article>
          <span>03</span>
          <strong>版本克隆</strong>
          <small>从已有场景复制出新的可复用版本</small>
        </article>
        <article>
          <span>04</span>
          <strong>一键执行</strong>
          <small>从库拉起场景执行并记录审计</small>
        </article>
      </div>

      <div class="scene-script-rail library-script-rail">
        <button
          v-for="script in dashboard.scene_scripts"
          :key="script.id"
          type="button"
          class="scene-script-card library-script-card"
          :class="{ active: sceneLibraryFilters.script_id === script.id }"
          @click="selectSceneLibraryScript(script)"
        >
          <span>{{ script.code }} · V{{ script.version }}</span>
          <strong>{{ script.name }}</strong>
          <p>{{ script.description }}</p>
          <small>{{ script.step_count }} 步 · {{ script.scenario_name }}</small>
        </button>
      </div>

      <div class="filter-bar library-filter-bar">
        <el-select v-model="sceneLibraryFilters.scenario_id" clearable placeholder="全部预演场景">
          <el-option v-for="item in dashboard.scenarios" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="sceneLibraryFilters.status" clearable placeholder="全部状态">
          <el-option label="草稿" value="DRAFT" />
          <el-option label="可复用" value="READY" />
          <el-option label="已归档" value="ARCHIVED" />
        </el-select>
        <el-select v-model="sceneLibraryFilters.visibility" clearable placeholder="可见范围">
          <el-option label="工作空间可用" value="WORKSPACE" />
          <el-option label="仅创建人可用" value="PRIVATE" />
        </el-select>
        <el-input
          v-model="sceneLibraryFilters.keyword"
          clearable
          placeholder="场景库、剧本或实例"
          @keyup.enter="loadSceneLibraries(1)"
        />
        <el-button type="primary" @click="loadSceneLibraries(1)">查询</el-button>
        <el-button @click="resetSceneLibraryFilters">重置</el-button>
      </div>

      <el-table v-loading="sceneLibraryLoading" :data="sceneLibraryPage.items" empty-text="还没有预演场景库">
        <el-table-column label="场景库" min-width="260">
          <template #default="{ row }">
            <button class="instance-link" type="button" @click="openSceneLibrary(row)">
              <strong>{{ row.name }}</strong>
              <small>{{ row.code }} · V{{ row.version }} · {{ row.script_name }}</small>
            </button>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="104">
          <template #default="{ row }">
            <el-tag :type="sceneLibraryTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="绑定实例" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.default_instance_name || '未绑定' }}</template>
        </el-table-column>
        <el-table-column label="流程 / 模型" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.process_template_name || '未绑定流程' }} / {{ row.data_model_name || '未绑定模型' }}
          </template>
        </el-table-column>
        <el-table-column label="执行次数" width="92">
          <template #default="{ row }">{{ row.run_count }} 次</template>
        </el-table-column>
        <el-table-column label="操作" width="230" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openSceneLibrary(row)">详情</el-button>
            <el-button link type="primary" @click="openSceneLibraryClone(row)">克隆</el-button>
            <el-button link type="success" :disabled="row.status !== 'READY'" @click="openSceneLibraryRun(row)">执行</el-button>
            <el-button
              link
              :type="row.status === 'ARCHIVED' ? 'primary' : 'warning'"
              @click="operateSceneLibrary(row, row.status === 'ARCHIVED' ? 'PUBLISHED' : 'ARCHIVED')"
            >
              {{ row.status === 'ARCHIVED' ? '发布' : '归档' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ sceneLibraryPage.total }} 个场景库版本</span>
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="sceneLibraryPage.page"
          :page-size="sceneLibraryPage.page_size"
          :total="sceneLibraryPage.total"
          @current-change="loadSceneLibraries"
        />
      </div>
    </section>

    <section v-show="activeWorkspace === 'scene' && activeModule === 'scene-run'" class="panel scene-panel">
      <div class="section-heading scene-heading">
        <div>
          <p class="eyebrow">SCENE ORCHESTRATION · X21</p>
          <h2>场景执行与人工闭环</h2>
        </div>
        <div class="scene-summary">
          <span><b>{{ dashboard.summary.scene_running_count }}</b> 执行中</span>
          <span><b>{{ dashboard.summary.scene_completed_count }}</b> 已完成</span>
          <span class="warning"><b>{{ dashboard.summary.work_order_open_count }}</b> 待闭环</span>
          <el-button plain @click="openSceneScriptCreate">新建剧本</el-button>
          <el-button type="primary" @click="openSceneCreate()">创建场景执行</el-button>
        </div>
      </div>

      <div class="scene-script-rail">
        <button
          v-for="script in dashboard.scene_scripts"
          :key="script.id"
          type="button"
          class="scene-script-card"
          :class="{ active: sceneFilters.script_id === script.id }"
          @click="selectSceneScript(script)"
        >
          <span>{{ script.code }} · V{{ script.version }}</span>
          <strong>{{ script.name }}</strong>
          <p>{{ script.description }}</p>
          <small>{{ script.step_count }} 步 · {{ script.scenario_name }}</small>
        </button>
      </div>

      <div class="filter-bar scene-filter-bar">
        <el-select v-model="sceneFilters.instance_id" clearable placeholder="全部预演实例">
          <el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="sceneFilters.script_id" clearable placeholder="全部场景剧本">
          <el-option v-for="item in dashboard.scene_scripts" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="sceneFilters.status" clearable placeholder="全部状态">
          <el-option label="待执行" value="PENDING" />
          <el-option label="执行中" value="RUNNING" />
          <el-option label="已完成" value="COMPLETED" />
          <el-option label="已取消" value="CANCELLED" />
          <el-option label="失败" value="FAILED" />
        </el-select>
        <el-input v-model="sceneFilters.keyword" clearable placeholder="场景执行或实例名称" @keyup.enter="loadSceneRuns(1)" />
        <el-button type="primary" @click="loadSceneRuns(1)">查询</el-button>
        <el-button @click="resetSceneFilters">重置</el-button>
      </div>

      <el-table v-loading="sceneLoading" :data="scenePage.items" empty-text="还没有场景执行">
        <el-table-column label="场景执行" min-width="250">
          <template #default="{ row }">
            <button class="instance-link" type="button" @click="openSceneRun(row)">
              <strong>{{ row.name }}</strong>
              <small>{{ row.code }} · {{ row.script_name }}</small>
            </button>
          </template>
        </el-table-column>
        <el-table-column prop="instance_name" label="预演实例" min-width="170" show-overflow-tooltip />
        <el-table-column label="状态" width="96">
          <template #default="{ row }"><el-tag :type="sceneTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag></template>
        </el-table-column>
        <el-table-column label="当前步骤" min-width="155">
          <template #default="{ row }">{{ currentSceneStepName(row) }}</template>
        </el-table-column>
        <el-table-column label="进度" min-width="170">
          <template #default="{ row }">
            <div class="progress-cell"><el-progress :percentage="row.progress_percent" :stroke-width="7" /><span>{{ row.completed_steps }}/{{ row.total_steps }} 步</span></div>
          </template>
        </el-table-column>
        <el-table-column label="人工工单" width="92">
          <template #default="{ row }">{{ row.work_order_count }} 单</template>
        </el-table-column>
        <el-table-column label="操作" width="92" fixed="right">
          <template #default="{ row }"><el-button link type="primary" @click="openSceneRun(row)">进入场景</el-button></template>
        </el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ scenePage.total }} 条场景执行</span>
        <el-pagination background layout="prev, pager, next" :current-page="scenePage.page" :page-size="scenePage.page_size" :total="scenePage.total" @current-change="loadSceneRuns" />
      </div>
    </section>

    <section v-show="activeWorkspace === 'scene' && activeModule === 'alert'" class="panel alert-panel">
      <div class="section-heading alert-heading">
        <div>
          <p class="eyebrow">ALERT SIMULATION · X22</p>
          <h2>告警演练与时序同步</h2>
        </div>
        <div class="alert-summary">
          <span class="pending"><b>{{ dashboard.summary.alert_pending_count }}</b> 待上报</span>
          <span class="active"><b>{{ dashboard.summary.alert_active_count }}</b> 活跃</span>
          <span class="recovered"><b>{{ dashboard.summary.alert_recovered_count }}</b> 已恢复</span>
          <el-button plain @click="openAlertTemplateCreate">新建告警模板</el-button>
          <el-button type="danger" @click="openAlertCreate()">配置演练告警</el-button>
        </div>
      </div>

      <div class="alert-template-rail">
        <button
          v-for="template in dashboard.alert_templates"
          :key="template.id"
          type="button"
          class="alert-template-card"
          :class="{ active: alertFilters.template_id === template.id }"
          @click="selectAlertTemplate(template)"
        >
          <span>{{ template.code }} · V{{ template.version }}</span>
          <strong>{{ template.name }}</strong>
          <p>{{ template.description }}</p>
          <small>{{ template.rule_count }} 条规则 · 默认{{ template.default_severity_label }}</small>
        </button>
      </div>

      <div class="filter-bar alert-filter-bar">
        <el-select v-model="alertFilters.instance_id" clearable placeholder="全部预演实例">
          <el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="alertFilters.template_id" clearable placeholder="全部告警模板">
          <el-option v-for="item in dashboard.alert_templates" :key="item.id" :label="item.name" :value="item.id" />
        </el-select>
        <el-select v-model="alertFilters.status" clearable placeholder="全部状态">
          <el-option label="待上报" value="PENDING" />
          <el-option label="活动告警" value="ACTIVE" />
          <el-option label="已确认" value="ACKNOWLEDGED" />
          <el-option label="已恢复" value="RECOVERED" />
        </el-select>
        <el-select v-model="alertFilters.severity" clearable placeholder="全部等级">
          <el-option label="一般" value="LOW" />
          <el-option label="关注" value="MEDIUM" />
          <el-option label="严重" value="HIGH" />
          <el-option label="紧急" value="CRITICAL" />
        </el-select>
        <el-input v-model="alertFilters.keyword" clearable placeholder="告警、设备或指标" @keyup.enter="loadAlerts(1)" />
        <el-button type="primary" @click="loadAlerts(1)">查询</el-button>
        <el-button @click="resetAlertFilters">重置</el-button>
      </div>

      <el-table v-loading="alertLoading" :data="alertPage.items" empty-text="还没有演练告警">
        <el-table-column label="演练告警" min-width="250">
          <template #default="{ row }">
            <button class="instance-link" type="button" @click="openAlert(row)">
              <strong>{{ row.title }}</strong>
              <small>{{ row.code }} · {{ row.template_name }}</small>
            </button>
          </template>
        </el-table-column>
        <el-table-column label="网元 / 指标" min-width="190">
          <template #default="{ row }"><strong>{{ row.resource_name || row.resource_id || '未指定网元' }}</strong><br /><small>{{ row.metric_name || row.metric_code || '通用告警' }}<template v-if="row.metric_value !== null"> · {{ row.metric_value }}</template></small></template>
        </el-table-column>
        <el-table-column label="等级" width="90"><template #default="{ row }"><el-tag :type="alertSeverityTagType(row.severity)" effect="plain">{{ row.severity_label }}</el-tag></template></el-table-column>
        <el-table-column label="状态" width="104"><template #default="{ row }"><el-tag :type="alertStatusTagType(row.status)" effect="dark">{{ row.status_label }}</el-tag></template></el-table-column>
        <el-table-column label="发生时间" width="164"><template #default="{ row }">{{ formatTime(row.occurred_at) }}</template></el-table-column>
        <el-table-column label="关联链路" min-width="160"><template #default="{ row }">{{ row.scene_run_name || row.data_batch_name || row.instance_name }}</template></el-table-column>
        <el-table-column label="操作" width="90" fixed="right"><template #default="{ row }"><el-button link type="primary" @click="openAlert(row)">处置</el-button></template></el-table-column>
      </el-table>
      <div class="pagination-row">
        <span>共 {{ alertPage.total }} 条演练告警</span>
        <el-pagination background layout="prev, pager, next" :current-page="alertPage.page" :page-size="alertPage.page_size" :total="alertPage.total" @current-change="loadAlerts" />
      </div>
    </section>

    <section v-show="activeWorkspace === 'scene' && activeModule === 'complaint'" class="panel complaint-panel">
      <div class="section-heading complaint-heading">
        <div>
          <p class="eyebrow">COMPLAINT STREAM</p>
          <h2>申告数据</h2>
        </div>
        <div class="header-actions">
          <el-button plain @click="exportCurrentComplaints"> 导出当前结果 </el-button>
          <el-button type="primary" plain @click="resetFilters">重置筛选</el-button>
        </div>
      </div>

      <div class="filter-bar">
        <el-select v-model="filters.instance_id" clearable placeholder="全部预演实例">
          <el-option
            v-for="item in dashboard.instances"
            :key="item.id"
            :label="item.name"
            :value="item.id"
          />
        </el-select>
        <el-select v-model="filters.customer_type" clearable placeholder="客户类型">
          <el-option label="公众客户" value="PUBLIC" />
          <el-option label="政企客户" value="ENTERPRISE" />
        </el-select>
        <el-select v-model="filters.severity" clearable placeholder="严重程度">
          <el-option label="一般" value="LOW" />
          <el-option label="关注" value="MEDIUM" />
          <el-option label="严重" value="HIGH" />
          <el-option label="紧急" value="CRITICAL" />
        </el-select>
        <el-select v-model="filters.validation_status" clearable placeholder="校验状态">
          <el-option label="有效" value="VALID" />
          <el-option label="无效" value="INVALID" />
        </el-select>
        <el-select v-model="filters.source" clearable placeholder="数据来源">
          <el-option label="系统生成" value="GENERATED" />
          <el-option label="人工导入" value="IMPORTED" />
        </el-select>
        <el-input
          v-model="filters.keyword"
          clearable
          placeholder="客户、标题或内容"
          @keyup.enter="loadComplaints(1)"
        />
        <el-button type="primary" @click="loadComplaints(1)">查询</el-button>
      </div>

      <el-table v-loading="complaintLoading" :data="complaintPage.items" min-height="280">
        <el-table-column label="发生时间" width="164">
          <template #default="{ row }">{{ formatTime(row.occurred_at) }}</template>
        </el-table-column>
        <el-table-column label="客户" min-width="190">
          <template #default="{ row }">
            <div class="customer-cell">
              <strong>{{ row.customer_name || row.customer_ref || '未命名客户' }}</strong>
              <span>{{ row.customer_type_label }} · {{ row.contact_masked || '无联系方式' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="category" label="申告类别" min-width="110" />
        <el-table-column label="严重程度" width="92">
          <template #default="{ row }">
            <span class="severity-dot" :class="row.severity.toLowerCase()"></span>
            {{ row.severity_label }}
          </template>
        </el-table-column>
        <el-table-column label="数据来源" width="100">
          <template #default="{ row }">{{ row.source_label }}</template>
        </el-table-column>
        <el-table-column label="校验" width="94">
          <template #default="{ row }">
            <el-tooltip
              :disabled="!row.validation_errors.length"
              :content="row.validation_errors.join('；')"
              placement="top"
            >
              <el-tag
                :type="row.validation_status === 'VALID' ? 'success' : 'danger'"
                effect="plain"
              >
                {{ row.validation_status_label }}
              </el-tag>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="申告摘要" min-width="250" show-overflow-tooltip />
      </el-table>
      <div class="pagination-row">
        <span>共 {{ complaintPage.total }} 条</span>
        <el-pagination
          background
          layout="prev, pager, next"
          :current-page="complaintPage.page"
          :page-size="complaintPage.page_size"
          :total="complaintPage.total"
          @current-change="loadComplaints"
        />
      </div>
    </section>

    <el-dialog v-model="createDialogVisible" title="新建预演实例" width="560px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-position="top">
        <el-form-item label="预演场景" prop="scenario_id">
          <el-select v-model="createForm.scenario_id" placeholder="选择一个可预演场景">
            <el-option
              v-for="item in dashboard.scenarios"
              :key="item.id"
              :label="`${item.name} · ${item.status_label}`"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="实例名称" prop="name">
          <el-input
            v-model="createForm.name"
            maxlength="128"
            placeholder="例如：公众宽带集中申告演练"
          />
        </el-form-item>
        <el-form-item label="实例编号">
          <el-input v-model="createForm.code" maxlength="64" placeholder="留空自动生成" />
        </el-form-item>
        <el-form-item label="计划启动时间">
          <el-date-picker
            v-model="createForm.planned_start_at"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ssZ"
            placeholder="可选"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitInstance"
          >创建并进入</el-button
        >
      </template>
    </el-dialog>

    <el-drawer
      v-model="instanceDrawerVisible"
      class="rehearsal-drawer"
      size="min(780px, 92vw)"
      :title="selectedInstance?.name || '预演实例'"
    >
      <div v-if="selectedInstance" v-loading="detailLoading" class="drawer-scroll">
        <section class="instance-command">
          <div>
            <p class="eyebrow">{{ selectedInstance.code }}</p>
            <h3>{{ selectedInstance.name }}</h3>
            <p>{{ selectedInstance.scenario_name }}</p>
          </div>
          <el-tag :type="statusTagType(selectedInstance.status)" size="large" effect="dark">
            {{ selectedInstance.status_label }}
          </el-tag>
        </section>

        <div class="instance-stats">
          <div>
            <strong>{{ selectedInstance.complaint_count }}</strong
            ><span>有效申告</span>
          </div>
          <div>
            <strong>{{ selectedInstance.invalid_count }}</strong
            ><span>异常数据</span>
          </div>
          <div>
            <strong>{{ selectedInstance.batch_count }}</strong
            ><span>数据批次</span>
          </div>
          <div>
            <strong>{{ selectedInstance.events?.length || 0 }}</strong
            ><span>审计事件</span>
          </div>
        </div>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">STATE MACHINE</p>
              <h3>预演控制</h3>
            </div>
            <span>准备 → 启动 → 完成</span>
          </div>
          <div class="control-actions">
            <el-button
              v-if="selectedInstance.status === 'DRAFT'"
              type="primary"
              :loading="operating"
              @click="operate('PREPARE')"
            >
              完成数据准备
            </el-button>
            <el-button
              v-if="selectedInstance.status === 'READY'"
              type="success"
              :loading="operating"
              @click="operate('START')"
            >
              启动预演
            </el-button>
            <el-button
              v-if="selectedInstance.status === 'RUNNING'"
              type="primary"
              :loading="operating"
              @click="operate('COMPLETE')"
            >
              完成预演
            </el-button>
            <el-button
              v-if="['DRAFT', 'READY', 'RUNNING'].includes(selectedInstance.status)"
              plain
              :loading="operating"
              @click="operate('CANCEL')"
            >
              取消实例
            </el-button>
            <span v-if="['COMPLETED', 'CANCELLED', 'FAILED'].includes(selectedInstance.status)">
              当前实例已结束，审计记录仍可查阅。
            </span>
          </div>
        </section>

        <section v-if="canPrepareData" class="drawer-section">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">DATA FACTORY</p>
              <h3>生成时序申告</h3>
            </div>
            <el-upload
              :show-file-list="false"
              accept=".csv,text/csv"
              :http-request="uploadComplaintFile"
            >
              <el-button plain :loading="importing">导入 CSV</el-button>
            </el-upload>
          </div>
          <div class="generator-grid">
            <el-select v-model="generateForm.template_id" placeholder="选择公客或政企模板">
              <el-option
                v-for="item in dashboard.templates"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <el-input-number
              v-model="generateForm.count"
              :min="1"
              :max="500"
              controls-position="right"
            />
            <el-date-picker
              v-model="generateForm.start_at"
              type="datetime"
              value-format="YYYY-MM-DDTHH:mm:ssZ"
              placeholder="序列起点"
            />
            <el-input-number
              v-model="generateForm.interval_minutes"
              :min="1"
              :max="1440"
              controls-position="right"
            />
            <el-button type="primary" :loading="generating" @click="generateData">
              生成申告
            </el-button>
          </div>
          <p class="helper-text">数量上限 500 条；间隔按分钟生成，联系方式只保留脱敏值。</p>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">PROCESS FACTORY · X19</p>
              <h3>生成处置流程</h3>
            </div>
            <span>{{ selectedInstance.process_runs?.length || 0 }} 条流程</span>
          </div>
          <div
            v-if="['READY', 'RUNNING'].includes(selectedInstance.status)"
            class="process-generator"
          >
            <el-select v-model="processForm.template_id" placeholder="选择处置流程模板">
              <el-option
                v-for="item in dashboard.process_templates"
                :key="item.id"
                :label="`${item.name} · ${item.step_count}步`"
                :value="item.id"
              />
            </el-select>
            <el-input v-model="processForm.name" maxlength="128" placeholder="流程名称（可选）" />
            <label class="auto-switch">
              <el-switch v-model="processForm.auto_advance" />
              <span>启用自动推进</span>
            </label>
            <el-button type="primary" :loading="processCreating" @click="createProcessRun">
              生成流程
            </el-button>
          </div>
          <p v-else-if="selectedInstance.status === 'DRAFT'" class="helper-text">
            请先完成数据准备，再生成处置流程。
          </p>
          <div class="instance-process-list">
            <button
              v-for="run in selectedInstance.process_runs || []"
              :key="run.id"
              type="button"
              @click="openProcessRun(run)"
            >
              <div>
                <strong>{{ run.name }}</strong>
                <small>{{ currentStepName(run) }} · {{ run.progress_percent }}%</small>
              </div>
              <el-tag :type="processTagType(run.status)" effect="plain">{{ run.status_label }}</el-tag>
            </button>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">SCENE FACTORY · X21</p>
              <h3>场景执行</h3>
            </div>
            <el-button
              type="primary"
              plain
              :disabled="!['DRAFT', 'READY', 'RUNNING'].includes(selectedInstance.status)"
              @click="openSceneCreate(selectedInstance)"
            >注入场景</el-button>
          </div>
          <p class="helper-text">将当前实例已有的申告批次、趋势数据或处置流程注入剧本后执行。</p>
          <div class="instance-process-list">
            <button v-for="run in selectedInstance.scene_runs || []" :key="run.id" type="button" @click="openSceneRun(run)">
              <div><strong>{{ run.name }}</strong><small>{{ currentSceneStepName(run) }} · {{ run.progress_percent }}%</small></div>
              <el-tag :type="sceneTagType(run.status)" effect="plain">{{ run.status_label }}</el-tag>
            </button>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">ALERT FACTORY · X22</p><h3>演练告警</h3></div>
            <el-button type="danger" plain :disabled="!['DRAFT', 'READY', 'RUNNING'].includes(selectedInstance.status)" @click="openAlertCreate(selectedInstance)">配置告警</el-button>
          </div>
          <p class="helper-text">告警可关联当前实例的场景执行和指标趋势批次，并进入统一时间轴。</p>
          <div class="instance-process-list alert-instance-list">
            <button v-for="alert in selectedInstance.alerts || []" :key="alert.id" type="button" @click="openAlert(alert)">
              <div><strong>{{ alert.title }}</strong><small>{{ alert.resource_name || alert.metric_name }} · {{ formatTime(alert.occurred_at) }}</small></div>
              <el-tag :type="alertStatusTagType(alert.status)" effect="plain">{{ alert.status_label }}</el-tag>
            </button>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">DATA MODEL · X23</p><h3>预演数据模型</h3></div>
            <el-button type="primary" plain @click="openDataModelCreate(selectedInstance)">构建模型</el-button>
          </div>
          <p class="helper-text">把当前实例下的申告、指标、流程、场景、工单和告警沉淀为版本化快照。</p>
          <div class="instance-process-list">
            <button v-for="model in selectedInstance.data_models || []" :key="model.id" type="button" @click="openDataModel(model)">
              <div><strong>{{ model.name }}</strong><small>V{{ model.current_version }} · {{ dataModelSourceSummary(model) }}</small></div>
              <el-tag :type="dataModelQualityTagType(model.quality_status)" effect="plain">{{ model.quality_status_label }}</el-tag>
            </button>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">BATCH LEDGER</p>
              <h3>数据批次</h3>
            </div>
            <span>{{ selectedInstance.batches?.length || 0 }} 个版本</span>
          </div>
          <el-table :data="selectedInstance.batches || []" empty-text="暂无数据批次">
            <el-table-column label="版本" width="68">
              <template #default="{ row }">V{{ row.version }}</template>
            </el-table-column>
            <el-table-column prop="template_name" label="来源模板" min-width="150" />
            <el-table-column label="状态" width="96">
              <template #default="{ row }">
                <el-tag :type="batchTagType(row.status)" effect="plain">{{
                  row.status_label
                }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="有效/异常" width="100">
              <template #default="{ row }"
                >{{ row.valid_count }} / {{ row.invalid_count }}</template
              >
            </el-table-column>
            <el-table-column label="操作" width="96">
              <template #default="{ row }">
                <el-button link type="primary" @click="rehearsalApi.exportBatchValidation(row)">
                  校验报告
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </section>

        <section class="drawer-section event-section">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">AUDIT TRAIL</p>
              <h3>状态与数据事件</h3>
            </div>
            <span>只追加，不覆盖</span>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="event in selectedInstance.events || []"
              :key="event.id"
              :timestamp="formatTime(event.create_time)"
              placement="top"
            >
              <strong>{{ event.event_type_label }}</strong>
              <p>
                {{ event.previous_status_label }} → {{ event.current_status_label }} ·
                {{ event.operator_name }}
              </p>
            </el-timeline-item>
          </el-timeline>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="dataCreateDrawerVisible"
      append-to-body
      class="rehearsal-drawer simulation-create-drawer"
      size="min(920px, 96vw)"
      title="自定义趋势数据"
    >
      <div class="drawer-scroll data-create-scroll">
        <section class="simulation-form-intro">
          <div>
            <p class="eyebrow">DATA CONSTRUCTION · X20</p>
            <h3>构造可复现的业务趋势</h3>
            <p>选择预演实例与模板，再调整字段范围、起止值和分布规则。</p>
          </div>
          <span>{{ dataForm.rules.length }} 字段 · {{ dataForm.count }} 点</span>
        </section>

        <section class="drawer-section simulation-base-form">
          <div class="drawer-heading">
            <div><p class="eyebrow">BASIC SETUP</p><h3>基础配置</h3></div>
            <span>数据批次将绑定到预演实例</span>
          </div>
          <div class="simulation-base-grid">
            <label>
              <span>预演实例</span>
              <el-select v-model="dataForm.instance_id" placeholder="选择预演实例">
                <el-option
                  v-for="item in availableDataInstances"
                  :key="item.id"
                  :label="`${item.name} · ${item.status_label}`"
                  :value="item.id"
                />
              </el-select>
            </label>
            <label>
              <span>数据模板</span>
              <el-select v-model="dataForm.template_id" placeholder="选择数据模板" @change="applyDataTemplate">
                <el-option
                  v-for="item in dashboard.data_templates"
                  :key="item.id"
                  :label="`${item.name} · ${item.kind_label}`"
                  :value="item.id"
                />
              </el-select>
            </label>
            <label class="wide-field">
              <span>批次名称</span>
              <el-input v-model="dataForm.name" maxlength="128" placeholder="留空则按模板与时间自动命名" />
            </label>
            <label>
              <span>时序点数</span>
              <el-input-number v-model="dataForm.count" :min="3" :max="500" controls-position="right" />
            </label>
            <label>
              <span>间隔（分钟）</span>
              <el-input-number v-model="dataForm.interval_minutes" :min="1" :max="1440" controls-position="right" />
            </label>
            <label>
              <span>序列起点</span>
              <el-date-picker
                v-model="dataForm.start_at"
                type="datetime"
                value-format="YYYY-MM-DDTHH:mm:ssZ"
                placeholder="选择起始时间"
              />
            </label>
            <label>
              <span>业务标签</span>
              <el-select
                v-model="dataForm.tags"
                multiple
                filterable
                allow-create
                default-first-option
                :multiple-limit="8"
                placeholder="选择或输入标签"
              >
                <el-option v-for="item in knownDataTags" :key="item" :label="item" :value="item" />
              </el-select>
            </label>
          </div>
        </section>

        <section class="drawer-section simulation-rule-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">FIELD RULES</p><h3>字段构造规则</h3></div>
            <el-button plain :disabled="dataForm.rules.length >= 8" @click="addDataRule">添加字段</el-button>
          </div>
          <div class="simulation-rule-list">
            <article v-for="(rule, index) in dataForm.rules" :key="index" class="simulation-rule-card">
              <div class="rule-number">{{ String(index + 1).padStart(2, '0') }}</div>
              <div class="rule-fields">
                <label><span>字段编号</span><el-input v-model="rule.code" maxlength="32" /></label>
                <label><span>显示名称</span><el-input v-model="rule.name" maxlength="64" /></label>
                <label><span>单位</span><el-input v-model="rule.unit" maxlength="16" /></label>
                <label>
                  <span>分布规则</span>
                  <el-select v-model="rule.distribution">
                    <el-option label="线性趋势" value="LINEAR" />
                    <el-option label="周期波动" value="WAVE" />
                    <el-option label="随机分布" value="RANDOM" />
                    <el-option label="阶跃变化" value="STEP" />
                  </el-select>
                </label>
                <label><span>最小值</span><el-input-number v-model="rule.min_value" :controls="false" /></label>
                <label><span>最大值</span><el-input-number v-model="rule.max_value" :controls="false" /></label>
                <label><span>起始值</span><el-input-number v-model="rule.start_value" :controls="false" /></label>
                <label><span>结束值</span><el-input-number v-model="rule.end_value" :controls="false" /></label>
                <label><span>小数位</span><el-input-number v-model="rule.decimals" :min="0" :max="4" /></label>
              </div>
              <el-button link type="danger" :disabled="dataForm.rules.length === 1" @click="removeDataRule(index)">删除</el-button>
            </article>
          </div>
        </section>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <span>生成结果会保留规则快照，可继续筛选与导出。</span>
          <div>
            <el-button @click="dataCreateDrawerVisible = false">取消</el-button>
            <el-button type="primary" :loading="dataGenerating" @click="generateSimulationData">生成趋势数据</el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-drawer
      v-model="dataDetailDrawerVisible"
      append-to-body
      class="rehearsal-drawer simulation-detail-drawer"
      size="min(920px, 96vw)"
      :title="selectedDataSimulation?.name || '数据趋势看板'"
    >
      <div v-if="selectedDataSimulation" v-loading="dataDetailLoading" class="drawer-scroll">
        <section class="simulation-command">
          <div>
            <p class="eyebrow">{{ selectedDataSimulation.code }} · {{ selectedDataSimulation.template_name }}</p>
            <h3>{{ selectedDataSimulation.name }}</h3>
            <p>{{ selectedDataSimulation.instance_name }} · {{ formatTimeRange(selectedDataSimulation.time_start, selectedDataSimulation.time_end) }}</p>
          </div>
          <div class="simulation-command-meta">
            <strong>{{ selectedDataSimulation.point_count }}</strong>
            <span>时序点 · {{ selectedDataSimulation.interval_minutes }} 分钟间隔</span>
            <el-tag :type="dataKindTagType(selectedDataSimulation.kind)" effect="dark">{{ selectedDataSimulation.kind_label }}</el-tag>
          </div>
        </section>

        <section class="drawer-section trend-section">
          <div class="drawer-heading trend-heading">
            <div><p class="eyebrow">TREND MONITOR</p><h3>指标趋势</h3></div>
            <div class="trend-actions">
              <el-select v-model="activeDataFieldCode" placeholder="选择字段">
                <el-option
                  v-for="rule in selectedDataSimulation.rules_snapshot"
                  :key="rule.code"
                  :label="`${rule.name}${rule.unit ? ` (${rule.unit})` : ''}`"
                  :value="rule.code"
                />
              </el-select>
              <el-button plain :loading="dataExporting" @click="exportSelectedDataSimulation">导出批次</el-button>
            </div>
          </div>
          <div v-if="selectedDataFieldSummary" class="trend-stat-grid">
            <div><span>最新值</span><strong>{{ formatDataValue(selectedDataFieldSummary.latest) }}</strong><small>{{ selectedDataFieldSummary.unit || '无单位' }}</small></div>
            <div><span>平均值</span><strong>{{ formatDataValue(selectedDataFieldSummary.average) }}</strong><small>全时段</small></div>
            <div><span>最小 / 最大</span><strong>{{ formatDataValue(selectedDataFieldSummary.minimum) }} / {{ formatDataValue(selectedDataFieldSummary.maximum) }}</strong><small>波动区间</small></div>
            <div><span>净变化</span><strong :class="selectedDataFieldSummary.trend.toLowerCase()">{{ signedDataValue(selectedDataFieldSummary.delta) }}</strong><small>{{ trendLabel(selectedDataFieldSummary.trend) }}</small></div>
          </div>
          <div v-if="chartSeries.length" class="trend-chart">
            <div class="chart-y-labels"><span>{{ chartMaximumLabel }}</span><span>{{ chartMinimumLabel }}</span></div>
            <svg viewBox="0 0 760 230" preserveAspectRatio="none" role="img" :aria-label="`${activeDataFieldName}趋势图`">
              <line v-for="line in [28, 82, 136, 190]" :key="line" x1="22" :y1="line" x2="738" :y2="line" class="chart-grid-line" />
              <polygon :points="chartAreaPoints" class="chart-area" />
              <polyline :points="chartPolyline" class="chart-line" />
            </svg>
            <div class="chart-x-labels"><span>{{ formatTime(selectedDataSimulation.time_start) }}</span><b>{{ activeDataFieldName }}</b><span>{{ formatTime(selectedDataSimulation.time_end) }}</span></div>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">POINT LEDGER</p><h3>时序明细</h3></div>
            <div class="tag-row"><span v-for="tag in selectedDataSimulation.tags" :key="tag">{{ tag }}</span></div>
          </div>
          <el-table :data="selectedDataSimulation.points || []" max-height="360" empty-text="暂无时序点">
            <el-table-column prop="sequence_no" label="#" width="56" />
            <el-table-column label="时间" width="168"><template #default="{ row }">{{ formatTime(row.occurred_at) }}</template></el-table-column>
            <el-table-column :label="activeDataFieldName" width="125">
              <template #default="{ row }"><strong>{{ formatDataValue(row.values[activeDataFieldCode]) }}</strong> {{ selectedDataFieldSummary?.unit }}</template>
            </el-table-column>
            <el-table-column prop="narrative" label="生成说明" min-width="300" show-overflow-tooltip />
          </el-table>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="dataModelCreateDrawerVisible"
      append-to-body
      class="rehearsal-drawer data-model-create-drawer"
      size="min(760px, 94vw)"
      title="构建预演数据模型"
    >
      <div class="drawer-scroll">
        <section class="simulation-command data-model-command">
          <div>
            <p class="eyebrow">BUILD STRATEGY · TRANSFORMER · VERSION</p>
            <h3>把当前预演实例沉淀成版本化数据模型</h3>
            <p>模型会聚合申告、时序、流程、场景、工单和告警，并生成质量检查与来源血缘。</p>
          </div>
          <div class="simulation-command-meta">
            <strong>{{ dashboard.summary.data_model_version_count }}</strong>
            <span>已加载版本</span>
          </div>
        </section>

        <section class="drawer-section simulation-base-form">
          <div class="drawer-heading">
            <div><p class="eyebrow">MODEL SETUP</p><h3>模型配置</h3></div>
            <span>构建后可重复加载形成新版本</span>
          </div>
          <div class="data-model-form-grid">
            <label>
              <span>预演实例</span>
              <el-select v-model="dataModelForm.instance_id" placeholder="选择预演实例" @change="syncDataModelScene">
                <el-option
                  v-for="item in dashboard.instances"
                  :key="item.id"
                  :label="`${item.name} · ${item.status_label}`"
                  :value="item.id"
                />
              </el-select>
            </label>
            <label>
              <span>构建策略</span>
              <el-select v-model="dataModelForm.build_strategy">
                <el-option label="全量实例构建" value="FULL_INSTANCE" />
                <el-option label="场景关联构建" value="SCENE_LINKED" />
                <el-option label="故障链路构建" value="FAULT_CHAIN" />
              </el-select>
            </label>
            <label>
              <span>关联场景</span>
              <el-select v-model="dataModelForm.scene_run_id" clearable placeholder="可选">
                <el-option
                  v-for="item in availableDataModelSceneRuns"
                  :key="item.id"
                  :label="`${item.name} · ${item.status_label}`"
                  :value="item.id"
                />
              </el-select>
            </label>
            <label>
              <span>转换器</span>
              <el-input v-model="dataModelForm.transformer_code" maxlength="64" />
            </label>
            <label class="wide-field">
              <span>模型名称</span>
              <el-input v-model="dataModelForm.name" maxlength="128" placeholder="留空自动按实例命名" />
            </label>
            <label class="wide-field">
              <span>模型说明</span>
              <el-input
                v-model="dataModelForm.description"
                type="textarea"
                maxlength="500"
                :rows="3"
                placeholder="可写清楚本次构建范围或验收用途"
              />
            </label>
          </div>
        </section>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <span>构建会立即生成 V1 与加载记录。</span>
          <div>
            <el-button @click="dataModelCreateDrawerVisible = false">取消</el-button>
            <el-button type="primary" :loading="dataModelCreating" @click="createDataModelFromForm">构建模型</el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-drawer
      v-model="dataModelDrawerVisible"
      append-to-body
      class="rehearsal-drawer data-model-detail-drawer"
      size="min(920px, 96vw)"
      :title="selectedDataModel?.name || '预演数据模型'"
    >
      <div v-if="selectedDataModel" v-loading="dataModelDetailLoading" class="drawer-scroll">
        <section class="simulation-command data-model-command">
          <div>
            <p class="eyebrow">{{ selectedDataModel.code }} · {{ selectedDataModel.transformer_code }}</p>
            <h3>{{ selectedDataModel.name }}</h3>
            <p>{{ selectedDataModel.instance_name }} · {{ selectedDataModel.build_strategy_label }} · V{{ selectedDataModel.current_version }}</p>
          </div>
          <div class="simulation-command-meta">
            <strong>{{ selectedDataModel.summary.quality_score ?? 0 }}</strong>
            <span>质量分</span>
            <el-tag :type="dataModelQualityTagType(selectedDataModel.quality_status)" effect="dark">
              {{ selectedDataModel.quality_status_label }}
            </el-tag>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">QUALITY CHECKS</p><h3>质量检查</h3></div>
            <el-button plain :loading="dataModelLoadingVersion" @click="reloadDataModel(selectedDataModel)">重新加载</el-button>
          </div>
          <div class="quality-check-list">
            <article
              v-for="check in latestDataModelVersion?.quality_report.checks || []"
              :key="check.code"
              :class="{ passed: check.passed }"
            >
              <span>{{ check.passed ? 'OK' : check.severity }}</span>
              <div><strong>{{ check.name }}</strong><small>{{ check.message }}</small></div>
            </article>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">SOURCE COUNTS</p><h3>来源规模</h3></div>
            <span>{{ selectedDataModel.lineage.sources?.length || 0 }} 个来源节点</span>
          </div>
          <div class="source-count-grid">
            <div v-for="item in dataModelSourceEntries(selectedDataModel)" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </div>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">VERSION LEDGER</p><h3>版本与加载记录</h3></div>
            <span>{{ selectedDataModel.versions?.length || 0 }} 个版本</span>
          </div>
          <el-table :data="selectedDataModel.versions || []" max-height="220" empty-text="暂无版本">
            <el-table-column label="版本" width="80"><template #default="{ row }">V{{ row.version }}</template></el-table-column>
            <el-table-column prop="transformer_code" label="转换器" width="140" />
            <el-table-column label="质量" width="104"><template #default="{ row }">{{ row.quality_report.status_label }}</template></el-table-column>
            <el-table-column label="加载时间" width="180"><template #default="{ row }">{{ formatTime(row.loaded_at) }}</template></el-table-column>
            <el-table-column prop="checksum" label="校验和" min-width="240" show-overflow-tooltip />
          </el-table>
          <el-table :data="selectedDataModel.loads || []" max-height="220" empty-text="暂无加载记录">
            <el-table-column prop="request_id" label="请求编号" min-width="190" show-overflow-tooltip />
            <el-table-column label="状态" width="110"><template #default="{ row }"><el-tag :type="dataModelLoadTagType(row.status)" effect="plain">{{ row.status_label }}</el-tag></template></el-table-column>
            <el-table-column prop="operator_name" label="操作人" width="100" />
            <el-table-column label="完成时间" width="180"><template #default="{ row }">{{ formatTime(row.completed_at) }}</template></el-table-column>
            <el-table-column prop="note" label="备注" min-width="180" show-overflow-tooltip />
          </el-table>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">LINEAGE SOURCES</p><h3>血缘来源</h3></div>
            <span>{{ selectedDataModel.lineage.relations?.length || 0 }} 条关系</span>
          </div>
          <div class="lineage-source-list">
            <article v-for="source in selectedDataModel.lineage.sources || []" :key="String(source.source_id)">
              <span>{{ source.source_type }}</span>
              <div><strong>{{ source.name }}</strong><small>{{ source.code }} · {{ source.count }} 条/点/步</small></div>
            </article>
          </div>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="tracebackCreateDrawerVisible"
      append-to-body
      class="rehearsal-drawer traceback-create-drawer"
      size="min(780px, 94vw)"
      title="生成数据动态回溯"
    >
      <div class="drawer-scroll">
        <section class="simulation-command traceback-command">
          <div>
            <p class="eyebrow">FACTS · WINDOW · PIVOTS · SNAPSHOT</p>
            <h3>把一次预演链路固化成可重复查看的回溯快照</h3>
            <p>快照不会随源数据变化，适合验收复盘、问题定位和跨角色协同。</p>
          </div>
          <div class="simulation-command-meta"><strong>7</strong><span>类事实节点</span></div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">TRACEBACK SETUP</p><h3>回溯配置</h3></div>
            <span>故障窗口会优先依据告警时序自动推断</span>
          </div>
          <div class="traceback-form-grid">
            <label>
              <span>预演实例</span>
              <el-select v-model="tracebackForm.instance_id" placeholder="选择预演实例" @change="syncTracebackLinks">
                <el-option
                  v-for="item in dashboard.instances"
                  :key="item.id"
                  :label="`${item.name} · ${item.status_label}`"
                  :value="item.id"
                />
              </el-select>
            </label>
            <label>
              <span>回溯范围</span>
              <el-select v-model="tracebackForm.scope">
                <el-option label="全量实例" value="FULL_INSTANCE" />
                <el-option label="故障窗口（自动推断）" value="INCIDENT_WINDOW" />
                <el-option label="自定义窗口" value="CUSTOM" />
              </el-select>
            </label>
            <label>
              <span>关联场景执行</span>
              <el-select v-model="tracebackForm.scene_run_id" clearable placeholder="可选">
                <el-option
                  v-for="item in availableTracebackSceneRuns"
                  :key="item.id"
                  :label="`${item.name} · ${item.status_label}`"
                  :value="item.id"
                />
              </el-select>
            </label>
            <label>
              <span>关联数据模型</span>
              <el-select v-model="tracebackForm.data_model_id" clearable placeholder="可选">
                <el-option
                  v-for="item in availableTracebackDataModels"
                  :key="item.id"
                  :label="`${item.name} · V${item.current_version}`"
                  :value="item.id"
                />
              </el-select>
            </label>
            <label class="wide">
              <span>事实节点</span>
              <el-select v-model="tracebackForm.kind_scope" multiple collapse-tags collapse-tags-tooltip placeholder="选择回放类型">
                <el-option v-for="item in tracebackKindOptions" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </label>
            <template v-if="tracebackForm.scope !== 'FULL_INSTANCE'">
              <label>
                <span>窗口开始</span>
                <el-date-picker
                  v-model="tracebackForm.window_start"
                  type="datetime"
                  clearable
                  value-format="YYYY-MM-DDTHH:mm:ssZ"
                  placeholder="自动推断或手工指定"
                />
              </label>
              <label>
                <span>窗口结束</span>
                <el-date-picker
                  v-model="tracebackForm.window_end"
                  type="datetime"
                  clearable
                  value-format="YYYY-MM-DDTHH:mm:ssZ"
                  placeholder="自动推断或手工指定"
                />
              </label>
            </template>
            <label class="wide"><span>快照名称</span><el-input v-model="tracebackForm.name" maxlength="128" placeholder="例如：核心链路故障动态回溯" /></label>
            <label class="wide"><span>说明</span><el-input v-model="tracebackForm.description" type="textarea" :rows="3" maxlength="500" show-word-limit /></label>
          </div>
        </section>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <span>生成后会保存来源构成、节点转移、数值变化和完整时间线。</span>
          <div>
            <el-button @click="tracebackCreateDrawerVisible = false">取消</el-button>
            <el-button type="primary" :loading="tracebackCreating" @click="submitTracebackForm">生成回溯</el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-drawer
      v-model="tracebackDrawerVisible"
      append-to-body
      class="rehearsal-drawer traceback-detail-drawer"
      size="min(980px, 96vw)"
      :title="selectedTraceback?.name || '数据动态回溯'"
    >
      <div v-if="selectedTraceback" v-loading="tracebackDetailLoading" class="drawer-scroll">
        <section class="simulation-command traceback-command">
          <div>
            <p class="eyebrow">{{ selectedTraceback.code }} · {{ selectedTraceback.scope_label }}</p>
            <h3>{{ selectedTraceback.name }}</h3>
            <p>{{ selectedTraceback.instance_name }} · {{ formatTime(selectedTraceback.generated_at) }}</p>
          </div>
          <div class="simulation-command-meta">
            <strong>{{ selectedTraceback.total_events }}</strong>
            <span>回溯事件</span>
            <el-tag :type="tracebackStatusTagType(selectedTraceback.status)" effect="dark">{{ selectedTraceback.status_label }}</el-tag>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">TRACEBACK SUMMARY</p><h3>链路摘要</h3></div>
            <el-button plain :loading="tracebackExporting" @click="exportSelectedTraceback">导出当前回溯</el-button>
          </div>
          <div class="traceback-summary-grid">
            <div><span>首个信号</span><strong>{{ selectedTraceback.summary.root_signal || '—' }}</strong></div>
            <div><span>末端信号</span><strong>{{ selectedTraceback.summary.latest_signal || '—' }}</strong></div>
            <div><span>主导节点</span><strong>{{ selectedTraceback.summary.dominant_kind_label || '—' }}</strong></div>
            <div><span>回放时长</span><strong>{{ selectedTraceback.summary.duration_minutes || 0 }} 分钟</strong></div>
            <div><span>节点数量</span><strong>{{ selectedTraceback.summary.node_count || 0 }}</strong></div>
            <div><span>跨节点转移</span><strong>{{ selectedTraceback.summary.transition_count || 0 }}</strong></div>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">PIVOT NODES</p><h3>事实节点对比</h3></div><span>按链路类型归并首末状态</span></div>
          <div class="traceback-node-grid">
            <article v-for="node in selectedTraceback.nodes || []" :key="node.kind">
              <div><span>{{ node.kind_label }}</span><b>{{ node.count }}</b></div>
              <strong>{{ node.first_title }}</strong>
              <i></i>
              <strong>{{ node.last_title }}</strong>
              <small>{{ formatTime(node.first_at) }} → {{ formatTime(node.last_at) }}</small>
            </article>
          </div>
        </section>

        <section v-if="selectedTraceback.deltas?.length" class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">VALUE DELTAS</p><h3>数值变化</h3></div><span>按绝对变化量排序</span></div>
          <el-table :data="selectedTraceback.deltas || []" max-height="260">
            <el-table-column prop="field" label="字段" min-width="150" />
            <el-table-column label="起始值" width="120"><template #default="{ row }">{{ formatDataValue(row.first_value) }}</template></el-table-column>
            <el-table-column label="结束值" width="120"><template #default="{ row }">{{ formatDataValue(row.last_value) }}</template></el-table-column>
            <el-table-column label="变化" width="120"><template #default="{ row }"><b :class="row.delta >= 0 ? 'delta-up' : 'delta-down'">{{ signedDataValue(row.delta) }}</b></template></el-table-column>
            <el-table-column label="观察窗口" min-width="250"><template #default="{ row }">{{ formatTimeRange(row.first_at, row.last_at) }}</template></el-table-column>
          </el-table>
        </section>

        <section class="drawer-section traceback-timeline-section">
          <div class="drawer-heading"><div><p class="eyebrow">IMMUTABLE PLAYBACK</p><h3>完整时间线</h3></div><span>校验和 {{ selectedTraceback.checksum.slice(0, 12) }}</span></div>
          <div class="traceback-transition-row">
            <span v-for="item in selectedTraceback.transitions || []" :key="`${item.from_kind}-${item.to_kind}`">
              {{ item.from_label }} → {{ item.to_label }} · {{ item.count }}
            </span>
          </div>
          <div class="traceback-timeline-list">
            <article v-for="item in selectedTraceback.items || []" :key="`${item.kind}-${item.reference_id}-${item.occurred_at}`">
              <time>{{ formatTime(item.occurred_at) }}</time>
              <span :class="item.kind.toLowerCase()"></span>
              <div><small>{{ item.kind_label }} · {{ item.status }}</small><strong>{{ item.title }}</strong><p>{{ item.subtitle }}</p></div>
            </article>
          </div>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="simulationRecordDrawerVisible"
      append-to-body
      class="rehearsal-drawer simulation-record-drawer"
      size="min(900px, 96vw)"
      :title="selectedSimulationRecord?.record.name || '预演记录详情'"
    >
      <div v-if="selectedSimulationRecord" v-loading="simulationRecordDetailLoading" class="drawer-scroll">
        <section class="record-command">
          <div>
            <p class="eyebrow">{{ selectedSimulationRecord.record.kind_label }} · RUN #{{ selectedSimulationRecord.record.occurrence_no }}</p>
            <h3>{{ selectedSimulationRecord.record.name }}</h3>
            <p>{{ selectedSimulationRecord.record.instance_name }} · {{ selectedSimulationRecord.record.code }}</p>
          </div>
          <div class="record-command-state">
            <strong>{{ selectedSimulationRecord.record.progress_percent }}%</strong>
            <el-tag :type="simulationRecordTagType(selectedSimulationRecord.record.state)" effect="dark">
              {{ selectedSimulationRecord.record.state_label }}
            </el-tag>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">RUN RESULT</p><h3>执行结果</h3></div>
            <span>{{ selectedSimulationRecord.activity_count }} 条明细证据</span>
          </div>
          <div class="record-result-grid">
            <div><span>原始状态</span><strong>{{ selectedSimulationRecord.record.status_label }}</strong></div>
            <div><span>统一结果</span><strong>{{ selectedSimulationRecord.record.state_label }}</strong></div>
            <div><span>执行耗时</span><strong>{{ formatDuration(selectedSimulationRecord.record.duration_seconds) }}</strong></div>
            <div><span>开始时间</span><strong>{{ formatTime(selectedSimulationRecord.record.started_at) }}</strong></div>
            <div><span>完成时间</span><strong>{{ formatTime(selectedSimulationRecord.record.completed_at) }}</strong></div>
            <div class="wide"><span>结果摘要</span><strong>{{ selectedSimulationRecord.record.result_summary }}</strong></div>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">SOURCE SNAPSHOT</p><h3>源记录摘要</h3></div>
            <span>直接来自原业务记录</span>
          </div>
          <div class="record-source-grid">
            <article v-for="item in simulationRecordSourceFacts" :key="item.label">
              <span>{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
            </article>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">HISTORY LEDGER</p><h3>历史进度与详情</h3></div>
            <span>按事实发生时间排序</span>
          </div>
          <div class="record-activity-list">
            <article v-for="item in selectedSimulationRecord.activity" :key="`${item.sequence_no}-${item.occurred_at}`">
              <span>{{ String(item.sequence_no).padStart(2, '0') }}</span>
              <i></i>
              <div><strong>{{ item.label }}</strong><small>{{ item.status_label }} · {{ formatTime(item.occurred_at) }}</small><p>{{ formatRecordDetail(item.detail) }}</p></div>
            </article>
          </div>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="capabilityMockDrawerVisible"
      append-to-body
      class="rehearsal-drawer capability-mock-drawer"
      size="min(760px, 96vw)"
      title="新建隔离能力"
    >
      <div class="drawer-scroll capability-mock-form">
        <section class="simulation-command capability-command">
          <div><p class="eyebrow">MOCK CONTRACT · X27</p><h3>定义隔离能力契约</h3><p>保存接口元数据与成功/失败响应模板，不连接真实生产系统。</p></div>
        </section>
        <div class="capability-form-grid">
          <label><span>所属场景</span><el-select v-model="capabilityMockForm.scenario_id"><el-option v-for="item in dashboard.scenarios" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
          <label><span>能力类型</span><el-select v-model="capabilityMockForm.kind"><el-option label="API 接口" value="API" /><el-option label="原子能力" value="ATOMIC" /></el-select></label>
          <label><span>能力编号</span><el-input v-model="capabilityMockForm.code" maxlength="64" placeholder="例如 QUERY-FAULT-DETAIL" /></label>
          <label><span>能力名称</span><el-input v-model="capabilityMockForm.name" maxlength="128" /></label>
          <label><span>请求方法</span><el-select v-model="capabilityMockForm.method"><el-option v-for="method in ['GET', 'POST', 'PUT', 'PATCH', 'DELETE']" :key="method" :label="method" :value="method" /></el-select></label>
          <label><span>默认调用耗时</span><el-input-number v-model="capabilityMockForm.default_latency_ms" :min="0" :max="120000" :step="50" controls-position="right" /></label>
          <label class="wide"><span>调用地址</span><el-input v-model="capabilityMockForm.endpoint" placeholder="/sandbox/... 或 atomic://..." /></label>
          <label class="wide"><span>说明</span><el-input v-model="capabilityMockForm.description" type="textarea" :rows="2" maxlength="500" /></label>
          <label class="wide"><span>请求 Schema JSON</span><el-input v-model="capabilityMockForm.request_schema_text" type="textarea" :rows="4" /></label>
          <label class="wide"><span>成功响应 JSON</span><el-input v-model="capabilityMockForm.response_template_text" type="textarea" :rows="4" /></label>
          <label class="wide"><span>失败响应 JSON</span><el-input v-model="capabilityMockForm.failure_template_text" type="textarea" :rows="4" /></label>
        </div>
        <div class="drawer-footer"><el-button @click="capabilityMockDrawerVisible = false">取消</el-button><el-button type="primary" :loading="capabilityMockCreating" @click="submitCapabilityMock">保存隔离能力</el-button></div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="capabilityCallDrawerVisible"
      append-to-body
      class="rehearsal-drawer capability-call-drawer"
      size="min(880px, 96vw)"
      :title="selectedCapabilityCall?.capability_name || '能力调用详情'"
    >
      <div v-if="selectedCapabilityCall" v-loading="capabilityCallDetailLoading" class="drawer-scroll">
        <section class="simulation-command capability-command">
          <div><p class="eyebrow">{{ selectedCapabilityCall.capability_kind_label }} · CALL #{{ selectedCapabilityCall.call_no }}</p><h3>{{ selectedCapabilityCall.capability_name }}</h3><p>{{ selectedCapabilityCall.instance_name }} · {{ selectedCapabilityCall.warroom_group }}</p></div>
          <div class="capability-call-state"><strong>HTTP {{ selectedCapabilityCall.http_status }}</strong><el-tag :type="capabilityStatusTagType(selectedCapabilityCall.status)" effect="dark">{{ selectedCapabilityCall.status_label }}</el-tag></div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">CALL FACTS</p><h3>调用事实</h3></div><span>{{ selectedCapabilityCall.source === 'REPLAY' ? '详情重放' : '沙盒调用' }}</span></div>
          <div class="record-result-grid"><div><span>能力编号</span><strong>{{ selectedCapabilityCall.capability_code }}</strong></div><div><span>调用耗时</span><strong>{{ selectedCapabilityCall.latency_ms }}ms</strong></div><div><span>开始时间</span><strong>{{ formatTime(selectedCapabilityCall.started_at) }}</strong></div><div><span>完成时间</span><strong>{{ formatTime(selectedCapabilityCall.finished_at) }}</strong></div><div class="wide"><span>请求幂等键</span><strong>{{ selectedCapabilityCall.request_id }}</strong></div></div>
        </section>
        <section class="drawer-section payload-compare"><article><div><p class="eyebrow">REQUEST</p><h3>请求快照</h3></div><pre>{{ formatJson(selectedCapabilityCall.request_payload) }}</pre></article><article><div><p class="eyebrow">RESPONSE</p><h3>响应快照</h3></div><pre>{{ formatJson(selectedCapabilityCall.response_payload) }}</pre></article></section>
        <section class="drawer-section"><div class="drawer-heading"><div><p class="eyebrow">REPLAY</p><h3>按原请求重放</h3></div><span>每次重放生成新的不可变记录</span></div><div class="capability-replay-actions"><el-button type="success" plain :loading="capabilityReplaying" @click="replaySelectedCapability('SUCCEEDED')">重放成功</el-button><el-button type="danger" plain :loading="capabilityReplaying" @click="replaySelectedCapability('FAILED')">重放失败</el-button><el-button type="warning" plain :loading="capabilityReplaying" @click="replaySelectedCapability('TIMEOUT')">重放超时</el-button></div></section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="faultConfigurationFormDrawerVisible"
      append-to-body
      class="rehearsal-drawer fault-configuration-form-drawer"
      size="min(860px, 96vw)"
      title="新建故障配置"
    >
      <div class="drawer-scroll fault-configuration-form">
        <section class="simulation-command fault-configuration-command">
          <div>
            <p class="eyebrow">FAULT CONTRACT · X28</p>
            <h3>编排一份可校验的故障配置</h3>
            <p>一次保存告警、超时、时段、拓扑和预案；校验通过后才允许绑定预演实例。</p>
          </div>
        </section>

        <div class="fault-configuration-form-grid">
          <label>
            <span>所属场景</span>
            <el-select v-model="faultConfigurationForm.scenario_id">
              <el-option v-for="item in dashboard.scenarios" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </label>
          <label>
            <span>配置编号</span>
            <el-input v-model="faultConfigurationForm.code" maxlength="64" placeholder="NETWORK-FAULT-CONFIG" />
          </label>
          <label class="wide">
            <span>配置名称</span>
            <el-input v-model="faultConfigurationForm.name" maxlength="128" placeholder="例如 核心网络夜间保障配置" />
          </label>
          <label class="wide">
            <span>配置说明</span>
            <el-input v-model="faultConfigurationForm.description" type="textarea" :rows="2" maxlength="500" />
          </label>
          <label class="wide json-field alert-json">
            <span><b>01</b> 告警规则 JSON</span>
            <el-input v-model="faultConfigurationForm.alert_rules_text" type="textarea" :rows="8" />
          </label>
          <label class="json-field">
            <span><b>02</b> 超时策略 JSON</span>
            <el-input v-model="faultConfigurationForm.timeout_policy_text" type="textarea" :rows="7" />
          </label>
          <label class="json-field">
            <span><b>03</b> 生效时段 JSON</span>
            <el-input v-model="faultConfigurationForm.active_window_text" type="textarea" :rows="7" />
          </label>
          <label class="wide json-field">
            <span><b>04</b> 拓扑快照 JSON</span>
            <el-input v-model="faultConfigurationForm.topology_snapshot_text" type="textarea" :rows="11" />
          </label>
          <label class="wide json-field">
            <span><b>05</b> 应急预案 JSON</span>
            <el-input v-model="faultConfigurationForm.emergency_plan_text" type="textarea" :rows="10" />
          </label>
        </div>

        <div class="drawer-footer">
          <span>保存后自动执行五项完整性校验，失败版本保留为待校验草稿。</span>
          <div>
            <el-button @click="faultConfigurationFormDrawerVisible = false">取消</el-button>
            <el-button type="primary" :loading="faultConfigurationCreating" @click="submitFaultConfiguration">保存并校验</el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="faultConfigurationDrawerVisible"
      append-to-body
      class="rehearsal-drawer fault-configuration-detail-drawer"
      size="min(920px, 96vw)"
      :title="selectedFaultConfiguration?.name || '故障配置详情'"
    >
      <div v-if="selectedFaultConfiguration" v-loading="faultConfigurationDetailLoading" class="drawer-scroll">
        <section class="simulation-command fault-configuration-command">
          <div>
            <p class="eyebrow">{{ selectedFaultConfiguration.code }} · VERSION {{ selectedFaultConfiguration.version }}</p>
            <h3>{{ selectedFaultConfiguration.name }}</h3>
            <p>{{ selectedFaultConfiguration.scenario_name }} · {{ selectedFaultConfiguration.description || '版本化故障配置快照' }}</p>
          </div>
          <div class="fault-detail-state">
            <strong>{{ selectedFaultConfiguration.validation_report.check_count || 0 }}/5</strong>
            <span>校验项</span>
            <el-tag :type="faultConfigurationStatusTagType(selectedFaultConfiguration.status)" effect="dark">{{ selectedFaultConfiguration.status_label }}</el-tag>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">VALIDATION GATE</p><h3>配置门禁</h3></div>
            <span>{{ selectedFaultConfiguration.validation_report.error_count || 0 }} 个问题</span>
          </div>
          <div class="fault-validation-grid">
            <article
              v-for="check in selectedFaultConfiguration.validation_report.checks || []"
              :key="check.code"
              :class="{ passed: check.passed }"
            >
              <span>{{ check.passed ? 'PASS' : 'FAIL' }}</span>
              <strong>{{ check.name }}</strong>
              <small>{{ check.message }}</small>
            </article>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">TOPOLOGY SNAPSHOT</p><h3>故障拓扑</h3></div>
            <span>{{ selectedFaultConfiguration.topology_snapshot.version || '未标记版本' }}</span>
          </div>
          <div class="topology-board fault-detail-topology">
            <div class="topology-nodes">
              <article
                v-for="(node, index) in selectedFaultConfiguration.topology_snapshot.nodes || []"
                :key="node.id"
                :class="faultNodeStateClass(node.state)"
              >
                <span>{{ String(index + 1).padStart(2, '0') }}</span><i></i><strong>{{ node.name }}</strong><small>{{ node.id }} · {{ node.type }}</small><em>{{ faultNodeStateLabel(node.state) }}</em>
              </article>
            </div>
            <div class="topology-links"><span v-for="link in selectedFaultConfiguration.topology_snapshot.links || []" :key="`${link.source}-${link.target}`">{{ link.source }} → {{ link.target }} / {{ link.state || 'UNKNOWN' }}</span></div>
          </div>
        </section>

        <section class="drawer-section fault-detail-policy-grid">
          <article>
            <div><p class="eyebrow">ALERT RULES</p><h3>告警条件</h3></div>
            <ul class="fault-rule-list">
              <li v-for="rule in selectedFaultConfiguration.alert_rules" :key="rule.code">
                <span :class="rule.severity.toLowerCase()">{{ rule.severity }}</span>
                <div><strong>{{ rule.name }}</strong><small>{{ rule.metric_code }} {{ rule.operator }} {{ rule.threshold }}{{ rule.unit || '' }}</small></div>
              </li>
            </ul>
          </article>
          <article>
            <div><p class="eyebrow">RUNTIME POLICY</p><h3>超时与时段</h3></div>
            <div class="fault-runtime-facts">
              <span>总时限<strong>{{ selectedFaultConfiguration.timeout_policy.overall_seconds || 0 }}s</strong></span>
              <span>步骤时限<strong>{{ selectedFaultConfiguration.timeout_policy.step_seconds || 0 }}s</strong></span>
              <span>超时动作<strong>{{ selectedFaultConfiguration.timeout_policy.on_timeout || '—' }}</strong></span>
              <span>运行窗口<strong>{{ selectedFaultConfiguration.active_window.start || '—' }}—{{ selectedFaultConfiguration.active_window.end || '—' }}</strong></span>
            </div>
          </article>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">EMERGENCY PLAN</p><h3>{{ selectedFaultConfiguration.emergency_plan.name || '未绑定预案' }}</h3></div>
            <span>{{ selectedFaultConfiguration.emergency_plan.owner || '未设置负责人' }}</span>
          </div>
          <div class="fault-plan-list">
            <article v-for="(step, index) in selectedFaultConfiguration.emergency_plan.steps || []" :key="step.code">
              <span>{{ String(index + 1).padStart(2, '0') }}</span>
              <div><strong>{{ step.name }}</strong><small>{{ step.code }} · {{ step.owner_role || '未分配角色' }}</small></div>
              <em>{{ step.target_minutes || 0 }} MIN</em>
            </article>
          </div>
        </section>

        <section class="drawer-section fault-binding-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">IMMUTABLE BINDING</p><h3>实例绑定</h3></div>
            <span>{{ selectedFaultConfiguration.bound_instance_count }} 个实例</span>
          </div>
          <div v-if="selectedFaultConfiguration.bound_instances?.length" class="fault-bound-list">
            <span v-for="item in selectedFaultConfiguration.bound_instances" :key="item.id"><b>{{ item.name }}</b>{{ item.code }} · {{ item.status_label }}</span>
          </div>
          <el-empty v-else :image-size="64" description="还没有实例使用该版本" />
        </section>

        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">AUDIT LEDGER</p><h3>配置审计</h3></div><span>{{ selectedFaultConfiguration.event_count }} 条事件</span></div>
          <div class="fault-audit-list">
            <article v-for="event in selectedFaultConfiguration.events || []" :key="event.id">
              <span>{{ String(event.sequence_no).padStart(2, '0') }}</span>
              <div><strong>{{ event.action_label }}</strong><small>{{ event.operator_name || '系统' }} · {{ formatTime(event.create_time) }}</small><p>{{ event.previous_status_label }} → {{ event.current_status_label }}<template v-if="event.instance_name"> · {{ event.instance_name }}</template></p></div>
            </article>
          </div>
        </section>

        <div class="drawer-footer">
          <span>归档不影响已绑定实例中的不可变配置快照。</span>
          <div>
            <el-button :disabled="selectedFaultConfiguration.status === 'ARCHIVED'" :loading="faultConfigurationOperating" @click="cloneFaultConfiguration(selectedFaultConfiguration)">克隆新版本</el-button>
            <el-button v-if="selectedFaultConfiguration.status === 'DRAFT'" type="warning" :loading="faultConfigurationOperating" @click="validateFaultConfiguration(selectedFaultConfiguration)">重新校验</el-button>
            <el-button v-if="selectedFaultConfiguration.status !== 'ARCHIVED'" type="danger" plain :loading="faultConfigurationOperating" @click="archiveFaultConfiguration(selectedFaultConfiguration)">归档版本</el-button>
          </div>
        </div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="sceneReplayCreateDrawerVisible"
      append-to-body
      class="rehearsal-drawer scene-replay-create-drawer"
      size="min(720px, 94vw)"
      title="生成场景动态回溯"
    >
      <div class="drawer-scroll">
        <section class="simulation-command scene-replay-command">
          <div><p class="eyebrow">X29 · SNAPSHOT GENERATOR</p><h3>流量与拓扑镜像固化</h3><p>从实例已应用的 X28 配置拓扑中，回放能力调用、告警与场景控制信号。</p></div>
          <span>SHA-256</span>
        </section>
        <section class="drawer-section">
          <div class="scene-replay-form-grid">
            <label><span>预演实例</span><el-select v-model="sceneReplayForm.instance_id" placeholder="仅显示已绑定故障配置的实例" @change="syncSceneReplayRun"><el-option v-for="item in sceneReplayInstances" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
            <label><span>关联场景执行</span><el-select v-model="sceneReplayForm.scene_run_id" clearable placeholder="可选"><el-option v-for="item in availableSceneReplayRuns" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
            <label class="wide"><span>镜像名称</span><el-input v-model="sceneReplayForm.name" maxlength="128" placeholder="例如：核心链路故障前后镜像回溯" /></label>
            <label><span>窗口开始</span><el-date-picker v-model="sceneReplayForm.window_start" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ" clearable placeholder="默认全量" /></label>
            <label><span>窗口结束</span><el-date-picker v-model="sceneReplayForm.window_end" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ" clearable placeholder="默认全量" /></label>
            <label class="wide"><span>说明</span><el-input v-model="sceneReplayForm.description" type="textarea" :rows="3" maxlength="500" /></label>
          </div>
        </section>
        <div class="drawer-footer"><span>每次生成都会保存独立不可变镜像，不覆盖历史回放。</span><div><el-button @click="sceneReplayCreateDrawerVisible = false">取消</el-button><el-button type="primary" :loading="sceneReplayCreating" @click="submitSceneReplay">生成镜像</el-button></div></div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="sceneReplayDrawerVisible"
      append-to-body
      class="rehearsal-drawer scene-replay-detail-drawer"
      size="min(960px, 96vw)"
      :title="selectedSceneReplay?.name || '场景动态回溯详情'"
    >
      <div v-if="selectedSceneReplay" v-loading="sceneReplayDetailLoading" class="drawer-scroll">
        <section class="simulation-command scene-replay-command">
          <div><p class="eyebrow">{{ selectedSceneReplay.code }} · {{ selectedSceneReplay.status_label }}</p><h3>{{ selectedSceneReplay.name }}</h3><p>{{ selectedSceneReplay.instance_name }} · {{ selectedSceneReplay.fault_configuration_name }} V{{ selectedSceneReplay.fault_configuration_version }}</p></div>
          <div class="replay-checksum"><span>SHA-256</span><code>{{ selectedSceneReplay.checksum }}</code></div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">MIRROR DELTAS</p><h3>前后镜像差异</h3></div><span>{{ selectedSceneReplay.changed_node_count }} 节点 · {{ selectedSceneReplay.changed_link_count }} 链路</span></div>
          <div class="replay-delta-list">
            <article v-for="node in selectedSceneReplay.mirror_comparison?.node_deltas || []" :key="node.node_id"><span>{{ node.node_id }}</span><strong>{{ node.node_name }}</strong><small>{{ node.before_state }} → {{ node.after_state }}</small></article>
            <article v-for="link in selectedSceneReplay.mirror_comparison?.link_deltas || []" :key="`${link.source}-${link.target}`"><span>LINK</span><strong>{{ link.source }} → {{ link.target }}</strong><small>{{ link.before_state }} → {{ link.after_state }}</small></article>
          </div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">NODE TRACE</p><h3>节点级回溯</h3></div><span>{{ selectedSceneReplay.node_trace_count }} 个节点</span></div>
          <div class="replay-node-detail-list"><article v-for="node in selectedSceneReplay.node_traces || []" :key="node.node_id" :class="{ changed: node.changed }"><span>{{ node.node_id }}</span><div><strong>{{ node.node_name }}</strong><small>{{ node.node_type }} · {{ node.traffic_count }} 帧 / {{ node.attention_count }} 需关注</small></div><em>{{ node.before_state }} → {{ node.after_state }}</em></article></div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">TRAFFIC LEDGER</p><h3>流量回放事实</h3></div><span>{{ selectedSceneReplay.traffic_frame_count }} 帧</span></div>
          <div class="replay-frame-list"><article v-for="frame in selectedSceneReplay.traffic_frames || []" :key="`${frame.sequence_no}-${frame.reference_id}`"><span>{{ String(frame.sequence_no).padStart(3, '0') }}</span><div><strong>{{ frame.title }}</strong><small>{{ frame.source_node }} → {{ frame.target_node }} · {{ frame.channel_label }} · {{ frame.latency_ms }}ms</small></div><em>{{ formatTime(frame.occurred_at) }}</em></article></div>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="faultReportCreateDrawerVisible"
      append-to-body
      class="rehearsal-drawer fault-report-create-drawer"
      size="min(760px, 94vw)"
      title="发起故障上报"
    >
      <div class="drawer-scroll">
        <section class="simulation-command fault-report-command">
          <div><p class="eyebrow">X30 · INCIDENT INTAKE</p><h3>故障事实首次固化</h3><p>仅允许选择已应用 X28 故障配置的实例，上报后模板、阶段和配置事实均不可覆盖。</p></div>
          <span>{{ selectedFaultReportTemplate?.default_level_label || '待选择模板' }}</span>
        </section>
        <section class="drawer-section">
          <div class="fault-report-form-grid">
            <label><span>预演实例</span><el-select v-model="faultReportForm.instance_id" placeholder="选择已绑定故障配置的实例" @change="syncFaultReportForm"><el-option v-for="item in faultReportInstances" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
            <label><span>上报模板</span><el-select v-model="faultReportForm.template_id" placeholder="选择版本化模板" @change="applyFaultReportTemplate"><el-option v-for="item in availableFaultReportTemplates" :key="item.id" :label="`${item.name} · V${item.version}`" :value="item.id" /></el-select></label>
            <label><span>故障等级</span><el-select v-model="faultReportForm.level"><el-option label="一级故障" value="LEVEL_1" /><el-option label="二级故障" value="LEVEL_2" /><el-option label="三级故障" value="LEVEL_3" /><el-option label="四级故障" value="LEVEL_4" /></el-select></label>
            <label><span>关联场景执行</span><el-select v-model="faultReportForm.scene_run_id" clearable placeholder="可选"><el-option v-for="item in availableFaultReportSceneRuns" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
            <label class="wide"><span>故障标题</span><el-input v-model="faultReportForm.title" maxlength="128" placeholder="例如：核心网络节点异常导致业务抖动" /></label>
            <label class="wide"><span>故障描述</span><el-input v-model="faultReportForm.description" type="textarea" :rows="3" maxlength="1000" placeholder="描述发现方式、异常现象与初步判断" /></label>
            <label class="wide"><span>影响范围</span><el-input v-model="faultReportForm.impact_scope" type="textarea" :rows="2" maxlength="500" placeholder="业务、区域、客户与节点影响" /></label>
            <label><span>证据引用编号</span><el-input v-model="faultReportForm.attachment_reference_id" maxlength="128" placeholder="可选，例如 OBS-20260917-001" /></label>
            <label><span>证据文件名</span><el-input v-model="faultReportForm.attachment_file_name" maxlength="255" placeholder="可选，例如 core-node.log" /></label>
          </div>
          <div v-if="selectedFaultReportTemplate" class="fault-report-template-preview">
            <span v-for="(stage, index) in selectedFaultReportTemplate.stage_definitions" :key="stage.code"><b>{{ index + 1 }}</b>{{ stage.name }}<small>{{ stage.owner_role }} · {{ stage.duration_minutes }} 分钟</small></span>
          </div>
        </section>
        <div class="drawer-footer"><span>附件 V1 保存外部引用与元数据，不上传真实文件。</span><div><el-button @click="faultReportCreateDrawerVisible = false">取消</el-button><el-button type="primary" :loading="faultReportCreating" @click="submitFaultReport">创建草稿</el-button></div></div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="faultReportDrawerVisible"
      append-to-body
      class="rehearsal-drawer fault-report-detail-drawer"
      size="min(920px, 96vw)"
      :title="selectedFaultReport?.title || '故障上报详情'"
    >
      <div v-if="selectedFaultReport" v-loading="faultReportDetailLoading" class="drawer-scroll">
        <section class="simulation-command fault-report-command">
          <div><p class="eyebrow">{{ selectedFaultReport.code }} · {{ selectedFaultReport.template_name }} V{{ selectedFaultReport.template_version }}</p><h3>{{ selectedFaultReport.title }}</h3><p>{{ selectedFaultReport.instance_name }} · {{ selectedFaultReport.impact_scope }}</p></div>
          <div class="fault-report-drawer-status" :class="selectedFaultReport.level.toLowerCase()"><strong>{{ selectedFaultReport.level_label }}</strong><span>{{ selectedFaultReport.status_label }}</span></div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">STAGED SLA</p><h3>分阶段上报进度</h3></div><span :class="{ 'text-danger': faultReportCountdown.overdue }">{{ faultReportCountdown.text }}</span></div>
          <div class="fault-report-detail-stages"><article v-for="(stage, index) in selectedFaultReport.template_snapshot.stage_definitions || []" :key="stage.code" :class="{ done: index + 1 < selectedFaultReport.stage_index, current: stage.code === selectedFaultReport.current_stage_code }"><span>{{ index + 1 }}</span><div><strong>{{ stage.name }}</strong><small>{{ stage.code }} · {{ stage.owner_role }}</small></div><em>{{ stage.duration_minutes }} MIN</em></article></div>
        </section>

        <section v-if="selectedFaultReport.allowed_actions.length" class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">RUNTIME CONTROL</p><h3>上报推进控制</h3></div><span>{{ selectedFaultReport.current_stage_name }}</span></div>
          <div class="fault-report-action-form">
            <el-select v-model="faultReportActionForm.action" placeholder="选择操作"><el-option v-for="action in selectedFaultReport.allowed_actions" :key="action" :label="faultReportActionLabel(action)" :value="action" /></el-select>
            <el-select v-if="faultReportActionForm.action === 'ESCALATED'" v-model="faultReportActionForm.level" placeholder="目标等级"><el-option label="一级故障" value="LEVEL_1" /><el-option label="二级故障" value="LEVEL_2" /><el-option label="三级故障" value="LEVEL_3" /></el-select>
            <template v-if="faultReportActionForm.action === 'ATTACHMENT_ADDED'">
              <el-input v-model="faultReportActionForm.attachment_reference_id" placeholder="证据引用编号" />
              <el-input v-model="faultReportActionForm.attachment_file_name" placeholder="证据文件名" />
            </template>
            <el-input v-model="faultReportActionForm.note" type="textarea" :rows="2" maxlength="500" placeholder="处置说明（推进、升级、恢复和关闭时必填）" />
            <el-button type="primary" :loading="faultReportOperating" @click="submitFaultReportAction">执行操作</el-button>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">EVIDENCE REFERENCES</p><h3>证据引用</h3></div><span>{{ selectedFaultReport.attachment_count }} 份</span></div>
          <div v-if="selectedFaultReport.attachments.length" class="fault-report-attachment-list"><article v-for="attachment in selectedFaultReport.attachments" :key="attachment.reference_id"><span>REF</span><div><strong>{{ attachment.file_name }}</strong><small>{{ attachment.reference_id }} · {{ attachment.content_type }} · {{ formatFileSize(attachment.file_size) }}</small></div><em>{{ attachment.added_by || '系统' }}</em></article></div>
          <el-empty v-else :image-size="54" description="暂无证据引用" />
        </section>

        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">IMMUTABLE EVENT LEDGER</p><h3>上报事实链</h3></div><span>{{ selectedFaultReport.event_count }} 条事件</span></div>
          <div class="fault-report-event-list"><article v-for="event in selectedFaultReport.events || []" :key="event.id"><span>{{ String(event.sequence_no).padStart(2, '0') }}</span><div><strong>{{ event.action_label }}</strong><small>{{ event.operator_name || '系统' }} · {{ formatTime(event.create_time) }}</small><p>{{ event.previous_status_label }} → {{ event.current_status_label }} · {{ event.previous_stage_code || 'START' }} → {{ event.current_stage_code }}</p></div></article></div>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="auxiliarySimulationCreateDrawerVisible"
      append-to-body
      class="rehearsal-drawer auxiliary-create-drawer"
      size="min(860px, 96vw)"
      title="组合随机因子"
    >
      <div class="drawer-scroll">
        <section class="simulation-command auxiliary-drawer-command">
          <div><p class="eyebrow">X31 · REPRODUCIBLE STOCHASTIC RUN</p><h3>把不确定性变成可复现实验</h3><p>同一随机种子、时长和因子配置会生成相同数值结果与 SHA-256，可用于复跑对比。</p></div>
          <span>SEED {{ auxiliarySimulationForm.seed }}</span>
        </section>
        <section class="drawer-section">
          <div class="auxiliary-base-form">
            <label><span>预演实例</span><el-select v-model="auxiliarySimulationForm.instance_id" placeholder="选择预演实例"><el-option v-for="item in dashboard.instances" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
            <label><span>演练名称</span><el-input v-model="auxiliarySimulationForm.name" maxlength="160" placeholder="例如：核心网抖动与流量峰值组合" /></label>
            <label><span>随机种子</span><el-input-number v-model="auxiliarySimulationForm.seed" :min="0" :max="4294967295" controls-position="right" /></label>
            <label><span>演练时长</span><el-input-number v-model="auxiliarySimulationForm.duration_minutes" :min="5" :max="720" controls-position="right" /><small>分钟</small></label>
          </div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">FACTOR MIXER</p><h3>随机因子组合</h3></div><span>{{ auxiliarySimulationForm.factors.filter((item) => item.enabled).length }} 项已启用</span></div>
          <div class="auxiliary-factor-form-list">
            <article v-for="factor in auxiliarySimulationForm.factors" :key="factor.code" :class="[factor.category.toLowerCase(), { enabled: factor.enabled }]">
              <header><el-switch v-model="factor.enabled" /><div><small>{{ factorCategoryLabel(factor.category) }} · {{ factor.code }}</small><strong>{{ factor.name }}</strong></div><em>{{ factor.unit }}</em></header>
              <div>
                <label><span>分布</span><el-select v-model="factor.distribution" :disabled="!factor.enabled"><el-option label="均匀分布" value="UNIFORM" /><el-option label="正态分布" value="NORMAL" /></el-select></label>
                <label><span>最小值</span><el-input-number v-model="factor.min_value" :disabled="!factor.enabled" :min="0" :precision="2" controls-position="right" /></label>
                <label><span>最大值</span><el-input-number v-model="factor.max_value" :disabled="!factor.enabled" :min="0.01" :precision="2" controls-position="right" /></label>
                <label><span>触发概率</span><el-slider v-model="factor.trigger_probability" :disabled="!factor.enabled" :min="0" :max="1" :step="0.05" :format-tooltip="(value: number) => `${Math.round(value * 100)}%`" /></label>
              </div>
            </article>
          </div>
        </section>
        <div class="drawer-footer"><span>结果将固化分钟级原始数据、统计对比、影响分析和异常点。</span><div><el-button @click="auxiliarySimulationCreateDrawerVisible = false">取消</el-button><el-button type="primary" :loading="auxiliarySimulationCreating" @click="submitAuxiliarySimulation">运行演练</el-button></div></div>
      </div>
    </el-drawer>

    <el-drawer
      v-model="auxiliarySimulationDrawerVisible"
      append-to-body
      class="rehearsal-drawer auxiliary-detail-drawer"
      size="min(960px, 96vw)"
      :title="selectedAuxiliarySimulation?.name || '辅助演练分析'"
    >
      <div v-if="selectedAuxiliarySimulation" v-loading="auxiliarySimulationDetailLoading" class="drawer-scroll">
        <section class="simulation-command auxiliary-drawer-command">
          <div><p class="eyebrow">{{ selectedAuxiliarySimulation.code }} · {{ selectedAuxiliarySimulation.instance_name }}</p><h3>{{ selectedAuxiliarySimulation.name }}</h3><p>{{ selectedAuxiliarySimulation.summary.conclusion }}</p></div>
          <span>SEED {{ selectedAuxiliarySimulation.seed }}</span>
        </section>
        <section class="drawer-section auxiliary-export-console">
          <div><p class="eyebrow">MULTI-FORMAT REPORT</p><h3>结果报告下载</h3><span>PDF 含图表分析，Excel/JSON 完整版包含分钟级原始数据。</span></div>
          <el-select v-model="auxiliaryExportForm.report_level"><el-option label="精简版" value="summary" /><el-option label="完整版" value="full" /></el-select>
          <el-select v-model="auxiliaryExportForm.export_format"><el-option label="PDF 报告" value="pdf" /><el-option label="Excel 数据" value="xlsx" /><el-option label="JSON 集成" value="json" /></el-select>
          <el-button type="primary" :loading="auxiliarySimulationExporting" @click="exportSelectedAuxiliary">下载报告</el-button>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">FACTOR IMPACT</p><h3>随机因子影响分析</h3></div><span>{{ selectedAuxiliarySimulation.triggered_factor_count }}/{{ selectedAuxiliarySimulation.factor_count }} 项命中</span></div>
          <div class="auxiliary-impact-list"><article v-for="(item, index) in selectedAuxiliarySimulation.impact_analysis" :key="index"><span>{{ String(index + 1).padStart(2, '0') }}</span><p>{{ item }}</p></article></div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">STATISTICAL DELTA</p><h3>注入前后统计对比</h3></div><span>均值 · 峰值 · 方差</span></div>
          <div class="auxiliary-stat-grid"><article v-for="item in selectedAuxiliarySimulation.statistics" :key="item.code"><small>{{ item.name }}</small><strong>{{ item.mean }}</strong><p>基线 {{ item.baseline }} · 峰值 {{ item.peak }}</p><em :class="{ rising: item.delta_percent > 0 }">{{ item.delta_percent > 0 ? '+' : '' }}{{ item.delta_percent }}%</em></article></div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">ANOMALY MARKERS</p><h3>异常点标注</h3></div><span>{{ selectedAuxiliarySimulation.anomaly_count }} 个窗口</span></div>
          <div v-if="selectedAuxiliarySimulation.anomalies?.length" class="auxiliary-anomaly-list"><article v-for="item in selectedAuxiliarySimulation.anomalies" :key="item.minute"><span>{{ item.minute }} MIN</span><div><strong>{{ item.reasons.join('；') }}</strong><small>{{ formatTime(item.occurred_at) }}</small></div></article></div>
          <el-empty v-else :image-size="54" description="本批次未识别到超阈值异常点" />
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="processDrawerVisible"
      append-to-body
      class="rehearsal-drawer process-drawer"
      size="min(860px, 94vw)"
      :title="selectedProcess?.name || '处置进度'"
    >
      <div v-if="selectedProcess" v-loading="processDetailLoading" class="drawer-scroll">
        <section class="process-command">
          <div>
            <p class="eyebrow">{{ selectedProcess.code }} · {{ selectedProcess.template_name }}</p>
            <h3>{{ selectedProcess.name }}</h3>
            <p>{{ selectedProcess.instance_name }} · {{ selectedProcess.auto_advance ? '自动推进' : '人工推进' }}</p>
          </div>
          <div class="process-command-status">
            <strong>{{ selectedProcess.progress_percent }}%</strong>
            <el-tag :type="processTagType(selectedProcess.status)" effect="dark">
              {{ selectedProcess.status_label }}
            </el-tag>
          </div>
        </section>

        <section class="drawer-section process-control">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">RUNTIME CONTROL</p>
              <h3>流程推进控制</h3>
            </div>
            <span>{{ selectedProcess.completed_steps }}/{{ selectedProcess.total_steps }} 步已处理</span>
          </div>
          <el-progress
            :percentage="selectedProcess.progress_percent"
            :stroke-width="10"
            :status="selectedProcess.status === 'FAILED' ? 'exception' : undefined"
          />
          <div v-if="selectedProcess.blocked_reason" class="blocked-reason">
            阻塞原因：{{ selectedProcess.blocked_reason }}
          </div>
          <div class="process-operation-form">
            <el-input
              v-model="processOperateForm.note"
              maxlength="500"
              placeholder="本次操作说明（可选）"
            />
            <el-input
              v-if="['RUNNING', 'BLOCKED'].includes(selectedProcess.status)"
              v-model="processOperateForm.reason"
              maxlength="500"
              placeholder="阻塞或失败原因"
            />
          </div>
          <div class="control-actions process-actions">
            <el-button
              v-if="selectedProcess.status === 'PENDING'"
              type="primary"
              :loading="processOperating"
              @click="operateProcess('START')"
            >启动流程</el-button>
            <template v-if="selectedProcess.status === 'RUNNING'">
              <el-button
                type="primary"
                :loading="processOperating"
                @click="operateProcess(selectedProcess.auto_advance ? 'AUTO_ADVANCE' : 'COMPLETE_STEP')"
              >{{ selectedProcess.auto_advance ? '自动推进一步' : '完成当前步骤' }}</el-button>
              <el-button :loading="processOperating" @click="operateProcess('BLOCK')">阻塞</el-button>
              <el-button :loading="processOperating" @click="operateProcess('SKIP')">跳过</el-button>
              <el-button type="danger" plain :loading="processOperating" @click="operateProcess('FAIL')">
                标记失败
              </el-button>
            </template>
            <el-button
              v-if="selectedProcess.status === 'BLOCKED'"
              type="success"
              :loading="processOperating"
              @click="operateProcess('RESUME')"
            >恢复执行</el-button>
            <el-button
              v-if="['PENDING', 'RUNNING', 'BLOCKED'].includes(selectedProcess.status)"
              plain
              :loading="processOperating"
              @click="operateProcess('CANCEL')"
            >取消流程</el-button>
            <span v-if="['COMPLETED', 'CANCELLED', 'FAILED'].includes(selectedProcess.status)">
              流程已结束，步骤快照与事件记录仍永久保留。
            </span>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">EXECUTION PATH</p>
              <h3>动态处置步骤</h3>
            </div>
            <span>模板快照，不受后续修改影响</span>
          </div>
          <div class="process-step-list">
            <article
              v-for="step in selectedProcess.steps || []"
              :key="step.id"
              class="process-step-card"
              :class="step.status.toLowerCase()"
            >
              <span class="process-step-index">{{ String(step.sequence_no).padStart(2, '0') }}</span>
              <div>
                <div class="process-step-title">
                  <strong>{{ step.name }}</strong>
                  <el-tag :type="stepTagType(step.status)" size="small" effect="plain">
                    {{ step.status_label }}
                  </el-tag>
                </div>
                <p>{{ step.description }}</p>
                <small>{{ step.owner_role }} · 计划 {{ step.planned_minutes }} 分钟</small>
                <em v-if="step.note">{{ step.note }}</em>
              </div>
            </article>
          </div>
        </section>

        <section class="drawer-section event-section">
          <div class="drawer-heading">
            <div>
              <p class="eyebrow">PROCESS AUDIT</p>
              <h3>流程事件</h3>
            </div>
            <span>共 {{ selectedProcess.events?.length || 0 }} 条</span>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="event in selectedProcess.events || []"
              :key="event.id"
              :timestamp="formatTime(event.create_time)"
              placement="top"
            >
              <strong>{{ event.action_label }}{{ event.step_name ? ` · ${event.step_name}` : '' }}</strong>
              <p>{{ event.previous_status_label }} → {{ event.current_status_label }} · {{ event.operator_name }}</p>
            </el-timeline-item>
          </el-timeline>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="sceneLibraryDrawerVisible"
      append-to-body
      class="rehearsal-drawer scene-library-drawer"
      size="min(900px, 96vw)"
      :title="selectedSceneLibrary?.name || '预演场景库'"
    >
      <div v-if="selectedSceneLibrary" v-loading="sceneLibraryDetailLoading" class="drawer-scroll">
        <section class="scene-command library-command">
          <div>
            <p class="eyebrow">{{ selectedSceneLibrary.code }} · V{{ selectedSceneLibrary.version }}</p>
            <h3>{{ selectedSceneLibrary.name }}</h3>
            <p>{{ selectedSceneLibrary.script_name }} · {{ selectedSceneLibrary.visibility_label }}</p>
          </div>
          <div class="process-command-status">
            <strong>{{ selectedSceneLibrary.run_count }}</strong>
            <span>执行次数</span>
            <el-tag :type="sceneLibraryTagType(selectedSceneLibrary.status)" effect="dark">
              {{ selectedSceneLibrary.status_label }}
            </el-tag>
          </div>
        </section>

        <section class="drawer-section library-link-grid">
          <div>
            <span>默认实例</span>
            <strong>{{ selectedSceneLibrary.default_instance_name || '未绑定' }}</strong>
          </div>
          <div>
            <span>流程模板</span>
            <strong>{{ selectedSceneLibrary.process_template_name || '未绑定' }}</strong>
          </div>
          <div>
            <span>数据模型</span>
            <strong>{{ selectedSceneLibrary.data_model_name || '未绑定' }}</strong>
          </div>
          <div>
            <span>权限角色</span>
            <strong>{{ selectedSceneLibrary.permission_roles.join(', ') || '未限制' }}</strong>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">SCRIPT SNAPSHOT</p><h3>剧本步骤</h3></div>
            <span>{{ selectedSceneLibrary.script?.step_count || 0 }} 步</span>
          </div>
          <div class="process-step-list">
            <article
              v-for="(step, index) in selectedSceneLibrary.script?.steps || []"
              :key="step.code"
              class="process-step-card"
            >
              <span class="process-step-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <div class="process-step-title"><strong>{{ step.name }}</strong></div>
                <p>{{ step.description }}</p>
                <small>预期：{{ step.expected_result || '按步骤说明完成' }}</small>
              </div>
            </article>
          </div>
        </section>

        <section class="drawer-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">RUN HISTORY</p><h3>场景执行记录</h3></div>
            <el-button
              type="primary"
              plain
              :disabled="selectedSceneLibrary.status !== 'READY'"
              @click="openSceneLibraryRun(selectedSceneLibrary)"
            >从库创建执行</el-button>
          </div>
          <div class="instance-process-list">
            <button
              v-for="run in selectedSceneLibrary.scene_runs || []"
              :key="run.id"
              type="button"
              @click="openSceneRun(run)"
            >
              <div><strong>{{ run.name }}</strong><small>{{ run.instance_name }} · {{ run.progress_percent }}%</small></div>
              <el-tag :type="sceneTagType(run.status)" effect="plain">{{ run.status_label }}</el-tag>
            </button>
          </div>
        </section>

        <section class="drawer-section event-section">
          <div class="drawer-heading">
            <div><p class="eyebrow">LIBRARY AUDIT</p><h3>场景库事件</h3></div>
            <span>共 {{ selectedSceneLibrary.events?.length || 0 }} 条</span>
          </div>
          <el-timeline>
            <el-timeline-item
              v-for="event in selectedSceneLibrary.events || []"
              :key="event.id"
              :timestamp="formatTime(event.create_time)"
              placement="top"
            >
              <strong>{{ event.action_label }}</strong>
              <p>{{ event.previous_status_label }} → {{ event.current_status_label }} · {{ event.operator_name }}</p>
            </el-timeline-item>
          </el-timeline>
        </section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="sceneLibraryFormDrawerVisible"
      append-to-body
      class="rehearsal-drawer scene-library-form-drawer"
      size="min(780px, 94vw)"
      :title="sceneLibraryForm.mode === 'create' ? '新建预演场景库' : '克隆预演场景库'"
    >
      <div class="drawer-scroll">
        <section class="simulation-form-intro scene-form-intro">
          <div>
            <p class="eyebrow">LIBRARY CONFIG · VERSIONING</p>
            <h3>沉淀可复用的场景版本</h3>
            <p>先绑定剧本，再按需关联默认实例、流程模板和数据模型；克隆会继承源库配置。</p>
          </div>
          <span>{{ sceneLibraryForm.mode === 'create' ? '新版本' : '克隆版本' }}</span>
        </section>

        <section class="drawer-section scene-library-form-grid">
          <label>
            <span>所属场景</span>
            <el-select v-model="sceneLibraryForm.scenario_id" :disabled="sceneLibraryForm.mode === 'clone'">
              <el-option v-for="item in dashboard.scenarios" :key="item.id" :label="item.name" :value="item.id" />
            </el-select>
          </label>
          <label>
            <span>场景剧本</span>
            <el-select v-model="sceneLibraryForm.script_id" :disabled="sceneLibraryForm.mode === 'clone'">
              <el-option v-for="item in sceneLibraryScripts" :key="item.id" :label="`${item.name} · V${item.version}`" :value="item.id" />
            </el-select>
          </label>
          <label>
            <span>场景库编号</span>
            <el-input v-model="sceneLibraryForm.code" :disabled="sceneLibraryForm.mode === 'clone'" maxlength="64" placeholder="例如 NETWORK-FAULT-LIB" />
          </label>
          <label>
            <span>可见范围</span>
            <el-select v-model="sceneLibraryForm.visibility">
              <el-option label="工作空间可用" value="WORKSPACE" />
              <el-option label="仅创建人可用" value="PRIVATE" />
            </el-select>
          </label>
          <label class="wide-field">
            <span>场景库名称</span>
            <el-input v-model="sceneLibraryForm.name" maxlength="128" />
          </label>
          <label class="wide-field">
            <span>说明</span>
            <el-input v-model="sceneLibraryForm.description" type="textarea" :rows="2" maxlength="500" show-word-limit />
          </label>
          <label>
            <span>默认实例</span>
            <el-select v-model="sceneLibraryForm.default_instance_id" clearable placeholder="可选">
              <el-option v-for="item in sceneLibraryInstances" :key="item.id" :label="`${item.name} · ${item.status_label}`" :value="item.id" />
            </el-select>
          </label>
          <label>
            <span>流程模板</span>
            <el-select v-model="sceneLibraryForm.process_template_id" clearable placeholder="可选">
              <el-option v-for="item in dashboard.process_templates" :key="item.id" :label="`${item.name} · V${item.version}`" :value="item.id" />
            </el-select>
          </label>
          <label>
            <span>数据模型</span>
            <el-select v-model="sceneLibraryForm.data_model_id" clearable placeholder="可选">
              <el-option v-for="item in sceneLibraryDataModels" :key="item.id" :label="`${item.name} · V${item.current_version}`" :value="item.id" />
            </el-select>
          </label>
          <label>
            <span>权限角色</span>
            <el-input v-model="sceneLibraryForm.permission_roles" placeholder="逗号分隔，例如 WORKSPACE_MANAGE" />
          </label>
          <label v-if="sceneLibraryForm.mode === 'clone'" class="wide-field">
            <span>克隆说明</span>
            <el-input v-model="sceneLibraryForm.note" maxlength="500" placeholder="本次克隆调整点" />
          </label>
        </section>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <span>保存后会记录场景库事件，执行历史不会被覆盖。</span>
          <div>
            <el-button @click="sceneLibraryFormDrawerVisible = false">取消</el-button>
            <el-button type="primary" :loading="sceneLibraryCreating" @click="submitSceneLibraryForm">保存场景库</el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-drawer
      v-model="sceneLibraryRunDrawerVisible"
      append-to-body
      class="rehearsal-drawer scene-library-run-drawer"
      size="min(620px, 94vw)"
      title="从场景库创建执行"
    >
      <div class="drawer-scroll">
        <section class="simulation-form-intro scene-form-intro">
          <div>
            <p class="eyebrow">RUN FROM LIBRARY</p>
            <h3>{{ selectedSceneLibrary?.name || '选择场景库' }}</h3>
            <p>会自动取目标实例最新的申告批次、趋势数据和处置流程，用于快速拉起场景执行。</p>
          </div>
          <span>V{{ selectedSceneLibrary?.version || '-' }}</span>
        </section>
        <section class="drawer-section scene-library-run-grid">
          <label class="wide-field">
            <span>目标实例</span>
            <el-select v-model="sceneLibraryRunForm.instance_id" placeholder="选择预演实例">
              <el-option v-for="item in availableDataInstances" :key="item.id" :label="`${item.name} · ${item.status_label}`" :value="item.id" />
            </el-select>
          </label>
          <label class="wide-field">
            <span>执行名称</span>
            <el-input v-model="sceneLibraryRunForm.name" maxlength="128" placeholder="留空使用场景库名称和实例名称" />
          </label>
          <label class="library-switch">
            <el-switch v-model="sceneLibraryRunForm.include_latest_complaint_batch" />
            <span>注入最新申告批次</span>
          </label>
          <label class="library-switch">
            <el-switch v-model="sceneLibraryRunForm.include_latest_data_batch" />
            <span>注入最新趋势批次</span>
          </label>
          <label class="library-switch">
            <el-switch v-model="sceneLibraryRunForm.include_latest_process_run" />
            <span>注入最新处置流程</span>
          </label>
        </section>
      </div>
      <template #footer>
        <div class="drawer-footer">
          <span>至少需要一个可注入数据源，否则后端会拒绝创建。</span>
          <div>
            <el-button @click="sceneLibraryRunDrawerVisible = false">取消</el-button>
            <el-button type="primary" :loading="sceneLibraryRunning" @click="createSceneRunFromLibrary">创建执行</el-button>
          </div>
        </div>
      </template>
    </el-drawer>

    <el-drawer
      v-model="sceneScriptDrawerVisible"
      append-to-body
      class="rehearsal-drawer scene-script-drawer"
      size="min(820px, 94vw)"
      title="新建场景剧本"
    >
      <div class="drawer-scroll">
        <section class="simulation-form-intro scene-form-intro">
          <div><p class="eyebrow">SCRIPT EDITOR · X21</p><h3>把预演动作编排成可执行步骤</h3><p>每次保存生成一个新版本，历史执行继续使用创建时的剧本快照。</p></div>
          <span>{{ sceneScriptForm.steps.length }} 个步骤</span>
        </section>
        <section class="drawer-section">
          <div class="scene-script-base-grid">
            <label><span>所属场景</span><el-select v-model="sceneScriptForm.scenario_id" placeholder="选择预演场景"><el-option v-for="item in dashboard.scenarios" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
            <label><span>剧本编号</span><el-input v-model="sceneScriptForm.code" maxlength="64" placeholder="例如 NETWORK-FAULT-CUSTOM" /></label>
            <label class="wide-field"><span>剧本名称</span><el-input v-model="sceneScriptForm.name" maxlength="128" /></label>
            <label class="wide-field"><span>剧本说明</span><el-input v-model="sceneScriptForm.description" type="textarea" :rows="2" maxlength="500" show-word-limit /></label>
          </div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">EXECUTION STEPS</p><h3>执行步骤</h3></div><el-button plain :disabled="sceneScriptForm.steps.length >= 20" @click="addSceneScriptStep">添加步骤</el-button></div>
          <div class="scene-step-editor-list">
            <article v-for="(step, index) in sceneScriptForm.steps" :key="index" class="scene-step-editor">
              <span>{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <div class="scene-step-editor-row"><el-input v-model="step.code" maxlength="64" placeholder="步骤编号" /><el-input v-model="step.name" maxlength="128" placeholder="步骤名称" /></div>
                <el-input v-model="step.description" maxlength="500" placeholder="执行说明" />
                <el-input v-model="step.expected_result" maxlength="500" placeholder="预期结果" />
              </div>
              <el-button link type="danger" :disabled="sceneScriptForm.steps.length === 1" @click="removeSceneScriptStep(index)">删除</el-button>
            </article>
          </div>
        </section>
      </div>
      <template #footer><div class="drawer-footer"><span>保存后即可用于同一预演场景下的实例。</span><div><el-button @click="sceneScriptDrawerVisible = false">取消</el-button><el-button type="primary" :loading="sceneScriptCreating" @click="createSceneScript">保存剧本版本</el-button></div></div></template>
    </el-drawer>

    <el-drawer
      v-model="sceneCreateDrawerVisible"
      append-to-body
      class="rehearsal-drawer scene-create-drawer"
      size="min(760px, 94vw)"
      title="创建场景执行"
    >
      <div class="drawer-scroll">
        <section class="simulation-form-intro scene-form-intro">
          <div><p class="eyebrow">DATA INJECTION · X21</p><h3>选择剧本并装配预演数据</h3><p>注入对象必须来自同一个预演实例，创建后会固化快照便于审计。</p></div>
          <span>{{ sceneInjectionCount }} 项注入</span>
        </section>
        <section class="drawer-section scene-create-form">
          <label><span>预演实例</span><el-select v-model="sceneCreateForm.instance_id" placeholder="选择活动实例" @change="loadSceneSourceInstance"><el-option v-for="item in availableDataInstances" :key="item.id" :label="`${item.name} · ${item.status_label}`" :value="item.id" /></el-select></label>
          <label><span>场景剧本</span><el-select v-model="sceneCreateForm.script_id" placeholder="选择匹配剧本"><el-option v-for="item in availableSceneScripts" :key="item.id" :label="`${item.name} · V${item.version}`" :value="item.id" /></el-select></label>
          <label><span>执行名称</span><el-input v-model="sceneCreateForm.name" maxlength="128" placeholder="留空自动生成" /></label>
          <label><span>申告批次</span><el-select v-model="sceneCreateForm.complaint_batch_ids" multiple collapse-tags placeholder="可多选"><el-option v-for="item in sceneSourceInstance?.batches || []" :key="item.id" :label="`V${item.version} · ${item.template_name} · ${item.valid_count}条`" :value="item.id" /></el-select></label>
          <label><span>趋势数据批次</span><el-select v-model="sceneCreateForm.data_batch_ids" multiple collapse-tags placeholder="可多选"><el-option v-for="item in sceneSourceInstance?.data_batches || []" :key="item.id" :label="`${item.name} · ${item.point_count}点`" :value="item.id" /></el-select></label>
          <label><span>处置流程</span><el-select v-model="sceneCreateForm.process_run_ids" multiple collapse-tags placeholder="可多选"><el-option v-for="item in sceneSourceInstance?.process_runs || []" :key="item.id" :label="`${item.name} · ${item.status_label}`" :value="item.id" /></el-select></label>
        </section>
        <section class="drawer-section injection-checklist">
          <div class="drawer-heading"><div><p class="eyebrow">INJECTION CHECK</p><h3>装配检查</h3></div><span>至少选择一类数据</span></div>
          <div><span>申告批次</span><strong>{{ sceneCreateForm.complaint_batch_ids.length }}</strong></div>
          <div><span>趋势批次</span><strong>{{ sceneCreateForm.data_batch_ids.length }}</strong></div>
          <div><span>处置流程</span><strong>{{ sceneCreateForm.process_run_ids.length }}</strong></div>
        </section>
      </div>
      <template #footer><div class="drawer-footer"><span>创建后由操作员逐步启动、完成、跳过或失败收口。</span><div><el-button @click="sceneCreateDrawerVisible = false">取消</el-button><el-button type="primary" :loading="sceneCreating" @click="createSceneRun">创建并进入</el-button></div></div></template>
    </el-drawer>

    <el-drawer
      v-model="sceneDrawerVisible"
      append-to-body
      class="rehearsal-drawer scene-run-drawer"
      size="min(900px, 96vw)"
      :title="selectedScene?.name || '场景执行'"
    >
      <div v-if="selectedScene" v-loading="sceneDetailLoading" class="drawer-scroll">
        <section class="scene-command">
          <div><p class="eyebrow">{{ selectedScene.code }} · {{ selectedScene.script_name }}</p><h3>{{ selectedScene.name }}</h3><p>{{ selectedScene.instance_name }} · 剧本 V{{ selectedScene.script_version }}</p></div>
          <div class="process-command-status"><strong>{{ selectedScene.progress_percent }}%</strong><el-tag :type="sceneTagType(selectedScene.status)" effect="dark">{{ selectedScene.status_label }}</el-tag></div>
        </section>
        <section class="drawer-section process-control">
          <div class="drawer-heading"><div><p class="eyebrow">SCENE CONTROL</p><h3>场景推进控制</h3></div><span>{{ selectedScene.completed_steps }}/{{ selectedScene.total_steps }} 步已处理</span></div>
          <el-progress :percentage="selectedScene.progress_percent" :stroke-width="10" :status="selectedScene.status === 'FAILED' ? 'exception' : undefined" />
          <div class="process-operation-form"><el-input v-model="sceneOperateForm.note" maxlength="500" placeholder="当前步骤执行说明（可选）" /><el-input v-if="selectedScene.status === 'RUNNING'" v-model="sceneOperateForm.reason" maxlength="500" placeholder="失败原因（标记失败时必填）" /></div>
          <div class="control-actions process-actions">
            <el-button v-if="selectedScene.status === 'PENDING'" type="primary" :loading="sceneOperating" @click="operateScene('START')">启动场景</el-button>
            <template v-if="selectedScene.status === 'RUNNING'"><el-button type="primary" :loading="sceneOperating" @click="operateScene('COMPLETE_STEP')">完成当前步骤</el-button><el-button :loading="sceneOperating" @click="operateScene('SKIP_STEP')">跳过步骤</el-button><el-button type="danger" plain :loading="sceneOperating" @click="operateScene('FAIL')">标记失败</el-button></template>
            <el-button v-if="['PENDING', 'RUNNING'].includes(selectedScene.status)" plain :loading="sceneOperating" @click="operateScene('CANCEL')">取消场景</el-button>
            <span v-if="['COMPLETED', 'CANCELLED', 'FAILED'].includes(selectedScene.status)">场景已结束，可查看自动总结并处理人工工单。</span>
          </div>
        </section>
        <section class="drawer-section injection-overview">
          <div class="drawer-heading"><div><p class="eyebrow">INJECTED SNAPSHOT</p><h3>数据注入快照</h3></div><span>创建后不可变</span></div>
          <div class="injection-metrics"><div><strong>{{ selectedScene.injected_snapshot.totals.complaints || 0 }}</strong><span>有效申告</span></div><div><strong>{{ selectedScene.injected_snapshot.totals.data_points || 0 }}</strong><span>趋势点</span></div><div><strong>{{ selectedScene.injected_snapshot.totals.process_runs || 0 }}</strong><span>处置流程</span></div></div>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">EXECUTION PATH</p><h3>场景剧本步骤</h3></div><span>逐步执行并保留输出</span></div>
          <div class="process-step-list"><article v-for="step in selectedScene.steps || []" :key="step.id" class="process-step-card" :class="step.status.toLowerCase()"><span class="process-step-index">{{ String(step.sequence_no).padStart(2, '0') }}</span><div><div class="process-step-title"><strong>{{ step.name }}</strong><el-tag :type="sceneStepTagType(step.status)" size="small" effect="plain">{{ step.status_label }}</el-tag></div><p>{{ step.description }}</p><small>预期：{{ step.expected_result || '按步骤说明完成' }}</small><em v-if="step.note">{{ step.note }}</em></div></article></div>
        </section>
        <section v-if="selectedScene.summary.conclusion" class="drawer-section scene-conclusion">
          <div class="drawer-heading"><div><p class="eyebrow">AUTO SUMMARY</p><h3>场景总结</h3></div><span>{{ formatTime(String(selectedScene.summary.generated_at || '')) }}</span></div>
          <p>{{ selectedScene.summary.conclusion }}</p><small>{{ selectedScene.summary.recommendation }}</small>
        </section>
        <section class="drawer-section scene-alert-section">
          <div class="drawer-heading"><div><p class="eyebrow">LINKED ALERTS</p><h3>关联演练告警</h3></div><span>{{ selectedScene.alerts?.length || 0 }} 条</span></div>
          <div class="scene-alert-list">
            <button v-for="alert in selectedScene.alerts || []" :key="alert.id" type="button" @click="openAlert(alert)">
              <span :class="`severity-${alert.severity.toLowerCase()}`"></span>
              <div><strong>{{ alert.title }}</strong><small>{{ alert.code }} · {{ alert.resource_name || alert.metric_name }}</small></div>
              <el-tag :type="alertStatusTagType(alert.status)" size="small" effect="plain">{{ alert.status_label }}</el-tag>
            </button>
          </div>
          <el-button plain @click="openAlertCreate(undefined, selectedScene)">为当前场景配置告警</el-button>
        </section>
        <section class="drawer-section work-order-section">
          <div class="drawer-heading"><div><p class="eyebrow">MANUAL CLOSED LOOP</p><h3>人工工单</h3></div><span>{{ selectedScene.work_orders?.length || 0 }} 单</span></div>
          <div class="work-order-create"><el-input v-model="workOrderForm.title" maxlength="160" placeholder="遗留事项标题" /><el-select v-model="workOrderForm.priority"><el-option label="低" value="LOW" /><el-option label="中" value="MEDIUM" /><el-option label="高" value="HIGH" /><el-option label="紧急" value="CRITICAL" /></el-select><el-input v-model="workOrderForm.assignee" maxlength="128" placeholder="责任人 / 班组" /><el-input v-model="workOrderForm.description" maxlength="1000" placeholder="问题说明（可选）" /><el-button type="primary" plain :loading="workOrderCreating" @click="createSceneWorkOrder">创建工单</el-button></div>
          <div class="work-order-list"><article v-for="order in selectedScene.work_orders || []" :key="order.id"><div><div><strong>{{ order.title }}</strong><el-tag :type="workOrderTagType(order.status)" size="small" effect="plain">{{ order.status_label }}</el-tag></div><p>{{ order.code }} · {{ order.priority_label }} · {{ order.assignee || '待分派' }}</p><small v-if="order.resolution">处理结果：{{ order.resolution }}</small></div><div class="work-order-actions"><el-button v-if="order.status === 'OPEN'" link type="primary" @click="operateSceneWorkOrder(order, 'ACCEPT')">受理</el-button><el-button v-if="order.status === 'PROCESSING'" link type="success" @click="operateSceneWorkOrder(order, 'RESOLVE')">解决</el-button><el-button v-if="order.status === 'RESOLVED'" link type="primary" @click="operateSceneWorkOrder(order, 'CLOSE')">关闭</el-button><el-button v-if="['RESOLVED', 'CLOSED'].includes(order.status)" link @click="operateSceneWorkOrder(order, 'REOPEN')">重开</el-button></div></article></div>
        </section>
        <section class="drawer-section event-section"><div class="drawer-heading"><div><p class="eyebrow">SCENE AUDIT</p><h3>场景事件</h3></div><span>共 {{ selectedScene.events?.length || 0 }} 条</span></div><el-timeline><el-timeline-item v-for="event in selectedScene.events || []" :key="event.id" :timestamp="formatTime(event.create_time)" placement="top"><strong>{{ event.action_label }}{{ event.step_name ? ` · ${event.step_name}` : '' }}</strong><p>{{ event.previous_status_label }} → {{ event.current_status_label }} · {{ event.operator_name }}</p></el-timeline-item></el-timeline></section>
      </div>
    </el-drawer>

    <el-drawer
      v-model="alertTemplateDrawerVisible"
      append-to-body
      class="rehearsal-drawer alert-template-drawer"
      size="min(820px, 94vw)"
      title="新建告警模板"
    >
      <div class="drawer-scroll">
        <section class="alert-command template-command">
          <div><p class="eyebrow">ALERT POLICY · X22</p><h3>配置告警规则版本</h3><p>阈值、指标和网元类型会随模板快照固化到每次演练告警。</p></div>
          <span>{{ alertTemplateForm.rules.length }} 条规则</span>
        </section>
        <section class="drawer-section alert-template-base-grid">
          <label><span>所属场景</span><el-select v-model="alertTemplateForm.scenario_id"><el-option v-for="item in dashboard.scenarios" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
          <label><span>默认等级</span><el-select v-model="alertTemplateForm.default_severity"><el-option label="一般" value="LOW" /><el-option label="关注" value="MEDIUM" /><el-option label="严重" value="HIGH" /><el-option label="紧急" value="CRITICAL" /></el-select></label>
          <label><span>模板编号</span><el-input v-model="alertTemplateForm.code" maxlength="64" placeholder="例如 ACCESS-ALERT" /></label>
          <label><span>模板名称</span><el-input v-model="alertTemplateForm.name" maxlength="128" /></label>
          <label class="wide-field"><span>模板说明</span><el-input v-model="alertTemplateForm.description" type="textarea" :rows="2" maxlength="500" show-word-limit /></label>
        </section>
        <section class="drawer-section">
          <div class="drawer-heading"><div><p class="eyebrow">THRESHOLD RULES</p><h3>阈值规则</h3></div><el-button plain :disabled="alertTemplateForm.rules.length >= 20" @click="addAlertRule">添加规则</el-button></div>
          <div class="alert-rule-list">
            <article v-for="(rule, index) in alertTemplateForm.rules" :key="index" class="alert-rule-card">
              <span>{{ String(index + 1).padStart(2, '0') }}</span>
              <div>
                <div class="alert-rule-grid"><el-input v-model="rule.code" placeholder="规则编号" /><el-input v-model="rule.name" placeholder="规则名称" /><el-input v-model="rule.metric_code" placeholder="指标编号" /><el-input v-model="rule.metric_name" placeholder="指标名称" /><el-select v-model="rule.operator"><el-option label=">" value="GT" /><el-option label=">=" value="GTE" /><el-option label="<" value="LT" /><el-option label="<=" value="LTE" /><el-option label="=" value="EQ" /></el-select><el-input-number v-model="rule.threshold" :controls="false" /><el-input v-model="rule.unit" placeholder="单位" /><el-input v-model="rule.resource_type" placeholder="网元类型" /></div>
              </div>
              <el-button link type="danger" :disabled="alertTemplateForm.rules.length === 1" @click="removeAlertRule(index)">删除</el-button>
            </article>
          </div>
        </section>
      </div>
      <template #footer><div class="drawer-footer"><span>同一编号再次保存会生成新版本。</span><div><el-button @click="alertTemplateDrawerVisible = false">取消</el-button><el-button type="primary" :loading="alertTemplateCreating" @click="createAlertTemplate">保存模板版本</el-button></div></div></template>
    </el-drawer>

    <el-drawer
      v-model="alertCreateDrawerVisible"
      append-to-body
      class="rehearsal-drawer alert-create-drawer"
      size="min(800px, 94vw)"
      title="配置演练告警"
    >
      <div class="drawer-scroll">
        <section class="alert-command">
          <div><p class="eyebrow">ALERT INJECTION · X22</p><h3>把阈值异常注入预演链路</h3><p>先配置为待上报，随后可按演练时间依次上报、确认和恢复。</p></div>
          <span>{{ selectedAlertRule?.metric_name || '选择规则' }}</span>
        </section>
        <section class="drawer-section alert-create-grid">
          <label><span>预演实例</span><el-select v-model="alertCreateForm.instance_id" @change="loadAlertSourceInstance"><el-option v-for="item in availableDataInstances" :key="item.id" :label="`${item.name} · ${item.status_label}`" :value="item.id" /></el-select></label>
          <label><span>告警模板</span><el-select v-model="alertCreateForm.template_id" @change="applyAlertTemplate"><el-option v-for="item in availableAlertTemplates" :key="item.id" :label="`${item.name} · V${item.version}`" :value="item.id" /></el-select></label>
          <label><span>阈值规则</span><el-select v-model="alertCreateForm.rule_code" @change="applyAlertRule"><el-option v-for="item in selectedAlertTemplate?.rules || []" :key="item.code" :label="`${item.name} · ${item.metric_name}`" :value="item.code" /></el-select></label>
          <label><span>告警等级</span><el-select v-model="alertCreateForm.severity"><el-option label="一般" value="LOW" /><el-option label="关注" value="MEDIUM" /><el-option label="严重" value="HIGH" /><el-option label="紧急" value="CRITICAL" /></el-select></label>
          <label><span>关联场景执行</span><el-select v-model="alertCreateForm.scene_run_id" clearable placeholder="可选"><el-option v-for="item in alertSourceInstance?.scene_runs || []" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
          <label><span>关联趋势批次</span><el-select v-model="alertCreateForm.data_batch_id" clearable placeholder="可选"><el-option v-for="item in alertSourceInstance?.data_batches || []" :key="item.id" :label="item.name" :value="item.id" /></el-select></label>
          <label class="wide-field"><span>告警标题</span><el-input v-model="alertCreateForm.title" maxlength="160" placeholder="留空使用规则名称" /></label>
          <label><span>网元编号</span><el-input v-model="alertCreateForm.resource_id" maxlength="128" placeholder="例如 NE-CORE-001" /></label>
          <label><span>网元名称</span><el-input v-model="alertCreateForm.resource_name" maxlength="160" /></label>
          <label><span>当前指标值</span><el-input-number v-model="alertCreateForm.metric_value" :controls="false" /></label>
          <label><span>触发阈值</span><el-input-number v-model="alertCreateForm.threshold" :controls="false" /></label>
          <label><span>发生时间</span><el-date-picker v-model="alertCreateForm.occurred_at" type="datetime" value-format="YYYY-MM-DDTHH:mm:ssZ" /></label>
          <label><span>来源系统</span><el-input v-model="alertCreateForm.source_system" maxlength="64" /></label>
          <label class="wide-field"><span>告警说明</span><el-input v-model="alertCreateForm.description" type="textarea" :rows="2" maxlength="1000" /></label>
        </section>
      </div>
      <template #footer><div class="drawer-footer"><span>配置后不会自动上报，由操作员控制演练节奏。</span><div><el-button @click="alertCreateDrawerVisible = false">取消</el-button><el-button type="danger" :loading="alertCreating" @click="createAlert">配置并进入</el-button></div></div></template>
    </el-drawer>

    <el-drawer
      v-model="alertDrawerVisible"
      append-to-body
      class="rehearsal-drawer alert-detail-drawer"
      size="min(920px, 96vw)"
      :title="selectedAlert?.title || '演练告警处置'"
    >
      <div v-if="selectedAlert" v-loading="alertDetailLoading" class="drawer-scroll">
        <section class="alert-command detail-command" :class="`severity-${selectedAlert.severity.toLowerCase()}`">
          <div><p class="eyebrow">{{ selectedAlert.code }} · {{ selectedAlert.template_name }}</p><h3>{{ selectedAlert.title }}</h3><p>{{ selectedAlert.resource_name || selectedAlert.resource_id || '未指定网元' }} · {{ selectedAlert.metric_name || '通用告警' }}</p></div>
          <div><strong>{{ selectedAlert.metric_value ?? '—' }}</strong><small>阈值 {{ selectedAlert.threshold ?? '—' }}</small><el-tag :type="alertStatusTagType(selectedAlert.status)" effect="dark">{{ selectedAlert.status_label }}</el-tag></div>
        </section>
        <section class="drawer-section alert-control">
          <div class="drawer-heading"><div><p class="eyebrow">ALERT CONTROL</p><h3>告警状态控制</h3></div><span>{{ selectedAlert.severity_label }} · {{ formatAlertDuration(selectedAlert.duration_seconds) }}</span></div>
          <div class="alert-operate-grid"><el-input v-model="alertOperateForm.note" maxlength="500" placeholder="本次操作说明（可选）" /><el-input-number v-model="alertOperateForm.metric_value" :controls="false" placeholder="最新指标值" /></div>
          <div class="control-actions"><el-button v-if="selectedAlert.status === 'PENDING'" type="danger" :loading="alertOperating" @click="operateAlert('REPORT')">上报告警</el-button><el-button v-if="selectedAlert.status === 'ACTIVE'" type="primary" :loading="alertOperating" @click="operateAlert('ACKNOWLEDGE')">确认告警</el-button><el-button v-if="['ACTIVE', 'ACKNOWLEDGED'].includes(selectedAlert.status)" type="success" :loading="alertOperating" @click="operateAlert('RECOVER')">恢复告警</el-button><span v-if="selectedAlert.status === 'RECOVERED'">告警已恢复，完整时序已归档。</span></div>
        </section>
        <section class="drawer-section alert-facts">
          <div><span>发生</span><strong>{{ formatTime(selectedAlert.occurred_at) }}</strong></div><div><span>上报</span><strong>{{ formatTime(selectedAlert.reported_at) }}</strong></div><div><span>确认</span><strong>{{ formatTime(selectedAlert.acknowledged_at) }}</strong></div><div><span>恢复</span><strong>{{ formatTime(selectedAlert.recovered_at) }}</strong></div><div><span>场景</span><strong>{{ selectedAlert.scene_run_name || '未关联' }}</strong></div><div><span>趋势</span><strong>{{ selectedAlert.data_batch_name || '未关联' }}</strong></div>
        </section>
        <section class="drawer-section event-section">
          <div class="drawer-heading"><div><p class="eyebrow">ALERT AUDIT</p><h3>告警事件</h3></div><span>{{ selectedAlert.events?.length || 0 }} 条</span></div>
          <el-timeline><el-timeline-item v-for="event in selectedAlert.events || []" :key="event.id" :timestamp="formatTime(event.occurred_at)" placement="top"><strong>{{ event.action_label }}</strong><p>{{ event.previous_status_label }} → {{ event.current_status_label }} · {{ event.operator_name }}</p><small v-if="event.detail.note">{{ event.detail.note }}</small></el-timeline-item></el-timeline>
        </section>
        <section class="drawer-section unified-timeline">
          <div class="drawer-heading"><div><p class="eyebrow">SYNCHRONIZED TIMELINE</p><h3>统一预演时间轴</h3></div><el-select v-model="timelineKind" clearable placeholder="全部事件" size="small"><el-option label="客户申告" value="COMPLAINT" /><el-option label="指标趋势" value="METRIC" /><el-option label="处置操作" value="PROCESS" /><el-option label="场景执行" value="SCENE" /><el-option label="演练告警" value="ALERT" /></el-select></div>
          <div class="timeline-counts"><span v-for="(count, kind) in alertTimeline?.kind_counts || {}" :key="kind">{{ timelineKindLabel(String(kind)) }} {{ count }}</span></div>
          <div class="unified-timeline-list"><article v-for="item in visibleTimelineItems" :key="`${item.kind}-${item.reference_id}-${item.occurred_at}`" :class="item.kind.toLowerCase()"><time>{{ formatTime(item.occurred_at) }}</time><span></span><div><small>{{ item.kind_label }}</small><strong>{{ item.title }}</strong><p>{{ item.subtitle }}</p></div></article></div>
        </section>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
  type UploadRequestOptions,
} from 'element-plus'

import rehearsalApi, {
  type AlertAction,
  type AlertFilters,
  type AlertPage,
  type AlertRule,
  type AlertSeverity,
  type AlertStatus,
  type AlertTemplate,
  type AuxiliaryReportFormat,
  type AuxiliaryReportLevel,
  type AuxiliarySimulation,
  type AuxiliarySimulationFilters,
  type AuxiliarySimulationPage,
  type CapabilityCall,
  type CapabilityCallFilters,
  type CapabilityCallPage,
  type CapabilityCallStatus,
  type CapabilityMock,
  type CapabilityMockKind,
  type ComplaintBatch,
  type ComplaintFilters,
  type ComplaintPage,
  type ComplaintTemplate,
  type DataDistribution,
  type DataFieldSummary,
  type DataModelBuildStrategy,
  type DataModelFilters,
  type DataModelPage,
  type DataModelQualityStatus,
  type DataSimulationBatch,
  type DataSimulationFilters,
  type DataSimulationKind,
  type DataSimulationPage,
  type DataSimulationRule,
  type DataSimulationTemplate,
  type FaultAlertRule,
  type FaultConfiguration,
  type FaultConfigurationFilters,
  type FaultConfigurationPage,
  type FaultConfigurationStatus,
  type FaultReport,
  type FaultReportAction,
  type FaultReportFilters,
  type FaultReportLevel,
  type FaultReportPage,
  type FaultReportStatus,
  type FaultReportTemplate,
  type InstanceAction,
  type InstanceStatus,
  type ProcessRun,
  type ProcessRunAction,
  type ProcessRunFilters,
  type ProcessRunPage,
  type ProcessRunStatus,
  type ProcessStepStatus,
  type ProcessTemplate,
  type RandomFactorDefinition,
  type RehearsalDashboard,
  type RehearsalAlert,
  type RehearsalDataModel,
  type RehearsalInstance,
  type RehearsalTraceback,
  type RehearsalTimeline,
  type SimulationRecord,
  type SimulationRecordDetail,
  type SimulationRecordFilters,
  type SimulationRecordKind,
  type SimulationRecordPage,
  type SimulationRecordState,
  type TimelineKind,
  type TracebackFilters,
  type TracebackPage,
  type TracebackScope,
  type TracebackStatus,
  type SceneRun,
  type SceneRunAction,
  type SceneRunFilters,
  type SceneRunPage,
  type SceneRunStatus,
  type SceneLibrary,
  type SceneLibraryFilters,
  type SceneLibraryPage,
  type SceneLibraryStatus,
  type SceneReplay,
  type SceneReplayFilters,
  type SceneReplayPage,
  type SceneReplayStatus,
  type SceneScript,
  type SceneScriptStep,
  type SceneStepStatus,
  type WorkOrder,
  type WorkOrderAction,
  type WorkOrderPriority,
  type WorkOrderStatus,
} from '@/api/rehearsal'
import { datetimeFormat } from '@/utils/time'

const emptyDashboard = (): RehearsalDashboard => ({
  summary: {
    scenario_count: 0,
    instance_count: 0,
    running_count: 0,
    ready_count: 0,
    complaint_count: 0,
    invalid_count: 0,
    batch_count: 0,
    process_run_count: 0,
    process_running_count: 0,
    process_blocked_count: 0,
    process_completed_count: 0,
    data_batch_count: 0,
    data_point_count: 0,
    metric_batch_count: 0,
    sentiment_batch_count: 0,
    data_model_count: 0,
    data_model_version_count: 0,
    data_model_warn_count: 0,
    traceback_count: 0,
    traceback_ready_count: 0,
    simulation_record_count: 0,
    capability_mock_count: 0,
    capability_call_count: 0,
    capability_call_succeeded_count: 0,
    capability_call_failed_count: 0,
    fault_configuration_count: 0,
    fault_configuration_ready_count: 0,
    fault_configuration_draft_count: 0,
    fault_configuration_bound_count: 0,
    scene_replay_count: 0,
    scene_replay_ready_count: 0,
    scene_replay_frame_count: 0,
    fault_report_template_count: 0,
    fault_report_count: 0,
    fault_report_active_count: 0,
    fault_report_overdue_count: 0,
    auxiliary_simulation_count: 0,
    auxiliary_simulation_attention_count: 0,
    scene_library_count: 0,
    scene_library_ready_count: 0,
    scene_run_count: 0,
    scene_running_count: 0,
    scene_completed_count: 0,
    work_order_count: 0,
    work_order_open_count: 0,
    alert_count: 0,
    alert_pending_count: 0,
    alert_active_count: 0,
    alert_recovered_count: 0,
  },
  customer_counts: { PUBLIC: 0, ENTERPRISE: 0 },
  severity_counts: { LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 },
  scenarios: [],
  templates: [],
  process_templates: [],
  process_runs: [],
  data_templates: [],
  data_batches: [],
  data_tag_counts: [],
  data_models: [],
  tracebacks: [],
  scene_scripts: [],
  scene_libraries: [],
  scene_runs: [],
  work_orders: [],
  alert_templates: [],
  alerts: [],
  capability_mocks: [],
  capability_calls: [],
  fault_configurations: [],
  scene_replays: [],
  fault_report_templates: [],
  fault_reports: [],
  random_factor_catalog: [],
  auxiliary_simulations: [],
  instances: [],
  latest_complaints: [],
})

const emptyComplaintPage = (): ComplaintPage => ({ total: 0, page: 1, page_size: 20, items: [] })
const emptyProcessPage = (): ProcessRunPage => ({ total: 0, page: 1, page_size: 10, items: [] })
const emptyDataPage = (): DataSimulationPage => ({ total: 0, page: 1, page_size: 10, items: [] })
const emptyDataModelPage = (): DataModelPage => ({ total: 0, page: 1, page_size: 10, items: [] })
const emptyTracebackPage = (): TracebackPage => ({ total: 0, page: 1, page_size: 10, items: [] })
const emptySimulationRecordPage = (): SimulationRecordPage => ({
  total: 0,
  page: 1,
  page_size: 10,
  summary: {
    total: 0,
    pending: 0,
    running: 0,
    succeeded: 0,
    attention: 0,
    failed: 0,
    average_duration_seconds: 0,
    kind_counts: {},
  },
  items: [],
})
const emptyCapabilityCallPage = (): CapabilityCallPage => ({
  total: 0,
  page: 1,
  page_size: 10,
  summary: { total: 0, succeeded: 0, failed: 0, timeout: 0, average_latency_ms: 0 },
  warrooms: [],
  items: [],
})
const emptyFaultConfigurationPage = (): FaultConfigurationPage => ({
  total: 0,
  page: 1,
  page_size: 10,
  summary: { total: 0, ready: 0, draft: 0, archived: 0, bound_instances: 0 },
  items: [],
})
const emptySceneReplayPage = (): SceneReplayPage => ({
  total: 0,
  page: 1,
  page_size: 10,
  summary: { total: 0, ready: 0, empty: 0, traffic_frames: 0, changed_nodes: 0, average_latency_ms: 0 },
  items: [],
})
const emptyFaultReportPage = (): FaultReportPage => ({
  total: 0,
  page: 1,
  page_size: 10,
  summary: { total: 0, draft: 0, active: 0, recovered: 0, closed: 0, overdue: 0, attachments: 0 },
  items: [],
})
const emptyAuxiliarySimulationPage = (): AuxiliarySimulationPage => ({
  total: 0,
  page: 1,
  page_size: 10,
  summary: { total: 0, attention: 0, factor_count: 0, triggered_factor_count: 0, anomaly_count: 0 },
  items: [],
})
const emptySceneLibraryPage = (): SceneLibraryPage => ({ total: 0, page: 1, page_size: 10, items: [] })
const emptyScenePage = (): SceneRunPage => ({ total: 0, page: 1, page_size: 10, items: [] })
const emptyAlertPage = (): AlertPage => ({ total: 0, page: 1, page_size: 10, items: [] })

const loading = ref(false)
const complaintLoading = ref(false)
const exporting = ref(false)
const detailLoading = ref(false)
const submitting = ref(false)
const generating = ref(false)
const importing = ref(false)
const operating = ref(false)
const processLoading = ref(false)
const processCreating = ref(false)
const processDetailLoading = ref(false)
const processOperating = ref(false)
const processExporting = ref(false)
const dataLoading = ref(false)
const dataGenerating = ref(false)
const dataDetailLoading = ref(false)
const dataExporting = ref(false)
const dataModelLoading = ref(false)
const dataModelCreating = ref(false)
const dataModelDetailLoading = ref(false)
const dataModelLoadingVersion = ref(false)
const tracebackLoading = ref(false)
const tracebackCreating = ref(false)
const tracebackDetailLoading = ref(false)
const tracebackExporting = ref(false)
const simulationRecordLoading = ref(false)
const simulationRecordDetailLoading = ref(false)
const simulationRecordExporting = ref(false)
const capabilityCallLoading = ref(false)
const capabilityInvoking = ref(false)
const capabilityCallDetailLoading = ref(false)
const capabilityReplaying = ref(false)
const capabilityMockCreating = ref(false)
const faultConfigurationLoading = ref(false)
const faultConfigurationCreating = ref(false)
const faultConfigurationDetailLoading = ref(false)
const faultConfigurationOperating = ref(false)
const sceneReplayLoading = ref(false)
const sceneReplayCreating = ref(false)
const sceneReplayDetailLoading = ref(false)
const faultReportLoading = ref(false)
const faultReportCreating = ref(false)
const faultReportDetailLoading = ref(false)
const faultReportOperating = ref(false)
const auxiliarySimulationLoading = ref(false)
const auxiliarySimulationCreating = ref(false)
const auxiliarySimulationDetailLoading = ref(false)
const auxiliarySimulationExporting = ref(false)
const sceneLibraryLoading = ref(false)
const sceneLibraryCreating = ref(false)
const sceneLibraryDetailLoading = ref(false)
const sceneLibraryOperating = ref(false)
const sceneLibraryRunning = ref(false)
const sceneLoading = ref(false)
const sceneCreating = ref(false)
const sceneDetailLoading = ref(false)
const sceneOperating = ref(false)
const sceneScriptCreating = ref(false)
const workOrderCreating = ref(false)
const alertLoading = ref(false)
const alertTemplateCreating = ref(false)
const alertCreating = ref(false)
const alertDetailLoading = ref(false)
const alertOperating = ref(false)
type RehearsalWorkspace = 'overview' | 'data' | 'fault' | 'scene'
type RehearsalModule =
  | 'process'
  | 'data-simulation'
  | 'data-model'
  | 'traceback'
  | 'record'
  | 'capability'
  | 'fault-configuration'
  | 'scene-replay'
  | 'fault-report'
  | 'auxiliary'
  | 'scene-library'
  | 'scene-run'
  | 'alert'
  | 'complaint'

const workspaceViews: ReadonlyArray<{
  value: RehearsalWorkspace
  index: string
  title: string
  description: string
  scope: string
}> = [
  { value: 'overview', index: '01', title: '总览与实例', description: '模板、控制链和实例入口', scope: '3 个模块' },
  { value: 'data', index: '02', title: '数据与处置', description: '趋势、模型、进度与回溯', scope: '5 个模块' },
  { value: 'fault', index: '03', title: '故障与回放', description: '配置、沙盒、上报与报告', scope: '5 个模块' },
  { value: 'scene', index: '04', title: '场景与闭环', description: '场景库、告警和申告数据', scope: '4 个模块' },
]
const activeWorkspace = ref<RehearsalWorkspace>('overview')
const rehearsalPage = ref<HTMLElement | null>(null)
const moduleViews: ReadonlyArray<{
  workspace: Exclude<RehearsalWorkspace, 'overview'>
  value: RehearsalModule
  title: string
  description: string
}> = [
  { workspace: 'data', value: 'process', title: '处置进度', description: '流程推进与步骤事实' },
  { workspace: 'data', value: 'data-simulation', title: '趋势数据', description: '指标和舆情时序数据' },
  { workspace: 'data', value: 'data-model', title: '数据模型', description: '版本、质量与血缘' },
  { workspace: 'data', value: 'traceback', title: '动态回溯', description: '链路快照和事件回放' },
  { workspace: 'data', value: 'record', title: '预演记录', description: '跨类型统一查询' },
  { workspace: 'fault', value: 'capability', title: '能力沙盒', description: '隔离调用与重放' },
  { workspace: 'fault', value: 'fault-configuration', title: '故障配置', description: '拓扑、门禁与预案' },
  { workspace: 'fault', value: 'scene-replay', title: '场景回放', description: '流量帧和镜像差异' },
  { workspace: 'fault', value: 'fault-report', title: '故障上报', description: '阶段 SLA 与证据链' },
  { workspace: 'fault', value: 'auxiliary', title: '辅助演练', description: '随机因子与结果报告' },
  { workspace: 'scene', value: 'scene-library', title: '场景库', description: '版本化场景资产' },
  { workspace: 'scene', value: 'scene-run', title: '场景执行', description: '剧本推进与人工闭环' },
  { workspace: 'scene', value: 'alert', title: '告警演练', description: '告警状态与时序同步' },
  { workspace: 'scene', value: 'complaint', title: '申告数据', description: '客户申告明细' },
]
const activeModule = ref<RehearsalModule>('process')
const activeModuleViews = computed(() => moduleViews.filter((item) => item.workspace === activeWorkspace.value))
const dashboard = ref<RehearsalDashboard>(emptyDashboard())
const complaintPage = ref<ComplaintPage>(emptyComplaintPage())
const processPage = ref<ProcessRunPage>(emptyProcessPage())
const dataPage = ref<DataSimulationPage>(emptyDataPage())
const dataModelPage = ref<DataModelPage>(emptyDataModelPage())
const tracebackPage = ref<TracebackPage>(emptyTracebackPage())
const simulationRecordPage = ref<SimulationRecordPage>(emptySimulationRecordPage())
const capabilityCallPage = ref<CapabilityCallPage>(emptyCapabilityCallPage())
const faultConfigurationPage = ref<FaultConfigurationPage>(emptyFaultConfigurationPage())
const sceneReplayPage = ref<SceneReplayPage>(emptySceneReplayPage())
const faultReportPage = ref<FaultReportPage>(emptyFaultReportPage())
const auxiliarySimulationPage = ref<AuxiliarySimulationPage>(emptyAuxiliarySimulationPage())
const sceneLibraryPage = ref<SceneLibraryPage>(emptySceneLibraryPage())
const scenePage = ref<SceneRunPage>(emptyScenePage())
const alertPage = ref<AlertPage>(emptyAlertPage())

function switchWorkspace(workspace: RehearsalWorkspace) {
  if (activeWorkspace.value === workspace) return
  preserveScrollPosition(() => {
    activeWorkspace.value = workspace
    if (workspace !== 'overview') {
      activeModule.value = moduleViews.find((item) => item.workspace === workspace)?.value || 'process'
    }
  })
}

function switchModule(module: RehearsalModule) {
  if (activeModule.value === module) return
  preserveScrollPosition(() => {
    activeModule.value = module
  })
}

function preserveScrollPosition(updateView: () => void) {
  const container = rehearsalPage.value
  const scrollTop = container?.scrollTop || 0
  updateView()
  nextTick(() => {
    if (!container || scrollTop <= 0) return
    const maximumScrollTop = Math.max(0, container.scrollHeight - container.clientHeight)
    container.scrollTop = Math.min(scrollTop, maximumScrollTop)
  })
}

const createDialogVisible = ref(false)
const instanceDrawerVisible = ref(false)
const processDrawerVisible = ref(false)
const dataCreateDrawerVisible = ref(false)
const dataDetailDrawerVisible = ref(false)
const dataModelCreateDrawerVisible = ref(false)
const dataModelDrawerVisible = ref(false)
const tracebackCreateDrawerVisible = ref(false)
const tracebackDrawerVisible = ref(false)
const simulationRecordDrawerVisible = ref(false)
const capabilityMockDrawerVisible = ref(false)
const capabilityCallDrawerVisible = ref(false)
const faultConfigurationFormDrawerVisible = ref(false)
const faultConfigurationDrawerVisible = ref(false)
const sceneReplayCreateDrawerVisible = ref(false)
const sceneReplayDrawerVisible = ref(false)
const faultReportCreateDrawerVisible = ref(false)
const faultReportDrawerVisible = ref(false)
const auxiliarySimulationCreateDrawerVisible = ref(false)
const auxiliarySimulationDrawerVisible = ref(false)
const sceneLibraryDrawerVisible = ref(false)
const sceneLibraryFormDrawerVisible = ref(false)
const sceneLibraryRunDrawerVisible = ref(false)
const sceneScriptDrawerVisible = ref(false)
const sceneCreateDrawerVisible = ref(false)
const sceneDrawerVisible = ref(false)
const alertTemplateDrawerVisible = ref(false)
const alertCreateDrawerVisible = ref(false)
const alertDrawerVisible = ref(false)
const selectedInstance = ref<RehearsalInstance>()
const selectedProcess = ref<ProcessRun>()
const selectedDataSimulation = ref<DataSimulationBatch>()
const selectedDataModel = ref<RehearsalDataModel>()
const selectedTraceback = ref<RehearsalTraceback>()
const selectedSimulationRecord = ref<SimulationRecordDetail>()
const selectedCapabilityCall = ref<CapabilityCall>()
const selectedFaultConfiguration = ref<FaultConfiguration>()
const selectedSceneReplay = ref<SceneReplay>()
const selectedFaultReport = ref<FaultReport>()
const selectedAuxiliarySimulation = ref<AuxiliarySimulation>()
const clockNow = ref(Date.now())
const sceneReplayCursor = ref(0)
const sceneReplayPlaying = ref(false)
const activeReplayNodeId = ref('')
let sceneReplayTimer: ReturnType<typeof setInterval> | null = null
let faultReportClockTimer: ReturnType<typeof setInterval> | null = null
const faultConfigurationPreviewId = ref('')
const selectedSceneLibrary = ref<SceneLibrary>()
const selectedScene = ref<SceneRun>()
const selectedAlert = ref<RehearsalAlert>()
const alertTimeline = ref<RehearsalTimeline>()
const sceneSourceInstance = ref<RehearsalInstance>()
const alertSourceInstance = ref<RehearsalInstance>()
const timelineKind = ref<'' | TimelineKind>('')
const activeDataFieldCode = ref('')
const createFormRef = ref<FormInstance>()

const filters = reactive<ComplaintFilters>({
  page: 1,
  page_size: 20,
  instance_id: '',
  customer_type: '',
  severity: '',
  validation_status: '',
  source: '',
  keyword: '',
})

const processFilters = reactive<ProcessRunFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  template_id: '',
  status: '',
  auto_advance: '',
  keyword: '',
})

const dataFilters = reactive<DataSimulationFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  template_id: '',
  kind: '',
  status: '',
  tag: '',
  keyword: '',
})

const dataModelFilters = reactive<DataModelFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  scene_run_id: '',
  build_strategy: '',
  quality_status: '',
  keyword: '',
})

const tracebackFilters = reactive<TracebackFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  scope: '',
  status: '',
  kind: '',
  keyword: '',
})

const simulationRecordFilters = reactive<SimulationRecordFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  kind: '',
  state: '',
  keyword: '',
  date_from: '',
  date_to: '',
})

const capabilityCallFilters = reactive<CapabilityCallFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  capability_id: '',
  kind: '',
  status: '',
  warroom_group: '',
  keyword: '',
  date_from: '',
  date_to: '',
})

const faultConfigurationFilters = reactive<FaultConfigurationFilters>({
  page: 1,
  page_size: 10,
  scenario_id: '',
  status: '',
  bound: '',
  keyword: '',
})

const sceneReplayFilters = reactive<SceneReplayFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  scene_run_id: '',
  status: '',
  node_id: '',
  keyword: '',
})

const faultReportFilters = reactive<FaultReportFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  template_id: '',
  status: '',
  level: '',
  overdue: '',
  keyword: '',
})

const auxiliarySimulationFilters = reactive<AuxiliarySimulationFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  status: '',
  seed: '',
  keyword: '',
})

const sceneLibraryFilters = reactive<SceneLibraryFilters>({
  page: 1,
  page_size: 10,
  scenario_id: '',
  script_id: '',
  status: '',
  visibility: '',
  keyword: '',
})

const sceneFilters = reactive<SceneRunFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  script_id: '',
  status: '',
  keyword: '',
})

const alertFilters = reactive<AlertFilters>({
  page: 1,
  page_size: 10,
  instance_id: '',
  template_id: '',
  status: '',
  severity: '',
  keyword: '',
})

const createForm = reactive({
  scenario_id: '',
  name: '',
  code: '',
  planned_start_at: null as string | null,
})

const generateForm = reactive({
  template_id: '',
  count: 20,
  start_at: new Date().toISOString(),
  interval_minutes: 5,
})

const processForm = reactive({
  template_id: '',
  name: '',
  auto_advance: false,
})

const processOperateForm = reactive({ note: '', reason: '' })

const dataForm = reactive({
  instance_id: '',
  template_id: '',
  name: '',
  count: 24,
  start_at: new Date().toISOString(),
  interval_minutes: 5,
  tags: [] as string[],
  rules: [] as DataSimulationRule[],
})

const dataModelForm = reactive({
  instance_id: '',
  scene_run_id: '' as string | null,
  name: '',
  description: '',
  build_strategy: 'FULL_INSTANCE' as DataModelBuildStrategy,
  transformer_code: 'CANONICAL_V1',
})

const tracebackForm = reactive({
  instance_id: '',
  scene_run_id: '' as string | null,
  data_model_id: '' as string | null,
  name: '',
  description: '',
  scope: 'FULL_INSTANCE' as TracebackScope,
  kind_scope: [
    'COMPLAINT',
    'METRIC',
    'SENTIMENT',
    'PROCESS',
    'SCENE',
    'ALERT',
    'WORK_ORDER',
  ] as TimelineKind[],
  window_start: null as string | null,
  window_end: null as string | null,
})

const capabilityInvokeForm = reactive({
  instance_id: '',
  capability_id: '',
  expected_status: 'SUCCEEDED' as CapabilityCallStatus,
  latency_ms: 120,
  warroom_group: '网络质量战情室',
  request_payload_text: '{\n  "resource_id": "NE-X27-001",\n  "include_metrics": true\n}',
})

const capabilityMockForm = reactive({
  scenario_id: '',
  code: '',
  name: '',
  description: '',
  kind: 'API' as CapabilityMockKind,
  method: 'POST',
  endpoint: '/sandbox/',
  default_latency_ms: 120,
  request_schema_text: '{\n  "required": [],\n  "properties": {}\n}',
  response_template_text: '{\n  "success": true,\n  "message": "调用完成"\n}',
  failure_template_text: '{\n  "code": "SIMULATION_FAILED",\n  "message": "调用失败"\n}',
})

const faultConfigurationForm = reactive({
  scenario_id: '',
  code: 'NETWORK-FAULT-CONFIG',
  name: '',
  description: '',
  alert_rules_text:
    '[\n  {\n    "code": "LATENCY_CRITICAL",\n    "name": "链路时延严重异常",\n    "severity": "CRITICAL",\n    "metric_code": "LATENCY_MS",\n    "operator": "GTE",\n    "threshold": 120,\n    "unit": "ms"\n  }\n]',
  timeout_policy_text:
    '{\n  "overall_seconds": 900,\n  "step_seconds": 300,\n  "on_timeout": "ESCALATE_AND_SWITCH",\n  "retry_limit": 1\n}',
  active_window_text:
    '{\n  "timezone": "Asia/Shanghai",\n  "weekdays": [1, 2, 3, 4, 5, 6, 7],\n  "start": "00:00",\n  "end": "23:59"\n}',
  topology_snapshot_text:
    '{\n  "version": "TOPOLOGY-V1",\n  "nodes": [\n    {"id": "CORE-A", "name": "核心节点 A", "type": "CORE", "state": "FAULT"},\n    {"id": "CORE-B", "name": "核心节点 B", "type": "CORE", "state": "STANDBY"}\n  ],\n  "links": [\n    {"source": "CORE-A", "target": "CORE-B", "state": "AVAILABLE"}\n  ]\n}',
  emergency_plan_text:
    '{\n  "code": "PLAN-FAULT-SWITCH",\n  "name": "故障隔离与旁路切换预案",\n  "owner": "网络运维战情室",\n  "steps": [\n    {"code": "CONFIRM", "name": "确认故障节点", "owner_role": "监控席", "target_minutes": 3},\n    {"code": "SWITCH", "name": "切换备用链路", "owner_role": "调度席", "target_minutes": 5}\n  ]\n}',
})

const faultConfigurationApplyForm = reactive({
  instance_id: '',
  note: '绑定 X28 故障配置快照',
})

const sceneReplayForm = reactive({
  instance_id: '',
  scene_run_id: '' as string | null,
  name: '',
  description: '',
  window_start: null as string | null,
  window_end: null as string | null,
})

const faultReportForm = reactive({
  instance_id: '',
  template_id: '',
  scene_run_id: '' as string | null,
  title: '',
  description: '',
  impact_scope: '',
  level: 'LEVEL_2' as FaultReportLevel,
  attachment_reference_id: '',
  attachment_file_name: '',
})

const faultReportActionForm = reactive({
  action: '' as '' | FaultReportAction,
  note: '',
  level: 'LEVEL_1' as FaultReportLevel,
  attachment_reference_id: '',
  attachment_file_name: '',
})

type AuxiliaryFactorForm = RandomFactorDefinition & { enabled: boolean }
const auxiliarySimulationForm = reactive({
  instance_id: '',
  name: '',
  seed: 20260917,
  duration_minutes: 60,
  factors: [] as AuxiliaryFactorForm[],
})
const auxiliaryExportForm = reactive({
  export_format: 'pdf' as AuxiliaryReportFormat,
  report_level: 'summary' as AuxiliaryReportLevel,
})

const sceneScriptForm = reactive({
  scenario_id: '',
  code: '',
  name: '',
  description: '',
  steps: [] as SceneScriptStep[],
})

const sceneLibraryForm = reactive({
  mode: 'create' as 'create' | 'clone',
  source_id: '',
  scenario_id: '',
  script_id: '',
  code: '',
  name: '',
  description: '',
  default_instance_id: '' as string | null,
  process_template_id: '' as string | null,
  data_model_id: '' as string | null,
  visibility: 'WORKSPACE' as 'WORKSPACE' | 'PRIVATE',
  permission_roles: 'WORKSPACE_MANAGE',
  note: '',
})

const sceneLibraryRunForm = reactive({
  library_id: '',
  instance_id: '' as string | null,
  name: '',
  include_latest_complaint_batch: true,
  include_latest_data_batch: true,
  include_latest_process_run: true,
})

const sceneCreateForm = reactive({
  instance_id: '',
  script_id: '',
  name: '',
  complaint_batch_ids: [] as string[],
  data_batch_ids: [] as string[],
  process_run_ids: [] as string[],
})

const sceneOperateForm = reactive({ note: '', reason: '' })
const workOrderForm = reactive({
  title: '',
  description: '',
  priority: 'MEDIUM' as WorkOrderPriority,
  assignee: '',
})

const alertTemplateForm = reactive({
  scenario_id: '',
  code: '',
  name: '',
  description: '',
  default_severity: 'HIGH' as AlertSeverity,
  rules: [] as AlertRule[],
})

const alertCreateForm = reactive({
  instance_id: '',
  template_id: '',
  rule_code: '',
  scene_run_id: '' as string | null,
  data_batch_id: '' as string | null,
  title: '',
  description: '',
  severity: 'HIGH' as AlertSeverity,
  source_system: '预演平台',
  resource_id: '',
  resource_name: '',
  metric_value: 120 as number | null,
  threshold: 100 as number | null,
  occurred_at: new Date().toISOString(),
})

const alertOperateForm = reactive({ note: '', metric_value: null as number | null })

const createRules: FormRules = {
  scenario_id: [{ required: true, message: '请选择预演场景', trigger: 'change' }],
  name: [{ required: true, message: '请输入实例名称', trigger: 'blur' }],
}

const workflowSteps = [
  { title: '选择模板', desc: '公众 / 政企数据蓝图' },
  { title: '生成或导入', desc: '按间隔构造时序申告' },
  { title: '构造趋势', desc: '自定义指标与舆情分布' },
  { title: '生成流程', desc: '固化动态处置步骤快照' },
  { title: '注入场景', desc: '装配剧本与预演数据快照' },
  { title: '告警演练', desc: '上报、确认、恢复与时序同步' },
  { title: '沉淀模型', desc: '策略、转换器、版本和血缘' },
  { title: '动态回溯', desc: '窗口、节点、转移与固化回放' },
  { title: '统一归档', desc: '进度、次数、结果与详情查询' },
  { title: '能力沙盒', desc: 'API 接口、原子能力与重放留痕' },
  { title: '故障矩阵', desc: '告警、超时、时段、拓扑与预案' },
  { title: '场景回放', desc: '流量帧、节点追踪与前后镜像' },
  { title: '故障上报', desc: '等级、阶段、时限与证据事实链' },
  { title: '辅助演练', desc: '随机因子、异常分析与多格式报告' },
]

const tracebackKindOptions: Array<{ label: string; value: TimelineKind }> = [
  { label: '客户申告', value: 'COMPLAINT' },
  { label: '指标趋势', value: 'METRIC' },
  { label: '舆情趋势', value: 'SENTIMENT' },
  { label: '处置操作', value: 'PROCESS' },
  { label: '场景执行', value: 'SCENE' },
  { label: '演练告警', value: 'ALERT' },
  { label: '人工工单', value: 'WORK_ORDER' },
]

const simulationRecordKindOptions: Array<{ label: string; value: SimulationRecordKind }> = [
  { label: '预演实例', value: 'INSTANCE' },
  { label: '申告批次', value: 'COMPLAINT_BATCH' },
  { label: '趋势数据', value: 'DATA_BATCH' },
  { label: '处置流程', value: 'PROCESS_RUN' },
  { label: '场景执行', value: 'SCENE_RUN' },
  { label: '演练告警', value: 'ALERT' },
  { label: '动态回溯', value: 'TRACEBACK' },
  { label: '能力调用', value: 'CAPABILITY_CALL' },
  { label: '故障上报', value: 'FAULT_REPORT' },
  { label: '辅助演练', value: 'AUXILIARY_SIMULATION' },
]

const metrics = computed(() => [
  {
    label: '预演实例',
    value: dashboard.value.summary.instance_count,
    hint: `${dashboard.value.summary.running_count} 个正在预演`,
  },
  {
    label: '有效申告',
    value: dashboard.value.summary.complaint_count,
    hint: `公众 ${dashboard.value.customer_counts.PUBLIC} · 政企 ${dashboard.value.customer_counts.ENTERPRISE}`,
  },
  {
    label: '处置流程',
    value: dashboard.value.summary.process_run_count,
    hint: `${dashboard.value.summary.process_running_count} 执行中 · ${dashboard.value.summary.process_blocked_count} 阻塞`,
  },
  {
    label: '预演时序',
    value: dashboard.value.summary.data_point_count,
    hint: `${dashboard.value.summary.data_batch_count} 个趋势批次`,
  },
  {
    label: '数据模型',
    value: dashboard.value.summary.data_model_count,
    hint: `${dashboard.value.summary.data_model_version_count} 个版本 · ${dashboard.value.summary.data_model_warn_count} 个提醒`,
  },
  {
    label: '动态回溯',
    value: dashboard.value.summary.traceback_count,
    hint: `${dashboard.value.summary.traceback_ready_count} 个快照可回放`,
  },
  {
    label: '预演记录',
    value: dashboard.value.summary.simulation_record_count,
    hint: '跨类型统一归档与查询',
  },
  {
    label: '能力调用',
    value: dashboard.value.summary.capability_call_count,
    hint: `${dashboard.value.summary.capability_call_succeeded_count} 成功 · ${dashboard.value.summary.capability_call_failed_count} 需关注`,
  },
  {
    label: '故障配置',
    value: dashboard.value.summary.fault_configuration_count,
    hint: `${dashboard.value.summary.fault_configuration_ready_count} 可应用 · ${dashboard.value.summary.fault_configuration_bound_count} 已绑定`,
  },
  {
    label: '场景回放',
    value: dashboard.value.summary.scene_replay_count,
    hint: `${dashboard.value.summary.scene_replay_frame_count} 个流量与控制帧`,
  },
  {
    label: '故障上报',
    value: dashboard.value.summary.fault_report_count,
    hint: `${dashboard.value.summary.fault_report_active_count} 起处理中 · ${dashboard.value.summary.fault_report_overdue_count} 起超时`,
  },
  {
    label: '辅助演练',
    value: dashboard.value.summary.auxiliary_simulation_count,
    hint: `${dashboard.value.summary.auxiliary_simulation_attention_count} 个批次存在异常点`,
  },
  {
    label: '场景库',
    value: dashboard.value.summary.scene_library_count,
    hint: `${dashboard.value.summary.scene_library_ready_count} 个可复用版本`,
  },
  {
    label: '场景执行',
    value: dashboard.value.summary.scene_run_count,
    hint: `${dashboard.value.summary.scene_running_count} 执行中 · ${dashboard.value.summary.work_order_open_count} 工单待闭环`,
  },
  {
    label: '演练告警',
    value: dashboard.value.summary.alert_count,
    hint: `${dashboard.value.summary.alert_active_count} 活跃 · ${dashboard.value.summary.alert_recovered_count} 已恢复`,
  },
  {
    label: '校验异常',
    value: dashboard.value.summary.invalid_count,
    hint: '异常数据保留、不会进入执行链',
  },
])

const availableDataInstances = computed(() =>
  dashboard.value.instances.filter((item) => ['DRAFT', 'READY', 'RUNNING'].includes(item.status)),
)

const availableSceneScripts = computed(() => {
  const instance = sceneSourceInstance.value
  return dashboard.value.scene_scripts.filter(
    (item) => !instance || item.scenario_id === instance.scenario_id,
  )
})

const sceneLibraryScripts = computed(() =>
  dashboard.value.scene_scripts.filter(
    (item) => !sceneLibraryForm.scenario_id || item.scenario_id === sceneLibraryForm.scenario_id,
  ),
)

const sceneLibraryInstances = computed(() =>
  dashboard.value.instances.filter(
    (item) => !sceneLibraryForm.scenario_id || item.scenario_id === sceneLibraryForm.scenario_id,
  ),
)

const sceneLibraryDataModels = computed(() =>
  dashboard.value.data_models.filter(
    (item) => !sceneLibraryForm.scenario_id || item.scenario_id === sceneLibraryForm.scenario_id,
  ),
)

const availableAlertTemplates = computed(() => {
  const instance = alertSourceInstance.value
  return dashboard.value.alert_templates.filter(
    (item) => !instance || item.scenario_id === instance.scenario_id,
  )
})

const selectedAlertTemplate = computed(() =>
  dashboard.value.alert_templates.find((item) => item.id === alertCreateForm.template_id),
)

const selectedAlertRule = computed(() =>
  selectedAlertTemplate.value?.rules.find((item) => item.code === alertCreateForm.rule_code),
)

const visibleTimelineItems = computed(() => {
  const items = alertTimeline.value?.items || []
  const filtered = timelineKind.value ? items.filter((item) => item.kind === timelineKind.value) : items
  return filtered.slice(-100).reverse()
})

const sceneInjectionCount = computed(
  () =>
    sceneCreateForm.complaint_batch_ids.length +
    sceneCreateForm.data_batch_ids.length +
    sceneCreateForm.process_run_ids.length,
)

const knownDataTags = computed(() => {
  const tags = new Set(dashboard.value.data_tag_counts.map((item) => item.name))
  dashboard.value.data_templates.forEach((item) => item.default_tags.forEach((tag) => tags.add(tag)))
  return [...tags]
})

const availableDataModelSceneRuns = computed(() =>
  dashboard.value.scene_runs.filter((item) => item.instance_id === dataModelForm.instance_id),
)

const availableTracebackSceneRuns = computed(() =>
  dashboard.value.scene_runs.filter((item) => item.instance_id === tracebackForm.instance_id),
)

const availableTracebackDataModels = computed(() =>
  dashboard.value.data_models.filter((item) => item.instance_id === tracebackForm.instance_id),
)

const selectedCapabilityMock = computed(() =>
  dashboard.value.capability_mocks.find((item) => item.id === capabilityInvokeForm.capability_id),
)

const faultConfigurationPreview = computed(
  () =>
    faultConfigurationPage.value.items.find(
      (item) => item.id === faultConfigurationPreviewId.value,
    ) || faultConfigurationPage.value.items[0],
)

const faultConfigurationInstances = computed(() =>
  dashboard.value.instances.filter(
    (item) =>
      !faultConfigurationPreview.value ||
      (item.scenario_id === faultConfigurationPreview.value.scenario_id &&
        !['COMPLETED', 'CANCELLED', 'FAILED'].includes(item.status)),
  ),
)

const sceneReplayInstances = computed(() =>
  dashboard.value.instances.filter((item) => Boolean(item.fault_configuration_id)),
)

const availableSceneReplayRuns = computed(() =>
  dashboard.value.scene_runs.filter((item) => item.instance_id === sceneReplayForm.instance_id),
)

const currentSceneReplayFrame = computed(
  () => selectedSceneReplay.value?.traffic_frames?.[sceneReplayCursor.value],
)

const activeSceneReplayNode = computed(() => {
  const nodeId = activeReplayNodeId.value || currentSceneReplayFrame.value?.target_node || ''
  return selectedSceneReplay.value?.node_traces?.find((item) => item.node_id === nodeId)
})

const faultReportInstances = computed(() =>
  dashboard.value.instances.filter(
    (item) => Boolean(item.fault_configuration_id) && !['COMPLETED', 'CANCELLED', 'FAILED'].includes(item.status),
  ),
)

const availableFaultReportTemplates = computed(() => {
  const instance = dashboard.value.instances.find((item) => item.id === faultReportForm.instance_id)
  return dashboard.value.fault_report_templates.filter(
    (item) => item.status === 'READY' && (!item.scenario_id || item.scenario_id === instance?.scenario_id),
  )
})

const selectedFaultReportTemplate = computed<FaultReportTemplate | undefined>(() =>
  dashboard.value.fault_report_templates.find((item) => item.id === faultReportForm.template_id),
)

const availableFaultReportSceneRuns = computed(() =>
  dashboard.value.scene_runs.filter((item) => item.instance_id === faultReportForm.instance_id),
)

const faultReportCountdown = computed(() =>
  selectedFaultReport.value ? reportCountdown(selectedFaultReport.value) : { text: '—', overdue: false },
)
const auxiliaryChartPolyline = computed(() => {
  const points = selectedAuxiliarySimulation.value?.points || []
  if (!points.length) return ''
  const maximum = Math.max(...points.map((item) => item.timeout_rate_pct), 1)
  return points
    .map((item, index) => {
      const x = (index / Math.max(points.length - 1, 1)) * 620
      const y = 142 - (item.timeout_rate_pct / maximum) * 132
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
})
const auxiliaryChartArea = computed(() => {
  const line = auxiliaryChartPolyline.value
  return line ? `M 0 150 L ${line.split(' ').join(' L ')} L 620 150 Z` : ''
})

const simulationRecordSourceFacts = computed(() => {
  const detail = selectedSimulationRecord.value?.detail || {}
  const labels: Record<string, string> = {
    source_label: '数据来源',
    status_label: '业务状态',
    version: '版本',
    point_count: '时序点数',
    total_count: '数据总量',
    valid_count: '有效数量',
    invalid_count: '异常数量',
    total_steps: '总步骤',
    completed_steps: '完成步骤',
    current_step_name: '当前步骤',
    work_order_count: '工单数量',
    alert_count: '告警数量',
    total_events: '回溯事实',
    severity_label: '告警等级',
    resource_name: '影响资源',
    scope_label: '回溯范围',
    checksum: '快照校验和',
  }
  const facts = Object.entries(labels).flatMap(([key, label]) => {
    const value = detail[key]
    if (value === undefined || value === null || value === '') return []
    return [{ label, value: String(value) }]
  })
  if (facts.length) return facts.slice(0, 12)
  const record = selectedSimulationRecord.value?.record
  return record
    ? [
        { label: '记录类型', value: record.kind_label },
        { label: '业务编号', value: record.code },
        { label: '明细数量', value: String(record.event_count) },
      ]
    : []
})

const latestDataModelVersion = computed(() => selectedDataModel.value?.versions?.[0])

const selectedDataFieldSummary = computed<DataFieldSummary | undefined>(() =>
  selectedDataSimulation.value?.summary.fields?.[activeDataFieldCode.value],
)

const activeDataFieldName = computed(
  () =>
    selectedDataSimulation.value?.rules_snapshot.find(
      (item) => item.code === activeDataFieldCode.value,
    )?.name || '指标',
)

const chartSeries = computed(() =>
  (selectedDataSimulation.value?.points || [])
    .map((item) => Number(item.values[activeDataFieldCode.value]))
    .filter((value) => Number.isFinite(value)),
)

const chartCoordinates = computed(() => {
  const values = chartSeries.value
  if (!values.length) return []
  const minimum = Math.min(...values)
  const maximum = Math.max(...values)
  const span = maximum - minimum || 1
  return values.map((value, index) => ({
    x: 22 + (index / Math.max(values.length - 1, 1)) * 716,
    y: 190 - ((value - minimum) / span) * 162,
  }))
})

const chartPolyline = computed(() =>
  chartCoordinates.value.map((item) => `${item.x.toFixed(2)},${item.y.toFixed(2)}`).join(' '),
)
const chartAreaPoints = computed(() =>
  chartCoordinates.value.length ? `22,190 ${chartPolyline.value} 738,190` : '',
)
const chartMaximumLabel = computed(() =>
  chartSeries.value.length ? formatDataValue(Math.max(...chartSeries.value)) : '—',
)
const chartMinimumLabel = computed(() =>
  chartSeries.value.length ? formatDataValue(Math.min(...chartSeries.value)) : '—',
)

const canPrepareData = computed(() =>
  selectedInstance.value ? ['DRAFT', 'READY'].includes(selectedInstance.value.status) : false,
)

function cleanFilters(source: ComplaintFilters): ComplaintFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as ComplaintFilters
}

function cleanProcessFilters(source: ProcessRunFilters): ProcessRunFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as ProcessRunFilters
}

function cleanDataFilters(source: DataSimulationFilters): DataSimulationFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as DataSimulationFilters
}

function cleanDataModelFilters(source: DataModelFilters): DataModelFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as DataModelFilters
}

function cleanTracebackFilters(source: TracebackFilters): TracebackFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as TracebackFilters
}

function cleanSimulationRecordFilters(source: SimulationRecordFilters): SimulationRecordFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as SimulationRecordFilters
}

function cleanCapabilityCallFilters(source: CapabilityCallFilters): CapabilityCallFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as CapabilityCallFilters
}

function cleanFaultConfigurationFilters(
  source: FaultConfigurationFilters,
): FaultConfigurationFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as FaultConfigurationFilters
}

function cleanFaultReportFilters(source: FaultReportFilters): FaultReportFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as FaultReportFilters
}

function cleanSceneLibraryFilters(source: SceneLibraryFilters): SceneLibraryFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as SceneLibraryFilters
}

function cleanSceneFilters(source: SceneRunFilters): SceneRunFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as SceneRunFilters
}

function cleanAlertFilters(source: AlertFilters): AlertFilters {
  return Object.fromEntries(
    Object.entries(source).filter(
      ([, value]) => value !== '' && value !== undefined && value !== null,
    ),
  ) as AlertFilters
}

function requestId(prefix: string) {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2, 8)}`
}

function formatTime(value: string | null) {
  return value ? datetimeFormat(value) : '—'
}

function formatTimeRange(start: string | null, end: string | null) {
  if (!start && !end) return '—'
  return `${formatTime(start)} → ${formatTime(end)}`
}

function formatDuration(seconds: number) {
  if (!seconds) return '0 秒'
  if (seconds < 60) return `${seconds} 秒`
  if (seconds < 3600) return `${Math.floor(seconds / 60)} 分 ${seconds % 60} 秒`
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  return `${hours} 小时 ${minutes} 分`
}

function formatFileSize(bytes: number) {
  if (!bytes) return '0 B'
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function reportCountdown(report: FaultReport) {
  if (['RECOVERED', 'CLOSED'].includes(report.status)) return { text: '阶段已完成', overdue: false }
  const delta = new Date(report.stage_deadline_at).getTime() - clockNow.value
  const totalSeconds = Math.max(Math.floor(Math.abs(delta) / 1000), 0)
  const hours = Math.floor(totalSeconds / 3600)
  const minutes = Math.floor((totalSeconds % 3600) / 60)
  const seconds = totalSeconds % 60
  const text = `${hours ? `${hours}h ` : ''}${String(minutes).padStart(2, '0')}m ${String(seconds).padStart(2, '0')}s`
  return { text: delta < 0 ? `超时 ${text}` : `剩余 ${text}`, overdue: delta < 0 }
}

function formatRecordDetail(detail: Record<string, unknown>) {
  const entries = Object.entries(detail || {}).slice(0, 4)
  if (!entries.length) return '无补充说明'
  return entries
    .map(([key, value]) => `${key}: ${typeof value === 'object' ? JSON.stringify(value) : String(value)}`)
    .join(' · ')
}

function formatJson(value: Record<string, unknown> | undefined) {
  return JSON.stringify(value || {}, null, 2)
}

function simulationRecordKindCode(kind: SimulationRecordKind) {
  return {
    INSTANCE: 'RUN',
    COMPLAINT_BATCH: 'CMP',
    DATA_BATCH: 'DAT',
    PROCESS_RUN: 'PRC',
    SCENE_RUN: 'SCN',
    ALERT: 'ALT',
    TRACEBACK: 'TRC',
    CAPABILITY_CALL: 'CAP',
    FAULT_REPORT: 'RPT',
    AUXILIARY_SIMULATION: 'AUX',
  }[kind]
}

function simulationRecordTagType(state: SimulationRecordState) {
  return {
    PENDING: 'info',
    RUNNING: 'primary',
    SUCCEEDED: 'success',
    ATTENTION: 'warning',
    FAILED: 'danger',
  }[state]
}

function capabilityStatusTagType(status: CapabilityCallStatus) {
  return {
    SUCCEEDED: 'success',
    FAILED: 'danger',
    TIMEOUT: 'warning',
  }[status]
}

function faultConfigurationStatusTagType(status: FaultConfigurationStatus) {
  return {
    DRAFT: 'warning',
    READY: 'success',
    ARCHIVED: 'info',
  }[status]
}

function sceneReplayTagType(status: SceneReplayStatus) {
  return status === 'READY' ? 'success' : 'warning'
}

function faultReportStatusTagType(status: FaultReportStatus) {
  return {
    DRAFT: 'info',
    REPORTED: 'warning',
    PROCESSING: 'primary',
    RECOVERED: 'success',
    CLOSED: 'success',
  }[status]
}

function faultReportLevelCode(level: FaultReportLevel) {
  return { LEVEL_1: 'L1', LEVEL_2: 'L2', LEVEL_3: 'L3', LEVEL_4: 'L4' }[level]
}

function faultReportActionLabel(action: FaultReportAction) {
  return {
    SUBMITTED: '正式上报',
    ACCEPTED: '受理故障',
    STAGE_ADVANCED: '推进下一阶段',
    ESCALATED: '升级故障等级',
    ATTACHMENT_ADDED: '补充证据引用',
    RECOVERED: '确认故障恢复',
    CLOSED: '关闭并归档',
  }[action]
}

function factorCategoryLabel(category: RandomFactorDefinition['category']) {
  return { NETWORK: '网络类', FAULT: '故障类', TRAFFIC: '流量类' }[category]
}

function faultNodeStateClass(state = '') {
  return `state-${state.toLowerCase() || 'unknown'}`
}

function faultNodeStateLabel(state = '') {
  const labels: Record<string, string> = {
    HEALTHY: '正常',
    FAULT: '故障',
    STANDBY: '备用',
    DEGRADED: '降级',
    ACTIVE: '在线',
    RECOVERED: '已恢复',
  }
  return labels[state] || state || '未知'
}

function formatDataValue(value: number | undefined) {
  if (value === undefined || !Number.isFinite(value)) return '—'
  return new Intl.NumberFormat('zh-CN', { maximumFractionDigits: 4 }).format(value)
}

function dataModelSourceSummary(model: RehearsalDataModel) {
  const counts = model.summary.source_counts || {}
  return `${counts.valid_complaints || 0} 申告 · ${counts.data_points || 0} 时序点 · ${counts.alerts || 0} 告警`
}

function dataModelSourceEntries(model: RehearsalDataModel) {
  const counts = model.summary.source_counts || {}
  return [
    { label: '有效申告', value: counts.valid_complaints || 0 },
    { label: '时序点', value: counts.data_points || 0 },
    { label: '处置流程', value: counts.process_runs || 0 },
    { label: '场景执行', value: counts.scene_runs || 0 },
    { label: '工单', value: counts.work_orders || 0 },
    { label: '告警事件', value: counts.alert_events || 0 },
  ]
}

function signedDataValue(value: number) {
  return `${value > 0 ? '+' : ''}${formatDataValue(value)}`
}

function trendLabel(trend: DataFieldSummary['trend']) {
  return trend === 'UP' ? '趋势上升' : trend === 'DOWN' ? '趋势下降' : '趋势平稳'
}

function statusTagType(status: InstanceStatus) {
  const types = {
    DRAFT: 'info',
    READY: 'warning',
    RUNNING: 'success',
    COMPLETED: 'primary',
    CANCELLED: 'info',
    FAILED: 'danger',
  } as const
  return types[status]
}

function batchTagType(status: ComplaintBatch['status']) {
  return status === 'READY' ? 'success' : status === 'PARTIAL' ? 'warning' : 'danger'
}

function processTagType(status: ProcessRunStatus) {
  const types = {
    PENDING: 'info',
    RUNNING: 'success',
    BLOCKED: 'warning',
    COMPLETED: 'primary',
    CANCELLED: 'info',
    FAILED: 'danger',
  } as const
  return types[status]
}

function stepTagType(status: ProcessStepStatus) {
  const types = {
    PENDING: 'info',
    RUNNING: 'success',
    BLOCKED: 'warning',
    COMPLETED: 'primary',
    SKIPPED: 'info',
    FAILED: 'danger',
  } as const
  return types[status]
}

function dataKindTagType(kind: DataSimulationKind) {
  return kind === 'METRIC' ? 'success' : 'warning'
}

function dataModelQualityTagType(status: DataModelQualityStatus) {
  const types = { PASS: 'success', WARN: 'warning', FAIL: 'danger' } as const
  return types[status]
}

function tracebackStatusTagType(status: TracebackStatus) {
  const types = { READY: 'success', EMPTY: 'warning', ARCHIVED: 'info' } as const
  return types[status]
}

function tracebackKindEntries(traceback: RehearsalTraceback) {
  return tracebackKindOptions
    .map((item) => ({ kind: item.value, label: item.label, count: traceback.kind_counts[item.value] || 0 }))
    .filter((item) => item.count > 0)
}

function sceneLibraryTagType(status: SceneLibraryStatus) {
  const types = { DRAFT: 'info', READY: 'success', ARCHIVED: 'info' } as const
  return types[status]
}

function dataModelLoadTagType(status: string) {
  const types = { LOADED: 'success', PARTIAL: 'warning', FAILED: 'danger' } as const
  return types[status as keyof typeof types] || 'info'
}

function sceneTagType(status: SceneRunStatus) {
  const types = {
    PENDING: 'info',
    RUNNING: 'success',
    COMPLETED: 'primary',
    CANCELLED: 'info',
    FAILED: 'danger',
  } as const
  return types[status]
}

function sceneStepTagType(status: SceneStepStatus) {
  const types = {
    PENDING: 'info',
    RUNNING: 'success',
    COMPLETED: 'primary',
    SKIPPED: 'info',
    FAILED: 'danger',
  } as const
  return types[status]
}

function workOrderTagType(status: WorkOrderStatus) {
  const types = { OPEN: 'warning', PROCESSING: 'primary', RESOLVED: 'success', CLOSED: 'info' } as const
  return types[status]
}

function alertStatusTagType(status: AlertStatus) {
  const types = {
    PENDING: 'info',
    ACTIVE: 'danger',
    ACKNOWLEDGED: 'warning',
    RECOVERED: 'success',
  } as const
  return types[status]
}

function alertSeverityTagType(severity: AlertSeverity) {
  const types = { LOW: 'info', MEDIUM: 'warning', HIGH: 'danger', CRITICAL: 'danger' } as const
  return types[severity]
}

function formatAlertDuration(seconds: number) {
  if (!seconds) return '尚未计时'
  if (seconds < 60) return `${seconds} 秒`
  const minutes = Math.floor(seconds / 60)
  return minutes < 60 ? `${minutes} 分钟` : `${Math.floor(minutes / 60)} 小时 ${minutes % 60} 分钟`
}

function timelineKindLabel(kind: string) {
  const labels: Record<string, string> = {
    COMPLAINT: '申告',
    METRIC: '指标',
    SENTIMENT: '舆情',
    PROCESS: '处置',
    SCENE: '场景',
    ALERT: '告警',
    WORK_ORDER: '工单',
  }
  return labels[kind] || kind
}

function currentStepName(run: ProcessRun) {
  if (run.status === 'COMPLETED') return '已全部完成'
  if (run.status === 'CANCELLED') return '流程已取消'
  if (run.status === 'FAILED') return '流程失败'
  return (
    run.steps?.find((item) => item.code === run.current_step_code)?.name ||
    run.current_step_name ||
    run.current_step_code ||
    '尚未启动'
  )
}

function currentSceneStepName(run: SceneRun) {
  if (run.status === 'COMPLETED') return '已全部完成'
  if (run.status === 'CANCELLED') return '场景已取消'
  if (run.status === 'FAILED') return '场景失败'
  return (
    run.steps?.find((item) => item.code === run.current_step_code)?.name ||
    run.current_step_name ||
    run.current_step_code ||
    '尚未启动'
  )
}

async function loadDashboard() {
  const response = await rehearsalApi.getDashboard(loading)
  dashboard.value = response.data
  if (!createForm.scenario_id && dashboard.value.scenarios[0]) {
    createForm.scenario_id = dashboard.value.scenarios[0].id
  }
  if (!generateForm.template_id && dashboard.value.templates[0]) {
    generateForm.template_id = dashboard.value.templates[0].id
  }
  if (!processForm.template_id && dashboard.value.process_templates[0]) {
    selectProcessTemplate(dashboard.value.process_templates[0], false)
  }
  if (!dataForm.instance_id && availableDataInstances.value[0]) {
    dataForm.instance_id = availableDataInstances.value[0].id
  }
  if (!dataForm.template_id && dashboard.value.data_templates[0]) {
    applyDataTemplate(dashboard.value.data_templates[0].id)
  }
  if (!dataModelForm.instance_id && dashboard.value.instances[0]) {
    dataModelForm.instance_id = dashboard.value.instances[0].id
    syncDataModelScene()
  }
  if (!tracebackForm.instance_id && dashboard.value.instances[0]) {
    tracebackForm.instance_id = dashboard.value.instances[0].id
    syncTracebackLinks()
  }
  if (!capabilityInvokeForm.instance_id && dashboard.value.instances[0]) {
    capabilityInvokeForm.instance_id = dashboard.value.instances[0].id
  }
  if (!capabilityInvokeForm.capability_id && dashboard.value.capability_mocks[0]) {
    selectCapabilityMock(dashboard.value.capability_mocks[0])
  }
  if (!capabilityMockForm.scenario_id && dashboard.value.scenarios[0]) {
    capabilityMockForm.scenario_id = dashboard.value.scenarios[0].id
  }
  if (!faultConfigurationForm.scenario_id && dashboard.value.scenarios[0]) {
    faultConfigurationForm.scenario_id = dashboard.value.scenarios[0].id
  }
  if (!faultConfigurationApplyForm.instance_id && dashboard.value.instances[0]) {
    faultConfigurationApplyForm.instance_id = dashboard.value.instances[0].id
  }
  if (!sceneReplayForm.instance_id && sceneReplayInstances.value[0]) {
    sceneReplayForm.instance_id = sceneReplayInstances.value[0].id
    syncSceneReplayRun()
  }
  if (!faultReportForm.instance_id && faultReportInstances.value[0]) {
    faultReportForm.instance_id = faultReportInstances.value[0].id
  }
  if (!faultReportForm.template_id && availableFaultReportTemplates.value[0]) {
    applyFaultReportTemplate(availableFaultReportTemplates.value[0].id)
  }
  if (!sceneScriptForm.scenario_id && dashboard.value.scenarios[0]) {
    sceneScriptForm.scenario_id = dashboard.value.scenarios[0].id
  }
  if (!sceneLibraryForm.scenario_id && dashboard.value.scenarios[0]) {
    sceneLibraryForm.scenario_id = dashboard.value.scenarios[0].id
  }
  if (!sceneLibraryForm.script_id && dashboard.value.scene_scripts[0]) {
    sceneLibraryForm.script_id = dashboard.value.scene_scripts[0].id
  }
  if (!sceneCreateForm.script_id && dashboard.value.scene_scripts[0]) {
    sceneCreateForm.script_id = dashboard.value.scene_scripts[0].id
  }
  if (!alertTemplateForm.scenario_id && dashboard.value.scenarios[0]) {
    alertTemplateForm.scenario_id = dashboard.value.scenarios[0].id
  }
  if (!alertCreateForm.template_id && dashboard.value.alert_templates[0]) {
    applyAlertTemplate(dashboard.value.alert_templates[0].id)
  }
}

async function loadComplaints(page = complaintPage.value.page) {
  filters.page = page
  const response = await rehearsalApi.getComplaints(cleanFilters(filters), complaintLoading)
  complaintPage.value = response.data
}

async function loadProcessRuns(page = processPage.value.page) {
  processFilters.page = page
  const response = await rehearsalApi.getProcessRuns(
    cleanProcessFilters(processFilters),
    processLoading,
  )
  processPage.value = response.data
}

async function loadDataSimulations(page = dataPage.value.page) {
  dataFilters.page = page
  const response = await rehearsalApi.getDataSimulations(cleanDataFilters(dataFilters), dataLoading)
  dataPage.value = response.data
}

async function loadDataModels(page = dataModelPage.value.page) {
  dataModelFilters.page = page
  const response = await rehearsalApi.getDataModels(
    cleanDataModelFilters(dataModelFilters),
    dataModelLoading,
  )
  dataModelPage.value = response.data
}

async function loadTracebacks(page = tracebackPage.value.page) {
  tracebackFilters.page = page
  const response = await rehearsalApi.getTracebacks(
    cleanTracebackFilters(tracebackFilters),
    tracebackLoading,
  )
  tracebackPage.value = response.data
}

async function loadSimulationRecords(page = simulationRecordPage.value.page) {
  simulationRecordFilters.page = page
  const response = await rehearsalApi.getSimulationRecords(
    cleanSimulationRecordFilters(simulationRecordFilters),
    simulationRecordLoading,
  )
  simulationRecordPage.value = response.data
}

async function loadCapabilityCalls(page = capabilityCallPage.value.page) {
  capabilityCallFilters.page = page
  const response = await rehearsalApi.getCapabilityCalls(
    cleanCapabilityCallFilters(capabilityCallFilters),
    capabilityCallLoading,
  )
  capabilityCallPage.value = response.data
}

async function loadFaultConfigurations(page = faultConfigurationPage.value.page) {
  faultConfigurationFilters.page = page
  const response = await rehearsalApi.getFaultConfigurations(
    cleanFaultConfigurationFilters(faultConfigurationFilters),
    faultConfigurationLoading,
  )
  faultConfigurationPage.value = response.data
  if (
    !faultConfigurationPreviewId.value ||
    !response.data.items.some((item) => item.id === faultConfigurationPreviewId.value)
  ) {
    faultConfigurationPreviewId.value = response.data.items[0]?.id || ''
  }
  if (
    !faultConfigurationApplyForm.instance_id ||
    !faultConfigurationInstances.value.some(
      (item) => item.id === faultConfigurationApplyForm.instance_id,
    )
  ) {
    faultConfigurationApplyForm.instance_id = faultConfigurationInstances.value[0]?.id || ''
  }
}

async function loadSceneReplays(page = sceneReplayPage.value.page) {
  sceneReplayFilters.page = page
  const response = await rehearsalApi.getSceneReplays(sceneReplayFilters, sceneReplayLoading)
  sceneReplayPage.value = response.data
  const preview = response.data.items.find((item) => item.id === selectedSceneReplay.value?.id)
    || response.data.items[0]
  if (preview && (!selectedSceneReplay.value || selectedSceneReplay.value.id !== preview.id)) {
    await selectSceneReplay(preview)
  } else if (!preview) {
    selectedSceneReplay.value = undefined
  }
}

async function loadFaultReports(page = faultReportPage.value.page) {
  faultReportFilters.page = page
  const response = await rehearsalApi.getFaultReports(
    cleanFaultReportFilters(faultReportFilters),
    faultReportLoading,
  )
  faultReportPage.value = response.data
  const preview = response.data.items.find((item) => item.id === selectedFaultReport.value?.id)
    || response.data.items[0]
  if (preview && preview.id !== selectedFaultReport.value?.id) {
    await selectFaultReport(preview)
  } else if (!preview) {
    selectedFaultReport.value = undefined
  }
}

async function loadAuxiliarySimulations(page = auxiliarySimulationPage.value.page) {
  auxiliarySimulationFilters.page = page
  const response = await rehearsalApi.getAuxiliarySimulations(
    auxiliarySimulationFilters,
    auxiliarySimulationLoading,
  )
  auxiliarySimulationPage.value = response.data
  const preview = response.data.items.find(
    (item) => item.id === selectedAuxiliarySimulation.value?.id,
  ) || response.data.items[0]
  if (preview && preview.id !== selectedAuxiliarySimulation.value?.id) {
    await selectAuxiliarySimulation(preview)
  } else if (!preview) {
    selectedAuxiliarySimulation.value = undefined
  }
}

async function loadSceneLibraries(page = sceneLibraryPage.value.page) {
  sceneLibraryFilters.page = page
  const response = await rehearsalApi.getSceneLibraries(
    cleanSceneLibraryFilters(sceneLibraryFilters),
    sceneLibraryLoading,
  )
  sceneLibraryPage.value = response.data
}

async function loadSceneRuns(page = scenePage.value.page) {
  sceneFilters.page = page
  const response = await rehearsalApi.getSceneRuns(cleanSceneFilters(sceneFilters), sceneLoading)
  scenePage.value = response.data
}

async function loadAlerts(page = alertPage.value.page) {
  alertFilters.page = page
  const response = await rehearsalApi.getAlerts(cleanAlertFilters(alertFilters), alertLoading)
  alertPage.value = response.data
}

async function refreshAll() {
  await Promise.all([
    loadDashboard(),
    loadComplaints(),
    loadProcessRuns(),
    loadDataSimulations(),
    loadDataModels(),
    loadTracebacks(),
    loadSimulationRecords(),
    loadCapabilityCalls(),
    loadFaultConfigurations(),
    loadSceneReplays(),
    loadFaultReports(),
    loadAuxiliarySimulations(),
    loadSceneLibraries(),
    loadSceneRuns(),
    loadAlerts(),
  ])
}

function resetFilters() {
  Object.assign(filters, {
    page: 1,
    page_size: 20,
    instance_id: '',
    customer_type: '',
    severity: '',
    validation_status: '',
    source: '',
    keyword: '',
  })
  loadComplaints(1)
}

function exportCurrentComplaints() {
  return rehearsalApi.exportComplaints(cleanFilters(filters), exporting)
}

function resetProcessFilters() {
  Object.assign(processFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    template_id: '',
    status: '',
    auto_advance: '',
    keyword: '',
  })
  loadProcessRuns(1)
}

function exportCurrentProcessRuns() {
  return rehearsalApi.exportProcessRuns(cleanProcessFilters(processFilters), processExporting)
}

function resetDataFilters() {
  Object.assign(dataFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    template_id: '',
    kind: '',
    status: '',
    tag: '',
    keyword: '',
  })
  loadDataSimulations(1)
}

function exportCurrentDataSimulations() {
  return rehearsalApi.exportDataSimulations(cleanDataFilters(dataFilters), dataExporting)
}

function resetDataModelFilters() {
  Object.assign(dataModelFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    scene_run_id: '',
    build_strategy: '',
    quality_status: '',
    keyword: '',
  })
  loadDataModels(1)
}

function resetTracebackFilters() {
  Object.assign(tracebackFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    scope: '',
    status: '',
    kind: '',
    keyword: '',
  })
  loadTracebacks(1)
}

function exportCurrentTracebacks() {
  return rehearsalApi.exportTracebacks(cleanTracebackFilters(tracebackFilters), tracebackExporting)
}

function resetSimulationRecordFilters() {
  Object.assign(simulationRecordFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    kind: '',
    state: '',
    keyword: '',
    date_from: '',
    date_to: '',
  })
  loadSimulationRecords(1)
}

function exportCurrentSimulationRecords() {
  return rehearsalApi.exportSimulationRecords(
    cleanSimulationRecordFilters(simulationRecordFilters),
    simulationRecordExporting,
  )
}

function resetCapabilityCallFilters() {
  Object.assign(capabilityCallFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    capability_id: '',
    kind: '',
    status: '',
    warroom_group: '',
    keyword: '',
    date_from: '',
    date_to: '',
  })
  loadCapabilityCalls(1)
}

function filterWarroom(name: string) {
  capabilityCallFilters.warroom_group = capabilityCallFilters.warroom_group === name ? '' : name
  loadCapabilityCalls(1)
}

function resetSceneLibraryFilters() {
  Object.assign(sceneLibraryFilters, {
    page: 1,
    page_size: 10,
    scenario_id: '',
    script_id: '',
    status: '',
    visibility: '',
    keyword: '',
  })
  loadSceneLibraries(1)
}

function selectSceneLibraryScript(script: SceneScript) {
  sceneLibraryFilters.script_id = script.id
  sceneLibraryForm.script_id = script.id
  sceneLibraryForm.scenario_id = script.scenario_id
  loadSceneLibraries(1)
}

function resetSceneFilters() {
  Object.assign(sceneFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    script_id: '',
    status: '',
    keyword: '',
  })
  loadSceneRuns(1)
}

function selectSceneScript(script: SceneScript) {
  sceneFilters.script_id = script.id
  sceneCreateForm.script_id = script.id
  loadSceneRuns(1)
}

function resetAlertFilters() {
  Object.assign(alertFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    template_id: '',
    status: '',
    severity: '',
    keyword: '',
  })
  loadAlerts(1)
}

function selectAlertTemplate(template: AlertTemplate) {
  alertFilters.template_id = template.id
  alertCreateForm.template_id = template.id
  applyAlertTemplate(template.id)
  loadAlerts(1)
}

function openCreateDialog() {
  createForm.name = ''
  createForm.code = ''
  createForm.planned_start_at = null
  createForm.scenario_id = dashboard.value.scenarios[0]?.id || ''
  createDialogVisible.value = true
}

async function submitInstance() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return
  const response = await rehearsalApi.createInstance(
    {
      request_id: requestId('ui-instance'),
      scenario_id: createForm.scenario_id,
      name: createForm.name,
      code: createForm.code || undefined,
      planned_start_at: createForm.planned_start_at,
      parameters: { capability: 'X18', source: 'rehearsal_console' },
    },
    submitting,
  )
  ElMessage.success(response.data.created ? '预演实例已创建' : '已返回幂等实例')
  createDialogVisible.value = false
  await Promise.all([loadDashboard(), loadSimulationRecords(1)])
  await openInstance(response.data.instance)
}

function chooseTemplate(template: ComplaintTemplate) {
  generateForm.template_id = template.id
  if (!selectedInstance.value) {
    ElMessage.info(`已选择“${template.name}”，请先新建或进入一个预演实例`)
    return
  }
  ElMessage.success(`已切换为“${template.name}”`)
}

function selectProcessTemplate(template: ProcessTemplate, filter = true) {
  processForm.template_id = template.id
  processForm.auto_advance = template.auto_advance
  if (filter) {
    processFilters.template_id = template.id
    loadProcessRuns(1)
  }
}

function cloneDataRules(rules: DataSimulationRule[]) {
  return rules.map((item) => ({ ...item }))
}

function applyDataTemplate(templateId: string) {
  const template = dashboard.value.data_templates.find((item) => item.id === templateId)
  if (!template) return
  dataForm.template_id = template.id
  dataForm.rules = cloneDataRules(template.default_rules)
  dataForm.tags = [...template.default_tags]
}

function openDataCreate(template?: DataSimulationTemplate) {
  const selected = template || dashboard.value.data_templates[0]
  dataForm.instance_id =
    selectedInstance.value && ['DRAFT', 'READY', 'RUNNING'].includes(selectedInstance.value.status)
      ? selectedInstance.value.id
      : availableDataInstances.value[0]?.id || ''
  dataForm.name = ''
  dataForm.count = 24
  dataForm.start_at = new Date().toISOString()
  dataForm.interval_minutes = 5
  if (selected) applyDataTemplate(selected.id)
  dataCreateDrawerVisible.value = true
}

function addDataRule() {
  if (dataForm.rules.length >= 8) return
  const index = dataForm.rules.length + 1
  dataForm.rules.push({
    code: `CUSTOM_FIELD_${index}`,
    name: `自定义字段${index}`,
    unit: '',
    min_value: 0,
    max_value: 100,
    start_value: 20,
    end_value: 80,
    distribution: 'LINEAR',
    decimals: 1,
  })
}

function removeDataRule(index: number) {
  if (dataForm.rules.length > 1) dataForm.rules.splice(index, 1)
}

function validateDataRules() {
  if (!dataForm.instance_id || !dataForm.template_id || !dataForm.start_at) {
    return '请完整填写预演实例、数据模板和序列起点'
  }
  if (!dataForm.rules.length) return '至少需要一个数据字段'
  const codes = new Set<string>()
  for (const [index, rule] of dataForm.rules.entries()) {
    rule.code = rule.code.trim().toUpperCase()
    rule.name = rule.name.trim()
    if (!/^[A-Z][A-Z0-9_]{0,31}$/.test(rule.code)) return `第 ${index + 1} 个字段编号格式不正确`
    if (!rule.name) return `第 ${index + 1} 个字段缺少显示名称`
    if (codes.has(rule.code)) return `字段编号 ${rule.code} 重复`
    if (rule.min_value >= rule.max_value) return `${rule.name}的最小值必须小于最大值`
    if (
      rule.start_value < rule.min_value ||
      rule.start_value > rule.max_value ||
      rule.end_value < rule.min_value ||
      rule.end_value > rule.max_value
    ) return `${rule.name}的起止值必须位于最小值和最大值之间`
    codes.add(rule.code)
  }
  return ''
}

async function generateSimulationData() {
  const validationError = validateDataRules()
  if (validationError) {
    ElMessage.warning(validationError)
    return
  }
  const response = await rehearsalApi.generateSimulationData(
    dataForm.instance_id,
    {
      request_id: requestId('ui-data-simulation'),
      template_id: dataForm.template_id,
      name: dataForm.name || undefined,
      count: dataForm.count,
      start_at: dataForm.start_at,
      interval_minutes: dataForm.interval_minutes,
      rules: cloneDataRules(dataForm.rules),
      tags: [...dataForm.tags],
    },
    dataGenerating,
  )
  dataCreateDrawerVisible.value = false
  ElMessage.success(`已生成 ${response.data.batch.point_count} 个时序点`)
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadDataSimulations(1)])
  if (selectedInstance.value?.id === dataForm.instance_id) await refreshSelectedInstance()
  await openDataSimulation(response.data.batch)
}

async function openDataSimulation(batch: DataSimulationBatch) {
  dataDetailDrawerVisible.value = true
  dataDetailLoading.value = true
  try {
    const response = await rehearsalApi.getDataSimulation(batch.id)
    selectedDataSimulation.value = response.data
    activeDataFieldCode.value = response.data.rules_snapshot[0]?.code || ''
  } finally {
    dataDetailLoading.value = false
  }
}

function exportSelectedDataSimulation() {
  if (!selectedDataSimulation.value) return
  return rehearsalApi.exportDataSimulations(
    { batch_id: selectedDataSimulation.value.id },
    dataExporting,
  )
}

function syncDataModelScene() {
  if (!availableDataModelSceneRuns.value.some((item) => item.id === dataModelForm.scene_run_id)) {
    dataModelForm.scene_run_id = availableDataModelSceneRuns.value[0]?.id || ''
  }
}

function openDataModelCreate(instance?: RehearsalInstance) {
  const target = instance || selectedInstance.value || dashboard.value.instances[0]
  dataModelForm.instance_id = target?.id || ''
  dataModelForm.scene_run_id = ''
  dataModelForm.name = ''
  dataModelForm.description = ''
  dataModelForm.build_strategy = 'FULL_INSTANCE'
  dataModelForm.transformer_code = 'CANONICAL_V1'
  syncDataModelScene()
  dataModelCreateDrawerVisible.value = true
}

function validateDataModelForm() {
  dataModelForm.transformer_code = dataModelForm.transformer_code.trim().toUpperCase()
  if (!dataModelForm.instance_id) return '请选择预演实例'
  if (!/^[A-Z][A-Z0-9_]{0,63}$/.test(dataModelForm.transformer_code)) {
    return '转换器编号需以字母开头且只含大写字母、数字或下划线'
  }
  if (dataModelForm.build_strategy === 'SCENE_LINKED' && !dataModelForm.scene_run_id) {
    return '场景关联构建需要选择一个场景执行'
  }
  return ''
}

async function createDataModelFromForm() {
  const validationError = validateDataModelForm()
  if (validationError) {
    ElMessage.warning(validationError)
    return
  }
  const response = await rehearsalApi.createDataModel(
    dataModelForm.instance_id,
    {
      request_id: requestId('ui-data-model'),
      name: dataModelForm.name.trim() || undefined,
      description: dataModelForm.description.trim() || undefined,
      build_strategy: dataModelForm.build_strategy,
      transformer_code: dataModelForm.transformer_code,
      scene_run_id: dataModelForm.scene_run_id || null,
      source_scope: {
        source: 'ui',
        scene_run_id: dataModelForm.scene_run_id || null,
      },
    },
    dataModelCreating,
  )
  dataModelCreateDrawerVisible.value = false
  ElMessage.success(response.data.created ? '预演数据模型已构建' : '已返回幂等数据模型')
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadDataModels(1)])
  if (selectedInstance.value?.id === dataModelForm.instance_id) await refreshSelectedInstance()
  await openDataModel(response.data.data_model)
}

async function openDataModel(model: RehearsalDataModel) {
  dataModelDrawerVisible.value = true
  dataModelDetailLoading.value = true
  try {
    const response = await rehearsalApi.getDataModel(model.id)
    selectedDataModel.value = response.data
    dataModelFilters.instance_id = response.data.instance_id
  } finally {
    dataModelDetailLoading.value = false
  }
}

async function reloadDataModel(model: RehearsalDataModel) {
  const response = await rehearsalApi.loadDataModel(
    model.id,
    {
      request_id: requestId('ui-data-model-load'),
      note: '页面手动重新加载',
    },
    dataModelLoadingVersion,
  )
  selectedDataModel.value = response.data.data_model
  ElMessage.success(response.data.created ? `已生成 V${response.data.data_model.current_version}` : '已返回幂等加载记录')
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadDataModels(dataModelPage.value.page)])
}

function syncTracebackLinks() {
  if (!availableTracebackSceneRuns.value.some((item) => item.id === tracebackForm.scene_run_id)) {
    tracebackForm.scene_run_id = availableTracebackSceneRuns.value[0]?.id || null
  }
  if (!availableTracebackDataModels.value.some((item) => item.id === tracebackForm.data_model_id)) {
    tracebackForm.data_model_id = availableTracebackDataModels.value[0]?.id || null
  }
}

function openTracebackCreate(instance?: RehearsalInstance) {
  const target = instance || selectedInstance.value || dashboard.value.instances[0]
  tracebackForm.instance_id = target?.id || ''
  tracebackForm.scene_run_id = null
  tracebackForm.data_model_id = null
  tracebackForm.name = target ? `${target.name} · 数据动态回溯` : ''
  tracebackForm.description = ''
  tracebackForm.scope = 'FULL_INSTANCE'
  tracebackForm.kind_scope = tracebackKindOptions.map((item) => item.value)
  tracebackForm.window_start = null
  tracebackForm.window_end = null
  syncTracebackLinks()
  tracebackCreateDrawerVisible.value = true
}

function validateTracebackForm() {
  if (!tracebackForm.instance_id) return '请选择预演实例'
  if (!tracebackForm.kind_scope.length) return '请至少选择一个事实节点'
  if (tracebackForm.scope === 'CUSTOM' && (!tracebackForm.window_start || !tracebackForm.window_end)) {
    return '自定义窗口需要同时填写开始和结束时间'
  }
  if (
    tracebackForm.window_start &&
    tracebackForm.window_end &&
    new Date(tracebackForm.window_start).getTime() > new Date(tracebackForm.window_end).getTime()
  ) return '回溯开始时间不能晚于结束时间'
  return ''
}

async function submitTracebackForm() {
  const validationError = validateTracebackForm()
  if (validationError) {
    ElMessage.warning(validationError)
    return
  }
  const response = await rehearsalApi.createTraceback(
    tracebackForm.instance_id,
    {
      request_id: requestId('ui-traceback'),
      name: tracebackForm.name.trim() || undefined,
      description: tracebackForm.description.trim() || undefined,
      scope: tracebackForm.scope,
      scene_run_id: tracebackForm.scene_run_id || null,
      data_model_id: tracebackForm.data_model_id || null,
      kind_scope: [...tracebackForm.kind_scope],
      window_start: tracebackForm.scope === 'FULL_INSTANCE' ? null : tracebackForm.window_start,
      window_end: tracebackForm.scope === 'FULL_INSTANCE' ? null : tracebackForm.window_end,
    },
    tracebackCreating,
  )
  tracebackCreateDrawerVisible.value = false
  ElMessage.success(response.data.created ? '数据动态回溯已生成' : '已返回幂等回溯快照')
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadTracebacks(1)])
  if (selectedInstance.value?.id === tracebackForm.instance_id) await refreshSelectedInstance()
  await openTraceback(response.data.traceback)
}

async function openTraceback(traceback: RehearsalTraceback) {
  tracebackDrawerVisible.value = true
  tracebackDetailLoading.value = true
  try {
    const response = await rehearsalApi.getTraceback(traceback.id)
    selectedTraceback.value = response.data
  } finally {
    tracebackDetailLoading.value = false
  }
}

function exportSelectedTraceback() {
  if (!selectedTraceback.value) return
  return rehearsalApi.exportTracebacks({ keyword: selectedTraceback.value.code }, tracebackExporting)
}

async function openSimulationRecord(record: SimulationRecord) {
  simulationRecordDrawerVisible.value = true
  simulationRecordDetailLoading.value = true
  try {
    const response = await rehearsalApi.getSimulationRecord(record.kind, record.resource_id)
    selectedSimulationRecord.value = response.data
  } finally {
    simulationRecordDetailLoading.value = false
  }
}

function capabilityPayloadExample(mock: CapabilityMock) {
  const required = Array.isArray(mock.request_schema.required)
    ? (mock.request_schema.required as string[])
    : []
  return Object.fromEntries(
    required.map((field) => {
      if (field.includes('resource')) return [field, 'NE-X27-001']
      if (field.includes('node')) return [field, 'NODE-X27-01']
      if (field.includes('strategy')) return [field, 'DRAIN_AND_BYPASS']
      return [field, 'SIMULATED_VALUE']
    }),
  )
}

function selectCapabilityMock(mock: CapabilityMock) {
  capabilityInvokeForm.capability_id = mock.id
  capabilityInvokeForm.expected_status = mock.default_status
  capabilityInvokeForm.latency_ms = mock.default_latency_ms
  capabilityInvokeForm.request_payload_text = JSON.stringify(capabilityPayloadExample(mock), null, 2)
  const matchingInstance = dashboard.value.instances.find((item) => item.scenario_id === mock.scenario_id)
  if (matchingInstance) capabilityInvokeForm.instance_id = matchingInstance.id
}

function parseJsonObject(value: string, label: string) {
  try {
    const parsed = JSON.parse(value || '{}')
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error('not-object')
    return parsed as Record<string, unknown>
  } catch {
    ElMessage.warning(`${label}必须是合法的 JSON 对象`)
    return null
  }
}

function parseJsonArray(value: string, label: string) {
  try {
    const parsed = JSON.parse(value || '[]')
    if (!Array.isArray(parsed)) throw new Error('not-array')
    return parsed as unknown[]
  } catch {
    ElMessage.warning(`${label}必须是合法的 JSON 数组`)
    return null
  }
}

async function invokeSelectedCapability() {
  if (!capabilityInvokeForm.instance_id || !selectedCapabilityMock.value) {
    ElMessage.warning('请先选择预演实例和演练能力')
    return
  }
  const requestPayload = parseJsonObject(capabilityInvokeForm.request_payload_text, '请求参数')
  if (!requestPayload) return
  const response = await rehearsalApi.invokeCapability(
    capabilityInvokeForm.instance_id,
    {
      request_id: requestId('capability-call'),
      capability_id: selectedCapabilityMock.value.id,
      request_payload: requestPayload,
      expected_status: capabilityInvokeForm.expected_status,
      latency_ms: capabilityInvokeForm.latency_ms,
      warroom_group: capabilityInvokeForm.warroom_group,
    },
    capabilityInvoking,
  )
  selectedCapabilityCall.value = response.data.call
  capabilityCallDrawerVisible.value = true
  ElMessage.success(response.data.call.status === 'SUCCEEDED' ? '调用成功' : '异常结果已留痕')
  await Promise.all([loadDashboard(), loadCapabilityCalls(1), loadSimulationRecords(1)])
}

function openCapabilityMockDrawer() {
  Object.assign(capabilityMockForm, {
    scenario_id: dashboard.value.scenarios[0]?.id || '',
    code: '',
    name: '',
    description: '',
    kind: 'API',
    method: 'POST',
    endpoint: '/sandbox/',
    default_latency_ms: 120,
    request_schema_text: '{\n  "required": [],\n  "properties": {}\n}',
    response_template_text: '{\n  "success": true,\n  "message": "调用完成"\n}',
    failure_template_text: '{\n  "code": "SIMULATION_FAILED",\n  "message": "调用失败"\n}',
  })
  capabilityMockDrawerVisible.value = true
}

async function submitCapabilityMock() {
  if (!capabilityMockForm.scenario_id || !capabilityMockForm.code.trim() || !capabilityMockForm.name.trim()) {
    ElMessage.warning('请完整填写所属场景、能力编号和名称')
    return
  }
  if (!capabilityMockForm.endpoint.trim()) {
    ElMessage.warning('请填写调用地址')
    return
  }
  const requestSchema = parseJsonObject(capabilityMockForm.request_schema_text, '请求 Schema')
  const responseTemplate = parseJsonObject(capabilityMockForm.response_template_text, '成功响应')
  const failureTemplate = parseJsonObject(capabilityMockForm.failure_template_text, '失败响应')
  if (!requestSchema || !responseTemplate || !failureTemplate) return
  const response = await rehearsalApi.createCapabilityMock(
    {
      scenario_id: capabilityMockForm.scenario_id,
      code: capabilityMockForm.code.trim().toUpperCase(),
      name: capabilityMockForm.name.trim(),
      description: capabilityMockForm.description.trim(),
      kind: capabilityMockForm.kind,
      method: capabilityMockForm.method,
      endpoint: capabilityMockForm.endpoint.trim(),
      request_schema: requestSchema,
      response_template: responseTemplate,
      failure_template: failureTemplate,
      default_latency_ms: capabilityMockForm.default_latency_ms,
    },
    capabilityMockCreating,
  )
  capabilityMockDrawerVisible.value = false
  await loadDashboard()
  selectCapabilityMock(response.data)
  ElMessage.success(`隔离能力 V${response.data.version} 已保存`)
}

async function openCapabilityCall(call: CapabilityCall) {
  capabilityCallDrawerVisible.value = true
  capabilityCallDetailLoading.value = true
  try {
    const response = await rehearsalApi.getCapabilityCall(call.id)
    selectedCapabilityCall.value = response.data
  } finally {
    capabilityCallDetailLoading.value = false
  }
}

async function replaySelectedCapability(expectedStatus: CapabilityCallStatus) {
  if (!selectedCapabilityCall.value) return
  const response = await rehearsalApi.replayCapabilityCall(
    selectedCapabilityCall.value.id,
    {
      request_id: requestId('capability-replay'),
      expected_status: expectedStatus,
      latency_ms: expectedStatus === 'TIMEOUT' ? 3000 : selectedCapabilityCall.value.latency_ms,
      warroom_group: selectedCapabilityCall.value.warroom_group,
    },
    capabilityReplaying,
  )
  selectedCapabilityCall.value = response.data.call
  ElMessage.success('重放记录已生成')
  await Promise.all([loadDashboard(), loadCapabilityCalls(1), loadSimulationRecords(1)])
}

function selectFaultConfiguration(configuration: FaultConfiguration) {
  faultConfigurationPreviewId.value = configuration.id
  const matchingInstance = dashboard.value.instances.find(
    (item) =>
      item.scenario_id === configuration.scenario_id &&
      !['COMPLETED', 'CANCELLED', 'FAILED'].includes(item.status),
  )
  faultConfigurationApplyForm.instance_id = matchingInstance?.id || ''
}

function resetFaultConfigurationFilters() {
  Object.assign(faultConfigurationFilters, {
    page: 1,
    page_size: 10,
    scenario_id: '',
    status: '',
    bound: '',
    keyword: '',
  })
  loadFaultConfigurations(1)
}

function openFaultConfigurationForm() {
  faultConfigurationForm.scenario_id = dashboard.value.scenarios[0]?.id || ''
  faultConfigurationForm.code = 'NETWORK-FAULT-CONFIG'
  faultConfigurationForm.name = ''
  faultConfigurationForm.description = ''
  faultConfigurationFormDrawerVisible.value = true
}

async function submitFaultConfiguration() {
  if (
    !faultConfigurationForm.scenario_id ||
    !faultConfigurationForm.code.trim() ||
    !faultConfigurationForm.name.trim()
  ) {
    ElMessage.warning('请完整填写所属场景、配置编号和名称')
    return
  }
  const alertRules = parseJsonArray(faultConfigurationForm.alert_rules_text, '告警规则')
  const timeoutPolicy = parseJsonObject(faultConfigurationForm.timeout_policy_text, '超时策略')
  const activeWindow = parseJsonObject(faultConfigurationForm.active_window_text, '运行时段')
  const topologySnapshot = parseJsonObject(
    faultConfigurationForm.topology_snapshot_text,
    '拓扑快照',
  )
  const emergencyPlan = parseJsonObject(faultConfigurationForm.emergency_plan_text, '应急预案')
  if (!alertRules || !timeoutPolicy || !activeWindow || !topologySnapshot || !emergencyPlan) return
  const response = await rehearsalApi.createFaultConfiguration(
    {
      request_id: requestId('fault-configuration'),
      scenario_id: faultConfigurationForm.scenario_id,
      code: faultConfigurationForm.code.trim().toUpperCase(),
      name: faultConfigurationForm.name.trim(),
      description: faultConfigurationForm.description.trim(),
      alert_rules: alertRules as FaultAlertRule[],
      timeout_policy: timeoutPolicy as FaultConfiguration['timeout_policy'],
      active_window: activeWindow as FaultConfiguration['active_window'],
      topology_snapshot: topologySnapshot as FaultConfiguration['topology_snapshot'],
      emergency_plan: emergencyPlan as FaultConfiguration['emergency_plan'],
    },
    faultConfigurationCreating,
  )
  faultConfigurationFormDrawerVisible.value = false
  ElMessage.success(
    response.data.configuration.status === 'READY'
      ? '故障配置已校验并可应用'
      : '配置已保存为待校验版本',
  )
  await Promise.all([loadDashboard(), loadFaultConfigurations(1)])
  await openFaultConfiguration(response.data.configuration)
}

async function cloneFaultConfiguration(configuration: FaultConfiguration) {
  const response = await rehearsalApi.cloneFaultConfiguration(
    configuration.id,
    {
      request_id: requestId('fault-configuration-clone'),
      name: `${configuration.name} V${configuration.version + 1}`,
      note: '从控制台克隆配置版本',
    },
    faultConfigurationOperating,
  )
  ElMessage.success(`已生成 V${response.data.configuration.version} 配置版本`)
  await Promise.all([loadDashboard(), loadFaultConfigurations(1)])
  await openFaultConfiguration(response.data.configuration)
}

async function validateFaultConfiguration(configuration: FaultConfiguration) {
  const response = await rehearsalApi.validateFaultConfiguration(
    configuration.id,
    '控制台手动校验',
    faultConfigurationOperating,
  )
  ElMessage.success(
    response.data.configuration.status === 'READY' ? '5 项配置校验通过' : '配置仍有校验问题',
  )
  await Promise.all([loadDashboard(), loadFaultConfigurations(faultConfigurationPage.value.page)])
  selectedFaultConfiguration.value = response.data.configuration
}

async function archiveFaultConfiguration(configuration: FaultConfiguration) {
  await ElMessageBox.confirm(`确认归档 ${configuration.name} V${configuration.version}？`, '归档配置', {
    type: 'warning',
  })
  const response = await rehearsalApi.archiveFaultConfiguration(
    configuration.id,
    '控制台归档',
    faultConfigurationOperating,
  )
  selectedFaultConfiguration.value = response.data.configuration
  ElMessage.success('故障配置已归档')
  await Promise.all([loadDashboard(), loadFaultConfigurations(faultConfigurationPage.value.page)])
}

async function applySelectedFaultConfiguration() {
  const configuration = faultConfigurationPreview.value
  if (!configuration || !faultConfigurationApplyForm.instance_id) {
    ElMessage.warning('请选择可应用配置和预演实例')
    return
  }
  const response = await rehearsalApi.applyFaultConfiguration(
    faultConfigurationApplyForm.instance_id,
    {
      request_id: requestId('fault-configuration-apply'),
      configuration_id: configuration.id,
      note: faultConfigurationApplyForm.note.trim(),
    },
    faultConfigurationOperating,
  )
  ElMessage.success(response.data.created ? '配置快照已绑定到预演实例' : '已返回幂等绑定结果')
  await Promise.all([loadDashboard(), loadFaultConfigurations(faultConfigurationPage.value.page)])
  if (selectedInstance.value?.id === faultConfigurationApplyForm.instance_id) {
    await refreshSelectedInstance()
  }
}

async function openFaultConfiguration(configuration: FaultConfiguration) {
  faultConfigurationDrawerVisible.value = true
  faultConfigurationDetailLoading.value = true
  try {
    const response = await rehearsalApi.getFaultConfiguration(configuration.id)
    selectedFaultConfiguration.value = response.data
    selectFaultConfiguration(response.data)
  } finally {
    faultConfigurationDetailLoading.value = false
  }
}

function stopSceneReplayPlayback() {
  if (sceneReplayTimer) clearInterval(sceneReplayTimer)
  sceneReplayTimer = null
  sceneReplayPlaying.value = false
}

function moveReplayCursor(delta: number) {
  const length = selectedSceneReplay.value?.traffic_frames?.length || 0
  if (!length) return
  sceneReplayCursor.value = (sceneReplayCursor.value + delta + length) % length
  activeReplayNodeId.value = currentSceneReplayFrame.value?.target_node || ''
}

function toggleSceneReplayPlayback() {
  if (sceneReplayPlaying.value) {
    stopSceneReplayPlayback()
    return
  }
  if (!(selectedSceneReplay.value?.traffic_frames?.length || 0)) return
  sceneReplayPlaying.value = true
  sceneReplayTimer = setInterval(() => moveReplayCursor(1), 1100)
}

async function selectSceneReplay(replay: SceneReplay) {
  stopSceneReplayPlayback()
  sceneReplayDetailLoading.value = true
  try {
    const response = await rehearsalApi.getSceneReplay(replay.id)
    selectedSceneReplay.value = response.data
    sceneReplayCursor.value = 0
    activeReplayNodeId.value = response.data.traffic_frames?.[0]?.target_node
      || response.data.node_traces?.[0]?.node_id
      || ''
  } finally {
    sceneReplayDetailLoading.value = false
  }
}

async function openSceneReplay(replay: SceneReplay) {
  sceneReplayDrawerVisible.value = true
  if (selectedSceneReplay.value?.id !== replay.id || !selectedSceneReplay.value.traffic_frames) {
    await selectSceneReplay(replay)
  }
}

function syncSceneReplayRun() {
  if (!availableSceneReplayRuns.value.some((item) => item.id === sceneReplayForm.scene_run_id)) {
    sceneReplayForm.scene_run_id = null
  }
}

function openSceneReplayCreate() {
  const instance = selectedInstance.value?.fault_configuration_id
    ? selectedInstance.value
    : sceneReplayInstances.value[0]
  sceneReplayForm.instance_id = instance?.id || ''
  sceneReplayForm.scene_run_id = null
  sceneReplayForm.name = instance ? `${instance.name} · 场景动态回溯` : ''
  sceneReplayForm.description = ''
  sceneReplayForm.window_start = null
  sceneReplayForm.window_end = null
  syncSceneReplayRun()
  sceneReplayCreateDrawerVisible.value = true
}

async function submitSceneReplay() {
  if (!sceneReplayForm.instance_id) {
    ElMessage.warning('请先为预演实例应用故障配置')
    return
  }
  if (
    sceneReplayForm.window_start
    && sceneReplayForm.window_end
    && new Date(sceneReplayForm.window_start).getTime() > new Date(sceneReplayForm.window_end).getTime()
  ) {
    ElMessage.warning('回放开始时间不能晚于结束时间')
    return
  }
  const response = await rehearsalApi.createSceneReplay(
    sceneReplayForm.instance_id,
    {
      request_id: requestId('scene-replay'),
      name: sceneReplayForm.name.trim() || undefined,
      description: sceneReplayForm.description.trim() || undefined,
      scene_run_id: sceneReplayForm.scene_run_id || null,
      window_start: sceneReplayForm.window_start,
      window_end: sceneReplayForm.window_end,
    },
    sceneReplayCreating,
  )
  sceneReplayCreateDrawerVisible.value = false
  ElMessage.success(response.data.created ? '场景动态回溯镜像已生成' : '已返回幂等回放镜像')
  await Promise.all([loadDashboard(), loadSceneReplays(1)])
  if (selectedInstance.value?.id === sceneReplayForm.instance_id) await refreshSelectedInstance()
  await selectSceneReplay(response.data.replay)
  sceneReplayDrawerVisible.value = true
}

function resetSceneReplayFilters() {
  Object.assign(sceneReplayFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    scene_run_id: '',
    status: '',
    node_id: '',
    keyword: '',
  })
  loadSceneReplays(1)
}

function applyFaultReportTemplate(templateId: string) {
  const template = dashboard.value.fault_report_templates.find((item) => item.id === templateId)
  if (!template) return
  faultReportForm.template_id = template.id
  faultReportForm.level = template.default_level
}

function syncFaultReportForm() {
  if (!availableFaultReportTemplates.value.some((item) => item.id === faultReportForm.template_id)) {
    applyFaultReportTemplate(availableFaultReportTemplates.value[0]?.id || '')
  }
  if (!availableFaultReportSceneRuns.value.some((item) => item.id === faultReportForm.scene_run_id)) {
    faultReportForm.scene_run_id = null
  }
}

function openFaultReportCreate() {
  const instance = selectedInstance.value?.fault_configuration_id
    ? selectedInstance.value
    : faultReportInstances.value[0]
  faultReportForm.instance_id = instance?.id || ''
  faultReportForm.template_id = ''
  faultReportForm.scene_run_id = null
  faultReportForm.title = instance ? `${instance.name} · 故障上报` : ''
  faultReportForm.description = ''
  faultReportForm.impact_scope = ''
  faultReportForm.attachment_reference_id = ''
  faultReportForm.attachment_file_name = ''
  syncFaultReportForm()
  faultReportCreateDrawerVisible.value = true
}

async function submitFaultReport() {
  if (!faultReportForm.instance_id || !faultReportForm.template_id) {
    ElMessage.warning('请选择已绑定故障配置的实例和上报模板')
    return
  }
  if (!faultReportForm.title.trim() || !faultReportForm.description.trim() || !faultReportForm.impact_scope.trim()) {
    ElMessage.warning('请完整填写故障标题、描述和影响范围')
    return
  }
  const attachments = faultReportForm.attachment_reference_id.trim()
    ? [{
        reference_id: faultReportForm.attachment_reference_id.trim(),
        file_name: faultReportForm.attachment_file_name.trim() || 'evidence.txt',
        content_type: 'text/plain',
        file_size: 0,
        note: '首次上报证据引用',
      }]
    : []
  const response = await rehearsalApi.createFaultReport(
    faultReportForm.instance_id,
    {
      request_id: requestId('fault-report'),
      template_id: faultReportForm.template_id,
      scene_run_id: faultReportForm.scene_run_id,
      title: faultReportForm.title.trim(),
      description: faultReportForm.description.trim(),
      impact_scope: faultReportForm.impact_scope.trim(),
      level: faultReportForm.level,
      occurred_at: new Date().toISOString(),
      attachments,
    },
    faultReportCreating,
  )
  faultReportCreateDrawerVisible.value = false
  ElMessage.success(response.data.created ? '故障上报草稿已创建' : '已返回幂等上报记录')
  await Promise.all([loadDashboard(), loadFaultReports(1), loadSimulationRecords(1)])
  await openFaultReport(response.data.report)
}

async function selectFaultReport(report: FaultReport) {
  faultReportDetailLoading.value = true
  try {
    const response = await rehearsalApi.getFaultReport(report.id)
    selectedFaultReport.value = response.data
    if (!response.data.allowed_actions.includes(faultReportActionForm.action as FaultReportAction)) {
      faultReportActionForm.action = response.data.allowed_actions[0] || ''
    }
  } finally {
    faultReportDetailLoading.value = false
  }
}

async function openFaultReport(report: FaultReport) {
  faultReportDrawerVisible.value = true
  await selectFaultReport(report)
}

function openFaultReportAction(action: FaultReportAction) {
  faultReportDrawerVisible.value = true
  faultReportActionForm.action = action
  faultReportActionForm.note = ''
  faultReportActionForm.level = 'LEVEL_1'
  faultReportActionForm.attachment_reference_id = ''
  faultReportActionForm.attachment_file_name = ''
}

async function operateSelectedFaultReport(action: FaultReportAction) {
  if (!selectedFaultReport.value) return
  const noteRequired = ['STAGE_ADVANCED', 'ESCALATED', 'RECOVERED', 'CLOSED'].includes(action)
  if (noteRequired && !faultReportActionForm.note.trim()) {
    ElMessage.warning('该操作必须填写处置说明')
    return
  }
  if (action === 'ESCALATED' && faultReportActionForm.level === selectedFaultReport.value.level) {
    ElMessage.warning('请选择高于当前故障的等级')
    return
  }
  if (action === 'ATTACHMENT_ADDED' && !faultReportActionForm.attachment_reference_id.trim()) {
    ElMessage.warning('请填写证据引用编号')
    return
  }
  const confirmed = await ElMessageBox.confirm(
    `确认${faultReportActionLabel(action)}“${selectedFaultReport.value.title}”？`,
    '故障上报操作确认',
    { type: action === 'ESCALATED' ? 'warning' : 'info', confirmButtonText: '确认执行', cancelButtonText: '返回' },
  ).then(() => true).catch(() => false)
  if (!confirmed) return
  const attachments = action === 'ATTACHMENT_ADDED'
    ? [{
        reference_id: faultReportActionForm.attachment_reference_id.trim(),
        file_name: faultReportActionForm.attachment_file_name.trim() || 'evidence.txt',
        content_type: 'text/plain',
        file_size: 0,
        note: faultReportActionForm.note.trim(),
      }]
    : undefined
  const response = await rehearsalApi.operateFaultReport(
    selectedFaultReport.value.id,
    {
      action,
      note: faultReportActionForm.note.trim(),
      level: action === 'ESCALATED' ? faultReportActionForm.level : undefined,
      attachments,
      event_at: new Date().toISOString(),
    },
    faultReportOperating,
  )
  selectedFaultReport.value = response.data.report
  faultReportActionForm.note = ''
  faultReportActionForm.attachment_reference_id = ''
  faultReportActionForm.attachment_file_name = ''
  faultReportActionForm.action = response.data.report.allowed_actions[0] || ''
  ElMessage.success(`${faultReportActionLabel(action)}成功`)
  await Promise.all([loadDashboard(), loadFaultReports(faultReportPage.value.page), loadSimulationRecords(1)])
  await selectFaultReport(response.data.report)
}

function submitFaultReportAction() {
  if (!faultReportActionForm.action) {
    ElMessage.warning('请选择上报操作')
    return
  }
  return operateSelectedFaultReport(faultReportActionForm.action)
}

function resetFaultReportFilters() {
  Object.assign(faultReportFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    template_id: '',
    status: '',
    level: '',
    overdue: '',
    keyword: '',
  })
  loadFaultReports(1)
}

function resetAuxiliarySimulationFilters() {
  Object.assign(auxiliarySimulationFilters, {
    page: 1,
    page_size: 10,
    instance_id: '',
    status: '',
    seed: '',
    keyword: '',
  })
  loadAuxiliarySimulations(1)
}

function openAuxiliarySimulationCreate() {
  auxiliarySimulationForm.instance_id = dashboard.value.instances[0]?.id || ''
  auxiliarySimulationForm.name = ''
  auxiliarySimulationForm.seed = Math.floor(Date.now() % 4294967295)
  auxiliarySimulationForm.duration_minutes = 60
  auxiliarySimulationForm.factors = dashboard.value.random_factor_catalog.map((item, index) => ({
    ...item,
    enabled: index === 0 || item.code === 'TRAFFIC_PEAK',
  }))
  auxiliarySimulationCreateDrawerVisible.value = true
}

async function submitAuxiliarySimulation() {
  if (!auxiliarySimulationForm.instance_id) {
    ElMessage.warning('请选择预演实例')
    return
  }
  const factors = auxiliarySimulationForm.factors
    .filter((item) => item.enabled)
    .map(({ enabled: _enabled, ...item }) => item)
  if (!factors.length) {
    ElMessage.warning('至少启用一个随机因子')
    return
  }
  if (factors.some((item) => item.max_value <= item.min_value)) {
    ElMessage.warning('随机因子的最大值必须大于最小值')
    return
  }
  const response = await rehearsalApi.createAuxiliarySimulation(
    auxiliarySimulationForm.instance_id,
    {
      request_id: requestId('ui-auxiliary-simulation'),
      name: auxiliarySimulationForm.name.trim(),
      seed: auxiliarySimulationForm.seed,
      duration_minutes: auxiliarySimulationForm.duration_minutes,
      factors,
    },
    auxiliarySimulationCreating,
  )
  auxiliarySimulationCreateDrawerVisible.value = false
  ElMessage.success(response.data.created ? '随机因子演练已完成' : '已返回相同幂等批次')
  await Promise.all([loadDashboard(), loadAuxiliarySimulations(1), loadSimulationRecords(1)])
  await openAuxiliarySimulation(response.data.simulation)
}

async function selectAuxiliarySimulation(simulation: AuxiliarySimulation) {
  auxiliarySimulationDetailLoading.value = true
  try {
    const response = await rehearsalApi.getAuxiliarySimulation(simulation.id)
    selectedAuxiliarySimulation.value = response.data
  } finally {
    auxiliarySimulationDetailLoading.value = false
  }
}

async function openAuxiliarySimulation(simulation: AuxiliarySimulation) {
  auxiliarySimulationDrawerVisible.value = true
  await selectAuxiliarySimulation(simulation)
}

function quickExportAuxiliary(simulation: AuxiliarySimulation, format: AuxiliaryReportFormat) {
  return rehearsalApi.exportAuxiliarySimulation(
    simulation,
    format,
    format === 'pdf' ? 'summary' : 'full',
    auxiliarySimulationExporting,
  )
}

function exportSelectedAuxiliary() {
  if (!selectedAuxiliarySimulation.value) return
  return rehearsalApi.exportAuxiliarySimulation(
    selectedAuxiliarySimulation.value,
    auxiliaryExportForm.export_format,
    auxiliaryExportForm.report_level,
    auxiliarySimulationExporting,
  )
}

function resetSceneLibraryForm(mode: 'create' | 'clone', source?: SceneLibrary) {
  const script = source
    ? dashboard.value.scene_scripts.find((item) => item.id === source.script_id)
    : dashboard.value.scene_scripts[0]
  sceneLibraryForm.mode = mode
  sceneLibraryForm.source_id = source?.id || ''
  sceneLibraryForm.scenario_id = source?.scenario_id || script?.scenario_id || dashboard.value.scenarios[0]?.id || ''
  sceneLibraryForm.script_id = source?.script_id || script?.id || ''
  sceneLibraryForm.code = mode === 'create' ? '' : source?.code || ''
  sceneLibraryForm.name = mode === 'create' ? '' : `${source?.name || '场景库'} 副本`
  sceneLibraryForm.description = source?.description || ''
  sceneLibraryForm.default_instance_id = source?.default_instance_id || null
  sceneLibraryForm.process_template_id = source?.process_template_id || null
  sceneLibraryForm.data_model_id = source?.data_model_id || null
  sceneLibraryForm.visibility = source?.visibility || 'WORKSPACE'
  sceneLibraryForm.permission_roles = (source?.permission_roles?.length ? source.permission_roles : ['WORKSPACE_MANAGE']).join(',')
  sceneLibraryForm.note = ''
}

function openSceneLibraryCreate(script?: SceneScript) {
  resetSceneLibraryForm('create')
  if (script) {
    sceneLibraryForm.scenario_id = script.scenario_id
    sceneLibraryForm.script_id = script.id
    sceneLibraryForm.code = script.code.replace(/SCENE/gi, 'LIBRARY').slice(0, 64)
    sceneLibraryForm.name = `${script.name}库`
  }
  sceneLibraryFormDrawerVisible.value = true
}

function openSceneLibraryClone(library: SceneLibrary) {
  resetSceneLibraryForm('clone', library)
  sceneLibraryFormDrawerVisible.value = true
}

function sceneLibraryRoles() {
  return sceneLibraryForm.permission_roles
    .split(',')
    .map((item) => item.trim().toUpperCase())
    .filter(Boolean)
}

function validateSceneLibraryForm() {
  if (!sceneLibraryForm.scenario_id || !sceneLibraryForm.script_id || !sceneLibraryForm.name.trim()) {
    return '请完整填写所属场景、场景剧本和场景库名称'
  }
  if (sceneLibraryForm.mode === 'create') {
    sceneLibraryForm.code = sceneLibraryForm.code.trim().toUpperCase()
    if (!/^[A-Z][A-Z0-9_-]{1,63}$/.test(sceneLibraryForm.code)) {
      return '场景库编号需以字母开头，且只包含大写字母、数字、下划线或短横线'
    }
  }
  return ''
}

async function submitSceneLibraryForm() {
  const validationError = validateSceneLibraryForm()
  if (validationError) {
    ElMessage.warning(validationError)
    return
  }
  const common = {
    request_id: requestId(sceneLibraryForm.mode === 'create' ? 'ui-scene-library' : 'ui-scene-library-clone'),
    name: sceneLibraryForm.name.trim(),
    description: sceneLibraryForm.description.trim(),
    default_instance_id: sceneLibraryForm.default_instance_id || null,
    process_template_id: sceneLibraryForm.process_template_id || null,
    data_model_id: sceneLibraryForm.data_model_id || null,
    visibility: sceneLibraryForm.visibility,
    permission_roles: sceneLibraryRoles(),
    configuration: { source: 'ui', coarse_version: 'X24' },
  }
  const response =
    sceneLibraryForm.mode === 'create'
      ? await rehearsalApi.createSceneLibrary(
          {
            ...common,
            scenario_id: sceneLibraryForm.scenario_id,
            script_id: sceneLibraryForm.script_id,
            code: sceneLibraryForm.code,
          },
          sceneLibraryCreating,
        )
      : await rehearsalApi.cloneSceneLibrary(
          sceneLibraryForm.source_id,
          {
            ...common,
            note: sceneLibraryForm.note.trim(),
          },
          sceneLibraryCreating,
        )
  sceneLibraryFormDrawerVisible.value = false
  ElMessage.success(response.data.created ? '场景库版本已保存' : '已返回幂等场景库')
  await Promise.all([loadDashboard(), loadSceneLibraries(1)])
  if (selectedInstance.value) await refreshSelectedInstance()
  await openSceneLibrary(response.data.library)
}

async function openSceneLibrary(library: SceneLibrary) {
  sceneLibraryDrawerVisible.value = true
  sceneLibraryDetailLoading.value = true
  try {
    const response = await rehearsalApi.getSceneLibrary(library.id)
    selectedSceneLibrary.value = response.data
  } finally {
    sceneLibraryDetailLoading.value = false
  }
}

async function operateSceneLibrary(library: SceneLibrary, action: 'PUBLISHED' | 'ARCHIVED') {
  const label = action === 'ARCHIVED' ? '归档' : '发布'
  const confirmed = await ElMessageBox.confirm(`确认${label}“${library.name}” V${library.version}？`, '场景库状态确认', {
    type: action === 'ARCHIVED' ? 'warning' : 'info',
    confirmButtonText: `确认${label}`,
    cancelButtonText: '返回',
  })
    .then(() => true)
    .catch(() => false)
  if (!confirmed) return
  const response = await rehearsalApi.operateSceneLibrary(
    library.id,
    { action, note: `页面${label}` },
    sceneLibraryOperating,
  )
  ElMessage.success(`${label}成功`)
  await Promise.all([loadDashboard(), loadSceneLibraries(sceneLibraryPage.value.page)])
  if (selectedSceneLibrary.value?.id === library.id) selectedSceneLibrary.value = response.data.library
}

function openSceneLibraryRun(library: SceneLibrary) {
  sceneLibraryRunForm.library_id = library.id
  sceneLibraryRunForm.instance_id = library.default_instance_id || availableDataInstances.value[0]?.id || null
  sceneLibraryRunForm.name = ''
  sceneLibraryRunForm.include_latest_complaint_batch = true
  sceneLibraryRunForm.include_latest_data_batch = true
  sceneLibraryRunForm.include_latest_process_run = true
  selectedSceneLibrary.value = library
  sceneLibraryRunDrawerVisible.value = true
}

async function createSceneRunFromLibrary() {
  if (!sceneLibraryRunForm.library_id) return
  if (!sceneLibraryRunForm.instance_id) {
    ElMessage.warning('请选择要执行的预演实例')
    return
  }
  const response = await rehearsalApi.createSceneRunFromLibrary(
    sceneLibraryRunForm.library_id,
    {
      request_id: requestId('ui-scene-library-run'),
      instance_id: sceneLibraryRunForm.instance_id,
      name: sceneLibraryRunForm.name.trim() || undefined,
      include_latest_complaint_batch: sceneLibraryRunForm.include_latest_complaint_batch,
      include_latest_data_batch: sceneLibraryRunForm.include_latest_data_batch,
      include_latest_process_run: sceneLibraryRunForm.include_latest_process_run,
    },
    sceneLibraryRunning,
  )
  sceneLibraryRunDrawerVisible.value = false
  ElMessage.success(response.data.created ? '已从场景库创建执行' : '已返回幂等场景执行')
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadSceneLibraries(sceneLibraryPage.value.page), loadSceneRuns(1)])
  if (selectedInstance.value?.id === response.data.run.instance_id) await refreshSelectedInstance()
  await openSceneRun(response.data.run)
}

async function openInstance(instance: RehearsalInstance) {
  instanceDrawerVisible.value = true
  detailLoading.value = true
  try {
    const response = await rehearsalApi.getInstance(instance.id)
    selectedInstance.value = response.data
    filters.instance_id = instance.id
    generateForm.start_at = new Date().toISOString()
    await loadComplaints(1)
  } finally {
    detailLoading.value = false
  }
}

async function refreshSelectedInstance() {
  if (!selectedInstance.value) return
  const response = await rehearsalApi.getInstance(selectedInstance.value.id)
  selectedInstance.value = response.data
  await refreshAll()
}

async function createProcessRun() {
  if (!selectedInstance.value || !processForm.template_id) {
    ElMessage.warning('请先选择处置流程模板')
    return
  }
  const response = await rehearsalApi.createProcessRun(
    selectedInstance.value.id,
    {
      request_id: requestId('ui-process'),
      template_id: processForm.template_id,
      name: processForm.name || undefined,
      auto_advance: processForm.auto_advance,
    },
    processCreating,
  )
  ElMessage.success(response.data.created ? '处置流程已生成' : '已返回幂等流程')
  processForm.name = ''
  await refreshSelectedInstance()
  await openProcessRun(response.data.run)
}

async function openProcessRun(run: ProcessRun) {
  processDrawerVisible.value = true
  processDetailLoading.value = true
  processOperateForm.note = ''
  processOperateForm.reason = ''
  try {
    const response = await rehearsalApi.getProcessRun(run.id)
    selectedProcess.value = response.data
  } finally {
    processDetailLoading.value = false
  }
}

async function operateProcess(action: ProcessRunAction) {
  if (!selectedProcess.value) return
  if (action === 'BLOCK' && !processOperateForm.reason.trim()) {
    ElMessage.warning('阻塞流程必须填写原因')
    return
  }
  if (action === 'FAIL' && !processOperateForm.reason.trim() && !processOperateForm.note.trim()) {
    ElMessage.warning('标记失败需要填写原因或说明')
    return
  }
  const labels: Record<ProcessRunAction, string> = {
    START: '启动流程',
    COMPLETE_STEP: '完成当前步骤',
    AUTO_ADVANCE: '自动推进一步',
    BLOCK: '阻塞当前步骤',
    RESUME: '恢复当前步骤',
    SKIP: '跳过当前步骤',
    FAIL: '标记流程失败',
    CANCEL: '取消流程',
  }
  const confirmed = await ElMessageBox.confirm(`确认${labels[action]}？`, '处置进度确认', {
    type: ['FAIL', 'CANCEL'].includes(action) ? 'warning' : 'info',
    confirmButtonText: '确认执行',
    cancelButtonText: '返回',
  })
    .then(() => true)
    .catch(() => false)
  if (!confirmed) return
  const response = await rehearsalApi.operateProcessRun(
    selectedProcess.value.id,
    {
      action,
      note: processOperateForm.note,
      reason: processOperateForm.reason,
    },
    processOperating,
  )
  selectedProcess.value = response.data.run
  processOperateForm.note = ''
  processOperateForm.reason = ''
  ElMessage.success(`${labels[action]}成功`)
  await refreshSelectedInstance()
}

async function generateData() {
  if (!selectedInstance.value || !generateForm.template_id || !generateForm.start_at) {
    ElMessage.warning('请先选择模板并填写序列起点')
    return
  }
  const response = await rehearsalApi.generateComplaints(
    selectedInstance.value.id,
    {
      request_id: requestId('ui-generate'),
      template_id: generateForm.template_id,
      count: generateForm.count,
      start_at: generateForm.start_at,
      interval_minutes: generateForm.interval_minutes,
    },
    generating,
  )
  ElMessage.success(`已生成 ${response.data.batch.valid_count} 条申告`)
  await refreshSelectedInstance()
}

async function uploadComplaintFile(options: UploadRequestOptions) {
  if (!selectedInstance.value) return
  const response = await rehearsalApi.importComplaints(
    selectedInstance.value.id,
    requestId('ui-import'),
    options.file,
    importing,
  )
  const batch = response.data.batch
  if (batch.invalid_count) {
    ElMessage.warning(`导入完成：${batch.valid_count} 条有效，${batch.invalid_count} 条异常`)
  } else {
    ElMessage.success(`导入完成：${batch.valid_count} 条全部通过`)
  }
  options.onSuccess?.(response)
  await refreshSelectedInstance()
}

async function operate(action: InstanceAction) {
  if (!selectedInstance.value) return
  const actionLabels: Record<InstanceAction, string> = {
    PREPARE: '完成数据准备',
    START: '启动预演',
    COMPLETE: '完成预演',
    CANCEL: '取消预演',
  }
  const confirmed = await ElMessageBox.confirm(
    `确认${actionLabels[action]}“${selectedInstance.value.name}”？`,
    '预演状态确认',
    {
      type: action === 'CANCEL' ? 'warning' : 'info',
      confirmButtonText: '确认',
      cancelButtonText: '返回',
    },
  )
    .then(() => true)
    .catch(() => false)
  if (!confirmed) return
  await rehearsalApi.operateInstance(
    selectedInstance.value.id,
    { action, note: `由预演控制台执行：${actionLabels[action]}` },
    operating,
  )
  ElMessage.success(`${actionLabels[action]}成功`)
  await refreshSelectedInstance()
}

function defaultSceneSteps(): SceneScriptStep[] {
  const source = dashboard.value.scene_scripts[0]?.steps
  return source?.length
    ? source.map((item) => ({ ...item }))
    : [
        {
          code: 'VERIFY_INJECTION',
          name: '校验注入数据',
          description: '核对所有注入数据的实例归属与完整性。',
          expected_result: '注入数据完整且可追溯。',
        },
      ]
}

function openSceneScriptCreate() {
  sceneScriptForm.scenario_id = dashboard.value.scenarios[0]?.id || ''
  sceneScriptForm.code = ''
  sceneScriptForm.name = ''
  sceneScriptForm.description = ''
  sceneScriptForm.steps = defaultSceneSteps()
  sceneScriptDrawerVisible.value = true
}

function addSceneScriptStep() {
  if (sceneScriptForm.steps.length >= 20) return
  const index = sceneScriptForm.steps.length + 1
  sceneScriptForm.steps.push({
    code: `STEP_${index}`,
    name: `预演步骤${index}`,
    description: '',
    expected_result: '',
  })
}

function removeSceneScriptStep(index: number) {
  if (sceneScriptForm.steps.length > 1) sceneScriptForm.steps.splice(index, 1)
}

async function createSceneScript() {
  if (!sceneScriptForm.scenario_id || !sceneScriptForm.code.trim() || !sceneScriptForm.name.trim()) {
    ElMessage.warning('请完整填写所属场景、剧本编号和名称')
    return
  }
  const seenCodes = new Set<string>()
  for (const [index, step] of sceneScriptForm.steps.entries()) {
    step.code = step.code.trim().toUpperCase()
    step.name = step.name.trim()
    if (!/^[A-Z][A-Z0-9_]{0,63}$/.test(step.code) || !step.name) {
      ElMessage.warning(`第 ${index + 1} 个步骤编号或名称不正确`)
      return
    }
    if (seenCodes.has(step.code)) {
      ElMessage.warning(`步骤编号 ${step.code} 重复`)
      return
    }
    seenCodes.add(step.code)
  }
  const response = await rehearsalApi.createSceneScript(
    {
      scenario_id: sceneScriptForm.scenario_id,
      code: sceneScriptForm.code.trim().toUpperCase(),
      name: sceneScriptForm.name.trim(),
      description: sceneScriptForm.description.trim(),
      steps: sceneScriptForm.steps.map((item) => ({ ...item })),
    },
    sceneScriptCreating,
  )
  sceneScriptDrawerVisible.value = false
  ElMessage.success(`剧本 ${response.data.name} V${response.data.version} 已保存`)
  await loadDashboard()
  sceneFilters.script_id = response.data.id
  sceneCreateForm.script_id = response.data.id
  await loadSceneRuns(1)
}

async function loadSceneSourceInstance(instanceId: string) {
  sceneCreateForm.complaint_batch_ids = []
  sceneCreateForm.data_batch_ids = []
  sceneCreateForm.process_run_ids = []
  sceneSourceInstance.value = undefined
  if (!instanceId) return
  const response = await rehearsalApi.getInstance(instanceId, sceneDetailLoading)
  sceneSourceInstance.value = response.data
  const firstScript = dashboard.value.scene_scripts.find(
    (item) => item.scenario_id === response.data.scenario_id,
  )
  if (!availableSceneScripts.value.some((item) => item.id === sceneCreateForm.script_id)) {
    sceneCreateForm.script_id = firstScript?.id || ''
  }
}

async function openSceneCreate(instance?: RehearsalInstance) {
  const target =
    instance && ['DRAFT', 'READY', 'RUNNING'].includes(instance.status)
      ? instance
      : availableDataInstances.value[0]
  sceneCreateForm.instance_id = target?.id || ''
  sceneCreateForm.script_id = ''
  sceneCreateForm.name = ''
  sceneCreateForm.complaint_batch_ids = []
  sceneCreateForm.data_batch_ids = []
  sceneCreateForm.process_run_ids = []
  sceneCreateDrawerVisible.value = true
  if (target) {
    await loadSceneSourceInstance(target.id)
    sceneCreateForm.complaint_batch_ids = (sceneSourceInstance.value?.batches || []).map(
      (item) => item.id,
    )
    sceneCreateForm.data_batch_ids = (sceneSourceInstance.value?.data_batches || []).map(
      (item) => item.id,
    )
    sceneCreateForm.process_run_ids = (sceneSourceInstance.value?.process_runs || []).map(
      (item) => item.id,
    )
  }
}

async function createSceneRun() {
  if (!sceneCreateForm.instance_id || !sceneCreateForm.script_id) {
    ElMessage.warning('请选择预演实例和场景剧本')
    return
  }
  if (!sceneInjectionCount.value) {
    ElMessage.warning('至少选择一个申告批次、趋势批次或处置流程')
    return
  }
  const response = await rehearsalApi.createSceneRun(
    sceneCreateForm.instance_id,
    {
      request_id: requestId('ui-scene'),
      script_id: sceneCreateForm.script_id,
      name: sceneCreateForm.name.trim() || undefined,
      complaint_batch_ids: [...sceneCreateForm.complaint_batch_ids],
      data_batch_ids: [...sceneCreateForm.data_batch_ids],
      process_run_ids: [...sceneCreateForm.process_run_ids],
    },
    sceneCreating,
  )
  sceneCreateDrawerVisible.value = false
  ElMessage.success(response.data.created ? '场景执行已创建' : '已返回幂等场景执行')
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadSceneRuns(1)])
  if (selectedInstance.value?.id === sceneCreateForm.instance_id) await refreshSelectedInstance()
  await openSceneRun(response.data.run)
}

async function openSceneRun(run: SceneRun) {
  sceneDrawerVisible.value = true
  sceneDetailLoading.value = true
  sceneOperateForm.note = ''
  sceneOperateForm.reason = ''
  try {
    const response = await rehearsalApi.getSceneRun(run.id)
    selectedScene.value = response.data
  } finally {
    sceneDetailLoading.value = false
  }
}

async function operateScene(action: SceneRunAction) {
  if (!selectedScene.value) return
  if (action === 'FAIL' && !sceneOperateForm.reason.trim()) {
    ElMessage.warning('标记场景失败时必须填写原因')
    return
  }
  const labels: Record<SceneRunAction, string> = {
    START: '启动场景',
    COMPLETE_STEP: '完成当前步骤',
    SKIP_STEP: '跳过当前步骤',
    FAIL: '标记场景失败',
    CANCEL: '取消场景',
  }
  const confirmed = await ElMessageBox.confirm(`确认${labels[action]}？`, '场景执行确认', {
    type: ['FAIL', 'CANCEL'].includes(action) ? 'warning' : 'info',
    confirmButtonText: '确认执行',
    cancelButtonText: '返回',
  })
    .then(() => true)
    .catch(() => false)
  if (!confirmed) return
  const response = await rehearsalApi.operateSceneRun(
    selectedScene.value.id,
    {
      action,
      note: sceneOperateForm.note.trim(),
      reason: sceneOperateForm.reason.trim(),
      output: sceneOperateForm.note.trim() ? { operator_note: sceneOperateForm.note.trim() } : {},
    },
    sceneOperating,
  )
  selectedScene.value = response.data.run
  sceneOperateForm.note = ''
  sceneOperateForm.reason = ''
  ElMessage.success(`${labels[action]}成功`)
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadSceneRuns(scenePage.value.page)])
  if (selectedInstance.value?.id === selectedScene.value.instance_id) await refreshSelectedInstance()
}

async function createSceneWorkOrder() {
  if (!selectedScene.value || !workOrderForm.title.trim()) {
    ElMessage.warning('请填写人工工单标题')
    return
  }
  const response = await rehearsalApi.createWorkOrder(
    selectedScene.value.id,
    {
      request_id: requestId('ui-work-order'),
      title: workOrderForm.title.trim(),
      description: workOrderForm.description.trim(),
      priority: workOrderForm.priority,
      assignee: workOrderForm.assignee.trim(),
    },
    workOrderCreating,
  )
  workOrderForm.title = ''
  workOrderForm.description = ''
  ElMessage.success(response.data.created ? '人工工单已创建' : '已返回幂等工单')
  await openSceneRun(selectedScene.value)
  await Promise.all([loadDashboard(), loadSimulationRecords(1)])
}

async function operateSceneWorkOrder(order: WorkOrder, action: WorkOrderAction) {
  let resolution = ''
  let assignee = ''
  if (action === 'ACCEPT') {
    const value = await ElMessageBox.prompt('填写责任人或班组（可沿用现有责任人）', '受理工单', {
      inputValue: order.assignee,
      confirmButtonText: '确认受理',
      cancelButtonText: '返回',
    })
      .then((result) => result.value)
      .catch(() => null)
    if (value === null) return
    assignee = value
  } else if (action === 'RESOLVE') {
    const value = await ElMessageBox.prompt('填写本次人工处理结果', '解决工单', {
      inputValidator: (input) => Boolean(input.trim()) || '处理结果不能为空',
      confirmButtonText: '确认解决',
      cancelButtonText: '返回',
    })
      .then((result) => result.value)
      .catch(() => null)
    if (value === null) return
    resolution = value
  } else {
    const label = action === 'CLOSE' ? '关闭' : '重新打开'
    const confirmed = await ElMessageBox.confirm(`确认${label}工单“${order.title}”？`, '工单状态确认', {
      type: action === 'REOPEN' ? 'warning' : 'info',
    })
      .then(() => true)
      .catch(() => false)
    if (!confirmed) return
  }
  await rehearsalApi.operateWorkOrder(order.id, { action, resolution, assignee }, sceneOperating)
  ElMessage.success('工单状态已更新')
  if (selectedScene.value) await openSceneRun(selectedScene.value)
  await Promise.all([loadDashboard(), loadSimulationRecords(1)])
}

function cloneAlertRules(rules: AlertRule[]) {
  return rules.map((item) => ({ ...item }))
}

function openAlertTemplateCreate() {
  const source = dashboard.value.alert_templates[0]
  alertTemplateForm.scenario_id = dashboard.value.scenarios[0]?.id || ''
  alertTemplateForm.code = ''
  alertTemplateForm.name = ''
  alertTemplateForm.description = ''
  alertTemplateForm.default_severity = source?.default_severity || 'HIGH'
  alertTemplateForm.rules = source?.rules.length
    ? cloneAlertRules(source.rules)
    : [
        {
          code: 'METRIC_HIGH',
          name: '指标超阈值',
          metric_code: 'METRIC_VALUE',
          metric_name: '指标值',
          operator: 'GT',
          threshold: 100,
          unit: '',
          resource_type: '网络设备',
        },
      ]
  alertTemplateDrawerVisible.value = true
}

function addAlertRule() {
  if (alertTemplateForm.rules.length >= 20) return
  const index = alertTemplateForm.rules.length + 1
  alertTemplateForm.rules.push({
    code: `ALERT_RULE_${index}`,
    name: `告警规则${index}`,
    metric_code: `METRIC_${index}`,
    metric_name: `预演指标${index}`,
    operator: 'GT',
    threshold: 100,
    unit: '',
    resource_type: '网络设备',
  })
}

function removeAlertRule(index: number) {
  if (alertTemplateForm.rules.length > 1) alertTemplateForm.rules.splice(index, 1)
}

async function createAlertTemplate() {
  if (!alertTemplateForm.scenario_id || !alertTemplateForm.code.trim() || !alertTemplateForm.name.trim()) {
    ElMessage.warning('请完整填写所属场景、模板编号和名称')
    return
  }
  const codes = new Set<string>()
  for (const [index, rule] of alertTemplateForm.rules.entries()) {
    rule.code = rule.code.trim().toUpperCase()
    rule.metric_code = rule.metric_code.trim().toUpperCase()
    rule.name = rule.name.trim()
    if (!/^[A-Z][A-Z0-9_]{0,63}$/.test(rule.code) || !/^[A-Z][A-Z0-9_]{0,63}$/.test(rule.metric_code) || !rule.name) {
      ElMessage.warning(`第 ${index + 1} 条规则编号、指标或名称不正确`)
      return
    }
    if (codes.has(rule.code)) {
      ElMessage.warning(`规则编号 ${rule.code} 重复`)
      return
    }
    codes.add(rule.code)
  }
  const response = await rehearsalApi.createAlertTemplate(
    {
      scenario_id: alertTemplateForm.scenario_id,
      code: alertTemplateForm.code.trim().toUpperCase(),
      name: alertTemplateForm.name.trim(),
      description: alertTemplateForm.description.trim(),
      default_severity: alertTemplateForm.default_severity,
      rules: cloneAlertRules(alertTemplateForm.rules),
    },
    alertTemplateCreating,
  )
  alertTemplateDrawerVisible.value = false
  ElMessage.success(`告警模板 ${response.data.name} V${response.data.version} 已保存`)
  await loadDashboard()
  alertFilters.template_id = response.data.id
  applyAlertTemplate(response.data.id)
  await loadAlerts(1)
}

function applyAlertRule(ruleCode: string) {
  const rule = selectedAlertTemplate.value?.rules.find((item) => item.code === ruleCode)
  if (!rule) return
  alertCreateForm.rule_code = rule.code
  alertCreateForm.title = rule.name
  alertCreateForm.threshold = rule.threshold
  alertCreateForm.metric_value = rule.threshold + Math.max(Math.abs(rule.threshold) * 0.2, 1)
}

function applyAlertTemplate(templateId: string) {
  const template = dashboard.value.alert_templates.find((item) => item.id === templateId)
  if (!template) return
  alertCreateForm.template_id = template.id
  alertCreateForm.severity = template.default_severity
  applyAlertRule(template.rules[0]?.code || '')
}

async function loadAlertSourceInstance(instanceId: string) {
  alertSourceInstance.value = undefined
  alertCreateForm.scene_run_id = ''
  alertCreateForm.data_batch_id = ''
  if (!instanceId) return
  const response = await rehearsalApi.getInstance(instanceId, alertDetailLoading)
  alertSourceInstance.value = response.data
  const template = dashboard.value.alert_templates.find(
    (item) => item.scenario_id === response.data.scenario_id,
  )
  if (!availableAlertTemplates.value.some((item) => item.id === alertCreateForm.template_id)) {
    applyAlertTemplate(template?.id || '')
  }
}

async function openAlertCreate(instance?: RehearsalInstance, scene?: SceneRun) {
  const target = scene
    ? dashboard.value.instances.find((item) => item.id === scene.instance_id)
    : instance && ['DRAFT', 'READY', 'RUNNING'].includes(instance.status)
      ? instance
      : availableDataInstances.value[0]
  alertCreateForm.instance_id = target?.id || ''
  alertCreateForm.title = ''
  alertCreateForm.description = ''
  alertCreateForm.resource_id = ''
  alertCreateForm.resource_name = ''
  alertCreateForm.source_system = '预演平台'
  alertCreateForm.occurred_at = new Date().toISOString()
  alertCreateDrawerVisible.value = true
  if (target) {
    await loadAlertSourceInstance(target.id)
    if (scene) alertCreateForm.scene_run_id = scene.id
    const metricBatch = alertSourceInstance.value?.data_batches?.find((item) => item.kind === 'METRIC')
    alertCreateForm.data_batch_id = metricBatch?.id || ''
    const template = availableAlertTemplates.value[0]
    if (template) applyAlertTemplate(template.id)
  }
}

async function createAlert() {
  if (!alertCreateForm.instance_id || !alertCreateForm.template_id || !alertCreateForm.rule_code) {
    ElMessage.warning('请选择预演实例、告警模板和阈值规则')
    return
  }
  if (new Date(alertCreateForm.occurred_at).getTime() > Date.now()) {
    ElMessage.warning('告警发生时间不能晚于当前时间')
    return
  }
  const response = await rehearsalApi.createAlert(
    alertCreateForm.instance_id,
    {
      request_id: requestId('ui-alert'),
      template_id: alertCreateForm.template_id,
      rule_code: alertCreateForm.rule_code,
      scene_run_id: alertCreateForm.scene_run_id || null,
      data_batch_id: alertCreateForm.data_batch_id || null,
      title: alertCreateForm.title.trim(),
      description: alertCreateForm.description.trim(),
      severity: alertCreateForm.severity,
      source_system: alertCreateForm.source_system.trim(),
      resource_id: alertCreateForm.resource_id.trim(),
      resource_name: alertCreateForm.resource_name.trim(),
      metric_value: alertCreateForm.metric_value,
      threshold: alertCreateForm.threshold,
      occurred_at: alertCreateForm.occurred_at,
      context: { capability: 'X22', source: 'rehearsal_console' },
    },
    alertCreating,
  )
  alertCreateDrawerVisible.value = false
  ElMessage.success(response.data.created ? '演练告警已配置' : '已返回幂等告警')
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadAlerts(1)])
  if (selectedInstance.value?.id === alertCreateForm.instance_id) await refreshSelectedInstance()
  if (selectedScene.value?.id === alertCreateForm.scene_run_id) await openSceneRun(selectedScene.value)
  await openAlert(response.data.alert)
}

async function openAlert(alert: RehearsalAlert) {
  alertDrawerVisible.value = true
  alertDetailLoading.value = true
  alertOperateForm.note = ''
  alertOperateForm.metric_value = alert.metric_value
  timelineKind.value = ''
  try {
    const [detailResponse, timelineResponse] = await Promise.all([
      rehearsalApi.getAlert(alert.id),
      rehearsalApi.getInstanceTimeline(alert.instance_id),
    ])
    selectedAlert.value = detailResponse.data
    alertTimeline.value = timelineResponse.data
    alertOperateForm.metric_value = detailResponse.data.metric_value
  } finally {
    alertDetailLoading.value = false
  }
}

async function operateAlert(action: AlertAction) {
  if (!selectedAlert.value) return
  const labels: Record<AlertAction, string> = {
    REPORT: '上报告警',
    ACKNOWLEDGE: '确认告警',
    RECOVER: '恢复告警',
  }
  const confirmed = await ElMessageBox.confirm(`确认${labels[action]}“${selectedAlert.value.title}”？`, '告警状态确认', {
    type: action === 'REPORT' ? 'warning' : 'info',
    confirmButtonText: '确认执行',
    cancelButtonText: '返回',
  })
    .then(() => true)
    .catch(() => false)
  if (!confirmed) return
  const response = await rehearsalApi.operateAlert(
    selectedAlert.value.id,
    {
      action,
      note: alertOperateForm.note.trim(),
      metric_value: alertOperateForm.metric_value,
      detail: { capability: 'X22' },
    },
    alertOperating,
  )
  selectedAlert.value = response.data.alert
  alertOperateForm.note = ''
  const timelineResponse = await rehearsalApi.getInstanceTimeline(response.data.alert.instance_id)
  alertTimeline.value = timelineResponse.data
  ElMessage.success(`${labels[action]}成功`)
  await Promise.all([loadDashboard(), loadSimulationRecords(1), loadAlerts(alertPage.value.page)])
  if (selectedScene.value?.id === response.data.alert.scene_run_id) await openSceneRun(selectedScene.value)
}

onMounted(() => {
  faultReportClockTimer = setInterval(() => {
    clockNow.value = Date.now()
  }, 1000)
  refreshAll()
})
onBeforeUnmount(() => {
  stopSceneReplayPlayback()
  if (faultReportClockTimer) clearInterval(faultReportClockTimer)
})
</script>

<style scoped lang="scss">
.rehearsal-page {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  overflow-anchor: none;
  padding: 22px;
  color: #17324a;
  background:
    linear-gradient(rgba(27, 70, 96, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(27, 70, 96, 0.035) 1px, transparent 1px), #f3f7f8;
  background-size: 24px 24px;
}

.command-hero {
  display: flex;
  justify-content: space-between;
  gap: 24px;
  align-items: flex-end;
  min-height: 184px;
  padding: 30px 34px;
  color: #f4fbff;
  background:
    radial-gradient(circle at 84% 12%, rgba(64, 210, 177, 0.22), transparent 31%),
    linear-gradient(128deg, #0c2536, #164a5c 68%, #176a69);
  border-radius: 12px 12px 28px 12px;
  box-shadow: 0 18px 40px rgba(11, 48, 65, 0.16);

  h1 {
    margin: 4px 0 12px;
    font-size: 34px;
    letter-spacing: -1px;
  }
}

.eyebrow {
  display: none;
}
.hero-copy {
  max-width: 660px;
  margin: 0;
  color: rgba(239, 250, 255, 0.74);
  line-height: 1.65;
}
.hero-actions {
  display: flex;
  flex-shrink: 0;
  gap: 10px;
}

.workspace-nav {
  position: sticky;
  top: 0;
  z-index: 8;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 4px;
  padding: 5px;
  margin: 14px 0;
  background: rgba(235, 242, 243, 0.94);
  border: 1px solid rgba(199, 215, 219, 0.94);
  border-radius: 10px;
  box-shadow: 0 6px 18px rgba(24, 65, 80, 0.07);
  backdrop-filter: blur(12px);
}

.workspace-nav button {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
  min-width: 0;
  padding: 10px 12px;
  color: #395763;
  text-align: left;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 7px;
  cursor: pointer;
  transition: 0.18s ease;
}

.workspace-nav button:hover {
  background: rgba(255, 255, 255, 0.72);
  border-color: #c6dadd;
}

.workspace-nav button.active {
  color: #f5fbfb;
  background: linear-gradient(118deg, #173b49, #176660);
  border-color: #245d62;
  box-shadow: 0 5px 14px rgba(20, 75, 80, 0.16);
}

.workspace-index {
  color: #71909a;
  font: 700 17px/1 'DIN Alternate', sans-serif;
}

.workspace-copy,
.workspace-copy strong,
.workspace-copy small {
  display: block;
  min-width: 0;
}

.workspace-copy strong {
  overflow: hidden;
  color: #203f4b;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-copy small {
  margin-top: 4px;
  overflow: hidden;
  color: #81949b;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.workspace-nav em {
  color: #80949b;
  font-size: 9px;
  font-style: normal;
  white-space: nowrap;
}

.workspace-nav button.active .workspace-index,
.workspace-nav button.active .workspace-copy strong {
  color: #fff;
}

.workspace-nav button.active .workspace-copy small,
.workspace-nav button.active em {
  color: rgba(233, 248, 247, 0.68);
}

.module-nav {
  position: sticky;
  top: 68px;
  z-index: 7;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 0;
  padding: 4px;
  margin: -2px 0 14px;
  background: rgba(255, 255, 255, 0.95);
  border: 1px solid #dce7e9;
  border-radius: 9px;
  box-shadow: 0 4px 14px rgba(32, 73, 91, 0.045);
  backdrop-filter: blur(10px);
}

.module-nav button {
  position: relative;
  display: grid;
  grid-template-columns: 1fr;
  gap: 3px;
  align-items: center;
  min-width: 0;
  padding: 10px 13px;
  color: #38545f;
  text-align: left;
  background: transparent;
  border: 0;
  border-radius: 6px;
  cursor: pointer;
  transition: 0.18s ease;
}

.module-nav button::after {
  position: absolute;
  right: 12px;
  bottom: 1px;
  left: 12px;
  height: 2px;
  content: '';
  background: transparent;
}

.module-nav button:hover {
  background: #f5f9f8;
}

.module-nav button.active {
  background: #edf7f4;
  box-shadow: inset 0 0 0 1px rgba(65, 145, 128, 0.18);
}

.module-nav button.active::after {
  background: #218a73;
}

.module-nav strong,
.module-nav small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.module-nav strong {
  color: #294955;
  font-size: 12px;
}

.module-nav small {
  color: #87999f;
  font-size: 9px;
}

.module-nav button.active strong {
  color: #18705f;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(148px, 1fr));
  gap: 12px;
  margin: 14px 0;
}

.metric-card,
.panel,
.workflow-strip {
  background: rgba(255, 255, 255, 0.96);
  border: 1px solid #dfeaed;
  box-shadow: 0 7px 22px rgba(32, 73, 91, 0.06);
}

.metric-card {
  position: relative;
  overflow: hidden;
  padding: 18px 20px;
  border-radius: 8px;

  &::before {
    content: '';
    position: absolute;
    inset: 0 auto 0 0;
    width: 3px;
    background: #24a087;
  }
  span {
    display: block;
    color: #607b89;
    font-size: 13px;
  }
  strong {
    display: block;
    margin: 7px 0 3px;
    color: #102f45;
    font:
      700 28px/1.1 'DIN Alternate',
      sans-serif;
  }
  small {
    color: #8b9da6;
  }
}

.workflow-strip,
.panel {
  border-radius: 10px;
}
.workflow-strip {
  padding: 20px;
  margin-bottom: 14px;
}
.section-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}
.section-heading.compact {
  margin-bottom: 14px;
}
.section-heading h2 {
  margin: 4px 0 0;
  color: #17364b;
  font-size: 18px;
}
.section-heading > span,
.drawer-heading > span {
  color: #8195a0;
  font-size: 12px;
}
.workflow-steps {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.workflow-steps.fourteen-steps {
  grid-template-columns: repeat(14, minmax(0, 1fr));
}
.workflow-step {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 8px 18px;
  border-left: 1px dashed #c7d7dc;
}
.workflow-step:first-child {
  border-left: 0;
  padding-left: 0;
}
.step-index {
  color: #9ab0b8;
  font:
    700 18px/1 'DIN Alternate',
    sans-serif;
}
.workflow-step strong,
.workflow-step small {
  display: block;
}
.workflow-step small {
  margin-top: 4px;
  color: #79909b;
}

.content-grid {
  display: grid;
  grid-template-columns: minmax(300px, 0.75fr) minmax(520px, 1.5fr);
  gap: 14px;
}
.panel {
  padding: 20px;
}
.template-list {
  display: grid;
  gap: 10px;
}
.template-card {
  display: flex;
  gap: 13px;
  width: 100%;
  padding: 14px;
  text-align: left;
  color: inherit;
  background: #f8fbfb;
  border: 1px solid #e1eaec;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.2s ease;
}
.template-card:hover {
  transform: translateY(-1px);
  border-color: #69b8a7;
  box-shadow: 0 8px 20px rgba(41, 125, 113, 0.09);
}
.template-symbol {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  color: white;
  font-weight: 800;
  background: #248b78;
  clip-path: polygon(0 0, 100% 0, 100% 72%, 72% 100%, 0 100%);
}
.template-symbol.enterprise {
  background: #d08532;
}
.template-main {
  min-width: 0;
  flex: 1;
}
.template-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
.template-main p {
  margin: 4px 0 10px;
  color: #81939d;
  font-size: 11px;
}
.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.tag-row span {
  padding: 2px 6px;
  color: #56717e;
  font-size: 11px;
  background: white;
  border: 1px solid #dce7e9;
}
.instance-link {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 3px;
  padding: 0;
  color: #17364b;
  text-align: left;
  background: none;
  border: 0;
  cursor: pointer;
}
.instance-link small {
  color: #80939c;
}

.process-panel {
  margin-top: 14px;
}
.process-heading {
  margin-bottom: 12px;
}
.process-summary {
  display: flex;
  align-items: center;
  gap: 14px;
  color: #66808c;
  font-size: 12px;
}
.process-summary b {
  margin-right: 3px;
  color: #17806f;
  font-size: 18px;
}
.process-summary .blocked b {
  color: #c57928;
}
.process-template-rail {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 12px;
}
.process-template-card {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  padding: 13px 15px;
  color: #1b4054;
  text-align: left;
  background: linear-gradient(120deg, #f7fbfa, #f3f7f8);
  border: 1px solid #dce8e9;
  border-radius: 7px;
  cursor: pointer;
  transition: 0.18s ease;
}
.process-template-card:hover,
.process-template-card.active {
  border-color: #4fae9a;
  box-shadow: inset 3px 0 #27927e;
}
.process-template-card span,
.process-template-card strong {
  display: block;
}
.process-template-card span,
.process-template-card small {
  color: #7a9099;
  font-size: 11px;
}
.process-template-card strong {
  margin-top: 4px;
}
.process-filter-bar {
  grid-template-columns: 1.2fr 1.2fr 0.8fr 1.2fr auto auto;
}
.progress-cell {
  display: grid;
  grid-template-columns: minmax(90px, 1fr) auto;
  align-items: center;
  gap: 7px;
}
.progress-cell span {
  color: #82959e;
  font-size: 11px;
}

.data-simulation-panel {
  margin-top: 14px;
  background:
    linear-gradient(115deg, rgba(31, 145, 125, 0.035), transparent 38%),
    rgba(255, 255, 255, 0.97);
}
.simulation-heading {
  margin-bottom: 12px;
}
.simulation-summary,
.trend-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.simulation-summary > span {
  color: #6f8792;
  font-size: 12px;
}
.simulation-summary b {
  margin-right: 3px;
  color: #157c6b;
  font-size: 18px;
}
.simulation-template-rail {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 12px;
}
.simulation-template-card {
  position: relative;
  padding: 15px 17px;
  overflow: hidden;
  color: #183b50;
  text-align: left;
  background: linear-gradient(125deg, #f5fbf9, #edf6f4);
  border: 1px solid #d7e8e4;
  border-radius: 8px;
  cursor: pointer;
  transition: 0.18s ease;
}
.simulation-template-card::after {
  position: absolute;
  top: -22px;
  right: -12px;
  width: 76px;
  height: 76px;
  content: '';
  border: 14px solid rgba(32, 143, 121, 0.08);
  border-radius: 50%;
}
.simulation-template-card.sentiment {
  background: linear-gradient(125deg, #fffaf2, #fbf2e4);
  border-color: #eee0c7;
}
.simulation-template-card.sentiment::after {
  border-color: rgba(197, 126, 38, 0.09);
}
.simulation-template-card:hover {
  transform: translateY(-1px);
  border-color: #55ad9a;
  box-shadow: 0 8px 20px rgba(39, 118, 103, 0.09);
}
.simulation-template-card > strong,
.simulation-template-card > p {
  display: block;
  max-width: calc(100% - 60px);
}
.simulation-template-card > strong {
  margin: 5px 0;
  font-size: 15px;
}
.simulation-template-card > p {
  min-height: 34px;
  margin: 0 0 9px;
  color: #708792;
  font-size: 12px;
  line-height: 1.45;
}
.simulation-template-code {
  color: #7d929c;
  font-size: 10px;
  letter-spacing: 0.5px;
}
.simulation-template-card > div {
  display: flex;
  gap: 6px;
}
.simulation-template-card > div span {
  padding: 2px 7px;
  color: #4e776e;
  font-size: 11px;
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(95, 151, 137, 0.2);
}
.data-filter-bar {
  grid-template-columns: 1.3fr 0.8fr 0.9fr 1.2fr auto auto;
}

.data-model-panel {
  margin-top: 14px;
  background:
    linear-gradient(115deg, rgba(31, 112, 145, 0.04), transparent 42%),
    rgba(255, 255, 255, 0.97);
}
.model-heading,
.model-summary {
  display: flex;
  align-items: center;
  gap: 12px;
}
.model-heading {
  justify-content: space-between;
}
.model-summary {
  flex-wrap: wrap;
  justify-content: flex-end;
}
.model-summary > span {
  color: #6f8792;
  font-size: 12px;
}
.model-summary b {
  margin-right: 3px;
  color: #176c87;
  font-size: 18px;
}
.model-summary .warning b {
  color: #bf7a24;
}
.model-flow-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 12px;
}
.model-flow-strip article {
  padding: 13px 14px;
  background: #f6fbfc;
  border: 1px solid #dbeaec;
  border-radius: 8px;
}
.model-flow-strip span,
.model-flow-strip strong,
.model-flow-strip small {
  display: block;
}
.model-flow-strip span {
  color: #7e99a5;
  font:
    700 16px/1 'DIN Alternate',
    sans-serif;
}
.model-flow-strip strong {
  margin: 6px 0 4px;
  color: #183b50;
  font-size: 14px;
}
.model-flow-strip small {
  color: #728894;
  line-height: 1.45;
}
.model-filter-bar {
  grid-template-columns: 1.2fr 0.9fr 0.8fr 1.2fr auto auto;
}
.data-model-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 13px;
}
.data-model-form-grid label,
.data-model-form-grid label > span {
  display: block;
}
.data-model-form-grid label > span {
  margin-bottom: 6px;
  color: #657b86;
  font-size: 12px;
}
.data-model-form-grid .wide-field {
  grid-column: 1 / -1;
}
.traceback-panel {
  margin-top: 14px;
  background:
    linear-gradient(90deg, rgba(20, 113, 126, 0.045) 1px, transparent 1px),
    radial-gradient(circle at 92% 0%, rgba(208, 133, 50, 0.12), transparent 31%),
    rgba(255, 255, 255, 0.98);
  background-size: 26px 100%, auto, auto;
  border-top: 3px solid #197b83;
}
.traceback-heading,
.traceback-summary {
  display: flex;
  align-items: center;
  gap: 12px;
}
.traceback-heading {
  justify-content: space-between;
}
.traceback-summary {
  flex-wrap: wrap;
  justify-content: flex-end;
}
.traceback-summary > span {
  color: #68818c;
  font-size: 12px;
}
.traceback-summary b {
  margin-right: 3px;
  color: #166f78;
  font-size: 18px;
}
.traceback-flow-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 12px;
}
.traceback-flow-strip article {
  position: relative;
  overflow: hidden;
  padding: 13px 14px;
  background: #f4faf9;
  border: 1px solid #d6e8e6;
  border-radius: 3px 10px 10px 10px;
}
.traceback-flow-strip article::after {
  position: absolute;
  right: -18px;
  bottom: -22px;
  width: 58px;
  height: 58px;
  content: '';
  border: 1px solid rgba(25, 123, 131, 0.12);
  transform: rotate(45deg);
}
.traceback-flow-strip span,
.traceback-flow-strip strong,
.traceback-flow-strip small {
  position: relative;
  z-index: 1;
  display: block;
}
.traceback-flow-strip span {
  color: #cf8736;
  font: 700 16px/1 'DIN Alternate', sans-serif;
}
.traceback-flow-strip strong {
  margin: 6px 0 4px;
  color: #17424b;
  font-size: 14px;
}
.traceback-flow-strip small {
  color: #708891;
  line-height: 1.45;
}
.traceback-filter-bar {
  grid-template-columns: repeat(4, minmax(130px, 0.8fr)) minmax(190px, 1.2fr) auto auto;
}
.traceback-state-cell {
  display: flex;
  gap: 7px;
  align-items: center;
  flex-wrap: wrap;
}
.traceback-state-cell > span {
  color: #536f7b;
  font-size: 12px;
}
.traceback-kind-chips,
.traceback-transition-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}
.traceback-kind-chips span,
.traceback-transition-row span {
  padding: 3px 7px;
  color: #4d6d74;
  font-size: 10px;
  background: #edf5f4;
  border: 1px solid #d5e5e3;
  border-radius: 999px;
}
.traceback-command {
  background:
    radial-gradient(circle at 82% 18%, rgba(235, 169, 86, 0.25), transparent 32%),
    linear-gradient(125deg, #102e3d, #176974);
}
.traceback-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 13px;
}
.traceback-form-grid label,
.traceback-form-grid label > span {
  display: block;
}
.traceback-form-grid label > span {
  margin-bottom: 6px;
  color: #657b86;
  font-size: 12px;
}
.traceback-form-grid .wide {
  grid-column: 1 / -1;
}
.traceback-summary-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.traceback-summary-grid > div {
  display: grid;
  gap: 6px;
  min-height: 82px;
  padding: 12px;
  background: #f5f9f9;
  border: 1px solid #dde9e9;
  border-radius: 7px;
}
.traceback-summary-grid span {
  color: #81969c;
  font-size: 11px;
}
.traceback-summary-grid strong {
  color: #214653;
  font-size: 13px;
  line-height: 1.45;
}
.traceback-node-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 9px;
}
.traceback-node-grid article {
  display: grid;
  gap: 7px;
  padding: 13px;
  background: linear-gradient(135deg, #f7fbfb, #eef6f5);
  border: 1px solid #dce9e7;
  border-left: 3px solid #24898b;
  border-radius: 5px;
}
.traceback-node-grid article > div {
  display: flex;
  justify-content: space-between;
  color: #246c72;
  font-size: 12px;
}
.traceback-node-grid article > strong {
  color: #31515d;
  font-size: 12px;
}
.traceback-node-grid article > i {
  width: 46px;
  height: 1px;
  background: #cf8736;
}
.traceback-node-grid article > small {
  color: #84969d;
  font-size: 10px;
}
.traceback-transition-row {
  margin-bottom: 14px;
}
.traceback-timeline-list {
  display: grid;
}
.traceback-timeline-list article {
  display: grid;
  grid-template-columns: 150px 14px 1fr;
  gap: 10px;
  min-height: 70px;
}
.traceback-timeline-list time {
  padding-top: 4px;
  color: #82959e;
  font-size: 11px;
  text-align: right;
}
.traceback-timeline-list article > span {
  position: relative;
  width: 10px;
  height: 10px;
  margin-top: 4px;
  background: #738b95;
  border: 2px solid white;
  border-radius: 50%;
  box-shadow: 0 0 0 1px #b8c7cd;
}
.traceback-timeline-list article > span::after {
  position: absolute;
  top: 10px;
  left: 3px;
  width: 1px;
  height: 56px;
  content: '';
  background: #dce5e8;
}
.traceback-timeline-list article:last-child > span::after {
  display: none;
}
.traceback-timeline-list article > span.metric,
.traceback-timeline-list article > span.sentiment {
  background: #238b79;
}
.traceback-timeline-list article > span.alert {
  background: #bd4b42;
}
.traceback-timeline-list article > span.process,
.traceback-timeline-list article > span.work_order {
  background: #cf8736;
}
.traceback-timeline-list article > div {
  display: grid;
  align-content: start;
  gap: 3px;
}
.traceback-timeline-list small {
  color: #8f7369;
  font-size: 10px;
  letter-spacing: 0.7px;
}
.traceback-timeline-list strong {
  color: #294657;
  font-size: 13px;
}
.traceback-timeline-list p {
  margin: 0;
  color: #80929b;
  font-size: 11px;
}
.delta-up {
  color: #b66d24;
}
.delta-down {
  color: #16806b;
}
.record-panel {
  margin-top: 14px;
  background:
    linear-gradient(115deg, rgba(35, 69, 93, 0.05), transparent 38%),
    repeating-linear-gradient(90deg, transparent 0 47px, rgba(24, 71, 91, 0.025) 48px),
    rgba(255, 255, 255, 0.98);
  border-top: 3px solid #274f69;
}
.record-heading,
.record-heading-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}
.record-heading {
  justify-content: space-between;
}
.record-heading-actions > span {
  color: #70838d;
  font-size: 12px;
}
.record-heading-actions b {
  margin-right: 4px;
  color: #274f69;
  font-size: 19px;
}
.record-scoreboard {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}
.record-scoreboard article {
  position: relative;
  display: grid;
  gap: 5px;
  min-height: 92px;
  padding: 13px;
  overflow: hidden;
  background: #f5f8fa;
  border: 1px solid #dce5e9;
  border-radius: 2px 8px 8px 8px;
}
.record-scoreboard article::before {
  position: absolute;
  top: 0;
  left: 0;
  width: 3px;
  height: 100%;
  content: '';
  background: #5c7888;
}
.record-scoreboard article.success::before { background: #2d8b72; }
.record-scoreboard article.running::before { background: #317ca1; }
.record-scoreboard article.attention::before { background: #c88635; }
.record-scoreboard article.failed::before { background: #b84a43; }
.record-scoreboard small {
  color: #84959d;
  font: 700 9px/1.2 'DIN Alternate', sans-serif;
  letter-spacing: 1px;
}
.record-scoreboard strong {
  color: #203f54;
  font: 700 23px/1 'DIN Alternate', sans-serif;
}
.record-scoreboard span {
  color: #82939b;
  font-size: 10px;
  line-height: 1.35;
}
.filter-bar.record-filter-bar {
  grid-template-columns: minmax(160px, 1.1fr) repeat(2, minmax(120px, 0.8fr)) minmax(140px, 0.9fr);
}
.record-filter-bar > *,
.record-filter-bar :deep(.el-date-editor) {
  width: 100%;
  min-width: 0;
}
.record-link {
  display: flex;
  gap: 10px;
  align-items: center;
  padding: 0;
  color: inherit;
  text-align: left;
  background: transparent;
  border: 0;
  cursor: pointer;
}
.record-link > span:last-child,
.record-link strong,
.record-link small {
  display: block;
}
.record-link strong {
  color: #29495d;
}
.record-link small {
  margin-top: 3px;
  color: #86969e;
  font-size: 10px;
}
.record-kind {
  display: grid;
  width: 34px;
  height: 34px;
  flex: 0 0 34px;
  place-items: center;
  color: #f5fbff;
  font: 700 9px/1 'DIN Alternate', sans-serif;
  letter-spacing: 0.5px;
  background: #466b7d;
  border-radius: 2px 10px 2px 2px;
}
.record-kind.data_batch,
.record-kind.traceback { background: #228174; }
.record-kind.process_run,
.record-kind.scene_run { background: #bb7930; }
.record-kind.alert { background: #a94740; }
.record-kind.capability_call { background: #7657a6; }
.record-command {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
  color: #f4f9fc;
  background:
    linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px),
    radial-gradient(circle at 84% 12%, rgba(67, 188, 165, 0.2), transparent 29%),
    linear-gradient(125deg, #172c3d, #28566b);
  background-size: 30px 100%, auto, auto;
  border-radius: 3px 12px 12px 12px;
}
.record-command h3 {
  margin: 5px 0;
  font-size: 22px;
}
.record-command p:last-child {
  margin: 0;
  color: rgba(255, 255, 255, 0.65);
}
.record-command-state {
  display: grid;
  justify-items: end;
  gap: 7px;
}
.record-command-state strong {
  font: 700 32px/1 'DIN Alternate', sans-serif;
}
.record-result-grid,
.record-source-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.record-result-grid > div,
.record-source-grid article {
  display: grid;
  gap: 6px;
  padding: 12px;
  background: #f5f8fa;
  border: 1px solid #dfe7ea;
  border-radius: 6px;
}
.record-result-grid .wide { grid-column: 1 / -1; }
.record-result-grid span,
.record-source-grid span {
  color: #84959d;
  font-size: 10px;
}
.record-result-grid strong,
.record-source-grid strong {
  color: #29495d;
  font-size: 12px;
  line-height: 1.5;
  word-break: break-word;
}
.record-activity-list {
  display: grid;
}
.record-activity-list article {
  display: grid;
  grid-template-columns: 32px 12px 1fr;
  gap: 10px;
  min-height: 74px;
}
.record-activity-list article > span {
  padding-top: 1px;
  color: #6d8794;
  font: 700 12px/1.4 'DIN Alternate', sans-serif;
  text-align: right;
}
.record-activity-list i {
  position: relative;
  width: 9px;
  height: 9px;
  margin-top: 3px;
  background: #2e7f79;
  border: 2px solid white;
  border-radius: 50%;
  box-shadow: 0 0 0 1px #a9bdc4;
}
.record-activity-list i::after {
  position: absolute;
  top: 9px;
  left: 3px;
  width: 1px;
  height: 58px;
  content: '';
  background: #dce5e8;
}
.record-activity-list article:last-child i::after { display: none; }
.record-activity-list article > div {
  display: grid;
  align-content: start;
  gap: 3px;
}
.record-activity-list strong { color: #29495d; font-size: 13px; }
.record-activity-list small { color: #7d919b; font-size: 10px; }
.record-activity-list p {
  margin: 0;
  color: #81939b;
  font-size: 11px;
  line-height: 1.45;
  word-break: break-word;
}
.capability-panel {
  margin-top: 14px;
  background:
    linear-gradient(135deg, rgba(118, 87, 166, 0.055), transparent 36%),
    repeating-linear-gradient(0deg, transparent 0 31px, rgba(36, 61, 73, 0.022) 32px),
    rgba(255, 255, 255, 0.98);
  border-top: 3px solid #7657a6;
}
.capability-heading,
.capability-heading-actions,
.capability-call-link,
.capability-call-state,
.sandbox-footer,
.capability-subheading {
  display: flex;
  align-items: center;
}
.capability-heading,
.sandbox-footer,
.capability-subheading {
  justify-content: space-between;
}
.capability-heading-actions { gap: 12px; }
.capability-heading-actions span { color: #72858d; font-size: 12px; }
.capability-heading-actions b { margin-right: 4px; color: #5c408c; font-size: 19px; }
.capability-scoreboard {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}
.capability-scoreboard article {
  display: grid;
  gap: 5px;
  min-height: 86px;
  padding: 13px;
  background: #f6f5f9;
  border: 1px solid #e1ddeb;
  border-left: 3px solid #7657a6;
  border-radius: 3px 9px 9px 3px;
}
.capability-scoreboard article.success { border-left-color: #27836c; }
.capability-scoreboard article.danger { border-left-color: #b9534d; }
.capability-scoreboard small { color: #8c849b; font: 700 9px/1.2 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.capability-scoreboard strong { color: #3f3454; font: 700 23px/1 'DIN Alternate', sans-serif; }
.capability-scoreboard span { color: #887f93; font-size: 10px; }
.capability-workbench {
  display: grid;
  grid-template-columns: minmax(300px, 0.9fr) minmax(460px, 1.45fr);
  gap: 12px;
  margin-bottom: 12px;
}
.capability-catalog,
.sandbox-console {
  padding: 14px;
  background: #f6f8f9;
  border: 1px solid #dde5e8;
  border-radius: 10px;
}
.capability-subheading { margin-bottom: 10px; }
.capability-subheading span { color: #344e5c; font-size: 13px; font-weight: 700; }
.capability-subheading small { color: #8998a0; font-size: 10px; }
.capability-catalog { display: grid; align-content: start; gap: 8px; }
.capability-card {
  display: flex;
  gap: 11px;
  align-items: center;
  padding: 11px;
  color: inherit;
  text-align: left;
  background: white;
  border: 1px solid #dce5e8;
  border-radius: 4px 10px 10px 4px;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease, box-shadow 0.2s ease;
}
.capability-card:hover,
.capability-card.active {
  border-color: #8d71b8;
  box-shadow: 0 8px 20px rgba(84, 57, 121, 0.1);
  transform: translateX(2px);
}
.capability-kind {
  display: grid;
  width: 36px;
  height: 36px;
  flex: 0 0 36px;
  place-items: center;
  color: white;
  font: 700 9px/1 'DIN Alternate', sans-serif;
  background: #7657a6;
  border-radius: 3px 11px 3px 3px;
}
.capability-kind.atomic { background: #b6752e; }
.capability-card-main { min-width: 0; }
.capability-card-main strong,
.capability-card-main small,
.capability-card-main em,
.capability-call-link strong,
.capability-call-link small { display: block; }
.capability-card-main strong { color: #334d5b; font-size: 13px; }
.capability-card-main small { margin-top: 3px; overflow: hidden; color: #768b95; font-size: 10px; text-overflow: ellipsis; white-space: nowrap; }
.capability-card-main em { margin-top: 5px; color: #9a7a51; font-size: 9px; font-style: normal; }
.sandbox-grid,
.capability-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.sandbox-grid label,
.capability-form-grid label { display: grid; gap: 5px; }
.sandbox-grid label > span,
.capability-form-grid label > span { color: #637983; font-size: 10px; font-weight: 700; }
.sandbox-grid .wide,
.capability-form-grid .wide { grid-column: 1 / -1; }
.sandbox-grid :deep(.el-input-number),
.capability-form-grid :deep(.el-input-number) { width: 100%; }
.sandbox-footer {
  gap: 12px;
  padding-top: 12px;
  margin-top: 12px;
  border-top: 1px dashed #cfdade;
}
.sandbox-footer span { color: #8066a6; font: 700 10px/1.3 'DIN Alternate', sans-serif; letter-spacing: 0.6px; }
.warroom-rail {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}
.warroom-rail button {
  display: grid;
  gap: 3px;
  padding: 10px 12px;
  color: inherit;
  text-align: left;
  background: #253b49;
  border: 1px solid #253b49;
  border-radius: 3px 9px 9px 3px;
  cursor: pointer;
}
.warroom-rail button.active { border-color: #bda4e2; box-shadow: inset 3px 0 #bda4e2; }
.warroom-rail small { color: #af9bc8; font: 700 8px/1 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.warroom-rail strong { color: #f4f1f8; font-size: 12px; }
.warroom-rail span { color: #9cb0b9; font-size: 9px; }
.filter-bar.capability-filter-bar { grid-template-columns: minmax(160px, 1.1fr) repeat(2, minmax(120px, 0.8fr)) minmax(190px, 1.25fr) auto auto; }
.capability-call-link { gap: 10px; padding: 0; color: inherit; text-align: left; background: transparent; border: 0; cursor: pointer; }
.capability-call-link strong { color: #344f5d; }
.capability-call-link small { margin-top: 3px; color: #87979f; font-size: 10px; }
.capability-command { background: radial-gradient(circle at 80% 0, rgba(196, 164, 231, 0.25), transparent 30%), linear-gradient(125deg, #2a2337, #4f3d68); }
.capability-call-state { flex-direction: column; align-items: flex-end; gap: 8px; }
.capability-call-state strong { color: white; font: 700 24px/1 'DIN Alternate', sans-serif; }
.capability-mock-form { display: grid; gap: 14px; }
.payload-compare { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.payload-compare article { min-width: 0; }
.payload-compare h3 { margin: 4px 0 10px; }
.payload-compare pre {
  min-height: 220px;
  max-height: 420px;
  padding: 14px;
  overflow: auto;
  color: #d8ecdf;
  font: 11px/1.55 ui-monospace, SFMono-Regular, Menlo, monospace;
  white-space: pre-wrap;
  word-break: break-word;
  background: #182a32;
  border-radius: 4px 10px 10px 4px;
}
.capability-replay-actions { display: flex; flex-wrap: wrap; gap: 8px; }
.fault-configuration-panel {
  margin-top: 14px;
  background:
    linear-gradient(135deg, rgba(188, 72, 54, 0.065), transparent 34%),
    repeating-linear-gradient(90deg, transparent 0 39px, rgba(34, 57, 68, 0.025) 40px),
    rgba(255, 255, 255, 0.985);
  border-top: 3px solid #b94f3d;
}
.fault-configuration-heading,
.fault-configuration-heading-actions,
.fault-blueprint-head,
.topology-board-head,
.fault-apply-bar,
.fault-config-link {
  display: flex;
  align-items: center;
}
.fault-configuration-heading,
.fault-blueprint-head,
.topology-board-head { justify-content: space-between; }
.fault-configuration-heading-actions { gap: 12px; }
.fault-configuration-heading-actions > span { color: #71858e; font-size: 12px; }
.fault-configuration-heading-actions b { margin-right: 4px; color: #a44334; font-size: 19px; }
.fault-scoreboard {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 12px;
}
.fault-scoreboard article {
  display: grid;
  gap: 5px;
  min-height: 82px;
  padding: 13px;
  background: #f8f6f4;
  border: 1px solid #e8ded9;
  border-left: 3px solid #5f7580;
  border-radius: 3px 9px 9px 3px;
}
.fault-scoreboard article.ready { border-left-color: #27826c; }
.fault-scoreboard article.draft { border-left-color: #bc7536; }
.fault-scoreboard small { color: #8b7e78; font: 700 9px/1.2 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.fault-scoreboard strong { color: #3e5059; font: 700 23px/1 'DIN Alternate', sans-serif; }
.fault-scoreboard span { color: #8b9294; font-size: 10px; }
.fault-workbench {
  display: grid;
  grid-template-columns: minmax(270px, 0.72fr) minmax(520px, 1.7fr);
  gap: 12px;
  margin-bottom: 12px;
}
.fault-config-rail {
  display: grid;
  align-content: start;
  gap: 8px;
  padding: 13px;
  background: #f4f6f6;
  border: 1px solid #dce4e6;
  border-radius: 9px;
}
.fault-config-rail > button {
  display: grid;
  grid-template-columns: 42px minmax(0, 1fr) auto;
  gap: 9px;
  align-items: center;
  padding: 10px;
  color: inherit;
  text-align: left;
  background: white;
  border: 1px solid #dce4e6;
  border-radius: 3px 9px 9px 3px;
  cursor: pointer;
  transition: border-color 0.2s ease, transform 0.2s ease;
}
.fault-config-rail > button:hover,
.fault-config-rail > button.active { border-color: #bd6a59; transform: translateX(2px); }
.fault-version {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  color: white;
  font: 700 11px/1 'DIN Alternate', sans-serif;
  background: #263e49;
  border-radius: 2px 10px 2px 2px;
}
.fault-config-rail strong,
.fault-config-rail small { display: block; }
.fault-config-rail strong { overflow: hidden; color: #324b57; font-size: 12px; text-overflow: ellipsis; white-space: nowrap; }
.fault-config-rail small { margin-top: 3px; color: #84949b; font-size: 9px; }
.fault-config-rail i { padding: 3px 5px; color: #8c5b2d; font-size: 8px; font-style: normal; background: #fbecda; border-radius: 3px; }
.fault-config-rail i.ready { color: #23745f; background: #e2f2ed; }
.fault-config-rail i.archived { color: #77858a; background: #edf0f1; }
.fault-blueprint {
  min-width: 0;
  padding: 14px;
  background: #f8faf9;
  border: 1px solid #dbe4e5;
  border-radius: 9px;
}
.fault-blueprint-head { gap: 14px; margin-bottom: 10px; }
.fault-blueprint-head h3 { margin: 4px 0; color: #293f4b; font-size: 16px; }
.fault-blueprint-head > div > span { color: #7b8d94; font-size: 10px; }
.topology-board {
  padding: 13px;
  background:
    linear-gradient(rgba(44, 76, 86, 0.38) 1px, transparent 1px),
    linear-gradient(90deg, rgba(44, 76, 86, 0.38) 1px, transparent 1px),
    #15272f;
  background-size: 20px 20px;
  border: 1px solid #29444e;
  border-radius: 4px 10px 10px 4px;
}
.topology-board-head { margin-bottom: 10px; }
.topology-board-head span { color: #d8e5e6; font: 700 10px/1 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.topology-board-head small { color: #8099a1; font-size: 9px; }
.topology-nodes {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.topology-nodes article {
  position: relative;
  display: grid;
  grid-template-columns: auto 7px minmax(0, 1fr);
  gap: 5px 7px;
  align-items: center;
  padding: 9px;
  background: rgba(27, 49, 58, 0.92);
  border: 1px solid #45616a;
  border-top: 2px solid #728991;
  border-radius: 2px 7px 7px 2px;
}
.topology-nodes article > span { color: #73909a; font: 700 9px/1 'DIN Alternate', sans-serif; }
.topology-nodes article > i { width: 7px; height: 7px; background: #7c9097; border-radius: 50%; box-shadow: 0 0 0 3px rgba(124, 144, 151, 0.15); }
.topology-nodes article > strong { overflow: hidden; color: #eef5f4; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.topology-nodes article > small { grid-column: 1 / 4; color: #829ba3; font-size: 8px; }
.topology-nodes article > em { position: absolute; right: 7px; bottom: 6px; color: #91a5ab; font-size: 7px; font-style: normal; letter-spacing: 0.5px; }
.topology-nodes article.fault { border-top-color: #df6954; }
.topology-nodes article.fault > i { background: #df6954; box-shadow: 0 0 0 3px rgba(223, 105, 84, 0.17); }
.topology-nodes article.degraded { border-top-color: #d69a42; }
.topology-nodes article.degraded > i { background: #d69a42; box-shadow: 0 0 0 3px rgba(214, 154, 66, 0.17); }
.topology-nodes article.standby { border-top-color: #7693cf; }
.topology-nodes article.standby > i { background: #7693cf; box-shadow: 0 0 0 3px rgba(118, 147, 207, 0.17); }
.topology-nodes article.healthy { border-top-color: #49a88e; }
.topology-nodes article.healthy > i { background: #49a88e; box-shadow: 0 0 0 3px rgba(73, 168, 142, 0.17); }
.topology-links { display: flex; flex-wrap: wrap; gap: 5px; margin-top: 10px; }
.topology-links span { padding: 4px 6px; color: #a7bbc0; font: 700 8px/1.2 ui-monospace, SFMono-Regular, Menlo, monospace; background: rgba(43, 69, 78, 0.82); border: 1px solid #3b5963; border-radius: 2px; }
.fault-policy-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 7px;
  margin-top: 9px;
}
.fault-policy-grid article { min-width: 0; padding: 10px; background: #f0f3f2; border: 1px solid #dce3e3; border-left: 2px solid #bd6a59; border-radius: 2px 7px 7px 2px; }
.fault-policy-grid small { display: block; color: #9a6a5f; font: 700 8px/1.2 'DIN Alternate', sans-serif; letter-spacing: 0.6px; }
.fault-policy-grid strong { display: block; margin-top: 6px; color: #314d58; font-size: 13px; }
.fault-policy-grid p { margin: 5px 0 0; overflow: hidden; color: #829197; font-size: 9px; line-height: 1.4; text-overflow: ellipsis; white-space: nowrap; }
.fault-apply-bar { gap: 10px; padding-top: 10px; margin-top: 10px; border-top: 1px dashed #cbd7d9; }
.fault-apply-bar > div { flex: 1; }
.fault-apply-bar span,
.fault-apply-bar small { display: block; }
.fault-apply-bar span { color: #38505c; font-size: 11px; font-weight: 700; }
.fault-apply-bar small { margin-top: 2px; color: #82949a; font-size: 9px; }
.fault-apply-bar :deep(.el-select) { width: min(260px, 36%); }
.filter-bar.fault-configuration-filter-bar { grid-template-columns: repeat(3, minmax(130px, 0.75fr)) minmax(190px, 1.25fr) auto auto; }
.fault-config-link { gap: 10px; padding: 0; color: inherit; text-align: left; background: transparent; border: 0; cursor: pointer; }
.fault-config-link > span { display: grid; width: 36px; height: 36px; place-items: center; color: white; font: 700 10px/1 'DIN Alternate', sans-serif; background: #b7503e; border-radius: 2px 9px 2px 2px; }
.fault-config-link i { font-style: normal; }
.fault-config-link strong,
.fault-config-link small { display: block; }
.fault-config-link strong { color: #344d59; }
.fault-config-link small { margin-top: 3px; color: #89979d; font-size: 9px; }
.fault-configuration-form { display: grid; gap: 14px; }
.fault-configuration-command { background: radial-gradient(circle at 82% 0, rgba(221, 111, 83, 0.3), transparent 31%), linear-gradient(125deg, #202f36, #4e332f); }
.fault-configuration-form-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.fault-configuration-form-grid label { display: grid; gap: 5px; min-width: 0; }
.fault-configuration-form-grid label > span { color: #617881; font-size: 10px; font-weight: 700; }
.fault-configuration-form-grid label > span b { margin-right: 5px; color: #b34f3c; font: 700 11px/1 'DIN Alternate', sans-serif; }
.fault-configuration-form-grid .wide { grid-column: 1 / -1; }
.fault-configuration-form-grid .json-field { padding: 10px; background: #f5f7f6; border: 1px solid #dde5e5; border-radius: 6px; }
.fault-configuration-form-grid .json-field :deep(textarea) { color: #34505b; font: 11px/1.5 ui-monospace, SFMono-Regular, Menlo, monospace; }
.fault-detail-state { display: grid; justify-items: end; gap: 3px; }
.fault-detail-state strong { color: white; font: 700 25px/1 'DIN Alternate', sans-serif; }
.fault-detail-state > span { color: #baaba7; font-size: 9px; }
.fault-validation-grid {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 7px;
}
.fault-validation-grid article { display: grid; gap: 5px; min-height: 92px; padding: 10px; background: #fcf4ef; border: 1px solid #efd9cc; border-top: 3px solid #cb654c; border-radius: 3px 8px 8px 3px; }
.fault-validation-grid article.passed { background: #f0f8f5; border-color: #d1e8e0; border-top-color: #2c8b71; }
.fault-validation-grid article > span { color: #b54e38; font: 700 8px/1 'DIN Alternate', sans-serif; letter-spacing: 0.8px; }
.fault-validation-grid article.passed > span { color: #258069; }
.fault-validation-grid strong { color: #344e5a; font-size: 11px; }
.fault-validation-grid small { color: #829096; font-size: 9px; line-height: 1.4; }
.fault-detail-topology { margin-top: 8px; }
.fault-detail-policy-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.fault-detail-policy-grid > article { min-width: 0; padding: 12px; background: #f8faf9; border: 1px solid #e0e7e7; border-radius: 7px; }
.fault-detail-policy-grid h3 { margin: 4px 0 10px; color: #334d59; }
.fault-rule-list { display: grid; gap: 7px; padding: 0; margin: 0; list-style: none; }
.fault-rule-list li { display: grid; grid-template-columns: 54px 1fr; gap: 8px; align-items: center; }
.fault-rule-list li > span { padding: 5px; color: #785829; font: 700 8px/1 'DIN Alternate', sans-serif; text-align: center; background: #f4e8d4; border-radius: 2px; }
.fault-rule-list li > span.high,
.fault-rule-list li > span.critical { color: #9e4436; background: #f7dfda; }
.fault-rule-list strong,
.fault-rule-list small { display: block; }
.fault-rule-list strong { color: #39525d; font-size: 11px; }
.fault-rule-list small { margin-top: 2px; color: #84949a; font-size: 9px; }
.fault-runtime-facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 7px; }
.fault-runtime-facts span { display: grid; gap: 5px; padding: 10px; color: #87969c; font-size: 9px; background: white; border: 1px solid #e0e7e7; border-radius: 3px; }
.fault-runtime-facts strong { overflow: hidden; color: #34505b; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }
.fault-plan-list,
.fault-audit-list { display: grid; gap: 7px; }
.fault-plan-list article { display: grid; grid-template-columns: 34px minmax(0, 1fr) auto; gap: 10px; align-items: center; padding: 10px; background: #f7f9f8; border: 1px solid #dfe7e7; border-left: 2px solid #be6a57; border-radius: 2px 7px 7px 2px; }
.fault-plan-list article > span { color: #a34a39; font: 700 12px/1 'DIN Alternate', sans-serif; }
.fault-plan-list strong,
.fault-plan-list small { display: block; }
.fault-plan-list strong { color: #344e59; font-size: 12px; }
.fault-plan-list small { margin-top: 3px; color: #84949a; font-size: 9px; }
.fault-plan-list em { color: #906052; font: 700 9px/1 'DIN Alternate', sans-serif; font-style: normal; }
.fault-bound-list { display: flex; flex-wrap: wrap; gap: 7px; }
.fault-bound-list > span { display: grid; gap: 3px; padding: 9px 11px; color: #849399; font-size: 9px; background: #f3f7f6; border: 1px solid #d9e5e2; border-left: 2px solid #338570; border-radius: 2px 7px 7px 2px; }
.fault-bound-list b { color: #34505b; font-size: 11px; }
.fault-audit-list article { display: grid; grid-template-columns: 34px 1fr; gap: 10px; padding: 9px 0; border-bottom: 1px dashed #d8e2e3; }
.fault-audit-list article > span { color: #a45140; font: 700 11px/1.4 'DIN Alternate', sans-serif; text-align: right; }
.fault-audit-list strong,
.fault-audit-list small { display: block; }
.fault-audit-list strong { color: #344d59; font-size: 11px; }
.fault-audit-list small { margin-top: 2px; color: #87969c; font-size: 9px; }
.fault-audit-list p { margin: 4px 0 0; color: #758a92; font-size: 10px; }
.scene-replay-panel {
  margin-top: 14px;
  background: linear-gradient(90deg, rgba(20, 168, 191, 0.045), transparent 45%), repeating-linear-gradient(0deg, transparent 0 27px, rgba(34, 77, 91, 0.025) 28px), #fbfdfe;
  border-top: 3px solid #1697aa;
}
.scene-replay-heading,
.scene-replay-heading-actions,
.replay-console-head,
.traffic-toolbar,
.node-trace-strip { display: flex; align-items: center; justify-content: space-between; gap: 14px; }
.scene-replay-heading-actions span { color: #6f858e; font-size: 12px; }
.scene-replay-heading-actions b { margin-right: 3px; color: #0b8499; font-size: 19px; }
.scene-replay-scoreboard { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-bottom: 12px; }
.scene-replay-scoreboard article { display: grid; gap: 5px; padding: 12px; background: #edf7f9; border: 1px solid #d5e8eb; border-radius: 3px; }
.scene-replay-scoreboard small { color: #63828d; font: 700 9px/1 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.scene-replay-scoreboard strong { color: #145b6b; font: 700 25px/1 'DIN Alternate', sans-serif; }
.scene-replay-scoreboard span { color: #83969d; font-size: 9px; }
.scene-replay-scoreboard .attention { background: #fff6ed; border-color: #ecd7c1; }
.scene-replay-scoreboard .attention strong { color: #b45b34; }
.scene-replay-workbench { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 10px; min-height: 420px; padding: 10px; margin-bottom: 12px; color: #d8edf1; background: #102630; border: 1px solid #21434e; border-radius: 4px; }
.scene-replay-rail { min-width: 0; padding-right: 9px; border-right: 1px solid #244550; }
.scene-replay-rail .capability-subheading { padding: 5px 4px 10px; color: #7fc4ce; }
.scene-replay-rail button { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; gap: 8px; align-items: center; width: 100%; padding: 10px 7px; color: #b6ccd2; text-align: left; background: transparent; border: 0; border-bottom: 1px solid #1c3c46; cursor: pointer; }
.scene-replay-rail button.active { background: linear-gradient(90deg, rgba(31, 180, 200, 0.18), transparent); border-left: 2px solid #3ad1e2; }
.scene-replay-rail button > span { color: #59c5d3; font: 700 10px/1 'DIN Alternate', sans-serif; }
.scene-replay-rail strong,
.scene-replay-rail small { display: block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.scene-replay-rail strong { color: #e0eff2; font-size: 11px; }
.scene-replay-rail small { margin-top: 4px; color: #668b94; font-size: 8px; }
.scene-replay-rail em { color: #65bd99; font-size: 8px; font-style: normal; }
.scene-replay-scope { display: grid; align-content: start; gap: 10px; min-width: 0; }
.replay-console-head { padding: 4px 4px 9px; border-bottom: 1px solid #244550; }
.replay-console-head h3 { margin: 3px 0; color: #f0fafb; font-size: 15px; }
.replay-console-head span { color: #70939c; font-size: 9px; }
.traffic-oscilloscope { padding: 12px; background: radial-gradient(circle at 78% 35%, rgba(35, 210, 220, 0.08), transparent 28%), #0a1c24; border: 1px solid #214550; border-radius: 3px; }
.traffic-toolbar { justify-content: flex-start; }
.traffic-toolbar button { width: 26px; height: 26px; color: #86d7df; background: #14323c; border: 1px solid #2c5f6a; cursor: pointer; }
.traffic-toolbar button.play { color: #07191f; background: #39c9d8; }
.traffic-toolbar span { color: #5c8b94; font: 700 9px/1 'DIN Alternate', sans-serif; letter-spacing: 0.8px; }
.traffic-toolbar strong { margin-left: auto; color: #c7edf1; font: 700 11px/1 'DIN Alternate', sans-serif; }
.traffic-oscilloscope :deep(.el-slider) { margin: 10px 0 6px; }
.traffic-frame-card { display: grid; grid-template-columns: 76px minmax(0, 1fr) auto auto; gap: 10px; align-items: center; padding: 9px 10px; background: rgba(30, 164, 180, 0.12); border-left: 2px solid #36c9d8; }
.traffic-frame-card.alert { background: rgba(199, 81, 53, 0.13); border-color: #d36a4b; }
.traffic-frame-card.control { background: rgba(182, 139, 54, 0.13); border-color: #d5a644; }
.traffic-frame-card span { color: #58c8d4; font: 700 9px/1 'DIN Alternate', sans-serif; }
.traffic-frame-card strong { color: #d7ecef; font-size: 11px; }
.traffic-frame-card small { color: #628b94; font-size: 8px; }
.traffic-frame-card em { color: #dfa66a; font-size: 9px; font-style: normal; }
.topology-mirror-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }
.topology-mirror-grid section { display: grid; gap: 6px; padding: 9px; background: #142c35; border: 1px solid #284b55; }
.topology-mirror-grid section.after { background: #102f36; border-color: #2b5b62; }
.topology-mirror-grid header { display: flex; align-items: center; justify-content: space-between; color: #58bdc9; font: 700 9px/1 'DIN Alternate', sans-serif; }
.topology-mirror-grid header small { color: #5d7c84; font-size: 8px; font-weight: 400; }
.topology-mirror-grid button { display: grid; grid-template-columns: 9px minmax(0, 1fr) auto auto; gap: 7px; align-items: center; padding: 7px 8px; color: #b8cdd2; text-align: left; background: #0f242c; border: 1px solid transparent; cursor: pointer; }
.topology-mirror-grid button.active { border-color: #42c8d5; }
.topology-mirror-grid button > i { width: 7px; height: 7px; background: #6e8991; border-radius: 50%; }
.topology-mirror-grid button.state-healthy > i,
.topology-mirror-grid button.state-active > i,
.topology-mirror-grid button.state-recovered > i { background: #42c995; box-shadow: 0 0 7px rgba(66, 201, 149, 0.7); }
.topology-mirror-grid button.state-fault > i,
.topology-mirror-grid button.state-degraded > i { background: #e16a4d; box-shadow: 0 0 7px rgba(225, 106, 77, 0.7); }
.topology-mirror-grid button strong { color: #dcecef; font-size: 10px; }
.topology-mirror-grid button small { color: #66858d; font-size: 8px; }
.topology-mirror-grid button em { color: #8bacb4; font-size: 8px; font-style: normal; }
.node-trace-strip { padding: 9px 11px; background: #17343e; border-left: 2px solid #33c5d5; }
.node-trace-strip div { display: grid; gap: 2px; }
.node-trace-strip div > span { color: #43bdc9; font: 700 8px/1 'DIN Alternate', sans-serif; }
.node-trace-strip strong { color: #dfedef; font-size: 11px; }
.node-trace-strip small,
.node-trace-strip > span { color: #78959c; font-size: 8px; }
.node-trace-strip > b { color: #e1a35c; font: 700 11px/1 'DIN Alternate', sans-serif; }
.scene-replay-filter-bar { grid-template-columns: 1.3fr 1fr 0.8fr 1.2fr auto auto; }
.scene-replay-link { display: flex; align-items: center; gap: 9px; width: 100%; padding: 0; color: inherit; text-align: left; background: transparent; border: 0; cursor: pointer; }
.scene-replay-link > span { display: grid; width: 32px; height: 32px; place-items: center; color: #f0fdff; font: 700 9px/1 'DIN Alternate', sans-serif; background: #148fa1; border-radius: 2px 8px 2px 2px; }
.scene-replay-link strong,
.scene-replay-link small { display: block; }
.scene-replay-link strong { color: #31515d; }
.scene-replay-link small { margin-top: 2px; color: #87979d; font-size: 9px; }
.scene-replay-command { background: radial-gradient(circle at 85% 15%, rgba(54, 211, 223, 0.24), transparent 28%), linear-gradient(125deg, #0d2630, #145d69); }
.scene-replay-command > span { color: #70d8e1; font: 700 12px/1 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.scene-replay-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.scene-replay-form-grid label { display: grid; gap: 5px; color: #708790; font-size: 10px; }
.scene-replay-form-grid .wide { grid-column: 1 / -1; }
.scene-replay-form-grid :deep(.el-select),
.scene-replay-form-grid :deep(.el-date-editor) { width: 100%; }
.replay-checksum { display: grid; justify-items: end; gap: 5px; max-width: 330px; }
.replay-checksum span { color: #70d8e1; font: 700 9px/1 'DIN Alternate', sans-serif; }
.replay-checksum code { overflow: hidden; max-width: 100%; color: #91b8bf; font-size: 8px; text-overflow: ellipsis; white-space: nowrap; }
.replay-delta-list,
.replay-node-detail-list,
.replay-frame-list { display: grid; gap: 7px; }
.replay-delta-list { grid-template-columns: repeat(2, minmax(0, 1fr)); }
.replay-delta-list article { display: grid; gap: 4px; padding: 10px; background: #fff7ef; border: 1px solid #ecd9c4; border-left: 2px solid #c46d3e; }
.replay-delta-list span { color: #b3643d; font: 700 9px/1 'DIN Alternate', sans-serif; }
.replay-delta-list strong { color: #4b5558; font-size: 11px; }
.replay-delta-list small { color: #9a765f; font-size: 9px; }
.replay-node-detail-list article,
.replay-frame-list article { display: grid; grid-template-columns: 62px minmax(0, 1fr) auto; gap: 10px; align-items: center; padding: 9px 10px; background: #f6f9fa; border: 1px solid #dfe8ea; }
.replay-node-detail-list article.changed { border-left: 3px solid #d07845; }
.replay-node-detail-list span,
.replay-frame-list > article > span { color: #16889a; font: 700 9px/1 'DIN Alternate', sans-serif; }
.replay-node-detail-list strong,
.replay-node-detail-list small,
.replay-frame-list strong,
.replay-frame-list small { display: block; }
.replay-node-detail-list strong,
.replay-frame-list strong { color: #36525d; font-size: 11px; }
.replay-node-detail-list small,
.replay-frame-list small { margin-top: 3px; color: #82949b; font-size: 9px; }
.replay-node-detail-list em,
.replay-frame-list em { color: #93684e; font-size: 9px; font-style: normal; }

.fault-report-panel { border-top: 3px solid #a33b36; }
.fault-report-heading-actions { display: flex; gap: 12px; align-items: center; color: #738892; font-size: 12px; }
.fault-report-heading-actions b { color: #a33b36; font: 700 18px/1 'DIN Alternate', sans-serif; }
.fault-report-scoreboard { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 8px; margin-bottom: 12px; }
.fault-report-scoreboard article { position: relative; display: grid; gap: 5px; overflow: hidden; padding: 13px 14px; background: #f6f8f8; border: 1px solid #dfe7e8; border-radius: 3px; }
.fault-report-scoreboard article::before { position: absolute; inset: 0 auto 0 0; width: 3px; content: ''; background: #70858c; }
.fault-report-scoreboard article.active::before { background: #c47a35; }
.fault-report-scoreboard article.danger { background: #fff2f0; border-color: #edcbc7; }
.fault-report-scoreboard article.danger::before { background: #b63e38; }
.fault-report-scoreboard small { color: #71868e; font: 700 9px/1 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.fault-report-scoreboard strong { color: #1d3f4b; font: 700 25px/1 'DIN Alternate', sans-serif; }
.fault-report-scoreboard span { color: #8a9a9f; font-size: 9px; }
.fault-report-workbench { display: grid; grid-template-columns: 300px minmax(0, 1fr); gap: 10px; min-height: 430px; padding: 10px; margin-bottom: 12px; color: #e4eef0; background: #17252a; border: 1px solid #33484d; border-radius: 4px; }
.fault-report-template-rail { display: grid; align-content: start; gap: 8px; padding-right: 10px; border-right: 1px solid #354a4f; }
.fault-report-template-rail article { padding: 10px; background: #1f3035; border: 1px solid #3a5056; }
.fault-report-template-rail header { display: grid; grid-template-columns: auto 1fr auto; gap: 8px; align-items: center; }
.fault-report-template-rail header span { padding: 3px 5px; color: #ffe1b9; font: 700 9px/1 'DIN Alternate', sans-serif; background: #735233; }
.fault-report-template-rail header strong { color: #eef6f7; font-size: 11px; }
.fault-report-template-rail header em { color: #e3a76f; font-size: 9px; font-style: normal; }
.fault-report-template-rail article > div { display: grid; gap: 4px; margin-top: 9px; }
.fault-report-template-rail article > div span { color: #8fa5aa; font-size: 9px; }
.fault-report-command-center { display: grid; align-content: start; gap: 12px; min-width: 0; }
.fault-report-command-center > header { display: flex; justify-content: space-between; gap: 14px; padding: 13px 15px; background: linear-gradient(118deg, #26393e, #213034); border-left: 3px solid #c96756; }
.fault-report-command-center h3 { margin: 4px 0; color: #fff; font-size: 17px; }
.fault-report-command-center header > div:first-child > span { color: #92a7ac; font-size: 10px; }
.fault-report-level { display: grid; min-width: 100px; text-align: right; }
.fault-report-level small { color: #879ba0; font: 700 8px/1 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.fault-report-level strong { margin: 5px 0; color: #e0a25d; font-size: 16px; }
.fault-report-level.level_1 strong { color: #ff746b; }
.fault-report-level em { color: #a6b8bc; font-size: 9px; font-style: normal; }
.fault-report-stage-line { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); }
.fault-report-stage-line article { position: relative; display: grid; gap: 4px; padding: 11px; background: #1d2d32; border: 1px solid #34494f; border-left: 0; }
.fault-report-stage-line article:first-child { border-left: 1px solid #34494f; }
.fault-report-stage-line article::after { position: absolute; top: 17px; right: -5px; z-index: 1; width: 8px; height: 8px; content: ''; background: #1d2d32; border-top: 1px solid #52666a; border-right: 1px solid #52666a; transform: rotate(45deg); }
.fault-report-stage-line article:last-child::after { display: none; }
.fault-report-stage-line article.done { background: #1b3d38; }
.fault-report-stage-line article.current { background: #50362f; border-color: #946253; }
.fault-report-stage-line span { color: #789096; font: 700 10px/1 'DIN Alternate', sans-serif; }
.fault-report-stage-line strong { color: #dce9eb; font-size: 10px; }
.fault-report-stage-line small { color: #80959a; font-size: 8px; }
.fault-report-runtime { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 7px; }
.fault-report-runtime > div { display: grid; gap: 4px; padding: 10px; background: #202f34; border: 1px solid #34464b; }
.fault-report-runtime span { color: #789096; font: 700 8px/1 'DIN Alternate', sans-serif; letter-spacing: 1px; }
.fault-report-runtime strong { color: #edf6f7; font: 700 17px/1.2 'DIN Alternate', sans-serif; }
.fault-report-runtime small { color: #83969a; font-size: 8px; }
.fault-report-runtime .overdue strong { color: #ff746b; }
.fault-report-quick-actions { display: flex; flex-wrap: wrap; gap: 7px; }
.fault-report-filter-bar { grid-template-columns: repeat(4, minmax(120px, 0.7fr)) minmax(200px, 1.2fr) auto auto; }
.fault-report-link { display: flex; gap: 9px; align-items: center; width: 100%; color: inherit; text-align: left; background: none; border: 0; cursor: pointer; }
.fault-report-link > span { display: grid; flex: 0 0 34px; height: 34px; place-items: center; color: #fff; font: 700 11px/1 'DIN Alternate', sans-serif; background: #657c83; border-radius: 2px; }
.fault-report-link > span.level_1 { background: #b63e38; }
.fault-report-link > span.level_2 { background: #c57136; }
.fault-report-link > span.level_3 { background: #367a8c; }
.fault-report-link strong, .fault-report-link small { display: block; }
.fault-report-link small, .table-subtext { margin-top: 3px; color: #84959c; font-size: 10px; }
.countdown-cell { color: #397666; font: 700 11px/1 'DIN Alternate', sans-serif; }
.countdown-cell.overdue, .text-danger { color: #b63e38 !important; }
.fault-report-command { background: linear-gradient(122deg, #1f3035, #45312d); }
.fault-report-drawer-status { display: grid; align-content: center; gap: 4px; min-width: 110px; text-align: right; }
.fault-report-drawer-status strong { color: #f3b273; font-size: 19px; }
.fault-report-drawer-status.level_1 strong { color: #ff7d75; }
.fault-report-drawer-status span { color: rgba(255, 255, 255, 0.7); font-size: 10px; }
.fault-report-form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 12px; }
.fault-report-form-grid label { display: grid; gap: 6px; }
.fault-report-form-grid label > span { color: #607983; font-size: 11px; }
.fault-report-form-grid .wide { grid-column: 1 / -1; }
.fault-report-template-preview { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); margin-top: 14px; }
.fault-report-template-preview > span { display: grid; gap: 4px; padding: 10px; color: #36515c; font-size: 10px; border: 1px solid #dce7e9; border-left: 0; }
.fault-report-template-preview > span:first-child { border-left: 1px solid #dce7e9; }
.fault-report-template-preview b { color: #a45843; font: 700 16px/1 'DIN Alternate', sans-serif; }
.fault-report-template-preview small { color: #8a9ba1; font-size: 8px; }
.fault-report-detail-stages, .fault-report-event-list, .fault-report-attachment-list { display: grid; gap: 7px; }
.fault-report-detail-stages article { display: grid; grid-template-columns: 34px minmax(0, 1fr) auto; gap: 10px; align-items: center; padding: 10px; background: #f6f8f8; border: 1px solid #dfe7e8; border-left: 3px solid #98aaaf; }
.fault-report-detail-stages article.done { border-left-color: #368977; }
.fault-report-detail-stages article.current { background: #fff5ed; border-left-color: #c66b3d; }
.fault-report-detail-stages article > span { color: #82969d; font: 700 16px/1 'DIN Alternate', sans-serif; }
.fault-report-detail-stages strong, .fault-report-detail-stages small { display: block; }
.fault-report-detail-stages strong { color: #344f59; font-size: 11px; }
.fault-report-detail-stages small { margin-top: 3px; color: #87989e; font-size: 9px; }
.fault-report-detail-stages em { color: #a46a4d; font: 700 9px/1 'DIN Alternate', sans-serif; font-style: normal; }
.fault-report-action-form { display: grid; grid-template-columns: 200px 180px minmax(0, 1fr) auto; gap: 8px; align-items: start; }
.fault-report-action-form .el-textarea { min-width: 220px; }
.fault-report-event-list article, .fault-report-attachment-list article { display: grid; grid-template-columns: 42px minmax(0, 1fr) auto; gap: 10px; align-items: center; padding: 9px 10px; background: #f7f9f9; border: 1px solid #dfe8e9; }
.fault-report-event-list article > span, .fault-report-attachment-list article > span { color: #a35b43; font: 700 10px/1 'DIN Alternate', sans-serif; }
.fault-report-event-list strong, .fault-report-event-list small, .fault-report-attachment-list strong, .fault-report-attachment-list small { display: block; }
.fault-report-event-list strong, .fault-report-attachment-list strong { color: #36515b; font-size: 11px; }
.fault-report-event-list small, .fault-report-attachment-list small { margin-top: 3px; color: #84969c; font-size: 9px; }
.fault-report-event-list p { margin: 3px 0 0; color: #71858c; font-size: 9px; }
.fault-report-attachment-list em { color: #7e9198; font-size: 9px; font-style: normal; }
.quality-check-list,
.lineage-source-list {
  display: grid;
  gap: 9px;
}
.quality-check-list article,
.lineage-source-list article {
  display: flex;
  gap: 12px;
  align-items: center;
  padding: 12px 13px;
  background: #f8fbfb;
  border: 1px solid #e0eaed;
  border-radius: 8px;
}
.quality-check-list article > span,
.lineage-source-list article > span {
  min-width: 58px;
  color: #b05f2b;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.4px;
}
.quality-check-list article.passed > span {
  color: #17866f;
}
.quality-check-list strong,
.quality-check-list small,
.lineage-source-list strong,
.lineage-source-list small {
  display: block;
}
.quality-check-list small,
.lineage-source-list small {
  margin-top: 3px;
  color: #7c919b;
}
.source-count-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 9px;
}
.source-count-grid > div {
  padding: 12px;
  background: #f6fbfc;
  border: 1px solid #e0eaed;
  border-radius: 8px;
}
.source-count-grid span,
.source-count-grid strong {
  display: block;
}
.source-count-grid span {
  color: #708894;
  font-size: 12px;
}
.source-count-grid strong {
  margin-top: 6px;
  color: #17364b;
  font:
    700 22px/1 'DIN Alternate',
    sans-serif;
}

.simulation-form-intro,
.simulation-command {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
  color: #f5fcff;
  background:
    radial-gradient(circle at 83% 18%, rgba(92, 224, 190, 0.25), transparent 31%),
    linear-gradient(125deg, #102f43, #176c64);
  border-radius: 10px;
}
.simulation-form-intro h3,
.simulation-command h3 {
  margin: 5px 0;
  font-size: 22px;
}
.simulation-form-intro p:last-child,
.simulation-command p:last-child {
  margin: 0;
  color: rgba(255, 255, 255, 0.7);
}
.simulation-form-intro > span {
  flex-shrink: 0;
  padding: 7px 10px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.18);
}
.simulation-base-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.simulation-base-grid label,
.rule-fields label {
  display: grid;
  gap: 5px;
  min-width: 0;
  color: #69818c;
  font-size: 11px;
}
.simulation-base-grid .wide-field {
  grid-column: 1 / -1;
}
.simulation-base-grid :deep(.el-select),
.simulation-base-grid :deep(.el-date-editor),
.simulation-base-grid :deep(.el-input-number),
.rule-fields :deep(.el-select),
.rule-fields :deep(.el-input-number) {
  width: 100%;
}
.simulation-rule-list {
  display: grid;
  gap: 9px;
}
.simulation-rule-card {
  display: grid;
  grid-template-columns: 34px 1fr auto;
  gap: 12px;
  align-items: start;
  padding: 13px;
  background: #f7fafb;
  border: 1px solid #dfe9eb;
  border-left: 3px solid #2b9a83;
  border-radius: 7px;
}
.rule-number {
  color: #98abb3;
  font: 700 16px/1.9 'DIN Alternate', sans-serif;
}
.rule-fields {
  display: grid;
  grid-template-columns: 1.1fr 1.2fr 0.65fr 1fr repeat(5, 0.72fr);
  gap: 8px;
}
.drawer-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.drawer-footer > span {
  color: #7e929b;
  font-size: 12px;
}
.simulation-command-meta {
  display: grid;
  justify-items: end;
  gap: 5px;
  flex-shrink: 0;
}
.simulation-command-meta strong {
  font: 700 31px/1 'DIN Alternate', sans-serif;
}
.simulation-command-meta span {
  color: rgba(255, 255, 255, 0.66);
  font-size: 11px;
}
.trend-heading {
  align-items: flex-end;
}
.trend-actions :deep(.el-select) {
  width: 210px;
}
.trend-stat-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 1px;
  margin-bottom: 11px;
  overflow: hidden;
  background: #dce8e9;
  border: 1px solid #dce8e9;
  border-radius: 7px;
}
.trend-stat-grid > div {
  padding: 12px 14px;
  background: #f9fbfb;
}
.trend-stat-grid span,
.trend-stat-grid strong,
.trend-stat-grid small {
  display: block;
}
.trend-stat-grid span,
.trend-stat-grid small {
  color: #7c919a;
  font-size: 11px;
}
.trend-stat-grid strong {
  margin: 6px 0 3px;
  color: #163c50;
  font: 700 20px/1.1 'DIN Alternate', sans-serif;
}
.trend-stat-grid strong.up {
  color: #17816f;
}
.trend-stat-grid strong.down {
  color: #cc6640;
}
.trend-chart {
  position: relative;
  padding: 12px 14px 8px 42px;
  background: linear-gradient(180deg, #f7fbfa, #fff);
  border: 1px solid #e0eaeb;
  border-radius: 8px;
}
.trend-chart svg {
  display: block;
  width: 100%;
  height: 230px;
  overflow: visible;
}
.chart-grid-line {
  stroke: #dfe9e9;
  stroke-dasharray: 4 5;
  stroke-width: 1;
}
.chart-area {
  fill: rgba(41, 155, 130, 0.12);
}
.chart-line {
  fill: none;
  stroke: #218f79;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3;
  vector-effect: non-scaling-stroke;
}
.chart-y-labels {
  position: absolute;
  inset: 28px auto 47px 9px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  color: #81959d;
  font-size: 10px;
}
.chart-x-labels {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  color: #81959d;
  font-size: 10px;
}
.chart-x-labels b {
  color: #376171;
}

.complaint-panel {
  margin-top: 14px;
  margin-bottom: 24px;
}
.complaint-heading {
  margin-bottom: 12px;
}
.header-actions {
  display: flex;
  gap: 8px;
}
.filter-bar {
  display: grid;
  grid-template-columns: 1.3fr repeat(4, minmax(105px, 0.7fr)) 1.4fr auto;
  gap: 8px;
  padding: 12px;
  margin-bottom: 12px;
  background: #f5f8f9;
  border: 1px solid #e4ecee;
  border-radius: 8px;
}
.customer-cell strong,
.customer-cell span {
  display: block;
}
.customer-cell span {
  margin-top: 3px;
  color: #84969e;
  font-size: 11px;
}
.severity-dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  margin-right: 5px;
  border-radius: 50%;
  background: #76a595;
}
.severity-dot.medium {
  background: #d0a139;
}
.severity-dot.high {
  background: #de793d;
}
.severity-dot.critical {
  background: #cf4141;
  box-shadow: 0 0 0 3px rgba(207, 65, 65, 0.12);
}
.pagination-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 14px;
  color: #84959d;
  font-size: 12px;
}

.drawer-scroll {
  height: 100%;
  min-height: 0;
  overflow-y: auto;
  padding: 0 4px 24px 0;
}
.instance-command {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
  padding: 22px;
  color: white;
  background: linear-gradient(125deg, #123247, #17645f);
  border-radius: 10px;
}
.instance-command h3 {
  margin: 5px 0;
  font-size: 22px;
}
.instance-command > div > p:last-child {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
}
.instance-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  margin: 12px 0;
  overflow: hidden;
  background: #dae7e9;
  border: 1px solid #dae7e9;
  border-radius: 8px;
}
.instance-stats div {
  padding: 13px;
  text-align: center;
  background: white;
}
.instance-stats strong,
.instance-stats span {
  display: block;
}
.instance-stats strong {
  color: #153b50;
  font:
    700 22px/1.1 'DIN Alternate',
    sans-serif;
}
.instance-stats span {
  margin-top: 4px;
  color: #81939b;
  font-size: 11px;
}
.drawer-section {
  padding: 18px;
  margin-top: 12px;
  background: #fff;
  border: 1px solid #e0eaec;
  border-radius: 9px;
}
.drawer-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}
.drawer-heading h3 {
  margin: 3px 0 0;
  font-size: 16px;
}
.control-actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: #81939c;
  font-size: 12px;
}
.generator-grid {
  display: grid;
  grid-template-columns: minmax(180px, 1.4fr) 120px minmax(200px, 1.2fr) 120px;
  gap: 8px;
}
.generator-grid > :deep(.el-button) {
  grid-column: 1 / -1;
  justify-self: end;
}
.process-generator {
  display: grid;
  grid-template-columns: minmax(180px, 1fr) minmax(180px, 1fr) auto auto;
  gap: 8px;
  align-items: center;
}
.auto-switch {
  display: flex;
  align-items: center;
  gap: 7px;
  color: #647e8a;
  font-size: 12px;
  white-space: nowrap;
}
.instance-process-list {
  display: grid;
  gap: 7px;
  margin-top: 12px;
}
.instance-process-list > button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 11px 12px;
  color: #17364b;
  text-align: left;
  background: #f7fafb;
  border: 1px solid #e1eaec;
  border-radius: 7px;
  cursor: pointer;
}
.instance-process-list strong,
.instance-process-list small {
  display: block;
}
.instance-process-list small {
  margin-top: 3px;
  color: #82959e;
}
.process-command {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
  color: #f5fcff;
  background:
    radial-gradient(circle at 82% 20%, rgba(88, 218, 185, 0.24), transparent 34%),
    linear-gradient(125deg, #102d40, #165b5a);
  border-radius: 10px;
}
.process-command h3 {
  margin: 5px 0;
  font-size: 22px;
}
.process-command p:last-child {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
}
.process-command-status {
  display: grid;
  justify-items: end;
  gap: 8px;
}
.process-command-status strong {
  font:
    700 31px/1 'DIN Alternate',
    sans-serif;
}
.process-control :deep(.el-progress) {
  margin-bottom: 12px;
}
.blocked-reason {
  padding: 9px 11px;
  margin-bottom: 10px;
  color: #92591f;
  font-size: 12px;
  background: #fff7e9;
  border-left: 3px solid #d9923e;
}
.process-operation-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}
.process-actions {
  padding-top: 2px;
}
.process-step-list {
  display: grid;
  gap: 8px;
}
.process-step-card {
  display: grid;
  grid-template-columns: 42px 1fr;
  gap: 12px;
  padding: 13px;
  background: #f8fafb;
  border: 1px solid #e1eaec;
  border-left: 3px solid #c9d7dc;
  border-radius: 7px;
}
.process-step-card.running {
  background: #eff9f6;
  border-left-color: #2b9b83;
}
.process-step-card.blocked {
  background: #fff8ed;
  border-left-color: #d38b35;
}
.process-step-card.completed {
  border-left-color: #78ac9e;
}
.process-step-card.failed {
  border-left-color: #cf4b4b;
}
.process-step-index {
  color: #9aadb5;
  font:
    700 18px/1.4 'DIN Alternate',
    sans-serif;
}
.process-step-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.process-step-card p {
  margin: 5px 0;
  color: #657f8a;
  font-size: 12px;
}
.process-step-card small {
  color: #8a9ca4;
}
.process-step-card em {
  display: block;
  margin-top: 6px;
  color: #4d6976;
  font-size: 11px;
  font-style: normal;
}
.helper-text {
  margin: 10px 0 0;
  color: #8a9ca4;
  font-size: 11px;
}
.event-section :deep(.el-timeline-item__content p) {
  margin: 4px 0 0;
  color: #84969e;
  font-size: 12px;
}

.scene-library-panel {
  margin-top: 14px;
  background:
    radial-gradient(circle at 88% 0%, rgba(89, 126, 194, 0.1), transparent 34%),
    rgba(255, 255, 255, 0.97);
  border-top: 3px solid #5872a6;
}
.library-heading,
.library-summary {
  display: flex;
  align-items: center;
  gap: 12px;
}
.library-heading {
  justify-content: space-between;
}
.library-summary {
  flex-wrap: wrap;
  justify-content: flex-end;
}
.library-summary > span {
  color: #6c8190;
  font-size: 12px;
}
.library-summary b {
  margin-right: 3px;
  color: #425d91;
  font-size: 18px;
}
.library-flow-strip {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 9px;
  margin-bottom: 12px;
}
.library-flow-strip article {
  padding: 13px 14px;
  background: #f6f8fd;
  border: 1px solid #dce4f2;
  border-radius: 8px;
}
.library-flow-strip span,
.library-flow-strip strong,
.library-flow-strip small {
  display: block;
}
.library-flow-strip span {
  color: #7c8fb2;
  font:
    700 16px/1 'DIN Alternate',
    sans-serif;
}
.library-flow-strip strong {
  margin: 6px 0 4px;
  color: #223b62;
  font-size: 14px;
}
.library-flow-strip small {
  color: #75869a;
  line-height: 1.45;
}
.library-script-rail {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.library-script-card {
  border-left-color: #5b74ab;
}
.library-filter-bar {
  grid-template-columns: repeat(3, minmax(135px, 1fr)) minmax(180px, 1.3fr) auto auto;
}
.library-command {
  background:
    radial-gradient(circle at 82% 20%, rgba(130, 162, 226, 0.26), transparent 34%),
    linear-gradient(125deg, #172a49, #49669c);
}
.library-link-grid,
.scene-library-form-grid,
.scene-library-run-grid {
  display: grid;
  gap: 12px;
}
.library-link-grid {
  grid-template-columns: repeat(4, minmax(0, 1fr));
}
.library-link-grid > div {
  padding: 13px;
  background: #f6f8fd;
  border: 1px solid #dfe6f2;
  border-radius: 8px;
}
.library-link-grid span,
.library-link-grid strong {
  display: block;
}
.library-link-grid span {
  color: #71839b;
  font-size: 12px;
}
.library-link-grid strong {
  margin-top: 5px;
  color: #223b62;
  word-break: break-all;
}
.scene-library-form-grid {
  grid-template-columns: repeat(2, minmax(0, 1fr));
}
.scene-library-form-grid label,
.scene-library-run-grid label {
  display: grid;
  gap: 6px;
  color: #607986;
  font-size: 12px;
}
.scene-library-form-grid .wide-field,
.scene-library-run-grid .wide-field {
  grid-column: 1 / -1;
}
.scene-library-run-grid {
  grid-template-columns: repeat(3, minmax(0, 1fr));
}
.library-switch {
  align-items: center;
  grid-template-columns: auto 1fr;
  padding: 12px;
  background: #f7fafc;
  border: 1px solid #e0e8f1;
  border-radius: 8px;
}

.scene-panel {
  margin-top: 14px;
  border-top: 3px solid #385b82;
}
.scene-heading,
.scene-summary {
  display: flex;
  align-items: center;
  gap: 14px;
}
.scene-heading {
  justify-content: space-between;
}
.scene-summary > span {
  color: #6d8290;
  font-size: 12px;
}
.scene-summary b {
  margin-right: 3px;
  color: #173a55;
  font-size: 18px;
}
.scene-summary .warning b {
  color: #bd742c;
}
.scene-script-rail {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0;
}
.scene-script-card {
  display: grid;
  gap: 7px;
  padding: 15px;
  color: #183b53;
  text-align: left;
  background: linear-gradient(145deg, #f9fbfc, #f1f6f8);
  border: 1px solid #dbe6ea;
  border-left: 4px solid #7890aa;
  border-radius: 8px;
  cursor: pointer;
}
.scene-script-card:hover,
.scene-script-card.active {
  background: #edf4f8;
  border-color: #507291;
  box-shadow: 0 7px 18px rgba(45, 75, 101, 0.1);
}
.scene-script-card > span,
.scene-script-card small {
  color: #82949e;
  font-size: 11px;
}
.scene-script-card strong {
  font-size: 15px;
}
.scene-script-card p {
  min-height: 36px;
  margin: 0;
  color: #607b89;
  font-size: 12px;
  line-height: 1.5;
}
.scene-filter-bar {
  grid-template-columns: repeat(3, minmax(135px, 1fr)) minmax(180px, 1.3fr) auto auto;
}
.scene-form-intro {
  background: linear-gradient(125deg, #132f45, #385d73);
}
.scene-script-base-grid,
.scene-create-form {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 13px;
}
.scene-script-base-grid label,
.scene-create-form label {
  display: grid;
  gap: 6px;
  color: #607986;
  font-size: 12px;
}
.scene-script-base-grid .wide-field {
  grid-column: 1 / -1;
}
.scene-step-editor-list {
  display: grid;
  gap: 9px;
}
.scene-step-editor {
  display: grid;
  grid-template-columns: 36px 1fr auto;
  gap: 10px;
  align-items: start;
  padding: 12px;
  background: #f7fafb;
  border: 1px solid #e0e9ec;
  border-radius: 7px;
}
.scene-step-editor > span {
  color: #8aa0ab;
  font: 700 16px/32px 'DIN Alternate', sans-serif;
}
.scene-step-editor > div,
.scene-step-editor-row {
  display: grid;
  gap: 8px;
}
.scene-step-editor-row {
  grid-template-columns: minmax(150px, 0.7fr) minmax(180px, 1.3fr);
}
.injection-checklist,
.injection-metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 9px;
}
.injection-checklist .drawer-heading {
  grid-column: 1 / -1;
}
.injection-checklist > div:not(.drawer-heading),
.injection-metrics > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f5f8fa;
  border: 1px solid #e1e9ec;
  border-radius: 6px;
}
.injection-checklist span,
.injection-metrics span {
  color: #6f8490;
  font-size: 12px;
}
.injection-checklist strong,
.injection-metrics strong {
  color: #244b67;
  font-size: 21px;
}
.scene-command {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
  color: #f5fbff;
  background:
    radial-gradient(circle at 80% 18%, rgba(126, 169, 207, 0.27), transparent 32%),
    linear-gradient(125deg, #102b41, #385f78);
  border-radius: 10px;
}
.scene-command h3 {
  margin: 5px 0;
  font-size: 22px;
}
.scene-command p:last-child {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
}
.scene-conclusion {
  color: #31556c;
  background: #f2f8f9;
  border-left: 4px solid #4e8c8b;
}
.scene-conclusion > p {
  margin: 0 0 7px;
  line-height: 1.65;
}
.scene-conclusion > small {
  color: #758c97;
}
.work-order-create {
  display: grid;
  grid-template-columns: minmax(180px, 1.5fr) 100px minmax(140px, 1fr) minmax(180px, 1.5fr) auto;
  gap: 8px;
  margin-bottom: 12px;
}
.work-order-list {
  display: grid;
  gap: 8px;
}
.work-order-list > article {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 12px 13px;
  background: #f8fafb;
  border: 1px solid #e1e9ec;
  border-radius: 7px;
}
.work-order-list > article > div:first-child > div {
  display: flex;
  align-items: center;
  gap: 8px;
}
.work-order-list p,
.work-order-list small {
  display: block;
  margin: 5px 0 0;
  color: #758a95;
  font-size: 11px;
}
.work-order-actions {
  display: flex;
  flex-shrink: 0;
}

.alert-panel {
  margin-top: 14px;
  background:
    linear-gradient(105deg, rgba(190, 55, 45, 0.045), transparent 38%),
    rgba(255, 255, 255, 0.98);
  border-top: 3px solid #b8493f;
}
.alert-heading,
.alert-summary {
  display: flex;
  align-items: center;
  gap: 14px;
}
.alert-heading {
  justify-content: space-between;
}
.alert-summary > span {
  color: #728691;
  font-size: 12px;
}
.alert-summary b {
  margin-right: 3px;
  font-size: 18px;
}
.alert-summary .pending b {
  color: #8d6b38;
}
.alert-summary .active b {
  color: #b83d35;
}
.alert-summary .recovered b {
  color: #23806d;
}
.alert-template-rail {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0;
}
.alert-template-card {
  display: grid;
  gap: 7px;
  padding: 15px;
  color: #3f302f;
  text-align: left;
  background: linear-gradient(145deg, #fffafa, #f7f3f2);
  border: 1px solid #eadfdd;
  border-left: 4px solid #c65b50;
  border-radius: 8px;
  cursor: pointer;
}
.alert-template-card:hover,
.alert-template-card.active {
  background: #fbefed;
  border-color: #bd5b51;
  box-shadow: 0 7px 18px rgba(130, 55, 48, 0.1);
}
.alert-template-card > span,
.alert-template-card small {
  color: #958581;
  font-size: 11px;
}
.alert-template-card p {
  min-height: 36px;
  margin: 0;
  color: #746763;
  font-size: 12px;
  line-height: 1.5;
}
.alert-filter-bar {
  grid-template-columns: repeat(4, minmax(125px, 1fr)) minmax(170px, 1.2fr) auto auto;
}
.alert-command {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
  padding: 22px;
  color: #fff8f7;
  background:
    radial-gradient(circle at 82% 15%, rgba(255, 183, 143, 0.2), transparent 34%),
    linear-gradient(125deg, #3c2525, #813f3a);
  border-radius: 10px;
}
.alert-command h3 {
  margin: 5px 0;
  font-size: 22px;
}
.alert-command p:last-child {
  margin: 0;
  color: rgba(255, 255, 255, 0.68);
}
.alert-command > span {
  padding: 8px 12px;
  color: #ffe7e3;
  font-size: 12px;
  border: 1px solid rgba(255, 255, 255, 0.26);
}
.template-command {
  background: linear-gradient(125deg, #273846, #5b4a46);
}
.alert-template-base-grid,
.alert-create-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.alert-template-base-grid label,
.alert-create-grid label {
  display: grid;
  gap: 6px;
  color: #667c87;
  font-size: 12px;
}
.alert-template-base-grid .wide-field,
.alert-create-grid .wide-field {
  grid-column: 1 / -1;
}
.alert-rule-list {
  display: grid;
  gap: 9px;
}
.alert-rule-card {
  display: grid;
  grid-template-columns: 34px 1fr auto;
  gap: 10px;
  align-items: start;
  padding: 12px;
  background: #fbf8f7;
  border: 1px solid #eadfdd;
  border-radius: 7px;
}
.alert-rule-card > span {
  color: #a98a84;
  font: 700 16px/32px 'DIN Alternate', sans-serif;
}
.alert-rule-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(110px, 1fr));
  gap: 8px;
}
.detail-command > div:last-child {
  display: grid;
  justify-items: end;
  gap: 5px;
}
.detail-command > div:last-child > strong {
  font: 700 30px/1 'DIN Alternate', sans-serif;
}
.detail-command > div:last-child > small {
  color: rgba(255, 255, 255, 0.68);
}
.alert-operate-grid {
  display: grid;
  grid-template-columns: 1fr 180px;
  gap: 8px;
  margin-bottom: 10px;
}
.alert-facts {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.alert-facts > div {
  display: grid;
  gap: 5px;
  padding: 12px;
  background: #f7f9fa;
  border: 1px solid #e1e8eb;
  border-radius: 6px;
}
.alert-facts span,
.alert-facts strong {
  font-size: 12px;
}
.alert-facts span {
  color: #83959e;
}
.timeline-counts {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 12px;
}
.timeline-counts span {
  padding: 4px 8px;
  color: #637b87;
  font-size: 11px;
  background: #eef3f5;
  border-radius: 999px;
}
.unified-timeline-list {
  display: grid;
}
.unified-timeline-list article {
  display: grid;
  grid-template-columns: 150px 14px 1fr;
  gap: 10px;
  min-height: 70px;
}
.unified-timeline-list time {
  padding-top: 4px;
  color: #82959e;
  font-size: 11px;
  text-align: right;
}
.unified-timeline-list article > span {
  position: relative;
  width: 10px;
  height: 10px;
  margin-top: 4px;
  background: #7c929d;
  border: 2px solid white;
  border-radius: 50%;
  box-shadow: 0 0 0 1px #b8c7cd;
}
.unified-timeline-list article > span::after {
  position: absolute;
  top: 10px;
  left: 3px;
  width: 1px;
  height: 56px;
  content: '';
  background: #dce5e8;
}
.unified-timeline-list article:last-child > span::after {
  display: none;
}
.unified-timeline-list article.alert > span {
  background: #bd4b42;
}
.unified-timeline-list article.metric > span {
  background: #278977;
}
.unified-timeline-list article > div {
  display: grid;
  align-content: start;
  gap: 3px;
}
.unified-timeline-list small {
  color: #9a746d;
  font-size: 10px;
  letter-spacing: 0.8px;
}
.unified-timeline-list strong {
  color: #294657;
  font-size: 13px;
}
.unified-timeline-list p {
  margin: 0;
  color: #80929b;
  font-size: 11px;
}
.scene-alert-list {
  display: grid;
  gap: 7px;
  margin-bottom: 10px;
}
.scene-alert-list button {
  display: grid;
  grid-template-columns: 4px 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 10px;
  color: #2d4756;
  text-align: left;
  background: #faf8f7;
  border: 1px solid #ebe1df;
  border-radius: 6px;
  cursor: pointer;
}
.scene-alert-list button > span {
  align-self: stretch;
  background: #c9864d;
}
.scene-alert-list button > span.severity-high,
.scene-alert-list button > span.severity-critical {
  background: #bd4b42;
}
.scene-alert-list strong,
.scene-alert-list small {
  display: block;
}
.scene-alert-list small {
  margin-top: 3px;
  color: #81939c;
  font-size: 11px;
}

.auxiliary-simulation-panel {
  background:
    radial-gradient(circle at 92% 0%, rgb(225 113 82 / 12%), transparent 32%),
    linear-gradient(145deg, #fbfcf9 0%, #f3f8f5 100%);
  border-color: #cbdad4;
}
.auxiliary-heading-actions { display: flex; align-items: center; gap: 16px; color: #536663; }
.auxiliary-heading-actions b { color: #d36143; font-size: 18px; }
.factor-catalog-grid { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 10px; margin-bottom: 18px; }
.factor-catalog-grid article { min-height: 126px; padding: 14px; border: 1px solid #d8e2de; border-radius: 14px; background: rgb(255 255 255 / 78%); box-shadow: 0 12px 28px rgb(26 64 57 / 5%); }
.factor-catalog-grid article::before { content: ''; display: block; width: 24px; height: 3px; margin-bottom: 12px; border-radius: 3px; background: #167a73; }
.factor-catalog-grid article.fault::before { background: #d36143; }
.factor-catalog-grid article.traffic::before { background: #d39a31; }
.factor-catalog-grid small, .factor-catalog-grid span { display: block; color: #72817e; font-size: 11px; }
.factor-catalog-grid strong { display: block; margin: 7px 0 10px; color: #172f2d; font-size: 16px; }
.factor-catalog-grid p { margin: 0 0 7px; color: #314b48; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.auxiliary-command-center { display: grid; grid-template-columns: 1.05fr 1.45fr; gap: 18px; margin: 18px 0; padding: 22px; border-radius: 18px; color: #edf7f4; background: linear-gradient(135deg, #102f31 0%, #163f3b 65%, #204c43 100%); box-shadow: 0 22px 44px rgb(15 49 48 / 18%); }
.auxiliary-command-copy h3 { margin: 4px 0 8px; color: #fff; font-size: 21px; }
.auxiliary-command-copy > span { display: block; min-height: 46px; color: #bdd2cd; line-height: 1.65; }
.auxiliary-command-copy > div { display: flex; align-items: center; gap: 10px; margin-top: 15px; }
.auxiliary-command-copy > div small { color: #83a69e; font-family: ui-monospace, SFMono-Regular, Menlo, monospace; }
.auxiliary-mini-chart { padding: 12px 14px 8px; border: 1px solid rgb(174 214 204 / 20%); border-radius: 13px; background: rgb(5 28 29 / 36%); }
.auxiliary-mini-chart header, .auxiliary-mini-chart footer { display: flex; justify-content: space-between; color: #91b3ab; font-size: 10px; letter-spacing: .08em; }
.auxiliary-mini-chart svg { display: block; width: 100%; height: 128px; margin: 6px 0; overflow: visible; }
.auxiliary-mini-chart footer strong { color: #ffb394; font-weight: 700; }
.auxiliary-stats-strip { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; overflow: hidden; border-radius: 10px; background: rgb(255 255 255 / 10%); }
.auxiliary-stats-strip article { padding: 12px 14px; background: rgb(11 41 40 / 72%); }
.auxiliary-stats-strip small, .auxiliary-stats-strip span { display: block; color: #8faca5; font-size: 11px; }
.auxiliary-stats-strip strong { display: block; margin: 4px 0; color: #fff; font-size: 21px; }
.auxiliary-stats-strip .rising, .auxiliary-stat-grid .rising { color: #ef8e70; }
.auxiliary-filter-bar { grid-template-columns: 1.2fr .9fr .75fr 1.2fr auto auto; }
.auxiliary-link { display: flex; align-items: center; gap: 10px; width: 100%; border: 0; background: none; text-align: left; cursor: pointer; }
.auxiliary-link > span { padding: 7px 8px; border-radius: 8px; color: #fff; background: #167a73; font: 700 10px ui-monospace, SFMono-Regular, Menlo, monospace; }
.auxiliary-link i { display: grid; min-width: 0; font-style: normal; }
.auxiliary-link small { overflow: hidden; color: #7b8986; text-overflow: ellipsis; white-space: nowrap; }
.auxiliary-drawer-command > span { padding: 10px 14px; border: 1px solid rgb(255 255 255 / 20%); border-radius: 10px; color: #ffb394; font: 700 14px ui-monospace, SFMono-Regular, Menlo, monospace; }
.auxiliary-base-form { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.auxiliary-base-form label { display: grid; gap: 7px; color: #566966; font-size: 12px; }
.auxiliary-base-form label:nth-child(4) { grid-template-columns: 1fr auto; align-items: end; }
.auxiliary-base-form label:nth-child(4) > span { grid-column: 1 / -1; }
.auxiliary-factor-form-list { display: grid; gap: 12px; }
.auxiliary-factor-form-list article { padding: 15px; border: 1px solid #dfe7e4; border-radius: 14px; background: #f9fbfa; opacity: .65; transition: .2s ease; }
.auxiliary-factor-form-list article.enabled { border-color: #90bcb4; background: #f2f8f6; opacity: 1; box-shadow: 0 10px 24px rgb(26 91 82 / 7%); }
.auxiliary-factor-form-list article header { display: grid; grid-template-columns: auto 1fr auto; align-items: center; gap: 12px; }
.auxiliary-factor-form-list article header div { display: grid; }
.auxiliary-factor-form-list article header small { color: #72817e; font-size: 10px; letter-spacing: .06em; }
.auxiliary-factor-form-list article header em { color: #167a73; font-style: normal; font-weight: 700; }
.auxiliary-factor-form-list article > div { display: grid; grid-template-columns: .9fr .75fr .75fr 1.2fr; gap: 12px; margin-top: 14px; }
.auxiliary-factor-form-list label { display: grid; gap: 6px; color: #697976; font-size: 11px; }
.auxiliary-export-console { display: grid; grid-template-columns: 1fr 118px 132px auto; align-items: end; gap: 12px; border-color: #b7d3cc; background: linear-gradient(135deg, #eef7f4, #fbfcf9); }
.auxiliary-export-console h3 { margin: 2px 0 5px; color: #173d39; }
.auxiliary-export-console span { color: #667a76; font-size: 12px; }
.auxiliary-impact-list { display: grid; gap: 8px; }
.auxiliary-impact-list article { display: grid; grid-template-columns: 36px 1fr; gap: 10px; align-items: start; padding: 11px 13px; border-radius: 10px; background: #f4f8f6; }
.auxiliary-impact-list article span { color: #1c8278; font: 700 12px ui-monospace, SFMono-Regular, Menlo, monospace; }
.auxiliary-impact-list article p { margin: 0; color: #3e5551; line-height: 1.55; }
.auxiliary-stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; }
.auxiliary-stat-grid article { position: relative; padding: 14px; border: 1px solid #dfe7e4; border-radius: 12px; background: #fff; }
.auxiliary-stat-grid small { color: #687b77; }
.auxiliary-stat-grid strong { display: block; margin: 5px 0; color: #183e3a; font-size: 22px; }
.auxiliary-stat-grid p { margin: 0; color: #84918e; font-size: 11px; }
.auxiliary-stat-grid em { position: absolute; top: 14px; right: 14px; color: #1c8278; font-style: normal; font-weight: 700; }
.auxiliary-anomaly-list { display: grid; gap: 8px; }
.auxiliary-anomaly-list article { display: grid; grid-template-columns: 72px 1fr; gap: 12px; padding: 12px; border-left: 3px solid #dc6f50; border-radius: 6px 10px 10px 6px; background: #fff6f2; }
.auxiliary-anomaly-list article > span { color: #c75e42; font: 700 11px ui-monospace, SFMono-Regular, Menlo, monospace; }
.auxiliary-anomaly-list article div { display: grid; gap: 4px; }
.auxiliary-anomaly-list small { color: #8e7770; }

@media (max-width: 1100px) {
  .workspace-nav { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .factor-catalog-grid { grid-template-columns: repeat(3, 1fr); }
  .auxiliary-command-center { grid-template-columns: 1fr; }
  .auxiliary-stats-strip { grid-column: auto; }
  .auxiliary-filter-bar { grid-template-columns: repeat(2, 1fr); }
  .auxiliary-export-console { grid-template-columns: 1fr 1fr; }
  .metric-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .content-grid {
    grid-template-columns: 1fr;
  }
  .simulation-summary {
    flex-wrap: wrap;
    justify-content: flex-end;
  }
  .workflow-steps.fourteen-steps {
    grid-template-columns: repeat(2, 1fr);
  }
  .filter-bar {
    grid-template-columns: repeat(3, 1fr);
  }
  .process-filter-bar,
  .process-generator,
  .library-filter-bar,
  .scene-filter-bar,
    .alert-filter-bar,
    .model-filter-bar,
    .traceback-filter-bar,
    .record-filter-bar,
    .capability-filter-bar,
    .fault-configuration-filter-bar,
    .scene-replay-filter-bar,
    .fault-report-filter-bar,
  .alert-rule-grid,
  .work-order-create {
    grid-template-columns: repeat(2, 1fr);
  }
  .model-flow-strip,
  .traceback-flow-strip,
  .record-scoreboard,
  .capability-scoreboard,
  .fault-scoreboard,
  .scene-replay-scoreboard,
  .fault-report-scoreboard,
  .warroom-rail,
  .library-flow-strip,
  .library-script-rail,
  .library-link-grid,
  .source-count-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .generator-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .capability-workbench {
    grid-template-columns: 1fr;
  }
  .fault-workbench { grid-template-columns: 1fr; }
  .scene-replay-workbench { grid-template-columns: 1fr; }
  .scene-replay-rail { padding-right: 0; border-right: 0; }
  .fault-report-workbench { grid-template-columns: 1fr; }
  .fault-report-template-rail { padding-right: 0; border-right: 0; }
  .fault-report-action-form { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .fault-validation-grid { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .topology-nodes { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .rule-fields {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .factor-catalog-grid,
  .auxiliary-stats-strip,
  .auxiliary-base-form,
  .auxiliary-factor-form-list article > div,
  .auxiliary-stat-grid,
  .auxiliary-filter-bar,
  .auxiliary-export-console { grid-template-columns: 1fr; }
  .auxiliary-heading-actions { align-items: flex-start; flex-direction: column; }
  .rehearsal-page {
    padding: 12px;
  }
  .command-hero {
    align-items: flex-start;
    flex-direction: column;
    padding: 24px;
  }
  .command-hero h1 {
    font-size: 27px;
  }
  .workspace-nav {
    position: static;
    grid-template-columns: 1fr;
  }
  .module-nav {
    position: static;
    grid-auto-columns: minmax(150px, 72vw);
    grid-auto-flow: column;
    grid-template-columns: none;
    overflow-x: auto;
    padding-bottom: 4px;
  }
  .metric-grid,
  .workflow-steps,
  .instance-stats {
    grid-template-columns: repeat(2, 1fr);
  }
  .workflow-step:nth-child(3) {
    border-left: 0;
  }
  .workflow-steps.fourteen-steps {
    grid-template-columns: 1fr;
  }
  .workflow-steps.fourteen-steps .workflow-step {
    padding-left: 0;
    border-left: 0;
    border-top: 1px dashed #c7d7dc;
  }
  .workflow-steps.fourteen-steps .workflow-step:first-child {
    border-top: 0;
  }
  .filter-bar,
  .generator-grid,
  .process-filter-bar,
  .process-generator,
  .process-operation-form,
  .process-template-rail,
  .library-filter-bar,
  .library-flow-strip,
  .library-script-rail,
  .library-link-grid,
  .scene-library-form-grid,
  .scene-library-run-grid,
  .scene-filter-bar,
  .scene-script-rail,
  .scene-script-base-grid,
  .scene-create-form,
  .scene-step-editor-row,
  .injection-checklist,
  .injection-metrics,
  .work-order-create,
    .model-flow-strip,
    .traceback-flow-strip,
    .traceback-form-grid,
    .traceback-summary-grid,
    .traceback-node-grid,
    .record-scoreboard,
    .record-filter-bar,
    .record-result-grid,
    .record-source-grid,
    .capability-scoreboard,
    .capability-filter-bar,
    .fault-configuration-filter-bar,
    .scene-replay-filter-bar,
    .fault-report-filter-bar,
    .warroom-rail,
    .sandbox-grid,
    .capability-form-grid,
    .payload-compare,
    .fault-scoreboard,
    .scene-replay-scoreboard,
    .fault-report-scoreboard,
    .fault-policy-grid,
    .fault-configuration-form-grid,
    .fault-validation-grid,
    .fault-detail-policy-grid,
    .fault-runtime-facts,
    .scene-replay-form-grid,
    .topology-mirror-grid,
    .replay-delta-list,
  .source-count-grid,
  .data-model-form-grid,
  .alert-template-rail,
  .alert-template-base-grid,
  .alert-create-grid,
  .alert-facts,
  .alert-operate-grid {
    grid-template-columns: 1fr;
  }
  .simulation-template-rail,
  .simulation-base-grid,
  .rule-fields,
  .trend-stat-grid {
    grid-template-columns: 1fr;
  }
  .simulation-base-grid .wide-field {
    grid-column: auto;
  }
  .fault-configuration-form-grid .wide { grid-column: auto; }
  .scene-replay-form-grid .wide { grid-column: auto; }
  .scene-replay-workbench { grid-template-columns: 1fr; min-height: 0; }
  .fault-report-workbench { grid-template-columns: 1fr; min-height: 0; }
  .fault-report-stage-line,
  .fault-report-runtime,
  .fault-report-template-preview,
  .fault-report-form-grid,
  .fault-report-action-form { grid-template-columns: 1fr; }
  .fault-report-form-grid .wide { grid-column: auto; }
  .traffic-frame-card { grid-template-columns: 1fr; }
  .topology-nodes { grid-template-columns: 1fr; }
  .fault-apply-bar { align-items: stretch; flex-direction: column; }
  .fault-apply-bar :deep(.el-select) { width: 100%; }
  .simulation-heading,
  .simulation-summary,
  .simulation-form-intro,
  .simulation-command,
  .drawer-footer,
  .trend-heading,
  .trend-actions {
    align-items: flex-start;
    flex-direction: column;
  }
  .simulation-rule-card {
    grid-template-columns: 28px 1fr;
  }
  .simulation-rule-card > :deep(.el-button) {
    grid-column: 2;
    justify-self: end;
  }
  .process-summary,
  .process-command,
  .traceback-heading,
  .traceback-summary,
  .traceback-command,
  .record-heading,
  .record-heading-actions,
  .record-command,
  .library-heading,
  .library-summary,
  .library-command,
  .scene-heading,
  .scene-summary,
  .scene-command,
  .work-order-list > article {
    align-items: flex-start;
    flex-direction: column;
  }
  .hero-actions,
  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }
}
</style>
