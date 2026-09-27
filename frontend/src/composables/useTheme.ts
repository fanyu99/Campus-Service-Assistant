import { ref, watch } from 'vue'

export type ThemeOption = '跟随系统' | '浅色' | '深色'

const STORAGE_KEY = 'campus-service-assistant-settings'

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

const theme = ref<ThemeOption>(readStoredTheme())
const media = window.matchMedia('(prefers-color-scheme: dark)')

function applyTheme() {
    const dark = theme.value === '深色' || (theme.value === '跟随系统' && media.matches)
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
}

media.addEventListener('change', applyTheme)
watch(theme, applyTheme, { immediate: true })

export function useTheme() {
    return { theme }
}