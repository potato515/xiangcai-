<template>
  <a-card class="page-card" :bordered="false">
    <template v-if="title || $slots.title" #title>
      <slot name="title">{{ title }}</slot>
    </template>
    <template v-if="$slots.extra" #extra>
      <slot name="extra" />
    </template>
    <slot />
  </a-card>
</template>

<script setup>
defineProps({
  title: { type: String, default: '' }
})
</script>

<style scoped>
.page-card {
  margin-bottom: 16px;
}
.page-card :deep(.arco-card-body) {
  padding: 20px;
}
</style>
