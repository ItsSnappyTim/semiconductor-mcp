import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]

_whitepaper_dir = os.environ.get("WHITEPAPER_DIR", "")
WHITEPAPER_DIR = Path(_whitepaper_dir) if _whitepaper_dir else PROJECT_ROOT / "data" / "whitepapers"

_db_path = os.environ.get("DB_PATH", "")
DB_PATH = Path(_db_path) if _db_path else PROJECT_ROOT / "data" / "whitepapers.db"

PORT = int(os.environ.get("PORT", 8000))

NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY", "")
MCP_AUTH_TOKEN = os.environ.get("MCP_AUTH_TOKEN", "")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ENABLE_EVAL = os.environ.get("ENABLE_EVAL", "").strip().lower() in {"1", "true", "yes"}

# Model configuration for eval tools (override to use different models for
# generation vs scoring — useful for cost/quality trade-offs)
GENERATION_MODEL = os.environ.get("GENERATION_MODEL", "claude-haiku-4-5-20251001")
EVAL_MODEL = os.environ.get("EVAL_MODEL", "claude-haiku-4-5-20251001")

# Server hardening
RATE_LIMIT_RPM = int(os.environ.get("RATE_LIMIT_RPM", "120"))
MAX_REQUEST_BODY_BYTES = int(os.environ.get("MAX_REQUEST_BODY_BYTES", str(1 * 1024 * 1024)))

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# Optional: UN Comtrade trade flow API (free key at comtradeapi.un.org)
COMTRADE_API_KEY = os.environ.get("COMTRADE_API_KEY", "")

# Optional: ITA Consolidated Screening List (free key at developer.trade.gov)
ITA_API_KEY = os.environ.get("ITA_API_KEY", "")

# Optional: OpenSanctions API key (free tier at opensanctions.org/api/)
OPENSANCTIONS_API_KEY = os.environ.get("OPENSANCTIONS_API_KEY", "")


def validate_config() -> None:
    if not NEWSAPI_KEY:
        raise ValueError("NEWSAPI_KEY environment variable is required")
    if not MCP_AUTH_TOKEN:
        raise ValueError("MCP_AUTH_TOKEN environment variable is required")
    if ENABLE_EVAL and not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY is required when ENABLE_EVAL is set")
