from __future__ import annotations

import requests
import streamlit as st

from backend.server import start_embedded_api
from core.offline_sync import queue_offline_action
from core.sample_data import bootstrap_sample_data

API_BASE = "http://127.0.0.1:8008"
st.set_page_config(page_title="FieldHaven v0.7", page_icon="🛠️", layout="wide")


def apply_theme(mode: str) -> None:
    if mode == "light":
        bg, fg, card = "#f7f8fc", "#111827", "rgba(0,0,0,.04)"
    else:
        bg, fg, card = "radial-gradient(circle at 10% 20%, #1f2430 0%, #10131c 45%, #080a11 100%)", "#f5f7fa", "rgba(255,255,255,.03)"
    st.markdown(
        f"""
        <style>
        .stApp {{ background: {bg}; color: {fg}; }}
        .fh-card {{ border:1px solid rgba(255,255,255,.12); border-left:4px solid #e63946; background:{card}; padding:1rem; border-radius:14px; margin-bottom:.7rem; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_get(endpoint: str, fallback=None):
    try:
        return requests.get(f"{API_BASE}{endpoint}", timeout=6).json()
    except Exception:
        return fallback if fallback is not None else []


def api_post(endpoint: str, payload=None, fallback=None):
    try:
        return requests.post(f"{API_BASE}{endpoint}", json=payload or {}, timeout=8).json()
    except Exception:
        return fallback if fallback is not None else {"message": "offline"}


def national_scale_page() -> None:
    st.subheader("National Scale & Marketing")
    st.dataframe(api_get("/jobs/national", []), use_container_width=True)
    if st.button("Generate Leads"):
        st.json(api_post("/marketing/leads", {"vertical": "retail", "region": "texas", "keywords": ["pos", "network"]}))
    tech = st.text_input("Technician", "Tech-USA")
    if st.button("Save Visibility Controls"):
        st.json(api_post("/marketing/visibility", {"technician": tech, "regions": ["TX", "OK"], "budget": 50}))


def ai_suite_page() -> None:
    st.subheader("Advanced AI Suite")
    transcript = st.text_area("Voice Transcript (local STT output)", "Need help pricing a same-day fiber repair.")
    if st.button("Run Voice AI Assistant"):
        st.json(api_post("/ai/voice-assistant", {"transcript": transcript}))
    if st.button("Predict Job Risk"):
        st.json(api_post("/ai/predictive-risk", {"job_id": "J-1002", "environment": "standard"}))
    if st.button("Generate Contract + Compliance"):
        st.json(api_post("/ai/contracts/generate", {"client": "Acme Retail", "scope": "POS refresh", "state": "TX"}))
    st.markdown("### AI Business Coach")
    st.write(api_post("/ai/business-coach", {"context": "pricing, marketing, tax optimization"}).get("advice", ""))


def ecosystem_page() -> None:
    st.subheader("Ecosystem Leadership")
    st.json(api_get("/integrations/public", {}))
    st.json(api_get("/triad/sso", {}))
    if st.button("Run Triad Data Sync"):
        st.json(api_post("/triad/sync", {"source": "fieldhaven", "targets": ["agentora", "memoria", "littup"]}))
    st.markdown("### Exportable Professional Data Pack")
    st.json(api_get("/exports/professional-pack", {}))


def governance_page() -> None:
    st.subheader("User Governance & Feedback")
    if st.button("Submit Governance Vote"):
        st.json(api_post("/governance/vote", {"topic": "routing enhancements", "vote": "yes", "voter": "TechA"}))
    if st.button("Submit Feedback"):
        st.json(api_post("/feedback/submit", {"category": "ux", "message": "Add map clustering on national board."}))
    if st.button("Submit Bug Bounty Report"):
        st.json(api_post("/bounty/report", {"severity": "medium", "description": "edge-case validation issue"}))


def reliability_page() -> None:
    st.subheader("Performance & Reliability")
    st.json(api_get("/reliability/status", {}))
    if st.button("Queue Offline Event"):
        st.json(queue_offline_action("sync_event", {"source": "mobile"}))
    if st.button("Run Offline Sync"):
        st.json(api_post("/offline/sync"))
    if st.button("Create Backup"):
        st.json(api_post("/backup"))
    if st.button("Push Notification Test"):
        st.json(api_post("/notifications/push", {"type": "job_alert", "message": "New national lead available"}))
    st.dataframe(api_get("/notifications/push", []), use_container_width=True)


def launch_readiness_page() -> None:
    st.subheader("Final Polish & Launch Readiness")
    st.json(api_get("/onboarding/wizard", {}))
    st.dataframe(api_get("/help/center", []), use_container_width=True)
    st.json(api_get("/checklist/production-ready", {}))
    if st.button("Write Audit Log"):
        st.json(api_post("/security/audit/log", {"actor": "admin", "event": "launch_check"}))
    st.json(api_get("/security/audit", {}))
    if st.button("Export Full Vault"):
        st.json(api_post("/vault/export"))
    st.markdown("### Events + Certifications")
    st.dataframe(api_get("/events/community", []), use_container_width=True)
    st.dataframe(api_get("/programs/certifications", []), use_container_width=True)


def main() -> None:
    bootstrap_sample_data()
    start_embedded_api()

    st.title("🛠️ FieldHaven v0.7")
    st.caption("National-scale, premium, local-first American platform for field tech ownership.")

    mode = st.sidebar.selectbox("Theme", ["dark", "light"])
    apply_theme(mode)

    page = st.sidebar.radio(
        "Navigate",
        ["National Scale", "AI Suite", "Ecosystem", "Governance", "Reliability", "Launch Readiness"],
    )

    if page == "National Scale":
        national_scale_page()
    elif page == "AI Suite":
        ai_suite_page()
    elif page == "Ecosystem":
        ecosystem_page()
    elif page == "Governance":
        governance_page()
    elif page == "Reliability":
        reliability_page()
    else:
        launch_readiness_page()


if __name__ == "__main__":
    main()
