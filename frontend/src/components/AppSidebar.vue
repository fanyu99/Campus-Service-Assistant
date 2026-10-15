<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useCharacterBubble } from '../composables/useCharacterBubble'
import { useProfile, avatarInitial } from '../composables/useProfile'

interface NavItem {
  name: string
  to: string
  icon: string
  label: string
}

const route = useRoute()
const { setHoverMessage, clearHoverMessage } = useCharacterBubble()

/* 侧栏身份信息原先写死「林同学 / 本科生 · 一校区」，与设置页脱节；
   改为消费 useProfile 的单一数据源。 */
const { profile } = useProfile()
const avatarText = computed(() => avatarInitial(profile.value.displayName))
const profileMeta = computed(() => [profile.value.school, profile.value.campus].filter(Boolean).join(' · '))

const primaryNav: NavItem[] = [
  { name: 'home', to: '/', icon: 'i-home', label: '首页' },
  { name: 'chat', to: '/chat', icon: 'i-chat', label: '我的对话' },
  { name: 'services', to: '/services', icon: 'i-list', label: '支持事项' },
  { name: 'history', to: '/history', icon: 'i-clock', label: '最近记录' },
]

const secondaryNav: NavItem[] = [
  { name: 'help', to: '/help', icon: 'i-help', label: '使用帮助' },
  { name: 'settings', to: '/settings', icon: 'i-sliders', label: '设置' },
]

function isActive(name: string) {
  return route.name === name
}

const navMessages: Record<string, string> = {
  home: '回首页找我吗？我就知道你会想我。',
  chat: '你要问我问题吗？',
  services: '校园事务，问我就对了。',
  history: '想看看我们之前聊过什么吗？',
  help: '遇到不会的就看这里，别害羞嘛。',
  settings: '要调整一下设置？我陪你。',
}

function showNavMessage(name: string) {
  setHoverMessage(navMessages[name] ?? '有什么问题尽管问我。')
}
</script>

<template>
  <aside class="sidebar" data-od-id="app-sidebar">
    <div class="brand" data-od-id="brand-lockup">
      <img class="brand-mark" src="/assets/brand-mark.png" alt="校园办事小秘书">
      <strong>校园办事小秘书</strong>
    </div>
    <nav class="primary-nav" aria-label="主导航">
      <router-link
        v-for="item in primaryNav"
        :key="item.name"
        :to="item.to"
        class="nav-item"
        :class="{ active: isActive(item.name) }"
        :data-od-id="`nav-${item.name}`"
        :data-tip="item.label"
        :aria-current="isActive(item.name) ? 'page' : undefined"
        @mouseenter="showNavMessage(item.name)"
        @mouseleave="clearHoverMessage"
        @focus="showNavMessage(item.name)"
        @blur="clearHoverMessage"
      >
        <svg class="i" aria-hidden="true"><use :href="`#${item.icon}`"/></svg><span>{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="sidebar-spacer"></div>
    <div class="side-status" data-od-id="kb-status"><span class="status-dot" aria-hidden="true"></span><span>办事指南已更新</span></div>

    <nav class="secondary-nav" aria-label="辅助导航">
      <router-link
        v-for="item in secondaryNav"
        :key="item.name"
        :to="item.to"
        class="nav-item"
        :class="{ active: isActive(item.name) }"
        :data-od-id="`nav-${item.name}`"
        :data-tip="item.label"
        :aria-current="isActive(item.name) ? 'page' : undefined"
        @mouseenter="showNavMessage(item.name)"
        @mouseleave="clearHoverMessage"
        @focus="showNavMessage(item.name)"
        @blur="clearHoverMessage"
      >
        <svg class="i" aria-hidden="true"><use :href="`#${item.icon}`"/></svg><span>{{ item.label }}</span>
      </router-link>
    </nav>
    <div class="profile" data-od-id="profile-chip">
      <span class="avatar" aria-hidden="true">{{ avatarText }}</span>
      <span class="profile-meta"><strong>{{ profile.displayName }}</strong><span>{{ profileMeta }}</span></span>
    </div>
    <div class="bar-actions">
      <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button-mobile"><svg class="i" aria-hidden="true"><use href="#i-bell"/></svg><span class="dot-badge"></span></button>
      <span class="avatar" role="img" :aria-label="'当前用户：' + profile.displayName">{{ avatarText }}</span>
    </div>
  </aside>
</template>

<style scoped>
.sidebar{position:relative;z-index:3;flex:0 0 200px;width:200px;display:flex;flex-direction:column;padding:22px 14px 16px}
.brand{display:flex;align-items:center;gap:10px;padding:0 6px 22px}
.brand-mark{position:relative;display:block;width:32px;height:32px;flex:0 0 auto;border-radius:50%;background:#fff;box-shadow:0 0 0 1px color-mix(in srgb,var(--accent) 45%,transparent),0 0 16px color-mix(in srgb,var(--accent) 38%,transparent),0 1px 3px rgba(80,30,10,.14);animation:brand-mark-glow 2.6s ease-in-out infinite}
.brand strong{font-family:var(--font-display);font-weight:900;font-size:15px;letter-spacing:-.01em;white-space:nowrap}
.primary-nav,.secondary-nav{display:grid;gap:3px}
@keyframes brand-mark-glow{0%,100%{filter:drop-shadow(0 0 0 color-mix(in srgb,var(--accent) 0%,transparent));transform:scale(1)}50%{filter:drop-shadow(0 0 9px color-mix(in srgb,var(--accent) 72%,transparent));transform:scale(1.04)}}
.secondary-nav{padding-top:12px;border-top:1px solid var(--border);margin-top:12px}
.nav-item{position:relative;display:flex;align-items:center;gap:10px;width:100%;min-height:40px;padding:0 10px;border-radius:11px;
  color:var(--muted);font-size:13.5px;text-align:left;text-decoration:none;transition:background .16s ease,color .16s ease,transform .16s ease}
.nav-item .i{width:16px;height:16px}
.nav-item > span{white-space:nowrap}
.nav-item:hover{background:var(--row-hover);color:var(--fg);transform:translateX(2px)}
.nav-item.active{background:var(--accent-soft);color:var(--accent);font-weight:500}
.nav-item.active:hover{color:var(--accent)}
/* tooltip：悬停或键盘聚焦时显示对应页面名 */
.nav-item::before,.nav-item::after{position:absolute;opacity:0;pointer-events:none;z-index:20;
  transition:opacity .22s ease,transform .22s cubic-bezier(.2,.8,.2,1)}
.nav-item::before{content:'';left:calc(100% + 6px);top:calc(50% - 4px);width:9px;height:9px;
  border-bottom:1px solid var(--tooltip-border);border-left:1px solid var(--tooltip-border);background:var(--tooltip-bg);
  transform:translateX(-5px) rotate(45deg)}
.nav-item::after{content:attr(data-tip);left:calc(100% + 10px);top:50%;transform:translate(-5px,-50%) scale(.96);transform-origin:left center;
  padding:9px 12px;border:1px solid var(--tooltip-border);border-radius:10px 14px;background:var(--tooltip-bg);box-shadow:var(--tooltip-shadow);
  color:var(--tooltip-text);font-size:12px;font-weight:500;line-height:1.2;letter-spacing:.01em;white-space:nowrap}
.nav-item:hover::before,.nav-item:focus-visible::before{opacity:1;transform:translateX(0) rotate(45deg)}
.nav-item:hover::after,.nav-item:focus-visible::after{opacity:1;transform:translate(0,-50%) scale(1)}
@media (hover:none){.nav-item::before,.nav-item::after{display:none}}
.sidebar-spacer{flex:1;min-height:16px}
.side-status{display:flex;align-items:center;gap:8px;padding:9px 10px;border-radius:11px;background:var(--row-hover);color:var(--muted);font-size:11.5px;line-height:1.45}
.status-dot{width:6px;height:6px;flex:0 0 auto;border-radius:50%;background:oklch(60% .13 148)}

.profile{display:flex;align-items:center;gap:9px;margin-top:14px;padding:6px 6px 0}
.profile-meta{min-width:0}
.profile-meta strong{display:block;font-size:12.5px;font-weight:500}
.profile-meta span{display:block;margin-top:2px;color:var(--muted);font-size:11px}
.bar-actions{display:none}

/* ── 窄桌面 ────────────────────────────────────────────────────────────── */
@media (max-width:1080px){
  .sidebar{flex-basis:74px;width:74px;padding-inline:10px;align-items:center}
  .brand{padding:0 0 20px;justify-content:center}
  .brand strong{position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  .nav-item{justify-content:center;gap:0;padding:0}
  .nav-item > span{position:absolute;width:1px;height:1px;margin:-1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
  .side-status,.profile-meta{display:none}
  .profile{justify-content:center}
}
@media (max-height:600px) and (min-width:701px){
  .sidebar{overflow-y:auto;scrollbar-width:thin}
  .sidebar-spacer{min-height:8px}
}

/* ── 移动端（≤700px）────────────────────────────────────────────────── */
@media (max-width:700px){
  .sidebar{flex:none;width:100%;flex-direction:row;align-items:center;gap:4px;padding:10px 18px;
    position:sticky;top:0;z-index:6;background:var(--page-bg)}
  .brand{padding:0;margin-right:auto;min-width:0}
  .brand strong{position:static;width:auto;height:auto;margin:0;overflow:hidden;clip:auto;display:block;font-size:14px;
    min-width:0;white-space:nowrap;text-overflow:ellipsis}
  .brand-mark{width:34px;height:34px}
  .sidebar-spacer,.side-status,.profile{display:none}
  .primary-nav,.secondary-nav{display:flex;gap:2px;padding:0;margin:0;border:0}
  .secondary-nav{border-left:1px solid var(--border);padding-left:6px;margin-left:2px}
  .nav-item{width:44px;height:44px;min-height:44px;justify-content:center;padding:0;border-radius:12px}
  .nav-item .i{width:19px;height:19px}
  .nav-item::before{left:calc(50% - 4px);top:calc(100% + 4px);transform:translateY(5px) rotate(45deg)}
  .nav-item::after{left:50%;top:calc(100% + 8px);transform:translate(-50%,5px) scale(.96);transform-origin:center top}
  .nav-item:hover::before,.nav-item:focus-visible::before{transform:translateY(0) rotate(45deg)}
  .nav-item:hover::after,.nav-item:focus-visible::after{transform:translate(-50%,0) scale(1)}
  .bar-actions{display:flex;align-items:center;gap:2px;padding-left:6px;border-left:1px solid var(--border)}
  .bar-actions .icon-btn{width:44px;height:44px}
  .bar-actions .avatar{display:none}
}
@media (max-width:380px){.brand strong{display:none}}
</style>


