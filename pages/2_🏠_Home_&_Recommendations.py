import streamlit as st
import pandas as pd
from utils.auth import decode_jwt
from utils.db import log_activity, fetch_ratings, rate_item
from utils.recommender import get_items_df, simple_search, content_based_for_user, user_user_collab, hybrid_recommendation, context_adjust
from utils.rl_bandit import EpsilonGreedy
from utils.graph_rec import graph_recommend

st.title("🏠 Home & Recommendations")

user = st.session_state.get("user")
if not user:
    st.warning("Please login first (left sidebar → Login / Signup).")
    st.stop()

st.sidebar.subheader("Context")
time_of_day = st.sidebar.selectbox("Time of day", ["morning","afternoon","evening","night","any"], index=4)

items = get_items_df()
st.write("### Browse Items")
q = st.text_input("Search (title/tags/description)")
if q:
    res = simple_search(q, top_k=10)
    st.dataframe(res[["item_id","title","tags","condition","timeslot","popularity"]])
else:
    st.dataframe(items[["item_id","title","tags","condition","timeslot","popularity"]])

st.write("### Your Recommendations")
# derive liked items from ratings > 0
ratings = pd.DataFrame(fetch_ratings())
liked = []

if not ratings.empty:
    # tolerant column detection
    user_col = next((c for c in ("user_id","userid","uid","user","id") if c in ratings.columns), None)
    rating_col = next((c for c in ("rating","rate","r") if c in ratings.columns), None)
    item_col = next((c for c in ("item_id","itemid","item","itemId") if c in ratings.columns), None)

    if user_col and rating_col and item_col:
        # rename columns to what recommender.py expects
        ratings = ratings.rename(columns={
            user_col: "user_id",
            rating_col: "rating",
            item_col: "item_id"
        })
        liked = ratings[(ratings["user_id"] == user["id"]) & (ratings["rating"] > 0)]["item_id"].tolist()
    else:
        liked = []


bandit = EpsilonGreedy(epsilon=0.2)
algo = bandit.choose()

if algo == "content":
    recs = content_based_for_user(liked, top_k=5)
elif algo == "collab":
    recs = user_user_collab(ratings, user_id=user["id"], top_k=5)
elif algo == "graph":
    # Guess condition from last liked or pick common one
    cond = "hypertension"
    if liked:
        cond = items[items["item_id"].isin(liked)]["condition"].mode().iloc[0]
    rec_items, rec_meds = graph_recommend(cond, top_k=5)
    recs = rec_items.copy()
    if rec_meds is not None and not rec_meds.empty:
        st.caption("Graph says you might also care about these medicines:")
        st.dataframe(rec_meds)
else:
    recs = hybrid_recommendation(liked, ratings, user_id=user["id"], top_k=5, alpha=0.6)

recs = context_adjust(recs, time_of_day=time_of_day)

if recs is not None and not recs.empty:
    for _, row in recs.iterrows():
        with st.container(border=True):
            st.subheader(f"{row['title']}  •  ({row['condition']})")
            st.caption(f"tags: {row['tags']} | time: {row['timeslot']}")
            st.write(row["description"])
            c1, c2, c3 = st.columns(3)
            with c1:
                if st.button(f"👍 Like #{row['item_id']}", key=f"like_{row['item_id']}"):
                    rate_item(user["id"], int(row["item_id"]), 1)
                    log_activity(user["id"], "like", int(row["item_id"]))
                    bandit.update(algo, True)   # ✅ record positive feedback
                    st.success("Thanks for the feedback!")
            with c2:
                if st.button(f"👎 Skip #{row['item_id']}", key=f"skip_{row['item_id']}"):
                    rate_item(user["id"], int(row["item_id"]), -1)
                    log_activity(user["id"], "skip", int(row["item_id"]))
                    bandit.update(algo, False)  # ❌ record negative feedback
                    st.info("Noted.")
            with c3:
                if st.button(f"📌 View #{row['item_id']}", key=f"view_{row['item_id']}"):
                    log_activity(user["id"], "view", int(row["item_id"]))
                    st.toast("Opened! (Pretend detail page)")

    st.caption(f"Served by algorithm: **{algo}** (epsilon-greedy demo)")
else:
    st.info("No recommendations yet. Try liking a few items or adjusting context.")
