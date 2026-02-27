from __future__ import annotations

from datetime import date
from pathlib import Path

import requests
import streamlit as st

from backend.server import start_embedded_api
from core.offline_sync import queue_offline_action
from core.sample_data import bootstrap_sample_data
from core.storage import DATA_DIR, load_json, save_json

API_BASE = "http://127.0.0.1:8008"
st.set_page_config(page_title="FieldHaven v0.3", page_icon="🛠️", layout="wide")


def load_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {background: radial-gradient(circle at 10% 20%, #1f2430 0%, #10131c 45%, #080a11 100%); color: #f5f5f5;}
        .fh-card {border: 1px solid rgba(255,255,255,0.09); border-left: 4px solid #e63946; background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 14px; margin-bottom: 0.8rem;}
        .fh-accent { color: #ffd166; font-weight: 700; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_get(endpoint: str, fallback=None):
    try:
        return requests.get(f"{API_BASE}{endpoint}", timeout=4).json()
    except Exception:
        return fallback if fallback is not None else []


def api_post(endpoint: str, payload=None, fallback=None):
    try:
        return requests.post(f"{API_BASE}{endpoint}", json=payload or {}, timeout=6).json()
    except Exception:
        return fallback if fallback is not None else {"message": "offline"}


def header() -> None:
    st.title("🛠️ FieldHaven v0.3")
    st.caption("American-first, local-first platform helping field techs earn more and stay protected.")
    a, b, c, d = st.columns(4)
    if a.button("🚨 Emergency", use_container_width=True):
        st.error(api_post("/support/emergency")["message"])
    if b.button("🔄 Offline Sync", use_container_width=True):
        st.success(str(api_post("/offline/sync")))
    if c.button("📅 Smart Schedule", use_container_width=True):
        st.success(api_post("/schedule/auto")["message"])
    if d.button("📤 QuickBooks Export", use_container_width=True):
        st.json(api_post("/exports/quickbooks"))


def smart_matching_page() -> None:
    st.subheader("Smart Job Matching + AI Auto-Bid")
    skills = st.multiselect("Skills", ["POS", "Networking", "Fiber", "Troubleshooting", "Install", "AV"])
    tech = st.text_input("Technician", value="Tech-USA")
    recs = api_post("/jobs/match", {"technician": tech, "skills": skills or ["Networking"], "fuel_cost_per_mile": 0.67}, [])
    st.dataframe(recs, use_container_width=True)
    if st.button("Run AI Auto-Bid"):
        st.json(api_post("/jobs/auto-bid", {"technician": tech, "skills": skills or ["Networking"]}))


def tools_page() -> None:
    st.subheader("Advanced Tech Tools")
    t1, t2, t3, t4 = st.tabs(["Offline Queue", "Quote + Earnings Optimizer", "Equipment Marketplace", "Compliance Tracker"])
    with t1:
        note = st.text_area("Offline job note")
        if st.button("Queue Offline Action"):
            st.success(str(queue_offline_action("job_note", {"note": note, "date": str(date.today())})))
        st.json(load_json(Path(DATA_DIR / "sync_queue.json"), []))
    with t2:
        scope = st.text_area("Job scope")
        hours = st.number_input("Labor hours", min_value=0.5, value=2.0)
        parts = st.number_input("Parts", min_value=0.0, value=0.0)
        if st.button("Generate AI Quote"):
            st.json(api_post("/quotes/generate", {"scope": scope, "labor_hours": hours, "parts_cost": parts}))
        st.markdown("#### Earnings optimizer")
        recs = api_post("/jobs/match", {"technician": "Optimizer", "skills": ["Fiber", "Troubleshooting"]}, [])
        if recs:
            best = recs[0]
            st.success(f"Best job now: {best['id']} with net ${best['estimated_net']}")
    with t3:
        st.dataframe(api_get("/equipment/marketplace", []), use_container_width=True)
        seller = st.text_input("Seller")
        item = st.text_input("Tool")
        price = st.number_input("Price", min_value=0.0, value=100.0)
        condition = st.selectbox("Condition", ["Used-Good", "Used-Excellent", "Refurbished"])
        if st.button("Post Equipment"):
            st.json(api_post("/equipment/marketplace", {"seller": seller, "item": item, "price": price, "condition": condition}))
    with t4:
        cert = st.text_input("Certification")
        exp = st.date_input("Expiry")
        tech = st.text_input("Technician name")
        if st.button("Add Reminder"):
            st.json(api_post("/compliance/certifications", {"cert": cert, "expiry": str(exp), "technician": tech}))
        st.dataframe(api_get("/compliance/certifications", []), use_container_width=True)


def earnings_protection_page() -> None:
    st.subheader("Earnings & Protection")
    c1, c2 = st.columns(2)
    with c1:
        jid = st.text_input("Job ID", value="J-1001")
        amt = st.number_input("Escrow amount", min_value=0.0, value=300.0)
        instant = st.toggle("Instant payout")
        if st.button("Fund Escrow"):
            st.json(api_post("/payments/escrow", {"job_id": jid, "amount": amt, "instant_payout": instant}))
        st.dataframe(api_get("/payments/escrow", []), use_container_width=True)
    with c2:
        st.markdown("### Dispute Resolution")
        did = st.text_input("Dispute ID", value="D-0002")
        if st.button("Submit Community Vote"):
            st.json(api_post("/disputes/vote", {"dispute_id": did, "vote": "support_tech", "voter": "member01"}))
        st.markdown("### Insurance + Bonding Marketplace")
        st.dataframe(api_get("/insurance/marketplace", []), use_container_width=True)


def community_page() -> None:
    st.subheader("Community Growth")
    a, b = st.columns(2)
    with a:
        st.markdown("### Private Forum")
        for post in api_get("/community/posts", []):
            st.markdown(f"- **{post['title']}** ({post['author']})")
        st.markdown("### Mentorship Matching")
        need = st.text_input("Mentorship focus")
        if st.button("Find Mentor"):
            st.json(api_post("/community/mentorship/match", {"tech": "new-tech", "focus": need}))
        st.markdown("### Success Stories")
        st.dataframe(api_get("/community/success-stories", []), use_container_width=True)
    with b:
        st.markdown("### Earnings Leaderboard (opt-in)")
        st.dataframe(api_get("/community/leaderboard", []), use_container_width=True)
        st.markdown("### Local Meetups + Training Events")
        st.dataframe(api_get("/community/events", []), use_container_width=True)
        st.markdown("### Resource Library")
        st.dataframe(api_get("/resources", []), use_container_width=True)


def triad_analytics_page() -> None:
    st.subheader("Triad369 + Analytics")
    t1, t2 = st.columns(2)
    with t1:
        prompt = st.text_area("Agentora prompt")
        if st.button("Agentora Quote"):
            st.json(api_post("/integrations/agentora/quote", {"prompt": prompt}))
        memo = st.text_area("Memoria note")
        if st.button("Save to Memoria"):
            st.json(api_post("/integrations/memoria/save", {"memory": memo, "date": str(date.today())}))
        litt = st.text_area("LittUp code job")
        if st.button("Queue LittUp"):
            st.json(api_post("/integrations/littup/code-job", {"payload": litt}))
    with t2:
        analytics = api_get("/analytics/earnings", {})
        st.markdown("### Earnings Over Time")
        st.bar_chart(analytics.get("earnings_by_month", {}))
        st.markdown("### Job Heat Map Data")
        st.dataframe(analytics.get("job_heatmap", []), use_container_width=True)


def mobile_pwa_page() -> None:
    st.subheader("Mobile PWA Readiness")
    st.info("FieldHaven v0.3 includes mobile-first quick actions and installable PWA manifest template under templates/pwa_manifest.json.")
    if st.button("Show Today's Schedule", use_container_width=True):
        st.dataframe(api_get("/schedule", []), use_container_width=True)


def main() -> None:
    bootstrap_sample_data()
    start_embedded_api()
    load_css()
    header()
    page = st.sidebar.radio(
        "Navigate",
        ["Smart Matching", "Tech Tools", "Earnings & Protection", "Community", "Triad + Analytics", "Mobile PWA"],
    )
    if page == "Smart Matching":
        smart_matching_page()
    elif page == "Tech Tools":
        tools_page()
    elif page == "Earnings & Protection":
        earnings_protection_page()
    elif page == "Community":
        community_page()
    elif page == "Triad + Analytics":
        triad_analytics_page()
    else:
        mobile_pwa_page()


if __name__ == "__main__":
    main()
