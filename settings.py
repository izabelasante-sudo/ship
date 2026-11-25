"""Load local settings without putting credentials in source code."""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(os.getenv("LAB_ENV_FILE", str(Path(__file__).with_name(".env"))))


def allowed_statistics() -> set[str]:
    return {s.strip() for s in os.getenv("REDIS_ALLOWED_KEYS", "shipwreck_summary,water_level_counts").split(",") if s.strip()}
