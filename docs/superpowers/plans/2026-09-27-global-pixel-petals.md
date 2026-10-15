# 全局像素花瓣与彗星拖尾 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Campus-Service-Assistant 全应用中统一实现像素花瓣背景与鼠标彗星拖尾，并移除所有点击爆发与扩散效果。

**Architecture:** 复用现有全局 `ParticleBackground` 入口和 `ParticleEngine` Canvas 渲染循环，将动画状态收敛为花瓣数组、环境粒子数组和鼠标 CometParticle 数组。点击事件不再进入动画引擎；首页旧的 `useHeroField` 逻辑不再挂载，确保全局只有一套动画。

**Tech Stack:** Vue 3、TypeScript、Canvas 2D、Vite、CSS variables。

---

## 文件边界

- Modify: `frontend/src/components/particle-background/particle-engine.ts` — 统一花瓣、环境粒子、彗星拖尾的数据更新和绘制。
- Modify: `frontend/src/components/particle-background/particle-types.ts` — 增加花瓣类型，删除点击爆发专用类型和配置字段。
- Modify: `frontend/src/components/particle-background/particle-presets.ts` — 设置花瓣数量、拖尾上限、运动降级参数。
- Modify: `frontend/src/components/particle-background/ParticleBackground.vue` — 删除 pointerdown 监听，保留全局生命周期与 resize/visibility 处理。
- Modify: `frontend/src/App.vue` — 以明确的全局配置挂载背景组件，保证所有路由共享一个 Canvas。
- Modify: `frontend/src/views/HomeView.vue` — 删除旧 `useHeroField` 的挂载和清理逻辑，避免重复动画。
- Modify: `frontend/src/styles/theme.css` — 调整花瓣与拖尾使用的现有动态色变量，确保浅色/深色主题对比度足够。
- Create: `docs/superpowers/specs/2026-09-27-global-pixel-petals-design.md` — 已批准设计说明。
- Create: `docs/superpowers/plans/2026-09-27-global-pixel-petals.md` — 本实施计划。

## Task 1: 固化类型和配置边界

- [ ] 在 `particle-types.ts` 增加 `CherryBlossom` 类型，字段包含 `x`、`y`、`z`、`vx`、`vy`、`rotation`、`spin`、`sway`、`life`、`maxLife`、`size`、`alpha`。
- [ ] 从 `ParticleBackgroundProps`、`ParticleConfig` 和相关引用中移除点击爆发配置；保留 `reducedMotion`、`opacity`、`zIndex`、`trailStrength` 等仍有用途的字段。
- [ ] 在 `particle-presets.ts` 将默认模式改为花瓣背景：花瓣数量随视口宽度计算，拖尾上限控制在约 180 个以内；减少动态效果时把花瓣与拖尾数量降到一半以下。
- [ ] 运行 `npm run type-check`，确认类型错误只来自尚未改造的引擎调用点，并记录失败位置。

## Task 2: 重写 Canvas 引擎的花瓣和拖尾逻辑

- [ ] 删除 `burstParticles`、`burstRings`、`solarPixels` 字段以及 `burst()`、`updateBursts()`、`drawBursts()` 相关代码。
- [ ] 增加花瓣初始化、补充和回收方法：花瓣从视口上方进入，使用 `sin` 摆动和 `rotation` 旋转，越过底部后回收并重新生成。
- [ ] 增加花瓣绘制方法：使用 `ctx.translate`、`ctx.rotate`、`ctx.scale` 绘制不规则五瓣/心形轮廓，填充当前主题的浅橙、粉橙和白色半透明色阶。
- [ ] 保留并调整 `setPointer()`：只在指针移动距离超过阈值时生成 CometParticle；拖尾使用方形 `fillRect`，按速度设置长度和透明度，严禁产生环形或径向爆发。
- [ ] 保留 `clearPointer()`、`resize()`、`destroy()`，确保 resize 后花瓣仍分布在可视区域且 Canvas 使用正确 DPR。
- [ ] 在 `draw()` 中按顺序清屏、更新指针、更新环境粒子、更新花瓣、更新拖尾、绘制花瓣、绘制环境粒子、绘制拖尾；不再调用任何 burst 方法。
- [ ] 运行 `npm run type-check`，确认引擎公开方法只包含 `resize`、`setPointer`、`clearPointer`、`draw`、`destroy`。

## Task 3: 移除点击事件和首页重复动画

- [ ] 从 `ParticleBackground.vue` 删除 `onPointerDown` 函数及 `window.addEventListener('pointerdown')` / `removeEventListener`。
- [ ] 将组件默认 props 改为花瓣模式，不再传递点击粒子相关参数。
- [ ] 在 `App.vue` 使用全局配置挂载 `ParticleBackground`，保持 Canvas 位于内容层下方且不会拦截指针。
- [ ] 在 `HomeView.vue` 删除 `useHeroField` 的 import、ref、调用和卸载逻辑；保留首页业务内容和布局不变。
- [ ] 运行 `rg -n "pointerdown|burst\(|clickBurst|burstParticles|burstRings|solarPixels|useHeroField" frontend/src`，预期生产入口不再出现这些点击爆发相关引用。

## Task 4: 校准主题色和可访问性

- [ ] 在 `theme.css` 为花瓣颜色增加语义变量或复用现有 `--fx-particle`、`--fx-particle-bright`、`--fx-particle-trail`，浅色和深色主题都保持足够的背景对比度。
- [ ] 确认 Canvas 使用 `aria-hidden="true"`、`pointer-events: none`，不改变页面键盘焦点顺序。
- [ ] 确认所有现有按钮文字继续保持 `white-space: nowrap`，不因背景组件改造引发布局变化。

## Task 5: 构建和浏览器验证

- [ ] 运行 `npm run type-check`，预期通过。
- [ ] 运行 `npm run build`，预期生成 Vite 生产构建且无 TypeScript/Vue 编译错误。
- [ ] 在已运行的 localhost 页面验证：首页、对话页、服务页、设置页都存在同一个背景 Canvas。
- [ ] 验证鼠标移动能产生方向性像素拖尾，鼠标停止后拖尾自然消失。
- [ ] 在首页和其他页面各点击数次，确认没有粒子迸发、圆环、扩散或点击脉冲。
- [ ] 验证窗口缩放、路由切换和深浅主题切换后花瓣仍持续渲染且没有控制台异常。

## Self-review

- 设计说明覆盖了全局范围、参考花瓣效果、彗星拖尾和点击移除要求。
- 计划明确列出了每个修改文件、公开接口和验证命令。
- 没有使用占位符；实现中不需要新增第三方依赖。
- v2 文件暂不作为生产入口，避免同一功能存在两个实现来源。
