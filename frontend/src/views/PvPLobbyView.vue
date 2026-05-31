<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { getMyRoom, listRooms, createRoom, joinRoom, type StudentCreateRoomIn } from '@/api/pvp'
import { getUnits } from '@/api/admin'
import { useAuthStore } from '@/stores/auth'
import type { PvpRoom, UnitOut } from '@/types/api'

const auth = useAuthStore()
const router = useRouter()
const rooms = ref<PvpRoom[]>([])
const myRoom = ref<PvpRoom | null>(null)
const loading = ref(false)
const error = ref('')
const showHistory = ref(false)
const expandedHistoryRoomId = ref<number | null>(null)
const showCreateForm = ref(false)
const creating = ref(false)
const createForm = ref<StudentCreateRoomIn>({
  title: '', description: '', group_size: 4,
  question_unit_ids: [], question_count: 10,
  battle_time_limit_seconds: 0,
})
const availableUnits = ref<UnitOut[]>([])

const activeRooms = computed(() =>
  rooms.value.filter(r => r.status !== 'finished')
)
const finishedRooms = computed(() =>
  rooms.value.filter(r => r.status === 'finished')
)
const recommendedRoom = computed(() => {
  if (myRoom.value) return myRoom.value
  return activeRooms.value.find(room => ['waiting', 'countdown', 'running'].includes(room.status)) || null
})

function statusLabel(status: string) {
  switch (status) {
    case 'waiting': return '等待中'
    case 'countdown': return '倒计时'
    case 'running': return '进行中'
    case 'finished': return '已结束'
    default: return status || '未知'
  }
}

function statusClass(status: string) {
  if (status === 'running') return 'status-chip status-chip--danger'
  if (status === 'countdown') return 'status-chip status-chip--warn'
  if (status === 'waiting') return 'status-chip status-chip--ok'
  return 'status-chip status-chip--neutral'
}

function rankLabel(rank: number) {
  if (rank === 1) return 'TOP1'
  if (rank === 2) return 'TOP2'
  if (rank === 3) return 'TOP3'
  return `#${rank}`
}

async function loadLobby() {
  if (!auth.token) return
  loading.value = true
  error.value = ''
  try {
    const [roomList, myRoomRes] = await Promise.all([
      listRooms(auth.token),
      getMyRoom(auth.token),
    ])
    rooms.value = roomList
    myRoom.value = myRoomRes.room
    if (myRoomRes.room?.status === 'running') {
      router.replace('/pvp/battle')
      return
    }
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败。'
  } finally {
    loading.value = false
  }
}

watch(myRoom, (room) => {
  if (room?.status === 'running') {
    router.replace('/pvp/battle')
  }
})

function openMyFlow() {
  if (!myRoom.value) return
  router.push(myRoom.value.status === 'running' ? '/pvp/battle' : '/pvp/room')
}

function toggleHistoryRoom(roomId: number) {
  expandedHistoryRoomId.value = expandedHistoryRoomId.value === roomId ? null : roomId
}

async function openCreateForm() {
  showCreateForm.value = true
  if (availableUnits.value.length === 0) {
    try {
      availableUnits.value = await getUnits(auth.token!)
    } catch { /* units failed, user can still proceed */ }
  }
}

async function doCreateRoom() {
  if (!createForm.value.title.trim()) { error.value = '请输入房间名称'; return }
  if (createForm.value.question_unit_ids.length === 0) { error.value = '至少选择一个出题单元'; return }
  creating.value = true
  error.value = ''
  try {
    await createRoom(createForm.value, auth.token!)
    showCreateForm.value = false
    createForm.value = { title: '', description: '', group_size: 4, question_unit_ids: [], question_count: 10, battle_time_limit_seconds: 0 }
    await loadLobby()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '创建房间失败。'
  } finally {
    creating.value = false
  }
}

async function doJoinRoom(roomId: number) {
  error.value = ''
  try {
    await joinRoom(roomId, auth.token!)
    await loadLobby()
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加入房间失败。'
  }
}

function toggleUnitInForm(unitId: number) {
  const ids = createForm.value.question_unit_ids
  if (ids.includes(unitId)) {
    createForm.value.question_unit_ids = ids.filter(id => id !== unitId)
  } else {
    createForm.value.question_unit_ids = [...ids, unitId]
  }
}

onMounted(() => {
  void loadLobby()
})
</script>

<template>
  <AppShell>
    <div class="lobby-page">
      <!-- Error Banner -->
      <div v-if="error" class="lobby-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ error }}</span>
        <button type="button" class="lobby-error-close" @click="error = ''">✕</button>
      </div>

      <!-- Hero Card -->
      <section class="lobby-hero">
        <div class="lobby-hero-left">
          <h1 class="lobby-title">竞技大厅</h1>
          <p class="lobby-desc">查看当前房间状态，进入准备或直接开始对战。</p>
          <div class="lobby-hero-status">
            <span>当前状态</span>
            <strong>{{ myRoom ? `已加入「${myRoom.title}」` : recommendedRoom ? `推荐「${recommendedRoom.title}」` : '未加入房间' }}</strong>
          </div>
        </div>
        <div class="lobby-hero-right">
          <button v-if="myRoom" type="button" class="btn-primary" @click="openMyFlow">
            {{ myRoom.status === 'running' ? '进入对战' : '打开我的房间' }}
          </button>
          <template v-else>
            <button type="button" class="btn-primary" @click="openCreateForm">创建房间</button>
            <button type="button" class="btn-outline" @click="loadLobby">刷新大厅</button>
          </template>
          <button v-if="finishedRooms.length > 0" type="button" class="btn-outline" @click="showHistory = !showHistory">
            {{ showHistory ? '收起历史' : `对战历史 (${finishedRooms.length})` }}
          </button>
        </div>
      </section>

      <!-- Loading -->
      <div v-if="loading && rooms.length === 0" class="lobby-loading">正在同步竞技大厅…</div>

      <!-- Main Content -->
      <template v-else>
        <div class="lobby-layout">
          <!-- Left: Room List -->
          <div class="lobby-left">
            <div class="lobby-section-head">
              <h2>开放房间</h2>
              <span class="lobby-count">{{ activeRooms.length }} 个</span>
            </div>

            <div v-if="activeRooms.length > 0" class="room-list">
              <article v-for="room in activeRooms" :key="room.id" class="room-card" :class="{ 'room-card--mine': room.id === myRoom?.id }">
                <div class="room-card-head">
                  <div>
                    <h4>{{ room.title }}</h4>
                    <p>{{ room.description || '教师配置的房间，用于课堂对战或分组练习。' }}</p>
                  </div>
                  <span class="chip" :class="statusClass(room.status)">{{ statusLabel(room.status) }}</span>
                </div>
                <div class="room-card-meta">
                  <span>{{ room.member_count }}/{{ room.group_size }} 人</span>
                  <span>{{ room.ready_count }} 已准备</span>
                  <span>{{ room.question_count }} 题</span>
                  <span v-if="room.battle_time_limit_seconds > 0">限时 {{ room.battle_time_limit_seconds }}s</span>
                  <span v-else>不限时</span>
                </div>
                <div class="room-card-foot">
                  <button v-if="room.id === myRoom?.id" type="button" class="btn-outline-sm" @click="openMyFlow">
                    {{ room.status === 'running' ? '进入对战' : '进入房间' }}
                  </button>
                  <button v-else-if="room.status === 'waiting' && room.member_count < room.group_size" type="button" class="btn-outline-sm" @click="doJoinRoom(room.id)">
                    加入房间
                  </button>
                  <span v-else class="room-card-tag">只读预览</span>
                  <span v-if="room.id === myRoom?.id" class="room-card-tag room-card-tag--mine">我的房间</span>
                </div>
              </article>
            </div>
            <div v-else-if="!myRoom" class="lobby-empty">暂无开放房间，等待教师创建。</div>
          </div>

          <!-- Right: My Room Panel -->
          <aside class="lobby-right">
            <div v-if="myRoom" class="side-card">
              <h3 class="side-card-title">我的房间</h3>
              <div class="side-room-name">{{ myRoom.title }}</div>
              <p class="side-room-desc">{{ myRoom.description || '教师端已把你加入当前房间。' }}</p>
              <div class="side-room-meta">
                <span class="chip" :class="statusClass(myRoom.status)">{{ statusLabel(myRoom.status) }}</span>
                <span>{{ myRoom.member_count }}/{{ myRoom.group_size }} 人</span>
                <span>{{ myRoom.question_count }} 题</span>
              </div>
              <button type="button" class="btn-primary btn-full" @click="openMyFlow">
                {{ myRoom.status === 'running' ? '进入对战' : '进入房间' }}
              </button>
            </div>
            <div v-else class="side-card side-card--empty">
              <h3 class="side-card-title">我的房间</h3>
              <p class="side-card-empty">暂无房间，等待教师分配或主动创建。</p>
              <button type="button" class="btn-outline btn-full" @click="openCreateForm">创建房间</button>
            </div>
          </aside>
        </div>

        <!-- Battle History -->
        <template v-if="showHistory && finishedRooms.length > 0">
          <div class="history-head">
            <h3>对战历史</h3>
            <span class="lobby-count">{{ finishedRooms.length }} 场</span>
          </div>
          <section class="history-grid">
            <article v-for="room in finishedRooms" :key="room.id" class="history-card" @click="toggleHistoryRoom(room.id)">
              <div class="history-card-top">
                <strong>{{ room.title }}</strong>
                <span>{{ room.member_count }} 人 · {{ room.question_count }} 题</span>
                <span class="history-chevron">{{ expandedHistoryRoomId === room.id ? '▲' : '▼' }}</span>
              </div>
              <div v-if="expandedHistoryRoomId === room.id" class="history-detail" @click.stop>
                <div class="history-detail-row" v-for="member in room.members" :key="member.user_id" :class="{ 'is-me': myRoom && member.user_id === auth.user?.id }">
                  <span class="hd-rank" :class="{ 'hd-rank--top': member.rank <= 3 }">{{ rankLabel(member.rank) }}</span>
                  <span class="hd-name">{{ member.nickname }}</span>
                  <span class="hd-stat">战力 {{ member.battle_power }}</span>
                  <span class="hd-stat">对{{ member.correct_count }} 错{{ member.wrong_count }}</span>
                  <span class="hd-stat">{{ member.accuracy }}%</span>
                </div>
              </div>
            </article>
          </section>
        </template>
      </template>
    </div>

    <!-- Create Room Modal -->
    <div v-if="showCreateForm" class="modal-overlay" @click.self="showCreateForm = false">
      <div class="modal-card">
        <div class="modal-head">
          <h3>创建竞技房间</h3>
          <button type="button" class="modal-close" @click="showCreateForm = false">✕</button>
        </div>
        <p class="modal-desc">创建一个新的对战房间，你将成为房主和第一个成员。</p>

        <div class="modal-form">
          <input v-model="createForm.title" type="text" placeholder="房间名称" class="modal-input" />
          <div class="modal-row">
            <input v-model.number="createForm.group_size" type="number" min="2" max="12" placeholder="人数上限" class="modal-input" />
            <input v-model.number="createForm.question_count" type="number" min="2" max="50" placeholder="题数" class="modal-input" />
          </div>
          <input v-model.number="createForm.battle_time_limit_seconds" type="number" min="0" max="3600" placeholder="总时限（秒，0=不限时）" class="modal-input" />
          <input v-model="createForm.description" type="text" placeholder="房间说明（可选）" class="modal-input" />

          <div class="modal-units">
            <p class="modal-units-label">出题单元（至少选一个）</p>
            <div class="modal-units-grid">
              <label v-for="unit in availableUnits" :key="unit.id" class="unit-chip" :class="{ 'unit-chip--on': createForm.question_unit_ids.includes(unit.id) }">
                <input type="checkbox" :checked="createForm.question_unit_ids.includes(unit.id)" @change="toggleUnitInForm(unit.id)" />
                <span>{{ unit.name }}</span>
              </label>
            </div>
          </div>
        </div>

        <div v-if="error" class="modal-err">{{ error }}</div>

        <div class="modal-foot">
          <button type="button" class="btn-ghost" @click="showCreateForm = false">取消</button>
          <button type="button" class="btn-primary" :disabled="creating" @click="doCreateRoom">
            {{ creating ? '创建中…' : '创建房间' }}
          </button>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
/* ── Shell ── */
.lobby-page {
  display: grid;
  gap: 18px;
  max-width: 1120px;
  margin: 0 auto;
  width: 100%;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
}


/* ── Error Banner ── */
.lobby-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.35);
  color: #FF3B30;
  font-size: 14px;
}
.lobby-error span { flex: 1; }
.lobby-error-close {
  width: 24px; height: 24px;
  display: flex; align-items: center; justify-content: center;
  border: none; border-radius: 6px;
  background: rgba(255,59,48,0.12); color: #FF3B30;
  font-size: 12px; cursor: pointer;
}

/* ── Hero ── */
.lobby-hero {
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  padding: 28px 32px;
  background: #FFFFFF; border-radius: 18px;
  border: 1px solid rgba(60,60,67,0.12);
  box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.05);
  flex-wrap: wrap;
}
.lobby-title { margin: 0 0 6px; font-size: 28px; font-weight: 700; color: #000; }
.lobby-desc { margin: 0 0 12px; font-size: 14px; color: rgba(60,60,67,0.6); }
.lobby-hero-status { display: flex; align-items: center; gap: 8px; font-size: 14px; }
.lobby-hero-status span { color: rgba(60,60,67,0.45); }
.lobby-hero-status strong { color: #000; }
.lobby-hero-right { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }

/* ── Loading ── */
.lobby-loading { text-align: center; padding: 32px; color: rgba(60,60,67,0.6); font-size: 14px; }

/* ── Layout ── */
.lobby-layout { display: grid; grid-template-columns: minmax(0,1fr) 340px; gap: 20px; align-items: start; }
.lobby-left { display: grid; gap: 16px; }

.lobby-section-head { display: flex; align-items: baseline; gap: 10px; }
.lobby-section-head h2 { margin: 0; font-size: 20px; font-weight: 700; color: #000; }
.lobby-count { font-size: 13px; color: rgba(60,60,67,0.45); }

/* ── Room List ── */
.room-list { display: grid; gap: 10px; }
.room-card {
  padding: 20px; border-radius: 14px;
  background: #FFFFFF; border: 1px solid rgba(60,60,67,0.12);
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
  transition: box-shadow 0.15s, border-color 0.15s;
}
.room-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.06); }
.room-card--mine { border-color: rgba(0,122,255,0.3); }
.room-card-head { display: flex; justify-content: space-between; gap: 12px; margin-bottom: 12px; }
.room-card-head h4 { margin: 0 0 4px; font-size: 17px; font-weight: 700; color: #000; }
.room-card-head p { margin: 0; font-size: 13px; color: rgba(60,60,67,0.6); line-height:1.4; }
.room-card-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 14px; font-size: 13px; color: rgba(60,60,67,0.6); }
.room-card-foot { display: flex; align-items: center; gap: 10px; }
.room-card-tag { font-size: 12px; color: rgba(60,60,67,0.45); }
.room-card-tag--mine { color: #007AFF; font-weight: 600; }

/* ── Status Chips ── */
.status-chip { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 8px; font-size: 12px; font-weight: 600; }
.status-chip--ok { background: rgba(52,199,89,0.12); color: #34C759; }
.status-chip--warn { background: rgba(255,149,0,0.1); color: #FF9500; }
.status-chip--danger { background: rgba(255,59,48,0.1); color: #FF3B30; }
.status-chip--neutral { background: rgba(60,60,67,0.06); color: rgba(60,60,67,0.6); }

/* ── Right Panel ── */
.lobby-right { display: grid; gap: 16px; }
.side-card {
  padding: 24px; border-radius: 18px;
  background: #FFFFFF; border: 1px solid rgba(60,60,67,0.12);
  box-shadow: 0 1px 2px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.05);
}
.side-card--empty { text-align: center; }
.side-card-title { margin: 0 0 8px; font-size: 18px; font-weight: 700; color: #000; }
.side-room-name { font-size: 17px; font-weight: 700; color: #000; margin-bottom: 4px; }
.side-room-desc { margin: 0 0 14px; font-size: 13px; color: rgba(60,60,67,0.6); line-height: 1.4; }
.side-room-meta { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 16px; font-size: 13px; color: rgba(60,60,67,0.6); align-items: center; }
.side-card-empty { margin: 0 0 16px; font-size: 14px; color: rgba(60,60,67,0.6); }

/* ── Empty State ── */
.lobby-empty { text-align: center; padding: 40px; color: rgba(60,60,67,0.45); font-size: 14px; }

/* ── History ── */
.history-head { display: flex; align-items: baseline; gap: 10px; margin: 8px 0 0; }
.history-head h3 { margin: 0; font-size: 18px; font-weight: 700; color: #000; }
.history-grid { display: grid; gap: 6px; margin-top: 12px; }
.history-card {
  padding: 14px 18px; border-radius: 12px;
  background: #FFFFFF; border: 1px solid rgba(60,60,67,0.12);
  cursor: pointer; transition: box-shadow 0.15s;
}
.history-card:hover { box-shadow: 0 2px 8px rgba(0,0,0,0.04); }
.history-card-top { display: flex; align-items: center; gap: 12px; font-size: 14px; }
.history-card-top strong { color: #000; }
.history-card-top span { color: rgba(60,60,67,0.6); }
.history-chevron { margin-left: auto; color: rgba(60,60,67,0.35); font-size: 12px; }
.history-detail { margin-top: 12px; padding-top: 10px; border-top: 1px solid rgba(60,60,67,0.12); display: grid; gap: 4px; }
.history-detail-row {
  display: flex; align-items: center; gap: 10px; padding: 6px 10px;
  border-radius: 8px; font-size: 13px;
}
.history-detail-row.is-me { background: rgba(0,122,255,0.06); }
.hd-rank { min-width: 40px; font-weight: 700; color: #000; }
.hd-rank--top { color:#007AFF; }
.hd-name { flex:1; color: #000; }
.hd-stat { font-size: 12px; color: rgba(60,60,67,0.6); white-space: nowrap; }

/* ── Buttons ── */
.btn-primary {
  height: 44px; padding: 0 24px; border: none; border-radius: 12px;
  background: #007AFF; color: #fff; font-size: 15px; font-weight: 600;
  font-family: inherit; cursor: pointer; white-space: nowrap;
  transition: background 0.15s, transform 0.1s;
}
.btn-primary:hover:not(:disabled) { background: #006EE6; }
.btn-primary:active:not(:disabled) { transform: scale(0.98); }
.btn-primary:disabled { opacity:0.5; cursor:not-allowed; }
.btn-outline {
  height: 44px; padding: 0 24px; border: 1px solid rgba(60,60,67,0.2); border-radius: 12px;
  background: #fff; color: #000; font-size: 15px; font-weight: 600;
  font-family: inherit; cursor: pointer; white-space: nowrap;
  transition: border-color 0.15s, background 0.15s;
}
.btn-outline:hover { border-color: #007AFF; background: rgba(0,122,255,0.04); }
.btn-outline-sm {
  height: 36px; padding: 0 16px; border: 1px solid rgba(0,122,255,0.45); border-radius: 10px;
  background: rgba(0,122,255,0.04); color: #007AFF; font-size: 14px; font-weight: 600;
  font-family: inherit; cursor: pointer;
  transition: background 0.15s;
}
.btn-outline-sm:hover { background: rgba(0,122,255,0.08); }
.btn-ghost {
  height: 44px; padding: 0 20px; border: none; border-radius: 12px;
  background: transparent; color: rgba(60,60,67,0.6); font-size: 14px; font-weight: 500;
  font-family: inherit; cursor: pointer;
  transition: color 0.15s, background 0.15s;
}
.btn-ghost:hover { color: #007AFF; background: rgba(0,122,255,0.04); }
.btn-full { width: 100%; margin-top: 4px; }

/* ── Modal ── */
.modal-overlay {
  position: fixed; inset: 0; z-index: 80;
  display: flex; align-items: center; justify-content: center; padding: 20px;
  background: rgba(0,0,0,0.22);
}
.modal-card {
  width: 480px; max-width: 100%; max-height: calc(100vh - 40px); overflow-y: auto;
  padding: 28px; border-radius: 20px;
  background: #FFFFFF; box-shadow: 0 18px 45px rgba(0,0,0,0.12);
}
.modal-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.modal-head h3 { margin: 0; font-size: 20px; font-weight: 700; }
.modal-close { border: none; background: none; font-size: 18px; cursor: pointer; color: rgba(60,60,67,0.45); }
.modal-desc { margin: 0 0 18px; font-size: 14px; color: rgba(60,60,67,0.6); }
.modal-form { display: grid; gap: 14px; }
.modal-row { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.modal-input {
  height: 44px; padding: 0 14px; border-radius: 10px;
  border: 1px solid rgba(60,60,67,0.18); background: #fff;
  font-size: 14px; font-family: inherit; outline: none;
  transition: border-color 0.15s;
}
.modal-input:focus { border-color: #007AFF; }
.modal-input::placeholder { color: rgba(60,60,67,0.35); }
.modal-units { margin-top: 4px; }
.modal-units-label { margin: 0 0 8px; font-size: 13px; color: rgba(60,60,67,0.6); }
.modal-units-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 6px;
  max-height: 150px; overflow-y: auto; padding: 8px;
  border: 1px solid rgba(60,60,67,0.12); border-radius: 10px;
}
.unit-chip {
  display: flex; align-items: center; gap: 6px; padding: 6px 10px;
  border-radius: 8px; cursor: pointer; font-size: 13px;
  border: 1px solid rgba(60,60,67,0.12); transition: background 0.15s, border-color 0.15s;
}
.unit-chip:hover { border-color: #007AFF; }
.unit-chip--on { background: rgba(0,122,255,0.08); border-color: rgba(0,122,255,0.45); color: #007AFF; }
.unit-chip input { width:auto; min-height:auto; accent-color:#007AFF; }
.modal-err { margin-top: 12px; font-size: 14px; color: #FF3B30; }
.modal-foot { display: flex; gap: 10px; margin-top: 18px; justify-content: flex-end; }

/* ── Responsive ── */
@media (max-width: 1024px) {
  .lobby-layout { grid-template-columns: 1fr; }
  .lobby-hero { flex-direction: column; align-items: flex-start; }
}
@media (max-width: 768px) {
  .modal-row { grid-template-columns: 1fr; }
  .lobby-hero-right { width: 100%; }
  .lobby-hero-right .btn-primary,
  .lobby-hero-right .btn-outline,
  .lobby-hero-right .btn-ghost { flex: 1; }
}
</style>
