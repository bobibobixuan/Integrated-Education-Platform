<script setup lang="ts">
import brandLogo from '@/assets/brand-logo.svg'
import { APP_ENGLISH_NAME } from '@/brand'

const props = withDefaults(defineProps<{
  alt?: string
  label?: string
  sublabel?: string
  size?: 'sm' | 'md' | 'lg'
  stacked?: boolean
}>(), {
  alt: APP_ENGLISH_NAME,
  label: '',
  sublabel: '',
  size: 'md',
  stacked: false,
})
</script>

<template>
  <div class="brand-logo" :class="[`brand-logo--${props.size}`, { 'brand-logo--stacked': props.stacked }]">
    <img class="brand-logo__image" :src="brandLogo" :alt="props.alt" />
    <div v-if="props.label || props.sublabel" class="brand-logo__copy">
      <strong v-if="props.label">{{ props.label }}</strong>
      <span v-if="props.sublabel">{{ props.sublabel }}</span>
    </div>
  </div>
</template>

<style scoped>
.brand-logo {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand-logo--stacked {
  flex-direction: column;
  align-items: flex-start;
}

.brand-logo__image {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
  filter: drop-shadow(0 10px 20px rgba(15, 23, 42, 0.12));
}

.brand-logo--sm .brand-logo__image {
  width: 34px;
  height: 34px;
}

.brand-logo--md .brand-logo__image {
  width: 46px;
  height: 46px;
}

.brand-logo--lg .brand-logo__image {
  width: 72px;
  height: 72px;
}

.brand-logo__copy {
  display: grid;
  gap: 2px;
  min-width: 0;
}

.brand-logo__copy strong {
  color: inherit;
  font-size: inherit;
  font-weight: 800;
  line-height: 1.1;
}

.brand-logo__copy span {
  color: inherit;
  opacity: 0.7;
  font-size: 0.78em;
  letter-spacing: 0.12em;
  text-transform: uppercase;
}
</style>
