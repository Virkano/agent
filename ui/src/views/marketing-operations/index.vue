<template>
  <div class="operations-page p-16-24">
    <header class="page-header">
      <div>
        <div class="eyebrow">MARKETING CONTROL DESK</div>
        <h2>营销运营监控</h2>
        <p>统一查看营销任务、客户对话、回答质量和执行风险。</p>
      </div>
      <div class="header-actions">
        <el-select
          v-model="filters.task_id"
          clearable
          filterable
          placeholder="全部营销任务"
          style="width: 220px"
          @change="loadOverview"
        >
          <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.id" />
        </el-select>
        <el-radio-group v-model="filters.days" @change="refreshDashboard">
          <el-radio-button :value="7">近7天</el-radio-button>
          <el-radio-button :value="30">近30天</el-radio-button>
          <el-radio-button :value="90">近90天</el-radio-button>
        </el-radio-group>
        <el-button :icon="Refresh" :loading="loading" @click="loadAll">刷新数据</el-button>
      </div>
    </header>

    <section class="health-panel" :class="`is-${overview.health.status.toLowerCase()}`">
      <div class="health-marker">
        <component :is="healthIcon" />
      </div>
      <div class="health-copy">
        <span>当前运行状态</span>
        <strong>{{ overview.health.label }}</strong>
        <p>{{ overview.health.summary }}</p>
      </div>
      <div class="health-period">
        <span>统计区间</span>
        <strong>{{ overview.range.start_date }} — {{ overview.range.end_date }}</strong>
        <small
          >更新时间 {{ overview.generated_at ? datetimeFormat(overview.generated_at) : '—' }}</small
        >
      </div>
      <div class="health-counts">
        <div>
          <span>紧急项</span>
          <strong>{{ overview.health.critical_count }}</strong>
        </div>
        <div>
          <span>关注项</span>
          <strong>{{ overview.health.warning_count }}</strong>
        </div>
      </div>
    </section>

    <section class="metric-grid">
      <article v-for="item in primaryMetrics" :key="item.key" class="metric-card">
        <div class="metric-topline">
          <span>{{ item.label }}</span>
          <i :class="`tone-${item.tone}`" />
        </div>
        <strong>{{ item.value }}</strong>
        <p>{{ item.hint }}</p>
      </article>
    </section>

    <section class="signal-strip">
      <div v-for="item in secondaryMetrics" :key="item.label">
        <span>{{ item.label }}</span>
        <strong :class="item.tone ? `text-${item.tone}` : ''">{{ item.value }}</strong>
      </div>
    </section>

    <section class="dashboard-grid">
      <el-card class="trend-card" shadow="never">
        <template #header>
          <div class="card-heading">
            <div>
              <strong>运行趋势</strong>
              <span>对话量与问题回答按天统计</span>
            </div>
            <span class="legend-note">单位：条</span>
          </div>
        </template>
        <LineCharts id="marketingOperationsTrend" height="300px" :option="trendOption" />
      </el-card>

      <el-card class="issue-card" shadow="never">
        <template #header>
          <div class="card-heading">
            <div>
              <strong>待关注事项</strong>
              <span>按影响程度自动排序</span>
            </div>
            <el-tag effect="plain" :type="overview.issues.length ? 'warning' : 'success'">
              {{ overview.issues.length }} 项
            </el-tag>
          </div>
        </template>
        <div v-if="overview.issues.length" class="issue-list">
          <button
            v-for="issue in overview.issues"
            :key="issue.type"
            type="button"
            class="issue-row"
            @click="openIssue(issue)"
          >
            <span class="issue-level" :class="`is-${issue.severity.toLowerCase()}`">
              {{ issueSeverityMap[issue.severity] }}
            </span>
            <span class="issue-copy">
              <strong>{{ issue.title }}</strong>
              <small>{{ issue.description }}</small>
            </span>
            <span class="issue-count">{{ issue.count || '—' }}</span>
            <span class="issue-link">查看</span>
          </button>
        </div>
        <el-empty v-else :image-size="70" description="当前周期没有需要处理的异常" />
      </el-card>
    </section>

    <el-card class="alert-workbench" shadow="never">
      <template #header>
        <div class="card-heading alert-heading">
          <div>
            <strong>告警处理台</strong>
            <span>告警会去重保存，处理过程和结论可追溯</span>
          </div>
          <div class="alert-heading-actions">
            <el-button :icon="Setting" @click="openRuleDrawer">告警规则</el-button>
            <el-button :icon="Refresh" :loading="alertLoading" @click="syncAndLoadAlerts"
              >同步告警</el-button
            >
          </div>
        </div>
      </template>

      <div class="alert-summary">
        <button
          v-for="item in alertSummaryItems"
          :key="item.status"
          type="button"
          :class="{ active: alertFilters.status === item.status }"
          @click="setAlertStatus(item.status)"
        >
          <span>{{ item.label }}</span>
          <strong>{{ item.value }}</strong>
        </button>
      </div>

      <div class="alert-toolbar">
        <el-select
          v-model="alertFilters.assignee"
          clearable
          placeholder="全部负责人"
          style="width: 160px"
          @change="loadAlerts(1)"
        >
          <el-option label="未认领" value="UNASSIGNED" />
          <el-option
            v-for="owner in alertOwnerOptions"
            :key="owner.assignee_id"
            :label="owner.assignee_name"
            :value="owner.assignee_id"
          />
        </el-select>
        <el-select
          v-model="alertFilters.severity"
          clearable
          placeholder="全部级别"
          style="width: 140px"
          @change="loadAlerts(1)"
        >
          <el-option label="紧急" value="CRITICAL" />
          <el-option label="关注" value="WARNING" />
          <el-option label="提示" value="INFO" />
        </el-select>
        <el-input
          v-model="alertFilters.keyword"
          clearable
          placeholder="搜索告警、说明或负责人"
          style="width: 260px"
          @keyup.enter="loadAlerts(1)"
          @clear="loadAlerts(1)"
        />
        <el-button type="primary" plain @click="loadAlerts(1)">查询</el-button>
        <el-checkbox v-model="alertFilters.active_only" border @change="loadAlerts(1)">
          仅看未关闭
        </el-checkbox>
        <el-checkbox
          v-model="alertFilters.sla_overdue"
          class="sla-filter"
          border
          @change="loadAlerts(1)"
        >
          SLA 超时 {{ alertPage.summary.sla_overdue_count }}
        </el-checkbox>
      </div>

      <el-table v-loading="alertLoading" :data="alertPage.records" row-key="id">
        <el-table-column label="级别" width="88">
          <template #default="{ row }">
            <el-tag :type="getAlertSeverity(row.severity).type" effect="dark">
              {{ getAlertSeverity(row.severity).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="告警" min-width="310">
          <template #default="{ row }">
            <div class="alert-title-cell">
              <strong>{{ row.title }}</strong>
              <span>{{ row.description }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="指标" width="90" align="right">
          <template #default="{ row }">
            <strong>{{ row.current_count }}</strong>
          </template>
        </el-table-column>
        <el-table-column label="来源" width="100">
          <template #default="{ row }">
            <span :class="row.source_active ? 'source-active' : 'source-recovered'">
              {{ row.source_active ? '仍有异常' : '已恢复' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="处理状态" width="104">
          <template #default="{ row }">
            <el-tag :type="getAlertStatus(row.status).type" effect="plain">
              {{ getAlertStatus(row.status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="SLA" width="158">
          <template #default="{ row }">
            <div class="sla-cell">
              <el-tag :type="getAlertSla(row).type" effect="plain" size="small">
                {{ getAlertSla(row).label }}
              </el-tag>
              <small>{{ getAlertSla(row).hint }}</small>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="负责人" width="120">
          <template #default="{ row }">{{ row.assignee_name || '未认领' }}</template>
        </el-table-column>
        <el-table-column label="最近触发" width="168">
          <template #default="{ row }">{{ datetimeFormat(row.last_triggered_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openAlert(row)">处理</el-button>
            <el-button v-if="row.target_route" link @click="router.push(row.target_route)"
              >查来源</el-button
            >
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="当前没有已生成的告警" />
        </template>
      </el-table>
      <div class="alert-pagination">
        <el-pagination
          v-model:current-page="alertPage.current"
          :page-size="alertPage.size"
          :total="alertPage.total"
          layout="total, prev, pager, next"
          @current-change="loadAlerts"
        />
      </div>
    </el-card>

    <el-card class="owner-performance-card" shadow="never">
      <template #header>
        <div class="card-heading">
          <div>
            <strong>负责人告警工单</strong>
            <span>按负责人处理轮次归集耗时，点击负责人可下钻当前待办</span>
          </div>
          <span class="legend-note">近 {{ performance.range.days }} 天</span>
        </div>
      </template>

      <div class="owner-summary-grid">
        <div>
          <span>工单总数</span>
          <strong>{{ performance.summary.total_count }}</strong>
        </div>
        <div>
          <span>处理中</span>
          <strong>{{ performance.summary.active_count }}</strong>
        </div>
        <div>
          <span>未认领</span>
          <strong :class="{ 'text-warning': performance.summary.unassigned_count }">
            {{ performance.summary.unassigned_count }}
          </strong>
        </div>
        <div>
          <span>平均首次响应</span>
          <strong>{{ formatWorkDuration(performance.summary.avg_response_seconds) }}</strong>
        </div>
        <div>
          <span>平均处理时长</span>
          <strong>{{ formatWorkDuration(performance.summary.avg_resolution_seconds) }}</strong>
        </div>
        <div>
          <span>SLA 达标率</span>
          <strong :class="getSlaRateClass(performance.summary.sla_attainment_rate)">
            {{ performance.summary.sla_attainment_rate }}%
          </strong>
        </div>
      </div>

      <el-table v-loading="performanceLoading" :data="performance.workload" row-key="assignee_name">
        <el-table-column prop="assignee_name" label="负责人" min-width="150" />
        <el-table-column prop="total_count" label="工单" width="76" align="right" />
        <el-table-column prop="active_count" label="未关闭" width="82" align="right" />
        <el-table-column label="SLA 超时" width="88" align="right">
          <template #default="{ row }">
            <span :class="{ 'text-danger': row.overdue_count }">{{ row.overdue_count }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="closed_count" label="已关闭" width="82" align="right" />
        <el-table-column label="平均响应" width="110" align="right">
          <template #default="{ row }">{{ formatWorkDuration(row.avg_response_seconds) }}</template>
        </el-table-column>
        <el-table-column label="平均处理" width="110" align="right">
          <template #default="{ row }">{{
            formatWorkDuration(row.avg_resolution_seconds)
          }}</template>
        </el-table-column>
        <el-table-column label="响应达标" width="104" align="right">
          <template #default="{ row }">{{ row.response_sla_rate }}%</template>
        </el-table-column>
        <el-table-column label="处理达标" width="104" align="right">
          <template #default="{ row }">{{ row.resolution_sla_rate }}%</template>
        </el-table-column>
        <el-table-column label="综合达标" width="104" align="right">
          <template #default="{ row }">
            <strong :class="getSlaRateClass(row.sla_attainment_rate)">
              {{ row.sla_attainment_rate }}%
            </strong>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="104" fixed="right">
          <template #default="{ row }">
            <el-button
              type="primary"
              link
              :disabled="!row.active_count"
              @click="drillDownOwner(row)"
            >
              查看待办
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="当前周期还没有告警工单" />
        </template>
      </el-table>
    </el-card>

    <el-card class="noise-analysis-card" shadow="never">
      <template #header>
        <div class="card-heading">
          <div>
            <strong>告警降噪与合并建议</strong>
            <span>识别短期重复刷新和同处理入口告警，保留独立状态但共享排查上下文</span>
          </div>
          <span class="legend-note">近 {{ noiseAnalysis.range.days }} 天</span>
        </div>
      </template>

      <div v-loading="noiseAnalysisLoading">
        <div class="noise-summary">
          <div>
            <span>监测告警</span><strong>{{ noiseAnalysis.summary.monitored_alert_count }}</strong>
          </div>
          <div>
            <span>重复告警</span>
            <strong :class="{ 'text-warning': noiseAnalysis.summary.repeated_alert_count }">
              {{ noiseAnalysis.summary.repeated_alert_count }}
            </strong>
          </div>
          <div>
            <span>高噪声</span>
            <strong :class="{ 'text-danger': noiseAnalysis.summary.high_noise_count }">
              {{ noiseAnalysis.summary.high_noise_count }}
            </strong>
          </div>
          <div>
            <span>已吸收重复刷新</span
            ><strong>{{ noiseAnalysis.summary.deduplicated_event_count }}</strong>
          </div>
          <div>
            <span>合并建议</span><strong>{{ noiseAnalysis.summary.merge_suggestion_count }}</strong>
          </div>
        </div>

        <div class="noise-analysis-grid">
          <section>
            <h4>重复告警排行</h4>
            <div v-if="noiseAnalysis.noise_alerts.length" class="noise-alert-list">
              <article v-for="item in noiseAnalysis.noise_alerts" :key="item.id">
                <div class="noise-alert-heading">
                  <strong>{{ item.title }}</strong>
                  <el-tag :type="getNoiseLevel(item.noise_level).type" size="small" effect="plain">
                    {{ item.noise_label }}
                  </el-tag>
                </div>
                <p>
                  刷新 {{ item.refresh_count }} 次 · 重开 {{ item.reopen_count }} 次 · 噪声分
                  {{ item.noise_score }}
                </p>
                <small>{{ item.recommendation }}</small>
                <div class="noise-alert-actions">
                  <el-button link type="primary" @click="openAlertById(item.id)"
                    >打开告警</el-button
                  >
                  <el-button
                    link
                    type="success"
                    :disabled="
                      item.status === 'CLOSED' ||
                      !item.suggested_root_cause_category ||
                      !item.suggested_resolution_type
                    "
                    @click="applyNoiseExperience(item)"
                  >
                    带入历史经验
                  </el-button>
                </div>
              </article>
            </div>
            <el-empty v-else :image-size="60" description="当前没有短期重复告警" />
          </section>

          <section>
            <h4>合并排查建议</h4>
            <div v-if="noiseAnalysis.merge_suggestions.length" class="merge-suggestion-list">
              <article v-for="item in noiseAnalysis.merge_suggestions" :key="item.group_key">
                <div>
                  <strong>{{ item.primary_alert_title }}</strong>
                  <el-tag size="small" effect="plain">{{ item.alert_count }} 条关联告警</el-tag>
                </div>
                <p>{{ item.reason }}</p>
                <div class="merge-candidates">
                  <el-tag
                    v-for="candidate in item.candidates"
                    :key="candidate.id"
                    :type="getAlertSeverity(candidate.severity).type"
                    size="small"
                    effect="plain"
                  >
                    {{ candidate.title }}（{{ candidate.current_count }}）
                  </el-tag>
                </div>
                <small>{{ item.recommendation }}</small>
                <el-button link type="primary" @click="openAlertById(item.primary_alert_id)">
                  查看主告警
                </el-button>
              </article>
            </div>
            <el-empty v-else :image-size="60" description="当前没有需要合并排查的告警" />
          </section>
        </div>
      </div>
    </el-card>

    <el-card class="retrospective-card" shadow="never">
      <template #header>
        <div class="card-heading">
          <div>
            <strong>告警复盘与问题归因</strong>
            <span>聚合已关闭告警的高频根因、处置方式和复发情况</span>
          </div>
          <div class="retrospective-actions">
            <el-select
              v-model="retrospectiveRootCause"
              clearable
              placeholder="全部根因"
              style="width: 140px"
              @change="loadRetrospective"
            >
              <el-option
                v-for="item in rootCauseOptions"
                :key="item.value"
                :label="item.label"
                :value="item.value"
              />
            </el-select>
            <el-button :loading="exportingRetrospective" @click="exportRetrospective"
              >导出复盘</el-button
            >
          </div>
        </div>
      </template>

      <div v-loading="retrospectiveLoading">
        <div class="retrospective-summary">
          <div>
            <span>已关闭</span><strong>{{ retrospective.summary.closed_count }}</strong>
          </div>
          <div>
            <span>已归因</span><strong>{{ retrospective.summary.classified_count }}</strong>
          </div>
          <div>
            <span>复发次数</span>
            <strong :class="{ 'text-warning': retrospective.summary.recurrence_count }">
              {{ retrospective.summary.recurrence_count }}
            </strong>
          </div>
          <div>
            <span>平均处理时长</span>
            <strong>{{ formatWorkDuration(retrospective.summary.avg_resolution_seconds) }}</strong>
          </div>
        </div>

        <div class="retrospective-grid">
          <section>
            <h4>高频根因</h4>
            <div v-if="retrospective.root_causes.length" class="distribution-list">
              <div v-for="item in retrospective.root_causes" :key="item.value">
                <span>{{ item.label }}</span>
                <el-progress :percentage="item.percentage" :stroke-width="7" />
                <strong>{{ item.count }}</strong>
              </div>
            </div>
            <el-empty v-else :image-size="55" description="暂无根因数据" />
          </section>
          <section>
            <h4>处置方式</h4>
            <div v-if="retrospective.resolution_types.length" class="distribution-list">
              <div v-for="item in retrospective.resolution_types" :key="item.value">
                <span>{{ item.label }}</span>
                <el-progress :percentage="item.percentage" :stroke-width="7" />
                <strong>{{ item.count }}</strong>
              </div>
            </div>
            <el-empty v-else :image-size="55" description="暂无处置数据" />
          </section>
          <section>
            <h4>复发告警</h4>
            <div v-if="retrospective.recurring_alerts.length" class="recurrence-list">
              <button
                v-for="item in retrospective.recurring_alerts"
                :key="item.id"
                type="button"
                @click="openAlertById(item.id)"
              >
                <span>{{ item.title }}</span>
                <strong>{{ item.recurrence_count }} 次</strong>
              </button>
            </div>
            <el-empty v-else :image-size="55" description="当前周期没有复发告警" />
          </section>
        </div>

        <el-table :data="retrospective.experiences" row-key="id">
          <el-table-column
            prop="title"
            label="近期处理经验"
            min-width="220"
            show-overflow-tooltip
          />
          <el-table-column prop="root_cause_label" label="根因" width="110" />
          <el-table-column prop="resolution_type_label" label="处置方式" width="120" />
          <el-table-column
            prop="close_note"
            label="处理结论"
            min-width="260"
            show-overflow-tooltip
          />
          <el-table-column prop="assignee_name" label="负责人" width="110" />
          <el-table-column label="关闭时间" width="168">
            <template #default="{ row }">{{ datetimeFormat(row.closed_at) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button type="primary" link @click="openAlertById(row.id)">查看</el-button>
            </template>
          </el-table-column>
          <template #empty><el-empty description="当前周期暂无已归因的关闭告警" /></template>
        </el-table>
      </div>
    </el-card>

    <el-card class="task-health-card" shadow="never">
      <template #header>
        <div class="card-heading">
          <div>
            <strong>任务健康明细</strong>
            <span>优先展示运行错误和待处理问题较多的任务</span>
          </div>
          <el-button type="primary" link @click="router.push('/marketing-task')"
            >管理任务</el-button
          >
        </div>
      </template>
      <el-table v-loading="loading" :data="overview.task_health" row-key="task_id">
        <el-table-column label="健康状态" width="118">
          <template #default="{ row }">
            <el-tag :type="getTaskHealth(row.health_status).type" effect="dark">
              {{ getTaskHealth(row.health_status).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="task_name" label="营销任务" min-width="210" show-overflow-tooltip />
        <el-table-column label="任务状态" width="110">
          <template #default="{ row }">{{ getTaskStatus(row.task_status) }}</template>
        </el-table-column>
        <el-table-column prop="customer_count" label="客户" width="86" align="right" />
        <el-table-column prop="conversation_count" label="对话" width="86" align="right" />
        <el-table-column label="平均响应" width="110" align="right">
          <template #default="{ row }">{{ formatDuration(row.avg_response_seconds) }}</template>
        </el-table-column>
        <el-table-column prop="quality_issue_count" label="质检问题" width="100" align="right" />
        <el-table-column prop="pending_review_count" label="待复核" width="90" align="right" />
        <el-table-column label="转化率" width="100" align="right">
          <template #default="{ row }">{{ row.conversion_rate }}%</template>
        </el-table-column>
        <el-table-column label="最近活动" width="168">
          <template #default="{ row }">
            {{ row.last_activity_at ? datetimeFormat(row.last_activity_at) : '暂无对话' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" link @click="openTask(row)">
              {{ row.quality_issue_count ? '查看质检' : '查看任务' }}
            </el-button>
          </template>
        </el-table-column>
        <template #empty>
          <el-empty description="当前工作空间还没有营销任务" />
        </template>
      </el-table>
    </el-card>

    <el-drawer v-model="alertDrawerVisible" title="告警处理" size="520px" @closed="clearAlertRoute">
      <template v-if="selectedAlert">
        <div class="alert-detail-head">
          <div>
            <el-tag :type="getAlertSeverity(selectedAlert.severity).type" effect="dark">
              {{ getAlertSeverity(selectedAlert.severity).label }}
            </el-tag>
            <el-tag :type="getAlertStatus(selectedAlert.status).type" effect="plain">
              {{ getAlertStatus(selectedAlert.status).label }}
            </el-tag>
          </div>
          <h3>{{ selectedAlert.title }}</h3>
          <p>{{ selectedAlert.description }}</p>
          <dl>
            <div>
              <dt>负责人</dt>
              <dd>{{ selectedAlert.assignee_name || '未认领' }}</dd>
            </div>
            <div>
              <dt>当前指标</dt>
              <dd>{{ selectedAlert.current_count }}</dd>
            </div>
            <div>
              <dt>来源状态</dt>
              <dd>{{ selectedAlert.source_active ? '仍有异常' : '指标已恢复' }}</dd>
            </div>
            <div>
              <dt>首次触发</dt>
              <dd>{{ datetimeFormat(selectedAlert.first_triggered_at) }}</dd>
            </div>
            <div>
              <dt>首次响应时限</dt>
              <dd :class="{ 'text-danger': selectedAlert.response_overdue }">
                {{ formatSlaTime(selectedAlert.response_due_at, selectedAlert.first_responded_at) }}
              </dd>
            </div>
            <div>
              <dt>处理完成时限</dt>
              <dd :class="{ 'text-danger': selectedAlert.resolution_overdue }">
                {{ formatSlaTime(selectedAlert.resolution_due_at, selectedAlert.closed_at) }}
              </dd>
            </div>
            <div>
              <dt>升级接收人</dt>
              <dd>{{ selectedAlert.escalation_user_name || '工作空间成员' }}</dd>
            </div>
            <div v-if="selectedAlert.root_cause_label">
              <dt>根因分类</dt>
              <dd>{{ selectedAlert.root_cause_label }}</dd>
            </div>
            <div v-if="selectedAlert.resolution_type_label">
              <dt>处置方式</dt>
              <dd>{{ selectedAlert.resolution_type_label }}</dd>
            </div>
            <div v-if="selectedAlert.impact_scope">
              <dt>影响范围</dt>
              <dd>{{ selectedAlert.impact_scope }}</dd>
            </div>
          </dl>
        </div>

        <div
          v-if="selectedAlert.capabilities.can_assign || selectedAlert.capabilities.can_transfer"
          class="collaboration-panel"
        >
          <div class="panel-title">
            <strong>{{
              selectedAlert.capabilities.can_assign ? '指派负责人' : '转派负责人'
            }}</strong>
            <span>转派不会重置全局处理 SLA</span>
          </div>
          <div class="assignment-row">
            <el-select
              v-model="collaborationAssignee"
              filterable
              clearable
              placeholder="选择工作空间成员"
            >
              <el-option
                v-for="member in availableAlertMembers"
                :key="member.id"
                :label="member.name"
                :value="member.id"
              />
            </el-select>
            <el-button
              type="primary"
              :loading="collaborating"
              :disabled="!collaborationAssignee"
              @click="submitAssignment"
            >
              {{ selectedAlert.capabilities.can_assign ? '确认指派' : '确认转派' }}
            </el-button>
          </div>
          <el-input
            v-model="collaborationNote"
            type="textarea"
            :rows="2"
            maxlength="2000"
            show-word-limit
            :placeholder="
              selectedAlert.capabilities.can_transfer
                ? '填写转派原因（必填）'
                : '填写指派说明（选填）'
            "
          />
        </div>

        <div v-if="selectedAlert.capabilities.can_subscribe" class="subscriber-panel">
          <div class="panel-title">
            <strong>关注人与通知</strong>
            <span>评论、附件和关闭状态会定向通知</span>
          </div>
          <div v-if="selectedAlert.subscribers.length" class="subscriber-tags">
            <el-tag
              v-for="subscriber in selectedAlert.subscribers"
              :key="subscriber.id"
              closable
              effect="plain"
              @close="removeSubscriber(subscriber.user_id)"
            >
              {{ subscriber.user_name }}
            </el-tag>
          </div>
          <div v-else class="empty-inline">尚无关注人</div>
          <div class="subscriber-row">
            <el-select
              v-model="subscriberMember"
              filterable
              clearable
              placeholder="添加工作空间成员"
            >
              <el-option
                v-for="member in availableSubscriberMembers"
                :key="member.id"
                :label="member.name"
                :value="member.id"
              />
            </el-select>
            <el-button
              type="primary"
              plain
              :loading="subscriberUpdating"
              :disabled="!subscriberMember"
              @click="addSubscriber"
            >
              添加关注
            </el-button>
          </div>
        </div>

        <div v-if="selectedAlert.capabilities.can_attach" class="attachment-panel">
          <div class="panel-title">
            <strong>排查附件</strong>
            <span>单个不超过 10 MB，保留 30 天</span>
          </div>
          <el-upload
            :show-file-list="false"
            :http-request="uploadAlertFile"
            accept=".png,.jpg,.jpeg,.webp,.pdf,.txt,.log,.csv,.json,.zip"
          >
            <el-button plain :loading="attachmentUploading">上传截图、日志或诊断文件</el-button>
          </el-upload>
          <div v-if="selectedAlert.attachments.length" class="attachment-list">
            <a
              v-for="attachment in selectedAlert.attachments"
              :key="attachment.id"
              :href="attachment.download_url"
              target="_blank"
              rel="noopener"
            >
              <span>{{ attachment.file_name }}</span>
              <small>
                {{ formatFileSize(attachment.file_size) }} · {{ attachment.uploader_name }} ·
                {{ datetimeFormat(attachment.create_time) }}
              </small>
            </a>
          </div>
        </div>

        <div class="handling-panel">
          <template v-if="selectedAlert.status !== 'CLOSED'">
            <div class="panel-title">
              <strong>关闭归因</strong>
              <span>关闭告警时必填根因和处置方式</span>
            </div>
            <div class="closure-fields">
              <el-select v-model="closeRootCause" placeholder="选择根因分类">
                <el-option
                  v-for="item in rootCauseOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
              <el-select v-model="closeResolutionType" placeholder="选择处置方式">
                <el-option
                  v-for="item in resolutionTypeOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </div>
            <el-input
              v-model="closeImpactScope"
              maxlength="500"
              show-word-limit
              placeholder="影响范围（选填），例如：华东区域营销对话"
            />
          </template>
          <label>处理说明 / 关闭结论</label>
          <el-input
            v-model="handleNote"
            type="textarea"
            :rows="3"
            maxlength="2000"
            show-word-limit
            placeholder="关闭告警时必须填写处理结论"
          />
          <div class="handling-actions">
            <el-button
              v-if="selectedAlert.status === 'OPEN'"
              :loading="handling"
              @click="handleSelectedAlert('CLAIM')"
              >认领</el-button
            >
            <el-button
              v-if="['OPEN', 'CLAIMED'].includes(selectedAlert.status)"
              type="primary"
              plain
              :loading="handling"
              @click="handleSelectedAlert('START')"
              >开始处理</el-button
            >
            <el-button
              v-if="selectedAlert.status !== 'CLOSED'"
              type="success"
              :disabled="!handleNote.trim() || !closeRootCause || !closeResolutionType"
              :loading="handling"
              @click="handleSelectedAlert('CLOSE')"
              >关闭告警</el-button
            >
            <el-button
              v-else
              type="warning"
              :loading="handling"
              @click="handleSelectedAlert('REOPEN')"
              >重新打开</el-button
            >
          </div>
        </div>

        <div v-if="selectedAlert.related_experiences.length" class="experience-hints">
          <h4>相似历史处理经验</h4>
          <article v-for="experience in selectedAlert.related_experiences" :key="experience.id">
            <div>
              <strong
                >{{ experience.root_cause_label }} · {{ experience.resolution_type_label }}</strong
              >
              <span>{{ datetimeFormat(experience.closed_at) }}</span>
            </div>
            <p>{{ experience.close_note }}</p>
            <small v-if="experience.impact_scope">影响范围：{{ experience.impact_scope }}</small>
          </article>
        </div>

        <div v-if="selectedAlert.capabilities.can_comment" class="comment-panel">
          <div class="panel-title">
            <strong>添加协作评论</strong>
            <span>补充排查进展、风险和下一步</span>
          </div>
          <el-input
            v-model="commentNote"
            type="textarea"
            :rows="2"
            maxlength="2000"
            show-word-limit
            placeholder="输入协作评论"
          />
          <div class="comment-actions">
            <el-button
              type="primary"
              plain
              :loading="collaborating"
              :disabled="!commentNote.trim()"
              @click="submitComment"
            >
              发布评论
            </el-button>
          </div>
        </div>

        <div v-if="selectedAlert.handling_rounds.length" class="handling-rounds">
          <h4>负责人轮次</h4>
          <article v-for="round in selectedAlert.handling_rounds" :key="round.id">
            <div>
              <strong>第 {{ round.sequence }} 轮 · {{ round.assignee_name }}</strong>
              <el-tag :type="round.ended_at ? 'info' : 'primary'" size="small" effect="plain">
                {{ round.ended_at ? getRoundEndReason(round.end_reason) : '当前负责' }}
              </el-tag>
            </div>
            <p>
              {{ datetimeFormat(round.assigned_at) }} 由 {{ round.assigned_by_name }} 指派
              <template v-if="round.first_responded_at">
                · {{ datetimeFormat(round.first_responded_at) }} 响应
              </template>
            </p>
            <small v-if="round.end_note">{{ round.end_note }}</small>
          </article>
        </div>

        <div class="action-history">
          <h4>协作与处理记录</h4>
          <el-timeline>
            <el-timeline-item
              v-for="action in selectedAlert.actions"
              :key="action.id"
              :timestamp="datetimeFormat(action.create_time)"
              placement="top"
            >
              <div class="history-card">
                <strong>{{ getAlertAction(action.action) }}</strong>
                <span>{{ action.operator_name || '系统' }}</span>
                <p v-if="action.snapshot.assignee_name" class="assignment-change">
                  <template v-if="action.snapshot.previous_assignee_name">
                    {{ action.snapshot.previous_assignee_name }} →
                  </template>
                  {{ action.snapshot.assignee_name }}
                </p>
                <p v-if="action.note">{{ action.note }}</p>
              </div>
            </el-timeline-item>
          </el-timeline>
        </div>
      </template>
    </el-drawer>

    <el-drawer v-model="ruleDrawerVisible" title="告警规则、效果与回滚" size="960px">
      <p class="rule-intro">
        规则按工作空间独立保存。这里集中完成 SLA 配置、阈值效果评估、推荐值应用和历史版本回滚。
      </p>
      <div v-if="alertRuleEffect" class="rule-effect-summary">
        <div>
          <span>规则总数</span>
          <strong>{{ alertRuleEffect.summary.rule_count }}</strong>
        </div>
        <div>
          <span>已启用</span>
          <strong>{{ alertRuleEffect.summary.enabled_rule_count }}</strong>
        </div>
        <div>
          <span>建议优化</span>
          <strong>{{ alertRuleEffect.summary.optimization_count }}</strong>
        </div>
        <div>
          <span>有效信号</span>
          <strong>{{ alertRuleEffect.summary.signal_event_count }}</strong>
        </div>
        <div>
          <span>误报关闭</span>
          <strong>{{ alertRuleEffect.summary.false_positive_count }}</strong>
        </div>
      </div>
      <p v-if="alertRuleEffect" class="rule-simulation-note">
        {{ alertRuleEffect.simulation_note }}
      </p>
      <div v-loading="ruleLoading" class="rule-list">
        <article
          v-for="effect in alertRuleEffect?.rules || []"
          :key="effect.rule.id"
          class="rule-row"
        >
          <div class="rule-head">
            <div class="rule-copy">
              <strong>{{ effect.rule.name }}</strong>
              <span>{{ effect.rule.description }}</span>
            </div>
            <el-switch
              v-model="effect.rule.enabled"
              inline-prompt
              active-text="开"
              inactive-text="关"
            />
          </div>
          <div class="rule-fields">
            <label>
              <span>告警级别</span>
              <el-select v-model="effect.rule.severity">
                <el-option label="紧急" value="CRITICAL" />
                <el-option label="关注" value="WARNING" />
                <el-option label="提示" value="INFO" />
              </el-select>
            </label>
            <label>
              <span>触发阈值</span>
              <el-input-number
                v-model="effect.rule.threshold"
                :min="1"
                :max="100000"
                controls-position="right"
              />
            </label>
            <label>
              <span>首次响应（分钟）</span>
              <el-input-number
                v-model="effect.rule.response_sla_minutes"
                :min="1"
                :max="10080"
                controls-position="right"
              />
            </label>
            <label>
              <span>处理完成（分钟）</span>
              <el-input-number
                v-model="effect.rule.resolution_sla_minutes"
                :min="1"
                :max="43200"
                controls-position="right"
              />
            </label>
            <label class="escalation-field">
              <span>升级接收人</span>
              <el-select
                v-model="effect.rule.escalation_user_id"
                clearable
                placeholder="工作空间成员"
              >
                <el-option
                  v-for="member in alertMembers"
                  :key="member.id"
                  :label="member.name"
                  :value="member.id"
                />
              </el-select>
            </label>
            <el-button
              class="rule-save"
              type="primary"
              :loading="savingRuleId === effect.rule.id"
              @click="saveRule(effect.rule)"
            >
              保存规则
            </el-button>
          </div>

          <section class="rule-effect-panel">
            <div class="rule-metrics">
              <div>
                <span>信号事件</span><strong>{{ effect.metrics.signal_event_count }}</strong>
              </div>
              <div>
                <span>重复率</span><strong>{{ effect.metrics.repeat_rate }}%</strong>
              </div>
              <div>
                <span>误报率</span><strong>{{ effect.metrics.false_positive_rate }}%</strong>
              </div>
              <div>
                <span>平均处理</span>
                <strong>{{ formatWorkDuration(effect.metrics.avg_resolution_seconds) }}</strong>
              </div>
            </div>
            <div
              class="rule-recommendation"
              :class="{ 'has-change': effect.recommendation.changed }"
            >
              <div>
                <span
                  >阈值建议 · {{ confidenceLabel(effect.recommendation.confidence) }}可信度</span
                >
                <strong>
                  当前 {{ effect.rule.threshold }} → 建议 {{ effect.recommendation.threshold }}
                </strong>
                <small>{{ effect.recommendation.reason }}</small>
              </div>
              <el-button
                v-if="effect.recommendation.changed"
                type="warning"
                plain
                :loading="savingRuleId === effect.rule.id"
                @click="applyRuleRecommendation(effect)"
              >
                应用推荐阈值
              </el-button>
            </div>
            <div class="threshold-simulations">
              <article v-for="simulation in effect.simulations" :key="simulation.threshold">
                <span>阈值 {{ simulation.threshold }}</span>
                <strong>预计触发 {{ simulation.estimated_trigger_count }} 次</strong>
                <small>减少 {{ simulation.estimated_reduction_rate }}%</small>
                <el-tag v-if="simulation.recommended" size="small" type="warning" effect="plain">
                  推荐
                </el-tag>
              </article>
            </div>
            <div class="rule-history">
              <h4>变更历史</h4>
              <el-empty v-if="!effect.history.length" description="尚无规则变更" :image-size="48" />
              <article v-for="change in effect.history" :key="change.id">
                <div>
                  <strong>V{{ change.version }} · {{ change.change_type_label }}</strong>
                  <span
                    >{{ datetimeFormat(change.create_time) }} ·
                    {{ change.operator_name || '系统' }}</span
                  >
                  <small>
                    阈值 {{ change.snapshot.threshold }} · 响应
                    {{ change.snapshot.response_sla_minutes }} 分钟 · 完成
                    {{ change.snapshot.resolution_sla_minutes }} 分钟
                  </small>
                  <p>{{ change.reason || '未填写变更原因' }}</p>
                </div>
                <el-button
                  size="small"
                  plain
                  :loading="rollingBackRuleId === effect.rule.id"
                  @click="rollbackRuleChange(effect, change)"
                >
                  回滚到此版本
                </el-button>
              </article>
            </div>
          </section>
        </article>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { CircleCheckFilled, Refresh, Setting, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox, type UploadRequestOptions } from 'element-plus'

import LineCharts from '@/components/app-charts/components/LineCharts.vue'
import marketingTaskApi, { type MarketingTask } from '@/api/marketing/task'
import marketingOperationsApi, {
  type MarketingAlert,
  type MarketingAlertCollaborateAction,
  type MarketingAlertHandleAction,
  type MarketingAlertMember,
  type MarketingAlertNoiseAnalysis,
  type MarketingAlertNoiseItem,
  type MarketingAlertOwnerPerformance,
  type MarketingAlertPage,
  type MarketingAlertPerformance,
  type MarketingAlertResolutionType,
  type MarketingAlertRetrospective,
  type MarketingAlertRootCause,
  type MarketingAlertRule,
  type MarketingAlertRuleChange,
  type MarketingAlertRuleEffect,
  type MarketingAlertRuleEffectItem,
  type MarketingAlertSeverity,
  type MarketingAlertStatus,
  type MarketingOperationsIssue,
  type MarketingOperationsOverview,
  type MarketingTaskHealth,
} from '@/api/marketing/operations'
import { datetimeFormat } from '@/utils/time'

const router = useRouter()
const route = useRoute()
const loading = ref(false)
const alertLoading = ref(false)
const performanceLoading = ref(false)
const noiseAnalysisLoading = ref(false)
const retrospectiveLoading = ref(false)
const exportingRetrospective = ref(false)
const handling = ref(false)
const collaborating = ref(false)
const subscriberUpdating = ref(false)
const attachmentUploading = ref(false)
const ruleLoading = ref(false)
const tasks = ref<MarketingTask[]>([])
const filters = ref<{ days: 7 | 30 | 90; task_id: string }>({ days: 7, task_id: '' })
const alertFilters = ref<{
  status: MarketingAlertStatus | ''
  severity: MarketingAlertSeverity | ''
  keyword: string
  assignee: string
  active_only: boolean
  sla_overdue: boolean
}>({ status: '', severity: '', keyword: '', assignee: '', active_only: false, sla_overdue: false })
const alertDrawerVisible = ref(false)
const ruleDrawerVisible = ref(false)
const selectedAlert = ref<MarketingAlert>()
const handleNote = ref('')
const closeRootCause = ref<MarketingAlertRootCause | ''>('')
const closeResolutionType = ref<MarketingAlertResolutionType | ''>('')
const closeImpactScope = ref('')
const collaborationAssignee = ref('')
const collaborationNote = ref('')
const commentNote = ref('')
const subscriberMember = ref('')
const alertRuleEffect = ref<MarketingAlertRuleEffect>()
const alertMembers = ref<MarketingAlertMember[]>([])
const savingRuleId = ref('')
const rollingBackRuleId = ref('')
const retrospectiveRootCause = ref<MarketingAlertRootCause | ''>('')

const rootCauseOptions: Array<{ value: MarketingAlertRootCause; label: string }> = [
  { value: 'MODEL', label: '模型服务' },
  { value: 'DATA', label: '客户数据' },
  { value: 'KNOWLEDGE', label: '知识内容' },
  { value: 'SYSTEM', label: '系统资源' },
  { value: 'PROCESS', label: '运营流程' },
  { value: 'OTHER', label: '其他' },
]
const resolutionTypeOptions: Array<{ value: MarketingAlertResolutionType; label: string }> = [
  { value: 'CONFIG_CHANGE', label: '调整配置' },
  { value: 'DATA_FIX', label: '修复数据' },
  { value: 'KNOWLEDGE_UPDATE', label: '更新知识' },
  { value: 'RETRY_RECOVERY', label: '重试恢复' },
  { value: 'MANUAL_INTERVENTION', label: '人工处置' },
  { value: 'FALSE_POSITIVE', label: '确认误报' },
  { value: 'OTHER', label: '其他' },
]

const emptyAlertPage = (): MarketingAlertPage => ({
  total: 0,
  records: [],
  current: 1,
  size: 10,
  summary: {
    total_count: 0,
    active_count: 0,
    open_count: 0,
    claimed_count: 0,
    processing_count: 0,
    closed_count: 0,
    critical_count: 0,
    sla_overdue_count: 0,
  },
})

const alertPage = ref<MarketingAlertPage>(emptyAlertPage())

const emptyPerformance = (): MarketingAlertPerformance => ({
  range: { days: 7, start_at: '', end_at: '' },
  summary: {
    total_count: 0,
    active_count: 0,
    closed_count: 0,
    overdue_count: 0,
    unassigned_count: 0,
    avg_response_seconds: 0,
    avg_resolution_seconds: 0,
    response_total: 0,
    response_met_count: 0,
    response_sla_rate: 0,
    resolution_total: 0,
    resolution_met_count: 0,
    resolution_sla_rate: 0,
    sla_milestone_total: 0,
    sla_milestone_met_count: 0,
    sla_attainment_rate: 0,
  },
  workload: [],
})

const performance = ref<MarketingAlertPerformance>(emptyPerformance())
const emptyNoiseAnalysis = (): MarketingAlertNoiseAnalysis => ({
  range: { days: 7, start_at: '', end_at: '' },
  summary: {
    monitored_alert_count: 0,
    repeated_alert_count: 0,
    high_noise_count: 0,
    deduplicated_event_count: 0,
    merge_suggestion_count: 0,
  },
  noise_alerts: [],
  merge_suggestions: [],
})
const noiseAnalysis = ref<MarketingAlertNoiseAnalysis>(emptyNoiseAnalysis())
const emptyRetrospective = (): MarketingAlertRetrospective => ({
  range: { days: 30, start_at: '', end_at: '' },
  summary: {
    closed_count: 0,
    classified_count: 0,
    recurrence_count: 0,
    avg_resolution_seconds: 0,
  },
  root_causes: [],
  resolution_types: [],
  recurring_alerts: [],
  experiences: [],
})
const retrospective = ref<MarketingAlertRetrospective>(emptyRetrospective())
const alertOwnerOptions = computed(() =>
  performance.value.workload.filter((item) => item.assignee_id),
)
const availableAlertMembers = computed(() =>
  alertMembers.value.filter((member) => member.id !== selectedAlert.value?.assignee_id),
)
const availableSubscriberMembers = computed(() => {
  const subscriberIds = new Set(selectedAlert.value?.subscribers.map((item) => item.user_id) || [])
  return alertMembers.value.filter((member) => !subscriberIds.has(member.id))
})

const emptyOverview = (): MarketingOperationsOverview => ({
  range: { days: 7, start_date: '—', end_date: '—', task_id: null },
  health: {
    status: 'HEALTHY',
    label: '等待数据',
    summary: '正在汇总当前工作空间的运行数据。',
    critical_count: 0,
    warning_count: 0,
  },
  metrics: {
    active_task_count: 0,
    task_count: 0,
    customer_count: 0,
    conversation_count: 0,
    conversation_success_rate: 0,
    avg_response_seconds: 0,
    slow_conversation_count: 0,
    total_tokens: 0,
    quality_review_count: 0,
    quality_pass_rate: 0,
    quality_issue_count: 0,
    pending_review_count: 0,
    preflight_count: 0,
    intercepted_count: 0,
    bypassed_count: 0,
    runtime_error_count: 0,
    overdue_batch_count: 0,
    converted_customer_count: 0,
    conversion_count: 0,
    conversion_rate: 0,
  },
  trend: [],
  issues: [],
  task_health: [],
  generated_at: '',
})

const overview = ref<MarketingOperationsOverview>(emptyOverview())

const alertSummaryItems = computed(() => [
  { status: '' as const, label: '全部告警', value: alertPage.value.summary.total_count },
  { status: 'OPEN' as const, label: '待处理', value: alertPage.value.summary.open_count },
  { status: 'CLAIMED' as const, label: '已认领', value: alertPage.value.summary.claimed_count },
  {
    status: 'PROCESSING' as const,
    label: '处理中',
    value: alertPage.value.summary.processing_count,
  },
  { status: 'CLOSED' as const, label: '已关闭', value: alertPage.value.summary.closed_count },
])

const healthIcon = computed(() =>
  overview.value.health.status === 'HEALTHY' ? CircleCheckFilled : WarningFilled,
)

const primaryMetrics = computed(() => [
  {
    key: 'conversation',
    label: '客户对话',
    value: overview.value.metrics.conversation_count.toLocaleString(),
    hint: `成功率 ${overview.value.metrics.conversation_success_rate}%`,
    tone: overview.value.metrics.runtime_error_count ? 'danger' : 'success',
  },
  {
    key: 'latency',
    label: '平均响应时间',
    value: formatDuration(overview.value.metrics.avg_response_seconds),
    hint: `超过10秒 ${overview.value.metrics.slow_conversation_count} 条`,
    tone: overview.value.metrics.slow_conversation_count ? 'warning' : 'success',
  },
  {
    key: 'quality',
    label: '质检通过率',
    value: `${overview.value.metrics.quality_pass_rate}%`,
    hint: `发现问题 ${overview.value.metrics.quality_issue_count} 条`,
    tone: overview.value.metrics.quality_issue_count ? 'warning' : 'success',
  },
  {
    key: 'pending',
    label: '待人工复核',
    value: overview.value.metrics.pending_review_count.toLocaleString(),
    hint: '问题回答处理队列',
    tone: overview.value.metrics.pending_review_count ? 'warning' : 'success',
  },
  {
    key: 'intercept',
    label: '灰度拦截',
    value: overview.value.metrics.intercepted_count.toLocaleString(),
    hint: `异常旁路 ${overview.value.metrics.bypassed_count} 条`,
    tone: overview.value.metrics.bypassed_count ? 'danger' : 'neutral',
  },
  {
    key: 'conversion',
    label: '客户转化率',
    value: `${overview.value.metrics.conversion_rate}%`,
    hint: `已办理 ${overview.value.metrics.converted_customer_count} 人`,
    tone: 'primary',
  },
])

const secondaryMetrics = computed(() => [
  { label: '进行中任务', value: overview.value.metrics.active_task_count },
  { label: '客户总数', value: overview.value.metrics.customer_count },
  { label: '运行错误', value: overview.value.metrics.runtime_error_count, tone: 'danger' },
  { label: '逾期批次', value: overview.value.metrics.overdue_batch_count, tone: 'warning' },
  { label: '发送前检测', value: overview.value.metrics.preflight_count },
  { label: 'Token消耗', value: overview.value.metrics.total_tokens.toLocaleString() },
])

const trendOption = computed(() => ({
  xData: overview.value.trend.map((item) => item.date.slice(5)),
  yData: [
    {
      name: '对话量',
      data: overview.value.trend.map((item) => item.conversation_count),
      area: true,
      smooth: true,
    },
    {
      name: '质检问题',
      data: overview.value.trend.map((item) => item.quality_issue_count),
      area: false,
      smooth: true,
    },
  ],
}))

const issueSeverityMap = { CRITICAL: '紧急', WARNING: '关注', INFO: '提示' }
const taskHealthMap = {
  HEALTHY: { label: '正常', type: 'success' as const },
  ATTENTION: { label: '需关注', type: 'warning' as const },
  ERROR: { label: '有异常', type: 'danger' as const },
}
const taskStatusMap = { DRAFT: '草稿', RUNNING: '进行中', PAUSED: '已暂停', FINISHED: '已结束' }
const alertSeverityMap = {
  CRITICAL: { label: '紧急', type: 'danger' as const },
  WARNING: { label: '关注', type: 'warning' as const },
  INFO: { label: '提示', type: 'info' as const },
}
const alertStatusMap = {
  OPEN: { label: '待处理', type: 'danger' as const },
  CLAIMED: { label: '已认领', type: 'warning' as const },
  PROCESSING: { label: '处理中', type: 'primary' as const },
  CLOSED: { label: '已关闭', type: 'success' as const },
}
const noiseLevelMap = {
  LOW: { type: 'info' as const },
  MEDIUM: { type: 'warning' as const },
  HIGH: { type: 'danger' as const },
}
const alertActionMap = {
  CREATED: '系统创建',
  REFRESHED: '指标刷新',
  CLAIMED: '认领告警',
  STARTED: '开始处理',
  CLOSED: '关闭告警',
  REOPENED: '重新打开',
  RESPONSE_OVERDUE: '首次响应超时',
  RESOLUTION_OVERDUE: '处理超时',
  ASSIGNED: '指派负责人',
  TRANSFERRED: '转派负责人',
  COMMENTED: '协作评论',
  SUBSCRIBED: '添加关注人',
  UNSUBSCRIBED: '移除关注人',
  ATTACHED: '上传附件',
}
const alertRoundEndReasonMap = {
  TRANSFERRED: '已转派',
  CLOSED: '已关闭',
  REOPENED: '已重开',
}

function getTaskHealth(status: MarketingTaskHealth['health_status']) {
  return taskHealthMap[status] || taskHealthMap.HEALTHY
}

function getTaskStatus(status: MarketingTaskHealth['task_status']) {
  return taskStatusMap[status] || status
}

function getAlertSeverity(severity: MarketingAlertSeverity) {
  return alertSeverityMap[severity]
}

function getAlertStatus(status: MarketingAlertStatus) {
  return alertStatusMap[status]
}

function getNoiseLevel(level: MarketingAlertNoiseItem['noise_level']) {
  return noiseLevelMap[level]
}

function getAlertAction(action: MarketingAlert['actions'][number]['action']) {
  return alertActionMap[action]
}

function getRoundEndReason(reason: MarketingAlert['handling_rounds'][number]['end_reason']) {
  return reason ? alertRoundEndReasonMap[reason] : ''
}

function formatDuration(seconds: number) {
  if (!seconds) return '0 秒'
  if (seconds < 1) return `${Math.round(seconds * 1000)} ms`
  return `${seconds.toFixed(seconds >= 10 ? 1 : 2)} 秒`
}

function formatWorkDuration(seconds: number) {
  if (!seconds) return '—'
  if (seconds < 60) return `${Math.round(seconds)} 秒`
  if (seconds < 3600) return `${(seconds / 60).toFixed(seconds >= 600 ? 0 : 1)} 分钟`
  return `${(seconds / 3600).toFixed(seconds >= 36_000 ? 0 : 1)} 小时`
}

function formatFileSize(bytes: number) {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  return `${(bytes / 1024 / 1024).toFixed(1)} MB`
}

function getSlaRateClass(rate: number) {
  if (rate >= 90) return 'text-success'
  if (rate >= 70) return 'text-warning'
  return rate ? 'text-danger' : ''
}

function formatRemaining(dueAt?: string | null) {
  if (!dueAt) return '未配置'
  const diffMinutes = Math.round((new Date(dueAt).getTime() - Date.now()) / 60_000)
  if (diffMinutes <= 0) return `已超时 ${Math.abs(diffMinutes)} 分钟`
  if (diffMinutes < 60) return `剩余 ${diffMinutes} 分钟`
  return `剩余 ${(diffMinutes / 60).toFixed(diffMinutes >= 600 ? 0 : 1)} 小时`
}

function formatSlaTime(dueAt?: string | null, completedAt?: string | null) {
  if (completedAt) return `已于 ${datetimeFormat(completedAt)} 完成`
  if (!dueAt) return '未配置'
  return `${datetimeFormat(dueAt)}（${formatRemaining(dueAt)}）`
}

function getAlertSla(alert: MarketingAlert) {
  if (alert.status === 'CLOSED') {
    return {
      label: '已完成',
      hint: alert.closed_at ? datetimeFormat(alert.closed_at) : '已关闭',
      type: 'success' as const,
    }
  }
  if (alert.resolution_overdue) {
    return {
      label: '处理超时',
      hint: formatRemaining(alert.resolution_due_at),
      type: 'danger' as const,
    }
  }
  if (alert.response_overdue) {
    return {
      label: '响应超时',
      hint: formatRemaining(alert.response_due_at),
      type: 'danger' as const,
    }
  }
  if (alert.first_responded_at) {
    return {
      label: '已响应',
      hint: formatRemaining(alert.resolution_due_at),
      type: 'primary' as const,
    }
  }
  return { label: '待响应', hint: formatRemaining(alert.response_due_at), type: 'warning' as const }
}

function loadOverview() {
  const params = {
    days: filters.value.days,
    ...(filters.value.task_id ? { task_id: filters.value.task_id } : {}),
  }
  return marketingOperationsApi.getOperationsOverview(params, loading).then((res) => {
    overview.value = res.data
  })
}

function loadAlerts(currentPage = alertPage.value.current) {
  return marketingOperationsApi
    .getAlertPage(
      { current_page: currentPage, page_size: alertPage.value.size },
      {
        status: alertFilters.value.status,
        severity: alertFilters.value.severity,
        keyword: alertFilters.value.keyword,
        ...(alertFilters.value.assignee && alertFilters.value.assignee !== 'UNASSIGNED'
          ? { assignee_id: alertFilters.value.assignee }
          : {}),
        unassigned: alertFilters.value.assignee === 'UNASSIGNED',
        active_only: alertFilters.value.active_only,
        sla_overdue: alertFilters.value.sla_overdue,
      },
      alertLoading,
    )
    .then((res) => {
      alertPage.value = res.data
      if (selectedAlert.value) {
        const latest = res.data.records.find((item) => item.id === selectedAlert.value?.id)
        if (latest) selectedAlert.value = latest
      }
    })
}

function loadPerformance() {
  return marketingOperationsApi
    .getAlertPerformance(filters.value.days, performanceLoading)
    .then((res) => {
      performance.value = res.data
    })
}

function loadNoiseAnalysis() {
  return marketingOperationsApi
    .getAlertNoiseAnalysis(filters.value.days, noiseAnalysisLoading)
    .then((res) => {
      noiseAnalysis.value = res.data
    })
}

function loadRetrospective() {
  return marketingOperationsApi
    .getAlertRetrospective(filters.value.days, retrospectiveRootCause.value, retrospectiveLoading)
    .then((res) => {
      retrospective.value = res.data
    })
}

function exportRetrospective() {
  return marketingOperationsApi.exportAlertRetrospective(
    filters.value.days,
    retrospectiveRootCause.value,
    exportingRetrospective,
  )
}

function syncAndLoadAlerts() {
  return marketingOperationsApi.syncAlerts(filters.value.days, alertLoading).then(() => {
    window.dispatchEvent(new Event('marketing-notification-updated'))
    return Promise.all([loadAlerts(1), loadPerformance(), loadNoiseAnalysis(), loadRetrospective()])
  })
}

function refreshDashboard() {
  return Promise.all([loadOverview(), syncAndLoadAlerts()])
}

function loadAll() {
  return Promise.all([
    marketingTaskApi.getTaskList().then((res) => {
      tasks.value = res.data
    }),
    loadOverview(),
    syncAndLoadAlerts(),
  ])
}

function setAlertStatus(status: MarketingAlertStatus | '') {
  alertFilters.value.status = status
  if (status === 'CLOSED') alertFilters.value.active_only = false
  loadAlerts(1)
}

function drillDownOwner(row: MarketingAlertOwnerPerformance) {
  alertFilters.value.status = ''
  alertFilters.value.assignee = row.assignee_id || 'UNASSIGNED'
  alertFilters.value.active_only = true
  alertFilters.value.sla_overdue = false
  loadAlerts(1).then(() => {
    document
      .querySelector('.alert-workbench')
      ?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  })
}

function openAlert(alert: MarketingAlert) {
  selectedAlert.value = alert
  handleNote.value = ''
  closeRootCause.value = ''
  closeResolutionType.value = ''
  closeImpactScope.value = ''
  collaborationAssignee.value = ''
  collaborationNote.value = ''
  commentNote.value = ''
  subscriberMember.value = ''
  alertDrawerVisible.value = true
  if (!alertMembers.value.length) {
    marketingOperationsApi.getAlertMembers().then((res) => {
      alertMembers.value = res.data
    })
  }
}

function openAlertFromRoute(alertId: unknown) {
  if (typeof alertId !== 'string' || !alertId || selectedAlert.value?.id === alertId) return
  marketingOperationsApi.getAlert(alertId, alertLoading).then((res) => openAlert(res.data))
}

function openAlertById(alertId: string) {
  marketingOperationsApi.getAlert(alertId, alertLoading).then((res) => openAlert(res.data))
}

function applyNoiseExperience(item: MarketingAlertNoiseItem) {
  marketingOperationsApi.getAlert(item.id, alertLoading).then((res) => {
    openAlert(res.data)
    closeRootCause.value = item.suggested_root_cause_category
    closeResolutionType.value = item.suggested_resolution_type
    handleNote.value = item.suggested_note ? `参考历史经验：${item.suggested_note}` : ''
    ElMessage.success('已带入历史归因，请核对本轮影响范围后关闭')
  })
}

function clearAlertRoute() {
  selectedAlert.value = undefined
  if (!route.query.alert_id) return
  const query = { ...route.query }
  delete query.alert_id
  router.replace({ query })
}

function handleSelectedAlert(action: MarketingAlertHandleAction) {
  if (!selectedAlert.value) return
  const closureData =
    action === 'CLOSE'
      ? {
          root_cause_category: closeRootCause.value || undefined,
          resolution_type: closeResolutionType.value || undefined,
          impact_scope: closeImpactScope.value,
        }
      : {}
  marketingOperationsApi
    .handleAlert(
      selectedAlert.value.id,
      { action, note: handleNote.value, ...closureData },
      handling,
    )
    .then((res) => {
      selectedAlert.value = res.data
      handleNote.value = ''
      closeRootCause.value = ''
      closeResolutionType.value = ''
      closeImpactScope.value = ''
      ElMessage.success(
        action === 'CLOSE'
          ? '告警已关闭'
          : action === 'REOPEN'
            ? '告警已重新打开'
            : '处理状态已更新',
      )
      Promise.all([loadAlerts(), loadPerformance(), loadNoiseAnalysis(), loadRetrospective()])
    })
}

function collaborateSelectedAlert(
  action: MarketingAlertCollaborateAction,
  data: { assignee_id?: string; note?: string },
) {
  if (!selectedAlert.value) return Promise.resolve()
  return marketingOperationsApi
    .collaborateAlert(selectedAlert.value.id, { action, ...data }, collaborating)
    .then((res) => {
      selectedAlert.value = res.data
      collaborationAssignee.value = ''
      collaborationNote.value = ''
      commentNote.value = ''
      return Promise.all([loadAlerts(), loadPerformance()])
    })
}

function submitAssignment() {
  if (!selectedAlert.value || !collaborationAssignee.value) return
  const action: MarketingAlertCollaborateAction = selectedAlert.value.capabilities.can_assign
    ? 'ASSIGN'
    : 'TRANSFER'
  if (action === 'TRANSFER' && !collaborationNote.value.trim()) {
    ElMessage.warning('转派时必须填写原因')
    return
  }
  collaborateSelectedAlert(action, {
    assignee_id: collaborationAssignee.value,
    note: collaborationNote.value,
  }).then(() => ElMessage.success(action === 'ASSIGN' ? '告警已指派' : '告警已转派'))
}

function submitComment() {
  const note = commentNote.value.trim()
  if (!note) return
  collaborateSelectedAlert('COMMENT', { note }).then(() => ElMessage.success('协作评论已发布'))
}

function updateSubscriber(action: 'ADD' | 'REMOVE', userId: string) {
  if (!selectedAlert.value) return Promise.resolve()
  return marketingOperationsApi
    .updateAlertSubscriber(selectedAlert.value.id, { action, user_id: userId }, subscriberUpdating)
    .then((res) => {
      selectedAlert.value = res.data
      subscriberMember.value = ''
      window.dispatchEvent(new Event('marketing-notification-updated'))
      return loadAlerts()
    })
}

function addSubscriber() {
  if (!subscriberMember.value) return
  updateSubscriber('ADD', subscriberMember.value).then(() => ElMessage.success('关注人已添加'))
}

function removeSubscriber(userId: string) {
  updateSubscriber('REMOVE', userId).then(() => ElMessage.success('关注人已移除'))
}

async function uploadAlertFile(options: UploadRequestOptions) {
  if (!selectedAlert.value) return
  const file = options.file
  if (file.size > 10 * 1024 * 1024) {
    ElMessage.warning('附件不能超过 10 MB')
    return
  }
  attachmentUploading.value = true
  try {
    const res = await marketingOperationsApi.uploadAlertAttachment(selectedAlert.value.id, file)
    selectedAlert.value = res.data
    options.onSuccess(res)
    window.dispatchEvent(new Event('marketing-notification-updated'))
    ElMessage.success('附件已上传')
    await loadAlerts()
  } finally {
    attachmentUploading.value = false
  }
}

function openRuleDrawer() {
  ruleDrawerVisible.value = true
  ruleLoading.value = true
  Promise.all([
    marketingOperationsApi.getAlertRuleEffect(filters.value.days),
    marketingOperationsApi.getAlertMembers(),
  ])
    .then(([effectRes, memberRes]) => {
      alertRuleEffect.value = effectRes.data
      alertMembers.value = memberRes.data
    })
    .finally(() => {
      ruleLoading.value = false
    })
}

function loadRuleEffect() {
  return marketingOperationsApi.getAlertRuleEffect(filters.value.days).then((res) => {
    alertRuleEffect.value = res.data
  })
}

function confidenceLabel(confidence: MarketingAlertRuleEffectItem['recommendation']['confidence']) {
  return { LOW: '低', MEDIUM: '中', HIGH: '高' }[confidence]
}

async function persistRule(rule: MarketingAlertRule, changeReason: string) {
  if (rule.resolution_sla_minutes < rule.response_sla_minutes) {
    ElMessage.warning('处理完成时限不能小于首次响应时限')
    return false
  }
  savingRuleId.value = rule.id
  try {
    const res = await marketingOperationsApi.updateAlertRule(rule.id, {
      enabled: rule.enabled,
      threshold: rule.threshold,
      severity: rule.severity,
      response_sla_minutes: rule.response_sla_minutes,
      resolution_sla_minutes: rule.resolution_sla_minutes,
      escalation_user_id: rule.escalation_user_id || null,
      change_reason: changeReason,
    })
    Object.assign(rule, res.data)
    await syncAndLoadAlerts()
    await loadRuleEffect()
    return true
  } finally {
    savingRuleId.value = ''
  }
}

function saveRule(rule: MarketingAlertRule) {
  persistRule(rule, '人工调整告警规则').then((saved) => {
    if (saved) ElMessage.success('告警规则已保存')
  })
}

function applyRuleRecommendation(effect: MarketingAlertRuleEffectItem) {
  ElMessageBox.confirm(
    `确认将“${effect.rule.name}”的阈值从 ${effect.rule.threshold} 调整为 ${effect.recommendation.threshold}？`,
    '应用推荐阈值',
    { type: 'warning', confirmButtonText: '确认应用', cancelButtonText: '取消' },
  ).then(async () => {
    effect.rule.threshold = effect.recommendation.threshold
    const saved = await persistRule(
      effect.rule,
      `应用效果评估推荐阈值 ${effect.recommendation.threshold}`,
    )
    if (saved) ElMessage.success('推荐阈值已应用并重新评估')
  })
}

function rollbackRuleChange(
  effect: MarketingAlertRuleEffectItem,
  change: MarketingAlertRuleChange,
) {
  ElMessageBox.confirm(
    `确认将“${effect.rule.name}”回滚到 V${change.version}（阈值 ${change.snapshot.threshold}）？当前配置会自动保存为新的回滚记录。`,
    '回滚规则版本',
    { type: 'warning', confirmButtonText: '确认回滚', cancelButtonText: '取消' },
  ).then(async () => {
    rollingBackRuleId.value = effect.rule.id
    try {
      await marketingOperationsApi.rollbackAlertRule(effect.rule.id, change.id)
      await syncAndLoadAlerts()
      await loadRuleEffect()
      ElMessage.success(`已回滚到 V${change.version}`)
    } finally {
      rollingBackRuleId.value = ''
    }
  })
}

function openIssue(issue: MarketingOperationsIssue) {
  router.push(issue.route)
}

function openTask(row: MarketingTaskHealth) {
  router.push(row.quality_issue_count ? '/marketing-quality' : '/marketing-task')
}

watch(
  () => route.query.alert_id,
  (alertId) => openAlertFromRoute(alertId),
)

onMounted(() => {
  loadAll().then(() => openAlertFromRoute(route.query.alert_id))
})
</script>

<style scoped lang="scss">
.operations-page {
  --ink: #182230;
  --muted: #647184;
  --line: #dfe5eb;
  --paper: #ffffff;
  --navy: #183b56;
  --teal: #0f766e;
  min-height: 100%;
  color: var(--ink);
  background:
    linear-gradient(rgba(27, 55, 75, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(27, 55, 75, 0.035) 1px, transparent 1px), #f5f7f8;
  background-size: 28px 28px;
}

.page-header,
.header-actions,
.health-panel,
.card-heading,
.metric-topline {
  display: flex;
  align-items: center;
}

.page-header {
  justify-content: space-between;
  gap: 24px;
  margin: 0 24px 18px;
}

.page-header h2 {
  margin: 3px 0 4px;
  font-family: 'STSong', 'Songti SC', serif;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.page-header p,
.health-copy p,
.metric-card p {
  margin: 0;
  color: var(--muted);
}

.eyebrow {
  color: var(--teal);
  font-family: 'SFMono-Regular', Consolas, monospace;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.header-actions {
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
}

.health-panel {
  position: relative;
  gap: 18px;
  min-height: 112px;
  margin-bottom: 16px;
  padding: 22px 26px;
  overflow: hidden;
  border: 1px solid #bfd9d3;
  border-left: 5px solid var(--teal);
  border-radius: 10px;
  background: #f7fcfa;
  box-shadow: 0 10px 25px rgba(31, 55, 71, 0.06);
}

.health-panel.is-warning {
  border-color: #ead7a8;
  border-left-color: #c78916;
  background: #fffbf1;
}

.health-panel.is-critical {
  border-color: #e6b8b5;
  border-left-color: #b83a32;
  background: #fff8f7;
}

.health-marker {
  display: grid;
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  color: var(--teal);
  background: #dcefea;
  font-size: 26px;
}

.is-warning .health-marker {
  color: #a66c00;
  background: #f7e9c4;
}

.is-critical .health-marker {
  color: #a42c25;
  background: #f4d9d6;
}

.health-copy {
  min-width: 260px;
  flex: 1;
}

.health-copy > span,
.health-period span,
.health-counts span {
  display: block;
  margin-bottom: 3px;
  color: var(--muted);
  font-size: 12px;
}

.health-copy > strong {
  display: block;
  margin-bottom: 5px;
  font-size: 20px;
}

.health-period {
  padding: 0 28px;
  border-right: 1px solid var(--line);
  border-left: 1px solid var(--line);
}

.health-period strong,
.health-period small {
  display: block;
}

.health-period small {
  margin-top: 5px;
  color: var(--muted);
}

.health-counts {
  display: flex;
  gap: 24px;
}

.health-counts strong {
  font-size: 24px;
  font-variant-numeric: tabular-nums;
}

.metric-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(150px, 1fr));
  gap: 12px;
}

.metric-card {
  min-width: 0;
  padding: 18px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: var(--paper);
}

.metric-topline {
  justify-content: space-between;
  color: var(--muted);
  font-size: 13px;
}

.metric-topline i {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #8d99a6;
}

.metric-topline .tone-success {
  background: #198754;
}

.metric-topline .tone-warning {
  background: #c78916;
}

.metric-topline .tone-danger {
  background: #c0392b;
}

.metric-topline .tone-primary {
  background: #246b8e;
}

.metric-card > strong {
  display: block;
  margin: 12px 0 5px;
  font-family: 'DIN Alternate', 'Avenir Next', sans-serif;
  font-size: 27px;
  font-variant-numeric: tabular-nums;
}

.metric-card p {
  overflow: hidden;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.signal-strip {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  margin: 12px 0 16px;
  border: 1px solid var(--line);
  border-radius: 8px;
  background: #edf1f3;
}

.signal-strip > div {
  display: flex;
  justify-content: space-between;
  padding: 11px 16px;
  border-right: 1px solid var(--line);
  font-size: 13px;
}

.signal-strip > div:last-child {
  border-right: none;
}

.signal-strip span {
  color: var(--muted);
}

.text-danger {
  color: #b6322a;
}

.text-warning {
  color: #9b6500;
}

.text-success {
  color: #198754;
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.65fr) minmax(360px, 1fr);
  gap: 16px;
  margin-bottom: 16px;
}

.trend-card,
.issue-card,
.alert-workbench,
.owner-performance-card,
.noise-analysis-card,
.retrospective-card,
.task-health-card {
  border: 1px solid var(--line);
  border-radius: 8px;
}

.alert-workbench {
  margin-bottom: 16px;
}

.owner-performance-card,
.noise-analysis-card,
.retrospective-card {
  margin-bottom: 16px;
}

.noise-summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1px;
  overflow: hidden;
  margin-bottom: 16px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--line);
}

.noise-summary > div {
  padding: 14px 16px;
  background: #f7f9fa;
}

.noise-summary span,
.noise-summary strong {
  display: block;
}

.noise-summary span {
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
}

.noise-summary strong {
  font-size: 22px;
}

.noise-analysis-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.noise-analysis-grid > section {
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: #f8fafb;
}

.noise-analysis-grid h4 {
  margin: 0 0 12px;
}

.noise-alert-list,
.merge-suggestion-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.noise-alert-list article,
.merge-suggestion-list article {
  padding: 11px 12px;
  border: 1px solid var(--line);
  border-radius: 6px;
  background: #fff;
}

.noise-alert-heading,
.merge-suggestion-list article > div:first-child {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}

.noise-alert-list p,
.merge-suggestion-list p {
  margin: 7px 0;
  color: var(--muted);
  font-size: 12px;
}

.noise-alert-list small,
.merge-suggestion-list small {
  display: block;
  color: #5d6b75;
  line-height: 1.6;
}

.noise-alert-actions {
  margin-top: 5px;
}

.merge-candidates {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-start !important;
  gap: 6px;
  margin: 8px 0;
}

.retrospective-actions {
  display: flex;
  gap: 10px;
}

.retrospective-summary {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  overflow: hidden;
  margin-bottom: 16px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--line);
}

.retrospective-summary > div {
  padding: 14px 16px;
  background: #f7f9fa;
}

.retrospective-summary span,
.retrospective-summary strong {
  display: block;
}

.retrospective-summary span {
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
}

.retrospective-summary strong {
  font-size: 22px;
}

.retrospective-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.retrospective-grid > section {
  min-height: 170px;
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: #f8fafb;
}

.retrospective-grid h4 {
  margin: 0 0 12px;
}

.distribution-list > div {
  display: grid;
  grid-template-columns: 74px minmax(0, 1fr) 28px;
  gap: 9px;
  align-items: center;
  margin-top: 10px;
  font-size: 12px;
}

.distribution-list strong {
  text-align: right;
}

.recurrence-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.recurrence-list button {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  padding: 9px 10px;
  border: 1px solid var(--line);
  border-radius: 5px;
  text-align: left;
  background: white;
  cursor: pointer;
}

.recurrence-list button span {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.owner-summary-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(120px, 1fr));
  gap: 1px;
  overflow: hidden;
  margin-bottom: 16px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--line);
}

.owner-summary-grid > div {
  padding: 14px 16px;
  background: #f7f9fa;
}

.owner-summary-grid span,
.owner-summary-grid strong {
  display: block;
}

.owner-summary-grid span {
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
}

.owner-summary-grid strong {
  font-family: 'DIN Alternate', 'Avenir Next', sans-serif;
  font-size: 22px;
  font-variant-numeric: tabular-nums;
}

.alert-heading-actions,
.handling-actions,
.alert-detail-head > div:first-child {
  display: flex;
  gap: 8px;
  align-items: center;
}

.alert-summary {
  display: grid;
  grid-template-columns: repeat(5, minmax(110px, 1fr));
  gap: 1px;
  overflow: hidden;
  margin-bottom: 14px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--line);
}

.alert-summary button {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: none;
  color: var(--muted);
  background: #f7f9fa;
  cursor: pointer;
}

.alert-summary button:hover,
.alert-summary button.active {
  color: var(--navy);
  background: #eaf3f5;
}

.alert-summary strong {
  color: var(--ink);
  font-family: 'DIN Alternate', 'Avenir Next', sans-serif;
  font-size: 20px;
}

.alert-toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 14px;
}

.sla-filter {
  margin-left: auto;
}

.alert-title-cell strong,
.alert-title-cell span {
  display: block;
}

.sla-cell small {
  display: block;
  margin-top: 4px;
  color: var(--muted);
  font-size: 11px;
  white-space: nowrap;
}

.alert-title-cell span {
  overflow: hidden;
  margin-top: 3px;
  color: var(--muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.source-active {
  color: #b6322a;
}

.source-recovered {
  color: #198754;
}

.alert-pagination {
  display: flex;
  justify-content: flex-end;
  padding-top: 14px;
}

.alert-detail-head {
  padding: 2px 2px 18px;
  border-bottom: 1px solid var(--line);
}

.alert-detail-head h3 {
  margin: 16px 0 7px;
  font-size: 20px;
}

.alert-detail-head > p,
.rule-intro {
  margin: 0;
  color: var(--muted);
  line-height: 1.7;
}

.alert-detail-head dl {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin: 18px 0 0;
}

.alert-detail-head dl div {
  padding: 10px 12px;
  border-radius: 5px;
  background: #f4f7f8;
}

.alert-detail-head dt {
  margin-bottom: 4px;
  color: var(--muted);
  font-size: 12px;
}

.alert-detail-head dd {
  margin: 0;
  font-weight: 600;
}

.handling-panel,
.collaboration-panel,
.comment-panel,
.subscriber-panel,
.attachment-panel,
.handling-rounds {
  padding: 18px 0;
  border-bottom: 1px solid var(--line);
}

.handling-panel label {
  display: block;
  margin: 12px 0 8px;
  font-weight: 600;
}

.closure-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 10px;
}

.handling-actions {
  justify-content: flex-end;
  margin-top: 12px;
}

.panel-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.panel-title span {
  color: var(--muted);
  font-size: 12px;
}

.assignment-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
  margin-bottom: 10px;
}

.comment-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 10px;
}

.subscriber-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.empty-inline {
  margin-bottom: 10px;
  color: var(--muted);
  font-size: 12px;
}

.subscriber-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 10px;
}

.attachment-list {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 10px;
}

.attachment-list a {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 9px 11px;
  border: 1px solid var(--line);
  border-radius: 5px;
  color: var(--el-color-primary);
  text-decoration: none;
  background: #f8fafb;
}

.attachment-list small {
  color: var(--muted);
  white-space: nowrap;
}

.handling-rounds h4 {
  margin: 0 0 12px;
}

.handling-rounds article {
  padding: 11px 12px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #f8fafb;
}

.handling-rounds article + article {
  margin-top: 8px;
}

.handling-rounds article > div {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.handling-rounds p,
.handling-rounds small {
  display: block;
  margin: 6px 0 0;
  color: var(--muted);
  line-height: 1.5;
}

.experience-hints {
  padding: 18px 0;
  border-bottom: 1px solid var(--line);
}

.experience-hints h4 {
  margin: 0 0 12px;
}

.experience-hints article {
  padding: 11px 12px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #f8fafb;
}

.experience-hints article + article {
  margin-top: 8px;
}

.experience-hints article > div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.experience-hints article span,
.experience-hints article small,
.experience-hints article p {
  color: var(--muted);
}

.experience-hints article p {
  margin: 7px 0;
  line-height: 1.5;
}

.assignment-change {
  color: var(--el-color-primary) !important;
  font-weight: 600;
}

.action-history h4 {
  margin: 20px 0 18px;
}

.history-card {
  padding: 10px 12px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #f8fafb;
}

.history-card > span {
  float: right;
  color: var(--muted);
  font-size: 12px;
}

.history-card p {
  margin: 7px 0 0;
  color: var(--muted);
  line-height: 1.55;
}

.rule-intro {
  padding: 0 0 16px;
}

.rule-effect-summary {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1px;
  overflow: hidden;
  margin-bottom: 10px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: var(--line);
}

.rule-effect-summary > div {
  padding: 12px 14px;
  background: #f7f9fa;
}

.rule-effect-summary span,
.rule-effect-summary strong {
  display: block;
}

.rule-effect-summary span {
  margin-bottom: 5px;
  color: var(--muted);
  font-size: 12px;
}

.rule-effect-summary strong {
  font-size: 20px;
}

.rule-simulation-note {
  margin: 0 0 14px;
  color: #8a6515;
  font-size: 12px;
  line-height: 1.55;
}

.rule-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.rule-row {
  padding: 14px;
  border: 1px solid var(--line);
  border-radius: 7px;
  background: #f8fafb;
}

.rule-head {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  justify-content: space-between;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--line);
}

.rule-fields {
  display: grid;
  grid-template-columns: 110px 130px 145px 145px;
  gap: 12px;
  align-items: end;
  padding-top: 12px;
}

.rule-fields label > span {
  display: block;
  margin-bottom: 6px;
  color: var(--muted);
  font-size: 12px;
}

.rule-fields :deep(.el-input-number),
.rule-fields :deep(.el-select) {
  width: 100%;
}

.escalation-field {
  grid-column: span 3;
}

.rule-save {
  width: 100%;
}

.rule-copy strong,
.rule-copy span {
  display: block;
}

.rule-copy span {
  margin-top: 4px;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.45;
}

.rule-effect-panel {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px dashed #cfd8df;
}

.rule-metrics {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 8px;
}

.rule-metrics > div {
  padding: 10px 12px;
  border-radius: 5px;
  background: #edf2f4;
}

.rule-metrics span,
.rule-metrics strong {
  display: block;
}

.rule-metrics span {
  margin-bottom: 4px;
  color: var(--muted);
  font-size: 11px;
}

.rule-metrics strong {
  font-size: 17px;
}

.rule-recommendation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 10px;
  padding: 11px 12px;
  border: 1px solid #d6e2e5;
  border-radius: 6px;
  background: #f5faf9;
}

.rule-recommendation.has-change {
  border-color: #e5c982;
  background: #fffaf0;
}

.rule-recommendation span,
.rule-recommendation strong,
.rule-recommendation small {
  display: block;
}

.rule-recommendation span,
.rule-recommendation small {
  color: var(--muted);
  font-size: 11px;
}

.rule-recommendation strong {
  margin: 4px 0;
}

.threshold-simulations {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
  margin-top: 10px;
}

.threshold-simulations article {
  position: relative;
  padding: 9px 10px;
  border: 1px solid var(--line);
  border-radius: 5px;
  background: #fff;
}

.threshold-simulations span,
.threshold-simulations strong,
.threshold-simulations small {
  display: block;
}

.threshold-simulations span,
.threshold-simulations small {
  color: var(--muted);
  font-size: 11px;
}

.threshold-simulations strong {
  margin: 4px 0;
  font-size: 13px;
}

.threshold-simulations .el-tag {
  position: absolute;
  top: 7px;
  right: 7px;
}

.rule-history {
  margin-top: 13px;
}

.rule-history h4 {
  margin: 0 0 8px;
  font-size: 13px;
}

.rule-history > article {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 9px 10px;
  border-top: 1px solid var(--line);
}

.rule-history > article > div {
  min-width: 0;
}

.rule-history span,
.rule-history small,
.rule-history p {
  display: block;
  margin: 3px 0 0;
  color: var(--muted);
  font-size: 11px;
}

.rule-history p {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-heading {
  justify-content: space-between;
  gap: 16px;
}

.card-heading strong,
.card-heading span {
  display: block;
}

.card-heading strong {
  margin-bottom: 3px;
  font-size: 16px;
}

.card-heading span,
.legend-note {
  color: var(--muted);
  font-size: 12px;
}

.issue-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.issue-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) 34px 34px;
  gap: 10px;
  align-items: center;
  width: 100%;
  padding: 12px;
  border: 1px solid transparent;
  border-radius: 6px;
  color: inherit;
  text-align: left;
  background: #f7f9fa;
  cursor: pointer;
  transition: 160ms ease;
}

.issue-row:hover {
  border-color: #a9c4cf;
  background: #f2f8fa;
  transform: translateX(2px);
}

.issue-level {
  padding: 3px 0;
  border-radius: 3px;
  color: #657180;
  font-size: 11px;
  text-align: center;
  background: #e4e9ed;
}

.issue-level.is-critical {
  color: #9d2b24;
  background: #f5dcda;
}

.issue-level.is-warning {
  color: #8a5a00;
  background: #f7e9c5;
}

.issue-copy {
  min-width: 0;
}

.issue-copy strong,
.issue-copy small {
  display: block;
}

.issue-copy small {
  margin-top: 3px;
  overflow: hidden;
  color: var(--muted);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.issue-count {
  font-weight: 700;
  text-align: right;
}

.issue-link {
  color: #236481;
  font-size: 12px;
}

@media (max-width: 1380px) {
  .metric-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .signal-strip {
    grid-template-columns: repeat(3, 1fr);
  }

  .signal-strip > div:nth-child(3) {
    border-right: none;
  }

  .signal-strip > div:nth-child(-n + 3) {
    border-bottom: 1px solid var(--line);
  }

  .owner-summary-grid {
    grid-template-columns: repeat(3, 1fr);
  }

  .noise-summary {
    grid-template-columns: repeat(3, 1fr);
  }

  .retrospective-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 980px) {
  .page-header,
  .health-panel {
    align-items: flex-start;
    flex-direction: column;
  }

  .header-actions {
    justify-content: flex-start;
  }

  .health-period {
    width: 100%;
    padding: 14px 0;
    border: none;
    border-top: 1px solid var(--line);
    border-bottom: 1px solid var(--line);
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .alert-summary {
    grid-template-columns: repeat(2, 1fr);
  }

  .owner-summary-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .noise-summary,
  .noise-analysis-grid,
  .retrospective-summary,
  .retrospective-grid,
  .closure-fields {
    grid-template-columns: 1fr;
  }
}
</style>
