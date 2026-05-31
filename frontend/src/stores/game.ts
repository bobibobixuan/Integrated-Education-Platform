import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from './auth'

function normalizeFillAnswer(answer: string) {
  return answer.trim().toLowerCase()
}

function splitFillAnswerVariants(answer: string) {
  return answer
    .split(/[;；]+/)
    .map(item => normalizeFillAnswer(item))
    .filter(Boolean)
}

function normalizeJudgeAnswer(answer: string) {
  const token = answer.trim().toLowerCase()
  if (['a', 'true', '对', '正确', '是', '√', '1', 't', 'yes', 'y'].includes(token)) return 'a'
  if (['b', 'false', '错', '错误', '否', '×', '0', 'f', 'no', 'n'].includes(token)) return 'b'
  return token
}
import { fetchUnits, fetchUnitQuestions, startSession, nextQuestion, submitAnswer } from '@/api/game'
import { syncStats } from '@/api/records'
import type { UnitOut, LevelOut, NextQuestionOut, AnswerSubmitResponse, QuestionOut } from '@/types/api'

export type GamePhase =
  | 'menu'
  | 'playing'
  | 'results'
  // practice
  | 'practice-unit-select'
  | 'practice'
  | 'practice-results'
  // extreme
  | 'extreme-select'
  | 'extreme-playing'
  | 'extreme-failed'
  | 'extreme-passed'

interface ExtremeSegment {
  unitIndex: number
  levelIndex: number
  unitId: number
  levelId: number
  levelName: string
}

export const useGameStore = defineStore('game', () => {
  const auth = useAuthStore()

  // Unit/Level list
  const units = ref<UnitOut[]>([])
  const selectedUnitId = ref<number | null>(null)
  const selectedLevelId = ref<number | null>(null)

  // Session state
  const phase = ref<GamePhase>('menu')
  const playSessionId = ref<string>('')
  const currentQuestion = ref<NextQuestionOut | null>(null)
  const questionStartTime = ref<number>(0)
  const sessionQuestionCount = ref(0)
  const answeredCount = ref(0)

  // Adventure results
  const lastResult = ref<AnswerSubmitResponse | null>(null)
  const combo = ref(0)
  const bestCombo = ref(0)
  const totalScore = ref(0)
  const sessionCorrect = ref(0)
  const sessionResults = ref<{ isCorrect: boolean; questionId: number; order: number }[]>([])

  // ── Practice mode ──
  const practiceQuestions = ref<QuestionOut[]>([])
  const practiceIndex = ref(0)
  const practiceAnswer = ref<string | null>(null)
  const practiceFeedback = ref<{ isCorrect: boolean; correctAnswer: string } | null>(null)
  const practiceCorrectCount = ref(0)
  const practiceTotalCount = ref(0)
  const practiceEnded = ref(false)

  // ── Extreme mode ──
  const extremeScope = ref<string>('')          // `unit:${id}` | 'dual'
  const extremeSegments = ref<ExtremeSegment[]>([])
  const extremeSegmentIndex = ref(0)
  const extremeRunCorrect = ref(0)
  const extremeRunAttempted = ref(0)
  const extremeFailedAtQuestion = ref<string>('')

  // Loading
  const loading = ref(false)
  const error = ref('')

  // ── Computed ──

  const levels = computed(() => {
    if (!selectedUnitId.value) return []
    const unit = units.value.find(u => u.id === selectedUnitId.value)
    if (!unit || !Array.isArray(unit.levels)) return []
    return unit.levels as LevelOut[]
  })

  const currentSegment = computed(() => {
    if (extremeSegmentIndex.value < extremeSegments.value.length) {
      return extremeSegments.value[extremeSegmentIndex.value]
    }
    return null
  })

  const extremeProgress = computed(() => {
    const total = extremeSegments.value.length
    if (total === 0) return { current: 0, total: 0, label: '' }
    const cur = Math.min(extremeSegmentIndex.value + 1, total)
    return {
      current: cur,
      total,
      label: `第 ${cur} / ${total} 段`,
    }
  })

  const practiceQuestionCount = computed(() => practiceQuestions.value.length)
  const practiceAccuracy = computed(() => {
    if (!practiceTotalCount.value) return 0
    return Math.round((practiceCorrectCount.value / practiceTotalCount.value) * 100)
  })

  // ── Unit loading ──

  async function loadUnits() {
    if (units.value.length > 0) return
    loading.value = true
    error.value = ''
    try {
      units.value = await fetchUnits(auth.token!)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加載單元失敗'
    } finally {
      loading.value = false
    }
  }

  function selectLevel(unitId: number, levelId: number) {
    selectedUnitId.value = unitId
    selectedLevelId.value = levelId
  }

  // ── Adventure: begin a level session ──

  async function beginLevel() {
    if (!selectedLevelId.value) return
    loading.value = true
    error.value = ''
    try {
      const session = await startSession({ level_id: selectedLevelId.value }, auth.token!)
      playSessionId.value = session.play_session_id
      sessionQuestionCount.value = session.question_count
      answeredCount.value = 0
      combo.value = 0
      bestCombo.value = 0
      totalScore.value = 0
      sessionCorrect.value = 0
      sessionResults.value = []
      lastResult.value = null
      phase.value = 'playing'
      await loadNextQuestion()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '開始關卡失敗'
    } finally {
      loading.value = false
    }
  }

  async function loadNextQuestion() {
    if (!playSessionId.value) return
    try {
      currentQuestion.value = await nextQuestion({ play_session_id: playSessionId.value }, auth.token!)
      questionStartTime.value = Date.now()
      lastResult.value = null
    } catch (e) {
      const msg = e instanceof Error ? e.message : ''
      if (msg.includes('所有题目已答完') || msg.includes('已结束')) {
        phase.value = 'results'
      } else {
        error.value = msg || '加載題目失敗'
      }
    }
  }

  async function answerQuestion(submittedAnswer: string) {
    if (!currentQuestion.value || !playSessionId.value) return
    const clientTimeSpent = (Date.now() - questionStartTime.value) / 1000
    try {
      const result = await submitAnswer({
        play_session_id: playSessionId.value,
        question_id: currentQuestion.value.question_id,
        submitted_answer: submittedAnswer,
        client_time_spent: clientTimeSpent,
      }, auth.token!)
      lastResult.value = result
      answeredCount.value++
      sessionResults.value.push({
        isCorrect: result.is_correct,
        questionId: currentQuestion.value.question_id,
        order: answeredCount.value,
      })
      if (result.is_correct) {
        combo.value++
        bestCombo.value = Math.max(bestCombo.value, combo.value)
        totalScore.value += result.score_added
        sessionCorrect.value++
      } else {
        combo.value = 0
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : ''
      if (msg.includes('Session 已结束') || msg.includes('所有题目已答完') || msg.includes('已答过')) {
        phase.value = 'results'
      } else {
        error.value = msg || '提交答案失敗'
      }
    }
  }

  function returnToMenu() {
    phase.value = 'menu'
    playSessionId.value = ''
    currentQuestion.value = null
    lastResult.value = null
  }

  // ── Practice mode ──

  function selectPracticeUnit(unitId: number) {
    selectedUnitId.value = unitId
  }

  async function beginPractice() {
    if (selectedUnitId.value === null) return
    loading.value = true
    error.value = ''
    practiceFeedback.value = null
    practiceAnswer.value = null
    practiceCorrectCount.value = 0
    practiceTotalCount.value = 0
    practiceEnded.value = false
    try {
      const questions = await fetchUnitQuestions(selectedUnitId.value, auth.token!)
      if (!questions.length) {
        error.value = '该单元暂无题目'
        return
      }
      practiceQuestions.value = shuffleArray(questions)
      practiceIndex.value = 0
      phase.value = 'practice'
    } catch (e) {
      error.value = e instanceof Error ? e.message : '加载题目失败'
    } finally {
      loading.value = false
    }
  }

  function submitPracticeAnswer(answer: string) {
    if (!practiceQuestions.value.length) return
    const q = practiceQuestions.value[practiceIndex.value]
    if (!q) return
    const correctAnswer = (q.answer || '').trim()
    const normalizedAnswer = answer.trim().toUpperCase()
    const normalizedCorrectAnswer = correctAnswer.trim().toUpperCase()
    const isMultiChoice = q.type === '多选题'
    const isFill = q.type === '填空题'
    const isJudge = q.type === '判断题'
    const isCorrect = isMultiChoice
      ? [...normalizedAnswer].sort().join('') === [...normalizedCorrectAnswer].sort().join('')
      : isJudge
        ? normalizeJudgeAnswer(answer) === normalizeJudgeAnswer(correctAnswer)
      : isFill
        ? splitFillAnswerVariants(correctAnswer).includes(normalizeFillAnswer(answer))
        : answer.trim().toLowerCase() === correctAnswer.toLowerCase()
    practiceFeedback.value = { isCorrect, correctAnswer: q.answer || '' }
    practiceAnswer.value = answer

    practiceTotalCount.value++
    if (isCorrect) practiceCorrectCount.value++
  }

  function nextPracticeQuestion() {
    practiceFeedback.value = null
    practiceAnswer.value = null
    practiceIndex.value++
    if (practiceIndex.value >= practiceQuestions.value.length) {
      // Refill: reshuffle and start over (infinite loop)
      practiceQuestions.value = shuffleArray([...practiceQuestions.value])
      practiceIndex.value = 0
    }
  }

  async function finishPractice() {
    // Sync practice count to backend
    try {
      await syncStats({ practice_increment: 1 }, auth.token!)
    } catch {
      // Non-critical, ignore
    }
    practiceEnded.value = true
    practiceFeedback.value = null
    practiceAnswer.value = null
    phase.value = 'practice-results'
  }

  function returnFromPractice() {
    phase.value = 'menu'
    practiceQuestions.value = []
    practiceIndex.value = 0
    practiceFeedback.value = null
    practiceAnswer.value = null
    practiceEnded.value = false
  }

  // ── Extreme mode ──

  async function selectExtreme(scope: string) {
    extremeScope.value = scope
    // Build segment list
    const segs: ExtremeSegment[] = []
    const allUnits = units.value

    if (scope.startsWith('unit:')) {
      const selectedId = Number(scope.slice(5))
      const unitIdx = allUnits.findIndex(unit => unit.id === selectedId)
      const unit = unitIdx >= 0 ? allUnits[unitIdx] : null
      if (unit && Array.isArray(unit.levels)) {
        ;(unit.levels as LevelOut[]).forEach((level, idx) => {
          segs.push({
            unitIndex: unitIdx, levelIndex: idx,
            unitId: unit.id, levelId: level.id,
            levelName: level.name,
          })
        })
      }
    } else if (scope === 'dual') {
      // Keep the original dual-unit rule: first two units challenge in sequence.
      for (const unitIdx of [0, 1]) {
        const unit = allUnits[unitIdx]
        if (unit && Array.isArray(unit.levels)) {
          ;(unit.levels as LevelOut[]).forEach((level, idx) => {
            segs.push({
              unitIndex: unitIdx, levelIndex: idx,
              unitId: unit.id, levelId: level.id,
              levelName: level.name,
            })
          })
        }
      }
    }

    extremeSegments.value = segs
    extremeSegmentIndex.value = 0
    extremeRunCorrect.value = 0
    extremeRunAttempted.value = 0
    extremeFailedAtQuestion.value = ''

    if (segs.length === 0) {
      error.value = '没有可挑战的关卡'
      phase.value = 'menu'
      return
    }

    // Start first segment
    await startExtremeSegment()
  }

  async function startExtremeSegment() {
    const seg = currentSegment.value
    if (!seg) {
      // All segments done → passed
      await completeExtremePass()
      return
    }

    loading.value = true
    error.value = ''
    try {
      const session = await startSession({ level_id: seg.levelId, mode: 'extreme' }, auth.token!)
      playSessionId.value = session.play_session_id
      sessionQuestionCount.value = session.question_count
      answeredCount.value = 0
      combo.value = 0
      bestCombo.value = 0
      totalScore.value = 0
      sessionCorrect.value = 0
      sessionResults.value = []
      lastResult.value = null
      phase.value = 'extreme-playing'
      await loadNextQuestion()
    } catch (e) {
      error.value = e instanceof Error ? e.message : '開始關卡失敗'
      phase.value = 'menu'
    } finally {
      loading.value = false
    }
  }

  async function answerExtremeQuestion(submittedAnswer: string) {
    if (!currentQuestion.value || !playSessionId.value) return
    const clientTimeSpent = (Date.now() - questionStartTime.value) / 1000
    try {
      const result = await submitAnswer({
        play_session_id: playSessionId.value,
        question_id: currentQuestion.value.question_id,
        submitted_answer: submittedAnswer,
        client_time_spent: clientTimeSpent,
      }, auth.token!)
      lastResult.value = result
      answeredCount.value++
      extremeRunAttempted.value++

      sessionResults.value.push({
        isCorrect: result.is_correct,
        questionId: currentQuestion.value.question_id,
        order: answeredCount.value,
      })

      if (result.is_correct) {
        combo.value++
        bestCombo.value = Math.max(bestCombo.value, combo.value)
        totalScore.value += result.score_added
        sessionCorrect.value++
        extremeRunCorrect.value++
      } else {
        // Wrong answer in extreme mode → game over
        combo.value = 0
        extremeFailedAtQuestion.value = currentQuestion.value.content
        phase.value = 'extreme-failed'
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : ''
      if (msg.includes('Session 已结束') || msg.includes('所有题目已答完') || msg.includes('已答过')) {
        // Session complete = segment passed
        onExtremeSegmentComplete()
      } else {
        error.value = msg || '提交答案失敗'
      }
    }
  }

  async function onExtremeSegmentComplete() {
    // Move to next segment
    extremeSegmentIndex.value++
    await startExtremeSegment()
  }

  async function completeExtremePass() {
    const isDual = extremeScope.value === 'dual'
    try {
      await syncStats({
        extreme_pass_increment: 1,
        extreme_dual_pass_increment: isDual ? 1 : 0,
      }, auth.token!)
    } catch {
      // Non-critical
    }
    phase.value = 'extreme-passed'
  }

  async function retryExtreme() {
    // Reset and restart
    await selectExtreme(extremeScope.value)
  }

  function returnFromExtreme() {
    phase.value = 'menu'
    playSessionId.value = ''
    currentQuestion.value = null
    lastResult.value = null
    extremeSegments.value = []
    extremeSegmentIndex.value = 0
  }

  // ── Utils ──

  function shuffleArray<T>(arr: T[]): T[] {
    const a = [...arr]
    for (let i = a.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1))
      ;[a[i], a[j]] = [a[j], a[i]]
    }
    return a
  }

  return {
    units, selectedUnitId, selectedLevelId,
    phase, playSessionId, currentQuestion, questionStartTime,
    sessionQuestionCount, answeredCount,
    lastResult, combo, bestCombo, totalScore, sessionCorrect, sessionResults,
    loading, error,
    levels,
    // Practice
    practiceQuestions, practiceIndex, practiceAnswer, practiceFeedback,
    practiceCorrectCount, practiceTotalCount, practiceEnded,
    practiceQuestionCount, practiceAccuracy,
    selectPracticeUnit, beginPractice, submitPracticeAnswer,
    nextPracticeQuestion, finishPractice, returnFromPractice,
    // Extreme
    extremeScope, extremeSegments, extremeSegmentIndex,
    extremeRunCorrect, extremeRunAttempted, extremeFailedAtQuestion,
    currentSegment, extremeProgress,
    selectExtreme, startExtremeSegment, answerExtremeQuestion,
    onExtremeSegmentComplete, retryExtreme, returnFromExtreme,
    // Core
    loadUnits, selectLevel, beginLevel, loadNextQuestion, answerQuestion, returnToMenu,
  }
})
