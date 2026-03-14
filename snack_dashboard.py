import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

# ── CONFIG ────────────────────────────────────────────────────────────────────

SHEET_ID = "1IX4irbd_vgWQMpYdmA_GIDZJgIt57L-1PzQtqcPqjo4"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

SNACK_NAMES_SHEET_ID = "1d2R96_8rIBUOm-qo20OeF1ZiKPGGcnrORfHzDmxDR-4"
SNACK_NAMES_URL = f"https://docs.google.com/spreadsheets/d/{SNACK_NAMES_SHEET_ID}/export?format=csv"

COL_NAME         = "What is your name? (Please use the same name for all ratings)"
COL_SNACK        = "Which snack are you rating? (Insert snack ID)"
COL_FLAVOUR      = "How would you rate the FLAVOUR of this snack?"
COL_TEXTURE      = "How would you rate the TEXTURE of this snack?"
COL_SNACKABILITY = "How would you rate the SNACKABILITY of this snack?"
COL_ORIGINALITY  = "How would you rate the ORIGINALITY of this snack?"

COL_SNACK_NAME      = "What is your snack called?"
COL_SNACK_ID_LOOKUP = "Snack ID:"

RATING_COLS   = [COL_FLAVOUR, COL_TEXTURE, COL_SNACKABILITY, COL_ORIGINALITY]
RATING_LABELS = ["Flavour", "Texture", "Snackability", "Originality"]

# Preferred categories for Snack Matches agreement
PREFERRED_CATS = ["Flavour", "Texture", "Snackability", "Originality"]

# ── PAGE SETUP ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="🍿 Snack Ratings", layout="centered")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Roboto+Mono:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Roboto Mono', monospace !important;
        background-color: #bbdcbe !important;
    }
    .stApp {
        background-color: #bbdcbe !important;
    }
    h1, h2, h3, h4 {
        font-family: 'Roboto Mono', monospace !important;
    }
    .snack-card {
        background-color: #ffffff55;
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        font-family: 'Roboto Mono', monospace;
    }
    .snack-card .rank {
        font-size: 0.75rem;
        color: #555;
        margin-bottom: 2px;
    }
    .snack-card .name {
        font-size: 1rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .snack-card .stars {
        font-size: 1.1rem;
        letter-spacing: 2px;
    }
    .snack-card .score {
        font-size: 0.8rem;
        color: #444;
    }
    .match-box {
        background-color: #ffffff55;
        border-radius: 12px;
        padding: 18px 20px;
        font-family: 'Roboto Mono', monospace;
        font-size: 1rem;
        line-height: 1.7;
    }
    .section-label {
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        color: #444;
        margin-bottom: 6px;
        font-family: 'Roboto Mono', monospace;
    }
    div[data-testid="stSelectbox"] label {
        font-family: 'Roboto Mono', monospace !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("🍿 Snack Ratings")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(subset=[COL_NAME, COL_SNACK] + RATING_COLS)
    df[COL_NAME] = df[COL_NAME].astype(str).str.strip()
    for col in RATING_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=RATING_COLS)
    return df

@st.cache_data(ttl=60)
def load_snack_names():
    names_df = pd.read_csv(SNACK_NAMES_URL)
    names_df[COL_SNACK_ID_LOOKUP] = names_df[COL_SNACK_ID_LOOKUP].apply(lambda x: str(int(float(x))).strip() if str(x).replace('.','',1).isdigit() else str(x).strip()).str.lstrip("0")
    names_df[COL_SNACK_NAME]      = names_df[COL_SNACK_NAME].astype(str).str.strip()
    return dict(zip(names_df[COL_SNACK_ID_LOOKUP], names_df[COL_SNACK_NAME]))

def snack_label(snack_id, snack_names):
    try:
        key = str(int(float(snack_id))).strip()
    except (ValueError, TypeError):
        key = str(snack_id).strip()
    name = snack_names.get(key)
    return f"{name}" if name else str(snack_id)


try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load ratings sheet.\n\nError: {e}")
    st.stop()

try:
    snack_names = load_snack_names()
except Exception as e:
    st.warning(f"Could not load snack names — showing IDs.\n\nError: {e}")
    snack_names = {}

def clean_id(val):
    try:
        return str(int(float(val))).strip()
    except (ValueError, TypeError):
        return str(val).strip()

df["Snack Label"] = df[COL_SNACK].map(lambda x: snack_label(clean_id(x), snack_names))

if st.button("🔄 Refresh"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ── 1. TOP SNACKS ─────────────────────────────────────────────────────────────

st.header("🏆 Top Snacks")

snack_avgs = (
    df.groupby("Snack Label")[RATING_COLS]
    .mean()
    .round(2)
    .reset_index()
)
snack_avgs.columns = ["Snack"] + RATING_LABELS

category_col_map = {
    "Flavour":      COL_FLAVOUR,
    "Texture":      COL_TEXTURE,
    "Snackability": COL_SNACKABILITY,
    "Originality":  COL_ORIGINALITY,
}

MEDALS = ["🥇", "🥈", "🥉"]

for label in RATING_LABELS:
    st.markdown(f"<div class='section-label'>The top snacks in the category <span style='font-size:1.1rem; font-weight:700; color:#222; text-transform:none; letter-spacing:0;'>{label}</span> are:</div>", unsafe_allow_html=True)
    top3 = snack_avgs.nlargest(3, label)[["Snack", label]].reset_index(drop=True)
    for i, row in top3.iterrows():
        st.markdown(f"""
        <div class="snack-card">
            <div class="rank">{MEDALS[i]} #{i+1}</div>
            <div class="name">{row['Snack']}</div>
            <div class="score">{row[label]:.1f} / 6</div>
        </div>
        """, unsafe_allow_html=True)
    st.write("")

st.divider()

# ── 2. SNACK MATCHES ──────────────────────────────────────────────────────────

st.header("🤝 Snack Matches")

if df[COL_NAME].nunique() < 2:
    st.info("Need at least 2 people to calculate taste similarity.")
else:
    # Build person × snack matrix for similarity
    person_snack = (
        df.groupby([COL_NAME, "Snack Label"])[RATING_COLS]
        .mean()
        .mean(axis=1)
        .unstack("Snack Label")
        .fillna(df[RATING_COLS].stack().mean())
    )

    people = person_snack.index.tolist()

    dist_values = cdist(person_snack.values, person_snack.values, metric="cityblock") / person_snack.shape[1]
    dist_matrix = pd.DataFrame(dist_values, index=people, columns=people)
    dist_matrix_copy = dist_matrix.values.copy()
    np.fill_diagonal(dist_matrix_copy, np.nan)
    dist_matrix = pd.DataFrame(dist_matrix_copy, index=people, columns=people)

    selected_person = st.selectbox("Select a person", sorted(people))

    most_similar_name  = dist_matrix.loc[selected_person].idxmin()
    most_similar_score = round(dist_matrix.loc[selected_person].min(), 2)
    least_similar_name = dist_matrix.loc[selected_person].idxmax()
    least_similar_score = round(dist_matrix.loc[selected_person].max(), 2)

    # ── Find shared agreements ────────────────────────────────────────────────
    # Per-person, per-snack, per-category averages
    person_detail = (
        df.groupby([COL_NAME, "Snack Label"])[RATING_COLS]
        .mean()
        .round(2)
    )
    person_detail.columns = RATING_LABELS

    # Find snacks rated by both people
    try:
        p1_data = person_detail.loc[selected_person]
        p2_data = person_detail.loc[most_similar_name]
        shared_snacks = p1_data.index.intersection(p2_data.index)

        agreement_sentences = []

        if len(shared_snacks) > 0:
            # Try preferred categories first (Flavour, Texture), then fall back
            found_cats = []
            for cat in PREFERRED_CATS:
                if len(found_cats) == 2:
                    break
                best_snack = None
                best_avg = -1
                for snack in shared_snacks:
                    r1 = p1_data.loc[snack, cat]
                    r2 = p2_data.loc[snack, cat]
                    # Must be within 1 star of each other AND average >= 4
                    if abs(r1 - r2) <= 1:
                        avg = (r1 + r2) / 2
                        if avg >= 4 and avg > best_avg:
                            best_avg = avg
                            best_snack = snack
                if best_snack:
                    found_cats.append((cat, best_snack, round(best_avg, 1)))

            for cat, snack, avg in found_cats:
                r1 = round(p1_data.loc[snack, cat])
                r2 = round(p2_data.loc[snack, cat])
                agreement_sentences.append(
                    f"You both really liked the <b>{cat.lower()}</b> of <b>{snack}</b> "
                    f"({selected_person}: {r1}, {most_similar_name}: {r2})"
                )
    except KeyError:
        agreement_sentences = []

    # ── Render match box ─────────────────────────────────────────────────────
    agreement_html = ""
    if agreement_sentences:
        agreement_html = "<br>" + "<br>".join(agreement_sentences)

    st.markdown(f"""
    <div class="match-box">
        <b>{selected_person}'s</b> taste is most similar to <b>{most_similar_name}'s</b>
        with a similarity score of <b>{most_similar_score}</b>
        and least similar to <b>{least_similar_name}'s</b>
        with a similarity score of <b>{least_similar_score}</b>.
        {agreement_html}
    </div>
    """, unsafe_allow_html=True)
