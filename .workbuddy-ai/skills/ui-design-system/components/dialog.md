# 弹窗：通知中心

## 设计思路

**解决的问题**：一个"角色趴在卡片上 + 卡片自带三层光效"的模态弹窗，同时要满足
三条硬约束：① 光效不能被 `overflow:auto` 的卡片裁掉；② 角色图底部有 30px 透明
留白，直接用 `bottom` 对不齐卡片上沿；③ 打开时要能读屏、能 Esc 关、焦点要进去。

**视觉与交互意图**：
- 遮罩：半透明 + `backdrop-filter: blur(10px)`，点击自身关闭。
- 角色"趴"在卡片上边框上：用图片 alpha 包围盒下界（`579/610 = 0.94918`）对齐
  卡片上沿并轻微下压 6px——手部正好压在边框线上，头部完整露出在卡片之外。
- 卡片三层光效全部挂在**外层 frame** 上（环境弥散光 / 底部呼吸背光 / 旋转描边环），
  卡片本身只是不透明底，中心自然盖住光晕、只露出外圈 → 形成"光晕扩散"。
- 角色气泡：每次打开随机一句；鼠标移到某条通知上时切成该条对应的台词。

**适用场景**：全站唯一的模态弹窗。新增同类弹窗照抄这套结构与定位算法。

## 完整代码

### 模板

```vue
<div v-if="isNoticeOpen" class="notification-modal" role="presentation" @click.self="closeNotice">
  <div class="notification-dialog-shell">
    <div class="notification-character">
      <img src="/assets/notification-character.png" alt="">
      <div class="character-bubble notification-bubble" role="status" aria-live="polite">{{ noticeMessage }}</div>
    </div>

    <div class="notification-card-frame">
      <span class="notification-card-ring" aria-hidden="true"></span>
      <section class="notification-card" role="dialog" aria-modal="true" aria-labelledby="notification-title">
        <button ref="noticeCloseButton" type="button" class="notification-close" aria-label="关闭通知" @click="closeNotice">
          <span class="notification-close-mark" aria-hidden="true"></span>
        </button>
        <div class="notification-header">
          <span class="notification-kicker">校园通知</span>
          <h2 id="notification-title">通知中心</h2>
        </div>
        <ul class="notification-list">
          <li
            v-for="item in notifications" :key="item.id" class="notification-item"
            @mouseenter="noticeHover = item.bubble" @mouseleave="noticeHover = null"
          >
            <span class="notification-item-icon">
              <svg class="i" aria-hidden="true"><use :href="`#${item.icon}`" /></svg>
            </span>
            <span class="notification-item-body">
              <span class="notification-item-meta"><strong>{{ item.type }}</strong><time>{{ item.time }}</time></span>
              <b>{{ item.title }}</b>
              <span>{{ item.detail }}</span>
            </span>
          </li>
        </ul>
      </section>
    </div>
  </div>
</div>
```

### 脚本（打开 / 关闭 / 焦点 / Esc）

```ts
const isNoticeOpen = ref(false)
const noticeCloseButton = ref<HTMLButtonElement | null>(null)

/** 通知按类型配图标：同一列表里三条类型不同，全用铃铛就没有区分度了 */
const notifications = [
  { id: 'service-update', type: '服务更新', icon: 'i-doc', title: '学生证补办服务说明已更新',
    detail: '补办材料清单已在支持事项里更新。', time: '刚刚', bubble: '学生证说明更新啦，快看。' },
  { id: 'repair-maintenance', type: '系统提醒', icon: 'i-wrench', title: '宿舍报修平台今晚进行维护',
    detail: '维护时间为 22:00–23:00，期间提交可能稍有延迟。', time: '今天 18:30', bubble: '报修平台今晚要维护，别怪我。' },
  { id: 'campus-event', type: '校园公告', icon: 'i-megaphone', title: '本周校园服务开放日开始报名',
    detail: '可以在活动中心预约线下咨询。', time: '昨天', bubble: '开放日能线下咨询，随你啦。' },
]

const noticeGreetings = [
  '哼，才不是特意来念通知的。',
  '通知都替你看过了，快看嘛。',
  '有新消息哦，别装没看见。',
  '这些通知，我勉为其难念念。',
]
const noticeBase = ref(noticeGreetings[0])
const noticeHover = ref<string | null>(null)
const noticeMessage = computed(() => noticeHover.value ?? noticeBase.value)

function pickNoticeGreeting() {
  return noticeGreetings[Math.floor(Math.random() * noticeGreetings.length)]
}

// 顶栏铃铛的点击是委托到 document 上的（多个页面都有铃铛）
function onDocumentClick(event: MouseEvent) {
  const trigger = (event.target as Element | null)?.closest<HTMLElement>('[data-od-id*="notification-button"]')
  if (!trigger) return
  trigger.querySelector('.dot-badge')?.remove()
  trigger.setAttribute('aria-label', '通知（无未读）')
  trigger.setAttribute('data-tip', '通知（无未读）')
  isNoticeOpen.value = true
}

function closeNotice() { isNoticeOpen.value = false }

function onWindowKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && isNoticeOpen.value) closeNotice()
}

watch(isNoticeOpen, async (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
  if (!open) return
  noticeBase.value = pickNoticeGreeting()
  noticeHover.value = null
  await nextTick()
  noticeCloseButton.value?.focus()      // 焦点进弹窗
})

onMounted(() => {
  document.addEventListener('click', onDocumentClick)
  window.addEventListener('keydown', onWindowKeydown)
})
onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
  window.removeEventListener('keydown', onWindowKeydown)
  document.body.style.overflow = ''
})
```

### 样式

```css
.notification-modal {
  position: fixed;
  z-index: 30;
  inset: 0;
  display: grid;
  place-items: center;
  padding: clamp(24px, 6vw, 72px);
  background: color-mix(in srgb, var(--page-bg) 68%, #64748b 32% / 72%);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
}

.notification-dialog-shell {
  --char-width: min(380px, 66vw);
  --char-height: calc(var(--char-width) * 0.69318);
  --char-gap: 56px;
  --char-band: calc(var(--char-height) * 0.94918 - 6px + var(--char-gap));
  --notice-card-radius: 32px;
  position: relative;
  width: min(620px, 100%);
  padding-top: var(--char-band);
}

/* ── 通知卡片光效 ──────────────────────────────────────────────────────
   frame 只做定位与层叠上下文，真正画光的是三个层（从下往上）：
     ::before                  环境弥散光 —— 圆角矩形 + 柔和锥形双瓣，仅呼吸不旋转
     ::after                   底部呼吸背光 —— 径向渐变 + 动态模糊
     .notification-card-ring   旋转渐变描边环（叠在卡片之上，靠 mask 只留 2px 边）
   背光/环境光都在卡片之下，卡片不透明底自然盖住中心，只露出外圈 → 形成「光晕扩散」。
   注意：卡片自身是 overflow:auto 的滚动容器，光效绝不能挂在卡片内部，
   否则会被裁掉（abs 子元素还会跟着内容一起滚走），所以单独起一层 frame。 */
.notification-card-frame { position: relative; z-index: 1; width: 100%; isolation: isolate; }

/* 环境弥散光：内容恒定不变（没有随时间的渐变角度变化），
   所以 blur 只会被栅格化一次，动画只走 opacity → 全程合成层，不重绘。 */
.notification-card-frame::before {
  content: '';
  position: absolute;
  z-index: 0;
  inset: -18px;
  border-radius: calc(var(--notice-card-radius) + 18px);
  background: conic-gradient(from 208deg,
    transparent 0deg, var(--notice-aura-a) 58deg, transparent 148deg,
    var(--notice-aura-b) 232deg, transparent 322deg);
  filter: blur(26px);
  opacity: .6;
  pointer-events: none;
  animation: notice-aura-breathe 7.6s ease-in-out infinite;
}

/* 底部呼吸背光：盒子比卡片宽 4%，向下溢出 70px，
   亮芯落在卡片下沿附近（渐变 66% 处），只有露在卡片外的部分可见。
   --notice-glow-fade 是同色相 alpha=0，避免插值出灰边。 */
.notification-card-frame::after {
  content: '';
  position: absolute;
  z-index: 0;
  left: -4%;
  right: -4%;
  bottom: -70px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(62% 100% at 50% 66%,
    var(--notice-glow-core) 0%, var(--notice-glow-halo) 42%, var(--notice-glow-fade) 76%);
  filter: blur(30px);
  opacity: .72;
  pointer-events: none;
  transform-origin: 50% 100%;
  animation: notice-glow-breathe 6.4s ease-in-out infinite;
  will-change: opacity, transform, filter;
}

/* 旋转描边环：外层 inset:-2px / padding:2px + xor 掩膜 = 只保留 2px 宽的边带
   内层 ::before 是一个 300% 见方的 conic 渐变方块，用 transform:rotate 旋转 ——
   纯合成层动画，不重绘渐变；旋转的是方块而不是渐变角度，
   所以掩膜（在父层坐标系里）不会跟着转，边带形状始终贴合卡片圆角。
   300% 是安全余量：只要卡片高宽比 < 2.83，方块任意角度都能盖满父层。
   overflow:hidden 把栅格范围收在卡片尺寸内，避免按 9 倍面积去栅格。 */
.notification-card-ring {
  position: absolute;
  z-index: 2;
  inset: -2px;
  padding: 2px;
  border-radius: calc(var(--notice-card-radius) + 2px);
  overflow: hidden;
  pointer-events: none;
  -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
  mask-composite: exclude;
}
.notification-card-ring::before {
  content: '';
  position: absolute;
  left: 50%;
  top: 50%;
  width: 300%;
  aspect-ratio: 1;
  background:
    conic-gradient(from 0deg,
      var(--notice-ring-fade) 0deg, var(--notice-ring-tail) 30deg,
      var(--notice-ring-fade) 118deg, var(--notice-ring-fade) 360deg),
    conic-gradient(from 0deg,
      var(--notice-ring-fade) 0deg, var(--notice-ring-hot) 50deg,
      var(--notice-ring-bright) 68deg, var(--notice-ring-hot) 88deg,
      var(--notice-ring-fade) 132deg, var(--notice-ring-fade) 360deg);
  transform: translate(-50%, -50%) rotate(0deg);
  will-change: transform;
  animation: notice-ring-spin 6.5s linear infinite;
}
@keyframes notice-ring-spin {
  from { transform: translate(-50%, -50%) rotate(0deg); }
  to   { transform: translate(-50%, -50%) rotate(360deg); }
}
@keyframes notice-aura-breathe { 0%, 100% { opacity: .44; } 50% { opacity: .76; } }
@keyframes notice-glow-breathe {
  0%, 100% { opacity: .52; filter: blur(24px); transform: scale(.94, 1); }
  50% { opacity: .88; filter: blur(38px); transform: scale(1.04, 1.12); }
}

.notification-card {
  position: relative;
  z-index: 1;
  width: 100%;
  max-height: min(720px, calc(100vh - 48px));
  overflow: auto;                      /* 滚动容器：光效不能放进来 */
  padding: clamp(30px, 4vw, 44px) clamp(22px, 5vw, 48px) 28px;
  border: 1px solid color-mix(in srgb, var(--border) 72%, white 28%);
  border-radius: var(--notice-card-radius);
  background: linear-gradient(145deg,
    color-mix(in srgb, var(--surface) 96%, white 4%),
    color-mix(in srgb, var(--surface) 90%, var(--accent-soft) 10%));
  box-shadow:
    0 26px 64px color-mix(in srgb, #172033 24%, transparent),
    0 8px 26px color-mix(in srgb, var(--fg) 9%, transparent);
  isolation: isolate;
}
.notification-card::before {
  content: '';
  position: absolute;
  z-index: -1;
  inset: 8px;
  border-radius: calc(var(--notice-card-radius) - 6px);
  border: 1px solid color-mix(in srgb, var(--accent) 14%, transparent);
  pointer-events: none;
}

/* 角色「趴」在卡片上边框上：0.94918 = 图片 alpha 包围盒下界 579 / 图片高 610，
   即「可视内容底边」在图片高度中的占比；用它对齐卡片上沿并轻微下压 6px，
   手部就正好压在边框线上，头部完整露出在卡片之外。
   注意不能直接用 img 的 bottom —— 图片底部还有 30px 透明留白。
   --char-gap 是角色顶部到 shell 顶部的留白，专门给上方的消息气泡用。 */
.notification-character {
  position: absolute;
  z-index: 2;
  top: var(--char-gap);
  left: 50%;
  width: var(--char-width);
  transform: translateX(-50%);
  pointer-events: none;
}
/* 气泡视觉样式来自全局 .character-bubble，这里只声明摆放位置：
   居中对齐角色，贴在角色头顶上方 6px，箭头垂直向下指向头部。 */
.notification-bubble { --bubble-rest: translateX(-50%); left: 50%; bottom: calc(100% + 6px); }
.notification-character img { display: block; width: 100%; height: auto; }

.notification-close {
  position: absolute;
  z-index: 5;
  top: 20px;
  right: 20px;
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border: 1px solid var(--border);
  border-radius: 50%;
  background: color-mix(in srgb, var(--surface) 82%, transparent);
  color: var(--muted);
}
.notification-close:hover { background: var(--accent-soft); color: var(--fg); }
.notification-close-mark { position: relative; width: 19px; height: 19px; display: block; }
.notification-close-mark::before,
.notification-close-mark::after {
  content: "";
  position: absolute;
  left: 8px;
  top: -1px;
  width: 3px;
  height: 21px;
  border-radius: 3px;
  background: currentColor;
  transform: rotate(45deg);
}
.notification-close-mark::after { transform: rotate(-45deg); }

.notification-header { position: relative; z-index: 1; text-align: center; }
.notification-kicker {
  display: inline-flex;
  padding: 5px 9px;
  border-radius: 999px;
  background: var(--accent-soft);
  color: var(--accent);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: .14em;
}
.notification-header h2 {
  margin: 12px 0 7px;
  font-family: var(--font-display);
  font-size: clamp(25px, 4vw, 34px);
  font-weight: 900;
  letter-spacing: -.03em;
}

.notification-list { position: relative; z-index: 1; display: grid; gap: 10px; margin: 26px 0 0; padding: 0; list-style: none; }
.notification-item {
  display: flex;
  gap: 12px;
  padding: 14px;
  border: 1px solid color-mix(in srgb, var(--border) 78%, transparent);
  border-radius: 17px;
  background: color-mix(in srgb, var(--surface) 72%, transparent);
}
.notification-item-icon {
  display: grid;
  place-items: center;
  width: 34px;
  height: 34px;
  flex: 0 0 auto;
  border-radius: 11px;
  background: var(--accent-soft);
  color: var(--accent);
}
.notification-item-icon .i { width: 16px; height: 16px; }
.notification-item-body { display: grid; min-width: 0; gap: 3px; line-height: 1.45; }
.notification-item-meta { display: flex; gap: 9px; align-items: center; color: var(--muted); font-size: 11px; }
.notification-item-meta strong { color: var(--accent); font-weight: 700; }
.notification-item-meta time { margin-left: auto; white-space: nowrap; }
.notification-item-body b { font-size: 13px; font-weight: 600; }
.notification-item-body > span:last-child { color: var(--muted); font-size: 12px; }

@media (max-width: 700px) {
  .notification-modal { padding: 18px; }
  .notification-dialog-shell { --char-width: min(270px, 72vw); --notice-card-radius: 25px; }
  .notification-card { max-height: calc(100vh - 36px); padding: 32px 16px 22px; }
  .notification-close { top: 14px; right: 14px; width: 36px; height: 36px; }
  .notification-header h2 { font-size: 27px; }
  .notification-item { padding: 12px; }
  .notification-item-body b { font-size: 12.5px; }
  .notification-item-body > span:last-child { font-size: 11.5px; }
  /* 窄屏收敛光效：背光/环境光收窄下压，避免糊满整屏，也省掉不必要的模糊面积 */
  .notification-card-frame::before { inset: -12px; border-radius: calc(var(--notice-card-radius) + 12px); filter: blur(18px); }
  .notification-card-frame::after { left: -2%; right: -2%; bottom: -52px; height: 160px; filter: blur(24px); }
  @keyframes notice-glow-breathe {
    0%, 100% { opacity: .52; filter: blur(20px); transform: scale(.94, 1); }
    50% { opacity: .86; filter: blur(30px); transform: scale(1.03, 1.1); }
  }
}

/* 无障碍：关闭全部光效动画，但保留静止的描边环与背光（仍是完整的视觉，只是不动） */
@media (prefers-reduced-motion: reduce) {
  .notification-card-frame::before,
  .notification-card-frame::after,
  .notification-card-ring::before { animation: none; }
  .notification-card-frame::after { opacity: .6; filter: blur(28px); transform: none; }
}
```

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **尺寸** | shell `width: min(620px,100%)`；角色宽 `--char-width: min(380px,66vw)`（窄屏 `min(270px,72vw)`）；卡片圆角 32px（窄屏 25px）；`max-height: min(720px, calc(100vh - 48px))`。 |
| **状态 · 打开** | 遮罩淡入（由 Vue 挂载直接呈现，无过渡类）；焦点移到关闭按钮；`document.body.style.overflow = 'hidden'`。 |
| **状态 · 关闭** | 关闭按钮点击 / Esc / 点击遮罩（`@click.self`）。关闭后恢复 body 滚动。 |
| **状态 · 未读** | 铃铛上的 `.dot-badge` 打开时 `remove()`，`aria-label` 与 `data-tip` 同步改成"通知（无未读）"。 |
| **角色台词** | 打开时随机一句（`noticeGreetings`）；hover 某条通知时切到该条的 `bubble`；移出恢复。 |
| **主题** | 全部走 `--notice-*` / `--surface` / `--accent-*`，明暗各一套光效变量。 |
| **移动端** | 光效收敛：`inset:-12px` + `blur(18px)`、背光 `bottom:-52px` + `blur(24px)`，呼吸幅度同步减小。 |
| **reduced-motion** | 三层动画全停，但保留静止的环与背光（`opacity:.6; blur(28px)`）——**是"不动"，不是"消失"**。 |

## 使用注意事项

**可访问性**
- `role="dialog"` + `aria-modal="true"` + `aria-labelledby`（指向标题 id）。
- 打开后**必须把焦点移进弹窗**（当前实现移到关闭按钮），关闭后应把焦点还给触发
  元素（当前未实现，可在 `closeNotice` 里补）。
- Esc 关闭挂 `window` 的 `keydown`；组件卸载时务必解绑并恢复 `body.style.overflow`。
- 角色气泡是 `role="status" aria-live="polite"`——它会在 hover 时频繁变化，
  用 `polite` 而不是 `assertive`，避免打断读屏。
- 角色图 `alt=""`（纯装饰）+ `pointer-events: none`。
- **当前实现没有焦点陷阱**（Tab 会跑出弹窗）。若要补，用 `inert` 或在 keydown 里
  做 Tab 循环。

**性能**
- 环境弥散光 `::before` 的 conic-gradient 内容恒定 → blur 只栅格化一次，
  动画只走 `opacity`（合成层）。**不要改成动态渐变角度**，否则每帧重绘。
- 描边环转的是 `transform: rotate`（合成层），**不是** conic 的角度。
  用 `@property` 动角度会逐帧重绘渐变，实测明显掉帧。
- 描边环的 `300%` 见方是安全余量（卡片高宽比 < 2.83 都盖得住），配
  `overflow:hidden` 把栅格范围收在卡片尺寸内，避免按 9 倍面积栅格。
- 所有光效层都要 `pointer-events: none`（实测否则会挡住关闭按钮与列表 hover）。
- `will-change` 只加在真正动的三层上，不要到处加。

**常见误用**
1. **把光效挂进 `.notification-card` 内部** —— 卡片是 `overflow:auto`，一定被裁，
   而且 abs 子元素会跟着内容滚走。必须走 frame。
2. **用 `img` 的 `bottom` 对齐卡片上沿** —— 图片底部有 30px 透明留白，会浮空。
   必须用 alpha 包围盒占比 `0.94918` 算。
3. **关闭时不恢复 `body.style.overflow`** —— 页面永久锁死滚动。
4. **`@click` 挂在遮罩上而不是 `@click.self`** —— 点卡片内部也会关闭。
5. **reduced-motion 下把背光整层 `display:none`** —— 用户明确要求"视觉仍完整"，
   只停动画。
