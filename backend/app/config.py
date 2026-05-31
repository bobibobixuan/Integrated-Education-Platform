import sys
from pathlib import Path
from pydantic import ConfigDict
from pydantic_settings import BaseSettings


def _get_base_dir() -> Path:
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def _ensure_data_dir(base: Path) -> Path:
    data_dir = base / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


class Settings(BaseSettings):
    DATABASE_URL: str = f"sqlite:///{_ensure_data_dir(_get_base_dir()) / 'app.dev-copy.db'}"
    JWT_SECRET: str = "change-me-in-production-use-a-random-64-char-string"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    model_config = ConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
    )

    def model_post_init(self, __context):
        default = "change-me-in-production-use-a-random-64-char-string"
        if self.JWT_SECRET == default:
            import warnings
            warnings.warn(
                "JWT_SECRET 仍为默认值！请通过 .env 文件或环境变量设置一个随机 64 字符密钥。"
                "生产环境使用默认密钥导致任意用户可伪造登录令牌。"
            )


settings = Settings()
