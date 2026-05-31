import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory('/app/'),
  routes: [
    { path: '/', name: 'home', component: () => import('@/views/HomeView.vue'), meta: { title: '学生导航', requiresAuth: true } },
    { path: '/login', name: 'login', component: () => import('@/views/LoginView.vue'), meta: { title: '登录 / 注册', backTo: '/' } },
    { path: '/account', name: 'account', component: () => import('@/views/AccountView.vue'), meta: { title: '个人中心', requiresAuth: true, backTo: '/' } },
    { path: '/adventure', name: 'adventure-map', component: () => import('@/views/AdventureMapView.vue'), meta: { title: '冒险地图', requiresAuth: true, backTo: '/' } },
    { path: '/adventure/play', name: 'adventure-play', component: () => import('@/views/AdventurePlayView.vue'), meta: { title: '冒险作答', requiresAuth: true, backTo: '/adventure' } },
    { path: '/adventure/result', name: 'adventure-result', component: () => import('@/views/AdventureResultView.vue'), meta: { title: '冒险结算', requiresAuth: true, backTo: '/adventure' } },
    { path: '/practice', name: 'practice-hub', component: () => import('@/views/PracticeHubView.vue'), meta: { title: '随机练习', requiresAuth: true, backTo: '/' } },
    { path: '/practice/session', name: 'practice-session', component: () => import('@/views/PracticeSessionView.vue'), meta: { title: '练习作答', requiresAuth: true, backTo: '/practice' } },
    { path: '/practice/result', name: 'practice-result', component: () => import('@/views/PracticeResultView.vue'), meta: { title: '练习总结', requiresAuth: true, backTo: '/practice' } },
    { path: '/extreme', name: 'extreme-hub', component: () => import('@/views/ExtremeHubView.vue'), meta: { title: '极限挑战', requiresAuth: true, backTo: '/' } },
    { path: '/extreme/session', name: 'extreme-session', component: () => import('@/views/ExtremeSessionView.vue'), meta: { title: '极限作答', requiresAuth: true, backTo: '/extreme' } },
    { path: '/extreme/result', name: 'extreme-result', component: () => import('@/views/ExtremeResultView.vue'), meta: { title: '极限结果', requiresAuth: true, backTo: '/extreme' } },
    { path: '/game', name: 'game', component: () => import('@/views/GameView.vue') },
    { path: '/game/:unitId/:levelId', name: 'game-level', component: () => import('@/views/GameView.vue') },
    { path: '/records', name: 'records', component: () => import('@/views/RecordsView.vue'), meta: { title: '学习记录', requiresAuth: true, backTo: '/' } },
    { path: '/pvp', name: 'pvp-lobby', component: () => import('@/views/PvPLobbyView.vue'), meta: { title: '竞技大厅', requiresAuth: true, backTo: '/' } },
    { path: '/pvp/room', name: 'pvp-room', component: () => import('@/views/PvPRoomView.vue'), meta: { title: '房间准备', requiresAuth: true, backTo: '/pvp' } },
    { path: '/pvp/battle', name: 'pvp-battle', component: () => import('@/views/PvPBattleView.vue'), meta: { title: 'PVP 对战', requiresAuth: true, backTo: '/pvp/room' } },
    { path: '/pvp/result', name: 'pvp-result', component: () => import('@/views/PvPResultView.vue'), meta: { title: '对战结算', requiresAuth: true, backTo: '/pvp' } },
    { path: '/leaderboard', name: 'leaderboard', component: () => import('@/views/LeaderboardView.vue'), meta: { title: '排行榜', backTo: '/' } },
    { path: '/achievements', name: 'achievements', component: () => import('@/views/AchievementsView.vue'), meta: { title: '成就墙', requiresAuth: true, backTo: '/' } },
    { path: '/admin', name: 'admin', component: () => import('@/views/AdminView.vue') },
  ]
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (to.meta.requiresAuth && !token) {
    return {
      name: 'login',
      query: { redirect: to.fullPath },
    }
  }

  if (to.path === '/game') {
    const mode = typeof to.query.mode === 'string' ? to.query.mode : ''
    if (mode === 'practice') return { name: 'practice-hub' }
    if (mode === 'extreme') return { name: 'extreme-hub' }
    return { name: 'adventure-map' }
  }

  if (to.path.startsWith('/game/')) {
    return { name: 'adventure-map' }
  }

  return true
})

export default router
