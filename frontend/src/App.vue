<script setup lang="ts">
import AppSidebar from './components/AppSidebar.vue'
import AppSprite from './components/AppSprite.vue'
</script>

<template>
  <AppSprite />
  <div class="app-shell">
    <AppSidebar />
    <router-view />
  </div>
</template>
