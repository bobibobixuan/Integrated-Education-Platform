<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useGameStore } from '@/stores/game'

const router = useRouter()
const game = useGameStore()

const passed = computed(() => game.phase === 'extreme-passed')

watch(() => game.phase, (phase) => {
  if (!['extreme-failed', 'extreme-passed'].includes(phase)) {
    router.replace('/extreme')
  }
}, { immediate: true })

async function retry() {
  await game.retryExtreme()
  if (game.phase === 'extreme-playing') {
    router.push('/extreme/session')
  }
}

function backToHub() {
  game.returnFromExtreme()
  router.push('/extreme')
}
</script>

<template>
  <AppShell>
    <section class="page-surface page-surface--light result-page">
      <div class="page-header page-header--center">
        <h2 class="page-title" :class="{ 'page-title--danger': !passed }">
          {{ passed ? '极限测试通过' : '考核失败' }}
        </h2>
        <p class="page-subtitle">
          {{ passed ? `全部 ${game.extremeRunCorrect} 题全对，一命通关。` : `本次已通过 ${game.extremeRunCorrect} / ${game.extremeRunAttempted} 题。` }}
        </p>
      </div>

      <div class="metrics-grid">
        <div class="metric-card metric-card--indigo">
          <div class="metric-value">{{ game.extremeRunCorrect }}</div>
          <div class="metric-label">正确题数</div>
        </div>
        <div class="metric-card metric-card--orange">
          <div class="metric-value">{{ game.extremeRunAttempted }}</div>
          <div class="metric-label">尝试题数</div>
        </div>
        <div class="metric-card metric-card--gold">
          <div class="metric-value">{{ game.extremeProgress.total }}</div>
          <div class="metric-label">挑战段数</div>
        </div>
      </div>

      <div class="screen-actions screen-actions--center">
        <button type="button" class="primary-button" @click="retry">{{ passed ? '再来一次' : '重新挑战' }}</button>
        <button type="button" class="secondary-button" @click="backToHub">返回入口页</button>
      </div>
    </section>
  </AppShell>
</template>

<style scoped>
.result-page {
  text-align: center;
}

.page-title--danger {
  color: var(--danger);
}
</style>
