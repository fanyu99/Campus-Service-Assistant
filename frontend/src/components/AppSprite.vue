<!--
  图标库统一基线（改图标前先看这里）：
    画布      viewBox 0 0 24 24
    安全框    主体图形收进 3.8–20.2（16.4×16.4，居中于 12,12）
              —— 同层级图标视觉重量一致，靠的就是这个框，不是靠眼睛估
    描边      fill:none + stroke:currentColor + stroke-width:1.7
              （定义在 theme.css 的 .i；任何组件都不要再单独覆盖 stroke-width）
    端点      stroke-linecap / stroke-linejoin 均为 round
    圆角      矩形一律 rx=2.5
    例外      箭头类（i-chev / i-arrow-up）与勾（i-check）形状本身窄扁，
              只对齐高度，不硬撑到 16.4 宽
-->
<template>
  <svg class="sprite" aria-hidden="true" focusable="false" xmlns="http://www.w3.org/2000/svg">
    <!-- ── 导航 ─────────────────────────────────────────────────────────── -->
    <symbol id="i-home" viewBox="0 0 24 24"><path d="M3.8 10.6L12 3.9l8.2 6.7V19a1.4 1.4 0 0 1-1.4 1.4h-4v-6.1H9.2v6.1H5.2A1.4 1.4 0 0 1 3.8 19z" /></symbol>
    <symbol id="i-chat" viewBox="0 0 24 24"><path d="M20.2 14.6a2 2 0 0 1-2 2H8.3L4.4 20.2V5.8a2 2 0 0 1 2-2h11.8a2 2 0 0 1 2 2z" /><path d="M8.6 9.8h6.8M8.6 13h4.2" /></symbol>
    <symbol id="i-list" viewBox="0 0 24 24"><path d="M8.8 5.6h11.4M8.8 12h11.4M8.8 18.4h11.4" /><path d="M4.4 5.6h.01M4.4 12h.01M4.4 18.4h.01" /></symbol>
    <symbol id="i-clock" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.2" /><path d="M12 7.6V12l3.2 1.9" /></symbol>
    <symbol id="i-help" viewBox="0 0 24 24"><circle cx="12" cy="12" r="8.2" /><path d="M9.7 9.5a2.4 2.4 0 1 1 3.3 2.3c-.7.3-1 .8-1 1.5v.3" /><path d="M12 16.6h.01" /></symbol>
    <symbol id="i-sliders" viewBox="0 0 24 24"><path d="M3.9 6.4h8.6M17.7 6.4h2.5M3.9 17.6h2M10.9 17.6h9.3" /><circle cx="15.2" cy="6.4" r="2.5" /><circle cx="8.4" cy="17.6" r="2.5" /></symbol>

    <!-- ── 通知（按类型区分，不再一律用铃铛）─────────────────────────────── -->
    <symbol id="i-bell" viewBox="0 0 24 24"><path d="M18.5 16.4V11.2a6.5 6.5 0 1 0-13 0v5.2L3.9 19h16.2z" /><path d="M9.9 21.2a2.4 2.4 0 0 0 4.2 0" /></symbol>
    <symbol id="i-megaphone" viewBox="0 0 24 24"><path d="M4.2 11.1L19.8 6.6v10.8L4.2 13.9z" /><path d="M11.4 16a2.7 2.7 0 1 1-5.2-1.4" /></symbol>
    <symbol id="i-doc" viewBox="0 0 24 24"><path d="M13.6 4.2H7.6a2.6 2.6 0 0 0-2.6 2.6v10.4a2.6 2.6 0 0 0 2.6 2.6h8.8a2.6 2.6 0 0 0 2.6-2.6V9.6z" /><path d="M13.6 4.2v5.4h5.4" /><path d="M9.4 13.6h5.2M9.4 16.4h5.2" /></symbol>
    <symbol id="i-wrench" viewBox="0 0 24 24"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" /></symbol>

    <!-- ── 事务（首页服务行与事项列表共用同一套映射）──────────────────────── -->
    <symbol id="i-id" viewBox="0 0 24 24"><rect x="3.8" y="4.8" width="16.4" height="14.4" rx="2.5" /><circle cx="8.8" cy="11.4" r="2.1" /><path d="M6.2 16.6a3 3 0 0 1 5.2 0M13.6 10.4h4.4M13.6 13.6h4.4" /></symbol>
    <symbol id="i-card" viewBox="0 0 24 24"><rect x="3.8" y="4.8" width="16.4" height="14.4" rx="2.5" /><path d="M3.8 9.6h16.4M6.8 14.4h3.2" /></symbol>
    <symbol id="i-calendar" viewBox="0 0 24 24"><rect x="3.8" y="5.4" width="16.4" height="14.4" rx="2.5" /><path d="M3.8 10.4h16.4M8.4 3.9v3.2M15.6 3.9v3.2" /></symbol>
    <symbol id="i-award" viewBox="0 0 24 24"><circle cx="12" cy="9.4" r="6.4" /><path d="M8.8 14.8L7.2 20.4l4.8-2.3 4.8 2.3-1.6-5.6" /></symbol>
    <symbol id="i-wifi" viewBox="0 0 24 24"><path d="M4.2 8.7a11.6 11.6 0 0 1 15.6 0" /><path d="M7.2 11.9a7.4 7.4 0 0 1 9.6 0" /><path d="M10.2 15.1a3.2 3.2 0 0 1 3.6 0" /><path d="M12 18.3h.01" /></symbol>

    <!-- ── 主题（常驻栏快捷切换：太阳＝当前浅色，月亮＝当前深色）──────────────
        太阳：中心圆 r=4.6，八条射线 6.5→8.2，外接半径 8.2 正好顶到安全框。
        月亮：把 Lucide 的 moon 按 16.4/18 缩放（6→5.47、9→8.2、端点 9→8.2），
        外弧即 r=8.2、圆心 (12,12) 的圆，包围盒恰好 3.8–20.2。 -->
    <symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4.6" /><path d="M12 3.8v1.7M12 18.5v1.7M3.8 12h1.7M18.5 12h1.7M6.2 6.2l1.2 1.2M16.6 16.6l1.2 1.2M17.8 6.2l-1.2 1.2M7.4 16.6l-1.2 1.2" /></symbol>
    <symbol id="i-moon" viewBox="0 0 24 24"><path d="M12 3.8a5.47 5.47 0 0 0 8.2 8.2 8.2 8.2 0 1 1-8.2-8.2Z" /></symbol>

    <!-- ── 通用 ─────────────────────────────────────────────────────────── -->
    <symbol id="i-search" viewBox="0 0 24 24"><circle cx="10.4" cy="10.4" r="6.4" /><path d="M15.1 15.1l4.8 4.8" /></symbol>
    <symbol id="i-chev" viewBox="0 0 24 24"><path d="M9.5 5.5l6.5 6.5-6.5 6.5" /></symbol>
    <symbol id="i-arrow-up" viewBox="0 0 24 24"><path d="M12 19.5V5" /><path d="M5.8 11.2L12 5l6.2 6.2" /></symbol>
    <symbol id="i-check" viewBox="0 0 24 24"><path d="M5 12.8l4.6 4.6L19 7.6" /></symbol>
  </svg>
</template>
