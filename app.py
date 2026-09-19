from __future__ import annotations

import io
import json

import streamlit as st

from analyzer import analyze_resume


st.set_page_config(page_title="Shortlist | Resume intelligence", page_icon="S", layout="wide")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap');
:root { --ink:#16211f; --muted:#61706b; --mint:#dff3e8; --lime:#b9df72; --paper:#fbfaf5; --line:#dbe4dc; }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; color:var(--ink); }
.stApp { background: radial-gradient(circle at 90% 0%, #e7f3d4 0, transparent 31%), linear-gradient(135deg, #fbfaf5 0%, #eef7f0 100%); }
h1, h2, h3 { font-family:'Space Grotesk', sans-serif; letter-spacing:0; }
h1 { font-size:3rem !important; line-height:1.05 !important; max-width:720px; }
.eyebrow { color:#557361; font-size:.75rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.4rem; }
.panel { background:rgba(255,255,255,.74); border:1px solid var(--line); border-radius:8px; padding:1.15rem 1.25rem; }
.score { font-family:'Space Grotesk'; font-size:3.9rem; font-weight:700; line-height:1; color:#315f43; }
.pill { display:inline-block; border-radius:999px; padding:.3rem .65rem; font-size:.78rem; font-weight:700; background:var(--mint); color:#285339; }
.gap { color:#9b463a; background:#fceae5; }
.muted { color:var(--muted); }
section[data-testid="stSidebar"] { background:#18302b; }
section[data-testid="stSidebar"] * { color:#edf5e9 !important; }
</style>
""", unsafe_allow_html=True)


def read_upload(upload) -> str:
    data = upload.getvalue()
    if upload.name.lower().endswith(".txt"):
        return data.decode("utf-8", errors="ignore")
    if upload.name.lower().endswith(".pdf"):
        from pypdf import PdfReader
        return "\n".join(page.extract_text() or "" for page in PdfReader(io.BytesIO(data)).pages)
    if upload.name.lower().endswith(".docx"):
        from docx import Document
        return "\n".join(paragraph.text for paragraph in Document(io.BytesIO(data)).paragraphs)
    return ""


def report_json(report) -> str:
    return json.dumps({
        "candidate": report.profile.name,
        "contact": {"email": report.profile.email, "phone": report.profile.phone},
        "score": report.score,
        "recommendation": report.recommendation,
        "skills": report.profile.skills,
        "required_matches": report.required_matches,
        "required_gaps": report.required_gaps,
        "preferred_matches": report.preferred_matches,
        "rationale": report.rationale,
    }, indent=2)


with st.sidebar:
    st.markdown("## SHORTLIST")
    st.caption("Resume intelligence, kept explainable.")
    st.markdown("### Workflow")
    st.markdown("1. Add the role brief\n2. Upload candidate resumes\n3. Compare the evidence")
    st.markdown("---")
    st.caption("Scoring weights: required skills 70%, experience 20%, preferred skills 10%.")

st.markdown('<div class="eyebrow">Hiring workspace / 01</div>', unsafe_allow_html=True)
st.title("Find the signal in every resume.")
st.markdown("Define the role once, then get consistent, evidence-backed screening reports across your candidate set.")
st.divider()

left, right = st.columns([1, 1], gap="large")
with left:
    st.markdown("### Role brief")
    job_text = st.text_area(
        "Job description", height=245,
        placeholder="Required qualifications\nPython\nSQL\nAt least 3 years experience\n\nPreferred\nDocker\nAWS",
        label_visibility="collapsed",
    )
with right:
    st.markdown("### Candidate resumes")
    uploads = st.file_uploader("Upload .txt, .pdf, or .docx files", type=["txt", "pdf", "docx"], accept_multiple_files=True)
    pasted = st.text_area("Or paste one resume", height=164, placeholder="Candidate name\nemail@example.com\nSkills: Python, SQL...", label_visibility="collapsed")

if st.button("Analyze candidates", type="primary", use_container_width=True):
    if not job_text.strip():
        st.error("Add a job description before analyzing.")
    elif not uploads and not pasted.strip():
        st.error("Upload or paste at least one resume.")
    else:
        candidates = [(upload.name, read_upload(upload)) for upload in uploads]
        if pasted.strip():
            candidates.append(("Pasted resume", pasted))
        st.session_state["reports"] = [(name, analyze_resume(text, job_text)) for name, text in candidates if text.strip()]

reports = st.session_state.get("reports", [])
if reports:
    st.divider()
    st.markdown(f"### Screening results <span class='muted'>/{len(reports)} candidates</span>", unsafe_allow_html=True)
    ordered = sorted(reports, key=lambda item: item[1].score, reverse=True)
    for filename, report in ordered:
        with st.container(border=True):
            summary, score_col, action = st.columns([3, 1, 1])
            with summary:
                st.markdown(f"#### {report.profile.name}")
                st.caption(f"{filename}  ·  {report.profile.email}")
                st.markdown(" ".join(f"`{skill}`" for skill in report.profile.skills[:8]) or "No recognized skills")
            with score_col:
                st.markdown(f"<div class='score'>{report.score}<small>/100</small></div>", unsafe_allow_html=True)
                st.markdown(f"<span class='pill {'gap' if report.recommendation == 'Do not advance' else ''}'>{report.recommendation}</span>", unsafe_allow_html=True)
            with action:
                st.download_button("Download report", report_json(report), file_name=f"{report.profile.name.replace(' ', '_')}_report.json", mime="application/json", key=filename)
            with st.expander("View analysis"):
                detail_left, detail_right = st.columns(2)
                with detail_left:
                    st.markdown("**What matches**")
                    st.write(", ".join(report.required_matches + report.preferred_matches) or "No direct matches found")
                    st.markdown("**Rationale**")
                    for item in report.rationale:
                        st.write(f"- {item}")
                with detail_right:
                    st.markdown("**Required gaps**")
                    st.write(", ".join(report.required_gaps) or "None")
                    st.markdown("**Profile**")
                    st.write(f"Experience: {report.profile.years_experience:g} years")
                    st.write(f"Education: {'; '.join(report.profile.education) or 'Not found'}")