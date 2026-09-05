<template>
  <div class="logs-page">
    <a-row :gutter="16">
      <a-col :span="6" v-for="card in levelCards" :key="card.level">
        <StatCard
          :title="card.title"
          :value="card.value"
          :icon="card.icon"
          :color="card.color"
        />
      </a-col>
    </a-row>

    <PageCard style="margin-top:16px">
      <template #title>运行日志</template>
      <template #extra>
        <a-space>
          <a-select v-model="filterLevel" placeholder="级别筛选" allow-clear style="width:120px" @change="loadLogs">
            <a-option value="INFO">INFO</a-option>
            <a-option value="WARNING">WARNING</a-option>
            <a-option value="ERROR">ERROR</a-option>
          </a-select>
          <a-input v-model="searchKeyword" placeholder="搜索关键词" style="width:200px" @press-enter="searchLogs">
            <template #prefix><icon-search /></template>
          </a-input>
          <a-switch v-model="autoRefresh" checked-text="自动刷新" unchecked-text="暂停" />
          <a-button size="small" @click="loadLogs">
            <template #icon><icon-refresh /></template>刷新
          </a-button>
        </a-space>
      </template>

      <div class="log-container">
        <div v-for="(log, idx) in logs" :key="idx" class="log-line" :class="'level-' + log.level">
          <span class="log-time">{{ log.time }}</span>
          <a-tag :color="levelColor(log.level)" size="small" class="log-level">{{ log.level }}</a-tag>
          <span class="log-logger">{{ log.logger }}</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
        <a-empty v-if="!logs.length" description="暂无日志" />
      </div>

      <div class="log-pagination">
        <a-pagination
          :total="total"
          :current="currentPage"
          :page-size="pageSize"
          @change="handlePageChange"
          show-total
        />
      </div>
    </PageCard>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { IconSearch, IconRefresh, IconInfoCircle, IconExclamationCircle, IconCloseCircle, IconBug } from '@arco-design/web-vue/es/icon'
import StatCard from '@/components/common/StatCard.vue'
import PageCard from '@/components/common/PageCard.vue'

const logs = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(50)
const filterLevel = ref('')
const searchKeyword = ref('')
const autoRefresh = ref(true)
let refreshTimer = null

const levelCards = ref([
  { title: 'INFO', value: '0', icon: IconInfoCircle, color: '#165dff' },
  { title: 'WARNING', value: '0', icon: IconExclamationCircle, color: '#ff7d00' },
  { title: 'ERROR', value: '0', icon: IconCloseCircle, color: '#f53f3f' },
  { title: 'DEBUG', value: '0', icon: IconBug, color: '#722ed1' }
])

const levelColor = (level) => {
  const map = { INFO: 'blue', WARNING: 'orange', ERROR: 'red', DEBUG: 'purple', CRITICAL: 'magenta' }
  return map[level] || 'gray'
}

const loadLogs = async () => {
  // 模拟日志数据（实际应调用 /api/logs/list）
  const mockLogs = generateMockLogs()
  let filtered = mockLogs
  if (filterLevel.value) {
    filtered = filtered.filter(l => l.level === filterLevel.value)
  }
  if (searchKeyword.value) {
    filtered = filtered.filter(l => searchKeyword.value.toLowerCase() in l.message.toLowerCase())
  }
  total.value = filtered.length
  const start = (currentPage.value - 1) * pageSize.value
  logs.value = filtered.slice(start, start + pageSize.value)

  // 更新级别统计
  const stats = { INFO: 0, WARNING: 0, ERROR: 0, DEBUG: 0 }
  mockLogs.forEach(l => { stats[l.level] = (stats[l.level] || 0) + 1 })
  levelCards.value[0].value = stats.INFO
  levelCards.value[1].value = stats.WARNING
  levelCards.value[2].value = stats.ERROR
  levelCards.value[3].value = stats.DEBUG
}

const generateMockLogs = () => {
  const levels = ['INFO', 'INFO', 'INFO', 'WARNING', 'ERROR', 'DEBUG']
  const loggers = ['spider_service', 'command_service', 'article_api', 'account_api', 'main', 'export_helper']
  const messages = [
    '爬虫服务已启动',
    '采集到 3 条新标题，今日累计 45 条',
    '文章 #42 生成成功，1280字',
    '豆包账号 #1 图片生成中',
    '百家号草稿创建成功',
    '浏览器空闲15分钟，自动关闭',
    '账号登录已过期，请重新登录',
    '文章导出Word成功',
    '指令队列处理中，待执行 2 条',
    'IP伪装已启用，代理: 127.0.0.1:7890'
  ]
  const result = []
  const now = new Date()
  for (let i = 0; i < 80; i++) {
    const t = new Date(now.getTime() - i * 30000)
    result.push({
      time: t.toLocaleString('zh-CN'),
      level: levels[Math.floor(Math.random() * levels.length)],
      logger: loggers[Math.floor(Math.random() * loggers.length)],
      message: messages[Math.floor(Math.random() * messages.length)]
    })
  }
  return result
}

const searchLogs = () => {
  currentPage.value = 1
  loadLogs()
}

const handlePageChange = (page) => {
  currentPage.value = page
  loadLogs()
}

onMounted(() => {
  loadLogs()
  refreshTimer = setInterval(() => {
    if (autoRefresh.value) loadLogs()
  }, 5000)
})

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer)
})
</script>

<style scoped>
.log-container {
  max-height: 500px;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}
.log-line {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-bottom: 1px solid var(--color-fill-1);
}
.log-line:hover {
  background: var(--color-fill-2);
}
.log-line.level-ERROR {
  background: rgba(245, 63, 63, 0.05);
}
.log-line.level-WARNING {
  background: rgba(255, 125, 0, 0.05);
}
.log-time {
  color: var(--color-text-4);
  flex-shrink: 0;
  width: 170px;
}
.log-level {
  flex-shrink: 0;
  width: 70px;
  text-align: center;
}
.log-logger {
  color: var(--color-text-3);
  flex-shrink: 0;
  width: 120px;
}
.log-message {
  color: var(--color-text-2);
  word-break: break-all;
  flex: 1;
}
.log-pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
