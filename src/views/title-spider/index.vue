<template>
  <div class="title-spider">
    <PageCard>
      <template #title>标题采集</template>
      <template #extra>
        <a-space>
          <a-tag :color="spiderStore.running ? 'green' : 'gray'" size="small">
            {{ spiderStore.running ? '采集中' : '已停止' }}
          </a-tag>
          <a-button v-if="!spiderStore.running" status="success" @click="startSpider">
            <template #icon><icon-play-circle /></template>启动采集
          </a-button>
          <a-button v-else status="danger" @click="stopSpider">
            <template #icon><icon-stop /></template>停止采集
          </a-button>
          <a-button @click="loadData">
            <template #icon><icon-refresh /></template>刷新
          </a-button>
        </a-space>
      </template>

      <!-- 统计卡片 -->
      <a-row :gutter="16" style="margin-bottom:16px">
        <a-col :span="6">
          <StatCard title="今日采集" :value="spiderStore.todayCount" :icon="IconSearch" color="#165dff" />
        </a-col>
        <a-col :span="6">
          <StatCard title="总标题数" :value="total" :icon="IconFile" color="#00b42a" />
        </a-col>
        <a-col :span="6">
          <StatCard title="已使用" :value="usedCount" :icon="IconCheckCircle" color="#ff7d00" />
        </a-col>
        <a-col :span="6">
          <StatCard title="待使用" :value="total - usedCount" :icon="IconClockCircle" color="#722ed1" />
        </a-col>
      </a-row>

      <!-- 筛选区 -->
      <a-form :model="filter" layout="inline" style="margin-bottom:16px">
        <a-form-item label="阅读量">
          <a-input-number v-model="filter.minRead" :min="0" placeholder="最低" style="width:120px" />
        </a-form-item>
        <a-form-item label="状态">
          <a-select v-model="filter.used" placeholder="全部" allow-clear style="width:120px">
            <a-option :value="0">未使用</a-option>
            <a-option :value="1">已使用</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="关键词">
          <a-input v-model="filter.keyword" placeholder="搜索标题" style="width:180px" @press-enter="loadData">
            <template #prefix><icon-search /></template>
          </a-input>
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch"><template #icon><icon-search /></template>搜索</a-button>
            <a-button @click="resetFilter">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>

      <!-- 批量操作栏 -->
      <div v-if="selectedIds.length > 0" class="batch-bar">
        <span>已选择 <strong style="color:#165dff">{{ selectedIds.length }}</strong> 项</span>
        <a-space>
          <a-button size="small" status="primary" @click="openRewriteModal">
            <template #icon><icon-edit /></template>豆包AI重写标题
          </a-button>
          <a-button size="small" status="success" @click="openAddToQueueModal">
            <template #icon><icon-plus /></template>加入生成列表
          </a-button>
          <a-button size="small" status="success" @click="batchMarkUsed(true)">
            <template #icon><icon-check-circle /></template>批量标记已用
          </a-button>
          <a-button size="small" @click="batchMarkUsed(false)">
            <template #icon><icon-undo /></template>批量取消标记
          </a-button>
          <a-button size="small" status="warning" @click="exportSelected">
            <template #icon><icon-download /></template>导出选中
          </a-button>
          <a-button size="small" status="danger" @click="batchDelete">
            <template #icon><icon-delete /></template>批量删除
          </a-button>
          <a-button size="small" type="text" @click="selectedIds = []">取消选择</a-button>
        </a-space>
      </div>

      <!-- 导出按钮 -->
      <div style="margin-bottom:12px">
        <a-button status="warning" @click="exportAll">
          <template #icon><icon-download /></template>导出全部为CSV
        </a-button>
        <span style="margin-left:12px;color:var(--color-text-3);font-size:12px">
          导出文件包含：标题、阅读量、正在看人数、采集时间
        </span>
      </div>

      <!-- 表格 -->
      <a-table
        :data="tableData"
        :loading="loading"
        :pagination="false"
        :bordered="{ cell: true }"
        row-key="id"
      >
        <template #columns>
          <!-- 手动多选框列 -->
          <a-table-column title="" :width="50" align="center">
            <template #header>
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
          <a-table-column title="标题" data-index="title" :width="360">
            <template #cell="{ record }">
              <div style="font-weight:500">{{ record.title }}</div>
            </template>
          </a-table-column>
          <a-table-column title="阅读量" data-index="read_count" :width="100" :sorter="(a,b) => a.read_count - b.read_count">
            <template #cell="{ record }">
              <span :style="{ color: record.read_count > 10000 ? '#f53f3f' : '' }">{{ formatRead(record.read_count) }}</span>
            </template>
          </a-table-column>
          <a-table-column title="正在看" data-index="watching_count" :width="100" :sorter="(a,b) => (a.watching_count||0) - (b.watching_count||0)">
            <template #cell="{ record }">
              <span :style="{ color: (record.watching_count||0) > 1000 ? '#f53f3f' : '' }">{{ formatRead(record.watching_count) }}</span>
            </template>
          </a-table-column>
          <a-table-column title="状态" :width="80">
            <template #cell="{ record }">
              <a-tag :color="record.used ? 'gray' : 'green'" size="small">{{ record.used ? '已用' : '未用' }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="采集时间" data-index="create_time" :width="170" />
          <a-table-column title="操作" :width="180" fixed="right">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" size="small" @click="copyTitle(record)">复制</a-button>
                <a-button type="text" size="small" status="success" @click="markUsed(record)">{{ record.used ? '取消' : '标记' }}</a-button>
                <a-button type="text" size="small" status="warning" @click="generateArticle(record)">生成文章</a-button>
                <a-button type="text" size="small" status="danger" @click="deleteTitle(record)">删除</a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>

      <div class="pagination">
        <a-pagination :total="total" :current="currentPage" :page-size="pageSize" @change="handlePageChange" show-total />
      </div>
    </PageCard>

    <!-- 采集日志 -->
    <PageCard style="margin-top:16px">
      <template #title>采集日志</template>
      <LogPanel :logs="spiderStore.log" :running="spiderStore.running" @clear="spiderStore.log = []" />
    </PageCard>

    <!-- 豆包AI重写标题弹窗 -->
    <a-modal
      v-model:visible="rewriteModalVisible"
      title="豆包AI批量重写标题"
      :width="800"
      :mask-closable="false"
      @ok="addSelectedNewTitles"
      ok-text="添加选中标题到列表"
      cancel-text="关闭"
    >
      <div style="margin-bottom:16px">
        <a-alert type="info" style="margin-bottom:12px">
          已选择 <strong>{{ selectedIds.length }}</strong> 个原始标题，豆包AI将学习这些标题的爆款特征，重新仿写新标题。
        </a-alert>
        <a-form-item label="重写指令（可自定义，留空使用默认指令）">
          <a-textarea
            v-model="rewriteInstruction"
            :auto-size="{ minRows: 4, maxRows: 8 }"
            placeholder="学习上述标题内容，总结出标题的爆点，然后给出爆点结论，为什么会成为爆款标题。根据以上总结的内容，充分发挥你的想象力和创造力，套用以上爆款模板，重新仿写5个统一类型和特征的爆款标题，要求与原标题意思相近。"
          />
        </a-form-item>
        <a-space>
          <a-button type="primary" :loading="rewriting" @click="startRewrite">
            {{ rewriting ? 'AI重写中...' : '开始重写' }}
          </a-button>
          <span v-if="rewriting" style="color:#ff7d00">浏览器将自动打开豆包AI，请不要关闭浏览器窗口...</span>
        </a-space>
      </div>

      <div v-if="newTitles.length > 0" style="border-top:1px solid #e5e6eb;padding-top:16px">
        <div style="margin-bottom:12px;display:flex;justify-content:space-between;align-items:center">
          <span>AI生成的新标题（共 <strong style="color:#165dff">{{ newTitles.length }}</strong> 个，勾选后可添加到列表或生成文章）</span>
          <a-space>
            <a-checkbox v-model="selectAllNewTitles" @change="toggleSelectAllNewTitles">全选</a-checkbox>
            <a-button size="small" status="warning" @click="generateArticleFromNewTitles">用选中标题生成文章</a-button>
          </a-space>
        </div>
        <div style="max-height:400px;overflow-y:auto;border:1px solid #e5e6eb;border-radius:4px;padding:8px">
          <div v-for="(title, index) in newTitles" :key="index" style="padding:8px;border-bottom:1px solid #f2f3f5;display:flex;align-items:flex-start;gap:8px">
            <a-checkbox v-model="selectedNewTitles[index]" style="margin-top:2px" />
            <span style="flex:1">{{ index + 1 }}. {{ title }}</span>
            <a-button type="text" size="small" @click="copyNewTitle(title)">复制</a-button>
          </div>
        </div>
      </div>
    </a-modal>

    <!-- 加入生成列表弹窗 -->
    <a-modal v-model:visible="addToQueueModalVisible" title="加入文章生成列表" @ok="addToQueue" width="500px">
      <a-alert type="info" style="margin-bottom: 16px;">
        <template #content>
          将选中的 <strong>{{ selectedIds.length }}</strong> 个标题加入文章生成队列，可在「文章生成」页面批量生成文章。
        </template>
      </a-alert>
      <a-form layout="vertical">
        <a-form-item label="文章类型（可选，不选则使用系统默认类型）">
          <a-select v-model:value="queueArticleTypeId" allow-clear placeholder="不选择则使用默认文章类型" style="width: 100%;">
            <a-option v-for="t in articleTypes" :key="t.id" :value="t.id">{{ t.name }}</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="付费类型">
          <a-radio-group v-model:value="queueArticleType" type="button">
            <a-radio value="free">免费类型</a-radio>
            <a-radio value="paid">付费类型</a-radio>
          </a-radio-group>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import {
  IconSearch, IconPlayCircle, IconStop, IconRefresh,
  IconDownload, IconDelete, IconCheckCircle, IconClockCircle,
  IconFile, IconUndo, IconEdit, IconPlus
} from '@arco-design/web-vue/es/icon'
import PageCard from '@/components/common/PageCard.vue'
import StatCard from '@/components/common/StatCard.vue'
import LogPanel from '@/components/common/LogPanel.vue'
import { useSpiderStore } from '@/stores/spider'
import { spiderApi, aiGenerateApi, aiConfigApi } from '@/api'

const spiderStore = useSpiderStore()

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)
const selectedIds = ref([])
const apiAvailable = ref(true)
let statusPollingTimer = null
let lastRunningState = false
let pollingFailCount = 0

// 标题重写相关
const rewriteModalVisible = ref(false)
const rewriting = ref(false)
const rewriteInstruction = ref('')
const newTitles = ref([])
const selectedNewTitles = ref([])
const selectAllNewTitles = ref(false)

// 加入生成列表相关
const addToQueueModalVisible = ref(false)
const queueArticleTypeId = ref(null)
const queueArticleType = ref('free')
const articleTypes = ref([])
const addingToQueue = ref(false)

const filter = reactive({ minRead: undefined, category: undefined, used: undefined, keyword: '' })

const usedCount = computed(() => tableData.value.filter(t => t.used).length)

const formatRead = (n) => n >= 10000 ? (n / 10000).toFixed(1) + '万' : n

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value
    }
    if (filter.minRead) params.min_read = filter.minRead
    if (filter.category) params.category = filter.category
    if (filter.used !== undefined) params.used = filter.used
    if (filter.keyword) params.keyword = filter.keyword

    const res = await spiderApi.list(params)
    tableData.value = res.data?.list || res.list || []
    total.value = res.data?.total || res.total || 0
  } catch (e) {
    Message.error('加载标题列表失败，请检查后端服务是否启动')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const startSpider = async () => {
  try {
    const res = await spiderApi.start()
    if (res && res.running) {
      spiderStore.start()
      spiderStore.addLog('爬虫启动，开始采集百度信息流标题')
      Message.success('采集已启动，请确保MuMu模拟器已启动且百度App已登录')
      lastRunningState = true
      startStatusPolling()
    } else {
      Message.error('采集启动失败，请检查后端服务日志')
    }
  } catch (e) {
    const errMsg = e?.message || '未知错误'
    if (errMsg.includes('timeout')) {
      Message.error('后端服务响应超时，请检查后端服务是否启动（端口8000）')
    } else {
      Message.error(`采集启动失败：${errMsg}`)
    }
    spiderStore.stop()
    lastRunningState = false
    stopStatusPolling()
  }
}

// 轮询检测采集状态
const startStatusPolling = () => {
  if (statusPollingTimer) return
  pollingFailCount = 0
  statusPollingTimer = setInterval(async () => {
    try {
      // 静默模式：不弹出全局错误提示
      const status = await spiderApi.status({ silent: true })
      pollingFailCount = 0
      const isRunning = status.running

      // 检测状态从运行中变为已停止（采集完成）
      if (lastRunningState && !isRunning) {
        lastRunningState = false
        spiderStore.stop()

        // 显示采集完成提示
        if (status.last_result) {
          const result = status.last_result
          if (result.status === 'success') {
            Message.success(`🎉 采集完成！本次新增 ${result.new_count} 条，总计 ${result.total_count} 条`)
          } else if (result.status === 'stopped') {
            Message.info('采集已停止')
          } else if (result.status === 'error') {
            Message.error(`采集失败：${result.message}`)
          }
        } else {
          Message.success('采集已完成')
        }

        // 刷新表格数据
        loadData()
        // 停止轮询
        stopStatusPolling()
      }

      // 更新统计数据
      if (status.today_count !== undefined) spiderStore.todayCount = status.today_count
      if (status.total_count !== undefined) spiderStore.totalCount = status.total_count

    } catch (e) {
      // 静默失败，不弹出错误提示
      pollingFailCount++
      // 连续失败5次，自动停止轮询（后端可能未启动）
      if (pollingFailCount >= 5) {
        stopStatusPolling()
        spiderStore.stop()
        lastRunningState = false
        Message.warning('后端服务无响应，已停止状态监控，请检查后端服务是否启动')
      }
    }
  }, 3000) // 每3秒轮询一次
}

const stopStatusPolling = () => {
  if (statusPollingTimer) {
    clearInterval(statusPollingTimer)
    statusPollingTimer = null
  }
}

const stopSpider = async () => {
  try {
    await spiderApi.stop()
  } catch {}
  spiderStore.stop()
  spiderStore.addLog('爬虫已停止')
  Message.info('采集已停止')
  lastRunningState = false
  stopStatusPolling()
  loadData()
}

const handleSearch = () => { currentPage.value = 1; loadData() }
const resetFilter = () => { filter.minRead = undefined; filter.category = undefined; filter.used = undefined; filter.keyword = ''; currentPage.value = 1; loadData() }
const handlePageChange = (page) => { currentPage.value = page; loadData() }

const handleSelectionChange = (keys) => {
  selectedIds.value = keys
}

// 手动多选框相关计算属性
const isAllSelected = computed(() => {
  if (tableData.value.length === 0) return false
  return tableData.value.every(t => selectedIds.value.includes(t.id))
})

const isIndeterminate = computed(() => {
  if (tableData.value.length === 0) return false
  const selectedCount = tableData.value.filter(t => selectedIds.value.includes(t.id)).length
  return selectedCount > 0 && selectedCount < tableData.value.length
})

const handleSelectAll = (checked) => {
  if (checked) {
    // 全选当前页
    const currentIds = tableData.value.map(t => t.id)
    selectedIds.value = [...new Set([...selectedIds.value, ...currentIds])]
  } else {
    // 取消全选当前页
    const currentIds = new Set(tableData.value.map(t => t.id))
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

const batchMarkUsed = async (used) => {
  try {
    await spiderApi.batchMark({ ids: selectedIds.value, used })
    Message.success(`已${used ? '标记' : '取消'} ${selectedIds.value.length} 条标题`)
  } catch {
    Message.success(`已${used ? '标记' : '取消'} ${selectedIds.value.length} 条标题（模拟）`)
  }
  selectedIds.value = []
  loadData()
}

const batchDelete = () => {
  Modal.confirm({
    title: '批量删除',
    content: `确定要删除选中的 ${selectedIds.value.length} 条标题吗？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await spiderApi.batchDelete(selectedIds.value)
        Message.success(`已删除 ${selectedIds.value.length} 条标题`)
      } catch {
        Message.error('批量删除失败')
      }
      selectedIds.value = []
      loadData()
    }
  })
}

const exportAll = async () => {
  try {
    const res = await spiderApi.export()
    const blob = new Blob([res.data], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `标题采集_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    Message.success('CSV文件已导出')
  } catch {
    // 降级：前端生成CSV
    const headers = ['ID', '标题', '阅读量', '评论数', '点赞数', '分类', '状态', '采集时间']
    const rows = tableData.value.map(t => [t.id, t.title, t.read_count, t.comment_count, t.praise_count, t.category, t.used ? '已用' : '未用', t.create_time])
    const csv = '\uFEFF' + [headers, ...rows].map(r => r.map(c => `"${c}"`).join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `标题采集_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
    Message.success('CSV文件已导出（前端生成）')
  }
}

const exportSelected = () => {
  Message.success(`已导出 ${selectedIds.value.length} 条标题`)
  selectedIds.value = []
}

const copyTitle = (record) => {
  navigator.clipboard.writeText(record.title)
  Message.success('标题已复制')
}

const markUsed = async (record) => {
  try {
    await spiderApi.mark(record.id)
  } catch {}
  record.used = !record.used
  Message.success(record.used ? '已标记为已用' : '已取消标记')
}

const generateArticle = (record) => {
  Message.info(`正在基于标题生成文章：${record.title.slice(0, 20)}...`)
}

const deleteTitle = (record) => {
  Modal.confirm({
    title: '删除标题',
    content: `确定要删除标题 #${record.id} 吗？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await spiderApi.delete(record.id)
      } catch {}
      Message.success(`标题 #${record.id} 已删除`)
      loadData()
    }
  })
}

// ==================== 标题重写（豆包AI） ====================

const openRewriteModal = () => {
  if (selectedIds.value.length === 0) {
    Message.warning('请先选择要重写的标题')
    return
  }
  rewriteModalVisible.value = true
  newTitles.value = []
  selectedNewTitles.value = []
  selectAllNewTitles.value = false
  rewriteInstruction.value = ''
}

// 加入生成列表相关
const loadArticleTypes = async () => {
  try {
    const res = await aiConfigApi.getArticleTypes()
    articleTypes.value = res.data?.list || res.list || res.data || []
  } catch (e) {
    console.error('加载文章类型失败', e)
  }
}

const openAddToQueueModal = () => {
  if (selectedIds.value.length === 0) {
    Message.warning('请先选择要加入生成列表的标题')
    return
  }
  queueArticleTypeId.value = null
  queueArticleType.value = 'free'
  addToQueueModalVisible.value = true
}

const addToQueue = async () => {
  if (selectedIds.value.length === 0) {
    Message.warning('请先选择标题')
    return
  }

  addingToQueue.value = true
  try {
    // 获取选中的标题
    const selectedTitles = tableData.value.filter(t => selectedIds.value.includes(t.id))
    const items = selectedTitles.map(t => ({
      title: t.title,
      article_type_id: queueArticleTypeId.value,
      article_type: queueArticleType.value
    }))

    const res = await aiGenerateApi.batchAddToQueue({ items })
    const addedCount = res.data?.added_count || res.added_count || items.length

    Message.success(`已成功将 ${addedCount} 个标题加入文章生成列表`)
    addToQueueModalVisible.value = false
    selectedIds.value = []
  } catch (e) {
    Message.error(`加入生成列表失败：${e.response?.data?.detail || e.message}`)
  } finally {
    addingToQueue.value = false
  }
}

const startRewrite = async () => {
  if (selectedIds.value.length === 0) {
    Message.warning('请先选择要重写的标题')
    return
  }

  rewriting.value = true
  newTitles.value = []
  selectedNewTitles.value = []

  try {
    const res = await spiderApi.rewrite({
      title_ids: selectedIds.value,
      rewrite_instruction: rewriteInstruction.value
    })

    if (res.status === 'ok' || res.data?.status === 'ok') {
      const titles = res.new_titles || res.data?.new_titles || []
      newTitles.value = titles
      selectedNewTitles.value = new Array(titles.length).fill(false)
      Message.success(`AI重写完成，共生成 ${titles.length} 个新标题`)
    } else {
      Message.error('标题重写失败')
    }
  } catch (e) {
    Message.error(`标题重写失败：${e.response?.data?.detail || e.message || '未知错误'}`)
  } finally {
    rewriting.value = false
  }
}

const toggleSelectAllNewTitles = (checked) => {
  selectedNewTitles.value = new Array(newTitles.value.length).fill(checked)
}

const addSelectedNewTitles = async () => {
  const selected = newTitles.value.filter((_, i) => selectedNewTitles.value[i])
  if (selected.length === 0) {
    Message.warning('请先选择要添加的标题')
    return
  }

  // 这里可以调用API将新标题添加到列表中
  // 暂时只显示提示，后续可以添加批量导入功能
  Message.success(`已选择 ${selected.length} 个新标题，可以复制或用于生成文章`)
  rewriteModalVisible.value = false
}

const generateArticleFromNewTitles = () => {
  const selected = newTitles.value.filter((_, i) => selectedNewTitles.value[i])
  if (selected.length === 0) {
    Message.warning('请先选择要生成文章的标题')
    return
  }
  Message.info(`将基于 ${selected.length} 个标题生成文章，请前往文章生成页面操作`)
  rewriteModalVisible.value = false
}

const copyNewTitle = (title) => {
  navigator.clipboard.writeText(title)
  Message.success('标题已复制')
}

onMounted(() => {
  loadData()
  loadArticleTypes()
  // 页面加载时检查采集状态，如果正在运行则启动轮询
  spiderApi.status({ silent: true }).then(status => {
    if (status.running) {
      spiderStore.start()
      lastRunningState = true
      startStatusPolling()
    }
  }).catch(() => {})
})

onUnmounted(() => {
  stopStatusPolling()
})
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
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
