import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useArticleStore = defineStore('article', () => {
  const list = ref([])
  const total = ref(0)
  const currentPage = ref(1)
  const pageSize = ref(15)
  const loading = ref(false)
  const selectedIds = ref([])
  const filter = ref({ status: undefined, topic: undefined, keyword: '' })

  const statusStats = computed(() => {
    const stats = {}
    list.value.forEach(a => {
      const s = a.generate_status
      stats[s] = (stats[s] || 0) + 1
    })
    return stats
  })

  const topicStats = computed(() => {
    const stats = {}
    list.value.forEach(a => {
      const t = a.topic_type || '未分类'
      stats[t] = (stats[t] || 0) + 1
    })
    return stats
  })

  const setList = (data, count) => {
    list.value = data
    total.value = count
  }

  const setPage = (page) => {
    currentPage.value = page
  }

  const toggleSelect = (id) => {
    const idx = selectedIds.value.indexOf(id)
    if (idx > -1) selectedIds.value.splice(idx, 1)
    else selectedIds.value.push(id)
  }

  const clearSelection = () => {
    selectedIds.value = []
  }

  const setFilter = (f) => {
    filter.value = { ...filter.value, ...f }
    currentPage.value = 1
  }

  const resetFilter = () => {
    filter.value = { status: undefined, topic: undefined, keyword: '' }
    currentPage.value = 1
  }

  return {
    list,
    total,
    currentPage,
    pageSize,
    loading,
    selectedIds,
    filter,
    statusStats,
    topicStats,
    setList,
    setPage,
    toggleSelect,
    clearSelection,
    setFilter,
    resetFilter
  }
})
