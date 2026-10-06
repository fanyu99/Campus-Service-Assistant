# 入场、路由切换与气泡弹出

## 设计思路

**解决的问题**：页面直接"出现"会显得生硬；但入场动画做重了（位移大、时长长）又会
让每次切页都在等。

**视觉与交互意图**：**入场轻、路由更快**。首页三区块错峰 55ms / 105ms 上浮 10px
淡入（460ms）；路由切换只有 180ms、位移 8px / -4px。前者是"第一次见面的仪式感"，
后者是"常客之间的点头"——**路由切换绝不能慢**，否则每次点侧栏都在等动画。

**入场动画只动 `opacity` + `transform`**，不触发重排。

## 完整代码

### 首页入场（三区块错峰）

```css
/* 入场：三个区块依次上浮淡入，只动 opacity / transform，不触发重排 */
.home-reveal .topbar,
.home-reveal .stage,
.home-reveal .panel { animation: home-fade-up 460ms cubic-bezier(.2, 0, 0, 1) both; }
.home-reveal .stage { animation-delay: 55ms; }
.home-reveal .panel { animation-delay: 105ms; }

@keyframes home-fade-up {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

@media (prefers-reduced-motion: reduce) {
  .home-reveal .topbar,
  .home-reveal .stage,
  .home-reveal .panel { animation: none; }
}
```

### 路由切换（180ms，`out-in`）

```css
.route-enter-active,
.route-leave-active {
  will-change: opacity, transform;
  transition: opacity 180ms cubic-bezier(.2, 0, 0, 1), transform 180ms cubic-bezier(.2, 0, 0, 1);
}
.route-enter-from { opacity: 0; transform: translateY(8px); }
.route-leave-to { opacity: 0; transform: translateY(-4px); }

@media (prefers-reduced-motion: reduce) {
  .route-enter-active,
  .route-leave-active { transition: none; }
  .route-enter-from,
  .route-leave-to { opacity: 1; transform: none; }
}
```

```vue
<!-- App.vue：mode="out-in" 保证旧页先走完再进新页，不会两页叠着 -->
<Transition name="route" mode="out-in">
  <router-view v-slot="{ Component, route }">
    <component :is="Component" :key="route.fullPath" />
  </router-view>
</Transition>
```

### 角色气泡弹出

```css
@keyframes bubble-pop {
  /* 注意：keyframes 里也要带上 --bubble-rest，否则动画结束会跳回 translateX(0) */
  from { opacity: 0; transform: var(--bubble-rest, translateX(0)) translateY(4px) scale(.98); }
  to   { opacity: 1; transform: var(--bubble-rest, translateX(0)); }
}
.character-bubble { animation: bubble-pop .24s ease both; }

@media (prefers-reduced-motion: reduce) { .character-bubble { animation: none; } }
```

### 下拉弹层（Vue `<Transition>`）

```css
.select-pop-enter-active,
.select-pop-leave-active { transition: opacity .16s ease, transform .16s ease; }
.select-pop-enter-from,
.select-pop-leave-to { opacity: 0; transform: translateY(-6px) scale(.98); }

@media (prefers-reduced-motion: reduce) {
  .select-pop-enter-active,
  .select-pop-leave-active { transition: none; }
}
```

### 品牌标呼吸（唯一的常驻小元素动画）

```css
.brand-mark { animation: brand-mark-glow 2.6s ease-in-out infinite; }
@keyframes brand-mark-glow {
  0%, 100% { filter: drop-shadow(0 0 0 color-mix(in srgb, var(--accent) 0%, transparent)); transform: scale(1); }
  50%      { filter: drop-shadow(0 0 9px color-mix(in srgb, var(--accent) 72%, transparent)); transform: scale(1.04); }
}
```

## 变体说明

| 动效 | 时长 | 曲线 | 位移 | 错峰 | 触发 |
| --- | --- | --- | --- | --- | --- |
| 首页入场 | 460ms | `.2,0,0,1` | `translateY(10px)` | 0 / 55 / 105ms | 挂载（`both`） |
| 路由 enter | 180ms | `.2,0,0,1` | `translateY(8px)` | — | 路由变更 |
| 路由 leave | 180ms | `.2,0,0,1` | `translateY(-4px)` | — | 路由变更 |
| 气泡弹出 | 240ms | `ease` | `translateY(4px) scale(.98)` | — | 挂载（`both`） |
| 下拉弹层 | 160ms | `ease` | `translateY(-6px) scale(.98)` | — | 展开/收起 |
| 品牌标呼吸 | 2.6s | `ease-in-out` | `scale(1→1.04)` | — | 常驻循环 |

| 变体 | 规则 |
| --- | --- |
| **主题** | 参数完全不随主题变（只有颜色 token 变）。 |
| **移动端** | 入场与路由参数不变；首页额外提 `.home-reveal { z-index: 7 }`、气泡 `z-index: 8`（避免被 sticky 导航栏遮住）。 |
| **矮视口** | 入场不变（它是 `opacity/transform`，不受高度影响）。 |
| **`both` 填充模式** | 入场与气泡用 `both`（保证动画前就是初始态，不会闪一帧）；路由用 `enter-from` / `leave-to` 类（Vue Transition 自己管理）。 |
| **reduced-motion** | 全部 `animation: none` / `transition: none`；路由的 `enter-from`/`leave-to` 要显式复位成 `opacity:1; transform:none`（否则会卡在不可见状态）。 |

## 使用注意事项

**可访问性**
- reduced-motion 分支里，**路由必须把 `enter-from` / `leave-to` 复位**
  （`opacity: 1; transform: none`），否则禁用动画后页面会永久停在 `opacity: 0`——
  这是最危险的一处降级 bug。
- 入场动画不要超过 500ms：用户已经点完了，等动画很烦。

**性能**
- 只动 `opacity` + `transform`，两者都能走合成层。
- `will-change` 只在 `.route-enter-active/.route-leave-active` 期间挂
  （Vue 会在这两个类存在时才应用），不是常驻。
- 品牌标呼吸动的是 `filter: drop-shadow`——**会逐帧重绘**。只有一个 32px 元素，
  可接受；**不要在列表项上复制这个写法**。
- 路由用 `mode="out-in"`：旧页完整退出后新页才进，避免两页同时存在导致
  双份滚动容器 / 双份粒子监听。

**常见误用**
1. **路由动画时长超过 200ms** —— 每次切页都在等。180ms 是实测的舒适值。
2. **reduced-motion 下忘记复位 `enter-from`** —— 页面永久不可见（见上）。
3. **入场用 `height` / `margin` 动画** —— 会触发整页重排，明显卡。
4. **气泡 keyframes 里忘了 `--bubble-rest`** —— 动画结束的瞬间气泡从
   `translateX(-18%)` 跳到 `translateX(0)`，肉眼可见地"闪一下"。
5. **给每个页面都加入场动画** —— 只有首页有（它是落地页）。内容页靠路由过渡
   就够了，叠加会显得慢。
6. **`<Transition>` 不用 `mode="out-in"`** —— 两页并存期间会有两个 `.main`
   滚动容器，滚动位置错乱。
