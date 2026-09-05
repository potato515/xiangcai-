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
import { ref, reactive, onMounted } from 'vue'
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

const handleSelectAll = (checked) => {
  selectedIds.value = checked ? tableData.value.map(t => t.id) : []
}

const handleSelect = (record, checked) => {
  if (checked) selectedIds.value.push(record.id)
  else selectedIds.value = selectedIds.value.filter(id => id !== record.id)
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
