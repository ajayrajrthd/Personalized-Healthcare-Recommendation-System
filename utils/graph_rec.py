from pathlib import Path
import pandas as pd
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]

def build_graph():
    items = pd.read_csv(ROOT / "data" / "items.csv")
    meds = pd.read_csv(ROOT / "data" / "medicines.csv")
    G = nx.Graph()
    # Add condition nodes, item nodes, medicine nodes
    for _, row in items.iterrows():
        G.add_node(f"item:{row['item_id']}", kind="item", condition=row["condition"])
        G.add_node(f"cond:{row['condition']}", kind="condition")
        G.add_edge(f"cond:{row['condition']}", f"item:{row['item_id']}")
    for _, row in meds.iterrows():
        G.add_node(f"med:{row['medicine_id']}", kind="medicine", condition=row["for_condition"])
        G.add_node(f"cond:{row['for_condition']}", kind="condition")
        G.add_edge(f"cond:{row['for_condition']}", f"med:{row['medicine_id']}")
    return G

def graph_recommend(condition: str, top_k: int = 5):
    import pandas as pd
    G = build_graph()
    # Rank neighbors of condition by degree centrality (toy example)
    neighbors = list(G.neighbors(f"cond:{condition}")) if G.has_node(f"cond:{condition}") else []
    deg = {n: G.degree(n) for n in neighbors}
    top = sorted(neighbors, key=lambda n: deg[n], reverse=True)[:top_k]
    # Map back to items
    items = pd.read_csv(ROOT / "data" / "items.csv")
    meds = pd.read_csv(ROOT / "data" / "medicines.csv")
    item_ids, med_ids = [], []
    for n in top:
        if n.startswith("item:"):
            item_ids.append(int(n.split(":")[1]))
        elif n.startswith("med:"):
            med_ids.append(int(n.split(":")[1]))
    rec_items = items[items["item_id"].isin(item_ids)].copy()
    rec_meds = meds[meds["medicine_id"].isin(med_ids)].copy()
    return rec_items, rec_meds
