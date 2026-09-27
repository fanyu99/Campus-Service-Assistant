<script setup lang="ts">

import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { recentConversations, serviceItems } from '../data/home.mock'
import { useEyeGaze } from '../composables/useEyeGaze'
import { useCharacterBubble } from '../composables/useCharacterBubble'

const DRAFT_KEY = 'campus-assistant.draft'
const MAX_H = 104

const router = useRouter()

const question = ref('')
const status = ref('')
const isError = ref(false)
const character = ref<HTMLElement | null>(null)
const inputEl = ref<HTMLTextAreaElement | null>(null)
const { hoverMessage, setHoverMessage, clearHoverMessage } = useCharacterBubble()

useEyeGaze(character)

/** 服务图标：按 id 映射到内联 sprite，数据层（home.mock.ts）保持不变 */
const SERVICE_ICON: Record<string, string> = {
  'student-card': 'i-id',
  'campus-card': 'i-card',
  repair: 'i-drop',
  leave: 'i-clock',
}
const visibleRecent = computed(() => recentConversations.slice(0, 3))

const hoverMessages = {
  services: ['这个我熟，才不是特意帮你的呢。', '校园事务我可是很在行的！'],
  recent: ['还想继续问上次的问题吗？', '记得很清楚嘛，要不要接着问？'],
  suggestions: ['这个问题不错，快问快问！', '哼，这种问题我也能回答。'],
}

function pickMessage(messages: string[]) {
  return messages[Math.floor(Math.random() * messages.length)]
}

function readProfileName() {
  const keys = ['campus-assistant.user', 'campus-assistant.profile', 'userProfile', 'currentUser']
  for (const key of keys) {
    try {
      const raw = localStorage.getItem(key)
      if (!raw) continue
      const data = JSON.parse(raw) as { name?: string; realName?: string; username?: string }
      const name = data.name ?? data.realName ?? data.username
      if (typeof name === 'string' && name.trim()) return name.trim()
    } catch (e) {
      /* 忽略无法解析的本地资料 */
    }
  }
  return ''
}

const userName = readProfileName()
const userLabel = userName ? userName + '同学' : '同学'
const greeting = computed(() => {
  const hour = new Date().getHours()
  const prefix = hour < 12 ? '早上好' : hour < 18 ? '下午好' : '晚上好'
  return prefix + '，' + userLabel
})
const waitingMessages = ['等待用户输入ing……', '我已经准备好了，快输入嘛～', '输入中？我在认真等着呢。']
const characterMessage = computed(() => {
  if (question.value.trim()) return waitingMessages[question.value.length % waitingMessages.length]
  return hoverMessage.value || greeting.value
})

function setHover(messages: string[]) {
  setHoverMessage(pickMessage(messages))
}

function clearHover() {
  clearHoverMessage()
}

function autoGrow() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, MAX_H) + 'px'
}

function fill(text: string) {
  question.value = text
  status.value = ''
  isError.value = false
  autoGrow()
  try {
    localStorage.setItem(DRAFT_KEY, text)
  } catch (e) {
    /* 隐私模式等场景下忽略 */
  }
  requestAnimationFrame(() => {
    const el = inputEl.value
    if (!el) return
    el.focus()
    el.setSelectionRange(text.length, text.length)
  })
}

/** 跳转到问答页；传入问题文本时通过 query 携带 */
function goChat(text?: string) {
  const q = text?.trim()
  router.push({ name: 'chat', query: q ? { q } : undefined })
}

function submitQuestion() {
  const text = question.value.trim()
  if (!text) {
    status.value = '先输入一个想咨询的校园事务，再点「开始咨询」'
    isError.value = true
    inputEl.value?.focus()
    return
  }
  isError.value = false
  goChat(text)
}

function onInput() {
  autoGrow()
  if (status.value) {
    status.value = ''
    isError.value = false
  }
  try {
    localStorage.setItem(DRAFT_KEY, question.value)
  } catch (e) {
    /* 忽略 */
  }
}

function onKeydown(e: KeyboardEvent) {
  // isComposing：中文输入法选词回车不应触发提交
  if (e.key === 'Enter' && !e.shiftKey && !e.isComposing) {
    e.preventDefault()
    submitQuestion()
  }
}

function dismissNotice(id: string) {
  const el = document.querySelector<HTMLElement>(`[data-od-id="${id}"]`)
  const dot = el?.querySelector('.dot-badge')
  if (dot) dot.remove()
  el?.setAttribute('aria-label', '通知（无未读）')
  el?.setAttribute('data-tip', '通知（无未读）')
}

try {
  const draft = localStorage.getItem(DRAFT_KEY)
  if (draft) question.value = draft
} catch (e) {
  /* 忽略 */
}

</script>

<template>
  <main class="main home-reveal" data-od-id="home-main">
    <header class="topbar" data-od-id="global-header">
      <nav class="crumb" aria-label="页面标题"><strong>首页</strong></nav>
      <div class="top-actions">
        <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button" @click="dismissNotice('notification-button')"><svg class="i" aria-hidden="true"><use href="#i-bell"/></svg><span class="dot-badge"></span></button>
        <span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="profile-chip-top">林</span>
      </div>
    </header>

    <div class="workspace">
      <section class="stage" data-od-id="ask-stage">
        <div class="character-layer" data-od-id="character-stage">
          <div class="character-wrap">
            <div class="character-bubble" role="status" aria-live="polite">{{ characterMessage }}</div>
            <div ref="character" class="character">
              <img class="ch-base" src="/assets/character.png" alt="">
              <div class="ch-iris-mask"><div class="ch-iris"><img src="/assets/character-iris.png" alt=""></div></div>
              <img class="ch-lash" src="/assets/character-lash.png" alt="">
            </div>
          </div>
        </div>

        <div class="composer-wrap">
          <form class="composer" :class="{ 'is-invalid': isError }" data-od-id="ask-composer" novalidate @submit.prevent="submitQuestion">
            <label class="sr-only" for="askInput">输入你想咨询的校园事务</label>
            <textarea id="askInput" ref="inputEl" v-model="question" data-od-id="ask-input" rows="1" maxlength="200" autocomplete="off" placeholder="试试问：学生证丢了怎么补办？" @input="onInput" @keydown="onKeydown"></textarea>
            <div class="composer-foot">
              <p class="composer-hint">Enter 发送 · Shift + Enter 换行</p>
              <button type="submit" class="send" data-od-id="ask-submit"><span>开始咨询</span><svg class="i" aria-hidden="true"><use href="#i-arrow-up"/></svg></button>
            </div>
          </form>
          <p class="composer-msg" :class="{ 'is-error': isError }" role="status" aria-live="polite">{{ status }}</p>
          <div class="chips" data-od-id="ask-suggestions">
            <button type="button" class="chip" @mouseenter="setHover(hoverMessages.suggestions)" @mouseleave="clearHover" @focus="setHover(hoverMessages.suggestions)" @blur="clearHover" @click="fill('学生证丢了怎么补办？')">学生证丢了怎么补办？</button>
            <button type="button" class="chip" @mouseenter="setHover(hoverMessages.suggestions)" @mouseleave="clearHover" @focus="setHover(hoverMessages.suggestions)" @blur="clearHover" @click="fill('宿舍水龙头坏了，应该在哪里报修？')">宿舍水龙头坏了去哪报修？</button>
            <button type="button" class="chip" @mouseenter="setHover(hoverMessages.suggestions)" @mouseleave="clearHover" @focus="setHover(hoverMessages.suggestions)" @blur="clearHover" @click="fill('因病请假需要哪些材料？')">因病请假需要哪些材料？</button>
          </div>
        </div>
      </section>

      <aside class="panel">
        <section data-od-id="quick-services">
          <div class="panel-head"><h2>常用服务</h2><button type="button" class="link-btn" data-od-id="view-all-services" @click="router.push({ name: 'services' })">查看全部</button></div>
          <ul class="list">
            <li v-for="item in serviceItems" :key="item.id">
              <button type="button" class="row" :data-od-id="`service-card-${item.id}`" @mouseenter="setHover(hoverMessages.services)" @mouseleave="clearHover" @focus="setHover(hoverMessages.services)" @blur="clearHover" @click="goChat(item.prompt)">
                <span class="row-icon" aria-hidden="true"><svg class="i"><use :href="'#' + SERVICE_ICON[item.id]"/></svg></span>
                <span class="row-title">{{ item.title }}</span>
                <span class="row-cat">{{ item.category }}</span>
                <svg class="i row-chev" aria-hidden="true"><use href="#i-chev"/></svg>
              </button>
            </li>
          </ul>
        </section>

        <section data-od-id="recent-conversations">
          <div class="panel-head"><h2>最近咨询</h2><button type="button" class="link-btn" data-od-id="view-all-history" @click="router.push({ name: 'history' })">全部记录</button></div>
          <ul class="list">
            <li v-for="item in visibleRecent" :key="item.id">
              <button type="button" class="recent-row" :data-od-id="item.id" @mouseenter="setHover(hoverMessages.recent)" @mouseleave="clearHover" @focus="setHover(hoverMessages.recent)" @blur="clearHover" @click="goChat(item.question)">
                <span class="recent-dot" aria-hidden="true"></span>
                <span class="recent-body"><strong>{{ item.question }}</strong><span>{{ item.time }}<i>·</i>{{ item.tag }}</span></span>
                <svg class="i row-chev" aria-hidden="true"><use href="#i-chev"/></svg>
              </button>
            </li>
          </ul>
        </section>
        <p class="mobile-note">本地演示 · 不收集敏感信息</p>
      </aside>
    </div>
  </main>
</template>

<style scoped>
/* ?? ???????????? opacity / transform??????????? ?? */
.home-reveal .topbar,
.home-reveal .stage,
.home-reveal .panel{animation:home-fade-up 460ms cubic-bezier(.2,0,0,1) both}
.home-reveal .stage{animation-delay:55ms}
.home-reveal .panel{animation-delay:105ms}
@keyframes home-fade-up{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
@media (prefers-reduced-motion:reduce){.character-bubble{animation:none}
  .home-reveal .topbar,.home-reveal .stage,.home-reveal .panel{animation:none}
}

/* ── 工作区 ────────────────────────────────────────────────────────────── */
.workspace{display:flex;gap:clamp(20px,2.4vw,38px);flex:1;min-height:0;padding-bottom:clamp(16px,2vw,26px)}
.stage{position:relative;display:flex;flex-direction:column;justify-content:flex-end;min-width:0;flex:1}

/* ── 动态色块层（原首页搜索栏背景效果，改为发色，置于角色上方）───────────── */

/* ── 角色（托腮趴桌）＋ 整个红色眼瞳跟随 ────────────────────────────────
   角色图已在资源侧抠成透明底（alpha 由原画四边泛洪求得），所以不再需要羽化遮罩，
   头发边缘是真实 alpha，不会再有白色方框。
   眼睛拆成三层，这是「睫毛不被带走」的关键：
     1) 底图      —— 虹膜位置已愈合为眼白
     2) 虹膜精灵  —— 只含虹膜像素（睫毛像素按颜色剔除），整层平移
     3) 睫毛层    —— 静止，压在最上层
   虹膜精灵的 alpha 里没有睫毛，且睫毛层始终盖在最上面，因此眼动只动眼瞳。 */
.character-wrap{position:relative;width:min(36%,230px)}.character-bubble{position:absolute;z-index:3;left:72%;bottom:calc(100% - 4px);width:max-content;max-width:min(300px,76vw);padding:10px 15px;border:1px solid var(--border);border-radius:18px;background:var(--surface);color:var(--fg);font-size:13px;line-height:1.5;text-align:center;box-shadow:0 10px 24px color-mix(in srgb,var(--fg) 8%,transparent);transform:translateX(-18%);animation:bubble-pop .24s ease both}.character-bubble::after{content:"";position:absolute;left:22%;bottom:-7px;width:12px;height:12px;border-right:1px solid var(--border);border-bottom:1px solid var(--border);background:var(--surface);transform:translateX(-50%) rotate(45deg)}@keyframes bubble-pop{from{opacity:0;transform:translateX(-18%) translateY(4px) scale(.98)}to{opacity:1;transform:translateX(-18%)}}
.character-layer{position:relative;z-index:1;display:flex;align-items:flex-end;justify-content:center;
  flex:0 0 auto;min-height:0;overflow:visible;margin-bottom:0}
.character{position:relative;aspect-ratio:1024/954;
  width:100%;
  /* 掩膜＝眼白开口（左 (395,599)、右 (613,532)，由真实像素量得）。
     半径必须 ≥ 精灵半径 + 最大位移，否则眼瞳移到极限时，领先侧那半圈描边会被
     掩膜切掉、看起来像虹膜被削平。精灵自身 alpha 已是实测椭圆（左 r54/r53、
     右 r56/r57），底图在该椭圆内已愈合为眼白，所以这里只需留够余量：
     rx = 虹膜 rx + 4(精灵外扩) + 14(横向位移) + 2(余量)，ry 同理 +12(纵向位移)。 */
  --eye-mask:
    radial-gradient(ellipse 6.836% 7.023% at 38.574% 62.788%, #000 88%, transparent 100%),
    radial-gradient(ellipse 7.031% 7.442% at 59.863% 55.765%, #000 88%, transparent 100%)}
.character img{position:absolute;display:block}
.ch-base{inset:0;width:100%;height:100%}
.ch-iris-mask{position:absolute;inset:0;pointer-events:none;-webkit-mask-image:var(--eye-mask);mask-image:var(--eye-mask)}
.ch-iris{position:absolute;inset:0;transform:translate(var(--gx,0%),var(--gy,0%))}
.ch-iris img,.ch-lash{left:30.8594%;top:46.1216%;width:37.8906%;height:24.7379%}
@media (prefers-reduced-motion:reduce){.ch-iris{transform:none}}

/* ── 聊天输入框（角色正好趴在其上沿）─────────────────────────────────── */
.composer-wrap{position:relative;z-index:2;width:min(660px,100%);margin:0 auto;display:flex;flex-direction:column;gap:10px}
.composer{display:flex;flex-direction:column;gap:9px;padding:14px 14px 11px;border:1px solid var(--border);
  border-radius:24px;background:var(--surface);transition:border-color .18s ease}
.composer:focus-within{border-color:var(--fg)}
.composer:has(:focus-visible){outline:2.5px solid var(--fg);outline-offset:2px}
.composer.is-invalid{border-color:var(--danger)}
.composer textarea{width:100%;min-height:25px;max-height:104px;padding:0 4px;border:0;background:transparent;
  color:var(--fg);font:400 15px/1.6 var(--font-body);resize:none;overflow-y:auto;outline:0}
.composer textarea::placeholder{color:var(--muted)}
.composer-foot{display:flex;align-items:center;justify-content:space-between;gap:12px;padding-left:4px}
.composer-hint{margin:0;color:var(--muted);font-size:12px;white-space:nowrap;min-width:0;overflow:hidden;text-overflow:ellipsis}
.send{display:inline-flex;align-items:center;gap:7px;flex:0 0 auto;height:38px;padding:0 16px;border-radius:13px;
  background:var(--accent);color:var(--page-bg);font-size:13px;font-weight:500;white-space:nowrap;transition:background .18s ease,transform .18s ease}
.send .i{width:15px;height:15px;stroke-width:2}
.send:hover{background:var(--accent-hover);transform:translateY(-1px)}
.send:active{transform:translateY(0)}
.composer-msg{margin:0;min-height:19px;font-size:12px;line-height:1.6;color:var(--fg);text-align:center}
.composer-msg.is-error{color:var(--danger)}
.chips{display:flex;flex-wrap:wrap;justify-content:center;gap:8px}
.chip{padding:7px 13px;border:1px solid var(--border);border-radius:100px;background:var(--surface);color:var(--fg);
  font-size:12.5px;white-space:nowrap;transition:background .16s ease,border-color .16s ease}
.chip:hover{background:var(--accent-soft);border-color:var(--accent)}

/* ── 右侧信息列 ────────────────────────────────────────────────────────── */
.panel{display:flex;flex-direction:column;gap:26px;flex:0 0 340px;width:340px;min-width:0}
.panel-head{display:flex;align-items:baseline;justify-content:space-between;gap:12px}
.panel h2{margin:0;font-family:var(--font-display);font-weight:900;font-size:16.5px;letter-spacing:-.012em}
.link-btn{flex:0 0 auto;padding:2px 0;color:var(--muted);font-size:12.5px;white-space:nowrap;transition:color .16s ease}
.link-btn:hover{color:var(--fg)}
.list{display:grid;gap:2px;margin-top:9px}
.row,.recent-row{display:flex;align-items:center;gap:11px;width:calc(100% + 20px);margin-inline:-10px;padding:6px 10px;
  border-radius:12px;color:var(--fg);text-align:left;transition:background .16s ease}
.row{min-height:46px}
.row:hover,.recent-row:hover{background:var(--row-hover)}
.row:hover .row-chev,.recent-row:hover .row-chev{color:var(--fg)}
.row-icon{display:grid;place-items:center;width:30px;height:30px;flex:0 0 auto;border-radius:9px;background:var(--surface);color:var(--fg)}
.row-icon .i{width:15px;height:15px}
.row-title{font-weight:500;min-width:0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:14px}
.row-cat{flex:0 0 auto;color:var(--muted);font-size:12px;white-space:nowrap}
.row-chev{width:14px;height:14px;flex:0 0 auto;color:var(--muted);transition:color .16s ease}
.recent-row{min-height:48px;padding:7px 10px}
.recent-dot{width:5px;height:5px;flex:0 0 auto;border-radius:50%;background:var(--muted)}
.recent-body{min-width:0;flex:1}
.recent-body strong{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:13.5px;font-weight:400}
.recent-body span{display:block;margin-top:3px;color:var(--muted);font-size:11.5px}
.recent-body i{margin:0 5px;font-style:normal;opacity:.6}
.mobile-note{display:none}

/* ── 窄桌面 ────────────────────────────────────────────────────────────── */
@media (max-width:1080px){
  .panel{flex-basis:272px;width:272px}
  .composer-hint{display:none}
  .composer-foot{justify-content:flex-end}
}
@media (max-width:940px){
  .workspace{gap:18px}
  .panel{flex-basis:250px;width:250px}
  .panel > section{min-width:0}
  .row,.recent-row{width:100%;margin-inline:0;padding-inline:8px}
}
@media (max-height:660px) and (min-width:701px){
  .composer{padding:10px 12px 8px;border-radius:20px}
  .chips{display:none}
  .composer-msg{min-height:0}
}

/* ── 移动端（≤700px）────────────────────────────────────────────────── */
@media (max-width:700px){
  .workspace{flex-direction:column;gap:22px;padding-bottom:36px}
  /* 移动端保持角色与对话框的相对位置，并将组合锚定在页面底部 */
  .character-layer{flex:none;width:100%;margin-bottom:0}
  .character-wrap{width:min(36%,230px)}
  .composer-wrap{width:100%}
  .composer{padding:13px 13px 11px;border-radius:22px}
  .composer textarea{font-size:16px}
  .send{height:44px;padding:0 18px}
  .panel{flex:none;width:100%;flex-direction:column;gap:30px}
  .panel h2{font-size:clamp(22px,6.3vw,30px);line-height:1.25}
  .row,.recent-row{min-height:52px;width:calc(100% + 16px);margin-inline:-8px;padding:8px}
  .chips{justify-content:flex-start}
  .chip{display:inline-flex;align-items:center;min-height:44px;padding:0 16px;font-size:13.5px}
  .mobile-note{display:block;margin:0;color:var(--muted);font-size:11.5px;line-height:1.6}
}
</style>

