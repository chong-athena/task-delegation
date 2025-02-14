# backend/app/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SLACK_TOKEN: str
    CHANNEL_ID: str
    OPEN_AI_API_KEY: str

    class Config:
        env_file = ".env"  # Path to your .env file

# Instantiate a single settings instance
settings = Settings()