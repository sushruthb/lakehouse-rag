import os
import requests
import streamlit as st

API_URL = os.environ.get("API_URL", "http://localhost:8080")

st.set_page_config(page_title="Lakehouse RAG", page_icon="🏛️", layout="wide")
st.title("🏛️ Lakehouse RAG Platform")
st.caption("Enterprise-grade RAG on Lakehouse architecture — arXiv AI/ML papers")

tab_qa, tab_lineage = st.tabs(["Q&A", "Data Lineage"])

with tab_qa:
    st.subheader("Ask a question about AI/ML research")
    question = st.text_input("Your question", placeholder="What is attention mechanism in transformers?")
    if st.button("Ask", type="primary") and question:
        with st.spinner("Retrieving and synthesising answer..."):
            try:
                resp = requests.post(f"{API_URL}/query", json={"question": question}, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    st.markdown("### Answer")
                    st.write(data["answer"])
                    st.markdown("### Sources")
                    for s in data["sources"]:
                        st.markdown(f"- [{s['title']}]({s['arxiv_url']}) (`{s['paper_id']}`)")
                else:
                    st.error(resp.json().get("error", "Unexpected error"))
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API. Is the pipeline running? Try `make seed` first.")

with tab_lineage:
    st.subheader("Trace a paper through the Medallion pipeline")
    paper_id = st.text_input("Paper ID", placeholder="2301.00001")
    if st.button("Trace Lineage", type="primary") and paper_id:
        with st.spinner("Fetching lineage..."):
            try:
                resp = requests.get(f"{API_URL}/lineage/{paper_id}", timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    events = data.get("events", [])
                    if events:
                        st.markdown("### Lineage Chain")
                        for e in events:
                            st.markdown(
                                f"**{e['run_at']}** — `{e['source']}` → `{e['target']}` via `{e['model']}`"
                            )
                    else:
                        st.info("No lineage events found for this paper ID.")
                else:
                    st.error("Failed to fetch lineage.")
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to API.")
