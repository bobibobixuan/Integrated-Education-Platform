import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import HomeView from '@/views/HomeView.vue'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: HomeView },
      { path: '/login', component: { template: '<div />' } },
      { path: '/adventure', component: { template: '<div />' } },
      { path: '/practice', component: { template: '<div />' } },
      { path: '/extreme', component: { template: '<div />' } },
      { path: '/pvp', component: { template: '<div />' } },
      { path: '/records', component: { template: '<div />' } },
      { path: '/achievements', component: { template: '<div />' } },
      { path: '/leaderboard', component: { template: '<div />' } },
      { path: '/account', component: { template: '<div />' } },
    ],
  })
}

describe('HomeView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('renders the student navigation hub', async () => {
    const router = makeRouter()
    router.push('/')
    await router.isReady()

    const wrapper = mount(HomeView, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.text()).toContain('知识学习对战平台')
    expect(wrapper.text()).toContain('账号状态')
    expect(wrapper.text()).toContain('开始冒险')
    expect(wrapper.text()).toContain('去登录')
  })
})
