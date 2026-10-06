# 首页布局

## 设计思路

**解决的问题**：首页要在**一屏内**放下"角色 + 输入区 + 右侧信息列"三块，且矮视口
（笔记本 1366×768）下不能被挤爆。

**视觉与交互意图**：
- **舞台区（左）**：角色层在上、composer 在下，角色"趴"在输入框上沿——这是首页的
  记忆点。整列 `justify-content: flex-end`，把组合压到底部。
- **面板区（右）**：固定 340px，两节（常用事项 / 最近记录），各自可滚。
- 三块入场时依次上浮淡入（55ms / 105ms 错峰）。

**适用场景**：首页。新增"舞台 + 侧栏"型页面可参照。

## 完整代码

### 结构

```vue
<main class="main home-reveal" data-od-id="home-main">
  <header class="topbar" data-od-id="global-header">…</header>

  <div class="workspace">
    <!-- 左：角色 + composer -->
    <section class="stage" data-od-id="ask-stage">
      <div class="character-layer" data-od-id="character-stage">
        <div class="character-wrap">
          <div class="character-bubble" role="status" aria-live="polite">{{ characterMessage }}</div>
          <div ref="character" class="character">
            <img class="ch-base" src="/assets/character.png" alt="">
            <div class="ch-iris-mask"><div class="ch-iris"><img src="/assets/character-iris.png" alt=""></div></div>
            <img class="ch-lash" src="/assets/character-lash.png" alt="">
          </div>
        </div>
      </div>

      <div class="composer-wrap">
        <form class="composer composer-shell" :class="{ 'is-invalid': isError }" novalidate @submit.prevent="submitQuestion">…</form>
        <p class="composer-msg" :class="{ 'is-error': isError }" role="status" aria-live="polite">{{ status }}</p>
        <div class="chips" data-od-id="ask-suggestions">
          <AnimatedButton @click="fill('学生证丢了怎么补办？')">学生证丢了怎么补办？</AnimatedButton>
          …
        </div>
      </div>
    </section>

    <!-- 右：信息列 -->
    <aside class="panel">
      <section data-od-id="quick-services">
        <div class="panel-head"><h2>常用事项</h2><button type="button" class="link-btn" @click="router.push({ name: 'services' })">全部事项</button></div>
        <ul class="list">…</ul>
      </section>
      <section data-od-id="recent-conversations">
        <div class="panel-head"><h2>最近记录</h2><button type="button" class="link-btn" @click="router.push({ name: 'history' })">全部记录</button></div>
        <ul class="list">…</ul>
      </section>
      <p class="mobile-note">演示数据 · 输入内容只保存在本机</p>
    </aside>
  </div>
</main>
```

### 样式

```css
/* 入场：三个区块依次上浮淡入，只动 opacity / transform，不触发重排 */
.home-reveal .topbar,
.home-reveal .stage,
.home-reveal .panel { animation: home-fade-up 460ms cubic-bezier(.2, 0, 0, 1) both; }
.home-reveal .stage { animation-delay: 55ms; }
.home-reveal .panel { animation-delay: 105ms; }
@keyframes home-fade-up { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }

.workspace {
  display: flex;
  gap: clamp(20px, 2.4vw, 38px);
  flex: 1;
  min-height: 0;                       /* 关键：允许内部压缩 */
  padding-bottom: clamp(16px, 2vw, 26px);
}

.stage {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;           /* 角色 + composer 压到底部 */
  min-width: 0;
  flex: 1;
}

.character-layer {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-end;
  justify-content: center;
  flex: 0 0 auto;
  min-height: 0;
  overflow: visible;                   /* 气泡要溢出到角色上方 */
  margin-bottom: 0;
}
.character-wrap { position: relative; width: min(36%, 230px); }

/* 气泡视觉在全局 .character-bubble，这里只声明位置 */
.character-bubble {
  left: 72%;
  bottom: calc(100% - 4px);
  --bubble-rest: translateX(-18%);
  --bubble-arrow-x: 22%;
}

/* 角色三层：底图（眼白已愈合）+ 虹膜层（整层平移）+ 睫毛层（静止压顶）
   掩膜半径必须 ≥ 精灵半径 + 最大位移，否则眼瞳移到极限时会被切平。 */
.character {
  position: relative;
  aspect-ratio: 1024 / 954;
  width: 100%;
  --eye-mask:
    radial-gradient(ellipse 6.836% 7.023% at 38.574% 62.788%, #000 88%, transparent 100%),
    radial-gradient(ellipse 7.031% 7.442% at 59.863% 55.765%, #000 88%, transparent 100%);
}
.character img { position: absolute; display: block; }
.ch-base { inset: 0; width: 100%; height: 100%; }
.ch-iris-mask { position: absolute; inset: 0; pointer-events: none; -webkit-mask-image: var(--eye-mask); mask-image: var(--eye-mask); }
.ch-iris { position: absolute; inset: 0; transform: translate(var(--gx, 0%), var(--gy, 0%)); }
.ch-iris img,
.ch-lash { left: 30.8594%; top: 46.1216%; width: 37.8906%; height: 24.7379%; }
@media (prefers-reduced-motion: reduce) { .ch-iris { transform: none; } }

.composer-wrap {
  position: relative;
  z-index: 2;
  width: min(660px, 100%);
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.chips { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; }

/* ── 右侧信息列 ──────────────────────────────────────────────────────── */
.panel { display: flex; flex-direction: column; gap: 26px; flex: 0 0 340px; width: 340px; min-width: 0; }
.panel-head { display: flex; align-items: baseline; justify-content: space-between; gap: 12px; }
.panel h2 { margin: 0; font-family: var(--font-display); font-weight: 900; font-size: 16.5px; letter-spacing: -.012em; }
.link-btn { flex: 0 0 auto; padding: 2px 0; color: var(--muted); font-size: 12.5px; white-space: nowrap; transition: color .16s ease; }
.link-btn:hover { color: var(--fg); }
.list { display: grid; gap: 2px; margin-top: 9px; }
.mobile-note { display: none; }

/* ── 窄桌面 ──────────────────────────────────────────────────────────── */
@media (max-width: 1080px) {
  .panel { flex-basis: 272px; width: 272px; }
  .composer-hint { display: none; }
  .composer-foot { justify-content: flex-end; }
}
@media (max-width: 940px) {
  .workspace { gap: 18px; }
  .panel { flex-basis: 250px; width: 250px; }
  .panel > section { min-width: 0; }
  .row,
  .recent-row { width: 100%; margin-inline: 0; padding-inline: 8px; }   /* 收回「破格」 */
}
/* 矮视口：靠删内容而不是缩字号 */
@media (max-height: 660px) and (min-width: 701px) {
  .composer { padding: 10px 12px 8px; border-radius: 20px; }
  .chips { display: none; }
  .composer-msg { min-height: 0; }
}

/* ── 移动端（≤700px）：纵向堆叠 ──────────────────────────────────────── */
@media (max-width: 700px) {
  /* 气泡会向角色上方伸展，提升首页层级，避免被移动端导航栏遮住 */
  .home-reveal { z-index: 7; }
  .character-bubble { z-index: 8; }
  .workspace { flex-direction: column; gap: 22px; padding-bottom: 36px; }
  .character-layer { flex: none; width: 100%; margin-bottom: 0; }
  .character-wrap { width: min(36%, 230px); }
  .composer-wrap { width: 100%; }
  .composer { padding: 13px 13px 11px; border-radius: 22px; }
  .composer textarea { font-size: 16px; }      /* 防 iOS 自动缩放 */
  .send { height: 44px; padding: 0 18px; }
  .panel { flex: none; width: 100%; flex-direction: column; gap: 30px; }
  .panel h2 { font-size: clamp(22px, 6.3vw, 30px); line-height: 1.25; }
  .row,
  .recent-row { min-height: 52px; width: calc(100% + 16px); margin-inline: -8px; padding: 8px; }
  .chips { justify-content: flex-start; }
  .mobile-note { display: block; margin: 0; color: var(--muted); font-size: 11.5px; line-height: 1.6; }
}

@media (prefers-reduced-motion: reduce) {
  .home-reveal .topbar,
  .home-reveal .stage,
  .home-reveal .panel { animation: none; }
  .composer,
  .composer::before,
  .composer::after { transition: none; animation: none; }
}
```

### 角色眼神跟随（composable）

```ts
// composables/useEyeGaze.ts —— 写 --gx / --gy，由 .ch-iris 消费
const MID_X = 0.49170
const MID_Y = 0.59041
const MAX_X = 1.367   // 14px / 1024
const MAX_Y = 1.258   // 12px / 954

function apply() {
  const el = host.value
  if (!el) return
  el.style.setProperty('--gx', cur.x.toFixed(3) + '%')
  el.style.setProperty('--gy', cur.y.toFixed(3) + '%')
}

function loop(ts: number) {
  raf = 0
  if (idle) {
    // 触屏没有指针：让眼睛缓慢环绕，角色不至于变成一张静止图
    if (!t0) t0 = ts
    const a = (ts - t0) / 6200
    tgt.x = Math.cos(a) * MAX_X * 0.55
    tgt.y = Math.sin(a) * MAX_Y * 0.55
  }
  cur.x += (tgt.x - cur.x) * 0.15        // 缓动跟随，不是瞬移
  cur.y += (tgt.y - cur.y) * 0.15
  const settled = Math.abs(tgt.x - cur.x) < 0.003 && Math.abs(tgt.y - cur.y) < 0.003
  if (settled) { cur.x = tgt.x; cur.y = tgt.y }
  apply()
  if (!settled || idle) raf = requestAnimationFrame(loop)
}
```

## 变体说明

| 变体 | 规则 |
| --- | --- |
| **宽桌面（>1080px）** | 舞台 flex:1 + 面板 340px；`gap: clamp(20px,2.4vw,38px)`。 |
| **窄桌面（≤1080px）** | 面板 →272px；隐藏 `composer-hint`；foot 右对齐。 |
| **更窄（≤940px）** | 面板 →250px；列表行收回"破格"写法（`width:100%`）。 |
| **矮视口（≤660px 高）** | composer 圆角 →20px、padding 收紧；**隐藏建议 chips**；`composer-msg` 高度归零。 |
| **移动端（≤700px）** | 纵向堆叠：角色层 → composer → 面板；面板 h2 放大到 `clamp(22px,6.3vw,30px)`；显示 `mobile-note`；`.home-reveal` 提 `z-index:7`、气泡 `z-index:8`。 |
| **主题** | 全走变量，无额外处理。 |
| **加载/空态** | 首页无加载态；最近记录为空时该节不渲染（当前 mock 恒有数据）。 |

## 使用注意事项

**可访问性**
- 气泡 `role="status" aria-live="polite"`（hover 时频繁变化，不能用 assertive）。
- `.character` 里的三张图全部 `alt=""`（纯装饰）。
- 建议 chips 用 `AnimatedButton`（真按钮），键盘可达；hover 与 focus 都要能
  触发角色台词（`@mouseenter` + `@focus` 成对写）。

**性能**
- 眼神跟随是常驻 rAF，但**只在未收敛或触屏 idle 模式才续帧**（`settled` 判断），
  静止时完全不跑。
- `fine = matchMedia('(hover: hover) and (pointer: fine)')`：触屏设备不监听
  `pointermove`，改成缓慢环绕（仍然是 rAF 常驻——这是刻意的设计取舍，角色不能
  变成静止图；`prefers-reduced-motion` 下会关掉）。
- 入场动画只动 `opacity` + `transform`。

**常见误用**
1. **`.workspace` 忘了 `min-height: 0`** —— flex 子项不会收缩，矮视口下 composer
   被顶出屏幕外。
2. **移动端忘了提 `z-index`** —— 气泡会被 sticky 导航栏盖住。
3. **`.character-layer` 写 `overflow: hidden`** —— 气泡出不来。必须是 `visible`。
4. **composer 的 `max-height` 不设上限** —— 长文本把角色顶没。首页 104px。
5. **离开首页时不清 hover 台词** —— 点"开始咨询"时鼠标还停在输入框上，
   `mouseleave` 不会触发，回到首页会残留输入提示语。**必须 `onBeforeUnmount(clearHoverMessage)`。**
