export interface LoginRequest { username: string; password: string }
export interface RegisterRequest { username: string; password: string; nickname: string }
export interface TokenResponse { access_token: string; refresh_token: string; token_type: string }
export interface UserResponse { id: number; username: string; nickname: string; role: string; is_active: boolean; force_password_change?: boolean }
export interface PasswordChangeRequest { old_password: string; new_password: string }
export interface ProfileUpdateRequest { nickname: string }

export interface QuestionOut {
  id: number; level_id: number; unit_id: number; type: string
  content: string; options: { letter: string; text: string }[] | null
  question_order: number; total_questions: number
  knowledge_meaning?: string; knowledge_rule?: string
  knowledge_error?: string; knowledge_example?: string
  answer?: string
}

export interface AnswerResult {
  success: boolean; is_correct: boolean; correct_answer: string
  knowledge: Record<string, string> | null; stars_earned: number
  new_combo: number; is_extreme_pass: boolean
}

export type WsMessage = {
  type: string
  [key: string]: unknown
}

// ── Units / Levels ──
export interface UnitOut {
  id: number; name: string; icon: string; subtitle: string
  description: string; learning_goal: string; coach_line: string
  starter_tip: string; color: string; sort_order: number
  levels?: LevelOut[] | number
}

export interface LevelOut {
  id: number; unit_id: number; name: string; icon: string; bg: string
  questions: number; sort_order: number
}

// ── Game Session (records) ──
export interface StartSessionIn { level_id: number; mode?: 'adventure' | 'extreme' | 'practice' }
export interface StartSessionOut { play_session_id: string; started_at: string; question_count: number }

export interface NextQuestionIn { play_session_id: string }
export interface NextQuestionOut {
  question_id: number; content: string; question_type: string
  options: { letter: string; text: string }[] | null
  question_order: number; total_questions: number
}

export interface AnswerSubmit {
  play_session_id: string; question_id: number
  submitted_answer: string; client_time_spent: number
}
export interface AnswerSubmitResponse {
  success: boolean; is_correct: boolean; correct_answer: string
  score_added: number; new_achievements?: AchievementUnlockSummary[]
}

export interface AchievementUnlockSummary {
  id: string; name: string; icon: string; description: string
  rarity: string; category: string
}

// ── PvP ──
export interface PvpMember {
  user_id: number; username: string; nickname: string; seat_order: number
  is_ready: boolean; is_online: boolean; battle_power: number
  correct_count: number; wrong_count: number; answered_count: number
  accuracy: number; best_streak: number; rank: number
  last_answer_at: string | null
}

export interface PvpRoomLog {
  id: number; room_id: number; message: string; category: string
  created_at: string | null
}

export interface PvpRoom {
  id: number; title: string; description: string; group_size: number
  status: string; mode: string; ranking_metric: string
  question_unit_ids: number[]; question_count: number
  battle_time_limit_seconds: number
  member_count: number; ready_count: number
  members: PvpMember[]; logs: PvpRoomLog[]
  created_at: string | null; server_now?: string | null; countdown_started_at: string | null; auto_start_at: string | null
  started_at: string | null; finished_at: string | null
  battle_started_at: string | null; battle_expires_at: string | null
}

export interface PvpReadyUpdateIn { is_ready: boolean }
export interface StudentPvpRoomOut { room: PvpRoom | null }

export interface PvpBattleQuestion {
  id: number; level_id: number; type: string
  content: string; options: { letter: string; text: string }[] | null
  question_order: number; total_questions: number
}

export interface PvpBattleSession {
  room: PvpRoom
  play_session_id: string; session_status: string
  question_count: number
  current_question: PvpBattleQuestion | null
  server_now?: string | null
}

export interface PvpBattleAnswerIn {
  play_session_id: string; question_id: number
  submitted_answer: string; client_time_spent: number
}

export interface PvpBattleAnswerOut {
  success: boolean; is_correct: boolean; correct_answer: string
  battle_power_delta: number; current_battle_power: number
  session_status: string; question_count: number
  knowledge: Record<string, string> | null
  next_question: PvpBattleQuestion | null
}

export interface PvpFinalizeIn { play_session_id: string }

// ── Leaderboard ──
export interface LeaderboardEntry {
  user_id: number; rank: number; nickname: string
  power_score: number; accuracy: number
  completed_levels: number; total_stars: number
  weekly_activity?: number
}

export interface LeaderboardResponse {
  entries: LeaderboardEntry[]
  my_rank: LeaderboardEntry | null
}

// ── Achievements ──
export interface Achievement {
  id: string; name: string; icon: string; description: string
  hint: string; rarity: string; category: string; unlocked: boolean
  unlocked_at?: string | null
}

// ── Admin ──
export interface AdminUser {
  id: number; username: string; nickname: string; role: string
  is_active: boolean; force_password_change?: boolean
}

export interface AdminStudent {
  user_id: number; username: string; nickname: string
  total_score: number; power_score: number; accuracy: number
  total_questions: number; completed_levels: number; total_stars: number
  practice_count: number; last_active: string | null; is_active: boolean
}

export interface AdminStudentLevelProgress {
  level_id: number
  stars: number
  unlocked: boolean
  best_combo: number
}

export interface AdminStudentLevelBreakdown {
  level_id: number
  unit_name: string
  level_name: string
  clear: number
  perfect: number
  speed: number
  combo: number
  total: number
}

export interface AdminStudentDetail {
  user_id: number
  username: string
  nickname: string
  is_active: boolean
  total_questions: number
  total_correct: number
  total_score: number
  power_score: number
  level_progress: AdminStudentLevelProgress[]
  level_breakdown: AdminStudentLevelBreakdown[]
}

export interface AdminStudentsResponse {
  items: AdminStudent[]; total: number; page: number; page_size: number
}

export interface AdminQuestion {
  id: number; title: string; content: string; type: string; answer: string
  options: { letter: string; text: string }[] | null
  level_id: number; level_name: string; unit_id: number; unit_name: string
  sort_order: number; is_active: boolean
  knowledge_meaning: string; knowledge_rule: string
  knowledge_error: string; knowledge_example: string
}

export interface AdminQuestionsResponse {
  items: AdminQuestion[]; total: number; page: number; page_size: number
}

export interface AdminPvpRoomCreate {
  title: string; description?: string; group_size: number
  member_user_ids: number[]; question_unit_ids: number[]
  question_count: number; battle_time_limit_seconds: number
}

export interface AdminDashboardStudent {
  user_id: number
  nickname: string
  power_score?: number
  accuracy?: number
  total_questions?: number
  last_active?: string | null
}

export interface AdminDashboardUnit {
  unit_name: string
  accuracy: number
  wrong_rate?: number
  avg_time_spent?: number
  answer_count?: number
}

export interface AdminDashboardOut {
  user_count: number
  active_student_count: number
  disabled_student_count: number
  question_count: number
  answer_count: number
  avg_accuracy: number
  avg_score: number
  total_power_score: number
  avg_power_score: number
  avg_weekly_activity: number
  completion_rate: number
  wrong_rate: number
  never_practiced_count: number
  hourly_trend: { date: string; count: number }[]
  unit_accuracy: AdminDashboardUnit[]
  weakest_units: AdminDashboardUnit[]
  top_students: AdminDashboardStudent[]
  inactive_students: AdminDashboardStudent[]
}

export interface AdminLevelAnalyticsItem {
  unit_name: string
  level_name: string
  total_attempts: number
  correct_rate: number
  avg_time_spent: number
  student_count: number
}

export interface AdminWrongQuestionItem {
  question_id: number
  question_content: string
  unit_name: string
  level_name: string
  wrong_count: number
  wrong_rate: number
  total_attempts: number
}

export interface PublicRegistrationSetting {
  allow_self_register: boolean
}

export interface RecordSummary {
  total_questions: number
  total_correct: number
  total_score: number
  power_score: number
  max_combo: number
  practice_count: number
  extreme_passes: number
  extreme_dual_passes: number
}

export interface ScoreStats {
  total_questions: number
  total_correct: number
  accuracy: number
  total_score: number
  power_score: number
  max_combo: number
  practice_count: number
  extreme_passes: number
  extreme_dual_passes: number
}

export interface ScoreProgressUnit {
  unit_id: number
  unit_name: string
  unit_icon: string
  levels: Array<{
    level_id: number
    name: string
    icon: string
    bg: string
    stars: number
    unlocked: boolean
  }>
}

export interface SyncStatsIn {
  practice_increment?: number
  extreme_pass_increment?: number
  extreme_dual_pass_increment?: number
}

export interface WrongQuestionRecord {
  id: number
  question_id: number
  question_content: string
  question_type: string
  user_answer: string
  correct_answer: string
  unit_id: number
  unit_name: string
  level_id: number
  level_name: string
  timestamp: string
  knowledge: {
    meaning: string
    rule: string
    error: string
    example: string
  } | null
}

// ── Admin Question CRUD ──
export interface QuestionCreatePayload {
  content: string
  type: string
  answer: string
  options: { letter: string; text: string }[] | null
  level_id: number
  title?: string
  sort_order?: number
  knowledge_meaning?: string
  knowledge_rule?: string
  knowledge_error?: string
  knowledge_example?: string
}

export interface QuestionUpdatePayload {
  content?: string
  type?: string
  answer?: string
  options?: { letter: string; text: string }[] | null
  level_id?: number
  title?: string
  is_active?: boolean
  sort_order?: number
  knowledge_meaning?: string
  knowledge_rule?: string
  knowledge_error?: string
  knowledge_example?: string
}
