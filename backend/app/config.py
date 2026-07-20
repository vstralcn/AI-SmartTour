"""应用配置"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# .env 位于项目根目录（config.py 在 backend/app/，向上三级）
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env", extra="ignore"
    )

    # 应用配置
    app_name: str = "AI-SmartTour"
    debug: bool = False

    # 数据库
    database_url: str = "sqlite+aiosqlite:///./smarttour.db"
    redis_url: str = "redis://localhost:6379/0"

    # LLM配置
    llm_api_key: str = ""
    llm_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"

    # 向量数据库
    vector_db_path: str = "./knowledge_base/vectors"
    knowledge_upload_dir: str = "./uploads"

    # 数字人配置
    digital_human_url: str = "http://localhost:8001"

    # 讯飞虚拟人（Web SDK 安全接入）：apiSecret/apiKey 仅后端持有，不下发前端。
    # 六项核心配置来源：交互平台 - 接口服务；缺任一项则前端自动降级回 VRM。
    xf_avatar_app_id: str = ""
    xf_avatar_api_key: str = ""
    xf_avatar_api_secret: str = ""
    xf_avatar_scene_id: str = ""
    xf_avatar_avatar_id: str = ""
    xf_avatar_vcn: str = ""
    xf_avatar_server_url: str = "wss://avatar.cn-huadong-1.xf-yun.com/v1/interact"

    # ASR/TTS
    asr_model_path: str = "./models/paraformer"
    tts_model_path: str = "./models/cosyvoice"


settings = Settings()
