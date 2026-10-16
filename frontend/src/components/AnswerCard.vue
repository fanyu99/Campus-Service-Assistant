<script setup lang="ts">
import type { AnswerCard } from '../api/client'

/**
 * 结构化办事卡片（契约 §3.3 的 answer 对象）。
 * 空字段直接不渲染该段，避免出现「无内容的标题」。
 */
defineProps<{ card: AnswerCard }>()
</script>

<template>
  <article class="answer-card" data-od-id="answer-card">
    <header class="card-head">
      <h3>{{ card.title }}</h3>
      <p v-if="card.summary">{{ card.summary }}</p>
    </header>

    <section v-if="card.eligibility.length" class="card-section">
      <h4><svg class="i" aria-hidden="true"><use href="#i-check" /></svg>办理条件</h4>
      <ul>
        <li v-for="(line, index) in card.eligibility" :key="index">{{ line }}</li>
      </ul>
    </section>

    <section v-if="card.materials.length" class="card-section">
      <h4><svg class="i" aria-hidden="true"><use href="#i-doc" /></svg>所需材料</h4>
      <ul>
        <li v-for="(line, index) in card.materials" :key="index">{{ line }}</li>
      </ul>
    </section>

    <section v-if="card.steps.length" class="card-section">
      <h4><svg class="i" aria-hidden="true"><use href="#i-list" /></svg>办理步骤</h4>
      <ol>
        <li v-for="(line, index) in card.steps" :key="index">{{ line }}</li>
      </ol>
    </section>

    <dl
      v-if="card.location || card.deadline || card.contacts.length"
      class="card-facts"
      data-od-id="answer-card-facts"
    >
      <div v-if="card.location">
        <dt>办理地点</dt>
        <dd>{{ card.location }}</dd>
      </div>
      <div v-if="card.deadline">
        <dt>截止日期</dt>
        <dd>{{ card.deadline }}</dd>
      </div>
      <div v-if="card.contacts.length">
        <dt>联系方式</dt>
        <dd>{{ card.contacts.join('、') }}</dd>
      </div>
    </dl>

    <ul v-if="card.warnings.length" class="card-warnings" data-od-id="answer-card-warnings">
      <li v-for="(line, index) in card.warnings" :key="index">
        <svg class="i" aria-hidden="true"><use href="#i-help" /></svg>
        <span>{{ line }}</span>
      </li>
    </ul>
  </article>
</template>

<style scoped>
.answer-card {
  display: grid;
  gap: 16px;
  padding: 16px 18px 18px;
  border: 1px solid var(--border);
  border-radius: 4px 18px 18px 18px;
  background: var(--surface);
  color: var(--fg);
}

.card-head {
  display: grid;
  gap: 6px;
}

.card-head h3 {
  margin: 0;
  font-family: var(--font-display);
  font-size: 17px;
  font-weight: 900;
  letter-spacing: 0;
}

.card-head p {
  margin: 0;
  color: var(--muted);
  font-size: 13px;
  line-height: 1.7;
}

.card-section {
  display: grid;
  gap: 8px;
}

.card-section h4 {
  display: flex;
  align-items: center;
  gap: 7px;
  margin: 0;
  color: var(--fg);
  font-size: 13px;
  font-weight: 600;
}

.card-section h4 .i {
  width: 15px;
  height: 15px;
  color: var(--accent);
}

.card-section ul,
.card-section ol {
  display: grid;
  gap: 6px;
  margin: 0;
  padding-left: 22px;
  color: var(--fg);
  font-size: 13.5px;
  line-height: 1.75;
}

.card-section li::marker {
  color: var(--muted);
}

.card-facts {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 12px 14px;
  border: 1px dashed var(--border);
  border-radius: 12px;
}

.card-facts div {
  display: grid;
  grid-template-columns: 72px minmax(0, 1fr);
  gap: 10px;
  align-items: baseline;
}

.card-facts dt {
  color: var(--muted);
  font-size: 12px;
}

.card-facts dd {
  margin: 0;
  color: var(--fg);
  font-size: 13px;
  line-height: 1.7;
  word-break: break-word;
}

.card-warnings {
  display: grid;
  gap: 7px;
  margin: 0;
  padding: 12px 14px;
  border-radius: 12px;
  background: color-mix(in srgb, var(--danger) 9%, transparent);
  list-style: none;
}

.card-warnings li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--fg);
  font-size: 12.5px;
  line-height: 1.7;
}

.card-warnings .i {
  width: 14px;
  height: 14px;
  flex: 0 0 auto;
  margin-top: 3px;
  color: var(--danger);
}

@media (max-width: 700px) {
  .answer-card {
    padding: 14px 14px 16px;
  }

  .card-facts div {
    grid-template-columns: 1fr;
    gap: 2px;
  }
}
</style>
