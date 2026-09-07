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
          <a-tag v-if="isDirty" color="red">有未保存的修改</a-tag>
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
      <!-- 左侧：内容编辑区 -->
      <a-col :span="14">
        <a-card class="editor-card">
          <template #title>
            <a-space>
              <span>内容编辑区</span>
              <a-tag v-if="selectedChapter" color="blue">正在编辑：第 {{ selectedChapter }} 段</a-tag>
            </a-space>
          </template>
          <template #extra>
            <a-space>
              <a-button @click="resetEdits" :disabled="!isDirty">
                <template #icon><icon-reload /></template>
                重置
              </a-button>
              <a-button type="primary" @click="saveEdits" :disabled="!isDirty" :loading="saving">
                <template #icon><icon-check /></template>
                确认保存
              </a-button>
            </a-space>
          </template>

          <!-- 文章标题编辑 -->
          <a-form layout="vertical" class="title-editor">
            <a-form-item label="文章标题">
              <a-input v-model="editData.title" placeholder="请输入文章标题" @change="markDirty" />
            </a-form-item>
          </a-form>

          <!-- 章节列表 -->
          <div class="chapter-list">
            <div
              v-for="(chapter, index) in editData.chapters"
              :key="chapter.num"
              class="chapter-item"
              :class="{ selected: selectedChapter === chapter.num, has_image: editData.selected_images?.[chapter.num] }"
              @click="selectChapter(chapter.num)"
            >
              <div class="chapter-header">
                <div class="chapter-title-wrap">
                  <span class="chapter-num">{{ chapter.num }}</span>
                  <a-input
                    v-model="chapter.title"
                    class="chapter-title-input"
                    placeholder="章节小标题（可选）"
                    @click.stop
                    @change="markDirty"
                  />
                </div>
                <div class="chapter-actions">
                  <a-tag v-if="editData.selected_images?.[chapter.num]" color="green" size="small">已配图</a-tag>
                  <a-tag v-else-if="editData.images?.[chapter.num]?.length" color="blue" size="small">
                    {{ editData.images[chapter.num].length }}张备选
                  </a-tag>
                </div>
              </div>
              <a-textarea
                v-model="chapter.content"
                class="chapter-content-input"
                :rows="4"
                placeholder="请输入章节内容"
                @click.stop
                @change="markDirty"
              />
              <!-- 已插入的图片预览 -->
              <div v-if="editData.selected_images?.[chapter.num]" class="inserted-image-preview">
                <span class="image-label">已插入配图：</span>
                <img :src="getImageUrl(editData.selected_images[chapter.num])" alt="已插入配图" />
              </div>
            </div>
          </div>
          <a-empty v-if="!editData.chapters?.length" description="暂无段落内容" />
        </a-card>
      </a-col>

      <!-- 右侧：图片展示区域 -->
      <a-col :span="10">
        <a-card title="图片展示区" class="image-panel-card">
          <template #extra>
            <a-tag v-if="selectedChapter" color="blue">第 {{ selectedChapter }} 段</a-tag>
            <a-tag v-else color="gray">请先选择章节</a-tag>
          </template>

          <!-- 未选择章节时的提示 -->
          <div v-if="!selectedChapter" class="no-chapter-tip">
            <a-empty description="请在左侧点击选择一个章节，查看该章节的候选图片" />
          </div>

          <!-- 选择章节后显示候选图片 -->
          <div v-else class="image-gallery">
            <div class="gallery-header">
              <span>第 {{ selectedChapter }} 段的候选图片（点击选择插入）：</span>
              <a-button
                v-if="currentChapterImages.length > 0"
                size="small"
                type="text"
                status="danger"
                @click="clearSelectedImage"
              >
                清除已选
              </a-button>
            </div>

            <!-- 候选图片横向一字排开 -->
            <div class="image-row">
              <div
                v-for="(img, idx) in currentChapterImages"
                :key="idx"
                class="image-card"
                :class="{ selected: editData.selected_images?.[selectedChapter] === img }"
                @click="selectChapterImage(selectedChapter, img)"
              >
                <div class="image-index">{{ idx + 1 }}</div>
                <img :src="getImageUrl(img)" alt="候选图" />
                <div class="image-overlay">
                  <icon-check v-if="editData.selected_images?.[selectedChapter] === img" />
                  <span v-else>点击插入</span>
                </div>
              </div>
              <div v-if="currentChapterImages.length === 0" class="no-images">
                <a-empty description="该章节暂无候选图片，请点击上方'生成配图'按钮生成" />
              </div>
            </div>

            <!-- 图片位置调整 -->
            <div v-if="editData.selected_images?.[selectedChapter]" class="position-adjust">
              <div class="adjust-header">
                <span class="adjust-title">图片插入位置：</span>
                <a-button size="small" type="text" status="danger" @click="clearSelectedImage">
                  清除已选
                </a-button>
              </div>
              <div class="position-buttons">
                <a-radio-group
                  v-model="currentChapter.image_position"
                  direction="horizontal"
                  size="small"
                  @change="markDirty"
                >
                  <a-radio value="before">章节前</a-radio>
                  <a-radio value="after">章节后</a-radio>
                  <a-radio value="inline">段落中</a-radio>
                </a-radio-group>
              </div>
              <div class="selected-image-preview">
                <span class="preview-label">当前选中的图片：</span>
                <img :src="getImageUrl(editData.selected_images[selectedChapter])" alt="选中的图片" />
              </div>
            </div>

            <!-- 所有章节图片概览 -->
            <div class="all-chapters-overview">
              <div class="overview-title">所有章节配图状态：</div>
              <div class="overview-list">
                <a-tag
                  v-for="chapter in editData.chapters"
                  :key="chapter.num"
                  :color="editData.selected_images?.[chapter.num] ? 'green' : (editData.images?.[chapter.num]?.length ? 'blue' : 'gray')"
                  style="margin-bottom: 4px;"
                  @click="selectChapter(chapter.num)"
                >
                  {{ chapter.num }}: {{ editData.selected_images?.[chapter.num] ? '已配图' : (editData.images?.[chapter.num]?.length ? editData.images[chapter.num].length + '张备选' : '无图') }}
                </a-tag>
              </div>
            </div>
          </div>
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
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { Message, Modal } from '@arco-design/web-vue'
import { aiGenerateApi, aiConfigApi } from '@/api'

const route = useRoute()
const articleId = route.params.id

const platformNames = {
  zhipu: '智谱AI',
  yuanbao: '腾讯元宝',
  doubao: '豆包'
}

const positionNames = {
  before: '章节前',
  after: '章节后',
  inline: '段落中'
}

// 原始文章数据（用于重置）
const originalArticle = ref(null)

// 文章数据（展示用）
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

// 编辑数据（用户修改的内容）
const editData = ref({
  title: '',
  chapters: [],
  images: {},
  selected_images: {}
})

// 是否有未保存的修改
const isDirty = ref(false)

// 正在保存
const saving = ref(false)

// 当前选中的章节（用于右侧图片展示）
const selectedChapter = ref(null)

// 勾选的段落（用于生成配图）
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

// 当前选中章节的候选图片
// 当前选中章节的候选图片
const currentChapterImages = computed(() => {
  if (!selectedChapter.value) return []
  return editData.value.images?.[selectedChapter.value] || []
})

// 当前选中的章节对象
const currentChapter = computed(() => {
  if (!selectedChapter.value) return null
  return editData.value.chapters.find(c => c.num === selectedChapter.value) || null
})

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

// 标记为有修改
function markDirty() {
  isDirty.value = true
}

// 选择章节（用于右侧图片展示）
function selectChapter(num) {
  selectedChapter.value = num
  // 如果该章节没有勾选，自动勾选
  if (!selectedChapters.value.includes(num)) {
    selectedChapters.value.push(num)
  }
}

// 选择章节图片
async function selectChapterImage(chapterNum, imagePath) {
  try {
    await aiGenerateApi.selectImage({
      article_id: parseInt(articleId),
      chapter_num: chapterNum,
      image_path: imagePath
    })
    // 更新本地数据
    if (!editData.value.selected_images) {
      editData.value.selected_images = {}
    }
    editData.value.selected_images[chapterNum] = imagePath
    // 同步到article
    if (!article.value.selected_images) {
      article.value.selected_images = {}
    }
    article.value.selected_images[chapterNum] = imagePath
    // 初始化图片位置
    const chapter = editData.value.chapters.find(c => c.num === chapterNum)
    if (chapter && !chapter.image_position) {
      chapter.image_position = 'after'
    }
    markDirty()
    Message.success('图片已插入，可在左侧调整插入位置')
  } catch (e) {
    Message.error('选择图片失败')
  }
}

// 清除已选图片
function clearSelectedImage() {
  if (!selectedChapter.value) return
  Modal.confirm({
    title: '确认清除',
    content: `确定要清除第 ${selectedChapter.value} 段已插入的图片吗？`,
    onOk: () => {
      if (editData.value.selected_images) {
        delete editData.value.selected_images[selectedChapter.value]
      }
      if (article.value.selected_images) {
        delete article.value.selected_images[selectedChapter.value]
      }
      markDirty()
      Message.success('已清除图片')
    }
  })
}

// 重置编辑
function resetEdits() {
  Modal.confirm({
    title: '确认重置',
    content: '确定要清空本次所有修改吗？将恢复到上次保存的状态。',
    okButtonProps: { status: 'danger' },
    onOk: () => {
      if (originalArticle.value) {
        // 深拷贝原始数据
        editData.value = JSON.parse(JSON.stringify({
          title: originalArticle.value.title,
          chapters: originalArticle.value.chapters,
          images: originalArticle.value.images,
          selected_images: originalArticle.value.selected_images
        }))
        article.value = JSON.parse(JSON.stringify(originalArticle.value))
        isDirty.value = false
        Message.success('已重置为原始状态')
      }
    }
  })
}

// 保存编辑
async function saveEdits() {
  saving.value = true
  try {
    // 拼接完整文章内容
    let fullContent = editData.value.title + '\n\n'
    editData.value.chapters.forEach(chapter => {
      if (chapter.title) {
        fullContent += chapter.title + '\n\n'
      }
      if (chapter.content) {
        fullContent += chapter.content + '\n\n'
      }
    })

    // 调用保存API
    await aiGenerateApi.updateArticle(articleId, {
      title: editData.value.title,
      content: fullContent,
      article_type: article.value.article_type,
      selected_images: editData.value.selected_images,
      chapters: editData.value.chapters
    })

    // 更新原始数据
    originalArticle.value = JSON.parse(JSON.stringify({
      ...article.value,
      title: editData.value.title,
      chapters: editData.value.chapters,
      images: editData.value.images,
      selected_images: editData.value.selected_images
    }))
    article.value = JSON.parse(JSON.stringify(originalArticle.value))

    isDirty.value = false
    Message.success('保存成功')
  } catch (e) {
    Message.error('保存失败：' + (e.message || ''))
    console.error(e)
  } finally {
    saving.value = false
  }
}

// 加载文章详情
async function loadArticle() {
  try {
    const res = await aiGenerateApi.getArticle(articleId)
    article.value = res
    // 保存原始数据（用于重置）
    originalArticle.value = JSON.parse(JSON.stringify(res))
    // 初始化编辑数据
    editData.value = JSON.parse(JSON.stringify({
      title: res.title,
      chapters: res.chapters || [],
      images: res.images || {},
      selected_images: res.selected_images || {}
    }))
    // 初始化图片位置
    editData.value.chapters.forEach(chapter => {
      if (editData.value.selected_images?.[chapter.num] && !chapter.image_position) {
        chapter.image_position = 'after'
      }
    })
    isDirty.value = false
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
    Message.warning('请先在左侧点击选择需要配图的段落')
    return
  }
  imageModalVisible.value = true
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
              Message.success('图片生成完成！请在右侧选择要插入的图片')
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
    if (!editData.value || !editData.value.chapters) {
      Message.warning('文章内容为空')
      return
    }

    // 拼接文章内容（包含图片位置标记）
    let content = editData.value.title + '\n\n'
    editData.value.chapters.forEach(chapter => {
      // 章节前图片
      if (editData.value.selected_images?.[chapter.num] && chapter.image_position === 'before') {
        content += '[图片]\n\n'
      }
      if (chapter.title) {
        content += chapter.title + '\n\n'
      }
      // 段落中图片
      if (editData.value.selected_images?.[chapter.num] && chapter.image_position === 'inline') {
        content += '[图片]\n\n'
      }
      if (chapter.content) {
        content += chapter.content + '\n\n'
      }
      // 章节后图片
      if (editData.value.selected_images?.[chapter.num] && chapter.image_position === 'after') {
        content += '[图片]\n\n'
      }
    })

    // 复制到剪贴板
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content).then(() => {
        Message.success('文章内容已复制到剪贴板')
      }).catch(() => {
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

.editor-card {
  min-height: 700px;
}

.title-editor {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e5e6eb;
}

.chapter-list {
  max-height: 750px;
  overflow-y: auto;
  padding-right: 8px;
}

.chapter-item {
  padding: 12px;
  margin-bottom: 12px;
  border: 1px solid #e5e6eb;
  border-radius: 4px;
  transition: all 0.2s;
  cursor: pointer;
}

.chapter-item.selected {
  border-color: #165dff;
  background-color: #f2f3ff;
  box-shadow: 0 0 0 2px rgba(22, 93, 255, 0.1);
}

.chapter-item.has_image {
  border-color: #00b42a;
}

.chapter-item.selected.has_image {
  border-color: #165dff;
}

.chapter-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  gap: 8px;
}

.chapter-title-wrap {
  display: flex;
  align-items: center;
  flex: 1;
  gap: 8px;
}

.chapter-num {
  font-weight: bold;
  color: #165dff;
  font-size: 14px;
  min-width: 28px;
}

.chapter-title-input {
  flex: 1;
}

.chapter-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.chapter-content-input {
  width: 100%;
}

.inserted-image-preview {
  margin-top: 12px;
  padding: 8px;
  background: #f7f8fa;
  border-radius: 4px;
}

.inserted-image-preview .image-label {
  display: block;
  font-size: 12px;
  color: #86909c;
  margin-bottom: 8px;
}

.inserted-image-preview img {
  max-width: 100%;
  max-height: 150px;
  border-radius: 4px;
}

/* 右侧图片面板 */
.image-panel-card {
  min-height: 700px;
}

.no-chapter-tip {
  padding: 40px 0;
}

.image-gallery {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.gallery-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #4e5969;
}

/* 候选图片横向一字排开 */
.image-row {
  display: flex;
  gap: 12px;
  overflow-x: auto;
  padding: 8px 0;
  min-height: 140px;
}

.image-card {
  position: relative;
  flex-shrink: 0;
  width: 120px;
  height: 120px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.image-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.image-card.selected {
  border-color: #00b42a;
  box-shadow: 0 0 0 3px rgba(0, 180, 42, 0.2);
}

.image-card .image-index {
  position: absolute;
  top: 4px;
  left: 4px;
  background: rgba(0, 0, 0, 0.6);
  color: white;
  font-size: 11px;
  padding: 2px 6px;
  border-radius: 2px;
  z-index: 2;
}

.image-card img {
  width: 100%;
  height: 100%;
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
  z-index: 1;
}

.image-card:hover .image-overlay {
  opacity: 1;
}

.image-card.selected .image-overlay {
  opacity: 1;
  background: rgba(0, 180, 42, 0.6);
}

.no-images {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 图片位置调整 */
.position-adjust {
  margin-top: 16px;
  padding: 12px;
  background: #f7f8fa;
  border-radius: 4px;
}

.adjust-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.adjust-title {
  font-size: 13px;
  font-weight: 500;
  color: #1d2129;
}

.position-buttons {
  margin-bottom: 12px;
}

.selected-image-preview {
  margin-top: 8px;
}

.selected-image-preview .preview-label {
  display: block;
  font-size: 12px;
  color: #86909c;
  margin-bottom: 8px;
}

.selected-image-preview img {
  max-width: 100%;
  max-height: 180px;
  border-radius: 4px;
  border: 1px solid #e5e6eb;
}

/* 所有章节图片概览 */
.all-chapters-overview {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e5e6eb;
}

.overview-title {
  font-size: 13px;
  color: #4e5969;
  margin-bottom: 8px;
}

.overview-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.overview-list .arco-tag {
  cursor: pointer;
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
