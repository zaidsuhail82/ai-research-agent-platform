import streamlit as st
import os
import requests
import xml.etree.ElementTree as ET
import random
import base64
import json
import time
from datetime import datetime
from typing import List, Dict

# ================================================================
# 1. PAGE CONFIGURATION
# ================================================================

st.set_page_config(
    page_title="AI Research Agent | Muhammad Zaid Suhail",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================================================================
# 2. GLOBAL CONFIG
# ================================================================

ARXIV_API = "http://export.arxiv.org/api/query"
HF_API = "https://router.huggingface.co/hf-inference/models/facebook/bart-large-cnn"

HEADERS = {
    "Authorization": f"Bearer {st.secrets['HUGGINGFACE_TOKEN']}"
}

OPENING_PHRASES = [
    "explored",
    "examined",
    "investigated",
    "analyzed",
    "evaluated",
    "introduced",
    "developed",
    "presented",
    "demonstrated",
    "proposed"
]

# ================================================================
# 3. SESSION STATE
# ================================================================

if "papers" not in st.session_state:
    st.session_state.papers = []

if "selected_papers" not in st.session_state:
    st.session_state.selected_papers = {}

if "report" not in st.session_state:
    st.session_state.report = None

if "notes" not in st.session_state:
    st.session_state.notes = ""

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ================================================================
# 4. ADVANCED CSS
# ================================================================

st.markdown("""
<style>

body {
background: radial-gradient(circle at top right,#161b22,#0d1117);
color:#c9d1d9;
font-family: Inter;
}

.hero {
text-align:center;
padding:40px;
background:rgba(255,255,255,0.02);
border-radius:20px;
border:1px solid rgba(255,255,255,0.1);
margin-bottom:30px;
}

.title {
font-size:3rem;
font-weight:800;
background:linear-gradient(90deg,#58a6ff,#00f2fe);
-webkit-background-clip:text;
-webkit-text-fill-color:transparent;
}

.resultbox {
background:#0d1117;
border:1px solid #30363d;
padding:25px;
border-radius:10px;
font-family:monospace;
white-space:pre-wrap;
position:relative;
}

.copybtn {
position:absolute;
top:10px;
right:10px;
background:#238636;
border:none;
color:white;
padding:6px 12px;
border-radius:6px;
cursor:pointer;
}

</style>

<script>
function copyText(id){
let text=document.getElementById(id).innerText;
navigator.clipboard.writeText(text);
}
</script>
""", unsafe_allow_html=True)

# ================================================================
# 5. UTILITY FUNCTIONS
# ================================================================

def format_author(authors: str, style="IEEE"):

    try:
        a = authors.split(",")[0].strip()
        parts = a.split(" ")
        last = parts[-1]
        first = parts[0][0]

        if style == "IEEE":
            return f"{first}. {last}"
        else:
            suffix = " et al." if "," in authors else ""
            return f"{last}, {first}.{suffix}"

    except:
        return "Unknown"

# ------------------------------------------------

def hf_query(prompt, min_len=80, max_len=200):

    payload = {
        "inputs": prompt[:3000],
        "parameters":{
            "min_length":min_len,
            "max_length":max_len,
            "do_sample":False
        }
    }

    try:
        r = requests.post(HF_API,headers=HEADERS,json=payload)

        if r.status_code==200:
            j=r.json()
            if isinstance(j,list):
                return j[0]["summary_text"]

        return "API Error"

    except Exception as e:
        return str(e)

# ------------------------------------------------

def fetch_arxiv(query,limit=5):

    url=f"{ARXIV_API}?search_query=all:{query}&start=0&max_results={limit}"

    r=requests.get(url)

    root=ET.fromstring(r.content)

    ns={"atom":"http://www.w3.org/2005/Atom"}

    papers=[]

    for entry in root.findall("atom:entry",ns):

        title=entry.find("atom:title",ns).text.strip()

        summary=entry.find("atom:summary",ns).text.strip()

        authors=[a.find("atom:name",ns).text for a in entry.findall("atom:author",ns)]

        year=entry.find("atom:published",ns).text[:4]

        pid=entry.find("atom:id",ns).text.split("/")[-1]

        papers.append({
            "title":title,
            "summary":summary,
            "authors":",".join(authors),
            "year":year,
            "id":pid
        })

    return papers

# ------------------------------------------------

def generate_lit(summary,style="IEEE",words=120):

    min_len=int(words*0.9)
    max_len=int(words*1.4)

    prompt=f"""
    Write a professional academic literature review summary.
    Style: {style}.
    Focus on methodology, contributions and results.

    Text:
    {summary}
    """

    return hf_query(prompt,min_len,max_len)

# ------------------------------------------------

def generate_research_idea(topic):

    prompt=f"""
    Generate three novel AI research ideas for topic:

    {topic}

    Include:
    - Problem
    - Proposed Method
    - Expected Contribution
    """

    return hf_query(prompt,120,220)

# ------------------------------------------------

def extract_keywords(text):

    words=text.split()

    freq={}

    for w in words:

        w=w.lower().strip(".,()")

        if len(w)<4:
            continue

        freq[w]=freq.get(w,0)+1

    k=sorted(freq,key=freq.get,reverse=True)

    return k[:10]

# ------------------------------------------------

def generate_methodology(topic):

    prompt=f"""
    Design an academic research methodology for:

    {topic}

    Include:
    dataset
    evaluation metrics
    model architecture
    experimental setup
    """

    return hf_query(prompt,120,220)

# ------------------------------------------------

def dataset_finder(topic):

    prompt=f"""
    Suggest real public datasets for research topic:

    {topic}

    Include dataset name and description.
    """

    return hf_query(prompt,80,160)

# ================================================================
# 6. HEADER
# ================================================================

st.markdown('<div class="hero">',unsafe_allow_html=True)

logo_path="media/logo.png"

if os.path.exists(logo_path):
    st.image(logo_path,width=250)

st.markdown('<div class="title">AI Research Agent</div>',unsafe_allow_html=True)

st.caption("Advanced Scientific Discovery Platform — Muhammad Zaid Suhail")

st.markdown("</div>",unsafe_allow_html=True)

# ================================================================
# 7. MAIN TABS
# ================================================================

tab1,tab2,tab3,tab4,tab5,tab6 = st.tabs([
"🌍 Global Discovery",
"📚 Literature Review",
"📊 Paper Comparison",
"🧠 Research Tools",
"💬 AI Assistant",
"📝 Research Notes"
])

# ================================================================
# TAB 1 GLOBAL DISCOVERY
# ================================================================

with tab1:

    st.subheader("Semantic Paper Search")

    col1,col2,col3=st.columns([6,1,2])

    with col1:
        query=st.text_input("Research Topic")

    with col2:
        limit=st.number_input("Limit",1,10,5)

    with col3:
        search=st.button("Search")

    if search and query:

        with st.spinner("Searching arXiv..."):

            papers=fetch_arxiv(query,limit)

            st.session_state.papers=papers

    for i,p in enumerate(st.session_state.papers):

        with st.container():

            c1,c2=st.columns([7,1])

            with c1:

                st.markdown(f"**{p['title']}**")

                st.caption(f"{p['authors']} ({p['year']})")

                with st.expander("Abstract"):
                    st.write(p["summary"])

            with c2:

                if st.checkbox("Select",key=f"s{i}"):

                    st.session_state.selected_papers[i]=p

# ================================================================
# TAB 2 LITERATURE REVIEW
# ================================================================

with tab2:

    st.subheader("Multi Paper Literature Review")

    style=st.selectbox("Citation Style",["IEEE","Harvard"])

    words=st.slider("Words",50,250,120)

    if st.button("Generate Review"):

        report=""

        for p in st.session_state.selected_papers.values():

            cite=format_author(p["authors"],style)

            verb=random.choice(OPENING_PHRASES)

            review=generate_lit(p["summary"],style,words)

            report+=f"{cite} ({p['year']}) {verb} {p['title']}. {review}\n\n"

        st.session_state.report=report

    if st.session_state.report:

        st.markdown(f"""
        <div class="resultbox">
        <button class="copybtn" onclick="copyText('rbox')">Copy</button>
        <div id="rbox">{st.session_state.report}</div>
        </div>
        """,unsafe_allow_html=True)

# ================================================================
# END PART 1
# ================================================================

# ================================================================
# TAB 3 — PAPER COMPARISON ENGINE
# ================================================================

with tab3:

    st.subheader("Paper Comparison Engine")

    if len(st.session_state.selected_papers) < 2:
        st.info("Select at least two papers in the Global Discovery tab.")
    else:

        papers = list(st.session_state.selected_papers.values())

        p1 = st.selectbox(
            "Paper A",
            papers,
            format_func=lambda x: x["title"]
        )

        p2 = st.selectbox(
            "Paper B",
            papers,
            format_func=lambda x: x["title"]
        )

        if st.button("Compare Papers"):

            prompt = f"""
Compare the following two research papers.

Paper A:
Title: {p1["title"]}
Abstract: {p1["summary"]}

Paper B:
Title: {p2["title"]}
Abstract: {p2["summary"]}

Compare them in terms of:
- research problem
- methodology
- strengths
- weaknesses
- contributions
"""

            with st.spinner("Analyzing papers..."):

                result = hf_query(prompt,120,240)

                st.markdown(f"""
                <div class="resultbox">
                <button class="copybtn" onclick="copyText('comparebox')">Copy</button>
                <div id="comparebox">{result}</div>
                </div>
                """,unsafe_allow_html=True)


# ================================================================
# TAB 4 — ADVANCED RESEARCH TOOLS
# ================================================================

with tab4:

    st.subheader("Advanced Research Toolkit")

    tool_tab1,tool_tab2,tool_tab3,tool_tab4,tool_tab5 = st.tabs([
        "💡 Research Ideas",
        "🔑 Keyword Analysis",
        "📊 Trend Analyzer",
        "🧪 Methodology Generator",
        "📂 Dataset Finder"
    ])

# ------------------------------------------------
# RESEARCH IDEA GENERATOR
# ------------------------------------------------

    with tool_tab1:

        topic = st.text_input("Research Topic for Idea Generation")

        if st.button("Generate Research Ideas") and topic:

            with st.spinner("Generating ideas..."):

                ideas = generate_research_idea(topic)

                st.markdown(f"""
                <div class="resultbox">
                <button class="copybtn" onclick="copyText('ideabox')">Copy</button>
                <div id="ideabox">{ideas}</div>
                </div>
                """,unsafe_allow_html=True)


# ------------------------------------------------
# KEYWORD EXTRACTION
# ------------------------------------------------

    with tool_tab2:

        text = st.text_area("Paste research abstract or text")

        if st.button("Extract Keywords") and text:

            kws = extract_keywords(text)

            st.write("### Top Keywords")

            for k in kws:
                st.write("•",k)


# ------------------------------------------------
# RESEARCH TREND ANALYZER
# ------------------------------------------------

    with tool_tab3:

        trend_topic = st.text_input("Trend Analysis Topic")

        if st.button("Analyze Trends") and trend_topic:

            prompt = f"""
Analyze emerging research trends in:

{trend_topic}

Discuss:
- current developments
- active research areas
- future opportunities
"""

            with st.spinner("Analyzing trends..."):

                trend = hf_query(prompt,120,240)

                st.markdown(f"""
                <div class="resultbox">
                <button class="copybtn" onclick="copyText('trendbox')">Copy</button>
                <div id="trendbox">{trend}</div>
                </div>
                """,unsafe_allow_html=True)


# ------------------------------------------------
# METHODOLOGY DESIGNER
# ------------------------------------------------

    with tool_tab4:

        m_topic = st.text_input("Research Topic for Methodology")

        if st.button("Generate Methodology") and m_topic:

            with st.spinner("Designing methodology..."):

                m = generate_methodology(m_topic)

                st.markdown(f"""
                <div class="resultbox">
                <button class="copybtn" onclick="copyText('methbox')">Copy</button>
                <div id="methbox">{m}</div>
                </div>
                """,unsafe_allow_html=True)


# ------------------------------------------------
# DATASET FINDER
# ------------------------------------------------

    with tool_tab5:

        d_topic = st.text_input("Dataset Topic")

        if st.button("Find Datasets") and d_topic:

            with st.spinner("Searching datasets..."):

                datasets = dataset_finder(d_topic)

                st.markdown(f"""
                <div class="resultbox">
                <button class="copybtn" onclick="copyText('datasetbox')">Copy</button>
                <div id="datasetbox">{datasets}</div>
                </div>
                """,unsafe_allow_html=True)


# ================================================================
# TAB 5 — AI RESEARCH ASSISTANT
# ================================================================

with tab5:

    st.subheader("AI Research Assistant")

    question = st.text_input("Ask a research question")

    if st.button("Ask") and question:

        prompt = f"""
You are an expert research assistant.

Answer the following scientific question clearly
and in academic tone:

{question}
"""

        with st.spinner("Thinking..."):

            answer = hf_query(prompt,120,240)

            st.session_state.chat_history.append(("user",question))
            st.session_state.chat_history.append(("ai",answer))

    for role,msg in st.session_state.chat_history:

        if role=="user":
            st.write("🧑‍💻",msg)
        else:
            st.write("🤖",msg)


# ================================================================
# TAB 6 — RESEARCH NOTES WORKSPACE
# ================================================================

with tab6:

    st.subheader("Research Notes")

    notes = st.text_area(
        "Write research notes here",
        value=st.session_state.notes,
        height=300
    )

    st.session_state.notes = notes

    if st.button("Save Notes"):

        st.success("Notes saved in session.")

# ================================================================
# ADVANCED RESEARCH ENGINES
# ================================================================

# ------------------------------------------------
# EXPERIMENT PLANNER
# ------------------------------------------------

def generate_experiment_plan(topic):

    prompt = f"""
Design a detailed experimental plan for research topic:

{topic}

Include:

- research hypothesis
- dataset selection
- preprocessing steps
- model training procedure
- evaluation metrics
- experiment validation
"""

    return hf_query(prompt,120,240)


# ------------------------------------------------
# IMPLEMENTATION GENERATOR
# ------------------------------------------------

def generate_code(topic):

    prompt = f"""
Generate example Python code for implementing
a machine learning research prototype for:

{topic}

Include:
- model architecture
- training pipeline
- evaluation
"""

    return hf_query(prompt,120,240)


# ------------------------------------------------
# BIBTEX GENERATOR
# ------------------------------------------------

def generate_bibtex(title,authors,year,pid):

    key = title.split(" ")[0] + year

    bib = f"""
@article{{{key},
  title={{ {title} }},
  author={{ {authors} }},
  year={{ {year} }},
  journal={{ arXiv }},
  url={{ https://arxiv.org/abs/{pid} }}
}}
"""

    return bib


# ------------------------------------------------
# RESEARCH GAP DETECTOR
# ------------------------------------------------

def detect_research_gaps(topic):

    prompt = f"""
Identify open research problems and research gaps in:

{topic}

Explain why these gaps exist and propose
potential directions for future work.
"""

    return hf_query(prompt,120,240)


# ------------------------------------------------
# SURVEY PAPER OUTLINE GENERATOR
# ------------------------------------------------

def generate_survey_outline(topic):

    prompt = f"""
Create a detailed outline for a survey paper on:

{topic}

Include:
- major sections
- subsections
- important themes
"""

    return hf_query(prompt,120,240)


# ------------------------------------------------
# RESEARCH PROPOSAL GENERATOR
# ------------------------------------------------

def generate_proposal(topic):

    prompt = f"""
Write a short academic research proposal for:

{topic}

Include:
- problem statement
- methodology
- expected contributions
"""

    return hf_query(prompt,120,240)


# ================================================================
# ADDITIONAL TOOL PANEL
# ================================================================

st.divider()

st.header("Advanced Research Lab")

lab1,lab2,lab3,lab4 = st.tabs([
"🧪 Experiment Planner",
"💻 Implementation Generator",
"📑 Citation Tools",
"🔍 Research Gap Analyzer"
])


# ------------------------------------------------
# EXPERIMENT DESIGN TOOL
# ------------------------------------------------

with lab1:

    topic = st.text_input("Experiment Topic")

    if st.button("Generate Experiment Plan") and topic:

        with st.spinner("Designing experiment..."):

            plan = generate_experiment_plan(topic)

            st.markdown(f"""
            <div class="resultbox">
            <button class="copybtn" onclick="copyText('expbox')">Copy</button>
            <div id="expbox">{plan}</div>
            </div>
            """,unsafe_allow_html=True)


# ------------------------------------------------
# IMPLEMENTATION GENERATOR
# ------------------------------------------------

with lab2:

    code_topic = st.text_input("Prototype Implementation Topic")

    if st.button("Generate Code Example") and code_topic:

        with st.spinner("Generating prototype code..."):

            code = generate_code(code_topic)

            st.markdown(f"""
            <div class="resultbox">
            <button class="copybtn" onclick="copyText('codebox')">Copy</button>
            <div id="codebox">{code}</div>
            </div>
            """,unsafe_allow_html=True)


# ------------------------------------------------
# BIBTEX GENERATOR
# ------------------------------------------------

with lab3:

    if st.session_state.papers:

        st.write("Generate BibTeX citation from discovered papers")

        selected = st.selectbox(
            "Select Paper",
            st.session_state.papers,
            format_func=lambda x: x["title"]
        )

        if st.button("Generate BibTeX"):

            bib = generate_bibtex(
                selected["title"],
                selected["authors"],
                selected["year"],
                selected["id"]
            )

            st.markdown(f"""
            <div class="resultbox">
            <button class="copybtn" onclick="copyText('bibbox')">Copy</button>
            <div id="bibbox">{bib}</div>
            </div>
            """,unsafe_allow_html=True)


# ------------------------------------------------
# RESEARCH GAP ANALYZER
# ------------------------------------------------

with lab4:

    gap_topic = st.text_input("Research Topic")

    if st.button("Detect Research Gaps") and gap_topic:

        with st.spinner("Analyzing literature gaps..."):

            gaps = detect_research_gaps(gap_topic)

            st.markdown(f"""
            <div class="resultbox">
            <button class="copybtn" onclick="copyText('gapbox')">Copy</button>
            <div id="gapbox">{gaps}</div>
            </div>
            """,unsafe_allow_html=True)


# ================================================================
# SURVEY PAPER BUILDER
# ================================================================

st.divider()

st.header("Survey Paper Builder")

survey_topic = st.text_input("Survey Topic")

col1,col2 = st.columns(2)

with col1:

    if st.button("Generate Survey Outline") and survey_topic:

        outline = generate_survey_outline(survey_topic)

        st.markdown(f"""
        <div class="resultbox">
        <button class="copybtn" onclick="copyText('outlinebox')">Copy</button>
        <div id="outlinebox">{outline}</div>
        </div>
        """,unsafe_allow_html=True)

with col2:

    if st.button("Generate Research Proposal") and survey_topic:

        proposal = generate_proposal(survey_topic)

        st.markdown(f"""
        <div class="resultbox">
        <button class="copybtn" onclick="copyText('proposalbox')">Copy</button>
        <div id="proposalbox">{proposal}</div>
        </div>
        """,unsafe_allow_html=True)


# ================================================================
# FOOTER
# ================================================================

st.divider()

st.markdown(
f"""
<div style="text-align:center;color:#8b949e;padding:30px">

AI Research Agent Platform<br>

Developed by <b>Muhammad Zaid Suhail</b><br>

Electrical Engineer | Applied AI Engineer<br>

{datetime.now().year}

</div>
""",
unsafe_allow_html=True
)
