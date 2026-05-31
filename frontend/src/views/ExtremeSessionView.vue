<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useGameStore } from '@/stores/game'

const router = useRouter()
const game = useGameStore()
const answer = ref('')
const showFeedback = ref(false)
const multiAnswers = ref<string[]>([])
const judgeOptions = [
  { letter: 'A', text: '正确' },
  { letter: 'B', text: '错误' },
]

const currentQuestionLabel = computed(() => {
  if (!game.currentQuestion) return ''
  return `${game.currentQuestion.question_order + 1} / ${game.currentQuestion.total_questions}`
})

const questionMode = computed(() => {
  const question = game.currentQuestion
  if (question?.question_type === '判断题') return 'judge'
  if (!question?.options?.length) return 'fill'
  if (question.question_type === '多选题') return 'multi'
  return 'choice'
})

const questionTypeLabel = computed(() => {
  if (questionMode.value === 'multi') return '多选题'
  if (questionMode.value === 'judge') return '判断题'
  if (questionMode.value === 'choice') return '单选题'
  return '填空题'
})

function formatDisplayedAnswer(answerValue?: string) {
  if (!answerValue) return ''
  if (questionMode.value === 'judge') {
    const normalized = answerValue.trim().toLowerCase()
    if (['a', 'true', '对', '正确', '是', '√', '1', 't', 'yes', 'y'].includes(normalized)) return '正确'
    if (['b', 'false', '错', '错误', '否', '×', '0', 'f', 'no', 'n'].includes(normalized)) return '错误'
  }
  return answerValue
}

function selectOption(value: string) {
  if (questionMode.value === 'multi') {
    if (multiAnswers.value.includes(value)) {
      multiAnswers.value = multiAnswers.value.filter(item => item !== value)
    } else {
      multiAnswers.value = [...multiAnswers.value, value].sort()
    }
    answer.value = multiAnswers.value.join('')
    return
  }
  answer.value = value
}

async function submit() {
  if (!answer.value.trim()) return
  showFeedback.value = true
  await game.answerExtremeQuestion(answer.value.trim())
}

async function nextQuestion() {
  showFeedback.value = false
  answer.value = ''
  multiAnswers.value = []
  if (game.phase === 'extreme-playing' && game.answeredCount >= game.sessionQuestionCount) {
    await game.onExtremeSegmentComplete()
    return
  }
  await game.loadNextQuestion()
}

watch(() => game.phase, (phase) => {
  if (phase === 'extreme-failed' || phase === 'extreme-passed') {
    router.replace('/extreme/result')
    return
  }
  if (phase !== 'extreme-playing') {
    router.replace('/extreme')
  }
}, { immediate: true })
</script>

<template>
  <AppShell compact>
    <div class="quiz-page">
      <div class="quiz-layout">
        <section class="quiz-card">
          <div class="qc-meta">
            <span class="qc-badge">{{ questionTypeLabel }}</span>
            <span class="qc-num">{{ currentQuestionLabel }}</span>
          </div>
          <p class="qc-text">{{ game.currentQuestion?.content }}</p>
          <div v-if="questionMode === 'choice'" class="qc-options">
            <button v-for="opt in game.currentQuestion!.options" :key="opt.letter" type="button" class="qc-opt" :class="{ 'qc-opt--sel': answer === opt.letter }" :disabled="showFeedback" @click="selectOption(opt.letter)">
              <span class="qc-opt-letter">{{ opt.letter }}</span><span>{{ opt.text }}</span>
            </button>
          </div>
          <div v-else-if="questionMode === 'multi'" class="qc-options">
            <button v-for="opt in game.currentQuestion!.options" :key="opt.letter" type="button" class="qc-opt" :class="{ 'qc-opt--sel': multiAnswers.includes(opt.letter) }" :disabled="showFeedback" @click="selectOption(opt.letter)">
              <span class="qc-opt-letter">{{ multiAnswers.includes(opt.letter) ? '✓' : opt.letter }}</span><span>{{ opt.text }}</span>
            </button>
          </div>
          <div v-else-if="questionMode === 'judge'" class="qc-options">
            <button v-for="opt in judgeOptions" :key="opt.letter" type="button" class="qc-opt" :class="{ 'qc-opt--sel': answer === opt.letter }" :disabled="showFeedback" @click="selectOption(opt.letter)">
              <span class="qc-opt-letter">{{ opt.letter }}</span><span>{{ opt.text }}</span>
            </button>
          </div>
          <div v-else class="qc-fill">
            <input v-model="answer" type="text" :disabled="showFeedback" placeholder="输入答案" class="qc-input" @keyup.enter="submit" />
          </div>
          <div class="qc-actions">
            <button type="button" class="btn-submit" :disabled="showFeedback || !answer.trim()" @click="submit">
              {{ questionMode === 'multi' && !showFeedback ? `确认答案 (${multiAnswers.length} 项)` : '确认答案' }}
            </button>
          </div>
          <div v-if="showFeedback && game.lastResult" class="qc-feedback" :class="{ 'qc-feedback--wrong': !game.lastResult.is_correct }">
            <strong>{{ game.lastResult.is_correct ? '✓ 继续前进' : '✕ 挑战失败' }}</strong>
            <span v-if="!game.lastResult.is_correct">正确答案：{{ formatDisplayedAnswer(game.lastResult.correct_answer) }}</span>
            <span v-else>得分 +{{ game.lastResult.score_added }}</span>
            <div v-if="game.lastResult.is_correct" class="qc-fb-actions">
              <button type="button" class="btn-next" @click="nextQuestion">下一题</button>
            </div>
          </div>
        </section>
        <aside class="quiz-side">
          <div class="quiz-status">
            <div class="qs-group"><span class="qs-label">关卡</span><strong>{{ game.currentSegment?.levelName || '极限' }}</strong></div>
            <div class="qs-group"><span class="qs-label">进度</span><strong>{{ game.extremeProgress.label }}</strong></div>
            <div class="qs-group"><span class="qs-label">正确</span><strong>{{ game.extremeRunCorrect }}</strong></div>
            <div class="qs-group"><span class="qs-label">容错</span><strong style="color:#FF3B30">0</strong></div>
          </div>
        </aside>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.quiz-page{max-width:1100px;margin:0 auto;width:100%;font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif;}
.quiz-layout{display:grid;grid-template-columns:1fr 200px;gap:16px;align-items:start;}

.quiz-side{display:grid;gap:12px;}
.quiz-status{padding:18px;border-radius:16px;background:#FFFFFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.03);display:grid;gap:12px;}
.qs-group{text-align:center;}
.qs-label{display:block;font-size:11px;color:rgba(60,60,67,0.45);text-transform:uppercase;letter-spacing:0.05em;margin-bottom:2px;}
.qs-group strong{font-size:18px;font-weight:800;color:#000;}
.quiz-card{padding:32px;border-radius:20px;background:#FFFFFF;border:1px solid rgba(60,60,67,0.12);box-shadow:0 1px 2px rgba(0,0,0,0.04),0 8px 24px rgba(0,0,0,0.05);display:grid;gap:20px;}
.qc-meta{display:flex;align-items:center;justify-content:space-between;gap:12px;}
.qc-badge{padding:4px 14px;border-radius:8px;font-size:13px;font-weight:700;background:rgba(0,122,255,0.08);color:#007AFF;border:1px solid rgba(0,122,255,0.25);}
.qc-num{font-size:14px;color:rgba(60,60,67,0.5);font-weight:600;}
.qc-text{margin:0;font-size:24px;font-weight:800;color:#000;line-height:1.4;}
.qc-options{display:grid;gap:10px;}
.qc-opt{display:flex;align-items:center;gap:14px;width:100%;min-height:56px;padding:12px 18px;border-radius:12px;border:1px solid rgba(60,60,67,0.12);background:#FFFFFF;text-align:left;font-family:inherit;font-size:15px;color:#000;cursor:pointer;transition:border-color 0.15s,background 0.15s;}
.qc-opt:hover:not(:disabled){border-color:rgba(0,122,255,0.3);background:rgba(0,122,255,0.02);}
.qc-opt:disabled{cursor:not-allowed;opacity:0.7;}
.qc-opt--sel{border-color:#007AFF;background:rgba(0,122,255,0.04);}
.qc-opt-letter{width:32px;height:32px;display:flex;align-items:center;justify-content:center;border-radius:999px;background:rgba(0,122,255,0.08);color:#007AFF;font-size:14px;font-weight:800;flex-shrink:0;}
.qc-opt--sel .qc-opt-letter{background:#007AFF;color:#fff;}
.qc-fill{display:grid;}
.qc-input{height:52px;padding:0 16px;border-radius:12px;border:1px solid rgba(60,60,67,0.18);background:#fff;font-size:16px;font-family:inherit;outline:none;transition:border-color 0.15s;}
.qc-input:focus{border-color:#007AFF;box-shadow:0 0 0 3px rgba(0,122,255,0.12);}
.qc-input::placeholder{color:rgba(60,60,67,0.35);}
.qc-actions{display:flex;justify-content:flex-end;}
.btn-submit{height:46px;padding:0 32px;border:none;border-radius:12px;background:#007AFF;color:#fff;font-size:16px;font-weight:600;font-family:inherit;cursor:pointer;transition:background 0.15s;}
.btn-submit:hover:not(:disabled){background:#006EE6;}
.btn-submit:disabled{opacity:0.45;cursor:not-allowed;}
.qc-feedback{display:flex;flex-direction:column;gap:8px;padding:16px 20px;border-radius:14px;background:rgba(52,199,89,0.08);border:1px solid rgba(52,199,89,0.2);}
.qc-feedback--wrong{background:rgba(255,59,48,0.06);border-color:rgba(255,59,48,0.2);}
.qc-feedback strong{font-size:15px;font-weight:700;color:#34C759;}
.qc-feedback--wrong strong{color:#FF3B30;}
.qc-feedback span{font-size:13px;color:rgba(60,60,67,0.6);}
.qc-fb-actions{margin-top:4px;}
.btn-next{height:40px;padding:0 20px;border:none;border-radius:10px;background:#007AFF;color:#fff;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer;}
.btn-next:hover{background:#006EE6;}
@media(max-width:768px){.quiz-layout{grid-template-columns:1fr;}.quiz-status{display:flex;}.quiz-card{padding:24px 18px;}.qc-text{font-size:20px;}.qc-actions{justify-content:stretch;}.btn-submit{width:100%;}}
</style>
