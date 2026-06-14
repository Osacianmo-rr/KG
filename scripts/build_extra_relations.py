# scripts/build_extra_relations.py
import pandas as pd
from pathlib import Path
from itertools import combinations

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# 加载已有关系（避免重复添加，先读取）
existing_rels = pd.read_csv(PROCESSED_DIR / "final_relations.csv", encoding='utf-8-sig')
existing_set = set(zip(existing_rels['source'], existing_rels['target'], existing_rels['relation']))

# 加载实体
df_entities = pd.read_csv(PROCESSED_DIR / "entities.csv", encoding='utf-8-sig')

# 定义共现关系映射
CO_OCCUR_RELATIONS = {
    ('Formula', 'Disease'): 'TREATS',
    ('Formula', 'Syndrome'): 'USED_FOR',
    ('Formula', 'Symptom'): 'RELIEVES',
    ('Herb', 'Disease'): 'TREATS',
    ('Ingredient', 'Target'): 'ACTS_ON',
    ('Target', 'Pathway'): 'INVOLVED_IN',
    ('Syndrome', 'Disease'): 'ASSOCIATED_WITH',
    ('Symptom', 'Disease'): 'SYMPTOM_OF',
}

new_rels = []

# 按文献分组
grouped = df_entities.groupby('PMID')
for pmid, group in grouped:
    entities = list(zip(group['Entity'], group['Type']))
    # 生成所有实体对
    for (e1, t1), (e2, t2) in combinations(entities, 2):
        # 检查预定义关系
        if (t1, t2) in CO_OCCUR_RELATIONS:
            rel = CO_OCCUR_RELATIONS[(t1, t2)]
            key = (e1, e2, rel)
            if key not in existing_set:
                new_rels.append({
                    'source': e1,
                    'source_type': t1,
                    'target': e2,
                    'target_type': t2,
                    'relation': rel
                })
                existing_set.add(key)
        elif (t2, t1) in CO_OCCUR_RELATIONS:
            rel = CO_OCCUR_RELATIONS[(t2, t1)]
            key = (e2, e1, rel)
            if key not in existing_set:
                new_rels.append({
                    'source': e2,
                    'source_type': t2,
                    'target': e1,
                    'target_type': t1,
                    'relation': rel
                })
                existing_set.add(key)

# 从 Dryad 推断 Ingredient→Target（可选：如果已经有 Herb→Ingredient 和 Herb→Target）
dryad_rels = pd.read_csv(PROCESSED_DIR / "tcmsp_rels.csv", encoding='utf-8-sig')
# 提取 Herb->Ingredient 和 Herb->Target
hi = dryad_rels[dryad_rels['relation'] == 'CONTAINS_INGREDIENT'][['source', 'target']].rename(columns={'source':'herb','target':'ingredient'})
ht = dryad_rels[dryad_rels['relation'] == 'TARGETS'][['source','target']].rename(columns={'source':'herb','target':'target'})
# 合并，生成 ingredient->target（一个 herb 下，成分和靶点可能相关）
merged = hi.merge(ht, on='herb')
it_pairs = merged[['ingredient','target']].drop_duplicates()
for _, row in it_pairs.iterrows():
    key = (row['ingredient'], row['target'], 'ACTS_ON')
    if key not in existing_set:
        new_rels.append({
            'source': row['ingredient'],
            'source_type': 'Ingredient',
            'target': row['target'],
            'target_type': 'Target',
            'relation': 'ACTS_ON'
        })
        existing_set.add(key)

# 保存新关系
if new_rels:
    new_df = pd.DataFrame(new_rels)
    new_df.to_csv(PROCESSED_DIR / "extra_relations.csv", index=False, encoding='utf-8-sig')
    # 合并到 final_relations.csv
    all_rels = pd.concat([existing_rels, new_df], ignore_index=True)
    all_rels.to_csv(PROCESSED_DIR / "final_relations.csv", index=False, encoding='utf-8-sig')
    print(f"新增 {len(new_rels)} 条关系，已合并到 final_relations.csv")
else:
    print("没有新关系生成")