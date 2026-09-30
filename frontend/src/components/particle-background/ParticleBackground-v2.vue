<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { resolveParticleConfig } from './particle-presets'
import { ParticleEngine } from './particle-engine'
import type { ParticleBackgroundProps } from './particle-types'

const props = withDefaults(defineProps<ParticleBackgroundProps>(), {
  particleCount: 88,
  petalCount: 34,
  trailStrength: 0.34,
  trailLimit: 180,
  opacity: 0.82,
  zIndex: 0,
  reducedMotion: false,
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
let engine: ParticleEngine | null = null
let frame = 0
let lastFrame = 0
let resizeObserver: ResizeObserver | null = null
let themeObserver: MutationObserver | null = null
let mediaQuery: MediaQueryList | null = null

function readThemeColors() {
  const styles = getComputedStyle(document.documentElement)
  const readNumberVar = (name: string) => {
    const value = Number.parseFloat(styles.getPropertyValue(name).trim())
    return Number.isFinite(value) ? value : undefined
  }
  return {
    particleColor: styles.getPropertyValue('--fx-particle').trim(),
    accentColor: styles.getPropertyValue('--fx-particle-bright').trim(),
    trailColor: styles.getPropertyValue('--fx-particle-trail').trim(),
    glowColor: styles.getPropertyValue('--fx-particle-glow').trim(),
    petalColor: styles.getPropertyValue('--fx-petal').trim(),
    petalHighlight: styles.getPropertyValue('--fx-petal-highlight').trim(),
    fieldOutlineAlpha: readNumberVar('--fx-field-outline-alpha'),
    fieldGlowStrength: readNumberVar('--fx-field-glow-strength'),
  }
}

function onPointerMove(event: PointerEvent) {
  engine?.setPointer(event.clientX, event.clientY)
  startLoop()
}

function onPointerLeave() {
  engine?.clearPointer()
}

function resize() {
  const canvas = canvasRef.value
  if (!canvas || !engine) return
  const dpr = Math.min(window.devicePixelRatio || 1, 2)
  engine.resize(window.innerWidth, window.innerHeight, dpr)
  startLoop()
}

function render(timestamp: number) {
  if (!engine) return
  const delta = Math.min(2, Math.max(0.5, (timestamp - lastFrame) / 16.67 || 1))
  lastFrame = timestamp
  engine.draw(delta)
  frame = requestAnimationFrame(render)
}

function startLoop() {
  if (!frame) {
    lastFrame = performance.now()
    frame = requestAnimationFrame(render)
  }
}

function stopLoop() {
  if (frame) cancelAnimationFrame(frame)
  frame = 0
}

function createEngine() {
  const canvas = canvasRef.value
  if (!canvas) return
  stopLoop()
  engine?.destroy()
  const reducedMotion = mediaQuery?.matches ?? false
  engine = new ParticleEngine(canvas, resolveParticleConfig(props, reducedMotion, readThemeColors()))
  resize()
  startLoop()
}

function onVisibilityChange() {
  if (document.hidden) stopLoop()
  else startLoop()
}

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
  createEngine()
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(document.documentElement)
  themeObserver = new MutationObserver(() => createEngine())
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  window.addEventListener('resize', resize, { passive: true })
  window.addEventListener('pointermove', onPointerMove, { passive: true })
  window.addEventListener('pointerleave', onPointerLeave, { passive: true })
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  stopLoop()
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  window.removeEventListener('resize', resize)
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerleave', onPointerLeave)
  document.removeEventListener('visibilitychange', onVisibilityChange)
  engine?.destroy()
  engine = null
})
</script>

<template>
  <canvas
    ref="canvasRef"
    class="particle-background"
    aria-hidden="true"
    :style="{ zIndex: props.zIndex ?? 0 }"
  />
</template>

<style scoped>
.particle-background {
  position: fixed;
  inset: 0;
  display: block;
  width: 100vw;
  height: 100vh;
  pointer-events: none;
  overflow: hidden;
}
</style>


