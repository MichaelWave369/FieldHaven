from __future__ import annotations

from pathlib import Path

from core.storage import DATA_DIR, save_json


def bootstrap_sample_data() -> None:
    defaults = {
        "jobs.json": [
            {"id": "J-1001", "title": "POS Refresh - Dallas", "payout": 265, "platform_fee": 0, "location": "Dallas, TX", "skills": ["POS", "Networking"], "status": "Open", "distance_miles": 18},
            {"id": "J-1002", "title": "Fiber Repair - Tulsa", "payout": 420, "platform_fee": 3, "location": "Tulsa, OK", "skills": ["Fiber", "Troubleshooting"], "status": "Open", "distance_miles": 32},
            {"id": "J-1003", "title": "Retail Cabling - Miami", "payout": 510, "platform_fee": 2, "location": "Miami, FL", "skills": ["Cabling", "Networking"], "status": "Open", "distance_miles": 14},
        ],
        "job_history.json": [{"id": "H-001", "completed": True, "margin": 220}],
        "market_rates.json": [{"service_type": "Fiber", "hourly": 115.0}, {"service_type": "POS", "hourly": 95.0}],
        "tech_directory.json": [{"id": "TD-0001", "technician": "TechA", "state": "TX", "skills": ["POS"], "verified": True, "reputation_score": 88}],
        "client_reviews.json": [],
        "contracts.json": [],
        "subscriptions.json": [],
        "revenue_share.json": [],
        "company_accounts.json": [],
        "partnerships.json": [],
        "marketing_visibility.json": [],
        "lead_gen.json": [],
        "triad_sync.json": [],
        "governance_votes.json": [],
        "feedback.json": [],
        "bug_bounty.json": [],
        "events.json": [{"id": "EV-001", "title": "Dallas Field Tech Meetup", "date": "2026-05-14", "location": "Dallas, TX"}],
        "certification_programs.json": [{"id": "CP-001", "name": "Fiber Basics", "provider": "FieldHaven Academy"}],
        "help_center.json": [{"topic": "Getting Started", "answer": "Complete onboarding wizard then publish profile."}],
        "notifications.json": [],
        "sync_queue.json": [],
        "audit_logs.json": [],
        "vault_exports.json": [],
        "exports.json": [],
        "memoria.json": [],
        "invoices.json": [],
    }

    for filename, payload in defaults.items():
        path = Path(DATA_DIR / filename)
        if not path.exists():
            save_json(path, payload)
