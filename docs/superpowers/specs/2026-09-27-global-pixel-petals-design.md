# 全局像素花瓣动态效果设计说明

## 目标

将 Campus-Service-Assistant 全应用的背景动画统一为单个 Canvas 动画层：背景持续洒落像素花瓣，鼠标移动时产生类似彗星轨迹的像素拖尾；移除所有鼠标点击触发的迸发粒子、扩散圆环和点击脉冲。

## 视觉与交互规则

- 花瓣沿参考项目的 Canvas 逻辑自然下落、旋转、摆动，并使用当前应用暖橙色主题进行配色。
- 鼠标移动只触发方向性像素拖尾，不触发点击反馈。
- 鼠标停止移动后，拖尾自然淡出；鼠标离开窗口后不再生成新粒子。
- 动画 Canvas 固定定位、`pointer-events: none`，不阻挡页面按钮、输入框和路由交互。
- 全局只保留一个动画循环，避免首页 `useHeroField` 与全局 `ParticleBackground` 重复绘制。
- `prefers-reduced-motion: reduce` 下减少花瓣数量并停用鼠标拖尾生成。
- 所有动画颜色从现有 `--fx-*` CSS 变量读取，不新增独立品牌色。

## 技术方案

1. 在现有 `particle-engine.ts` 中删除 burstParticles、burstRings、solarPixels 及其更新/绘制逻辑。
2. 增加 CherryBlossom 数据结构与花瓣生命周期，实现参考项目的二维 Canvas 花瓣效果，但改为 TypeScript 原生实现，不引入 jQuery。
3. 保留 CometParticle 作为鼠标拖尾数据结构，调整为方形像素绘制，并限制最大数量。
4. `ParticleBackground.vue` 只监听 `pointermove`、`pointerleave`、`resize` 和页面可见性变化，不再监听 `pointerdown`。
5. `App.vue` 使用全局背景组件；`HomeView.vue` 停止挂载旧的 `useHeroField`，避免重复动画。
6. 保留现有未使用的 v2 文件暂不删除，避免扩大变更范围；生产入口只使用改造后的主组件和引擎。

## 验收标准

- 点击页面任意位置不会出现粒子迸发、圆环或扩散。
- 鼠标快速移动时能看到连续的像素拖尾，拖尾方向与移动方向一致。
- 花瓣在所有路由都可见，且不会覆盖交互控件的点击区域。
- 页面切换、窗口缩放、深浅主题切换后 Canvas 仍正常运行。
- `npm run type-check` 和 `npm run build` 通过。
- 页面不存在水平滚动，动画不会导致控制台报错。
