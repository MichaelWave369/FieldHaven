from __future__ import annotations

from pathlib import Path

import requests
import streamlit as st

from backend.server import start_embedded_api
from core.offline_sync import queue_offline_action
from core.sample_data import bootstrap_sample_data
from core.storage import DATA_DIR, load_json

API_BASE = "http://127.0.0.1:8008"
st.set_page_config(page_title="FieldHaven v0.4", page_icon="🛠️", layout="wide")


def load_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {background: radial-gradient(circle at 10% 20%, #1f2430 0%, #10131c 45%, #080a11 100%); color: #f5f5f5;}
        .card {border:1px solid rgba(255,255,255,.12); border-left:4px solid #e63946; padding:1rem; border-radius:14px; margin-bottom:.7rem; background:rgba(255,255,255,.03)}
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_get(endpoint: str, fallback=None):
    try:
        return requests.get(f"{API_BASE}{endpoint}", timeout=5).json()
    except Exception:
        return fallback if fallback is not None else []


def api_post(endpoint: str, payload=None, fallback=None):
    try:
        return requests.post(f"{API_BASE}{endpoint}", json=payload or {}, timeout=8).json()
    except Exception:
        return fallback if fallback is not None else {"message": "offline"}


def top_bar() -> None:
    a, b, c, d = st.columns(4)
    if a.button("🚨 Emergency", use_container_width=True):
        st.error(api_post("/support/emergency")["message"])
    if b.button("🔄 Smart Sync", use_container_width=True):
        st.success(str(api_post("/offline/sync")))
    if c.button("📦 Vault Export", use_container_width=True):
        st.info(str(api_post("/vault/export")))
    if d.button("🔔 Push Alert Test", use_container_width=True):
        st.json(api_post("/notifications/push", {"kind": "new_job", "text": "New job available"}))


def team_page() -> None:
    st.subheader("Scaling & Team Features")
    c1, c2 = st.columns(2)
    with c1:
        team_id = st.text_input("Team ID", "TEAM-USA-01")
        job_id = st.text_input("Assign Job ID", "J-1001")
        tech = st.text_input("Technician", "TechA")
        if st.button("Assign Job"):
            st.json(api_post("/teams/assign", {"team_id": team_id, "job_id": job_id, "technician": tech}))
        st.dataframe(api_get(f"/teams/calendar/{team_id}", []), use_container_width=True)
    with c2:
        sender = st.text_input("Crew Chat Sender", "CrewLead")
        msg = st.text_area("Crew Chat Message")
        if st.button("Send Crew Message"):
            st.json(api_post("/teams/chat", {"team_id": team_id, "sender": sender, "message": msg}))
        st.dataframe(api_get(f"/teams/chat/{team_id}", []), use_container_width=True)


def business_page() -> None:
    st.subheader("Business Intelligence + AI Advisor")
    analytics = api_get("/analytics/business", {})
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Earnings", f"${analytics.get('total_earnings',0):,.2f}")
    m2.metric("Avg Job Payout", f"${analytics.get('avg_job_payout',0):,.2f}")
    m3.metric("Tax Reserve", f"${analytics.get('estimated_tax_reserve',0):,.2f}")
    st.dataframe(analytics.get("top_profitable_jobs", []), use_container_width=True)
    ctx = st.text_area("AI business advisor context", "Improve pricing, marketing, and growth for a 2-tech crew.")
    if st.button("Run AI Advisor"):
        st.write(api_post("/advisor/business", {"context": ctx}).get("response", ""))


def vendor_page() -> None:
    st.subheader("Partnerships & Vendor Resources")
    st.dataframe(api_get("/vendor/marketplace", []), use_container_width=True)
    purpose = st.selectbox("Financing purpose", ["Van lease", "Tool financing", "Insurance premium", "Equipment lease"])
    amount = st.number_input("Requested amount", min_value=0.0, value=5000.0)
    if st.button("One-click Financing"):
        st.json(api_post("/vendor/financing", {"purpose": purpose, "amount": amount}))


def mobile_page() -> None:
    st.subheader("Mobile + Notifications")
    st.info("PWA manifest + push notification APIs are enabled for installable mobile workflows.")
    if st.button("Queue Offline Note"):
        st.json(queue_offline_action("field_update", {"note": "Completed initial diagnostics"}))
    conflict = st.text_input("Conflict ID", "CF-001")
    if st.button("Resolve Sync Conflict"):
        st.json(api_post("/offline/resolve-conflict", {"conflict_id": conflict, "resolution": "latest_timestamp_wins"}))
    st.dataframe(api_get("/notifications/push", []), use_container_width=True)


def security_page() -> None:
    st.subheader("Security, Ownership, Governance")
    p1, p2 = st.columns(2)
    with p1:
        if st.button("Save Privacy Settings"):
            st.json(api_post("/privacy/settings", {"share_analytics": False, "allow_leaderboard": True, "mode": "private-by-default"}))
        action = st.text_input("Audit action", "updated_escrow")
        if st.button("Write Audit Log"):
            st.json(api_post("/audit/logs", {"actor": "owner", "action": action}))
        st.dataframe(api_get("/audit/logs", []), use_container_width=True)
    with p2:
        feat = st.text_input("Feature request", "Crew bulk dispatch")
        if st.button("Submit Governance Vote"):
            st.json(api_post("/governance/features", {"feature": feat, "vote": "up"}))
        st.dataframe(api_get("/governance/features", []), use_container_width=True)


def triad_page() -> None:
    st.subheader("Triad369 Deep Integration")
    st.json(api_get("/triad/sso", {}))
    prompt = st.text_area("Agentora prompt")
    if st.button("Agentora Quote"):
        st.json(api_post("/integrations/agentora/quote", {"prompt": prompt}))
    memo = st.text_area("Memoria note")
    if st.button("Save Memoria"):
        st.json(api_post("/integrations/memoria/save", {"note": memo}))
    litt = st.text_area("LittUp code task")
    if st.button("Queue LittUp Task"):
        st.json(api_post("/integrations/littup/code-job", {"task": litt}))


def main() -> None:
    bootstrap_sample_data()
    start_embedded_api()
    load_css()
    st.title("🛠️ FieldHaven v0.4")
    st.caption("Professional, scalable, American-first field tech platform.")
    top_bar()

    page = st.sidebar.radio(
        "Navigate",
        ["Teams", "Business Intel", "Vendor Hub", "Mobile + Notifications", "Security + Governance", "Triad SSO"],
    )

    if page == "Teams":
        team_page()
    elif page == "Business Intel":
        business_page()
    elif page == "Vendor Hub":
        vendor_page()
    elif page == "Mobile + Notifications":
        mobile_page()
    elif page == "Security + Governance":
        security_page()
    else:
        triad_page()


if __name__ == "__main__":
    main()
