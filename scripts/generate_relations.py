import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

ENTITIES_CSV = PROJECT_ROOT / "data" / "processed" / "entities.csv"
RELATIONS_CSV = PROJECT_ROOT / "data" / "processed" / "relations.csv"

df = pd.read_csv(ENTITIES_CSV)

relations = []

for _, row in df.iterrows():

    relations.append({
        "source": str(row["PMID"]),
        "source_type": "Paper",
        "relation": "MENTIONS",
        "target": row["Entity"],
        "target_type": row["Type"]
    })

relations_df = pd.DataFrame(relations)

relations_df.drop_duplicates(inplace=True)

relations_df.to_csv(
    RELATIONS_CSV,
    index=False,
    encoding="utf-8-sig"
)

print(relations_df["relation"].value_counts())

print("关系数：", len(relations_df))