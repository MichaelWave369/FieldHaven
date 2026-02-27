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
        "skills": ["POS", "Networking"],
        "status": "Open",
        "distance_miles": 18,
        "description": "Swap 3 legacy POS terminals with encrypted units.",
    },
    {
        "id": "J-1002",
        "title": "Fiber Troubleshooting - Tulsa, OK",
        "client": "Heartland Fiber",
        "payout": 420.00,
        "platform_fee": 3.0,
        "location": "Tulsa, OK",
        "skills": ["Fiber", "Troubleshooting"],
        "status": "Open",
        "distance_miles": 32,
        "description": "Diagnose packet loss and replace damaged panel.",
    },
    {
        "id": "J-1003",
        "title": "Digital Signage Install - Phoenix, AZ",
        "client": "Southwest Hospitality",
        "payout": 510.00,
        "platform_fee": 0.0,
        "location": "Phoenix, AZ",
        "skills": ["Install", "AV"],
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
    {"author": "TechRangerTX", "topic": "Safety", "title": "Rooftop checklist", "body": "Confirm anchors and weather."},
    {"author": "FiberMomUSA", "topic": "Mentoring", "title": "Weekly mentoring", "body": "Scope, invoicing, safety."},
]

SAMPLE_KB = [
    {"title": "How escrow works", "category": "Payments", "content": "Funds reserved before dispatch."},
    {"title": "Emergency protocol", "category": "Safety", "content": "Use emergency button and call US support."},
]

SAMPLE_SUCCESS_STORIES = [
    {"tech": "Alex-Reno", "story": "Raised monthly income 31% via smart scheduling.", "opt_in": True}
]

SAMPLE_RESOURCES = [
    {"type": "Tax Tips", "name": "Quarterly 1099 Tax Checklist"},
    {"type": "Insurance", "name": "General Liability Starter Guide"},
    {"type": "Training", "name": "Fiber Certification Path"},
    {"type": "Legal", "name": "Independent Contractor Rights (US)"},
]

SAMPLE_EQUIPMENT = [
    {"id": "EQ-001", "seller": "CableVetCA", "item": "Fluke LinkRunner", "price": 450, "condition": "Used-Good"},
    {"id": "EQ-002", "seller": "NetTechOH", "item": "Fiber Cleaver Kit", "price": 190, "condition": "Used-Excellent"},
]

SAMPLE_MEETUPS = [
    {"id": "EV-001", "title": "Texas Tech Meetup", "location": "Dallas, TX", "date": "2026-04-18"},
    {"id": "EV-002", "title": "Fiber Training Night", "location": "Tulsa, OK", "date": "2026-05-02"},
]

SAMPLE_LEADERBOARD = [
    {"tech": "OptIn-TechA", "earnings": 8200, "jobs": 21},
    {"tech": "OptIn-TechB", "earnings": 7600, "jobs": 18},
]


def bootstrap_sample_data() -> None:
    defaults = {
        "jobs.json": SAMPLE_JOBS,
        "client_ratings.json": SAMPLE_CLIENT_RATINGS,
        "community_posts.json": SAMPLE_COMMUNITY_POSTS,
        "knowledge_base.json": SAMPLE_KB,
        "success_stories.json": SAMPLE_SUCCESS_STORIES,
        "resources.json": SAMPLE_RESOURCES,
        "equipment_marketplace.json": SAMPLE_EQUIPMENT,
        "events.json": SAMPLE_MEETUPS,
        "leaderboard.json": SAMPLE_LEADERBOARD,
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
        "insurance_marketplace.json": [],
        "mentor_matches.json": [],
        "exports.json": [],
    }
    for filename, payload in defaults.items():
        target = Path(DATA_DIR / filename)
        if not target.exists():
            save_json(target, payload)
