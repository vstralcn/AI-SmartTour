"""数字人推理服务 — MuseTalk 口型驱动 + ffmpeg 模拟降级

工作模式（自动检测）：
  GPU 可用 → 使用 MuseTalk 生成真人口型同步视频
  无 GPU   → 使用 ffmpeg 对静态图片做 Ken Burns 缩放动画

调用方（backend broadcast API）：
  POST /generate   → 提交生成任务，返回 job_id
  GET  /jobs/{id}  → 查询任务状态
  GET  /jobs/{id}/video → 下载生成的 MP4
"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

logger = logging.getLogger("digital-human")

# ── 目录 ──────────────────────────────────────────────────────────────
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/data/outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── 任务存储（生产环境应换 Redis） ────────────────────────────────────
jobs: dict[str, dict] = {}


# ── GPU 检测 ──────────────────────────────────────────────────────────
def _gpu_available() -> bool:
    try:
        r = subprocess.run(
            ["nvidia-smi"],
            capture_output=True, text=True, timeout=5,
        )
        return r.returncode == 0
    except Exception:
        return False


HAS_GPU = _gpu_available()


# ── 生命周期 ──────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    logger.info(
        "Digital Human Service started | engine=%s",
        "musetalk" if HAS_GPU else "simulate(ffmpeg)",
    )
    yield
    # 清理过期任务（保留最近 50 个）
    keep = set(sorted(jobs, key=lambda j: jobs[j].get("created_at", 0))[-50:])
    for jid in list(jobs):
        if jid not in keep:
            jobs.pop(jid, None)
            shutil.rmtree(OUTPUT_DIR / jid, ignore_errors=True)


app = FastAPI(
    title="Digital Human Service",
    version="0.2.0",
    lifespan=lifespan,
)


# ── 健康检查 ──────────────────────────────────────────────────────────
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "digital-human",
        "engine": "musetalk" if HAS_GPU else "simulate",
        "gpu_available": HAS_GPU,
    }


# ── 提交生成任务 ──────────────────────────────────────────────────────
@app.post("/generate")
async def generate(
    image: UploadFile = File(...),
    text: str = Form(""),
    emotion: str = Form("neutral"),
    max_duration: int = Form(30),
):
    job_id = str(uuid.uuid4())
    job_dir = OUTPUT_DIR / job_id
    job_dir.mkdir(parents=True)

    # 保存参考图片
    img_path = job_dir / "reference.png"
    await image.seek(0)
    raw = await image.read()
    if not raw:
        raise HTTPException(422, "图片内容为空")
    img_path.write_bytes(raw)

    now = asyncio.get_event_loop().time()
    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "video_path": None,
        "has_audio": False,
        "engine": "musetalk" if HAS_GPU else "simulate",
        "created_at": now,
    }

    asyncio.create_task(
        _generate_video(job_id, job_dir, img_path, text, emotion, max_duration)
    )

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "任务已提交",
        "has_audio": False,
        "engine": "musetalk" if HAS_GPU else "simulate",
    }


# ── 查询任务状态 ──────────────────────────────────────────────────────
@app.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return {
        "job_id": job_id,
        "status": job["status"],
        "progress": job.get("progress", 0),
        "has_audio": job.get("has_audio", False),
        "engine": job.get("engine", "unknown"),
    }


# ── 下载生成的视频 ────────────────────────────────────────────────────
@app.get("/jobs/{job_id}/video")
async def get_job_video(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    if job["status"] == "queued" or job["status"] == "processing":
        raise HTTPException(425, "视频尚未生成完毕")
    if job["status"] == "failed":
        raise HTTPException(422, f"生成失败：{job.get('message', '未知错误')}")
    vp = job.get("video_path")
    if not vp or not Path(vp).exists():
        raise HTTPException(404, "视频文件不存在")
    return FileResponse(vp, media_type="video/mp4")


# ── 后台生成逻辑 ──────────────────────────────────────────────────────
async def _generate_video(
    job_id: str,
    job_dir: Path,
    img_path: Path,
    text: str,
    emotion: str,
    max_duration: int,
) -> None:
    video_path = job_dir / "output.mp4"
    duration = min(max(len(text) // 3, 5), max_duration)  # 按文本长度估算

    try:
        if HAS_GPU:
            await _musetalk_generate(job_id, job_dir, img_path, text, emotion, duration, video_path)
        else:
            await _ffmpeg_simulate(job_id, img_path, duration, video_path)
    except Exception as exc:
        logger.exception("生成失败 job=%s", job_id)
        jobs[job_id].update({"status": "failed", "message": str(exc)})


# ── MuseTalk 真人口型（GPU） ──────────────────────────────────────────
async def _musetalk_generate(
    job_id: str,
    job_dir: Path,
    img_path: Path,
    text: str,
    emotion: str,
    duration: int,
    video_path: Path,
) -> None:
    # ── 预留 MuseTalk 推理接入点 ──────────────────────────────────────
    # 当 MuseTalk 模型文件就位后：
    #   1. 用 TTS 引擎将 text 转音频 → job_dir/audio.wav
    #   2. 调用 MuseTalk 推理：python inference.py \
    #        --audio job_dir/audio.wav \
    #        --face img_path \
    #        --outpath video_path \
    #        --emotion emotion
    #   3. 合并音轨
    #   4. jobs[job_id]["has_audio"] = True

    # GPU 可用但 MuseTalk 尚未接入时，也降级为 ffmpeg 模拟
    logger.warning("MuseTalk 推理尚未接入, 降级为 ffmpeg 模拟")
    await _ffmpeg_simulate(job_id, img_path, duration, video_path)


# ── ffmpeg 模拟模式（无 GPU / MuseTalk 未接入） ──────────────────────
async def _ffmpeg_simulate(
    job_id: str,
    img_path: Path,
    duration: int,
    video_path: Path,
) -> None:
    jobs[job_id].update({"status": "processing", "progress": 30})

    # Ken Burns 缩放动画：从 1.0 缓慢放大到 1.03，叠加微小平移
    filter_complex = (
        "scale=1280:1280:force_original_aspect_ratio=increase,"
        "crop=1280:1280,"
        "zoompan=z='min(zoom+0.0003,1.03)':d=125:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=640x640"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(img_path),
        "-vf", filter_complex,
        "-c:v", "libx264",
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-r", "15",
        "-preset", "fast",
        "-crf", "23",
        str(video_path),
    ]

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    _, stderr = await proc.communicate()

    if proc.returncode != 0:
        err = stderr.decode(errors="replace")[-500:]
        raise RuntimeError(f"ffmpeg 返回 {proc.returncode}: {err}")

    if not video_path.exists() or video_path.stat().st_size == 0:
        raise RuntimeError("ffmpeg 输出文件为空")

    jobs[job_id].update({
        "status": "done",
        "progress": 100,
        "video_path": str(video_path),
        "has_audio": False,
        "engine": "simulate",
    })
    logger.info("生成完成 job=%s duration=%ds size=%dKB",
                job_id, duration, video_path.stat().st_size // 1024)
