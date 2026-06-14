import pandas as pd
from pathlib import Path

BASE = Path(r"D:\Python310\TCM_Depression_KnowledgeGraph\data\symmap\SymMap v2.0")

hb = pd.read_excel(BASE / "SMHB file.xlsx")
smit = pd.read_excel(BASE / "SMIT file.xlsx")
smtt = pd.read_excel(BASE / "SMTT file.xlsx")

# ========= Nodes =========
herb_nodes = hb.iloc[:, :2]
herb_nodes.columns = ["name", "label"]
herb_nodes["label"] = "Herb"

ingredient_nodes = pd.DataFrame({
    "name": pd.concat([smit["Ingredient"], smtt["Ingredient"]]).dropna().unique()
})
ingredient_nodes["label"] = "Ingredient"

target_nodes = pd.DataFrame({
    "name": smtt["Target"].dropna().unique()
})
target_nodes["label"] = "Target"

nodes = pd.concat([herb_nodes, ingredient_nodes, target_nodes])
nodes = nodes.drop_duplicates(subset=["name"])
nodes.insert(0, "id", range(len(nodes)))

# ========= Relations =========
rel_hi = smit[["Herb", "Ingredient"]].dropna()
rel_hi.columns = ["source", "target"]
rel_hi["relation"] = "HAS_INGREDIENT"

rel_it = smtt[["Ingredient", "Target"]].dropna()
rel_it.columns = ["source", "target"]
rel_it["relation"] = "TARGETS"

relations = pd.concat([rel_hi, rel_it]).drop_duplicates()

# ========= Save =========
OUT = BASE / "output"
OUT.mkdir(exist_ok=True)

nodes.to_csv(OUT / "symmap_nodes.csv", index=False, encoding="utf-8-sig")
relations.to_csv(OUT / "symmap_relations.csv", index=False, encoding="utf-8-sig")

print("SymMap build done:", len(nodes), len(relations))