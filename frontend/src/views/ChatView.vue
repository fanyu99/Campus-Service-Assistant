<script setup lang="ts">

import { nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import AnimatedButton from '../components/AnimatedButton.vue'

type Message = {
  id: number
  role: 'user' | 'assistant'
  text: string
  time: string
}

const route = useRoute()
const question = ref('')
const status = ref('')
const isError = ref(false)
const isSending = ref(false)
const inputEl = ref<HTMLTextAreaElement | null>(null)
const messageList = ref<HTMLElement | null>(null)
let nextMessageId = 2


const initialQuestion = typeof route.query.q === 'string' ? route.query.q.trim() : ''
const messages = ref<Message[]>([
  ...(initialQuestion
    ? [{ id: 1, role: 'user' as const, text: initialQuestion, time: '刚刚' }]
    : []),
])

if (initialQuestion) {
  messages.value.push({
    id: nextMessageId++,
    role: 'assistant',
    text: '我已收到你的问题，正在整理与校园事务相关的办理流程。你可以继续补充院系、校区或时间等信息，我会给出更准确的建议。',
    time: '刚刚',
  })
}

function autoGrow() {
  const el = inputEl.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 132) + 'px'
}

function scrollToLatest() {
  nextTick(() => {
    const el = messageList.value
    if (el) el.scrollTop = el.scrollHeight
  })
}

function clearStatus() {
  status.value = ''
  isError.value = false
}

function onInput() {
  autoGrow()
  clearStatus()
}

function useSuggestion(text: string) {
  question.value = text
  clearStatus()
  autoGrow()
  nextTick(() => {
    inputEl.value?.focus()
    inputEl.value?.setSelectionRange(text.length, text.length)
  })
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
    event.preventDefault()
    submitQuestion()
  }
}

function getTime() {
  return new Intl.DateTimeFormat('zh-CN', { hour: '2-digit', minute: '2-digit' }).format(new Date())
}

function submitQuestion() {
  const text = question.value.trim()
  if (!text || isSending.value) {
    if (!text) {
      status.value = '先输入你想咨询的校园事务'
      isError.value = true
      inputEl.value?.focus()
    }
    return
  }

  isSending.value = true
  clearStatus()
  messages.value.push({ id: nextMessageId++, role: 'user', text, time: '刚刚' })
  question.value = ''
  autoGrow()
  scrollToLatest()

  window.setTimeout(() => {
    messages.value.push({
      id: nextMessageId++,
      role: 'assistant',
      text: '好的，我会围绕这个问题为你梳理办理条件、所需材料和办理入口。当前页面是原型演示，后续可接入校园服务知识库返回具体结果。',
      time: getTime(),
    })
    isSending.value = false
    scrollToLatest()
  }, 520)
}

watch(
  () => route.query.q,
  (value) => {
    const text = typeof value === 'string' ? value.trim() : ''
    if (!text || messages.value.length) return
    messages.value.push({ id: nextMessageId++, role: 'user', text, time: '刚刚' })
    scrollToLatest()
  },
)

</script>

<template>
  <main class="main chat-main" data-od-id="chat-main">
    <header class="topbar" data-od-id="chat-header">
      <nav class="crumb" aria-label="页面标题">
        <strong>我的对话</strong>
      </nav>
      <div class="top-actions">
        <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="chat-notification-button">
          <svg class="i" aria-hidden="true"><use href="#i-bell" /></svg>
          <span class="dot-badge" />
        </button>
        <span class="avatar" role="img" aria-label="当前用户：林同学" data-od-id="chat-profile-chip">林</span>
      </div>
    </header>

    <section class="chat-workspace" data-od-id="conversation-workspace">

      <div class="chat-column">
        <div class="chat-heading" data-od-id="chat-heading">
          <h1>我的对话</h1>
        </div>

        <div ref="messageList" class="message-list" role="log" aria-live="polite" data-od-id="message-list">
          <div v-if="!messages.length" class="empty-state" data-od-id="empty-conversation">
            <p> 询问问题 </p>
            <p>例如：校园卡丢失后应该怎么处理？</p>
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            class="message-row"
            :class="`is-${message.role}`"
            :data-od-id="`${message.role}-message-${message.id}`"
          >
            <img v-if="message.role === 'assistant'" class="message-avatar" src="/assets/brand-mark.png" alt="" aria-hidden="true" />
            <div class="message-content">
              <div class="message-meta">
                <strong>{{ message.role === 'assistant' ? '校园助手' : '我' }}</strong>
                <span>{{ message.time }}</span>
              </div>
              <p class="message-bubble">{{ message.text }}</p>
            </div>
          </article>

          <div v-if="isSending" class="typing-row" data-od-id="typing-indicator">
            <img class="message-avatar" src="/assets/brand-mark.png" alt="" aria-hidden="true" />
            <div class="typing-bubble" role="status" aria-label="校园助手正在生成回答">
              <div class="loading-animation loading-animation--assistant" aria-hidden="true">
                <span class="loading-ball" />
                <span class="loading-ball" />
                <span class="loading-ball" />
                <span class="loading-shadow" />
                <span class="loading-shadow" />
                <span class="loading-shadow" />
              </div>
            </div>
          </div>
        </div>

        <div class="composer-wrap chat-composer-wrap" data-od-id="chat-composer-wrap">
          <form class="composer" :class="{ 'is-invalid': isError }" novalidate data-od-id="chat-composer" @submit.prevent="submitQuestion">
            <label class="sr-only" for="chatInput">输入你想咨询的校园事务</label>
            <textarea id="chatInput" ref="inputEl" v-model="question" rows="1" maxlength="200" autocomplete="off" placeholder="试试问：学生证丢了怎么补办？" data-od-id="chat-input" @input="onInput" @keydown="onKeydown" />
            <div class="composer-foot">
              <p class="composer-hint">Enter 发送 · Shift + Enter 换行</p>
              <button type="submit" class="send spark-button" :class="{ 'is-loading': isSending }" :disabled="isSending" data-od-id="chat-send-button">
                <span v-if="isSending" class="sr-only">正在发送，校园助手准备回答中</span>
                <span v-if="isSending" class="loading-animation loading-animation--button" aria-hidden="true">
                  <span class="loading-ball" />
                  <span class="loading-ball" />
                  <span class="loading-ball" />
                  <span class="loading-shadow" />
                  <span class="loading-shadow" />
                  <span class="loading-shadow" />
                </span>
                <template v-else>
                  <span>开始咨询</span><svg class="i" aria-hidden="true"><use href="#i-arrow-up" /></svg>
                </template>
              </button>
            </div>
          </form>
          <p class="composer-msg" :class="{ 'is-error': isError }" role="status" aria-live="polite" data-od-id="chat-status">{{ status }}</p>
          <div class="chips" data-od-id="suggestion-list">
            <AnimatedButton data-od-id="suggestion-student-card" @click="useSuggestion('学生证丢了怎么补办？')">学生证丢了怎么补办？</AnimatedButton>
            <AnimatedButton data-od-id="suggestion-repair" @click="useSuggestion('宿舍水龙头坏了，应该在哪里报修？')">宿舍报修去哪办理？</AnimatedButton>
            <AnimatedButton data-od-id="suggestion-leave" @click="useSuggestion('因病请假需要准备哪些材料？')">因病请假需要哪些材料？</AnimatedButton>
          </div>
        </div>
      </div>
    </section>
  </main>
</template>

<style scoped>
.chat-main {
  min-height: 0;
  overflow: hidden;
}

.chat-workspace {
  position: relative;
  display: flex;
  flex: 1;
  min-height: 0;
  justify-content: center;
  padding: 18px 0 28px;
  overflow: hidden;
}


.chat-column {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  width: min(100%, 860px);
  min-height: 0;
}

.chat-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  padding: 22px 6px 14px;
}

.chat-heading h1 {
  max-width: 600px;
  margin: 0;
  font-family: var(--font-display);
  font-size: clamp(24px, 3vw, 32px);
  font-weight: 900;
  line-height: 1.35;
  letter-spacing: 0;
}


.message-list {
  display: flex;
  flex: 1;
  flex-direction: column;
  gap: 20px;
  min-height: 0;
  padding: 18px 6px 16px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--border) transparent;
}

.empty-state {
  display: grid;
  place-items: center;
  align-content: center;
  flex: 1;
  min-height: 230px;
  color: var(--muted);
  text-align: center;
}

.empty-state p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
}

.message-row,
.typing-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 82%;
  user-select: text;
  -webkit-user-select: text;
}

.message-row.is-user {
  align-self: flex-end;
  justify-content: flex-end;
}

.message-row.is-assistant,
.typing-row {
  align-self: flex-start;
}

.message-avatar {
  display: block;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: #fff;
  box-shadow: 0 1px 3px rgba(80, 30, 10, .14);
  object-fit: cover;
}

.message-content {
  min-width: 0;
}

.message-row.is-user .message-content {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.message-meta {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin: 0 4px 6px;
  color: var(--muted);
  font-size: 11px;
}

.message-meta strong {
  color: var(--fg);
  font-size: 12px;
  font-weight: 600;
}

.message-bubble {
  margin: 0;
  padding: 12px 15px;
  border: 1px solid var(--border);
  border-radius: 4px 16px 16px 16px;
  background: var(--surface);
  color: var(--fg);
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.message-row.is-user .message-bubble {
  border-color: transparent;
  border-radius: 16px 4px 16px 16px;
  background: var(--accent);
  color: var(--page-bg);
}

.typing-bubble {
  display: flex;
  align-items: center;
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid color-mix(in srgb, var(--accent) 22%, var(--border));
  border-radius: 4px 16px 16px 16px;
  background: var(--surface);
}

.loading-animation {
  --loader-ball-size: 12px;
  --loader-track-width: 62px;
  --loader-height: 31px;
  --loader-rest-top: 0px;
  --loader-floor-top: 25px;
  --loader-shadow-width: 13px;
  --loader-shadow-top: 27px;
  position: relative;
  z-index: 1;
  width: var(--loader-track-width);
  height: var(--loader-height);
}

.loading-ball,
.loading-shadow {
  position: absolute;
  display: block;
  transform-origin: 50%;
}

.loading-ball {
  top: var(--loader-floor-top);
  left: 4px;
  width: var(--loader-ball-size);
  height: var(--loader-ball-size);
  border-radius: 50%;
  background: var(--accent);
  box-shadow: 0 3px 8px color-mix(in srgb, var(--accent) 26%, transparent);
  animation: loader-ball .5s alternate infinite ease;
}

.loading-ball:nth-child(2) { left: 25px; animation-delay: .2s; }
.loading-ball:nth-child(3) { left: 46px; animation-delay: .3s; }

.loading-shadow {
  top: var(--loader-shadow-top);
  left: 3px;
  z-index: -1;
  width: var(--loader-shadow-width);
  height: 4px;
  border-radius: 50%;
  background: color-mix(in srgb, var(--accent) 44%, transparent);
  filter: blur(1px);
  animation: loader-shadow .5s alternate infinite ease;
}

.loading-shadow:nth-child(5) { left: 24px; animation-delay: .2s; }
.loading-shadow:nth-child(6) { left: 45px; animation-delay: .3s; }

@keyframes loader-ball {
  0% {
    top: var(--loader-floor-top);
    height: 5px;
    border-radius: 50px 50px 25px 25px;
    transform: scaleX(1.7);
  }

  40% {
    height: var(--loader-ball-size);
    border-radius: 50%;
    transform: scaleX(1);
  }

  100% { top: var(--loader-rest-top); }
}

@keyframes loader-shadow {
  0% { transform: scaleX(1.5); }
  40% { transform: scaleX(1); opacity: .7; }
  100% { transform: scaleX(.2); opacity: .4; }
}

.loading-animation--button {
  --loader-ball-size: 6px;
  --loader-track-width: 30px;
  --loader-height: 17px;
  --loader-floor-top: 11px;
  --loader-shadow-top: 14px;
  --loader-shadow-width: 7px;
}

.loading-animation--button .loading-ball { left: 1px; }
.loading-animation--button .loading-ball:nth-child(2) { left: 12px; }
.loading-animation--button .loading-ball:nth-child(3) { left: 23px; }
.loading-animation--button .loading-shadow { left: 0; height: 2px; }
.loading-animation--button .loading-shadow:nth-child(5) { left: 11px; }
.loading-animation--button .loading-shadow:nth-child(6) { left: 22px; }

.send.is-loading {
  gap: 0;
  min-width: 58px;
  padding-inline: 13px;
}

.chat-composer-wrap {
  position: relative;
  z-index: 2;
  width: min(660px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.composer {
  position: relative;
  isolation: isolate;
  display: flex;
  flex-direction: column;
  gap: 9px;
  overflow: hidden;
  padding: 14px 14px 11px;
  border: 1px solid transparent;
  border-radius: 24px;
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(110deg, var(--border), color-mix(in srgb, var(--accent) 42%, var(--border)), var(--border)) border-box;
  box-shadow: 0 7px 18px color-mix(in srgb, var(--fg) 4%, transparent);
  transition: box-shadow .24s ease, background .3s ease, transform .24s ease;
}

.composer::before {
  content: '';
  position: absolute;
  z-index: 0;
  inset: 0;
  opacity: .74;
  pointer-events: none;
  background-image:
    linear-gradient(to right, var(--composer-grid-line) 1px, transparent 1px),
    linear-gradient(to bottom, var(--composer-grid-line) 1px, transparent 1px),
    linear-gradient(135deg, transparent 0 53%, var(--composer-grid-fade) 78%);
  background-size: 16px 16px, 16px 16px, 100% 100%;
  background-position: center;
  transition: opacity .24s ease, filter .3s ease;
}

.composer::after {
  content: '';
  position: absolute;
  z-index: 2;
  inset: 0;
  padding: 2px;
  border-radius: inherit;
  pointer-events: none;
  opacity: 0;
  background: linear-gradient(105deg, transparent 15%, var(--composer-flow-hot) 40%, var(--composer-flow-bright) 50%, var(--accent) 60%, transparent 85%);
  background-size: 220% 100%;
  background-position: 100% 50%;
  filter: drop-shadow(0 0 6px var(--composer-hover-glow));
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  transition: opacity .2s ease, filter .2s ease;
}

.composer textarea,
.composer-foot { position: relative; z-index: 1; }

.composer:hover {
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(118deg, var(--accent-hover), var(--accent), var(--accent-hover)) border-box;
  box-shadow: 0 0 0 2px var(--composer-hover-glow), 0 0 22px var(--composer-hover-glow), 0 14px 30px color-mix(in srgb, var(--composer-hover-glow) 60%, transparent);
}

.composer:hover::before {
  opacity: 1;
  filter: saturate(1.25) contrast(1.08);
  animation: composer-grid-drift 2.6s linear infinite;
}

.composer:hover::after {
  opacity: .9;
  animation: composer-border-flow 2s linear infinite;
}

.composer:focus-within {
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(125deg, var(--composer-flow-hot), var(--composer-flow-bright), var(--accent)) border-box;
  box-shadow: 0 0 0 3px var(--composer-focus-glow), 0 0 30px var(--composer-focus-glow), 0 16px 38px color-mix(in srgb, var(--composer-focus-glow) 64%, transparent);
}

.composer:focus-within::before {
  opacity: 1;
  filter: saturate(1.4) contrast(1.12);
  animation: composer-grid-drift 1.35s linear infinite;
}

.composer:focus-within::after {
  opacity: 1;
  filter: drop-shadow(0 0 10px var(--composer-focus-glow));
  animation: composer-border-flow 1.05s linear infinite;
}

@keyframes composer-grid-drift {
  from { background-position: 0 0, 0 0, center; }
  to { background-position: 32px 32px, 32px 32px, center; }
}

@keyframes composer-border-flow {
  from { background-position: 100% 50%; }
  to { background-position: -120% 50%; }
}
.composer:has(:focus-visible) { outline: 2.5px solid var(--fg); outline-offset: 2px; }
.composer.is-invalid {
  background:
    linear-gradient(var(--surface), var(--surface)) padding-box,
    linear-gradient(125deg, var(--danger), color-mix(in srgb, var(--danger) 42%, var(--border)), var(--danger)) border-box;
}

.composer textarea {
  width: 100%;
  min-height: 25px;
  max-height: 104px;
  padding: 0 4px;
  border: 0;
  background: transparent;
  color: var(--fg);
  font: 400 15px/1.6 var(--font-body);
  resize: none;
  overflow-y: auto;
  outline: 0;
}

.composer textarea::placeholder { color: var(--muted); }

.composer-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-left: 4px;
}

.composer-hint {
  margin: 0;
  min-width: 0;
  overflow: hidden;
  color: var(--muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.send {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  flex: 0 0 auto;
  height: 38px;
  padding: 0 16px;
  border-radius: 13px;
  background: var(--accent);
  color: var(--page-bg);
  font-size: 13px;
  font-weight: 500;
  white-space: nowrap;
  transition: background .18s ease, transform .18s ease;
}

.send .i { width: 15px; height: 15px; stroke-width: 2; }
.send:hover { background: var(--accent-hover); transform: translateY(-1px); }
.send:active { transform: translateY(0); }
.send:disabled { cursor: wait; opacity: .68; transform: none; }

.composer-msg {
  margin: 0;
  min-height: 19px;
  color: var(--fg);
  font-size: 12px;
  line-height: 1.6;
  text-align: center;
}

.composer-msg.is-error { color: var(--danger); }

.chips {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

@media (max-width: 700px) {
  .chat-main {
    min-height: 100svh;
    overflow: visible;
  }

  .chat-workspace {
    min-height: calc(100svh - 74px);
    padding: 8px 0 18px;
    overflow: visible;
  }


  .chat-heading {
    gap: 12px;
    padding: 12px 0 10px;
  }

  .chat-heading h1 { font-size: 24px; }

  .message-list { padding-inline: 0; }

  .message-row,
  .typing-row { max-width: 92%; }

  .chat-composer-wrap { width: 100%; }
  .composer { padding: 13px 13px 11px; border-radius: 22px; }
  .composer textarea { font-size: 16px; }
  .send { height: 44px; padding: 0 18px; }
  .chips { justify-content: flex-start; overflow-x: auto; flex-wrap: nowrap; scrollbar-width: none; padding-block: 3px; }
  .chips::-webkit-scrollbar { display: none; }
}

@media (prefers-reduced-motion: reduce) {

  .send,
  .composer,
  .composer::before,
  .composer::after,
  .loading-ball,
  .loading-shadow {
    transition: none;
    animation: none;
  }

  .loading-ball {
    top: var(--loader-rest-top);
    height: var(--loader-ball-size);
    transform: none;
  }

  .loading-shadow {
    transform: scaleX(.7);
    opacity: .5;
  }
}
</style>








