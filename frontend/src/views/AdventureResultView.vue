<script setup lang="ts">
import { computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useGameStore } from '@/stores/game'

const router = useRouter()
const game = useGameStore()

const accuracy = computed(() => {
  if (!game.sessionQuestionCount) return 0
  return Math.round((game.sessionCorrect / game.sessionQuestionCount) * 100)
})

watch(() => game.phase, (phase) => {
  if (phase !== 'results') {
    router.replace('/adventure')
  }
}, { immediate: true })

function backToMap() {
  game.returnToMenu()
  router.push('/adventure')
}
</script>

<template>
  <AppShell>
    <div class="result-container">
      <!-- Left: Settlement Card -->
      <section class="settlement-card">
        <div class="check-badge">
          <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#34C759" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <h1 class="settlement-title">关卡完成</h1>
        <p class="settlement-desc">查看本次得分、正确率和连击表现。</p>
        <div class="settlement-divider"></div>
        <div class="settlement-actions">
          <button type="button" class="btn-primary" @click="backToMap">返回地图</button>
          <button type="button" class="btn-secondary" @click="router.push('/records')">查看学习记录</button>
        </div>
      </section>

      <!-- Right: Stats Grid -->
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-accent stat-accent--blue"></div>
          <div class="stat-value">{{ game.totalScore }}</div>
          <div class="stat-label">获得积分</div>
        </div>
        <div class="stat-card">
          <div class="stat-accent stat-accent--green"></div>
          <div class="stat-value">{{ game.sessionCorrect }}<span class="stat-sub"> / {{ game.sessionQuestionCount }}</span></div>
          <div class="stat-label">正确题数</div>
        </div>
        <div class="stat-card">
          <div class="stat-accent stat-accent--orange"></div>
          <div class="stat-value">{{ game.bestCombo }}</div>
          <div class="stat-label">最高连击</div>
        </div>
        <div class="stat-card">
          <div class="stat-accent stat-accent--red"></div>
          <div class="stat-value">{{ accuracy }}<span class="stat-suffix">%</span></div>
          <div class="stat-label">正确率</div>
        </div>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
/* ── Layout ── */
.result-container {
  display: grid;
  grid-template-columns: 430px 1fr;
  gap: 24px;
  align-items: stretch;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ── Settlement Card ── */
.settlement-card {
  background: #FFFFFF;
  border-radius: 20px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
  padding: 44px 36px;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.check-badge {
  width: 72px;
  height: 72px;
  border-radius: 999px;
  background: rgba(52, 199, 89, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24px;
}

.settlement-title {
  margin: 0 0 10px;
  font-size: 32px;
  font-weight: 700;
  color: #000000;
  letter-spacing: -0.02em;
}

.settlement-desc {
  margin: 0;
  font-size: 15px;
  color: rgba(60, 60, 67, 0.6);
  line-height: 1.5;
}

.settlement-divider {
  width: 100%;
  height: 1px;
  background: rgba(60, 60, 67, 0.12);
  margin: 32px 0;
}

.settlement-actions {
  width: 100%;
  display: grid;
  gap: 12px;
}

/* ── Buttons ── */
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
  font-size: 16px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}

.btn-primary:hover {
  background: #006EE6;
}

.btn-primary:active {
  transform: scale(0.98);
}

.btn-secondary {
  width: 100%;
  height: 46px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(60, 60, 67, 0.18);
  border-radius: 12px;
  background: #FFFFFF;
  color: #000000;
  font-size: 16px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  transition: background 0.15s, transform 0.1s;
}

.btn-secondary:hover {
  background: rgba(0, 0, 0, 0.03);
}

.btn-secondary:active {
  transform: scale(0.98);
}

/* ── Stats Grid ── */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-content: start;
}

.stat-card {
  background: #FFFFFF;
  border-radius: 18px;
  border: 1px solid rgba(60, 60, 67, 0.12);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
  padding: 36px 32px;
  display: flex;
  flex-direction: column;
}

.stat-accent {
  width: 22px;
  height: 4px;
  border-radius: 999px;
  margin-bottom: 20px;
}

.stat-accent--blue   { background: #007AFF; }
.stat-accent--green  { background: #34C759; }
.stat-accent--orange { background: #FF9500; }
.stat-accent--red    { background: #FF3B30; }

.stat-value {
  font-size: 52px;
  font-weight: 700;
  color: #000000;
  line-height: 1.05;
  margin-bottom: 8px;
  word-break: break-all;
}

.stat-sub {
  font-size: 24px;
  font-weight: 500;
  color: rgba(60, 60, 67, 0.36);
}

.stat-suffix {
  font-size: 24px;
  font-weight: 500;
  color: rgba(60, 60, 67, 0.36);
  margin-left: 2px;
}

.stat-label {
  font-size: 17px;
  font-weight: 600;
  color: rgba(60, 60, 67, 0.6);
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .result-container {
    grid-template-columns: 1fr;
  }

  .settlement-card {
    padding: 32px 24px;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
  }

  .stat-value {
    font-size: 40px;
  }
}

@media (max-width: 420px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .settlement-title {
    font-size: 26px;
  }

  .check-badge {
    width: 60px;
    height: 60px;
  }

  .settlement-card {
    padding: 28px 20px;
  }

  .stat-card {
    padding: 28px 24px;
  }

  .stat-value {
    font-size: 36px;
  }
}
</style>
