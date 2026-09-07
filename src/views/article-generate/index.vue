<template>
  <div class="article-generate-page">
    <!-- 批量任务进度 -->
    <a-card v-if="batchRunning || batchTask" title="批量生成任务进度" :bordered="false" style="margin-bottom: 16px;">
      <a-descriptions :column="3" bordered size="small">
        <a-descriptions-item label="任务状态">
          <a-tag :color="batchStatusColor">{{ batchStatusText }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="当前进度">
          {{ batchTask ? `${batchTask.current_index + 1}/${batchTask.total_count}` : '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="成功/失败">
          <span style="color: #00b42a;">{{ batchTask?.success_count || 0 }}</span>
          /
          <span style="color: #f53f3f;">{{ batchTask?.failed_count || 0 }}</span>
        </a-descriptions-item>
        <a-descriptions-item label="当前标题" :span="2">
          {{ batchTask?.current_title || '-' }}
        </a-descriptions-item>
        <a-descriptions-item label="操作">
          <a-button v-if="batchRunning" size="small" status="danger" @click="stopBatchTask">停止任务</a-button>
        </a-descriptions-item>
      </a-descriptions>
      <a-progress
        v-if="batchTask"
        :percent="batchTask.total_count ? Math.round(((batchTask.current_index + 1) / batchTask.total_count) * 100) : 0"
        style="margin-top: 12px;"
      />
    </a-card>

    <a-row :gutter="16">
      <!-- 左侧：待生成队列 -->
      <a-col :span="16">
        <a-card title="文章生成队列" :bordered="false">
          <template #extra>
            <a-space>
              <a-button size="small" @click="showAddModal = true">
                <template #icon><icon-plus /></template>手动添加
              </a-button>
              <a-button size="small" status="warning" @click="resetAllStuckItems">
                <template #icon><icon-reload /></template>重置卡住任务
              </a-button>
              <a-button size="small" status="danger" @click="clearQueue" :disabled="queue.length === 0">
                <template #icon><icon-delete /></template>清空队列
              </a-button>
            </a-space>
          </template>

          <!-- 批量操作栏 -->
          <div v-if="selectedQueueIds.length > 0" class="batch-bar">
            <span>已选择 <strong style="color:#165dff">{{ selectedQueueIds.length }}</strong> 项</span>
            <a-space>
              <a-select
                v-model="batchArticleTypeId"
                placeholder="批量设置文章类型"
                style="width: 180px;"
                allow-clear
                size="small"
              >
                <a-option v-for="t in articleTypes" :key="t.id" :value="t.id">{{ t.name }}</a-option>
              </a-select>
              <a-button size="small" type="primary" @click="batchUpdateType">应用类型</a-button>
              <a-button size="small" status="danger" @click="batchDeleteQueue">删除选中</a-button>
              <a-button size="small" type="text" @click="selectedQueueIds = []">取消选择</a-button>
            </a-space>
          </div>

          <a-table
            :data="pagedQueue"
            :loading="queueLoading"
            :pagination="paginationConfig"
            :bordered="{ cell: true }"
            row-key="id"
            size="small"
            @page-change="handlePageChange"
            @page-size-change="handlePageSizeChange"
          >
            <template #columns>
              <a-table-column :width="50" align="center">
                <template #title>
                  <a-checkbox
                    :model-value="isAllQueueSelected"
                    :indeterminate="isQueueIndeterminate"
                    @change="handleQueueSelectAll"
                  />
                </template>
                <template #cell="{ record }">
                  <a-checkbox
                    :model-value="selectedQueueIds.includes(record.id)"
                    @change="(checked) => handleQueueRowSelect(record, checked)"
                  />
                </template>
              </a-table-column>
              <a-table-column title="ID" data-index="id" :width="60" />
              <a-table-column title="标题" data-index="title">
                <template #cell="{ record }">
                  <a-input
                    v-if="editingId === record.id"
                    v-model:value="editingTitle"
                    size="small"
                    @blur="saveEdit(record)"
                    @keyup.enter="saveEdit(record)"
                    ref="editInputRef"
                  />
                  <span v-else @click="startEdit(record)" style="cursor: pointer;">{{ record.title }}</span>
                </template>
              </a-table-column>
              <a-table-column title="文章类型" :width="160">
                <template #cell="{ record }">
                  <a-select
                    v-model:value="record.article_type_id"
                    placeholder="默认类型"
                    style="width: 100%;"
                    allow-clear
                    size="small"
                    @change="updateQueueItem(record)"
                  >
                    <a-option v-for="t in articleTypes" :key="t.id" :value="t.id">{{ t.name }}</a-option>
                  </a-select>
                </template>
              </a-table-column>
              <a-table-column title="付费类型" :width="100">
                <template #cell="{ record }">
                  <a-tag :color="record.article_type === 'paid' ? 'orange' : 'green'" size="small">
                    {{ record.article_type === 'paid' ? '付费' : '免费' }}
                  </a-tag>
                </template>
              </a-table-column>
              <a-table-column title="状态" :width="80">
                <template #cell="{ record }">
                  <a-tag :color="queueStatusColor(record.status)" size="small">{{ queueStatusText(record.status) }}</a-tag>
                </template>
              </a-table-column>
              <a-table-column title="操作" :width="180" fixed="right">
                <template #cell="{ record }">
                  <a-space>
                    <a-button
                      v-if="record.status !== 'pending'"
                      type="text"
                      size="small"
                      status="warning"
                      @click="resetQueueItem(record)"
                    >
                      重新生成
                    </a-button>
                    <a-button type="text" size="small" status="danger" @click="removeQueueItem(record)">删除</a-button>
                  </a-space>
                </template>
              </a-table-column>
            </template>
          </a-table>

          <a-empty v-if="queue.length === 0" description="队列为空，请从标题采集页面添加或手动添加" />
        </a-card>
      </a-col>

      <!-- 右侧：批量任务配置 -->
      <a-col :span="8">
        <a-card title="批量生成配置" :bordered="false">
          <a-form layout="vertical" :model="batchForm">
            <a-form-item label="AI平台" required>
              <a-select v-model="batchForm.platform" style="width: 100%;" @change="onPlatformChange">
                <a-option value="zhipu">智谱AI</a-option>
                <a-option value="yuanbao">腾讯元宝</a-option>
                <a-option value="doubao">豆包</a-option>
              </a-select>
            </a-form-item>

            <a-form-item label="选择账号" required>
              <a-select v-model="batchForm.account_id" style="width: 100%;" :placeholder="'请选择' + platformNames[batchForm.platform] + '账号'">
                <a-option v-for="acc in accounts" :key="acc.id" :value="acc.account_id">
                  {{ acc.name }}（{{ acc.account_id }}）
                </a-option>
              </a-select>
            </a-form-item>

            <a-form-item label="生成配套图片">
              <a-switch v-model="batchForm.generate_images" />
              <span style="margin-left: 8px; font-size: 12px; color: var(--color-text-3);">为每篇文章的章节生成3张备选图</span>
            </a-form-item>

            <a-divider />

            <a-form-item label="待生成数量">
              <a-statistic :value="queue.length" suffix="篇" />
            </a-form-item>

            <a-form-item>
              <a-button
                type="primary"
                long
                :loading="batchStarting"
                :disabled="getGenerateItems().length === 0 || !batchForm.platform || !batchForm.account_id || batchRunning"
                @click="startBatchTask"
              >
                <template #icon><icon-play-circle /></template>
                {{ selectedQueueIds.length > 0 ? `启动批量生成（选中${selectedQueueIds.length}篇）` : `启动批量生成（全部${getGenerateItems().length}篇）` }}
              </a-button>
              <div v-if="selectedQueueIds.length > 0" style="text-align:center;font-size:12px;color:#165dff;margin-top:4px;">
                已选择 {{ selectedQueueIds.length }} 篇，将只生成选中的文章（取消选择则生成全部）
              </div>
            </a-form-item>

            <a-alert type="info" style="margin-top: 12px;">
              <template #content>
                <div style="font-size: 12px; line-height: 1.6;">
                  <p><strong>执行逻辑：</strong></p>
                  <p>• 按顺序逐个生成文章与配套图片</p>
                  <p>• 单篇失败不中断，自动继续下一篇</p>
                  <p>• 单篇最大超时时间：6分钟</p>
                  <p>• 未选择文章类型的使用系统默认类型</p>
                </div>
              </template>
            </a-alert>
          </a-form>
        </a-card>
      </a-col>
    </a-row>

    <!-- 手动添加弹窗 -->
    <a-modal v-model:visible="showAddModal" title="手动添加文章到队列" @ok="addManualItem">
      <a-form layout="vertical">
        <a-form-item label="文章标题" required>
          <a-textarea v-model:value="manualTitle" :auto-size="{ minRows: 2, maxRows: 4 }" placeholder="请输入文章标题" />
        </a-form-item>
        <a-form-item label="文章类型">
          <a-select v-model:value="manualArticleTypeId" allow-clear placeholder="不选择则使用默认类型" style="width: 100%;">
            <a-option v-for="t in articleTypes" :key="t.id" :value="t.id">{{ t.name }}</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="付费类型">
          <a-radio-group v-model:value="manualArticleType" type="button">
            <a-radio value="free">免费类型</a-radio>
            <a-radio value="paid">付费类型</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import {
  IconPlus, IconDelete, IconPlayCircle
} from '@arco-design/web-vue/es/icon'
import { aiGenerateApi, aiConfigApi } from '@/api'

const queue = ref([])
const queueLoading = ref(false)
const selectedQueueIds = ref([])
const batchArticleTypeId = ref(null)
const editingId = ref(null)
const editingTitle = ref('')
const editInputRef = ref(null)

// 分页相关变量
const currentPage = ref(1)
const pageSize = ref(10)
const pagedQueue = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return queue.value.slice(start, end)
})
const paginationConfig = computed(() => ({
  current: currentPage.value,
  pageSize: pageSize.value,
  total: queue.value.length,
  showTotal: true,
  showPageSize: true,
  pageSizeOptions: [10, 15, 20]
}))
const handlePageChange = (page) => {
  currentPage.value = page
}
const handlePageSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const showAddModal = ref(false)
const manualTitle = ref('')
const manualArticleTypeId = ref(null)
const manualArticleType = ref('free')

const articleTypes = ref([])
const accounts = ref([])
const platformNames = { zhipu: '智谱AI', yuanbao: '腾讯元宝', doubao: '豆包' }

const batchForm = ref({
  platform: 'zhipu',
  account_id: '',
  generate_images: true
})

const batchStarting = ref(false)
const batchRunning = ref(false)
const batchTask = ref(null)
let batchPollingTimer = null

const isAllQueueSelected = computed(() => {
  if (pagedQueue.value.length === 0) return false
  return pagedQueue.value.every(item => selectedQueueIds.value.includes(item.id))
})

const isQueueIndeterminate = computed(() => {
  if (pagedQueue.value.length === 0) return false
  const selectedCount = pagedQueue.value.filter(item => selectedQueueIds.value.includes(item.id)).length
  return selectedCount > 0 && selectedCount < pagedQueue.value.length
})

const batchStatusColor = computed(() => {
  const status = batchTask.value?.status
  if (status === 'running') return 'blue'
  if (status === 'success') return 'green'
  if (status === 'failed') return 'red'
  if (status === 'partial') return 'orange'
  return 'gray'
})

const batchStatusText = computed(() => {
  const status = batchTask.value?.status
  const map = { pending: '等待中', running: '运行中', success: '全部成功', failed: '全部失败', partial: '部分成功' }
  return map[status] || status || '-'
})

const loadQueue = async () => {
  queueLoading.value = true
  try {
    const res = await aiGenerateApi.getQueue()
    queue.value = res.data?.list || res.list || []
  } catch (e) {
    Message.error('加载生成队列失败')
  } finally {
    queueLoading.value = false
  }
}

const loadArticleTypes = async () => {
  try {
    const res = await aiConfigApi.getArticleTypes()
    articleTypes.value = res.data?.list || res.list || res.data || []
  } catch (e) {
    console.error('加载文章类型失败', e)
  }
}

const loadAccounts = async () => {
  try {
    const res = await aiConfigApi.getAccounts(batchForm.value.platform)
    accounts.value = res.data?.list || res.list || res.data || []
  } catch (e) {
    console.error('加载账号失败', e)
  }
}

const onPlatformChange = () => {
  batchForm.value.account_id = ''
  loadAccounts()
}

const handleQueueSelectAll = (checked) => {
  if (checked) {
    // 全选当前页
    const currentIds = pagedQueue.value.map(i => i.id)
    selectedQueueIds.value = [...new Set([...selectedQueueIds.value, ...currentIds])]
  } else {
    // 取消全选当前页
    const currentIds = new Set(pagedQueue.value.map(i => i.id))
    selectedQueueIds.value = selectedQueueIds.value.filter(id => !currentIds.has(id))
  }
}

const handleQueueRowSelect = (record, checked) => {
  if (checked) {
    if (!selectedQueueIds.value.includes(record.id)) {
      selectedQueueIds.value.push(record.id)
    }
  } else {
    selectedQueueIds.value = selectedQueueIds.value.filter(id => id !== record.id)
  }
}

const startEdit = (record) => {
  editingId.value = record.id
  editingTitle.value = record.title
}

const saveEdit = async (record) => {
  if (editingTitle.value && editingTitle.value !== record.title) {
    try {
      await aiGenerateApi.updateQueueItem(record.id, { title: editingTitle.value })
      record.title = editingTitle.value
      Message.success('标题已更新')
    } catch (e) {
      Message.error('更新标题失败')
    }
  }
  editingId.value = null
}

const updateQueueItem = async (record) => {
  try {
    // 确保类型转换为整数
    const typeId = record.article_type_id ? parseInt(record.article_type_id) : null
    await aiGenerateApi.updateQueueItem(parseInt(record.id), { article_type_id: typeId })
    Message.success('文章类型已更新')
  } catch (e) {
    Message.error(`更新文章类型失败：${e.response?.data?.detail || e.message}`)
  }
}

const removeQueueItem = (record) => {
  Modal.confirm({
    title: '移除确认',
    content: `确定要从队列中移除"${record.title.slice(0, 20)}..."吗？`,
    onOk: async () => {
      try {
        await aiGenerateApi.removeFromQueue(record.id)
        queue.value = queue.value.filter(i => i.id !== record.id)
        selectedQueueIds.value = selectedQueueIds.value.filter(id => id !== record.id)
        Message.success('已移除')
      } catch (e) {
        Message.error('移除失败')
      }
    }
  })
}

const batchUpdateType = async () => {
  if (selectedQueueIds.value.length === 0) {
    Message.warning('请先选择要修改的文章')
    return
  }
  if (!batchArticleTypeId.value) {
    Message.warning('请先选择文章类型')
    return
  }
  try {
    // 确保ID和类型ID都转换为整数
    const intIds = selectedQueueIds.value.map(id => parseInt(id))
    const intTypeId = parseInt(batchArticleTypeId.value)
    await aiGenerateApi.batchUpdateQueue({
      ids: intIds,
      article_type_id: intTypeId
    })
    // 重新加载队列数据，确保表格显示最新数据
    await loadQueue()
    Message.success(`已更新 ${selectedQueueIds.value.length} 项的文章类型`)
  } catch (e) {
    Message.error(`批量更新失败：${e.response?.data?.detail || e.message}`)
  }
}

const batchDeleteQueue = () => {
  Modal.confirm({
    title: '批量删除确认',
    content: `确定要删除选中的 ${selectedQueueIds.value.length} 项吗？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await aiGenerateApi.batchDeleteQueue({ ids: selectedQueueIds.value })
        queue.value = queue.value.filter(i => !selectedQueueIds.value.includes(i.id))
        selectedQueueIds.value = []
        Message.success('已删除')
      } catch (e) {
        Message.error('删除失败')
      }
    }
  })
}

const clearQueue = () => {
  Modal.confirm({
    title: '清空队列确认',
    content: '确定要清空整个生成队列吗？此操作不可恢复。',
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await aiGenerateApi.clearQueue()
        queue.value = []
        selectedQueueIds.value = []
        Message.success('队列已清空')
      } catch (e) {
        Message.error('清空失败')
      }
    }
  })
}

const resetQueueItem = (record) => {
  const statusText = {
    success: '已完成',
    running: '生成中',
    failed: '失败'
  }[record.status] || record.status

  Modal.confirm({
    title: '重新生成确认',
    content: `任务"${record.title.slice(0, 30)}..."当前状态为"${statusText}"，确定要重新生成吗？之前生成的内容会被清空。`,
    okButtonProps: { status: 'warning' },
    okText: '重新生成',
    onOk: async () => {
      try {
        await aiGenerateApi.resetQueueItem(record.id)
        // 更新本地状态
        const item = queue.value.find(i => i.id === record.id)
        if (item) {
          item.status = 'pending'
          item.error = ''
          item.article_content = ''
        }
        Message.success('已重置为待生成状态，请选择后重新开始生成')
      } catch (e) {
        Message.error('重置失败')
      }
    }
  })
}

const resetAllStuckItems = () => {
  const stuckCount = queue.value.filter(i => i.status === 'running').length
  if (stuckCount === 0) {
    Message.info('当前没有卡住的任务')
    return
  }
  Modal.confirm({
    title: '重置所有卡住任务',
    content: `检测到 ${stuckCount} 个状态为"生成中"的任务，确定要全部重置为"待生成"吗？`,
    okButtonProps: { status: 'warning' },
    onOk: async () => {
      try {
        const res = await aiGenerateApi.resetAllStuckItems()
        // 更新本地状态
        queue.value.forEach(item => {
          if (item.status === 'running') {
            item.status = 'pending'
            item.error = ''
          }
        })
        Message.success(`已重置 ${res.reset_count || stuckCount} 个卡住的任务`)
      } catch (e) {
        Message.error('重置失败')
      }
    }
  })
}

const addManualItem = async () => {
  if (!manualTitle.value.trim()) {
    Message.warning('请输入文章标题')
    return
  }
  try {
    await aiGenerateApi.addToQueue({
      title: manualTitle.value.trim(),
      article_type_id: manualArticleTypeId.value,
      article_type: manualArticleType.value,
      platform: batchForm.value.platform,
      account_id: batchForm.value.account_id
    })
    Message.success('已添加到队列')
    showAddModal.value = false
    manualTitle.value = ''
    manualArticleTypeId.value = null
    manualArticleType.value = 'free'
    loadQueue()
  } catch (e) {
    Message.error('添加失败')
  }
}

// 获取需要生成的文章列表
// 如果有选中的文章，只返回选中的待生成文章；如果没有选中的文章，返回所有待生成文章
const getGenerateItems = () => {
  const pendingItems = queue.value.filter(i => i.status === 'pending' || i.status === 'failed')
  if (selectedQueueIds.value.length > 0) {
    // 只返回选中的待生成文章
    return pendingItems.filter(i => selectedQueueIds.value.includes(i.id))
  }
  // 返回所有待生成文章
  return pendingItems
}

const startBatchTask = async () => {
  const generateItems = getGenerateItems()
  if (generateItems.length === 0) {
    Message.warning(selectedQueueIds.value.length > 0 ? '选中的文章中没有待生成的（全部已成功）' : '没有待生成的文章（全部已成功）')
    return
  }
  if (!batchForm.value.platform || !batchForm.value.account_id) {
    Message.warning('请选择AI平台和账号')
    return
  }

  batchStarting.value = true
  try {
    const itemIds = generateItems.map(i => i.id)

    const res = await aiGenerateApi.createBatchTask({
      item_ids: itemIds,
      platform: batchForm.value.platform,
      account_id: batchForm.value.account_id,
      generate_images: batchForm.value.generate_images
    })

    const batchId = res.data?.batch_id || res.batch_id
    await aiGenerateApi.startBatchTask(batchId)

    batchRunning.value = true
    Message.success(`批量任务已启动（${generateItems.length}篇）`)
    startBatchPolling(batchId)
  } catch (e) {
    Message.error(`启动失败：${e.response?.data?.detail || e.message}`)
  } finally {
    batchStarting.value = false
  }
}

const stopBatchTask = async () => {
  Modal.confirm({
    title: '停止批量任务',
    content: '确定要停止当前批量任务吗？正在生成的文章可能会中断。',
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await aiGenerateApi.stopBatchTask()
        batchRunning.value = false
        Message.success('停止信号已发送')
      } catch (e) {
        Message.error('停止失败')
      }
    }
  })
}

const startBatchPolling = (batchId) => {
  if (batchPollingTimer) {
    clearInterval(batchPollingTimer)
  }
  batchPollingTimer = setInterval(async () => {
    try {
      const res = await aiGenerateApi.getBatchTaskStatus(batchId)
      batchTask.value = res.data?.task || res.task
      const engine = res.data?.engine || res.engine

      if (engine?.is_running) {
        batchRunning.value = true
      } else {
        batchRunning.value = false
        clearInterval(batchPollingTimer)
        batchPollingTimer = null
        loadQueue()
        const status = batchTask.value?.status
        if (status === 'success') {
          Message.success('批量任务全部完成！')
        } else if (status === 'partial') {
          Message.warning(`批量任务部分完成，成功${batchTask.value?.success_count}篇，失败${batchTask.value?.failed_count}篇`)
        } else if (status === 'failed') {
          Message.error('批量任务全部失败')
        }
      }
    } catch (e) {
      console.error('轮询批量任务状态失败', e)
    }
  }, 5000)
}

const queueStatusColor = (status) => {
  const map = { pending: 'gray', running: 'blue', success: 'green', failed: 'red', skipped: 'orange' }
  return map[status] || 'gray'
}

const queueStatusText = (status) => {
  const map = { pending: '待生成', running: '生成中', success: '已成功', failed: '失败', skipped: '已跳过' }
  return map[status] || status
}

onMounted(() => {
  loadQueue()
  loadArticleTypes()
  loadAccounts()
})

onUnmounted(() => {
  if (batchPollingTimer) {
    clearInterval(batchPollingTimer)
  }
})
</script>

<style scoped>
.article-generate-page {
  padding: 0;
}

.batch-bar {
  background: #e8f3ff;
  padding: 8px 12px;
  border-radius: 4px;
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
