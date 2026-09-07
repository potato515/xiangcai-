import request from '@/utils/request'

// ==================== 认证相关 ====================
export const authApi = {
  login: (data) => request.post('/auth/login', data),
  logout: (token) => request.post('/auth/logout', null, { params: { token } }),
  me: (token) => request.get('/auth/me', { params: { token } })
}

// ==================== 文章相关 ====================
export const articleApi = {
  list: (params) => request.get('/article/list', { params }),
  detail: (id) => request.get(`/article/detail/${id}`),
  create: (data) => request.post('/article/create', data),
  regenerate: (id) => request.post(`/article/regenerate/${id}`),
  batch: (data) => request.post('/article/batch', data),
  delete: (id) => request.delete(`/article/${id}`),
  export: (id) => request.get(`/article/export/${id}`),
  topics: () => request.get('/article/topics'),
  downloadTemplate: () => request.get('/article/download-template', { responseType: 'blob' }),
  batchUpload: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request.post('/article/batch-upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}

// ==================== 账号相关（5平台统一路由） ====================
export const accountApi = {
  list: (platform) => request.get(`/account/${platform}/list`),
  create: (platform, data) => request.post(`/account/${platform}/create`, data),
  update: (platform, id, data) => request.post(`/account/${platform}/update/${id}`, data),
  delete: (platform, id) => request.delete(`/account/${platform}/${id}`),
  login: (platform, id) => request.post(`/account/${platform}/login/${id}`),
  toggle: (platform, id) => request.post(`/account/${platform}/toggle/${id}`)
}

// ==================== 话题相关 ====================
export const topicApi = {
  list: () => request.get('/topic/list'),
  create: (data) => request.post('/topic/create', data),
  update: (id, data) => request.post(`/topic/update/${id}`, data),
  delete: (id) => request.delete(`/topic/${id}`),
  toggle: (id) => request.post(`/topic/toggle/${id}`)
}

// ==================== 标题采集（爬虫）相关 ====================
export const spiderApi = {
  list: (params) => request.get('/spider/list', { params }),
  start: () => request.post('/spider/start'),
  stop: () => request.post('/spider/stop'),
  status: (config = {}) => request.get('/spider/status', config),
  mark: (id) => request.post(`/spider/mark/${id}`),
  batchMark: (data) => request.post('/spider/batch-mark', data),
  export: () => request.get('/spider/export', { responseType: 'blob' }),
  delete: (id) => request.delete(`/spider/${id}`),
  batchDelete: (ids) => request.post('/spider/batch-delete', { ids }),
  rewrite: (data) => request.post('/spider/rewrite', data)
}

// ==================== 指令队列相关 ====================
export const commandApi = {
  list: (params) => request.get('/command/list', { params }),
  stats: () => request.get('/command/stats'),
  retry: (id) => request.post(`/command/retry/${id}`),
  clear: (clearAll = false) => request.post('/command/clear', null, { params: { clear_all: clearAll } }),
  delete: (id) => request.delete(`/command/${id}`)
}

// ==================== 系统设置相关 ====================
export const settingsApi = {
  getAll: () => request.get('/settings/all'),
  getCategory: (category) => request.get(`/settings/${category}`),
  saveCategory: (category, data) => request.post(`/settings/${category}`, data),
  getFormatting: () => request.get('/settings/formatting'),
  saveFormatting: (data) => request.post('/settings/formatting/save', data),
  getExport: () => request.get('/settings/export'),
  saveExport: (data) => request.post('/settings/export/save', data),
  getGenerate: () => request.get('/settings/generate'),
  saveGenerate: (data) => request.post('/settings/generate/save', data)
}

// ==================== 日志监控相关 ====================
export const logsApi = {
  list: (params) => request.get('/logs/list', { params }),
  levels: () => request.get('/logs/levels'),
  search: (params) => request.get('/logs/search', { params })
}

// ==================== 全局相关 ====================
export const globalApi = {
  health: () => request.get('/health'),
  status: () => request.get('/global/status')
}

// ==================== AI配置相关 ====================
export const aiConfigApi = {
  // 文章类型
  getArticleTypes: () => request.get('/ai-config/article-types'),
  createArticleType: (data) => request.post('/ai-config/article-types', data),
  updateArticleType: (id, data) => request.put(`/ai-config/article-types/${id}`, data),
  deleteArticleType: (id) => request.delete(`/ai-config/article-types/${id}`),
  // 提示词
  getPrompts: () => request.get('/ai-config/prompts'),
  updatePrompts: (data) => request.post('/ai-config/prompts', data),
  // AI账号
  getAccounts: (platform) => request.get(`/ai-config/accounts/${platform}`),
  createAccount: (platform, data) => request.post(`/ai-config/accounts/${platform}`, data),
  updateAccount: (platform, id, data) => request.put(`/ai-config/accounts/${platform}/${id}`, data),
  deleteAccount: (platform, id) => request.delete(`/ai-config/accounts/${platform}/${id}`),
  // 生成设置
  getSettings: () => request.get('/ai-config/settings'),
  updateSettings: (data) => request.post('/ai-config/settings', data),
  // 完整配置
  getAll: () => request.get('/ai-config/all')
}

// ==================== AI生成相关 ====================
export const aiGenerateApi = {
  // 生成文章
  generateArticle: (data) => request.post('/ai-generate/generate/article', data),
  getGenerateStatus: (taskId) => request.get(`/ai-generate/generate/status/${taskId}`),
  // 文章列表
  getArticles: (params) => request.get('/ai-generate/articles', { params }),
  getArticle: (id) => request.get(`/ai-generate/articles/${id}`),
  updateArticle: (id, data) => request.put(`/ai-generate/articles/${id}`, data),
  deleteArticle: (id) => request.delete(`/ai-generate/articles/${id}`),
  // 生成图片
  generateImages: (data) => request.post('/ai-generate/generate/images', data),
  regenerateAllImages: (data) => request.post('/ai-generate/generate/images/regenerate-all', data),
  selectImage: (data) => request.post('/ai-generate/images/select', data),
  getArticleImages: (articleId) => request.get(`/ai-generate/images/${articleId}`),
  // 排版与导出
  formatArticle: (articleId) => request.get(`/ai-generate/format/${articleId}`),
  exportArticle: (articleId) => request.post(`/ai-generate/export/${articleId}`),
  getFormatSettings: () => request.get('/ai-generate/format-settings'),
  saveFormatSettings: (data) => request.post('/ai-generate/format-settings', data),
  // 文章生成队列（待生成列表）
  getQueue: () => request.get('/ai-generate/queue'),
  addToQueue: (data) => request.post('/ai-generate/queue/add', data),
  batchAddToQueue: (data) => request.post('/ai-generate/queue/batch-add', data),
  updateQueueItem: (id, data) => request.put(`/ai-generate/queue/${id}`, data),
  batchUpdateQueue: (data) => request.post('/ai-generate/queue/batch-update', data),
  removeFromQueue: (id) => request.delete(`/ai-generate/queue/${id}`),
  batchDeleteQueue: (data) => request.post('/ai-generate/queue/batch-delete', data),
  clearQueue: () => request.post('/ai-generate/queue/clear'),
  resetQueueItem: (itemId) => request.post(`/ai-generate/queue/reset/${itemId}`),
  resetAllStuckItems: () => request.post('/ai-generate/queue/reset-all-stuck'),
  // 批量生成任务
  createBatchTask: (data) => request.post('/ai-generate/batch/create', data),
  startBatchTask: (batchId) => request.post(`/ai-generate/batch/start/${batchId}`),
  stopBatchTask: () => request.post('/ai-generate/batch/stop'),
  getBatchTaskStatus: (batchId) => request.get(`/ai-generate/batch/status/${batchId}`),
  getBatchTaskList: () => request.get('/ai-generate/batch/list'),
  getBatchEngineStatus: () => request.get('/ai-generate/batch/engine-status')
}
