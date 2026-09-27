<script setup lang="ts">

import { nextTick, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

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
            <div class="typing-bubble"><i /><i /><i /></div>
          </div>
        </div>

        <div class="composer-wrap chat-composer-wrap" data-od-id="chat-composer-wrap">
          <form class="composer" :class="{ 'is-invalid': isError }" novalidate data-od-id="chat-composer" @submit.prevent="submitQuestion">
            <label class="sr-only" for="chatInput">输入你想咨询的校园事务</label>
            <textarea id="chatInput" ref="inputEl" v-model="question" rows="1" maxlength="200" autocomplete="off" placeholder="试试问：学生证丢了怎么补办？" data-od-id="chat-input" @input="onInput" @keydown="onKeydown" />
            <div class="composer-foot">
              <p class="composer-hint">Enter 发送 · Shift + Enter 换行</p>
              <button type="submit" class="send" :disabled="isSending" data-od-id="chat-send-button"><span>{{ isSending ? '处理中' : '开始咨询' }}</span><svg class="i" aria-hidden="true"><use href="#i-arrow-up" /></svg></button>
            </div>
          </form>
          <p class="composer-msg" :class="{ 'is-error': isError }" role="status" aria-live="polite" data-od-id="chat-status">{{ status }}</p>
          <div class="chips" data-od-id="suggestion-list">
            <button type="button" class="chip" data-od-id="suggestion-student-card" @click="useSuggestion('学生证丢了怎么补办？')">学生证丢了怎么补办？</button>
            <button type="button" class="chip" data-od-id="suggestion-repair" @click="useSuggestion('宿舍水龙头坏了，应该在哪里报修？')">宿舍报修去哪办理？</button>
            <button type="button" class="chip" data-od-id="suggestion-leave" @click="useSuggestion('因病请假需要准备哪些材料？')">因病请假需要哪些材料？</button>
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
  gap: 4px;
  min-height: 34px;
  padding: 0 14px;
  border: 1px solid var(--border);
  border-radius: 4px 16px 16px 16px;
  background: var(--surface);
}

.typing-bubble i {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: var(--accent);
  animation: typing 1s ease-in-out infinite;
}

.typing-bubble i:nth-child(2) { animation-delay: .12s; }
.typing-bubble i:nth-child(3) { animation-delay: .24s; }

@keyframes typing {
  0%, 60%, 100% { transform: translateY(0); opacity: .42; }
  30% { transform: translateY(-3px); opacity: 1; }
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
  display: flex;
  flex-direction: column;
  gap: 9px;
  padding: 14px 14px 11px;
  border: 1px solid var(--border);
  border-radius: 24px;
  background: var(--surface);
  transition: border-color .18s ease;
}

.composer:focus-within { border-color: var(--fg); }
.composer:has(:focus-visible) { outline: 2.5px solid var(--fg); outline-offset: 2px; }
.composer.is-invalid { border-color: var(--danger); }

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
  gap: 8px;
}

.chip {
  padding: 7px 13px;
  border: 1px solid var(--border);
  border-radius: 100px;
  background: var(--surface);
  color: var(--fg);
  font-size: 12.5px;
  white-space: nowrap;
  transition: background .16s ease, border-color .16s ease;
}

.chip:hover { background: var(--accent-soft); border-color: var(--accent); }

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
  .chips { justify-content: flex-start; overflow-x: auto; flex-wrap: nowrap; scrollbar-width: none; }
  .chips::-webkit-scrollbar { display: none; }
  .chip { display: inline-flex; align-items: center; min-height: 44px; padding: 0 16px; font-size: 13.5px; }
}

@media (prefers-reduced-motion: reduce) {

  .send,
  .chip,
  .composer,
  .typing-bubble i {
    transition: none;
    animation: none;
  }
}
</style>






