import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useSpiderStore = defineStore('spider', () => {
  const running = ref(false)
  const todayCount = ref(0)
  const totalCount = ref(0)
  const usedCount = ref(0)
  const currentPage = ref(1)
  const log = ref([])

  const pendingCount = computed(() => totalCount.value - usedCount.value)

  const start = () => {
    running.value = true
    addLog('爬虫启动')
  }

  const stop = () => {
    running.value = false
    addLog('爬虫停止')
  }

  const addLog = (msg) => {
    const time = new Date().toLocaleTimeString()
    log.value.unshift({ time, msg })
    if (log.value.length > 100) log.value.pop()
  }

  const updateStats = (data) => {
    if (data.todayCount !== undefined) todayCount.value = data.todayCount
    if (data.totalCount !== undefined) totalCount.value = data.totalCount
    if (data.usedCount !== undefined) usedCount.value = data.usedCount
  }

  const reset = () => {
    running.value = false
    todayCount.value = 0
    log.value = []
  }

  return {
    running,
    todayCount,
    totalCount,
    usedCount,
    currentPage,
    log,
    pendingCount,
    start,
    stop,
    addLog,
    updateStats,
    reset
  }
})
