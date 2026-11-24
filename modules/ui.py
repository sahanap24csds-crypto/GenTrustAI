"""Visual layer: theme CSS and small HTML components."""

import html

import streamlit as st

TONES = {
    "good": "#34d399",
    "warn": "#fbbf24",
    "bad": "#fb7185",
    "muted": "#94a3b8",
    "brand": "#7c83ff",
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

:root {
  --bg: #0a0f1f;
  --surface: #111936;
  --surface-2: #17214a;
  --border: rgba(148, 163, 255, 0.16);
  --text: #e8ecff;
  --muted: #9aa5d1;
  --primary: #7c83ff;
  --accent: #22d3ee;
  --good: #34d399;
  --warn: #fbbf24;
  --bad: #fb7185;
}

html, body, .stApp, [class*="css"] {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}

.stApp {
  background:
    radial-gradient(1100px 560px at 8% -10%, rgba(124, 131, 255, 0.20), transparent 60%),
    radial-gradient(900px 520px at 100% 0%, rgba(34, 211, 238, 0.13), transparent 55%),
    var(--bg);
  color: var(--text);
}

#MainMenu, footer { visibility: hidden; }
header[data-testid="stHeader"] { background: transparent; }

.block-container {
  max-width: 1120px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}

h1, h2, h3, h4 { letter-spacing: -0.02em; }

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0e1530 0%, #0a0f1f 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

.gt-side-brand {
  display: flex; align-items: center; gap: 0.7rem; margin-bottom: 0.4rem;
}
.gt-side-brand .gt-mark { width: 38px; height: 38px; font-size: 1.1rem; border-radius: 11px; }
.gt-side-title { font-weight: 800; font-size: 1.15rem; line-height: 1.1; }
.gt-side-sub { color: var(--muted); font-size: 0.75rem; }

.gt-section-label {
  text-transform: uppercase; letter-spacing: 0.12em; font-size: 0.68rem;
  color: var(--muted); font-weight: 700; margin: 1.2rem 0 0.4rem;
}

/* ---------- Hero ---------- */
.gt-hero {
  position: relative; padding: 2.2rem 2.2rem 2rem; border-radius: 24px;
  border: 1px solid var(--border); overflow: hidden; margin-bottom: 1.6rem;
  background:
    linear-gradient(135deg, rgba(124, 131, 255, 0.16), rgba(34, 211, 238, 0.07)),
    var(--surface);
  animation: gt-rise 0.6s ease both;
}
.gt-hero::after {
  content: ""; position: absolute; width: 340px; height: 340px; right: -90px; top: -120px;
  background: radial-gradient(circle, rgba(124, 131, 255, 0.35), transparent 65%);
  pointer-events: none;
}
.gt-brandrow { display: flex; align-items: center; gap: 1rem; position: relative; z-index: 1; }
.gt-mark {
  width: 56px; height: 56px; border-radius: 16px; display: grid; place-items: center;
  font-size: 1.7rem; color: #fff; flex-shrink: 0;
  background: linear-gradient(135deg, #7c83ff, #22d3ee);
  box-shadow: 0 10px 30px rgba(124, 131, 255, 0.4);
}
.gt-title {
  font-size: 2.3rem; font-weight: 800; line-height: 1.05; margin: 0;
  background: linear-gradient(90deg, #ffffff, #b9c0ff 60%, #8be9f9);
  -webkit-background-clip: text; background-clip: text; color: transparent;
}
.gt-tagline { color: var(--muted); font-size: 1.02rem; margin: 0.9rem 0 0; max-width: 640px; position: relative; z-index: 1; }
.gt-badges { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1.2rem; position: relative; z-index: 1; }
.gt-badge {
  font-size: 0.78rem; font-weight: 600; padding: 0.38rem 0.8rem; border-radius: 999px;
  border: 1px solid var(--border); background: rgba(255, 255, 255, 0.04); color: #cfd5ff;
}

/* ---------- Cards ---------- */
.gt-card {
  background: var(--surface); border: 1px solid var(--border); border-radius: 20px;
  padding: 1.3rem 1.4rem; animation: gt-rise 0.5s ease both;
}
.gt-card h4 { margin: 0 0 0.3rem; font-size: 1rem; }
.gt-card p { margin: 0; color: var(--muted); font-size: 0.9rem; line-height: 1.55; }

.gt-steps { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 1rem; margin: 0.4rem 0 1rem; }
.gt-step-num {
  width: 34px; height: 34px; border-radius: 10px; display: grid; place-items: center;
  font-weight: 800; margin-bottom: 0.8rem; color: #fff;
  background: linear-gradient(135deg, #7c83ff, #22d3ee);
}

.gt-section-title {
  font-size: 1.25rem; font-weight: 700; margin: 1.6rem 0 0.2rem;
}
.gt-section-sub { color: var(--muted); font-size: 0.9rem; margin-bottom: 0.9rem; }

/* ---------- Gauge ---------- */
.gt-gauge-wrap { display: flex; flex-direction: column; align-items: center; gap: 1rem; text-align: center; }
.gt-gauge {
  --p: 0; --c: #34d399;
  width: 190px; height: 190px; border-radius: 50%; position: relative; display: grid; place-items: center;
  background: conic-gradient(var(--c) calc(var(--p) * 1%), rgba(255, 255, 255, 0.08) 0);
  box-shadow: 0 0 70px color-mix(in srgb, var(--c) 28%, transparent);
}
.gt-gauge::before { content: ""; position: absolute; inset: 15px; border-radius: 50%; background: var(--surface); }
.gt-gauge-inner { position: relative; text-align: center; }
.gt-gauge-num { font-size: 3.1rem; font-weight: 800; line-height: 1; }
.gt-gauge-num small { font-size: 1.2rem; font-weight: 600; color: var(--muted); }
.gt-gauge-sub { font-size: 0.68rem; color: var(--muted); letter-spacing: 0.12em; text-transform: uppercase; margin-top: 0.3rem; }
.gt-gauge.sm { width: 120px; height: 120px; }
.gt-gauge.sm::before { inset: 11px; }
.gt-gauge.sm .gt-gauge-num { font-size: 2rem; }
.gt-gauge.sm .gt-gauge-num small { font-size: 0.9rem; }

.gt-verdict-label { font-size: 1.35rem; font-weight: 800; }
.gt-verdict-msg { color: var(--muted); font-size: 0.92rem; max-width: 330px; line-height: 1.5; }

/* ---------- Chips, bars, stats ---------- */
.gt-chip {
  display: inline-flex; align-items: center; gap: 0.35rem; font-size: 0.72rem; font-weight: 700;
  letter-spacing: 0.04em; text-transform: uppercase; padding: 0.28rem 0.7rem; border-radius: 999px;
  border: 1px solid transparent; white-space: nowrap;
}
.gt-chip.good { color: var(--good); background: rgba(52, 211, 153, 0.12); border-color: rgba(52, 211, 153, 0.3); }
.gt-chip.warn { color: var(--warn); background: rgba(251, 191, 36, 0.12); border-color: rgba(251, 191, 36, 0.3); }
.gt-chip.bad { color: var(--bad); background: rgba(251, 113, 133, 0.12); border-color: rgba(251, 113, 133, 0.3); }
.gt-chip.muted { color: #94a3b8; background: rgba(148, 163, 184, 0.12); border-color: rgba(148, 163, 184, 0.28); }

.gt-stat { background: var(--surface); border: 1px solid var(--border); border-radius: 18px; padding: 1.1rem 1.2rem; animation: gt-rise 0.5s ease both; }
.gt-stat-label { color: var(--muted); font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700; }
.gt-stat-value { font-size: 2rem; font-weight: 800; margin: 0.25rem 0 0.1rem; }
.gt-stat-hint { color: var(--muted); font-size: 0.8rem; }

.gt-bar { height: 7px; border-radius: 99px; background: rgba(255, 255, 255, 0.08); overflow: hidden; margin-top: 0.7rem; }
.gt-bar > span { display: block; height: 100%; border-radius: 99px; }

.gt-finding {
  display: flex; gap: 0.7rem; align-items: flex-start; padding: 0.8rem 1rem; border-radius: 14px;
  background: var(--surface); border: 1px solid var(--border); margin-bottom: 0.55rem; font-size: 0.93rem;
}
.gt-dot { width: 9px; height: 9px; border-radius: 50%; margin-top: 0.45rem; flex-shrink: 0; }

.gt-claim-head { display: flex; gap: 0.8rem; align-items: flex-start; justify-content: space-between; }
.gt-claim-text { font-size: 1rem; font-weight: 500; line-height: 1.5; }
.gt-claim-num { color: var(--muted); font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.1em; margin-bottom: 0.2rem; }
.gt-reason { color: #c4cbf0; font-size: 0.92rem; line-height: 1.6; margin-top: 0.6rem; }
.gt-meta { color: var(--muted); font-size: 0.8rem; margin-top: 0.5rem; }

.gt-note {
  border-left: 3px solid var(--primary); background: rgba(124, 131, 255, 0.08);
  padding: 0.8rem 1rem; border-radius: 0 12px 12px 0; color: #c4cbf0; font-size: 0.85rem; line-height: 1.55; margin-top: 1rem;
}
.gt-footer { text-align: center; color: var(--muted); font-size: 0.78rem; margin-top: 3rem; }

/* ---------- Streamlit widget polish ---------- */
.stButton > button, .stDownloadButton > button {
  width: 100%; border-radius: 14px; font-weight: 600; padding: 0.65rem 1rem;
  border: 1px solid var(--border); background: var(--surface-2); color: var(--text);
  transition: transform 0.15s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
  border-color: var(--primary); transform: translateY(-1px); color: #fff;
}
.stButton > button[kind="primary"] {
  border: none; color: #fff; font-size: 1.05rem; padding: 0.85rem 1rem;
  background: linear-gradient(135deg, #6c74ff 0%, #22b8e8 100%);
  box-shadow: 0 10px 30px rgba(108, 116, 255, 0.35);
}
.stButton > button[kind="primary"]:hover { box-shadow: 0 14px 38px rgba(108, 116, 255, 0.5); transform: translateY(-2px); }

[data-testid="stTextArea"] textarea {
  background: var(--surface); border: 1px solid var(--border); border-radius: 16px;
  font-size: 0.98rem; line-height: 1.6; padding: 1rem 1.1rem;
}
[data-testid="stTextArea"] textarea:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(124, 131, 255, 0.25); }
[data-testid="stTextInput"] input { border-radius: 12px; }

.stTabs [data-baseweb="tab-list"] { gap: 0.3rem; border-bottom: 1px solid var(--border); }
.stTabs [data-baseweb="tab"] { border-radius: 12px 12px 0 0; padding: 0.7rem 1.1rem; font-weight: 600; color: var(--muted); }
.stTabs [aria-selected="true"] { color: #fff; }
.stTabs [data-baseweb="tab-highlight"] { background: linear-gradient(90deg, #7c83ff, #22d3ee); height: 3px; border-radius: 3px; }

[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 14px; background: rgba(255, 255, 255, 0.02); }
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"] .gt-claim-head) { border-radius: 18px; }
[data-testid="stStatus"] { border-radius: 16px; border: 1px solid var(--border); background: var(--surface); }

@keyframes gt-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
@media (max-width: 700px) {
  .gt-title { font-size: 1.7rem; }
  .gt-hero { padding: 1.5rem 1.2rem; }
}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def esc(value):
    return html.escape(str(value), quote=True)


def render(markup):
    """Render HTML safely through Streamlit's markdown (no indentation/blank lines)."""
    flattened = " ".join(line.strip() for line in markup.strip().splitlines())
    st.markdown(flattened, unsafe_allow_html=True)


def color(tone):
    return TONES.get(tone, TONES["muted"])


# ------------------------------------------------------------------
# Components
# ------------------------------------------------------------------

def hero():
    render("""
    <div class="gt-hero">
      <div class="gt-brandrow">
        <div class="gt-mark">🛡️</div>
        <h1 class="gt-title">GenTrust AI</h1>
      </div>
      <p class="gt-tagline">Know what to trust in AI-generated text. Paste any answer and get an
      evidence-based reliability report in under a minute.</p>
      <div class="gt-badges">
        <span class="gt-badge">🔎 Fact-checked against the web</span>
        <span class="gt-badge">🔁 Self-consistency tested</span>
        <span class="gt-badge">📚 Citations verified</span>
      </div>
    </div>
    """)


def how_it_works():
    render("""
    <div class="gt-steps">
      <div class="gt-card"><div class="gt-step-num">1</div><h4>Paste an answer</h4>
        <p>Drop in any text from ChatGPT, Claude, Gemini or another AI.</p></div>
      <div class="gt-card"><div class="gt-step-num">2</div><h4>We investigate</h4>
        <p>Claims are fact-checked, the model is re-asked, and citations are looked up.</p></div>
      <div class="gt-card"><div class="gt-step-num">3</div><h4>See the evidence</h4>
        <p>Get a clear score, plain-language findings, and the sources behind every verdict.</p></div>
    </div>
    """)


def section_title(title, subtitle=""):
    sub = f'<div class="gt-section-sub">{esc(subtitle)}</div>' if subtitle else ""
    render(f'<div class="gt-section-title">{esc(title)}</div>{sub}')


def chip(text, tone="muted"):
    return f'<span class="gt-chip {tone}">{esc(text)}</span>'


def gauge(score, tone, caption="Trust score", small=False):
    value = 0 if score is None else int(score)
    shown = "–" if score is None else f"{value}<small>%</small>"
    size = " sm" if small else ""
    return (
        f'<div class="gt-gauge{size}" style="--p:{value};--c:{color(tone)}">'
        f'<div class="gt-gauge-inner"><div class="gt-gauge-num">{shown}</div>'
        f'<div class="gt-gauge-sub">{esc(caption)}</div></div></div>'
    )


def tone_for_score(score):
    if score is None:
        return "muted"
    if score >= 70:
        return "good"
    if score >= 50:
        return "warn"
    return "bad"


def stat_card(label, value, hint="", score=None):
    tone = tone_for_score(score)
    bar = ""
    if score is not None:
        bar = f'<div class="gt-bar"><span style="width:{int(score)}%;background:{color(tone)}"></span></div>'
    return (
        f'<div class="gt-stat"><div class="gt-stat-label">{esc(label)}</div>'
        f'<div class="gt-stat-value">{value}</div>'
        f'<div class="gt-stat-hint">{esc(hint)}</div>{bar}</div>'
    )


def finding(text, tone):
    return (
        f'<div class="gt-finding"><span class="gt-dot" style="background:{color(tone)}"></span>'
        f'<span>{esc(text)}</span></div>'
    )


def footer():
    render('<div class="gt-footer">GenTrust AI · Automated checks reduce risk but never replace human judgement.</div>')
