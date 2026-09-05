<template>
  <div class="settings-page">
    <a-card title="导出设置">
      <a-form :model="form" layout="vertical" @submit="save">
        <a-form-item label="自动排版并导出"><a-switch v-model="form.isAutoFormatAndExport" /></a-form-item>
        <a-form-item label="导出到指定目录"><a-switch v-model="form.isExportSpecifiedDirectory" /></a-form-item>
        <a-form-item label="指定导出目录" v-if="form.isExportSpecifiedDirectory">
          <a-input v-model="form.exportSpecifiedDirectory" placeholder="如：D:\Articles\Export">
            <template #prefix><icon-folder /></template>
          </a-input>
        </a-form-item>
        <a-alert type="info" content="导出的Word文档将按话题分类存放在指定目录下" style="margin-bottom:16px" />
        <a-form-item>
          <a-space>
            <a-button type="primary" html-type="submit"><template #icon><icon-save /></template>保存设置</a-button>
          </a-space>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>
<script setup>
import { reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconSave, IconFolder } from '@arco-design/web-vue/es/icon'
import { settingsApi } from '@/api'

const form = reactive({ isAutoFormatAndExport: false, isExportSpecifiedDirectory: true, exportSpecifiedDirectory: 'D:\\Articles\\Export' })
const save = async () => { try { await settingsApi.saveExport(form) } catch {} Message.success('导出设置已保存') }
</script>
