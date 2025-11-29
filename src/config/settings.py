import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DELTA_API_KEY = os.getenv("DELTA_API_KEY")
    DELTA_API_SECRET = os.getenv("DELTA_API_SECRET")
    DATABASE_URL = os.getenv("DATABASE_URL")
    GROQ_API_KEYS = [os.getenv(f"GROQ_API_KEY_{i}") for i in range(1, 10) if os.getenv(f"GROQ_API_KEY_{i}")]

settings = Settings()
