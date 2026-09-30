<script setup lang="ts">

import { computed, ref } from 'vue'
import { serviceItems } from '../data/home.mock'

const query = ref('')
const activeCategory = ref('全部')

const categories = ['全部', '证件与校园卡', '宿舍与后勤', '请假与学业', '奖助与缴费', '网络与账号']
const serviceGroups: Record<string, string> = {
  'student-card': '证件与校园卡', 'campus-card': '证件与校园卡', repair: '宿舍与后勤', leave: '请假与学业', scholarship: '奖助与缴费', network: '网络与账号',
}
const extendedServices = [
  ...serviceItems,
  { id: 'scholarship', title: '奖助学金申请', description: '申请条件、材料与提交时间', category: '学业', icon: '¥', tone: 'orange', prompt: '申请奖助学金需要准备哪些材料？' },
  { id: 'network', title: '校园网与账号', description: '网络开通、密码与账号问题', category: '账号', icon: '@', tone: 'blue', prompt: '校园网账号无法登录应该怎么处理？' },
]
const visibleServices = computed(() => {
  const normalized = query.value.trim().toLowerCase()
  return extendedServices.filter((item) => {
    const inCategory = activeCategory.value === '全部' || serviceGroups[item.id] === activeCategory.value
    const inQuery = !normalized || [item.title, item.description, item.category].join(' ').toLowerCase().includes(normalized)
    return inCategory && inQuery
  })
})
function dismissNotice(id: string) {
  const el = document.querySelector<HTMLElement>('[data-od-id="' + id + '"]')
  const dot = el?.querySelector('.dot-badge')
  if (dot) dot.remove()
  el?.setAttribute('aria-label', '通知（无未读）')
  el?.setAttribute('data-tip', '通知（无未读）')
}

</script>

<template>
  <main class="main services-page" data-od-id="services-main">
    <header class="topbar" data-od-id="global-header">
      <nav class="crumb" aria-label="页面标题"><strong>支持事项</strong></nav>
      <div class="top-actions"><button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button"><svg class="i" aria-hidden="true"><use href="#i-bell"/></svg><span class="dot-badge"></span></button><span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="profile-chip-top">林</span></div>
    </header>
    <section class="services-content" data-od-id="services-content">
      <div class="services-intro" data-od-id="services-intro">
        <h1 data-od-id="services-heading">支持事项</h1>
        <label class="search-field composer-shell" data-od-id="services-search"><span class="sr-only">搜索支持事项</span><input v-model="query" type="search" placeholder="搜索事项名称或关键词" autocomplete="off" /><button v-if="query" type="button" class="clear-search" aria-label="清空搜索" @click="query = ''">清除</button></label>
        <div class="category-filter" role="list" aria-label="事项分类" data-od-id="service-categories"><button v-for="category in categories" :key="category" type="button" class="category-tab" :class="{ 'is-active': activeCategory === category }" :aria-pressed="activeCategory === category" @click="activeCategory = category">{{ category }}</button></div>
      </div>
      <section class="service-list-wrap" aria-labelledby="services-heading" data-od-id="service-list">
        <div class="list-heading"><span>常用办理入口</span><span class="list-count">{{ visibleServices.length }} 项</span></div>
        <ul v-if="visibleServices.length" class="service-list"><li v-for="item in visibleServices" :key="item.id" class="service-item" :data-od-id="'service-item-' + item.id"><span class="service-mark" aria-hidden="true">{{ item.icon }}</span><div class="service-copy"><h2>{{ item.title }}</h2><p>{{ item.description }}</p></div><span class="service-category">{{ item.category }}</span><RouterLink class="service-link spark-button" :to="{ name: 'chat', query: { q: item.prompt } }" :aria-label="'咨询' + item.title">开始咨询<svg class="i" aria-hidden="true"><use href="#i-chev"/></svg></RouterLink></li></ul>
        <div v-else class="empty-state" data-od-id="services-empty"><h2>没有找到匹配事项</h2><p>试试更短的关键词，或切换到“全部”查看所有支持事项。</p><button type="button" class="text-action spark-button" @click="query = ''; activeCategory = '全部'">重置筛选</button></div>
      </section>
    </section>
  </main>
</template>

<style scoped>
/* 同 HelpView：页面级滚动必须由 .main 自己承担，否则超出一屏的内容会被裁掉 */
.services-page{min-height:0;overflow-y:auto;overflow-x:hidden;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.services-content{position:relative;z-index:1;display:grid;grid-template-columns:minmax(250px,.82fr) minmax(0,1.35fr);gap:clamp(34px,6vw,92px);width:min(1080px,100%);margin:auto;padding:clamp(26px,5vh,70px) 0 clamp(30px,5vh,72px)}.services-intro{align-self:start;padding-top:clamp(8px,3vh,42px)}.eyebrow{margin:0 0 14px;color:var(--accent);font-size:11px;letter-spacing:.08em;font-weight:600}h1{margin:0;font-family:var(--font-display);font-size:clamp(32px,4.4vw,54px);line-height:1.28;font-weight:900;letter-spacing:-.025em}.search-field{display:flex;align-items:center;gap:9px;margin-top:26px;min-height:46px;padding:0 12px}.search-field .i{width:16px;height:16px;color:var(--muted)}.search-field input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:var(--fg);font:400 13px/1.5 var(--font-body)}.search-field input::placeholder{color:var(--muted)}.clear-search{flex:0 0 auto;color:var(--muted);font-size:12px;white-space:nowrap}.clear-search:hover{color:var(--fg)}.category-filter{display:flex;flex-wrap:wrap;gap:7px;margin-top:14px}.category-tab{min-height:34px;padding:0 11px;border:1px solid var(--border);border-radius:999px;background:transparent;color:var(--muted);font-size:12px;white-space:nowrap;transition:background .16s ease,color .16s ease,border-color .16s ease}.category-tab:hover{border-color:var(--fg);color:var(--fg)}.category-tab.is-active{border-color:var(--fg);background:var(--fg);color:var(--page-bg)}.service-list-wrap{min-width:0;padding-top:clamp(8px,3vh,40px)}.list-heading{display:flex;align-items:center;justify-content:space-between;gap:14px;padding-bottom:13px;border-bottom:1px solid var(--border);color:var(--fg);font-size:13px;font-weight:550}.list-count{color:var(--muted);font-size:12px;font-weight:400;white-space:nowrap}.service-list{display:grid}.service-item{display:grid;grid-template-columns:38px minmax(0,1fr) auto auto;align-items:center;gap:13px;min-height:84px;padding:15px 0;border-bottom:1px solid var(--border);transition:background .16s ease}.service-item:hover{background:color-mix(in oklch,var(--row-hover) 55%,transparent)}.service-mark{display:grid;place-items:center;width:34px;height:34px;border:1px solid var(--border);border-radius:10px;background:var(--surface);color:var(--accent);font-size:14px;font-weight:600}.service-copy{min-width:0}.service-copy h2{margin:0;font-size:14px;font-weight:550;line-height:1.45}.service-copy p{margin:4px 0 0;color:var(--muted);font-size:12px;line-height:1.5}.service-category{color:var(--muted);font-size:11px;white-space:nowrap}.service-link{display:inline-flex;align-items:center;gap:5px;color:var(--fg);font-size:12px;font-weight:550;text-decoration:none;white-space:nowrap}.service-link:hover{color:var(--accent)}.service-link .i{width:13px;height:13px}.empty-state{padding:46px 0;border-bottom:1px solid var(--border)}.empty-state h2{margin:0;font-size:16px;font-weight:550}.empty-state p{margin:8px 0 16px;color:var(--muted);font-size:13px;line-height:1.7}.text-action{padding:0;color:var(--fg);font-size:13px;font-weight:550;white-space:nowrap}.text-action:hover{color:var(--accent)}
@media (max-width:900px){.services-content{grid-template-columns:minmax(220px,.7fr) minmax(0,1.3fr);gap:30px}.service-item{grid-template-columns:34px minmax(0,1fr) auto}.service-category{display:none}}@media (max-width:700px){.services-page{min-height:auto;overflow:visible}.services-content{display:block;width:100%;padding:28px 0 40px}.services-intro{padding-top:0}.service-list-wrap{padding-top:42px}.service-item{grid-template-columns:34px minmax(0,1fr) auto;gap:10px;min-height:78px}.category-filter{overflow-x:auto;flex-wrap:nowrap;padding-bottom:3px}.category-tab{flex:0 0 auto;min-height:40px}}@media (prefers-reduced-motion:reduce){.service-item,.service-link,.category-tab{transition:none}}
</style>












