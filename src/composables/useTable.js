import { ref, reactive } from 'vue'

export function useTable(fetchFn, options = {}) {
  const {
    defaultPage = 1,
    defaultPageSize = 15,
    immediate = true
  } = options

  const data = ref([])
  const total = ref(0)
  const loading = ref(false)
  const currentPage = ref(defaultPage)
  const pageSize = ref(defaultPageSize)
  const filter = reactive({})
  const selectedKeys = ref([])

  const loadData = async () => {
    loading.value = true
    try {
      const res = await fetchFn({
        page: currentPage.value,
        pageSize: pageSize.value,
        ...filter
      })
      data.value = res.list || res.data || res.articles || []
      total.value = res.total || res.count || 0
    } catch (e) {
      console.error('Table load error:', e)
    } finally {
      loading.value = false
    }
  }

  const handlePageChange = (page) => {
    currentPage.value = page
    loadData()
  }

  const handlePageSizeChange = (size) => {
    pageSize.value = size
    currentPage.value = 1
    loadData()
  }

  const handleSearch = () => {
    currentPage.value = 1
    loadData()
  }

  const handleReset = () => {
    Object.keys(filter).forEach(k => delete filter[k])
    currentPage.value = 1
    loadData()
  }

  const toggleSelect = (key) => {
    const idx = selectedKeys.value.indexOf(key)
    if (idx > -1) selectedKeys.value.splice(idx, 1)
    else selectedKeys.value.push(key)
  }

  const clearSelection = () => {
    selectedKeys.value = []
  }

  const refresh = () => {
    loadData()
  }

  if (immediate) {
    loadData()
  }

  return {
    data,
    total,
    loading,
    currentPage,
    pageSize,
    filter,
    selectedKeys,
    loadData,
    handlePageChange,
    handlePageSizeChange,
    handleSearch,
    handleReset,
    toggleSelect,
    clearSelection,
    refresh
  }
}
