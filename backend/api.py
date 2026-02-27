from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from core.offline_sync import process_sync_queue
from core.storage import DATA_DIR, backup_data, load_json, save_json
from services.ai_assistant import ask_local_ollama

app = FastAPI(title="FieldHaven API", version="0.3.0")


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


class QuoteRequest(BaseModel):
    scope: str
    labor_hours: float
    parts_cost: float = 0.0


class EscrowRequest(BaseModel):
    job_id: str
    amount: float
    instant_payout: bool = False


class JobMatchRequest(BaseModel):
    technician: str
    home_zip: str = "00000"
    skills: list[str]
    fuel_cost_per_mile: float = 0.67


class MarketplaceItem(BaseModel):
    seller: str
    item: str
    price: float
    condition: str


class CertificationReminder(BaseModel):
    cert: str
    expiry: str
    technician: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fieldhaven-api", "version": "0.3.0"}


@app.get("/jobs")
def list_jobs() -> list[dict]:
    return load_json(Path(DATA_DIR / "jobs.json"), [])


@app.get("/jobs/route/{job_id}")
def route_estimate(job_id: str) -> dict:
    for job in load_json(Path(DATA_DIR / "jobs.json"), []):
        if job["id"] == job_id:
            miles = float(job.get("distance_miles", 10))
            return {"job_id": job_id, "distance_miles": miles, "estimated_drive_minutes": int(miles * 2.1)}
    return {"message": "job not found"}


@app.post("/jobs/match")
def match_jobs(req: JobMatchRequest) -> list[dict]:
    recs = []
    for job in load_json(Path(DATA_DIR / "jobs.json"), []):
        if job.get("status") != "Open":
            continue
        overlap = len(set(req.skills).intersection(set(job.get("skills", []))))
        travel = job.get("distance_miles", 20) * req.fuel_cost_per_mile
        net = job["payout"] - travel
        score = round(net + (overlap * 75) - (job.get("platform_fee", 0) * 6), 2)
        recs.append({**job, "match_score": score, "estimated_travel_cost": round(travel, 2), "estimated_net": round(net, 2)})
    return sorted(recs, key=lambda x: x["match_score"], reverse=True)


@app.post("/jobs/auto-bid")
def auto_bid(req: JobMatchRequest) -> dict:
    ranked = match_jobs(req)
    top = ranked[:2]
    bids = []
    store = load_json(Path(DATA_DIR / "bids.json"), [])
    for job in top:
        amt = round(job["payout"] * 0.98, 2)
        bid = {
            "job_id": job["id"],
            "technician": req.technician,
            "bid_amount": amt,
            "eta_hours": 24,
            "ai_reason": ask_local_ollama(f"Explain briefly why this bid is fair for {job['title']}."),
            "created_at": datetime.utcnow().isoformat(),
        }
        store.append(bid)
        bids.append(bid)
    save_json(Path(DATA_DIR / "bids.json"), store)
    return {"submitted": len(bids), "bids": bids}


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


@app.post("/schedule/auto")
def smart_schedule() -> dict:
    jobs = [j for j in load_json(Path(DATA_DIR / "jobs.json"), []) if j["status"] == "Open"]
    jobs = sorted(jobs, key=lambda j: (j.get("distance_miles", 999), -j.get("payout", 0)))
    schedule = [{"slot": f"Slot {i}", "job_id": j["id"], "location": j["location"]} for i, j in enumerate(jobs, 1)]
    save_json(Path(DATA_DIR / "schedule.json"), schedule)
    return {"message": "Smart schedule generated", "items": len(schedule)}


@app.get("/schedule")
def get_schedule() -> list[dict]:
    return load_json(Path(DATA_DIR / "schedule.json"), [])


@app.post("/quotes/generate")
def generate_quote(req: QuoteRequest) -> dict:
    labor_rate = 95.0
    subtotal = req.labor_hours * labor_rate + req.parts_cost
    quote = {
        "id": f"QTE-{datetime.utcnow().strftime('%H%M%S')}",
        "scope": req.scope,
        "subtotal": round(subtotal, 2),
        "tech_fee_pct": 0.0,
        "total": round(subtotal, 2),
        "suggested_text": ask_local_ollama(f"Write a concise professional quote for: {req.scope}"),
    }
    quotes = load_json(Path(DATA_DIR / "quotes.json"), [])
    quotes.append(quote)
    save_json(Path(DATA_DIR / "quotes.json"), quotes)
    return quote


@app.post("/payments/escrow")
def open_escrow(req: EscrowRequest) -> dict:
    records = load_json(Path(DATA_DIR / "escrow.json"), [])
    fee_pct = 1.5 if req.instant_payout else 0.5
    payload = {
        "id": f"E-{len(records)+1:04}",
        "job_id": req.job_id,
        "amount": req.amount,
        "status": "Funded",
        "instant_payout": req.instant_payout,
        "fee_breakdown": {"platform_fee_pct": fee_pct, "platform_fee_amount": round(req.amount * fee_pct / 100, 2)},
        "guarantee": "US-backed payout protection after completion verification",
    }
    records.append(payload)
    save_json(Path(DATA_DIR / "escrow.json"), records)
    return payload


@app.get("/payments/escrow")
def list_escrow() -> list[dict]:
    return load_json(Path(DATA_DIR / "escrow.json"), [])


@app.get("/analytics/earnings")
def analytics_earnings() -> dict:
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    by_month = {}
    for inv in invoices:
        month = inv.get("generated_on", datetime.utcnow().date().isoformat())[:7]
        by_month[month] = by_month.get(month, 0) + float(inv.get("amount", 0))
    heatmap = [{"location": j["location"], "jobs": 1, "avg_payout": j["payout"]} for j in jobs]
    return {"earnings_by_month": by_month, "job_heatmap": heatmap, "total_jobs": len(jobs)}


@app.post("/exports/quickbooks")
def export_quickbooks() -> dict:
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    rows = ["InvoiceID,Client,Amount,Status"]
    for inv in invoices:
        rows.append(f"{inv.get('id','')},{inv.get('client','')},{inv.get('amount',0)},{inv.get('status','')}")
    content = "\n".join(rows)
    exports = load_json(Path(DATA_DIR / "exports.json"), [])
    record = {"id": f"X-{len(exports)+1:04}", "kind": "quickbooks_csv", "content": content}
    exports.append(record)
    save_json(Path(DATA_DIR / "exports.json"), exports)
    return record


@app.get("/community/posts")
def list_posts() -> list[dict]:
    return load_json(Path(DATA_DIR / "community_posts.json"), [])


@app.post("/community/mentorship/match")
def mentorship_match(payload: dict) -> dict:
    data = load_json(Path(DATA_DIR / "mentor_matches.json"), [])
    rec = {"id": f"MM-{len(data)+1:04}", **payload, "matched": "US-Mentor-01"}
    data.append(rec)
    save_json(Path(DATA_DIR / "mentor_matches.json"), data)
    return rec


@app.get("/community/success-stories")
def success_stories() -> list[dict]:
    return load_json(Path(DATA_DIR / "success_stories.json"), [])


@app.get("/community/leaderboard")
def leaderboard() -> list[dict]:
    return load_json(Path(DATA_DIR / "leaderboard.json"), [])


@app.get("/community/events")
def events() -> list[dict]:
    return load_json(Path(DATA_DIR / "events.json"), [])


@app.get("/clients/ratings")
def list_client_ratings() -> list[dict]:
    return load_json(Path(DATA_DIR / "client_ratings.json"), [])


@app.post("/disputes/vote")
def dispute_vote(vote: dict) -> dict:
    disputes = load_json(Path(DATA_DIR / "disputes.json"), [])
    did = vote.get("dispute_id", "D-0001")
    target = next((d for d in disputes if d.get("id") == did), None)
    if target is None:
        target = {"id": did, "votes": [], "status": "Open", "mediator": "US Neutral Mediator"}
        disputes.append(target)
    target["votes"].append(vote)
    save_json(Path(DATA_DIR / "disputes.json"), disputes)
    return {"message": "Community vote recorded", "dispute": target}


@app.get("/insurance/marketplace")
def insurance_marketplace() -> list[dict]:
    data = load_json(Path(DATA_DIR / "insurance_marketplace.json"), [])
    if not data:
        data = [
            {"carrier": "Liberty Tech Shield", "product": "General Liability", "rate_note": "Tech-friendly monthly options"},
            {"carrier": "US Bond Works", "product": "Performance Bond", "rate_note": "Discounts for verified track record"},
        ]
        save_json(Path(DATA_DIR / "insurance_marketplace.json"), data)
    return data


@app.get("/equipment/marketplace")
def equipment_marketplace() -> list[dict]:
    return load_json(Path(DATA_DIR / "equipment_marketplace.json"), [])


@app.post("/equipment/marketplace")
def add_equipment(item: MarketplaceItem) -> dict:
    data = load_json(Path(DATA_DIR / "equipment_marketplace.json"), [])
    rec = {"id": f"EQ-{len(data)+1:03}", **item.model_dump()}
    data.append(rec)
    save_json(Path(DATA_DIR / "equipment_marketplace.json"), data)
    return rec


@app.post("/compliance/certifications")
def add_certification(reminder: CertificationReminder) -> dict:
    data = load_json(Path(DATA_DIR / "certifications.json"), [])
    rec = {"id": f"C-{len(data)+1:03}", **reminder.model_dump(), "reminder_sent": False}
    data.append(rec)
    save_json(Path(DATA_DIR / "certifications.json"), data)
    return rec


@app.get("/compliance/certifications")
def list_certifications() -> list[dict]:
    return load_json(Path(DATA_DIR / "certifications.json"), [])


@app.post("/support/ticket")
def create_support_ticket(ticket: SupportTicket) -> dict:
    tickets = load_json(Path(DATA_DIR / "tickets.json"), [])
    payload = {**ticket.model_dump(), "id": f"T-{len(tickets)+1:04}", "created_at": datetime.utcnow().isoformat(), "sla": "US-human callback <2 business hours"}
    tickets.append(payload)
    save_json(Path(DATA_DIR / "tickets.json"), tickets)
    return payload


@app.post("/support/live-chat")
def live_chat(msg: dict) -> dict:
    chats = load_json(Path(DATA_DIR / "chat_messages.json"), [])
    payload = {"id": f"C-{len(chats)+1:04}", **msg, "agent": "US Support Team", "response": "US support specialist connected."}
    chats.append(payload)
    save_json(Path(DATA_DIR / "chat_messages.json"), chats)
    return payload


@app.get("/support/knowledge-base")
def knowledge_base() -> list[dict]:
    return load_json(Path(DATA_DIR / "knowledge_base.json"), [])


@app.post("/support/emergency")
def emergency_help() -> dict:
    return {"message": "Emergency escalation opened", "phone": "1-800-FIELD-US", "created_at": datetime.utcnow().isoformat()}


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
    rec = {"id": f"M-{len(data)+1:04}", "payload": payload, "saved_at": datetime.utcnow().isoformat()}
    data.append(rec)
    save_json(Path(DATA_DIR / "memoria.json"), data)
    return rec


@app.post("/integrations/littup/code-job")
def littup_code_job(payload: dict) -> dict:
    return {"provider": "LittUp", "status": "queued", "payload": payload}


@app.post("/backup")
def create_backup() -> dict:
    path = backup_data()
    return {"message": "Backup created", "file": str(path)}
