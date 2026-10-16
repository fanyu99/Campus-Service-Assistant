<script setup lang="ts">

import { computed, nextTick, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ApiError, sendChatMessage } from '../api/client'
import type { ChatResponse } from '../api/client'
import { describeApiError } from '../data/answer-status'
import { useProfile, avatarInitial } from '../composables/useProfile'
import AnimatedButton from '../components/AnimatedButton.vue'
import ThemeToggleButton from '../components/ThemeToggleButton.vue'
import AnswerCard from '../components/AnswerCard.vue'
import FeedbackBar from '../components/FeedbackBar.vue'
import SourceList from '../components/SourceList.vue'
import StateNotice from '../components/StateNotice.vue'

/** 一条消息：用户文本、助手结构化响应，或本地/接口失败（可重试） */
type ChatMessage = {
  id: number
  role: 'user' | 'assistant'
  time: string
  text?: string
  response?: ChatResponse
  failure?: { message: string; retryText: string }
}

const route = useRoute()
const router = useRouter()
const { profile } = useProfile()
const avatarText = computed(() => avatarInitial(profile.value.displayName))
const question = ref('')
const status = ref('')
const isError = ref(false)
const isSending = ref(false)
const inputEl = ref<HTMLTextAreaElement | null>(null)
const messageList = ref<HTMLElement | null>(null)
/** 会话标识：首轮为 null，后端创建后回传，后续轮次原样带回（契约 §4.3） */
const conversationId = ref<string | null>(null)
const messages = ref<ChatMessage[]>([])
let nextMessageId = 1
let lastSubmitted = ''


const initialQuestion = typeof route.query.q === 'string' ? route.query.q.trim() : ''

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

/**
 * 发送一轮提问。
 * - 首轮 `conversation_id` 传 null，后端创建会话；之后原样回传，刷新页面即新会话（契约 §4.3）。
 * - 会话失效（404）时清空标识并提示，用户可直接重发，避免卡在坏会话上。
 */
async function send(text: string, appendUser = true): Promise<void> {
  const message = text.trim()
  if (!message || isSending.value) return

  if (appendUser) {
    messages.value.push({ id: nextMessageId++, role: 'user', text: message, time: '刚刚' })
  }
  lastSubmitted = message
  isSending.value = true
  clearStatus()
  scrollToLatest()

  try {
    const response = await sendChatMessage({
      conversation_id: conversationId.value,
      message,
    })
    conversationId.value = response.conversation_id
    messages.value.push({ id: nextMessageId++, role: 'assistant', time: getTime(), response })
  } catch (error) {
    if (error instanceof ApiError && error.code === 'CONVERSATION_NOT_FOUND') {
      conversationId.value = null
    }
    messages.value.push({
      id: nextMessageId++,
      role: 'assistant',
      time: getTime(),
      failure: { message: describeApiError(error), retryText: message },
    })
  } finally {
    isSending.value = false
    scrollToLatest()
  }
}

function submitQuestion() {
  const text = question.value.trim()
  if (!text) {
    status.value = '先写下你要咨询的事，再发送'
    isError.value = true
    inputEl.value?.focus()
    return
  }
  if (isSending.value) return
  question.value = ''
  autoGrow()
  void send(text)
}

function retry(text: string): void {
  void send(text, false)
}

function goServices(): void {
  router.push({ name: 'services' })
}

/** 依据不足时，区分「完全没有资料」与「有资料但已过期/未核验」两种提示 */
function evidenceTitle(response: ChatResponse): string {
  return response.sources.length
    ? '暂时没有可依据的最新资料'
    : '没有找到可靠的办理依据'
}

function evidenceDescription(response: ChatResponse): string {
  return response.sources.length
    ? '找到的相关资料已过期或尚未核验，不作为办理依据；请以学校最新通知为准。'
    : '这个问题我暂时没有可依据的官方资料，建议咨询责任部门，或换一种问法。'
}

/* 从首页/支持事项带问题跳转过来时自动提问；同一问题不重复发送 */
if (initialQuestion) {
  void send(initialQuestion)
}

watch(
  () => route.query.q,
  (value) => {
    const text = typeof value === 'string' ? value.trim() : ''
    if (!text || text === lastSubmitted) return
    void send(text)
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
        <ThemeToggleButton />
        <button type="button" class="icon-btn" aria-label="通知" data-tip="通知" data-od-id="chat-notification-button">
          <svg class="i" aria-hidden="true"><use href="#i-bell" /></svg>
          <span class="dot-badge" />
        </button>
        <span class="avatar" role="img" :aria-label="'当前用户：' + profile.displayName" data-od-id="chat-profile-chip">{{ avatarText }}</span>
      </div>
    </header>

    <section class="chat-workspace" data-od-id="conversation-workspace">

      <div class="chat-column">
        <div class="chat-heading" data-od-id="chat-heading">
          <h1>咨询校园事务</h1>
        </div>

        <div ref="messageList" class="message-list" role="log" aria-live="polite" data-od-id="message-list">
          <div v-if="!messages.length" class="empty-state" data-od-id="empty-conversation">
            <p>还没有对话</p>
            <p>在下方输入框写下问题，也可以直接选一个示例</p>
          </div>

          <article
            v-for="message in messages"
            :key="message.id"
            class="message-row"
            :class="`is-${message.role}`"
            :data-od-id="`${message.role}-message-${message.id}`"
          >
            <img v-if="message.role === 'assistant'" class="message-avatar" src="/assets/brand-mark.webp" alt="" aria-hidden="true" width="256" height="256" decoding="async" />
            <div class="message-content">
              <div class="message-meta">
                <strong>{{ message.role === 'assistant' ? '校园助手' : '我' }}</strong>
                <span>{{ message.time }}</span>
              </div>

              <p v-if="message.text" class="message-bubble">{{ message.text }}</p>

              <template v-else-if="message.response">
                <!-- answered：结构化办事卡片 + 来源 + 反馈栏 -->
                <template v-if="message.response.status === 'answered' && message.response.answer">
                  <AnswerCard :card="message.response.answer" />
                  <SourceList :sources="message.response.sources" heading="来源" />
                  <FeedbackBar :conversation-id="message.response.conversation_id" />
                </template>

                <!-- need_clarification：把追问当作助手消息，用户直接接着回答 -->
                <template v-else-if="message.response.status === 'need_clarification'">
                  <p class="message-bubble">{{ message.response.clarifying_question ?? '能再多说一点吗？' }}</p>
                  <p class="follow-hint">补充信息后直接发送，我会接着这次对话回答。</p>
                </template>

                <!-- unsupported：给出支持范围，不编造 -->
                <StateNotice
                  v-else-if="message.response.status === 'unsupported'"
                  tone="info"
                  title="这个问题暂时不在服务范围内"
                  description="目前支持学生证补办、校园卡补办、宿舍报修、请假办理、奖助学金、转专业与毕业手续。"
                  action-label="看看支持事项"
                  @action="goServices"
                />

                <!-- insufficient_evidence：拒答，并回带过期/未核验来源做风险提示 -->
                <template v-else-if="message.response.status === 'insufficient_evidence'">
                  <StateNotice
                    tone="warn"
                    :title="evidenceTitle(message.response)"
                    :description="evidenceDescription(message.response)"
                  />
                  <SourceList
                    v-if="message.response.sources.length"
                    :sources="message.response.sources"
                    heading="已找到但不可用的资料"
                  />
                </template>

                <!-- conflict：不给确定结论 -->
                <template v-else-if="message.response.status === 'conflict'">
                  <StateNotice
                    tone="warn"
                    title="资料来源存在冲突，暂不给确定结论"
                    description="同一事项存在口径不一致的通知，请联系责任部门确认后再办理。"
                  />
                  <SourceList :sources="message.response.sources" heading="存在冲突的来源" />
                </template>

                <!-- service_error：服务异常，可重试 -->
                <StateNotice
                  v-else
                  tone="error"
                  title="智能问答服务暂时不可用"
                  description="稍后再试一次；若持续失败，请稍后再来。"
                />
              </template>

              <StateNotice
                v-else-if="message.failure"
                tone="error"
                :title="message.failure.message"
                description="可以直接重试这一次提问。"
                action-label="重试"
                @action="retry(message.failure.retryText)"
              />
            </div>
          </article>

          <div v-if="isSending" class="typing-row" data-od-id="typing-indicator">
            <img class="message-avatar" src="/assets/brand-mark.webp" alt="" aria-hidden="true" width="256" height="256" decoding="async" />
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
                <span v-if="isSending" class="sr-only">正在发送</span>
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
            <AnimatedButton data-od-id="suggestion-repair" @click="useSuggestion('宿舍报修去哪办理？')">宿舍报修去哪办理？</AnimatedButton>
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

.follow-hint {
  margin: 8px 4px 0;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.6;
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

.send .i { width: 15px; height: 15px; }
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
  .send { height: var(--control-h); padding: 0 18px; }
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








