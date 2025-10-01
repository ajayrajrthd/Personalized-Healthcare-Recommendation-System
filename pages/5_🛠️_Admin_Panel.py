import streamlit as st
import pandas as pd
from pathlib import Path

st.title("🛠️ Admin Panel")

# -------------------------
# Admin check
# -------------------------
user = st.session_state.get("user")
if not user or user.get("role") != "Admin":
    st.warning("Admin only. Please login with an Admin account.")
    st.stop()

# -------------------------
# CSV path and load
# -------------------------
items_path = Path(__file__).resolve().parents[1] / "data" / "items.csv"
df = pd.read_csv(items_path, dtype={
    "item_id": int, "title": str, "tags": str, "description": str,
    "condition": str, "timeslot": str, "popularity": int
})

# -------------------------
# Display current items
# -------------------------
st.write("### Items")
st.dataframe(df)

# -------------------------
# Add / Edit Item
# -------------------------
st.write("### Add / Edit Item")
with st.form("item_form"):
    item_id = st.number_input(
        "item_id (unique)", 
        value=int(df["item_id"].max() + 1 if not df.empty else 1),
        min_value=1,
        step=1
    )
    title = st.text_input("title")
    tags = st.text_input("tags (comma separated)")
    description = st.text_area("description")
    condition = st.text_input("condition")
    timeslot = st.selectbox("timeslot", ["morning","afternoon","evening","night","any"], index=4)
    popularity = st.number_input("popularity", value=10, min_value=0)
    submitted = st.form_submit_button("Save Item")

    if submitted:
        new_row = {
            "item_id": int(item_id),
            "title": title,
            "tags": tags,
            "description": description,
            "condition": condition,
            "timeslot": timeslot,
            "popularity": int(popularity)
        }
        # Remove old item if editing
        df = df[df["item_id"] != int(item_id)]
        # Append new row
        df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
        df.to_csv(items_path, index=False)
        st.success(f"Item {item_id} saved successfully.")
        st.rerun()  # stable rerun

# -------------------------
# Delete Item
# -------------------------
st.write("### Delete Item")
del_id = st.number_input("item_id to delete", value=1, min_value=1, step=1)

if st.button("Delete Item"):
    if del_id in df["item_id"].values:
        df = df[df["item_id"] != del_id]
        df.to_csv(items_path, index=False)
        st.success(f"Deleted item_id {del_id}.")
        st.rerun()
    else:
        st.warning("No such item_id exists.")
