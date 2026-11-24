"""GenTrust AI - Generative AI hallucination & reliability assessment."""

import os

import streamlit as st
from dotenv import load_dotenv

from modules import ui
from modules.llm import DEFAULT_MODEL, MODEL_CHOICES, LLMError, chat, make_client
from modules.pipeline import MAX_ANSWER_CHARS, run_analysis
from modules.views import render_report

load_dotenv()

st.set_page_config(
    page_title="GenTrust AI · Hallucination & Reliability Checker",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)
ui.inject_css()

EXAMPLES = {
    "🧪 Science facts": (
        "Albert Einstein was born in Ulm, Germany in 1879. He received the Nobel Prize in "
        "Physics in 1925 for his theory of relativity. Einstein published his special theory "
        "of relativity in 1905 while working at the Swiss Patent Office in Bern. The speed of "
        "light in a vacuum is approximately 299,792 kilometres per second.\n\n"
        "References\n"
        "10.9999/ai.hallucination.2023.042\n"
        "LeCun, Bengio & Hinton (2015). Deep learning. Nature. https://doi.org/10.1038/nature14539"
    ),
    "🌍 Space & geography": (
        "The Apollo 11 mission landed the first humans on the Moon in July 1969. The Great Wall "
        "of China is easily visible from the Moon with the naked eye. Mount Everest, at 8,849 "
        "metres, is the highest mountain above sea level. The Amazon is the longest river in the "
        "world, flowing through Brazil and Peru."
    ),
    "🩺 Health myths": (
        "Humans use only 10 percent of their brains. Vitamin C reliably cures the common cold. "
        "The human body has 206 bones in adulthood. Antibiotics are effective against viral "
        "infections such as influenza."
    ),
}


def load_example(text):
    st.session_state["answer_text"] = text
    st.session_state.pop("analysis_result", None)


def clear_text():
    st.session_state["answer_text"] = ""
    st.session_state.pop("analysis_result", None)


# ------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------

env_key = os.getenv("GROQ_API_KEY", "").strip().strip('"').strip("'")
if env_key.lower().startswith("your_") or env_key.lower() in ("", "paste_your_key_here"):
    env_key = ""

with st.sidebar:
    ui.render("""
    <div class="gt-side-brand"><div class="gt-mark">🛡️</div>
    <div><div class="gt-side-title">GenTrust AI</div>
    <div class="gt-side-sub">Reliability assessment</div></div></div>
    """)

    ui.render('<div class="gt-section-label">Connection</div>')
    if env_key:
        api_key = env_key
        ui.render(ui.chip("API key loaded", "good"))
    else:
        api_key = st.text_input(
            "Groq API key",
            type="password",
            placeholder="gsk_…",
            help="Get a free key at console.groq.com/keys. To save it permanently, put it in the .env file.",
            key="manual_key",
        ).strip()

    default_model = os.getenv("GROQ_MODEL", "").strip() or DEFAULT_MODEL
    choices = MODEL_CHOICES.copy()
    if default_model not in choices:
        choices.insert(0, default_model)
    choices.append("Custom…")

    picked = st.selectbox("AI model", choices, index=choices.index(default_model))
    if picked == "Custom…":
        model = st.text_input("Custom model ID", placeholder="e.g. llama-3.3-70b-versatile").strip()
    else:
        model = picked

    if st.button("Test connection"):
        if not api_key:
            st.error("Add your Groq API key first.")
        elif not model:
            st.error("Enter a model ID.")
        else:
            try:
                with st.spinner("Contacting Groq…"):
                    chat(make_client(api_key), model, [{"role": "user", "content": "Reply with the word OK."}], max_tokens=20, retries=1)
                st.success("Connected and working.")
            except LLMError as exc:
                st.error(str(exc))
            except Exception as exc:  # noqa: BLE001
                st.error(f"Connection failed: {exc}")

    ui.render('<div class="gt-section-label">Analysis depth</div>')
    max_claims = st.slider("Claims to fact-check", 3, 15, 8, help="More claims = more thorough, but slower.")
    run_consistency = st.toggle("Consistency test", value=True, help="Re-asks the model the same questions several times.")
    num_questions = 3
    if run_consistency:
        num_questions = st.slider("Consistency questions", 1, 5, 3)
    run_citations = st.toggle("Citation check", value=True, help="Looks up DOIs, links and references.")

    st.write("")
    with st.expander("How the score works"):
        st.markdown(
            """
**Overall trust** blends three checks:

- **Factual accuracy (60%)**: supported claims count fully, unverifiable claims half, contradicted claims zero.
- **Consistency (25%)**: how stable the model's answers are when re-asked.
- **Citations (15%)**: whether references actually exist.

Checks that are switched off or find nothing are left out and the rest are re-weighted.
            """
        )

# ------------------------------------------------------------------
# Header + input
# ------------------------------------------------------------------

ui.hero()

ui.section_title("Paste an AI-generated answer", "From ChatGPT, Claude, Gemini, Copilot or any other assistant.")

answer = st.text_area(
    "AI answer",
    key="answer_text",
    height=240,
    label_visibility="collapsed",
    placeholder="Paste the complete AI-generated response here…",
)

length = len(answer.strip())
if length > MAX_ANSWER_CHARS:
    st.caption(f"{length:,} characters · only the first {MAX_ANSWER_CHARS:,} will be analysed.")
else:
    st.caption(f"{length:,} / {MAX_ANSWER_CHARS:,} characters")

ui.render('<div class="gt-section-label">No text handy? Try an example</div>')
cols = st.columns(len(EXAMPLES) + 1)
for col, (name, text) in zip(cols, EXAMPLES.items()):
    col.button(name, key=f"ex_{name}", on_click=load_example, args=(text,))
cols[-1].button("🧹 Clear", key="clear", on_click=clear_text)

st.write("")
analyse = st.button("🔍  Analyse reliability", type="primary")

# ------------------------------------------------------------------
# Run analysis
# ------------------------------------------------------------------

if analyse:
    if length < 20:
        st.warning("Please paste a longer AI-generated answer (at least a sentence or two).")
    elif not api_key:
        st.error("Add your Groq API key in the sidebar, or put it in the .env file, then try again.")
    elif not model:
        st.error("Please choose or enter an AI model in the sidebar.")
    else:
        st.session_state.pop("analysis_result", None)

        with st.status("Analysing your answer…", expanded=True) as status:
            bar = st.progress(0.0)
            message = st.empty()

            def on_progress(fraction, text):
                bar.progress(fraction)
                message.markdown(f"**{text}**")

            try:
                result = run_analysis(
                    make_client(api_key),
                    model,
                    answer,
                    {
                        "max_claims": max_claims,
                        "num_questions": num_questions,
                        "run_consistency": run_consistency,
                        "run_citations": run_citations,
                    },
                    on_progress,
                )
                st.session_state["analysis_result"] = result
                status.update(label="Analysis complete", state="complete", expanded=False)
            except LLMError as exc:
                status.update(label="Analysis stopped", state="error", expanded=True)
                st.error(str(exc))
            except Exception as exc:  # noqa: BLE001
                status.update(label="Analysis stopped", state="error", expanded=True)
                st.error(f"Something went wrong: {exc}")

# ------------------------------------------------------------------
# Report or onboarding
# ------------------------------------------------------------------

if "analysis_result" in st.session_state:
    render_report(st.session_state["analysis_result"])
else:
    ui.how_it_works()

ui.footer()
