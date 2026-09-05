<template>
  <div class="command-page">
    <a-row :gutter="16">
      <a-col :span="6" v-for="card in statCards" :key="card.title">
        <StatCard
          :title="card.title"
          :value="card.value"
          :icon="card.icon"
          :color="card.color"
        />
      </a-col>
    </a-row>

    <PageCard style="margin-top:16px">
      <template #title>指令队列</template>
      <template #extra>
        <a-space>
          <a-tag :color="wsConnected ? 'green' : 'gray'" size="small">
            {{ wsConnected ? '实时连接' : '未连接' }}
          </a-tag>
          <a-button size="small" @click="refresh">
            <template #icon><icon-refresh /></template>刷新
          </a-button>
          <a-button size="small" status="danger" @click="clearAll">
            <template #icon><icon-delete /></template>清空指令
          </a-button>
        </a-space>
      </template>

      <a-table
        :data="commandList"
        :loading="loading"
        :pagination="false"
        :bordered="{ cell: true }"
        row-key="id"
      >
        <template #columns>
          <a-table-column title="ID" data-index="id" :width="70" />
          <a-table-column title="指令类型" data-index="type" :width="140">
            <template #cell="{ record }">
              <a-tag :color="typeColor(record.type)">{{ typeText(record.type) }}</a-tag>
            </template>
          </a-table-column>
          <a-table-column title="平台" data-index="platform" :width="100" />
          <a-table-column title="关联文章" data-index="article_id" :width="100" />
          <a-table-column title="状态" data-index="status" :width="100">
            <template #cell="{ record }">
              <StatusTag :status="record.status" type="command" />
            </template>
          </a-table-column>
          <a-table-column title="创建时间" data-index="create_time" :width="170" />
          <a-table-column title="执行时间" data-index="execute_time" :width="170" />
          <a-table-column title="结果" data-index="result" :width="200">
            <template #cell="{ record }">
              <span :style="{ color: record.status === 3 ? '#f53f3f' : '' }">
                {{ record.result || '-' }}
              </span>
            </template>
          </a-table-column>
          <a-table-column title="操作" :width="100" fixed="right">
            <template #cell="{ record }">
              <a-button v-if="record.status === 0" type="text" size="small" @click="retry(record)">重试</a-button>
              <a-button v-else type="text" size="small" @click="viewDetail(record)">详情</a-button>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </PageCard>

    <PageCard style="margin-top:16px">
      <template #title>实时日志</template>
      <LogPanel :logs="logs" :running="wsConnected" @clear="logs = []" />
    </PageCard>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { Message, Modal } from '@arco-design/web-vue'
import { IconRefresh, IconDelete, IconClockCircle, IconPlayCircle, IconCheckCircle, IconCloseCircle } from '@arco-design/web-vue/es/icon'
import StatCard from '@/components/common/StatCard.vue'
import PageCard from '@/components/common/PageCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import LogPanel from '@/components/common/LogPanel.vue'
import { useWebSocket } from '@/composables/useWebSocket'

const loading = ref(false)
const commandList = ref([])
const logs = ref([])

const statCards = ref([
  { title: '待执行', value: '3', icon: IconClockCircle, color: '#ff7d00' },
  { title: '执行中', value: '1', icon: IconPlayCircle, color: '#165dff' },
  { title: '已完成', value: '156', icon: IconCheckCircle, color: '#00b42a' },
  { title: '失败', value: '2', icon: IconCloseCircle, color: '#f53f3f' }
])

const { connected: wsConnected, connect, disconnect, send } = useWebSocket('ws://127.0.0.1:8000/ws/command', {
  autoReconnect: true,
  onMessage: (data) => {
    if (data.type === 'log') {
      logs.value.unshift({ time: new Date().toLocaleTimeString(), msg: data.msg, level: data.level || 'info' })
      if (logs.value.length > 100) logs.value.pop()
    } else if (data.type === 'command_update') {
      const idx = commandList.value.findIndex(c => c.id === data.id)
      if (idx > -1) commandList.value[idx] = { ...commandList.value[idx], ...data }
    }
  },
  onOpen: () => {
    logs.value.unshift({ time: new Date().toLocaleTimeString(), msg: 'WebSocket 连接成功', level: 'success' })
  },
  onClose: () => {
    logs.value.unshift({ time: new Date().toLocaleTimeString(), msg: 'WebSocket 连接断开，正在重连...', level: 'warn' })
  }
})

const typeMap = {
  trigger_login: { text: '触发登录', color: 'blue' },
  scan_qrcode: { text: '扫描二维码', color: 'cyan' },
  message_code: { text: '短信验证码', color: 'orange' },
  generate_article: { text: '生成文章', color: 'green' },
  generate_image: { text: '生成图片', color: 'purple' },
  baijiahao_draft: { text: '百家号草稿', color: 'red' }
}

const typeText = (t) => typeMap[t]?.text || t
const typeColor = (t) => typeMap[t]?.color || 'gray'

const loadMockData = () => {
  loading.value = true
  setTimeout(() => {
    commandList.value = [
      { id: 101, type: 'generate_article', platform: '仰度AI', article_id: 45, status: 1, create_time: '2026-09-04 14:30:12', execute_time: '2026-09-04 14:30:15', result: '正在生成...' },
      { id: 100, type: 'generate_image', platform: '豆包', article_id: 44, status: 0, create_time: '2026-09-04 14:28:45', execute_time: '-', result: '-' },
      { id: 99, type: 'baijiahao_draft', platform: '百家号', article_id: 43, status: 0, create_time: '2026-09-04 14:25:30', execute_time: '-', result: '-' },
      { id: 98, type: 'generate_article', platform: '仰度AI', article_id: 42, status: 2, create_time: '2026-09-04 14:20:10', execute_time: '2026-09-04 14:20:15', result: '文章生成成功，1280字' },
      { id: 97, type: 'generate_image', platform: '豆包', article_id: 42, status: 2, create_time: '2026-09-04 14:22:00', execute_time: '2026-09-04 14:22:05', result: '5张图片生成成功' },
      { id: 96, type: 'baijiahao_draft', platform: '百家号', article_id: 41, status: 2, create_time: '2026-09-04 14:15:00', execute_time: '2026-09-04 14:15:10', result: '草稿创建成功' },
      { id: 95, type: 'generate_article', platform: '仰度AI', article_id: 40, status: 3, create_time: '2026-09-04 14:10:00', execute_time: '2026-09-04 14:10:05', result: '账号登录已过期，请重新登录' },
      { id: 94, type: 'trigger_login', platform: '百家号', article_id: '-', status: 2, create_time: '2026-09-04 14:05:00', execute_time: '2026-09-04 14:05:10', result: '登录成功' }
    ]
    loading.value = false
  }, 500)
}

const refresh = () => {
  loadMockData()
  Message.success('已刷新')
}

const clearAll = () => {
  Modal.confirm({
    title: '确认清空',
    content: '确定要清空所有已完成和失败的指令吗？待执行和执行中的指令不会被清除。',
    onOk: () => {
      commandList.value = commandList.value.filter(c => c.status === 0 || c.status === 1)
      Message.success('已清空历史指令')
    }
  })
}

const retry = (record) => {
  Message.info(`已重新提交指令 #${record.id}`)
  record.status = 0
  record.result = '-'
}

const viewDetail = (record) => {
  Modal.info({
    title: `指令 #${record.id} 详情`,
    content: `类型: ${typeText(record.type)}\n平台: ${record.platform}\n状态: ${record.status}\n结果: ${record.result || '无'}`
  })
}

onMounted(() => {
  loadMockData()
  connect()
})

onUnmounted(() => {
  disconnect()
})
</script>
