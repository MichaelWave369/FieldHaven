from __future__ import annotations

from pathlib import Path

from core.storage import DATA_DIR, save_json


SAMPLE_JOBS = [
    {
        "id": "J-1001",
        "title": "POS Terminal Swap - Dallas, TX",
        "client": "Lone Star Retail Group",
        "payout": 265.00,
        "platform_fee": 0.0,
        "location": "Dallas, TX",
        "status": "Open",
        "description": "Swap 3 legacy POS terminals with new encrypted units. Includes test and photo proof.",
    },
    {
        "id": "J-1002",
        "title": "Fiber Troubleshooting - Tulsa, OK",
        "client": "Heartland Fiber",
        "payout": 420.00,
        "platform_fee": 5.0,
        "location": "Tulsa, OK",
        "status": "Open",
        "description": "Diagnose intermittent packet loss and replace damaged patch panel if required.",
    },
    {
        "id": "J-1003",
        "title": "Digital Signage Install - Phoenix, AZ",
        "client": "Southwest Hospitality",
        "payout": 510.00,
        "platform_fee": 0.0,
        "location": "Phoenix, AZ",
        "status": "Assigned",
        "description": "Mount and configure 4 lobby displays. Validate remote monitoring dashboard.",
    },
]

SAMPLE_CLIENT_RATINGS = [
    {
        "client": "Lone Star Retail Group",
        "rating": 4.7,
        "notes": "Pays on time and scope is clear.",
    },
    {
        "client": "Heartland Fiber",
        "rating": 3.2,
        "notes": "Supportive PM, but dispatch instructions can change last minute.",
    },
]

SAMPLE_COMMUNITY_POSTS = [
    {
        "author": "TechRangerTX",
        "topic": "Safety",
        "title": "Checklist before rooftop jobs",
        "body": "Always confirm ladder anchor points and weather before dispatch confirmation.",
    },
    {
        "author": "FiberMomUSA",
        "topic": "Client Alerts",
        "title": "Watch out: missing access notes",
        "body": "A national chain in OKC has recurring lockout issues. Ask for local manager contact early.",
    },
]


def bootstrap_sample_data() -> None:
    defaults = {
        "jobs.json": SAMPLE_JOBS,
        "client_ratings.json": SAMPLE_CLIENT_RATINGS,
        "community_posts.json": SAMPLE_COMMUNITY_POSTS,
        "job_logs.json": [],
        "invoices.json": [],
        "tickets.json": [],
        "certifications.json": [],
        "disputes.json": [],
    }

    for filename, payload in defaults.items():
        target = Path(DATA_DIR / filename)
        if not target.exists():
            save_json(target, payload)
