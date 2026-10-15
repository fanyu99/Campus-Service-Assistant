<script setup lang="ts">
/**
 * 通知中心弹窗（含角色与三层光效）。
 *
 * 三条硬约束（踩过，别改回去）：
 *   1. 光效绝不能挂在 .notification-card 内部 —— 卡片是 overflow:auto 的滚动容器，
 *      挂在里面会被裁掉，abs 子元素还会跟着内容一起滚走。所以单独起一层 frame。
 *   2. 角色图底部有 30px 透明留白，不能用 img 的 bottom 对齐卡片上沿，
 *      必须用 alpha 包围盒占比 0.94918（579 / 610）算。
 *   3. 打开后焦点必须进弹窗；Esc 与点遮罩都要能关；关闭要恢复 body 滚动。
 *
 * 依赖：
 *   - src/styles/theme.css 的 --notice-* 变量 + .character-bubble
 *   - AppSprite 提供的 #i-doc / #i-wrench / #i-megaphone / #i-bell
 */
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

const props = defineProps<{
  open: boolean
  notifications: {
    id: string
    type: string
    icon: string
    title: string
    detail: string
    time: string
    bubble: string
  }[]
}>()

const emit = defineEmits<{ (e: 'close'): void }>()

const closeButton = ref<HTMLButtonElement | null>(null)

/** 每次打开随机一句；鼠标移到某条通知上时切成该条对应的台词 */
const greetings = [
  '哼，才不是特意来念通知的。',
  '通知都替你看过了，快看嘛。',
  '有新消息哦，别装没看见。',
  '这些通知，我勉为其难念念。',
]
const base = ref(greetings[0])
const hover = ref<string | null>(null)
const message = computed(() => hover.value ?? base.value)

function pickGreeting() {
  return greetings[Math.floor(Math.random() * greetings.length)]
}

function close() {
  emit('close')
}

function onKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && props.open) close()
}

watch(
  () => props.open,
  async (open) => {
    document.body.style.overflow = open ? 'hidden' : ''
    if (!open) return
    base.value = pickGreeting()
    hover.value = null
    await nextTick()
    closeButton.value?.focus()
  },
)

onMounted(() => window.addEventListener('keydown', onKeydown))
onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  document.body.style.overflow = ''
})
</script>

<template>
  <div v-if="open" class="notification-modal" role="presentation" @click.self="close">
    <div class="notification-dialog-shell">
      <!-- 角色「趴」在卡片上边框上 -->
      <div class="notification-character">
        <img src="/assets/notification-character.png" alt="">
        <div class="character-bubble notification-bubble" role="status" aria-live="polite">{{ message }}</div>
      </div>

      <!-- frame 承载三层光效；卡片只负责内容 -->
      <div class="notification-card-frame">
        <span class="notification-card-ring" aria-hidden="true"></span>
        <section class="notification-card" role="dialog" aria-modal="true" aria-labelledby="notification-title">
          <button ref="closeButton" type="button" class="notification-close" aria-label="关闭通知" @click="close">
            <span class="notification-close-mark" aria-hidden="true"></span>
          </button>

          <div class="notification-header">
            <span class="notification-kicker">校园通知</span>
            <h2 id="notification-title">通知中心</h2>
          </div>

          <ul class="notification-list">
            <li
              v-for="item in notifications"
              :key="item.id"
              class="notification-item"
              @mouseenter="hover = item.bubble"
              @mouseleave="hover = null"
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
</template>

<style scoped>
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
  /* 0.94918 = 图片 alpha 包围盒下界 579 / 图片高 610，即「可视内容底边」在图片高度中的占比。
     用它对齐卡片上沿并下压 6px，手部正好压在边框线上，头部完整露出在卡片之外。
     --char-gap 是角色顶部到 shell 顶部的留白，专门给上方的消息气泡用。 */
  --char-band: calc(var(--char-height) * 0.94918 - 6px + var(--char-gap));
  --notice-card-radius: 32px;
  position: relative;
  width: min(620px, 100%);
  padding-top: var(--char-band);
}

/* ── 光效三层全部挂在 frame 上 ──────────────────────────────────────────
     ::before                  环境弥散光（conic 双瓣，只呼吸 opacity，内容恒定）
     ::after                   底部呼吸背光（径向渐变，opacity+scale+blur 三联动）
     .notification-card-ring   旋转渐变描边环（mask 只留 2px 边，转的是方块不是角度） */
.notification-card-frame { position: relative; z-index: 1; width: 100%; isolation: isolate; }

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
  /* 300% 是安全余量：只要卡片高宽比 < 2.83，方块任意角度都能盖满父层。
     配 overflow:hidden 把栅格范围收在卡片尺寸内，避免按 9 倍面积去栅格。 */
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
@keyframes notice-ring-spin { from { transform: translate(-50%, -50%) rotate(0deg); } to { transform: translate(-50%, -50%) rotate(360deg); } }
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
  overflow: auto;
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

.notification-character {
  position: absolute;
  z-index: 2;
  top: var(--char-gap);
  left: 50%;
  width: var(--char-width);
  transform: translateX(-50%);
  pointer-events: none;
}
/* 气泡视觉来自全局 .character-bubble，这里只声明位置 */
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
  /* 窄屏收敛光效：避免糊满整屏，也省掉不必要的模糊面积 */
  .notification-card-frame::before { inset: -12px; border-radius: calc(var(--notice-card-radius) + 12px); filter: blur(18px); }
  .notification-card-frame::after { left: -2%; right: -2%; bottom: -52px; height: 160px; filter: blur(24px); }
  @keyframes notice-glow-breathe {
    0%, 100% { opacity: .52; filter: blur(20px); transform: scale(.94, 1); }
    50% { opacity: .86; filter: blur(30px); transform: scale(1.03, 1.1); }
  }
}

/* 无障碍：关闭全部光效动画，但保留静止的描边环与背光（视觉仍完整，只是不动） */
@media (prefers-reduced-motion: reduce) {
  .notification-card-frame::before,
  .notification-card-frame::after,
  .notification-card-ring::before { animation: none; }
  .notification-card-frame::after { opacity: .6; filter: blur(28px); transform: none; }
}
</style>
