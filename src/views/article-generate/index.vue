<template>
  <div class="article-generate-page">
    <a-card title="文章生成" :bordered="false">
      <a-form layout="vertical" :model="form">
        <!-- 第一步：选择标题和内容配置 -->
        <a-divider orientation="left">第一步：标题与内容配置</a-divider>
        <a-form-item label="文章标题" required>
          <a-textarea
            v-model="form.title"
            :auto-size="{ minRows: 2, maxRows: 4 }"
            placeholder="请输入文章标题，或从下方采集标题中选择"
          />
        </a-form-item>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="文章类型（选择后使用对应提示词）">
              <a-select v-model="form.article_type_id" style="width: 100%;" allow-clear placeholder="不选择则使用默认提示词">
                <a-option v-for="t in articleTypes" :key="t.id" :value="t.id">
                  {{ t.name }}
                </a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="付费类型">
              <a-radio-group v-model="form.article_type" type="button">
                <a-radio value="free">免费类型</a-radio>
                <a-radio value="paid">付费类型</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item label="附加要求（可选）">
          <a-textarea
            v-model="form.apply_prompt"
            :auto-size="{ minRows: 2, maxRows: 4 }"
            placeholder="可选的附加要求，会追加到提示词后面"
          />
        </a-form-item>

        <!-- 第二步：选择AI平台和账号 -->
        <a-divider orientation="left">第二步：选择AI平台与账号</a-divider>
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="AI平台" required>
              <a-select v-model="form.platform" style="width: 100%;" @change="onPlatformChange">
                <a-option value="zhipu">智谱AI</a-option>
                <a-option value="yuanbao">腾讯元宝</a-option>
                <a-option value="doubao">豆包</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="选择账号" required>
              <a-select v-model="form.account_id" style="width: 100%;" :placeholder="'请选择' + platformNames[form.platform] + '账号'">
                <a-option v-for="acc in accounts" :key="acc.id" :value="acc.account_id">
                  {{ acc.name }}（{{ acc.account_id }}）
                </a-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <a-form-item>
          <a-space>
            <a-button type="primary" :loading="generating" @click="generateArticle">
              {{ generating ? '生成中...' : '开始生成文章' }}
            </a-button>
            <a-button @click="resetForm">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>

      <!-- 生成进度 -->
      <a-alert v-if="taskStatus" :type="taskStatus.status === 'success' ? 'success' : taskStatus.status === 'failed' ? 'error' : 'info'" style="margin-bottom: 16px;">
        <template #title>
          <span v-if="taskStatus.status === 'running'">文章生成中，请耐心等待（浏览器自动化需要较长时间）...</span>
          <span v-else-if="taskStatus.status === 'success'">
            生成成功！
            <a-link @click="goToDetail(taskStatus.article_id)">查看文章详情 →</a-link>
          </span>
          <span v-else>生成失败：{{ taskStatus.message }}</span>
        </template>
      </a-alert>
    </a-card>

    <!-- 采集标题选择 -->
    <a-card title="从采集标题中选择" :bordered="false" style="margin-top: 16px;">
      <a-input-search
        v-model="titleKeyword"
        placeholder="搜索标题"
        style="margin-bottom: 12px; width: 300px;"
        @search="loadTitles"
      />
      <a-table :data="titles" :pagination="pagination" size="small" row-key="id" @page-change="onPageChange">
        <template #columns>
          <a-table-column title="ID" data-index="id" :width="60" />
          <a-table-column title="标题" data-index="title" />
          <a-table-column title="操作" :width="100">
            <template #cell="{ record }">
              <a-button size="mini" type="text" @click="selectTitle(record)">选择</a-button>
            </template>
          </a-table-column>
        </template>
      </a-table>
    </a-card>

    <!-- 最近生成的文章 -->
    <a-card title="最近生成的文章" :bordered="false" style="margin-top: 16px;">
      <a-table :data="recentArticles" :pagination="false" size="small" row-key="id">
        <template #columns>
          <a-table-column title="ID" data-index="id" :width="60" />
          <a-table-column title="标题" data-index="title" />
          <a-table-column title="平台" data-index="platform" :width="100">
            <template #cell="{ record }">{{ platformNames[record.platform] || record.platform }}</template>
          </a-table-column>
          <a-table-column title="类型" data-index="article_type" :width="80">
            <template #cell="{ record }">{{ record.article_type === 'paid' ? '付费' : '免费' }}</template>
          </a-table-column>
          <a-table-column title="生成时间" data-index="create_time" :width="160" />
          <a-table-column title="操作" :width="100">
            <template #cell="{ record }">
              <a-button size="mini" type="text" @click="goToDetail(record.id)">详情</a-button>
            </template>
          </a-table-column>
        </template>
      </a-table>
      <a-empty v-if="recentArticles.length === 0" description="暂无生成的文章" />
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { aiConfigApi, aiGenerateApi, spiderApi } from '@/api'

const router = useRouter()

const platformNames = {
  zhipu: '智谱AI',
  yuanbao: '腾讯元宝',
  doubao: '豆包'
}

// 表单
const form = ref({
  title: '',
  platform: 'zhipu',
  account_id: '',
  article_type_id: null,
  article_type: 'free',
  apply_prompt: ''
})

// 账号列表
const accounts = ref([])
const articleTypes = ref([])

// 采集标题
const titles = ref([])
const titleKeyword = ref('')
const pagination = ref({ current: 1, pageSize: 10, total: 0 })

// 最近文章
const recentArticles = ref([])

// 生成状态
const generating = ref(false)
const taskStatus = ref(null)
let statusTimer = null

// 平台切换
async function onPlatformChange() {
  form.value.account_id = ''
  await loadAccounts()
}

// 加载账号
async function loadAccounts() {
  try {
    const res = await aiConfigApi.getAccounts(form.value.platform)
    accounts.value = res.list || []
  } catch (e) {
    console.error('加载账号失败', e)
  }
}

// 加载文章类型
async function loadArticleTypes() {
  try {
    const res = await aiConfigApi.getArticleTypes()
    articleTypes.value = res.list || []
  } catch (e) {
    console.error('加载文章类型失败', e)
  }
}

// 加载设置
async function loadSettings() {
  try {
    const res = await aiConfigApi.getSettings()
    if (res.default_ai_platform) form.value.platform = res.default_ai_platform
    if (res.default_article_type) form.value.article_type = res.default_article_type
  } catch (e) {
    console.error('加载设置失败', e)
  }
}

// 加载采集标题
async function loadTitles() {
  try {
    const res = await spiderApi.list({
      page: pagination.value.current,
      pageSize: pagination.value.pageSize,
      keyword: titleKeyword.value
    })
    titles.value = res.list || []
    pagination.value.total = res.total || 0
  } catch (e) {
    console.error('加载标题失败', e)
  }
}

function onPageChange(page) {
  pagination.value.current = page
  loadTitles()
}

// 选择标题
function selectTitle(record) {
  form.value.title = record.title
  Message.success('已选择标题')
}

// 生成文章
async function generateArticle() {
  if (!form.value.title) {
    Message.warning('请输入文章标题')
    return
  }
  if (!form.value.platform) {
    Message.warning('请选择AI平台')
    return
  }
  if (!form.value.account_id) {
    Message.warning('请选择账号')
    return
  }

  generating.value = true
  taskStatus.value = { status: 'running', message: '' }

  try {
    const res = await aiGenerateApi.generateArticle({
      title: form.value.title,
      platform: form.value.platform,
      account_id: form.value.account_id,
      article_type_id: form.value.article_type_id,
      article_type: form.value.article_type,
      apply_prompt: form.value.apply_prompt
    })

    // 轮询任务状态
    const taskId = res.task_id
    statusTimer = setInterval(async () => {
      try {
        const status = await aiGenerateApi.getGenerateStatus(taskId)
        taskStatus.value = status
        if (status.status === 'success' || status.status === 'failed') {
          clearInterval(statusTimer)
          generating.value = false
          loadRecentArticles()
          if (status.status === 'success') {
            Message.success('文章生成成功！')
          } else {
            Message.error('文章生成失败：' + status.message)
          }
        }
      } catch (e) {
        console.error('查询任务状态失败', e)
      }
    }, 5000)

  } catch (e) {
    generating.value = false
    taskStatus.value = { status: 'failed', message: e.message || '生成失败' }
    Message.error('生成失败')
  }
}

// 重置表单
function resetForm() {
  form.value = {
    title: '',
    platform: 'zhipu',
    account_id: '',
    article_type_id: null,
    article_type: 'free',
    apply_prompt: '',
    chapter_count: 10
  }
  taskStatus.value = null
  loadAccounts()
}

// 跳转详情
function goToDetail(id) {
  router.push(`/article/detail/${id}`)
}

// 加载最近文章
async function loadRecentArticles() {
  try {
    const res = await aiGenerateApi.getArticles({ page: 1, pageSize: 10 })
    recentArticles.value = res.list || []
  } catch (e) {
    console.error('加载最近文章失败', e)
  }
}

onMounted(() => {
  loadSettings()
  loadAccounts()
  loadArticleTypes()
  loadTitles()
  loadRecentArticles()
})
</script>

<style scoped>
.article-generate-page {
  padding: 16px;
}
</style>
