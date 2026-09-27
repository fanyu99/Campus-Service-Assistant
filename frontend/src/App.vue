<script setup lang="ts">
import AppSidebar from './components/AppSidebar.vue'
import AppSprite from './components/AppSprite.vue'
import ParticleBackground from './components/particle-background/ParticleBackground.vue'
import { useTheme } from './composables/useTheme'

useTheme()
</script>

<template>
  <AppSprite />
  <ParticleBackground
    :particle-count="82"
    :petal-count="72"
    :heart-scale="62"
    :repulsion-strength="0.86"
    :heart-force-radius="1.22"
    :gravity="0.012"
    :wind-strength="0.022"
    :drift-strength="0.28"
    :trail-strength="0.26"
    :trail-limit="120"
    :waterline-ratio="0.88"
    :water-depth="0.06"
    :ripple-limit="54"
    :opacity="0.82"
  />
  <div class="app-shell">
    <AppSidebar />
    <Transition name="route" mode="out-in">
      <router-view v-slot="{ Component, route }">
        <component :is="Component" :key="route.fullPath" />
      </router-view>
    </Transition>
  </div>
</template>






