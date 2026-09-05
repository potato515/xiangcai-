<template>
  <div class="batch-import">
    <a-page-header title="批量导入标题" @back="$router.back()">
      <template #sub-title>通过Excel模板批量导入文章标题，支持话题、AI类型、文章类型、限定提示词</template>
    </a-page-header>

    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="14">
        <a-card title="上传文件">
          <a-upload
            :custom-request="handleUpload"
            :show-file-list="false"
            accept=".xlsx,.xls"
            drag
          >
            <div class="upload-area">
              <icon-upload :size="48" style="color:#165dff" />
              <div style="margin-top:12px;font-size:15px">点击或拖拽Excel文件到此处</div>
              <div style="margin-top:8px;color:var(--color-text-3);font-size:13px">
                支持 .xlsx / .xls 格式，请先下载模板填写
              </div>
            </div>
          </a-upload>

          <a-alert
            v-if="uploadResult"
            :type="uploadResult.success ? 'success' : 'error'"
            :content="uploadResult.message"
            style="margin-top:16px"
            :closable="true"
            @close="uploadResult = null"
          />
        </a-card>

        <a-card title="导入记录" style="margin-top:16px">
          <a-table :data="importHistory" :pagination="false" bordered size="small">
            <template #columns>
              <a-table-column title="文件名" data-index="filename" />
              <a-table-column title="导入数量" data-index="count" :width="100" />
              <a-table-column title="导入时间" data-index="time" :width="180" />
              <a-table-column title="状态" data-index="status" :width="100">
                <template #cell="{ record }">
                  <a-tag :color="record.status === '成功' ? 'green' : 'red'">{{ record.status }}</a-tag>
                </template>
              </a-table-column>
            </template>
          </a-table>
        </a-card>
      </a-col>

      <a-col :span="10">
        <a-card title="操作指引">
          <a-steps direction="vertical" :current="3">
            <a-step title="下载模板">
              <template #description>
                点击下方按钮下载Excel模板，模板包含标题、话题、出文AI、文章类型、限定提示词五列
              </template>
            </a-step>
            <a-step title="填写数据">
              <template #description>
                按照模板格式填写标题数据，话题和AI类型可使用下拉选择，限定提示词可选填
              </template>
            </a-step>
            <a-step title="上传导入">
              <template #description>
                将填写好的Excel文件上传，系统自动解析并创建文章生成任务
              </template>
            </a-step>
            <a-step title="查看结果" status="process">
              <template #description>
                导入成功后可在文章管理页面查看生成进度
              </template>
            </a-step>
          </a-steps>
        </a-card>

        <a-card title="模板说明" style="margin-top:16px">
          <a-descriptions :column="1" size="small" bordered>
            <a-descriptions-item label="标题">必填，文章标题，建议30-60字</a-descriptions-item>
            <a-descriptions-item label="话题">必填，从下拉列表选择已有话题</a-descriptions-item>
            <a-descriptions-item label="出文AI">必填，老系统/新系统/智谱web</a-descriptions-item>
            <a-descriptions-item label="文章类型">必填，免费图文/付费订阅</a-descriptions-item>
            <a-descriptions-item label="限定提示词">选填，AI生成时的附加约束条件</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <a-button type="primary" long style="margin-top:16px" @click="downloadTemplate">
          <template #icon><icon-download /></template>
          下载标题批量导入模板
        </a-button>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconUpload, IconDownload } from '@arco-design/web-vue/es/icon'
import { articleApi } from '@/api'

const uploadResult = ref(null)
const importHistory = ref([
  { filename: '标题批量_20260901.xlsx', count: 50, time: '2026-09-01 14:30:00', status: '成功' },
  { filename: '家庭伦理标题.xlsx', count: 30, time: '2026-08-28 10:15:00', status: '成功' }
])

const handleUpload = async (option) => {
  const file = option.fileItem.file
  try {
    const res = await articleApi.batchUpload(file)
    uploadResult.value = { success: true, message: res || '导入成功' }
    importHistory.value.unshift({
      filename: file.name,
      count: parseInt(res) || 0,
      time: new Date().toLocaleString(),
      status: '成功'
    })
    Message.success('导入成功')
  } catch (e) {
    uploadResult.value = { success: false, message: '导入失败，请检查文件格式' }
    Message.error('导入失败')
  }
}

const downloadTemplate = async () => {
  try {
    const blob = await articleApi.downloadTemplate()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = '标题批量导入模板.xlsx'
    a.click()
    window.URL.revokeObjectURL(url)
  } catch {
    Message.success('模板下载中（模拟）')
  }
}
</script>

<style scoped>
.upload-area {
  padding: 40px 20px;
  text-align: center;
  border: 2px dashed var(--color-border-2);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.upload-area:hover {
  border-color: #165dff;
  background: rgba(22, 93, 255, 0.02);
}
</style>
