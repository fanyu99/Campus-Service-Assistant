# 对话页布局

## 设计思路

**解决的问题**：对话页要"消息区滚、输入区不动"——这与 `app-shell.md` 的通用规则
（页面级滚动交给 `.main`）**正好相反**。是全站唯一的有意例外。

**视觉与交互意图**：
- `.chat-main { overflow: hidden }` 钉死页面；
- `.message-list { flex: 1; overflow-y: auto }` 独立滚动；
- composer 固定在底部（`flex: 0 0 auto`，由 `.composer-wrap` 承载）。
- 消息最大宽度 82%（移动端 92%），左右分列：助手在左（带头像）、用户在右。

**适用场景**：对话页，以及任何"顶部固定 + 中间滚动 + 底部固定输入"的布局。

## 完整代码

### 结构

```vue
<main class="main chat-main" data-od-id="chat-main">
  <header class="topbar" data-od-id="chat-header">…</header>

  <section class="chat-workspace" data-od-id="conversation-workspace">
    <div class="chat-column">
      <div class="chat-heading" data-od-id="chat-heading"><h1>咨询校园事务</h1></div>

      <div ref="messageList" class="message-list" role="log" aria-live="polite" data-od-id="message-list">
        <div v-if="!messages.length" class="empty-state" data-od-id="empty-conversation">
          <p>还没有对话</p>
          <p>在下方输入框写下问题，也可以直接选一个示例</p>
        </div>

        <article
          v-for="message in messages" :key="message.id"
          class="message-row" :class="`is-${message.role}`"
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
            <div class="loading-animation loading-animation--assistant" aria-hidden="true">…</div>
          </div>
        </div>
      </div>

      <div class="composer-wrap chat-composer-wrap" data-od-id="chat-composer-wrap">
        <form class="composer composer-shell" :class="{ 'is-invalid': isError }" novalidate @submit.prevent="submitQuestion">…</form>
        <p class="composer-msg" :class="{ 'is-error': isError }" role="status" aria-live="polite">{{ status }}</p>
        <div class="chips" data-od-id="suggestion-list">
          <AnimatedButton @click="useSuggestion('学生证丢了怎么补办？')">学生证丢了怎么补办？</AnimatedButton>
          …
        </div>
      </div>
    </div>
  </section>
</main>
```

### 样式

```css
/* 唯一的有意例外：页面不滚，消息区自己滚 */
.chat-main { min-height: 0; overflow: hidden; }

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
  min-height: 0;               /* 允许 message-list 收缩 */
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
  flex: 1;                     /* 吃掉剩余高度 */
  flex-direction: column;
  gap: 20px;
  min-height: 0;               /* 关键：否则不会收缩，滚动失效 */
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
.empty-state p { margin: 0; color: var(--muted); font-size: 13px; }

.message-row,
.typing-row {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  max-width: 82%;
  user-select: text;           /* body 全局禁选，消息必须恢复 */
  -webkit-user-select: text;
}
.message-row.is-user { align-self: flex-end; justify-content: flex-end; }
.message-row.is-assistant,
.typing-row { align-self: flex-start; }

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

.message-content { min-width: 0; }
.message-row.is-user .message-content { display: flex; flex-direction: column; align-items: flex-end; }

.message-meta { display: flex; align-items: baseline; gap: 8px; margin: 0 4px 6px; color: var(--muted); font-size: 11px; }
.message-meta strong { color: var(--fg); font-size: 12px; font-weight: 600; }

.message-bubble {
  margin: 0;
  padding: 12px 15px;
  border: 1px solid var(--border);
  border-radius: 4px 16px 16px 16px;      /* 左上小角 = 指向头像 */
  background: var(--surface);
  color: var(--fg);
  font-size: 14px;
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}
.message-row.is-user .message-bubble {
  border-color: transparent;
  border-radius: 16px 4px 16px 16px;      /* 右上小角镜像 */
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

.chat-composer-wrap {
  position: relative;
  z-index: 2;
  width: min(660px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chips { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }

@media (max-width: 700px) {
  /* 移动端回到文档滚动：放开页面级限制 */
  .chat-main { min-height: 100svh; overflow: visible; }
  .chat-workspace { min-height: calc(100svh - 74px); padding: 8px 0 18px; overflow: visible; }
  .chat-heading { gap: 12px; padding: 12px 0 10px; }
  .chat-heading h1 { font-size: 24px; }
  .message-list { padding-inline: 0; }
  .message-row,
  .typing-row { max-width: 92%; }
  .chat-composer-wrap { width: 100%; }
  .composer { padding: 13px 13px 11px; border-radius: 22px; }
  .composer textarea { font-size: 16px; }
  .send { height: 44px; padding: 0 18px; }
  /* 建议 chips 改横向滚动：AnimatedButton 有 flex:0 0 auto，不会被压扁 */
  .chips { justify-content: flex-start; overflow-x: auto; flex-wrap: nowrap; scrollbar-width: none; padding-block: 3px; }
  .chips::-webkit-scrollbar { display: none; }
}
```

### 滚动到最新

```ts
function scrollToLatest() {
  nextTick(() => {
    const el = messageList.value
    if (el) el.scrollTop = el.scrollHeight
  })
}
// 发送后、收到回复后各调一次
```

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **消息宽度** | 桌面 `max-width: 82%`；移动端 `92%`。 |
| **气泡圆角** | 助手 `4px 16px 16px 16px`；用户 `16px 4px 16px 16px`（小角指向说话者）。 |
| **用户气泡** | `--accent` 底 + `--page-bg` 字 + `border-color: transparent`。 |
| **加载态** | `.typing-row` + `.loading-animation--assistant`；发送按钮同时进 `.is-loading` + `disabled`。 |
| **空态** | 撑满型：`flex:1; min-height:230px` 居中两行文字。 |
| **矮视口** | `.message-list` 自然收缩；没有额外的矮视口规则（因为它已经是可滚容器）。 |
| **移动端** | 页面放开 `overflow: visible`，走文档滚动；`min-height: 100svh`；chips 横向滚动。 |
| **主题** | 全变量；用户气泡的 `--page-bg` 文字在深色主题下变成深色字压在 `--accent` 上（**注意：深色主题 `--accent` 提到 L62%，白/黑字对比度需实测**）。 |

## 使用注意事项

**可访问性**
- `.message-list` 用 `role="log" aria-live="polite"`——新消息会被读屏播报。
- 消息区**必须 `user-select: text`**（`body` 全局禁选了）。
- 助手头像 `alt=""` + `aria-hidden="true"`（纯装饰，说话者已在 `.message-meta` 里
  用文字给出）。
- 空态不需要 `role="status"`（它是静态的）。

**性能**
- `.chat-column` / `.message-list` 都要 `min-height: 0`，缺一个滚动就失效。
- 消息多的时候没有做虚拟滚动。当前量级（几十条）没问题；超过几百条要加
  虚拟列表或分页。

**常见误用**
1. **照抄 `content-page-layout.md` 的 `overflow-y: auto` 到 `.chat-main`** ——
   会变成"整页滚 + 消息区也滚"的双滚动条。对话页必须 `overflow: hidden`。
2. **`.message-list` 忘了 `flex: 1`** —— 消息区不占位，composer 会被顶到顶部。
3. **移动端不放开 `overflow`** —— 小屏上出现内部小滚动窗，且软键盘弹出时
   composer 会被遮住。
4. **气泡圆角不镜像** —— 用户消息看起来也像助手发的。
5. **发送后不滚到底** —— 新消息在视野外。发送后与收到回复后各调一次
   `scrollToLatest()`（因为 DOM 更新在 nextTick）。
