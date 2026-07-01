<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Edit, Plus, Refresh, VideoPause, VideoPlay, View } from '@element-plus/icons-vue'
import { useAdminPvpStore } from '@/stores/adminPvp'
import type { PvpRoom } from '@/types/api'

const pvpStore = useAdminPvpStore()
const formVisible = ref(false)
const detailVisible = ref(false)
const detailActiveTab = ref('overview')

function getErrorMessage(error: unknown) {
  return error instanceof Error ? error.message : '操作失败，请稍后重试。'
}

async function openCreateDialog() {
  try {
    await pvpStore.openNewRoomForm()
    formVisible.value = true
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
}

async function openEditDialog(room: PvpRoom) {
  try {
    await pvpStore.openEditRoomForm(room)
    formVisible.value = true
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
}

function openRoomDetail(room: PvpRoom) {
  pvpStore.selectedRoomId = room.id
  detailActiveTab.value = 'overview'
  detailVisible.value = true
}

function handleRowClick(row: PvpRoom) {
  openRoomDetail(row)
}

async function saveRoom() {
  try {
    const isEditing = pvpStore.editingRoomId !== null
    await pvpStore.saveRoom()
    formVisible.value = false
    ElMessage.success(isEditing ? '竞技房间已更新。' : '竞技房间已创建。')
  } catch (error) {
    ElMessage.error(getErrorMessage(error))
  }
}

async function refreshRooms() {
  await pvpStore.loadRooms()
  pvpStore.requestRoomsSnapshot()
}

function getRoomRowClassName({ row }: { row: PvpRoom }) {
  return row.id === pvpStore.selectedRoomId ? 'is-selected-room' : ''
}

function isWaitingRoom(room: PvpRoom) {
  return room.status === 'waiting'
}

function isRunningRoom(room: PvpRoom) {
  return room.status === 'running'
}

function isFinishedRoom(room: PvpRoom) {
  return room.status === 'finished'
}

function canEditRoom(room: PvpRoom) {
  return room.status !== 'running' && room.status !== 'countdown'
}

function formatNullableDate(value: string | null | undefined) {
  return value ? pvpStore.formatDateTime(value) : '暂无数据'
}

async function confirmStartRoom(room: PvpRoom) {
  try {
    await ElMessageBox.confirm(
      '开始后学生将进入正式对战流程，确认立即开始吗？',
      '开始竞技房间',
      {
        confirmButtonText: '立即开始',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    await pvpStore.startRoom(room.id)
    ElMessage.success('竞技房间已开始。')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(getErrorMessage(error))
  }
}

async function confirmFinishRoom(room: PvpRoom) {
  try {
    await ElMessageBox.confirm(
      '结束后将立即进行结算并锁定当前结果，确认继续吗？',
      '结束竞技房间',
      {
        confirmButtonText: '结束并结算',
        cancelButtonText: '取消',
        type: 'warning',
      },
    )
    await pvpStore.finishRoom(room.id)
    ElMessage.success('竞技房间已结束。')
  } catch (error) {
    if (error === 'cancel' || error === 'close') return
    ElMessage.error(getErrorMessage(error))
  }
}

function unitLevelCount(unit: { levels?: unknown }) {
  if (Array.isArray(unit.levels)) return unit.levels.length
  return typeof unit.levels === 'number' ? unit.levels : 0
}

onMounted(() => {
  void pvpStore.loadRooms()
  pvpStore.connectSocket()
})

onUnmounted(() => {
  pvpStore.closeSocket()
})
</script>

<template>
  <section class="admin-page">
    <div class="admin-page__heading">
      <div>
        <p>PVP</p>
        <h2>PVP 管理</h2>
      </div>
      <div class="admin-page__actions">
        <el-tag :type="pvpStore.socketReady ? 'success' : 'info'">
          {{ pvpStore.socketReady ? '实时同步已连接' : '实时同步连接中' }}
        </el-tag>
        <el-button :icon="Refresh" :loading="pvpStore.loading" @click="refreshRooms">刷新</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreateDialog">创建房间</el-button>
      </div>
    </div>

    <el-alert
      v-if="pvpStore.error"
      class="admin-page__alert"
      :title="pvpStore.error"
      type="error"
      show-icon
      :closable="false"
    />

    <el-row :gutter="16" class="pvp-summary">
      <el-col :xs="24" :sm="12" :lg="4">
        <el-card shadow="never" class="pvp-kpi">
          <span>房间总数</span>
          <strong>{{ pvpStore.formatNumber(pvpStore.pvpOverview.total) }}</strong>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="4">
        <el-card shadow="never" class="pvp-kpi">
          <span>等待中</span>
          <strong>{{ pvpStore.formatNumber(pvpStore.pvpOverview.waiting) }}</strong>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="4">
        <el-card shadow="never" class="pvp-kpi">
          <span>进行中</span>
          <strong>{{ pvpStore.formatNumber(pvpStore.pvpOverview.running) }}</strong>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="4">
        <el-card shadow="never" class="pvp-kpi">
          <span>已结束</span>
          <strong>{{ pvpStore.formatNumber(pvpStore.pvpOverview.finished) }}</strong>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="4">
        <el-card shadow="never" class="pvp-kpi">
          <span>在线成员</span>
          <strong>{{ pvpStore.formatNumber(pvpStore.pvpOverview.onlineMembers) }}</strong>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :lg="4">
        <el-card shadow="never" class="pvp-kpi pvp-kpi--meta">
          <span>快照同步</span>
          <strong>{{ pvpStore.socketReady ? '已连接' : '等待同步' }}</strong>
          <small>{{ pvpStore.pvpOverview.lastSnapshotAt ? pvpStore.formatDateTime(pvpStore.pvpOverview.lastSnapshotAt) : '暂无数据' }}</small>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never" class="admin-pvp-card">
      <template #header>
        <div class="pvp-card-head">
          <div>
            <strong>比赛房间控制台</strong>
            <span>按状态执行编辑、开赛、结算和详情查看。</span>
          </div>
          <el-button :icon="Refresh" :loading="pvpStore.loading" @click="refreshRooms">刷新列表</el-button>
        </div>
      </template>

      <el-skeleton v-if="pvpStore.loading && pvpStore.rooms.length === 0" :rows="8" animated />
      <el-empty v-else-if="pvpStore.rooms.length === 0" description="当前还没有竞技房间">
        <el-button type="primary" @click="openCreateDialog">创建房间</el-button>
      </el-empty>
      <el-table
        v-else
        :data="pvpStore.rooms"
        border
        row-key="id"
        :row-class-name="getRoomRowClassName"
        @row-click="handleRowClick"
      >
        <el-table-column label="房间" min-width="220">
          <template #default="{ row }">
            <div class="room-cell">
              <strong>{{ row.title }}</strong>
              <span>{{ row.description || '未填写房间说明' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <div class="pvp-status-cell">
              <el-tag :type="pvpStore.roomStatusType(row.status)">
                {{ pvpStore.roomStatusLabel(row.status) }}
              </el-tag>
              <span>{{ row.mode || '暂无模式' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="人数" width="130">
          <template #default="{ row }">
            <div class="pvp-member-count">
              <strong>{{ row.member_count }}/{{ row.group_size }}</strong>
              <span>{{ pvpStore.formatNumber(row.ready_count) }} 人已准备</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="题量" width="90">
          <template #default="{ row }">{{ pvpStore.formatNumber(row.question_count) }}</template>
        </el-table-column>
        <el-table-column label="总时限" width="110">
          <template #default="{ row }">{{ pvpStore.formatSeconds(row.battle_time_limit_seconds) }}</template>
        </el-table-column>
        <el-table-column label="创建时间" width="130">
          <template #default="{ row }">{{ formatNullableDate(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" :icon="View" @click.stop="openRoomDetail(row)">详情</el-button>
            <el-button v-if="canEditRoom(row)" link :icon="Edit" @click.stop="openEditDialog(row)">编辑</el-button>
            <el-button
              v-if="isWaitingRoom(row)"
              link
              type="success"
              :icon="VideoPlay"
              @click.stop="confirmStartRoom(row)"
            >
              开始
            </el-button>
            <el-button
              v-if="isRunningRoom(row)"
              link
              type="danger"
              :icon="VideoPause"
              @click.stop="confirmFinishRoom(row)"
            >
              结束
            </el-button>
            <el-button v-if="isFinishedRoom(row)" link type="info" @click.stop="openRoomDetail(row)">查看结果</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-drawer v-model="detailVisible" title="房间详情" size="640px">
      <template v-if="pvpStore.selectedRoom">
        <div class="room-detail">
          <div class="room-detail__profile">
            <div>
              <strong>{{ pvpStore.selectedRoom.title }}</strong>
              <span>{{ pvpStore.selectedRoom.description || '未填写房间说明' }}</span>
            </div>
            <el-tag :type="pvpStore.roomStatusType(pvpStore.selectedRoom.status)">
              {{ pvpStore.roomStatusLabel(pvpStore.selectedRoom.status) }}
            </el-tag>
          </div>

          <div class="room-detail__actions">
            <el-button v-if="canEditRoom(pvpStore.selectedRoom)" @click="openEditDialog(pvpStore.selectedRoom)">编辑房间</el-button>
            <el-button
              v-if="pvpStore.canStartSelectedRoom"
              type="success"
              @click="confirmStartRoom(pvpStore.selectedRoom)"
            >
              开始比赛
            </el-button>
            <el-button
              v-if="pvpStore.canFinishSelectedRoom"
              type="danger"
              @click="confirmFinishRoom(pvpStore.selectedRoom)"
            >
              结束并结算
            </el-button>
          </div>

          <el-tabs v-model="detailActiveTab" class="room-detail__tabs">
            <el-tab-pane label="房间概览" name="overview">
              <div class="room-detail__metrics">
                <article><span>状态</span><strong>{{ pvpStore.selectedRoomStatusText }}</strong></article>
                <article><span>模式</span><strong>{{ pvpStore.selectedRoom.mode || '暂无数据' }}</strong></article>
                <article><span>成员</span><strong>{{ pvpStore.selectedRoom.member_count }}/{{ pvpStore.selectedRoom.group_size }}</strong></article>
                <article><span>题量</span><strong>{{ pvpStore.formatNumber(pvpStore.selectedRoom.question_count) }}</strong></article>
                <article><span>总时限</span><strong>{{ pvpStore.formatSeconds(pvpStore.selectedRoom.battle_time_limit_seconds) }}</strong></article>
                <article><span>已准备</span><strong>{{ pvpStore.formatNumber(pvpStore.selectedRoom.ready_count) }}</strong></article>
                <article><span>创建时间</span><strong>{{ formatNullableDate(pvpStore.selectedRoom.created_at) }}</strong></article>
                <article><span>开始时间</span><strong>{{ formatNullableDate(pvpStore.selectedRoom.started_at || pvpStore.selectedRoom.battle_started_at) }}</strong></article>
                <article><span>结束时间</span><strong>{{ formatNullableDate(pvpStore.selectedRoom.finished_at) }}</strong></article>
                <article><span>快照时间</span><strong>{{ pvpStore.lastSnapshotAt ? pvpStore.formatDateTime(pvpStore.lastSnapshotAt) : '等待同步' }}</strong></article>
              </div>
            </el-tab-pane>

            <el-tab-pane label="成员状态" name="members">
              <el-table :data="pvpStore.selectedRoomMembers" border size="small" empty-text="暂无成员">
                <el-table-column label="排名" width="70">
                  <template #default="{ row }">#{{ row.rank || '暂无' }}</template>
                </el-table-column>
                <el-table-column label="学生" min-width="130">
                  <template #default="{ row }">
                    <div class="room-member-cell">
                      <strong>{{ row.nickname }}</strong>
                      <span>@{{ row.username }}</span>
                    </div>
                  </template>
                </el-table-column>
                <el-table-column label="在线" width="80">
                  <template #default="{ row }">
                    <el-tag size="small" :type="row.is_online ? 'success' : 'info'">
                      {{ row.is_online ? '在线' : '离线' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="准备" width="80">
                  <template #default="{ row }">
                    <el-tag size="small" :type="row.is_ready ? 'success' : 'info'">
                      {{ row.is_ready ? '已准备' : '未准备' }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column label="分数" width="90">
                  <template #default="{ row }">{{ pvpStore.formatNumber(row.battle_power) }}</template>
                </el-table-column>
                <el-table-column label="正确率" width="90">
                  <template #default="{ row }">{{ pvpStore.formatPercent(row.accuracy) }}</template>
                </el-table-column>
                <el-table-column label="已答" width="80">
                  <template #default="{ row }">{{ pvpStore.formatNumber(row.answered_count) }}</template>
                </el-table-column>
              </el-table>
            </el-tab-pane>

            <el-tab-pane label="对战进度" name="progress">
              <div class="room-detail__metrics">
                <article><span>当前题号</span><strong>等待同步</strong></article>
                <article><span>总题数</span><strong>{{ pvpStore.formatNumber(pvpStore.selectedRoomProgress.totalQuestions) }}</strong></article>
                <article><span>已提交人数</span><strong>{{ pvpStore.formatNumber(pvpStore.selectedRoomProgress.submittedMembers) }}</strong></article>
                <article><span>累计答题</span><strong>{{ pvpStore.formatNumber(pvpStore.selectedRoomProgress.answeredCount) }}</strong></article>
                <article>
                  <span>平均正确率</span>
                  <strong>
                    {{ pvpStore.selectedRoomProgress.averageAccuracy === null ? '暂无数据' : pvpStore.formatPercent(pvpStore.selectedRoomProgress.averageAccuracy) }}
                  </strong>
                </article>
                <article>
                  <span>当前领先者</span>
                  <strong>{{ pvpStore.selectedRoomProgress.leader?.nickname || '暂无数据' }}</strong>
                </article>
              </div>
            </el-tab-pane>

            <el-tab-pane label="日志 / 事件" name="logs">
              <div class="room-sync-meta">
                <span>WebSocket 状态：{{ pvpStore.socketReady ? '已连接' : '等待同步' }}</span>
                <span>快照更新时间：{{ pvpStore.lastSnapshotAt ? pvpStore.formatDateTime(pvpStore.lastSnapshotAt) : '暂无数据' }}</span>
              </div>
              <el-empty v-if="pvpStore.selectedRoomLogs.length === 0" description="暂无房间日志" />
              <div v-else class="room-log-list">
                <article v-for="log in pvpStore.selectedRoomLogs" :key="log.id">
                  <p>{{ log.message }}</p>
                  <span>{{ log.category }} · {{ pvpStore.formatDateTime(log.created_at) }}</span>
                </article>
              </div>
            </el-tab-pane>
          </el-tabs>
        </div>
      </template>
      <el-empty v-else description="请选择一个房间" />
    </el-drawer>

    <el-dialog
      v-model="formVisible"
      :title="pvpStore.editingRoomId !== null ? '编辑竞技房间' : '新建竞技房间'"
      width="760px"
      class="pvp-room-dialog"
      align-center
    >
      <el-form :model="pvpStore.roomForm" label-position="top" class="pvp-room-form">
        <section class="pvp-form-section">
          <div class="pvp-form-section__head">
            <strong>基础信息</strong>
            <span>用于教师识别房间和控制比赛容量。</span>
          </div>
          <el-row :gutter="14">
            <el-col :xs="24" :md="12">
              <el-form-item label="房间名称">
                <el-input v-model.trim="pvpStore.roomForm.title" placeholder="例如：三年级计算挑战" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="房间说明">
                <el-input v-model.trim="pvpStore.roomForm.description" placeholder="可选，显示给后台识别" />
              </el-form-item>
            </el-col>
          </el-row>
        </section>

        <section class="pvp-form-section">
          <div class="pvp-form-section__head">
            <strong>比赛规则</strong>
            <span>不新增协议字段，只配置现有房间参数。</span>
          </div>
          <el-row :gutter="14">
            <el-col :xs="24" :md="8">
              <el-form-item label="人数上限">
                <el-input-number v-model="pvpStore.roomForm.group_size" :min="2" :max="12" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="题数">
                <el-input-number v-model="pvpStore.roomForm.question_count" :min="2" :max="50" />
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="8">
              <el-form-item label="总时限（秒）">
                <el-input-number v-model="pvpStore.roomForm.battle_time_limit_seconds" :min="0" :max="3600" />
              </el-form-item>
            </el-col>
          </el-row>
        </section>

        <section class="pvp-form-section">
          <div class="pvp-form-section__head">
            <strong>参赛与出题</strong>
            <span>选择参赛学生和本场出题单元。</span>
          </div>
          <el-row :gutter="14">
            <el-col :xs="24" :md="12">
              <el-form-item label="参赛学生">
                <el-select
                  v-model="pvpStore.roomForm.member_user_ids"
                  multiple
                  filterable
                  collapse-tags
                  collapse-tags-tooltip
                  :loading="pvpStore.selectorLoading"
                  popper-class="admin-pvp-select-popper"
                  placeholder="请选择学生"
                >
                  <el-option
                    v-for="student in pvpStore.sortedStudents"
                    :key="student.user_id"
                    :label="`${student.nickname} (${student.username})`"
                    :value="student.user_id"
                  >
                    <span class="select-option-title">{{ student.nickname }}</span>
                    <span class="select-option-meta">{{ student.username }} · ID {{ student.user_id }}{{ student.is_active ? '' : ' · 已禁用' }}</span>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :xs="24" :md="12">
              <el-form-item label="出题单元">
                <el-select
                  v-model="pvpStore.roomForm.question_unit_ids"
                  multiple
                  filterable
                  collapse-tags
                  collapse-tags-tooltip
                  :loading="pvpStore.selectorLoading"
                  popper-class="admin-pvp-select-popper"
                  placeholder="请选择单元"
                >
                  <el-option
                    v-for="unit in pvpStore.units"
                    :key="unit.id"
                    :label="unit.name"
                    :value="unit.id"
                  >
                    <span class="select-option-title">{{ unit.name }}</span>
                    <span class="select-option-meta">{{ unit.subtitle || '无副标题' }} · {{ unitLevelCount(unit) }} 个关卡 · ID {{ unit.id }}</span>
                  </el-option>
                </el-select>
              </el-form-item>
            </el-col>
          </el-row>
        </section>
      </el-form>

      <template #footer>
        <el-button @click="formVisible = false">取消</el-button>
        <el-button type="primary" :loading="pvpStore.saving" @click="saveRoom">保存房间</el-button>
      </template>
    </el-dialog>
  </section>
</template>

<style scoped>
.admin-page__heading,
.admin-page__actions {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.admin-page__heading {
  margin-bottom: 18px;
}

.admin-page__heading p {
  margin: 0 0 4px;
  color: var(--admin-primary);
  font-size: 13px;
}

.admin-page__heading h2 {
  margin: 0;
  font-size: 26px;
}

.admin-page__alert {
  margin-bottom: 16px;
}

.pvp-summary {
  margin-bottom: 16px;
  row-gap: 16px;
}

.pvp-kpi,
.admin-pvp-card {
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius);
}

.admin-pvp-card :deep(.el-card__body) {
  max-height: calc(100dvh - 360px);
  overflow: auto;
  scrollbar-gutter: stable;
}

.pvp-kpi span,
.pvp-kpi strong {
  display: block;
}

.pvp-kpi span {
  color: var(--admin-muted);
  font-size: 13px;
}

.pvp-kpi strong {
  margin-top: 8px;
  color: var(--admin-text);
  font-size: 28px;
}

.pvp-kpi small {
  display: block;
  margin-top: 8px;
  color: var(--admin-muted);
  font-size: 12px;
}

.pvp-kpi--meta strong {
  font-size: 18px;
}

.pvp-card-head {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.pvp-card-head strong,
.pvp-card-head span {
  display: block;
}

.pvp-card-head strong {
  color: var(--admin-text);
  font-size: 16px;
}

.pvp-card-head span {
  margin-top: 4px;
  color: var(--admin-muted);
  font-size: 13px;
}

.room-cell {
  display: grid;
  gap: 4px;
}

.room-cell strong {
  color: var(--admin-text);
}

.room-cell span {
  color: var(--admin-muted);
  font-size: 12px;
}

.pvp-status-cell,
.pvp-member-count,
.room-member-cell {
  display: grid;
  gap: 4px;
}

.pvp-status-cell span,
.pvp-member-count span,
.room-member-cell span {
  color: var(--admin-muted);
  font-size: 12px;
}

.pvp-member-count strong,
.room-member-cell strong {
  color: var(--admin-text);
}

:deep(.el-table__row.is-selected-room > .el-table__cell) {
  background: rgba(37, 99, 235, 0.08);
}

.room-detail {
  display: grid;
  gap: 16px;
}

.room-detail__profile,
.room-detail__actions {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: space-between;
}

.room-detail__profile strong,
.room-detail__profile span {
  display: block;
}

.room-detail__profile strong {
  color: var(--admin-text);
  font-size: 20px;
}

.room-detail__profile span {
  color: var(--admin-muted);
}

.room-detail__metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.room-detail__metrics article {
  padding: 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-surface-soft);
}

.room-detail__metrics span,
.room-detail__metrics strong {
  display: block;
}

.room-detail__metrics span {
  color: var(--admin-muted);
  font-size: 12px;
}

.room-detail__metrics strong {
  margin-top: 6px;
  color: var(--admin-text);
  font-size: 18px;
  line-height: 1.35;
  word-break: break-word;
}

.room-detail__tabs {
  margin-top: 2px;
}

.room-sync-meta {
  display: grid;
  gap: 6px;
  margin-bottom: 14px;
  padding: 12px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-surface-soft);
  color: var(--admin-muted);
  font-size: 13px;
}

.room-log-list {
  display: grid;
  max-height: 280px;
  gap: 10px;
  overflow: auto;
}

.room-log-list article {
  padding: 12px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
}

.room-log-list p {
  margin: 0 0 6px;
}

.room-log-list span,
.select-option-meta {
  font-size: 12px;
}

.pvp-room-form {
  display: grid;
  gap: 14px;
}

.pvp-form-section {
  padding: 16px;
  border: 1px solid var(--admin-border);
  border-radius: 16px;
  background: var(--admin-surface-soft);
}

.pvp-form-section__head {
  display: grid;
  gap: 4px;
  margin-bottom: 14px;
}

.pvp-form-section__head strong {
  color: var(--admin-text);
  font-size: 15px;
}

.pvp-form-section__head span {
  color: var(--admin-muted);
  font-size: 12px;
  line-height: 1.6;
}

.pvp-room-form :deep(.el-form-item) {
  margin-bottom: 14px;
}

.pvp-room-form :deep(.el-form-item:last-child) {
  margin-bottom: 0;
}

.pvp-room-form :deep(.el-input__wrapper),
.pvp-room-form :deep(.el-select__wrapper) {
  min-height: 42px;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 0 0 1px var(--admin-border) inset;
}

.pvp-room-form :deep(.el-input__wrapper.is-focus),
.pvp-room-form :deep(.el-select__wrapper.is-focused) {
  box-shadow:
    0 0 0 1px var(--admin-primary) inset,
    0 0 0 3px rgba(37, 99, 235, 0.12);
}

.pvp-room-form :deep(.el-input-number .el-input__wrapper) {
  min-height: 42px;
  border-radius: 0;
  box-shadow: none;
}

.pvp-room-form :deep(.el-input-number) {
  overflow: hidden;
  border: 1px solid var(--admin-border);
  border-radius: 14px;
  background: #ffffff;
}

.pvp-room-form :deep(.el-input-number.is-controls-right),
.pvp-room-form :deep(.el-input-number.is-without-controls) {
  border-radius: 14px;
}

.pvp-room-form :deep(.el-input-number .el-input__inner) {
  font-weight: 700;
}

.el-select,
.el-input-number {
  width: 100%;
}

@media (max-width: 760px) {
  .admin-page__heading,
  .pvp-card-head,
  .room-detail__profile,
  .room-detail__actions {
    align-items: flex-start;
    flex-direction: column;
  }

  .room-detail__metrics {
    grid-template-columns: 1fr;
  }

  .admin-pvp-card :deep(.el-card__body) {
    max-height: calc(100dvh - 320px);
  }
}
</style>
