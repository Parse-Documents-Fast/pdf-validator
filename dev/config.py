from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    http_addr: str = ":8000"
    max_file_size_mb: int = 10

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }

settings = Settings()
