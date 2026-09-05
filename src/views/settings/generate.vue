<template>
  <div class="settings-page">
    <a-card title="生成设置">
      <a-form :model="form" layout="vertical" @submit="save">
        <a-form-item label="默认出文AI">
          <a-radio-group v-model="form.ai">
            <a-radio value="yangdu_old">仰度老系统</a-radio>
            <a-radio value="yangdu_new">仰度新系统</a-radio>
            <a-radio value="zhipu">智谱web</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="出图模式">
          <a-radio-group v-model="form.imageMode">
            <a-radio value="one-image">分章节模式</a-radio>
            <a-radio value="all-image">总结模式</a-radio>
          </a-radio-group>
        </a-form-item>
        <a-form-item label="文章生成间隔（秒）"><a-input-number v-model="form.articleInterval" :min="5" :max="300" /></a-form-item>
        <a-form-item label="图片生成间隔（秒）"><a-input-number v-model="form.imageInterval" :min="5" :max="300" /></a-form-item>
        <a-form-item label="单账号每日最大出文数"><a-input-number v-model="form.maxArticlePerDay" :min="1" :max="50" /></a-form-item>
        <a-form-item label="单账号每日最大出图数"><a-input-number v-model="form.maxImagePerDay" :min="1" :max="50" /></a-form-item>
        <a-form-item label="浏览器空闲自动关闭（分钟）"><a-input-number v-model="form.browserIdleTimeout" :min="5" :max="120" /></a-form-item>
        <a-divider>爬虫设置</a-divider>
        <a-form-item label="每日采集上限（最小）"><a-input-number v-model="form.spiderMinCount" :min="10" :max="500" /></a-form-item>
        <a-form-item label="每日采集上限（最大）"><a-input-number v-model="form.spiderMaxCount" :min="10" :max="500" /></a-form-item>
        <a-form-item label="新文章最低阅读量"><a-input-number v-model="form.newLimit" :min="0" :max="100000" /></a-form-item>
        <a-form-item label="旧文章最低阅读量"><a-input-number v-model="form.oldLimit" :min="0" :max="100000" /></a-form-item>
        <a-form-item>
          <a-button type="primary" html-type="submit"><template #icon><icon-save /></template>保存设置</a-button>
        </a-form-item>
      </a-form>
    </a-card>
  </div>
</template>
<script setup>
import { reactive } from 'vue'
import { Message } from '@arco-design/web-vue'
import { IconSave } from '@arco-design/web-vue/es/icon'
import { settingsApi } from '@/api'

const form = reactive({
  ai: 'yangdu_new', imageMode: 'one-image', articleInterval: 30, imageInterval: 20,
  maxArticlePerDay: 10, maxImagePerDay: 10, browserIdleTimeout: 15,
  spiderMinCount: 50, spiderMaxCount: 100, newLimit: 1000, oldLimit: 5000
})
const save = async () => { try { await settingsApi.saveGenerate(form) } catch {} Message.success('生成设置已保存') }
</script>
