---
kind: frontend_style
name: Vue3 + Vite 双前端应用样式体系
category: frontend_style
scope:
    - '**'
source_files:
    - frontend/tourist-app/src/App.vue
    - frontend/tourist-app/src/style.css
    - frontend/tourist-app/src/components/DigitalHuman/DigitalHuman.vue
    - frontend/admin-panel/src/App.vue
    - frontend/admin-panel/src/views/Analytics/AnalyticsView.vue
    - frontend/tourist-app/package.json
    - frontend/admin-panel/package.json
---

## 系统概览
本项目包含两个独立的前端应用，均基于 Vue3 + TypeScript + Vite 构建，但采用不同的 UI 策略：
- **tourist-app（游客端）**：轻量原生 CSS + scoped 样式，配合 Three.js/VRM 实现 3D 数字人交互
- **admin-panel（管理端）**：Element Plus 组件库 + ECharts 数据可视化，面向后台运营场景

## 技术栈与工具链
- 框架：Vue 3.5 + `<script setup>` + `<style scoped>` 单文件组件
- 构建：Vite 5 + vue-tsc 类型检查
- 状态：Pinia 3
- 路由：Vue Router 4
- HTTP：Axios
- 管理端额外依赖：Element Plus 2.14、ECharts 6 + vue-echarts 8
- 游客端额外依赖：Three.js 0.169 + @pixiv/three-vrm 3.4

## 样式组织方式
### 游客端（tourist-app）
- 全局样式极简：`src/style.css` 为空，`App.vue` 中仅定义 `*` 重置和 body 字体
- 组件级样式全部使用 `<style scoped>`，无外部 CSS 预处理
- 主题通过 JS 计算属性动态注入：`bgGradient`、`accentColor` 根据 emotion 状态映射不同渐变色与强调色
- 深色模式为默认风格，大量使用 `rgba(255,255,255,0.xx)` 半透明白字与 `backdrop-filter: blur()` 毛玻璃效果
- 关键视觉模式：
  - 情绪→背景渐变映射（neutral/happy/explaining/caring/excited 五种）
  - 情绪→强调色映射（#7c6cf0/#f472b6/#60a5fa/#fb923c/#f87171）
  - 三态降级：video → vrm → image

### 管理端（admin-panel）
- 基于 Element Plus 的卡片式布局，白色背景 + 浅灰边框 + 圆角阴影
- 图表配色统一采用 Tailwind 语义色：`#22c55e`(正)、`#eab308`(中)、`#ef4444`(负)
- 页面结构：顶部标题 + 概览卡片网格 + 双列图表区 + 建议列表
- 未引入 CSS 预处理器或原子化框架，纯手写 scoped CSS

## 设计约定
- 组件命名：PascalCase 目录 + `.vue` 后缀，按功能域分目录（ChatPanel/DigitalHuman/VoiceInput / Analytics/KnowledgeBase 等）
- 样式隔离：所有组件样式使用 scoped，避免全局污染
- 响应式：未使用媒体查询，主要依靠 Flex/Grid 自适应布局
- 图标：SVG sprite (`public/icons.svg`) 内联引用
- 资源路径：静态资源统一放在 `public/` 下，通过绝对路径引用

## 缺失项
- 无统一的 CSS 变量/Design Token 体系，颜色值在多处硬编码
- 无 CSS 预处理器（SCSS/Less/Stylus）、无 Tailwind、无 PostCSS 插件
- 无移动端适配策略（无 viewport meta 调整、无 rem/vw 方案）
- 无暗色/亮色主题切换机制（游客端固定深色，管理端固定浅色）
- 无样式单元测试或视觉回归测试