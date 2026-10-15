import type { Ref } from 'vue'

/**
 * Legacy compatibility hook. The product now uses the single global
 * ParticleBackground canvas, so this hook intentionally does not mount a second field.
 */
export function useHeroField(_root: Ref<HTMLElement | null>) {
  return undefined
}
