<script setup lang="ts">

import { computed, ref, useTemplateRef } from 'vue'
import AppSelect from '../components/AppSelect.vue'
import ThemeToggleButton from '../components/ThemeToggleButton.vue'
import { setTheme, useTheme, type ThemeOption } from '../composables/useTheme'
import { useProfile, avatarInitial, clearLocalData as clearStoredData } from '../composables/useProfile'

const noticeRead = ref(false)
const saved = ref(false)

/* 资料统一走 useProfile：写入即持久化，并会与 useTheme 的 theme 字段 merge。
   用带 setter 的 computed 接 v-model，避免再维护一份本地 ref + watch 同步。 */
const { profile, setProfile } = useProfile()
const displayName = computed({
  get: () => profile.value.displayName,
  set: (value: string) => setProfile({ displayName: value }),
})
const school = computed({
  get: () => profile.value.school,
  set: (value: string) => setProfile({ school: value }),
})
const campus = computed({
  get: () => profile.value.campus,
  set: (value: string) => setProfile({ campus: value }),
})
const avatarText = computed(() => avatarInitial(profile.value.displayName))

const { theme } = useTheme()
const themeOptions: readonly ThemeOption[] = ['跟随系统', '浅色', '深色']
const themeSelect = useTemplateRef<{ triggerEl: HTMLButtonElement | null }>('themeSelect')

/**
 * 主题不能直接 v-model 到 theme 上：切换要从触点按钮张开一个圆扩散铺满整页，
 * 所以先量出按钮中心当圆心，再交给 setTheme（见 composables/themeRipple.ts）。
 */
function onThemeChange(next: ThemeOption) {
  const rect = themeSelect.value?.triggerEl?.getBoundingClientRect()
  setTheme(next, rect ? { x: rect.left + rect.width / 2, y: rect.top + rect.height / 2 } : undefined)
}

function dismissNotice() {
  noticeRead.value = true
}

function saveProfile() {
  saved.value = true
  window.setTimeout(() => { saved.value = false }, 1800)
}

function clearLocalData() {
  /* 同时清掉首页草稿（原实现只删了设置键，草稿会残留） */
  clearStoredData()
  saved.value = true
  window.setTimeout(() => { saved.value = false }, 1800)
}

</script>

<template>
  <main class="main settings-page" data-od-id="settings-main">
    <header class="topbar" data-od-id="settings-header">
      <nav class="crumb" aria-label="页面标题"><strong>设置</strong></nav>
      <div class="top-actions"><ThemeToggleButton /><button type="button" class="icon-btn" :aria-label="noticeRead ? '通知（无未读）' : '通知'" :data-tip="noticeRead ? '通知（无未读）' : '通知'" data-od-id="settings-notification-button" @click="dismissNotice"><svg class="i" aria-hidden="true"><use href="#i-bell" /></svg><span v-if="!noticeRead" class="dot-badge" /></button><span class="avatar" role="img" :aria-label="'当前用户：' + profile.displayName" data-od-id="settings-profile-chip">{{ avatarText }}</span></div>
    </header>

    <section class="settings-content" data-od-id="settings-content">
      <div class="settings-head"><h1 data-od-id="settings-heading">设置</h1></div>

      <div class="settings-layout">
        <section class="settings-section profile-section" data-od-id="profile-settings"><div class="section-heading"><div><h2>个人资料</h2></div><span class="profile-mark" aria-hidden="true">{{ avatarText }}</span></div><div class="profile-grid"><label class="field"><span>显示名称</span><span class="composer-shell"><input v-model="displayName" type="text" autocomplete="name" /></span></label><label class="field"><span>学校</span><span class="composer-shell"><input v-model="school" type="text" autocomplete="organization" /></span></label><label class="field"><span>校区</span><span class="composer-shell"><input v-model="campus" type="text" /></span></label></div></section>

        <section class="settings-section" data-od-id="appearance-settings"><div class="section-heading"><div><h2>页面外观</h2></div></div><div class="setting-row"><div><strong>主题</strong></div><AppSelect ref="themeSelect" :model-value="theme" :options="themeOptions" label="选择主题" class="select-shell" data-od-id="theme-select" @update:model-value="onThemeChange" /></div></section>

        <section class="settings-section data-section" data-od-id="data-settings"><div class="section-heading"><div><h2>数据管理</h2></div></div><div class="data-actions"><button type="button" class="secondary-button spark-button" data-od-id="save-settings-button" @click="saveProfile">保存修改</button><button type="button" class="text-button" data-od-id="clear-settings-button" @click="clearLocalData">清除本机保存的设置</button></div><p v-if="saved" class="save-status" aria-live="polite">已保存</p></section>
      </div>
    </section>
  </main>
</template>

<style scoped>
.settings-page{min-height:0;overflow-y:auto;overflow-x:hidden;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.settings-content{position:relative;z-index:1;width:min(900px,100%);margin:auto;padding:clamp(26px,5vh,70px) 0 clamp(30px,5vh,72px)}.settings-head{padding:clamp(8px,3vh,40px) 0 30px}.settings-head h1{margin:0;font-family:var(--font-display);font-size:clamp(32px,4.4vw,54px);line-height:1.3;font-weight:900;letter-spacing:-.025em}.intro-copy{max-width:48ch;margin:16px 0 0;color:var(--muted);font-size:14px;line-height:1.8}.settings-layout{display:grid;gap:14px}.settings-section{padding:22px 0;border-top:1px solid var(--border)}.section-heading{display:flex;align-items:flex-start;justify-content:space-between;gap:18px}.section-heading h2{margin:0;font-size:16px;font-weight:650;line-height:1.45}.section-heading p{margin:5px 0 0;color:var(--muted);font-size:12px;line-height:1.6}.profile-mark{display:grid;place-items:center;width:42px;height:42px;border-radius:13px;background:var(--accent);color:var(--page-bg);font-size:15px;font-weight:650}.profile-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px;margin-top:20px}.field{display:grid;gap:7px;color:var(--fg);font-size:12px;font-weight:550}.field .composer-shell{display:block;width:100%;min-height:44px}.field input{display:block;width:100%;min-height:42px;padding:0 12px;border:0;border-radius:inherit;background:transparent;color:var(--fg);font:400 13px/1.5 var(--font-body);outline:0}.setting-row .select-shell{flex:0 0 auto;width:150px}.setting-row{display:flex;align-items:center;justify-content:space-between;gap:18px;min-height:66px;padding:14px 0;border-bottom:1px solid var(--border)}.setting-row>div{display:grid;gap:4px;min-width:0}.setting-row strong{font-size:13px;font-weight:550}.setting-row span{color:var(--muted);font-size:12px;line-height:1.5}.data-actions{display:flex;align-items:center;gap:12px;margin-top:20px}.secondary-button{min-height:42px;padding:0 16px;border:1px solid var(--fg);border-radius:11px;background:var(--fg);color:var(--page-bg);font-size:13px;font-weight:550;white-space:nowrap}.secondary-button:hover{background:var(--accent-hover)}.text-button{min-height:42px;padding:0 3px;color:var(--muted);font-size:12px;white-space:nowrap}.text-button:hover{color:var(--danger)}.save-status{margin:13px 0 0;color:var(--muted);font-size:12px}.settings-section[data-od-id="appearance-settings"] .setting-row{border-bottom:0}.data-section{padding-bottom:0}
@media (max-width:700px){.settings-page{min-height:auto;overflow:visible}.settings-content{width:100%;padding:28px 0 40px}.settings-head{padding-top:0}.profile-grid{grid-template-columns:1fr}.setting-row{min-height:70px}.setting-row .select-shell{width:132px}.data-actions{align-items:flex-start;flex-direction:column;gap:6px}.secondary-button,.text-button{min-height:44px}.settings-section{padding:20px 0}}
@media (prefers-reduced-motion:reduce){.secondary-button,.composer-shell,.field input{transition:none;animation:none}}
</style>








