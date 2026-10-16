# 角色动态拆分与动画改造记录

日期：2026-10-16

分支：`feature/character-motion`

## 改造目标

在保留原有眼睛跟随鼠标效果的基础上，将女孩贴图中的装饰元素拆分出来，使左右爱心能够独立上下浮动，顶部呆毛能够轻微摆动。女孩主体本身保持静止，避免出现整体贴图位移。

## 修改内容

### 1. 角色素材拆分

- `frontend/public/assets/character-base-motion.png`
  - 作为新的角色主体底图。
  - 去除原贴图中的左右爱心和顶部呆毛。
  - 保留人物主体、服装、表情和眼眶区域。
- `frontend/public/assets/character-heart-left.png`
  - 独立左侧爱心透明素材。
- `frontend/public/assets/character-heart-right.png`
  - 独立右侧爱心透明素材。
- `frontend/public/assets/character-ahoge.png`
  - 独立顶部呆毛透明素材。

原始 `character.webp` 保留未覆盖，作为备份资源。

### 2. 首页图层与动画

修改文件：`frontend/src/views/HomeView.vue`

- 将角色底图切换为 `character-base-motion.png`。
- 增加左右爱心图层，并设置不同的动画时长和延迟，使两侧运动不同步。
- 增加呆毛图层，围绕根部做轻微旋转和上下位移。
- 保留虹膜层和睫毛层的层级关系，眼睛跟随鼠标的逻辑不变。
- 装饰图层使用 `pointer-events: none`，不阻挡输入框和页面交互。
- 增加 `will-change: transform`，降低动画过程中的视觉抖动。
- 增加 `prefers-reduced-motion: reduce` 兼容：用户关闭动画时，爱心、呆毛和虹膜动画会停止。

## 动画参数

- 爱心：约 3.9 秒循环，右侧爱心约 4.6 秒循环；上下移动约 7px，并带有轻微旋转和缩放。
- 呆毛：约 3.2 秒循环；旋转范围约 -4° 到 5°，并带有约 2px 的轻微上移。
- 主体：不参与装饰动画，保持静止。

## 验证记录

已完成以下本地检查：

- `npm run type-check`：通过。
- `npm run test`：通过，2 个测试文件、6 个测试用例全部通过。
- `npm run build`：通过，Vite 生产构建成功。
- 本地开发服务：`http://127.0.0.1:5173/` 返回 HTTP 200。
- Chrome 本地渲染检查：确认新底图、左右爱心和呆毛图层均被加载；桌面端角色位置和装饰层显示正常。

## 范围说明

本次仅涉及首页角色视觉资源和 `HomeView.vue` 的图层动画，不修改后端、数据库、接口、眼动逻辑或原始备份素材。
