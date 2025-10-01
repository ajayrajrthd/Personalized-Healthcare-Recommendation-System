from pathlib import Path
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from scipy import sparse
from typing import List, Dict, Optional
import json

ROOT = Path(__file__).resolve().parents[1]
ITEMS_CSV = ROOT / "data" / "items.csv"

# Fit TF-IDF on startup (small data; OK to refit)
_items = pd.read_csv(ITEMS_CSV)
_items["text"] = (_items["title"].fillna("") + " " +
                  _items["tags"].fillna("") + " " +
                  _items["description"].fillna(""))
_vectorizer = TfidfVectorizer(stop_words="english")
_item_vectors = _vectorizer.fit_transform(_items["text"].values)

def get_items_df() -> pd.DataFrame:
    return _items.copy()

def content_similar_items(item_id: int, top_k: int = 5) -> pd.DataFrame:
    idx = _items.index[_items["item_id"] == item_id]
    if len(idx) == 0:
        return pd.DataFrame()
    idx = idx[0]
    sims = cosine_similarity(_item_vectors[idx], _item_vectors).flatten()
    order = sims.argsort()[::-1]
    # Skip itself
    order = [i for i in order if i != idx]
    top_idx = order[:top_k]
    res = _items.iloc[top_idx].copy()
    res["score"] = sims[top_idx]
    return res

def content_based_for_user(liked_item_ids: List[int], top_k: int = 5) -> pd.DataFrame:
    if not liked_item_ids:
        # fallback to popularity
        res = _items.sort_values("popularity", ascending=False).head(top_k).copy()
        res["score"] = (res["popularity"] - res["popularity"].min()) / ((res["popularity"].max() - res["popularity"].min()) + 1e-6)
        return res
    sims = np.zeros(_items.shape[0])
    for iid in liked_item_ids:
        idx = _items.index[_items["item_id"] == iid]
        if len(idx) == 0: 
            continue
        idx = idx[0]
        s = cosine_similarity(_item_vectors[idx], _item_vectors).flatten()
        sims = np.maximum(sims, s)  # max-pool across liked items
    order = sims.argsort()[::-1]
    # remove liked ones
    kept = [i for i in order if _items.iloc[i]["item_id"] not in liked_item_ids]
    top_idx = kept[:top_k]
    res = _items.iloc[top_idx].copy()
    res["score"] = sims[top_idx]
    return res



def user_user_collab(rating_df: pd.DataFrame, user_id: int, top_k: int = 5) -> pd.DataFrame:
    if rating_df is None or rating_df.empty:
        return pd.DataFrame()

    # tolerant rename
    rename_map = {}
    for c in list(rating_df.columns):
        col_lower = str(c).lower()
        if col_lower in ("user_id", "userid", "uid", "user", "id"):
            rename_map[c] = "user_id"
        elif col_lower in ("item_id", "itemid", "item", "iid"):
            rename_map[c] = "item_id"
        elif col_lower in ("rating", "rate", "r", "score"):
            rename_map[c] = "rating"
    if rename_map:
        rating_df = rating_df.rename(columns=rename_map)

    # Require the three core columns
    if not {"user_id", "item_id", "rating"}.issubset(rating_df.columns):
        return pd.DataFrame()

    # Force numeric types (safe conversion)
    rating_df["user_id"] = pd.to_numeric(rating_df["user_id"], errors="coerce").fillna(0).astype(int)
    rating_df["item_id"] = pd.to_numeric(rating_df["item_id"], errors="coerce").fillna(0).astype(int)
    rating_df["rating"] = pd.to_numeric(rating_df["rating"], errors="coerce").fillna(0.0).astype(float)

    # If user not present, return empty
    if user_id not in rating_df["user_id"].unique():
        return pd.DataFrame()




    # Pivot to user-item matrix
    mat = rating_df.pivot_table(index="user_id", columns="item_id", values="rating", fill_value=0)
    if user_id not in mat.index:
        return pd.DataFrame()
    
    # Cosine similarity between target user and others
    A = mat.values
    # Normalize rows
    norms = np.linalg.norm(A, axis=1, keepdims=True) + 1e-9
    A_norm = A / norms
    target = A_norm[mat.index.get_loc(user_id)]
    sims = A_norm @ target
    # Zero self
    sims[mat.index.get_loc(user_id)] = 0.0
    # Weighted sum of others' ratings
    weights = sims.reshape(-1, 1)
    scores = (A_norm * weights).sum(axis=0)
    # Exclude items already rated by user
    rated_items = set(mat.columns[mat.loc[user_id] > 0].tolist())
    candidates = [(item_id, scores[i]) for i, item_id in enumerate(mat.columns) if item_id not in rated_items]
    candidates.sort(key=lambda x: x[1], reverse=True)
    top = candidates[:top_k]
    if not top:
        return pd.DataFrame()
    # Map to items
    items = pd.read_csv(ITEMS_CSV)
    df = items[items["item_id"].isin([i for i, _ in top])].copy()
    score_map = {i:s for i,s in top}
    df["score"] = df["item_id"].map(score_map).fillna(0.0)
    df = df.sort_values("score", ascending=False)
    return df

def hybrid_recommendation(liked_item_ids: List[int], rating_df: pd.DataFrame, user_id: int, top_k: int = 5, alpha: float = 0.6) -> pd.DataFrame:
    
    # standardize column names
    if rating_df is None:
        rating_df = pd.DataFrame()

    # Normalize rating_df columns
    if not rating_df.empty:
        rename_map = {}
        for c in rating_df.columns:
            col_lower = str(c).lower()
            if col_lower in ("user_id", "userid", "uid", "user", "id"):
                rename_map[c] = "user_id"
            elif col_lower in ("item_id", "itemid", "item", "iid"):
                rename_map[c] = "item_id"
            elif col_lower in ("rating", "rate", "r", "score"):
                rename_map[c] = "rating"
        if rename_map:
            rating_df = rating_df.rename(columns=rename_map)

    # Call recommenders
    cb = content_based_for_user(liked_item_ids, top_k=top_k * 2)
    cf = user_user_collab(rating_df, user_id, top_k=top_k * 2)

    # Fallback to popularity
    if (cb is None or cb.empty) and (cf is None or cf.empty):
        df = get_items_df().sort_values("popularity", ascending=False).head(top_k).copy()
        if not df.empty:
            pop = df["popularity"].astype(float)
            denom = (pop.max() - pop.min()) or 1.0
            df["score"] = (pop - pop.min()) / (denom + 1e-9)
        else:
            df["score"] = 0.0
        return df

    if cb is None or cb.empty:
        return cf.head(top_k)
    if cf is None or cf.empty:
        return cb.head(top_k)

    # Blend
    cb = cb.reset_index(drop=True)
    cf = cf.reset_index(drop=True)
    cb["cb_rank"] = np.linspace(1, 0, len(cb))
    cf["cf_rank"] = np.linspace(1, 0, len(cf))

    merged = pd.merge(cb[["item_id", "cb_rank"]],
                      cf[["item_id", "cf_rank"]],
                      on="item_id", how="outer")
    merged["cb_rank"] = merged["cb_rank"].fillna(0)
    merged["cf_rank"] = merged["cf_rank"].fillna(0)
    merged["score"] = alpha * merged["cb_rank"] + (1 - alpha) * merged["cf_rank"]

    items_df = get_items_df()
    out = pd.merge(merged, items_df, on="item_id", how="left").drop_duplicates("item_id")
    out = out.sort_values("score", ascending=False).head(top_k)

    return out[items_df.columns.tolist() + ["score"] if not items_df.empty else ["item_id", "score"]]

def context_adjust(recs: pd.DataFrame, time_of_day: str = "any", trending_weight: float = 0.2) -> pd.DataFrame:
    if recs.empty:
        return recs
    recs = recs.copy()
    # Boost if timeslot matches
    recs["time_boost"] = (recs["timeslot"].fillna("any").str.lower().eq(time_of_day.lower())).astype(float) * 0.1
    # Normalize popularity
    pop = recs["popularity"].astype(float)
    pop_norm = (pop - pop.min()) / (pop.max() - pop.min() + 1e-9)
    recs["trend_boost"] = trending_weight * pop_norm
    recs["score_adj"] = recs.get("score", 0.5) + recs["time_boost"] + recs["trend_boost"]
    recs = recs.sort_values("score_adj", ascending=False)
    return recs

def simple_search(query: str, top_k: int = 10) -> pd.DataFrame:
    q = query.strip().lower()
    items = get_items_df()
    mask = items["title"].str.lower().str.contains(q) | items["tags"].str.lower().str.contains(q) | items["description"].str.lower().str.contains(q)
    df = items[mask].copy()
    if df.empty:
        return df
    vecs = _vectorizer.transform(df["title"].fillna("") + " " + df["tags"].fillna("") + " " + df["description"].fillna(""))
    qvec = _vectorizer.transform([q])
    sims = cosine_similarity(qvec, vecs).flatten()
    df["score"] = sims
    return df.sort_values("score", ascending=False).head(top_k)
