<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { resolveParticleConfig } from './particle-presets'
import { ParticleEngine } from './particle-engine'
import type { ParticleBackgroundProps } from './particle-types'

const props = withDefaults(defineProps<ParticleBackgroundProps>(), {
  particleCount: 82,
  petalCount: 72,
  trailStrength: 0.26,
  trailLimit: 120,
  heartScale: 62,
  repulsionStrength: 0.86,
  heartForceRadius: 1.22,
  gravity: 0.012,
  windStrength: 0.022,
  driftStrength: 0.28,
  waterlineRatio: 0.88,
  waterDepth: 0.06,
  rippleLimit: 54,
  fieldBoundaryAlpha: 0,
  fieldGlowStrength: 0,
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
    waterColor: styles.getPropertyValue('--fx-water').trim(),
    waterHighlight: styles.getPropertyValue('--fx-water-highlight').trim(),
    rippleColor: styles.getPropertyValue('--fx-ripple').trim(),
    fieldOutlineAlpha: readNumberVar('--fx-field-outline-alpha'),
    fieldGlowStrength: readNumberVar('--fx-field-glow-strength'),
  }
}

function onPointerDown(event: PointerEvent) {
  if (event.pointerType === 'mouse' && event.button !== 0) return
  engine?.spawnBurst(event.clientX, event.clientY)
  startLoop()
}
function onPointerMove(event: PointerEvent) {
  engine?.setPointer(event.clientX, event.clientY)
  startLoop()
}

function onTouchMove(event: TouchEvent) {
  const touch = event.touches[0]
  if (!touch) return
  engine?.setPointer(touch.clientX, touch.clientY)
  startLoop()
}

function onPointerLeave() {
  engine?.clearPointer()
}

function onTouchEnd() {
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
  themeObserver = new MutationObserver(() => {
    createEngine()
    // 立刻补画一帧：换主题可能正被 View Transitions 拍快照，只靠 rAF 会让
    // 新快照里留着旧配色（粒子颜色与底色渐变都会滞后一拍）。
    engine?.draw(1)
  })
  themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
  window.addEventListener('resize', resize, { passive: true })
  window.addEventListener('pointerdown', onPointerDown, { passive: true })
  window.addEventListener('pointermove', onPointerMove, { passive: true })
  window.addEventListener('pointerleave', onPointerLeave, { passive: true })
  window.addEventListener('touchmove', onTouchMove, { passive: true })
  window.addEventListener('touchend', onTouchEnd, { passive: true })
  window.addEventListener('touchcancel', onTouchEnd, { passive: true })
  document.addEventListener('visibilitychange', onVisibilityChange)
})

onBeforeUnmount(() => {
  stopLoop()
  resizeObserver?.disconnect()
  themeObserver?.disconnect()
  window.removeEventListener('resize', resize)
  window.removeEventListener('pointerdown', onPointerDown)
  window.removeEventListener('pointermove', onPointerMove)
  window.removeEventListener('pointerleave', onPointerLeave)
  window.removeEventListener('touchmove', onTouchMove)
  window.removeEventListener('touchend', onTouchEnd)
  window.removeEventListener('touchcancel', onTouchEnd)
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







