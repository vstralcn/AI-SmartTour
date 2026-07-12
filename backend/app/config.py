"""应用配置"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    # 应用配置
    app_name: str = "AI-SmartTour"
    debug: bool = False

    # 数据库
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/smarttour"
    redis_url: str = "redis://localhost:6379/0"

    # LLM配置
    llm_api_key: str = ""
    llm_api_base: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen-plus"

    # 向量数据库
    vector_db_path: str = "./knowledge_base/vectors"

    # 数字人配置
    digital_human_url: str = "http://localhost:8001"

    # ASR/TTS
    asr_model_path: str = "./models/paraformer"
    tts_model_path: str = "./models/cosyvoice"

settings = Settings()
