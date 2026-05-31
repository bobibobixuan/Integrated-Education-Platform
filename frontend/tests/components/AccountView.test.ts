import { describe, it, expect, beforeEach } from 'vitest'
import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { createMemoryHistory, createRouter } from 'vue-router'
import AccountView from '@/views/AccountView.vue'
import { useAuthStore } from '@/stores/auth'

function makeRouter() {
  return createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: { template: '<div />' } },
      { path: '/account', component: AccountView },
      { path: '/login', component: { template: '<div />' } },
    ],
  })
}

describe('AccountView', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    const auth = useAuthStore()
    auth.user = {
      id: 1,
      username: 'alice',
      nickname: 'Alice',
      role: 'user',
      is_active: true,
    }
    auth.token = 'token'
  })

  it('renders account forms', async () => {
    const router = makeRouter()
    router.push('/account')
    await router.isReady()

    const wrapper = mount(AccountView, {
      global: {
        plugins: [router],
      },
    })

    expect(wrapper.text()).toContain('个人中心')
    expect(wrapper.text()).toContain('基本资料')
    expect(wrapper.text()).toContain('密码管理')
  })
})
