from __future__ import annotations

from datetime import date
from pathlib import Path

import requests
import streamlit as st

from backend.server import start_embedded_api
from core.sample_data import bootstrap_sample_data
from core.storage import DATA_DIR, load_json, save_json
from services.ai_assistant import ask_local_ollama

st.set_page_config(page_title="FieldHaven v0.1", page_icon="🛠️", layout="wide")


def load_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {
            background: radial-gradient(circle at 10% 20%, #1f2430 0%, #10131c 45%, #080a11 100%);
            color: #f5f5f5;
        }
        .fh-card {
            border: 1px solid rgba(255,255,255,0.09);
            border-left: 4px solid #e63946;
            background: rgba(255,255,255,0.03);
            padding: 1rem;
            border-radius: 14px;
            margin-bottom: 0.8rem;
        }
        .fh-accent { color: #ffd166; font-weight: 700; }
        .fh-subtle { color: #98a4b3; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_get(endpoint: str, fallback: list[dict] | None = None):
    try:
        return requests.get(f"http://127.0.0.1:8008{endpoint}", timeout=2).json()
    except Exception:
        return fallback if fallback is not None else []


def market_view() -> None:
    st.subheader("Fair Job Marketplace")
    st.caption("Transparent pay. Low/zero tech fees. American support built in.")
    jobs = api_get("/jobs", load_json(Path(DATA_DIR / "jobs.json"), []))
    cols = st.columns(3)
    for idx, job in enumerate(jobs):
        with cols[idx % 3]:
            st.markdown(
                f"""
                <div class='fh-card'>
                    <div class='fh-accent'>{job['title']}</div>
                    <div>{job['location']} • {job['client']}</div>
                    <div>Payout: <b>${job['payout']:.2f}</b> | Tech fee: <b>{job['platform_fee']}%</b></div>
                    <div class='fh-subtle'>{job['description']}</div>
                    <div>Status: {job['status']}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    with st.expander("Bid / Direct Accept"):
        tech_name = st.text_input("Technician Name", key="bid_tech")
        job_id = st.text_input("Job ID", key="job_id")
        bid = st.number_input("Bid Amount", min_value=0.0, value=250.0)
        eta = st.number_input("ETA (hours)", min_value=1, value=24)
        c1, c2 = st.columns(2)
        if c1.button("Submit Bid"):
            payload = {"job_id": job_id, "technician": tech_name, "bid_amount": bid, "eta_hours": int(eta)}
            response = requests.post("http://127.0.0.1:8008/jobs/bid", json=payload, timeout=3).json()
            st.success(response["message"])
        if c2.button("Direct Accept"):
            payload = {"job_id": job_id, "technician": tech_name}
            response = requests.post("http://127.0.0.1:8008/jobs/accept", json=payload, timeout=3).json()
            st.info(response["message"])


def tools_view() -> None:
    st.subheader("Tech Tools Suite")
    tab1, tab2, tab3, tab4 = st.tabs(["Offline Logs", "Invoicing", "Tax & Docs", "Training & Safety"])
    with tab1:
        start = st.time_input("Start", key="log_start")
        end = st.time_input("End", key="log_end")
        notes = st.text_area("Work Notes", key="log_notes")
        if st.button("Save Local Job Log"):
            logs_path = Path(DATA_DIR / "job_logs.json")
            logs = load_json(logs_path, [])
            logs.append({"date": str(date.today()), "start": str(start), "end": str(end), "notes": notes})
            save_json(logs_path, logs)
            st.success("Saved locally for offline-first workflow.")
    with tab2:
        st.write("Generate fast invoices and track payout guarantees.")
        client = st.text_input("Client", key="inv_client")
        amount = st.number_input("Amount", min_value=0.0, value=325.0, key="inv_amt")
        if st.button("Generate Invoice"):
            invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
            invoice = {
                "id": f"INV-{len(invoices)+1:04}",
                "client": client,
                "amount": amount,
                "status": "Escrow Pending",
                "generated_on": str(date.today()),
            }
            invoices.append(invoice)
            save_json(Path(DATA_DIR / "invoices.json"), invoices)
            st.json(invoice)
    with tab3:
        income = st.number_input("Estimated annual 1099 income", min_value=0.0, value=65000.0)
        rate = st.slider("Tax reserve %", 10, 40, 24)
        reserve = income * (rate / 100)
        st.metric("Suggested tax reserve", f"${reserve:,.2f}")
        st.markdown("Document templates are available in `/templates` for invoice, dispute, and safety plans.")
    with tab4:
        cert = st.text_input("Certification Name")
        expiry = st.date_input("Expiration Date")
        if st.button("Track Certification"):
            certs = load_json(Path(DATA_DIR / "certifications.json"), [])
            certs.append({"cert": cert, "expiry": str(expiry)})
            save_json(Path(DATA_DIR / "certifications.json"), certs)
            st.success("Certification tracked.")
        st.info("Insurance marketplace integration hooks ready for preferred US carriers.")


def support_and_community_view() -> None:
    st.subheader("American Support + Community Protection")
    left, right = st.columns(2)
    with left:
        st.markdown("### Real Humans in the US")
        st.write("Chat, phone, and ticket support handled by US-based human teams.")
        tech = st.text_input("Technician", key="ticket_tech")
        channel = st.selectbox("Channel", ["Chat", "Phone", "Ticket"])
        issue = st.text_area("Issue")
        if st.button("Open Support Ticket"):
            payload = {"technician": tech, "channel": channel, "issue": issue}
            response = requests.post("http://127.0.0.1:8008/support/ticket", json=payload, timeout=3).json()
            st.success(f"Ticket {response['id']} created")
            st.caption(response["sla"])

        st.markdown("### Local AI Assistant (Ollama)")
        prompt = st.text_area("Ask for quote, troubleshooting plan, or invoice wording")
        if st.button("Ask Assistant"):
            st.write(ask_local_ollama(prompt))

    with right:
        st.markdown("### Rate the Client")
        ratings = api_get("/clients/ratings", [])
        st.dataframe(ratings, use_container_width=True)

        st.markdown("### Private Tech Community")
        posts = api_get("/community/posts", [])
        for post in posts:
            st.markdown(f"**{post['title']}** — {post['author']}")
            st.caption(post["body"])

        st.markdown("### Dispute Resolution")
        st.write("Community voting or neutral arbitration options are available for payment/scope disputes.")


def integration_view() -> None:
    st.subheader("Triad369 Integration")
    st.markdown("- Agentora/Memoria SSO hook points pre-wired.")
    st.markdown("- Agentora task hooks can assist with quote generation and troubleshooting.")
    st.code(
        """
POST /hooks/agentora/quote
POST /hooks/agentora/troubleshoot
GET  /auth/memoria/callback
        """
    )
    if st.button("Create Local Backup"):
        response = requests.post("http://127.0.0.1:8008/backup", timeout=3).json()
        st.success(response["message"])
        st.caption(response["file"])


def dashboard_header() -> None:
    st.title("🛠️ FieldHaven v0.1")
    st.caption("The American Field Tech Haven — fair marketplace, real US support, local-first privacy.")
    k1, k2, k3, k4 = st.columns(4)
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    open_jobs = len([j for j in jobs if j["status"] == "Open"])
    k1.metric("Open Jobs", open_jobs)
    k2.metric("Avg Payout", f"${sum(j['payout'] for j in jobs)/max(1,len(jobs)):.0f}")
    k3.metric("Tech Fees", "0-5%")
    k4.metric("Support Region", "USA")


def main() -> None:
    bootstrap_sample_data()
    start_embedded_api()
    load_css()
    dashboard_header()

    page = st.sidebar.radio(
        "Navigate",
        ["Job Board", "Calendar & Earnings", "Tools Suite", "Support + Community", "Triad369 Hooks"],
    )

    if page == "Job Board":
        market_view()
    elif page == "Calendar & Earnings":
        st.subheader("Calendar & Earnings Tracker")
        st.write("Mobile-first calendar block is ready for sync providers (Google, Outlook, CalDAV).")
        invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
        paid = sum(inv["amount"] for inv in invoices)
        st.metric("Total Logged Earnings", f"${paid:,.2f}")
        st.dataframe(invoices, use_container_width=True)
    elif page == "Tools Suite":
        tools_view()
    elif page == "Support + Community":
        support_and_community_view()
    else:
        integration_view()


if __name__ == "__main__":
    main()
