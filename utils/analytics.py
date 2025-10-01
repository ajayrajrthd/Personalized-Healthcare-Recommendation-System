import pandas as pd
from .db import fetch_user_events, fetch_ratings

def _find_col(df: pd.DataFrame, candidates):
    """Return actual column name from df that matches any candidate (case-insensitive), or None."""
    if df is None or df.empty:
        return None
    cols_map = {str(c).lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in cols_map:
            return cols_map[cand.lower()]
    return None

def kpis():
    events = pd.DataFrame(fetch_user_events())
    ratings = pd.DataFrame(fetch_ratings())

    # DAU / MAU (detect timestamp-like column)
    ts_col = _find_col(events, ["timestamp", "time", "created_at", "ts", "date"])
    if ts_col is not None:
        try:
            times = pd.to_datetime(events[ts_col], errors="coerce")
            dau = times.dt.strftime("%Y-%m-%d").nunique()
            mau = times.dt.strftime("%Y-%m").nunique()
        except Exception:
            dau, mau = 0, 0
    else:
        dau, mau = 0, 0

    total_events = len(events)

    # Ratings / CTR (detect rating column)
    rating_col = _find_col(ratings, ["rating", "rate", "r", "score", "value"])
    total_ratings = len(ratings)
    if rating_col is not None and total_ratings > 0:
        try:
            ctr = (pd.to_numeric(ratings[rating_col], errors="coerce") > 0).mean() * 100.0
        except Exception:
            ctr = 0.0
    else:
        ctr = 0.0

    # Unique users: prefer ratings' user col, else events' user col
    user_col = _find_col(ratings, ["user_id", "userid", "uid", "user", "id"])
    if user_col is None:
        user_col = _find_col(events, ["user_id", "userid", "uid", "user", "id"])
    total_users = int(ratings[user_col].nunique()) if (user_col is not None and not ratings.empty) else (int(events[user_col].nunique()) if (user_col is not None and not events.empty) else 0)

    return {
        "DAU (unique days w/ events)": int(dau),
        "MAU (unique months w/ events)": int(mau),
        "Events logged": int(total_events),
        "Ratings count": int(total_ratings),
        "Positive rating rate (%)": round(float(ctr), 2),
        "Unique users (approx)": int(total_users),
    }

def algo_performance():
    ratings = pd.DataFrame(fetch_ratings())
    if ratings.empty:
        return pd.DataFrame(columns=["algorithm","impressions","positive","ctr"])

    # detect item & rating columns
    item_col = _find_col(ratings, ["item_id", "itemid", "item", "iid"])
    rating_col = _find_col(ratings, ["rating", "rate", "r", "score", "value"])

    if item_col is None or rating_col is None:
        # not enough data to compute per-item CTR
        return pd.DataFrame(columns=["algorithm","impressions","positive","ctr"])

    # ensure numeric conversion for rating counting
    ratings["_rating_num"] = pd.to_numeric(ratings[rating_col], errors="coerce").fillna(0.0)

    group = ratings.groupby(item_col)["_rating_num"].agg(impressions="count", positive=lambda s: (s > 0).sum())
    group["ctr"] = (group["positive"] / group["impressions"] * 100).round(2)
    out = group.reset_index().rename(columns={item_col: "item_id"})
    return out
