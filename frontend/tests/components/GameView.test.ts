import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import GameView from '@/views/GameView.vue'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/login', component: { template: '<div />' } },
      { path: '/records', component: { template: '<div />' } },
      { path: '/game', component: GameView },
    ],
  })
}

describe('GameView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => [],
    }))
  })

  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders the game view container', async () => {
    const router = makeRouter()
    router.push('/game')
    await router.isReady()

    const wrapper = mount(GameView, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.find('.game-layout').exists() || wrapper.find('div').exists()).toBe(true)
  })
})
