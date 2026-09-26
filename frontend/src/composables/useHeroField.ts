import { onBeforeUnmount, onMounted, type Ref } from 'vue'

/**
 * 搜索栏（输入框）背后的动态色块层 —— 沿用原首页 hero 的结构：
 * 两枚随指针缓动的有机色块 + 点阵 + 指针附近的辉光与点阵扰动（canvas）。
 * 配色由原来的暖橙/米色改为角色头发色相（oklch 74% .154 36）。
 */
export function useHeroField(root: Ref<HTMLElement | null>) {
  let raf = 0
  let ctx: CanvasRenderingContext2D | null = null
  let w = 0
  let h = 0
  const p = { x: 0, y: 0, tx: 0, ty: 0, vx: 0, vy: 0, live: false }
  let elOrb1: HTMLElement | null = null
  let elOrb2: HTMLElement | null = null
  let elGlow: HTMLElement | null = null
  let elTrail: HTMLElement | null = null
  let elCanvas: HTMLCanvasElement | null = null

  function draw() {
    if (!ctx || !w || !h) return
    ctx.clearRect(0, 0, w, h)
    const x = w * (0.74 + p.x * 0.12)
    const y = h * (0.44 + p.y * 0.16)
    const speed = Math.min(1, Math.sqrt(p.vx * p.vx + p.vy * p.vy) * 7)

    // 柔和暖红辉光（页面为白底，用普通叠加而非 screen）
    const g = ctx.createRadialGradient(x, y, 0, x, y, Math.max(w, h) * 0.42)
    g.addColorStop(0, `rgba(252,132,99,${(0.2 + speed * 0.1).toFixed(3)})`)
    g.addColorStop(0.34, 'rgba(240,140,110,0.10)')
    g.addColorStop(1, 'rgba(240,140,110,0)')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, w, h)

    // 指针附近的点阵扰动
    const step = 22
    for (let gx = w * 0.5; gx < w; gx += step) {
      for (let gy = 8; gy < h; gy += step) {
        const dx = gx - x
        const dy = gy - y
        const infl = Math.max(0, 1 - Math.sqrt(dx * dx + dy * dy) / 210)
        if (infl <= 0) continue
        ctx.fillStyle = `rgba(214,88,52,${(0.05 + infl * 0.16).toFixed(3)})`
        ctx.fillRect(gx + p.vx * infl * 2, gy + p.vy * infl * 2, 1.6, 1.6)
      }
    }
  }

  function resize() {
    if (!elCanvas) return
    const r = elCanvas.getBoundingClientRect()
    if (!r.width || !r.height) return
    const dpr = Math.min(window.devicePixelRatio || 1, 2)
    w = r.width
    h = r.height
    elCanvas.width = Math.round(w * dpr)
    elCanvas.height = Math.round(h * dpr)
    ctx = elCanvas.getContext('2d')
    if (ctx) ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    draw()
  }

  function settle() {
    const nx = (p.tx - p.x) * 0.11
    const ny = (p.ty - p.y) * 0.11
    p.vx = nx - p.vx * 0.76
    p.vy = ny - p.vy * 0.76
    p.x += nx
    p.y += ny
    const dist = Math.min(1, Math.sqrt(p.x * p.x + p.y * p.y) / 0.72)
    const ang = (Math.atan2(p.y, p.x) * 180) / Math.PI

    if (elOrb1) {
      elOrb1.style.cssText =
        `--orb-x:${(p.x * 18).toFixed(1)}px;--orb-y:${(p.y * 15).toFixed(1)}px;` +
        `--orb-rotate:${(ang * 0.08).toFixed(2)}deg;--orb-scale:${(1 + dist * 0.08).toFixed(3)};` +
        `--orb-radius:${(46 + p.x * 10).toFixed(1)}% ${(54 - p.y * 9).toFixed(1)}% ` +
        `${(60 + p.y * 11).toFixed(1)}% ${(40 - p.x * 8).toFixed(1)}% / ` +
        `${(45 + p.y * 9).toFixed(1)}% ${(38 - p.x * 7).toFixed(1)}% ` +
        `${(62 + p.x * 8).toFixed(1)}% ${(55 - p.y * 10).toFixed(1)}%`
    }
    if (elOrb2) {
      elOrb2.style.cssText =
        `--orb-x:${(p.x * -12).toFixed(1)}px;--orb-y:${(p.y * -10).toFixed(1)}px;` +
        `--orb-rotate:${(-ang * 0.12).toFixed(2)}deg;--orb-scale:${(1 + dist * 0.12).toFixed(3)};` +
        `--orb-radius:${(54 - p.y * 9).toFixed(1)}% ${(46 + p.y * 8).toFixed(1)}% ` +
        `${(41 - p.x * 9).toFixed(1)}% ${(59 + p.x * 8).toFixed(1)}% / ` +
        `${(58 - p.x * 8).toFixed(1)}% ${(44 + p.y * 8).toFixed(1)}% ` +
        `${(56 + p.x * 7).toFixed(1)}% ${(42 - p.y * 8).toFixed(1)}%`
    }
    const gx = `${(50 + p.x * 34).toFixed(1)}%`
    const gy = `${(50 + p.y * 32).toFixed(1)}%`
    if (elGlow) elGlow.style.cssText = `--glow-x:${gx};--glow-y:${gy}`
    if (elTrail) elTrail.style.cssText = `--glow-x:${gx};--glow-y:${gy}`
    draw()

    const settled =
      !p.live && Math.abs(p.x) < 0.002 && Math.abs(p.y) < 0.002 &&
      Math.abs(p.vx) < 0.002 && Math.abs(p.vy) < 0.002
    if (settled) {
      p.x = p.y = p.vx = p.vy = 0
      draw()
      raf = 0
      return
    }
    raf = requestAnimationFrame(settle)
  }

  function kick() {
    if (!raf) raf = requestAnimationFrame(settle)
  }

  function onMove(e: PointerEvent) {
    const host = root.value
    if (!host) return
    const r = host.getBoundingClientRect()
    if (!r.width || !r.height) return
    p.tx = ((e.clientX - r.left) / r.width - 0.5) * 2
    p.ty = ((e.clientY - r.top) / r.height - 0.5) * 2
    p.live = true
    elGlow?.classList.add('on')
    elTrail?.classList.add('on')
    kick()
  }

  function onLeave() {
    p.live = false
    elGlow?.classList.remove('on')
    elTrail?.classList.remove('on')
  }

  onMounted(() => {
    const host = root.value
    if (!host) return
    elCanvas = host.querySelector('.fx-canvas')
    elOrb1 = host.querySelector('.fx-orb-1')
    elOrb2 = host.querySelector('.fx-orb-2')
    elGlow = host.querySelector('.fx-glow')
    elTrail = host.querySelector('.fx-trail')
    resize()
    window.addEventListener('resize', resize, { passive: true })
    window.addEventListener('pointermove', onMove, { passive: true })
    window.addEventListener('pointerleave', onLeave, { passive: true })
  })

  onBeforeUnmount(() => {
    window.removeEventListener('resize', resize)
    window.removeEventListener('pointermove', onMove)
    window.removeEventListener('pointerleave', onLeave)
    if (raf) cancelAnimationFrame(raf)
    raf = 0
  })
}
