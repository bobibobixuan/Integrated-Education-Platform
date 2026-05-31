<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { usePvpStore } from '@/stores/pvp'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const pvp = usePvpStore()
const auth = useAuthStore()

const myMember = computed(() => pvp.allMembers.find(member => member.user_id === auth.user?.id) || null)
const finalLabel = computed(() => pvp.roomStatus === 'finished' ? '最终排名' : '个人结算已完成')

function backToLobby() {
  pvp.reset()
  router.push('/pvp')
}
</script>

<template>
  <AppShell>
    <section v-if="pvp.room || pvp.allMembers.length" class="page-surface page-surface--light result-page">
      <div class="page-header page-header--center">
        <h2 class="page-title">{{ finalLabel }}</h2>
        <p class="page-subtitle">
          {{ pvp.roomStatus === 'finished'
            ? '房间已经结束，下面是最终排位。'
            : '你的答题会话已经收口，当前可以先看排位，再回大厅等待老师结束整场对战。' }}
        </p>
      </div>

      <div class="metrics-grid">
        <div class="metric-card metric-card--indigo">
          <div class="metric-value">#{{ myMember?.rank || '-' }}</div>
          <div class="metric-label">我的名次</div>
        </div>
        <div class="metric-card metric-card--green">
          <div class="metric-value">{{ myMember?.battle_power ?? pvp.myBattlePower }}</div>
          <div class="metric-label">当前战力</div>
        </div>
        <div class="metric-card metric-card--gold">
          <div class="metric-value">{{ myMember?.correct_count || 0 }}</div>
          <div class="metric-label">答对题数</div>
        </div>
        <div class="metric-card metric-card--orange">
          <div class="metric-value">{{ myMember?.wrong_count || 0 }}</div>
          <div class="metric-label">答错题数</div>
        </div>
      </div>

      <div class="rank-list">
        <article
          v-for="member in pvp.allMembers"
          :key="member.user_id"
          class="rank-row"
          :class="{ 'is-me': member.user_id === auth.user?.id }"
        >
          <span>#{{ member.rank }}</span>
          <strong>{{ member.nickname }}</strong>
          <span>{{ member.battle_power }}</span>
        </article>
      </div>

      <div class="screen-actions screen-actions--center">
        <button type="button" class="primary-button" @click="backToLobby">返回大厅</button>
        <button type="button" class="secondary-button" @click="router.push('/records')">查看学习记录</button>
      </div>
    </section>

    <section v-else class="page-surface page-surface--light result-page">
      <div class="page-header page-header--center">
        <h2 class="page-title">当前没有可展示的结算快照</h2>
        <p class="page-subtitle">如果你刚刷新页面，旧会话快照可能已经丢失，直接回大厅重新进入即可。</p>
      </div>
      <div class="screen-actions screen-actions--center">
        <button type="button" class="primary-button" @click="backToLobby">返回大厅</button>
      </div>
    </section>
  </AppShell>
</template>

<style scoped>
.result-page {
  text-align: center;
}

.rank-list {
  display: grid;
  gap: 12px;
  width: min(720px, 100%);
  margin: 0 auto;
}

.rank-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  border: 1px solid var(--border);
  border-radius: 20px;
  background: rgba(255, 255, 255, 0.72);
}

.rank-row.is-me {
  border-color: rgba(91, 91, 214, 0.35);
  background: rgba(91, 91, 214, 0.08);
}

.rank-row span {
  color: var(--text-secondary);
}

.rank-row strong {
  color: var(--text-primary);
  font-family: var(--font-display);
}
</style>
