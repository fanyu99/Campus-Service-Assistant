import type { ParticleBackgroundProps, ParticleConfig } from './particle-types'

export const defaultParticleConfig: ParticleConfig = {
  count: 82,
  petalCount: 72,
  particleColor: '#b84735',
  accentColor: '#e85d4a',
  petalColor: '#d86b58',
  petalHighlight: '#f4b6a6',
  trailColor: '#ffffff',
  glowColor: '246, 105, 82',
  waterColor: '25, 39, 52',
  waterHighlight: '255, 188, 170',
  rippleColor: '255, 188, 170',
  fieldOutlineAlpha: 0.56,
  trailStrength: 0.26,
  trailLimit: 120,
  heartScale: 156,
  repulsionStrength: 0.54,
  heartForceRadius: 1.18,
  gravity: 0.012,
  windStrength: 0.022,
  driftStrength: 0.28,
  waterlineRatio: 0.72,
  waterDepth: 0.28,
  rippleLimit: 54,
  fieldBoundaryAlpha: 0.72,
  fieldGlowStrength: 0.72,
  opacity: 0.82,
  zIndex: 0,
  reducedMotion: false,
}

export function resolveParticleConfig(
  props: ParticleBackgroundProps,
  reducedMotionPreference: boolean,
  themeColors: Partial<Pick<ParticleConfig, 'particleColor' | 'accentColor' | 'trailColor' | 'glowColor' | 'petalColor' | 'petalHighlight' | 'waterColor' | 'waterHighlight' | 'rippleColor' | 'fieldOutlineAlpha' | 'fieldGlowStrength'>> = {},
): ParticleConfig {
  const config: ParticleConfig = {
    ...defaultParticleConfig,
    count: props.particleCount ?? defaultParticleConfig.count,
    petalCount: props.petalCount ?? defaultParticleConfig.petalCount,
    particleColor: props.particleColor ?? themeColors.particleColor ?? defaultParticleConfig.particleColor,
    accentColor: props.accentColor ?? themeColors.accentColor ?? defaultParticleConfig.accentColor,
    petalColor: props.petalColor ?? themeColors.petalColor ?? defaultParticleConfig.petalColor,
    petalHighlight: props.petalHighlight ?? themeColors.petalHighlight ?? defaultParticleConfig.petalHighlight,
    trailColor: themeColors.trailColor ?? defaultParticleConfig.trailColor,
    glowColor: themeColors.glowColor ?? defaultParticleConfig.glowColor,
    waterColor: themeColors.waterColor ?? defaultParticleConfig.waterColor,
    waterHighlight: themeColors.waterHighlight ?? defaultParticleConfig.waterHighlight,
    rippleColor: themeColors.rippleColor ?? defaultParticleConfig.rippleColor,
    fieldOutlineAlpha: themeColors.fieldOutlineAlpha ?? defaultParticleConfig.fieldOutlineAlpha,
    trailStrength: props.trailStrength ?? defaultParticleConfig.trailStrength,
    trailLimit: props.trailLimit ?? defaultParticleConfig.trailLimit,
    heartScale: props.heartScale ?? defaultParticleConfig.heartScale,
    repulsionStrength: props.repulsionStrength ?? defaultParticleConfig.repulsionStrength,
    heartForceRadius: props.heartForceRadius ?? defaultParticleConfig.heartForceRadius,
    gravity: props.gravity ?? defaultParticleConfig.gravity,
    windStrength: props.windStrength ?? defaultParticleConfig.windStrength,
    driftStrength: props.driftStrength ?? defaultParticleConfig.driftStrength,
    waterlineRatio: props.waterlineRatio ?? defaultParticleConfig.waterlineRatio,
    waterDepth: props.waterDepth ?? defaultParticleConfig.waterDepth,
    rippleLimit: props.rippleLimit ?? defaultParticleConfig.rippleLimit,
    fieldBoundaryAlpha: props.fieldBoundaryAlpha ?? defaultParticleConfig.fieldBoundaryAlpha,
    fieldGlowStrength: props.fieldGlowStrength ?? themeColors.fieldGlowStrength ?? defaultParticleConfig.fieldGlowStrength,
    opacity: props.opacity ?? defaultParticleConfig.opacity,
    zIndex: props.zIndex ?? defaultParticleConfig.zIndex,
    reducedMotion: props.reducedMotion ?? defaultParticleConfig.reducedMotion,
  }

  if (reducedMotionPreference || config.reducedMotion) {
    config.count = Math.min(config.count, 32)
    config.petalCount = Math.min(config.petalCount, 32)
    config.trailLimit = 0
    config.trailStrength = 0
    config.repulsionStrength = 0
    config.rippleLimit = Math.min(config.rippleLimit, 16)
  }

  return config
}

