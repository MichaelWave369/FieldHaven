from __future__ import annotations

from datetime import date
from pathlib import Path

import requests
import streamlit as st

from backend.server import start_embedded_api
from core.offline_sync import queue_offline_action
from core.sample_data import bootstrap_sample_data
from core.storage import DATA_DIR, load_json, save_json
from services.ai_assistant import ask_local_ollama

API_BASE = "http://127.0.0.1:8008"
st.set_page_config(page_title="FieldHaven v0.2", page_icon="🛠️", layout="wide")


def load_css() -> None:
    st.markdown(
        """
        <style>
        .stApp {background: radial-gradient(circle at 10% 20%, #1f2430 0%, #10131c 45%, #080a11 100%); color: #f5f5f5;}
        .fh-card {border: 1px solid rgba(255,255,255,0.09); border-left: 4px solid #e63946; background: rgba(255,255,255,0.03); padding: 1rem; border-radius: 14px; margin-bottom: 0.8rem;}
        .fh-accent { color: #ffd166; font-weight: 700; }
        .fh-subtle { color: #98a4b3; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def api_get(endpoint: str, fallback=None):
    try:
        return requests.get(f"{API_BASE}{endpoint}", timeout=3).json()
    except Exception:
        return fallback if fallback is not None else []


def api_post(endpoint: str, payload=None, fallback=None):
    try:
        return requests.post(f"{API_BASE}{endpoint}", json=payload or {}, timeout=4).json()
    except Exception:
        return fallback if fallback is not None else {"message": "offline"}


def quick_actions() -> None:
    c1, c2, c3, c4 = st.columns(4)
    if c1.button("🚨 Emergency Help", use_container_width=True):
        st.error(api_post("/support/emergency")["message"])
    if c2.button("🔄 Sync Offline Queue", use_container_width=True):
        st.success(str(api_post("/offline/sync")))
    if c3.button("💾 Backup", use_container_width=True):
        st.info(api_post("/backup")["file"])
    if c4.button("📅 Smart Schedule", use_container_width=True):
        st.success(api_post("/schedule/auto")["message"])


def dashboard_header() -> None:
    st.title("🛠️ FieldHaven v0.2")
    st.caption("American-first, local-first platform for independent field tech success.")
    quick_actions()
    jobs = load_json(Path(DATA_DIR / "jobs.json"), [])
    invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Open Jobs", len([j for j in jobs if j["status"] == "Open"]))
    k2.metric("Avg Payout", f"${sum(j['payout'] for j in jobs)/max(1,len(jobs)):.0f}")
    k3.metric("Total Earnings", f"${sum(i['amount'] for i in invoices):,.2f}")
    k4.metric("Tech Fee", "0-5%")


def job_marketplace() -> None:
    st.subheader("Advanced Job Tools")
    jobs = api_get("/jobs", load_json(Path(DATA_DIR / "jobs.json"), []))
    for job in jobs:
        route = api_get(f"/jobs/route/{job['id']}", {})
        st.markdown(
            f"<div class='fh-card'><div class='fh-accent'>{job['title']}</div>"
            f"<div>{job['location']} • {job['client']}</div>"
            f"<div>Payout <b>${job['payout']:.2f}</b> | Tech fee <b>{job['platform_fee']}%</b> | Drive est <b>{route.get('estimated_drive_minutes','-')} min</b></div>"
            f"<div class='fh-subtle'>{job['description']}</div></div>",
            unsafe_allow_html=True,
        )
    with st.expander("Bid / Direct Accept"):
        tech_name = st.text_input("Technician Name")
        job_id = st.text_input("Job ID")
        bid = st.number_input("Bid Amount", min_value=0.0, value=250.0)
        if st.button("Submit Bid"):
            res = api_post("/jobs/bid", {"job_id": job_id, "technician": tech_name, "bid_amount": bid, "eta_hours": 24})
            st.success(res["message"])
        if st.button("Direct Accept"):
            res = api_post("/jobs/accept", {"job_id": job_id, "technician": tech_name})
            st.info(res["message"])


def tools_suite() -> None:
    st.subheader("Tools Suite: Offline, Quote, Invoices")
    t1, t2, t3 = st.tabs(["Offline Mode", "Quick Quote (AI)", "Invoices + Escrow"])
    with t1:
        notes = st.text_area("Offline job note")
        if st.button("Save Offline Event"):
            item = queue_offline_action("job_log", {"date": str(date.today()), "notes": notes})
            st.success(f"Queued {item['id']}")
        st.json(load_json(Path(DATA_DIR / "sync_queue.json"), []))
    with t2:
        scope = st.text_area("Scope")
        hrs = st.number_input("Labor hours", min_value=0.5, value=2.0)
        parts = st.number_input("Parts cost", min_value=0.0, value=0.0)
        if st.button("Generate Quote"):
            quote = api_post("/quotes/generate", {"scope": scope, "labor_hours": hrs, "parts_cost": parts})
            st.json(quote)
    with t3:
        client = st.text_input("Invoice client")
        amount = st.number_input("Invoice amount", min_value=0.0, value=350.0)
        job_id = st.text_input("Escrow job ID")
        if st.button("Create Invoice"):
            invoices = load_json(Path(DATA_DIR / "invoices.json"), [])
            payload = {"id": f"INV-{len(invoices)+1:04}", "client": client, "amount": amount, "status": "Escrow Pending"}
            invoices.append(payload)
            save_json(Path(DATA_DIR / "invoices.json"), invoices)
            st.success("Invoice created")
        if st.button("Fund Escrow"):
            st.success(str(api_post("/payments/escrow", {"job_id": job_id, "amount": amount})))


def support_hub() -> None:
    st.subheader("American Support Hub")
    a, b = st.columns(2)
    with a:
        tech = st.text_input("Technician")
        msg = st.text_area("Live chat message")
        if st.button("Start Live Chat"):
            chat = api_post("/support/live-chat", {"technician": tech, "message": msg})
            st.success(f"{chat['agent']}: {chat['response']}")
        issue = st.text_area("Ticket issue")
        if st.button("Create Ticket"):
            t = api_post("/support/ticket", {"technician": tech, "channel": "Ticket", "issue": issue})
            st.info(f"Ticket {t['id']}")
    with b:
        st.markdown("### Knowledge Base")
        st.dataframe(api_get("/support/knowledge-base", []), use_container_width=True)
        st.markdown("### Local AI Troubleshooter")
        q = st.text_area("Troubleshoot prompt")
        if st.button("Ask AI"):
            st.write(ask_local_ollama(q))


def community_and_protection() -> None:
    st.subheader("Community + Fair Pay Protection")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("### Forum + Mentoring")
        for post in api_get("/community/posts", []):
            st.markdown(f"**{post['title']}** — {post['author']}")
            st.caption(post["body"])
        st.markdown("### Success Stories")
        st.dataframe(api_get("/community/success-stories", []), use_container_width=True)
    with c2:
        st.markdown("### Rate the Client")
        st.dataframe(api_get("/clients/ratings", []), use_container_width=True)
        st.markdown("### Dispute Voting")
        dispute_id = st.text_input("Dispute ID", value="D-0001")
        if st.button("Vote: Support Tech"):
            st.success(api_post("/disputes/vote", {"dispute_id": dispute_id, "voter": "community_member", "vote": "support_tech"})["message"])
        st.markdown("### Resource Library")
        st.dataframe(api_get("/resources", []), use_container_width=True)


def triad_integrations() -> None:
    st.subheader("Triad Integrations")
    t1, t2, t3 = st.columns(3)
    with t1:
        st.markdown("**Agentora**")
        prompt = st.text_area("Quote/troubleshoot prompt")
        if st.button("Run Agentora Quote"):
            st.json(api_post("/integrations/agentora/quote", {"prompt": prompt, "model": "llama3.1"}))
    with t2:
        st.markdown("**Memoria**")
        memory = st.text_area("Job memory")
        if st.button("Save to Memoria"):
            st.json(api_post("/integrations/memoria/save", {"memory": memory, "date": str(date.today())}))
    with t3:
        st.markdown("**LittUp**")
        code_job = st.text_area("Code-related job payload")
        if st.button("Send to LittUp"):
            st.json(api_post("/integrations/littup/code-job", {"body": code_job}))


def mobile_view() -> None:
    st.subheader("Mobile Quick View")
    st.write("Optimized quick actions for on-site techs.")
    if st.button("Check Today's Schedule", use_container_width=True):
        st.dataframe(api_get("/schedule", []), use_container_width=True)


def main() -> None:
    bootstrap_sample_data()
    start_embedded_api()
    load_css()
    dashboard_header()
    page = st.sidebar.radio(
        "Navigate",
        ["Job Marketplace", "Tools Suite", "Support Hub", "Community", "Triad", "Mobile"],
    )
    if page == "Job Marketplace":
        job_marketplace()
    elif page == "Tools Suite":
        tools_suite()
    elif page == "Support Hub":
        support_hub()
    elif page == "Community":
        community_and_protection()
    elif page == "Triad":
        triad_integrations()
    else:
        mobile_view()


if __name__ == "__main__":
    main()
