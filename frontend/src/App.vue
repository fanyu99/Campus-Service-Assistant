<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import AppSidebar from './components/AppSidebar.vue'
import AppSprite from './components/AppSprite.vue'
import ParticleBackground from './components/particle-background/ParticleBackground.vue'
import { useTheme } from './composables/useTheme'

useTheme()

const isNoticeOpen = ref(false)
const noticeCloseButton = ref<HTMLButtonElement | null>(null)
const notifications = [
  { id: 'service-update', type: '服务更新', title: '学生证补办服务说明已更新', detail: '现在可以在服务中心直接查看材料清单。', time: '刚刚',
    bubble: '学生证说明更新啦，快看。' },
  { id: 'repair-maintenance', type: '系统提醒', title: '宿舍报修平台今晚进行维护', detail: '维护时间为 22:00–23:00，期间提交可能稍有延迟。', time: '今天 18:30',
    bubble: '报修平台今晚要维护，别怪我。' },
  { id: 'campus-event', type: '校园公告', title: '本周校园服务开放日开始报名', detail: '欢迎前往活动中心预约线下咨询。', time: '昨天',
    bubble: '开放日能线下咨询，随你啦。' },
]

/** 通知弹窗角色气泡：每次打开随机一句；鼠标移到某条通知上时切成该条对应的台词 */
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

function onDocumentClick(event: MouseEvent) {
  const target = event.target as Element | null
  const trigger = target?.closest<HTMLElement>('[data-od-id*="notification-button"]')
  if (!trigger) return

  trigger.querySelector('.dot-badge')?.remove()
  trigger.setAttribute('aria-label', '通知（无未读）')
  trigger.setAttribute('data-tip', '通知（无未读）')
  isNoticeOpen.value = true
}

function closeNotice() {
  isNoticeOpen.value = false
}

function onWindowKeydown(event: KeyboardEvent) {
  if (event.key === 'Escape' && isNoticeOpen.value) closeNotice()
}

watch(isNoticeOpen, async (open) => {
  document.body.style.overflow = open ? 'hidden' : ''
  if (!open) return
  noticeBase.value = pickNoticeGreeting()
  noticeHover.value = null
  await nextTick()
  noticeCloseButton.value?.focus()
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
</script>

<template>
  <AppSprite />
  <ParticleBackground
    :particle-count="82"
    :petal-count="72"
    :heart-scale="62"
    :repulsion-strength="0.86"
    :heart-force-radius="1.22"
    :gravity="0.012"
    :wind-strength="0.022"
    :drift-strength="0.28"
    :trail-strength="0.26"
    :trail-limit="120"
    :waterline-ratio="0.88"
    :water-depth="0.06"
    :ripple-limit="54"
    :opacity="0.82"
  />
  <div class="app-shell">
    <AppSidebar />
    <Transition name="route" mode="out-in">
      <router-view v-slot="{ Component, route }">
        <component :is="Component" :key="route.fullPath" />
      </router-view>
    </Transition>
  </div>

  <div v-if="isNoticeOpen" class="notification-modal" role="presentation" @click.self="closeNotice">
    <div class="notification-dialog-shell">
      <div class="notification-character">
        <img src="/assets/notification-character.png" alt="">
        <div class="character-bubble notification-bubble" role="status" aria-live="polite">{{ noticeMessage }}</div>
      </div>

      <section class="notification-card" role="dialog" aria-modal="true" aria-labelledby="notification-title">
        <button ref="noticeCloseButton" type="button" class="notification-close" aria-label="关闭通知" @click="closeNotice">
          <span class="notification-close-mark" aria-hidden="true"></span>
        </button>
        <div class="notification-header">
          <span class="notification-kicker">CAMPUS UPDATE</span>
          <h2 id="notification-title">通知中心</h2>
        </div>
        <ul class="notification-list">
          <li
            v-for="item in notifications"
            :key="item.id"
            class="notification-item"
            @mouseenter="noticeHover = item.bubble"
            @mouseleave="noticeHover = null"
          >
            <span class="notification-item-icon"><svg class="i" aria-hidden="true"><use href="#i-bell"/></svg></span>
            <span class="notification-item-body"><span class="notification-item-meta"><strong>{{ item.type }}</strong><time>{{ item.time }}</time></span><b>{{ item.title }}</b><span>{{ item.detail }}</span></span>
          </li>
        </ul>
      </section>
    </div>
  </div>
</template>
<style scoped>
.notification-modal{position:fixed;z-index:30;inset:0;display:grid;place-items:center;padding:clamp(24px,6vw,72px);background:color-mix(in srgb,var(--page-bg) 68%,#64748b 32% / 72%);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px)}
.notification-dialog-shell{--char-width:min(380px,66vw);--char-height:calc(var(--char-width) * 0.69318);--char-gap:56px;--char-band:calc(var(--char-height) * 0.94918 - 6px + var(--char-gap));position:relative;width:min(620px,100%);padding-top:var(--char-band)}
.notification-card{position:relative;z-index:1;width:100%;max-height:min(720px,calc(100vh - 48px));overflow:auto;padding:clamp(30px,4vw,44px) clamp(22px,5vw,48px) 28px;border:1px solid color-mix(in srgb,var(--border) 72%,white 28%);border-radius:32px;background:linear-gradient(145deg,color-mix(in srgb,var(--surface) 96%,white 4%),color-mix(in srgb,var(--surface) 90%,var(--accent-soft) 10%));box-shadow:0 32px 80px color-mix(in srgb,#172033 28%,transparent),0 8px 28px color-mix(in srgb,var(--fg) 10%,transparent);isolation:isolate}
.notification-card::before{content:'';position:absolute;z-index:-1;inset:8px;border-radius:26px;border:1px solid color-mix(in srgb,var(--accent) 14%,transparent);pointer-events:none}
/* 角色“趴”在卡片上边框上：0.94918 = 图片 alpha 包围盒下界 579 / 图片高 610，
   即「可视内容底边」在图片高度中的占比；用它对齐卡片上沿并轻微下压 6px，
   手部就正好压在边框线上，头部完整露出在卡片之外。
   注意不能直接用 img 的 bottom —— 图片底部还有 30px 透明留白。
   --char-gap 是角色顶部到 shell 顶部的留白，专门给上方的消息气泡用。 */
.notification-character{position:absolute;z-index:2;top:var(--char-gap);left:50%;width:var(--char-width);transform:translateX(-50%);pointer-events:none}
/* 气泡视觉样式来自 theme.css 的全局 .character-bubble，这里只声明摆放位置：
   居中对齐角色，贴在角色头顶上方 6px，箭头垂直向下指向头部。 */
.notification-bubble{--bubble-rest:translateX(-50%);left:50%;bottom:calc(100% + 6px)}
.notification-character img{display:block;width:100%;height:auto}
.notification-close{position:absolute;z-index:5;top:20px;right:20px;display:grid;place-items:center;width:40px;height:40px;border:1px solid var(--border);border-radius:50%;background:color-mix(in srgb,var(--surface) 82%,transparent);color:var(--muted)}
.notification-close:hover{background:var(--accent-soft);color:var(--fg)}
.notification-close-mark{position:relative;width:19px;height:19px;display:block}.notification-close-mark::before,.notification-close-mark::after{content:"";position:absolute;left:8px;top:-1px;width:3px;height:21px;border-radius:3px;background:currentColor;transform:rotate(45deg)}.notification-close-mark::after{transform:rotate(-45deg)}
.notification-header{position:relative;z-index:1;text-align:center}.notification-kicker{display:inline-flex;padding:5px 9px;border-radius:999px;background:var(--accent-soft);color:var(--accent);font-size:10px;font-weight:700;letter-spacing:.14em}.notification-header h2{margin:12px 0 7px;font-family:var(--font-display);font-size:clamp(25px,4vw,34px);font-weight:900;letter-spacing:-.03em}
.notification-list{position:relative;z-index:1;display:grid;gap:10px;margin:26px 0 0;padding:0;list-style:none}.notification-item{display:flex;gap:12px;padding:14px;border:1px solid color-mix(in srgb,var(--border) 78%,transparent);border-radius:17px;background:color-mix(in srgb,var(--surface) 72%,transparent)}.notification-item-icon{display:grid;place-items:center;width:34px;height:34px;flex:0 0 auto;border-radius:11px;background:var(--accent-soft);color:var(--accent)}.notification-item-icon .i{width:16px;height:16px}.notification-item-body{display:grid;min-width:0;gap:3px;line-height:1.45}.notification-item-meta{display:flex;gap:9px;align-items:center;color:var(--muted);font-size:11px}.notification-item-meta strong{color:var(--accent);font-weight:700}.notification-item-meta time{margin-left:auto;white-space:nowrap}.notification-item-body b{font-size:13px;font-weight:600}.notification-item-body>span:last-child{color:var(--muted);font-size:12px}
@media (max-width:700px){.notification-modal{padding:18px}.notification-dialog-shell{--char-width:min(270px,72vw)}.notification-card{max-height:calc(100vh - 36px);padding:32px 16px 22px;border-radius:25px}.notification-close{top:14px;right:14px;width:36px;height:36px}.notification-header h2{font-size:27px}.notification-item{padding:12px}.notification-item-body b{font-size:12.5px}.notification-item-body>span:last-child{font-size:11.5px}}
</style>

