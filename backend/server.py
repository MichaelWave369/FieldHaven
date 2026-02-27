from __future__ import annotations

import threading

import uvicorn


_server_started = False


def run_api() -> None:
    uvicorn.run("backend.api:app", host="127.0.0.1", port=8008, log_level="warning")


def start_embedded_api() -> None:
    global _server_started
    if _server_started:
        return
    thread = threading.Thread(target=run_api, daemon=True)
    thread.start()
    _server_started = True
