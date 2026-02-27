from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from core.storage import DATA_DIR, backup_data, load_json, save_json
from services.ai_assistant import ask_local_ollama

app = FastAPI(title="FieldHaven API", version="0.1.0")


class BidRequest(BaseModel):
    job_id: str
    technician: str
    bid_amount: float
    eta_hours: int = 24


class AcceptRequest(BaseModel):
    job_id: str
    technician: str


class SupportTicket(BaseModel):
    technician: str
    channel: str
    issue: str


class AIRequest(BaseModel):
    prompt: str
    model: str = "llama3.1"


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fieldhaven-api"}


@app.get("/jobs")
def list_jobs() -> list[dict]:
    return load_json(Path(DATA_DIR / "jobs.json"), [])


@app.post("/jobs/bid")
def submit_bid(req: BidRequest) -> dict:
    bids_path = Path(DATA_DIR / "bids.json")
    bids = load_json(bids_path, [])
    bids.append({**req.model_dump(), "created_at": datetime.utcnow().isoformat()})
    save_json(bids_path, bids)
    return {"message": "Bid submitted with transparent terms.", "bid": req.model_dump()}


@app.post("/jobs/accept")
def accept_job(req: AcceptRequest) -> dict:
    jobs_path = Path(DATA_DIR / "jobs.json")
    jobs = load_json(jobs_path, [])
    for job in jobs:
        if job["id"] == req.job_id and job["status"] == "Open":
            job["status"] = "Assigned"
            job["accepted_by"] = req.technician
            save_json(jobs_path, jobs)
            return {"message": "Job accepted under FieldHaven fair terms.", "job": job}
    return {"message": "Job not open or not found."}


@app.get("/community/posts")
def list_posts() -> list[dict]:
    return load_json(Path(DATA_DIR / "community_posts.json"), [])


@app.get("/clients/ratings")
def list_client_ratings() -> list[dict]:
    return load_json(Path(DATA_DIR / "client_ratings.json"), [])


@app.post("/support/ticket")
def create_support_ticket(ticket: SupportTicket) -> dict:
    tickets_path = Path(DATA_DIR / "tickets.json")
    tickets = load_json(tickets_path, [])
    payload = {
        **ticket.model_dump(),
        "id": f"T-{len(tickets)+1:04}",
        "created_at": datetime.utcnow().isoformat(),
        "sla": "US-based human callback < 2 business hours",
    }
    tickets.append(payload)
    save_json(tickets_path, tickets)
    return payload


@app.post("/assistant")
def assistant(req: AIRequest) -> dict:
    return {"response": ask_local_ollama(req.prompt, req.model)}


@app.post("/backup")
def create_backup() -> dict:
    path = backup_data()
    return {"message": "Backup created", "file": str(path)}
