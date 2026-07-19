"""数字人高清播报代理 API

前端 → 后端（本路由） → digital-human 推理服务（8001）

流程：
  1. POST   /digital-human/broadcast     → 提交任务，返回 job_id
  2. GET    /digital-human/broadcast/{id} → 轮询状态
  3. GET    /digital-human/broadcast/{id}/video → 下载视频

降级策略：
  - digital-human 服务不可用时，后端本地用 ffmpeg 生成模拟视频
  - 均无 ffmpeg 时返回 503，前端降级为实时 TTS 播报
"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import settings

logger = logging.getLogger("broadcast")

router = APIRouter(prefix="/digital-human", tags=["数字人播报"])

# ── 本地临时目录（无 GPU 时 ffmpeg 降级用） ─────────────────────────
LOCAL_OUTPUT = Path(tempfile.gettempdir()) / "smarttour_broadcast"
LOCAL_OUTPUT.mkdir(parents=True, exist_ok=True)

# ── 任务存储（生产用 Redis） ─────────────────────────────────────────
jobs: dict[str, dict] = {}


def _has_local_ffmpeg() -> bool:
    return shutil.which("ffmpeg") is not None


HAS_FFMPEG = _has_local_ffmpeg()


# ═════════════════════════════════════════════════════════════════════
# 1. 提交高清播报任务
# ═════════════════════════════════════════════════════════════════════
@router.post("/broadcast")
async def request_broadcast(
    text: str = Form(...),
    emotion: str = Form("neutral"),
    image: UploadFile = File(...),
):
    job_id = str(uuid.uuid4())
    now = asyncio.get_event_loop().time()

    job: dict = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0,
        "has_audio": False,
        "engine": "unknown",
        "video_path": None,
        "message": "",
        "created_at": now,
    }
    jobs[job_id] = job

    # 尝试提交到 digital-human 服务
    dh_url = settings.digital_human_url.rstrip("/")
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await image.seek(0)
            raw = await image.read()
            resp = await client.post(
                f"{dh_url}/generate",
                data={"text": text, "emotion": emotion},
                files={"image": ("avatar.png", raw, "image/png")},
            )
            if resp.status_code == 200:
                data = resp.json()
                job.update({
                    "status": "processing",
                    "engine": data.get("engine", "musetalk"),
                    "_dh_job_id": data.get("job_id"),
                    "_dh_url": dh_url,
                })
                # 启动后台轮询 digital-human 结果
                asyncio.create_task(_poll_dh(job_id, data["job_id"], dh_url))
                return _job_response(job_id, job)
            logger.warning("digital-human 返回非 200: %s", resp.status_code)
    except httpx.RequestError as exc:
        logger.warning("digital-human 不可达 (%s), 降级为本地 ffmpeg", exc)

    # 降级：本地 ffmpeg 生成
    if not HAS_FFMPEG:
        job.update({"status": "failed", "message": "无可用的视频生成引擎"})
        return _job_response(job_id, job)

    job.update({"status": "processing", "engine": "simulate"})
    asyncio.create_task(_local_simulate(job_id, image, text, emotion))
    return _job_response(job_id, job)


# ═════════════════════════════════════════════════════════════════════
# 2. 轮询任务状态
# ═════════════════════════════════════════════════════════════════════
@router.get("/broadcast/{job_id}")
async def get_broadcast_job(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return _job_response(job_id, job)


# ═════════════════════════════════════════════════════════════════════
# 3. 下载生成的视频
# ═════════════════════════════════════════════════════════════════════
@router.get("/broadcast/{job_id}/video")
async def get_broadcast_video(job_id: str):
    job = jobs.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    if job["status"] in ("queued", "processing"):
        raise HTTPException(425, "视频仍在生成中")
    if job["status"] == "failed":
        raise HTTPException(422, f"生成失败：{job.get('message', '未知错误')}")
    vp = job.get("video_path")
    if not vp or not Path(vp).exists():
        raise HTTPException(404, "视频文件不存在")
    return FileResponse(vp, media_type="video/mp4")


# ═════════════════════════════════════════════════════════════════════
# 内部 helpers
# ═════════════════════════════════════════════════════════════════════

def _job_response(job_id: str, job: dict) -> dict:
    return {
        "job_id": job_id,
        "status": job["status"],
        "message": job.get("message", ""),
        "has_audio": job.get("has_audio", False),
        "engine": job.get("engine", "unknown"),
    }


async def _poll_dh(job_id: str, dh_job_id: str, dh_url: str) -> None:
    """轮询 digital-human 服务直至任务完成"""
    deadline = asyncio.get_event_loop().time() + 180
    async with httpx.AsyncClient(timeout=5) as client:
        while asyncio.get_event_loop().time() < deadline:
            await asyncio.sleep(2)
            try:
                resp = await client.get(f"{dh_url}/jobs/{dh_job_id}")
                if resp.status_code != 200:
                    continue
                data = resp.json()
                jobs[job_id].update({
                    "status": data["status"],
                    "progress": data.get("progress", 0),
                })
                if data["status"] == "done":
                    # 获取视频流并转发
                    video_resp = await client.get(f"{dh_url}/jobs/{dh_job_id}/video")
                    if video_resp.status_code == 200:
                        local_path = LOCAL_OUTPUT / f"{job_id}.mp4"
                        local_path.write_bytes(video_resp.content)
                        jobs[job_id].update({
                            "video_path": str(local_path),
                            "has_audio": data.get("has_audio", False),
                            "engine": data.get("engine", "musetalk"),
                        })
                    return
                if data["status"] == "failed":
                    return
            except httpx.RequestError:
                logger.warning("轮询 digital-human 失败 job=%s", job_id)

        jobs[job_id].update({
            "status": "failed",
            "message": "轮询数字人服务超时",
        })


async def _local_simulate(
    job_id: str,
    image: UploadFile,
    text: str,
    emotion: str,
) -> None:
    """本地 ffmpeg 模拟生成"""
    job_dir = LOCAL_OUTPUT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    img_path = job_dir / "reference.png"

    await image.seek(0)
    img_path.write_bytes(await image.read())

    video_path = job_dir / "output.mp4"
    duration = min(max(len(text) // 3, 5), 30)

    jobs[job_id]["progress"] = 30

    filter_complex = (
        "scale=1280:1280:force_original_aspect_ratio=increase,"
        "crop=1280:1280,"
        "zoompan=z='min(zoom+0.0003,1.03)':d=125:"
        "x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s=640x640"
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

    if proc.returncode != 0 or not video_path.exists() or video_path.stat().st_size == 0:
        err = stderr.decode(errors="replace")[-500:] if stderr else "未知错误"
        jobs[job_id].update({"status": "failed", "message": f"ffmpeg 失败: {err}"})
        shutil.rmtree(job_dir, ignore_errors=True)
        return

    jobs[job_id].update({
        "status": "done",
        "progress": 100,
        "video_path": str(video_path),
        "has_audio": False,
        "engine": "simulate",
    })
    logger.info("本地模拟完成 job=%s duration=%ds", job_id, duration)
