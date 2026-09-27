# 首页角色对话气泡 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为首页角色增加基于时间问候、悬停提示和输入等待状态的只读对话气泡。

**Architecture:** 使用 `useCharacterBubble` 作为轻量共享状态，侧边栏和首页通过同一状态实例交换悬停提示。HomeView 负责根据用户资料、时间和输入状态计算气泡文案，并在角色上方渲染只读气泡。

**Tech Stack:** Vue 3 `<script setup>`、TypeScript、Vue Router、现有 CSS variables、Vite。

---

### Task 1: Add shared bubble state

**Files:**
- Create: `frontend/src/composables/useCharacterBubble.ts`

- [ ] 导出响应式 `hoverMessage` 与 `setHoverMessage`、`clearHoverMessage`。
- [ ] 在模块级创建共享状态，确保 AppSidebar 和 HomeView 使用同一个实例。
- [ ] 允许传入 `string | null`，清除后回到首页自己的默认/输入状态。

### Task 2: Add sidebar hover/focus messages

**Files:**
- Modify: `frontend/src/components/AppSidebar.vue`

- [ ] 为导航项增加对应的傲娇可爱文案。
- [ ] 在 `mouseenter` 与 `focus` 时设置消息，在 `mouseleave` 与 `blur` 时清除消息。
- [ ] 不影响 router-link 的跳转与 active 样式。

### Task 3: Render the character bubble and home interactions

**Files:**
- Modify: `frontend/src/views/HomeView.vue`

- [ ] 增加无资料回退为“同学”的用户名格式化逻辑。
- [ ] 根据当前小时生成早上/下午/晚上问候语。
- [ ] 输入非空时优先显示等待文案，输入清空时恢复问候或悬停文案。
- [ ] 增加角色气泡模板，标记为只读并提供 `aria-live`。
- [ ] 为服务卡片、最近对话、快捷问题增加 hover/focus 文案绑定。

### Task 4: Style the bubble

**Files:**
- Modify: `frontend/src/views/HomeView.vue`

- [ ] 使用现有 token 实现气泡背景、边框、文字和小尾巴。
- [ ] 增加轻微进入动画并在 reduced motion 下关闭。
- [ ] 确保桌面和移动端不遮挡输入框，限制文字换行与宽度。

### Task 5: Verify

**Files:**
- Modify: none

- [ ] 运行 `npm run build`，确认 TypeScript 与 Vite 构建成功。
- [ ] 在浏览器检查首页首次问候、导航/卡片悬停、输入即时等待状态。
- [ ] 检查 `git diff --check`，确认无空白错误。

