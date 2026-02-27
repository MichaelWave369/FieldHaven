from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from core.offline_sync import process_sync_queue
from core.storage import DATA_DIR, backup_data, load_json, save_json
from services.ai_assistant import ask_local_ollama

app = FastAPI(title="FieldHaven API", version="0.6.0")


class PredictiveMatchRequest(BaseModel):
    technician: str
    skills: list[str]
    fuel_cost_per_mile: float = 0.67


class SmartPricingRequest(BaseModel):
    service_type: str
    labor_hours: float
    parts_cost: float = 0.0
    urgency: str = "standard"


class PremiumSubscriptionRequest(BaseModel):
    technician: str
    tier: str = "premium_plus"


class RevenueShareRequest(BaseModel):
    technician: str
    community_actions: int


class DirectoryProfileRequest(BaseModel):
    technician: str
    state: str
    skills: list[str]
    verified: bool = True


class ClientReviewRequest(BaseModel):
    client: str
    technician: str
    rating: float
    review: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fieldhaven-api", "version": "0.6.0"}


@app.get("/pwa/manifest")
def pwa_manifest() -> dict:
    return load_json(Path("templates/pwa_manifest.json"), {})


@app.get("/pwa/config")
def pwa_config() -> dict:
    return {
        "installable": True,
        "desktop": True,
        "mobile": True,
        "offline_mode": True,
        "background_sync": True,
    }


@app.post("/offline/sync")
def offline_sync() -> dict:
    return process_sync_queue()


@app.post("/offline/background-sync")
def background_sync() -> dict:
    result = process_sync_queue()
    result["mode"] = "background"
    return result


@app.post("/ai/predictive-match")
def predictive_match(req: PredictiveMatchRequest) -> list[dict]:
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    history = load_json(Path(DATA_DIR / "job_history.json"), [])
    completion_bonus = 20 if history else 5
    ranked = []
    for job in jobs:
        if job.get("status") != "Open":
            continue
        overlap = len(set(req.skills).intersection(set(job.get("skills", []))))
        travel_cost = float(job.get("distance_miles", 20)) * req.fuel_cost_per_mile
        risk = round(max(1.0, 5.0 - overlap - float(job.get("platform_fee", 0)) / 2), 2)
        expected_profit = round(float(job.get("payout", 0)) - travel_cost, 2)
        score = round(expected_profit + overlap * 85 + completion_bonus - risk * 7, 2)
        ranked.append(
            {
                **job,
                "risk_score": risk,
                "expected_profit": expected_profit,
                "predictive_score": score,
            }
        )
    return sorted(ranked, key=lambda x: x["predictive_score"], reverse=True)


@app.post("/ai/smart-pricing")
def smart_pricing(req: SmartPricingRequest) -> dict:
    rates = load_json(Path(DATA_DIR / "market_rates.json"), [{"service_type": req.service_type, "hourly": 95.0}])
    hourly = next((r["hourly"] for r in rates if r["service_type"] == req.service_type), 95.0)
    urgency_mult = 1.25 if req.urgency == "urgent" else 1.0
    subtotal = (hourly * req.labor_hours + req.parts_cost) * urgency_mult
    return {
        "service_type": req.service_type,
        "recommended_hourly": round(hourly * urgency_mult, 2),
        "recommended_total": round(subtotal, 2),
    }


@app.post("/ai/business-coach")
def ai_business_coach(payload: dict) -> dict:
    context = payload.get("context", "growth, marketing, pricing, taxes")
    return {
        "coach": "local-ollama",
        "advice": ask_local_ollama(f"Give concise field-tech business coaching for: {context}"),
    }


@app.get("/monetization/premium-tiers")
def premium_tiers() -> list[dict]:
    return [
        {"tier": "free", "fee": 0, "benefits": ["job board", "community"]},
        {"tier": "premium_plus", "fee": 19, "benefits": ["priority support", "higher profile visibility", "advanced AI tools"]},
    ]


@app.post("/monetization/subscribe")
def subscribe_premium(req: PremiumSubscriptionRequest) -> dict:
    subs = load_json(Path(DATA_DIR / "subscriptions.json"), [])
    rec = {"id": f"SUB-{len(subs)+1:04}", **req.model_dump(), "status": "active", "created_at": datetime.utcnow().isoformat()}
    subs.append(rec)
    save_json(Path(DATA_DIR / "subscriptions.json"), subs)
    return rec


@app.post("/monetization/revenue-share")
def revenue_share(req: RevenueShareRequest) -> dict:
    reward = round(req.community_actions * 2.5, 2)
    rec = {"technician": req.technician, "community_actions": req.community_actions, "reward_credit": reward}
    shares = load_json(Path(DATA_DIR / "revenue_share.json"), [])
    shares.append(rec)
    save_json(Path(DATA_DIR / "revenue_share.json"), shares)
    return rec


@app.get("/directory/techs")
def directory_techs() -> list[dict]:
    return load_json(Path(DATA_DIR / "tech_directory.json"), [])


@app.post("/directory/techs")
def add_directory_tech(profile: DirectoryProfileRequest) -> dict:
    items = load_json(Path(DATA_DIR / "tech_directory.json"), [])
    rep = 80 + len(profile.skills) * 2
    rec = {"id": f"TD-{len(items)+1:04}", **profile.model_dump(), "reputation_score": min(100, rep)}
    items.append(rec)
    save_json(Path(DATA_DIR / "tech_directory.json"), items)
    return rec


@app.get("/reviews/clients")
def client_reviews() -> list[dict]:
    return load_json(Path(DATA_DIR / "client_reviews.json"), [])


@app.post("/reviews/clients")
def add_client_review(review: ClientReviewRequest) -> dict:
    reviews = load_json(Path(DATA_DIR / "client_reviews.json"), [])
    rec = {"id": f"CR-{len(reviews)+1:04}", **review.model_dump(), "created_at": datetime.utcnow().isoformat()}
    reviews.append(rec)
    save_json(Path(DATA_DIR / "client_reviews.json"), reviews)
    return rec


@app.get("/enterprise/company-accounts")
def company_accounts() -> list[dict]:
    return load_json(Path(DATA_DIR / "company_accounts.json"), [])


@app.post("/enterprise/company-accounts")
def create_company_account(payload: dict) -> dict:
    companies = load_json(Path(DATA_DIR / "company_accounts.json"), [])
    rec = {"id": f"CO-{len(companies)+1:04}", **payload, "created_at": datetime.utcnow().isoformat()}
    companies.append(rec)
    save_json(Path(DATA_DIR / "company_accounts.json"), companies)
    return rec


@app.get("/enterprise/partnerships")
def enterprise_partnerships() -> list[dict]:
    data = load_json(Path(DATA_DIR / "partnerships.json"), [])
    if not data:
        data = [
            {"partner": "American Tool Supply", "type": "tools", "benefit": "member discounts"},
            {"partner": "United Contractor Insurance", "type": "insurance", "benefit": "preferred rates"},
            {"partner": "Freedom Equipment Finance", "type": "financing", "benefit": "fast approvals"},
        ]
        save_json(Path(DATA_DIR / "partnerships.json"), data)
    return data


@app.get("/reports/business-health")
def business_health() -> dict:
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    gross = sum(float(i.get("amount", 0)) for i in invoices)
    projected = round((gross / max(1, len(invoices))) * 12, 2) if invoices else 0.0
    return {
        "gross_income": round(gross, 2),
        "projected_annual": projected,
        "health": "Strong" if projected >= 60000 else "Growing",
    }


@app.post("/exports/quickbooks")
def quickbooks_export() -> dict:
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    rows = ["InvoiceID,Client,Amount,Status"]
    for inv in invoices:
        rows.append(f"{inv.get('id','')},{inv.get('client','')},{inv.get('amount',0)},{inv.get('status','')}")
    record = {"id": f"QB-{datetime.utcnow().strftime('%H%M%S')}", "csv": "\n".join(rows)}
    exports = load_json(Path(DATA_DIR / "exports.json"), [])
    exports.append(record)
    save_json(Path(DATA_DIR / "exports.json"), exports)
    return record


@app.get("/security/audit")
def security_audit() -> dict:
    return {
        "encryption_at_rest": "local disk controls",
        "audit_logs": len(load_json(Path(DATA_DIR / "audit_logs.json"), [])),
        "data_ownership": "full local export available",
    }


@app.post("/security/audit/log")
def create_audit_log(payload: dict) -> dict:
    logs = load_json(Path(DATA_DIR / "audit_logs.json"), [])
    rec = {"id": f"AUD-{len(logs)+1:04}", **payload, "timestamp": datetime.utcnow().isoformat()}
    logs.append(rec)
    save_json(Path(DATA_DIR / "audit_logs.json"), logs)
    return rec


@app.post("/vault/export")
def vault_export() -> dict:
    snapshot = {}
    for p in Path(DATA_DIR).glob("*.json"):
        snapshot[p.name] = load_json(p, [])
    rec = {"created_at": datetime.utcnow().isoformat(), "files": len(snapshot), "snapshot": snapshot}
    exports = load_json(Path(DATA_DIR / "vault_exports.json"), [])
    exports.append(rec)
    save_json(Path(DATA_DIR / "vault_exports.json"), exports)
    return {"files": rec["files"], "created_at": rec["created_at"]}


@app.get("/events/community")
def community_events() -> list[dict]:
    return load_json(Path(DATA_DIR / "events.json"), [])


@app.get("/programs/certifications")
def certifications() -> list[dict]:
    return load_json(Path(DATA_DIR / "certification_programs.json"), [])


@app.get("/integrations/public")
def public_api() -> dict:
    return {"openapi": "/openapi.json", "docs": "/docs", "version": "v0.6"}


@app.get("/triad/sso")
def triad_sso() -> dict:
    return {"agentora": "connected", "memoria": "connected", "littup": "connected"}


@app.post("/integrations/agentora/quote")
def agentora_quote(payload: dict) -> dict:
    return {"provider": "Agentora", "response": ask_local_ollama(payload.get("prompt", ""))}


@app.post("/integrations/memoria/save")
def memoria_save(payload: dict) -> dict:
    memories = load_json(Path(DATA_DIR / "memoria.json"), [])
    rec = {"id": f"M-{len(memories)+1:04}", "payload": payload, "saved_at": datetime.utcnow().isoformat()}
    memories.append(rec)
    save_json(Path(DATA_DIR / "memoria.json"), memories)
    return rec


@app.post("/integrations/littup/code-job")
def littup_code_job(payload: dict) -> dict:
    return {"provider": "LittUp", "status": "queued", "payload": payload}


@app.post("/notifications/push")
def push_notification(payload: dict) -> dict:
    notes = load_json(Path(DATA_DIR / "notifications.json"), [])
    rec = {"id": f"N-{len(notes)+1:04}", **payload, "created_at": datetime.utcnow().isoformat()}
    notes.append(rec)
    save_json(Path(DATA_DIR / "notifications.json"), notes)
    return rec


@app.get("/notifications/push")
def list_notifications() -> list[dict]:
    return load_json(Path(DATA_DIR / "notifications.json"), [])


@app.post("/backup")
def backup() -> dict:
    path = backup_data()
    return {"message": "Backup created", "file": str(path)}
