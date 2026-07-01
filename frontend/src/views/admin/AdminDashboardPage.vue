<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { Refresh, Setting, Switch, User } from '@element-plus/icons-vue'
import AdminBarList from '@/components/admin/AdminBarList.vue'
import AdminDashboardCustomizeDrawer from '@/components/admin/AdminDashboardCustomizeDrawer.vue'
import AdminDashboardWidgetShell from '@/components/admin/AdminDashboardWidgetShell.vue'
import AdminMiniLineChart from '@/components/admin/AdminMiniLineChart.vue'
import { useAdminDashboardStore } from '@/stores/adminDashboard'
import { useAdminDashboardLayoutStore } from '@/stores/adminDashboardLayout'
import type { AdminDashboardWidgetConfig } from '@/stores/adminDashboardLayout'
import type { LeaderboardEntry } from '@/types/api'

const router = useRouter()
const dashboardStore = useAdminDashboardStore()
const layoutStore = useAdminDashboardLayoutStore()
const customizeDrawerVisible = ref(false)

function getWidgetDescription(widget: AdminDashboardWidgetConfig) {
  const descriptions: Record<AdminDashboardWidgetConfig['id'], string> = {
    kpi: '学生、题库、作答、正确率和活跃度的核心指标。',
    trend: '用折线概览每天的答题热度变化。',
    leaderboard: '保留旧后台战力榜和周活跃榜查看能力。',
    riskUnits: '快速识别基础稳固和薄弱的单元。',
    focusStudents: '当前战力领先学生与近期未活跃学生。',
    quickActions: '常用模块直接跳转到独立页面。',
  }
  return descriptions[widget.id]
}

function getWidgetColSpan(widget: AdminDashboardWidgetConfig) {
  return widget.width === 'full' ? 24 : 12
}

function handleRegistrationChange(value: string | number | boolean) {
  void dashboardStore.setAllowSelfRegister(Boolean(value))
}

function handleLeaderboardTypeChange(value: string | number | boolean) {
  void dashboardStore.loadLeaderboard(value as 'power' | 'weekly')
}

function handleLeaderboardRowClick(row: LeaderboardEntry) {
  dashboardStore.selectedLeaderboardUserId = row.user_id
}

onMounted(() => {
  layoutStore.loadLayout()
  void dashboardStore.loadDashboard()
})
</script>

<template>
  <section class="admin-dashboard-page">
    <div class="admin-page__heading">
      <div>
        <p>Dashboard</p>
        <h2>仪表盘</h2>
      </div>
      <div class="admin-page__actions">
        <el-switch
          v-model="dashboardStore.allowSelfRegister"
          :loading="dashboardStore.registrationSaving"
          active-text="允许学生自主注册"
          @change="handleRegistrationChange"
        />
        <el-button :icon="Refresh" :loading="dashboardStore.loading" @click="dashboardStore.loadDashboard">
          刷新数据
        </el-button>
        <el-button :icon="Setting" @click="customizeDrawerVisible = true">自定义布局</el-button>
      </div>
    </div>

    <el-alert
      v-if="dashboardStore.error"
      class="admin-dashboard-page__alert"
      :title="dashboardStore.error"
      type="error"
      show-icon
      :closable="false"
    />

    <el-skeleton v-if="dashboardStore.loading && !dashboardStore.hasData" :rows="10" animated />

    <template v-else-if="dashboardStore.hasData">
      <el-row v-if="layoutStore.visibleWidgets.length > 0" :gutter="16" class="admin-dashboard-page__layout">
        <el-col
          v-for="widget in layoutStore.visibleWidgets"
          :key="widget.id"
          :xs="24"
          :lg="getWidgetColSpan(widget)"
        >
          <AdminDashboardWidgetShell
            :title="widget.title"
            :description="getWidgetDescription(widget)"
            :show-actions="widget.id === 'trend' || widget.id === 'leaderboard'"
          >
            <template #actions>
              <el-tag v-if="widget.id === 'trend'" type="info">7 天</el-tag>
              <el-select
                v-else-if="widget.id === 'leaderboard'"
                v-model="dashboardStore.leaderboardType"
                class="admin-leaderboard-select"
                @change="handleLeaderboardTypeChange"
              >
                <el-option label="战力榜" value="power" />
                <el-option label="周活跃榜" value="weekly" />
              </el-select>
            </template>

            <el-row v-if="widget.id === 'kpi'" :gutter="16" class="admin-dashboard-page__kpi-grid">
              <el-col v-for="item in dashboardStore.kpis" :key="item.label" :xs="24" :sm="12" :lg="8" :xl="4">
                <div class="admin-kpi-card">
                  <span>{{ item.label }}</span>
                  <strong>{{ item.value }}</strong>
                  <small>{{ item.hint }}</small>
                </div>
              </el-col>
            </el-row>

            <AdminMiniLineChart
              v-if="widget.id === 'trend'"
              :points="dashboardStore.trendPoints"
              aria-label="近 7 天作答趋势图"
            />

            <div v-if="widget.id === 'riskUnits'" class="admin-dashboard-page__split">
              <section>
                <div class="admin-dashboard-page__subhead">
                  <strong>单元正确率对比</strong>
                  <span>基础掌握情况</span>
                </div>
                <AdminBarList :items="dashboardStore.unitAccuracyBars" suffix="%" empty-copy="暂无单元正确率数据" />
              </section>
              <section>
                <div class="admin-dashboard-page__subhead">
                  <strong>重点风险单元</strong>
                  <span>按错误率和耗时排序</span>
                </div>
                <AdminBarList :items="dashboardStore.weakestUnitBars" suffix="%" empty-copy="暂无风险单元数据" />
              </section>
            </div>

            <div v-if="widget.id === 'quickActions'" class="admin-quick-links">
              <el-button
                v-for="item in dashboardStore.quickLinks"
                :key="item.path"
                class="admin-quick-link"
                @click="router.push(item.path)"
              >
                <span>
                  <strong>{{ item.label }}</strong>
                  <small>{{ item.desc }}</small>
                </span>
                <el-tag size="small" type="info">{{ item.meta }}</el-tag>
              </el-button>
            </div>

            <template v-if="widget.id === 'focusStudents'">
              <AdminBarList :items="dashboardStore.topStudentBars" empty-copy="暂无重点学生数据" />

              <div v-if="dashboardStore.inactiveStudents.length > 0" class="admin-inactive-list">
                <article v-for="student in dashboardStore.inactiveStudents" :key="student.user_id">
                  <el-icon><User /></el-icon>
                  <div>
                    <strong>{{ student.nickname }}</strong>
                    <span>
                      {{ dashboardStore.formatNumber(student.total_questions) }} 题 /
                      最近 {{ dashboardStore.formatDateTime(student.last_active) }}
                    </span>
                  </div>
                  <el-button text :icon="Switch" @click="router.push('/admin/students')">查看</el-button>
                </article>
              </div>
            </template>

            <el-table
              v-if="widget.id === 'leaderboard'"
              v-loading="dashboardStore.leaderboardLoading"
              :data="dashboardStore.leaderboard.slice(0, 8)"
              border
              size="small"
              empty-text="暂无排行榜数据"
              @row-click="handleLeaderboardRowClick"
            >
              <el-table-column label="排名" width="72">
                <template #default="{ row }">#{{ row.rank }}</template>
              </el-table-column>
              <el-table-column prop="nickname" label="学生" min-width="120" />
              <el-table-column :label="dashboardStore.leaderboardType === 'power' ? '战力' : '周活跃'" width="100">
                <template #default="{ row }">
                  {{ dashboardStore.leaderboardType === 'power'
                    ? dashboardStore.formatNumber(row.power_score)
                    : dashboardStore.formatNumber(row.weekly_activity) }}
                </template>
              </el-table-column>
              <el-table-column label="正确率" width="90">
                <template #default="{ row }">{{ dashboardStore.formatPercent(row.accuracy) }}</template>
              </el-table-column>
            </el-table>

            <div
              v-if="widget.id === 'leaderboard' && dashboardStore.selectedLeaderboardEntry"
              class="admin-leaderboard-focus"
            >
              <strong>{{ dashboardStore.selectedLeaderboardEntry.nickname }}</strong>
              <span>
                排名 #{{ dashboardStore.selectedLeaderboardEntry.rank }} ·
                通关 {{ dashboardStore.formatNumber(dashboardStore.selectedLeaderboardEntry.completed_levels) }} ·
                星数 {{ dashboardStore.formatNumber(dashboardStore.selectedLeaderboardEntry.total_stars) }}
              </span>
            </div>
          </AdminDashboardWidgetShell>
        </el-col>
      </el-row>

      <el-empty v-else description="当前没有显示的仪表盘模块">
        <el-button type="primary" @click="layoutStore.resetLayout">恢复默认布局</el-button>
      </el-empty>
    </template>

    <el-empty v-else description="暂无仪表盘数据">
      <el-button type="primary" :loading="dashboardStore.loading" @click="dashboardStore.loadDashboard">
        重新加载
      </el-button>
    </el-empty>

    <AdminDashboardCustomizeDrawer v-model="customizeDrawerVisible" />
  </section>
</template>

<style scoped>
.admin-page__heading {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 18px;
}

.admin-page__heading p {
  margin: 0 0 4px;
  color: var(--admin-primary);
  font-size: 13px;
}

.admin-page__heading h2 {
  margin: 0;
  color: var(--admin-text);
  font-size: 26px;
}

.admin-page__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  justify-content: flex-end;
}

.admin-dashboard-page__alert {
  margin-bottom: 16px;
}

.admin-dashboard-page__layout {
  row-gap: 16px;
}

.admin-dashboard-page__kpi-grid {
  row-gap: 16px;
}

.admin-kpi-card {
  min-height: 128px;
  height: 100%;
  padding: 18px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
  background: var(--admin-surface-soft);
}

.admin-kpi-card span,
.admin-kpi-card small {
  display: block;
  color: var(--admin-muted);
}

.admin-kpi-card strong {
  display: block;
  margin: 10px 0;
  color: var(--admin-text);
  font-size: 30px;
  line-height: 1;
}

.admin-dashboard-page__split {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 18px;
}

.admin-dashboard-page__subhead {
  display: flex;
  gap: 8px;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 14px;
}

.admin-dashboard-page__subhead strong {
  color: var(--admin-text);
  font-size: 14px;
}

.admin-dashboard-page__subhead span {
  color: var(--admin-muted);
  font-size: 12px;
}

.admin-quick-links {
  display: grid;
  gap: 10px;
}

.admin-quick-link {
  justify-content: space-between;
  width: 100%;
  height: auto;
  padding: 14px;
  white-space: normal;
}

.admin-quick-link span {
  display: grid;
  gap: 4px;
  min-width: 0;
  text-align: left;
}

.admin-quick-link strong,
.admin-quick-link small {
  display: block;
}

.admin-quick-link small {
  color: var(--admin-muted);
  line-height: 1.5;
}

.admin-inactive-list {
  display: grid;
  gap: 10px;
  margin-top: 16px;
}

.admin-inactive-list article {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  align-items: center;
  padding: 12px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-surface-soft);
}

.admin-inactive-list strong,
.admin-inactive-list span {
  display: block;
}

.admin-inactive-list strong {
  color: var(--admin-text);
}

.admin-inactive-list span {
  color: var(--admin-muted);
  font-size: 12px;
}

.admin-leaderboard-select {
  max-width: 120px;
}

.admin-leaderboard-focus {
  display: grid;
  gap: 4px;
  margin-top: 12px;
  padding: 12px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-surface-soft);
}

.admin-leaderboard-focus strong {
  color: var(--admin-text);
}

.admin-leaderboard-focus span {
  color: var(--admin-muted);
  font-size: 12px;
}

@media (max-width: 760px) {
  .admin-page__heading {
    align-items: flex-start;
    flex-direction: column;
  }

  .admin-page__actions {
    justify-content: flex-start;
    width: 100%;
  }

  .admin-dashboard-page__split {
    grid-template-columns: 1fr;
  }
}
</style>
