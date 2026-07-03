from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_FILE = PROJECT_ROOT / ".env"


def load_project_env(*, env_path: Path | None = None) -> bool:
    """Load environment variables from a .env file without overriding existing values."""
    target = env_path if env_path is not None else DEFAULT_ENV_FILE
    if not target.is_file():
        return False

    try:
        from dotenv import load_dotenv
    except ImportError:
        return False

    load_dotenv(target, override=False)
    return True
