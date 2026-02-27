# FieldHaven v0.3

FieldHaven is an American-first, open-source, local-first platform built to help independent field technicians thrive.

## v0.3 Upgrades

### 1) Smart Job Matching & AI Assistant
- AI-powered job recommendations based on skills, pay, distance, and travel cost.
- AI auto-bidding for top matched jobs.
- Earnings optimizer suggestions in the dashboard.

### 2) Advanced Tech Tools
- Mobile-first PWA readiness with install manifest template.
- QuickBooks export endpoint.
- Community equipment marketplace for buying/selling tools.
- Compliance and certification tracker with reminder records.

### 3) Earnings & Protection
- Escrow payment guarantee with optional instant payout.
- Transparent fee breakdown on escrow records.
- Dispute workflow with neutral American mediator attribution.
- Insurance and bonding marketplace feed.

### 4) Community Growth
- Tech-only private forum feed and mentorship matching.
- Success stories and opt-in leaderboard.
- Local meetup and training event calendar.

### 5) Triad369 + Analytics
- Deeper Agentora / Memoria / LittUp integration endpoints.
- Analytics endpoint for earnings-over-time and job heat map data.
- Performance-oriented local JSON APIs and offline sync support.

## Quick Start
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Privacy + Local-first
FieldHaven stores operational data locally (`data/*.json`) and can be self-hosted by local tech communities.
