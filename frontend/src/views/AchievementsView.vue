<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { fetchAchievements } from '@/api/achievements'
import { useAuthStore } from '@/stores/auth'
import type { Achievement } from '@/types/api'

const router = useRouter()
const auth = useAuthStore()
const achievements = ref<Achievement[]>([])
const loading = ref(false)
const error = ref('')

const unlockedCount = computed(() => achievements.value.filter(item => item.unlocked).length)
const rareCount = computed(() => achievements.value.filter(item => item.rarity === 'rare').length)
const epicCount = computed(() => achievements.value.filter(item => item.rarity === 'epic').length)
const latestUnlocked = computed(() =>
  achievements.value
    .filter(item => item.unlocked && item.unlocked_at)
    .sort((a, b) => new Date(b.unlocked_at ?? 0).getTime() - new Date(a.unlocked_at ?? 0).getTime())[0] ?? null
)

function achievementMark(item: Achievement) {
  if (item.rarity === 'epic') return 'E'
  if (item.rarity === 'rare') return 'R'
  return 'A'
}

function formatUnlockedAt(value?: string | null) {
  if (!value) return ''
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return new Intl.DateTimeFormat('zh-CN', {
    month: 'numeric',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date)
}

async function loadAchievements() {
  if (!auth.token) return

  loading.value = true
  error.value = ''
  try {
    achievements.value = await fetchAchievements(auth.token)
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败。'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  if (!auth.isAuthenticated) return
  loadAchievements()
})
</script>

<template>
  <AppShell title="成就殿堂">
    <div class="ach-page">
      <!-- Error -->
      <div v-if="error" class="ach-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ error }}</span>
        <button type="button" class="ach-error-close" @click="error = ''">✕</button>
      </div>

      <!-- Unauthenticated -->
      <section v-if="!auth.isAuthenticated" class="ach-empty-card">
        <h2>登录后查看你的成就墙</h2>
        <p>成就、稀有度和解锁状态都和当前账号绑定。</p>
        <div class="ach-empty-btns">
          <button type="button" class="btn-primary" @click="router.push('/login')">去登录</button>
          <button type="button" class="btn-ghost" @click="router.push('/')">返回首页</button>
        </div>
      </section>

      <div v-else-if="loading" class="ach-loading">正在加载成就数据…</div>

      <template v-else>
        <!-- Title -->
        <header class="ach-header">
          <h1 class="ach-title">成就墙</h1>
          <p class="ach-desc">查看已解锁成就、稀有度分布和解锁进度。</p>
        </header>

        <!-- Summary Cards -->
        <div class="ach-summary">
          <div class="sum-card">
            <span class="sum-label">总成就</span>
            <strong class="sum-val">{{ achievements.length }}</strong>
          </div>
          <div class="sum-card">
            <span class="sum-label">已解锁</span>
            <strong class="sum-val sum-val--ok">{{ unlockedCount }}</strong>
          </div>
          <div class="sum-card">
            <span class="sum-label">未解锁</span>
            <strong class="sum-val sum-val--muted">{{ Math.max(achievements.length - unlockedCount, 0) }}</strong>
          </div>
          <div class="sum-card">
            <span class="sum-label">解锁率</span>
            <strong class="sum-val sum-val--blue">{{ achievements.length ? Math.round((unlockedCount / achievements.length) * 100) : 0 }}%</strong>
          </div>
        </div>

        <!-- Rarity Overview -->
        <div class="ach-rarity">
          <h3 class="ach-section-title">稀有度概览</h3>
          <div class="rarity-row">
            <span class="rarity-chip rarity-chip--common">普通 {{ achievements.filter(item => item.rarity === 'common').length }}</span>
            <span class="rarity-chip rarity-chip--rare">稀有 {{ rareCount }}</span>
            <span class="rarity-chip rarity-chip--epic">史诗 {{ epicCount }}</span>
          </div>
        </div>

        <section v-if="latestUnlocked" class="ach-latest">
          <span class="ach-latest-label">最近解锁</span>
          <div class="ach-latest-card">
            <div class="ach-latest-icon">{{ achievementMark(latestUnlocked) }}</div>
            <div class="ach-latest-info">
              <strong>{{ latestUnlocked.name }}</strong>
              <p>{{ latestUnlocked.description }}</p>
            </div>
            <span class="ach-latest-time">{{ formatUnlockedAt(latestUnlocked.unlocked_at) }}</span>
          </div>
        </section>

        <!-- Empty State -->
        <div v-if="achievements.length === 0" class="ach-empty-card">
          <h3>暂无成就数据</h3>
          <p>完成练习、闯关或挑战后会在这里显示成就。</p>
          <div class="ach-empty-btns">
            <button type="button" class="btn-primary" @click="loadAchievements()">刷新成就</button>
            <button type="button" class="btn-outline" @click="router.push('/game')">回到闯关</button>
          </div>
        </div>

        <!-- Achievement Grid -->
        <section v-else class="ach-grid">
          <article v-for="ach in achievements" :key="ach.id" class="ach-card" :class="{ 'ach-card--locked': !ach.unlocked }">
            <div class="ach-card-top">
              <div class="ach-card-icon">{{ achievementMark(ach) }}</div>
              <div class="ach-card-badges">
                <span class="ach-badge" :class="'ach-badge--' + ach.rarity">{{ ach.rarity }}</span>
                <span class="ach-badge">{{ ach.category }}</span>
              </div>
            </div>
            <h4 class="ach-card-name">{{ ach.name }}</h4>
            <p class="ach-card-desc">{{ ach.description }}</p>
            <div class="ach-card-foot">
              <span class="ach-card-status" :class="{ 'ach-card-status--ok': ach.unlocked }">
                {{ ach.unlocked ? '已解锁' : '未解锁' }}
              </span>
              <span class="ach-card-hint">
                {{ ach.unlocked ? `解锁时间：${formatUnlockedAt(ach.unlocked_at) || '刚刚解锁'}` : ach.hint }}
              </span>
            </div>
          </article>
        </section>

        <!-- Bottom Actions -->
        <div class="ach-actions">
          <button type="button" class="btn-primary" @click="loadAchievements()">刷新成就</button>
          <button type="button" class="btn-outline" @click="router.push('/game')">回到闯关</button>
        </div>
      </template>
    </div>
  </AppShell>
</template>

<style scoped>
/* ── Shell ── */
.ach-page {
  min-height: 100vh; background: #F2F2F7; padding-bottom: 40px;
  width: 100%;
  display: grid; gap: 18px;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ── Error ── */
.ach-error {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px; border-radius: 12px;
  background: rgba(255,59,48,0.08); border: 1px solid rgba(255,59,48,0.35);
  color: #FF3B30; font-size: 14px;
}
.ach-error span { flex:1; }
.ach-error-close {
  width:24px; height:24px; display:flex; align-items:center; justify-content:center;
  border:none; border-radius:6px; background:rgba(255,59,48,0.12); color:#FF3B30;
  font-size:12px; cursor:pointer;
}

/* ── Unauthenticated ── */
.ach-empty-card {
  text-align:center; padding:60px 32px; border-radius:18px;
  background:#FFFFFF; border:1px solid rgba(60,60,67,0.12);
  box-shadow:0 1px 2px rgba(0,0,0,0.04),0 8px 24px rgba(0,0,0,0.05);
}
.ach-empty-card h2 { margin:0 0 8px; font-size:22px; font-weight:700; color:#000; }
.ach-empty-card p { margin:0 0 24px; font-size:14px; color:rgba(60,60,67,0.6); }
.ach-empty-btns { display:flex; gap:12px; justify-content:center; flex-wrap:wrap; }

/* ── States ── */
.ach-loading { text-align:center; padding:40px; color:rgba(60,60,67,0.6); font-size:14px; }
.ach-empty { text-align:center; padding:40px; color:rgba(60,60,67,0.45); font-size:14px; }

/* ── Header ── */
.ach-header { text-align:center; padding:8px 0 0; }
.ach-title { margin:0; font-size:30px; font-weight:700; color:#000; }
.ach-desc { margin:6px 0 0; font-size:14px; color:rgba(60,60,67,0.6); }

/* ── Summary ── */
.ach-summary { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.sum-card {
  padding:20px 16px; text-align:center; border-radius:16px;
  background:#FFFFFF; border:1px solid rgba(60,60,67,0.12);
  box-shadow:0 1px 2px rgba(0,0,0,0.03);
}
.sum-label { display:block; font-size:12px; color:rgba(60,60,67,0.45); text-transform:uppercase; letter-spacing:0.05em; margin-bottom:6px; }
.sum-val { font-size:28px; font-weight:800; color:#000; }
.sum-val--ok { color:#34C759; }
.sum-val--muted { color:rgba(60,60,67,0.45); }
.sum-val--blue { color:#007AFF; }

/* ── Rarity ── */
.ach-rarity { margin-top:4px; }
.ach-section-title { margin:0 0 10px; font-size:16px; font-weight:700; color:#000; }
.rarity-row { display:flex; gap:8px; flex-wrap:wrap; }
.rarity-chip {
  padding:6px 14px; border-radius:10px; font-size:13px; font-weight:600;
  border:1px solid rgba(60,60,67,0.12); background:#FFFFFF;
}
.rarity-chip--common { color:rgba(60,60,67,0.6); }
.rarity-chip--rare { color:#007AFF; border-color:rgba(0,122,255,0.25); background:rgba(0,122,255,0.04); }
.rarity-chip--epic { color:#FF9500; border-color:rgba(255,149,0,0.25); background:rgba(255,149,0,0.04); }

.ach-latest { display:grid; gap:10px; }
.ach-latest-label { font-size:13px; font-weight:600; color:rgba(60,60,67,0.6); }
.ach-latest-card {
  display:grid; grid-template-columns:auto 1fr auto; gap:12px; align-items:center;
  padding:16px 18px; border-radius:16px; background:#FFFFFF;
  border:1px solid rgba(60,60,67,0.12); box-shadow:0 1px 2px rgba(0,0,0,0.03);
}
.ach-latest-icon {
  width:44px; height:44px; border-radius:12px; display:flex; align-items:center; justify-content:center;
  font-size:16px; font-weight:700; color:#007AFF; background:rgba(0,122,255,0.08);
}
.ach-latest-info strong { display:block; font-size:15px; color:#000; }
.ach-latest-info p { margin:4px 0 0; font-size:13px; line-height:1.5; color:rgba(60,60,67,0.6); }
.ach-latest-time { font-size:12px; color:rgba(60,60,67,0.45); }

/* ── Grid ── */
.ach-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(240px,1fr)); gap:14px; }
.ach-card {
  padding:22px; border-radius:16px;
  background:#FFFFFF; border:1px solid rgba(60,60,67,0.12);
  box-shadow:0 1px 2px rgba(0,0,0,0.03);
  display:flex; flex-direction:column; gap:12px;
  transition:box-shadow 0.15s;
}
.ach-card:hover { box-shadow:0 4px 16px rgba(0,0,0,0.06); }
.ach-card--locked { opacity:0.65; }
.ach-card--locked:hover { opacity:0.85; }
.ach-card-top { display:flex; align-items:flex-start; gap:12px; }
.ach-card-icon {
  width:46px; height:46px; display:flex; align-items:center; justify-content:center;
  border-radius:12px; background:rgba(0,122,255,0.08); font-size:16px; font-weight:700; color:#007AFF; flex-shrink:0;
}
.ach-card--locked .ach-card-icon { background:rgba(60,60,67,0.06); }
.ach-card-badges { display:flex; gap:6px; flex-wrap:wrap; }
.ach-badge {
  padding:2px 10px; border-radius:999px; font-size:11px; font-weight:700;
  background:rgba(60,60,67,0.06); color:rgba(60,60,67,0.6);
}
.ach-badge--common { background:rgba(60,60,67,0.06); color:rgba(60,60,67,0.5); }
.ach-badge--rare { background:rgba(0,122,255,0.08); color:#007AFF; }
.ach-badge--epic { background:rgba(255,149,0,0.08); color:#FF9500; }
.ach-badge--legendary { background:rgba(255,59,48,0.08); color:#FF3B30; }
.ach-card-name { margin:0; font-size:17px; font-weight:700; color:#000; }
.ach-card-desc { margin:0; font-size:13px; color:rgba(60,60,67,0.6); line-height:1.5; flex:1; }
.ach-card-foot { display:flex; flex-direction:column; gap:4px; }
.ach-card-status { font-size:12px; font-weight:600; color:rgba(60,60,67,0.45); }
.ach-card-status--ok { color:#34C759; }
.ach-card-hint { font-size:12px; color:rgba(60,60,67,0.45); line-height:1.4; }

/* ── Buttons ── */
.btn-primary {
  height:44px; padding:0 24px; border:none; border-radius:12px;
  background:#007AFF; color:#fff; font-size:15px; font-weight:600;
  font-family:inherit; cursor:pointer;
  transition:background 0.15s,transform 0.1s;
}
.btn-primary:hover { background:#006EE6; }
.btn-primary:active { transform:scale(0.98); }
.btn-outline {
  height:44px; padding:0 24px; border:1px solid rgba(60,60,67,0.2); border-radius:12px;
  background:#fff; color:#000; font-size:15px; font-weight:600;
  font-family:inherit; cursor:pointer;
  transition:border-color 0.15s,background 0.15s;
}
.btn-outline:hover { border-color:#007AFF; background:rgba(0,122,255,0.04); }
.btn-ghost {
  height:44px; padding:0 20px; border:none; border-radius:12px;
  background:transparent; color:rgba(60,60,67,0.6); font-size:14px; font-weight:500;
  font-family:inherit; cursor:pointer;
}
.btn-ghost:hover { color:#007AFF; background:rgba(0,122,255,0.04); }
.ach-actions { display:flex; gap:12px; justify-content:center; padding-bottom:8px; }

/* ── Responsive ── */
@media (max-width:768px) {
  .ach-summary { grid-template-columns:repeat(2,1fr); }
  .ach-grid { grid-template-columns:1fr; }
  .ach-latest-card { grid-template-columns:auto 1fr; }
  .ach-latest-time { grid-column:2; }
}
@media (max-width:480px) {
  .ach-summary { grid-template-columns:1fr; }
}
</style>
