<script setup lang="ts">
import { ref } from 'vue'

import { submitFeedback } from '../api/client'
import type { FeedbackReasonCode } from '../api/client'
import { describeApiError } from '../data/answer-status'
import AppSelect from './AppSelect.vue'

/**
 * 反馈栏（契约 §4.5）：有帮助 / 没帮助 + 原因码 + 可选短评。
 * 「没帮助」才展开原因与短评；提交成功后收起为致谢文案，不再重复提交。
 */
const props = defineProps<{ conversationId: string }>()
const emit = defineEmits<{ (e: 'submitted'): void }>()

const REASON_LABELS: Record<FeedbackReasonCode, string> = {
  SOURCE_ERROR: '来源错误',
  INCOMPLETE_STEPS: '流程不完整',
  OUTDATED_CONTENT: '内容过期',
  OTHER: '其他',
}
const REASON_OPTIONS = Object.values(REASON_LABELS)

type Stage = 'idle' | 'detail' | 'sending' | 'done'

const stage = ref<Stage>('idle')
const helpful = ref(true)
const reasonLabel = ref<string>(REASON_LABELS.OUTDATED_CONTENT)
const comment = ref('')
const errorText = ref('')

function codeFromLabel(label: string): FeedbackReasonCode {
  const found = (Object.keys(REASON_LABELS) as FeedbackReasonCode[]).find(
    (key) => REASON_LABELS[key] === label,
  )
  return found ?? 'OTHER'
}

async function send(): Promise<void> {
  stage.value = 'sending'
  errorText.value = ''
  const text = comment.value.trim()
  try {
    await submitFeedback({
      conversation_id: props.conversationId,
      helpful: helpful.value,
      reason_code: helpful.value ? null : codeFromLabel(reasonLabel.value),
      comment: text ? text : null,
    })
    stage.value = 'done'
    emit('submitted')
  } catch (cause) {
    errorText.value = describeApiError(cause)
    stage.value = helpful.value ? 'idle' : 'detail'
  }
}

function pick(value: boolean): void {
  helpful.value = value
  errorText.value = ''
  if (value) {
    void send()
  } else {
    stage.value = 'detail'
  }
}

function cancel(): void {
  stage.value = 'idle'
  errorText.value = ''
}
</script>

<template>
  <div class="feedback-bar" data-od-id="feedback-bar">
    <p v-if="stage === 'done'" class="feedback-thanks" role="status">
      <svg class="i" aria-hidden="true"><use href="#i-check" /></svg>
      谢谢反馈，我们会据此更新知识库。
    </p>

    <template v-else>
      <div class="feedback-ask">
        <span class="feedback-question">这个回答有帮助吗？</span>
        <div class="feedback-actions">
          <button
            type="button"
            class="feedback-btn spark-button"
            :disabled="stage === 'sending'"
            data-od-id="feedback-helpful"
            @click="pick(true)"
          >有帮助</button>
          <button
            type="button"
            class="feedback-btn spark-button"
            :disabled="stage === 'sending'"
            data-od-id="feedback-not-helpful"
            @click="pick(false)"
          >没帮助</button>
        </div>
      </div>

      <form v-if="stage === 'detail' || stage === 'sending'" class="feedback-detail" @submit.prevent="send">
        <AppSelect v-model="reasonLabel" :options="REASON_OPTIONS" label="反馈原因" />
        <label class="comment-shell composer-shell">
          <span class="sr-only">补充说明</span>
          <input
            v-model="comment"
            type="text"
            maxlength="200"
            placeholder="可选：补充说明（200 字以内）"
            autocomplete="off"
            data-od-id="feedback-comment"
          />
        </label>
        <div class="feedback-detail-actions">
          <button type="submit" class="feedback-btn spark-button" :disabled="stage === 'sending'" data-od-id="feedback-submit">
            {{ stage === 'sending' ? '提交中…' : '提交反馈' }}
          </button>
          <button type="button" class="feedback-cancel" :disabled="stage === 'sending'" @click="cancel">取消</button>
        </div>
      </form>

      <p v-if="errorText" class="feedback-error" role="alert">{{ errorText }}</p>
    </template>
  </div>
</template>

<style scoped>
.feedback-bar {
  display: grid;
  gap: 10px;
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px dashed var(--border);
}

.feedback-ask {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 10px;
}

.feedback-question {
  color: var(--muted);
  font-size: 12.5px;
}

.feedback-actions {
  display: flex;
  gap: 8px;
}

.feedback-btn {
  min-height: 32px;
  padding: 0 13px;
  border: 1px solid var(--border);
  border-radius: var(--control-radius-pill);
  color: var(--fg);
  font-size: 12.5px;
}

.feedback-btn:hover:not(:disabled) {
  border-color: var(--fg);
}

.feedback-btn:disabled {
  cursor: not-allowed;
  opacity: .6;
}

.feedback-detail {
  display: grid;
  gap: 9px;
  padding: 11px;
  border: 1px solid var(--border);
  border-radius: 14px;
  background: color-mix(in srgb, var(--surface) 70%, transparent);
}

.comment-shell {
  display: flex;
  align-items: center;
  min-height: 42px;
  padding: 0 12px;
}

.comment-shell input {
  width: 100%;
  min-width: 0;
  border: 0;
  outline: 0;
  background: transparent;
  color: var(--fg);
  font: 400 13px/1.5 var(--font-body);
}

.comment-shell input::placeholder {
  color: var(--muted);
}

.feedback-detail-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.feedback-cancel {
  color: var(--muted);
  font-size: 12.5px;
}

.feedback-cancel:hover:not(:disabled) {
  color: var(--fg);
}

.feedback-thanks {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0;
  color: var(--muted);
  font-size: 12.5px;
}

.feedback-thanks .i {
  width: 14px;
  height: 14px;
  color: var(--accent);
}

.feedback-error {
  margin: 0;
  color: var(--danger);
  font-size: 12.5px;
}

@media (max-width: 700px) {
  .feedback-btn {
    min-height: var(--control-h);
  }

  .feedback-ask {
    align-items: flex-start;
  }
}
</style>
