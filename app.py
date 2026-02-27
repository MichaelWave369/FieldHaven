from __future__ import annotations

import requests
import streamlit as st

from backend.server import start_embedded_api
from core.offline_sync import queue_offline_action
from core.sample_data import bootstrap_sample_data

API_BASE = "http://127.0.0.1:8008"
st.set_page_config(page_title="FieldHaven v0.5", page_icon="🛠️", layout="wide")


def apply_theme(mode: str) -> None:
    if mode == "light":
        bg = "#f7f8fb"
        fg = "#141821"
        card = "rgba(20,24,33,.05)"
    else:
        bg = "radial-gradient(circle at 10% 20%, #1f2430 0%, #10131c 45%, #080a11 100%)"
        fg = "#f5f5f5"
        card = "rgba(255,255,255,.03)"

    st.markdown(
        f"""
        <style>
        .stApp {{background: {bg}; color: {fg};}}
        .fh-card {{border:1px solid rgba(255,255,255,.12); border-left:4px solid #e63946; padding:1rem; border-radius:14px; margin-bottom:.6rem; background:{card};}}
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


def ai_page() -> None:
    st.subheader("Advanced AI: Predictive Match + Smart Pricing")
    skills = st.multiselect("Skills", ["POS", "Networking", "Fiber", "Troubleshooting"])
    tech = st.text_input("Technician", "Tech-USA")
    if st.button("Run Predictive Matching"):
        recs = api_post("/ai/predictive-match", {"technician": tech, "skills": skills or ["POS"]}, [])
        st.dataframe(recs, use_container_width=True)

    service_type = st.selectbox("Service Type", ["Fiber", "POS", "Networking"])
    hours = st.number_input("Hours", min_value=0.5, value=2.0)
    urgency = st.selectbox("Urgency", ["standard", "urgent"])
    if st.button("Smart Price Suggestion"):
        st.json(api_post("/ai/smart-pricing", {"service_type": service_type, "labor_hours": hours, "parts_cost": 0, "urgency": urgency}))


def marketplace_page() -> None:
    st.subheader("Full Marketplace")
    st.markdown("#### Tech-to-Tech Listings")
    st.dataframe(api_get("/marketplace/tech", []), use_container_width=True)
    seller = st.text_input("Seller")
    item = st.text_input("Item")
    price = st.number_input("Price", min_value=0.0, value=100.0)
    if st.button("Post Listing"):
        st.json(api_post("/marketplace/tech", {"seller": seller, "category": "Tools", "item": item, "price": price, "condition": "Used-Good"}))

    st.markdown("#### Vendor Deals")
    st.dataframe(api_get("/marketplace/vendor-deals", []), use_container_width=True)


def reporting_page() -> None:
    st.subheader("Advanced Reporting & Finance")
    c1, c2, c3 = st.columns(3)
    tax = api_get("/reports/tax", {})
    forecast = api_get("/reports/forecast", {})
    c1.metric("Estimated Tax", f"${tax.get('estimated_tax',0):,.2f}")
    c2.metric("Quarterly Reserve", f"${tax.get('recommended_quarterly',0):,.2f}")
    c3.metric("Forecast", f"${forecast.get('projected_annual_earnings',0):,.2f}")
    st.info(f"Business Health: {forecast.get('business_health','N/A')}")
    if st.button("Generate QuickBooks Export"):
        st.json(api_post("/exports/quickbooks"))


def governance_page() -> None:
    st.subheader("Community Governance")
    feature = st.text_input("Feature request")
    if st.button("Vote Feature"):
        st.json(api_post("/governance/features", {"feature": feature, "vote": "up"}))
    st.dataframe(api_get("/governance/features", []), use_container_width=True)

    moderator = st.text_input("Moderator nominee")
    if st.button("Elect Moderator"):
        st.json(api_post("/governance/moderators", {"name": moderator, "role": "community_moderator"}))
    st.dataframe(api_get("/governance/moderators", []), use_container_width=True)


def integrations_page() -> None:
    st.subheader("Public API & Triad Integrations")
    st.json(api_get("/public/openapi-links", {}))
    st.json(api_get("/triad/sso", {}))

    prompt = st.text_area("Agentora prompt")
    if st.button("Agentora Quote"):
        st.json(api_post("/integrations/agentora/quote", {"prompt": prompt}))


def polish_page() -> None:
    st.subheader("Polish & Performance")
    if st.button("Queue Offline Action"):
        st.json(queue_offline_action("job_update", {"note": "arrived onsite"}))
    if st.button("Run Offline Sync"):
        st.json(api_post("/offline/sync"))
    if st.button("Push Test Notification"):
        st.json(api_post("/notifications/push", {"type": "payment_alert", "message": "Escrow funded"}))
    st.dataframe(api_get("/notifications/push", []), use_container_width=True)


def main() -> None:
    bootstrap_sample_data()
    start_embedded_api()

    st.title("🛠️ FieldHaven v0.5")
    st.caption("Production-ready, local-first American platform for field tech ownership and growth.")

    mode = st.sidebar.selectbox("Theme", ["dark", "light"])
    apply_theme(mode)

    page = st.sidebar.radio(
        "Navigate",
        ["AI", "Marketplace", "Reporting", "Governance", "API + Triad", "Polish"],
    )

    if page == "AI":
        ai_page()
    elif page == "Marketplace":
        marketplace_page()
    elif page == "Reporting":
        reporting_page()
    elif page == "Governance":
        governance_page()
    elif page == "API + Triad":
        integrations_page()
    else:
        polish_page()


if __name__ == "__main__":
    main()
