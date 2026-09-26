<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'
import { recentConversations, serviceItems } from '../data/home.mock'
import { useEyeGaze } from '../composables/useEyeGaze'
import { useHeroField } from '../composables/useHeroField'

const DRAFT_KEY = 'campus-assistant.draft'
const MAX_H = 104

const router = useRouter()

const question = ref('')
const status = ref('')
const isError = ref(false)
const character = ref<HTMLElement | null>(null)
const fxLayer = ref<HTMLElement | null>(null)
const inputEl = ref<HTMLTextAreaElement | null>(null)

useEyeGaze(character)
useHeroField(fxLayer)

/** 服务图标：按 id 映射到内联 sprite，数据层（home.mock.ts）保持不变 */
const SERVICE_ICON: Record<string, string> = {
  'student-card': 'i-id',
  'campus-card': 'i-card',
  repair: 'i-drop',
  leave: 'i-clock',
}
const visibleRecent = computed(() => recentConversations.slice(0, 3))

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
  <main class="main" data-od-id="home-main">
    <header class="topbar" data-od-id="global-header">
      <nav class="crumb" aria-label="页面标题"><strong>首页</strong></nav>
      <div class="top-actions">
        <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="notification-button" @click="dismissNotice('notification-button')"><svg class="i" aria-hidden="true"><use href="#i-bell"/></svg><span class="dot-badge"></span></button>
        <span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="profile-chip-top">林</span>
      </div>
    </header>

    <div class="workspace">
      <section class="stage" data-od-id="ask-stage">
        <div ref="fxLayer" class="fx-layer" aria-hidden="true" data-od-id="hero-field">
          <canvas class="fx-canvas"></canvas>
          <div class="fx-grid"></div>
          <div class="fx-orb fx-orb-1"></div>
          <div class="fx-orb fx-orb-2"></div>
          <div class="fx-glow"></div>
          <div class="fx-trail"></div>
        </div>

        <div class="character-layer" data-od-id="character-stage" aria-hidden="true">
          <div ref="character" class="character">
            <img class="ch-base" src="/assets/character.png" alt="">
            <div class="ch-iris-mask"><div class="ch-iris"><img src="/assets/character-iris.png" alt=""></div></div>
            <img class="ch-lash" src="/assets/character-lash.png" alt="">
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
            <button type="button" class="chip" @click="fill('学生证丢了怎么补办？')">学生证丢了怎么补办？</button>
            <button type="button" class="chip" @click="fill('宿舍水龙头坏了，应该在哪里报修？')">宿舍水龙头坏了去哪报修？</button>
            <button type="button" class="chip" @click="fill('因病请假需要准备哪些材料？')">因病请假需要哪些材料？</button>
          </div>
        </div>
      </section>

      <aside class="panel">
        <section data-od-id="quick-services">
          <div class="panel-head"><h2>常用服务</h2><button type="button" class="link-btn" data-od-id="view-all-services" @click="router.push({ name: 'services' })">查看全部</button></div>
          <ul class="list">
            <li v-for="item in serviceItems" :key="item.id">
              <button type="button" class="row" :data-od-id="`service-card-${item.id}`" @click="goChat(item.prompt)">
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
              <button type="button" class="recent-row" :data-od-id="item.id" @click="goChat(item.question)">
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
/* ── 工作区 ────────────────────────────────────────────────────────────── */
.workspace{display:flex;gap:clamp(20px,2.4vw,38px);flex:1;min-height:0;padding-bottom:clamp(16px,2vw,26px)}
.stage{position:relative;display:flex;flex-direction:column;min-width:0;flex:1}

/* ── 动态色块层（原首页搜索栏背景效果，改为发色，置于角色上方）───────────── */
.fx-layer{position:absolute;inset:0;z-index:0;overflow:hidden;pointer-events:none;isolation:isolate}
.fx-canvas{position:absolute;inset:0;width:100%;height:100%;opacity:.9}
.fx-grid{position:absolute;inset:0;opacity:.62;
  background-image:linear-gradient(var(--fx-dot) 1px,transparent 1px),linear-gradient(90deg,var(--fx-dot) 1px,transparent 1px);
  background-size:23px 23px;
  -webkit-mask-image:linear-gradient(100deg,transparent 6%,#000 58%,#000 88%,transparent 100%);
          mask-image:linear-gradient(100deg,transparent 6%,#000 58%,#000 88%,transparent 100%)}
.fx-orb{position:absolute;border-radius:var(--orb-radius,48% 52% 56% 44% / 50% 42% 58% 50%);
  transform:translate3d(var(--orb-x,0),var(--orb-y,0),0) rotate(var(--orb-rotate,0deg)) scale(var(--orb-scale,1));
  transition:border-radius .55s ease,transform .7s cubic-bezier(.2,.72,.2,1)}
.fx-orb-1{right:0;top:3%;width:min(54%,470px);aspect-ratio:1.22;background:var(--fx-orb-1)}
.fx-orb-2{left:1%;top:12%;width:min(30%,250px);aspect-ratio:1;background:var(--fx-orb-2)}
.fx-glow,.fx-trail{position:absolute;inset:0;opacity:0;transition:opacity .35s ease}
.fx-glow{background:radial-gradient(circle at var(--glow-x,74%) var(--glow-y,44%),oklch(93% .07 40 / .62),oklch(80% .13 38 / .16) 32%,transparent 64%)}
.fx-trail{filter:blur(12px);background:radial-gradient(ellipse 18% 28% at var(--glow-x,74%) var(--glow-y,44%),oklch(70% .154 36 / .2),transparent 72%)}
.fx-glow.on,.fx-trail.on{opacity:1}

/* ── 角色（托腮趴桌）＋ 整个红色眼瞳跟随 ────────────────────────────────
   角色图已在资源侧抠成透明底（alpha 由原画四边泛洪求得），所以不再需要羽化遮罩，
   头发边缘是真实 alpha，不会再有白色方框。
   眼睛拆成三层，这是「睫毛不被带走」的关键：
     1) 底图      —— 虹膜位置已愈合为眼白
     2) 虹膜精灵  —— 只含虹膜像素（睫毛像素按颜色剔除），整层平移
     3) 睫毛层    —— 静止，压在最上层
   虹膜精灵的 alpha 里没有睫毛，且睫毛层始终盖在最上面，因此眼动只动眼瞳。 */
.character-layer{position:relative;z-index:1;container-type:size;display:flex;align-items:flex-end;justify-content:center;
  flex:1;min-height:0;overflow:hidden;margin-bottom:-6px}
.character{position:relative;aspect-ratio:1024/954;
  width:min(100%,calc(100cqh * 1024 / 954),640px);
  /* 掩膜＝眼白开口（左 (395,599) 58×58、右 (613,532) 60×60，由真实像素量得）。
     比虹膜大约 11px：眼瞳在这个开口内平移，越界部分被柔和裁掉，等价于被眼睑挡住，
     不会溢到眼外的皮肤上。 */
  --eye-mask:
    radial-gradient(ellipse 5.664% 6.080% at 38.574% 62.788%, #000 88%, transparent 100%),
    radial-gradient(ellipse 5.859% 6.289% at 59.863% 55.765%, #000 88%, transparent 100%)}
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
  background:var(--accent);color:#fff;font-size:13px;font-weight:500;white-space:nowrap;transition:background .18s ease,transform .18s ease}
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
  /* 移动端宽度已由 width:100% 决定；size containment 会让 flex:none 的元素高度塌成 0 */
  .character-layer{container-type:normal;flex:none;width:100%;margin-bottom:-6px}
  .character{width:100%}
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
