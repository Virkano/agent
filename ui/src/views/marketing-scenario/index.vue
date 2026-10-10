<template>
  <div class="marketing-scenario p-16-24">
    <h2 class="ml-24 mb-16">营销场景</h2>
    <el-card style="--el-card-padding: 0">
      <div class="p-24">
        <div class="flex-between mb-16">
          <div>
            <el-button type="primary" @click="openCreate">创建场景</el-button>
          </div>
          <div class="flex align-center">
            <el-select
              v-model="searchForm.status"
              class="mr-8"
              clearable
              placeholder="状态"
              style="width: 140px"
              @change="getList"
            >
              <el-option label="草稿" value="DRAFT" />
              <el-option label="启用" value="ACTIVE" />
              <el-option label="停用" value="PAUSED" />
            </el-select>
            <el-input
              v-model="searchForm.name"
              clearable
              placeholder="搜索场景/客群/目标"
              style="width: 260px"
              @change="getList"
            />
          </div>
        </div>

        <app-table
          :data="scenarioList"
          :pagination-config="paginationConfig"
          :maxTableHeight="300"
          v-loading="loading"
          @sizeChange="handleSizeChange"
          @changePage="getList"
        >
          <el-table-column prop="name" label="场景名称" min-width="190" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusMap[row.status]?.type">
                {{ statusMap[row.status]?.label || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="target_audience" label="目标客群" min-width="180" show-overflow-tooltip />
          <el-table-column prop="objective" label="营销目标" min-width="180" show-overflow-tooltip />
          <el-table-column prop="channel" label="渠道" width="110" />
          <el-table-column prop="application_name" label="关联智能体" min-width="180" show-overflow-tooltip />
          <el-table-column prop="knowledge_name" label="关联知识库" min-width="180" show-overflow-tooltip />
          <el-table-column label="推荐策略" min-width="160" show-overflow-tooltip>
            <template #default="{ row }">
              {{ getPolicySummary(row) }}
            </template>
          </el-table-column>
          <el-table-column prop="update_time" label="更新时间" width="170">
            <template #default="{ row }">{{ datetimeFormat(row.update_time) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="210" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openSimulation(row)">试运行</el-button>
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </app-table>
      </div>
    </el-card>

    <el-drawer v-model="drawerVisible" :title="editingId ? '编辑营销场景' : '创建营销场景'" size="520px">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="场景名称" prop="name">
          <el-input v-model="form.name" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio-button label="DRAFT">草稿</el-radio-button>
            <el-radio-button label="ACTIVE">启用</el-radio-button>
            <el-radio-button label="PAUSED">停用</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标客群">
          <el-input v-model="form.target_audience" placeholder="例如：199 套餐高价值存量客户" />
        </el-form-item>
        <el-form-item label="营销目标">
          <el-input v-model="form.objective" placeholder="例如：引导升级 299/399 融合套餐" />
        </el-form-item>
        <el-form-item label="触达渠道">
          <el-select v-model="form.channel" style="width: 100%">
            <el-option label="在线客服" value="ONLINE" />
            <el-option label="短信" value="SMS" />
            <el-option label="外呼" value="CALL" />
            <el-option label="企业微信" value="WE_COM" />
          </el-select>
        </el-form-item>
        <el-form-item label="关联智能体">
          <el-select v-model="form.application_id" clearable filterable style="width: 100%">
            <el-option
              v-for="item in applicationOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="关联知识库">
          <el-select v-model="form.knowledge_id" clearable filterable style="width: 100%">
            <el-option
              v-for="item in knowledgeOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-divider content-position="left">营销推荐策略</el-divider>
        <el-alert
          title="策略只用于命中条件明确的客户；未命中时不会承诺优惠或资费。"
          type="info"
          :closable="false"
          class="mb-16"
        />
        <el-form-item label="启用推荐策略">
          <el-switch v-model="recommendationPolicy.enabled" />
        </el-form-item>
        <template v-if="recommendationPolicy.enabled">
          <el-card v-for="(offer, index) in recommendationPolicy.offers" :key="offer.id" class="mb-16">
            <template #header>
              <div class="flex-between">
                <span>活动 {{ index + 1 }}</span>
                <el-button link type="danger" :disabled="recommendationPolicy.offers.length === 1" @click="removeOffer(index)">
                  删除
                </el-button>
              </div>
            </template>
            <el-form-item label="活动名称">
              <el-input v-model="offer.name" maxlength="128" placeholder="例如：199 套餐同价扩容活动" />
            </el-form-item>
            <el-form-item label="客户可见权益">
              <el-input
                v-model="offer.benefit"
                type="textarea"
                :rows="2"
                maxlength="500"
                placeholder="例如：优先核实是否可在原套餐基础上增加通用流量。"
              />
            </el-form-item>
            <el-form-item label="适用当前套餐关键词">
              <el-input v-model="offerPlanKeywords[index]" placeholder="多个关键词用逗号分隔，例如：199,融合" />
            </el-form-item>
            <el-form-item label="适用省份（留空表示不限）">
              <el-input v-model="offerProvinces[index]" placeholder="多个省份用逗号分隔，例如：广东,江苏" />
            </el-form-item>
            <div class="flex">
              <el-form-item label="最低近月流量（GB）" class="mr-12" style="flex: 1">
                <el-input-number v-model="offer.min_data_usage_gb" :min="0" style="width: 100%" />
              </el-form-item>
              <el-form-item label="最低近月通话（分钟）" style="flex: 1">
                <el-input-number v-model="offer.min_call_usage_minutes" :min="0" style="width: 100%" />
              </el-form-item>
            </div>
            <div class="flex">
              <el-form-item label="优先级（数字越小越优先）" class="mr-12" style="flex: 1">
                <el-input-number v-model="offer.priority" :min="1" style="width: 100%" />
              </el-form-item>
              <el-form-item label="互斥组（可选）" style="flex: 1">
                <el-input v-model="offer.exclusive_group" maxlength="64" placeholder="例如：199升级活动" />
              </el-form-item>
            </div>
            <el-form-item label="生效日期（留空表示立即长期生效）">
              <el-date-picker
                v-model="offerEffectiveRanges[index]"
                type="daterange"
                value-format="YYYY-MM-DD"
                range-separator="至"
                start-placeholder="开始日期"
                end-placeholder="结束日期"
                style="width: 100%"
              />
            </el-form-item>
            <el-form-item label="费用边界（客户可见）">
              <el-input
                v-model="offer.fee_note"
                maxlength="300"
                placeholder="例如：费用以当地实际可办理方案为准，办理前会确认月费变化。"
              />
            </el-form-item>
            <el-form-item label="合约边界（客户可见）">
              <el-input
                v-model="offer.contract_note"
                maxlength="300"
                placeholder="例如：办理前会确认优惠期限和合约期。"
              />
            </el-form-item>
          </el-card>
          <el-button plain type="primary" @click="addOffer">新增活动</el-button>
        </template>
        <el-form-item label="配置说明">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="记录推荐策略、合规注意点、后续要接入的渠道或指标"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submit">保存</el-button>
      </template>
    </el-drawer>

    <el-dialog v-model="simulationVisible" title="客户画像试运行" width="520px" destroy-on-close>
      <el-alert title="试运行采用与客户实际对话相同的策略匹配规则，不会创建会话或修改客户数据。" type="info" :closable="false" class="mb-16" />
      <el-form label-position="top">
        <el-form-item label="当前套餐">
          <el-input v-model="simulationForm.current_plan" placeholder="例如：199元套餐" />
        </el-form-item>
        <el-form-item label="省份">
          <el-input v-model="simulationForm.province" placeholder="例如：广东" />
        </el-form-item>
        <div class="flex">
          <el-form-item label="近月流量" class="mr-12" style="flex: 1">
            <el-input v-model="simulationForm.monthly_data_usage" placeholder="例如：80GB" />
          </el-form-item>
          <el-form-item label="近月通话" style="flex: 1">
            <el-input v-model="simulationForm.monthly_call_usage" placeholder="例如：300分钟" />
          </el-form-item>
        </div>
      </el-form>
      <el-alert v-if="simulationResult" :type="simulationResult.status === 'MATCHED' ? 'success' : 'warning'" :closable="false">
        <template #title>
          {{ simulationResult.status === 'MATCHED' ? `命中：${simulationResult.offer_name}` : '未命中任何有效活动' }}
        </template>
        <div v-if="simulationResult.status === 'MATCHED'" class="mt-8">
          优先级 {{ simulationResult.priority }}；{{ simulationResult.benefit }}
        </div>
      </el-alert>
      <template #footer>
        <el-button @click="simulationVisible = false">关闭</el-button>
        <el-button type="primary" :loading="simulationLoading" @click="runSimulation">开始试运行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { onMounted, ref } from 'vue'

import applicationApi from '@/api/application/application'
import knowledgeApi from '@/api/knowledge/knowledge'
import marketingScenarioApi, {
  type MarketingRecommendationOffer,
  type MarketingRecommendationPolicy,
  type MarketingScenario,
} from '@/api/marketing/scenario'
import { datetimeFormat } from '@/utils/time'

const loading = ref(false)
const submitLoading = ref(false)
const drawerVisible = ref(false)
const simulationVisible = ref(false)
const editingId = ref<string>()
const simulationScenarioId = ref<string>()
const formRef = ref<FormInstance>()
const scenarioList = ref<MarketingScenario[]>([])
const applicationOptions = ref<any[]>([])
const knowledgeOptions = ref<any[]>([])
const searchForm = ref({ name: '', status: '' })
const paginationConfig = ref({
  current_page: 1,
  page_size: 20,
  total: 0,
})

const defaultForm = (): MarketingScenario => ({
  name: '',
  target_audience: '',
  objective: '',
  channel: 'ONLINE',
  status: 'DRAFT',
  application_id: null,
  knowledge_id: null,
  config: {},
  description: '',
})

const form = ref<MarketingScenario>(defaultForm())
const recommendationPolicy = ref<MarketingRecommendationPolicy>({ enabled: false, offers: [] })
const offerPlanKeywords = ref<string[]>([])
const offerProvinces = ref<string[]>([])
const offerEffectiveRanges = ref<string[][]>([])
const simulationLoading = ref(false)
const simulationResult = ref<Record<string, any>>()
const simulationForm = ref({
  current_plan: '',
  province: '',
  monthly_data_usage: '',
  monthly_call_usage: '',
})

const rules: FormRules = {
  name: [{ required: true, message: '请输入场景名称', trigger: 'blur' }],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
}

const statusMap: Record<string, { label: string; type: '' | 'success' | 'warning' | 'info' | 'danger' }> = {
  DRAFT: { label: '草稿', type: 'info' },
  ACTIVE: { label: '启用', type: 'success' },
  PAUSED: { label: '停用', type: 'warning' },
}

function getList() {
  marketingScenarioApi
    .getScenarioPage(paginationConfig.value, searchForm.value, loading)
    .then((res) => {
      scenarioList.value = res.data.records
      paginationConfig.value.total = res.data.total
      paginationConfig.value.current_page = res.data.current
      paginationConfig.value.page_size = res.data.size
    })
}

function handleSizeChange() {
  paginationConfig.value.current_page = 1
  getList()
}

function loadOptions() {
  applicationApi.getAllApplication({ name: '' }).then((res) => {
    applicationOptions.value = res.data || []
  })
  knowledgeApi.getKnowledgeList({ name: '' }).then((res) => {
    knowledgeOptions.value = res.data || []
  })
}

function openCreate() {
  editingId.value = undefined
  form.value = defaultForm()
  resetRecommendationPolicy()
  drawerVisible.value = true
}

function openEdit(row: MarketingScenario) {
  editingId.value = row.id
  form.value = {
    name: row.name,
    target_audience: row.target_audience,
    objective: row.objective,
    channel: row.channel || 'ONLINE',
    status: row.status || 'DRAFT',
    application_id: row.application_id || null,
    knowledge_id: row.knowledge_id || null,
    config: row.config || {},
    description: row.description || '',
  }
  loadRecommendationPolicy(row.config?.recommendation_policy)
  drawerVisible.value = true
}

function defaultOffer(): MarketingRecommendationOffer {
  return {
    id: `offer-${Date.now()}-${Math.random().toString(16).slice(2)}`,
    name: '',
    benefit: '',
    plan_keywords: [],
    provinces: [],
    min_data_usage_gb: 0,
    min_call_usage_minutes: 0,
    priority: 100,
    exclusive_group: '',
    effective_start: '',
    effective_end: '',
    fee_note: '费用以当地实际可办理方案为准，办理前会确认月费变化。',
    contract_note: '办理前会确认优惠期限和合约期。',
  }
}

function resetRecommendationPolicy() {
  recommendationPolicy.value = { enabled: false, offers: [defaultOffer()] }
  offerPlanKeywords.value = ['']
  offerProvinces.value = ['']
  offerEffectiveRanges.value = [[]]
}

function loadRecommendationPolicy(policy: unknown) {
  const source = policy && typeof policy === 'object' ? policy as Partial<MarketingRecommendationPolicy> : {}
  const offers = Array.isArray(source.offers) && source.offers.length
    ? source.offers.map((offer) => ({ ...defaultOffer(), ...offer }))
    : [defaultOffer()]
  recommendationPolicy.value = { enabled: Boolean(source.enabled), offers }
  offerPlanKeywords.value = offers.map((offer) => (offer.plan_keywords || []).join(','))
  offerProvinces.value = offers.map((offer) => (offer.provinces || []).join(','))
  offerEffectiveRanges.value = offers.map((offer) => [offer.effective_start || '', offer.effective_end || ''].filter(Boolean))
}

function addOffer() {
  recommendationPolicy.value.offers.push(defaultOffer())
  offerPlanKeywords.value.push('')
  offerProvinces.value.push('')
  offerEffectiveRanges.value.push([])
}

function removeOffer(index: number) {
  if (recommendationPolicy.value.offers.length === 1) return
  recommendationPolicy.value.offers.splice(index, 1)
  offerPlanKeywords.value.splice(index, 1)
  offerProvinces.value.splice(index, 1)
  offerEffectiveRanges.value.splice(index, 1)
}

function splitKeywords(value: string) {
  return value.split(/[,，]/).map((item) => item.trim()).filter(Boolean)
}

function getRecommendationPolicyPayload(): MarketingRecommendationPolicy {
  return {
    enabled: recommendationPolicy.value.enabled,
    offers: recommendationPolicy.value.offers
      .filter((offer) => offer.name.trim())
      .map((offer, index) => ({
        ...offer,
        name: offer.name.trim(),
        benefit: offer.benefit.trim(),
        plan_keywords: splitKeywords(offerPlanKeywords.value[index] || ''),
        provinces: splitKeywords(offerProvinces.value[index] || ''),
        priority: offer.priority || 100,
        exclusive_group: offer.exclusive_group?.trim() || '',
        effective_start: offerEffectiveRanges.value[index]?.[0] || '',
        effective_end: offerEffectiveRanges.value[index]?.[1] || '',
      })),
  }
}

function getPolicySummary(row: MarketingScenario) {
  const policy = row.config?.recommendation_policy
  if (!policy?.enabled) return '未启用'
  const names = Array.isArray(policy.offers) ? policy.offers.map((offer: any) => offer.name).filter(Boolean) : []
  return names.join('、') || '已启用，未配置活动'
}

function openSimulation(row: MarketingScenario) {
  if (!row.id) return
  simulationScenarioId.value = row.id
  simulationForm.value = {
    current_plan: '',
    province: '',
    monthly_data_usage: '',
    monthly_call_usage: '',
  }
  simulationResult.value = undefined
  simulationVisible.value = true
}

function runSimulation() {
  if (!simulationScenarioId.value) return
  marketingScenarioApi
    .simulateRecommendation(simulationScenarioId.value, simulationForm.value, simulationLoading)
    .then((res) => {
      simulationResult.value = res.data.recommendation
    })
}

function submit() {
  formRef.value?.validate((valid) => {
    if (!valid) return
    form.value.config = {
      ...(form.value.config || {}),
      recommendation_policy: getRecommendationPolicyPayload(),
    }
    const request = editingId.value
      ? marketingScenarioApi.updateScenario(editingId.value, form.value, submitLoading)
      : marketingScenarioApi.createScenario(form.value, submitLoading)
    request.then(() => {
      ElMessage.success('保存成功')
      drawerVisible.value = false
      getList()
    })
  })
}

function remove(row: MarketingScenario) {
  if (!row.id) return
  ElMessageBox.confirm(`确认删除营销场景「${row.name}」吗？`, '删除确认', { type: 'warning' }).then(() => {
    marketingScenarioApi.deleteScenario(row.id as string, loading).then(() => {
      ElMessage.success('删除成功')
      getList()
    })
  })
}

onMounted(() => {
  getList()
  loadOptions()
})
</script>
