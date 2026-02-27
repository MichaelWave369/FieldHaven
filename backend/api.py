from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from core.offline_sync import process_sync_queue
from core.storage import DATA_DIR, backup_data, load_json, save_json
from services.ai_assistant import ask_local_ollama

app = FastAPI(title="FieldHaven API", version="0.2.0")


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


class ChatMessage(BaseModel):
    technician: str
    message: str


class QuoteRequest(BaseModel):
    scope: str
    labor_hours: float
    parts_cost: float = 0.0


class EscrowRequest(BaseModel):
    job_id: str
    amount: float


class DisputeVote(BaseModel):
    dispute_id: str
    voter: str
    vote: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fieldhaven-api", "version": "0.2.0"}


@app.get("/jobs")
def list_jobs() -> list[dict]:
    return load_json(Path(DATA_DIR / "jobs.json"), [])


@app.get("/jobs/route/{job_id}")
def route_estimate(job_id: str) -> dict:
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    for job in jobs:
        if job["id"] == job_id:
            miles = float(job.get("distance_miles", 10))
            return {"job_id": job_id, "distance_miles": miles, "estimated_drive_minutes": int(miles * 2.1)}
    return {"message": "job not found"}


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


@app.get("/schedule")
def get_schedule() -> list[dict]:
    return load_json(Path(DATA_DIR / "schedule.json"), [])


@app.post("/schedule/auto")
def smart_schedule() -> dict:
    jobs = [job for job in load_json(Path(DATA_DIR / "jobs.json"), []) if job["status"] == "Open"]
    jobs = sorted(jobs, key=lambda j: (j.get("distance_miles", 999), -j.get("payout", 0)))
    schedule = []
    for index, job in enumerate(jobs, start=1):
        schedule.append({"slot": f"Slot {index}", "job_id": job["id"], "location": job["location"]})
    save_json(Path(DATA_DIR / "schedule.json"), schedule)
    return {"message": "Smart schedule generated", "items": len(schedule)}


@app.get("/community/posts")
def list_posts() -> list[dict]:
    return load_json(Path(DATA_DIR / "community_posts.json"), [])


@app.get("/community/success-stories")
def success_stories() -> list[dict]:
    return load_json(Path(DATA_DIR / "success_stories.json"), [])


@app.get("/resources")
def resources() -> list[dict]:
    return load_json(Path(DATA_DIR / "resources.json"), [])


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


@app.post("/support/live-chat")
def live_chat(msg: ChatMessage) -> dict:
    chats = load_json(Path(DATA_DIR / "chat_messages.json"), [])
    payload = {
        "id": f"C-{len(chats)+1:04}",
        **msg.model_dump(),
        "agent": "US Support Team",
        "response": "A US-based support specialist will reply shortly.",
        "created_at": datetime.utcnow().isoformat(),
    }
    chats.append(payload)
    save_json(Path(DATA_DIR / "chat_messages.json"), chats)
    return payload


@app.get("/support/knowledge-base")
def knowledge_base() -> list[dict]:
    return load_json(Path(DATA_DIR / "knowledge_base.json"), [])


@app.post("/support/emergency")
def emergency_help() -> dict:
    return {
        "message": "Emergency escalation opened with US rapid response.",
        "phone": "1-800-FIELD-US",
        "created_at": datetime.utcnow().isoformat(),
    }


@app.post("/quotes/generate")
def generate_quote(req: QuoteRequest) -> dict:
    labor_rate = 95.0
    subtotal = req.labor_hours * labor_rate + req.parts_cost
    fee_pct = 0.0
    total = subtotal * (1 + fee_pct / 100)
    ai_hint = ask_local_ollama(f"Write a short professional quote for scope: {req.scope}")
    quote = {
        "id": f"QTE-{datetime.utcnow().strftime('%H%M%S')}",
        "scope": req.scope,
        "labor_hours": req.labor_hours,
        "parts_cost": req.parts_cost,
        "subtotal": round(subtotal, 2),
        "tech_fee_pct": fee_pct,
        "total": round(total, 2),
        "suggested_text": ai_hint,
    }
    quotes = load_json(Path(DATA_DIR / "quotes.json"), [])
    quotes.append(quote)
    save_json(Path(DATA_DIR / "quotes.json"), quotes)
    return quote


@app.post("/payments/escrow")
def open_escrow(req: EscrowRequest) -> dict:
    records = load_json(Path(DATA_DIR / "escrow.json"), [])
    payload = {
        "id": f"E-{len(records)+1:04}",
        "job_id": req.job_id,
        "amount": req.amount,
        "status": "Funded",
        "guarantee": "Payout protected after completion verification",
    }
    records.append(payload)
    save_json(Path(DATA_DIR / "escrow.json"), records)
    return payload


@app.get("/payments/escrow")
def list_escrow() -> list[dict]:
    return load_json(Path(DATA_DIR / "escrow.json"), [])


@app.post("/disputes/vote")
def dispute_vote(vote: DisputeVote) -> dict:
    disputes = load_json(Path(DATA_DIR / "disputes.json"), [])
    target = next((d for d in disputes if d.get("id") == vote.dispute_id), None)
    if target is None:
        target = {"id": vote.dispute_id, "votes": [], "status": "Open"}
        disputes.append(target)
    target["votes"].append(vote.model_dump())
    save_json(Path(DATA_DIR / "disputes.json"), disputes)
    return {"message": "Community vote recorded", "dispute": target}


@app.post("/assistant")
def assistant(req: AIRequest) -> dict:
    return {"response": ask_local_ollama(req.prompt, req.model)}


@app.post("/offline/sync")
def sync_offline() -> dict:
    return process_sync_queue()


@app.post("/integrations/agentora/quote")
def agentora_quote(req: AIRequest) -> dict:
    return {"provider": "Agentora", "response": ask_local_ollama(req.prompt, req.model)}


@app.post("/integrations/agentora/troubleshoot")
def agentora_troubleshoot(req: AIRequest) -> dict:
    return {"provider": "Agentora", "response": ask_local_ollama(req.prompt, req.model)}


@app.post("/integrations/memoria/save")
def memoria_save(payload: dict) -> dict:
    data = load_json(Path(DATA_DIR / "memoria.json"), [])
    record = {"id": f"M-{len(data)+1:04}", "payload": payload, "saved_at": datetime.utcnow().isoformat()}
    data.append(record)
    save_json(Path(DATA_DIR / "memoria.json"), data)
    return record


@app.post("/integrations/littup/code-job")
def littup_code_job(payload: dict) -> dict:
    return {"provider": "LittUp", "status": "queued", "payload": payload}


@app.post("/backup")
def create_backup() -> dict:
    path = backup_data()
    return {"message": "Backup created", "file": str(path)}
