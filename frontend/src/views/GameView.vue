<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route = useRoute()
const router = useRouter()

onMounted(() => {
  const mode = typeof route.query.mode === 'string' ? route.query.mode : ''
  if (mode === 'practice') {
    router.replace('/practice')
    return
  }
  if (mode === 'extreme') {
    router.replace('/extreme')
    return
  }
  router.replace('/adventure')
})
</script>

<template>
  <div class="legacy-bridge">正在跳转到新的学生端页面…</div>
</template>

<style scoped>
.legacy-bridge {
  min-height: 40vh;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
}
</style>
