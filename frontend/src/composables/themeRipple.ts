/**
 * 主题切换的「圆形扩散」过渡（水波涟漪）。
 *
 * 走 View Transitions API：新旧主题各被拍成一张全屏快照，
 *   ::view-transition-new(root)  新主题 —— clip-path 的圆从触点向外张开
 *   ::view-transition-old(root)  旧主题 —— 原地不动，被圆慢慢盖住
 * 两层都是 fixed 快照，真实 DOM 只换颜色、不动布局，所以动画全程布局不变。
 * 样式全在 theme.css 的「主题切换：圆形扩散」一节，这里只负责算几何 + 开关。
 *
 * 为什么半径要自己算：`circle(150%)` 那类百分比只是「够用」的近似，
 * 需求要的是「触点 → 最远角落」的真实距离，所以这里按视口算准了再写进
 * --theme-ripple-radius，扩散圆和波峰环共用同一个值。
 *
 * 另外两层装饰（大波峰环、触点周围的水滴涟漪）的颜色只能由实元素提供 ——
 * 伪元素自身的绘制会被快照整块盖掉，所以这里还要负责让它们开始绘制（见 PAINT_CLASS）：
 *   .theme-ripple-veil  整屏纯色 → 被 mask 切成贴着水波前沿的一圈大波峰
 *   .theme-ripple-pond  触点周围几圈同心波 → 整体 scale 放大，比大圆跑得快
 */

export type RippleOrigin = { x: number; y: number }

/** 扩散期间挂在 <html> 上的类：theme.css 里所有 ::view-transition-* 规则都以它为前缀 */
const RIPPLE_CLASS = 'theme-rippling'

/**
 * 让「需要进快照的实元素」开始绘制：`.theme-ripple-veil` 变成一块纯色（大波峰的颜色），
 * `.theme-ripple-pond` 画出触点周围那几圈水滴涟漪。
 *
 * 为什么必须由实元素画：伪元素自身的 background/border 不会绘制，快照会整块盖住
 * 元素自身的绘制（见 theme.css 的说明）。
 *
 * 只在「新快照拍下之前」挂上、全程挂着：挂早了页面还没被旧快照盖住，会闪一下
 * （veil 是整屏纯色，闪起来最明显）；挂晚/摘早了新快照里就没有这两层颜色。
 * 扩散期间它们一直躺在两个 root 快照下面，所以自己不会被看见。
 */
const PAINT_CLASS = 'theme-rippling-paint'

type ViewTransitionLike = {
    finished: Promise<void>
}

type ViewTransitionDocument = Document & {
    startViewTransition?: (callback: () => void) => ViewTransitionLike
}

/** 连续切换时的序号：只让最后一次扩散负责收尾，避免前一次的清理打断后一次 */
let rippleSeq = 0

/** 浏览器支持 + 用户没有要求减弱动效，才值得扩散 */
export function canPlayThemeRipple(): boolean {
    const doc = document as ViewTransitionDocument
    return typeof doc.startViewTransition === 'function'
        && !window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * 从 origin 处张开一个圆铺满整页，圆到位的同时把主题换掉。
 *
 * @param commit 真正落主题的动作（同步改 <html data-theme>）。
 *               必须由动画在「新快照拍下之前」调用，否则旧快照会拍到新配色，圆就没得铺了。
 * @param origin 圆心（视口坐标），一般传触点按钮的中心。
 */
export function playThemeRipple(commit: () => void, origin: RippleOrigin): void {
    const doc = document as ViewTransitionDocument
    const startViewTransition = doc.startViewTransition
    if (!startViewTransition) {
        commit()
        return
    }

    const { innerWidth: width, innerHeight: height } = window
    // 最远角落 = 水平、垂直方向都最远的那个角，所以两个方向各取 max 再合成。
    // +8px 是安全余量，保证圆一定盖过角落（否则可能留下一线没被铺到的像素）。
    const radius = Math.hypot(
        Math.max(origin.x, width - origin.x),
        Math.max(origin.y, height - origin.y),
    ) + 8

    const root = document.documentElement
    const token = (rippleSeq += 1)
    root.style.setProperty('--theme-ripple-x', `${origin.x}px`)
    root.style.setProperty('--theme-ripple-y', `${origin.y}px`)
    root.style.setProperty('--theme-ripple-radius', `${radius}px`)
    root.classList.add(RIPPLE_CLASS)

    const transition = startViewTransition.call(doc, () => {
        // 两层的颜色都跟着新主题走，所以要等 commit 之后才挂（其实两者同帧生效）
        root.classList.add(PAINT_CLASS)
        commit()
    })

    // finished 在伪元素树被拆掉之后兑现，此时收尾不会有可见的一帧
    void transition.finished.finally(() => {
        if (token !== rippleSeq) return
        root.classList.remove(RIPPLE_CLASS, PAINT_CLASS)
        root.style.removeProperty('--theme-ripple-x')
        root.style.removeProperty('--theme-ripple-y')
        root.style.removeProperty('--theme-ripple-radius')
    })
}
