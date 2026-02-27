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
        "distance_miles": 18,
        "description": "Swap 3 legacy POS terminals with new encrypted units.",
    },
    {
        "id": "J-1002",
        "title": "Fiber Troubleshooting - Tulsa, OK",
        "client": "Heartland Fiber",
        "payout": 420.00,
        "platform_fee": 5.0,
        "location": "Tulsa, OK",
        "status": "Open",
        "distance_miles": 32,
        "description": "Diagnose packet loss and replace damaged patch panel if required.",
    },
    {
        "id": "J-1003",
        "title": "Digital Signage Install - Phoenix, AZ",
        "client": "Southwest Hospitality",
        "payout": 510.00,
        "platform_fee": 0.0,
        "location": "Phoenix, AZ",
        "status": "Assigned",
        "distance_miles": 8,
        "description": "Mount and configure 4 lobby displays.",
    },
]

SAMPLE_CLIENT_RATINGS = [
    {"client": "Lone Star Retail Group", "rating": 4.7, "notes": "Pays on time and scope is clear."},
    {"client": "Heartland Fiber", "rating": 3.2, "notes": "PMs helpful; dispatch notes can drift."},
]

SAMPLE_COMMUNITY_POSTS = [
    {
        "author": "TechRangerTX",
        "topic": "Safety",
        "title": "Checklist before rooftop jobs",
        "body": "Confirm anchors, weather, and local contacts before dispatch acceptance.",
    },
    {
        "author": "FiberMomUSA",
        "topic": "Mentoring",
        "title": "New tech mentoring thread",
        "body": "Weekly live mentoring for new 1099 techs covering scope, invoicing, and safety.",
    },
]

SAMPLE_KB = [
    {"title": "How escrow works", "category": "Payments", "content": "Funds are reserved before dispatch."},
    {"title": "Emergency protocol", "category": "Safety", "content": "Use emergency button then call US support."},
]

SAMPLE_SUCCESS_STORIES = [
    {"tech": "Alex-Reno", "story": "Raised monthly income 31% using smart scheduling + transparent jobs."}
]

SAMPLE_RESOURCES = [
    {"type": "Tax Tips", "name": "Quarterly 1099 Tax Checklist"},
    {"type": "Insurance", "name": "General Liability Starter Guide"},
    {"type": "Training", "name": "Fiber Certification Path"},
    {"type": "Legal", "name": "Independent Contractor Rights (US)"},
]


def bootstrap_sample_data() -> None:
    defaults = {
        "jobs.json": SAMPLE_JOBS,
        "client_ratings.json": SAMPLE_CLIENT_RATINGS,
        "community_posts.json": SAMPLE_COMMUNITY_POSTS,
        "knowledge_base.json": SAMPLE_KB,
        "success_stories.json": SAMPLE_SUCCESS_STORIES,
        "resources.json": SAMPLE_RESOURCES,
        "job_logs.json": [],
        "invoices.json": [],
        "tickets.json": [],
        "certifications.json": [],
        "disputes.json": [],
        "chat_messages.json": [],
        "quotes.json": [],
        "schedule.json": [],
        "escrow.json": [],
        "sync_queue.json": [],
        "memoria.json": [],
    }
    for filename, payload in defaults.items():
        target = Path(DATA_DIR / filename)
        if not target.exists():
            save_json(target, payload)
