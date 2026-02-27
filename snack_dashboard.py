import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

# ── CONFIG ────────────────────────────────────────────────────────────────────

SHEET_ID = "1IX4irbd_vgWQMpYdmA_GIDZJgIt57L-1PzQtqcPqjo4"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

SNACK_NAMES_SHEET_ID = "1d2R96_8rIBUOm-qo20OeF1ZiKPGGcnrORfHzDmxDR-4"
SNACK_NAMES_URL = f"https://docs.google.com/spreadsheets/d/{SNACK_NAMES_SHEET_ID}/export?format=csv"

# Ratings sheet columns
COL_NAME         = "What is your name? (Please use the same name for all ratings)"
COL_SNACK        = "Which snack are you rating? (Insert snack ID)"
COL_FLAVOUR      = "How would you rate the FLAVOUR of this snack?"
COL_TEXTURE      = "How would you rate the TEXTURE of this snack?"
COL_SNACKABILITY = "How would you rate the SNACKABILITY of this snack?"
COL_ORIGINALITY  = "How would you rate the ORIGINALITY of this snack?"

# Snack names sheet columns
COL_SNACK_NAME      = "What is your snack called?"
COL_SNACK_ID_LOOKUP = "Snack ID:"

RATING_COLS   = [COL_FLAVOUR, COL_TEXTURE, COL_SNACKABILITY, COL_ORIGINALITY]
RATING_LABELS = ["Flavour", "Texture", "Snackability", "Originality"]

# ── PAGE SETUP ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="🍿 Snack Ratings", layout="wide")
st.title("🍿 Snack Rating Dashboard")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_data():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(subset=[COL_NAME, COL_SNACK] + RATING_COLS)
    for col in RATING_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=RATING_COLS)
    return df

@st.cache_data(ttl=60)
def load_snack_names():
    names_df = pd.read_csv(SNACK_NAMES_URL)
    names_df[COL_SNACK_ID_LOOKUP] = names_df[COL_SNACK_ID_LOOKUP].astype(str).str.strip()
    names_df[COL_SNACK_NAME]      = names_df[COL_SNACK_NAME].astype(str).str.strip()
    return dict(zip(names_df[COL_SNACK_ID_LOOKUP], names_df[COL_SNACK_NAME]))

def snack_label(snack_id, snack_names):
    name = snack_names.get(str(snack_id).strip())
    return f"{name} ({snack_id})" if name else str(snack_id)

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load ratings sheet. Make sure it is set to 'Anyone with the link can view'.\n\nError: {e}")
    st.stop()

try:
    snack_names = load_snack_names()
except Exception as e:
    st.warning(f"Could not load snack names sheet — showing IDs only.\n\nError: {e}")
    snack_names = {}

df["Snack Label"] = df[COL_SNACK].astype(str).map(lambda x: snack_label(x, snack_names))

st.caption(f"Loaded {len(df)} ratings from {df[COL_NAME].nunique()} people across {df[COL_SNACK].nunique()} snacks.")

if st.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ── 1. SNACK AVERAGES ─────────────────────────────────────────────────────────

st.header("📊 Snack Averages")

snack_avgs = (
    df.groupby("Snack Label")[RATING_COLS]
    .mean()
    .round(2)
    .reset_index()
)
snack_avgs.columns = ["Snack"] + RATING_LABELS
snack_avgs["Combined Average"] = snack_avgs[RATING_LABELS].mean(axis=1).round(2)
snack_avgs = snack_avgs.sort_values("Combined Average", ascending=False).reset_index(drop=True)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("Ratings by category")
    st.dataframe(snack_avgs, use_container_width=True, hide_index=True)

with col2:
    st.subheader("Combined average")
    st.bar_chart(
        snack_avgs.set_index("Snack")["Combined Average"],
        use_container_width=True
    )

st.divider()

# ── 2. SNACK MATCHES ──────────────────────────────────────────────────────────

st.header("🤝 Snack Matches")

if df[COL_NAME].nunique() < 2:
    st.info("Need at least 2 people to calculate taste similarity.")
else:
    # Build person × snack matrix
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
    least_similar_name  = dist_matrix.loc[selected_person].idxmax()
    least_similar_score = round(dist_matrix.loc[selected_person].max(), 2)

    st.markdown(
        f"**{selected_person}'s** taste is most similar to **{most_similar_name}'s** "
        f"with a similarity score of **{most_similar_score}** "
        f"and least similar to **{least_similar_name}'s** "
        f"with a similarity score of **{least_similar_score}**."
    )
