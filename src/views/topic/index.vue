<template>
  <PageCard>
    <template #title>话题管理</template>
    <template #extra>
      <a-button type="primary" @click="showModal = true">
        <template #icon><icon-plus /></template>新增话题
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
      :data="pagedTableData"
      :loading="loading"
      :pagination="paginationConfig"
      :bordered="{ cell: true }"
      row-key="id"
      @page-change="handlePageChange"
      @page-size-change="handlePageSizeChange"
    >
      <template #columns>
        <a-table-column :width="50" align="center">
          <template #title>
            <a-checkbox
              :model-value="isAllSelected"
              :indeterminate="isIndeterminate"
              @change="handleSelectAll"
            />
          </template>
          <template #cell="{ record }">
            <a-checkbox
              :model-value="selectedIds.includes(record.id)"
              @change="(checked) => handleRowSelect(record, checked)"
            />
          </template>
        </a-table-column>
        <a-table-column title="ID" data-index="id" :width="70" />
        <a-table-column title="话题名称" data-index="name" :width="200" />
        <a-table-column title="描述" data-index="description" :width="300" />
        <a-table-column title="文章数量" data-index="article_count" :width="100" />
        <a-table-column title="状态" data-index="enabled" :width="100">
          <template #cell="{ record }">
            <a-tag :color="record.enabled === 1 ? 'green' : 'gray'">{{ record.enabled === 1 ? '启用' : '禁用' }}</a-tag>
          </template>
        </a-table-column>
        <a-table-column title="创建时间" data-index="create_time" :width="170" />
        <a-table-column title="操作" :width="180" fixed="right">
          <template #cell="{ record }">
            <a-space>
              <a-button type="text" size="small" @click="toggleTopic(record)">{{ record.enabled === 1 ? '禁用' : '启用' }}</a-button>
              <a-button type="text" size="small" @click="editTopic(record)">编辑</a-button>
              <a-button type="text" size="small" status="danger" @click="deleteTopic(record)">删除</a-button>
            </a-space>
          </template>
        </a-table-column>
      </template>
    </a-table>

    <a-empty v-if="!loading && tableData.length === 0" description="暂无话题，点击右上角新增" />

    <!-- 新增/编辑弹窗 -->
    <a-modal v-model:visible="showModal" :title="editingId ? '编辑话题' : '新增话题'" @ok="saveTopic" confirm-loading="saving">
      <a-form :model="form" layout="vertical">
        <a-form-item label="话题名称" required>
          <a-input v-model="form.name" placeholder="请输入话题名称" />
        </a-form-item>
        <a-form-item label="描述">
          <a-textarea v-model="form.description" placeholder="请输入话题描述" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </PageCard>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconPlus, IconDelete } from '@arco-design/web-vue/es/icon'
import PageCard from '@/components/common/PageCard.vue'
import { topicApi } from '@/api'

const loading = ref(false)
const tableData = ref([])
const showModal = ref(false)
const saving = ref(false)
const editingId = ref(null)
const selectedIds = ref([])

// 分页相关
const currentPage = ref(1)
const pageSize = ref(15)
const pagedTableData = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return tableData.value.slice(start, end)
})
const paginationConfig = computed(() => ({
  current: currentPage.value,
  pageSize: pageSize.value,
  total: tableData.value.length,
  showTotal: true,
  showPageSize: true,
  pageSizeOptions: [10, 15, 20]
}))
const handlePageChange = (page) => { currentPage.value = page }
const handlePageSizeChange = (size) => { pageSize.value = size; currentPage.value = 1 }

const form = reactive({ name: '', description: '' })

const loadData = async () => {
  loading.value = true
  try {
    const res = await topicApi.list()
    tableData.value = res.data?.list || res.list || []
  } catch {
    Message.error('加载话题列表失败，请检查后端服务')
    tableData.value = []
  } finally {
    loading.value = false
  }
}

// 手动多选框相关计算属性（只针对当前页）
const isAllSelected = computed(() => {
  if (pagedTableData.value.length === 0) return false
  return pagedTableData.value.every(t => selectedIds.value.includes(t.id))
})
const isIndeterminate = computed(() => {
  if (pagedTableData.value.length === 0) return false
  const selectedCount = pagedTableData.value.filter(t => selectedIds.value.includes(t.id)).length
  return selectedCount > 0 && selectedCount < pagedTableData.value.length
})
const handleSelectAll = (checked) => {
  if (checked) {
    const currentIds = pagedTableData.value.map(t => t.id)
    selectedIds.value = [...new Set([...selectedIds.value, ...currentIds])]
  } else {
    const currentIds = new Set(pagedTableData.value.map(t => t.id))
    selectedIds.value = selectedIds.value.filter(id => !currentIds.has(id))
  }
}
const handleRowSelect = (record, checked) => {
  if (checked) {
    if (!selectedIds.value.includes(record.id)) {
      selectedIds.value.push(record.id)
    }
  } else {
    selectedIds.value = selectedIds.value.filter(id => id !== record.id)
  }
}

const toggleTopic = async (record) => {
  try {
    await topicApi.toggle(record.id)
    record.enabled = record.enabled === 1 ? 0 : 1
    Message.success(`话题已${record.enabled === 1 ? '启用' : '禁用'}`)
  } catch {
    Message.error('操作失败')
  }
}

const editTopic = (record) => {
  editingId.value = record.id
  form.name = record.name
  form.description = record.description || ''
  showModal.value = true
}

const saveTopic = async () => {
  if (!form.name) {
    Message.warning('请输入话题名称')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await topicApi.update(editingId.value, { ...form })
      Message.success('话题更新成功')
    } else {
      await topicApi.create({ ...form })
      Message.success('话题创建成功')
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

const deleteTopic = (record) => {
  Modal.confirm({
    title: '删除话题',
    content: `确定要删除话题「${record.name}」吗？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await topicApi.delete(record.id)
        Message.success('话题已删除')
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
    content: `确定要删除选中的 ${selectedIds.value.length} 个话题吗？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        for (const id of selectedIds.value) {
          await topicApi.delete(id)
        }
        Message.success(`已删除 ${selectedIds.value.length} 个话题`)
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
  form.name = ''
  form.description = ''
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
