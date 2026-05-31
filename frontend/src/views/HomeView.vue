<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { getMyRoom } from '@/api/pvp'
import BrandLogo from '@/components/BrandLogo.vue'
import { APP_ENGLISH_NAME, APP_NAME } from '@/brand'
import type { PvpRoom } from '@/types/api'
import type { StudentCardState } from '@/router/meta'
import { stateLabel, type StudentNavCard } from '@/lib/student-navigation'

const router = useRouter()
const auth = useAuthStore()
const myRoom = ref<PvpRoom | null>(null)

const userLabel = computed(() => auth.user?.nickname || auth.user?.username || '未登录')
const roomStatusLabel = computed(() => myRoom.value ? statusLabel(myRoom.value.status) : '暂无房间')
const suggestedPath = computed(() => {
  if (!auth.isAuthenticated) return '/login'
  if (myRoom.value?.status === 'running') return '/pvp/battle'
  if (myRoom.value) return '/pvp/room'
  return '/adventure'
})
const suggestedLabel = computed(() => {
  if (!auth.isAuthenticated) return '登录后开始'
  if (myRoom.value?.status === 'running') return '返回进行中的对战'
  if (myRoom.value) return '进入当前房间'
  return '继续今日学习'
})
const overviewCards = computed(() => [
  {
    label: '账号状态',
    value: auth.isAuthenticated ? '已登录' : '游客模式',
    note: auth.isAuthenticated ? '学习记录会自动保留在账号中。' : '登录后同步冒险、练习和竞技进度。',
  },
  {
    label: '竞技状态',
    value: roomStatusLabel.value,
    note: myRoom.value ? `当前房间：${myRoom.value.title}` : '还没有分配中的竞技房间。',
  },
  {
    label: '推荐入口',
    value: auth.isAuthenticated ? '继续挑战' : '先登录',
    note: auth.isAuthenticated ? '先从冒险地图开始，再按需要切到练习或竞技。' : '登录后可以进入完整学习流程。',
  },
])

const primaryCards = computed<StudentNavCard[]>(() => {
  const pvpRecommended = myRoom.value?.status === 'running'
  const lockedState: StudentCardState = auth.isAuthenticated ? 'default' : 'locked'

  return [
    {
      title: '开始冒险',
      description: '选择单元与关卡，逐步完成学习挑战。',
      status: auth.isAuthenticated ? '推荐继续' : '登录后开始',
      destination: '进入冒险地图',
      state: pvpRecommended ? 'default' : (auth.isAuthenticated ? 'recommended' : lockedState),
      accent: 'indigo',
    },
    {
      title: '随机练习',
      description: '专注刷题和解析，练习结束单独进入总结页。',
      status: auth.isAuthenticated ? '自由进入' : '登录后进入',
      destination: '打开练习入口',
      state: lockedState,
      accent: 'mint',
    },
    {
      title: '极限挑战',
      description: '一命到底，答错即止，分成入口页、作答页和结果页。',
      status: auth.isAuthenticated ? '高压模式' : '登录后挑战',
      destination: '打开极限入口',
      state: lockedState,
      accent: 'gold',
    },
    {
      title: 'PVP 竞技',
      description: '先进大厅看推荐，再进房间准备，最后进入战斗与结算。',
      status: myRoom.value ? `当前 ${statusLabel(myRoom.value.status)}` : '等待教师分配',
      destination: myRoom.value?.status === 'running' ? '进入对战' : '进入竞技大厅',
      state: myRoom.value ? (pvpRecommended ? 'attention' : 'resume') : lockedState,
      accent: 'rose',
    },
  ]
})

const secondaryCards = computed<StudentNavCard[]>(() => [
  {
    title: '学习记录',
    description: '回看积分、正确率、错题和练习次数。',
    status: auth.isAuthenticated ? '查看历史' : '登录后可看',
    destination: '打开学习记录',
    state: auth.isAuthenticated ? 'default' : 'locked',
    accent: 'slate',
  },
  {
    title: '成就墙',
    description: '查看已经解锁和待解锁的学习成就。',
    status: auth.isAuthenticated ? '查看进度' : '登录后可看',
    destination: '打开成就页',
    state: auth.isAuthenticated ? 'default' : 'locked',
    accent: 'mint',
  },
  {
    title: '排行榜',
    description: '公开查看当前战力与学习表现排行。',
    status: '公开可看',
    destination: '打开排行榜',
    state: 'default',
    accent: 'gold',
  },
])

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

function routeForPrimary(title: string) {
  if (title === '开始冒险') return '/adventure'
  if (title === '随机练习') return '/practice'
  if (title === '极限挑战') return '/extreme'
  return '/pvp'
}

function routeForSecondary(title: string) {
  if (title === '学习记录') return '/records'
  if (title === '成就墙') return '/achievements'
  return '/leaderboard'
}

function open(path: string) {
  router.push(path)
}

function logout() {
  auth.logout()
  router.push('/')
}

onMounted(async () => {
  if (!auth.token) return
  try {
    const res = await getMyRoom(auth.token)
    myRoom.value = res.room
  } catch {
    myRoom.value = null
  }
})
</script>

<template>
  <div class="home-page">
    <!-- Top: Horizontal Branding Bar -->
    <header class="home-header">
      <BrandLogo size="md" :alt="APP_NAME" />
      <div class="home-header-text">
        <h1 class="home-title">{{ APP_NAME }}</h1>
        <p class="home-subtitle">{{ APP_ENGLISH_NAME }}</p>
      </div>
    </header>

    <!-- Main: Two-Column Layout -->
    <main class="home-main">
      <!-- Left Column -->
      <div class="home-left">
        <!-- Overview Cards -->
        <div class="overview-row" aria-label="学习概览">
          <article v-for="item in overviewCards" :key="item.label" class="overview-card">
            <span class="ov-label">{{ item.label }}</span>
            <strong class="ov-value">{{ item.value }}</strong>
            <p class="ov-note">{{ item.note }}</p>
          </article>
        </div>

        <!-- Features Card -->
        <section class="features-card">
          <!-- Primary Features (2×2) -->
          <div class="features-grid">
            <button
              v-for="card in primaryCards"
              :key="card.title"
              type="button"
              class="feature-item"
              @click="open(routeForPrimary(card.title))"
            >
              <div class="fi-icon" :class="`fi-icon--${card.accent}`">
                <!-- 开始冒险: compass -->
                <svg v-if="card.title === '开始冒险'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/><polygon points="16.24 7.76 14.12 14.12 7.76 16.24 9.88 9.88 16.24 7.76"/>
                </svg>
                <!-- 随机练习: target / crosshair -->
                <svg v-else-if="card.title === '随机练习'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>
                </svg>
                <!-- 极限挑战: zap -->
                <svg v-else-if="card.title === '极限挑战'" width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
                </svg>
                <!-- PVP 竞技: swords -->
                <svg v-else width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M14.5 17.5L3 6V3h3l11.5 11.5"/><path d="M13 19l6-6"/><path d="M16 16l4 4"/><path d="M19 21l2-2"/><path d="M4.5 12.5l7 7"/>
                </svg>
              </div>
              <div class="fi-body">
                <div class="fi-meta">
                  <span class="fi-state">{{ stateLabel(card.state) }}</span>
                  <span class="fi-status">{{ card.status }}</span>
                </div>
                <strong class="fi-title">{{ card.title }}</strong>
                <p class="fi-desc">{{ card.description }}</p>
              </div>
              <span class="fi-chevron">›</span>
            </button>
          </div>

          <!-- Divider -->
          <div class="features-divider"></div>

          <!-- Utility Entries (3 cards) -->
          <div class="utility-row">
            <button
              v-for="card in secondaryCards"
              :key="card.title"
              type="button"
              class="utility-item"
              @click="open(routeForSecondary(card.title))"
            >
              <div class="ui-body">
                <strong class="ui-title">{{ card.title }}</strong>
                <p class="ui-desc">{{ card.description }}</p>
              </div>
              <span class="ui-arrow">›</span>
            </button>
          </div>
        </section>
      </div>

      <!-- Right Column: Account Panel -->
      <aside class="home-right">
        <section class="side-card">
          <!-- User Header -->
          <div class="side-user">
            <span class="side-avatar">{{ userLabel.slice(0, 2).toUpperCase() }}</span>
            <div>
              <strong class="side-name">{{ auth.isAuthenticated ? userLabel : '未登录' }}</strong>
              <p class="side-status">{{ roomStatusLabel }}</p>
            </div>
          </div>

          <h3 class="side-heading">今日推荐</h3>
          <p class="side-hint">{{ auth.isAuthenticated ? '已连接个人学习记录与竞技状态。' : '登录后保存学习记录、排行榜与房间进度。' }}</p>

          <!-- Dynamic CTA -->
          <button type="button" class="side-cta" @click="open(suggestedPath)">
            {{ suggestedLabel }}
          </button>

          <div class="side-divider"></div>

          <!-- Quick Links -->
          <div class="side-group">
            <p class="side-group-label">快速入口</p>
            <button type="button" class="side-link" @click="open('/account')">个人中心</button>
            <button type="button" class="side-link" @click="open('/leaderboard')">先看排行榜</button>
          </div>

          <div class="side-divider"></div>

          <!-- More Actions -->
          <div class="side-group">
            <p class="side-group-label">更多操作</p>
            <button type="button" class="side-link" @click="open(auth.isAuthenticated ? '/account' : '/login')">
              {{ auth.isAuthenticated ? '进入个人中心' : '去登录' }}
            </button>
            <button type="button" class="side-link" @click="open(auth.isAuthenticated ? '/records' : '/leaderboard')">
              {{ auth.isAuthenticated ? '查看学习记录' : '先看排行榜' }}
            </button>
          </div>

          <div class="side-divider"></div>

          <!-- Logout -->
          <button v-if="auth.isAuthenticated" type="button" class="side-logout" @click="logout">退出登录</button>
        </section>
      </aside>
    </main>
  </div>
</template>

<style scoped>
/* ── Page Shell ── */
.home-page {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 20px 0 40px;
  background: #f5f6fa;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ── Header ── */
.home-header {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 0 28px 12px;
  flex-shrink: 0;
  max-width: 1220px;
  width: 100%;
  margin: 0 auto;
}

.home-header-text {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.home-title {
  margin: 0;
  font-size: 24px;
  font-weight: 800;
  color: #050505;
  letter-spacing: -0.02em;
  line-height: 1;
}

.home-subtitle {
  margin: 0;
  font-size: 14px;
  font-weight: 400;
  color: rgba(60, 60, 67, 0.36);
}

/* ── Main Layout ── */
.home-main {
  max-width: 1220px;
  width: 100%;
  margin: 0 auto;
  padding: 0 24px 20px;
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: 22px;
  align-items: start;
  flex: 1;
}

.home-left {
  display: grid;
  gap: 10px;
  min-width: 0;
  align-content: start;
}

/* ── Overview Cards ── */
.overview-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.overview-card {
  padding: 16px 18px;
  border-radius: 14px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  background: #FFFFFF;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 4px 12px rgba(0, 0, 0, 0.03);
  min-width: 0;
}

.ov-label {
  display: block;
  font-size: 11px;
  font-weight: 800;
  color: rgba(60, 60, 67, 0.45);
  text-transform: uppercase;
  letter-spacing: 0.08em;
  margin-bottom: 8px;
}

.ov-value {
  display: block;
  font-size: 18px;
  font-weight: 700;
  color: #050505;
  line-height: 1.2;
}

.ov-note {
  margin: 8px 0 0;
  font-size: 13px;
  color: rgba(60, 60, 67, 0.68);
  line-height: 1.5;
}

/* ── Features Card ── */
.features-card {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
  padding: 20px 24px;
}

.features-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

/* ── Feature Item ── */
.feature-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  border-radius: 14px;
  background: #FFFFFF;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}

.feature-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border-color: rgba(10, 132, 255, 0.25);
}

.feature-item:active {
  transform: translateY(0) scale(0.99);
}

.fi-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.fi-icon--indigo { background: rgba(10, 132, 255, 0.12); color: #0a84ff; }
.fi-icon--mint   { background: rgba(34, 197, 94, 0.12);  color: #22c55e; }
.fi-icon--gold   { background: rgba(255, 138, 0, 0.12);  color: #ff8a00; }
.fi-icon--rose   { background: rgba(10, 132, 255, 0.12); color: #0a84ff; }

.fi-body {
  flex: 1;
  min-width: 0;
}

.fi-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.fi-state {
  display: inline-flex;
  align-items: center;
  padding: 2px 10px;
  border-radius: 999px;
  background: rgba(10, 132, 255, 0.08);
  color: #0a84ff;
  font-size: 11px;
  font-weight: 700;
}

.fi-status {
  font-size: 12px;
  color: rgba(60, 60, 67, 0.45);
}

.fi-title {
  display: block;
  font-size: 17px;
  font-weight: 700;
  color: #050505;
  margin-bottom: 2px;
}

.fi-desc {
  margin: 0;
  font-size: 12px;
  color: rgba(60, 60, 67, 0.68);
  line-height: 1.4;
}

.fi-chevron {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 22px;
  font-weight: 400;
  color: rgba(60, 60, 67, 0.25);
}

/* ── Features Divider ── */
.features-divider {
  height: 1px;
  background: rgba(60, 60, 67, 0.12);
  margin: 16px 0;
}

/* ── Utility Row ── */
.utility-row {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.utility-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  border-radius: 12px;
  background: #FFFFFF;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  transition: transform 0.15s, box-shadow 0.15s, border-color 0.15s;
}

.utility-item:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.06);
  border-color: rgba(10, 132, 255, 0.25);
}

.utility-item:active {
  transform: translateY(0) scale(0.99);
}

.ui-body {
  flex: 1;
  min-width: 0;
}

.ui-title {
  display: block;
  font-size: 15px;
  font-weight: 700;
  color: #050505;
  margin-bottom: 2px;
}

.ui-desc {
  margin: 0;
  font-size: 12px;
  color: rgba(60, 60, 67, 0.68);
  line-height: 1.4;
}

.ui-arrow {
  flex-shrink: 0;
  font-size: 20px;
  color: rgba(60, 60, 67, 0.25);
}

/* ── Right Column ── */
.home-right {
}

.side-card {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.05);
  padding: 20px 22px;
}

/* ── Side User ── */
.side-user {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.side-avatar {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(10, 132, 255, 0.12);
  color: #0a84ff;
  font-size: 15px;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.side-name {
  display: block;
  font-size: 17px;
  font-weight: 700;
  color: #050505;
}

.side-status {
  margin: 2px 0 0;
  font-size: 13px;
  color: rgba(60, 60, 67, 0.45);
}

/* ── Side Sections ── */
.side-heading {
  margin: 0 0 4px;
  font-size: 16px;
  font-weight: 700;
  color: #050505;
}

.side-hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: rgba(60, 60, 67, 0.68);
  line-height: 1.4;
}

/* ── Side CTA ── */
.side-cta {
  width: 100%;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 10px;
  background: #0a84ff;
  color: #FFFFFF;
  font-size: 15px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}

.side-cta:hover {
  background: #006edc;
}

.side-cta:active {
  transform: scale(0.98);
}

/* ── Side Divider ── */
.side-divider {
  height: 1px;
  background: rgba(60, 60, 67, 0.12);
  margin: 14px 0;
}

/* ── Side Group ── */
.side-group-label {
  margin: 0 0 8px;
  font-size: 11px;
  font-weight: 700;
  color: rgba(60, 60, 67, 0.45);
  text-transform: uppercase;
  letter-spacing: 0.06em;
}

.side-link {
  width: 100%;
  height: 36px;
  display: flex;
  align-items: center;
  padding: 0 12px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  border-radius: 10px;
  background: #FFFFFF;
  color: #050505;
  font-size: 14px;
  font-weight: 500;
  font-family: inherit;
  cursor: pointer;
  text-align: left;
  transition: background 0.15s, border-color 0.15s;
}

.side-link + .side-link {
  margin-top: 6px;
}

.side-link:hover {
  background: rgba(0, 0, 0, 0.03);
  border-color: rgba(10, 132, 255, 0.25);
}

/* ── Side Logout ── */
.side-logout {
  width: 100%;
  height: 38px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 10px;
  background: rgba(255, 59, 48, 0.08);
  color: #ff3b30;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s;
}

.side-logout:hover {
  background: rgba(255, 59, 48, 0.14);
}

/* ── Responsive ── */
@media (max-width: 900px) {
  .home-main {
    grid-template-columns: 1fr;
  }

  .home-right {
    position: static;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .utility-row {
    grid-template-columns: 1fr;
  }

  .overview-row {
    grid-template-columns: 1fr;
  }

  .home-title {
    font-size: 32px;
  }
}

@media (max-width: 640px) {
  .home-page {
    padding: 24px 0 40px;
  }

  .home-main {
    padding: 0 16px;
  }

  .features-card {
    padding: 18px;
  }

  .feature-item {
    padding: 16px;
  }

  .side-card {
    padding: 20px;
  }

  .home-title {
    font-size: 28px;
  }
}
</style>
