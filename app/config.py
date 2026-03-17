from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SUPABASE_URL: str
    SUPABASE_SERVICE_KEY: str
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    JWT_SECRET: str
    CLOUDFLARE_R2_BUCKET: str = ""
    CLOUDFLARE_R2_ACCOUNT_ID: str = ""
    CLOUDFLARE_R2_ACCESS_KEY: str = ""
    CLOUDFLARE_R2_SECRET_KEY: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
