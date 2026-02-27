from __future__ import annotations

from pathlib import Path

from core.storage import DATA_DIR, save_json


def bootstrap_sample_data() -> None:
    defaults = {
        "jobs.json": [
            {"id": "J-1001", "title": "POS Refresh - Dallas", "payout": 265, "platform_fee": 0, "location": "Dallas, TX", "skills": ["POS", "Networking"], "status": "Open", "distance_miles": 18},
            {"id": "J-1002", "title": "Fiber Repair - Tulsa", "payout": 420, "platform_fee": 3, "location": "Tulsa, OK", "skills": ["Fiber", "Troubleshooting"], "status": "Open", "distance_miles": 32},
        ],
        "job_history.json": [{"id": "H-001", "completed": True, "margin": 220}],
        "market_rates.json": [{"service_type": "Fiber", "hourly": 115.0}, {"service_type": "POS", "hourly": 95.0}],
        "tech_marketplace.json": [{"id": "MP-0001", "seller": "TechA", "category": "Tools", "item": "Cable Tester", "price": 180, "condition": "Used-Good"}],
        "vendor_deals.json": [],
        "invoices.json": [],
        "exports.json": [],
        "feature_votes.json": [],
        "moderators.json": [],
        "memoria.json": [],
        "notifications.json": [],
        "sync_queue.json": [],
    }

    for filename, payload in defaults.items():
        path = Path(DATA_DIR / filename)
        if not path.exists():
            save_json(path, payload)
