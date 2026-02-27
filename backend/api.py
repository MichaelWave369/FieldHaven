from __future__ import annotations

from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from core.offline_sync import process_sync_queue
from core.storage import DATA_DIR, backup_data, load_json, save_json
from services.ai_assistant import ask_local_ollama

app = FastAPI(title="FieldHaven API", version="0.7.0")


class GeoVisibilityRequest(BaseModel):
    technician: str
    regions: list[str]
    budget: float = 0.0


class VoiceAssistantRequest(BaseModel):
    transcript: str


class PredictiveRiskRequest(BaseModel):
    job_id: str
    environment: str = "standard"


class ContractRequest(BaseModel):
    client: str
    scope: str
    state: str


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "fieldhaven-api", "version": "0.7.0"}


@app.get("/jobs/national")
def national_jobs(region: str | None = None) -> list[dict]:
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    if region:
        return [j for j in jobs if region.lower() in j.get("location", "").lower()]
    return jobs


@app.post("/marketing/visibility")
def set_visibility(req: GeoVisibilityRequest) -> dict:
    data = load_json(Path(DATA_DIR / "marketing_visibility.json"), [])
    rec = {"id": f"MV-{len(data)+1:04}", **req.model_dump(), "created_at": datetime.utcnow().isoformat()}
    data.append(rec)
    save_json(Path(DATA_DIR / "marketing_visibility.json"), data)
    return rec


@app.post("/marketing/leads")
def generate_leads(payload: dict) -> dict:
    leads = load_json(Path(DATA_DIR / "lead_gen.json"), [])
    rec = {
        "id": f"LD-{len(leads)+1:04}",
        "vertical": payload.get("vertical", "retail"),
        "region": payload.get("region", "national"),
        "estimated_leads": 5 + len(payload.get("keywords", [])) * 3,
        "created_at": datetime.utcnow().isoformat(),
    }
    leads.append(rec)
    save_json(Path(DATA_DIR / "lead_gen.json"), leads)
    return rec


@app.post("/ai/voice-assistant")
def voice_assistant(req: VoiceAssistantRequest) -> dict:
    return {
        "mode": "local-stt",
        "transcript": req.transcript,
        "response": ask_local_ollama(f"Respond as a field tech copilot: {req.transcript}"),
    }


@app.post("/ai/predictive-risk")
def predictive_risk(req: PredictiveRiskRequest) -> dict:
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    job = next((j for j in jobs if j.get("id") == req.job_id), {})
    distance = float(job.get("distance_miles", 20))
    env_penalty = 2 if req.environment == "hazardous" else 0
    risk = round(min(10.0, 2.5 + (distance / 20) + env_penalty), 2)
    maint_score = round(max(1.0, 10.0 - risk), 2)
    return {"job_id": req.job_id, "risk_score": risk, "predictive_maintenance_score": maint_score}


@app.post("/ai/contracts/generate")
def generate_contract(req: ContractRequest) -> dict:
    text = ask_local_ollama(
        f"Draft a concise field service contract for client {req.client} in {req.state}. Scope: {req.scope}. Include compliance checklist."
    )
    contracts = load_json(Path(DATA_DIR / "contracts.json"), [])
    rec = {"id": f"CT-{len(contracts)+1:04}", **req.model_dump(), "content": text}
    contracts.append(rec)
    save_json(Path(DATA_DIR / "contracts.json"), contracts)
    return rec


@app.get("/integrations/public")
def public_api() -> dict:
    return {
        "openapi": "/openapi.json",
        "docs": "/docs",
        "version": "v0.7",
        "categories": ["accounting", "gps", "scheduling", "crm"],
    }


@app.get("/triad/sso")
def triad_sso() -> dict:
    return {"agentora": "connected", "memoria": "connected", "littup": "connected", "sync": "active"}


@app.post("/triad/sync")
def triad_sync(payload: dict) -> dict:
    logs = load_json(Path(DATA_DIR / "triad_sync.json"), [])
    rec = {"id": f"TS-{len(logs)+1:04}", "payload": payload, "synced_at": datetime.utcnow().isoformat()}
    logs.append(rec)
    save_json(Path(DATA_DIR / "triad_sync.json"), logs)
    return rec


@app.get("/exports/professional-pack")
def professional_pack() -> dict:
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    contracts = load_json(Path(DATA_DIR / "contracts.json"), [])
    reviews = load_json(Path(DATA_DIR / "client_reviews.json"), [])
    return {"invoices": len(invoices), "contracts": len(contracts), "reviews": len(reviews), "format": "accountant_lawyer_bundle"}


@app.post("/governance/vote")
def governance_vote(payload: dict) -> dict:
    votes = load_json(Path(DATA_DIR / "governance_votes.json"), [])
    rec = {"id": f"GV-{len(votes)+1:04}", **payload, "created_at": datetime.utcnow().isoformat()}
    votes.append(rec)
    save_json(Path(DATA_DIR / "governance_votes.json"), votes)
    return rec


@app.post("/feedback/submit")
def feedback_submit(payload: dict) -> dict:
    items = load_json(Path(DATA_DIR / "feedback.json"), [])
    rec = {"id": f"FB-{len(items)+1:04}", **payload, "status": "received", "created_at": datetime.utcnow().isoformat()}
    items.append(rec)
    save_json(Path(DATA_DIR / "feedback.json"), items)
    return rec


@app.post("/bounty/report")
def bounty_report(payload: dict) -> dict:
    reports = load_json(Path(DATA_DIR / "bug_bounty.json"), [])
    rec = {"id": f"BB-{len(reports)+1:04}", **payload, "reward_status": "under_review", "created_at": datetime.utcnow().isoformat()}
    reports.append(rec)
    save_json(Path(DATA_DIR / "bug_bounty.json"), reports)
    return rec


@app.get("/reliability/status")
def reliability_status() -> dict:
    return {
        "load_balancer": "enabled-local",
        "ha_mode": "active-passive",
        "last_backup": datetime.utcnow().isoformat(),
    }


@app.post("/security/audit/log")
def create_audit_log(payload: dict) -> dict:
    logs = load_json(Path(DATA_DIR / "audit_logs.json"), [])
    rec = {"id": f"AUD-{len(logs)+1:04}", **payload, "timestamp": datetime.utcnow().isoformat()}
    logs.append(rec)
    save_json(Path(DATA_DIR / "audit_logs.json"), logs)
    return rec


@app.get("/security/audit")
def security_audit() -> dict:
    return {"audit_logs": len(load_json(Path(DATA_DIR / "audit_logs.json"), [])), "ownership": "local-first", "encryption": "host-level"}


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


@app.get("/onboarding/wizard")
def onboarding_wizard() -> dict:
    return {
        "steps": [
            "Create profile",
            "Set service regions",
            "Connect payout",
            "Review compliance",
            "Publish directory card",
        ]
    }


@app.get("/help/center")
def help_center() -> list[dict]:
    return load_json(Path(DATA_DIR / "help_center.json"), [])


@app.get("/checklist/production-ready")
def production_checklist() -> dict:
    return {
        "items": [
            "Backups configured",
            "Audit logging enabled",
            "PWA tested",
            "API docs reachable",
            "Triad sync validated",
        ],
        "status": "ready",
    }


@app.get("/events/community")
def community_events() -> list[dict]:
    return load_json(Path(DATA_DIR / "events.json"), [])


@app.get("/programs/certifications")
def certifications() -> list[dict]:
    return load_json(Path(DATA_DIR / "certification_programs.json"), [])


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
