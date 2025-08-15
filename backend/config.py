import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "secret123")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost/interview_db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

    # Gemini API
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_key")
    GEMINI_API_KEY1 = os.getenv("GEMINI_API_KEY1", "your_gemini_key1")
    GEMINI_API_KEY2 = os.getenv("GEMINI_API_KEY2", "your_gemini_key2")
    GEMINI_API_KEY3 = os.getenv("GEMINI_API_KEY3", "your_gemini_key3")
    GEMINI_API_KEY4 = os.getenv("GEMINI_API_KEY4", "your_gemini_key4")
    GEMINI_API_KEY5 = os.getenv("GEMINI_API_KEY5", "your_gemini_key5")
    GEMINI_API_KEY6 = os.getenv("GEMINI_API_KEY6", "your_gemini_key6")
    GEMINI_API_KEY7 = os.getenv("GEMINI_API_KEY7", "your_gemini_key7")
    GEMINI_API_KEY8 = os.getenv("GEMINI_API_KEY8", "your_gemini_key8")
    GEMINI_API_KEY9 = os.getenv("GEMINI_API_KEY9", "your_gemini_key9")
    GEMINI_API_KEY10 = os.getenv("GEMINI_API_KEY10", "your_gemini_key10")
    GEMINI_API_KEY11 = os.getenv("GEMINI_API_KEY11", "your_gemini_key11")
    GEMINI_API_KEY12 = os.getenv("GEMINI_API_KEY12", "your_gemini_key12")
    GEMINI_API_KEY13 = os.getenv("GEMINI_API_KEY13", "your_gemini_key13")
    GEMINI_API_KEY14 = os.getenv("GEMINI_API_KEY14", "your_gemini_key14")
