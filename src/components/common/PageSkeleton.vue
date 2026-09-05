<template>
  <div class="skeleton-page">
    <a-row :gutter="16" v-if="type === 'dashboard' || type === 'all'">
      <a-col :span="6" v-for="i in 4" :key="i">
        <a-card :bordered="false" class="skeleton-card">
          <a-skeleton :loading="true" :animation="true" :text="{ rows: 2, width: ['60%', '40%'] }" :avatar="{ size: 48, shape: 'circle' }" />
        </a-card>
      </a-col>
    </a-row>

    <a-card :bordered="false" class="skeleton-card" style="margin-top:16px" v-if="type === 'table' || type === 'all'">
      <a-skeleton :loading="true" :animation="true" :text="{ rows: 8, width: ['100%', '100%', '100%', '100%', '100%', '100%', '100%', '100%'] }" />
    </a-card>

    <a-card :bordered="false" class="skeleton-card" style="margin-top:16px" v-if="type === 'detail' || type === 'all'">
      <a-skeleton :loading="true" :animation="true" :text="{ rows: 6, width: ['100%', '80%', '100%', '60%', '100%', '90%'] }" />
    </a-card>
  </div>
</template>

<script setup>
defineProps({
  type: { type: String, default: 'all' } // all / dashboard / table / detail
})
</script>

<style scoped>
.skeleton-card :deep(.arco-card-body) {
  padding: 20px;
}
</style>
