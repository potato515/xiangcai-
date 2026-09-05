<template>
  <a-card class="stat-card" :bordered="false">
    <div class="stat-inner">
      <div class="stat-icon" :style="{ background: color }">
        <component :is="icon" :size="24" style="color:#fff" />
      </div>
      <div class="stat-info">
        <div class="stat-value">{{ value }}</div>
        <div class="stat-title">{{ title }}</div>
        <div v-if="subTitle" class="stat-sub">{{ subTitle }}</div>
      </div>
      <div v-if="$slots.extra" class="stat-extra">
        <slot name="extra" />
      </div>
    </div>
  </a-card>
</template>

<script setup>
defineProps({
  title: { type: String, required: true },
  value: { type: [String, Number], required: true },
  icon: { type: Object, required: true },
  color: { type: String, default: '#165dff' },
  subTitle: { type: String, default: '' }
})
</script>

<style scoped>
.stat-card :deep(.arco-card-body) {
  padding: 20px;
}
.stat-inner {
  display: flex;
  align-items: center;
  gap: 16px;
}
.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.stat-value {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}
.stat-title {
  font-size: 13px;
  color: var(--color-text-3);
  margin-top: 4px;
}
.stat-sub {
  font-size: 12px;
  color: var(--color-text-4);
  margin-top: 2px;
}
.stat-extra {
  margin-left: auto;
}
</style>
