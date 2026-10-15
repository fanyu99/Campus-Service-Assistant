<script setup lang="ts">

import { computed, ref } from 'vue'
import { recentConversations } from '../data/home.mock'
import { useProfile, avatarInitial } from '../composables/useProfile'
import ThemeToggleButton from '../components/ThemeToggleButton.vue'

const { profile } = useProfile()
const avatarText = computed(() => avatarInitial(profile.value.displayName))

const activeFilter = ref('全部')
const query = ref('')
const records = recentConversations.map((item, index) => ({ ...item, status: index === 1 ? '待继续' : '已完成', detail: index === 1 ? '上次对话还可以继续查看办理条件' : '已查看过相关办理路径' }))
const filters = ['全部', '待继续', '已完成']
const visibleRecords = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return records.filter((item) => {
    const inFilter = activeFilter.value === '全部' || item.status === activeFilter.value
    const inQuery = !keyword || `${item.question} ${item.detail} ${item.tag}`.toLowerCase().includes(keyword)
    return inFilter && inQuery
  })
})
</script>

<template>
  <main class="main history-page" data-od-id="history-main">
    <header class="topbar" data-od-id="global-header"><nav class="crumb" aria-label="页面标题"><strong>最近记录</strong></nav><div class="top-actions"><ThemeToggleButton /><button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button"><svg class="i" aria-hidden="true"><use href="#i-bell"/></svg><span class="dot-badge"></span></button><span class="avatar" role="img" :aria-label="'当前用户：' + profile.displayName" data-od-id="profile-chip-top">{{ avatarText }}</span></div></header>
    <section class="history-content" data-od-id="history-content"><div class="history-head"><div class="history-title-block"><h1 data-od-id="history-heading">查找历史记录</h1><label class="history-search composer-shell" data-od-id="history-search"><svg class="i" aria-hidden="true"><use href="#i-search" /></svg><span class="sr-only">搜索历史记录</span><input v-model="query" type="search" placeholder="按问题或标签搜索" autocomplete="off" /><button v-if="query" type="button" class="clear-search" aria-label="清空" @click="query = ''">清空</button></label></div><nav class="history-filters" aria-label="记录筛选" data-od-id="history-filters"><button v-for="filter in filters" :key="filter" type="button" class="filter-tab" :class="{ 'is-active': activeFilter === filter }" :aria-pressed="activeFilter === filter" @click="activeFilter = filter">{{ filter }}</button></nav></div>
      <section class="history-list-wrap" aria-labelledby="history-heading" data-od-id="history-list"><div class="history-list-heading"><span>对话记录</span><span class="list-count">按时间排序</span></div><ul v-if="visibleRecords.length" class="history-list"><li v-for="item in visibleRecords" :key="item.id" class="history-item" :data-od-id="'history-item-' + item.id"><time class="record-time">{{ item.time }}</time><div class="record-body"><div class="record-title-line"><h2>{{ item.question }}</h2><span class="record-status" :class="{ 'is-pending': item.status === '待继续' }">{{ item.status }}</span></div><p>{{ item.detail }}<span class="record-tag">{{ item.tag }}</span></p></div><RouterLink class="record-link spark-button" :to="{ name: 'chat', query: { q: item.question } }" :aria-label="'继续咨询：' + item.question">继续咨询<svg class="i" aria-hidden="true"><use href="#i-chev"/></svg></RouterLink></li></ul><div v-else class="empty-state" data-od-id="history-empty"><h2>还没有咨询记录</h2><p>咨询过一次后，问题和办理进度会显示在这里。</p><RouterLink class="text-action spark-button" :to="{ name: 'chat' }">开始咨询</RouterLink></div></section>
    </section>
  </main>
</template>

<style scoped>
/* 同 HelpView：页面级滚动必须由 .main 自己承担，否则超出一屏的内容会被裁掉 */
.history-page{min-height:0;overflow-y:auto;overflow-x:hidden;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.history-content{position:relative;z-index:1;width:min(1020px,100%);margin:auto;padding:clamp(26px,5vh,70px) 0 clamp(30px,5vh,72px)}.history-title-block{display:grid;gap:18px;min-width:min(430px,100%)}.history-search{display:flex;align-items:center;gap:9px;min-height:46px;padding:0 12px}.history-search .i{width:16px;height:16px;color:var(--muted)}.history-search input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:var(--fg);font:400 13px/1.5 var(--font-body)}.history-search input::placeholder{color:var(--muted)}.clear-search{flex:0 0 auto;color:var(--muted);font-size:12px}.clear-search:hover{color:var(--fg)}.history-head{display:flex;align-items:flex-end;justify-content:space-between;gap:24px;padding:clamp(8px,3vh,40px) 0 30px}h1{margin:0;font-family:var(--font-display);font-size:clamp(32px,4.4vw,54px);line-height:1.28;font-weight:900;letter-spacing:-.025em}.history-filters{display:flex;gap:5px;padding-bottom:2px}.filter-tab{min-height:36px;padding:0 12px;border:1px solid transparent;border-radius:var(--control-radius-pill);color:var(--muted);font-size:12px;white-space:nowrap}.filter-tab:hover{border-color:var(--border);color:var(--fg)}.filter-tab.is-active{background:var(--fg);color:var(--page-bg)}.history-list-heading{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:0 0 13px;border-bottom:1px solid var(--border);color:var(--fg);font-size:13px;font-weight:550}.list-count{color:var(--muted);font-size:12px;font-weight:400;white-space:nowrap}.history-list{display:grid}.history-item{display:grid;grid-template-columns:100px minmax(0,1fr) auto;align-items:center;gap:22px;min-height:92px;padding:18px 0;border-bottom:1px solid var(--border);transition:background .16s ease}.history-item:hover{background:color-mix(in oklch,var(--row-hover) 55%,transparent)}.record-time{color:var(--muted);font-size:12px;white-space:nowrap}.record-body{min-width:0;user-select:text;-webkit-user-select:text}.record-title-line{display:flex;align-items:center;gap:10px;min-width:0}.record-title-line h2{min-width:0;margin:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px;font-weight:550;line-height:1.5}.record-status{flex:0 0 auto;padding:4px 7px;border-radius:6px;background:var(--surface);color:var(--muted);font-size:11px;white-space:nowrap}.record-status.is-pending{background:var(--accent-soft);color:var(--accent)}.record-body p{margin:5px 0 0;color:var(--muted);font-size:12px;line-height:1.55}.record-tag{margin-left:10px;color:var(--fg);white-space:nowrap}.record-tag::before{content:'·';margin-right:10px;color:var(--border)}.record-link{display:inline-flex;align-items:center;gap:5px;color:var(--fg);font-size:12px;font-weight:550;text-decoration:none;white-space:nowrap}.record-link:hover{color:var(--accent)}.record-link .i{width:13px;height:13px}.empty-state{padding:46px 0;border-bottom:1px solid var(--border)}.empty-state h2{margin:0;font-size:16px;font-weight:550}.empty-state p{margin:8px 0 16px;color:var(--muted);font-size:13px;line-height:1.7}.text-action{display:inline-flex;color:var(--fg);font-size:13px;font-weight:550;text-decoration:none;white-space:nowrap}.text-action:hover{color:var(--accent)}
@media (max-width:800px){.history-title-block{width:100%;min-width:0}.history-head{align-items:flex-start;flex-direction:column;gap:22px}.history-filters{width:100%;overflow-x:auto}.filter-tab{min-height:var(--control-h);flex:0 0 auto}.history-item{grid-template-columns:82px minmax(0,1fr);gap:12px}.record-link{grid-column:2;justify-self:start}}@media (max-width:700px){.history-page{min-height:auto;overflow:visible}.history-content{width:100%;padding:28px 0 40px}.history-head{padding-top:0}.history-list-heading{padding-bottom:11px}.history-item{grid-template-columns:1fr;gap:7px;min-height:0;padding:17px 0}.record-title-line{align-items:flex-start}.record-title-line h2{white-space:normal;overflow:visible}.record-link{grid-column:auto}.record-link,.text-action{min-height:var(--control-h)}}@media (prefers-reduced-motion:reduce){.history-item,.record-link,.filter-tab{transition:none}}
</style>









