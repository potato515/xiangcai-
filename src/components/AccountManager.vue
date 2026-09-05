<template>
  <PageCard>
    <template #title>{{ platformLabel }}账号管理</template>
    <template #extra>
      <a-button type="primary" @click="showModal = true">
        <template #icon><icon-plus /></template>新增账号
      </a-button>
    </template>

    <!-- 批量操作栏 -->
    <div v-if="selectedIds.length > 0" class="batch-bar">
      <span>已选择 <strong style="color:#165dff">{{ selectedIds.length }}</strong> 项</span>
      <a-space>
        <a-button size="small" status="danger" @click="batchDelete">
          <template #icon><icon-delete /></template>批量删除
        </a-button>
        <a-button size="small" type="text" @click="selectedIds = []">取消选择</a-button>
      </a-space>
    </div>

    <a-table
      :data="tableData"
      :loading="loading"
      :pagination="false"
      :bordered="{ cell: true }"
      row-key="id"
      @select-all="handleSelectAll"
      @select="handleSelect"
    >
      <template #columns>
        <a-table-column type="selection" :width="50" />
        <a-table-column title="ID" data-index="id" :width="70" />
        <a-table-column title="用户名" data-index="username" :width="160" />
        <a-table-column v-if="platform === 'yangdu'" title="账号类型" data-index="account_type" :width="120">
          <template #cell="{ record }">{{ accountTypeText(record.account_type) }}</template>
        </a-table-column>
        <a-table-column title="登录状态" data-index="login_status" :width="100">
          <template #cell="{ record }">
            <StatusTag :status="record.login_status" type="login" />
          </template>
        </a-table-column>
        <a-table-column title="浏览器状态" data-index="browser_state" :width="100">
          <template #cell="{ record }">
            <StatusTag :status="record.browser_state" type="browser" />
          </template>
        </a-table-column>
        <a-table-column title="启用" data-index="enabled" :width="80">
          <template #cell="{ record }">
            <a-switch :checked="record.enabled === 1" size="small" @change="toggleAccount(record)" />
          </template>
        </a-table-column>
        <a-table-column title="今日发布" data-index="today_count" :width="90" />
        <a-table-column title="备注" data-index="remark" :width="150" />
        <a-table-column title="操作" :width="200" fixed="right">
          <template #cell="{ record }">
            <a-space>
              <a-button type="text" size="small" status="success" @click="triggerLogin(record)">触发登录</a-button>
              <a-button type="text" size="small" @click="editAccount(record)">编辑</a-button>
              <a-button type="text" size="small" status="danger" @click="deleteAccount(record)">删除</a-button>
            </a-space>
          </template>
        </a-table-column>
      </template>
    </a-table>

    <a-empty v-if="!loading && tableData.length === 0" description="暂无账号，点击右上角新增" />

    <!-- 新增/编辑弹窗 -->
    <a-modal v-model:visible="showModal" :title="editingId ? '编辑账号' : '新增账号'" @ok="saveAccount" confirm-loading="saving">
      <a-form :model="form" layout="vertical">
        <a-form-item label="用户名" required>
          <a-input v-model="form.username" placeholder="请输入用户名" />
        </a-form-item>
        <a-form-item label="密码">
          <a-input-password v-model="form.password" placeholder="请输入密码（可选，可填Cookie）" />
        </a-form-item>
        <a-form-item label="Cookie">
          <a-textarea v-model="form.cookie" placeholder="请输入Cookie（可选）" :rows="2" />
        </a-form-item>
        <a-form-item v-if="platform === 'yangdu'" label="账号类型">
          <a-select v-model="form.account_type" style="width:100%">
            <a-option value="old">老系统</a-option>
            <a-option value="new">新系统</a-option>
            <a-option value="zhipu">智谱web</a-option>
          </a-select>
        </a-form-item>
        <a-form-item v-if="platform === 'yuanbao'" label="模型">
          <a-select v-model="form.account_type" style="width:100%">
            <a-option value="deepseek">DeepSeek</a-option>
            <a-option value="hunyuan">Hunyuan</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="备注">
          <a-input v-model="form.remark" placeholder="请输入备注（可选）" />
        </a-form-item>
      </a-form>
    </a-modal>
  </PageCard>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus, IconDelete } from '@arco-design/web-vue/es/icon'
import PageCard from '@/components/common/PageCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { accountApi } from '@/api'

const props = defineProps({
  platform: { type: String, required: true },
  platformLabel: { type: String, required: true }
})

const loading = ref(false)
const tableData = ref([])
const showModal = ref(false)
const saving = ref(false)
const editingId = ref(null)
const selectedIds = ref([])

const form = reactive({
  username: '',
  password: '',
  cookie: '',
  account_type: '',
  remark: ''
})

const accountTypeText = (t) => ({ old: '老系统', new: '新系统', zhipu: '智谱web', deepseek: 'DeepSeek', hunyuan: 'Hunyuan' }[t] || t)

const loadData = async () => {
  loading.value = true
  try {
    const res = await accountApi.list(props.platform)
    tableData.value = res.data?.list || res.list || []
  } catch (e) {
    Message.error(`加载${props.platformLabel}账号列表失败，请检查后端服务`)
    tableData.value = []
  } finally {
    loading.value = false
  }
}

const handleSelectAll = (checked) => {
  selectedIds.value = checked ? tableData.value.map(a => a.id) : []
}

const handleSelect = (record, checked) => {
  if (checked) selectedIds.value.push(record.id)
  else selectedIds.value = selectedIds.value.filter(id => id !== record.id)
}

const triggerLogin = async (record) => {
  try {
    await accountApi.login(props.platform, record.id)
    Message.success(`账号 ${record.username} 登录指令已发送`)
  } catch {
    Message.error('触发登录失败，请检查后端服务')
  }
  loadData()
}

const toggleAccount = async (record) => {
  try {
    await accountApi.toggle(props.platform, record.id)
    record.enabled = record.enabled === 1 ? 0 : 1
    Message.success(`账号已${record.enabled === 1 ? '启用' : '禁用'}`)
  } catch {
    Message.error('操作失败')
  }
}

const editAccount = (record) => {
  editingId.value = record.id
  form.username = record.username
  form.password = record.password || ''
  form.cookie = record.cookie || ''
  form.account_type = record.account_type || ''
  form.remark = record.remark || ''
  showModal.value = true
}

const saveAccount = async () => {
  if (!form.username) {
    Message.warning('请输入用户名')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await accountApi.update(props.platform, editingId.value, { ...form })
      Message.success('账号更新成功')
    } else {
      await accountApi.create(props.platform, { ...form })
      Message.success('账号创建成功')
    }
    showModal.value = false
    resetForm()
    loadData()
  } catch {
    Message.error('保存失败，请检查后端服务')
  } finally {
    saving.value = false
  }
}

const deleteAccount = (record) => {
  Modal.confirm({
    title: '删除账号',
    content: `确定要删除账号 ${record.username} 吗？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await accountApi.delete(props.platform, record.id)
        Message.success('账号已删除')
        loadData()
      } catch {
        Message.error('删除失败')
      }
    }
  })
}

const batchDelete = () => {
  Modal.confirm({
    title: '批量删除',
    content: `确定要删除选中的 ${selectedIds.value.length} 个账号吗？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        for (const id of selectedIds.value) {
          await accountApi.delete(props.platform, id)
        }
        Message.success(`已删除 ${selectedIds.value.length} 个账号`)
        selectedIds.value = []
        loadData()
      } catch {
        Message.error('批量删除失败')
      }
    }
  })
}

const resetForm = () => {
  editingId.value = null
  form.username = ''
  form.password = ''
  form.cookie = ''
  form.account_type = ''
  form.remark = ''
}

onMounted(() => loadData())
</script>

<style scoped>
.batch-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: var(--color-primary-light-1);
  border-radius: 4px;
  margin-bottom: 12px;
}
</style>
