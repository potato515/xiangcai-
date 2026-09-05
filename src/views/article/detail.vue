<template>
  <div class="article-detail">
    <a-page-header :title="article.title || '文章详情'" @back="$router.back()">
      <template #sub-title>
        <a-space>
          <a-tag color="blue">{{ platformNames[article.platform] || article.platform }}</a-tag>
          <a-tag :color="article.article_type === 'paid' ? 'orange' : 'cyan'">
            {{ article.article_type === 'paid' ? '付费类型' : '免费类型' }}
          </a-tag>
          <a-tag color="green">{{ article.chapters?.length || 0 }} 个段落</a-tag>
        </a-space>
      </template>
      <template #extra>
        <a-space>
          <a-button type="primary" @click="showImageGenerateModal">
            <template #icon><icon-image /></template>
            生成配图
          </a-button>
          <a-button status="success" @click="autoFormat">
            <template #icon><icon-edit /></template>
            自动排版
          </a-button>
          <a-button @click="copyArticleContent">
            <template #icon><icon-copy /></template>
            复制内容
          </a-button>
          <a-button @click="exportWord">
            <template #icon><icon-download /></template>
            导出Word
          </a-button>
        </a-space>
      </template>
    </a-page-header>

    <a-row :gutter="16" style="margin-top: 16px">
      <!-- 左侧：段落列表 -->
      <a-col :span="14">
        <a-card title="文章段落（勾选需要配图的段落）" class="chapters-card">
          <div class="chapter-list">
            <div
              v-for="chapter in article.chapters"
              :key="chapter.num"
              class="chapter-item"
              :class="{ selected: selectedChapters.includes(chapter.num), has_image: article.selected_images?.[chapter.num] }"
            >
              <div class="chapter-header">
                <a-checkbox v-model="selectedChapters" :value="chapter.num">
                  <span class="chapter-num">{{ chapter.num }}</span>
                  <span class="chapter-title">{{ chapter.title }}</span>
                </a-checkbox>
                <a-tag v-if="article.selected_images?.[chapter.num]" color="green" size="small">已配图</a-tag>
                <a-tag v-else-if="article.images?.[chapter.num]?.length" color="blue" size="small">
                  {{ article.images[chapter.num].length }}张备选
                </a-tag>
              </div>
              <div class="chapter-content">{{ chapter.content }}</div>

              <!-- 备选图片选择 -->
              <div v-if="article.images?.[chapter.num]?.length" class="image-selector">
                <div class="selector-title">选择最终插入的图片：</div>
                <a-row :gutter="8">
                  <a-col :span="8" v-for="(img, idx) in article.images[chapter.num]" :key="idx">
                    <div
                      class="image-option"
                      :class="{ selected: article.selected_images?.[chapter.num] === img }"
                      @click="selectImage(chapter.num, img)"
                    >
                      <img :src="getImageUrl(img)" alt="备选图" />
                      <div class="image-overlay">
                        <icon-check v-if="article.selected_images?.[chapter.num] === img" />
                        <span v-else>点击选择</span>
                      </div>
                    </div>
                  </a-col>
                </a-row>
              </div>
            </div>
          </div>
          <a-empty v-if="!article.chapters?.length" description="暂无段落内容" />
        </a-card>
      </a-col>

      <!-- 右侧：文章预览 -->
      <a-col :span="10">
        <a-card title="文章预览（含已选图片）" class="preview-card">
          <div class="preview-content">
            <h2 class="preview-title">{{ article.title }}</h2>
            <div v-for="chapter in article.chapters" :key="chapter.num" class="preview-chapter">
              <h3 class="preview-chapter-title">{{ chapter.num }}. {{ chapter.title }}</h3>
              <img
                v-if="article.selected_images?.[chapter.num]"
                :src="getImageUrl(article.selected_images[chapter.num])"
                class="preview-image"
                alt="配图"
              />
              <p class="preview-chapter-content">{{ chapter.content }}</p>
            </div>
          </div>
          <a-empty v-if="!article.content" description="暂无正文内容" />
        </a-card>
      </a-col>
    </a-row>

    <!-- 生成配图弹窗 -->
    <a-modal
      v-model:visible="imageModalVisible"
      title="生成配图"
      :width="600"
    >
      <a-form layout="vertical">
        <a-form-item label="已勾选的段落">
          <a-tag v-for="num in selectedChapters" :key="num" color="blue" style="margin-right: 4px;">
            第 {{ num }} 段
          </a-tag>
          <span v-if="selectedChapters.length === 0" style="color: #999;">请先在左侧勾选需要配图的段落</span>
        </a-form-item>
        <a-form-item label="选择豆包账号" required>
          <a-select v-model="imageForm.account_id" style="width: 100%;" placeholder="请选择豆包账号">
            <a-option v-for="acc in doubaoAccounts" :key="acc.id" :value="acc.account_id">
              {{ acc.name }}（{{ acc.account_id }}）
            </a-option>
          </a-select>
        </a-form-item>
        <a-form-item label="每个段落备选图片数量">
          <a-input-number v-model="imageForm.count" :min="1" :max="10" />
        </a-form-item>
        <a-alert type="info">
          生成图片需要打开浏览器自动化操作豆包网页版，每个段落生成{{ imageForm.count }}张备选图片，预计需要较长时间，请耐心等待。
        </a-alert>
      </a-form>
      <template #footer>
        <a-space>
          <a-button @click="imageModalVisible = false">取消</a-button>
          <a-button type="primary" :loading="generatingImages" @click="generateImages">开始生成</a-button>
        </a-space>
      </template>
    </a-modal>

    <!-- 生成进度弹窗 -->
    <a-modal v-model:visible="progressModalVisible" title="图片生成进度" :footer="null" :closable="false">
      <div class="progress-content">
        <a-progress :percent="progressPercent" status="active" />
        <div class="progress-text">{{ progressText }}</div>
        <div v-if="imageTaskResults" class="progress-results">
          <div v-for="(result, num) in imageTaskResults" :key="num" class="result-item">
            <span>第 {{ num }} 段：</span>
            <a-tag :color="result.success ? 'green' : 'red'" size="small">
              {{ result.success ? `成功（${result.image_paths.length}张）` : '失败' }}
            </a-tag>
            <span v-if="!result.success" style="color: #f53f3f; margin-left: 8px;">{{ result.message }}</span>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { Message } from '@arco-design/web-vue'
import { aiGenerateApi, aiConfigApi } from '@/api'

const route = useRoute()
const articleId = route.params.id

const platformNames = {
  zhipu: '智谱AI',
  yuanbao: '腾讯元宝',
  doubao: '豆包'
}

// 文章数据
const article = ref({
  id: null,
  title: '',
  platform: '',
  article_type: 'free',
  content: '',
  chapters: [],
  images: {},
  selected_images: {}
})

// 勾选的段落
const selectedChapters = ref([])

// 豆包账号
const doubaoAccounts = ref([])

// 生成配图弹窗
const imageModalVisible = ref(false)
const imageForm = ref({
  account_id: '',
  count: 3
})
const generatingImages = ref(false)

// 进度弹窗
const progressModalVisible = ref(false)
const progressPercent = ref(0)
const progressText = ref('')
const imageTaskResults = ref(null)

// 获取图片URL
function getImageUrl(path) {
  if (!path) return ''
  // 如果是本地路径，通过静态文件服务访问
  if (path.startsWith('D:') || path.startsWith('C:')) {
    const filename = path.split(/[\\/]/).pop()
    return `/images/${filename}`
  }
  return path
}

// 加载文章详情
async function loadArticle() {
  try {
    const res = await aiGenerateApi.getArticle(articleId)
    article.value = res
    // 初始化已配图的段落
    if (res.selected_images) {
      // 不自动勾选，让用户自己选择
    }
  } catch (e) {
    Message.error('加载文章失败')
    console.error(e)
  }
}

// 加载豆包账号
async function loadDoubaoAccounts() {
  try {
    const res = await aiConfigApi.getAccounts('doubao')
    doubaoAccounts.value = res.list || []
  } catch (e) {
    console.error('加载豆包账号失败', e)
  }
}

// 显示生成配图弹窗
function showImageGenerateModal() {
  if (selectedChapters.value.length === 0) {
    Message.warning('请先勾选需要配图的段落')
    return
  }
  imageModalVisible.value = true
}

// 选择最终图片
async function selectImage(chapterNum, imagePath) {
  try {
    await aiGenerateApi.selectImage({
      article_id: parseInt(articleId),
      chapter_num: chapterNum,
      image_path: imagePath
    })
    // 更新本地数据
    if (!article.value.selected_images) {
      article.value.selected_images = {}
    }
    article.value.selected_images[chapterNum] = imagePath
    Message.success('已选择图片')
  } catch (e) {
    Message.error('选择图片失败')
  }
}

// 生成配图
async function generateImages() {
  if (!imageForm.value.account_id) {
    Message.warning('请选择豆包账号')
    return
  }

  generatingImages.value = true
  imageModalVisible.value = false
  progressModalVisible.value = true
  progressPercent.value = 0
  progressText.value = '正在启动图片生成任务...'
  imageTaskResults.value = null

  try {
    const res = await aiGenerateApi.generateImages({
      article_id: parseInt(articleId),
      chapter_nums: selectedChapters.value,
      account_id: imageForm.value.account_id,
      count: imageForm.value.count
    })

    // 轮询任务状态
    const taskId = res.task_id
    const total = selectedChapters.value.length

    const timer = setInterval(async () => {
      try {
        const status = await aiGenerateApi.getGenerateStatus(taskId)

        if (status.results) {
          const done = Object.keys(status.results).length
          progressPercent.value = Math.round((done / total) * 100)
          progressText.value = `已完成 ${done}/${total} 个段落`
          imageTaskResults.value = status.results
        }

        if (status.status === 'success' || status.status === 'failed') {
          clearInterval(timer)
          generatingImages.value = false
          progressPercent.value = 100
          progressText.value = status.status === 'success' ? '全部完成！' : '部分失败'

          setTimeout(() => {
            progressModalVisible.value = false
            loadArticle()
            if (status.status === 'success') {
              Message.success('图片生成完成！')
            } else {
              Message.warning('部分段落图片生成失败，请查看详情')
            }
          }, 1500)
        }
      } catch (e) {
        console.error('查询任务状态失败', e)
      }
    }, 5000)

  } catch (e) {
    generatingImages.value = false
    progressModalVisible.value = false
    Message.error('图片生成失败：' + (e.message || ''))
  }
}

// 自动排版
async function autoFormat() {
  try {
    const res = await aiGenerateApi.formatArticle(articleId)
    // 在新窗口打开排版预览
    const previewWindow = window.open('', '_blank')
    if (previewWindow) {
      previewWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <meta charset="UTF-8">
          <title>${res.title || '文章排版预览'}</title>
          <style>
            body { max-width: 800px; margin: 0 auto; padding: 40px 20px; font-family: 'Microsoft YaHei', sans-serif; }
          </style>
        </head>
        <body>
          ${res.html}
        </body>
        </html>
      `)
      previewWindow.document.close()
    }
    Message.success('排版预览已打开')
  } catch (e) {
    Message.error('排版失败：' + (e.message || ''))
  }
}

// 复制文章内容
function copyArticleContent() {
  try {
    if (!article.value || !article.value.chapters) {
      Message.warning('文章内容为空')
      return
    }

    // 拼接文章内容
    let content = article.value.title + '\n\n'
    article.value.chapters.forEach(chapter => {
      if (chapter.title) {
        content += chapter.title + '\n\n'
      }
      if (chapter.content) {
        content += chapter.content + '\n\n'
      }
    })

    // 复制到剪贴板
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content).then(() => {
        Message.success('文章内容已复制到剪贴板')
      }).catch(() => {
        // 降级方案：使用textarea
        fallbackCopy(content)
      })
    } else {
      fallbackCopy(content)
    }
  } catch (e) {
    Message.error('复制失败：' + (e.message || ''))
  }
}

// 降级复制方案
function fallbackCopy(text) {
  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.style.position = 'fixed'
  textarea.style.opacity = '0'
  document.body.appendChild(textarea)
  textarea.select()
  try {
    document.execCommand('copy')
    Message.success('文章内容已复制到剪贴板')
  } catch (e) {
    Message.error('复制失败，请手动复制')
  }
  document.body.removeChild(textarea)
}

// 导出Word
async function exportWord() {
  try {
    Message.loading({ content: '正在导出Word...', key: 'export' })
    const res = await aiGenerateApi.exportArticle(articleId)
    Message.success({ content: '导出成功！', key: 'export' })
    // 触发下载
    if (res.download_url) {
      const link = document.createElement('a')
      link.href = res.download_url
      link.download = res.filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    }
  } catch (e) {
    Message.error({ content: '导出失败：' + (e.message || ''), key: 'export' })
  }
}

onMounted(() => {
  loadArticle()
  loadDoubaoAccounts()
})
</script>

<style scoped>
.article-detail {
  padding: 16px;
}

.chapters-card {
  min-height: 600px;
}

.chapter-list {
  max-height: 700px;
  overflow-y: auto;
}

.chapter-item {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  transition: all 0.2s;
}

.chapter-item.selected {
  border-color: #165dff;
  background-color: #f2f3ff;
}

.chapter-item.has_image {
  border-color: #00b42a;
}

.chapter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.chapter-num {
  font-weight: bold;
  color: #165dff;
  margin-right: 8px;
}

.chapter-title {
  font-weight: 500;
}

.chapter-content {
  color: #4e5969;
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
}

.image-selector {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed #e5e6eb;
}

.selector-title {
  font-size: 12px;
  color: #86909c;
  margin-bottom: 8px;
}

.image-option {
  position: relative;
  cursor: pointer;
  border-radius: 4px;
  overflow: hidden;
  border: 2px solid transparent;
}

.image-option.selected {
  border-color: #00b42a;
}

.image-option img {
  width: 100%;
  height: 80px;
  object-fit: cover;
  display: block;
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
}

.image-option:hover .image-overlay {
  opacity: 1;
}

.image-option.selected .image-overlay {
  opacity: 1;
  background: rgba(0, 180, 42, 0.6);
}

.preview-card {
  min-height: 600px;
}

.preview-content {
  max-height: 700px;
  overflow-y: auto;
}

.preview-title {
  font-size: 20px;
  font-weight: bold;
  margin-bottom: 16px;
  text-align: center;
}

.preview-chapter {
  margin-bottom: 20px;
}

.preview-chapter-title {
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  color: #1d2129;
}

.preview-image {
  width: 100%;
  border-radius: 4px;
  margin-bottom: 8px;
}

.preview-chapter-content {
  font-size: 13px;
  line-height: 1.8;
  color: #4e5969;
  white-space: pre-wrap;
}

.progress-content {
  padding: 16px 0;
}

.progress-text {
  text-align: center;
  margin-top: 12px;
  color: #4e5969;
}

.progress-results {
  margin-top: 16px;
}

.result-item {
  margin-bottom: 8px;
  font-size: 13px;
}
</style>
