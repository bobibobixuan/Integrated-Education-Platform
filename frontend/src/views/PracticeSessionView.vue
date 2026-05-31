<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import AppShell from '@/components/AppShell.vue'
import { useGameStore } from '@/stores/game'
import type { QuestionOut } from '@/types/api'

const router = useRouter()
const game = useGameStore()
const answer = ref('')
const multiAnswers = ref<string[]>([])
const judgeOptions = [
  { letter: 'A', text: '正确' },
  { letter: 'B', text: '错误' },
]

const practiceQuestion = computed<QuestionOut | null>(() => game.practiceQuestions[game.practiceIndex] || null)
const currentLabel = computed(() => {
  if (!practiceQuestion.value) return ''
  return `${game.practiceIndex + 1} / ${game.practiceQuestions.length}`
})

const questionMode = computed(() => {
  const question = practiceQuestion.value
  if (question?.type === '判断题') return 'judge'
  if (!question?.options?.length) return 'fill'
  if (question.type === '多选题') return 'multi'
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

function submit() {
  const finalAnswer = answer.value.trim()
  if (!finalAnswer && !practiceQuestion.value?.options?.length) return
  game.submitPracticeAnswer(finalAnswer)
}

function nextQuestion() {
  answer.value = ''
  multiAnswers.value = []
  game.nextPracticeQuestion()
}

async function finish() {
  await game.finishPractice()
  router.push('/practice/result')
}

watch(() => game.phase, (phase) => {
  if (phase === 'practice-results') {
    router.replace('/practice/result')
    return
  }
  if (phase !== 'practice') {
    router.replace('/practice')
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
            <span class="qc-num">{{ currentLabel }}</span>
          </div>
          <p class="qc-text">{{ practiceQuestion?.content }}</p>
          <div v-if="questionMode === 'choice'" class="qc-options">
            <button v-for="opt in practiceQuestion!.options" :key="opt.letter" type="button" class="qc-opt" :class="{ 'qc-opt--sel': answer === opt.letter }" :disabled="!!game.practiceFeedback" @click="selectOption(opt.letter)">
              <span class="qc-opt-letter">{{ opt.letter }}</span><span>{{ opt.text }}</span>
            </button>
          </div>
          <div v-else-if="questionMode === 'multi'" class="qc-options">
            <button v-for="opt in practiceQuestion!.options" :key="opt.letter" type="button" class="qc-opt" :class="{ 'qc-opt--sel': multiAnswers.includes(opt.letter) }" :disabled="!!game.practiceFeedback" @click="selectOption(opt.letter)">
              <span class="qc-opt-letter">{{ multiAnswers.includes(opt.letter) ? '✓' : opt.letter }}</span><span>{{ opt.text }}</span>
            </button>
          </div>
          <div v-else-if="questionMode === 'judge'" class="qc-options">
            <button v-for="opt in judgeOptions" :key="opt.letter" type="button" class="qc-opt" :class="{ 'qc-opt--sel': answer === opt.letter }" :disabled="!!game.practiceFeedback" @click="selectOption(opt.letter)">
              <span class="qc-opt-letter">{{ opt.letter }}</span><span>{{ opt.text }}</span>
            </button>
          </div>
          <div v-else class="qc-fill">
            <input v-model="answer" type="text" :disabled="!!game.practiceFeedback" placeholder="输入答案" class="qc-input" @keyup.enter="submit" />
          </div>
          <div class="qc-actions">
            <button type="button" class="btn-submit" :disabled="!!game.practiceFeedback || !answer.trim()" @click="submit">
              {{ questionMode === 'multi' && !game.practiceFeedback ? `查看答案 (${multiAnswers.length} 项)` : '查看答案' }}
            </button>
          </div>
          <div v-if="game.practiceFeedback" class="qc-feedback" :class="{ 'qc-feedback--wrong': !game.practiceFeedback.isCorrect }">
            <strong>{{ game.practiceFeedback.isCorrect ? '✓ 回答正确' : '✕ 回答错误' }}</strong>
            <span v-if="!game.practiceFeedback.isCorrect">正确答案：{{ formatDisplayedAnswer(game.practiceFeedback.correctAnswer) }}</span>
            <div class="qc-knowledge">
              <p><strong>解析：</strong>{{ practiceQuestion?.knowledge_meaning || '暂无解析。' }}</p>
              <p v-if="practiceQuestion?.knowledge_rule"><strong>规则：</strong>{{ practiceQuestion.knowledge_rule }}</p>
              <p v-if="practiceQuestion?.knowledge_error"><strong>易错点：</strong>{{ practiceQuestion.knowledge_error }}</p>
              <p v-if="practiceQuestion?.knowledge_example"><strong>例子：</strong>{{ practiceQuestion.knowledge_example }}</p>
            </div>
            <div class="qc-fb-actions">
              <button type="button" class="btn-next" @click="nextQuestion">下一题</button>
              <button type="button" class="btn-back" @click="finish">结束练习</button>
            </div>
          </div>
        </section>
        <aside class="quiz-side">
          <div class="quiz-status">
            <div class="qs-group"><span class="qs-label">模式</span><strong>随机练习</strong></div>
            <div class="qs-group"><span class="qs-label">进度</span><strong>{{ currentLabel }}</strong></div>
            <div class="qs-group"><span class="qs-label">正确</span><strong>{{ game.practiceCorrectCount }}</strong></div>
            <div class="qs-group"><span class="qs-label">已答</span><strong>{{ game.practiceTotalCount }}</strong></div>
          </div>
        </aside>
      </div>
    </div>
  </AppShell>
</template>

<style scoped>
.quiz-page { max-width:1100px; margin:0 auto; width:100%; font-family:-apple-system,BlinkMacSystemFont,"SF Pro Display","SF Pro Text","PingFang SC","Microsoft YaHei",sans-serif; }
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
.qc-feedback{display:flex;flex-direction:column;gap:12px;padding:16px 20px;border-radius:14px;background:rgba(52,199,89,0.08);border:1px solid rgba(52,199,89,0.2);}
.qc-feedback--wrong{background:rgba(255,59,48,0.06);border-color:rgba(255,59,48,0.2);}
.qc-feedback strong{font-size:15px;font-weight:700;color:#34C759;}
.qc-feedback--wrong strong{color:#FF3B30;}
.qc-feedback span{font-size:13px;color:rgba(60,60,67,0.6);}
.qc-knowledge{margin-top:4px;padding:14px;border-radius:10px;background:rgba(0,0,0,0.02);border:1px solid rgba(60,60,67,0.08);display:grid;gap:6px;}
.qc-knowledge p{margin:0;font-size:13px;color:rgba(60,60,67,0.6);line-height:1.6;}
.qc-knowledge strong{color:#000;font-size:13px;}
.qc-fb-actions{display:flex;gap:10px;}
.btn-next{height:40px;padding:0 20px;border:none;border-radius:10px;background:#007AFF;color:#fff;font-size:14px;font-weight:600;font-family:inherit;cursor:pointer;}
.btn-next:hover{background:#006EE6;}
.btn-back{height:40px;padding:0 20px;border:1px solid rgba(60,60,67,0.18);border-radius:10px;background:#fff;color:rgba(60,60,67,0.6);font-size:14px;font-weight:500;font-family:inherit;cursor:pointer;}
.btn-back:hover{background:rgba(0,0,0,0.03);}
@media(max-width:768px){.quiz-layout{grid-template-columns:1fr;}.quiz-status{display:flex;}.quiz-card{padding:24px 18px;}.qc-text{font-size:20px;}.qc-actions{justify-content:stretch;}.btn-submit{width:100%;}}
</style>
