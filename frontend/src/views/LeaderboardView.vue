<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import AppShell from '@/components/AppShell.vue'
import { fetchLeaderboard } from '@/api/leaderboard'
import { useAuthStore } from '@/stores/auth'
import type { LeaderboardEntry } from '@/types/api'

const auth = useAuthStore()
const entries = ref<LeaderboardEntry[]>([])
const myRank = ref<LeaderboardEntry | null>(null)
const loading = ref(false)
const error = ref('')
const type = ref<'power' | 'weekly'>('power')

const scoreHeader = computed(() => (type.value === 'power' ? '战力' : '在线时长'))
const extraHeader = computed(() => (type.value === 'power' ? '正确率' : '已通关'))

async function loadLeaderboard() {
  loading.value = true
  error.value = ''
  try {
    const data = await fetchLeaderboard(auth.token, type.value)
    entries.value = data.entries
    myRank.value = data.my_rank
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败。'
  } finally {
    loading.value = false
  }
}

function scoreText(entry: LeaderboardEntry) {
  return type.value === 'power'
    ? `${entry.power_score}`
    : `${entry.weekly_activity ?? 0} 分钟`
}

function extraText(entry: LeaderboardEntry) {
  return type.value === 'power'
    ? `${entry.accuracy}%`
    : `${entry.completed_levels} 关`
}

onMounted(loadLeaderboard)
</script>

<template>
  <AppShell title="排行榜">
    <div class="lb-page">
      <!-- Error Banner -->
      <div v-if="error" class="lb-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ error }}</span>
        <button type="button" class="lb-error-close" @click="error = ''">✕</button>
      </div>

      <!-- Title -->
      <header class="lb-header">
        <h1 class="lb-title">排行榜</h1>
        <p class="lb-desc">公开展示战力榜和在线时长榜；登录后会额外高亮你的个人名次。</p>
      </header>

      <!-- Segmented Control -->
      <div class="lb-tabs">
        <button type="button" class="lb-tab" :class="{ active: type === 'power' }" @click="type = 'power'; loadLeaderboard()">战力总榜</button>
        <button type="button" class="lb-tab" :class="{ active: type === 'weekly' }" @click="type = 'weekly'; loadLeaderboard()">在线时长榜</button>
      </div>

      <!-- States -->
      <div v-if="loading" class="lb-loading">正在加载排行榜…</div>
      <div v-else-if="entries.length === 0" class="lb-empty">暂无排行榜数据。</div>

      <template v-else>
        <!-- Podium: Top 3 -->
        <div class="lb-podium">
          <article v-if="entries[1]" class="podium-card podium-card--left">
            <div class="podium-avatar podium-avatar--silver">2</div>
            <strong>{{ entries[1].nickname }}</strong>
            <span>{{ scoreText(entries[1]) }}</span>
          </article>
          <article v-if="entries[0]" class="podium-card podium-card--center">
            <div class="podium-avatar podium-avatar--gold">1</div>
            <strong>{{ entries[0].nickname }}</strong>
            <span>{{ scoreText(entries[0]) }}</span>
          </article>
          <article v-if="entries[2]" class="podium-card podium-card--right">
            <div class="podium-avatar podium-avatar--bronze">3</div>
            <strong>{{ entries[2].nickname }}</strong>
            <span>{{ scoreText(entries[2]) }}</span>
          </article>
        </div>

        <!-- Table Header -->
        <div class="lb-thead">
          <span>排名</span>
          <span>昵称</span>
          <span>{{ scoreHeader }}</span>
          <span>{{ extraHeader }}</span>
        </div>

        <!-- Leaderboard List -->
        <div class="lb-list">
          <article v-for="entry in entries" :key="entry.user_id" class="lb-row" :class="{ 'lb-row--me': myRank && entry.user_id === myRank.user_id }">
            <span class="lbr-rank">#{{ entry.rank }}</span>
            <strong class="lbr-name">{{ entry.nickname }}</strong>
            <span class="lbr-score">{{ scoreText(entry) }}</span>
            <span class="lbr-extra">{{ extraText(entry) }}</span>
          </article>
        </div>

        <!-- My Rank -->
        <div v-if="myRank" class="lb-my">
          你的名次：第 {{ myRank.rank }} 名，{{ scoreHeader }} {{ type === 'power' ? myRank.power_score : myRank.weekly_activity ?? 0 }}
        </div>
      </template>
    </div>
  </AppShell>
</template>

<style scoped>
/* ── Shell ── */
.lb-page {
  min-height: 100vh; background: #F2F2F7; padding-bottom: 40px;
  width: 100%;
  display: grid;
  gap: 18px;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ── Error ── */
.lb-error {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 14px; border-radius: 12px;
  background: rgba(255,59,48,0.08); border: 1px solid rgba(255,59,48,0.35);
  color: #FF3B30; font-size: 14px;
}
.lb-error span { flex:1; }
.lb-error-close {
  width:24px; height:24px; display:flex; align-items:center; justify-content:center;
  border:none; border-radius:6px; background:rgba(255,59,48,0.12); color:#FF3B30;
  font-size:12px; cursor:pointer;
}

/* ── Header ── */
.lb-header { text-align: center; padding: 8px 0 0; }
.lb-title { margin:0; font-size:30px; font-weight:700; color:#000; }
.lb-desc { margin:6px 0 0; font-size:14px; color:rgba(60,60,67,0.6); }

/* ── Segmented Control ── */
.lb-tabs {
  display:grid; grid-template-columns:1fr 1fr; gap:0;
  padding:4px; background:#F2F2F7; border-radius:12px;
  max-width:360px; margin:0 auto; width:100%;
}
.lb-tab {
  height:42px; border:none; border-radius:10px; background:transparent;
  color:rgba(60,60,67,0.6); font-size:15px; font-weight:500;
  font-family:inherit; cursor:pointer;
  transition:background 0.15s,color 0.15s,box-shadow 0.15s;
}
.lb-tab.active {
  background:#fff; color:#007AFF; font-weight:600;
  box-shadow:0 2px 8px rgba(0,0,0,0.08);
}

/* ── States ── */
.lb-loading { text-align:center; padding:40px; color:rgba(60,60,67,0.6); font-size:14px; }
.lb-empty { text-align:center; padding:40px; color:rgba(60,60,67,0.45); font-size:14px; }

/* ── Podium ── */
.lb-podium {
  display:grid; grid-template-columns:1fr 1fr 1fr; gap:14px;
  align-items:end; margin-top:8px;
}
.podium-card {
  padding:20px 14px; text-align:center; border-radius:16px;
  background:#FFFFFF; border:1px solid rgba(60,60,67,0.12);
  box-shadow:0 1px 2px rgba(0,0,0,0.04),0 4px 12px rgba(0,0,0,0.03);
}
.podium-card--center { padding:28px 14px; }
.podium-card strong { display:block; margin:10px 0 4px; font-size:16px; font-weight:700; color:#000; }
.podium-card span { font-size:14px; color:rgba(60,60,67,0.6); font-weight:600; }
.podium-avatar {
  width:44px; height:44px; border-radius:999px; margin:0 auto;
  display:flex; align-items:center; justify-content:center;
  font-size:20px; font-weight:800; color:#fff;
}
.podium-avatar--gold { background:#007AFF; }
.podium-avatar--silver { background:rgba(60,60,67,0.45); }
.podium-avatar--bronze { background:#FF9500; }
.podium-card--center .podium-avatar { width:56px; height:56px; font-size:24px; }

/* ── Table Header ── */
.lb-thead {
  display:grid; grid-template-columns:70px minmax(0,1fr) 120px 100px; gap:12px;
  padding:0 14px 10px; align-items:center;
  color:rgba(60,60,67,0.45); font-size:12px; font-weight:700;
  text-transform:uppercase; letter-spacing:0.05em;
}

/* ── List ── */
.lb-list { display:grid; gap:6px; }
.lb-row {
  display:grid; grid-template-columns:70px minmax(0,1fr) 120px 100px; gap:12px;
  align-items:center; padding:14px 16px; border-radius:12px;
  background:#FFFFFF; border:1px solid rgba(60,60,67,0.08);
  transition:background 0.15s;
}
.lb-row--me { background:rgba(0,122,255,0.06); border-color:rgba(0,122,255,0.2); }
.lbr-rank { font-size:16px; font-weight:800; color:#000; }
.lbr-name { font-size:15px; color:#000; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
.lbr-score { font-size:15px; font-weight:700; color:#000; }
.lbr-extra { font-size:14px; color:rgba(60,60,67,0.6); }

/* ── My Rank ── */
.lb-my {
  margin-top:4px; padding:16px 20px; border-radius:14px;
  background:rgba(0,122,255,0.06); border:1px solid rgba(0,122,255,0.15);
  color:#007AFF; font-size:15px; font-weight:700; text-align:center;
}

/* ── Responsive ── */
@media (max-width:768px) {
  .lb-podium { grid-template-columns:1fr; }
  .lb-thead { display:none; }
  .lb-row { grid-template-columns:1fr; gap:6px; }
  .lbr-rank { font-size:14px; }
}
</style>
