<template>
  <div class="log-panel">
    <div class="log-header">
      <span class="log-title">运行日志</span>
      <a-space>
        <a-tag :color="running ? 'green' : 'gray'" size="small">
          {{ running ? '运行中' : '已停止' }}
        </a-tag>
        <a-button size="mini" type="text" @click="$emit('clear')">清空</a-button>
      </a-space>
    </div>
    <div class="log-body" ref="logBody">
      <div v-for="(item, idx) in logs" :key="idx" class="log-line">
        <span class="log-time">{{ item.time }}</span>
        <span class="log-msg" :class="item.level">{{ item.msg }}</span>
      </div>
      <a-empty v-if="!logs.length" description="暂无日志" />
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  logs: { type: Array, default: () => [] },
  running: { type: Boolean, default: false }
})

defineEmits(['clear'])

const logBody = ref(null)

watch(() => props.logs.length, () => {
  nextTick(() => {
    if (logBody.value) logBody.value.scrollTop = 0
  })
})
</script>

<style scoped>
.log-panel {
  border: 1px solid var(--color-border-2);
  border-radius: 4px;
  overflow: hidden;
}
.log-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: var(--color-fill-2);
  border-bottom: 1px solid var(--color-border-2);
}
.log-title {
  font-weight: 600;
  font-size: 13px;
}
.log-body {
  max-height: 300px;
  overflow-y: auto;
  padding: 8px 12px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 12px;
}
.log-line {
  display: flex;
  gap: 8px;
  padding: 2px 0;
  border-bottom: 1px solid var(--color-fill-1);
}
.log-time {
  color: var(--color-text-4);
  flex-shrink: 0;
}
.log-msg {
  color: var(--color-text-2);
  word-break: break-all;
}
.log-msg.error { color: #f53f3f; }
.log-msg.warn { color: #ff7d00; }
.log-msg.success { color: #00b42a; }
</style>
