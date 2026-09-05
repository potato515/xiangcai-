<template>
  <div class="settings-page">
    <a-card title="排版设置">
      <a-form :model="form" layout="vertical" @submit="save">
        <a-row :gutter="24">
          <a-col :span="12">
            <a-form-item label="引言颜色"><a-color-picker v-model="form.introColor" show-text /></a-form-item>
            <a-form-item label="引言斜体"><a-switch v-model="form.introItalic" /></a-form-item>
            <a-form-item label="引言加粗"><a-switch v-model="form.introBlod" /></a-form-item>
            <a-form-item label="对话换行"><a-switch v-model="form.dialogueNewParagraph" /></a-form-item>
            <a-form-item label="对话加粗">
              <a-select v-model="form.dialogueBlod" allow-clear style="width:100%">
                <a-option value="colonAndContent">冒号和内容都加粗</a-option>
              </a-select>
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="创作声明前置"><a-switch v-model="form.declareBefore" /></a-form-item>
            <a-form-item label="创作声明斜体"><a-switch v-model="form.declareItalic" /></a-form-item>
            <a-form-item label="创作声明加粗"><a-switch v-model="form.declareBlod" /></a-form-item>
            <a-form-item label="段落首行缩进"><a-switch v-model="form.paragraphIndent" /></a-form-item>
            <a-form-item label="免费文章追加话题"><a-switch v-model="form.freeAticleTopic" /></a-form-item>
          </a-col>
        </a-row>
        <a-divider>过滤设置</a-divider>
        <a-form-item label="包含以下文字的段落过滤">
          <a-select v-model="form.filterContainText" mode="tags" placeholder="输入后回车添加" style="width:100%" />
        </a-form-item>
        <a-form-item label="以以下文字开头的段落过滤">
          <a-select v-model="form.filterStartText" mode="tags" placeholder="输入后回车添加" style="width:100%" />
        </a-form-item>
        <a-form-item label="移除文字">
          <a-select v-model="form.removeText" mode="tags" placeholder="输入后回车添加" style="width:100%" />
        </a-form-item>
        <a-divider>图片章节</a-divider>
        <a-form-item label="在以下章节后插入图片">
          <a-select v-model="imageChapters" mode="tags" placeholder="如：01、02、03" style="width:100%" />
        </a-form-item>
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit"><template #icon><icon-save /></template>保存设置</a-button>
            <a-button @click="reset">重置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>
<script setup>
import { ref, reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconSave } from '@arco-design/web-vue/es/icon'
import { settingsApi } from '@/api'

const imageChapters = ref(['01', '03', '05', '07', '09'])
const form = reactive({
  introColor: '#165dff',
  introItalic: true,
  introBlod: false,
  dialogueNewParagraph: true,
  dialogueBlod: 'colonAndContent',
  declareBefore: false,
  declareItalic: true,
  declareBlod: false,
  paragraphIndent: true,
  freeAticleTopic: false,
  filterContainText: ['关注我', '点赞', '收藏'],
  filterStartText: ['#', '##'],
  removeText: ['未完待续']
})

const save = async () => { try { await settingsApi.saveFormatting({ ...form, checkedChapters: imageChapters.value }) } catch {} Message.success('排版设置已保存') }
const reset = () => { Message.info('已重置为默认值') }
</script>
