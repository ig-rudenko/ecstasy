<script setup>
import {computed} from 'vue'
import {RouterLink} from 'vue-router'

const props = defineProps({
  to: {
    type: [String, Object],
    required: true,
  },
  target: {
    type: String,
    required: false,
    default: 'self'
  }
})

const isExternalLink = computed(() => {
  return typeof props.to === 'string' && props.to.startsWith('http')
})
</script>

<template>
  <a v-if="isExternalLink" :href="to" :target="target">
    <slot/>
  </a>
  <router-link v-else :to="to">
    <slot/>
  </router-link>
</template>