from __future__ import annotations

from pathlib import Path

from core.storage import DATA_DIR, save_json

SAMPLE_JOBS = [
    {"id": "J-1001", "title": "POS Refresh - Dallas", "client": "Lone Star Retail", "payout": 265, "platform_fee": 0.0, "location": "Dallas, TX", "skills": ["POS", "Networking"], "status": "Open", "distance_miles": 18},
    {"id": "J-1002", "title": "Fiber Repair - Tulsa", "client": "Heartland Fiber", "payout": 420, "platform_fee": 3.0, "location": "Tulsa, OK", "skills": ["Fiber", "Troubleshooting"], "status": "Open", "distance_miles": 32},
    {"id": "J-1003", "title": "Signage Install - Phoenix", "client": "SW Hospitality", "payout": 510, "platform_fee": 0.0, "location": "Phoenix, AZ", "skills": ["Install", "AV"], "status": "Assigned", "distance_miles": 8},
]


def bootstrap_sample_data() -> None:
    defaults = {
        "jobs.json": SAMPLE_JOBS,
        "client_ratings.json": [{"client": "Lone Star Retail", "rating": 4.7}],
        "community_posts.json": [{"author": "TechRangerTX", "title": "Weekly Crew Tips", "body": "Stay safe and document scope."}],
        "resources.json": [{"type": "Tax", "name": "1099 Checklist"}],
        "invoices.json": [],
        "bids.json": [],
        "quotes.json": [],
        "escrow.json": [],
        "schedule.json": [],
        "sync_queue.json": [],
        "sync_conflicts.json": [],
        "notifications.json": [],
        "team_assignments.json": [],
        "crew_chat.json": [],
        "vendor_marketplace.json": [],
        "financing_requests.json": [],
        "vault_exports.json": [],
        "privacy_settings.json": {"share_analytics": False, "allow_leaderboard": False},
        "audit_logs.json": [],
        "feature_votes.json": [],
        "memoria.json": [],
    }
    for filename, payload in defaults.items():
        path = Path(DATA_DIR / filename)
        if not path.exists():
            save_json(path, payload)
