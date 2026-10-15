export interface ParticleBackgroundProps {
  particleCount?: number
  petalCount?: number
  particleColor?: string
  accentColor?: string
  petalColor?: string
  petalHighlight?: string
  trailStrength?: number
  trailLimit?: number
  heartScale?: number
  repulsionStrength?: number
  heartForceRadius?: number
  gravity?: number
  windStrength?: number
  driftStrength?: number
  opacity?: number
  waterlineRatio?: number
  waterDepth?: number
  rippleLimit?: number
  fieldBoundaryAlpha?: number
  fieldGlowStrength?: number
  zIndex?: number
  reducedMotion?: boolean
}

export interface ParticleConfig {
  count: number
  petalCount: number
  particleColor: string
  accentColor: string
  petalColor: string
  petalHighlight: string
  trailColor: string
  glowColor: string
  waterColor: string
  waterHighlight: string
  rippleColor: string
  trailStrength: number
  trailLimit: number
  heartScale: number
  repulsionStrength: number
  heartForceRadius: number
  gravity: number
  windStrength: number
  driftStrength: number
  waterlineRatio: number
  waterDepth: number
  rippleLimit: number
  fieldBoundaryAlpha: number
  fieldOutlineAlpha: number
  fieldGlowStrength: number
  opacity: number
  zIndex: number
  reducedMotion: boolean
}

export interface PointerState {
  x: number
  y: number
  targetX: number
  targetY: number
  active: boolean
  speed: number
  lastMovedAt: number
}

export interface Particle {
  x: number
  y: number
  vx: number
  vy: number
  radius: number
  alpha: number
  phase: number
  twinkleSpeed: number
}

export interface CometParticle {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  maxLife: number
  radius: number
  trail: Array<{ x: number; y: number }>
}

export type CherryBlossomState = 'falling' | 'floating'

export interface CherryBlossom {
  x: number
  y: number
  z: number
  vx: number
  vy: number
  rotation: number
  spin: number
  sway: number
  phase: number
  life: number
  maxLife: number
  size: number
  alpha: number
  state: CherryBlossomState
  waterY: number
  floatLife: number
  floatDuration: number
  landingLife: number
  landingMaxLife: number
  isBurst: boolean
  baseAlpha: number
}

export interface WaterRipple {
  x: number
  y: number
  life: number
  maxLife: number
  radius: number
  strength: number
}





