import streamlit as st
import pandas as pd
import numpy as np
from scipy.spatial.distance import cdist

# ── CONFIG ────────────────────────────────────────────────────────────────────

SHEET_ID = "1IX4irbd_vgWQMpYdmA_GIDZJgIt57L-1PzQtqcPqjo4"
SHEET_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"

# Update these if your column names differ
COL_NAME         = "What is your name? (Please use the same name for all ratings)"
COL_SNACK        = "Which snack are you rating? (Insert snack ID)"
COL_FLAVOUR      = "How would you rate the FLAVOUR of this snack?"
COL_TEXTURE      = "How would you rate the TEXTURE of this snack?"
COL_SNACKABILITY = "How would you rate the SNACKABILITY of this snack?"
COL_ORIGINALITY  = "How would you rate the ORIGINALITY of this snack?"

RATING_COLS = [COL_FLAVOUR, COL_TEXTURE, COL_SNACKABILITY, COL_ORIGINALITY]
RATING_LABELS = ["Flavour", "Texture", "Snackability", "Originality"]

# ── PAGE SETUP ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="🍿 Snack Ratings", layout="wide")
st.title("🍿 Snack Rating Dashboard")

# ── LOAD DATA ─────────────────────────────────────────────────────────────────

@st.cache_data(ttl=60)  # re-fetches from Google Sheets every 60 seconds on refresh
def load_data():
    df = pd.read_csv(SHEET_URL)
    df = df.dropna(subset=[COL_NAME, COL_SNACK] + RATING_COLS)
    for col in RATING_COLS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=RATING_COLS)
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"Could not load data from Google Sheets. Make sure the sheet is set to 'Anyone with the link can view'.\n\nError: {e}")
    st.stop()

st.caption(f"Loaded {len(df)} ratings from {df[COL_NAME].nunique()} people across {df[COL_SNACK].nunique()} snacks.")

if st.button("🔄 Refresh data"):
    st.cache_data.clear()
    st.rerun()

st.divider()

# ── 1. SNACK AVERAGES ─────────────────────────────────────────────────────────

st.header("📊 Snack Averages")

snack_avgs = (
    df.groupby(COL_SNACK)[RATING_COLS]
    .mean()
    .round(2)
    .reset_index()
)
snack_avgs.columns = ["Snack ID"] + RATING_LABELS
snack_avgs["Combined Average"] = snack_avgs[RATING_LABELS].mean(axis=1).round(2)
snack_avgs = snack_avgs.sort_values("Combined Average", ascending=False).reset_index(drop=True)

col1, col2 = st.columns([1.5, 1])

with col1:
    st.subheader("Ratings by category")
    st.dataframe(snack_avgs, use_container_width=True, hide_index=True)

with col2:
    st.subheader("Combined average")
    st.bar_chart(
        snack_avgs.set_index("Snack ID")["Combined Average"],
        use_container_width=True
    )

st.divider()

# ── 2. SNACK DETAIL ───────────────────────────────────────────────────────────

st.header("🔍 Snack Detail")

selected_snack = st.selectbox("Select a snack to inspect", snack_avgs["Snack ID"].tolist())

snack_row = snack_avgs[snack_avgs["Snack ID"] == selected_snack].iloc[0]
radar_data = pd.DataFrame({
    "Category": RATING_LABELS,
    "Average Rating": [snack_row[label] for label in RATING_LABELS]
})

col3, col4 = st.columns(2)
with col3:
    st.bar_chart(radar_data.set_index("Category"), use_container_width=True)
with col4:
    snack_responses = df[df[COL_SNACK] == selected_snack]
    st.metric("Number of ratings", len(snack_responses))
    st.metric("Combined average", f"{snack_row['Combined Average']:.2f}")
    st.metric("Best category", radar_data.loc[radar_data['Average Rating'].idxmax(), 'Category'])

st.divider()

# ── 3. TASTE SIMILARITY ───────────────────────────────────────────────────────

st.header("👥 Taste Similarity")

if df[COL_NAME].nunique() < 2:
    st.info("Need at least 2 people to calculate similarity.")
else:
    person_snack = (
        df.groupby([COL_NAME, COL_SNACK])[RATING_COLS]
        .mean()
        .mean(axis=1)
        .unstack(COL_SNACK)
        .fillna(df[RATING_COLS].stack().mean())
    )

    people = person_snack.index.tolist()

    dist_values = cdist(person_snack.values, person_snack.values, metric="cityblock") / person_snack.shape[1]
    dist_matrix = pd.DataFrame(dist_values, index=people, columns=people)

    dist_matrix_copy = dist_matrix.values.copy()
    np.fill_diagonal(dist_matrix_copy, np.nan)
    dist_matrix = pd.DataFrame(dist_matrix_copy, index=people, columns=people)

    similarity_results = pd.DataFrame({
        "Person": people,
        "Most Similar Taster": [dist_matrix.loc[p].idxmin() for p in people],
        "Similarity Score": [round(dist_matrix.loc[p].min(), 2) for p in people],
        "Most Dissimilar Taster": [dist_matrix.loc[p].idxmax() for p in people],
        "Dissimilarity Score": [round(dist_matrix.loc[p].max(), 2) for p in people],
    })

    st.dataframe(similarity_results, use_container_width=True, hide_index=True)

    st.subheader("Full distance matrix")
    st.caption("Lower = more similar taste")
    st.dataframe(dist_matrix.round(2), use_container_width=True)

st.divider()

# ── 4. INDIVIDUAL PROFILE ─────────────────────────────────────────────────────

st.header("🧑 Individual Profile")

selected_person = st.selectbox("Select a person", sorted(df[COL_NAME].unique()))

person_df = df[df[COL_NAME] == selected_person]
person_avgs = person_df.groupby(COL_SNACK)[RATING_COLS].mean().round(2)
person_avgs.columns = RATING_LABELS
person_avgs["Combined"] = person_avgs.mean(axis=1).round(2)
person_avgs = person_avgs.sort_values("Combined", ascending=False)

st.write(f"**{selected_person}** has rated **{len(person_df)}** snack(s).")
st.dataframe(person_avgs, use_container_width=True)
