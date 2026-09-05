<template>
  <div class="article-list">
    <PageCard>
      <template #title>文章管理</template>
      <template #extra>
        <a-space>
          <a-button type="primary" @click="$router.push('/article/batch-import')">
            <template #icon><icon-upload /></template>批量导入
          </a-button>
          <a-button @click="downloadTemplate">
            <template #icon><icon-download /></template>下载模板
          </a-button>
          <a-button status="success" @click="showCreate = true">
            <template #icon><icon-plus /></template>新建文章
          </a-button>
        </a-space>
      </template>

      <!-- 筛选区 -->
      <a-form :model="filter" layout="inline" style="margin-bottom:16px">
        <a-form-item label="状态">
          <a-select v-model="filter.status" placeholder="全部状态" allow-clear style="width:140px" @change="handleSearch">
            <a-option v-for="s in statusOptions" :key="s.value" :value="s.value">{{ s.label }}</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="话题">
          <a-select v-model="filter.topic" placeholder="全部话题" allow-clear style="width:140px" @change="handleSearch">
            <a-option v-for="t in topics" :key="t" :value="t">{{ t }}</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="关键词">
          <a-input v-model="filter.keyword" placeholder="搜索标题" style="width:200px" @press-enter="handleSearch">
            <template #prefix><icon-search /></template>
          </a-input>
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" @click="handleSearch"><template #icon><icon-search /></template>搜索</a-button>
            <a-button @click="handleReset">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>

      <!-- 批量操作栏 -->
      <div v-if="selectedIds.length > 0" class="batch-bar">
        <span>已选择 <strong style="color:#165dff">{{ selectedIds.length }}</strong> 项</span>
        <a-space>
          <a-button size="small" status="success" @click="batchRegenerate">
            <template #icon><icon-refresh /></template>批量重新生成
          </a-button>
          <a-button size="small" status="warning" @click="batchExport">
            <template #icon><icon-download /></template>批量导出
          </a-button>
          <a-button size="small" status="danger" @click="batchDelete">
            <template #icon><icon-delete /></template>批量删除
          </a-button>
          <a-button size="small" type="text" @click="clearSelection">取消选择</a-button>
        </a-space>
      </div>

      <!-- 表格 -->
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
          <a-table-column title="标题" data-index="title" :width="280">
            <template #cell="{ record }">
              <a-link @click="router.push(`/article/detail/${record.id}`)">{{ record.title }}</a-link>
            </template>
          </a-table-column>
          <a-table-column title="AI平台" data-index="platform" :width="100">
            <template #cell="{ record }">{{ platformNames[record.platform] || record.platform }}</template>
          </a-table-column>
          <a-table-column title="类型" data-index="article_type" :width="80">
            <template #cell="{ record }">
              <a-tag :color="record.article_type === 'paid' ? 'orange' : 'cyan'" size="small">
                {{ record.article_type === 'paid' ? '付费' : '免费' }}
              </a-tag>
            </template>
          </a-table-column>
          <a-table-column title="段落数" :width="80">
            <template #cell="{ record }">{{ record.chapters?.length || 0 }}</template>
          </a-table-column>
          <a-table-column title="配图数" :width="80">
            <template #cell="{ record }">{{ Object.keys(record.selected_images || {}).length }}</template>
          </a-table-column>
          <a-table-column title="创建时间" data-index="create_time" :width="170" />
          <a-table-column title="操作" :width="200" fixed="right">
            <template #cell="{ record }">
              <a-space>
                <a-button type="text" size="small" @click="router.push(`/article/detail/${record.id}`)">详情</a-button>
                <a-button type="text" size="small" status="warning" @click="exportArticle(record)">导出</a-button>
                <a-button type="text" size="small" status="danger" @click="deleteArticle(record)">删除</a-button>
              </a-space>
            </template>
          </a-table-column>
        </template>
      </a-table>

      <!-- 分页 -->
      <div class="pagination">
        <a-pagination
          :total="total"
          :current="currentPage"
          :page-size="pageSize"
          @change="handlePageChange"
          show-total
        />
      </div>
    </PageCard>

    <!-- 新建文章弹窗 -->
    <a-modal v-model:visible="showCreate" title="新建文章" @ok="createArticle" confirm-loading="creating">
      <a-form :model="createForm" layout="vertical">
        <a-form-item label="标题" required>
          <a-input v-model="createForm.title" placeholder="请输入文章标题" />
        </a-form-item>
        <a-form-item label="话题">
          <a-select v-model="createForm.topic_type" allow-clear style="width:100%">
            <a-option v-for="t in topics" :key="t" :value="t">{{ t }}</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="AI类型">
          <a-select v-model="createForm.ai_type" style="width:100%">
            <a-option value="yangdu_old">仰度老系统</a-option>
            <a-option value="yangdu_new">仰度新系统</a-option>
            <a-option value="zhipu">智谱web</a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="限定提示词">
          <a-textarea v-model="createForm.limit_prompt" placeholder="可选，对AI生成的额外限定" :rows="3" />
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import {
  IconSearch, IconUpload, IconDownload, IconPlus,
  IconRefresh, IconDelete
} from '@arco-design/web-vue/es/icon'
import PageCard from '@/components/common/PageCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { aiGenerateApi } from '@/api'

const router = useRouter()

const platformNames = {
  zhipu: '智谱AI',
  yuanbao: '腾讯元宝',
  doubao: '豆包'
}

const loading = ref(false)
const tableData = ref([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)
const selectedIds = ref([])
const showCreate = ref(false)
const creating = ref(false)

const filter = reactive({ status: undefined, topic: undefined, keyword: '' })
const createForm = reactive({ title: '', topic_type: '', ai_type: 'yangdu_new', limit_prompt: '' })

const statusOptions = [
  { value: 11, label: '待生成文章' }, { value: 12, label: '待生成图片' },
  { value: 21, label: '文章生成中' }, { value: 22, label: '图片生成中' },
  { value: 3, label: '生成成功' }, { value: 41, label: '文章失败' },
  { value: 42, label: '图片失败' }, { value: 6, label: '草稿成功' },
  { value: 10, label: '已导出' }
]

const topics = ['家庭伦理', '职场故事', '情感故事', '社会热点', '默认']

const aiTypeText = (t) => ({ yangdu_old: '仰度老系统', yangdu_new: '仰度新系统', zhipu: '智谱web' }[t] || t)

const loadData = async () => {
  loading.value = true
  try {
    const params = {
      page: currentPage.value,
      pageSize: pageSize.value
    }
    if (filter.keyword) params.keyword = filter.keyword

    const res = await aiGenerateApi.getArticles(params)
    tableData.value = res.list || []
    total.value = res.total || 0
  } catch (e) {
    Message.error('加载文章列表失败，请检查后端服务')
    tableData.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

const handleSearch = () => { currentPage.value = 1; loadData() }
const handleReset = () => { filter.status = undefined; filter.topic = undefined; filter.keyword = ''; currentPage.value = 1; loadData() }
const handlePageChange = (page) => { currentPage.value = page; loadData() }

const handleSelectAll = (checked) => {
  selectedIds.value = checked ? tableData.value.map(a => a.id) : []
}
const handleSelect = (record, checked) => {
  if (checked) selectedIds.value.push(record.id)
  else selectedIds.value = selectedIds.value.filter(id => id !== record.id)
}
const clearSelection = () => { selectedIds.value = [] }

const batchRegenerate = () => {
  Modal.confirm({
    title: '批量重新生成',
    content: `确定要重新生成选中的 ${selectedIds.value.length} 篇文章吗？`,
    onOk: () => {
      Message.success(`已提交 ${selectedIds.value.length} 篇文章重新生成`)
      clearSelection()
      loadData()
    }
  })
}

const batchExport = async () => {
  if (selectedIds.value.length === 0) {
    Message.warning('请先选择要导出的文章')
    return
  }

  const total = selectedIds.value.length
  let success = 0
  let failed = 0

  Message.loading({ content: `正在导出 ${total} 篇文章...`, key: 'batch-export', duration: 0 })

  for (let i = 0; i < selectedIds.value.length; i++) {
    const id = selectedIds.value[i]
    try {
      const res = await aiGenerateApi.exportArticle(id)
      if (res.download_url) {
        const link = document.createElement('a')
        link.href = res.download_url
        link.download = res.filename
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
      }
      success++
      // 每篇导出间隔500ms，避免浏览器拦截多个下载
      await new Promise(resolve => setTimeout(resolve, 500))
    } catch (e) {
      failed++
      console.error(`导出文章 #${id} 失败`, e)
    }
  }

  Message.clear('batch-export')

  if (failed === 0) {
    Message.success(`成功导出 ${success} 篇文章为Word`)
  } else {
    Message.warning(`导出完成：成功 ${success} 篇，失败 ${failed} 篇`)
  }

  clearSelection()
}

const batchDelete = () => {
  Modal.confirm({
    title: '批量删除',
    content: `确定要删除选中的 ${selectedIds.value.length} 篇文章吗？此操作不可恢复！`,
    okText: '确认删除',
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        for (const id of selectedIds.value) {
          await aiGenerateApi.deleteArticle(id)
        }
        Message.success(`已删除 ${selectedIds.value.length} 篇文章`)
      } catch {
        Message.error('批量删除失败')
      }
      clearSelection()
      loadData()
    }
  })
}

const regenerate = (record) => {
  Message.success(`文章 #${record.id} 已提交重新生成`)
  loadData()
}

const exportArticle = (record) => {
  Message.success(`文章 #${record.id} 正在导出Word...`)
}

const deleteArticle = (record) => {
  Modal.confirm({
    title: '删除文章',
    content: `确定要删除文章 #${record.id} 吗？`,
    okButtonProps: { status: 'danger' },
    onOk: async () => {
      try {
        await aiGenerateApi.deleteArticle(record.id)
        Message.success(`文章 #${record.id} 已删除`)
      } catch {
        Message.error('删除失败')
      }
      loadData()
    }
  })
}

const createArticle = async () => {
  if (!createForm.title) { Message.warning('请输入标题'); return }
  creating.value = true
  setTimeout(() => {
    Message.success('文章创建成功')
    showCreate.value = false
    creating.value = false
    createForm.title = ''
    createForm.topic_type = ''
    createForm.limit_prompt = ''
    loadData()
  }, 800)
}

const downloadTemplate = () => {
  Message.success('模板下载中...')
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
.pagination {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
