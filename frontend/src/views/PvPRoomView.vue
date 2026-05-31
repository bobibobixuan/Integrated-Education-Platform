<script setup lang="ts">
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useAuthStore } from '@/stores/auth'
import { usePvpStore } from '@/stores/pvp'

const auth = useAuthStore()
const router = useRouter()
const pvp = usePvpStore()
let pollTimer: ReturnType<typeof setInterval> | null = null

const room = computed(() => pvp.room)
const myMember = computed(() => room.value?.members.find(member => member.user_id === auth.user?.id) || null)
const rankedMembers = computed(() => [...(room.value?.members || [])].sort((a, b) => b.battle_power - a.battle_power))
const countdownLabel = computed(() => {
  const seconds = pvp.countdownSeconds
  if (seconds <= 0) return '即将开始'
  return `${seconds} 秒后开始`
})
const canEnterBattle = computed(() => room.value?.status === 'running')
const leaveBlocked = computed(() => room.value?.status === 'countdown' || room.value?.status === 'running')

function statusLabel(status: string) {
  switch (status) {
    case 'waiting':
      return '等待中'
    case 'countdown':
      return '倒计时'
    case 'running':
      return '进行中'
    case 'finished':
      return '已结束'
    default:
      return status || '未知'
  }
}

watch(() => room.value?.status, (status) => {
  if (status === 'running') {
    router.replace('/pvp/battle')
  }
})

onMounted(() => {
  pvp.setupWsHandlers()
  void pvp.fetchMyRoom()
  pollTimer = setInterval(() => void pvp.fetchMyRoom(), 5000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<template>
  <AppShell>
    <div class="room-page">
      <!-- Error Banner -->
      <div v-if="pvp.error" class="error-banner">
        <span>{{ pvp.error }}</span>
        <button type="button" class="error-close" @click="pvp.error = ''">关闭</button>
      </div>

      <!-- No Room State -->
      <section v-if="!room" class="no-room-state">
        <div class="no-room-content">
          <h2 class="no-room-title">你当前不在任何房间中</h2>
          <p class="no-room-desc">回到大厅后可以看当前开放房间，真正加入仍由教师端控制。</p>
          <button type="button" class="btn-lobby" @click="router.push('/pvp')">返回大厅</button>
        </div>
      </section>

      <!-- Room Exists -->
      <template v-else>
        <div class="room-layout">
          <!-- Left Column -->
          <div class="room-left">
            <!-- Room Summary Card -->
            <section class="card room-summary-card">
              <div class="summary-left">
                <div class="summary-label">房间信息</div>
                <h1 class="room-number">{{ room.title }}</h1>
                <div class="summary-meta">
                  <span class="status-pill">{{ statusLabel(room.status) }}</span>
                  <span class="member-count">{{ room.member_count }} / {{ room.group_size }} 人</span>
                </div>
              </div>
              <div class="summary-right">
                <div class="summary-label">对战设置</div>
                <div class="battle-settings">
                  <span>{{ room.question_count }} 题</span>
                  <span class="settings-sep">·</span>
                  <span>限时 {{ room.battle_time_limit_seconds }}s</span>
                  <span class="settings-sep">·</span>
                  <span>{{ room.ranking_metric === 'battle_power' ? '战斗力' : room.ranking_metric }}</span>
                </div>
                <div class="battle-mode">{{ room.mode === 'pvp' ? 'PVP 对战' : room.mode }}</div>
              </div>
            </section>

            <!-- Room Members Card -->
            <section class="card room-members-card">
              <div class="card-header">
                <h3 class="card-title">房间成员</h3>
                <p class="card-subtitle">当前房间成员与准备状态</p>
              </div>

              <div v-if="room.status === 'countdown'" class="countdown-strip">
                <div class="countdown-strip-text">
                  <strong>全员已准备，房间即将开战</strong>
                  <span>倒计时结束后自动进入对战</span>
                </div>
                <div class="countdown-strip-badge">{{ pvp.countdownSeconds || 0 }}</div>
              </div>

              <div class="member-list">
                <div
                  v-for="member in room.members"
                  :key="member.user_id"
                  class="member-row"
                >
                  <div class="member-avatar member-avatar--filled">{{ member.nickname.slice(0, 1) }}</div>
                  <div class="member-info">
                    <span class="member-name">{{ member.nickname }}</span>
                    <span class="member-seat">{{ member.seat_order }} 号位</span>
                  </div>
                  <span class="member-status" :class="{ 'member-status--ready': member.is_ready }">
                    {{ member.is_ready ? '已准备' : '未准备' }}
                  </span>
                </div>
                <div
                  v-for="i in (room.group_size - room.members.length)"
                  :key="'empty-' + i"
                  class="member-row member-row--empty"
                >
                  <div class="member-avatar member-avatar--empty">
                    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="rgba(60,60,67,0.36)" stroke-width="1.5" stroke-linecap="round">
                      <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
                      <circle cx="9" cy="7" r="4" />
                      <line x1="19" y1="8" x2="19" y2="14" />
                      <line x1="22" y1="11" x2="16" y2="11" />
                    </svg>
                  </div>
                  <div class="member-info">
                    <span class="member-name member-name--empty">等待玩家加入</span>
                    <span class="member-seat">{{ (room.members.length + i) }} 号位</span>
                  </div>
                  <span class="member-status member-status--empty">空位</span>
                </div>
              </div>

              <div v-if="room.logs?.length" class="logs-section">
                <h4 class="logs-title">最近播报</h4>
                <div class="logs-list">
                  <div v-for="log in room.logs.slice(-6)" :key="log.id" class="log-item">{{ log.message }}</div>
                </div>
              </div>
            </section>
          </div>

          <!-- Right Column -->
          <div class="room-right">
            <!-- My Status Card -->
            <section class="card my-status-card">
              <h3 class="card-title">我的状态</h3>
              <div v-if="myMember" class="status-grid">
                <div class="status-cell">
                  <span class="status-label">座位</span>
                  <strong class="status-value">{{ myMember.seat_order }}</strong>
                </div>
                <div class="status-cell">
                  <span class="status-label">名次</span>
                  <strong class="status-value">{{ myMember.rank }}</strong>
                </div>
                <div class="status-cell">
                  <span class="status-label">战力</span>
                  <strong class="status-value">{{ myMember.battle_power }}</strong>
                </div>
                <div class="status-cell">
                  <span class="status-label">对 / 错</span>
                  <strong class="status-value">{{ myMember.correct_count }} / {{ myMember.wrong_count }}</strong>
                </div>
              </div>
            </section>

            <!-- Action Card -->
            <section class="card action-card" v-if="myMember">
              <div class="action-status">
                当前状态：<strong>{{ myMember.is_ready ? '已准备' : '未准备' }}</strong>
              </div>
              <div v-if="leaveBlocked" class="action-lock-tip">
                对战进入倒计时或开战后不能退出；如果离开大厅，会自动回到答题界面。
              </div>
              <button
                type="button"
                class="btn-primary"
                :disabled="pvp.loading"
                @click="pvp.toggleReady()"
              >
                {{ myMember.is_ready ? '取消准备' : '准备' }}
              </button>
              <button
                v-if="canEnterBattle"
                type="button"
                class="btn-primary"
                @click="router.push('/pvp/battle')"
              >
                进入对战
              </button>
              <button
                v-else-if="room.status === 'countdown'"
                type="button"
                class="btn-primary"
                disabled
              >
                {{ countdownLabel }}
              </button>
              <button
                type="button"
                class="btn-danger"
                :disabled="pvp.loading || !pvp.canLeaveRoom"
                @click="pvp.doLeaveRoom()"
              >
                {{ pvp.canLeaveRoom ? '退出房间' : '当前不可退出' }}
              </button>
            </section>

            <!-- Ranking Card -->
            <section class="card ranking-card">
              <h3 class="card-title">实时排名</h3>
              <div class="ranking-table">
                <div class="ranking-header">
                  <span class="rh-rank">#</span>
                  <span class="rh-name">玩家</span>
                  <span class="rh-power">战力</span>
                  <span class="rh-score">对/错</span>
                </div>
                <div
                  v-for="member in rankedMembers"
                  :key="member.user_id"
                  class="ranking-row"
                  :class="{ 'ranking-row--me': member.user_id === auth.user?.id }"
                >
                  <span class="rr-rank">{{ member.rank }}</span>
                  <span class="rr-name">{{ member.nickname }}</span>
                  <span class="rr-power">{{ member.battle_power }}</span>
                  <span class="rr-score">{{ member.correct_count }}/{{ member.wrong_count }}</span>
                </div>
              </div>
            </section>
          </div>
        </div>
      </template>
    </div>
  </AppShell>
</template>

<style scoped>
/* ── Page Shell ── */
.room-page {
  padding: 0;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ── Error Banner ── */
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  margin-bottom: 20px;
  border-radius: 14px;
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.2);
  color: #FF3B30;
  font-size: 14px;
  font-weight: 600;
}

.error-close {
  flex-shrink: 0;
  border: none;
  background: rgba(255, 59, 48, 0.1);
  color: #FF3B30;
  font-size: 13px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
}

.error-close:hover {
  background: rgba(255, 59, 48, 0.18);
}

/* ── No Room State ── */
.no-room-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
}

.no-room-content {
  text-align: center;
  max-width: 400px;
}

.no-room-title {
  margin: 0 0 12px;
  font-size: 22px;
  font-weight: 800;
  color: #000000;
}

.no-room-desc {
  margin: 0 0 28px;
  font-size: 15px;
  color: rgba(60, 60, 67, 0.6);
  line-height: 1.5;
}

.btn-lobby {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 44px;
  padding: 0 28px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  border-radius: 12px;
  background: #FFFFFF;
  color: #007AFF;
  font-size: 16px;
  font-weight: 700;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}

.btn-lobby:hover {
  background: rgba(0, 0, 0, 0.04);
}

.btn-lobby:active {
  transform: scale(0.98);
}

/* ── Room Layout ── */
.room-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 380px);
  gap: 20px;
  align-items: start;
}

.room-left,
.room-right {
  display: grid;
  gap: 18px;
}

/* ── Card Base ── */
.card {
  background: #FFFFFF;
  border-radius: 20px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.03);
}

.card-title {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 800;
  color: #000000;
}

.card-subtitle {
  margin: 0;
  font-size: 13px;
  color: rgba(60, 60, 67, 0.6);
}

.card-header {
  margin-bottom: 18px;
}

/* ── Room Summary Card ── */
.room-summary-card {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: 24px;
  padding: 28px 32px;
}

.summary-label {
  font-size: 12px;
  font-weight: 800;
  color: rgba(60, 60, 67, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.06em;
  margin-bottom: 8px;
}

.room-number {
  margin: 0 0 14px;
  font-size: 38px;
  font-weight: 800;
  color: #000000;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.summary-meta {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border-radius: 10px;
  background: rgba(52, 199, 89, 0.14);
  color: #34C759;
  font-size: 13px;
  font-weight: 800;
}

.member-count {
  font-size: 15px;
  color: rgba(60, 60, 67, 0.6);
  font-weight: 600;
}

.summary-right {
  text-align: right;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.battle-settings {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 16px;
  font-weight: 700;
  color: #000000;
  margin-top: 4px;
}

.settings-sep {
  color: rgba(60, 60, 67, 0.2);
  font-weight: 400;
}

.battle-mode {
  margin-top: 10px;
  font-size: 13px;
  color: rgba(60, 60, 67, 0.6);
  font-weight: 600;
}

/* ── Room Members Card ── */
.room-members-card {
  padding: 28px 32px;
}

.countdown-strip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px 20px;
  margin-bottom: 20px;
  border-radius: 14px;
  background: rgba(255, 149, 0, 0.08);
  border: 1px solid rgba(255, 149, 0, 0.18);
}

.countdown-strip-text strong {
  display: block;
  font-size: 15px;
  font-weight: 800;
  color: #000000;
  margin-bottom: 4px;
}

.countdown-strip-text span {
  font-size: 13px;
  color: rgba(60, 60, 67, 0.6);
}

.countdown-strip-badge {
  flex-shrink: 0;
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 14px;
  background: #FF9500;
  color: #FFFFFF;
  font-size: 24px;
  font-weight: 900;
  letter-spacing: -0.02em;
}

/* ── Member List ── */
.member-list {
  display: grid;
}

.member-row {
  display: grid;
  grid-template-columns: 48px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  padding: 16px 0;
  border-bottom: 1px solid rgba(60, 60, 67, 0.12);
}

.member-row:last-child {
  border-bottom: none;
}

.member-row--empty {
  opacity: 0.55;
}

.member-avatar {
  width: 48px;
  height: 48px;
  border-radius: 999px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.member-avatar--filled {
  background: rgba(0, 122, 255, 0.12);
  color: #007AFF;
  font-size: 18px;
  font-weight: 800;
}

.member-avatar--empty {
  background: rgba(60, 60, 67, 0.08);
}

.member-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}

.member-name {
  font-size: 17px;
  font-weight: 700;
  color: #000000;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.member-name--empty {
  color: rgba(60, 60, 67, 0.36);
}

.member-seat {
  font-size: 13px;
  color: rgba(60, 60, 67, 0.6);
}

.member-status {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 800;
  background: rgba(255, 149, 0, 0.1);
  color: #FF9500;
}

.member-status--ready {
  background: rgba(52, 199, 89, 0.12);
  color: #34C759;
}

.member-status--empty {
  background: rgba(60, 60, 67, 0.06);
  color: rgba(60, 60, 67, 0.36);
}

/* ── Logs ── */
.logs-section {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid rgba(60, 60, 67, 0.12);
}

.logs-title {
  margin: 0 0 12px;
  font-size: 16px;
  font-weight: 800;
  color: #000000;
}

.logs-list {
  display: grid;
  gap: 8px;
}

.log-item {
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(60, 60, 67, 0.04);
  font-size: 13px;
  color: rgba(60, 60, 67, 0.6);
  line-height: 1.4;
}

/* ── My Status Card ── */
.my-status-card {
  padding: 24px;
}

.status-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  margin-top: 18px;
}

.status-cell {
  padding: 18px 14px;
  text-align: center;
  border: 1px solid rgba(60, 60, 67, 0.12);
  border-radius: 12px;
  margin: -1px 0 0 -1px;
}

.status-label {
  display: block;
  font-size: 12px;
  color: rgba(60, 60, 67, 0.6);
  font-weight: 600;
  margin-bottom: 6px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.status-value {
  display: block;
  font-size: 22px;
  font-weight: 800;
  color: #000000;
}

/* ── Action Card ── */
.action-card {
  padding: 24px;
  display: grid;
  gap: 12px;
}

.action-status {
  font-size: 14px;
  color: rgba(60, 60, 67, 0.6);
  margin-bottom: 4px;
}

.action-status strong {
  color: #000000;
}

.action-lock-tip {
  padding: 12px 14px;
  border-radius: 10px;
  background: rgba(255, 149, 0, 0.08);
  border: 1px solid rgba(255, 149, 0, 0.18);
  color: #9a6700;
  font-size: 13px;
  line-height: 1.5;
 }

.btn-primary {
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 12px;
  background: #007AFF;
  color: #FFFFFF;
  font-size: 18px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s, opacity 0.15s;
}

.btn-primary:hover:not(:disabled) {
  background: #006EE6;
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

.btn-danger {
  width: 100%;
  height: 44px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(255, 59, 48, 0.45);
  border-radius: 12px;
  background: rgba(255, 59, 48, 0.06);
  color: #FF3B30;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s, opacity 0.15s;
}

.btn-danger:hover:not(:disabled) {
  background: rgba(255, 59, 48, 0.1);
}

.btn-danger:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-danger:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* ── Ranking Card ── */
.ranking-card {
  padding: 24px;
}

.ranking-table {
  margin-top: 18px;
}

.ranking-header {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) 60px 50px;
  gap: 8px;
  padding: 0 0 10px;
  border-bottom: 1px solid rgba(60, 60, 67, 0.12);
  font-size: 12px;
  font-weight: 700;
  color: rgba(60, 60, 67, 0.6);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.ranking-row {
  display: grid;
  grid-template-columns: 36px minmax(0, 1fr) 60px 50px;
  gap: 8px;
  padding: 12px 0;
  border-bottom: 1px solid rgba(60, 60, 67, 0.08);
  font-size: 14px;
  align-items: center;
}

.ranking-row:last-child {
  border-bottom: none;
}

.ranking-row--me {
  background: rgba(0, 122, 255, 0.04);
  border-radius: 10px;
  padding-left: 8px;
  padding-right: 8px;
  margin: 0 -8px;
}

.rr-rank {
  font-weight: 800;
  color: rgba(60, 60, 67, 0.6);
}

.rr-name {
  font-weight: 700;
  color: #000000;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rr-power {
  font-weight: 800;
  color: #007AFF;
  text-align: right;
}

.rr-score {
  font-size: 13px;
  color: rgba(60, 60, 67, 0.6);
  text-align: right;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .room-layout {
    grid-template-columns: 1fr;
  }

  .room-summary-card {
    grid-template-columns: 1fr;
    padding: 22px;
    gap: 18px;
  }

  .summary-right {
    align-items: flex-start;
    text-align: left;
  }

  .room-number {
    font-size: 30px;
  }

  .card {
    padding: 22px;
  }

  .room-members-card {
    padding: 22px;
  }
}

@media (max-width: 480px) {
  .status-grid {
    grid-template-columns: 1fr;
  }

  .summary-meta {
    flex-wrap: wrap;
  }

  .battle-settings {
    flex-wrap: wrap;
  }
}
</style>
