import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { useAuthStore } from './auth'
import { useWebSocketStore } from './websocket'
import {
  finalizeSession,
  getMyBattle,
  getMyRoom,
  leaveRoom,
  submitPvpAnswer,
  updateReady,
} from '@/api/pvp'
import type { PvpBattleAnswerOut, PvpBattleQuestion, PvpMember, PvpRoom } from '@/types/api'

type RankTrend = 'up' | 'down' | ''

function compareMembers(a: PvpMember, b: PvpMember) {
  return (
    b.battle_power - a.battle_power ||
    b.correct_count - a.correct_count ||
    a.wrong_count - b.wrong_count ||
    a.seat_order - b.seat_order
  )
}

function rankMembersSnapshot(items: PvpMember[]) {
  return [...items]
    .map((item) => ({ ...item }))
    .sort(compareMembers)
    .map((item, index) => ({ ...item, rank: index + 1 }))
}

function parseServerTime(value: string) {
  const normalized = /(?:Z|[+-]\d{2}:\d{2})$/.test(value) ? value : `${value}Z`
  return new Date(normalized).getTime()
}

export const usePvpStore = defineStore('pvp', () => {
  const auth = useAuthStore()
  const wsStore = useWebSocketStore()

  const room = ref<PvpRoom | null>(null)
  const members = ref<PvpMember[]>([])
  const roomStatus = ref('')
  const countdownSeconds = ref(0)
  const countdownTimer = ref<ReturnType<typeof setTimeout> | null>(null)

  const playSessionId = ref('')
  const sessionStatus = ref('')
  const questionCount = ref(0)
  const currentQuestion = ref<PvpBattleQuestion | null>(null)
  const pendingNextQuestion = ref<PvpBattleQuestion | null>(null)
  const lastPvpResult = ref<PvpBattleAnswerOut | null>(null)
  const myBattlePower = ref(0)
  const myRank = ref(0)
  const questionStartTime = ref(0)
  const lastRoomStateTime = ref('')
  const battleTimeLeft = ref(0)
  const battleTotalSeconds = ref(0)
  const serverClockOffsetMs = ref(0)
  const rankTrendMap = ref<Record<number, RankTrend>>({})

  let battleTimerInterval: ReturnType<typeof setInterval> | null = null
  let wsHandlersBound = false
  let battleFinalizeRequested = false
  const rankTrendTimers = new Map<number, ReturnType<typeof setTimeout>>()

  const showFeedback = ref(false)
  const loading = ref(false)
  const error = ref('')

  const isInRoom = computed(() => room.value !== null)
  const isRunning = computed(() => roomStatus.value === 'running')
  const isCountdown = computed(() => roomStatus.value === 'countdown')
  const canLeaveRoom = computed(() => roomStatus.value === 'waiting')
  const isMyTurn = computed(() => sessionStatus.value === 'active' && currentQuestion.value !== null)
  const allMembers = computed(() => members.value)
  const battleProgressPercent = computed(() => {
    if (!battleTotalSeconds.value) return 0
    return Math.max(0, Math.min(100, (battleTimeLeft.value / battleTotalSeconds.value) * 100))
  })

  function updateMySnapshotFromMembers() {
    const me = members.value.find((member) => member.user_id === auth.user?.id)
    if (!me) {
      myBattlePower.value = 0
      myRank.value = 0
      return
    }
    myBattlePower.value = me.battle_power
    myRank.value = me.rank
  }

  function clearRankTrend(userId: number) {
    const next = { ...rankTrendMap.value }
    delete next[userId]
    rankTrendMap.value = next
    const timer = rankTrendTimers.get(userId)
    if (timer) {
      clearTimeout(timer)
      rankTrendTimers.delete(userId)
    }
  }

  function setRankTrend(userId: number, trend: RankTrend) {
    if (!trend) {
      clearRankTrend(userId)
      return
    }
    const timer = rankTrendTimers.get(userId)
    if (timer) {
      clearTimeout(timer)
    }
    rankTrendMap.value = { ...rankTrendMap.value, [userId]: trend }
    rankTrendTimers.set(
      userId,
      setTimeout(() => {
        clearRankTrend(userId)
      }, 900),
    )
  }

  function applyMemberSnapshot(nextMembers: PvpMember[]) {
    const previousRanks = new Map(members.value.map((member) => [member.user_id, member.rank]))
    const rankedMembers = rankMembersSnapshot(nextMembers)
    members.value = rankedMembers
    for (const member of rankedMembers) {
      const previousRank = previousRanks.get(member.user_id)
      if (!previousRank || previousRank === member.rank) {
        clearRankTrend(member.user_id)
        continue
      }
      setRankTrend(member.user_id, member.rank < previousRank ? 'up' : 'down')
    }
    for (const userId of previousRanks.keys()) {
      if (!rankedMembers.some((member) => member.user_id === userId)) {
        clearRankTrend(userId)
      }
    }
    updateMySnapshotFromMembers()
  }

  function getBattleTiming(roomData: PvpRoom) {
    const explicitStart = roomData.battle_started_at ?? roomData.started_at
    const explicitEnd = roomData.battle_expires_at
    if (!explicitStart || !explicitEnd) {
      const total = roomData.battle_time_limit_seconds || 0
      if (!explicitStart || !total) return { startAt: 0, endAt: 0, total }
      const startAt = parseServerTime(explicitStart)
      return { startAt, endAt: startAt + total * 1000, total }
    }
    const startAt = parseServerTime(explicitStart)
    const endAt = parseServerTime(explicitEnd)
    const total = Math.max(0, Math.round((endAt - startAt) / 1000))
    return { startAt, endAt, total }
  }

  function syncServerClock(serverNow?: string | null) {
    if (!serverNow) return
    serverClockOffsetMs.value = parseServerTime(serverNow) - Date.now()
  }

  function currentServerMs() {
    return Date.now() + serverClockOffsetMs.value
  }

  function stopCountdown() {
    if (countdownTimer.value) {
      clearTimeout(countdownTimer.value)
      countdownTimer.value = null
    }
    countdownSeconds.value = 0
  }

  function startCountdown(autoStartAt: string) {
    stopCountdown()
    const target = parseServerTime(autoStartAt)
    const tick = () => {
      const remaining = Math.max(0, Math.ceil((target - currentServerMs()) / 1000))
      countdownSeconds.value = remaining
      if (remaining <= 0) {
        stopCountdown()
        return
      }
      countdownTimer.value = setTimeout(tick, 200)
    }
    tick()
  }

  function stopBattleTimer() {
    if (battleTimerInterval) {
      clearInterval(battleTimerInterval)
      battleTimerInterval = null
    }
    battleTimeLeft.value = 0
    battleTotalSeconds.value = 0
    battleFinalizeRequested = false
  }

  async function triggerBattleTimeoutFinalize() {
    if (battleFinalizeRequested || roomStatus.value !== 'running') return
    battleFinalizeRequested = true
    await doFinalize({ silent: true })
  }

  function startBattleTimer(roomData: PvpRoom) {
    stopBattleTimer()
    const { endAt, total } = getBattleTiming(roomData)
    if (!endAt || !total) return

    battleTotalSeconds.value = total
    const tick = () => {
      const left = Math.max(0, Math.ceil((endAt - currentServerMs()) / 1000))
      battleTimeLeft.value = left
      if (left <= 0) {
        stopBattleTimer()
        void triggerBattleTimeoutFinalize()
      }
    }
    tick()
    battleTimerInterval = setInterval(tick, 1000)
  }

  function syncRoomState(roomData: PvpRoom | null) {
    room.value = roomData
    if (!roomData) {
      members.value = []
      roomStatus.value = ''
      stopCountdown()
      stopBattleTimer()
      return
    }

    syncServerClock(roomData.server_now)
    roomStatus.value = roomData.status
    applyMemberSnapshot(roomData.members || [])

    if (roomStatus.value === 'countdown' && roomData.auto_start_at) {
      startCountdown(roomData.auto_start_at)
    } else {
      stopCountdown()
    }

    if (roomStatus.value === 'running') {
      startBattleTimer(roomData)
    } else {
      stopBattleTimer()
    }
  }

  function syncBattleState(result: {
    room: PvpRoom
    play_session_id: string
    session_status: string
    question_count: number
    current_question: PvpBattleQuestion | null
    server_now?: string | null
  }) {
    syncServerClock(result.server_now ?? result.room.server_now)
    const previousQuestionId = currentQuestion.value?.id ?? null
    playSessionId.value = result.play_session_id
    sessionStatus.value = result.session_status
    questionCount.value = result.question_count
    currentQuestion.value = result.current_question
    const nextQuestionId = result.current_question?.id ?? null
    if (nextQuestionId !== previousQuestionId) {
      questionStartTime.value = Date.now()
    }
    syncRoomState(result.room)
  }

  function setupWsHandlers() {
    if (wsHandlersBound) return
    wsHandlersBound = true

    wsStore.on('pvp_room_state', (msg) => {
      const roomData = (msg.room as PvpRoom | null | undefined) ?? null
      if (!roomData) {
        syncRoomState(null)
        return
      }

      const msgTime = roomData.finished_at || roomData.battle_started_at || roomData.started_at || roomData.auto_start_at || ''
      if (msgTime && lastRoomStateTime.value && msgTime < lastRoomStateTime.value) return
      if (msgTime) lastRoomStateTime.value = msgTime

      syncRoomState(roomData)
    })
    wsStore.on('pvp_battle_session', (msg) => {
      const roomData = msg.room as PvpRoom | undefined
      if (!roomData || typeof msg.play_session_id !== 'string' || typeof msg.session_status !== 'string' || typeof msg.question_count !== 'number') {
        return
      }
      syncBattleState({
        room: roomData,
        play_session_id: msg.play_session_id,
        session_status: msg.session_status,
        question_count: msg.question_count,
        current_question: (msg.current_question as PvpBattleQuestion | null | undefined) ?? null,
        server_now: (msg.server_now as string | null | undefined) ?? roomData.server_now,
      })
    })
    wsStore.on('pvp_rooms', (_msg) => {
      // Lobby list is fetched elsewhere; battle page only needs direct room snapshots.
    })
    wsStore.on('pvp_error', (msg) => {
      error.value = (msg.message as string) || '对战状态同步失败'
    })
  }

  async function fetchMyRoom(options: { silent?: boolean } = {}) {
    if (!options.silent) {
      loading.value = true
      error.value = ''
    }
    try {
      const result = await getMyRoom(auth.token!)
      syncRoomState(result.room)
      return result.room
    } catch (e) {
      const message = e instanceof Error ? e.message : '获取房间失败'
      if (!options.silent) {
        error.value = message
      }
      throw e
    } finally {
      if (!options.silent) {
        loading.value = false
      }
    }
  }

  async function toggleReady() {
    if (!room.value) return
    const myMember = members.value.find((member) => member.user_id === auth.user?.id)
    const newReady = !myMember?.is_ready
    loading.value = true
    error.value = ''
    try {
      const result = await updateReady({ is_ready: newReady }, auth.token!)
      syncRoomState(result.room)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '操作失败'
    } finally {
      loading.value = false
    }
  }

  async function doLeaveRoom() {
    if (!canLeaveRoom.value) {
      error.value = '对战已进入倒计时或进行中，不能退出房间'
      return
    }
    loading.value = true
    error.value = ''
    try {
      await leaveRoom(auth.token!)
      syncRoomState(null)
    } catch (e) {
      error.value = e instanceof Error ? e.message : '退出房间失败'
    } finally {
      loading.value = false
    }
  }

  async function fetchBattle(options: { silent?: boolean } = {}) {
    if (!options.silent) {
      loading.value = true
      error.value = ''
    }
    try {
      const result = await getMyBattle(auth.token!)
      syncBattleState(result)
      return result
    } catch (e) {
      const message = e instanceof Error ? e.message : '获取对战失败'
      if (!options.silent) {
        error.value = message
      }
      throw e
    } finally {
      if (!options.silent) {
        loading.value = false
      }
    }
  }

  async function syncBattleProgress() {
    try {
      await fetchBattle({ silent: true })
      return
    } catch {
      try {
        await fetchMyRoom({ silent: true })
      } catch {
        // ignore transient sync failures during battle
      }
    }
  }

  function requestBattleSnapshot() {
    wsStore.send({ type: 'request_pvp_battle' })
  }

  async function answerQuestion(submittedAnswer: string) {
    if (!currentQuestion.value || !playSessionId.value) return
    const clientTimeSpent = (Date.now() - questionStartTime.value) / 1000
    try {
      const result = await submitPvpAnswer({
        play_session_id: playSessionId.value,
        question_id: currentQuestion.value.id,
        submitted_answer: submittedAnswer,
        client_time_spent: clientTimeSpent,
      }, auth.token!)
      lastPvpResult.value = result
      sessionStatus.value = result.session_status
      showFeedback.value = true

      const myId = auth.user?.id
      const localNow = new Date().toISOString()
      const updatedMembers = members.value.map((member) => {
        if (member.user_id !== myId) return member
        const answeredCount = member.answered_count + 1
        const correctCount = member.correct_count + (result.is_correct ? 1 : 0)
        const wrongCount = member.wrong_count + (result.is_correct ? 0 : 1)
        return {
          ...member,
          battle_power: result.current_battle_power,
          correct_count: correctCount,
          wrong_count: wrongCount,
          answered_count: answeredCount,
          accuracy: answeredCount > 0 ? Number(((correctCount * 100) / answeredCount).toFixed(1)) : 0,
          last_answer_at: localNow,
        }
      })
      applyMemberSnapshot(updatedMembers)

      if (result.next_question) {
        pendingNextQuestion.value = result.next_question
      } else if (result.session_status === 'completed') {
        pendingNextQuestion.value = null
      }
    } catch (e) {
      error.value = e instanceof Error ? e.message : '提交答案失败'
    }
  }

  function nextAfterFeedback() {
    showFeedback.value = false
    lastPvpResult.value = null
    if (pendingNextQuestion.value) {
      currentQuestion.value = pendingNextQuestion.value
      pendingNextQuestion.value = null
      questionStartTime.value = Date.now()
    }
  }

  async function doFinalize(options: { silent?: boolean } = {}) {
    if (!playSessionId.value) return false
    if (!options.silent) {
      loading.value = true
      error.value = ''
    }
    try {
      const result = await finalizeSession({ play_session_id: playSessionId.value }, auth.token!)
      syncRoomState(result)
      sessionStatus.value = result.status === 'finished' ? 'completed' : sessionStatus.value
      return true
    } catch (e) {
      const message = e instanceof Error ? e.message : '结束对战失败'
      if (!(message.includes('已结束') && roomStatus.value === 'finished')) {
        error.value = message
      }
      return roomStatus.value === 'finished'
    } finally {
      if (!options.silent) {
        loading.value = false
      }
    }
  }

  function rankTrendFor(userId: number) {
    return rankTrendMap.value[userId] ?? ''
  }

  function reset() {
    syncRoomState(null)
    playSessionId.value = ''
    sessionStatus.value = ''
    questionCount.value = 0
    currentQuestion.value = null
    pendingNextQuestion.value = null
    lastPvpResult.value = null
    myBattlePower.value = 0
    myRank.value = 0
    showFeedback.value = false
    lastRoomStateTime.value = ''
    error.value = ''
    for (const userId of [...rankTrendTimers.keys()]) {
      clearRankTrend(userId)
    }
  }

  return {
    room,
    members,
    roomStatus,
    countdownSeconds,
    battleTimeLeft,
    battleTotalSeconds,
    battleProgressPercent,
    playSessionId,
    sessionStatus,
    questionCount,
    currentQuestion,
    lastPvpResult,
    myBattlePower,
    myRank,
    showFeedback,
    loading,
    error,
    isInRoom,
    isRunning,
    isCountdown,
    canLeaveRoom,
    isMyTurn,
    allMembers,
    rankTrendFor,
    setupWsHandlers,
    fetchMyRoom,
    toggleReady,
    doLeaveRoom,
    fetchBattle,
    syncBattleProgress,
    requestBattleSnapshot,
    answerQuestion,
    nextAfterFeedback,
    doFinalize,
    reset,
  }
})
