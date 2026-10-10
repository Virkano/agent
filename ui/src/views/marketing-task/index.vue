<template>
  <div class="marketing-task p-16-24">
    <h2 class="ml-24 mb-16">营销任务</h2>
    <el-card style="--el-card-padding: 0">
      <div class="p-24">
        <div class="flex-between mb-16">
          <div>
            <el-button type="primary" @click="openCreate">创建任务</el-button>
            <el-button class="ml-8" @click="openApprovalQueue">审批待办</el-button>
          </div>
          <div class="flex align-center">
            <el-select
              v-model="searchForm.scenario_id"
              class="mr-8"
              clearable
              filterable
              placeholder="营销场景"
              style="width: 220px"
              @change="getList"
            >
              <el-option
                v-for="item in scenarioOptions"
                :key="item.id"
                :label="item.name"
                :value="item.id"
              />
            </el-select>
            <el-select
              v-model="searchForm.status"
              class="mr-8"
              clearable
              placeholder="任务状态"
              style="width: 130px"
              @change="getList"
            >
              <el-option label="草稿" value="DRAFT" />
              <el-option label="进行中" value="RUNNING" />
              <el-option label="暂停" value="PAUSED" />
              <el-option label="已完成" value="FINISHED" />
            </el-select>
            <el-input
              v-model="searchForm.name"
              clearable
              placeholder="搜索任务/客群/目标"
              style="width: 240px"
              @change="getList"
            />
          </div>
        </div>

        <app-table
          :data="taskList"
          :pagination-config="paginationConfig"
          :maxTableHeight="300"
          v-loading="loading"
          @sizeChange="handleSizeChange"
          @changePage="getList"
        >
          <el-table-column prop="name" label="任务名称" min-width="200" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100">
            <template #default="{ row }">
              <el-tag :type="statusMap[row.status]?.type">
                {{ statusMap[row.status]?.label || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="scenario_name"
            label="营销场景"
            min-width="180"
            show-overflow-tooltip
          />
          <el-table-column
            prop="target_audience"
            label="目标客群"
            min-width="180"
            show-overflow-tooltip
          />
          <el-table-column
            prop="objective"
            label="任务目标"
            min-width="180"
            show-overflow-tooltip
          />
          <el-table-column prop="channel" label="渠道" width="100" />
          <el-table-column prop="target_count" label="目标数" width="90" />
          <el-table-column prop="chat_count" label="会话数" width="90" />
          <el-table-column
            prop="application_name"
            label="智能体"
            min-width="170"
            show-overflow-tooltip
          />
          <el-table-column
            prop="knowledge_name"
            label="知识库"
            min-width="170"
            show-overflow-tooltip
          />
          <el-table-column prop="update_time" label="更新时间" width="170">
            <template #default="{ row }">{{ datetimeFormat(row.update_time) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="320" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" :disabled="!row.chat_url" @click="openChat(row)"
                >测试</el-button
              >
              <el-button link type="primary" :disabled="!row.chat_url" @click="copyChatUrl(row)"
                >复制链接</el-button
              >
              <el-button link type="primary" @click="openCustomers(row)">客户</el-button>
              <el-button link type="primary" @click="openDashboard(row)">看板</el-button>
              <el-button link type="primary" @click="openEffect(row)">复盘</el-button>
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="remove(row)">删除</el-button>
            </template>
          </el-table-column>
        </app-table>
      </div>
    </el-card>

    <el-drawer v-model="approvalQueueVisible" title="审批待办与超时预警" size="900px">
      <div v-loading="approvalQueueLoading">
        <el-alert
          class="mb-16"
          type="info"
          :closable="false"
          title="待办按审批截止时间排序；仅工作空间管理员且非创建人可直接审批。"
        />
        <el-descriptions :column="2" border class="mb-16">
          <el-descriptions-item label="待审批批次">{{
            approvalQueueData?.summary.pending_count || 0
          }}</el-descriptions-item>
          <el-descriptions-item label="已超时">
            <el-tag :type="approvalQueueData?.summary.overdue_count ? 'danger' : 'success'">
              {{ approvalQueueData?.summary.overdue_count || 0 }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
        <el-table :data="approvalQueueData?.records || []" border max-height="620">
          <el-table-column
            prop="task_name"
            label="营销任务"
            min-width="190"
            show-overflow-tooltip
          />
          <el-table-column prop="name" label="批次" min-width="190" show-overflow-tooltip />
          <el-table-column prop="creator_name" label="创建人" width="120" />
          <el-table-column prop="owner_name" label="负责人" width="120">
            <template #default="{ row }">{{ row.owner_name || '-' }}</template>
          </el-table-column>
          <el-table-column label="审批截止" width="180">
            <template #default="{ row }">
              <el-tag v-if="row.is_approval_overdue" type="danger">已超时</el-tag>
              <span v-else>{{
                row.approval_due_at ? datetimeFormat(row.approval_due_at) : '-'
              }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="approval_sla_hours" label="SLA" width="90">
            <template #default="{ row }">{{ row.approval_sla_hours }} 小时</template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button
                v-if="row.can_approve"
                link
                type="primary"
                @click="openTouchBatchApproval(row, row.task_id)"
                >审批</el-button
              >
              <span v-else class="text-secondary">待其他主管</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <el-drawer
      v-model="drawerVisible"
      :title="editingId ? '编辑营销任务' : '创建营销任务'"
      size="560px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
        <el-form-item label="任务名称" prop="name">
          <el-input v-model="form.name" maxlength="128" show-word-limit />
        </el-form-item>
        <el-form-item label="营销场景" prop="scenario_id">
          <el-select
            v-model="form.scenario_id"
            filterable
            style="width: 100%"
            @change="syncScenarioDefaults"
          >
            <el-option
              v-for="item in scenarioOptions"
              :key="item.id"
              :label="item.name"
              :value="item.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-radio-group v-model="form.status">
            <el-radio-button label="DRAFT">草稿</el-radio-button>
            <el-radio-button label="RUNNING">进行中</el-radio-button>
            <el-radio-button label="PAUSED">暂停</el-radio-button>
            <el-radio-button label="FINISHED">已完成</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="目标客群">
          <el-input v-model="form.target_audience" placeholder="例如：199 套餐高价值存量客户" />
        </el-form-item>
        <el-form-item label="任务目标">
          <el-input v-model="form.objective" placeholder="例如：引导咨询套餐升级并收集异议点" />
        </el-form-item>
        <el-form-item label="触达渠道">
          <el-select v-model="form.channel" style="width: 100%">
            <el-option label="在线客服" value="ONLINE" />
            <el-option label="短信" value="SMS" />
            <el-option label="外呼" value="CALL" />
            <el-option label="企业微信" value="WE_COM" />
          </el-select>
        </el-form-item>
        <el-form-item label="目标触达数">
          <el-input-number v-model="form.target_count" :min="0" style="width: 100%" />
        </el-form-item>
        <el-form-item label="首批灰度人数">
          <el-input-number
            v-model="form.config.pilot_size"
            :min="0"
            :max="10000"
            style="width: 100%"
          />
          <div class="mt-8">填写大于 0 的人数后，首个触达批次将最多入选该人数；0 表示不限制。</div>
        </el-form-item>
        <el-form-item label="审批 SLA（小时）">
          <el-input-number
            v-model="form.config.approval_sla_hours"
            :min="1"
            :max="168"
            style="width: 100%"
          />
          <div class="mt-8">新建或修改后重提的批次将在此时限内完成审批，默认 24 小时。</div>
        </el-form-item>
        <el-form-item label="营销活动库">
          <el-select
            v-model="form.campaign_ids"
            multiple
            clearable
            filterable
            placeholder="不选择则沿用营销场景的历史策略"
            style="width: 100%"
          >
            <el-option
              v-for="item in campaignOptions"
              :key="item.id"
              :label="`${item.name}（v${item.version}）`"
              :value="item.id"
            />
          </el-select>
          <div class="mt-8">
            保存任务时会固化活动版本；后续活动改版、暂停或归档不会影响已有任务和会话。
          </div>
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
        <el-form-item label="任务说明">
          <el-input
            v-model="form.description"
            type="textarea"
            :rows="4"
            placeholder="记录触达批次、权益边界、转人工规则、后续复盘口径"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitLoading" @click="submit">保存</el-button>
      </template>
    </el-drawer>

    <el-drawer v-model="customerVisible" title="营销客户名单" size="900px">
      <div class="flex-between mb-16">
        <div>
          <el-button type="primary" @click="openCustomerCreate">新增客户</el-button>
          <el-button @click="openCustomerImport">导入名单</el-button>
          <el-button @click="openTouchBatch">触达批次</el-button>
          <el-button @click="openFollowUpQueue">待办队列</el-button>
        </div>
        <div class="flex align-center">
          <el-select
            v-model="customerSearch.status"
            class="mr-8"
            clearable
            placeholder="客户状态"
            style="width: 130px"
            @change="getCustomers"
          >
            <el-option label="待触达" value="PENDING" />
            <el-option label="已触达" value="TOUCHED" />
            <el-option label="已咨询" value="CONSULTED" />
            <el-option label="有意向" value="INTENT" />
            <el-option label="无意向" value="NO_INTENT" />
            <el-option label="转人工" value="MANUAL" />
          </el-select>
          <el-input
            v-model="customerSearch.name"
            clearable
            placeholder="搜索客户/手机号/套餐"
            style="width: 220px"
            @change="getCustomers"
          />
        </div>
      </div>
      <app-table
        :data="customerList"
        :pagination-config="customerPagination"
        :maxTableHeight="430"
        v-loading="customerLoading"
        @sizeChange="handleCustomerSizeChange"
        @changePage="getCustomers"
      >
        <el-table-column prop="name" label="客户" min-width="120" show-overflow-tooltip />
        <el-table-column
          prop="phone_masked"
          label="手机号/标识"
          width="130"
          show-overflow-tooltip
        />
        <el-table-column prop="province" label="省份" width="90" />
        <el-table-column
          prop="current_plan"
          label="当前套餐"
          min-width="130"
          show-overflow-tooltip
        />
        <el-table-column prop="monthly_data_usage" label="近月流量" width="110" />
        <el-table-column prop="monthly_call_usage" label="近月通话" width="110" />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="customerStatusMap[row.status]?.type">
              {{ customerStatusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="意向/异议" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            {{ getCustomerInsightSummary(row) }}
          </template>
        </el-table-column>
        <el-table-column label="转化结果" min-width="150" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag
              v-if="row.latest_conversion"
              :type="conversionOutcomeMap[row.latest_conversion.outcome]?.type"
            >
              {{
                conversionOutcomeMap[row.latest_conversion.outcome]?.label ||
                row.latest_conversion.outcome
              }}
            </el-tag>
            <span v-else>-</span>
            <span v-if="row.latest_conversion?.product_name" class="ml-8">{{
              row.latest_conversion.product_name
            }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="chat_count" label="会话数" width="90" />
        <el-table-column label="操作" width="315" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :disabled="!row.chat_url" @click="openCustomerChat(row)"
              >测试</el-button
            >
            <el-button
              link
              type="primary"
              :disabled="!row.chat_url"
              @click="copyCustomerChatUrl(row)"
              >复制链接</el-button
            >
            <el-button link type="primary" @click="openCustomerFollowUp(row)">跟进</el-button>
            <el-button link type="success" @click="openCustomerConversion(row)">转化</el-button>
            <el-button link type="primary" @click="openCustomerEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="removeCustomer(row)">删除</el-button>
          </template>
        </el-table-column>
      </app-table>
    </el-drawer>

    <el-dialog v-model="customerImportVisible" title="导入客户名单" width="920px" destroy-on-close>
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        title="支持 CSV、XLSX，单次最多 1000 行、5MB。客户标识（手机号或客户 ID）为必填字段；校验通过后才会新增客户，已有标识和文件内重复行会跳过。"
      />
      <div class="flex-between mb-16">
        <el-upload
          :auto-upload="false"
          :file-list="customerImportFileList"
          :limit="1"
          accept=".csv,.xlsx"
          :on-change="handleCustomerImportFile"
          :on-remove="clearCustomerImportFile"
        >
          <el-button type="primary" plain>选择名单文件</el-button>
        </el-upload>
        <el-button link type="primary" @click="downloadCustomerImportTemplate"
          >下载 CSV 模板</el-button
        >
      </div>
      <template v-if="customerImportFile">
        <el-form label-position="top" class="mb-16">
          <el-form-item label="字段映射">
            <el-row :gutter="12" class="w-full">
              <el-col
                v-for="field in customerImportFields"
                :key="field.key"
                :span="12"
                class="mb-8"
              >
                <div class="flex align-center">
                  <span style="width: 110px"
                    >{{ field.label
                    }}<span v-if="field.required" class="color-danger"> *</span></span
                  >
                  <el-select
                    v-model="customerImportMapping[field.key]"
                    clearable
                    placeholder="不导入"
                    style="flex: 1"
                  >
                    <el-option
                      v-for="header in customerImportHeaders"
                      :key="header"
                      :label="header"
                      :value="header"
                    />
                  </el-select>
                </div>
              </el-col>
            </el-row>
          </el-form-item>
          <el-button
            type="primary"
            :loading="customerImportPreviewLoading"
            @click="previewCustomerImport"
            >校验并预览</el-button
          >
        </el-form>
      </template>
      <template v-if="customerImportPreviewData">
        <el-descriptions :column="4" border class="mb-16">
          <el-descriptions-item label="源数据">{{
            customerImportPreviewData.summary.total_count
          }}</el-descriptions-item>
          <el-descriptions-item label="可导入"
            ><el-tag type="success">{{
              customerImportPreviewData.summary.ready_count
            }}</el-tag></el-descriptions-item
          >
          <el-descriptions-item label="重复跳过"
            ><el-tag type="warning">{{
              customerImportPreviewData.summary.skipped_count
            }}</el-tag></el-descriptions-item
          >
          <el-descriptions-item label="格式错误"
            ><el-tag type="danger">{{
              customerImportPreviewData.summary.error_count
            }}</el-tag></el-descriptions-item
          >
        </el-descriptions>
        <el-table
          :data="customerImportPreviewData.rows"
          border
          max-height="300"
          size="small"
          class="mb-16"
        >
          <el-table-column prop="row_number" label="行号" width="70" />
          <el-table-column label="客户" min-width="120" show-overflow-tooltip
            ><template #default="{ row }">{{ row.data.name || '-' }}</template></el-table-column
          >
          <el-table-column prop="phone_masked" label="客户标识" min-width="130" />
          <el-table-column label="套餐" min-width="150" show-overflow-tooltip
            ><template #default="{ row }">{{
              row.data.current_plan || '-'
            }}</template></el-table-column
          >
          <el-table-column label="校验结果" min-width="200" show-overflow-tooltip>
            <template #default="{ row }"
              ><el-tag :type="customerImportStatusMap[row.status].type">{{
                customerImportStatusMap[row.status].label
              }}</el-tag
              ><span v-if="row.reason" class="ml-8">{{ row.reason }}</span></template
            >
          </el-table-column>
        </el-table>
      </template>
      <h4 class="mb-8">最近导入记录</h4>
      <el-table
        :data="customerImportHistory"
        v-loading="customerImportHistoryLoading"
        border
        max-height="180"
        size="small"
      >
        <el-table-column prop="file_name" label="文件" min-width="180" show-overflow-tooltip />
        <el-table-column prop="imported_count" label="已导入" width="80" />
        <el-table-column prop="skipped_count" label="跳过" width="80" />
        <el-table-column prop="error_count" label="错误" width="80" />
        <el-table-column prop="operator_name" label="操作人" width="110" />
        <el-table-column label="时间" width="170"
          ><template #default="{ row }">{{
            datetimeFormat(row.create_time)
          }}</template></el-table-column
        >
      </el-table>
      <template #footer>
        <el-button @click="customerImportVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="!customerImportPreviewData?.summary.ready_count"
          :loading="customerImportSubmitLoading"
          @click="submitCustomerImport"
          >确认导入 {{ customerImportPreviewData?.summary.ready_count || 0 }} 条</el-button
        >
      </template>
    </el-dialog>

    <el-drawer v-model="touchBatchVisible" title="触达批次" size="760px">
      <div class="flex-between mb-16">
        <span>批次生成后会固化入选和排除快照，不会影响客户原始名单。</span>
        <el-button type="primary" @click="openTouchBatchCreate">生成批次</el-button>
      </div>
      <el-table :data="touchBatchList" v-loading="touchBatchLoading" border max-height="560">
        <el-table-column prop="name" label="批次名称" min-width="220" show-overflow-tooltip />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="touchBatchStatusMap[row.status]?.type">
              {{ touchBatchStatusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="approval_status" label="审批" width="100">
          <template #default="{ row }">
            <el-tag :type="touchBatchApprovalMap[row.approval_status || 'PENDING']?.type">
              {{ touchBatchApprovalMap[row.approval_status || 'PENDING']?.label || '-' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="审批截止" width="170">
          <template #default="{ row }">
            <el-tag v-if="row.is_approval_overdue" type="danger">已超时</el-tag>
            <span v-else>{{
              row.approval_due_at ? datetimeFormat(row.approval_due_at) : '-'
            }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="selected_count" label="入选" width="90" />
        <el-table-column prop="excluded_count" label="排除" width="90" />
        <el-table-column prop="owner_name" label="负责人" width="100" show-overflow-tooltip />
        <el-table-column prop="deadline" label="截止时间" width="170">
          <template #default="{ row }">{{
            row.deadline ? datetimeFormat(row.deadline) : '-'
          }}</template>
        </el-table-column>
        <el-table-column label="筛选条件" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ getTouchBatchFilterSummary(row) }}</template>
        </el-table-column>
        <el-table-column prop="create_time" label="生成时间" width="170">
          <template #default="{ row }">{{ datetimeFormat(row.create_time) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.can_approve"
              link
              type="primary"
              @click="openTouchBatchApproval(row)"
            >
              审批
            </el-button>
            <el-button
              v-else-if="row.can_resubmit"
              link
              type="primary"
              @click="openTouchBatchResubmit(row)"
              >修改重提</el-button
            >
            <span v-else-if="row.approval_status === 'PENDING'" class="text-secondary"
              >待主管审批</span
            >
            <el-button
              link
              type="primary"
              :disabled="row.approval_status !== 'APPROVED'"
              @click="openTouchExecution(row)"
            >
              执行
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-drawer v-model="touchExecutionVisible" title="批次执行与复盘" size="980px">
      <template v-if="touchBatchDetail">
        <div class="flex-between mb-16">
          <div>
            <h3 class="m-0">{{ touchBatchDetail.batch.name }}</h3>
            <div class="mt-8">仅可记录该批次入选快照中的客户；关闭批次后不可再新增结果。</div>
          </div>
          <el-tag :type="touchBatchStatusMap[touchBatchDetail.batch.status]?.type">
            {{
              touchBatchStatusMap[touchBatchDetail.batch.status]?.label ||
              touchBatchDetail.batch.status
            }}
          </el-tag>
        </div>
        <el-alert
          v-if="touchBatchDetail.batch.approval_status !== 'APPROVED'"
          class="mb-16"
          type="warning"
          :closable="false"
          title="当前批次尚未审批通过，不能开始执行或记录触达结果。"
        />
        <el-form label-position="top" class="mb-16">
          <el-row :gutter="16">
            <el-col :span="6">
              <el-form-item label="负责人">
                <el-input
                  v-model="touchBatchScheduleForm.owner_name"
                  maxlength="64"
                  placeholder="填写坐席或小组名称"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="7">
              <el-form-item label="截止时间">
                <el-date-picker
                  v-model="touchBatchScheduleForm.deadline"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm:ss"
                  clearable
                  placeholder="选择截止时间"
                  style="width: 100%"
                />
              </el-form-item>
            </el-col>
            <el-col :span="5">
              <el-form-item label="批次状态">
                <el-select v-model="touchBatchScheduleForm.status" style="width: 100%">
                  <el-option label="待执行" value="READY" />
                  <el-option
                    label="执行中（需审批通过）"
                    value="RUNNING"
                    :disabled="touchBatchDetail.batch.approval_status !== 'APPROVED'"
                  />
                  <el-option label="已关闭" value="CLOSED" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label=" ">
                <el-button
                  type="primary"
                  :loading="touchBatchScheduleLoading"
                  style="width: 100%; margin-top: 22px"
                  @click="saveTouchBatchSchedule"
                >
                  保存安排
                </el-button>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>

        <el-descriptions :column="4" border class="mb-16">
          <el-descriptions-item label="审批状态">
            <el-tag
              :type="
                touchBatchApprovalMap[touchBatchDetail.batch.approval_status || 'PENDING']?.type
              "
            >
              {{
                touchBatchApprovalMap[touchBatchDetail.batch.approval_status || 'PENDING']?.label ||
                '-'
              }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="创建人">{{
            touchBatchDetail.batch.creator_name || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="审批人">{{
            touchBatchDetail.batch.approver_name || '-'
          }}</el-descriptions-item>
          <el-descriptions-item label="审批时间">
            {{
              touchBatchDetail.batch.approved_at
                ? datetimeFormat(touchBatchDetail.batch.approved_at)
                : '-'
            }}
          </el-descriptions-item>
          <el-descriptions-item label="入选">{{
            touchBatchDetail.metrics.selected_count
          }}</el-descriptions-item>
          <el-descriptions-item label="已记录">{{
            touchBatchDetail.metrics.executed_count
          }}</el-descriptions-item>
          <el-descriptions-item label="待执行">{{
            touchBatchDetail.metrics.waiting_count
          }}</el-descriptions-item>
          <el-descriptions-item label="有意向 / 转人工">
            {{ touchBatchDetail.metrics.intent_count }} /
            {{ touchBatchDetail.metrics.manual_count }}
          </el-descriptions-item>
          <el-descriptions-item label="已联系">{{
            touchBatchDetail.metrics.contacted_count
          }}</el-descriptions-item>
          <el-descriptions-item label="未接通">{{
            touchBatchDetail.metrics.no_answer_count
          }}</el-descriptions-item>
          <el-descriptions-item label="明确拒绝">{{
            touchBatchDetail.metrics.rejected_count
          }}</el-descriptions-item>
          <el-descriptions-item label="确认办理 / 流失">
            {{ touchBatchDetail.metrics.converted_count }} /
            {{ touchBatchDetail.metrics.lost_count }}
          </el-descriptions-item>
          <el-descriptions-item label="转化率"
            >{{ touchBatchDetail.metrics.conversion_rate }}%</el-descriptions-item
          >
        </el-descriptions>

        <el-table :data="touchBatchDetail.batch.customer_snapshot || []" border max-height="420">
          <el-table-column prop="name" label="客户" min-width="120" />
          <el-table-column prop="phone_masked" label="手机号/标识" width="130" />
          <el-table-column prop="current_plan" label="套餐" min-width="130" show-overflow-tooltip />
          <el-table-column label="最近结果" min-width="150" show-overflow-tooltip>
            <template #default="{ row }">{{ getLatestExecutionSummary(row.customer_id) }}</template>
          </el-table-column>
          <el-table-column label="操作" width="170" fixed="right">
            <template #default="{ row }">
              <el-button
                link
                type="primary"
                :disabled="
                  touchBatchDetail.batch.status === 'CLOSED' ||
                  touchBatchDetail.batch.approval_status !== 'APPROVED'
                "
                @click="openExecutionRecord(row)"
              >
                记录结果
              </el-button>
              <el-button link type="success" @click="openBatchCustomerConversion(row)"
                >确认转化</el-button
              >
            </template>
          </el-table-column>
        </el-table>

        <h3 class="mt-24 mb-12">转化归因记录</h3>
        <el-table :data="touchBatchDetail.conversions || []" border max-height="220">
          <el-table-column prop="customer_name" label="客户" width="120" />
          <el-table-column prop="outcome" label="结果" width="110">
            <template #default="{ row }">
              <el-tag :type="conversionOutcomeMap[row.outcome]?.type">
                {{ conversionOutcomeMap[row.outcome]?.label || row.outcome }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column
            prop="product_name"
            label="办理套餐/产品"
            min-width="150"
            show-overflow-tooltip
          />
          <el-table-column prop="note" label="说明" min-width="220" show-overflow-tooltip />
          <el-table-column prop="operator_name" label="登记人" width="110" />
          <el-table-column prop="create_time" label="时间" width="170">
            <template #default="{ row }">{{ datetimeFormat(row.create_time) }}</template>
          </el-table-column>
        </el-table>

        <h3 class="mt-24 mb-12">审批留痕</h3>
        <el-table :data="touchBatchDetail.approval_records || []" border max-height="220">
          <el-table-column prop="action" label="动作" width="120">
            <template #default="{ row }">{{
              touchBatchApprovalActionMap[row.action] || row.action
            }}</template>
          </el-table-column>
          <el-table-column
            prop="note"
            label="意见 / 修改说明"
            min-width="300"
            show-overflow-tooltip
          />
          <el-table-column prop="operator_name" label="操作人" width="130" />
          <el-table-column prop="create_time" label="时间" width="170">
            <template #default="{ row }">{{ datetimeFormat(row.create_time) }}</template>
          </el-table-column>
        </el-table>

        <h3 class="mt-24 mb-12">执行记录</h3>
        <el-table :data="touchBatchDetail.executions" border max-height="280">
          <el-table-column prop="customer_name" label="客户" width="110" />
          <el-table-column prop="result" label="结果" width="110">
            <template #default="{ row }">{{
              touchExecutionResultMap[row.result] || row.result
            }}</template>
          </el-table-column>
          <el-table-column prop="note" label="记录" min-width="260" show-overflow-tooltip />
          <el-table-column prop="next_follow_up_at" label="下次跟进" width="170">
            <template #default="{ row }">{{
              row.next_follow_up_at ? datetimeFormat(row.next_follow_up_at) : '-'
            }}</template>
          </el-table-column>
          <el-table-column prop="operator_name" label="操作人" width="110" />
          <el-table-column prop="create_time" label="时间" width="170">
            <template #default="{ row }">{{ datetimeFormat(row.create_time) }}</template>
          </el-table-column>
        </el-table>
      </template>
    </el-drawer>

    <el-dialog
      v-model="touchExecutionFormVisible"
      title="记录触达结果"
      width="520px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="客户">
          <el-input
            :model-value="executionCustomer?.name || executionCustomer?.phone_masked || ''"
            disabled
          />
        </el-form-item>
        <el-form-item label="触达结果" required>
          <el-select v-model="touchExecutionForm.result" style="width: 100%">
            <el-option label="已联系" value="CONTACTED" />
            <el-option label="未接通" value="NO_ANSWER" />
            <el-option label="明确拒绝" value="REJECTED" />
            <el-option label="有办理意向" value="INTENT" />
            <el-option label="转人工处理" value="MANUAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="执行记录" required>
          <el-input
            v-model="touchExecutionForm.note"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="下次跟进时间">
          <el-date-picker
            v-model="touchExecutionForm.next_follow_up_at"
            type="datetime"
            value-format="YYYY-MM-DDTHH:mm:ss"
            clearable
            style="width: 100%"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="touchExecutionFormVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="touchExecutionSubmitLoading"
          @click="submitTouchExecution"
          >保存结果</el-button
        >
      </template>
    </el-dialog>

    <el-dialog
      v-model="touchBatchApprovalVisible"
      title="审批触达批次"
      width="520px"
      destroy-on-close
    >
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        title="仅工作空间管理员可审批；批次创建人不能审批自己创建的批次。"
      />
      <el-form label-position="top">
        <el-form-item label="批次名称">
          <el-input :model-value="approvingTouchBatch?.name || ''" disabled />
        </el-form-item>
        <el-form-item label="审批结论" required>
          <el-radio-group v-model="touchBatchApprovalForm.approval_status">
            <el-radio value="APPROVED">通过</el-radio>
            <el-radio value="REJECTED">驳回</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="审批意见">
          <el-input
            v-model="touchBatchApprovalForm.approval_note"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            placeholder="例如：客群范围、筛选条件及话术已核验。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="touchBatchApprovalVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="touchBatchApprovalLoading"
          @click="submitTouchBatchApproval"
          >确认审批</el-button
        >
      </template>
    </el-dialog>

    <el-dialog
      v-model="touchBatchCreateVisible"
      :title="resubmittingTouchBatch ? '修改并重新提交触达批次' : '生成触达批次'"
      width="560px"
      destroy-on-close
    >
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        :title="
          resubmittingTouchBatch
            ? '修改筛选条件后将重新生成快照，并再次进入待审批。'
            : '只生成筛选快照和待办依据，不会自动给客户发送消息。'
        "
      />
      <el-form label-position="top">
        <el-form-item label="批次名称" required>
          <el-input
            v-model="touchBatchForm.name"
            maxlength="128"
            placeholder="例如：广东199套餐流量关怀-第一批"
          />
        </el-form-item>
        <el-form-item label="客户状态">
          <el-select v-model="touchBatchForm.statuses" multiple style="width: 100%">
            <el-option label="待触达" value="PENDING" />
            <el-option label="已触达" value="TOUCHED" />
            <el-option label="已咨询" value="CONSULTED" />
            <el-option label="有意向" value="INTENT" />
            <el-option label="转人工" value="MANUAL" />
          </el-select>
        </el-form-item>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="套餐关键词">
              <el-input v-model="touchBatchForm.plan_keyword" placeholder="例如：199" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="省份">
              <el-input v-model="touchBatchForm.province" placeholder="例如：广东" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="12">
          <el-col :span="12">
            <el-form-item label="最低流量（GB）">
              <el-input-number
                v-model="touchBatchForm.min_data_usage_gb"
                :min="0"
                :precision="0"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="最低通话（分钟）">
              <el-input-number
                v-model="touchBatchForm.min_call_usage_minutes"
                :min="0"
                :precision="0"
                style="width: 100%"
              />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="冷却期（天）">
          <el-input-number
            v-model="touchBatchForm.cooldown_days"
            :min="0"
            :max="365"
            style="width: 100%"
          />
          <div class="mt-8">冷却期内已入选过批次的客户会自动排除；设为 0 表示不限制。</div>
        </el-form-item>
        <el-form-item v-if="resubmittingTouchBatch" label="修改说明" required>
          <el-input
            v-model="touchBatchResubmitNote"
            type="textarea"
            :rows="3"
            maxlength="2000"
            show-word-limit
            placeholder="说明针对驳回意见做了哪些修改"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="touchBatchCreateVisible = false">取消</el-button>
        <el-button type="primary" :loading="touchBatchSubmitLoading" @click="submitTouchBatch">
          {{ resubmittingTouchBatch ? '重新提交' : '生成' }}
        </el-button>
      </template>
    </el-dialog>

    <el-drawer v-model="followUpQueueVisible" title="待跟进队列" size="760px">
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        title="队列按“转人工 → 有意向 → 已咨询 → 待触达 → 已触达”排序；无意向客户默认不进入队列。"
      />
      <el-table :data="followUpQueue" v-loading="followUpQueueLoading" border max-height="600">
        <el-table-column prop="name" label="客户" min-width="120" show-overflow-tooltip />
        <el-table-column prop="phone_masked" label="手机号/标识" width="130" />
        <el-table-column
          prop="current_plan"
          label="当前套餐"
          min-width="130"
          show-overflow-tooltip
        />
        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="customerStatusMap[row.status]?.type">
              {{ customerStatusMap[row.status]?.label || row.status }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="intent" label="意向" min-width="130" show-overflow-tooltip />
        <el-table-column
          prop="queue_reason"
          label="进入原因"
          min-width="180"
          show-overflow-tooltip
        />
        <el-table-column label="最近批次" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">{{ row.latest_batch?.name || '-' }}</template>
        </el-table-column>
      </el-table>
    </el-drawer>

    <el-dialog
      v-model="customerFollowUpVisible"
      title="记录人工跟进"
      width="480px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="客户">
          <el-input
            :model-value="followUpCustomer?.name || followUpCustomer?.phone_masked || ''"
            disabled
          />
        </el-form-item>
        <el-form-item label="跟进结果">
          <el-select v-model="customerFollowUpForm.status" style="width: 100%">
            <el-option label="已咨询，待继续跟进" value="CONSULTED" />
            <el-option label="明确有意向" value="INTENT" />
            <el-option label="暂时无意向" value="NO_INTENT" />
            <el-option label="需要人工处理" value="MANUAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="意向标签">
          <el-input
            v-model="customerFollowUpForm.intent"
            maxlength="64"
            placeholder="例如：费用敏感，待回访"
          />
        </el-form-item>
        <el-form-item label="跟进记录" required>
          <el-input
            v-model="customerFollowUpForm.note"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            placeholder="记录已确认的信息、约定的下一步和处理人"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customerFollowUpVisible = false">取消</el-button>
        <el-button type="primary" :loading="customerFollowUpLoading" @click="submitCustomerFollowUp"
          >保存跟进</el-button
        >
      </template>
    </el-dialog>

    <el-dialog
      v-model="customerConversionVisible"
      title="确认转化结果"
      width="520px"
      destroy-on-close
    >
      <el-alert
        class="mb-16"
        type="info"
        :closable="false"
        title="确认办理或确认流失会保留历史记录，并更新客户状态；如未选择批次，系统自动归因到该客户最近一次触达批次。"
      />
      <el-form label-position="top">
        <el-form-item label="客户">
          <el-input
            :model-value="conversionCustomer?.name || conversionCustomer?.phone_masked || ''"
            disabled
          />
        </el-form-item>
        <el-form-item label="结果" required>
          <el-radio-group v-model="conversionForm.outcome">
            <el-radio value="CONVERTED">确认办理</el-radio>
            <el-radio value="LOST">确认流失</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item v-if="conversionForm.outcome === 'CONVERTED'" label="办理套餐/产品" required>
          <el-input
            v-model="conversionForm.product_name"
            maxlength="128"
            placeholder="例如：199 元套餐升档"
          />
        </el-form-item>
        <el-form-item label="归因批次">
          <el-select
            v-model="conversionForm.batch_id"
            clearable
            placeholder="自动识别最近触达批次"
            style="width: 100%"
          >
            <el-option
              v-for="batch in touchBatchList"
              :key="batch.id"
              :label="batch.name"
              :value="batch.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="结果说明" required>
          <el-input
            v-model="conversionForm.note"
            type="textarea"
            :rows="4"
            maxlength="2000"
            show-word-limit
            placeholder="记录办理确认、流失原因或后续凭据。"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customerConversionVisible = false">取消</el-button>
        <el-button
          type="primary"
          :loading="customerConversionLoading"
          @click="submitCustomerConversion"
          >确认登记</el-button
        >
      </template>
    </el-dialog>

    <el-drawer
      v-model="customerFormVisible"
      :title="editingCustomerId ? '编辑客户' : '新增客户'"
      size="480px"
    >
      <el-form ref="customerFormRef" :model="customerForm" label-position="top">
        <el-form-item label="客户名称">
          <el-input v-model="customerForm.name" maxlength="128" />
        </el-form-item>
        <el-form-item label="手机号/客户标识">
          <el-input v-model="customerForm.phone" maxlength="64" />
        </el-form-item>
        <el-form-item label="省份">
          <el-input v-model="customerForm.province" maxlength="64" />
        </el-form-item>
        <el-form-item label="当前套餐">
          <el-input
            v-model="customerForm.current_plan"
            placeholder="例如：199元套餐"
            maxlength="128"
          />
        </el-form-item>
        <el-form-item label="近月流量">
          <el-input
            v-model="customerForm.monthly_data_usage"
            placeholder="例如：80GB"
            maxlength="64"
          />
        </el-form-item>
        <el-form-item label="近月通话">
          <el-input
            v-model="customerForm.monthly_call_usage"
            placeholder="例如：300分钟"
            maxlength="64"
          />
        </el-form-item>
        <el-form-item label="客户状态">
          <el-select v-model="customerForm.status" style="width: 100%">
            <el-option label="待触达" value="PENDING" />
            <el-option label="已触达" value="TOUCHED" />
            <el-option label="已咨询" value="CONSULTED" />
            <el-option label="有意向" value="INTENT" />
            <el-option label="无意向" value="NO_INTENT" />
            <el-option label="转人工" value="MANUAL" />
          </el-select>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="customerForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="customerFormVisible = false">取消</el-button>
        <el-button type="primary" :loading="customerSubmitLoading" @click="submitCustomer"
          >保存</el-button
        >
      </template>
    </el-drawer>

    <el-drawer v-model="dashboardVisible" title="任务经营看板" size="900px">
      <div v-loading="dashboardLoading">
        <template v-if="dashboardData">
          <el-descriptions :column="4" border class="mb-16">
            <el-descriptions-item label="客户总数">{{
              dashboardData.funnel.customer_count || 0
            }}</el-descriptions-item>
            <el-descriptions-item label="已触达">{{
              dashboardData.funnel.touched_count || 0
            }}</el-descriptions-item>
            <el-descriptions-item label="有意向">{{
              dashboardData.funnel.intent_count || 0
            }}</el-descriptions-item>
            <el-descriptions-item label="转人工">{{
              dashboardData.funnel.manual_count || 0
            }}</el-descriptions-item>
            <el-descriptions-item label="确认办理 / 流失">
              {{ dashboardData.funnel.converted_count || 0 }} /
              {{ dashboardData.funnel.lost_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="转化率"
              >{{ dashboardData.funnel.conversion_rate || 0 }}%</el-descriptions-item
            >
            <el-descriptions-item label="批次总数">{{
              dashboardData.batch_summary.total || 0
            }}</el-descriptions-item>
            <el-descriptions-item label="执行中 / 待执行">
              {{ dashboardData.batch_summary.running || 0 }} /
              {{ dashboardData.batch_summary.ready || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="逾期批次">
              <el-tag :type="dashboardData.batch_summary.overdue ? 'danger' : 'success'">
                {{ dashboardData.batch_summary.overdue || 0 }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item label="待审批 / 已驳回">
              {{ dashboardData.batch_summary.pending_approval || 0 }} /
              {{ dashboardData.batch_summary.rejected_approval || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="审批超时 / 平均耗时">
              {{ dashboardData.batch_summary.approval_overdue || 0 }} /
              {{ dashboardData.batch_summary.avg_approval_hours || 0 }} 小时
            </el-descriptions-item>
            <el-descriptions-item label="已记录执行客户">{{
              dashboardData.batch_summary.execution_customer_count || 0
            }}</el-descriptions-item>
          </el-descriptions>
          <h3 class="mb-12">批次进度</h3>
          <el-table :data="dashboardData.batches" border max-height="320">
            <el-table-column prop="name" label="批次" min-width="220" show-overflow-tooltip />
            <el-table-column prop="owner_name" label="负责人" width="120" />
            <el-table-column prop="status" label="状态" width="100">
              <template #default="{ row }">{{
                touchBatchStatusMap[row.status]?.label || row.status
              }}</template>
            </el-table-column>
            <el-table-column label="进度" width="120">
              <template #default="{ row }"
                >{{ row.executed_count }} / {{ row.selected_count }}</template
              >
            </el-table-column>
            <el-table-column label="办理 / 流失" width="110">
              <template #default="{ row }"
                >{{ row.converted_count || 0 }} / {{ row.lost_count || 0 }}</template
              >
            </el-table-column>
            <el-table-column prop="deadline" label="截止时间" width="170">
              <template #default="{ row }">{{
                row.deadline ? datetimeFormat(row.deadline) : '-'
              }}</template>
            </el-table-column>
            <el-table-column label="预警" width="90">
              <template #default="{ row }"
                ><el-tag v-if="row.is_overdue" type="danger">已逾期</el-tag
                ><span v-else>-</span></template
              >
            </el-table-column>
          </el-table>
          <h3 class="mt-24 mb-12">优先处理客户</h3>
          <el-table :data="dashboardData.priority_customers" border max-height="260">
            <el-table-column prop="name" label="客户" min-width="120" />
            <el-table-column prop="phone_masked" label="手机号/标识" width="130" />
            <el-table-column prop="current_plan" label="套餐" min-width="140" />
            <el-table-column prop="status" label="状态" width="110">
              <template #default="{ row }"
                ><el-tag :type="customerStatusMap[row.status]?.type">{{
                  customerStatusMap[row.status]?.label || row.status
                }}</el-tag></template
              >
            </el-table-column>
            <el-table-column
              prop="intent"
              label="意向/处理原因"
              min-width="180"
              show-overflow-tooltip
            />
          </el-table>
        </template>
      </div>
    </el-drawer>

    <el-drawer v-model="effectVisible" title="营销任务复盘" size="760px">
      <div v-loading="effectLoading">
        <template v-if="effectData">
          <el-descriptions :column="2" border>
            <el-descriptions-item label="任务名称">
              {{ effectData.task?.name }}
            </el-descriptions-item>
            <el-descriptions-item label="营销场景">
              {{ effectData.task?.scenario_name || '-' }}
            </el-descriptions-item>
            <el-descriptions-item label="会话数">
              {{ effectData.metrics?.chat_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="目标客户">
              {{ effectData.metrics?.customer_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="已触达/已咨询">
              {{ effectData.metrics?.touched_count || 0 }} /
              {{ effectData.metrics?.consulted_customer_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="有意向/转人工">
              {{ effectData.metrics?.intent_count || 0 }} /
              {{ effectData.metrics?.manual_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="确认办理/流失">
              {{ effectData.metrics?.converted_count || 0 }} /
              {{ effectData.metrics?.lost_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="意向率">
              {{ effectData.metrics?.intent_rate || 0 }}%
            </el-descriptions-item>
            <el-descriptions-item label="转化率">
              {{ effectData.metrics?.conversion_rate || 0 }}%
            </el-descriptions-item>
            <el-descriptions-item label="已记录人工跟进">
              {{ effectData.metrics?.follow_up_record_count || 0 }} 次
            </el-descriptions-item>
            <el-descriptions-item label="自动沉淀客户数">
              {{ effectData.metrics?.auto_insight_customer_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="主要异议" :span="2">
              {{ getObjectionSummary(effectData.metrics?.objection_summary) }}
            </el-descriptions-item>
            <el-descriptions-item label="消息数">
              {{ effectData.metrics?.record_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="平均耗时">
              {{ effectData.metrics?.avg_run_time || 0 }} 秒
            </el-descriptions-item>
            <el-descriptions-item label="总 Token">
              {{ effectData.metrics?.total_tokens || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="点赞/点踩">
              {{ effectData.metrics?.star_count || 0 }} /
              {{ effectData.metrics?.trample_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="风险提示">
              跑偏 {{ effectData.metrics?.suspicious_answer_count || 0 }}， 运行错误
              {{ effectData.metrics?.runtime_error_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="质检结果">
              正常 {{ effectData.metrics?.quality_pass_count || 0 }}，待复核
              {{ effectData.metrics?.quality_pending_count || 0 }}，高风险
              {{ effectData.metrics?.quality_high_risk_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="质检通过率">
              {{ effectData.metrics?.quality_pass_rate || 0 }}%
            </el-descriptions-item>
            <el-descriptions-item label="人工质检进度">
              待处理 {{ effectData.metrics?.quality_manual_pending_count || 0 }}，已复核
              {{ effectData.metrics?.quality_manual_reviewed_count || 0 }}，已修订
              {{ effectData.metrics?.quality_manual_revised_count || 0 }}
            </el-descriptions-item>
            <el-descriptions-item label="主要质检问题" :span="2">
              {{ getQualityIssueSummary(effectData.metrics?.quality_issue_summary) }}
            </el-descriptions-item>
          </el-descriptions>

          <h3 class="mt-24 mb-12">最近对话</h3>
          <template v-if="effectData.metrics?.recommendation_summary?.length">
            <h3 class="mt-24 mb-12">推荐策略效果</h3>
            <el-table :data="effectData.metrics.recommendation_summary" size="small" border>
              <el-table-column prop="offer_name" label="活动" min-width="220" />
              <el-table-column prop="priority" label="优先级" width="90" />
              <el-table-column prop="chat_count" label="会话" width="80" />
              <el-table-column prop="record_count" label="消息" width="80" />
              <el-table-column prop="intent_count" label="意向" width="80" />
              <el-table-column prop="manual_count" label="人工" width="80" />
              <el-table-column prop="converted_count" label="办理" width="80" />
            </el-table>
          </template>
          <app-table
            :data="effectData.records?.records || []"
            :pagination-config="effectPagination"
            :maxTableHeight="360"
            @sizeChange="handleEffectSizeChange"
            @changePage="getEffect"
          >
            <el-table-column
              prop="problem_text"
              label="用户问题"
              min-width="220"
              show-overflow-tooltip
            />
            <el-table-column
              prop="answer_text"
              label="回答摘要"
              min-width="320"
              show-overflow-tooltip
            />
            <el-table-column prop="run_time" label="耗时" width="90">
              <template #default="{ row }">{{ row.run_time || 0 }} 秒</template>
            </el-table-column>
            <el-table-column prop="total_tokens" label="Token" width="90" />
            <el-table-column label="质检状态" width="140">
              <template #default="{ row }">
                <el-tag :type="qualityStatusMap[row.quality_review?.status]?.type || 'info'">
                  {{ qualityStatusMap[row.quality_review?.status]?.label || '未质检' }}
                  <template v-if="row.quality_review"> · {{ row.quality_review.score }}分</template>
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="质检原因" min-width="260" show-overflow-tooltip>
              <template #default="{ row }">
                {{ getQualityReasons(row.quality_review) }}
              </template>
            </el-table-column>
            <el-table-column prop="create_time" label="时间" width="170">
              <template #default="{ row }">{{ datetimeFormat(row.create_time) }}</template>
            </el-table-column>
          </app-table>
        </template>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import {
  ElMessage,
  ElMessageBox,
  type FormInstance,
  type FormRules,
  type UploadFile,
  type UploadUserFile,
} from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import applicationApi from '@/api/application/application'
import knowledgeApi from '@/api/knowledge/knowledge'
import marketingScenarioApi, { type MarketingScenario } from '@/api/marketing/scenario'
import campaignApi, { type MarketingCampaign } from '@/api/marketing/campaign'
import marketingTaskApi, {
  type MarketingConversionRecordWrite,
  type MarketingCustomer,
  type MarketingCustomerImportBatch,
  type MarketingCustomerImportPreview,
  type MarketingTask,
  type MarketingTaskDashboard,
  type MarketingTouchBatch,
  type MarketingTouchBatchCreate,
  type MarketingTouchBatchDetail,
  type MarketingTouchExecution,
} from '@/api/marketing/task'
import { copyClick } from '@/utils/clipboard'
import { datetimeFormat } from '@/utils/time'

const route = useRoute()
const loading = ref(false)
const submitLoading = ref(false)
const drawerVisible = ref(false)
const effectVisible = ref(false)
const dashboardVisible = ref(false)
const approvalQueueVisible = ref(false)
const customerVisible = ref(false)
const customerFormVisible = ref(false)
const customerFollowUpVisible = ref(false)
const customerConversionVisible = ref(false)
const customerImportVisible = ref(false)
const touchBatchVisible = ref(false)
const touchBatchCreateVisible = ref(false)
const touchBatchApprovalVisible = ref(false)
const followUpQueueVisible = ref(false)
const touchExecutionVisible = ref(false)
const touchExecutionFormVisible = ref(false)
const editingId = ref<string>()
const effectTaskId = ref<string>()
const customerTaskId = ref<string>()
const approvalTaskId = ref<string>()
const editingCustomerId = ref<string>()
const formRef = ref<FormInstance>()
const customerFormRef = ref<FormInstance>()
const taskList = ref<MarketingTask[]>([])
const effectData = ref<any>()
const dashboardData = ref<MarketingTaskDashboard>()
const approvalQueueData = ref<any>()
const customerList = ref<MarketingCustomer[]>([])
const customerImportFile = ref<File>()
const customerImportFileList = ref<UploadUserFile[]>([])
const customerImportHeaders = ref<string[]>([])
const customerImportMapping = ref<Record<string, string>>({})
const customerImportPreviewData = ref<MarketingCustomerImportPreview>()
const customerImportHistory = ref<MarketingCustomerImportBatch[]>([])
const touchBatchList = ref<MarketingTouchBatch[]>([])
const followUpQueue = ref<any[]>([])
const touchBatchDetail = ref<MarketingTouchBatchDetail>()
const approvingTouchBatch = ref<MarketingTouchBatch>()
const resubmittingTouchBatch = ref<MarketingTouchBatch>()
const executionCustomer = ref<Record<string, any>>()
const scenarioOptions = ref<MarketingScenario[]>([])
const applicationOptions = ref<any[]>([])
const knowledgeOptions = ref<any[]>([])
const campaignOptions = ref<MarketingCampaign[]>([])
const searchForm = ref({
  name: '',
  status: '',
  scenario_id: typeof route.query.scenario_id === 'string' ? route.query.scenario_id : '',
})
const paginationConfig = ref({
  current_page: 1,
  page_size: 20,
  total: 0,
})
const effectLoading = ref(false)
const dashboardLoading = ref(false)
const approvalQueueLoading = ref(false)
const customerLoading = ref(false)
const customerSubmitLoading = ref(false)
const customerFollowUpLoading = ref(false)
const customerConversionLoading = ref(false)
const customerImportPreviewLoading = ref(false)
const customerImportSubmitLoading = ref(false)
const customerImportHistoryLoading = ref(false)
const touchBatchLoading = ref(false)
const touchBatchSubmitLoading = ref(false)
const touchBatchApprovalLoading = ref(false)
const followUpQueueLoading = ref(false)
const touchBatchDetailLoading = ref(false)
const touchBatchScheduleLoading = ref(false)
const touchExecutionSubmitLoading = ref(false)
const effectPagination = ref({
  current_page: 1,
  page_size: 10,
  total: 0,
})
const customerPagination = ref({
  current_page: 1,
  page_size: 10,
  total: 0,
})
const customerSearch = ref({ name: '', status: '' })

const defaultForm = (): MarketingTask => ({
  name: '',
  scenario_id: '',
  target_audience: '',
  objective: '',
  channel: 'ONLINE',
  status: 'DRAFT',
  application_id: null,
  knowledge_id: null,
  target_count: 0,
  config: { approval_sla_hours: 24, pilot_size: 0 },
  campaign_ids: [],
  description: '',
})

const form = ref<MarketingTask>(defaultForm())
const defaultCustomerForm = (): MarketingCustomer => ({
  name: '',
  phone: '',
  province: '',
  current_plan: '',
  monthly_data_usage: '',
  monthly_call_usage: '',
  status: 'PENDING',
  intent: '',
  remark: '',
  config: {},
})
const customerForm = ref<MarketingCustomer>(defaultCustomerForm())
const followUpCustomer = ref<MarketingCustomer>()
const conversionCustomer = ref<MarketingCustomer>()
const defaultTouchBatchForm = (): MarketingTouchBatchCreate => ({
  name: '',
  plan_keyword: '',
  province: '',
  min_data_usage_gb: 0,
  min_call_usage_minutes: 0,
  statuses: ['PENDING'],
  cooldown_days: 7,
})
const touchBatchForm = ref<MarketingTouchBatchCreate>(defaultTouchBatchForm())
const touchBatchResubmitNote = ref('')
const touchBatchScheduleForm = ref({
  owner_name: '',
  deadline: '' as string | null,
  status: 'READY' as NonNullable<MarketingTouchBatch['status']>,
})
const touchBatchApprovalForm = ref({
  approval_status: 'APPROVED' as 'APPROVED' | 'REJECTED',
  approval_note: '',
})
const touchExecutionForm = ref({
  result: 'CONTACTED' as MarketingTouchExecution['result'],
  note: '',
  next_follow_up_at: '' as string | null,
})
const customerFollowUpForm = ref({
  status: 'CONSULTED' as NonNullable<MarketingCustomer['status']>,
  intent: '待跟进',
  note: '',
})
const conversionForm = ref<MarketingConversionRecordWrite>({
  outcome: 'CONVERTED',
  product_name: '',
  note: '',
  batch_id: null,
})
const customerImportFields = [
  { key: 'name', label: '客户名称', required: false },
  { key: 'phone', label: '手机号/客户标识', required: true },
  { key: 'province', label: '省份', required: false },
  { key: 'current_plan', label: '当前套餐', required: false },
  { key: 'monthly_data_usage', label: '近月流量', required: false },
  { key: 'monthly_call_usage', label: '近月通话', required: false },
  { key: 'intent', label: '初始意向', required: false },
  { key: 'remark', label: '备注', required: false },
]

const rules: FormRules = {
  name: [{ required: true, message: '请输入任务名称', trigger: 'blur' }],
  scenario_id: [{ required: true, message: '请选择营销场景', trigger: 'change' }],
  status: [{ required: true, message: '请选择任务状态', trigger: 'change' }],
}

const statusMap: Record<
  string,
  { label: string; type: '' | 'success' | 'warning' | 'info' | 'danger' }
> = {
  DRAFT: { label: '草稿', type: 'info' },
  RUNNING: { label: '进行中', type: 'success' },
  PAUSED: { label: '暂停', type: 'warning' },
  FINISHED: { label: '已完成', type: '' },
}
const qualityStatusMap: Record<
  string,
  { label: string; type: '' | 'success' | 'warning' | 'info' | 'danger' }
> = {
  PASS: { label: '正常', type: 'success' },
  REVIEW: { label: '需复核', type: 'warning' },
  HIGH_RISK: { label: '高风险', type: 'danger' },
}
const customerStatusMap: Record<
  string,
  { label: string; type: '' | 'success' | 'warning' | 'info' | 'danger' }
> = {
  PENDING: { label: '待触达', type: 'info' },
  TOUCHED: { label: '已触达', type: '' },
  CONSULTED: { label: '已咨询', type: 'success' },
  INTENT: { label: '有意向', type: 'success' },
  NO_INTENT: { label: '无意向', type: 'info' },
  MANUAL: { label: '转人工', type: 'warning' },
  CONVERTED: { label: '已办理', type: 'success' },
}
const conversionOutcomeMap: Record<
  string,
  { label: string; type: '' | 'success' | 'warning' | 'info' | 'danger' }
> = {
  CONVERTED: { label: '确认办理', type: 'success' },
  LOST: { label: '确认流失', type: 'info' },
}
const customerImportStatusMap: Record<
  string,
  { label: string; type: '' | 'success' | 'warning' | 'info' | 'danger' }
> = {
  READY: { label: '可导入', type: 'success' },
  SKIPPED: { label: '跳过', type: 'warning' },
  ERROR: { label: '错误', type: 'danger' },
}
const touchBatchStatusMap: Record<
  string,
  { label: string; type: '' | 'success' | 'warning' | 'info' | 'danger' }
> = {
  READY: { label: '待执行', type: 'info' },
  RUNNING: { label: '执行中', type: 'success' },
  CLOSED: { label: '已关闭', type: '' },
}
const touchBatchApprovalMap: Record<
  string,
  { label: string; type: '' | 'success' | 'warning' | 'info' | 'danger' }
> = {
  PENDING: { label: '待审批', type: 'warning' },
  APPROVED: { label: '已通过', type: 'success' },
  REJECTED: { label: '已驳回', type: 'danger' },
}
const touchBatchApprovalActionMap: Record<string, string> = {
  SUBMITTED: '提交审批',
  APPROVED: '审批通过',
  REJECTED: '审批驳回',
  RESUBMITTED: '修改后重提',
}
const touchExecutionResultMap: Record<string, string> = {
  CONTACTED: '已联系',
  NO_ANSWER: '未接通',
  REJECTED: '明确拒绝',
  INTENT: '有办理意向',
  MANUAL: '转人工处理',
}

function getList() {
  marketingTaskApi.getTaskPage(paginationConfig.value, searchForm.value, loading).then((res) => {
    taskList.value = res.data.records
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
  marketingScenarioApi.getScenarioList({ status: '' }).then((res) => {
    scenarioOptions.value = res.data || []
  })
  applicationApi.getAllApplication({ name: '' }).then((res) => {
    applicationOptions.value = res.data || []
  })
  knowledgeApi.getKnowledgeList({ name: '' }).then((res) => {
    knowledgeOptions.value = res.data || []
  })
  campaignApi.list({ status: 'ACTIVE' }).then((res) => {
    campaignOptions.value = res.data || []
  })
}

function syncScenarioDefaults() {
  const scenario = scenarioOptions.value.find((item) => item.id === form.value.scenario_id)
  if (!scenario) return
  form.value.target_audience = form.value.target_audience || scenario.target_audience || ''
  form.value.objective = form.value.objective || scenario.objective || ''
  form.value.channel = form.value.channel || scenario.channel || 'ONLINE'
  form.value.application_id = form.value.application_id || scenario.application_id || null
  form.value.knowledge_id = form.value.knowledge_id || scenario.knowledge_id || null
}

function openCreate() {
  editingId.value = undefined
  form.value = defaultForm()
  if (searchForm.value.scenario_id) {
    form.value.scenario_id = searchForm.value.scenario_id
    syncScenarioDefaults()
  }
  drawerVisible.value = true
}

function openEdit(row: MarketingTask) {
  editingId.value = row.id
  form.value = {
    name: row.name,
    scenario_id: row.scenario_id,
    target_audience: row.target_audience,
    objective: row.objective,
    channel: row.channel || 'ONLINE',
    status: row.status || 'DRAFT',
    application_id: row.application_id || null,
    knowledge_id: row.knowledge_id || null,
    target_count: row.target_count || 0,
    config: { approval_sla_hours: 24, pilot_size: 0, ...(row.config || {}) },
    campaign_ids: row.campaign_ids || [],
    description: row.description || '',
  }
  drawerVisible.value = true
}

function submit() {
  formRef.value?.validate((valid) => {
    if (!valid) return
    const request = editingId.value
      ? marketingTaskApi.updateTask(editingId.value, form.value, submitLoading)
      : marketingTaskApi.createTask(form.value, submitLoading)
    request.then(() => {
      ElMessage.success('保存成功')
      drawerVisible.value = false
      getList()
    })
  })
}

function getFullChatUrl(row: MarketingTask) {
  if (!row.chat_url) return ''
  return `${window.location.origin}${row.chat_url}`
}

function openChat(row: MarketingTask) {
  const url = getFullChatUrl(row)
  if (url) window.open(url, '_blank')
}

function copyChatUrl(row: MarketingTask) {
  const url = getFullChatUrl(row)
  if (url) copyClick(url)
}

function openCustomers(row: MarketingTask) {
  if (!row.id) return
  customerTaskId.value = row.id
  customerPagination.value.current_page = 1
  customerSearch.value = { name: '', status: '' }
  customerVisible.value = true
  getCustomers()
}

function getCustomers() {
  if (!customerTaskId.value) return
  marketingTaskApi
    .getCustomerPage(
      customerTaskId.value,
      customerPagination.value,
      customerSearch.value,
      customerLoading,
    )
    .then((res) => {
      customerList.value = res.data.records
      customerPagination.value.total = res.data.total
      customerPagination.value.current_page = res.data.current
      customerPagination.value.page_size = res.data.size
    })
}

function handleCustomerSizeChange() {
  customerPagination.value.current_page = 1
  getCustomers()
}

function openCustomerImport() {
  if (!customerTaskId.value) return
  customerImportFile.value = undefined
  customerImportFileList.value = []
  customerImportHeaders.value = []
  customerImportMapping.value = {}
  customerImportPreviewData.value = undefined
  customerImportVisible.value = true
  getCustomerImportHistory()
}

function handleCustomerImportFile(file: UploadFile) {
  const rawFile = file.raw
  if (!rawFile) return
  const suffix = rawFile.name.split('.').pop()?.toLowerCase()
  if (!['csv', 'xlsx'].includes(suffix || '')) {
    ElMessage.warning('仅支持 CSV 或 XLSX 客户名单文件')
    customerImportFileList.value = []
    return
  }
  if (rawFile.size > 5 * 1024 * 1024) {
    ElMessage.warning('导入文件不能超过 5MB')
    customerImportFileList.value = []
    return
  }
  customerImportFile.value = rawFile
  customerImportFileList.value = [file]
  customerImportHeaders.value = []
  customerImportMapping.value = {}
  customerImportPreviewData.value = undefined
}

function clearCustomerImportFile() {
  customerImportFile.value = undefined
  customerImportFileList.value = []
  customerImportHeaders.value = []
  customerImportMapping.value = {}
  customerImportPreviewData.value = undefined
}

function previewCustomerImport() {
  if (!customerTaskId.value || !customerImportFile.value) {
    ElMessage.warning('请先选择客户名单文件')
    return
  }
  const formData = new FormData()
  formData.append('file', customerImportFile.value, customerImportFile.value.name)
  if (Object.keys(customerImportMapping.value).length) {
    formData.append('mapping', JSON.stringify(customerImportMapping.value))
  }
  marketingTaskApi
    .previewCustomerImport(customerTaskId.value, formData, customerImportPreviewLoading)
    .then((res) => {
      customerImportPreviewData.value = res.data
      customerImportHeaders.value = res.data.headers
      customerImportMapping.value = { ...res.data.mapping }
    })
}

function submitCustomerImport() {
  if (!customerTaskId.value || !customerImportPreviewData.value?.summary.ready_count) return
  const preview = customerImportPreviewData.value
  marketingTaskApi
    .confirmCustomerImport(
      customerTaskId.value,
      { file_name: preview.file_name, mapping: preview.mapping, rows: preview.rows },
      customerImportSubmitLoading,
    )
    .then((res) => {
      ElMessage.success(
        `已导入 ${res.data.batch.imported_count} 名客户，跳过 ${res.data.batch.skipped_count} 条`,
      )
      customerImportVisible.value = false
      getCustomers()
      getList()
    })
}

function getCustomerImportHistory() {
  if (!customerTaskId.value) return
  marketingTaskApi
    .getCustomerImportHistory(customerTaskId.value, customerImportHistoryLoading)
    .then((res) => {
      customerImportHistory.value = res.data || []
    })
}

function downloadCustomerImportTemplate() {
  const content =
    '\ufeff客户名称,手机号,省份,当前套餐,近月流量,近月通话,初始意向,备注\n张女士,13800000000,广东,199元套餐,80GB,300分钟,待触达,示例数据\n'
  const url = URL.createObjectURL(new Blob([content], { type: 'text/csv;charset=utf-8' }))
  const link = document.createElement('a')
  link.href = url
  link.download = '营销客户名单导入模板.csv'
  link.click()
  URL.revokeObjectURL(url)
}

function getTouchBatches() {
  if (!customerTaskId.value) return
  marketingTaskApi.getTouchBatches(customerTaskId.value, touchBatchLoading).then((res) => {
    touchBatchList.value = res.data || []
  })
}

function openTouchBatch() {
  touchBatchVisible.value = true
  getTouchBatches()
}

function openTouchBatchCreate() {
  resubmittingTouchBatch.value = undefined
  touchBatchResubmitNote.value = ''
  touchBatchForm.value = defaultTouchBatchForm()
  touchBatchCreateVisible.value = true
}

function submitTouchBatch() {
  if (!customerTaskId.value) return
  if (!touchBatchForm.value.name.trim()) {
    ElMessage.warning('请填写批次名称')
    return
  }
  if (!touchBatchForm.value.statuses?.length) {
    ElMessage.warning('请至少选择一种客户状态')
    return
  }
  if (resubmittingTouchBatch.value?.id && !touchBatchResubmitNote.value.trim()) {
    ElMessage.warning('请填写修改说明')
    return
  }
  const request = resubmittingTouchBatch.value?.id
    ? marketingTaskApi.resubmitTouchBatch(
        customerTaskId.value,
        resubmittingTouchBatch.value.id,
        { ...touchBatchForm.value, resubmit_note: touchBatchResubmitNote.value },
        touchBatchSubmitLoading,
      )
    : marketingTaskApi.createTouchBatch(
        customerTaskId.value,
        touchBatchForm.value,
        touchBatchSubmitLoading,
      )
  request.then((res) => {
    ElMessage.success(
      resubmittingTouchBatch.value
        ? `批次已重新提交，入选 ${res.data.selected_count || 0} 人`
        : `批次已生成，入选 ${res.data.selected_count || 0} 人`,
    )
    touchBatchCreateVisible.value = false
    resubmittingTouchBatch.value = undefined
    getTouchBatches()
  })
}

function getTouchBatchFilterSummary(row: MarketingTouchBatch) {
  const filter = row.filter_config || {}
  const statuses = Array.isArray(filter.statuses)
    ? filter.statuses.map((item) => customerStatusMap[item]?.label || item)
    : []
  const conditions = [
    statuses.length ? `状态：${statuses.join('、')}` : '',
    filter.plan_keyword ? `套餐：${filter.plan_keyword}` : '',
    filter.province ? `省份：${filter.province}` : '',
    filter.min_data_usage_gb ? `流量≥${filter.min_data_usage_gb}GB` : '',
    filter.min_call_usage_minutes ? `通话≥${filter.min_call_usage_minutes}分钟` : '',
  ].filter(Boolean)
  return conditions.join('；') || '未设置额外条件'
}

function openTouchExecution(row: MarketingTouchBatch) {
  if (!customerTaskId.value || !row.id) return
  if (row.approval_status !== 'APPROVED') {
    ElMessage.warning('请先审批通过该批次，再进入执行')
    return
  }
  touchExecutionVisible.value = true
  marketingTaskApi
    .getTouchBatchDetail(customerTaskId.value, row.id, touchBatchDetailLoading)
    .then((res) => {
      touchBatchDetail.value = res.data
      touchBatchScheduleForm.value = {
        owner_name: res.data.batch.owner_name || '',
        deadline: res.data.batch.deadline || '',
        status: res.data.batch.status || 'READY',
      }
    })
}

function openTouchBatchApproval(row: MarketingTouchBatch, taskId = customerTaskId.value) {
  if (!row.id || !taskId) return
  approvingTouchBatch.value = row
  approvalTaskId.value = taskId
  touchBatchApprovalForm.value = {
    approval_status: row.approval_status === 'REJECTED' ? 'REJECTED' : 'APPROVED',
    approval_note: row.approval_note || '',
  }
  touchBatchApprovalVisible.value = true
}

function openTouchBatchResubmit(row: MarketingTouchBatch) {
  const filters = row.filter_config || {}
  resubmittingTouchBatch.value = row
  touchBatchResubmitNote.value = ''
  touchBatchForm.value = {
    name: row.name,
    plan_keyword: filters.plan_keyword || '',
    province: filters.province || '',
    min_data_usage_gb: filters.min_data_usage_gb || 0,
    min_call_usage_minutes: filters.min_call_usage_minutes || 0,
    statuses: filters.statuses || ['PENDING'],
    cooldown_days: filters.cooldown_days ?? 7,
  }
  touchBatchCreateVisible.value = true
}

function submitTouchBatchApproval() {
  if (!approvalTaskId.value || !approvingTouchBatch.value?.id) return
  marketingTaskApi
    .approveTouchBatch(
      approvalTaskId.value,
      approvingTouchBatch.value.id,
      touchBatchApprovalForm.value,
      touchBatchApprovalLoading,
    )
    .then(() => {
      ElMessage.success(
        touchBatchApprovalForm.value.approval_status === 'APPROVED'
          ? '批次已审批通过'
          : '批次已驳回',
      )
      touchBatchApprovalVisible.value = false
      getTouchBatches()
      if (approvalQueueVisible.value) getApprovalQueue()
    })
}

function getApprovalQueue() {
  marketingTaskApi.getApprovalQueue(approvalQueueLoading).then((res) => {
    approvalQueueData.value = res.data
  })
}

function openApprovalQueue() {
  approvalQueueVisible.value = true
  getApprovalQueue()
}

function saveTouchBatchSchedule() {
  if (!customerTaskId.value || !touchBatchDetail.value?.batch.id) return
  marketingTaskApi
    .updateTouchBatch(
      customerTaskId.value,
      touchBatchDetail.value.batch.id,
      touchBatchScheduleForm.value,
      touchBatchScheduleLoading,
    )
    .then((res) => {
      touchBatchDetail.value = {
        ...touchBatchDetail.value!,
        batch: { ...touchBatchDetail.value!.batch, ...res.data },
      }
      ElMessage.success('批次安排已保存')
      getTouchBatches()
    })
}

function getLatestExecutionSummary(customerId: string) {
  const execution = touchBatchDetail.value?.executions.find(
    (item) => item.customer_id === customerId,
  )
  if (!execution) return '尚未记录'
  return `${touchExecutionResultMap[execution.result] || execution.result}：${execution.note}`
}

function openExecutionRecord(row: Record<string, any>) {
  executionCustomer.value = row
  touchExecutionForm.value = {
    result: 'CONTACTED',
    note: '',
    next_follow_up_at: '',
  }
  touchExecutionFormVisible.value = true
}

function submitTouchExecution() {
  if (
    !customerTaskId.value ||
    !touchBatchDetail.value?.batch.id ||
    !executionCustomer.value?.customer_id
  )
    return
  if (!touchExecutionForm.value.note.trim()) {
    ElMessage.warning('请填写执行记录')
    return
  }
  marketingTaskApi
    .createTouchExecution(
      customerTaskId.value,
      touchBatchDetail.value.batch.id,
      {
        customer_id: executionCustomer.value.customer_id,
        result: touchExecutionForm.value.result,
        note: touchExecutionForm.value.note,
        next_follow_up_at: touchExecutionForm.value.next_follow_up_at || null,
      },
      touchExecutionSubmitLoading,
    )
    .then(() => {
      ElMessage.success('触达结果已记录')
      touchExecutionFormVisible.value = false
      openTouchExecution(touchBatchDetail.value!.batch)
      getCustomers()
      getFollowUpQueueAfterExecution()
    })
}

function getFollowUpQueueAfterExecution() {
  if (!followUpQueueVisible.value || !customerTaskId.value) return
  marketingTaskApi.getFollowUpQueue(customerTaskId.value, followUpQueueLoading).then((res) => {
    followUpQueue.value = res.data || []
  })
}

function openFollowUpQueue() {
  if (!customerTaskId.value) return
  followUpQueueVisible.value = true
  marketingTaskApi.getFollowUpQueue(customerTaskId.value, followUpQueueLoading).then((res) => {
    followUpQueue.value = res.data || []
  })
}

function openCustomerCreate() {
  editingCustomerId.value = undefined
  customerForm.value = defaultCustomerForm()
  customerFormVisible.value = true
}

function openCustomerEdit(row: MarketingCustomer) {
  editingCustomerId.value = row.id
  customerForm.value = {
    name: row.name || '',
    phone: row.phone || '',
    province: row.province || '',
    current_plan: row.current_plan || '',
    monthly_data_usage: row.monthly_data_usage || '',
    monthly_call_usage: row.monthly_call_usage || '',
    status: row.status || 'PENDING',
    intent: row.intent || '',
    remark: row.remark || '',
    config: row.config || {},
  }
  customerFormVisible.value = true
}

function getCustomerInsightSummary(row: MarketingCustomer) {
  const insight = row.config?.marketing_insight
  if (!insight) return row.intent || '-'
  const objections = Array.isArray(insight.objection_tags) ? insight.objection_tags.join('、') : ''
  return [row.intent || insight.intent, objections].filter(Boolean).join(' · ') || '-'
}

function getObjectionSummary(summary: Array<{ tag: string; count: number }> | undefined) {
  if (!summary?.length) return '暂无'
  return summary.map((item) => `${item.tag} ${item.count}`).join('，')
}

function getQualityIssueSummary(summary: Array<{ reason: string; count: number }> | undefined) {
  if (!summary?.length) return '暂无'
  return summary.map((item) => `${item.reason} ${item.count}`).join('；')
}

function getQualityReasons(review: { reasons?: string[]; suggestion?: string } | undefined) {
  if (!review?.reasons?.length) return '无风险项'
  return [...review.reasons, review.suggestion].filter(Boolean).join('；')
}

function openCustomerFollowUp(row: MarketingCustomer) {
  if (row.status === 'CONVERTED') {
    ElMessage.warning('该客户已确认办理，如需更正请通过“转化”登记新的结果')
    return
  }
  followUpCustomer.value = row
  customerFollowUpForm.value = {
    status:
      row.status === 'INTENT' || row.status === 'NO_INTENT' || row.status === 'MANUAL'
        ? row.status
        : 'CONSULTED',
    intent: row.intent || '待跟进',
    note: '',
  }
  customerFollowUpVisible.value = true
}

function openCustomerConversion(row: MarketingCustomer, batchId: string | null = null) {
  if (!customerTaskId.value || !row.id) return
  conversionCustomer.value = row
  conversionForm.value = {
    outcome: row.latest_conversion?.outcome || 'CONVERTED',
    product_name: row.latest_conversion?.product_name || '',
    note: '',
    batch_id:
      batchId ||
      row.latest_conversion?.batch_id ||
      row.config?.marketing_latest_touch_batch?.id ||
      null,
  }
  if (!touchBatchList.value.length) getTouchBatches()
  customerConversionVisible.value = true
}

function openBatchCustomerConversion(row: Record<string, any>) {
  const batchId = touchBatchDetail.value?.batch.id || null
  openCustomerConversion(
    {
      id: row.customer_id,
      name: row.name,
      phone_masked: row.phone_masked,
      latest_conversion: null,
      config: {},
    },
    batchId,
  )
}

function submitCustomerConversion() {
  if (!customerTaskId.value || !conversionCustomer.value?.id) return
  if (conversionForm.value.outcome === 'CONVERTED' && !conversionForm.value.product_name?.trim()) {
    ElMessage.warning('请填写实际办理的套餐或产品')
    return
  }
  if (!conversionForm.value.note.trim()) {
    ElMessage.warning('请填写结果说明')
    return
  }
  marketingTaskApi
    .recordCustomerConversion(
      customerTaskId.value,
      conversionCustomer.value.id,
      conversionForm.value,
      customerConversionLoading,
    )
    .then(() => {
      ElMessage.success(
        conversionForm.value.outcome === 'CONVERTED' ? '已确认办理并完成归因' : '已登记流失结果',
      )
      customerConversionVisible.value = false
      getCustomers()
      getList()
      getFollowUpQueueAfterExecution()
      if (touchExecutionVisible.value && touchBatchDetail.value?.batch.id)
        openTouchExecution(touchBatchDetail.value.batch)
      if (dashboardVisible.value && customerTaskId.value) getDashboard(customerTaskId.value)
      if (effectVisible.value && effectTaskId.value === customerTaskId.value) getEffect()
    })
}

function submitCustomerFollowUp() {
  if (!customerTaskId.value || !followUpCustomer.value?.id) return
  if (!customerFollowUpForm.value.note.trim()) {
    ElMessage.warning('请填写跟进记录')
    return
  }
  marketingTaskApi
    .followUpCustomer(
      customerTaskId.value,
      followUpCustomer.value.id,
      customerFollowUpForm.value,
      customerFollowUpLoading,
    )
    .then(() => {
      ElMessage.success('跟进已记录')
      customerFollowUpVisible.value = false
      getCustomers()
      getList()
    })
}

function submitCustomer() {
  if (!customerTaskId.value) return
  const request = editingCustomerId.value
    ? marketingTaskApi.updateCustomer(
        customerTaskId.value,
        editingCustomerId.value,
        customerForm.value,
        customerSubmitLoading,
      )
    : marketingTaskApi.createCustomer(
        customerTaskId.value,
        customerForm.value,
        customerSubmitLoading,
      )
  request.then(() => {
    ElMessage.success('保存成功')
    customerFormVisible.value = false
    getCustomers()
    getList()
  })
}

function getFullCustomerChatUrl(row: MarketingCustomer) {
  if (!row.chat_url) return ''
  return `${window.location.origin}${row.chat_url}`
}

function openCustomerChat(row: MarketingCustomer) {
  const url = getFullCustomerChatUrl(row)
  if (url) window.open(url, '_blank')
}

function copyCustomerChatUrl(row: MarketingCustomer) {
  const url = getFullCustomerChatUrl(row)
  if (url) copyClick(url)
}

function removeCustomer(row: MarketingCustomer) {
  if (!customerTaskId.value || !row.id) return
  ElMessageBox.confirm(
    `确认删除客户「${row.name || row.phone_masked || row.id}」吗？`,
    '删除确认',
    {
      type: 'warning',
    },
  ).then(() => {
    marketingTaskApi
      .deleteCustomer(customerTaskId.value as string, row.id as string, customerLoading)
      .then(() => {
        ElMessage.success('删除成功')
        getCustomers()
        getList()
      })
  })
}

function openDashboard(row: MarketingTask) {
  if (!row.id) return
  dashboardVisible.value = true
  getDashboard(row.id)
}

function getDashboard(taskId: string) {
  marketingTaskApi.getTaskDashboard(taskId, dashboardLoading).then((res) => {
    dashboardData.value = res.data
  })
}

function openEffect(row: MarketingTask) {
  if (!row.id) return
  effectTaskId.value = row.id
  effectPagination.value.current_page = 1
  effectVisible.value = true
  getEffect()
}

function getEffect() {
  if (!effectTaskId.value) return
  marketingTaskApi
    .getTaskEffect(effectTaskId.value, effectPagination.value, effectLoading)
    .then((res) => {
      effectData.value = res.data
      effectPagination.value.total = res.data.records.total
      effectPagination.value.current_page = res.data.records.current
      effectPagination.value.page_size = res.data.records.size
    })
}

function handleEffectSizeChange() {
  effectPagination.value.current_page = 1
  getEffect()
}

function remove(row: MarketingTask) {
  if (!row.id) return
  ElMessageBox.confirm(`确认删除营销任务「${row.name}」吗？`, '删除确认', { type: 'warning' }).then(
    () => {
      marketingTaskApi.deleteTask(row.id as string, loading).then(() => {
        ElMessage.success('删除成功')
        getList()
      })
    },
  )
}

onMounted(() => {
  getList()
  loadOptions()
})
</script>
