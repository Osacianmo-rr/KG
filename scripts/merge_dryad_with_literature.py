# scripts/merge_dryad_with_literature.py
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# 加载 Dryad 节点和关系
dryad_nodes = pd.read_csv(PROCESSED_DIR / "tcmsp_nodes.csv", encoding='utf-8-sig')
dryad_rels = pd.read_csv(PROCESSED_DIR / "tcmsp_rels.csv", encoding='utf-8-sig')

# 加载文献实体
df_entities = pd.read_csv(PROCESSED_DIR / "entities.csv", encoding='utf-8-sig')
lit_nodes = df_entities[['Entity', 'Type']].drop_duplicates().rename(columns={'Entity': 'id', 'Type': 'type'})
lit_nodes['name'] = lit_nodes['id']

# 加载论文节点
df_papers = pd.read_csv(PROCESSED_DIR / "high_quality_corpus.csv", encoding='utf-8-sig')
paper_nodes = pd.DataFrame({
    'id': df_papers['PMID'].astype(str),
    'type': 'Paper',
    'name': df_papers['PMID'].astype(str)
}).drop_duplicates()

# 合并所有节点
all_nodes = pd.concat([dryad_nodes, lit_nodes, paper_nodes], ignore_index=True)
all_nodes = all_nodes.drop_duplicates(subset=['id'])

# 生成 MENTIONS 关系（论文->实体）
mentions = []
for _, row in df_entities.iterrows():
    mentions.append({
        'source': str(row['PMID']),
        'source_type': 'Paper',
        'target': row['Entity'],
        'target_type': row['Type'],
        'relation': 'MENTIONS'
    })
# 合并所有关系（Dryad 已有关系 + MENTIONS）
all_rels = pd.concat([dryad_rels, pd.DataFrame(mentions)], ignore_index=True)
all_rels = all_rels.drop_duplicates()

# 保存最终文件
all_nodes.to_csv(PROCESSED_DIR / "final_nodes.csv", index=False, encoding='utf-8-sig')
all_rels.to_csv(PROCESSED_DIR / "final_relations.csv", index=False, encoding='utf-8-sig')

print(f"最终节点数: {len(all_nodes)}")
print(f"最终关系数: {len(all_rels)}")
print("节点类型分布:")
print(all_nodes['type'].value_counts())