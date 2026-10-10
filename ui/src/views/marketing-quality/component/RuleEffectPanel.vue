<template>
  <el-card class="rule-effect-card" shadow="never">
    <template #header>
      <div class="rule-heading">
        <div>
          <div class="rule-title">
            规则效果分析
            <el-tag type="info" effect="plain">建议层 · 不拦截</el-tag>
          </div>
          <p>用人工复核结果衡量规则准确性，只有通过全部门槛的高风险规则才进入灰度候选。</p>
        </div>
        <el-button :loading="loading" @click="loadEffect">刷新分析</el-button>
      </div>
    </template>

    <div class="gate-strip">
      <span>准入门槛</span>
      <strong>人工样本 ≥ {{ effect.thresholds.min_reviewed_samples }}</strong>
      <strong>问题确认率 ≥ {{ effect.thresholds.min_issue_confirmation_rate }}%</strong>
      <strong>误报率 ≤ {{ effect.thresholds.max_false_positive_rate }}%</strong>
      <strong>仅限高风险规则</strong>
    </div>

    <div class="effect-summary">
      <div>
        <span>问题命中记录</span>
        <strong>{{ effect.summary.hit_record_count }}</strong>
      </div>
      <div>
        <span>已人工复核</span>
        <strong>{{ effect.summary.manually_reviewed_record_count }}</strong>
      </div>
      <div>
        <span>待复核</span>
        <strong>{{ effect.summary.pending_record_count }}</strong>
      </div>
      <div class="eligible-metric">
        <span>可进入灰度候选</span>
        <strong>{{ effect.summary.eligible_rule_count }}</strong>
      </div>
    </div>

    <div class="effect-filters">
      <el-select
        v-model="filters.task_id"
        clearable
        placeholder="全部营销任务"
        @change="loadEffect"
      >
        <el-option v-for="task in tasks" :key="task.id" :label="task.name" :value="task.id" />
      </el-select>
      <el-select v-model="filters.risk_type" clearable placeholder="全部规则" @change="loadEffect">
        <el-option
          v-for="item in effect.risk_type_options"
          :key="item.value"
          :label="item.label"
          :value="item.value"
        />
      </el-select>
      <el-date-picker
        v-model="filters.date_range"
        type="daterange"
        value-format="YYYY-MM-DD"
        range-separator="至"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        @change="loadEffect"
      />
      <el-button @click="resetFilters">重置</el-button>
    </div>

    <el-table v-loading="loading" :data="effect.rules" row-key="risk_type" max-height="520">
      <el-table-column label="质检规则" min-width="190" fixed="left">
        <template #default="{ row }">
          <div class="rule-name">{{ row.label }}</div>
          <div class="rule-code">{{ row.risk_type }}</div>
        </template>
      </el-table-column>
      <el-table-column label="风险级别" width="105">
        <template #default="{ row }">
          <el-tag :type="row.is_high_risk ? 'danger' : 'warning'" effect="plain">
            {{ row.is_high_risk ? '高风险' : '需复核' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="规则命中" width="105" align="right">
        <template #default="{ row }">
          <strong>{{ row.hit_count }}</strong>
          <small>影子 {{ row.shadow_hit_count }}</small>
        </template>
      </el-table-column>
      <el-table-column label="人工样本" width="125">
        <template #default="{ row }">
          <div>{{ row.reviewed_count }} / {{ effect.thresholds.min_reviewed_samples }}</div>
          <small>待处理 {{ row.pending_count }}</small>
        </template>
      </el-table-column>
      <el-table-column label="复核结论" min-width="170">
        <template #default="{ row }">
          <div>确认问题 {{ row.confirmed_issue_count }} · 误报 {{ row.false_positive_count }}</div>
          <small>其中已修订 {{ row.revised_count }}</small>
        </template>
      </el-table-column>
      <el-table-column label="准确性" min-width="190">
        <template #default="{ row }">
          <div class="rate-line">
            <span>确认率</span>
            <strong>{{ formatRate(row.issue_confirmation_rate) }}</strong>
          </div>
          <div class="rate-line muted">
            <span>误报率</span>
            <strong>{{ formatRate(row.false_positive_rate) }}</strong>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="灰度准入" min-width="260" fixed="right">
        <template #default="{ row }">
          <el-tag :type="getGateType(row)" effect="dark">{{ row.gate_label }}</el-tag>
          <div v-if="row.blockers.length" class="blockers">
            {{ getBlockerMessages(row.blockers) }}
          </div>
          <div v-else class="eligible-copy">已满足候选条件，仍需管理员确认后才能灰度。</div>
        </template>
      </el-table-column>
      <template #empty>
        <el-empty description="当前筛选条件下没有规则数据" />
      </template>
    </el-table>
  </el-card>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import marketingTaskApi, {
  type MarketingQualityRuleEffect,
  type MarketingQualityRuleEffectBlocker,
  type MarketingQualityRuleEffectItem,
  type MarketingTask,
} from '@/api/marketing/task'

defineProps<{ tasks: MarketingTask[] }>()

const loading = ref(false)
const filters = ref({
  task_id: '',
  risk_type: '',
  date_range: [] as string[],
})
const effect = ref<MarketingQualityRuleEffect>({
  summary: {
    hit_record_count: 0,
    pending_record_count: 0,
    manually_reviewed_record_count: 0,
    preflight_record_count: 0,
    preflight_risk_record_count: 0,
    eligible_rule_count: 0,
    displayed_rule_count: 0,
  },
  thresholds: {
    min_reviewed_samples: 20,
    min_issue_confirmation_rate: 90,
    max_false_positive_rate: 5,
    high_risk_only: true,
  },
  risk_type_options: [],
  rules: [],
  generated_at: '',
})

function buildParams() {
  const params: Record<string, string> = {}
  if (filters.value.task_id) params.task_id = filters.value.task_id
  if (filters.value.risk_type) params.risk_type = filters.value.risk_type
  if (filters.value.date_range.length === 2) {
    params.date_from = filters.value.date_range[0]
    params.date_to = filters.value.date_range[1]
  }
  return params
}

function loadEffect() {
  marketingTaskApi.getQualityRuleEffect(buildParams(), loading).then((res) => {
    effect.value = res.data
  })
}

function resetFilters() {
  filters.value = { task_id: '', risk_type: '', date_range: [] }
  loadEffect()
}

function formatRate(rate: number | null) {
  return rate === null ? '暂无样本' : `${rate.toFixed(1)}%`
}

function getBlockerMessages(blockers: MarketingQualityRuleEffectBlocker[]) {
  return blockers.map((item) => item.message).join('；')
}

function getGateType(row: MarketingQualityRuleEffectItem): 'success' | 'info' | 'warning' {
  if (row.eligible) return 'success'
  if (row.gate_status === 'NOT_HIGH_RISK') return 'info'
  return 'warning'
}

onMounted(loadEffect)
</script>

<style scoped lang="scss">
.rule-effect-card {
  border-color: #dfe6e2;
}

.rule-heading {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;

  p {
    margin: 6px 0 0;
    color: #718096;
    font-size: 13px;
  }
}

.rule-title {
  display: flex;
  gap: 10px;
  align-items: center;
  color: #203049;
  font-size: 16px;
  font-weight: 700;
}

.gate-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 20px;
  align-items: center;
  padding: 11px 14px;
  color: #476055;
  background: linear-gradient(90deg, #edf7f2, #f8fbf9);
  border-left: 4px solid #278466;

  span {
    color: #278466;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.08em;
  }

  strong {
    font-size: 12px;
    font-weight: 600;
  }
}

.effect-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 14px 0;

  > div {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 13px 15px;
    background: #f7f9fc;
    border: 1px solid #edf0f4;
    border-radius: 6px;
  }

  span {
    color: #718096;
    font-size: 12px;
  }

  strong {
    color: #203049;
    font-size: 24px;
  }

  .eligible-metric {
    background: #edf7f2;

    strong {
      color: #278466;
    }
  }
}

.effect-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 14px;

  :deep(.el-select) {
    width: 220px;
  }
}

.rule-name {
  color: #203049;
  font-weight: 700;
}

.rule-code,
small,
.blockers,
.eligible-copy {
  display: block;
  margin-top: 4px;
  color: #7b8798;
  font-size: 11px;
  line-height: 1.45;
}

.rule-code {
  font-family: 'SFMono-Regular', Consolas, monospace;
}

.rate-line {
  display: flex;
  justify-content: space-between;
  color: #315747;

  &.muted {
    margin-top: 4px;
    color: #7b8798;
  }
}

.eligible-copy {
  color: #278466;
}

@media (max-width: 900px) {
  .rule-heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .effect-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
