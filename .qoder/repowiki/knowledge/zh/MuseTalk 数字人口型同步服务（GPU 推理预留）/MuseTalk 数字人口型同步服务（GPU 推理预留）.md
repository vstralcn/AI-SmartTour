---
kind: external_dependency
name: MuseTalk 数字人口型同步服务（GPU 推理预留）
slug: musetalk-avatar-sync
category: external_dependency
category_hints:
    - framework_behavior
scope:
    - '**'
---

### 身份与角色
- 独立 FastAPI 服务 `digital_human` 提供 `/generate`、`/jobs/{id}`、`/jobs/{id}/video` 异步任务接口，用于根据静态形象图片 + 文本生成口型同步视频。
- GPU Profile 下通过 nvidia-container-runtime 分配 GPU，检测 `nvidia-smi` 决定是否走 MuseTalk 真人口型路径；无 GPU 时降级为 ffmpeg Ken Burns 缩放动画模拟。

### 行为约束
- 当前 MuseTalk 推理尚未接入（代码注释标注预留点），即使检测到 GPU 也会降级到 ffmpeg 模拟模式；真实口型同步需在 `_musetalk_generate` 中接入 TTS + inference.py 管线。
- 任务结果按 job_id 存储在本地磁盘目录（OUTPUT_DIR），生产环境应替换为 Redis 任务队列 + 对象存储。

### 部署注意
- 该服务通过 `--profile gpu` 按需启动，不占用 CPU 资源；后端通过 `DIGITAL_HUMAN_URL` 环境变量发现该服务地址。