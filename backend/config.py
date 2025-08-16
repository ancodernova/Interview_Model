import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    # Prisma (Postgres via Railway)
    DATABASE_URL = os.getenv("DATABASE_URL")  

    SECRET_KEY = os.getenv("SECRET_KEY", "super-secret")  
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-jwt")

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    # Gemini API keys (rotation pool)
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_API_KEY1 = os.getenv("GEMINI_API_KEY1", "")
    GEMINI_API_KEY2 = os.getenv("GEMINI_API_KEY2", "")
    GEMINI_API_KEY3 = os.getenv("GEMINI_API_KEY3", "")
    GEMINI_API_KEY4 = os.getenv("GEMINI_API_KEY4", "")
    GEMINI_API_KEY5 = os.getenv("GEMINI_API_KEY5", "")
    GEMINI_API_KEY6 = os.getenv("GEMINI_API_KEY6", "")
    GEMINI_API_KEY7 = os.getenv("GEMINI_API_KEY7", "")
    GEMINI_API_KEY8 = os.getenv("GEMINI_API_KEY8", "")
    GEMINI_API_KEY9 = os.getenv("GEMINI_API_KEY9", "")
    GEMINI_API_KEY10 = os.getenv("GEMINI_API_KEY10", "")
    GEMINI_API_KEY11 = os.getenv("GEMINI_API_KEY11", "")
    GEMINI_API_KEY12 = os.getenv("GEMINI_API_KEY12", "")
    GEMINI_API_KEY13 = os.getenv("GEMINI_API_KEY13", "")
    GEMINI_API_KEY14 = os.getenv("GEMINI_API_KEY14", "")
