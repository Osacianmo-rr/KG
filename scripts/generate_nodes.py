import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENTITIES_CSV = PROJECT_ROOT / "data" / "processed" / "entities.csv"

OUTPUT = PROJECT_ROOT / "data" / "processed" / "nodes.csv"

df = pd.read_csv(ENTITIES_CSV)

nodes = []

# Paper节点
for pmid in df["PMID"].unique():

    nodes.append({
        "id": str(pmid),
        "type": "Paper"
    })

# 实体节点
entity_nodes = (
    df[["Entity", "Type"]]
    .drop_duplicates()
)

for _, row in entity_nodes.iterrows():

    nodes.append({
        "id": row["Entity"],
        "type": row["Type"]
    })

nodes_df = pd.DataFrame(nodes)

nodes_df.drop_duplicates(inplace=True)

nodes_df.to_csv(
    OUTPUT,
    index=False,
    encoding="utf-8-sig"
)

print("节点数：", len(nodes_df))