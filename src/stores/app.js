import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

export const useAppStore = defineStore('app', () => {
  const darkMode = ref(localStorage.getItem('xiangcai_dark') === 'true')
  const sidebarCollapsed = ref(false)
  const apiBaseUrl = ref(localStorage.getItem('xiangcai_api') || 'http://127.0.0.1:8000')
  const autoRefresh = ref(true)
  const refreshInterval = ref(5000)

  const toggleDark = () => {
    darkMode.value = !darkMode.value
    localStorage.setItem('xiangcai_dark', darkMode.value)
    document.body.setAttribute('arco-theme', darkMode.value ? 'dark' : '')
  }

  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  const setApiBaseUrl = (url) => {
    apiBaseUrl.value = url
    localStorage.setItem('xiangcai_api', url)
  }

  watch(darkMode, (val) => {
    document.body.setAttribute('arco-theme', val ? 'dark' : '')
  }, { immediate: true })

  return {
    darkMode,
    sidebarCollapsed,
    apiBaseUrl,
    autoRefresh,
    refreshInterval,
    toggleDark,
    toggleSidebar,
    setApiBaseUrl
  }
})
