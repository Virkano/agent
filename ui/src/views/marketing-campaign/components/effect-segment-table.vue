<template>
  <el-table :data="data" border empty-text="暂无命中客户数据">
    <el-table-column prop="name" label="分组" min-width="130" />
    <el-table-column prop="customer_count" label="客户" width="70" />
    <el-table-column prop="intent_count" label="意向" width="70" />
    <el-table-column prop="converted_count" label="办理" width="70" />
    <el-table-column prop="manual_count" label="转人工" width="80" />
    <el-table-column prop="no_intent_count" label="无意向" width="80" />
    <el-table-column label="意向率" width="80">
      <template #default="{ row }">{{ row.intent_rate }}%</template>
    </el-table-column>
    <el-table-column label="办理率" width="80">
      <template #default="{ row }">{{ row.conversion_rate }}%</template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import type { MarketingCampaignEffectSegment } from '@/api/marketing/campaign'

defineProps<{
  data: MarketingCampaignEffectSegment[]
}>()
</script>
