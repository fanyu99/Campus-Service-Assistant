import type {
  CherryBlossom,
  CometParticle,
  Particle,
  ParticleConfig,
  PointerState,
  WaterRipple,
} from './particle-types'

const TAU = Math.PI * 2

export class ParticleEngine {
  private readonly ctx: CanvasRenderingContext2D
  private readonly canvas: HTMLCanvasElement
  private readonly config: ParticleConfig
  private particles: Particle[] = []
  private petals: CherryBlossom[] = []
  private burstPool: CherryBlossom[] = []
  private ripples: WaterRipple[] = []
  private comets: CometParticle[] = []
  private pointer: PointerState = { x: 0, y: 0, targetX: 0, targetY: 0, active: false, speed: 0, lastMovedAt: 0 }
  private width = 0
  private height = 0
  private waterY = 0
  private lastCometX = 0
  private lastCometY = 0

  constructor(canvas: HTMLCanvasElement, config: ParticleConfig) {
    const context = canvas.getContext('2d')
    if (!context) throw new Error('Canvas 2D context unavailable')
    this.canvas = canvas
    this.ctx = context
    this.config = config
  }

  resize(width: number, height: number, dpr = 1): void {
    this.width = width
    this.height = height
    this.waterY = height * this.config.waterlineRatio
    this.canvas.width = Math.floor(width * dpr)
    this.canvas.height = Math.floor(height * dpr)
    this.canvas.style.width = `${width}px`
    this.canvas.style.height = `${height}px`
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

    if (this.particles.length === 0) this.seedParticles()
    else this.wrapParticles()
    if (this.petals.length === 0) this.seedPetals()
    else this.petals.forEach((petal) => {
      petal.x = Math.min(Math.max(petal.x, -80), width + 80)
      petal.waterY = this.waterY + this.waveAt(petal.x, 0)
      if (petal.state === 'floating') petal.y = petal.waterY
    })
  }

  setPointer(x: number, y: number, active = true): void {
    const dx = x - this.pointer.targetX
    const dy = y - this.pointer.targetY
    const distance = Math.hypot(dx, dy)
    this.pointer.speed = Math.min(1, distance / 55)
    this.pointer.targetX = x
    this.pointer.targetY = y
    this.pointer.active = active
    this.pointer.lastMovedAt = performance.now()

    if (!this.config.reducedMotion && distance > 5 && distance > Math.hypot(x - this.lastCometX, y - this.lastCometY)) {
      this.spawnComet(x, y, dx, dy)
      this.lastCometX = x
      this.lastCometY = y
    }
  }

  clearPointer(): void {
    this.pointer.active = false
  }

  draw(delta = 1): void {
    if (!this.width || !this.height) return
    const { ctx } = this
    ctx.clearRect(0, 0, this.width, this.height)
    this.updatePointer()
    this.updateParticles(delta)
    this.updatePetals(delta)
    this.updateRipples(delta)
    this.updateComets(delta)
    this.drawAtmosphere()
    this.drawWaterSurface()
    this.drawHeartField()
    this.drawRipples()
    this.drawPetals()
    this.drawParticles()
    this.drawComets()
  }

  destroy(): void {
    this.particles = []
    this.petals = []
    this.burstPool = []
    this.ripples = []
    this.comets = []
    this.ctx.clearRect(0, 0, this.width, this.height)
  }

  private seedParticles(): void {
    this.particles = Array.from({ length: this.config.count }, () => ({
      x: Math.random() * this.width,
      y: Math.random() * this.height,
      vx: (Math.random() - 0.5) * 0.16,
      vy: (Math.random() - 0.5) * 0.16,
      radius: 0.7 + Math.random() * 1.4,
      alpha: 0.16 + Math.random() * 0.36,
      phase: Math.random() * TAU,
      twinkleSpeed: 0.01 + Math.random() * 0.022,
    }))
  }

  private seedPetals(): void {
    const widthFactor = Math.min(1.48, Math.max(0.72, this.width / 960))
    const count = Math.max(20, Math.round(this.config.petalCount * widthFactor))
    this.petals = Array.from({ length: count }, () => this.createPetal(true))
  }

  private createPetal(initial = false): CherryBlossom {
    const depth = Math.random()
    const size = 5 + depth * 10
    const waterY = this.waterY + this.waveAt(Math.random() * this.width, 0)
    return {
      x: Math.random() * (this.width + 110) - 55,
      y: initial ? Math.random() * (waterY + 80) - 40 : -size - Math.random() * 80,
      z: depth,
      vx: -0.18 + Math.random() * 0.42,
      vy: 0.32 + depth * 1.04,
      rotation: Math.random() * TAU,
      spin: (Math.random() - 0.5) * (0.014 + depth * 0.036),
      sway: 5 + Math.random() * (11 + depth * 18),
      phase: Math.random() * TAU,
      life: 0,
      maxLife: 780 + Math.random() * 560,
      size,
      alpha: 0.38 + depth * 0.44,
      state: 'falling',
      waterY,
      floatLife: 0,
      floatDuration: 180 + Math.random() * 300,
      landingLife: 0,
      landingMaxLife: 34 + Math.random() * 18,
      isBurst: false,
      baseAlpha: 0.38 + depth * 0.44,
    }
  }

  spawnBurst(x: number, y: number): void {
    if (this.config.reducedMotion) return
    this.setPointer(x, y)

    const count = 10 + Math.floor(Math.random() * 21)
    for (let index = 0; index < count; index += 1) {
      const activeBursts = this.petals.filter((petal) => petal.isBurst)
      let petal: CherryBlossom | undefined

      if (activeBursts.length >= 200) {
        const oldest = activeBursts.reduce((candidate, current) => (
          current.life / current.maxLife > candidate.life / candidate.maxLife ? current : candidate
        ))
        const oldestIndex = this.petals.indexOf(oldest)
        if (oldestIndex >= 0) {
          this.petals.splice(oldestIndex, 1)
          petal = oldest
        }
      }

      if (!petal && activeBursts.length < 200) {
        petal = this.burstPool.pop() ?? this.createPetal()
      }
      if (!petal) continue

      const angle = Math.random() * TAU
      const speed = 3 + Math.random() * 6
      const depth = 0.58 + Math.random() * 0.42
      const size = 5 + depth * 8
      const baseAlpha = 0.62 + Math.random() * 0.32
      petal.x = x
      petal.y = y
      petal.z = depth
      petal.vx = Math.cos(angle) * speed + (Math.random() - 0.5) * 0.45
      petal.vy = Math.sin(angle) * speed + (Math.random() - 0.5) * 0.45
      petal.rotation = Math.random() * TAU
      petal.spin = (Math.random() - 0.5) * 0.14
      petal.sway = 1.5 + Math.random() * 3
      petal.phase = Math.random() * TAU
      petal.life = 0
      petal.maxLife = 120 + Math.random() * 120
      petal.size = size
      petal.alpha = baseAlpha
      petal.baseAlpha = baseAlpha
      petal.state = 'falling'
      petal.waterY = this.waterY
      petal.floatLife = 0
      petal.floatDuration = 0
      petal.landingLife = 0
      petal.landingMaxLife = 0
      petal.isBurst = true
      this.petals.push(petal)
    }
  }
  private spawnComet(x: number, y: number, dx: number, dy: number): void {
    if (this.comets.length >= this.config.trailLimit) this.comets.splice(0, Math.ceil(this.comets.length * 0.14))
    const speed = Math.min(1, Math.hypot(dx, dy) / 36)
    const trailLength = Math.min(8, 3 + Math.floor(speed * 5))
    const trail = Array.from({ length: trailLength }, (_, index) => ({ x: x - dx * index * 0.2, y: y - dy * index * 0.2 }))
    this.comets.push({ x, y, vx: dx * 0.07, vy: dy * 0.07, life: 0, maxLife: 22 + speed * 26, radius: 1.2 + speed * 1.9, trail })
  }

  private updatePointer(): void {
    this.pointer.x += (this.pointer.targetX - this.pointer.x) * 0.15
    this.pointer.y += (this.pointer.targetY - this.pointer.y) * 0.15
    this.pointer.speed *= 0.9
    // The field remains active while the pointer stays inside the page; pointerleave/touchend explicitly clears it.
  }

  private updateParticles(delta: number): void {
    for (const particle of this.particles) {
      particle.x += particle.vx * delta
      particle.y += particle.vy * delta
      particle.phase += particle.twinkleSpeed * delta
      if (particle.x < -12) particle.x = this.width + 12
      if (particle.x > this.width + 12) particle.x = -12
      if (particle.y < -12) particle.y = this.height + 12
      if (particle.y > this.height + 12) particle.y = -12
    }
  }

  private updatePetals(delta: number): void {
    for (let index = this.petals.length - 1; index >= 0; index -= 1) {
      const petal = this.petals[index]
      petal.life += delta
      petal.phase += 0.018 * delta
      petal.rotation += petal.spin * delta

      if (petal.isBurst) {
        const progress = Math.min(1, petal.life / petal.maxLife)
        petal.vy += this.config.gravity * 1.8 * delta
        petal.vx += Math.sin(petal.phase * 0.72 + petal.life * 0.012) * this.config.windStrength * 0.35 * delta
        this.applyHeartRepulsion(petal, delta)
        petal.vx *= Math.pow(0.985, delta)
        petal.vy *= Math.pow(0.985, delta)
        petal.x += petal.vx * delta
        petal.y += petal.vy * delta
        petal.alpha = petal.baseAlpha * Math.pow(1 - progress, 0.85)
        if (petal.life >= petal.maxLife) {
          this.petals.splice(index, 1)
          if (this.burstPool.length < 200) this.burstPool.push(petal)
        }
        continue
      }

      if (petal.state === 'floating') {
        petal.floatLife += delta
        petal.landingLife += delta
        const drift = this.config.driftStrength * (0.6 + petal.z * 0.8)
        petal.x += (0.16 + drift * 0.6 + Math.sin(petal.phase * 0.38) * 0.22) * delta
        petal.waterY = this.waterY + this.waveAt(petal.x, petal.floatLife)
        petal.y += (petal.waterY - petal.y) * 0.08
        petal.rotation += Math.sin(petal.phase * 0.5) * 0.006 * delta
        petal.alpha *= 0.9992
        if (petal.floatLife > petal.floatDuration || petal.x > this.width + 90 || petal.alpha < 0.08) this.petals[index] = this.createPetal()
        continue
      }

      petal.vy = Math.min(petal.vy + this.config.gravity * delta, 2.35)
      petal.vx += Math.sin(petal.phase * 0.72 + petal.life * 0.012) * this.config.windStrength * delta
      petal.vx *= 0.996
      this.applyHeartRepulsion(petal, delta)
      petal.x += (petal.vx + Math.sin(petal.phase) * petal.sway * 0.012) * delta
      petal.y += petal.vy * delta

      const surfaceY = this.waterY + this.waveAt(petal.x, petal.life)
      if (petal.y >= surfaceY) {
        petal.state = 'floating'
        petal.waterY = surfaceY
        petal.y = surfaceY
        petal.vy = 0
        petal.vx *= 0.35
        petal.floatLife = 0
        petal.landingLife = 0
        this.spawnRipple(petal.x, surfaceY, 0.6 + petal.z * 0.45)
      } else if (petal.life >= petal.maxLife || petal.x < -120 || petal.x > this.width + 120) {
        this.petals[index] = this.createPetal()
      }
    }
  }

  private applyHeartRepulsion(petal: CherryBlossom, delta: number): void {
    if (!this.pointer.active || this.config.repulsionStrength <= 0) return
    const dx = petal.x - this.pointer.x
    const dy = petal.y - this.pointer.y
    const scale = this.heartScale()
    const x = dx / scale
    const y = -dy / scale
    const heartValue = Math.pow(x * x + y * y - 1, 3) - x * x * Math.pow(y, 3)
    if (heartValue >= 0) return

    // The implicit heart curve is negative inside. Use both the signed field depth
    // and the local radius so the petal is pushed out smoothly instead of snapping.
    const fieldDepth = Math.min(1.35, Math.max(0, -heartValue) * 2.2)
    const distance = Math.max(0.1, Math.hypot(dx, dy))
    const radial = Math.min(1, distance / Math.max(1, scale))
    const falloff = 0.2 + fieldDepth * 0.8
    const force = this.config.repulsionStrength * falloff * (0.55 + radial * 0.45) * delta
    const nx = dx / distance
    const ny = dy / distance
    const tangent = Math.sin(petal.phase * 0.55 + petal.life * 0.008) * 0.18

    petal.vx += nx * force + -ny * force * tangent
    petal.vy += ny * force + nx * force * tangent
    petal.vx *= 0.985
    petal.vy *= 0.985
  }

  private updateRipples(delta: number): void {
    for (let index = this.ripples.length - 1; index >= 0; index -= 1) {
      const ripple = this.ripples[index]
      ripple.life += delta
      ripple.radius += (0.9 + ripple.strength * 0.7) * delta
      if (ripple.life >= ripple.maxLife) this.ripples.splice(index, 1)
    }
  }

  private spawnRipple(x: number, y: number, strength: number): void {
    if (this.config.rippleLimit <= 0) return
    if (this.ripples.length >= this.config.rippleLimit) this.ripples.shift()
    this.ripples.push({ x, y, life: 0, maxLife: 48 + strength * 24, radius: 2 + strength * 2, strength })
  }

  private updateComets(delta: number): void {
    for (let index = this.comets.length - 1; index >= 0; index -= 1) {
      const comet = this.comets[index]
      comet.life += delta
      comet.x += comet.vx * delta
      comet.y += comet.vy * delta
      comet.vx *= 0.9
      comet.vy *= 0.9
      for (let trailIndex = comet.trail.length - 1; trailIndex > 0; trailIndex -= 1) {
        comet.trail[trailIndex].x += (comet.trail[trailIndex - 1].x - comet.trail[trailIndex].x) * 0.45
        comet.trail[trailIndex].y += (comet.trail[trailIndex - 1].y - comet.trail[trailIndex].y) * 0.45
      }
      comet.trail[0].x += (comet.x - comet.trail[0].x) * 0.65
      comet.trail[0].y += (comet.y - comet.trail[0].y) * 0.65
      if (comet.life >= comet.maxLife) this.comets.splice(index, 1)
    }
  }

  private wrapParticles(): void {
    for (const particle of this.particles) {
      particle.x = Math.min(Math.max(particle.x, -12), this.width + 12)
      particle.y = Math.min(Math.max(particle.y, -12), this.height + 12)
    }
  }

  private drawAtmosphere(): void {
    const gradient = this.ctx.createLinearGradient(0, 0, 0, this.height)
    gradient.addColorStop(0, 'rgba(24, 28, 36, 0.16)')
    gradient.addColorStop(Math.max(0.42, this.config.waterlineRatio - 0.08), 'rgba(50, 35, 43, 0.05)')
    gradient.addColorStop(1, 'rgba(8, 20, 30, 0.12)')
    this.ctx.fillStyle = gradient
    this.ctx.fillRect(0, 0, this.width, this.height)

    if (!this.pointer.active || this.config.reducedMotion) return
    const radius = 170 + this.pointer.speed * 120
    const glow = this.ctx.createRadialGradient(this.pointer.x, this.pointer.y, 0, this.pointer.x, this.pointer.y, radius)
    glow.addColorStop(0, `rgba(${this.config.glowColor}, ${(0.05 + this.pointer.speed * 0.08).toFixed(3)})`)
    glow.addColorStop(1, `rgba(${this.config.glowColor}, 0)`)
    this.ctx.fillStyle = glow
    this.ctx.fillRect(0, 0, this.width, this.height)
  }

  private drawWaterSurface(): void {
    const { ctx } = this
    // Keep the water transparent: only a thin, perspective-like shimmer anchors
    // the bottom edge without tinting the page with a large opaque panel.
    ctx.save()
    ctx.globalAlpha = 0.085 * this.config.opacity
    ctx.strokeStyle = this.config.waterHighlight
    ctx.lineWidth = 0.8
    for (let row = 0; row < 4; row += 1) {
      const depth = row / 3
      const y = this.waterY + 10 + depth * (this.height - this.waterY - 16)
      const amplitude = 1 + depth * 2.2
      ctx.beginPath()
      for (let x = -24; x <= this.width + 24; x += 20) {
        const wave = Math.sin(x * 0.016 + row * 0.85 + performance.now() * 0.00028) * amplitude
        if (x === -24) ctx.moveTo(x, y + wave)
        else ctx.lineTo(x, y + wave)
      }
      ctx.stroke()
    }
    ctx.restore()
  }

  private drawHeartField(): void {
    if (
      !this.pointer.active ||
      this.config.reducedMotion ||
      (this.config.fieldOutlineAlpha <= 0.01 && this.config.fieldGlowStrength <= 0.01)
    ) return

    const scale = this.heartScale()
    const glowAlpha = (0.035 + this.pointer.speed * 0.045) * this.config.fieldGlowStrength * this.config.opacity
    const glow = this.ctx.createRadialGradient(this.pointer.x, this.pointer.y, scale * 0.18, this.pointer.x, this.pointer.y, scale * 1.5)
    glow.addColorStop(0, `rgba(${this.config.glowColor}, ${glowAlpha.toFixed(3)})`)
    glow.addColorStop(0.68, `rgba(${this.config.glowColor}, ${(glowAlpha * 0.45).toFixed(3)})`)
    glow.addColorStop(1, `rgba(${this.config.glowColor}, 0)`)
    this.ctx.fillStyle = glow
    this.ctx.fillRect(this.pointer.x - scale * 1.65, this.pointer.y - scale * 1.65, scale * 3.3, scale * 3.3)

    if (this.config.fieldOutlineAlpha <= 0.01) return
    this.ctx.save()
    const boundaryAlpha = this.config.fieldOutlineAlpha * (0.42 + this.pointer.speed * 0.58) * this.config.opacity
    const boundaryColor = this.config.petalHighlight

    // Draw a continuous, softly blurred heart boundary instead of a hard dashed outline.
    this.ctx.globalAlpha = boundaryAlpha
    this.ctx.strokeStyle = boundaryColor
    this.ctx.lineWidth = 1.2 + this.pointer.speed * 0.45
    this.ctx.shadowColor = boundaryColor
    this.ctx.shadowBlur = 12 + this.pointer.speed * 8
    this.traceHeart(this.pointer.x, this.pointer.y, scale)
    this.ctx.stroke()

    // Keep a restrained core edge so the boundary remains legible inside the glow.
    this.ctx.shadowBlur = 0
    this.ctx.globalAlpha = boundaryAlpha * 0.38
    this.ctx.lineWidth = 0.7
    this.traceHeart(this.pointer.x, this.pointer.y, scale)
    this.ctx.stroke()
    this.ctx.restore()
  }

  private drawRipples(): void {
    const { ctx } = this
    for (const ripple of this.ripples) {
      const progress = Math.min(1, ripple.life / ripple.maxLife)
      ctx.save()
      ctx.translate(ripple.x, ripple.y)
      ctx.scale(1, 0.25)
      ctx.globalAlpha = (1 - progress) * 0.52 * this.config.opacity * ripple.strength
      ctx.strokeStyle = this.config.rippleColor
      ctx.lineWidth = 0.8 + ripple.strength * 0.25
      ctx.beginPath()
      ctx.ellipse(0, 0, ripple.radius, ripple.radius * 0.54, 0, 0, TAU)
      ctx.stroke()
      ctx.restore()
    }
    ctx.globalAlpha = 1
  }

  private drawPetals(): void {
    const { ctx } = this
    const sorted = [...this.petals].sort((a, b) => a.z - b.z)
    for (const petal of sorted) {
      const depthScale = 0.58 + petal.z * 0.72
      const size = petal.size * depthScale
      const surfaceAlpha = petal.state === 'floating' ? 0.78 : 1
      ctx.save()
      ctx.translate(petal.x, petal.y - (petal.state === 'floating' ? size * 0.16 : 0))
      ctx.rotate(petal.rotation)
      ctx.globalAlpha = petal.alpha * surfaceAlpha * this.config.opacity
      ctx.fillStyle = petal.z > 0.58 ? this.config.petalHighlight : this.config.petalColor
      ctx.beginPath()
      ctx.moveTo(0, size * 0.52)
      ctx.bezierCurveTo(-size * 0.9, size * 0.18, -size * 0.58, -size * 0.74, 0, -size * 0.26)
      ctx.bezierCurveTo(size * 0.58, -size * 0.74, size * 0.9, size * 0.18, 0, size * 0.52)
      ctx.fill()
      ctx.globalAlpha *= 0.34
      ctx.fillStyle = this.config.accentColor
      ctx.fillRect(-size * 0.08, -size * 0.18, Math.max(1, size * 0.12), size * 0.58)
      ctx.restore()
    }
    ctx.globalAlpha = 1
  }

  private drawParticles(): void {
    const { ctx } = this
    for (const particle of this.particles) {
      const pulse = 0.72 + Math.sin(particle.phase) * 0.28
      ctx.globalAlpha = particle.alpha * pulse * this.config.opacity
      ctx.fillStyle = this.config.particleColor
      ctx.fillRect(Math.floor(particle.x), Math.floor(particle.y), Math.max(1, Math.floor(particle.radius)), Math.max(1, Math.floor(particle.radius)))
    }
    ctx.globalAlpha = 1
  }

  private drawComets(): void {
    const { ctx } = this
    for (const comet of this.comets) {
      const lifeAlpha = 1 - comet.life / comet.maxLife
      for (let index = comet.trail.length - 1; index >= 0; index -= 1) {
        const point = comet.trail[index]
        const trailProgress = index / Math.max(1, comet.trail.length - 1)
        const pixelSize = Math.max(1, Math.floor(comet.radius * (1.1 - trailProgress * 0.55)))
        ctx.globalAlpha = lifeAlpha * this.config.trailStrength * (1 - trailProgress) * 0.95
        ctx.fillStyle = index % 4 === 0 ? this.config.trailColor : this.config.accentColor
        ctx.fillRect(Math.floor(point.x - pixelSize / 2), Math.floor(point.y - pixelSize / 2), pixelSize, pixelSize)
      }
      ctx.globalAlpha = lifeAlpha
      ctx.fillStyle = this.config.trailColor
      const headSize = Math.max(2, Math.floor(comet.radius * 1.7))
      ctx.fillRect(Math.floor(comet.x - headSize / 2), Math.floor(comet.y - headSize / 2), headSize, headSize)
    }
    ctx.globalAlpha = 1
  }

  private heartScale(): number {
    const responsiveScale = Math.min(1.15, Math.max(0.82, Math.min(this.width, this.height) / 780))
    return Math.min(this.config.heartScale * responsiveScale, Math.min(this.width, this.height) * 0.28)
  }

  private traceHeart(centerX: number, centerY: number, scale: number): void {
    const { ctx } = this
    const steps = 96
    for (let index = 0; index <= steps; index += 1) {
      const t = (index / steps) * TAU
      const x = Math.sin(t) ** 3
      const y = -(13 * Math.cos(t) - 5 * Math.cos(2 * t) - 2 * Math.cos(3 * t) - Math.cos(4 * t)) / 16
      const px = centerX + x * scale
      const py = centerY + y * scale
      if (index === 0) ctx.moveTo(px, py)
      else ctx.lineTo(px, py)
    }
  }

  private waveAt(x: number, time: number): number {
    return Math.sin(x * 0.018 + time * 0.026) * 1.7 + Math.sin(x * 0.008 - time * 0.016) * 1.1
  }
}








