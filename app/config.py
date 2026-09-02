import os
from pathlib import Path
from dataclasses import dataclass

# Load .env file from project root
ROOT_DIR = Path(__file__).resolve().parent.parent
dotenv_path = ROOT_DIR / ".env"

try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=dotenv_path)
except ImportError:
    pass


@dataclass(frozen=True)
class Settings:
    # Sarvam AI
    SARVAM_API_KEY: str = os.getenv("SARVAM_API_KEY", "")
    SARVAM_MODEL: str = os.getenv("SARVAM_MODEL", "saaras:v4")
    SARVAM_DEFAULT_LANGUAGE: str = os.getenv("SARVAM_DEFAULT_LANGUAGE", "kn-IN")

    # Groq LLM
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")

    # Twilio
    TWILIO_SID: str = os.getenv("TWILIO_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_PHONE_NUMBER: str = os.getenv("TWILIO_PHONE_NUMBER", "")

    # MySQL Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "password")
    DB_NAME: str = os.getenv("DB_NAME", "agrimatch")

    # Server Settings
    API_HOST: str = os.getenv("API_HOST", "127.0.0.1")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))
    API_URL: str = os.getenv("API_URL", "http://127.0.0.1:8000/process-voice")

    # Matching Logic
    MATCH_RADIUS_KM: float = float(os.getenv("MATCH_RADIUS_KM", "50.0"))

    # Ngrok Tunneling
    NGROK_DOMAIN: str = os.getenv("NGROK_DOMAIN", "")
    NGROK_AUTHTOKEN: str = os.getenv("NGROK_AUTHTOKEN", "")


settings = Settings()

