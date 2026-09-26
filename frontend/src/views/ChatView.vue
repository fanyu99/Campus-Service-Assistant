<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import PagePlaceholder from '../components/PagePlaceholder.vue'

const route = useRoute()

const incomingQuestion = computed(() => {
  const q = route.query.q
  return typeof q === 'string' ? q : ''
})
</script>

<template>
  <PagePlaceholder>
    <p v-if="incomingQuestion" class="ph-note">已接收问题：{{ incomingQuestion }}</p>
  </PagePlaceholder>
</template>

<style scoped>
.ph-note{margin:6px 0 0;padding:9px 14px;border:1px dashed var(--border);border-radius:12px;
  background:var(--surface);color:var(--fg);font-size:13px;max-width:52ch;word-break:break-word}
</style>