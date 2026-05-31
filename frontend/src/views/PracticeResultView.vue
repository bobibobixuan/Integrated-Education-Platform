<script setup lang="ts">
import { watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useGameStore } from '@/stores/game'

const router = useRouter()
const game = useGameStore()

watch(() => game.phase, (phase) => {
  if (phase !== 'practice-results') {
    router.replace('/practice')
  }
}, { immediate: true })

function backToHub() {
  game.returnFromPractice()
  router.push('/practice')
}
</script>

<template>
  <AppShell>
    <section class="page-surface page-surface--light result-page">
      <div class="page-header page-header--center">
        <h2 class="page-title">练习总结</h2>
        <p class="page-subtitle">练习模式单独收口到总结页，继续练和返回导航不再和题目页抢位置。</p>
      </div>

      <div class="metrics-grid">
        <div class="metric-card metric-card--indigo">
          <div class="metric-value">{{ game.practiceTotalCount }}</div>
          <div class="metric-label">已答题数</div>
        </div>
        <div class="metric-card metric-card--green">
          <div class="metric-value">{{ game.practiceCorrectCount }}</div>
          <div class="metric-label">答对题数</div>
        </div>
        <div class="metric-card metric-card--gold">
          <div class="metric-value">{{ game.practiceAccuracy }}%</div>
          <div class="metric-label">正确率</div>
        </div>
        <div class="metric-card metric-card--orange">
          <div class="metric-value">{{ game.practiceQuestionCount }}</div>
          <div class="metric-label">练习题池</div>
        </div>
      </div>

      <div class="screen-actions screen-actions--center">
        <button type="button" class="primary-button" @click="backToHub">继续练习</button>
        <button type="button" class="secondary-button" @click="router.push('/records')">查看学习记录</button>
      </div>
    </section>
  </AppShell>
</template>

<style scoped>
.result-page {
  text-align: center;
}
</style>
