from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from core.offline_sync import process_sync_queue
from core.storage import DATA_DIR, backup_data, load_json, save_json
from services.ai_assistant import ask_local_ollama

app = FastAPI(title="FieldHaven API", version="0.5.0")


class JobMatchRequest(BaseModel):
    technician: str
    skills: list[str]
    fuel_cost_per_mile: float = 0.67


class PricingRequest(BaseModel):
    service_type: str
    labor_hours: float
    parts_cost: float = 0.0
    urgency: str = "standard"


class MarketplacePost(BaseModel):
    seller: str
    category: str
    item: str
    price: float
    condition: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fieldhaven-api", "version": "0.5.0"}


@app.post("/ai/predictive-match")
def predictive_match(req: JobMatchRequest) -> list[dict]:
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    history = load_json(Path(DATA_DIR / "job_history.json"), [])
    completion_bonus = 15 if history else 5
    result = []
    for job in jobs:
        if job.get("status") != "Open":
            continue
        overlap = len(set(req.skills) & set(job.get("skills", [])))
        travel = float(job.get("distance_miles", 20)) * req.fuel_cost_per_mile
        risk = round(max(1.0, 5.0 - overlap - (job.get("platform_fee", 0) / 2)), 2)
        expected_margin = round(float(job.get("payout", 0)) - travel, 2)
        score = round(expected_margin + overlap * 90 + completion_bonus - risk * 8, 2)
        result.append({
            **job,
            "risk_score": risk,
            "expected_margin": expected_margin,
            "predictive_score": score,
            "ai_note": ask_local_ollama(f"Why is {job['title']} a strong or weak fit?"),
        })
    return sorted(result, key=lambda r: r["predictive_score"], reverse=True)


@app.post("/ai/smart-pricing")
def smart_pricing(req: PricingRequest) -> dict:
    market = load_json(Path(DATA_DIR / "market_rates.json"), [{"service_type": req.service_type, "hourly": 95.0}])
    hourly = next((r["hourly"] for r in market if r["service_type"] == req.service_type), 95.0)
    urgency_mult = 1.25 if req.urgency == "urgent" else 1.0
    subtotal = (hourly * req.labor_hours + req.parts_cost) * urgency_mult
    return {
        "service_type": req.service_type,
        "recommended_rate": round(hourly * urgency_mult, 2),
        "recommended_total": round(subtotal, 2),
        "strategy": ask_local_ollama(f"Give a concise pricing strategy for {req.service_type} with urgency {req.urgency}"),
    }


@app.get("/marketplace/tech")
def tech_marketplace() -> list[dict]:
    return load_json(Path(DATA_DIR / "tech_marketplace.json"), [])


@app.post("/marketplace/tech")
def create_marketplace_post(post: MarketplacePost) -> dict:
    items = load_json(Path(DATA_DIR / "tech_marketplace.json"), [])
    rec = {"id": f"MP-{len(items)+1:04}", **post.model_dump(), "created_at": datetime.utcnow().isoformat()}
    items.append(rec)
    save_json(Path(DATA_DIR / "tech_marketplace.json"), items)
    return rec


@app.get("/marketplace/vendor-deals")
def vendor_deals() -> list[dict]:
    deals = load_json(Path(DATA_DIR / "vendor_deals.json"), [])
    if not deals:
        deals = [
            {"vendor": "USA Tool Direct", "deal": "15% off meters", "members_only": True},
            {"vendor": "Patriot Fleet Vans", "deal": "$199/mo starter lease credit", "members_only": True},
        ]
        save_json(Path(DATA_DIR / "vendor_deals.json"), deals)
    return deals


@app.get("/reports/tax")
def tax_report() -> dict:
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    gross = round(sum(float(i.get("amount", 0)) for i in invoices), 2)
    estimated_tax = round(gross * 0.24, 2)
    return {"gross_income": gross, "estimated_tax": estimated_tax, "recommended_quarterly": round(estimated_tax / 4, 2)}


@app.post("/exports/quickbooks")
def quickbooks_export() -> dict:
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    csv_rows = ["InvoiceID,Client,Amount,Status"] + [f"{i.get('id','')},{i.get('client','')},{i.get('amount',0)},{i.get('status','')}" for i in invoices]
    rec = {"id": f"QB-{datetime.utcnow().strftime('%H%M%S')}", "content": "\n".join(csv_rows)}
    exports = load_json(Path(DATA_DIR / "exports.json"), [])
    exports.append(rec)
    save_json(Path(DATA_DIR / "exports.json"), exports)
    return rec


@app.get("/reports/forecast")
def earnings_forecast() -> dict:
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    monthly = sum(float(i.get("amount", 0)) for i in invoices[-6:]) / max(1, min(6, len(invoices)))
    projected = round(monthly * 12, 2)
    health = "Strong" if projected >= 60000 else "Growing"
    return {"projected_annual_earnings": projected, "business_health": health}


@app.get("/governance/features")
def feature_votes() -> list[dict]:
    return load_json(Path(DATA_DIR / "feature_votes.json"), [])


@app.post("/governance/features")
def add_feature_vote(payload: dict) -> dict:
    votes = load_json(Path(DATA_DIR / "feature_votes.json"), [])
    rec = {"id": f"GV-{len(votes)+1:04}", **payload, "created_at": datetime.utcnow().isoformat()}
    votes.append(rec)
    save_json(Path(DATA_DIR / "feature_votes.json"), votes)
    return rec


@app.get("/governance/moderators")
def moderators() -> list[dict]:
    return load_json(Path(DATA_DIR / "moderators.json"), [])


@app.post("/governance/moderators")
def elect_moderator(payload: dict) -> dict:
    mods = load_json(Path(DATA_DIR / "moderators.json"), [])
    rec = {"id": f"MOD-{len(mods)+1:03}", **payload, "elected_at": datetime.utcnow().isoformat()}
    mods.append(rec)
    save_json(Path(DATA_DIR / "moderators.json"), mods)
    return rec


@app.get("/public/openapi-links")
def public_api_links() -> dict:
    return {"openapi": "/openapi.json", "docs": "/docs", "description": "Public API for accounting, GPS, scheduling integrations"}


@app.get("/triad/sso")
def triad_sso() -> dict:
    return {"agentora": "connected", "memoria": "connected", "littup": "connected", "mode": "sso-ready"}


@app.post("/integrations/agentora/quote")
def agentora_quote(payload: dict) -> dict:
    return {"provider": "Agentora", "response": ask_local_ollama(payload.get("prompt", ""))}


@app.post("/integrations/memoria/save")
def memoria_save(payload: dict) -> dict:
    mem = load_json(Path(DATA_DIR / "memoria.json"), [])
    rec = {"id": f"M-{len(mem)+1:04}", "payload": payload, "saved_at": datetime.utcnow().isoformat()}
    mem.append(rec)
    save_json(Path(DATA_DIR / "memoria.json"), mem)
    return rec


@app.post("/integrations/littup/code-job")
def littup_job(payload: dict) -> dict:
    return {"provider": "LittUp", "status": "queued", "payload": payload}


@app.post("/notifications/push")
def create_notification(payload: dict) -> dict:
    notes = load_json(Path(DATA_DIR / "notifications.json"), [])
    rec = {"id": f"N-{len(notes)+1:04}", **payload, "created_at": datetime.utcnow().isoformat()}
    notes.append(rec)
    save_json(Path(DATA_DIR / "notifications.json"), notes)
    return rec


@app.get("/notifications/push")
def list_notifications() -> list[dict]:
    return load_json(Path(DATA_DIR / "notifications.json"), [])


@app.post("/offline/sync")
def offline_sync() -> dict:
    return process_sync_queue()


@app.post("/backup")
def backup() -> dict:
    path = backup_data()
    return {"message": "Backup created", "file": str(path)}
