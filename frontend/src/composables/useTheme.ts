import { ref, watch } from 'vue'
import { canPlayThemeRipple, playThemeRipple, type RippleOrigin } from './themeRipple'

export type ThemeOption = '跟随系统' | '浅色' | '深色'

const STORAGE_KEY = 'campus-service-assistant-settings'
const DARK_QUERY = '(prefers-color-scheme: dark)'

function readStoredTheme(): ThemeOption {
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        if (!raw) return '跟随系统'
        const value = JSON.parse(raw)?.theme
        return value === '浅色' || value === '深色' ? value : '跟随系统'
    } catch {
        return '跟随系统'
    }
}

/**
 * 把主题写回本机设置。
 * 必须与已存的键合并：设置页保存的是 {displayName, school, campus, theme} 整个对象，
 * 直接覆盖会把个人资料冲掉。用 merge 之后，两边谁先写都不会互相破坏。
 */
function persistTheme(option: ThemeOption): void {
    try {
        const raw = localStorage.getItem(STORAGE_KEY)
        const saved = raw ? JSON.parse(raw) ?? {} : {}
        localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...saved, theme: option }))
    } catch {
        // 隐私模式 / 配额满：存不进去也不该影响切换本身
    }
}

const theme = ref<ThemeOption>(readStoredTheme())
const media = window.matchMedia(DARK_QUERY)

/** 选项最终落在明/暗哪一套：跟随系统时看系统偏好 */
function resolveDark(option: ThemeOption): boolean {
    return option === '深色' || (option === '跟随系统' && media.matches)
}

/**
 * 当前实际落在明还是暗（跟随系统时看系统偏好）。
 * 单独用一个 ref 而不是 computed：media.matches 不是响应式依赖，
 * 系统偏好变化时 computed 不会重算；而 paint() 每次都会跑，在这里同步最可靠。
 * 常驻栏的快捷切换按钮用它决定显示太阳还是月亮。
 */
const isDark = ref(resolveDark(theme.value))

/**
 * 把主题写进 <html data-theme>。
 * 幂等：值没变就不写 —— 重复写同一个值也会惊动 ParticleBackground 的 MutationObserver，
 * 让它白重建一次粒子引擎。
 */
function paint(option: ThemeOption): void {
    const next = resolveDark(option) ? 'dark' : 'light'
    isDark.value = next === 'dark'
    if (document.documentElement.dataset.theme !== next) document.documentElement.dataset.theme = next
}

// 系统主题变化只在「跟随系统」时生效；这种切换不做扩散（没有触点），直接落。
media.addEventListener('change', () => {
    if (theme.value === '跟随系统') paint(theme.value)
})

// 兜底：任何直接改 theme.value 的地方（含初始化）都能落到 DOM 上
watch(theme, paint, { immediate: true })

/**
 * 切换主题，并从 origin（触点按钮中心）张开一个圆扩散铺满整页。
 *
 * 三种走法：
 * - 选中的就是当前项 → 什么都不做，连 DOM 都不碰（需求：同主题不触发任何变化）
 * - 明暗没变（浅色 ↔ 跟随系统，而系统正好是浅色）→ 只更新选项，不值得为「没变的样子」播动画
 * - 其余 → 交给 View Transitions 做圆形扩散，主题在动画回调里落地
 */
export function setTheme(option: ThemeOption, origin?: RippleOrigin): void {
    if (option === theme.value) return

    // 主题必须等扩散动画的回调再落，否则旧快照拍到的是新配色，圆就没东西可铺了
    const commit = () => {
        theme.value = option
        paint(option)
        persistTheme(option)
    }

    if (!origin || resolveDark(option) === resolveDark(theme.value) || !canPlayThemeRipple()) {
        commit()
        return
    }

    playThemeRipple(commit, origin)
}

export function useTheme() {
    return { theme, isDark }
}
