<template>
  <a-tag :color="color">{{ text }}</a-tag>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: { type: [Number, String], required: true },
  type: { type: String, default: 'article' }
})

const articleStatusMap = {
  11: { text: '待生成文章', color: 'orange' },
  12: { text: '待生成图片', color: 'orange' },
  21: { text: '文章生成中', color: 'blue' },
  22: { text: '图片生成中', color: 'blue' },
  3: { text: '生成成功', color: 'green' },
  41: { text: '文章失败', color: 'red' },
  42: { text: '图片失败', color: 'red' },
  5: { text: '草稿创建中', color: 'cyan' },
  6: { text: '草稿成功', color: 'green' },
  7: { text: '草稿失败', color: 'red' },
  8: { text: '已复制', color: 'purple' },
  9: { text: '待草稿', color: 'orange' },
  10: { text: '已导出', color: 'gray' }
}

const loginStatusMap = {
  0: { text: '未登录', color: 'red' },
  1: { text: '已登录', color: 'green' }
}

const browserStateMap = {
  0: { text: '未启动', color: 'gray' },
  1: { text: '初始化', color: 'orange' },
  2: { text: '检查登录', color: 'blue' },
  3: { text: '未登录', color: 'red' },
  4: { text: '运行中', color: 'green' }
}

const commandStatusMap = {
  0: { text: '待执行', color: 'orange' },
  1: { text: '执行中', color: 'blue' },
  2: { text: '已完成', color: 'green' },
  3: { text: '失败', color: 'red' }
}

const text = computed(() => {
  const map = props.type === 'login' ? loginStatusMap
    : props.type === 'browser' ? browserStateMap
    : props.type === 'command' ? commandStatusMap
    : articleStatusMap
  return map[props.status]?.text || props.status
})

const color = computed(() => {
  const map = props.type === 'login' ? loginStatusMap
    : props.type === 'browser' ? browserStateMap
    : props.type === 'command' ? commandStatusMap
    : articleStatusMap
  return map[props.status]?.color || 'gray'
})
</script>
