<template>
  <div class="empty-state">
    <a-empty :description="description">
      <template v-if="$slots.image" #image>
        <slot name="image" />
      </template>
    </a-empty>
    <div v-if="$slots.action" class="empty-action">
      <slot name="action" />
    </div>
  </div>
</template>

<script setup>
defineProps({
  description: { type: String, default: '暂无数据' }
})
</script>

<style scoped>
.empty-state {
  padding: 40px 0;
  text-align: center;
}
.empty-action {
  margin-top: 16px;
}
</style>
