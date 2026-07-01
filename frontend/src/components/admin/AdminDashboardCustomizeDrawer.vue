<script setup lang="ts">
import { Bottom, RefreshLeft, Top } from '@element-plus/icons-vue'
import { useAdminDashboardLayoutStore } from '@/stores/adminDashboardLayout'
import type { AdminDashboardWidgetConfig, AdminDashboardWidgetWidth } from '@/stores/adminDashboardLayout'

const visible = defineModel<boolean>({ default: false })
const layoutStore = useAdminDashboardLayoutStore()

function handleVisibleChange(widget: AdminDashboardWidgetConfig, value: string | number | boolean) {
  layoutStore.toggleWidget(widget.id, Boolean(value))
}

function handleWidthChange(widget: AdminDashboardWidgetConfig, value: string | number | boolean) {
  layoutStore.setWidgetWidth(widget.id, value as AdminDashboardWidgetWidth)
}
</script>

<template>
  <el-drawer v-model="visible" title="自定义仪表盘布局" size="420px" class="admin-dashboard-customize">
    <div class="admin-dashboard-customize__intro">
      <strong>工作台模块</strong>
      <span>调整显示、顺序和宽度后会自动保存在当前浏览器。</span>
    </div>

    <div class="admin-dashboard-customize__list">
      <article v-for="(widget, index) in layoutStore.widgets" :key="widget.id" class="admin-dashboard-customize__item">
        <div class="admin-dashboard-customize__item-head">
          <div>
            <strong>{{ widget.title }}</strong>
            <span>{{ widget.visible ? '已显示' : '已隐藏' }}</span>
          </div>
          <el-switch
            :model-value="widget.visible"
            active-text="显示"
            inactive-text="隐藏"
            @change="handleVisibleChange(widget, $event)"
          />
        </div>

        <div class="admin-dashboard-customize__controls">
          <el-button-group>
            <el-button :icon="Top" :disabled="index === 0" @click="layoutStore.moveWidgetUp(widget.id)">
              上移
            </el-button>
            <el-button
              :icon="Bottom"
              :disabled="index === layoutStore.widgets.length - 1"
              @click="layoutStore.moveWidgetDown(widget.id)"
            >
              下移
            </el-button>
          </el-button-group>

          <el-select :model-value="widget.width" @change="handleWidthChange(widget, $event)">
            <el-option label="半宽" value="half" />
            <el-option label="全宽" value="full" />
          </el-select>
        </div>
      </article>
    </div>

    <template #footer>
      <div class="admin-dashboard-customize__footer">
        <el-button :icon="RefreshLeft" @click="layoutStore.resetLayout">恢复默认布局</el-button>
        <el-button type="primary" @click="visible = false">完成</el-button>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.admin-dashboard-customize__intro {
  display: grid;
  gap: 6px;
  margin-bottom: 16px;
  padding: 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-surface-soft);
}

.admin-dashboard-customize__intro strong {
  color: var(--admin-text);
}

.admin-dashboard-customize__intro span {
  color: var(--admin-muted);
  font-size: 13px;
  line-height: 1.6;
}

.admin-dashboard-customize__list {
  display: grid;
  gap: 12px;
}

.admin-dashboard-customize__item {
  display: grid;
  gap: 12px;
  padding: 14px;
  border: 1px solid var(--admin-border);
  border-radius: 16px;
  background: var(--admin-surface);
}

.admin-dashboard-customize__item-head,
.admin-dashboard-customize__controls,
.admin-dashboard-customize__footer {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.admin-dashboard-customize__item-head strong,
.admin-dashboard-customize__item-head span {
  display: block;
}

.admin-dashboard-customize__item-head strong {
  color: var(--admin-text);
}

.admin-dashboard-customize__item-head span {
  margin-top: 4px;
  color: var(--admin-muted);
  font-size: 12px;
}

.admin-dashboard-customize__controls .el-select {
  width: 110px;
}

.admin-dashboard-customize__footer {
  width: 100%;
}

@media (max-width: 520px) {
  .admin-dashboard-customize__item-head,
  .admin-dashboard-customize__controls,
  .admin-dashboard-customize__footer {
    align-items: flex-start;
    flex-direction: column;
  }

  .admin-dashboard-customize__controls .el-select {
    width: 100%;
  }
}
</style>
