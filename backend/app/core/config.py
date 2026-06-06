from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    app_name: str = "real-time-financial-analytics-platform"
    environment: str = "local"
    database_url: str = "postgresql+psycopg2://finuser:finpass@localhost:5432/finanalytics"
    redis_url: str = "redis://localhost:6379/0"
    kafka_bootstrap_servers: str = "localhost:9092"
    jwt_secret_key: str = "change-me-in-production"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
