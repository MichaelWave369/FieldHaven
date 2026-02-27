from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from core.storage import DATA_DIR, load_json, save_json

SYNC_QUEUE_PATH = Path(DATA_DIR / "sync_queue.json")


def queue_offline_action(action: str, payload: dict[str, Any]) -> dict[str, Any]:
    queue = load_json(SYNC_QUEUE_PATH, [])
    item = {
        "id": f"Q-{len(queue)+1:05}",
        "action": action,
        "payload": payload,
        "created_at": datetime.utcnow().isoformat(),
        "status": "queued",
    }
    queue.append(item)
    save_json(SYNC_QUEUE_PATH, queue)
    return item


def process_sync_queue() -> dict[str, int]:
    queue = load_json(SYNC_QUEUE_PATH, [])
    synced = 0
    for item in queue:
        if item["status"] == "queued":
            item["status"] = "synced"
            item["synced_at"] = datetime.utcnow().isoformat()
            synced += 1
    save_json(SYNC_QUEUE_PATH, queue)
    return {"synced": synced, "remaining": len([i for i in queue if i['status'] != 'synced'])}
