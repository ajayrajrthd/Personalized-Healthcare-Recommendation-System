import streamlit as st
import pandas as pd
from pathlib import Path
from utils.sentiment import sentiment_score

st.title("💊 Medicine Recommendation")

meds = pd.read_csv(Path(__file__).resolve().parents[1] / "data" / "medicines.csv")

condition = st.selectbox("Select condition", sorted(meds["for_condition"].unique().tolist()))
allergies = st.text_input("Known allergies (comma separated, e.g., allergy-ace, allergy-metformin)")

# Filter by condition
rec = meds[meds["for_condition"] == condition].copy()

# Filter out contraindicated by allergy token matching
if allergies:
    bad = set([a.strip().lower() for a in allergies.split(",")])
    def safe(row):
        contras = set((row["contraindications"] or "").lower().split(","))
        return contras.isdisjoint(bad)
    rec = rec[rec.apply(safe, axis=1)]

st.write("### Recommendations")
if rec.empty:
    st.info("No safe medicines found given current filters.")
else:
    for _, row in rec.iterrows():
        with st.container(border=True):
            st.subheader(row["name"])
            st.caption(f"For: {row['for_condition']} | Contraindications: {row['contraindications']}")
            st.write(row["description"])
            review = st.text_input(f"Write an optional review for {row['name']}:", key=f"rv_{row['medicine_id']}")
            if review:
                s = sentiment_score(review)
                st.caption(f"Detected sentiment score: {s:.2f} (−1..+1)")

st.warning("This demo is **not** medical advice. Always consult a qualified doctor or pharmacist.")
