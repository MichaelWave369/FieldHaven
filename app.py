from __future__ import annotations

import requests
import streamlit as st

from backend.server import start_embedded_api
from core.offline_sync import queue_offline_action
from core.sample_data import bootstrap_sample_data

API_BASE = "http://127.0.0.1:8008"
st.set_page_config(page_title="FieldHaven v0.6", page_icon="🛠️", layout="wide")


def theme(mode: str) -> None:
    if mode == "light":
        bg = "#f6f7fb"
        fg = "#161b22"
        card = "rgba(0,0,0,.03)"
    else:
        bg = "radial-gradient(circle at 10% 20%, #1f2430 0%, #10131c 45%, #080a11 100%)"
        fg = "#f5f5f5"
        card = "rgba(255,255,255,.03)"
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
        return requests.get(f"{API_BASE}{endpoint}", timeout=5).json()
    except Exception:
        return fallback if fallback is not None else []


def api_post(endpoint: str, payload=None, fallback=None):
    try:
        return requests.post(f"{API_BASE}{endpoint}", json=payload or {}, timeout=8).json()
    except Exception:
        return fallback if fallback is not None else {"message": "offline"}


def pwa_page() -> None:
    st.subheader("Multi-Platform Experience")
    st.json(api_get("/pwa/config", {}))
    st.json(api_get("/pwa/manifest", {}))
    if st.button("Queue Offline Action"):
        st.json(queue_offline_action("visit", {"context": "mobile_pwa"}))
    if st.button("Run Background Sync"):
        st.json(api_post("/offline/background-sync"))


def monetization_page() -> None:
    st.subheader("Advanced Monetization (Tech-Friendly)")
    st.dataframe(api_get("/monetization/premium-tiers", []), use_container_width=True)
    tech = st.text_input("Technician", "Tech-USA")
    if st.button("Subscribe Premium"):
        st.json(api_post("/monetization/subscribe", {"technician": tech, "tier": "premium_plus"}))
    actions = st.number_input("Community contribution actions", min_value=0, value=10)
    if st.button("Calculate Revenue Share"):
        st.json(api_post("/monetization/revenue-share", {"technician": tech, "community_actions": int(actions)}))


def directory_page() -> None:
    st.subheader("National Directory & Reputation")
    st.dataframe(api_get("/directory/techs", []), use_container_width=True)
    name = st.text_input("New Technician Profile")
    state = st.text_input("State", "TX")
    if st.button("Add Verified Profile"):
        st.json(api_post("/directory/techs", {"technician": name, "state": state, "skills": ["POS", "Networking"], "verified": True}))

    st.markdown("### Client Reviews")
    st.dataframe(api_get("/reviews/clients", []), use_container_width=True)
    if st.button("Add Client Review"):
        st.json(api_post("/reviews/clients", {"client": "SampleClient", "technician": name or "Tech-USA", "rating": 4.8, "review": "Great scope clarity and fast pay."}))


def ai_coach_page() -> None:
    st.subheader("AI Business Coach")
    context = st.text_area("Business coaching context", "Improve pricing and tax planning for a 2-tech operation.")
    if st.button("Get AI Coach Advice"):
        st.write(api_post("/ai/business-coach", {"context": context}).get("advice", ""))
    st.markdown("### Predictive Match")
    st.dataframe(api_post("/ai/predictive-match", {"technician": "Tech-USA", "skills": ["POS", "Fiber"]}, []), use_container_width=True)
    st.markdown("### Smart Pricing")
    st.json(api_post("/ai/smart-pricing", {"service_type": "POS", "labor_hours": 2.0, "parts_cost": 15.0, "urgency": "standard"}))


def enterprise_page() -> None:
    st.subheader("Enterprise & Partnerships")
    if st.button("Create Company Account"):
        st.json(api_post("/enterprise/company-accounts", {"name": "USA Tech Crew", "owner": "Owner01", "size": 5}))
    st.dataframe(api_get("/enterprise/company-accounts", []), use_container_width=True)
    st.markdown("### Official Partnerships")
    st.dataframe(api_get("/enterprise/partnerships", []), use_container_width=True)


def final_polish_page() -> None:
    st.subheader("Final Polish & Scale")
    st.metric("API Health", api_get("/health", {}).get("status", "unknown"))
    st.json(api_get("/reports/business-health", {}))
    if st.button("Run Security Audit Log"):
        st.json(api_post("/security/audit/log", {"actor": "system", "event": "routine_check"}))
    st.json(api_get("/security/audit", {}))
    if st.button("Export Full Vault"):
        st.json(api_post("/vault/export"))
    st.markdown("### Community Events")
    st.dataframe(api_get("/events/community", []), use_container_width=True)
    st.markdown("### Certification Programs")
    st.dataframe(api_get("/programs/certifications", []), use_container_width=True)


def integrations_page() -> None:
    st.subheader("Public API & Triad369 Integrations")
    st.json(api_get("/integrations/public", {}))
    st.json(api_get("/triad/sso", {}))
    prompt = st.text_input("Agentora Prompt")
    if st.button("Run Agentora Quote"):
        st.json(api_post("/integrations/agentora/quote", {"prompt": prompt}))


def main() -> None:
    bootstrap_sample_data()
    start_embedded_api()

    st.title("🛠️ FieldHaven v0.6")
    st.caption("Premium professional American platform built tech-first, local-first, and open-source.")

    mode = st.sidebar.selectbox("Theme", ["dark", "light"])
    theme(mode)

    page = st.sidebar.radio(
        "Navigate",
        ["PWA", "Monetization", "Directory", "AI Coach", "Enterprise", "Final Polish", "Integrations"],
    )

    if page == "PWA":
        pwa_page()
    elif page == "Monetization":
        monetization_page()
    elif page == "Directory":
        directory_page()
    elif page == "AI Coach":
        ai_coach_page()
    elif page == "Enterprise":
        enterprise_page()
    elif page == "Final Polish":
        final_polish_page()
    else:
        integrations_page()


if __name__ == "__main__":
    main()
