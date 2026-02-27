# FieldHaven v0.1

**The American Field Tech Haven** — an open-source, self-hostable platform built to support independent field technicians with fair pay, transparent job terms, real US support, and local-first privacy.

---

## Hero

FieldHaven is designed as an all-in-one alternative to extractive field service marketplaces. Instead of punishing techs with hidden terms and opaque fees, FieldHaven provides:

- Transparent pay and visible platform fees
- Low/zero technician fees
- Real US-based human support (chat/phone/ticket)
- Powerful technician tools (offline logs, invoicing, tax estimator, dispute workflows)
- Private community protections and client ratings
- Fully open-source + self-hostable architecture

---

## Stack

- **Frontend:** Streamlit (dark/noir with warm accents)
- **Backend:** FastAPI (embedded in Streamlit runtime)
- **Data:** Local JSON storage (local-first + self-hostable)
- **AI Assistant:** Local Ollama hook for private quote/troubleshooting/invoice help
- **License:** MIT

---

## Quick Start

```bash
git clone https://github.com/MichaelWave369/FieldHaven.git
cd FieldHaven
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

API runs embedded at `http://127.0.0.1:8008`.

---

## Feature Map

### 1) Fair Job Marketplace
- Transparent payout + visible platform fee per job
- Bid workflow and direct accept
- Fair assignment state updates

### 2) American Support Center
- Real US-human support ticket workflow
- Chat/phone/ticket options
- Local Ollama assistant for fast guidance

### 3) Tech Tools Suite
- Offline job logging + time tracking
- Invoice generation + escrow status
- Tax reserve estimator
- Insurance/safety/training placeholders + certification tracker
- Dispute flow templates

### 4) Community & Protection
- Private community feed examples
- Rate-the-client dataset
- Local-first storage (self-hosted or on-device)

### 5) Triad369 Integration Hooks
- Agentora/Memoria SSO callback placeholders
- Agentora quote/troubleshooting hook endpoints documented
- Backup/export tooling

---

## Screenshots

> Add screenshots here after first run.

- `docs/screenshots/dashboard.png`
- `docs/screenshots/marketplace.png`
- `docs/screenshots/tools_suite.png`

---

## Why FieldHaven is Better than Field Nation

- **Tech-first economics:** low/zero fees for technicians
- **Transparent terms:** no hidden payout games
- **US support, real humans:** escalation and accountability
- **Local-first data:** privacy and operational resilience
- **Open-source governance:** no black-box lock-in
- **Self-hostability:** regional co-ops and tech groups can run their own stack

---

## Project Structure

```text
FieldHaven/
├── app.py
├── backend/
│   ├── api.py
│   └── server.py
├── core/
│   ├── sample_data.py
│   └── storage.py
├── services/
│   └── ai_assistant.py
├── templates/
│   ├── dispute_template.md
│   ├── invoice_template.md
│   └── safety_checklist_template.md
├── data/
├── tests/
├── LICENSE
└── requirements.txt
```

---

## Triad369-Launchpad Readiness

FieldHaven includes:
- clear MIT licensing,
- modular app/service boundaries,
- local-first defaults,
- integration hook stubs for Agentora/Memoria,
- production-oriented API patterns ready for extension.
