<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useAuthStore } from '@/stores/auth'
import { usePvpStore } from '@/stores/pvp'

const router = useRouter()
const pvp = usePvpStore()
const auth = useAuthStore()
const answer = ref('')
const multiAnswers = ref<string[]>([])
let battleSyncTimer: ReturnType<typeof setInterval> | null = null
let battleHttpFallbackTimer: ReturnType<typeof setInterval> | null = null
const judgeOptions = [
  { letter: 'A', text: '正确' },
  { letter: 'B', text: '错误' },
]

function formatDuration(totalSeconds: number) {
  const safe = Math.max(0, totalSeconds)
  const hours = Math.floor(safe / 3600)
  const minutes = Math.floor((safe % 3600) / 60)
  const seconds = safe % 60
  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`
  }
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

const questionType = computed(() => {
  const q = pvp.currentQuestion
  if (!q) return 'fill'
  if (q.type === '判断题') return 'judge'
  if (!q.options?.length) return 'fill'
  if (q.type === '多选题') return 'multi'
  return 'choice'
})

const typeLabel = computed(() => {
  if (questionType.value === 'multi') return '多选题'
  if (questionType.value === 'judge') return '判断题'
  if (questionType.value === 'choice') return '单选题'
  return '填空题'
})

const progressLabel = computed(() => {
  if (!pvp.currentQuestion) return ''
  return `第 ${pvp.currentQuestion.question_order + 1} / ${pvp.questionCount} 题`
})

const myMember = computed(() => pvp.allMembers.find((member) => member.user_id === auth.user?.id) || null)
const waitingForRoomFinish = computed(() => pvp.sessionStatus === 'completed' && pvp.roomStatus !== 'finished')
const rankMembers = computed(() => pvp.allMembers.map((member) => ({
  ...member,
  trend: pvp.rankTrendFor(member.user_id),
})))
const totalDurationLabel = computed(() => formatDuration(pvp.battleTotalSeconds || pvp.room?.battle_time_limit_seconds || 0))
const remainingLabel = computed(() => formatDuration(pvp.battleTimeLeft))
const timerTone = computed(() => {
  if (pvp.battleTimeLeft <= 0) return 'timer-expired'
  if (pvp.battleTimeLeft <= 60) return 'timer-danger'
  if (pvp.battleTimeLeft <= 180) return 'timer-warning'
  return ''
})

function formatDisplayedAnswer(answerValue?: string) {
  if (!answerValue) return ''
  if (questionType.value === 'judge') {
    const normalized = answerValue.trim().toLowerCase()
    if (['a', 'true', '对', '正确', '是', '√', '1', 't', 'yes', 'y'].includes(normalized)) return '正确'
    if (['b', 'false', '错', '错误', '否', '×', '0', 'f', 'no', 'n'].includes(normalized)) return '错误'
  }
  return answerValue
}

onMounted(() => {
  pvp.setupWsHandlers()
  void pvp.fetchBattle()
  battleSyncTimer = setInterval(() => {
    pvp.requestBattleSnapshot()
  }, 1000)
  battleHttpFallbackTimer = setInterval(() => {
    void pvp.syncBattleProgress()
  }, 4000)
})

onUnmounted(() => {
  if (battleSyncTimer) {
    clearInterval(battleSyncTimer)
    battleSyncTimer = null
  }
  if (battleHttpFallbackTimer) {
    clearInterval(battleHttpFallbackTimer)
    battleHttpFallbackTimer = null
  }
})

function onSelectOption(value: string) {
  if (questionType.value === 'multi') {
    if (multiAnswers.value.includes(value)) {
      multiAnswers.value = multiAnswers.value.filter((item) => item !== value)
    } else {
      multiAnswers.value = [...multiAnswers.value, value].sort()
    }
    answer.value = multiAnswers.value.join('')
    return
  }
  answer.value = value
}

async function onSubmitAnswer() {
  if (!answer.value.trim()) return
  await pvp.answerQuestion(answer.value.trim())
}

function onNextQuestion() {
  answer.value = ''
  multiAnswers.value = []
  pvp.nextAfterFeedback()
}

async function onSyncFinalize() {
  const ok = await pvp.doFinalize()
  if (ok && pvp.roomStatus === 'finished') {
    router.replace('/pvp/result')
  }
}

watch(() => pvp.roomStatus, (status) => {
  if (status === 'finished') {
    router.replace('/pvp/result')
  }
})
</script>

<template>
  <AppShell compact>
    <div class="quiz-page">
      <!-- Error Banner -->
      <div v-if="pvp.error" class="error-banner">
        <span>{{ pvp.error }}</span>
        <button type="button" class="error-close" @click="pvp.error = ''">关闭</button>
      </div>

      <!-- Top Status Bar -->
      <div class="top-status-bar">
        <div class="tsb-group">
          <span class="tsb-label">当前模式</span>
          <span class="tsb-value">PVP 对战</span>
        </div>
        <div class="tsb-divider"></div>
        <div class="tsb-group">
          <span class="tsb-label">题目进度</span>
          <span class="tsb-value">{{ progressLabel || '—' }}</span>
        </div>
        <div class="tsb-divider"></div>
        <div class="tsb-group">
          <span class="tsb-label">战力 · 排名</span>
          <span class="tsb-value">{{ pvp.myBattlePower }} · #{{ pvp.myRank || '-' }}</span>
        </div>
        <div class="tsb-divider"></div>
        <div class="tsb-group">
          <span class="tsb-label">对 · 错</span>
          <span class="tsb-value">{{ myMember?.correct_count || 0 }} / {{ myMember?.wrong_count || 0 }}</span>
        </div>
        <div class="tsb-divider"></div>
        <div class="tsb-group">
          <span class="tsb-label">剩余时间</span>
          <span class="tsb-value" :class="timerTone">{{ remainingLabel }}</span>
        </div>
      </div>

      <!-- Main Battle Layout -->
      <section v-if="pvp.isMyTurn || waitingForRoomFinish" class="quiz-layout">
        <!-- Left: Question Card -->
        <article class="quiz-card">
          <!-- Header -->
          <div class="quiz-card__header">
            <div>
              <h2>{{ pvp.isMyTurn ? '当前题目' : '等待房间结束' }}</h2>
              <p v-if="pvp.isMyTurn">仔细阅读题目，选择或输入你的答案。</p>
              <p v-else>你的题目已经做完了。系统会在所有成员完成答题或总时长归零后自动跳转最终结算。</p>
            </div>
          </div>

          <!-- Active Question -->
          <article v-if="pvp.isMyTurn && pvp.currentQuestion" class="question-area">
            <div class="question-meta">
              <span class="q-type-badge" :class="`q-type--${questionType}`">{{ typeLabel }}</span>
              <span class="q-progress">{{ progressLabel }}</span>
              <span v-if="pvp.sessionStatus === 'active'" class="q-live">答题中</span>
            </div>

            <p class="question-text">{{ pvp.currentQuestion.content }}</p>

            <!-- Choice Options -->
            <div v-if="questionType === 'choice'" class="option-list">
              <p class="option-hint">选择一个正确答案</p>
              <button
                v-for="opt in pvp.currentQuestion.options"
                :key="opt.letter"
                type="button"
                class="option-btn"
                :class="{ 'is-selected': answer === opt.letter }"
                :disabled="pvp.showFeedback"
                @click="onSelectOption(opt.letter)"
              >
                <span class="option-letter" :class="{ 'is-chosen': answer === opt.letter }">{{ opt.letter }}</span>
                <span class="option-text">{{ opt.text }}</span>
              </button>
            </div>

            <!-- Multi-select Options -->
            <div v-else-if="questionType === 'multi'" class="option-list">
              <p class="option-hint">选择一个或多个正确答案</p>
              <button
                v-for="opt in pvp.currentQuestion.options"
                :key="opt.letter"
                type="button"
                class="option-btn"
                :class="{ 'is-selected': multiAnswers.includes(opt.letter) }"
                :disabled="pvp.showFeedback"
                @click="onSelectOption(opt.letter)"
              >
                <span class="option-letter" :class="{ 'is-chosen': multiAnswers.includes(opt.letter) }">
                  {{ multiAnswers.includes(opt.letter) ? '✓' : opt.letter }}
                </span>
                <span class="option-text">{{ opt.text }}</span>
              </button>
            </div>

            <!-- Judge Options -->
            <div v-else-if="questionType === 'judge'" class="option-list">
              <p class="option-hint">判断题请选择正确或错误</p>
              <button
                v-for="opt in judgeOptions"
                :key="opt.letter"
                type="button"
                class="option-btn"
                :class="{ 'is-selected': answer === opt.letter }"
                :disabled="pvp.showFeedback"
                @click="onSelectOption(opt.letter)"
              >
                <span class="option-letter" :class="{ 'is-chosen': answer === opt.letter }">{{ opt.letter }}</span>
                <span class="option-text">{{ opt.text }}</span>
              </button>
            </div>

            <!-- Fill Input -->
            <div v-else class="fill-panel">
              <p class="fill-label">输入你的答案</p>
              <input
                v-model="answer"
                type="text"
                class="fill-input"
                :disabled="pvp.showFeedback"
                placeholder="输入你的答案…"
                @keyup.enter="onSubmitAnswer"
              />
            </div>

            <!-- Action Buttons -->
            <div class="quiz-actions">
              <button
                type="button"
                class="btn-primary"
                :disabled="!answer.trim() || pvp.showFeedback"
                @click="onSubmitAnswer"
              >
                {{ questionType === 'multi' && !pvp.showFeedback ? `确认答案 (${multiAnswers.length} 项)` : '确认答案' }}
              </button>
            </div>

            <!-- Feedback Panel -->
            <Transition name="feedback-pop">
              <div v-if="pvp.showFeedback && pvp.lastPvpResult" class="feedback-inline" :class="{ 'is-wrong': !pvp.lastPvpResult.is_correct }">
                <div class="feedback-inline__icon">
                  <svg v-if="pvp.lastPvpResult.is_correct" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>
                  <svg v-else width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                </div>
                <div class="feedback-inline__body">
                  <strong>{{ pvp.lastPvpResult.is_correct ? '答案正确' : '答案错误' }}</strong>
                  <p v-if="pvp.lastPvpResult.is_correct">战力 +{{ pvp.lastPvpResult.battle_power_delta }}</p>
                  <p v-else>正确答案：<em>{{ formatDisplayedAnswer(pvp.lastPvpResult.correct_answer) }}</em></p>
                </div>
                <button type="button" class="btn-secondary btn-secondary--sm" @click="onNextQuestion">
                  {{ pvp.lastPvpResult.session_status === 'completed' ? '查看排名' : '下一题' }}
                </button>
              </div>
            </Transition>
          </article>

          <!-- Settle Wait (all questions done) -->
          <div v-else class="settle-wait">
            <div class="settle-wait__copy">
              <strong>你已完成本轮全部题目</strong>
              <p>现在仍会实时看到战力和排名变化。房间结束后会自动进入最终结算，并出现在大厅历史记录里。</p>
            </div>
            <div class="settle-wait__metrics">
              <div class="sw-metric">
                <span>当前排名</span>
                <strong>#{{ myMember?.rank || '-' }}</strong>
              </div>
              <div class="sw-metric">
                <span>当前战力</span>
                <strong>{{ myMember?.battle_power ?? pvp.myBattlePower }}</strong>
              </div>
              <div class="sw-metric">
                <span>答对 / 答错</span>
                <strong>{{ myMember?.correct_count || 0 }} / {{ myMember?.wrong_count || 0 }}</strong>
              </div>
            </div>
            <div class="settle-wait__actions">
              <button type="button" class="btn-secondary" @click="pvp.fetchBattle()">刷新状态</button>
              <button type="button" class="btn-secondary" @click="onSyncFinalize">同步结算</button>
            </div>
          </div>
        </article>

        <!-- Right: Side Panel -->
        <aside class="quiz-side">
          <!-- Countdown Card -->
          <article v-if="pvp.battleTotalSeconds > 0" class="side-card side-card--timer">
            <div class="side-card__header">
              <h3>倒计时</h3>
              <p>剩余答题时间</p>
            </div>
            <div class="countdown-display">
              <span class="countdown-value" :class="timerTone">{{ remainingLabel }}</span>
              <span class="countdown-total">/ {{ totalDurationLabel }}</span>
            </div>
            <div class="countdown-bar">
              <div class="countdown-bar__fill" :class="timerTone" :style="{ width: `${pvp.battleProgressPercent}%` }"></div>
            </div>
            <p class="countdown-note">时间归零后立即停止作答并自动结算。</p>
          </article>

          <!-- Ranking Card -->
          <article class="side-card">
            <div class="side-card__header">
              <h3>实时排名</h3>
              <p>答题结果实时刷新</p>
            </div>
            <TransitionGroup name="rank-shift" tag="div" class="rank-list">
              <div
                v-for="member in rankMembers"
                :key="member.user_id"
                class="rank-row"
                :class="[
                  { 'is-me': member.user_id === auth.user?.id },
                  member.trend ? `trend-${member.trend}` : '',
                ]"
              >
                <span class="rank-row__pos">#{{ member.rank }}</span>
                <span class="rank-row__name">{{ member.nickname }}</span>
                <span class="rank-row__power">{{ member.battle_power }}</span>
                <span v-if="member.trend === 'up'" class="rank-arrow rank-arrow--up">↑</span>
                <span v-else-if="member.trend === 'down'" class="rank-arrow rank-arrow--down">↓</span>
                <span v-else class="rank-arrow" style="visibility:hidden"> </span>
              </div>
            </TransitionGroup>
          </article>
        </aside>
      </section>

      <!-- Waiting for sync -->
      <div v-else-if="!pvp.loading" class="quiz-empty">
        <h2>等待题目或房间状态同步</h2>
        <p>如果老师刚开战或总时长刚刚结束，页面会自动刷新到最新状态。</p>
        <button type="button" class="btn-secondary" @click="pvp.fetchBattle()">刷新状态</button>
      </div>

      <!-- Loading -->
      <div v-if="pvp.loading" class="quiz-loading">正在同步对战状态…</div>
    </div>
  </AppShell>
</template>

<style scoped>
/* ── Page Shell ── */
.quiz-page {
  display: grid;
  gap: 16px;
  padding: 0 0 24px;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "PingFang SC", "Microsoft YaHei", sans-serif;
}

/* ── Error Banner ── */
.error-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 14px 20px;
  border-radius: 12px;
  background: rgba(255, 59, 48, 0.08);
  border: 1px solid rgba(255, 59, 48, 0.22);
  color: #b42318;
  font-size: 14px;
  font-weight: 600;
}

.error-close {
  flex-shrink: 0;
  border: none;
  background: rgba(255, 59, 48, 0.1);
  color: #b42318;
  font-size: 13px;
  font-weight: 700;
  padding: 6px 14px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.15s;
  font-family: inherit;
}

.error-close:hover {
  background: rgba(255, 59, 48, 0.18);
}

/* ── Top Status Bar ── */
.top-status-bar {
  display: flex;
  align-items: center;
  gap: 0;
  padding: 18px 28px;
  border-radius: 16px;
  background: #FFFFFF;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
}

.tsb-group {
  flex: 1;
  min-width: 0;
  padding: 0 20px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.tsb-label {
  font-size: 13px;
  color: #6b7280;
  font-weight: 600;
}

.tsb-value {
  font-size: 22px;
  font-weight: 800;
  color: #111827;
  letter-spacing: -0.02em;
}

.tsb-value.timer-warning { color: #f59e0b; }
.tsb-value.timer-danger  { color: #ef4444; }
.tsb-value.timer-expired { color: #dc2626; }

.tsb-divider {
  width: 1px;
  height: 44px;
  background: rgba(15, 23, 42, 0.08);
  flex-shrink: 0;
}

/* ── Timer Bar (global) ── */
.timer-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 20px;
  border-radius: 12px;
  background: #FFFFFF;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.timer-bar__track {
  flex: 1;
  height: 8px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.timer-bar__fill {
  height: 100%;
  border-radius: inherit;
  background: #007AFF;
  transition: width 1s linear;
}

.timer-bar__fill.timer-warning { background: #f59e0b; }
.timer-bar__fill.timer-danger  { background: #ef4444; }
.timer-bar__fill.timer-expired { background: #dc2626; }

.timer-bar__label {
  flex-shrink: 0;
  font-size: 13px;
  font-weight: 700;
  color: #6b7280;
  font-variant-numeric: tabular-nums;
}

/* ── Main Layout ── */
.quiz-layout {
  display: grid;
  grid-template-columns: minmax(720px, 1fr) 340px;
  gap: 16px;
  align-items: start;
}

/* ── Question Card ── */
.quiz-card {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
  padding: 28px;
  min-height: 480px;
  display: grid;
  gap: 20px;
  align-content: start;
}

.quiz-card__header h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}

.quiz-card__header p {
  margin: 6px 0 0;
  font-size: 14px;
  color: #6b7280;
}

/* ── Question Meta ── */
.question-meta {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.q-type-badge {
  display: inline-flex;
  align-items: center;
  padding: 5px 14px;
  border-radius: 999px;
  font-size: 13px;
  font-weight: 700;
  color: #007AFF;
  background: rgba(0, 122, 255, 0.08);
  border: 1px solid rgba(0, 122, 255, 0.45);
}

.q-type--multi { color: #f59e0b; background: rgba(245, 158, 11, 0.08); border-color: rgba(245, 158, 11, 0.45); }
.q-type--fill  { color: #22c55e; background: rgba(34, 197, 94, 0.08);  border-color: rgba(34, 197, 94, 0.45); }
.q-type--judge { color: #0ea5e9; background: rgba(14, 165, 233, 0.08);  border-color: rgba(14, 165, 233, 0.45); }

.q-progress {
  font-size: 13px;
  font-weight: 600;
  color: #6b7280;
}

.q-live {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(52, 199, 89, 0.1);
  color: #16a34a;
  font-size: 12px;
  font-weight: 700;
}

.q-live::before {
  content: '';
  width: 6px;
  height: 6px;
  border-radius: 999px;
  background: #22c55e;
  animation: livePulse 1.2s ease-in-out infinite;
}

@keyframes livePulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* ── Question Text ── */
.question-text {
  margin: 0;
  font-size: 26px;
  font-weight: 800;
  color: #111827;
  line-height: 1.35;
}

/* ── Options ── */
.option-list {
  display: grid;
  gap: 10px;
}

.option-hint {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
}

.option-btn {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 58px;
  padding: 14px 18px;
  border-radius: 10px;
  border: 1px solid #d6dbe5;
  background: #FFFFFF;
  color: #111827;
  cursor: pointer;
  text-align: left;
  font-family: inherit;
  font-size: 15px;
  transition: border-color 0.15s, background 0.15s, box-shadow 0.15s;
}

.option-btn:hover:not(:disabled) {
  border-color: rgba(0, 122, 255, 0.45);
  background: rgba(0, 122, 255, 0.035);
}

.option-btn.is-selected {
  border-color: #007AFF;
  background: rgba(0, 122, 255, 0.04);
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}

.option-btn:disabled {
  opacity: 0.7;
  cursor: default;
}

.option-letter {
  width: 32px;
  height: 32px;
  border-radius: 999px;
  background: #f1f3f7;
  color: #374151;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 700;
  flex-shrink: 0;
  transition: background 0.15s, color 0.15s;
}

.option-letter.is-chosen {
  background: #007AFF;
  color: #FFFFFF;
}

.option-text {
  flex: 1;
  min-width: 0;
}

/* ── Fill Panel ── */
.fill-panel {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #dfe3eb;
  background: #fafbfc;
}

.fill-label {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 700;
  color: #111827;
}

.fill-input {
  width: 100%;
  height: 44px;
  padding: 0 14px;
  border: 1px solid #d6dbe5;
  border-radius: 8px;
  font-size: 15px;
  font-family: inherit;
  color: #111827;
  background: #FFFFFF;
  outline: none;
  transition: border-color 0.15s, box-shadow 0.15s;
  box-sizing: border-box;
}

.fill-input:focus {
  border-color: #007AFF;
  box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.12);
}

.fill-input::placeholder {
  color: #9ca3af;
}

.fill-input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ── Quiz Actions ── */
.quiz-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.btn-primary {
  height: 46px;
  min-width: 128px;
  padding: 0 24px;
  border: none;
  border-radius: 10px;
  background: #007AFF;
  color: #FFFFFF;
  font-size: 15px;
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
  opacity: 0.55;
  cursor: not-allowed;
}

.btn-secondary {
  height: 46px;
  min-width: 128px;
  padding: 0 24px;
  border: 1px solid #d7dce6;
  border-radius: 10px;
  background: #FFFFFF;
  color: #374151;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s, transform 0.1s;
}

.btn-secondary:hover:not(:disabled) {
  border-color: rgba(0, 122, 255, 0.45);
  background: rgba(0, 122, 255, 0.04);
}

.btn-secondary:active:not(:disabled) {
  transform: scale(0.98);
}

.btn-secondary--sm {
  height: 40px;
  min-width: auto;
  padding: 0 18px;
  font-size: 14px;
  border-radius: 8px;
  flex-shrink: 0;
}

/* ── Feedback Inline ── */
.feedback-inline {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 20px;
  border-radius: 12px;
  background: rgba(52, 199, 89, 0.08);
  border: 1px solid rgba(52, 199, 89, 0.22);
}

.feedback-inline.is-wrong {
  background: rgba(255, 59, 48, 0.08);
  border-color: rgba(255, 59, 48, 0.22);
}

.feedback-inline__icon {
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: rgba(52, 199, 89, 0.15);
  color: #16a34a;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feedback-inline.is-wrong .feedback-inline__icon {
  background: rgba(255, 59, 48, 0.12);
  color: #dc2626;
}

.feedback-inline__body {
  flex: 1;
  min-width: 0;
}

.feedback-inline__body strong {
  display: block;
  font-size: 16px;
  color: #16a34a;
}

.feedback-inline.is-wrong .feedback-inline__body strong {
  color: #dc2626;
}

.feedback-inline__body p {
  margin: 4px 0 0;
  font-size: 14px;
  color: #374151;
}

.feedback-inline__body em {
  font-style: normal;
  font-weight: 700;
  color: #007AFF;
}

/* ── Settle Wait ── */
.settle-wait {
  display: grid;
  gap: 20px;
}

.settle-wait__copy strong {
  display: block;
  font-size: 18px;
  font-weight: 800;
  color: #111827;
}

.settle-wait__copy p {
  margin: 8px 0 0;
  font-size: 14px;
  color: #6b7280;
  line-height: 1.6;
}

.settle-wait__metrics {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.sw-metric {
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  background: #fafbfc;
  text-align: center;
}

.sw-metric span {
  display: block;
  font-size: 12px;
  color: #6b7280;
  font-weight: 600;
  margin-bottom: 6px;
}

.sw-metric strong {
  display: block;
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}

.settle-wait__actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

/* ── Side Cards ── */
.quiz-side {
  display: grid;
  gap: 14px;
}

.side-card {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 4px 16px rgba(15, 23, 42, 0.04);
  padding: 20px;
}

.side-card__header h3 {
  margin: 0;
  font-size: 17px;
  font-weight: 800;
  color: #111827;
}

.side-card__header p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #6b7280;
}

/* ── Side Stats ── */
.side-stats {
  display: grid;
  gap: 8px;
  margin-top: 16px;
}

.side-stat {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-radius: 10px;
  background: #f8f9fb;
  border: 1px solid rgba(15, 23, 42, 0.06);
}

.side-stat span {
  font-size: 13px;
  color: #6b7280;
  font-weight: 600;
}

.side-stat strong {
  font-size: 16px;
  font-weight: 800;
  color: #111827;
}

/* ── Countdown ── */
.countdown-display {
  display: flex;
  align-items: baseline;
  gap: 4px;
  margin-top: 16px;
}

.countdown-value {
  font-size: 40px;
  font-weight: 800;
  color: #111827;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.02em;
  line-height: 1;
}

.countdown-value.timer-warning { color: #f59e0b; }
.countdown-value.timer-danger  { color: #ef4444; }
.countdown-value.timer-expired { color: #dc2626; }

.countdown-total {
  font-size: 16px;
  color: #9ca3af;
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}

.countdown-bar {
  height: 6px;
  margin-top: 14px;
  border-radius: 999px;
  background: rgba(15, 23, 42, 0.06);
  overflow: hidden;
}

.countdown-bar__fill {
  height: 100%;
  border-radius: inherit;
  background: #007AFF;
  transition: width 1s linear;
}

.countdown-bar__fill.timer-warning { background: #f59e0b; }
.countdown-bar__fill.timer-danger  { background: #ef4444; }
.countdown-bar__fill.timer-expired { background: #dc2626; }

.countdown-note {
  margin: 10px 0 0;
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.5;
}

/* ── Ranking List ── */
.rank-list {
  display: grid;
  gap: 6px;
  margin-top: 14px;
}

.rank-row {
  display: grid;
  grid-template-columns: 36px 1fr auto auto;
  gap: 8px;
  align-items: center;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid transparent;
  transition: border-color 0.15s, background 0.15s;
}

.rank-row.is-me {
  background: rgba(0, 122, 255, 0.08);
  border-color: rgba(0, 122, 255, 0.2);
}

.rank-row__pos {
  font-size: 14px;
  font-weight: 800;
  color: #6b7280;
}

.rank-row.is-me .rank-row__pos {
  color: #007AFF;
}

.rank-row__name {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.rank-row.is-me .rank-row__name {
  color: #007AFF;
  font-weight: 700;
}

.rank-row__power {
  font-size: 14px;
  font-weight: 800;
  color: #374151;
  font-variant-numeric: tabular-nums;
}

.rank-arrow {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 900;
}

.rank-arrow--up {
  color: #16a34a;
  background: rgba(52, 199, 89, 0.12);
}

.rank-arrow--down {
  color: #dc2626;
  background: rgba(255, 59, 48, 0.1);
}

/* rank animations */
.rank-row.trend-up {
  animation: rankPulseUp 0.8s ease-out;
}

.rank-row.trend-down {
  animation: rankPulseDown 0.8s ease-out;
}

.rank-shift-move {
  transition: transform 0.3s ease;
}

.rank-shift-enter-active {
  animation: rankReveal 0.24s ease;
}

@keyframes rankPulseUp {
  0% { transform: translateY(0); }
  35% { transform: translateY(-6px); }
  100% { transform: translateY(0); }
}

@keyframes rankPulseDown {
  0% { transform: translateY(0); }
  35% { transform: translateY(6px); }
  100% { transform: translateY(0); }
}

@keyframes rankReveal {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

/* feedback transition */
.feedback-pop-enter-active {
  animation: fbFadeUp 0.28s ease;
}

.feedback-pop-leave-active {
  animation: fbFadeUp 0.16s ease reverse;
}

@keyframes fbFadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* ── Empty / Loading ── */
.quiz-empty {
  background: #FFFFFF;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.08);
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
  padding: 48px 28px;
  text-align: center;
}

.quiz-empty h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 800;
  color: #111827;
}

.quiz-empty p {
  margin: 10px 0 20px;
  font-size: 14px;
  color: #6b7280;
}

.quiz-loading {
  text-align: center;
  padding: 32px;
  font-size: 15px;
  color: #6b7280;
}

/* ── Responsive ── */
@media (max-width: 1100px) {
  .quiz-layout {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .top-status-bar {
    flex-wrap: wrap;
    gap: 10px;
    padding: 16px;
  }

  .tsb-group {
    flex: 1 1 40%;
    padding: 0 10px;
  }

  .tsb-divider {
    display: none;
  }

  .tsb-value {
    font-size: 18px;
  }

  .quiz-card {
    padding: 20px;
  }

  .question-text {
    font-size: 22px;
  }

  .quiz-actions {
    flex-direction: column;
  }

  .btn-primary,
  .btn-secondary {
    width: 100%;
  }

  .settle-wait__metrics {
    grid-template-columns: 1fr;
  }

  .feedback-inline {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
