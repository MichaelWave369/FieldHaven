from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def load_json(path: Path, default: Any) -> Any:
    ensure_dirs()
    if not path.exists():
        save_json(path, default)
        return default
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_json(path: Path, payload: Any) -> None:
    ensure_dirs()
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def backup_data() -> Path:
    ensure_dirs()
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    archive_path = BACKUP_DIR / f"fieldhaven_backup_{stamp}.json"
    snapshot = {}
    for file_path in DATA_DIR.glob("*.json"):
        snapshot[file_path.name] = load_json(file_path, [])
    save_json(archive_path, snapshot)
    return archive_path
