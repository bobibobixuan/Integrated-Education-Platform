<script setup lang="ts">
defineProps<{
  title: string
  description?: string
  showActions?: boolean
}>()
</script>

<template>
  <el-card shadow="never" class="admin-dashboard-widget">
    <template #header>
      <div class="admin-dashboard-widget__header">
        <div>
          <strong>{{ title }}</strong>
          <span v-if="description">{{ description }}</span>
        </div>
        <div v-if="showActions && $slots.actions" class="admin-dashboard-widget__actions">
          <slot name="actions" />
        </div>
      </div>
    </template>
    <slot />
  </el-card>
</template>

<style scoped>
.admin-dashboard-widget {
  min-height: 100%;
}

.admin-dashboard-widget__header {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.admin-dashboard-widget__header strong,
.admin-dashboard-widget__header span {
  display: block;
}

.admin-dashboard-widget__header strong {
  color: var(--admin-text);
  font-size: 16px;
}

.admin-dashboard-widget__header span {
  margin-top: 4px;
  color: var(--admin-muted);
  font-size: 13px;
  line-height: 1.5;
}

.admin-dashboard-widget__actions {
  display: flex;
  flex-shrink: 0;
  gap: 8px;
  align-items: center;
}

@media (max-width: 760px) {
  .admin-dashboard-widget__header {
    align-items: flex-start;
    flex-direction: column;
  }
}
</style>
