from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from core.offline_sync import process_sync_queue
from core.storage import DATA_DIR, backup_data, load_json, save_json
from services.ai_assistant import ask_local_ollama

app = FastAPI(title="FieldHaven API", version="0.4.0")


class JobMatchRequest(BaseModel):
    technician: str
    skills: list[str]
    fuel_cost_per_mile: float = 0.67


class EscrowRequest(BaseModel):
    job_id: str
    amount: float
    instant_payout: bool = False


class QuoteRequest(BaseModel):
    scope: str
    labor_hours: float
    parts_cost: float = 0.0


class TeamAssignRequest(BaseModel):
    team_id: str
    job_id: str
    technician: str


class CrewChatMessage(BaseModel):
    team_id: str
    sender: str
    message: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fieldhaven-api", "version": "0.4.0"}


@app.get("/jobs")
def list_jobs() -> list[dict]:
    return load_json(Path(DATA_DIR / "jobs.json"), [])


@app.post("/jobs/match")
def match_jobs(req: JobMatchRequest) -> list[dict]:
    scored: list[dict] = []
    for job in load_json(Path(DATA_DIR / "jobs.json"), []):
        if job.get("status") != "Open":
            continue
        overlap = len(set(req.skills) & set(job.get("skills", [])))
        travel = float(job.get("distance_miles", 20)) * req.fuel_cost_per_mile
        net = float(job["payout"]) - travel
        score = round(net + overlap * 80 - float(job.get("platform_fee", 0)) * 6, 2)
        scored.append({**job, "match_score": score, "estimated_net": round(net, 2), "estimated_travel_cost": round(travel, 2)})
    return sorted(scored, key=lambda j: j["match_score"], reverse=True)


@app.post("/jobs/auto-bid")
def auto_bid(req: JobMatchRequest) -> dict:
    ranked = match_jobs(req)[:3]
    bids = load_json(Path(DATA_DIR / "bids.json"), [])
    new_bids = []
    for job in ranked:
        bid = {
            "job_id": job["id"],
            "technician": req.technician,
            "bid_amount": round(job["payout"] * 0.98, 2),
            "eta_hours": 24,
            "created_at": datetime.utcnow().isoformat(),
            "ai_reason": ask_local_ollama(f"Why is this a fair competitive bid? {job['title']}"),
        }
        new_bids.append(bid)
        bids.append(bid)
    save_json(Path(DATA_DIR / "bids.json"), bids)
    return {"submitted": len(new_bids), "bids": new_bids}


@app.post("/quotes/generate")
def generate_quote(req: QuoteRequest) -> dict:
    subtotal = req.labor_hours * 95.0 + req.parts_cost
    quote = {
        "id": f"QTE-{datetime.utcnow().strftime('%H%M%S')}",
        "scope": req.scope,
        "subtotal": round(subtotal, 2),
        "total": round(subtotal, 2),
        "suggested_text": ask_local_ollama(f"Create professional quote language: {req.scope}"),
    }
    quotes = load_json(Path(DATA_DIR / "quotes.json"), [])
    quotes.append(quote)
    save_json(Path(DATA_DIR / "quotes.json"), quotes)
    return quote


@app.post("/payments/escrow")
def open_escrow(req: EscrowRequest) -> dict:
    data = load_json(Path(DATA_DIR / "escrow.json"), [])
    fee_pct = 1.5 if req.instant_payout else 0.5
    rec = {
        "id": f"E-{len(data)+1:04}",
        "job_id": req.job_id,
        "amount": req.amount,
        "status": "Funded",
        "instant_payout": req.instant_payout,
        "fee_breakdown": {"platform_fee_pct": fee_pct, "platform_fee_amount": round(req.amount * fee_pct / 100, 2)},
    }
    data.append(rec)
    save_json(Path(DATA_DIR / "escrow.json"), data)
    return rec


@app.get("/payments/escrow")
def list_escrow() -> list[dict]:
    return load_json(Path(DATA_DIR / "escrow.json"), [])


@app.post("/teams/assign")
def team_assign(req: TeamAssignRequest) -> dict:
    assignments = load_json(Path(DATA_DIR / "team_assignments.json"), [])
    rec = {"id": f"TA-{len(assignments)+1:04}", **req.model_dump(), "assigned_at": datetime.utcnow().isoformat()}
    assignments.append(rec)
    save_json(Path(DATA_DIR / "team_assignments.json"), assignments)
    return rec


@app.get("/teams/calendar/{team_id}")
def team_calendar(team_id: str) -> list[dict]:
    assignments = load_json(Path(DATA_DIR / "team_assignments.json"), [])
    return [a for a in assignments if a["team_id"] == team_id]


@app.post("/teams/chat")
def crew_chat(msg: CrewChatMessage) -> dict:
    chats = load_json(Path(DATA_DIR / "crew_chat.json"), [])
    rec = {"id": f"CC-{len(chats)+1:04}", **msg.model_dump(), "created_at": datetime.utcnow().isoformat()}
    chats.append(rec)
    save_json(Path(DATA_DIR / "crew_chat.json"), chats)
    return rec


@app.get("/teams/chat/{team_id}")
def crew_chat_history(team_id: str) -> list[dict]:
    chats = load_json(Path(DATA_DIR / "crew_chat.json"), [])
    return [c for c in chats if c["team_id"] == team_id]


@app.get("/analytics/business")
def analytics_business() -> dict:
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    total_earnings = sum(float(i.get("amount", 0)) for i in invoices)
    avg_payout = round(sum(float(j.get("payout", 0)) for j in jobs) / max(1, len(jobs)), 2)
    profitable = sorted(jobs, key=lambda j: float(j.get("payout", 0)) - float(j.get("distance_miles", 0)) * 0.67, reverse=True)[:5]
    tax_estimate = round(total_earnings * 0.24, 2)
    return {
        "total_earnings": total_earnings,
        "avg_job_payout": avg_payout,
        "estimated_tax_reserve": tax_estimate,
        "top_profitable_jobs": profitable,
        "client_patterns": load_json(Path(DATA_DIR / "client_ratings.json"), []),
    }


@app.post("/advisor/business")
def ai_business_advisor(payload: dict) -> dict:
    context = payload.get("context", "pricing, marketing, growth")
    response = ask_local_ollama(f"As an American field service business advisor, suggest 5 actions for: {context}")
    return {"advisor": "local-ai", "response": response}


@app.get("/vendor/marketplace")
def vendor_marketplace() -> list[dict]:
    data = load_json(Path(DATA_DIR / "vendor_marketplace.json"), [])
    if not data:
        data = [
            {"vendor": "USA Tool Direct", "category": "Tools", "discount": "12% tech-only"},
            {"vendor": "Patriot Fleet Vans", "category": "Vehicles", "discount": "Lease rebates"},
            {"vendor": "ShieldLine Insurance", "category": "Insurance", "discount": "Preferred tech rates"},
            {"vendor": "American Parts Grid", "category": "Parts", "discount": "Bulk crew pricing"},
        ]
        save_json(Path(DATA_DIR / "vendor_marketplace.json"), data)
    return data


@app.post("/vendor/financing")
def vendor_financing(payload: dict) -> dict:
    requests = load_json(Path(DATA_DIR / "financing_requests.json"), [])
    rec = {"id": f"F-{len(requests)+1:04}", **payload, "status": "prequalified", "created_at": datetime.utcnow().isoformat()}
    requests.append(rec)
    save_json(Path(DATA_DIR / "financing_requests.json"), requests)
    return rec


@app.post("/offline/sync")
def sync_offline() -> dict:
    return process_sync_queue()


@app.post("/offline/resolve-conflict")
def resolve_conflict(payload: dict) -> dict:
    log = load_json(Path(DATA_DIR / "sync_conflicts.json"), [])
    rec = {"id": f"SC-{len(log)+1:04}", **payload, "resolved_at": datetime.utcnow().isoformat()}
    log.append(rec)
    save_json(Path(DATA_DIR / "sync_conflicts.json"), log)
    return rec


@app.get("/notifications/push")
def push_notifications() -> list[dict]:
    return load_json(Path(DATA_DIR / "notifications.json"), [])


@app.post("/notifications/push")
def create_push_notification(payload: dict) -> dict:
    notes = load_json(Path(DATA_DIR / "notifications.json"), [])
    rec = {"id": f"N-{len(notes)+1:04}", **payload, "created_at": datetime.utcnow().isoformat()}
    notes.append(rec)
    save_json(Path(DATA_DIR / "notifications.json"), notes)
    return rec


@app.post("/vault/export")
def vault_export() -> dict:
    snapshot = {}
    for p in Path(DATA_DIR).glob("*.json"):
        snapshot[p.name] = load_json(p, [])
    exports = load_json(Path(DATA_DIR / "vault_exports.json"), [])
    rec = {"id": f"V-{len(exports)+1:04}", "created_at": datetime.utcnow().isoformat(), "files": len(snapshot), "snapshot": snapshot}
    exports.append(rec)
    save_json(Path(DATA_DIR / "vault_exports.json"), exports)
    return {"id": rec["id"], "created_at": rec["created_at"], "files": rec["files"]}


@app.post("/privacy/settings")
def privacy_settings(payload: dict) -> dict:
    save_json(Path(DATA_DIR / "privacy_settings.json"), payload)
    return payload


@app.get("/audit/logs")
def audit_logs() -> list[dict]:
    return load_json(Path(DATA_DIR / "audit_logs.json"), [])


@app.post("/audit/logs")
def create_audit_log(payload: dict) -> dict:
    logs = load_json(Path(DATA_DIR / "audit_logs.json"), [])
    rec = {"id": f"A-{len(logs)+1:04}", **payload, "timestamp": datetime.utcnow().isoformat()}
    logs.append(rec)
    save_json(Path(DATA_DIR / "audit_logs.json"), logs)
    return rec


@app.get("/governance/features")
def governance_features() -> list[dict]:
    return load_json(Path(DATA_DIR / "feature_votes.json"), [])


@app.post("/governance/features")
def governance_vote(payload: dict) -> dict:
    votes = load_json(Path(DATA_DIR / "feature_votes.json"), [])
    rec = {"id": f"GV-{len(votes)+1:04}", **payload, "created_at": datetime.utcnow().isoformat()}
    votes.append(rec)
    save_json(Path(DATA_DIR / "feature_votes.json"), votes)
    return rec


@app.get("/triad/sso")
def triad_sso() -> dict:
    return {"agentora": "connected", "memoria": "connected", "littup": "connected", "mode": "local-dev-sso"}


@app.post("/integrations/agentora/quote")
def agentora_quote(payload: dict) -> dict:
    prompt = payload.get("prompt", "")
    return {"provider": "Agentora", "response": ask_local_ollama(prompt)}


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


@app.get("/resources")
def resources() -> list[dict]:
    return load_json(Path(DATA_DIR / "resources.json"), [])


@app.get("/community/posts")
def community_posts() -> list[dict]:
    return load_json(Path(DATA_DIR / "community_posts.json"), [])


@app.post("/support/emergency")
def emergency_help() -> dict:
    return {"message": "Emergency escalation opened", "phone": "1-800-FIELD-US", "created_at": datetime.utcnow().isoformat()}


@app.post("/backup")
def create_backup() -> dict:
    path = backup_data()
    return {"message": "Backup created", "file": str(path)}
