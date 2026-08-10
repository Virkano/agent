<template>
  <el-dialog v-model="dialogVisible" :close-on-click-modal="false" :close-on-press-escape="false"
             :destroy-on-close="true" width="860">
    <template #header>
      <h4 class="mb-8 medium">{{ t('views.chatUser.syncUsers') }}</h4>
      <div class="color-secondary lighter">{{ t('views.chatUser.syncUsersTip') }}</div>
    </template>
    <el-form label-position="top" ref="formRef" :rules="rules" :model="form"
             require-asterisk-position="right">
      <el-form-item :label="$t('views.userManage.source.label')" prop="sync_type">
        <el-select v-model="form.sync_type" :placeholder="$t('common.selectPlaceholder')" @change="getSystemUserList">
          <el-option
            v-for="option in syncTypeOptions"
            :key="option.value"
            :label="option.label"
            :value="option.value"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <div v-if="form.sync_type === 'system'">
      <div class="flex-between mb-12">
        <el-input
          v-model="searchValue"
          clearable
          style="width: 280px"
          :placeholder="$t('common.searchBar.placeholder')"
          @keyup.enter="searchSystemUsers"
          @clear="searchSystemUsers"
        />
        <el-button @click="searchSystemUsers">{{ $t('common.search') }}</el-button>
      </div>
      <el-table
        :data="systemUserData"
        height="360"
        border
        v-loading="userLoading"
        @selection-change="selectionChange"
      >
        <el-table-column type="selection" width="48" />
        <el-table-column prop="username" :label="$t('views.login.loginForm.username.label')" min-width="150" />
        <el-table-column prop="nick_name" :label="$t('views.userManage.userForm.nick_name.label')" min-width="140" />
        <el-table-column prop="email" label="Email" min-width="180" show-overflow-tooltip />
        <el-table-column prop="is_active" :label="$t('common.status.label')" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'">
              {{ row.is_active ? $t('common.status.enable') : $t('common.status.disable') }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="flex-between mt-12">
        <span class="color-secondary lighter">
          {{ selectedUsers.length }} / {{ paginationConfig.total }}
        </span>
        <el-pagination
          v-model:current-page="paginationConfig.current_page"
          v-model:page-size="paginationConfig.page_size"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          :total="paginationConfig.total"
          @size-change="getSystemUserList"
          @current-change="getSystemUserList"
        />
      </div>
    </div>
    <template #footer>
      <span class="dialog-footer">
        <el-button @click.prevent="dialogVisible = false"> {{ $t('common.cancel') }} </el-button>
        <el-button type="primary" @click="submit(formRef)" :loading="loading">
          {{ $t('common.import') }}
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import {ref, reactive} from 'vue'
import type {FormInstance} from 'element-plus'
import {MsgError, MsgSuccess} from '@/utils/message'
import {t} from '@/locales'
import userManageApi from '@/api/system/chat-user'
import systemChatUserApi from '@/api/system/chat-user'
import systemUserApi from '@/api/system/user-manage'

const syncTypeOptions = ref<Array<{ label: string; value: string }>>([
  {label: t('views.userManage.source.local'), value: 'system'},
])

const emit = defineEmits<{
  (e: 'refresh'): void;
}>();

const dialogVisible = ref<boolean>(false)
const defaultForm = {
  sync_type: 'system',
}
const form = ref<{
  sync_type: string
}>({
  ...defaultForm,
})

function open() {
  form.value = {...defaultForm}
  getSyncType()
  searchValue.value = ''
  selectedUsers.value = []
  paginationConfig.current_page = 1
  getSystemUserList()
  dialogVisible.value = true
}

async function getSyncType() {
  return systemChatUserApi.getSyncType().then((res) => {
    if (res.data && res.data.length > 0) {
      const types = res.data.map((item: any) => (typeof item === 'string' ? item : item.value))
      syncTypeOptions.value = syncTypeOptions.value.filter(option => types.includes(option.value))
    }
  })
}

const formRef = ref<FormInstance>();

const rules = reactive({
  sync_type: [{required: true, message: t('common.selectPlaceholder'), trigger: 'blur'}],
})

const loading = ref<boolean>(false)
const userLoading = ref<boolean>(false)
const searchValue = ref('')
const selectedUsers = ref<any[]>([])
const systemUserData = ref<any[]>([])
const paginationConfig = reactive({
  current_page: 1,
  page_size: 10,
  total: 0,
})

function selectionChange(rows: any[]) {
  selectedUsers.value = rows
}

function searchSystemUsers() {
  paginationConfig.current_page = 1
  getSystemUserList()
}

function getSystemUserList() {
  if (form.value.sync_type !== 'system') {
    return
  }
  const params = searchValue.value ? { username: searchValue.value } : {}
  systemUserApi.getUserManage(paginationConfig, params, userLoading).then((res) => {
    systemUserData.value = res.data.records || []
    paginationConfig.total = res.data.total || 0
    selectedUsers.value = []
  })
}

const submit = async (formEl: FormInstance | undefined) => {
  if (!formEl) return
  await formEl.validate((valid) => {
    if (valid) {
      const userIds = selectedUsers.value.map((user) => user.id)
      if (form.value.sync_type === 'system' && userIds.length === 0) {
        MsgError(t('common.selectPlaceholder'))
        return
      }
      userManageApi.batchSync(form.value.sync_type, userIds, loading).then((res) => {
        if (res.data) {
          const count = res.data.success_count
          let ErrorMsg = ''
          if (res.data.conflict_users && res.data.conflict_users.length > 0) {
            // 遍历res.data.conflict_users， 他是一个数组里面是对象
            res.data.conflict_users.forEach((item: any) => {
              if (item.type === 'username') {
                ErrorMsg += '\n\n' + t('views.chatUser.syncMessage.usernameExist') + " [ " + item.users.join(',') + '\n' + ' ]'
              }
              if (item.type === 'nick_name') {
                ErrorMsg += '\n\n' + t('views.chatUser.syncMessage.nicknameExist') + " [ " + item.users.join(',') + '\n' + ' ]'
              }
            })
          }
          MsgSuccess(t('views.chatUser.syncMessage.title', {count: count}) + ErrorMsg)
          emit('refresh')
          dialogVisible.value = false
        }

      })
    }
  })
}

defineExpose({open})
</script>
