import { onBeforeUnmount, onMounted, type Ref } from 'vue'

/**
 * 整个红色眼瞳随鼠标平移。
 *
 * 做法：底图不动；另一份同样的图被两枚**固定椭圆掩膜**裁出双眼区域，整层平移。
 * 掩膜略大于虹膜，因此整个眼瞳都在掩膜内滑动，露出的是眼白/下眼睑；
 * 掩膜边缘落在眼白与睫毛等均匀区域，滑动时边界不可见。
 *
 * 全部几何量由 assets/character.png（1024×954）的真实像素量得：
 *   左虹膜中心 (393.5, 598.5)、半径 ≈43.5；右虹膜中心 (613.5, 528)、半径 ≈50
 *   掩膜取 r58 / r66（略大于虹膜），最大位移 14×12px（位移后虹膜仍不出掩膜）
 */
const MID_X = 0.49170
const MID_Y = 0.59041
const MAX_X = 1.367 // 14px / 1024
const MAX_Y = 1.258 // 12px / 954

export function useEyeGaze(host: Ref<HTMLElement | null>) {
  let raf = 0
  let idle = false
  let t0 = 0
  let last: { x: number; y: number } | null = null
  const cur = { x: 0, y: 0 }
  const tgt = { x: 0, y: 0 }

  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)')
  const fine = window.matchMedia('(hover: hover) and (pointer: fine)')

  function apply() {
    const el = host.value
    if (!el) return
    el.style.setProperty('--gx', cur.x.toFixed(3) + '%')
    el.style.setProperty('--gy', cur.y.toFixed(3) + '%')
  }

  function loop(ts: number) {
    raf = 0
    if (idle) {
      // 触屏没有指针：让眼睛缓慢环绕，角色不至于变成一张静止图
      if (!t0) t0 = ts
      const a = (ts - t0) / 6200
      tgt.x = Math.cos(a) * MAX_X * 0.55
      tgt.y = Math.sin(a) * MAX_Y * 0.55
    }
    cur.x += (tgt.x - cur.x) * 0.15
    cur.y += (tgt.y - cur.y) * 0.15
    const settled = Math.abs(tgt.x - cur.x) < 0.003 && Math.abs(tgt.y - cur.y) < 0.003
    if (settled) {
      cur.x = tgt.x
      cur.y = tgt.y
    }
    apply()
    if (!settled || idle) raf = requestAnimationFrame(loop)
  }

  function kick() {
    if (!raf) raf = requestAnimationFrame(loop)
  }

  function aim(clientX: number, clientY: number) {
    const el = host.value
    if (!el) return
    const r = el.getBoundingClientRect()
    if (!r.width || !r.height) return
    let nx = (clientX - (r.left + r.width * MID_X)) / (r.width * 0.5)
    let ny = (clientY - (r.top + r.height * MID_Y)) / (r.height * 0.5)
    const m = Math.sqrt(nx * nx + ny * ny)
    if (m > 1) {
      nx /= m
      ny /= m // 限制在单位圆内，方向不变
    }
    tgt.x = nx * MAX_X
    tgt.y = ny * MAX_Y
    kick()
  }

  function onPointerMove(e: PointerEvent) {
    if (!fine.matches || idle) return
    last = { x: e.clientX, y: e.clientY }
    aim(e.clientX, e.clientY)
  }
  function reaim() {
    if (last && !idle) aim(last.x, last.y)
  }
  function syncMode() {
    idle = !fine.matches && !reduce.matches
    t0 = 0
    last = null
    if (!idle) {
      tgt.x = 0
      tgt.y = 0
    }
    kick()
  }

  onMounted(() => {
    window.addEventListener('pointermove', onPointerMove, { passive: true })
    window.addEventListener('resize', reaim, { passive: true })
    window.addEventListener('scroll', reaim, { passive: true })
    fine.addEventListener('change', syncMode)
    reduce.addEventListener('change', syncMode)
    syncMode()
  })

  onBeforeUnmount(() => {
    window.removeEventListener('pointermove', onPointerMove)
    window.removeEventListener('resize', reaim)
    window.removeEventListener('scroll', reaim)
    fine.removeEventListener('change', syncMode)
    reduce.removeEventListener('change', syncMode)
    if (raf) cancelAnimationFrame(raf)
    raf = 0
  })
}
