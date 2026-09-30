<script setup lang="ts">

import { computed, ref } from 'vue'
import AnimatedButton from '../components/AnimatedButton.vue'

const query = ref('')
const activeCategory = ref('全部')
const openId = ref('account')
const noticeRead = ref(false)

const categories = ['全部', '开始使用', '咨询与记录', '账号与设置']
const faqs = [
  { id: 'account', category: '开始使用', question: '如何开始一次校园事务咨询？', answer: '进入“我的对话”，在输入框中描述你的问题，也可以先从“支持事项”选择具体事务。建议补充院系、校区或办理时间，助手会更容易判断办理路径。' },
  { id: 'service', category: '开始使用', question: '找不到对应的支持事项怎么办？', answer: '直接输入你遇到的问题即可。系统会先根据关键词匹配相近事项，再引导你确认办理条件、所需材料和办理入口。' },
  { id: 'record', category: '咨询与记录', question: '最近记录会保存哪些内容？', answer: '最近记录会保留你的咨询主题和最近一次对话状态，方便你继续查看。当前原型使用本地演示数据，后续可接入校园服务知识库。' },
  { id: 'continue', category: '咨询与记录', question: '可以继续之前的咨询吗？', answer: '可以。在“最近记录”中选择一条记录，点击“继续咨询”即可回到对话页面，并带入原来的问题。' },
  { id: 'notice', category: '账号与设置', question: '如何切换深色模式？', answer: '进入“设置”，在页面外观的主题中选择“深色”。选择“跟随系统”时，页面会自动匹配系统的深浅色偏好。' },
  { id: 'privacy', category: '账号与设置', question: '我的咨询内容会被公开吗？', answer: '不会。咨询内容只用于当前账户下的服务体验和后续对话衔接。正式版本上线前还会补充更完整的隐私说明与数据管理入口。' },
]

const visibleFaqs = computed(() => {
  const keyword = query.value.trim().toLowerCase()
  return faqs.filter((item) => {
    const inCategory = activeCategory.value === '全部' || item.category === activeCategory.value
    const inQuery = !keyword || `${item.question} ${item.answer} ${item.category}`.toLowerCase().includes(keyword)
    return inCategory && inQuery
  })
})

function dismissNotice() {
  noticeRead.value = true
}

</script>

<template>
  <main class="main help-page" data-od-id="help-main">
    <header class="topbar" data-od-id="help-header">
      <nav class="crumb" aria-label="页面标题"><strong>使用帮助</strong></nav>
      <div class="top-actions"><button type="button" class="icon-btn" :aria-label="noticeRead ? '通知（无未读）' : '通知'" :data-tip="noticeRead ? '通知（无未读）' : '通知'" data-od-id="help-notification-button" @click="dismissNotice"><svg class="i" aria-hidden="true"><use href="#i-bell" /></svg><span v-if="!noticeRead" class="dot-badge" /></button><span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="help-profile-chip">林</span></div>
    </header>

    <section class="help-content" data-od-id="help-content">
      <div class="help-intro" data-od-id="help-intro">
        <h1 data-od-id="help-heading">使用帮助</h1>

        <label class="help-search composer-shell" data-od-id="help-search"><svg class="i" aria-hidden="true"><use href="#i-search" /></svg><span class="sr-only">搜索帮助内容</span><input v-model="query" type="search" placeholder="搜索问题或关键词" autocomplete="off" /><button v-if="query" type="button" class="clear-search" aria-label="清空搜索" @click="query = ''">清除</button></label>
        <div class="help-categories" role="list" aria-label="帮助分类" data-od-id="help-categories"><button v-for="category in categories" :key="category" type="button" class="category-tab" :class="{ 'is-active': activeCategory === category }" :aria-pressed="activeCategory === category" @click="activeCategory = category">{{ category }}</button></div>
      </div>

      <section class="faq-section" aria-labelledby="help-heading" data-od-id="help-faq-section">
        <div class="section-heading"><span>常见问题</span><span class="result-count">{{ visibleFaqs.length }} 条结果</span></div>
        <div v-if="visibleFaqs.length" class="faq-list">
          <article v-for="item in visibleFaqs" :key="item.id" class="faq-item" :class="{ 'is-open': openId === item.id }" :data-od-id="'faq-' + item.id">
            <button type="button" class="faq-question" :aria-expanded="openId === item.id" @click="openId = openId === item.id ? '' : item.id"><span>{{ item.question }}</span><svg class="i" aria-hidden="true"><use href="#i-chev" /></svg></button>
            <p v-if="openId === item.id" class="faq-answer">{{ item.answer }}</p>
          </article>
        </div>
        <div v-else class="empty-state" data-od-id="help-empty"><h2>没有找到相关问题</h2><p>换一个关键词试试，或直接进入对话描述你的情况。</p><RouterLink class="text-action spark-button" :to="{ name: 'chat' }">开始咨询<svg class="i" aria-hidden="true"><use href="#i-chev" /></svg></RouterLink></div>
      </section>

      <aside class="help-contact" data-od-id="help-contact"><div><p class="contact-label">还需要帮助？</p><h2>直接描述你的问题</h2><p>如果帮助内容没有覆盖你的情况，可以让助手根据具体场景继续判断。</p></div><AnimatedButton :to="{ name: 'chat' }" data-od-id="help-contact-link">进入我的对话</AnimatedButton></aside>
    </section>
  </main>
</template>

<style scoped>
/* .main 在 .app-shell（height:100vh + overflow:hidden）里被钉死高度，
   所以「页面级滚动」必须由 .main 自己承担：overflow-y:auto 建立滚动容器，
   否则内容超过一屏会被直接裁掉、滚轮和键盘都够不到（FAQ 变多或窗口变矮时就会踩到）。
   与 SettingsView 的 .settings-page 保持同一写法。 */
.help-page{min-height:0;overflow-y:auto;overflow-x:hidden;scrollbar-width:thin;scrollbar-color:var(--border) transparent}
.help-content{position:relative;z-index:1;width:min(1020px,100%);margin:auto;padding:clamp(26px,5vh,70px) 0 clamp(30px,5vh,72px)}.help-intro{max-width:680px;padding:clamp(8px,3vh,40px) 0 26px}.eyebrow{margin:0 0 14px;color:var(--accent);font-size:11px;letter-spacing:.08em;font-weight:600}.help-intro h1{margin:0;font-family:var(--font-display);font-size:clamp(32px,4.4vw,54px);line-height:1.3;font-weight:900;letter-spacing:-.025em}.help-search{display:flex;align-items:center;gap:9px;margin-top:25px;min-height:48px;padding:0 13px}.help-search .i{width:16px;height:16px;color:var(--muted)}.help-search input{min-width:0;flex:1;border:0;outline:0;background:transparent;color:var(--fg);font:400 13px/1.5 var(--font-body)}.help-search input::placeholder{color:var(--muted)}.clear-search{flex:0 0 auto;color:var(--muted);font-size:12px;white-space:nowrap}.clear-search:hover{color:var(--fg)}.help-categories{display:flex;flex-wrap:wrap;gap:7px;margin-top:14px}.category-tab{min-height:36px;padding:0 12px;border:1px solid var(--border);border-radius:999px;background:transparent;color:var(--muted);font-size:12px;white-space:nowrap;transition:background .16s ease,color .16s ease,border-color .16s ease}.category-tab:hover{border-color:var(--fg);color:var(--fg)}.category-tab.is-active{border-color:var(--fg);background:var(--fg);color:var(--page-bg)}
.faq-section{max-width:860px}.section-heading{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:0 0 13px;border-bottom:1px solid var(--border);color:var(--fg);font-size:13px;font-weight:550}.result-count{color:var(--muted);font-size:12px;font-weight:400;white-space:nowrap}.faq-list{display:grid}.faq-item{border-bottom:1px solid var(--border)}.faq-question{display:flex;align-items:center;justify-content:space-between;gap:16px;width:100%;min-height:64px;padding:0;text-align:left;color:var(--fg);font-size:14px;font-weight:550;white-space:nowrap}.faq-question .i{flex:0 0 auto;width:15px;height:15px;transform:rotate(90deg);transition:transform .18s ease}.faq-item.is-open .faq-question .i{transform:rotate(-90deg)}.faq-answer{max-width:72ch;margin:0;padding:0 32px 18px 0;color:var(--muted);font-size:13px;line-height:1.8;user-select:text;-webkit-user-select:text}.empty-state{padding:44px 0;border-bottom:1px solid var(--border)}.empty-state h2{margin:0;font-size:16px;font-weight:550}.empty-state p{margin:8px 0 16px;color:var(--muted);font-size:13px;line-height:1.7}.text-action{display:inline-flex;align-items:center;gap:6px;color:var(--fg);font-size:13px;font-weight:550;text-decoration:none;white-space:nowrap}.text-action:hover{color:var(--accent)}.text-action .i{width:14px;height:14px}.help-contact{display:flex;align-items:center;justify-content:space-between;gap:22px;margin-top:40px;padding:24px 26px;border:1px solid var(--border);border-radius:18px;background:color-mix(in oklch,var(--surface) 78%,transparent)}.contact-label{margin:0 0 8px;color:var(--accent);font-size:11px;font-weight:600;letter-spacing:.06em}.help-contact h2{margin:0;font-family:var(--font-display);font-size:20px;font-weight:800;line-height:1.35}.help-contact p:last-child{max-width:48ch;margin:7px 0 0;color:var(--muted);font-size:12px;line-height:1.7}
@media (max-width:700px){.help-page{min-height:auto;overflow:visible}.help-content{width:100%;padding:28px 0 40px}.help-intro{padding-top:0}.help-categories{overflow-x:auto;flex-wrap:nowrap;padding-bottom:3px}.category-tab{flex:0 0 auto;min-height:40px}.faq-question{min-height:60px;white-space:normal}.faq-answer{padding-right:22px}.help-contact{align-items:flex-start;flex-direction:column;margin-top:32px;padding:20px}}
@media (prefers-reduced-motion:reduce){.faq-question,.category-tab{transition:none}}
</style>









