# SmartTour 项目长期笔记

## 项目概览
智慧景区导览系统：AI 数字人导游 + 路线推荐 + 知识库 RAG。
- 后端：FastAPI（`backend/app`），Python 3.11+
- 前端：Vue 3 + Vite + TS（`frontend/tourist-app`），管理端 `frontend/admin-panel`
- 数字人推理服务：`digital_human/`（MuseTalk / ffmpeg 模拟），FastAPI 端口 8001
- 编排：`docker-compose.yml`

## 数字人架构（三种模式，自动降级）
`DigitalHuman.vue` 编排器按优先级：`video` > `xunfei` > `vrm` > `image`
- **讯飞虚拟人**（`XunfeiAvatar.vue`）：实时互动，SDK 部署在 `public/sdk/avatar-sdk-web_3.2.3.1002/`
- **VRM 3D**（`VrmAvatar.vue`）：Three.js + @pixiv/three-vrm，本地模型 `public/models/guide.vrm`
- **图片降级**（`ImageAvatar.vue`）：贴图 + 动效
- **高清播报**：后端 `digital_human_broadcast.py` 调用 digital_human 服务生成 MP4

## 讯飞 SDK 关键约定
- **必须传 `useInlinePlayer: true`** 给 `new AvatarPlatform()`，否则 SDK 不创建 player、
  不挂载 wrapper、不播放视频流 → 黑屏且无报错。这是 2026-07-19 修复的黑屏根因。
- 安全接入：apiKey/apiSecret 仅后端持有，前端只拿 signedUrl（HMAC-SHA256 签名）。
  后端签名时 authorization/date/host 原样拼接，**不做 URL 编码**（否则触发讯飞 11203）。
- 配置项：`.env` 中 `XF_AVATAR_*` 六项，缺任一项后端返回 `enabled=false`，前端降级。

## 前端开发约定
- 依赖安装：`npm install --legacy-peer-deps`（typescript@5.5 与 @vue/tsconfig@0.9.1 冲突）
- 类型检查：`npm run build`（= `vue-tsc --noEmit && vite build`）
- 讯飞 SDK 动态 import（`/* @vite-ignore */`），不进打包
- AvatarPlatform 实例不可放入 ref/reactive（Vue 代理破坏 SDK 私有成员）

## Docker 部署坑点（重要！）
`tourist-app` 服务在 docker-compose.yml 中**没有 volumes 挂载源码**，
跑的是 Dockerfile 两阶段构建（node build → nginx 静态服务）的产物 dist/。
- 改 .vue 后 `docker compose up -d` 或 `restart` **看不到变化**（复用旧镜像）
- 必须 `docker compose up -d --build tourist-app` 才会重新打包
- 缓存命中时用 `docker compose build --no-cache tourist-app`
- 浏览器还需 Ctrl+Shift+R 强刷（index.html 无 hash 可能被缓存）
- **开发期建议本地 `npm run dev`**（Vite HMR 即时生效），docker 仅用于部署

## 前端设计系统（style.css 全局 token）
- **品牌色**：紫蓝渐变 `--gradient-brand: linear-gradient(135deg, #6366f1 → #8b5cf6 → #a855f7)`
- **圆角**：sm 8 / md 12 / lg 16 / xl 20 / 2xl 24 / 3xl 32 / pill 999
- **阴影**：`--shadow-sm/md/lg` + `--shadow-glow`（紫蓝发光）
- **间距**：1-9 token；缓动：`--ease-out: cubic-bezier(0.16, 1, 0.3, 1)` + 150/220/320ms
- **风格关键词**：圆角玻璃感、渐变光斑、segmented 控件、chip 行、shimmer 按钮
- **所有 scoped CSS 必须用 design token**，不要硬编码颜色/圆角

## 讯飞 SDK Wrapper 渲染层坑点
SDK 内部 `player.container = wrapper` 把 `<video>` 元素插到 wrapper 里，但元素没有
显式 width/height，会渲染为 0 尺寸。**必须**用 `:deep(video) { width:100%!important; height:100%!important; }`。
另：wrapper 在 flex 容器中要用 `position:absolute; inset:0` 或 `flex:1; min-height:0`
才能撑满父级。

## 后端关键路由（均挂 `/api/v1` 前缀）
- `POST /chat/stream` WebSocket 流式对话
- `GET /avatar/active` 当前激活数字人
- `GET /avatar/xunfei/signed-url` 讯飞签名地址（公开，无需鉴权）
- `POST /digital-human/broadcast` 高清播报生成 + 轮询
- `POST /recommend/route` 路线推荐
