"""
Configuration — load all settings from environment variables.
Copy .env.example to .env and fill in your keys.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ── API Keys ──────────────────────────────────────────────────────────────────
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
SERPAPI_KEY: str = os.getenv("SERPAPI_KEY", "")

# ── LLM Settings ──────────────────────────────────────────────────────────────
GEMINI_MODEL: str = "gemini-2.5-flash"
GEMINI_EMBEDDING_MODEL: str = "models/text-embedding-004"

# ── SerpAPI Settings ──────────────────────────────────────────────────────────
SERPAPI_MAX_RESULTS: int = 20          # articles per daily run
SERPAPI_TIME_PERIOD: str = "d"         # past 24h

# ── Scraping ──────────────────────────────────────────────────────────────────
SCRAPE_TIMEOUT_SECONDS: int = 15
SCRAPE_MAX_RETRIES: int = 2
MIN_ARTICLE_LENGTH: int = 200          # shorter articles are discarded

# ── Scheduler ─────────────────────────────────────────────────────────────────
SCHEDULE_HOUR: int = int(os.getenv("SCHEDULE_HOUR", "8"))    # 8 AM daily
SCHEDULE_MINUTE: int = int(os.getenv("SCHEDULE_MINUTE", "0"))

# ── Output ────────────────────────────────────────────────────────────────────
REPORTS_DIR: str = os.getenv("REPORTS_DIR", "./reports")
