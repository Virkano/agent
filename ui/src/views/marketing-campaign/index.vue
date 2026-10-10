<template>
  <div class="p-16-24">
    <h2 class="ml-24 mb-16">营销活动库</h2>
    <el-card
      ><div class="flex-between mb-16">
        <el-button type="primary" @click="openCreate">新建活动</el-button>
        <div>
          <el-select
            v-model="query.status"
            clearable
            placeholder="状态"
            class="mr-8"
            style="width: 120px"
            @change="load"
            ><el-option label="草稿" value="DRAFT" /><el-option
              label="已上线"
              value="ACTIVE" /><el-option label="已暂停" value="PAUSED" /><el-option
              label="已归档"
              value="ARCHIVED" /></el-select
          ><el-input
            v-model="query.name"
            clearable
            placeholder="搜索活动/编码"
            style="width: 220px"
            @change="load"
          />
        </div>
      </div>
      <app-table
        :data="rows"
        :pagination-config="pagination"
        v-loading="loading"
        @changePage="load"
        @sizeChange="resize"
        ><el-table-column prop="name" label="活动" min-width="180" /><el-table-column
          prop="code"
          label="编码"
          width="150"
        /><el-table-column prop="version" label="版本" width="80"
          ><template #default="{ row }">v{{ row.version }}</template></el-table-column
        ><el-table-column prop="status" label="状态" width="100"
          ><template #default="{ row }"
            ><el-tag :type="statusType[row.status || 'DRAFT']">{{
              statusText[row.status || 'DRAFT']
            }}</el-tag></template
          ></el-table-column
        ><el-table-column label="发布审批" width="110"
          ><template #default="{ row }"
            ><el-tag :type="approvalType[row.approval_status || 'DRAFT']">{{
              approvalText[row.approval_status || 'DRAFT']
            }}</el-tag></template
          ></el-table-column
        ><el-table-column prop="priority" label="优先级" width="90" /><el-table-column
          label="生效期"
          min-width="180"
          ><template #default="{ row }"
            >{{ row.effective_start || '长期' }} ~ {{ row.effective_end || '长期' }}</template
          ></el-table-column
        ><el-table-column label="操作" width="250" fixed="right"
          ><template #default="{ row }"
            ><el-button link type="primary" @click="openEdit(row)">编辑</el-button
            ><el-button link type="primary" @click="openEffect(row)">效果</el-button
            ><el-button link type="primary" @click="openVersions(row)">版本</el-button
            ><el-button v-if="row.can_submit" link type="primary" @click="submitCampaign(row)"
              >提交</el-button
            ><el-button v-if="row.can_approve" link type="success" @click="approveCampaign(row)"
              >通过</el-button
            ><el-button link type="danger" @click="archive(row)">归档</el-button></template
          ></el-table-column
        ></app-table
      ></el-card
    >
    <el-drawer v-model="visible" :title="editingId ? '编辑活动' : '新建活动'" size="560px"
      ><el-form :model="form" label-position="top"
        ><el-form-item label="活动名称" required><el-input v-model="form.name" /></el-form-item
        ><el-form-item label="活动编码" required
          ><el-input v-model="form.code" :disabled="Boolean(editingId)" /></el-form-item
        ><el-form-item label="状态"
          ><el-radio-group v-model="form.status"
            ><el-radio-button label="DRAFT">草稿</el-radio-button
            ><el-radio-button label="PAUSED">暂停</el-radio-button></el-radio-group
          ></el-form-item
        ><el-form-item label="客户可见权益" required
          ><el-input v-model="form.benefit" type="textarea" :rows="3" /></el-form-item
        ><el-form-item label="费用说明"><el-input v-model="form.fee_note" /></el-form-item
        ><el-form-item label="合约说明"><el-input v-model="form.contract_note" /></el-form-item
        ><el-row :gutter="12"
          ><el-col :span="12"
            ><el-form-item label="优先级"
              ><el-input-number
                v-model="form.priority"
                :min="1"
                style="width: 100%" /></el-form-item></el-col
          ><el-col :span="12"
            ><el-form-item label="互斥组"
              ><el-input v-model="form.exclusive_group" /></el-form-item></el-col></el-row
        ><el-form-item label="适用套餐关键词（逗号分隔）"
          ><el-input v-model="keywords" placeholder="199, 299" /></el-form-item
        ><el-form-item label="适用省份（逗号分隔）"
          ><el-input v-model="provinces" placeholder="广东, 浙江" /></el-form-item
        ><el-row :gutter="12"
          ><el-col :span="12"
            ><el-form-item label="最低流量 GB"
              ><el-input-number
                v-model="form.min_data_usage_gb"
                :min="0"
                style="width: 100%" /></el-form-item></el-col
          ><el-col :span="12"
            ><el-form-item label="最低通话分钟"
              ><el-input-number
                v-model="form.min_call_usage_minutes"
                :min="0"
                style="width: 100%" /></el-form-item></el-col></el-row
        ><el-form-item label="生效日期"
          ><el-date-picker
            v-model="dates"
            type="daterange"
            value-format="YYYY-MM-DD"
            style="width: 100%" /></el-form-item
        ><el-form-item label="说明"
          ><el-input v-model="form.description" type="textarea" :rows="3" /></el-form-item></el-form
      ><template #footer
        ><el-button @click="visible = false">取消</el-button
        ><el-button type="primary" :loading="submitLoading" @click="save">保存</el-button></template
      ></el-drawer
    >
    <el-drawer v-model="versionVisible" title="活动版本历史" size="960px">
      <el-alert
        title="恢复历史版本会创建一个新的草稿版本，必须重新提交审批；已有任务和会话快照不会改变。"
        type="info"
        :closable="false"
        class="mb-16"
      />
      <el-table :data="versionData" v-loading="versionLoading" border>
        <el-table-column type="expand">
          <template #default="{ row }">
            <el-descriptions :column="2" border class="m-16">
              <el-descriptions-item label="活动名称">{{ row.snapshot.name }}</el-descriptions-item>
              <el-descriptions-item label="活动编码">{{ row.snapshot.code }}</el-descriptions-item>
              <el-descriptions-item label="客户可见权益">{{
                row.snapshot.benefit
              }}</el-descriptions-item>
              <el-descriptions-item label="优先级">{{
                row.snapshot.priority
              }}</el-descriptions-item>
              <el-descriptions-item label="互斥组">{{
                row.snapshot.exclusive_group || '无'
              }}</el-descriptions-item>
              <el-descriptions-item label="适用套餐">{{
                (row.snapshot.plan_keywords || []).join('、') || '不限'
              }}</el-descriptions-item>
              <el-descriptions-item label="适用省份">{{
                (row.snapshot.provinces || []).join('、') || '不限'
              }}</el-descriptions-item>
              <el-descriptions-item label="最低流量"
                >{{ row.snapshot.min_data_usage_gb || 0 }} GB</el-descriptions-item
              >
              <el-descriptions-item label="最低通话"
                >{{ row.snapshot.min_call_usage_minutes || 0 }} 分钟</el-descriptions-item
              >
              <el-descriptions-item label="生效期">{{
                `${row.snapshot.effective_start || '长期'} ~ ${row.snapshot.effective_end || '长期'}`
              }}</el-descriptions-item>
              <el-descriptions-item label="费用说明">{{
                row.snapshot.fee_note
              }}</el-descriptions-item>
              <el-descriptions-item label="合约说明">{{
                row.snapshot.contract_note
              }}</el-descriptions-item>
              <el-descriptions-item label="活动说明" :span="2">{{
                row.snapshot.description || '-'
              }}</el-descriptions-item>
            </el-descriptions>
          </template>
        </el-table-column>
        <el-table-column label="版本" width="80">
          <template #default="{ row }">v{{ row.version }}</template>
        </el-table-column>
        <el-table-column label="变更" width="150">
          <template #default="{ row }">
            {{ versionChangeText[row.change_type] || row.change_type }}
            <span v-if="row.source_version">（来自 v{{ row.source_version }}）</span>
          </template>
        </el-table-column>
        <el-table-column label="审批" width="110">
          <template #default="{ row }">
            <el-tag :type="approvalType[row.approval_status]">{{
              approvalText[row.approval_status]
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="变更字段" min-width="180">
          <template #default="{ row }">{{ changedFieldText(row.changed_fields) }}</template>
        </el-table-column>
        <el-table-column prop="operator_name" label="操作人" width="110" />
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.can_restore" link type="primary" @click="restoreVersion(row)"
              >恢复</el-button
            >
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>
    <el-drawer v-model="effectVisible" title="活动效果复盘与放量建议" size="760px">
      <div v-loading="effectLoading" v-if="effectData">
        <el-alert
          :title="effectData.recommendation.action"
          :description="effectData.recommendation.reason"
          type="info"
          :closable="false"
        />
        <el-descriptions :column="2" border class="mt-16">
          <el-descriptions-item label="命中会话">{{
            effectData.metrics.chat_count
          }}</el-descriptions-item>
          <el-descriptions-item label="命中客户">{{
            effectData.metrics.customer_count
          }}</el-descriptions-item>
          <el-descriptions-item label="意向率"
            >{{ effectData.metrics.intent_rate }}%</el-descriptions-item
          >
          <el-descriptions-item label="转人工率"
            >{{ effectData.metrics.manual_rate }}%</el-descriptions-item
          >
          <el-descriptions-item label="建议下批人数">{{
            effectData.recommendation.suggested_next_batch_size || '-'
          }}</el-descriptions-item>
        </el-descriptions>
        <div class="flex-between mt-16 mb-8">
          <strong>分层效果</strong>
          <el-button :loading="effectExporting" @click="downloadEffectExcel"
            >导出复盘 Excel</el-button
          >
        </div>
        <el-tabs>
          <el-tab-pane label="按省份">
            <effect-segment-table :data="effectData.breakdowns.province" />
          </el-tab-pane>
          <el-tab-pane label="按当前套餐">
            <effect-segment-table :data="effectData.breakdowns.current_plan" />
          </el-tab-pane>
        </el-tabs>
        <el-select
          v-if="effectData.eligible_tasks.length"
          v-model="effectTaskId"
          class="mt-16"
          placeholder="选择要放量的营销任务"
          style="width: 100%"
        >
          <el-option
            v-for="task in effectData.eligible_tasks"
            :key="task.id"
            :label="task.name"
            :value="task.id"
          />
        </el-select>
        <div class="mt-16">
          <el-button
            v-if="effectData.recommendation.action === 'EXPAND'"
            type="primary"
            :disabled="!effectTaskId"
            @click="executeAction('EXPAND')"
            >创建放量批次</el-button
          >
          <el-button
            v-if="effectData.recommendation.action === 'PAUSE'"
            type="warning"
            @click="executeAction('PAUSE')"
            >暂停活动</el-button
          >
        </div>
      </div>
    </el-drawer>
  </div>
</template>
<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import campaignApi, {
  type MarketingCampaign,
  type MarketingCampaignEffect,
  type MarketingCampaignVersion,
} from '@/api/marketing/campaign'
import EffectSegmentTable from './components/effect-segment-table.vue'
const loading = ref(false),
  submitLoading = ref(false),
  visible = ref(false),
  editingId = ref<string>(),
  rows = ref<MarketingCampaign[]>([]),
  query = ref({ name: '', status: '' }),
  pagination = ref({ current_page: 1, page_size: 20, total: 0 }),
  keywords = ref(''),
  provinces = ref(''),
  dates = ref<string[]>([])
const effectVisible = ref(false)
const effectLoading = ref(false)
const effectExporting = ref(false)
const effectData = ref<MarketingCampaignEffect>()
const effectCampaignId = ref('')
const effectTaskId = ref('')
const versionVisible = ref(false)
const versionLoading = ref(false)
const versionCampaign = ref<MarketingCampaign>()
const versionData = ref<MarketingCampaignVersion[]>([])
const defaults = (): MarketingCampaign => ({
  name: '',
  code: '',
  status: 'DRAFT',
  benefit: '',
  fee_note: '费用以当地实际可办理方案为准。',
  contract_note: '办理前会确认优惠期限和合约期。',
  priority: 100,
  exclusive_group: '',
  plan_keywords: [],
  provinces: [],
  min_data_usage_gb: 0,
  min_call_usage_minutes: 0,
  description: '',
})
const form = ref<MarketingCampaign>(defaults())
const statusText: Record<string, string> = {
  DRAFT: '草稿',
  ACTIVE: '已上线',
  PAUSED: '已暂停',
  ARCHIVED: '已归档',
}
const statusType: Record<string, any> = {
  DRAFT: 'info',
  ACTIVE: 'success',
  PAUSED: 'warning',
  ARCHIVED: '',
}
const approvalText: Record<string, string> = {
  DRAFT: '未提交',
  PENDING: '待审批',
  APPROVED: '已通过',
  REJECTED: '已驳回',
}
const approvalType: Record<string, any> = {
  DRAFT: 'info',
  PENDING: 'warning',
  APPROVED: 'success',
  REJECTED: 'danger',
}
const versionChangeText: Record<string, string> = {
  BASELINE: '历史基线',
  CREATE: '创建',
  UPDATE: '编辑',
  RESTORE: '恢复历史版',
  ARCHIVE: '归档',
}
const campaignFieldText: Record<string, string> = {
  name: '活动名称',
  code: '活动编码',
  priority: '优先级',
  exclusive_group: '互斥组',
  benefit: '客户权益',
  fee_note: '费用说明',
  contract_note: '合约说明',
  plan_keywords: '适用套餐',
  provinces: '适用省份',
  min_data_usage_gb: '最低流量',
  min_call_usage_minutes: '最低通话',
  effective_start: '开始日期',
  effective_end: '结束日期',
  description: '活动说明',
}
function changedFieldText(fields: string[]) {
  return fields.length
    ? fields.map((field) => campaignFieldText[field] || field).join('、')
    : '基线版本'
}
function load() {
  campaignApi.page(pagination.value, query.value, loading).then((res: any) => {
    rows.value = res.data.records
    pagination.value.total = res.data.total
    pagination.value.current_page = res.data.current
    pagination.value.page_size = res.data.size
  })
}
function resize() {
  pagination.value.current_page = 1
  load()
}
function openCreate() {
  editingId.value = undefined
  form.value = defaults()
  keywords.value = ''
  provinces.value = ''
  dates.value = []
  visible.value = true
}
function openEdit(row: MarketingCampaign) {
  editingId.value = row.id
  form.value = { ...defaults(), ...row }
  keywords.value = (row.plan_keywords || []).join(',')
  provinces.value = (row.provinces || []).join(',')
  dates.value = [row.effective_start || '', row.effective_end || ''].filter(Boolean)
  visible.value = true
}
function save() {
  if (!form.value.name.trim() || !form.value.code.trim() || !form.value.benefit.trim()) {
    ElMessage.warning('请填写活动名称、编码和客户可见权益')
    return
  }
  const data = {
    ...form.value,
    plan_keywords: keywords.value
      .split(',')
      .map((v) => v.trim())
      .filter(Boolean),
    provinces: provinces.value
      .split(',')
      .map((v) => v.trim())
      .filter(Boolean),
    effective_start: dates.value[0] || null,
    effective_end: dates.value[1] || null,
  }
  const req = editingId.value
    ? campaignApi.update(editingId.value, data, submitLoading)
    : campaignApi.create(data, submitLoading)
  req.then(() => {
    ElMessage.success('保存成功')
    visible.value = false
    load()
  })
}
function archive(row: MarketingCampaign) {
  if (!row.id) return
  ElMessageBox.confirm(
    `归档活动「${row.name}」后，已有任务快照不受影响。确认归档吗？`,
    '归档确认',
    { type: 'warning' },
  ).then(() =>
    campaignApi.remove(row.id!, loading).then(() => {
      ElMessage.success('已归档')
      load()
    }),
  )
}
function submitCampaign(row: MarketingCampaign) {
  if (!row.id) return
  campaignApi.submit(row.id, loading).then(() => {
    ElMessage.success('已提交主管审批')
    load()
  })
}
function approveCampaign(row: MarketingCampaign) {
  if (!row.id) return
  ElMessageBox.confirm(`确认通过活动「${row.name}」并上线吗？`, '活动审批', {
    type: 'warning',
  }).then(() =>
    campaignApi.approve(row.id!, 'APPROVED', '', loading).then(() => {
      ElMessage.success('活动已通过并上线')
      load()
    }),
  )
}
function openEffect(row: MarketingCampaign) {
  if (!row.id) return
  effectVisible.value = true
  effectCampaignId.value = row.id
  effectTaskId.value = ''
  campaignApi.effect(row.id, effectLoading).then((res) => {
    effectData.value = res.data
  })
}

function downloadEffectExcel() {
  if (!effectData.value || !effectCampaignId.value) return
  campaignApi
    .exportEffect(
      effectCampaignId.value,
      `${effectData.value.campaign.name}-活动复盘.xlsx`,
      effectExporting,
    )
    .then(() => ElMessage.success('Excel 复盘已导出'))
}
function openVersions(row: MarketingCampaign) {
  if (!row.id) return
  versionCampaign.value = row
  versionVisible.value = true
  campaignApi.versions(row.id, versionLoading).then((res: any) => {
    versionData.value = res.data.records || []
  })
}
function restoreVersion(row: MarketingCampaignVersion) {
  if (!versionCampaign.value?.id) return
  ElMessageBox.confirm(
    `确认将 v${row.version} 恢复为新的草稿版本吗？恢复后需要重新提交审批。`,
    '恢复历史版本',
    { type: 'warning' },
  ).then(() =>
    campaignApi
      .restore(versionCampaign.value!.id!, row.version, versionLoading)
      .then((res: any) => {
        ElMessage.success(`已生成 v${res.data.version} 草稿版本`)
        versionVisible.value = false
        load()
      }),
  )
}
function executeAction(action: 'EXPAND' | 'PAUSE') {
  campaignApi
    .action(
      effectCampaignId.value,
      { action, task_id: effectTaskId.value || undefined },
      effectLoading,
    )
    .then(() => {
      ElMessage.success(action === 'EXPAND' ? '已创建放量批次，等待审批' : '活动已暂停')
      effectVisible.value = false
      load()
    })
}
onMounted(load)
</script>
