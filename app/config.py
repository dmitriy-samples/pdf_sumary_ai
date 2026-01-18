import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{BASE_DIR}/pdf_summary.db")

# LLM Provider configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()  # "openai", "gemini", or "ionet"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# io.net configuration (OpenAI-compatible API)
IONET_API_KEY = os.getenv("IONET_API_KEY")
IONET_BASE_URL = os.getenv("IONET_BASE_URL", "https://api.intelligence.io.solutions/api/v1")
IONET_MODEL = os.getenv("IONET_MODEL", "deepseek-ai/DeepSeek-V3")

# LLM parameters
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.3"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1500"))

# Rate limiting (requests per minute)
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "5"))

# PDF processing limits
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "50"))
MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
MAX_PAGES = int(os.getenv("MAX_PAGES", "100"))
ALLOWED_EXTENSIONS = {".pdf"}
