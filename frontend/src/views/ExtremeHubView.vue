<script setup lang="ts">
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useGameStore } from '@/stores/game'
import type { UnitOut } from '@/types/api'

const router = useRouter()
const game = useGameStore()

const selectedUnit = computed<UnitOut | null>(() =>
  game.units.find(unit => unit.id === game.selectedUnitId) ?? null
)
const dualEnabled = computed(() => game.units.length >= 2)
const selectedUnitMark = computed(() => {
  const name = selectedUnit.value?.name?.trim()
  return name ? name.slice(0, 1) : '课'
})
const dualUnitNames = computed(() =>
  game.units.slice(0, 2).map(unit => unit.name).join(' + ')
)

async function startSingleUnitExtreme() {
  if (!selectedUnit.value) return
  await game.selectExtreme(`unit:${selectedUnit.value.id}`)
  if (game.phase === 'extreme-playing') {
    router.push('/extreme/session')
  }
}

async function startDualExtreme() {
  await game.selectExtreme('dual')
  if (game.phase === 'extreme-playing') {
    router.push('/extreme/session')
  }
}

function onUnitChange() {
  if (game.selectedUnitId) return
  const firstUnit = game.units[0]
  if (firstUnit) {
    game.selectedUnitId = firstUnit.id
  }
}

onMounted(async () => {
  await game.loadUnits()
  if (!game.selectedUnitId && game.units[0]) {
    game.selectedUnitId = game.units[0].id
  }
})
</script>

<template>
  <AppShell>
    <div class="ex-page">
      <div v-if="game.error" class="ex-error">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <span>{{ game.error }}</span>
        <button type="button" class="ex-error-close" @click="game.error = ''">关闭</button>
      </div>

      <header class="ex-header">
        <h1 class="ex-title">极限挑战</h1>
        <p class="ex-desc">一命到底，答错即止。先选择单元，再决定进入单元极限或双单元连考。</p>
      </header>

      <div v-if="game.loading && game.units.length === 0" class="ex-loading">正在加载挑战配置…</div>

      <div v-else class="ex-layout">
        <aside class="ex-left">
          <h3 class="ex-section-title">挑战单元</h3>
          <select v-model="game.selectedUnitId" class="ex-select" @change="onUnitChange">
            <option :value="null" disabled>请选择挑战单元</option>
            <option v-for="unit in game.units" :key="unit.id" :value="unit.id">{{ unit.name }}</option>
          </select>

          <div class="ex-rule-card">
            <strong>规则保持不变</strong>
            <p>极限模式仍然是一命到底，任意题答错立即结束；通关后才会计入极限统计。</p>
          </div>
        </aside>

        <section class="ex-right">
          <div v-if="!selectedUnit" class="ex-card ex-card--empty">
            <h3>先选择挑战单元</h3>
            <p>从左侧选一个单元后，可以开始该单元的极限挑战。</p>
          </div>

          <template v-else>
            <div class="ex-card">
              <div class="ex-unit-head">
                <span class="ex-unit-icon">{{ selectedUnitMark }}</span>
                <div>
                  <h3>{{ selectedUnit.name }}</h3>
                  <p>{{ selectedUnit.learning_goal || selectedUnit.description }}</p>
                </div>
              </div>
            </div>

            <div class="ex-card">
              <h4 class="ex-card-label">选择挑战模式</h4>

              <button type="button" class="mode-card" @click="startSingleUnitExtreme">
                <div class="mode-card-icon mode-card-icon--green" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                    <path d="M7 4H17V20H7V4Z" stroke="currentColor" stroke-width="1.8"/>
                    <path d="M9.5 8H14.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                    <path d="M9.5 12H14.5" stroke="currentColor" stroke-width="1.8" stroke-linecap="round"/>
                  </svg>
                </div>
                <div class="mode-card-body">
                  <strong>{{ selectedUnit.name }} 极限测</strong>
                  <span>连续挑战当前单元全部关卡，只要错一题就立刻结束。</span>
                </div>
              </button>

              <button type="button" class="mode-card mode-card--dual" :disabled="!dualEnabled" @click="startDualExtreme">
                <div class="mode-card-icon mode-card-icon--amber" aria-hidden="true">
                  <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
                    <path d="M5 6.5C5 5.7 5.7 5 6.5 5H10V19H6.5C5.7 19 5 18.3 5 17.5V6.5Z" stroke="currentColor" stroke-width="1.8"/>
                    <path d="M14 5H17.5C18.3 5 19 5.7 19 6.5V17.5C19 18.3 18.3 19 17.5 19H14V5Z" stroke="currentColor" stroke-width="1.8"/>
                    <path d="M12 5V19" stroke="currentColor" stroke-width="1.8"/>
                  </svg>
                </div>
                <div class="mode-card-body">
                  <strong>双单元综合大考</strong>
                  <span v-if="dualEnabled">{{ dualUnitNames }} 连续作答，规则仍然是一题都不能错。</span>
                  <span v-else>至少需要两个单元后，才能开启双单元极限挑战。</span>
                </div>
              </button>

              <div class="ex-summary">
                <span>当前单元：{{ selectedUnit.name }}</span>
                <span>关卡数：{{ Array.isArray(selectedUnit.levels) ? selectedUnit.levels.length : 0 }}</span>
                <span>双单元：{{ dualEnabled ? dualUnitNames : '暂不可用' }}</span>
              </div>
            </div>
          </template>
        </section>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.ex-page {
  max-width: 1100px;
  margin: 0 auto;
  width: 100%;
  display: grid;
  gap: 18px;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
}

.ex-error {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 12px;
  background: rgba(255,59,48,0.08);
  border: 1px solid rgba(255,59,48,0.35);
  color: #FF3B30;
  font-size: 14px;
}
.ex-error span { flex: 1; }
.ex-error-close {
  height: 28px;
  padding: 0 10px;
  border: none;
  border-radius: 8px;
  background: rgba(255,59,48,0.12);
  color: #FF3B30;
  font-size: 12px;
  cursor: pointer;
}

.ex-header { text-align: center; padding: 4px 0 0; }
.ex-title { margin: 0; font-size: 28px; font-weight: 700; color: #000; }
.ex-desc { margin: 6px 0 0; font-size: 14px; color: rgba(60,60,67,0.6); }
.ex-loading { text-align: center; padding: 40px; color: rgba(60,60,67,0.6); }
.ex-section-title { margin: 0 0 10px; font-size: 16px; font-weight: 700; color: #000; }

.ex-layout { display: grid; grid-template-columns: 300px 1fr; gap: 20px; align-items: start; }
.ex-left { display: grid; gap: 14px; }
.ex-right { display: grid; gap: 16px; }

.ex-select {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border-radius: 12px;
  border: 1px solid rgba(60,60,67,0.18);
  background: #FFFFFF;
  font-size: 15px;
  font-family: inherit;
  color: #000;
  outline: none;
  cursor: pointer;
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%23666' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat;
  background-position: right 14px center;
  padding-right: 36px;
}
.ex-select:focus { border-color: #007AFF; box-shadow: 0 0 0 3px rgba(0,122,255,0.12); }

.ex-rule-card,
.ex-card {
  padding: 24px;
  border-radius: 18px;
  background: #FFFFFF;
  border: 1px solid rgba(60,60,67,0.12);
  box-shadow: 0 1px 2px rgba(0,0,0,0.03);
}
.ex-rule-card strong { display: block; font-size: 15px; color: #000; margin-bottom: 6px; }
.ex-rule-card p { margin: 0; font-size: 13px; line-height: 1.5; color: rgba(60,60,67,0.6); }

.ex-card--empty { text-align: center; padding: 40px 24px; }
.ex-card--empty h3 { margin: 0 0 8px; font-size: 18px; font-weight: 700; color: #000; }
.ex-card--empty p { margin: 0; font-size: 14px; color: rgba(60,60,67,0.6); }
.ex-card-label { margin: 0 0 12px; font-size: 15px; font-weight: 700; color: #000; }

.ex-unit-head { display: flex; align-items: flex-start; gap: 14px; }
.ex-unit-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 12px;
  background: rgba(255,149,0,0.1);
  color: #FF9500;
  font-size: 18px;
  font-weight: 700;
  flex-shrink: 0;
}
.ex-unit-head h3 { margin: 0 0 4px; font-size: 20px; font-weight: 700; color: #000; }
.ex-unit-head p { margin: 0; font-size: 13px; line-height: 1.5; color: rgba(60,60,67,0.6); }

.mode-card {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 10px;
  padding: 18px 20px;
  border-radius: 14px;
  border: 1px solid rgba(60,60,67,0.12);
  background: #FFFFFF;
  text-align: left;
  font-family: inherit;
  cursor: pointer;
  transition: box-shadow 0.15s, border-color 0.15s;
}
.mode-card:hover:not(:disabled) { box-shadow: 0 4px 16px rgba(0,0,0,0.06); border-color: rgba(0,122,255,0.25); }
.mode-card:disabled { opacity: 0.5; cursor: not-allowed; }
.mode-card--dual { background: rgba(0,122,255,0.02); border-color: rgba(0,122,255,0.15); }

.mode-card-icon {
  width: 46px;
  height: 46px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.mode-card-icon--green { background: rgba(52,199,89,0.12); color: #34C759; }
.mode-card-icon--amber { background: rgba(255,149,0,0.12); color: #FF9500; }

.mode-card-body { flex: 1; min-width: 0; }
.mode-card-body strong { display: block; margin-bottom: 4px; font-size: 16px; font-weight: 700; color: #000; }
.mode-card-body span { font-size: 13px; line-height: 1.4; color: rgba(60,60,67,0.6); }

.ex-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding-top: 14px;
  border-top: 1px solid rgba(60,60,67,0.1);
  margin-top: 4px;
  font-size: 13px;
  color: rgba(60,60,67,0.6);
}

@media (max-width: 768px) {
  .ex-layout { grid-template-columns: 1fr; }
}
</style>
