# examples

本目录是 ui-design-system 的**可直接运行**副本。所有代码与项目里的实现一致，
变量命名与 `foundations/`、`components/`、`motion/` 里的文档完全对应。

## 目录

| 文件 | 是什么 | 怎么用 |
| --- | --- | --- |
| `theme.css` | 完整 token 文件（字体 / 明暗两套变量 / 全局类） | 直接复制到 `src/styles/theme.css`，或 `import './theme.css'` |
| `design-system.html` | 单文件演示页，浏览器直接打开 | 双击即可，依赖同目录的 `theme.css` |
| `AnimatedButton.vue` | 动效描边按钮组件 | 复制到 `src/components/` |
| `AppSelect.vue` | 自绘下拉选择组件 | 复制到 `src/components/` |
| `ComposerField.vue` | 统一输入框外壳的完整用法（主 composer / 搜索框 / 表单字段） | 复制到 `src/components/` 或照抄进页面 |
| `NoticeCard.vue` | 通知中心弹窗（含三层光效与角色定位） | 复制到 `src/components/` |
| `AppSprite.vue` | 19 个图标的内联 sprite | 复制到 `src/components/`，在 `App.vue` 顶部挂一次 |

## 跑起来

### 只看效果（零依赖）

```bash
# 直接在浏览器里打开演示页（与 theme.css 同目录，<link> 会正常加载）
start design-system.html      # Windows
open design-system.html       # macOS
```

演示页包含：色板（明暗可切）、字体层级、圆角与阴影、按钮四类、输入框三态、
列表行、卡片光效、加载指示器、空态、图标全览。右上角按钮切深浅主题。

### 接入现有项目（Vue 3 + Vite）

1. 把 `theme.css` 放到 `src/styles/theme.css`，在 `main.ts` 里
   `import './styles/theme.css'`。
2. 复制需要的组件到 `src/components/`。
3. `App.vue` 顶部挂一次 sprite 与主题扩散载体：

```vue
<script setup lang="ts">
import AppSprite from './components/AppSprite.vue'
import { useTheme } from './composables/useTheme'
useTheme()
</script>

<template>
  <AppSprite />
  <div class="theme-ripple-veil" aria-hidden="true" />
  <div class="theme-ripple-pond" aria-hidden="true" />
  <!-- 你的应用 -->
</template>
```

> 主题切换的圆形扩散还需要 `composables/useTheme.ts` 与
> `composables/themeRipple.ts`，完整代码见 `motion/theme-ripple.md`。

4. 字体文件放到 `public/assets/fonts/`（`DMSans-Regular.woff2`、
   `Epilogue-Black.woff2`）；没有的话会回退到系统字体，不影响布局。

## 命名对照（文档 ↔ 代码）

| 文档里的名字 | 代码里的名字 |
| --- | --- |
| 强调色 | `--accent` / `--accent-hover` / `--accent-soft` |
| 输入框外壳 | `.composer-shell` + `--composer-*` |
| 光扫按钮 | `.spark-button` |
| 动效描边按钮 | `.animated-button` |
| 角色气泡 | `.character-bubble` + `--bubble-rest` / `--bubble-arrow-x` |
| 通知光效 | `--notice-*` + `.notification-card-frame` |
| 主题扩散 | `--theme-ripple-*` + `.theme-ripple-veil` / `.theme-ripple-pond` |
| 加载指示器 | `.loading-animation` + `--loader-*` |

改任何数值时，先改 `theme.css` 里的变量；组件里的字面值只应该是
`width/height/padding` 这类布局量。
